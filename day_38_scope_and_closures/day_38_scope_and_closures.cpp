#include <algorithm>
#include <cassert>
#include <functional>
#include <iomanip>
#include <iostream>
#include <map>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

/*
 * Scope and Closures: repository-policy simulation
 *
 * The case study uses C++ lambdas to model configurable policies while
 * explicitly demonstrating the distinction between:
 *
 * - global/static storage
 * - function-local variables
 * - lexical capture
 * - block lifetime
 * - captured state
 * - value capture versus reference capture
 * - mutable closure state
 *
 * The domain is deliberately built around validation policies because
 * closures are useful when behavior must retain configuration without
 * requiring a globally shared variable.
 */

namespace GlobalConfiguration {
    constexpr int minimumReviewScore = 70;
    const std::string systemName = "Repository Governance Engine";
}

int globalEvaluationCount = 0;

void demonstrateGlobalScope() {
    std::cout << "\n=== Global scope ===\n";
    std::cout << "System: " << GlobalConfiguration::systemName << '\n';
    std::cout << "Minimum review score: "
              << GlobalConfiguration::minimumReviewScore << '\n';

    ++globalEvaluationCount;
    std::cout << "Global evaluation count: "
              << globalEvaluationCount << '\n';
}

void demonstrateFunctionScope() {
    std::cout << "\n=== Function-local scope ===\n";

    const int localThreshold = 3;

    {
        const int blockThreshold = 5;
        std::cout << "Inside block: " << blockThreshold << '\n';
    }

    // blockThreshold no longer exists here.
    std::cout << "Function-local threshold: " << localThreshold << '\n';
}

struct Review {
    std::string reviewer;
    int score;
    bool approved;
};

struct PullRequest {
    std::string identifier;
    std::string sourceBranch;
    std::string targetBranch;
    bool checksPassed;
    std::vector<Review> reviews;
};

class GovernanceEngine {
public:
    using Policy = std::function<bool(const PullRequest&)>;

    explicit GovernanceEngine(std::string protectedBranch)
        : protectedBranch_(std::move(protectedBranch)) {}

    void addPolicy(std::string name, Policy policy) {
        policies_.emplace_back(std::move(name), std::move(policy));
    }

    bool eligible(const PullRequest& request) const {
        for (const auto& [name, policy] : policies_) {
            const bool passed = policy(request);
            std::cout << std::left << std::setw(28)
                      << name << (passed ? "PASS" : "FAIL") << '\n';

            if (!passed) {
                return false;
            }
        }

        return true;
    }

private:
    std::string protectedBranch_;
    std::vector<std::pair<std::string, Policy>> policies_;
};

void demonstrateValueCapture() {
    std::cout << "\n=== Value capture ===\n";

    int requiredApprovals = 2;

    auto approvalPolicy = [requiredApprovals](const PullRequest& request) {
        const auto approvals = std::count_if(
            request.reviews.begin(),
            request.reviews.end(),
            [](const Review& review) {
                return review.approved;
            }
        );

        return approvals >= requiredApprovals;
    };

    // Changing the original variable would not alter the closure because
    // requiredApprovals was copied into the lambda's closure object.
    requiredApprovals = 10;

    PullRequest request{
        "PR-101",
        "feature/scope",
        "main",
        true,
        {
            {"reviewer-a", 90, true},
            {"reviewer-b", 88, true}
        }
    };

    std::cout << "Copied policy result: "
              << (approvalPolicy(request) ? "PASS" : "FAIL") << '\n';
}

void demonstrateReferenceCapture() {
    std::cout << "\n=== Reference capture ===\n";

    int requiredApprovals = 2;

    auto approvalPolicy = [&requiredApprovals](const PullRequest& request) {
        const auto approvals = std::count_if(
            request.reviews.begin(),
            request.reviews.end(),
            [](const Review& review) {
                return review.approved;
            }
        );

        return approvals >= requiredApprovals;
    };

    PullRequest request{
        "PR-102",
        "feature/closure",
        "main",
        true,
        {
            {"reviewer-a", 90, true},
            {"reviewer-b", 88, true}
        }
    };

    std::cout << "Two approvals: "
              << (approvalPolicy(request) ? "PASS" : "FAIL") << '\n';

    requiredApprovals = 3;

    std::cout << "Three approvals required after rebinding source variable: "
              << (approvalPolicy(request) ? "PASS" : "FAIL") << '\n';
}

std::function<bool(const PullRequest&)> makeBranchPolicy(
    std::string expectedTarget
) {
    /*
     * expectedTarget is captured by value. The returned lambda remains valid
     * after this function returns because its closure owns the captured copy.
     */
    return [expectedTarget = std::move(expectedTarget)]
           (const PullRequest& request) {
        return request.targetBranch == expectedTarget;
    };
}

std::function<bool(const PullRequest&)> makeScorePolicy(
    int minimumScore
) {
    if (minimumScore < 0 || minimumScore > 100) {
        throw std::invalid_argument("score threshold must be between 0 and 100");
    }

    return [minimumScore](const PullRequest& request) {
        if (request.reviews.empty()) {
            return false;
        }

        const double average = [&request] {
            int total = 0;

            for (const auto& review : request.reviews) {
                total += review.score;
            }

            return static_cast<double>(total) /
                   static_cast<double>(request.reviews.size());
        }();

        return average >= minimumScore;
    };
}

std::function<bool(const PullRequest&)> makeStatusPolicy(
    bool checksRequired
) {
    return [checksRequired](const PullRequest& request) {
        return !checksRequired || request.checksPassed;
    };
}

void demonstratePolicyClosures() {
    std::cout << "\n=== Policy factories and lexical capture ===\n";

    PullRequest request{
        "PR-103",
        "feature/governance",
        "main",
        true,
        {
            {"alice", 92, true},
            {"bob", 87, true}
        }
    };

    GovernanceEngine engine("main");

    engine.addPolicy(
        "Protected target branch",
        makeBranchPolicy("main")
    );

    engine.addPolicy(
        "Required status checks",
        makeStatusPolicy(true)
    );

    engine.addPolicy(
        "Minimum review quality",
        makeScorePolicy(80)
    );

    engine.addPolicy(
        "Two approvals",
        [](const PullRequest& pr) {
            return std::count_if(
                       pr.reviews.begin(),
                       pr.reviews.end(),
                       [](const Review& review) {
                           return review.approved;
                       }
                   ) >= 2;
        }
    );

    std::cout << "\nEvaluating " << request.identifier << '\n';
    const bool eligible = engine.eligible(request);

    std::cout << "Merge eligibility: "
              << (eligible ? "ELIGIBLE" : "BLOCKED") << '\n';
}

class AttemptTracker {
public:
    explicit AttemptTracker(int maximum)
        : maximum_(maximum) {
        if (maximum_ <= 0) {
            throw std::invalid_argument("maximum must be positive");
        }
    }

    bool consume() {
        if (attempts_ >= maximum_) {
            return false;
        }

        ++attempts_;
        return true;
    }

    int attempts() const {
        return attempts_;
    }

private:
    int maximum_;
    int attempts_{0};
};

void demonstrateClosureState() {
    std::cout << "\n=== Mutable closure state ===\n";

    int invocationCount = 0;

    auto recordEvaluation = [&invocationCount] {
        ++invocationCount;
        return invocationCount;
    };

    std::cout << "Invocation: " << recordEvaluation() << '\n';
    std::cout << "Invocation: " << recordEvaluation() << '\n';

    // The closure stores a reference, so it intentionally modifies the
    // surrounding variable. The caller must ensure that the referenced
    // object's lifetime exceeds every use of the closure.
    std::cout << "Captured variable: " << invocationCount << '\n';

    AttemptTracker tracker(2);
    std::cout << "Tracker consume: " << tracker.consume() << '\n';
    std::cout << "Tracker consume: " << tracker.consume() << '\n';
    std::cout << "Tracker consume after limit: " << tracker.consume() << '\n';
}

void demonstrateDanglingReferenceHazard() {
    std::cout << "\n=== Lifetime safety ===\n";

    /*
     * A reference-capturing lambda must not outlive the object it references.
     * The unsafe pattern would return a lambda capturing a local variable
     * by reference. This program deliberately avoids constructing that
     * undefined behavior.
     *
     * Value capture is preferable when the closure needs independent,
     * long-lived configuration.
     */
    const int configuration = 42;

    auto safeClosure = [configuration] {
        return configuration;
    };

    std::cout << "Safe captured configuration: "
              << safeClosure() << '\n';
}

void runAssertions() {
    const PullRequest request{
        "PR-TEST",
        "feature/test",
        "main",
        true,
        {
            {"a", 95, true},
            {"b", 90, true}
        }
    };

    auto branchPolicy = makeBranchPolicy("main");
    auto scorePolicy = makeScorePolicy(80);

    assert(branchPolicy(request));
    assert(scorePolicy(request));

    auto counter = [value = 0]() mutable {
        return ++value;
    };

    assert(counter() == 1);
    assert(counter() == 2);

    std::cout << "\nAll C++ scope and closure assertions passed.\n";
}

int main() {
    try {
        std::cout << GlobalConfiguration::systemName << '\n';

        demonstrateGlobalScope();
        demonstrateFunctionScope();
        demonstrateValueCapture();
        demonstrateReferenceCapture();
        demonstratePolicyClosures();
        demonstrateClosureState();
        demonstrateDanglingReferenceHazard();
        runAssertions();

        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Fatal error: " << error.what() << '\n';
        return 1;
    }
}
