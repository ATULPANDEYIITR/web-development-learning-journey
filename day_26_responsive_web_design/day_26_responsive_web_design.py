"""
Responsive Web Design: Mobile-First Design, Breakpoints, Media Queries,
Responsive Typography, and Responsive Images

This standalone study script teaches responsive web design from fundamentals
through advanced implementation patterns. It generates a complete responsive
HTML/CSS/JavaScript demonstration page in memory, validates responsive design
configuration, simulates breakpoint decisions, calculates fluid typography and
image dimensions, demonstrates responsive image selection, and runs a small
test suite.

The script uses only Python's standard library.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from html import escape
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple
import math
import re
import tempfile
import textwrap
import unittest


# ============================================================================
# 1. FUNDAMENTAL TERMINOLOGY
# ============================================================================

TERMS: Dict[str, str] = {
    "responsive web design": (
        "A design and implementation approach that allows a website to adapt "
        "its layout, content, typography, images, and interaction to different "
        "viewport sizes and device capabilities."
    ),
    "mobile-first": (
        "A strategy in which the base CSS is designed for small screens first "
        "and larger-screen enhancements are added with progressively wider "
        "media queries."
    ),
    "breakpoint": (
        "A viewport condition at which a layout changes because the existing "
        "layout no longer provides an appropriate user experience."
    ),
    "media query": (
        "A CSS conditional rule that applies styles when media features such "
        "as viewport width, orientation, resolution, or user preferences match."
    ),
    "fluid layout": (
        "A layout whose dimensions can continuously adapt instead of being "
        "restricted to one fixed screen width."
    ),
    "responsive typography": (
        "Typography that adapts to available space using flexible units, "
        "clamping, line-height rules, and breakpoint-specific adjustments."
    ),
    "responsive image": (
        "An image implementation that supplies an appropriate source or "
        "display size for the user's viewport and device characteristics."
    ),
    "viewport": (
        "The visible area of a browser through which a page is currently "
        "displayed."
    ),
    "content breakpoint": (
        "A breakpoint selected because the content or layout needs to change, "
        "rather than because a particular device has a specific screen size."
    ),
}


def print_section(title: str) -> None:
    """Print a consistent study-section heading."""
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def print_terms() -> None:
    """Display core responsive-design terminology."""
    print_section("1. CORE TERMINOLOGY")

    for term, definition in TERMS.items():
        print(f"\n{term.upper()}")
        print(f"  {definition}")


# ============================================================================
# 2. VIEWPORTS, BREAKPOINTS, AND LAYOUT MODES
# ============================================================================

@dataclass(frozen=True)
class Breakpoint:
    """
    A named responsive breakpoint.

    A breakpoint describes a minimum viewport width. It does not represent a
    device model. Real responsive designs should choose breakpoints based on
    where the content needs to change.
    """

    name: str
    min_width: int


DEFAULT_BREAKPOINTS: Tuple[Breakpoint, ...] = (
    Breakpoint("mobile", 0),
    Breakpoint("tablet", 600),
    Breakpoint("desktop", 900),
    Breakpoint("wide", 1200),
)


def validate_breakpoints(breakpoints: Sequence[Breakpoint]) -> None:
    """Validate that breakpoint widths are ordered and non-negative."""
    if not breakpoints:
        raise ValueError("At least one breakpoint is required.")

    previous = -1

    for breakpoint in breakpoints:
        if breakpoint.min_width < 0:
            raise ValueError("Breakpoint widths cannot be negative.")

        if breakpoint.min_width < previous:
            raise ValueError("Breakpoints must be ordered by minimum width.")

        previous = breakpoint.min_width


def get_layout_mode(
    viewport_width: float,
    breakpoints: Sequence[Breakpoint] = DEFAULT_BREAKPOINTS,
) -> str:
    """
    Determine the active responsive layout mode.

    Example:
        375  -> mobile
        768  -> tablet
        1024 -> desktop
        1440 -> wide
    """
    if viewport_width < 0:
        raise ValueError("Viewport width cannot be negative.")

    validate_breakpoints(breakpoints)

    active = breakpoints[0].name

    for breakpoint in breakpoints:
        if viewport_width >= breakpoint.min_width:
            active = breakpoint.name
        else:
            break

    return active


def demonstrate_breakpoints() -> None:
    """Show how the active layout mode changes with viewport width."""
    print_section("2. BREAKPOINTS")

    test_widths = [320, 375, 480, 600, 768, 899, 900, 1024, 1199, 1200, 1440]

    print("Viewport width -> active layout mode")

    for width in test_widths:
        mode = get_layout_mode(width)
        print(f"{width:>4}px -> {mode}")


# ============================================================================
# 3. MOBILE-FIRST DESIGN
# ============================================================================

MOBILE_FIRST_EXPLANATION = """
Mobile-first CSS starts with the smallest practical layout and progressively
adds capabilities as more viewport space becomes available.

A typical structure is:

    Base rules
        -> small-screen layout

    @media (min-width: 600px)
        -> tablet enhancements

    @media (min-width: 900px)
        -> desktop enhancements

This approach naturally encourages:
- simple document flow,
- readable content,
- touch-friendly controls,
- smaller initial CSS complexity,
- progressive enhancement,
- fewer assumptions about large screens.

It does not mean that mobile users receive a reduced-quality experience.
It means that the essential experience is established first.
"""


def mobile_first_card_columns(viewport_width: float) -> int:
    """
    Return the number of content columns in a mobile-first card grid.

    The design starts with one column and progressively increases columns.
    """
    if viewport_width < 0:
        raise ValueError("Viewport width cannot be negative.")

    if viewport_width >= 1200:
        return 4
    if viewport_width >= 900:
        return 3
    if viewport_width >= 600:
        return 2
    return 1


def demonstrate_mobile_first() -> None:
    """Demonstrate progressive enhancement from one column to four."""
    print_section("3. MOBILE-FIRST LAYOUT")

    print(textwrap.dedent(MOBILE_FIRST_EXPLANATION).strip())

    for width in (360, 599, 600, 899, 900, 1199, 1200, 1600):
        columns = mobile_first_card_columns(width)
        print(f"{width:>4}px viewport -> {columns} content column(s)")


# ============================================================================
# 4. CSS MEDIA QUERY MODEL
# ============================================================================

@dataclass(frozen=True)
class MediaQueryCondition:
    """
    Simplified representation of common responsive media-query conditions.

    This model is useful for understanding the logic before writing CSS.
    """

    min_width: Optional[int] = None
    max_width: Optional[int] = None
    orientation: Optional[str] = None

    def matches(self, width: int, height: int) -> bool:
        """Return True when the viewport satisfies all supplied conditions."""
        if width <= 0 or height <= 0:
            raise ValueError("Viewport dimensions must be positive.")

        if self.min_width is not None and width < self.min_width:
            return False

        if self.max_width is not None and width > self.max_width:
            return False

        if self.orientation is not None:
            actual_orientation = "landscape" if width >= height else "portrait"

            if self.orientation not in {"portrait", "landscape"}:
                raise ValueError("Unsupported orientation.")

            if actual_orientation != self.orientation:
                return False

        return True


def demonstrate_media_queries() -> None:
    """Demonstrate media-query condition matching."""
    print_section("4. MEDIA QUERY LOGIC")

    conditions = {
        "tablet-or-larger": MediaQueryCondition(min_width=600),
        "compact": MediaQueryCondition(max_width=599),
        "portrait-tablet": MediaQueryCondition(
            min_width=600,
            max_width=1024,
            orientation="portrait",
        ),
        "large-landscape": MediaQueryCondition(
            min_width=900,
            orientation="landscape",
        ),
    }

    viewports = [
        (375, 812),
        (768, 1024),
        (1024, 768),
        (1440, 900),
    ]

    for width, height in viewports:
        print(f"\nViewport: {width}x{height}")

        for name, condition in conditions.items():
            print(f"  {name:>20}: {condition.matches(width, height)}")


# ============================================================================
# 5. RESPONSIVE TYPOGRAPHY
# ============================================================================

@dataclass(frozen=True)
class FluidTypography:
    """
    Model a CSS clamp() typography rule.

    CSS equivalent concept:
        font-size: clamp(min-size, preferred-fluid-size, max-size);

    The preferred size here is represented as:
        slope * viewport_width + intercept
    """

    minimum_px: float
    slope_per_px: float
    intercept_px: float
    maximum_px: float

    def __post_init__(self) -> None:
        if self.minimum_px <= 0:
            raise ValueError("Minimum font size must be positive.")

        if self.maximum_px < self.minimum_px:
            raise ValueError("Maximum size cannot be smaller than minimum size.")

    def size_for_viewport(self, viewport_width: float) -> float:
        """Calculate a clamped fluid font size."""
        if viewport_width <= 0:
            raise ValueError("Viewport width must be positive.")

        preferred = (
            self.slope_per_px * viewport_width
            + self.intercept_px
        )

        return max(self.minimum_px, min(preferred, self.maximum_px))


def px_to_rem(px: float, root_font_size: float = 16.0) -> float:
    """Convert CSS pixels to rem using the selected root font size."""
    if root_font_size <= 0:
        raise ValueError("Root font size must be positive.")

    return px / root_font_size


def calculate_reading_width(
    viewport_width: float,
    side_padding: float = 24.0,
    maximum_width: float = 720.0,
) -> float:
    """
    Calculate a readable text measure.

    Responsive text should not simply become infinitely wide on large screens.
    A max-width improves line length and reading comfort.
    """
    if viewport_width <= 0:
        raise ValueError("Viewport width must be positive.")

    if side_padding < 0:
        raise ValueError("Side padding cannot be negative.")

    if maximum_width <= 0:
        raise ValueError("Maximum width must be positive.")

    available = viewport_width - (2 * side_padding)

    return max(0.0, min(available, maximum_width))


def demonstrate_responsive_typography() -> None:
    """Show fluid heading sizes and constrained text widths."""
    print_section("5. RESPONSIVE TYPOGRAPHY")

    heading = FluidTypography(
        minimum_px=28,
        slope_per_px=0.025,
        intercept_px=12,
        maximum_px=56,
    )

    for width in (320, 375, 600, 768, 1024, 1440, 1920):
        size = heading.size_for_viewport(width)
        reading_width = calculate_reading_width(width)

        print(
            f"{width:>4}px -> heading {size:>5.1f}px "
            f"({px_to_rem(size):.2f}rem), "
            f"text measure {reading_width:.0f}px"
        )


# ============================================================================
# 6. RESPONSIVE IMAGES
# ============================================================================

@dataclass(frozen=True)
class ImageCandidate:
    """
    A responsive image candidate.

    width is the intrinsic pixel width of the source image.
    density represents the device-pixel-ratio target.
    """

    name: str
    width: int
    density: float = 1.0

    def __post_init__(self) -> None:
        if self.width <= 0:
            raise ValueError("Image width must be positive.")

        if self.density <= 0:
            raise ValueError("Image density must be positive.")


def select_best_image_candidate(
    candidates: Sequence[ImageCandidate],
    rendered_width: float,
    device_pixel_ratio: float = 1.0,
) -> ImageCandidate:
    """
    Select the smallest source that can satisfy the required physical pixels.

    This approximates the purpose of responsive image source selection.
    Browsers use much richer algorithms for srcset/sizes selection, but this
    model makes the core concept explicit.
    """
    if not candidates:
        raise ValueError("At least one image candidate is required.")

    if rendered_width <= 0:
        raise ValueError("Rendered width must be positive.")

    if device_pixel_ratio <= 0:
        raise ValueError("Device pixel ratio must be positive.")

    required_width = rendered_width * device_pixel_ratio

    ordered = sorted(
        candidates,
        key=lambda candidate: candidate.width * candidate.density,
    )

    for candidate in ordered:
        if candidate.width * candidate.density >= required_width:
            return candidate

    return ordered[-1]


def generate_srcset(candidates: Sequence[ImageCandidate]) -> str:
    """Generate a width-descriptor srcset string."""
    if not candidates:
        raise ValueError("At least one image candidate is required.")

    return ", ".join(
        f"{candidate.name} {candidate.width}w"
        for candidate in sorted(candidates, key=lambda item: item.width)
    )


def demonstrate_responsive_images() -> None:
    """Demonstrate responsive image candidate selection."""
    print_section("6. RESPONSIVE IMAGES")

    candidates = [
        ImageCandidate("hero-480.jpg", 480),
        ImageCandidate("hero-768.jpg", 768),
        ImageCandidate("hero-1200.jpg", 1200),
        ImageCandidate("hero-1600.jpg", 1600),
        ImageCandidate("hero-2400.jpg", 2400),
    ]

    print("Generated srcset:")
    print(generate_srcset(candidates))

    scenarios = [
        (320, 1.0),
        (375, 2.0),
        (768, 1.0),
        (900, 2.0),
        (1200, 1.0),
        (1440, 2.0),
    ]

    for rendered_width, dpr in scenarios:
        selected = select_best_image_candidate(
            candidates,
            rendered_width,
            dpr,
        )

        print(
            f"Rendered: {rendered_width}px, DPR: {dpr:.1f} "
            f"-> {selected.name}"
        )


# ============================================================================
# 7. IMAGE ASPECT RATIO AND CROPPING
# ============================================================================

@dataclass(frozen=True)
class ImageDimensions:
    """Represent intrinsic image dimensions."""

    width: int
    height: int

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Image dimensions must be positive.")

    @property
    def aspect_ratio(self) -> float:
        return self.width / self.height


def calculate_cover_crop(
    image: ImageDimensions,
    container_width: float,
    container_height: float,
) -> Tuple[float, float]:
    """
    Calculate scaled image dimensions for CSS object-fit: cover.

    The result preserves aspect ratio while fully covering the container.
    """
    if container_width <= 0 or container_height <= 0:
        raise ValueError("Container dimensions must be positive.")

    scale = max(
        container_width / image.width,
        container_height / image.height,
    )

    return image.width * scale, image.height * scale


def demonstrate_image_cropping() -> None:
    """Show how object-fit: cover changes rendered dimensions."""
    print_section("7. IMAGE ASPECT RATIO AND COVER")

    source = ImageDimensions(2400, 1600)

    containers = [
        (320, 180),
        (375, 240),
        (768, 400),
        (1200, 500),
    ]

    print(f"Source aspect ratio: {source.aspect_ratio:.3f}")

    for width, height in containers:
        rendered = calculate_cover_crop(source, width, height)

        print(
            f"Container {width}x{height} -> "
            f"rendered {rendered[0]:.1f}x{rendered[1]:.1f}"
        )


# ============================================================================
# 8. CSS ARCHITECTURE FOR RESPONSIVE DESIGN
# ============================================================================

RESPONSIVE_CSS = """
/*
 * Responsive Web Design Reference Implementation
 *
 * Strategy:
 * 1. Base rules are mobile-first.
 * 2. Layout expands with min-width media queries.
 * 3. Grid uses flexible tracks instead of device-specific assumptions.
 * 4. Typography uses clamp() for fluid scaling.
 * 5. Images use width: 100%, height: auto, and object-fit where required.
 */

:root {
  --content-max: 72rem;
  --space-1: 0.5rem;
  --space-2: 0.75rem;
  --space-3: 1rem;
  --space-4: 1.5rem;
  --space-5: 2rem;
  --text-size: 1rem;
  --heading-size: clamp(1.75rem, 4vw + 0.5rem, 3.5rem);
}

*,
*::before,
*::after {
  box-sizing: border-box;
}

html {
  font-size: 100%;
  scroll-behavior: smooth;
}

body {
  margin: 0;
  font-family:
    system-ui,
    -apple-system,
    BlinkMacSystemFont,
    "Segoe UI",
    sans-serif;
  font-size: var(--text-size);
  line-height: 1.6;
}

img {
  display: block;
  max-width: 100%;
  height: auto;
}

.page-shell {
  width: min(100% - 2rem, var(--content-max));
  margin-inline: auto;
}

.content-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--space-4);
}

.cards {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--space-3);
}

.hero-title {
  font-size: var(--heading-size);
  line-height: 1.05;
}

.card-image {
  width: 100%;
  aspect-ratio: 16 / 9;
  object-fit: cover;
}

@media (min-width: 600px) {
  .cards {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (min-width: 900px) {
  .content-grid {
    grid-template-columns: minmax(0, 2fr) minmax(16rem, 1fr);
  }

  .cards {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (min-width: 1200px) {
  .cards {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}

@media (prefers-reduced-motion: reduce) {
  html {
    scroll-behavior: auto;
  }

  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
"""


def validate_css_has_mobile_first_structure(css: str) -> List[str]:
    """
    Perform simple static checks against the demonstration CSS.

    This is not a CSS parser. It intentionally checks only architectural
    characteristics useful for teaching responsive design.
    """
    errors: List[str] = []

    if "grid-template-columns: 1fr;" not in css:
        errors.append("Base layout should define a single-column mobile layout.")

    if "@media (min-width: 600px)" not in css:
        errors.append("Tablet enhancement media query is missing.")

    if "@media (min-width: 900px)" not in css:
        errors.append("Desktop enhancement media query is missing.")

    if "clamp(" not in css:
        errors.append("Fluid typography using clamp() is missing.")

    if "max-width: 100%" not in css:
        errors.append("Responsive image max-width rule is missing.")

    if "aspect-ratio:" not in css:
        errors.append("Aspect-ratio handling is missing.")

    return errors


# ============================================================================
# 9. RESPONSIVE HTML GENERATION
# ============================================================================

def generate_demo_html() -> str:
    """
    Generate a complete HTML document using responsive design principles.

    The document demonstrates:
    - viewport configuration,
    - semantic structure,
    - responsive navigation,
    - fluid typography,
    - responsive grid,
    - responsive images,
    - accessible controls,
    - reduced-motion preference support.
    """
    cards = []

    for number in range(1, 9):
        cards.append(
            f"""
            <article class="card">
                <img
                    class="card-image"
                    src="https://picsum.photos/seed/responsive{number}/800/450"
                    srcset="
                        https://picsum.photos/seed/responsive{number}/480/270 480w,
                        https://picsum.photos/seed/responsive{number}/800/450 800w,
                        https://picsum.photos/seed/responsive{number}/1200/675 1200w
                    "
                    sizes="
                        (min-width: 1200px) 25vw,
                        (min-width: 900px) 33vw,
                        (min-width: 600px) 50vw,
                        100vw
                    "
                    alt="Responsive demonstration image {number}"
                    loading="lazy"
                    width="1200"
                    height="675"
                >
                <div class="card-body">
                    <h2>Responsive Card {number}</h2>
                    <p>
                        This card participates in a mobile-first grid that
                        progressively adds columns as space becomes available.
                    </p>
                </div>
            </article>
            """
        )

    return textwrap.dedent(
        f"""\
        <!doctype html>
        <html lang="en">
        <head>
            <meta charset="utf-8">
            <meta
                name="viewport"
                content="width=device-width, initial-scale=1"
            >
            <title>Responsive Web Design Laboratory</title>
            <style>
                {RESPONSIVE_CSS}

                body {{
                    background: #0b1020;
                    color: #edf2f7;
                }}

                .site-header {{
                    padding-block: 1rem;
                    border-bottom: 1px solid #334155;
                }}

                .navigation {{
                    display: flex;
                    flex-wrap: wrap;
                    gap: 1rem;
                    align-items: center;
                    justify-content: space-between;
                }}

                .navigation-links {{
                    display: flex;
                    flex-wrap: wrap;
                    gap: 0.75rem;
                    padding: 0;
                    margin: 0;
                    list-style: none;
                }}

                .hero {{
                    padding-block: clamp(2rem, 8vw, 7rem);
                }}

                .hero p {{
                    max-width: 45rem;
                    font-size: clamp(1rem, 1.5vw, 1.25rem);
                }}

                .card {{
                    overflow: hidden;
                    border: 1px solid #334155;
                    border-radius: 1rem;
                    background: #111827;
                }}

                .card-body {{
                    padding: 1rem;
                }}

                a {{
                    color: #93c5fd;
                }}

                :focus-visible {{
                    outline: 3px solid #fbbf24;
                    outline-offset: 3px;
                }}
            </style>
        </head>
        <body>
            <header class="site-header">
                <div class="page-shell navigation">
                    <strong>Responsive Lab</strong>
                    <nav aria-label="Primary navigation">
                        <ul class="navigation-links">
                            <li><a href="#principles">Principles</a></li>
                            <li><a href="#cards">Cards</a></li>
                            <li><a href="#images">Images</a></li>
                        </ul>
                    </nav>
                </div>
            </header>

            <main>
                <section class="page-shell hero" id="principles">
                    <p>Mobile-first responsive architecture</p>
                    <h1 class="hero-title">
                        One content system, many viewport sizes
                    </h1>
                    <p>
                        This page uses fluid typography, flexible grids,
                        semantic HTML, responsive images, and progressive
                        enhancement.
                    </p>
                </section>

                <section class="page-shell" id="cards">
                    <div class="cards">
                        {"".join(cards)}
                    </div>
                </section>

                <section class="page-shell hero" id="images">
                    <h2>Responsive image strategy</h2>
                    <picture>
                        <source
                            media="(min-width: 900px)"
                            srcset="
                                https://picsum.photos/seed/large/1600/700
                            "
                        >
                        <source
                            media="(min-width: 600px)"
                            srcset="
                                https://picsum.photos/seed/medium/1000/650
                            "
                        >
                        <img
                            src="https://picsum.photos/seed/small/700/700"
                            alt="Example image demonstrating picture sources"
                            width="700"
                            height="700"
                            loading="lazy"
                        >
                    </picture>
                </section>
            </main>
        </body>
        </html>
        """
    )


# ============================================================================
# 10. ACCESSIBILITY AND INTERACTION CONSIDERATIONS
# ============================================================================

def calculate_touch_target_size(
    width_px: float,
    height_px: float,
    minimum_px: float = 44.0,
) -> bool:
    """
    Check whether a control meets a configurable touch-target dimension.

    The 44px value is a practical implementation target. Accessibility
    requirements can vary by platform and standard, so this helper intentionally
    exposes the threshold instead of treating one number as universal law.
    """
    if width_px <= 0 or height_px <= 0:
        raise ValueError("Control dimensions must be positive.")

    if minimum_px <= 0:
        raise ValueError("Minimum target size must be positive.")

    return width_px >= minimum_px and height_px >= minimum_px


def demonstrate_accessibility() -> None:
    """Demonstrate responsive interaction considerations."""
    print_section("10. ACCESSIBILITY AND RESPONSIVE INTERACTION")

    targets = [
        ("small icon", 32, 32),
        ("compact button", 44, 44),
        ("large button", 120, 48),
    ]

    for name, width, height in targets:
        acceptable = calculate_touch_target_size(width, height)
        print(f"{name:>16}: {width}x{height} -> target check: {acceptable}")

    print(
        "\nResponsive design should also consider keyboard focus, readable "
        "contrast, zoom, reduced motion, semantic HTML, and content order."
    )


# ============================================================================
# 11. PERFORMANCE MODEL
# ============================================================================

@dataclass(frozen=True)
class Resource:
    """Represent a downloadable image resource for a simple bandwidth model."""

    name: str
    kilobytes: float

    def __post_init__(self) -> None:
        if self.kilobytes < 0:
            raise ValueError("Resource size cannot be negative.")


def estimate_transfer_time(
    resource: Resource,
    megabits_per_second: float,
) -> float:
    """
    Estimate ideal transfer time in seconds.

    Real networks have latency, protocol overhead, congestion, server delay,
    compression effects, and other variables, so this is intentionally a
    simplified educational model.
    """
    if megabits_per_second <= 0:
        raise ValueError("Network speed must be positive.")

    megabits = resource.kilobytes * 8 / 1000

    return megabits / megabits_per_second


def demonstrate_performance() -> None:
    """Compare a desktop-sized image with an appropriately sized mobile image."""
    print_section("11. PERFORMANCE")

    desktop = Resource("hero-2400.jpg", 900)
    mobile = Resource("hero-480.jpg", 120)

    network_speed = 10

    desktop_time = estimate_transfer_time(desktop, network_speed)
    mobile_time = estimate_transfer_time(mobile, network_speed)

    print(f"Desktop resource: {desktop.kilobytes} KB")
    print(f"Mobile resource:  {mobile.kilobytes} KB")
    print(f"Estimated desktop transfer: {desktop_time:.3f} seconds")
    print(f"Estimated mobile transfer:  {mobile_time:.3f} seconds")

    print(
        "\nResponsive images can reduce unnecessary transfer by supplying "
        "sources appropriate to rendered dimensions."
    )


# ============================================================================
# 12. EDGE CASES
# ============================================================================

def safe_css_length(value: float, unit: str) -> str:
    """
    Convert a numeric value to a safe CSS length.

    This demonstrates validation before data becomes CSS.
    """
    if not math.isfinite(value):
        raise ValueError("CSS length must be finite.")

    if value < 0:
        raise ValueError("This helper accepts non-negative lengths.")

    allowed_units = {"px", "rem", "em", "%", "vw", "vh", "ch"}

    if unit not in allowed_units:
        raise ValueError(f"Unsupported CSS unit: {unit}")

    return f"{value:g}{unit}"


def demonstrate_edge_cases() -> None:
    """Exercise important invalid inputs."""
    print_section("12. EDGE CASES AND VALIDATION")

    valid_values = [
        (16, "px"),
        (1.5, "rem"),
        (80, "%"),
        (5, "vw"),
    ]

    for value, unit in valid_values:
        print(f"{value} {unit} -> {safe_css_length(value, unit)}")

    invalid_values = [
        (-1, "px"),
        (10, "invalid"),
        (math.inf, "px"),
    ]

    for value, unit in invalid_values:
        try:
            safe_css_length(value, unit)
        except ValueError as error:
            print(f"Rejected {value} {unit}: {error}")


# ============================================================================
# 13. COMPLETE RESPONSIVE DESIGN CONFIGURATION
# ============================================================================

@dataclass
class ResponsiveDesignSystem:
    """
    Central configuration for a responsive design system.

    Centralizing design decisions makes responsive behavior easier to test and
    maintain than scattering arbitrary device-specific values throughout code.
    """

    breakpoints: Tuple[Breakpoint, ...] = DEFAULT_BREAKPOINTS
    content_max_width: int = 1152
    base_font_size: float = 16.0
    spacing_scale: Tuple[float, ...] = (
        4,
        8,
        12,
        16,
        24,
        32,
        48,
        64,
    )

    def validate(self) -> None:
        """Validate design-system configuration."""
        validate_breakpoints(self.breakpoints)

        if self.content_max_width <= 0:
            raise ValueError("Content max width must be positive.")

        if self.base_font_size <= 0:
            raise ValueError("Base font size must be positive.")

        if any(value <= 0 for value in self.spacing_scale):
            raise ValueError("Spacing values must be positive.")

        if tuple(sorted(self.spacing_scale)) != self.spacing_scale:
            raise ValueError("Spacing scale must be ordered.")


def demonstrate_design_system() -> None:
    """Validate and inspect a complete responsive design system."""
    print_section("13. RESPONSIVE DESIGN SYSTEM")

    system = ResponsiveDesignSystem()
    system.validate()

    print(f"Content maximum: {system.content_max_width}px")
    print(f"Root font size: {system.base_font_size}px")
    print(f"Spacing scale: {system.spacing_scale}")

    for width in (375, 768, 1024, 1440):
        mode = get_layout_mode(width, system.breakpoints)
        columns = mobile_first_card_columns(width)
        print(f"{width}px -> {mode}, {columns} card columns")


# ============================================================================
# 14. RESPONSIVE DESIGN CHECKLIST
# ============================================================================

RESPONSIVE_CHECKLIST = [
    "Use a viewport meta element for normal responsive browser behavior.",
    "Start with a usable small-screen layout.",
    "Choose breakpoints where content needs a change.",
    "Prefer flexible grids and intrinsic sizing over fixed device layouts.",
    "Use min-width media queries for mobile-first enhancement.",
    "Use rem, em, %, vw, vh, ch, and clamp() appropriately.",
    "Keep text measure constrained on large screens.",
    "Use responsive images with srcset and sizes where appropriate.",
    "Provide width and height attributes to reduce layout shifts.",
    "Use picture when art direction or media-specific sources are required.",
    "Use object-fit when images must fill a constrained media box.",
    "Lazy-load below-the-fold images when appropriate.",
    "Do not hide essential content merely because the viewport is small.",
    "Keep controls usable with touch, mouse, keyboard, and zoom.",
    "Respect prefers-reduced-motion.",
    "Test intermediate widths rather than only popular device widths.",
    "Test portrait and landscape orientations.",
    "Check long text, localization, and unusual content lengths.",
    "Avoid unnecessary horizontal scrolling.",
    "Measure actual performance instead of assuming that responsive means fast.",
]


def print_checklist() -> None:
    """Print the implementation checklist."""
    print_section("14. RESPONSIVE DESIGN CHECKLIST")

    for number, item in enumerate(RESPONSIVE_CHECKLIST, start=1):
        print(f"{number:>2}. {item}")


# ============================================================================
# 15. AUTOMATED TESTS
# ============================================================================

class ResponsiveDesignTests(unittest.TestCase):
    """Automated tests for the educational responsive-design model."""

    def test_breakpoint_selection(self) -> None:
        self.assertEqual(get_layout_mode(375), "mobile")
        self.assertEqual(get_layout_mode(768), "tablet")
        self.assertEqual(get_layout_mode(1024), "desktop")
        self.assertEqual(get_layout_mode(1440), "wide")

    def test_grid_progression(self) -> None:
        self.assertEqual(mobile_first_card_columns(375), 1)
        self.assertEqual(mobile_first_card_columns(600), 2)
        self.assertEqual(mobile_first_card_columns(900), 3)
        self.assertEqual(mobile_first_card_columns(1200), 4)

    def test_media_query(self) -> None:
        query = MediaQueryCondition(min_width=600)
        self.assertFalse(query.matches(599, 800))
        self.assertTrue(query.matches(600, 800))

    def test_orientation(self) -> None:
        portrait = MediaQueryCondition(orientation="portrait")
        landscape = MediaQueryCondition(orientation="landscape")

        self.assertTrue(portrait.matches(600, 800))
        self.assertFalse(portrait.matches(800, 600))
        self.assertTrue(landscape.matches(800, 600))

    def test_fluid_typography_is_clamped(self) -> None:
        typography = FluidTypography(20, 0.05, 0, 40)

        self.assertEqual(typography.size_for_viewport(100), 20)
        self.assertEqual(typography.size_for_viewport(500), 25)
        self.assertEqual(typography.size_for_viewport(1000), 40)

    def test_reading_width_is_constrained(self) -> None:
        self.assertEqual(calculate_reading_width(400), 352)
        self.assertEqual(calculate_reading_width(2000), 720)

    def test_responsive_image_selection(self) -> None:
        candidates = [
            ImageCandidate("480", 480),
            ImageCandidate("800", 800),
            ImageCandidate("1200", 1200),
        ]

        self.assertEqual(
            select_best_image_candidate(candidates, 400).name,
            "480",
        )

        self.assertEqual(
            select_best_image_candidate(candidates, 600).name,
            "800",
        )

        self.assertEqual(
            select_best_image_candidate(candidates, 600, 2).name,
            "1200",
        )

    def test_image_crop_preserves_aspect_ratio(self) -> None:
        source = ImageDimensions(1600, 900)
        rendered_width, rendered_height = calculate_cover_crop(
            source,
            800,
            800,
        )

        self.assertGreaterEqual(rendered_width, 800)
        self.assertGreaterEqual(rendered_height, 800)

    def test_touch_target(self) -> None:
        self.assertFalse(calculate_touch_target_size(32, 32))
        self.assertTrue(calculate_touch_target_size(44, 44))

    def test_css_validation(self) -> None:
        errors = validate_css_has_mobile_first_structure(RESPONSIVE_CSS)
        self.assertEqual(errors, [])

    def test_css_length_validation(self) -> None:
        self.assertEqual(safe_css_length(1.5, "rem"), "1.5rem")

        with self.assertRaises(ValueError):
            safe_css_length(-1, "px")

        with self.assertRaises(ValueError):
            safe_css_length(1, "invalid")


def run_tests() -> bool:
    """Run the embedded test suite and return whether all tests pass."""
    print_section("15. AUTOMATED TESTS")

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        ResponsiveDesignTests
    )

    result = unittest.TextTestRunner(verbosity=1).run(suite)

    return result.wasSuccessful()


# ============================================================================
# 16. GENERATE AN EXAMPLE PROJECT FILE
# ============================================================================

def write_demo_project(destination: Optional[Path] = None) -> Path:
    """
    Write the generated responsive page to a temporary or supplied location.

    A temporary location is used by default so the script remains
    self-contained and does not unexpectedly modify the working directory.
    """
    if destination is None:
        directory = Path(tempfile.mkdtemp(prefix="responsive-web-design-"))
        destination = directory / "index.html"
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)

    destination.write_text(
        generate_demo_html(),
        encoding="utf-8",
    )

    return destination


# ============================================================================
# 17. SECURITY AND PRODUCTION CONSIDERATIONS
# ============================================================================

SECURITY_AND_PRODUCTION_NOTES = [
    (
        "Do not treat responsive CSS as a security boundary. "
        "CSS visibility does not protect sensitive data."
    ),
    (
        "Do not place secrets in HTML, CSS, JavaScript, image URLs, or "
        "client-visible responsive configuration."
    ),
    (
        "Validate server-side data independently of client-side validation. "
        "Responsive forms still require normal server-side security controls."
    ),
    (
        "Use HTTPS for production websites and use appropriate security "
        "headers at the server or platform level."
    ),
    (
        "Use trusted image sources and appropriate content-security policies "
        "when the application architecture supports them."
    ),
    (
        "Optimize image dimensions and formats without sacrificing required "
        "visual quality or accessibility."
    ),
    (
        "Test layout behavior with browser zoom and text enlargement rather "
        "than assuming viewport width is the only accessibility variable."
    ),
]


def print_security_notes() -> None:
    """Display production and security considerations."""
    print_section("16. SECURITY AND PRODUCTION")

    for item in SECURITY_AND_PRODUCTION_NOTES:
        print(f"- {item}")


# ============================================================================
# 18. MAIN STUDY PROGRAM
# ============================================================================

def main() -> None:
    """Run the complete responsive web design study program."""
    print("=" * 78)
    print("RESPONSIVE WEB DESIGN STUDY PROGRAM")
    print("=" * 78)

    print_terms()
    demonstrate_breakpoints()
    demonstrate_mobile_first()
    demonstrate_media_queries()
    demonstrate_responsive_typography()
    demonstrate_responsive_images()
    demonstrate_image_cropping()

    print_section("8. REFERENCE RESPONSIVE CSS")
    print(RESPONSIVE_CSS.strip())

    print_section("9. GENERATED HTML")
    html = generate_demo_html()
    print(f"Generated document length: {len(html):,} characters")
    print("HTML includes:")
    print("  - viewport configuration")
    print("  - semantic sections")
    print("  - mobile-first grid")
    print("  - responsive typography")
    print("  - srcset and sizes")
    print("  - picture art direction")
    print("  - lazy loading")
    print("  - accessible focus styling")
    print("  - reduced-motion support")

    demonstrate_accessibility()
    demonstrate_performance()
    demonstrate_edge_cases()
    demonstrate_design_system()
    print_checklist()
    print_security_notes()

    output_path = write_demo_project()

    print_section("17. GENERATED DEMONSTRATION FILE")
    print(f"Responsive HTML written to: {output_path}")

    tests_passed = run_tests()

    print_section("18. STUDY PROGRAM STATUS")
    if tests_passed:
        print("All responsive-design model tests passed.")
    else:
        print("Some tests failed. Inspect the test output above.")

    print("\nKey principle:")
    print(
        "Responsive design is a content-driven system: start with a usable "
        "small-screen experience, then enhance the layout as space permits."
    )


if __name__ == "__main__":
    main()
