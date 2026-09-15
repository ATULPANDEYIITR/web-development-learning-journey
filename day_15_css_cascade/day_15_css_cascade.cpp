/*
 * CSS Cascade Case Study
 *
 * Scenario:
 *     A company is building a reusable product-card UI for an e-commerce
 *     dashboard. Several teams contribute CSS:
 *
 *     - global design-system styles
 *     - component styles
 *     - featured-card modifiers
 *     - accessibility overrides
 *     - page-specific styles
 *
 * The system must determine which declaration wins for a property while
 * explaining why competing declarations lose.
 *
 * This C++17 program builds a simplified CSS cascade engine that models:
 *
 *     - elements
 *     - selectors
 *     - declarations
 *     - specificity
 *     - source order
 *     - !important
 *     - inheritance
 *     - CSS-wide keywords
 *     - custom properties
 *     - validation
 *     - debugging traces
 *     - complexity considerations
 *
 * Compile:
 *     g++ -std=c++17 -O2 css_cascade_case_study.cpp -o css_cascade
 */

#include <algorithm>
#include <cctype>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <regex>
#include <sstream>
#include <stdexcept>
#include <string>
#include <tuple>
#include <unordered_map>
#include <vector>

using namespace std;


// ============================================================================
// 1. Utility functions
// ============================================================================

string trim(const string& input) {
    const auto first = input.find_first_not_of(" \t\n\r");

    if (first == string::npos) {
        return "";
    }

    const auto last = input.find_last_not_of(" \t\n\r");

    return input.substr(first, last - first + 1);
}

vector<string> splitWhitespace(const string& input) {
    istringstream stream(input);
    vector<string> parts;
    string part;

    while (stream >> part) {
        parts.push_back(part);
    }

    return parts;
}

bool startsWith(const string& text, const string& prefix) {
    return text.rfind(prefix, 0) == 0;
}


// ============================================================================
// 2. Specificity
// ============================================================================

struct Specificity {
    int id = 0;
    int classAttributePseudoClass = 0;
    int typePseudoElement = 0;

    bool operator<(const Specificity& other) const {
        return tie(
            id,
            classAttributePseudoClass,
            typePseudoElement
        ) <
        tie(
            other.id,
            other.classAttributePseudoClass,
            other.typePseudoElement
        );
    }

    bool operator==(const Specificity& other) const {
        return id == other.id &&
               classAttributePseudoClass ==
                   other.classAttributePseudoClass &&
               typePseudoElement ==
                   other.typePseudoElement;
    }

    string toString() const {
        return "(" +
               to_string(id) + ", " +
               to_string(classAttributePseudoClass) + ", " +
               to_string(typePseudoElement) + ")";
    }
};

Specificity calculateSpecificity(const string& selector) {
    Specificity result;

    // This is an educational approximation. A production browser supports
    // the complete modern Selectors specification and its special specificity
    // rules for selectors such as :where(), :is(), and :not().
    regex idRegex(R"(#[A-Za-z_][A-Za-z0-9_-]*)");
    regex classRegex(R"(\.[A-Za-z_][A-Za-z0-9_-]*)");
    regex attributeRegex(R"(\[[^\]]+\])");
    regex pseudoClassRegex(R"(:[A-Za-z_-][A-Za-z0-9_-]*(?:\([^)]*\))?)");
    regex pseudoElementRegex(R"(::[A-Za-z_-][A-Za-z0-9_-]*)");

    result.id = distance(
        sregex_iterator(selector.begin(), selector.end(), idRegex),
        sregex_iterator()
    );

    const int classCount = distance(
        sregex_iterator(selector.begin(), selector.end(), classRegex),
        sregex_iterator()
    );

    const int attributeCount = distance(
        sregex_iterator(selector.begin(), selector.end(), attributeRegex),
        sregex_iterator()
    );

    int pseudoClassCount = 0;

    for (sregex_iterator it(
             selector.begin(),
             selector.end(),
             pseudoClassRegex);
         it != sregex_iterator();
         ++it) {

        if (it->str().rfind("::", 0) != 0) {
            ++pseudoClassCount;
        }
    }

    const int pseudoElementCount = distance(
        sregex_iterator(
            selector.begin(),
            selector.end(),
            pseudoElementRegex
        ),
        sregex_iterator()
    );

    result.classAttributePseudoClass =
        classCount +
        attributeCount +
        pseudoClassCount;

    string simplified = selector;

    simplified = regex_replace(
        simplified,
        idRegex,
        " "
    );

    simplified = regex_replace(
        simplified,
        classRegex,
        " "
    );

    simplified = regex_replace(
        simplified,
        attributeRegex,
        " "
    );

    simplified = regex_replace(
        simplified,
        pseudoElementRegex,
        " "
    );

    simplified = regex_replace(
        simplified,
        pseudoClassRegex,
        " "
    );

    regex typeRegex(R"((^|[\s>+~])([A-Za-z][A-Za-z0-9_-]*))");

    for (sregex_iterator it(
             simplified.begin(),
             simplified.end(),
             typeRegex);
         it != sregex_iterator();
         ++it) {

        const string typeName = (*it)[2].str();

        if (!typeName.empty()) {
            ++result.typePseudoElement;
        }
    }

    result.typePseudoElement += pseudoElementCount;

    return result;
}


// ============================================================================
// 3. DOM representation
// ============================================================================

struct Element {
    string tag;
    optional<string> id;
    vector<string> classes;
    unordered_map<string, string> attributes;
    unordered_map<string, string> inlineStyles;

    Element* parent = nullptr;
    vector<Element*> children;

    string description() const {
        string result = tag;

        if (id.has_value()) {
            result += "#" + id.value();
        }

        for (const auto& className : classes) {
            result += "." + className;
        }

        return result;
    }

    bool hasClass(const string& className) const {
        return find(
            classes.begin(),
            classes.end(),
            className
        ) != classes.end();
    }
};

void addChild(Element& parent, Element& child) {
    child.parent = &parent;
    parent.children.push_back(&child);
}


// ============================================================================
// 4. Selector matching
// ============================================================================

bool matchesSimpleSelector(
    const Element& element,
    string selector
) {
    selector = trim(selector);

    if (selector.empty()) {
        return false;
    }

    // Pseudo-class matching is not fully implemented in this teaching engine.
    const size_t pseudoPosition = selector.find(':');

    if (pseudoPosition != string::npos) {
        selector = selector.substr(0, pseudoPosition);
    }

    if (selector.empty()) {
        return true;
    }

    regex tagRegex(R"(^([A-Za-z][A-Za-z0-9_-]*)|\*)");

    smatch tagMatch;

    if (regex_search(selector, tagMatch, tagRegex)) {
        string tag = tagMatch.str();

        if (tag != "*" &&
            tag != element.tag) {
            return false;
        }
    }

    regex idRegex(R"(#([A-Za-z_][A-Za-z0-9_-]*))");

    for (sregex_iterator it(
             selector.begin(),
             selector.end(),
             idRegex);
         it != sregex_iterator();
         ++it) {

        const string expectedId = (*it)[1].str();

        if (!element.id.has_value() ||
            element.id.value() != expectedId) {
            return false;
        }
    }

    regex classRegex(R"(\.([A-Za-z_][A-Za-z0-9_-]*))");

    for (sregex_iterator it(
             selector.begin(),
             selector.end(),
             classRegex);
         it != sregex_iterator();
         ++it) {

        const string expectedClass = (*it)[1].str();

        if (!element.hasClass(expectedClass)) {
            return false;
        }
    }

    regex attributeRegex(R"(\[([A-Za-z_][A-Za-z0-9_-]*)(?:=([^\]]+))?\])");

    for (sregex_iterator it(
             selector.begin(),
             selector.end(),
             attributeRegex);
         it != sregex_iterator();
         ++it) {

        const string attributeName = (*it)[1].str();

        auto found = element.attributes.find(attributeName);

        if (found == element.attributes.end()) {
            return false;
        }

        const string expectedValue = (*it)[2].str();

        if (!expectedValue.empty()) {
            string normalizedExpected =
                trim(expectedValue);

            if (!normalizedExpected.empty() &&
                (normalizedExpected.front() == '"' ||
                 normalizedExpected.front() == '\'')) {

                normalizedExpected =
                    normalizedExpected.substr(
                        1,
                        normalizedExpected.size() - 2
                    );
            }

            if (found->second != normalizedExpected) {
                return false;
            }
        }
    }

    return true;
}

bool selectorMatches(
    const Element& element,
    const string& selector
) {
    const string normalized = trim(selector);

    if (normalized.find('>') != string::npos) {
        const size_t position = normalized.rfind('>');

        const string parentSelector =
            trim(normalized.substr(0, position));

        const string childSelector =
            trim(normalized.substr(position + 1));

        if (!matchesSimpleSelector(
                element,
                childSelector)) {
            return false;
        }

        if (element.parent == nullptr) {
            return false;
        }

        return selectorMatches(
            *element.parent,
            parentSelector
        );
    }

    const vector<string> parts =
        splitWhitespace(normalized);

    if (parts.empty()) {
        return false;
    }

    if (parts.size() == 1) {
        return matchesSimpleSelector(
            element,
            parts.front()
        );
    }

    if (!matchesSimpleSelector(
            element,
            parts.back())) {
        return false;
    }

    const Element* ancestor = element.parent;

    for (
        int index = static_cast<int>(parts.size()) - 2;
        index >= 0;
        --index
    ) {
        bool found = false;

        while (ancestor != nullptr) {
            if (matchesSimpleSelector(
                    *ancestor,
                    parts[index])) {

                found = true;
                ancestor = ancestor->parent;
                break;
            }

            ancestor = ancestor->parent;
        }

        if (!found) {
            return false;
        }
    }

    return true;
}


// ============================================================================
// 5. CSS declarations and rules
// ============================================================================

struct Declaration {
    string property;
    string value;
    bool important = false;

    int sourceOrder = 0;
    string selector;
    Specificity specificity;
};

struct Rule {
    string selector;
    vector<Declaration> declarations;
    int sourceOrder = 0;
};

Declaration createDeclaration(
    const string& selector,
    const string& property,
    string value,
    int sourceOrder
) {
    value = trim(value);

    bool important = false;

    const string importantSuffix = "!important";

    if (value.size() >= importantSuffix.size() &&
        value.compare(
            value.size() - importantSuffix.size(),
            importantSuffix.size(),
            importantSuffix
        ) == 0) {

        important = true;

        value = trim(
            value.substr(
                0,
                value.size() - importantSuffix.size()
            )
        );
    }

    return {
        property,
        value,
        important,
        sourceOrder,
        selector,
        calculateSpecificity(selector)
    };
}

Rule createRule(
    const string& selector,
    const map<string, string>& declarations,
    int sourceOrder
) {
    Rule rule{
        selector,
        {},
        sourceOrder
    };

    for (const auto& [property, value] : declarations) {
        rule.declarations.push_back(
            createDeclaration(
                selector,
                property,
                value,
                sourceOrder
            )
        );
    }

    return rule;
}


// ============================================================================
// 6. Cascade comparison
// ============================================================================

bool declarationWins(
    const Declaration& candidate,
    const Declaration& currentWinner
) {
    // Important declarations enter a higher importance category.
    if (candidate.important != currentWinner.important) {
        return candidate.important;
    }

    // This case study models author styles only, so origin is equal.
    if (candidate.specificity !=
        currentWinner.specificity) {

        return currentWinner.specificity <
               candidate.specificity;
    }

    // If the previous dimensions tie, later source order wins.
    return candidate.sourceOrder >
           currentWinner.sourceOrder;
}


// ============================================================================
// 7. Cascade engine
// ============================================================================

class CascadeEngine {
private:
    vector<Rule> rules;

    static const map<string, string> initialValues;

    static bool isInheritedProperty(
        const string& property
    ) {
        static const vector<string> inherited{
            "color",
            "font-family",
            "font-size",
            "font-weight",
            "line-height",
            "text-align",
            "visibility",
            "cursor"
        };

        return find(
            inherited.begin(),
            inherited.end(),
            property
        ) != inherited.end();
    }

    optional<Declaration> inlineDeclaration(
        const Element& element,
        const string& property
    ) const {
        auto found =
            element.inlineStyles.find(property);

        if (found == element.inlineStyles.end()) {
            return nullopt;
        }

        return createDeclaration(
            "style attribute",
            property,
            found->second,
            1000000000
        );
    }

public:
    explicit CascadeEngine(vector<Rule> cssRules)
        : rules(std::move(cssRules)) {}

    vector<Declaration> candidatesFor(
        const Element& element,
        const string& property
    ) const {
        vector<Declaration> candidates;

        for (const Rule& rule : rules) {
            if (!selectorMatches(
                    element,
                    rule.selector)) {
                continue;
            }

            for (const Declaration& declaration :
                 rule.declarations) {

                if (declaration.property == property) {
                    candidates.push_back(declaration);
                }
            }
        }

        const auto inlineValue =
            inlineDeclaration(element, property);

        if (inlineValue.has_value()) {
            candidates.push_back(
                inlineValue.value()
            );
        }

        return candidates;
    }

    string resolve(
        const Element& element,
        const string& property
    ) const {
        vector<Declaration> candidates =
            candidatesFor(element, property);

        if (!candidates.empty()) {
            Declaration winner = candidates.front();

            for (size_t index = 1;
                 index < candidates.size();
                 ++index) {

                if (declarationWins(
                        candidates[index],
                        winner)) {

                    winner = candidates[index];
                }
            }

            const string value =
                trim(winner.value);

            if (value == "inherit") {
                if (element.parent != nullptr) {
                    return resolve(
                        *element.parent,
                        property
                    );
                }

                return initialValue(property);
            }

            if (value == "initial") {
                return initialValue(property);
            }

            if (value == "unset") {
                if (isInheritedProperty(property) &&
                    element.parent != nullptr) {

                    return resolve(
                        *element.parent,
                        property
                    );
                }

                return initialValue(property);
            }

            if (value == "revert") {
                return initialValue(property);
            }

            return value;
        }

        if (isInheritedProperty(property) &&
            element.parent != nullptr) {

            return resolve(
                *element.parent,
                property
            );
        }

        return initialValue(property);
    }

    void explain(
        const Element& element,
        const string& property
    ) const {
        cout << "\n------------------------------------------------------------\n";
        cout << "Debugging " << property
             << " on " << element.description() << "\n";
        cout << "------------------------------------------------------------\n";

        const vector<Declaration> candidates =
            candidatesFor(element, property);

        if (candidates.empty()) {
            cout << "No matching declaration.\n";
            cout << "Final value: "
                 << resolve(element, property)
                 << "\n";
            return;
        }

        Declaration winner = candidates.front();

        for (size_t index = 1;
             index < candidates.size();
             ++index) {

            if (declarationWins(
                    candidates[index],
                    winner)) {

                winner = candidates[index];
            }
        }

        vector<Declaration> ordered = candidates;

        sort(
            ordered.begin(),
            ordered.end(),
            [](const Declaration& first,
               const Declaration& second) {

                if (first.important !=
                    second.important) {

                    return first.important >
                           second.important;
                }

                if (!(first.specificity ==
                      second.specificity)) {

                    return second.specificity <
                           first.specificity;
                }

                return first.sourceOrder >
                       second.sourceOrder;
            }
        );

        for (const Declaration& declaration :
             ordered) {

            const bool isWinner =
                declaration.property ==
                    winner.property &&
                declaration.selector ==
                    winner.selector &&
                declaration.sourceOrder ==
                    winner.sourceOrder;

            cout
                << (isWinner ? "[WINNER] " : "[loser ] ")
                << left
                << setw(28)
                << declaration.selector
                << " "
                << declaration.property
                << ": "
                << declaration.value
                << (declaration.important
                        ? " !important"
                        : "")
                << " specificity="
                << declaration.specificity.toString()
                << " order="
                << declaration.sourceOrder
                << "\n";
        }

        cout << "Final value: "
             << resolve(element, property)
             << "\n";
    }

    static string initialValue(
        const string& property
    ) {
        auto found =
            initialValues.find(property);

        if (found != initialValues.end()) {
            return found->second;
        }

        return "initial";
    }
};

const map<string, string>
CascadeEngine::initialValues{
    {"color", "black"},
    {"background-color", "transparent"},
    {"font-size", "medium"},
    {"font-weight", "normal"},
    {"display", "inline"},
    {"margin", "0"},
    {"padding", "0"},
    {"border", "none"},
    {"opacity", "1"}
};


// ============================================================================
// 8. Custom properties
// ============================================================================

unordered_map<string, string>
collectCustomProperties(
    const CascadeEngine& engine,
    const Element& element
) {
    unordered_map<string, string> properties;

    if (element.parent != nullptr) {
        properties =
            collectCustomProperties(
                engine,
                *element.parent
            );
    }

    /*
     * We cannot directly inspect private rules from this compact engine.
     * The case study therefore demonstrates custom-property inheritance
     * using inline custom properties and parent/child state.
     */

    for (const auto& [property, value] :
         element.inlineStyles) {

        if (startsWith(property, "--")) {
            properties[property] = value;
        }
    }

    return properties;
}

string resolveSimpleVar(
    const string& value,
    const unordered_map<string, string>& properties
) {
    const string prefix = "var(";

    const size_t start = value.find(prefix);

    if (start == string::npos) {
        return value;
    }

    const size_t close =
        value.find(')', start);

    if (close == string::npos) {
        throw runtime_error(
            "Malformed var() expression"
        );
    }

    string content =
        trim(
            value.substr(
                start + prefix.size(),
                close - start - prefix.size()
            )
        );

    const size_t comma =
        content.find(',');

    string variableName = trim(
        comma == string::npos
            ? content
            : content.substr(0, comma)
    );

    string fallback =
        comma == string::npos
            ? ""
            : trim(content.substr(comma + 1));

    auto found =
        properties.find(variableName);

    string replacement;

    if (found != properties.end()) {
        replacement = found->second;
    } else if (!fallback.empty()) {
        replacement = fallback;
    } else {
        throw runtime_error(
            "Undefined custom property: " +
            variableName
        );
    }

    return value.substr(0, start) +
           replacement +
           value.substr(close + 1);
}


// ============================================================================
// 9. Validation
// ============================================================================

void validateElement(const Element& element) {
    if (element.tag.empty()) {
        throw invalid_argument(
            "Element tag cannot be empty."
        );
    }

    for (const string& className :
         element.classes) {

        if (className.empty()) {
            throw invalid_argument(
                "Class names cannot be empty."
            );
        }
    }
}


// ============================================================================
// 10. Product-card case study
// ============================================================================

void runProductCardCaseStudy() {
    cout << "\n============================================================\n";
    cout << "CSS CASCADE PRODUCT-CARD CASE STUDY\n";
    cout << "============================================================\n";

    // ------------------------------------------------------------
    // DOM construction
    // ------------------------------------------------------------

    Element page{
        "main",
        nullopt,
        {"product-page"},
        {},
        {},
        nullptr,
        {}
    };

    Element card{
        "article",
        nullopt,
        {"product-card", "featured"},
        {{"data-state", "active"}},
        {},
        nullptr,
        {}
    };

    Element title{
        "h2",
        nullopt,
        {"product-title"},
        {},
        {},
        nullptr,
        {}
    };

    Element price{
        "span",
        nullopt,
        {"price"},
        {},
        {},
        nullptr,
        {}
    };

    addChild(page, card);
    addChild(card, title);
    addChild(card, price);

    validateElement(page);
    validateElement(card);
    validateElement(title);
    validateElement(price);

    // ------------------------------------------------------------
    // CSS rules from multiple conceptual layers of the organization.
    // ------------------------------------------------------------

    vector<Rule> rules;

    rules.push_back(
        createRule(
            ".product-page",
            {
                {"font-family", "Arial"},
                {"color", "slategray"}
            },
            1
        )
    );

    rules.push_back(
        createRule(
            ".product-card",
            {
                {"color", "black"},
                {"background-color", "white"},
                {"padding", "20px"}
            },
            2
        )
    );

    rules.push_back(
        createRule(
            ".product-card.featured",
            {
                {"background-color", "lightyellow"}
            },
            3
        )
    );

    rules.push_back(
        createRule(
            ".product-card .product-title",
            {
                {"color", "darkblue"},
                {"font-size", "1.5rem"}
            },
            4
        )
    );

    rules.push_back(
        createRule(
            "[data-state=active] .price",
            {
                {"color", "green"},
                {"font-weight", "bold"}
            },
            5
        )
    );

    rules.push_back(
        createRule(
            ".price",
            {
                {"color", "gray"}
            },
            6
        )
    );

    // Deliberate important accessibility override.
    rules.push_back(
        createRule(
            ".price",
            {
                {"color", "darkgreen !important"}
            },
            7
        )
    );

    CascadeEngine engine(rules);

    // ------------------------------------------------------------
    // Resolve the major visual properties.
    // ------------------------------------------------------------

    vector<pair<Element*, vector<string>>> inspections{
        {
            &card,
            {
                "color",
                "background-color",
                "font-family",
                "padding"
            }
        },
        {
            &title,
            {
                "color",
                "font-family",
                "font-size"
            }
        },
        {
            &price,
            {
                "color",
                "font-family",
                "font-weight"
            }
        }
    };

    for (const auto& [element, properties] :
         inspections) {

        cout << "\n" << element->description() << "\n";

        for (const string& property :
             properties) {

            cout
                << "  "
                << left
                << setw(20)
                << property
                << " -> "
                << engine.resolve(
                    *element,
                    property
                )
                << "\n";
        }
    }

    // ------------------------------------------------------------
    // Debug the most contentious property.
    // ------------------------------------------------------------

    engine.explain(
        price,
        "color"
    );

    engine.explain(
        title,
        "color"
    );

    // ------------------------------------------------------------
    // Demonstrate an inline style conflict.
    // ------------------------------------------------------------

    price.inlineStyles["color"] = "orange";

    cout << "\nAfter adding inline color: orange\n";

    engine.explain(
        price,
        "color"
    );

    // Inline normal style does not beat an important author declaration
    // in this simplified importance model.

    // ------------------------------------------------------------
    // Demonstrate explicit inheritance.
    // ------------------------------------------------------------

    cout << "\nInheritance test:\n";

    rules.push_back(
        createRule(
            ".product-page",
            {
                {"color", "teal"}
            },
            8
        )
    );

    CascadeEngine updatedEngine(rules);

    cout
        << "Title color: "
        << updatedEngine.resolve(
            title,
            "color"
        )
        << "\n";

    cout
        << "Title font-family: "
        << updatedEngine.resolve(
            title,
            "font-family"
        )
        << "\n";
}


// ============================================================================
// 11. Edge cases and failure conditions
// ============================================================================

void runEdgeCases() {
    cout << "\n============================================================\n";
    cout << "EDGE CASES\n";
    cout << "============================================================\n";

    // Case 1: No declaration.
    {
        Element element{
            "div",
            nullopt,
            {"unknown"},
            {},
            {},
            nullptr,
            {}
        };

        CascadeEngine engine({});

        cout
            << "No declaration, display -> "
            << engine.resolve(
                element,
                "display"
            )
            << "\n";
    }

    // Case 2: Inherited property.
    {
        Element parent{
            "div",
            nullopt,
            {},
            {},
            {},
            nullptr,
            {}
        };

        Element child{
            "span",
            nullopt,
            {},
            {},
            {},
            nullptr,
            {}
        };

        addChild(parent, child);

        CascadeEngine engine({
            createRule(
                "div",
                {
                    {"color", "purple"}
                },
                1
            )
        });

        cout
            << "Inherited color -> "
            << engine.resolve(
                child,
                "color"
            )
            << "\n";
    }

    // Case 3: Important beats normal.
    {
        Element element{
            "button",
            nullopt,
            {"button"},
            {},
            {},
            nullptr,
            {}
        };

        CascadeEngine engine({
            createRule(
                ".button",
                {
                    {"color", "red"}
                },
                1
            ),
            createRule(
                ".button",
                {
                    {"color", "blue !important"}
                },
                2
            )
        });

        cout
            << "Important declaration -> "
            << engine.resolve(
                element,
                "color"
            )
            << "\n";
    }

    // Case 4: Source order when specificity ties.
    {
        Element element{
            "div",
            nullopt,
            {"box"},
            {},
            {},
            nullptr,
            {}
        };

        CascadeEngine engine({
            createRule(
                ".box",
                {
                    {"color", "red"}
                },
                1
            ),
            createRule(
                ".box",
                {
                    {"color", "blue"}
                },
                2
            )
        });

        cout
            << "Source-order winner -> "
            << engine.resolve(
                element,
                "color"
            )
            << "\n";
    }
}


// ============================================================================
// 12. Complexity discussion
// ============================================================================

void printComplexityAnalysis() {
    cout << "\n============================================================\n";
    cout << "COMPLEXITY AND DESIGN ANALYSIS\n";
    cout << "============================================================\n";

    cout << R"(
The simplified resolver scans every CSS rule for each property lookup.

If:
    R = number of rules
    D = average declarations per rule
    A = ancestor depth

A simplified lookup is approximately O(R + A), ignoring the cost of
individual selector parsing and matching.

A real browser uses substantially more sophisticated data structures,
caching, invalidation strategies, selector indexes, style sharing, and
incremental recalculation.

Important engineering trade-offs:

1. Simplicity
   A direct scan is easy to understand but inefficient at large scale.

2. Caching
   Computed styles can be reused when relevant inputs have not changed.

3. Invalidation
   A class change can invalidate styles for an element and potentially
   descendants, depending on the selectors involved.

4. DOM size
   More elements can increase style and layout work.

5. Selector complexity
   Deep relationships and broad selectors can complicate style matching.

6. Maintainability
   A theoretically efficient stylesheet can still be difficult to debug
   if specificity and overrides are poorly structured.

7. Correctness
   A real browser must obey the complete CSS specifications, not this
   educational subset.
)" << "\n";
}


// ============================================================================
// 13. Production-oriented principles
// ============================================================================

void printProductionPrinciples() {
    cout << "\n============================================================\n";
    cout << "PRODUCTION PRINCIPLES\n";
    cout << "============================================================\n";

    const vector<string> principles{
        "Prefer reusable class selectors for component styling.",
        "Keep selector specificity intentionally low.",
        "Use IDs sparingly in styling architecture.",
        "Treat !important as an exceptional tool.",
        "Use cascade layers to establish explicit stylesheet architecture.",
        "Separate component, utility, and override responsibilities.",
        "Use DevTools to identify the winning declaration.",
        "Do not solve every conflict by increasing specificity.",
        "Test focus, hover, disabled, responsive, and dynamic states.",
        "Validate custom properties and their fallback behavior.",
        "Measure real rendering performance instead of relying on assumptions.",
        "Account for accessibility when overriding visual styles."
    };

    for (size_t index = 0;
         index < principles.size();
         ++index) {

        cout
            << setw(2)
            << index + 1
            << ". "
            << principles[index]
            << "\n";
    }
}


// ============================================================================
// 14. Main
// ============================================================================

int main() {
    try {
        runProductCardCaseStudy();
        runEdgeCases();
        printComplexityAnalysis();
        printProductionPrinciples();

        cout << "\n============================================================\n";
        cout << "CASE STUDY COMPLETE\n";
        cout << "============================================================\n";

    } catch (const exception& error) {
        cerr
            << "Fatal error: "
            << error.what()
            << "\n";

        return 1;
    }

    return 0;
}
