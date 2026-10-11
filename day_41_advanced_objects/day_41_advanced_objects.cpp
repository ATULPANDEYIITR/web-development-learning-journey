#include <algorithm>
#include <iostream>
#include <map>
#include <optional>
#include <set>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

// Repository deployment policies are represented as data properties.
// This case study models descriptor-like mutability, immutable policy fields,
// prototype-based defaults, and merge eligibility in a release governance engine.

enum class ReviewState {
    Commented,
    Approved,
    ChangesRequested,
    Dismissed
};

enum class CheckState {
    Pending,
    Passed,
    Failed
};

enum class MergeStrategy {
    MergeCommit,
    Squash,
    Rebase
};

struct PropertyDescriptor {
    std::string value;
    bool writable = true;
    bool enumerable = true;
    bool configurable = true;
};

class PolicyObject {
public:
    void define(const std::string& name, PropertyDescriptor descriptor) {
        if (name.empty()) {
            throw std::invalid_argument("Property name cannot be empty.");
        }

        auto it = properties_.find(name);

        if (it == properties_.end() && !extensible_) {
            throw std::logic_error("Cannot add a property to a non-extensible policy.");
        }

        if (it != properties_.end() && !it->second.configurable) {
            const auto& old = it->second;

            if (descriptor.configurable || descriptor.enumerable != old.enumerable) {
                throw std::logic_error("Cannot alter locked descriptor attributes.");
            }

            if (!old.writable &&
                (descriptor.writable || descriptor.value != old.value)) {
                throw std::logic_error("Cannot alter a locked property value.");
            }
        }

        properties_[name] = std::move(descriptor);
    }

    const std::string& get(const std::string& name) const {
        auto it = properties_.find(name);
        if (it == properties_.end()) {
            throw std::out_of_range("Unknown policy property: " + name);
        }
        return it->second.value;
    }

    void set(const std::string& name, const std::string& value) {
        auto it = properties_.find(name);

        if (it == properties_.end()) {
            if (!extensible_) {
                throw std::logic_error("Cannot add a property to a locked policy.");
            }

            properties_.emplace(name, PropertyDescriptor{value});
            return;
        }

        if (!it->second.writable) {
            throw std::logic_error("Policy property is not writable: " + name);
        }

        it->second.value = value;
    }

    void preventExtensions() {
        extensible_ = false;
    }

    void seal() {
        extensible_ = false;
        sealed_ = true;

        for (auto& [name, descriptor] : properties_) {
            (void)name;
            descriptor.configurable = false;
        }
    }

    void freeze() {
        seal();

        for (auto& [name, descriptor] : properties_) {
            (void)name;
            descriptor.writable = false;
        }

        frozen_ = true;
    }

    bool isFrozen() const {
        if (!sealed_ || !frozen_) {
            return false;
        }

        return std::all_of(
            properties_.begin(),
            properties_.end(),
            [](const auto& entry) {
                return !entry.second.configurable && !entry.second.writable;
            }
        );
    }

private:
    std::map<std::string, PropertyDescriptor> properties_;
    bool extensible_ = true;
    bool sealed_ = false;
    bool frozen_ = false;
};

class PolicyPrototype {
public:
    explicit PolicyPrototype(
        std::map<std::string, std::string> properties = {},
        const PolicyPrototype* parent = nullptr
    ) : properties_(std::move(properties)), parent_(parent) {}

    std::optional<std::string> lookup(const std::string& name) const {
        auto it = properties_.find(name);

        if (it != properties_.end()) {
            return it->second;
        }

        if (parent_ != nullptr) {
            return parent_->lookup(name);
        }

        return std::nullopt;
    }

    void setOwn(const std::string& name, const std::string& value) {
        properties_[name] = value;
    }

private:
    std::map<std::string, std::string> properties_;
    const PolicyPrototype* parent_;
};

struct Review {
    std::string reviewer;
    ReviewState state;
};

struct StatusCheck {
    std::string name;
    CheckState state;
};

struct PullRequest {
    int id;
    std::string sourceBranch;
    std::string targetBranch;
    std::string author;
    bool draft = false;
    bool open = true;
    bool mergeConflict = false;
    bool conversationsResolved = true;
    std::string currentHead;
    std::string reviewedHead;
    std::vector<Review> reviews;
    std::vector<StatusCheck> checks;
};

struct BranchProtection {
    std::string branch;
    int requiredApprovals = 2;
    bool requireCodeOwner = true;
    bool requireChecks = true;
    bool requireResolvedConversations = true;
    bool disallowForcePush = true;
    bool disallowDeletion = true;
    bool requireLinearHistory = false;
    bool dismissStaleApprovals = true;
    std::set<std::string> codeOwners;
    std::set<std::string> allowedMergeStrategies = {
        "squash", "rebase"
    };
};

struct EligibilityResult {
    bool eligible = true;
    std::vector<std::string> reasons;

    void reject(std::string reason) {
        eligible = false;
        reasons.push_back(std::move(reason));
    }
};

class GovernanceEngine {
public:
    explicit GovernanceEngine(BranchProtection protection)
        : protection_(std::move(protection)) {}

    EligibilityResult evaluate(const PullRequest& request) const {
        EligibilityResult result;

        if (!request.open) {
            result.reject("Pull Request is closed.");
        }

        if (request.draft) {
            result.reject("Draft Pull Requests cannot be merged.");
        }

        if (request.targetBranch != protection_.branch) {
            result.reject("Target branch does not match the protected branch.");
        }

        if (request.sourceBranch == request.targetBranch) {
            result.reject("Source and target branches must differ.");
        }

        if (request.mergeConflict) {
            result.reject("Merge conflicts must be resolved.");
        }

        if (protection_.requireResolvedConversations &&
            !request.conversationsResolved) {
            result.reject("Review conversations remain unresolved.");
        }

        std::set<std::string> approvedReviewers;
        bool hasCodeOwnerApproval = false;

        for (const auto& review : request.reviews) {
            // Only the latest state for each reviewer should govern eligibility.
            // Processing in order replaces earlier decisions by the same reviewer.
            if (review.state == ReviewState::Approved) {
                approvedReviewers.insert(review.reviewer);
            } else {
                approvedReviewers.erase(review.reviewer);
            }
        }

        // This simplified model records the head commit reviewers evaluated.
        // Production systems should track review commit IDs individually.
        if (protection_.dismissStaleApprovals &&
            request.reviewedHead != request.currentHead) {
            approvedReviewers.clear();
            result.reject("Approvals are stale because the source branch changed.");
        }

        if (static_cast<int>(approvedReviewers.size()) <
            protection_.requiredApprovals) {
            result.reject("Required independent approvals have not been met.");
        }

        for (const auto& reviewer : approvedReviewers) {
            if (protection_.codeOwners.count(reviewer) > 0) {
                hasCodeOwnerApproval = true;
            }
        }

        if (protection_.requireCodeOwner && !hasCodeOwnerApproval) {
            result.reject("A required code owner has not approved.");
        }

        if (protection_.requireChecks) {
            if (request.checks.empty()) {
                result.reject("No required status checks were reported.");
            }

            for (const auto& check : request.checks) {
                if (check.state != CheckState::Passed) {
                    result.reject("Status check is not passing: " + check.name);
                }
            }
        }

        return result;
    }

    bool canUseStrategy(MergeStrategy strategy) const {
        std::string name;

        switch (strategy) {
            case MergeStrategy::MergeCommit:
                name = "merge";
                break;
            case MergeStrategy::Squash:
                name = "squash";
                break;
            case MergeStrategy::Rebase:
                name = "rebase";
                break;
        }

        return protection_.allowedMergeStrategies.count(name) > 0;
    }

    const BranchProtection& protection() const {
        return protection_;
    }

private:
    BranchProtection protection_;
};

void printResult(const PullRequest& request, const EligibilityResult& result) {
    std::cout << "\nPull Request #" << request.id << " ("
              << request.sourceBranch << " -> " << request.targetBranch << ")\n";

    if (result.eligible) {
        std::cout << "Merge eligible.\n";
    } else {
        std::cout << "Merge blocked:\n";
        for (const auto& reason : result.reasons) {
            std::cout << "  - " << reason << '\n';
        }
    }
}

int main() {
    try {
        PolicyObject policy;
        policy.define("required_approvals", {"2", false, true, false});
        policy.define("required_checks", {"ci,security", false, true, false});
        policy.freeze();

        std::cout << "Frozen policy: " << std::boolalpha
                  << policy.isFrozen() << '\n';

        try {
            policy.set("required_approvals", "1");
        } catch (const std::logic_error& error) {
            std::cout << "Policy mutation blocked: " << error.what() << '\n';
        }

        PolicyPrototype organizationDefaults({
            {"minimum_approvals", "2"},
            {"force_push", "disabled"}
        });

        PolicyPrototype repositoryPolicy(
            {{"required_checks", "ci,security"}},
            &organizationDefaults
        );

        std::cout << "Inherited approval threshold: "
                  << *repositoryPolicy.lookup("minimum_approvals") << '\n';

        BranchProtection protection;
        protection.branch = "main";
        protection.requiredApprovals = 2;
        protection.requireCodeOwner = true;
        protection.codeOwners = {"maya", "liam"};

        GovernanceEngine engine(protection);

        PullRequest ready{
            42,
            "feature/audit-log",
            "main",
            "noah",
            false,
            true,
            false,
            true,
            "abc123",
            "abc123",
            {
                {"maya", ReviewState::Approved},
                {"liam", ReviewState::Approved}
            },
            {
                {"ci", CheckState::Passed},
                {"security-scan", CheckState::Passed}
            }
        };

        printResult(ready, engine.evaluate(ready));

        PullRequest blocked{
            43,
            "feature/payment-retry",
            "main",
            "noah",
            false,
            true,
            false,
            false,
            "def456",
            "old456",
            {
                {"maya", ReviewState::Approved},
                {"liam", ReviewState::ChangesRequested}
            },
            {
                {"ci", CheckState::Passed},
                {"security-scan", CheckState::Pending}
            }
        };

        printResult(blocked, engine.evaluate(blocked));

        PullRequest draft{
            44,
            "feature/metrics",
            "main",
            "noah",
            true,
            true,
            false,
            true,
            "ghi789",
            "ghi789",
            {
                {"maya", ReviewState::Approved},
                {"liam", ReviewState::Approved}
            },
            {
                {"ci", CheckState::Passed}
            }
        };

        printResult(draft, engine.evaluate(draft));

        std::cout << "\nSquash merge permitted: "
                  << engine.canUseStrategy(MergeStrategy::Squash) << '\n';
        std::cout << "Merge commit permitted: "
                  << engine.canUseStrategy(MergeStrategy::MergeCommit) << '\n';

        std::cout
            << "\nThis engine evaluates policy; it does not modify a Git repository. "
            << "Actual branch protection must also be enforced by the hosting platform.\n";
    } catch (const std::exception& error) {
        std::cerr << "Governance failure: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
