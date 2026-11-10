from __future__ import annotations

import json
import logging
import unittest
from dataclasses import dataclass, field
from enum import Enum
from html import escape
from typing import Any, Callable


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
logger = logging.getLogger("react_introduction")


class ComponentError(Exception):
    """Raised when a component definition is invalid."""


class RenderError(Exception):
    """Raised when rendering fails."""


class NodeType(Enum):
    ELEMENT = "element"
    TEXT = "text"
    FRAGMENT = "fragment"


@dataclass(frozen=True)
class VNode:
    """Immutable virtual DOM node."""

    node_type: NodeType
    tag: str | None = None
    props: dict[str, Any] = field(default_factory=dict)
    children: tuple["VNode", ...] = ()
    text: str | None = None

    def __post_init__(self):
        object.__setattr__(self, "props", dict(self.props))
        object.__setattr__(self, "children", tuple(self.children))

        if self.node_type == NodeType.TEXT and self.text is None:
            raise ComponentError("Text nodes require text content.")

        if self.node_type == NodeType.ELEMENT:
            if not self.tag or not self.tag.replace("-", "").isalnum():
                raise ComponentError("Invalid element tag.")

        if self.node_type == NodeType.FRAGMENT and self.tag is not None:
            raise ComponentError("Fragments cannot have element tags.")


def text_node(value: Any) -> VNode:
    return VNode(
        node_type=NodeType.TEXT,
        text=str(value)
    )


def element(
    tag: str,
    props: dict[str, Any] | None = None,
    *children: VNode
) -> VNode:
    if not isinstance(tag, str):
        raise ComponentError("Tag must be a string.")

    return VNode(
        node_type=NodeType.ELEMENT,
        tag=tag,
        props=props or {},
        children=tuple(children)
    )


def fragment(*children: VNode) -> VNode:
    return VNode(
        node_type=NodeType.FRAGMENT,
        children=tuple(children)
    )


def normalize_child(child: Any) -> VNode:
    if isinstance(child, VNode):
        return child

    if child is None or isinstance(child, bool):
        return fragment()

    if isinstance(child, (str, int, float)):
        return text_node(child)

    if isinstance(child, (list, tuple)):
        return fragment(
            *(normalize_child(item) for item in child)
        )

    raise ComponentError(
        f"Unsupported child type: {type(child).__name__}"
    )


def component(function: Callable) -> Callable:
    """Mark a callable as a reusable component."""

    def wrapper(props: dict[str, Any] | None = None):
        result = function(props or {})

        if not isinstance(result, VNode):
            raise ComponentError(
                f"{function.__name__} must return a VNode."
            )

        return result

    wrapper.__name__ = function.__name__
    return wrapper


@dataclass
class ComponentRegistry:
    """Stores reusable component definitions."""

    components: dict[str, Callable] = field(default_factory=dict)

    def register(self, name: str, function: Callable) -> None:
        if not name or name in self.components:
            raise ComponentError(
                f"Invalid or duplicate component: {name}"
            )

        self.components[name] = function

    def render_component(
        self,
        name: str,
        props: dict[str, Any] | None = None
    ) -> VNode:
        if name not in self.components:
            raise ComponentError(
                f"Unknown component: {name}"
            )

        return self.components[name](props or {})


VOID_ELEMENTS = {
    "area", "base", "br", "col", "embed", "hr",
    "img", "input", "link", "meta", "param",
    "source", "track", "wbr"
}


def render_attributes(props: dict[str, Any]) -> str:
    attributes = []

    for name, value in sorted(props.items()):
        if name in {"children", "key", "ref"}:
            continue

        if name.startswith("on"):
            continue

        if value is None or value is False:
            continue

        attribute_name = {
            "className": "class",
            "htmlFor": "for"
        }.get(name, name)

        if not attribute_name.replace("-", "").replace("_", "").isalnum():
            raise RenderError("Invalid attribute name.")

        if value is True:
            attributes.append(
                f'{attribute_name}=""'
            )
            continue

        if isinstance(value, dict):
            if name == "style":
                style = ";".join(
                    f"{key.replace('_', '-')}:"
                    f"{val}"
                    for key, val in value.items()
                )
                value = style
            else:
                value = json.dumps(value)

        if isinstance(value, (list, tuple)):
            value = " ".join(map(str, value))

        attributes.append(
            f'{attribute_name}="{escape(str(value), quote=True)}"'
        )

    return (" " + " ".join(attributes)) if attributes else ""


def render_to_html(node: VNode) -> str:
    """Convert a virtual tree into escaped HTML."""

    if node.node_type == NodeType.TEXT:
        return escape(node.text or "")

    if node.node_type == NodeType.FRAGMENT:
        return "".join(
            render_to_html(child)
            for child in node.children
        )

    tag = node.tag
    attributes = render_attributes(node.props)

    if tag in VOID_ELEMENTS:
        if node.children:
            raise RenderError(
                f"Void element '{tag}' cannot have children."
            )
        return f"<{tag}{attributes}/>"

    children_html = "".join(
        render_to_html(child)
        for child in node.children
    )

    return (
        f"<{tag}{attributes}>"
        f"{children_html}"
        f"</{tag}>"
    )


@dataclass
class ComponentState:
    """Small state container illustrating state-driven rendering."""

    values: dict[str, Any] = field(default_factory=dict)
    version: int = 0

    def get(self, key: str, default: Any = None) -> Any:
        return self.values.get(key, default)

    def set(self, key: str, value: Any) -> bool:
        if self.values.get(key) == value:
            return False

        self.values[key] = value
        self.version += 1
        return True


@dataclass
class RenderResult:
    html: str
    component_count: int
    text_count: int


def inspect_tree(node: VNode) -> tuple[int, int]:
    components = 0
    texts = 0

    if node.node_type == NodeType.ELEMENT:
        components += 1

    if node.node_type == NodeType.TEXT:
        texts += 1

    for child in node.children:
        child_components, child_texts = inspect_tree(child)
        components += child_components
        texts += child_texts

    return components, texts


def render_application(root: VNode) -> RenderResult:
    html = render_to_html(root)
    components, texts = inspect_tree(root)

    return RenderResult(
        html=html,
        component_count=components,
        text_count=texts
    )


# ---------------------------------------------------------
# Reusable application components
# ---------------------------------------------------------

@component
def Header(props: dict[str, Any]) -> VNode:
    return element(
        "header",
        {"className": "site-header"},
        element(
            "h1",
            {},
            text_node(props.get("title", "React Introduction"))
        ),
        element(
            "p",
            {},
            text_node(props.get("subtitle", "Component-based UI"))
        )
    )


@component
def Card(props: dict[str, Any]) -> VNode:
    return element(
        "article",
        {"className": "card"},
        element("h2", {}, text_node(props["title"])),
        element("p", {}, text_node(props["description"]))
    )


@component
def Counter(props: dict[str, Any]) -> VNode:
    count = props["count"]

    return element(
        "section",
        {"className": "counter"},
        element("h2", {}, text_node("Interactive Counter")),
        element(
            "p",
            {"aria-live": "polite"},
            text_node(f"Current count: {count}")
        ),
        element(
            "button",
            {"type": "button", "disabled": True},
            text_node("State changes are simulated in Python")
        )
    )


def build_application(state: ComponentState) -> VNode:
    registry = ComponentRegistry()

    registry.register("Header", Header)
    registry.register("Card", Card)
    registry.register("Counter", Counter)

    cards = [
        {
            "title": "Component Architecture",
            "description": "Build interfaces from independent reusable components."
        },
        {
            "title": "JSX",
            "description": "Describe interface structures using JavaScript XML syntax."
        },
        {
            "title": "Virtual DOM",
            "description": "Represent UI structures as lightweight in-memory objects."
        },
        {
            "title": "Rendering",
            "description": "Convert component output into browser-visible elements."
        }
    ]

    card_nodes = [
        registry.render_component("Card", card)
        for card in cards
    ]

    return element(
        "main",
        {"className": "application"},
        registry.render_component(
            "Header",
            {
                "title": "React Introduction",
                "subtitle": "Components, JSX, Virtual DOM and Rendering"
            }
        ),
        element(
            "section",
            {"className": "card-grid"},
            *card_nodes
        ),
        registry.render_component(
            "Counter",
            {"count": state.get("count", 0)}
        )
    )


# ---------------------------------------------------------
# Virtual DOM comparison
# ---------------------------------------------------------

def compare_nodes(old: VNode, new: VNode, path: str = "root") -> list[str]:
    """Report conceptual changes between two virtual DOM trees."""

    changes = []

    if old.node_type != new.node_type:
        return [f"REPLACE {path}: node type changed"]

    if old.node_type == NodeType.TEXT:
        if old.text != new.text:
            changes.append(f"UPDATE_TEXT {path}")
        return changes

    if old.tag != new.tag:
        return [f"REPLACE {path}: element type changed"]

    if old.props != new.props:
        changes.append(f"UPDATE_PROPS {path}")

    maximum = max(len(old.children), len(new.children))

    for index in range(maximum):
        child_path = f"{path}.{index}"

        if index >= len(old.children):
            changes.append(f"INSERT {child_path}")
        elif index >= len(new.children):
            changes.append(f"REMOVE {child_path}")
        else:
            changes.extend(
                compare_nodes(
                    old.children[index],
                    new.children[index],
                    child_path
                )
            )

    return changes


# ---------------------------------------------------------
# Application tests
# ---------------------------------------------------------

class ReactIntroductionTests(unittest.TestCase):

    def test_text_escaping(self):
        node = text_node("<script>alert(1)</script>")
        result = render_to_html(node)
        self.assertNotIn("<script>", result)
        self.assertIn("&lt;script&gt;", result)

    def test_component_rendering(self):
        node = Header({"title": "Test"})
        result = render_to_html(node)
        self.assertIn("<h1>Test</h1>", result)

    def test_state_management(self):
        state = ComponentState({"count": 0})
        self.assertTrue(state.set("count", 1))
        self.assertFalse(state.set("count", 1))
        self.assertEqual(state.version, 1)

    def test_virtual_dom_comparison(self):
        old = element("p", {}, text_node("Old"))
        new = element("p", {}, text_node("New"))

        changes = compare_nodes(old, new)

        self.assertTrue(
            any("UPDATE_TEXT" in change for change in changes)
        )

    def test_void_element_validation(self):
        node = element("img", {}, text_node("Invalid"))

        with self.assertRaises(RenderError):
            render_to_html(node)

    def test_invalid_component_result(self):
        registry = ComponentRegistry()
        registry.register("Broken", lambda props: "invalid")

        with self.assertRaises(ComponentError):
            registry.render_component("Broken")

    def test_attribute_escaping(self):
        node = element(
            "div",
            {"title": '"unsafe"'},
            text_node("Safe")
        )
        self.assertIn("&quot;unsafe&quot;", render_to_html(node))


def main():
    state = ComponentState({"count": 0})

    root = build_application(state)
    result = render_application(root)

    print("=" * 65)
    print("REACT INTRODUCTION: COMPONENT RENDERING SIMULATION")
    print("=" * 65)

    print("\nRendered HTML:\n")
    print(result.html)

    print("\nVirtual DOM statistics:")
    print(f"Element nodes: {result.component_count}")
    print(f"Text nodes: {result.text_count}")

    updated_state = ComponentState({"count": 0})
    old_tree = build_application(updated_state)

    updated_state.set("count", 1)
    new_tree = build_application(updated_state)

    print("\nVirtual DOM comparison:")
    changes = compare_nodes(old_tree, new_tree)

    for change in changes:
        print(change)

    print("\nRunning tests:")
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        ReactIntroductionTests
    )
    test_result = unittest.TextTestRunner(verbosity=2).run(suite)

    if not test_result.wasSuccessful():
        raise SystemExit(1)

    print("\nAll tests passed.")


if __name__ == "__main__":
    main()
