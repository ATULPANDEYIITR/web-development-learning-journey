/**
 * CSS Animations: Keyframes, Animation Properties, Transforms,
 * Performance, Accessibility, and Browser-Oriented Design
 *
 * This file uses JavaScript to model important animation concepts numerically
 * and to demonstrate how CSS animation behavior can be represented in an
 * application-oriented environment.
 *
 * It can be executed with a modern JavaScript runtime such as Node.js.
 */

"use strict";

// ============================================================================
// 1. BASIC INTERPOLATION
// ============================================================================

function clamp(value, minimum = 0, maximum = 1) {
    return Math.min(maximum, Math.max(minimum, value));
}

function lerp(start, end, progress) {
    return start + (end - start) * clamp(progress);
}

console.log("=== 1. Linear interpolation ===");

for (const progress of [0, 0.25, 0.5, 0.75, 1]) {
    console.log(
        `progress=${progress.toFixed(2)} -> ` +
        `${lerp(0, 100, progress).toFixed(2)}px`
    );
}


// ============================================================================
// 2. EASING FUNCTIONS
// ============================================================================

function linear(progress) {
    return progress;
}

function easeIn(progress) {
    return progress ** 2;
}

function easeOut(progress) {
    return 1 - (1 - progress) ** 2;
}

function easeInOut(progress) {
    if (progress < 0.5) {
        return 2 * progress ** 2;
    }

    return 1 - ((-2 * progress + 2) ** 2) / 2;
}

function easeInCubic(progress) {
    return progress ** 3;
}

function easeOutCubic(progress) {
    return 1 - (1 - progress) ** 3;
}

function easeOutBack(progress) {
    const c1 = 1.70158;
    const c3 = c1 + 1;

    return (
        1 +
        c3 * (progress - 1) ** 3 +
        c1 * (progress - 1) ** 2
    );
}

const easingFunctions = {
    linear,
    "ease-in": easeIn,
    "ease-out": easeOut,
    "ease-in-out": easeInOut,
    "ease-in-cubic": easeInCubic,
    "ease-out-cubic": easeOutCubic,
    "ease-out-back": easeOutBack
};

console.log("\n=== 2. Easing ===");

for (const [name, easing] of Object.entries(easingFunctions)) {
    const values = [0, 0.25, 0.5, 0.75, 1].map(
        progress => easing(progress).toFixed(3)
    );

    console.log(`${name.padEnd(18)} ${values.join(", ")}`);
}


// ============================================================================
// 3. TRANSFORM MODEL
// ============================================================================

class Transform {
    constructor({
        x = 0,
        y = 0,
        scaleX = 1,
        scaleY = 1,
        rotation = 0,
        skewX = 0,
        skewY = 0
    } = {}) {
        this.x = x;
        this.y = y;
        this.scaleX = scaleX;
        this.scaleY = scaleY;
        this.rotation = rotation;
        this.skewX = skewX;
        this.skewY = skewY;
    }

    interpolate(other, progress) {
        return new Transform({
            x: lerp(this.x, other.x, progress),
            y: lerp(this.y, other.y, progress),
            scaleX: lerp(this.scaleX, other.scaleX, progress),
            scaleY: lerp(this.scaleY, other.scaleY, progress),
            rotation: lerp(this.rotation, other.rotation, progress),
            skewX: lerp(this.skewX, other.skewX, progress),
            skewY: lerp(this.skewY, other.skewY, progress)
        });
    }

    toCSS() {
        const parts = [];

        if (this.x !== 0 || this.y !== 0) {
            parts.push(
                `translate(${this.x.toFixed(2)}px, ${this.y.toFixed(2)}px)`
            );
        }

        if (this.scaleX !== 1 || this.scaleY !== 1) {
            parts.push(
                `scale(${this.scaleX.toFixed(3)}, ${this.scaleY.toFixed(3)})`
            );
        }

        if (this.rotation !== 0) {
            parts.push(`rotate(${this.rotation.toFixed(2)}deg)`);
        }

        if (this.skewX !== 0) {
            parts.push(`skewX(${this.skewX.toFixed(2)}deg)`);
        }

        if (this.skewY !== 0) {
            parts.push(`skewY(${this.skewY.toFixed(2)}deg)`);
        }

        return parts.length > 0 ? parts.join(" ") : "none";
    }
}

console.log("\n=== 3. Transforms ===");

const transforms = [
    new Transform({ x: 100 }),
    new Transform({ y: -50 }),
    new Transform({ scaleX: 1.5, scaleY: 1.5 }),
    new Transform({ rotation: 45 }),
    new Transform({ x: 50, y: 25, rotation: 30, scaleX: 1.2, scaleY: 1.2 })
];

for (const transform of transforms) {
    console.log(transform.toCSS());
}


// ============================================================================
// 4. KEYFRAME DATA
// ============================================================================

class Keyframe {
    constructor(offset, transform, opacity = 1) {
        if (offset < 0 || offset > 1) {
            throw new RangeError("Keyframe offset must be between 0 and 1.");
        }

        if (opacity < 0 || opacity > 1) {
            throw new RangeError("Opacity must be between 0 and 1.");
        }

        this.offset = offset;
        this.transform = transform;
        this.opacity = opacity;
    }
}

class Animation {
    constructor({
        name,
        duration,
        delay = 0,
        timingFunction = linear,
        iterationCount = 1,
        direction = "normal",
        fillMode = "none",
        keyframes
    }) {
        if (!name) {
            throw new Error("Animation name is required.");
        }

        if (duration <= 0) {
            throw new RangeError("Animation duration must be positive.");
        }

        if (!Array.isArray(keyframes) || keyframes.length === 0) {
            throw new Error("At least one keyframe is required.");
        }

        const validDirections = [
            "normal",
            "reverse",
            "alternate",
            "alternate-reverse"
        ];

        const validFillModes = [
            "none",
            "forwards",
            "backwards",
            "both"
        ];

        if (!validDirections.includes(direction)) {
            throw new Error(`Unsupported direction: ${direction}`);
        }

        if (!validFillModes.includes(fillMode)) {
            throw new Error(`Unsupported fill mode: ${fillMode}`);
        }

        if (
            iterationCount !== "infinite" &&
            (!Number.isFinite(iterationCount) || iterationCount <= 0)
        ) {
            throw new RangeError("Iteration count must be positive.");
        }

        this.name = name;
        this.duration = duration;
        this.delay = delay;
        this.timingFunction = timingFunction;
        this.iterationCount = iterationCount;
        this.direction = direction;
        this.fillMode = fillMode;
        this.keyframes = [...keyframes].sort(
            (a, b) => a.offset - b.offset
        );
    }

    get activeDuration() {
        if (this.iterationCount === "infinite") {
            return Infinity;
        }

        return this.duration * this.iterationCount;
    }

    get totalDuration() {
        if (this.iterationCount === "infinite") {
            return Infinity;
        }

        return this.delay + this.activeDuration;
    }

    iterationProgress(activeTime) {
        if (activeTime <= 0) {
            return {
                progress: 0,
                iteration: 0
            };
        }

        if (
            this.iterationCount !== "infinite" &&
            activeTime >= this.activeDuration
        ) {
            const finalIteration = Math.max(
                0,
                Math.ceil(this.iterationCount) - 1
            );

            return {
                progress: 1,
                iteration: finalIteration
            };
        }

        const rawIteration = activeTime / this.duration;
        const iteration = Math.floor(rawIteration);
        let progress = rawIteration - iteration;

        switch (this.direction) {
            case "normal":
                break;

            case "reverse":
                progress = 1 - progress;
                break;

            case "alternate":
                if (iteration % 2 === 1) {
                    progress = 1 - progress;
                }
                break;

            case "alternate-reverse":
                if (iteration % 2 === 0) {
                    progress = 1 - progress;
                }
                break;
        }

        return { progress, iteration };
    }

    interpolateKeyframes(progress) {
        const eased = clamp(this.timingFunction(clamp(progress)));

        if (this.keyframes.length === 1) {
            return {
                transform: this.keyframes[0].transform,
                opacity: this.keyframes[0].opacity
            };
        }

        if (eased <= this.keyframes[0].offset) {
            return {
                transform: this.keyframes[0].transform,
                opacity: this.keyframes[0].opacity
            };
        }

        const last = this.keyframes[this.keyframes.length - 1];

        if (eased >= last.offset) {
            return {
                transform: last.transform,
                opacity: last.opacity
            };
        }

        for (let index = 0; index < this.keyframes.length - 1; index++) {
            const left = this.keyframes[index];
            const right = this.keyframes[index + 1];

            if (eased >= left.offset && eased <= right.offset) {
                const interval = right.offset - left.offset;
                const localProgress =
                    interval === 0
                        ? 1
                        : (eased - left.offset) / interval;

                return {
                    transform: left.transform.interpolate(
                        right.transform,
                        localProgress
                    ),
                    opacity: lerp(
                        left.opacity,
                        right.opacity,
                        localProgress
                    )
                };
            }
        }

        throw new Error("Keyframe interpolation failed.");
    }

    stateAt(time) {
        if (time < this.delay) {
            if (this.fillMode === "backwards" || this.fillMode === "both") {
                const first = this.keyframes[0];

                return {
                    transform: first.transform,
                    opacity: first.opacity,
                    phase: "before"
                };
            }

            return {
                transform: new Transform(),
                opacity: 1,
                phase: "before"
            };
        }

        const activeTime = time - this.delay;

        if (
            this.iterationCount !== "infinite" &&
            activeTime >= this.activeDuration
        ) {
            if (this.fillMode === "forwards" || this.fillMode === "both") {
                const { progress } = this.iterationProgress(activeTime);

                const state = this.interpolateKeyframes(progress);

                return {
                    ...state,
                    phase: "after"
                };
            }

            return {
                transform: new Transform(),
                opacity: 1,
                phase: "after"
            };
        }

        const { progress, iteration } =
            this.iterationProgress(activeTime);

        return {
            ...this.interpolateKeyframes(progress),
            phase: "active",
            iteration
        };
    }
}


// ============================================================================
// 5. PRACTICAL MULTI-STAGE ANIMATION
// ============================================================================

const entranceAnimation = new Animation({
    name: "card-enter",
    duration: 1.5,
    timingFunction: easeInOut,
    fillMode: "forwards",
    keyframes: [
        new Keyframe(
            0,
            new Transform({ y: 30, scaleX: 0.95, scaleY: 0.95 }),
            0
        ),
        new Keyframe(
            0.6,
            new Transform({ y: -4, scaleX: 1.01, scaleY: 1.01 }),
            0.9
        ),
        new Keyframe(
            1,
            new Transform({ y: 0, scaleX: 1, scaleY: 1 }),
            1
        )
    ]
});

console.log("\n=== 4. Multi-stage animation ===");

for (const time of [0, 0.25, 0.5, 0.75, 1, 1.25, 1.5]) {
    const state = entranceAnimation.stateAt(time);

    console.log(
        `t=${time.toFixed(2)}s | ` +
        `phase=${state.phase.padEnd(6)} | ` +
        `transform=${state.transform.toCSS().padEnd(55)} | ` +
        `opacity=${state.opacity.toFixed(3)}`
    );
}


// ============================================================================
// 6. CSS GENERATION
// ============================================================================

function generateKeyframesCSS(animation) {
    const lines = [`@keyframes ${animation.name} {`];

    for (const keyframe of animation.keyframes) {
        lines.push(`  ${keyframe.offset * 100}% {`);
        lines.push(
            `    transform: ${keyframe.transform.toCSS()};`
        );
        lines.push(
            `    opacity: ${keyframe.opacity.toFixed(3)};`
        );
        lines.push("  }");
    }

    lines.push("}");

    return lines.join("\n");
}

console.log("\n=== 5. Generated CSS ===");
console.log(generateKeyframesCSS(entranceAnimation));


// ============================================================================
// 7. CSS ANIMATION SHORTHAND
// ============================================================================

console.log(
    `
=== 6. Animation shorthand ===

animation: card-enter 1.5s ease-in-out 0s 1 normal forwards;

Longhand properties provide the same concepts individually:

animation-name
animation-duration
animation-timing-function
animation-delay
animation-iteration-count
animation-direction
animation-fill-mode
animation-play-state
`
);


// ============================================================================
// 8. TRANSFORM ORDER
// ============================================================================

function multiply3x3(a, b) {
    const result = Array.from({ length: 3 }, () =>
        Array(3).fill(0)
    );

    for (let row = 0; row < 3; row++) {
        for (let column = 0; column < 3; column++) {
            for (let k = 0; k < 3; k++) {
                result[row][column] += a[row][k] * b[k][column];
            }
        }
    }

    return result;
}

function translationMatrix(x, y) {
    return [
        [1, 0, x],
        [0, 1, y],
        [0, 0, 1]
    ];
}

function rotationMatrix(degrees) {
    const radians = degrees * Math.PI / 180;
    const cosine = Math.cos(radians);
    const sine = Math.sin(radians);

    return [
        [cosine, -sine, 0],
        [sine, cosine, 0],
        [0, 0, 1]
    ];
}

function applyMatrix(matrix, x, y) {
    return {
        x: matrix[0][0] * x +
           matrix[0][1] * y +
           matrix[0][2],

        y: matrix[1][0] * x +
           matrix[1][1] * y +
           matrix[1][2]
    };
}

console.log("\n=== 7. Transform order ===");

const translation = translationMatrix(100, 0);
const rotation = rotationMatrix(90);

const translateThenRotate = multiply3x3(rotation, translation);
const rotateThenTranslate = multiply3x3(translation, rotation);

console.log(
    "translate then rotate:",
    applyMatrix(translateThenRotate, 1, 0)
);

console.log(
    "rotate then translate:",
    applyMatrix(rotateThenTranslate, 1, 0)
);


// ============================================================================
// 9. ITERATION DIRECTIONS
// ============================================================================

console.log("\n=== 8. Animation direction ===");

for (const direction of [
    "normal",
    "reverse",
    "alternate",
    "alternate-reverse"
]) {
    const animation = new Animation({
        name: direction,
        duration: 1,
        iterationCount: 3,
        direction,
        fillMode: "forwards",
        keyframes: [
            new Keyframe(0, new Transform({ x: 0 })),
            new Keyframe(1, new Transform({ x: 100 }))
        ]
    });

    const positions = [0, 0.5, 1, 1.5, 2, 2.5].map(
        time => animation.stateAt(time).transform.x.toFixed(1)
    );

    console.log(`${direction.padEnd(18)} ${positions.join(", ")}`);
}


// ============================================================================
// 10. NEGATIVE DELAY
// ============================================================================

console.log("\n=== 9. Negative animation delay ===");

const delayedAnimation = new Animation({
    name: "negative-delay",
    duration: 4,
    delay: -1,
    fillMode: "both",
    keyframes: [
        new Keyframe(0, new Transform({ x: 0 })),
        new Keyframe(1, new Transform({ x: 400 }))
    ]
});

for (const time of [0, 0.5, 1, 2, 3]) {
    const state = delayedAnimation.stateAt(time);

    console.log(
        `time=${time}s -> x=${state.transform.x.toFixed(1)}px`
    );
}


// ============================================================================
// 11. PLAY STATE
// ============================================================================

class AnimationController {
    constructor(animation) {
        this.animation = animation;
        this.currentTime = 0;
        this.playing = true;
    }

    tick(deltaSeconds) {
        if (deltaSeconds < 0) {
            throw new RangeError("Elapsed time cannot be negative.");
        }

        if (this.playing) {
            this.currentTime += deltaSeconds;
        }

        return this.animation.stateAt(this.currentTime);
    }

    pause() {
        this.playing = false;
    }

    play() {
        this.playing = true;
    }
}

console.log("\n=== 10. Play state ===");

const controller = new AnimationController(entranceAnimation);

for (const delta of [0.2, 0.2, 0.2]) {
    console.log(
        "running:",
        controller.tick(delta).transform.toCSS()
    );
}

controller.pause();

console.log(
    "paused:",
    controller.tick(1).transform.toCSS()
);

controller.play();

console.log(
    "resumed:",
    controller.tick(0.2).transform.toCSS()
);


// ============================================================================
// 12. STEPS() TIMING
// ============================================================================

function steps(progress, count) {
    if (!Number.isInteger(count) || count <= 0) {
        throw new RangeError("steps() requires a positive integer.");
    }

    return Math.min(count, Math.floor(progress * count)) / count;
}

console.log("\n=== 11. steps() timing ===");

for (const count of [2, 4, 8]) {
    const values = [];

    for (let index = 0; index <= 8; index++) {
        values.push(
            steps(index / 8, count).toFixed(3)
        );
    }

    console.log(`steps(${count}): ${values.join(", ")}`);
}


// ============================================================================
// 13. CUBIC-BEZIER
// ============================================================================

function cubicBezierScalar(p0, p1, p2, p3, t) {
    const inverse = 1 - t;

    return (
        inverse ** 3 * p0 +
        3 * inverse ** 2 * t * p1 +
        3 * inverse * t ** 2 * p2 +
        t ** 3 * p3
    );
}

console.log("\n=== 12. Cubic Bezier ===");

for (const t of [0, 0.25, 0.5, 0.75, 1]) {
    console.log(
        `t=${t.toFixed(2)} -> ` +
        `${cubicBezierScalar(0, 0.25, 0.75, 1, t).toFixed(3)}`
    );
}


// ============================================================================
// 14. PROPERTY PERFORMANCE MODEL
// ============================================================================

const propertyClassification = {
    transform: "compositor-friendly",
    opacity: "compositor-friendly",
    "background-color": "paint-related",
    "box-shadow": "paint-related",
    width: "layout-related",
    height: "layout-related",
    left: "layout-related",
    top: "layout-related",
    margin: "layout-related",
    padding: "layout-related"
};

const estimatedCosts = {
    "compositor-friendly": {
        layout: 0.2,
        paint: 0.3,
        composite: 1.5
    },
    "paint-related": {
        layout: 0.4,
        paint: 6,
        composite: 1.5
    },
    "layout-related": {
        layout: 7,
        paint: 6,
        composite: 1.5
    }
};

function simulatePerformance(property, frameCount = 120) {
    const category =
        propertyClassification[property] || "paint-related";

    const costs = estimatedCosts[category];
    const samples = [];

    for (let frame = 0; frame < frameCount; frame++) {
        const variation =
            Math.sin(frame / 5) * 0.3;

        const frameTime =
            costs.layout +
            costs.paint +
            costs.composite +
            variation;

        samples.push({
            frameTime,
            layout: costs.layout,
            paint: costs.paint,
            composite: costs.composite
        });
    }

    const average =
        samples.reduce(
            (sum, sample) => sum + sample.frameTime,
            0
        ) / samples.length;

    const droppedFrames =
        samples.filter(sample => sample.frameTime > 16.67).length;

    return {
        property,
        category,
        averageFrameTime: average,
        droppedFramePercentage:
            droppedFrames / samples.length * 100
    };
}

console.log("\n=== 13. Performance model ===");

for (const property of [
    "transform",
    "opacity",
    "background-color",
    "box-shadow",
    "width",
    "left"
]) {
    const result = simulatePerformance(property);

    console.log(
        `${property.padEnd(18)} ` +
        `category=${result.category.padEnd(20)} ` +
        `avg=${result.averageFrameTime.toFixed(2)}ms ` +
        `slow=${result.droppedFramePercentage.toFixed(1)}%`
    );
}


// ============================================================================
// 15. FRAME RATE BUDGETS
// ============================================================================

function frameBudget(refreshRate) {
    if (refreshRate <= 0) {
        throw new RangeError("Refresh rate must be positive.");
    }

    return 1000 / refreshRate;
}

console.log("\n=== 14. Frame budgets ===");

for (const refreshRate of [60, 90, 120, 144, 240]) {
    console.log(
        `${refreshRate}Hz -> ` +
        `${frameBudget(refreshRate).toFixed(3)}ms/frame`
    );
}


// ============================================================================
// 16. BROWSER-SIDE REDUCED MOTION
// ============================================================================

function detectReducedMotion(environment = globalThis) {
    if (
        !environment.matchMedia ||
        typeof environment.matchMedia !== "function"
    ) {
        return false;
    }

    return environment
        .matchMedia("(prefers-reduced-motion: reduce)")
        .matches;
}

console.log("\n=== 15. Reduced motion ===");

console.log(
    "Current environment supports reduced-motion detection:",
    typeof globalThis.matchMedia === "function"
);

console.log(
    "Detected reduced motion:",
    detectReducedMotion()
);


// ============================================================================
// 17. PRACTICAL DOM EXAMPLE
// ============================================================================

function createAnimationStyles() {
    return `
@keyframes card-enter {
    from {
        opacity: 0;
        transform: translateY(24px) scale(0.98);
    }

    to {
        opacity: 1;
        transform: translateY(0) scale(1);
    }
}

.card {
    animation:
        card-enter 700ms
        cubic-bezier(0.22, 1, 0.36, 1)
        forwards;
}

@media (prefers-reduced-motion: reduce) {
    .card {
        animation: none;
        opacity: 1;
        transform: none;
    }
}
`;
}

console.log("\n=== 16. Browser CSS ===");
console.log(createAnimationStyles());


// ============================================================================
// 18. EVENT-DRIVEN BROWSER EXAMPLE
// ============================================================================

function browserInteractionExample() {
    if (
        typeof document === "undefined" ||
        typeof window === "undefined"
    ) {
        return {
            supported: false,
            reason: "No browser DOM is available in this runtime."
        };
    }

    const element = document.querySelector(".animated-card");

    if (!element) {
        return {
            supported: false,
            reason: "Expected .animated-card was not found."
        };
    }

    element.addEventListener("animationstart", event => {
        console.log(
            `Animation started: ${event.animationName}`
        );
    });

    element.addEventListener("animationend", event => {
        console.log(
            `Animation ended: ${event.animationName}`
        );
    });

    element.addEventListener("animationcancel", event => {
        console.log(
            `Animation cancelled: ${event.animationName}`
        );
    });

    return {
        supported: true
    };
}

console.log("\n=== 17. Browser event handling ===");
console.log(browserInteractionExample());


// ============================================================================
// 19. WEB ANIMATIONS API COMPARISON
// ============================================================================

function webAnimationsApiExample() {
    if (
        typeof document === "undefined" ||
        typeof Element === "undefined"
    ) {
        return {
            supported: false,
            reason: "The Web Animations API example requires a browser."
        };
    }

    const element = document.querySelector(".animated-card");

    if (!element || typeof element.animate !== "function") {
        return {
            supported: false,
            reason: "Element.animate() is unavailable."
        };
    }

    const animation = element.animate(
        [
            {
                opacity: 0,
                transform: "translateY(24px)"
            },
            {
                opacity: 1,
                transform: "translateY(0)"
            }
        ],
        {
            duration: 700,
            easing: "cubic-bezier(0.22, 1, 0.36, 1)",
            fill: "forwards"
        }
    );

    return {
        supported: true,
        animation
    };
}

console.log("\n=== 18. Web Animations API ===");
console.log(webAnimationsApiExample().supported);


// ============================================================================
// 20. PERFORMANCE OBSERVATION MODEL
// ============================================================================

class FrameMonitor {
    constructor(targetFrameRate = 60) {
        if (targetFrameRate <= 0) {
            throw new RangeError("Frame rate must be positive.");
        }

        this.targetFrameRate = targetFrameRate;
        this.budget = 1000 / targetFrameRate;
        this.samples = [];
    }

    record(frameDurationMs) {
        if (!Number.isFinite(frameDurationMs) || frameDurationMs < 0) {
            throw new RangeError("Invalid frame duration.");
        }

        this.samples.push(frameDurationMs);
    }

    report() {
        if (this.samples.length === 0) {
            return {
                frameCount: 0,
                average: 0,
                slowPercentage: 0
            };
        }

        const average =
            this.samples.reduce(
                (sum, value) => sum + value,
                0
            ) / this.samples.length;

        const slowFrames =
            this.samples.filter(
                value => value > this.budget
            ).length;

        return {
            frameCount: this.samples.length,
            average,
            slowPercentage:
                slowFrames / this.samples.length * 100
        };
    }
}

console.log("\n=== 19. Frame monitoring ===");

const monitor = new FrameMonitor(60);

for (const frameDuration of [
    8, 10, 12, 14, 15, 16, 17, 20, 9, 11
]) {
    monitor.record(frameDuration);
}

console.log(monitor.report());


// ============================================================================
// 21. CSS PROPERTY VALIDATION
// ============================================================================

function validateAnimationConfiguration(configuration) {
    const errors = [];

    if (!configuration.name) {
        errors.push("Animation name is required.");
    }

    if (
        !Number.isFinite(configuration.duration) ||
        configuration.duration <= 0
    ) {
        errors.push("Duration must be a positive finite number.");
    }

    if (
        configuration.iterationCount !== "infinite" &&
        (
            !Number.isFinite(configuration.iterationCount) ||
            configuration.iterationCount <= 0
        )
    ) {
        errors.push("Iteration count must be positive or infinite.");
    }

    const directions = [
        "normal",
        "reverse",
        "alternate",
        "alternate-reverse"
    ];

    if (!directions.includes(configuration.direction)) {
        errors.push("Invalid animation direction.");
    }

    const fillModes = [
        "none",
        "forwards",
        "backwards",
        "both"
    ];

    if (!fillModes.includes(configuration.fillMode)) {
        errors.push("Invalid fill mode.");
    }

    return {
        valid: errors.length === 0,
        errors
    };
}

console.log("\n=== 20. Configuration validation ===");

console.log(
    validateAnimationConfiguration({
        name: "pulse",
        duration: 1000,
        iterationCount: "infinite",
        direction: "alternate",
        fillMode: "both"
    })
);

console.log(
    validateAnimationConfiguration({
        name: "",
        duration: -10,
        iterationCount: 0,
        direction: "invalid",
        fillMode: "invalid"
    })
);


// ============================================================================
// 22. ACCESSIBILITY POLICY
// ============================================================================

class MotionPolicy {
    constructor(prefersReducedMotion) {
        this.prefersReducedMotion = Boolean(
            prefersReducedMotion
        );
    }

    animationSettings(normalSettings) {
        if (!this.prefersReducedMotion) {
            return normalSettings;
        }

        return {
            ...normalSettings,
            duration: 1,
            iterationCount: 1,
            animation: "none"
        };
    }
}

console.log("\n=== 21. Motion policy ===");

const normalSettings = {
    duration: 1200,
    iterationCount: "infinite",
    animation: "float"
};

console.log(
    "Normal:",
    new MotionPolicy(false).animationSettings(normalSettings)
);

console.log(
    "Reduced:",
    new MotionPolicy(true).animationSettings(normalSettings)
);


// ============================================================================
// 23. MULTIPLE ANIMATION CONCEPT
// ============================================================================

console.log(
    `
=== 22. Multiple animations ===

CSS can run multiple animation timelines:

animation:
    move 2s ease-in-out infinite,
    fade 1s linear forwards;

The timelines can target different properties. When multiple animations
affect the same property, the cascade and animation-composition rules become
important.
`
);


// ============================================================================
// 24. TRANSFORM PERFORMANCE RECOMMENDATIONS
// ============================================================================

const performanceGuidelines = [
    {
        property: "transform",
        typicalUse: "Movement, scaling, rotation",
        concern: "Verify actual compositor behavior."
    },
    {
        property: "opacity",
        typicalUse: "Fading",
        concern: "Watch large numbers of simultaneously animated elements."
    },
    {
        property: "width",
        typicalUse: "Layout resizing",
        concern: "Can trigger layout and paint work."
    },
    {
        property: "left",
        typicalUse: "Positioning",
        concern: "Prefer transform for purely visual movement when suitable."
    },
    {
        property: "box-shadow",
        typicalUse: "Depth and emphasis",
        concern: "Large blurred shadows can be paint-intensive."
    }
];

console.log("\n=== 23. Property guidance ===");

for (const guideline of performanceGuidelines) {
    console.log(
        `${guideline.property}: ` +
        `${guideline.typicalUse}. ` +
        `${guideline.concern}`
    );
}


// ============================================================================
// 25. TESTS
// ============================================================================

function assert(condition, message) {
    if (!condition) {
        throw new Error(`Assertion failed: ${message}`);
    }
}

console.log("\n=== 24. Automated checks ===");

const testAnimation = new Animation({
    name: "test",
    duration: 1,
    keyframes: [
        new Keyframe(0, new Transform({ x: 0 })),
        new Keyframe(1, new Transform({ x: 100 }))
    ]
});

assert(
    testAnimation.stateAt(0).transform.x === 0,
    "Animation should start at x=0."
);

assert(
    testAnimation.stateAt(1).transform.x === 100,
    "Animation should end at x=100."
);

const midpoint = testAnimation.stateAt(0.5).transform.x;

assert(
    midpoint >= 0 && midpoint <= 100,
    "Midpoint should be inside the animation interval."
);

const reverseAnimation = new Animation({
    name: "reverse",
    duration: 1,
    direction: "reverse",
    keyframes: [
        new Keyframe(0, new Transform({ x: 0 })),
        new Keyframe(1, new Transform({ x: 100 }))
    ]
});

assert(
    reverseAnimation.stateAt(0).transform.x === 100,
    "Reverse animation should begin at the final keyframe."
);

const interpolated = new Transform({ x: 0 }).interpolate(
    new Transform({ x: 100 }),
    0.5
);

assert(
    interpolated.x === 50,
    "Transform interpolation should produce x=50."
);

console.log("All JavaScript animation checks passed.");


// ============================================================================
// 26. COMMON DESIGN ERRORS
// ============================================================================

console.log(
    `
=== 25. Common errors ===

1. Animating layout properties when transform would achieve the same visual
   result.
2. Applying will-change to every animated element.
3. Running infinite animations that provide no functional value.
4. Ignoring prefers-reduced-motion.
5. Using overly long or overly short durations.
6. Selecting an easing function without considering the interaction.
7. Forgetting animation-fill-mode when the final state must persist.
8. Creating multiple animations that compete over the same property.
9. Measuring only desktop performance.
10. Assuming transform is automatically cheap in every situation.
`
);


// ============================================================================
// 27. FINAL REFERENCE
// ============================================================================

const reference = {
    "@keyframes": "Defines animation stages.",
    "animation-name": "Selects a keyframe sequence.",
    "animation-duration": "Defines one iteration's duration.",
    "animation-timing-function": "Controls temporal interpolation.",
    "animation-delay": "Delays the active timeline.",
    "animation-iteration-count": "Defines repetitions.",
    "animation-direction": "Controls iteration direction.",
    "animation-fill-mode": "Controls styles before and after activity.",
    "animation-play-state": "Controls running or paused state.",
    "transform": "Changes visual geometry using transform functions.",
    "opacity": "Controls transparency.",
    "will-change": "Hints at expected future property changes.",
    "prefers-reduced-motion": "Represents a user motion preference."
};

console.log("\n=== 26. Reference ===");

for (const [term, description] of Object.entries(reference)) {
    console.log(`${term.padEnd(30)} ${description}`);
}
