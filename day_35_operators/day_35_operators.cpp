#include <algorithm>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <stdexcept>
#include <string>
#include <vector>

/*
 * Repository Governance Case Study
 *
 * The system evaluates whether a Pull Request targeting a protected branch
 * can be merged. Operators are used to express arithmetic limits, comparisons,
 * logical policy composition, assignments, and conditional decisions.
 *
 * C++17 is used so std::optional can represent values that may be absent.
 */

enum class ReviewState {
    Pending,
    Approved,
    ChangesRequested,
    Commented
};

enum class CheckState {
    Pending,
    Passed,
    Failed
};

struct Reviewer {
    std::string username;
    bool eligible;
};

struct Review {
    Reviewer reviewer;
    ReviewState state;
    std::vector<std::string> comments;
};

struct PullRequest {
    int number;
    std::string sourceBranch;
    std::string targetBranch;
    int additions;
    int deletions;
    bool draft;
    bool mergeable;
    std::vector<Review> reviews;
    std::map<std::string, CheckState> statusChecks;
};

struct BranchProtection {
    std::string branchName;
    int requiredApprovals;
    int maximumChangedFiles;
    bool requirePassingChecks;
    bool requireConversationResolution;
    bool allowForcePush;
    bool allowDirectPush;
};

class MergeEligibilityEngine {
public:
    explicit MergeEligibilityEngine(BranchProtection policy)
        : policy_(std::move(policy)) {}

    bool canMerge(const PullRequest& pr) const {
        const int changedLines = pr.additions + pr.deletions;

        const bool branchProtected =
            pr.targetBranch == policy_.branchName;

        const bool sizeAllowed =
            changedLines <= policy_.maximumChangedFiles;

        const bool approvalsSatisfied =
            countCurrentApprovals(pr) >= policy_.requiredApprovals;

        const bool checksSatisfied =
            !policy_.requirePassingChecks || allChecksPassed(pr);

        const bool conversationsSatisfied =
            !policy_.requireConversationResolution ||
            allConversationsResolved(pr);

        /*
         * Each condition represents a separate governance rule. Combining
         * them with && prevents one successful condition from bypassing
         * another mandatory rule.
         */
        return branchProtected &&
               !pr.draft &&
               pr.mergeable &&
               sizeAllowed &&
               approvalsSatisfied &&
               checksSatisfied &&
               conversationsSatisfied;
    }

    std::vector<std::string> explain(const PullRequest& pr) const {
        std::vector<std::string> failures;

        const int changedLines = pr.additions + pr.deletions;

        if (pr.targetBranch != policy_.branchName) {
            failures.push_back("Pull Request targets an unprotected branch");
        }

        if (pr.draft) {
            failures.push_back("Pull Request is still a draft");
        }

        if (!pr.mergeable) {
            failures.push_back("Pull Request currently has a merge conflict");
        }

        if (changedLines > policy_.maximumChangedFiles) {
            failures.push_back("Change exceeds the configured size limit");
        }

        if (countCurrentApprovals(pr) < policy_.requiredApprovals) {
            failures.push_back("Required approval count has not been reached");
        }

        if (policy_.requirePassingChecks && !allChecksPassed(pr)) {
            failures.push_back("At least one required status check has not passed");
        }

        if (policy_.requireConversationResolution &&
            !allConversationsResolved(pr)) {
            failures.push_back("An inline review conversation remains unresolved");
        }

        return failures;
    }

private:
    BranchProtection policy_;

    static bool isApproval(const Review& review) {
        return review.reviewer.eligible &&
               review.state == ReviewState::Approved;
    }

    static int countCurrentApprovals(const PullRequest& pr) {
        int count = 0;

        for (const Review& review : pr.reviews) {
            if (isApproval(review)) {
                ++count;
            }
        }

        return count;
    }

    static bool allChecksPassed(const PullRequest& pr) {
        if (pr.statusChecks.empty()) {
            return false;
        }

        return std::all_of(
            pr.statusChecks.begin(),
            pr.statusChecks.end(),
            [](const auto& entry) {
                return entry.second == CheckState::Passed;
            });
    }

    static bool allConversationsResolved(const PullRequest& pr) {
        /*
         * For this case study, a review comment containing "[unresolved]"
         * represents an active discussion. Real systems would normally store
         * an explicit resolution state rather than encode it in text.
         */
        for (const Review& review : pr.reviews) {
            for (const std::string& comment : review.comments) {
                if (comment.find("[unresolved]") != std::string::npos) {
                    return false;
                }
            }
        }

        return true;
    }
};

std::string mergeDecision(bool eligible) {
    return eligible ? "MERGE ALLOWED" : "MERGE BLOCKED";
}

void printEvaluation(
    const PullRequest& pr,
    const MergeEligibilityEngine& engine) {

    std::cout << "\nPull Request #" << pr.number << "\n";
    std::cout << "Source: " << pr.sourceBranch
              << " -> Target: " << pr.targetBranch << "\n";

    const bool eligible = engine.canMerge(pr);

    std::cout << "Decision: " << mergeDecision(eligible) << "\n";

    const auto failures = engine.explain(pr);

    if (failures.empty()) {
        std::cout << "All configured governance conditions are satisfied.\n";
    } else {
        for (const auto& failure : failures) {
            std::cout << "Blocked by: " << failure << "\n";
        }
    }
}

int main() {
    BranchProtection mainPolicy{
        "main",
        2,
        500,
        true,
        true,
        false,
        false
    };

    MergeEligibilityEngine engine(mainPolicy);

    PullRequest healthy{
        101,
        "feature/payment-timeout",
        "main",
        120,
        80,
        false,
        true,
        {
            {
                {"reviewer-alice", true},
                ReviewState::Approved,
                {}
            },
            {
                {"reviewer-bob", true},
                ReviewState::Approved,
                {}
            },
            {
                {"external-contributor", false},
                ReviewState::Approved,
                {}
            }
        },
        {
            {"unit-tests", CheckState::Passed},
            {"security-scan", CheckState::Passed},
            {"build", CheckState::Passed}
        }
    };

    PullRequest blockedByReview{
        102,
        "feature/audit-log",
        "main",
        50,
        25,
        false,
        true,
        {
            {
                {"reviewer-alice", true},
                ReviewState::Approved,
                {"Audit logging structure looks correct."}
            },
            {
                {"reviewer-bob", true},
                ReviewState::ChangesRequested,
                {"[unresolved] Validate retention policy."}
            }
        },
        {
            {"unit-tests", CheckState::Passed},
            {"security-scan", CheckState::Passed},
            {"build", CheckState::Passed}
        }
    };

    PullRequest blockedByChecks{
        103,
        "feature/search-index",
        "main",
        180,
        130,
        false,
        true,
        {
            {
                {"reviewer-alice", true},
                ReviewState::Approved,
                {}
            },
            {
                {"reviewer-bob", true},
                ReviewState::Approved,
                {}
            }
        },
        {
            {"unit-tests", CheckState::Passed},
            {"security-scan", CheckState::Failed},
            {"build", CheckState::Passed}
        }
    };

    PullRequest draftRequest{
        104,
        "feature/reporting",
        "main",
        40,
        20,
        true,
        true,
        {
            {
                {"reviewer-alice", true},
                ReviewState::Approved,
                {}
            },
            {
                {"reviewer-bob", true},
                ReviewState::Approved,
                {}
            }
        },
        {
            {"unit-tests", CheckState::Passed}
        }
    };

    printEvaluation(healthy, engine);
    printEvaluation(blockedByReview, engine);
    printEvaluation(blockedByChecks, engine);
    printEvaluation(draftRequest, engine);

    // std::optional models a nullable configuration value without using
    // a magic sentinel such as -1.
    std::optional<int> optionalApprovalLimit;
    const int effectiveLimit = optionalApprovalLimit.value_or(2);

    std::cout << "\nOptional approval limit: " << effectiveLimit << "\n";

    // Assignment through a mutable policy object demonstrates that governance
    // configuration is data and can be changed deliberately.
    BranchProtection emergencyPolicy = mainPolicy;
    emergencyPolicy.requiredApprovals = 1;
    emergencyPolicy.requireConversationResolution = false;

    MergeEligibilityEngine emergencyEngine(emergencyPolicy);

    std::cout << "Emergency policy decision for PR #102: "
              << mergeDecision(emergencyEngine.canMerge(blockedByReview))
              << "\n";

    return 0;
}
