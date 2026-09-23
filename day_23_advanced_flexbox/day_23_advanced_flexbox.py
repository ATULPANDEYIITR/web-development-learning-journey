"""
Advanced Flexbox: flex-grow, flex-shrink, flex-basis, ordering, nested layouts,
and common patterns.

This standalone study script models important Flexbox concepts without requiring
a browser. It combines:
1. Beginner-friendly demonstrations of the Flexbox mental model.
2. A simplified but useful flex sizing engine for grow/shrink/basis.
3. Ordering and nested-layout examples.
4. Common UI layout patterns.
5. Edge cases, validation, debugging information, and performance considerations.

The calculations intentionally explain the main Flexbox algorithm rather than
attempting to replace a browser's complete CSS layout engine. Real browsers
also account for min/max constraints, intrinsic sizes, min-width:auto behavior,
writing modes, aspect ratios, replaced elements, percentages, and many other
details.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Optional, Sequence


# ---------------------------------------------------------------------------
# 1. FUNDAMENTAL FLEXBOX VOCABULARY
# ---------------------------------------------------------------------------

def explain_fundamentals() -> None:
    print("\n" + "=" * 78)
    print("1. FLEXBOX FUNDAMENTALS")
    print("=" * 78)

    concepts = {
        "flex container": (
            "An element whose display value is flex or inline-flex. "
            "Its direct children become flex items."
        ),
        "main axis": (
            "The primary direction in which flex items are laid out. "
            "It is controlled by flex-direction."
        ),
        "cross axis": (
            "The axis perpendicular to the main axis."
        ),
        "flex-grow": (
            "A non-negative factor describing how an item participates "
            "in distributing positive free space."
        ),
        "flex-shrink": (
            "A non-negative factor describing how an item participates "
            "in distributing negative free space."
        ),
        "flex-basis": (
            "The initial main-size contribution used by the flex sizing "
            "algorithm before flexible growth or shrinking."
        ),
        "order": (
            "A property that changes an item's visual ordering within a "
            "flex container without changing normal DOM source order."
        ),
        "nested flexbox": (
            "A flex item can itself be a flex container, allowing layouts "
            "to be composed from multiple independent flex formatting contexts."
        ),
    }

    for name, explanation in concepts.items():
        print(f"\n{name}:")
        print(f"  {explanation}")


# ---------------------------------------------------------------------------
# 2. A SMALL FLEX SIZING MODEL
# ---------------------------------------------------------------------------

@dataclass
class FlexItem:
    """
    A simplified representation of a flex item.

    basis:
        The starting main size used by our educational sizing model.

    grow:
        flex-grow factor. Negative values are invalid in CSS.

    shrink:
        flex-shrink factor. Negative values are invalid in CSS.

    min_size / max_size:
        Optional simplified constraints used to demonstrate how a real
        layout can become more complicated than a simple proportional split.

    order:
        Visual ordering value. Lower values are placed first.

    name:
        Human-readable identifier.
    """

    name: str
    basis: float
    grow: float = 0.0
    shrink: float = 1.0
    order: int = 0
    min_size: Optional[float] = None
    max_size: Optional[float] = None
    final_size: Optional[float] = field(default=None, init=False)

    def validate(self) -> None:
        if self.basis < 0:
            raise ValueError(f"{self.name}: basis cannot be negative.")
        if self.grow < 0:
            raise ValueError(f"{self.name}: flex-grow cannot be negative.")
        if self.shrink < 0:
            raise ValueError(f"{self.name}: flex-shrink cannot be negative.")
        if self.min_size is not None and self.min_size < 0:
            raise ValueError(f"{self.name}: min_size cannot be negative.")
        if (
            self.min_size is not None
            and self.max_size is not None
            and self.min_size > self.max_size
        ):
            raise ValueError(
                f"{self.name}: min_size cannot exceed max_size."
            )


def calculate_positive_free_space(
    container_size: float,
    items: Sequence[FlexItem],
) -> float:
    """Return container space remaining after the flex bases."""
    total_basis = sum(item.basis for item in items)
    return container_size - total_basis


def calculate_negative_free_space(
    container_size: float,
    items: Sequence[FlexItem],
) -> float:
    """Return the amount by which the bases exceed the container."""
    total_basis = sum(item.basis for item in items)
    return max(0.0, total_basis - container_size)


def distribute_positive_free_space(
    container_size: float,
    items: Sequence[FlexItem],
) -> List[FlexItem]:
    """
    Simplified flex-grow distribution.

    If the total basis is smaller than the container, the remaining space is
    divided according to flex-grow factors.

    Example:
        container = 1000
        bases = 200, 200
        grow = 1, 3

        free space = 600
        item A receives 150
        item B receives 450
    """
    for item in items:
        item.validate()

    free_space = calculate_positive_free_space(container_size, items)

    if free_space <= 0:
        for item in items:
            item.final_size = item.basis
        return list(items)

    total_grow = sum(item.grow for item in items)

    if total_grow == 0:
        for item in items:
            item.final_size = item.basis
        return list(items)

    for item in items:
        addition = free_space * (item.grow / total_grow)
        item.final_size = item.basis + addition

    return list(items)


def distribute_negative_free_space(
    container_size: float,
    items: Sequence[FlexItem],
) -> List[FlexItem]:
    """
    Simplified flex-shrink distribution.

    A crucial detail is that shrink is not normally proportional to the raw
    shrink factor alone. The flex base size participates in the scaled
    shrink factor:

        scaled shrink factor = flex-shrink * flex-basis

    This explains why two items with equal shrink values can lose different
    amounts of space when their bases differ.
    """
    for item in items:
        item.validate()

    negative_space = calculate_negative_free_space(container_size, items)

    if negative_space <= 0:
        for item in items:
            item.final_size = item.basis
        return list(items)

    scaled_factors = [
        item.shrink * item.basis
        for item in items
    ]
    total_scaled_factor = sum(scaled_factors)

    if total_scaled_factor == 0:
        for item in items:
            item.final_size = item.basis
        return list(items)

    for item, scaled_factor in zip(items, scaled_factors):
        reduction = negative_space * (
            scaled_factor / total_scaled_factor
        )
        item.final_size = max(0.0, item.basis - reduction)

    return list(items)


def resolve_flexible_sizes(
    container_size: float,
    items: Sequence[FlexItem],
) -> List[FlexItem]:
    """
    Choose grow or shrink behavior based on the total basis.

    This is deliberately simpler than the full browser algorithm. It is useful
    for understanding the relationship between basis, grow, and shrink.
    """
    if not items:
        return []

    total_basis = sum(item.basis for item in items)

    if total_basis < container_size:
        return distribute_positive_free_space(container_size, items)

    if total_basis > container_size:
        return distribute_negative_free_space(container_size, items)

    for item in items:
        item.final_size = item.basis

    return list(items)


def print_sizes(items: Iterable[FlexItem]) -> None:
    for item in items:
        print(
            f"{item.name:15} "
            f"basis={item.basis:7.2f} "
            f"grow={item.grow:5.2f} "
            f"shrink={item.shrink:5.2f} "
            f"final={item.final_size if item.final_size is not None else '-':>7}"
        )


# ---------------------------------------------------------------------------
# 3. FLEX-GROW
# ---------------------------------------------------------------------------

def demonstrate_flex_grow() -> None:
    print("\n" + "=" * 78)
    print("2. FLEX-GROW")
    print("=" * 78)

    print(
        """
flex-grow controls how positive free space is distributed.

Suppose a 1000px container contains:
    Item A: basis 200px, grow 1
    Item B: basis 200px, grow 3

Total basis = 400px
Free space = 600px
Total grow factor = 4

A receives 600 * 1/4 = 150px extra.
B receives 600 * 3/4 = 450px extra.

Final sizes:
    A = 350px
    B = 650px
"""
    )

    items = [
        FlexItem("Item A", basis=200, grow=1),
        FlexItem("Item B", basis=200, grow=3),
    ]

    resolve_flexible_sizes(1000, items)
    print_sizes(items)

    print("\nImportant distinction:")
    print("flex-grow does not mean 'make this item this many pixels wider'.")
    print("It is a proportional factor for distributing available free space.")


# ---------------------------------------------------------------------------
# 4. FLEX-SHRINK
# ---------------------------------------------------------------------------

def demonstrate_flex_shrink() -> None:
    print("\n" + "=" * 78)
    print("3. FLEX-SHRINK")
    print("=" * 78)

    print(
        """
Consider a 500px container:

    Item A: basis 400px, shrink 1
    Item B: basis 300px, shrink 1

Total basis = 700px
Overflow = 200px

The scaled shrink factors are:
    A: 400 * 1 = 400
    B: 300 * 1 = 300

Therefore A gives up 200 * 400/700.
B gives up 200 * 300/700.

Equal flex-shrink values do not necessarily mean equal pixel reductions.
"""
    )

    items = [
        FlexItem("Large item", basis=400, shrink=1),
        FlexItem("Small item", basis=300, shrink=1),
    ]

    resolve_flexible_sizes(500, items)
    print_sizes(items)


# ---------------------------------------------------------------------------
# 5. FLEX-BASIS
# ---------------------------------------------------------------------------

def demonstrate_flex_basis() -> None:
    print("\n" + "=" * 78)
    print("4. FLEX-BASIS")
    print("=" * 78)

    print(
        """
flex-basis establishes the initial main-size contribution.

Conceptually:
    flex-basis: 250px
    flex-basis: 30%
    flex-basis: auto
    flex-basis: 0

The difference between 0 and auto is particularly important.

With flex: 1, browsers commonly interpret the shorthand as:
    flex: 1 1 0%

This means the items compete for free space from a zero basis rather than
starting from their content sizes.

With:
    flex: 1 1 auto

the existing main-size/content contribution can influence the initial sizes.
"""
    )

    equal_distribution = [
        FlexItem("A", basis=0, grow=1),
        FlexItem("B", basis=0, grow=1),
        FlexItem("C", basis=0, grow=1),
    ]

    resolve_flexible_sizes(900, equal_distribution)

    print("Three flex: 1 style items represented with a zero basis:")
    print_sizes(equal_distribution)

    content_weighted = [
        FlexItem("Short content", basis=100, grow=1),
        FlexItem("Long content", basis=300, grow=1),
    ]

    resolve_flexible_sizes(900, content_weighted)

    print("\nTwo flex: 1 1 auto style items with different bases:")
    print_sizes(content_weighted)


# ---------------------------------------------------------------------------
# 6. FLEX SHORTHAND
# ---------------------------------------------------------------------------

def demonstrate_flex_shorthand() -> None:
    print("\n" + "=" * 78)
    print("5. THE FLEX SHORTHAND")
    print("=" * 78)

    examples = [
        ("flex: 1", "Commonly treated as flex-grow: 1; flex-shrink: 1; flex-basis: 0%."),
        ("flex: 0 1 auto", "Does not grow, may shrink, and uses the auto basis."),
        ("flex: 1 1 auto", "Can grow and shrink while using an auto basis."),
        ("flex: 0 0 240px", "Fixed 240px basis with no growing or shrinking."),
        ("flex: 2 1 200px", "Starts around 200px and participates in flexible sizing."),
    ]

    for syntax, meaning in examples:
        print(f"{syntax:20} -> {meaning}")


# ---------------------------------------------------------------------------
# 7. ORDERING
# ---------------------------------------------------------------------------

def demonstrate_order() -> None:
    print("\n" + "=" * 78)
    print("6. ORDER")
    print("=" * 78)

    items = [
        {"name": "Header", "order": 0},
        {"name": "Navigation", "order": 2},
        {"name": "Main content", "order": 1},
        {"name": "Footer", "order": 3},
        {"name": "Alert", "order": -1},
    ]

    print("DOM/source order:")
    print(" -> ".join(item["name"] for item in items))

    visual_order = sorted(items, key=lambda item: item["order"])

    print("\nVisual order:")
    print(" -> ".join(item["name"] for item in visual_order))

    print(
        """
Accessibility warning:
Changing visual order does not necessarily change the logical DOM order.
Keyboard navigation, screen-reader reading order, focus management, and
meaningful source structure should be considered before using order extensively.
"""
    )


# ---------------------------------------------------------------------------
# 8. DIRECTION AND AXES
# ---------------------------------------------------------------------------

def demonstrate_axes() -> None:
    print("\n" + "=" * 78)
    print("7. MAIN AXIS AND CROSS AXIS")
    print("=" * 78)

    examples = {
        "row": ("main axis = horizontal", "cross axis = vertical"),
        "row-reverse": ("main axis = horizontal, reversed", "cross axis = vertical"),
        "column": ("main axis = vertical", "cross axis = horizontal"),
        "column-reverse": ("main axis = vertical, reversed", "cross axis = horizontal"),
    }

    for direction, (main_axis, cross_axis) in examples.items():
        print(f"{direction:15} | {main_axis:35} | {cross_axis}")


# ---------------------------------------------------------------------------
# 9. NESTED FLEX LAYOUTS
# ---------------------------------------------------------------------------

@dataclass
class Panel:
    name: str
    children: List[str]


def demonstrate_nested_layouts() -> None:
    print("\n" + "=" * 78)
    print("8. NESTED FLEXBOX")
    print("=" * 78)

    layout = {
        "page": Panel(
            "page",
            ["topbar", "content-area", "footer"],
        ),
        "content-area": Panel(
            "content-area",
            ["sidebar", "main"],
        ),
        "main": Panel(
            "main",
            ["toolbar", "article", "actions"],
        ),
        "toolbar": Panel(
            "toolbar",
            ["title", "search", "profile"],
        ),
    }

    def show_panel(name: str, level: int = 0) -> None:
        panel = layout.get(name)
        if panel is None:
            return

        print("  " * level + f"- {panel.name}")
        for child in panel.children:
            show_panel(child, level + 1)

    show_panel("page")

    print(
        """
A nested layout works because a flex item may also be a flex container.

For example:
    page -> flex column
    content-area -> flex row
    main -> flex column
    toolbar -> flex row

Each container establishes its own local main axis and cross axis.
"""
    )


# ---------------------------------------------------------------------------
# 10. COMMON PATTERN: NAVBAR
# ---------------------------------------------------------------------------

def demonstrate_navbar_pattern() -> None:
    print("\n" + "=" * 78)
    print("9. COMMON PATTERN: NAVBAR")
    print("=" * 78)

    print(
        """
HTML structure conceptually:

<nav>
    <div class="brand">Brand</div>
    <div class="links">...</div>
    <div class="actions">...</div>
</nav>

A typical CSS strategy is:
    nav { display: flex; align-items: center; }
    .brand { flex: 0 0 auto; }
    .links { flex: 1 1 auto; }
    .actions { flex: 0 0 auto; }

The flexible middle section consumes available space while the brand and
actions retain their intrinsic sizes.
"""
    )


# ---------------------------------------------------------------------------
# 11. COMMON PATTERN: SIDEBAR + CONTENT
# ---------------------------------------------------------------------------

def demonstrate_sidebar_pattern() -> None:
    print("\n" + "=" * 78)
    print("10. COMMON PATTERN: SIDEBAR + CONTENT")
    print("=" * 78)

    items = [
        FlexItem("Sidebar", basis=260, grow=0, shrink=0),
        FlexItem("Main content", basis=0, grow=1, shrink=1),
    ]

    resolve_flexible_sizes(1200, items)
    print_sizes(items)

    print(
        """
A common implementation is:

    .layout {
        display: flex;
    }

    .sidebar {
        flex: 0 0 260px;
    }

    .main {
        flex: 1 1 0;
        min-width: 0;
    }

The min-width: 0 detail matters because flex items can otherwise resist
shrinking due to their minimum content size in common browser situations.
"""
    )


# ---------------------------------------------------------------------------
# 12. COMMON PATTERN: CARD ROW
# ---------------------------------------------------------------------------

def demonstrate_cards() -> None:
    print("\n" + "=" * 78)
    print("11. COMMON PATTERN: CARD ROW")
    print("=" * 78)

    cards = [
        FlexItem("Card 1", basis=240, grow=1, shrink=1),
        FlexItem("Card 2", basis=240, grow=1, shrink=1),
        FlexItem("Card 3", basis=240, grow=1, shrink=1),
    ]

    for width in (800, 1200, 1600):
        print(f"\nContainer width: {width}px")
        resolve_flexible_sizes(width, cards)
        print_sizes(cards)


# ---------------------------------------------------------------------------
# 13. WRAPPING CONCEPT
# ---------------------------------------------------------------------------

def wrap_into_lines(
    container_size: float,
    items: Sequence[FlexItem],
) -> List[List[FlexItem]]:
    """
    Simple educational model for flex-wrap.

    This packs items onto lines using their bases. It does not implement the
    complete CSS line formation algorithm, but it illustrates why wrapping
    changes the problem from one global row into multiple flex lines.
    """
    lines: List[List[FlexItem]] = []
    current: List[FlexItem] = []
    current_size = 0.0

    for item in items:
        if item.basis > container_size:
            if current:
                lines.append(current)
                current = []
                current_size = 0.0

            lines.append([item])
            continue

        if current and current_size + item.basis > container_size:
            lines.append(current)
            current = []
            current_size = 0.0

        current.append(item)
        current_size += item.basis

    if current:
        lines.append(current)

    return lines


def demonstrate_wrapping() -> None:
    print("\n" + "=" * 78)
    print("12. FLEX-WRAP")
    print("=" * 78)

    items = [
        FlexItem("A", 280),
        FlexItem("B", 280),
        FlexItem("C", 280),
        FlexItem("D", 280),
        FlexItem("E", 280),
    ]

    lines = wrap_into_lines(900, items)

    for number, line in enumerate(lines, start=1):
        print(
            f"Line {number}: "
            + ", ".join(item.name for item in line)
        )

    print(
        """
With flex-wrap: wrap, items can form multiple flex lines. Each line has its
own flexible sizing process. align-content can then affect the distribution
of the lines along the cross axis when there is extra cross-axis space.
"""
    )


# ---------------------------------------------------------------------------
# 14. MINIMUM AND MAXIMUM CONSTRAINTS
# ---------------------------------------------------------------------------

def apply_size_constraints(items: Sequence[FlexItem]) -> None:
    """
    Apply simple min/max constraints after a proportional calculation.

    A real browser's algorithm freezes and redistributes space when constraints
    are violated. This helper is intentionally explicit so the educational
    effect is visible.
    """
    for item in items:
        if item.final_size is None:
            item.final_size = item.basis

        if item.min_size is not None:
            item.final_size = max(item.final_size, item.min_size)

        if item.max_size is not None:
            item.final_size = min(item.final_size, item.max_size)


def demonstrate_constraints() -> None:
    print("\n" + "=" * 78)
    print("13. MIN/MAX CONSTRAINTS")
    print("=" * 78)

    items = [
        FlexItem(
            "Sidebar",
            basis=200,
            grow=1,
            min_size=180,
            max_size=320,
        ),
        FlexItem(
            "Content",
            basis=200,
            grow=3,
            min_size=300,
        ),
    ]

    resolve_flexible_sizes(1000, items)
    apply_size_constraints(items)
    print_sizes(items)

    print(
        """
The real CSS algorithm is iterative. When an item reaches a min-width or
max-width constraint, it can become frozen and the remaining free space is
redistributed among the other flexible items.

This is one reason browser layout cannot be reduced to a single arithmetic
formula.
"""
    )


# ---------------------------------------------------------------------------
# 15. EDGE CASES
# ---------------------------------------------------------------------------

def demonstrate_edge_cases() -> None:
    print("\n" + "=" * 78)
    print("14. EDGE CASES")
    print("=" * 78)

    cases = [
        (
            "No free space",
            600,
            [FlexItem("A", 300, grow=1), FlexItem("B", 300, grow=1)],
        ),
        (
            "Positive space but zero grow",
            1000,
            [FlexItem("A", 200), FlexItem("B", 300)],
        ),
        (
            "Zero basis",
            900,
            [FlexItem("A", 0, grow=1), FlexItem("B", 0, grow=2)],
        ),
        (
            "Overflow with zero shrink",
            500,
            [FlexItem("A", 400, shrink=0), FlexItem("B", 300, shrink=0)],
        ),
    ]

    for title, width, items in cases:
        print(f"\n{title}")
        resolve_flexible_sizes(width, items)
        print_sizes(items)

    print(
        """
Important browser-level edge cases include:

- Long unbreakable strings.
- Images with intrinsic dimensions.
- min-width:auto behavior.
- Percentage flex-basis values.
- Nested containers with constrained widths.
- flex-wrap combined with align-content.
- Vertical writing modes.
- Aspect-ratio interactions.
- Overflow caused by content.
- Min/max constraints that cause iterative redistribution.
"""
    )


# ---------------------------------------------------------------------------
# 16. COMMON MISTAKES
# ---------------------------------------------------------------------------

def demonstrate_common_mistakes() -> None:
    print("\n" + "=" * 78)
    print("15. COMMON MISTAKES")
    print("=" * 78)

    mistakes = [
        (
            "Mistake",
            "Using width when flex-basis is the more direct main-axis control.",
            "Use flex-basis when the component's flexible sizing should start from a controlled basis.",
        ),
        (
            "Mistake",
            "Assuming flex-grow is a percentage width.",
            "Treat grow as a ratio for distributing positive free space.",
        ),
        (
            "Mistake",
            "Assuming equal shrink means equal pixel loss.",
            "Remember that the basis participates in the scaled shrink factor.",
        ),
        (
            "Mistake",
            "Using order to repair a poor semantic DOM structure.",
            "Keep logical source order meaningful and use order sparingly.",
        ),
        (
            "Mistake",
            "Forgetting min-width: 0 in a shrinking content area.",
            "Test long content and explicitly control minimum size when appropriate.",
        ),
        (
            "Mistake",
            "Expecting align-items to distribute items along the main axis.",
            "justify-content operates along the main axis; align-items operates along the cross axis.",
        ),
    ]

    for category, mistake, correction in mistakes:
        print(f"\n{category}: {mistake}")
        print(f"Correction: {correction}")


# ---------------------------------------------------------------------------
# 17. DEBUGGING
# ---------------------------------------------------------------------------

def demonstrate_debugging() -> None:
    print("\n" + "=" * 78)
    print("16. DEBUGGING FLEXBOX")
    print("=" * 78)

    debugging_steps = [
        "Identify the flex container.",
        "Check display: flex or inline-flex.",
        "Determine flex-direction and therefore the main axis.",
        "Inspect flex-basis, width/height, and intrinsic content.",
        "Check flex-grow and flex-shrink.",
        "Check min-width/min-height and max-width/max-height.",
        "Check whether wrapping is enabled.",
        "Inspect justify-content and align-items.",
        "Inspect each item's computed size in browser developer tools.",
        "Test long text, narrow widths, and unusually large content.",
    ]

    for number, step in enumerate(debugging_steps, start=1):
        print(f"{number:2}. {step}")


# ---------------------------------------------------------------------------
# 18. PERFORMANCE AND DESIGN
# ---------------------------------------------------------------------------

def demonstrate_performance_considerations() -> None:
    print("\n" + "=" * 78)
    print("17. PERFORMANCE AND DESIGN CONSIDERATIONS")
    print("=" * 78)

    points = [
        "Prefer a simple layout hierarchy rather than unnecessary nesting.",
        "Avoid forcing frequent synchronous layout measurements in JavaScript.",
        "Batch DOM reads and writes when manipulating layouts dynamically.",
        "Avoid excessive resize handlers; use ResizeObserver when appropriate.",
        "Use CSS for static layout rules rather than JavaScript calculations.",
        "Test responsive behavior at narrow, medium, and wide sizes.",
        "Be careful with large lists, nested flex containers, and expensive descendants.",
        "Use semantic HTML independently of visual Flexbox ordering.",
    ]

    for point in points:
        print(f"- {point}")


# ---------------------------------------------------------------------------
# 19. RESPONSIVE DESIGN MODEL
# ---------------------------------------------------------------------------

def responsive_card_sizes(
    viewport_width: int,
    minimum_card_width: int = 240,
    gap: int = 24,
) -> int:
    """
    Estimate how many cards can fit in one row.

    This is a teaching utility, not a browser CSS replacement.
    """
    if viewport_width <= 0:
        raise ValueError("Viewport width must be positive.")

    if minimum_card_width <= 0:
        raise ValueError("Minimum card width must be positive.")

    if gap < 0:
        raise ValueError("Gap cannot be negative.")

    return max(
        1,
        (viewport_width + gap) // (minimum_card_width + gap),
    )


def demonstrate_responsive_design() -> None:
    print("\n" + "=" * 78)
    print("18. RESPONSIVE FLEXBOX THINKING")
    print("=" * 78)

    for viewport in (360, 768, 1024, 1440, 1920):
        columns = responsive_card_sizes(viewport)
        print(
            f"Viewport {viewport:4}px -> approximately "
            f"{columns} card(s) per row"
        )

    print(
        """
Flexbox can often express responsive relationships without manually
calculating every width. A common pattern is:

    display: flex;
    flex-wrap: wrap;
    gap: 1rem;

    .card {
        flex: 1 1 240px;
    }

This says that cards prefer a 240px basis, can grow, and can shrink,
while wrapping allows the collection to move onto additional lines.
"""
    )


# ---------------------------------------------------------------------------
# 20. ADVANCED COMPARISON OF FLEX VALUES
# ---------------------------------------------------------------------------

def compare_flex_values() -> None:
    print("\n" + "=" * 78)
    print("19. COMPARING COMMON FLEX VALUES")
    print("=" * 78)

    examples = {
        "flex: 1": "Strong equal-sharing pattern when items should divide available space.",
        "flex: 1 1 auto": "Flexible item whose intrinsic/main-size contribution matters.",
        "flex: 0 0 auto": "No flexible growth or shrink; retain automatic size.",
        "flex: 0 0 250px": "Fixed 250px basis with no flexible resizing.",
        "flex: 2 1 200px": "Starts from 200px and receives twice the grow share of a grow-1 sibling.",
        "flex: 0 1 300px": "Prefers 300px, does not grow, but may shrink.",
    }

    for value, description in examples.items():
        print(f"{value:22} -> {description}")


# ---------------------------------------------------------------------------
# 21. MINI RESPONSIVE DASHBOARD MODEL
# ---------------------------------------------------------------------------

@dataclass
class DashboardRegion:
    name: str
    basis: float
    grow: float
    shrink: float


def simulate_dashboard(width: float) -> None:
    """
    Simulate a common dashboard:
        sidebar + content
        content contains a toolbar and flexible panels conceptually.
    """
    print(f"\nDashboard width = {width}px")

    regions = [
        DashboardRegion("Sidebar", 260, 0, 0),
        DashboardRegion("Main", 700, 1, 1),
    ]

    items = [
        FlexItem(
            region.name,
            region.basis,
            region.grow,
            region.shrink,
        )
        for region in regions
    ]

    resolve_flexible_sizes(width, items)
    print_sizes(items)

    if width < 700:
        print(
            "Design note: a real responsive dashboard might switch to a "
            "different layout instead of forcing this row to remain."
        )


def demonstrate_dashboard() -> None:
    print("\n" + "=" * 78)
    print("20. INDUSTRY-STYLE DASHBOARD MODEL")
    print("=" * 78)

    for width in (1400, 1000, 800, 600):
        simulate_dashboard(width)


# ---------------------------------------------------------------------------
# 22. VALIDATION AND FAILURE HANDLING
# ---------------------------------------------------------------------------

def demonstrate_validation() -> None:
    print("\n" + "=" * 78)
    print("21. VALIDATION AND ERROR HANDLING")
    print("=" * 78)

    invalid_examples = [
        FlexItem("Negative basis", basis=-10),
        FlexItem("Negative grow", basis=100, grow=-1),
        FlexItem("Negative shrink", basis=100, shrink=-1),
        FlexItem("Invalid bounds", basis=100, min_size=300, max_size=200),
    ]

    for item in invalid_examples:
        try:
            item.validate()
        except ValueError as error:
            print(f"Caught validation error: {error}")


# ---------------------------------------------------------------------------
# 23. TESTS
# ---------------------------------------------------------------------------

def test_grow_distribution() -> None:
    items = [
        FlexItem("A", 200, grow=1),
        FlexItem("B", 200, grow=3),
    ]

    resolve_flexible_sizes(1000, items)

    assert round(items[0].final_size or 0, 6) == 350
    assert round(items[1].final_size or 0, 6) == 650


def test_shrink_distribution() -> None:
    items = [
        FlexItem("A", 400, shrink=1),
        FlexItem("B", 300, shrink=1),
    ]

    resolve_flexible_sizes(500, items)

    assert round(items[0].final_size or 0, 6) == round(500 - 200 * 400 / 700, 6)
    assert round(items[1].final_size or 0, 6) == round(500 - 200 * 300 / 700, 6)


def test_zero_grow() -> None:
    items = [
        FlexItem("A", 100, grow=0),
        FlexItem("B", 100, grow=0),
    ]

    resolve_flexible_sizes(500, items)

    assert items[0].final_size == 100
    assert items[1].final_size == 100


def test_order() -> None:
    items = [
        {"name": "C", "order": 2},
        {"name": "A", "order": 0},
        {"name": "B", "order": 1},
    ]

    result = [item["name"] for item in sorted(items, key=lambda x: x["order"])]

    assert result == ["A", "B", "C"]


def run_tests() -> None:
    print("\n" + "=" * 78)
    print("22. EXECUTABLE TESTS")
    print("=" * 78)

    tests = [
        test_grow_distribution,
        test_shrink_distribution,
        test_zero_grow,
        test_order,
    ]

    for test in tests:
        test()
        print(f"PASS: {test.__name__}")

    print(f"\n{len(tests)} tests passed.")


# ---------------------------------------------------------------------------
# 24. COMPLETE STUDY SESSION
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 78)
    print("ADVANCED FLEXBOX STUDY PROGRAM")
    print("=" * 78)
    print(
        "Topic: flex-grow, flex-shrink, flex-basis, ordering, "
        "nested layouts, and common patterns"
    )

    explain_fundamentals()
    demonstrate_flex_grow()
    demonstrate_flex_shrink()
    demonstrate_flex_basis()
    demonstrate_flex_shorthand()
    demonstrate_order()
    demonstrate_axes()
    demonstrate_nested_layouts()
    demonstrate_navbar_pattern()
    demonstrate_sidebar_pattern()
    demonstrate_cards()
    demonstrate_wrapping()
    demonstrate_constraints()
    demonstrate_edge_cases()
    demonstrate_common_mistakes()
    demonstrate_debugging()
    demonstrate_performance_considerations()
    demonstrate_responsive_design()
    compare_flex_values()
    demonstrate_dashboard()
    demonstrate_validation()
    run_tests()

    print("\n" + "=" * 78)
    print("END OF FLEXBOX STUDY PROGRAM")
    print("=" * 78)


if __name__ == "__main__":
    main()
