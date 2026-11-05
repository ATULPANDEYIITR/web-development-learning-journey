#include <algorithm>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <memory>
#include <optional>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace fs = std::filesystem;

/*
 * Node.js Fundamentals: Runtime Deployment Governance
 *
 * This C++17 program models a Node.js application deployment.
 * It validates runtime compatibility, module dependencies,
 * environment configuration, filesystem permissions, and
 * application startup requirements.
 */

enum class RuntimeMode {
    Development,
    Test,
    Production
};

enum class CheckStatus {
    Passed,
    Warning,
    Failed
};

struct CheckResult {
    std::string category;
    std::string message;
    CheckStatus status;
};

struct RuntimeVersion {
    int major;
    int minor;
    int patch;

    static RuntimeVersion parse(const std::string& input) {
        RuntimeVersion version{};
        char first, second;

        std::istringstream stream(input);

        if (!(stream >> version.major >> first
                     >> version.minor >> second
                     >> version.patch) ||
            first != '.' || second != '.') {
            throw std::invalid_argument("Invalid Node.js version.");
        }

        if (version.major < 0 ||
            version.minor < 0 ||
            version.patch < 0) {
            throw std::invalid_argument("Negative version component.");
        }

        return version;
    }

    bool operator>=(const RuntimeVersion& other) const {
        if (major != other.major) return major > other.major;
        if (minor != other.minor) return minor > other.minor;
        return patch >= other.patch;
    }

    std::string toString() const {
        return std::to_string(major) + "." +
               std::to_string(minor) + "." +
               std::to_string(patch);
    }
};

class Environment {
private:
    std::map<std::string, std::string> values;

public:
    void set(const std::string& key, const std::string& value) {
        if (key.empty()) {
            throw std::invalid_argument("Empty environment key.");
        }

        values[key] = value;
    }

    std::optional<std::string> get(
        const std::string& key
    ) const {
        auto it = values.find(key);

        if (it == values.end()) {
            return std::nullopt;
        }

        return it->second;
    }

    int getInteger(
        const std::string& key,
        int defaultValue,
        int minimum,
        int maximum
    ) const {
        auto raw = get(key);

        if (!raw.has_value()) {
            return defaultValue;
        }

        try {
            std::size_t processed = 0;
            int value = std::stoi(*raw, &processed);

            if (processed != raw->size()) {
                throw std::invalid_argument("Invalid integer.");
            }

            if (value < minimum || value > maximum) {
                throw std::out_of_range("Value outside permitted range.");
            }

            return value;

        } catch (const std::exception&) {
            throw std::invalid_argument(
                "Invalid environment integer: " + key
            );
        }
    }

    std::vector<CheckResult> validate(
        const std::vector<std::string>& required
    ) const {
        std::vector<CheckResult> results;

        for (const auto& key : required) {
            auto value = get(key);

            bool valid = value.has_value() && !value->empty();

            results.push_back({
                "ENVIRONMENT",
                valid ? key + " is configured."
                      : key + " is missing or empty.",
                valid ? CheckStatus::Passed : CheckStatus::Failed
            });
        }

        return results;
    }
};

struct Module {
    std::string name;
    std::string version;
    std::vector<std::string> dependencies;
    bool builtin = false;
};

class ModuleGraph {
private:
    std::map<std::string, Module> modules;

    const std::set<std::string> builtins = {
        "fs", "path", "os", "http", "https",
        "events", "crypto", "util", "stream",
        "buffer", "url", "assert", "process"
    };

    enum class VisitState {
        Unvisited,
        Visiting,
        Visited
    };

    bool visit(
        const std::string& name,
        std::map<std::string, VisitState>& states
    ) const {
        if (builtins.count(name)) {
            return true;
        }

        auto module = modules.find(name);

        if (module == modules.end()) {
            return false;
        }

        if (states[name] == VisitState::Visiting) {
            throw std::runtime_error(
                "Circular module dependency: " + name
            );
        }

        if (states[name] == VisitState::Visited) {
            return true;
        }

        states[name] = VisitState::Visiting;

        for (const auto& dependency : module->second.dependencies) {
            if (!visit(dependency, states)) {
                return false;
            }
        }

        states[name] = VisitState::Visited;
        return true;
    }

public:
    void registerModule(const Module& module) {
        if (module.name.empty()) {
            throw std::invalid_argument("Module name cannot be empty.");
        }

        if (modules.count(module.name) || builtins.count(module.name)) {
            throw std::invalid_argument(
                "Duplicate module: " + module.name
            );
        }

        modules.emplace(module.name, module);
    }

    bool validate(const std::string& entryModule) const {
        std::map<std::string, VisitState> states;

        return visit(entryModule, states);
    }

    void display() const {
        for (const auto& [name, module] : modules) {
            std::cout << name << "@" << module.version << "\n";

            for (const auto& dependency : module.dependencies) {
                std::cout << "  -> " << dependency << "\n";
            }
        }
    }
};

class SecureFileManager {
private:
    fs::path root;

public:
    explicit SecureFileManager(const fs::path& directory) {
        fs::create_directories(directory);
        root = fs::weakly_canonical(directory);
    }

    fs::path resolve(const fs::path& relative) const {
        if (relative.empty() || relative.is_absolute()) {
            throw std::invalid_argument("Invalid relative path.");
        }

        fs::path candidate = fs::weakly_canonical(root / relative);

        auto rootIterator = root.begin();
        auto candidateIterator = candidate.begin();

        for (; rootIterator != root.end(); ++rootIterator, ++candidateIterator) {
            if (candidateIterator == candidate.end() ||
                *rootIterator != *candidateIterator) {
                throw std::runtime_error(
                    "Filesystem path escapes application root."
                );
            }
        }

        return candidate;
    }

    void writeFile(
        const std::string& relative,
        const std::string& content
    ) const {
        fs::path target = resolve(relative);

        fs::create_directories(target.parent_path());

        fs::path temporary = target.string() + ".tmp";

        {
            std::ofstream output(
                temporary,
                std::ios::out | std::ios::trunc
            );

            if (!output) {
                throw std::runtime_error(
                    "Cannot create temporary file."
                );
            }

            output << content;

            if (!output) {
                throw std::runtime_error(
                    "File write failed."
                );
            }
        }

        // Rename provides atomic replacement on the same filesystem
        // on common local filesystems when the target can be replaced.
        std::error_code error;
        fs::rename(temporary, target, error);

        if (error) {
            fs::remove(temporary);
            throw std::runtime_error(
                "File replacement failed: " + error.message()
            );
        }
    }

    std::string readFile(const std::string& relative) const {
        fs::path target = resolve(relative);

        std::ifstream input(target);

        if (!input) {
            throw std::runtime_error("Cannot open application file.");
        }

        std::ostringstream buffer;
        buffer << input.rdbuf();

        return buffer.str();
    }

    std::vector<std::string> listFiles() const {
        std::vector<std::string> files;

        for (const auto& entry : fs::recursive_directory_iterator(root)) {
            if (entry.is_symlink()) {
                continue;
            }

            if (entry.is_regular_file()) {
                files.push_back(
                    fs::relative(entry.path(), root).string()
                );
            }
        }

        std::sort(files.begin(), files.end());

        return files;
    }
};

class DeploymentEngine {
private:
    RuntimeVersion actual;
    RuntimeVersion minimum;
    RuntimeMode mode;
    const Environment& environment;
    const ModuleGraph& modules;

public:
    DeploymentEngine(
        RuntimeVersion actualVersion,
        RuntimeVersion requiredVersion,
        RuntimeMode runtimeMode,
        const Environment& env,
        const ModuleGraph& graph
    )
        : actual(actualVersion),
          minimum(requiredVersion),
          mode(runtimeMode),
          environment(env),
          modules(graph) {}

    std::vector<CheckResult> evaluate() const {
        std::vector<CheckResult> results;

        bool compatible = actual >= minimum;

        results.push_back({
            "RUNTIME",
            "Actual Node.js version: " + actual.toString(),
            compatible ? CheckStatus::Passed : CheckStatus::Failed
        });

        auto envResults = environment.validate({
            "NODE_ENV",
            "PORT",
            "DATABASE_URL"
        });

        results.insert(
            results.end(),
            envResults.begin(),
            envResults.end()
        );

        bool moduleValid = modules.validate("inventory-api");

        results.push_back({
            "MODULES",
            "Application dependency graph validation.",
            moduleValid ? CheckStatus::Passed : CheckStatus::Failed
        });

        return results;
    }

    bool ready() const {
        auto results = evaluate();

        return std::none_of(
            results.begin(),
            results.end(),
            [](const CheckResult& result) {
                return result.status == CheckStatus::Failed;
            }
        );
    }
};

std::string statusText(CheckStatus status) {
    switch (status) {
        case CheckStatus::Passed: return "PASS";
        case CheckStatus::Warning: return "WARN";
        case CheckStatus::Failed: return "FAIL";
    }

    return "UNKNOWN";
}

int main() {
    try {
        std::cout << "==========================================\n";
        std::cout << "NODE.JS RUNTIME GOVERNANCE ENGINE\n";
        std::cout << "==========================================\n";

        RuntimeVersion actual = RuntimeVersion::parse("22.11.0");
        RuntimeVersion minimum = RuntimeVersion::parse("18.0.0");

        Environment environment;

        environment.set("NODE_ENV", "production");
        environment.set("PORT", "8080");
        environment.set(
            "DATABASE_URL",
            "postgresql://localhost/inventory"
        );

        std::cout << "\nENVIRONMENT CONFIGURATION\n";

        std::cout << "Mode: "
                  << *environment.get("NODE_ENV") << "\n";

        int port = environment.getInteger(
            "PORT", 3000, 1, 65535
        );

        std::cout << "Port: " << port << "\n";

        std::cout << "\nMODULE DEPENDENCY GRAPH\n";

        ModuleGraph graph;

        graph.registerModule({
            "database", "2.0.0", {"crypto", "events"}
        });

        graph.registerModule({
            "inventory-service", "1.0.0", {"database", "fs"}
        });

        graph.registerModule({
            "inventory-api", "1.0.0", {
                "inventory-service", "http", "path"
            }
        });

        graph.display();

        std::cout << "\nFILESYSTEM OPERATIONS\n";

        fs::path directory =
            fs::temp_directory_path() / "node-fundamentals-cpp";

        SecureFileManager files(directory);

        files.writeFile(
            "config/runtime.json",
            "{ \"mode\": \"production\", \"port\": 8080 }"
        );

        std::cout << files.readFile("config/runtime.json") << "\n";

        for (const auto& filename : files.listFiles()) {
            std::cout << "File: " << filename << "\n";
        }

        try {
            files.resolve("../../outside.json");
        } catch (const std::exception& error) {
            std::cout << "Security validation: "
                      << error.what() << "\n";
        }

        std::cout << "\nRUNTIME DEPLOYMENT EVALUATION\n";

        DeploymentEngine engine(
            actual,
            minimum,
            RuntimeMode::Production,
            environment,
            graph
        );

        for (const auto& result : engine.evaluate()) {
            std::cout << statusText(result.status)
                      << " [" << result.category << "] "
                      << result.message << "\n";
        }

        std::cout << "\nDEPLOYMENT: "
                  << (engine.ready() ? "READY" : "BLOCKED")
                  << "\n";

        std::cout << "\nFAILURE SCENARIOS\n";

        Environment invalid;
        invalid.set("PORT", "70000");

        try {
            invalid.getInteger("PORT", 3000, 1, 65535);
        } catch (const std::exception& error) {
            std::cout << "Invalid configuration: "
                      << error.what() << "\n";
        }

        ModuleGraph incomplete;

        incomplete.registerModule({
            "inventory-api", "1.0.0", {"missing-module"}
        });

        std::cout << "Missing module detected: "
                  << (!incomplete.validate("inventory-api")
                      ? "YES" : "NO")
                  << "\n";

        std::cout << "\nEXECUTION COMPLETED\n";

    } catch (const std::exception& error) {
        std::cerr << "FATAL ERROR: " << error.what() << "\n";
        return 1;
    }

    return 0;
}
