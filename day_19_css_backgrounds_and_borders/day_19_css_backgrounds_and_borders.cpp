/*
 * CSS Backgrounds and Borders
 * ===========================
 *
 * Industry-style C++ case study:
 * A theme and component rendering engine that models the visual configuration
 * commonly used by a web application's design system.
 *
 * The program demonstrates:
 * - typed representation of CSS visual properties
 * - validation
 * - background layers
 * - gradients
 * - borders
 * - radius
 * - shadows
 * - clipping
 * - design tokens
 * - component composition
 * - serialization to CSS
 * - deterministic output
 * - error handling
 * - complexity considerations
 *
 * Compile:
 *   g++ -std=c++17 -O2 css_backgrounds_borders.cpp -o css_demo
 *
 * Run:
 *   ./css_demo
 */

#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <regex>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>


// ============================================================================
// 1. BASIC UTILITIES
// ============================================================================

std::string trim(const std::string& value) {
    const std::string whitespace = " \t\n\r";
    const auto first = value.find_first_not_of(whitespace);

    if (first == std::string::npos) {
        return "";
    }

    const auto last = value.find_last_not_of(whitespace);
    return value.substr(first, last - first + 1);
}

bool isPositive(double value) {
    return std::isfinite(value) && value > 0.0;
}

std::string indent(const std::string& text, const std::string& prefix) {
    std::stringstream input(text);
    std::stringstream output;
    std::string line;

    while (std::getline(input, line)) {
        output << prefix << line << '\n';
    }

    std::string result = output.str();

    if (!result.empty()) {
        result.pop_back();
    }

    return result;
}


// ============================================================================
// 2. RGB COLOR MODEL
// ============================================================================

struct RGBColor {
    int red;
    int green;
    int blue;
    double alpha = 1.0;

    RGBColor(int red, int green, int blue, double alpha = 1.0)
        : red(red), green(green), blue(blue), alpha(alpha) {
        validate();
    }

    void validate() const {
        if (red < 0 || red > 255 ||
            green < 0 || green > 255 ||
            blue < 0 || blue > 255) {
            throw std::invalid_argument(
                "RGB channels must be between 0 and 255."
            );
        }

        if (alpha < 0.0 || alpha > 1.0) {
            throw std::invalid_argument(
                "Alpha must be between 0 and 1."
            );
        }
    }

    std::string toCSS() const {
        std::ostringstream output;

        output << "rgb("
               << red << ' '
               << green << ' '
               << blue;

        if (alpha < 1.0) {
            output << " / "
                   << std::fixed
                   << std::setprecision(2)
                   << alpha;
        }

        output << ')';
        return output.str();
    }
};


// ============================================================================
// 3. GRADIENT COLOR INTERPOLATION
// ============================================================================

RGBColor interpolate(
    const RGBColor& start,
    const RGBColor& end,
    double progress
) {
    if (progress < 0.0 || progress > 1.0) {
        throw std::out_of_range(
            "Gradient progress must be between 0 and 1."
        );
    }

    const auto interpolateChannel = [progress](int a, int b) {
        return static_cast<int>(
            std::lround(
                a + (b - a) * progress
            )
        );
    };

    const double alpha =
        start.alpha + (end.alpha - start.alpha) * progress;

    return RGBColor(
        interpolateChannel(start.red, end.red),
        interpolateChannel(start.green, end.green),
        interpolateChannel(start.blue, end.blue),
        alpha
    );
}


// ============================================================================
// 4. BACKGROUND LAYERS
// ============================================================================

enum class BackgroundLayerType {
    Color,
    Image,
    LinearGradient,
    RadialGradient,
    ConicGradient
};

std::string layerTypeName(BackgroundLayerType type) {
    switch (type) {
        case BackgroundLayerType::Color:
            return "color";
        case BackgroundLayerType::Image:
            return "image";
        case BackgroundLayerType::LinearGradient:
            return "linear-gradient";
        case BackgroundLayerType::RadialGradient:
            return "radial-gradient";
        case BackgroundLayerType::ConicGradient:
            return "conic-gradient";
    }

    throw std::logic_error("Unknown background layer type.");
}


struct BackgroundLayer {
    BackgroundLayerType type;
    std::string value;
    std::string position = "center";
    std::string size = "auto";
    std::string repeat = "no-repeat";
    std::string attachment = "scroll";

    std::string toCSS() const {
        std::ostringstream output;

        switch (type) {
            case BackgroundLayerType::Color:
                output << value;
                break;

            case BackgroundLayerType::Image:
                output << "url('" << value << "')";
                break;

            case BackgroundLayerType::LinearGradient:
            case BackgroundLayerType::RadialGradient:
            case BackgroundLayerType::ConicGradient:
                output << value;
                break;
        }

        if (type != BackgroundLayerType::Color) {
            output << ' '
                   << position
                   << " / "
                   << size
                   << ' '
                   << repeat;
        }

        return output.str();
    }
};


// ============================================================================
// 5. BORDER MODEL
// ============================================================================

enum class BorderStyle {
    None,
    Solid,
    Dashed,
    Dotted,
    Double,
    Groove,
    Ridge,
    Inset,
    Outset
};

std::string borderStyleName(BorderStyle style) {
    switch (style) {
        case BorderStyle::None:
            return "none";
        case BorderStyle::Solid:
            return "solid";
        case BorderStyle::Dashed:
            return "dashed";
        case BorderStyle::Dotted:
            return "dotted";
        case BorderStyle::Double:
            return "double";
        case BorderStyle::Groove:
            return "groove";
        case BorderStyle::Ridge:
            return "ridge";
        case BorderStyle::Inset:
            return "inset";
        case BorderStyle::Outset:
            return "outset";
    }

    throw std::logic_error("Unknown border style.");
}


struct Border {
    double width;
    BorderStyle style;
    RGBColor color;

    Border(
        double width,
        BorderStyle style,
        RGBColor color
    )
        : width(width),
          style(style),
          color(std::move(color)) {
        if (width < 0.0 || !std::isfinite(width)) {
            throw std::invalid_argument(
                "Border width must be non-negative and finite."
            );
        }
    }

    std::string toCSS() const {
        std::ostringstream output;

        output << std::fixed
               << std::setprecision(1)
               << width
               << "px "
               << borderStyleName(style)
               << ' '
               << color.toCSS();

        return output.str();
    }
};


// ============================================================================
// 6. BORDER RADIUS
// ============================================================================

struct BorderRadius {
    std::string topLeft;
    std::string topRight;
    std::string bottomRight;
    std::string bottomLeft;

    explicit BorderRadius(std::string all)
        : topLeft(all),
          topRight(all),
          bottomRight(all),
          bottomLeft(all) {}

    BorderRadius(
        std::string topLeft,
        std::string topRight,
        std::string bottomRight,
        std::string bottomLeft
    )
        : topLeft(std::move(topLeft)),
          topRight(std::move(topRight)),
          bottomRight(std::move(bottomRight)),
          bottomLeft(std::move(bottomLeft)) {}

    std::string toCSS() const {
        return topLeft + " " +
               topRight + " " +
               bottomRight + " " +
               bottomLeft;
    }
};


// ============================================================================
// 7. BOX SHADOW
// ============================================================================

struct BoxShadow {
    double offsetX;
    double offsetY;
    double blur;
    double spread;
    RGBColor color;
    bool inset;

    BoxShadow(
        double offsetX,
        double offsetY,
        double blur,
        double spread,
        RGBColor color,
        bool inset = false
    )
        : offsetX(offsetX),
          offsetY(offsetY),
          blur(blur),
          spread(spread),
          color(std::move(color)),
          inset(inset) {
        if (blur < 0.0) {
            throw std::invalid_argument(
                "Shadow blur cannot be negative."
            );
        }
    }

    std::string toCSS() const {
        std::ostringstream output;

        if (inset) {
            output << "inset ";
        }

        output << offsetX << "px "
               << offsetY << "px "
               << blur << "px "
               << spread << "px "
               << color.toCSS();

        return output.str();
    }
};


// ============================================================================
// 8. CLIPPING MODEL
// ============================================================================

enum class BackgroundClip {
    BorderBox,
    PaddingBox,
    ContentBox,
    Text
};

std::string backgroundClipName(BackgroundClip clip) {
    switch (clip) {
        case BackgroundClip::BorderBox:
            return "border-box";
        case BackgroundClip::PaddingBox:
            return "padding-box";
        case BackgroundClip::ContentBox:
            return "content-box";
        case BackgroundClip::Text:
            return "text";
    }

    throw std::logic_error("Unknown background clip.");
}


// ============================================================================
// 9. DESIGN TOKENS
// ============================================================================

struct DesignTokens {
    std::string surface = "#0f172a";
    std::string raisedSurface = "#1e293b";
    std::string border = "#334155";
    std::string accent = "#38bdf8";
    std::string radiusMedium = "16px";
    std::string radiusLarge = "24px";
    std::string softShadow =
        "0 12px 32px rgb(0 0 0 / 0.22)";

    std::string toCSS() const {
        std::ostringstream output;

        output
            << ":root {\n"
            << "  --surface: " << surface << ";\n"
            << "  --surface-raised: " << raisedSurface << ";\n"
            << "  --border: " << border << ";\n"
            << "  --accent: " << accent << ";\n"
            << "  --radius-medium: " << radiusMedium << ";\n"
            << "  --radius-large: " << radiusLarge << ";\n"
            << "  --shadow-soft: " << softShadow << ";\n"
            << "}";

        return output.str();
    }
};


// ============================================================================
// 10. COMPONENT MODEL
// ============================================================================

class UIComponent {
private:
    std::string selector;
    std::map<std::string, std::string> declarations;
    std::vector<UIComponent> children;

public:
    explicit UIComponent(std::string selector)
        : selector(std::move(selector)) {
        if (this->selector.empty()) {
            throw std::invalid_argument(
                "Component selector cannot be empty."
            );
        }
    }

    UIComponent& property(
        const std::string& name,
        const std::string& value
    ) {
        if (name.empty()) {
            throw std::invalid_argument(
                "CSS property name cannot be empty."
            );
        }

        declarations[name] = value;
        return *this;
    }

    UIComponent& child(UIComponent component) {
        children.push_back(std::move(component));
        return children.back();
    }

    std::string toCSS() const {
        std::ostringstream output;

        output << selector << " {\n";

        for (const auto& [property, value] : declarations) {
            output << "  "
                   << property
                   << ": "
                   << value
                   << ";\n";
        }

        output << "}";

        for (const auto& nested : children) {
            output << "\n\n"
                   << nested.toCSS();
        }

        return output.str();
    }
};


// ============================================================================
// 11. CARD SYSTEM
// ============================================================================

UIComponent createProductCard() {
    UIComponent card(".product-card");

    card
        .property("position", "relative")
        .property("overflow", "hidden")
        .property("background", "#0f172a")
        .property("border", "1px solid #334155")
        .property("border-radius", "20px")
        .property(
            "box-shadow",
            "0 16px 40px rgb(0 0 0 / 0.22)"
        );

    UIComponent media(".product-card__media");

    media
        .property("height", "220px")
        .property(
            "background",
            "url('product.jpg') center / cover no-repeat"
        )
        .property("border-radius", "20px 20px 0 0");

    UIComponent content(".product-card__content");

    content
        .property("position", "relative")
        .property("padding", "24px")
        .property(
            "background",
            "rgb(15 23 42 / 0.94)"
        )
        .property(
            "border-top",
            "1px solid rgb(148 163 184 / 0.18)"
        );

    UIComponent button(".product-card__button");

    button
        .property(
            "background",
            "linear-gradient(135deg, #06b6d4, #7c3aed)"
        )
        .property(
            "border",
            "1px solid rgb(255 255 255 / 0.14)"
        )
        .property("border-radius", "9999px")
        .property(
            "box-shadow",
            "0 8px 20px rgb(6 182 212 / 0.22)"
        )
        .property("color", "white")
        .property("padding", "12px 20px");

    UIComponent focus(".product-card__button:focus-visible");

    focus
        .property("outline", "3px solid white")
        .property("outline-offset", "4px");

    card.child(std::move(media));
    card.child(std::move(content));
    card.child(std::move(button));
    card.child(std::move(focus));

    return card;
}


// ============================================================================
// 12. BACKGROUND SIZE CALCULATOR
// ============================================================================

struct Dimensions {
    double width;
    double height;
};


struct BackgroundSizeResult {
    Dimensions cover;
    Dimensions contain;
};


BackgroundSizeResult calculateBackgroundSize(
    double containerWidth,
    double containerHeight,
    double imageWidth,
    double imageHeight
) {
    if (!isPositive(containerWidth) ||
        !isPositive(containerHeight) ||
        !isPositive(imageWidth) ||
        !isPositive(imageHeight)) {
        throw std::invalid_argument(
            "All dimensions must be positive."
        );
    }

    const double coverScale = std::max(
        containerWidth / imageWidth,
        containerHeight / imageHeight
    );

    const double containScale = std::min(
        containerWidth / imageWidth,
        containerHeight / imageHeight
    );

    return {
        {
            imageWidth * coverScale,
            imageHeight * coverScale
        },
        {
            imageWidth * containScale,
            imageHeight * containScale
        }
    };
}


// ============================================================================
// 13. ACCESSIBILITY AUDIT
// ============================================================================

struct AccessibilityAudit {
    bool visibleFocus;
    bool sufficientTextContrast;
    bool essentialInformationInHTML;
    bool reasonableShadowUsage;
    bool mobileBackgroundTested;

    std::vector<std::string> issues() const {
        std::vector<std::string> results;

        if (!visibleFocus) {
            results.emplace_back(
                "Provide a visible keyboard focus indicator."
            );
        }

        if (!sufficientTextContrast) {
            results.emplace_back(
                "Verify text contrast against imagery and gradients."
            );
        }

        if (!essentialInformationInHTML) {
            results.emplace_back(
                "Move essential information out of CSS backgrounds."
            );
        }

        if (!reasonableShadowUsage) {
            results.emplace_back(
                "Reduce excessive or repeated large shadows."
            );
        }

        if (!mobileBackgroundTested) {
            results.emplace_back(
                "Test background behavior on mobile viewport sizes."
            );
        }

        return results;
    }
};


// ============================================================================
// 14. SECURITY VALIDATION
// ============================================================================

bool isSafeImageSource(const std::string& source) {
    const std::string normalized = trim(source);

    if (normalized.empty()) {
        return false;
    }

    std::string lowercase = normalized;

    std::transform(
        lowercase.begin(),
        lowercase.end(),
        lowercase.begin(),
        [](unsigned char character) {
            return static_cast<char>(std::tolower(character));
        }
    );

    if (lowercase.find("javascript:") != std::string::npos) {
        return false;
    }

    return lowercase.rfind("https://", 0) == 0 ||
           lowercase.rfind("http://", 0) == 0 ||
           lowercase.rfind("/", 0) == 0 ||
           lowercase.rfind("./", 0) == 0 ||
           lowercase.rfind("../", 0) == 0;
}


// ============================================================================
// 15. PERFORMANCE MODEL
// ============================================================================

struct VisualComplexity {
    int backgroundLayers;
    int shadowLayers;
    int gradientLayers;
    int largeBlurCount;

    int score() const {
        return backgroundLayers +
               shadowLayers * 2 +
               gradientLayers +
               largeBlurCount * 3;
    }
};


// ============================================================================
// 16. TEST HELPERS
// ============================================================================

void require(bool condition, const std::string& message) {
    if (!condition) {
        throw std::runtime_error(
            "Test failed: " + message
        );
    }
}

void runTests() {
    std::cout << "\n--- Running C++ tests ---\n";

    RGBColor color(255, 255, 255);
    require(
        color.toCSS() == "rgb(255 255 255)",
        "RGB CSS serialization"
    );

    RGBColor midpoint = interpolate(
        RGBColor(0, 0, 0),
        RGBColor(100, 200, 50),
        0.5
    );

    require(
        midpoint.red == 50 &&
        midpoint.green == 100 &&
        midpoint.blue == 25,
        "color interpolation"
    );

    BackgroundSizeResult dimensions =
        calculateBackgroundSize(
            100,
            100,
            200,
            100
        );

    require(
        std::abs(dimensions.cover.width - 200.0) < 0.001,
        "cover width"
    );

    require(
        std::abs(dimensions.cover.height - 100.0) < 0.001,
        "cover height"
    );

    require(
        std::abs(dimensions.contain.width - 100.0) < 0.001,
        "contain width"
    );

    require(
        std::abs(dimensions.contain.height - 50.0) < 0.001,
        "contain height"
    );

    Border border(
        2.0,
        BorderStyle::Solid,
        RGBColor(51, 65, 85)
    );

    require(
        border.toCSS().find("solid") != std::string::npos,
        "border serialization"
    );

    BoxShadow boxShadow(
        0,
        8,
        24,
        0,
        RGBColor(0, 0, 0, 0.2)
    );

    require(
        boxShadow.toCSS().find("24") != std::string::npos,
        "shadow serialization"
    );

    require(
        isSafeImageSource("images/hero.jpg"),
        "safe relative image"
    );

    require(
        !isSafeImageSource("javascript:alert(1)"),
        "unsafe URL rejection"
    );

    UIComponent component = createProductCard();

    const std::string css = component.toCSS();

    require(
        css.find("border-radius") != std::string::npos,
        "component radius"
    );

    require(
        css.find("box-shadow") != std::string::npos,
        "component shadow"
    );

    std::cout << "All C++ tests passed.\n";
}


// ============================================================================
// 17. MAIN CASE STUDY
// ============================================================================

int main() {
    try {
        std::cout << std::fixed
                  << std::setprecision(2);

        std::cout
            << "\nCASE STUDY: DESIGN SYSTEM COMPONENT RENDERER\n"
            << "---------------------------------------------\n";

        std::cout
            << "\nProblem:\n"
            << "A web application needs a consistent visual language "
            << "for cards, dashboards, media surfaces, and interactive "
            << "controls. The system must represent backgrounds, gradients, "
            << "borders, rounded corners, shadows, clipping, and focus "
            << "states as reusable design tokens and components.\n";

        // --------------------------------------------------------------------
        // Design tokens
        // --------------------------------------------------------------------

        DesignTokens tokens;

        std::cout << "\n--- Design tokens ---\n";
        std::cout << tokens.toCSS() << "\n";

        // --------------------------------------------------------------------
        // Background layers
        // --------------------------------------------------------------------

        BackgroundLayer gradient{
            BackgroundLayerType::LinearGradient,
            "linear-gradient(135deg, #06b6d4, #7c3aed)",
            "center",
            "cover",
            "no-repeat",
            "scroll"
        };

        BackgroundLayer image{
            BackgroundLayerType::Image,
            "hero.jpg",
            "center",
            "cover",
            "no-repeat",
            "scroll"
        };

        std::cout << "\n--- Background layers ---\n";
        std::cout << "Gradient: "
                  << gradient.toCSS()
                  << "\n";
        std::cout << "Image:    "
                  << image.toCSS()
                  << "\n";

        std::cout
            << "\nThe gradient can be placed before the image so that "
            << "the gradient visually overlays the image.\n";

        // --------------------------------------------------------------------
        // Border
        // --------------------------------------------------------------------

        Border border(
            1.0,
            BorderStyle::Solid,
            RGBColor(51, 65, 85)
        );

        std::cout << "\n--- Border ---\n";
        std::cout << "border: "
                  << border.toCSS()
                  << ";\n";

        // --------------------------------------------------------------------
        // Radius
        // --------------------------------------------------------------------

        BorderRadius radius("20px");

        std::cout << "\n--- Border radius ---\n";
        std::cout
            << "border-radius: "
            << radius.toCSS()
            << ";\n";

        // --------------------------------------------------------------------
        // Shadow
        // --------------------------------------------------------------------

        BoxShadow shadow(
            0,
            16,
            40,
            0,
            RGBColor(0, 0, 0, 0.22)
        );

        std::cout << "\n--- Box shadow ---\n";
        std::cout
            << "box-shadow: "
            << shadow.toCSS()
            << ";\n";

        // --------------------------------------------------------------------
        // Clipping
        // --------------------------------------------------------------------

        std::cout << "\n--- Background clipping ---\n";
        std::cout
            << "background-clip: "
            << backgroundClipName(BackgroundClip::PaddingBox)
            << ";\n";

        std::cout
            << "A padding-box clip prevents the element's own background "
            << "from painting underneath the border while retaining it "
            << "through the padding region.\n";

        // --------------------------------------------------------------------
        // Background sizing analysis
        // --------------------------------------------------------------------

        BackgroundSizeResult sizing =
            calculateBackgroundSize(
                1200,
                500,
                1600,
                900
            );

        std::cout << "\n--- Background sizing analysis ---\n";
        std::cout
            << "cover  = "
            << sizing.cover.width
            << " x "
            << sizing.cover.height
            << " px\n";

        std::cout
            << "contain = "
            << sizing.contain.width
            << " x "
            << sizing.contain.height
            << " px\n";

        std::cout
            << "cover guarantees coverage of the container but may crop "
            << "parts of the source image. contain preserves the entire "
            << "image but may leave empty space.\n";

        // --------------------------------------------------------------------
        // Gradient interpolation
        // --------------------------------------------------------------------

        RGBColor gradientStart(14, 165, 233);
        RGBColor gradientEnd(139, 92, 246);

        std::cout << "\n--- Gradient interpolation ---\n";

        for (double progress : {0.0, 0.25, 0.5, 0.75, 1.0}) {
            RGBColor color = interpolate(
                gradientStart,
                gradientEnd,
                progress
            );

            std::cout
                << "t="
                << progress
                << " -> "
                << color.toCSS()
                << "\n";
        }

        // --------------------------------------------------------------------
        // Accessibility
        // --------------------------------------------------------------------

        AccessibilityAudit audit{
            true,
            true,
            true,
            true,
            true
        };

        std::cout << "\n--- Accessibility audit ---\n";

        const auto accessibilityIssues = audit.issues();

        if (accessibilityIssues.empty()) {
            std::cout
                << "No issues detected by the basic audit.\n";
        } else {
            for (const auto& issue : accessibilityIssues) {
                std::cout << "- "
                          << issue
                          << "\n";
            }
        }

        // --------------------------------------------------------------------
        // Security
        // --------------------------------------------------------------------

        std::cout << "\n--- Image source validation ---\n";

        const std::vector<std::string> sources{
            "images/hero.jpg",
            "https://example.com/image.webp",
            "javascript:alert(1)",
            ""
        };

        for (const auto& source : sources) {
            std::cout
                << std::setw(38)
                << std::left
                << (source.empty() ? "<empty>" : source)
                << " -> "
                << (
                    isSafeImageSource(source)
                        ? "accepted"
                        : "rejected"
                )
                << "\n";
        }

        // --------------------------------------------------------------------
        // Component
        // --------------------------------------------------------------------

        UIComponent card = createProductCard();

        std::cout
            << "\n--- Generated product-card component ---\n";
        std::cout
            << card.toCSS()
            << "\n";

        // --------------------------------------------------------------------
        // Complexity
        // --------------------------------------------------------------------

        VisualComplexity complexity{
            2,
            2,
            2,
            1
        };

        std::cout
            << "\n--- Visual complexity estimate ---\n";
        std::cout
            << "Conceptual rendering score: "
            << complexity.score()
            << "\n";

        std::cout
            << "This score is not a browser benchmark. It is a simple "
            << "engineering heuristic illustrating why many layers, large "
            << "blur effects, and repeated shadows deserve performance "
            << "testing.\n";

        // --------------------------------------------------------------------
        // Unit tests
        // --------------------------------------------------------------------

        runTests();

        // --------------------------------------------------------------------
        // Production rules
        // --------------------------------------------------------------------

        const std::vector<std::string> productionRules{
            "Keep essential information in semantic HTML.",
            "Check contrast when text appears over images or gradients.",
            "Keep keyboard focus visible.",
            "Optimize large background images.",
            "Test background-position with cover at different aspect ratios.",
            "Avoid unnecessary background-attachment: fixed usage.",
            "Use design tokens for repeated colors, radii, and shadows.",
            "Keep visual effects restrained when many elements appear together.",
            "Validate externally supplied image URLs.",
            "Test zoom, keyboard navigation, and narrow mobile layouts."
        };

        std::cout
            << "\n--- Production checklist ---\n";

        for (std::size_t index = 0;
             index < productionRules.size();
             ++index) {
            std::cout
                << std::setw(2)
                << (index + 1)
                << ". "
                << productionRules[index]
                << "\n";
        }

        std::cout
            << "\nCase study completed successfully.\n";

        return 0;
    }
    catch (const std::exception& error) {
        std::cerr
            << "\nFatal error: "
            << error.what()
            << "\n";

        return 1;
    }
}
