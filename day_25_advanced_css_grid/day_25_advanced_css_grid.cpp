/*
 * Advanced CSS Grid
 * -----------------
 *
 * C++17 case study:
 * A responsive analytics dashboard layout planner.
 *
 * This program models a realistic application that receives a collection
 * of dashboard widgets and produces a CSS Grid layout plan.
 *
 * The program demonstrates:
 *   - Explicit and implicit grid concepts
 *   - minmax() reasoning
 *   - auto-fit-style column estimation
 *   - Widget placement
 *   - Named dashboard regions
 *   - Responsive layout planning
 *   - Validation
 *   - Error handling
 *   - Data structures
 *   - Sorting and filtering
 *   - Complexity analysis
 *   - CSS generation
 *   - Edge cases
 *
 * Compile:
 *   g++ -std=c++17 -O2 -Wall -Wextra -pedantic advanced_css_grid.cpp -o grid
 */

#include <algorithm>
#include <iomanip>
#include <iostream>
#include <limits>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>


// ---------------------------------------------------------------------------
// ENUMERATIONS
// ---------------------------------------------------------------------------

enum class WidgetType {
    Header,
    Navigation,
    Chart,
    Table,
    Metric,
    Alert,
    Activity,
    Footer
};

enum class Priority {
    Low,
    Medium,
    High
};


// ---------------------------------------------------------------------------
// CONVERSION HELPERS
// ---------------------------------------------------------------------------

std::string widgetTypeToString(WidgetType type) {
    switch (type) {
        case WidgetType::Header:
            return "Header";
        case WidgetType::Navigation:
            return "Navigation";
        case WidgetType::Chart:
            return "Chart";
        case WidgetType::Table:
            return "Table";
        case WidgetType::Metric:
            return "Metric";
        case WidgetType::Alert:
            return "Alert";
        case WidgetType::Activity:
            return "Activity";
        case WidgetType::Footer:
            return "Footer";
    }

    return "Unknown";
}

std::string priorityToString(Priority priority) {
    switch (priority) {
        case Priority::Low:
            return "Low";
        case Priority::Medium:
            return "Medium";
        case Priority::High:
            return "High";
    }

    return "Unknown";
}


// ---------------------------------------------------------------------------
// GRID CONFIGURATION
// ---------------------------------------------------------------------------

struct GridConfig {
    int viewportWidthPx = 1440;
    int viewportHeightPx = 900;

    int minimumCardWidthPx = 240;
    int gapPx = 16;

    int sidebarMinimumPx = 220;
    int sidebarMaximumPx = 300;

    int asideMinimumPx = 280;
    int asideMaximumPx = 380;

    bool useAutoFit = true;
};


// ---------------------------------------------------------------------------
// WIDGET MODEL
// ---------------------------------------------------------------------------

struct Widget {
    int id;
    std::string name;
    WidgetType type;

    int preferredWidthUnits;
    int preferredHeightUnits;

    Priority priority;

    bool canSpanColumns;
    bool canSpanRows;

    bool visible = true;

    Widget(
        int widgetId,
        std::string widgetName,
        WidgetType widgetType,
        int widthUnits,
        int heightUnits,
        Priority widgetPriority,
        bool columnSpanning,
        bool rowSpanning
    )
        : id(widgetId),
          name(std::move(widgetName)),
          type(widgetType),
          preferredWidthUnits(widthUnits),
          preferredHeightUnits(heightUnits),
          priority(widgetPriority),
          canSpanColumns(columnSpanning),
          canSpanRows(rowSpanning) {}
};


// ---------------------------------------------------------------------------
// GRID POSITION
// ---------------------------------------------------------------------------

struct GridPosition {
    int columnStart = 1;
    int columnEnd = 2;
    int rowStart = 1;
    int rowEnd = 2;

    bool valid() const {
        return
            columnStart >= 1 &&
            columnEnd > columnStart &&
            rowStart >= 1 &&
            rowEnd > rowStart;
    }
};


// ---------------------------------------------------------------------------
// PLACED WIDGET
// ---------------------------------------------------------------------------

struct PlacedWidget {
    Widget widget;
    GridPosition position;
};


// ---------------------------------------------------------------------------
// GRID PLANNER
// ---------------------------------------------------------------------------

class GridPlanner {
private:
    GridConfig config_;
    std::vector<Widget> widgets_;

    int calculateAutoFitColumns() const {
        if (config_.viewportWidthPx <= 0) {
            return 0;
        }

        const int minimum =
            std::max(1, config_.minimumCardWidthPx);

        const int gap =
            std::max(0, config_.gapPx);

        /*
         * This approximates:
         *
         *   repeat(auto-fit, minmax(minimum, 1fr))
         *
         * The browser's actual CSS Grid algorithm is more sophisticated.
         * This model is useful for application-level planning only.
         */
        const int columns =
            (config_.viewportWidthPx + gap) /
            (minimum + gap);

        return std::max(1, columns);
    }

    std::vector<Widget> visibleWidgets() const {
        std::vector<Widget> result;

        for (const Widget& widget : widgets_) {
            if (widget.visible) {
                result.push_back(widget);
            }
        }

        return result;
    }

public:
    explicit GridPlanner(GridConfig config)
        : config_(std::move(config)) {

        if (config_.viewportWidthPx <= 0) {
            throw std::invalid_argument(
                "Viewport width must be positive."
            );
        }

        if (config_.viewportHeightPx <= 0) {
            throw std::invalid_argument(
                "Viewport height must be positive."
            );
        }

        if (config_.minimumCardWidthPx <= 0) {
            throw std::invalid_argument(
                "Minimum card width must be positive."
            );
        }

        if (config_.gapPx < 0) {
            throw std::invalid_argument(
                "Grid gap cannot be negative."
            );
        }
    }

    void addWidget(const Widget& widget) {
        if (widget.id <= 0) {
            throw std::invalid_argument(
                "Widget ID must be positive."
            );
        }

        if (widget.name.empty()) {
            throw std::invalid_argument(
                "Widget name cannot be empty."
            );
        }

        if (widget.preferredWidthUnits <= 0) {
            throw std::invalid_argument(
                "Preferred width must be positive."
            );
        }

        if (widget.preferredHeightUnits <= 0) {
            throw std::invalid_argument(
                "Preferred height must be positive."
            );
        }

        const auto duplicate =
            std::find_if(
                widgets_.begin(),
                widgets_.end(),
                [&](const Widget& existing) {
                    return existing.id == widget.id;
                }
            );

        if (duplicate != widgets_.end()) {
            throw std::invalid_argument(
                "Duplicate widget ID."
            );
        }

        widgets_.push_back(widget);
    }

    int columnCount() const {
        return calculateAutoFitColumns();
    }

    std::vector<PlacedWidget> createResponsivePlan() const {
        std::vector<Widget> visible = visibleWidgets();

        /*
         * High-priority items are processed first so large structural
         * components can receive placement before ordinary cards.
         *
         * This is an application-specific policy. CSS Grid itself does not
         * assign semantic priorities to elements.
         */
        std::stable_sort(
            visible.begin(),
            visible.end(),
            [](const Widget& left, const Widget& right) {
                if (left.priority != right.priority) {
                    return static_cast<int>(left.priority) >
                           static_cast<int>(right.priority);
                }

                return left.id < right.id;
            }
        );

        const int columns =
            std::max(1, columnCount());

        std::vector<PlacedWidget> result;

        int currentColumn = 1;
        int currentRow = 1;

        for (const Widget& widget : visible) {
            int columnSpan = 1;
            int rowSpan = 1;

            if (widget.canSpanColumns) {
                columnSpan =
                    std::min(
                        widget.preferredWidthUnits,
                        columns
                    );
            }

            if (widget.canSpanRows) {
                rowSpan =
                    std::max(
                        1,
                        widget.preferredHeightUnits
                    );
            }

            /*
             * If the requested span does not fit on the current row,
             * move to an implicit next row.
             */
            if (
                currentColumn + columnSpan - 1 >
                columns
            ) {
                currentColumn = 1;
                ++currentRow;
            }

            GridPosition position;

            position.columnStart = currentColumn;
            position.columnEnd =
                currentColumn + columnSpan;

            position.rowStart = currentRow;
            position.rowEnd =
                currentRow + rowSpan;

            if (!position.valid()) {
                throw std::logic_error(
                    "Generated invalid Grid position."
                );
            }

            result.push_back(
                PlacedWidget{
                    widget,
                    position
                }
            );

            currentColumn += columnSpan;

            if (currentColumn > columns) {
                currentColumn = 1;
                ++currentRow;
            }
        }

        return result;
    }

    std::string generateCSS() const {
        std::ostringstream css;

        css
            << ".dashboard {\n"
            << "  display: grid;\n"
            << "  grid-template-columns: "
            << "minmax("
            << config_.sidebarMinimumPx
            << "px, "
            << config_.sidebarMaximumPx
            << "px) "
            << "minmax(0, 1fr) "
            << "minmax("
            << config_.asideMinimumPx
            << "px, "
            << config_.asideMaximumPx
            << "px);\n"
            << "  grid-template-rows: "
            << "auto minmax(20rem, 1fr) auto;\n"
            << "  gap: "
            << config_.gapPx
            << "px;\n"
            << "}\n\n";

        css
            << ".widget-grid {\n"
            << "  display: grid;\n"
            << "  grid-template-columns: repeat("
            << (config_.useAutoFit ? "auto-fit" : "auto-fill")
            << ", minmax("
            << config_.minimumCardWidthPx
            << "px, 1fr));\n"
            << "  gap: "
            << config_.gapPx
            << "px;\n"
            << "}\n";

        return css.str();
    }

    void printPlan() const {
        const std::vector<PlacedWidget> plan =
            createResponsivePlan();

        std::cout
            << "\nResponsive Grid Plan\n"
            << "====================\n";

        std::cout
            << "Viewport: "
            << config_.viewportWidthPx
            << "px x "
            << config_.viewportHeightPx
            << "px\n";

        std::cout
            << "Minimum card width: "
            << config_.minimumCardWidthPx
            << "px\n";

        std::cout
            << "Gap: "
            << config_.gapPx
            << "px\n";

        std::cout
            << "Estimated columns: "
            << columnCount()
            << "\n\n";

        for (const PlacedWidget& item : plan) {
            const GridPosition& p = item.position;

            std::cout
                << std::left
                << std::setw(20)
                << item.widget.name
                << " | "
                << std::setw(10)
                << widgetTypeToString(item.widget.type)
                << " | priority="
                << std::setw(6)
                << priorityToString(item.widget.priority)
                << " | columns "
                << p.columnStart
                << " / "
                << p.columnEnd
                << " | rows "
                << p.rowStart
                << " / "
                << p.rowEnd
                << "\n";
        }
    }
};


// ---------------------------------------------------------------------------
// RESPONSIVE CSS STRATEGY
// ---------------------------------------------------------------------------

class ResponsiveStrategy {
public:
    static std::string explain() {
        return
            "The dashboard uses three concepts together:\n"
            "1. minmax() protects minimum and maximum track behavior.\n"
            "2. auto-fit allows repeated card tracks to respond to space.\n"
            "3. implicit rows allow additional content to extend the grid.\n";
    }

    static int estimateColumns(
        int width,
        int minimum,
        int gap
    ) {
        if (width <= 0) {
            throw std::invalid_argument(
                "Width must be positive."
            );
        }

        if (minimum <= 0) {
            throw std::invalid_argument(
                "Minimum width must be positive."
            );
        }

        if (gap < 0) {
            throw std::invalid_argument(
                "Gap cannot be negative."
            );
        }

        return std::max(
            1,
            (width + gap) /
            (minimum + gap)
        );
    }
};


// ---------------------------------------------------------------------------
// EDGE CASE DEMONSTRATIONS
// ---------------------------------------------------------------------------

void demonstrateEdgeCases() {
    std::cout
        << "\nEdge Cases\n"
        << "==========\n";

    const std::vector<int> widths{
        320,
        480,
        768,
        1024,
        1440,
        1920
    };

    for (const int width : widths) {
        const int columns =
            ResponsiveStrategy::estimateColumns(
                width,
                240,
                16
            );

        std::cout
            << width
            << "px -> "
            << columns
            << " estimated column(s)\n";
    }

    std::cout
        << "\nInvalid configuration checks:\n";

    try {
        ResponsiveStrategy::estimateColumns(
            800,
            0,
            16
        );
    } catch (const std::exception& error) {
        std::cout
            << "Caught expected error: "
            << error.what()
            << "\n";
    }

    try {
        ResponsiveStrategy::estimateColumns(
            800,
            240,
            -1
        );
    } catch (const std::exception& error) {
        std::cout
            << "Caught expected error: "
            << error.what()
            << "\n";
    }
}


// ---------------------------------------------------------------------------
// COMPLEXITY DISCUSSION
// ---------------------------------------------------------------------------

void explainComplexity() {
    std::cout
        << "\nComplexity Considerations\n"
        << "=========================\n"
        << "Widget validation: O(1) per basic validation operation.\n"
        << "Duplicate-ID search: O(n) for each insertion in this implementation.\n"
        << "Priority sorting: O(n log n).\n"
        << "Placement pass: O(n) after sorting.\n"
        << "CSS generation: O(1) relative to widget count.\n\n"
        << "For very large dashboards, an unordered_set could maintain widget IDs\n"
        << "for average O(1) duplicate detection. The vector remains useful here\n"
        << "because dashboard widgets are also stored in display order.\n";
}


// ---------------------------------------------------------------------------
// MAIN CASE STUDY
// ---------------------------------------------------------------------------

int main() {
    try {
        GridConfig configuration;

        configuration.viewportWidthPx = 1440;
        configuration.viewportHeightPx = 900;
        configuration.minimumCardWidthPx = 240;
        configuration.gapPx = 16;
        configuration.sidebarMinimumPx = 220;
        configuration.sidebarMaximumPx = 300;
        configuration.asideMinimumPx = 280;
        configuration.asideMaximumPx = 380;
        configuration.useAutoFit = true;

        GridPlanner planner(configuration);

        /*
         * A realistic analytics dashboard:
         *
         * - Header spans the dashboard.
         * - Navigation is persistent.
         * - Metric cards are compact.
         * - Charts can span columns.
         * - A table may require additional width.
         * - Alerts and activity feed are secondary components.
         */
        planner.addWidget(
            Widget(
                1,
                "Global Header",
                WidgetType::Header,
                4,
                1,
                Priority::High,
                true,
                false
            )
        );

        planner.addWidget(
            Widget(
                2,
                "Navigation",
                WidgetType::Navigation,
                1,
                4,
                Priority::High,
                false,
                true
            )
        );

        planner.addWidget(
            Widget(
                3,
                "Revenue Metric",
                WidgetType::Metric,
                1,
                1,
                Priority::Medium,
                false,
                false
            )
        );

        planner.addWidget(
            Widget(
                4,
                "Traffic Metric",
                WidgetType::Metric,
                1,
                1,
                Priority::Medium,
                false,
                false
            )
        );

        planner.addWidget(
            Widget(
                5,
                "Conversion Metric",
                WidgetType::Metric,
                1,
                1,
                Priority::Medium,
                false,
                false
            )
        );

        planner.addWidget(
            Widget(
                6,
                "Revenue Chart",
                WidgetType::Chart,
                2,
                2,
                Priority::High,
                true,
                true
            )
        );

        planner.addWidget(
            Widget(
                7,
                "Traffic Chart",
                WidgetType::Chart,
                2,
                2,
                Priority::High,
                true,
                true
            )
        );

        planner.addWidget(
            Widget(
                8,
                "Transactions",
                WidgetType::Table,
                3,
                3,
                Priority::High,
                true,
                true
            )
        );

        planner.addWidget(
            Widget(
                9,
                "System Alerts",
                WidgetType::Alert,
                1,
                1,
                Priority::Medium,
                false,
                false
            )
        );

        planner.addWidget(
            Widget(
                10,
                "Recent Activity",
                WidgetType::Activity,
                1,
                2,
                Priority::Low,
                false,
                true
            )
        );

        planner.addWidget(
            Widget(
                11,
                "Footer",
                WidgetType::Footer,
                4,
                1,
                Priority::Low,
                true,
                false
            )
        );

        std::cout
            << "ADVANCED CSS GRID CASE STUDY\n"
            << "============================\n\n";

        std::cout
            << ResponsiveStrategy::explain()
            << "\n";

        planner.printPlan();

        std::cout
            << "\nGenerated CSS\n"
            << "=============\n"
            << planner.generateCSS()
            << "\n";

        demonstrateEdgeCases();
        explainComplexity();

        std::cout
            << "\nImplementation Notes\n"
            << "====================\n"
            << "The C++ planner does not attempt to reproduce the browser's complete\n"
            << "CSS Grid layout algorithm. It models application-level decisions\n"
            << "such as widget validation, ordering, track estimation, and CSS\n"
            << "generation. The browser remains responsible for actual layout.\n\n"
            << "The distinction is important: application code should describe\n"
            << "layout intent, while CSS Grid should perform responsive layout.\n";

        return 0;
    }
    catch (const std::exception& error) {
        std::cerr
            << "Fatal configuration error: "
            << error.what()
            << '\n';

        return 1;
    }
}
