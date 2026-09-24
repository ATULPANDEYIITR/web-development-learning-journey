/*
 * CSS Grid Fundamentals
 * ======================
 *
 * A browser-executable companion study for:
 *
 * - Grid containers
 * - Rows
 * - Columns
 * - Tracks
 * - Grid cells
 * - Grid lines
 * - Gaps
 * - Grid areas
 * - Explicit and implicit grids
 * - fr units
 * - repeat()
 * - minmax()
 * - auto-fit
 * - auto-fill
 * - Item placement
 * - Spanning
 * - Alignment
 * - Responsive layouts
 *
 * The script creates its own demonstration page when executed in a browser.
 * It also contains JavaScript calculations that make CSS Grid sizing rules
 * easier to understand numerically.
 *
 * Run:
 * 1. Save as css-grid-fundamentals.js.
 * 2. Open a browser developer console.
 * 3. Paste the file into the console, or load it from an HTML page.
 */

"use strict";


// -----------------------------------------------------------------------------
// Section 1: Utility functions
// -----------------------------------------------------------------------------

function createElement(tagName, className, textContent = "") {
    const element = document.createElement(tagName);

    if (className) {
        element.className = className;
    }

    if (textContent) {
        element.textContent = textContent;
    }

    return element;
}


function createSection(title, description = "") {
    const section = createElement("section", "study-section");

    const heading = createElement("h2", "", title);
    section.appendChild(heading);

    if (description) {
        const paragraph = createElement("p", "", description);
        section.appendChild(paragraph);
    }

    return section;
}


function createCodeDisplay(code) {
    const pre = createElement("pre", "code-display");
    pre.textContent = code;
    return pre;
}


function logConcept(title, value) {
    console.log(`${title}:`, value);
}


// -----------------------------------------------------------------------------
// Section 2: Basic CSS Grid demonstration
// -----------------------------------------------------------------------------

function createBasicGrid() {
    const section = createSection(
        "Grid container, rows, columns, tracks, and cells",
        "A basic four-column grid demonstrates the relationship between tracks and items."
    );

    const grid = createElement("div", "demo-grid basic-grid");

    const items = [
        ["Header", "header"],
        ["Navigation", "navigation"],
        ["Main", "main"],
        ["Aside", "aside"],
        ["Footer", "footer"]
    ];

    for (const [label, className] of items) {
        const item = createElement("div", `grid-item ${className}`, label);
        grid.appendChild(item);
    }

    section.appendChild(grid);

    section.appendChild(
        createCodeDisplay(`
.demo-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    grid-template-rows: 80px 180px 80px;
    gap: 16px;
}
        `.trim())
    );

    return section;
}


// -----------------------------------------------------------------------------
// Section 3: Grid line demonstration
// -----------------------------------------------------------------------------

function createGridLineDemo() {
    const section = createSection(
        "Grid lines and spanning",
        "Grid lines define the boundaries between tracks."
    );

    const grid = createElement("div", "demo-grid line-grid");

    for (let index = 1; index <= 8; index += 1) {
        const item = createElement("div", "grid-item", `Item ${index}`);
        grid.appendChild(item);
    }

    section.appendChild(grid);

    section.appendChild(
        createCodeDisplay(`
.line-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
}

.line-grid .grid-item:first-child {
    grid-column: 1 / 3;
}
        `.trim())
    );

    return section;
}


// -----------------------------------------------------------------------------
// Section 4: Grid areas
// -----------------------------------------------------------------------------

function createGridAreaDemo() {
    const section = createSection(
        "Named grid areas",
        "grid-template-areas gives a layout a readable spatial structure."
    );

    const grid = createElement("div", "area-grid");

    const items = [
        ["Header", "area-header"],
        ["Sidebar", "area-sidebar"],
        ["Main content", "area-main"],
        ["Aside", "area-aside"],
        ["Footer", "area-footer"]
    ];

    for (const [label, className] of items) {
        grid.appendChild(createElement("div", `grid-item ${className}`, label));
    }

    section.appendChild(grid);

    section.appendChild(
        createCodeDisplay(`
.area-grid {
    display: grid;
    grid-template-columns: 220px 1fr 240px;
    grid-template-rows: auto 1fr auto;
    grid-template-areas:
        "header header header"
        "sidebar main aside"
        "footer footer footer";
    gap: 16px;
}

.area-header { grid-area: header; }
.area-sidebar { grid-area: sidebar; }
.area-main { grid-area: main; }
.area-aside { grid-area: aside; }
.area-footer { grid-area: footer; }
        `.trim())
    );

    return section;
}


// -----------------------------------------------------------------------------
// Section 5: Responsive card grid
// -----------------------------------------------------------------------------

function createResponsiveCardDemo() {
    const section = createSection(
        "Responsive cards with minmax() and auto-fit",
        "The browser chooses how many columns can fit while maintaining a minimum card width."
    );

    const grid = createElement("div", "responsive-card-grid");

    const cards = [
        "Analytics",
        "Security",
        "Database",
        "Cloud",
        "Networking",
        "Artificial Intelligence",
        "Automation",
        "Monitoring"
    ];

    for (const title of cards) {
        const card = createElement("article", "card");
        card.appendChild(createElement("h3", "", title));
        card.appendChild(
            createElement(
                "p",
                "",
                "This card participates in a responsive CSS Grid."
            )
        );
        grid.appendChild(card);
    }

    section.appendChild(grid);

    section.appendChild(
        createCodeDisplay(`
.responsive-card-grid {
    display: grid;
    grid-template-columns:
        repeat(auto-fit, minmax(220px, 1fr));
    gap: 20px;
}
        `.trim())
    );

    return section;
}


// -----------------------------------------------------------------------------
// Section 6: Nested Grid
// -----------------------------------------------------------------------------

function createNestedGridDemo() {
    const section = createSection(
        "Nested grids",
        "A grid item can become another grid container."
    );

    const outer = createElement("div", "nested-outer");

    const sidebar = createElement("div", "grid-item nested-sidebar", "Sidebar");

    const main = createElement("div", "nested-main");

    const innerItems = [
        "Metric A",
        "Metric B",
        "Metric C",
        "Metric D"
    ];

    for (const label of innerItems) {
        main.appendChild(createElement("div", "grid-item", label));
    }

    outer.appendChild(sidebar);
    outer.appendChild(main);

    section.appendChild(outer);

    section.appendChild(
        createCodeDisplay(`
.nested-outer {
    display: grid;
    grid-template-columns: 220px 1fr;
    gap: 16px;
}

.nested-main {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
}
        `.trim())
    );

    return section;
}


// -----------------------------------------------------------------------------
// Section 7: Alignment demonstration
// -----------------------------------------------------------------------------

function createAlignmentDemo() {
    const section = createSection(
        "Alignment",
        "Grid has separate controls for item alignment and alignment of the entire grid."
    );

    const container = createElement("div", "alignment-grid");

    const alignments = ["start", "center", "end"];

    for (const alignment of alignments) {
        const cell = createElement("div", "alignment-cell");
        cell.style.alignItems = alignment;

        const box = createElement(
            "div",
            "alignment-box",
            alignment
        );

        cell.appendChild(box);
        container.appendChild(cell);
    }

    section.appendChild(container);

    section.appendChild(
        createCodeDisplay(`
justify-items: controls horizontal alignment
align-items: controls vertical alignment

justify-content: controls the grid as a whole horizontally
align-content: controls the grid as a whole vertically

justify-self / align-self:
control one particular grid item
        `.trim())
    );

    return section;
}


// -----------------------------------------------------------------------------
// Section 8: Grid sizing calculations
// -----------------------------------------------------------------------------

function calculateEqualFrTracks(containerWidth, trackCount, gap) {
    if (!Number.isFinite(containerWidth) || containerWidth < 0) {
        throw new RangeError("containerWidth must be non-negative.");
    }

    if (!Number.isInteger(trackCount) || trackCount <= 0) {
        throw new RangeError("trackCount must be a positive integer.");
    }

    if (!Number.isFinite(gap) || gap < 0) {
        throw new RangeError("gap must be non-negative.");
    }

    const totalGap = Math.max(0, trackCount - 1) * gap;
    const remainingSpace = containerWidth - totalGap;

    if (remainingSpace < 0) {
        throw new RangeError("Gaps exceed the available container width.");
    }

    const trackSize = remainingSpace / trackCount;

    return Array.from(
        { length: trackCount },
        () => trackSize
    );
}


function calculateWeightedFrTracks(containerWidth, fractions, gap) {
    if (!Array.isArray(fractions) || fractions.length === 0) {
        throw new TypeError("fractions must be a non-empty array.");
    }

    if (fractions.some(value => !Number.isFinite(value) || value <= 0)) {
        throw new RangeError("Every fraction must be positive.");
    }

    if (!Number.isFinite(containerWidth) || containerWidth < 0) {
        throw new RangeError("containerWidth must be non-negative.");
    }

    if (!Number.isFinite(gap) || gap < 0) {
        throw new RangeError("gap must be non-negative.");
    }

    const totalGap = Math.max(0, fractions.length - 1) * gap;
    const remainingSpace = containerWidth - totalGap;

    if (remainingSpace < 0) {
        throw new RangeError("Gaps exceed the available width.");
    }

    const totalFraction = fractions.reduce(
        (sum, fraction) => sum + fraction,
        0
    );

    return fractions.map(
        fraction => remainingSpace * fraction / totalFraction
    );
}


function calculateResponsiveColumnCount(
    containerWidth,
    minimumCardWidth,
    gap
) {
    if (containerWidth <= 0) {
        throw new RangeError("Container width must be positive.");
    }

    if (minimumCardWidth <= 0) {
        throw new RangeError("Minimum card width must be positive.");
    }

    if (gap < 0) {
        throw new RangeError("Gap cannot be negative.");
    }

    return Math.max(
        1,
        Math.floor(
            (containerWidth + gap) /
            (minimumCardWidth + gap)
        )
    );
}


// -----------------------------------------------------------------------------
// Section 9: Numerical sizing study
// -----------------------------------------------------------------------------

function runSizingCalculations() {
    console.group("CSS Grid sizing calculations");

    const equalTracks = calculateEqualFrTracks(
        1000,
        4,
        20
    );

    logConcept("Four equal 1fr tracks", equalTracks);

    const weightedTracks = calculateWeightedFrTracks(
        1200,
        [1, 2, 1],
        24
    );

    logConcept("1fr 2fr 1fr tracks", weightedTracks);

    const widths = [320, 500, 768, 1024, 1440];

    const responsiveResults = widths.map(width => ({
        width,
        columns: calculateResponsiveColumnCount(
            width,
            220,
            20
        )
    }));

    console.table(responsiveResults);

    console.groupEnd();
}


// -----------------------------------------------------------------------------
// Section 10: Practical grid inspection
// -----------------------------------------------------------------------------

function inspectGrid(element) {
    if (!(element instanceof HTMLElement)) {
        throw new TypeError("inspectGrid expects an HTMLElement.");
    }

    const styles = window.getComputedStyle(element);

    return {
        display: styles.display,
        gridTemplateColumns: styles.gridTemplateColumns,
        gridTemplateRows: styles.gridTemplateRows,
        gridTemplateAreas: styles.gridTemplateAreas,
        columnGap: styles.columnGap,
        rowGap: styles.rowGap,
        justifyItems: styles.justifyItems,
        alignItems: styles.alignItems,
        justifyContent: styles.justifyContent,
        alignContent: styles.alignContent,
        gridAutoFlow: styles.gridAutoFlow,
        gridAutoColumns: styles.gridAutoColumns,
        gridAutoRows: styles.gridAutoRows
    };
}


// -----------------------------------------------------------------------------
// Section 11: Demonstrating explicit and implicit placement
// -----------------------------------------------------------------------------

function createExplicitImplicitDemo() {
    const section = createSection(
        "Explicit and implicit grid tracks",
        "Explicit tracks are declared directly. Implicit tracks can be generated when content requires additional space."
    );

    const grid = createElement("div", "explicit-implicit-grid");

    for (let index = 1; index <= 7; index += 1) {
        const item = createElement(
            "div",
            "grid-item",
            `Item ${index}`
        );

        if (index === 7) {
            item.style.gridRow = "4";
        }

        grid.appendChild(item);
    }

    section.appendChild(grid);

    section.appendChild(
        createCodeDisplay(`
.explicit-implicit-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    grid-template-rows: repeat(2, 80px);
    grid-auto-rows: 100px;
}
        `.trim())
    );

    return section;
}


// -----------------------------------------------------------------------------
// Section 12: CSS generated by JavaScript
// -----------------------------------------------------------------------------

function injectStyles() {
    const style = document.createElement("style");

    style.textContent = `
        :root {
            font-family: Arial, Helvetica, sans-serif;
        }

        body {
            margin: 0;
            padding: 24px;
            background: #111;
            color: #eee;
        }

        .study-container {
            max-width: 1200px;
            margin: 0 auto;
        }

        .study-section {
            margin-bottom: 32px;
            padding: 20px;
            border: 1px solid #444;
            border-radius: 12px;
        }

        .study-section h2 {
            margin-top: 0;
        }

        .demo-grid,
        .area-grid,
        .nested-outer,
        .responsive-card-grid,
        .alignment-grid,
        .explicit-implicit-grid {
            display: grid;
            gap: 16px;
        }

        .basic-grid {
            grid-template-columns: repeat(4, 1fr);
            grid-template-rows: 80px 180px 80px;
        }

        .basic-grid .header {
            grid-column: 1 / -1;
        }

        .basic-grid .navigation {
            grid-column: 1;
        }

        .basic-grid .main {
            grid-column: 2 / 4;
        }

        .basic-grid .aside {
            grid-column: 4;
        }

        .basic-grid .footer {
            grid-column: 1 / -1;
        }

        .line-grid {
            grid-template-columns: repeat(4, 1fr);
        }

        .line-grid .grid-item:first-child {
            grid-column: 1 / 3;
        }

        .area-grid {
            grid-template-columns: 220px 1fr 240px;
            grid-template-rows: auto minmax(180px, 1fr) auto;
            grid-template-areas:
                "header header header"
                "sidebar main aside"
                "footer footer footer";
        }

        .area-header {
            grid-area: header;
        }

        .area-sidebar {
            grid-area: sidebar;
        }

        .area-main {
            grid-area: main;
        }

        .area-aside {
            grid-area: aside;
        }

        .area-footer {
            grid-area: footer;
        }

        .responsive-card-grid {
            grid-template-columns:
                repeat(auto-fit, minmax(220px, 1fr));
        }

        .nested-outer {
            grid-template-columns: 220px 1fr;
        }

        .nested-main {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
        }

        .alignment-grid {
            grid-template-columns: repeat(3, 1fr);
            min-height: 180px;
        }

        .alignment-cell {
            display: grid;
            justify-items: center;
            align-items: center;
            min-height: 140px;
            border: 1px dashed #555;
        }

        .alignment-box {
            padding: 20px;
            border: 1px solid #888;
        }

        .explicit-implicit-grid {
            grid-template-columns: repeat(3, 1fr);
            grid-template-rows: repeat(2, 80px);
            grid-auto-rows: 100px;
        }

        .grid-item,
        .card {
            padding: 20px;
            border: 1px solid #666;
            border-radius: 8px;
            box-sizing: border-box;
        }

        .card h3 {
            margin-top: 0;
        }

        .code-display {
            overflow-x: auto;
            padding: 16px;
            border: 1px solid #444;
            border-radius: 8px;
            white-space: pre-wrap;
        }

        @media (max-width: 800px) {
            .area-grid {
                grid-template-columns: 1fr;
                grid-template-areas:
                    "header"
                    "main"
                    "sidebar"
                    "aside"
                    "footer";
            }

            .nested-outer {
                grid-template-columns: 1fr;
            }
        }
    `;

    document.head.appendChild(style);
}


// -----------------------------------------------------------------------------
// Section 13: Build the complete study page
// -----------------------------------------------------------------------------

function buildStudyPage() {
    injectStyles();

    const existingContainer = document.querySelector(
        ".css-grid-study-container"
    );

    if (existingContainer) {
        existingContainer.remove();
    }

    const container = createElement(
        "main",
        "study-container css-grid-study-container"
    );

    const title = createElement(
        "h1",
        "",
        "CSS Grid Fundamentals"
    );

    const introduction = createElement(
        "p",
        "",
        "Interactive demonstrations of containers, tracks, rows, columns, gaps, placement, and named grid areas."
    );

    container.appendChild(title);
    container.appendChild(introduction);

    container.appendChild(createBasicGrid());
    container.appendChild(createGridLineDemo());
    container.appendChild(createGridAreaDemo());
    container.appendChild(createResponsiveCardDemo());
    container.appendChild(createNestedGridDemo());
    container.appendChild(createAlignmentDemo());
    container.appendChild(createExplicitImplicitDemo());

    document.body.appendChild(container);

    return container;
}


// -----------------------------------------------------------------------------
// Section 14: Browser measurements
// -----------------------------------------------------------------------------

function reportLiveMeasurements() {
    const grid = document.querySelector(".responsive-card-grid");

    if (!grid) {
        return;
    }

    const styles = inspectGrid(grid);
    const rectangle = grid.getBoundingClientRect();

    console.group("Live CSS Grid measurement");

    console.log("Grid width:", rectangle.width);
    console.log("Grid height:", rectangle.height);
    console.log("Computed columns:", styles.gridTemplateColumns);
    console.log("Computed rows:", styles.gridTemplateRows);
    console.log("Column gap:", styles.columnGap);
    console.log("Row gap:", styles.rowGap);

    console.groupEnd();
}


// -----------------------------------------------------------------------------
// Section 15: Error handling examples
// -----------------------------------------------------------------------------

function demonstrateValidation() {
    console.group("CSS Grid validation examples");

    const cases = [
        () => calculateEqualFrTracks(1000, 4, 20),
        () => calculateEqualFrTracks(1000, 0, 20),
        () => calculateEqualFrTracks(100, 3, 60),
        () => calculateResponsiveColumnCount(800, 220, 20)
    ];

    cases.forEach((operation, index) => {
        try {
            const result = operation();
            console.log(`Case ${index + 1}:`, result);
        } catch (error) {
            console.error(
                `Case ${index + 1} failed safely:`,
                error.message
            );
        }
    });

    console.groupEnd();
}


// -----------------------------------------------------------------------------
// Section 16: Responsive resize observer
// -----------------------------------------------------------------------------

function observeResponsiveGrid() {
    const grid = document.querySelector(".responsive-card-grid");

    if (!grid || typeof ResizeObserver === "undefined") {
        return;
    }

    const observer = new ResizeObserver(entries => {
        for (const entry of entries) {
            const width = entry.contentRect.width;

            const columns = calculateResponsiveColumnCount(
                width,
                220,
                20
            );

            console.log(
                `Responsive grid width=${width.toFixed(1)}px, `
                + `estimated minimum columns=${columns}`
            );
        }
    });

    observer.observe(grid);
}


// -----------------------------------------------------------------------------
// Section 17: Application-style dashboard
// -----------------------------------------------------------------------------

function createDashboardExample() {
    const section = createSection(
        "Industry-style dashboard layout",
        "A twelve-column grid can provide a flexible foundation for dashboards."
    );

    const dashboard = createElement("div", "dashboard-grid");

    const widgets = [
        ["System Status", "status"],
        ["Revenue", "revenue"],
        ["Users", "users"],
        ["Activity", "activity"],
        ["Operations", "operations"],
        ["Alerts", "alerts"]
    ];

    for (const [label, className] of widgets) {
        const widget = createElement(
            "article",
            `dashboard-widget ${className}`
        );

        widget.appendChild(createElement("h3", "", label));
        widget.appendChild(
            createElement(
                "p",
                "",
                "Dashboard content area"
            )
        );

        dashboard.appendChild(widget);
    }

    section.appendChild(dashboard);

    section.appendChild(
        createCodeDisplay(`
.dashboard-grid {
    display: grid;
    grid-template-columns: repeat(12, 1fr);
    gap: 16px;
}

.status {
    grid-column: span 8;
}

.revenue,
.users {
    grid-column: span 2;
}

.activity {
    grid-column: span 6;
}

.operations {
    grid-column: span 4;
}

.alerts {
    grid-column: span 2;
}
        `.trim())
    );

    const style = document.createElement("style");

    style.textContent = `
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(12, minmax(0, 1fr));
            gap: 16px;
        }

        .dashboard-widget {
            min-width: 0;
            padding: 20px;
            border: 1px solid #666;
            border-radius: 8px;
        }

        .dashboard-widget.status {
            grid-column: span 8;
        }

        .dashboard-widget.revenue,
        .dashboard-widget.users {
            grid-column: span 2;
        }

        .dashboard-widget.activity {
            grid-column: span 6;
        }

        .dashboard-widget.operations {
            grid-column: span 4;
        }

        .dashboard-widget.alerts {
            grid-column: span 2;
        }

        @media (max-width: 800px) {
            .dashboard-widget {
                grid-column: 1 / -1 !important;
            }
        }
    `;

    document.head.appendChild(style);

    return section;
}


// -----------------------------------------------------------------------------
// Section 18: Initialization
// -----------------------------------------------------------------------------

function initializeCSSGridStudy() {
    if (!document.body || !document.head) {
        throw new Error("This script must run in a browser document.");
    }

    const container = buildStudyPage();

    const dashboardSection = createDashboardExample();
    container.appendChild(dashboardSection);

    runSizingCalculations();
    demonstrateValidation();
    reportLiveMeasurements();
    observeResponsiveGrid();

    console.log(
        "CSS Grid study initialized successfully."
    );

    console.log(
        "Inspect the generated elements with browser developer tools "
        + "to observe their computed grid properties."
    );
}


if (typeof document !== "undefined") {
    if (document.readyState === "loading") {
        document.addEventListener(
            "DOMContentLoaded",
            initializeCSSGridStudy,
            { once: true }
        );
    } else {
        initializeCSSGridStudy();
    }
}
