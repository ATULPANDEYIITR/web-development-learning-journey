"""
Flexbox Fundamentals: A Comprehensive Python Study Program

This program teaches CSS Flexbox from beginner to advanced concepts by:
1. Modeling the main Flexbox terminology and rules.
2. Demonstrating common CSS declarations as data.
3. Simulating simplified flex sizing and alignment calculations.
4. Validating Flexbox configurations.
5. Comparing layout strategies.
6. Building progressively more realistic responsive-layout examples.

The program intentionally does not require third-party packages.
It is an educational model of Flexbox, not a replacement for a browser's
CSS layout engine. Real browser layout involves many additional algorithms,
intrinsic sizing rules, writing modes, min/max constraints, replaced
elements, text measurement, percentages, aspect ratios, and rounding rules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from math import floor
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


# ---------------------------------------------------------------------------
# 1. FUNDAMENTAL TERMINOLOGY
# ---------------------------------------------------------------------------

class FlexDirection(str, Enum):
    ROW = "row"
    ROW_REVERSE = "row-reverse"
    COLUMN = "column"
    COLUMN_REVERSE = "column-reverse"


class FlexWrap(str, Enum):
    NOWRAP = "nowrap"
    WRAP = "wrap"
    WRAP_REVERSE = "wrap-reverse"


class JustifyContent(str, Enum):
    FLEX_START = "flex-start"
    FLEX_END = "flex-end"
    CENTER = "center"
    SPACE_BETWEEN = "space-between"
    SPACE_AROUND = "space-around"
    SPACE_EVENLY = "space-evenly"


class AlignItems(str, Enum):
    STRETCH = "stretch"
    FLEX_START = "flex-start"
    FLEX_END = "flex-end"
    CENTER = "center"
    BASELINE = "baseline"


class AlignContent(str, Enum):
    STRETCH = "stretch"
    FLEX_START = "flex-start"
    FLEX_END = "center"
    SPACE_BETWEEN = "space-between"
    SPACE_AROUND = "space-around"
    SPACE_EVENLY = "space-evenly"


class AlignSelf(str, Enum):
    AUTO = "auto"
    STRETCH = "stretch"
    FLEX_START = "flex-start"
    FLEX_END = "flex-end"
    CENTER = "center"
    BASELINE = "baseline"


@dataclass
class FlexItem:
    """
    A simplified representation of a flex item.

    flex-basis:
        Initial size used before free-space distribution.

    flex-grow:
        Proportion of positive free space assigned to this item.

    flex-shrink:
        Proportion used when the flex line has negative free space.

    order:
        Controls visual ordering within a flex container.
    """

    name: str
    basis: float
    grow: float = 0.0
    shrink: float = 1.0
    order: int = 0
    min_size: Optional[float] = None
    max_size: Optional[float] = None

    def __post_init__(self) -> None:
        if self.basis < 0:
            raise ValueError("flex-basis cannot be negative")
        if self.grow < 0:
            raise ValueError("flex-grow cannot be negative")
        if self.shrink < 0:
            raise ValueError("flex-shrink cannot be negative")
        if self.min_size is not None and self.min_size < 0:
            raise ValueError("min_size cannot be negative")
        if (
            self.min_size is not None
            and self.max_size is not None
            and self.min_size > self.max_size
        ):
            raise ValueError("min_size cannot exceed max_size")


@dataclass
class FlexContainer:
    """
    Simplified Flexbox container model.

    The object records the major container-level Flexbox properties.
    """

    main_size: float
    cross_size: float
    direction: FlexDirection = FlexDirection.ROW
    wrap: FlexWrap = FlexWrap.NOWRAP
    justify_content: JustifyContent = JustifyContent.FLEX_START
    align_items: AlignItems = AlignItems.STRETCH
    align_content: AlignContent = AlignContent.STRETCH
    gap: float = 0.0
    row_gap: Optional[float] = None
    column_gap: Optional[float] = None

    def __post_init__(self) -> None:
        if self.main_size < 0 or self.cross_size < 0:
            raise ValueError("container dimensions cannot be negative")
        if self.gap < 0:
            raise ValueError("gap cannot be negative")

    @property
    def effective_row_gap(self) -> float:
        return self.gap if self.row_gap is None else self.row_gap

    @property
    def effective_column_gap(self) -> float:
        return self.gap if self.column_gap is None else self.column_gap


# ---------------------------------------------------------------------------
# 2. BASIC CSS PROPERTY KNOWLEDGE
# ---------------------------------------------------------------------------

FLEX_CONTAINER_PROPERTIES: Dict[str, str] = {
    "display": "flex | inline-flex",
    "flex-direction": "row | row-reverse | column | column-reverse",
    "flex-wrap": "nowrap | wrap | wrap-reverse",
    "flex-flow": "<flex-direction> <flex-wrap>",
    "justify-content": (
        "flex-start | flex-end | center | space-between | "
        "space-around | space-evenly"
    ),
    "align-items": (
        "stretch | flex-start | flex-end | center | baseline"
    ),
    "align-content": (
        "stretch | flex-start | flex-end | center | "
        "space-between | space-around | space-evenly"
    ),
    "gap": "<length> | <row-gap> <column-gap>",
    "row-gap": "<length>",
    "column-gap": "<length>",
}

FLEX_ITEM_PROPERTIES: Dict[str, str] = {
    "order": "integer",
    "flex-grow": "number",
    "flex-shrink": "number",
    "flex-basis": "auto | content | <length> | <percentage>",
    "flex": "<grow> <shrink> <basis>",
    "align-self": "auto | stretch | flex-start | flex-end | center | baseline",
}


def print_property_reference() -> None:
    """Print the major Flexbox properties and their value categories."""
    print("\n=== FLEXBOX PROPERTY REFERENCE ===")

    print("\nContainer properties:")
    for property_name, values in FLEX_CONTAINER_PROPERTIES.items():
        print(f"  {property_name:18} -> {values}")

    print("\nItem properties:")
    for property_name, values in FLEX_ITEM_PROPERTIES.items():
        print(f"  {property_name:18} -> {values}")


# ---------------------------------------------------------------------------
# 3. AXES AND DIRECTION
# ---------------------------------------------------------------------------

def explain_axes(direction: FlexDirection) -> None:
    """
    Explain the relationship between flex-direction and the axes.

    Main axis:
        Direction in which flex items are laid out.

    Cross axis:
        Axis perpendicular to the main axis.

    Important:
        justify-content works on the main axis.
        align-items and align-self work on the cross axis.
        This relationship is more important than memorizing "horizontal"
        versus "vertical".
    """
    if direction in (FlexDirection.ROW, FlexDirection.ROW_REVERSE):
        main_axis = "horizontal"
        cross_axis = "vertical"
    else:
        main_axis = "vertical"
        cross_axis = "horizontal"

    print(f"\nDirection: {direction.value}")
    print(f"  Main axis : {main_axis}")
    print(f"  Cross axis: {cross_axis}")
    print("  justify-content -> main axis")
    print("  align-items     -> cross axis")
    print("  align-self      -> cross axis for an individual item")


# ---------------------------------------------------------------------------
# 4. FLEX-BASIS, FLEX-GROW, FLEX-SHRINK
# ---------------------------------------------------------------------------

def distribute_positive_free_space(
    container_size: float,
    items: Sequence[FlexItem],
    gap: float = 0.0,
) -> Dict[str, float]:
    """
    Simplified positive-free-space distribution.

    When the sum of hypothetical item sizes plus gaps is smaller than the
    container's main size, the remaining space is positive free space.

    Each item's share is approximately:

        item.grow / sum(all grow factors) * free_space

    This function also applies simple min/max constraints after distribution.
    Real browser layout can perform multiple freeze-and-resolve passes.
    """
    if container_size < 0:
        raise ValueError("container_size cannot be negative")
    if gap < 0:
        raise ValueError("gap cannot be negative")
    if not items:
        return {}

    total_basis = sum(item.basis for item in items)
    total_gaps = gap * max(0, len(items) - 1)
    free_space = container_size - total_basis - total_gaps

    sizes = {item.name: item.basis for item in items}

    if free_space <= 0:
        return sizes

    total_grow = sum(item.grow for item in items)
    if total_grow == 0:
        return sizes

    for item in items:
        share = free_space * (item.grow / total_grow)
        proposed = item.basis + share

        if item.min_size is not None:
            proposed = max(proposed, item.min_size)

        if item.max_size is not None:
            proposed = min(proposed, item.max_size)

        sizes[item.name] = proposed

    return sizes


def distribute_negative_free_space(
    container_size: float,
    items: Sequence[FlexItem],
    gap: float = 0.0,
) -> Dict[str, float]:
    """
    Simplified negative-free-space distribution.

    If flex items require more space than the container provides, shrinking
    occurs according to scaled shrink factors:

        scaled factor = flex-shrink * flex-basis

    The real specification contains freezing and constraint resolution;
    this function demonstrates the central principle without pretending to
    be a complete browser layout engine.
    """
    if container_size < 0:
        raise ValueError("container_size cannot be negative")
    if gap < 0:
        raise ValueError("gap cannot be negative")
    if not items:
        return {}

    total_basis = sum(item.basis for item in items)
    total_gaps = gap * max(0, len(items) - 1)
    negative_space = container_size - total_basis - total_gaps

    sizes = {item.name: item.basis for item in items}

    if negative_space >= 0:
        return sizes

    deficit = -negative_space
    scaled_factors = {
        item.name: item.shrink * item.basis
        for item in items
    }
    total_factor = sum(scaled_factors.values())

    if total_factor == 0:
        return sizes

    for item in items:
        reduction = deficit * scaled_factors[item.name] / total_factor
        proposed = item.basis - reduction

        if item.min_size is not None:
            proposed = max(proposed, item.min_size)

        if item.max_size is not None:
            proposed = min(proposed, item.max_size)

        sizes[item.name] = max(0.0, proposed)

    return sizes


def demonstrate_flex_sizing() -> None:
    print("\n=== FLEX SIZING ===")

    items = [
        FlexItem("A", basis=100, grow=1),
        FlexItem("B", basis=100, grow=2),
        FlexItem("C", basis=100, grow=1),
    ]

    positive = distribute_positive_free_space(500, items, gap=10)

    print("\nPositive free space:")
    print("Container = 500px, gap = 10px")
    for name, size in positive.items():
        print(f"  {name}: {size:.2f}px")

    shrinking_items = [
        FlexItem("A", basis=300, shrink=1),
        FlexItem("B", basis=200, shrink=2),
        FlexItem("C", basis=100, shrink=1),
    ]

    negative = distribute_negative_free_space(
        500,
        shrinking_items,
        gap=10,
    )

    print("\nNegative free space:")
    print("Container = 500px, gap = 10px")
    for name, size in negative.items():
        print(f"  {name}: {size:.2f}px")


# ---------------------------------------------------------------------------
# 5. THE FLEX SHORTHAND
# ---------------------------------------------------------------------------

def expand_flex_shorthand(value: str) -> Tuple[float, float, str]:
    """
    Parse common flex shorthand forms.

    Common patterns:
        flex: 1
        flex: 2
        flex: 1 1 200px
        flex: 0 1 auto

    CSS has additional grammar forms. This educational parser focuses on
    frequently used forms and rejects unsupported or malformed input.
    """
    parts = value.strip().split()

    if not parts:
        raise ValueError("flex shorthand cannot be empty")

    if len(parts) == 1:
        token = parts[0]

        if token == "none":
            return 0.0, 0.0, "auto"

        if token == "auto":
            return 1.0, 1.0, "auto"

        if token == "initial":
            return 0.0, 1.0, "auto"

        try:
            grow = float(token)
        except ValueError as exc:
            raise ValueError(
                f"Unsupported one-value flex shorthand: {value}"
            ) from exc

        return grow, 1.0, "0%"

    if len(parts) == 2:
        try:
            grow = float(parts[0])
            shrink = float(parts[1])
        except ValueError as exc:
            raise ValueError(
                "Two-value form must contain numeric grow and shrink values"
            ) from exc

        return grow, shrink, "0%"

    if len(parts) == 3:
        try:
            grow = float(parts[0])
            shrink = float(parts[1])
        except ValueError as exc:
            raise ValueError(
                "First two flex shorthand values must be numbers"
            ) from exc

        basis = parts[2]
        return grow, shrink, basis

    raise ValueError(f"Unsupported flex shorthand: {value}")


def demonstrate_flex_shorthand() -> None:
    print("\n=== FLEX SHORTHAND ===")

    examples = [
        "1",
        "2",
        "1 1 200px",
        "0 1 auto",
        "none",
        "auto",
        "initial",
    ]

    for example in examples:
        try:
            grow, shrink, basis = expand_flex_shorthand(example)
            print(
                f"  flex: {example:12} -> "
                f"grow={grow}, shrink={shrink}, basis={basis}"
            )
        except ValueError as error:
            print(f"  flex: {example:12} -> ERROR: {error}")


# ---------------------------------------------------------------------------
# 6. JUSTIFY-CONTENT SIMULATION
# ---------------------------------------------------------------------------

def justify_positions(
    container_size: float,
    item_sizes: Sequence[float],
    justify: JustifyContent,
) -> List[float]:
    """
    Return simplified starting positions for one flex line.

    The function assumes:
      * one line
      * no margins
      * no auto margins
      * no wrapping
      * fixed item sizes
    """
    if container_size < 0:
        raise ValueError("container_size cannot be negative")
    if any(size < 0 for size in item_sizes):
        raise ValueError("item sizes cannot be negative")

    if not item_sizes:
        return []

    occupied = sum(item_sizes)
    free = container_size - occupied

    if free < 0:
        # Overflow is intentionally represented as sequential placement.
        return sequential_positions(item_sizes)

    count = len(item_sizes)

    if justify == JustifyContent.FLEX_START:
        leading = 0
        between = 0

    elif justify == JustifyContent.FLEX_END:
        leading = free
        between = 0

    elif justify == JustifyContent.CENTER:
        leading = free / 2
        between = 0

    elif justify == JustifyContent.SPACE_BETWEEN:
        leading = 0
        between = free / (count - 1) if count > 1 else 0

    elif justify == JustifyContent.SPACE_AROUND:
        between = free / count if count else 0
        leading = between / 2

    elif justify == JustifyContent.SPACE_EVENLY:
        between = free / (count + 1)
        leading = between

    else:
        raise ValueError(f"Unsupported justify-content: {justify}")

    positions: List[float] = []
    cursor = leading

    for size in item_sizes:
        positions.append(cursor)
        cursor += size + between

    return positions


def sequential_positions(item_sizes: Sequence[float]) -> List[float]:
    """Return sequential positions without extra free-space distribution."""
    positions: List[float] = []
    cursor = 0.0

    for size in item_sizes:
        positions.append(cursor)
        cursor += size

    return positions


def demonstrate_justify_content() -> None:
    print("\n=== JUSTIFY-CONTENT ===")

    item_sizes = [80, 100, 60]

    for mode in JustifyContent:
        positions = justify_positions(500, item_sizes, mode)
        formatted = ", ".join(f"{position:.1f}px" for position in positions)
        print(f"  {mode.value:15} -> {formatted}")


# ---------------------------------------------------------------------------
# 7. ALIGN-ITEMS CONCEPT
# ---------------------------------------------------------------------------

def align_item_position(
    container_cross_size: float,
    item_cross_size: float,
    alignment: AlignItems,
) -> float:
    """
    Return the simplified cross-axis offset of one item.

    Baseline alignment depends on font metrics in a real browser and therefore
    cannot be represented accurately with only geometric dimensions.
    """
    if container_cross_size < 0 or item_cross_size < 0:
        raise ValueError("sizes cannot be negative")

    if alignment == AlignItems.FLEX_START:
        return 0.0

    if alignment == AlignItems.FLEX_END:
        return max(0.0, container_cross_size - item_cross_size)

    if alignment == AlignItems.CENTER:
        return max(0.0, (container_cross_size - item_cross_size) / 2)

    if alignment == AlignItems.STRETCH:
        # A stretched item normally occupies the line's cross size when its
        # cross-axis size is auto. Offset is still at the line's start.
        return 0.0

    if alignment == AlignItems.BASELINE:
        # A simplified geometric approximation only.
        return 0.0

    raise ValueError(f"Unsupported alignment: {alignment}")


def demonstrate_alignment() -> None:
    print("\n=== ALIGN-ITEMS ===")

    container_height = 300
    item_height = 80

    for alignment in AlignItems:
        offset = align_item_position(
            container_height,
            item_height,
            alignment,
        )
        print(
            f"  {alignment.value:12} -> "
            f"cross-axis offset {offset:.1f}px"
        )


# ---------------------------------------------------------------------------
# 8. WRAPPING INTO FLEX LINES
# ---------------------------------------------------------------------------

@dataclass
class FlexLine:
    items: List[FlexItem] = field(default_factory=list)
    used_main_size: float = 0.0


def create_flex_lines(
    container_size: float,
    items: Sequence[FlexItem],
    gap: float = 0.0,
) -> List[FlexLine]:
    """
    Group items into lines according to their basis sizes.

    This is a simplified model:
      * basis is treated as the hypothetical main size
      * margins are ignored
      * min/max resolution is simplified
      * flex growth/shrink is handled separately
    """
    if container_size < 0:
        raise ValueError("container_size cannot be negative")
    if gap < 0:
        raise ValueError("gap cannot be negative")

    ordered_items = sorted(
        items,
        key=lambda item: (item.order, items.index(item)),
    )

    lines: List[FlexLine] = []
    current = FlexLine()

    for item in ordered_items:
        required = item.basis
        if current.items:
            required += gap

        if (
            current.items
            and current.used_main_size + required > container_size
        ):
            lines.append(current)
            current = FlexLine()

        if current.items:
            current.used_main_size += gap

        current.items.append(item)
        current.used_main_size += item.basis

    if current.items:
        lines.append(current)

    return lines


def demonstrate_wrapping() -> None:
    print("\n=== FLEX-WRAP ===")

    items = [
        FlexItem("Card 1", 180),
        FlexItem("Card 2", 180),
        FlexItem("Card 3", 180),
        FlexItem("Card 4", 180),
        FlexItem("Card 5", 180),
    ]

    lines = create_flex_lines(600, items, gap=20)

    for index, line in enumerate(lines, start=1):
        names = ", ".join(item.name for item in line.items)
        print(
            f"  Line {index}: {names} "
            f"(basis used = {line.used_main_size:.0f}px)"
        )


# ---------------------------------------------------------------------------
# 9. ORDER AND ACCESSIBILITY
# ---------------------------------------------------------------------------

def visual_order(items: Sequence[FlexItem]) -> List[str]:
    """
    Return the visual order created by CSS order.

    Important accessibility principle:
    CSS order changes visual arrangement, but it should not be used as a
    substitute for meaningful DOM/source order. Keyboard navigation,
    screen-reader interpretation, and reading order can be affected by
    source structure rather than visual presentation.
    """
    return [
        item.name
        for item in sorted(
            items,
            key=lambda item: (item.order, items.index(item)),
        )
    ]


def demonstrate_order() -> None:
    print("\n=== ORDER ===")

    items = [
        FlexItem("Navigation", 100, order=0),
        FlexItem("Main content", 300, order=2),
        FlexItem("Sidebar", 150, order=1),
    ]

    print("DOM/source order:")
    print("  " + " -> ".join(item.name for item in items))

    print("Visual order:")
    print("  " + " -> ".join(visual_order(items)))

    print(
        "Important: source order should normally remain logical and "
        "accessible; visual order is a presentation mechanism."
    )


# ---------------------------------------------------------------------------
# 10. AUTO MARGINS
# ---------------------------------------------------------------------------

def auto_margin_example(
    container_size: float,
    fixed_item_sizes: Sequence[float],
) -> Tuple[float, float]:
    """
    Demonstrate the main idea behind an auto margin.

    With one auto margin and positive free space, that margin can absorb all
    remaining main-axis space. This is commonly used to push a navigation
    group or button toward an edge.
    """
    if container_size < 0:
        raise ValueError("container_size cannot be negative")
    if any(size < 0 for size in fixed_item_sizes):
        raise ValueError("item sizes cannot be negative")

    used = sum(fixed_item_sizes)
    free = max(0.0, container_size - used)

    return used, free


def demonstrate_auto_margin() -> None:
    print("\n=== AUTO MARGIN ===")

    used, auto_margin = auto_margin_example(
        800,
        [120, 220, 100],
    )

    print(f"Fixed item space: {used}px")
    print(f"One auto margin absorbs: {auto_margin}px")
    print(
        "Typical CSS pattern: margin-inline-start: auto; "
        "pushes a later item toward the opposite edge."
    )


# ---------------------------------------------------------------------------
# 11. COMMON FLEXBOX MISTAKES
# ---------------------------------------------------------------------------

def validate_common_configuration(
    container: FlexContainer,
    items: Sequence[FlexItem],
) -> List[str]:
    """
    Perform educational validation of common configuration mistakes.
    """
    warnings: List[str] = []

    if container.wrap == FlexWrap.NOWRAP and len(items) > 1:
        total = sum(item.basis for item in items)
        gaps = container.gap * (len(items) - 1)

        if total + gaps > container.main_size:
            warnings.append(
                "Items exceed the main-axis size while flex-wrap is nowrap; "
                "the line may overflow."
            )

    if any(item.order != 0 for item in items):
        warnings.append(
            "Non-default order changes visual order. Keep source order "
            "logical for accessibility."
        )

    if container.gap < 0:
        warnings.append("Negative gap is invalid.")

    for item in items:
        if item.grow > 0 and item.max_size is not None:
            warnings.append(
                f"{item.name} can grow but has max_size={item.max_size}px; "
                "growth may stop at the maximum."
            )

    return warnings


def demonstrate_validation() -> None:
    print("\n=== CONFIGURATION VALIDATION ===")

    container = FlexContainer(
        main_size=500,
        cross_size=300,
        wrap=FlexWrap.NOWRAP,
        gap=20,
    )

    items = [
        FlexItem("A", 250),
        FlexItem("B", 250),
        FlexItem("C", 250, order=1),
    ]

    warnings = validate_common_configuration(container, items)

    if warnings:
        for warning in warnings:
            print(f"  Warning: {warning}")
    else:
        print("  No educational warnings detected.")


# ---------------------------------------------------------------------------
# 12. RESPONSIVE CARD LAYOUT MODEL
# ---------------------------------------------------------------------------

@dataclass
class Card:
    title: str
    minimum_width: float
    content_height: float


def responsive_card_rows(
    container_width: float,
    cards: Sequence[Card],
    gap: float,
) -> List[List[Card]]:
    """
    Model a responsive card row arrangement.

    This resembles the conceptual behavior of:

        display: flex;
        flex-wrap: wrap;
        gap: ...;

    A card is placed on the current line while it fits; otherwise a new line
    is created.
    """
    if container_width <= 0:
        raise ValueError("container_width must be positive")
    if gap < 0:
        raise ValueError("gap cannot be negative")

    rows: List[List[Card]] = []
    current_row: List[Card] = []
    current_width = 0.0

    for card in cards:
        if card.minimum_width <= 0:
            raise ValueError("card minimum width must be positive")

        extra_gap = gap if current_row else 0.0

        if (
            current_row
            and current_width + extra_gap + card.minimum_width
            > container_width
        ):
            rows.append(current_row)
            current_row = []
            current_width = 0.0
            extra_gap = 0.0

        current_row.append(card)
        current_width += extra_gap + card.minimum_width

    if current_row:
        rows.append(current_row)

    return rows


def demonstrate_responsive_layout() -> None:
    print("\n=== RESPONSIVE CARD LAYOUT ===")

    cards = [
        Card("Python", 220, 160),
        Card("JavaScript", 220, 180),
        Card("C++", 220, 170),
        Card("Databases", 220, 150),
        Card("Networking", 220, 190),
        Card("Security", 220, 175),
    ]

    for width in (1200, 800, 500):
        rows = responsive_card_rows(width, cards, gap=20)
        print(f"\nContainer width: {width}px")

        for row_number, row in enumerate(rows, start=1):
            titles = ", ".join(card.title for card in row)
            print(f"  Row {row_number}: {titles}")


# ---------------------------------------------------------------------------
# 13. FLEXBOX VS OTHER LAYOUT MODELS
# ---------------------------------------------------------------------------

def compare_layout_models() -> None:
    print("\n=== FLEXBOX AND RELATED LAYOUT MODELS ===")

    comparison = {
        "Flexbox": (
            "One-dimensional layout; excellent for rows, columns, "
            "alignment, distribution, and component internals."
        ),
        "Grid": (
            "Two-dimensional layout; useful when rows and columns must "
            "be controlled together."
        ),
        "Block flow": (
            "Natural document flow; useful for normal vertical content."
        ),
        "Positioning": (
            "Useful for overlays and special spatial relationships; "
            "not a general replacement for normal layout."
        ),
    }

    for model, description in comparison.items():
        print(f"  {model:16}: {description}")


# ---------------------------------------------------------------------------
# 14. FLEXBOX CSS GENERATOR
# ---------------------------------------------------------------------------

def generate_flex_css(
    direction: str = "row",
    wrap: str = "wrap",
    justify: str = "space-between",
    align: str = "center",
    gap: str = "1rem",
) -> str:
    """
    Generate a small reusable Flexbox CSS rule.

    Validation here prevents common invalid values in educational examples.
    """
    valid_directions = {value.value for value in FlexDirection}
    valid_wraps = {value.value for value in FlexWrap}
    valid_justify = {value.value for value in JustifyContent}
    valid_align = {value.value for value in AlignItems}

    if direction not in valid_directions:
        raise ValueError("Invalid flex-direction")
    if wrap not in valid_wraps:
        raise ValueError("Invalid flex-wrap")
    if justify not in valid_justify:
        raise ValueError("Invalid justify-content")
    if align not in valid_align:
        raise ValueError("Invalid align-items")

    return (
        ".flex-container {\n"
        "    display: flex;\n"
        f"    flex-direction: {direction};\n"
        f"    flex-wrap: {wrap};\n"
        f"    justify-content: {justify};\n"
        f"    align-items: {align};\n"
        f"    gap: {gap};\n"
        "}"
    )


# ---------------------------------------------------------------------------
# 15. TESTING
# ---------------------------------------------------------------------------

def run_assertion_tests() -> None:
    """Small tests for the educational layout functions."""
    assert expand_flex_shorthand("1") == (1.0, 1.0, "0%")
    assert expand_flex_shorthand("1 1 200px") == (1.0, 1.0, "200px")
    assert justify_positions(300, [100], JustifyContent.CENTER) == [100.0]

    positions = justify_positions(
        400,
        [100, 100],
        JustifyContent.SPACE_BETWEEN,
    )
    assert positions == [0.0, 300.0]

    rows = responsive_card_rows(
        500,
        [
            Card("A", 200, 100),
            Card("B", 200, 100),
            Card("C", 200, 100),
        ],
        20,
    )
    assert len(rows) == 2

    lines = create_flex_lines(
        500,
        [
            FlexItem("A", 200),
            FlexItem("B", 200),
            FlexItem("C", 200),
        ],
        gap=20,
    )
    assert len(lines) == 2

    print("\n=== TESTS ===")
    print("All educational assertions passed.")


# ---------------------------------------------------------------------------
# 16. ADVANCED DISCUSSION THROUGH DATA
# ---------------------------------------------------------------------------

def print_advanced_considerations() -> None:
    considerations = [
        (
            "flex-basis versus width",
            "flex-basis controls the flex base size along the main axis; "
            "width is not always equivalent, especially in a column layout "
            "or when flex sizing and intrinsic sizing interact."
        ),
        (
            "min-width: auto",
            "Flex items can have an automatic minimum size based on content. "
            "A common practical pattern is min-width: 0 when a flex child "
            "must be allowed to shrink below its content's intrinsic width."
        ),
        (
            "gap versus margins",
            "gap expresses spacing between flex items and avoids edge-margin "
            "management. Margins remain useful when spacing must belong to "
            "individual items or when auto margins are needed."
        ),
        (
            "flex-grow",
            "Growth distributes positive free space according to grow factors."
        ),
        (
            "flex-shrink",
            "Shrink distributes negative free space using scaled shrink "
            "factors based on flex-shrink and the flex base size."
        ),
        (
            "wrapping",
            "When wrapping is enabled, items are collected into flex lines. "
            "Multi-line alignment introduces align-content."
        ),
        (
            "align-content",
            "It affects the distribution of multiple flex lines, not the "
            "individual items inside a single line."
        ),
        (
            "align-self",
            "It lets one flex item override the container's align-items value."
        ),
        (
            "writing modes",
            "Logical concepts such as main and cross axes are more reliable "
            "than assuming that row always means left-to-right."
        ),
        (
            "accessibility",
            "Visual rearrangement should not be used to create a confusing "
            "reading or keyboard-navigation order."
        ),
    ]

    print("\n=== ADVANCED CONSIDERATIONS ===")

    for title, explanation in considerations:
        print(f"\n{title}:")
        print(f"  {explanation}")


# ---------------------------------------------------------------------------
# 17. COMPLETE EXAMPLE CONFIGURATION
# ---------------------------------------------------------------------------

def complete_example() -> None:
    print("\n=== COMPLETE FLEXBOX EXAMPLE ===")

    container = FlexContainer(
        main_size=900,
        cross_size=400,
        direction=FlexDirection.ROW,
        wrap=FlexWrap.WRAP,
        justify_content=JustifyContent.SPACE_BETWEEN,
        align_items=AlignItems.CENTER,
        align_content=AlignContent.SPACE_AROUND,
        gap=24,
    )

    items = [
        FlexItem("Sidebar", 180, grow=0, shrink=1),
        FlexItem("Main", 420, grow=1, shrink=1, min_size=240),
        FlexItem("Actions", 160, grow=0, shrink=1),
    ]

    print(f"Container main size: {container.main_size}px")
    print(f"Container cross size: {container.cross_size}px")
    print(f"Direction: {container.direction.value}")
    print(f"Wrap: {container.wrap.value}")
    print(f"Justify: {container.justify_content.value}")
    print(f"Align items: {container.align_items.value}")
    print(f"Gap: {container.gap}px")

    sizes = distribute_positive_free_space(
        container.main_size,
        items,
        container.gap,
    )

    print("\nResolved simplified main-axis sizes:")
    for name, size in sizes.items():
        print(f"  {name}: {size:.2f}px")


# ---------------------------------------------------------------------------
# 18. PROGRAM ENTRY POINT
# ---------------------------------------------------------------------------

def main() -> None:
    print("FLEXBOX FUNDAMENTALS")
    print("====================")
    print(
        "This program models important CSS Flexbox concepts from basic "
        "terminology to simplified layout algorithms."
    )

    print_property_reference()

    for direction in FlexDirection:
        explain_axes(direction)

    demonstrate_flex_sizing()
    demonstrate_flex_shorthand()
    demonstrate_justify_content()
    demonstrate_alignment()
    demonstrate_wrapping()
    demonstrate_order()
    demonstrate_auto_margin()
    demonstrate_validation()
    demonstrate_responsive_layout()
    compare_layout_models()

    print("\n=== GENERATED CSS ===")
    print(
        generate_flex_css(
            direction="row",
            wrap="wrap",
            justify="space-between",
            align="center",
            gap="1rem",
        )
    )

    run_assertion_tests()
    print_advanced_considerations()
    complete_example()

    print("\n=== STUDY CHECKLIST ===")
    checklist = [
        "Understand flex container versus flex item.",
        "Understand main axis versus cross axis.",
        "Understand flex-direction.",
        "Understand flex-wrap.",
        "Understand justify-content.",
        "Understand align-items and align-self.",
        "Understand align-content for multiple lines.",
        "Understand flex-basis, flex-grow, and flex-shrink.",
        "Understand the flex shorthand.",
        "Understand gap and auto margins.",
        "Understand wrapping and line formation.",
        "Understand order and accessibility implications.",
        "Understand min/max constraints and intrinsic sizing.",
        "Understand when Grid is more appropriate.",
    ]

    for number, item in enumerate(checklist, start=1):
        print(f"{number:2}. {item}")


if __name__ == "__main__":
    main()
