"""
CSS Positioning — Static, Relative, Absolute, Fixed, Sticky, z-index,
Stacking Contexts

This standalone Python study program teaches CSS positioning from beginner
to advanced level. CSS itself runs in a browser, so Python is used here as
an educational simulator and analyzer. The program models the conceptual
rules behind containing blocks, offsets, normal flow, stacking order, and
stacking contexts.

Run:
    python css_positioning.py
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


# ============================================================================
# 1. FUNDAMENTALS
# ============================================================================

print("=" * 78)
print("CSS POSITIONING: STATIC, RELATIVE, ABSOLUTE, FIXED, STICKY, z-index")
print("=" * 78)


class Position(Enum):
    STATIC = "static"
    RELATIVE = "relative"
    ABSOLUTE = "absolute"
    FIXED = "fixed"
    STICKY = "sticky"


class Axis(Enum):
    X = "x"
    Y = "y"


@dataclass
class Rectangle:
    """
    A simplified rectangle.

    In a real browser, dimensions are affected by CSS layout, box sizing,
    intrinsic content, flex/grid algorithms, transforms, writing modes, and
    many other mechanisms. This class deliberately models only the geometry
    needed for positioning demonstrations.
    """

    x: float
    y: float
    width: float
    height: float

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def bottom(self) -> float:
        return self.y + self.height

    def contains(self, x: float, y: float) -> bool:
        return self.x <= x <= self.right and self.y <= y <= self.bottom

    def __str__(self) -> str:
        return (
            f"x={self.x:.1f}, y={self.y:.1f}, "
            f"width={self.width:.1f}, height={self.height:.1f}"
        )


@dataclass
class Element:
    name: str
    position: Position = Position.STATIC
    z_index: Optional[int] = None
    top: Optional[float] = None
    right: Optional[float] = None
    bottom: Optional[float] = None
    left: Optional[float] = None
    width: float = 100
    height: float = 40
    normal_x: float = 0
    normal_y: float = 0
    parent: Optional["Element"] = None
    establishes_stacking_context: bool = False
    children: List["Element"] = field(default_factory=list)

    def add_child(self, child: "Element") -> None:
        child.parent = self
        self.children.append(child)

    def effective_z_index(self) -> int:
        """
        CSS treats auto differently from explicit integer z-index.

        For a simplified educational model, auto is represented as 0 when
        comparing siblings within a basic stacking-context demonstration.
        """
        return 0 if self.z_index is None else self.z_index


# ============================================================================
# 2. STATIC POSITIONING
# ============================================================================

print("\n1. STATIC POSITIONING")
print("-" * 78)

static_box = Element(
    name="static-box",
    position=Position.STATIC,
    top=30,
    left=50,
    normal_x=20,
    normal_y=40,
)

print("position: static is the default positioning mode.")
print("Its position is determined by normal document flow.")
print(f"Normal-flow location: ({static_box.normal_x}, {static_box.normal_y})")
print(f"Requested top: {static_box.top}")
print(f"Requested left: {static_box.left}")
print("For a static element, top/right/bottom/left do not reposition it.")


# ============================================================================
# 3. RELATIVE POSITIONING
# ============================================================================

print("\n2. RELATIVE POSITIONING")
print("-" * 78)

relative_box = Element(
    name="relative-box",
    position=Position.RELATIVE,
    top=20,
    left=35,
    normal_x=100,
    normal_y=80,
)

relative_x = relative_box.normal_x + (relative_box.left or 0) - (
    relative_box.right or 0
)
relative_y = relative_box.normal_y + (relative_box.top or 0) - (
    relative_box.bottom or 0
)

print("A relatively positioned element remains in normal flow.")
print("Its original space is preserved.")
print(f"Normal location: ({relative_box.normal_x}, {relative_box.normal_y})")
print(f"Offset location: ({relative_x}, {relative_y})")
print("Important: relative positioning changes visual placement,")
print("but following normal-flow content behaves as if the original space remains.")


# ============================================================================
# 4. CORRECT OFFSET RESOLUTION
# ============================================================================

def resolve_relative_position(element: Element) -> Tuple[float, float]:
    """
    Resolve the simplified physical offsets for a relatively positioned
    element.

    CSS has a more specific rule when opposing offsets are both supplied:
    left/right and top/bottom can interact depending on writing direction.
    For this study model, we use left when available and top when available,
    then use right/bottom as fallbacks.
    """
    x = element.normal_x
    y = element.normal_y

    if element.left is not None:
        x += element.left
    elif element.right is not None:
        x -= element.right

    if element.top is not None:
        y += element.top
    elif element.bottom is not None:
        y -= element.bottom

    return x, y


print("\nRelative-position calculation:")
print(resolve_relative_position(relative_box))


# ============================================================================
# 5. ABSOLUTE POSITIONING
# ============================================================================

print("\n3. ABSOLUTE POSITIONING")
print("-" * 78)

container = Element(
    name="card",
    position=Position.RELATIVE,
    width=500,
    height=300,
    normal_x=100,
    normal_y=100,
)

badge = Element(
    name="badge",
    position=Position.ABSOLUTE,
    top=15,
    right=20,
    width=70,
    height=30,
)

container.add_child(badge)

absolute_x = container.normal_x + container.width - badge.width - badge.right
absolute_y = container.normal_y + badge.top

print("An absolutely positioned element is removed from normal flow.")
print("Its containing block is usually established by a suitable ancestor.")
print(f"Container: {container.name}")
print(f"Badge position: x={absolute_x}, y={absolute_y}")
print("The badge does not reserve normal-flow space.")


# ============================================================================
# 6. CONTAINING BLOCKS
# ============================================================================

print("\n4. CONTAINING BLOCKS")
print("-" * 78)


def find_absolute_containing_block(element: Element) -> Optional[Element]:
    """
    Simplified containing-block lookup.

    A positioned ancestor is one of the most common ways to establish the
    containing block for an absolutely positioned descendant. Real CSS also
    has containing-block rules involving transforms, filters, containment,
    will-change, and other properties.
    """
    ancestor = element.parent

    while ancestor is not None:
        if ancestor.position != Position.STATIC:
            return ancestor

        if ancestor.establishes_stacking_context:
            return ancestor

        ancestor = ancestor.parent

    return None


deep_container = Element(
    name="positioned-parent",
    position=Position.RELATIVE,
    width=600,
    height=400,
)

middle = Element(
    name="ordinary-child",
    position=Position.STATIC,
)

deep_badge = Element(
    name="absolute-child",
    position=Position.ABSOLUTE,
    top=10,
    left=10,
)

deep_container.add_child(middle)
middle.add_child(deep_badge)

containing_block = find_absolute_containing_block(deep_badge)

print(
    "Absolute child containing block:",
    containing_block.name if containing_block else "viewport/initial containing block",
)


# ============================================================================
# 7. ABSOLUTE INSET COMBINATIONS
# ============================================================================

print("\n5. ABSOLUTE INSET COMBINATIONS")
print("-" * 78)


def describe_insets(element: Element) -> str:
    """
    Explain common absolute-positioning inset combinations.

    This is descriptive rather than a full browser layout engine.
    """
    supplied = {
        "top": element.top,
        "right": element.right,
        "bottom": element.bottom,
        "left": element.left,
    }

    active = [name for name, value in supplied.items() if value is not None]

    if not active:
        return "No insets supplied: the browser uses the static-position rules."

    if {"top", "left", "right", "bottom"}.issubset(active):
        return (
            "All four physical insets are supplied. If width/height are auto, "
            "the available space can determine the used size."
        )

    if {"left", "right"}.issubset(active):
        return "Both horizontal insets are supplied; width can be constrained."

    if {"top", "bottom"}.issubset(active):
        return "Both vertical insets are supplied; height can be constrained."

    return f"Explicit insets: {', '.join(active)}"


for example in [
    Element("top-left", Position.ABSOLUTE, top=0, left=0),
    Element("top-right", Position.ABSOLUTE, top=0, right=0),
    Element("centered-area", Position.ABSOLUTE, top=0, right=0, bottom=0, left=0),
    Element("bottom", Position.ABSOLUTE, bottom=20, left=20),
]:
    print(f"{example.name}: {describe_insets(example)}")


# ============================================================================
# 8. CENTERING WITH ABSOLUTE POSITIONING
# ============================================================================

print("\n6. ABSOLUTE CENTERING")
print("-" * 78)


def center_absolute(
    parent_width: float,
    parent_height: float,
    child_width: float,
    child_height: float,
) -> Tuple[float, float]:
    """
    Model the classic top/left 50% + transform(-50%, -50%) technique.

    The transform is not itself an inset. It visually moves the element by
    half of its own dimensions after the 50% positioning point is calculated.
    """
    x = parent_width * 0.5 - child_width * 0.5
    y = parent_height * 0.5 - child_height * 0.5
    return x, y


print(
    "Centered child:",
    center_absolute(parent_width=800, parent_height=500,
                    child_width=200, child_height=100),
)


# ============================================================================
# 9. FIXED POSITIONING
# ============================================================================

print("\n7. FIXED POSITIONING")
print("-" * 78)


@dataclass
class Viewport:
    width: float
    height: float
    scroll_x: float = 0
    scroll_y: float = 0


def resolve_fixed_position(element: Element, viewport: Viewport) -> Tuple[float, float]:
    """
    Simplified fixed-position calculation.

    Normally, a fixed element is positioned relative to the viewport and
    remains visually fixed while the document scrolls. Certain CSS features,
    notably transforms on ancestors in relevant circumstances, can alter
    the containing-block behavior.
    """
    if element.left is not None:
        x = element.left
    elif element.right is not None:
        x = viewport.width - element.width - element.right
    else:
        x = element.normal_x

    if element.top is not None:
        y = element.top
    elif element.bottom is not None:
        y = viewport.height - element.height - element.bottom
    else:
        y = element.normal_y

    return x, y


viewport = Viewport(width=1440, height=900, scroll_y=1800)

fixed_button = Element(
    name="support-button",
    position=Position.FIXED,
    right=24,
    bottom=24,
    width=160,
    height=50,
)

before_scroll = resolve_fixed_position(fixed_button, Viewport(1440, 900, 0, 0))
after_scroll = resolve_fixed_position(fixed_button, viewport)

print("Position before scrolling:", before_scroll)
print("Position after scrolling: ", after_scroll)
print("The viewport-relative coordinates remain unchanged in this model.")


# ============================================================================
# 10. STICKY POSITIONING
# ============================================================================

print("\n8. STICKY POSITIONING")
print("-" * 78)


def sticky_y_position(
    normal_y: float,
    top: Optional[float],
    scroll_y: float,
    containing_start: float,
    containing_end: float,
    element_height: float,
) -> float:
    """
    Simplified vertical sticky-position calculation.

    Sticky behaves like a relatively positioned element until a threshold is
    crossed. It can then remain offset from the scrollport until its containing
    block's boundary prevents it from moving farther.
    """
    if top is None:
        return normal_y

    natural_viewport_y = normal_y - scroll_y
    constrained = max(natural_viewport_y, top)

    maximum_viewport_y = containing_end - scroll_y - element_height
    return min(constrained, maximum_viewport_y)


sticky_header = Element(
    name="section-header",
    position=Position.STICKY,
    top=0,
    width=600,
    height=50,
    normal_y=400,
)

for scroll in [0, 200, 399, 400, 600, 1000]:
    y = sticky_y_position(
        normal_y=sticky_header.normal_y,
        top=sticky_header.top,
        scroll_y=scroll,
        containing_start=0,
        containing_end=1500,
        element_height=sticky_header.height,
    )
    print(f"scrollY={scroll:4}: sticky viewport y={y:6.1f}")


# ============================================================================
# 11. WHY STICKY SOMETIMES DOES NOT WORK
# ============================================================================

print("\n9. COMMON STICKY FAILURE CONDITIONS")
print("-" * 78)

sticky_failure_conditions = [
    "No inset such as top: 0 is supplied on the relevant axis.",
    "The scrollable/container geometry does not provide enough room.",
    "An ancestor's overflow/scrolling behavior changes which scroll container matters.",
    "The sticky element is constrained by the boundaries of its containing block.",
    "A flex/grid layout can change available space and stretching behavior.",
    "The element may appear not to stick because its threshold is never reached.",
]

for condition in sticky_failure_conditions:
    print("•", condition)


# ============================================================================
# 12. z-index
# ============================================================================

print("\n10. z-INDEX")
print("-" * 78)


def stacking_sort_key(element: Element) -> Tuple[int, int]:
    """
    Simplified sibling stacking order.

    This function is intentionally not a full CSS painting algorithm.
    It demonstrates the common case where positioned elements within one
    stacking context are compared by their z-index.
    """
    positioned = element.position != Position.STATIC
    return (
        element.effective_z_index(),
        1 if positioned else 0,
    )


siblings = [
    Element("background", Position.STATIC, z_index=None),
    Element("menu", Position.RELATIVE, z_index=10),
    Element("modal", Position.ABSOLUTE, z_index=100),
    Element("tooltip", Position.FIXED, z_index=1000),
]

print("Approximate sibling order from back to front:")
for element in sorted(siblings, key=stacking_sort_key):
    print(
        f"{element.name:12} "
        f"position={element.position.value:9} "
        f"z-index={element.z_index}"
    )


# ============================================================================
# 13. z-index DOES NOT MEAN GLOBAL PRIORITY
# ============================================================================

print("\n11. z-INDEX IS NOT A GLOBAL NUMBER")
print("-" * 78)

root = Element(
    "root",
    position=Position.STATIC,
    establishes_stacking_context=True,
)

context_a = Element(
    "context-A",
    position=Position.RELATIVE,
    z_index=1,
    establishes_stacking_context=True,
)

context_b = Element(
    "context-B",
    position=Position.RELATIVE,
    z_index=2,
    establishes_stacking_context=True,
)

child_a = Element(
    "child-A",
    position=Position.ABSOLUTE,
    z_index=99999,
)

child_b = Element(
    "child-B",
    position=Position.ABSOLUTE,
    z_index=1,
)

root.add_child(context_a)
root.add_child(context_b)
context_a.add_child(child_a)
context_b.add_child(child_b)

print("context-A z-index:", context_a.z_index)
print("child-A z-index:  ", child_a.z_index)
print("context-B z-index:", context_b.z_index)
print("child-B z-index:  ", child_b.z_index)
print(
    "Even a very large child-A z-index cannot escape its parent's stacking "
    "context and automatically paint above a sibling stacking context."
)


# ============================================================================
# 14. STACKING CONTEXT TRIGGERS
# ============================================================================

print("\n12. COMMON STACKING-CONTEXT TRIGGERS")
print("-" * 78)

stacking_context_triggers = {
    "root element": "The root element forms the root stacking context.",
    "positioned + non-auto z-index": "A positioned element with an explicit z-index can establish one.",
    "position: fixed": "Fixed-positioned elements participate in stacking-context behavior.",
    "position: sticky": "Sticky-positioned elements establish stacking-context behavior.",
    "opacity < 1": "Transparency creates an isolated painting relationship.",
    "transform": "A non-none transform establishes a new stacking context.",
    "filter": "A non-none filter can establish one.",
    "isolation: isolate": "Explicitly requests a new stacking context.",
    "mix-blend-mode": "Non-normal blending participates in stacking isolation.",
    "containment": "Certain containment values establish stacking contexts.",
    "will-change": "Certain declared future changes can establish one.",
}

for trigger, explanation in stacking_context_triggers.items():
    print(f"{trigger:28} -> {explanation}")


# ============================================================================
# 15. STACKING CONTEXT TREE
# ============================================================================

print("\n13. STACKING-CONTEXT TREE")
print("-" * 78)


def print_tree(
    element: Element,
    depth: int = 0,
) -> None:
    marker = "[SC]" if element.establishes_stacking_context else ""
    print(
        "  " * depth
        + f"{element.name} "
        + f"position={element.position.value} "
        + f"z={element.z_index} {marker}"
    )

    for child in element.children:
        print_tree(child, depth + 1)


print_tree(root)


# ============================================================================
# 16. NORMAL FLOW VS POSITIONED ELEMENTS
# ============================================================================

print("\n14. NORMAL FLOW VS POSITIONED ELEMENTS")
print("-" * 78)

flow_examples = [
    ("static", "Participates in normal flow."),
    ("relative", "Participates in normal flow but can be visually offset."),
    ("absolute", "Removed from normal flow."),
    ("fixed", "Removed from normal flow and generally positioned against the viewport."),
    ("sticky", "Participates in flow while behaving relatively, then sticks within constraints."),
]

for name, behavior in flow_examples:
    print(f"{name:9}: {behavior}")


# ============================================================================
# 17. STATIC POSITIONING AND MARGIN COLLAPSING
# ============================================================================

print("\n15. POSITIONING AND MARGIN COLLAPSING")
print("-" * 78)

print(
    "Positioning interacts with layout, but positioning and margin collapsing "
    "are separate concepts."
)
print(
    "A common mistake is assuming position: relative is required to stop every "
    "kind of margin behavior. It is not a universal layout fix."
)


# ============================================================================
# 18. PARENT RELATIVE + CHILD ABSOLUTE PATTERN
# ============================================================================

print("\n16. PRACTICAL CARD OVERLAY")
print("-" * 78)


@dataclass
class Card:
    x: float
    y: float
    width: float
    height: float

    def badge_position(
        self,
        badge_width: float,
        badge_height: float,
        top: float,
        right: float,
    ) -> Tuple[float, float]:
        """
        Equivalent conceptual model:

        .card {
            position: relative;
        }

        .badge {
            position: absolute;
            top: ...;
            right: ...;
        }
        """
        return (
            self.x + self.width - badge_width - right,
            self.y + top,
        )


product_card = Card(100, 200, 320, 220)
print(
    "Badge coordinates:",
    product_card.badge_position(60, 28, 12, 12),
)


# ============================================================================
# 19. EDGE CASES
# ============================================================================

print("\n17. EDGE CASES")
print("-" * 78)

edge_cases = [
    "position: static with top/left: offsets do not reposition the element.",
    "position: relative with no offsets: visual position normally remains unchanged.",
    "absolute element with no positioned ancestor: its containing block may be the initial containing block.",
    "fixed element: ancestor transforms and related containing-block rules can change expected behavior.",
    "sticky with no top/bottom/left/right threshold: it has no sticking threshold on that axis.",
    "negative z-index: can place content behind other content inside the relevant stacking context, subject to the painting rules.",
    "z-index: 999999 is not a universal guarantee of being on top.",
    "overflow can clip descendants, so high z-index cannot necessarily escape clipping.",
    "transforms can create stacking contexts and containing blocks, producing surprising layering or fixed-position behavior.",
]

for case in edge_cases:
    print("•", case)


# ============================================================================
# 20. COMMON MISTAKES
# ============================================================================

print("\n18. COMMON MISTAKES")
print("-" * 78)

mistakes = {
    "Absolute child is positioned relative to viewport":
        "Check whether the intended ancestor establishes the containing block.",
    "z-index appears ignored":
        "Check stacking contexts, positioned status, painting order, and clipping.",
    "Sticky does not stick":
        "Check the inset, scroll container, available space, and ancestor layout.",
    "Fixed element scrolls":
        "Inspect ancestors for properties that affect its containing block, especially transforms.",
    "Elements overlap unexpectedly":
        "Inspect both layout geometry and stacking order. z-index does not repair incorrect geometry.",
    "Using absolute positioning for complete page layout":
        "Prefer normal flow, flexbox, or grid for primary layout; reserve absolute positioning for overlays and anchored elements.",
    "Using huge z-index values everywhere":
        "Use a deliberate layer scale and understand the stacking contexts that contain each layer.",
}

for mistake, solution in mistakes.items():
    print(f"\nProblem: {mistake}\nReason/approach: {solution}")


# ============================================================================
# 21. PERFORMANCE AND DESIGN CONSIDERATIONS
# ============================================================================

print("\n19. PERFORMANCE AND DESIGN CONSIDERATIONS")
print("-" * 78)

performance_points = [
    "Do not assume position:absolute is automatically faster or slower than normal layout.",
    "Large numbers of frequently moving elements can increase rendering work.",
    "Transforms are often useful for animation because browsers can optimize them differently from layout-changing properties.",
    "Avoid unnecessary stacking contexts when building very complex interfaces.",
    "Keep z-index values understandable instead of using arbitrary enormous numbers.",
    "Use semantic layout systems such as flexbox/grid for structural layout.",
    "Use absolute/fixed/sticky positioning for behavior that actually requires those relationships.",
]

for point in performance_points:
    print("•", point)


# ============================================================================
# 22. SECURITY CONSIDERATIONS
# ============================================================================

print("\n20. SECURITY CONSIDERATIONS")
print("-" * 78)

print(
    "CSS positioning itself is primarily a presentation mechanism and is not "
    "an access-control system."
)
print(
    "Hiding an element behind another element, moving it off-screen, or using "
    "opacity does not make sensitive information secure."
)
print(
    "Security-sensitive information should be protected at the application "
    "and server layers rather than relying on CSS visibility or positioning."
)


# ============================================================================
# 23. RESPONSIVE DESIGN
# ============================================================================

print("\n21. RESPONSIVE DESIGN")
print("-" * 78)


@dataclass
class ResponsiveRule:
    viewport_width: int
    desktop_breakpoint: int = 768

    def layout_strategy(self) -> str:
        if self.viewport_width >= self.desktop_breakpoint:
            return "Use normal layout with positioning only for required overlays."
        return "Reduce fixed offsets and prefer flow/flex/grid for narrow screens."


for width in [360, 768, 1024, 1440]:
    rule = ResponsiveRule(width)
    print(width, "px ->", rule.layout_strategy())


# ============================================================================
# 24. LAYER SYSTEM
# ============================================================================

print("\n22. PRACTICAL LAYER SYSTEM")
print("-" * 78)

layer_scale: Dict[str, int] = {
    "base-content": 0,
    "dropdown": 100,
    "sticky-navigation": 200,
    "overlay": 500,
    "modal": 1000,
    "toast": 1100,
}

for layer, value in layer_scale.items():
    print(f"{layer:22} z-index={value}")


# ============================================================================
# 25. POSITIONING DECISION FUNCTION
# ============================================================================

print("\n23. POSITIONING DECISION GUIDE")
print("-" * 78)


def choose_positioning(
    needs_normal_flow: bool,
    needs_local_offset: bool,
    anchored_to_parent: bool,
    anchored_to_viewport: bool,
    should_stick_during_scroll: bool,
) -> str:
    """
    Convert a design requirement into a likely positioning mode.

    This is a teaching aid, not a replacement for actual CSS layout analysis.
    """
    if should_stick_during_scroll:
        return "sticky"

    if anchored_to_viewport:
        return "fixed"

    if anchored_to_parent:
        return "absolute"

    if needs_local_offset:
        return "relative"

    if needs_normal_flow:
        return "static"

    return "static"


scenarios = [
    {
        "name": "article heading",
        "needs_normal_flow": True,
        "needs_local_offset": False,
        "anchored_to_parent": False,
        "anchored_to_viewport": False,
        "should_stick_during_scroll": False,
    },
    {
        "name": "notification badge",
        "needs_normal_flow": False,
        "needs_local_offset": False,
        "anchored_to_parent": True,
        "anchored_to_viewport": False,
        "should_stick_during_scroll": False,
    },
    {
        "name": "cookie control",
        "needs_normal_flow": False,
        "needs_local_offset": False,
        "anchored_to_parent": False,
        "anchored_to_viewport": True,
        "should_stick_during_scroll": False,
    },
    {
        "name": "section navigation",
        "needs_normal_flow": True,
        "needs_local_offset": False,
        "anchored_to_parent": False,
        "anchored_to_viewport": False,
        "should_stick_during_scroll": True,
    },
    {
        "name": "slightly shifted icon",
        "needs_normal_flow": True,
        "needs_local_offset": True,
        "anchored_to_parent": False,
        "anchored_to_viewport": False,
        "should_stick_during_scroll": False,
    },
]

for scenario in scenarios:
    selected = choose_positioning(
        scenario["needs_normal_flow"],
        scenario["needs_local_offset"],
        scenario["anchored_to_parent"],
        scenario["anchored_to_viewport"],
        scenario["should_stick_during_scroll"],
    )
    print(f"{scenario['name']:24} -> position: {selected}")


# ============================================================================
# 26. SIMPLE CSS GENERATOR
# ============================================================================

print("\n24. GENERATING REAL CSS")
print("-" * 78)


def css_rule(
    selector: str,
    properties: Dict[str, str],
) -> str:
    lines = [f"{selector} {{"]
    for property, value in properties.items():
        lines.append(f"  {property}: {value};")
    lines.append("}")
    return "\n".join(lines)


print(
    css_rule(
        ".card",
        {
            "position": "relative",
            "width": "320px",
            "height": "220px",
        },
    )
)

print(
    css_rule(
        ".card__badge",
        {
            "position": "absolute",
            "top": "12px",
            "right": "12px",
            "z-index": "10",
        },
    )
)


# ============================================================================
# 27. MINI STYLE ANALYZER
# ============================================================================

print("\n25. MINI POSITIONING ANALYZER")
print("-" * 78)


def analyze_element(element: Element) -> List[str]:
    findings: List[str] = []

    if element.position == Position.STATIC:
        findings.append(
            "Static: normal-flow layout; physical inset properties do not reposition it."
        )

    if element.position == Position.RELATIVE:
        findings.append(
            "Relative: remains in flow; offsets visually shift it from its normal position."
        )

    if element.position == Position.ABSOLUTE:
        findings.append(
            "Absolute: removed from normal flow; inspect the containing block."
        )

    if element.position == Position.FIXED:
        findings.append(
            "Fixed: generally tied to the viewport/scrollport and removed from flow."
        )

    if element.position == Position.STICKY:
        findings.append(
            "Sticky: participates in layout and becomes constrained/stuck during scrolling."
        )

    if element.z_index is not None:
        findings.append(f"Explicit z-index: {element.z_index}.")

    if element.establishes_stacking_context:
        findings.append("This element is marked as a stacking-context boundary.")

    if element.position == Position.ABSOLUTE and element.parent is None:
        findings.append(
            "No parent is modeled; containing-block resolution requires inspection."
        )

    return findings


for item in [static_box, relative_box, badge, fixed_button, sticky_header]:
    print(f"\n{item.name}:")
    for finding in analyze_element(item):
        print("  -", finding)


# ============================================================================
# 28. TESTS
# ============================================================================

print("\n26. SELF-TESTS")
print("-" * 78)


def run_tests() -> None:
    assert Position.STATIC.value == "static"
    assert Position.RELATIVE.value == "relative"
    assert Position.ABSOLUTE.value == "absolute"
    assert Position.FIXED.value == "fixed"
    assert Position.STICKY.value == "sticky"

    test_relative = Element(
        "test",
        Position.RELATIVE,
        top=10,
        left=15,
        normal_x=100,
        normal_y=200,
    )
    assert resolve_relative_position(test_relative) == (115, 210)

    test_parent = Element(
        "parent",
        Position.RELATIVE,
    )
    test_child = Element(
        "child",
        Position.ABSOLUTE,
    )
    test_parent.add_child(test_child)
    assert find_absolute_containing_block(test_child) is test_parent

    fixed = Element(
        "fixed",
        Position.FIXED,
        right=10,
        bottom=20,
        width=100,
        height=50,
    )
    assert resolve_fixed_position(fixed, Viewport(800, 600)) == (690, 530)

    sticky_y = sticky_y_position(
        normal_y=500,
        top=0,
        scroll_y=500,
        containing_start=0,
        containing_end=1500,
        element_height=50,
    )
    assert sticky_y == 0

    print("All tests passed.")


run_tests()


# ============================================================================
# 29. FINAL REFERENCE TABLE
# ============================================================================

print("\n27. FINAL REFERENCE")
print("-" * 78)

reference = [
    ("static", "Normal flow", "No", "Not normally used for inset offsets"),
    ("relative", "Normal flow", "No", "Offset from normal position"),
    ("absolute", "Removed", "Yes", "Containing block"),
    ("fixed", "Removed", "Yes", "Usually viewport/scrollport"),
    ("sticky", "Flow + constrained", "Yes", "Scroll container / containing block"),
]

print(
    f"{'position':12} {'flow':24} {'offsets':12} {'reference':35}"
)
print("-" * 78)

for row in reference:
    print(f"{row[0]:12} {row[1]:24} {row[2]:12} {row[3]:35}")

print("\nStudy complete.")
