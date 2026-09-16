/*
 * CSS Colors and Units: Responsive Dashboard Case Study
 * ======================================================
 *
 * Modern C++17 program.
 *
 * This program models a small responsive dashboard design system and
 * demonstrates the mathematics and engineering decisions behind:
 *
 *   - HEX colors
 *   - RGB / RGBA
 *   - HSL / HSLA
 *   - Alpha compositing
 *   - Color contrast
 *   - px
 *   - %
 *   - em
 *   - rem
 *   - vh
 *   - vw
 *   - vmin
 *   - vmax
 *   - fluid sizing
 *   - design tokens
 *   - responsive components
 *   - validation
 *   - error handling
 *   - complexity and trade-offs
 *
 * The program does not render CSS. It acts as a design-system calculation
 * engine that generates CSS values and evaluates responsive behavior.
 *
 * Compile:
 *   g++ -std=c++17 -O2 -Wall -Wextra -pedantic main.cpp -o css_units
 *
 * Run:
 *   ./css_units
 */

#include <algorithm>
#include <cassert>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <sstream>
#include <stdexcept>
#include <string>
#include <tuple>
#include <utility>
#include <vector>


// -----------------------------------------------------------------------------
// 1. GENERAL UTILITIES
// -----------------------------------------------------------------------------

void printSection(const std::string& title) {
    std::cout << "\n"
              << std::string(78, '=')
              << "\n"
              << title
              << "\n"
              << std::string(78, '=')
              << "\n";
}

double clampValue(double value, double minimum, double maximum) {
    return std::max(minimum, std::min(value, maximum));
}

std::string formatNumber(double value) {
    std::ostringstream output;
    output << std::fixed << std::setprecision(2) << value;

    std::string result = output.str();

    while (!result.empty() && result.back() == '0') {
        result.pop_back();
    }

    if (!result.empty() && result.back() == '.') {
        result.pop_back();
    }

    return result;
}


// -----------------------------------------------------------------------------
// 2. COLOR MODEL
// -----------------------------------------------------------------------------

class Color {
public:
    int red;
    int green;
    int blue;
    double alpha;

    Color(
        int redValue,
        int greenValue,
        int blueValue,
        double alphaValue = 1.0
    )
        : red(redValue),
          green(greenValue),
          blue(blueValue),
          alpha(alphaValue) {
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

        if (!std::isfinite(alpha) || alpha < 0.0 || alpha > 1.0) {
            throw std::invalid_argument(
                "Alpha must be between 0 and 1."
            );
        }
    }

    static int hexDigit(char character) {
        if (character >= '0' && character <= '9') {
            return character - '0';
        }

        if (character >= 'a' && character <= 'f') {
            return character - 'a' + 10;
        }

        if (character >= 'A' && character <= 'F') {
            return character - 'A' + 10;
        }

        throw std::invalid_argument(
            "Invalid hexadecimal digit."
        );
    }

    static int byteFromHex(
        char first,
        char second
    ) {
        return hexDigit(first) * 16 + hexDigit(second);
    }

    static Color fromHex(std::string value) {
        if (!value.empty() && value.front() == '#') {
            value.erase(value.begin());
        }

        if (value.size() == 3 || value.size() == 4) {
            std::string expanded;

            for (char character : value) {
                expanded += character;
                expanded += character;
            }

            value = expanded;
        }

        if (value.size() != 6 && value.size() != 8) {
            throw std::invalid_argument(
                "HEX must contain 3, 4, 6, or 8 digits."
            );
        }

        int red = byteFromHex(value[0], value[1]);
        int green = byteFromHex(value[2], value[3]);
        int blue = byteFromHex(value[4], value[5]);

        double alpha = 1.0;

        if (value.size() == 8) {
            alpha =
                byteFromHex(value[6], value[7]) / 255.0;
        }

        return Color(red, green, blue, alpha);
    }

    std::string toHex() const {
        static const char* digits = "0123456789abcdef";

        auto byteToHex = [&](int value) {
            std::string result;
            result += digits[(value >> 4) & 0xF];
            result += digits[value & 0xF];
            return result;
        };

        std::string result = "#";
        result += byteToHex(red);
        result += byteToHex(green);
        result += byteToHex(blue);

        if (alpha < 1.0) {
            int alphaByte = static_cast<int>(
                std::round(alpha * 255.0)
            );

            result += byteToHex(alphaByte);
        }

        return result;
    }

    std::string toRgbCss() const {
        std::ostringstream output;

        output << "rgb("
               << red << " "
               << green << " "
               << blue;

        if (alpha < 1.0) {
            output << " / "
                   << formatNumber(alpha);
        }

        output << ")";

        return output.str();
    }
};


// -----------------------------------------------------------------------------
// 3. HSL MODEL
// -----------------------------------------------------------------------------

struct Hsl {
    double hue;
    double saturation;
    double lightness;
    double alpha;
};

Hsl rgbToHsl(const Color& color) {
    double red = color.red / 255.0;
    double green = color.green / 255.0;
    double blue = color.blue / 255.0;

    double maximum = std::max({red, green, blue});
    double minimum = std::min({red, green, blue});
    double difference = maximum - minimum;

    double lightness = (maximum + minimum) / 2.0;

    double hue = 0.0;
    double saturation = 0.0;

    if (difference != 0.0) {
        saturation =
            difference /
            (1.0 - std::abs(2.0 * lightness - 1.0));

        if (maximum == red) {
            hue =
                60.0 *
                std::fmod(
                    (green - blue) / difference,
                    6.0
                );
        } else if (maximum == green) {
            hue =
                60.0 *
                (((blue - red) / difference) + 2.0);
        } else {
            hue =
                60.0 *
                (((red - green) / difference) + 4.0);
        }
    }

    if (hue < 0.0) {
        hue += 360.0;
    }

    return {
        std::fmod(hue, 360.0),
        saturation * 100.0,
        lightness * 100.0,
        color.alpha
    };
}

Color hslToRgb(
    double hue,
    double saturation,
    double lightness,
    double alpha = 1.0
) {
    if (!std::isfinite(hue)) {
        throw std::invalid_argument(
            "Hue must be finite."
        );
    }

    if (saturation < 0.0 || saturation > 100.0) {
        throw std::invalid_argument(
            "Saturation must be between 0 and 100."
        );
    }

    if (lightness < 0.0 || lightness > 100.0) {
        throw std::invalid_argument(
            "Lightness must be between 0 and 100."
        );
    }

    hue = std::fmod(hue, 360.0);

    if (hue < 0.0) {
        hue += 360.0;
    }

    saturation /= 100.0;
    lightness /= 100.0;

    double chroma =
        (1.0 - std::abs(2.0 * lightness - 1.0))
        * saturation;

    double intermediate =
        chroma *
        (1.0 - std::abs(
            std::fmod(hue / 60.0, 2.0) - 1.0
        ));

    double match =
        lightness - chroma / 2.0;

    double r1 = 0.0;
    double g1 = 0.0;
    double b1 = 0.0;

    if (hue < 60.0) {
        r1 = chroma;
        g1 = intermediate;
    } else if (hue < 120.0) {
        r1 = intermediate;
        g1 = chroma;
    } else if (hue < 180.0) {
        g1 = chroma;
        b1 = intermediate;
    } else if (hue < 240.0) {
        g1 = intermediate;
        b1 = chroma;
    } else if (hue < 300.0) {
        r1 = intermediate;
        b1 = chroma;
    } else {
        r1 = chroma;
        b1 = intermediate;
    }

    return Color(
        static_cast<int>(std::round((r1 + match) * 255.0)),
        static_cast<int>(std::round((g1 + match) * 255.0)),
        static_cast<int>(std::round((b1 + match) * 255.0)),
        alpha
    );
}

std::string toHslCss(const Color& color) {
    Hsl hsl = rgbToHsl(color);

    std::ostringstream output;

    output << "hsl("
           << formatNumber(hsl.hue)
           << " "
           << formatNumber(hsl.saturation)
           << "% "
           << formatNumber(hsl.lightness)
           << "%";

    if (color.alpha < 1.0) {
        output << " / "
               << formatNumber(color.alpha);
    }

    output << ")";

    return output.str();
}


// -----------------------------------------------------------------------------
// 4. ALPHA COMPOSITING
// -----------------------------------------------------------------------------

int compositeChannel(
    int foreground,
    int background,
    double alpha
) {
    return static_cast<int>(
        std::round(
            foreground * alpha +
            background * (1.0 - alpha)
        )
    );
}

Color alphaComposite(
    const Color& foreground,
    const Color& background
) {
    Color foregroundOpaque(
        foreground.red,
        foreground.green,
        foreground.blue
    );

    return Color(
        compositeChannel(
            foreground.red,
            background.red,
            foreground.alpha
        ),
        compositeChannel(
            foreground.green,
            background.green,
            foreground.alpha
        ),
        compositeChannel(
            foreground.blue,
            background.blue,
            foreground.alpha
        )
    );
}


// -----------------------------------------------------------------------------
// 5. CONTRAST CALCULATION
// -----------------------------------------------------------------------------

double srgbChannelToLinear(int channel) {
    double normalized =
        channel / 255.0;

    if (normalized <= 0.04045) {
        return normalized / 12.92;
    }

    return std::pow(
        (normalized + 0.055) / 1.055,
        2.4
    );
}

double relativeLuminance(const Color& color) {
    double red =
        srgbChannelToLinear(color.red);

    double green =
        srgbChannelToLinear(color.green);

    double blue =
        srgbChannelToLinear(color.blue);

    return (
        0.2126 * red +
        0.7152 * green +
        0.0722 * blue
    );
}

double contrastRatio(
    const Color& first,
    const Color& second
) {
    double firstLuminance =
        relativeLuminance(first);

    double secondLuminance =
        relativeLuminance(second);

    double lighter =
        std::max(
            firstLuminance,
            secondLuminance
        );

    double darker =
        std::min(
            firstLuminance,
            secondLuminance
        );

    return (
        (lighter + 0.05) /
        (darker + 0.05)
    );
}


// -----------------------------------------------------------------------------
// 6. COLOR TRANSFORMATIONS
// -----------------------------------------------------------------------------

Color adjustLightness(
    const Color& color,
    double amount
) {
    Hsl hsl = rgbToHsl(color);

    double adjusted =
        clampValue(
            hsl.lightness + amount,
            0.0,
            100.0
        );

    return hslToRgb(
        hsl.hue,
        hsl.saturation,
        adjusted,
        color.alpha
    );
}


// -----------------------------------------------------------------------------
// 7. CSS UNIT SYSTEM
// -----------------------------------------------------------------------------

enum class Unit {
    Px,
    Percent,
    Em,
    Rem,
    Vh,
    Vw,
    Vmin,
    Vmax
};

std::string unitName(Unit unit) {
    switch (unit) {
        case Unit::Px:
            return "px";
        case Unit::Percent:
            return "%";
        case Unit::Em:
            return "em";
        case Unit::Rem:
            return "rem";
        case Unit::Vh:
            return "vh";
        case Unit::Vw:
            return "vw";
        case Unit::Vmin:
            return "vmin";
        case Unit::Vmax:
            return "vmax";
    }

    throw std::logic_error(
        "Unknown CSS unit."
    );
}

std::string cssValue(
    double value,
    Unit unit
) {
    return formatNumber(value) + unitName(unit);
}


// -----------------------------------------------------------------------------
// 8. VIEWPORT MODEL
// -----------------------------------------------------------------------------

class Viewport {
public:
    double width;
    double height;

    Viewport(double widthValue, double heightValue)
        : width(widthValue),
          height(heightValue) {
        if (width <= 0.0 || height <= 0.0) {
            throw std::invalid_argument(
                "Viewport dimensions must be positive."
            );
        }
    }

    double vh(double value) const {
        return height * value / 100.0;
    }

    double vw(double value) const {
        return width * value / 100.0;
    }

    double vmin(double value) const {
        return std::min(width, height)
               * value / 100.0;
    }

    double vmax(double value) const {
        return std::max(width, height)
               * value / 100.0;
    }
};


// -----------------------------------------------------------------------------
// 9. DESIGN TOKENS
// -----------------------------------------------------------------------------

struct DesignTokens {
    Color primary;
    Color success;
    Color danger;
    Color surface;
    Color text;

    double rootFontSize;

    DesignTokens()
        : primary(Color::fromHex("#3498db")),
          success(Color::fromHex("#2ecc71")),
          danger(Color::fromHex("#e74c3c")),
          surface(Color::fromHex("#f5f7fa")),
          text(Color::fromHex("#1f2937")),
          rootFontSize(16.0) {}

    std::string toCss() const {
        std::ostringstream output;

        output
            << ":root {\n"
            << "    --color-primary: "
            << primary.toHex()
            << ";\n"

            << "    --color-primary-light: "
            << adjustLightness(primary, 15).toHex()
            << ";\n"

            << "    --color-primary-dark: "
            << adjustLightness(primary, -15).toHex()
            << ";\n"

            << "    --color-success: "
            << success.toHex()
            << ";\n"

            << "    --color-danger: "
            << danger.toHex()
            << ";\n"

            << "    --color-surface: "
            << surface.toHex()
            << ";\n"

            << "    --color-text: "
            << text.toHex()
            << ";\n"

            << "    --space-1: 0.25rem;\n"
            << "    --space-2: 0.5rem;\n"
            << "    --space-4: 1rem;\n"
            << "    --space-6: 1.5rem;\n"
            << "    --space-8: 2rem;\n"
            << "}";

        return output.str();
    }
};


// -----------------------------------------------------------------------------
// 10. RESPONSIVE DASHBOARD COMPONENTS
// -----------------------------------------------------------------------------

class ResponsiveDashboard {
private:
    Viewport viewport;
    DesignTokens tokens;

public:
    ResponsiveDashboard(
        Viewport viewportValue,
        DesignTokens tokensValue
    )
        : viewport(std::move(viewportValue)),
          tokens(std::move(tokensValue)) {}

    double pagePaddingPx() const {
        /*
         * Model:
         *
         *     clamp(1rem, 4vw, 3rem)
         *
         * The preferred value responds to viewport width, while the minimum
         * and maximum values prevent extreme spacing.
         */
        return clampValue(
            viewport.vw(4.0),
            tokens.rootFontSize,
            tokens.rootFontSize * 3.0
        );
    }

    double headingSizePx() const {
        /*
         * Model:
         *
         *     clamp(2rem, 5vw, 4rem)
         */
        return clampValue(
            viewport.vw(5.0),
            tokens.rootFontSize * 2.0,
            tokens.rootFontSize * 4.0
        );
    }

    double heroHeightPx() const {
        return viewport.vh(70.0);
    }

    double cardWidthPx() const {
        /*
         * Model:
         *
         *     width: 92%;
         *     max-width: 720px;
         *
         * A component becomes fluid on smaller screens but remains bounded
         * on large screens.
         */
        return std::min(
            viewport.width * 0.92,
            720.0
        );
    }

    std::string generateCss() const {
        std::ostringstream output;

        output
            << ".dashboard {\n"
            << "    width: 92%;\n"
            << "    max-width: 1200px;\n"
            << "    margin-inline: auto;\n"
            << "    padding: "
            << cssValue(pagePaddingPx(), Unit::Px)
            << ";\n"
            << "}\n\n"

            << ".dashboard__hero {\n"
            << "    min-height: 70vh;\n"
            << "    padding: 8vh 4vw;\n"
            << "}\n\n"

            << ".dashboard__title {\n"
            << "    font-size: clamp(2rem, 5vw, 4rem);\n"
            << "    color: "
            << tokens.text.toHex()
            << ";\n"
            << "}\n\n"

            << ".dashboard__card {\n"
            << "    width: 100%;\n"
            << "    max-width: 720px;\n"
            << "    padding: 1.5rem;\n"
            << "    background: rgb(255 255 255 / 0.92);\n"
            << "    border-radius: 0.75rem;\n"
            << "}\n\n"

            << ".dashboard__button {\n"
            << "    padding: 0.75em 1.25em;\n"
            << "    color: white;\n"
            << "    background: hsl(204 70% 53%);\n"
            << "}\n";

        return output.str();
    }

    void printMetrics() const {
        std::cout
            << "Viewport: "
            << viewport.width
            << "x"
            << viewport.height
            << "\n";

        std::cout
            << "Page padding: "
            << pagePaddingPx()
            << "px\n";

        std::cout
            << "Heading size: "
            << headingSizePx()
            << "px\n";

        std::cout
            << "Hero height: "
            << heroHeightPx()
            << "px\n";

        std::cout
            << "Card width: "
            << cardWidthPx()
            << "px\n";
    }
};


// -----------------------------------------------------------------------------
// 11. COLOR PALETTE
// -----------------------------------------------------------------------------

std::vector<Color> createPalette(
    const Color& base
) {
    return {
        adjustLightness(base, -30),
        adjustLightness(base, -15),
        base,
        adjustLightness(base, 15),
        adjustLightness(base, 30)
    };
}


// -----------------------------------------------------------------------------
// 12. DEMONSTRATION
// -----------------------------------------------------------------------------

void demonstrateColors() {
    printSection("1. Color representations");

    std::vector<std::string> hexValues = {
        "#000000",
        "#ffffff",
        "#3498db",
        "#abc",
        "#336699cc"
    };

    for (const std::string& value : hexValues) {
        Color color = Color::fromHex(value);

        std::cout
            << value
            << " -> "
            << color.toRgbCss()
            << " -> "
            << toHslCss(color)
            << "\n";
    }

    Color translucent =
        Color::fromHex("#3498db80");

    std::cout
        << "RGBA HEX: "
        << translucent.toHex()
        << "\n";
}

void demonstrateHsl() {
    printSection("2. HSL conversion");

    std::vector<Color> colors = {
        Color(255, 0, 0),
        Color(52, 152, 219),
        Color(46, 204, 113),
        Color(155, 89, 182)
    };

    for (const Color& color : colors) {
        Hsl hsl = rgbToHsl(color);

        std::cout
            << color.toHex()
            << " -> HSL("
            << std::fixed
            << std::setprecision(1)
            << hsl.hue
            << ", "
            << hsl.saturation
            << "%, "
            << hsl.lightness
            << "%)\n";
    }
}

void demonstrateAlpha() {
    printSection("3. Alpha compositing");

    Color red(255, 0, 0);
    Color white(255, 255, 255);

    for (double alpha : {0.0, 0.25, 0.5, 0.75, 1.0}) {
        Color foreground(
            red.red,
            red.green,
            red.blue,
            alpha
        );

        Color result =
            alphaComposite(foreground, white);

        std::cout
            << "alpha="
            << alpha
            << " -> "
            << result.toHex()
            << "\n";
    }
}

void demonstrateContrast() {
    printSection("4. Contrast analysis");

    std::vector<std::pair<Color, Color>> pairs = {
        {
            Color(0, 0, 0),
            Color(255, 255, 255)
        },
        {
            Color(255, 255, 255),
            Color(52, 152, 219)
        },
        {
            Color(30, 30, 30),
            Color(240, 240, 240)
        }
    };

    for (const auto& pair : pairs) {
        double ratio =
            contrastRatio(
                pair.first,
                pair.second
            );

        std::cout
            << pair.first.toHex()
            << " on "
            << pair.second.toHex()
            << " -> "
            << std::fixed
            << std::setprecision(2)
            << ratio
            << ":1\n";
    }
}

void demonstratePalette() {
    printSection("5. HSL-based palette generation");

    Color primary =
        Color::fromHex("#3498db");

    for (const Color& color :
         createPalette(primary)) {
        std::cout
            << color.toHex()
            << " "
            << toHslCss(color)
            << "\n";
    }
}

void demonstrateUnits() {
    printSection("6. CSS unit calculations");

    const double rootFontSize = 16.0;
    const double componentFontSize = 20.0;

    std::cout
        << "2rem at 16px root: "
        << 2.0 * rootFontSize
        << "px\n";

    std::cout
        << "1.5em at 20px context: "
        << 1.5 * componentFontSize
        << "px\n";

    std::cout
        << "50% of 1200px: "
        << 0.5 * 1200.0
        << "px\n";

    std::cout
        << "4vw of 1440px viewport: "
        << 0.04 * 1440.0
        << "px\n";

    std::cout
        << "70vh of 900px viewport: "
        << 0.70 * 900.0
        << "px\n";
}

void demonstrateResponsiveDashboard() {
    printSection("7. Responsive dashboard case study");

    DesignTokens tokens;

    std::vector<Viewport> viewports = {
        Viewport(375, 667),
        Viewport(768, 1024),
        Viewport(1440, 900),
        Viewport(2560, 1440)
    };

    for (const Viewport& viewport : viewports) {
        ResponsiveDashboard dashboard(
            viewport,
            tokens
        );

        dashboard.printMetrics();
        std::cout << "\n";
    }

    std::cout
        << "Generated design tokens:\n\n"
        << tokens.toCss()
        << "\n";
}

void demonstrateGeneratedCss() {
    printSection("8. Generated CSS architecture");

    DesignTokens tokens;

    ResponsiveDashboard dashboard(
        Viewport(1440, 900),
        tokens
    );

    std::cout
        << dashboard.generateCss()
        << "\n";
}


// -----------------------------------------------------------------------------
// 13. FAILURE CONDITIONS
// -----------------------------------------------------------------------------

void demonstrateValidation() {
    printSection("9. Validation and failure conditions");

    try {
        Color invalid(256, 0, 0);
        (void)invalid;
    } catch (const std::exception& error) {
        std::cout
            << "Invalid RGB rejected: "
            << error.what()
            << "\n";
    }

    try {
        Color invalidAlpha(
            0,
            0,
            0,
            1.5
        );

        (void)invalidAlpha;
    } catch (const std::exception& error) {
        std::cout
            << "Invalid alpha rejected: "
            << error.what()
            << "\n";
    }

    try {
        Color invalidHex =
            Color::fromHex("#12");

        (void)invalidHex;
    } catch (const std::exception& error) {
        std::cout
            << "Invalid HEX rejected: "
            << error.what()
            << "\n";
    }

    try {
        Viewport invalidViewport(0, 900);
        (void)invalidViewport;
    } catch (const std::exception& error) {
        std::cout
            << "Invalid viewport rejected: "
            << error.what()
            << "\n";
    }
}


// -----------------------------------------------------------------------------
// 14. COMPLEXITY DISCUSSION IN EXECUTABLE FORM
// -----------------------------------------------------------------------------

void demonstrateComplexity() {
    printSection("10. Complexity considerations");

    std::cout
        << "HEX parsing: O(1), because CSS color strings have bounded length.\n";

    std::cout
        << "RGB to HSL conversion: O(1), using a fixed number of arithmetic operations.\n";

    std::cout
        << "HSL to RGB conversion: O(1), using a fixed number of branches and arithmetic operations.\n";

    std::cout
        << "Contrast calculation: O(1), using three color channels.\n";

    std::cout
        << "Palette generation for k colors: O(k).\n";

    std::cout
        << "Responsive layout calculation: O(1) per component because "
           "each component uses a fixed set of formulas.\n";

    std::cout
        << "Memory usage for individual color calculations: O(1).\n";

    std::cout
        << "For a large design system, the dominant engineering concern is "
           "usually consistency and rendering behavior rather than the cost "
           "of individual color conversions.\n";
}


// -----------------------------------------------------------------------------
// 15. ASSERTIONS
// -----------------------------------------------------------------------------

void runTests() {
    printSection("11. Self-tests");

    Color red =
        Color::fromHex("#ff0000");

    assert(red.red == 255);
    assert(red.green == 0);
    assert(red.blue == 0);
    assert(red.alpha == 1.0);

    Color shorthand =
        Color::fromHex("#abc");

    assert(shorthand.toHex() == "#aabbcc");

    Color rgba =
        Color::fromHex("#ff000080");

    assert(rgba.red == 255);
    assert(rgba.green == 0);
    assert(rgba.blue == 0);

    Hsl redHsl =
        rgbToHsl(red);

    assert(
        std::abs(redHsl.hue) < 1e-9
    );

    assert(
        std::abs(redHsl.saturation - 100.0)
        < 1e-9
    );

    assert(
        std::abs(redHsl.lightness - 50.0)
        < 1e-9
    );

    Color reconstructed =
        hslToRgb(0, 100, 50);

    assert(reconstructed.red == 255);
    assert(reconstructed.green == 0);
    assert(reconstructed.blue == 0);

    Viewport viewport(1000, 800);

    assert(
        std::abs(viewport.vw(50) - 500) < 1e-9
    );

    assert(
        std::abs(viewport.vh(50) - 400) < 1e-9
    );

    assert(
        std::abs(viewport.vmin(50) - 400) < 1e-9
    );

    assert(
        std::abs(viewport.vmax(50) - 500) < 1e-9
    );

    assert(
        std::abs(
            contrastRatio(
                Color(0, 0, 0),
                Color(255, 255, 255)
            ) - 21.0
        ) < 0.01
    );

    std::cout
        << "All self-tests passed.\n";
}


// -----------------------------------------------------------------------------
// 16. MAIN APPLICATION
// -----------------------------------------------------------------------------

int main() {
    try {
        demonstrateColors();
        demonstrateHsl();
        demonstrateAlpha();
        demonstrateContrast();
        demonstratePalette();
        demonstrateUnits();
        demonstrateResponsiveDashboard();
        demonstrateGeneratedCss();
        demonstrateValidation();
        demonstrateComplexity();
        runTests();

        printSection("12. Production design principles");

        std::cout
            << "1. Use semantic color tokens instead of scattering raw colors.\n"
            << "2. Use rem when root-relative sizing improves consistency.\n"
            << "3. Use em when component-relative typography is intentional.\n"
            << "4. Use percentages for relationships with containing blocks.\n"
            << "5. Use viewport units for viewport-relative behavior.\n"
            << "6. Constrain fluid values with min(), max(), or clamp().\n"
            << "7. Test text and background contrast.\n"
            << "8. Treat transparency as a compositing operation, not merely a visual decoration.\n"
            << "9. Validate generated values before they enter a production stylesheet.\n"
            << "10. Test responsive behavior across multiple viewport dimensions.\n";

        printSection("13. Case study CSS");

        std::cout
            << "A production dashboard can combine:\n"
            << "  - semantic color tokens\n"
            << "  - HEX for durable color definitions\n"
            << "  - HSL for controlled color transformations\n"
            << "  - RGB alpha for translucent surfaces\n"
            << "  - rem for spacing and typography\n"
            << "  - % for container relationships\n"
            << "  - vh/vw for viewport-scale sections\n"
            << "  - vmin/vmax for dimension-independent scaling\n"
            << "  - clamp() for bounded fluid typography\n";

        return 0;
    }
    catch (const std::exception& error) {
        std::cerr
            << "Fatal error: "
            << error.what()
            << "\n";

        return 1;
    }
}
