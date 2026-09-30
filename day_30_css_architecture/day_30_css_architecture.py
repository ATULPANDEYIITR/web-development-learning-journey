"""
CSS Architecture Laboratory

A self-contained executable model of maintainable CSS architecture.

The program models four complementary CSS architecture techniques:
- BEM naming for explicit component structure
- Utility classes for narrowly scoped reusable rules
- Component styles for component-owned presentation
- CSS variables for centralized design tokens and runtime theming

It also provides:
- selector validation
- specificity analysis
- architecture policy checks
- dependency-aware stylesheet organization
- theme resolution
- CSS generation
- maintainability metrics
- demonstrations of common architectural failures
- deterministic tests

No external packages are required.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import re
import textwrap
from typing import Iterable


class StyleLayer(Enum):
    RESET = "reset"
    TOKENS = "tokens"
    BASE = "base"
    OBJECTS = "objects"
    COMPONENTS = "components"
    UTILITIES = "utilities"
    OVERRIDES = "overrides"


LAYER_ORDER = {
    StyleLayer.RESET: 0,
    StyleLayer.TOKENS: 1,
    StyleLayer.BASE: 2,
    StyleLayer.OBJECTS: 3,
    StyleLayer.COMPONENTS: 4,
    StyleLayer.UTILITIES: 5,
    StyleLayer.OVERRIDES: 6,
}


@dataclass(frozen=True)
class CssRule:
    selector: str
    declarations: dict[str, str]
    layer: StyleLayer
    source: str = ""

    def declaration_count(self) -> int:
        return len(self.declarations)


@dataclass
class Component:
    name: str
    element: str
    block: str
    modifiers: set[str] = field(default_factory=set)
    elements: set[str] = field(default_factory=set)
    utilities: set[str] = field(default_factory=set)

    def classes(self) -> set[str]:
        classes = {self.block}
        classes.update(f"{self.block}__{element}" for element in self.elements)
        classes.update(f"{self.block}--{modifier}" for modifier in self.modifiers)
        classes.update(self.utilities)
        return classes


@dataclass(frozen=True)
class DesignTokens:
    colors: dict[str, str]
    spacing: dict[str, str]
    typography: dict[str, str]
    radii: dict[str, str]
    shadows: dict[str, str]

    def to_css(self) -> str:
        lines = [":root {"]
        groups = (
            ("color", self.colors),
            ("space", self.spacing),
            ("font", self.typography),
            ("radius", self.radii),
            ("shadow", self.shadows),
        )

        for prefix, values in groups:
            for name, value in values.items():
                lines.append(f"  --{prefix}-{name}: {value};")

        lines.append("}")
        return "\n".join(lines)


@dataclass
class Theme:
    name: str
    overrides: dict[str, str]

    def to_css(self, selector: str = ":root") -> str:
        lines = [f"{selector} {{"]
        for variable, value in self.overrides.items():
            lines.append(f"  {variable}: {value};")
        lines.append("}")
        return "\n".join(lines)


@dataclass(frozen=True)
class ArchitectureViolation:
    category: str
    message: str
    selector: str = ""

    def __str__(self) -> str:
        location = f" [{self.selector}]" if self.selector else ""
        return f"{self.category}{location}: {self.message}"


BEM_BLOCK_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
BEM_CLASS_RE = re.compile(
    r"^(?P<block>[a-z][a-z0-9]*(?:-[a-z0-9]+)*)"
    r"(?:(?:__(?P<element>[a-z][a-z0-9]*(?:-[a-z0-9]+)*))|"
    r"(?:--(?P<modifier>[a-z][a-z0-9]*(?:-[a-z0-9]+)*)))?$"
)

UTILITY_NAMES = {
    "u-hidden",
    "u-sr-only",
    "u-text-center",
    "u-flex",
    "u-grid",
    "u-gap-sm",
    "u-gap-md",
    "u-gap-lg",
    "u-mt-sm",
    "u-mt-md",
    "u-mt-lg",
    "u-p-sm",
    "u-p-md",
    "u-p-lg",
    "u-w-full",
}

DISALLOWED_GLOBAL_CLASS_PATTERNS = (
    re.compile(r"^button$"),
    re.compile(r"^card$"),
    re.compile(r"^title$"),
    re.compile(r"^header$"),
    re.compile(r"^active$"),
)


def bem_parts(class_name: str) -> tuple[str, str | None, str | None] | None:
    match = BEM_CLASS_RE.fullmatch(class_name)
    if not match:
        return None

    return (
        match.group("block"),
        match.group("element"),
        match.group("modifier"),
    )


def is_bem_class(class_name: str) -> bool:
    return bem_parts(class_name) is not None


def bem_block(name: str) -> str:
    if not BEM_BLOCK_RE.fullmatch(name):
        raise ValueError(f"Invalid BEM block name: {name}")
    return name


def bem_element(block: str, element: str) -> str:
    bem_block(block)

    if not BEM_BLOCK_RE.fullmatch(element):
        raise ValueError(f"Invalid BEM element name: {element}")

    return f"{block}__{element}"


def bem_modifier(block: str, modifier: str) -> str:
    bem_block(block)

    if not BEM_BLOCK_RE.fullmatch(modifier):
        raise ValueError(f"Invalid BEM modifier name: {modifier}")

    return f"{block}--{modifier}"


def utility_class(name: str) -> str:
    if name not in UTILITY_NAMES:
        raise ValueError(
            f"Unknown utility '{name}'. "
            f"Define utilities explicitly instead of silently inventing them."
        )
    return name


def extract_classes(selector: str) -> list[str]:
    return re.findall(r"\.([a-zA-Z0-9_-]+)", selector)


def calculate_specificity(selector: str) -> tuple[int, int, int]:
    """
    Approximate CSS specificity as (IDs, classes/attributes/pseudo-classes, elements).

    This deliberately handles the selector forms used by this laboratory rather
    than attempting to implement every CSS Selectors specification feature.
    """
    without_strings = re.sub(r'"[^"]*"|\'[^\']*\'', "", selector)

    ids = len(re.findall(r"#[a-zA-Z0-9_-]+", without_strings))
    classes = len(re.findall(r"\.[a-zA-Z0-9_-]+", without_strings))
    classes += len(re.findall(r"\[[^\]]+\]", without_strings))
    classes += len(
        re.findall(
            r":(?!:)[a-zA-Z0-9_-]+(?:\([^)]*\))?",
            without_strings,
        )
    )

    cleaned = re.sub(r"#[a-zA-Z0-9_-]+", " ", without_strings)
    cleaned = re.sub(r"\.[a-zA-Z0-9_-]+", " ", cleaned)
    cleaned = re.sub(r"\[[^\]]+\]", " ", cleaned)
    cleaned = re.sub(r"::?[a-zA-Z0-9_-]+(?:\([^)]*\))?", " ", cleaned)
    cleaned = re.sub(r"[>+~*]", " ", cleaned)

    html_elements = {
        "html", "body", "main", "header", "footer", "nav", "section",
        "article", "aside", "div", "span", "button", "input", "form",
        "label", "a", "ul", "ol", "li", "p", "h1", "h2", "h3", "img",
    }

    elements = sum(
        1
        for token in re.findall(r"\b[a-zA-Z][a-zA-Z0-9-]*\b", cleaned)
        if token.lower() in html_elements
    )

    return ids, classes, elements


def selector_is_descendant_heavy(selector: str) -> bool:
    """
    Deep descendant selectors couple a component to its surrounding markup.
    """
    return len(re.findall(r"\s+", selector.strip())) >= 2


class ArchitectureLinter:
    def __init__(
        self,
        rules: Iterable[CssRule],
        known_components: Iterable[Component],
        known_utilities: Iterable[str],
    ) -> None:
        self.rules = list(rules)
        self.components = list(known_components)
        self.known_utilities = set(known_utilities)

    def lint(self) -> list[ArchitectureViolation]:
        violations: list[ArchitectureViolation] = []

        for rule in self.rules:
            classes = extract_classes(rule.selector)
            specificity = calculate_specificity(rule.selector)

            if rule.layer == StyleLayer.UTILITIES:
                if len(classes) != 1 or classes[0] not in self.known_utilities:
                    violations.append(
                        ArchitectureViolation(
                            "utility-boundary",
                            "A utility rule should expose one recognized utility class.",
                            rule.selector,
                        )
                    )

                if specificity != (0, 1, 0):
                    violations.append(
                        ArchitectureViolation(
                            "utility-specificity",
                            "Utilities should normally remain at single-class specificity.",
                            rule.selector,
                        )
                    )

            if rule.layer == StyleLayer.COMPONENTS:
                for class_name in classes:
                    if class_name.startswith("u-"):
                        violations.append(
                            ArchitectureViolation(
                                "component-boundary",
                                "Utility classes should be composed in markup, not defined inside component selectors.",
                                rule.selector,
                            )
                        )

                if selector_is_descendant_heavy(rule.selector):
                    violations.append(
                        ArchitectureViolation(
                            "component-coupling",
                            "Deep descendant selectors make component markup structure part of the CSS contract.",
                            rule.selector,
                        )
                    )

            for class_name in classes:
                if any(pattern.fullmatch(class_name) for pattern in DISALLOWED_GLOBAL_CLASS_PATTERNS):
                    violations.append(
                        ArchitectureViolation(
                            "global-naming",
                            "Generic class names create ownership ambiguity in a component-oriented architecture.",
                            rule.selector,
                        )
                    )

            if specificity[0] > 0:
                violations.append(
                    ArchitectureViolation(
                        "specificity",
                        "ID selectors create unnecessary specificity pressure for component styles.",
                        rule.selector,
                    )
                )

        return violations


class Stylesheet:
    def __init__(self) -> None:
        self.rules: list[CssRule] = []

    def add_rule(self, rule: CssRule) -> None:
        self.rules.append(rule)

    def validate_layer_order(self) -> None:
        previous = -1
        for rule in self.rules:
            current = LAYER_ORDER[rule.layer]
            if current < previous:
                raise ValueError(
                    f"Layer order violation: {rule.selector} appears after a later layer."
                )
            previous = current

    def render(self) -> str:
        self.validate_layer_order()

        output: list[str] = []

        current_layer: StyleLayer | None = None
        for rule in self.rules:
            if rule.layer != current_layer:
                if output:
                    output.append("")
                output.append(f"/* {rule.layer.value} */")
                current_layer = rule.layer

            output.append(f"{rule.selector} {{")
            for property_name, value in rule.declarations.items():
                output.append(f"  {property_name}: {value};")
            output.append("}")

        return "\n".join(output)


def build_design_tokens() -> DesignTokens:
    return DesignTokens(
        colors={
            "surface": "#10141c",
            "surface-raised": "#171d27",
            "text": "#f5f7fa",
            "text-muted": "#aab4c3",
            "accent": "#7dd3fc",
            "success": "#86efac",
            "danger": "#fca5a5",
            "border": "#303b4d",
        },
        spacing={
            "xs": "0.25rem",
            "sm": "0.5rem",
            "md": "1rem",
            "lg": "1.5rem",
            "xl": "2rem",
        },
        typography={
            "body": "1rem",
            "small": "0.875rem",
            "title": "1.5rem",
            "weight-normal": "400",
            "weight-bold": "700",
        },
        radii={
            "sm": "0.375rem",
            "md": "0.625rem",
            "lg": "1rem",
        },
        shadows={
            "card": "0 8px 24px rgb(0 0 0 / 0.22)",
        },
    )


def build_components() -> list[Component]:
    return [
        Component(
            name="Review Card",
            element="article",
            block=bem_block("review-card"),
            elements={"header", "title", "meta", "status", "actions"},
            modifiers={"approved", "changes-requested"},
            utilities={"u-p-md", "u-mt-md"},
        ),
        Component(
            name="Status Badge",
            element="span",
            block=bem_block("status-badge"),
            elements={"label"},
            modifiers={"success", "warning", "danger"},
        ),
        Component(
            name="Repository Header",
            element="header",
            block=bem_block("repository-header"),
            elements={"title", "description", "actions"},
            modifiers={"compact"},
        ),
    ]


def build_stylesheet() -> Stylesheet:
    tokens = build_design_tokens()
    sheet = Stylesheet()

    sheet.add_rule(
        CssRule(
            selector="*",
            declarations={"box-sizing": "border-box"},
            layer=StyleLayer.RESET,
            source="global reset",
        )
    )

    for variable, value in {
        "--color-surface": tokens.colors["surface"],
        "--color-surface-raised": tokens.colors["surface-raised"],
        "--color-text": tokens.colors["text"],
        "--color-text-muted": tokens.colors["text-muted"],
        "--color-accent": tokens.colors["accent"],
        "--color-border": tokens.colors["border"],
        "--space-sm": tokens.spacing["sm"],
        "--space-md": tokens.spacing["md"],
        "--space-lg": tokens.spacing["lg"],
        "--radius-md": tokens.radii["md"],
        "--shadow-card": tokens.shadows["card"],
    }.items():
        sheet.add_rule(
            CssRule(
                selector=":root",
                declarations={variable: value},
                layer=StyleLayer.TOKENS,
                source="design tokens",
            )
        )

    sheet.add_rule(
        CssRule(
            selector="body",
            declarations={
                "margin": "0",
                "background": "var(--color-surface)",
                "color": "var(--color-text)",
                "font-family": "system-ui, sans-serif",
            },
            layer=StyleLayer.BASE,
            source="document defaults",
        )
    )

    sheet.add_rule(
        CssRule(
            selector=".review-card",
            declarations={
                "background": "var(--color-surface-raised)",
                "border": "1px solid var(--color-border)",
                "border-radius": "var(--radius-md)",
                "box-shadow": "var(--shadow-card)",
            },
            layer=StyleLayer.COMPONENTS,
            source="review-card component",
        )
    )

    sheet.add_rule(
        CssRule(
            selector=".review-card__header",
            declarations={
                "display": "flex",
                "align-items": "center",
                "justify-content": "space-between",
                "gap": "var(--space-md)",
            },
            layer=StyleLayer.COMPONENTS,
            source="review-card component",
        )
    )

    sheet.add_rule(
        CssRule(
            selector=".review-card__title",
            declarations={
                "margin": "0",
                "font-size": "1.125rem",
                "font-weight": "var(--font-weight-bold, 700)",
            },
            layer=StyleLayer.COMPONENTS,
            source="review-card component",
        )
    )

    sheet.add_rule(
        CssRule(
            selector=".review-card--approved",
            declarations={
                "border-color": "var(--color-success, #86efac)",
            },
            layer=StyleLayer.COMPONENTS,
            source="review-card modifier",
        )
    )

    sheet.add_rule(
        CssRule(
            selector=".status-badge",
            declarations={
                "display": "inline-flex",
                "align-items": "center",
                "padding": "0.25rem 0.5rem",
                "border-radius": "999px",
                "font-size": "0.875rem",
            },
            layer=StyleLayer.COMPONENTS,
            source="status-badge component",
        )
    )

    sheet.add_rule(
        CssRule(
            selector=".status-badge--success",
            declarations={
                "background": "color-mix(in srgb, var(--color-success, #86efac) 18%, transparent)",
                "color": "var(--color-success, #86efac)",
            },
            layer=StyleLayer.COMPONENTS,
            source="status-badge modifier",
        )
    )

    sheet.add_rule(
        CssRule(
            selector=".u-flex",
            declarations={"display": "flex"},
            layer=StyleLayer.UTILITIES,
            source="layout utility",
        )
    )

    sheet.add_rule(
        CssRule(
            selector=".u-gap-md",
            declarations={"gap": "var(--space-md)"},
            layer=StyleLayer.UTILITIES,
            source="spacing utility",
        )
    )

    sheet.add_rule(
        CssRule(
            selector=".u-p-md",
            declarations={"padding": "var(--space-md)"},
            layer=StyleLayer.UTILITIES,
            source="spacing utility",
        )
    )

    return sheet


def demonstrate_bem() -> None:
    print("\nBEM naming")
    block = bem_block("review-card")
    title = bem_element(block, "title")
    approved = bem_modifier(block, "approved")

    print(f"Block:    {block}")
    print(f"Element:  {title}")
    print(f"Modifier: {approved}")

    examples = [block, title, approved, "review-card__header", "review-card--changes-requested"]
    for class_name in examples:
        print(f"  {class_name:<35} valid={is_bem_class(class_name)}")

    invalid = ["card-title", "review_card", "ReviewCard", "review-card___title"]
    for class_name in invalid:
        print(f"  {class_name:<35} valid={is_bem_class(class_name)}")


def demonstrate_utilities() -> None:
    print("\nUtility classes")
    utilities = ["u-flex", "u-gap-md", "u-p-md"]

    for utility in utilities:
        print(f"  {utility}: {utility_class(utility)}")

    print(
        "Utilities remain intentionally small. "
        "They encode reusable behavior such as spacing or layout rather than "
        "the identity of a particular UI component."
    )


def demonstrate_component_composition() -> None:
    print("\nComponent composition")

    component = Component(
        name="Repository Review Card",
        element="article",
        block="review-card",
        elements={"header", "title", "actions"},
        modifiers={"approved"},
        utilities={"u-p-md", "u-mt-md"},
    )

    print("Component class contract:")
    for class_name in sorted(component.classes()):
        print(f"  .{class_name}")

    print(
        "\nMarkup conceptually combines component ownership with utilities:\n"
        "  <article class=\"review-card review-card--approved u-p-md\">"
    )


def demonstrate_tokens_and_themes() -> None:
    print("\nCSS variables and themes")

    tokens = build_design_tokens()
    print(tokens.to_css())

    dark = Theme(
        name="dark",
        overrides={
            "--color-surface": "#10141c",
            "--color-surface-raised": "#171d27",
            "--color-text": "#f5f7fa",
        },
    )

    light = Theme(
        name="light",
        overrides={
            "--color-surface": "#f7f8fa",
            "--color-surface-raised": "#ffffff",
            "--color-text": "#172033",
        },
    )

    print("\nDark theme:")
    print(dark.to_css('[data-theme="dark"]'))

    print("\nLight theme:")
    print(light.to_css('[data-theme="light"]'))


def demonstrate_specificity() -> None:
    print("\nSpecificity analysis")

    selectors = [
        ".review-card",
        ".review-card__title",
        ".review-card .review-card__title",
        "#dashboard .review-card",
        "article.review-card",
    ]

    for selector in selectors:
        print(f"  {selector:<45} specificity={calculate_specificity(selector)}")

    print(
        "\nA component architecture normally favors low, predictable specificity. "
        "This reduces the need for increasingly specific overrides."
    )


def demonstrate_linting() -> None:
    print("\nArchitecture linting")

    sheet = build_stylesheet()
    components = build_components()
    linter = ArchitectureLinter(sheet.rules, components, UTILITY_NAMES)
    violations = linter.lint()

    if not violations:
        print("  No architecture violations detected.")
    else:
        for violation in violations:
            print(f"  {violation}")

    intentionally_bad_rules = [
        CssRule(
            selector=".card .title",
            declarations={"color": "red"},
            layer=StyleLayer.COMPONENTS,
            source="legacy stylesheet",
        ),
        CssRule(
            selector="#dashboard .review-card",
            declarations={"padding": "20px"},
            layer=StyleLayer.COMPONENTS,
            source="legacy stylesheet",
        ),
        CssRule(
            selector=".review-card .u-p-md",
            declarations={"padding": "var(--space-md)"},
            layer=StyleLayer.COMPONENTS,
            source="incorrect utility ownership",
        ),
    ]

    bad_linter = ArchitectureLinter(
        intentionally_bad_rules,
        components,
        UTILITY_NAMES,
    )

    print("\nDeliberately problematic rules:")
    for violation in bad_linter.lint():
        print(f"  {violation}")


def demonstrate_layer_order() -> None:
    print("\nLayer ordering")

    sheet = build_stylesheet()
    sheet.validate_layer_order()

    for rule in sheet.rules:
        print(f"  {rule.layer.value:<11} {rule.selector}")

    print(
        "\nThe ordering expresses architectural intent: tokens and base rules "
        "establish foundations, components own component presentation, and "
        "utilities provide explicit composition points."
    )


def demonstrate_generated_css() -> None:
    print("\nGenerated stylesheet")

    css = build_stylesheet().render()
    print(textwrap.indent(css, "  "))


def calculate_metrics(rules: Iterable[CssRule]) -> dict[str, float]:
    rules = list(rules)

    if not rules:
        return {
            "rules": 0,
            "declarations": 0,
            "average_declarations_per_rule": 0.0,
            "high_specificity_rules": 0,
            "deep_selectors": 0,
        }

    high_specificity = sum(
        1
        for rule in rules
        if calculate_specificity(rule.selector)[0] > 0
        or calculate_specificity(rule.selector)[1] >= 3
    )

    deep_selectors = sum(
        1 for rule in rules if selector_is_descendant_heavy(rule.selector)
    )

    declarations = sum(rule.declaration_count() for rule in rules)

    return {
        "rules": len(rules),
        "declarations": declarations,
        "average_declarations_per_rule": declarations / len(rules),
        "high_specificity_rules": high_specificity,
        "deep_selectors": deep_selectors,
    }


def demonstrate_maintainability_metrics() -> None:
    print("\nMaintainability metrics")

    metrics = calculate_metrics(build_stylesheet().rules)

    for name, value in metrics.items():
        if isinstance(value, float):
            print(f"  {name:<34} {value:.2f}")
        else:
            print(f"  {name:<34} {value}")

    print(
        "\nThese metrics are diagnostic rather than absolute quality scores. "
        "A small stylesheet can still be difficult to maintain if its ownership "
        "boundaries are unclear, while a large stylesheet can remain manageable "
        "when selectors, tokens, and component responsibilities are predictable."
    )


def demonstrate_failure_modes() -> None:
    print("\nFailure modes and their architectural consequences")

    failures = {
        "Generic component names":
            "Classes such as .card or .active make ownership ambiguous and encourage collisions.",
        "Deep descendant selectors":
            "Selectors such as .page .sidebar .card .title depend on surrounding markup.",
        "Component-specific spacing utilities":
            "Encoding .review-card-padding-24 as a utility mixes component identity with utility responsibility.",
        "Repeated literal colors":
            "Hard-coded values spread visual decisions across files and make theme changes expensive.",
        "Specificity escalation":
            "Adding IDs or increasingly deep selectors turns overrides into a cascade arms race.",
        "Uncontrolled utility growth":
            "A utility layer can become an unstructured second component system if every arbitrary declaration becomes a utility.",
        "Variable indirection without naming":
            "Poorly named custom properties obscure intent and make token replacement difficult.",
    }

    for name, consequence in failures.items():
        print(f"  {name}: {consequence}")


def demonstrate_edge_cases() -> None:
    print("\nValidation and edge cases")

    tests = [
        ("valid block", lambda: bem_block("repository-header")),
        ("invalid block", lambda: bem_block("Repository_Header")),
        ("valid element", lambda: bem_element("review-card", "status")),
        ("invalid element", lambda: bem_element("review-card", "status.label")),
        ("known utility", lambda: utility_class("u-gap-md")),
        ("unknown utility", lambda: utility_class("utility-that-does-not-exist")),
    ]

    for label, operation in tests:
        try:
            result = operation()
            print(f"  {label:<22} accepted -> {result}")
        except ValueError as exc:
            print(f"  {label:<22} rejected -> {exc}")


def demonstrate_realistic_page_model() -> None:
    print("\nRealistic repository page model")

    page_markup = {
        "repository-header": [
            "repository-header",
            "repository-header__title",
            "repository-header__description",
            "repository-header__actions",
        ],
        "review-card": [
            "review-card",
            "review-card--approved",
            "review-card__header",
            "review-card__title",
            "review-card__meta",
            "status-badge",
            "status-badge--success",
            "u-flex",
            "u-gap-md",
        ],
    }

    for component, classes in page_markup.items():
        print(f"\n  {component}")
        for class_name in classes:
            print(f"    .{class_name}")

    print(
        "\nThe component names establish ownership, modifiers express component "
        "state, and utilities express orthogonal layout concerns."
    )


def run_tests() -> None:
    print("\nExecutable checks")

    assert is_bem_class("review-card")
    assert is_bem_class("review-card__title")
    assert is_bem_class("review-card--approved")
    assert not is_bem_class("review_card")
    assert not is_bem_class("ReviewCard")

    assert calculate_specificity(".review-card") == (0, 1, 0)
    assert calculate_specificity("#app .review-card") == (1, 1, 0)

    tokens = build_design_tokens()
    assert "--color-accent: #7dd3fc;" in tokens.to_css()

    sheet = build_stylesheet()
    sheet.validate_layer_order()
    assert ".review-card" in sheet.render()

    violations = ArchitectureLinter(
        sheet.rules,
        build_components(),
        UTILITY_NAMES,
    ).lint()

    assert not violations

    try:
        bem_element("review-card", "invalid.element")
    except ValueError:
        pass
    else:
        raise AssertionError("Invalid BEM element should be rejected.")

    print("  All assertions passed.")


def main() -> None:
    print("=" * 72)
    print("CSS ARCHITECTURE LABORATORY")
    print("BEM | Utility Classes | Component Styles | CSS Variables")
    print("=" * 72)

    demonstrate_bem()
    demonstrate_utilities()
    demonstrate_component_composition()
    demonstrate_tokens_and_themes()
    demonstrate_specificity()
    demonstrate_linting()
    demonstrate_layer_order()
    demonstrate_generated_css()
    demonstrate_maintainability_metrics()
    demonstrate_failure_modes()
    demonstrate_edge_cases()
    demonstrate_realistic_page_model()
    run_tests()

    print("\nArchitecture model completed successfully.")


if __name__ == "__main__":
    main()
