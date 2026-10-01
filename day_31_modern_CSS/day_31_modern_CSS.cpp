#include <algorithm>
#include <cctype>
#include <exception>
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

/*
 * Modern CSS Design-System Audit Engine
 *
 * This C++17 case study models a CSS architecture for a component library.
 * It does not attempt to implement a browser's CSS parser or rendering
 * engine. Instead, it represents stylesheet features as structured records
 * and evaluates practical design-system constraints.
 *
 * The system audits:
 *   - custom-property token definitions and var() dependencies
 *   - nested CSS relationships
 *   - :is() selector groups
 *   - :where() low-specificity defaults
 *   - :has() relational selectors
 *   - logical properties
 *
 * Scenario:
 * A design-system team is preparing a form and dashboard component library.
 * Each component must consume shared tokens, prefer logical layout
 * properties, use :where() for low-specificity defaults, and use :has()
 * only when the relationship between a parent and descendant is meaningful.
 *
 * Compile:
 *   g++ -std=c++17 -O2 modern_css_audit.cpp -o modern_css_audit
 */

namespace css {

struct Token {
    std::string name;
    std::string value;
    bool inherits{true};
};

struct SelectorRule {
    std::string selector;
    std::map<std::string, std::string> declarations;
    std::string purpose;
};

struct AuditIssue {
    std::string severity;
    std::string component;
    std::string message;
};

struct AuditReport {
    std::vector<AuditIssue> issues;
    std::map<std::string, int> featureCounts;

    bool passed() const {
        return std::none_of(
            issues.begin(),
            issues.end(),
            [](const AuditIssue& issue) {
                return issue.severity == "ERROR";
            }
        );
    }
};

struct CssSystem {
    std::vector<Token> tokens;
    std::vector<SelectorRule> rules;
};

static bool startsWith(const std::string& text, const std::string& prefix) {
    return text.rfind(prefix, 0) == 0;
}

static std::string trim(const std::string& value) {
    const auto first = value.find_first_not_of(" \t\r\n");

    if (first == std::string::npos) {
        return "";
    }

    const auto last = value.find_last_not_of(" \t\r\n");
    return value.substr(first, last - first + 1);
}

static std::vector<std::string> split(const std::string& text, char delimiter) {
    std::vector<std::string> parts;
    std::stringstream stream(text);
    std::string part;

    while (std::getline(stream, part, delimiter)) {
        parts.push_back(trim(part));
    }

    return parts;
}

static std::set<std::string> extractVarDependencies(
    const std::string& value
) {
    std::set<std::string> dependencies;

    const std::regex pattern(
        R"(var\(\s*(--[-_a-zA-Z0-9]+))"
    );

    for (
        std::sregex_iterator it(value.begin(), value.end(), pattern);
        it != std::sregex_iterator();
        ++it
    ) {
        dependencies.insert((*it)[1].str());
    }

    return dependencies;
}

/*
 * Custom-property dependency analysis catches token graphs such as:
 *
 *   --surface-raised: var(--surface);
 *   --surface: var(--base-surface);
 *
 * It also detects cycles, which are invalid dependency graphs for a
 * predictable token system.
 */
class TokenGraph {
private:
    std::map<std::string, std::string> values;

    enum class VisitState {
        Unvisited,
        Visiting,
        Visited
    };

    bool visit(
        const std::string& token,
        std::map<std::string, VisitState>& states,
        std::vector<std::string>& path,
        std::string& cycle
    ) const {
        const auto state = states[token];

        if (state == VisitState::Visiting) {
            auto position = std::find(path.begin(), path.end(), token);

            std::ostringstream output;

            if (position != path.end()) {
                for (auto it = position; it != path.end(); ++it) {
                    if (it != position) {
                        output << " -> ";
                    }
                    output << *it;
                }
                output << " -> " << token;
            } else {
                output << token;
            }

            cycle = output.str();
            return false;
        }

        if (state == VisitState::Visited) {
            return true;
        }

        states[token] = VisitState::Visiting;
        path.push_back(token);

        for (const auto& dependency : extractVarDependencies(values.at(token))) {
            if (!values.contains(dependency)) {
                path.pop_back();
                return false;
            }

            if (!visit(dependency, states, path, cycle)) {
                return false;
            }
        }

        path.pop_back();
        states[token] = VisitState::Visited;
        return true;
    }

public:
    explicit TokenGraph(const std::vector<Token>& tokens) {
        for (const auto& token : tokens) {
            values[token.name] = token.value;
        }
    }

    bool hasUndefinedReference(
        std::string& tokenName,
        std::string& dependency
    ) const {
        for (const auto& [name, value] : values) {
            for (const auto& candidate : extractVarDependencies(value)) {
                if (!values.contains(candidate)) {
                    tokenName = name;
                    dependency = candidate;
                    return true;
                }
            }
        }

        return false;
    }

    std::optional<std::string> findCycle() const {
        std::map<std::string, VisitState> states;

        for (const auto& [name, _] : values) {
            states[name] = VisitState::Unvisited;
        }

        for (const auto& [name, _] : values) {
            if (states[name] != VisitState::Unvisited) {
                continue;
            }

            std::vector<std::string> path;
            std::string cycle;

            if (!visit(name, states, path, cycle)) {
                if (!cycle.empty()) {
                    return cycle;
                }
            }
        }

        return std::nullopt;
    }

    std::optional<std::string> resolve(
        const std::string& name,
        std::set<std::string> resolving = {}
    ) const {
        if (!values.contains(name)) {
            return std::nullopt;
        }

        if (resolving.contains(name)) {
            return std::nullopt;
        }

        resolving.insert(name);

        std::string result = values.at(name);

        /*
         * The resolver intentionally handles the common design-token form
         * var(--token). A production CSS engine must also account for fallback
         * grammar, registered custom-property syntax, computed values, and
         * cascade scope.
         */
        const std::regex pattern(
            R"(var\(\s*(--[-_a-zA-Z0-9]+)\s*\))"
        );

        std::smatch match;

        while (std::regex_search(result, match, pattern)) {
            const std::string dependency = match[1].str();

            auto resolved = resolve(dependency, resolving);

            if (!resolved.has_value()) {
                return std::nullopt;
            }

            result.replace(
                static_cast<std::size_t>(match.position()),
                static_cast<std::size_t>(match.length()),
                *resolved
            );
        }

        return result;
    }
};

static bool isLogicalProperty(const std::string& property) {
    static const std::regex logical(
        R"((margin|padding|border|inset)-(block|inline)(-.+)?)"
    );

    return std::regex_match(property, logical);
}

static bool isPhysicalDirectionalProperty(const std::string& property) {
    static const std::set<std::string> physical = {
        "margin-left",
        "margin-right",
        "padding-left",
        "padding-right",
        "left",
        "right",
        "top",
        "bottom",
        "border-left",
        "border-right"
    };

    return physical.contains(property);
}

static int countMatches(
    const std::string& value,
    const std::regex& pattern
) {
    return static_cast<int>(
        std::distance(
            std::sregex_iterator(value.begin(), value.end(), pattern),
            std::sregex_iterator()
        )
    );
}

class CssAuditor {
public:
    AuditReport audit(const CssSystem& system) const {
        AuditReport report;

        auditTokens(system, report);
        auditSelectors(system, report);
        auditDeclarations(system, report);

        return report;
    }

private:
    static void addIssue(
        AuditReport& report,
        const std::string& severity,
        const std::string& component,
        const std::string& message
    ) {
        report.issues.push_back({
            severity,
            component,
            message
        });
    }

    static void auditTokens(
        const CssSystem& system,
        AuditReport& report
    ) {
        report.featureCounts["custom property definitions"] =
            static_cast<int>(system.tokens.size());

        int varUses = 0;

        for (const auto& token : system.tokens) {
            varUses += countMatches(
                token.value,
                std::regex(R"(var\()")
            );

            if (!startsWith(token.name, "--")) {
                addIssue(
                    report,
                    "ERROR",
                    "tokens",
                    "Custom property name does not begin with '--': "
                        + token.name
                );
            }
        }

        report.featureCounts["var() references"] = varUses;

        TokenGraph graph(system.tokens);

        std::string tokenName;
        std::string dependency;

        if (graph.hasUndefinedReference(tokenName, dependency)) {
            addIssue(
                report,
                "ERROR",
                "tokens",
                tokenName + " references undefined " + dependency
            );
        }

        if (auto cycle = graph.findCycle(); cycle.has_value()) {
            addIssue(
                report,
                "ERROR",
                "tokens",
                "Custom-property dependency cycle: " + *cycle
            );
        }

        for (const auto& token : system.tokens) {
            if (auto resolved = graph.resolve(token.name);
                resolved.has_value()) {
                if (token.name == "--surface-raised") {
                    std::cout
                        << "Resolved --surface-raised: "
                        << *resolved
                        << '\n';
                }
            }
        }
    }

    static void auditSelectors(
        const CssSystem& system,
        AuditReport& report
    ) {
        for (const auto& rule : system.rules) {
            const auto& selector = rule.selector;

            if (selector.find(":is(") != std::string::npos) {
                report.featureCounts[":is() selectors"]++;
            }

            if (selector.find(":where(") != std::string::npos) {
                report.featureCounts[":where() selectors"]++;
            }

            if (selector.find(":has(") != std::string::npos) {
                report.featureCounts[":has() selectors"]++;
            }

            /*
             * :where() is appropriate for defaults that should not create
             * difficult override chains. The audit flags a component that
             * combines :where() with an explicit !important declaration.
             */
            if (
                selector.find(":where(") != std::string::npos &&
                rule.declarations.contains("all") &&
                rule.declarations.at("all").find("!important")
                    != std::string::npos
            ) {
                addIssue(
                    report,
                    "WARNING",
                    rule.purpose,
                    ":where() is being paired with !important; "
                    "review the intended cascade."
                );
            }

            /*
             * :has() is a relationship selector. It should describe a real
             * component relationship, such as a field reacting to an invalid
             * descendant control.
             */
            if (
                selector.find(":has(*)") != std::string::npos
            ) {
                addIssue(
                    report,
                    "WARNING",
                    rule.purpose,
                    ":has(*) is broad. Prefer a meaningful descendant "
                    "relationship when the component permits it."
                );
            }
        }
    }

    static void auditDeclarations(
        const CssSystem& system,
        AuditReport& report
    ) {
        for (const auto& rule : system.rules) {
            for (const auto& [property, value] : rule.declarations) {
                if (isLogicalProperty(property)) {
                    report.featureCounts["logical properties"]++;
                }

                if (isPhysicalDirectionalProperty(property)) {
                    report.featureCounts["physical directional properties"]++;

                    addIssue(
                        report,
                        "WARNING",
                        rule.purpose,
                        "Physical directional property '" + property
                            + "' may prevent writing-mode-aware reuse."
                    );
                }

                if (value.find("var(") != std::string::npos) {
                    report.featureCounts["tokenized declarations"]++;
                }
            }
        }
    }
};

static CssSystem createProductionSystem() {
    CssSystem system;

    system.tokens = {
        {"--color-brand", "#2563eb", true},
        {"--color-brand-strong", "#1d4ed8", true},
        {"--color-surface", "#ffffff", true},
        {"--color-surface-raised", "var(--color-surface)", true},
        {"--color-text", "#172033", true},
        {"--color-muted", "#64748b", true},
        {"--color-danger", "#b91c1c", true},
        {"--space-2", "0.5rem", true},
        {"--space-3", "0.75rem", true},
        {"--space-4", "1rem", true},
        {"--radius-md", "0.75rem", true},
    };

    system.rules = {
        {
            ".application",
            {
                {"max-inline-size", "72rem"},
                {"margin-inline", "auto"},
                {"padding-block", "var(--space-6, 1.5rem)"},
                {"padding-inline", "var(--space-4)"}
            },
            "application shell"
        },
        {
            ".application > header",
            {
                {"display", "flex"},
                {"gap", "var(--space-4, 1rem)"},
                {"padding-block", "var(--space-3)"}
            },
            "application header"
        },
        {
            ".toolbar:has(button[aria-expanded=\"true\"])",
            {
                {"outline", "2px solid var(--color-brand)"},
                {"outline-offset", "0.25rem"}
            },
            "interactive toolbar state"
        },
        {
            ".card:is(:hover, :focus-within)",
            {
                {"border-color", "var(--color-brand)"}
            },
            "card interaction state"
        },
        {
            ".card:where(.compact)",
            {
                {"padding-block", "var(--space-3)"}
            },
            "card low-specificity variant"
        },
        {
            ".form-field:has(input:invalid)",
            {
                {"border-block-start", "2px solid var(--color-danger)"},
                {"padding-block", "var(--space-3)"}
            },
            "validation-aware form field"
        },
        {
            ".form-field > :is(input, select, textarea)",
            {
                {"padding-inline", "var(--space-3)"},
                {"padding-block", "var(--space-2)"},
                {"min-inline-size", "0"}
            },
            "form-control group"
        },
        {
            ".form-field > :where(.help, .status)",
            {
                {"font-size", "0.875rem"},
                {"color", "var(--color-muted)"}
            },
            "form supporting text"
        }
    };

    return system;
}

static CssSystem createBrokenSystem() {
    CssSystem system = createProductionSystem();

    /*
     * These entries intentionally represent architecture problems so the
     * audit engine can demonstrate real failure detection.
     */
    system.tokens.push_back({
        "--broken-token",
        "var(--missing-token)",
        true
    });

    system.tokens.push_back({
        "--cycle-a",
        "var(--cycle-b)",
        true
    });

    system.tokens.push_back({
        "--cycle-b",
        "var(--cycle-a)",
        true
    });

    system.rules.push_back({
        ".legacy-card",
        {
            {"padding-left", "1rem"},
            {"margin-right", "auto"}
        },
        "legacy card compatibility"
    });

    return system;
}

static void printReport(const AuditReport& report) {
    std::cout << "\nCSS SYSTEM AUDIT\n";
    std::cout << "================\n";

    std::cout << "\nFeature inventory\n";
    std::cout << "-----------------\n";

    for (const auto& [feature, count] : report.featureCounts) {
        std::cout << std::left
                  << std::setw(36)
                  << feature
                  << count
                  << '\n';
    }

    std::cout << "\nFindings\n";
    std::cout << "--------\n";

    if (report.issues.empty()) {
        std::cout << "No findings.\n";
        return;
    }

    for (const auto& issue : report.issues) {
        std::cout
            << '[' << issue.severity << "] "
            << issue.component << ": "
            << issue.message
            << '\n';
    }

    std::cout << "\nAudit state: "
              << (report.passed() ? "PASS" : "FAIL")
              << '\n';
}

static void printArchitectureCaseStudy() {
    std::cout << "\nCASE STUDY: COMPONENT LIBRARY ARCHITECTURE\n";
    std::cout << "==========================================\n";

    std::cout
        << "The component library separates responsibilities across six "
        << "modern CSS mechanisms.\n\n";

    std::cout
        << "Custom properties provide the token layer. Components consume "
        << "var(--token) values instead of embedding every theme value.\n";

    std::cout
        << "Nesting keeps parent-child styling relationships local to the "
        << "component rule, such as an application header inside .application.\n";

    std::cout
        << ":is() groups selectors when several element or state forms share "
        << "the same declaration while retaining the specificity behavior "
        << "defined by the most specific argument.\n";

    std::cout
        << ":where() groups selectors for defaults whose specificity should "
        << "remain zero, making component-level overrides easier to maintain.\n";

    std::cout
        << ":has() allows a component to react to a descendant relationship, "
        << "such as .form-field:has(input:invalid), without requiring a "
        << "separate state class maintained by JavaScript.\n";

    std::cout
        << "Logical properties describe block and inline axes. A component "
        << "using padding-inline and border-block-start expresses layout "
        << "intent without assuming left-to-right horizontal coordinates.\n";
}

static void demonstrateFailureModes() {
    std::cout << "\nFAILURE-MODE ANALYSIS\n";
    std::cout << "=====================\n";

    std::cout
        << "Undefined custom-property references can invalidate a "
        << "computed declaration when no usable fallback exists.\n";

    std::cout
        << "Custom-property cycles create an invalid dependency graph and "
        << "must be prevented in a design-token system.\n";

    std::cout
        << "Excessive selector specificity can make component variants "
        << "difficult to override. :where() is useful when a selector "
        << "should remain deliberately weak.\n";

    std::cout
        << "Broad :has() relationships can create unnecessary style "
        << "dependencies. Component-specific descendants make intent clearer "
        << "and give browsers a more constrained selector relationship.\n";

    std::cout
        << "Physical left/right declarations can encode assumptions about "
        << "writing direction. Logical properties avoid that coupling.\n";

    std::cout
        << "A CSS audit tool should not claim to be a browser CSS parser. "
        << "The case study therefore treats parsing and rendering as external "
        << "browser responsibilities and concentrates on architectural "
        << "constraints that can be checked from structured rules.\n";
}

static void demonstrateTokenResolution() {
    std::cout << "\nTOKEN RESOLUTION\n";
    std::cout << "================\n";

    const CssSystem system = createProductionSystem();
    const TokenGraph graph(system.tokens);

    for (const std::string& name : {
        "--color-surface",
        "--color-surface-raised",
        "--color-brand"
    }) {
        const auto resolved = graph.resolve(name);

        std::cout
            << name
            << " => "
            << (resolved.has_value() ? *resolved : "<unresolvable>")
            << '\n';
    }
}

static void runBrokenSystemAudit() {
    std::cout << "\nINTENTIONAL FAILURE CASES\n";
    std::cout << "=========================\n";

    const CssSystem broken = createBrokenSystem();
    const CssAuditor auditor;
    const AuditReport report = auditor.audit(broken);

    printReport(report);
}

int main() {
    try {
        std::cout << "MODERN CSS DESIGN-SYSTEM AUDIT ENGINE\n";
        std::cout << "=====================================\n";

        printArchitectureCaseStudy();
        demonstrateTokenResolution();

        std::cout << "\nPRODUCTION SYSTEM AUDIT\n";
        std::cout << "=======================\n";

        const CssSystem production = createProductionSystem();
        const CssAuditor auditor;
        const AuditReport report = auditor.audit(production);

        printReport(report);

        demonstrateFailureModes();
        runBrokenSystemAudit();

        std::cout
            << "\nC++17 case study completed. The program models CSS "
            << "architecture rather than replacing a browser's cascade, "
            << "selector engine, or layout engine.\n";

        return 0;
    } catch (const std::exception& error) {
        std::cerr
            << "Fatal audit error: "
            << error.what()
            << '\n';

        return 1;
    }
}
