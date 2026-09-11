"""
HTML Accessibility: WCAG, Semantic Navigation, Labels, Keyboard Accessibility,
ARIA Basics, and Screen Readers

A self-contained study script for learning web accessibility from beginner
through advanced concepts.

The examples are represented as HTML strings and analyzed with Python so that
the file remains a single executable study resource without requiring a browser
or external packages.

Run:
    python html_accessibility.py
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple


# =============================================================================
# 1. BASIC TERMINOLOGY
# =============================================================================

def section(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def explain(term: str, definition: str) -> None:
    print(f"\n{term}")
    print("-" * len(term))
    print(definition)


def show_html(label: str, source: str) -> None:
    print(f"\n{label}")
    print("-" * len(label))
    print(source.strip())


def demo_output(label: str, value: object) -> None:
    print(f"\n{label}: {value}")


def beginner_terminology() -> None:
    section("1. Accessibility fundamentals")

    terms = {
        "Accessibility (a11y)":
            "The practice of designing websites and applications so that "
            "people with different abilities can perceive, understand, "
            "navigate, interact with, and contribute to digital content.",
        "Assistive technology":
            "Software or hardware that helps a person interact with a "
            "computer. Examples include screen readers, screen magnifiers, "
            "speech recognition software, and alternative input devices.",
        "Screen reader":
            "Software that converts relevant interface information into "
            "speech or refreshable Braille. It generally works from the "
            "browser's accessibility tree rather than simply reading raw "
            "source code from top to bottom.",
        "Keyboard accessibility":
            "The ability to operate interactive functionality using a "
            "keyboard or keyboard-like input without requiring a mouse.",
        "Semantic HTML":
            "Using HTML elements according to their meaning and intended "
            "purpose, such as nav, main, button, form, label, and heading.",
        "ARIA":
            "Accessible Rich Internet Applications. WAI-ARIA provides "
            "attributes that can communicate roles, states, and properties "
            "to assistive technologies when native HTML semantics are "
            "insufficient.",
        "WCAG":
            "Web Content Accessibility Guidelines, a technical standard "
            "for improving the accessibility of web content.",
    }

    for term, definition in terms.items():
        explain(term, definition)


# =============================================================================
# 2. THE WCAG PRINCIPLES
# =============================================================================

@dataclass
class WCAGPrinciple:
    name: str
    abbreviation: str
    meaning: str
    examples: List[str]


WCAG_PRINCIPLES = [
    WCAGPrinciple(
        "Perceivable",
        "P",
        "Information and user-interface components must be presented in "
        "ways users can perceive.",
        [
            "Provide text alternatives for meaningful images.",
            "Provide captions for relevant prerecorded video.",
            "Maintain sufficient color contrast.",
            "Do not communicate essential information through color alone.",
        ],
    ),
    WCAGPrinciple(
        "Operable",
        "O",
        "Users must be able to operate the interface and navigation.",
        [
            "Make functionality keyboard accessible.",
            "Provide visible keyboard focus.",
            "Avoid interactions that trap keyboard focus.",
            "Give users enough time to read and operate content.",
        ],
    ),
    WCAGPrinciple(
        "Understandable",
        "U",
        "Information and interface operation should be understandable.",
        [
            "Use clear labels.",
            "Keep navigation consistent.",
            "Identify input errors clearly.",
            "Provide instructions before complex form input.",
        ],
    ),
    WCAGPrinciple(
        "Robust",
        "R",
        "Content should remain interpretable by a broad range of user "
        "agents and assistive technologies.",
        [
            "Use valid, meaningful HTML.",
            "Expose appropriate semantics.",
            "Use ARIA according to its intended patterns.",
            "Keep custom widgets compatible with accessibility APIs.",
        ],
    ),
]


def demonstrate_wcag() -> None:
    section("2. WCAG and the POUR model")

    print(
        "WCAG organizes accessibility guidance around four principles, "
        "commonly remembered as POUR:"
    )

    for principle in WCAG_PRINCIPLES:
        print(f"\n{principle.name} ({principle.abbreviation})")
        print(f"Meaning: {principle.meaning}")
        for example in principle.examples:
            print(f"  - {example}")

    print(
        "\nWCAG conformance levels are commonly described as A, AA, and AAA. "
        "A represents the minimum level, AA contains additional requirements, "
        "and AAA represents a more demanding level. A particular legal or "
        "organizational requirement may specify which level applies."
    )


# =============================================================================
# 3. SEMANTIC HTML
# =============================================================================

SEMANTIC_ELEMENTS = {
    "header": "Introductory or navigational content for a page or section.",
    "nav": "A section containing major navigation links.",
    "main": "The dominant, unique content of the document.",
    "section": "A thematic grouping of content, normally with a heading.",
    "article": "A self-contained composition that could stand independently.",
    "aside": "Content indirectly related to the surrounding content.",
    "footer": "Footer information for a page or section.",
    "button": "An interactive control that performs an action.",
    "a": "A hyperlink to another resource or location.",
    "form": "A region containing controls for submitting or processing input.",
    "label": "A label associated with a form control.",
    "fieldset": "Groups related form controls.",
    "legend": "Provides a caption for a fieldset.",
    "h1-h6": "Heading elements representing document hierarchy.",
}


def semantic_html_examples() -> None:
    section("3. Semantic HTML")

    for element, meaning in SEMANTIC_ELEMENTS.items():
        print(f"{element:12} -> {meaning}")

    show_html(
        "Poor navigation",
        """
<div class="navigation">
    <div onclick="goHome()">Home</div>
    <div onclick="goProducts()">Products</div>
    <div onclick="goContact()">Contact</div>
</div>
""",
    )

    show_html(
        "Semantic navigation",
        """
<nav aria-label="Primary">
    <ul>
        <li><a href="/">Home</a></li>
        <li><a href="/products">Products</a></li>
        <li><a href="/contact">Contact</a></li>
    </ul>
</nav>
""",
    )

    show_html(
        "Poor action control",
        """
<div class="button" onclick="saveData()">Save</div>
""",
    )

    show_html(
        "Native button",
        """
<button type="button" onclick="saveData()">Save</button>
""",
    )

    print(
        "\nThe native button already carries important semantics. It can be "
        "focused and activated through standard keyboard interaction, and its "
        "meaning is exposed through browser accessibility APIs."
    )


# =============================================================================
# 4. DOCUMENT STRUCTURE AND HEADINGS
# =============================================================================

@dataclass
class Heading:
    level: int
    text: str


def heading_outline(headings: Sequence[Heading]) -> List[str]:
    """Create a readable representation of a heading hierarchy."""
    result = []

    for heading in headings:
        indentation = "  " * max(heading.level - 1, 0)
        result.append(f"{indentation}H{heading.level}: {heading.text}")

    return result


def heading_demo() -> None:
    section("4. Headings and document structure")

    good_headings = [
        Heading(1, "University Admissions"),
        Heading(2, "Eligibility"),
        Heading(2, "Application process"),
        Heading(3, "Required documents"),
        Heading(3, "Application fee"),
        Heading(2, "Contact"),
    ]

    print("Example heading hierarchy:")
    print("\n".join(heading_outline(good_headings)))

    print(
        "\nHeading elements should represent structure rather than visual "
        "font size. CSS should normally control appearance."
    )

    show_html(
        "A structured document",
        """
<main>
    <h1>University Admissions</h1>

    <section>
        <h2>Eligibility</h2>
        <p>Applicants must satisfy the published eligibility criteria.</p>
    </section>

    <section>
        <h2>Application process</h2>

        <h3>Required documents</h3>
        <p>Prepare the required documents before submission.</p>

        <h3>Application fee</h3>
        <p>The applicable fee is displayed during application.</p>
    </section>
</main>
""",
    )

    show_html(
        "Avoid heading misuse",
        """
<h1>University Admissions</h1>
<h1>Required documents</h1>
<h1>Application fee</h1>
""",
    )

    print(
        "\nA perfectly linear numeric sequence is not the only consideration. "
        "The important point is that headings form a meaningful hierarchy. "
        "Skipping a level can sometimes be technically valid when the "
        "document structure remains understandable, but deliberate, "
        "consistent hierarchy is preferable."
    )


# =============================================================================
# 5. LANDMARKS AND NAVIGATION
# =============================================================================

def landmark_demo() -> None:
    section("5. Semantic landmarks and navigation")

    show_html(
        "Accessible page landmarks",
        """
<header>
    <a href="#main-content">Skip to main content</a>
</header>

<nav aria-label="Primary">
    <a href="/">Home</a>
    <a href="/courses">Courses</a>
    <a href="/about">About</a>
</nav>

<main id="main-content">
    <h1>Courses</h1>
    <p>Course information appears here.</p>
</main>

<aside aria-label="Related information">
    <h2>Related</h2>
    <a href="/faq">FAQ</a>
</aside>

<footer>
    <p>Copyright information</p>
</footer>
""",
    )

    explain(
        "Landmarks",
        "Landmarks divide a page into recognizable regions. Screen-reader "
        "users can often navigate among these regions rather than listening "
        "to every element sequentially.",
    )

    explain(
        "Skip link",
        "A skip link provides a fast path around repeated content such as "
        "a large header or navigation menu. It is especially useful for "
        "keyboard users.",
    )

    show_html(
        "Skip link target",
        """
<a href="#main-content">Skip to main content</a>

<main id="main-content">
    ...
</main>
""",
    )


# =============================================================================
# 6. LINKS VERSUS BUTTONS
# =============================================================================

def links_and_buttons_demo() -> None:
    section("6. Links versus buttons")

    comparisons = [
        (
            "Link",
            "Moves the user to another URL, document location, or resource.",
        ),
        (
            "Button",
            "Performs an action such as opening a dialog, submitting data, "
            "toggling a setting, or starting an operation.",
        ),
    ]

    for name, meaning in comparisons:
        print(f"{name}: {meaning}")

    show_html(
        "Correct distinction",
        """
<a href="/account">View account</a>

<button type="button" id="open-settings">
    Open settings
</button>
""",
    )

    show_html(
        "Common mistake",
        """
<a href="#" onclick="openSettings()">Open settings</a>
""",
    )

    print(
        "\nUsing an anchor as a button can create avoidable keyboard and "
        "semantic problems. Choose the native element whose behavior matches "
        "the intended interaction."
    )


# =============================================================================
# 7. FORM ACCESSIBILITY
# =============================================================================

@dataclass
class FormControl:
    control_id: str
    control_type: str
    label: str
    required: bool = False
    description: Optional[str] = None
    error: Optional[str] = None


def render_accessible_form_control(control: FormControl) -> str:
    attributes = [
        f'id="{html.escape(control.control_id)}"',
        f'type="{html.escape(control.control_type)}"',
    ]

    if control.required:
        attributes.append("required")

    if control.description:
        description_id = f"{control.control_id}-description"
        attributes.append(f'aria-describedby="{description_id}"')

    if control.error:
        error_id = f"{control.control_id}-error"
        attributes.append(f'aria-describedby="{error_id}"')
        attributes.append('aria-invalid="true"')

    element = f"<input {' '.join(attributes)}>"

    pieces = [
        f'<label for="{html.escape(control.control_id)}">'
        f"{html.escape(control.label)}</label>"
    ]

    if control.description:
        pieces.append(
            f'<p id="{control.control_id}-description">'
            f"{html.escape(control.description)}</p>"
        )

    if control.error:
        pieces.append(
            f'<p id="{control.control_id}-error" role="alert">'
            f"{html.escape(control.error)}</p>"
        )

    pieces.append(element)

    return "\n".join(pieces)


def form_accessibility_demo() -> None:
    section("7. Accessible forms")

    valid_control = FormControl(
        control_id="email",
        control_type="email",
        label="Email address",
        required=True,
        description="Use an address that you can access.",
    )

    invalid_control = FormControl(
        control_id="password",
        control_type="password",
        label="Password",
        required=True,
        error="Password must contain at least 12 characters.",
    )

    show_html(
        "Accessible form control",
        render_accessible_form_control(valid_control),
    )

    show_html(
        "Accessible invalid form control",
        render_accessible_form_control(invalid_control),
    )

    show_html(
        "Poor form control",
        """
<input type="text" placeholder="Enter email">
""",
    )

    print(
        "\nPlaceholder text is not a replacement for a persistent label. "
        "Labels help users identify controls before, during, and after input."
    )

    show_html(
        "Grouped radio buttons",
        """
<fieldset>
    <legend>Preferred contact method</legend>

    <label>
        <input type="radio" name="contact" value="email">
        Email
    </label>

    <label>
        <input type="radio" name="contact" value="phone">
        Phone
    </label>
</fieldset>
""",
    )


# =============================================================================
# 8. LABEL ASSOCIATION
# =============================================================================

def validate_label_association(html_source: str) -> List[str]:
    """
    Perform a small educational check for label/input associations.

    This is intentionally not a full HTML parser. It demonstrates the logic
    behind one accessibility check without pretending to replace browser
    accessibility testing.
    """
    problems = []

    input_ids = set(
        re.findall(r'<input\b[^>]*\bid=["\']([^"\']+)["\']', html_source, re.I)
    )

    labels = re.findall(
        r'<label\b([^>]*)>(.*?)</label>',
        html_source,
        re.I | re.S,
    )

    for attributes, content in labels:
        match = re.search(
            r'\bfor=["\']([^"\']+)["\']',
            attributes,
            re.I,
        )

        if match:
            target_id = match.group(1)

            if target_id not in input_ids:
                problems.append(
                    f"Label references missing control id '{target_id}'."
                )
        else:
            if not re.search(r'<input\b', content, re.I):
                problems.append(
                    "Label has neither a matching 'for' attribute nor a "
                    "nested input control."
                )

    return problems


def label_validation_demo() -> None:
    section("8. Label association validation")

    good = """
<label for="username">Username</label>
<input id="username" type="text">
"""

    bad = """
<label for="user-name">Username</label>
<input id="username" type="text">
"""

    demo_output("Valid example", validate_label_association(good))
    demo_output("Invalid example", validate_label_association(bad))


# =============================================================================
# 9. KEYBOARD ACCESSIBILITY
# =============================================================================

KEYBOARD_ORDER = [
    "Skip link",
    "Primary navigation",
    "Search",
    "Main content controls",
    "Footer links",
]


def keyboard_demo() -> None:
    section("9. Keyboard accessibility")

    print("Illustrative keyboard navigation order:")
    for number, item in enumerate(KEYBOARD_ORDER, start=1):
        print(f"{number}. {item}")

    print(
        "\nImportant keyboard concepts:"
        "\n  Tab: usually moves focus forward among focusable controls."
        "\n  Shift+Tab: usually moves focus backward."
        "\n  Enter: commonly activates links and some controls."
        "\n  Space: commonly activates buttons and toggles."
        "\n  Arrow keys: often operate composite widgets such as menus, tabs, "
        "radio groups, and listboxes."
        "\n  Escape: often closes dialogs, menus, or popups."
    )

    show_html(
        "Native controls provide keyboard behavior",
        """
<button type="button">Open dialog</button>
<a href="/profile">Profile</a>
<input type="search" aria-label="Search">
""",
    )

    show_html(
        "A dangerous custom-control pattern",
        """
<div tabindex="0" onclick="activate()">Open</div>
""",
    )

    print(
        "\nAdding tabindex=0 does not automatically turn a div into a fully "
        "accessible button. A custom control may need keyboard event handling, "
        "semantics, focus styling, state communication, and correct interaction "
        "behavior. Native controls avoid most of this complexity."
    )


# =============================================================================
# 10. TABINDEX
# =============================================================================

def tabindex_demo() -> None:
    section("10. tabindex")

    values = {
        "No tabindex":
            "Uses the element's native focus behavior.",
        'tabindex="0"':
            "Places an otherwise focusable element into the normal document "
            "tab sequence.",
        'tabindex="-1"':
            "Removes the element from sequential Tab navigation while still "
            "allowing script or programmatic focus.",
        'tabindex="1" or greater':
            "Creates a positive custom tab order and is generally discouraged "
            "because it can produce confusing focus sequences.",
    }

    for value, explanation in values.items():
        print(f"{value}: {explanation}")

    show_html(
        "Useful programmatic focus target",
        """
<main id="main-content" tabindex="-1">
    <h1>Search results</h1>
</main>
""",
    )


# =============================================================================
# 11. FOCUS MANAGEMENT
# =============================================================================

@dataclass
class FocusEvent:
    action: str
    expected_focus: str


def focus_management_demo() -> None:
    section("11. Focus management")

    dialog_flow = [
        FocusEvent("User activates 'Delete account'", "Delete dialog"),
        FocusEvent("Dialog opens", "Dialog heading or first meaningful control"),
        FocusEvent("User completes or cancels", "Original 'Delete account' button"),
    ]

    for event in dialog_flow:
        print(f"{event.action} -> focus should move to {event.expected_focus}")

    print(
        "\nA modal dialog should normally:"
        "\n  - expose dialog semantics;"
        "\n  - have an accessible name;"
        "\n  - move focus into the dialog when opened;"
        "\n  - keep keyboard interaction within the modal while it is modal;"
        "\n  - close predictably;"
        "\n  - restore focus to a sensible element when it closes."
    )


# =============================================================================
# 12. VISIBLE FOCUS
# =============================================================================

def visible_focus_demo() -> None:
    section("12. Visible keyboard focus")

    show_html(
        "Accessible focus styling",
        """
<style>
button:focus-visible,
a:focus-visible,
input:focus-visible {
    outline: 3px solid currentColor;
    outline-offset: 3px;
}
</style>
""",
    )

    print(
        "\nRemoving the browser's focus indicator without supplying an "
        "equivalent visible indicator can make keyboard navigation difficult. "
        "Focus should remain visually distinguishable."
    )


# =============================================================================
# 13. IMAGES AND ALTERNATIVE TEXT
# =============================================================================

@dataclass
class ImageExample:
    purpose: str
    markup: str
    reason: str


IMAGE_EXAMPLES = [
    ImageExample(
        "Informative image",
        '<img src="sales-chart.png" alt="Sales increased from 2024 to 2025.">',
        "The alt text communicates the meaningful information.",
    ),
    ImageExample(
        "Decorative image",
        '<img src="decorative-line.svg" alt="">',
        "An empty alt attribute tells assistive technology that the image "
        "does not add meaningful content.",
    ),
    ImageExample(
        "Functional image",
        '<button type="button"><img src="search.svg" alt="Search"></button>',
        "The accessible name describes the button's action.",
    ),
    ImageExample(
        "Image containing important text",
        '<img src="offer.png" alt="Application deadline: 30 September.">',
        "Important information inside the image needs an accessible text "
        "equivalent.",
    ),
]


def image_accessibility_demo() -> None:
    section("13. Images and alternative text")

    for example in IMAGE_EXAMPLES:
        print(f"\n{example.purpose}")
        print(example.markup)
        print(f"Reason: {example.reason}")

    print(
        "\nAlternative text should communicate purpose, not mechanically "
        "describe every visible pixel. Context determines the appropriate "
        "alternative."
    )


# =============================================================================
# 14. COLOR AND CONTRAST
# =============================================================================

def relative_luminance(red: int, green: int, blue: int) -> float:
    """Calculate relative luminance using the WCAG sRGB procedure."""
    channels = []

    for channel in (red, green, blue):
        normalized = channel / 255.0

        if normalized <= 0.03928:
            linear = normalized / 12.92
        else:
            linear = ((normalized + 0.055) / 1.055) ** 2.4

        channels.append(linear)

    return (
        0.2126 * channels[0]
        + 0.7152 * channels[1]
        + 0.0722 * channels[2]
    )


def contrast_ratio(
    foreground: Tuple[int, int, int],
    background: Tuple[int, int, int],
) -> float:
    """Calculate contrast ratio between two sRGB colors."""
    foreground_luminance = relative_luminance(*foreground)
    background_luminance = relative_luminance(*background)

    lighter = max(foreground_luminance, background_luminance)
    darker = min(foreground_luminance, background_luminance)

    return (lighter + 0.05) / (darker + 0.05)


def contrast_demo() -> None:
    section("14. Color contrast")

    examples = [
        ((0, 0, 0), (255, 255, 255)),
        ((120, 120, 120), (255, 255, 255)),
        ((255, 255, 255), (30, 60, 120)),
    ]

    for foreground, background in examples:
        ratio = contrast_ratio(foreground, background)
        print(
            f"Foreground {foreground}, background {background}: "
            f"{ratio:.2f}:1"
        )

    print(
        "\nContrast requirements depend on text size, weight, content type, "
        "and the applicable WCAG criterion. Do not treat one numerical ratio "
        "as the complete accessibility evaluation."
    )

    print(
        "\nColor should not be the sole mechanism for communicating meaning. "
        "For example, an error state should use text, icons, labels, or other "
        "information in addition to color."
    )


# =============================================================================
# 15. ARIA BASICS
# =============================================================================

ARIA_CATEGORIES = {
    "role": "Communicates what an interface object is.",
    "state": "Communicates a dynamic condition such as expanded or checked.",
    "property": "Communicates a characteristic such as an accessible label.",
}


def aria_demo() -> None:
    section("15. ARIA basics")

    for category, meaning in ARIA_CATEGORIES.items():
        print(f"{category}: {meaning}")

    show_html(
        "ARIA-expanded",
        """
<button
    type="button"
    aria-expanded="false"
    aria-controls="account-menu">
    Account
</button>

<div id="account-menu" hidden>
    ...
</div>
""",
    )

    show_html(
        "ARIA-pressed",
        """
<button type="button" aria-pressed="false">
    Bold
</button>
""",
    )

    show_html(
        "ARIA-selected",
        """
<div role="tablist" aria-label="Account sections">
    <button role="tab" aria-selected="true" aria-controls="overview">
        Overview
    </button>
    <button role="tab" aria-selected="false" aria-controls="activity">
        Activity
    </button>
</div>
""",
    )

    print(
        "\nA central ARIA rule is: prefer native HTML semantics when they "
        "already provide the required behavior. ARIA can expose semantics, "
        "but it does not automatically implement keyboard behavior or "
        "application logic."
    )


# =============================================================================
# 16. THE FIRST RULE OF ARIA
# =============================================================================

def first_rule_of_aria_demo() -> None:
    section("16. Native HTML versus unnecessary ARIA")

    show_html(
        "Prefer native HTML",
        """
<button type="button">Save</button>
""",
    )

    show_html(
        "Unnecessarily verbose equivalent",
        """
<div role="button" tabindex="0">
    Save
</div>
""",
    )

    print(
        "\nThe second example creates a larger responsibility. The developer "
        "must reproduce button behavior, including relevant keyboard input, "
        "focus behavior, disabled state handling, and interaction semantics."
    )


# =============================================================================
# 17. ACCESSIBLE NAMES
# =============================================================================

def accessible_name_demo() -> None:
    section("17. Accessible names")

    show_html(
        "Visible text provides a clear name",
        """
<button type="button">Save changes</button>
""",
    )

    show_html(
        "aria-label provides a name when appropriate",
        """
<button type="button" aria-label="Close dialog">
    <svg aria-hidden="true">...</svg>
</button>
""",
    )

    show_html(
        "aria-labelledby references visible naming content",
        """
<h2 id="dialog-title">Delete account</h2>

<div role="dialog" aria-labelledby="dialog-title">
    ...
</div>
""",
    )

    print(
        "\nAn accessible name is the name exposed to accessibility APIs for "
        "an interface object. It is not always identical to the visible "
        "text, but visible text should generally remain the primary source "
        "when it adequately communicates the control's purpose."
    )


# =============================================================================
# 18. ARIA DESCRIPTIONS AND ERROR MESSAGES
# =============================================================================

def descriptions_and_errors_demo() -> None:
    section("18. Descriptions, instructions, and errors")

    show_html(
        "Descriptive relationship",
        """
<label for="account-number">Account number</label>
<input
    id="account-number"
    type="text"
    aria-describedby="account-help">

<p id="account-help">
    Enter the 10-digit account number shown on your statement.
</p>
""",
    )

    show_html(
        "Invalid input",
        """
<label for="email">Email address</label>
<input
    id="email"
    type="email"
    aria-invalid="true"
    aria-describedby="email-error">

<p id="email-error" role="alert">
    Enter a valid email address.
</p>
""",
    )

    print(
        "\nError communication should identify the affected field and "
        "explain what needs to be corrected. The application should not rely "
        "only on a color change or a visual icon."
    )


# =============================================================================
# 19. LIVE REGIONS
# =============================================================================

def live_region_demo() -> None:
    section("19. ARIA live regions")

    show_html(
        "Status message",
        """
<div role="status" aria-live="polite">
    3 results found.
</div>
""",
    )

    show_html(
        "Assertive alert",
        """
<div role="alert">
    Payment failed.
</div>
""",
    )

    print(
        "\nLive regions communicate dynamically updated content that may not "
        "otherwise be announced at the right time. Assertive announcements "
        "should be used sparingly because they can interrupt the user's "
        "current activity."
    )


# =============================================================================
# 20. HIDDEN CONTENT
# =============================================================================

def hidden_content_demo() -> None:
    section("20. Hidden content and accessibility trees")

    examples = {
        "display: none":
            "Normally removes the element from visual rendering and the "
            "accessibility representation.",
        "hidden attribute":
            "Provides semantic hidden state and is generally unavailable "
            "to assistive technology.",
        "visibility: hidden":
            "Normally hides the element and prevents normal interaction.",
        "aria-hidden=\"true\"":
            "Requests that the element be excluded from the accessibility "
            "tree while it may remain visually present.",
    }

    for technique, meaning in examples.items():
        print(f"{technique}: {meaning}")

    show_html(
        "Decorative icon",
        """
<button type="button">
    <svg aria-hidden="true">...</svg>
    Delete
</button>
""",
    )

    print(
        "\nDo not apply aria-hidden=true to a focusable element or an element "
        "that contains required accessible information. Doing so can create "
        "a mismatch between keyboard focus and the accessibility tree."
    )


# =============================================================================
# 21. SCREEN READER MENTAL MODEL
# =============================================================================

@dataclass
class AccessibilityNode:
    role: str
    name: str
    state: Optional[str] = None


def simulated_accessibility_tree() -> List[AccessibilityNode]:
    return [
        AccessibilityNode("navigation", "Primary"),
        AccessibilityNode("link", "Home"),
        AccessibilityNode("link", "Courses"),
        AccessibilityNode("main", ""),
        AccessibilityNode("heading", "Course catalog"),
        AccessibilityNode("button", "Filter courses", "collapsed"),
        AccessibilityNode("textbox", "Search courses"),
    ]


def screen_reader_demo() -> None:
    section("21. Screen readers and the accessibility tree")

    print(
        "A simplified conceptual accessibility tree might expose nodes such "
        "as the following:"
    )

    for node in simulated_accessibility_tree():
        state = f" [{node.state}]" if node.state else ""
        name = f' "{node.name}"' if node.name else ""
        print(f"  {node.role}{name}{state}")

    print(
        "\nThis is a conceptual model rather than a browser-specific dump. "
        "Browsers derive accessibility information from DOM semantics, "
        "computed names, states, properties, CSS visibility, and ARIA."
    )

    print(
        "\nScreen-reader users may navigate by:"
        "\n  - headings;"
        "\n  - landmarks;"
        "\n  - links;"
        "\n  - form controls;"
        "\n  - buttons;"
        "\n  - tables;"
        "\n  - lists;"
        "\n  - reading order."
    )


# =============================================================================
# 22. SOURCE ORDER VERSUS VISUAL ORDER
# =============================================================================

def source_order_demo() -> None:
    section("22. Reading order and source order")

    show_html(
        "Preferred source order",
        """
<main>
    <h1>Checkout</h1>
    <form>
        <label for="name">Name</label>
        <input id="name" type="text">

        <button type="submit">Place order</button>
    </form>
</main>
""",
    )

    print(
        "\nCSS can visually reposition elements. Excessive visual reordering "
        "can create a mismatch between what sighted users see and what "
        "keyboard or assistive-technology users encounter. Logical source "
        "order should normally match the intended reading and interaction "
        "order."
    )


# =============================================================================
# 23. TABLE ACCESSIBILITY
# =============================================================================

def table_accessibility_demo() -> None:
    section("23. Accessible tables")

    show_html(
        "Basic data table",
        """
<table>
    <caption>Quarterly revenue by region</caption>
    <thead>
        <tr>
            <th scope="col">Region</th>
            <th scope="col">Q1</th>
            <th scope="col">Q2</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <th scope="row">North</th>
            <td>120000</td>
            <td>135000</td>
        </tr>
        <tr>
            <th scope="row">South</th>
            <td>98000</td>
            <td>112000</td>
        </tr>
    </tbody>
</table>
""",
    )

    print(
        "\nUse tables for genuine tabular relationships, not for page layout. "
        "Captions identify the table, while appropriate header markup and "
        "scope relationships help communicate row and column meaning."
    )


# =============================================================================
# 24. LANGUAGE
# =============================================================================

def language_demo() -> None:
    section("24. Document language")

    show_html(
        "Language declaration",
        """
<html lang="en">
    ...
</html>
""",
    )

    show_html(
        "Language change within a document",
        """
<p>The French greeting is <span lang="fr">Bonjour</span>.</p>
""",
    )

    print(
        "\nThe language attribute helps assistive technologies select "
        "appropriate pronunciation and language-specific behavior."
    )


# =============================================================================
# 25. PAGE TITLE
# =============================================================================

def title_demo() -> None:
    section("25. Page titles")

    show_html(
        "Meaningful title",
        """
<head>
    <title>Course catalog | Example University</title>
</head>
""",
    )

    print(
        "\nThe document title is important because it can be announced by "
        "assistive technology and helps users identify a page among browser "
        "tabs, history entries, and other contexts."
    )


# =============================================================================
# 26. FORM AUTOCOMPLETE AND INPUT TYPES
# =============================================================================

def autocomplete_demo() -> None:
    section("26. Input purpose and autocomplete")

    show_html(
        "Meaningful input metadata",
        """
<label for="given-name">First name</label>
<input
    id="given-name"
    name="given-name"
    type="text"
    autocomplete="given-name">
""",
    )

    show_html(
        "Email input",
        """
<label for="email">Email address</label>
<input
    id="email"
    name="email"
    type="email"
    autocomplete="email">
""",
    )

    print(
        "\nCorrect input types and autocomplete tokens can help browsers and "
        "assistive technologies understand input purpose and support users "
        "with cognitive or motor disabilities."
    )


# =============================================================================
# 27. CUSTOM CHECKBOX EXAMPLE
# =============================================================================

@dataclass
class ToggleState:
    checked: bool = False

    def toggle(self) -> None:
        self.checked = not self.checked

    @property
    def aria_checked(self) -> str:
        return "true" if self.checked else "false"


def custom_checkbox_demo() -> None:
    section("27. Native checkbox versus custom widget")

    show_html(
        "Preferred implementation",
        """
<label>
    <input type="checkbox" name="notifications">
    Receive notifications
</label>
""",
    )

    state = ToggleState()

    show_html(
        "Custom widget requires state management",
        """
<div
    role="checkbox"
    tabindex="0"
    aria-checked="false">
    Receive notifications
</div>
""",
    )

    print(f"Initial custom state: aria-checked={state.aria_checked}")

    state.toggle()

    print(f"After activation: aria-checked={state.aria_checked}")

    print(
        "\nA real custom checkbox must also handle the appropriate keyboard "
        "interaction, focus styling, accessible naming, state updates, and "
        "event behavior. This is why native controls are usually preferable."
    )


# =============================================================================
# 28. CUSTOM DISCLOSURE WIDGET
# =============================================================================

@dataclass
class Disclosure:
    expanded: bool = False

    def activate(self) -> None:
        self.expanded = not self.expanded

    def render(self) -> str:
        expanded = "true" if self.expanded else "false"
        hidden_attribute = "" if self.expanded else " hidden"

        return f"""
<button
    type="button"
    aria-expanded="{expanded}"
    aria-controls="details">
    Show details
</button>

<div id="details"{hidden_attribute}>
    Detailed information.
</div>
""".strip()


def disclosure_demo() -> None:
    section("28. Disclosure widgets")

    disclosure = Disclosure()

    show_html("Collapsed state", disclosure.render())

    disclosure.activate()

    show_html("Expanded state", disclosure.render())


# =============================================================================
# 29. MODAL DIALOG STRUCTURE
# =============================================================================

def dialog_demo() -> None:
    section("29. Dialog accessibility")

    show_html(
        "Dialog structure",
        """
<dialog
    aria-labelledby="dialog-title"
    aria-describedby="dialog-description">

    <h2 id="dialog-title">Delete account</h2>

    <p id="dialog-description">
        This action permanently removes your account.
    </p>

    <button type="button">Cancel</button>
    <button type="button">Delete account</button>
</dialog>
""",
    )

    print(
        "\nDialog accessibility includes naming, description when useful, "
        "keyboard operation, focus placement, modal behavior where applicable, "
        "and sensible focus restoration."
    )


# =============================================================================
# 30. MENUS AND NAVIGATION
# =============================================================================

def navigation_menu_demo() -> None:
    section("30. Navigation menus")

    show_html(
        "Ordinary site navigation",
        """
<nav aria-label="Primary">
    <ul>
        <li><a href="/">Home</a></li>
        <li><a href="/products">Products</a></li>
        <li><a href="/support">Support</a></li>
    </ul>
</nav>
""",
    )

    print(
        "\nAn ordinary website navigation list does not automatically need "
        "the ARIA menu pattern. The ARIA menu pattern represents a more "
        "specific application-style interaction with specialized keyboard "
        "behavior. Misusing role=menu can make ordinary navigation harder "
        "to operate."
    )


# =============================================================================
# 31. TABS
# =============================================================================

@dataclass
class Tab:
    name: str
    panel_id: str
    selected: bool = False


class TabSet:
    def __init__(self, tabs: Sequence[Tab]):
        self.tabs = list(tabs)

        if self.tabs and not any(tab.selected for tab in self.tabs):
            self.tabs[0].selected = True

    def select(self, index: int) -> None:
        if index < 0 or index >= len(self.tabs):
            raise IndexError("Tab index is outside the valid range.")

        for tab_number, tab in enumerate(self.tabs):
            tab.selected = tab_number == index

    def state(self) -> List[Dict[str, object]]:
        return [
            {
                "name": tab.name,
                "panel": tab.panel_id,
                "selected": tab.selected,
            }
            for tab in self.tabs
        ]


def tab_demo() -> None:
    section("31. Tabs as a composite widget")

    tabs = TabSet(
        [
            Tab("Overview", "overview"),
            Tab("Activity", "activity"),
            Tab("Settings", "settings"),
        ]
    )

    print("Initial state:", tabs.state())

    tabs.select(2)

    print("After selecting Settings:", tabs.state())

    print(
        "\nA complete tab implementation requires more than role=tab. "
        "Developers must implement selection state, tab-panel relationships, "
        "focus behavior, keyboard navigation, and visibility rules."
    )


# =============================================================================
# 32. CAROUSELS
# =============================================================================

def carousel_demo() -> None:
    section("32. Carousel accessibility considerations")

    show_html(
        "Conceptual carousel structure",
        """
<section aria-roledescription="carousel" aria-label="Featured courses">
    <div role="group" aria-label="Slide 1 of 3">
        <h2>Python fundamentals</h2>
    </div>

    <button type="button" aria-label="Previous slide">
        Previous
    </button>

    <button type="button" aria-label="Next slide">
        Next
    </button>

    <button type="button" aria-label="Pause automatic rotation">
        Pause
    </button>
</section>
""",
    )

    print(
        "\nCarousels introduce timing, focus, announcement, and control "
        "complexity. Automatic movement should not make content difficult to "
        "read or operate. A user should have an accessible mechanism to "
        "control relevant movement."
    )


# =============================================================================
# 33. MEDIA ACCESSIBILITY
# =============================================================================

def media_demo() -> None:
    section("33. Audio and video accessibility")

    show_html(
        "Video with captions",
        """
<video controls>
    <source src="lecture.mp4" type="video/mp4">
    <track
        kind="captions"
        src="lecture-en.vtt"
        srclang="en"
        label="English">
</video>
""",
    )

    print(
        "\nCaptions provide synchronized text for spoken dialogue and "
        "relevant audio information. Transcripts can provide a text "
        "alternative for audio or video content and can also improve "
        "searchability and comprehension."
    )


# =============================================================================
# 34. REDUCED MOTION
# =============================================================================

def reduced_motion_demo() -> None:
    section("34. Motion and user preferences")

    show_html(
        "Respecting reduced-motion preferences",
        """
@media (prefers-reduced-motion: reduce) {
    *,
    *::before,
    *::after {
        animation-duration: 0.01ms;
        animation-iteration-count: 1;
        transition-duration: 0.01ms;
        scroll-behavior: auto;
    }
}
""",
    )

    print(
        "\nAnimations can affect people with vestibular or motion sensitivity. "
        "The exact implementation should preserve usability while reducing "
        "nonessential motion when users express that preference."
    )


# =============================================================================
# 35. RESPONSIVE ACCESSIBILITY
# =============================================================================

def responsive_demo() -> None:
    section("35. Responsive and mobile accessibility")

    print(
        "\nAccessibility is not limited to desktop screen readers. A robust "
        "mobile experience should consider:"
        "\n  - touch target usability;"
        "\n  - zoom and text resizing;"
        "\n  - orientation;"
        "\n  - reflow;"
        "\n  - screen-reader gestures;"
        "\n  - keyboard support when a physical keyboard is present;"
        "\n  - responsive focus and dialog behavior."
    )

    show_html(
        "Responsive viewport",
        """
<meta
    name="viewport"
    content="width=device-width, initial-scale=1">
""",
    )


# =============================================================================
# 36. ERROR HANDLING IN FORMS
# =============================================================================

@dataclass
class ValidationResult:
    valid: bool
    errors: Dict[str, str] = field(default_factory=dict)


def validate_registration(
    name: str,
    email: str,
    password: str,
) -> ValidationResult:
    errors: Dict[str, str] = {}

    if not name.strip():
        errors["name"] = "Enter your name."

    if "@" not in email or "." not in email:
        errors["email"] = "Enter a valid email address."

    if len(password) < 12:
        errors["password"] = "Password must contain at least 12 characters."

    return ValidationResult(
        valid=not errors,
        errors=errors,
    )


def form_validation_demo() -> None:
    section("36. Accessible validation")

    result = validate_registration(
        name="",
        email="invalid",
        password="short",
    )

    print("Valid:", result.valid)

    for field_name, message in result.errors.items():
        print(f"{field_name}: {message}")

    show_html(
        "Error summary pattern",
        """
<div role="alert" tabindex="-1">
    <h2>There are 3 errors</h2>
    <ul>
        <li><a href="#name">Enter your name.</a></li>
        <li><a href="#email">Enter a valid email address.</a></li>
        <li><a href="#password">Password must contain at least 12 characters.</a></li>
    </ul>
</div>
""",
    )

    print(
        "\nAn error summary can provide a fast route to invalid controls. "
        "Individual controls should still communicate their own errors."
    )


# =============================================================================
# 37. DYNAMIC APPLICATION STATE
# =============================================================================

@dataclass
class AccessibleButton:
    label: str
    pressed: bool = False

    def activate(self) -> None:
        self.pressed = not self.pressed

    def html(self) -> str:
        value = "true" if self.pressed else "false"
        return (
            f'<button type="button" aria-pressed="{value}">'
            f"{html.escape(self.label)}</button>"
        )


def dynamic_state_demo() -> None:
    section("37. Dynamic state and synchronization")

    favorite = AccessibleButton("Favorite")

    print(favorite.html())

    favorite.activate()

    print(favorite.html())

    print(
        "\nWhen a visual state changes, the corresponding semantic state "
        "should change at the same time. A favorite button that looks active "
        "but continues to expose aria-pressed=false creates conflicting "
        "information."
    )


# =============================================================================
# 38. FOCUS TRAPS
# =============================================================================

def focus_trap_demo() -> None:
    section("38. Focus traps")

    print(
        "\nA focus trap can be appropriate inside a genuinely modal dialog, "
        "where focus must remain inside the active modal until it closes."
    )

    print(
        "\nA focus trap is problematic when used accidentally or on ordinary "
        "page content. Users can become unable to reach other controls."
    )

    print(
        "\nProduction modal implementations should account for:"
        "\n  - first focus;"
        "\n  - last focus;"
        "\n  - Tab;"
        "\n  - Shift+Tab;"
        "\n  - Escape;"
        "\n  - modal close;"
        "\n  - focus restoration;"
        "\n  - nested dialogs if supported."
    )


# =============================================================================
# 39. KEYBOARD EVENT MODEL
# =============================================================================

@dataclass
class KeyEvent:
    key: str
    action: str


KEYBOARD_EVENTS = [
    KeyEvent("Tab", "Move focus forward"),
    KeyEvent("Shift+Tab", "Move focus backward"),
    KeyEvent("Enter", "Activate a link or applicable control"),
    KeyEvent("Space", "Activate or toggle applicable controls"),
    KeyEvent("Escape", "Close a modal or popup when defined by its pattern"),
    KeyEvent("Arrow keys", "Navigate within applicable composite widgets"),
]


def keyboard_event_demo() -> None:
    section("39. Keyboard interaction design")

    for event in KEYBOARD_EVENTS:
        print(f"{event.key:16} -> {event.action}")

    print(
        "\nKeyboard support should follow the expected interaction model for "
        "the widget. Arbitrary key handling can conflict with browser or "
        "assistive-technology expectations."
    )


# =============================================================================
# 40. ACCESSIBLE NAME CALCULATION CONCEPT
# =============================================================================

def approximate_accessible_name(html_source: str) -> Optional[str]:
    """
    A deliberately simplified accessible-name demonstration.

    Real accessible-name computation follows a detailed standard algorithm.
    This function illustrates several common sources without claiming to
    implement the complete algorithm.
    """
    aria_label = re.search(
        r'\baria-label=["\']([^"\']+)["\']',
        html_source,
        re.I,
    )

    if aria_label:
        return aria_label.group(1).strip()

    labelledby = re.search(
        r'\baria-labelledby=["\']([^"\']+)["\']',
        html_source,
        re.I,
    )

    if labelledby:
        return f"Text referenced by {labelledby.group(1)}"

    text = re.sub(r"<[^>]+>", " ", html_source)
    text = re.sub(r"\s+", " ", text).strip()

    return text or None


def accessible_name_demo() -> None:
    section("40. Accessible-name reasoning")

    examples = [
        '<button>Save changes</button>',
        '<button aria-label="Close dialog"><svg></svg></button>',
        '<input aria-label="Search courses">',
    ]

    for source in examples:
        print(source)
        print("Approximate name:", approximate_accessible_name(source))

    print(
        "\nThis Python function is intentionally incomplete. Real browser "
        "accessibility behavior involves a formal accessible-name-and-"
        "description computation algorithm and many element-specific rules."
    )


# =============================================================================
# 41. ARIA VALIDATION
# =============================================================================

KNOWN_ROLES = {
    "button",
    "checkbox",
    "dialog",
    "link",
    "main",
    "navigation",
    "radio",
    "status",
    "tab",
    "tablist",
    "tabpanel",
    "textbox",
}


def find_aria_roles(html_source: str) -> List[str]:
    return re.findall(
        r'\brole=["\']([^"\']+)["\']',
        html_source,
        re.I,
    )


def validate_aria_roles(html_source: str) -> List[str]:
    errors = []

    for role in find_aria_roles(html_source):
        if role not in KNOWN_ROLES:
            errors.append(f"Unknown educational role value: {role}")

    return errors


def aria_validation_demo() -> None:
    section("41. Basic ARIA validation")

    good = """
<div role="button" tabindex="0">Save</div>
"""

    bad = """
<div role="made-up-control">Save</div>
"""

    print("Good:", validate_aria_roles(good))
    print("Bad:", validate_aria_roles(bad))

    print(
        "\nThis is only a small educational validator. Correct ARIA requires "
        "checking role-specific required states, supported properties, "
        "relationships, keyboard interaction, naming, and more."
    )


# =============================================================================
# 42. SEMANTIC HTML LINTER
# =============================================================================

@dataclass
class AccessibilityIssue:
    severity: str
    rule: str
    message: str


class AccessibilityLinter:
    """
    Small educational HTML accessibility linter.

    It intentionally uses regular expressions rather than pretending to be a
    standards-complete HTML parser or automated WCAG checker.
    """

    def lint(self, source: str) -> List[AccessibilityIssue]:
        issues: List[AccessibilityIssue] = []

        self._check_images(source, issues)
        self._check_buttons(source, issues)
        self._check_links(source, issues)
        self._check_language(source, issues)
        self._check_title(source, issues)
        self._check_labels(source, issues)
        self._check_positive_tabindex(source, issues)
        self._check_aria_hidden_focusable(source, issues)

        return issues

    @staticmethod
    def _check_images(
        source: str,
        issues: List[AccessibilityIssue],
    ) -> None:
        for image in re.findall(r"<img\b([^>]*)>", source, re.I):
            if not re.search(r"\balt\s*=", image, re.I):
                issues.append(
                    AccessibilityIssue(
                        "error",
                        "image-alt",
                        "An img element is missing an alt attribute.",
                    )
                )

    @staticmethod
    def _check_buttons(
        source: str,
        issues: List[AccessibilityIssue],
    ) -> None:
        for button in re.findall(
            r"<button\b([^>]*)>(.*?)</button>",
            source,
            re.I | re.S,
        ):
            attributes, content = button
            name = re.sub(r"<[^>]+>", " ", content).strip()

            if not name and not re.search(r"\baria-label\s*=", attributes, re.I):
                issues.append(
                    AccessibilityIssue(
                        "error",
                        "button-name",
                        "A button appears to have no accessible naming text.",
                    )
                )

    @staticmethod
    def _check_links(
        source: str,
        issues: List[AccessibilityIssue],
    ) -> None:
        for href, content in re.findall(
            r"<a\b[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>",
            source,
            re.I | re.S,
        ):
            name = re.sub(r"<[^>]+>", " ", content).strip()

            if not name:
                issues.append(
                    AccessibilityIssue(
                        "error",
                        "link-name",
                        f"Link '{href}' appears to have no text name.",
                    )
                )

    @staticmethod
    def _check_language(
        source: str,
        issues: List[AccessibilityIssue],
    ) -> None:
        if re.search(r"<html\b", source, re.I):
            if not re.search(r"<html\b[^>]*\blang=", source, re.I):
                issues.append(
                    AccessibilityIssue(
                        "warning",
                        "document-language",
                        "The html element does not declare a language.",
                    )
                )

    @staticmethod
    def _check_title(
        source: str,
        issues: List[AccessibilityIssue],
    ) -> None:
        if re.search(r"<html\b", source, re.I):
            if not re.search(r"<title\b[^>]*>.*?</title>", source, re.I | re.S):
                issues.append(
                    AccessibilityIssue(
                        "warning",
                        "page-title",
                        "No title element was detected.",
                    )
                )

    @staticmethod
    def _check_labels(
        source: str,
        issues: List[AccessibilityIssue],
    ) -> None:
        controls = re.findall(
            r"<input\b([^>]*)>",
            source,
            re.I,
        )

        for attributes in controls:
            input_type = re.search(
                r'\btype=["\']([^"\']+)["\']',
                attributes,
                re.I,
            )

            if input_type and input_type.group(1).lower() == "hidden":
                continue

            if not re.search(
                r"\baria-label\s*=|\baria-labelledby\s*=",
                attributes,
                re.I,
            ):
                control_id = re.search(
                    r'\bid=["\']([^"\']+)["\']',
                    attributes,
                    re.I,
                )

                if not control_id:
                    issues.append(
                        AccessibilityIssue(
                            "warning",
                            "form-label",
                            "An input has no id suitable for a "
                            "for-associated label.",
                        )
                    )

    @staticmethod
    def _check_positive_tabindex(
        source: str,
        issues: List[AccessibilityIssue],
    ) -> None:
        if re.search(r'\btabindex=["\'][1-9]\d*["\']', source, re.I):
            issues.append(
                AccessibilityIssue(
                    "warning",
                    "positive-tabindex",
                    "Positive tabindex values can create a confusing "
                    "custom focus order.",
                )
            )

    @staticmethod
    def _check_aria_hidden_focusable(
        source: str,
        issues: List[AccessibilityIssue],
    ) -> None:
        if re.search(
            r'<(?:button|a|input|select|textarea)\b[^>]*\baria-hidden=["\']true',
            source,
            re.I,
        ):
            issues.append(
                AccessibilityIssue(
                    "error",
                    "aria-hidden-focusable",
                    "A commonly focusable element is marked aria-hidden=true.",
                )
            )


def linter_demo() -> None:
    section("42. Educational accessibility linter")

    source = """
<html>
<head>
</head>
<body>
    <img src="chart.png">

    <button></button>

    <a href="/products"></a>

    <input type="text">

    <div tabindex="2">Custom focus</div>

    <button aria-hidden="true">Hidden action</button>
</body>
</html>
"""

    linter = AccessibilityLinter()
    issues = linter.lint(source)

    for issue in issues:
        print(
            f"[{issue.severity.upper()}] "
            f"{issue.rule}: {issue.message}"
        )

    print(
        "\nAutomated checks are useful, but they cannot determine every "
        "accessibility problem. A page can pass automated checks and still "
        "have poor keyboard behavior, confusing instructions, incorrect "
        "semantics, inaccessible interaction flows, or poor content."
    )


# =============================================================================
# 43. ACCESSIBILITY TESTING PYRAMID
# =============================================================================

def testing_strategy_demo() -> None:
    section("43. Accessibility testing strategy")

    layers = [
        (
            "Static and automated checks",
            "Detect obvious issues such as missing alt attributes, invalid "
            "relationships, contrast problems, and some semantic errors.",
        ),
        (
            "Keyboard testing",
            "Verify every interactive flow without a mouse.",
        ),
        (
            "Screen-reader testing",
            "Verify names, roles, states, reading order, landmarks, headings, "
            "forms, announcements, and interaction behavior.",
        ),
        (
            "Zoom and reflow testing",
            "Check whether enlarged content remains usable and understandable.",
        ),
        (
            "Manual functional testing",
            "Test real workflows rather than isolated elements.",
        ),
        (
            "User testing",
            "People with disabilities can reveal practical barriers that "
            "automated rules and developer assumptions may miss.",
        ),
    ]

    for layer, purpose in layers:
        print(f"\n{layer}\n  {purpose}")


# =============================================================================
# 44. AUTOMATED VERSUS MANUAL TESTING
# =============================================================================

def automated_vs_manual_demo() -> None:
    section("44. Automated testing versus manual testing")

    comparisons = [
        (
            "Missing alt attribute",
            "Often automatable",
            "Still requires contextual review of whether the alt text is appropriate.",
        ),
        (
            "Keyboard operation",
            "Limited automation",
            "Manual interaction is essential.",
        ),
        (
            "Meaningful heading hierarchy",
            "Partly automatable",
            "Human judgment may be required to determine whether the structure is meaningful.",
        ),
        (
            "Color contrast",
            "Often automatable",
            "Context, states, overlays, and visual presentation still require review.",
        ),
        (
            "Correct accessible label",
            "Partly automatable",
            "Human judgment is needed to determine whether the label communicates purpose.",
        ),
    ]

    print(f"{'Problem':35} {'Automation':20} Manual consideration")
    print("-" * 100)

    for problem, automation, manual in comparisons:
        print(f"{problem:35} {automation:20} {manual}")


# =============================================================================
# 45. ACCESSIBILITY REQUIREMENTS IN DESIGN
# =============================================================================

def design_requirements_demo() -> None:
    section("45. Accessibility as a design requirement")

    requirements = [
        "Keyboard operation should be considered before implementation.",
        "Focus behavior should be designed for dialogs, menus, and dynamic views.",
        "Forms should have labels, instructions, validation, and error recovery.",
        "Information should not depend solely on color, sound, animation, or hover.",
        "Content structure should remain meaningful without CSS.",
        "Responsive layouts should remain usable under zoom and reflow.",
        "Interaction states should be communicated visually and semantically.",
    ]

    for requirement in requirements:
        print(f"- {requirement}")


# =============================================================================
# 46. PROGRESSIVE ENHANCEMENT
# =============================================================================

def progressive_enhancement_demo() -> None:
    section("46. Progressive enhancement")

    show_html(
        "A resilient form",
        """
<form action="/search" method="get">
    <label for="query">Search</label>
    <input id="query" name="q" type="search">
    <button type="submit">Search</button>
</form>
""",
    )

    print(
        "\nA basic form can work using ordinary HTML submission. JavaScript "
        "can enhance the experience with asynchronous behavior while "
        "preserving the underlying semantic and interaction model."
    )


# =============================================================================
# 47. SEMANTIC FALLBACK
# =============================================================================

def semantic_fallback_demo() -> None:
    section("47. Semantic fallback and graceful failure")

    print(
        "\nWhen a custom component fails, the user should ideally still have "
        "a meaningful path through the application. Native HTML elements "
        "provide a strong baseline because browsers already understand their "
        "semantics and standard interaction patterns."
    )

    show_html(
        "Strong baseline",
        """
<form>
    <label for="search">Search products</label>
    <input id="search" type="search">
    <button type="submit">Search</button>
</form>
""",
    )


# =============================================================================
# 48. SINGLE-PAGE APPLICATION ACCESSIBILITY
# =============================================================================

def spa_accessibility_demo() -> None:
    section("48. Single-page application considerations")

    print(
        "\nIn a single-page application, changing the URL or visible content "
        "does not necessarily produce the same navigation experience as a "
        "traditional page load."
    )

    print(
        "\nImportant considerations:"
        "\n  - update document.title when views change;"
        "\n  - manage focus after route changes;"
        "\n  - provide a clear page or view heading;"
        "\n  - announce important asynchronous updates;"
        "\n  - preserve meaningful browser history behavior;"
        "\n  - ensure controls remain keyboard accessible."
    )


# =============================================================================
# 49. INFINITE SCROLL
# =============================================================================

def infinite_scroll_demo() -> None:
    section("49. Infinite scrolling")

    print(
        "\nInfinite scrolling can create accessibility challenges because "
        "content appears dynamically, keyboard users may lose context, and "
        "screen-reader users may not understand what changed."
    )

    print(
        "\nA robust implementation should consider:"
        "\n  - a meaningful loading status;"
        "\n  - stable focus;"
        "\n  - predictable document order;"
        "\n  - an accessible alternative to endless scrolling when appropriate;"
        "\n  - preserving user position when content is inserted."
    )


# =============================================================================
# 50. DRAG AND DROP
# =============================================================================

def drag_and_drop_demo() -> None:
    section("50. Drag-and-drop accessibility")

    print(
        "\nDrag-and-drop should not be the only way to perform an operation. "
        "Provide an alternative interaction such as buttons, menus, or "
        "keyboard-operable controls."
    )

    show_html(
        "Alternative action controls",
        """
<button type="button">Move item up</button>
<button type="button">Move item down</button>
""",
    )


# =============================================================================
# 51. TOOLTIP CONSIDERATIONS
# =============================================================================

def tooltip_demo() -> None:
    section("51. Tooltips")

    print(
        "\nA tooltip should not be the only place where essential information "
        "is communicated. Hover-only behavior excludes keyboard and touch "
        "users."
    )

    show_html(
        "Visible explanatory text",
        """
<label for="tax-id">
    Tax identification number
</label>
<p id="tax-id-help">
    Enter the number exactly as it appears on your tax document.
</p>

<input
    id="tax-id"
    aria-describedby="tax-id-help">
""",
    )


# =============================================================================
# 52. PLACEHOLDERS
# =============================================================================

def placeholder_demo() -> None:
    section("52. Placeholder text")

    show_html(
        "Do not use placeholder as the only label",
        """
<input
    type="email"
    placeholder="Email address">
""",
    )

    show_html(
        "Use a label plus optional placeholder",
        """
<label for="email">Email address</label>
<input
    id="email"
    type="email"
    placeholder="name@example.com">
""",
    )

    print(
        "\nPlaceholder text can disappear during typing and can have weaker "
        "visual contrast. It should supplement, not replace, a persistent "
        "label."
    )


# =============================================================================
# 53. AUTOPLAY AND TIMING
# =============================================================================

def timing_demo() -> None:
    section("53. Timing and autoplay")

    print(
        "\nInterfaces that automatically advance, expire, disappear, or "
        "refresh can create accessibility problems."
    )

    print(
        "\nRelevant design questions:"
        "\n  - Can users pause or stop moving content?"
        "\n  - Is there enough time to complete an interaction?"
        "\n  - Will session expiration warn the user?"
        "\n  - Can users extend time when appropriate?"
        "\n  - Does an automatic update move keyboard focus unexpectedly?"
    )


# =============================================================================
# 54. AUTHENTICATION
# =============================================================================

def authentication_accessibility_demo() -> None:
    section("54. Accessible authentication")

    print(
        "\nAuthentication flows should avoid unnecessary cognitive or motor "
        "barriers. Interfaces should provide accessible labels, error "
        "messages, predictable focus, and appropriate input semantics."
    )

    show_html(
        "Accessible sign-in structure",
        """
<form>
    <h1>Sign in</h1>

    <label for="username">Username</label>
    <input
        id="username"
        name="username"
        autocomplete="username">

    <label for="password">Password</label>
    <input
        id="password"
        name="password"
        type="password"
        autocomplete="current-password">

    <button type="submit">Sign in</button>
</form>
""",
    )


# =============================================================================
# 55. INTERNATIONALIZATION
# =============================================================================

def internationalization_demo() -> None:
    section("55. Internationalization and accessibility")

    print(
        "\nAccessibility and internationalization often intersect through "
        "language identification, text direction, date formats, labels, "
        "number formats, and culturally understandable instructions."
    )

    show_html(
        "Right-to-left language example",
        """
<html lang="ar" dir="rtl">
    ...
</html>
""",
    )


# =============================================================================
# 56. ACCESSIBLE CSS
# =============================================================================

def accessible_css_demo() -> None:
    section("56. Accessible CSS practices")

    show_html(
        "Avoid removing focus",
        """
/* Avoid this when no equivalent focus indicator exists. */
button:focus {
    outline: none;
}
""",
    )

    show_html(
        "Support forced colors",
        """
@media (forced-colors: active) {
    button,
    input,
    select {
        border: 1px solid ButtonText;
    }
}
""",
    )

    print(
        "\nCSS should preserve distinguishability, focus visibility, text "
        "readability, responsive behavior, and state information. Styling "
        "should not destroy native semantics or make interaction dependent "
        "on hover alone."
    )


# =============================================================================
# 57. VISUAL VERSUS SEMANTIC STATE
# =============================================================================

def visual_semantic_state_demo() -> None:
    section("57. Visual state versus semantic state")

    states = [
        ("Accordion open", "aria-expanded=true"),
        ("Accordion closed", "aria-expanded=false"),
        ("Toggle pressed", "aria-pressed=true"),
        ("Checkbox checked", "aria-checked=true"),
        ("Tab selected", "aria-selected=true"),
        ("Invalid input", "aria-invalid=true"),
    ]

    for visual_state, semantic_state in states:
        print(f"{visual_state:25} -> {semantic_state}")


# =============================================================================
# 58. LIVE CONTENT AND FOCUS
# =============================================================================

def async_update_demo() -> None:
    section("58. Asynchronous updates")

    show_html(
        "Search status",
        """
<form>
    <label for="search">Search courses</label>
    <input id="search" type="search">
    <button type="submit">Search</button>
</form>

<p id="status" role="status" aria-live="polite">
    12 results found.
</p>
""",
    )

    print(
        "\nThe application should not unnecessarily steal focus when a "
        "background update occurs. A status message can communicate relevant "
        "changes without moving the user's focus."
    )


# =============================================================================
# 59. ERROR PREVENTION
# =============================================================================

def error_prevention_demo() -> None:
    section("59. Error prevention")

    print(
        "\nFor important submissions, interfaces can reduce errors by:"
        "\n  - clearly labeling fields;"
        "\n  - preserving entered information after validation;"
        "\n  - allowing review before final submission;"
        "\n  - providing confirmation of critical values;"
        "\n  - making destructive actions explicit."
    )


# =============================================================================
# 60. ACCESSIBILITY AND SECURITY
# =============================================================================

def security_considerations_demo() -> None:
    section("60. Accessibility and security considerations")

    print(
        "\nAccessibility and security can interact in important ways."
    )

    print(
        "\nExamples:"
        "\n  - Do not expose sensitive information through unnecessarily "
        "verbose live announcements."
        "\n  - Error messages should explain correction without revealing "
        "security-sensitive details."
        "\n  - Authentication challenges should have accessible alternatives "
        "when appropriate."
        "\n  - Avoid relying on inaccessible client-side controls for security."
        "\n  - Server-side authorization must remain independent of accessibility "
        "attributes such as aria-disabled."
    )

    show_html(
        "Important distinction",
        """
<button aria-disabled="true">Submit</button>
""",
    )

    print(
        "\naria-disabled communicates an accessibility state. It is not a "
        "security mechanism. Server-side authorization and validation must "
        "still enforce actual permissions and business rules."
    )


# =============================================================================
# 61. PERFORMANCE AND ACCESSIBILITY
# =============================================================================

def performance_demo() -> None:
    section("61. Performance and accessibility")

    print(
        "\nPerformance affects accessibility because delays can increase "
        "cognitive and interaction burden, especially for users with slower "
        "connections, older devices, assistive technologies, or cognitive "
        "constraints."
    )

    print(
        "\nUseful practices:"
        "\n  - avoid unnecessary client-side work;"
        "\n  - provide meaningful loading states;"
        "\n  - preserve focus during asynchronous operations;"
        "\n  - avoid huge DOM trees when they are unnecessary;"
        "\n  - do not repeatedly announce trivial updates."
    )


# =============================================================================
# 62. COMMON MISTAKES
# =============================================================================

COMMON_MISTAKES = [
    (
        "Using div elements as buttons",
        "Use native button elements whenever the control performs an action.",
    ),
    (
        "Using placeholder as a label",
        "Provide an actual label associated with the form control.",
    ),
    (
        "Removing focus outlines",
        "Provide an equally visible focus indicator.",
    ),
    (
        "Using color alone",
        "Provide text, icons, patterns, labels, or other redundant cues.",
    ),
    (
        "Adding ARIA everywhere",
        "Prefer native HTML semantics and add ARIA only when needed.",
    ),
    (
        "Using aria-hidden on focusable content",
        "Keep focusable content represented in the accessibility tree.",
    ),
    (
        "Using positive tabindex values",
        "Prefer native order and tabindex=0 or -1 when appropriate.",
    ),
    (
        "Creating hover-only interactions",
        "Ensure equivalent keyboard and touch access.",
    ),
    (
        "Ignoring focus after route changes",
        "Move or preserve focus intentionally so the new view is understandable.",
    ),
    (
        "Treating automated tests as proof of accessibility",
        "Combine automated, keyboard, screen-reader, and human testing.",
    ),
]


def common_mistakes_demo() -> None:
    section("62. Common accessibility mistakes")

    for mistake, correction in COMMON_MISTAKES:
        print(f"\nMistake: {mistake}")
        print(f"Better approach: {correction}")


# =============================================================================
# 63. NATIVE HTML DECISION TREE
# =============================================================================

def native_html_decision_tree() -> None:
    section("63. Choosing native HTML before ARIA")

    questions = [
        "Does HTML already have an element for this control?",
        "Does that element provide the required keyboard behavior?",
        "Does the browser expose the required semantics automatically?",
        "Can CSS provide the desired visual appearance without changing semantics?",
        "If native HTML cannot meet the requirement, is a standard ARIA pattern appropriate?",
    ]

    for number, question in enumerate(questions, start=1):
        print(f"{number}. {question}")

    print(
        "\nThe design principle is to minimize custom accessibility behavior "
        "when a native element already provides the needed functionality."
    )


# =============================================================================
# 64. CUSTOM WIDGET RESPONSIBILITIES
# =============================================================================

CUSTOM_WIDGET_RESPONSIBILITIES = [
    "Accessible name",
    "Role",
    "State",
    "Properties",
    "Keyboard behavior",
    "Pointer behavior",
    "Focus management",
    "Visible focus",
    "Disabled state",
    "Dynamic announcements when necessary",
    "Correct relationships between controls and content",
    "Responsive behavior",
]


def custom_widget_demo() -> None:
    section("64. Responsibilities of a custom widget")

    for responsibility in CUSTOM_WIDGET_RESPONSIBILITIES:
        print(f"- {responsibility}")


# =============================================================================
# 65. ACCESSIBILITY ACCEPTANCE CRITERIA
# =============================================================================

def acceptance_criteria_demo() -> None:
    section("65. Accessibility acceptance criteria")

    criteria = [
        "Every interactive control has an accessible name.",
        "All functionality is operable using keyboard input.",
        "Keyboard focus is visible.",
        "Focus order is logical.",
        "Dialogs manage focus correctly.",
        "Form controls have appropriate labels.",
        "Validation errors are understandable and associated with controls.",
        "Images have contextually appropriate alternatives.",
        "Headings and landmarks form meaningful structure.",
        "Dynamic state changes are exposed to assistive technology.",
        "Color is not the only means of conveying meaning.",
        "Content remains usable under zoom and responsive reflow.",
    ]

    for criterion in criteria:
        print(f"[ ] {criterion}")


# =============================================================================
# 66. CODE REVIEW CHECKLIST
# =============================================================================

def code_review_checklist() -> None:
    section("66. Accessibility code-review checklist")

    checklist = {
        "HTML":
            "Are semantic elements used instead of generic containers?",
        "Navigation":
            "Are major navigation areas labeled and logically structured?",
        "Forms":
            "Does every relevant control have a proper accessible label?",
        "Keyboard":
            "Can every interaction be completed without a mouse?",
        "Focus":
            "Is focus visible and intentionally managed?",
        "ARIA":
            "Is ARIA necessary, correct, and synchronized with state?",
        "Images":
            "Does every meaningful image have an appropriate text alternative?",
        "Content":
            "Are headings, lists, tables, and language metadata meaningful?",
        "Errors":
            "Can users identify and correct errors?",
        "Dynamic updates":
            "Are important updates communicated without unnecessary focus changes?",
    }

    for area, question in checklist.items():
        print(f"{area:18}: {question}")


# =============================================================================
# 67. SMALL END-TO-END ACCESSIBLE PAGE
# =============================================================================

ACCESSIBLE_PAGE = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Course search | Example University</title>
</head>
<body>
    <a href="#main-content">Skip to main content</a>

    <header>
        <nav aria-label="Primary">
            <a href="/">Home</a>
            <a href="/courses" aria-current="page">Courses</a>
            <a href="/contact">Contact</a>
        </nav>
    </header>

    <main id="main-content">
        <h1>Course search</h1>

        <form action="/courses" method="get">
            <label for="course-search">Search courses</label>
            <input
                id="course-search"
                name="q"
                type="search"
                autocomplete="off">

            <button type="submit">Search</button>
        </form>

        <p id="results-status" role="status">
            12 courses found.
        </p>

        <section aria-labelledby="results-heading">
            <h2 id="results-heading">Search results</h2>

            <article>
                <h3>Python fundamentals</h3>
                <p>Learn core Python programming concepts.</p>
                <a href="/courses/python">View course</a>
            </article>
        </section>
    </main>

    <footer>
        <p>Example University</p>
    </footer>
</body>
</html>
""".strip()


def end_to_end_demo() -> None:
    section("67. End-to-end accessible HTML page")

    print(ACCESSIBLE_PAGE)

    print(
        "\nImportant properties of this example:"
        "\n  - language is declared;"
        "\n  - viewport is configured;"
        "\n  - page title is meaningful;"
        "\n  - skip navigation is available;"
        "\n  - navigation uses nav;"
        "\n  - current page is communicated;"
        "\n  - main content has a unique landmark;"
        "\n  - headings describe structure;"
        "\n  - form input has a label;"
        "\n  - native button behavior is used;"
        "\n  - asynchronous result information has a status role;"
        "\n  - article content is self-contained."
    )


# =============================================================================
# 68. END-TO-END LINT
# =============================================================================

def end_to_end_lint_demo() -> None:
    section("68. Linting the example page")

    linter = AccessibilityLinter()
    issues = linter.lint(ACCESSIBLE_PAGE)

    if not issues:
        print("No issues were detected by this small educational linter.")
    else:
        for issue in issues:
            print(issue)


# =============================================================================
# 69. EDGE CASES
# =============================================================================

def edge_cases_demo() -> None:
    section("69. Accessibility edge cases")

    edge_cases = [
        (
            "Icon-only button",
            "The icon needs an accessible name unless meaningful visible "
            "text already names the button.",
        ),
        (
            "Decorative SVG",
            "It can often be excluded from the accessibility tree when it "
            "adds no useful information.",
        ),
        (
            "Clickable card",
            "Do not make a large generic container clickable when a semantic "
            "link or button can express the actual action.",
        ),
        (
            "Disabled control",
            "Native disabled semantics and aria-disabled have different "
            "behavior and should not be treated as interchangeable.",
        ),
        (
            "Visually hidden content",
            "Content hidden only visually may remain available to assistive "
            "technology depending on the technique used.",
        ),
        (
            "Multiple nav regions",
            "Give multiple navigation landmarks distinguishing accessible "
            "names when users need to differentiate them.",
        ),
        (
            "Repeated headings",
            "Repeated heading text is not automatically wrong. Context and "
            "structure determine whether it is understandable.",
        ),
        (
            "Dynamic validation",
            "Do not move focus unexpectedly for every small validation update.",
        ),
    ]

    for title, explanation in edge_cases:
        print(f"\n{title}")
        print(f"  {explanation}")


# =============================================================================
# 70. ARIA STATE TABLE
# =============================================================================

ARIA_STATES = {
    "aria-expanded": "Whether a controlled expandable element is expanded.",
    "aria-pressed": "Whether a toggle button is currently pressed.",
    "aria-checked": "Checked state for applicable widgets.",
    "aria-selected": "Selection state for applicable composite widgets.",
    "aria-current": "Identifies the current item in a set, such as current page.",
    "aria-disabled": "Communicates that an element is disabled.",
    "aria-invalid": "Communicates that an input value fails validation.",
    "aria-busy": "Communicates that an area is currently being updated.",
    "aria-hidden": "Requests exclusion from the accessibility tree.",
}


def aria_state_table_demo() -> None:
    section("70. Important ARIA states and properties")

    for attribute, meaning in ARIA_STATES.items():
        print(f"{attribute:20} {meaning}")


# =============================================================================
# 71. ACCESSIBLE RELATIONSHIPS
# =============================================================================

RELATIONSHIPS = {
    "for -> id":
        "Associates a label with a form control.",
    "aria-labelledby -> id":
        "References content used to provide an accessible name.",
    "aria-describedby -> id":
        "References content providing additional description.",
    "aria-controls -> id":
        "Indicates that a control affects another interface object.",
    "aria-owns -> id":
        "Can express ownership relationships, but should not be used "
        "casually when ordinary DOM structure is sufficient.",
}


def relationships_demo() -> None:
    section("71. Accessible relationships")

    for relationship, meaning in RELATIONSHIPS.items():
        print(f"{relationship}\n  {meaning}")


# =============================================================================
# 72. DISABLED STATES
# =============================================================================

def disabled_state_demo() -> None:
    section("72. Disabled controls")

    show_html(
        "Native disabled control",
        """
<button type="button" disabled>
    Submit
</button>
""",
    )

    show_html(
        "ARIA-disabled custom or conditionally interactive control",
        """
<div
    role="button"
    tabindex="0"
    aria-disabled="true">
    Submit
</div>
""",
    )

    print(
        "\nThe native disabled attribute affects browser interaction behavior. "
        "aria-disabled communicates state but does not automatically prevent "
        "activation. Application logic must enforce the intended behavior."
    )


# =============================================================================
# 73. CURRENT PAGE
# =============================================================================

def current_page_demo() -> None:
    section("73. aria-current and current navigation")

    show_html(
        "Current page",
        """
<nav aria-label="Primary">
    <a href="/">Home</a>
    <a href="/courses" aria-current="page">Courses</a>
    <a href="/contact">Contact</a>
</nav>
""",
    )

    print(
        "\naria-current is useful for identifying the current item in a set. "
        "It should represent actual current state rather than being added "
        "merely as decoration."
    )


# =============================================================================
# 74. LANGUAGE AND DIRECTION EDGE CASE
# =============================================================================

def direction_demo() -> None:
    section("74. Text direction")

    show_html(
        "Bidirectional content",
        """
<p dir="ltr">English content</p>
<p dir="rtl">محتوى عربي</p>
""",
    )

    print(
        "\nLanguage and direction metadata can be important when content "
        "mixes scripts or languages. Direction should follow the actual "
        "content rather than visual assumptions."
    )


# =============================================================================
# 75. DOCUMENT OUTLINE ANALYSIS
# =============================================================================

def analyze_heading_levels(headings: Sequence[Heading]) -> List[str]:
    warnings = []

    previous_level = None

    for heading in headings:
        if previous_level is not None:
            if heading.level > previous_level + 1:
                warnings.append(
                    f"H{heading.level} follows H{previous_level}; "
                    "review whether the hierarchy is intentional."
                )

        previous_level = heading.level

    return warnings


def heading_analysis_demo() -> None:
    section("75. Heading hierarchy analysis")

    headings = [
        Heading(1, "Dashboard"),
        Heading(2, "Revenue"),
        Heading(4, "Monthly revenue"),
        Heading(2, "Users"),
    ]

    print("\n".join(heading_outline(headings)))

    for warning in analyze_heading_levels(headings):
        print("Warning:", warning)

    print(
        "\nThis check is a heuristic. Heading level analysis cannot by itself "
        "determine whether a page's information architecture is correct."
    )


# =============================================================================
# 76. LIST SEMANTICS
# =============================================================================

def list_semantics_demo() -> None:
    section("76. Lists")

    show_html(
        "Navigation list",
        """
<ul>
    <li><a href="/home">Home</a></li>
    <li><a href="/courses">Courses</a></li>
    <li><a href="/contact">Contact</a></li>
</ul>
""",
    )

    show_html(
        "Ordered procedure",
        """
<ol>
    <li>Create an account.</li>
    <li>Verify your email.</li>
    <li>Submit the application.</li>
</ol>
""",
    )

    print(
        "\nUse ul when order is not meaningful and ol when sequence matters. "
        "Semantic list structure gives assistive technology useful grouping "
        "and item-count information."
    )


# =============================================================================
# 77. QUOTES AND ABBREVIATIONS
# =============================================================================

def text_semantics_demo() -> None:
    section("77. Text semantics")

    show_html(
        "Semantic text elements",
        """
<p>
    The <abbr title="World Wide Web Consortium">W3C</abbr>
    publishes web standards.
</p>

<blockquote cite="https://example.com/source">
    An important quotation.
</blockquote>

<p>
    Press <kbd>Ctrl</kbd> + <kbd>S</kbd> to save.
</p>
""",
    )

    print(
        "\nSemantic text elements can provide additional information to user "
        "agents and improve the structural meaning of content."
    )


# =============================================================================
# 78. IFRAME ACCESSIBILITY
# =============================================================================

def iframe_demo() -> None:
    section("78. Embedded content")

    show_html(
        "Named iframe",
        """
<iframe
    title="University campus map"
    src="/campus-map">
</iframe>
""",
    )

    print(
        "\nEmbedded browsing contexts should have a meaningful title when "
        "users need to understand what the frame contains."
    )


# =============================================================================
# 79. SVG ACCESSIBILITY
# =============================================================================

def svg_demo() -> None:
    section("79. SVG accessibility")

    show_html(
        "Decorative SVG",
        """
<button type="button">
    <svg aria-hidden="true" focusable="false">
        ...
    </svg>
    Delete
</button>
""",
    )

    show_html(
        "Informative SVG",
        """
<svg role="img" aria-labelledby="chart-title">
    <title id="chart-title">Revenue increased by 15 percent.</title>
    ...
</svg>
""",
    )

    print(
        "\nWhether an SVG should be exposed as meaningful content depends on "
        "its purpose and context."
    )


# =============================================================================
# 80. CANVAS CONSIDERATIONS
# =============================================================================

def canvas_demo() -> None:
    section("80. Canvas considerations")

    show_html(
        "Canvas fallback content",
        """
<canvas>
    Your browser does not support the canvas element.
</canvas>
""",
    )

    print(
        "\nCanvas is a drawing surface rather than a semantic document. "
        "Interactive canvas applications require careful accessible "
        "alternatives or an equivalent semantic interface."
    )


# =============================================================================
# 81. ACCESSIBILITY API CONCEPT
# =============================================================================

def accessibility_api_demo() -> None:
    section("81. Accessibility APIs")

    platforms = {
        "Windows": "Accessibility technologies interact through platform "
                   "accessibility mechanisms such as UI Automation.",
        "macOS/iOS": "Accessibility technologies interact through Apple's "
                     "accessibility frameworks.",
        "Linux": "Accessibility commonly involves technologies such as AT-SPI.",
        "Web": "Browsers map DOM and accessibility semantics into platform "
                "accessibility interfaces used by assistive technologies.",
    }

    for platform, description in platforms.items():
        print(f"{platform}: {description}")

    print(
        "\nThe exact accessibility API differs by operating system and "
        "browser. Web developers generally work with HTML semantics, ARIA, "
        "CSS, and browser behavior rather than directly programming each "
        "platform accessibility API."
    )


# =============================================================================
# 82. ACCESSIBILITY TREE VERSUS DOM
# =============================================================================

def dom_vs_accessibility_tree_demo() -> None:
    section("82. DOM versus accessibility tree")

    print(
        "\nThe DOM contains the document's elements and structure. The "
        "accessibility tree is a related representation optimized for "
        "communication with accessibility services."
    )

    print(
        "\nConsequences:"
        "\n  - visually hidden or CSS-hidden elements may be absent;"
        "\n  - aria-hidden can remove information from the accessibility tree;"
        "\n  - accessible names may differ from raw DOM text;"
        "\n  - CSS and browser state can affect exposure;"
        "\n  - semantic HTML can produce useful roles automatically."
    )


# =============================================================================
# 83. ACCESSIBILITY TREE SIMULATION
# =============================================================================

def build_simple_tree() -> Dict[str, object]:
    return {
        "role": "main",
        "name": "",
        "children": [
            {
                "role": "heading",
                "name": "Account",
            },
            {
                "role": "textbox",
                "name": "Email address",
            },
            {
                "role": "button",
                "name": "Save changes",
            },
        ],
    }


def print_tree(node: Dict[str, object], depth: int = 0) -> None:
    role = node.get("role", "unknown")
    name = node.get("name", "")

    print(
        "  " * depth
        + role
        + (f' "{name}"' if name else "")
    )

    children = node.get("children", [])

    if isinstance(children, list):
        for child in children:
            if isinstance(child, dict):
                print_tree(child, depth + 1)


def tree_simulation_demo() -> None:
    section("83. Simplified accessibility-tree simulation")

    tree = build_simple_tree()
    print_tree(tree)


# =============================================================================
# 84. TESTING A KEYBOARD FLOW
# =============================================================================

def test_keyboard_flow(
    controls: Sequence[str],
    expected_order: Sequence[str],
) -> bool:
    return list(controls) == list(expected_order)


def keyboard_test_demo() -> None:
    section("84. Testing keyboard order")

    actual = [
        "Skip link",
        "Primary navigation",
        "Search",
        "Main content controls",
    ]

    expected = [
        "Skip link",
        "Primary navigation",
        "Search",
        "Main content controls",
    ]

    passed = test_keyboard_flow(actual, expected)

    print("Expected:", expected)
    print("Actual:  ", actual)
    print("Passed:  ", passed)


# =============================================================================
# 85. TESTING ACCESSIBLE STATES
# =============================================================================

def test_toggle_state() -> bool:
    button = AccessibleButton("Notifications")

    if button.pressed:
        return False

    button.activate()

    if not button.pressed:
        return False

    return button.html().find('aria-pressed="true"') != -1


def state_test_demo() -> None:
    section("85. Testing semantic state synchronization")

    print("Toggle state test:", "PASS" if test_toggle_state() else "FAIL")


# =============================================================================
# 86. UNIT TEST STYLE ASSERTIONS
# =============================================================================

def accessibility_assertions() -> None:
    section("86. Basic assertions")

    good_html = """
<label for="email">Email address</label>
<input id="email" type="email">
"""

    assert not validate_label_association(good_html)

    assert contrast_ratio((0, 0, 0), (255, 255, 255)) > 20

    assert test_toggle_state()

    print("All educational assertions passed.")


# =============================================================================
# 87. WCAG-STYLE ISSUE CLASSIFICATION
# =============================================================================

@dataclass
class AccessibilityFinding:
    principle: str
    impact: str
    example: str
    remediation: str


FINDINGS = [
    AccessibilityFinding(
        "Perceivable",
        "High",
        "Meaningful image has no text alternative.",
        "Provide contextually appropriate alternative text.",
    ),
    AccessibilityFinding(
        "Operable",
        "High",
        "Custom dialog cannot be operated with keyboard.",
        "Implement keyboard interaction and focus management.",
    ),
    AccessibilityFinding(
        "Understandable",
        "Medium",
        "Validation error does not identify the invalid field.",
        "Associate a clear error message with the affected control.",
    ),
    AccessibilityFinding(
        "Robust",
        "High",
        "Custom widget exposes an incorrect role or state.",
        "Use native HTML or implement a valid ARIA pattern correctly.",
    ),
]


def findings_demo() -> None:
    section("87. Classifying accessibility findings")

    for finding in FINDINGS:
        print(f"\nPrinciple: {finding.principle}")
        print(f"Impact: {finding.impact}")
        print(f"Example: {finding.example}")
        print(f"Remediation: {finding.remediation}")


# =============================================================================
# 88. ACCESSIBILITY DEBT
# =============================================================================

def accessibility_debt_demo() -> None:
    section("88. Accessibility debt")

    print(
        "\nAccessibility debt is the accumulated cost of accessibility "
        "problems that are postponed during product development."
    )

    print(
        "\nExamples include:"
        "\n  - custom controls with no keyboard support;"
        "\n  - inconsistent heading structures;"
        "\n  - missing form labels;"
        "\n  - inaccessible dialogs;"
        "\n  - inaccessible legacy navigation;"
        "\n  - state information represented only visually."
    )

    print(
        "\nAddressing accessibility during design and implementation is "
        "usually less expensive than retrofitting complex interaction "
        "components after production."
    )


# =============================================================================
# 89. COMPONENT DESIGN
# =============================================================================

@dataclass
class ComponentContract:
    name: str
    role: str
    accessible_name_source: str
    keyboard_behavior: str
    state: str


def component_contract_demo() -> None:
    section("89. Accessible component contracts")

    contract = ComponentContract(
        name="Disclosure",
        role="button",
        accessible_name_source="Visible button text",
        keyboard_behavior="Enter or Space activates the native button",
        state="aria-expanded reflects whether controlled content is open",
    )

    print(f"Component: {contract.name}")
    print(f"Role: {contract.role}")
    print(f"Name: {contract.accessible_name_source}")
    print(f"Keyboard: {contract.keyboard_behavior}")
    print(f"State: {contract.state}")


# =============================================================================
# 90. ACCESSIBILITY DESIGN SYSTEM
# =============================================================================

def design_system_demo() -> None:
    section("90. Accessibility in a design system")

    components = [
        "Button",
        "Link",
        "Text input",
        "Select",
        "Checkbox",
        "Radio group",
        "Dialog",
        "Disclosure",
        "Tabs",
        "Tooltip",
        "Alert",
        "Status message",
        "Navigation",
    ]

    for component in components:
        print(
            f"{component}: define semantics, naming, keyboard behavior, "
            "focus, states, error behavior, and responsive behavior."
        )


# =============================================================================
# 91. REGRESSION TESTING
# =============================================================================

def regression_testing_demo() -> None:
    section("91. Accessibility regression testing")

    print(
        "\nAccessibility should be treated as a regression-sensitive quality "
        "attribute. A previously accessible component can become inaccessible "
        "after visual redesign, refactoring, routing changes, or introduction "
        "of custom interaction."
    )

    regression_cases = [
        "Button text changed but accessible name was lost.",
        "Focus outline disappeared after CSS refactoring.",
        "Dialog opens but focus remains behind it.",
        "Route changes but focus remains on an obsolete control.",
        "ARIA state is no longer synchronized with component state.",
        "Form error rendering broke the label relationship.",
    ]

    for case in regression_cases:
        print(f"- {case}")


# =============================================================================
# 92. ACCESSIBILITY PERFORMANCE TRADE-OFFS
# =============================================================================

def accessibility_tradeoffs_demo() -> None:
    section("92. Accessibility trade-offs")

    tradeoffs = [
        (
            "Custom widget",
            "Can provide specialized interaction",
            "Requires more accessibility implementation and testing",
        ),
        (
            "Animation",
            "Can communicate state or improve visual feedback",
            "Can create motion sensitivity or distraction",
        ),
        (
            "Automatic announcements",
            "Can inform users of dynamic changes",
            "Too many announcements can interrupt users",
        ),
        (
            "Client-side routing",
            "Can provide fast transitions",
            "Requires deliberate title and focus management",
        ),
        (
            "Visual simplification",
            "Can reduce clutter",
            "Removing visible context can harm comprehension",
        ),
    ]

    for feature, benefit, cost in tradeoffs:
        print(f"\n{feature}")
        print(f"  Benefit: {benefit}")
        print(f"  Accessibility cost: {cost}")


# =============================================================================
# 93. SEMANTIC HTML GENERATOR
# =============================================================================

@dataclass
class Course:
    title: str
    description: str
    url: str


def render_course_article(course: Course) -> str:
    return f"""
<article>
    <h2>{html.escape(course.title)}</h2>
    <p>{html.escape(course.description)}</p>
    <a href="{html.escape(course.url)}">
        View {html.escape(course.title)}
    </a>
</article>
""".strip()


def semantic_generator_demo() -> None:
    section("93. Generating semantic HTML")

    courses = [
        Course(
            "Python Fundamentals",
            "Variables, conditions, loops, functions, and data structures.",
            "/courses/python",
        ),
        Course(
            "SQL Fundamentals",
            "Queries, filtering, joins, aggregation, and database concepts.",
            "/courses/sql",
        ),
    ]

    for course in courses:
        print(render_course_article(course))
        print()


# =============================================================================
# 94. ESCAPING USER CONTENT
# =============================================================================

def safe_html_text(value: str) -> str:
    """
    Escape text before placing it into an HTML text context.

    This demonstrates a security practice that also matters when generating
    accessible markup from user-controlled content.
    """
    return html.escape(value, quote=True)


def html_escaping_demo() -> None:
    section("94. Security when generating accessible HTML")

    user_text = '<img src=x onerror="alert(1)">'

    print("Original:", user_text)
    print("Escaped:", safe_html_text(user_text))

    print(
        "\nAccessibility attributes and semantic markup do not make untrusted "
        "HTML safe. User-controlled content must still be handled according "
        "to the appropriate output-encoding and sanitization strategy."
    )


# =============================================================================
# 95. ACCESSIBLE URL AND LINK TEXT
# =============================================================================

def link_text_demo() -> None:
    section("95. Meaningful link text")

    show_html(
        "Weak link text",
        """
<a href="/report">Click here</a>
""",
    )

    show_html(
        "Meaningful link text",
        """
<a href="/report">Download the annual accessibility report</a>
""",
    )

    print(
        "\nLink text should communicate the destination or purpose. This "
        "becomes especially important when users navigate through a list of "
        "links without reading the surrounding paragraph."
    )


# =============================================================================
# 96. CURRENT STATE OF CONTROLS
# =============================================================================

def current_state_demo() -> None:
    section("96. Communicating current state")

    show_html(
        "Current page state",
        """
<a href="/dashboard" aria-current="page">Dashboard</a>
""",
    )

    show_html(
        "Expanded state",
        """
<button
    type="button"
    aria-expanded="true"
    aria-controls="filters">
    Filters
</button>
""",
    )

    show_html(
        "Selected state",
        """
<button
    role="tab"
    aria-selected="true"
    aria-controls="profile-panel">
    Profile
</button>
""",
    )


# =============================================================================
# 97. ACCESSIBLE ALERTS
# =============================================================================

def alert_demo() -> None:
    section("97. Alerts and status messages")

    show_html(
        "Important alert",
        """
<div role="alert">
    Your payment could not be processed.
</div>
""",
    )

    show_html(
        "Non-interruptive status",
        """
<div role="status">
    Your profile has been saved.
</div>
""",
    )

    print(
        "\nThe distinction is important. Alerts are intended for important "
        "messages that may require prompt attention, while status messages "
        "are generally less disruptive."
    )


# =============================================================================
# 98. ACCESSIBLE SEARCH
# =============================================================================

def search_demo() -> None:
    section("98. Accessible search")

    show_html(
        "Search form",
        """
<form role="search" action="/search" method="get">
    <label for="site-search">Search this site</label>
    <input id="site-search" name="q" type="search">
    <button type="submit">Search</button>
</form>
""",
    )

    print(
        "\nThe search landmark can help users identify the purpose of the "
        "form. Native search input semantics can also provide useful "
        "platform and browser behavior."
    )


# =============================================================================
# 99. ACCESSIBLE FOOTER
# =============================================================================

def footer_demo() -> None:
    section("99. Footer semantics")

    show_html(
        "Footer with navigation",
        """
<footer>
    <nav aria-label="Footer">
        <a href="/privacy">Privacy</a>
        <a href="/terms">Terms</a>
        <a href="/contact">Contact</a>
    </nav>
</footer>
""",
    )


# =============================================================================
# 100. PRODUCTION ACCESSIBILITY WORKFLOW
# =============================================================================

def production_workflow_demo() -> None:
    section("100. Production accessibility workflow")

    workflow = [
        "Define accessibility requirements during discovery.",
        "Use semantic HTML during implementation.",
        "Design keyboard and focus behavior for interactive components.",
        "Define accessible names, roles, states, and relationships.",
        "Test forms and validation states.",
        "Run automated checks.",
        "Perform keyboard-only testing.",
        "Perform screen-reader testing.",
        "Test zoom, reflow, responsive layouts, and motion preferences.",
        "Record accessibility defects with reproducible steps.",
        "Fix regressions as part of normal development.",
        "Include accessibility in acceptance criteria and release review.",
    ]

    for number, step in enumerate(workflow, start=1):
        print(f"{number:2}. {step}")


# =============================================================================
# 101. COMPLETE CHECKLIST
# =============================================================================

def complete_accessibility_checklist() -> Dict[str, List[str]]:
    return {
        "Structure": [
            "Document language declared",
            "Meaningful page title",
            "Logical headings",
            "Semantic landmarks",
            "Logical source order",
        ],
        "Navigation": [
            "Keyboard navigation works",
            "Focus is visible",
            "Skip link available when appropriate",
            "Current navigation state communicated",
            "No unexpected focus traps",
        ],
        "Forms": [
            "Labels associated with controls",
            "Instructions available when needed",
            "Required state communicated",
            "Errors identified clearly",
            "Errors associated with affected controls",
        ],
        "Images and media": [
            "Meaningful images have suitable alternatives",
            "Decorative images are appropriately ignored",
            "Video has relevant captions",
            "Audio/video has appropriate text alternatives",
        ],
        "ARIA": [
            "Native HTML considered first",
            "Roles are valid",
            "States are synchronized",
            "ARIA relationships reference existing content",
            "Focusable content is not incorrectly aria-hidden",
        ],
        "Responsive behavior": [
            "Content remains usable when enlarged",
            "No important information depends only on hover",
            "Touch and keyboard interaction remain usable",
            "Motion preferences are respected where applicable",
        ],
        "Testing": [
            "Automated checks performed",
            "Keyboard testing performed",
            "Screen-reader testing performed",
            "Real workflows tested",
            "Accessibility regressions covered",
        ],
    }


def print_complete_checklist() -> None:
    section("101. Complete accessibility checklist")

    checklist = complete_accessibility_checklist()

    for category, items in checklist.items():
        print(f"\n{category}")
        for item in items:
            print(f"  [ ] {item}")


# =============================================================================
# 102. PRACTICAL MINI TEST SUITE
# =============================================================================

def run_practical_tests() -> None:
    section("102. Practical mini test suite")

    tests: List[Tuple[str, Callable[[], bool]]] = [
        (
            "Accessible label relationship",
            lambda: not validate_label_association(
                '<label for="email">Email</label>'
                '<input id="email" type="email">'
            ),
        ),
        (
            "Contrast calculation",
            lambda: contrast_ratio((0, 0, 0), (255, 255, 255)) >= 21,
        ),
        (
            "Toggle state synchronization",
            test_toggle_state,
        ),
        (
            "Keyboard flow",
            lambda: test_keyboard_flow(
                ["A", "B", "C"],
                ["A", "B", "C"],
            ),
        ),
        (
            "Heading heuristic",
            lambda: bool(
                analyze_heading_levels(
                    [Heading(1, "Page"), Heading(2, "Section")]
                )
                == []
            ),
        ),
    ]

    passed = 0

    for name, test in tests:
        try:
            result = bool(test())
        except Exception as error:
            result = False
            print(f"{name}: ERROR ({error})")

        print(f"{name}: {'PASS' if result else 'FAIL'}")

        if result:
            passed += 1

    print(f"\nPassed {passed} of {len(tests)} practical tests.")


# =============================================================================
# 103. FINAL STUDY REFERENCE
# =============================================================================

def final_reference() -> None:
    section("103. Compact reference")

    reference = {
        "WCAG":
            "Perceivable, Operable, Understandable, Robust.",
        "Semantic HTML":
            "Use elements according to meaning and built-in behavior.",
        "Navigation":
            "Use semantic nav regions, meaningful links, and skip mechanisms "
            "when appropriate.",
        "Forms":
            "Use labels, grouping, instructions, validation, and clear errors.",
        "Keyboard":
            "Every interactive function should be usable without a mouse.",
        "Focus":
            "Keep focus visible and manage it deliberately during dynamic changes.",
        "ARIA":
            "Use it to supplement semantics when necessary, not as a replacement "
            "for native HTML.",
        "Screen readers":
            "Interact with browser-exposed accessibility information, including "
            "roles, names, states, properties, and relationships.",
        "Testing":
            "Combine automated analysis with keyboard, screen-reader, zoom, "
            "responsive, and human testing.",
    }

    for topic, rule in reference.items():
        print(f"{topic:20}: {rule}")


# =============================================================================
# 104. MAIN PROGRAM
# =============================================================================

def main() -> None:
    """
    Run the complete accessibility study program.

    Each function is independent enough to be inspected and reused as a
    learning example. The sequence progresses from basic terminology to
    implementation, testing, edge cases, and production considerations.
    """

    beginner_terminology()
    demonstrate_wcag()
    semantic_html_examples()
    heading_demo()
    landmark_demo()
    links_and_buttons_demo()
    form_accessibility_demo()
    label_validation_demo()
    keyboard_demo()
    tabindex_demo()
    focus_management_demo()
    visible_focus_demo()
    image_accessibility_demo()
    contrast_demo()
    aria_demo()
    first_rule_of_aria_demo()
    accessible_name_demo()
    descriptions_and_errors_demo()
    live_region_demo()
    hidden_content_demo()
    screen_reader_demo()
    source_order_demo()
    table_accessibility_demo()
    language_demo()
    title_demo()
    autocomplete_demo()
    custom_checkbox_demo()
    disclosure_demo()
    dialog_demo()
    navigation_menu_demo()
    tab_demo()
    carousel_demo()
    media_demo()
    reduced_motion_demo()
    responsive_demo()
    form_validation_demo()
    dynamic_state_demo()
    focus_trap_demo()
    keyboard_event_demo()
    accessible_name_demo()
    aria_validation_demo()
    linter_demo()
    testing_strategy_demo()
    automated_vs_manual_demo()
    design_requirements_demo()
    progressive_enhancement_demo()
    semantic_fallback_demo()
    spa_accessibility_demo()
    infinite_scroll_demo()
    drag_and_drop_demo()
    tooltip_demo()
    placeholder_demo()
    timing_demo()
    authentication_accessibility_demo()
    internationalization_demo()
    accessible_css_demo()
    visual_semantic_state_demo()
    async_update_demo()
    error_prevention_demo()
    security_considerations_demo()
    performance_demo()
    common_mistakes_demo()
    native_html_decision_tree()
    custom_widget_demo()
    acceptance_criteria_demo()
    code_review_checklist()
    end_to_end_demo()
    end_to_end_lint_demo()
    edge_cases_demo()
    aria_state_table_demo()
    relationships_demo()
    disabled_state_demo()
    current_page_demo()
    direction_demo()
    heading_analysis_demo()
    list_semantics_demo()
    text_semantics_demo()
    iframe_demo()
    svg_demo()
    canvas_demo()
    accessibility_api_demo()
    dom_vs_accessibility_tree_demo()
    tree_simulation_demo()
    keyboard_test_demo()
    state_test_demo()
    accessibility_assertions()
    findings_demo()
    accessibility_debt_demo()
    component_contract_demo()
    design_system_demo()
    regression_testing_demo()
    accessibility_tradeoffs_demo()
    semantic_generator_demo()
    html_escaping_demo()
    link_text_demo()
    current_state_demo()
    alert_demo()
    search_demo()
    footer_demo()
    production_workflow_demo()
    print_complete_checklist()
    run_practical_tests()
    final_reference()

    print("\n" + "=" * 78)
    print("End of HTML accessibility study script")
    print("=" * 78)


if __name__ == "__main__":
    main()
