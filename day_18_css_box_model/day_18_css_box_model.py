"""
CSS Box Model: Content, Padding, Border, Margin, box-sizing,
Dimensions, and Overflow

This standalone study script teaches the CSS box model from beginner
concepts through practical calculations, validation, edge cases,
layout reasoning, and production-oriented considerations.

The program does not require external packages.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


# ============================================================================
# 1. FUNDAMENTAL CONCEPTS
# ============================================================================

def print_section(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def explain_box_model() -> None:
    print_section("1. The CSS Box Model")

    print(
        """
Every normal CSS element is represented by a rectangular box.

From the inside outward, the conceptual layers are:

    content
    padding
    border
    margin

Content:
    The area containing text, images, child elements, or other content.

Padding:
    Space between the content and the border.

Border:
    The visible boundary surrounding the padding and content.

Margin:
    Space outside the border that separates the element from other boxes.

The important distinction is that margin is outside the element's border,
while padding is part of the element's box.

For example:

    width: 200px;
    padding: 20px;
    border: 5px solid black;
    margin: 30px;

The total horizontal space occupied by the element, ignoring margin
collapse and other layout rules, depends on box-sizing.
"""
    )


# ============================================================================
# 2. MATHEMATICAL MODEL
# ============================================================================

@dataclass
class BoxDimensions:
    content_width: float
    content_height: float

    padding_top: float = 0
    padding_right: float = 0
    padding_bottom: float = 0
    padding_left: float = 0

    border_top: float = 0
    border_right: float = 0
    border_bottom: float = 0
    border_left: float = 0

    margin_top: float = 0
    margin_right: float = 0
    margin_bottom: float = 0
    margin_left: float = 0

    def padding_width(self) -> float:
        return self.padding_left + self.padding_right

    def padding_height(self) -> float:
        return self.padding_top + self.padding_bottom

    def border_width(self) -> float:
        return self.border_left + self.border_right

    def border_height(self) -> float:
        return self.border_top + self.border_bottom

    def margin_width(self) -> float:
        return self.margin_left + self.margin_right

    def margin_height(self) -> float:
        return self.margin_top + self.margin_bottom

    def content_box_width(self) -> float:
        return self.content_width

    def content_box_height(self) -> float:
        return self.content_height

    def padding_box_width(self) -> float:
        return self.content_width + self.padding_width()

    def padding_box_height(self) -> float:
        return self.content_height + self.padding_height()

    def border_box_width(self) -> float:
        return self.padding_box_width() + self.border_width()

    def border_box_height(self) -> float:
        return self.padding_box_height() + self.border_height()

    def margin_box_width(self) -> float:
        return self.border_box_width() + self.margin_width()

    def margin_box_height(self) -> float:
        return self.border_box_height() + self.margin_height()


def demonstrate_dimensions() -> None:
    print_section("2. Calculating Box Dimensions")

    box = BoxDimensions(
        content_width=200,
        content_height=100,
        padding_top=20,
        padding_right=30,
        padding_bottom=20,
        padding_left=30,
        border_top=5,
        border_right=5,
        border_bottom=5,
        border_left=5,
        margin_top=15,
        margin_right=25,
        margin_bottom=15,
        margin_left=25,
    )

    print(f"Content width:       {box.content_box_width()}px")
    print(f"Padding-box width:   {box.padding_box_width()}px")
    print(f"Border-box width:    {box.border_box_width()}px")
    print(f"Margin-box width:    {box.margin_box_width()}px")

    print()
    print(f"Content height:      {box.content_box_height()}px")
    print(f"Padding-box height:  {box.padding_box_height()}px")
    print(f"Border-box height:   {box.border_box_height()}px")
    print(f"Margin-box height:   {box.margin_box_height()}px")

    print(
        """
For content-box sizing:

border-box width =
    content width
    + left/right padding
    + left/right border

margin-box width =
    border-box width
    + left/right margin
"""
    )


# ============================================================================
# 3. box-sizing
# ============================================================================

def calculate_used_dimensions(
    declared_width: float,
    declared_height: float,
    padding_horizontal: float,
    padding_vertical: float,
    border_horizontal: float,
    border_vertical: float,
    box_sizing: str,
) -> tuple[float, float]:
    """
    Calculate the resulting border-box dimensions for the two common
    box-sizing values.

    content-box:
        width and height refer to content dimensions.

    border-box:
        width and height include padding and border.
    """
    if declared_width < 0 or declared_height < 0:
        raise ValueError("Declared dimensions cannot be negative.")

    if min(
        padding_horizontal,
        padding_vertical,
        border_horizontal,
        border_vertical,
    ) < 0:
        raise ValueError("Padding and border dimensions cannot be negative.")

    if box_sizing == "content-box":
        return (
            declared_width + padding_horizontal + border_horizontal,
            declared_height + padding_vertical + border_vertical,
        )

    if box_sizing == "border-box":
        if declared_width < padding_horizontal + border_horizontal:
            raise ValueError(
                "The declared width is smaller than the required "
                "horizontal padding and border."
            )

        if declared_height < padding_vertical + border_vertical:
            raise ValueError(
                "The declared height is smaller than the required "
                "vertical padding and border."
            )

        return declared_width, declared_height

    raise ValueError("box-sizing must be 'content-box' or 'border-box'.")


def demonstrate_box_sizing() -> None:
    print_section("3. content-box versus border-box")

    parameters = {
        "declared_width": 200,
        "declared_height": 100,
        "padding_horizontal": 40,
        "padding_vertical": 20,
        "border_horizontal": 10,
        "border_vertical": 10,
    }

    for sizing in ("content-box", "border-box"):
        width, height = calculate_used_dimensions(
            **parameters,
            box_sizing=sizing,
        )

        print(f"{sizing:12} -> border-box: {width}px × {height}px")

    print(
        """
With content-box:

    width: 200px
    padding: 20px left + 20px right
    border: 5px left + 5px right

    actual border-box width = 250px

With border-box:

    width: 200px

The 200px includes the horizontal padding and border, so the content
area becomes smaller.

This is why border-box is frequently convenient for predictable
component dimensions.
"""
    )


# ============================================================================
# 4. GLOBAL border-box PATTERN
# ============================================================================

def explain_global_box_sizing() -> None:
    print_section("4. A Common Global box-sizing Strategy")

    css = """*,
*::before,
*::after {
    box-sizing: border-box;
}"""

    print(css)

    print(
        """
The universal selector applies the rule to normal elements.

The pseudo-element selectors ensure generated ::before and ::after
boxes use the same sizing model.

This does not eliminate all layout complexity. It simply makes explicit
width and height calculations more predictable.
"""
    )


# ============================================================================
# 5. CSS WIDTH AND HEIGHT VALUES
# ============================================================================

def explain_dimensions() -> None:
    print_section("5. CSS Dimensions")

    examples = {
        "fixed": "width: 320px;",
        "percentage": "width: 50%;",
        "viewport": "width: 50vw;",
        "minimum": "min-width: 240px;",
        "maximum": "max-width: 100%;",
        "automatic": "width: auto;",
        "calculated": "width: calc(100% - 40px);",
        "clamped": "width: clamp(240px, 50vw, 720px);",
    }

    for name, example in examples.items():
        print(f"{name:12}: {example}")

    print(
        """
Width is not always a single fixed number.

Important distinctions:

- width: 300px gives a fixed declared width.
- width: 50% depends on the containing block.
- max-width limits how large an element can become.
- min-width establishes a lower bound.
- width: auto lets the layout algorithm determine the used size.
- calc() performs CSS arithmetic.
- clamp() expresses minimum, preferred, and maximum values.

Height has additional practical complications because percentage heights
often depend on whether the containing block has a definite height.
"""
    )


# ============================================================================
# 6. PADDING
# ============================================================================

def demonstrate_padding_shorthand() -> None:
    print_section("6. Padding Shorthand")

    values = {
        "one value": "padding: 10px;",
        "two values": "padding: 10px 20px;",
        "three values": "padding: 10px 20px 30px;",
        "four values": "padding: 10px 20px 30px 40px;",
    }

    for description, declaration in values.items():
        print(f"{description:12}: {declaration}")

    print(
        """
The four-value order is:

    top
    right
    bottom
    left

Two values mean:

    top/bottom
    left/right

Three values mean:

    top
    left/right
    bottom

Padding cannot be negative.
"""
    )


# ============================================================================
# 7. BORDER
# ============================================================================

def demonstrate_borders() -> None:
    print_section("7. Borders")

    examples = [
        "border: 1px solid black;",
        "border: 2px dashed currentColor;",
        "border: 4px double black;",
        "border-width: 1px 2px 3px 4px;",
        "border-radius: 12px;",
    ]

    for example in examples:
        print(example)

    print(
        """
Border width contributes to the border box.

A border has multiple dimensions:

    border-width
    border-style
    border-color

Each side can also be controlled independently.

For layout calculations, border thickness matters even if the border is
transparent or visually subtle.
"""
    )


# ============================================================================
# 8. MARGIN
# ============================================================================

def demonstrate_margins() -> None:
    print_section("8. Margins")

    print(
        """
Margins create space outside the border box.

Examples:

    margin: 20px;
    margin: 10px 20px;
    margin: 10px 20px 30px;
    margin: 10px 20px 30px 40px;

Unlike padding, margins may be negative.

Negative margins can move boxes toward or across neighboring layout
regions and should be used deliberately.

A major subtlety is vertical margin collapsing in normal block flow.
Adjacent vertical margins can combine rather than simply add.
"""
    )


# ============================================================================
# 9. MARGIN COLLAPSING
# ============================================================================

def collapsed_vertical_margin(first: float, second: float) -> float:
    """
    Simplified model for two adjoining positive vertical margins.

    For two positive margins in a normal block formatting context,
    the resulting collapsed margin is the larger margin.
    """
    if first < 0 or second < 0:
        raise ValueError("This simplified demonstration accepts positive margins.")

    return max(first, second)


def demonstrate_margin_collapse() -> None:
    print_section("9. Vertical Margin Collapse")

    first_margin = 30
    second_margin = 20

    print(f"First margin:  {first_margin}px")
    print(f"Second margin: {second_margin}px")
    print(f"Collapsed:     {collapsed_vertical_margin(first_margin, second_margin)}px")

    print(
        """
This simplified calculation represents the common positive-margin case.

Margin collapsing is associated with normal block flow. It does not
behave identically in flexbox or grid layout, where the relevant layout
algorithms differ.

Padding and borders prevent some parent/child margin-collapsing situations
because they establish separation between the relevant edges.
"""
    )


# ============================================================================
# 10. OVERFLOW
# ============================================================================

def calculate_overflow(
    content_width: float,
    content_height: float,
    available_width: float,
    available_height: float,
) -> dict[str, float]:
    return {
        "horizontal_overflow": max(0, content_width - available_width),
        "vertical_overflow": max(0, content_height - available_height),
    }


def demonstrate_overflow() -> None:
    print_section("10. Overflow")

    result = calculate_overflow(
        content_width=600,
        content_height=500,
        available_width=400,
        available_height=300,
    )

    print(f"Horizontal overflow: {result['horizontal_overflow']}px")
    print(f"Vertical overflow:   {result['vertical_overflow']}px")

    print(
        """
Common overflow values include:

    visible
    hidden
    clip
    scroll
    auto

Example:

    overflow: auto;

This allows scrolling when content exceeds the available box.

Axis-specific properties are also available:

    overflow-x
    overflow-y

Overflow is not merely a visual issue. It can affect usability,
scroll containers, keyboard navigation, sticky positioning, and
performance.
"""
    )


# ============================================================================
# 11. OVERFLOW EDGE CASES
# ============================================================================

def demonstrate_overflow_edge_cases() -> None:
    print_section("11. Overflow Edge Cases")

    cases = [
        ("content smaller than box", 300, 200, 400, 300),
        ("horizontal overflow", 600, 200, 400, 300),
        ("vertical overflow", 300, 500, 400, 300),
        ("both axes overflow", 600, 500, 400, 300),
    ]

    for name, content_w, content_h, box_w, box_h in cases:
        result = calculate_overflow(content_w, content_h, box_w, box_h)

        print(
            f"{name:28} -> "
            f"x={result['horizontal_overflow']}px, "
            f"y={result['vertical_overflow']}px"
        )

    print(
        """
overflow: hidden can conceal content that users need.

overflow: auto usually provides scrolling only when necessary.

overflow: scroll requests scrolling mechanisms even when content may fit.

overflow: clip is more restrictive and is intended when scrolling is not
wanted.

A production interface should avoid using overflow merely to hide a
layout defect.
"""
    )


# ============================================================================
# 12. BOX MODEL INSPECTION
# ============================================================================

@dataclass
class CSSBox:
    name: str
    declared_width: float
    declared_height: float
    padding: float
    border: float
    margin: float
    box_sizing: str = "content-box"

    def border_box(self) -> tuple[float, float]:
        width, height = calculate_used_dimensions(
            self.declared_width,
            self.declared_height,
            self.padding * 2,
            self.padding * 2,
            self.border * 2,
            self.border * 2,
            self.box_sizing,
        )
        return width, height

    def margin_box(self) -> tuple[float, float]:
        width, height = self.border_box()
        return width + self.margin * 2, height + self.margin * 2


def demonstrate_component_analysis() -> None:
    print_section("12. Component-Level Box Analysis")

    card = CSSBox(
        name="Product card",
        declared_width=320,
        declared_height=180,
        padding=24,
        border=1,
        margin=16,
        box_sizing="border-box",
    )

    border_width, border_height = card.border_box()
    margin_width, margin_height = card.margin_box()

    print(f"Component:          {card.name}")
    print(f"Border-box:         {border_width}px × {border_height}px")
    print(f"Margin-box:         {margin_width}px × {margin_height}px")

    print(
        """
A component can be analyzed as a hierarchy:

    content
      ↓
    padding
      ↓
    border
      ↓
    margin

When debugging a component, determine which layer is causing the
unexpected size before changing arbitrary width or height values.
"""
    )


# ============================================================================
# 13. WIDTH VALIDATION
# ============================================================================

def validate_box(
    width: float,
    height: float,
    padding: float,
    border: float,
    margin: float,
) -> list[str]:
    errors: list[str] = []

    if width < 0:
        errors.append("Width cannot be negative.")

    if height < 0:
        errors.append("Height cannot be negative.")

    if padding < 0:
        errors.append("Padding cannot be negative.")

    if border < 0:
        errors.append("Border width cannot be negative.")

    # Margin can legally be negative, so it is intentionally not rejected.
    return errors


def demonstrate_validation() -> None:
    print_section("13. Validation and Invalid Assumptions")

    test_cases = [
        (200, 100, 20, 2, 10),
        (-1, 100, 20, 2, 10),
        (200, 100, -5, 2, 10),
        (200, 100, 20, 2, -30),
    ]

    for values in test_cases:
        errors = validate_box(*values)

        if errors:
            print(f"{values} -> INVALID")
            for error in errors:
                print(f"    {error}")
        else:
            print(f"{values} -> valid")


# ============================================================================
# 14. RESPONSIVE BOX CALCULATIONS
# ============================================================================

def responsive_width(
    viewport_width: float,
    percentage: float,
    minimum: float,
    maximum: float,
) -> float:
    preferred = viewport_width * percentage
    return max(minimum, min(preferred, maximum))


def demonstrate_responsive_sizing() -> None:
    print_section("14. Responsive Sizing")

    for viewport in (320, 480, 768, 1024, 1440, 1920):
        width = responsive_width(
            viewport_width=viewport,
            percentage=0.8,
            minimum=280,
            maximum=900,
        )
        print(f"Viewport {viewport:4}px -> component {width:6.1f}px")

    print(
        """
This models the basic idea behind:

    width: 80%;
    min-width: 280px;
    max-width: 900px;

CSS can express the same concept directly with constraints.
"""
    )


# ============================================================================
# 15. BOX MODEL AND FLEXIBLE LAYOUTS
# ============================================================================

def explain_layout_interaction() -> None:
    print_section("15. Box Model and Layout Systems")

    print(
        """
The box model describes the dimensions of boxes, while layout systems
determine how boxes are arranged.

Important layout systems include:

    Normal flow
    Flexbox
    Grid
    Positioned layout

The same padding, border, margin, width, and height properties can behave
differently depending on the formatting context.

For example:

    display: flex;

changes how child boxes participate in layout.

This is why a box-model calculation alone cannot explain every browser
layout result.
"""
    )


# ============================================================================
# 16. DEBUGGING CHECKLIST
# ============================================================================

def debugging_checklist() -> None:
    print_section("16. Box Model Debugging Checklist")

    checks = [
        "Inspect the element in browser developer tools.",
        "Check the computed width and height.",
        "Check padding on all four sides.",
        "Check border widths on all four sides.",
        "Check margins on all four sides.",
        "Inspect the box-sizing value.",
        "Check min-width and max-width.",
        "Check min-height and max-height.",
        "Inspect overflow and overflow-x/overflow-y.",
        "Check whether flexbox or grid changes the available space.",
        "Check whether the containing block has the expected dimensions.",
        "Check for long unbreakable text.",
        "Check replaced elements such as images and their intrinsic sizes.",
        "Check whether a scrollbar changes available layout space.",
        "Avoid fixing symptoms with arbitrary negative margins.",
    ]

    for index, check in enumerate(checks, start=1):
        print(f"{index:2}. {check}")


# ============================================================================
# 17. COMMON MISTAKES
# ============================================================================

def common_mistakes() -> None:
    print_section("17. Common Mistakes")

    mistakes = {
        "Mistake": "Assuming width always means final visible width.",
        "Correction": "Check box-sizing, padding, and border.",
    }

    for key, value in mistakes.items():
        print(f"{key}: {value}")

    print(
        """
Other common mistakes:

1. Forgetting that content-box is the historical default.
2. Adding padding to a fixed-width element and causing unexpected growth.
3. Using overflow: hidden to conceal a broken layout.
4. Assuming margin and padding are interchangeable.
5. Ignoring min-width and max-width constraints.
6. Forgetting that percentage dimensions depend on a containing block.
7. Treating margin collapse as ordinary arithmetic.
8. Assuming height: 100% always means viewport height.
9. Ignoring intrinsic dimensions of images and other replaced elements.
10. Using fixed widths when responsive constraints would be more suitable.
"""
    )


# ============================================================================
# 18. PERFORMANCE AND PRODUCTION CONSIDERATIONS
# ============================================================================

def production_considerations() -> None:
    print_section("18. Production Considerations")

    print(
        """
Good production CSS generally favors:

- predictable sizing models,
- reusable component rules,
- responsive constraints,
- minimal unnecessary fixed dimensions,
- deliberate overflow behavior,
- accessible scrolling,
- readable content,
- consistent spacing scales,
- careful handling of replaced elements,
- developer-tool inspection during debugging.

Performance considerations:

Large numbers of layout-affecting changes can cause repeated style,
layout, and paint work. JavaScript that repeatedly changes dimensions
inside tight loops can contribute to layout thrashing.

Security considerations:

The box model itself is not a security mechanism. CSS should not be
treated as protection against malicious input. Untrusted content should
be handled using appropriate application-level validation and browser
security mechanisms.

Accessibility considerations:

A visually hidden overflow region may still contain content that is
important to keyboard or assistive-technology users. Scrollable regions
should remain usable with keyboard input and should not unexpectedly
trap focus.
"""
    )


# ============================================================================
# 19. MINI CSS CASE STUDY
# ============================================================================

def case_study() -> None:
    print_section("19. Mini Responsive Card Case Study")

    css = """
.card {
    box-sizing: border-box;
    width: min(100%, 360px);
    padding: 24px;
    border: 1px solid #999;
    margin: 16px;
    overflow: auto;
}

.card__title {
    margin: 0 0 12px;
}

.card__content {
    overflow-wrap: anywhere;
}
""".strip()

    print(css)

    print(
        """
The card uses border-box so its declared width includes padding and
border.

width: min(100%, 360px) prevents the card from exceeding its available
width while retaining a 360px maximum.

overflow: auto allows content to remain reachable when it exceeds the
available area.

overflow-wrap: anywhere helps prevent long unbroken strings from
creating unexpected horizontal overflow.
"""
    )


# ============================================================================
# 20. EXERCISES AS EXECUTABLE CHECKS
# ============================================================================

def run_executable_checks() -> None:
    print_section("20. Executable Verification Checks")

    width, height = calculate_used_dimensions(
        declared_width=200,
        declared_height=100,
        padding_horizontal=40,
        padding_vertical=20,
        border_horizontal=10,
        border_vertical=10,
        box_sizing="content-box",
    )

    assert width == 250
    assert height == 130

    width, height = calculate_used_dimensions(
        declared_width=200,
        declared_height=100,
        padding_horizontal=40,
        padding_vertical=20,
        border_horizontal=10,
        border_vertical=10,
        box_sizing="border-box",
    )

    assert width == 200
    assert height == 100

    assert collapsed_vertical_margin(30, 20) == 30

    overflow = calculate_overflow(500, 300, 400, 300)
    assert overflow["horizontal_overflow"] == 100
    assert overflow["vertical_overflow"] == 0

    print("All executable checks passed.")


# ============================================================================
# 21. INTERACTIVE CALCULATOR
# ============================================================================

def read_non_negative_number(prompt: str) -> float:
    while True:
        try:
            value = float(input(prompt))

            if value < 0:
                print("Enter a non-negative number.")
                continue

            return value

        except ValueError:
            print("Enter a valid number.")


def interactive_box_calculator() -> None:
    print_section("21. Interactive CSS Box Calculator")

    print("Enter content dimensions and box-model components.")
    print("Use 0 where a component is not present.")

    content_width = read_non_negative_number("Content width (px): ")
    content_height = read_non_negative_number("Content height (px): ")
    padding_horizontal = read_non_negative_number(
        "Total horizontal padding (px): "
    )
    padding_vertical = read_non_negative_number(
        "Total vertical padding (px): "
    )
    border_horizontal = read_non_negative_number(
        "Total horizontal border (px): "
    )
    border_vertical = read_non_negative_number(
        "Total vertical border (px): "
    )
    margin_horizontal = read_non_negative_number(
        "Total horizontal margin (px): "
    )
    margin_vertical = read_non_negative_number(
        "Total vertical margin (px): "
    )

    content_box_width = content_width
    content_box_height = content_height

    padding_box_width = content_box_width + padding_horizontal
    padding_box_height = content_box_height + padding_vertical

    border_box_width = padding_box_width + border_horizontal
    border_box_height = padding_box_height + border_vertical

    margin_box_width = border_box_width + margin_horizontal
    margin_box_height = border_box_height + margin_vertical

    print("\nCalculated dimensions:")
    print(f"Content box: {content_box_width:g} × {content_box_height:g}px")
    print(f"Padding box: {padding_box_width:g} × {padding_box_height:g}px")
    print(f"Border box:  {border_box_width:g} × {border_box_height:g}px")
    print(f"Margin box:  {margin_box_width:g} × {margin_box_height:g}px")


# ============================================================================
# 22. MAIN PROGRAM
# ============================================================================

def main() -> None:
    explain_box_model()
    demonstrate_dimensions()
    demonstrate_box_sizing()
    explain_global_box_sizing()
    explain_dimensions()
    demonstrate_padding_shorthand()
    demonstrate_borders()
    demonstrate_margins()
    demonstrate_margin_collapse()
    demonstrate_overflow()
    demonstrate_overflow_edge_cases()
    demonstrate_component_analysis()
    demonstrate_validation()
    demonstrate_responsive_sizing()
    explain_layout_interaction()
    debugging_checklist()
    common_mistakes()
    production_considerations()
    case_study()
    run_executable_checks()

    print_section("23. Optional Interactive Exercise")
    print(
        "The interactive calculator is available as "
        "interactive_box_calculator()."
    )

    # The function is intentionally not called automatically so the study
    # script can run non-interactively in terminals, CI systems, and IDEs.


if __name__ == "__main__":
    main()
