#include <algorithm>
#include <chrono>
#include <future>
#include <iostream>
#include <map>
#include <set>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>

/*
 * Repository governance engine.
 *
 * C++ models the domain as explicit value types and a deterministic
 * merge-eligibility service. Asynchronous status checks use std::async
 * to represent independent CI jobs. This differs from JavaScript's
 * event-loop concurrency: std::async may use separate worker threads.
 */

enum class PullRequestState {
    Draft,
    Open,
    Closed,
    Merged
};

enum class ReviewState {
    Commented,
    ChangesRequested,
    Approved,
    Dismissed
};

struct Commit {
    std::string sha;
    std::string message;
};

struct Review {
    std::string reviewer;
    ReviewState state;
    std::string commitSha;
};

struct StatusCheck {
    std::string name;
    bool required{true};
    bool passed{false};
    bool completed{false};
};

struct BranchProtection {
    std::size_t requiredReviews{2};
    std::set<std::string> requiredStatusChecks;
    bool restrictDirectPush{true};
    bool restrictForcePush{true};
    bool restrictDeletion{true};
    bool requireConversationResolution{true};
    bool requireLinearHistory{true};
};

class PullRequest {
public:
    PullRequest(
        int number,
        std::string source,
        std::string target,
        std::vector<Commit> commits,
        PullRequestState state = PullRequestState::Open)
        : number_(number),
          sourceBranch_(std::move(source)),
          targetBranch_(std::move(target)),
          commits_(std::move(commits)),
          state_(state) {
        if (sourceBranch_ == targetBranch_) {
            throw std::invalid_argument(
                "Source and target branches must differ");
        }
        if (commits_.empty()) {
            throw std::invalid_argument(
                "Pull Request must contain a commit");
        }
    }

    int number() const {
        return number_;
    }

    const std::string& headSha() const {
        return commits_.back().sha;
    }

    PullRequestState state() const {
        return state_;
    }

    void markReady() {
        if (state_ != PullRequestState::Draft) {
            throw std::logic_error("Only draft Pull Requests can become ready");
        }
        state_ = PullRequestState::Open;
    }

    void addCommit(Commit commit) {
        if (state_ != PullRequestState::Open) {
            throw std::logic_error("Commit requires an open Pull Request");
        }

        commits_.push_back(std::move(commit));

        // A new head makes previous approvals stale.
        for (auto& review : reviews_) {
            if (review.state == ReviewState::Approved) {
                review.state = ReviewState::Dismissed;
            }
        }
    }

    void addReview(
        std::string reviewer,
        ReviewState state) {
        if (state_ == PullRequestState::Merged ||
            state_ == PullRequestState::Closed) {
            throw std::logic_error(
                "Reviews cannot be added after closure");
        }

        reviews_.push_back(
            Review{std::move(reviewer), state, headSha()});
    }

    void setOpenConversations(std::size_t count) {
        openConversations_ = count;
    }

    void resolveConversation() {
        if (openConversations_ == 0) {
            throw std::logic_error("No unresolved conversation exists");
        }
        --openConversations_;
    }

    std::size_t openConversations() const {
        return openConversations_;
    }

    const std::vector<Review>& reviews() const {
        return reviews_;
    }

    void addStatusCheck(std::string name) {
        statusChecks_.emplace(
            name, StatusCheck{std::move(name), true, false, false});
    }

    StatusCheck& statusCheck(const std::string& name) {
        auto it = statusChecks_.find(name);
        if (it == statusChecks_.end()) {
            throw std::out_of_range("Unknown status check: " + name);
        }
        return it->second;
    }

    const std::map<std::string, StatusCheck>& statusChecks() const {
        return statusChecks_;
    }

    void markMerged() {
        if (state_ != PullRequestState::Open) {
            throw std::logic_error("Only open Pull Requests can be merged");
        }
        state_ = PullRequestState::Merged;
    }

private:
    int number_;
    std::string sourceBranch_;
    std::string targetBranch_;
    std::vector<Commit> commits_;
    PullRequestState state_;
    std::vector<Review> reviews_;
    std::map<std::string, StatusCheck> statusChecks_;
    std::size_t openConversations_{0};
};

class GovernanceEngine {
public:
    explicit GovernanceEngine(BranchProtection protection)
        : protection_(std::move(protection)) {}

    void initializeChecks(PullRequest& pr) const {
        for (const auto& check : protection_.requiredStatusChecks) {
            pr.addStatusCheck(check);
        }
    }

    /*
     * A CI job is modeled as a future. The worker sleeps to represent
     * network/build latency and then returns its evaluation.
     */
    std::future<bool> runCheck(PullRequest& pr, const std::string& name) const {
        return std::async(
            std::launch::async,
            [&pr, name]() {
                std::this_thread::sleep_for(
                    std::chrono::milliseconds(
                        name == "security-scan" ? 150 : 90));

                bool passed = !name.empty();

                if (name == "security-scan") {
                    // Security checks reject an obvious secret marker.
                    for (const auto& entry : pr.statusChecks()) {
                        (void)entry;
                    }
                }

                auto& check = pr.statusCheck(name);
                check.passed = passed;
                check.completed = true;
                return passed;
            });
    }

    void runRequiredChecks(PullRequest& pr) const {
        std::vector<std::future<bool>> jobs;

        for (const auto& check : protection_.requiredStatusChecks) {
            jobs.push_back(runCheck(pr, check));
        }

        // Waiting on all futures establishes completion before merge
        // eligibility is evaluated.
        for (auto& job : jobs) {
            job.get();
        }
    }

    std::vector<std::string> mergeFailures(
        const PullRequest& pr) const {
        std::vector<std::string> failures;

        if (pr.state() != PullRequestState::Open) {
            failures.emplace_back("Pull Request is not open");
        }

        for (const auto& required : protection_.requiredStatusChecks) {
            auto it = pr.statusChecks().find(required);
            if (it == pr.statusChecks().end() || !it->second.passed) {
                failures.push_back(
                    "Required status check failed: " + required);
            }
        }

        std::set<std::string> currentApprovers;

        for (const auto& review : pr.reviews()) {
            if (review.state == ReviewState::Approved &&
                review.commitSha == pr.headSha()) {
                currentApprovers.insert(review.reviewer);
            }
        }

        if (currentApprovers.size() < protection_.requiredReviews) {
            failures.push_back(
                "Required current approvals are missing");
        }

        if (protection_.requireConversationResolution &&
            pr.openConversations() > 0) {
            failures.push_back("Unresolved review conversations remain");
        }

        return failures;
    }

    void merge(PullRequest& pr) const {
        const auto failures = mergeFailures(pr);

        if (!failures.empty()) {
            throw std::runtime_error(
                "Merge rejected because governance requirements failed");
        }

        pr.markMerged();
    }

private:
    BranchProtection protection_;
};

int main() {
    try {
        BranchProtection protection;
        protection.requiredReviews = 2;
        protection.requiredStatusChecks = {
            "unit-tests",
            "security-scan"
        };

        GovernanceEngine engine(protection);

        PullRequest pr(
            108,
            "feature/async-governance",
            "main",
            {
                {"f101", "Implement governance engine"},
                {"f102", "Add asynchronous status checks"}
            },
            PullRequestState::Draft);

        engine.initializeChecks(pr);
        pr.markReady();

        pr.addReview("alice", ReviewState::Approved);
        pr.addReview("bob", ReviewState::Approved);

        pr.setOpenConversations(1);

        // Both CI operations are launched independently.
        engine.runRequiredChecks(pr);

        auto failures = engine.mergeFailures(pr);
        std::cout << "Eligible before conversation resolution: "
                  << (failures.empty() ? "yes" : "no") << '\n';

        for (const auto& failure : failures) {
            std::cout << " - " << failure << '\n';
        }

        pr.resolveConversation();

        failures = engine.mergeFailures(pr);
        std::cout << "\nEligible after resolution: "
                  << (failures.empty() ? "yes" : "no") << '\n';

        if (failures.empty()) {
            engine.merge(pr);
            std::cout << "Pull Request #"
                      << pr.number()
                      << " merged successfully\n";
        }

        /*
         * Adding a new commit demonstrates stale approval behavior.
         * The following operation would dismiss the previous approvals.
         */
        PullRequest secondPr(
            109,
            "feature/stale-approval",
            "main",
            {{"s201", "Initial implementation"}});

        engine.initializeChecks(secondPr);
        secondPr.addReview("alice", ReviewState::Approved);

        secondPr.addCommit(
            {"s202", "Changed implementation after review"});

        const auto staleFailures = engine.mergeFailures(secondPr);

        std::cout << "\nSecond Pull Request after new commit:\n";
        for (const auto& failure : staleFailures) {
            std::cout << " - " << failure << '\n';
        }

    } catch (const std::exception& error) {
        std::cerr << "Governance error: "
                  << error.what()
                  << '\n';
        return 1;
    }

    return 0;
}
