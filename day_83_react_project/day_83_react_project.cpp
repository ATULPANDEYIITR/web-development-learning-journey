#include <algorithm>
#include <chrono>
#include <iostream>
#include <map>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;

enum class PRState {
    Draft,
    Open,
    Closed,
    Merged
};

enum class ReviewState {
    Approved,
    ChangesRequested,
    Commented,
    Dismissed
};

enum class CheckState {
    Pending,
    Success,
    Failure
};

enum class MergeStrategy {
    MergeCommit,
    Squash,
    Rebase
};

struct Commit {
    string id;
    string message;
    string author;
};

struct Branch {
    string name;
    string head;
    bool protectedBranch = false;
    vector<string> history;
};

struct Review {
    string reviewer;
    ReviewState state;
    string reviewedCommit;
};

struct StatusCheck {
    string name;
    CheckState state;
};

struct PullRequest {
    int id;
    string title;
    string author;
    string source;
    string target;
    string baseCommit;
    string headCommit;
    PRState state = PRState::Open;
    vector<Review> reviews;
    map<string, StatusCheck> checks;
    int unresolvedConversations = 0;
    bool draft = false;
};

struct ProtectionPolicy {
    size_t requiredApprovals = 2;
    set<string> requiredChecks = {
        "build", "tests", "security"
    };
    bool requireResolvedConversations = true;
    bool requireUpToDate = true;
    bool allowDirectPush = false;
    bool allowForcePush = false;
    bool allowAdminBypass = false;
    bool requireLinearHistory = true;
};

struct Evaluation {
    bool eligible;
    vector<string> reasons;
};

class RepositoryGovernance {
private:
    string repositoryName;
    map<string, Commit> commits;
    map<string, Branch> branches;
    map<int, PullRequest> pullRequests;
    map<string, ProtectionPolicy> policies;
    set<string> eligibleReviewers;
    vector<string> auditLog;

    int nextPRId = 1001;
    int nextCommitId = 1;

    string generateCommitId() {
        return "commit-" + to_string(nextCommitId++);
    }

    void record(const string& message) {
        auditLog.push_back(message);
    }

    PullRequest& getPR(int id) {
        auto it = pullRequests.find(id);

        if (it == pullRequests.end()) {
            throw invalid_argument("Pull Request does not exist.");
        }

        return it->second;
    }

    const PullRequest& getPR(int id) const {
        auto it = pullRequests.find(id);

        if (it == pullRequests.end()) {
            throw invalid_argument("Pull Request does not exist.");
        }

        return it->second;
    }

public:
    explicit RepositoryGovernance(string name)
        : repositoryName(move(name)) {
        if (repositoryName.empty()) {
            throw invalid_argument("Repository name is required.");
        }
    }

    string createCommit(
        const string& message,
        const string& author
    ) {
        if (message.empty() || author.empty()) {
            throw invalid_argument("Commit fields cannot be empty.");
        }

        string id = generateCommitId();

        commits.emplace(
            id,
            Commit{id, message, author}
        );

        record("COMMIT_CREATED: " + id);

        return id;
    }

    void createBranch(
        const string& name,
        const string& startingCommit
    ) {
        if (name.empty() || !commits.count(startingCommit)) {
            throw invalid_argument("Invalid branch definition.");
        }

        if (branches.count(name)) {
            throw invalid_argument("Branch already exists.");
        }

        branches.emplace(
            name,
            Branch{name, startingCommit, false, {startingCommit}}
        );

        record("BRANCH_CREATED: " + name);
    }

    void registerReviewer(const string& reviewer) {
        if (reviewer.empty()) {
            throw invalid_argument("Reviewer identity is required.");
        }

        eligibleReviewers.insert(reviewer);
    }

    void configureProtection(
        const string& branch,
        const ProtectionPolicy& policy
    ) {
        auto it = branches.find(branch);

        if (it == branches.end()) {
            throw invalid_argument("Branch does not exist.");
        }

        it->second.protectedBranch = true;
        policies[branch] = policy;

        record("BRANCH_PROTECTED: " + branch);
    }

    void pushCommit(
        const string& branchName,
        const string& commitId,
        bool force = false,
        bool administrator = false
    ) {
        auto branchIt = branches.find(branchName);

        if (branchIt == branches.end() || !commits.count(commitId)) {
            throw invalid_argument("Unknown branch or commit.");
        }

        Branch& branch = branchIt->second;

        if (branch.protectedBranch) {
            const auto& policy = policies.at(branchName);

            if (!administrator && !policy.allowDirectPush) {
                throw runtime_error("Direct push blocked.");
            }

            if (force && !policy.allowForcePush) {
                throw runtime_error("Force push blocked.");
            }

            if (administrator && !policy.allowAdminBypass) {
                throw runtime_error("Administrator bypass is disabled.");
            }
        }

        branch.head = commitId;
        branch.history.push_back(commitId);

        record("COMMIT_PUSHED: " + branchName);
    }

    int createPullRequest(
        const string& title,
        const string& author,
        const string& source,
        const string& target,
        bool draft = false
    ) {
        if (title.empty() || author.empty()) {
            throw invalid_argument("Title and author are required.");
        }

        if (source == target ||
            !branches.count(source) ||
            !branches.count(target)) {
            throw invalid_argument("Invalid source or target branch.");
        }

        if (branches.at(source).head == branches.at(target).head) {
            throw runtime_error("No proposed changes exist.");
        }

        int id = nextPRId++;

        PullRequest pr;
        pr.id = id;
        pr.title = title;
        pr.author = author;
        pr.source = source;
        pr.target = target;
        pr.baseCommit = branches.at(target).head;
        pr.headCommit = branches.at(source).head;
        pr.state = draft ? PRState::Draft : PRState::Open;
        pr.draft = draft;

        pullRequests.emplace(id, move(pr));

        record("PULL_REQUEST_CREATED: " + to_string(id));

        return id;
    }

    void publishDraft(int id) {
        PullRequest& pr = getPR(id);

        if (pr.state != PRState::Draft) {
            throw runtime_error("Pull Request is not a draft.");
        }

        pr.state = PRState::Open;
        pr.draft = false;

        record("DRAFT_PUBLISHED: " + to_string(id));
    }

    void addReview(
        int id,
        const string& reviewer,
        ReviewState state
    ) {
        PullRequest& pr = getPR(id);

        if (pr.state != PRState::Open || pr.draft) {
            throw runtime_error("Pull Request cannot be reviewed.");
        }

        if (!eligibleReviewers.count(reviewer)) {
            throw runtime_error("Reviewer is not eligible.");
        }

        if (reviewer == pr.author) {
            throw runtime_error("Self-approval is prohibited.");
        }

        // One current decision per reviewer.
        auto it = find_if(
            pr.reviews.begin(),
            pr.reviews.end(),
            [&](const Review& review) {
                return review.reviewer == reviewer;
            }
        );

        Review newReview{
            reviewer,
            state,
            pr.headCommit
        };

        if (it == pr.reviews.end()) {
            pr.reviews.push_back(newReview);
        } else {
            *it = newReview;
        }

        record("REVIEW_SUBMITTED: " + reviewer);
    }

    void dismissReview(int id, const string& reviewer) {
        PullRequest& pr = getPR(id);

        auto it = find_if(
            pr.reviews.begin(),
            pr.reviews.end(),
            [&](const Review& review) {
                return review.reviewer == reviewer;
            }
        );

        if (it == pr.reviews.end()) {
            throw invalid_argument("Review does not exist.");
        }

        it->state = ReviewState::Dismissed;

        record("REVIEW_DISMISSED: " + reviewer);
    }

    void setCheck(
        int id,
        const string& name,
        CheckState state
    ) {
        PullRequest& pr = getPR(id);

        if (pr.state != PRState::Open || name.empty()) {
            throw runtime_error("Invalid status-check update.");
        }

        pr.checks[name] = StatusCheck{name, state};

        record("CHECK_UPDATED: " + name);
    }

    void addConversation(int id) {
        PullRequest& pr = getPR(id);

        if (pr.state != PRState::Open) {
            throw runtime_error("Pull Request is not open.");
        }

        ++pr.unresolvedConversations;
    }

    void resolveConversation(int id) {
        PullRequest& pr = getPR(id);

        if (pr.unresolvedConversations == 0) {
            throw runtime_error("No unresolved conversation exists.");
        }

        --pr.unresolvedConversations;
    }

    void synchronizeBase(int id) {
        PullRequest& pr = getPR(id);

        if (pr.state != PRState::Open) {
            throw runtime_error("Pull Request is not open.");
        }

        pr.baseCommit = branches.at(pr.target).head;
        pr.headCommit = branches.at(pr.source).head;

        // A new proposed commit requires fresh review and CI evidence.
        pr.reviews.clear();
        pr.checks.clear();

        record("BASE_SYNCHRONIZED: " + to_string(id));
    }

    Evaluation evaluate(int id) const {
        const PullRequest& pr = getPR(id);

        Evaluation result{true, {}};

        auto policyIt = policies.find(pr.target);

        ProtectionPolicy defaultPolicy;
        const ProtectionPolicy& policy =
            policyIt == policies.end()
                ? defaultPolicy
                : policyIt->second;

        if (pr.state != PRState::Open) {
            result.reasons.push_back("Pull Request is not open.");
        }

        if (pr.draft) {
            result.reasons.push_back("Draft must be published.");
        }

        if (policy.requireUpToDate &&
            pr.baseCommit != branches.at(pr.target).head) {
            result.reasons.push_back("Target branch has advanced.");
        }

        set<string> approvals;
        bool changesRequested = false;

        for (const Review& review : pr.reviews) {
            if (review.reviewedCommit != pr.headCommit) {
                continue;
            }

            if (review.state == ReviewState::Approved) {
                approvals.insert(review.reviewer);
            }

            if (review.state == ReviewState::ChangesRequested) {
                changesRequested = true;
            }
        }

        if (changesRequested) {
            result.reasons.push_back("Changes have been requested.");
        }

        if (approvals.size() < policy.requiredApprovals) {
            result.reasons.push_back(
                "Insufficient distinct approvals."
            );
        }

        for (const string& required : policy.requiredChecks) {
            auto check = pr.checks.find(required);

            if (check == pr.checks.end() ||
                check->second.state != CheckState::Success) {
                result.reasons.push_back(
                    "Required check failed or is pending: " + required
                );
            }
        }

        if (policy.requireResolvedConversations &&
            pr.unresolvedConversations > 0) {
            result.reasons.push_back(
                "Unresolved conversations remain."
            );
        }

        result.eligible = result.reasons.empty();

        return result;
    }

    string merge(
        int id,
        MergeStrategy strategy,
        const string& actor
    ) {
        PullRequest& pr = getPR(id);

        Evaluation evaluation = evaluate(id);

        if (!evaluation.eligible) {
            string message = "Merge rejected:";

            for (const string& reason : evaluation.reasons) {
                message += "\n- " + reason;
            }

            throw runtime_error(message);
        }

        Branch& target = branches.at(pr.target);

        string strategyName;

        switch (strategy) {
            case MergeStrategy::MergeCommit:
                strategyName = "merge commit";
                break;
            case MergeStrategy::Squash:
                strategyName = "squash";
                break;
            case MergeStrategy::Rebase:
                strategyName = "rebase";
                break;
        }

        string mergeId = createCommit(
            "PR #" + to_string(id) + " merged using " + strategyName,
            actor
        );

        target.head = mergeId;
        target.history.push_back(mergeId);
        pr.state = PRState::Merged;

        record("PULL_REQUEST_MERGED: " + to_string(id));

        return mergeId;
    }

    void closePullRequest(int id) {
        PullRequest& pr = getPR(id);

        if (pr.state != PRState::Open &&
            pr.state != PRState::Draft) {
            throw runtime_error("Pull Request cannot be closed.");
        }

        pr.state = PRState::Closed;

        record("PULL_REQUEST_CLOSED: " + to_string(id));
    }

    void reopenPullRequest(int id) {
        PullRequest& pr = getPR(id);

        if (pr.state != PRState::Closed) {
            throw runtime_error("Only closed Pull Requests can reopen.");
        }

        pr.state = PRState::Open;

        record("PULL_REQUEST_REOPENED: " + to_string(id));
    }

    void printDashboard() const {
        int open = 0;
        int drafts = 0;
        int merged = 0;
        int closed = 0;
        int eligible = 0;

        for (const auto& entry : pullRequests) {
            const PullRequest& pr = entry.second;

            switch (pr.state) {
                case PRState::Open:
                    ++open;
                    if (evaluate(pr.id).eligible) ++eligible;
                    break;
                case PRState::Draft:
                    ++drafts;
                    break;
                case PRState::Merged:
                    ++merged;
                    break;
                case PRState::Closed:
                    ++closed;
                    break;
            }
        }

        cout << "\n========== REPOSITORY DASHBOARD ==========\n";
        cout << "Repository: " << repositoryName << '\n';
        cout << "Branches: " << branches.size() << '\n';
        cout << "Commits: " << commits.size() << '\n';
        cout << "Total Pull Requests: " << pullRequests.size() << '\n';
        cout << "Open: " << open << '\n';
        cout << "Draft: " << drafts << '\n';
        cout << "Merged: " << merged << '\n';
        cout << "Closed: " << closed << '\n';
        cout << "Merge Eligible: " << eligible << '\n';
        cout << "Audit Events: " << auditLog.size() << '\n';
        cout << "==========================================\n";
    }

    void printEligibility(int id) const {
        Evaluation result = evaluate(id);

        cout << "\nPR #" << id << " MERGE EVALUATION\n";
        cout << "Eligible: "
             << (result.eligible ? "YES" : "NO") << '\n';

        for (const string& reason : result.reasons) {
            cout << " - " << reason << '\n';
        }
    }
};

int main() {
    try {
        RepositoryGovernance repository("enterprise-admin-platform");

        string initial = repository.createCommit(
            "Initial platform release",
            "platform-team"
        );

        repository.createBranch("main", initial);
        repository.createBranch("feature/analytics", initial);

        string featureCommit = repository.createCommit(
            "Implement analytics module",
            "developer"
        );

        repository.pushCommit("feature/analytics", featureCommit);

        ProtectionPolicy policy;
        policy.requiredApprovals = 2;
        policy.requiredChecks = {
            "build",
            "tests",
            "security"
        };

        repository.configureProtection("main", policy);

        repository.registerReviewer("reviewer-1");
        repository.registerReviewer("reviewer-2");

        int pr = repository.createPullRequest(
            "Implement production admin dashboard",
            "developer",
            "feature/analytics",
            "main"
        );

        repository.addReview(
            pr,
            "reviewer-1",
            ReviewState::Approved
        );

        repository.addReview(
            pr,
            "reviewer-2",
            ReviewState::Approved
        );

        repository.setCheck(pr, "build", CheckState::Success);
        repository.setCheck(pr, "tests", CheckState::Success);
        repository.setCheck(pr, "security", CheckState::Success);

        repository.addConversation(pr);
        repository.resolveConversation(pr);

        repository.printEligibility(pr);

        string mergeCommit = repository.merge(
            pr,
            MergeStrategy::Squash,
            "release-manager"
        );

        cout << "\nCreated merge commit: " << mergeCommit << '\n';

        repository.printDashboard();

        return 0;

    } catch (const exception& error) {
        cerr << "Governance error: " << error.what() << '\n';
        return 1;
    }
}

/*
 * Complexity:
 * - Ordered-map lookup: O(log n)
 * - Reviewer membership: O(log r)
 * - Review evaluation: O(r + c + q)
 * - Dashboard aggregation: O(p * (r + c + q))
 *
 * Production systems can maintain indexed approval counts and
 * check summaries to avoid repeatedly scanning large collections.
 */
