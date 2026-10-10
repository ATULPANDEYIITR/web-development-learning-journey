#include <algorithm>
#include <cctype>
#include <iostream>
#include <map>
#include <optional>
#include <set>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

using namespace std;

// A repository governance engine provides a realistic case study in object
// properties, member functions, nested objects, computed keys, and copying.

enum class ReviewState {
    Pending,
    Approved,
    ChangesRequested,
    Commented,
    Dismissed
};

enum class PullRequestState {
    Draft,
    Open,
    Merged,
    Closed
};

enum class MergeStrategy {
    MergeCommit,
    Squash,
    Rebase
};

string toString(ReviewState state) {
    switch (state) {
        case ReviewState::Pending: return "PENDING";
        case ReviewState::Approved: return "APPROVED";
        case ReviewState::ChangesRequested: return "CHANGES_REQUESTED";
        case ReviewState::Commented: return "COMMENTED";
        case ReviewState::Dismissed: return "DISMISSED";
    }
    throw logic_error("Unknown review state");
}

struct Reviewer {
    string username;
    bool active = true;
    bool eligible = true;

    void validate() const {
        if (username.empty()) {
            throw invalid_argument("Reviewer username cannot be empty");
        }
    }
};

struct ReviewComment {
    string filePath;
    size_t line;
    string body;
    bool resolved = false;

    void validate() const {
        if (filePath.empty()) {
            throw invalid_argument("Review comment requires a file path");
        }
        if (line == 0) {
            throw invalid_argument("Review comment lines are one-based");
        }
        if (body.empty()) {
            throw invalid_argument("Review comment cannot be empty");
        }
    }
};

struct Review {
    Reviewer reviewer;
    ReviewState state;
    vector<ReviewComment> comments;
    string commitSha;

    void validate() const {
        reviewer.validate();
        if (commitSha.empty()) {
            throw invalid_argument("A review must identify the reviewed commit");
        }
        for (const auto& comment : comments) {
            comment.validate();
        }
    }
};

struct BranchProtection {
    string branchName;
    size_t requiredApprovals = 1;
    set<string> requiredChecks;
    bool requireConversationResolution = true;
    bool requireLinearHistory = false;
    bool allowDirectPush = false;
    bool allowForcePush = false;
    bool allowDeletion = false;
    bool dismissStaleApprovals = true;
    bool administratorsMustComply = true;

    void validate() const {
        if (branchName.empty()) {
            throw invalid_argument("Protected branch name cannot be empty");
        }
    }
};

struct PullRequest {
    int number;
    string title;
    string sourceBranch;
    string targetBranch;
    string headSha;
    string baseSha;
    PullRequestState state = PullRequestState::Open;
    bool draft = false;
    bool hasConflicts = false;
    map<string, bool> statusChecks;
    vector<Review> reviews;
    vector<ReviewComment> generalComments;
    set<string> requestedReviewers;

    // Computed properties derive values from current state.
    bool isOpen() const {
        return state == PullRequestState::Open;
    }

    string displayId(const string& repository) const {
        return repository + "#" + to_string(number);
    }

    void requestReview(const Reviewer& reviewer) {
        reviewer.validate();
        if (!reviewer.active || !reviewer.eligible) {
            throw invalid_argument("Reviewer is inactive or ineligible");
        }
        if (!isOpen()) {
            throw logic_error("Review requests require an open pull request");
        }
        requestedReviewers.insert(reviewer.username);
    }

    void submitReview(Review review) {
        review.validate();
        if (!isOpen()) {
            throw logic_error("Cannot submit a review to a non-open request");
        }
        if (review.reviewer.username.empty()) {
            throw invalid_argument("Reviewer is required");
        }

        // A new review by the same reviewer supersedes that reviewer's
        // previous current decision for this simplified policy model.
        reviews.erase(
            remove_if(reviews.begin(), reviews.end(),
                [&](const Review& oldReview) {
                    return oldReview.reviewer.username ==
                           review.reviewer.username;
                }),
            reviews.end()
        );

        requestedReviewers.erase(review.reviewer.username);
        reviews.push_back(move(review));
    }

    void synchronizeBase(const string& newBaseSha) {
        if (!isOpen()) {
            throw logic_error("Only open pull requests can be synchronized");
        }
        if (newBaseSha.empty()) {
            throw invalid_argument("Base commit cannot be empty");
        }
        if (newBaseSha != baseSha) {
            baseSha = newBaseSha;
            if (headSha.empty()) {
                throw logic_error("Pull request head commit is missing");
            }
            if (newBaseSha != baseSha) {
                throw logic_error("Unexpected synchronization state");
            }
            // This model uses the head SHA as the reviewed change version.
            // Base changes invalidate approvals when the policy requires it.
        }
    }
};

struct MergeDecision {
    bool eligible = false;
    vector<string> blockers;
    string summary() const {
        if (eligible) {
            return "Eligible to merge";
        }
        string result = "Blocked:";
        for (const auto& blocker : blockers) {
            result += "\n  - " + blocker;
        }
        return result;
    }
};

class GovernanceEngine {
public:
    MergeDecision evaluate(
        const PullRequest& pr,
        const BranchProtection& policy,
        const string& currentHeadSha
    ) const {
        MergeDecision decision;

        if (!pr.isOpen()) {
            decision.blockers.push_back("Pull request is not open");
        }
        if (pr.draft) {
            decision.blockers.push_back("Draft pull request cannot be merged");
        }
        if (pr.hasConflicts) {
            decision.blockers.push_back("Merge conflicts must be resolved");
        }
        if (pr.sourceBranch == pr.targetBranch) {
            decision.blockers.push_back("Source and target branches must differ");
        }
        if (pr.targetBranch != policy.branchName) {
            decision.blockers.push_back("Target does not match protected branch");
        }
        if (pr.headSha != currentHeadSha) {
            decision.blockers.push_back("Pull request head is stale");
        }

        for (const auto& checkName : policy.requiredChecks) {
            const auto check = pr.statusChecks.find(checkName);
            if (check == pr.statusChecks.end() || !check->second) {
                decision.blockers.push_back(
                    "Required check missing or failing: " + checkName
                );
            }
        }

        size_t approvals = 0;
        bool changesRequested = false;

        for (const auto& review : pr.reviews) {
            if (review.commitSha != currentHeadSha &&
                policy.dismissStaleApprovals) {
                continue;
            }

            if (!review.reviewer.active || !review.reviewer.eligible) {
                continue;
            }

            if (review.state == ReviewState::Approved) {
                ++approvals;
            }
            if (review.state == ReviewState::ChangesRequested) {
                changesRequested = true;
            }
        }

        if (approvals < policy.requiredApprovals) {
            decision.blockers.push_back(
                "Insufficient eligible approvals: " +
                to_string(approvals) + "/" +
                to_string(policy.requiredApprovals)
            );
        }

        if (changesRequested) {
            decision.blockers.push_back(
                "An eligible reviewer has requested changes"
            );
        }

        if (policy.requireConversationResolution) {
            for (const auto& comment : pr.generalComments) {
                if (!comment.resolved) {
                    decision.blockers.push_back(
                        "Unresolved review conversation at " + comment.filePath
                    );
                }
            }

            for (const auto& review : pr.reviews) {
                for (const auto& comment : review.comments) {
                    if (!comment.resolved) {
                        decision.blockers.push_back(
                            "Unresolved inline discussion at " + comment.filePath
                        );
                    }
                }
            }
        }

        decision.eligible = decision.blockers.empty();
        return decision;
    }

    void merge(
        PullRequest& pr,
        const BranchProtection& policy,
        const string& currentHeadSha,
        MergeStrategy strategy
    ) const {
        const MergeDecision decision = evaluate(pr, policy, currentHeadSha);
        if (!decision.eligible) {
            throw logic_error(decision.summary());
        }

        if (strategy == MergeStrategy::Rebase && !policy.requireLinearHistory) {
            // Rebase is still allowed here; linear-history protection is
            // a constraint on the resulting history, not a forced strategy.
        }

        pr.state = PullRequestState::Merged;
    }
};

int main() {
    try {
        BranchProtection policy;
        policy.branchName = "main";
        policy.requiredApprovals = 2;
        policy.requiredChecks = {"unit-tests", "security-scan"};
        policy.requireConversationResolution = true;
        policy.dismissStaleApprovals = true;
        policy.validate();

        PullRequest pr{
            204,
            "Harden webhook authentication",
            "feature/webhook-auth",
            "main",
            "commit-9af2",
            "base-70bd"
        };

        pr.statusChecks["unit-tests"] = true;
        pr.statusChecks["security-scan"] = true;

        Reviewer reviewerA{"mira", true, true};
        Reviewer reviewerB{"lee", true, true};

        pr.requestReview(reviewerA);
        pr.requestReview(reviewerB);

        pr.submitReview(Review{
            reviewerA,
            ReviewState::Approved,
            {ReviewComment{
                "src/webhook.cpp", 88,
                "Signature verification now rejects missing headers.",
                true
            }},
            "commit-9af2"
        });

        pr.submitReview(Review{
            reviewerB,
            ReviewState::Approved,
            {},
            "commit-9af2"
        });

        pr.generalComments.push_back(ReviewComment{
            "README.md", 35,
            "Document the key rotation procedure.",
            false
        });

        GovernanceEngine engine;

        cout << pr.displayId("platform/payments") << '\n';
        cout << engine.evaluate(pr, policy, "commit-9af2").summary() << '\n';

        // Resolving a conversation changes merge eligibility without
        // changing the approval records.
        pr.generalComments.front().resolved = true;
        cout << "\nAfter resolving the conversation:\n";
        cout << engine.evaluate(pr, policy, "commit-9af2").summary() << '\n';

        // New commits make earlier approvals stale under this policy.
        pr.headSha = "commit-c3d1";
        cout << "\nAfter a new source commit:\n";
        cout << engine.evaluate(pr, policy, "commit-c3d1").summary() << '\n';

        // Review the new commit before attempting the merge.
        pr.submitReview(Review{
            reviewerA, ReviewState::Approved, {}, "commit-c3d1"
        });
        pr.submitReview(Review{
            reviewerB, ReviewState::Approved, {}, "commit-c3d1"
        });

        engine.merge(pr, policy, "commit-c3d1", MergeStrategy::Squash);
        cout << "\nFinal pull request state: "
             << (pr.state == PullRequestState::Merged ? "MERGED" : "NOT MERGED")
             << '\n';

        // Computed object properties can be represented by map lookups.
        map<string, string> metadata{
            {"owner", "platform"},
            {"defaultBranch", "main"}
        };
        const string propertyName = "defaultBranch";
        const auto property = metadata.find(propertyName);

        if (property != metadata.end()) {
            cout << "Computed property [" << propertyName << "] = "
                 << property->second << '\n';
        }

    } catch (const exception& error) {
        cerr << "Governance error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
