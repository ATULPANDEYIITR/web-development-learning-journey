#include <algorithm>
#include <functional>
#include <iomanip>
#include <iostream>
#include <map>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

/*
 * Repository build-graph case study for ES module architecture.
 *
 * The build planner models JavaScript module dependencies, named and default
 * exports, missing imports, duplicate exports, circular dependencies, and
 * deterministic dependency-first build order.
 *
 * Compile:
 *   g++ -std=c++17 -Wall -Wextra -pedantic module_architecture.cpp -o module_architecture
 */

enum class ExportKind {
    Named,
    Default
};

struct ExportSymbol {
    std::string name;
    ExportKind kind;
};

struct ImportBinding {
    std::string specifier;
    std::string importedName;
    std::string localName;
    bool isDefault = false;
};

struct Module {
    std::string path;
    std::vector<ExportSymbol> exports;
    std::vector<ImportBinding> imports;
};

class ModuleBuildPlanner {
private:
    std::map<std::string, Module> modules;
    std::map<std::string, std::set<std::string>> dependencies;

    static bool isSafeRelativeSpecifier(const std::string& specifier) {
        if (specifier.empty() || specifier.front() != '.') {
            return false;
        }

        // This case study accepts relative source paths only. A production
        // resolver would also implement package exports, aliases, extensions,
        // URL schemes, and the host's exact resolution rules.
        return specifier.find("..\\") == std::string::npos;
    }

    static std::string normalizeRelative(
        const std::string& fromPath,
        const std::string& specifier
    ) {
        std::vector<std::string> parts;
        std::string combined;

        const auto slash = fromPath.find_last_of('/');
        if (slash != std::string::npos) {
            combined = fromPath.substr(0, slash + 1);
        }
        combined += specifier;

        std::stringstream stream(combined);
        std::string part;

        while (std::getline(stream, part, '/')) {
            if (part.empty() || part == ".") {
                continue;
            }

            if (part == "..") {
                if (parts.empty()) {
                    throw std::invalid_argument(
                        "Relative import escapes the source root: " + specifier
                    );
                }
                parts.pop_back();
            } else {
                parts.push_back(part);
            }
        }

        std::string result;
        for (const auto& item : parts) {
            if (!result.empty()) {
                result += '/';
            }
            result += item;
        }

        return result;
    }

    const Module& resolveModule(
        const std::string& fromPath,
        const std::string& specifier
    ) const {
        if (!isSafeRelativeSpecifier(specifier)) {
            throw std::invalid_argument(
                "Unsupported or unsafe import specifier: " + specifier
            );
        }

        const std::string resolved = normalizeRelative(fromPath, specifier);
        const auto found = modules.find(resolved);

        if (found == modules.end()) {
            throw std::runtime_error(
                "Cannot resolve '" + specifier + "' imported by " + fromPath
            );
        }

        return found->second;
    }

    static bool hasExport(
        const Module& module,
        const std::string& name,
        bool isDefault
    ) {
        return std::any_of(
            module.exports.begin(),
            module.exports.end(),
            [&](const ExportSymbol& symbol) {
                if (isDefault) {
                    return symbol.kind == ExportKind::Default;
                }
                return symbol.kind == ExportKind::Named && symbol.name == name;
            }
        );
    }

public:
    void addModule(Module module) {
        if (module.path.empty()) {
            throw std::invalid_argument("Module path cannot be empty.");
        }

        if (modules.count(module.path)) {
            throw std::invalid_argument("Duplicate module path: " + module.path);
        }

        std::set<std::string> namedExports;
        bool defaultExportSeen = false;

        for (const auto& symbol : module.exports) {
            if (symbol.kind == ExportKind::Default) {
                if (defaultExportSeen) {
                    throw std::invalid_argument(
                        module.path + " declares multiple default exports"
                    );
                }
                defaultExportSeen = true;
            } else if (symbol.name.empty() ||
                       !namedExports.insert(symbol.name).second) {
                throw std::invalid_argument(
                    module.path + " declares an invalid or duplicate named export"
                );
            }
        }

        modules.emplace(module.path, std::move(module));
    }

    void validate() {
        dependencies.clear();

        for (const auto& entry : modules) {
            const Module& module = entry.second;
            dependencies[module.path];

            for (const auto& binding : module.imports) {
                const Module& target = resolveModule(
                    module.path,
                    binding.specifier
                );

                if (!hasExport(target, binding.importedName, binding.isDefault)) {
                    const std::string requested = binding.isDefault
                        ? "default"
                        : binding.importedName;

                    throw std::runtime_error(
                        module.path + " imports missing export '" + requested +
                        "' from " + target.path
                    );
                }

                dependencies[module.path].insert(target.path);
            }
        }
    }

    std::vector<std::string> buildOrder() const {
        std::map<std::string, std::size_t> remaining;
        std::map<std::string, std::set<std::string>> dependents;

        for (const auto& entry : modules) {
            remaining[entry.first] = dependencies.at(entry.first).size();

            for (const auto& dependency : dependencies.at(entry.first)) {
                dependents[dependency].insert(entry.first);
            }
        }

        // A sorted ready set makes the result reproducible across executions.
        std::set<std::string> ready;
        for (const auto& entry : remaining) {
            if (entry.second == 0) {
                ready.insert(entry.first);
            }
        }

        std::vector<std::string> result;

        while (!ready.empty()) {
            const std::string current = *ready.begin();
            ready.erase(ready.begin());
            result.push_back(current);

            for (const auto& dependent : dependents[current]) {
                auto& count = remaining.at(dependent);
                if (--count == 0) {
                    ready.insert(dependent);
                }
            }
        }

        if (result.size() != modules.size()) {
            std::vector<std::string> involved;
            for (const auto& entry : remaining) {
                if (entry.second > 0) {
                    involved.push_back(entry.first);
                }
            }

            std::ostringstream message;
            message << "Circular dependency prevents build ordering:";
            for (const auto& path : involved) {
                message << ' ' << path;
            }
            throw std::runtime_error(message.str());
        }

        return result;
    }

    void printGraph() const {
        for (const auto& entry : dependencies) {
            std::cout << entry.first << " depends on";
            if (entry.second.empty()) {
                std::cout << " no local modules";
            } else {
                for (const auto& dependency : entry.second) {
                    std::cout << ' ' << dependency;
                }
            }
            std::cout << '\n';
        }
    }
};

Module makeModule(
    std::string path,
    std::vector<ExportSymbol> exports,
    std::vector<ImportBinding> imports = {}
) {
    return Module{
        std::move(path),
        std::move(exports),
        std::move(imports)
    };
}

int main() {
    try {
        ModuleBuildPlanner planner;

        planner.addModule(makeModule(
            "src/domain/pricing.js",
            {
                {"calculateTotal", ExportKind::Named},
                {"default", ExportKind::Default}
            }
        ));

        planner.addModule(makeModule(
            "src/domain/tax.js",
            {{"calculateTax", ExportKind::Named}}
        ));

        planner.addModule(makeModule(
            "src/application/invoice.js",
            {
                {"createInvoice", ExportKind::Named}
            },
            {
                {"../domain/pricing.js", "calculateTotal", "calculateTotal", false},
                {"../domain/tax.js", "calculateTax", "calculateTax", false}
            }
        ));

        planner.addModule(makeModule(
            "src/ui/summary.js",
            {{"renderSummary", ExportKind::Named}},
            {
                {"../application/invoice.js", "createInvoice", "createInvoice", false}
            }
        ));

        planner.validate();

        std::cout << "Repository module dependency graph\n";
        planner.printGraph();

        std::cout << "\nDeterministic build order\n";
        for (const auto& path : planner.buildOrder()) {
            std::cout << "  " << path << '\n';
        }

        std::cout << "\nMissing-export failure case\n";
        ModuleBuildPlanner broken;
        broken.addModule(makeModule(
            "src/shared.js",
            {{"formatMoney", ExportKind::Named}}
        ));
        broken.addModule(makeModule(
            "src/report.js",
            {{"createReport", ExportKind::Named}},
            {{"./shared.js", "formatDate", "formatDate", false}}
        ));

        try {
            broken.validate();
        } catch (const std::runtime_error& error) {
            std::cout << "Rejected: " << error.what() << '\n';
        }

        std::cout << "\nCircular-dependency failure case\n";
        ModuleBuildPlanner cyclic;
        cyclic.addModule(makeModule(
            "src/a.js",
            {{"a", ExportKind::Named}},
            {{"./b.js", "b", "b", false}}
        ));
        cyclic.addModule(makeModule(
            "src/b.js",
            {{"b", ExportKind::Named}},
            {{"./a.js", "a", "a", false}}
        ));

        cyclic.validate();

        try {
            static_cast<void>(cyclic.buildOrder());
        } catch (const std::runtime_error& error) {
            std::cout << "Rejected: " << error.what() << '\n';
        }

        std::cout << "\nRepository architecture checks completed.\n";
    } catch (const std::exception& error) {
        std::cerr << "Build planner error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
