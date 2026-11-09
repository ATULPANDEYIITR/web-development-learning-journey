#include <algorithm>
#include <functional>
#include <iostream>
#include <map>
#include <queue>
#include <set>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

using namespace std;

/*
 * TypeScript Architecture Governance Engine.
 *
 * Models:
 * - Module boundaries.
 * - Interface declarations.
 * - Named exports and imports.
 * - Declaration modules.
 * - Dependency graphs.
 * - Circular dependency detection.
 * - Strict compiler configuration.
 * - Architecture validation.
 * - Build ordering.
 *
 * Standard: C++17
 * External dependencies: None.
 */

enum class ModuleType {
    ESModule,
    CommonJS,
    Declaration,
    Ambient
};

enum class DiagnosticLevel {
    Error,
    Warning,
    Information
};

string toString(ModuleType type) {
    switch (type) {
        case ModuleType::ESModule: return "ES Module";
        case ModuleType::CommonJS: return "CommonJS";
        case ModuleType::Declaration: return "Declaration";
        case ModuleType::Ambient: return "Ambient";
    }
    return "Unknown";
}

string toString(DiagnosticLevel level) {
    switch (level) {
        case DiagnosticLevel::Error: return "ERROR";
        case DiagnosticLevel::Warning: return "WARNING";
        case DiagnosticLevel::Information: return "INFO";
    }
    return "UNKNOWN";
}

struct Property {
    string name;
    string type;
    bool optional = false;
    bool readonly = false;
};

struct InterfaceDefinition {
    string name;
    vector<Property> properties;
    vector<string> parents;
};

struct Module {
    string name;
    string filePath;
    ModuleType type = ModuleType::ESModule;
    set<string> exports;
    set<string> imports;
    set<string> interfaces;
    bool entryPoint = false;
};

struct Diagnostic {
    string code;
    DiagnosticLevel level;
    string message;
    string location;
};

class ArchitectureException : public runtime_error {
public:
    explicit ArchitectureException(const string& message)
        : runtime_error(message) {}
};

class CompilerConfiguration {
public:
    string target = "ES2022";
    string module = "NodeNext";
    string moduleResolution = "NodeNext";
    string rootDir = "src";
    string outDir = "dist";

    bool strict = true;
    bool strictNullChecks = true;
    bool noImplicitAny = true;
    bool strictFunctionTypes = true;
    bool strictPropertyInitialization = true;
    bool noImplicitOverride = true;
    bool noUnusedLocals = true;
    bool noUncheckedIndexedAccess = true;
    bool exactOptionalPropertyTypes = true;
    bool declaration = true;
    bool sourceMap = true;
    bool declarationMap = true;

    void validate() const {
        if (strict) {
            if (
                !strictNullChecks ||
                !noImplicitAny ||
                !strictFunctionTypes ||
                !strictPropertyInitialization
            ) {
                throw ArchitectureException(
                    "Strict mode conflicts with disabled strict checks."
                );
            }
        }

        if (rootDir == outDir) {
            throw ArchitectureException(
                "Source and output directories cannot be identical."
            );
        }

        if (target.empty() || module.empty()) {
            throw ArchitectureException(
                "Target and module cannot be empty."
            );
        }
    }
};

class InterfaceRegistry {
private:
    unordered_map<string, InterfaceDefinition> interfaces;

    void resolveRecursive(
        const string& name,
        unordered_set<string>& visiting,
        unordered_map<string, Property>& result
    ) const {
        auto it = interfaces.find(name);

        if (it == interfaces.end()) {
            throw ArchitectureException(
                "Unknown interface: " + name
            );
        }

        if (visiting.count(name)) {
            throw ArchitectureException(
                "Circular interface inheritance: " + name
            );
        }

        visiting.insert(name);

        for (const string& parent : it->second.parents) {
            resolveRecursive(parent, visiting, result);
        }

        for (const Property& property : it->second.properties) {
            auto existing = result.find(property.name);

            if (
                existing != result.end() &&
                existing->second.type != property.type
            ) {
                throw ArchitectureException(
                    "Conflicting inherited property: " +
                    property.name
                );
            }

            result[property.name] = property;
        }

        visiting.erase(name);
    }

public:
    void add(const InterfaceDefinition& definition) {
        if (definition.name.empty()) {
            throw ArchitectureException(
                "Interface name cannot be empty."
            );
        }

        if (interfaces.count(definition.name)) {
            throw ArchitectureException(
                "Duplicate interface: " + definition.name
            );
        }

        set<string> names;

        for (const auto& property : definition.properties) {
            if (
                property.name.empty() ||
                property.type.empty() ||
                !names.insert(property.name).second
            ) {
                throw ArchitectureException(
                    "Invalid or duplicate interface property."
                );
            }
        }

        interfaces.emplace(definition.name, definition);
    }

    unordered_map<string, Property> resolve(
        const string& name
    ) const {
        unordered_set<string> visiting;
        unordered_map<string, Property> result;

        resolveRecursive(name, visiting, result);
        return result;
    }

    vector<string> validateImplementation(
        const string& name,
        const unordered_map<string, string>& implementation
    ) const {
        auto contract = resolve(name);
        vector<string> errors;

        for (const auto& [propertyName, property] : contract) {
            auto value = implementation.find(propertyName);

            if (value == implementation.end()) {
                if (!property.optional) {
                    errors.push_back(
                        "Missing property: " + propertyName
                    );
                }
            } else if (
                value->second == "null" &&
                !property.optional
            ) {
                errors.push_back(
                    "Required property cannot be null: " +
                    propertyName
                );
            }
        }

        return errors;
    }

    bool exists(const string& name) const {
        return interfaces.count(name) != 0;
    }
};

class ModuleRegistry {
private:
    map<string, Module> modules;

public:
    void add(const Module& module) {
        if (module.name.empty() || module.filePath.empty()) {
            throw ArchitectureException(
                "Module name and path are required."
            );
        }

        if (modules.count(module.name)) {
            throw ArchitectureException(
                "Duplicate module: " + module.name
            );
        }

        modules.emplace(module.name, module);
    }

    const map<string, Module>& all() const {
        return modules;
    }

    const Module* get(const string& name) const {
        auto it = modules.find(name);

        if (it == modules.end()) {
            return nullptr;
        }

        return &it->second;
    }
};

class DependencyAnalyzer {
private:
    const ModuleRegistry& registry;

public:
    explicit DependencyAnalyzer(
        const ModuleRegistry& moduleRegistry
    ) : registry(moduleRegistry) {}

    vector<string> buildOrder() const {
        unordered_map<string, int> indegree;
        unordered_map<string, set<string>> graph;

        for (const auto& [name, module] : registry.all()) {
            indegree[name] = 0;
            graph[name];
        }

        for (const auto& [name, module] : registry.all()) {
            for (const string& dependency : module.imports) {
                if (!registry.get(dependency)) {
                    throw ArchitectureException(
                        "Unknown imported module: " + dependency
                    );
                }

                graph[name].insert(dependency);
                indegree[dependency]++;
            }
        }

        queue<string> ready;

        for (const auto& [name, degree] : indegree) {
            if (degree == 0) {
                ready.push(name);
            }
        }

        vector<string> result;

        while (!ready.empty()) {
            string current = ready.front();
            ready.pop();

            result.push_back(current);

            for (const string& dependency : graph[current]) {
                if (--indegree[dependency] == 0) {
                    ready.push(dependency);
                }
            }
        }

        if (result.size() != registry.all().size()) {
            throw ArchitectureException(
                "Circular module dependency detected."
            );
        }

        return result;
    }
};

class ArchitectureEngine {
private:
    CompilerConfiguration configuration;
    InterfaceRegistry interfaces;
    ModuleRegistry modules;
    vector<Diagnostic> diagnostics;

public:
    InterfaceRegistry& interfaceRegistry() {
        return interfaces;
    }

    ModuleRegistry& moduleRegistry() {
        return modules;
    }

    CompilerConfiguration& compilerConfiguration() {
        return configuration;
    }

    const vector<Diagnostic>& validate() {
        diagnostics.clear();

        try {
            configuration.validate();
        } catch (const exception& error) {
            diagnostics.push_back({
                "CONFIG001",
                DiagnosticLevel::Error,
                error.what(),
                "tsconfig.json"
            });
        }

        for (const auto& [name, module] : modules.all()) {
            for (const string& dependency : module.imports) {
                if (!modules.get(dependency)) {
                    diagnostics.push_back({
                        "MODULE001",
                        DiagnosticLevel::Error,
                        "Unknown imported module: " + dependency,
                        module.filePath
                    });
                }
            }

            for (const string& interfaceName : module.interfaces) {
                if (!interfaces.exists(interfaceName)) {
                    diagnostics.push_back({
                        "TYPE001",
                        DiagnosticLevel::Error,
                        "Unknown interface: " + interfaceName,
                        module.filePath
                    });
                }
            }

            if (
                module.type == ModuleType::Declaration &&
                module.exports.empty()
            ) {
                diagnostics.push_back({
                    "DECL001",
                    DiagnosticLevel::Warning,
                    "Declaration module has no exports.",
                    module.filePath
                });
            }
        }

        try {
            DependencyAnalyzer analyzer(modules);
            analyzer.buildOrder();
        } catch (const exception& error) {
            diagnostics.push_back({
                "MODULE002",
                DiagnosticLevel::Error,
                error.what(),
                ""
            });
        }

        return diagnostics;
    }

    bool isValid() const {
        return none_of(
            diagnostics.begin(),
            diagnostics.end(),
            [](const Diagnostic& diagnostic) {
                return diagnostic.level == DiagnosticLevel::Error;
            }
        );
    }

    void printReport() const {
        cout << "\nARCHITECTURE DIAGNOSTICS\n";
        cout << "-----------------------\n";

        if (diagnostics.empty()) {
            cout << "No issues detected.\n";
            return;
        }

        for (const auto& diagnostic : diagnostics) {
            cout
                << "[" << toString(diagnostic.level) << "] "
                << diagnostic.code << ": "
                << diagnostic.message << "\n";

            if (!diagnostic.location.empty()) {
                cout << "  File: " << diagnostic.location << "\n";
            }
        }
    }
};

void addSampleInterfaces(ArchitectureEngine& engine) {
    InterfaceDefinition entity{
        "Entity",
        {
            {"id", "string", false, true}
        },
        {}
    };

    InterfaceDefinition user{
        "User",
        {
            {"email", "string", false, false},
            {"displayName", "string", false, false},
            {"phone", "string", true, false}
        },
        {"Entity"}
    };

    InterfaceDefinition repository{
        "UserRepository",
        {
            {
                "findById",
                "(id: string) => Promise<User | null>",
                false,
                false
            },
            {
                "save",
                "(user: User) => Promise<void>",
                false,
                false
            }
        },
        {}
    };

    engine.interfaceRegistry().add(entity);
    engine.interfaceRegistry().add(user);
    engine.interfaceRegistry().add(repository);
}

void addSampleModules(ArchitectureEngine& engine) {
    Module domain;
    domain.name = "domain";
    domain.filePath = "src/domain/user.ts";
    domain.exports = {
        "Entity", "User", "UserRepository"
    };
    domain.interfaces = {
        "Entity", "User", "UserRepository"
    };

    Module infrastructure;
    infrastructure.name = "infrastructure";
    infrastructure.filePath =
        "src/infrastructure/user-repository.ts";
    infrastructure.imports = {"domain"};
    infrastructure.exports = {
        "PostgresUserRepository"
    };
    infrastructure.interfaces = {"UserRepository"};

    Module services;
    services.name = "services";
    services.filePath = "src/services/user-service.ts";
    services.imports = {
        "domain", "infrastructure"
    };
    services.exports = {"UserService"};
    services.interfaces = {"User"};

    Module api;
    api.name = "api";
    api.filePath = "src/api/server.ts";
    api.imports = {"services"};
    api.exports = {"startServer"};
    api.entryPoint = true;

    engine.moduleRegistry().add(domain);
    engine.moduleRegistry().add(infrastructure);
    engine.moduleRegistry().add(services);
    engine.moduleRegistry().add(api);
}

void runTests() {
    InterfaceRegistry registry;

    registry.add({
        "Base",
        {{"id", "string", false, false}},
        {}
    });

    registry.add({
        "Child",
        {{"name", "string", false, false}},
        {"Base"}
    });

    auto valid = registry.validateImplementation(
        "Child",
        {
            {"id", "U-101"},
            {"name", "Developer"}
        }
    );

    if (!valid.empty()) {
        throw ArchitectureException(
            "Valid interface implementation was rejected."
        );
    }

    auto invalid = registry.validateImplementation(
        "Child",
        {
            {"id", "U-101"}
        }
    );

    if (invalid.size() != 1) {
        throw ArchitectureException(
            "Missing property was not detected."
        );
    }

    ModuleRegistry modules;

    Module a;
    a.name = "application";
    a.filePath = "src/application.ts";
    a.imports = {"domain"};

    Module b;
    b.name = "domain";
    b.filePath = "src/domain.ts";

    modules.add(a);
    modules.add(b);

    DependencyAnalyzer analyzer(modules);
    auto order = analyzer.buildOrder();

    if (order.size() != 2) {
        throw ArchitectureException(
            "Dependency ordering test failed."
        );
    }

    CompilerConfiguration invalidConfig;
    invalidConfig.strictNullChecks = false;

    bool rejected = false;

    try {
        invalidConfig.validate();
    } catch (const ArchitectureException&) {
        rejected = true;
    }

    if (!rejected) {
        throw ArchitectureException(
            "Strict configuration test failed."
        );
    }

    cout << "All C++17 architecture tests passed.\n";
}

int main() {
    try {
        runTests();

        ArchitectureEngine engine;

        addSampleInterfaces(engine);
        addSampleModules(engine);

        const auto& diagnostics = engine.validate();

        engine.printReport();

        if (!engine.isValid()) {
            cerr << "\nArchitecture validation failed.\n";
            return 1;
        }

        DependencyAnalyzer analyzer(engine.moduleRegistry());

        cout << "\nMODULE BUILD ORDER\n";

        const vector<string> order = analyzer.buildOrder();

        for (size_t i = 0; i < order.size(); ++i) {
            cout << i + 1 << ". " << order[i] << "\n";
        }

        cout << "\nINTERFACE CONTRACT VALIDATION\n";

        const auto errors =
            engine.interfaceRegistry().validateImplementation(
                "User",
                {
                    {"id", "USR-101"},
                    {"email", "developer@example.com"},
                    {"displayName", "Development User"}
                }
            );

        if (errors.empty()) {
            cout << "User implementation is structurally valid.\n";
        } else {
            for (const string& error : errors) {
                cout << error << "\n";
            }
        }

        cout << "\nREGISTERED MODULES\n";

        for (const auto& [name, module] :
             engine.moduleRegistry().all()) {
            cout
                << name << " | "
                << module.filePath << " | "
                << toString(module.type) << "\n";
        }

        cout << "\nCompiler target: "
             << engine.compilerConfiguration().target << "\n";

        cout << "Strict mode: "
             << (engine.compilerConfiguration().strict
                     ? "enabled" : "disabled")
             << "\n";

        return 0;

    } catch (const exception& error) {
        cerr << "Architecture error: "
             << error.what() << "\n";
        return 1;
    }
}
