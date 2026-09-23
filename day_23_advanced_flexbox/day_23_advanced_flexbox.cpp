/*
 * Advanced Flexbox Case Study
 *
 * Scenario:
 *     A responsive operations dashboard must display a fixed navigation
 *     sidebar, a flexible main workspace, a toolbar, and a collection of
 *     responsive information cards.
 *
 * The program models the core Flexbox sizing concepts:
 *     - flex-basis
 *     - flex-grow
 *     - flex-shrink
 *     - ordering
 *     - nested flex containers
 *     - wrapping
 *     - minimum and maximum constraints
 *     - validation
 *     - responsive layout decisions
 *     - complexity and implementation trade-offs
 *
 * Compile:
 *     g++ -std=c++17 -Wall -Wextra -pedantic flexbox_case_study.cpp -o flexbox_case_study
 */

#include <algorithm>
#include <cassert>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <limits>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

using namespace std;


// ============================================================================
// 1. BASIC DATA MODEL
// ============================================================================

struct FlexItem {
    string name;
    double basis = 0.0;
    double grow = 0.0;
    double shrink = 1.0;
    int order = 0;

    optional<double> minSize;
    optional<double> maxSize;

    double finalSize = 0.0;

    void validate() const {
        if (!isfinite(basis) || basis < 0.0) {
            throw invalid_argument(
                name + ": flex-basis must be non-negative."
            );
        }

        if (!isfinite(grow) || grow < 0.0) {
            throw invalid_argument(
                name + ": flex-grow must be non-negative."
            );
        }

        if (!isfinite(shrink) || shrink < 0.0) {
            throw invalid_argument(
                name + ": flex-shrink must be non-negative."
            );
        }

        if (minSize.has_value() && *minSize < 0.0) {
            throw invalid_argument(
                name + ": minimum size cannot be negative."
            );
        }

        if (
            minSize.has_value() &&
            maxSize.has_value() &&
            *minSize > *maxSize
        ) {
            throw invalid_argument(
                name + ": minimum size exceeds maximum size."
            );
        }
    }
};


// ============================================================================
// 2. FLEX SIZING ENGINE
// ============================================================================

class FlexSizingEngine {
public:
    static double totalBasis(const vector<FlexItem>& items) {
        double total = 0.0;

        for (const auto& item : items) {
            total += item.basis;
        }

        return total;
    }

    static void distributePositiveSpace(
        double containerSize,
        vector<FlexItem>& items
    ) {
        const double basis = totalBasis(items);
        const double freeSpace = containerSize - basis;

        if (freeSpace <= 0.0) {
            for (auto& item : items) {
                item.finalSize = item.basis;
            }
            return;
        }

        double totalGrow = 0.0;

        for (const auto& item : items) {
            totalGrow += item.grow;
        }

        if (totalGrow == 0.0) {
            for (auto& item : items) {
                item.finalSize = item.basis;
            }
            return;
        }

        for (auto& item : items) {
            const double addition =
                freeSpace * (item.grow / totalGrow);

            item.finalSize = item.basis + addition;
        }
    }

    static void distributeNegativeSpace(
        double containerSize,
        vector<FlexItem>& items
    ) {
        const double basis = totalBasis(items);
        const double overflow = basis - containerSize;

        if (overflow <= 0.0) {
            for (auto& item : items) {
                item.finalSize = item.basis;
            }
            return;
        }

        /*
         * CSS Flexbox uses a scaled shrink factor:
         *
         *     flex-shrink * flex-basis
         *
         * This is important because a 400px item and a 100px item with
         * shrink=1 do not normally lose the same number of pixels.
         */
        double totalScaledShrink = 0.0;

        for (const auto& item : items) {
            totalScaledShrink += item.shrink * item.basis;
        }

        if (totalScaledShrink == 0.0) {
            for (auto& item : items) {
                item.finalSize = item.basis;
            }
            return;
        }

        for (auto& item : items) {
            const double scaledFactor =
                item.shrink * item.basis;

            const double reduction =
                overflow *
                (scaledFactor / totalScaledShrink);

            item.finalSize =
                max(0.0, item.basis - reduction);
        }
    }

    static void resolve(
        double containerSize,
        vector<FlexItem>& items
    ) {
        if (!isfinite(containerSize) || containerSize < 0.0) {
            throw invalid_argument(
                "Container size must be non-negative."
            );
        }

        for (const auto& item : items) {
            item.validate();
        }

        if (items.empty()) {
            return;
        }

        const double basis = totalBasis(items);

        if (basis < containerSize) {
            distributePositiveSpace(
                containerSize,
                items
            );
        } else if (basis > containerSize) {
            distributeNegativeSpace(
                containerSize,
                items
            );
        } else {
            for (auto& item : items) {
                item.finalSize = item.basis;
            }
        }
    }

    static void applySimpleConstraints(
        vector<FlexItem>& items
    ) {
        /*
         * A browser uses a more sophisticated iterative freezing algorithm.
         * This method intentionally shows only the visible effect of
         * min/max constraints.
         */
        for (auto& item : items) {
            if (item.minSize.has_value()) {
                item.finalSize =
                    max(item.finalSize, *item.minSize);
            }

            if (item.maxSize.has_value()) {
                item.finalSize =
                    min(item.finalSize, *item.maxSize);
            }
        }
    }
};


// ============================================================================
// 3. OUTPUT UTILITIES
// ============================================================================

void printItems(const vector<FlexItem>& items) {
    cout << left
         << setw(18) << "Item"
         << setw(12) << "Basis"
         << setw(10) << "Grow"
         << setw(10) << "Shrink"
         << setw(12) << "Order"
         << setw(14) << "Final"
         << '\n';

    cout << string(76, '-') << '\n';

    for (const auto& item : items) {
        cout << left
             << setw(18) << item.name
             << setw(12) << fixed << setprecision(2) << item.basis
             << setw(10) << item.grow
             << setw(10) << item.shrink
             << setw(12) << item.order
             << setw(14) << item.finalSize
             << '\n';
    }
}


void printSection(const string& title) {
    cout << '\n'
         << string(78, '=')
         << '\n'
         << title
         << '\n'
         << string(78, '=')
         << '\n';
}


// ============================================================================
// 4. ORDERING MODEL
// ============================================================================

void demonstrateOrdering() {
    printSection("ORDERING");

    vector<FlexItem> items = {
        {"Header", 150, 0, 1, 0},
        {"Navigation", 220, 0, 1, 2},
        {"Main", 600, 1, 1, 1},
        {"Footer", 150, 0, 1, 3},
        {"Alert", 100, 0, 1, -1}
    };

    cout << "Source order:\n";

    for (const auto& item : items) {
        cout << "  " << item.name
             << " (order=" << item.order << ")\n";
    }

    sort(
        items.begin(),
        items.end(),
        [](const FlexItem& leftItem, const FlexItem& rightItem) {
            return leftItem.order < rightItem.order;
        }
    );

    cout << "\nVisual order according to order values:\n";

    for (const auto& item : items) {
        cout << "  " << item.name << '\n';
    }

    cout
        << "\nDesign constraint: visual ordering should not be used as a "
        << "substitute for meaningful semantic source order.\n";
}


// ============================================================================
// 5. FLEX-GROW CASE
// ============================================================================

void demonstrateGrowth() {
    printSection("FLEX-GROW CASE");

    vector<FlexItem> items = {
        {"Analytics", 200, 1, 1, 0},
        {"Research", 200, 3, 1, 0}
    };

    cout << "Container width: 1000px\n";
    cout << "Total basis: 400px\n";
    cout << "Free space: 600px\n";
    cout << "Grow ratio: 1:3\n\n";

    FlexSizingEngine::resolve(1000, items);

    printItems(items);
}


// ============================================================================
// 6. FLEX-SHRINK CASE
// ============================================================================

void demonstrateShrink() {
    printSection("FLEX-SHRINK CASE");

    vector<FlexItem> items = {
        {"Large panel", 400, 0, 1, 0},
        {"Small panel", 300, 0, 1, 0}
    };

    cout << "Container width: 500px\n";
    cout << "Total basis: 700px\n";
    cout << "Overflow: 200px\n";
    cout << "Scaled shrink factors: 400 and 300\n\n";

    FlexSizingEngine::resolve(500, items);

    printItems(items);
}


// ============================================================================
// 7. FLEX-BASIS CASE
// ============================================================================

void demonstrateBasis() {
    printSection("FLEX-BASIS CASE");

    vector<FlexItem> items = {
        {"Zero basis A", 0, 1, 1, 0},
        {"Zero basis B", 0, 1, 1, 0},
        {"Zero basis C", 0, 1, 1, 0}
    };

    FlexSizingEngine::resolve(900, items);

    cout
        << "A zero-basis, grow-enabled group distributes the available "
        << "space according to grow factors.\n\n";

    printItems(items);

    cout
        << "\nA basis of zero should not be confused with zero final size. "
        << "Growth can produce a substantial final size.\n";
}


// ============================================================================
// 8. SIDEBAR + MAIN DASHBOARD
// ============================================================================

struct Dashboard {
    double viewportWidth;
    vector<FlexItem> regions;

    explicit Dashboard(double width)
        : viewportWidth(width),
          regions{
              {"Sidebar", 260, 0, 0, 0},
              {"Main workspace", 700, 1, 1, 0}
          } {}

    void calculate() {
        FlexSizingEngine::resolve(
            viewportWidth,
            regions
        );
    }

    void print() const {
        cout
            << "\nDashboard viewport: "
            << viewportWidth
            << "px\n";

        printItems(regions);

        if (viewportWidth < 760) {
            cout
                << "\nResponsive decision: this width is small enough "
                << "that a production dashboard might switch from a "
                << "sidebar row to a stacked or collapsed navigation model.\n";
        }
    }
};


void demonstrateDashboard() {
    printSection("INDUSTRY-STYLE DASHBOARD");

    for (double width : {1440.0, 1200.0, 900.0, 700.0, 520.0}) {
        Dashboard dashboard(width);
        dashboard.calculate();
        dashboard.print();
    }
}


// ============================================================================
// 9. NESTED LAYOUT TREE
// ============================================================================

class LayoutNode {
private:
    string name;
    string direction;
    vector<LayoutNode> children;

public:
    LayoutNode(
        string nodeName,
        string flexDirection
    )
        : name(move(nodeName)),
          direction(move(flexDirection)) {}

    void addChild(LayoutNode child) {
        children.push_back(move(child));
    }

    void print(int depth = 0) const {
        cout
            << string(depth * 2, ' ')
            << "- "
            << name
            << " [flex-direction="
            << direction
            << "]\n";

        for (const auto& child : children) {
            child.print(depth + 1);
        }
    }
};


void demonstrateNestedLayout() {
    printSection("NESTED FLEX LAYOUT");

    LayoutNode page("Page", "column");

    LayoutNode header("Header", "row");
    LayoutNode content("Content area", "row");
    LayoutNode sidebar("Sidebar", "column");
    LayoutNode main("Main workspace", "column");
    LayoutNode toolbar("Toolbar", "row");
    LayoutNode cards("Card collection", "row");
    LayoutNode footer("Footer", "row");

    main.addChild(move(toolbar));
    main.addChild(move(cards));

    content.addChild(move(sidebar));
    content.addChild(move(main));

    page.addChild(move(header));
    page.addChild(move(content));
    page.addChild(move(footer));

    page.print();
}


// ============================================================================
// 10. FLEX-WRAP LINE FORMATION
// ============================================================================

vector<vector<FlexItem>> createWrappedLines(
    double containerSize,
    const vector<FlexItem>& items
) {
    vector<vector<FlexItem>> lines;
    vector<FlexItem> currentLine;
    double currentBasis = 0.0;

    for (const auto& item : items) {
        if (item.basis > containerSize) {
            if (!currentLine.empty()) {
                lines.push_back(currentLine);
                currentLine.clear();
                currentBasis = 0.0;
            }

            lines.push_back({item});
            continue;
        }

        if (
            !currentLine.empty() &&
            currentBasis + item.basis > containerSize
        ) {
            lines.push_back(currentLine);
            currentLine.clear();
            currentBasis = 0.0;
        }

        currentLine.push_back(item);
        currentBasis += item.basis;
    }

    if (!currentLine.empty()) {
        lines.push_back(currentLine);
    }

    return lines;
}


void demonstrateWrapping() {
    printSection("FLEX-WRAP");

    vector<FlexItem> cards;

    for (int i = 1; i <= 7; ++i) {
        cards.push_back({
            "Card " + to_string(i),
            250,
            1,
            1,
            0
        });
    }

    const double containerWidth = 900;

    const auto lines =
        createWrappedLines(
            containerWidth,
            cards
        );

    for (size_t i = 0; i < lines.size(); ++i) {
        cout << "Line " << i + 1 << ": ";

        for (size_t j = 0; j < lines[i].size(); ++j) {
            if (j > 0) {
                cout << ", ";
            }

            cout << lines[i][j].name;
        }

        cout << '\n';
    }
}


// ============================================================================
// 11. NAVBAR MODEL
// ============================================================================

void demonstrateNavbar() {
    printSection("NAVIGATION BAR");

    vector<FlexItem> navbar = {
        {"Brand", 160, 0, 0, 0},
        {"Links", 300, 1, 1, 0},
        {"Actions", 180, 0, 0, 0}
    };

    FlexSizingEngine::resolve(
        1000,
        navbar
    );

    printItems(navbar);

    cout
        << "\nThe middle links region is flexible while the brand and "
        << "actions retain stable bases.\n";
}


// ============================================================================
// 12. CONSTRAINT CASE
// ============================================================================

void demonstrateConstraints() {
    printSection("MINIMUM AND MAXIMUM CONSTRAINTS");

    vector<FlexItem> items = {
        {
            "Sidebar",
            200,
            1,
            1,
            0,
            180.0,
            320.0
        },
        {
            "Main",
            200,
            3,
            1,
            0,
            300.0,
            nullopt
        }
    };

    FlexSizingEngine::resolve(
        1000,
        items
    );

    FlexSizingEngine::applySimpleConstraints(
        items
    );

    printItems(items);

    cout
        << "\nProduction note: the real Flexbox algorithm can freeze "
        << "items that hit constraints and redistribute remaining free space.\n";
}


// ============================================================================
// 13. FAILURE CONDITIONS
// ============================================================================

void demonstrateFailures() {
    printSection("VALIDATION AND FAILURE CONDITIONS");

    vector<FlexItem> invalidItems = {
        {"Negative basis", -20, 1, 1, 0},
        {"Negative grow", 100, -1, 1, 0},
        {"Negative shrink", 100, 1, -1, 0},
        {
            "Invalid limits",
            100,
            1,
            1,
            0,
            300.0,
            200.0
        }
    };

    for (const auto& item : invalidItems) {
        try {
            item.validate();
            cout
                << item.name
                << ": unexpectedly accepted.\n";
        } catch (const invalid_argument& error) {
            cout
                << item.name
                << ": "
                << error.what()
                << '\n';
        }
    }
}


// ============================================================================
// 14. PERFORMANCE MODEL
// ============================================================================

void demonstrateComplexity() {
    printSection("COMPLEXITY AND PERFORMANCE");

    cout
        << "Basic one-line grow/shrink calculations scan n items: O(n).\n"
        << "Sorting items by order requires O(n log n) in a typical comparison sort.\n"
        << "Wrapping with a sequential packing pass is O(n).\n"
        << "A complete browser layout engine is more complex because layout may\n"
        << "depend on intrinsic content sizes, constraints, nested descendants,\n"
        << "line formation, and repeated measurement or resolution steps.\n";
}


// ============================================================================
// 15. TESTS
// ============================================================================

void assertNear(
    double actual,
    double expected,
    double tolerance = 1e-9
) {
    if (abs(actual - expected) > tolerance) {
        ostringstream message;

        message
            << "Expected "
            << expected
            << ", received "
            << actual;

        throw runtime_error(
            message.str()
        );
    }
}


void testGrow() {
    vector<FlexItem> items = {
        {"A", 200, 1, 1, 0},
        {"B", 200, 3, 1, 0}
    };

    FlexSizingEngine::resolve(
        1000,
        items
    );

    assertNear(
        items[0].finalSize,
        350.0
    );

    assertNear(
        items[1].finalSize,
        650.0
    );
}


void testShrink() {
    vector<FlexItem> items = {
        {"A", 400, 0, 1, 0},
        {"B", 300, 0, 1, 0}
    };

    FlexSizingEngine::resolve(
        500,
        items
    );

    assertNear(
        items[0].finalSize,
        500.0 - (200.0 * 400.0 / 700.0)
    );

    assertNear(
        items[1].finalSize,
        500.0 - (200.0 * 300.0 / 700.0)
    );
}


void testNoGrowth() {
    vector<FlexItem> items = {
        {"A", 100, 0, 1, 0},
        {"B", 100, 0, 1, 0}
    };

    FlexSizingEngine::resolve(
        500,
        items
    );

    assertNear(
        items[0].finalSize,
        100.0
    );

    assertNear(
        items[1].finalSize,
        100.0
    );
}


void testWrapping() {
    vector<FlexItem> items = {
        {"A", 300, 0, 1, 0},
        {"B", 300, 0, 1, 0},
        {"C", 300, 0, 1, 0},
        {"D", 300, 0, 1, 0}
    };

    auto lines =
        createWrappedLines(
            900,
            items
        );

    if (lines.size() != 2) {
        throw runtime_error(
            "Wrapping test expected two lines."
        );
    }

    if (
        lines[0].size() != 3 ||
        lines[1].size() != 1
    ) {
        throw runtime_error(
            "Unexpected line distribution."
        );
    }
}


void runTests() {
    printSection("TESTS");

    struct TestCase {
        string name;
        void (*function)();
    };

    vector<TestCase> tests = {
        {"flex-grow distribution", testGrow},
        {"flex-shrink distribution", testShrink},
        {"zero-grow behavior", testNoGrowth},
        {"flex-wrap line formation", testWrapping}
    };

    int passed = 0;

    for (const auto& test : tests) {
        try {
            test.function();

            cout
                << "PASS: "
                << test.name
                << '\n';

            ++passed;
        } catch (const exception& error) {
            cout
                << "FAIL: "
                << test.name
                << " -> "
                << error.what()
                << '\n';
        }
    }

    cout
        << passed
        << "/"
        << tests.size()
        << " tests passed.\n";
}


// ============================================================================
// 16. MAIN
// ============================================================================

int main() {
    cout
        << string(78, '=')
        << '\n'
        << "ADVANCED FLEXBOX C++ CASE STUDY"
        << '\n'
        << string(78, '=')
        << '\n';

    try {
        demonstrateGrowth();
        demonstrateShrink();
        demonstrateBasis();
        demonstrateOrdering();
        demonstrateNestedLayout();
        demonstrateWrapping();
        demonstrateNavbar();
        demonstrateConstraints();
        demonstrateDashboard();
        demonstrateFailures();
        demonstrateComplexity();
        runTests();
    } catch (const exception& error) {
        cerr
            << "Fatal error: "
            << error.what()
            << '\n';

        return 1;
    }

    cout
        << "\nProgram completed successfully.\n";

    return 0;
}
