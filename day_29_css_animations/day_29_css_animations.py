"""
CSS Animations: Keyframes, Animation Properties, Transforms, and Performance
===========================================================================

This standalone Python study file teaches the conceptual model behind CSS
animations and provides executable simulations of animation timing, keyframes,
transforms, interpolation, easing, composition, performance analysis, and
common edge cases.

Python cannot execute CSS in a browser, so the implementation models the
underlying animation mechanics numerically. The generated examples can be
used to understand what a browser is conceptually doing when it evaluates
CSS animation rules.

No third-party packages are required.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from math import cos, pi, sin
from statistics import mean
from typing import Callable, Iterable


# ============================================================================
# 1. FUNDAMENTAL TERMINOLOGY
# ============================================================================

def print_section(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


print_section("1. CSS Animation Fundamentals")

print(
    """
A CSS animation changes one or more CSS property values over time.

The central pieces are:

  @keyframes
      Defines the stages of an animation.

  animation-name
      Selects a keyframe animation.

  animation-duration
      Determines how long one iteration takes.

  animation-timing-function
      Controls interpolation speed over time.

  animation-delay
      Delays the start of the animation.

  animation-iteration-count
      Controls how many times the animation runs.

  animation-direction
      Controls whether iterations run normally, in reverse, or alternate.

  animation-fill-mode
      Determines which styles apply before and after the active interval.

  animation-play-state
      Controls whether the animation is running or paused.

  transform
      Provides efficient visual changes such as translation, rotation,
      scaling, and skewing.

A browser typically evaluates the animation timeline, resolves the current
keyframe interval, interpolates the values, and applies the resulting style.
"""
)


# ============================================================================
# 2. TRANSFORM DATA TYPES
# ============================================================================

@dataclass
class Transform:
    """
    A simplified 2D transform representation.

    CSS supports transform functions such as:
        translate()
        translateX()
        translateY()
        scale()
        rotate()
        skewX()
        skewY()

    Real CSS transforms are represented internally using matrices. This class
    keeps the educational model readable.
    """

    x: float = 0.0
    y: float = 0.0
    scale_x: float = 1.0
    scale_y: float = 1.0
    rotation_degrees: float = 0.0
    skew_x_degrees: float = 0.0
    skew_y_degrees: float = 0.0

    def interpolate(self, other: "Transform", progress: float) -> "Transform":
        return Transform(
            x=lerp(self.x, other.x, progress),
            y=lerp(self.y, other.y, progress),
            scale_x=lerp(self.scale_x, other.scale_x, progress),
            scale_y=lerp(self.scale_y, other.scale_y, progress),
            rotation_degrees=lerp(
                self.rotation_degrees,
                other.rotation_degrees,
                progress,
            ),
            skew_x_degrees=lerp(
                self.skew_x_degrees,
                other.skew_x_degrees,
                progress,
            ),
            skew_y_degrees=lerp(
                self.skew_y_degrees,
                other.skew_y_degrees,
                progress,
            ),
        )

    def css(self) -> str:
        parts = []

        if self.x != 0 or self.y != 0:
            parts.append(f"translate({self.x:.2f}px, {self.y:.2f}px)")

        if self.scale_x != 1 or self.scale_y != 1:
            parts.append(f"scale({self.scale_x:.3f}, {self.scale_y:.3f})")

        if self.rotation_degrees != 0:
            parts.append(f"rotate({self.rotation_degrees:.2f}deg)")

        if self.skew_x_degrees != 0:
            parts.append(f"skewX({self.skew_x_degrees:.2f}deg)")

        if self.skew_y_degrees != 0:
            parts.append(f"skewY({self.skew_y_degrees:.2f}deg)")

        return " ".join(parts) if parts else "none"


# ============================================================================
# 3. BASIC INTERPOLATION
# ============================================================================

def lerp(start: float, end: float, progress: float) -> float:
    """Linear interpolation between two numeric values."""
    progress = max(0.0, min(1.0, progress))
    return start + (end - start) * progress


print_section("2. Linear Interpolation")

print("Interpolate from 0px to 100px:")

for progress in (0.0, 0.25, 0.5, 0.75, 1.0):
    value = lerp(0, 100, progress)
    print(f"  progress={progress:.2f} -> {value:.1f}px")


# ============================================================================
# 4. EASING FUNCTIONS
# ============================================================================

EasingFunction = Callable[[float], float]


def linear(progress: float) -> float:
    return progress


def ease_in(progress: float) -> float:
    return progress * progress


def ease_out(progress: float) -> float:
    return 1 - (1 - progress) ** 2


def ease_in_out(progress: float) -> float:
    if progress < 0.5:
        return 2 * progress * progress
    return 1 - ((-2 * progress + 2) ** 2) / 2


def ease_in_cubic(progress: float) -> float:
    return progress ** 3


def ease_out_cubic(progress: float) -> float:
    return 1 - (1 - progress) ** 3


def ease_in_out_cubic(progress: float) -> float:
    if progress < 0.5:
        return 4 * progress ** 3
    return 1 - ((-2 * progress + 2) ** 3) / 2


def ease_out_back(progress: float) -> float:
    """
    Overshooting easing.

    This models the visual idea behind a cubic-bezier curve that briefly
    exceeds the final interpolated value before settling.
    """
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (progress - 1) ** 3 + c1 * (progress - 1) ** 2


EASINGS: dict[str, EasingFunction] = {
    "linear": linear,
    "ease-in": ease_in,
    "ease-out": ease_out,
    "ease-in-out": ease_in_out,
    "ease-in-cubic": ease_in_cubic,
    "ease-out-cubic": ease_out_cubic,
    "ease-in-out-cubic": ease_in_out_cubic,
    "ease-out-back": ease_out_back,
}


print_section("3. Timing Functions")

for name, function in EASINGS.items():
    values = [function(p / 4) for p in range(5)]
    formatted = ", ".join(f"{value:.3f}" for value in values)
    print(f"{name:18} {formatted}")


# ============================================================================
# 5. KEYFRAMES
# ============================================================================

@dataclass
class Keyframe:
    offset: float
    transform: Transform
    opacity: float = 1.0

    def __post_init__(self) -> None:
        if not 0 <= self.offset <= 1:
            raise ValueError("Keyframe offset must be between 0 and 1.")
        if not 0 <= self.opacity <= 1:
            raise ValueError("Opacity must be between 0 and 1.")


@dataclass
class Animation:
    name: str
    keyframes: list[Keyframe]
    duration_seconds: float
    timing_function: EasingFunction = linear
    delay_seconds: float = 0.0
    iteration_count: float | str = 1
    direction: str = "normal"
    fill_mode: str = "none"

    def __post_init__(self) -> None:
        if self.duration_seconds <= 0:
            raise ValueError("Animation duration must be positive.")

        if self.direction not in {
            "normal",
            "reverse",
            "alternate",
            "alternate-reverse",
        }:
            raise ValueError("Unsupported animation direction.")

        if self.fill_mode not in {"none", "forwards", "backwards", "both"}:
            raise ValueError("Unsupported fill mode.")

        if self.iteration_count != "infinite":
            if float(self.iteration_count) <= 0:
                raise ValueError("Iteration count must be positive.")

        self.keyframes.sort(key=lambda keyframe: keyframe.offset)

        if not self.keyframes:
            raise ValueError("An animation needs at least one keyframe.")

    @property
    def total_duration(self) -> float | None:
        if self.iteration_count == "infinite":
            return None
        return self.delay_seconds + self.duration_seconds * float(
            self.iteration_count
        )

    def _iteration_progress(self, local_time: float) -> tuple[float, int]:
        """
        Return normalized progress and iteration number.

        The method handles exact iteration boundaries carefully so that a
        finite animation can reach its final keyframe.
        """
        if local_time <= 0:
            return 0.0, 0

        raw_iteration = local_time / self.duration_seconds

        if (
            self.iteration_count != "infinite"
            and raw_iteration >= float(self.iteration_count)
        ):
            final_iteration = max(0, int(float(self.iteration_count)) - 1)
            return 1.0, final_iteration

        iteration_number = int(raw_iteration)
        progress = raw_iteration - iteration_number

        if self.direction == "normal":
            pass
        elif self.direction == "reverse":
            progress = 1 - progress
        elif self.direction == "alternate":
            if iteration_number % 2 == 1:
                progress = 1 - progress
        elif self.direction == "alternate-reverse":
            if iteration_number % 2 == 0:
                progress = 1 - progress

        return progress, iteration_number

    def state_at(self, time_seconds: float) -> tuple[Transform, float]:
        """
        Evaluate the animation at a specific time.

        This models:
          delay
          active interval
          fill mode
          iteration count
          direction
          timing function
          keyframe interpolation
        """
        if time_seconds < self.delay_seconds:
            if self.fill_mode in {"backwards", "both"}:
                first = self.keyframes[0]
                return first.transform, first.opacity
            return Transform(), 1.0

        active_time = time_seconds - self.delay_seconds

        if (
            self.iteration_count != "infinite"
            and active_time
            >= self.duration_seconds * float(self.iteration_count)
        ):
            if self.fill_mode in {"forwards", "both"}:
                progress, _ = self._iteration_progress(active_time)
                return self._interpolate_keyframes(progress)
            return Transform(), 1.0

        progress, _ = self._iteration_progress(active_time)
        return self._interpolate_keyframes(progress)

    def _interpolate_keyframes(
        self,
        normalized_progress: float,
    ) -> tuple[Transform, float]:
        eased_progress = self.timing_function(
            max(0.0, min(1.0, normalized_progress))
        )

        if len(self.keyframes) == 1:
            keyframe = self.keyframes[0]
            return keyframe.transform, keyframe.opacity

        if eased_progress <= self.keyframes[0].offset:
            first = self.keyframes[0]
            return first.transform, first.opacity

        if eased_progress >= self.keyframes[-1].offset:
            last = self.keyframes[-1]
            return last.transform, last.opacity

        for left, right in zip(self.keyframes, self.keyframes[1:]):
            if left.offset <= eased_progress <= right.offset:
                interval = right.offset - left.offset

                if interval == 0:
                    local_progress = 1.0
                else:
                    local_progress = (
                        eased_progress - left.offset
                    ) / interval

                transform = left.transform.interpolate(
                    right.transform,
                    local_progress,
                )

                opacity = lerp(
                    left.opacity,
                    right.opacity,
                    local_progress,
                )

                return transform, opacity

        raise RuntimeError("Unable to resolve animation keyframe interval.")


# ============================================================================
# 6. A FIRST COMPLETE ANIMATION
# ============================================================================

slide_animation = Animation(
    name="slide-and-fade",
    duration_seconds=2.0,
    timing_function=ease_in_out,
    keyframes=[
        Keyframe(
            offset=0.0,
            transform=Transform(x=0),
            opacity=0.0,
        ),
        Keyframe(
            offset=0.5,
            transform=Transform(x=100),
            opacity=1.0,
        ),
        Keyframe(
            offset=1.0,
            transform=Transform(x=200),
            opacity=1.0,
        ),
    ],
)


print_section("4. Evaluating a Multi-Keyframe Animation")

for time in [0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0]:
    transform, opacity = slide_animation.state_at(time)
    print(
        f"t={time:4.2f}s | "
        f"transform={transform.css():35} | "
        f"opacity={opacity:.3f}"
    )


# ============================================================================
# 7. MAPPING THE MODEL TO CSS
# ============================================================================

def css_keyframes(animation: Animation) -> str:
    """Generate readable CSS @keyframes syntax from the model."""
    lines = [f"@keyframes {animation.name} {{"]

    for keyframe in animation.keyframes:
        percentage = keyframe.offset * 100
        lines.append(f"  {percentage:g}% {{")
        lines.append(f"    transform: {keyframe.transform.css()};")
        lines.append(f"    opacity: {keyframe.opacity:.3f};")
        lines.append("  }")

    lines.append("}")
    return "\n".join(lines)


def css_animation_rule(animation: Animation, selector: str = ".animated") -> str:
    iteration = animation.iteration_count
    return (
        f"{selector} {{\n"
        f"  animation-name: {animation.name};\n"
        f"  animation-duration: {animation.duration_seconds}s;\n"
        f"  animation-timing-function: "
        f"{'linear' if animation.timing_function is linear else 'custom easing'};\n"
        f"  animation-delay: {animation.delay_seconds}s;\n"
        f"  animation-iteration-count: {iteration};\n"
        f"  animation-direction: {animation.direction};\n"
        f"  animation-fill-mode: {animation.fill_mode};\n"
        f"}}"
    )


print_section("5. CSS Representation")

print(css_keyframes(slide_animation))
print()
print(css_animation_rule(slide_animation))


# ============================================================================
# 8. ANIMATION PROPERTY SHORTHAND
# ============================================================================

def explain_animation_shorthand() -> None:
    print(
        """
The animation shorthand can combine:

animation:
    name
    duration
    timing-function
    delay
    iteration-count
    direction
    fill-mode
    play-state

For example:

animation: slide-and-fade 2s ease-in-out 0s 1 normal both;

The order is intentionally compact, but explicit longhand properties are
often easier to maintain when a component has many animation settings.
"""
    )


explain_animation_shorthand()


# ============================================================================
# 9. TRANSFORM FUNCTIONS
# ============================================================================

print_section("6. Transform Concepts")

transform_examples = [
    Transform(x=50),
    Transform(y=-30),
    Transform(scale_x=1.5, scale_y=1.5),
    Transform(rotation_degrees=45),
    Transform(skew_x_degrees=15),
    Transform(x=20, y=30, scale_x=1.2, scale_y=1.2, rotation_degrees=15),
]

for transform in transform_examples:
    print(transform.css())


# ============================================================================
# 10. TRANSFORM ORDER
# ============================================================================

print(
    """
Transform functions are not generally commutative.

For example:

  transform: translateX(100px) rotate(45deg);

is not equivalent to:

  transform: rotate(45deg) translateX(100px);

CSS transform composition uses matrix multiplication, so changing function
order can change the final coordinate system and visual result.
"""
)


def rotation_matrix(degrees: float) -> list[list[float]]:
    radians = degrees * pi / 180
    return [
        [cos(radians), -sin(radians)],
        [sin(radians), cos(radians)],
    ]


def multiply_matrix(
    first: list[list[float]],
    second: list[list[float]],
) -> list[list[float]]:
    return [
        [
            sum(first[row][k] * second[k][column] for k in range(3))
            for column in range(3)
        ]
        for row in range(3)
    ]


def translation_matrix(x: float, y: float) -> list[list[float]]:
    return [
        [1, 0, x],
        [0, 1, y],
        [0, 0, 1],
    ]


def homogeneous_rotation_matrix(degrees: float) -> list[list[float]]:
    two_by_two = rotation_matrix(degrees)
    return [
        [two_by_two[0][0], two_by_two[0][1], 0],
        [two_by_two[1][0], two_by_two[1][1], 0],
        [0, 0, 1],
    ]


def apply_matrix(
    matrix: list[list[float]],
    x: float,
    y: float,
) -> tuple[float, float]:
    result_x = matrix[0][0] * x + matrix[0][1] * y + matrix[0][2]
    result_y = matrix[1][0] * x + matrix[1][1] * y + matrix[1][2]
    return result_x, result_y


print_section("7. Transform Composition")

point = (1.0, 0.0)
translation = translation_matrix(100, 0)
rotation = homogeneous_rotation_matrix(90)

translate_then_rotate = multiply_matrix(rotation, translation)
rotate_then_translate = multiply_matrix(translation, rotation)

print(
    "translate -> rotate:",
    apply_matrix(translate_then_rotate, *point),
)

print(
    "rotate -> translate:",
    apply_matrix(rotate_then_translate, *point),
)


# ============================================================================
# 11. ITERATION AND DIRECTION
# ============================================================================

print_section("8. Iteration Count and Direction")

for direction in (
    "normal",
    "reverse",
    "alternate",
    "alternate-reverse",
):
    animation = Animation(
        name=direction,
        duration_seconds=1,
        iteration_count=3,
        direction=direction,
        fill_mode="forwards",
        keyframes=[
            Keyframe(0, Transform(x=0)),
            Keyframe(1, Transform(x=100)),
        ],
    )

    values = []
    for time in [0, 0.5, 1.0, 1.5, 2.0, 2.5]:
        transform, _ = animation.state_at(time)
        values.append(round(transform.x, 1))

    print(f"{direction:18}: {values}")


# ============================================================================
# 12. FILL MODES
# ============================================================================

print_section("9. Fill Modes")

for fill_mode in ("none", "backwards", "forwards", "both"):
    animation = Animation(
        name=f"fill-{fill_mode}",
        duration_seconds=2,
        delay_seconds=1,
        fill_mode=fill_mode,
        keyframes=[
            Keyframe(0, Transform(x=10), opacity=0),
            Keyframe(1, Transform(x=100), opacity=1),
        ],
    )

    before_start = animation.state_at(0.5)
    after_end = animation.state_at(3.5)

    print(
        f"{fill_mode:10} | "
        f"before={before_start[0].x:5.1f}px | "
        f"after={after_end[0].x:5.1f}px"
    )


# ============================================================================
# 13. CSS ANIMATION VS TRANSITION
# ============================================================================

print_section("10. Animation Versus Transition")

print(
    """
A transition generally describes a change between two states caused by a
property value change, such as:

button:hover {
    transform: scale(1.05);
    transition: transform 180ms ease;
}

An animation is timeline-driven and can contain multiple keyframes:

@keyframes pulse {
    0%   { transform: scale(1); }
    50%  { transform: scale(1.08); }
    100% { transform: scale(1); }
}

button {
    animation: pulse 1.2s ease-in-out infinite;
}

Transitions are useful for state changes.
Animations are useful for sequences, looping effects, staged motion, and
timeline-controlled visual behavior.
"""
)


# ============================================================================
# 14. CSS PROPERTY CATEGORIES
# ============================================================================

class PropertyCategory(Enum):
    COMPOSITOR_FRIENDLY = "compositor-friendly"
    PAINT_RELATED = "paint-related"
    LAYOUT_RELATED = "layout-related"
    CONTENT_RELATED = "content-related"


PROPERTY_CATEGORIES = {
    "transform": PropertyCategory.COMPOSITOR_FRIENDLY,
    "opacity": PropertyCategory.COMPOSITOR_FRIENDLY,
    "background-color": PropertyCategory.PAINT_RELATED,
    "box-shadow": PropertyCategory.PAINT_RELATED,
    "width": PropertyCategory.LAYOUT_RELATED,
    "height": PropertyCategory.LAYOUT_RELATED,
    "margin": PropertyCategory.LAYOUT_RELATED,
    "padding": PropertyCategory.LAYOUT_RELATED,
    "top": PropertyCategory.LAYOUT_RELATED,
    "left": PropertyCategory.LAYOUT_RELATED,
    "font-size": PropertyCategory.LAYOUT_RELATED,
}


print_section("11. Property Categories and Performance")

for property_name, category in PROPERTY_CATEGORIES.items():
    print(f"{property_name:18} -> {category.value}")


# ============================================================================
# 15. PERFORMANCE MODEL
# ============================================================================

@dataclass
class PerformanceSample:
    frame_time_ms: float
    layout_cost_ms: float
    paint_cost_ms: float
    composite_cost_ms: float

    @property
    def within_60fps_budget(self) -> bool:
        return self.frame_time_ms <= 16.67

    @property
    def within_120fps_budget(self) -> bool:
        return self.frame_time_ms <= 8.33


@dataclass
class PerformanceReport:
    samples: list[PerformanceSample] = field(default_factory=list)

    @property
    def average_frame_time(self) -> float:
        return mean(sample.frame_time_ms for sample in self.samples)

    @property
    def slow_frame_percentage(self) -> float:
        slow = sum(
            not sample.within_60fps_budget
            for sample in self.samples
        )
        return slow / len(self.samples) * 100 if self.samples else 0.0

    def print_report(self) -> None:
        print(f"Frames: {len(self.samples)}")
        print(f"Average frame time: {self.average_frame_time:.2f} ms")
        print(f"Frames over 16.67 ms: {self.slow_frame_percentage:.1f}%")


def simulate_performance(
    property_name: str,
    frame_count: int = 120,
) -> PerformanceReport:
    category = PROPERTY_CATEGORIES.get(
        property_name,
        PropertyCategory.PAINT_RELATED,
    )

    base_cost = {
        PropertyCategory.COMPOSITOR_FRIENDLY: 2.0,
        PropertyCategory.PAINT_RELATED: 7.0,
        PropertyCategory.LAYOUT_RELATED: 13.0,
        PropertyCategory.CONTENT_RELATED: 15.0,
    }[category]

    samples = []

    for frame in range(frame_count):
        variation = 0.5 * sin(frame / 5)
        layout_cost = (
            0.2
            if category != PropertyCategory.LAYOUT_RELATED
            else base_cost * 0.5
        )

        paint_cost = (
            0.3
            if category == PropertyCategory.COMPOSITOR_FRIENDLY
            else base_cost * 0.5
        )

        composite_cost = 1.0 + variation

        total = max(
            0.1,
            layout_cost + paint_cost + composite_cost,
        )

        samples.append(
            PerformanceSample(
                frame_time_ms=total,
                layout_cost_ms=layout_cost,
                paint_cost_ms=paint_cost,
                composite_cost_ms=composite_cost,
            )
        )

    return PerformanceReport(samples)


for property_name in ("transform", "opacity", "box-shadow", "width"):
    print(f"\n{property_name}:")
    simulate_performance(property_name).print_report()


# ============================================================================
# 16. FRAME BUDGET
# ============================================================================

print_section("12. Frame Budgets")

print(
    """
At approximately 60 Hz, one frame has about 16.67 ms available.

At approximately 120 Hz, one frame has about 8.33 ms available.

These are total frame budgets, not budgets exclusively available to CSS
animations. JavaScript, style calculation, layout, paint, compositing,
browser work, and other tasks can consume the same frame.

A smooth animation therefore depends on the complete rendering pipeline.
"""
)


def frame_budget(refresh_rate_hz: float) -> float:
    if refresh_rate_hz <= 0:
        raise ValueError("Refresh rate must be positive.")
    return 1000 / refresh_rate_hz


for refresh_rate in (60, 90, 120, 144, 240):
    print(
        f"{refresh_rate:3} Hz -> "
        f"{frame_budget(refresh_rate):.3f} ms/frame"
    )


# ============================================================================
# 17. WILL-CHANGE
# ============================================================================

print_section("13. will-change")

print(
    """
The CSS property:

will-change: transform;

allows an author to communicate that a property is expected to change.

It is not a universal performance switch.

Potential benefits:
  - The browser may prepare an element for frequent changes.
  - It can help some animation scenarios.

Potential costs:
  - Extra memory.
  - Extra compositor layers.
  - More GPU/resource pressure.
  - Poor results when applied indiscriminately to many elements.

Use it selectively and verify its effect using browser performance tools.
"""
)


# ============================================================================
# 18. ACCESSIBILITY: REDUCED MOTION
# ============================================================================

print_section("14. Reduced Motion")

print(
    """
Users may request reduced motion through the operating system.

CSS can respond with:

@media (prefers-reduced-motion: reduce) {
    .animated-element {
        animation: none;
        transition: none;
    }
}

Reduced motion does not necessarily mean every visual state change must
disappear. It means unnecessary motion should be reduced or replaced with a
less motion-intensive presentation.

This is particularly important for:
  - large parallax movement
  - rapid scaling
  - repeated spinning
  - flashing effects
  - continuous decorative motion
"""
)


# ============================================================================
# 19. ACCESSIBILITY MODEL
# ============================================================================

@dataclass
class AccessibilityPolicy:
    prefers_reduced_motion: bool
    animation_enabled: bool = True

    def should_animate(self) -> bool:
        if self.prefers_reduced_motion:
            return False
        return self.animation_enabled


for preference in (False, True):
    policy = AccessibilityPolicy(prefers_reduced_motion=preference)
    print(
        f"prefers-reduced-motion={preference} -> "
        f"animate={policy.should_animate()}"
    )


# ============================================================================
# 20. MULTIPLE ANIMATIONS
# ============================================================================

print_section("15. Multiple Animations")

print(
    """
CSS supports comma-separated animation declarations:

animation:
    move 2s ease-in-out infinite,
    fade 1s linear forwards;

Each animation has its own timeline and can affect different properties.

Care must be taken when two animations target the same property because the
animation cascade and compositing rules determine the resulting value.
"""
)


# ============================================================================
# 21. ADVANCED KEYFRAME INTERPOLATION
# ============================================================================

print_section("16. Advanced Multi-Stage Motion")

advanced_animation = Animation(
    name="orbit-like-motion",
    duration_seconds=4,
    timing_function=ease_in_out_cubic,
    iteration_count="infinite",
    direction="alternate",
    keyframes=[
        Keyframe(
            offset=0.0,
            transform=Transform(x=0, y=0, scale_x=1),
            opacity=0.4,
        ),
        Keyframe(
            offset=0.25,
            transform=Transform(x=80, y=-40, scale_x=1.1),
            opacity=0.8,
        ),
        Keyframe(
            offset=0.5,
            transform=Transform(x=160, y=0, scale_x=1.25),
            opacity=1,
        ),
        Keyframe(
            offset=0.75,
            transform=Transform(x=80, y=40, scale_x=1.1),
            opacity=0.8,
        ),
        Keyframe(
            offset=1.0,
            transform=Transform(x=0, y=0, scale_x=1),
            opacity=0.4,
        ),
    ],
)

for time in [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5]:
    transform, opacity = advanced_animation.state_at(time)
    print(
        f"{time:4.1f}s -> "
        f"{transform.css():55} "
        f"opacity={opacity:.3f}"
    )


# ============================================================================
# 22. CUBIC-BEZIER CONCEPT
# ============================================================================

print_section("17. Cubic-Bezier Concept")

print(
    """
CSS commonly expresses custom easing using:

cubic-bezier(x1, y1, x2, y2)

The x coordinates control the timing relationship and the y coordinates
control the output progression.

The control points define a parametric cubic curve. CSS implementations solve
for the output corresponding to the requested timeline progress.

Typical built-in timing functions are conceptually represented by cubic
Bezier curves, although steps() uses a different discrete timing model.
"""
)


def cubic_bezier(
    p0: float,
    p1: float,
    p2: float,
    p3: float,
    t: float,
) -> float:
    return (
        (1 - t) ** 3 * p0
        + 3 * (1 - t) ** 2 * t * p1
        + 3 * (1 - t) * t ** 2 * p2
        + t ** 3 * p3
    )


for t in [0, 0.25, 0.5, 0.75, 1]:
    value = cubic_bezier(0, 0.25, 0.75, 1, t)
    print(f"t={t:.2f} -> {value:.3f}")


# ============================================================================
# 23. STEPS TIMING FUNCTION
# ============================================================================

print_section("18. steps() Timing")

def steps(progress: float, number_of_steps: int) -> float:
    if number_of_steps <= 0:
        raise ValueError("Number of steps must be positive.")
    return min(
        number_of_steps,
        int(progress * number_of_steps),
    ) / number_of_steps


for count in (2, 4, 8):
    values = [steps(p / 8, count) for p in range(9)]
    print(f"steps({count}): {values}")


print(
    """
steps() is useful for discrete visual changes rather than smooth interpolation.

Typical uses include:
  - sprite-sheet animation
  - digital counters
  - typewriter-like effects
  - frame-by-frame visual changes
"""
)


# ============================================================================
# 24. EDGE CASES
# ============================================================================

print_section("19. Edge Cases")

edge_cases = [
    ("zero duration", 0),
    ("negative duration", -1),
    ("negative delay", -0.5),
]

for name, duration in edge_cases:
    try:
        animation = Animation(
            name=name.replace(" ", "-"),
            duration_seconds=duration,
            keyframes=[
                Keyframe(0, Transform()),
                Keyframe(1, Transform(x=100)),
            ],
        )
        print(name, animation)
    except ValueError as error:
        print(f"{name}: rejected -> {error}")


# ============================================================================
# 25. NEGATIVE DELAYS
# ============================================================================

print_section("20. Negative Delay Concept")

negative_delay_animation = Animation(
    name="negative-delay",
    duration_seconds=4,
    delay_seconds=-1,
    keyframes=[
        Keyframe(0, Transform(x=0)),
        Keyframe(1, Transform(x=400)),
    ],
)

print(
    """
A negative animation delay can cause an animation to appear as though it
started before the element became visible.

For example, a -1s delay on a 4s animation conceptually starts the animation
one second into its active timeline.
"""
)

for time in [0, 0.5, 1, 2, 3]:
    transform, _ = negative_delay_animation.state_at(time + 1)
    print(f"timeline={time:.1f}s -> x={transform.x:.1f}px")


# ============================================================================
# 26. PAUSED ANIMATIONS
# ============================================================================

print_section("21. animation-play-state")

print(
    """
animation-play-state has two main values:

running
paused

Pausing an animation does not erase its timeline state. The current visual
position remains fixed while it is paused.

A common interaction pattern is:

.card {
    animation: float 3s ease-in-out infinite;
}

.card:hover {
    animation-play-state: paused;
}
"""
)


@dataclass
class AnimationController:
    animation: Animation
    current_time: float = 0.0
    playing: bool = True

    def tick(self, elapsed_seconds: float) -> tuple[Transform, float]:
        if self.playing:
            self.current_time += max(0, elapsed_seconds)

        return self.animation.state_at(self.current_time)

    def pause(self) -> None:
        self.playing = False

    def play(self) -> None:
        self.playing = True


controller = AnimationController(slide_animation)

for elapsed in [0.25, 0.25, 0.25]:
    transform, _ = controller.tick(elapsed)
    print(f"running -> x={transform.x:.1f}px")

controller.pause()

for elapsed in [1, 1]:
    transform, _ = controller.tick(elapsed)
    print(f"paused  -> x={transform.x:.1f}px")

controller.play()

transform, _ = controller.tick(0.25)
print(f"resumed -> x={transform.x:.1f}px")


# ============================================================================
# 27. PERFORMANCE COMPARISON
# ============================================================================

print_section("22. Performance Comparison")

for property_name in (
    "transform",
    "opacity",
    "background-color",
    "box-shadow",
    "width",
    "left",
):
    report = simulate_performance(property_name, frame_count=60)
    print(
        f"{property_name:18} "
        f"average={report.average_frame_time:6.2f} ms "
        f"slow={report.slow_frame_percentage:5.1f}%"
    )


# ============================================================================
# 28. WHY TRANSFORM IS COMMONLY PREFERRED
# ============================================================================

print(
    """
For movement, these two approaches can produce similar visual goals:

  left: 100px;

and:

  transform: translateX(100px);

Animating layout properties such as left can require layout recalculation
depending on the surrounding document and browser optimizations.

Animating transform and opacity is commonly preferred for independent visual
motion because browsers can often process them efficiently in the compositor.

This is a guideline, not a guarantee. Actual performance depends on the
browser, device, DOM complexity, effects, layerization, and surrounding work.
"""
)


# ============================================================================
# 29. COMMON MISTAKES
# ============================================================================

print_section("23. Common Mistakes")

mistakes = {
    "Animating layout unnecessarily":
        "Prefer transform for visual movement when appropriate.",
    "Using will-change everywhere":
        "Reserve it for cases where measurement shows a meaningful benefit.",
    "Ignoring reduced motion":
        "Respect prefers-reduced-motion for motion-heavy interfaces.",
    "Animating too many elements":
        "Reduce simultaneous work and avoid unnecessary decorative motion.",
    "Using huge box-shadows":
        "Large blurred effects can increase paint cost.",
    "Animating width and height":
        "Layout-affecting properties can be more expensive than transforms.",
    "Forgetting fill-mode":
        "The element may snap back after an animation finishes.",
    "Confusing transition and animation":
        "Transitions respond to state changes; animations provide timelines.",
    "Overusing infinite animation":
        "Continuous motion consumes resources and can distract users.",
    "Ignoring frame rate":
        "A design that looks smooth at 60 Hz may expose problems at higher rates.",
}

for mistake, correction in mistakes.items():
    print(f"- {mistake}: {correction}")


# ============================================================================
# 30. PRODUCTION DESIGN CHECKLIST
# ============================================================================

print_section("24. Production Checklist")

checklist = [
    "Define the desired visual state before writing keyframes.",
    "Use meaningful animation names.",
    "Keep durations appropriate to the interaction.",
    "Choose easing that matches the physical or interaction model.",
    "Prefer transform and opacity for common independent motion.",
    "Avoid unnecessary layout-triggering animations.",
    "Test on low-powered devices.",
    "Test high-refresh-rate displays.",
    "Measure actual rendering performance.",
    "Respect prefers-reduced-motion.",
    "Avoid excessive simultaneous animations.",
    "Use will-change selectively.",
    "Check focus and keyboard interaction.",
    "Ensure animation does not hide essential information.",
    "Consider animation cancellation and interruption.",
    "Test animation-delay and fill-mode edge cases.",
    "Use browser developer tools to inspect rendering behavior.",
]

for number, item in enumerate(checklist, start=1):
    print(f"{number:2}. {item}")


# ============================================================================
# 31. COMPLETE CSS EXAMPLE
# ============================================================================

print_section("25. Complete CSS Example")

complete_css = """
.card {
  opacity: 0;
  transform: translateY(24px);
  animation: card-enter 700ms cubic-bezier(0.22, 1, 0.36, 1) forwards;
}

@keyframes card-enter {
  0% {
    opacity: 0;
    transform: translateY(24px);
  }

  100% {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (prefers-reduced-motion: reduce) {
  .card {
    animation: none;
    opacity: 1;
    transform: none;
  }
}
"""

print(complete_css)


# ============================================================================
# 32. FINAL STUDY EXERCISES AS EXECUTABLE CHECKS
# ============================================================================

print_section("26. Executable Concept Checks")


def assert_between(value: float, low: float, high: float) -> None:
    assert low <= value <= high, (
        f"Expected {value} to be between {low} and {high}"
    )


# Keyframe interpolation should reach endpoints.
test_animation = Animation(
    name="test",
    duration_seconds=1,
    keyframes=[
        Keyframe(0, Transform(x=0)),
        Keyframe(1, Transform(x=100)),
    ],
)

start_transform, _ = test_animation.state_at(0)
middle_transform, _ = test_animation.state_at(0.5)
end_transform, _ = test_animation.state_at(1)

assert start_transform.x == 0
assert_between(middle_transform.x, 0, 100)
assert end_transform.x == 100

# Direction should reverse the timeline.
reverse_animation = Animation(
    name="reverse",
    duration_seconds=1,
    direction="reverse",
    keyframes=[
        Keyframe(0, Transform(x=0)),
        Keyframe(1, Transform(x=100)),
    ],
)

reverse_start, _ = reverse_animation.state_at(0)
reverse_end, _ = reverse_animation.state_at(1)

assert reverse_start.x == 100
assert reverse_end.x == 0

# Transform interpolation should interpolate independently.
transform_a = Transform(x=0, scale_x=1, rotation_degrees=0)
transform_b = Transform(x=100, scale_x=2, rotation_degrees=90)
transform_middle = transform_a.interpolate(transform_b, 0.5)

assert transform_middle.x == 50
assert transform_middle.scale_x == 1.5
assert transform_middle.rotation_degrees == 45

print("All executable concept checks passed.")


# ============================================================================
# 33. STUDY REFERENCE
# ============================================================================

print_section("27. Compact Reference")

reference = {
    "@keyframes": "Defines animation stages.",
    "animation-name": "Selects the keyframes.",
    "animation-duration": "Controls iteration duration.",
    "animation-timing-function": "Controls temporal interpolation.",
    "animation-delay": "Offsets when the animation becomes active.",
    "animation-iteration-count": "Controls repetitions.",
    "animation-direction": "Controls playback direction.",
    "animation-fill-mode": "Controls styles outside the active interval.",
    "animation-play-state": "Pauses or resumes an animation.",
    "transform": "Changes visual geometry without directly changing layout.",
    "opacity": "Controls transparency and is commonly efficient to animate.",
    "will-change": "Hints at expected property changes; use selectively.",
    "prefers-reduced-motion": "Provides a user preference for reduced motion.",
}

for term, definition in reference.items():
    print(f"{term:32} {definition}")


print(
    """
Study principle:

An effective CSS animation is not merely a collection of keyframes. It is a
combination of timeline design, interpolation, transforms, property selection,
accessibility, browser rendering behavior, and measured performance.

The most important production habit is to verify the visual and performance
result in the target environment rather than assuming that a particular CSS
property is always cheap or always expensive.
"""
)
