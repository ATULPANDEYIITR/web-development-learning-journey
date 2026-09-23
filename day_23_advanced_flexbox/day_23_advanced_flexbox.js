"use strict";

/*
 * Advanced Flexbox
 *
 * This JavaScript file complements the Python study program by modeling
 * important Flexbox calculations and demonstrating how the concepts map
 * naturally to browser-side layout code.
 *
 * The calculations below are educational models. A browser implements the
 * complete CSS Flexbox specification and must account for intrinsic sizes,
 * min/max constraints, wrapping, writing modes, percentages, aspect ratios,
 * content measurements, and other details.
 */

// ---------------------------------------------------------------------------
// 1. BASIC FLEXBOX VOCABULARY
// ---------------------------------------------------------------------------

function explainFundamentals() {
    console.log("\n=== 1. FLEXBOX FUNDAMENTALS ===");

    const concepts = {
        "Flex container":
            "An element with display:flex or display:inline-flex. Its direct children become flex items.",
        "Main axis":
            "The primary layout direction controlled by flex-direction.",
        "Cross axis":
            "The axis perpendicular to the main axis.",
        "flex-grow":
            "A factor used to distribute positive free space.",
        "flex-shrink":
            "A factor used to distribute negative free space.",
        "flex-basis":
            "The initial main-size contribution before flexible growth or shrinking.",
        "order":
            "A visual ordering property for flex items.",
        "Nested Flexbox":
            "A flex item can itself be a flex container."
    };

    for (const [name, definition] of Object.entries(concepts)) {
        console.log(`${name}: ${definition}`);
    }
}


// ---------------------------------------------------------------------------
// 2. FLEX ITEM MODEL
// ---------------------------------------------------------------------------

class FlexItem {
    constructor({
        name,
        basis,
        grow = 0,
        shrink = 1,
        order = 0,
        minSize = null,
        maxSize = null
    }) {
        this.name = name;
        this.basis = basis;
        this.grow = grow;
        this.shrink = shrink;
        this.order = order;
        this.minSize = minSize;
        this.maxSize = maxSize;
        this.finalSize = null;

        this.validate();
    }

    validate() {
        if (!Number.isFinite(this.basis) || this.basis < 0) {
            throw new Error(`${this.name}: basis must be a non-negative number.`);
        }

        if (!Number.isFinite(this.grow) || this.grow < 0) {
            throw new Error(`${this.name}: grow must be non-negative.`);
        }

        if (!Number.isFinite(this.shrink) || this.shrink < 0) {
            throw new Error(`${this.name}: shrink must be non-negative.`);
        }

        if (this.minSize !== null && this.minSize < 0) {
            throw new Error(`${this.name}: minSize cannot be negative.`);
        }

        if (
            this.minSize !== null &&
            this.maxSize !== null &&
            this.minSize > this.maxSize
        ) {
            throw new Error(
                `${this.name}: minSize cannot be greater than maxSize.`
            );
        }
    }
}


// ---------------------------------------------------------------------------
// 3. FLEX-GROW CALCULATION
// ---------------------------------------------------------------------------

function distributePositiveFreeSpace(containerSize, items) {
    const totalBasis = items.reduce(
        (total, item) => total + item.basis,
        0
    );

    const freeSpace = containerSize - totalBasis;

    if (freeSpace <= 0) {
        for (const item of items) {
            item.finalSize = item.basis;
        }
        return items;
    }

    const totalGrow = items.reduce(
        (total, item) => total + item.grow,
        0
    );

    if (totalGrow === 0) {
        for (const item of items) {
            item.finalSize = item.basis;
        }
        return items;
    }

    for (const item of items) {
        const additionalSpace =
            freeSpace * (item.grow / totalGrow);

        item.finalSize = item.basis + additionalSpace;
    }

    return items;
}


// ---------------------------------------------------------------------------
// 4. FLEX-SHRINK CALCULATION
// ---------------------------------------------------------------------------

function distributeNegativeFreeSpace(containerSize, items) {
    const totalBasis = items.reduce(
        (total, item) => total + item.basis,
        0
    );

    const overflow = totalBasis - containerSize;

    if (overflow <= 0) {
        for (const item of items) {
            item.finalSize = item.basis;
        }
        return items;
    }

    /*
     * The important detail is scaled shrink factors:
     *
     *     scaled factor = flex-shrink * flex-basis
     *
     * This means a larger flex basis generally contributes more to the
     * shrink distribution when shrink factors are equal.
     */
    const scaledFactors = items.map(
        item => item.shrink * item.basis
    );

    const totalScaledFactor = scaledFactors.reduce(
        (total, value) => total + value,
        0
    );

    if (totalScaledFactor === 0) {
        for (const item of items) {
            item.finalSize = item.basis;
        }
        return items;
    }

    items.forEach((item, index) => {
        const reduction =
            overflow *
            (scaledFactors[index] / totalScaledFactor);

        item.finalSize = Math.max(
            0,
            item.basis - reduction
        );
    });

    return items;
}


// ---------------------------------------------------------------------------
// 5. GENERIC FLEX SIZING MODEL
// ---------------------------------------------------------------------------

function resolveFlexibleSizes(containerSize, items) {
    if (!Number.isFinite(containerSize) || containerSize < 0) {
        throw new Error("Container size must be a non-negative number.");
    }

    if (items.length === 0) {
        return [];
    }

    const totalBasis = items.reduce(
        (total, item) => total + item.basis,
        0
    );

    if (totalBasis < containerSize) {
        return distributePositiveFreeSpace(
            containerSize,
            items
        );
    }

    if (totalBasis > containerSize) {
        return distributeNegativeFreeSpace(
            containerSize,
            items
        );
    }

    items.forEach(item => {
        item.finalSize = item.basis;
    });

    return items;
}


function printItems(items) {
    console.table(
        items.map(item => ({
            name: item.name,
            basis: Number(item.basis.toFixed(2)),
            grow: item.grow,
            shrink: item.shrink,
            finalSize:
                item.finalSize === null
                    ? null
                    : Number(item.finalSize.toFixed(2))
        }))
    );
}


// ---------------------------------------------------------------------------
// 6. FLEX-GROW EXAMPLE
// ---------------------------------------------------------------------------

function demonstrateGrow() {
    console.log("\n=== 2. FLEX-GROW ===");

    const items = [
        new FlexItem({
            name: "Item A",
            basis: 200,
            grow: 1
        }),
        new FlexItem({
            name: "Item B",
            basis: 200,
            grow: 3
        })
    ];

    resolveFlexibleSizes(1000, items);
    printItems(items);

    /*
     * Total basis = 400.
     * Free space = 600.
     * Grow ratio = 1:3.
     *
     * A receives 150 additional pixels.
     * B receives 450 additional pixels.
     */
}


// ---------------------------------------------------------------------------
// 7. FLEX-SHRINK EXAMPLE
// ---------------------------------------------------------------------------

function demonstrateShrink() {
    console.log("\n=== 3. FLEX-SHRINK ===");

    const items = [
        new FlexItem({
            name: "Large item",
            basis: 400,
            shrink: 1
        }),
        new FlexItem({
            name: "Small item",
            basis: 300,
            shrink: 1
        })
    ];

    resolveFlexibleSizes(500, items);
    printItems(items);

    /*
     * The items need 700px but only have 500px.
     * Overflow = 200px.
     *
     * Scaled shrink factors:
     * Large = 400 * 1
     * Small = 300 * 1
     *
     * Equal shrink values therefore do not imply equal pixel reductions.
     */
}


// ---------------------------------------------------------------------------
// 8. FLEX-BASIS COMPARISON
// ---------------------------------------------------------------------------

function demonstrateBasis() {
    console.log("\n=== 4. FLEX-BASIS ===");

    const zeroBasisItems = [
        new FlexItem({
            name: "A",
            basis: 0,
            grow: 1
        }),
        new FlexItem({
            name: "B",
            basis: 0,
            grow: 1
        }),
        new FlexItem({
            name: "C",
            basis: 0,
            grow: 1
        })
    ];

    resolveFlexibleSizes(900, zeroBasisItems);

    console.log("Zero-basis equal sharing:");
    printItems(zeroBasisItems);

    const contentInfluencedItems = [
        new FlexItem({
            name: "Short content",
            basis: 100,
            grow: 1
        }),
        new FlexItem({
            name: "Long content",
            basis: 300,
            grow: 1
        })
    ];

    resolveFlexibleSizes(900, contentInfluencedItems);

    console.log("Different bases with equal grow:");
    printItems(contentInfluencedItems);
}


// ---------------------------------------------------------------------------
// 9. ORDER
// ---------------------------------------------------------------------------

function demonstrateOrder() {
    console.log("\n=== 5. ORDER ===");

    const sourceOrder = [
        { name: "Header", order: 0 },
        { name: "Navigation", order: 2 },
        { name: "Main", order: 1 },
        { name: "Footer", order: 3 },
        { name: "Alert", order: -1 }
    ];

    console.log(
        "Source order:",
        sourceOrder.map(item => item.name).join(" -> ")
    );

    const visualOrder = [...sourceOrder].sort(
        (a, b) => a.order - b.order
    );

    console.log(
        "Visual order:",
        visualOrder.map(item => item.name).join(" -> ")
    );

    /*
     * Keep source order meaningful.
     *
     * CSS order changes visual placement, not the semantic structure of the
     * document. Excessive use can create confusing keyboard and assistive
     * technology experiences.
     */
}


// ---------------------------------------------------------------------------
// 10. FLEX-DIRECTION AND AXES
// ---------------------------------------------------------------------------

function demonstrateAxes() {
    console.log("\n=== 6. AXES ===");

    const directions = {
        row: {
            mainAxis: "horizontal",
            crossAxis: "vertical"
        },
        "row-reverse": {
            mainAxis: "horizontal, reversed",
            crossAxis: "vertical"
        },
        column: {
            mainAxis: "vertical",
            crossAxis: "horizontal"
        },
        "column-reverse": {
            mainAxis: "vertical, reversed",
            crossAxis: "horizontal"
        }
    };

    console.table(directions);
}


// ---------------------------------------------------------------------------
// 11. NESTED FLEXBOX MODEL
// ---------------------------------------------------------------------------

class LayoutNode {
    constructor(name, display = "flex", direction = "row") {
        this.name = name;
        this.display = display;
        this.direction = direction;
        this.children = [];
    }

    addChild(child) {
        this.children.push(child);
        return this;
    }
}


function printLayoutTree(node, depth = 0) {
    console.log(
        `${"  ".repeat(depth)}- ${node.name} ` +
        `[${node.display}, ${node.direction}]`
    );

    for (const child of node.children) {
        printLayoutTree(child, depth + 1);
    }
}


function demonstrateNestedLayouts() {
    console.log("\n=== 7. NESTED FLEXBOX ===");

    const page = new LayoutNode(
        "Page",
        "flex",
        "column"
    );

    const header = new LayoutNode(
        "Header",
        "flex",
        "row"
    );

    const content = new LayoutNode(
        "Content area",
        "flex",
        "row"
    );

    const sidebar = new LayoutNode(
        "Sidebar",
        "flex",
        "column"
    );

    const main = new LayoutNode(
        "Main",
        "flex",
        "column"
    );

    const toolbar = new LayoutNode(
        "Toolbar",
        "flex",
        "row"
    );

    const footer = new LayoutNode(
        "Footer",
        "flex",
        "row"
    );

    content.addChild(sidebar).addChild(main);
    main.addChild(toolbar);
    page
        .addChild(header)
        .addChild(content)
        .addChild(footer);

    printLayoutTree(page);
}


// ---------------------------------------------------------------------------
// 12. BROWSER-SIDE CSS DEMONSTRATION
// ---------------------------------------------------------------------------

function createBrowserFlexDemo() {
    /*
     * This function only runs when a DOM exists.
     *
     * It creates a small responsive card layout using real CSS Flexbox.
     * This is useful because the sizing model above explains the algorithm,
     * while the browser demonstration uses an actual Flexbox implementation.
     */
    if (typeof document === "undefined") {
        console.log(
            "\nBrowser DOM not available. Run this portion in a browser."
        );
        return;
    }

    const container = document.createElement("div");

    container.style.display = "flex";
    container.style.flexWrap = "wrap";
    container.style.gap = "16px";
    container.style.padding = "16px";
    container.style.maxWidth = "900px";
    container.style.boxSizing = "border-box";

    const cardNames = [
        "Analytics",
        "Security",
        "Operations",
        "Research"
    ];

    for (const name of cardNames) {
        const card = document.createElement("article");

        card.textContent = name;
        card.style.flex = "1 1 200px";
        card.style.minWidth = "0";
        card.style.padding = "20px";
        card.style.boxSizing = "border-box";
        card.style.border = "1px solid #888";

        container.appendChild(card);
    }

    document.body.appendChild(container);

    console.log(
        "Created a real flex-wrap layout with flex: 1 1 200px."
    );
}


// ---------------------------------------------------------------------------
// 13. SIDEBAR + CONTENT PATTERN
// ---------------------------------------------------------------------------

function demonstrateSidebarPattern() {
    console.log("\n=== 8. SIDEBAR + CONTENT ===");

    const layout = [
        new FlexItem({
            name: "Sidebar",
            basis: 260,
            grow: 0,
            shrink: 0
        }),
        new FlexItem({
            name: "Main content",
            basis: 0,
            grow: 1,
            shrink: 1
        })
    ];

    resolveFlexibleSizes(1200, layout);
    printItems(layout);

    /*
     * A typical CSS implementation is:
     *
     * .layout { display: flex; }
     * .sidebar { flex: 0 0 260px; }
     * .main { flex: 1 1 0; min-width: 0; }
     *
     * min-width: 0 is useful when the main content must actually shrink
     * instead of allowing minimum content size to force overflow.
     */
}


// ---------------------------------------------------------------------------
// 14. NAVIGATION BAR PATTERN
// ---------------------------------------------------------------------------

function demonstrateNavbarPattern() {
    console.log("\n=== 9. NAVBAR PATTERN ===");

    const navbar = [
        new FlexItem({
            name: "Brand",
            basis: 150,
            grow: 0,
            shrink: 0
        }),
        new FlexItem({
            name: "Links",
            basis: 300,
            grow: 1,
            shrink: 1
        }),
        new FlexItem({
            name: "Actions",
            basis: 180,
            grow: 0,
            shrink: 0
        })
    ];

    resolveFlexibleSizes(1000, navbar);
    printItems(navbar);

    console.log(
        "The middle region absorbs available space while the edge regions remain stable."
    );
}


// ---------------------------------------------------------------------------
// 15. FLEX-WRAP LINE FORMATION
// ---------------------------------------------------------------------------

function wrapIntoLines(containerSize, items) {
    const lines = [];
    let currentLine = [];
    let currentSize = 0;

    for (const item of items) {
        if (item.basis > containerSize) {
            if (currentLine.length > 0) {
                lines.push(currentLine);
                currentLine = [];
                currentSize = 0;
            }

            lines.push([item]);
            continue;
        }

        if (
            currentLine.length > 0 &&
            currentSize + item.basis > containerSize
        ) {
            lines.push(currentLine);
            currentLine = [];
            currentSize = 0;
        }

        currentLine.push(item);
        currentSize += item.basis;
    }

    if (currentLine.length > 0) {
        lines.push(currentLine);
    }

    return lines;
}


function demonstrateWrapping() {
    console.log("\n=== 10. FLEX-WRAP ===");

    const items = [280, 280, 280, 280, 280].map(
        (basis, index) =>
            new FlexItem({
                name: `Card ${index + 1}`,
                basis
            })
    );

    const lines = wrapIntoLines(900, items);

    lines.forEach((line, index) => {
        console.log(
            `Line ${index + 1}:`,
            line.map(item => item.name).join(", ")
        );
    });
}


// ---------------------------------------------------------------------------
// 16. MIN/MAX CONSTRAINTS
// ---------------------------------------------------------------------------

function applySimpleConstraints(items) {
    for (const item of items) {
        if (item.finalSize === null) {
            item.finalSize = item.basis;
        }

        if (item.minSize !== null) {
            item.finalSize = Math.max(
                item.finalSize,
                item.minSize
            );
        }

        if (item.maxSize !== null) {
            item.finalSize = Math.min(
                item.finalSize,
                item.maxSize
            );
        }
    }

    return items;
}


function demonstrateConstraints() {
    console.log("\n=== 11. MIN/MAX CONSTRAINTS ===");

    const items = [
        new FlexItem({
            name: "Sidebar",
            basis: 200,
            grow: 1,
            minSize: 180,
            maxSize: 320
        }),
        new FlexItem({
            name: "Main",
            basis: 200,
            grow: 3,
            minSize: 300
        })
    ];

    resolveFlexibleSizes(1000, items);
    applySimpleConstraints(items);

    printItems(items);

    console.log(
        "A complete browser algorithm may freeze constrained items and redistribute remaining free space."
    );
}


// ---------------------------------------------------------------------------
// 17. RESPONSIVE CARD CALCULATION
// ---------------------------------------------------------------------------

function estimateColumns(
    viewportWidth,
    minimumCardWidth = 240,
    gap = 24
) {
    if (viewportWidth <= 0) {
        throw new Error("viewportWidth must be positive.");
    }

    if (minimumCardWidth <= 0) {
        throw new Error("minimumCardWidth must be positive.");
    }

    if (gap < 0) {
        throw new Error("gap cannot be negative.");
    }

    return Math.max(
        1,
        Math.floor(
            (viewportWidth + gap) /
            (minimumCardWidth + gap)
        )
    );
}


function demonstrateResponsiveDesign() {
    console.log("\n=== 12. RESPONSIVE DESIGN ===");

    for (const width of [360, 768, 1024, 1440, 1920]) {
        console.log(
            `${width}px viewport -> approximately ` +
            `${estimateColumns(width)} card(s) per row`
        );
    }

    console.log(
        "Typical CSS: flex-wrap: wrap; and flex: 1 1 240px."
    );
}


// ---------------------------------------------------------------------------
// 18. PERFORMANCE AND DEBUGGING
// ---------------------------------------------------------------------------

function demonstratePerformanceAndDebugging() {
    console.log("\n=== 13. PERFORMANCE AND DEBUGGING ===");

    const checklist = [
        "Identify the flex container.",
        "Determine the main axis from flex-direction.",
        "Inspect computed flex-basis.",
        "Inspect flex-grow and flex-shrink.",
        "Check min-width and min-height.",
        "Check max-width and max-height.",
        "Check wrapping and line formation.",
        "Inspect justify-content and align-items.",
        "Test long unbroken content.",
        "Avoid unnecessary JavaScript layout calculations.",
        "Batch DOM reads and writes.",
        "Use CSS Flexbox for static layout behavior."
    ];

    checklist.forEach(
        (item, index) =>
            console.log(`${index + 1}. ${item}`)
    );
}


// ---------------------------------------------------------------------------
// 19. ERROR HANDLING
// ---------------------------------------------------------------------------

function demonstrateValidation() {
    console.log("\n=== 14. VALIDATION ===");

    const invalidDefinitions = [
        {
            name: "Negative basis",
            basis: -10
        },
        {
            name: "Negative grow",
            basis: 100,
            grow: -1
        },
        {
            name: "Invalid bounds",
            basis: 100,
            minSize: 300,
            maxSize: 200
        }
    ];

    for (const definition of invalidDefinitions) {
        try {
            new FlexItem(definition);
        } catch (error) {
            console.log(`Caught: ${error.message}`);
        }
    }
}


// ---------------------------------------------------------------------------
// 20. TESTS
// ---------------------------------------------------------------------------

function assertAlmostEqual(actual, expected, tolerance = 0.000001) {
    if (Math.abs(actual - expected) > tolerance) {
        throw new Error(
            `Expected ${expected}, received ${actual}.`
        );
    }
}


function testGrowDistribution() {
    const items = [
        new FlexItem({
            name: "A",
            basis: 200,
            grow: 1
        }),
        new FlexItem({
            name: "B",
            basis: 200,
            grow: 3
        })
    ];

    resolveFlexibleSizes(1000, items);

    assertAlmostEqual(items[0].finalSize, 350);
    assertAlmostEqual(items[1].finalSize, 650);
}


function testShrinkDistribution() {
    const items = [
        new FlexItem({
            name: "A",
            basis: 400,
            shrink: 1
        }),
        new FlexItem({
            name: "B",
            basis: 300,
            shrink: 1
        })
    ];

    resolveFlexibleSizes(500, items);

    assertAlmostEqual(
        items[0].finalSize,
        500 - (200 * 400 / 700)
    );

    assertAlmostEqual(
        items[1].finalSize,
        500 - (200 * 300 / 700)
    );
}


function testOrder() {
    const items = [
        { name: "C", order: 2 },
        { name: "A", order: 0 },
        { name: "B", order: 1 }
    ];

    const result = [...items]
        .sort((a, b) => a.order - b.order)
        .map(item => item.name);

    const expected = ["A", "B", "C"];

    if (JSON.stringify(result) !== JSON.stringify(expected)) {
        throw new Error("Order test failed.");
    }
}


function runTests() {
    console.log("\n=== 15. TESTS ===");

    const tests = [
        testGrowDistribution,
        testShrinkDistribution,
        testOrder
    ];

    for (const test of tests) {
        test();
        console.log(`PASS: ${test.name}`);
    }

    console.log(`${tests.length} tests passed.`);
}


// ---------------------------------------------------------------------------
// 21. MAIN
// ---------------------------------------------------------------------------

function main() {
    console.log("=".repeat(78));
    console.log("ADVANCED FLEXBOX JAVASCRIPT STUDY PROGRAM");
    console.log("=".repeat(78));

    explainFundamentals();
    demonstrateGrow();
    demonstrateShrink();
    demonstrateBasis();
    demonstrateOrder();
    demonstrateAxes();
    demonstrateNestedLayouts();
    demonstrateSidebarPattern();
    demonstrateNavbarPattern();
    demonstrateWrapping();
    demonstrateConstraints();
    demonstrateResponsiveDesign();
    demonstratePerformanceAndDebugging();
    demonstrateValidation();
    runTests();

    /*
     * This function is intentionally not called automatically in a browser
     * because it would print a large educational log to the console.
     *
     * createBrowserFlexDemo() can be called from a browser environment when
     * an actual DOM demonstration is desired.
     */
}

main();

if (typeof window !== "undefined") {
    window.createBrowserFlexDemo = createBrowserFlexDemo;
}
