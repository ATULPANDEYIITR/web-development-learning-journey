/*
 * Flexbox Fundamentals: C++ Case Study
 *
 * Case study:
 * A responsive dashboard layout engine for a terminal-based application.
 *
 * The program models core Flexbox ideas without depending on a browser:
 *   - flex direction
 *   - flex wrapping
 *   - flex-basis
 *   - flex-grow
 *   - flex-shrink
 *   - gaps
 *   - main-axis distribution
 *   - cross-axis alignment
 *   - order
 *   - minimum and maximum sizes
 *   - responsive line formation
 *   - validation
 *   - complexity analysis
 *
 * This is an educational approximation, not a browser-compatible CSS
 * implementation. Browser engines implement many additional rules for
 * intrinsic sizing, percentages, margins, min/max constraints, text,
 * aspect ratios, writing modes, and layout rounding.
 *
 * Compile:
 *   g++ -std=c++17 -Wall -Wextra -pedantic flexbox_case_study.cpp -o flexbox
 */

#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <numeric>
#include <optional>
#include <stdexcept>
#include <string>
#include <vector>

enum class FlexDirection {
    Row,
    RowReverse,
    Column,
    ColumnReverse
};

enum class FlexWrap {
    NoWrap,
    Wrap,
    WrapReverse
};

enum class JustifyContent {
    FlexStart,
    FlexEnd,
    Center,
    SpaceBetween,
    SpaceAround,
    SpaceEvenly
};

enum class AlignItems {
    Stretch,
    FlexStart,
    FlexEnd,
    Center,
    Baseline
};

std::string toString(FlexDirection direction) {
    switch (direction) {
        case FlexDirection::Row:
            return "row";
        case FlexDirection::RowReverse:
            return "row-reverse";
        case FlexDirection::Column:
            return "column";
        case FlexDirection::ColumnReverse:
            return "column-reverse";
    }

    return "unknown";
}

std::string toString(FlexWrap wrap) {
    switch (wrap) {
        case FlexWrap::NoWrap:
            return "nowrap";
        case FlexWrap::Wrap:
            return "wrap";
        case FlexWrap::WrapReverse:
            return "wrap-reverse";
    }

    return "unknown";
}

std::string toString(JustifyContent value) {
    switch (value) {
        case JustifyContent::FlexStart:
            return "flex-start";
        case JustifyContent::FlexEnd:
            return "flex-end";
        case JustifyContent::Center:
            return "center";
        case JustifyContent::SpaceBetween:
            return "space-between";
        case JustifyContent::SpaceAround:
            return "space-around";
        case JustifyContent::SpaceEvenly:
            return "space-evenly";
    }

    return "unknown";
}

std::string toString(AlignItems value) {
    switch (value) {
        case AlignItems::Stretch:
            return "stretch";
        case AlignItems::FlexStart:
            return "flex-start";
        case AlignItems::FlexEnd:
            return "flex-end";
        case AlignItems::Center:
            return "center";
        case AlignItems::Baseline:
            return "baseline";
    }

    return "unknown";
}


// ---------------------------------------------------------------------------
// FLEX ITEM
// ---------------------------------------------------------------------------

struct FlexItem {
    std::string name;

    // flex-basis is the starting main-axis size in this simplified model.
    double basis = 0.0;

    // Positive free space is distributed using flex-grow.
    double grow = 0.0;

    // Negative free space is distributed using flex-shrink multiplied
    // by the flex base size.
    double shrink = 1.0;

    // Lower order values appear earlier in visual ordering.
    int order = 0;

    std::optional<double> minSize;
    std::optional<double> maxSize;

    double resolvedSize = 0.0;

    FlexItem(
        std::string itemName,
        double itemBasis,
        double itemGrow = 0.0,
        double itemShrink = 1.0,
        int itemOrder = 0
    )
        : name(std::move(itemName)),
          basis(itemBasis),
          grow(itemGrow),
          shrink(itemShrink),
          order(itemOrder),
          resolvedSize(itemBasis) {

        validate();
    }

    void validate() const {
        if (basis < 0.0) {
            throw std::invalid_argument(
                "Flex basis cannot be negative."
            );
        }

        if (grow < 0.0 || shrink < 0.0) {
            throw std::invalid_argument(
                "Flex grow and shrink factors cannot be negative."
            );
        }

        if (
            minSize.has_value() &&
            minSize.value() < 0.0
        ) {
            throw std::invalid_argument(
                "Minimum size cannot be negative."
            );
        }

        if (
            maxSize.has_value() &&
            maxSize.value() < 0.0
        ) {
            throw std::invalid_argument(
                "Maximum size cannot be negative."
            );
        }

        if (
            minSize.has_value() &&
            maxSize.has_value() &&
            minSize.value() > maxSize.value()
        ) {
            throw std::invalid_argument(
                "Minimum size cannot exceed maximum size."
            );
        }
    }
};


// ---------------------------------------------------------------------------
// FLEX LINE
// ---------------------------------------------------------------------------

struct FlexLine {
    std::vector<FlexItem*> items;
    double usedMainSize = 0.0;
};


// ---------------------------------------------------------------------------
// FLEX CONTAINER
// ---------------------------------------------------------------------------

class FlexContainer {
private:
    double mainSize_;
    double crossSize_;

    FlexDirection direction_;
    FlexWrap wrap_;
    JustifyContent justifyContent_;
    AlignItems alignItems_;

    double gap_;

    std::vector<FlexItem> items_;

public:
    FlexContainer(
        double mainSize,
        double crossSize,
        FlexDirection direction,
        FlexWrap wrap,
        JustifyContent justifyContent,
        AlignItems alignItems,
        double gap
    )
        : mainSize_(mainSize),
          crossSize_(crossSize),
          direction_(direction),
          wrap_(wrap),
          justifyContent_(justifyContent),
          alignItems_(alignItems),
          gap_(gap) {

        if (mainSize < 0.0 || crossSize < 0.0) {
            throw std::invalid_argument(
                "Container dimensions cannot be negative."
            );
        }

        if (gap < 0.0) {
            throw std::invalid_argument(
                "Gap cannot be negative."
            );
        }
    }

    void addItem(const FlexItem& item) {
        items_.push_back(item);
    }

    std::vector<FlexItem>& items() {
        return items_;
    }

    const std::vector<FlexItem>& items() const {
        return items_;
    }

    double mainSize() const {
        return mainSize_;
    }

    double crossSize() const {
        return crossSize_;
    }

    double gap() const {
        return gap_;
    }

    FlexWrap wrap() const {
        return wrap_;
    }

    JustifyContent justifyContent() const {
        return justifyContent_;
    }

    AlignItems alignItems() const {
        return alignItems_;
    }

    // -----------------------------------------------------------------------
    // LINE FORMATION
    // -----------------------------------------------------------------------

    std::vector<FlexLine> createLines() {
        std::vector<FlexItem*> orderedItems;

        for (auto& item : items_) {
            orderedItems.push_back(&item);
        }

        std::stable_sort(
            orderedItems.begin(),
            orderedItems.end(),
            [](const FlexItem* left, const FlexItem* right) {
                return left->order < right->order;
            }
        );

        std::vector<FlexLine> lines;
        FlexLine current;

        for (FlexItem* item : orderedItems) {
            const double extraGap =
                current.items.empty() ? 0.0 : gap_;

            const double required =
                item->basis + extraGap;

            const bool wouldOverflow =
                !current.items.empty() &&
                current.usedMainSize + required > mainSize_;

            if (
                wrap_ != FlexWrap::NoWrap &&
                wouldOverflow
            ) {
                lines.push_back(current);
                current = FlexLine{};
            }

            const double gapBefore =
                current.items.empty() ? 0.0 : gap_;

            current.items.push_back(item);
            current.usedMainSize += gapBefore + item->basis;
        }

        if (!current.items.empty()) {
            lines.push_back(current);
        }

        return lines;
    }

    // -----------------------------------------------------------------------
    // FLEX GROW / SHRINK
    // -----------------------------------------------------------------------

    void resolveLine(FlexLine& line) {
        if (line.items.empty()) {
            return;
        }

        const double totalBasis =
            std::accumulate(
                line.items.begin(),
                line.items.end(),
                0.0,
                [](double sum, const FlexItem* item) {
                    return sum + item->basis;
                }
            );

        const double totalGap =
            gap_ * static_cast<double>(
                line.items.size() > 0
                    ? line.items.size() - 1
                    : 0
            );

        const double freeSpace =
            mainSize_ - totalBasis - totalGap;

        // Positive free space is distributed by flex-grow.
        if (freeSpace > 0.0) {
            const double totalGrow =
                std::accumulate(
                    line.items.begin(),
                    line.items.end(),
                    0.0,
                    [](double sum, const FlexItem* item) {
                        return sum + item->grow;
                    }
                );

            for (FlexItem* item : line.items) {
                double size = item->basis;

                if (totalGrow > 0.0) {
                    size +=
                        freeSpace *
                        item->grow /
                        totalGrow;
                }

                item->resolvedSize =
                    clampToConstraints(*item, size);
            }

            return;
        }

        // Negative free space requires shrinking.
        if (freeSpace < 0.0) {
            const double deficit = -freeSpace;

            double totalScaledShrink = 0.0;

            for (const FlexItem* item : line.items) {
                totalScaledShrink +=
                    item->shrink * item->basis;
            }

            for (FlexItem* item : line.items) {
                double size = item->basis;

                if (totalScaledShrink > 0.0) {
                    const double scaledFactor =
                        item->shrink * item->basis;

                    size -=
                        deficit *
                        scaledFactor /
                        totalScaledShrink;
                }

                item->resolvedSize =
                    clampToConstraints(*item, size);
            }

            return;
        }

        // No free space and no deficit.
        for (FlexItem* item : line.items) {
            item->resolvedSize = item->basis;
        }
    }

    static double clampToConstraints(
        const FlexItem& item,
        double size
    ) {
        if (item.minSize.has_value()) {
            size = std::max(
                size,
                item.minSize.value()
            );
        }

        if (item.maxSize.has_value()) {
            size = std::min(
                size,
                item.maxSize.value()
            );
        }

        return std::max(0.0, size);
    }

    // -----------------------------------------------------------------------
    // MAIN-AXIS POSITIONING
    // -----------------------------------------------------------------------

    std::vector<double> calculateMainAxisPositions(
        const FlexLine& line
    ) const {
        std::vector<double> positions;

        if (line.items.empty()) {
            return positions;
        }

        double occupied = 0.0;

        for (const FlexItem* item : line.items) {
            occupied += item->resolvedSize;
        }

        const double naturalGap =
            gap_ *
            static_cast<double>(
                line.items.size() > 0
                    ? line.items.size() - 1
                    : 0
            );

        occupied += naturalGap;

        const double freeSpace =
            std::max(0.0, mainSize_ - occupied);

        double leading = 0.0;
        double between = gap_;

        switch (justifyContent_) {
            case JustifyContent::FlexStart:
                leading = 0.0;
                between = gap_;
                break;

            case JustifyContent::FlexEnd:
                leading = freeSpace;
                between = gap_;
                break;

            case JustifyContent::Center:
                leading = freeSpace / 2.0;
                between = gap_;
                break;

            case JustifyContent::SpaceBetween:
                leading = 0.0;

                if (line.items.size() > 1) {
                    between =
                        gap_ +
                        freeSpace /
                        static_cast<double>(
                            line.items.size() - 1
                        );
                } else {
                    between = 0.0;
                }

                break;

            case JustifyContent::SpaceAround:
                between =
                    gap_ +
                    freeSpace /
                    static_cast<double>(
                        line.items.size()
                    );

                leading = between / 2.0;
                break;

            case JustifyContent::SpaceEvenly:
                between =
                    gap_ +
                    freeSpace /
                    static_cast<double>(
                        line.items.size() + 1
                    );

                leading = between;
                break;
        }

        double cursor = leading;

        for (const FlexItem* item : line.items) {
            positions.push_back(cursor);
            cursor += item->resolvedSize + between;
        }

        return positions;
    }

    // -----------------------------------------------------------------------
    // CROSS-AXIS ALIGNMENT
    // -----------------------------------------------------------------------

    double crossAxisOffset(
        double itemCrossSize
    ) const {
        if (itemCrossSize < 0.0) {
            throw std::invalid_argument(
                "Cross-axis item size cannot be negative."
            );
        }

        switch (alignItems_) {
            case AlignItems::FlexStart:
                return 0.0;

            case AlignItems::FlexEnd:
                return std::max(
                    0.0,
                    crossSize_ - itemCrossSize
                );

            case AlignItems::Center:
                return std::max(
                    0.0,
                    (crossSize_ - itemCrossSize) / 2.0
                );

            case AlignItems::Stretch:
                // A real browser stretches an auto-sized item along the
                // cross axis. The offset itself remains at the start.
                return 0.0;

            case AlignItems::Baseline:
                // Baseline alignment requires font metrics. This model
                // uses a zero geometric offset as an approximation.
                return 0.0;
        }

        return 0.0;
    }

    // -----------------------------------------------------------------------
    // REPORTING
    // -----------------------------------------------------------------------

    void printLayout() {
        std::cout << "\n=== DASHBOARD FLEX LAYOUT ===\n";
        std::cout << "Main size       : "
                  << mainSize_ << "px\n";
        std::cout << "Cross size      : "
                  << crossSize_ << "px\n";
        std::cout << "Direction       : "
                  << toString(direction_) << '\n';
        std::cout << "Wrap            : "
                  << toString(wrap_) << '\n';
        std::cout << "Justify content : "
                  << toString(justifyContent_) << '\n';
        std::cout << "Align items     : "
                  << toString(alignItems_) << '\n';
        std::cout << "Gap             : "
                  << gap_ << "px\n";

        auto lines = createLines();

        std::cout << "Flex lines      : "
                  << lines.size() << "\n";

        for (std::size_t lineIndex = 0;
             lineIndex < lines.size();
             ++lineIndex) {

            auto& line = lines[lineIndex];

            resolveLine(line);

            auto positions =
                calculateMainAxisPositions(line);

            std::cout
                << "\nLine "
                << lineIndex + 1
                << ":\n";

            for (std::size_t index = 0;
                 index < line.items.size();
                 ++index) {

                FlexItem* item = line.items[index];

                std::cout
                    << "  "
                    << std::left
                    << std::setw(15)
                    << item->name
                    << " position="
                    << std::setw(8)
                    << std::fixed
                    << std::setprecision(2)
                    << positions[index]
                    << " size="
                    << std::setw(8)
                    << item->resolvedSize
                    << " grow="
                    << item->grow
                    << " shrink="
                    << item->shrink
                    << '\n';
            }
        }
    }
};


// ---------------------------------------------------------------------------
// VALIDATION
// ---------------------------------------------------------------------------

void validateDashboard(
    const FlexContainer& container
) {
    std::cout << "\n=== CONFIGURATION VALIDATION ===\n";

    const auto& items = container.items();

    double totalBasis = 0.0;

    for (const auto& item : items) {
        totalBasis += item.basis;
    }

    const double totalGaps =
        container.gap() *
        static_cast<double>(
            items.size() > 0 ? items.size() - 1 : 0
        );

    if (
        container.wrap() == FlexWrap::NoWrap &&
        totalBasis + totalGaps > container.mainSize()
    ) {
        std::cout
            << "Warning: items exceed the available main-axis "
               "space while wrapping is disabled.\n";
    } else {
        std::cout
            << "Main-axis capacity check passed for the "
               "configured wrapping mode.\n";
    }

    bool customOrder = false;

    for (const auto& item : items) {
        if (item.order != 0) {
            customOrder = true;
        }
    }

    if (customOrder) {
        std::cout
            << "Warning: custom order changes visual order. "
               "Keep semantic source order meaningful.\n";
    }

    std::cout
        << "Validation completed.\n";
}


// ---------------------------------------------------------------------------
// RESPONSIVE SCENARIO
// ---------------------------------------------------------------------------

void runResponsiveScenario() {
    std::cout << "\n=== RESPONSIVE SCENARIO ===\n";

    const std::vector<double> viewportWidths = {
        1200.0,
        850.0,
        600.0,
        420.0
    };

    for (double width : viewportWidths) {
        /*
         * The dashboard behaves conceptually like:
         *
         *   display: flex;
         *   flex-wrap: wrap;
         *   gap: 20px;
         *
         * The item basis values represent minimum practical card widths.
         */
        FlexContainer dashboard(
            width,
            600.0,
            FlexDirection::Row,
            FlexWrap::Wrap,
            JustifyContent::SpaceBetween,
            AlignItems::Stretch,
            20.0
        );

        FlexItem analytics("Analytics", 240.0, 1.0, 1.0);
        FlexItem activity("Activity", 240.0, 1.0, 1.0);
        FlexItem alerts("Alerts", 240.0, 1.0, 1.0);
        FlexItem security("Security", 240.0, 1.0, 1.0);
        FlexItem storage("Storage", 240.0, 1.0, 1.0);

        analytics.minSize = 180.0;
        activity.minSize = 180.0;
        alerts.minSize = 180.0;
        security.minSize = 180.0;
        storage.minSize = 180.0;

        dashboard.addItem(analytics);
        dashboard.addItem(activity);
        dashboard.addItem(alerts);
        dashboard.addItem(security);
        dashboard.addItem(storage);

        std::cout
            << "\nViewport width: "
            << width
            << "px\n";

        auto lines = dashboard.createLines();

        std::cout
            << "Required flex lines: "
            << lines.size()
            << '\n';

        for (std::size_t index = 0;
             index < lines.size();
             ++index) {

            std::cout << "  Line "
                      << index + 1
                      << ": ";

            for (std::size_t itemIndex = 0;
                 itemIndex < lines[index].items.size();
                 ++itemIndex) {

                if (itemIndex > 0) {
                    std::cout << ", ";
                }

                std::cout
                    << lines[index]
                           .items[itemIndex]
                           ->name;
            }

            std::cout << '\n';
        }
    }
}


// ---------------------------------------------------------------------------
// EDGE CASES
// ---------------------------------------------------------------------------

void demonstrateEdgeCases() {
    std::cout << "\n=== EDGE CASES ===\n";

    {
        FlexContainer container(
            500.0,
            300.0,
            FlexDirection::Row,
            FlexWrap::NoWrap,
            JustifyContent::FlexStart,
            AlignItems::Stretch,
            0.0
        );

        container.addItem(
            FlexItem("Zero grow", 200.0, 0.0, 1.0)
        );

        container.addItem(
            FlexItem("Growing", 100.0, 1.0, 1.0)
        );

        auto lines = container.createLines();

        for (auto& line : lines) {
            container.resolveLine(line);
        }

        std::cout
            << "Positive free space with one growing item: "
               "only that item receives growth.\n";
    }

    {
        FlexContainer container(
            300.0,
            300.0,
            FlexDirection::Row,
            FlexWrap::NoWrap,
            JustifyContent::FlexStart,
            AlignItems::Stretch,
            10.0
        );

        FlexItem large("Large", 500.0, 0.0, 0.0);

        container.addItem(large);

        auto lines = container.createLines();

        for (auto& line : lines) {
            container.resolveLine(line);
        }

        std::cout
            << "Zero shrink factor: item does not participate "
               "in shrink distribution.\n";
    }

    {
        FlexContainer container(
            700.0,
            300.0,
            FlexDirection::Row,
            FlexWrap::NoWrap,
            JustifyContent::Center,
            AlignItems::Center,
            20.0
        );

        FlexItem constrained(
            "Constrained",
            200.0,
            1.0,
            1.0
        );

        constrained.maxSize = 250.0;

        container.addItem(constrained);

        auto lines = container.createLines();

        for (auto& line : lines) {
            container.resolveLine(line);
        }

        std::cout
            << "Maximum constraint: growth is capped by max-size.\n";
    }
}


// ---------------------------------------------------------------------------
// COMPLEXITY DISCUSSION
// ---------------------------------------------------------------------------

void printComplexityAnalysis() {
    std::cout << "\n=== COMPLEXITY CONSIDERATIONS ===\n";

    std::cout
        << "Line formation: O(n) after ordering.\n";

    std::cout
        << "Visual ordering: O(n log n) because the implementation "
           "uses stable_sort.\n";

    std::cout
        << "Free-space distribution: O(n) per flex line.\n";

    std::cout
        << "Position calculation: O(n) per flex line.\n";

    std::cout
        << "Memory usage: O(n) for item and line storage.\n";

    std::cout
        << "Real browser engines perform substantially more work because "
           "CSS layout includes intrinsic sizing, style resolution, "
           "layout dependencies, fragmentation, text measurement, "
           "painting interactions, and many specification details.\n";
}


// ---------------------------------------------------------------------------
// ARCHITECTURAL LESSONS
// ---------------------------------------------------------------------------

void printArchitecturalLessons() {
    std::cout << "\n=== DESIGN DECISIONS ===\n";

    const std::vector<std::string> lessons = {
        "Separate FlexItem data from FlexContainer layout behavior.",
        "Validate sizes and factors at object boundaries.",
        "Keep line formation separate from free-space resolution.",
        "Keep main-axis distribution separate from cross-axis alignment.",
        "Use enums instead of unrestricted strings for layout modes.",
        "Represent optional constraints explicitly.",
        "Use stable ordering so equal order values preserve source order.",
        "Treat the implementation as a simplified educational model rather "
        "than a complete browser layout engine.",
        "Prefer semantic source order even when visual order is customized."
    };

    for (const auto& lesson : lessons) {
        std::cout << "  - " << lesson << '\n';
    }
}


// ---------------------------------------------------------------------------
// MAIN
// ---------------------------------------------------------------------------

int main() {
    try {
        std::cout
            << "FLEXBOX FUNDAMENTALS - C++ CASE STUDY\n"
               "======================================\n";

        /*
         * Industry-style scenario:
         *
         * A dashboard contains several independent cards. Their sizes must
         * adapt to the available viewport. The layout uses a row-oriented
         * flex container, wrapping, gaps, flexible growth, and constraints.
         */
        FlexContainer dashboard(
            1000.0,
            650.0,
            FlexDirection::Row,
            FlexWrap::Wrap,
            JustifyContent::SpaceBetween,
            AlignItems::Center,
            24.0
        );

        FlexItem navigation(
            "Navigation",
            180.0,
            0.0,
            1.0,
            0
        );

        FlexItem analytics(
            "Analytics",
            300.0,
            1.0,
            1.0,
            0
        );

        FlexItem activity(
            "Activity",
            260.0,
            1.0,
            1.0,
            0
        );

        FlexItem security(
            "Security",
            220.0,
            1.0,
            1.0,
            0
        );

        FlexItem actions(
            "Actions",
            160.0,
            0.0,
            1.0,
            0
        );

        analytics.minSize = 220.0;
        analytics.maxSize = 520.0;

        activity.minSize = 200.0;
        security.minSize = 180.0;

        dashboard.addItem(navigation);
        dashboard.addItem(analytics);
        dashboard.addItem(activity);
        dashboard.addItem(security);
        dashboard.addItem(actions);

        validateDashboard(dashboard);
        dashboard.printLayout();

        runResponsiveScenario();
        demonstrateEdgeCases();
        printComplexityAnalysis();
        printArchitecturalLessons();

        std::cout
            << "\n=== CASE STUDY COMPLETE ===\n"
               "The program modeled Flexbox as a collection of layout "
               "constraints and free-space distribution rules.\n";

        return 0;
    }
    catch (const std::exception& error) {
        std::cerr
            << "Fatal error: "
            << error.what()
            << '\n';

        return 1;
    }
}
