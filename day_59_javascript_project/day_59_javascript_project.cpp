#include <algorithm>
#include <chrono>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

using namespace std;

string timestamp() {
    auto now = chrono::system_clock::now();
    time_t t = chrono::system_clock::to_time_t(now);

    ostringstream out;
    out << put_time(gmtime(&t), "%Y-%m-%dT%H:%M:%SZ");
    return out.str();
}

string makeId(const string& prefix, int number) {
    return prefix + "-" + to_string(number);
}

enum class PRState {
    Draft,
    Open,
    Closed,
    Merged
};

enum class ReviewState {
    Commented,
    Approved,
    ChangesRequested,
    Dismissed
};

enum class CheckState {
    Pending,
    Passing,
    Failing
};

enum class TaskState {
    Todo,
    InProgress,
    Done
};

enum class MergeStrategy {
    MergeCommit,
    Squash,
    Rebase
};

string toString(PRState state) {
    switch (state) {
        case PRState::Draft: return "draft";
        case PRState::Open: return "open";
        case PRState::Closed: return "closed";
        case PRState::Merged: return "merged";
    }
    return "unknown";
}

string toString(ReviewState state) {
    switch (state) {
        case ReviewState::Commented: return "commented";
        case ReviewState::Approved: return "approved";
        case ReviewState::ChangesRequested: return "changes_requested";
        case ReviewState::Dismissed: return "dismissed";
    }
    return "unknown";
}

string toString(CheckState state) {
    switch (state) {
        case CheckState::Pending: return "pending";
        case CheckState::Passing: return "passing";
        case CheckState::Failing: return "failing";
    }
    return "unknown";
}

string toString(TaskState state) {
    switch (state) {
        case TaskState::Todo: return "todo";
        case TaskState::InProgress: return "in_progress";
        case TaskState::Done: return "done";
    }
    return "unknown";
}

string toString(MergeStrategy strategy) {
    switch (strategy) {
        case MergeStrategy::MergeCommit: return "merge_commit";
        case MergeStrategy::Squash: return "squash";
        case MergeStrategy::Rebase: return "rebase";
    }
    return "unknown";
}

struct Commit {
    string sha;
    string author;
    string message;
    string createdAt;
};

struct ReviewComment {
    string id;
    string reviewer;
    string body;
    bool resolved{false};
};

struct Review {
    string id;
    string reviewer;
    ReviewState state;
    string commitSha;
    bool dismissed{false};
    vector<ReviewComment> comments;
};

struct StatusCheck {
    string name;
    CheckState state;
    string commitSha;
};

struct BranchProtection {
    int requiredReviews{1};
    set<string> requiredChecks;
    bool restrictDirectPush{true};
    bool restrictForcePush{true};
    bool restrictDeletion{true};
    bool requireConversationResolution{true};
    bool requireLinearHistory{false};
    bool allowAdministratorBypass{false};
};

struct Branch {
    string name;
    bool protectedBranch{false};
    vector<Commit> commits;
};

struct PullRequest {
    int number{};
    string title;
    string source;
    string target;
    string author;
    PRState state{PRState::Open};
    vector<Commit> commits;
    set<string> reviewers;
    vector<Review> reviews;
    map<string, StatusCheck> checks;
    optional<MergeStrategy> mergeStrategy;
};

struct Task {
    string id;
    string title;
    string description;
    TaskState state{TaskState::Todo};
    string priority;
    optional<int> linkedPr;
};

class GovernanceEngine {
private:
    unordered_map<string, Branch> branches;
    map<int, PullRequest> pullRequests;
    unordered_map<string, Task> tasks;
    unordered_map<string, BranchProtection> protection;
    int nextPr{1};
    int sequence{1};

    Branch& branch(const string& name) {
        auto it = branches.find(name);
        if (it == branches.end()) {
            throw runtime_error("Unknown branch: " + name);
        }
        return it->second;
    }

    PullRequest& pr(int number) {
        auto it = pullRequests.find(number);
        if (it == pullRequests.end()) {
            throw runtime_error("Unknown pull request.");
        }
        return it->second;
    }

    string nextId(const string& prefix) {
        return makeId(prefix, sequence++);
    }

    string head(const PullRequest& request) const {
        if (request.commits.empty()) {
            return "";
        }
        return request.commits.back().sha;
    }

public:
    void createBranch(const string& name, const optional<string>& base = nullopt) {
        if (branches.contains(name)) {
            throw runtime_error("Branch already exists.");
        }

        Branch result;
        result.name = name;

        if (base.has_value()) {
            result.commits = branch(*base).commits;
        }

        branches.emplace(name, move(result));
    }

    Commit commit(
        const string& branchName,
        const string& author,
        const string& message
    ) {
        if (author.empty() || message.empty()) {
            throw invalid_argument("Commit author and message are required.");
        }

        Branch& target = branch(branchName);

        Commit result{
            nextId("sha"),
            author,
            message,
            timestamp()
        };

        target.commits.push_back(result);
        return result;
    }

    void protectBranch(
        const string& name,
        BranchProtection policy
    ) {
        Branch& target = branch(name);
        target.protectedBranch = true;
        protection[name] = move(policy);
    }

    Task createTask(
        const string& title,
        const string& description,
        const string& priority
    ) {
        static const set<string> valid{
            "low", "medium", "high", "critical"
        };

        if (title.empty() || !valid.contains(priority)) {
            throw invalid_argument("Invalid task.");
        }

        Task task{
            nextId("task"),
            title,
            description,
            TaskState::Todo,
            priority,
            nullopt
        };

        tasks[task.id] = task;
        return task;
    }

    void updateTask(const string& taskId, TaskState state) {
        auto it = tasks.find(taskId);
        if (it == tasks.end()) {
            throw runtime_error("Task not found.");
        }

        it->second.state = state;
    }

    PullRequest createPullRequest(
        const string& title,
        const string& source,
        const string& target,
        const string& author,
        bool draft = false
    ) {
        Branch& sourceBranch = branch(source);
        branch(target);

        if (source == target || sourceBranch.commits.empty()) {
            throw invalid_argument("Invalid pull request branches.");
        }

        PullRequest request;
        request.number = nextPr++;
        request.title = title;
        request.source = source;
        request.target = target;
        request.author = author;
        request.state = draft ? PRState::Draft : PRState::Open;
        request.commits = sourceBranch.commits;

        pullRequests.emplace(request.number, request);
        return request;
    }

    void markReady(int number) {
        PullRequest& request = pr(number);

        if (request.state != PRState::Draft) {
            throw runtime_error("Only draft PRs can be marked ready.");
        }

        request.state = PRState::Open;
    }

    void requestReview(int number, const string& reviewer) {
        PullRequest& request = pr(number);

        if (request.state != PRState::Draft &&
            request.state != PRState::Open) {
            throw runtime_error("PR cannot accept reviewer requests.");
        }

        if (reviewer.empty() || reviewer == request.author) {
            throw invalid_argument("Invalid reviewer.");
        }

        request.reviewers.insert(reviewer);
    }

    Review& submitReview(
        int number,
        const string& reviewer,
        ReviewState state
    ) {
        PullRequest& request = pr(number);

        if (request.state != PRState::Open) {
            throw runtime_error("Only open PRs can receive reviews.");
        }

        if (!request.reviewers.contains(reviewer)) {
            throw runtime_error("Reviewer was not requested.");
        }

        if (reviewer == request.author) {
            throw runtime_error("Author cannot review its own PR.");
        }

        Review review;
        review.id = nextId("review");
        review.reviewer = reviewer;
        review.state = state;
        review.commitSha = head(request);

        request.reviews.push_back(move(review));
        return request.reviews.back();
    }

    ReviewComment& addComment(
        int number,
        const string& reviewId,
        const string& body
    ) {
        PullRequest& request = pr(number);

        for (Review& review : request.reviews) {
            if (review.id == reviewId) {
                if (body.empty()) {
                    throw invalid_argument("Comment cannot be empty.");
                }

                ReviewComment comment{
                    nextId("comment"),
                    review.reviewer,
                    body,
                    false
                };

                review.comments.push_back(move(comment));
                return review.comments.back();
            }
        }

        throw runtime_error("Review not found.");
    }

    void resolveComment(int number, const string& commentId) {
        PullRequest& request = pr(number);

        for (Review& review : request.reviews) {
            for (ReviewComment& comment : review.comments) {
                if (comment.id == commentId) {
                    comment.resolved = true;
                    return;
                }
            }
        }

        throw runtime_error("Comment not found.");
    }

    void setCheck(
        int number,
        const string& name,
        CheckState state
    ) {
        PullRequest& request = pr(number);

        request.checks[name] = StatusCheck{
            name,
            state,
            head(request)
        };
    }

    pair<bool, vector<string>> eligibility(
        int number,
        const string& actor,
        bool administrator = false
    ) {
        PullRequest& request = pr(number);
        vector<string> reasons;

        if (request.state != PRState::Open) {
            reasons.push_back("pull request is not open");
        }

        if (request.commits.empty()) {
            reasons.push_back("pull request has no commits");
        }

        auto policyIt = protection.find(request.target);
        if (policyIt == protection.end()) {
            return {reasons.empty(), reasons};
        }

        const BranchProtection& policy = policyIt->second;

        if (actor == request.author) {
            reasons.push_back("author cannot merge its own pull request");
        }

        bool bypass =
            administrator && policy.allowAdministratorBypass;

        if (!bypass) {
            string currentHead = head(request);
            set<string> approvals;

            for (const Review& review : request.reviews) {
                if (review.state == ReviewState::Approved &&
                    !review.dismissed &&
                    review.commitSha == currentHead) {
                    approvals.insert(review.reviewer);
                }
            }

            if (static_cast<int>(approvals.size()) <
                policy.requiredReviews) {
                reasons.push_back(
                    "required current approvals are missing"
                );
            }

            for (const string& required : policy.requiredChecks) {
                auto checkIt = request.checks.find(required);

                if (checkIt == request.checks.end()) {
                    reasons.push_back("missing check: " + required);
                    continue;
                }

                if (checkIt->second.state != CheckState::Passing) {
                    reasons.push_back(
                        "failing check: " + required
                    );
                }

                if (checkIt->second.commitSha != currentHead) {
                    reasons.push_back(
                        "stale check: " + required
                    );
                }
            }

            if (policy.requireConversationResolution) {
                for (const Review& review : request.reviews) {
                    for (const ReviewComment& comment : review.comments) {
                        if (!comment.resolved) {
                            reasons.push_back(
                                "unresolved review conversation"
                            );
                            break;
                        }
                    }
                }
            }
        }

        return {reasons.empty(), reasons};
    }

    Commit merge(
        int number,
        const string& actor,
        MergeStrategy strategy
    ) {
        PullRequest& request = pr(number);

        auto result = eligibility(number, actor);
        if (!result.first) {
            ostringstream message;
            message << "Merge blocked:";
            for (const string& reason : result.second) {
                message << " " << reason << ";";
            }
            throw runtime_error(message.str());
        }

        Branch& target = branch(request.target);

        Commit merged{
            nextId("sha"),
            actor,
            toString(strategy) + " merge PR #" +
                to_string(request.number) + ": " +
                request.title,
            timestamp()
        };

        target.commits.push_back(merged);
        request.state = PRState::Merged;
        request.mergeStrategy = strategy;

        return merged;
    }

    void linkTask(const string& taskId, int prNumber) {
        auto it = tasks.find(taskId);
        if (it == tasks.end()) {
            throw runtime_error("Task not found.");
        }

        pr(prNumber);
        it->second.linkedPr = prNumber;
    }

    void printDashboard() const {
        cout << "\n=== Repository Governance Dashboard ===\n\n";

        cout << "Branches:\n";
        for (const auto& [name, branchData] : branches) {
            cout << "  " << name
                 << " | protected=" << boolalpha
                 << branchData.protectedBranch
                 << " | commits=" << branchData.commits.size()
                 << "\n";
        }

        cout << "\nPull Requests:\n";
        for (const auto& [number, request] : pullRequests) {
            cout << "  #" << number
                 << " " << request.title
                 << " | " << toString(request.state)
                 << " | " << request.source
                 << " -> " << request.target
                 << "\n";

            auto policy = const_cast<GovernanceEngine*>(this)
                ->eligibility(number, "release-manager");

            cout << "     merge eligible=" << boolalpha
                 << policy.first << "\n";

            if (!policy.first) {
                for (const auto& reason : policy.second) {
                    cout << "     - " << reason << "\n";
                }
            }
        }

        cout << "\nTasks:\n";
        for (const auto& [id, task] : tasks) {
            cout << "  " << id
                 << " | " << task.title
                 << " | " << toString(task.state)
                 << " | priority=" << task.priority
                 << "\n";
        }
    }
};

int main() {
    try {
        GovernanceEngine engine;

        engine.createBranch("main");
        engine.commit(
            "main",
            "platform-admin",
            "Initialize task management platform"
        );

        BranchProtection policy;
        policy.requiredReviews = 2;
        policy.requiredChecks = {
            "unit-tests",
            "security-scan"
        };
        policy.restrictDirectPush = true;
        policy.restrictForcePush = true;
        policy.restrictDeletion = true;
        policy.requireConversationResolution = true;
        policy.requireLinearHistory = true;

        engine.protectBranch("main", policy);

        engine.createBranch("feature/task-board", "main");
        engine.commit(
            "feature/task-board",
            "developer",
            "Add task state machine"
        );
        engine.commit(
            "feature/task-board",
            "developer",
            "Add repository governance controls"
        );

        Task task = engine.createTask(
            "Implement governed task workflow",
            "A task can be completed only after its linked change is eligible for merge.",
            "high"
        );

        PullRequest request = engine.createPullRequest(
            "Implement governed task workflow",
            "feature/task-board",
            "main",
            "developer",
            true
        );

        engine.linkTask(task.id, request.number);
        engine.markReady(request.number);

        engine.requestReview(request.number, "reviewer-one");
        engine.requestReview(request.number, "reviewer-two");

        Review& first = engine.submitReview(
            request.number,
            "reviewer-one",
            ReviewState::ChangesRequested
        );

        ReviewComment& comment = engine.addComment(
            request.number,
            first.id,
            "Validate task transitions before persistence."
        );

        auto blocked = engine.eligibility(
            request.number,
            "release-manager"
        );

        if (blocked.first) {
            throw runtime_error("PR should be blocked before approvals.");
        }

        engine.resolveComment(request.number, comment.id);

        engine.submitReview(
            request.number,
            "reviewer-one",
            ReviewState::Approved
        );

        engine.submitReview(
            request.number,
            "reviewer-two",
            ReviewState::Approved
        );

        engine.setCheck(
            request.number,
            "unit-tests",
            CheckState::Passing
        );

        engine.setCheck(
            request.number,
            "security-scan",
            CheckState::Passing
        );

        auto eligible = engine.eligibility(
            request.number,
            "release-manager"
        );

        if (!eligible.first) {
            throw runtime_error(
                "Expected PR to become merge eligible."
            );
        }

        engine.merge(
            request.number,
            "release-manager",
            MergeStrategy::Squash
        );

        engine.updateTask(task.id, TaskState::Done);
        engine.printDashboard();

    } catch (const exception& error) {
        cerr << "Application error: "
             << error.what() << '\n';
        return 1;
    }

    return 0;
}
