#include <algorithm>
#include <iostream>
#include <map>
#include <set>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

enum class PullRequestState {
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
    Passed,
    Failed,
    Cancelled
};

enum class MergeStrategy {
    MergeCommit,
    Squash,
    Rebase
};

std::string to_string(PullRequestState state) {
    switch (state) {
        case PullRequestState::Draft: return "draft";
        case PullRequestState::Open: return "open";
        case PullRequestState::Closed: return "closed";
        case PullRequestState::Merged: return "merged";
    }
    return "unknown";
}

std::string to_string(MergeStrategy strategy) {
    switch (strategy) {
        case MergeStrategy::MergeCommit: return "merge_commit";
        case MergeStrategy::Squash: return "squash";
        case MergeStrategy::Rebase: return "rebase";
    }
    return "unknown";
}

struct Reviewer {
    std::string username;
    bool active = true;
    bool canReview = true;
    bool administrator = false;
};

struct Review {
    std::string reviewer;
    ReviewState state;
    std::string reviewedHead;
    int sequence;
};

struct StatusCheck {
    std::string name;
    std::string head;
    CheckState state;
};

struct ReviewThread {
    std::string id;
    bool resolved = false;
};

struct Branch {
    std::string name;
    std::string head;
    bool protectedBranch = false;
    bool deleted = false;
};

struct ProtectionPolicy {
    int minimumApprovals = 2;
    std::set<std::string> requiredChecks;
    bool requireConversationResolution = true;
    bool requireLinearHistory = true;
    bool requirePullRequest = true;
    bool allowMergeCommit = false;
    bool allowSquash = true;
    bool allowRebase = true;
    bool allowDirectPush = false;
    bool allowForcePush = false;
    bool prohibitBranchDeletion = true;
    bool allowAdminBypass = false;
};

struct PullRequest {
    int number = 0;
    std::string author;
    std::string sourceBranch;
    std::string targetBranch;
    std::string sourceHead;
    std::string baseHeadAtSync;
    PullRequestState state = PullRequestState::Draft;
    bool draft = true;
    std::vector<Review> reviews;
    std::vector<StatusCheck> checks;
    std::vector<ReviewThread> threads;
};

struct MergeDecision {
    bool eligible = false;
    int approvals = 0;
    std::vector<std::string> reasons;
};

class GovernanceEngine {
private:
    std::unordered_map<std::string, Branch> branches;
    std::unordered_map<std::string, Reviewer> reviewers;
    std::unordered_map<int, PullRequest> pullRequests;
    std::unordered_map<std::string, ProtectionPolicy> policies;
    int reviewSequence = 0;

    Branch& requireBranch(const std::string& name) {
        auto it = branches.find(name);
        if (it == branches.end() || it->second.deleted) {
            throw std::runtime_error("Branch does not exist: " + name);
        }
        return it->second;
    }

    PullRequest& requirePR(int number) {
        auto it = pullRequests.find(number);
        if (it == pullRequests.end()) {
            throw std::runtime_error("Pull Request does not exist.");
        }
        return it->second;
    }

    ProtectionPolicy policyFor(const std::string& branch) const {
        auto it = policies.find(branch);
        return it == policies.end() ? ProtectionPolicy{} : it->second;
    }

    std::unordered_map<std::string, Review> latestReviews(
        const PullRequest& pr
    ) const {
        std::unordered_map<std::string, Review> latest;
        for (const Review& review : pr.reviews) {
            auto it = latest.find(review.reviewer);
            if (it == latest.end() || review.sequence > it->second.sequence) {
                latest[review.reviewer] = review;
            }
        }
        return latest;
    }

    bool hasPassingCheck(
        const PullRequest& pr,
        const std::string& name
    ) const {
        return std::any_of(
            pr.checks.begin(),
            pr.checks.end(),
            [&](const StatusCheck& check) {
                return check.name == name &&
                       check.head == pr.sourceHead &&
                       check.state == CheckState::Passed;
            }
        );
    }

public:
    explicit GovernanceEngine(const std::string& initialHead) {
        if (initialHead.empty()) {
            throw std::invalid_argument("Initial commit identifier is required.");
        }
        branches.emplace("main", Branch{"main", initialHead, true, false});
    }

    void registerReviewer(const Reviewer& reviewer) {
        if (reviewer.username.empty()) {
            throw std::invalid_argument("Reviewer username cannot be empty.");
        }
        reviewers[reviewer.username] = reviewer;
    }

    void protectBranch(
        const std::string& branchName,
        const ProtectionPolicy& policy
    ) {
        requireBranch(branchName);
        if (policy.minimumApprovals < 0) {
            throw std::invalid_argument("Minimum approvals cannot be negative.");
        }
        policies[branchName] = policy;
        branches.at(branchName).protectedBranch = true;
    }

    void createBranch(const std::string& name, const std::string& from) {
        if (name.empty() || branches.count(name)) {
            throw std::runtime_error("Branch name is empty or already exists.");
        }

        const Branch& source = requireBranch(from);
        branches.emplace(name, Branch{name, source.head, false, false});
    }

    void advanceFeatureHead(
        const std::string& branchName,
        const std::string& newHead
    ) {
        Branch& branch = requireBranch(branchName);
        if (branch.protectedBranch && !policyFor(branchName).allowDirectPush) {
            throw std::runtime_error("Direct push to protected branch is prohibited.");
        }
        if (newHead.empty() || newHead == branch.head) {
            throw std::invalid_argument("A new, non-empty head identifier is required.");
        }

        branch.head = newHead;
        for (auto& entry : pullRequests) {
            PullRequest& pr = entry.second;
            if (
                pr.sourceBranch == branchName &&
                (pr.state == PullRequestState::Open ||
                 pr.state == PullRequestState::Draft)
            ) {
                pr.sourceHead = newHead;
            }
        }
    }

    PullRequest& openPullRequest(
        int number,
        const std::string& author,
        const std::string& source,
        const std::string& target = "main",
        bool draft = true
    ) {
        if (number <= 0 || pullRequests.count(number)) {
            throw std::runtime_error("Pull Request number must be positive and unique.");
        }
        if (author.empty() || source == target) {
            throw std::invalid_argument("Invalid author or identical source and target.");
        }

        Branch& sourceBranch = requireBranch(source);
        Branch& targetBranch = requireBranch(target);

        PullRequest pr;
        pr.number = number;
        pr.author = author;
        pr.sourceBranch = source;
        pr.targetBranch = target;
        pr.sourceHead = sourceBranch.head;
        pr.baseHeadAtSync = targetBranch.head;
        pr.draft = draft;
        pr.state = draft ? PullRequestState::Draft : PullRequestState::Open;

        return pullRequests.emplace(number, std::move(pr)).first->second;
    }

    void markReady(int number) {
        PullRequest& pr = requirePR(number);
        if (pr.state != PullRequestState::Draft) {
            throw std::runtime_error("Only draft Pull Requests can become ready.");
        }
        pr.state = PullRequestState::Open;
        pr.draft = false;
    }

    void closePullRequest(int number) {
        PullRequest& pr = requirePR(number);
        if (pr.state != PullRequestState::Open &&
            pr.state != PullRequestState::Draft) {
            throw std::runtime_error("Only active Pull Requests can be closed.");
        }
        pr.state = PullRequestState::Closed;
    }

    void reopenPullRequest(int number) {
        PullRequest& pr = requirePR(number);
        if (pr.state != PullRequestState::Closed) {
            throw std::runtime_error("Only closed Pull Requests can be reopened.");
        }
        pr.state = PullRequestState::Open;
        pr.draft = false;
    }

    void submitReview(
        int number,
        const std::string& reviewerName,
        ReviewState state
    ) {
        PullRequest& pr = requirePR(number);
        auto reviewerIt = reviewers.find(reviewerName);

        if (reviewerIt == reviewers.end() ||
            !reviewerIt->second.active ||
            !reviewerIt->second.canReview) {
            throw std::runtime_error("Reviewer is not eligible.");
        }
        if (reviewerName == pr.author) {
            throw std::runtime_error("Pull Request authors cannot review their own changes.");
        }
        if (pr.state != PullRequestState::Open || pr.draft) {
            throw std::runtime_error("Reviews require an open, non-draft Pull Request.");
        }
        if (state == ReviewState::Dismissed) {
            throw std::invalid_argument("Use dismissReview for dismissal events.");
        }

        pr.reviews.push_back(
            Review{reviewerName, state, pr.sourceHead, ++reviewSequence}
        );
    }

    void dismissReview(int number, const std::string& reviewerName) {
        PullRequest& pr = requirePR(number);
        const auto latest = latestReviews(pr);
        auto it = latest.find(reviewerName);

        if (it == latest.end()) {
            throw std::runtime_error("No review exists for this reviewer.");
        }

        pr.reviews.push_back(
            Review{
                reviewerName,
                ReviewState::Dismissed,
                it->second.reviewedHead,
                ++reviewSequence
            }
        );
    }

    void recordCheck(int number, const std::string& name, CheckState state) {
        PullRequest& pr = requirePR(number);
        if (name.empty()) {
            throw std::invalid_argument("Status-check name cannot be empty.");
        }
        pr.checks.push_back(StatusCheck{name, pr.sourceHead, state});
    }

    void addReviewThread(int number, const std::string& id) {
        PullRequest& pr = requirePR(number);
        if (id.empty()) {
            throw std::invalid_argument("Thread identifier cannot be empty.");
        }

        auto existing = std::find_if(
            pr.threads.begin(),
            pr.threads.end(),
            [&](const ReviewThread& thread) { return thread.id == id; }
        );
        if (existing != pr.threads.end()) {
            throw std::runtime_error("Review thread already exists.");
        }

        pr.threads.push_back(ReviewThread{id, false});
    }

    void resolveReviewThread(int number, const std::string& id) {
        PullRequest& pr = requirePR(number);
        auto thread = std::find_if(
            pr.threads.begin(),
            pr.threads.end(),
            [&](const ReviewThread& item) { return item.id == id; }
        );
        if (thread == pr.threads.end()) {
            throw std::runtime_error("Review thread does not exist.");
        }
        thread->resolved = true;
    }

    MergeDecision evaluateMerge(
        int number,
        MergeStrategy strategy,
        const std::string& actor
    ) const {
        auto prIt = pullRequests.find(number);
        if (prIt == pullRequests.end()) {
            throw std::runtime_error("Pull Request does not exist.");
        }

        const PullRequest& pr = prIt->second;
        const Branch& source = branches.at(pr.sourceBranch);
        const Branch& target = branches.at(pr.targetBranch);
        const ProtectionPolicy policy = policyFor(pr.targetBranch);

        MergeDecision decision;
        auto addFailure = [&](const std::string& reason) {
            decision.reasons.push_back(reason);
        };

        if (pr.state != PullRequestState::Open || pr.draft) {
            addFailure("Pull Request must be open and ready.");
        }
        if (source.head != pr.sourceHead) {
            addFailure("Pull Request source head is not current.");
        }
        if (target.head != pr.baseHeadAtSync) {
            addFailure("Target branch advanced; synchronize the base branch.");
        }

        auto actorIt = reviewers.find(actor);
        const bool bypass =
            actorIt != reviewers.end() &&
            actorIt->second.active &&
            actorIt->second.administrator &&
            policy.allowAdminBypass;

        const auto latest = latestReviews(pr);
        for (const auto& entry : latest) {
            const Review& review = entry.second;
            auto reviewerIt = reviewers.find(entry.first);

            if (
                reviewerIt != reviewers.end() &&
                reviewerIt->second.active &&
                reviewerIt->second.canReview &&
                entry.first != pr.author &&
                review.state == ReviewState::Approved &&
                review.reviewedHead == pr.sourceHead
            ) {
                ++decision.approvals;
            }
        }

        if (!bypass) {
            if (decision.approvals < policy.minimumApprovals) {
                addFailure(
                    "Insufficient current approvals: " +
                    std::to_string(decision.approvals) + "/" +
                    std::to_string(policy.minimumApprovals)
                );
            }

            const bool changesRequested = std::any_of(
                latest.begin(),
                latest.end(),
                [&](const auto& entry) {
                    return entry.second.state == ReviewState::ChangesRequested &&
                           entry.second.reviewedHead == pr.sourceHead;
                }
            );
            if (changesRequested) {
                addFailure("A current review requests changes.");
            }

            for (const std::string& check : policy.requiredChecks) {
                if (!hasPassingCheck(pr, check)) {
                    addFailure("Required check has not passed: " + check);
                }
            }

            if (policy.requireConversationResolution) {
                const bool unresolved = std::any_of(
                    pr.threads.begin(),
                    pr.threads.end(),
                    [](const ReviewThread& thread) { return !thread.resolved; }
                );
                if (unresolved) {
                    addFailure("Review conversations must be resolved.");
                }
            }

            bool strategyAllowed = false;
            switch (strategy) {
                case MergeStrategy::MergeCommit:
                    strategyAllowed = policy.allowMergeCommit;
                    break;
                case MergeStrategy::Squash:
                    strategyAllowed = policy.allowSquash;
                    break;
                case MergeStrategy::Rebase:
                    strategyAllowed = policy.allowRebase;
                    break;
            }

            if (!strategyAllowed) {
                addFailure("Selected merge strategy is not permitted.");
            }
            if (
                policy.requireLinearHistory &&
                strategy == MergeStrategy::MergeCommit
            ) {
                addFailure("Merge commits violate the linear-history requirement.");
            }
        }

        decision.eligible = decision.reasons.empty();
        return decision;
    }

    std::string mergePullRequest(
        int number,
        MergeStrategy strategy,
        const std::string& actor
    ) {
        const MergeDecision decision = evaluateMerge(number, strategy, actor);

        if (!decision.eligible) {
            std::string message = "Merge blocked:";
            for (const std::string& reason : decision.reasons) {
                message += "\n - " + reason;
            }
            throw std::runtime_error(message);
        }

        PullRequest& pr = requirePR(number);
        Branch& source = requireBranch(pr.sourceBranch);
        Branch& target = requireBranch(pr.targetBranch);

        // These identifiers model resulting commits; no cryptographic object
        // IDs or Git pack files are produced by this governance example.
        const std::string mergeHead =
            "merge-" + std::to_string(number) + "-" + to_string(strategy);

        target.head = mergeHead;
        pr.state = PullRequestState::Merged;
        return mergeHead;
    }

    void directPush(
        const std::string& branchName,
        const std::string& newHead,
        bool force
    ) {
        Branch& branch = requireBranch(branchName);
        const ProtectionPolicy policy = policyFor(branchName);

        if (branch.protectedBranch) {
            if (policy.requirePullRequest || !policy.allowDirectPush) {
                throw std::runtime_error("Direct push is blocked by branch protection.");
            }
            if (force && !policy.allowForcePush) {
                throw std::runtime_error("Force push is blocked by branch protection.");
            }
        }

        if (newHead.empty()) {
            throw std::invalid_argument("New commit identifier is required.");
        }
        branch.head = newHead;
    }

    void deleteBranch(const std::string& branchName) {
        Branch& branch = requireBranch(branchName);
        if (branchName == "main") {
            throw std::runtime_error("The default branch cannot be deleted.");
        }

        const ProtectionPolicy policy = policyFor(branchName);
        if (branch.protectedBranch && policy.prohibitBranchDeletion) {
            throw std::runtime_error("Deletion of protected branch is blocked.");
        }

        branch.deleted = true;
    }

    const Branch& getBranch(const std::string& name) const {
        auto it = branches.find(name);
        if (it == branches.end() || it->second.deleted) {
            throw std::runtime_error("Branch does not exist.");
        }
        return it->second;
    }

    const PullRequest& getPullRequest(int number) const {
        auto it = pullRequests.find(number);
        if (it == pullRequests.end()) {
            throw std::runtime_error("Pull Request does not exist.");
        }
        return it->second;
    }
};

int main() {
    try {
        GovernanceEngine repository("commit-main-0001");

        repository.registerReviewer(Reviewer{"alice", true, true, true});
        repository.registerReviewer(Reviewer{"bob", true, true, false});
        repository.registerReviewer(Reviewer{"carol", true, true, false});
        repository.registerReviewer(Reviewer{"dave", true, false, false});

        ProtectionPolicy policy;
        policy.minimumApprovals = 2;
        policy.requiredChecks = {"unit-tests", "security-scan"};
        policy.requireConversationResolution = true;
        policy.requireLinearHistory = true;
        policy.allowMergeCommit = false;
        policy.allowSquash = true;
        policy.allowRebase = true;
        policy.allowDirectPush = false;
        policy.allowForcePush = false;
        policy.prohibitBranchDeletion = true;

        repository.protectBranch("main", policy);
        repository.createBranch("feature/payment-validation", "main");
        repository.advanceFeatureHead(
            "feature/payment-validation",
            "commit-feature-0002"
        );

        PullRequest& pr = repository.openPullRequest(
            105,
            "alice",
            "feature/payment-validation",
            "main",
            true
        );

        repository.markReady(pr.number);
        repository.addReviewThread(pr.number, "discussion-17");

        repository.submitReview(pr.number, "bob", ReviewState::Approved);
        repository.submitReview(pr.number, "carol", ReviewState::Approved);
        repository.recordCheck(pr.number, "unit-tests", CheckState::Passed);
        repository.recordCheck(pr.number, "security-scan", CheckState::Passed);

        // Source advancement invalidates approvals and checks tied to the old head.
        repository.advanceFeatureHead(
            "feature/payment-validation",
            "commit-feature-0003"
        );

        MergeDecision stale = repository.evaluateMerge(
            pr.number,
            MergeStrategy::Squash,
            "alice"
        );

        std::cout << "Eligibility after source update: "
                  << (stale.eligible ? "yes" : "no") << '\n';
        for (const std::string& reason : stale.reasons) {
            std::cout << " - " << reason << '\n';
        }

        repository.submitReview(pr.number, "bob", ReviewState::Approved);
        repository.submitReview(pr.number, "carol", ReviewState::Approved);
        repository.recordCheck(pr.number, "unit-tests", CheckState::Passed);
        repository.recordCheck(pr.number, "security-scan", CheckState::Passed);
        repository.resolveReviewThread(pr.number, "discussion-17");

        MergeDecision finalDecision = repository.evaluateMerge(
            pr.number,
            MergeStrategy::Squash,
            "alice"
        );

        std::cout << "\nFinal eligibility: "
                  << (finalDecision.eligible ? "yes" : "no") << '\n';
        std::cout << "Current approvals: " << finalDecision.approvals << '\n';

        if (finalDecision.eligible) {
            const std::string mergedHead = repository.mergePullRequest(
                pr.number,
                MergeStrategy::Squash,
                "alice"
            );
            std::cout << "Merged head: " << mergedHead << '\n';
            std::cout << "PR state: "
                      << to_string(repository.getPullRequest(pr.number).state)
                      << '\n';
        }

        try {
            repository.submitReview(pr.number, "dave", ReviewState::Approved);
        } catch (const std::exception& error) {
            std::cout << "\nExpected reviewer failure: " << error.what() << '\n';
        }

        try {
            repository.directPush("main", "unauthorized-head", false);
        } catch (const std::exception& error) {
            std::cout << "Expected branch-protection failure: "
                      << error.what() << '\n';
        }

        try {
            repository.deleteBranch("main");
        } catch (const std::exception& error) {
            std::cout << "Expected branch-deletion failure: "
                      << error.what() << '\n';
        }

    } catch (const std::exception& error) {
        std::cerr << "Repository workflow error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
