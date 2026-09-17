"""
Typography Study Laboratory
===========================

Topic:
Font families, web fonts, font weight, line height, letter spacing,
text alignment, and typography hierarchy.

This standalone Python program teaches typography concepts through:
- Fundamental terminology and measurements
- Font-family classification
- Font stacks and fallback behavior
- Font weight
- Font size
- Line height
- Letter spacing
- Text alignment
- Typography hierarchy
- Readability calculations
- Responsive typography
- CSS generation
- Validation
- Accessibility considerations
- Performance considerations
- A complete typography-system simulation

The program uses only the Python standard library.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from math import ceil
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


# ---------------------------------------------------------------------------
# 1. Fundamental terminology
# ---------------------------------------------------------------------------

print("=" * 78)
print("TYPOGRAPHY STUDY LABORATORY")
print("=" * 78)
print(
    """
Typography is the design and arrangement of text so that written information
is readable, understandable, structured, and visually appropriate.

The main properties studied here are:

font family    -> the typeface or family used to render text
font weight    -> the thickness of glyph strokes
font size      -> the size assigned to text
line height    -> vertical distance occupied by successive lines
letter spacing -> additional horizontal space between characters
text alignment -> horizontal positioning of text
hierarchy      -> visual ordering that communicates importance
"""
)


# ---------------------------------------------------------------------------
# 2. Font-family classification
# ---------------------------------------------------------------------------

class FontCategory(Enum):
    SERIF = "serif"
    SANS_SERIF = "sans-serif"
    MONOSPACE = "monospace"
    CURSIVE = "cursive"
    FANTASY = "fantasy"


FONT_CATEGORIES: Dict[FontCategory, List[str]] = {
    FontCategory.SERIF: [
        "Georgia",
        "Times New Roman",
        "Garamond",
    ],
    FontCategory.SANS_SERIF: [
        "Arial",
        "Helvetica",
        "Verdana",
        "Inter",
        "Roboto",
    ],
    FontCategory.MONOSPACE: [
        "Consolas",
        "Courier New",
        "Monaco",
    ],
    FontCategory.CURSIVE: [
        "Comic Sans MS",
        "Brush Script MT",
    ],
    FontCategory.FANTASY: [
        "Impact",
        "Papyrus",
    ],
}

print("\nFONT-FAMILY CLASSIFICATIONS")
for category, families in FONT_CATEGORIES.items():
    print(f"{category.value:12}: {', '.join(families)}")


# ---------------------------------------------------------------------------
# 3. Font stacks
# ---------------------------------------------------------------------------

def build_font_stack(primary: str, fallbacks: Sequence[str], generic: str) -> str:
    """
    Build a CSS font-family declaration.

    A browser tries the first available family and proceeds through the list
    when a font cannot be used. The generic family provides a final category
    fallback.
    """
    all_families = [primary, *fallbacks, generic]

    def quote_if_needed(font_name: str) -> str:
        if " " in font_name:
            return f'"{font_name}"'
        return font_name

    return ", ".join(quote_if_needed(name) for name in all_families)


font_stack = build_font_stack(
    "Inter",
    ["Arial", "Helvetica"],
    "sans-serif",
)

print("\nFONT STACK")
print(font_stack)


# ---------------------------------------------------------------------------
# 4. Font weight
# ---------------------------------------------------------------------------

VALID_CSS_WEIGHTS = {
    100: "Thin",
    200: "Extra Light",
    300: "Light",
    400: "Normal",
    500: "Medium",
    600: "Semi Bold",
    700: "Bold",
    800: "Extra Bold",
    900: "Black",
}


def describe_weight(weight: int) -> str:
    """Return a human-readable description for a CSS numeric weight."""
    if weight not in VALID_CSS_WEIGHTS:
        raise ValueError("Font weight must be one of the CSS values 100..900.")
    return VALID_CSS_WEIGHTS[weight]


print("\nFONT WEIGHTS")
for weight, description in VALID_CSS_WEIGHTS.items():
    print(f"{weight}: {description}")


# ---------------------------------------------------------------------------
# 5. Font-size units
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FontSize:
    pixels: float

    def to_rem(self, root_size: float = 16.0) -> float:
        if root_size <= 0:
            raise ValueError("Root font size must be positive.")
        return self.pixels / root_size

    def to_em(self, parent_size: float) -> float:
        if parent_size <= 0:
            raise ValueError("Parent font size must be positive.")
        return self.pixels / parent_size


font_size = FontSize(24)

print("\nFONT SIZE UNITS")
print(f"24px = {font_size.to_rem():.2f}rem when root size is 16px")
print(f"24px = {font_size.to_em(16):.2f}em when parent size is 16px")


# ---------------------------------------------------------------------------
# 6. Line height
# ---------------------------------------------------------------------------

def line_height_pixels(font_size_px: float, line_height: float) -> float:
    """
    Convert unitless line-height into pixels.

    CSS commonly uses a unitless value such as 1.5 because it scales naturally
    with the element's font size.
    """
    if font_size_px <= 0:
        raise ValueError("Font size must be positive.")
    if line_height <= 0:
        raise ValueError("Line height must be positive.")
    return font_size_px * line_height


print("\nLINE HEIGHT")
for size, multiplier in [(16, 1.5), (20, 1.5), (32, 1.2)]:
    print(
        f"{size}px text with {multiplier} line-height -> "
        f"{line_height_pixels(size, multiplier):.1f}px"
    )


# ---------------------------------------------------------------------------
# 7. Letter spacing
# ---------------------------------------------------------------------------

def adjusted_character_width(
    character_width_px: float,
    letter_spacing_px: float,
) -> float:
    """
    Approximate the horizontal advance of a character.

    Real font shaping is more complicated because glyph widths, kerning,
    ligatures, scripts, and rendering engines affect actual measurements.
    """
    return character_width_px + letter_spacing_px


print("\nLETTER SPACING")
for spacing in [-0.02, 0.0, 0.08, 0.15]:
    print(
        f"Additional spacing: {spacing:+.2f}px -> "
        f"approximate character advance: "
        f"{adjusted_character_width(8, spacing):.2f}px"
    )


# ---------------------------------------------------------------------------
# 8. Text alignment
# ---------------------------------------------------------------------------

ALIGNMENTS = {
    "left": "Text begins at the left edge of its text box.",
    "right": "Text ends at the right edge of its text box.",
    "center": "Text is centered inside its text box.",
    "justify": "Text is distributed across the available line width.",
}


print("\nTEXT ALIGNMENT")
for alignment, explanation in ALIGNMENTS.items():
    print(f"{alignment:8}: {explanation}")


# ---------------------------------------------------------------------------
# 9. Typography hierarchy
# ---------------------------------------------------------------------------

@dataclass
class TypeStyle:
    name: str
    font_family: str
    font_size_px: float
    font_weight: int
    line_height: float
    letter_spacing_px: float = 0.0
    text_alignment: str = "left"

    def validate(self) -> List[str]:
        errors: List[str] = []

        if self.font_size_px <= 0:
            errors.append("Font size must be positive.")

        if self.font_weight not in VALID_CSS_WEIGHTS:
            errors.append("Font weight must be a valid CSS numeric weight.")

        if self.line_height <= 0:
            errors.append("Line height must be positive.")

        if self.text_alignment not in ALIGNMENTS:
            errors.append("Unsupported text alignment.")

        return errors


hierarchy = [
    TypeStyle("display", "Inter", 56, 700, 1.05, -1.2),
    TypeStyle("h1", "Inter", 40, 700, 1.15, -0.7),
    TypeStyle("h2", "Inter", 32, 700, 1.20, -0.4),
    TypeStyle("h3", "Inter", 24, 600, 1.25, -0.2),
    TypeStyle("body", "Inter", 16, 400, 1.60, 0.0),
    TypeStyle("small", "Inter", 14, 400, 1.50, 0.1),
    TypeStyle("caption", "Inter", 12, 400, 1.40, 0.1),
]

print("\nTYPOGRAPHY HIERARCHY")
for style in hierarchy:
    print(
        f"{style.name:8} "
        f"{style.font_size_px:>5.0f}px "
        f"weight={style.font_weight} "
        f"line-height={style.line_height:.2f} "
        f"spacing={style.letter_spacing_px:+.2f}px"
    )


# ---------------------------------------------------------------------------
# 10. CSS generation
# ---------------------------------------------------------------------------

def css_property(name: str, value: str) -> str:
    """Generate one CSS property line."""
    return f"    {name}: {value};"


def type_style_to_css(selector: str, style: TypeStyle) -> str:
    """
    Convert a TypeStyle object into a complete CSS rule.
    """
    errors = style.validate()
    if errors:
        raise ValueError(f"{selector}: {'; '.join(errors)}")

    return "\n".join(
        [
            f"{selector} {{",
            css_property("font-family", style.font_family),
            css_property("font-size", f"{style.font_size_px:g}px"),
            css_property("font-weight", str(style.font_weight)),
            css_property("line-height", f"{style.line_height:g}"),
            css_property("letter-spacing", f"{style.letter_spacing_px:g}px"),
            css_property("text-align", style.text_alignment),
            "}",
        ]
    )


print("\nGENERATED CSS")
for style in hierarchy:
    print(type_style_to_css(f".type-{style.name}", style))
    print()


# ---------------------------------------------------------------------------
# 11. Web-font concepts
# ---------------------------------------------------------------------------

@dataclass
class WebFont:
    family: str
    source_urls: List[str]
    weights: List[int]
    styles: List[str] = field(default_factory=lambda: ["normal"])

    def supports(self, weight: int, style: str = "normal") -> bool:
        return weight in self.weights and style in self.styles


inter_web_font = WebFont(
    family="Inter",
    source_urls=[
        "/fonts/inter-400.woff2",
        "/fonts/inter-600.woff2",
        "/fonts/inter-700.woff2",
    ],
    weights=[400, 600, 700],
)

print("\nWEB-FONT CAPABILITY")
for requested_weight in [400, 500, 600, 700, 800]:
    print(
        f"Inter weight {requested_weight}: "
        f"{'available' if inter_web_font.supports(requested_weight) else 'not supplied'}"
    )


# ---------------------------------------------------------------------------
# 12. Simulating font fallback
# ---------------------------------------------------------------------------

def choose_available_font(
    requested_families: Sequence[str],
    installed_families: Iterable[str],
    generic_fallback: str,
) -> str:
    """
    Simulate a simplified browser font-family selection.

    Actual browser selection also considers font-face declarations,
    Unicode coverage, variation axes, style, weight, and platform fonts.
    """
    installed = {font.lower() for font in installed_families}

    for family in requested_families:
        if family.lower() in installed:
            return family

    return generic_fallback


chosen_font = choose_available_font(
    ["Inter", "Helvetica", "Arial"],
    ["Arial", "Consolas"],
    "sans-serif",
)

print("\nFONT FALLBACK SIMULATION")
print(f"Selected family: {chosen_font}")


# ---------------------------------------------------------------------------
# 13. Responsive typography
# ---------------------------------------------------------------------------

def linear_interpolation(
    minimum: float,
    maximum: float,
    viewport_width: float,
    minimum_width: float,
    maximum_width: float,
) -> float:
    """
    Calculate a linearly interpolated responsive value.

    This models the conceptual behavior of CSS clamp() and viewport-based
    typography. Production CSS can use clamp() directly.
    """
    if maximum_width <= minimum_width:
        raise ValueError("Maximum width must exceed minimum width.")

    ratio = (viewport_width - minimum_width) / (
        maximum_width - minimum_width
    )
    ratio = max(0.0, min(1.0, ratio))

    return minimum + ratio * (maximum - minimum)


print("\nRESPONSIVE TYPOGRAPHY")
for viewport in [320, 768, 1024, 1440, 1920]:
    size = linear_interpolation(32, 56, viewport, 320, 1440)
    print(f"Viewport {viewport:4}px -> display size {size:.1f}px")


# ---------------------------------------------------------------------------
# 14. Readability and line-length estimation
# ---------------------------------------------------------------------------

def estimate_characters_per_line(
    container_width_px: float,
    average_character_width_px: float,
) -> int:
    """
    Estimate characters per line.

    This is a heuristic rather than a typography engine. Real text layout
    depends on individual glyph widths, kerning, language, and shaping.
    """
    if container_width_px <= 0 or average_character_width_px <= 0:
        raise ValueError("Both dimensions must be positive.")

    return max(1, int(container_width_px / average_character_width_px))


def estimate_line_count(
    text: str,
    container_width_px: float,
    average_character_width_px: float,
) -> int:
    chars_per_line = estimate_characters_per_line(
        container_width_px,
        average_character_width_px,
    )

    words = text.split()
    if not words:
        return 0

    lines = 1
    current_length = 0

    for word in words:
        word_length = len(word)

        if word_length > chars_per_line:
            if current_length > 0:
                lines += 1
                current_length = 0

            extra_lines = ceil(word_length / chars_per_line)
            lines += extra_lines - 1
            current_length = word_length % chars_per_line
            continue

        required = word_length if current_length == 0 else word_length + 1

        if current_length + required <= chars_per_line:
            current_length += required
        else:
            lines += 1
            current_length = word_length

    return lines


sample_text = (
    "Typography controls how readers perceive structure, emphasis, "
    "rhythm, and readability in a digital interface."
)

print("\nREADABILITY ESTIMATION")
for width in [280, 400, 600, 760]:
    lines = estimate_line_count(sample_text, width, 8)
    print(f"Container {width}px -> approximately {lines} line(s)")


# ---------------------------------------------------------------------------
# 15. Typography scale
# ---------------------------------------------------------------------------

def create_modular_scale(
    base_size: float,
    ratio: float,
    steps: Sequence[int],
) -> Dict[int, float]:
    """
    Generate a modular type scale.

    Positive steps create larger sizes; negative steps create smaller sizes.
    """
    if base_size <= 0 or ratio <= 0:
        raise ValueError("Base size and ratio must be positive.")

    return {
        step: base_size * (ratio ** step)
        for step in steps
    }


scale = create_modular_scale(16, 1.25, [-2, -1, 0, 1, 2, 3, 4])

print("\nMODULAR TYPE SCALE")
for step, size in scale.items():
    print(f"step {step:+}: {size:.2f}px")


# ---------------------------------------------------------------------------
# 16. Typography tokens
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TypographyToken:
    name: str
    size_rem: float
    weight: int
    line_height: float
    tracking_em: float

    def to_css_variable(self) -> str:
        return (
            f"  --type-{self.name}-size: {self.size_rem:g}rem;\n"
            f"  --type-{self.name}-weight: {self.weight};\n"
            f"  --type-{self.name}-line: {self.line_height:g};\n"
            f"  --type-{self.name}-tracking: {self.tracking_em:g}em;"
        )


tokens = [
    TypographyToken("display", 3.5, 700, 1.05, -0.02),
    TypographyToken("heading-1", 2.5, 700, 1.15, -0.015),
    TypographyToken("heading-2", 2.0, 700, 1.20, -0.01),
    TypographyToken("body", 1.0, 400, 1.60, 0.0),
    TypographyToken("small", 0.875, 400, 1.50, 0.005),
]

print("\nDESIGN TOKENS")
print(":root {")
for token in tokens:
    print(token.to_css_variable())
print("}")


# ---------------------------------------------------------------------------
# 17. Accessibility validation
# ---------------------------------------------------------------------------

@dataclass
class AccessibilityReport:
    warnings: List[str]
    passed_checks: List[str]

    @property
    def passed(self) -> bool:
        return not self.warnings


def validate_accessibility(style: TypeStyle) -> AccessibilityReport:
    warnings: List[str] = []
    passed: List[str] = []

    if style.font_size_px < 12:
        warnings.append("Text below 12px may be difficult for many users.")
    else:
        passed.append("Font size is not unusually small.")

    if style.line_height < 1.2:
        warnings.append("Very tight line height can reduce readability.")
    else:
        passed.append("Line height provides reasonable vertical separation.")

    if abs(style.letter_spacing_px) > style.font_size_px * 0.08:
        warnings.append(
            "Large tracking changes may impair word recognition."
        )
    else:
        passed.append("Letter spacing is within a conservative range.")

    if style.font_weight == 300 and style.font_size_px < 14:
        warnings.append(
            "Very light small text can become difficult to read."
        )
    else:
        passed.append("Weight and size combination is not obviously problematic.")

    return AccessibilityReport(warnings, passed)


print("\nACCESSIBILITY CHECK")
for style in [hierarchy[0], hierarchy[-1], hierarchy[4]]:
    report = validate_accessibility(style)
    print(f"{style.name}: {'PASS' if report.passed else 'WARNINGS'}")
    for warning in report.warnings:
        print(f"  - {warning}")


# ---------------------------------------------------------------------------
# 18. Validation of typography systems
# ---------------------------------------------------------------------------

@dataclass
class TypographySystem:
    name: str
    styles: Dict[str, TypeStyle]

    def validate(self) -> Dict[str, List[str]]:
        return {
            name: style.validate()
            for name, style in self.styles.items()
        }

    def generate_css(self) -> str:
        blocks = []

        for name, style in self.styles.items():
            blocks.append(type_style_to_css(f".type-{name}", style))

        return "\n\n".join(blocks)


system = TypographySystem(
    name="Academic Interface",
    styles={style.name: style for style in hierarchy},
)

print("\nSYSTEM VALIDATION")
for name, errors in system.validate().items():
    print(f"{name:10}: {'valid' if not errors else ', '.join(errors)}")


# ---------------------------------------------------------------------------
# 19. Comparison of serif, sans-serif, and monospace roles
# ---------------------------------------------------------------------------

FONT_ROLE_GUIDANCE = {
    "serif": [
        "Long-form editorial content",
        "Traditional or literary visual language",
        "Print-inspired interfaces",
    ],
    "sans-serif": [
        "Interfaces",
        "Dashboards",
        "Navigation",
        "General digital content",
    ],
    "monospace": [
        "Source code",
        "Logs",
        "Identifiers",
        "Tabular technical data",
    ],
}

print("\nCOMMON FONT-FAMILY ROLES")
for category, roles in FONT_ROLE_GUIDANCE.items():
    print(f"\n{category.upper()}")
    for role in roles:
        print(f"  - {role}")


# ---------------------------------------------------------------------------
# 20. Edge cases
# ---------------------------------------------------------------------------

print("\nEDGE CASES")

edge_cases = [
    ("empty text", ""),
    ("single character", "A"),
    ("very long word", "supercalifragilisticexpialidocious"),
    ("multiple spaces", "Typography    needs    whitespace."),
    ("Unicode text", "Typography: café, naïve, हिन्दी, 日本語"),
]

for description, value in edge_cases:
    lines = estimate_line_count(value, 300, 8)
    print(f"{description:20}: estimated lines={lines}")


# ---------------------------------------------------------------------------
# 21. Common implementation mistakes
# ---------------------------------------------------------------------------

MISTAKES = [
    (
        "Using too many font families",
        "Creates visual inconsistency and can increase font downloads."
    ),
    (
        "Using arbitrary font weights",
        "A requested weight may not exist in the loaded font."
    ),
    (
        "Setting extremely small text",
        "Reduces readability and accessibility."
    ),
    (
        "Using fixed pixel line-height everywhere",
        "Can become inappropriate when font size changes responsively."
    ),
    (
        "Excessive letter spacing",
        "Can damage word shapes and reading rhythm."
    ),
    (
        "Using center alignment for long paragraphs",
        "Makes line starts inconsistent and can slow reading."
    ),
    (
        "Creating hierarchy only with font size",
        "Hierarchy can also depend on weight, spacing, position, and grouping."
    ),
]

print("\nCOMMON MISTAKES")
for mistake, consequence in MISTAKES:
    print(f"- {mistake}: {consequence}")


# ---------------------------------------------------------------------------
# 22. Performance considerations
# ---------------------------------------------------------------------------

@dataclass
class FontAsset:
    family: str
    weight: int
    style: str
    format: str
    size_kb: int

    def is_modern_format(self) -> bool:
        return self.format.lower() == "woff2"


font_assets = [
    FontAsset("Inter", 400, "normal", "woff2", 32),
    FontAsset("Inter", 600, "normal", "woff2", 34),
    FontAsset("Inter", 700, "normal", "woff2", 35),
]

print("\nFONT PERFORMANCE MODEL")
total_kb = sum(asset.size_kb for asset in font_assets)

for asset in font_assets:
    print(
        f"{asset.family} {asset.weight}: "
        f"{asset.size_kb}KB, modern={asset.is_modern_format()}"
    )

print(f"Approximate total font payload: {total_kb}KB")


# ---------------------------------------------------------------------------
# 23. CSS @font-face generation
# ---------------------------------------------------------------------------

def generate_font_face(font: WebFont) -> str:
    """
    Generate illustrative @font-face declarations.

    One source file is assigned to each supplied weight. Real production
    systems may use variable fonts, unicode-range, font-display, preload,
    subsetting, and multiple source formats depending on browser support.
    """
    blocks = []

    for weight, source in zip(font.weights, font.source_urls):
        blocks.append(
            "\n".join(
                [
                    "@font-face {",
                    f"  font-family: '{font.family}';",
                    f"  src: url('{source}') format('woff2');",
                    f"  font-weight: {weight};",
                    "  font-style: normal;",
                    "  font-display: swap;",
                    "}",
                ]
            )
        )

    return "\n\n".join(blocks)


print("\nWEB-FONT CSS")
print(generate_font_face(inter_web_font))


# ---------------------------------------------------------------------------
# 24. Text-style comparison
# ---------------------------------------------------------------------------

def compare_styles(first: TypeStyle, second: TypeStyle) -> Dict[str, object]:
    """Compare two typography styles property by property."""
    return {
        "font_family_same": first.font_family == second.font_family,
        "font_size_difference_px": first.font_size_px - second.font_size_px,
        "weight_difference": first.font_weight - second.font_weight,
        "line_height_difference": first.line_height - second.line_height,
        "letter_spacing_difference_px": (
            first.letter_spacing_px - second.letter_spacing_px
        ),
        "alignment_same": first.text_alignment == second.text_alignment,
    }


comparison = compare_styles(hierarchy[1], hierarchy[4])

print("\nSTYLE COMPARISON: H1 VS BODY")
for property_name, value in comparison.items():
    print(f"{property_name}: {value}")


# ---------------------------------------------------------------------------
# 25. Production typography system
# ---------------------------------------------------------------------------

@dataclass
class ProductionTypographySystem:
    font_family: str
    base_size_px: float
    base_line_height: float
    styles: Dict[str, TypeStyle]

    def css(self) -> str:
        lines = [
            ":root {",
            f"  --font-family-base: {self.font_family};",
            f"  --font-size-base: {self.base_size_px:g}px;",
            f"  --line-height-base: {self.base_line_height:g};",
            "}",
            "",
        ]

        for name, style in self.styles.items():
            lines.append(type_style_to_css(f".{name}", style))
            lines.append("")

        return "\n".join(lines)


production_system = ProductionTypographySystem(
    font_family=font_stack,
    base_size_px=16,
    base_line_height=1.6,
    styles={
        "page-title": TypeStyle(
            "page-title", font_stack, 48, 700, 1.10, -0.8
        ),
        "section-title": TypeStyle(
            "section-title", font_stack, 30, 700, 1.20, -0.4
        ),
        "body": TypeStyle(
            "body", font_stack, 16, 400, 1.60, 0.0
        ),
        "metadata": TypeStyle(
            "metadata", font_stack, 13, 500, 1.40, 0.05
        ),
    },
)

print("\nPRODUCTION TYPOGRAPHY SYSTEM")
print(production_system.css())


# ---------------------------------------------------------------------------
# 26. Typography decision helper
# ---------------------------------------------------------------------------

def recommend_text_alignment(content_type: str) -> str:
    """
    Provide a structural default, not an absolute design rule.
    """
    normalized = content_type.strip().lower()

    if normalized in {"paragraph", "article", "documentation", "body"}:
        return "left"
    if normalized in {"heading", "hero", "marketing"}:
        return "left"
    if normalized in {"table-number", "numeric-data"}:
        return "right"
    if normalized in {"short-label", "badge"}:
        return "center"

    return "left"


print("\nALIGNMENT DECISION EXAMPLES")
for content_type in [
    "paragraph",
    "heading",
    "numeric-data",
    "badge",
    "documentation",
]:
    print(
        f"{content_type:15} -> "
        f"{recommend_text_alignment(content_type)}"
    )


# ---------------------------------------------------------------------------
# 27. Final study checklist
# ---------------------------------------------------------------------------

CHECKLIST = [
    "Choose a coherent primary font family.",
    "Provide sensible fallback families.",
    "Load only required font weights.",
    "Use font size to establish scale.",
    "Use line height to establish vertical rhythm.",
    "Use letter spacing carefully.",
    "Use alignment according to content structure.",
    "Create a clear hierarchy between headings and body text.",
    "Validate small text and tight line heights.",
    "Test typography across viewport sizes.",
    "Consider font loading performance.",
    "Test real content rather than isolated sample words.",
    "Check multilingual and Unicode coverage when applicable.",
    "Avoid relying on font appearance alone to communicate meaning.",
]

print("\nTYPOGRAPHY CHECKLIST")
for item in CHECKLIST:
    print(f"[ ] {item}")


print("\n" + "=" * 78)
print("END OF TYPOGRAPHY STUDY LABORATORY")
print("=" * 78)
