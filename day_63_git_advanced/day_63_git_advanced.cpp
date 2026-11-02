#include <algorithm>
#include <exception>
#include <iostream>
#include <map>
#include <optional>
#include <set>
#include <stdexcept>
#include <string>
#include <tuple>
#include <unordered_map>
#include <vector>

enum class CommitType {
    Normal,
    Merge,
    Revert
};

struct Commit {
    std::string id;
    std::string message;
    std::vector<std::string> parents;
    std::map<std::string, std::string> tree;
    CommitType type{CommitType::Normal};
    std::map<std::string, std::string> metadata;
};

struct StashEntry {
    std::string message;
    std::map<std::string, std::string> tree;
    std::string base;
};

class GitError : public std::runtime_error {
public:
    explicit GitError(const std::string& message) : std::runtime_error(message) {}
};

class Repository {
private:
    std::unordered_map<std::string, Commit> commits;
    std::map<std::string, std::string> branches;
    std::map<std::string, std::string> tags;
    std::vector<StashEntry> stashes;
    std::map<std::string, std::string> workingTree;
    std::string currentBranch{"main"};
    unsigned long long sequence{0};

    std::string makeId(const std::string& message) {
        ++sequence;
        std::hash<std::string> hasher;
        return std::to_string(hasher(
            std::to_string(sequence) + "|" + message
        )).substr(0, 10);
    }

    const Commit& commitAt(const std::string& id) const {
        auto it = commits.find(id);
        if (it == commits.end()) throw GitError("Unknown commit: " + id);
        return it->second;
    }

    std::set<std::string> ancestors(const std::string& id) const {
        std::set<std::string> result;
        std::vector<std::string> stack{id};

        while (!stack.empty()) {
            auto current = stack.back();
            stack.pop_back();

            if (!result.insert(current).second) continue;

            const auto& commit = commitAt(current);
            stack.insert(stack.end(), commit.parents.begin(), commit.parents.end());
        }

        return result;
    }

    std::vector<std::string> firstParentChain(const std::string& id) const {
        std::vector<std::string> chain;
        std::string current = id;

        while (!current.empty()) {
            chain.push_back(current);
            const auto& commit = commitAt(current);
            current = commit.parents.empty() ? "" : commit.parents.front();
        }

        return chain;
    }

    std::string mergeBase(
        const std::string& left,
        const std::string& right
    ) const {
        auto leftAncestors = ancestors(left);

        for (const auto& candidate : firstParentChain(right)) {
            if (leftAncestors.contains(candidate)) return candidate;
        }

        throw GitError("No merge base");
    }

    std::string createCommit(
        const std::string& message,
        const std::map<std::string, std::string>& tree,
        const std::vector<std::string>& parents,
        CommitType type = CommitType::Normal,
        const std::map<std::string, std::string>& metadata = {}
    ) {
        if (message.empty()) throw GitError("Commit message cannot be empty");

        Commit commit;
        commit.id = makeId(message);
        commit.message = message;
        commit.parents = parents;
        commit.tree = tree;
        commit.type = type;
        commit.metadata = metadata;

        commits.emplace(commit.id, commit);
        return commit.id;
    }

public:
    Repository() {
        const auto root = createCommit("Initial application", {}, {});
        branches["main"] = root;
        workingTree.clear();
    }

    const std::string& head() const {
        return branches.at(currentBranch);
    }

    void checkout(const std::string& branch) {
        if (!branches.contains(branch)) throw GitError("Unknown branch");
        currentBranch = branch;
        workingTree = commitAt(head()).tree;
    }

    void createBranch(const std::string& name) {
        if (branches.contains(name)) throw GitError("Branch already exists");
        branches[name] = head();
    }

    void write(const std::string& path, const std::string& content) {
        if (path.empty() || path.front() == '/' || content.find('\0') != std::string::npos) {
            throw GitError("Invalid repository path or content");
        }
        workingTree[path] = content;
    }

    std::map<std::string, std::string> status() const {
        const auto& committed = commitAt(head()).tree;
        std::set<std::string> paths;

        for (const auto& [path, _] : committed) paths.insert(path);
        for (const auto& [path, _] : workingTree) paths.insert(path);

        std::map<std::string, std::string> result;

        for (const auto& path : paths) {
            auto oldIt = committed.find(path);
            auto newIt = workingTree.find(path);

            std::optional<std::string> oldValue =
                oldIt == committed.end()
                ? std::nullopt
                : std::optional<std::string>(oldIt->second);

            std::optional<std::string> newValue =
                newIt == workingTree.end()
                ? std::nullopt
                : std::optional<std::string>(newIt->second);

            if (oldValue != newValue) {
                result[path] = !oldValue ? "added"
                    : !newValue ? "deleted"
                    : "modified";
            }
        }

        return result;
    }

    std::string commit(const std::string& message) {
        if (status().empty()) throw GitError("Nothing to commit");

        const auto id = createCommit(
            message,
            workingTree,
            {head()}
        );
        branches[currentBranch] = id;
        return id;
    }

    std::string merge(const std::string& sourceBranch) {
        if (!branches.contains(sourceBranch)) throw GitError("Unknown branch");

        const auto source = branches.at(sourceBranch);
        const auto target = head();

        if (source == target) return target;

        if (ancestors(source).contains(target)) {
            branches[currentBranch] = source;
            workingTree = commitAt(source).tree;
            return source;
        }

        if (ancestors(target).contains(source)) return target;

        const auto base = mergeBase(target, source);
        const auto& baseTree = commitAt(base).tree;
        const auto& ours = commitAt(target).tree;
        const auto& theirs = commitAt(source).tree;

        auto merged = ours;
        std::set<std::string> paths;

        for (const auto& [path, _] : baseTree) paths.insert(path);
        for (const auto& [path, _] : ours) paths.insert(path);
        for (const auto& [path, _] : theirs) paths.insert(path);

        for (const auto& path : paths) {
            auto get = [](const auto& tree, const std::string& key)
                -> std::optional<std::string> {
                auto it = tree.find(key);
                return it == tree.end()
                    ? std::nullopt
                    : std::optional<std::string>(it->second);
            };

            const auto b = get(baseTree, path);
            const auto o = get(ours, path);
            const auto t = get(theirs, path);

            if (o == t) {
                if (!o) merged.erase(path);
                else merged[path] = *o;
            } else if (o == b) {
                if (!t) merged.erase(path);
                else merged[path] = *t;
            } else if (t != b) {
                throw GitError("Merge conflict in " + path);
            }
        }

        const auto id = createCommit(
            "Merge " + sourceBranch + " into " + currentBranch,
            merged,
            {target, source},
            CommitType::Merge
        );

        branches[currentBranch] = id;
        workingTree = merged;
        return id;
    }

    std::string cherryPick(const std::string& sourceId) {
        const auto& source = commitAt(sourceId);

        if (source.parents.empty()) {
            throw GitError("Cannot cherry-pick root commit");
        }

        const auto& parent = commitAt(source.parents.front());
        const auto& current = commitAt(head()).tree;
        auto result = current;

        std::set<std::string> paths;
        for (const auto& [path, _] : parent.tree) paths.insert(path);
        for (const auto& [path, _] : source.tree) paths.insert(path);

        auto value = [](const auto& tree, const std::string& path)
            -> std::optional<std::string> {
            auto it = tree.find(path);
            return it == tree.end()
                ? std::nullopt
                : std::optional<std::string>(it->second);
        };

        for (const auto& path : paths) {
            const auto before = value(parent.tree, path);
            const auto after = value(source.tree, path);
            const auto currentValue = value(current, path);

            if (before == after) continue;

            if (currentValue != before) {
                throw GitError("Cherry-pick conflict in " + path);
            }

            if (!after) result.erase(path);
            else result[path] = *after;
        }

        const auto id = createCommit(
            "Cherry-pick: " + source.message,
            result,
            {head()},
            CommitType::Normal,
            {{"cherry-picked-from", source.id}}
        );

        branches[currentBranch] = id;
        workingTree = result;
        return id;
    }

    void stashPush(const std::string& message) {
        if (status().empty()) throw GitError("No local changes");

        stashes.push_back({message, workingTree, head()});
        workingTree = commitAt(head()).tree;
    }

    void stashPop() {
        if (stashes.empty()) throw GitError("No stash entries");

        const auto& entry = stashes.back();

        if (commitAt(head()).tree != commitAt(entry.base).tree) {
            throw GitError("Stash requires conflict resolution");
        }

        workingTree = entry.tree;
        stashes.pop_back();
    }

    void reset(const std::string& target, const std::string& mode) {
        commitAt(target);

        if (mode != "soft" && mode != "mixed" && mode != "hard") {
            throw GitError("Invalid reset mode");
        }

        const auto oldTree = workingTree;
        branches[currentBranch] = target;

        if (mode == "hard" || mode == "mixed") {
            workingTree = commitAt(target).tree;
        } else {
            workingTree = oldTree;
        }
    }

    std::string revert(const std::string& targetId) {
        const auto& target = commitAt(targetId);

        if (target.parents.empty()) {
            throw GitError("Cannot revert root commit");
        }

        const auto& parent = commitAt(target.parents.front());
        const auto& current = commitAt(head()).tree;
        auto result = current;

        std::set<std::string> paths;
        for (const auto& [path, _] : parent.tree) paths.insert(path);
        for (const auto& [path, _] : target.tree) paths.insert(path);

        auto get = [](const auto& tree, const std::string& path)
            -> std::optional<std::string> {
            auto it = tree.find(path);
            return it == tree.end()
                ? std::nullopt
                : std::optional<std::string>(it->second);
        };

        for (const auto& path : paths) {
            const auto before = get(parent.tree, path);
            const auto after = get(target.tree, path);
            const auto currentValue = get(current, path);

            if (before == after) continue;

            if (currentValue != after) {
                throw GitError("Revert conflict in " + path);
            }

            if (!before) result.erase(path);
            else result[path] = *before;
        }

        const auto id = createCommit(
            "Revert: " + target.message,
            result,
            {head()},
            CommitType::Revert,
            {{"reverts", target.id}}
        );

        branches[currentBranch] = id;
        workingTree = result;
        return id;
    }

    void tag(const std::string& name) {
        if (name.empty() || name.front() == '-' || name.find(' ') != std::string::npos) {
            throw GitError("Invalid tag name");
        }
        if (tags.contains(name)) throw GitError("Tag already exists");
        tags[name] = head();
    }

    void printLog() const {
        for (const auto& id : firstParentChain(head())) {
            const auto& commit = commitAt(id);
            std::cout << "  " << id << " " << commit.message << '\n';
        }
    }

    void printState() const {
        std::cout << "Branch: " << currentBranch << '\n';
        std::cout << "HEAD:   " << head() << '\n';
        std::cout << "Tags:\n";
        for (const auto& [name, id] : tags) {
            std::cout << "  " << name << " -> " << id << '\n';
        }
        std::cout << "Working-tree changes:\n";
        for (const auto& [path, state] : status()) {
            std::cout << "  " << state << " " << path << '\n';
        }
    }
};

int main() {
    try {
        Repository repo;

        repo.write("app.cpp", "int main() { return 0; }\n");
        const auto base = repo.commit("Add application entry point");

        repo.createBranch("feature/cache");
        repo.checkout("feature/cache");
        repo.write("cache.cpp", "constexpr int CACHE_SIZE = 256;\n");
        repo.commit("Add cache configuration");

        repo.write("cache.cpp", "constexpr int CACHE_SIZE = 512;\n");
        repo.commit("Tune cache size");

        repo.checkout("main");
        repo.write("README.md", "# Deployment\n");
        repo.commit("Document deployment");

        repo.merge("feature/cache");

        repo.createBranch("maintenance");
        repo.checkout("maintenance");
        repo.cherryPick(base);

        repo.write("local.conf", "timeout=30\n");
        repo.stashPush("Temporary local configuration");
        repo.stashPop();

        const auto revertTarget = repo.head();
        repo.revert(revertTarget);
        repo.tag("v1.0.0");

        std::cout << "=== Git Advanced Repository Model ===\n";
        repo.printState();
        std::cout << "First-parent history:\n";
        repo.printLog();

        return 0;
    } catch (const std::exception& ex) {
        std::cerr << "Workflow error: " << ex.what() << '\n';
        return 1;
    }
}
