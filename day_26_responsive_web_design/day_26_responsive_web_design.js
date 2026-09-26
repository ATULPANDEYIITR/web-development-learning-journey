/*
 * Responsive Web Design
 * Mobile-first design, breakpoints, media queries,
 * responsive typography, and responsive images.
 *
 * This file is self-contained and can run in a modern browser or Node.js.
 * It demonstrates the logic behind responsive design and also produces a
 * complete responsive HTML document.
 */

"use strict";

// ============================================================================
// 1. CORE RESPONSIVE DESIGN DATA
// ============================================================================

const BREAKPOINTS = Object.freeze([
    Object.freeze({ name: "mobile", minWidth: 0 }),
    Object.freeze({ name: "tablet", minWidth: 600 }),
    Object.freeze({ name: "desktop", minWidth: 900 }),
    Object.freeze({ name: "wide", minWidth: 1200 })
]);

const RESPONSIVE_TERMS = Object.freeze({
    responsiveWebDesign:
        "A design approach in which layout, content, typography, images, and interaction adapt to available space and device characteristics.",
    mobileFirst:
        "A strategy that establishes the base experience for small screens and progressively enhances it at larger widths.",
    breakpoint:
        "A condition at which the layout changes because the current arrangement is no longer appropriate.",
    mediaQuery:
        "A CSS conditional mechanism that applies rules when media features satisfy specified conditions.",
    responsiveTypography:
        "Typography that adapts to available space using fluid units, clamping, readable measures, and controlled line lengths.",
    responsiveImage:
        "An image strategy that provides an appropriate source or rendering size for the user's conditions."
});

function assert(condition, message) {
    if (!condition) {
        throw new Error(message);
    }
}

// ============================================================================
// 2. BREAKPOINTS
// ============================================================================

function validateBreakpoints(breakpoints) {
    assert(Array.isArray(breakpoints), "Breakpoints must be an array.");
    assert(breakpoints.length > 0, "At least one breakpoint is required.");

    let previous = -1;

    for (const breakpoint of breakpoints) {
        assert(
            Number.isInteger(breakpoint.minWidth) &&
            breakpoint.minWidth >= 0,
            "Breakpoint widths must be non-negative integers."
        );

        assert(
            breakpoint.minWidth >= previous,
            "Breakpoints must be ordered by minimum width."
        );

        previous = breakpoint.minWidth;
    }
}

function getLayoutMode(viewportWidth, breakpoints = BREAKPOINTS) {
    assert(
        Number.isFinite(viewportWidth) && viewportWidth >= 0,
        "Viewport width must be a non-negative number."
    );

    validateBreakpoints(breakpoints);

    let active = breakpoints[0].name;

    for (const breakpoint of breakpoints) {
        if (viewportWidth >= breakpoint.minWidth) {
            active = breakpoint.name;
        } else {
            break;
        }
    }

    return active;
}

function getGridColumns(viewportWidth) {
    if (viewportWidth >= 1200) return 4;
    if (viewportWidth >= 900) return 3;
    if (viewportWidth >= 600) return 2;
    return 1;
}

// ============================================================================
// 3. MEDIA QUERY MODEL
// ============================================================================

class MediaQueryCondition {
    constructor({
        minWidth = null,
        maxWidth = null,
        orientation = null,
        prefersReducedMotion = null
    } = {}) {
        this.minWidth = minWidth;
        this.maxWidth = maxWidth;
        this.orientation = orientation;
        this.prefersReducedMotion = prefersReducedMotion;

        if (minWidth !== null) {
            assert(minWidth >= 0, "minWidth cannot be negative.");
        }

        if (maxWidth !== null) {
            assert(maxWidth >= 0, "maxWidth cannot be negative.");
        }

        if (orientation !== null) {
            assert(
                orientation === "portrait" ||
                orientation === "landscape",
                "Unsupported orientation."
            );
        }
    }

    matches(viewport) {
        const {
            width,
            height,
            reducedMotion = false
        } = viewport;

        assert(width > 0 && height > 0, "Viewport dimensions must be positive.");

        if (this.minWidth !== null && width < this.minWidth) {
            return false;
        }

        if (this.maxWidth !== null && width > this.maxWidth) {
            return false;
        }

        if (this.orientation !== null) {
            const actualOrientation =
                width >= height ? "landscape" : "portrait";

            if (actualOrientation !== this.orientation) {
                return false;
            }
        }

        if (
            this.prefersReducedMotion !== null &&
            reducedMotion !== this.prefersReducedMotion
        ) {
            return false;
        }

        return true;
    }
}

// ============================================================================
// 4. RESPONSIVE TYPOGRAPHY
// ============================================================================

function clamp(minimum, preferred, maximum) {
    assert(
        minimum <= maximum,
        "The minimum cannot be larger than the maximum."
    );

    return Math.max(minimum, Math.min(preferred, maximum));
}

function fluidFontSize(
    viewportWidth,
    minimumPx,
    slope,
    intercept,
    maximumPx
) {
    assert(viewportWidth > 0, "Viewport width must be positive.");
    assert(minimumPx > 0, "Minimum font size must be positive.");
    assert(maximumPx >= minimumPx, "Maximum font size is invalid.");

    const preferred = slope * viewportWidth + intercept;

    return clamp(
        minimumPx,
        preferred,
        maximumPx
    );
}

function pxToRem(px, rootFontSize = 16) {
    assert(rootFontSize > 0, "Root font size must be positive.");
    return px / rootFontSize;
}

function calculateReadableMeasure(
    viewportWidth,
    horizontalPadding = 24,
    maximumWidth = 720
) {
    assert(viewportWidth > 0, "Viewport width must be positive.");
    assert(horizontalPadding >= 0, "Padding cannot be negative.");
    assert(maximumWidth > 0, "Maximum width must be positive.");

    const available =
        viewportWidth - horizontalPadding * 2;

    return Math.max(
        0,
        Math.min(available, maximumWidth)
    );
}

// ============================================================================
// 5. RESPONSIVE IMAGES
// ============================================================================

class ImageCandidate {
    constructor(name, width, density = 1) {
        assert(typeof name === "string" && name.length > 0, "Invalid name.");
        assert(width > 0, "Image width must be positive.");
        assert(density > 0, "Image density must be positive.");

        this.name = name;
        this.width = width;
        this.density = density;
    }

    get physicalWidth() {
        return this.width * this.density;
    }
}

function selectBestImage(
    candidates,
    renderedWidth,
    devicePixelRatio = 1
) {
    assert(candidates.length > 0, "No image candidates supplied.");
    assert(renderedWidth > 0, "Rendered width must be positive.");
    assert(devicePixelRatio > 0, "Device pixel ratio must be positive.");

    const requiredWidth =
        renderedWidth * devicePixelRatio;

    const ordered = [...candidates].sort(
        (a, b) => a.physicalWidth - b.physicalWidth
    );

    return (
        ordered.find(
            candidate => candidate.physicalWidth >= requiredWidth
        ) || ordered[ordered.length - 1]
    );
}

function generateSrcset(candidates) {
    return [...candidates]
        .sort((a, b) => a.width - b.width)
        .map(candidate => `${candidate.name} ${candidate.width}w`)
        .join(", ");
}

function generateSizes() {
    /*
     * sizes tells the browser approximately how wide the image will render.
     * This allows the browser to choose an appropriate srcset candidate.
     */
    return [
        "(min-width: 1200px) 25vw",
        "(min-width: 900px) 33vw",
        "(min-width: 600px) 50vw",
        "100vw"
    ].join(", ");
}

// ============================================================================
// 6. ART DIRECTION
// ============================================================================

class ImageSource {
    constructor({
        media = null,
        source,
        width,
        height
    }) {
        assert(source, "Image source is required.");
        assert(width > 0 && height > 0, "Invalid image dimensions.");

        this.media = media;
        this.source = source;
        this.width = width;
        this.height = height;
    }

    get aspectRatio() {
        return this.width / this.height;
    }
}

function selectArtDirectedSource(sources, viewportWidth) {
    /*
     * This is a simplified model of <picture> source ordering.
     * In actual HTML, the browser evaluates <source media="..."> conditions.
     */
    for (const source of sources) {
        if (source.media === null) {
            continue;
        }

        const match = source.media.match(
            /min-width:\s*(\d+)px/
        );

        if (match && viewportWidth >= Number(match[1])) {
            return source;
        }
    }

    return sources.find(source => source.media === null) || null;
}

// ============================================================================
// 7. LAYOUT CALCULATIONS
// ============================================================================

function calculateCardWidth(
    viewportWidth,
    columnCount,
    gap = 16,
    horizontalPadding = 32
) {
    assert(viewportWidth > 0, "Viewport width must be positive.");
    assert(columnCount > 0, "Column count must be positive.");
    assert(gap >= 0, "Gap cannot be negative.");
    assert(horizontalPadding >= 0, "Padding cannot be negative.");

    const available =
        viewportWidth - horizontalPadding * 2;

    const totalGap = gap * (columnCount - 1);

    return Math.max(
        0,
        (available - totalGap) / columnCount
    );
}

function calculateCoverDimensions(
    sourceWidth,
    sourceHeight,
    containerWidth,
    containerHeight
) {
    assert(
        sourceWidth > 0 &&
        sourceHeight > 0 &&
        containerWidth > 0 &&
        containerHeight > 0,
        "All dimensions must be positive."
    );

    const scale = Math.max(
        containerWidth / sourceWidth,
        containerHeight / sourceHeight
    );

    return {
        width: sourceWidth * scale,
        height: sourceHeight * scale
    };
}

// ============================================================================
// 8. CSS GENERATION
// ============================================================================

const RESPONSIVE_CSS = `
:root {
    --content-max: 72rem;
    --page-padding: 1rem;
    --gap: 1rem;
    --heading-size: clamp(1.75rem, 4vw + 0.5rem, 3.5rem);
}

*,
*::before,
*::after {
    box-sizing: border-box;
}

html {
    font-size: 100%;
    scroll-behavior: smooth;
}

body {
    margin: 0;
    font-family:
        system-ui,
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
    line-height: 1.6;
}

img {
    display: block;
    max-width: 100%;
    height: auto;
}

.page-shell {
    width: min(
        calc(100% - 2rem),
        var(--content-max)
    );
    margin-inline: auto;
}

.hero-title {
    font-size: var(--heading-size);
    line-height: 1.05;
}

.content-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: var(--gap);
}

.cards {
    display: grid;
    grid-template-columns: 1fr;
    gap: var(--gap);
}

.card-image {
    width: 100%;
    aspect-ratio: 16 / 9;
    object-fit: cover;
}

@media (min-width: 600px) {
    .cards {
        grid-template-columns:
            repeat(2, minmax(0, 1fr));
    }
}

@media (min-width: 900px) {
    .content-grid {
        grid-template-columns:
            minmax(0, 2fr)
            minmax(16rem, 1fr);
    }

    .cards {
        grid-template-columns:
            repeat(3, minmax(0, 1fr));
    }
}

@media (min-width: 1200px) {
    .cards {
        grid-template-columns:
            repeat(4, minmax(0, 1fr));
    }
}

@media (prefers-reduced-motion: reduce) {
    html {
        scroll-behavior: auto;
    }

    *,
    *::before,
    *::after {
        animation-duration: 0.01ms !important;
        transition-duration: 0.01ms !important;
    }
}

@media (orientation: landscape) and (max-width: 800px) {
    .hero {
        padding-block: 1.5rem;
    }
}
`;

// ============================================================================
// 9. COMPLETE RESPONSIVE HTML
// ============================================================================

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function createCard(number) {
    const seed = `responsive-${number}`;

    return `
        <article class="card">
            <img
                class="card-image"
                src="https://picsum.photos/seed/${seed}/800/450"
                srcset="
                    https://picsum.photos/seed/${seed}/480/270 480w,
                    https://picsum.photos/seed/${seed}/800/450 800w,
                    https://picsum.photos/seed/${seed}/1200/675 1200w
                "
                sizes="${generateSizes()}"
                alt="Responsive design demonstration ${number}"
                width="1200"
                height="675"
                loading="lazy"
            >
            <div class="card-content">
                <h2>Responsive Card ${number}</h2>
                <p>
                    This card moves from a single column on small screens
                    to multiple columns as the viewport expands.
                </p>
            </div>
        </article>
    `;
}

function generateResponsiveHtml() {
    const cards = Array.from(
        { length: 8 },
        (_, index) => createCard(index + 1)
    ).join("\n");

    return `<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta
        name="viewport"
        content="width=device-width, initial-scale=1"
    >
    <title>Responsive Web Design Demonstration</title>
    <style>
        ${RESPONSIVE_CSS}

        body {
            background: #0b1020;
            color: #edf2f7;
        }

        .site-header {
            padding-block: 1rem;
            border-bottom: 1px solid #334155;
        }

        .navigation {
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
            justify-content: space-between;
            align-items: center;
        }

        .navigation-links {
            display: flex;
            flex-wrap: wrap;
            gap: 0.75rem;
            list-style: none;
            padding: 0;
            margin: 0;
        }

        .hero {
            padding-block: clamp(2rem, 8vw, 7rem);
        }

        .hero-copy {
            max-width: 48rem;
        }

        .cards {
            margin-block: 2rem;
        }

        .card {
            overflow: hidden;
            border: 1px solid #334155;
            border-radius: 1rem;
            background: #111827;
        }

        .card-content {
            padding: 1rem;
        }

        a {
            color: #93c5fd;
        }

        :focus-visible {
            outline: 3px solid #fbbf24;
            outline-offset: 3px;
        }

        .feature-image {
            width: 100%;
            border-radius: 1rem;
        }
    </style>
</head>
<body>
    <header class="site-header">
        <div class="page-shell navigation">
            <strong>Responsive Lab</strong>

            <nav aria-label="Primary navigation">
                <ul class="navigation-links">
                    <li><a href="#principles">Principles</a></li>
                    <li><a href="#cards">Cards</a></li>
                    <li><a href="#images">Images</a></li>
                </ul>
            </nav>
        </div>
    </header>

    <main>
        <section
            class="page-shell hero"
            id="principles"
        >
            <div class="hero-copy">
                <p>Mobile-first responsive architecture</p>

                <h1 class="hero-title">
                    One interface adapting to many viewports
                </h1>

                <p>
                    This implementation combines flexible layout,
                    responsive typography, responsive images, accessibility,
                    and progressive enhancement.
                </p>
            </div>
        </section>

        <section
            class="page-shell"
            id="cards"
            aria-labelledby="cards-heading"
        >
            <h2 id="cards-heading">Responsive card grid</h2>
            <div class="cards">
                ${cards}
            </div>
        </section>

        <section
            class="page-shell hero"
            id="images"
            aria-labelledby="image-heading"
        >
            <h2 id="image-heading">
                Art-directed responsive image
            </h2>

            <picture>
                <source
                    media="(min-width: 900px)"
                    srcset="https://picsum.photos/seed/desktop/1600/700"
                >

                <source
                    media="(min-width: 600px)"
                    srcset="https://picsum.photos/seed/tablet/1000/650"
                >

                <img
                    class="feature-image"
                    src="https://picsum.photos/seed/mobile/700/700"
                    alt="Example of art-directed responsive imagery"
                    width="700"
                    height="700"
                    loading="lazy"
                >
            </picture>
        </section>
    </main>
</body>
</html>`;
}

// ============================================================================
// 10. BROWSER-SIDE BEHAVIOR
// ============================================================================

function setupBrowserDiagnostics() {
    if (typeof window === "undefined") {
        return;
    }

    const updateDiagnostics = () => {
        const width = window.innerWidth;
        const height = window.innerHeight;

        const diagnostic = document.querySelector("#responsive-status");

        if (!diagnostic) {
            return;
        }

        diagnostic.textContent =
            `Viewport: ${width}×${height} | ` +
            `Mode: ${getLayoutMode(width)} | ` +
            `Columns: ${getGridColumns(width)}`;
    };

    window.addEventListener(
        "resize",
        updateDiagnostics,
        { passive: true }
    );

    updateDiagnostics();
}

// ============================================================================
// 11. ACCESSIBILITY
// ============================================================================

function hasAcceptableTouchTarget(
    width,
    height,
    minimum = 44
) {
    assert(width > 0 && height > 0, "Invalid target dimensions.");
    assert(minimum > 0, "Minimum target size must be positive.");

    return width >= minimum && height >= minimum;
}

function prefersReducedMotion() {
    if (typeof window === "undefined" || !window.matchMedia) {
        return false;
    }

    return window.matchMedia(
        "(prefers-reduced-motion: reduce)"
    ).matches;
}

// ============================================================================
// 12. PERFORMANCE CALCULATIONS
// ============================================================================

function estimateTransferTimeSeconds(
    kilobytes,
    megabitsPerSecond
) {
    assert(kilobytes >= 0, "Resource size cannot be negative.");
    assert(
        megabitsPerSecond > 0,
        "Network speed must be positive."
    );

    const megabits = (kilobytes * 8) / 1000;

    return megabits / megabitsPerSecond;
}

function compareImageTransfers() {
    const mobileImage = 120;
    const desktopImage = 900;
    const networkSpeed = 10;

    return {
        mobileSeconds: estimateTransferTimeSeconds(
            mobileImage,
            networkSpeed
        ),
        desktopSeconds: estimateTransferTimeSeconds(
            desktopImage,
            networkSpeed
        )
    };
}

// ============================================================================
// 13. VALIDATION AND TESTING
// ============================================================================

function testBreakpoints() {
    assert(
        getLayoutMode(375) === "mobile",
        "375px should use mobile mode."
    );

    assert(
        getLayoutMode(768) === "tablet",
        "768px should use tablet mode."
    );

    assert(
        getLayoutMode(1024) === "desktop",
        "1024px should use desktop mode."
    );

    assert(
        getLayoutMode(1440) === "wide",
        "1440px should use wide mode."
    );
}

function testTypography() {
    const small = fluidFontSize(
        320,
        28,
        0.025,
        12,
        56
    );

    const large = fluidFontSize(
        2000,
        28,
        0.025,
        12,
        56
    );

    assert(small >= 28, "Font size fell below minimum.");
    assert(large <= 56, "Font size exceeded maximum.");
}

function testImages() {
    const candidates = [
        new ImageCandidate("480", 480),
        new ImageCandidate("800", 800),
        new ImageCandidate("1200", 1200)
    ];

    assert(
        selectBestImage(candidates, 400).name === "480",
        "Incorrect 1x image selection."
    );

    assert(
        selectBestImage(candidates, 600).name === "800",
        "Incorrect image selection."
    );

    assert(
        selectBestImage(candidates, 600, 2).name === "1200",
        "Incorrect DPR-aware selection."
    );
}

function testMediaQueries() {
    const tablet = new MediaQueryCondition({
        minWidth: 600
    });

    assert(
        !tablet.matches({ width: 599, height: 800 }),
        "Tablet query matched too early."
    );

    assert(
        tablet.matches({ width: 600, height: 800 }),
        "Tablet query did not match at threshold."
    );

    const portrait = new MediaQueryCondition({
        orientation: "portrait"
    });

    assert(
        portrait.matches({
            width: 600,
            height: 800
        }),
        "Portrait condition failed."
    );
}

function testLayoutMath() {
    const cardWidth = calculateCardWidth(
        1200,
        4,
        16,
        32
    );

    assert(
        Math.abs(cardWidth - 276) < 0.0001,
        "Card-width calculation is incorrect."
    );

    const covered = calculateCoverDimensions(
        1600,
        900,
        800,
        800
    );

    assert(
        covered.width >= 800 &&
        covered.height >= 800,
        "Cover calculation does not cover container."
    );
}

function runTests() {
    testBreakpoints();
    testTypography();
    testImages();
    testMediaQueries();
    testLayoutMath();

    return "All responsive-design JavaScript tests passed.";
}

// ============================================================================
// 14. DEMONSTRATIONS
// ============================================================================

function runDemonstrations() {
    console.log("=".repeat(78));
    console.log("RESPONSIVE WEB DESIGN JAVASCRIPT STUDY");
    console.log("=".repeat(78));

    console.log("\nCore concepts:");

    for (const [name, description] of Object.entries(
        RESPONSIVE_TERMS
    )) {
        console.log(`\n${name}`);
        console.log(`  ${description}`);
    }

    console.log("\nBreakpoint demonstration:");

    for (const width of [
        320,
        375,
        600,
        768,
        900,
        1024,
        1200,
        1440
    ]) {
        console.log(
            `${width}px -> ${getLayoutMode(width)} -> ` +
            `${getGridColumns(width)} column(s)`
        );
    }

    console.log("\nResponsive typography:");

    for (const width of [
        320,
        375,
        600,
        768,
        1024,
        1440,
        1920
    ]) {
        const px = fluidFontSize(
            width,
            28,
            0.025,
            12,
            56
        );

        console.log(
            `${width}px -> ${px.toFixed(1)}px -> ` +
            `${pxToRem(px).toFixed(2)}rem`
        );
    }

    console.log("\nResponsive images:");

    const candidates = [
        new ImageCandidate("hero-480.jpg", 480),
        new ImageCandidate("hero-768.jpg", 768),
        new ImageCandidate("hero-1200.jpg", 1200),
        new ImageCandidate("hero-1600.jpg", 1600),
        new ImageCandidate("hero-2400.jpg", 2400)
    ];

    console.log(generateSrcset(candidates));

    for (const [width, dpr] of [
        [320, 1],
        [375, 2],
        [768, 1],
        [900, 2],
        [1440, 2]
    ]) {
        const selected = selectBestImage(
            candidates,
            width,
            dpr
        );

        console.log(
            `${width}px at DPR ${dpr} -> ${selected.name}`
        );
    }

    console.log("\nAccessibility:");
    console.log(
        `32×32 touch target -> ${
            hasAcceptableTouchTarget(32, 32)
        }`
    );
    console.log(
        `44×44 touch target -> ${
            hasAcceptableTouchTarget(44, 44)
        }`
    );

    console.log("\nPerformance:");
    console.log(compareImageTransfers());

    console.log("\nGenerated HTML length:");
    console.log(`${generateResponsiveHtml().length} characters`);

    console.log("\nTests:");
    console.log(runTests());

    if (typeof document !== "undefined") {
        setupBrowserDiagnostics();
    }

    if (typeof window !== "undefined") {
        console.log(
            `Reduced-motion preference: ${prefersReducedMotion()}`
        );
    }
}

// ============================================================================
// 15. NODE.JS EXPORT / BROWSER EXECUTION
// ============================================================================

if (typeof module !== "undefined" && module.exports) {
    module.exports = {
        BREAKPOINTS,
        MediaQueryCondition,
        ImageCandidate,
        getLayoutMode,
        getGridColumns,
        fluidFontSize,
        pxToRem,
        calculateReadableMeasure,
        selectBestImage,
        generateSrcset,
        generateSizes,
        ImageSource,
        selectArtDirectedSource,
        calculateCardWidth,
        calculateCoverDimensions,
        generateResponsiveHtml,
        hasAcceptableTouchTarget,
        estimateTransferTimeSeconds,
        compareImageTransfers,
        runTests
    };
}

if (typeof document !== "undefined") {
    document.addEventListener(
        "DOMContentLoaded",
        setupBrowserDiagnostics
    );
}

if (
    typeof process !== "undefined" &&
    process.argv &&
    import.meta.url === `file://${process.argv[1]}`
) {
    runDemonstrations();
}
