#include <algorithm>
#include <cstdint>
#include <exception>
#include <iomanip>
#include <iostream>
#include <map>
#include <queue>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

using namespace std;

class GitError : public runtime_error {
public:
    using runtime_error::runtime_error;
};

class ValidationError : public GitError {
public:
    using GitError::GitError;
};

class RepositoryStateError : public GitError {
public:
    using GitError::GitError;
};

enum class ObjectType {
    Blob,
    Tree,
    Commit
};

enum class FileState {
    Unchanged,
    Staged,
    Modified,
    Untracked
};

struct GitObject {
    ObjectType type;
    string content;
    string id;
};

struct Commit {
    string id;
    string message;
    string author;
    vector<string> parents;
    map<string, string> tree;
};

struct Branch {
    string name;
    string commitId;
};

class Repository {
private:
    map<string, string> workingTree;
    map<string, string> index;
    unordered_map<string, GitObject> objects;
    unordered_map<string, Commit> commits;
    map<string, Branch> branches;

    string headBranch = "main";
    string detachedHead;

    static string pseudoHash(const string& input) {
        // A deterministic identifier is enough for this educational model.
        // Production Git uses SHA-1/SHA-256 object IDs with exact object framing.
        uint64_t h = 1469598103934665603ULL;
        for (unsigned char c : input) {
            h ^= c;
            h *= 1099511628211ULL;
        }

        stringstream ss;
        ss << hex << setw(16) << setfill('0') << h;
        return ss.str();
    }

    string head() const {
        if (!detachedHead.empty()) {
            return detachedHead;
        }

        auto it = branches.find(headBranch);
        return it == branches.end() ? "" : it->second.commitId;
    }

    void validatePath(const string& file) const {
        if (file.empty() || file[0] == '/' ||
            file.find("..") != string::npos) {
            throw ValidationError("Unsafe repository path: " + file);
        }
    }

    void validateBranchName(const string& name) const {
        if (name.empty() || name.front() == '/' || name.back() == '/' ||
            name.find("..") != string::npos) {
            throw ValidationError("Invalid branch name: " + name);
        }

        for (char c : name) {
            if (!(isalnum(static_cast<unsigned char>(c)) ||
                  c == '.' || c == '_' || c == '/' || c == '-')) {
                throw ValidationError("Invalid branch name: " + name);
            }
        }
    }

    bool isAncestorInternal(
        const string& ancestor,
        const string& descendant
    ) const {
        if (ancestor.empty() || descendant.empty()) return false;

        vector<string> stack{descendant};
        unordered_set<string> seen;

        while (!stack.empty()) {
            string current = stack.back();
            stack.pop_back();

            if (!seen.insert(current).second) continue;
            if (current == ancestor) return true;

            const auto& commit = commits.at(current);
            for (const string& parent : commit.parents) {
                stack.push_back(parent);
            }
        }

        return false;
    }

    string mergeBase(
        const string& left,
        const string& right
    ) const {
        unordered_map<string, int> leftDistance;
        queue<string> q;
        q.push(left);
        leftDistance[left] = 0;

        while (!q.empty()) {
            string current = q.front();
            q.pop();

            for (const string& parent : commits.at(current).parents) {
                if (!leftDistance.count(parent)) {
                    leftDistance[parent] = leftDistance[current] + 1;
                    q.push(parent);
                }
            }
        }

        unordered_map<string, int> rightDistance;
        q.push(right);
        rightDistance[right] = 0;

        while (!q.empty()) {
            string current = q.front();
            q.pop();

            for (const string& parent : commits.at(current).parents) {
                if (!rightDistance.count(parent)) {
                    rightDistance[parent] = rightDistance[current] + 1;
                    q.push(parent);
                }
            }
        }

        string best;
        int bestDistance = INT_MAX;

        for (const auto& [id, distance] : leftDistance) {
            if (rightDistance.count(id)) {
                int total = distance + rightDistance[id];
                if (total < bestDistance) {
                    bestDistance = total;
                    best = id;
                }
            }
        }

        return best;
    }

public:
    Repository() {
        branches.emplace("main", Branch{"main", ""});
    }

    void writeFile(const string& file, const string& content) {
        validatePath(file);
        workingTree[file] = content;
    }

    void add(const vector<string>& files) {
        for (const string& file : files) {
            validatePath(file);

            if (!workingTree.count(file)) {
                throw GitError("File does not exist: " + file);
            }

            index[file] = workingTree.at(file);
        }
    }

    void addAll() {
        index = workingTree;
    }

    map<FileState, vector<string>> status() const {
        map<FileState, vector<string>> result;
        const string currentHead = head();

        map<string, string> committed;
        if (!currentHead.empty()) {
            committed = commits.at(currentHead).tree;
        }

        set<string> paths;
        for (const auto& [path, _] : committed) paths.insert(path);
        for (const auto& [path, _] : index) paths.insert(path);
        for (const auto& [path, _] : workingTree) paths.insert(path);

        for (const string& file : paths) {
            auto committedIt = committed.find(file);
            auto indexIt = index.find(file);
            auto workingIt = workingTree.find(file);

            string committedValue =
                committedIt == committed.end() ? "" : committedIt->second;
            string indexValue =
                indexIt == index.end() ? "" : indexIt->second;
            string workingValue =
                workingIt == workingTree.end() ? "" : workingIt->second;

            bool tracked = committedIt != committed.end() ||
                           indexIt != index.end();

            if (tracked && committedValue != indexValue) {
                result[FileState::Staged].push_back(file);
            }

            if (indexValue != workingValue && workingIt != workingTree.end()) {
                result[FileState::Modified].push_back(file);
            }

            if (!committed.count(file) && !index.count(file) &&
                workingTree.count(file)) {
                result[FileState::Untracked].push_back(file);
            }
        }

        return result;
    }

    bool dirty() const {
        const auto states = status();
        return !states.empty();
    }

    string commit(const string& message, const string& author) {
        if (message.empty() || author.empty()) {
            throw ValidationError("Commit message and author are required.");
        }

        if (index.empty()) {
            throw RepositoryStateError("Nothing is staged.");
        }

        string parent = head();

        stringstream payload;
        payload << author << '\n' << message << '\n' << parent << '\n';

        for (const auto& [path, content] : index) {
            string blobId = pseudoHash("blob:" + path + ":" + content);

            objects.emplace(
                blobId,
                GitObject{ObjectType::Blob, content, blobId}
            );

            payload << path << '=' << blobId << '\n';
        }

        string id = pseudoHash("commit:" + payload.str());

        vector<string> parents;
        if (!parent.empty()) parents.push_back(parent);

        commits.emplace(
            id,
            Commit{id, message, author, parents, index}
        );

        objects.emplace(
            id,
            GitObject{ObjectType::Commit, payload.str(), id}
        );

        if (!detachedHead.empty()) {
            detachedHead = id;
        } else {
            branches.at(headBranch).commitId = id;
        }

        return id;
    }

    void createBranch(
        const string& name,
        const string& startPoint = ""
    ) {
        validateBranchName(name);

        if (branches.count(name)) {
            throw ValidationError("Branch already exists: " + name);
        }

        string point = startPoint.empty() ? head() : startPoint;

        if (!point.empty() && !commits.count(point)) {
            throw GitError("Unknown branch start point.");
        }

        branches.emplace(name, Branch{name, point});
    }

    void checkout(const string& target) {
        if (dirty()) {
            throw RepositoryStateError(
                "Cannot checkout with uncommitted changes."
            );
        }

        if (branches.count(target)) {
            detachedHead.clear();
            headBranch = target;
            restoreTree(branches.at(target).commitId);
            return;
        }

        if (!commits.count(target)) {
            throw GitError("Unknown branch or commit: " + target);
        }

        detachedHead = target;
        restoreTree(target);
    }

    void restoreTree(const string& commitId) {
        workingTree.clear();
        index.clear();

        if (commitId.empty()) return;

        const auto& tree = commits.at(commitId).tree;
        workingTree = tree;
        index = tree;
    }

    string merge(const string& sourceBranch) {
        if (!detachedHead.empty()) {
            throw RepositoryStateError("Merge requires attached HEAD.");
        }

        if (!branches.count(sourceBranch)) {
            throw GitError("Source branch does not exist.");
        }

        if (dirty()) {
            throw RepositoryStateError("Working tree must be clean.");
        }

        string ours = head();
        string theirs = branches.at(sourceBranch).commitId;

        if (theirs.empty()) {
            throw RepositoryStateError("Source branch has no commits.");
        }

        if (ours.empty()) {
            branches.at(headBranch).commitId = theirs;
            restoreTree(theirs);
            return theirs;
        }

        if (ours == theirs || isAncestorInternal(theirs, ours)) {
            return ours;
        }

        if (isAncestorInternal(ours, theirs)) {
            branches.at(headBranch).commitId = theirs;
            restoreTree(theirs);
            return theirs;
        }

        string base = mergeBase(ours, theirs);
        if (base.empty()) {
            throw RepositoryStateError("No merge base exists.");
        }

        const auto& baseTree = commits.at(base).tree;
        const auto& ourTree = commits.at(ours).tree;
        const auto& theirTree = commits.at(theirs).tree;

        set<string> files;
        for (const auto& [file, _] : baseTree) files.insert(file);
        for (const auto& [file, _] : ourTree) files.insert(file);
        for (const auto& [file, _] : theirTree) files.insert(file);

        map<string, string> merged;
        vector<string> conflicts;

        auto get = [](const map<string, string>& tree,
                      const string& file) -> string {
            auto it = tree.find(file);
            return it == tree.end() ? "" : it->second;
        };

        for (const string& file : files) {
            string baseValue = get(baseTree, file);
            string ourValue = get(ourTree, file);
            string theirValue = get(theirTree, file);

            if (ourValue == theirValue) {
                if (!ourValue.empty()) merged[file] = ourValue;
            } else if (ourValue == baseValue) {
                if (!theirValue.empty()) merged[file] = theirValue;
            } else if (theirValue == baseValue) {
                if (!ourValue.empty()) merged[file] = ourValue;
            } else {
                conflicts.push_back(file);
            }
        }

        if (!conflicts.empty()) {
            stringstream error;
            error << "Merge conflicts:";
            for (const string& file : conflicts) error << ' ' << file;
            throw RepositoryStateError(error.str());
        }

        workingTree = merged;
        index = merged;

        return commit(
            "Merge branch '" + sourceBranch + "' into " + headBranch,
            "merge-bot"
        );
    }

    void printStatus() const {
        const auto states = status();

        cout << "\nSTATUS\n";

        auto print = [&](FileState state, const string& label) {
            cout << "  " << label << ":";
            auto it = states.find(state);

            if (it == states.end()) {
                cout << " -\n";
                return;
            }

            for (const string& file : it->second) {
                cout << ' ' << file;
            }
            cout << '\n';
        };

        print(FileState::Staged, "staged");
        print(FileState::Modified, "modified");
        print(FileState::Untracked, "untracked");
    }

    void printBranches() const {
        cout << "\nBRANCHES\n";

        for (const auto& [name, branch] : branches) {
            cout << "  " << name << " -> "
                 << (branch.commitId.empty()
                         ? "(empty)"
                         : branch.commitId.substr(0, 12))
                 << '\n';
        }
    }

    string currentHead() const {
        return head();
    }

    size_t objectCount() const {
        return objects.size();
    }

    size_t commitCount() const {
        return commits.size();
    }
};

int main() {
    try {
        Repository repository;

        repository.writeFile("README.md", "# Repository\n");
        repository.writeFile("main.cpp", "int version = 1;\n");
        repository.addAll();

        string initial = repository.commit(
            "Initialize repository",
            "developer@example.com"
        );

        repository.writeFile("main.cpp", "int version = 2;\n");
        repository.writeFile("local.log", "diagnostic information\n");
        repository.printStatus();

        repository.add({"main.cpp"});

        repository.createBranch("feature/audit");
        repository.checkout("feature/audit");

        repository.writeFile(
            "audit.conf",
            "audit.enabled=true\n"
        );
        repository.add({"audit.conf"});

        string feature = repository.commit(
            "Add audit configuration",
            "security@example.com"
        );

        repository.checkout("main");

        repository.writeFile(
            "README.md",
            "# Repository\nGovernance model\n"
        );
        repository.add({"README.md"});
        string mainUpdate = repository.commit(
            "Document repository workflow",
            "developer@example.com"
        );

        string merged = repository.merge("feature/audit");

        repository.printBranches();

        cout << "\nCOMMIT IDENTIFIERS\n";
        cout << "initial:    " << initial.substr(0, 12) << '\n';
        cout << "feature:    " << feature.substr(0, 12) << '\n';
        cout << "main:       " << mainUpdate.substr(0, 12) << '\n';
        cout << "merge:      " << merged.substr(0, 12) << '\n';

        cout << "\nOBJECT DATABASE\n";
        cout << "objects: " << repository.objectCount() << '\n';
        cout << "commits: " << repository.commitCount() << '\n';

        repository.checkout(initial);
        cout << "\nDETACHED HEAD: "
             << repository.currentHead().substr(0, 12) << '\n';

        repository.checkout("main");
        cout << "ATTACHED HEAD: "
             << repository.currentHead().substr(0, 12) << '\n';

        try {
            repository.writeFile("../outside.txt", "blocked");
        } catch (const ValidationError&) {
            cout << "\nUnsafe path rejected.\n";
        }

        cout << "\nRepository workflow validated.\n";
        return 0;
    } catch (const exception& error) {
        cerr << "Fatal error: " << error.what() << '\n';
        return 1;
    }
}
