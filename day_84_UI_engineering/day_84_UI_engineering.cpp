#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <regex>
#include <set>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

/*
 * UI Engineering: Repository-scale Design System Governance.
 *
 * C++17 implementation of:
 * - Token management
 * - Reusable component definitions
 * - Component dependency validation
 * - Accessibility policy evaluation
 * - Design-system approval
 * - Theme configuration
 * - Production component release eligibility
 */

using namespace std;

enum class TokenType {
    Color,
    Spacing,
    Typography,
    Radius,
    Elevation,
    Motion
};

enum class ComponentState {
    Draft,
    Review,
    Approved,
    Deprecated
};

enum class AccessibilityLevel {
    A,
    AA,
    AAA
};

enum class Severity {
    Error,
    Warning
};

string toString(ComponentState state) {
    switch (state) {
        case ComponentState::Draft: return "Draft";
        case ComponentState::Review: return "Review";
        case ComponentState::Approved: return "Approved";
        case ComponentState::Deprecated: return "Deprecated";
    }
    throw logic_error("Unknown component state");
}

struct Token {
    string name;
    TokenType type;
    string value;
    optional<string> alias;
};

struct AccessibilityPolicy {
    string semanticRole;
    bool accessibleName;
    bool keyboardOperable;
    bool visibleFocus;
    double contrastRatio;
    AccessibilityLevel level = AccessibilityLevel::AA;
};

struct Component {
    string name;
    string version;
    string category;
    map<string, string> properties;
    vector<string> tokenDependencies;
    vector<string> componentDependencies;
    AccessibilityPolicy accessibility;
    ComponentState state = ComponentState::Draft;
};

struct Finding {
    Severity severity;
    string subject;
    string message;
};

class TokenRegistry {
private:
    map<string, Token> tokens;
    map<string, map<string, string>> themes;

public:
    void registerToken(const Token& token) {
        static const regex identifier(
            R"(^[a-z][a-z0-9-]*(\.[a-z][a-z0-9-]*)*$)"
        );

        if (!regex_match(token.name, identifier)) {
            throw invalid_argument("Invalid token name: " + token.name);
        }

        if (tokens.count(token.name)) {
            throw invalid_argument("Duplicate token: " + token.name);
        }

        if (token.value.empty()) {
            throw invalid_argument("Token value cannot be empty");
        }

        if (token.alias && *token.alias == token.name) {
            throw invalid_argument("Token cannot reference itself");
        }

        if (token.type == TokenType::Color && !token.alias) {
            static const regex colorPattern(R"(^#[0-9a-fA-F]{6}$)");

            if (!regex_match(token.value, colorPattern)) {
                throw invalid_argument("Invalid color: " + token.value);
            }
        }

        tokens.emplace(token.name, token);
    }

    string resolve(
        const string& name,
        const optional<string>& theme = nullopt
    ) const {
        set<string> visited;
        string current = name;

        while (true) {
            if (!visited.insert(current).second) {
                throw runtime_error("Circular token alias: " + current);
            }

            if (theme && themes.count(*theme)) {
                const auto& overrides = themes.at(*theme);
                auto overrideIt = overrides.find(current);

                if (overrideIt != overrides.end()) {
                    return overrideIt->second;
                }
            }

            auto it = tokens.find(current);

            if (it == tokens.end()) {
                throw out_of_range("Unknown token: " + current);
            }

            if (!it->second.alias) {
                return it->second.value;
            }

            current = *it->second.alias;
        }
    }

    void registerTheme(
        const string& name,
        const map<string, string>& overrides
    ) {
        if (themes.count(name)) {
            throw invalid_argument("Duplicate theme: " + name);
        }

        for (const auto& [tokenName, value] : overrides) {
            if (!tokens.count(tokenName)) {
                throw invalid_argument(
                    "Unknown theme token: " + tokenName
                );
            }

            if (value.empty()) {
                throw invalid_argument("Empty theme override");
            }
        }

        themes.emplace(name, overrides);
    }

    size_t size() const {
        return tokens.size();
    }
};

class AccessibilityEngine {
public:
    static double luminance(const string& color) {
        static const regex pattern(R"(^#[0-9a-fA-F]{6}$)");

        if (!regex_match(color, pattern)) {
            throw invalid_argument("Invalid hexadecimal color");
        }

        vector<double> channels;

        for (int i : {1, 3, 5}) {
            int value = stoi(color.substr(i, 2), nullptr, 16);
            double normalized = value / 255.0;

            channels.push_back(
                normalized <= 0.04045
                    ? normalized / 12.92
                    : pow((normalized + 0.055) / 1.055, 2.4)
            );
        }

        return 0.2126 * channels[0]
            + 0.7152 * channels[1]
            + 0.0722 * channels[2];
    }

    static double contrast(
        const string& foreground,
        const string& background
    ) {
        double first = luminance(foreground);
        double second = luminance(background);

        return (max(first, second) + 0.05)
            / (min(first, second) + 0.05);
    }

    static vector<string> evaluate(
        const AccessibilityPolicy& policy
    ) {
        vector<string> errors;

        if (policy.semanticRole.empty()) {
            errors.push_back("Missing semantic role");
        }

        if (!policy.accessibleName) {
            errors.push_back("Missing accessible name");
        }

        if (!policy.keyboardOperable) {
            errors.push_back("Keyboard operation unavailable");
        }

        if (!policy.visibleFocus) {
            errors.push_back("Visible focus indicator unavailable");
        }

        double minimum = 4.5;

        if (policy.level == AccessibilityLevel::AAA) {
            minimum = 7.0;
        } else if (policy.level == AccessibilityLevel::A) {
            minimum = 3.0;
        }

        if (!isfinite(policy.contrastRatio) ||
            policy.contrastRatio < 0 ||
            policy.contrastRatio > 21) {
            errors.push_back("Invalid contrast ratio");
        } else if (policy.contrastRatio < minimum) {
            errors.push_back("Contrast requirement not satisfied");
        }

        return errors;
    }
};

class RepositoryGovernance {
private:
    TokenRegistry& tokenRegistry;
    unordered_map<string, Component> components;

    void visit(
        const string& name,
        set<string>& temporary,
        set<string>& permanent,
        vector<string>& ordered
    ) const {
        if (permanent.count(name)) {
            return;
        }

        if (temporary.count(name)) {
            throw runtime_error(
                "Circular component dependency: " + name
            );
        }

        auto it = components.find(name);

        if (it == components.end()) {
            throw out_of_range("Unknown component: " + name);
        }

        temporary.insert(name);

        for (const string& dependency :
             it->second.componentDependencies) {
            visit(dependency, temporary, permanent, ordered);
        }

        temporary.erase(name);
        permanent.insert(name);
        ordered.push_back(name);
    }

public:
    explicit RepositoryGovernance(TokenRegistry& registry)
        : tokenRegistry(registry) {}

    void registerComponent(Component component) {
        if (component.name.empty() || component.name[0] < 'A' ||
            component.name[0] > 'Z') {
            throw invalid_argument("Invalid component name");
        }

        static const regex versionPattern(R"(^\d+\.\d+\.\d+$)");

        if (!regex_match(component.version, versionPattern)) {
            throw invalid_argument("Invalid semantic version");
        }

        if (components.count(component.name)) {
            throw invalid_argument(
                "Duplicate component: " + component.name
            );
        }

        if (component.category.empty()) {
            throw invalid_argument("Component category is required");
        }

        components.emplace(component.name, move(component));
    }

    vector<string> validate(const string& name) const {
        const auto it = components.find(name);

        if (it == components.end()) {
            throw out_of_range("Component not found: " + name);
        }

        vector<string> errors;
        const Component& component = it->second;

        for (const string& token : component.tokenDependencies) {
            try {
                tokenRegistry.resolve(token);
            } catch (const exception& error) {
                errors.push_back(error.what());
            }
        }

        for (const string& dependency :
             component.componentDependencies) {
            if (!components.count(dependency)) {
                errors.push_back(
                    "Unknown component dependency: " + dependency
                );
            }
        }

        vector<string> accessibilityErrors =
            AccessibilityEngine::evaluate(component.accessibility);

        errors.insert(
            errors.end(),
            accessibilityErrors.begin(),
            accessibilityErrors.end()
        );

        return errors;
    }

    vector<string> dependencyOrder() const {
        set<string> temporary;
        set<string> permanent;
        vector<string> ordered;

        for (const auto& [name, component] : components) {
            visit(name, temporary, permanent, ordered);
        }

        return ordered;
    }

    void moveToReview(const string& name) {
        auto it = components.find(name);

        if (it == components.end()) {
            throw out_of_range("Component not found");
        }

        if (it->second.state != ComponentState::Draft) {
            throw logic_error("Only draft components can enter review");
        }

        it->second.state = ComponentState::Review;
    }

    void approve(const string& name) {
        auto it = components.find(name);

        if (it == components.end()) {
            throw out_of_range("Component not found");
        }

        if (it->second.state != ComponentState::Review) {
            throw logic_error("Component must be under review");
        }

        vector<string> errors = validate(name);

        if (!errors.empty()) {
            string message = "Approval rejected:";

            for (const string& error : errors) {
                message += "\n- " + error;
            }

            throw runtime_error(message);
        }

        it->second.state = ComponentState::Approved;
    }

    bool eligibleForRelease(const string& name) const {
        auto it = components.find(name);

        if (it == components.end()) {
            return false;
        }

        if (it->second.state != ComponentState::Approved) {
            return false;
        }

        return validate(name).empty();
    }

    const Component& get(const string& name) const {
        auto it = components.find(name);

        if (it == components.end()) {
            throw out_of_range("Unknown component");
        }

        return it->second;
    }

    size_t size() const {
        return components.size();
    }
};

int main() {
    try {
        TokenRegistry tokens;

        tokens.registerToken({
            "color.brand.primary",
            TokenType::Color,
            "#2457C5",
            nullopt
        });

        tokens.registerToken({
            "color.text.primary",
            TokenType::Color,
            "#172033",
            nullopt
        });

        tokens.registerToken({
            "color.action.primary",
            TokenType::Color,
            "color.brand.primary",
            "color.brand.primary"
        });

        tokens.registerToken({
            "spacing.medium",
            TokenType::Spacing,
            "16px",
            nullopt
        });

        tokens.registerTheme("dark", {
            {"color.brand.primary", "#8CAFFF"},
            {"color.text.primary", "#FFFFFF"}
        });

        cout << "Token count: " << tokens.size() << "\n";
        cout << "Primary action: "
             << tokens.resolve("color.action.primary") << "\n";

        cout << "Dark theme primary: "
             << tokens.resolve(
                    "color.brand.primary",
                    string("dark")
                )
             << "\n";

        const double primaryContrast =
            AccessibilityEngine::contrast("#FFFFFF", "#2457C5");

        cout << fixed << setprecision(2);
        cout << "Button contrast: "
             << primaryContrast << ":1\n";

        RepositoryGovernance governance(tokens);

        AccessibilityPolicy buttonPolicy{
            "button",
            true,
            true,
            true,
            primaryContrast,
            AccessibilityLevel::AA
        };

        Component button{
            "Button",
            "1.0.0",
            "Actions",
            {
                {"variant", "primary"},
                {"size", "medium"}
            },
            {
                "color.action.primary",
                "spacing.medium"
            },
            {},
            buttonPolicy,
            ComponentState::Draft
        };

        governance.registerComponent(button);

        AccessibilityPolicy iconPolicy{
            "button",
            true,
            true,
            true,
            5.0,
            AccessibilityLevel::AA
        };

        Component iconButton{
            "IconButton",
            "1.0.0",
            "Actions",
            {
                {"icon", "search"},
                {"label", "Search"}
            },
            {
                "color.text.primary"
            },
            {
                "Button"
            },
            iconPolicy,
            ComponentState::Draft
        };

        governance.registerComponent(iconButton);

        cout << "\nDependency order:\n";

        for (const string& name : governance.dependencyOrder()) {
            cout << "  " << name << "\n";
        }

        cout << "\nApproval workflow:\n";

        governance.moveToReview("Button");
        governance.approve("Button");

        governance.moveToReview("IconButton");
        governance.approve("IconButton");

        for (const string& name : {
            string("Button"),
            string("IconButton")
        }) {
            const Component& component = governance.get(name);

            cout << name << ": "
                 << toString(component.state)
                 << ", release eligible: "
                 << boolalpha
                 << governance.eligibleForRelease(name)
                 << "\n";
        }

        cout << "\nFailure handling:\n";

        AccessibilityPolicy invalidPolicy{
            "button",
            false,
            false,
            false,
            2.0,
            AccessibilityLevel::AA
        };

        vector<string> errors =
            AccessibilityEngine::evaluate(invalidPolicy);

        for (const string& error : errors) {
            cout << "  " << error << "\n";
        }

        cout << "\nDependency validation completed.\n";

    } catch (const exception& error) {
        cerr << "Governance failure: " << error.what() << "\n";
        return 1;
    }

    return 0;
}
