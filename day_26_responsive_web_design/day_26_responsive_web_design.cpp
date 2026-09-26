/*
    Responsive Web Design Technical Case Study
    --------------------------------------------

    Scenario:
    A content publishing platform serves an article catalog to users with
    different viewport sizes, device-pixel ratios, orientations, and network
    conditions.

    The C++ program models the responsive decision system behind the website.

    It demonstrates:
    - mobile-first breakpoints
    - content-driven layout decisions
    - responsive grid calculations
    - responsive typography
    - responsive image selection
    - device-pixel-ratio handling
    - art direction
    - image cropping
    - validation
    - accessibility checks
    - performance estimation
    - caching considerations
    - modular class design
    - error handling
    - algorithmic complexity

    Compile:
        g++ -std=c++17 -O2 responsive_web_design.cpp -o responsive_web_design

    Run:
        ./responsive_web_design
*/

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
#include <utility>
#include <vector>

// ============================================================================
// 1. BASIC DATA STRUCTURES
// ============================================================================

struct Viewport {
    int width;
    int height;
    double devicePixelRatio;
    bool prefersReducedMotion;

    Viewport(
        int width_,
        int height_,
        double devicePixelRatio_ = 1.0,
        bool prefersReducedMotion_ = false
    )
        : width(width_),
          height(height_),
          devicePixelRatio(devicePixelRatio_),
          prefersReducedMotion(prefersReducedMotion_) {
        if (width <= 0 || height <= 0) {
            throw std::invalid_argument(
                "Viewport dimensions must be positive."
            );
        }

        if (devicePixelRatio <= 0.0) {
            throw std::invalid_argument(
                "Device pixel ratio must be positive."
            );
        }
    }

    bool isLandscape() const {
        return width >= height;
    }

    std::string orientation() const {
        return isLandscape() ? "landscape" : "portrait";
    }
};

struct Breakpoint {
    std::string name;
    int minWidth;
};

// ============================================================================
// 2. RESPONSIVE BREAKPOINT SYSTEM
// ============================================================================

class BreakpointSystem {
private:
    std::vector<Breakpoint> breakpoints;

public:
    explicit BreakpointSystem(std::vector<Breakpoint> values)
        : breakpoints(std::move(values)) {
        validate();
    }

    void validate() const {
        if (breakpoints.empty()) {
            throw std::invalid_argument(
                "At least one breakpoint is required."
            );
        }

        int previous = -1;

        for (const auto& breakpoint : breakpoints) {
            if (breakpoint.minWidth < 0) {
                throw std::invalid_argument(
                    "Breakpoint cannot be negative."
                );
            }

            if (breakpoint.minWidth < previous) {
                throw std::invalid_argument(
                    "Breakpoints must be ordered."
                );
            }

            previous = breakpoint.minWidth;
        }
    }

    std::string modeFor(const Viewport& viewport) const {
        std::string active = breakpoints.front().name;

        for (const auto& breakpoint : breakpoints) {
            if (viewport.width >= breakpoint.minWidth) {
                active = breakpoint.name;
            } else {
                break;
            }
        }

        return active;
    }
};

// ============================================================================
// 3. CONTENT-DRIVEN GRID
// ============================================================================

class ResponsiveGrid {
private:
    int gapPx;
    int horizontalPaddingPx;

public:
    ResponsiveGrid(
        int gapPx_,
        int horizontalPaddingPx_
    )
        : gapPx(gapPx_),
          horizontalPaddingPx(horizontalPaddingPx_) {
        if (gapPx < 0 || horizontalPaddingPx < 0) {
            throw std::invalid_argument(
                "Grid spacing cannot be negative."
            );
        }
    }

    int columnsFor(const Viewport& viewport) const {
        /*
            The thresholds are content decisions, not device names.

            A real production design should choose these values after testing
            actual content. A breakpoint is useful when the current content
            arrangement becomes unsuitable.
        */
        if (viewport.width >= 1200) {
            return 4;
        }

        if (viewport.width >= 900) {
            return 3;
        }

        if (viewport.width >= 600) {
            return 2;
        }

        return 1;
    }

    double cardWidthFor(const Viewport& viewport) const {
        const int columns = columnsFor(viewport);

        const double availableWidth =
            static_cast<double>(
                viewport.width -
                2 * horizontalPaddingPx
            );

        const double totalGaps =
            static_cast<double>(
                gapPx * (columns - 1)
            );

        if (availableWidth <= totalGaps) {
            return 0.0;
        }

        return (
            availableWidth - totalGaps
        ) / static_cast<double>(columns);
    }
};

// ============================================================================
// 4. RESPONSIVE TYPOGRAPHY
// ============================================================================

class FluidTypography {
private:
    double minimumPx;
    double slope;
    double intercept;
    double maximumPx;

public:
    FluidTypography(
        double minimumPx_,
        double slope_,
        double intercept_,
        double maximumPx_
    )
        : minimumPx(minimumPx_),
          slope(slope_),
          intercept(intercept_),
          maximumPx(maximumPx_) {
        if (minimumPx <= 0.0 ||
            maximumPx <= 0.0 ||
            maximumPx < minimumPx) {
            throw std::invalid_argument(
                "Invalid typography limits."
            );
        }
    }

    double sizeFor(const Viewport& viewport) const {
        /*
            This models:

                font-size:
                    clamp(
                        minimum,
                        preferred,
                        maximum
                    );

            The preferred value is a linear function of viewport width.
        */
        const double preferred =
            slope * viewport.width + intercept;

        return std::max(
            minimumPx,
            std::min(preferred, maximumPx)
        );
    }

    double remFor(
        const Viewport& viewport,
        double rootFontSize = 16.0
    ) const {
        if (rootFontSize <= 0.0) {
            throw std::invalid_argument(
                "Root font size must be positive."
            );
        }

        return sizeFor(viewport) / rootFontSize;
    }
};

// ============================================================================
// 5. RESPONSIVE IMAGE CANDIDATES
// ============================================================================

struct ImageCandidate {
    std::string filename;
    int intrinsicWidth;
    double density;

    ImageCandidate(
        std::string filename_,
        int intrinsicWidth_,
        double density_ = 1.0
    )
        : filename(std::move(filename_)),
          intrinsicWidth(intrinsicWidth_),
          density(density_) {
        if (intrinsicWidth <= 0) {
            throw std::invalid_argument(
                "Image width must be positive."
            );
        }

        if (density <= 0.0) {
            throw std::invalid_argument(
                "Image density must be positive."
            );
        }
    }

    double physicalPixelWidth() const {
        return (
            static_cast<double>(intrinsicWidth) *
            density
        );
    }
};

// ============================================================================
// 6. RESPONSIVE IMAGE SELECTOR
// ============================================================================

class ResponsiveImageSelector {
public:
    static ImageCandidate select(
        const std::vector<ImageCandidate>& candidates,
        double renderedWidth,
        double devicePixelRatio
    ) {
        if (candidates.empty()) {
            throw std::invalid_argument(
                "Image candidate list cannot be empty."
            );
        }

        if (renderedWidth <= 0.0) {
            throw std::invalid_argument(
                "Rendered width must be positive."
            );
        }

        if (devicePixelRatio <= 0.0) {
            throw std::invalid_argument(
                "Device pixel ratio must be positive."
            );
        }

        /*
            The browser needs enough intrinsic pixels to avoid unnecessary
            upscaling.

            Required physical pixels:

                rendered CSS pixels × device pixel ratio
        */
        const double requiredPixels =
            renderedWidth * devicePixelRatio;

        std::vector<ImageCandidate> ordered = candidates;

        std::sort(
            ordered.begin(),
            ordered.end(),
            [](const ImageCandidate& a,
               const ImageCandidate& b) {
                return a.physicalPixelWidth() <
                       b.physicalPixelWidth();
            }
        );

        for (const auto& candidate : ordered) {
            if (candidate.physicalPixelWidth() >= requiredPixels) {
                return candidate;
            }
        }

        /*
            If no candidate is large enough, return the largest available
            source. Production systems may instead impose a maximum quality
            policy or fetch a higher-resolution source.
        */
        return ordered.back();
    }
};

// ============================================================================
// 7. RESPONSIVE IMAGE MARKUP MODEL
// ============================================================================

class ImageMarkup {
private:
    std::vector<ImageCandidate> candidates;

public:
    explicit ImageMarkup(
        std::vector<ImageCandidate> candidates_
    )
        : candidates(std::move(candidates_)) {
        if (candidates.empty()) {
            throw std::invalid_argument(
                "Image markup requires candidates."
            );
        }
    }

    std::string srcset() const {
        std::vector<ImageCandidate> ordered = candidates;

        std::sort(
            ordered.begin(),
            ordered.end(),
            [](const ImageCandidate& a,
               const ImageCandidate& b) {
                return a.intrinsicWidth <
                       b.intrinsicWidth;
            }
        );

        std::ostringstream output;

        for (std::size_t index = 0;
             index < ordered.size();
             ++index) {
            if (index > 0) {
                output << ", ";
            }

            output
                << ordered[index].filename
                << " "
                << ordered[index].intrinsicWidth
                << "w";
        }

        return output.str();
    }

    std::string sizes() const {
        return
            "(min-width: 1200px) 25vw, "
            "(min-width: 900px) 33vw, "
            "(min-width: 600px) 50vw, "
            "100vw";
    }
};

// ============================================================================
// 8. ART DIRECTION
// ============================================================================

struct ArtDirectedSource {
    std::string minimumWidthCondition;
    int minimumWidth;
    std::string filename;
};

class ArtDirectionSelector {
public:
    static std::string select(
        const std::vector<ArtDirectedSource>& sources,
        const Viewport& viewport
    ) {
        if (sources.empty()) {
            throw std::invalid_argument(
                "Art-direction source list cannot be empty."
            );
        }

        const ArtDirectedSource* selected = nullptr;

        for (const auto& source : sources) {
            if (viewport.width >= source.minimumWidth) {
                if (
                    selected == nullptr ||
                    source.minimumWidth >
                        selected->minimumWidth
                ) {
                    selected = &source;
                }
            }
        }

        if (selected != nullptr) {
            return selected->filename;
        }

        /*
            A source with minimumWidth = 0 serves as the fallback.
        */
        for (const auto& source : sources) {
            if (source.minimumWidth == 0) {
                return source.filename;
            }
        }

        throw std::runtime_error(
            "No applicable art-direction source."
        );
    }
};

// ============================================================================
// 9. IMAGE COVER CALCULATION
// ============================================================================

struct Dimensions {
    double width;
    double height;
};

class ImageCropCalculator {
public:
    static Dimensions cover(
        double sourceWidth,
        double sourceHeight,
        double containerWidth,
        double containerHeight
    ) {
        if (
            sourceWidth <= 0.0 ||
            sourceHeight <= 0.0 ||
            containerWidth <= 0.0 ||
            containerHeight <= 0.0
        ) {
            throw std::invalid_argument(
                "Image dimensions must be positive."
            );
        }

        const double scale = std::max(
            containerWidth / sourceWidth,
            containerHeight / sourceHeight
        );

        return {
            sourceWidth * scale,
            sourceHeight * scale
        };
    }
};

// ============================================================================
// 10. ACCESSIBILITY MODEL
// ============================================================================

class AccessibilityChecker {
public:
    static bool acceptableTouchTarget(
        double width,
        double height,
        double minimum = 44.0
    ) {
        if (
            width <= 0.0 ||
            height <= 0.0 ||
            minimum <= 0.0
        ) {
            throw std::invalid_argument(
                "Touch-target dimensions must be positive."
            );
        }

        return width >= minimum &&
               height >= minimum;
    }

    static bool hasReadableTextMeasure(
        double contentWidth,
        double maximumReadingWidth = 720.0
    ) {
        if (contentWidth <= 0.0) {
            throw std::invalid_argument(
                "Content width must be positive."
            );
        }

        return contentWidth <= maximumReadingWidth;
    }
};

// ============================================================================
// 11. PERFORMANCE MODEL
// ============================================================================

struct NetworkProfile {
    std::string name;
    double megabitsPerSecond;
};

class PerformanceEstimator {
public:
    static double transferSeconds(
        double kilobytes,
        const NetworkProfile& network
    ) {
        if (kilobytes < 0.0) {
            throw std::invalid_argument(
                "Resource size cannot be negative."
            );
        }

        if (network.megabitsPerSecond <= 0.0) {
            throw std::invalid_argument(
                "Network speed must be positive."
            );
        }

        const double megabits =
            (kilobytes * 8.0) / 1000.0;

        return (
            megabits /
            network.megabitsPerSecond
        );
    }
};

// ============================================================================
// 12. ARTICLE CONTENT MODEL
// ============================================================================

struct Article {
    int id;
    std::string title;
    std::string category;
    int estimatedReadingMinutes;
    std::vector<ImageCandidate> images;
};

class ArticleCatalog {
private:
    std::vector<Article> articles;

public:
    void add(Article article) {
        if (article.id <= 0) {
            throw std::invalid_argument(
                "Article ID must be positive."
            );
        }

        if (article.title.empty()) {
            throw std::invalid_argument(
                "Article title cannot be empty."
            );
        }

        if (article.images.empty()) {
            throw std::invalid_argument(
                "Article must have responsive images."
            );
        }

        articles.push_back(std::move(article));
    }

    const std::vector<Article>& all() const {
        return articles;
    }

    std::vector<Article> filterByCategory(
        const std::string& category
    ) const {
        std::vector<Article> result;

        for (const auto& article : articles) {
            if (article.category == category) {
                result.push_back(article);
            }
        }

        return result;
    }
};

// ============================================================================
// 13. RESPONSIVE PAGE RENDER MODEL
// ============================================================================

class ResponsivePageRenderer {
private:
    BreakpointSystem breakpointSystem;
    ResponsiveGrid grid;
    FluidTypography headingTypography;

public:
    ResponsivePageRenderer()
        : breakpointSystem({
            {"mobile", 0},
            {"tablet", 600},
            {"desktop", 900},
            {"wide", 1200}
        }),
          grid(16, 32),
          headingTypography(
              28.0,
              0.025,
              12.0,
              56.0
          ) {}

    void renderArticleSummary(
        const Article& article,
        const Viewport& viewport
    ) const {
        const std::string mode =
            breakpointSystem.modeFor(viewport);

        const int columns =
            grid.columnsFor(viewport);

        const double cardWidth =
            grid.cardWidthFor(viewport);

        const double headingSize =
            headingTypography.sizeFor(viewport);

        const ImageCandidate selectedImage =
            ResponsiveImageSelector::select(
                article.images,
                cardWidth,
                viewport.devicePixelRatio
            );

        std::cout
            << "\nArticle: "
            << article.title
            << "\n  Category: "
            << article.category
            << "\n  Viewport: "
            << viewport.width
            << "x"
            << viewport.height
            << "\n  Orientation: "
            << viewport.orientation()
            << "\n  Responsive mode: "
            << mode
            << "\n  Grid columns: "
            << columns
            << "\n  Estimated card width: "
            << std::fixed
            << std::setprecision(1)
            << cardWidth
            << "px"
            << "\n  Fluid heading size: "
            << headingSize
            << "px"
            << "\n  Selected image: "
            << selectedImage.filename
            << "\n  Device pixel ratio: "
            << viewport.devicePixelRatio
            << "\n  Reduced motion: "
            << (
                viewport.prefersReducedMotion
                    ? "yes"
                    : "no"
            )
            << "\n";
    }
};

// ============================================================================
// 14. CACHE MODEL
// ============================================================================

class ImageCache {
private:
    std::map<std::string, int> cachedResources;

public:
    void store(
        const std::string& filename,
        int kilobytes
    ) {
        if (filename.empty()) {
            throw std::invalid_argument(
                "Cache key cannot be empty."
            );
        }

        if (kilobytes < 0) {
            throw std::invalid_argument(
                "Cached size cannot be negative."
            );
        }

        cachedResources[filename] = kilobytes;
    }

    bool contains(
        const std::string& filename
    ) const {
        return cachedResources.find(filename) !=
               cachedResources.end();
    }

    std::size_t count() const {
        return cachedResources.size();
    }
};

// ============================================================================
// 15. SECURITY AND PRODUCTION VALIDATION
// ============================================================================

class ProductionValidator {
public:
    static void validateArticle(const Article& article) {
        if (article.id <= 0) {
            throw std::invalid_argument(
                "Invalid article ID."
            );
        }

        if (article.title.size() > 300) {
            throw std::invalid_argument(
                "Article title exceeds configured length."
            );
        }

        if (article.category.empty()) {
            throw std::invalid_argument(
                "Article category is required."
            );

        }

        for (const auto& image : article.images) {
            if (image.filename.find("javascript:") !=
                std::string::npos) {
                throw std::invalid_argument(
                    "Unsafe image reference."
                );
            }
        }
    }
};

// ============================================================================
// 16. TEST HELPERS
// ============================================================================

void expect(
    bool condition,
    const std::string& message
) {
    if (!condition) {
        throw std::runtime_error(
            "Test failed: " + message
        );
    }
}

void testBreakpointSystem() {
    BreakpointSystem system({
        {"mobile", 0},
        {"tablet", 600},
        {"desktop", 900},
        {"wide", 1200}
    });

    expect(
        system.modeFor(Viewport(375, 800)) == "mobile",
        "375px should be mobile."
    );

    expect(
        system.modeFor(Viewport(768, 1000)) == "tablet",
        "768px should be tablet."
    );

    expect(
        system.modeFor(Viewport(1024, 768)) == "desktop",
        "1024px should be desktop."
    );

    expect(
        system.modeFor(Viewport(1440, 900)) == "wide",
        "1440px should be wide."
    );
}

void testGrid() {
    ResponsiveGrid grid(16, 32);

    expect(
        grid.columnsFor(Viewport(375, 800)) == 1,
        "Mobile should have one column."
    );

    expect(
        grid.columnsFor(Viewport(768, 1024)) == 2,
        "Tablet should have two columns."
    );

    expect(
        grid.columnsFor(Viewport(1024, 768)) == 3,
        "Desktop should have three columns."
    );

    expect(
        grid.columnsFor(Viewport(1440, 900)) == 4,
        "Wide should have four columns."
    );
}

void testTypography() {
    FluidTypography typography(
        28.0,
        0.025,
        12.0,
        56.0
    );

    const double small =
        typography.sizeFor(Viewport(320, 700));

    const double large =
        typography.sizeFor(Viewport(2000, 1000));

    expect(
        small >= 28.0,
        "Typography went below minimum."
    );

    expect(
        large <= 56.0,
        "Typography exceeded maximum."
    );
}

void testResponsiveImages() {
    std::vector<ImageCandidate> candidates = {
        {"hero-480.jpg", 480},
        {"hero-800.jpg", 800},
        {"hero-1200.jpg", 1200},
        {"hero-1600.jpg", 1600}
    };

    auto first =
        ResponsiveImageSelector::select(
            candidates,
            400,
            1.0
        );

    expect(
        first.filename == "hero-480.jpg",
        "Incorrect first image."
    );

    auto highDensity =
        ResponsiveImageSelector::select(
            candidates,
            600,
            2.0
        );

    expect(
        highDensity.filename == "hero-1200.jpg",
        "Incorrect DPR-aware image."
    );
}

void testAccessibility() {
    expect(
        !AccessibilityChecker::acceptableTouchTarget(
            32,
            32
        ),
        "32px target should fail the configured check."
    );

    expect(
        AccessibilityChecker::acceptableTouchTarget(
            44,
            44
        ),
        "44px target should pass the configured check."
    );
}

void testPerformance() {
    NetworkProfile network{
        "10 Mbps",
        10.0
    };

    const double time =
        PerformanceEstimator::transferSeconds(
            120,
            network
        );

    expect(
        time > 0.0,
        "Transfer time should be positive."
    );
}

void runTests() {
    testBreakpointSystem();
    testGrid();
    testTypography();
    testResponsiveImages();
    testAccessibility();
    testPerformance();

    std::cout
        << "\nAll C++ responsive-design tests passed.\n";
}

// ============================================================================
// 17. CASE STUDY DATA
// ============================================================================

Article createArticle(
    int id,
    const std::string& title,
    const std::string& category
) {
    return Article{
        id,
        title,
        category,
        8,
        {
            {"hero-480.jpg", 480},
            {"hero-768.jpg", 768},
            {"hero-1200.jpg", 1200},
            {"hero-1600.jpg", 1600},
            {"hero-2400.jpg", 2400}
        }
    };
}

// ============================================================================
// 18. MAIN PROGRAM
// ============================================================================

int main() {
    try {
        std::cout
            << "============================================================\n"
            << "RESPONSIVE WEB DESIGN CASE STUDY\n"
            << "============================================================\n";

        ArticleCatalog catalog;

        catalog.add(
            createArticle(
                1,
                "Designing Flexible Interfaces",
                "design"
            )
        );

        catalog.add(
            createArticle(
                2,
                "Responsive Performance Engineering",
                "performance"
            )
        );

        catalog.add(
            createArticle(
                3,
                "Accessible Responsive Components",
                "accessibility"
            )
        );

        for (const auto& article : catalog.all()) {
            ProductionValidator::validateArticle(article);
        }

        ResponsivePageRenderer renderer;

        const std::vector<Viewport> viewports = {
            Viewport(375, 812, 1.0, false),
            Viewport(768, 1024, 1.0, false),
            Viewport(1024, 768, 2.0, false),
            Viewport(1440, 900, 2.0, true)
        };

        std::cout
            << "\n---------------- RESPONSIVE RENDERING ----------------\n";

        for (const auto& viewport : viewports) {
            renderer.renderArticleSummary(
                catalog.all().front(),
                viewport
            );
        }

        std::cout
            << "\n---------------- RESPONSIVE IMAGE MARKUP ----------------\n";

        ImageMarkup markup({
            {"hero-480.jpg", 480},
            {"hero-768.jpg", 768},
            {"hero-1200.jpg", 1200},
            {"hero-1600.jpg", 1600}
        });

        std::cout
            << "srcset: "
            << markup.srcset()
            << "\n";

        std::cout
            << "sizes: "
            << markup.sizes()
            << "\n";

        std::cout
            << "\n---------------- ART DIRECTION ----------------\n";

        std::vector<ArtDirectedSource> artDirection = {
            {
                "fallback",
                0,
                "mobile-crop.jpg"
            },
            {
                "(min-width: 600px)",
                600,
                "tablet-crop.jpg"
            },
            {
                "(min-width: 900px)",
                900,
                "desktop-crop.jpg"
            }
        };

        for (const auto& viewport : viewports) {
            std::cout
                << viewport.width
                << "px -> "
                << ArtDirectionSelector::select(
                    artDirection,
                    viewport
                )
                << "\n";
        }

        std::cout
            << "\n---------------- IMAGE CROPPING ----------------\n";

        Dimensions covered =
            ImageCropCalculator::cover(
                2400,
                1600,
                800,
                500
            );

        std::cout
            << std::fixed
            << std::setprecision(2)
            << "Rendered cover dimensions: "
            << covered.width
            << "x"
            << covered.height
            << "\n";

        std::cout
            << "\n---------------- ACCESSIBILITY ----------------\n";

        std::cout
            << "32x32 target: "
            << (
                AccessibilityChecker::acceptableTouchTarget(
                    32,
                    32
                )
                ? "acceptable"
                : "below configured target"
            )
            << "\n";

        std::cout
            << "44x44 target: "
            << (
                AccessibilityChecker::acceptableTouchTarget(
                    44,
                    44
                )
                ? "acceptable"
                : "below configured target"
            )
            << "\n";

        std::cout
            << "\n---------------- PERFORMANCE ----------------\n";

        const NetworkProfile network{
            "Example 10 Mbps connection",
            10.0
        };

        const double mobileImageSeconds =
            PerformanceEstimator::transferSeconds(
                120,
                network
            );

        const double desktopImageSeconds =
            PerformanceEstimator::transferSeconds(
                900,
                network
            );

        std::cout
            << "120 KB image: "
            << mobileImageSeconds
            << " seconds idealized transfer\n";

        std::cout
            << "900 KB image: "
            << desktopImageSeconds
            << " seconds idealized transfer\n";

        std::cout
            << "\n---------------- CACHE MODEL ----------------\n";

        ImageCache cache;

        cache.store("hero-480.jpg", 120);
        cache.store("hero-1200.jpg", 420);

        std::cout
            << "Cached resources: "
            << cache.count()
            << "\n";

        std::cout
            << "hero-480.jpg cached: "
            << (
                cache.contains("hero-480.jpg")
                    ? "yes"
                    : "no"
            )
            << "\n";

        std::cout
            << "\n---------------- TESTS ----------------\n";

        runTests();

        std::cout
            << "\n---------------- ARCHITECTURAL NOTES ----------------\n";

        std::cout
            << "1. Base layout begins with one column.\n"
            << "2. Larger layouts are progressive enhancements.\n"
            << "3. Breakpoints are content-driven rather than device-specific.\n"
            << "4. Fluid typography avoids abrupt size changes.\n"
            << "5. srcset and sizes allow responsive image selection.\n"
            << "6. picture supports art direction when composition must change.\n"
            << "7. Accessibility is treated as a layout requirement.\n"
            << "8. Performance depends partly on transferring appropriate assets.\n"
            << "9. Client-side responsiveness is not a security boundary.\n"
            << "10. Production systems require real browser and device testing.\n";

        std::cout
            << "\nCase study completed successfully.\n";

        return 0;
    }
    catch (const std::exception& error) {
        std::cerr
            << "\nERROR: "
            << error.what()
            << "\n";

        return 1;
    }
}
