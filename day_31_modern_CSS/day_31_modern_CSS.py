#!/usr/bin/env python3
"""
Modern CSS laboratory.

This executable script demonstrates:
- CSS custom properties and fallback behavior
- Custom-property dependency graphs and cycle detection
- CSS nesting
- :is() and :where() selector semantics
- :has() relational selectors
- Logical properties and writing-mode-aware layout
- Generation and validation of a practical CSS design system
- CSS feature detection and browser-facing diagnostics
- A small CSS architecture analyzer for production-oriented checks

The program intentionally generates CSS rather than requiring third-party
packages. It also models several CSS rules so that important relationships
can be inspected from the command line.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import re
import textwrap
from collections import defaultdict, deque
from typing import Iterable


# ---------------------------------------------------------------------------
# Custom properties
# ---------------------------------------------------------------------------

@dataclass
class DesignTokens:
    """A practical token set represented as CSS custom properties."""

    values: dict[str, str] = field(default_factory=dict)

    def set(self, name: str, value: str) -> None:
        if not name.startswith("--"):
            raise ValueError("CSS custom property names must begin with '--'.")
        self.values[name] = value

    def get(self, name: str, fallback: str | None = None) -> str | None:
        return self.values.get(name, fallback)

    def as_css(self, selector: str = ":root") -> str:
        lines = [f"{selector} {{"]
        for name, value in self.values.items():
            lines.append(f"  {name}: {value};")
        lines.append("}")
        return "\n".join(lines)


def extract_var_references(value: str) -> list[str]:
    """Extract custom-property names referenced by var(--token) expressions."""
    return re.findall(r"var\(\s*(--[-_a-zA-Z0-9]+)", value)


def resolve_custom_property(
    name: str,
    values: dict[str, str],
    stack: tuple[str, ...] = (),
) -> str:
    """
    Resolve a small but useful subset of CSS var() expressions.

    CSS itself resolves custom properties at computed-value time. This model
    is deliberately limited to demonstrate dependency resolution, fallbacks,
    and cycles without pretending to be a complete CSS parser.
    """
    if name in stack:
        cycle = " -> ".join((*stack, name))
        raise ValueError(f"Custom-property cycle detected: {cycle}")

    if name not in values:
        raise KeyError(f"Unknown custom property: {name}")

    value = values[name]

    pattern = re.compile(
        r"var\(\s*(--[-_a-zA-Z0-9]+)"
        r"(?:\s*,\s*([^()]+))?\s*\)"
    )

    def replace(match: re.Match[str]) -> str:
        dependency = match.group(1)
        fallback = match.group(2)

        if dependency not in values:
            if fallback is not None:
                return fallback.strip()
            raise KeyError(
                f"{name} depends on undefined {dependency} without a fallback"
            )

        return resolve_custom_property(
            dependency,
            values,
            (*stack, name),
        )

    previous = None
    resolved = value

    # Multiple passes support chains such as:
    # --surface-strong -> --surface -> --color-blue
    while previous != resolved and "var(" in resolved:
        previous = resolved
        resolved = pattern.sub(replace, resolved)

    return resolved


def demonstrate_custom_properties() -> None:
    print("\nCUSTOM PROPERTIES")
    print("=================")

    tokens = DesignTokens(
        {
            "--color-blue-600": "#2563eb",
            "--color-blue-700": "#1d4ed8",
            "--color-surface": "white",
            "--color-surface-raised": "var(--color-surface)",
            "--color-text": "#172033",
            "--color-muted": "#64748b",
            "--space-1": "0.25rem",
            "--space-2": "0.5rem",
            "--space-3": "0.75rem",
            "--space-4": "1rem",
            "--radius-md": "0.75rem",
            "--focus-ring": "0 0 0 3px rgb(37 99 235 / 25%)",
        }
    )

    print(tokens.as_css())

    values = tokens.values

    for name in (
        "--color-surface-raised",
        "--color-text",
        "--focus-ring",
    ):
        print(f"{name} => {resolve_custom_property(name, values)}")

    fallback_value = "var(--missing-spacing, 1rem)"
    temporary = {**values, "--card-gap": fallback_value}
    print(
        "--card-gap =>",
        resolve_custom_property("--card-gap", temporary),
        "(fallback used)",
    )

    cyclic = {
        "--a": "var(--b)",
        "--b": "var(--c)",
        "--c": "var(--a)",
    }

    try:
        resolve_custom_property("--a", cyclic)
    except ValueError as exc:
        print("Cycle validation:", exc)


# ---------------------------------------------------------------------------
# CSS selector modeling
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Element:
    """
    Minimal DOM-like structure used to reason about :has().

    This is not a browser DOM. It contains only the relationships needed for
    the selector examples in this script.
    """

    tag: str
    classes: frozenset[str] = frozenset()
    attributes: dict[str, str] = field(default_factory=dict)
    children: tuple["Element", ...] = ()

    def has_class(self, name: str) -> bool:
        return name in self.classes

    def descendant_matches(self, predicate) -> bool:
        return any(
            predicate(child) or child.descendant_matches(predicate)
            for child in self.children
        )


def has_class(element: Element, class_name: str) -> bool:
    """Represent the useful portion of .card:has(.error)."""
    return element.has_class(class_name)


def contains_descendant_with_class(
    element: Element,
    class_name: str,
) -> bool:
    return element.descendant_matches(
        lambda node: node.has_class(class_name)
    )


def demonstrate_has() -> None:
    print("\n:HAS() RELATIONAL SELECTOR")
    print("==========================")

    invalid_input = Element(
        tag="input",
        classes=frozenset({"input", "error"}),
        attributes={"aria-invalid": "true"},
    )

    valid_input = Element(
        tag="input",
        classes=frozenset({"input"}),
        attributes={"aria-invalid": "false"},
    )

    invalid_field = Element(
        tag="div",
        classes=frozenset({"field"}),
        children=(invalid_input,),
    )

    valid_field = Element(
        tag="div",
        classes=frozenset({"field"}),
        children=(valid_input,),
    )

    print(
        ".field:has(.error) =>",
        contains_descendant_with_class(invalid_field, "error"),
    )
    print(
        ".field:has(.error) =>",
        contains_descendant_with_class(valid_field, "error"),
    )

    print(
        "CSS relationship: a parent can react to a descendant state without "
        "adding a JavaScript-only state class."
    )


# ---------------------------------------------------------------------------
# Selector specificity
# ---------------------------------------------------------------------------

def specificity(selector: str) -> tuple[int, int, int]:
    """
    Approximate CSS specificity for the selector forms used by this example.

    :is() and :has() take the specificity of their most specific argument.
    :where() deliberately contributes zero specificity.
    """
    selector = re.sub(r'"[^"]*"|\'[^\']*\'', "", selector)

    id_count = len(re.findall(r"#[a-zA-Z0-9_-]+", selector))

    def functional_specificity(
        function_name: str,
        source: str,
    ) -> tuple[int, int, int]:
        pattern = re.compile(
            rf":{function_name}\(([^()]*)\)"
        )
        matches = pattern.findall(source)
        result = [0, 0, 0]

        for content in matches:
            candidates = [
                specificity(part.strip())
                for part in content.split(",")
                if part.strip()
            ]

            if function_name == "where":
                contribution = (0, 0, 0)
            elif candidates:
                contribution = max(candidates)
            else:
                contribution = (0, 0, 0)

            result[0] += contribution[0]
            result[1] += contribution[1]
            result[2] += contribution[2]

        return tuple(result)

    is_spec = functional_specificity("is", selector)
    has_spec = functional_specificity("has", selector)

    selector_without_functions = re.sub(
        r":(?:is|where|has)\([^()]*\)",
        "",
        selector,
    )

    class_count = len(
        re.findall(
            r"\.[a-zA-Z0-9_-]+"
            r"|\[[^\]]+\]"
            r"|:(?!:)[a-zA-Z-]+",
            selector_without_functions,
        )
    )

    element_count = len(
        re.findall(
            r"(?<![#.:\w-])"
            r"(?:[a-zA-Z][a-zA-Z0-9-]*|\*)",
            selector_without_functions,
        )
    )

    return (
        id_count + is_spec[0] + has_spec[0],
        class_count + is_spec[1] + has_spec[1],
        element_count + is_spec[2] + has_spec[2],
    )


def demonstrate_selector_specificity() -> None:
    print("\n:is(), :where(), AND SPECIFICITY")
    print("================================")

    selectors = [
        ".nav :is(a, button, [role='button'])",
        ".nav :where(a, button, [role='button'])",
        ".form:has(input:invalid)",
        "#application :is(.field, .group)",
    ]

    for selector in selectors:
        print(f"{selector}")
        print(f"  approximate specificity = {specificity(selector)}")

    print(
        ":where() is useful for low-specificity defaults, while :is() and "
        ":has() participate in specificity according to their most specific "
        "argument."
    )


# ---------------------------------------------------------------------------
# Logical properties
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class LogicalBox:
    """
    Layout declaration expressed entirely with logical properties.

    The values describe block and inline dimensions rather than physical
    top/right/bottom/left directions.
    """

    padding_block: str
    padding_inline: str
    margin_inline: str
    border_block_start: str
    border_inline_end: str

    def to_css(self) -> str:
        return textwrap.dedent(
            f"""\
            padding-block: {self.padding_block};
            padding-inline: {self.padding_inline};
            margin-inline: {self.margin_inline};
            border-block-start: {self.border_block_start};
            border-inline-end: {self.border_inline_end};"""
        )


def demonstrate_logical_properties() -> None:
    print("\nLOGICAL PROPERTIES")
    print("===================")

    card = LogicalBox(
        padding_block="var(--space-4)",
        padding_inline="var(--space-5, 1.25rem)",
        margin_inline="auto",
        border_block_start="2px solid var(--color-blue-600)",
        border_inline_end="1px solid var(--color-muted)",
    )

    print(card.to_css())

    print(
        "These declarations describe layout relative to the writing mode. "
        "They do not hard-code left/right or top/bottom."
    )


# ---------------------------------------------------------------------------
# Modern CSS generation
# ---------------------------------------------------------------------------

BASE_CSS = """
:root {
  --color-brand: #2563eb;
  --color-brand-strong: #1d4ed8;
  --color-surface: #ffffff;
  --color-surface-muted: #f8fafc;
  --color-text: #172033;
  --color-muted: #64748b;
  --color-danger: #b91c1c;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-6: 1.5rem;
  --radius-md: 0.75rem;
  --content-width: 70rem;
}

.app-shell {
  max-inline-size: var(--content-width);
  margin-inline: auto;
  padding-block: var(--space-6);
  padding-inline: var(--space-4);

  & > header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: var(--space-4);
  }

  & .toolbar {
    display: flex;
    gap: var(--space-3);

    &:has(button[aria-expanded="true"]) {
      outline: 2px solid var(--color-brand);
      outline-offset: 0.25rem;
    }
  }
}

.card {
  padding-block: var(--space-4);
  padding-inline: var(--space-4);
  border: 1px solid var(--color-muted);
  border-radius: var(--radius-md);
  background: var(--color-surface);

  &:is(:hover, :focus-within) {
    border-color: var(--color-brand);
  }

  &:where(.compact) {
    padding-block: var(--space-3);
  }

  &:has(.validation-error) {
    border-color: var(--color-danger);
  }
}

.form-field {
  display: grid;
  gap: var(--space-2);

  &:has(input:invalid) {
    & > label {
      color: var(--color-danger);
    }

    & > input {
      border-color: var(--color-danger);
    }
  }
}
""".strip()


def validate_css_features(css: str) -> dict[str, int]:
    """Count the modern CSS mechanisms used by the generated stylesheet."""
    return {
        "custom_properties": len(re.findall(r"--[\w-]+\s*:", css)),
        "var_functions": len(re.findall(r"\bvar\(", css)),
        "nested_blocks": css.count("&"),
        "is_selectors": len(re.findall(r":is\(", css)),
        "where_selectors": len(re.findall(r":where\(", css)),
        "has_selectors": len(re.findall(r":has\(", css)),
        "logical_properties": len(
            re.findall(
                r"\b(?:margin|padding|border|inset|block|inline)"
                r"-(?:block|inline|start|end|size)",
                css,
            )
        ),
    }


def generate_theme_variant(base_css: str) -> str:
    """
    Create a dark theme using token overrides rather than duplicating
    component declarations.
    """
    dark_tokens = """
[data-theme="dark"] {
  --color-surface: #0f172a;
  --color-surface-muted: #111827;
  --color-text: #e5e7eb;
  --color-muted: #94a3b8;
  --color-brand: #60a5fa;
  --color-brand-strong: #93c5fd;
}
""".strip()

    return f"{base_css}\n\n{dark_tokens}"


def validate_production_rules(css: str) -> list[str]:
    """
    Perform architecture-level checks that are useful before shipping.

    This is not a standards-compliant CSS parser. It is a targeted linting
    layer for the stylesheet generated by this learning artifact.
    """
    warnings: list[str] = []

    if "!important" in css:
        warnings.append(
            "The stylesheet contains !important, which can complicate "
            "specificity and component overrides."
        )

    if re.search(r"\b(?:margin|padding)-(?:left|right)\s*:", css):
        warnings.append(
            "Physical horizontal spacing appears alongside logical spacing; "
            "review internationalization requirements."
        )

    if re.search(r"\b(?:left|right|top|bottom)\s*:", css):
        warnings.append(
            "Physical directional properties were detected; verify whether "
            "logical properties would better represent the layout intent."
        )

    if len(re.findall(r":has\(", css)) > 10:
        warnings.append(
            "Many :has() selectors are present. Test real DOM structures and "
            "style recalculation behavior on target browsers."
        )

    return warnings


# ---------------------------------------------------------------------------
# A small CSS cascade example
# ---------------------------------------------------------------------------

@dataclass
class StyleRule:
    selector: str
    declarations: dict[str, str]
    specificity: tuple[int, int, int]


def choose_winning_declaration(
    rules: Iterable[StyleRule],
    property_name: str,
) -> str | None:
    """
    Model a simplified cascade for one property.

    Real CSS also considers origins, importance, layers, scope, source order,
    inheritance, and other details. This function intentionally isolates
    selector specificity for educational analysis.
    """
    applicable = [
        rule
        for rule in rules
        if property_name in rule.declarations
    ]

    if not applicable:
        return None

    winner = max(
        enumerate(applicable),
        key=lambda item: (item[1].specificity, item[0]),
    )[1]

    return winner.declarations[property_name]


def demonstrate_cascade() -> None:
    print("\nSPECIFICITY AND CASCADE")
    print("=======================")

    rules = [
        StyleRule(
            ".card",
            {"border-color": "var(--color-muted)"},
            specificity(".card"),
        ),
        StyleRule(
            ".card:where(.compact)",
            {"border-color": "var(--color-brand)"},
            specificity(".card:where(.compact)"),
        ),
        StyleRule(
            ".dashboard .card:is(.selected, :focus-within)",
            {"border-color": "var(--color-brand-strong)"},
            specificity(".dashboard .card:is(.selected, :focus-within)"),
        ),
    ]

    for rule in rules:
        print(rule.selector, "=>", rule.specificity)

    winner = choose_winning_declaration(rules, "border-color")
    print("Simplified winning declaration:", winner)

    print(
        "The :where() selector deliberately stays easy to override; "
        ":is() can contribute meaningful specificity."
    )


# ---------------------------------------------------------------------------
# Feature-support diagnostics
# ---------------------------------------------------------------------------

def browser_feature_report() -> dict[str, str]:
    """
    Produce a compatibility checklist for a browser-side diagnostic.

    CSS feature support changes over time, so the script reports the feature
    to test rather than hard-coding browser-version claims.
    """
    return {
        "custom_properties": "CSS.supports('color', 'var(--token)')",
        "nesting": "CSS.supports('selector(&)')",
        "is": "CSS.supports('selector(:is(*))')",
        "where": "CSS.supports('selector(:where(*))')",
        "has": "CSS.supports('selector(:has(*))')",
        "logical_properties": (
            "CSS.supports('margin-inline', '1rem')"
        ),
    }


def print_feature_report() -> None:
    print("\nBROWSER FEATURE DETECTION")
    print("=========================")

    for feature, expression in browser_feature_report().items():
        print(f"{feature:22} {expression}")

    print(
        "Feature detection is preferable to assuming support from a browser "
        "name or from a remembered compatibility table."
    )


# ---------------------------------------------------------------------------
# Practical form example
# ---------------------------------------------------------------------------

FORM_CSS = """
.settings-form {
  display: grid;
  gap: var(--space-4);

  & .field {
    display: grid;
    gap: var(--space-2);

    &:has(input:invalid) {
      & > label {
        color: var(--color-danger);
      }

      & > input {
        border-color: var(--color-danger);
        box-shadow: var(--focus-ring);
      }
    }

    &:has(input:valid) {
      & > .status {
        color: #15803d;
      }
    }
  }

  & :is(input, select, textarea) {
    min-inline-size: 0;
    padding-block: var(--space-2);
    padding-inline: var(--space-3);
  }

  & :where(.help-text, .status) {
    font-size: 0.875rem;
    color: var(--color-muted);
  }
}
""".strip()


def demonstrate_form_architecture() -> None:
    print("\nFORM STATE ARCHITECTURE")
    print("========================")
    print(FORM_CSS)

    print(
        "The form uses :has() for parent-level validation state, :is() to "
        "group form controls, and :where() for intentionally low-specificity "
        "supporting text."
    )


# ---------------------------------------------------------------------------
# File output
# ---------------------------------------------------------------------------

def write_demo_stylesheet(path: str = "modern-css-demo.css") -> None:
    """Write a complete stylesheet for browser inspection."""
    stylesheet = generate_theme_variant(
        BASE_CSS + "\n\n" + FORM_CSS
    )

    with open(path, "w", encoding="utf-8") as file:
        file.write(stylesheet + "\n")

    print(f"\nGenerated stylesheet: {path}")


# ---------------------------------------------------------------------------
# JSON report
# ---------------------------------------------------------------------------

def build_report() -> dict:
    """Build machine-readable metadata about the demonstrated mechanisms."""
    counts = validate_css_features(BASE_CSS + "\n" + FORM_CSS)

    return {
        "artifact": "modern-css-laboratory",
        "topic": [
            "custom properties",
            "CSS nesting",
            ":is()",
            ":where()",
            ":has()",
            "logical properties",
        ],
        "feature_counts": counts,
        "production_warnings": validate_production_rules(
            BASE_CSS + "\n" + FORM_CSS
        ),
    }


def write_json_report(path: str = "modern-css-report.json") -> None:
    with open(path, "w", encoding="utf-8") as file:
        json.dump(build_report(), file, indent=2)

    print(f"Generated report: {path}")


# ---------------------------------------------------------------------------
# Integrated demonstration
# ---------------------------------------------------------------------------

def main() -> None:
    print("MODERN CSS LABORATORY")
    print("=====================")
    print(
        "Executable models and generated CSS for modern custom properties, "
        "nesting, relational selectors, and logical layout."
    )

    demonstrate_custom_properties()
    demonstrate_has()
    demonstrate_selector_specificity()
    demonstrate_logical_properties()
    demonstrate_cascade()
    demonstrate_form_architecture()
    print_feature_report()

    print("\nGENERATED CSS ANALYSIS")
    print("======================")

    complete_css = BASE_CSS + "\n\n" + FORM_CSS
    counts = validate_css_features(complete_css)

    for feature, count in counts.items():
        print(f"{feature:22} {count}")

    warnings = validate_production_rules(complete_css)

    if warnings:
        print("\nProduction checks:")
        for warning in warnings:
            print(f"- {warning}")
    else:
        print("\nProduction checks: no targeted warnings.")

    write_demo_stylesheet()
    write_json_report()

    print("\nGenerated stylesheet preview:")
    print("--------------------------------")
    print(generate_theme_variant(BASE_CSS))
    print("--------------------------------")

    print(
        "\nThe generated CSS is intended for a modern browser. The Python "
        "models intentionally do not attempt to replace a standards-compliant "
        "browser CSS engine."
    )


if __name__ == "__main__":
    main()
