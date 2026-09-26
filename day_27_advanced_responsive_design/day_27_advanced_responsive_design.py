"""
Advanced Responsive Design
==========================

Topic:
    Container queries, fluid layouts, clamp(), and responsive components.

This standalone study script explains responsive-design mathematics and
generates a complete HTML/CSS demonstration that can be opened in a browser.

The Python portion focuses on:
    1. Responsive-design fundamentals.
    2. Viewport versus container responsiveness.
    3. Breakpoints.
    4. Fluid sizing.
    5. clamp(minimum, preferred, maximum).
    6. Linear interpolation.
    7. Container-query reasoning.
    8. Responsive component decisions.
    9. CSS value validation.
    10. A small responsive-layout simulation.
    11. Generation of a self-contained browser demonstration.
    12. Edge cases and tests.

No third-party packages are required.
"""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import Iterable


# ---------------------------------------------------------------------------
# 1. FUNDAMENTAL RESPONSIVE-DESIGN CONCEPTS
# ---------------------------------------------------------------------------

def explain_fundamentals() -> None:
    """Print the core vocabulary used throughout this study file."""
    concepts = {
        "Responsive design":
            "A design approach where layout, sizing, spacing, and behavior "
            "adapt to available space and device conditions.",
        "Viewport":
            "The visible browser area in which a document is rendered.",
        "Breakpoint":
            "A condition at which a layout or component changes behavior.",
        "Fluid layout":
            "A layout whose dimensions can continuously adapt instead of "
            "changing only at fixed breakpoints.",
        "Container query":
            "A CSS query that allows a component to respond to its containing "
            "element's size rather than directly to the viewport.",
        "clamp()":
            "A CSS function that constrains a preferred value between a "
            "minimum and maximum.",
        "Responsive component":
            "A reusable UI component whose internal layout adapts to the "
            "space available to that component.",
    }

    print("\n=== FUNDAMENTAL TERMINOLOGY ===")
    for name, definition in concepts.items():
        print(f"{name}: {definition}")


# ---------------------------------------------------------------------------
# 2. BREAKPOINTS
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Breakpoint:
    """Represents a viewport or container threshold."""
    name: str
    minimum_width: float


BREAKPOINTS = (
    Breakpoint("compact", 0),
    Breakpoint("comfortable", 600),
    Breakpoint("expanded", 900),
    Breakpoint("wide", 1200),
)


def classify_width(width: float, breakpoints: Iterable[Breakpoint] = BREAKPOINTS) -> str:
    """
    Classify a width using the largest breakpoint not exceeding the width.

    This demonstrates traditional breakpoint-based thinking. A production
    CSS design should avoid accumulating unnecessary breakpoints.
    """
    if width < 0:
        raise ValueError("Width cannot be negative.")

    ordered = sorted(breakpoints, key=lambda item: item.minimum_width)
    selected = ordered[0]

    for breakpoint in ordered:
        if width >= breakpoint.minimum_width:
            selected = breakpoint
        else:
            break

    return selected.name


# ---------------------------------------------------------------------------
# 3. FLUID INTERPOLATION
# ---------------------------------------------------------------------------

def linear_interpolate(
    width: float,
    minimum_width: float,
    maximum_width: float,
    minimum_value: float,
    maximum_value: float,
) -> float:
    """
    Linearly interpolate a value between two widths.

    The function intentionally clamps the interpolation ratio so values
    outside the design range do not extrapolate unexpectedly.
    """
    if maximum_width <= minimum_width:
        raise ValueError("maximum_width must be greater than minimum_width.")

    ratio = (width - minimum_width) / (maximum_width - minimum_width)
    ratio = max(0.0, min(1.0, ratio))

    return minimum_value + ratio * (maximum_value - minimum_value)


def demonstrate_fluid_spacing() -> None:
    """Show a continuously changing spacing value."""
    print("\n=== FLUID SPACING ===")

    for width in (320, 480, 768, 1024, 1440):
        spacing = linear_interpolate(
            width=width,
            minimum_width=320,
            maximum_width=1440,
            minimum_value=16,
            maximum_value=48,
        )

        print(
            f"viewport={width:4.0f}px -> "
            f"spacing={spacing:5.1f}px -> "
            f"layout={classify_width(width)}"
        )


# ---------------------------------------------------------------------------
# 4. clamp() MATHEMATICS
# ---------------------------------------------------------------------------

def clamp_value(minimum: float, preferred: float, maximum: float) -> float:
    """
    Simulate CSS clamp(minimum, preferred, maximum).

    Mathematically:
        max(minimum, min(preferred, maximum))
    """
    if minimum > maximum:
        raise ValueError("The minimum cannot exceed the maximum.")

    return max(minimum, min(preferred, maximum))


def css_clamp_value(
    width: float,
    minimum_width: float,
    maximum_width: float,
    minimum_value: float,
    maximum_value: float,
) -> float:
    """
    Simulate a common CSS expression:

        clamp(min_value, fluid_value, max_value)

    The fluid preferred value is represented using linear interpolation.
    """
    preferred = linear_interpolate(
        width,
        minimum_width,
        maximum_width,
        minimum_value,
        maximum_value,
    )

    return clamp_value(minimum_value, preferred, maximum_value)


def demonstrate_clamp() -> None:
    """
    Demonstrate the practical idea behind CSS clamp().

    A real CSS declaration could be:

        font-size: clamp(1.25rem, 2vw + 0.5rem, 2rem);

    The browser evaluates the preferred expression continuously and then
    keeps the result inside the minimum/maximum bounds.
    """
    print("\n=== clamp() SIMULATION ===")

    for viewport_width in (240, 320, 480, 768, 1024, 1440, 1920):
        font_size = css_clamp_value(
            width=viewport_width,
            minimum_width=320,
            maximum_width=1440,
            minimum_value=20,
            maximum_value=32,
        )

        print(
            f"{viewport_width:4d}px viewport -> "
            f"{font_size:5.1f}px heading size"
        )


# ---------------------------------------------------------------------------
# 5. RESPONSIVE COMPONENT MODEL
# ---------------------------------------------------------------------------

@dataclass
class ComponentState:
    """
    Represents a component's layout mode.

    A component should ideally react to its own available space. The Python
    model lets us reason about that behavior without a browser.
    """

    width: float
    mode: str
    columns: int
    show_secondary_text: bool
    compact_controls: bool


def responsive_component_state(container_width: float) -> ComponentState:
    """
    Select a component layout based on container width.

    These thresholds correspond conceptually to CSS container queries.
    """
    if container_width < 360:
        return ComponentState(
            width=container_width,
            mode="compact",
            columns=1,
            show_secondary_text=False,
            compact_controls=True,
        )

    if container_width < 640:
        return ComponentState(
            width=container_width,
            mode="standard",
            columns=1,
            show_secondary_text=True,
            compact_controls=True,
        )

    return ComponentState(
        width=container_width,
        mode="expanded",
        columns=2,
        show_secondary_text=True,
        compact_controls=False,
    )


def demonstrate_container_logic() -> None:
    """Compare component behavior at different container widths."""
    print("\n=== CONTAINER-BASED COMPONENT LOGIC ===")

    for width in (280, 340, 420, 580, 640, 760):
        state = responsive_component_state(width)

        print(
            f"container={width:3.0f}px | "
            f"mode={state.mode:9s} | "
            f"columns={state.columns} | "
            f"secondary_text={state.show_secondary_text} | "
            f"compact_controls={state.compact_controls}"
        )


# ---------------------------------------------------------------------------
# 6. VIEWPORT QUERIES VERSUS CONTAINER QUERIES
# ---------------------------------------------------------------------------

def compare_responsive_strategies() -> None:
    """
    Explain when each type of responsive condition is useful.

    This is deliberately printed as factual guidance rather than treating
    one mechanism as universally superior.
    """
    print("\n=== VIEWPORT QUERIES VS CONTAINER QUERIES ===")

    comparison = [
        (
            "Viewport media query",
            "Responds to browser/device conditions.",
            "Global navigation, page-level grids, print rules, orientation."
        ),
        (
            "Container query",
            "Responds to the size of a component's containing box.",
            "Cards, widgets, reusable panels, dashboards, sidebars."
        ),
        (
            "Fluid CSS",
            "Changes continuously over a range.",
            "Typography, gaps, padding, widths and other scalable values."
        ),
        (
            "clamp()",
            "Combines a fluid preferred value with hard limits.",
            "Safe fluid typography, spacing and component dimensions."
        ),
    ]

    for mechanism, behavior, examples in comparison:
        print(f"\n{mechanism}")
        print(f"  Behavior: {behavior}")
        print(f"  Examples: {examples}")


# ---------------------------------------------------------------------------
# 7. ACCESSIBILITY AND ROBUSTNESS
# ---------------------------------------------------------------------------

def validate_responsive_constraints(
    minimum_font_size: float,
    maximum_font_size: float,
    minimum_spacing: float,
    maximum_spacing: float,
) -> list[str]:
    """Validate common constraints before values are placed into CSS."""
    errors: list[str] = []

    if minimum_font_size <= 0:
        errors.append("Minimum font size must be positive.")

    if maximum_font_size < minimum_font_size:
        errors.append("Maximum font size cannot be smaller than minimum size.")

    if minimum_spacing < 0:
        errors.append("Minimum spacing cannot be negative.")

    if maximum_spacing < minimum_spacing:
        errors.append("Maximum spacing cannot be smaller than minimum spacing.")

    return errors


def demonstrate_validation() -> None:
    """Show successful and unsuccessful design-value validation."""
    print("\n=== RESPONSIVE VALUE VALIDATION ===")

    valid = validate_responsive_constraints(16, 32, 8, 48)
    invalid = validate_responsive_constraints(0, 12, 32, 8)

    print("Valid configuration:", "accepted" if not valid else valid)
    print("Invalid configuration:", "accepted" if not invalid else invalid)


# ---------------------------------------------------------------------------
# 8. CSS GENERATION
# ---------------------------------------------------------------------------

CSS = r"""
:root {
    color-scheme: dark;
    --page-max: 1400px;
    --page-padding: clamp(1rem, 3vw, 3rem);
    --section-gap: clamp(2rem, 6vw, 6rem);
    --card-gap: clamp(0.75rem, 2vw, 1.5rem);
    --radius: clamp(0.75rem, 1.5vw, 1.25rem);
    --heading-size: clamp(2rem, 5vw + 0.5rem, 5rem);
    --body-size: clamp(1rem, 0.35vw + 0.95rem, 1.2rem);
}

* {
    box-sizing: border-box;
}

html {
    scroll-behavior: smooth;
}

body {
    margin: 0;
    min-width: 280px;
    background: #08090c;
    color: #f5f7fa;
    font-family:
        Inter,
        ui-sans-serif,
        system-ui,
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
    font-size: var(--body-size);
    line-height: 1.6;
}

img,
svg {
    display: block;
    max-width: 100%;
}

button,
input {
    font: inherit;
}

.page {
    width: min(100% - 2 * var(--page-padding), var(--page-max));
    margin-inline: auto;
}

.hero {
    min-height: 70svh;
    display: grid;
    align-items: center;
    padding-block: var(--section-gap);
}

.hero h1 {
    max-width: 12ch;
    margin: 0;
    font-size: var(--heading-size);
    line-height: 0.95;
    text-wrap: balance;
}

.hero p {
    max-width: 65ch;
}

.section {
    margin-block: var(--section-gap);
}

.demo-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(100%, 280px), 1fr));
    gap: var(--card-gap);
}

.demo-card {
    container-type: inline-size;
    container-name: demo-card;
    padding: clamp(1rem, 4cqw, 2rem);
    border: 1px solid #30343b;
    border-radius: var(--radius);
    background: #101319;
}

.demo-card__body {
    display: grid;
    gap: 1rem;
}

.demo-card__content {
    min-width: 0;
}

.demo-card__title {
    margin: 0;
    font-size: clamp(1.25rem, 3cqw, 2rem);
    line-height: 1.1;
}

.demo-card__description {
    color: #b7bdc7;
}

.demo-card__actions {
    display: flex;
    flex-wrap: wrap;
    gap: 0.6rem;
}

.demo-card__action {
    min-height: 2.75rem;
    padding-inline: 1rem;
    border: 1px solid #4a505b;
    border-radius: 999px;
    background: transparent;
    color: inherit;
    cursor: pointer;
}

@container demo-card (min-width: 520px) {
    .demo-card__body {
        grid-template-columns: minmax(0, 1fr) auto;
        align-items: center;
    }

    .demo-card__actions {
        justify-content: flex-end;
    }
}

@container demo-card (max-width: 359px) {
    .demo-card__description {
        display: none;
    }

    .demo-card__action {
        width: 100%;
    }
}

.fluid-panel {
    padding: clamp(1rem, 4vw, 3rem);
    border-radius: clamp(1rem, 3vw, 2rem);
    background: linear-gradient(135deg, #11151c, #1a2029);
}

.fluid-panel h2 {
    margin-top: 0;
    font-size: clamp(1.75rem, 4vw, 3.5rem);
    text-wrap: balance;
}

.responsive-dashboard {
    container-type: inline-size;
}

.dashboard-layout {
    display: grid;
    gap: 1rem;
}

.dashboard-stat {
    padding: clamp(1rem, 3cqw, 1.75rem);
    border: 1px solid #30343b;
    border-radius: 1rem;
    background: #0e1116;
}

.dashboard-stat strong {
    display: block;
    font-size: clamp(1.5rem, 5cqw, 3rem);
}

@container (min-width: 700px) {
    .dashboard-layout {
        grid-template-columns: repeat(3, 1fr);
    }
}

@container (min-width: 1000px) {
    .dashboard-layout {
        grid-template-columns: repeat(4, 1fr);
    }
}

@media (prefers-reduced-motion: reduce) {
    html {
        scroll-behavior: auto;
    }
}
"""


# ---------------------------------------------------------------------------
# 9. HTML GENERATION
# ---------------------------------------------------------------------------

def build_card(index: int, title: str, description: str) -> str:
    """Create one reusable responsive card."""
    safe_title = escape(title)
    safe_description = escape(description)

    return f"""
    <article class="demo-card">
        <div class="demo-card__body">
            <div class="demo-card__content">
                <h3 class="demo-card__title">{index}. {safe_title}</h3>
                <p class="demo-card__description">{safe_description}</p>
            </div>
            <div class="demo-card__actions">
                <button class="demo-card__action" type="button"
                        data-action="inspect">
                    Inspect
                </button>
                <button class="demo-card__action" type="button"
                        data-action="toggle">
                    Toggle
                </button>
            </div>
        </div>
    </article>
    """


def build_html() -> str:
    """Build a self-contained HTML study demonstration."""
    cards = [
        (
            "Container Query",
            "This card responds to its own container width instead of "
            "assuming that the viewport width represents its available space."
        ),
        (
            "Fluid Typography",
            "The heading uses clamp() so its size changes continuously while "
            "remaining inside explicit minimum and maximum bounds."
        ),
        (
            "Fluid Spacing",
            "Padding and gaps use clamp() to avoid abrupt changes between "
            "small and large layouts."
        ),
        (
            "Responsive Component",
            "The component changes from a stacked arrangement to a "
            "multi-column arrangement when its own container grows."
        ),
    ]

    cards_html = "\n".join(
        build_card(index, title, description)
        for index, (title, description) in enumerate(cards, start=1)
    )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description"
      content="Advanced responsive design demonstration">
<title>Advanced Responsive Design</title>
<style>
{CSS}
</style>
</head>
<body>
<main class="page">
    <section class="hero">
        <div>
            <p>Advanced Responsive Design</p>
            <h1>Design around available space.</h1>
            <p>
                This demonstration combines container queries, fluid layouts,
                clamp(), CSS container units, and responsive components.
            </p>
        </div>
    </section>

    <section class="section">
        <div class="demo-grid">
            {cards_html}
        </div>
    </section>

    <section class="section">
        <div class="fluid-panel">
            <h2>Fluid values avoid unnecessary breakpoint jumps.</h2>
            <p>
                Resize the browser continuously. The typography, spacing and
                card behavior adapt at different rates because each mechanism
                solves a different responsive-design problem.
            </p>
        </div>
    </section>

    <section class="section">
        <div class="responsive-dashboard">
            <div class="dashboard-layout">
                <article class="dashboard-stat">
                    <strong data-number="42">42</strong>
                    <span>Container-aware metric</span>
                </article>
                <article class="dashboard-stat">
                    <strong data-number="18">18</strong>
                    <span>Fluid spacing units</span>
                </article>
                <article class="dashboard-stat">
                    <strong data-number="7">7</strong>
                    <span>Responsive states</span>
                </article>
                <article class="dashboard-stat">
                    <strong data-number="100">100%</strong>
                    <span>CSS-driven layout</span>
                </article>
            </div>
        </div>
    </section>
</main>

<script>
"use strict";

document.querySelectorAll("[data-action]").forEach((button) => {{
    button.addEventListener("click", () => {{
        const card = button.closest(".demo-card");

        if (!card) {{
            return;
        }}

        if (button.dataset.action === "toggle") {{
            card.classList.toggle("is-active");
            button.textContent =
                card.classList.contains("is-active")
                    ? "Active"
                    : "Toggle";
        }}

        if (button.dataset.action === "inspect") {{
            const width = card.getBoundingClientRect().width;
            console.log(
                "Component width:",
                Math.round(width) + "px"
            );
        }}
    }});
}});

const observer = new ResizeObserver((entries) => {{
    for (const entry of entries) {{
        entry.target.dataset.containerWidth =
            Math.round(entry.contentRect.width);
    }}
}});

document.querySelectorAll(".demo-card").forEach((card) => {{
    observer.observe(card);
}});
</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# 10. GENERATE THE PRACTICAL DEMONSTRATION
# ---------------------------------------------------------------------------

def write_demo_file(filename: str = "responsive_design_demo.html") -> Path:
    """
    Write the generated browser demonstration.

    UTF-8 is used explicitly so the output is portable across systems.
    """
    path = Path(filename)
    path.write_text(build_html(), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# 11. EDGE CASES
# ---------------------------------------------------------------------------

def demonstrate_edge_cases() -> None:
    """Demonstrate important boundary conditions."""
    print("\n=== EDGE CASES ===")

    test_widths = (-1, 0, 279, 280, 359, 360, 599, 600, 899, 900, 1199, 1200)

    for width in test_widths:
        try:
            state = responsive_component_state(width)

            print(
                f"width={width:4d}px -> "
                f"mode={state.mode}, columns={state.columns}"
            )
        except Exception as error:
            print(f"width={width:4d}px -> error: {error}")

    print("\nclamp boundaries:")
    for preferred in (-10, 10, 20, 30, 50):
        result = clamp_value(16, preferred, 32)
        print(f"clamp(16, {preferred}, 32) -> {result}")


# ---------------------------------------------------------------------------
# 12. COMMON MISTAKES
# ---------------------------------------------------------------------------

def print_common_mistakes() -> None:
    """Print concise implementation checks."""
    mistakes = [
        "Using many arbitrary breakpoints instead of designing around layout constraints.",
        "Assuming viewport width equals component width.",
        "Using fixed pixel typography that becomes uncomfortable across sizes.",
        "Using clamp() without meaningful minimum and maximum limits.",
        "Allowing long words or unbreakable content to overflow containers.",
        "Ignoring user zoom and larger text settings.",
        "Hiding essential information solely because a component became narrow.",
        "Using JavaScript resize handlers when CSS can solve the layout problem.",
        "Creating container-query rules without declaring an appropriate query container.",
        "Testing only one device width instead of testing intermediate widths.",
    ]

    print("\n=== COMMON MISTAKES ===")
    for number, mistake in enumerate(mistakes, start=1):
        print(f"{number:2d}. {mistake}")


# ---------------------------------------------------------------------------
# 13. TESTS
# ---------------------------------------------------------------------------

def run_tests() -> None:
    """Execute lightweight tests for the mathematical and layout models."""
    print("\n=== TESTS ===")

    assert classify_width(320) == "compact"
    assert classify_width(600) == "comfortable"
    assert classify_width(900) == "expanded"
    assert classify_width(1200) == "wide"

    assert linear_interpolate(320, 320, 1440, 16, 48) == 16
    assert linear_interpolate(1440, 320, 1440, 16, 48) == 48
    assert linear_interpolate(880, 320, 1440, 16, 48) == 32

    assert clamp_value(16, 10, 32) == 16
    assert clamp_value(16, 24, 32) == 24
    assert clamp_value(16, 40, 32) == 32

    assert responsive_component_state(300).mode == "compact"
    assert responsive_component_state(500).mode == "standard"
    assert responsive_component_state(800).mode == "expanded"

    assert validate_responsive_constraints(16, 32, 8, 48) == []
    assert validate_responsive_constraints(0, 32, 8, 48)
    assert validate_responsive_constraints(32, 16, 8, 48)

    print("All tests passed.")


# ---------------------------------------------------------------------------
# 14. PERFORMANCE REASONING
# ---------------------------------------------------------------------------

def performance_notes() -> None:
    """Print implementation-level performance considerations."""
    print("\n=== PERFORMANCE CONSIDERATIONS ===")

    notes = [
        "Prefer CSS media and container queries for layout decisions.",
        "Avoid continuously writing layout-affecting styles from resize events.",
        "ResizeObserver is useful when JavaScript genuinely needs element-size information.",
        "Use CSS Grid and Flexbox instead of JavaScript-generated coordinates.",
        "Keep container-query selectors understandable and reasonably scoped.",
        "Avoid unnecessary DOM mutations during resize.",
        "Use responsive images and appropriate intrinsic dimensions.",
        "Test real content, because text wrapping can expose layout problems.",
    ]

    for note in notes:
        print(f"- {note}")


# ---------------------------------------------------------------------------
# 15. SECURITY AND PRODUCTION CONSIDERATIONS
# ---------------------------------------------------------------------------

def production_notes() -> None:
    """Print security, accessibility and production considerations."""
    print("\n=== PRODUCTION CONSIDERATIONS ===")

    notes = [
        "Responsive CSS does not replace semantic HTML or accessibility testing.",
        "Do not use CSS to conceal information that users need to operate the application.",
        "Respect prefers-reduced-motion when responsive transitions include animation.",
        "Avoid injecting untrusted strings into generated HTML without escaping.",
        "The generated demonstration uses html.escape() for dynamic card text.",
        "Validate responsive states with keyboard navigation and zoom.",
        "Check layouts at intermediate widths, not only conventional device widths.",
        "Use min-width: 0 where grid or flex children may otherwise overflow.",
        "Use min(), max(), and clamp() when continuous constraints are clearer than breakpoints.",
    ]

    for note in notes:
        print(f"- {note}")


# ---------------------------------------------------------------------------
# 16. MAIN STUDY PROGRAM
# ---------------------------------------------------------------------------

def main() -> None:
    """Run the complete responsive-design study."""
    print("=" * 72)
    print("ADVANCED RESPONSIVE DESIGN STUDY")
    print("=" * 72)

    explain_fundamentals()
    demonstrate_fluid_spacing()
    demonstrate_clamp()
    demonstrate_container_logic()
    compare_responsive_strategies()
    demonstrate_validation()
    demonstrate_edge_cases()
    print_common_mistakes()
    performance_notes()
    production_notes()
    run_tests()

    generated_file = write_demo_file()

    print("\n=== PRACTICAL DEMONSTRATION ===")
    print(f"Generated: {generated_file.resolve()}")
    print("Open the HTML file in a modern browser and resize the window.")
    print("The browser demonstration contains container queries and clamp().")


if __name__ == "__main__":
    main()
