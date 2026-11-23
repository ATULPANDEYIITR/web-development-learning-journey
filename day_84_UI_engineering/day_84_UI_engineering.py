#!/usr/bin/env python3
"""
UI Engineering: Design Systems, Component Libraries, Design Tokens,
Accessibility, and Reusable UI Architecture.

Python implementation of a design-system governance and validation engine.
Uses only the Python standard library.
"""

from __future__ import annotations

import json
import re
import sys
import unittest
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class TokenType(str, Enum):
    COLOR = "color"
    SPACING = "spacing"
    TYPOGRAPHY = "typography"
    RADIUS = "radius"
    ELEVATION = "elevation"
    MOTION = "motion"


class ComponentStatus(str, Enum):
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    DEPRECATED = "deprecated"


class AccessibilityLevel(str, Enum):
    A = "A"
    AA = "AA"
    AAA = "AAA"


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True)
class DesignToken:
    name: str
    category: TokenType
    value: str
    description: str = ""
    alias: Optional[str] = None

    def validate(self) -> list[str]:
        errors = []

        if not re.fullmatch(r"[a-z][a-z0-9-]*(?:\.[a-z][a-z0-9-]*)*", self.name):
            errors.append(f"Invalid token name: {self.name}")

        if not self.value.strip():
            errors.append(f"Token {self.name} has an empty value")

        if self.category == TokenType.COLOR:
            if self.value.startswith("#"):
                if not re.fullmatch(r"#[0-9a-fA-F]{6}", self.value):
                    errors.append(f"Invalid hexadecimal color: {self.value}")
            elif not self.alias:
                errors.append(f"Color token {self.name} requires a valid color or alias")

        if self.category == TokenType.SPACING:
            if not re.fullmatch(r"\d+(?:\.\d+)?(?:px|rem)", self.value):
                errors.append(f"Invalid spacing value: {self.value}")

        if self.alias and self.alias == self.name:
            errors.append("A token cannot reference itself")

        return errors


@dataclass
class AccessibilityRequirement:
    semantic_role: str
    accessible_name: bool
    keyboard_operable: bool
    visible_focus: bool
    contrast_ratio: Optional[float] = None
    level: AccessibilityLevel = AccessibilityLevel.AA

    def validate(self) -> list[str]:
        errors = []

        if not self.semantic_role:
            errors.append("Semantic role is required")

        if not self.accessible_name:
            errors.append("Accessible name is missing")

        if not self.keyboard_operable:
            errors.append("Component is not keyboard operable")

        if not self.visible_focus:
            errors.append("Visible keyboard focus is missing")

        minimum = {
            AccessibilityLevel.A: 3.0,
            AccessibilityLevel.AA: 4.5,
            AccessibilityLevel.AAA: 7.0,
        }[self.level]

        if self.contrast_ratio is not None:
            if not 0 <= self.contrast_ratio <= 21:
                errors.append("Contrast ratio must be between 0 and 21")
            elif self.contrast_ratio < minimum:
                errors.append(
                    f"Contrast ratio {self.contrast_ratio} "
                    f"is below {self.level.value} requirement {minimum}"
                )

        return errors


@dataclass
class Component:
    name: str
    category: str
    version: str
    properties: dict[str, Any]
    token_dependencies: list[str]
    accessibility: AccessibilityRequirement
    status: ComponentStatus = ComponentStatus.DRAFT
    dependencies: list[str] = field(default_factory=list)

    def validate(self) -> list[str]:
        errors = []

        if not re.fullmatch(r"[A-Z][A-Za-z0-9]*", self.name):
            errors.append(f"Invalid component name: {self.name}")

        if not re.fullmatch(r"\d+\.\d+\.\d+", self.version):
            errors.append(f"Invalid semantic version: {self.version}")

        if not self.category.strip():
            errors.append("Component category is required")

        if self.name in self.dependencies:
            errors.append("Component cannot depend on itself")

        errors.extend(self.accessibility.validate())
        return errors


@dataclass
class ValidationResult:
    severity: Severity
    subject: str
    message: str


class DesignSystem:
    def __init__(self, name: str):
        if not name.strip():
            raise ValueError("Design system name cannot be empty")

        self.name = name
        self.tokens: dict[str, DesignToken] = {}
        self.components: dict[str, Component] = {}
        self.results: list[ValidationResult] = []

    def add_token(self, token: DesignToken) -> None:
        if token.name in self.tokens:
            raise ValueError(f"Duplicate token: {token.name}")

        errors = token.validate()
        if errors:
            raise ValueError("; ".join(errors))

        self.tokens[token.name] = token

    def add_component(self, component: Component) -> None:
        if component.name in self.components:
            raise ValueError(f"Duplicate component: {component.name}")

        errors = component.validate()
        if errors:
            raise ValueError("; ".join(errors))

        self.components[component.name] = component

    def resolve_token(self, name: str) -> str:
        visited: set[str] = set()
        current = name

        while True:
            if current in visited:
                raise ValueError(f"Token alias cycle detected: {current}")

            visited.add(current)

            token = self.tokens.get(current)
            if token is None:
                raise KeyError(f"Unknown token: {current}")

            if token.alias is None:
                return token.value

            current = token.alias

    def validate_dependencies(self) -> list[ValidationResult]:
        results = []

        for component in self.components.values():
            for token_name in component.token_dependencies:
                if token_name not in self.tokens:
                    results.append(
                        ValidationResult(
                            Severity.ERROR,
                            component.name,
                            f"Unknown design token: {token_name}",
                        )
                    )

            for dependency in component.dependencies:
                if dependency not in self.components:
                    results.append(
                        ValidationResult(
                            Severity.ERROR,
                            component.name,
                            f"Unknown component dependency: {dependency}",
                        )
                    )

        return results

    def dependency_order(self) -> list[str]:
        """Topological ordering detects cyclic component dependencies."""
        graph = {
            name: component.dependencies
            for name, component in self.components.items()
        }

        temporary: set[str] = set()
        permanent: set[str] = set()
        ordered: list[str] = []

        def visit(name: str) -> None:
            if name in permanent:
                return

            if name in temporary:
                raise ValueError(f"Component dependency cycle at {name}")

            if name not in graph:
                raise ValueError(f"Unknown component dependency: {name}")

            temporary.add(name)

            for dependency in graph[name]:
                visit(dependency)

            temporary.remove(name)
            permanent.add(name)
            ordered.append(name)

        for name in graph:
            visit(name)

        return ordered

    def approve_component(self, name: str) -> None:
        component = self.components.get(name)

        if component is None:
            raise KeyError(name)

        if component.status not in (
            ComponentStatus.DRAFT,
            ComponentStatus.REVIEW,
        ):
            raise ValueError("Only draft or review components can be approved")

        if self.validate_dependencies():
            raise ValueError("Design system has unresolved dependencies")

        component.status = ComponentStatus.APPROVED

    def audit(self) -> list[ValidationResult]:
        results = self.validate_dependencies()

        for component in self.components.values():
            for error in component.validate():
                results.append(
                    ValidationResult(Severity.ERROR, component.name, error)
                )

            if component.status == ComponentStatus.DEPRECATED:
                results.append(
                    ValidationResult(
                        Severity.WARNING,
                        component.name,
                        "Component is deprecated",
                    )
                )

        for token in self.tokens.values():
            for error in token.validate():
                results.append(
                    ValidationResult(Severity.ERROR, token.name, error)
                )

        self.results = results
        return results

    def export(self, output: Path) -> None:
        document = {
            "name": self.name,
            "tokens": {
                name: {
                    **asdict(token),
                    "category": token.category.value,
                }
                for name, token in self.tokens.items()
            },
            "components": {
                name: {
                    **asdict(component),
                    "status": component.status.value,
                    "accessibility": {
                        **asdict(component.accessibility),
                        "level": component.accessibility.level.value,
                    },
                }
                for name, component in self.components.items()
            },
        }

        output.write_text(
            json.dumps(document, indent=2),
            encoding="utf-8",
        )


def calculate_contrast(foreground: str, background: str) -> float:
    """Calculate WCAG relative luminance contrast ratio."""

    def luminance(color: str) -> float:
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", color):
            raise ValueError(f"Invalid color: {color}")

        channels = [
            int(color[i:i + 2], 16) / 255
            for i in (1, 3, 5)
        ]

        linear = [
            channel / 12.92
            if channel <= 0.04045
            else ((channel + 0.055) / 1.055) ** 2.4
            for channel in channels
        ]

        return (
            0.2126 * linear[0]
            + 0.7152 * linear[1]
            + 0.0722 * linear[2]
        )

    light = max(luminance(foreground), luminance(background))
    dark = min(luminance(foreground), luminance(background))

    return (light + 0.05) / (dark + 0.05)


def build_example() -> DesignSystem:
    system = DesignSystem("Enterprise UI System")

    system.add_token(
        DesignToken("color.brand.primary", TokenType.COLOR, "#2457C5")
    )
    system.add_token(
        DesignToken("color.text.primary", TokenType.COLOR, "#172033")
    )
    system.add_token(
        DesignToken("color.surface.default", TokenType.COLOR, "#FFFFFF")
    )
    system.add_token(
        DesignToken(
            "color.action.primary",
            TokenType.COLOR,
            "color.brand.primary",
            alias="color.brand.primary",
        )
    )
    system.add_token(
        DesignToken("spacing.medium", TokenType.SPACING, "16px")
    )
    system.add_token(
        DesignToken("spacing.large", TokenType.SPACING, "24px")
    )
    system.add_token(
        DesignToken("radius.medium", TokenType.RADIUS, "8px")
    )

    button_accessibility = AccessibilityRequirement(
        semantic_role="button",
        accessible_name=True,
        keyboard_operable=True,
        visible_focus=True,
        contrast_ratio=calculate_contrast("#FFFFFF", "#2457C5"),
    )

    system.add_component(
        Component(
            name="Button",
            category="Actions",
            version="1.0.0",
            properties={
                "variant": ["primary", "secondary", "danger"],
                "size": ["small", "medium", "large"],
                "disabled": False,
            },
            token_dependencies=[
                "color.action.primary",
                "spacing.medium",
                "radius.medium",
            ],
            accessibility=button_accessibility,
        )
    )

    system.add_component(
        Component(
            name="IconButton",
            category="Actions",
            version="1.0.0",
            properties={
                "icon": "search",
                "label": "Search",
                "size": "medium",
            },
            token_dependencies=[
                "color.text.primary",
                "spacing.medium",
            ],
            accessibility=AccessibilityRequirement(
                semantic_role="button",
                accessible_name=True,
                keyboard_operable=True,
                visible_focus=True,
                contrast_ratio=calculate_contrast("#172033", "#FFFFFF"),
            ),
            dependencies=["Button"],
        )
    )

    system.add_component(
        Component(
            name="TextField",
            category="Forms",
            version="1.0.0",
            properties={
                "label": "Email address",
                "required": True,
                "type": "email",
            },
            token_dependencies=[
                "color.text.primary",
                "spacing.medium",
                "radius.medium",
            ],
            accessibility=AccessibilityRequirement(
                semantic_role="textbox",
                accessible_name=True,
                keyboard_operable=True,
                visible_focus=True,
                contrast_ratio=calculate_contrast("#172033", "#FFFFFF"),
            ),
        )
    )

    return system


class DesignSystemTests(unittest.TestCase):
    def test_contrast(self):
        self.assertGreaterEqual(
            calculate_contrast("#000000", "#FFFFFF"),
            21.0,
        )

    def test_token_alias(self):
        system = build_example()
        self.assertEqual(
            system.resolve_token("color.action.primary"),
            "#2457C5",
        )

    def test_dependency_order(self):
        system = build_example()
        order = system.dependency_order()
        self.assertLess(order.index("Button"), order.index("IconButton"))

    def test_accessibility_failure(self):
        requirement = AccessibilityRequirement(
            semantic_role="button",
            accessible_name=False,
            keyboard_operable=True,
            visible_focus=False,
            contrast_ratio=2.0,
        )
        self.assertGreaterEqual(len(requirement.validate()), 3)

    def test_alias_cycle(self):
        system = DesignSystem("Test")
        system.tokens["color.a"] = DesignToken(
            "color.a", TokenType.COLOR, "color.b", alias="color.b"
        )
        system.tokens["color.b"] = DesignToken(
            "color.b", TokenType.COLOR, "color.a", alias="color.a"
        )

        with self.assertRaises(ValueError):
            system.resolve_token("color.a")


def main() -> None:
    system = build_example()

    print(f"Design system: {system.name}")
    print("\nResolved design tokens:")

    for name in system.tokens:
        print(f"  {name}: {system.resolve_token(name)}")

    print("\nComponent dependency order:")
    print("  " + " -> ".join(system.dependency_order()))

    print("\nAccessibility contrast:")
    ratio = calculate_contrast("#FFFFFF", "#2457C5")
    print(f"  White on primary blue: {ratio:.2f}:1")

    print("\nGovernance audit:")
    results = system.audit()

    if not results:
        print("  No governance violations detected.")
    else:
        for result in results:
            print(
                f"  [{result.severity.value}] "
                f"{result.subject}: {result.message}"
            )

    output = Path("design-system.json")
    system.export(output)
    print(f"\nExported configuration: {output.resolve()}")

    if "--test" in sys.argv:
        unittest.main(argv=[sys.argv[0]])


if __name__ == "__main__":
    main()
