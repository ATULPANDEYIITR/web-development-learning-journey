#include <algorithm>
#include <cctype>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <regex>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;

enum class CheckState {
    Pending,
    Passed,
    Failed
};

enum class ReviewState {
    Pending,
    Approved,
    ChangesRequested,
    Commented
};

enum class PullRequestState {
    Draft,
    Open,
    Merged,
    Closed
};

struct StatusCheck {
    string name;
    CheckState state;
};

struct Review {
    string reviewer;
    ReviewState state;
    string comment;
};

struct PullRequest {
    int id;
    string title;
    string sourceBranch;
    string targetBranch;
    PullRequestState state;
    vector<string> commits;
    vector<Review> reviews;
    vector<StatusCheck> checks;
    bool conversationsResolved;
};

struct BranchPolicy {
    string branchName;
    int requiredApprovals;
    set<string> requiredChecks;
    set<string> allowedReviewers;
    bool requireResolvedConversations;
    bool restrictDirectPushes;
    bool prohibitForcePushes;
    bool prohibitDeletion;
    bool requireLinearHistory;
};

struct EligibilityResult {
    bool eligible;
    vector<string> blockers;
};

class RepositoryGovernance {
private:
    BranchPolicy policy;

    static bool containsMergeCommit(const PullRequest& pr) {
        // This simplified model marks commits with an explicit merge prefix.
        return any_of(pr.commits.begin(), pr.commits.end(),
                      [](const string& commit) {
                          return commit.rfind("MERGE:", 0) == 0;
                      });
    }

public:
    explicit RepositoryGovernance(BranchPolicy configuredPolicy)
        : policy(std::move(configuredPolicy)) {
        if (policy.requiredApprovals < 0) {
            throw invalid_argument("Required approval count cannot be negative");
        }
    }

    EligibilityResult evaluate(const PullRequest& pr) const {
        EligibilityResult result{true, {}};

        auto block = [&](const string& reason) {
            result.eligible = false;
            result.blockers.push_back(reason);
        };

        if (pr.state == PullRequestState::Draft) {
            block("Draft pull requests cannot be merged");
        } else if (pr.state == PullRequestState::Closed) {
            block("Closed pull request must be reopened before merging");
        } else if (pr.state == PullRequestState::Merged) {
            block("Pull request has already been merged");
        }

        if (pr.targetBranch != policy.branchName) {
            block("Target branch does not match the protected branch");
        }

        if (pr.sourceBranch.empty() || pr.targetBranch.empty()) {
            block("Source and target branches must be specified");
        }

        if (pr.sourceBranch == pr.targetBranch) {
            block("Source and target branches must differ");
        }

        if (pr.commits.empty()) {
            block("Pull request contains no commits");
        }

        if (policy.requireLinearHistory && containsMergeCommit(pr)) {
            block("Merge commits violate the linear-history policy");
        }

        if (policy.requireResolvedConversations && !pr.conversationsResolved) {
            block("Review conversations remain unresolved");
        }

        // The latest submitted review by each reviewer determines that
        // reviewer's current state. A later review replaces an earlier one.
        map<string, ReviewState> latestReview;
        for (const Review& review : pr.reviews) {
            if (review.reviewer.empty()) {
                continue;
            }

            if (policy.allowedReviewers.count(review.reviewer) == 0) {
                block("Review submitted by ineligible reviewer: " + review.reviewer);
                continue;
            }

            latestReview[review.reviewer] = review.state;
        }

        int approvals = 0;
        bool changesRequested = false;

        for (const auto& entry : latestReview) {
            if (entry.second == ReviewState::Approved) {
                ++approvals;
            } else if (entry.second == ReviewState::ChangesRequested) {
                changesRequested = true;
            }
        }

        if (approvals < policy.requiredApprovals) {
            block("Insufficient approvals: " + to_string(approvals) +
                  " of " + to_string(policy.requiredApprovals));
        }

        if (changesRequested) {
            block("At least one latest review requests changes");
        }

        map<string, CheckState> latestChecks;
        for (const StatusCheck& check : pr.checks) {
            latestChecks[check.name] = check.state;
        }

        for (const string& required : policy.requiredChecks) {
            auto found = latestChecks.find(required);
            if (found == latestChecks.end()) {
                block("Required status check is missing: " + required);
            } else if (found->second != CheckState::Passed) {
                block("Required status check is not passing: " + required);
            }
        }

        return result;
    }

    bool canDirectPush() const {
        return !policy.restrictDirectPushes;
    }

    bool canForcePush() const {
        return !policy.prohibitForcePushes;
    }

    bool canDeleteBranch() const {
        return !policy.prohibitDeletion;
    }
};

string toString(PullRequestState state) {
    switch (state) {
        case PullRequestState::Draft: return "Draft";
        case PullRequestState::Open: return "Open";
        case PullRequestState::Merged: return "Merged";
        case PullRequestState::Closed: return "Closed";
    }
    return "Unknown";
}

void printEligibility(const PullRequest& pr, const EligibilityResult& result) {
    cout << "\nPR #" << pr.id << ": " << pr.title
         << " [" << toString(pr.state) << "]\n";

    if (result.eligible) {
        cout << "Merge eligible under the configured policy.\n";
        return;
    }

    cout << "Merge blocked:\n";
    for (const string& blocker : result.blockers) {
        cout << "  - " << blocker << '\n';
    }
}

optional<string> validatePullRequestTitle(const string& title) {
    // Keep validation bounded and use a simple expression for predictable cost.
    static const regex titlePattern(R"([A-Za-z0-9][A-Za-z0-9 :._-]{4,119})");

    if (!regex_match(title, titlePattern)) {
        return "Title must contain 5-120 permitted characters and start with a letter or digit";
    }

    return nullopt;
}

int main() {
    try {
        cout << "Repository Governance and Merge Eligibility Engine\n";

        BranchPolicy mainPolicy{
            "main",
            2,
            {"build", "unit-tests", "security-scan"},
            {"reviewer-ana", "reviewer-raj", "reviewer-meera"},
            true,
            true,
            true,
            true,
            true
        };

        RepositoryGovernance governance(mainPolicy);

        vector<PullRequest> requests{
            {
                184,
                "Improve supplier validation",
                "feature/supplier-validation",
                "main",
                PullRequestState::Open,
                {"a1b2c3", "d4e5f6"},
                {
                    {"reviewer-ana", ReviewState::Approved, "Validation is clear"},
                    {"reviewer-raj", ReviewState::Approved, "Tests cover invalid records"}
                },
                {
                    {"build", CheckState::Passed},
                    {"unit-tests", CheckState::Passed},
                    {"security-scan", CheckState::Passed}
                },
                true
            },
            {
                185,
                "Change payment callback handling",
                "feature/payment-callback",
                "main",
                PullRequestState::Open,
                {"b2c3d4"},
                {
                    {"reviewer-ana", ReviewState::Approved, "Initial review"},
                    {"reviewer-ana", ReviewState::ChangesRequested,
                     "Recheck signature verification"},
                    {"reviewer-meera", ReviewState::Approved, "Other changes are sound"}
                },
                {
                    {"build", CheckState::Passed},
                    {"unit-tests", CheckState::Failed},
                    {"security-scan", CheckState::Passed}
                },
                false
            },
            {
                186,
                "Document supplier API contract",
                "docs/supplier-api",
                "main",
                PullRequestState::Draft,
                {"c3d4e5"},
                {},
                {
                    {"build", CheckState::Passed},
                    {"unit-tests", CheckState::Passed},
                    {"security-scan", CheckState::Passed}
                },
                true
            },
            {
                187,
                "Refactor approval workflow",
                "feature/approval-workflow",
                "main",
                PullRequestState::Open,
                {"MERGE:branch-sync", "e4f5a6"},
                {
                    {"reviewer-ana", ReviewState::Approved, "Reviewed"},
                    {"reviewer-raj", ReviewState::Approved, "Reviewed"}
                },
                {
                    {"build", CheckState::Passed},
                    {"unit-tests", CheckState::Passed},
                    {"security-scan", CheckState::Passed}
                },
                true
            }
        };

        for (const PullRequest& pr : requests) {
            const optional<string> titleError = validatePullRequestTitle(pr.title);
            if (titleError) {
                cout << "PR #" << pr.id << " rejected: " << *titleError << '\n';
                continue;
            }

            printEligibility(pr, governance.evaluate(pr));
        }

        cout << "\nProtected branch capabilities\n";
        cout << boolalpha;
        cout << "Direct push allowed: " << governance.canDirectPush() << '\n';
        cout << "Force push allowed: " << governance.canForcePush() << '\n';
        cout << "Branch deletion allowed: " << governance.canDeleteBranch() << '\n';

        cout << "\nEdge case: invalid approval configuration\n";
        try {
            BranchPolicy invalidPolicy{
                "main", -1, {}, {}, true, true, true, true, true
            };
            RepositoryGovernance invalidGovernance(invalidPolicy);
        } catch (const invalid_argument& error) {
            cout << "Configuration rejected: " << error.what() << '\n';
        }

        cout << "\nPolicy limitation\n";
        cout << "This in-memory model does not verify commit ancestry, "
             << "signed commits, or live CI identities. Production systems "
             << "must obtain those facts from trusted repository services.\n";
    } catch (const exception& error) {
        cerr << "Fatal error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
