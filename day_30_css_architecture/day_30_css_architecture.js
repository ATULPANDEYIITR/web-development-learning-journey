/**
 * CSS Architecture Laboratory
 *
 * This Node.js-compatible program models maintainable CSS architecture
 * through four related but distinct mechanisms:
 *
 *   BEM             -> naming and component ownership
 *   Utilities       -> small reusable behavioral/layout rules
 *   Components      -> styles owned by a UI component
 *   CSS variables   -> centralized values and runtime theme switching
 *
 * The implementation intentionally uses JavaScript-specific strengths:
 * classes, Maps, Sets, event-driven state changes, validation, serialization,
 * and an event-based merge-like style policy simulation for CSS architecture.
 *
 * Run:
 *   node css-architecture.js
 */

"use strict";

const BEM_PATTERN =
  /^[a-z][a-z0-9]*(?:-[a-z0-9]+)*(?:(?:__[a-z][a-z0-9]*(?:-[a-z0-9]+)*)|(?:--[a-z][a-z0-9]*(?:-[a-z0-9]+)*))?$/;

const UTILITY_RULES = new Map([
  ["u-flex", { display: "flex" }],
  ["u-grid", { display: "grid" }],
  ["u-gap-sm", { gap: "var(--space-sm)" }],
  ["u-gap-md", { gap: "var(--space-md)" }],
  ["u-gap-lg", { gap: "var(--space-lg)" }],
  ["u-p-sm", { padding: "var(--space-sm)" }],
  ["u-p-md", { padding: "var(--space-md)" }],
  ["u-p-lg", { padding: "var(--space-lg)" }],
  ["u-text-center", { "text-align": "center" }],
  ["u-w-full", { width: "100%" }],
  ["u-hidden", { display: "none" }],
]);

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

function bemBlock(name) {
  if (!/^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$/.test(name)) {
    throw new Error(`Invalid BEM block: ${name}`);
  }
  return name;
}

function bemElement(block, element) {
  bemBlock(block);

  if (!/^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$/.test(element)) {
    throw new Error(`Invalid BEM element: ${element}`);
  }

  return `${block}__${element}`;
}

function bemModifier(block, modifier) {
  bemBlock(block);

  if (!/^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$/.test(modifier)) {
    throw new Error(`Invalid BEM modifier: ${modifier}`);
  }

  return `${block}--${modifier}`;
}

function parseBemClass(className) {
  const match = className.match(
    /^([a-z][a-z0-9]*(?:-[a-z0-9]+)*)(?:__([a-z][a-z0-9]*(?:-[a-z0-9]+)*)|--([a-z][a-z0-9]*(?:-[a-z0-9]+)*))?$/
  );

  if (!match) {
    return null;
  }

  return {
    block: match[1],
    element: match[2] ?? null,
    modifier: match[3] ?? null,
  };
}

function isBemClass(className) {
  return parseBemClass(className) !== null;
}

function utility(name) {
  if (!UTILITY_RULES.has(name)) {
    throw new Error(`Unknown utility class: ${name}`);
  }

  return name;
}

function specificity(selector) {
  /*
   * This calculator covers the selector vocabulary used by the example.
   * It is intentionally conservative rather than pretending to be a complete
   * CSS parser.
   */
  const ids = (selector.match(/#[\w-]+/g) || []).length;
  const classes = [
    ...(selector.match(/\.[\w-]+/g) || []),
    ...(selector.match(/\[[^\]]+\]/g) || []),
    ...(selector.match(/:(?!:)[\w-]+(?:\([^)]*\))?/g) || []),
  ].length;

  const withoutSpecialSelectors = selector
    .replace(/#[\w-]+/g, " ")
    .replace(/\.[\w-]+/g, " ")
    .replace(/\[[^\]]+\]/g, " ")
    .replace(/::?[\w-]+(?:\([^)]*\))?/g, " ")
    .replace(/[>+~*]/g, " ");

  const elements = (
    withoutSpecialSelectors.match(
      /\b(html|body|main|header|footer|nav|section|article|aside|div|span|button|input|form|label|a|ul|ol|li|p|h1|h2|h3|img)\b/gi
    ) || []
  ).length;

  return [ids, classes, elements];
}

function deepSelector(selector) {
  return (selector.trim().match(/\s+/g) || []).length >= 2;
}

class CssRule {
  constructor(selector, declarations, layer, source = "") {
    this.selector = selector;
    this.declarations = Object.freeze({ ...declarations });
    this.layer = layer;
    this.source = source;
  }

  render() {
    const body = Object.entries(this.declarations)
      .map(([property, value]) => `  ${property}: ${value};`)
      .join("\n");

    return `${this.selector} {\n${body}\n}`;
  }
}

class Component {
  constructor(name, block) {
    this.name = name;
    this.block = bemBlock(block);
    this.elements = new Set();
    this.modifiers = new Set();
  }

  addElement(name) {
    this.elements.add(name);
    return this;
  }

  addModifier(name) {
    this.modifiers.add(name);
    return this;
  }

  classes() {
    const result = new Set([this.block]);

    for (const element of this.elements) {
      result.add(bemElement(this.block, element));
    }

    for (const modifier of this.modifiers) {
      result.add(bemModifier(this.block, modifier));
    }

    return result;
  }
}

class DesignTokenRegistry {
  constructor() {
    this.groups = new Map();
  }

  define(group, name, value) {
    if (!/^[a-z][a-z0-9-]*$/.test(name)) {
      throw new Error(`Invalid token name: ${name}`);
    }

    if (!this.groups.has(group)) {
      this.groups.set(group, new Map());
    }

    this.groups.get(group).set(name, value);
  }

  variable(group, name) {
    if (!this.groups.has(group) || !this.groups.get(group).has(name)) {
      throw new Error(`Token does not exist: ${group}.${name}`);
    }

    return `var(--${group}-${name})`;
  }

  render() {
    const lines = [":root {"];

    for (const [group, tokens] of this.groups) {
      for (const [name, value] of tokens) {
        lines.push(`  --${group}-${name}: ${value};`);
      }
    }

    lines.push("}");
    return lines.join("\n");
  }

  snapshot() {
    const result = {};

    for (const [group, tokens] of this.groups) {
      result[group] = Object.fromEntries(tokens);
    }

    return result;
  }
}

class ThemeManager {
  constructor(tokens) {
    this.tokens = tokens;
    this.themes = new Map();
    this.activeTheme = null;
  }

  register(name, overrides) {
    this.themes.set(name, new Map(Object.entries(overrides)));
  }

  activate(name) {
    if (!this.themes.has(name)) {
      throw new Error(`Unknown theme: ${name}`);
    }

    this.activeTheme = name;
  }

  resolvedVariables() {
    const base = {};

    for (const [group, values] of this.tokens.groups) {
      for (const [name, value] of values) {
        base[`--${group}-${name}`] = value;
      }
    }

    if (this.activeTheme) {
      for (const [variable, value] of this.themes.get(this.activeTheme)) {
        base[variable] = value;
      }
    }

    return base;
  }

  renderSelector() {
    if (!this.activeTheme) {
      return ":root";
    }

    return `[data-theme="${this.activeTheme}"]`;
  }

  renderOverrides() {
    if (!this.activeTheme) {
      return "";
    }

    const lines = [`${this.renderSelector()} {`];

    for (const [variable, value] of this.themes.get(this.activeTheme)) {
      lines.push(`  ${variable}: ${value};`);
    }

    lines.push("}");
    return lines.join("\n");
  }
}

class CssArchitecture {
  constructor() {
    this.rules = [];
    this.layers = [
      "reset",
      "tokens",
      "base",
      "components",
      "utilities",
      "overrides",
    ];
  }

  add(rule) {
    this.rules.push(rule);
  }

  validateOrder() {
    let previous = -1;

    for (const rule of this.rules) {
      const current = this.layers.indexOf(rule.layer);

      if (current === -1) {
        throw new Error(`Unknown CSS layer: ${rule.layer}`);
      }

      if (current < previous) {
        throw new Error(
          `CSS layer order violation near selector ${rule.selector}`
        );
      }

      previous = current;
    }
  }

  render() {
    this.validateOrder();

    let previousLayer = null;
    const output = [];

    for (const rule of this.rules) {
      if (rule.layer !== previousLayer) {
        if (output.length > 0) {
          output.push("");
        }

        output.push(`/* ${rule.layer} */`);
        previousLayer = rule.layer;
      }

      output.push(rule.render());
    }

    return output.join("\n");
  }
}

class ArchitectureLinter {
  constructor({ knownUtilities, knownComponents }) {
    this.knownUtilities = knownUtilities;
    this.knownComponents = knownComponents;
  }

  lint(rules) {
    const violations = [];

    for (const rule of rules) {
      const classes = [...rule.selector.matchAll(/\.([\w-]+)/g)].map(
        (match) => match[1]
      );

      if (rule.layer === "utilities") {
        if (
          classes.length !== 1 ||
          !this.knownUtilities.has(classes[0])
        ) {
          violations.push({
            category: "utility-boundary",
            selector: rule.selector,
            message:
              "A utility rule should normally represent one recognized utility class.",
          });
        }

        if (JSON.stringify(specificity(rule.selector)) !== "[0,1,0]") {
          violations.push({
            category: "utility-specificity",
            selector: rule.selector,
            message:
              "Utilities should normally remain at single-class specificity.",
          });
        }
      }

      if (rule.layer === "components") {
        if (classes.some((className) => className.startsWith("u-"))) {
          violations.push({
            category: "component-boundary",
            selector: rule.selector,
            message:
              "Utilities should be composed in markup instead of being owned by component selectors.",
          });
        }

        if (deepSelector(rule.selector)) {
          violations.push({
            category: "component-coupling",
            selector: rule.selector,
            message:
              "Deep descendant selectors make surrounding markup part of the component contract.",
          });
        }
      }

      if (specificity(rule.selector)[0] > 0) {
        violations.push({
          category: "specificity",
          selector: rule.selector,
          message:
            "ID selectors create unnecessary specificity pressure.",
        });
      }

      for (const className of classes) {
        if (
          ["button", "card", "title", "header", "active"].includes(className)
        ) {
          violations.push({
            category: "global-naming",
            selector: rule.selector,
            message:
              "Generic class names create unclear ownership between components.",
          });
        }
      }
    }

    return violations;
  }
}

class WorkflowEventBus {
  constructor() {
    this.listeners = new Map();
  }

  on(eventName, listener) {
    if (!this.listeners.has(eventName)) {
      this.listeners.set(eventName, []);
    }

    this.listeners.get(eventName).push(listener);
  }

  emit(eventName, payload) {
    for (const listener of this.listeners.get(eventName) || []) {
      listener(payload);
    }
  }
}

class ThemePreviewController {
  constructor(themeManager) {
    this.themeManager = themeManager;
    this.events = new WorkflowEventBus();
  }

  switchTheme(themeName) {
    this.themeManager.activate(themeName);

    this.events.emit("themeChanged", {
      theme: themeName,
      selector: this.themeManager.renderSelector(),
      variables: this.themeManager.resolvedVariables(),
    });
  }
}

function createTokens() {
  const tokens = new DesignTokenRegistry();

  tokens.define("color", "surface", "#10141c");
  tokens.define("color", "surface-raised", "#171d27");
  tokens.define("color", "text", "#f5f7fa");
  tokens.define("color", "text-muted", "#aab4c3");
  tokens.define("color", "accent", "#7dd3fc");
  tokens.define("color", "success", "#86efac");
  tokens.define("color", "danger", "#fca5a5");
  tokens.define("color", "border", "#303b4d");

  tokens.define("space", "sm", "0.5rem");
  tokens.define("space", "md", "1rem");
  tokens.define("space", "lg", "1.5rem");

  tokens.define("radius", "sm", "0.375rem");
  tokens.define("radius", "md", "0.625rem");
  tokens.define("radius", "lg", "1rem");

  tokens.define("font", "body", "1rem");
  tokens.define("font", "small", "0.875rem");
  tokens.define("font", "title", "1.5rem");
  tokens.define("font", "weight-bold", "700");

  return tokens;
}

function createArchitecture() {
  const tokens = createTokens();
  const architecture = new CssArchitecture();

  architecture.add(
    new CssRule(
      "*",
      { "box-sizing": "border-box" },
      "reset",
      "global box model normalization"
    )
  );

  architecture.add(
    new CssRule(
      ":root",
      {
        "--color-surface": "#10141c",
        "--color-surface-raised": "#171d27",
        "--color-text": "#f5f7fa",
        "--color-text-muted": "#aab4c3",
        "--color-accent": "#7dd3fc",
        "--color-border": "#303b4d",
        "--space-sm": "0.5rem",
        "--space-md": "1rem",
        "--space-lg": "1.5rem",
        "--radius-md": "0.625rem",
        "--font-weight-bold": "700",
      },
      "tokens",
      "generated token layer"
    )
  );

  architecture.add(
    new CssRule(
      "body",
      {
        margin: "0",
        background: "var(--color-surface)",
        color: "var(--color-text)",
        "font-family": "system-ui, sans-serif",
      },
      "base",
      "document defaults"
    )
  );

  architecture.add(
    new CssRule(
      ".review-card",
      {
        background: "var(--color-surface-raised)",
        border: "1px solid var(--color-border)",
        "border-radius": "var(--radius-md)",
      },
      "components",
      "review-card component"
    )
  );

  architecture.add(
    new CssRule(
      ".review-card__header",
      {
        display: "flex",
        "align-items": "center",
        "justify-content": "space-between",
        gap: "var(--space-md)",
      },
      "components",
      "review-card component"
    )
  );

  architecture.add(
    new CssRule(
      ".review-card__title",
      {
        margin: "0",
        "font-size": "1.125rem",
        "font-weight": "var(--font-weight-bold)",
      },
      "components",
      "review-card component"
    )
  );

  architecture.add(
    new CssRule(
      ".review-card--approved",
      {
        "border-color": "var(--color-success, #86efac)",
      },
      "components",
      "review-card state modifier"
    )
  );

  architecture.add(
    new CssRule(
      ".status-badge",
      {
        display: "inline-flex",
        "align-items": "center",
        padding: "0.25rem 0.5rem",
        "border-radius": "999px",
        "font-size": "var(--font-small, 0.875rem)",
      },
      "components",
      "status-badge component"
    )
  );

  architecture.add(
    new CssRule(
      ".status-badge--success",
      {
        background:
          "color-mix(in srgb, var(--color-success, #86efac) 18%, transparent)",
        color: "var(--color-success, #86efac)",
      },
      "components",
      "status-badge state modifier"
    )
  );

  for (const [className, declarations] of UTILITY_RULES) {
    architecture.add(
      new CssRule(
        `.${className}`,
        declarations,
        "utilities",
        "utility layer"
      )
    );
  }

  return { tokens, architecture };
}

function demonstrateBEM() {
  console.log("\nBEM component contract");

  const block = bemBlock("review-card");
  const elements = [
    bemElement(block, "header"),
    bemElement(block, "title"),
    bemElement(block, "actions"),
  ];
  const modifiers = [
    bemModifier(block, "approved"),
    bemModifier(block, "changes-requested"),
  ];

  console.log(`Block: .${block}`);
  console.log("Elements:");
  for (const element of elements) {
    console.log(`  .${element}`);
  }

  console.log("Modifiers:");
  for (const modifier of modifiers) {
    console.log(`  .${modifier}`);
  }

  console.log("\nParser:");
  for (const className of [
    "review-card",
    "review-card__title",
    "review-card--approved",
    "review_card",
  ]) {
    console.log(`  ${className}: ${JSON.stringify(parseBemClass(className))}`);
  }
}

function demonstrateUtilities() {
  console.log("\nUtility composition");

  const markupClasses = [
    "review-card",
    "review-card--approved",
    utility("u-p-md"),
    utility("u-mt-md"),
    utility("u-flex"),
  ];

  console.log(
    "A component can compose independent layout concerns without changing its BEM identity:"
  );
  console.log(`  class="${markupClasses.join(" ")}"`);

  console.log("\nDefined utility behavior:");
  for (const className of ["u-p-md", "u-flex", "u-gap-md"]) {
    console.log(`  .${className} -> ${JSON.stringify(UTILITY_RULES.get(className))}`);
  }
}

function demonstrateComponentBoundaries() {
  console.log("\nComponent ownership");

  const reviewCard = new Component("Review Card", "review-card")
    .addElement("header")
    .addElement("title")
    .addElement("meta")
    .addElement("actions")
    .addModifier("approved")
    .addModifier("changes-requested");

  console.log(`Component: ${reviewCard.name}`);

  for (const className of reviewCard.classes()) {
    console.log(`  .${className}`);
  }

  console.log(
    "\nThe block owns visual structure. Elements identify internal roles. "
    + "Modifiers represent component state rather than creating unrelated global selectors."
  );
}

function demonstrateVariablesAndThemes() {
  console.log("\nCSS custom properties and runtime themes");

  const tokens = createTokens();

  console.log(tokens.render());

  const themeManager = new ThemeManager(tokens);

  themeManager.register("dark", {
    "--color-surface": "#10141c",
    "--color-surface-raised": "#171d27",
    "--color-text": "#f5f7fa",
  });

  themeManager.register("light", {
    "--color-surface": "#f7f8fa",
    "--color-surface-raised": "#ffffff",
    "--color-text": "#172033",
  });

  const controller = new ThemePreviewController(themeManager);

  controller.events.on("themeChanged", (event) => {
    console.log(`\nTheme event received: ${event.theme}`);
    console.log(`Selector: ${event.selector}`);
    console.log(
      `Surface: ${event.variables["--color-surface"]}`
    );
  });

  controller.switchTheme("dark");
  controller.switchTheme("light");

  console.log("\nCurrent override CSS:");
  console.log(themeManager.renderOverrides());
}

function demonstrateSpecificity() {
  console.log("\nSpecificity pressure");

  const selectors = [
    ".review-card",
    ".review-card__title",
    ".review-card .review-card__title",
    "article.review-card",
    "#dashboard .review-card",
  ];

  for (const selector of selectors) {
    console.log(`  ${selector.padEnd(42)} ${specificity(selector).join(",")}`);
  }

  console.log(
    "\nThe architecture favors selectors that can be reasoned about locally. "
    + "An ID selector can win the cascade against a component class and encourage "
    + "future selectors to become even more specific."
  );
}

function demonstrateLinting() {
  console.log("\nArchitecture linting");

  const { architecture } = createArchitecture();

  const components = [
    new Component("Review Card", "review-card"),
    new Component("Status Badge", "status-badge"),
  ];

  const linter = new ArchitectureLinter({
    knownUtilities: new Set(UTILITY_RULES.keys()),
    knownComponents: components,
  });

  const validViolations = linter.lint(architecture.rules);

  console.log(
    validViolations.length === 0
      ? "  Valid architecture produced no violations."
      : validViolations
  );

  const badRules = [
    new CssRule(
      ".card .title",
      { color: "red" },
      "components",
      "legacy selector"
    ),
    new CssRule(
      "#dashboard .review-card",
      { padding: "20px" },
      "components",
      "specificity escalation"
    ),
    new CssRule(
      ".review-card .u-p-md",
      { padding: "var(--space-md)" },
      "components",
      "utility incorrectly owned by component selector"
    ),
  ];

  console.log("\nDeliberately problematic selectors:");

  for (const violation of linter.lint(badRules)) {
    console.log(
      `  ${violation.category} [${violation.selector}]: ${violation.message}`
    );
  }
}

function demonstrateGeneratedStylesheet() {
  console.log("\nGenerated CSS architecture");

  const { architecture } = createArchitecture();
  console.log(architecture.render());
}

function calculateMetrics(rules) {
  const declarationCount = rules.reduce(
    (total, rule) => total + Object.keys(rule.declarations).length,
    0
  );

  const highSpecificityRules = rules.filter(([rule]) => {
    const [ids, classes] = specificity(rule.selector);
    return ids > 0 || classes >= 3;
  }).length;

  const deepSelectors = rules.filter((rule) =>
    deepSelector(rule.selector)
  ).length;

  return {
    rules: rules.length,
    declarations: declarationCount,
    averageDeclarationsPerRule:
      rules.length === 0 ? 0 : declarationCount / rules.length,
    highSpecificityRules,
    deepSelectors,
  };
}

function demonstrateMetrics() {
  console.log("\nMaintainability diagnostics");

  const { architecture } = createArchitecture();
  const metrics = calculateMetrics(architecture.rules);

  for (const [key, value] of Object.entries(metrics)) {
    const formatted =
      typeof value === "number" && !Number.isInteger(value)
        ? value.toFixed(2)
        : value;

    console.log(`  ${key.padEnd(32)} ${formatted}`);
  }

  console.log(
    "\nMetrics reveal structural pressure but do not replace human review. "
    + "Selector ownership, meaningful naming, and appropriate abstraction boundaries "
    + "remain architectural decisions."
  );
}

function demonstrateFailureModes() {
  console.log("\nArchitecture failure modes");

  const cases = [
    {
      name: "Generic class ownership",
      issue:
        ".card and .title can be claimed by unrelated components, producing accidental coupling.",
    },
    {
      name: "Descendant dependency",
      issue:
        ".repository .sidebar .card .title requires a particular DOM hierarchy to remain styled correctly.",
    },
    {
      name: "Utility overreach",
      issue:
        "A utility such as .review-card-approved-with-padding mixes component identity with reusable behavior.",
    },
    {
      name: "Literal-value duplication",
      issue:
        "Repeating the same color or spacing value prevents a single design-token change from propagating safely.",
    },
    {
      name: "Specificity escalation",
      issue:
        "Fixing a conflict with an ID selector makes subsequent overrides harder to express predictably.",
    },
    {
      name: "Token misuse",
      issue:
        "A custom property with unclear naming can hide semantic intent even though the cascade remains valid.",
    },
  ];

  for (const item of cases) {
    console.log(`  ${item.name}: ${item.issue}`);
  }
}

function demonstrateEdgeCases() {
  console.log("\nEdge cases");

  const operations = [
    ["Valid BEM block", () => bemBlock("repository-header")],
    ["Invalid BEM block", () => bemBlock("Repository_Header")],
    ["Valid utility", () => utility("u-gap-md")],
    ["Invalid utility", () => utility("u-random-padding")],
    ["Unknown theme", () => {
      const manager = new ThemeManager(createTokens());
      manager.activate("nonexistent");
    }],
  ];

  for (const [name, operation] of operations) {
    try {
      console.log(`  ${name}: accepted -> ${operation() ?? "success"}`);
    } catch (error) {
      console.log(`  ${name}: rejected -> ${error.message}`);
    }
  }
}

function runTests() {
  console.log("\nExecutable checks");

  assert(isBemClass("review-card"), "Block should be valid.");
  assert(
    isBemClass("review-card__title"),
    "Element should be valid."
  );
  assert(
    isBemClass("review-card--approved"),
    "Modifier should be valid."
  );
  assert(
    !isBemClass("review_card"),
    "Underscore naming should be rejected."
  );

  assert(
    JSON.stringify(specificity(".review-card")) === "[0,1,0]",
    "Component class specificity is incorrect."
  );

  assert(
    JSON.stringify(specificity("#app .review-card")) === "[1,1,0]",
    "ID plus class specificity is incorrect."
  );

  const tokens = createTokens();
  assert(
    tokens.variable("space", "md") === "var(--space-md)",
    "Token variable resolution failed."
  );

  const { architecture } = createArchitecture();
  architecture.validateOrder();

  const linter = new ArchitectureLinter({
    knownUtilities: new Set(UTILITY_RULES.keys()),
    knownComponents: [
      new Component("Review Card", "review-card"),
    ],
  });

  assert(
    linter.lint(architecture.rules).length === 0,
    "Valid architecture should pass linting."
  );

  try {
    bemElement("review-card", "invalid.element");
    throw new Error("Invalid BEM element was incorrectly accepted.");
  } catch (error) {
    assert(
      error.message.includes("Invalid BEM element"),
      "Unexpected BEM validation error."
    );
  }

  console.log("  All JavaScript checks passed.");
}

function main() {
  console.log("=".repeat(72));
  console.log("CSS ARCHITECTURE LABORATORY");
  console.log("BEM | Utility Classes | Component Styles | CSS Variables");
  console.log("=".repeat(72));

  demonstrateBEM();
  demonstrateUtilities();
  demonstrateComponentBoundaries();
  demonstrateVariablesAndThemes();
  demonstrateSpecificity();
  demonstrateLinting();
  demonstrateGeneratedStylesheet();
  demonstrateMetrics();
  demonstrateFailureModes();
  demonstrateEdgeCases();
  runTests();

  console.log("\nCSS architecture model completed successfully.");
}

main();
