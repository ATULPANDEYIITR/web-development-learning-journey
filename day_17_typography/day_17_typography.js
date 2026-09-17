/*
 * Typography Study Laboratory
 *
 * Topic:
 * Font families, web fonts, font weight, line height, letter spacing,
 * text alignment, and typography hierarchy.
 *
 * This file complements the Python implementation by focusing on:
 * - JavaScript data modeling
 * - Browser-oriented CSS generation
 * - Responsive typography calculations
 * - Font loading concepts
 * - DOM integration
 * - Validation
 * - Performance-oriented font configuration
 * - A practical typography preview system
 *
 * The file runs in Node.js without external packages.
 * When loaded in a browser, the optional DOM demonstration becomes active.
 */

"use strict";

// -----------------------------------------------------------------------------
// 1. Fundamental typography model
// -----------------------------------------------------------------------------

const typographyConcepts = {
    fontFamily: "The typeface family used to render text.",
    fontWeight: "The thickness or emphasis level of a font.",
    fontSize: "The nominal size assigned to text.",
    lineHeight: "The vertical spacing allocated to each line.",
    letterSpacing: "Additional horizontal spacing between characters.",
    textAlign: "Horizontal alignment inside the text box.",
    hierarchy: "Visual ordering that communicates relative importance."
};

console.log("TYPOGRAPHY CONCEPTS");
console.table(typographyConcepts);


// -----------------------------------------------------------------------------
// 2. Font-family classifications
// -----------------------------------------------------------------------------

const fontFamilies = {
    serif: ["Georgia", "Times New Roman", "Garamond"],
    sansSerif: ["Inter", "Arial", "Helvetica", "Roboto"],
    monospace: ["Consolas", "Courier New", "Monaco"],
    cursive: ["Comic Sans MS", "Brush Script MT"],
    fantasy: ["Impact", "Papyrus"]
};

console.log("\nFONT FAMILIES");
console.table(fontFamilies);


// -----------------------------------------------------------------------------
// 3. Font stacks
// -----------------------------------------------------------------------------

function quoteFontFamily(family) {
    return family.includes(" ") ? `"${family}"` : family;
}

function buildFontStack(primary, fallbacks, genericFamily) {
    return [primary, ...fallbacks, genericFamily]
        .map(quoteFontFamily)
        .join(", ");
}

const interfaceFontStack = buildFontStack(
    "Inter",
    ["Arial", "Helvetica"],
    "sans-serif"
);

console.log("\nFONT STACK:");
console.log(interfaceFontStack);


// -----------------------------------------------------------------------------
// 4. CSS font-weight model
// -----------------------------------------------------------------------------

const fontWeights = Object.freeze({
    100: "Thin",
    200: "Extra Light",
    300: "Light",
    400: "Normal",
    500: "Medium",
    600: "Semi Bold",
    700: "Bold",
    800: "Extra Bold",
    900: "Black"
});

function validateFontWeight(weight) {
    return Object.prototype.hasOwnProperty.call(fontWeights, weight);
}

function describeFontWeight(weight) {
    if (!validateFontWeight(weight)) {
        throw new RangeError("Invalid CSS font weight.");
    }

    return fontWeights[weight];
}

console.log("\nFONT WEIGHT EXAMPLES");
for (const weight of [400, 500, 600, 700]) {
    console.log(weight, describeFontWeight(weight));
}


// -----------------------------------------------------------------------------
// 5. Typography style object
// -----------------------------------------------------------------------------

class TypographyStyle {
    constructor({
        name,
        fontFamily,
        fontSizeRem,
        fontWeight,
        lineHeight,
        letterSpacingEm = 0,
        textAlign = "left"
    }) {
        this.name = name;
        this.fontFamily = fontFamily;
        this.fontSizeRem = fontSizeRem;
        this.fontWeight = fontWeight;
        this.lineHeight = lineHeight;
        this.letterSpacingEm = letterSpacingEm;
        this.textAlign = textAlign;
    }

    validate() {
        const errors = [];

        if (!this.name) {
            errors.push("A style name is required.");
        }

        if (!this.fontFamily) {
            errors.push("A font family is required.");
        }

        if (!(this.fontSizeRem > 0)) {
            errors.push("Font size must be positive.");
        }

        if (!validateFontWeight(this.fontWeight)) {
            errors.push("Font weight must be between 100 and 900.");
        }

        if (!(this.lineHeight > 0)) {
            errors.push("Line height must be positive.");
        }

        if (!["left", "right", "center", "justify"].includes(this.textAlign)) {
            errors.push("Unsupported text alignment.");
        }

        return errors;
    }

    toCSS(selector) {
        const errors = this.validate();

        if (errors.length > 0) {
            throw new Error(
                `${this.name}: ${errors.join(" ")}`
            );
        }

        return [
            `${selector} {`,
            `  font-family: ${this.fontFamily};`,
            `  font-size: ${this.fontSizeRem}rem;`,
            `  font-weight: ${this.fontWeight};`,
            `  line-height: ${this.lineHeight};`,
            `  letter-spacing: ${this.letterSpacingEm}em;`,
            `  text-align: ${this.textAlign};`,
            `}`
        ].join("\n");
    }
}


// -----------------------------------------------------------------------------
// 6. Typography hierarchy
// -----------------------------------------------------------------------------

const typographyHierarchy = [
    new TypographyStyle({
        name: "display",
        fontFamily: interfaceFontStack,
        fontSizeRem: 3.5,
        fontWeight: 700,
        lineHeight: 1.05,
        letterSpacingEm: -0.02
    }),

    new TypographyStyle({
        name: "heading-1",
        fontFamily: interfaceFontStack,
        fontSizeRem: 2.5,
        fontWeight: 700,
        lineHeight: 1.15,
        letterSpacingEm: -0.015
    }),

    new TypographyStyle({
        name: "heading-2",
        fontFamily: interfaceFontStack,
        fontSizeRem: 2,
        fontWeight: 700,
        lineHeight: 1.2,
        letterSpacingEm: -0.01
    }),

    new TypographyStyle({
        name: "heading-3",
        fontFamily: interfaceFontStack,
        fontSizeRem: 1.5,
        fontWeight: 600,
        lineHeight: 1.25,
        letterSpacingEm: -0.005
    }),

    new TypographyStyle({
        name: "body",
        fontFamily: interfaceFontStack,
        fontSizeRem: 1,
        fontWeight: 400,
        lineHeight: 1.6
    }),

    new TypographyStyle({
        name: "small",
        fontFamily: interfaceFontStack,
        fontSizeRem: 0.875,
        fontWeight: 400,
        lineHeight: 1.5,
        letterSpacingEm: 0.005
    })
];

console.log("\nTYPOGRAPHY HIERARCHY");
for (const style of typographyHierarchy) {
    console.log(
        `${style.name}: ${style.fontSizeRem}rem / ` +
        `${style.lineHeight}, weight ${style.fontWeight}`
    );
}


// -----------------------------------------------------------------------------
// 7. Modular type scale
// -----------------------------------------------------------------------------

function createTypeScale(baseRem, ratio, minimumStep, maximumStep) {
    if (baseRem <= 0 || ratio <= 0) {
        throw new RangeError("Base size and ratio must be positive.");
    }

    const scale = {};

    for (let step = minimumStep; step <= maximumStep; step += 1) {
        scale[step] = baseRem * Math.pow(ratio, step);
    }

    return scale;
}

const typeScale = createTypeScale(1, 1.25, -2, 4);

console.log("\nMODULAR TYPE SCALE");
console.table(typeScale);


// -----------------------------------------------------------------------------
// 8. Responsive font-size calculation
// -----------------------------------------------------------------------------

function clamp(minimum, preferred, maximum) {
    return Math.min(Math.max(preferred, minimum), maximum);
}

function responsiveHeadingSize(viewportWidth) {
    // This approximates CSS:
    // font-size: clamp(2rem, 4vw, 3.5rem);
    const preferred = viewportWidth * 0.04;
    return clamp(2, preferred / 16, 3.5);
}

console.log("\nRESPONSIVE TYPE");
for (const viewportWidth of [320, 768, 1024, 1440, 1920]) {
    console.log(
        `${viewportWidth}px -> ` +
        `${responsiveHeadingSize(viewportWidth).toFixed(2)}rem`
    );
}


// -----------------------------------------------------------------------------
// 9. Letter-spacing calculations
// -----------------------------------------------------------------------------

function calculateTracking(fontSizePx, trackingEm) {
    if (fontSizePx <= 0) {
        throw new RangeError("Font size must be positive.");
    }

    return fontSizePx * trackingEm;
}

console.log("\nLETTER SPACING");
for (const tracking of [-0.02, 0, 0.01, 0.04]) {
    console.log(
        `${tracking}em at 16px = ` +
        `${calculateTracking(16, tracking).toFixed(3)}px`
    );
}


// -----------------------------------------------------------------------------
// 10. Readability-oriented line-height model
// -----------------------------------------------------------------------------

function calculateLineHeight(fontSizePx, lineHeight) {
    if (fontSizePx <= 0 || lineHeight <= 0) {
        throw new RangeError("Font size and line height must be positive.");
    }

    return fontSizePx * lineHeight;
}

function readabilityReport(style) {
    const warnings = [];

    if (style.fontSizeRem < 0.75) {
        warnings.push("Text is unusually small.");
    }

    if (style.lineHeight < 1.2) {
        warnings.push("Line height is tight.");
    }

    if (Math.abs(style.letterSpacingEm) > 0.08) {
        warnings.push("Letter spacing is unusually large.");
    }

    if (style.fontWeight === 300 && style.fontSizeRem < 0.875) {
        warnings.push("Light weight combined with small text may reduce legibility.");
    }

    return {
        passed: warnings.length === 0,
        warnings
    };
}

console.log("\nREADABILITY REPORT");
for (const style of typographyHierarchy) {
    console.log(style.name, readabilityReport(style));
}


// -----------------------------------------------------------------------------
// 11. Web-font declarations
// -----------------------------------------------------------------------------

const webFont = {
    family: "Inter",
    weights: [
        { weight: 400, file: "/fonts/inter-400.woff2" },
        { weight: 600, file: "/fonts/inter-600.woff2" },
        { weight: 700, file: "/fonts/inter-700.woff2" }
    ],
    format: "woff2",
    display: "swap"
};

function generateFontFaceCSS(font) {
    return font.weights.map(({ weight, file }) => {
        return [
            "@font-face {",
            `  font-family: "${font.family}";`,
            `  src: url("${file}") format("${font.format}");`,
            `  font-weight: ${weight};`,
            "  font-style: normal;",
            `  font-display: ${font.display};`,
            "}"
        ].join("\n");
    }).join("\n\n");
}

console.log("\nWEB-FONT CSS");
console.log(generateFontFaceCSS(webFont));


// -----------------------------------------------------------------------------
// 12. Font loading strategy
// -----------------------------------------------------------------------------

async function demonstrateFontLoading() {
    /*
     * document.fonts is browser-specific. This function deliberately checks
     * for its existence so that the file remains executable in Node.js.
     */
    if (typeof document === "undefined" || !document.fonts) {
        return {
            supported: false,
            message: "Font Loading API is unavailable in this runtime."
        };
    }

    await document.fonts.ready;

    return {
        supported: true,
        status: document.fonts.status
    };
}


// -----------------------------------------------------------------------------
// 13. Typography design tokens
// -----------------------------------------------------------------------------

const typographyTokens = Object.freeze({
    display: {
        size: "clamp(2rem, 4vw, 3.5rem)",
        weight: 700,
        lineHeight: 1.05,
        tracking: "-0.02em"
    },

    heading1: {
        size: "clamp(1.9rem, 3vw, 2.5rem)",
        weight: 700,
        lineHeight: 1.15,
        tracking: "-0.015em"
    },

    heading2: {
        size: "clamp(1.6rem, 2.5vw, 2rem)",
        weight: 700,
        lineHeight: 1.2,
        tracking: "-0.01em"
    },

    body: {
        size: "1rem",
        weight: 400,
        lineHeight: 1.6,
        tracking: "0"
    },

    small: {
        size: "0.875rem",
        weight: 400,
        lineHeight: 1.5,
        tracking: "0.005em"
    }
});

console.log("\nTYPOGRAPHY TOKENS");
console.dir(typographyTokens, { depth: null });


// -----------------------------------------------------------------------------
// 14. Generate a complete CSS variable system
// -----------------------------------------------------------------------------

function generateTypographyVariables(tokens) {
    const lines = [":root {"];

    for (const [name, token] of Object.entries(tokens)) {
        lines.push(`  --type-${name}-size: ${token.size};`);
        lines.push(`  --type-${name}-weight: ${token.weight};`);
        lines.push(`  --type-${name}-line: ${token.lineHeight};`);
        lines.push(`  --type-${name}-tracking: ${token.tracking};`);
    }

    lines.push("}");

    return lines.join("\n");
}

console.log("\nCSS VARIABLES");
console.log(generateTypographyVariables(typographyTokens));


// -----------------------------------------------------------------------------
// 15. Alignment decision model
// -----------------------------------------------------------------------------

function recommendAlignment(contentType) {
    const normalized = contentType.trim().toLowerCase();

    if (["paragraph", "article", "documentation", "body"].includes(normalized)) {
        return "left";
    }

    if (["numeric-data", "table-number"].includes(normalized)) {
        return "right";
    }

    if (["badge", "short-label"].includes(normalized)) {
        return "center";
    }

    return "left";
}

console.log("\nALIGNMENT EXAMPLES");

for (const contentType of [
    "paragraph",
    "documentation",
    "numeric-data",
    "badge",
    "heading"
]) {
    console.log(
        `${contentType}: ${recommendAlignment(contentType)}`
    );
}


// -----------------------------------------------------------------------------
// 16. Font fallback simulation
// -----------------------------------------------------------------------------

function chooseAvailableFont(fontStack, availableFonts) {
    const normalizedAvailable = new Set(
        availableFonts.map(font => font.toLowerCase())
    );

    for (const family of fontStack) {
        if (normalizedAvailable.has(family.toLowerCase())) {
            return family;
        }
    }

    return "generic fallback";
}

const requestedFonts = [
    "Inter",
    "Arial",
    "Helvetica",
    "sans-serif"
];

console.log("\nFONT FALLBACK");

console.log(
    chooseAvailableFont(
        requestedFonts,
        ["Arial", "Consolas"]
    )
);


// -----------------------------------------------------------------------------
// 17. Performance analysis
// -----------------------------------------------------------------------------

function analyzeFontPayload(fontFiles) {
    const totalBytes = fontFiles.reduce(
        (total, font) => total + font.sizeBytes,
        0
    );

    const weightCount = new Set(
        fontFiles.map(font => font.weight)
    ).size;

    return {
        totalBytes,
        totalKilobytes: totalBytes / 1024,
        weightCount,
        averageBytesPerWeight: totalBytes / Math.max(weightCount, 1)
    };
}

const fontFiles = [
    { weight: 400, sizeBytes: 32000 },
    { weight: 600, sizeBytes: 34000 },
    { weight: 700, sizeBytes: 35000 }
];

console.log("\nFONT PAYLOAD ANALYSIS");
console.table(analyzeFontPayload(fontFiles));


// -----------------------------------------------------------------------------
// 18. CSS generation from the hierarchy
// -----------------------------------------------------------------------------

function generateTypographyCSS(styles) {
    return styles
        .map(style => style.toCSS(`.type-${style.name}`))
        .join("\n\n");
}

const generatedCSS = generateTypographyCSS(typographyHierarchy);

console.log("\nGENERATED TYPOGRAPHY CSS");
console.log(generatedCSS);


// -----------------------------------------------------------------------------
// 19. Browser-side typography preview
// -----------------------------------------------------------------------------

function createTypographyPreview() {
    if (typeof document === "undefined") {
        return null;
    }

    const container = document.createElement("main");
    container.className = "typography-preview";

    const heading = document.createElement("h1");
    heading.textContent = "Typography hierarchy";
    heading.className = "type-heading-1";

    const subheading = document.createElement("h2");
    subheading.textContent = "Font, spacing, rhythm, and alignment";
    subheading.className = "type-heading-2";

    const paragraph = document.createElement("p");
    paragraph.textContent =
        "A typography system gives text a consistent visual structure " +
        "across a digital product.";
    paragraph.className = "type-body";

    container.append(heading, subheading, paragraph);

    return container;
}


// -----------------------------------------------------------------------------
// 20. Browser font loading demonstration
// -----------------------------------------------------------------------------

async function loadTypographyFont() {
    /*
     * FontFace allows an application to explicitly load a font.
     *
     * The URL is illustrative. A production application must point to an
     * actual font asset served by the application.
     */
    if (typeof FontFace === "undefined" || typeof document === "undefined") {
        return {
            loaded: false,
            reason: "FontFace API is unavailable."
        };
    }

    const font = new FontFace(
        "StudyFont",
        'url("/fonts/study-font-400.woff2") format("woff2")',
        {
            weight: "400",
            style: "normal"
        }
    );

    try {
        const loadedFont = await font.load();
        document.fonts.add(loadedFont);

        return {
            loaded: true,
            family: loadedFont.family
        };
    } catch (error) {
        return {
            loaded: false,
            reason: error instanceof Error ? error.message : String(error)
        };
    }
}


// -----------------------------------------------------------------------------
// 21. Variable-font concept
// -----------------------------------------------------------------------------

class VariableFontRange {
    constructor({
        family,
        minimumWeight = 100,
        maximumWeight = 900
    }) {
        this.family = family;
        this.minimumWeight = minimumWeight;
        this.maximumWeight = maximumWeight;
    }

    validateWeight(weight) {
        return (
            Number.isInteger(weight) &&
            weight >= this.minimumWeight &&
            weight <= this.maximumWeight
        );
    }

    css(weight) {
        if (!this.validateWeight(weight)) {
            throw new RangeError(
                `Weight must be between ${this.minimumWeight} and ` +
                `${this.maximumWeight}.`
            );
        }

        return `font-variation-settings: "wght" ${weight};`;
    }
}

const variableInter = new VariableFontRange({
    family: "Inter Variable"
});

console.log("\nVARIABLE FONT");
console.log(variableInter.css(575));


// -----------------------------------------------------------------------------
// 22. Text measure estimation
// -----------------------------------------------------------------------------

function estimateCharactersPerLine(containerWidthPx, averageCharacterWidthPx) {
    if (containerWidthPx <= 0 || averageCharacterWidthPx <= 0) {
        throw new RangeError("Dimensions must be positive.");
    }

    return Math.max(
        1,
        Math.floor(containerWidthPx / averageCharacterWidthPx)
    );
}

function estimateLineCount(text, containerWidthPx, averageCharacterWidthPx) {
    if (!text.trim()) {
        return 0;
    }

    const charactersPerLine = estimateCharactersPerLine(
        containerWidthPx,
        averageCharacterWidthPx
    );

    let lines = 1;
    let currentLength = 0;

    for (const word of text.trim().split(/\s+/)) {
        if (word.length > charactersPerLine) {
            if (currentLength > 0) {
                lines++;
                currentLength = 0;
            }

            lines += Math.ceil(word.length / charactersPerLine) - 1;
            currentLength = word.length % charactersPerLine;
            continue;
        }

        const requiredLength =
            currentLength === 0 ? word.length : word.length + 1;

        if (currentLength + requiredLength <= charactersPerLine) {
            currentLength += requiredLength;
        } else {
            lines++;
            currentLength = word.length;
        }
    }

    return lines;
}

const sampleText =
    "Typography controls structure, emphasis, rhythm, and readability.";

console.log("\nTEXT MEASURE");
for (const width of [280, 400, 600, 760]) {
    console.log(
        `${width}px -> approximately ` +
        `${estimateLineCount(sampleText, width, 8)} line(s)`
    );
}


// -----------------------------------------------------------------------------
// 23. Edge cases
// -----------------------------------------------------------------------------

console.log("\nEDGE CASES");

const edgeCases = [
    "",
    "A",
    "supercalifragilisticexpialidocious",
    "Typography    uses    whitespace.",
    "café हिन्दी 日本語"
];

for (const value of edgeCases) {
    console.log({
        text: value,
        estimatedLines: estimateLineCount(value, 300, 8)
    });
}


// -----------------------------------------------------------------------------
// 24. Security and reliability considerations
// -----------------------------------------------------------------------------

function sanitizeFontFamilyForCSS(family) {
    /*
     * This is a conservative validation function, not a complete CSS parser.
     * Applications should not directly concatenate untrusted user input into
     * CSS declarations.
     */
    if (
        typeof family !== "string" ||
        family.length === 0 ||
        family.length > 100
    ) {
        throw new TypeError("Invalid font family.");
    }

    if (/[{};]/.test(family)) {
        throw new Error("Potentially unsafe CSS characters detected.");
    }

    return family;
}

console.log("\nSAFE FONT-FAMILY VALIDATION");
console.log(sanitizeFontFamilyForCSS("Inter, Arial, sans-serif"));


// -----------------------------------------------------------------------------
// 25. Export reusable values for Node.js
// -----------------------------------------------------------------------------

const typographyStudy = {
    typographyConcepts,
    fontFamilies,
    fontWeights,
    typographyHierarchy,
    typographyTokens,
    buildFontStack,
    createTypeScale,
    generateTypographyCSS,
    calculateLineHeight,
    calculateTracking,
    readabilityReport,
    analyzeFontPayload,
    recommendAlignment,
    estimateLineCount
};

if (typeof module !== "undefined" && module.exports) {
    module.exports = typographyStudy;
}


// -----------------------------------------------------------------------------
// 26. Optional browser execution
// -----------------------------------------------------------------------------

if (typeof window !== "undefined" && typeof document !== "undefined") {
    const preview = createTypographyPreview();

    if (preview) {
        document.body.appendChild(preview);
    }

    const styleElement = document.createElement("style");
    styleElement.textContent = generatedCSS;
    document.head.appendChild(styleElement);
}


// -----------------------------------------------------------------------------
// 27. End-of-file study checklist
// -----------------------------------------------------------------------------

console.log("\nTYPOGRAPHY STUDY CHECKLIST");

const checklist = [
    "Use a coherent font-family strategy.",
    "Provide reliable fallback fonts.",
    "Load only the weights actually required.",
    "Use font size to establish scale.",
    "Use line height to establish vertical rhythm.",
    "Use letter spacing carefully.",
    "Choose text alignment according to content structure.",
    "Build hierarchy through multiple typographic properties.",
    "Test typography at multiple viewport sizes.",
    "Check small text and tight line-height combinations.",
    "Optimize font loading and file size.",
    "Validate Unicode and multilingual coverage.",
    "Do not inject untrusted values directly into CSS.",
    "Test typography with real content."
];

for (const item of checklist) {
    console.log(`[ ] ${item}`);
}
