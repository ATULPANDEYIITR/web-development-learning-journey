"use strict";

/*
 * CSS Box Model: practical JavaScript companion
 *
 * This file demonstrates:
 *   - CSS box-model calculations
 *   - content-box and border-box
 *   - padding, border, and margin
 *   - overflow detection
 *   - DOM measurement
 *   - getComputedStyle()
 *   - offsetWidth/clientWidth/scrollWidth
 *   - validation
 *   - responsive calculations
 *   - a small reusable BoxModelInspector
 *
 * Run in a browser by loading this file from an HTML page.
 * The computational examples also work in Node.js.
 */

// ============================================================================
// 1. BASIC BOX MODEL CALCULATIONS
// ============================================================================

function calculateContentBoxWidth(contentWidth) {
    return contentWidth;
}

function calculatePaddingBoxWidth(contentWidth, paddingLeft, paddingRight) {
    return contentWidth + paddingLeft + paddingRight;
}

function calculateBorderBoxWidth(
    contentWidth,
    paddingLeft,
    paddingRight,
    borderLeft,
    borderRight
) {
    return (
        contentWidth +
        paddingLeft +
        paddingRight +
        borderLeft +
        borderRight
    );
}

function calculateMarginBoxWidth(
    contentWidth,
    paddingLeft,
    paddingRight,
    borderLeft,
    borderRight,
    marginLeft,
    marginRight
) {
    return (
        calculateBorderBoxWidth(
            contentWidth,
            paddingLeft,
            paddingRight,
            borderLeft,
            borderRight
        ) +
        marginLeft +
        marginRight
    );
}

console.log("=== Basic box model calculation ===");

const contentWidth = 200;
const paddingLeft = 20;
const paddingRight = 20;
const borderLeft = 5;
const borderRight = 5;
const marginLeft = 30;
const marginRight = 30;

console.log("Content box:", calculateContentBoxWidth(contentWidth));
console.log(
    "Padding box:",
    calculatePaddingBoxWidth(contentWidth, paddingLeft, paddingRight)
);
console.log(
    "Border box:",
    calculateBorderBoxWidth(
        contentWidth,
        paddingLeft,
        paddingRight,
        borderLeft,
        borderRight
    )
);
console.log(
    "Margin box:",
    calculateMarginBoxWidth(
        contentWidth,
        paddingLeft,
        paddingRight,
        borderLeft,
        borderRight,
        marginLeft,
        marginRight
    )
);


// ============================================================================
// 2. content-box AND border-box
// ============================================================================

function calculateUsedBorderBoxWidth({
    declaredWidth,
    paddingLeft,
    paddingRight,
    borderLeft,
    borderRight,
    boxSizing
}) {
    if (declaredWidth < 0) {
        throw new RangeError("Width cannot be negative.");
    }

    if (boxSizing === "content-box") {
        return (
            declaredWidth +
            paddingLeft +
            paddingRight +
            borderLeft +
            borderRight
        );
    }

    if (boxSizing === "border-box") {
        return declaredWidth;
    }

    throw new Error(
        "boxSizing must be 'content-box' or 'border-box'."
    );
}

const sizingExample = {
    declaredWidth: 200,
    paddingLeft: 20,
    paddingRight: 20,
    borderLeft: 5,
    borderRight: 5
};

console.log("\n=== box-sizing ===");

console.log(
    "content-box:",
    calculateUsedBorderBoxWidth({
        ...sizingExample,
        boxSizing: "content-box"
    })
);

console.log(
    "border-box:",
    calculateUsedBorderBoxWidth({
        ...sizingExample,
        boxSizing: "border-box"
    })
);


// ============================================================================
// 3. VALIDATION
// ============================================================================

function validateBoxValues(values) {
    const errors = [];

    const nonNegativeProperties = [
        "width",
        "height",
        "padding",
        "border"
    ];

    for (const property of nonNegativeProperties) {
        if (values[property] < 0) {
            errors.push(`${property} cannot be negative.`);
        }
    }

    // Margin is deliberately excluded because negative margins are valid CSS.
    return errors;
}

console.log("\n=== Validation ===");

console.log(
    validateBoxValues({
        width: 300,
        height: 150,
        padding: 20,
        border: 1,
        margin: -10
    })
);

console.log(
    validateBoxValues({
        width: -1,
        height: 150,
        padding: -5,
        border: 1,
        margin: 10
    })
);


// ============================================================================
// 4. OVERFLOW CALCULATION
// ============================================================================

function calculateOverflow(contentWidth, contentHeight, boxWidth, boxHeight) {
    return {
        horizontal: Math.max(0, contentWidth - boxWidth),
        vertical: Math.max(0, contentHeight - boxHeight)
    };
}

console.log("\n=== Overflow ===");

console.log(
    calculateOverflow(
        600,
        500,
        400,
        300
    )
);


// ============================================================================
// 5. RESPONSIVE WIDTH
// ============================================================================

function clamp(value, minimum, maximum) {
    return Math.min(Math.max(value, minimum), maximum);
}

function responsiveComponentWidth(
    viewportWidth,
    percentage,
    minimum,
    maximum
) {
    return clamp(
        viewportWidth * percentage,
        minimum,
        maximum
    );
}

console.log("\n=== Responsive sizing ===");

for (const viewportWidth of [320, 480, 768, 1024, 1440]) {
    console.log(
        `${viewportWidth}px viewport -> ` +
        `${responsiveComponentWidth(viewportWidth, 0.8, 280, 900)}px`
    );
}


// ============================================================================
// 6. DOM DEMONSTRATION
// ============================================================================

function createBoxModelDemo() {
    if (typeof document === "undefined") {
        console.log(
            "\nDOM demonstration skipped because this runtime has no document."
        );
        return;
    }

    const container = document.createElement("section");
    container.id = "box-model-demo";

    const title = document.createElement("h2");
    title.textContent = "CSS Box Model Demo";

    const box = document.createElement("div");

    box.textContent =
        "This element contains content, padding, border, and margin.";

    Object.assign(box.style, {
        width: "240px",
        height: "120px",
        padding: "20px",
        border: "4px solid black",
        margin: "30px",
        boxSizing: "content-box",
        overflow: "auto",
        overflowWrap: "anywhere"
    });

    container.append(title, box);
    document.body.appendChild(container);

    return box;
}


// ============================================================================
// 7. DOM MEASUREMENT
// ============================================================================

function inspectElementBox(element) {
    if (!(element instanceof Element)) {
        throw new TypeError("Expected a DOM Element.");
    }

    const computed = getComputedStyle(element);

    const measurement = {
        width: computed.width,
        height: computed.height,

        paddingTop: computed.paddingTop,
        paddingRight: computed.paddingRight,
        paddingBottom: computed.paddingBottom,
        paddingLeft: computed.paddingLeft,

        borderTopWidth: computed.borderTopWidth,
        borderRightWidth: computed.borderRightWidth,
        borderBottomWidth: computed.borderBottomWidth,
        borderLeftWidth: computed.borderLeftWidth,

        marginTop: computed.marginTop,
        marginRight: computed.marginRight,
        marginBottom: computed.marginBottom,
        marginLeft: computed.marginLeft,

        boxSizing: computed.boxSizing,

        clientWidth: element.clientWidth,
        clientHeight: element.clientHeight,

        offsetWidth: element.offsetWidth,
        offsetHeight: element.offsetHeight,

        scrollWidth: element.scrollWidth,
        scrollHeight: element.scrollHeight
    };

    return measurement;
}


// ============================================================================
// 8. UNDERSTANDING DOM DIMENSION PROPERTIES
// ============================================================================

function explainDomDimensions() {
    console.log(`
DOM dimension concepts:

clientWidth/clientHeight:
    Content + padding. Borders and most scrollbar space are excluded.

offsetWidth/offsetHeight:
    Border-box dimensions, generally including scrollbar space.

scrollWidth/scrollHeight:
    Size required to contain the element's content, including content
    that is not currently visible because of overflow.

getComputedStyle(element):
    Provides computed CSS values, useful for inspecting padding, borders,
    margins, dimensions, overflow, and box-sizing.
`);
}


// ============================================================================
// 9. DETECTING OVERFLOW IN THE BROWSER
// ============================================================================

function hasHorizontalOverflow(element) {
    return element.scrollWidth > element.clientWidth;
}

function hasVerticalOverflow(element) {
    return element.scrollHeight > element.clientHeight;
}

function getOverflowState(element) {
    return {
        horizontal: hasHorizontalOverflow(element),
        vertical: hasVerticalOverflow(element)
    };
}


// ============================================================================
// 10. REUSABLE INSPECTOR CLASS
// ============================================================================

class BoxModelInspector {
    constructor(element) {
        if (!(element instanceof Element)) {
            throw new TypeError("BoxModelInspector requires a DOM Element.");
        }

        this.element = element;
    }

    computedStyle() {
        return getComputedStyle(this.element);
    }

    dimensions() {
        const style = this.computedStyle();

        return {
            declaredWidth: style.width,
            declaredHeight: style.height,
            boxSizing: style.boxSizing,

            clientWidth: this.element.clientWidth,
            clientHeight: this.element.clientHeight,

            offsetWidth: this.element.offsetWidth,
            offsetHeight: this.element.offsetHeight,

            scrollWidth: this.element.scrollWidth,
            scrollHeight: this.element.scrollHeight
        };
    }

    spacing() {
        const style = this.computedStyle();

        return {
            padding: {
                top: style.paddingTop,
                right: style.paddingRight,
                bottom: style.paddingBottom,
                left: style.paddingLeft
            },
            border: {
                top: style.borderTopWidth,
                right: style.borderRightWidth,
                bottom: style.borderBottomWidth,
                left: style.borderLeftWidth
            },
            margin: {
                top: style.marginTop,
                right: style.marginRight,
                bottom: style.marginBottom,
                left: style.marginLeft
            }
        };
    }

    overflow() {
        return {
            horizontal: hasHorizontalOverflow(this.element),
            vertical: hasVerticalOverflow(this.element)
        };
    }

    report() {
        return {
            dimensions: this.dimensions(),
            spacing: this.spacing(),
            overflow: this.overflow()
        };
    }
}


// ============================================================================
// 11. RESPONSIVE BOX USING CSS CUSTOM PROPERTIES
// ============================================================================

function createResponsiveCard() {
    if (typeof document === "undefined") {
        return null;
    }

    const card = document.createElement("article");

    card.textContent =
        "Responsive card with predictable box sizing and overflow handling.";

    card.style.setProperty("box-sizing", "border-box");
    card.style.setProperty("width", "min(100%, 360px)");
    card.style.setProperty("padding", "24px");
    card.style.setProperty("border", "1px solid currentColor");
    card.style.setProperty("margin", "16px");
    card.style.setProperty("overflow", "auto");
    card.style.setProperty("overflow-wrap", "anywhere");

    document.body.appendChild(card);

    return card;
}


// ============================================================================
// 12. EDGE CASE: LONG UNBREAKABLE CONTENT
// ============================================================================

function demonstrateLongContent() {
    if (typeof document === "undefined") {
        return;
    }

    const container = document.createElement("div");
    container.style.width = "300px";
    container.style.boxSizing = "border-box";
    container.style.border = "1px solid black";
    container.style.padding = "12px";

    const content = document.createElement("div");
    content.textContent =
        "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";

    // Without an appropriate wrapping rule, long tokens can produce
    // unexpected horizontal overflow.
    content.style.overflowWrap = "anywhere";

    container.appendChild(content);
    document.body.appendChild(container);

    return container;
}


// ============================================================================
// 13. MARGIN AND PADDING COMPARISON
// ============================================================================

function compareSpacing() {
    return {
        padding: {
            insideBorder: true,
            partOfBorderBox: true,
            negativeAllowed: false
        },
        margin: {
            outsideBorder: true,
            partOfBorderBox: false,
            negativeAllowed: true
        }
    };
}

console.log("\n=== Padding versus margin ===");
console.log(compareSpacing());


// ============================================================================
// 14. SIMPLE ASSERTIONS
// ============================================================================

function assertEqual(actual, expected, description) {
    if (actual !== expected) {
        throw new Error(
            `${description}: expected ${expected}, received ${actual}`
        );
    }
}

function runTests() {
    assertEqual(
        calculateBorderBoxWidth(200, 20, 20, 5, 5),
        250,
        "content-box width calculation"
    );

    assertEqual(
        calculateUsedBorderBoxWidth({
            declaredWidth: 200,
            paddingLeft: 20,
            paddingRight: 20,
            borderLeft: 5,
            borderRight: 5,
            boxSizing: "border-box"
        }),
        200,
        "border-box width calculation"
    );

    const overflow = calculateOverflow(600, 500, 400, 300);

    assertEqual(
        overflow.horizontal,
        200,
        "horizontal overflow calculation"
    );

    assertEqual(
        overflow.vertical,
        200,
        "vertical overflow calculation"
    );

    console.log("\nAll JavaScript tests passed.");
}


// ============================================================================
// 15. BROWSER EXECUTION
// ============================================================================

function runBrowserDemonstration() {
    if (typeof document === "undefined") {
        return;
    }

    const box = createBoxModelDemo();
    createResponsiveCard();
    demonstrateLongContent();

    if (box) {
        const inspector = new BoxModelInspector(box);

        console.log("\n=== Browser box-model inspection ===");
        console.table(inspector.report());
        console.log("Overflow:", inspector.overflow());
    }

    explainDomDimensions();
}


// ============================================================================
// 16. START
// ============================================================================

runTests();
runBrowserDemonstration();
