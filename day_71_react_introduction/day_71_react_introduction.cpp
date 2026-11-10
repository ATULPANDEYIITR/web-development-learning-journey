#include <algorithm>
#include <cctype>
#include <functional>
#include <iostream>
#include <map>
#include <memory>
#include <optional>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

using namespace std;


// ---------------------------------------------------------
// Domain model: Virtual DOM
// ---------------------------------------------------------

enum class NodeType {
    Element,
    Text,
    Fragment
};

enum class PatchType {
    Replace,
    UpdateText,
    UpdateProps,
    Insert,
    Remove
};

struct Patch {
    PatchType type;
    string path;
    string description;
};

struct VNode {
    NodeType type;
    string tag;
    string text;
    map<string, string> props;
    vector<shared_ptr<VNode>> children;

    static shared_ptr<VNode> createText(const string& value) {
        auto node = make_shared<VNode>();

        node->type = NodeType::Text;
        node->text = value;

        return node;
    }

    static shared_ptr<VNode> createElement(
        const string& tag,
        map<string, string> props = {},
        vector<shared_ptr<VNode>> children = {}
    ) {
        if (tag.empty()) {
            throw invalid_argument("Element tag cannot be empty.");
        }

        for (unsigned char character : tag) {
            if (!isalnum(character) && character != '-') {
                throw invalid_argument("Invalid element tag.");
            }
        }

        auto node = make_shared<VNode>();

        node->type = NodeType::Element;
        node->tag = tag;
        node->props = move(props);
        node->children = move(children);

        return node;
    }

    static shared_ptr<VNode> createFragment(
        vector<shared_ptr<VNode>> children = {}
    ) {
        auto node = make_shared<VNode>();

        node->type = NodeType::Fragment;
        node->children = move(children);

        return node;
    }
};


// ---------------------------------------------------------
// Component architecture
// ---------------------------------------------------------

using Props = map<string, string>;
using ComponentFunction = function<shared_ptr<VNode>(const Props&)>;

class ComponentRegistry {
private:
    unordered_map<string, ComponentFunction> components;

public:
    void registerComponent(
        const string& name,
        ComponentFunction function
    ) {
        if (name.empty() || !function) {
            throw invalid_argument("Invalid component registration.");
        }

        if (components.count(name)) {
            throw invalid_argument("Duplicate component: " + name);
        }

        components.emplace(name, move(function));
    }

    shared_ptr<VNode> render(
        const string& name,
        const Props& props = {}
    ) const {
        auto it = components.find(name);

        if (it == components.end()) {
            throw runtime_error("Unknown component: " + name);
        }

        auto result = it->second(props);

        if (!result) {
            throw runtime_error(
                "Component returned a null virtual node."
            );
        }

        return result;
    }
};


// ---------------------------------------------------------
// HTML rendering and escaping
// ---------------------------------------------------------

string escapeHTML(const string& value) {
    string result;

    for (char character : value) {
        switch (character) {
            case '&': result += "&amp;"; break;
            case '<': result += "&lt;"; break;
            case '>': result += "&gt;"; break;
            case '"': result += "&quot;"; break;
            case '\'': result += "&#39;"; break;
            default: result += character;
        }
    }

    return result;
}

const set<string> VOID_ELEMENTS = {
    "area", "base", "br", "col", "embed",
    "hr", "img", "input", "link", "meta",
    "param", "source", "track", "wbr"
};

string renderHTML(const shared_ptr<VNode>& node) {
    if (!node) {
        throw runtime_error("Cannot render null node.");
    }

    if (node->type == NodeType::Text) {
        return escapeHTML(node->text);
    }

    if (node->type == NodeType::Fragment) {
        string result;

        for (const auto& child : node->children) {
            result += renderHTML(child);
        }

        return result;
    }

    string result = "<" + node->tag;

    for (const auto& [name, value] : node->props) {
        if (name.rfind("on", 0) == 0) {
            continue;
        }

        if (name.empty()) {
            throw runtime_error("Empty attribute name.");
        }

        for (unsigned char character : name) {
            if (!isalnum(character) && character != '-' && character != '_') {
                throw runtime_error("Invalid attribute name.");
            }
        }

        result += " " + name + "=\"" + escapeHTML(value) + "\"";
    }

    if (VOID_ELEMENTS.count(node->tag)) {
        if (!node->children.empty()) {
            throw runtime_error(
                "Void HTML elements cannot contain children."
            );
        }

        return result + "/>";
    }

    result += ">";

    for (const auto& child : node->children) {
        result += renderHTML(child);
    }

    result += "</" + node->tag + ">";

    return result;
}


// ---------------------------------------------------------
// Virtual DOM reconciliation
// ---------------------------------------------------------

void reconcile(
    const shared_ptr<VNode>& oldNode,
    const shared_ptr<VNode>& newNode,
    const string& path,
    vector<Patch>& patches
) {
    if (!oldNode || !newNode) {
        patches.push_back({
            PatchType::Replace,
            path,
            "Replace missing node"
        });
        return;
    }

    if (oldNode->type != newNode->type) {
        patches.push_back({
            PatchType::Replace,
            path,
            "Node type changed"
        });
        return;
    }

    if (oldNode->type == NodeType::Text) {
        if (oldNode->text != newNode->text) {
            patches.push_back({
                PatchType::UpdateText,
                path,
                "Text content changed"
            });
        }
        return;
    }

    if (oldNode->tag != newNode->tag) {
        patches.push_back({
            PatchType::Replace,
            path,
            "Element tag changed"
        });
        return;
    }

    if (oldNode->props != newNode->props) {
        patches.push_back({
            PatchType::UpdateProps,
            path,
            "Element properties changed"
        });
    }

    size_t maximum = max(
        oldNode->children.size(),
        newNode->children.size()
    );

    for (size_t index = 0; index < maximum; ++index) {
        string childPath = path + "." + to_string(index);

        if (index >= oldNode->children.size()) {
            patches.push_back({
                PatchType::Insert,
                childPath,
                "Insert child"
            });
        } else if (index >= newNode->children.size()) {
            patches.push_back({
                PatchType::Remove,
                childPath,
                "Remove child"
            });
        } else {
            reconcile(
                oldNode->children[index],
                newNode->children[index],
                childPath,
                patches
            );
        }
    }
}


// ---------------------------------------------------------
// Application state
// ---------------------------------------------------------

class CounterState {
private:
    int value = 0;

public:
    int getValue() const {
        return value;
    }

    void increment() {
        if (value == 1000000) {
            throw overflow_error("Counter limit reached.");
        }

        ++value;
    }

    void decrement() {
        if (value == 0) {
            throw underflow_error("Counter cannot become negative.");
        }

        --value;
    }

    void reset() {
        value = 0;
    }
};


// ---------------------------------------------------------
// Component definitions
// ---------------------------------------------------------

void registerComponents(ComponentRegistry& registry) {

    registry.registerComponent(
        "Header",
        [](const Props& props) {
            auto it = props.find("title");

            string title = it == props.end()
                ? "React Introduction"
                : it->second;

            return VNode::createElement(
                "header",
                {{"class", "application-header"}},
                {
                    VNode::createElement(
                        "h1",
                        {},
                        {VNode::createText(title)}
                    )
                }
            );
        }
    );

    registry.registerComponent(
        "Card",
        [](const Props& props) {
            auto title = props.find("title");
            auto description = props.find("description");

            if (title == props.end() ||
                description == props.end()) {
                throw invalid_argument(
                    "Card requires title and description."
                );
            }

            return VNode::createElement(
                "article",
                {{"class", "concept-card"}},
                {
                    VNode::createElement(
                        "h2",
                        {},
                        {VNode::createText(title->second)}
                    ),
                    VNode::createElement(
                        "p",
                        {},
                        {VNode::createText(description->second)}
                    )
                }
            );
        }
    );

    registry.registerComponent(
        "Counter",
        [](const Props& props) {
            auto it = props.find("value");

            if (it == props.end()) {
                throw invalid_argument(
                    "Counter requires a value."
                );
            }

            return VNode::createElement(
                "section",
                {{"class", "counter"}},
                {
                    VNode::createElement(
                        "p",
                        {},
                        {
                            VNode::createText(
                                "Current count: " + it->second
                            )
                        }
                    )
                }
            );
        }
    );
}


// ---------------------------------------------------------
// Application construction
// ---------------------------------------------------------

shared_ptr<VNode> buildApplication(
    const ComponentRegistry& registry,
    int count
) {
    vector<shared_ptr<VNode>> cards;

    vector<pair<string, string>> concepts = {
        {
            "Component Architecture",
            "Reusable interface units organized in a component tree."
        },
        {
            "JSX",
            "JavaScript syntax for describing interface structures."
        },
        {
            "Virtual DOM",
            "An in-memory representation of the rendered interface."
        },
        {
            "Rendering",
            "Updating browser-visible elements from component output."
        }
    };

    for (const auto& [title, description] : concepts) {
        cards.push_back(
            registry.render(
                "Card",
                {
                    {"title", title},
                    {"description", description}
                }
            )
        );
    }

    auto header = registry.render(
        "Header",
        {{"title", "React Introduction"}}
    );

    auto counter = registry.render(
        "Counter",
        {{"value", to_string(count)}}
    );

    auto cardContainer = VNode::createElement(
        "section",
        {{"class", "card-grid"}},
        move(cards)
    );

    return VNode::createElement(
        "main",
        {{"class", "application"}},
        {header, cardContainer, counter}
    );
}


// ---------------------------------------------------------
// Tree inspection
// ---------------------------------------------------------

size_t countNodes(const shared_ptr<VNode>& node) {
    if (!node) {
        return 0;
    }

    size_t count = 1;

    for (const auto& child : node->children) {
        count += countNodes(child);
    }

    return count;
}


// ---------------------------------------------------------
// Test suite
// ---------------------------------------------------------

void runTests() {

    auto escaped = VNode::createText("<script>alert(1)</script>");

    if (renderHTML(escaped).find("<script>") != string::npos) {
        throw runtime_error("HTML escaping test failed.");
    }

    CounterState counter;

    counter.increment();

    if (counter.getValue() != 1) {
        throw runtime_error("Counter increment test failed.");
    }

    counter.decrement();

    if (counter.getValue() != 0) {
        throw runtime_error("Counter decrement test failed.");
    }

    bool underflowDetected = false;

    try {
        counter.decrement();
    } catch (const underflow_error&) {
        underflowDetected = true;
    }

    if (!underflowDetected) {
        throw runtime_error("Counter underflow test failed.");
    }

    auto oldTree = VNode::createElement(
        "p",
        {},
        {VNode::createText("Old")}
    );

    auto newTree = VNode::createElement(
        "p",
        {},
        {VNode::createText("New")}
    );

    vector<Patch> patches;

    reconcile(oldTree, newTree, "root", patches);

    if (patches.size() != 1 ||
        patches[0].type != PatchType::UpdateText) {
        throw runtime_error("Reconciliation test failed.");
    }

    bool invalidElementDetected = false;

    try {
        VNode::createElement("invalid tag");
    } catch (const invalid_argument&) {
        invalidElementDetected = true;
    }

    if (!invalidElementDetected) {
        throw runtime_error("Tag validation test failed.");
    }

    cout << "All C++ tests passed.\n";
}


// ---------------------------------------------------------
// Main
// ---------------------------------------------------------

int main() {
    try {
        ComponentRegistry registry;
        registerComponents(registry);

        CounterState counter;
        counter.increment();
        counter.increment();

        auto initialTree = buildApplication(registry, 1);
        auto updatedTree = buildApplication(
            registry,
            counter.getValue()
        );

        cout << "REACT INTRODUCTION\n";
        cout << "==================\n\n";

        cout << "Rendered virtual DOM:\n";
        cout << renderHTML(initialTree) << "\n\n";

        cout << "Node count: "
             << countNodes(initialTree) << "\n";

        cout << "\nReconciliation patches:\n";

        vector<Patch> patches;

        reconcile(
            initialTree,
            updatedTree,
            "root",
            patches
        );

        for (const auto& patch : patches) {
            cout << patch.description
                 << " at "
                 << patch.path
                 << "\n";
        }

        runTests();

    } catch (const exception& error) {
        cerr << "Application error: "
             << error.what() << "\n";

        return 1;
    }

    return 0;
}
