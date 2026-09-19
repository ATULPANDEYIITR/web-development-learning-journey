"""
CSS Backgrounds and Borders
============================

A self-contained study companion for:
- background colors
- background images
- background positioning, sizing, repetition, and attachment
- multiple backgrounds
- gradients
- borders and border styles
- border radius
- outlines
- shadows
- clipping
- background-origin and background-clip
- CSS box model relationships
- practical UI composition
- accessibility, performance, and security considerations

The examples are represented as Python data structures and generators so that
the file remains executable without requiring a browser or external package.
The generated CSS can be copied into an HTML document for visual inspection.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from textwrap import dedent
from typing import Iterable
import math
import re
import unittest


# ============================================================================
# 1. FUNDAMENTALS
# ============================================================================

print("=" * 78)
print("CSS BACKGROUNDS AND BORDERS")
print("=" * 78)


def explain_fundamentals() -> None:
    """Print the conceptual model used throughout the examples."""
    concepts = {
        "background": (
            "Painted behind an element's content and padding. CSS backgrounds "
            "can contain colors, images, gradients, and multiple layers."
        ),
        "border": (
            "A box edge surrounding the padding and content areas. It has "
            "width, style, and color."
        ),
        "border-radius": (
            "Rounds the corners of an element's border box. It can also clip "
            "backgrounds when combined with background clipping behavior."
        ),
        "box-shadow": (
            "Draws one or more shadows around an element's border box. A "
            "shadow is visual decoration and does not normally affect layout."
        ),
        "outline": (
            "A line drawn outside the border. It does not consume normal box "
            "space and is commonly useful for keyboard focus."
        ),
        "clipping": (
            "Controls which part of an element's painting remains visible."
        ),
        "gradient": (
            "A CSS image generated from color transitions instead of a bitmap "
            "file."
        ),
    }

    for name, description in concepts.items():
        print(f"\n{name}:")
        print(f"  {description}")


explain_fundamentals()


# ============================================================================
# 2. CSS DECLARATION MODEL
# ============================================================================

@dataclass
class CSSRule:
    """A small representation of a CSS rule."""

    selector: str
    declarations: dict[str, str] = field(default_factory=dict)

    def render(self) -> str:
        body = "\n".join(
            f"  {property_name}: {value};"
            for property_name, value in self.declarations.items()
        )
        return f"{self.selector} {{\n{body}\n}}"


def render_stylesheet(rules: Iterable[CSSRule]) -> str:
    """Render multiple CSS rules as a stylesheet."""
    return "\n\n".join(rule.render() for rule in rules)


basic_rule = CSSRule(
    ".card",
    {
        "background-color": "#111827",
        "color": "#f9fafb",
        "border": "1px solid #374151",
        "border-radius": "16px",
        "padding": "24px",
    },
)

print("\n--- Basic CSS rule ---")
print(basic_rule.render())


# ============================================================================
# 3. COLOR BACKGROUNDS
# ============================================================================

color_examples = {
    "named": "background-color: navy;",
    "hex": "background-color: #0f172a;",
    "rgb": "background-color: rgb(15 23 42);",
    "rgba": "background-color: rgb(15 23 42 / 0.85);",
    "hsl": "background-color: hsl(222 47% 11%);",
    "transparent": "background-color: transparent;",
}

print("\n--- Background color forms ---")
for syntax_name, declaration in color_examples.items():
    print(f"{syntax_name:12}: {declaration}")


# ============================================================================
# 4. BACKGROUND IMAGES
# ============================================================================

background_image_rule = CSSRule(
    ".hero",
    {
        "background-image": "url('hero.jpg')",
        "background-repeat": "no-repeat",
        "background-position": "center",
        "background-size": "cover",
    },
)

print("\n--- Background image ---")
print(background_image_rule.render())


def describe_background_size(
    container_width: float,
    container_height: float,
    image_width: float,
    image_height: float,
) -> dict[str, float]:
    """
    Compare the scale factors used by background-size: cover and contain.

    cover:
        Scale enough to completely cover the container.
        Some image content may extend outside the container.

    contain:
        Scale enough for the entire image to fit.
        Empty space may remain around the image.
    """
    if min(container_width, container_height, image_width, image_height) <= 0:
        raise ValueError("All dimensions must be positive.")

    cover_scale = max(
        container_width / image_width,
        container_height / image_height,
    )
    contain_scale = min(
        container_width / image_width,
        container_height / image_height,
    )

    return {
        "cover_width": image_width * cover_scale,
        "cover_height": image_height * cover_scale,
        "contain_width": image_width * contain_scale,
        "contain_height": image_height * contain_scale,
    }


size_result = describe_background_size(1200, 500, 1600, 900)

print("\n--- cover vs contain calculation ---")
for key, value in size_result.items():
    print(f"{key:16}: {value:.2f}px")


# ============================================================================
# 5. BACKGROUND POSITION
# ============================================================================

background_position_examples = [
    "left top",
    "center center",
    "right bottom",
    "50% 25%",
    "20px 40px",
]

print("\n--- Background positions ---")
for position in background_position_examples:
    print(f"background-position: {position};")


# ============================================================================
# 6. BACKGROUND REPEAT
# ============================================================================

repeat_values = [
    "repeat",
    "repeat-x",
    "repeat-y",
    "no-repeat",
    "space",
    "round",
]

print("\n--- Background repetition ---")
for repeat_value in repeat_values:
    print(f"background-repeat: {repeat_value};")


# ============================================================================
# 7. BACKGROUND ATTACHMENT
# ============================================================================

attachment_examples = [
    "scroll",
    "local",
    "fixed",
]

print("\n--- Background attachment ---")
for attachment in attachment_examples:
    print(f"background-attachment: {attachment};")


# ============================================================================
# 8. MULTIPLE BACKGROUNDS
# ============================================================================

multiple_backgrounds = CSSRule(
    ".dashboard",
    {
        "background-image": (
            "linear-gradient(rgb(15 23 42 / 0.88), rgb(15 23 42 / 0.88)), "
            "url('dashboard.jpg')"
        ),
        "background-position": "center, center",
        "background-size": "cover, cover",
        "background-repeat": "no-repeat, no-repeat",
    },
)

print("\n--- Multiple backgrounds ---")
print(multiple_backgrounds.render())

print(
    "\nImportant rule: with comma-separated background layers, "
    "the first image is painted on top of later image layers."
)


# ============================================================================
# 9. GRADIENTS
# ============================================================================

gradient_examples = {
    "linear": (
        "background: linear-gradient(90deg, #0ea5e9, #8b5cf6);"
    ),
    "linear_with_stops": (
        "background: linear-gradient("
        "90deg, #0ea5e9 0%, #8b5cf6 55%, #ec4899 100%);"
    ),
    "radial": (
        "background: radial-gradient(circle at center, #38bdf8, #0f172a);"
    ),
    "conic": (
        "background: conic-gradient("
        "from 45deg, #ef4444, #f59e0b, #22c55e, #3b82f6, #ef4444);"
    ),
    "repeating_linear": (
        "background: repeating-linear-gradient("
        "45deg, #111827 0 10px, #1f2937 10px 20px);"
    ),
    "repeating_radial": (
        "background: repeating-radial-gradient("
        "circle, #111827 0 8px, #374151 8px 16px);"
    ),
}

print("\n--- Gradient forms ---")
for gradient_type, declaration in gradient_examples.items():
    print(f"{gradient_type:20}: {declaration}")


def interpolate_color(
    start: tuple[int, int, int],
    end: tuple[int, int, int],
    progress: float,
) -> tuple[int, int, int]:
    """
    Demonstrate the conceptual interpolation behind a simple two-color
    gradient. CSS engines perform the actual rendering.
    """
    if not 0 <= progress <= 1:
        raise ValueError("progress must be between 0 and 1")

    return tuple(
        round(start[index] + (end[index] - start[index]) * progress)
        for index in range(3)
    )


print("\n--- Gradient color interpolation ---")
for progress in (0, 0.25, 0.5, 0.75, 1):
    color = interpolate_color((14, 165, 233), (139, 92, 246), progress)
    print(f"{progress:4.2f}: rgb{color}")


# ============================================================================
# 10. BORDERS
# ============================================================================

border_styles = [
    "none",
    "solid",
    "dashed",
    "dotted",
    "double",
    "groove",
    "ridge",
    "inset",
    "outset",
]

print("\n--- Border styles ---")
for style in border_styles:
    print(f"border: 2px {style} #64748b;")


border_rule = CSSRule(
    ".panel",
    {
        "border-width": "2px",
        "border-style": "solid",
        "border-color": "#475569",
        "border-top-color": "#38bdf8",
        "border-right-color": "#8b5cf6",
        "border-bottom-color": "#ec4899",
        "border-left-color": "#22c55e",
    },
)

print("\n--- Individual border sides ---")
print(border_rule.render())


# ============================================================================
# 11. BORDER WIDTH AND BOX DIMENSIONS
# ============================================================================

def border_box_dimensions(
    content_width: float,
    content_height: float,
    padding_horizontal: float,
    padding_vertical: float,
    border_horizontal: float,
    border_vertical: float,
    box_sizing: str = "content-box",
) -> tuple[float, float]:
    """
    Calculate the rendered border-box dimensions for the common box-sizing
    models.

    content-box:
        Declared width represents content width.

    border-box:
        Declared width represents the complete border box. This function
        receives the content dimensions and therefore demonstrates how the
        corresponding outer size would be assembled.
    """
    if any(
        value < 0
        for value in (
            content_width,
            content_height,
            padding_horizontal,
            padding_vertical,
            border_horizontal,
            border_vertical,
        )
    ):
        raise ValueError("Dimensions cannot be negative.")

    if box_sizing not in {"content-box", "border-box"}:
        raise ValueError("box_sizing must be content-box or border-box")

    if box_sizing == "content-box":
        return (
            content_width + padding_horizontal + border_horizontal,
            content_height + padding_vertical + border_vertical,
        )

    return (
        content_width + padding_horizontal + border_horizontal,
        content_height + padding_vertical + border_vertical,
    )


print("\n--- Box model calculation ---")
outer_width, outer_height = border_box_dimensions(
    content_width=300,
    content_height=150,
    padding_horizontal=40,
    padding_vertical=32,
    border_horizontal=4,
    border_vertical=4,
)
print(f"Border-box width : {outer_width}px")
print(f"Border-box height: {outer_height}px")

print(
    "\nNote: CSS box-sizing changes how a declared width/height is interpreted. "
    "The calculation above illustrates how content, padding, and borders "
    "contribute to an outer size."
)


# ============================================================================
# 12. BORDER RADIUS
# ============================================================================

radius_examples = {
    "small": "border-radius: 6px;",
    "medium": "border-radius: 12px;",
    "large": "border-radius: 24px;",
    "pill": "border-radius: 9999px;",
    "circle": "border-radius: 50%;",
    "per_corner": "border-radius: 4px 12px 20px 28px;",
    "elliptical": "border-radius: 30px / 15px;",
}

print("\n--- Border-radius forms ---")
for radius_name, declaration in radius_examples.items():
    print(f"{radius_name:12}: {declaration}")


# ============================================================================
# 13. BORDER IMAGE
# ============================================================================

border_image_rule = CSSRule(
    ".decorative-frame",
    {
        "border": "12px solid transparent",
        "border-image-source": "url('frame.png')",
        "border-image-slice": "30",
        "border-image-width": "1",
        "border-image-repeat": "round",
    },
)

print("\n--- Border image ---")
print(border_image_rule.render())


# ============================================================================
# 14. OUTLINE
# ============================================================================

outline_rule = CSSRule(
    ".keyboard-focus",
    {
        "outline": "3px solid #38bdf8",
        "outline-offset": "4px",
    },
)

print("\n--- Outline ---")
print(outline_rule.render())

print(
    "\nAccessibility principle: do not remove visible keyboard focus without "
    "providing an equally visible alternative."
)


# ============================================================================
# 15. SHADOWS
# ============================================================================

shadow_examples = {
    "simple": "box-shadow: 0 4px 12px rgb(0 0 0 / 0.25);",
    "spread": "box-shadow: 0 8px 24px 4px rgb(0 0 0 / 0.20);",
    "inset": "box-shadow: inset 0 2px 8px rgb(0 0 0 / 0.30);",
    "multiple": (
        "box-shadow: 0 2px 6px rgb(0 0 0 / 0.18), "
        "0 12px 30px rgb(0 0 0 / 0.14);"
    ),
}

print("\n--- Box shadows ---")
for shadow_name, declaration in shadow_examples.items():
    print(f"{shadow_name:10}: {declaration}")


@dataclass
class BoxShadow:
    """Structured representation of a CSS box-shadow."""

    offset_x: float
    offset_y: float
    blur_radius: float
    spread_radius: float
    color: str
    inset: bool = False

    def __post_init__(self) -> None:
        if self.blur_radius < 0:
            raise ValueError("Blur radius cannot be negative.")

    def to_css(self) -> str:
        inset_text = "inset " if self.inset else ""
        return (
            f"box-shadow: {inset_text}"
            f"{self.offset_x}px {self.offset_y}px "
            f"{self.blur_radius}px {self.spread_radius}px {self.color};"
        )


shadow = BoxShadow(0, 8, 24, 0, "rgb(0 0 0 / 0.2)")
print("\nStructured shadow:")
print(shadow.to_css())


# ============================================================================
# 16. TEXT SHADOW
# ============================================================================

text_shadow_rule = CSSRule(
    ".headline",
    {
        "text-shadow": "0 3px 8px rgb(0 0 0 / 0.35)",
    },
)

print("\n--- Text shadow ---")
print(text_shadow_rule.render())


# ============================================================================
# 17. BACKGROUND CLIPPING AND ORIGIN
# ============================================================================

clipping_rule = CSSRule(
    ".clipped-card",
    {
        "background-color": "#0f172a",
        "background-image": "linear-gradient(135deg, #06b6d4, #7c3aed)",
        "background-clip": "padding-box",
        "background-origin": "border-box",
        "border": "3px solid transparent",
        "border-radius": "18px",
    },
)

print("\n--- Background origin and clip ---")
print(clipping_rule.render())

clip_values = [
    "border-box",
    "padding-box",
    "content-box",
    "text",
]

print("\nCommon background-clip values:")
for value in clip_values:
    print(f"  {value}")


# ============================================================================
# 18. BORDER RADIUS + CLIPPING
# ============================================================================

rounded_media_rule = CSSRule(
    ".thumbnail",
    {
        "width": "320px",
        "height": "200px",
        "border-radius": "20px",
        "overflow": "hidden",
        "background-image": "url('thumbnail.jpg')",
        "background-size": "cover",
        "background-position": "center",
    },
)

print("\n--- Rounded media surface ---")
print(rounded_media_rule.render())

print(
    "\nSubtle distinction: border-radius defines rounded corners for the box. "
    "overflow: hidden can clip child content to the rounded shape, while "
    "background-clip controls where the element's own background is painted."
)


# ============================================================================
# 19. CSS CUSTOM PROPERTIES
# ============================================================================

theme_rule = CSSRule(
    ":root",
    {
        "--surface": "#0f172a",
        "--surface-raised": "#1e293b",
        "--border": "#334155",
        "--accent": "#38bdf8",
        "--radius": "16px",
        "--shadow": "0 12px 32px rgb(0 0 0 / 0.22)",
    },
)

card_using_variables = CSSRule(
    ".theme-card",
    {
        "background": "var(--surface-raised)",
        "border": "1px solid var(--border)",
        "border-radius": "var(--radius)",
        "box-shadow": "var(--shadow)",
    },
)

print("\n--- Custom properties ---")
print(render_stylesheet([theme_rule, card_using_variables]))


# ============================================================================
# 20. LAYERS AND SHORTHAND
# ============================================================================

shorthand_rule = CSSRule(
    ".banner",
    {
        "background": (
            "linear-gradient(rgb(2 6 23 / 0.70), rgb(2 6 23 / 0.70)), "
            "url('banner.jpg') center / cover no-repeat"
        ),
    },
)

print("\n--- Background shorthand ---")
print(shorthand_rule.render())

print(
    "\nBackground shorthand can combine color, image, position, size, "
    "repeat, attachment, origin, and clip. The slash separates position "
    "from size when both appear in the shorthand."
)


# ============================================================================
# 21. RESPONSIVE BACKGROUND PATTERN
# ============================================================================

responsive_css = dedent(
    """
    .responsive-hero {
      min-height: 60vh;
      background:
        linear-gradient(rgb(2 6 23 / 0.72), rgb(2 6 23 / 0.72)),
        url("hero-wide.jpg") center / cover no-repeat;
    }

    @media (max-width: 700px) {
      .responsive-hero {
        min-height: 70vh;
        background-image:
          linear-gradient(rgb(2 6 23 / 0.78), rgb(2 6 23 / 0.78)),
          url("hero-mobile.jpg");
      }
    }
    """
).strip()

print("\n--- Responsive background example ---")
print(responsive_css)


# ============================================================================
# 22. VALIDATION HELPERS
# ============================================================================

HEX_COLOR_PATTERN = re.compile(
    r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{4}|"
    r"[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$"
)


def validate_hex_color(value: str) -> bool:
    """Validate common hexadecimal CSS colors."""
    return bool(HEX_COLOR_PATTERN.fullmatch(value))


def validate_radius(value: str) -> bool:
    """Validate simple non-negative CSS radius values."""
    return bool(re.fullmatch(r"(?:0|[0-9]+(?:\.[0-9]+)?)(?:px|rem|em|%)", value))


def validate_url(value: str) -> bool:
    """
    Basic validation for a local CSS url() source.

    This deliberately rejects javascript: URLs. A production CSS pipeline
    should use a stronger parser and an allowlist appropriate to the system.
    """
    normalized = value.strip().lower()
    return (
        normalized.startswith(("https://", "http://", "/", "./", "../"))
        and "javascript:" not in normalized
    )


print("\n--- Validation examples ---")
for color in ("#fff", "#112233", "#112233cc", "#xyz", "red"):
    print(f"{color:10} valid hex: {validate_hex_color(color)}")

for radius in ("16px", "1.5rem", "50%", "-2px", "large"):
    print(f"{radius:10} valid radius: {validate_radius(radius)}")

for url in ("images/hero.jpg", "https://example.com/image.jpg", "javascript:alert(1)"):
    print(f"{url:32} valid URL: {validate_url(url)}")


# ============================================================================
# 23. ACCESSIBILITY AND PERFORMANCE CHECKS
# ============================================================================

@dataclass
class VisualDesignAudit:
    """Simple rule-based audit for background and border choices."""

    has_focus_indicator: bool
    text_over_image_has_overlay: bool
    decorative_image_is_nonessential: bool
    uses_reasonable_shadow_count: bool
    avoids_unnecessary_fixed_backgrounds: bool

    def issues(self) -> list[str]:
        issues: list[str] = []

        if not self.has_focus_indicator:
            issues.append(
                "Provide a visible keyboard focus indicator."
            )

        if not self.text_over_image_has_overlay:
            issues.append(
                "Check text contrast over background imagery."
            )

        if not self.decorative_image_is_nonessential:
            issues.append(
                "Do not rely on CSS background images for essential information."
            )

        if not self.uses_reasonable_shadow_count:
            issues.append(
                "Reduce excessive or expensive shadow layers."
            )

        if not self.avoids_unnecessary_fixed_backgrounds:
            issues.append(
                "Review background-attachment: fixed for mobile and performance."
            )

        return issues


audit = VisualDesignAudit(
    has_focus_indicator=True,
    text_over_image_has_overlay=True,
    decorative_image_is_nonessential=True,
    uses_reasonable_shadow_count=True,
    avoids_unnecessary_fixed_backgrounds=True,
)

print("\n--- Visual design audit ---")
if not audit.issues():
    print("No issues detected by the basic rule set.")
else:
    for issue in audit.issues():
        print(f"- {issue}")


# ============================================================================
# 24. COMPLETE COMPONENT GENERATOR
# ============================================================================

def create_component_styles() -> str:
    """
    Build a realistic card component using backgrounds, borders, radius,
    shadows, gradients, and clipping.
    """
    rules = [
        CSSRule(
            ".product-card",
            {
                "position": "relative",
                "overflow": "hidden",
                "background": "#0f172a",
                "border": "1px solid #334155",
                "border-radius": "20px",
                "box-shadow": "0 16px 40px rgb(0 0 0 / 0.22)",
            },
        ),
        CSSRule(
            ".product-card::before",
            {
                "content": "''",
                "position": "absolute",
                "inset": "0",
                "background": (
                    "linear-gradient("
                    "135deg, rgb(56 189 248 / 0.18), "
                    "transparent 45%, rgb(139 92 246 / 0.18)"
                    ")"
                ),
                "pointer-events": "none",
            },
        ),
        CSSRule(
            ".product-card__media",
            {
                "height": "220px",
                "background": "url('product.jpg') center / cover no-repeat",
                "border-radius": "20px 20px 0 0",
            },
        ),
        CSSRule(
            ".product-card__content",
            {
                "position": "relative",
                "padding": "24px",
                "background": "rgb(15 23 42 / 0.94)",
                "border-top": "1px solid rgb(148 163 184 / 0.18)",
            },
        ),
        CSSRule(
            ".product-card__button",
            {
                "background": "linear-gradient(135deg, #06b6d4, #7c3aed)",
                "border": "1px solid rgb(255 255 255 / 0.14)",
                "border-radius": "9999px",
                "box-shadow": "0 8px 20px rgb(6 182 212 / 0.22)",
                "color": "white",
                "padding": "12px 20px",
            },
        ),
        CSSRule(
            ".product-card__button:focus-visible",
            {
                "outline": "3px solid #f8fafc",
                "outline-offset": "4px",
            },
        ),
    ]

    return render_stylesheet(rules)


component_css = create_component_styles()

print("\n--- Complete component CSS ---")
print(component_css)


# ============================================================================
# 25. GENERATING A SELF-CONTAINED HTML DEMO
# ============================================================================

def create_html_demo() -> str:
    """
    Create a browser-ready demonstration page.

    The page references an external image URL only as an optional visual
    demonstration. The core CSS remains usable without that image.
    """
    css = create_component_styles()

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>CSS Backgrounds and Borders</title>
  <style>
    :root {{
      color-scheme: dark;
      font-family: system-ui, sans-serif;
      background: #020617;
      color: #f8fafc;
    }}

    body {{
      min-height: 100vh;
      margin: 0;
      display: grid;
      place-items: center;
      padding: 32px;
      box-sizing: border-box;
    }}

    {css}
  </style>
</head>
<body>
  <article class="product-card">
    <div class="product-card__media" aria-hidden="true"></div>
    <div class="product-card__content">
      <h1>Background and Border Demo</h1>
      <p>
        A component combining a background image, gradient overlay, rounded
        corners, border, shadow, and visible keyboard focus.
      </p>
      <button class="product-card__button">Inspect styling</button>
    </div>
  </article>
</body>
</html>
"""
    return html


demo = create_html_demo()

print("\n--- HTML demo generated in memory ---")
print(f"Characters: {len(demo)}")
print("The demo combines the major concepts into one component.")


# ============================================================================
# 26. CSS DESIGN TOKENS
# ============================================================================

@dataclass(frozen=True)
class DesignTokens:
    surface: str = "#0f172a"
    surface_raised: str = "#1e293b"
    border: str = "#334155"
    accent: str = "#38bdf8"
    radius_small: str = "8px"
    radius_medium: str = "16px"
    radius_large: str = "24px"
    shadow_soft: str = "0 8px 24px rgb(0 0 0 / 0.18)"

    def as_css(self) -> str:
        return dedent(
            f"""
            :root {{
              --surface: {self.surface};
              --surface-raised: {self.surface_raised};
              --border: {self.border};
              --accent: {self.accent};
              --radius-small: {self.radius_small};
              --radius-medium: {self.radius_medium};
              --radius-large: {self.radius_large};
              --shadow-soft: {self.shadow_soft};
            }}
            """
        ).strip()


tokens = DesignTokens()
print("\n--- Design token system ---")
print(tokens.as_css())


# ============================================================================
# 27. RESPONSIVE IMAGE STRATEGY
# ============================================================================

def choose_background_asset(viewport_width: int) -> str:
    """
    Select a conceptual image asset based on viewport width.

    In real CSS, <picture> or responsive image techniques are often preferable
    when the image is content. CSS backgrounds are suitable for decoration.
    """
    if viewport_width <= 480:
        return "hero-mobile.webp"
    if viewport_width <= 1024:
        return "hero-tablet.webp"
    return "hero-desktop.webp"


print("\n--- Responsive asset selection ---")
for width in (360, 768, 1440):
    print(f"{width}px viewport -> {choose_background_asset(width)}")


# ============================================================================
# 28. ADVANCED EDGE CASES
# ============================================================================

def calculate_pill_radius(height: float) -> float:
    """A pill normally uses at least half the element's height as radius."""
    if height <= 0:
        raise ValueError("Height must be positive.")
    return height / 2


def clamp(value: float, minimum: float, maximum: float) -> float:
    """Python equivalent of the concept represented by CSS clamp()."""
    if minimum > maximum:
        raise ValueError("minimum cannot exceed maximum")
    return max(minimum, min(value, maximum))


print("\n--- Edge-case calculations ---")
print(f"Pill radius for 40px high element: {calculate_pill_radius(40)}px")
print(f"clamp(24, 16, 32) -> {clamp(24, 16, 32)}")
print(f"clamp(8, 16, 32)  -> {clamp(8, 16, 32)}")
print(f"clamp(48, 16, 32) -> {clamp(48, 16, 32)}")


# ============================================================================
# 29. COMMON MISTAKES AS MACHINE-CHECKABLE RULES
# ============================================================================

@dataclass
class CSSMistake:
    mistake: str
    correction: str


common_mistakes = [
    CSSMistake(
        "Using background images for essential text or information.",
        "Use semantic HTML content and use backgrounds primarily for decoration.",
    ),
    CSSMistake(
        "Using background-size: cover without checking focal-point cropping.",
        "Test multiple aspect ratios and adjust background-position.",
    ),
    CSSMistake(
        "Removing focus outlines globally.",
        "Keep a visible :focus-visible treatment.",
    ),
    CSSMistake(
        "Using huge uncompressed background images.",
        "Resize, compress, modernize, and serve appropriately sized assets.",
    ),
    CSSMistake(
        "Applying many large blurred shadows to many elements.",
        "Use a restrained shadow system and test rendering performance.",
    ),
    CSSMistake(
        "Confusing background-clip with overflow clipping.",
        "Understand whether you are clipping the element's background or its children.",
    ),
]

print("\n--- Common mistakes and corrections ---")
for item in common_mistakes:
    print(f"\nMistake:     {item.mistake}")
    print(f"Correction:  {item.correction}")


# ============================================================================
# 30. TESTS
# ============================================================================

class TestCSSStudyExamples(unittest.TestCase):
    """Tests for the executable conceptual helpers."""

    def test_hex_colors(self) -> None:
        self.assertTrue(validate_hex_color("#fff"))
        self.assertTrue(validate_hex_color("#12345678"))
        self.assertFalse(validate_hex_color("#12"))

    def test_radius(self) -> None:
        self.assertTrue(validate_radius("16px"))
        self.assertTrue(validate_radius("50%"))
        self.assertFalse(validate_radius("-1px"))

    def test_interpolation(self) -> None:
        self.assertEqual(
            interpolate_color((0, 0, 0), (100, 200, 50), 0),
            (0, 0, 0),
        )
        self.assertEqual(
            interpolate_color((0, 0, 0), (100, 200, 50), 1),
            (100, 200, 50),
        )

    def test_shadow(self) -> None:
        self.assertIn("box-shadow:", shadow.to_css())

    def test_background_size(self) -> None:
        result = describe_background_size(100, 100, 200, 100)
        self.assertAlmostEqual(result["cover_width"], 200)
        self.assertAlmostEqual(result["cover_height"], 100)
        self.assertAlmostEqual(result["contain_width"], 100)
        self.assertAlmostEqual(result["contain_height"], 50)

    def test_component_css(self) -> None:
        css = create_component_styles()
        self.assertIn("border-radius", css)
        self.assertIn("background", css)
        self.assertIn("box-shadow", css)


def run_tests() -> None:
    """Run the study-file unit tests without requiring pytest."""
    print("\n--- Running Python tests ---")
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TestCSSStudyExamples
    )
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)


run_tests()


# ============================================================================
# 31. FINAL REFERENCE TABLE
# ============================================================================

reference = {
    "background-color": "Sets the background color.",
    "background-image": "Adds one or more background images.",
    "background-position": "Controls the initial position of a background image.",
    "background-size": "Controls rendered background image dimensions.",
    "background-repeat": "Controls repetition of a background image.",
    "background-attachment": "Controls how a background participates in scrolling.",
    "background-origin": "Defines the box used to position a background image.",
    "background-clip": "Defines the region where the background is painted.",
    "background": "Shorthand for multiple background properties.",
    "border": "Shorthand for border width, style, and color.",
    "border-radius": "Rounds box corners.",
    "border-image": "Uses an image as a border.",
    "outline": "Paints an outline outside the border.",
    "box-shadow": "Creates shadows around the box.",
    "text-shadow": "Creates shadows behind text glyphs.",
    "overflow": "Controls clipping and overflow of descendants/content.",
}

print("\n--- Quick reference ---")
for property_name, purpose in reference.items():
    print(f"{property_name:22} {purpose}")


# ============================================================================
# 32. PRODUCTION CHECKLIST
# ============================================================================

production_checklist = [
    "Use semantic HTML rather than putting essential information in backgrounds.",
    "Check contrast whenever text is placed over an image or gradient.",
    "Keep keyboard focus visible.",
    "Use appropriately sized, compressed background assets.",
    "Prefer modern image formats when browser support permits.",
    "Test cover cropping at narrow and wide aspect ratios.",
    "Use background layers deliberately and document complex combinations.",
    "Use border-radius consistently as part of a design system.",
    "Avoid excessive shadow blur and excessive shadow layers.",
    "Use CSS custom properties for repeated visual tokens.",
    "Treat externally controlled image URLs as untrusted input.",
    "Avoid javascript: URLs and unsafe CSS injection paths.",
    "Test high-contrast, reduced-motion, zoom, and keyboard interaction.",
    "Inspect mobile rendering when using fixed backgrounds.",
    "Use developer tools to inspect computed styles and box geometry.",
]

print("\n--- Production checklist ---")
for number, item in enumerate(production_checklist, start=1):
    print(f"{number:02}. {item}")


print("\n" + "=" * 78)
print("Study file completed successfully.")
print("=" * 78)
