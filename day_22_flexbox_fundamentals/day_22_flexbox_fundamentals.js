/*
 * Flexbox Fundamentals: JavaScript Study File
 *
 * This file complements the Python study program by demonstrating how
 * Flexbox can be created, inspected, manipulated, and tested from
 * JavaScript in a browser environment.
 *
 * The examples are written so that the same file can run in a browser.
 * Browser-specific examples are activated when `document` is available.
 *
 * No external packages are required.
 */

// ---------------------------------------------------------------------------
// 1. FLEXBOX PROPERTY MODEL
// ---------------------------------------------------------------------------

const flexboxProperties = {
    container: {
        display: ["flex", "inline-flex"],
        flexDirection: ["row", "row-reverse", "column", "column-reverse"],
        flexWrap: ["nowrap", "wrap", "wrap-reverse"],
        justifyContent: [
            "flex-start",
            "flex-end",
            "center",
            "space-between",
            "space-around",
            "space-evenly"
        ],
        alignItems: [
            "stretch",
            "flex-start",
            "flex-end",
            "center",
            "baseline"
        ],
        alignContent: [
            "stretch",
            "flex-start",
            "flex-end",
            "center",
            "space-between",
            "space-around",
            "space-evenly"
        ],
        gap: "length or row-gap column-gap"
    },

    item: {
        order: "integer",
        flexGrow: "number",
        flexShrink: "number",
        flexBasis: "auto | content | length | percentage",
        flex: "grow shrink basis",
        alignSelf: [
            "auto",
            "stretch",
            "flex-start",
            "flex-end",
            "center",
            "baseline"
        ]
    }
};

console.log("Flexbox property model:", flexboxProperties);


// ---------------------------------------------------------------------------
// 2. BEGINNER: CREATING A FLEX CONTAINER
// ---------------------------------------------------------------------------

function createFlexContainer() {
    const container = document.createElement("div");

    container.style.display = "flex";
    container.style.flexDirection = "row";
    container.style.justifyContent = "space-between";
    container.style.alignItems = "center";
    container.style.gap = "16px";

    return container;
}

function createFlexItem(label) {
    const item = document.createElement("div");

    item.textContent = label;
    item.style.padding = "16px";
    item.style.border = "1px solid #999";

    return item;
}


// ---------------------------------------------------------------------------
// 3. FLEX DIRECTION
// ---------------------------------------------------------------------------

function demonstrateDirections(container) {
    const directions = [
        "row",
        "row-reverse",
        "column",
        "column-reverse"
    ];

    directions.forEach((direction) => {
        container.style.flexDirection = direction;

        console.log(
            `flex-direction=${direction}: ` +
            "the main axis changes according to the direction."
        );
    });

    // Restore a predictable default.
    container.style.flexDirection = "row";
}


// ---------------------------------------------------------------------------
// 4. JUSTIFY-CONTENT
// ---------------------------------------------------------------------------

function demonstrateJustifyContent(container) {
    const values = [
        "flex-start",
        "flex-end",
        "center",
        "space-between",
        "space-around",
        "space-evenly"
    ];

    values.forEach((value) => {
        container.style.justifyContent = value;

        console.log(
            `justify-content=${value}: ` +
            "distributes free space along the main axis."
        );
    });

    container.style.justifyContent = "flex-start";
}


// ---------------------------------------------------------------------------
// 5. ALIGN-ITEMS
// ---------------------------------------------------------------------------

function demonstrateAlignItems(container) {
    const values = [
        "stretch",
        "flex-start",
        "flex-end",
        "center",
        "baseline"
    ];

    values.forEach((value) => {
        container.style.alignItems = value;

        console.log(
            `align-items=${value}: ` +
            "controls alignment on the cross axis."
        );
    });

    container.style.alignItems = "center";
}


// ---------------------------------------------------------------------------
// 6. FLEX-GROW, FLEX-SHRINK, FLEX-BASIS
// ---------------------------------------------------------------------------

function configureFlexibleItems(items) {
    if (items.length < 3) {
        throw new Error("At least three items are required.");
    }

    items[0].style.flex = "1 1 150px";
    items[1].style.flex = "2 1 150px";
    items[2].style.flex = "1 1 150px";

    console.log(
        "The middle item receives twice the positive free-space share "
        "of each neighboring item when growth is possible."
    );
}


// ---------------------------------------------------------------------------
// 7. FLEX SHORTHAND PARSER
// ---------------------------------------------------------------------------

function parseFlexShorthand(value) {
    if (typeof value !== "string" || value.trim() === "") {
        throw new TypeError("flex shorthand must be a non-empty string.");
    }

    const parts = value.trim().split(/\s+/);

    if (parts.length === 1) {
        const token = parts[0];

        if (token === "none") {
            return {
                grow: 0,
                shrink: 0,
                basis: "auto"
            };
        }

        if (token === "auto") {
            return {
                grow: 1,
                shrink: 1,
                basis: "auto"
            };
        }

        if (token === "initial") {
            return {
                grow: 0,
                shrink: 1,
                basis: "auto"
            };
        }

        const grow = Number(token);

        if (Number.isFinite(grow) && grow >= 0) {
            return {
                grow,
                shrink: 1,
                basis: "0%"
            };
        }
    }

    if (parts.length === 3) {
        const grow = Number(parts[0]);
        const shrink = Number(parts[1]);

        if (
            Number.isFinite(grow) &&
            Number.isFinite(shrink) &&
            grow >= 0 &&
            shrink >= 0
        ) {
            return {
                grow,
                shrink,
                basis: parts[2]
            };
        }
    }

    throw new Error(`Unsupported flex shorthand: ${value}`);
}

function demonstrateFlexShorthand() {
    const examples = [
        "1",
        "2",
        "1 1 200px",
        "0 1 auto",
        "none",
        "auto",
        "initial"
    ];

    examples.forEach((example) => {
        console.log(example, "=>", parseFlexShorthand(example));
    });
}


// ---------------------------------------------------------------------------
// 8. SIMPLIFIED FLEX GROWTH CALCULATION
// ---------------------------------------------------------------------------

function distributePositiveFreeSpace(containerSize, items, gap = 0) {
    if (!Number.isFinite(containerSize) || containerSize < 0) {
        throw new RangeError("containerSize must be non-negative.");
    }

    if (!Number.isFinite(gap) || gap < 0) {
        throw new RangeError("gap must be non-negative.");
    }

    if (!Array.isArray(items) || items.length === 0) {
        return [];
    }

    const totalBasis = items.reduce(
        (sum, item) => sum + item.basis,
        0
    );

    const totalGap = Math.max(0, items.length - 1) * gap;
    const freeSpace = containerSize - totalBasis - totalGap;

    if (freeSpace <= 0) {
        return items.map((item) => ({
            name: item.name,
            size: item.basis
        }));
    }

    const totalGrow = items.reduce(
        (sum, item) => sum + item.grow,
        0
    );

    if (totalGrow === 0) {
        return items.map((item) => ({
            name: item.name,
            size: item.basis
        }));
    }

    return items.map((item) => ({
        name: item.name,
        size: item.basis + freeSpace * item.grow / totalGrow
    }));
}

function demonstrateGrowthCalculation() {
    const items = [
        { name: "A", basis: 100, grow: 1 },
        { name: "B", basis: 100, grow: 2 },
        { name: "C", basis: 100, grow: 1 }
    ];

    const result = distributePositiveFreeSpace(500, items, 10);

    console.log("Simplified positive free-space calculation:");

    result.forEach((item) => {
        console.log(`${item.name}: ${item.size.toFixed(2)}px`);
    });
}


// ---------------------------------------------------------------------------
// 9. FLEX-WRAP AND RESPONSIVE CARDS
// ---------------------------------------------------------------------------

function createCard(title, minimumWidth = 220) {
    return {
        title,
        minimumWidth
    };
}

function createResponsiveRows(containerWidth, cards, gap = 16) {
    if (containerWidth <= 0) {
        throw new RangeError("containerWidth must be positive.");
    }

    if (gap < 0) {
        throw new RangeError("gap cannot be negative.");
    }

    const rows = [];
    let currentRow = [];
    let currentWidth = 0;

    for (const card of cards) {
        if (card.minimumWidth <= 0) {
            throw new RangeError(
                `Invalid minimum width for ${card.title}.`
            );
        }

        const requiredGap = currentRow.length > 0 ? gap : 0;

        if (
            currentRow.length > 0 &&
            currentWidth +
            requiredGap +
            card.minimumWidth >
            containerWidth
        ) {
            rows.push(currentRow);
            currentRow = [];
            currentWidth = 0;
        }

        const newGap = currentRow.length > 0 ? gap : 0;

        currentRow.push(card);
        currentWidth += newGap + card.minimumWidth;
    }

    if (currentRow.length > 0) {
        rows.push(currentRow);
    }

    return rows;
}

function demonstrateResponsiveRows() {
    const cards = [
        createCard("Python"),
        createCard("JavaScript"),
        createCard("C++"),
        createCard("CSS"),
        createCard("Security")
    ];

    [1000, 700, 450].forEach((width) => {
        const rows = createResponsiveRows(width, cards, 20);

        console.log(`Container width: ${width}px`);

        rows.forEach((row, index) => {
            console.log(
                `  Row ${index + 1}: ` +
                row.map((card) => card.title).join(", ")
            );
        });
    });
}


// ---------------------------------------------------------------------------
// 10. CSS ORDER AND ACCESSIBILITY
// ---------------------------------------------------------------------------

function demonstrateOrder(items) {
    if (!Array.isArray(items)) {
        throw new TypeError("items must be an array.");
    }

    items.forEach((item) => {
        if (!Number.isInteger(item.order)) {
            throw new TypeError(
                `Invalid order value for ${item.name}.`
            );
        }
    });

    const visualOrder = [...items]
        .sort((a, b) => a.order - b.order)
        .map((item) => item.name);

    console.log("Source order:", items.map((item) => item.name));
    console.log("Visual order:", visualOrder);
    console.log(
        "Accessibility principle: source order should remain meaningful "
        "even when visual presentation changes."
    );
}


// ---------------------------------------------------------------------------
// 11. AUTO MARGIN
// ---------------------------------------------------------------------------

function explainAutoMargin(container) {
    const navigation = container.querySelector(".navigation");
    const actions = container.querySelector(".actions");

    if (!navigation || !actions) {
        throw new Error(
            "Expected .navigation and .actions elements."
        );
    }

    // In a row flex container, auto margin consumes available main-axis
    // free space. This pushes the actions group toward the opposite side.
    actions.style.marginInlineStart = "auto";

    console.log(
        "Applied margin-inline-start:auto to the actions group."
    );
}


// ---------------------------------------------------------------------------
// 12. DOM-BASED FLEXBOX DEMONSTRATION
// ---------------------------------------------------------------------------

function buildInteractiveDemo(root) {
    if (!root) {
        throw new Error("A root element is required.");
    }

    root.innerHTML = "";

    const container = document.createElement("div");

    container.style.display = "flex";
    container.style.flexDirection = "row";
    container.style.flexWrap = "wrap";
    container.style.gap = "12px";
    container.style.padding = "12px";
    container.style.border = "2px solid #777";

    const controls = document.createElement("div");

    controls.style.display = "flex";
    controls.style.flexWrap = "wrap";
    controls.style.gap = "8px";
    controls.style.marginBottom = "16px";

    const directionSelect = document.createElement("select");
    const directions = [
        "row",
        "row-reverse",
        "column",
        "column-reverse"
    ];

    directions.forEach((direction) => {
        const option = document.createElement("option");
        option.value = direction;
        option.textContent = direction;
        directionSelect.appendChild(option);
    });

    const justifySelect = document.createElement("select");
    const justifyValues = [
        "flex-start",
        "flex-end",
        "center",
        "space-between",
        "space-around",
        "space-evenly"
    ];

    justifyValues.forEach((value) => {
        const option = document.createElement("option");
        option.value = value;
        option.textContent = value;
        justifySelect.appendChild(option);
    });

    const alignSelect = document.createElement("select");
    const alignValues = [
        "stretch",
        "flex-start",
        "flex-end",
        "center",
        "baseline"
    ];

    alignValues.forEach((value) => {
        const option = document.createElement("option");
        option.value = value;
        option.textContent = value;
        alignSelect.appendChild(option);
    });

    const wrapButton = document.createElement("button");
    wrapButton.textContent = "Toggle Wrap";

    controls.appendChild(directionSelect);
    controls.appendChild(justifySelect);
    controls.appendChild(alignSelect);
    controls.appendChild(wrapButton);

    for (let index = 1; index <= 6; index += 1) {
        const item = createFlexItem(`Item ${index}`);

        item.style.minWidth = "100px";
        item.style.boxSizing = "border-box";

        container.appendChild(item);
    }

    directionSelect.addEventListener("change", (event) => {
        container.style.flexDirection = event.target.value;
    });

    justifySelect.addEventListener("change", (event) => {
        container.style.justifyContent = event.target.value;
    });

    alignSelect.addEventListener("change", (event) => {
        container.style.alignItems = event.target.value;
    });

    let wrapping = true;

    wrapButton.addEventListener("click", () => {
        wrapping = !wrapping;

        container.style.flexWrap = wrapping
            ? "wrap"
            : "nowrap";
    });

    root.appendChild(controls);
    root.appendChild(container);

    return container;
}


// ---------------------------------------------------------------------------
// 13. CSSOM INSPECTION
// ---------------------------------------------------------------------------

function inspectFlexElement(element) {
    if (!(element instanceof Element)) {
        throw new TypeError("element must be a DOM Element.");
    }

    const styles = getComputedStyle(element);

    return {
        display: styles.display,
        flexDirection: styles.flexDirection,
        flexWrap: styles.flexWrap,
        justifyContent: styles.justifyContent,
        alignItems: styles.alignItems,
        alignContent: styles.alignContent,
        gap: styles.gap
    };
}


// ---------------------------------------------------------------------------
// 14. PERFORMANCE CONSIDERATIONS
// ---------------------------------------------------------------------------

function demonstrateBatchStyleUpdates(container, items) {
    /*
     * Reading layout information such as offsetWidth can force the browser
     * to calculate layout. Repeated read/write/read/write sequences can
     * contribute to layout thrashing.
     *
     * A better pattern is often:
     *   1. read required measurements,
     *   2. calculate desired values,
     *   3. perform writes together.
     */

    const containerWidth = container.clientWidth;

    const targetWidth = Math.max(
        100,
        Math.floor(containerWidth / Math.max(1, items.length))
    );

    items.forEach((item) => {
        item.style.flexBasis = `${targetWidth}px`;
    });

    return targetWidth;
}


// ---------------------------------------------------------------------------
// 15. VALIDATION
// ---------------------------------------------------------------------------

function validateFlexConfiguration(configuration) {
    const errors = [];

    const validDirections = flexboxProperties.container.flexDirection;
    const validWraps = flexboxProperties.container.flexWrap;
    const validJustify = flexboxProperties.container.justifyContent;
    const validAlign = flexboxProperties.container.alignItems;

    if (!validDirections.includes(configuration.direction)) {
        errors.push("Invalid flex-direction.");
    }

    if (!validWraps.includes(configuration.wrap)) {
        errors.push("Invalid flex-wrap.");
    }

    if (!validJustify.includes(configuration.justify)) {
        errors.push("Invalid justify-content.");
    }

    if (!validAlign.includes(configuration.align)) {
        errors.push("Invalid align-items.");
    }

    if (
        !Number.isFinite(configuration.gap) ||
        configuration.gap < 0
    ) {
        errors.push("gap must be a non-negative number.");
    }

    return errors;
}


// ---------------------------------------------------------------------------
// 16. TESTS
// ---------------------------------------------------------------------------

function runTests() {
    console.log("\n=== JAVASCRIPT TESTS ===");

    const parsed = parseFlexShorthand("1 1 200px");

    console.assert(parsed.grow === 1);
    console.assert(parsed.shrink === 1);
    console.assert(parsed.basis === "200px");

    const result = distributePositiveFreeSpace(
        500,
        [
            { name: "A", basis: 100, grow: 1 },
            { name: "B", basis: 100, grow: 2 },
            { name: "C", basis: 100, grow: 1 }
        ],
        10
    );

    console.assert(result.length === 3);
    console.assert(result[1].size > result[0].size);

    const rows = createResponsiveRows(
        450,
        [
            createCard("A"),
            createCard("B"),
            createCard("C")
        ],
        20
    );

    console.assert(rows.length === 2);

    const validationErrors = validateFlexConfiguration({
        direction: "row",
        wrap: "wrap",
        justify: "center",
        align: "center",
        gap: 16
    });

    console.assert(validationErrors.length === 0);

    console.log("All JavaScript assertions passed.");
}


// ---------------------------------------------------------------------------
// 17. BROWSER ENTRY POINT
// ---------------------------------------------------------------------------

function runBrowserExamples() {
    if (typeof document === "undefined") {
        return;
    }

    const container = createFlexContainer();

    for (let index = 1; index <= 3; index += 1) {
        container.appendChild(createFlexItem(`Item ${index}`));
    }

    demonstrateDirections(container);
    demonstrateJustifyContent(container);
    demonstrateAlignItems(container);

    configureFlexibleItems(
        Array.from(container.children)
    );

    console.log(
        "Created example Flexbox container:",
        container
    );

    const existingDemoRoot = document.querySelector(
        "[data-flexbox-demo]"
    );

    if (existingDemoRoot) {
        buildInteractiveDemo(existingDemoRoot);
    }
}


// ---------------------------------------------------------------------------
// 18. RUN LANGUAGE-LEVEL EXAMPLES
// ---------------------------------------------------------------------------

demonstrateFlexShorthand();
demonstrateGrowthCalculation();
demonstrateResponsiveRows();

demonstrateOrder([
    { name: "Header", order: 0 },
    { name: "Main", order: 2 },
    { name: "Sidebar", order: 1 }
]);

runTests();
runBrowserExamples();

console.log(
    "Flexbox study file loaded. " +
    "Use the browser console to inspect the examples."
);
