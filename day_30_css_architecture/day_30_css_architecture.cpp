/*
 * CSS Architecture Governance Engine
 *
 * C++17 case study:
 * A design-system team maintains a repository containing shared CSS for a
 * multi-page developer portal. The team needs enforceable architectural rules
 * so that BEM components, utility classes, component styles, and CSS variables
 * remain separate responsibilities.
 *
 * The program models:
 *   - BEM component ownership
 *   - component elements and modifiers
 *   - utility-class constraints
 *   - design-token/custom-property requirements
 *   - selector specificity
 *   - CSS architecture layers
 *   - merge-time architecture validation
 *   - maintainability diagnostics
 *   - failure reporting
 *
 * Compile:
 *   g++ -std=c++17 -Wall -Wextra -pedantic css_architecture.cpp -o css_architecture
 */

#include <algorithm>
#include <iomanip>
#include <iostream>
#include <map>
#include <regex>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <tuple>
#include <vector>

enum class CssLayer {
    Reset = 0,
    Tokens = 1,
    Base = 2,
    Components = 3,
    Utilities = 4,
    Overrides = 5
};

std::string layerName(CssLayer layer) {
    switch (layer) {
        case CssLayer::Reset:
            return "reset";
        case CssLayer::Tokens:
            return "tokens";
        case CssLayer::Base:
            return "base";
        case CssLayer::Components:
            return "components";
        case CssLayer::Utilities:
            return "utilities";
        case CssLayer::Overrides:
            return "overrides";
    }

    throw std::logic_error("Unknown CSS layer");
}

int layerRank(CssLayer layer) {
    return static_cast<int>(layer);
}

struct Specificity {
    int ids = 0;
    int classes = 0;
    int elements = 0;

    bool operator>(const Specificity& other) const {
        return std::tie(ids, classes, elements) >
               std::tie(other.ids, other.classes, other.elements);
    }

    std::string toString() const {
        return "(" + std::to_string(ids) + ", " +
               std::to_string(classes) + ", " +
               std::to_string(elements) + ")";
    }
};

struct CssRule {
    std::string selector;
    std::map<std::string, std::string> declarations;
    CssLayer layer;
    std::string source;

    std::size_t declarationCount() const {
        return declarations.size();
    }
};

struct Violation {
    std::string category;
    std::string selector;
    std::string message;

    std::string toString() const {
        std::ostringstream output;
        output << category << " [" << selector << "]: " << message;
        return output.str();
    }
};

bool isValidIdentifier(const std::string& value) {
    static const std::regex pattern(
        R"(^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$)"
    );
    return std::regex_match(value, pattern);
}

std::string makeBemBlock(const std::string& block) {
    if (!isValidIdentifier(block)) {
        throw std::invalid_argument("Invalid BEM block: " + block);
    }

    return block;
}

std::string makeBemElement(
    const std::string& block,
    const std::string& element
) {
    makeBemBlock(block);

    if (!isValidIdentifier(element)) {
        throw std::invalid_argument("Invalid BEM element: " + element);
    }

    return block + "__" + element;
}

std::string makeBemModifier(
    const std::string& block,
    const std::string& modifier
) {
    makeBemBlock(block);

    if (!isValidIdentifier(modifier)) {
        throw std::invalid_argument("Invalid BEM modifier: " + modifier);
    }

    return block + "--" + modifier;
}

bool isBemClass(const std::string& className) {
    static const std::regex pattern(
        R"(^[a-z][a-z0-9]*(?:-[a-z0-9]+)*(?:(?:__[a-z][a-z0-9]*(?:-[a-z0-9]+)*)|(?:--[a-z][a-z0-9]*(?:-[a-z0-9]+)*))?$)"
    );

    return std::regex_match(className, pattern);
}

std::set<std::string> utilityClasses() {
    return {
        "u-flex",
        "u-grid",
        "u-gap-sm",
        "u-gap-md",
        "u-gap-lg",
        "u-p-sm",
        "u-p-md",
        "u-p-lg",
        "u-text-center",
        "u-w-full",
        "u-hidden"
    };
}

bool isUtilityClass(const std::string& className) {
    const auto utilities = utilityClasses();
    return utilities.find(className) != utilities.end();
}

std::vector<std::string> selectorClasses(const std::string& selector) {
    static const std::regex classPattern(R"(\.([A-Za-z0-9_-]+))");

    std::vector<std::string> classes;
    for (
        std::sregex_iterator iterator(selector.begin(), selector.end(), classPattern);
        iterator != std::sregex_iterator();
        ++iterator
    ) {
        classes.push_back((*iterator)[1].str());
    }

    return classes;
}

Specificity calculateSpecificity(const std::string& selector) {
    Specificity result;

    static const std::regex idPattern(R"(#[A-Za-z0-9_-]+)");
    static const std::regex classPattern(R"(\.[A-Za-z0-9_-]+)");
    static const std::regex attributePattern(R"(\[[^\]]+\])");
    static const std::regex pseudoClassPattern(
        R"(:[A-Za-z0-9_-]+(?:\([^)]*\))?)"
    );

    result.ids = std::distance(
        std::sregex_iterator(selector.begin(), selector.end(), idPattern),
        std::sregex_iterator()
    );

    result.classes =
        std::distance(
            std::sregex_iterator(
                selector.begin(),
                selector.end(),
                classPattern
            ),
            std::sregex_iterator()
        ) +
        std::distance(
            std::sregex_iterator(
                selector.begin(),
                selector.end(),
                attributePattern
            ),
            std::sregex_iterator()
        ) +
        std::distance(
            std::sregex_iterator(
                selector.begin(),
                selector.end(),
                pseudoClassPattern
            ),
            std::sregex_iterator()
        );

    /*
     * The case study only needs to recognize common HTML element names.
     * A production CSS parser would need a complete selector grammar.
     */
    static const std::set<std::string> elements = {
        "html", "body", "main", "header", "footer", "nav",
        "section", "article", "aside", "div", "span", "button",
        "input", "form", "label", "a", "ul", "ol", "li",
        "p", "h1", "h2", "h3", "img"
    };

    static const std::regex tokenPattern(R"([A-Za-z][A-Za-z0-9-]*)");

    std::string cleaned = selector;

    cleaned = std::regex_replace(
        cleaned,
        idPattern,
        " "
    );
    cleaned = std::regex_replace(
        cleaned,
        classPattern,
        " "
    );
    cleaned = std::regex_replace(
        cleaned,
        attributePattern,
        " "
    );
    cleaned = std::regex_replace(
        cleaned,
        pseudoClassPattern,
        " "
    );

    for (
        std::sregex_iterator iterator(
            cleaned.begin(),
            cleaned.end(),
            tokenPattern
        );
        iterator != std::sregex_iterator();
        ++iterator
    ) {
        std::string token = (*iterator)[0].str();

        if (elements.find(token) != elements.end()) {
            ++result.elements;
        }
    }

    return result;
}

bool isDeepSelector(const std::string& selector) {
    std::size_t whitespaceCount = 0;
    bool previousWhitespace = false;

    for (char character : selector) {
        bool whitespace = std::isspace(
            static_cast<unsigned char>(character)
        );

        if (whitespace && !previousWhitespace) {
            ++whitespaceCount;
        }

        previousWhitespace = whitespace;
    }

    return whitespaceCount >= 2;
}

class Component {
public:
    Component(std::string name, std::string block)
        : name_(std::move(name)),
          block_(makeBemBlock(block)) {}

    void addElement(const std::string& element) {
        elements_.insert(element);
    }

    void addModifier(const std::string& modifier) {
        modifiers_.insert(modifier);
    }

    const std::string& name() const {
        return name_;
    }

    const std::string& block() const {
        return block_;
    }

    std::set<std::string> classes() const {
        std::set<std::string> result{block_};

        for (const auto& element : elements_) {
            result.insert(makeBemElement(block_, element));
        }

        for (const auto& modifier : modifiers_) {
            result.insert(makeBemModifier(block_, modifier));
        }

        return result;
    }

private:
    std::string name_;
    std::string block_;
    std::set<std::string> elements_;
    std::set<std::string> modifiers_;
};

class TokenRegistry {
public:
    void define(
        const std::string& group,
        const std::string& name,
        const std::string& value
    ) {
        if (!isValidIdentifier(name)) {
            throw std::invalid_argument(
                "Invalid design token name: " + name
            );
        }

        tokens_[group][name] = value;
    }

    std::string variable(
        const std::string& group,
        const std::string& name
    ) const {
        auto groupIterator = tokens_.find(group);

        if (groupIterator == tokens_.end()) {
            throw std::out_of_range(
                "Unknown token group: " + group
            );
        }

        auto tokenIterator = groupIterator->second.find(name);

        if (tokenIterator == groupIterator->second.end()) {
            throw std::out_of_range(
                "Unknown design token: " + group + "." + name
            );
        }

        return "var(--" + group + "-" + name + ")";
    }

    std::string render() const {
        std::ostringstream output;
        output << ":root {\n";

        for (const auto& [group, values] : tokens_) {
            for (const auto& [name, value] : values) {
                output << "  --"
                       << group
                       << "-"
                       << name
                       << ": "
                       << value
                       << ";\n";
            }
        }

        output << "}";
        return output.str();
    }

private:
    std::map<std::string, std::map<std::string, std::string>> tokens_;
};

class CssArchitecture {
public:
    void addRule(CssRule rule) {
        rules_.push_back(std::move(rule));
    }

    const std::vector<CssRule>& rules() const {
        return rules_;
    }

    void validateLayerOrder() const {
        int previous = -1;

        for (const auto& rule : rules_) {
            int current = layerRank(rule.layer);

            if (current < previous) {
                throw std::logic_error(
                    "CSS layer ordering is inconsistent near " +
                    rule.selector
                );
            }

            previous = current;
        }
    }

    std::string render() const {
        validateLayerOrder();

        std::ostringstream output;
        CssLayer previousLayer = CssLayer::Reset;
        bool firstRule = true;

        for (const auto& rule : rules_) {
            if (
                firstRule ||
                rule.layer != previousLayer
            ) {
                if (!firstRule) {
                    output << "\n";
                }

                output << "/* " << layerName(rule.layer) << " */\n";
                previousLayer = rule.layer;
                firstRule = false;
            }

            output << rule.selector << " {\n";

            for (const auto& [property, value] : rule.declarations) {
                output << "  "
                       << property
                       << ": "
                       << value
                       << ";\n";
            }

            output << "}\n";
        }

        return output.str();
    }

private:
    std::vector<CssRule> rules_;
};

class ArchitectureLinter {
public:
    ArchitectureLinter(
        std::set<std::string> utilities,
        std::vector<Component> components
    )
        : utilities_(std::move(utilities)),
          components_(std::move(components)) {}

    std::vector<Violation> lint(
        const std::vector<CssRule>& rules
    ) const {
        std::vector<Violation> violations;

        for (const auto& rule : rules) {
            auto classes = selectorClasses(rule.selector);
            auto specificity = calculateSpecificity(rule.selector);

            if (rule.layer == CssLayer::Utilities) {
                if (
                    classes.size() != 1 ||
                    utilities_.find(classes.front()) == utilities_.end()
                ) {
                    violations.push_back({
                        "utility-boundary",
                        rule.selector,
                        "A utility selector should normally contain one recognized utility class."
                    });
                }

                if (
                    specificity.ids != 0 ||
                    specificity.classes != 1 ||
                    specificity.elements != 0
                ) {
                    violations.push_back({
                        "utility-specificity",
                        rule.selector,
                        "Utilities should remain at single-class specificity."
                    });
                }
            }

            if (rule.layer == CssLayer::Components) {
                bool containsUtility = std::any_of(
                    classes.begin(),
                    classes.end(),
                    [](const std::string& className) {
                        return className.rfind("u-", 0) == 0;
                    }
                );

                if (containsUtility) {
                    violations.push_back({
                        "component-boundary",
                        rule.selector,
                        "Utilities should be composed in markup rather than owned by component selectors."
                    });
                }

                if (isDeepSelector(rule.selector)) {
                    violations.push_back({
                        "component-coupling",
                        rule.selector,
                        "Deep descendants make surrounding markup part of the component contract."
                    });
                }
            }

            if (specificity.ids > 0) {
                violations.push_back({
                    "specificity",
                    rule.selector,
                    "ID selectors create unnecessary specificity pressure."
                });
            }

            const std::set<std::string> genericNames = {
                "card", "title", "header", "button", "active"
            };

            for (const auto& className : classes) {
                if (genericNames.find(className) != genericNames.end()) {
                    violations.push_back({
                        "global-naming",
                        rule.selector,
                        "Generic class names make ownership ambiguous."
                    });
                }
            }
        }

        return violations;
    }

private:
    std::set<std::string> utilities_;
    std::vector<Component> components_;
};

CssArchitecture buildArchitecture(TokenRegistry& tokens) {
    tokens.define("color", "surface", "#10141c");
    tokens.define("color", "surface-raised", "#171d27");
    tokens.define("color", "text", "#f5f7fa");
    tokens.define("color", "text-muted", "#aab4c3");
    tokens.define("color", "accent", "#7dd3fc");
    tokens.define("color", "success", "#86efac");
    tokens.define("color", "danger", "#fca5a5");
    tokens.define("color", "border", "#303b4d");

    tokens.define("space", "sm", "0.5rem");
    tokens.define("space", "md", "1rem");
    tokens.define("space", "lg", "1.5rem");

    tokens.define("radius", "md", "0.625rem");
    tokens.define("font", "small", "0.875rem");
    tokens.define("font", "title", "1.5rem");
    tokens.define("font", "weight-bold", "700");

    CssArchitecture architecture;

    architecture.addRule({
        "*",
        {{"box-sizing", "border-box"}},
        CssLayer::Reset,
        "global reset"
    });

    architecture.addRule({
        ":root",
        {
            {"--color-surface", "#10141c"},
            {"--color-surface-raised", "#171d27"},
            {"--color-text", "#f5f7fa"},
            {"--color-text-muted", "#aab4c3"},
            {"--color-accent", "#7dd3fc"},
            {"--color-border", "#303b4d"},
            {"--space-sm", "0.5rem"},
            {"--space-md", "1rem"},
            {"--space-lg", "1.5rem"},
            {"--radius-md", "0.625rem"},
            {"--font-weight-bold", "700"}
        },
        CssLayer::Tokens,
        "design tokens"
    });

    architecture.addRule({
        "body",
        {
            {"margin", "0"},
            {"background", "var(--color-surface)"},
            {"color", "var(--color-text)"},
            {"font-family", "system-ui, sans-serif"}
        },
        CssLayer::Base,
        "document defaults"
    });

    architecture.addRule({
        ".review-card",
        {
            {"background", "var(--color-surface-raised)"},
            {"border", "1px solid var(--color-border)"},
            {"border-radius", "var(--radius-md)"}
        },
        CssLayer::Components,
        "review-card component"
    });

    architecture.addRule({
        ".review-card__header",
        {
            {"display", "flex"},
            {"align-items", "center"},
            {"justify-content", "space-between"},
            {"gap", "var(--space-md)"}
        },
        CssLayer::Components,
        "review-card component"
    });

    architecture.addRule({
        ".review-card__title",
        {
            {"margin", "0"},
            {"font-size", "1.125rem"},
            {"font-weight", "var(--font-weight-bold)"}
        },
        CssLayer::Components,
        "review-card component"
    });

    architecture.addRule({
        ".review-card--approved",
        {
            {"border-color", "var(--color-success, #86efac)"}
        },
        CssLayer::Components,
        "review-card modifier"
    });

    architecture.addRule({
        ".status-badge",
        {
            {"display", "inline-flex"},
            {"align-items", "center"},
            {"padding", "0.25rem 0.5rem"},
            {"border-radius", "999px"},
            {"font-size", "0.875rem"}
        },
        CssLayer::Components,
        "status-badge component"
    });

    architecture.addRule({
        ".status-badge--success",
        {
            {
                "background",
                "color-mix(in srgb, var(--color-success, #86efac) 18%, transparent)"
            },
            {"color", "var(--color-success, #86efac)"}
        },
        CssLayer::Components,
        "status-badge modifier"
    });

    architecture.addRule({
        ".u-flex",
        {{"display", "flex"}},
        CssLayer::Utilities,
        "layout utility"
    });

    architecture.addRule({
        ".u-gap-md",
        {{"gap", "var(--space-md)"}},
        CssLayer::Utilities,
        "spacing utility"
    });

    architecture.addRule({
        ".u-p-md",
        {{"padding", "var(--space-md)"}},
        CssLayer::Utilities,
        "spacing utility"
    });

    return architecture;
}

void printComponents() {
    std::cout << "\nBEM component contracts\n";

    Component reviewCard("Review Card", "review-card");
    reviewCard.addElement("header");
    reviewCard.addElement("title");
    reviewCard.addElement("meta");
    reviewCard.addElement("actions");
    reviewCard.addModifier("approved");
    reviewCard.addModifier("changes-requested");

    std::cout << "Component: " << reviewCard.name() << "\n";

    for (const auto& className : reviewCard.classes()) {
        std::cout << "  ." << className << "\n";
    }

    Component statusBadge("Status Badge", "status-badge");
    statusBadge.addElement("label");
    statusBadge.addModifier("success");
    statusBadge.addModifier("warning");
    statusBadge.addModifier("danger");

    std::cout << "\nComponent: " << statusBadge.name() << "\n";

    for (const auto& className : statusBadge.classes()) {
        std::cout << "  ." << className << "\n";
    }
}

void demonstrateTokens(TokenRegistry& tokens) {
    std::cout << "\nCSS variable registry\n";
    std::cout << tokens.render() << "\n";

    std::cout << "\nSemantic references:\n";
    std::cout << "  spacing: "
              << tokens.variable("space", "md")
              << "\n";
    std::cout << "  surface: "
              << tokens.variable("color", "surface")
              << "\n";
    std::cout << "  radius: "
              << tokens.variable("radius", "md")
              << "\n";

    /*
     * A semantic variable such as --color-surface lets components depend on
     * meaning instead of a literal color. Themes can replace the variable
     * without changing every component selector.
     */
}

void demonstrateSpecificity() {
    std::cout << "\nSelector specificity\n";

    const std::vector<std::string> selectors = {
        ".review-card",
        ".review-card__title",
        ".review-card .review-card__title",
        "article.review-card",
        "#dashboard .review-card"
    };

    for (const auto& selector : selectors) {
        std::cout << "  "
                  << std::left
                  << std::setw(40)
                  << selector
                  << calculateSpecificity(selector).toString()
                  << "\n";
    }
}

void demonstrateArchitectureLinting(
    const CssArchitecture& architecture
) {
    Component reviewCard("Review Card", "review-card");
    Component statusBadge("Status Badge", "status-badge");

    ArchitectureLinter linter(
        utilityClasses(),
        {reviewCard, statusBadge}
    );

    auto violations = linter.lint(architecture.rules());

    std::cout << "\nValid architecture lint result\n";

    if (violations.empty()) {
        std::cout << "  No violations detected.\n";
    } else {
        for (const auto& violation : violations) {
            std::cout << "  " << violation.toString() << "\n";
        }
    }

    std::vector<CssRule> badRules = {
        {
            ".card .title",
            {{"color", "red"}},
            CssLayer::Components,
            "legacy component"
        },
        {
            "#dashboard .review-card",
            {{"padding", "20px"}},
            CssLayer::Components,
            "specificity escalation"
        },
        {
            ".review-card .u-p-md",
            {{"padding", "var(--space-md)"}},
            CssLayer::Components,
            "incorrect utility ownership"
        }
    };

    std::cout << "\nProblematic architecture lint result\n";

    for (const auto& violation : linter.lint(badRules)) {
        std::cout << "  " << violation.toString() << "\n";
    }
}

void demonstrateFailureModes() {
    std::cout << "\nArchitecture failure modes\n";

    const std::map<std::string, std::string> failures = {
        {
            "Generic names",
            ".card and .title provide no reliable ownership boundary."
        },
        {
            "Deep selectors",
            "Descendant-heavy selectors couple styling to DOM hierarchy."
        },
        {
            "Utility overreach",
            "Component-specific utilities become a duplicate component naming system."
        },
        {
            "Repeated literals",
            "Repeated colors and spacing values make coordinated visual changes expensive."
        },
        {
            "Specificity escalation",
            "ID selectors make later overrides harder to reason about."
        },
        {
            "Unbounded tokens",
            "A variable registry without semantic naming becomes difficult to govern."
        }
    };

    for (const auto& [name, explanation] : failures) {
        std::cout << "  " << name << ": "
                  << explanation
                  << "\n";
    }
}

struct Metrics {
    std::size_t rules = 0;
    std::size_t declarations = 0;
    std::size_t highSpecificityRules = 0;
    std::size_t deepSelectors = 0;

    double averageDeclarations() const {
        if (rules == 0) {
            return 0.0;
        }

        return static_cast<double>(declarations) /
               static_cast<double>(rules);
    }
};

Metrics calculateMetrics(
    const std::vector<CssRule>& rules
) {
    Metrics metrics;
    metrics.rules = rules.size();

    for (const auto& rule : rules) {
        metrics.declarations += rule.declarationCount();

        const auto specificity = calculateSpecificity(rule.selector);

        if (
            specificity.ids > 0 ||
            specificity.classes >= 3
        ) {
            ++metrics.highSpecificityRules;
        }

        if (isDeepSelector(rule.selector)) {
            ++metrics.deepSelectors;
        }
    }

    return metrics;
}

void demonstrateMaintainabilityMetrics(
    const CssArchitecture& architecture
) {
    std::cout << "\nMaintainability diagnostics\n";

    Metrics metrics = calculateMetrics(architecture.rules());

    std::cout << "  Rules: "
              << metrics.rules
              << "\n";

    std::cout << "  Declarations: "
              << metrics.declarations
              << "\n";

    std::cout << "  Average declarations/rule: "
              << std::fixed
              << std::setprecision(2)
              << metrics.averageDeclarations()
              << "\n";

    std::cout << "  High-specificity rules: "
              << metrics.highSpecificityRules
              << "\n";

    std::cout << "  Deep selectors: "
              << metrics.deepSelectors
              << "\n";
}

void demonstrateEdgeCases() {
    std::cout << "\nValidation edge cases\n";

    try {
        makeBemBlock("ReviewCard");
        std::cout << "  Unexpected: invalid block accepted.\n";
    } catch (const std::exception& error) {
        std::cout << "  Invalid block rejected: "
                  << error.what()
                  << "\n";
    }

    try {
        makeBemElement("review-card", "status.label");
        std::cout << "  Unexpected: invalid element accepted.\n";
    } catch (const std::exception& error) {
        std::cout << "  Invalid element rejected: "
                  << error.what()
                  << "\n";
    }

    try {
        TokenRegistry registry;
        registry.define("space", "md", "1rem");
        registry.variable("space", "unknown");
        std::cout << "  Unexpected: unknown token accepted.\n";
    } catch (const std::exception& error) {
        std::cout << "  Unknown token rejected: "
                  << error.what()
                  << "\n";
    }
}

void runTests() {
    std::cout << "\nExecutable checks\n";

    if (!isBemClass("review-card")) {
        throw std::runtime_error("BEM block validation failed.");
    }

    if (!isBemClass("review-card__title")) {
        throw std::runtime_error("BEM element validation failed.");
    }

    if (!isBemClass("review-card--approved")) {
        throw std::runtime_error("BEM modifier validation failed.");
    }

    if (isBemClass("review_card")) {
        throw std::runtime_error("Invalid BEM name was accepted.");
    }

    const auto simpleSpecificity =
        calculateSpecificity(".review-card");

    if (
        simpleSpecificity.ids != 0 ||
        simpleSpecificity.classes != 1 ||
        simpleSpecificity.elements != 0
    ) {
        throw std::runtime_error(
            "Unexpected simple class specificity."
        );
    }

    TokenRegistry tokens;
    tokens.define("space", "md", "1rem");

    if (tokens.variable("space", "md") != "var(--space-md)") {
        throw std::runtime_error("Token variable generation failed.");
    }

    CssArchitecture architecture =
        buildArchitecture(tokens);

    architecture.validateLayerOrder();

    ArchitectureLinter linter(
        utilityClasses(),
        {
            Component("Review Card", "review-card")
        }
    );

    if (!linter.lint(architecture.rules()).empty()) {
        throw std::runtime_error(
            "Valid architecture failed linting."
        );
    }

    std::cout << "  All C++ checks passed.\n";
}

int main() {
    try {
        std::cout << "============================================================\n";
        std::cout << "CSS ARCHITECTURE GOVERNANCE ENGINE\n";
        std::cout << "BEM | Utilities | Components | CSS Variables\n";
        std::cout << "============================================================\n";

        TokenRegistry tokens;
        CssArchitecture architecture =
            buildArchitecture(tokens);

        printComponents();
        demonstrateTokens(tokens);
        demonstrateSpecificity();
        demonstrateArchitectureLinting(architecture);
        demonstrateMaintainabilityMetrics(architecture);
        demonstrateFailureModes();
        demonstrateEdgeCases();

        std::cout << "\nGenerated architecture\n";
        std::cout << architecture.render();

        runTests();

        std::cout
            << "\nRepository stylesheet governance simulation completed successfully.\n";

        return 0;
    } catch (const std::exception& error) {
        std::cerr
            << "Fatal architecture validation error: "
            << error.what()
            << "\n";

        return 1;
    }
}
