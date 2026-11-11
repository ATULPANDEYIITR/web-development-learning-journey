#!/usr/bin/env python3
"""
React Components: Functional Components, Props, Composition and Reusability.

A self-contained component-system simulator demonstrating:
- Functional component definitions
- Typed prop validation
- Default props and required props
- Component composition and nesting
- Reusable component registry
- Conditional rendering
- Component trees and recursive rendering
- Prop immutability
- Duplicate identifiers and circular composition detection
- JSON serialization and testing
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
logger = logging.getLogger("component_system")


class PropType(Enum):
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"
    ANY = "any"


class ComponentError(Exception):
    """Base component-system exception."""


class PropValidationError(ComponentError):
    """Raised when component properties are invalid."""


class ComponentNotFoundError(ComponentError):
    """Raised when a component does not exist."""


class CompositionError(ComponentError):
    """Raised when component composition is invalid."""


def matches_type(value: Any, expected: PropType) -> bool:
    if expected == PropType.ANY:
        return True
    if expected == PropType.STRING:
        return isinstance(value, str)
    if expected == PropType.NUMBER:
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == PropType.BOOLEAN:
        return isinstance(value, bool)
    if expected == PropType.OBJECT:
        return isinstance(value, dict)
    if expected == PropType.ARRAY:
        return isinstance(value, list)
    return False


@dataclass(frozen=True)
class PropDefinition:
    name: str
    prop_type: PropType
    required: bool = False
    default: Any = None
    has_default: bool = False

    def __post_init__(self):
        if not self.name.isidentifier():
            raise ValueError(f"Invalid property name: {self.name}")

        if self.has_default and not matches_type(
            self.default, self.prop_type
        ):
            raise ValueError(
                f"Default value for {self.name} has incorrect type"
            )

        if self.required and self.has_default:
            raise ValueError(
                f"{self.name} cannot be both required and defaulted"
            )


@dataclass
class ComponentNode:
    component_name: str
    props: dict[str, Any] = field(default_factory=dict)
    children: list["ComponentNode | str"] = field(default_factory=list)
    node_id: str | None = None


@dataclass
class ComponentDefinition:
    name: str
    description: str
    props: dict[str, PropDefinition]
    renderer: Callable[[dict[str, Any], list[Any]], Any]
    allow_children: bool = True


class ComponentRegistry:
    """Stores reusable component definitions."""

    def __init__(self):
        self._components: dict[str, ComponentDefinition] = {}

    def register(self, definition: ComponentDefinition):
        if definition.name in self._components:
            raise ComponentError(
                f"Component already registered: {definition.name}"
            )

        if not definition.name.isidentifier():
            raise ValueError("Component name must be a valid identifier")

        self._components[definition.name] = definition
        logger.info("Registered component: %s", definition.name)

    def get(self, name: str) -> ComponentDefinition:
        try:
            return self._components[name]
        except KeyError as exc:
            raise ComponentNotFoundError(name) from exc

    def names(self) -> list[str]:
        return sorted(self._components)


class ComponentRenderer:
    """Validates properties and renders component trees."""

    def __init__(self, registry: ComponentRegistry):
        self.registry = registry

    def validate_props(
        self,
        definition: ComponentDefinition,
        supplied: dict[str, Any]
    ) -> dict[str, Any]:

        validated = {}

        unknown = set(supplied) - set(definition.props)
        if unknown:
            raise PropValidationError(
                f"{definition.name}: unknown props {sorted(unknown)}"
            )

        for name, schema in definition.props.items():
            if name in supplied:
                value = supplied[name]
            elif schema.has_default:
                value = schema.default
            elif schema.required:
                raise PropValidationError(
                    f"{definition.name}: missing required prop '{name}'"
                )
            else:
                continue

            if not matches_type(value, schema.prop_type):
                raise PropValidationError(
                    f"{definition.name}.{name} expects "
                    f"{schema.prop_type.value}"
                )

            validated[name] = value

        return validated

    def render(
        self,
        node: ComponentNode,
        ancestors: tuple[int, ...] = ()
    ) -> Any:

        if id(node) in ancestors:
            raise CompositionError("Circular component composition detected")

        definition = self.registry.get(node.component_name)

        if not definition.allow_children and node.children:
            raise CompositionError(
                f"{node.component_name} does not accept children"
            )

        props = self.validate_props(definition, node.props)

        child_values = [
            self.render(child, ancestors + (id(node),))
            if isinstance(child, ComponentNode)
            else str(child)
            for child in node.children
        ]

        result = definition.renderer(props, child_values)

        return {
            "component": definition.name,
            "id": node.node_id,
            "props": props,
            "output": result,
            "children": child_values
        }


def text_renderer(props, children):
    return {
        "element": "text",
        "content": props["text"]
    }


def button_renderer(props, children):
    return {
        "element": "button",
        "label": props["label"],
        "variant": props["variant"],
        "disabled": props["disabled"],
        "children": children
    }


def card_renderer(props, children):
    return {
        "element": "card",
        "title": props["title"],
        "description": props["description"],
        "content": children
    }


def badge_renderer(props, children):
    return {
        "element": "badge",
        "label": props["label"],
        "color": props["color"]
    }


def conditional_renderer(props, children):
    return {
        "element": "conditional",
        "visible": props["condition"],
        "content": children if props["condition"] else []
    }


def create_registry() -> ComponentRegistry:
    registry = ComponentRegistry()

    registry.register(ComponentDefinition(
        name="Text",
        description="Reusable text component",
        props={
            "text": PropDefinition(
                "text", PropType.STRING, required=True
            )
        },
        renderer=text_renderer,
        allow_children=False
    ))

    registry.register(ComponentDefinition(
        name="Button",
        description="Reusable action button",
        props={
            "label": PropDefinition(
                "label", PropType.STRING, required=True
            ),
            "variant": PropDefinition(
                "variant", PropType.STRING,
                default="primary", has_default=True
            ),
            "disabled": PropDefinition(
                "disabled", PropType.BOOLEAN,
                default=False, has_default=True
            )
        },
        renderer=button_renderer
    ))

    registry.register(ComponentDefinition(
        name="Card",
        description="Composable content container",
        props={
            "title": PropDefinition(
                "title", PropType.STRING, required=True
            ),
            "description": PropDefinition(
                "description", PropType.STRING,
                default="", has_default=True
            )
        },
        renderer=card_renderer
    ))

    registry.register(ComponentDefinition(
        name="Badge",
        description="Status indicator",
        props={
            "label": PropDefinition(
                "label", PropType.STRING, required=True
            ),
            "color": PropDefinition(
                "color", PropType.STRING,
                default="blue", has_default=True
            )
        },
        renderer=badge_renderer,
        allow_children=False
    ))

    registry.register(ComponentDefinition(
        name="Conditional",
        description="Conditional component container",
        props={
            "condition": PropDefinition(
                "condition", PropType.BOOLEAN, required=True
            )
        },
        renderer=conditional_renderer
    ))

    return registry


def build_dashboard() -> ComponentNode:
    return ComponentNode(
        component_name="Card",
        node_id="dashboard-card",
        props={
            "title": "Project Dashboard",
            "description": "Reusable component composition example"
        },
        children=[
            ComponentNode(
                component_name="Text",
                props={"text": "Project status: operational"}
            ),
            ComponentNode(
                component_name="Badge",
                props={
                    "label": "Active",
                    "color": "green"
                }
            ),
            ComponentNode(
                component_name="Button",
                props={
                    "label": "View Projects",
                    "variant": "primary"
                }
            ),
            ComponentNode(
                component_name="Conditional",
                props={"condition": True},
                children=[
                    ComponentNode(
                        component_name="Text",
                        props={"text": "Additional details are available"}
                    )
                ]
            )
        ]
    )


def run_tests(renderer: ComponentRenderer):
    # Valid component rendering.
    button = ComponentNode(
        "Button",
        {"label": "Save"}
    )
    rendered = renderer.render(button)
    assert rendered["output"]["variant"] == "primary"
    assert rendered["output"]["disabled"] is False

    # Required property validation.
    try:
        renderer.render(ComponentNode("Button", {}))
        raise AssertionError("Missing required prop was accepted")
    except PropValidationError:
        pass

    # Invalid property type.
    try:
        renderer.render(ComponentNode(
            "Button",
            {"label": 100}
        ))
        raise AssertionError("Invalid prop type was accepted")
    except PropValidationError:
        pass

    # Unknown properties.
    try:
        renderer.render(ComponentNode(
            "Badge",
            {"label": "Ready", "unexpected": True}
        ))
        raise AssertionError("Unknown property was accepted")
    except PropValidationError:
        pass

    # Circular composition.
    circular = ComponentNode("Card", {"title": "Circular"})
    circular.children.append(circular)

    try:
        renderer.render(circular)
        raise AssertionError("Circular composition was accepted")
    except CompositionError:
        pass

    # Conditional rendering.
    hidden = renderer.render(ComponentNode(
        "Conditional",
        {"condition": False},
        children=["Hidden content"]
    ))
    assert hidden["output"]["content"] == []

    logger.info("All component tests passed")


def save_output(data: Any, filename: str = "component_output.json"):
    path = Path(filename)

    # Avoid writing outside the current working directory.
    if path.name != filename or path.is_absolute():
        raise ValueError("Invalid output filename")

    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    logger.info("Saved component output to %s", path)


def main():
    registry = create_registry()
    renderer = ComponentRenderer(registry)

    run_tests(renderer)

    dashboard = build_dashboard()
    result = renderer.render(dashboard)

    print("\nRegistered components:")
    for name in registry.names():
        print(f"- {name}")

    print("\nRendered component tree:")
    print(json.dumps(result, indent=2))

    save_output(result)


if __name__ == "__main__":
    main()
