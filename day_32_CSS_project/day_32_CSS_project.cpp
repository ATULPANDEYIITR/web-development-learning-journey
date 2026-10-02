#include <algorithm>
#include <cmath>
#include <exception>
#include <iomanip>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

/*
 * Responsive Landing Page Layout Engine
 *
 * This C++17 case study models the constraint logic behind a responsive
 * landing page. It does not attempt to render HTML. Instead, it represents
 * page components as objects with minimum and preferred dimensions and uses
 * viewport constraints to choose practical layout modes.
 *
 * The design intentionally avoids device-specific names such as "phone"
 * or "tablet". Layout decisions are based on available width and content
 * requirements.
 */

struct Component {
    std::string name;
    double minimum_width;
    double preferred_width;
    double minimum_height;
    bool can_grow;

    void validate() const {
        if (name.empty()) {
            throw std::invalid_argument("Component name cannot be empty.");
        }

        if (minimum_width <= 0.0 || preferred_width <= 0.0) {
            throw std::invalid_argument(
                "Component widths must be greater than zero: " + name
            );
        }

        if (minimum_height <= 0.0) {
            throw std::invalid_argument(
                "Component height must be greater than zero: " + name
            );
        }

        if (preferred_width < minimum_width) {
            throw std::invalid_argument(
                "Preferred width cannot be smaller than minimum width: " + name
            );
        }
    }
};

enum class NavigationMode {
    Collapsed,
    Horizontal
};

enum class HeroArrangement {
    Stacked,
    TwoColumn
};

struct LayoutResult {
    int viewport_width;
    int viewport_height;
    NavigationMode navigation;
    HeroArrangement hero;
    int feature_columns;
    double estimated_content_height;
    std::vector<std::string> warnings;
};

class LayoutEngine {
public:
    explicit LayoutEngine(std::vector<Component> components)
        : components_(std::move(components)) {
        for (const auto& component : components_) {
            component.validate();
        }
    }

    LayoutResult evaluate(int viewport_width, int viewport_height) const {
        if (viewport_width < 320) {
            throw std::invalid_argument(
                "Viewport width below the supported 320px minimum."
            );
        }

        if (viewport_height <= 0) {
            throw std::invalid_argument(
                "Viewport height must be greater than zero."
            );
        }

        LayoutResult result{
            viewport_width,
            viewport_height,
            NavigationMode::Collapsed,
            HeroArrangement::Stacked,
            1,
            0.0,
            {}
        };

        /*
         * The navigation breakpoint is derived from the space required by
         * the actual navigation content. At this width the full navigation
         * can fit without forcing links into unreadable wrapping.
         */
        constexpr int navigation_breakpoint = 700;

        if (viewport_width >= navigation_breakpoint) {
            result.navigation = NavigationMode::Horizontal;
            result.hero = HeroArrangement::TwoColumn;
        }

        result.feature_columns = calculateFeatureColumns(viewport_width);

        result.estimated_content_height =
            calculateEstimatedHeight(result, viewport_width);

        if (viewport_width < 380) {
            result.warnings.emplace_back(
                "Very narrow viewport: verify long headings and form controls "
                "with production content."
            );
        }

        if (viewport_height < 500) {
            result.warnings.emplace_back(
                "Short viewport: primary content may require substantial scrolling."
            );
        }

        return result;
    }

private:
    std::vector<Component> components_;

    static int calculateFeatureColumns(int viewport_width) {
        /*
         * Three feature cards are desirable only when each card can receive
         * at least 260px. The calculation is based on available content
         * width rather than on a named device category.
         */
        constexpr int content_gutter = 64;
        constexpr int minimum_card_width = 260;
        constexpr int gap = 16;

        const int usable_width = viewport_width - content_gutter;

        if (usable_width < minimum_card_width) {
            return 1;
        }

        const int possible_columns =
            (usable_width + gap) / (minimum_card_width + gap);

        return std::clamp(possible_columns, 1, 3);
    }

    static double calculateEstimatedHeight(
        const LayoutResult& result,
        int viewport_width
    ) {
        double height = 0.0;

        // Header contribution.
        height += 76.0;

        /*
         * The hero requires less vertical space when text and visual content
         * can occupy two columns. The estimate is intentionally simple:
         * a layout engine must establish constraints, while a browser's
         * rendering engine would perform the exact text measurement.
         */
        if (result.hero == HeroArrangement::Stacked) {
            height += 760.0;
        } else {
            height += 620.0;
        }

        height += 520.0; // Features.
        height += 430.0; // Process.
        height += 420.0; // Contact.
        height += 80.0;  // Footer.

        if (result.feature_columns == 1) {
            height += 240.0;
        }

        /*
         * Wider screens generally allow less vertical wrapping. This factor
         * is bounded so the model never reports an unrealistically negative
         * or zero content height.
         */
        const double width_factor =
            std::clamp(1200.0 / static_cast<double>(viewport_width), 0.72, 1.0);

        height *= width_factor;

        return std::max(height, 600.0);
    }
};

std::string toString(NavigationMode mode) {
    switch (mode) {
        case NavigationMode::Collapsed:
            return "collapsed";
        case NavigationMode::Horizontal:
            return "horizontal";
    }

    return "unknown";
}

std::string toString(HeroArrangement arrangement) {
    switch (arrangement) {
        case HeroArrangement::Stacked:
            return "stacked";
        case HeroArrangement::TwoColumn:
            return "two-column";
    }

    return "unknown";
}

void printResult(const LayoutResult& result) {
    std::cout
        << std::left
        << std::setw(8) << result.viewport_width
        << std::setw(16) << toString(result.navigation)
        << std::setw(14) << toString(result.hero)
        << std::setw(10) << result.feature_columns
        << std::fixed
        << std::setprecision(0)
        << result.estimated_content_height
        << "px";

    if (!result.warnings.empty()) {
        std::cout << "  warnings=" << result.warnings.size();
    }

    std::cout << '\n';
}

void printWarnings(const LayoutResult& result) {
    for (const auto& warning : result.warnings) {
        std::cout << "  - " << warning << '\n';
    }
}

void runResponsiveCaseStudy() {
    std::cout << "Responsive Landing Page Layout Engine\n";
    std::cout << "=====================================\n\n";

    const std::vector<Component> components{
        {
            "primary navigation",
            520.0,
            720.0,
            76.0,
            true
        },
        {
            "hero copy",
            300.0,
            700.0,
            420.0,
            true
        },
        {
            "hero visual",
            280.0,
            520.0,
            360.0,
            true
        },
        {
            "feature card",
            220.0,
            360.0,
            300.0,
            true
        },
        {
            "contact form",
            280.0,
            520.0,
            240.0,
            true
        }
    };

    LayoutEngine engine(components);

    const std::vector<std::pair<int, int>> viewports{
        {320, 720},
        {360, 800},
        {600, 900},
        {700, 900},
        {1024, 900},
        {1440, 900}
    };

    std::cout
        << std::left
        << std::setw(8) << "Width"
        << std::setw(16) << "Navigation"
        << std::setw(14) << "Hero"
        << std::setw(10) << "Columns"
        << "Estimated height\n";

    std::cout << std::string(72, '-') << '\n';

    for (const auto& [width, height] : viewports) {
        const LayoutResult result = engine.evaluate(width, height);
        printResult(result);
    }

    std::cout << "\nEdge-case warnings\n";
    std::cout << "------------------\n";

    const LayoutResult narrow_result = engine.evaluate(320, 720);
    printWarnings(narrow_result);

    const LayoutResult short_result = engine.evaluate(1024, 400);
    printWarnings(short_result);
}

void runConstraintFailureCase() {
    std::cout << "\nConstraint validation case\n";
    std::cout << "==========================\n";

    try {
        const Component invalid_component{
            "invalid feature",
            320.0,
            240.0,
            200.0,
            true
        };

        invalid_component.validate();

        std::cout << "Unexpected result: invalid component was accepted.\n";
    } catch (const std::invalid_argument& error) {
        std::cout << "Rejected invalid layout constraint: "
                  << error.what() << '\n';
    }
}

void runViewportFailureCase() {
    std::cout << "\nViewport validation case\n";
    std::cout << "========================\n";

    const std::vector<Component> valid_components{
        {"hero", 300.0, 600.0, 400.0, true}
    };

    LayoutEngine engine(valid_components);

    try {
        static_cast<void>(engine.evaluate(280, 720));
        std::cout << "Unexpected result: unsupported viewport was accepted.\n";
    } catch (const std::invalid_argument& error) {
        std::cout << "Rejected unsupported viewport: "
                  << error.what() << '\n';
    }
}

int main() {
    try {
        runResponsiveCaseStudy();
        runConstraintFailureCase();
        runViewportFailureCase();
    } catch (const std::exception& error) {
        std::cerr << "Fatal layout-engine error: "
                  << error.what() << '\n';
        return 1;
    }

    return 0;
}
