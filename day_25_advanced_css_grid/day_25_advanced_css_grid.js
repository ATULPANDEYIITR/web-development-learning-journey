/*
 * Advanced CSS Grid Study and Demonstration
 *
 * This file demonstrates CSS Grid concepts from JavaScript by:
 * - Creating real Grid containers in a browser.
 * - Applying minmax(), auto-fit, and auto-fill.
 * - Demonstrating explicit and implicit tracks.
 * - Measuring actual rendered dimensions.
 * - Building a responsive dashboard.
 * - Demonstrating dynamic Grid item placement.
 * - Showing the difference between layout calculation and DOM order.
 *
 * The file can be loaded with:
 *   <script src="advanced-grid.js"></script>
 *
 * It is intentionally self-contained and uses only browser APIs.
 */

"use strict";

/* -------------------------------------------------------------------------
 * 1. BASIC UTILITIES
 * ---------------------------------------------------------------------- */

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

function addStyleSheet(cssText) {
  const style = document.createElement("style");
  style.textContent = cssText;
  document.head.appendChild(style);
  return style;
}

function createSection(title, description) {
  const section = createElement("section", "grid-demo-section");

  const heading = createElement("h2", "", title);
  const paragraph = createElement("p", "", description);

  section.appendChild(heading);
  section.appendChild(paragraph);

  return section;
}

function ensureDemoRoot() {
  let root = document.querySelector("#css-grid-study");

  if (!root) {
    root = createElement("main", "");
    root.id = "css-grid-study";
    document.body.appendChild(root);
  }

  return root;
}


/* -------------------------------------------------------------------------
 * 2. GLOBAL STYLES
 * ---------------------------------------------------------------------- */

const GLOBAL_CSS = `
  * {
    box-sizing: border-box;
  }

  body {
    margin: 0;
    font-family:
      system-ui,
      -apple-system,
      BlinkMacSystemFont,
      "Segoe UI",
      sans-serif;
    line-height: 1.5;
    background: #101318;
    color: #f2f4f8;
  }

  #css-grid-study {
    width: min(1200px, calc(100% - 2rem));
    margin: 2rem auto;
  }

  .grid-demo-section {
    margin-block: 2rem;
    padding: 1rem;
    border: 1px solid #343b48;
    border-radius: 12px;
    background: #181d25;
  }

  .demo-grid {
    display: grid;
    gap: 1rem;
    margin-top: 1rem;
  }

  .demo-card {
    min-width: 0;
    padding: 1rem;
    border-radius: 10px;
    background: #252c37;
    border: 1px solid #414b5b;
  }

  .demo-card strong {
    display: block;
    margin-bottom: 0.35rem;
  }

  .demo-label {
    margin-top: 0.75rem;
    padding: 0.5rem;
    border-radius: 6px;
    background: #0d1117;
    font-family: monospace;
    white-space: pre-wrap;
  }

  .dashboard {
    display: grid;
    grid-template-columns:
      minmax(12rem, 16rem)
      minmax(0, 1fr)
      minmax(14rem, 22rem);
    grid-template-rows:
      auto
      minmax(15rem, 1fr)
      auto;
    grid-template-areas:
      "sidebar header header"
      "sidebar main aside"
      "sidebar footer footer";
    gap: 1rem;
  }

  .dashboard-header {
    grid-area: header;
  }

  .dashboard-sidebar {
    grid-area: sidebar;
  }

  .dashboard-main {
    grid-area: main;
  }

  .dashboard-aside {
    grid-area: aside;
  }

  .dashboard-footer {
    grid-area: footer;
  }

  .dashboard > * {
    min-width: 0;
    padding: 1rem;
    border: 1px solid #414b5b;
    border-radius: 10px;
    background: #252c37;
  }

  .measurement {
    margin-top: 0.75rem;
    padding: 0.75rem;
    background: #0d1117;
    border-radius: 6px;
    font-family: monospace;
  }

  @media (max-width: 900px) {
    .dashboard {
      grid-template-columns: 1fr;
      grid-template-areas:
        "header"
        "main"
        "aside"
        "sidebar"
        "footer";
    }
  }
`;

addStyleSheet(GLOBAL_CSS);


/* -------------------------------------------------------------------------
 * 3. minmax()
 * ---------------------------------------------------------------------- */

function demonstrateMinmax(root) {
  const section = createSection(
    "1. minmax()",
    "Each card has a minimum track size while the 1fr maximum distributes remaining space."
  );

  const grid = createElement("div", "demo-grid");
  grid.style.gridTemplateColumns = "repeat(3, minmax(180px, 1fr))";

  for (let index = 1; index <= 6; index += 1) {
    const card = createElement(
      "article",
      "demo-card",
      `Card ${index}`
    );

    grid.appendChild(card);
  }

  const label = createElement(
    "div",
    "demo-label",
    "grid-template-columns: repeat(3, minmax(180px, 1fr));"
  );

  section.appendChild(grid);
  section.appendChild(label);
  root.appendChild(section);
}


/* -------------------------------------------------------------------------
 * 4. auto-fit
 * ---------------------------------------------------------------------- */

function demonstrateAutoFit(root) {
  const section = createSection(
    "2. auto-fit",
    "auto-fit collapses empty repeated tracks, allowing existing items to expand into available space."
  );

  const grid = createElement("div", "demo-grid");

  grid.style.gridTemplateColumns =
    "repeat(auto-fit, minmax(180px, 1fr))";

  for (let index = 1; index <= 4; index += 1) {
    const card = createElement(
      "article",
      "demo-card",
      `auto-fit item ${index}`
    );

    grid.appendChild(card);
  }

  const label = createElement(
    "div",
    "demo-label",
    "repeat(auto-fit, minmax(180px, 1fr))"
  );

  section.appendChild(grid);
  section.appendChild(label);
  root.appendChild(section);
}


/* -------------------------------------------------------------------------
 * 5. auto-fill
 * ---------------------------------------------------------------------- */

function demonstrateAutoFill(root) {
  const section = createSection(
    "3. auto-fill",
    "auto-fill preserves the repeated track structure even when fewer items are present."
  );

  const grid = createElement("div", "demo-grid");

  grid.style.gridTemplateColumns =
    "repeat(auto-fill, minmax(180px, 1fr))";

  for (let index = 1; index <= 2; index += 1) {
    const card = createElement(
      "article",
      "demo-card",
      `auto-fill item ${index}`
    );

    grid.appendChild(card);
  }

  const label = createElement(
    "div",
    "demo-label",
    "repeat(auto-fill, minmax(180px, 1fr))"
  );

  section.appendChild(grid);
  section.appendChild(label);
  root.appendChild(section);
}


/* -------------------------------------------------------------------------
 * 6. EXPLICIT GRID
 * ---------------------------------------------------------------------- */

function demonstrateExplicitGrid(root) {
  const section = createSection(
    "4. Explicit tracks",
    "The number and sizing of columns and rows are declared directly."
  );

  const grid = createElement("div", "demo-grid");

  grid.style.gridTemplateColumns = "120px 1fr 160px";
  grid.style.gridTemplateRows = "80px 160px";

  for (let index = 1; index <= 6; index += 1) {
    const card = createElement(
      "article",
      "demo-card",
      `Explicit item ${index}`
    );

    grid.appendChild(card);
  }

  const label = createElement(
    "div",
    "demo-label",
    "grid-template-columns: 120px 1fr 160px;\n" +
    "grid-template-rows: 80px 160px;"
  );

  section.appendChild(grid);
  section.appendChild(label);
  root.appendChild(section);
}


/* -------------------------------------------------------------------------
 * 7. IMPLICIT GRID
 * ---------------------------------------------------------------------- */

function demonstrateImplicitGrid(root) {
  const section = createSection(
    "5. Implicit rows",
    "Only one row is explicitly declared. Additional rows are generated automatically."
  );

  const grid = createElement("div", "demo-grid");

  grid.style.gridTemplateColumns = "repeat(3, 1fr)";
  grid.style.gridTemplateRows = "100px";
  grid.style.gridAutoRows = "minmax(80px, auto)";

  for (let index = 1; index <= 8; index += 1) {
    const card = createElement(
      "article",
      "demo-card",
      `Implicit-grid item ${index}`
    );

    grid.appendChild(card);
  }

  const label = createElement(
    "div",
    "demo-label",
    "grid-template-columns: repeat(3, 1fr);\n" +
    "grid-template-rows: 100px;\n" +
    "grid-auto-rows: minmax(80px, auto);"
  );

  section.appendChild(grid);
  section.appendChild(label);
  root.appendChild(section);
}


/* -------------------------------------------------------------------------
 * 8. grid-auto-flow
 * ---------------------------------------------------------------------- */

function demonstrateAutoFlow(root) {
  const section = createSection(
    "6. grid-auto-flow",
    "The auto-placement algorithm can fill rows or columns automatically."
  );

  const grid = createElement("div", "demo-grid");

  grid.style.gridTemplateColumns = "repeat(3, 1fr)";
  grid.style.gridTemplateRows = "repeat(2, 100px)";
  grid.style.gridAutoFlow = "row";

  for (let index = 1; index <= 6; index += 1) {
    const card = createElement(
      "article",
      "demo-card",
      `Flow item ${index}`
    );

    grid.appendChild(card);
  }

  const label = createElement(
    "div",
    "demo-label",
    "grid-auto-flow: row;"
  );

  section.appendChild(grid);
  section.appendChild(label);
  root.appendChild(section);
}


/* -------------------------------------------------------------------------
 * 9. NAMED AREAS
 * ---------------------------------------------------------------------- */

function demonstrateNamedAreas(root) {
  const section = createSection(
    "7. Named grid areas",
    "Named areas express a complex layout in terms of semantic regions."
  );

  const dashboard = createElement("div", "dashboard");

  const header = createElement(
    "header",
    "dashboard-header",
    "Header"
  );

  const sidebar = createElement(
    "aside",
    "dashboard-sidebar",
    "Sidebar"
  );

  const main = createElement(
    "main",
    "dashboard-main",
    "Main content"
  );

  const aside = createElement(
    "aside",
    "dashboard-aside",
    "Secondary content"
  );

  const footer = createElement(
    "footer",
    "dashboard-footer",
    "Footer"
  );

  dashboard.append(header, sidebar, main, aside, footer);

  section.appendChild(dashboard);
  root.appendChild(section);
}


/* -------------------------------------------------------------------------
 * 10. LINE-BASED PLACEMENT
 * ---------------------------------------------------------------------- */

function demonstrateLinePlacement(root) {
  const section = createSection(
    "8. Line-based placement",
    "Grid items can span multiple columns or rows using numbered grid lines."
  );

  const grid = createElement("div", "demo-grid");

  grid.style.gridTemplateColumns = "repeat(4, 1fr)";
  grid.style.gridTemplateRows = "repeat(3, 90px)";

  const header = createElement(
    "article",
    "demo-card",
    "Header: columns 1 / -1"
  );

  header.style.gridColumn = "1 / -1";

  const sidebar = createElement(
    "article",
    "demo-card",
    "Sidebar: columns 1 / 2, rows 2 / 4"
  );

  sidebar.style.gridColumn = "1 / 2";
  sidebar.style.gridRow = "2 / 4";

  const content = createElement(
    "article",
    "demo-card",
    "Content: columns 2 / -1"
  );

  content.style.gridColumn = "2 / -1";
  content.style.gridRow = "2 / 4";

  grid.append(header, sidebar, content);

  const label = createElement(
    "div",
    "demo-label",
    "grid-column: 1 / -1;\n" +
    "grid-column: 1 / 2;\n" +
    "grid-row: 2 / 4;"
  );

  section.appendChild(grid);
  section.appendChild(label);
  root.appendChild(section);
}


/* -------------------------------------------------------------------------
 * 11. ACTUAL BROWSER MEASUREMENT
 * ---------------------------------------------------------------------- */

function demonstrateMeasurement(root) {
  const section = createSection(
    "9. Measuring rendered Grid tracks",
    "getBoundingClientRect() reads the dimensions produced by the browser's actual layout engine."
  );

  const grid = createElement("div", "demo-grid");

  grid.style.gridTemplateColumns =
    "repeat(auto-fit, minmax(180px, 1fr))";

  for (let index = 1; index <= 5; index += 1) {
    grid.appendChild(
      createElement(
        "article",
        "demo-card",
        `Measured card ${index}`
      )
    );
  }

  const measurement = createElement(
    "div",
    "measurement"
  );

  section.appendChild(grid);
  section.appendChild(measurement);
  root.appendChild(section);

  const updateMeasurement = () => {
    const gridRect = grid.getBoundingClientRect();
    const firstCard = grid.firstElementChild;

    if (!firstCard) {
      measurement.textContent = "No cards available.";
      return;
    }

    const cardRect = firstCard.getBoundingClientRect();

    measurement.textContent =
      `Grid width: ${gridRect.width.toFixed(2)}px\n` +
      `First card width: ${cardRect.width.toFixed(2)}px\n` +
      `Viewport width: ${window.innerWidth}px`;
  };

  updateMeasurement();

  window.addEventListener("resize", updateMeasurement);
}


/* -------------------------------------------------------------------------
 * 12. DYNAMIC GRID ITEMS
 * ---------------------------------------------------------------------- */

class ResponsiveCardGrid {
  constructor(container, minimumCardWidth = 220) {
    if (!(container instanceof HTMLElement)) {
      throw new TypeError("container must be an HTMLElement.");
    }

    if (!Number.isFinite(minimumCardWidth) || minimumCardWidth <= 0) {
      throw new RangeError(
        "minimumCardWidth must be a positive number."
      );
    }

    this.container = container;
    this.minimumCardWidth = minimumCardWidth;

    this.container.style.display = "grid";
    this.container.style.gridTemplateColumns =
      `repeat(auto-fit, minmax(${minimumCardWidth}px, 1fr))`;
    this.container.style.gap = "1rem";
  }

  addCard(title, description = "") {
    const card = createElement("article", "demo-card");

    const heading = createElement("strong", "", title);
    const body = createElement("span", "", description);

    card.append(heading, body);
    this.container.appendChild(card);

    return card;
  }

  removeLastCard() {
    const lastCard = this.container.lastElementChild;

    if (lastCard) {
      lastCard.remove();
      return true;
    }

    return false;
  }

  count() {
    return this.container.children.length;
  }
}

function demonstrateDynamicGrid(root) {
  const section = createSection(
    "10. Dynamic responsive Grid",
    "JavaScript changes the DOM while CSS Grid continues to manage the responsive layout."
  );

  const grid = createElement("div", "demo-grid");
  section.appendChild(grid);
  root.appendChild(section);

  const responsiveGrid = new ResponsiveCardGrid(grid, 190);

  responsiveGrid.addCard(
    "Data",
    "Grid remains responsive without JavaScript breakpoint calculations."
  );

  responsiveGrid.addCard(
    "Security",
    "The DOM remains ordered even though visual layout changes."
  );

  responsiveGrid.addCard(
    "Performance",
    "CSS handles the repeated track calculation."
  );

  responsiveGrid.addCard(
    "Accessibility",
    "Source order remains meaningful."
  );

  const label = createElement(
    "div",
    "demo-label",
    `Cards currently rendered: ${responsiveGrid.count()}`
  );

  section.appendChild(label);
}


/* -------------------------------------------------------------------------
 * 13. DENSE AUTO-PLACEMENT
 * ---------------------------------------------------------------------- */

function demonstrateDensePlacement(root) {
  const section = createSection(
    "11. Dense auto-placement",
    "dense allows later items to fill earlier holes, which can improve packing but must be evaluated against reading order."
  );

  const grid = createElement("div", "demo-grid");

  grid.style.gridTemplateColumns = "repeat(4, 1fr)";
  grid.style.gridAutoRows = "90px";
  grid.style.gridAutoFlow = "row dense";

  const large = createElement(
    "article",
    "demo-card",
    "Large item"
  );

  large.style.gridColumn = "span 2";
  large.style.gridRow = "span 2";

  grid.appendChild(large);

  for (let index = 1; index <= 6; index += 1) {
    grid.appendChild(
      createElement(
        "article",
        "demo-card",
        `Dense item ${index}`
      )
    );
  }

  section.appendChild(grid);
  root.appendChild(section);
}


/* -------------------------------------------------------------------------
 * 14. SUBGRID
 * ---------------------------------------------------------------------- */

function demonstrateSubgrid(root) {
  const section = createSection(
    "12. subgrid",
    "subgrid allows nested content to participate in the parent grid's track sizing."
  );

  const supported = CSS.supports(
    "grid-template-rows",
    "subgrid"
  );

  const message = createElement(
    "div",
    "demo-label",
    supported
      ? "This browser reports support for CSS subgrid."
      : "This browser does not report CSS subgrid support."
  );

  section.appendChild(message);
  root.appendChild(section);
}


/* -------------------------------------------------------------------------
 * 15. VALIDATION AND EDGE CASES
 * ---------------------------------------------------------------------- */

function validateGridConfiguration(configuration) {
  const errors = [];

  if (!configuration || typeof configuration !== "object") {
    return ["Configuration must be an object."];
  }

  if (
    !Number.isFinite(configuration.minimumWidth) ||
    configuration.minimumWidth <= 0
  ) {
    errors.push("minimumWidth must be positive.");
  }

  if (
    !Number.isFinite(configuration.gap) ||
    configuration.gap < 0
  ) {
    errors.push("gap must be zero or greater.");
  }

  if (
    configuration.mode !== "auto-fit" &&
    configuration.mode !== "auto-fill"
  ) {
    errors.push("mode must be auto-fit or auto-fill.");
  }

  return errors;
}

function demonstrateValidation(root) {
  const section = createSection(
    "13. Configuration validation",
    "Application code should validate values before constructing dynamic Grid declarations."
  );

  const examples = [
    {
      minimumWidth: 240,
      gap: 16,
      mode: "auto-fit",
    },
    {
      minimumWidth: 0,
      gap: 16,
      mode: "auto-fit",
    },
    {
      minimumWidth: 240,
      gap: -5,
      mode: "auto-fit",
    },
    {
      minimumWidth: 240,
      gap: 16,
      mode: "unknown",
    },
  ];

  const list = createElement("ul");

  examples.forEach((configuration) => {
    const errors = validateGridConfiguration(configuration);
    const result =
      errors.length === 0
        ? "valid"
        : `invalid: ${errors.join(" ")}`;

    const item = createElement(
      "li",
      "",
      `${JSON.stringify(configuration)} -> ${result}`
    );

    list.appendChild(item);
  });

  section.appendChild(list);
  root.appendChild(section);
}


/* -------------------------------------------------------------------------
 * 16. PERFORMANCE MODEL
 * ---------------------------------------------------------------------- */

function estimateColumns(
  containerWidth,
  minimumTrackWidth,
  gap
) {
  if (
    !Number.isFinite(containerWidth) ||
    !Number.isFinite(minimumTrackWidth) ||
    !Number.isFinite(gap)
  ) {
    throw new TypeError("All parameters must be finite numbers.");
  }

  if (containerWidth <= 0) {
    throw new RangeError("containerWidth must be positive.");
  }

  if (minimumTrackWidth <= 0) {
    throw new RangeError("minimumTrackWidth must be positive.");
  }

  if (gap < 0) {
    throw new RangeError("gap cannot be negative.");
  }

  return Math.max(
    1,
    Math.floor(
      (containerWidth + gap) /
      (minimumTrackWidth + gap)
    )
  );
}

function demonstratePerformanceModel(root) {
  const section = createSection(
    "14. Track-count estimation",
    "This JavaScript calculation is an approximation for reasoning about auto-fit; it is not a replacement for the browser's layout engine."
  );

  const widths = [320, 480, 768, 1024, 1440];

  const list = createElement("ul");

  widths.forEach((width) => {
    const columns = estimateColumns(width, 240, 16);

    list.appendChild(
      createElement(
        "li",
        "",
        `${width}px container -> approximately ${columns} minimum tracks`
      )
    );
  });

  section.appendChild(list);
  root.appendChild(section);
}


/* -------------------------------------------------------------------------
 * 17. COMPLETE DEMO INITIALIZATION
 * ---------------------------------------------------------------------- */

function initializeCSSGridStudy() {
  const root = ensureDemoRoot();

  root.innerHTML = "";

  const title = createElement(
    "h1",
    "",
    "Advanced CSS Grid Study"
  );

  const introduction = createElement(
    "p",
    "",
    "Interactive demonstrations of minmax(), auto-fit, auto-fill, implicit grids, responsive layouts, placement, named areas, dense packing, subgrid, validation, and measurement."
  );

  root.append(title, introduction);

  demonstrateMinmax(root);
  demonstrateAutoFit(root);
  demonstrateAutoFill(root);
  demonstrateExplicitGrid(root);
  demonstrateImplicitGrid(root);
  demonstrateAutoFlow(root);
  demonstrateNamedAreas(root);
  demonstrateLinePlacement(root);
  demonstrateMeasurement(root);
  demonstrateDynamicGrid(root);
  demonstrateDensePlacement(root);
  demonstrateSubgrid(root);
  demonstrateValidation(root);
  demonstratePerformanceModel(root);
}


/* -------------------------------------------------------------------------
 * 18. BROWSER-SAFE STARTUP
 * ---------------------------------------------------------------------- */

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


/*
 * Important implementation principle:
 *
 * JavaScript should generally not reproduce CSS Grid's layout algorithm.
 * CSS Grid is a browser layout system. JavaScript is useful for generating
 * or modifying content, reacting to application state, measuring results
 * when necessary, and validating application data.
 *
 * For responsive Grid layout, prefer CSS such as:
 *
 * repeat(auto-fit, minmax(16rem, 1fr))
 *
 * instead of calculating breakpoints in JavaScript.
 */
