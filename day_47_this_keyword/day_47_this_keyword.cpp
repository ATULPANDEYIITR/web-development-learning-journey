#include <algorithm>
#include <iostream>
#include <map>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

/*
 * Repository governance case study.
 *
 * C++ does not have JavaScript's dynamic `this` binding, call, apply,
 * or bind. A member function receives an implicit object parameter,
 * represented by this. The program models explicit receiver selection
 * using object references and callable wrappers.
 *
 * Compile:
 *   g++ -std=c++17 -Wall -Wextra -pedantic this_keyword_case_study.cpp -o governance
 * Run:
 *   ./governance
 */

class PullRequest {
private:
    int number_;
    std::string author_;
    std::string sourceBranch_;
    std::string targetBranch_;
    int approvals_;
    int requiredApprovals_;
    std::map<std::string, bool> checks_;
    bool protectedTarget_;
    bool conversationsResolved_;

public:
    PullRequest(
        int number,
        std::string author,
        std::string sourceBranch,
        std::string targetBranch,
        int approvals,
        int requiredApprovals,
        std::map<std::string, bool> checks,
        bool protectedTarget,
        bool conversationsResolved
    )
        : number_(number),
          author_(std::move(author)),
          sourceBranch_(std::move(sourceBranch)),
          targetBranch_(std::move(targetBranch)),
          approvals_(approvals),
          requiredApprovals_(requiredApprovals),
          checks_(std::move(checks)),
          protectedTarget_(protectedTarget),
          conversationsResolved_(conversationsResolved) {
        if (number_ <= 0) {
            throw std::invalid_argument("Pull request number must be positive");
        }
        if (author_.empty() || sourceBranch_.empty() || targetBranch_.empty()) {
            throw std::invalid_argument("Author and branch names are required");
        }
        if (sourceBranch_ == targetBranch_) {
            throw std::invalid_argument("Source and target branches must differ");
        }
        if (approvals_ < 0 || requiredApprovals_ < 0) {
            throw std::invalid_argument("Approval counts cannot be negative");
        }
    }

    // In a C++ member function, this points to the object on which the
    // member was invoked. It is not dynamically replaced like JavaScript this.
    bool isMergeEligible() const {
        const bool checksPassed = std::all_of(
            checks_.begin(),
            checks_.end(),
            [](const auto& check) {
                return check.second;
            }
        );

        return approvals_ >= requiredApprovals_
            && checksPassed
            && conversationsResolved_;
    }

    std::string report() const {
        std::string result =
            "PR #" + std::to_string(number_) +
            " by " + author_ +
            "\n  " + sourceBranch_ + " -> " + targetBranch_;

        result += "\n  approvals: " + std::to_string(approvals_)
            + "/" + std::to_string(requiredApprovals_);

        for (const auto& [name, passed] : checks_) {
            result += "\n  check " + name + ": "
                + (passed ? "PASS" : "FAIL");
        }

        result += "\n  protected target: "
            + std::string(protectedTarget_ ? "yes" : "no");

        result += "\n  conversations resolved: "
            + std::string(conversationsResolved_ ? "yes" : "no");

        result += "\n  merge eligible: "
            + std::string(isMergeEligible() ? "yes" : "no");

        return result;
    }

    int number() const {
        return number_;
    }
};

class GovernanceService {
private:
    std::string serviceName_;

public:
    explicit GovernanceService(std::string serviceName)
        : serviceName_(std::move(serviceName)) {}

    // The explicit PullRequest reference is analogous to selecting a
    // receiver before invoking a function. C++ cannot change this binding.
    bool evaluate(const PullRequest& request) const {
        std::cout << serviceName_ << " evaluating PR #"
                  << request.number() << '\n';
        return request.isMergeEligible();
    }
};

int main() {
    try {
        PullRequest eligible(
            42,
            "maya",
            "feature/auth-check",
            "main",
            2,
            2,
            {{"unit-tests", true}, {"security-scan", true}, {"lint", true}},
            true,
            true
        );

        PullRequest blocked(
            43,
            "arun",
            "feature/cache-change",
            "main",
            1,
            2,
            {{"unit-tests", true}, {"security-scan", false}, {"lint", true}},
            true,
            false
        );

        GovernanceService service("MergeEligibilityService");

        std::cout << eligible.report() << "\n\n";
        std::cout << blocked.report() << "\n\n";

        std::cout << std::boolalpha;
        std::cout << "Service decision for PR #42: "
                  << service.evaluate(eligible) << '\n';
        std::cout << "Service decision for PR #43: "
                  << service.evaluate(blocked) << '\n';

        // A member-function pointer identifies a method but still requires
        // an object on which to invoke it. The receiver remains explicit.
        bool (PullRequest::*eligibilityMethod)() const =
            &PullRequest::isMergeEligible;

        std::cout << "Member pointer invocation: "
                  << (eligible.*eligibilityMethod)() << '\n';

        // A lambda can capture a specific object by reference. This is
        // similar to retaining a chosen receiver in a callback, although
        // C++ lifetime rules require the captured object to remain alive.
        const PullRequest& capturedRequest = eligible;
        auto boundDecision = [&capturedRequest]() {
            return capturedRequest.isMergeEligible();
        };

        std::cout << "Captured receiver decision: "
                  << boundDecision() << '\n';

        // Reference capture is safe here because eligible outlives the
        // lambda. Storing this callback beyond that lifetime would dangle.
    } catch (const std::exception& error) {
        std::cerr << "Governance failure: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
