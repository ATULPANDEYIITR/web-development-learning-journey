#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

/*
 * CSS Box Model Case Study
 *
 * Scenario:
 *     A web application needs a predictable component sizing engine for
 *     cards, panels, and responsive containers. The C++ program models
 *     important CSS box-model calculations so the layout rules can be
 *     tested independently of a browser.
 *
 * The program demonstrates:
 *     content
 *     padding
 *     border
 *     margin
 *     content-box
 *     border-box
 *     dimensions
 *     min/max constraints
 *     overflow
 *     validation
 *     reusable classes
 *     test-like verification
 *
 * Compile:
 *     C++17 or later
 */

namespace cssbox {

// ============================================================================
// Basic types
// ============================================================================

struct Edges {
    double top{0};
    double right{0};
    double bottom{0};
    double left{0};

    double horizontal() const {
        return left + right;
    }

    double vertical() const {
        return top + bottom;
    }
};

enum class BoxSizing {
    ContentBox,
    BorderBox
};

enum class OverflowMode {
    Visible,
    Hidden,
    Clip,
    Scroll,
    Auto
};

struct Size {
    double width{0};
    double height{0};
};

struct OverflowResult {
    double horizontal{0};
    double vertical{0};

    bool hasHorizontalOverflow() const {
        return horizontal > 0;
    }

    bool hasVerticalOverflow() const {
        return vertical > 0;
    }
};

// ============================================================================
// Utility validation
// ============================================================================

void requireNonNegative(double value, const std::string& field) {
    if (!std::isfinite(value)) {
        throw std::invalid_argument(field + " must be finite.");
    }

    if (value < 0) {
        throw std::invalid_argument(field + " cannot be negative.");
    }
}

void validateEdges(const Edges& edges, const std::string& field) {
    requireNonNegative(edges.top, field + ".top");
    requireNonNegative(edges.right, field + ".right");
    requireNonNegative(edges.bottom, field + ".bottom");
    requireNonNegative(edges.left, field + ".left");
}

// ============================================================================
// Box model
// ============================================================================

class BoxModel {
private:
    Size declaredSize_;
    Edges padding_;
    Edges border_;
    Edges margin_;
    BoxSizing boxSizing_;

    std::optional<double> minWidth_;
    std::optional<double> maxWidth_;
    std::optional<double> minHeight_;
    std::optional<double> maxHeight_;

public:
    BoxModel(
        Size declaredSize,
        Edges padding,
        Edges border,
        Edges margin,
        BoxSizing boxSizing = BoxSizing::ContentBox
    )
        : declaredSize_(declaredSize),
          padding_(padding),
          border_(border),
          margin_(margin),
          boxSizing_(boxSizing) {

        requireNonNegative(declaredSize_.width, "declared width");
        requireNonNegative(declaredSize_.height, "declared height");
        validateEdges(padding_, "padding");
        validateEdges(border_, "border");

        // Margins are intentionally not validated as non-negative because
        // CSS permits negative margins.
        if (!std::isfinite(margin_.top) ||
            !std::isfinite(margin_.right) ||
            !std::isfinite(margin_.bottom) ||
            !std::isfinite(margin_.left)) {
            throw std::invalid_argument("Margins must be finite.");
        }
    }

    void setWidthConstraints(
        std::optional<double> minimum,
        std::optional<double> maximum
    ) {
        if (minimum && *minimum < 0) {
            throw std::invalid_argument("Minimum width cannot be negative.");
        }

        if (maximum && *maximum < 0) {
            throw std::invalid_argument("Maximum width cannot be negative.");
        }

        if (minimum && maximum && *minimum > *maximum) {
            throw std::invalid_argument(
                "Minimum width cannot exceed maximum width."
            );
        }

        minWidth_ = minimum;
        maxWidth_ = maximum;
    }

    void setHeightConstraints(
        std::optional<double> minimum,
        std::optional<double> maximum
    ) {
        if (minimum && *minimum < 0) {
            throw std::invalid_argument("Minimum height cannot be negative.");
        }

        if (maximum && *maximum < 0) {
            throw std::invalid_argument("Maximum height cannot be negative.");
        }

        if (minimum && maximum && *minimum > *maximum) {
            throw std::invalid_argument(
                "Minimum height cannot exceed maximum height."
            );
        }

        minHeight_ = minimum;
        maxHeight_ = maximum;
    }

    Size contentSize() const {
        if (boxSizing_ == BoxSizing::ContentBox) {
            return declaredSize_;
        }

        // border-box means declared dimensions include padding and border.
        const double contentWidth =
            declaredSize_.width -
            padding_.horizontal() -
            border_.horizontal();

        const double contentHeight =
            declaredSize_.height -
            padding_.vertical() -
            border_.vertical();

        if (contentWidth < 0 || contentHeight < 0) {
            throw std::invalid_argument(
                "Border-box dimensions are too small for "
                "the specified padding and border."
            );
        }

        return {contentWidth, contentHeight};
    }

    Size paddingBoxSize() const {
        const Size content = contentSize();

        return {
            content.width + padding_.horizontal(),
            content.height + padding_.vertical()
        };
    }

    Size borderBoxSize() const {
        const Size paddingBox = paddingBoxSize();

        return {
            paddingBox.width + border_.horizontal(),
            paddingBox.height + border_.vertical()
        };
    }

    Size constrainedBorderBoxSize() const {
        Size result = borderBoxSize();

        if (minWidth_) {
            result.width = std::max(result.width, *minWidth_);
        }

        if (maxWidth_) {
            result.width = std::min(result.width, *maxWidth_);
        }

        if (minHeight_) {
            result.height = std::max(result.height, *minHeight_);
        }

        if (maxHeight_) {
            result.height = std::min(result.height, *maxHeight_);
        }

        return result;
    }

    Size marginBoxSize() const {
        const Size borderBox = constrainedBorderBoxSize();

        return {
            borderBox.width + margin_.horizontal(),
            borderBox.height + margin_.vertical()
        };
    }

    const Edges& padding() const {
        return padding_;
    }

    const Edges& border() const {
        return border_;
    }

    const Edges& margin() const {
        return margin_;
    }

    BoxSizing boxSizing() const {
        return boxSizing_;
    }
};

// ============================================================================
// Overflow
// ============================================================================

OverflowResult calculateOverflow(
    Size contentSize,
    Size availableSize
) {
    if (contentSize.width < 0 ||
        contentSize.height < 0 ||
        availableSize.width < 0 ||
        availableSize.height < 0) {
        throw std::invalid_argument(
            "Content and available dimensions cannot be negative."
        );
    }

    return {
        std::max(0.0, contentSize.width - availableSize.width),
        std::max(0.0, contentSize.height - availableSize.height)
    };
}

std::string overflowDescription(
    OverflowMode mode
) {
    switch (mode) {
        case OverflowMode::Visible:
            return "visible: content may extend outside the box";

        case OverflowMode::Hidden:
            return "hidden: overflowing content is clipped";

        case OverflowMode::Clip:
            return "clip: content is clipped without creating scrolling";

        case OverflowMode::Scroll:
            return "scroll: scrolling mechanism is requested";

        case OverflowMode::Auto:
            return "auto: scrolling is provided when needed";
    }

    return "unknown";
}

// ============================================================================
// Responsive width model
// ============================================================================

double responsiveWidth(
    double containerWidth,
    double percentage,
    double minimum,
    double maximum
) {
    requireNonNegative(containerWidth, "container width");
    requireNonNegative(percentage, "percentage");
    requireNonNegative(minimum, "minimum");
    requireNonNegative(maximum, "maximum");

    if (minimum > maximum) {
        throw std::invalid_argument(
            "Minimum responsive width cannot exceed maximum width."
        );
    }

    const double preferred = containerWidth * percentage;

    return std::clamp(preferred, minimum, maximum);
}

// ============================================================================
// Margin collapse demonstration
// ============================================================================

double collapsePositiveVerticalMargins(
    double first,
    double second
) {
    requireNonNegative(first, "first margin");
    requireNonNegative(second, "second margin");

    // This is a simplified representation of two adjoining positive
    // vertical margins in normal block flow.
    return std::max(first, second);
}

// ============================================================================
// Application-level component
// ============================================================================

class ProductCard {
private:
    std::string productName_;
    double viewportWidth_;
    BoxModel box_;

public:
    ProductCard(
        std::string productName,
        double viewportWidth
    )
        : productName_(std::move(productName)),
          viewportWidth_(viewportWidth),
          box_(
              {360, 220},
              {24, 24, 24, 24},
              {1, 1, 1, 1},
              {16, 16, 16, 16},
              BoxSizing::BorderBox
          ) {

        requireNonNegative(viewportWidth_, "viewport width");

        // The card cannot exceed its available viewport width.
        box_.setWidthConstraints(
            280.0,
            std::min(360.0, viewportWidth_)
        );
    }

    void printReport() const {
        const Size content = box_.contentSize();
        const Size padding = box_.paddingBoxSize();
        const Size border = box_.constrainedBorderBoxSize();
        const Size margin = box_.marginBoxSize();

        std::cout << "\nProduct card: " << productName_ << "\n";
        std::cout << "----------------------------------------\n";

        std::cout << "Content box:  "
                  << content.width << " x "
                  << content.height << " px\n";

        std::cout << "Padding box:  "
                  << padding.width << " x "
                  << padding.height << " px\n";

        std::cout << "Border box:   "
                  << border.width << " x "
                  << border.height << " px\n";

        std::cout << "Margin box:   "
                  << margin.width << " x "
                  << margin.height << " px\n";
    }
};

// ============================================================================
// Demonstrations
// ============================================================================

void demonstrateBasicBoxModel() {
    std::cout << "\n=== BASIC BOX MODEL ===\n";

    BoxModel box(
        {200, 100},
        {20, 30, 20, 30},
        {5, 5, 5, 5},
        {15, 25, 15, 25},
        BoxSizing::ContentBox
    );

    const Size content = box.contentSize();
    const Size padding = box.paddingBoxSize();
    const Size border = box.borderBoxSize();
    const Size margin = box.marginBoxSize();

    std::cout << "Content: "
              << content.width << " x "
              << content.height << "\n";

    std::cout << "Padding box: "
              << padding.width << " x "
              << padding.height << "\n";

    std::cout << "Border box: "
              << border.width << " x "
              << border.height << "\n";

    std::cout << "Margin box: "
              << margin.width << " x "
              << margin.height << "\n";
}

void demonstrateBoxSizing() {
    std::cout << "\n=== CONTENT-BOX VS BORDER-BOX ===\n";

    const Size declared{200, 100};
    const Edges padding{20, 20, 20, 20};
    const Edges border{5, 5, 5, 5};
    const Edges margin{0, 0, 0, 0};

    BoxModel contentBox(
        declared,
        padding,
        border,
        margin,
        BoxSizing::ContentBox
    );

    BoxModel borderBox(
        declared,
        padding,
        border,
        margin,
        BoxSizing::BorderBox
    );

    const Size contentBoxResult = contentBox.borderBoxSize();
    const Size borderBoxResult = borderBox.borderBoxSize();

    std::cout << "content-box border dimensions: "
              << contentBoxResult.width << " x "
              << contentBoxResult.height << "\n";

    std::cout << "border-box border dimensions:   "
              << borderBoxResult.width << " x "
              << borderBoxResult.height << "\n";

    std::cout
        << "The same declared width can therefore represent different "
        << "content areas.\n";
}

void demonstrateOverflow() {
    std::cout << "\n=== OVERFLOW ===\n";

    const Size content{800, 600};
    const Size available{500, 400};

    const OverflowResult result =
        calculateOverflow(content, available);

    std::cout << "Horizontal overflow: "
              << result.horizontal << " px\n";

    std::cout << "Vertical overflow: "
              << result.vertical << " px\n";

    for (OverflowMode mode : {
        OverflowMode::Visible,
        OverflowMode::Hidden,
        OverflowMode::Clip,
        OverflowMode::Scroll,
        OverflowMode::Auto
    }) {
        std::cout << "Mode: "
                  << overflowDescription(mode)
                  << "\n";
    }
}

void demonstrateResponsiveSizing() {
    std::cout << "\n=== RESPONSIVE SIZING ===\n";

    const std::vector<double> viewports{
        320, 480, 768, 1024, 1440, 1920
    };

    for (double viewport : viewports) {
        const double width =
            responsiveWidth(
                viewport,
                0.80,
                280,
                900
            );

        std::cout << std::fixed
                  << std::setprecision(1)
                  << "Viewport "
                  << viewport
                  << " px -> component "
                  << width
                  << " px\n";
    }
}

void demonstrateMarginCollapse() {
    std::cout << "\n=== MARGIN COLLAPSE ===\n";

    const double first = 30;
    const double second = 20;

    std::cout << "First margin:  "
              << first << " px\n";

    std::cout << "Second margin: "
              << second << " px\n";

    std::cout << "Simplified collapsed result: "
              << collapsePositiveVerticalMargins(first, second)
              << " px\n";
}

// ============================================================================
// Verification
// ============================================================================

void expectNear(
    double actual,
    double expected,
    double tolerance,
    const std::string& description
) {
    if (std::abs(actual - expected) > tolerance) {
        std::ostringstream message;

        message
            << description
            << ": expected "
            << expected
            << ", received "
            << actual;

        throw std::runtime_error(message.str());
    }
}

void runTests() {
    std::cout << "\n=== VERIFICATION TESTS ===\n";

    BoxModel contentBox(
        {200, 100},
        {20, 20, 20, 20},
        {5, 5, 5, 5},
        {0, 0, 0, 0},
        BoxSizing::ContentBox
    );

    Size contentBoxSize = contentBox.borderBoxSize();

    expectNear(
        contentBoxSize.width,
        250,
        0.001,
        "content-box width"
    );

    expectNear(
        contentBoxSize.height,
        150,
        0.001,
        "content-box height"
    );

    BoxModel borderBox(
        {200, 100},
        {20, 20, 20, 20},
        {5, 5, 5, 5},
        {0, 0, 0, 0},
        BoxSizing::BorderBox
    );

    Size borderBoxSize = borderBox.borderBoxSize();

    expectNear(
        borderBoxSize.width,
        200,
        0.001,
        "border-box width"
    );

    expectNear(
        borderBoxSize.height,
        100,
        0.001,
        "border-box height"
    );

    OverflowResult overflow =
        calculateOverflow({600, 500}, {400, 300});

    expectNear(
        overflow.horizontal,
        200,
        0.001,
        "horizontal overflow"
    );

    expectNear(
        overflow.vertical,
        200,
        0.001,
        "vertical overflow"
    );

    expectNear(
        collapsePositiveVerticalMargins(30, 20),
        30,
        0.001,
        "positive margin collapse"
    );

    std::cout << "All tests passed.\n";
}

// ============================================================================
// Error handling demonstration
// ============================================================================

void demonstrateFailureConditions() {
    std::cout << "\n=== FAILURE CONDITIONS ===\n";

    try {
        BoxModel invalid(
            {100, 100},
            {60, 60, 60, 60},
            {10, 10, 10, 10},
            {0, 0, 0, 0},
            BoxSizing::BorderBox
        );

        // The declared 100px width cannot contain 120px padding plus borders.
        invalid.contentSize();

        std::cout << "Unexpected: invalid box accepted.\n";
    }
    catch (const std::exception& error) {
        std::cout << "Handled invalid border-box: "
                  << error.what()
                  << "\n";
    }

    try {
        BoxModel valid(
            {300, 150},
            {20, 20, 20, 20},
            {1, 1, 1, 1},
            {-10, 10, -10, 10},
            BoxSizing::BorderBox
        );

        // Negative margins are legal, so construction succeeds.
        Size result = valid.marginBoxSize();

        std::cout << "Negative-margin example: "
                  << result.width
                  << " x "
                  << result.height
                  << " px\n";
    }
    catch (const std::exception& error) {
        std::cout << "Unexpected failure: "
                  << error.what()
                  << "\n";
    }
}

// ============================================================================
// Main
// ============================================================================

} // namespace cssbox

int main() {
    try {
        std::cout
            << "CSS Box Model Technical Case Study\n"
            << "C++17 implementation\n";

        cssbox::demonstrateBasicBoxModel();
        cssbox::demonstrateBoxSizing();
        cssbox::demonstrateOverflow();
        cssbox::demonstrateResponsiveSizing();
        cssbox::demonstrateMarginCollapse();

        std::cout << "\n=== INDUSTRY-STYLE COMPONENT ===\n";

        cssbox::ProductCard card(
            "Technical Product Card",
            768
        );

        card.printReport();

        cssbox::demonstrateFailureConditions();
        cssbox::runTests();

        std::cout << "\nProgram completed successfully.\n";
    }
    catch (const std::exception& error) {
        std::cerr
            << "Fatal error: "
            << error.what()
            << "\n";

        return 1;
    }

    return 0;
}
