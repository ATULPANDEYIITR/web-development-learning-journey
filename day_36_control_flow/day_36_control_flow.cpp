#include <algorithm>
#include <iostream>
#include <map>
#include <optional>
#include <stdexcept>
#include <string>
#include <vector>

/*
 * Case study: a repository automation service evaluates a collection of
 * validation jobs before allowing a release operation to proceed.
 *
 * The focus is control flow: conditional policy evaluation, switch-based
 * dispatch, loops, early termination, skipped work, state transitions, and
 * failure handling.
 */

enum class JobState {
    Pending,
    Running,
    Passed,
    Failed,
    Skipped
};

enum class Command {
    Build,
    Test,
    Deploy,
    Status,
    Unknown
};

struct Job {
    std::string name;
    bool enabled;
    bool shouldPass;
    JobState state{JobState::Pending};
};

struct EvaluationResult {
    bool deployable;
    std::vector<std::string> failures;
    std::vector<std::string> skipped;
};

Command parseCommand(const std::string& command) {
    if (command == "build") {
        return Command::Build;
    }

    if (command == "test") {
        return Command::Test;
    }

    if (command == "deploy") {
        return Command::Deploy;
    }

    if (command == "status") {
        return Command::Status;
    }

    return Command::Unknown;
}

std::string commandName(Command command) {
    switch (command) {
        case Command::Build:
            return "build";
        case Command::Test:
            return "test";
        case Command::Deploy:
            return "deploy";
        case Command::Status:
            return "status";
        case Command::Unknown:
            return "unknown";
    }

    return "unknown";
}

void executeCommand(Command command) {
    /*
     * switch is appropriate when one enumerated state determines exactly one
     * operation. The default-like Unknown branch prevents accidental action.
     */
    switch (command) {
        case Command::Build:
            std::cout << "Building artifacts\n";
            break;

        case Command::Test:
            std::cout << "Running tests\n";
            break;

        case Command::Deploy:
            std::cout << "Deploying release\n";
            break;

        case Command::Status:
            std::cout << "Showing release status\n";
            break;

        case Command::Unknown:
            std::cout << "Rejecting unknown command\n";
            break;
    }
}

bool transitionJob(Job& job) {
    /*
     * The state machine prevents a job from jumping directly from Pending to
     * Passed. Each transition is controlled by the previous state.
     */
    switch (job.state) {
        case JobState::Pending:
            if (!job.enabled) {
                job.state = JobState::Skipped;
                return true;
            }

            job.state = JobState::Running;
            [[fallthrough]];

        case JobState::Running:
            if (job.shouldPass) {
                job.state = JobState::Passed;
                return true;
            }

            job.state = JobState::Failed;
            return false;

        case JobState::Passed:
        case JobState::Skipped:
            return true;

        case JobState::Failed:
            return false;
    }

    return false;
}

EvaluationResult evaluateJobs(std::vector<Job>& jobs) {
    EvaluationResult result{true, {}, {}};

    for (Job& job : jobs) {
        if (!job.enabled) {
            job.state = JobState::Skipped;
            result.skipped.push_back(job.name);
            continue;
        }

        const bool passed = transitionJob(job);

        if (!passed) {
            result.deployable = false;
            result.failures.push_back(job.name);
        }
    }

    return result;
}

std::optional<int> findFirstFailure(const std::vector<int>& checks) {
    for (int index = 0; index < static_cast<int>(checks.size()); ++index) {
        if (checks[index] < 0) {
            return index;
        }
    }

    return std::nullopt;
}

double calculateRiskAdjustment(
    double amount,
    const std::string& customerType,
    double riskScore
) {
    if (amount < 0.0) {
        throw std::invalid_argument("amount cannot be negative");
    }

    if (riskScore < 0.0 || riskScore > 1.0) {
        throw std::invalid_argument("risk score must be between 0 and 1");
    }

    if (riskScore >= 0.9) {
        return 1.0;
    }

    if (amount == 0.0) {
        return 0.0;
    }

    if (customerType == "enterprise") {
        if (amount >= 10000.0) {
            return 0.15;
        }

        return 0.10;
    }

    if (customerType == "student") {
        return 0.20;
    }

    return 0.0;
}

std::map<std::string, int> countStates(const std::vector<Job>& jobs) {
    std::map<std::string, int> counts{
        {"passed", 0},
        {"failed", 0},
        {"skipped", 0},
        {"pending", 0},
        {"running", 0}
    };

    for (const Job& job : jobs) {
        switch (job.state) {
            case JobState::Passed:
                ++counts["passed"];
                break;

            case JobState::Failed:
                ++counts["failed"];
                break;

            case JobState::Skipped:
                ++counts["skipped"];
                break;

            case JobState::Pending:
                ++counts["pending"];
                break;

            case JobState::Running:
                ++counts["running"];
                break;
        }
    }

    return counts;
}

void printJobState(const Job& job) {
    std::string state;

    switch (job.state) {
        case JobState::Pending:
            state = "pending";
            break;
        case JobState::Running:
            state = "running";
            break;
        case JobState::Passed:
            state = "passed";
            break;
        case JobState::Failed:
            state = "failed";
            break;
        case JobState::Skipped:
            state = "skipped";
            break;
    }

    std::cout << job.name << " -> " << state << '\n';
}

int main() {
    try {
        std::cout << "Command dispatch\n";

        for (const std::string& rawCommand :
             {"build", "test", "deploy", "unknown"}) {
            const Command command = parseCommand(rawCommand);
            std::cout << rawCommand << " -> "
                      << commandName(command) << '\n';
            executeCommand(command);
        }

        std::cout << "\nRelease validation case study\n";

        std::vector<Job> jobs{
            {"compile", true, true},
            {"unit-tests", true, true},
            {"security-scan", true, false},
            {"documentation-check", false, true},
            {"package", true, true}
        };

        const EvaluationResult evaluation = evaluateJobs(jobs);

        for (const Job& job : jobs) {
            printJobState(job);
        }

        std::cout << "Deployable: "
                  << (evaluation.deployable ? "yes" : "no") << '\n';

        if (!evaluation.failures.empty()) {
            std::cout << "Failed jobs:\n";

            for (const std::string& failure : evaluation.failures) {
                std::cout << "  " << failure << '\n';
            }
        }

        if (!evaluation.skipped.empty()) {
            std::cout << "Skipped jobs:\n";

            for (const std::string& skipped : evaluation.skipped) {
                std::cout << "  " << skipped << '\n';
            }
        }

        std::cout << "\nEarly termination\n";

        const std::vector<int> checks{10, 20, 30, -1, 40, 50};
        const std::optional<int> firstFailure = findFirstFailure(checks);

        if (firstFailure.has_value()) {
            std::cout << "First failure index: "
                      << firstFailure.value() << '\n';
        } else {
            std::cout << "All checks passed\n";
        }

        std::cout << "\nState distribution\n";

        const auto stateCounts = countStates(jobs);

        for (const auto& [state, count] : stateCounts) {
            std::cout << state << ": " << count << '\n';
        }

        std::cout << "\nBusiness-rule branching\n";
        std::cout << "Enterprise adjustment: "
                  << calculateRiskAdjustment(25000, "enterprise", 0.1)
                  << '\n';

        std::cout << "Student adjustment: "
                  << calculateRiskAdjustment(500, "student", 0.2)
                  << '\n';

        std::cout << "High-risk adjustment: "
                  << calculateRiskAdjustment(500, "consumer", 0.95)
                  << '\n';

        std::cout << "\nLoop control characteristics\n";

        int processed = 0;

        for (int value = 1; value <= 20; ++value) {
            if (value % 2 != 0) {
                continue;
            }

            if (value > 12) {
                break;
            }

            ++processed;
            std::cout << "Processed even value: " << value << '\n';
        }

        std::cout << "Processed count: " << processed << '\n';
    } catch (const std::exception& error) {
        std::cerr << "Execution error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
