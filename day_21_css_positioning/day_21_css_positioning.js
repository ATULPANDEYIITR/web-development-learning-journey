/*
 * CSS Positioning — JavaScript Companion
 *
 * This file complements the Python study by modeling CSS positioning
 * concepts with JavaScript objects, calculations, DOM-style abstractions,
 * event-driven scrolling, and a browser-ready demonstration.
 *
 * It can run in Node.js. The browserDemo() function is also usable in a
 * browser console or page script.
 */

"use strict";

// ============================================================================
// 1. BASIC POSITIONING DATA
// ============================================================================

const Position = Object.freeze({
  STATIC: "static",
  RELATIVE: "relative",
  ABSOLUTE: "absolute",
  FIXED: "fixed",
  STICKY: "sticky",
});

function logSection(title) {
  console.log(`\n${"=".repeat(76)}\n${title}\n${"=".repeat(76)}`);
}

function createElementModel(name, options = {}) {
  return {
    name,
    position: options.position ?? Position.STATIC,
    zIndex: options.zIndex ?? "auto",
    top: options.top ?? null,
    right: options.right ?? null,
    bottom: options.bottom ?? null,
    left: options.left ?? null,
    width: options.width ?? 100,
    height: options.height ?? 40,
    normalX: options.normalX ?? 0,
    normalY: options.normalY ?? 0,
    establishesStackingContext: options.establishesStackingContext ?? false,
    parent: null,
    children: [],
  };
}

function appendChild(parent, child) {
  child.parent = parent;
  parent.children.push(child);
}


// ============================================================================
// 2. STATIC
// ============================================================================

logSection("1. STATIC POSITIONING");

const staticElement = createElementModel("paragraph", {
  position: Position.STATIC,
  top: 100,
  left: 100,
  normalX: 20,
  normalY: 30,
});

console.log("Position:", staticElement.position);
console.log("Normal-flow coordinates:", {
  x: staticElement.normalX,
  y: staticElement.normalY,
});
console.log(
  "top/left do not reposition a static element because the static position " +
  "does not respond to inset offsets."
);


// ============================================================================
// 3. RELATIVE
// ============================================================================

logSection("2. RELATIVE POSITIONING");

function resolveRelativePosition(element) {
  let x = element.normalX;
  let y = element.normalY;

  // In a simple physical-coordinate model, left takes precedence over right.
  if (element.left !== null) {
    x += element.left;
  } else if (element.right !== null) {
    x -= element.right;
  }

  if (element.top !== null) {
    y += element.top;
  } else if (element.bottom !== null) {
    y -= element.bottom;
  }

  return { x, y };
}

const relativeElement = createElementModel("icon", {
  position: Position.RELATIVE,
  normalX: 100,
  normalY: 100,
  left: 15,
  top: -5,
});

console.log("Normal position:", {
  x: relativeElement.normalX,
  y: relativeElement.normalY,
});
console.log("Visual position:", resolveRelativePosition(relativeElement));
console.log(
  "The original layout space remains reserved by the relatively positioned element."
);


// ============================================================================
// 4. ABSOLUTE POSITIONING
// ============================================================================

logSection("3. ABSOLUTE POSITIONING");

const card = createElementModel("card", {
  position: Position.RELATIVE,
  normalX: 100,
  normalY: 80,
  width: 400,
  height: 240,
});

const badge = createElementModel("badge", {
  position: Position.ABSOLUTE,
  top: 12,
  right: 15,
  width: 70,
  height: 28,
});

appendChild(card, badge);

function findAbsoluteContainingBlock(element) {
  let ancestor = element.parent;

  while (ancestor) {
    if (ancestor.position !== Position.STATIC) {
      return ancestor;
    }

    if (ancestor.establishesStackingContext) {
      return ancestor;
    }

    ancestor = ancestor.parent;
  }

  return null;
}

function resolveAbsolutePosition(element) {
  const containingBlock = findAbsoluteContainingBlock(element);

  if (!containingBlock) {
    return {
      x: element.left ?? 0,
      y: element.top ?? 0,
      reference: "initial containing block / simplified viewport model",
    };
  }

  let x = 0;
  let y = 0;

  if (element.left !== null) {
    x = element.left;
  } else if (element.right !== null) {
    x = containingBlock.width - element.width - element.right;
  }

  if (element.top !== null) {
    y = element.top;
  } else if (element.bottom !== null) {
    y = containingBlock.height - element.height - element.bottom;
  }

  return {
    x: containingBlock.normalX + x,
    y: containingBlock.normalY + y,
    reference: containingBlock.name,
  };
}

console.log("Absolute containing block:", findAbsoluteContainingBlock(badge)?.name);
console.log("Badge coordinates:", resolveAbsolutePosition(badge));


// ============================================================================
// 5. ABSOLUTE CENTERING
// ============================================================================

logSection("4. ABSOLUTE CENTERING");

function centerAbsolute(parentWidth, parentHeight, childWidth, childHeight) {
  return {
    x: (parentWidth - childWidth) / 2,
    y: (parentHeight - childHeight) / 2,
  };
}

console.log(
  "Centered modal:",
  centerAbsolute(1200, 800, 500, 300)
);


// ============================================================================
// 6. FIXED
// ============================================================================

logSection("5. FIXED POSITIONING");

function resolveFixedPosition(element, viewport) {
  let x;
  let y;

  if (element.left !== null) {
    x = element.left;
  } else if (element.right !== null) {
    x = viewport.width - element.width - element.right;
  } else {
    x = element.normalX;
  }

  if (element.top !== null) {
    y = element.top;
  } else if (element.bottom !== null) {
    y = viewport.height - element.height - element.bottom;
  } else {
    y = element.normalY;
  }

  return { x, y };
}

const floatingButton = createElementModel("help-button", {
  position: Position.FIXED,
  right: 20,
  bottom: 20,
  width: 140,
  height: 50,
});

const viewportBeforeScroll = {
  width: 1440,
  height: 900,
  scrollY: 0,
};

const viewportAfterScroll = {
  width: 1440,
  height: 900,
  scrollY: 2500,
};

console.log(
  "Before scroll:",
  resolveFixedPosition(floatingButton, viewportBeforeScroll)
);
console.log(
  "After scroll:",
  resolveFixedPosition(floatingButton, viewportAfterScroll)
);

console.log(
  "In the ordinary fixed-position model, document scrolling does not change " +
  "the element's viewport-relative coordinates."
);


// ============================================================================
// 7. STICKY
// ============================================================================

logSection("6. STICKY POSITIONING");

function resolveStickyY({
  normalY,
  top,
  scrollY,
  containingEnd,
  elementHeight,
}) {
  if (top === null) {
    return normalY - scrollY;
  }

  const naturalViewportY = normalY - scrollY;
  const stickyViewportY = Math.max(naturalViewportY, top);
  const maximumViewportY = containingEnd - scrollY - elementHeight;

  return Math.min(stickyViewportY, maximumViewportY);
}

const stickyHeader = createElementModel("section-header", {
  position: Position.STICKY,
  top: 0,
  normalY: 400,
  width: 600,
  height: 50,
});

for (const scrollY of [0, 200, 399, 400, 600, 1000, 1450]) {
  console.log(
    `scrollY=${String(scrollY).padStart(4)} -> viewportY=${resolveStickyY({
      normalY: stickyHeader.normalY,
      top: stickyHeader.top,
      scrollY,
      containingEnd: 1500,
      elementHeight: stickyHeader.height,
    })}`
  );
}


// ============================================================================
// 8. z-INDEX AND STACKING
// ============================================================================

logSection("7. z-INDEX");

function approximateZIndex(element) {
  return element.zIndex === "auto" ? 0 : Number(element.zIndex);
}

const layers = [
  createElementModel("content", {
    position: Position.STATIC,
    zIndex: "auto",
  }),
  createElementModel("dropdown", {
    position: Position.ABSOLUTE,
    zIndex: 100,
  }),
  createElementModel("modal", {
    position: Position.FIXED,
    zIndex: 1000,
  }),
  createElementModel("toast", {
    position: Position.FIXED,
    zIndex: 1100,
  }),
];

layers
  .slice()
  .sort((a, b) => approximateZIndex(a) - approximateZIndex(b))
  .forEach((layer, index) => {
    console.log(
      `${index + 1}. ${layer.name}: z-index=${layer.zIndex}`
    );
  });


// ============================================================================
// 9. STACKING CONTEXTS
// ============================================================================

logSection("8. STACKING CONTEXTS");

function createsCommonStackingContext(element, css = {}) {
  if (element === css.root) {
    return true;
  }

  if (
    element.position === Position.RELATIVE &&
    element.zIndex !== "auto"
  ) {
    return true;
  }

  if (element.position === Position.ABSOLUTE && element.zIndex !== "auto") {
    return true;
  }

  if (element.position === Position.FIXED) {
    return true;
  }

  if (element.position === Position.STICKY) {
    return true;
  }

  if (css.opacity !== undefined && Number(css.opacity) < 1) {
    return true;
  }

  if (css.transform && css.transform !== "none") {
    return true;
  }

  if (css.filter && css.filter !== "none") {
    return true;
  }

  if (css.isolation === "isolate") {
    return true;
  }

  if (css.mixBlendMode && css.mixBlendMode !== "normal") {
    return true;
  }

  return false;
}

const stackingExamples = [
  {
    name: "root",
    element: createElementModel("root"),
    css: {},
  },
  {
    name: "relative + z-index",
    element: createElementModel("panel", {
      position: Position.RELATIVE,
      zIndex: 2,
    }),
    css: {},
  },
  {
    name: "opacity",
    element: createElementModel("transparent"),
    css: { opacity: 0.8 },
  },
  {
    name: "transform",
    element: createElementModel("transformed"),
    css: { transform: "translateZ(0)" },
  },
  {
    name: "isolation",
    element: createElementModel("isolated"),
    css: { isolation: "isolate" },
  },
];

for (const example of stackingExamples) {
  console.log(
    `${example.name}:`,
    createsCommonStackingContext(example.element, {
      ...example.css,
      root: example.name === "root" ? example.element : null,
    })
  );
}


// ============================================================================
// 10. WHY HUGE z-INDEX VALUES DO NOT SOLVE EVERYTHING
// ============================================================================

logSection("9. NESTED STACKING CONTEXTS");

const applicationRoot = createElementModel("application-root", {
  position: Position.STATIC,
});

const leftContext = createElementModel("left-context", {
  position: Position.RELATIVE,
  zIndex: 1,
  establishesStackingContext: true,
});

const rightContext = createElementModel("right-context", {
  position: Position.RELATIVE,
  zIndex: 2,
  establishesStackingContext: true,
});

const leftModal = createElementModel("left-modal", {
  position: Position.ABSOLUTE,
  zIndex: 999999,
});

const rightPopup = createElementModel("right-popup", {
  position: Position.ABSOLUTE,
  zIndex: 1,
});

appendChild(applicationRoot, leftContext);
appendChild(applicationRoot, rightContext);
appendChild(leftContext, leftModal);
appendChild(rightContext, rightPopup);

console.log("Left context z-index:", leftContext.zIndex);
console.log("Left modal z-index:", leftModal.zIndex);
console.log("Right context z-index:", rightContext.zIndex);
console.log("Right popup z-index:", rightPopup.zIndex);

console.log(
  "The child z-index is interpreted within its stacking context; it is not " +
  "a globally comparable number across the entire page."
);


// ============================================================================
// 11. STACKING CONTEXT TREE
// ============================================================================

logSection("10. STACKING-CONTEXT TREE");

function printElementTree(element, depth = 0) {
  const marker = element.establishesStackingContext ? " [SC]" : "";

  console.log(
    `${"  ".repeat(depth)}${element.name} ` +
    `position=${element.position} ` +
    `z-index=${element.zIndex}${marker}`
  );

  for (const child of element.children) {
    printElementTree(child, depth + 1);
  }
}

printElementTree(applicationRoot);


// ============================================================================
// 12. EVENT-DRIVEN SCROLL MODEL
// ============================================================================

logSection("11. EVENT-DRIVEN STICKY BEHAVIOR");

class ScrollContainer {
  constructor(height, contentHeight) {
    this.height = height;
    this.contentHeight = contentHeight;
    this.scrollY = 0;
    this.listeners = new Set();
  }

  addScrollListener(listener) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  scrollTo(y) {
    const maximum = Math.max(0, this.contentHeight - this.height);

    // Validation prevents impossible scroll positions.
    this.scrollY = Math.max(0, Math.min(y, maximum));

    for (const listener of this.listeners) {
      listener(this.scrollY);
    }
  }
}

const article = new ScrollContainer(800, 3000);

article.addScrollListener((scrollY) => {
  const y = resolveStickyY({
    normalY: 500,
    top: 20,
    scrollY,
    containingEnd: 2600,
    elementHeight: 60,
  });

  console.log(`scroll=${scrollY}, sticky header viewportY=${y}`);
});

article.scrollTo(0);
article.scrollTo(300);
article.scrollTo(700);
article.scrollTo(1600);
article.scrollTo(5000);


// ============================================================================
// 13. CSS GENERATION
// ============================================================================

logSection("12. GENERATING PRACTICAL CSS");

function createCssRule(selector, properties) {
  const lines = [`${selector} {`];

  for (const [property, value] of Object.entries(properties)) {
    lines.push(`  ${property}: ${value};`);
  }

  lines.push("}");
  return lines.join("\n");
}

console.log(
  createCssRule(".product-card", {
    position: "relative",
    width: "320px",
    minHeight: "220px",
  })
);

console.log(
  createCssRule(".product-card__badge", {
    position: "absolute",
    top: "12px",
    right: "12px",
    zIndex: "10",
  })
);


// ============================================================================
// 14. BROWSER DEMONSTRATION
// ============================================================================

logSection("13. BROWSER-SIDE DEMONSTRATION");

function browserDemo() {
  if (typeof document === "undefined") {
    console.log(
      "browserDemo() requires a browser DOM. The rest of this file can run in Node.js."
    );
    return;
  }

  const style = document.createElement("style");

  style.textContent = `
    .positioning-demo {
      position: relative;
      min-height: 900px;
      padding: 40px;
      font-family: system-ui, sans-serif;
    }

    .positioning-demo__card {
      position: relative;
      width: min(600px, 100%);
      min-height: 280px;
      margin: 80px auto;
      border: 2px solid #222;
      padding: 30px;
    }

    .positioning-demo__badge {
      position: absolute;
      top: 15px;
      right: 15px;
      padding: 8px 12px;
      background: black;
      color: white;
    }

    .positioning-demo__sticky {
      position: sticky;
      top: 0;
      z-index: 10;
      padding: 15px;
      background: white;
      border-bottom: 1px solid #ccc;
    }

    .positioning-demo__fixed {
      position: fixed;
      right: 20px;
      bottom: 20px;
      z-index: 1000;
      padding: 12px 16px;
    }
  `;

  document.head.appendChild(style);

  const wrapper = document.createElement("main");
  wrapper.className = "positioning-demo";

  const sticky = document.createElement("div");
  sticky.className = "positioning-demo__sticky";
  sticky.textContent = "Sticky navigation";

  const cardElement = document.createElement("section");
  cardElement.className = "positioning-demo__card";
  cardElement.textContent =
    "This card establishes the containing block for its absolute badge.";

  const badgeElement = document.createElement("span");
  badgeElement.className = "positioning-demo__badge";
  badgeElement.textContent = "BADGE";

  const fixedElement = document.createElement("button");
  fixedElement.className = "positioning-demo__fixed";
  fixedElement.textContent = "Fixed";

  cardElement.appendChild(badgeElement);
  wrapper.appendChild(sticky);
  wrapper.appendChild(cardElement);
  wrapper.appendChild(fixedElement);
  document.body.appendChild(wrapper);

  return {
    wrapper,
    sticky,
    cardElement,
    badgeElement,
    fixedElement,
  };
}


// ============================================================================
// 15. DOM GEOMETRY
// ============================================================================

logSection("14. DOM GEOMETRY");

function inspectBrowserGeometry(element) {
  if (!element || typeof element.getBoundingClientRect !== "function") {
    throw new TypeError(
      "inspectBrowserGeometry expects a browser DOM element."
    );
  }

  const rectangle = element.getBoundingClientRect();

  return {
    left: rectangle.left,
    top: rectangle.top,
    right: rectangle.right,
    bottom: rectangle.bottom,
    width: rectangle.width,
    height: rectangle.height,
  };
}

console.log(
  "inspectBrowserGeometry(element) reads the visual viewport-relative rectangle."
);
console.log(
  "getBoundingClientRect() is useful when diagnosing actual browser geometry."
);


// ============================================================================
// 16. ERROR HANDLING
// ============================================================================

logSection("15. VALIDATION AND ERROR HANDLING");

function validatePositioningModel(element) {
  const validPositions = new Set(Object.values(Position));

  if (!validPositions.has(element.position)) {
    throw new RangeError(`Unsupported position: ${element.position}`);
  }

  for (const property of ["top", "right", "bottom", "left"]) {
    const value = element[property];

    if (value !== null && (!Number.isFinite(value))) {
      throw new TypeError(`${property} must be null or a finite number.`);
    }
  }

  if (element.width < 0 || element.height < 0) {
    throw new RangeError("Width and height cannot be negative.");
  }

  return true;
}

const validElement = createElementModel("valid", {
  position: Position.ABSOLUTE,
  top: 10,
  left: 20,
  width: 100,
  height: 40,
});

console.log("Valid model:", validatePositioningModel(validElement));

try {
  validatePositioningModel({
    ...validElement,
    position: "floating",
  });
} catch (error) {
  console.log("Expected validation error:", error.message);
}


// ============================================================================
// 17. PERFORMANCE CONSIDERATIONS
// ============================================================================

logSection("16. PERFORMANCE CONSIDERATIONS");

function compareAnimationProperties() {
  return [
    {
      property: "top/left",
      category: "layout-related",
      guidance:
        "Can require layout and subsequent paint work depending on the situation.",
    },
    {
      property: "transform",
      category: "visual transformation",
      guidance:
        "Often suitable for animation because it can avoid ordinary layout changes.",
    },
    {
      property: "z-index",
      category: "painting/layering",
      guidance:
        "Changes stacking order; frequent changes should be evaluated in real rendering scenarios.",
    },
  ];
}

for (const item of compareAnimationProperties()) {
  console.log(
    `${item.property}: ${item.category} -> ${item.guidance}`
  );
}


// ============================================================================
// 18. POSITIONING DECISION FUNCTION
// ============================================================================

logSection("17. POSITIONING DECISION GUIDE");

function choosePositioning({
  normalFlow = true,
  localOffset = false,
  anchoredToParent = false,
  anchoredToViewport = false,
  sticksDuringScroll = false,
}) {
  if (sticksDuringScroll) {
    return Position.STICKY;
  }

  if (anchoredToViewport) {
    return Position.FIXED;
  }

  if (anchoredToParent) {
    return Position.ABSOLUTE;
  }

  if (localOffset) {
    return Position.RELATIVE;
  }

  if (normalFlow) {
    return Position.STATIC;
  }

  return Position.STATIC;
}

const useCases = [
  {
    name: "ordinary paragraph",
    normalFlow: true,
  },
  {
    name: "badge on card",
    normalFlow: false,
    anchoredToParent: true,
  },
  {
    name: "floating support button",
    normalFlow: false,
    anchoredToViewport: true,
  },
  {
    name: "section heading",
    normalFlow: true,
    sticksDuringScroll: true,
  },
  {
    name: "small visual adjustment",
    normalFlow: true,
    localOffset: true,
  },
];

for (const useCase of useCases) {
  console.log(
    `${useCase.name}: ${choosePositioning(useCase)}`
  );
}


// ============================================================================
// 19. SELF-TESTS
// ============================================================================

logSection("18. SELF-TESTS");

function assert(condition, message) {
  if (!condition) {
    throw new Error(`Assertion failed: ${message}`);
  }
}

assert(Position.STATIC === "static", "static value");
assert(Position.RELATIVE === "relative", "relative value");
assert(Position.ABSOLUTE === "absolute", "absolute value");
assert(Position.FIXED === "fixed", "fixed value");
assert(Position.STICKY === "sticky", "sticky value");

const relativeTest = createElementModel("test", {
  position: Position.RELATIVE,
  normalX: 100,
  normalY: 200,
  left: 20,
  top: 10,
});

const relativeResult = resolveRelativePosition(relativeTest);

assert(relativeResult.x === 120, "relative x");
assert(relativeResult.y === 210, "relative y");

const parentTest = createElementModel("parent", {
  position: Position.RELATIVE,
});

const childTest = createElementModel("child", {
  position: Position.ABSOLUTE,
});

appendChild(parentTest, childTest);

assert(
  findAbsoluteContainingBlock(childTest) === parentTest,
  "absolute containing block"
);

const fixedResult = resolveFixedPosition(
  createElementModel("fixed-test", {
    position: Position.FIXED,
    right: 10,
    bottom: 20,
    width: 100,
    height: 50,
  }),
  { width: 800, height: 600 }
);

assert(fixedResult.x === 690, "fixed x");
assert(fixedResult.y === 530, "fixed y");

console.log("All JavaScript tests passed.");


// ============================================================================
// 20. EXPORTS FOR NODE.JS
// ============================================================================

if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    Position,
    createElementModel,
    appendChild,
    resolveRelativePosition,
    findAbsoluteContainingBlock,
    resolveAbsolutePosition,
    centerAbsolute,
    resolveFixedPosition,
    resolveStickyY,
    createsCommonStackingContext,
    choosePositioning,
    validatePositioningModel,
    ScrollContainer,
    browserDemo,
  };
}
