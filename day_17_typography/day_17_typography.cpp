/*
 * Typography Management System
 *
 * C++17 technical case study
 *
 * Scenario:
 * A large documentation and analytics platform needs a centralized
 * typography engine. The engine stores typography tokens, validates them,
 * generates CSS, estimates readable text measures, evaluates responsive
 * sizes, analyzes font assets, and reports potential accessibility problems.
 *
 * The program deliberately models typography as structured data rather than
 * scattered formatting values. This mirrors how a production design system
 * can centralize typography decisions.
 */

#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_set>
#include <utility>
#include <vector>

using namespace std;


// -----------------------------------------------------------------------------
// Enumerations
// -----------------------------------------------------------------------------

enum class FontCategory {
    Serif,
    SansSerif,
    Monospace,
    Cursive,
    Fantasy
};

enum class TextAlignment {
    Left,
    Right,
    Center,
    Justify
};

string toString(FontCategory category) {
    switch (category) {
        case FontCategory::Serif:
            return "serif";
        case FontCategory::SansSerif:
            return "sans-serif";
        case FontCategory::Monospace:
            return "monospace";
        case FontCategory::Cursive:
            return "cursive";
        case FontCategory::Fantasy:
            return "fantasy";
    }

    throw logic_error("Unknown font category.");
}

string toString(TextAlignment alignment) {
    switch (alignment) {
        case TextAlignment::Left:
            return "left";
        case TextAlignment::Right:
            return "right";
        case TextAlignment::Center:
            return "center";
        case TextAlignment::Justify:
            return "justify";
    }

    throw logic_error("Unknown text alignment.");
}


// -----------------------------------------------------------------------------
// Font-weight model
// -----------------------------------------------------------------------------

string describeWeight(int weight) {
    static const map<int, string> weights = {
        {100, "Thin"},
        {200, "Extra Light"},
        {300, "Light"},
        {400, "Normal"},
        {500, "Medium"},
        {600, "Semi Bold"},
        {700, "Bold"},
        {800, "Extra Bold"},
        {900, "Black"}
    };

    auto iterator = weights.find(weight);

    if (iterator == weights.end()) {
        throw invalid_argument("Font weight must be a CSS weight from 100 to 900.");
    }

    return iterator->second;
}


// -----------------------------------------------------------------------------
// Typography style
// -----------------------------------------------------------------------------

struct TypographyStyle {
    string name;
    string fontFamily;
    double fontSizeRem;
    int fontWeight;
    double lineHeight;
    double letterSpacingEm;
    TextAlignment alignment;

    vector<string> validate() const {
        vector<string> errors;

        if (name.empty()) {
            errors.emplace_back("Style name cannot be empty.");
        }

        if (fontFamily.empty()) {
            errors.emplace_back("Font family cannot be empty.");
        }

        if (fontSizeRem <= 0.0) {
            errors.emplace_back("Font size must be positive.");
        }

        try {
            static_cast<void>(describeWeight(fontWeight));
        } catch (const exception& exception) {
            errors.emplace_back(exception.what());
        }

        if (lineHeight <= 0.0) {
            errors.emplace_back("Line height must be positive.");
        }

        return errors;
    }

    string toCSS(const string& selector) const {
        vector<string> errors = validate();

        if (!errors.empty()) {
            throw invalid_argument(
                "Cannot generate CSS for " + name + ": " + errors.front()
            );
        }

        ostringstream css;

        css << selector << " {\n"
            << "    font-family: " << fontFamily << ";\n"
            << fixed << setprecision(3)
            << "    font-size: " << fontSizeRem << "rem;\n"
            << "    font-weight: " << fontWeight << ";\n"
            << "    line-height: " << lineHeight << ";\n"
            << "    letter-spacing: " << letterSpacingEm << "em;\n"
            << "    text-align: " << toString(alignment) << ";\n"
            << "}";

        return css.str();
    }
};


// -----------------------------------------------------------------------------
// Font asset
// -----------------------------------------------------------------------------

struct FontAsset {
    string family;
    int weight;
    string style;
    string format;
    size_t sizeBytes;

    bool isModernWebFormat() const {
        return format == "woff2";
    }
};


// -----------------------------------------------------------------------------
// Font repository
// -----------------------------------------------------------------------------

class FontRepository {
private:
    vector<FontAsset> assets;

public:
    void add(FontAsset asset) {
        if (asset.family.empty()) {
            throw invalid_argument("Font family cannot be empty.");
        }

        describeWeight(asset.weight);

        if (asset.sizeBytes == 0) {
            throw invalid_argument("Font asset size must be positive.");
        }

        assets.push_back(move(asset));
    }

    bool supports(
        const string& family,
        int weight,
        const string& style = "normal"
    ) const {
        return any_of(
            assets.begin(),
            assets.end(),
            [&](const FontAsset& asset) {
                return asset.family == family &&
                       asset.weight == weight &&
                       asset.style == style;
            }
        );
    }

    size_t totalBytes() const {
        size_t total = 0;

        for (const FontAsset& asset : assets) {
            total += asset.sizeBytes;
        }

        return total;
    }

    size_t countWeights(const string& family) const {
        unordered_set<int> weights;

        for (const FontAsset& asset : assets) {
            if (asset.family == family) {
                weights.insert(asset.weight);
            }
        }

        return weights.size();
    }

    const vector<FontAsset>& getAssets() const {
        return assets;
    }
};


// -----------------------------------------------------------------------------
// Typography system
// -----------------------------------------------------------------------------

class TypographySystem {
private:
    string name;
    vector<TypographyStyle> styles;

public:
    explicit TypographySystem(string systemName)
        : name(move(systemName)) {}

    void addStyle(TypographyStyle style) {
        if (!style.validate().empty()) {
            throw invalid_argument(
                "Invalid typography style: " + style.name
            );
        }

        auto duplicate = find_if(
            styles.begin(),
            styles.end(),
            [&](const TypographyStyle& existing) {
                return existing.name == style.name;
            }
        );

        if (duplicate != styles.end()) {
            throw invalid_argument(
                "Duplicate typography style: " + style.name
            );
        }

        styles.push_back(move(style));
    }

    const TypographyStyle* findStyle(const string& styleName) const {
        auto iterator = find_if(
            styles.begin(),
            styles.end(),
            [&](const TypographyStyle& style) {
                return style.name == styleName;
            }
        );

        if (iterator == styles.end()) {
            return nullptr;
        }

        return &(*iterator);
    }

    string generateCSS() const {
        ostringstream css;

        css << "/* " << name << " */\n\n";

        for (size_t index = 0; index < styles.size(); ++index) {
            const TypographyStyle& style = styles[index];

            css << style.toCSS(".type-" + style.name);

            if (index + 1 < styles.size()) {
                css << "\n\n";
            }
        }

        return css.str();
    }

    const vector<TypographyStyle>& getStyles() const {
        return styles;
    }
};


// -----------------------------------------------------------------------------
// Typography analyzer
// -----------------------------------------------------------------------------

struct AccessibilityReport {
    vector<string> warnings;
    vector<string> passedChecks;

    bool passed() const {
        return warnings.empty();
    }
};

class TypographyAnalyzer {
public:
    static AccessibilityReport analyze(
        const TypographyStyle& style
    ) {
        AccessibilityReport report;

        if (style.fontSizeRem < 0.75) {
            report.warnings.emplace_back(
                "Text is unusually small."
            );
        } else {
            report.passedChecks.emplace_back(
                "Font size is not unusually small."
            );
        }

        if (style.lineHeight < 1.2) {
            report.warnings.emplace_back(
                "Line height may be too tight for comfortable reading."
            );
        } else {
            report.passedChecks.emplace_back(
                "Line height provides reasonable separation."
            );
        }

        if (abs(style.letterSpacingEm) > 0.08) {
            report.warnings.emplace_back(
                "Letter spacing is unusually large."
            );
        } else {
            report.passedChecks.emplace_back(
                "Letter spacing is within a conservative range."
            );
        }

        if (style.fontWeight == 300 && style.fontSizeRem < 0.875) {
            report.warnings.emplace_back(
                "Light small text can become difficult to read."
            );
        } else {
            report.passedChecks.emplace_back(
                "Font weight and size combination is reasonable."
            );
        }

        return report;
    }
};


// -----------------------------------------------------------------------------
// Responsive typography
// -----------------------------------------------------------------------------

double clamp(
    double minimum,
    double preferred,
    double maximum
) {
    return max(minimum, min(preferred, maximum));
}

double responsiveHeadingRem(double viewportWidthPx) {
    // Conceptual equivalent:
    // font-size: clamp(2rem, 4vw, 3.5rem);
    const double preferredRem = viewportWidthPx * 0.04 / 16.0;

    return clamp(2.0, preferredRem, 3.5);
}


// -----------------------------------------------------------------------------
// Readability and text measure
// -----------------------------------------------------------------------------

size_t estimateCharactersPerLine(
    double containerWidthPx,
    double averageCharacterWidthPx
) {
    if (containerWidthPx <= 0 ||
        averageCharacterWidthPx <= 0) {
        throw invalid_argument(
            "Width and character width must be positive."
        );
    }

    return max(
        static_cast<size_t>(1),
        static_cast<size_t>(
            containerWidthPx / averageCharacterWidthPx
        )
    );
}

size_t estimateLineCount(
    const string& text,
    double containerWidthPx,
    double averageCharacterWidthPx
) {
    if (text.empty()) {
        return 0;
    }

    const size_t charactersPerLine =
        estimateCharactersPerLine(
            containerWidthPx,
            averageCharacterWidthPx
        );

    istringstream input(text);
    string word;

    size_t lines = 1;
    size_t currentLength = 0;

    while (input >> word) {
        const size_t wordLength = word.size();

        if (wordLength > charactersPerLine) {
            if (currentLength > 0) {
                ++lines;
                currentLength = 0;
            }

            lines +=
                (wordLength + charactersPerLine - 1) /
                charactersPerLine - 1;

            currentLength = wordLength % charactersPerLine;
            continue;
        }

        const size_t required =
            currentLength == 0
                ? wordLength
                : wordLength + 1;

        if (currentLength + required <= charactersPerLine) {
            currentLength += required;
        } else {
            ++lines;
            currentLength = wordLength;
        }
    }

    return lines;
}


// -----------------------------------------------------------------------------
// Typography scale
// -----------------------------------------------------------------------------

map<int, double> createTypeScale(
    double baseRem,
    double ratio,
    int minimumStep,
    int maximumStep
) {
    if (baseRem <= 0 || ratio <= 0) {
        throw invalid_argument(
            "Base size and ratio must be positive."
        );
    }

    map<int, double> scale;

    for (int step = minimumStep;
         step <= maximumStep;
         ++step) {
        scale[step] =
            baseRem * pow(ratio, step);
    }

    return scale;
}


// -----------------------------------------------------------------------------
// Font fallback
// -----------------------------------------------------------------------------

string chooseFont(
    const vector<string>& requestedFamilies,
    const unordered_set<string>& installedFamilies,
    const string& genericFallback
) {
    for (const string& family : requestedFamilies) {
        if (installedFamilies.find(family) !=
            installedFamilies.end()) {
            return family;
        }
    }

    return genericFallback;
}


// -----------------------------------------------------------------------------
// Alignment helper
// -----------------------------------------------------------------------------

TextAlignment recommendedAlignment(
    const string& contentType
) {
    if (
        contentType == "paragraph" ||
        contentType == "article" ||
        contentType == "documentation" ||
        contentType == "body"
    ) {
        return TextAlignment::Left;
    }

    if (
        contentType == "numeric-data" ||
        contentType == "table-number"
    ) {
        return TextAlignment::Right;
    }

    if (
        contentType == "badge" ||
        contentType == "short-label"
    ) {
        return TextAlignment::Center;
    }

    return TextAlignment::Left;
}


// -----------------------------------------------------------------------------
// CSS-safe font-family validation
// -----------------------------------------------------------------------------

string validateFontFamily(const string& family) {
    if (family.empty() || family.size() > 100) {
        throw invalid_argument(
            "Font family length is invalid."
        );
    }

    if (
        family.find('{') != string::npos ||
        family.find('}') != string::npos ||
        family.find(';') != string::npos
    ) {
        throw invalid_argument(
            "Potentially unsafe CSS characters detected."
        );
    }

    return family;
}


// -----------------------------------------------------------------------------
// System report
// -----------------------------------------------------------------------------

void printAccessibilityReport(
    const string& styleName,
    const AccessibilityReport& report
) {
    cout << styleName << ": "
         << (report.passed() ? "PASS" : "WARNINGS")
         << '\n';

    for (const string& warning : report.warnings) {
        cout << "  WARNING: " << warning << '\n';
    }

    for (const string& passed : report.passedChecks) {
        cout << "  PASS: " << passed << '\n';
    }
}


// -----------------------------------------------------------------------------
// Main technical case study
// -----------------------------------------------------------------------------

int main() {
    try {
        cout << string(78, '=') << '\n';
        cout << "TYPOGRAPHY MANAGEMENT SYSTEM\n";
        cout << string(78, '=') << "\n\n";

        // ---------------------------------------------------------------------
        // Step 1: Establish the font strategy.
        // ---------------------------------------------------------------------

        validateFontFamily(
            "Inter, Arial, Helvetica, sans-serif"
        );

        const string primaryFont =
            "Inter, Arial, Helvetica, sans-serif";

        cout << "Primary font stack:\n"
             << "  " << primaryFont << "\n\n";


        // ---------------------------------------------------------------------
        // Step 2: Register only the weights the system requires.
        // ---------------------------------------------------------------------

        FontRepository fonts;

        fonts.add({
            "Inter",
            400,
            "normal",
            "woff2",
            32000
        });

        fonts.add({
            "Inter",
            600,
            "normal",
            "woff2",
            34000
        });

        fonts.add({
            "Inter",
            700,
            "normal",
            "woff2",
            35000
        });

        cout << "Font repository:\n";
        cout << "  Total assets: "
             << fonts.getAssets().size() << '\n';
        cout << "  Total payload: "
             << fonts.totalBytes() / 1024.0
             << " KB\n";
        cout << "  Available Inter weights: "
             << fonts.countWeights("Inter") << "\n\n";


        // ---------------------------------------------------------------------
        // Step 3: Build a coherent hierarchy.
        //
        // A hierarchy is not merely a collection of large and small text.
        // Size, weight, line-height, spacing, and placement work together.
        // ---------------------------------------------------------------------

        TypographySystem system("Documentation Platform");

        system.addStyle({
            "display",
            primaryFont,
            3.5,
            700,
            1.05,
            -0.02,
            TextAlignment::Left
        });

        system.addStyle({
            "heading-1",
            primaryFont,
            2.5,
            700,
            1.15,
            -0.015,
            TextAlignment::Left
        });

        system.addStyle({
            "heading-2",
            primaryFont,
            2.0,
            700,
            1.20,
            -0.01,
            TextAlignment::Left
        });

        system.addStyle({
            "heading-3",
            primaryFont,
            1.5,
            600,
            1.25,
            -0.005,
            TextAlignment::Left
        });

        system.addStyle({
            "body",
            primaryFont,
            1.0,
            400,
            1.60,
            0.0,
            TextAlignment::Left
        });

        system.addStyle({
            "metadata",
            primaryFont,
            0.8125,
            500,
            1.40,
            0.005,
            TextAlignment::Left
        });


        // ---------------------------------------------------------------------
        // Step 4: Validate every style before publishing it.
        // ---------------------------------------------------------------------

        cout << "STYLE VALIDATION\n";

        for (const TypographyStyle& style :
             system.getStyles()) {
            vector<string> errors = style.validate();

            cout << "  " << style.name << ": ";

            if (errors.empty()) {
                cout << "valid\n";
            } else {
                cout << "invalid\n";

                for (const string& error : errors) {
                    cout << "    - " << error << '\n';
                }
            }
        }

        cout << '\n';


        // ---------------------------------------------------------------------
        // Step 5: Check font availability for each hierarchy level.
        // ---------------------------------------------------------------------

        cout << "FONT AVAILABILITY\n";

        for (const TypographyStyle& style :
             system.getStyles()) {
            cout << "  " << style.name
                 << " weight " << style.fontWeight
                 << ": "
                 << (
                     fonts.supports(
                         "Inter",
                         style.fontWeight
                     )
                         ? "available"
                         : "missing"
                 )
                 << '\n';
        }

        cout << '\n';


        // ---------------------------------------------------------------------
        // Step 6: Analyze accessibility-related typography risks.
        // ---------------------------------------------------------------------

        cout << "ACCESSIBILITY ANALYSIS\n";

        for (const TypographyStyle& style :
             system.getStyles()) {
            printAccessibilityReport(
                style.name,
                TypographyAnalyzer::analyze(style)
            );
        }

        cout << '\n';


        // ---------------------------------------------------------------------
        // Step 7: Demonstrate responsive hierarchy.
        // ---------------------------------------------------------------------

        cout << "RESPONSIVE HEADING SCALE\n";

        const vector<double> viewports = {
            320,
            480,
            768,
            1024,
            1440,
            1920
        };

        cout << fixed << setprecision(2);

        for (double viewport : viewports) {
            cout << "  "
                 << viewport
                 << "px -> "
                 << responsiveHeadingRem(viewport)
                 << "rem\n";
        }

        cout << '\n';


        // ---------------------------------------------------------------------
        // Step 8: Estimate readable text measure.
        // ---------------------------------------------------------------------

        const string documentationText =
            "Typography controls structure, emphasis, rhythm, "
            "and readability in digital documentation.";

        cout << "TEXT MEASURE ESTIMATION\n";

        for (double width :
             {280.0, 400.0, 600.0, 760.0}) {
            cout << "  "
                 << width
                 << "px container -> approximately "
                 << estimateLineCount(
                        documentationText,
                        width,
                        8.0
                    )
                 << " line(s)\n";
        }

        cout << '\n';


        // ---------------------------------------------------------------------
        // Step 9: Demonstrate modular typography.
        // ---------------------------------------------------------------------

        cout << "MODULAR TYPE SCALE\n";

        map<int, double> scale =
            createTypeScale(
                1.0,
                1.25,
                -2,
                4
            );

        for (const auto& [step, size] : scale) {
            cout << "  step "
                 << showpos << step
                 << noshowpos
                 << ": "
                 << fixed << setprecision(3)
                 << size
                 << "rem\n";
        }

        cout << '\n';


        // ---------------------------------------------------------------------
        // Step 10: Demonstrate font fallback.
        // ---------------------------------------------------------------------

        unordered_set<string> installedFonts = {
            "Arial",
            "Consolas"
        };

        vector<string> requestedFonts = {
            "Inter",
            "Helvetica",
            "Arial",
            "sans-serif"
        };

        cout << "FONT FALLBACK\n";
        cout << "  Selected: "
             << chooseFont(
                    requestedFonts,
                    installedFonts,
                    "sans-serif"
                )
             << "\n\n";


        // ---------------------------------------------------------------------
        // Step 11: Demonstrate content-specific alignment.
        // ---------------------------------------------------------------------

        cout << "ALIGNMENT POLICY\n";

        const vector<string> contentTypes = {
            "paragraph",
            "heading",
            "numeric-data",
            "badge",
            "documentation"
        };

        for (const string& contentType : contentTypes) {
            cout << "  "
                 << contentType
                 << " -> "
                 << toString(
                        recommendedAlignment(contentType)
                    )
                 << '\n';
        }

        cout << '\n';


        // ---------------------------------------------------------------------
        // Step 12: Generate deployable CSS.
        // ---------------------------------------------------------------------

        cout << "GENERATED CSS\n";
        cout << system.generateCSS() << "\n\n";


        // ---------------------------------------------------------------------
        // Step 13: Production font-performance analysis.
        //
        // Every additional font weight can increase network transfer.
        // Loading a complete family when only a few weights are needed is
        // often unnecessary.
        // ---------------------------------------------------------------------

        cout << "FONT PERFORMANCE\n";

        cout << "  Total font payload: "
             << fonts.totalBytes() / 1024.0
             << " KB\n";

        cout << "  Average asset size: "
             << fonts.totalBytes() /
                    static_cast<double>(
                        fonts.getAssets().size()
                    ) /
                    1024.0
             << " KB\n";

        cout << "  Modern WOFF2 assets: ";

        size_t modernAssets = count_if(
            fonts.getAssets().begin(),
            fonts.getAssets().end(),
            [](const FontAsset& asset) {
                return asset.isModernWebFormat();
            }
        );

        cout << modernAssets
             << "/"
             << fonts.getAssets().size()
             << "\n\n";


        // ---------------------------------------------------------------------
        // Step 14: Important edge cases.
        // ---------------------------------------------------------------------

        cout << "EDGE CASES\n";

        const vector<string> edgeTexts = {
            "",
            "A",
            "supercalifragilisticexpialidocious",
            "Typography    uses    whitespace."
        };

        for (const string& text : edgeTexts) {
            cout << "  Text length "
                 << text.size()
                 << " -> ";

            try {
                cout << estimateLineCount(
                            text,
                            300,
                            8
                        )
                     << " estimated line(s)\n";
            } catch (const exception& exception) {
                cout << "error: "
                     << exception.what()
                     << '\n';
            }
        }

        cout << '\n';


        // ---------------------------------------------------------------------
        // Step 15: Failure condition.
        //
        // A production system should reject invalid design tokens instead of
        // silently generating broken CSS.
        // ---------------------------------------------------------------------

        cout << "FAILURE CONDITION TEST\n";

        try {
            TypographyStyle invalidStyle{
                "invalid",
                primaryFont,
                1.0,
                450,
                1.5,
                0.0,
                TextAlignment::Left
            };

            vector<string> errors =
                invalidStyle.validate();

            if (!errors.empty()) {
                cout << "  Rejected invalid style:\n";

                for (const string& error : errors) {
                    cout << "    - "
                         << error
                         << '\n';
                }
            }
        } catch (const exception& exception) {
            cout << "  Exception: "
                 << exception.what()
                 << '\n';
        }

        cout << '\n';


        // ---------------------------------------------------------------------
        // Step 16: Complexity considerations.
        // ---------------------------------------------------------------------

        cout << "COMPLEXITY CONSIDERATIONS\n";
        cout << "  Style validation: O(1) per style for fixed properties.\n";
        cout << "  Font availability lookup: O(n) over registered assets.\n";
        cout << "  CSS generation: O(s), where s is the number of styles.\n";
        cout << "  Text line estimation: O(w), where w is the number of words.\n";
        cout << "  Type-scale generation: O(k), where k is the number of steps.\n";
        cout << '\n';


        // ---------------------------------------------------------------------
        // Step 17: Architectural trade-offs.
        // ---------------------------------------------------------------------

        cout << "ARCHITECTURAL TRADE-OFFS\n";
        cout << "  Centralized tokens improve consistency but require governance.\n";
        cout << "  More font weights improve expressive range but increase payload.\n";
        cout << "  Responsive sizing improves adaptability but needs testing at\n";
        cout << "  intermediate viewport widths.\n";
        cout << "  Aggressive letter spacing can create distinctive headings but may\n";
        cout << "  reduce readability when applied to ordinary text.\n";
        cout << '\n';


        // ---------------------------------------------------------------------
        // Step 18: Production checklist.
        // ---------------------------------------------------------------------

        cout << "PRODUCTION CHECKLIST\n";

        const vector<string> checklist = {
            "Use a coherent font-family strategy.",
            "Provide fallback fonts.",
            "Load only required weights and styles.",
            "Use line-height appropriate to the content.",
            "Use letter-spacing conservatively.",
            "Establish explicit hierarchy.",
            "Test responsive typography.",
            "Test multilingual content.",
            "Measure actual font payload.",
            "Validate design tokens before publication.",
            "Avoid injecting untrusted CSS values.",
            "Test with real content and real layouts."
        };

        for (const string& item : checklist) {
            cout << "  [ ] "
                 << item
                 << '\n';
        }

        cout << "\n"
             << string(78, '=')
             << '\n'
             << "TYPOGRAPHY MANAGEMENT SYSTEM COMPLETE\n"
             << string(78, '=')
             << '\n';

        return 0;

    } catch (const exception& exception) {
        cerr << "Fatal error: "
             << exception.what()
             << '\n';

        return 1;
    }
}
