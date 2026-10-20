#include <algorithm>
#include <exception>
#include <iostream>
#include <map>
#include <numeric>
#include <optional>
#include <set>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

enum class PullRequestState {
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

enum class MergeStrategy {
    MergeCommit,
    Squash,
    Rebase
};

struct Commit {
    std::string sha;
    std::string message;
};

struct Review {
    std::string reviewer;
    ReviewState state;
    std::vector<std::string> comments;
};

struct StatusCheck {
    std::string name;
    bool passed;
    bool required;
};

struct BranchProtection {
    std::size_t requiredReviews{1};
    std::set<std::string> requiredChecks;
    bool requireConversationResolution{true};
    bool requireLinearHistory{false};
    bool allowDirectPush{false};
    bool allowForcePush{false};
    bool allowDeletion{false};
    bool allowAdminBypass{false};
};

struct PullRequest {
    int number{};
    std::string sourceBranch;
    std::string targetBranch;
    std::vector<Commit> commits;
    PullRequestState state{PullRequestState::Draft};
    std::vector<Review> reviews;
    std::map<std::string, StatusCheck> checks;
    std::size_t unresolvedConversations{};
    bool hasConflicts{false};
    bool synchronizedWithBase{true};
    MergeStrategy mergeStrategy{MergeStrategy::Squash};
};

class GovernanceEngine {
public:
    static std::size_t approvalCount(const PullRequest& pr) {
        return static_cast<std::size_t>(std::count_if(
            pr.reviews.begin(),
            pr.reviews.end(),
            [](const Review& review) {
                return review.state == ReviewState::Approved;
            }
        ));
    }

    static bool hasRequestedChanges(const PullRequest& pr) {
        return std::any_of(
            pr.reviews.begin(),
            pr.reviews.end(),
            [](const Review& review) {
                return review.state == ReviewState::ChangesRequested;
            }
        );
    }

    static bool requiredChecksPass(
        const PullRequest& pr,
        const BranchProtection& policy
    ) {
        return std::all_of(
            policy.requiredChecks.begin(),
            policy.requiredChecks.end(),
            [&](const std::string& name) {
                const auto it = pr.checks.find(name);
                return it != pr.checks.end() && it->second.passed;
            }
        );
    }

    static std::vector<std::string> mergeReasons(
        const PullRequest& pr,
        const BranchProtection& policy
    ) {
        std::vector<std::string> reasons;

        if (pr.state != PullRequestState::Open) {
            reasons.emplace_back("pull request is not open");
        }

        if (pr.commits.empty()) {
            reasons.emplace_back("pull request contains no commits");
        }

        if (pr.sourceBranch == pr.targetBranch) {
            reasons.emplace_back("source and target branches are identical");
        }

        if (!pr.synchronizedWithBase) {
            reasons.emplace_back("source branch is behind the target branch");
        }

        if (pr.hasConflicts) {
            reasons.emplace_back("merge conflicts must be resolved");
        }

        if (hasRequestedChanges(pr)) {
            reasons.emplace_back("a reviewer has requested changes");
        }

        if (approvalCount(pr) < policy.requiredReviews) {
            reasons.emplace_back("required approvals are missing");
        }

        if (!requiredChecksPass(pr, policy)) {
            reasons.emplace_back("required status checks have not passed");
        }

        if (
            policy.requireConversationResolution &&
            pr.unresolvedConversations > 0
        ) {
            reasons.emplace_back("review conversations remain unresolved");
        }

        return reasons;
    }

    static bool canMerge(
        const PullRequest& pr,
        const BranchProtection& policy
    ) {
        return mergeReasons(pr, policy).empty();
    }

    static PullRequest openDraft(const PullRequest& pr) {
        if (pr.state != PullRequestState::Draft) {
            throw std::logic_error(
                "only draft pull requests can be opened"
            );
        }

        PullRequest copy = pr;
        copy.state = PullRequestState::Open;
        return copy;
    }

    static PullRequest addReview(
        const PullRequest& pr,
        Review review
    ) {
        if (pr.state != PullRequestState::Open) {
            throw std::logic_error(
                "reviews require an open pull request"
            );
        }

        if (review.reviewer.empty()) {
            throw std::invalid_argument("reviewer cannot be empty");
        }

        PullRequest copy = pr;
        copy.reviews.push_back(std::move(review));
        return copy;
    }

    static PullRequest updateCheck(
        const PullRequest& pr,
        const std::string& name,
        bool passed
    ) {
        if (name.empty()) {
            throw std::invalid_argument("check name cannot be empty");
        }

        PullRequest copy = pr;
        copy.checks[name] = StatusCheck{name, passed, true};
        return copy;
    }

    static PullRequest resolveConversation(const PullRequest& pr) {
        PullRequest copy = pr;

        if (copy.unresolvedConversations > 0) {
            --copy.unresolvedConversations;
        }

        return copy;
    }

    static PullRequest synchronize(const PullRequest& pr) {
        PullRequest copy = pr;
        copy.synchronizedWithBase = true;
        copy.hasConflicts = false;
        return copy;
    }

    static PullRequest merge(
        const PullRequest& pr,
        const BranchProtection& policy
    ) {
        const auto reasons = mergeReasons(pr, policy);

        if (!reasons.empty()) {
            throw std::runtime_error(
                "merge blocked: " + join(reasons)
            );
        }

        PullRequest copy = pr;
        copy.state = PullRequestState::Merged;
        return copy;
    }

private:
    static std::string join(
        const std::vector<std::string>& values
    ) {
        std::string result;

        for (std::size_t i = 0; i < values.size(); ++i) {
            if (i != 0) {
                result += "; ";
            }
            result += values[i];
        }

        return result;
    }
};

template <typename T, typename Function>
auto functionalMap(
    const std::vector<T>& values,
    Function function
) -> std::vector<decltype(function(values.front()))> {
    using Result = decltype(function(values.front()));
    std::vector<Result> result;
    result.reserve(values.size());

    for (const auto& value : values) {
        result.push_back(function(value));
    }

    return result;
}

template <typename T, typename Predicate>
std::vector<T> functionalFilter(
    const std::vector<T>& values,
    Predicate predicate
) {
    std::vector<T> result;

    std::copy_if(
        values.begin(),
        values.end(),
        std::back_inserter(result),
        predicate
    );

    return result;
}

std::string normalizeMessage(const Commit& commit) {
    std::string result = commit.message;

    result.erase(
        result.begin(),
        std::find_if(
            result.begin(),
            result.end(),
            [](unsigned char c) { return !std::isspace(c); }
        )
    );

    result.erase(
        std::find_if(
            result.rbegin(),
            result.rend(),
            [](unsigned char c) { return !std::isspace(c); }
        ).base(),
        result.end()
    );

    return result;
}

int main() {
    try {
        BranchProtection policy{
            2,
            {"unit-tests", "security-scan"},
            true,
            true,
            false,
            false,
            false,
            false
        };

        std::vector<Commit> commits{
            {"a1b2c3d", " add repository workflow model "},
            {"b2c3d4e", "implement merge eligibility"},
            {"c3d4e5f", "fix"}
        };

        PullRequest pr{
            42,
            "feature/governance-engine",
            "main",
            commits,
            PullRequestState::Draft,
            {},
            {
                {"unit-tests", {"unit-tests", true, true}},
                {"security-scan", {"security-scan", false, true}}
            },
            2,
            false,
            true,
            MergeStrategy::Squash
        };

        pr = GovernanceEngine::openDraft(pr);

        pr = GovernanceEngine::addReview(
            pr,
            {
                "reviewer-alice",
                ReviewState::Approved,
                {"Policy model is clear."}
            }
        );

        pr = GovernanceEngine::addReview(
            pr,
            {
                "reviewer-bob",
                ReviewState::Commented,
                {"Resolve the policy discussion."}
            }
        );

        const auto normalized = functionalMap(
            commits,
            [](const Commit& commit) {
                return normalizeMessage(commit);
            }
        );

        const auto meaningful = functionalFilter(
            normalized,
            [](const std::string& message) {
                return message.size() >= 8;
            }
        );

        std::cout << "Functional commit pipeline:\n";
        for (const auto& message : meaningful) {
            std::cout << "  " << message << '\n';
        }

        std::cout << "\nInitial merge state: "
                  << std::boolalpha
                  << GovernanceEngine::canMerge(pr, policy)
                  << '\n';

        for (const auto& reason :
             GovernanceEngine::mergeReasons(pr, policy)) {
            std::cout << "  Blocked by: " << reason << '\n';
        }

        pr = GovernanceEngine::addReview(
            pr,
            {
                "reviewer-bob",
                ReviewState::Approved,
                {}
            }
        );

        pr = GovernanceEngine::updateCheck(
            pr,
            "security-scan",
            true
        );

        pr = GovernanceEngine::resolveConversation(pr);
        pr = GovernanceEngine::resolveConversation(pr);
        pr = GovernanceEngine::synchronize(pr);

        std::cout << "\nFinal merge state: "
                  << GovernanceEngine::canMerge(pr, policy)
                  << '\n';

        if (GovernanceEngine::canMerge(pr, policy)) {
            pr = GovernanceEngine::merge(pr, policy);
            std::cout << "Pull request merged.\n";
        }

        // The source vector was never modified by the functional pipeline.
        std::cout << "\nOriginal commit remains unchanged: "
                  << commits.front().message << '\n';

    } catch (const std::exception& error) {
        std::cerr << "Governance error: "
                  << error.what()
                  << '\n';
        return 1;
    }

    return 0;
}
