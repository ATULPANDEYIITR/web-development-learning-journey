/*
 * CSS Transitions — JavaScript Laboratory
 *
 * This file complements a CSS transition study by:
 *   1. Generating transition CSS.
 *   2. Simulating timing functions.
 *   3. Modeling interactive component states.
 *   4. Demonstrating DOM-based transitions in a browser.
 *   5. Demonstrating transition events.
 *   6. Demonstrating validation and performance-oriented design.
 *
 * The file is self-contained and uses only standard JavaScript and browser
 * APIs. It can be executed with Node.js for the non-DOM demonstrations.
 */

"use strict";


// ============================================================================
// 1. BASIC UTILITIES
// ============================================================================

function clamp(value, minimum = 0, maximum = 1) {
    return Math.max(minimum, Math.min(maximum, value));
}

function interpolate(start, end, progress) {
    const t = clamp(progress);
    return start + (end - start) * t;
}

function cssTime(milliseconds) {
    if (!Number.isFinite(milliseconds) || milliseconds < 0) {
        throw new RangeError("CSS time must be a non-negative finite number.");
    }

    return `${milliseconds}ms`;
}


// ============================================================================
// 2. TRANSITION REPRESENTATION
// ============================================================================

class Transition {
    constructor(property, duration, timingFunction = "ease", delay = 0) {
        if (!property || typeof property !== "string") {
            throw new TypeError("property must be a non-empty string.");
        }

        if (!Number.isFinite(duration) || duration < 0) {
            throw new RangeError("duration must be >= 0.");
        }

        if (!Number.isFinite(delay) || delay < 0) {
            throw new RangeError("delay must be >= 0.");
        }

        this.property = property;
        this.duration = duration;
        this.timingFunction = timingFunction;
        this.delay = delay;
    }

    toCSS() {
        return `${this.property} ${cssTime(this.duration)} ` +
            `${this.timingFunction} ${cssTime(this.delay)}`;
    }

    get totalTime() {
        return this.duration + this.delay;
    }
}

const basicTransition = new Transition(
    "transform",
    240,
    "ease-out",
    0
);

console.log("Basic transition:", basicTransition.toCSS());
console.log("Total time:", basicTransition.totalTime, "ms");


// ============================================================================
// 3. CSS TIMING FUNCTIONS
// ============================================================================

function linear(t) {
    return clamp(t);
}

function easeIn(t) {
    const x = clamp(t);
    return x ** 3;
}

function easeOut(t) {
    const x = clamp(t);
    return 1 - (1 - x) ** 3;
}

function easeInOut(t) {
    const x = clamp(t);

    if (x < 0.5) {
        return 4 * x ** 3;
    }

    return 1 - ((-2 * x + 2) ** 3) / 2;
}

/*
 * Cubic Bézier timing functions use two control points.
 *
 * CSS syntax:
 *
 *     cubic-bezier(x1, y1, x2, y2)
 *
 * The x coordinates control time mapping and the y coordinates control
 * output progress.
 */
function cubicBezier(x1, y1, x2, y2) {
    if (
        x1 < 0 || x1 > 1 ||
        x2 < 0 || x2 > 1
    ) {
        throw new RangeError(
            "CSS cubic-bezier x coordinates must be between 0 and 1."
        );
    }

    function coordinate(t, first, second) {
        return (
            3 * (1 - t) ** 2 * t * first +
            3 * (1 - t) * t ** 2 * second +
            t ** 3
        );
    }

    return function timingFunction(progress) {
        const targetX = clamp(progress);

        let low = 0;
        let high = 1;

        /*
         * x(t) is numerically inverted so that the corresponding y(t)
         * represents visual progress at the requested elapsed-time fraction.
         */
        for (let iteration = 0; iteration < 30; iteration += 1) {
            const middle = (low + high) / 2;
            const currentX = coordinate(middle, x1, x2);

            if (currentX < targetX) {
                low = middle;
            } else {
                high = middle;
            }
        }

        const parameter = (low + high) / 2;
        return coordinate(parameter, y1, y2);
    };
}

const timingFunctions = {
    linear,
    "ease-in": easeIn,
    "ease-out": easeOut,
    "ease-in-out": easeInOut,
    ease: cubicBezier(0.25, 0.1, 0.25, 1)
};

console.log("\nTiming-function samples:");

for (const [name, functionReference] of Object.entries(timingFunctions)) {
    const values = [0, 0.25, 0.5, 0.75, 1].map(
        point => Number(functionReference(point).toFixed(3))
    );

    console.log(name.padStart(12), values);
}


// ============================================================================
// 4. STEPPED TIMING
// ============================================================================

function steps(count, progress, position = "end") {
    if (!Number.isInteger(count) || count <= 0) {
        throw new RangeError("count must be a positive integer.");
    }

    const t = clamp(progress);

    if (position === "end") {
        if (count === 1) {
            return 1;
        }

        return Math.min(count - 1, Math.floor(t * count)) / (count - 1);
    }

    if (position === "start") {
        return Math.min(count, Math.floor(t * count) + 1) / count;
    }

    throw new RangeError("position must be 'start' or 'end'.");
}

console.log("\nsteps(5, t, 'end'):");

for (const point of [0, 0.25, 0.5, 0.75, 1]) {
    console.log(point, steps(5, point, "end"));
}


// ============================================================================
// 5. SIMULATING PROPERTY INTERPOLATION
// ============================================================================

function sampleTransition(start, end, timingFunction, sampleCount = 11) {
    if (sampleCount < 2) {
        throw new RangeError("sampleCount must be at least 2.");
    }

    const samples = [];

    for (let index = 0; index < sampleCount; index += 1) {
        const elapsedProgress = index / (sampleCount - 1);
        const visualProgress = timingFunction(elapsedProgress);

        samples.push({
            timeProgress: elapsedProgress,
            visualProgress,
            value: interpolate(start, end, visualProgress)
        });
    }

    return samples;
}

console.log("\nOpacity transition from 0 to 1:");

for (const sample of sampleTransition(0, 1, easeOut)) {
    console.log(
        `time=${sample.timeProgress.toFixed(2)} ` +
        `visual=${sample.visualProgress.toFixed(3)} ` +
        `value=${sample.value.toFixed(3)}`
    );
}


// ============================================================================
// 6. TRANSITION LISTS
// ============================================================================

function buildTransitionList(transitions) {
    if (!Array.isArray(transitions) || transitions.length === 0) {
        throw new TypeError("At least one transition is required.");
    }

    return transitions.map(item => {
        if (!(item instanceof Transition)) {
            throw new TypeError(
                "Every item must be a Transition instance."
            );
        }

        return item.toCSS();
    }).join(", ");
}

const cardTransition = buildTransitionList([
    new Transition("transform", 220, "ease-out"),
    new Transition("opacity", 180, "linear"),
    new Transition("box-shadow", 300, "ease")
]);

console.log("\nMultiple properties:");
console.log(cardTransition);


// ============================================================================
// 7. GENERATING COMPONENT CSS
// ============================================================================

function createButtonCSS() {
    return `
.button {
    background-color: #1f2937;
    color: white;
    transform: translateY(0);
    transition:
        background-color 200ms ease,
        transform 200ms ease,
        box-shadow 200ms ease;
}

.button:hover {
    background-color: #334155;
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgb(0 0 0 / 0.20);
}

.button:focus-visible {
    outline: 3px solid currentColor;
    outline-offset: 3px;
}

.button:active {
    transform: translateY(0) scale(0.98);
}
`.trim();
}

console.log("\nGenerated button CSS:");
console.log(createButtonCSS());


// ============================================================================
// 8. INTERACTIVE STATE MODEL
// ============================================================================

class InteractiveButtonModel {
    static STATES = new Set([
        "idle",
        "hover",
        "focus",
        "active",
        "disabled"
    ]);

    constructor() {
        this.state = "idle";
    }

    setState(nextState) {
        if (!InteractiveButtonModel.STATES.has(nextState)) {
            throw new Error(`Invalid state: ${nextState}`);
        }

        this.state = nextState;
    }

    getStyles() {
        const styles = {
            transform: "translateY(0) scale(1)",
            opacity: "1",
            cursor: "pointer"
        };

        switch (this.state) {
            case "hover":
                styles.transform = "translateY(-2px) scale(1)";
                break;

            case "focus":
                styles.outline = "3px solid currentColor";
                break;

            case "active":
                styles.transform = "translateY(0) scale(0.98)";
                break;

            case "disabled":
                styles.opacity = "0.55";
                styles.cursor = "not-allowed";
                break;

            default:
                break;
        }

        return styles;
    }
}

const buttonModel = new InteractiveButtonModel();

console.log("\nButton states:");

for (const state of InteractiveButtonModel.STATES) {
    buttonModel.setState(state);
    console.log(state, buttonModel.getStyles());
}


// ============================================================================
// 9. CSS CUSTOM PROPERTIES AND DESIGN TOKENS
// ============================================================================

const motionTokens = Object.freeze({
    instant: Object.freeze({
        duration: 0,
        easing: "linear"
    }),
    quick: Object.freeze({
        duration: 120,
        easing: "ease-out"
    }),
    standard: Object.freeze({
        duration: 220,
        easing: "ease"
    }),
    emphasis: Object.freeze({
        duration: 400,
        easing: "ease-in-out"
    })
});

function transitionFromToken(tokenName, propertyName) {
    const token = motionTokens[tokenName];

    if (!token) {
        throw new Error(`Unknown motion token: ${tokenName}`);
    }

    return (
        `${propertyName} ${cssTime(token.duration)} ${token.easing}`
    );
}

console.log("\nMotion tokens:");
console.log(transitionFromToken("quick", "transform"));
console.log(transitionFromToken("standard", "opacity"));


// ============================================================================
// 10. STAGGERED DELAYS
// ============================================================================

function createStaggeredTransitions(
    itemCount,
    baseDelay = 0,
    delayStep = 60
) {
    if (!Number.isInteger(itemCount) || itemCount < 0) {
        throw new RangeError("itemCount must be a non-negative integer.");
    }

    if (baseDelay < 0 || delayStep < 0) {
        throw new RangeError("Delay values must be non-negative.");
    }

    return Array.from({ length: itemCount }, (_, index) => {
        return new Transition(
            "opacity",
            300,
            "ease-out",
            baseDelay + index * delayStep
        );
    });
}

console.log("\nStaggered transitions:");

createStaggeredTransitions(5).forEach((transition, index) => {
    console.log(`Item ${index + 1}:`, transition.toCSS());
});


// ============================================================================
// 11. TRANSITION TIMELINE
// ============================================================================

function createTimeline(duration, delay, sampleCount = 8) {
    if (duration < 0 || delay < 0) {
        throw new RangeError("duration and delay must be non-negative.");
    }

    const total = duration + delay;

    if (total === 0) {
        return [{ elapsed: 0, progress: 1 }];
    }

    const timeline = [];

    for (let index = 0; index < sampleCount; index += 1) {
        const elapsed = total * index / (sampleCount - 1);

        let progress;

        if (elapsed <= delay) {
            progress = 0;
        } else {
            progress = duration === 0
                ? 1
                : clamp((elapsed - delay) / duration);
        }

        timeline.push({
            elapsed: Math.round(elapsed),
            progress
        });
    }

    return timeline;
}

console.log("\nTimeline with 200ms delay and 400ms duration:");

console.table(createTimeline(400, 200));


// ============================================================================
// 12. VALIDATION
// ============================================================================

const commonlyTransitionedProperties = new Set([
    "opacity",
    "transform",
    "color",
    "background-color",
    "border-color",
    "box-shadow",
    "width",
    "height",
    "filter",
    "visibility"
]);

function validateTransition(transition) {
    if (!(transition instanceof Transition)) {
        throw new TypeError("Expected a Transition instance.");
    }

    const warnings = [];

    if (!commonlyTransitionedProperties.has(transition.property)) {
        warnings.push(
            `Property '${transition.property}' is not in the educational ` +
            "common-property list."
        );
    }

    if (transition.duration > 1000) {
        warnings.push(
            "The duration exceeds one second; verify that the interaction " +
            "does not feel delayed."
        );
    }

    if (
        transition.property === "width" ||
        transition.property === "height"
    ) {
        warnings.push(
            "Dimension changes can affect layout and should be tested " +
            "for rendering performance."
        );
    }

    if (transition.property === "box-shadow") {
        warnings.push(
            "Complex shadows can increase paint cost."
        );
    }

    return warnings;
}

const validationTarget = new Transition(
    "width",
    1200,
    "ease",
    100
);

console.log("\nValidation warnings:");
console.log(validateTransition(validationTarget));


// ============================================================================
// 13. BROWSER DEMONSTRATION
// ============================================================================

function createBrowserDemo() {
    if (typeof document === "undefined") {
        console.log(
            "\nBrowser demonstration skipped: document is not available."
        );
        return;
    }

    const style = document.createElement("style");

    style.textContent = `
        .transition-lab {
            min-height: 100vh;
            padding: 40px;
            background: #030712;
            color: #f8fafc;
            font-family: system-ui, sans-serif;
        }

        .transition-lab__grid {
            display: grid;
            grid-template-columns:
                repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
            max-width: 900px;
            margin: 0 auto;
        }

        .transition-lab__card {
            padding: 24px;
            border: 1px solid #374151;
            border-radius: 16px;
            background: #111827;

            /*
             * Keep the transition on the base element. This means both
             * entering and leaving the hover state are interpolated.
             */
            transform: translateY(0) scale(1);

            transition:
                transform 240ms cubic-bezier(0.2, 0.8, 0.2, 1),
                background-color 240ms ease,
                border-color 240ms ease,
                box-shadow 240ms ease;
        }

        .transition-lab__card:hover {
            transform: translateY(-6px) scale(1.02);
            background: #1f2937;
            border-color: #60a5fa;
            box-shadow: 0 18px 40px rgb(0 0 0 / 0.35);
        }

        .transition-lab__button {
            margin-top: 20px;
            padding: 12px 18px;
            border: 0;
            border-radius: 10px;
            background: #60a5fa;
            color: #0f172a;
            cursor: pointer;

            transition:
                transform 160ms ease-out,
                filter 160ms ease-out;
        }

        .transition-lab__button:hover {
            transform: translateY(-2px);
            filter: brightness(1.1);
        }

        .transition-lab__button:active {
            transform: translateY(0) scale(0.97);
        }

        .transition-lab__button:focus-visible {
            outline: 3px solid white;
            outline-offset: 3px;
        }

        .transition-lab__panel {
            max-width: 900px;
            margin: 24px auto 0;
            padding: 20px;
            border-radius: 12px;
            background: #1f2937;

            opacity: 0;
            transform: translateY(12px);
            pointer-events: none;

            transition:
                opacity 220ms ease,
                transform 220ms ease;
        }

        .transition-lab__panel.is-open {
            opacity: 1;
            transform: translateY(0);
            pointer-events: auto;
        }

        @media (prefers-reduced-motion: reduce) {
            *,
            *::before,
            *::after {
                transition-duration: 0.01ms !important;
            }
        }
    `;

    document.head.appendChild(style);

    const root = document.createElement("main");
    root.className = "transition-lab";

    root.innerHTML = `
        <section class="transition-lab__grid">
            <article class="transition-lab__card">
                <h2>Transform</h2>
                <p>Hover to move and scale the card.</p>
            </article>

            <article class="transition-lab__card">
                <h2>Color</h2>
                <p>Background and border colors also transition.</p>
            </article>

            <article class="transition-lab__card">
                <h2>Shadow</h2>
                <p>The shadow changes with the interactive state.</p>
            </article>
        </section>

        <section class="transition-lab__grid">
            <button
                class="transition-lab__button"
                type="button"
                id="transition-lab-toggle"
            >
                Toggle panel
            </button>
        </section>

        <section
            class="transition-lab__panel"
            id="transition-lab-panel"
            aria-hidden="true"
        >
            <h2>Animated panel</h2>
            <p>
                Opacity and transform transition between closed and open
                states.
            </p>
        </section>
    `;

    document.body.appendChild(root);

    const toggleButton = document.querySelector(
        "#transition-lab-toggle"
    );

    const panel = document.querySelector(
        "#transition-lab-panel"
    );

    toggleButton.addEventListener("click", () => {
        const isOpen = panel.classList.toggle("is-open");

        panel.setAttribute(
            "aria-hidden",
            String(!isOpen)
        );
    });

    /*
     * transitionrun fires when a transition is generated.
     */
    panel.addEventListener("transitionrun", event => {
        console.log(
            "transitionrun:",
            event.propertyName
        );
    });

    /*
     * transitionstart fires when the active transition begins after delay.
     */
    panel.addEventListener("transitionstart", event => {
        console.log(
            "transitionstart:",
            event.propertyName
        );
    });

    /*
     * transitionend indicates normal completion.
     */
    panel.addEventListener("transitionend", event => {
        console.log(
            "transitionend:",
            event.propertyName
        );
    });

    /*
     * transitioncancel indicates that the transition did not complete.
     */
    panel.addEventListener("transitioncancel", event => {
        console.log(
            "transitioncancel:",
            event.propertyName
        );
    });

    return root;
}


// ============================================================================
// 14. REQUESTANIMATIONFRAME EXAMPLE
// ============================================================================

function demonstrateAnimationFrameSampling() {
    if (typeof requestAnimationFrame === "undefined") {
        console.log(
            "\nrequestAnimationFrame is unavailable in this runtime."
        );
        return;
    }

    /*
     * requestAnimationFrame is useful when JavaScript itself must calculate
     * per-frame values. For ordinary CSS transitions, prefer CSS rather than
     * replacing the browser's optimized CSS interpolation with a JavaScript
     * frame loop.
     */
    const startTime = performance.now();
    const duration = 500;

    function frame(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = clamp(elapsed / duration);
        const visualProgress = easeOut(progress);

        console.log({
            elapsed: Math.round(elapsed),
            progress: Number(progress.toFixed(3)),
            visualProgress: Number(visualProgress.toFixed(3))
        });

        if (progress < 1) {
            requestAnimationFrame(frame);
        }
    }

    requestAnimationFrame(frame);
}


// ============================================================================
// 15. TRANSITION EVENTS AS PROMISE
// ============================================================================

function waitForTransition(element, propertyName, timeout = 1000) {
    /*
     * A production application should not wait indefinitely for
     * transitionend because a transition can be canceled or disabled.
     */
    if (!(element instanceof Element)) {
        throw new TypeError("element must be a DOM Element.");
    }

    return new Promise(resolve => {
        let finished = false;

        const cleanup = result => {
            if (finished) {
                return;
            }

            finished = true;
            clearTimeout(timer);
            element.removeEventListener(
                "transitionend",
                handleEnd
            );
            element.removeEventListener(
                "transitioncancel",
                handleCancel
            );
            resolve(result);
        };

        const handleEnd = event => {
            if (
                !propertyName ||
                event.propertyName === propertyName
            ) {
                cleanup({
                    status: "ended",
                    propertyName: event.propertyName
                });
            }
        };

        const handleCancel = event => {
            if (
                !propertyName ||
                event.propertyName === propertyName
            ) {
                cleanup({
                    status: "cancelled",
                    propertyName: event.propertyName
                });
            }
        };

        const timer = setTimeout(() => {
            cleanup({
                status: "timeout",
                propertyName
            });
        }, timeout);

        element.addEventListener(
            "transitionend",
            handleEnd
        );

        element.addEventListener(
            "transitioncancel",
            handleCancel
        );
    });
}


// ============================================================================
// 16. TRANSITION VS JAVASCRIPT
// ============================================================================

function chooseImplementation(requirement) {
    const cssFriendly = new Set([
        "hover",
        "focus",
        "active",
        "simple-state-change",
        "visual-emphasis"
    ]);

    const javascriptUseful = new Set([
        "complex-sequence",
        "dynamic-data",
        "physics-like-control",
        "application-state-coordination"
    ]);

    if (cssFriendly.has(requirement)) {
        return "Prefer CSS transitions.";
    }

    if (javascriptUseful.has(requirement)) {
        return (
            "JavaScript may coordinate state while CSS handles visual " +
            "interpolation."
        );
    }

    return "Evaluate the requirement before selecting CSS or JavaScript.";
}

console.log("\nImplementation choices:");
console.log(
    "hover:",
    chooseImplementation("hover")
);
console.log(
    "complex sequence:",
    chooseImplementation("complex-sequence")
);


// ============================================================================
// 17. PERFORMANCE GUIDANCE
// ============================================================================

const performanceGuidance = [
    {
        property: "transform",
        characteristic: "Often suitable for movement.",
        reason: "Avoids directly changing geometric layout in common cases."
    },
    {
        property: "opacity",
        characteristic: "Often suitable for fades.",
        reason: "Commonly handled efficiently by the rendering pipeline."
    },
    {
        property: "width",
        characteristic: "Layout-sensitive.",
        reason: "Changing dimensions can affect surrounding layout."
    },
    {
        property: "height",
        characteristic: "Layout-sensitive.",
        reason: "May cause layout recalculation."
    },
    {
        property: "box-shadow",
        characteristic: "Paint-sensitive.",
        reason: "Complex shadows can increase rendering cost."
    }
];

console.log("\nPerformance guidance:");
console.table(performanceGuidance);


// ============================================================================
// 18. ACCESSIBILITY
// ============================================================================

function accessibilityChecklist() {
    return [
        "Provide :focus-visible styling for keyboard users.",
        "Do not make essential information hover-only.",
        "Do not rely exclusively on color to communicate state.",
        "Respect prefers-reduced-motion.",
        "Keep transition durations short enough for responsive controls.",
        "Do not make motion so strong that it distracts from content.",
        "Keep the semantic state independent from the visual transition."
    ];
}

console.log("\nAccessibility checklist:");
accessibilityChecklist().forEach(
    (item, index) => console.log(`${index + 1}. ${item}`)
);


// ============================================================================
// 19. CSS GENERATOR FOR A COMPLETE COMPONENT
// ============================================================================

function createCardComponentCSS() {
    const transformTransition = new Transition(
        "transform",
        220,
        "cubic-bezier(0.2, 0.8, 0.2, 1)"
    );

    const colorTransition = new Transition(
        "background-color",
        220,
        "ease"
    );

    const borderTransition = new Transition(
        "border-color",
        220,
        "ease"
    );

    const shadowTransition = new Transition(
        "box-shadow",
        300,
        "ease"
    );

    const transition = buildTransitionList([
        transformTransition,
        colorTransition,
        borderTransition,
        shadowTransition
    ]);

    return `
.card {
    transform: translateY(0);
    background-color: #111827;
    border-color: #374151;
    box-shadow: 0 4px 14px rgb(0 0 0 / 0.12);
    transition: ${transition};
}

.card:hover {
    transform: translateY(-5px);
    background-color: #1f2937;
    border-color: #60a5fa;
    box-shadow: 0 16px 36px rgb(0 0 0 / 0.25);
}

.card:focus-visible {
    outline: 3px solid #60a5fa;
    outline-offset: 4px;
}

@media (prefers-reduced-motion: reduce) {
    .card {
        transition-duration: 0.01ms;
    }
}
`.trim();
}

console.log("\nComplete component CSS:");
console.log(createCardComponentCSS());


// ============================================================================
// 20. EDGE CASES
// ============================================================================

const edgeCases = [
    [
        "Zero duration",
        "The state changes without visible interpolation."
    ],
    [
        "Long delay",
        "The state change can appear unresponsive."
    ],
    [
        "Repeated state changes",
        "A transition can be interrupted and replaced."
    ],
    [
        "Removed element",
        "The transition may never emit a normal transitionend."
    ],
    [
        "Non-interpolable property",
        "The property may use discrete transition behavior."
    ],
    [
        "Transform overwrite",
        "A later transform declaration replaces an earlier one."
    ],
    [
        "Reduced motion",
        "Motion should be substantially reduced when requested."
    ],
    [
        "Hover on touch devices",
        "Hover behavior is not equivalent to pointer-independent input."
    ]
];

console.log("\nEdge cases:");

for (const [name, behavior] of edgeCases) {
    console.log(`${name}: ${behavior}`);
}


// ============================================================================
// 21. SELF-TESTS
// ============================================================================

function assert(condition, message) {
    if (!condition) {
        throw new Error(`Assertion failed: ${message}`);
    }
}

function runTests() {
    assert(clamp(-1) === 0, "clamp lower boundary");
    assert(clamp(0.5) === 0.5, "clamp middle");
    assert(clamp(2) === 1, "clamp upper boundary");

    assert(
        interpolate(0, 100, 0.5) === 50,
        "numeric interpolation"
    );

    assert(
        linear(0.5) === 0.5,
        "linear timing"
    );

    assert(
        easeIn(0) === 0 && easeIn(1) === 1,
        "ease-in boundaries"
    );

    assert(
        easeOut(0) === 0 && easeOut(1) === 1,
        "ease-out boundaries"
    );

    const transition = new Transition(
        "opacity",
        300,
        "ease",
        100
    );

    assert(
        transition.totalTime === 400,
        "transition total time"
    );

    assert(
        transition.toCSS() === "opacity 300ms ease 100ms",
        "transition shorthand"
    );

    const combined = buildTransitionList([
        new Transition("opacity", 200),
        new Transition("transform", 250, "ease-out")
    ]);

    assert(
        combined.includes("opacity 200ms ease 0ms"),
        "opacity transition"
    );

    assert(
        combined.includes("transform 250ms ease-out 0ms"),
        "transform transition"
    );

    console.log("\nAll JavaScript tests passed.");
}

runTests();


// ============================================================================
// 22. OPTIONAL BROWSER INITIALIZATION
// ============================================================================

if (typeof document !== "undefined") {
    /*
     * This code executes only when the file is loaded in a browser.
     * It does not execute during normal Node.js execution.
     */
    if (document.readyState === "loading") {
        document.addEventListener(
            "DOMContentLoaded",
            createBrowserDemo,
            { once: true }
        );
    } else {
        createBrowserDemo();
    }
}


// ============================================================================
// 23. NODE.JS-SAFE EXPORTS
// ============================================================================

if (typeof module !== "undefined" && module.exports) {
    module.exports = {
        Transition,
        clamp,
        interpolate,
        linear,
        easeIn,
        easeOut,
        easeInOut,
        cubicBezier,
        steps,
        sampleTransition,
        buildTransitionList,
        validateTransition,
        createTimeline,
        createStaggeredTransitions,
        transitionFromToken,
        chooseImplementation
    };
}

/*
 * Important architectural principle:
 *
 * CSS should normally own simple visual transitions:
 *
 *     state -> CSS class/pseudo-class -> transition
 *
 * JavaScript should normally own application state and complex coordination:
 *
 *     application event -> state change -> CSS class -> CSS transition
 *
 * This separation keeps visual interpolation declarative while allowing
 * JavaScript to coordinate behavior when application logic requires it.
 */
