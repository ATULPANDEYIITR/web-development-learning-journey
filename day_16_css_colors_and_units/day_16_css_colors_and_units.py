"""
CSS Colors and Units
====================

A standalone Python study companion for understanding CSS colors and CSS units.

The program models and demonstrates:

- Named colors
- HEX colors
- RGB and RGBA
- HSL and HSLA
- Opacity and alpha compositing
- Absolute units such as px
- Relative units such as %, em, rem
- Viewport units such as vh, vw, vmin, vmax
- Unit conversion and validation
- Color conversion between RGB and HSL
- Contrast calculations
- Responsive sizing calculations
- CSS value generation
- Edge cases and common mistakes
- Practical responsive design examples

Python does not execute CSS. These examples calculate and generate CSS values so
that the underlying mathematics and behavior can be studied independently.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import floor, ceil
from typing import Optional
import re


# ---------------------------------------------------------------------------
# SECTION 1: FUNDAMENTALS
# ---------------------------------------------------------------------------

def section(title: str) -> None:
    """Print a readable section heading."""
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def explain(message: str) -> None:
    """Print explanatory text used by the executable lesson."""
    print(message)


section("1. What CSS colors and units represent")

explain(
    "CSS colors describe visual color values. CSS units describe numerical "
    "dimensions, distances, proportions, angles, time, resolution, or other "
    "quantities. This program focuses on colors and common length units."
)

explain(
    "Examples of CSS color syntax include #3498db, rgb(52 152 219), "
    "hsl(204 70% 53%), and named colors such as red."
)

explain(
    "Examples of CSS length syntax include 16px, 50%, 1.25em, 1rem, "
    "100vh, 50vw, 50vmin, and 50vmax."
)


# ---------------------------------------------------------------------------
# SECTION 2: COLOR REPRESENTATIONS
# ---------------------------------------------------------------------------

NAMED_COLORS = {
    "black": "#000000",
    "white": "#ffffff",
    "red": "#ff0000",
    "green": "#008000",
    "blue": "#0000ff",
    "yellow": "#ffff00",
    "cyan": "#00ffff",
    "magenta": "#ff00ff",
    "gray": "#808080",
    "orange": "#ffa500",
    "purple": "#800080",
    "transparent": "#00000000",
}


def normalize_hex(value: str) -> str:
    """Normalize common HEX forms to lowercase six-digit HEX."""
    value = value.strip().lower()

    if value.startswith("#"):
        value = value[1:]

    if len(value) == 3:
        if not re.fullmatch(r"[0-9a-f]{3}", value):
            raise ValueError("Invalid three-digit HEX color.")
        value = "".join(character * 2 for character in value)

    elif len(value) == 4:
        if not re.fullmatch(r"[0-9a-f]{4}", value):
            raise ValueError("Invalid four-digit HEX color.")
        # Four-digit HEX is RRGGBBAA after expansion.
        value = "".join(character * 2 for character in value)

    elif len(value) in (6, 8):
        if not re.fullmatch(r"[0-9a-f]+", value):
            raise ValueError("HEX color contains invalid characters.")
    else:
        raise ValueError("HEX color must contain 3, 4, 6, or 8 digits.")

    return "#" + value


def hex_to_rgba(value: str) -> tuple[int, int, int, float]:
    """Convert #RGB, #RGBA, #RRGGBB, or #RRGGBBAA to RGBA."""
    normalized = normalize_hex(value)[1:]

    if len(normalized) == 6:
        red = int(normalized[0:2], 16)
        green = int(normalized[2:4], 16)
        blue = int(normalized[4:6], 16)
        alpha = 1.0
    else:
        red = int(normalized[0:2], 16)
        green = int(normalized[2:4], 16)
        blue = int(normalized[4:6], 16)
        alpha = int(normalized[6:8], 16) / 255

    return red, green, blue, alpha


def rgba_to_hex(
    red: int,
    green: int,
    blue: int,
    alpha: Optional[float] = None,
) -> str:
    """Convert RGB or RGBA values to HEX."""
    validate_rgb(red, green, blue)

    result = f"#{red:02x}{green:02x}{blue:02x}"

    if alpha is not None:
        validate_alpha(alpha)
        alpha_byte = round(alpha * 255)
        result += f"{alpha_byte:02x}"

    return result


def validate_rgb(red: int, green: int, blue: int) -> None:
    """Validate RGB channels."""
    for channel_name, value in (
        ("red", red),
        ("green", green),
        ("blue", blue),
    ):
        if not isinstance(value, int):
            raise TypeError(f"{channel_name} must be an integer.")
        if not 0 <= value <= 255:
            raise ValueError(f"{channel_name} must be between 0 and 255.")


def validate_alpha(alpha: float) -> None:
    """Validate an alpha value in the range 0..1."""
    if not 0 <= alpha <= 1:
        raise ValueError("Alpha must be between 0 and 1.")


section("2. Named colors")

for name in ("red", "blue", "orange", "white", "black"):
    print(f"{name:10} -> {NAMED_COLORS[name]}")

explain(
    "Named colors are convenient but limited compared with numeric color "
    "models. HEX, RGB, and HSL provide much more precise control."
)


section("3. HEX colors")

hex_examples = [
    "#000000",
    "#ffffff",
    "#3498db",
    "#abc",
    "#123456",
    "#336699cc",
]

for value in hex_examples:
    rgba = hex_to_rgba(value)
    print(f"{value:12} -> RGBA {rgba}")

explain(
    "A six-digit HEX value stores red, green, and blue channels as hexadecimal "
    "bytes. #RRGGBB therefore contains three values from 00 through FF."
)

explain(
    "The eight-digit form #RRGGBBAA adds an alpha channel. The alpha byte "
    "ranges from 00 for fully transparent to FF for fully opaque."
)


section("4. RGB and RGBA")

rgb_examples = [
    (255, 0, 0),
    (0, 128, 255),
    (52, 152, 219),
    (255, 165, 0),
]

for red, green, blue in rgb_examples:
    print(
        f"rgb({red} {green} {blue}) -> "
        f"{rgba_to_hex(red, green, blue)}"
    )

print("RGBA:", rgba_to_hex(52, 152, 219, 0.50))

explain(
    "RGB represents additive red, green, and blue channels. In modern CSS, "
    "rgb() can use space-separated channels and an optional slash for alpha."
)


# ---------------------------------------------------------------------------
# SECTION 3: HSL
# ---------------------------------------------------------------------------

def rgb_to_hsl(
    red: int,
    green: int,
    blue: int,
) -> tuple[float, float, float]:
    """
    Convert RGB 0..255 to HSL.

    Hue is returned in degrees.
    Saturation and lightness are returned as percentages.
    """
    validate_rgb(red, green, blue)

    r = red / 255
    g = green / 255
    b = blue / 255

    maximum = max(r, g, b)
    minimum = min(r, g, b)
    difference = maximum - minimum

    lightness = (maximum + minimum) / 2

    if difference == 0:
        hue = 0
        saturation = 0
    else:
        saturation = difference / (
            1 - abs(2 * lightness - 1)
        )

        if maximum == r:
            hue = 60 * (((g - b) / difference) % 6)
        elif maximum == g:
            hue = 60 * (((b - r) / difference) + 2)
        else:
            hue = 60 * (((r - g) / difference) + 4)

    return hue % 360, saturation * 100, lightness * 100


def hsl_to_rgb(
    hue: float,
    saturation: float,
    lightness: float,
) -> tuple[int, int, int]:
    """
    Convert HSL to RGB.

    Hue: degrees.
    Saturation: 0..100.
    Lightness: 0..100.
    """
    if not 0 <= saturation <= 100:
        raise ValueError("Saturation must be between 0 and 100.")
    if not 0 <= lightness <= 100:
        raise ValueError("Lightness must be between 0 and 100.")

    hue %= 360
    saturation /= 100
    lightness /= 100

    chroma = (
        (1 - abs(2 * lightness - 1)) * saturation
    )

    intermediate = chroma * (
        1 - abs(((hue / 60) % 2) - 1)
    )

    match_value = lightness - chroma / 2

    if hue < 60:
        r1, g1, b1 = chroma, intermediate, 0
    elif hue < 120:
        r1, g1, b1 = intermediate, chroma, 0
    elif hue < 180:
        r1, g1, b1 = 0, chroma, intermediate
    elif hue < 240:
        r1, g1, b1 = 0, intermediate, chroma
    elif hue < 300:
        r1, g1, b1 = intermediate, 0, chroma
    else:
        r1, g1, b1 = chroma, 0, intermediate

    return (
        round((r1 + match_value) * 255),
        round((g1 + match_value) * 255),
        round((b1 + match_value) * 255),
    )


section("5. HSL colors")

colors = [
    (255, 0, 0),
    (52, 152, 219),
    (46, 204, 113),
    (155, 89, 182),
    (241, 196, 15),
]

for rgb in colors:
    hsl = rgb_to_hsl(*rgb)
    print(f"RGB {rgb} -> HSL {hsl[0]:.1f}°, {hsl[1]:.1f}%, {hsl[2]:.1f}%")

hsl_examples = [
    (0, 100, 50),
    (210, 70, 53),
    (120, 60, 50),
    (0, 0, 50),
]

for hsl in hsl_examples:
    rgb = hsl_to_rgb(*hsl)
    print(f"HSL {hsl} -> RGB {rgb}")

explain(
    "HSL separates hue, saturation, and lightness. Hue identifies the basic "
    "color around a 360-degree color wheel. Saturation describes color intensity. "
    "Lightness controls how light or dark the color is."
)


# ---------------------------------------------------------------------------
# SECTION 4: ALPHA AND OPACITY
# ---------------------------------------------------------------------------

def composite_channel(
    foreground: int,
    background: int,
    alpha: float,
) -> int:
    """Composite one channel using standard source-over alpha blending."""
    validate_alpha(alpha)
    return round(
        foreground * alpha + background * (1 - alpha)
    )


def alpha_composite(
    foreground: tuple[int, int, int],
    background: tuple[int, int, int],
    alpha: float,
) -> tuple[int, int, int]:
    """Composite an RGB foreground over an RGB background."""
    validate_rgb(*foreground)
    validate_rgb(*background)
    validate_alpha(alpha)

    return tuple(
        composite_channel(foreground[index], background[index], alpha)
        for index in range(3)
    )


section("6. Opacity and alpha")

foreground = (255, 0, 0)
background = (255, 255, 255)

for alpha in (0, 0.25, 0.5, 0.75, 1):
    result = alpha_composite(foreground, background, alpha)
    print(f"Red over white at alpha={alpha:.2f} -> {result}")

explain(
    "Alpha controls transparency of a color. An alpha value of 0 is fully "
    "transparent and 1 is fully opaque."
)

explain(
    "The CSS opacity property affects an entire element and its descendants. "
    "An alpha value inside a color affects that specific color. These are "
    "not interchangeable when descendants or compositing are involved."
)


# ---------------------------------------------------------------------------
# SECTION 5: CSS UNITS
# ---------------------------------------------------------------------------

def css_px(value: float) -> str:
    """Return a CSS pixel value."""
    return f"{value:g}px"


def css_percent(value: float) -> str:
    """Return a CSS percentage value."""
    return f"{value:g}%"


def css_em(value: float) -> str:
    """Return an em value."""
    return f"{value:g}em"


def css_rem(value: float) -> str:
    """Return a rem value."""
    return f"{value:g}rem"


def css_vh(value: float) -> str:
    """Return a viewport-height value."""
    return f"{value:g}vh"


def css_vw(value: float) -> str:
    """Return a viewport-width value."""
    return f"{value:g}vw"


def css_vmin(value: float) -> str:
    """Return a viewport-minimum value."""
    return f"{value:g}vmin"


def css_vmax(value: float) -> str:
    """Return a viewport-maximum value."""
    return f"{value:g}vmax"


section("7. CSS length units")

units = [
    ("px", "CSS pixel"),
    ("%", "percentage"),
    ("em", "relative to the relevant font size"),
    ("rem", "relative to the root element font size"),
    ("vh", "1% of viewport height"),
    ("vw", "1% of viewport width"),
    ("vmin", "1% of the smaller viewport dimension"),
    ("vmax", "1% of the larger viewport dimension"),
]

for unit, meaning in units:
    print(f"{unit:5} -> {meaning}")


# ---------------------------------------------------------------------------
# SECTION 6: PIXEL CALCULATIONS
# ---------------------------------------------------------------------------

section("8. px calculations")

example_px_values = [1, 8, 16, 24, 32, 48, 64]

for value in example_px_values:
    print(f"{value:2}px -> CSS: {css_px(value)}")

explain(
    "px is an absolute CSS length unit in the CSS layout model. It is useful "
    "for precise borders, icons, controls, and dimensions where fixed sizing "
    "is appropriate. A CSS pixel is not necessarily one physical device pixel."
)


# ---------------------------------------------------------------------------
# SECTION 7: PERCENTAGES
# ---------------------------------------------------------------------------

def percentage_of(value: float, reference: float) -> float:
    """Calculate a percentage of a reference dimension."""
    return reference * value / 100


section("9. Percentage units")

parent_width = 1200
parent_height = 800

for percentage in (25, 50, 75, 100):
    print(
        f"width: {percentage}% of {parent_width}px -> "
        f"{percentage_of(percentage, parent_width):g}px"
    )

explain(
    "A percentage does not have one universal reference. The reference depends "
    "on the property and layout context. For width, percentages commonly refer "
    "to the containing block's width. Height percentages can require a definite "
    "containing-block height."
)


# ---------------------------------------------------------------------------
# SECTION 8: EM AND REM
# ---------------------------------------------------------------------------

def em_to_px(em_value: float, current_font_size: float) -> float:
    """Convert em to pixels using the relevant font size."""
    return em_value * current_font_size


def rem_to_px(rem_value: float, root_font_size: float = 16) -> float:
    """Convert rem to pixels using the root font size."""
    return rem_value * root_font_size


section("10. em and rem")

root_font_size = 16
parent_font_size = 20

for value in (0.75, 1, 1.25, 1.5, 2):
    print(
        f"{value:g}rem -> {rem_to_px(value, root_font_size):g}px; "
        f"{value:g}em in a {parent_font_size}px context -> "
        f"{em_to_px(value, parent_font_size):g}px"
    )

explain(
    "rem is based on the root element's font size. em is relative to the "
    "relevant font-size context and can therefore compound through nesting."
)

nested_parent = 20
nested_child = em_to_px(1.5, nested_parent)
nested_grandchild = em_to_px(1.5, nested_child)

print("Nested em example:")
print(f"Parent font size:       {nested_parent}px")
print(f"Child 1.5em:            {nested_child:g}px")
print(f"Grandchild 1.5em:       {nested_grandchild:g}px")

explain(
    "This compounding behavior is one reason rem is often easier to reason "
    "about for a global type scale."
)


# ---------------------------------------------------------------------------
# SECTION 9: VIEWPORT UNITS
# ---------------------------------------------------------------------------

@dataclass
class Viewport:
    """Represent a browser viewport for unit calculations."""
    width: float
    height: float

    @property
    def vmin(self) -> float:
        return min(self.width, self.height)

    @property
    def vmax(self) -> float:
        return max(self.width, self.height)

    def vh(self, value: float) -> float:
        return self.height * value / 100

    def vw(self, value: float) -> float:
        return self.width * value / 100

    def vmin_value(self, value: float) -> float:
        return self.vmin * value / 100

    def vmax_value(self, value: float) -> float:
        return self.vmax * value / 100


section("11. Viewport units")

desktop = Viewport(width=1440, height=900)
mobile = Viewport(width=390, height=844)

for name, viewport in (
    ("desktop", desktop),
    ("mobile", mobile),
):
    print(f"\n{name}: {viewport.width}x{viewport.height}")
    print(f"10vh   -> {viewport.vh(10):g}px")
    print(f"10vw   -> {viewport.vw(10):g}px")
    print(f"10vmin -> {viewport.vmin_value(10):g}px")
    print(f"10vmax -> {viewport.vmax_value(10):g}px")

explain(
    "vh is based on viewport height and vw on viewport width. vmin uses the "
    "smaller viewport dimension, while vmax uses the larger dimension."
)

explain(
    "Modern CSS also has dynamic, small, and large viewport variants such as "
    "dvh, svh, and lvh. They are useful when mobile browser UI changes the "
    "visual viewport. This study program focuses on the requested traditional "
    "vh, vw, vmin, and vmax units."
)


# ---------------------------------------------------------------------------
# SECTION 10: RESPONSIVE DESIGN MODEL
# ---------------------------------------------------------------------------

@dataclass
class ResponsiveCard:
    """Model a responsive card using several CSS unit strategies."""
    max_width_px: float
    width_percent: float
    horizontal_padding_rem: float

    def css_width(self) -> str:
        return (
            f"width: {css_percent(self.width_percent)}; "
            f"max-width: {css_px(self.max_width_px)};"
        )

    def css_padding(self) -> str:
        return (
            f"padding: {css_rem(self.horizontal_padding_rem)};"
        )


section("12. Responsive component calculation")

card = ResponsiveCard(
    max_width_px=720,
    width_percent=92,
    horizontal_padding_rem=1.5,
)

print(card.css_width())
print(card.css_padding())

explain(
    "A common responsive strategy is to combine relative width with a maximum "
    "fixed width. The percentage allows the component to shrink on small screens "
    "while max-width prevents it from becoming excessively wide on large screens."
)


# ---------------------------------------------------------------------------
# SECTION 11: CLAMP-STYLE FLUID SIZING
# ---------------------------------------------------------------------------

def clamp(value: float, minimum: float, maximum: float) -> float:
    """Return value constrained to a minimum and maximum."""
    return max(minimum, min(value, maximum))


def fluid_font_size(
    viewport_width: float,
    preferred_vw: float,
    minimum_px: float,
    maximum_px: float,
) -> float:
    """
    Model a CSS clamp() expression such as:

        clamp(1rem, 2vw, 2rem)

    Here the preferred term is represented by a viewport-width percentage.
    """
    preferred_px = viewport_width * preferred_vw / 100
    return clamp(preferred_px, minimum_px, maximum_px)


section("13. Fluid sizing with clamp-like logic")

for width in (320, 480, 768, 1024, 1440, 1920):
    size = fluid_font_size(
        viewport_width=width,
        preferred_vw=3,
        minimum_px=16,
        maximum_px=48,
    )
    print(f"Viewport {width:4}px -> fluid size {size:5.1f}px")

explain(
    "CSS clamp() is useful when a value should grow with the viewport but "
    "must remain within safe minimum and maximum limits."
)


# ---------------------------------------------------------------------------
# SECTION 12: COLOR PALETTES
# ---------------------------------------------------------------------------

def adjust_lightness(
    rgb: tuple[int, int, int],
    delta: float,
) -> tuple[int, int, int]:
    """Adjust HSL lightness by a percentage amount."""
    hue, saturation, lightness = rgb_to_hsl(*rgb)
    new_lightness = clamp(lightness + delta, 0, 100)
    return hsl_to_rgb(hue, saturation, new_lightness)


def make_palette(base_color: tuple[int, int, int]) -> list[tuple[int, int, int]]:
    """Create a simple lightness-based palette."""
    return [
        adjust_lightness(base_color, -30),
        adjust_lightness(base_color, -15),
        base_color,
        adjust_lightness(base_color, 15),
        adjust_lightness(base_color, 30),
    ]


section("14. Generating a color palette")

base_color = (52, 152, 219)

for color in make_palette(base_color):
    print(color, "->", rgba_to_hex(*color))

explain(
    "HSL is particularly convenient for educational palette generation because "
    "lightness can be changed while preserving hue and saturation."
)


# ---------------------------------------------------------------------------
# SECTION 13: ACCESSIBILITY AND CONTRAST
# ---------------------------------------------------------------------------

def srgb_channel_to_linear(channel: int) -> float:
    """Convert an 8-bit sRGB channel to a linear-light value."""
    normalized = channel / 255
    if normalized <= 0.04045:
        return normalized / 12.92
    return ((normalized + 0.055) / 1.055) ** 2.4


def relative_luminance(rgb: tuple[int, int, int]) -> float:
    """Calculate WCAG-style relative luminance."""
    validate_rgb(*rgb)
    r, g, b = (
        srgb_channel_to_linear(channel)
        for channel in rgb
    )
    return (
        0.2126 * r +
        0.7152 * g +
        0.0722 * b
    )


def contrast_ratio(
    foreground: tuple[int, int, int],
    background: tuple[int, int, int],
) -> float:
    """Calculate the contrast ratio between two opaque RGB colors."""
    first = relative_luminance(foreground)
    second = relative_luminance(background)

    lighter = max(first, second)
    darker = min(first, second)

    return (lighter + 0.05) / (darker + 0.05)


section("15. Color contrast")

contrast_examples = [
    ((0, 0, 0), (255, 255, 255)),
    ((255, 255, 255), (52, 152, 219)),
    ((255, 255, 255), (20, 20, 20)),
    ((30, 30, 30), (240, 240, 240)),
]

for foreground_color, background_color in contrast_examples:
    ratio = contrast_ratio(foreground_color, background_color)
    print(
        f"{rgba_to_hex(*foreground_color)} on "
        f"{rgba_to_hex(*background_color)} -> "
        f"{ratio:.2f}:1"
    )

explain(
    "Contrast ratio is important for readable interfaces. Hue alone does not "
    "guarantee sufficient contrast. Two colors can have very different hues "
    "yet poor text readability if their luminance is too similar."
)


# ---------------------------------------------------------------------------
# SECTION 14: VALIDATION AND EDGE CASES
# ---------------------------------------------------------------------------

section("16. Edge cases and validation")

invalid_values = [
    "#12",
    "#gggggg",
    "#12345",
    "1234567",
]

for value in invalid_values:
    try:
        normalize_hex(value)
        print(value, "unexpectedly accepted")
    except (TypeError, ValueError) as error:
        print(value, "-> rejected:", error)

for rgb in [
    (256, 0, 0),
    (-1, 0, 0),
    (0, 300, 0),
]:
    try:
        validate_rgb(*rgb)
        print(rgb, "unexpectedly accepted")
    except (TypeError, ValueError) as error:
        print(rgb, "-> rejected:", error)

for alpha in (-0.1, 1.1):
    try:
        validate_alpha(alpha)
        print(alpha, "unexpectedly accepted")
    except ValueError as error:
        print(alpha, "-> rejected:", error)


# ---------------------------------------------------------------------------
# SECTION 15: COLOR CLASS
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Color:
    """
    Immutable RGBA color model.

    RGB channels are integers in 0..255.
    Alpha is a float in 0..1.
    """

    red: int
    green: int
    blue: int
    alpha: float = 1.0

    def __post_init__(self) -> None:
        validate_rgb(self.red, self.green, self.blue)
        validate_alpha(self.alpha)

    @classmethod
    def from_hex(cls, value: str) -> "Color":
        red, green, blue, alpha = hex_to_rgba(value)
        return cls(red, green, blue, alpha)

    @classmethod
    def from_hsl(
        cls,
        hue: float,
        saturation: float,
        lightness: float,
        alpha: float = 1.0,
    ) -> "Color":
        red, green, blue = hsl_to_rgb(
            hue,
            saturation,
            lightness,
        )
        return cls(red, green, blue, alpha)

    def to_hex(self) -> str:
        return rgba_to_hex(
            self.red,
            self.green,
            self.blue,
            self.alpha if self.alpha < 1 else None,
        )

    def to_rgb_css(self) -> str:
        if self.alpha == 1:
            return f"rgb({self.red} {self.green} {self.blue})"

        return (
            f"rgb({self.red} {self.green} {self.blue} / "
            f"{self.alpha:g})"
        )

    def to_hsl_css(self) -> str:
        hue, saturation, lightness = rgb_to_hsl(
            self.red,
            self.green,
            self.blue,
        )

        if self.alpha == 1:
            return (
                f"hsl({hue:.1f} {saturation:.1f}% "
                f"{lightness:.1f}%)"
            )

        return (
            f"hsl({hue:.1f} {saturation:.1f}% "
            f"{lightness:.1f}% / {self.alpha:g})"
        )

    def with_alpha(self, alpha: float) -> "Color":
        return Color(
            self.red,
            self.green,
            self.blue,
            alpha,
        )

    def lighten(self, amount: float) -> "Color":
        hue, saturation, lightness = rgb_to_hsl(
            self.red,
            self.green,
            self.blue,
        )

        return Color.from_hsl(
            hue,
            saturation,
            clamp(lightness + amount, 0, 100),
            self.alpha,
        )

    def darken(self, amount: float) -> "Color":
        return self.lighten(-amount)


section("17. Reusable Color abstraction")

brand = Color.from_hex("#3498db")

print("HEX:", brand.to_hex())
print("RGB:", brand.to_rgb_css())
print("HSL:", brand.to_hsl_css())
print("Transparent:", brand.with_alpha(0.4).to_rgb_css())
print("Light:", brand.lighten(15).to_hex())
print("Dark:", brand.darken(15).to_hex())


# ---------------------------------------------------------------------------
# SECTION 16: CSS TOKEN GENERATION
# ---------------------------------------------------------------------------

def generate_css_tokens() -> str:
    """Generate a small CSS custom-property design token set."""
    primary = Color.from_hex("#3498db")
    success = Color.from_hex("#2ecc71")
    danger = Color.from_hex("#e74c3c")
    surface = Color.from_hex("#f5f7fa")
    text = Color.from_hex("#1f2937")

    lines = [
        ":root {",
        f"  --color-primary: {primary.to_hex()};",
        f"  --color-primary-light: {primary.lighten(15).to_hex()};",
        f"  --color-primary-dark: {primary.darken(15).to_hex()};",
        f"  --color-success: {success.to_hex()};",
        f"  --color-danger: {danger.to_hex()};",
        f"  --color-surface: {surface.to_hex()};",
        f"  --color-text: {text.to_hex()};",
        "  --space-1: 0.25rem;",
        "  --space-2: 0.5rem;",
        "  --space-3: 0.75rem;",
        "  --space-4: 1rem;",
        "  --space-6: 1.5rem;",
        "  --space-8: 2rem;",
        "}",
    ]

    return "\n".join(lines)


section("18. CSS custom properties")

print(generate_css_tokens())


# ---------------------------------------------------------------------------
# SECTION 17: PRACTICAL RESPONSIVE PAGE MODEL
# ---------------------------------------------------------------------------

@dataclass
class ResponsiveLayout:
    """Calculate dimensions for a simple responsive interface."""
    viewport: Viewport
    root_font_size: float = 16

    def page_padding(self) -> float:
        """Use 4vw but keep padding between 16px and 48px."""
        return clamp(
            self.viewport.vw(4),
            16,
            48,
        )

    def heading_size(self) -> float:
        """Model clamp(2rem, 5vw, 4rem)."""
        return clamp(
            self.viewport.vw(5),
            2 * self.root_font_size,
            4 * self.root_font_size,
        )

    def hero_height(self) -> float:
        """Model a hero using 70vh."""
        return self.viewport.vh(70)


section("19. Practical responsive layout")

for viewport in (
    Viewport(375, 667),
    Viewport(768, 1024),
    Viewport(1440, 900),
    Viewport(2560, 1440),
):
    layout = ResponsiveLayout(viewport)

    print(
        f"\nViewport: {viewport.width:g}x{viewport.height:g}"
    )
    print(
        f"Page padding: {layout.page_padding():.1f}px"
    )
    print(
        f"Heading size: {layout.heading_size():.1f}px"
    )
    print(
        f"Hero height: {layout.hero_height():.1f}px"
    )


# ---------------------------------------------------------------------------
# SECTION 18: UNIT COMPARISON
# ---------------------------------------------------------------------------

section("20. Unit comparison")

comparison = {
    "px": "Fixed CSS length; useful for precision.",
    "%": "Relative to a property-specific reference.",
    "em": "Relative to the relevant font-size context.",
    "rem": "Relative to the root font size.",
    "vh": "Relative to viewport height.",
    "vw": "Relative to viewport width.",
    "vmin": "Relative to the smaller viewport dimension.",
    "vmax": "Relative to the larger viewport dimension.",
}

for unit, description in comparison.items():
    print(f"{unit:5} | {description}")


# ---------------------------------------------------------------------------
# SECTION 19: COMMON MISTAKES
# ---------------------------------------------------------------------------

section("21. Common mistakes")

mistakes = [
    (
        "Using #fffggg",
        "HEX accepts hexadecimal digits only: 0-9 and a-f."
    ),
    (
        "Assuming % always means viewport percentage",
        "Percentages depend on the property and layout context."
    ),
    (
        "Assuming em always means root font size",
        "rem is root-relative; em depends on its relevant font-size context."
    ),
    (
        "Using opacity when only the background should be transparent",
        "Element opacity also affects descendants; use an alpha color when appropriate."
    ),
    (
        "Choosing colors only by hue",
        "Text accessibility depends strongly on contrast and luminance."
    ),
    (
        "Using huge fixed pixel dimensions everywhere",
        "Responsive interfaces generally combine fixed, relative, and constrained values."
    ),
]

for mistake, correction in mistakes:
    print(f"\nMistake: {mistake}")
    print(f"Correction: {correction}")


# ---------------------------------------------------------------------------
# SECTION 20: PRODUCTION CONSIDERATIONS
# ---------------------------------------------------------------------------

section("22. Production considerations")

production_points = [
    "Use design tokens through CSS custom properties for consistent color and spacing.",
    "Use rem for scalable typography and spacing systems where root-relative behavior is desirable.",
    "Use percentages and viewport units for responsive relationships rather than forcing every dimension into px.",
    "Use max-width and min/max constraints to prevent extreme layouts.",
    "Validate color contrast for text and important controls.",
    "Do not communicate state using color alone when another visual cue is needed.",
    "Use alpha carefully because compositing can reduce perceived contrast.",
    "Test responsive units across different viewport sizes and device configurations.",
    "Prefer modern color functions and syntax when browser support and project requirements allow them.",
    "Keep colors semantic, such as --color-danger, rather than naming every token only by appearance."
]

for point in production_points:
    print("-", point)


# ---------------------------------------------------------------------------
# SECTION 21: SELF-TESTS
# ---------------------------------------------------------------------------

section("23. Self-tests")

assert normalize_hex("#abc") == "#aabbcc"
assert hex_to_rgba("#ff0000") == (255, 0, 0, 1.0)
assert hex_to_rgba("#ff000080") == (255, 0, 0, 128 / 255)
assert rgba_to_hex(255, 0, 0) == "#ff0000"
assert rgba_to_hex(255, 0, 0, 1) == "#ff0000ff"

red_hsl = rgb_to_hsl(255, 0, 0)
assert abs(red_hsl[0] - 0) < 1e-9
assert abs(red_hsl[1] - 100) < 1e-9
assert abs(red_hsl[2] - 50) < 1e-9

red_rgb = hsl_to_rgb(0, 100, 50)
assert red_rgb == (255, 0, 0)

assert rem_to_px(1) == 16
assert rem_to_px(2) == 32
assert em_to_px(2, 20) == 40

test_viewport = Viewport(1000, 800)
assert test_viewport.vw(50) == 500
assert test_viewport.vh(50) == 400
assert test_viewport.vmin_value(50) == 400
assert test_viewport.vmax_value(50) == 500

assert clamp(5, 10, 20) == 10
assert clamp(15, 10, 20) == 15
assert clamp(25, 10, 20) == 20

assert alpha_composite((0, 0, 0), (255, 255, 255), 0) == (
    255,
    255,
    255,
)
assert alpha_composite((0, 0, 0), (255, 255, 255, 255), 1) == (
    0,
    0,
    0,
)

print("All self-tests passed.")


# ---------------------------------------------------------------------------
# SECTION 22: FINAL EXECUTABLE CSS EXAMPLE
# ---------------------------------------------------------------------------

section("24. Complete generated CSS example")

css_example = """
:root {
  --root-size: 16px;

  --color-primary: #3498db;
  --color-primary-light: #5dade2;
  --color-primary-dark: #2874a6;

  --color-surface: #f5f7fa;
  --color-text: #1f2937;

  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-4: 1rem;
  --space-6: 1.5rem;
  --space-8: 2rem;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  color: var(--color-text);
  background: var(--color-surface);
  font-size: 1rem;
}

.page {
  width: 92%;
  max-width: 75rem;
  margin-inline: auto;
  padding: clamp(1rem, 4vw, 3rem);
}

.hero {
  min-height: 70vh;
  padding: 8vh 4vw;
}

.hero h1 {
  font-size: clamp(2rem, 5vw, 4rem);
}

.card {
  width: 100%;
  padding: 1.5rem;
  border-radius: 0.75rem;
  background: rgb(255 255 255 / 0.92);
}

.button {
  padding: 0.75em 1.25em;
  color: white;
  background: hsl(204 70% 53%);
}

.button:hover {
  background: hsl(204 70% 43%);
}
""".strip()

print(css_example)

explain(
    "The generated example combines semantic colors, HEX, RGB alpha, HSL, "
    "px-compatible root sizing, percentages, rem, em, vh, vw, and clamp-style "
    "responsive sizing in one coherent stylesheet."
)

print("\nStudy file execution complete.")
