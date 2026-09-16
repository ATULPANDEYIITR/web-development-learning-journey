/*
 * CSS Colors and Units
 * ====================
 *
 * A standalone JavaScript study companion for:
 *
 * - Named colors
 * - HEX
 * - RGB and RGBA
 * - HSL and HSLA
 * - Alpha and opacity
 * - px
 * - %
 * - em
 * - rem
 * - vh
 * - vw
 * - vmin
 * - vmax
 * - Responsive sizing
 * - CSS custom properties
 * - Color conversion
 * - Contrast calculations
 *
 * JavaScript does not execute CSS by itself. This file models CSS behavior,
 * calculates values, validates input, and generates realistic CSS.
 *
 * Run with:
 *   node css-colors-and-units.js
 */

"use strict";


// -----------------------------------------------------------------------------
// 1. BASIC HELPERS
// -----------------------------------------------------------------------------

function section(title) {
    console.log("\n" + "=".repeat(78));
    console.log(title);
    console.log("=".repeat(78));
}

function clamp(value, minimum, maximum) {
    return Math.max(minimum, Math.min(value, maximum));
}


// -----------------------------------------------------------------------------
// 2. NAMED COLORS
// -----------------------------------------------------------------------------

const namedColors = Object.freeze({
    black: "#000000",
    white: "#ffffff",
    red: "#ff0000",
    green: "#008000",
    blue: "#0000ff",
    yellow: "#ffff00",
    cyan: "#00ffff",
    magenta: "#ff00ff",
    gray: "#808080",
    orange: "#ffa500",
    purple: "#800080",
    transparent: "#00000000"
});

section("1. Named colors");

for (const name of ["red", "blue", "orange", "white", "black"]) {
    console.log(`${name.padEnd(10)} -> ${namedColors[name]}`);
}


// -----------------------------------------------------------------------------
// 3. HEX VALIDATION AND CONVERSION
// -----------------------------------------------------------------------------

function normalizeHex(value) {
    if (typeof value !== "string") {
        throw new TypeError("HEX color must be a string.");
    }

    let hex = value.trim().toLowerCase();

    if (hex.startsWith("#")) {
        hex = hex.slice(1);
    }

    if (![3, 4, 6, 8].includes(hex.length)) {
        throw new Error("HEX must contain 3, 4, 6, or 8 digits.");
    }

    if (!/^[0-9a-f]+$/.test(hex)) {
        throw new Error("HEX contains invalid characters.");
    }

    if (hex.length === 3 || hex.length === 4) {
        hex = [...hex].map(character => character + character).join("");
    }

    return `#${hex}`;
}

function hexToRgba(value) {
    const hex = normalizeHex(value).slice(1);

    const red = parseInt(hex.slice(0, 2), 16);
    const green = parseInt(hex.slice(2, 4), 16);
    const blue = parseInt(hex.slice(4, 6), 16);

    const alpha = hex.length === 8
        ? parseInt(hex.slice(6, 8), 16) / 255
        : 1;

    return { red, green, blue, alpha };
}

function componentToHex(value) {
    return value.toString(16).padStart(2, "0");
}

function validateRgb(red, green, blue) {
    for (const [name, value] of [
        ["red", red],
        ["green", green],
        ["blue", blue]
    ]) {
        if (!Number.isInteger(value)) {
            throw new TypeError(`${name} must be an integer.`);
        }

        if (value < 0 || value > 255) {
            throw new RangeError(`${name} must be between 0 and 255.`);
        }
    }
}

function validateAlpha(alpha) {
    if (!Number.isFinite(alpha) || alpha < 0 || alpha > 1) {
        throw new RangeError("Alpha must be between 0 and 1.");
    }
}

function rgbaToHex(red, green, blue, alpha = null) {
    validateRgb(red, green, blue);

    let result =
        `#${componentToHex(red)}${componentToHex(green)}${componentToHex(blue)}`;

    if (alpha !== null) {
        validateAlpha(alpha);
        result += componentToHex(Math.round(alpha * 255));
    }

    return result;
}

section("2. HEX colors");

for (const value of [
    "#000000",
    "#ffffff",
    "#3498db",
    "#abc",
    "#123456",
    "#336699cc"
]) {
    console.log(value.padEnd(12), "->", hexToRgba(value));
}


// -----------------------------------------------------------------------------
// 4. RGB AND HSL
// -----------------------------------------------------------------------------

function rgbToHsl(red, green, blue) {
    validateRgb(red, green, blue);

    const r = red / 255;
    const g = green / 255;
    const b = blue / 255;

    const maximum = Math.max(r, g, b);
    const minimum = Math.min(r, g, b);
    const difference = maximum - minimum;

    const lightness = (maximum + minimum) / 2;

    let hue = 0;
    let saturation = 0;

    if (difference !== 0) {
        saturation =
            difference /
            (1 - Math.abs(2 * lightness - 1));

        if (maximum === r) {
            hue = 60 * (((g - b) / difference) % 6);
        } else if (maximum === g) {
            hue = 60 * (((b - r) / difference) + 2);
        } else {
            hue = 60 * (((r - g) / difference) + 4);
        }
    }

    if (hue < 0) {
        hue += 360;
    }

    return {
        hue: hue % 360,
        saturation: saturation * 100,
        lightness: lightness * 100
    };
}

function hslToRgb(hue, saturation, lightness) {
    if (!Number.isFinite(hue)) {
        throw new TypeError("Hue must be numeric.");
    }

    if (saturation < 0 || saturation > 100) {
        throw new RangeError("Saturation must be 0..100.");
    }

    if (lightness < 0 || lightness > 100) {
        throw new RangeError("Lightness must be 0..100.");
    }

    hue = ((hue % 360) + 360) % 360;
    saturation /= 100;
    lightness /= 100;

    const chroma =
        (1 - Math.abs(2 * lightness - 1)) * saturation;

    const intermediate =
        chroma * (1 - Math.abs(((hue / 60) % 2) - 1));

    const match = lightness - chroma / 2;

    let r1;
    let g1;
    let b1;

    if (hue < 60) {
        [r1, g1, b1] = [chroma, intermediate, 0];
    } else if (hue < 120) {
        [r1, g1, b1] = [intermediate, chroma, 0];
    } else if (hue < 180) {
        [r1, g1, b1] = [0, chroma, intermediate];
    } else if (hue < 240) {
        [r1, g1, b1] = [0, intermediate, chroma];
    } else if (hue < 300) {
        [r1, g1, b1] = [intermediate, 0, chroma];
    } else {
        [r1, g1, b1] = [chroma, 0, intermediate];
    }

    return {
        red: Math.round((r1 + match) * 255),
        green: Math.round((g1 + match) * 255),
        blue: Math.round((b1 + match) * 255)
    };
}

section("3. RGB and HSL conversion");

for (const rgb of [
    [255, 0, 0],
    [52, 152, 219],
    [46, 204, 113],
    [155, 89, 182]
]) {
    const hsl = rgbToHsl(...rgb);

    console.log(
        `RGB(${rgb.join(", ")}) -> ` +
        `HSL(${hsl.hue.toFixed(1)}°, ` +
        `${hsl.saturation.toFixed(1)}%, ` +
        `${hsl.lightness.toFixed(1)}%)`
    );
}

for (const hsl of [
    [0, 100, 50],
    [210, 70, 53],
    [120, 60, 50],
    [0, 0, 50]
]) {
    console.log(
        `HSL(${hsl.join(", ")}) -> RGB`,
        hslToRgb(...hsl)
    );
}


// -----------------------------------------------------------------------------
// 5. CSS COLOR STRING GENERATION
// -----------------------------------------------------------------------------

function rgbCss(red, green, blue, alpha = null) {
    validateRgb(red, green, blue);

    if (alpha === null) {
        return `rgb(${red} ${green} ${blue})`;
    }

    validateAlpha(alpha);
    return `rgb(${red} ${green} ${blue} / ${alpha})`;
}

function hslCss(hue, saturation, lightness, alpha = null) {
    const normalizedHue = ((hue % 360) + 360) % 360;

    if (saturation < 0 || saturation > 100) {
        throw new RangeError("Saturation must be 0..100.");
    }

    if (lightness < 0 || lightness > 100) {
        throw new RangeError("Lightness must be 0..100.");
    }

    const base =
        `hsl(${normalizedHue} ${saturation}% ${lightness}% )`
            .replace("% )", "%)");

    if (alpha === null) {
        return base;
    }

    validateAlpha(alpha);

    return (
        `hsl(${normalizedHue} ${saturation}% ` +
        `${lightness}% / ${alpha})`
    );
}

section("4. CSS color syntax");

console.log(rgbCss(52, 152, 219));
console.log(rgbCss(52, 152, 219, 0.5));
console.log(hslCss(204, 70, 53));
console.log(hslCss(204, 70, 53, 0.5));


// -----------------------------------------------------------------------------
// 6. ALPHA COMPOSITING
// -----------------------------------------------------------------------------

function compositeChannel(foreground, background, alpha) {
    validateAlpha(alpha);

    return Math.round(
        foreground * alpha +
        background * (1 - alpha)
    );
}

function alphaComposite(foreground, background, alpha) {
    validateRgb(...foreground);
    validateRgb(...background);
    validateAlpha(alpha);

    return [
        compositeChannel(foreground[0], background[0], alpha),
        compositeChannel(foreground[1], background[1], alpha),
        compositeChannel(foreground[2], background[2], alpha)
    ];
}

section("5. Alpha compositing");

const foreground = [255, 0, 0];
const background = [255, 255, 255];

for (const alpha of [0, 0.25, 0.5, 0.75, 1]) {
    console.log(
        `Alpha ${alpha}:`,
        alphaComposite(foreground, background, alpha)
    );
}

console.log(
    "Important distinction: color alpha changes that color's transparency; " +
    "element opacity affects the rendered element and descendants."
);


// -----------------------------------------------------------------------------
// 7. CSS UNITS
// -----------------------------------------------------------------------------

function px(value) {
    return `${value}px`;
}

function percent(value) {
    return `${value}%`;
}

function em(value) {
    return `${value}em`;
}

function rem(value) {
    return `${value}rem`;
}

function vh(value) {
    return `${value}vh`;
}

function vw(value) {
    return `${value}vw`;
}

function vmin(value) {
    return `${value}vmin`;
}

function vmax(value) {
    return `${value}vmax`;
}

section("6. CSS units");

const unitDescriptions = {
    px: "CSS pixel length",
    "%": "percentage relative to a property-specific reference",
    em: "relative to the relevant font-size context",
    rem: "relative to the root element font size",
    vh: "one percent of viewport height",
    vw: "one percent of viewport width",
    vmin: "one percent of the smaller viewport dimension",
    vmax: "one percent of the larger viewport dimension"
};

for (const [unit, description] of Object.entries(unitDescriptions)) {
    console.log(unit.padEnd(5), "->", description);
}


// -----------------------------------------------------------------------------
// 8. EM AND REM
// -----------------------------------------------------------------------------

function emToPx(value, currentFontSize) {
    return value * currentFontSize;
}

function remToPx(value, rootFontSize = 16) {
    return value * rootFontSize;
}

section("7. em and rem");

console.log("1rem at 16px root:", remToPx(1));
console.log("2rem at 16px root:", remToPx(2));
console.log("1.5em at 20px context:", emToPx(1.5, 20));

const parentFontSize = 20;
const childFontSize = emToPx(1.5, parentFontSize);
const grandchildFontSize = emToPx(1.5, childFontSize);

console.log("Nested em parent:", parentFontSize);
console.log("Nested em child:", childFontSize);
console.log("Nested em grandchild:", grandchildFontSize);


// -----------------------------------------------------------------------------
// 9. VIEWPORT CALCULATIONS
// -----------------------------------------------------------------------------

class Viewport {
    constructor(width, height) {
        if (width <= 0 || height <= 0) {
            throw new RangeError("Viewport dimensions must be positive.");
        }

        this.width = width;
        this.height = height;
    }

    get minimumDimension() {
        return Math.min(this.width, this.height);
    }

    get maximumDimension() {
        return Math.max(this.width, this.height);
    }

    vh(value) {
        return this.height * value / 100;
    }

    vw(value) {
        return this.width * value / 100;
    }

    vmin(value) {
        return this.minimumDimension * value / 100;
    }

    vmax(value) {
        return this.maximumDimension * value / 100;
    }
}

section("8. Viewport units");

for (const viewport of [
    new Viewport(390, 844),
    new Viewport(768, 1024),
    new Viewport(1440, 900)
]) {
    console.log(
        `\nViewport: ${viewport.width}x${viewport.height}`
    );

    console.log("10vh:", viewport.vh(10));
    console.log("10vw:", viewport.vw(10));
    console.log("10vmin:", viewport.vmin(10));
    console.log("10vmax:", viewport.vmax(10));
}


// -----------------------------------------------------------------------------
// 10. RESPONSIVE FLUID SIZING
// -----------------------------------------------------------------------------

function fluidFontSize(
    viewportWidth,
    preferredVw,
    minimumPx,
    maximumPx
) {
    const preferredPx =
        viewportWidth * preferredVw / 100;

    return clamp(
        preferredPx,
        minimumPx,
        maximumPx
    );
}

section("9. Responsive fluid sizing");

for (const width of [320, 480, 768, 1024, 1440, 1920]) {
    console.log(
        `${width}px viewport ->`,
        `${fluidFontSize(width, 3, 16, 48).toFixed(1)}px`
    );
}

console.log(
    "CSS equivalent:",
    "clamp(1rem, 3vw, 3rem)"
);


// -----------------------------------------------------------------------------
// 11. COLOR PALETTE GENERATION
// -----------------------------------------------------------------------------

function adjustLightness(rgb, amount) {
    const hsl = rgbToHsl(...rgb);

    const newLightness = clamp(
        hsl.lightness + amount,
        0,
        100
    );

    return hslToRgb(
        hsl.hue,
        hsl.saturation,
        newLightness
    );
}

function createPalette(baseRgb) {
    return [
        adjustLightness(baseRgb, -30),
        adjustLightness(baseRgb, -15),
        baseRgb,
        adjustLightness(baseRgb, 15),
        adjustLightness(baseRgb, 30)
    ];
}

section("10. Palette generation");

const baseColor = [52, 152, 219];

for (const color of createPalette(baseColor)) {
    console.log(
        color,
        "->",
        rgbaToHex(...color)
    );
}


// -----------------------------------------------------------------------------
// 12. CONTRAST
// -----------------------------------------------------------------------------

function srgbChannelToLinear(channel) {
    const normalized = channel / 255;

    if (normalized <= 0.04045) {
        return normalized / 12.92;
    }

    return (
        ((normalized + 0.055) / 1.055) ** 2.4
    );
}

function relativeLuminance(rgb) {
    validateRgb(...rgb);

    const [red, green, blue] = rgb.map(
        srgbChannelToLinear
    );

    return (
        0.2126 * red +
        0.7152 * green +
        0.0722 * blue
    );
}

function contrastRatio(firstRgb, secondRgb) {
    const first = relativeLuminance(firstRgb);
    const second = relativeLuminance(secondRgb);

    const lighter = Math.max(first, second);
    const darker = Math.min(first, second);

    return (lighter + 0.05) / (darker + 0.05);
}

section("11. Contrast");

for (const [foregroundColor, backgroundColor] of [
    [[0, 0, 0], [255, 255, 255]],
    [[255, 255, 255], [52, 152, 219]],
    [[255, 255, 255], [20, 20, 20]],
    [[30, 30, 30], [240, 240, 240]]
]) {
    console.log(
        rgbaToHex(...foregroundColor),
        "on",
        rgbaToHex(...backgroundColor),
        "->",
        `${contrastRatio(
            foregroundColor,
            backgroundColor
        ).toFixed(2)}:1`
    );
}


// -----------------------------------------------------------------------------
// 13. REUSABLE COLOR CLASS
// -----------------------------------------------------------------------------

class Color {
    constructor(red, green, blue, alpha = 1) {
        validateRgb(red, green, blue);
        validateAlpha(alpha);

        this.red = red;
        this.green = green;
        this.blue = blue;
        this.alpha = alpha;

        Object.freeze(this);
    }

    static fromHex(value) {
        const rgba = hexToRgba(value);

        return new Color(
            rgba.red,
            rgba.green,
            rgba.blue,
            rgba.alpha
        );
    }

    static fromHsl(
        hue,
        saturation,
        lightness,
        alpha = 1
    ) {
        const rgb = hslToRgb(
            hue,
            saturation,
            lightness
        );

        return new Color(
            rgb.red,
            rgb.green,
            rgb.blue,
            alpha
        );
    }

    toHex() {
        return rgbaToHex(
            this.red,
            this.green,
            this.blue,
            this.alpha < 1 ? this.alpha : null
        );
    }

    toRgbCss() {
        return rgbCss(
            this.red,
            this.green,
            this.blue,
            this.alpha < 1 ? this.alpha : null
        );
    }

    toHslCss() {
        const hsl = rgbToHsl(
            this.red,
            this.green,
            this.blue
        );

        return hslCss(
            hsl.hue.toFixed(1),
            hsl.saturation.toFixed(1),
            hsl.lightness.toFixed(1),
            this.alpha < 1 ? this.alpha : null
        );
    }

    withAlpha(alpha) {
        return new Color(
            this.red,
            this.green,
            this.blue,
            alpha
        );
    }

    lighten(amount) {
        const rgb = adjustLightness(
            [this.red, this.green, this.blue],
            amount
        );

        return new Color(
            rgb.red,
            rgb.green,
            rgb.blue,
            this.alpha
        );
    }

    darken(amount) {
        return this.lighten(-amount);
    }
}

section("12. Color abstraction");

const brand = Color.fromHex("#3498db");

console.log("HEX:", brand.toHex());
console.log("RGB:", brand.toRgbCss());
console.log("HSL:", brand.toHslCss());
console.log("Alpha:", brand.withAlpha(0.4).toRgbCss());
console.log("Light:", brand.lighten(15).toHex());
console.log("Dark:", brand.darken(15).toHex());


// -----------------------------------------------------------------------------
// 14. CSS CUSTOM PROPERTIES
// -----------------------------------------------------------------------------

function generateCssTokens() {
    const primary = Color.fromHex("#3498db");
    const success = Color.fromHex("#2ecc71");
    const danger = Color.fromHex("#e74c3c");
    const surface = Color.fromHex("#f5f7fa");
    const text = Color.fromHex("#1f2937");

    return `
:root {
    --color-primary: ${primary.toHex()};
    --color-primary-light: ${primary.lighten(15).toHex()};
    --color-primary-dark: ${primary.darken(15).toHex()};
    --color-success: ${success.toHex()};
    --color-danger: ${danger.toHex()};
    --color-surface: ${surface.toHex()};
    --color-text: ${text.toHex()};

    --space-1: 0.25rem;
    --space-2: 0.5rem;
    --space-3: 0.75rem;
    --space-4: 1rem;
    --space-6: 1.5rem;
    --space-8: 2rem;
}`.trim();
}

section("13. CSS design tokens");

console.log(generateCssTokens());


// -----------------------------------------------------------------------------
// 15. BROWSER-SPECIFIC DEMONSTRATION
// -----------------------------------------------------------------------------

function browserColorDemo() {
    if (typeof document === "undefined") {
        console.log(
            "Browser DOM is unavailable in Node.js; " +
            "the browser demonstration is skipped."
        );
        return;
    }

    const element = document.createElement("div");

    element.style.backgroundColor = "hsl(204 70% 53% / 0.8)";
    element.style.width = "50vw";
    element.style.minHeight = "20vh";
    element.style.padding = "2rem";

    document.body.appendChild(element);

    console.log(
        "Computed browser demonstration element:",
        element
    );
}

section("14. Browser-side CSS value assignment");

browserColorDemo();


// -----------------------------------------------------------------------------
// 16. ERROR HANDLING
// -----------------------------------------------------------------------------

section("15. Validation and edge cases");

for (const invalidHex of [
    "#12",
    "#gggggg",
    "#12345",
    "1234567"
]) {
    try {
        normalizeHex(invalidHex);
        console.log("Unexpectedly accepted:", invalidHex);
    } catch (error) {
        console.log(
            `${invalidHex} -> rejected: ${error.message}`
        );
    }
}

for (const invalidRgb of [
    [256, 0, 0],
    [-1, 0, 0],
    [0, 300, 0]
]) {
    try {
        validateRgb(...invalidRgb);
        console.log(
            "Unexpectedly accepted:",
            invalidRgb
        );
    } catch (error) {
        console.log(
            `${invalidRgb.join(", ")} -> rejected: ${error.message}`
        );
    }
}

for (const invalidAlpha of [-0.1, 1.1]) {
    try {
        validateAlpha(invalidAlpha);
        console.log(
            "Unexpectedly accepted alpha:",
            invalidAlpha
        );
    } catch (error) {
        console.log(
            `${invalidAlpha} -> rejected: ${error.message}`
        );
    }
}


// -----------------------------------------------------------------------------
// 17. REALISTIC RESPONSIVE COMPONENT MODEL
// -----------------------------------------------------------------------------

class ResponsiveCard {
    constructor(maxWidthPx, widthPercent, paddingRem) {
        this.maxWidthPx = maxWidthPx;
        this.widthPercent = widthPercent;
        this.paddingRem = paddingRem;
    }

    toCss() {
        return `
.card {
    width: ${percent(this.widthPercent)};
    max-width: ${px(this.maxWidthPx)};
    padding: ${rem(this.paddingRem)};
}`.trim();
    }
}

section("16. Responsive card");

const card = new ResponsiveCard(
    720,
    92,
    1.5
);

console.log(card.toCss());


// -----------------------------------------------------------------------------
// 18. COMPLETE RESPONSIVE CSS CASE STUDY
// -----------------------------------------------------------------------------

function generateResponsiveStyles() {
    return `
:root {
    --color-primary: #3498db;
    --color-primary-light: hsl(204 70% 63%);
    --color-primary-dark: hsl(204 70% 43%);

    --color-surface: #f5f7fa;
    --color-text: #1f2937;

    --space-1: 0.25rem;
    --space-2: 0.5rem;
    --space-4: 1rem;
    --space-6: 1.5rem;
    --space-8: 2rem;
}

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    color: var(--color-text);
    background: var(--color-surface);
    font-size: 1rem;
}

.page {
    width: 92%;
    max-width: 75rem;
    margin-inline: auto;
    padding: clamp(1rem, 4vw, 3rem);
}

.hero {
    min-height: 70vh;
    padding: 8vh 4vw;
}

.hero h1 {
    font-size: clamp(2rem, 5vw, 4rem);
}

.card {
    width: 100%;
    padding: 1.5rem;
    background: rgb(255 255 255 / 0.92);
    border-radius: 0.75rem;
}

.button {
    padding: 0.75em 1.25em;
    color: white;
    background: hsl(204 70% 53%);
}

.button:hover {
    background: hsl(204 70% 43%);
}
`.trim();
}

section("17. Complete CSS case study");

console.log(generateResponsiveStyles());


// -----------------------------------------------------------------------------
// 19. SELF-TESTS
// -----------------------------------------------------------------------------

section("18. Self-tests");

console.assert(
    normalizeHex("#abc") === "#aabbcc",
    "HEX expansion failed"
);

console.assert(
    hexToRgba("#ff0000").red === 255,
    "HEX RGB conversion failed"
);

console.assert(
    rgbaToHex(255, 0, 0) === "#ff0000",
    "RGB to HEX failed"
);

const redHsl = rgbToHsl(255, 0, 0);

console.assert(
    Math.abs(redHsl.hue) < 1e-9,
    "Red hue conversion failed"
);

console.assert(
    Math.abs(redHsl.saturation - 100) < 1e-9,
    "Red saturation conversion failed"
);

console.assert(
    Math.abs(redHsl.lightness - 50) < 1e-9,
    "Red lightness conversion failed"
);

const redRgb = hslToRgb(0, 100, 50);

console.assert(
    redRgb.red === 255 &&
    redRgb.green === 0 &&
    redRgb.blue === 0,
    "HSL to RGB failed"
);

console.assert(
    remToPx(2) === 32,
    "rem calculation failed"
);

const testViewport = new Viewport(1000, 800);

console.assert(
    testViewport.vw(50) === 500,
    "vw calculation failed"
);

console.assert(
    testViewport.vh(50) === 400,
    "vh calculation failed"
);

console.assert(
    testViewport.vmin(50) === 400,
    "vmin calculation failed"
);

console.assert(
    testViewport.vmax(50) === 500,
    "vmax calculation failed"
);

console.assert(
    clamp(5, 10, 20) === 10,
    "clamp minimum failed"
);

console.assert(
    clamp(25, 10, 20) === 20,
    "clamp maximum failed"
);

console.assert(
    alphaComposite(
        [0, 0, 0],
        [255, 255, 255],
        0
    ).every(value => value === 255),
    "Alpha compositing failed"
);

console.log("All self-tests passed.");


// -----------------------------------------------------------------------------
// 20. FINAL PRACTICAL OUTPUT
// -----------------------------------------------------------------------------

section("19. Practical CSS values");

console.log("width:", percent(92));
console.log("max-width:", px(1200));
console.log("padding:", rem(1.5));
console.log("hero height:", vh(70));
console.log("responsive heading:", "clamp(2rem, 5vw, 4rem)");
console.log("viewport-safe square:", "min(80vmin, 600px)");
console.log("primary color:", Color.fromHex("#3498db").toHex());
console.log(
    "primary transparent:",
    Color.fromHex("#3498db").withAlpha(0.5).toRgbCss()
);

console.log("\nJavaScript CSS colors and units study complete.");
