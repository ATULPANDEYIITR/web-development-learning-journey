/*
 * Advanced Responsive Design
 * ==========================
 *
 * C++17 case study:
 * A responsive analytics dashboard layout engine.
 *
 * The program models a realistic application in which the same dashboard
 * component can be placed in:
 *
 *   - a full-width desktop workspace,
 *   - a sidebar,
 *   - a tablet panel,
 *   - a mobile-width panel.
 *
 * The key design problem is that a component should often respond to its
 * available container width rather than blindly responding to the viewport.
 *
 * This program models:
 *
 *   1. Container measurements.
 *   2. Viewport measurements.
 *   3. Breakpoint classification.
 *   4. Fluid interpolation.
 *   5. clamp()-style bounded values.
 *   6. Container-aware card layout.
 *   7. Dashboard grid calculation.
 *   8. Content validation.
 *   9. Layout overflow detection.
 *  10. Performance-oriented layout calculations.
 *  11. Error handling.
 *  12. Unit-style assertions.
 *
 * Compile:
 *     g++ -std=c++17 -O2 responsive_design.cpp -o responsive_design
 *
 * Run:
 *     ./responsive_design
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
#include <vector>

namespace responsive {

// ---------------------------------------------------------------------------
// 1. BASIC DATA STRUCTURES
// ---------------------------------------------------------------------------

struct Size {
    double width{};
    double height{};
};

struct Viewport {
    double width{};
    double height{};
};

enum class ComponentMode {
    Compact,
    Standard,
    Expanded,
    Wide
};

std::string toString(ComponentMode mode) {
    switch (mode) {
        case ComponentMode::Compact:
            return "compact";
        case ComponentMode::Standard:
            return "standard";
        case ComponentMode::Expanded:
            return "expanded";
        case ComponentMode::Wide:
            return "wide";
    }

    throw std::logic_error("Unknown ComponentMode.");
}

struct CardLayout {
    ComponentMode mode{ComponentMode::Compact};
    int columns{1};
    double gap{};
    double padding{};
    double titleSize{};
    bool showDescription{true};
    bool stackActions{true};
};

struct DashboardLayout {
    int columns{1};
    double gap{};
    double cardWidth{};
    double cardHeight{};
    bool sidebarVisible{false};
};


// ---------------------------------------------------------------------------
// 2. VALIDATED DIMENSIONS
// ---------------------------------------------------------------------------

class Container {
public:
    explicit Container(Size size) : size_(size) {
        validate();
    }

    double width() const {
        return size_.width;
    }

    double height() const {
        return size_.height;
    }

private:
    Size size_;

    void validate() const {
        if (!std::isfinite(size_.width) ||
            !std::isfinite(size_.height)) {
            throw std::invalid_argument(
                "Container dimensions must be finite."
            );
        }

        if (size_.width < 0 || size_.height < 0) {
            throw std::invalid_argument(
                "Container dimensions cannot be negative."
            );
        }
    }
};


// ---------------------------------------------------------------------------
// 3. clamp()-STYLE OPERATION
// ---------------------------------------------------------------------------

double clampValue(
    double minimum,
    double preferred,
    double maximum
) {
    if (!std::isfinite(minimum) ||
        !std::isfinite(preferred) ||
        !std::isfinite(maximum)) {
        throw std::invalid_argument(
            "clamp values must be finite."
        );
    }

    if (minimum > maximum) {
        throw std::invalid_argument(
            "clamp minimum cannot exceed maximum."
        );
    }

    return std::max(
        minimum,
        std::min(preferred, maximum)
    );
}


// ---------------------------------------------------------------------------
// 4. FLUID INTERPOLATION
// ---------------------------------------------------------------------------

double interpolate(
    double input,
    double inputMinimum,
    double inputMaximum,
    double outputMinimum,
    double outputMaximum
) {
    if (inputMaximum <= inputMinimum) {
        throw std::invalid_argument(
            "Input maximum must exceed input minimum."
        );
    }

    const double ratio =
        (input - inputMinimum) /
        (inputMaximum - inputMinimum);

    const double boundedRatio =
        std::max(0.0, std::min(1.0, ratio));

    return outputMinimum +
        boundedRatio *
        (outputMaximum - outputMinimum);
}


// ---------------------------------------------------------------------------
// 5. RESPONSIVE TYPOGRAPHY
// ---------------------------------------------------------------------------

double calculateTitleSize(double containerWidth) {
    /*
     * This is a numerical analogue of:
     *
     *     clamp(1.25rem, fluid-preferred-value, 2.25rem)
     *
     * CSS remains responsible for actual browser typography. The C++
     * implementation models the underlying constraint for the application
     * case study.
     */
    const double preferred = interpolate(
        containerWidth,
        280.0,
        1200.0,
        20.0,
        36.0
    );

    return clampValue(20.0, preferred, 36.0);
}


// ---------------------------------------------------------------------------
// 6. CONTAINER-AWARE CARD LAYOUT
// ---------------------------------------------------------------------------

CardLayout calculateCardLayout(
    const Container& container
) {
    const double width = container.width();

    CardLayout layout;

    /*
     * These are container thresholds, not viewport thresholds.
     *
     * A card inside a narrow sidebar can therefore become compact even when
     * the browser itself is extremely wide.
     */
    if (width < 360.0) {
        layout.mode = ComponentMode::Compact;
        layout.columns = 1;
        layout.gap = 10.0;
        layout.padding = 12.0;
        layout.showDescription = false;
        layout.stackActions = true;
    } else if (width < 640.0) {
        layout.mode = ComponentMode::Standard;
        layout.columns = 1;
        layout.gap = 14.0;
        layout.padding = 16.0;
        layout.showDescription = true;
        layout.stackActions = true;
    } else if (width < 960.0) {
        layout.mode = ComponentMode::Expanded;
        layout.columns = 2;
        layout.gap = 18.0;
        layout.padding = 20.0;
        layout.showDescription = true;
        layout.stackActions = false;
    } else {
        layout.mode = ComponentMode::Wide;
        layout.columns = 3;
        layout.gap = 22.0;
        layout.padding = 24.0;
        layout.showDescription = true;
        layout.stackActions = false;
    }

    layout.titleSize = calculateTitleSize(width);

    return layout;
}


// ---------------------------------------------------------------------------
// 7. DASHBOARD GRID
// ---------------------------------------------------------------------------

DashboardLayout calculateDashboardLayout(
    const Container& container,
    int itemCount
) {
    if (itemCount < 0) {
        throw std::invalid_argument(
            "itemCount cannot be negative."
        );
    }

    const double width = container.width();

    DashboardLayout layout;

    /*
     * The minimum useful card width is part of the design constraint.
     * The resulting grid is therefore derived from available space.
     */
    constexpr double minimumCardWidth = 220.0;

    layout.columns = std::max(
        1,
        static_cast<int>(
            std::floor(
                width / minimumCardWidth
            )
        )
    );

    /*
     * A hard maximum prevents an extremely wide monitor from creating an
     * impractical number of columns.
     */
    layout.columns = std::min(layout.columns, 5);

    if (itemCount > 0) {
        layout.columns = std::min(
            layout.columns,
            itemCount
        );
    }

    layout.gap = clampValue(
        12.0,
        width * 0.018,
        28.0
    );

    const double totalGaps =
        layout.gap * (layout.columns - 1);

    layout.cardWidth =
        (width - totalGaps) / layout.columns;

    /*
     * A fixed aspect ratio is used for the dashboard cards. Real products
     * can instead derive height from actual content requirements.
     */
    layout.cardHeight = layout.cardWidth * 0.62;

    /*
     * A sidebar is an example of why container queries matter conceptually:
     * the dashboard can be narrow even when the viewport is wide.
     */
    layout.sidebarVisible = width >= 720.0;

    return layout;
}


// ---------------------------------------------------------------------------
// 8. CONTENT FIT VALIDATION
// ---------------------------------------------------------------------------

struct ContentMeasurement {
    double requiredWidth{};
    double availableWidth{};
};

bool fitsWithoutHorizontalOverflow(
    const ContentMeasurement& content
) {
    return content.requiredWidth <= content.availableWidth;
}

std::string overflowMessage(
    const ContentMeasurement& content
) {
    if (fitsWithoutHorizontalOverflow(content)) {
        return "content fits";
    }

    std::ostringstream message;

    message << "horizontal overflow: required "
            << content.requiredWidth
            << "px, available "
            << content.availableWidth
            << "px";

    return message.str();
}


// ---------------------------------------------------------------------------
// 9. COMPLETE DASHBOARD MODEL
// ---------------------------------------------------------------------------

class AnalyticsDashboard {
public:
    AnalyticsDashboard(
        Container container,
        int cardCount
    )
        : container_(std::move(container)),
          cardCount_(cardCount) {

        if (cardCount < 0) {
            throw std::invalid_argument(
                "cardCount cannot be negative."
            );
        }
    }

    void recompute() {
        cardLayout_ =
            calculateCardLayout(container_);

        dashboardLayout_ =
            calculateDashboardLayout(
                container_,
                cardCount_
            );
    }

    void print() const {
        std::cout
            << "Container: "
            << container_.width()
            << "px x "
            << container_.height()
            << "px\n";

        std::cout
            << "Component mode: "
            << toString(cardLayout_.mode)
            << "\n";

        std::cout
            << "Card columns: "
            << cardLayout_.columns
            << "\n";

        std::cout
            << "Dashboard columns: "
            << dashboardLayout_.columns
            << "\n";

        std::cout
            << "Gap: "
            << std::fixed
            << std::setprecision(1)
            << dashboardLayout_.gap
            << "px\n";

        std::cout
            << "Card width: "
            << dashboardLayout_.cardWidth
            << "px\n";

        std::cout
            << "Card height: "
            << dashboardLayout_.cardHeight
            << "px\n";

        std::cout
            << "Title size: "
            << cardLayout_.titleSize
            << "px\n";

        std::cout
            << "Description: "
            << (cardLayout_.showDescription
                ? "visible"
                : "hidden")
            << "\n";

        std::cout
            << "Actions: "
            << (cardLayout_.stackActions
                ? "stacked"
                : "inline")
            << "\n";

        std::cout
            << "Sidebar mode: "
            << (dashboardLayout_.sidebarVisible
                ? "available"
                : "compact")
            << "\n";
    }

    const CardLayout& cardLayout() const {
        return cardLayout_;
    }

    const DashboardLayout& dashboardLayout() const {
        return dashboardLayout_;
    }

private:
    Container container_;
    int cardCount_;
    CardLayout cardLayout_;
    DashboardLayout dashboardLayout_;
};


// ---------------------------------------------------------------------------
// 10. RESPONSIVE-SYSTEM COMPARISON
// ---------------------------------------------------------------------------

void printResponsiveComparison() {
    std::cout
        << "\n=== RESPONSIVE STRATEGY COMPARISON ===\n";

    std::cout
        << "Viewport media query:\n"
        << "  Responds to viewport-level conditions.\n"
        << "  Useful for page-level navigation and global layout.\n\n";

    std::cout
        << "Container query:\n"
        << "  Responds to a component's containing size.\n"
        << "  Useful for reusable cards, widgets and dashboard panels.\n\n";

    std::cout
        << "Fluid layout:\n"
        << "  Changes continuously over a range.\n"
        << "  Useful for dimensions, spacing and typography.\n\n";

    std::cout
        << "clamp():\n"
        << "  Constrains a preferred value between two bounds.\n"
        << "  Useful when continuous scaling needs safe limits.\n";
}


// ---------------------------------------------------------------------------
// 11. INTERACTIVE CASE STUDY
// ---------------------------------------------------------------------------

std::optional<double> readPositiveWidth(
    const std::string& prompt
) {
    std::cout << prompt;

    double width{};

    if (!(std::cin >> width)) {
        return std::nullopt;
    }

    if (!std::isfinite(width) || width <= 0) {
        return std::nullopt;
    }

    return width;
}

void runInteractiveCaseStudy() {
    std::cout
        << "\n=== INTERACTIVE DASHBOARD CASE STUDY ===\n"
        << "Enter a container width in pixels.\n"
        << "Enter 0 or invalid input to skip the interactive section.\n";

    std::cout << "Container width: ";

    double width{};

    if (!(std::cin >> width)) {
        std::cin.clear();
        std::cin.ignore(
            std::numeric_limits<std::streamsize>::max(),
            '\n'
        );
        return;
    }

    if (!std::isfinite(width) || width <= 0) {
        return;
    }

    std::cout << "Card count: ";

    int cardCount{};

    if (!(std::cin >> cardCount) || cardCount < 0) {
        std::cout
            << "Invalid card count. Using 6.\n";

        cardCount = 6;

        std::cin.clear();
        std::cin.ignore(
            std::numeric_limits<std::streamsize>::max(),
            '\n'
        );
    }

    AnalyticsDashboard dashboard(
        Container({width, 700.0}),
        cardCount
    );

    dashboard.recompute();
    dashboard.print();

    ContentMeasurement content{
        420.0,
        dashboard.dashboardLayout().cardWidth
    };

    std::cout
        << "Content-fit check: "
        << overflowMessage(content)
        << "\n";
}


// ---------------------------------------------------------------------------
// 12. AUTOMATED TESTS
// ---------------------------------------------------------------------------

void runTests() {
    std::cout
        << "\n=== AUTOMATED TESTS ===\n";

    assert(
        clampValue(10.0, 5.0, 20.0)
        == 10.0
    );

    assert(
        clampValue(10.0, 15.0, 20.0)
        == 15.0
    );

    assert(
        clampValue(10.0, 30.0, 20.0)
        == 20.0
    );

    assert(
        std::abs(
            interpolate(
                0.0,
                0.0,
                100.0,
                10.0,
                20.0
            ) - 10.0
        ) < 0.0001
    );

    assert(
        std::abs(
            interpolate(
                50.0,
                0.0,
                100.0,
                10.0,
                20.0
            ) - 15.0
        ) < 0.0001
    );

    assert(
        std::abs(
            interpolate(
                100.0,
                0.0,
                100.0,
                10.0,
                20.0
            ) - 20.0
        ) < 0.0001
    );

    {
        Container compact({320.0, 600.0});
        CardLayout layout =
            calculateCardLayout(compact);

        assert(
            layout.mode ==
            ComponentMode::Compact
        );

        assert(layout.columns == 1);
        assert(!layout.showDescription);
    }

    {
        Container standard({500.0, 600.0});
        CardLayout layout =
            calculateCardLayout(standard);

        assert(
            layout.mode ==
            ComponentMode::Standard
        );

        assert(layout.columns == 1);
        assert(layout.showDescription);
    }

    {
        Container expanded({800.0, 600.0});
        CardLayout layout =
            calculateCardLayout(expanded);

        assert(
            layout.mode ==
            ComponentMode::Expanded
        );

        assert(layout.columns == 2);
        assert(!layout.stackActions);
    }

    {
        Container wide({1400.0, 800.0});
        DashboardLayout layout =
            calculateDashboardLayout(wide, 10);

        assert(layout.columns == 5);
        assert(layout.cardWidth > 0);
    }

    {
        ContentMeasurement fitting{100.0, 200.0};

        assert(
            fitsWithoutHorizontalOverflow(fitting)
        );
    }

    {
        ContentMeasurement overflowing{300.0, 200.0};

        assert(
            !fitsWithoutHorizontalOverflow(overflowing)
        );
    }

    std::cout
        << "All automated tests passed.\n";
}


// ---------------------------------------------------------------------------
// 13. ERROR-HANDLING DEMONSTRATION
// ---------------------------------------------------------------------------

void demonstrateErrorHandling() {
    std::cout
        << "\n=== ERROR HANDLING ===\n";

    try {
        Container invalid({-100.0, 400.0});
        (void)invalid;
    } catch (const std::exception& error) {
        std::cout
            << "Rejected invalid container: "
            << error.what()
            << "\n";
    }

    try {
        clampValue(100.0, 50.0, 20.0);
    } catch (const std::exception& error) {
        std::cout
            << "Rejected invalid clamp bounds: "
            << error.what()
            << "\n";
    }

    try {
        interpolate(
            10.0,
            100.0,
            100.0,
            10.0,
            20.0
        );
    } catch (const std::exception& error) {
        std::cout
            << "Rejected invalid interpolation range: "
            << error.what()
            << "\n";
    }
}


// ---------------------------------------------------------------------------
// 14. PERFORMANCE ANALYSIS
// ---------------------------------------------------------------------------

void printComplexityAnalysis() {
    std::cout
        << "\n=== COMPLEXITY ===\n"
        << "clampValue: O(1) time, O(1) space.\n"
        << "interpolate: O(1) time, O(1) space.\n"
        << "calculateCardLayout: O(1) time, O(1) space.\n"
        << "calculateDashboardLayout: O(1) time, O(1) space.\n"
        << "Dashboard recomputation: O(1) for the modeled layout state.\n"
        << "Rendering a real dashboard remains dependent on DOM/UI size.\n";
}


// ---------------------------------------------------------------------------
// 15. MAIN
// ---------------------------------------------------------------------------

} // namespace responsive

int main() {
    using namespace responsive;

    try {
        std::cout
            << "============================================================\n"
            << "ADVANCED RESPONSIVE DESIGN CASE STUDY\n"
            << "============================================================\n";

        printResponsiveComparison();

        std::cout
            << "\n=== PREDEFINED DASHBOARD STATES ===\n";

        const std::vector<double> widths{
            320.0,
            480.0,
            640.0,
            900.0,
            1280.0,
            1600.0
        };

        for (double width : widths) {
            std::cout
                << "\n--- " << width << "px container ---\n";

            AnalyticsDashboard dashboard(
                Container({width, 720.0}),
                8
            );

            dashboard.recompute();
            dashboard.print();
        }

        runTests();
        demonstrateErrorHandling();
        printComplexityAnalysis();

        runInteractiveCaseStudy();

        std::cout
            << "\nCase study completed.\n";

        return 0;
    } catch (const std::exception& error) {
        std::cerr
            << "Fatal error: "
            << error.what()
            << '\n';

        return 1;
    }
}
