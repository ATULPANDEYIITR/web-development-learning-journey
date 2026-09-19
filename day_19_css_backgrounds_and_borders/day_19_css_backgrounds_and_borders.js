/*
 * CSS Backgrounds and Borders
 * ===========================
 *
 * Executable JavaScript companion covering:
 * - background colors
 * - background images
 * - background positioning and sizing
 * - multiple backgrounds
 * - gradients
 * - borders
 * - border radius
 * - outlines
 * - shadows
 * - clipping
 * - CSS custom properties
 * - validation
 * - component generation
 * - browser-oriented demonstrations
 *
 * The file uses standard JavaScript only.
 * Run with:
 *   node css-backgrounds-borders.js
 */

// ============================================================================
// 1. FUNDAMENTAL REPRESENTATION
// ============================================================================

console.log("=".repeat(78));
console.log("CSS BACKGROUNDS AND BORDERS");
console.log("=".repeat(78));

const concepts = {
  background:
    "Painting behind an element's content and padding. It may contain colors, images, gradients, or multiple layers.",
  border:
    "A visible edge around an element. It has width, style, and color.",
  borderRadius:
    "Rounds the corners of the element's box.",
  boxShadow:
    "Adds one or more visual shadows around or inside a box.",
  outline:
    "A visual line outside the border that does not normally consume layout space.",
  clipping:
    "Controls which painted or descendant content remains visible.",
  gradient:
    "A generated CSS image based on color transitions."
};

for (const [name, description] of Object.entries(concepts)) {
  console.log(`\n${name}:`);
  console.log(`  ${description}`);
}


// ============================================================================
// 2. CSS RULE BUILDER
// ============================================================================

class CSSRule {
  constructor(selector, declarations = {}) {
    if (!selector || typeof selector !== "string") {
      throw new TypeError("A CSS selector must be a non-empty string.");
    }

    this.selector = selector;
    this.declarations = { ...declarations };
  }

  set(property, value) {
    if (!property || typeof property !== "string") {
      throw new TypeError("CSS property must be a non-empty string.");
    }

    this.declarations[property] = String(value);
    return this;
  }

  render() {
    const lines = Object.entries(this.declarations)
      .map(([property, value]) => `  ${property}: ${value};`)
      .join("\n");

    return `${this.selector} {\n${lines}\n}`;
  }
}

function renderStylesheet(rules) {
  return rules.map((rule) => rule.render()).join("\n\n");
}

const cardRule = new CSSRule(".card", {
  "background-color": "#111827",
  color: "#f8fafc",
  border: "1px solid #334155",
  "border-radius": "16px",
  padding: "24px"
});

console.log("\n--- Basic CSS rule ---");
console.log(cardRule.render());


// ============================================================================
// 3. BACKGROUND COLOR
// ============================================================================

const backgroundColors = [
  "background-color: navy;",
  "background-color: #0f172a;",
  "background-color: rgb(15 23 42);",
  "background-color: rgb(15 23 42 / 0.85);",
  "background-color: hsl(222 47% 11%);",
  "background-color: transparent;"
];

console.log("\n--- Background color forms ---");
for (const declaration of backgroundColors) {
  console.log(declaration);
}


// ============================================================================
// 4. BACKGROUND IMAGE
// ============================================================================

const heroRule = new CSSRule(".hero", {
  "background-image": "url('hero.jpg')",
  "background-repeat": "no-repeat",
  "background-position": "center",
  "background-size": "cover"
});

console.log("\n--- Background image ---");
console.log(heroRule.render());


// ============================================================================
// 5. COVER VS CONTAIN
// ============================================================================

function backgroundSizeDimensions(
  containerWidth,
  containerHeight,
  imageWidth,
  imageHeight
) {
  const values = [
    containerWidth,
    containerHeight,
    imageWidth,
    imageHeight
  ];

  if (!values.every((value) => Number.isFinite(value) && value > 0)) {
    throw new RangeError("All dimensions must be positive finite numbers.");
  }

  const coverScale = Math.max(
    containerWidth / imageWidth,
    containerHeight / imageHeight
  );

  const containScale = Math.min(
    containerWidth / imageWidth,
    containerHeight / imageHeight
  );

  return {
    cover: {
      width: imageWidth * coverScale,
      height: imageHeight * coverScale
    },
    contain: {
      width: imageWidth * containScale,
      height: imageHeight * containScale
    }
  };
}

const sizeResult = backgroundSizeDimensions(1200, 500, 1600, 900);

console.log("\n--- cover vs contain ---");
console.log("cover  :", sizeResult.cover);
console.log("contain:", sizeResult.contain);


// ============================================================================
// 6. POSITION AND REPEAT
// ============================================================================

const positions = [
  "left top",
  "center center",
  "right bottom",
  "50% 25%",
  "20px 40px"
];

console.log("\n--- Background positions ---");
positions.forEach((position) => {
  console.log(`background-position: ${position};`);
});

const repeatModes = [
  "repeat",
  "repeat-x",
  "repeat-y",
  "no-repeat",
  "space",
  "round"
];

console.log("\n--- Background repetition ---");
repeatModes.forEach((mode) => {
  console.log(`background-repeat: ${mode};`);
});


// ============================================================================
// 7. MULTIPLE BACKGROUNDS
// ============================================================================

const multipleBackgroundRule = new CSSRule(".dashboard", {
  "background-image":
    "linear-gradient(rgb(15 23 42 / 0.88), rgb(15 23 42 / 0.88)), url('dashboard.jpg')",
  "background-position": "center, center",
  "background-size": "cover, cover",
  "background-repeat": "no-repeat, no-repeat"
});

console.log("\n--- Multiple backgrounds ---");
console.log(multipleBackgroundRule.render());

console.log(
  "\nThe first comma-separated background layer is painted above later layers."
);


// ============================================================================
// 8. GRADIENT GENERATORS
// ============================================================================

function linearGradient(angle, stops) {
  if (!Array.isArray(stops) || stops.length < 2) {
    throw new Error("A gradient requires at least two color stops.");
  }

  return `linear-gradient(${angle}, ${stops.join(", ")})`;
}

function radialGradient(shape, position, stops) {
  if (!Array.isArray(stops) || stops.length < 2) {
    throw new Error("A gradient requires at least two color stops.");
  }

  return `radial-gradient(${shape} at ${position}, ${stops.join(", ")})`;
}

function conicGradient(angle, stops) {
  if (!Array.isArray(stops) || stops.length < 2) {
    throw new Error("A gradient requires at least two color stops.");
  }

  return `conic-gradient(from ${angle}, ${stops.join(", ")})`;
}

const gradients = [
  linearGradient("90deg", ["#0ea5e9", "#8b5cf6"]),
  linearGradient("135deg", [
    "#0ea5e9 0%",
    "#8b5cf6 55%",
    "#ec4899 100%"
  ]),
  radialGradient("circle", "center", ["#38bdf8", "#0f172a"]),
  conicGradient("45deg", [
    "#ef4444",
    "#f59e0b",
    "#22c55e",
    "#3b82f6",
    "#ef4444"
  ])
];

console.log("\n--- Generated gradients ---");
gradients.forEach((gradient) => console.log(gradient));


// ============================================================================
// 9. COLOR INTERPOLATION
// ============================================================================

function interpolateChannel(start, end, progress) {
  if (!Number.isFinite(progress) || progress < 0 || progress > 1) {
    throw new RangeError("Progress must be between 0 and 1.");
  }

  return Math.round(start + (end - start) * progress);
}

function interpolateRGB(start, end, progress) {
  if (
    !Array.isArray(start) ||
    !Array.isArray(end) ||
    start.length !== 3 ||
    end.length !== 3
  ) {
    throw new TypeError("RGB values must contain three channels.");
  }

  return start.map((channel, index) =>
    interpolateChannel(channel, end[index], progress)
  );
}

console.log("\n--- Gradient interpolation ---");

for (const progress of [0, 0.25, 0.5, 0.75, 1]) {
  console.log(
    progress,
    interpolateRGB([14, 165, 233], [139, 92, 246], progress)
  );
}


// ============================================================================
// 10. BORDERS
// ============================================================================

const borderStyles = [
  "none",
  "solid",
  "dashed",
  "dotted",
  "double",
  "groove",
  "ridge",
  "inset",
  "outset"
];

console.log("\n--- Border styles ---");
borderStyles.forEach((style) => {
  console.log(`border: 2px ${style} #64748b;`);
});

const individualBorders = new CSSRule(".panel", {
  "border-width": "2px",
  "border-style": "solid",
  "border-color": "#475569",
  "border-top-color": "#38bdf8",
  "border-right-color": "#8b5cf6",
  "border-bottom-color": "#ec4899",
  "border-left-color": "#22c55e"
});

console.log("\n--- Individual border sides ---");
console.log(individualBorders.render());


// ============================================================================
// 11. BORDER RADIUS
// ============================================================================

const radiusExamples = {
  small: "border-radius: 6px;",
  medium: "border-radius: 12px;",
  large: "border-radius: 24px;",
  pill: "border-radius: 9999px;",
  circle: "border-radius: 50%;",
  corners: "border-radius: 4px 12px 20px 28px;",
  elliptical: "border-radius: 30px / 15px;"
};

console.log("\n--- Border-radius forms ---");
for (const [name, declaration] of Object.entries(radiusExamples)) {
  console.log(`${name.padEnd(12)}: ${declaration}`);
}


// ============================================================================
// 12. SHADOW MODEL
// ============================================================================

class BoxShadow {
  constructor({
    offsetX = 0,
    offsetY = 0,
    blur = 0,
    spread = 0,
    color = "rgb(0 0 0 / 0.2)",
    inset = false
  } = {}) {
    if (blur < 0) {
      throw new RangeError("Blur radius cannot be negative.");
    }

    this.offsetX = offsetX;
    this.offsetY = offsetY;
    this.blur = blur;
    this.spread = spread;
    this.color = color;
    this.inset = inset;
  }

  toCSS() {
    const prefix = this.inset ? "inset " : "";

    return (
      `box-shadow: ${prefix}${this.offsetX}px ${this.offsetY}px ` +
      `${this.blur}px ${this.spread}px ${this.color};`
    );
  }
}

const shadow = new BoxShadow({
  offsetX: 0,
  offsetY: 12,
  blur: 32,
  color: "rgb(0 0 0 / 0.24)"
});

console.log("\n--- Structured shadow ---");
console.log(shadow.toCSS());

const shadowExamples = [
  "box-shadow: 0 4px 12px rgb(0 0 0 / 0.25);",
  "box-shadow: 0 8px 24px 4px rgb(0 0 0 / 0.20);",
  "box-shadow: inset 0 2px 8px rgb(0 0 0 / 0.30);",
  "box-shadow: 0 2px 6px rgb(0 0 0 / 0.18), 0 12px 30px rgb(0 0 0 / 0.14);"
];

console.log("\n--- Shadow examples ---");
shadowExamples.forEach((example) => console.log(example));


// ============================================================================
// 13. OUTLINE AND FOCUS
// ============================================================================

const focusRule = new CSSRule(".keyboard-focus:focus-visible", {
  outline: "3px solid #38bdf8",
  "outline-offset": "4px"
});

console.log("\n--- Focus outline ---");
console.log(focusRule.render());


// ============================================================================
// 14. BACKGROUND CLIP AND ORIGIN
// ============================================================================

const clippingRule = new CSSRule(".clipped-card", {
  "background-color": "#0f172a",
  "background-image":
    "linear-gradient(135deg, #06b6d4, #7c3aed)",
  "background-clip": "padding-box",
  "background-origin": "border-box",
  border: "3px solid transparent",
  "border-radius": "18px"
});

console.log("\n--- Background clipping ---");
console.log(clippingRule.render());


// ============================================================================
// 15. VALIDATION
// ============================================================================

const HEX_COLOR_PATTERN =
  /^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$/;

function isHexColor(value) {
  return typeof value === "string" && HEX_COLOR_PATTERN.test(value);
}

function isCSSRadius(value) {
  return (
    typeof value === "string" &&
    /^(?:0|[0-9]+(?:\.[0-9]+)?)(?:px|rem|em|%)$/.test(value)
  );
}

function isSafeImageURL(value) {
  if (typeof value !== "string") {
    return false;
  }

  const normalized = value.trim().toLowerCase();

  return (
    /^(https?:\/\/|\/|\.\/|\.\.\/)/.test(normalized) &&
    !normalized.includes("javascript:")
  );
}

console.log("\n--- Validation ---");

for (const color of ["#fff", "#112233", "#112233cc", "#xyz", "red"]) {
  console.log(color.padEnd(12), isHexColor(color));
}

for (const radius of ["16px", "1.5rem", "50%", "-2px", "large"]) {
  console.log(radius.padEnd(12), isCSSRadius(radius));
}

for (const url of [
  "images/hero.jpg",
  "https://example.com/image.jpg",
  "javascript:alert(1)"
]) {
  console.log(url.padEnd(34), isSafeImageURL(url));
}


// ============================================================================
// 16. CSS CUSTOM PROPERTIES
// ============================================================================

const designTokens = {
  "--surface": "#0f172a",
  "--surface-raised": "#1e293b",
  "--border": "#334155",
  "--accent": "#38bdf8",
  "--radius": "16px",
  "--shadow": "0 12px 32px rgb(0 0 0 / 0.22)"
};

const tokenRule = new CSSRule(":root", designTokens);

const tokenCard = new CSSRule(".token-card", {
  background: "var(--surface-raised)",
  border: "1px solid var(--border)",
  "border-radius": "var(--radius)",
  "box-shadow": "var(--shadow)"
});

console.log("\n--- CSS custom properties ---");
console.log(renderStylesheet([tokenRule, tokenCard]));


// ============================================================================
// 17. COMPONENT GENERATION
// ============================================================================

function createProductCardStyles() {
  return [
    new CSSRule(".product-card", {
      position: "relative",
      overflow: "hidden",
      background: "#0f172a",
      border: "1px solid #334155",
      "border-radius": "20px",
      "box-shadow": "0 16px 40px rgb(0 0 0 / 0.22)"
    }),

    new CSSRule(".product-card::before", {
      content: "''",
      position: "absolute",
      inset: "0",
      background:
        "linear-gradient(135deg, rgb(56 189 248 / 0.18), transparent 45%, rgb(139 92 246 / 0.18))",
      "pointer-events": "none"
    }),

    new CSSRule(".product-card__media", {
      height: "220px",
      background: "url('product.jpg') center / cover no-repeat",
      "border-radius": "20px 20px 0 0"
    }),

    new CSSRule(".product-card__content", {
      position: "relative",
      padding: "24px",
      background: "rgb(15 23 42 / 0.94)",
      "border-top": "1px solid rgb(148 163 184 / 0.18)"
    }),

    new CSSRule(".product-card__button", {
      background: "linear-gradient(135deg, #06b6d4, #7c3aed)",
      border: "1px solid rgb(255 255 255 / 0.14)",
      "border-radius": "9999px",
      "box-shadow": "0 8px 20px rgb(6 182 212 / 0.22)",
      color: "#fff",
      padding: "12px 20px"
    }),

    focusRule
  ];
}

const componentStyles = createProductCardStyles();

console.log("\n--- Complete component CSS ---");
console.log(renderStylesheet(componentStyles));


// ============================================================================
// 18. BROWSER-SIDE DOM DEMONSTRATION
// ============================================================================

function createBrowserDemo() {
  if (typeof document === "undefined") {
    return {
      supported: false,
      reason: "This function requires a browser DOM."
    };
  }

  const style = document.createElement("style");

  style.textContent = `
    :root {
      color-scheme: dark;
      font-family: system-ui, sans-serif;
    }

    body {
      min-height: 100vh;
      margin: 0;
      display: grid;
      place-items: center;
      padding: 32px;
      box-sizing: border-box;
      background:
        radial-gradient(circle at 20% 20%, rgb(56 189 248 / 0.16), transparent 30%),
        linear-gradient(135deg, #020617, #111827);
      color: #f8fafc;
    }

    .browser-demo-card {
      width: min(680px, 100%);
      overflow: hidden;
      border: 1px solid #334155;
      border-radius: 24px;
      background:
        linear-gradient(rgb(15 23 42 / 0.30), rgb(15 23 42 / 0.30)),
        url("hero.jpg") center / cover no-repeat;
      box-shadow:
        0 20px 60px rgb(0 0 0 / 0.28),
        inset 0 1px 0 rgb(255 255 255 / 0.08);
    }

    .browser-demo-card__content {
      padding: 40px;
      background: linear-gradient(
        rgb(2 6 23 / 0.50),
        rgb(2 6 23 / 0.92)
      );
    }

    .browser-demo-card button {
      border: 1px solid rgb(255 255 255 / 0.16);
      border-radius: 9999px;
      padding: 12px 20px;
      background: linear-gradient(135deg, #06b6d4, #7c3aed);
      color: white;
    }

    .browser-demo-card button:focus-visible {
      outline: 3px solid white;
      outline-offset: 4px;
    }
  `;

  document.head.appendChild(style);

  const article = document.createElement("article");
  article.className = "browser-demo-card";

  const content = document.createElement("div");
  content.className = "browser-demo-card__content";

  const heading = document.createElement("h1");
  heading.textContent = "Background and Border Demo";

  const paragraph = document.createElement("p");
  paragraph.textContent =
    "This browser-generated component combines a background image, gradient, border, radius, shadow, clipping, and focus styling.";

  const button = document.createElement("button");
  button.type = "button";
  button.textContent = "Inspect styling";

  content.append(heading, paragraph, button);
  article.appendChild(content);
  document.body.appendChild(article);

  return {
    supported: true,
    element: article
  };
}


// ============================================================================
// 19. RESPONSIVE BACKGROUND STRATEGY
// ============================================================================

function chooseBackgroundAsset(viewportWidth) {
  if (!Number.isFinite(viewportWidth) || viewportWidth <= 0) {
    throw new RangeError("Viewport width must be positive.");
  }

  if (viewportWidth <= 480) {
    return "hero-mobile.webp";
  }

  if (viewportWidth <= 1024) {
    return "hero-tablet.webp";
  }

  return "hero-desktop.webp";
}

console.log("\n--- Responsive asset strategy ---");

for (const width of [360, 768, 1440]) {
  console.log(
    `${width}px viewport -> ${chooseBackgroundAsset(width)}`
  );
}


// ============================================================================
// 20. CSS CLAMP CONCEPT
// ============================================================================

function clamp(value, minimum, maximum) {
  if (minimum > maximum) {
    throw new RangeError("Minimum cannot exceed maximum.");
  }

  return Math.max(minimum, Math.min(value, maximum));
}

console.log("\n--- clamp concept ---");
console.log("clamp(24, 16, 32):", clamp(24, 16, 32));
console.log("clamp(8, 16, 32): ", clamp(8, 16, 32));
console.log("clamp(48, 16, 32):", clamp(48, 16, 32));


// ============================================================================
// 21. ACCESSIBILITY AND PERFORMANCE AUDIT
// ============================================================================

class VisualDesignAudit {
  constructor(options = {}) {
    this.hasFocusIndicator = Boolean(options.hasFocusIndicator);
    this.textOverImageHasOverlay = Boolean(
      options.textOverImageHasOverlay
    );
    this.decorativeImageIsNonessential = Boolean(
      options.decorativeImageIsNonessential
    );
    this.reasonableShadowCount = Boolean(options.reasonableShadowCount);
    this.avoidsUnnecessaryFixedBackgrounds = Boolean(
      options.avoidsUnnecessaryFixedBackgrounds
    );
  }

  issues() {
    const issues = [];

    if (!this.hasFocusIndicator) {
      issues.push("Provide a visible keyboard focus indicator.");
    }

    if (!this.textOverImageHasOverlay) {
      issues.push("Check text contrast over imagery.");
    }

    if (!this.decorativeImageIsNonessential) {
      issues.push(
        "Do not place essential information only in CSS backgrounds."
      );
    }

    if (!this.reasonableShadowCount) {
      issues.push("Reduce excessive shadow layers.");
    }

    if (!this.avoidsUnnecessaryFixedBackgrounds) {
      issues.push(
        "Review background-attachment: fixed on mobile and low-powered devices."
      );
    }

    return issues;
  }
}

const audit = new VisualDesignAudit({
  hasFocusIndicator: true,
  textOverImageHasOverlay: true,
  decorativeImageIsNonessential: true,
  reasonableShadowCount: true,
  avoidsUnnecessaryFixedBackgrounds: true
});

console.log("\n--- Visual design audit ---");

const auditIssues = audit.issues();

if (auditIssues.length === 0) {
  console.log("No issues detected by the basic audit.");
} else {
  auditIssues.forEach((issue) => console.log(`- ${issue}`));
}


// ============================================================================
// 22. PERFORMANCE MODEL
// ============================================================================

function estimateVisualComplexity({
  backgroundLayers,
  shadowLayers,
  gradientLayers,
  largeBlurCount
}) {
  const components = [
    backgroundLayers,
    shadowLayers,
    gradientLayers,
    largeBlurCount
  ];

  if (!components.every((value) => Number.isInteger(value) && value >= 0)) {
    throw new TypeError("Complexity values must be non-negative integers.");
  }

  return (
    backgroundLayers +
    shadowLayers * 2 +
    gradientLayers +
    largeBlurCount * 3
  );
}

console.log("\n--- Conceptual visual complexity ---");

console.log(
  estimateVisualComplexity({
    backgroundLayers: 2,
    shadowLayers: 2,
    gradientLayers: 2,
    largeBlurCount: 1
  })
);


// ============================================================================
// 23. ERROR HANDLING EXAMPLES
// ============================================================================

function safeGradient(stops) {
  try {
    return linearGradient("90deg", stops);
  } catch (error) {
    return {
      error: error.message
    };
  }
}

console.log("\n--- Error handling ---");
console.log(safeGradient(["#000", "#fff"]));
console.log(safeGradient(["#000"]));


// ============================================================================
// 24. CSS CONTAINMENT AND CLIPPING DISTINCTION
// ============================================================================

const clippingComparison = {
  "background-clip: border-box":
    "Background is painted through the border box.",
  "background-clip: padding-box":
    "Background is painted through the padding box.",
  "background-clip: content-box":
    "Background is painted through the content box.",
  "overflow: hidden":
    "Descendant and overflowing content is clipped to the element's padding box or applicable overflow clipping area.",
  "border-radius":
    "Rounds the box geometry and participates in clipping behavior."
};

console.log("\n--- Clipping distinctions ---");

for (const [property, meaning] of Object.entries(clippingComparison)) {
  console.log(`${property}: ${meaning}`);
}


// ============================================================================
// 25. COMMON MISTAKES
// ============================================================================

const commonMistakes = [
  {
    mistake: "Using background images for essential content.",
    correction:
      "Use semantic HTML for essential information and backgrounds for decoration."
  },
  {
    mistake: "Ignoring cropping caused by background-size: cover.",
    correction:
      "Test multiple aspect ratios and tune background-position."
  },
  {
    mistake: "Removing focus outlines.",
    correction:
      "Use :focus-visible with a strong, accessible alternative."
  },
  {
    mistake: "Shipping unnecessarily large background images.",
    correction:
      "Resize and compress assets and select suitable formats."
  },
  {
    mistake: "Using excessive shadow blur.",
    correction:
      "Use a small, consistent elevation system."
  },
  {
    mistake: "Confusing background clipping with child clipping.",
    correction:
      "Choose background-clip for background painting and overflow or clip-path when descendant content must be clipped."
  }
];

console.log("\n--- Common mistakes ---");

for (const item of commonMistakes) {
  console.log(`\nMistake:    ${item.mistake}`);
  console.log(`Correction: ${item.correction}`);
}


// ============================================================================
// 26. TESTS
// ============================================================================

function assert(condition, message) {
  if (!condition) {
    throw new Error(`Assertion failed: ${message}`);
  }
}

function runTests() {
  console.log("\n--- Running JavaScript tests ---");

  assert(isHexColor("#fff"), "short hex color should be valid");
  assert(isHexColor("#12345678"), "8-digit hex should be valid");
  assert(!isHexColor("#xyz"), "invalid hex should be rejected");

  assert(isCSSRadius("16px"), "pixel radius should be valid");
  assert(isCSSRadius("50%"), "percentage radius should be valid");
  assert(!isCSSRadius("-1px"), "negative radius should be rejected");

  const interpolation = interpolateRGB(
    [0, 0, 0],
    [100, 200, 50],
    0.5
  );

  assert(
    JSON.stringify(interpolation) === JSON.stringify([50, 100, 25]),
    "RGB interpolation should calculate the midpoint"
  );

  const dimensions = backgroundSizeDimensions(
    100,
    100,
    200,
    100
  );

  assert(dimensions.cover.width === 200, "cover width should be 200");
  assert(dimensions.cover.height === 100, "cover height should be 100");
  assert(dimensions.contain.width === 100, "contain width should be 100");
  assert(dimensions.contain.height === 50, "contain height should be 50");

  assert(
    isSafeImageURL("images/hero.jpg"),
    "relative image path should be accepted"
  );

  assert(
    !isSafeImageURL("javascript:alert(1)"),
    "javascript URL should be rejected"
  );

  const generatedCSS = renderStylesheet(createProductCardStyles());

  assert(
    generatedCSS.includes("border-radius"),
    "component should contain border radius"
  );

  assert(
    generatedCSS.includes("box-shadow"),
    "component should contain shadow"
  );

  console.log("All JavaScript tests passed.");
}

runTests();


// ============================================================================
// 27. FINAL REFERENCE
// ============================================================================

const reference = {
  "background-color": "Sets the background color.",
  "background-image": "Adds one or more background images.",
  "background-position": "Controls image positioning.",
  "background-size": "Controls rendered image dimensions.",
  "background-repeat": "Controls image repetition.",
  "background-attachment": "Controls background scrolling behavior.",
  "background-origin": "Defines the box used as the image positioning area.",
  "background-clip": "Defines the background painting area.",
  background: "Shorthand for background-related properties.",
  border: "Shorthand for border width, style, and color.",
  "border-radius": "Rounds corners.",
  "border-image": "Uses an image to construct the border.",
  outline: "Paints an outline outside the border.",
  "box-shadow": "Creates box shadows.",
  "text-shadow": "Creates shadows behind text.",
  overflow: "Controls overflowing content and clipping."
};

console.log("\n--- Quick reference ---");

for (const [property, purpose] of Object.entries(reference)) {
  console.log(`${property.padEnd(22)} ${purpose}`);
}


// ============================================================================
// 28. BROWSER EXECUTION NOTE
// ============================================================================

if (typeof window !== "undefined") {
  console.log("\nBrowser environment detected.");
  console.log(
    "Call createBrowserDemo() to insert the interactive visual example."
  );
} else {
  console.log("\nNode.js environment detected.");
  console.log(
    "Browser-only DOM construction was skipped safely."
  );
}

console.log("\n" + "=".repeat(78));
console.log("Study file completed successfully.");
console.log("=".repeat(78));
