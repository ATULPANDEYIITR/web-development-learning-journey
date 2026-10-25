#include <algorithm>
#include <cassert>
#include <cctype>
#include <iostream>
#include <map>
#include <memory>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

using namespace std;

class DOMError : public runtime_error {
public:
    explicit DOMError(const string& message) : runtime_error(message) {}
};

enum class SelectorKind {
    Tag,
    Id,
    Class,
    Attribute
};

struct Selector {
    SelectorKind kind;
    string value;

    static Selector parse(const string& source) {
        if (source.empty()) throw DOMError("Selector cannot be empty.");

        if (source.front() == '#') {
            if (source.size() == 1) throw DOMError("Empty ID selector.");
            return {SelectorKind::Id, source.substr(1)};
        }
        if (source.front() == '.') {
            if (source.size() == 1) throw DOMError("Empty class selector.");
            return {SelectorKind::Class, source.substr(1)};
        }
        if (source.front() == '[' && source.back() == ']') {
            string name = source.substr(1, source.size() - 2);
            if (name.empty()) throw DOMError("Empty attribute selector.");
            return {SelectorKind::Attribute, name};
        }
        if (source.find_first_of(" >+~,:") != string::npos) {
            throw DOMError("Only simple selectors are supported.");
        }
        return {SelectorKind::Tag, source};
    }
};

struct Element {
    string tag;
    map<string, string> attributes;
    string text;
    Element* parent = nullptr;
    vector<unique_ptr<Element>> children;

    explicit Element(string tagName, string content = "")
        : tag(move(tagName)), text(move(content)) {
        transform(tag.begin(), tag.end(), tag.begin(),
                  [](unsigned char c) { return static_cast<char>(tolower(c)); });
        if (tag.empty() || !isalpha(static_cast<unsigned char>(tag[0])) ||
            !all_of(tag.begin(), tag.end(), [](unsigned char c) {
                return isalnum(c) || c == '-';
            })) {
            throw DOMError("Invalid element name.");
        }
    }

    bool contains(const Element* candidate) const {
        if (this == candidate) return true;
        for (const auto& child : children) {
            if (child->contains(candidate)) return true;
        }
        return false;
    }

    Element& append(unique_ptr<Element> child) {
        if (!child) throw DOMError("Cannot append a null child.");
        if (child.get() == this || child->contains(this)) {
            throw DOMError("Mutation would create a cycle.");
        }
        if (child->parent != nullptr) {
            throw DOMError("Child already belongs to a parent.");
        }
        child->parent = this;
        children.push_back(move(child));
        return *children.back();
    }

    void setAttribute(const string& name, const string& value) {
        if (name.empty() || any_of(name.begin(), name.end(),
            [](unsigned char c) { return isspace(c); })) {
            throw DOMError("Invalid attribute name.");
        }
        attributes[name] = value;
    }

    bool matches(const Selector& selector) const {
        switch (selector.kind) {
            case SelectorKind::Tag:
                return tag == selector.value;
            case SelectorKind::Id: {
                auto it = attributes.find("id");
                return it != attributes.end() && it->second == selector.value;
            }
            case SelectorKind::Class: {
                auto it = attributes.find("class");
                if (it == attributes.end()) return false;
                string value = " " + it->second + " ";
                return value.find(" " + selector.value + " ") != string::npos;
            }
            case SelectorKind::Attribute:
                return attributes.count(selector.value) > 0;
        }
        return false;
    }

    void collect(const Selector& selector, vector<Element*>& output) {
        for (auto& child : children) {
            if (child->matches(selector)) output.push_back(child.get());
            child->collect(selector, output);
        }
    }

    vector<Element*> querySelectorAll(const string& source) {
        Selector selector = Selector::parse(source);
        vector<Element*> result;
        collect(selector, result);
        return result;
    }

    Element* querySelector(const string& source) {
        auto results = querySelectorAll(source);
        return results.empty() ? nullptr : results.front();
    }

    void remove() {
        if (!parent) throw DOMError("Root element cannot be removed.");
        auto& siblings = parent->children;
        auto it = find_if(siblings.begin(), siblings.end(),
            [this](const unique_ptr<Element>& item) { return item.get() == this; });
        if (it == siblings.end()) throw DOMError("Parent-child relationship is inconsistent.");
        (*it)->parent = nullptr;
        siblings.erase(it);
    }

    static string escapeHTML(const string& input, bool attribute = false) {
        string result;
        for (char c : input) {
            switch (c) {
                case '&': result += "&amp;"; break;
                case '<': result += "&lt;"; break;
                case '>': result += "&gt;"; break;
                case '"': result += attribute ? "&quot;" : "\""; break;
                case '\'': result += attribute ? "&#39;" : "'"; break;
                default: result += c;
            }
        }
        return result;
    }

    string toHTML() const {
        string output = "<" + tag;
        for (const auto& [key, value] : attributes) {
            output += " " + escapeHTML(key, true) + "=\"" +
                      escapeHTML(value, true) + "\"";
        }
        static const vector<string> voidTags = {
            "area", "base", "br", "col", "embed", "hr", "img", "input",
            "link", "meta", "param", "source", "track", "wbr"
        };
        bool isVoid = find(voidTags.begin(), voidTags.end(), tag) != voidTags.end();
        if (isVoid && (!text.empty() || !children.empty())) {
            throw DOMError("Void elements cannot contain content.");
        }
        output += ">";
        if (isVoid) return output;
        output += escapeHTML(text);
        for (const auto& child : children) output += child->toHTML();
        output += "</" + tag + ">";
        return output;
    }
};

unique_ptr<Element> makeElement(const string& tag, const string& text = "") {
    return make_unique<Element>(tag, text);
}

class RepositoryDashboard {
    unique_ptr<Element> root;

public:
    RepositoryDashboard() : root(makeElement("main")) {
        root->setAttribute("id", "repository");
        root->setAttribute("class", "dashboard");
        root->append(makeElement("h1", "Repository Dashboard"));

        auto status = makeElement("p", "Review queue");
        status->setAttribute("class", "status");
        status->setAttribute("data-state", "ready");
        root->append(move(status));

        auto list = makeElement("ul");
        list->setAttribute("id", "pull-requests");

        const vector<pair<int, string>> entries = {
            {101, "Validate API input"},
            {102, "Improve database indexes"},
            {103, "Fix navigation tests"}
        };

        for (const auto& [number, title] : entries) {
            auto item = makeElement("li");
            item->setAttribute("class", "pull-request");
            item->setAttribute("data-number", to_string(number));
            auto titleElement = makeElement("span", title);
            titleElement->setAttribute("class", "title");
            item->append(move(titleElement));
            list->append(move(item));
        }
        root->append(move(list));
    }

    Element& document() { return *root; }

    void addPullRequest(int number, const string& title) {
        if (number <= 0) throw DOMError("Pull request number must be positive.");
        if (title.find_first_not_of(" \t\r\n") == string::npos) {
            throw DOMError("Title cannot be empty.");
        }
        Element* list = root->querySelector("#pull-requests");
        if (!list) throw DOMError("Pull request list is missing.");

        for (Element* item : list->querySelectorAll(".pull-request")) {
            auto it = item->attributes.find("data-number");
            if (it != item->attributes.end() && it->second == to_string(number)) {
                throw DOMError("Duplicate pull request number.");
            }
        }

        auto item = makeElement("li");
        item->setAttribute("class", "pull-request");
        item->setAttribute("data-number", to_string(number));
        auto label = makeElement("span", title);
        label->setAttribute("class", "title");
        item->append(move(label));
        list->append(move(item));
    }

    void removePullRequest(int number) {
        Element* list = root->querySelector("#pull-requests");
        if (!list) throw DOMError("Pull request list is missing.");
        for (Element* item : list->querySelectorAll(".pull-request")) {
            auto it = item->attributes.find("data-number");
            if (it != item->attributes.end() && it->second == to_string(number)) {
                item->remove();
                return;
            }
        }
        throw DOMError("Pull request not found.");
    }

    void updateFirstTitle(const string& title) {
        Element* list = root->querySelector("#pull-requests");
        Element* item = list ? list->querySelector(".pull-request") : nullptr;
        Element* label = item ? item->querySelector("span") : nullptr;
        if (!label) throw DOMError("First title element is missing.");
        label->text = title;
    }
};

int main() {
    try {
        RepositoryDashboard dashboard;
        Element& root = dashboard.document();

        cout << "Initial DOM:\n" << root.toHTML() << "\n\n";
        assert(root.querySelectorAll(".pull-request").size() == 3);

        dashboard.updateFirstTitle("Validate API input and reject unsafe payloads");
        dashboard.addPullRequest(104, "Add audit logging");
        dashboard.removePullRequest(103);

        cout << "Updated DOM:\n" << root.toHTML() << "\n\n";
        assert(root.querySelectorAll(".pull-request").size() == 3);
        assert(root.querySelector("#missing") == nullptr);

        try {
            dashboard.addPullRequest(104, "Duplicate entry");
            throw DOMError("Duplicate validation unexpectedly passed.");
        } catch (const DOMError& error) {
            if (string(error.what()) == "Duplicate validation unexpectedly passed.") throw;
            cout << "Expected validation failure: " << error.what() << "\n";
        }

        auto unsafe = makeElement("p", "<script>alert(1)</script>");
        assert(unsafe->toHTML().find("&lt;script&gt;") != string::npos);

        cout << "All checks passed.\n";
        cout << "Tree traversal and selector evaluation: O(n) per full scan.\n";
        cout << "Unique ownership through unique_ptr prevents shared ownership and leaks.\n";
    } catch (const exception& error) {
        cerr << "DOM workflow failed: " << error.what() << '\n';
        return 1;
    }
    return 0;
}
