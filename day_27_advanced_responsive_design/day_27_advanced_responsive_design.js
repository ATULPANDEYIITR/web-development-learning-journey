"use strict";

/*
 * Advanced Responsive Design
 *
 * JavaScript complements CSS by handling cases where application logic
 * genuinely needs to know the size of an element.
 *
 * Main topics:
 *   - ResizeObserver
 *   - Container-aware application behavior
 *   - CSS custom properties
 *   - clamp() inspection
 *   - responsive component state
 *   - debounced resize work
 *   - validation and error handling
 *   - performance-aware DOM updates
 *
 * Run this file:
 *   1. In a browser by loading it from an HTML document.
 *   2. With Node.js to execute the mathematical demonstrations.
 *
 * Browser-specific code checks for DOM APIs before using them.
 */

// ---------------------------------------------------------------------------
// 1. BASIC RESPONSIVE MATH
// ---------------------------------------------------------------------------

function clampValue(minimum, preferred, maximum) {
    if (minimum > maximum) {
        throw new RangeError("minimum cannot exceed maximum");
    }

    return Math.max(minimum, Math.min(preferred, maximum));
}

function linearInterpolate(
    value,
    inputMinimum,
    inputMaximum,
    outputMinimum,
    outputMaximum
) {
    if (inputMaximum <= inputMinimum) {
        throw new RangeError(
            "inputMaximum must be greater than inputMinimum"
        );
    }

    const ratio = (value - inputMinimum) /
        (inputMaximum - inputMinimum);

    const boundedRatio = Math.max(0, Math.min(1, ratio));

    return outputMinimum +
        boundedRatio * (outputMaximum - outputMinimum);
}

function responsiveFontSize(width) {
    const preferred = linearInterpolate(
        width,
        320,
        1440,
        20,
        32
    );

    return clampValue(20, preferred, 32);
}

function demonstrateFluidMath() {
    const widths = [240, 320, 480, 768, 1024, 1440, 1920];

    console.log("Fluid typography:");

    for (const width of widths) {
        console.log(
            `${width}px -> ${responsiveFontSize(width).toFixed(1)}px`
        );
    }
}


// ---------------------------------------------------------------------------
// 2. RESPONSIVE COMPONENT STATE
// ---------------------------------------------------------------------------

class ResponsiveCardController {
    constructor(element) {
        if (!(element instanceof HTMLElement)) {
            throw new TypeError(
                "ResponsiveCardController requires an HTMLElement"
            );
        }

        this.element = element;
        this.lastWidth = null;
        this.resizeObserver = null;
    }

    calculateState(width) {
        if (width < 360) {
            return {
                mode: "compact",
                columns: 1,
                showDescription: false
            };
        }

        if (width < 640) {
            return {
                mode: "standard",
                columns: 1,
                showDescription: true
            };
        }

        return {
            mode: "expanded",
            columns: 2,
            showDescription: true
        };
    }

    update(width) {
        const state = this.calculateState(width);

        this.element.dataset.responsiveMode = state.mode;

        // CSS should perform most visual layout work. JavaScript only stores
        // application state when the application genuinely needs it.
        this.element.style.setProperty(
            "--observed-width",
            `${Math.round(width)}px`
        );

        this.lastWidth = width;

        return state;
    }

    connect() {
        if (!("ResizeObserver" in window)) {
            throw new Error(
                "ResizeObserver is not supported by this browser."
            );
        }

        this.resizeObserver = new ResizeObserver((entries) => {
            for (const entry of entries) {
                this.update(entry.contentRect.width);
            }
        });

        this.resizeObserver.observe(this.element);
    }

    disconnect() {
        if (this.resizeObserver) {
            this.resizeObserver.disconnect();
            this.resizeObserver = null;
        }
    }
}


// ---------------------------------------------------------------------------
// 3. CSS CUSTOM PROPERTIES
// ---------------------------------------------------------------------------

function readResponsiveCustomProperties(element) {
    if (!(element instanceof HTMLElement)) {
        throw new TypeError("Expected an HTMLElement.");
    }

    const computedStyle = getComputedStyle(element);

    return {
        pagePadding: computedStyle
            .getPropertyValue("--page-padding")
            .trim(),

        sectionGap: computedStyle
            .getPropertyValue("--section-gap")
            .trim(),

        headingSize: computedStyle
            .getPropertyValue("--heading-size")
            .trim()
    };
}


// ---------------------------------------------------------------------------
// 4. CONTAINER-BASED INFORMATION
// ---------------------------------------------------------------------------

function getElementWidth(element) {
    if (!(element instanceof Element)) {
        throw new TypeError("Expected a DOM Element.");
    }

    return element.getBoundingClientRect().width;
}

function describeContainer(element) {
    const width = getElementWidth(element);

    let category;

    if (width < 360) {
        category = "compact";
    } else if (width < 640) {
        category = "standard";
    } else if (width < 960) {
        category = "expanded";
    } else {
        category = "wide";
    }

    return {
        width: Math.round(width),
        category
    };
}


// ---------------------------------------------------------------------------
// 5. RESPONSIVE DASHBOARD
// ---------------------------------------------------------------------------

class ResponsiveDashboard {
    constructor(root) {
        if (!(root instanceof HTMLElement)) {
            throw new TypeError(
                "ResponsiveDashboard requires an HTMLElement"
            );
        }

        this.root = root;
        this.observer = null;
        this.updateCount = 0;
    }

    calculateColumns(width) {
        if (width < 500) {
            return 1;
        }

        if (width < 800) {
            return 2;
        }

        if (width < 1100) {
            return 3;
        }

        return 4;
    }

    update(width) {
        const columns = this.calculateColumns(width);

        this.root.dataset.columns = String(columns);
        this.root.style.setProperty(
            "--application-columns",
            String(columns)
        );

        this.updateCount += 1;

        return columns;
    }

    start() {
        if (!("ResizeObserver" in window)) {
            throw new Error(
                "ResizeObserver is required for this dashboard."
            );
        }

        this.observer = new ResizeObserver((entries) => {
            const entry = entries[0];

            if (!entry) {
                return;
            }

            this.update(entry.contentRect.width);
        });

        this.observer.observe(this.root);
    }

    stop() {
        this.observer?.disconnect();
        this.observer = null;
    }
}


// ---------------------------------------------------------------------------
// 6. EVENT DELEGATION
// ---------------------------------------------------------------------------

function installCardInteractions(root) {
    if (!(root instanceof HTMLElement)) {
        throw new TypeError("Expected an HTMLElement root.");
    }

    root.addEventListener("click", (event) => {
        const target = event.target;

        if (!(target instanceof Element)) {
            return;
        }

        const button = target.closest("[data-action]");

        if (!button || !root.contains(button)) {
            return;
        }

        const card = button.closest(".demo-card");

        if (!card) {
            return;
        }

        const action = button.getAttribute("data-action");

        if (action === "toggle") {
            card.classList.toggle("is-active");

            button.textContent = card.classList.contains("is-active")
                ? "Active"
                : "Toggle";
        }

        if (action === "inspect") {
            const details = describeContainer(card);
            console.log("Container information:", details);
        }
    });
}


// ---------------------------------------------------------------------------
// 7. RESIZE HANDLING FOR VIEWPORT-LEVEL APPLICATION LOGIC
// ---------------------------------------------------------------------------

function createDebouncedFunction(callback, delay = 150) {
    if (typeof callback !== "function") {
        throw new TypeError("callback must be a function");
    }

    let timeoutId = null;

    return (...argumentsList) => {
        clearTimeout(timeoutId);

        timeoutId = setTimeout(() => {
            callback(...argumentsList);
        }, delay);
    };
}

function installViewportDiagnostics() {
    const update = () => {
        const width = window.innerWidth;
        const height = window.innerHeight;

        console.log(
            `Viewport: ${width}px × ${height}px`
        );
    };

    const debouncedUpdate = createDebouncedFunction(update, 200);

    window.addEventListener("resize", debouncedUpdate);

    update();
}


// ---------------------------------------------------------------------------
// 8. ACCESSIBILITY-AWARE RESPONSIVE BEHAVIOR
// ---------------------------------------------------------------------------

function inspectMotionPreference() {
    if (!window.matchMedia) {
        return "unknown";
    }

    return window.matchMedia(
        "(prefers-reduced-motion: reduce)"
    ).matches
        ? "reduced"
        : "normal";
}

function installMotionPreferenceListener(callback) {
    if (typeof callback !== "function") {
        throw new TypeError("callback must be a function");
    }

    if (!window.matchMedia) {
        return () => {};
    }

    const mediaQuery = window.matchMedia(
        "(prefers-reduced-motion: reduce)"
    );

    const listener = () => {
        callback(mediaQuery.matches);
    };

    mediaQuery.addEventListener("change", listener);

    return () => {
        mediaQuery.removeEventListener("change", listener);
    };
}


// ---------------------------------------------------------------------------
// 9. VALIDATION
// ---------------------------------------------------------------------------

function validateResponsiveConfiguration(configuration) {
    if (!configuration ||
        typeof configuration !== "object") {
        throw new TypeError(
            "configuration must be an object"
        );
    }

    const {
        minimumWidth,
        maximumWidth,
        minimumFontSize,
        maximumFontSize
    } = configuration;

    const errors = [];

    if (!Number.isFinite(minimumWidth) || minimumWidth < 0) {
        errors.push("minimumWidth must be a non-negative number");
    }

    if (!Number.isFinite(maximumWidth) ||
        maximumWidth <= minimumWidth) {
        errors.push(
            "maximumWidth must be greater than minimumWidth"
        );
    }

    if (!Number.isFinite(minimumFontSize) ||
        minimumFontSize <= 0) {
        errors.push(
            "minimumFontSize must be greater than zero"
        );
    }

    if (!Number.isFinite(maximumFontSize) ||
        maximumFontSize < minimumFontSize) {
        errors.push(
            "maximumFontSize must not be smaller than minimumFontSize"
        );
    }

    return {
        valid: errors.length === 0,
        errors
    };
}


// ---------------------------------------------------------------------------
// 10. NODE-SAFE DEMONSTRATION
// ---------------------------------------------------------------------------

function runNodeDemonstration() {
    console.log(
        "=== ADVANCED RESPONSIVE DESIGN: JAVASCRIPT ==="
    );

    demonstrateFluidMath();

    const configuration = {
        minimumWidth: 320,
        maximumWidth: 1440,
        minimumFontSize: 20,
        maximumFontSize: 32
    };

    console.log(
        "Configuration validation:",
        validateResponsiveConfiguration(configuration)
    );

    console.log(
        "Invalid configuration validation:",
        validateResponsiveConfiguration({
            minimumWidth: 1000,
            maximumWidth: 500,
            minimumFontSize: 0,
            maximumFontSize: 10
        })
    );
}


// ---------------------------------------------------------------------------
// 11. BROWSER INITIALIZATION
// ---------------------------------------------------------------------------

function initializeBrowserDemo() {
    const cards = document.querySelectorAll(".demo-card");

    for (const card of cards) {
        const controller = new ResponsiveCardController(card);
        controller.connect();

        // Keep a reference so the controller is not accidentally discarded
        // by application code that later needs to disconnect observers.
        card.responsiveController = controller;
    }

    const interactionRoot = document.querySelector("main");

    if (interactionRoot) {
        installCardInteractions(interactionRoot);
    }

    const dashboardRoot = document.querySelector(
        ".responsive-dashboard"
    );

    if (dashboardRoot) {
        const dashboard = new ResponsiveDashboard(dashboardRoot);
        dashboard.start();
        dashboardRoot.responsiveDashboard = dashboard;
    }

    installViewportDiagnostics();

    console.log(
        "Motion preference:",
        inspectMotionPreference()
    );

    const removeMotionListener =
        installMotionPreferenceListener((reduced) => {
            console.log(
                "Motion preference changed:",
                reduced ? "reduced" : "normal"
            );
        });

    window.removeResponsiveMotionListener = removeMotionListener;
}


// ---------------------------------------------------------------------------
// 12. EXECUTION
// ---------------------------------------------------------------------------

if (typeof window === "undefined") {
    runNodeDemonstration();
} else {
    window.addEventListener(
        "DOMContentLoaded",
        initializeBrowserDemo,
        { once: true }
    );
}
