#include <algorithm>
#include <cmath>
#include <exception>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <set>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

/*
 * Repository governance and merge-eligibility engine.
 *
 * The system evaluates errors in repository change workflows. It distinguishes
 * invalid requests, unavailable resources, policy violations, and operational
 * failures. It uses C++17 standard-library facilities only.
 */

class GovernanceError : public std::runtime_error {
public:
    using std::runtime_error::runtime_error;
};

class ValidationError : public GovernanceError {
public:
    using GovernanceError::GovernanceError;
};

class ResourceNotFoundError : public GovernanceError {
public:
    using GovernanceError::GovernanceError;
};

class PolicyViolationError : public GovernanceError {
public:
    using GovernanceError::GovernanceError;
};

class InvalidTransitionError : public GovernanceError {
public:
    using GovernanceError::GovernanceError;
};

enum class CheckState {
    Pending,
    Passed,
    Failed,
    Cancelled
};

enum class ReviewState {
    Commented,
    Approved,
    ChangesRequested,
    Dismissed
};

enum class PullRequestState {
    Draft,
    Open,
    Closed,
    Merged
};

struct Review {
    std::string reviewer;
    ReviewState state;
    std::string commitId;
    bool eligibleReviewer;
};

struct StatusCheck {
    std::string name;
    CheckState state;
    std::string commitId;
};

struct PullRequest {
    int id;
    std::string title;
    std::string author;
    std::string sourceBranch;
    std::string targetBranch;
    std::string headCommit;
    PullRequestState state;
    bool hasMergeConflict;
    std::vector<Review> reviews;
    std::vector<StatusCheck> checks;
    int unresolvedConversations;
};

struct BranchProtection {
    std::string branch;
    int requiredApprovals;
    std::set<std::string> requiredChecks;
    bool requireConversationResolution;
    bool requireLinearHistory;
    bool prohibitDirectPush;
    bool prohibitForcePush;
    bool prohibitDeletion;
    bool dismissStaleApprovals;
    bool administratorsMayBypass;
};

struct EligibilityReport {
    bool eligible;
    std::vector<std::string> blockers;
};

std::string toString(CheckState state) {
    switch (state) {
        case CheckState::Pending: return "PENDING";
        case CheckState::Passed: return "PASSED";
        case CheckState::Failed: return "FAILED";
        case CheckState::Cancelled: return "CANCELLED";
    }
    throw ValidationError("Unknown status-check state.");
}

std::string toString(ReviewState state) {
    switch (state) {
        case ReviewState::Commented: return "COMMENTED";
        case ReviewState::Approved: return "APPROVED";
        case ReviewState::ChangesRequested: return "CHANGES_REQUESTED";
        case ReviewState::Dismissed: return "DISMISSED";
    }
    throw ValidationError("Unknown review state.");
}

void validateNonempty(const std::string& value, const std::string& field) {
    if (value.empty() || value.find_first_not_of(" \t\r\n") == std::string::npos) {
        throw ValidationError(field + " must not be empty.");
    }
}

class RepositoryGovernance {
private:
    std::map<std::string, BranchProtection> protections;
    std::map<int, PullRequest> pullRequests;

    static void validateProtection(const BranchProtection& policy) {
        validateNonempty(policy.branch, "Protected branch");

        if (policy.requiredApprovals < 0) {
            throw ValidationError("Required approval count cannot be negative.");
        }

        for (const auto& check : policy.requiredChecks) {
            validateNonempty(check, "Required check name");
        }
    }

    static void validatePullRequest(const PullRequest& pr) {
        if (pr.id <= 0) {
            throw ValidationError("Pull request ID must be positive.");
        }

        validateNonempty(pr.title, "Pull request title");
        validateNonempty(pr.author, "Pull request author");
        validateNonempty(pr.sourceBranch, "Source branch");
        validateNonempty(pr.targetBranch, "Target branch");
        validateNonempty(pr.headCommit, "Head commit");

        if (pr.sourceBranch == pr.targetBranch) {
            throw ValidationError("Source and target branches must differ.");
        }

        if (pr.unresolvedConversations < 0) {
            throw ValidationError("Unresolved conversation count cannot be negative.");
        }

        std::set<std::string> reviewers;
        for (const auto& review : pr.reviews) {
            validateNonempty(review.reviewer, "Reviewer");
            validateNonempty(review.commitId, "Review commit");
            if (!reviewers.insert(review.reviewer).second) {
                throw ValidationError("A reviewer may have only one effective review record.");
            }
        }

        std::set<std::string> checks;
        for (const auto& check : pr.checks) {
            validateNonempty(check.name, "Status check name");
            validateNonempty(check.commitId, "Status check commit");
            if (!checks.insert(check.name).second) {
                throw ValidationError("Duplicate status-check name.");
            }
        }
    }

public:
    void protectBranch(const BranchProtection& policy) {
        validateProtection(policy);
        protections[policy.branch] = policy;
    }

    void addPullRequest(const PullRequest& pr) {
        validatePullRequest(pr);

        if (pullRequests.count(pr.id) != 0) {
            throw ValidationError("Pull request ID already exists.");
        }

        pullRequests.emplace(pr.id, pr);
    }

    const PullRequest& getPullRequest(int id) const {
        auto it = pullRequests.find(id);
        if (it == pullRequests.end()) {
            throw ResourceNotFoundError("Pull request not found: " + std::to_string(id));
        }
        return it->second;
    }

    void transition(int id, PullRequestState next) {
        auto it = pullRequests.find(id);
        if (it == pullRequests.end()) {
            throw ResourceNotFoundError("Cannot transition an unknown pull request.");
        }

        PullRequest& pr = it->second;
        bool allowed = false;

        switch (pr.state) {
            case PullRequestState::Draft:
                allowed = next == PullRequestState::Open || next == PullRequestState::Closed;
                break;
            case PullRequestState::Open:
                allowed = next == PullRequestState::Closed || next == PullRequestState::Merged;
                break;
            case PullRequestState::Closed:
                allowed = next == PullRequestState::Open;
                break;
            case PullRequestState::Merged:
                allowed = false;
                break;
        }

        if (!allowed) {
            throw InvalidTransitionError("Requested pull request state transition is invalid.");
        }

        if (next == PullRequestState::Merged) {
            const EligibilityReport report = evaluate(id);
            if (!report.eligible) {
                std::string message = "Merge rejected:";
                for (const auto& blocker : report.blockers) {
                    message += "\n - " + blocker;
                }
                throw PolicyViolationError(message);
            }
        }

        pr.state = next;
    }

    EligibilityReport evaluate(int id) const {
        const PullRequest& pr = getPullRequest(id);
        EligibilityReport report{true, {}};

        auto policyIt = protections.find(pr.targetBranch);
        if (policyIt == protections.end()) {
            report.blockers.push_back("Target branch has no registered governance policy.");
        } else {
            const BranchProtection& policy = policyIt->second;

            if (pr.state != PullRequestState::Open) {
                report.blockers.push_back("Pull request is not open.");
            }

            if (pr.hasMergeConflict) {
                report.blockers.push_back("Merge conflicts must be resolved.");
            }

            std::set<std::string> approvedReviewers;
            bool changeRequested = false;

            for (const auto& review : pr.reviews) {
                if (!review.eligibleReviewer || review.reviewer == pr.author) {
                    continue;
                }

                // With stale approval dismissal enabled, a review is effective
                // only when it evaluates the current head commit.
                if (policy.dismissStaleApprovals && review.commitId != pr.headCommit) {
                    continue;
                }

                if (review.state == ReviewState::ChangesRequested) {
                    changeRequested = true;
                } else if (review.state == ReviewState::Approved) {
                    approvedReviewers.insert(review.reviewer);
                }
            }

            if (changeRequested) {
                report.blockers.push_back(
                    "An eligible reviewer has an effective changes-requested review."
                );
            }

            if (static_cast<int>(approvedReviewers.size()) < policy.requiredApprovals) {
                report.blockers.push_back(
                    "Insufficient eligible approvals: " +
                    std::to_string(approvedReviewers.size()) + " of " +
                    std::to_string(policy.requiredApprovals) + "."
                );
            }

            for (const auto& required : policy.requiredChecks) {
                auto checkIt = std::find_if(
                    pr.checks.begin(),
                    pr.checks.end(),
                    [&](const StatusCheck& check) {
                        return check.name == required && check.commitId == pr.headCommit;
                    }
                );

                if (checkIt == pr.checks.end()) {
                    report.blockers.push_back("Required check is missing or stale: " + required);
                } else if (checkIt->state != CheckState::Passed) {
                    report.blockers.push_back(
                        "Required check " + required + " is " + toString(checkIt->state) + "."
                    );
                }
            }

            if (policy.requireConversationResolution && pr.unresolvedConversations > 0) {
                report.blockers.push_back(
                    std::to_string(pr.unresolvedConversations) +
                    " review conversation(s) remain unresolved."
                );
            }

            if (policy.requireLinearHistory) {
                // The model represents merge strategy as an explicit reviewable
                // condition; a real hosting platform also inspects Git history.
                report.blockers.push_back(
                    "Linear-history strategy must be confirmed before merging."
                );
            }
        }

        report.eligible = report.blockers.empty();
        return report;
    }

    void printReport(int id) const {
        const PullRequest& pr = getPullRequest(id);
        const EligibilityReport report = evaluate(id);

        std::cout << "\nPR #" << pr.id << ": " << pr.title << '\n';
        std::cout << "  Source: " << pr.sourceBranch
                  << " -> Target: " << pr.targetBranch << '\n';
        std::cout << "  Merge eligible: " << (report.eligible ? "YES" : "NO") << '\n';

        for (const auto& blocker : report.blockers) {
            std::cout << "  Blocker: " << blocker << '\n';
        }
    }
};

int main() {
    try {
        RepositoryGovernance governance;

        governance.protectBranch(BranchProtection{
            "main",
            2,
            {"build", "unit-tests", "security-scan"},
            true,
            false,
            true,
            true,
            true,
            true,
            false
        });

        PullRequest ready{
            108,
            "Validate release configuration",
            "developer-alex",
            "feature/release-validation",
            "main",
            "commit-a91",
            PullRequestState::Open,
            false,
            {
                {"reviewer-mira", ReviewState::Approved, "commit-a91", true},
                {"reviewer-sam", ReviewState::Approved, "commit-a91", true}
            },
            {
                {"build", CheckState::Passed, "commit-a91"},
                {"unit-tests", CheckState::Passed, "commit-a91"},
                {"security-scan", CheckState::Passed, "commit-a91"}
            },
            0
        };

        PullRequest blocked{
            109,
            "Update deployment credentials",
            "developer-jules",
            "feature/credential-update",
            "main",
            "commit-b72",
            PullRequestState::Open,
            true,
            {
                {"reviewer-mira", ReviewState::Approved, "commit-b70", true},
                {"reviewer-sam", ReviewState::ChangesRequested, "commit-b72", true},
                {"developer-jules", ReviewState::Approved, "commit-b72", true}
            },
            {
                {"build", CheckState::Passed, "commit-b72"},
                {"unit-tests", CheckState::Pending, "commit-b72"}
            },
            2
        };

        governance.addPullRequest(ready);
        governance.addPullRequest(blocked);

        governance.printReport(108);
        governance.printReport(109);

        try {
            governance.transition(109, PullRequestState::Merged);
        } catch (const PolicyViolationError& error) {
            std::cout << "\nExpected merge rejection:\n" << error.what() << '\n';
        }

        governance.transition(108, PullRequestState::Merged);
        std::cout << "\nPR #108 merged after governance checks passed.\n";

        try {
            governance.transition(108, PullRequestState::Open);
        } catch (const InvalidTransitionError& error) {
            std::cout << "Expected invalid transition: " << error.what() << '\n';
        }

        try {
            governance.getPullRequest(999);
        } catch (const ResourceNotFoundError& error) {
            std::cout << "Expected lookup failure: " << error.what() << '\n';
        }

        try {
            PullRequest invalid{
                110, "", "developer-lee", "feature/x", "main", "commit-c11",
                PullRequestState::Open, false, {}, {}, 0
            };
            governance.addPullRequest(invalid);
        } catch (const ValidationError& error) {
            std::cout << "Expected validation failure: " << error.what() << '\n';
        }

        std::cout << "\nRepository governance simulation completed.\n";
        return 0;
    } catch (const std::exception& error) {
        // This outer boundary records an unexpected failure and returns a
        // nonzero exit code so CI can distinguish failure from success.
        std::cerr << "Fatal governance error: " << error.what() << '\n';
        return 1;
    }
}
