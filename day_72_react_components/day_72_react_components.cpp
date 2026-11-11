#include <algorithm>
#include <functional>
#include <iostream>
#include <map>
#include <memory>
#include <optional>
#include <set>
#include <stdexcept>
#include <string>
#include <utility>
#include <variant>
#include <vector>

using namespace std;

/*
 * React Component Architecture Simulator.
 *
 * Models:
 * - Functional component definitions
 * - Property schemas and validation
 * - Component composition
 * - Reusable component registration
 * - Immutable component properties
 * - Recursive component rendering
 * - Conditional rendering
 * - Dependency and cycle detection
 * - Repository-style component governance
 */

enum class PropType {
    String,
    Number,
    Boolean
};

using PropValue = variant<string, double, bool>;

string typeName(PropType type) {
    switch (type) {
        case PropType::String: return "string";
        case PropType::Number: return "number";
        case PropType::Boolean: return "boolean";
    }
    return "unknown";
}

struct PropDefinition {
    PropType type;
    bool required = false;
    optional<PropValue> defaultValue;
};

using PropMap = map<string, PropValue>;

struct ComponentNode {
    string componentName;
    string nodeId;
    PropMap props;
    vector<shared_ptr<ComponentNode>> children;
};

struct ComponentDefinition {
    string name;
    string description;
    map<string, PropDefinition> schema;
    bool acceptsChildren = true;
};

struct RenderedNode {
    string name;
    string nodeId;
    string output;
    vector<RenderedNode> children;
};

class ComponentError : public runtime_error {
public:
    explicit ComponentError(const string& message)
        : runtime_error(message) {}
};

class ComponentRegistry {
private:
    map<string, ComponentDefinition> components;

public:
    void registerComponent(const ComponentDefinition& definition) {
        if (definition.name.empty()) {
            throw ComponentError("Component name cannot be empty");
        }

        if (components.count(definition.name)) {
            throw ComponentError(
                "Duplicate component: " + definition.name
            );
        }

        components.emplace(definition.name, definition);
    }

    const ComponentDefinition& get(const string& name) const {
        auto it = components.find(name);

        if (it == components.end()) {
            throw ComponentError("Unknown component: " + name);
        }

        return it->second;
    }

    vector<string> names() const {
        vector<string> result;

        for (const auto& entry : components) {
            result.push_back(entry.first);
        }

        return result;
    }
};


class ComponentEngine {
private:
    const ComponentRegistry& registry;

    static bool matchesType(
        const PropValue& value,
        PropType expected
    ) {
        switch (expected) {
            case PropType::String:
                return holds_alternative<string>(value);
            case PropType::Number:
                return holds_alternative<double>(value);
            case PropType::Boolean:
                return holds_alternative<bool>(value);
        }

        return false;
    }

    static string stringify(const PropValue& value) {
        if (holds_alternative<string>(value)) {
            return get<string>(value);
        }

        if (holds_alternative<double>(value)) {
            return to_string(get<double>(value));
        }

        return get<bool>(value) ? "true" : "false";
    }

    PropMap validate(
        const ComponentDefinition& definition,
        const PropMap& supplied
    ) const {
        PropMap result;

        for (const auto& [name, value] : supplied) {
            auto it = definition.schema.find(name);

            if (it == definition.schema.end()) {
                throw ComponentError(
                    definition.name + ": unknown property " + name
                );
            }

            if (!matchesType(value, it->second.type)) {
                throw ComponentError(
                    definition.name + "." + name +
                    " expects " + typeName(it->second.type)
                );
            }

            result.emplace(name, value);
        }

        for (const auto& [name, schema] : definition.schema) {
            if (result.count(name)) {
                continue;
            }

            if (schema.defaultValue.has_value()) {
                result.emplace(name, *schema.defaultValue);
            } else if (schema.required) {
                throw ComponentError(
                    definition.name + ": missing property " + name
                );
            }
        }

        return result;
    }

    RenderedNode renderInternal(
        const ComponentNode& node,
        set<const ComponentNode*>& ancestors
    ) const {
        if (ancestors.count(&node)) {
            throw ComponentError("Circular component composition");
        }

        ancestors.insert(&node);

        const auto& definition = registry.get(node.componentName);

        if (!definition.acceptsChildren && !node.children.empty()) {
            throw ComponentError(
                definition.name + " does not accept children"
            );
        }

        PropMap props = validate(definition, node.props);

        RenderedNode result;
        result.name = definition.name;
        result.nodeId = node.nodeId;

        result.output = "<" + definition.name;

        for (const auto& [name, value] : props) {
            result.output +=
                " " + name + "=\"" + stringify(value) + "\"";
        }

        result.output += ">";

        for (const auto& child : node.children) {
            if (!child) {
                throw ComponentError("Null child component");
            }

            result.children.push_back(
                renderInternal(*child, ancestors)
            );
        }

        result.output += "</" + definition.name + ">";

        ancestors.erase(&node);
        return result;
    }

    static void printTree(
        const RenderedNode& node,
        int depth = 0
    ) {
        cout << string(depth * 2, ' ')
             << node.name
             << " [" << node.nodeId << "] "
             << node.output << '\n';

        for (const auto& child : node.children) {
            printTree(child, depth + 1);
        }
    }

public:
    explicit ComponentEngine(const ComponentRegistry& registry)
        : registry(registry) {}

    RenderedNode render(const ComponentNode& root) const {
        set<const ComponentNode*> ancestors;
        return renderInternal(root, ancestors);
    }

    void display(const RenderedNode& root) const {
        printTree(root);
    }
};


// Component definitions.

ComponentRegistry buildRegistry() {
    ComponentRegistry registry;

    registry.registerComponent({
        "Text",
        "Displays text content",
        {
            {"content", {PropType::String, true, nullopt}},
            {"tone", {PropType::String, false,
                      PropValue(string("normal"))}}
        },
        false
    });

    registry.registerComponent({
        "Button",
        "Reusable interactive button",
        {
            {"label", {PropType::String, true, nullopt}},
            {"disabled", {PropType::Boolean, false,
                          PropValue(false)}},
            {"variant", {PropType::String, false,
                         PropValue(string("primary"))}}
        },
        false
    });

    registry.registerComponent({
        "Badge",
        "Status indicator",
        {
            {"label", {PropType::String, true, nullopt}},
            {"status", {PropType::String, false,
                        PropValue(string("neutral"))}}
        },
        false
    });

    registry.registerComponent({
        "Card",
        "Content composition container",
        {
            {"title", {PropType::String, true, nullopt}},
            {"description", {PropType::String, false,
                             PropValue(string(""))}}
        },
        true
    });

    registry.registerComponent({
        "Conditional",
        "Conditional content wrapper",
        {
            {"visible", {PropType::Boolean, true, nullopt}}
        },
        true
    });

    return registry;
}


shared_ptr<ComponentNode> makeNode(
    string name,
    string id,
    PropMap props = {}
) {
    auto node = make_shared<ComponentNode>();
    node->componentName = move(name);
    node->nodeId = move(id);
    node->props = move(props);
    return node;
}


ComponentNode buildDashboard() {
    ComponentNode dashboard;
    dashboard.componentName = "Card";
    dashboard.nodeId = "project-dashboard";
    dashboard.props = {
        {"title", string("Project Dashboard")},
        {"description", string("Component composition example")}
    };

    dashboard.children.push_back(
        makeNode("Text", "description", {
            {"content", string("System status: operational")}
        })
    );

    dashboard.children.push_back(
        makeNode("Badge", "status", {
            {"label", string("Active")},
            {"status", string("success")}
        })
    );

    dashboard.children.push_back(
        makeNode("Button", "action", {
            {"label", string("Open Projects")},
            {"variant", string("primary")}
        })
    );

    auto conditional = makeNode(
        "Conditional",
        "conditional-section",
        {{"visible", true}}
    );

    conditional->children.push_back(
        makeNode("Text", "additional-info", {
            {"content", string("Additional project information")}
        })
    );

    dashboard.children.push_back(conditional);

    return dashboard;
}


void runTests(const ComponentEngine& engine) {
    // Default property handling.
    auto button = makeNode(
        "Button",
        "test-button",
        {{"label", string("Save")}}
    );

    auto result = engine.render(*button);

    if (result.output.find("disabled=\"false\"") ==
        string::npos) {
        throw ComponentError("Default prop test failed");
    }

    // Missing required property.
    try {
        auto invalid = makeNode("Button", "invalid");
        engine.render(*invalid);
        throw ComponentError("Missing property was accepted");
    } catch (const ComponentError& error) {
        if (string(error.what()) == "Missing property was accepted") {
            throw;
        }
    }

    // Incorrect property type.
    try {
        auto invalid = makeNode(
            "Badge",
            "invalid-badge",
            {{"label", 123.0}}
        );

        engine.render(*invalid);
        throw ComponentError("Incorrect type was accepted");
    } catch (const ComponentError& error) {
        if (string(error.what()) == "Incorrect type was accepted") {
            throw;
        }
    }

    // Unknown property.
    try {
        auto invalid = makeNode(
            "Text",
            "invalid-text",
            {
                {"content", string("Hello")},
                {"unexpected", true}
            }
        );

        engine.render(*invalid);
        throw ComponentError("Unknown property was accepted");
    } catch (const ComponentError& error) {
        if (string(error.what()) == "Unknown property was accepted") {
            throw;
        }
    }

    // Circular composition.
    auto circular = makeNode(
        "Card",
        "circular",
        {{"title", string("Circular")}}
    );

    circular->children.push_back(circular);

    try {
        engine.render(*circular);
        throw ComponentError("Circular composition was accepted");
    } catch (const ComponentError& error) {
        if (string(error.what()) == "Circular composition was accepted") {
            throw;
        }
    }

    cout << "All component tests passed.\n";
}


int main() {
    try {
        const ComponentRegistry registry = buildRegistry();
        const ComponentEngine engine(registry);

        cout << "Registered components:\n";

        for (const auto& name : registry.names()) {
            cout << "- " << name << '\n';
        }

        runTests(engine);

        cout << "\nRendered component hierarchy:\n";

        ComponentNode dashboard = buildDashboard();
        RenderedNode rendered = engine.render(dashboard);

        engine.display(rendered);

    } catch (const exception& error) {
        cerr << "Component system error: "
             << error.what() << '\n';
        return 1;
    }

    return 0;
}
