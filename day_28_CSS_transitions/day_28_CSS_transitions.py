"""
CSS Transitions — Comprehensive Study and Executable Demonstrations

This file teaches CSS transitions from beginner to advanced concepts through
self-contained examples, generated CSS, validation, timing-function simulation,
accessibility considerations, and a small interactive UI model.

The script does not require third-party packages.
"""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from math import ceil
from typing import Callable, Iterable


# ============================================================================
# 1. FUNDAMENTALS
# ============================================================================

print("=" * 78)
print("CSS TRANSITIONS: FUNDAMENTALS TO ADVANCED CONCEPTS")
print("=" * 78)

print(
    """
A CSS transition creates a smooth interpolation between two CSS states.

Typical sequence:

    Default state
        |
        | user interaction or state change
        v
    Changed state
        |
        | transition property controls interpolation
        v
    Smooth visual change

A transition commonly consists of:

    transition-property
    transition-duration
    transition-timing-function
    transition-delay

The shorthand form is:

    transition: property duration timing-function delay;

Example:

    transition: background-color 300ms ease 0ms;

Important distinction:

    transition = how a property changes between states
    animation  = a potentially multi-step timeline controlled by keyframes

A transition normally requires a property to have a starting value and an
ending value. CSS calculates intermediate values during the transition.
"""
)


# ============================================================================
# 2. BASIC CSS GENERATION
# ============================================================================

def transition_rule(
    selector: str,
    property_name: str,
    duration_ms: int,
    timing_function: str = "ease",
    delay_ms: int = 0,
) -> str:
    """Generate a basic CSS rule containing a transition and changed state."""
    if duration_ms < 0:
        raise ValueError("Transition duration cannot be negative.")
    if delay_ms < 0:
        raise ValueError("Transition delay cannot be negative.")
    if not selector.strip():
        raise ValueError("Selector cannot be empty.")
    if not property_name.strip():
        raise ValueError("Property name cannot be empty.")

    return (
        f"{selector} {{\n"
        f"  transition: {property_name} {duration_ms}ms "
        f"{timing_function} {delay_ms}ms;\n"
        f"}}"
    )


print("\n--- Basic transition rule ---")
print(
    transition_rule(
        ".button",
        "background-color",
        300,
        "ease",
        0,
    )
)

print(
    """
The browser does not need JavaScript for a normal hover transition.

CSS:

    .button {
        background-color: steelblue;
        transition: background-color 300ms ease;
    }

    .button:hover {
        background-color: royalblue;
    }

The hover selector changes the state. The transition determines how the
browser moves from the old value to the new value.
"""
)


# ============================================================================
# 3. TRANSITION COMPONENTS
# ============================================================================

@dataclass(frozen=True)
class Transition:
    """Represent the four conceptual components of a CSS transition."""

    property_name: str
    duration_ms: int
    timing_function: str = "ease"
    delay_ms: int = 0

    def __post_init__(self) -> None:
        if self.duration_ms < 0:
            raise ValueError("duration_ms must be >= 0")
        if self.delay_ms < 0:
            raise ValueError("delay_ms must be >= 0")
        if not self.property_name:
            raise ValueError("property_name cannot be empty")

    def shorthand(self) -> str:
        """Return CSS transition shorthand."""
        return (
            f"{self.property_name} {self.duration_ms}ms "
            f"{self.timing_function} {self.delay_ms}ms"
        )

    @property
    def total_time_ms(self) -> int:
        """Return delay + active transition duration."""
        return self.delay_ms + self.duration_ms


basic_transition = Transition(
    property_name="transform",
    duration_ms=250,
    timing_function="ease-out",
    delay_ms=0,
)

print("\n--- Transition object ---")
print("Property:", basic_transition.property_name)
print("Duration:", basic_transition.duration_ms, "ms")
print("Timing function:", basic_transition.timing_function)
print("Delay:", basic_transition.delay_ms, "ms")
print("Shorthand:", basic_transition.shorthand())
print("Total elapsed time:", basic_transition.total_time_ms, "ms")


# ============================================================================
# 4. TRANSITION-PROPERTY
# ============================================================================

print(
    """
--- transition-property ---

transition-property identifies which CSS property or properties should
transition.

Examples:

    transition-property: opacity;
    transition-property: transform;
    transition-property: background-color;
    transition-property: opacity, transform;

Using `all` is possible:

    transition: all 250ms ease;

But `all` can make behavior harder to reason about and can accidentally
animate properties that were not intended to move. Explicit properties are
usually easier to maintain.

Good:

    transition: transform 200ms ease, opacity 200ms ease;

Less controlled:

    transition: all 200ms ease;
"""
)


# ============================================================================
# 5. TRANSITION-DURATION
# ============================================================================

def duration_category(duration_ms: int) -> str:
    """Classify a transition duration for educational purposes."""
    if duration_ms < 0:
        raise ValueError("Duration cannot be negative.")
    if duration_ms == 0:
        return "instant"
    if duration_ms < 150:
        return "very fast"
    if duration_ms <= 300:
        return "short"
    if duration_ms <= 700:
        return "moderate"
    if duration_ms <= 1200:
        return "long"
    return "very long"


print("\n--- Duration categories ---")
for duration in (0, 100, 200, 300, 500, 1000, 1500):
    print(f"{duration:>4} ms -> {duration_category(duration)}")

print(
    """
Duration is normally expressed using:

    ms  milliseconds
    s   seconds

Examples:

    transition-duration: 200ms;
    transition-duration: 0.2s;

200ms and 0.2s represent the same duration.

A duration of zero disables the visible interpolation, although state changes
still occur.
"""
)


# ============================================================================
# 6. DELAYS
# ============================================================================

def transition_timeline(duration_ms: int, delay_ms: int, samples: int = 6) -> list[tuple[int, float]]:
    """
    Produce a simple timeline.

    Progress remains 0 during the delay and reaches 1 at the end of the
    transition. This models the conceptual timeline, not browser rendering.
    """
    if duration_ms < 0 or delay_ms < 0:
        raise ValueError("Duration and delay must be non-negative.")
    if samples < 2:
        raise ValueError("At least two samples are required.")

    total = delay_ms + duration_ms
    if total == 0:
        return [(0, 1.0)]

    result: list[tuple[int, float]] = []

    for index in range(samples):
        elapsed = round(total * index / (samples - 1))

        if elapsed <= delay_ms:
            progress = 0.0
        else:
            progress = min(
                1.0,
                (elapsed - delay_ms) / duration_ms if duration_ms else 1.0,
            )

        result.append((elapsed, progress))

    return result


print("\n--- Delay timeline ---")
for elapsed, progress in transition_timeline(400, 200):
    print(f"elapsed={elapsed:>4}ms | progress={progress:.2f}")

print(
    """
A delay postpones the beginning of the transition.

    transition: opacity 400ms ease 200ms;

Conceptually:

    0ms ---------------- 200ms |---------------- 600ms
                 delay          transition

The delay is not part of the interpolation itself. It is a waiting period
before the active transition starts.
"""
)


# ============================================================================
# 7. TIMING FUNCTIONS
# ============================================================================

TimingFunction = Callable[[float], float]


def clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    """Clamp a value into an inclusive interval."""
    return max(minimum, min(maximum, value))


def linear(t: float) -> float:
    """Linear timing: constant rate."""
    return clamp(t)


def ease_in(t: float) -> float:
    """Educational cubic ease-in approximation."""
    t = clamp(t)
    return t * t * t


def ease_out(t: float) -> float:
    """Educational cubic ease-out approximation."""
    t = clamp(t)
    return 1 - (1 - t) ** 3


def ease_in_out(t: float) -> float:
    """Educational cubic ease-in-out approximation."""
    t = clamp(t)

    if t < 0.5:
        return 4 * t * t * t

    return 1 - ((-2 * t + 2) ** 3) / 2


def cubic_bezier(
    p1x: float,
    p1y: float,
    p2x: float,
    p2y: float,
) -> TimingFunction:
    """
    Create an approximate cubic-bezier timing function.

    CSS cubic-bezier() maps time progress through x(t) to output progress
    y(t). Because x is not generally equal to t, we numerically invert x(t)
    using binary search.
    """

    values = (p1x, p1y, p2x, p2y)

    if not all(0 <= value <= 1 for value in values):
        raise ValueError(
            "This educational implementation expects control points in [0, 1]."
        )

    def bezier_coordinate(t: float, a1: float, a2: float) -> float:
        return (
            3 * (1 - t) ** 2 * t * a1
            + 3 * (1 - t) * t ** 2 * a2
            + t ** 3
        )

    def timing_function(progress: float) -> float:
        progress = clamp(progress)

        low = 0.0
        high = 1.0

        # Invert x(t) so that the resulting y represents the progress at
        # the requested elapsed-time fraction.
        for _ in range(30):
            middle = (low + high) / 2
            x = bezier_coordinate(middle, p1x, p2x)

            if x < progress:
                low = middle
            else:
                high = middle

        parameter = (low + high) / 2
        return bezier_coordinate(parameter, p1y, p2y)

    return timing_function


TIMING_FUNCTIONS: dict[str, TimingFunction] = {
    "linear": linear,
    "ease-in": ease_in,
    "ease-out": ease_out,
    "ease-in-out": ease_in_out,
    "ease": cubic_bezier(0.25, 0.1, 0.25, 1.0),
}


print("\n--- Timing-function comparison ---")
sample_points = [0.0, 0.25, 0.5, 0.75, 1.0]

for name, function in TIMING_FUNCTIONS.items():
    values = [round(function(point), 3) for point in sample_points]
    print(f"{name:>12}: {values}")

print(
    """
Timing functions change the rate of interpolation.

Common functions:

    linear
    ease
    ease-in
    ease-out
    ease-in-out

Cubic Bézier functions use:

    cubic-bezier(x1, y1, x2, y2)

The x coordinates describe timing and the y coordinates describe output
progress. CSS constrains the x control points to the interval 0..1, while
the y values can technically extend outside that interval to produce
overshooting behavior.

Examples:

    cubic-bezier(0.25, 0.1, 0.25, 1)
    cubic-bezier(0.42, 0, 1, 1)
    cubic-bezier(0, 0, 0.58, 1)

The named `ease` function corresponds to a predefined cubic Bézier curve.
"""
)


# ============================================================================
# 8. STEP TIMING FUNCTIONS
# ============================================================================

def steps(number_of_steps: int, t: float, position: str = "end") -> float:
    """
    Approximate CSS steps() timing.

    `end` changes at the end of each step.
    `start` changes at the beginning of each step.
    """
    if number_of_steps <= 0:
        raise ValueError("number_of_steps must be positive.")

    t = clamp(t)

    if position == "end":
        return min(number_of_steps - 1, int(t * number_of_steps)) / (
            number_of_steps - 1
        ) if number_of_steps > 1 else 1.0

    if position == "start":
        return min(number_of_steps, int(t * number_of_steps) + 1) / number_of_steps

    raise ValueError("position must be 'start' or 'end'")


print("\n--- steps() timing ---")
for position in ("start", "end"):
    values = [round(steps(5, t, position), 3) for t in sample_points]
    print(position, values)

print(
    """
`steps()` is useful when a continuous visual change is undesirable.

Example:

    transition: width 1s steps(5, end);

Instead of many tiny interpolations, the value changes in discrete stages.

This can be useful for sprite-like interfaces, progress indicators, or
intentional stepped visual effects.
"""
)


# ============================================================================
# 9. INTERPOLATING NUMERIC VALUES
# ============================================================================

def interpolate(start: float, end: float, progress: float) -> float:
    """Linearly interpolate between two numeric values."""
    progress = clamp(progress)
    return start + (end - start) * progress


def demonstrate_property(
    property_name: str,
    start: float,
    end: float,
    timing_function: TimingFunction,
    samples: int = 11,
) -> list[tuple[float, float]]:
    """Return conceptual property values across a transition."""
    if samples < 2:
        raise ValueError("samples must be >= 2")

    output = []

    for index in range(samples):
        time_progress = index / (samples - 1)
        visual_progress = timing_function(time_progress)
        value = interpolate(start, end, visual_progress)
        output.append((time_progress, value))

    return output


print("\n--- Transform-like numeric interpolation ---")
for time_progress, value in demonstrate_property(
    "scale",
    1.0,
    1.2,
    TIMING_FUNCTIONS["ease-out"],
):
    print(f"time={time_progress:.2f} | scale={value:.3f}")


# ============================================================================
# 10. WHICH PROPERTIES TRANSITION WELL?
# ============================================================================

TRANSITION_FRIENDLY_PROPERTIES = {
    "opacity": "Numeric interpolation; commonly used for fades.",
    "transform": "Transforms such as translate, rotate, scale, and skew.",
    "color": "Color interpolation between compatible color values.",
    "background-color": "Useful for hover and state changes.",
    "border-color": "Useful for focus and validation states.",
    "box-shadow": "Can transition but may be more expensive visually.",
    "width": "Can transition when values are interpolable, but layout can change.",
    "height": "Can transition with explicit interpolable values.",
}

print("\n--- Commonly transitioned properties ---")
for property_name, explanation in TRANSITION_FRIENDLY_PROPERTIES.items():
    print(f"{property_name:>16}: {explanation}")

print(
    """
Properties related to visual compositing are often preferred for smooth UI
motion:

    transform
    opacity

Changing layout-related properties such as width, height, top, left, margin,
or padding may trigger layout work. That does not mean they can never be
transitioned, but their performance characteristics differ.

A transition does not make an inherently expensive property cheap.
"""
)


# ============================================================================
# 11. TRANSFORM COMPOSITION
# ============================================================================

@dataclass
class CardState:
    """Simple model of a card's interactive visual state."""

    scale: float = 1.0
    translate_y: float = 0.0
    rotation: float = 0.0
    opacity: float = 1.0

    def to_css(self) -> str:
        return (
            f"transform: translateY({self.translate_y:.1f}px) "
            f"scale({self.scale:.3f}) rotate({self.rotation:.1f}deg); "
            f"opacity: {self.opacity:.3f};"
        )


normal_card = CardState()
hover_card = CardState(
    scale=1.03,
    translate_y=-4,
    rotation=0.2,
    opacity=1.0,
)

print("\n--- Interactive card states ---")
print("Normal:", normal_card.to_css())
print("Hover :", hover_card.to_css())

print(
    """
Transforms can combine multiple operations:

    transform:
        translateY(-4px)
        scale(1.03)
        rotate(0.2deg);

In actual CSS these are normally written on one declaration:

    transform: translateY(-4px) scale(1.03) rotate(0.2deg);

The order of transform functions matters because transformations compose
mathematically and are not generally commutative.
"""
)


# ============================================================================
# 12. MULTIPLE PROPERTIES
# ============================================================================

def build_multi_transition(
    transitions: Iterable[Transition],
) -> str:
    """Create CSS shorthand for several transitioned properties."""
    transition_list = list(transitions)

    if not transition_list:
        raise ValueError("At least one transition is required.")

    return ", ".join(item.shorthand() for item in transition_list)


multi_transition = build_multi_transition(
    [
        Transition("transform", 250, "ease-out"),
        Transition("opacity", 200, "linear"),
        Transition("box-shadow", 300, "ease"),
    ]
)

print("\n--- Multiple transitions ---")
print("transition:", multi_transition)

print(
    """
Different properties can have different durations and timing functions:

    transition:
        transform 250ms ease-out,
        opacity 200ms linear,
        box-shadow 300ms ease;

A comma separates transition definitions.

The number of transition-property, duration, timing-function, and delay
values can interact through CSS list matching rules. Understanding those
lists is important when using the longhand properties separately.
"""
)


# ============================================================================
# 13. HOVER STATES
# ============================================================================

def hover_button_css() -> str:
    """Return a complete hover button example."""
    return """\
.button {
    background: #202938;
    color: white;
    transform: translateY(0);
    transition:
        background-color 200ms ease,
        transform 200ms ease,
        box-shadow 200ms ease;
}

.button:hover {
    background: #334155;
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgb(0 0 0 / 0.20);
}
"""


print("\n--- Hover example ---")
print(hover_button_css())

print(
    """
Hover is a pointer state, not a general interaction model.

A common accessibility mistake is designing an important interaction so that
it is available only through :hover. Keyboard users and touch users may not
receive the same interaction.

For controls, consider:

    :hover
    :focus
    :focus-visible
    :active

The transition can be shared across these states.
"""
)


# ============================================================================
# 14. FOCUS AND ACTIVE STATES
# ============================================================================

FOCUS_BUTTON_CSS = """\
.button {
    transition:
        transform 160ms ease-out,
        background-color 160ms ease-out,
        box-shadow 160ms ease-out;
}

.button:hover {
    transform: translateY(-2px);
}

.button:focus-visible {
    outline: 3px solid currentColor;
    outline-offset: 3px;
}

.button:active {
    transform: translateY(0) scale(0.98);
}
"""

print("\n--- Accessible interaction states ---")
print(FOCUS_BUTTON_CSS)


# ============================================================================
# 15. REDUCED MOTION
# ============================================================================

REDUCED_MOTION_CSS = """\
@media (prefers-reduced-motion: reduce) {
    *,
    *::before,
    *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
        scroll-behavior: auto !important;
    }
}
"""

print("\n--- Reduced-motion preference ---")
print(REDUCED_MOTION_CSS)

print(
    """
Respecting prefers-reduced-motion allows users whose operating-system
settings request reduced motion to receive a substantially reduced
transition effect.

This is especially important when an interface contains:

    large movement
    repeated motion
    parallax-like effects
    strong zooming
    rapid transitions
"""
)


# ============================================================================
# 16. TRANSITIONS AND DISPLAY / VISIBILITY
# ============================================================================

print(
    """
--- display, visibility, and opacity ---

A frequent misconception is:

    transition: display 300ms ease;

Traditional CSS `display: none` -> `display: block` changes do not behave like
ordinary numeric interpolation.

A common fading pattern historically uses opacity:

    .panel {
        opacity: 0;
        visibility: hidden;
        transition:
            opacity 200ms ease,
            visibility 0s linear 200ms;
    }

    .panel.is-open {
        opacity: 1;
        visibility: visible;
        transition:
            opacity 200ms ease,
            visibility 0s linear 0s;
    }

The exact interaction depends on the browser's support for newer discrete
transition capabilities and the desired accessibility behavior.

Opacity alone does not automatically make an element non-interactive.
An invisible element can still occupy space and potentially remain
interactive depending on the implementation.
"""
)


# ============================================================================
# 17. TRANSITIONABLE VS DISCRETE BEHAVIOR
# ============================================================================

print(
    """
CSS property changes fall into different interpolation behaviors.

Common smoothly interpolated examples:

    opacity
    transform
    many numeric properties
    many color properties

Discrete state examples include values such as:

    display: none/block

Modern CSS has expanded support for transitioning some discrete properties
using mechanisms such as `transition-behavior: allow-discrete`, but browser
support and the exact property behavior must be considered when targeting
real production environments.

A transition should therefore never be assumed to work simply because a
property appears in a transition declaration.
"""
)


# ============================================================================
# 18. NEGATIVE DELAYS
# ============================================================================

print(
    """
--- Negative delays ---

CSS permits negative transition delays.

Example:

    transition: transform 500ms ease -200ms;

A negative delay means the transition behaves as though it had already been
running for part of its duration when the state change occurs.

This is an advanced technique and should be used carefully because it can
make interaction timing less intuitive.
"""
)


# ============================================================================
# 19. CASCADING AND INHERITANCE
# ============================================================================

print(
    """
--- Cascading considerations ---

`transition` is not inherited in the normal sense.

For example:

    .parent {
        transition: opacity 300ms ease;
    }

does not automatically cause a child element's opacity changes to use the
same transition.

The transition declaration belongs to the element whose property is
changing.

Selectors, specificity, source order, media queries, and CSS cascade rules
can all determine which declaration is active.
"""
)


# ============================================================================
# 20. TRANSITION-END EVENT CONCEPT
# ============================================================================

def transition_event_sequence(
    property_name: str,
    duration_ms: int,
    delay_ms: int,
) -> list[str]:
    """Model the conceptual JavaScript transition lifecycle."""
    if duration_ms < 0 or delay_ms < 0:
        raise ValueError("Times cannot be negative.")

    if duration_ms == 0:
        return [
            "style/state change",
            "no visible interpolation",
        ]

    return [
        "style/state change",
        f"wait {delay_ms}ms",
        f"interpolate {property_name} for {duration_ms}ms",
        "transitionend event may fire",
    ]


print("\n--- Conceptual transition lifecycle ---")
for event in transition_event_sequence("opacity", 300, 100):
    print("*", event)

print(
    """
JavaScript can observe transition lifecycle events:

    transitionrun
    transitionstart
    transitioncancel
    transitionend

For production code, event-driven logic should not assume that a transition
always completes. It can be interrupted by a new state, removed from the
DOM, or otherwise canceled.
"""
)


# ============================================================================
# 21. VALIDATION
# ============================================================================

VALID_CSS_PROPERTIES = {
    "opacity",
    "transform",
    "color",
    "background-color",
    "border-color",
    "box-shadow",
    "width",
    "height",
    "filter",
    "visibility",
}


def validate_transition(transition: Transition) -> list[str]:
    """Return educational warnings for a transition configuration."""
    warnings: list[str] = []

    if transition.property_name not in VALID_CSS_PROPERTIES:
        warnings.append(
            f"Property '{transition.property_name}' is not in this "
            "educational common-property list."
        )

    if transition.duration_ms > 1000:
        warnings.append(
            "Duration exceeds one second; verify that the long motion "
            "does not make interaction feel slow."
        )

    if transition.property_name in {"width", "height"}:
        warnings.append(
            "Layout dimensions may cause layout recalculation; test performance."
        )

    if transition.property_name == "box-shadow":
        warnings.append(
            "Large or complex shadows can increase rendering cost."
        )

    return warnings


print("\n--- Transition validation ---")
test_transition = Transition("width", 1200, "ease", 100)

for warning in validate_transition(test_transition):
    print("WARNING:", warning)


# ============================================================================
# 22. COMMON MISTAKES
# ============================================================================

COMMON_MISTAKES = {
    "No starting value": "A transition needs meaningful before/after states.",
    "transition on :hover only": (
        "The reverse interaction can become abrupt when the declaration "
        "is not present on the base element."
    ),
    "transition: all": (
        "It can unintentionally transition properties and make maintenance "
        "more difficult."
    ),
    "huge duration": (
        "Long transitions can delay feedback and make controls feel slow."
    ),
    "hover-only interaction": (
        "Touch and keyboard users need equivalent interaction paths."
    ),
    "transform overwrite": (
        "A new transform declaration replaces the previous transform list "
        "unless the transformations are combined."
    ),
    "ignoring reduced motion": (
        "Users may explicitly request less movement."
    ),
    "assuming every property interpolates": (
        "CSS properties have different interpolation and discrete behaviors."
    ),
}

print("\n--- Common mistakes ---")
for mistake, explanation in COMMON_MISTAKES.items():
    print(f"\n{mistake}:")
    print(" ", explanation)


# ============================================================================
# 23. TRANSFORM OVERWRITE DEMONSTRATION
# ============================================================================

print(
    """
--- Transform overwrite ---

This does NOT accumulate declarations:

    .card {
        transform: translateY(-4px);
        transform: scale(1.05);
    }

The second declaration replaces the first.

Use:

    transform: translateY(-4px) scale(1.05);

when both transformations are required.
"""
)


# ============================================================================
# 24. PERFORMANCE MODEL
# ============================================================================

@dataclass(frozen=True)
class PropertyPerformance:
    property_name: str
    typical_category: str
    practical_note: str


PERFORMANCE_MODEL = [
    PropertyPerformance(
        "transform",
        "compositing-friendly in many cases",
        "Often preferred for movement.",
    ),
    PropertyPerformance(
        "opacity",
        "compositing-friendly in many cases",
        "Often preferred for fades.",
    ),
    PropertyPerformance(
        "width",
        "layout-sensitive",
        "Changing dimensions can affect surrounding layout.",
    ),
    PropertyPerformance(
        "height",
        "layout-sensitive",
        "Can trigger layout work and affect descendants/siblings.",
    ),
    PropertyPerformance(
        "box-shadow",
        "paint-sensitive",
        "Large or complex shadows can be costly.",
    ),
]

print("\n--- Performance considerations ---")
for item in PERFORMANCE_MODEL:
    print(
        f"{item.property_name:>12} | "
        f"{item.typical_category:<32} | {item.practical_note}"
    )

print(
    """
Performance should be measured rather than assumed.

A common practical pattern is:

    transform: translate(...);
    opacity: ...;

These often avoid the same layout consequences associated with directly
changing dimensions or positional layout properties.

`will-change` exists, but it should not be applied indiscriminately:

    will-change: transform;

It communicates an anticipated change to the browser and can increase
resource usage if overused. It is not a universal performance switch.
"""
)


# ============================================================================
# 25. ANIMATING GRADIENT-LIKE UI STATES
# ============================================================================

print(
    """
--- Practical UI pattern ---

A polished card can transition multiple properties:

    .card {
        transform: translateY(0);
        border-color: transparent;
        box-shadow: 0 4px 14px rgb(0 0 0 / 0.12);

        transition:
            transform 220ms ease-out,
            border-color 220ms ease,
            box-shadow 220ms ease;
    }

    .card:hover {
        transform: translateY(-4px);
        border-color: currentColor;
        box-shadow: 0 12px 28px rgb(0 0 0 / 0.18);
    }

The transition belongs on `.card`, not only `.card:hover`, so entering and
leaving the hover state can both use the same smooth behavior.
"""
)


# ============================================================================
# 26. STAGGERED DELAYS
# ============================================================================

def staggered_transitions(
    item_count: int,
    base_delay_ms: int,
    step_ms: int,
) -> list[Transition]:
    """Generate transition delays for a list of UI items."""
    if item_count < 0:
        raise ValueError("item_count cannot be negative.")
    if base_delay_ms < 0 or step_ms < 0:
        raise ValueError("Delay values cannot be negative.")

    return [
        Transition(
            property_name="opacity",
            duration_ms=300,
            timing_function="ease-out",
            delay_ms=base_delay_ms + index * step_ms,
        )
        for index in range(item_count)
    ]


print("\n--- Staggered delay example ---")
for index, item in enumerate(staggered_transitions(5, 0, 60), start=1):
    print(f"Item {index}: {item.shorthand()}")

print(
    """
Staggering uses different delays:

    item 1 -> 0ms
    item 2 -> 60ms
    item 3 -> 120ms
    item 4 -> 180ms
    item 5 -> 240ms

This can create a cascading interface effect.

It should be used carefully because excessive sequencing can slow access to
information.
"""
)


# ============================================================================
# 27. CSS CUSTOM PROPERTIES
# ============================================================================

CUSTOM_PROPERTY_CSS = """\
.component {
    --transition-duration: 220ms;
    --transition-ease: cubic-bezier(0.2, 0.8, 0.2, 1);

    transition:
        transform var(--transition-duration) var(--transition-ease),
        opacity var(--transition-duration) var(--transition-ease);
}

.component:hover {
    transform: translateY(-3px);
}
"""

print("\n--- CSS custom properties ---")
print(CUSTOM_PROPERTY_CSS)

print(
    """
Custom properties make transition systems easier to centralize:

    --transition-duration
    --transition-ease

This is especially useful for design systems where many components share
interaction timing.
"""
)


# ============================================================================
# 28. DESIGN SYSTEM MODEL
# ============================================================================

@dataclass(frozen=True)
class MotionToken:
    """A reusable design-system transition token."""

    name: str
    duration_ms: int
    timing_function: str

    def css_variable_block(self) -> str:
        safe_name = self.name.replace("_", "-")
        return (
            f"--motion-{safe_name}-duration: {self.duration_ms}ms;\n"
            f"--motion-{safe_name}-easing: {self.timing_function};"
        )


MOTION_TOKENS = [
    MotionToken("instant", 0, "linear"),
    MotionToken("quick", 120, "ease-out"),
    MotionToken("standard", 220, "ease"),
    MotionToken("emphasis", 400, "ease-in-out"),
]

print("\n--- Motion tokens ---")
for token in MOTION_TOKENS:
    print(f"\n{token.name}:")
    print(token.css_variable_block())


# ============================================================================
# 29. INTERACTIVE COMPONENT STATE MACHINE
# ============================================================================

class InteractiveButton:
    """
    Model a button's logical states.

    CSS normally renders these states using pseudo-classes. This Python class
    models the conceptual state changes so the timing logic can be tested
    independently.
    """

    VALID_STATES = {"idle", "hover", "focus", "active", "disabled"}

    def __init__(self) -> None:
        self.state = "idle"

    def set_state(self, new_state: str) -> None:
        if new_state not in self.VALID_STATES:
            raise ValueError(f"Unknown button state: {new_state}")
        self.state = new_state

    def style_changes(self) -> dict[str, str]:
        styles = {
            "transform": "translateY(0)",
            "opacity": "1",
            "background-color": "#202938",
            "cursor": "pointer",
        }

        if self.state == "hover":
            styles["transform"] = "translateY(-2px)"
            styles["background-color"] = "#334155"

        elif self.state == "focus":
            styles["box-shadow"] = "0 0 0 3px currentColor"

        elif self.state == "active":
            styles["transform"] = "translateY(0) scale(0.98)"

        elif self.state == "disabled":
            styles["opacity"] = "0.55"
            styles["cursor"] = "not-allowed"

        return styles


print("\n--- Button state model ---")
button = InteractiveButton()

for state in ("idle", "hover", "focus", "active", "disabled"):
    button.set_state(state)
    print(f"{state:>8}: {button.style_changes()}")


# ============================================================================
# 30. VALIDATING CSS VALUES
# ============================================================================

def css_time(milliseconds: int) -> str:
    """Convert a non-negative integer duration to a CSS time."""
    if milliseconds < 0:
        raise ValueError("CSS time cannot be negative in this helper.")
    return f"{milliseconds}ms"


def build_transition(
    property_name: str,
    duration_ms: int,
    timing_function: str = "ease",
    delay_ms: int = 0,
) -> str:
    """Build and validate a transition shorthand."""
    transition = Transition(
        property_name,
        duration_ms,
        timing_function,
        delay_ms,
    )
    return transition.shorthand()


print("\n--- CSS value helper ---")
print(css_time(250))
print(build_transition("opacity", 250, "ease-out"))


# ============================================================================
# 31. TESTS
# ============================================================================

def run_tests() -> None:
    """Run lightweight assertions without third-party test frameworks."""
    assert clamp(-1) == 0
    assert clamp(0.5) == 0.5
    assert clamp(2) == 1

    assert interpolate(0, 100, 0) == 0
    assert interpolate(0, 100, 0.5) == 50
    assert interpolate(0, 100, 1) == 100

    assert linear(0.5) == 0.5
    assert ease_in(0) == 0
    assert ease_in(1) == 1
    assert ease_out(0) == 0
    assert ease_out(1) == 1
    assert ease_in_out(0) == 0
    assert ease_in_out(1) == 1

    transition = Transition("opacity", 300, "ease", 100)
    assert transition.total_time_ms == 400
    assert transition.shorthand() == "opacity 300ms ease 100ms"

    timeline = transition_timeline(300, 100)
    assert timeline[0][1] == 0
    assert timeline[-1][1] == 1

    generated = build_multi_transition(
        [
            Transition("opacity", 200),
            Transition("transform", 250, "ease-out"),
        ]
    )
    assert "opacity 200ms ease 0ms" in generated
    assert "transform 250ms ease-out 0ms" in generated

    button = InteractiveButton()
    button.set_state("hover")
    assert button.style_changes()["transform"] == "translateY(-2px)"

    print("\nAll built-in tests passed.")


run_tests()


# ============================================================================
# 32. COMPLETE HTML DEMONSTRATION
# ============================================================================

def create_demo_html() -> str:
    """Generate a complete self-contained HTML page demonstrating transitions."""
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CSS Transition Laboratory</title>
    <style>
        :root {
            color-scheme: dark;
            --surface: #111827;
            --surface-raised: #1f2937;
            --text: #f8fafc;
            --accent: #60a5fa;
            --transition-fast: 160ms;
            --transition-standard: 240ms;
            --ease-standard: cubic-bezier(0.2, 0.8, 0.2, 1);
        }

        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            min-height: 100vh;
            padding: 40px;
            background: #030712;
            color: var(--text);
            font-family: system-ui, sans-serif;
        }

        main {
            max-width: 900px;
            margin: 0 auto;
        }

        .demo-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
        }

        .card {
            padding: 24px;
            border: 1px solid #374151;
            border-radius: 16px;
            background: var(--surface);
            transform: translateY(0) scale(1);
            transition:
                transform var(--transition-standard) var(--ease-standard),
                background-color var(--transition-standard) ease,
                border-color var(--transition-standard) ease,
                box-shadow var(--transition-standard) ease;
        }

        .card:hover {
            transform: translateY(-6px) scale(1.02);
            background: var(--surface-raised);
            border-color: var(--accent);
            box-shadow: 0 18px 40px rgb(0 0 0 / 0.35);
        }

        .button {
            margin-top: 16px;
            padding: 12px 18px;
            border: 0;
            border-radius: 10px;
            background: var(--accent);
            color: #0f172a;
            cursor: pointer;
            transform: translateY(0);
            transition:
                transform var(--transition-fast) ease-out,
                filter var(--transition-fast) ease-out;
        }

        .button:hover {
            transform: translateY(-2px);
            filter: brightness(1.1);
        }

        .button:active {
            transform: translateY(0) scale(0.97);
        }

        .button:focus-visible {
            outline: 3px solid white;
            outline-offset: 3px;
        }

        .panel {
            margin-top: 24px;
            padding: 20px;
            border-radius: 12px;
            background: var(--surface-raised);
            opacity: 0;
            transform: translateY(10px);
            pointer-events: none;
            transition:
                opacity 220ms ease,
                transform 220ms ease;
        }

        .panel.is-open {
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
    </style>
</head>
<body>
<main>
    <h1>CSS Transition Laboratory</h1>
    <p>
        Hover cards, activate the button, and inspect the focus state to
        observe different transition mechanisms.
    </p>

    <section class="demo-grid" aria-label="Transition demonstrations">
        <article class="card">
            <h2>Transform</h2>
            <p>
                Hover this card to interpolate translation and scale.
            </p>
        </article>

        <article class="card">
            <h2>Shadow</h2>
            <p>
                The card also changes its shadow and border color.
            </p>
        </article>

        <article class="card">
            <h2>Multiple Properties</h2>
            <p>
                Each property participates in the same interaction.
            </p>
        </article>
    </section>

    <button class="button" id="toggleButton" type="button">
        Toggle Panel
    </button>

    <section class="panel" id="panel" aria-hidden="true">
        <h2>Transition State</h2>
        <p>
            Opacity and transform are transitioning together.
        </p>
    </section>
</main>

<script>
    const toggleButton = document.querySelector("#toggleButton");
    const panel = document.querySelector("#panel");

    toggleButton.addEventListener("click", () => {
        const isOpen = panel.classList.toggle("is-open");
        panel.setAttribute("aria-hidden", String(!isOpen));
    });

    panel.addEventListener("transitionend", (event) => {
        if (event.propertyName === "opacity") {
            console.log("Opacity transition completed.");
        }
    });
</script>
</body>
</html>
"""
    return html


demo_html = create_demo_html()

print("\n--- Generated interactive HTML size ---")
print(f"{len(demo_html):,} characters")

print(
    """
The generated HTML demonstrates:

    * transition-property
    * transition-duration
    * transition-timing-function
    * CSS custom properties
    * hover
    * active
    * focus-visible
    * transform
    * opacity
    * box-shadow
    * class-based state changes
    * JavaScript transitionend
    * prefers-reduced-motion
    * responsive layout

The HTML is intentionally generated as a string so this Python study file
remains self-contained.
"""
)


# ============================================================================
# 33. EDGE CASES
# ============================================================================

print("\n--- Edge cases ---")

edge_cases = [
    ("Duration = 0", "No visible interpolation."),
    ("Delay > duration", "The element waits longer before changing."),
    ("State changes repeatedly", "A transition may be interrupted or restarted."),
    ("Element removed during transition", "The transition may never reach its end."),
    ("Property is non-interpolable", "The browser may treat it as discrete."),
    ("Two declarations conflict", "Cascade rules determine the active state."),
    ("Transform declarations overwrite", "Combine transformations into one value."),
    ("User requests reduced motion", "Reduce or effectively disable motion."),
]

for case, behavior in edge_cases:
    print(f"{case:<32} -> {behavior}")


# ============================================================================
# 34. ADVANCED ARCHITECTURAL PATTERN
# ============================================================================

class TransitionSystem:
    """
    A small transition design-system model.

    It separates motion tokens from component-specific state definitions.
    This mirrors how larger design systems centralize motion decisions.
    """

    def __init__(self, tokens: Iterable[MotionToken]) -> None:
        self.tokens = {token.name: token for token in tokens}

    def get(self, token_name: str) -> MotionToken:
        try:
            return self.tokens[token_name]
        except KeyError as exc:
            raise KeyError(
                f"Unknown motion token: {token_name}"
            ) from exc

    def transition(self, token_name: str, property_name: str) -> str:
        token = self.get(token_name)
        return (
            f"{property_name} {token.duration_ms}ms "
            f"{token.timing_function}"
        )


motion_system = TransitionSystem(MOTION_TOKENS)

print("\n--- Design-system transition lookup ---")
print(motion_system.transition("quick", "transform"))
print(motion_system.transition("standard", "opacity"))


# ============================================================================
# 35. PRACTICAL CSS REVIEW CHECKLIST
# ============================================================================

REVIEW_CHECKLIST = [
    "Is the transition placed on the element's base state?",
    "Are only the necessary properties transitioned?",
    "Is the duration appropriate for the interaction?",
    "Does the timing function fit the type of motion?",
    "Is a delay genuinely useful?",
    "Does keyboard focus receive an equivalent visual state?",
    "Does the interaction remain understandable on touch devices?",
    "Is reduced motion respected?",
    "Are layout-heavy properties being changed unnecessarily?",
    "Could repeated transitions become distracting?",
    "Can an interrupted transition leave the UI in a confusing state?",
    "Are CSS custom properties useful for consistency?",
    "Has performance been checked on realistic devices?",
]

print("\n--- Production review checklist ---")
for number, item in enumerate(REVIEW_CHECKLIST, start=1):
    print(f"{number:>2}. {item}")


# ============================================================================
# 36. FINAL CONCEPTUAL MODEL
# ============================================================================

print(
    """
--- Final conceptual model ---

Think about a transition as:

    START VALUE
        |
        | state changes
        v
    DELAY
        |
        v
    TIMING FUNCTION
        |
        v
    INTERPOLATION
        |
        v
    END VALUE

The four primary CSS controls are:

    transition-property
    transition-duration
    transition-timing-function
    transition-delay

The shorthand combines them:

    transition:
        property duration timing-function delay;

For robust interfaces, combine transitions with:

    hover states
    focus-visible states
    active states
    class/state-based interaction
    accessible semantics
    reduced-motion preferences
    explicit property selection
    sensible durations
    performance-aware property choices
    careful event handling

The key implementation principle is to separate state from motion:
CSS selectors or application state establish WHAT the interface should look
like, while transition declarations establish HOW it moves between states.
"""
)

print("\n" + "=" * 78)
print("CSS TRANSITIONS STUDY SCRIPT COMPLETE")
print("=" * 78)
