"""
CSS FUNDAMENTALS: A COMPLETE BEGINNER-TO-ADVANCED STUDY SCRIPT

Topic covered:
- Purpose of CSS
- CSS syntax
- Selectors
- Declarations
- Properties
- Values
- Inline CSS
- Internal CSS
- External CSS
- Selector types
- Specificity
- Cascade and inheritance
- Common mistakes
- Edge cases
- Practical HTML/CSS generation
- Validation
- Maintainability
- Performance
- Security considerations
- Debugging and production considerations

This Python program is intentionally self-contained and uses only the Python
standard library. It teaches CSS concepts while also generating real HTML/CSS
files that can be opened in a web browser.

Run:
    python css_fundamentals.py
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import shutil
import tempfile
import webbrowser


# ============================================================================
# 1. INTRODUCTION
# ============================================================================

def print_title(title: str) -> None:
    """Print a consistent section heading."""
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def print_concept(name: str, explanation: str) -> None:
    """Display a concise educational concept."""
    print(f"\n{name}")
    print("-" * len(name))
    print(explanation)


def introduction() -> None:
    print_title("1. WHAT CSS IS")

    print_concept(
        "CSS",
        "CSS stands for Cascading Style Sheets. It is a stylesheet language "
        "used to describe how HTML elements should be presented in a browser."
    )

    print_concept(
        "HTML versus CSS",
        "HTML provides structure and meaning. CSS controls presentation. "
        "For example, an HTML heading can represent a page heading, while "
        "CSS can define its color, size, spacing, alignment, and typography."
    )

    print_concept(
        "Why CSS exists",
        "Separating structure from presentation allows the same HTML document "
        "to be styled differently without rewriting the document structure."
    )

    print(
        """
A simple mental model:

    HTML = What the content is
    CSS  = How the content looks
    JavaScript = How the page behaves

CSS commonly controls:

    - colors
    - fonts
    - text formatting
    - spacing
    - borders
    - backgrounds
    - dimensions
    - layouts
    - responsive behavior
    - visual states
    - animations and transitions

CSS does not replace HTML. CSS works by selecting elements in the HTML
document and assigning declarations to those elements.
"""
    )


# ============================================================================
# 2. BASIC CSS SYNTAX
# ============================================================================

def basic_syntax() -> None:
    print_title("2. CSS SYNTAX")

    print(
        """
The basic CSS rule has this structure:

    selector {
        property: value;
    }

Example:

    p {
        color: blue;
        font-size: 18px;
    }

The three major parts are:

    selector
        Identifies the HTML elements to which the rule applies.

    property
        Identifies the visual or behavioral characteristic being changed.

    value
        Specifies what the property should become.

A declaration consists of:

    property: value;

A CSS rule contains a selector and one or more declarations.
"""
    )

    rule = CSSRule(
        selector="p",
        declarations={
            "color": "blue",
            "font-size": "18px",
        },
    )

    print("Python representation of the CSS rule:")
    print(rule.to_css())

    print_concept(
        "Semicolon",
        "A semicolon normally separates declarations. The final declaration "
        "can technically omit it, but consistently using semicolons is the "
        "better practice because it prevents accidental syntax problems when "
        "another declaration is added later."
    )

    print_concept(
        "Curly braces",
        "Curly braces contain the declarations belonging to a CSS rule."
    )

    print_concept(
        "Colon",
        "A colon separates a property from its value."
    )


@dataclass
class CSSRule:
    """A small Python representation of a CSS rule."""

    selector: str
    declarations: dict[str, str]

    def to_css(self) -> str:
        lines = [f"{self.selector} {{"]

        for property_name, value in self.declarations.items():
            lines.append(f"    {property_name}: {value};")

        lines.append("}")
        return "\n".join(lines)


# ============================================================================
# 3. SELECTORS
# ============================================================================

def selectors() -> None:
    print_title("3. CSS SELECTORS")

    print(
        """
A selector determines which HTML elements a CSS rule targets.

Common selector categories include:

    Universal selector
        *

    Type selector
        p
        h1
        button

    Class selector
        .card
        .warning

    ID selector
        #header
        #main-title

    Attribute selector
        input[type="email"]
        a[target="_blank"]

    Descendant selector
        .card p

    Child selector
        .card > p

    Adjacent sibling selector
        h2 + p

    General sibling selector
        h2 ~ p

    Group selector
        h1, h2, h3

Pseudo-classes and pseudo-elements are also selectors:

    :hover
    :focus
    :first-child
    ::before
    ::after
"""
    )

    examples = {
        "Universal selector": "*",
        "Type selector": "p",
        "Class selector": ".card",
        "ID selector": "#main-title",
        "Attribute selector": 'input[type="email"]',
        "Descendant selector": ".card p",
        "Child selector": ".card > p",
        "Adjacent sibling selector": "h2 + p",
        "General sibling selector": "h2 ~ p",
        "Grouped selector": "h1, h2, h3",
        "Pseudo-class": "button:hover",
        "Pseudo-element": "p::first-letter",
    }

    for name, selector in examples.items():
        print(f"{name:30} {selector}")

    print(
        """
Important distinction:

    .card
        Selects every element whose class attribute contains "card".

    #card
        Selects the element whose ID is "card".

    div
        Selects every div element.

Classes are generally preferred for reusable styling. IDs have higher
specificity and are often better reserved for unique document identification
rather than general-purpose styling.
"""
    )


# ============================================================================
# 4. DECLARATIONS, PROPERTIES, AND VALUES
# ============================================================================

def declarations_properties_values() -> None:
    print_title("4. DECLARATIONS, PROPERTIES, AND VALUES")

    print(
        """
A declaration is a property-value pair.

Example:

    color: red;

Here:

    color = property
    red   = value

A rule can contain multiple declarations:

    .profile {
        color: #222;
        background-color: white;
        padding: 20px;
        border-radius: 8px;
    }

Properties describe what is being changed.

Examples:

    color
    background-color
    width
    height
    margin
    padding
    border
    font-size
    font-family
    display
    position

Values depend on the property.

Examples:

    color: red;
    color: #ff0000;
    color: rgb(255, 0, 0);

    width: 300px;
    width: 50%;
    width: 20rem;

    display: block;
    display: flex;
    display: grid;
"""
    )

    rule = CSSRule(
        selector=".profile",
        declarations={
            "color": "#222",
            "background-color": "white",
            "padding": "20px",
            "border-radius": "8px",
        },
    )

    print("Complete example:")
    print(rule.to_css())


# ============================================================================
# 5. COMMON CSS VALUE TYPES
# ============================================================================

def value_types() -> None:
    print_title("5. COMMON CSS VALUE TYPES")

    values = {
        "Keyword": "block",
        "Length": "20px",
        "Relative length": "2rem",
        "Percentage": "50%",
        "Color keyword": "red",
        "Hex color": "#3366ff",
        "RGB color": "rgb(51, 102, 255)",
        "RGBA color": "rgba(51, 102, 255, 0.5)",
        "HSL color": "hsl(220 100% 60%)",
        "Number": "1.5",
        "Integer": "400",
        "Function": "calc(100% - 20px)",
        "Variable": "var(--primary-color)",
    }

    for category, value in values.items():
        print(f"{category:22} {value}")

    print(
        """
Important units:

    px
        CSS pixel. Useful when a precise dimension is required.

    %
        Relative to another dimension or containing context.

    em
        Relative to the computed font size of the relevant element.

    rem
        Relative to the root element's font size.

    vw
        One percent of the viewport width.

    vh
        One percent of the viewport height.

Modern CSS also supports many other units and functions, but the units above
are fundamental to understanding CSS sizing.
"""
    )


# ============================================================================
# 6. THREE WAYS TO APPLY CSS
# ============================================================================

def css_application_methods() -> None:
    print_title("6. INLINE, INTERNAL, AND EXTERNAL CSS")

    print(
        """
INLINE CSS

CSS is placed directly in an HTML element using the style attribute.

Example:

    <p style="color: red;">Important text</p>

Advantages:
    - quick for very small experiments
    - directly attached to one element

Disadvantages:
    - difficult to maintain at scale
    - poor separation of concerns
    - difficult to reuse
    - can make HTML difficult to read

INTERNAL CSS

CSS is placed inside a style element in the HTML document.

Example:

    <style>
        p {
            color: blue;
        }
    </style>

Advantages:
    - useful for page-specific styles
    - no additional stylesheet request is necessary for the page

Disadvantages:
    - styles are less reusable across pages
    - HTML files can become large

EXTERNAL CSS

CSS is stored in a separate stylesheet.

Example HTML:

    <link rel="stylesheet" href="styles.css">

Example styles.css:

    p {
        color: green;
    }

Advantages:
    - reusable
    - maintainable
    - separates structure from presentation
    - suitable for multi-page websites

For production websites, external stylesheets are commonly the preferred
organization method.
"""
    )


# ============================================================================
# 7. CASCADE
# ============================================================================

def cascade() -> None:
    print_title("7. THE CASCADE")

    print(
        """
The word "cascading" describes how CSS resolves competing rules.

When several rules apply to the same element and property, the browser
determines which declaration wins.

Important factors include:

    1. Origin and importance
    2. Cascade layers
    3. Specificity
    4. Scope
    5. Source order

A simplified beginner model is:

    important rules
        ↓
    specificity
        ↓
    later rule when competing rules have equivalent priority

Example:

    p {
        color: blue;
    }

    p {
        color: red;
    }

The second declaration wins because both selectors have the same specificity
and the second rule appears later.

Avoid solving every conflict by adding !important. Excessive use of !important
can make a stylesheet difficult to reason about.
"""
    )


# ============================================================================
# 8. SPECIFICITY
# ============================================================================

def specificity() -> None:
    print_title("8. SPECIFICITY")

    print(
        """
Specificity is a mechanism used by CSS to determine which competing selector
has greater priority.

A useful conceptual hierarchy is:

    inline styles
        >
    ID selectors
        >
    class, attribute, and pseudo-class selectors
        >
    type selectors and pseudo-elements
        >
    universal selector

Example:

    p {
        color: blue;
    }

    .message {
        color: green;
    }

    #important-message {
        color: red;
    }

If one paragraph matches all three selectors, the ID selector normally has
greater specificity than the class and type selectors.

Specificity should not be treated as a reason to create unnecessarily complex
selectors. Low-complexity selectors are generally easier to maintain.
"""
    )

    print(
        """
A common specificity representation uses four conceptual components:

    inline, ID, class/attribute/pseudo-class, type/pseudo-element

Examples:

    p
        0-0-0-1

    .message
        0-0-1-0

    #message
        0-1-0-0

    #message .warning p
        0-1-1-1

This notation is useful for comparing selectors, although the complete CSS
cascade has additional rules beyond a simple numerical score.
"""
    )


# ============================================================================
# 9. INHERITANCE
# ============================================================================

def inheritance() -> None:
    print_title("9. INHERITANCE")

    print(
        """
Some CSS properties can inherit their computed value from a parent element.

For example:

    body {
        color: #222;
        font-family: Arial, sans-serif;
    }

A child paragraph often inherits color and font-family unless another rule
overrides them.

Not every property inherits.

Commonly inherited properties include:

    color
    font-family
    font-size in many normal document flows

Properties such as margin, padding, border, and width generally do not inherit.

Explicit inheritance keywords include:

    inherit
    initial
    unset
    revert
    revert-layer

Example:

    .child {
        color: inherit;
    }
"""
    )


# ============================================================================
# 10. COMMENTS
# ============================================================================

def comments() -> None:
    print_title("10. CSS COMMENTS")

    print(
        """
CSS comments use:

    /* comment */

Example:

    /* Main navigation */
    nav {
        display: flex;
    }

Comments are useful for explaining non-obvious design decisions and organizing
large stylesheets. Do not rely on comments to compensate for confusing naming
or unnecessarily complex CSS.
"""
    )


# ============================================================================
# 11. GROUPING AND REUSE
# ============================================================================

def grouping_and_reuse() -> None:
    print_title("11. GROUPING AND REUSABLE STYLES")

    print(
        """
Multiple selectors can share one rule:

    h1, h2, h3 {
        font-family: sans-serif;
    }

Classes are particularly useful for reusable styling:

    .button {
        padding: 10px 16px;
        border-radius: 6px;
    }

    .button-primary {
        background: navy;
        color: white;
    }

The same class can be applied to multiple elements.

This is one reason classes are central to scalable CSS architecture.
"""
    )


# ============================================================================
# 12. CSS CUSTOM PROPERTIES
# ============================================================================

def custom_properties() -> None:
    print_title("12. CSS CUSTOM PROPERTIES")

    print(
        """
CSS custom properties are variables defined using names beginning with --.

Example:

    :root {
        --primary-color: #2457d6;
        --spacing-unit: 8px;
    }

They can be used with var():

    .button {
        background-color: var(--primary-color);
        padding: var(--spacing-unit);
    }

Fallback values can be supplied:

    color: var(--missing-color, black);

Custom properties improve consistency because repeated design values can be
centralized.
"""
    )

    css = """
:root {
    --primary-color: #2457d6;
    --spacing-unit: 8px;
}

.button {
    background-color: var(--primary-color);
    padding: calc(var(--spacing-unit) * 2);
}
""".strip()

    print(css)


# ============================================================================
# 13. COMMON PROPERTIES
# ============================================================================

def common_properties() -> None:
    print_title("13. FUNDAMENTAL CSS PROPERTIES")

    property_groups = {
        "Text": [
            "color",
            "font-family",
            "font-size",
            "font-weight",
            "line-height",
            "text-align",
            "text-decoration",
        ],
        "Background": [
            "background-color",
            "background-image",
            "background-size",
            "background-position",
        ],
        "Box model": [
            "width",
            "height",
            "margin",
            "padding",
            "border",
            "box-sizing",
        ],
        "Display": [
            "display",
            "visibility",
            "overflow",
        ],
        "Positioning": [
            "position",
            "top",
            "right",
            "bottom",
            "left",
            "z-index",
        ],
    }

    for group, properties in property_groups.items():
        print(f"\n{group}:")
        for property_name in properties:
            print(f"    {property_name}")


# ============================================================================
# 14. CSS BOX MODEL
# ============================================================================

def box_model() -> None:
    print_title("14. THE CSS BOX MODEL")

    print(
        """
Every normal HTML element can be understood using the box model:

    content
        ↓
    padding
        ↓
    border
        ↓
    margin

Example:

    .card {
        width: 300px;
        padding: 20px;
        border: 1px solid #ccc;
        margin: 30px;
    }

A common production practice is:

    *,
    *::before,
    *::after {
        box-sizing: border-box;
    }

With border-box, the declared width includes the content, padding, and border
within the element's sizing calculation.

This often makes layout calculations easier to reason about.
"""
    )


# ============================================================================
# 15. DISPLAY BASICS
# ============================================================================

def display_basics() -> None:
    print_title("15. DISPLAY BASICS")

    print(
        """
Common display values include:

    block
        Usually begins on a new line and can occupy available width.

    inline
        Flows within text and generally does not accept width and height in
        the same way a block-level box does.

    inline-block
        Combines inline flow with a box that can accept dimensions.

    none
        Removes the element from normal layout.

    flex
        Creates a flex formatting context.

    grid
        Creates a grid formatting context.

Modern layouts commonly use Flexbox and Grid for structured layout rather
than relying on large numbers of positional offsets.
"""
    )


# ============================================================================
# 16. PSEUDO-CLASSES
# ============================================================================

def pseudo_classes() -> None:
    print_title("16. PSEUDO-CLASSES")

    print(
        """
A pseudo-class represents a state or structural condition.

Examples:

    :hover
        Pointer is positioned over an element.

    :focus
        Element has focus.

    :focus-visible
        Element has focus and the browser determines that a visible focus
        indication is appropriate.

    :active
        Element is being activated.

    :disabled
        Form control is disabled.

    :checked
        Checkbox or radio control is checked.

    :first-child
        Element is the first child of its parent.

    :nth-child(...)
        Selects elements according to a child-position pattern.

Accessibility-sensitive interfaces should provide clear focus styling rather
than removing focus indicators without replacement.
"""
    )


# ============================================================================
# 17. PSEUDO-ELEMENTS
# ============================================================================

def pseudo_elements() -> None:
    print_title("17. PSEUDO-ELEMENTS")

    print(
        """
Pseudo-elements represent a conceptual part of an element.

Examples:

    ::before
    ::after
    ::first-letter
    ::first-line
    ::selection

Example:

    .required::after {
        content: " *";
    }

Generated content is useful for decorative presentation, but essential
information should generally exist in meaningful HTML rather than only in CSS
generated content.
"""
    )


# ============================================================================
# 18. ATTRIBUTE SELECTORS
# ============================================================================

def attribute_selectors() -> None:
    print_title("18. ATTRIBUTE SELECTORS")

    print(
        """
Attribute selectors target elements according to attributes.

Examples:

    [disabled]
        Any element with a disabled attribute.

    input[type="email"]
        Email input controls.

    a[target="_blank"]
        Links whose target attribute is _blank.

Other attribute operators include:

    [attr^="value"]   starts with
    [attr$="value"]   ends with
    [attr*="value"]   contains
    [attr~="value"]   contains a whitespace-separated word
    [attr|="value"]   exact value or value followed by a hyphen
"""
    )


# ============================================================================
# 19. COMBINATORS
# ============================================================================

def combinators() -> None:
    print_title("19. SELECTOR COMBINATORS")

    combinations = {
        "Descendant": ".card p",
        "Child": ".card > p",
        "Adjacent sibling": "h2 + p",
        "General sibling": "h2 ~ p",
    }

    for description, selector in combinations.items():
        print(f"{description:20} {selector}")

    print(
        """
Descendant:
    Matches paragraphs at any descendant level inside .card.

Child:
    Matches paragraphs that are direct children of .card.

Adjacent sibling:
    Matches a p immediately following an h2.

General sibling:
    Matches p elements appearing later among the siblings of h2.
"""
    )


# ============================================================================
# 20. INLINE STYLE SPECIFICITY
# ============================================================================

def inline_specificity() -> None:
    print_title("20. INLINE CSS AND SPECIFICITY")

    print(
        """
An inline style is written directly on an HTML element:

    <p style="color: red;">Text</p>

Inline declarations normally have higher author-level specificity than
ordinary ID, class, and type selectors.

This does not mean inline styles are always preferable. High priority can
make later maintenance harder.

A stylesheet might contain:

    p {
        color: blue;
    }

while the element contains:

    style="color: red"

The inline declaration normally wins in this ordinary comparison.
"""
    )


# ============================================================================
# 21. CSS VALIDATION
# ============================================================================

CSS_PROPERTY_PATTERN = re.compile(
    r"^[a-zA-Z][a-zA-Z0-9-]*$"
)

CSS_VALUE_PATTERN = re.compile(
    r"^[^\{\};]+$"
)


def validate_css_rule(rule: CSSRule) -> tuple[bool, list[str]]:
    """
    Perform a deliberately lightweight CSS validation.

    This is not a replacement for a browser's CSS parser. It demonstrates
    how structured validation can catch obvious mistakes before output.
    """
    errors: list[str] = []

    if not rule.selector.strip():
        errors.append("Selector cannot be empty.")

    if "{" in rule.selector or "}" in rule.selector:
        errors.append("Selector contains an unexpected brace.")

    for property_name, value in rule.declarations.items():
        if not CSS_PROPERTY_PATTERN.fullmatch(property_name):
            errors.append(
                f"Invalid property name: {property_name!r}"
            )

        if not value.strip():
            errors.append(
                f"Empty value for property: {property_name!r}"
            )

        if not CSS_VALUE_PATTERN.fullmatch(value.strip()):
            errors.append(
                f"Suspicious value for property: {property_name!r}"
            )

    return not errors, errors


def validation_demo() -> None:
    print_title("21. BASIC CSS VALIDATION WITH PYTHON")

    valid_rule = CSSRule(
        selector=".notice",
        declarations={
            "color": "white",
            "background-color": "#2457d6",
            "padding": "12px",
        },
    )

    invalid_rule = CSSRule(
        selector="",
        declarations={
            "bad property": "",
            "color": "red; }",
        },
    )

    for name, rule in [
        ("Valid rule", valid_rule),
        ("Invalid rule", invalid_rule),
    ]:
        valid, errors = validate_css_rule(rule)
        print(f"\n{name}: {'VALID' if valid else 'INVALID'}")

        if errors:
            for error in errors:
                print(f"  - {error}")


# ============================================================================
# 22. BUILDING CSS WITH PYTHON
# ============================================================================

def build_stylesheet() -> str:
    """
    Build a realistic external stylesheet.

    The stylesheet demonstrates:
    - element selectors
    - class selectors
    - descendant selectors
    - pseudo-classes
    - custom properties
    - box sizing
    - responsive media query
    """
    return """
:root {
    --primary-color: #2457d6;
    --primary-dark: #173b96;
    --page-background: #f4f7fb;
    --surface: #ffffff;
    --text-color: #202735;
    --muted-text: #64748b;
    --border-color: #d7deea;
    --spacing-unit: 8px;
}

*,
*::before,
*::after {
    box-sizing: border-box;
}

body {
    margin: 0;
    background-color: var(--page-background);
    color: var(--text-color);
    font-family: Arial, sans-serif;
    line-height: 1.6;
}

.page {
    width: min(1100px, calc(100% - 32px));
    margin: 0 auto;
    padding: calc(var(--spacing-unit) * 4) 0;
}

.hero {
    background-color: var(--surface);
    border: 1px solid var(--border-color);
    border-radius: 14px;
    padding: calc(var(--spacing-unit) * 4);
    margin-bottom: calc(var(--spacing-unit) * 3);
}

.hero h1 {
    margin-top: 0;
}

.hero p {
    color: var(--muted-text);
}

.card-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: calc(var(--spacing-unit) * 2);
}

.card {
    background-color: var(--surface);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: calc(var(--spacing-unit) * 3);
}

.card h2 {
    margin-top: 0;
}

.button {
    display: inline-block;
    padding: 10px 16px;
    border: 0;
    border-radius: 8px;
    background-color: var(--primary-color);
    color: white;
    text-decoration: none;
    cursor: pointer;
}

.button:hover {
    background-color: var(--primary-dark);
}

.button:focus-visible {
    outline: 3px solid #9db4ff;
    outline-offset: 2px;
}

.notice {
    margin-top: calc(var(--spacing-unit) * 3);
    padding: calc(var(--spacing-unit) * 2);
    border-left: 4px solid var(--primary-color);
    background-color: #eaf0ff;
}

@media (max-width: 800px) {
    .card-grid {
        grid-template-columns: 1fr;
    }
}
""".strip()


def build_html() -> str:
    """
    Build an HTML document demonstrating external, internal, and inline CSS.

    The internal stylesheet and inline style are intentionally included for
    teaching. The external stylesheet is linked through styles.css.
    """
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CSS Fundamentals Demonstration</title>

    <link rel="stylesheet" href="styles.css">

    <style>
        .internal-example {
            border: 2px dashed #7c3aed;
            padding: 16px;
            margin-top: 16px;
        }

        .internal-example strong {
            color: #7c3aed;
        }
    </style>
</head>
<body>
    <main class="page">
        <section class="hero">
            <h1>CSS Fundamentals</h1>
            <p>
                This page demonstrates real CSS rules generated by the
                accompanying Python study script.
            </p>

            <p
                class="notice"
                style="font-weight: 700;"
            >
                This paragraph contains an inline CSS declaration.
            </p>

            <div class="internal-example">
                <strong>Internal CSS:</strong>
                this box is styled by the style element in the HTML document.
            </div>
        </section>

        <section class="card-grid">
            <article class="card">
                <h2>Selectors</h2>
                <p>
                    Classes, element selectors, descendant selectors, and
                    pseudo-classes can target elements.
                </p>
                <a class="button" href="#selectors">Read example</a>
            </article>

            <article class="card">
                <h2>Properties</h2>
                <p>
                    Properties such as color, padding, margin, display, and
                    border describe what should change.
                </p>
                <a class="button" href="#properties">Read example</a>
            </article>

            <article class="card">
                <h2>Values</h2>
                <p>
                    Values can be keywords, numbers, lengths, percentages,
                    colors, functions, or custom properties.
                </p>
                <a class="button" href="#values">Read example</a>
            </article>
        </section>
    </main>
</body>
</html>
""".strip()


# ============================================================================
# 23. CREATE A REAL CSS PROJECT
# ============================================================================

def create_demo_project() -> Path:
    """
    Create a temporary demonstration project containing HTML and external CSS.
    """
    project_directory = Path(
        tempfile.mkdtemp(prefix="css_fundamentals_")
    )

    html_path = project_directory / "index.html"
    css_path = project_directory / "styles.css"

    html_path.write_text(
        build_html(),
        encoding="utf-8",
    )

    css_path.write_text(
        build_stylesheet(),
        encoding="utf-8",
    )

    return project_directory


def demo_project() -> None:
    print_title("22. COMPLETE HTML + EXTERNAL CSS DEMONSTRATION")

    project_directory = create_demo_project()

    print(f"Created demonstration project:")
    print(f"    {project_directory}")
    print(f"    {project_directory / 'index.html'}")
    print(f"    {project_directory / 'styles.css'}")

    print(
        """
The generated page contains:

    External CSS
        styles.css is linked with a link element.

    Internal CSS
        A style element inside index.html styles .internal-example.

    Inline CSS
        One paragraph uses the style attribute.

This demonstrates the three fundamental ways CSS can be attached to HTML.
"""
    )

    html_path = project_directory / "index.html"

    try:
        webbrowser.open(html_path.resolve().as_uri())
        print("The demonstration page was requested from the default browser.")
    except Exception as error:
        print(f"Browser opening was unavailable: {error}")


# ============================================================================
# 24. CSS COMMENTS AND FORMATTING
# ============================================================================

def formatting_best_practices() -> None:
    print_title("23. CSS FORMATTING AND MAINTAINABILITY")

    print(
        """
Prefer consistent formatting:

    .card {
        padding: 20px;
        border: 1px solid #ddd;
        background-color: white;
    }

Useful practices:

    - use meaningful class names
    - group related declarations
    - keep indentation consistent
    - avoid unnecessarily deep selectors
    - avoid duplicated declarations
    - prefer reusable classes
    - keep specificity manageable
    - organize styles logically
    - use custom properties for repeated design values
    - preserve accessible focus states
    - avoid unexplained !important declarations

Poor naming:

    .blue-box-2

Better when the element represents a reusable component:

    .profile-card

The best naming strategy describes the role or meaning of the component rather
than only its current visual appearance.
"""
    )


# ============================================================================
# 25. COMMON MISTAKES
# ============================================================================

def common_mistakes() -> None:
    print_title("24. COMMON CSS MISTAKES")

    mistakes = {
        "Missing semicolon":
            "color: red  should normally be written as  color: red;",
        "Missing colon":
            "color red  should be  color: red;",
        "Wrong selector":
            ".button targets a class, while button targets the element.",
        "Wrong unit":
            "20 px is invalid because CSS units cannot contain that space.",
        "Invalid property":
            "backgroundcolour is not the standard property name; use background-color.",
        "Case assumptions":
            "HTML/CSS matching behavior has specific rules and should not be assumed blindly.",
        "Confusing margin and padding":
            "Margin is outside the border; padding is inside the border.",
        "Excessive !important":
            "It can make the cascade difficult to control.",
        "Overly specific selectors":
            "Deep selectors create fragile dependencies and specificity conflicts.",
        "Removing focus":
            "outline: none without an accessible replacement harms keyboard navigation.",
        "Using CSS for meaning":
            "Important content should not exist only as decorative generated content.",
        "Inline-style overuse":
            "Large applications become harder to maintain when presentation is embedded throughout HTML.",
    }

    for mistake, explanation in mistakes.items():
        print(f"\n{mistake}")
        print(f"    {explanation}")


# ============================================================================
# 26. EDGE CASES
# ============================================================================

def edge_cases() -> None:
    print_title("25. CSS EDGE CASES AND SUBTLE BEHAVIOR")

    print(
        """
1. Unknown properties

Browsers generally ignore declarations they do not understand.

Example:

    p {
        imaginary-property: 10px;
        color: blue;
    }

The invalid declaration does not normally prevent the valid color declaration
from being processed.

2. Invalid values

If a value is invalid for a property, that declaration may be discarded.

3. Multiple declarations of the same property

Example:

    p {
        color: blue;
        color: red;
    }

The later declaration wins when both declarations have otherwise equivalent
cascade priority.

4. Shorthand properties

Example:

    margin: 10px 20px;

This represents top/bottom and left/right margins.

5. Longhand properties

The equivalent conceptual properties include:

    margin-top
    margin-right
    margin-bottom
    margin-left

6. CSS variables can contain complex values

A custom property stores tokens rather than being limited to a simple number.

7. calc()

CSS can perform calculations:

    width: calc(100% - 40px);

8. Missing custom properties

Using:

    color: var(--missing);

can make the declaration invalid at computed-value time unless an appropriate
fallback is supplied.

Safer:

    color: var(--missing, black);

9. Specificity conflicts

Adding a class may not override a more specific selector. The complete cascade
must be considered.

10. Source order

When competing declarations have the same relevant priority and specificity,
the later declaration can win.
"""
    )


# ============================================================================
# 27. SECURITY
# ============================================================================

def security_considerations() -> None:
    print_title("26. CSS SECURITY CONSIDERATIONS")

    print(
        """
CSS is primarily a presentation language, but production systems still need
security awareness.

1. Untrusted CSS

Do not blindly inject user-controlled text into a stylesheet or style
attribute.

2. HTML injection

A value intended to be displayed as text must be safely handled by the
application generating HTML. CSS does not replace HTML output encoding.

3. External resources

CSS can reference external resources in appropriate contexts. Production
applications should understand their content security policy and resource
loading rules.

4. Privacy-sensitive selectors

Modern browsers have restrictions around certain information-leaking CSS
techniques. Applications should not rely on CSS as a security boundary.

5. CSS is not authorization

Hiding an element with:

    display: none;

does not protect the underlying data. Sensitive data must be protected on the
server and in application logic.

6. CSS injection

Applications that allow users to customize CSS should sanitize and constrain
the accepted syntax according to the application's security model.

7. Content Security Policy

A production application may use CSP to restrict unsafe resource and style
sources. CSP configuration must be designed together with the application's
actual rendering architecture.
"""
    )


# ============================================================================
# 28. PERFORMANCE
# ============================================================================

def performance_considerations() -> None:
    print_title("27. CSS PERFORMANCE")

    print(
        """
CSS performance depends on stylesheet size, selector complexity, layout
changes, rendering behavior, and resource loading.

Useful practices include:

    - remove unused CSS in production builds
    - avoid unnecessary duplication
    - avoid extremely complex selectors
    - reuse shared classes
    - keep critical rendering requirements in mind
    - minimize unnecessary style recalculation
    - avoid excessive DOM complexity
    - compress production CSS where appropriate

Selector matching is only one part of rendering performance. Modern browsers
are highly optimized, so maintainability and correctness should generally not
be sacrificed for microscopic selector-level optimizations.

Large visual effects such as filters, expensive shadows, and animations can
also affect rendering depending on the device and implementation.
"""
    )


# ============================================================================
# 29. DEBUGGING
# ============================================================================

def debugging() -> None:
    print_title("28. DEBUGGING CSS")

    print(
        """
A systematic debugging process is more reliable than randomly changing
properties.

Step 1:
    Confirm that the stylesheet is actually loaded.

Step 2:
    Confirm that the selector matches the intended element.

Step 3:
    Inspect the element in browser developer tools.

Step 4:
    Check the Styles and Computed panels.

Step 5:
    Look for crossed-out declarations.

Step 6:
    Investigate specificity and source order.

Step 7:
    Check inheritance.

Step 8:
    Check whether the value is valid for the property.

Step 9:
    Inspect the box model.

Step 10:
    Test responsive behavior at different viewport sizes.

Common symptom:

    "My color is not changing."

Possible causes:

    - stylesheet not loaded
    - selector does not match
    - declaration contains a syntax error
    - another rule wins the cascade
    - inline style overrides the stylesheet
    - inherited value is being misunderstood
    - browser state or cache is involved
"""
    )


# ============================================================================
# 30. ACCESSIBILITY
# ============================================================================

def accessibility() -> None:
    print_title("29. CSS AND ACCESSIBILITY")

    print(
        """
CSS should support accessible interfaces.

Important considerations:

    Focus
        Keyboard users need a visible focus indication.

    Contrast
        Text and important interface elements need sufficient visual contrast.

    Text scaling
        Avoid layouts that break when text becomes larger.

    Motion
        Respect user preferences for reduced motion when animations are used.

    Content order
        Visual rearrangement should not create a confusing experience when
        compared with the semantic document order.

    Hidden content
        display: none removes content from normal rendering and can affect
        accessibility-tree exposure depending on the mechanism used.

    Color
        Do not communicate essential information through color alone.
"""
    )


# ============================================================================
# 31. RESPONSIVE CSS
# ============================================================================

def responsive_css() -> None:
    print_title("30. RESPONSIVE CSS")

    print(
        """
Responsive CSS allows layouts to adapt to different viewport sizes.

A media query has the general structure:

    @media (condition) {
        selector {
            property: value;
        }
    }

Example:

    @media (max-width: 800px) {
        .card-grid {
            grid-template-columns: 1fr;
        }
    }

The demonstration stylesheet generated by this script uses exactly this
pattern to change a three-column card layout into a single-column layout on
narrower screens.
"""
    )


# ============================================================================
# 32. CSS ARCHITECTURE
# ============================================================================

def architecture() -> None:
    print_title("31. CSS DESIGN AND ARCHITECTURE")

    print(
        """
For small pages, a single stylesheet can be sufficient.

For larger applications, styles often benefit from logical organization such
as:

    base
        global defaults and typography

    layout
        page-level structure

    components
        buttons, cards, forms, navigation

    utilities
        small reusable helper classes

    themes
        colors and design tokens

The exact architecture depends on project size and team conventions.

Avoid creating a complicated architecture for a tiny website. Complexity should
solve an actual maintenance problem.
"""
    )


# ============================================================================
# 33. COMPARISON TABLE
# ============================================================================

def comparison() -> None:
    print_title("32. IMPORTANT COMPARISONS")

    rows = [
        (
            "Inline CSS",
            "style attribute",
            "One element",
            "Low reuse, high local priority",
        ),
        (
            "Internal CSS",
            "style element",
            "One document",
            "Useful for page-specific rules",
        ),
        (
            "External CSS",
            "separate .css file",
            "Multiple documents",
            "Highly reusable and maintainable",
        ),
        (
            "Class selector",
            ".component",
            "Many matching elements",
            "Strong general-purpose choice",
        ),
        (
            "ID selector",
            "#unique",
            "Usually one element",
            "Higher specificity",
        ),
        (
            "Type selector",
            "button",
            "Elements of that type",
            "Low specificity",
        ),
    ]

    headers = (
        "Concept",
        "Syntax",
        "Typical scope",
        "Important characteristic",
    )

    widths = [18, 24, 25, 35]

    print(
        f"{headers[0]:<{widths[0]}} "
        f"{headers[1]:<{widths[1]}} "
        f"{headers[2]:<{widths[2]}} "
        f"{headers[3]}"
    )

    print("-" * sum(widths))

    for row in rows:
        print(
            f"{row[0]:<{widths[0]}} "
            f"{row[1]:<{widths[1]}} "
            f"{row[2]:<{widths[2]}} "
            f"{row[3]}"
        )


# ============================================================================
# 34. PRACTICAL COMPLETE EXAMPLE
# ============================================================================

def complete_example() -> None:
    print_title("33. COMPLETE CSS RULE EXAMPLE")

    example = CSSRule(
        selector=".product-card",
        declarations={
            "background-color": "white",
            "color": "#202735",
            "width": "300px",
            "padding": "24px",
            "margin": "16px",
            "border": "1px solid #d7deea",
            "border-radius": "12px",
            "box-sizing": "border-box",
        },
    )

    valid, errors = validate_css_rule(example)

    print(example.to_css())
    print(f"\nValidation result: {'PASS' if valid else 'FAIL'}")

    if errors:
        for error in errors:
            print(error)


# ============================================================================
# 35. SIMPLE CSS PARSER FOR EDUCATIONAL PURPOSES
# ============================================================================

def parse_simple_css(css_text: str) -> list[CSSRule]:
    """
    Parse a deliberately restricted subset of CSS.

    This educational parser handles simple rules such as:

        p {
            color: red;
            font-size: 16px;
        }

    It is not a standards-compliant CSS parser. Real CSS supports nested
    constructs, comments, escaped identifiers, custom syntax, functions,
    media queries, layers, at-rules, and many other features.
    """
    rules: list[CSSRule] = []

    pattern = re.compile(
        r"([^{}]+)\{([^{}]*)\}",
        flags=re.MULTILINE | re.DOTALL,
    )

    for selector_text, declaration_text in pattern.findall(css_text):
        selector = selector_text.strip()
        declarations: dict[str, str] = {}

        for declaration in declaration_text.split(";"):
            declaration = declaration.strip()

            if not declaration or ":" not in declaration:
                continue

            property_name, value = declaration.split(":", 1)

            declarations[property_name.strip()] = value.strip()

        rules.append(
            CSSRule(
                selector=selector,
                declarations=declarations,
            )
        )

    return rules


def parser_demo() -> None:
    print_title("34. EDUCATIONAL CSS PARSER")

    css = """
.card {
    color: #222;
    padding: 20px;
}

.button {
    background-color: blue;
    color: white;
}
""".strip()

    print("Input CSS:")
    print(css)

    rules = parse_simple_css(css)

    print("\nParsed rules:")

    for rule in rules:
        print()
        print(rule.to_css())


# ============================================================================
# 36. TESTING
# ============================================================================

def run_tests() -> None:
    print_title("35. AUTOMATED TESTS")

    valid_rule = CSSRule(
        selector=".button",
        declarations={
            "color": "white",
            "background-color": "blue",
        },
    )

    valid, errors = validate_css_rule(valid_rule)

    assert valid, f"Expected valid CSS rule: {errors}"
    assert ".button" in valid_rule.to_css()
    assert "color: white;" in valid_rule.to_css()

    parsed = parse_simple_css(
        ".card { color: red; padding: 10px; }"
    )

    assert len(parsed) == 1
    assert parsed[0].selector == ".card"
    assert parsed[0].declarations["color"] == "red"
    assert parsed[0].declarations["padding"] == "10px"

    invalid_rule = CSSRule(
        selector="",
        declarations={
            "bad property": "10px",
        },
    )

    valid, errors = validate_css_rule(invalid_rule)

    assert not valid
    assert errors

    print("All educational tests passed.")


# ============================================================================
# 37. PRODUCTION CONSIDERATIONS
# ============================================================================

def production_considerations() -> None:
    print_title("36. PRODUCTION CSS CONSIDERATIONS")

    print(
        """
A production stylesheet should be evaluated from several perspectives.

Correctness
    Does the styling behave correctly across supported browsers and viewport
    sizes?

Maintainability
    Can another developer understand and safely modify the rules?

Accessibility
    Are keyboard navigation, focus, contrast, text scaling, and reduced-motion
    needs considered?

Performance
    Is unused CSS removed? Are resource sizes reasonable? Are expensive visual
    effects used deliberately?

Consistency
    Are repeated values centralized through a sensible design-token strategy?

Specificity
    Can components be overridden without escalating into a specificity war?

Browser compatibility
    Are the selected CSS features supported by the browsers that the
    application promises to support?

Security
    Are user-controlled values prevented from becoming unsafe CSS or HTML?

Deployment
    Are CSS assets correctly served, cached, compressed, and versioned?

A good stylesheet is not merely visually attractive. It should remain
predictable as the application grows.
"""
    )


# ============================================================================
# 38. FINAL HANDS-ON EXERCISE
# ============================================================================

def hands_on_example() -> None:
    print_title("37. HANDS-ON CSS CONSTRUCTION")

    html = """<article class="profile">
    <h2>Developer Profile</h2>
    <p class="role">Frontend Developer</p>
    <button class="button">Contact</button>
</article>"""

    css = """
.profile {
    width: min(100%, 360px);
    padding: 24px;
    background-color: white;
    color: #202735;
    border: 1px solid #d7deea;
    border-radius: 12px;
}

.profile h2 {
    margin-top: 0;
}

.profile .role {
    color: #64748b;
}

.profile .button {
    padding: 10px 16px;
    background-color: #2457d6;
    color: white;
    border: 0;
    border-radius: 8px;
}
""".strip()

    print("HTML:")
    print(html)

    print("\nCSS:")
    print(css)

    print(
        """
Identify the components:

    .profile
        Class selector targeting the article.

    width
        Property.

    min(100%, 360px)
        Function-based value.

    padding
        Property controlling internal spacing.

    background-color
        Property controlling the background.

    #202735
        Hexadecimal color value.

    .profile h2
        Descendant selector.

    .button
        Reusable class selector.

The example demonstrates how selectors, declarations, properties, and values
combine to create a practical component.
"""
    )


# ============================================================================
# 39. CLEANUP
# ============================================================================

def cleanup_project(project_directory: Path) -> None:
    """
    Remove the temporary demonstration directory.

    The function is kept separate so the user can easily modify the script to
    preserve the generated project instead.
    """
    try:
        shutil.rmtree(project_directory)
        print(f"Removed temporary project: {project_directory}")
    except OSError as error:
        print(f"Could not remove temporary project: {error}")


# ============================================================================
# 40. STUDY CHECKLIST
# ============================================================================

def study_checklist() -> None:
    print_title("38. CSS FUNDAMENTALS CHECKLIST")

    checklist = [
        "Understand the purpose of CSS.",
        "Recognize a CSS rule.",
        "Identify a selector.",
        "Identify a declaration.",
        "Identify a property.",
        "Identify a value.",
        "Use type selectors.",
        "Use class selectors.",
        "Understand ID selectors.",
        "Understand attribute selectors.",
        "Use descendant and child combinators.",
        "Understand pseudo-classes.",
        "Understand pseudo-elements.",
        "Understand the cascade.",
        "Understand specificity.",
        "Understand inheritance.",
        "Understand the box model.",
        "Distinguish margin from padding.",
        "Understand inline CSS.",
        "Understand internal CSS.",
        "Understand external CSS.",
        "Use CSS custom properties.",
        "Use media queries.",
        "Debug CSS using browser developer tools.",
        "Consider accessibility.",
        "Consider performance.",
        "Avoid unnecessary specificity.",
        "Use maintainable class names.",
        "Understand why CSS is not a security boundary.",
    ]

    for number, item in enumerate(checklist, start=1):
        print(f"[ ] {number:02}. {item}")


# ============================================================================
# 41. MAIN PROGRAM
# ============================================================================

def main() -> None:
    """Run the complete CSS fundamentals course."""
    introduction()
    basic_syntax()
    selectors()
    declarations_properties_values()
    value_types()
    css_application_methods()
    cascade()
    specificity()
    inheritance()
    comments()
    grouping_and_reuse()
    custom_properties()
    common_properties()
    box_model()
    display_basics()
    pseudo_classes()
    pseudo_elements()
    attribute_selectors()
    combinators()
    inline_specificity()
    validation_demo()
    formatting_best_practices()
    common_mistakes()
    edge_cases()
    security_considerations()
    performance_considerations()
    debugging()
    accessibility()
    responsive_css()
    architecture()
    comparison()
    complete_example()
    parser_demo()
    run_tests()
    production_considerations()
    hands_on_example()
    study_checklist()

    print_title("39. OPTIONAL BROWSER DEMONSTRATION")

    project_directory = create_demo_project()

    print(
        f"""
A complete browser demonstration has been created at:

    {project_directory}

Files:

    index.html
    styles.css

The project demonstrates all three CSS application methods:

    1. External CSS through styles.css
    2. Internal CSS through a style element
    3. Inline CSS through a style attribute
"""
    )

    try:
        webbrowser.open(
            (project_directory / "index.html").resolve().as_uri()
        )
        print("The demonstration page was opened using the default browser.")
    except Exception as error:
        print(f"Browser launch failed: {error}")

    print(
        """
The temporary project is intentionally left in place so that the generated
HTML and CSS can be inspected and modified manually.

To remove it after experimentation, delete the directory shown above.
"""
    )


if __name__ == "__main__":
    main()
