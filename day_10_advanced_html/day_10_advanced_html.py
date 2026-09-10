"""
Advanced HTML Study Script
Topic:
Metadata, favicon, Open Graph basics, structured document hierarchy,
HTML entities, and accessibility-oriented markup.

This is a standalone Python study file. It uses Python to demonstrate,
generate, validate, compare, and inspect important HTML concepts.

No external packages are required.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from html import escape
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse


# ============================================================================
# 1. HTML FUNDAMENTALS AND DOCUMENT STRUCTURE
# ============================================================================

print("=" * 80)
print("ADVANCED HTML: METADATA, DOCUMENT STRUCTURE, ENTITIES, AND ACCESSIBILITY")
print("=" * 80)


basic_html_document = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Accessible Example Page</title>
</head>
<body>
    <header>
        <h1>Accessible HTML Example</h1>
    </header>

    <main>
        <section>
            <h2>Introduction</h2>
            <p>Semantic HTML gives meaning to document content.</p>
        </section>
    </main>

    <footer>
        <p>Copyright information</p>
    </footer>
</body>
</html>"""

print("\n1. A complete structured HTML document:\n")
print(basic_html_document)


# ============================================================================
# 2. HTML DOCUMENT HIERARCHY
# ============================================================================

print("\n" + "=" * 80)
print("2. HTML DOCUMENT HIERARCHY")
print("=" * 80)

print(
    """
The normal hierarchy is:

Document
├── <!DOCTYPE html>
└── <html>
    ├── <head>
    │   ├── metadata
    │   ├── title
    │   ├── favicon references
    │   ├── social metadata
    │   └── external resources
    │
    └── <body>
        ├── header
        ├── navigation
        ├── main
        │   ├── section
        │   │   ├── heading
        │   │   └── content
        │   └── article
        ├── aside
        └── footer

Important distinction:
<head> contains document metadata and resource declarations.
<body> contains content intended to form the document's visible structure.
"""
)

hierarchy_example = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Document Hierarchy</title>
</head>
<body>
    <header>
        <nav aria-label="Primary navigation">
            <a href="/">Home</a>
            <a href="/about">About</a>
        </nav>
    </header>

    <main>
        <article>
            <header>
                <h1>Article title</h1>
                <p>Published <time datetime="2026-09-10">September 10, 2026</time></p>
            </header>

            <section aria-labelledby="introduction-heading">
                <h2 id="introduction-heading">Introduction</h2>
                <p>Article content belongs inside meaningful structural elements.</p>
            </section>
        </article>

        <aside aria-label="Related information">
            <h2>Related information</h2>
            <p>Supporting content can be placed here.</p>
        </aside>
    </main>

    <footer>
        <p>Site footer</p>
    </footer>
</body>
</html>"""

print(hierarchy_example)


# ============================================================================
# 3. DOCTYPE
# ============================================================================

print("\n" + "=" * 80)
print("3. DOCTYPE")
print("=" * 80)

doctype = "<!DOCTYPE html>"

print(
    """
The HTML5 document type declaration is:

""" + doctype + """

It tells the browser to interpret the document using standards-oriented
HTML parsing behavior.

It is not an HTML element and does not appear inside <html>.
"""
)


# ============================================================================
# 4. THE HTML LANG ATTRIBUTE
# ============================================================================

print("\n" + "=" * 80)
print("4. LANGUAGE IDENTIFICATION")
print("=" * 80)

language_examples = [
    '<html lang="en">',
    '<html lang="en-IN">',
    '<html lang="fr">',
    '<html lang="hi">',
]

for example in language_examples:
    print(example)

print(
    """
The lang attribute identifies the language of the document.

It helps:
- screen readers select appropriate pronunciation rules,
- browsers process language-sensitive behavior,
- search systems understand document language,
- users of assistive technology interpret content correctly.

Use a specific language value when appropriate, such as en-IN for English
as used in India. Do not select a language merely because it resembles
the user's location.
"""
)


# ============================================================================
# 5. METADATA
# ============================================================================

print("\n" + "=" * 80)
print("5. HTML METADATA")
print("=" * 80)

metadata_example = """<head>
    <meta charset="UTF-8">

    <meta name="viewport"
          content="width=device-width, initial-scale=1.0">

    <meta name="description"
          content="A structured HTML page demonstrating semantic markup.">

    <meta name="author"
          content="Example Author">

    <meta name="robots"
          content="index, follow">

    <title>Structured HTML Example</title>
</head>"""

print(metadata_example)

print(
    """
Metadata is information about the document rather than ordinary document
content.

Common metadata includes:
- character encoding,
- viewport configuration,
- document description,
- author information,
- robots directives,
- theme color,
- social sharing metadata,
- resource hints,
- document title.

Metadata belongs primarily in <head>.
"""
)


# ============================================================================
# 6. CHARACTER ENCODING
# ============================================================================

print("\n" + "=" * 80)
print("6. CHARACTER ENCODING")
print("=" * 80)

charset_tag = '<meta charset="UTF-8">'

print(charset_tag)

sample_unicode = "English | हिन्दी | বাংলা | 日本語 | العربية | € | © | ™ | ✓"
print("\nUnicode example:")
print(sample_unicode)

print(
    """
UTF-8 is the normal character encoding used for modern HTML documents.

The declaration should occur early in the document's <head> so that the
browser knows how to interpret the document's bytes.

Character encoding is separate from HTML entity syntax. UTF-8 can represent
many Unicode characters directly, while entities provide named or numeric
ways to express characters in HTML source.
"""
)


# ============================================================================
# 7. VIEWPORT METADATA
# ============================================================================

print("\n" + "=" * 80)
print("7. VIEWPORT METADATA")
print("=" * 80)

viewport_tag = '<meta name="viewport" content="width=device-width, initial-scale=1.0">'

print(viewport_tag)

print(
    """
The viewport declaration is important for responsive pages.

width=device-width
    Requests a layout viewport corresponding to the device's CSS viewport.

initial-scale=1.0
    Sets the initial zoom level to 1.

A viewport declaration does not itself make a page responsive. Responsive
CSS, flexible layouts, appropriate media queries, and suitable content
structure are still required.
"""
)


# ============================================================================
# 8. TITLE AND DESCRIPTION
# ============================================================================

print("\n" + "=" * 80)
print("8. TITLE AND DESCRIPTION")
print("=" * 80)

title_tag = "<title>Advanced HTML Study</title>"
description_tag = (
    '<meta name="description" '
    'content="A structured example of advanced HTML concepts.">'
)

print(title_tag)
print(description_tag)

print(
    """
<title> identifies the document in browser interfaces such as tabs and
history and is an important document-level signal.

The description metadata provides a concise description of the page.
Search engines may use it when constructing search-result snippets, but
the description is not a guaranteed search-result text.

A common mistake is confusing <title> with <h1>.
<title> belongs to document metadata.
<h1> is a visible document heading.
"""
)


# ============================================================================
# 9. FAVICON
# ============================================================================

print("\n" + "=" * 80)
print("9. FAVICON")
print("=" * 80)

favicon_examples = [
    '<link rel="icon" href="/favicon.ico">',
    '<link rel="icon" type="image/png" href="/icons/favicon-32.png">',
    '<link rel="apple-touch-icon" href="/icons/apple-touch-icon.png">',
]

for tag in favicon_examples:
    print(tag)

print(
    """
A favicon is a small icon associated with a website or document.

A common modern declaration is:

<link rel="icon" type="image/png" href="/icons/favicon-32.png">

Important considerations:
- the referenced file must actually exist,
- the MIME type should correspond to the resource,
- multiple icon sizes can be supplied when appropriate,
- favicon support varies across user agents,
- an icon reference does not replace meaningful page titles.

The favicon is metadata/resource information rather than visible body content.
"""
)


# ============================================================================
# 10. OPEN GRAPH BASICS
# ============================================================================

print("\n" + "=" * 80)
print("10. OPEN GRAPH METADATA")
print("=" * 80)

open_graph_example = """<meta property="og:title"
      content="Advanced HTML Study">

<meta property="og:description"
      content="Metadata, structured HTML, entities, and accessibility.">

<meta property="og:type"
      content="website">

<meta property="og:url"
      content="https://example.com/advanced-html">

<meta property="og:image"
      content="https://example.com/images/advanced-html.jpg">"""

print(open_graph_example)

print(
    """
Open Graph metadata is a social-sharing metadata convention originally
introduced by Facebook and widely understood by social platforms.

Common properties include:

og:title
    Title associated with a shared page.

og:description
    Short description associated with the shared page.

og:type
    Type of object, commonly website or article.

og:url
    Canonical URL associated with the shared object.

og:image
    Image associated with the shared object.

Open Graph metadata does not create the page's visible content. It describes
how a page can be represented when shared through compatible systems.

A common mistake is using name= for Open Graph properties. Open Graph uses
property=:

Correct:
<meta property="og:title" content="Example">

Incorrect:
<meta name="og:title" content="Example">
"""
)


# ============================================================================
# 11. TWITTER/X-STYLE CARD METADATA
# ============================================================================

print("\n" + "=" * 80)
print("11. SOCIAL CARD METADATA")
print("=" * 80)

social_card_example = """<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Advanced HTML Study">
<meta name="twitter:description"
      content="Structured HTML and accessibility concepts.">
<meta name="twitter:image"
      content="https://example.com/images/share.jpg">"""

print(social_card_example)

print(
    """
Some platforms use their own metadata conventions in addition to Open Graph.

The important design principle is to keep metadata consistent:
- title should represent the actual page,
- description should match the page's subject,
- image should be relevant,
- URL should identify the intended page.

Social metadata is not a substitute for normal SEO, accessibility, or
semantic HTML.
"""
)


# ============================================================================
# 12. CANONICAL URL
# ============================================================================

print("\n" + "=" * 80)
print("12. CANONICAL URL")
print("=" * 80)

canonical_example = (
    '<link rel="canonical" href="https://example.com/articles/html-basics">'
)

print(canonical_example)

print(
    """
A canonical link identifies the preferred URL for substantially equivalent
or duplicate versions of a page.

It is different from og:url:
- canonical is primarily a search/document indexing signal,
- og:url is social-sharing metadata.

They commonly point to the same URL, but they have different purposes.
"""
)


# ============================================================================
# 13. STRUCTURED DOCUMENT HIERARCHY
# ============================================================================

print("\n" + "=" * 80)
print("13. STRUCTURED DOCUMENT HIERARCHY")
print("=" * 80)

semantic_structure = """<body>
    <header>
        <h1>Company Documentation</h1>
    </header>

    <nav aria-label="Documentation navigation">
        <a href="/docs">Documentation</a>
        <a href="/contact">Contact</a>
    </nav>

    <main>
        <article>
            <header>
                <h2>HTML Metadata</h2>
            </header>

            <section aria-labelledby="metadata-basics">
                <h3 id="metadata-basics">Metadata basics</h3>
                <p>Metadata describes document properties.</p>
            </section>

            <section aria-labelledby="favicon">
                <h3 id="favicon">Favicons</h3>
                <p>Favicons associate icons with documents.</p>
            </section>
        </article>

        <aside>
            <h2>Related topics</h2>
            <a href="/docs/accessibility">Accessibility</a>
        </aside>
    </main>

    <footer>
        <p>Documentation footer</p>
    </footer>
</body>"""

print(semantic_structure)

print(
    """
Semantic elements communicate structural meaning.

<header>
    Introductory or navigational content for a page or section.

<nav>
    A major group of navigation links.

<main>
    The dominant content of the document. A document normally has one
    primary <main> region.

<article>
    A self-contained composition that could make sense independently.

<section>
    A thematic grouping of content, normally with a heading.

<aside>
    Complementary content related to the surrounding material.

<footer>
    Footer information for a page or section.

Semantic HTML is preferable to replacing every structural element with
generic <div> elements.
"""
)


# ============================================================================
# 14. HEADING HIERARCHY
# ============================================================================

print("\n" + "=" * 80)
print("14. HEADING HIERARCHY")
print("=" * 80)

heading_example = """<h1>Advanced HTML</h1>
<h2>Metadata</h2>
<h3>Character encoding</h3>
<h3>Viewport</h3>
<h2>Accessibility</h2>
<h3>Labels</h3>
<h3>Landmarks</h3>"""

print(heading_example)

print(
    """
Headings establish a content hierarchy.

<h1> is normally the primary page heading.
<h2> identifies major subdivisions.
<h3> identifies subdivisions within an h2.
<h4>, <h5>, and <h6> provide deeper levels.

Do not choose a heading level merely because its default visual appearance
looks attractive. CSS should control presentation; heading levels should
represent document structure.

Avoid jumping between levels without a meaningful structural reason.
"""
)


# ============================================================================
# 15. HTML ENTITIES
# ============================================================================

print("\n" + "=" * 80)
print("15. HTML ENTITIES")
print("=" * 80)

entity_examples = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
    "©": "&copy;",
    "®": "&reg;",
    "™": "&trade;",
    "€": "&euro;",
    "non-breaking space": "&nbsp;",
}

for character, entity in entity_examples.items():
    print(f"{character!r:22} -> {entity}")

print(
    """
An HTML character reference allows a character to be represented using
named or numeric syntax.

Examples:
&amp;   represents &
&lt;    represents <
&gt;    represents >
&quot;  represents "
&#39;   represents '
&copy;  represents ©

Numeric references can be decimal or hexadecimal.

Decimal:
&#169;

Hexadecimal:
&#xA9;

Entities are particularly important when literal characters could otherwise
be interpreted as HTML markup.

For ordinary Unicode text, direct UTF-8 characters are often readable and
appropriate. Entities are not required for every non-ASCII character.
"""
)


# ============================================================================
# 16. HTML ENTITY ENCODING WITH PYTHON
# ============================================================================

print("\n" + "=" * 80)
print("16. ENTITY ENCODING WITH PYTHON")
print("=" * 80)

unsafe_text = '<script>alert("test")</script> & "quoted text"'
safe_text = escape(unsafe_text, quote=True)

print("Original text:")
print(unsafe_text)

print("\nHTML-escaped representation:")
print(safe_text)

print(
    """
Python's html.escape() is useful when inserting untrusted text into HTML
text or attribute contexts where HTML escaping is appropriate.

Escaping is context-dependent. HTML escaping does not automatically make a
value safe for JavaScript, CSS, SQL, shell commands, or every other context.

A frequent security error is assuming that one escaping mechanism works
everywhere.
"""
)


# ============================================================================
# 17. SAFE HTML TEXT GENERATION
# ============================================================================

print("\n" + "=" * 80)
print("17. SAFE HTML TEXT GENERATION")
print("=" * 80)


def make_paragraph(user_text: str) -> str:
    """Create a paragraph while escaping HTML-sensitive characters."""
    return f"<p>{escape(user_text)}</p>"


def make_attribute_value(value: str) -> str:
    """Escape a value intended for an HTML attribute."""
    return escape(value, quote=True)


user_input = '<img src=x onerror="alert(1)">'
generated_paragraph = make_paragraph(user_input)

print("Untrusted input:")
print(user_input)

print("\nEscaped paragraph:")
print(generated_paragraph)

print(
    """
This prevents the supplied string from being interpreted as an HTML element
when the output is inserted as HTML text.

The general security principle is:

Treat external data as data, not markup.

Server-side HTML generation, template engines, and client-side DOM APIs each
have their own safety rules. Prefer APIs that insert text as text when HTML
interpretation is unnecessary.
"""
)


# ============================================================================
# 18. ACCESSIBILITY-ORIENTED LINKS
# ============================================================================

print("\n" + "=" * 80)
print("18. ACCESSIBLE LINKS")
print("=" * 80)

accessible_link = '<a href="/pricing">View pricing plans</a>'
weak_link = '<a href="/pricing">Click here</a>'

print("Preferred:")
print(accessible_link)

print("\nLess informative:")
print(weak_link)

print(
    """
Link text should communicate the destination or purpose.

A screen-reader user may navigate through links independently of surrounding
paragraph text. Generic labels such as "click here" provide little context.

Do not add aria-label merely to compensate for poor visible link text when
clear visible text would solve the problem.
"""
)


# ============================================================================
# 19. IMAGES AND ALT TEXT
# ============================================================================

print("\n" + "=" * 80)
print("19. ACCESSIBLE IMAGES")
print("=" * 80)

image_examples = {
    "informative": '<img src="/images/chart.png" alt="Revenue increased from 20 to 35 million.">',
    "decorative": '<img src="/images/divider.png" alt="">',
    "bad": '<img src="/images/chart.png">',
}

for category, markup in image_examples.items():
    print(f"{category.title():12}: {markup}")

print(
    """
The alt attribute provides a text alternative for an image.

Informative image:
    alt should communicate the image's relevant meaning.

Decorative image:
    alt="" indicates that the image does not provide useful content.

Missing alt:
    may leave assistive technologies without an appropriate alternative.

Do not write "image of" or "picture of" automatically. The assistive
technology already identifies the element as an image in many contexts.
"""
)


# ============================================================================
# 20. FIGURE AND FIGCAPTION
# ============================================================================

print("\n" + "=" * 80)
print("20. FIGURE AND FIGCAPTION")
print("=" * 80)

figure_example = """<figure>
    <img
        src="/images/architecture.png"
        alt="Diagram showing the hierarchy of an HTML document."
    >
    <figcaption>
        HTML document hierarchy from document type through body content.
    </figcaption>
</figure>"""

print(figure_example)

print(
    """
<figure> represents self-contained content such as an illustration, diagram,
photo, chart, or code example.

<figcaption> provides a caption associated with the figure.

The caption is not a replacement for alt text. Alt text serves as the
alternative text representation of the image, while the caption can provide
additional visible context.
"""
)


# ============================================================================
# 21. FORM LABELS
# ============================================================================

print("\n" + "=" * 80)
print("21. ACCESSIBLE FORM CONTROLS")
print("=" * 80)

form_example = """<form>
    <div>
        <label for="email">Email address</label>
        <input
            id="email"
            name="email"
            type="email"
            autocomplete="email"
            required
        >
    </div>

    <div>
        <label for="message">Message</label>
        <textarea
            id="message"
            name="message"
            rows="5"
        ></textarea>
    </div>

    <button type="submit">Send message</button>
</form>"""

print(form_example)

print(
    """
A <label> gives a form control an understandable name.

The for attribute should match the controlled input's id:

<label for="email">Email address</label>
<input id="email">

This explicit relationship is useful for assistive technology and also
allows users to activate the control by selecting its label.

The name attribute is important for form submission.

The type attribute should reflect the expected input.

The required attribute expresses a native constraint.

Native HTML controls are usually preferable to recreating equivalent
controls from generic elements.
"""
)


# ============================================================================
# 22. FIELDSET AND LEGEND
# ============================================================================

print("\n" + "=" * 80)
print("22. GROUPING RELATED FORM CONTROLS")
print("=" * 80)

fieldset_example = """<fieldset>
    <legend>Preferred contact method</legend>

    <label>
        <input type="radio" name="contact" value="email">
        Email
    </label>

    <label>
        <input type="radio" name="contact" value="phone">
        Phone
    </label>
</fieldset>"""

print(fieldset_example)

print(
    """
<fieldset> groups related form controls.

<legend> gives the group a descriptive caption.

Radio buttons representing alternatives should normally share the same
name so that they form one logical group.
"""
)


# ============================================================================
# 23. BUTTONS VERSUS LINKS
# ============================================================================

print("\n" + "=" * 80)
print("23. BUTTONS VERSUS LINKS")
print("=" * 80)

button_vs_link = """<!-- Navigation to another URL -->
<a href="/account">Open account</a>

<!-- Action performed on the current page -->
<button type="button">Open menu</button>"""

print(button_vs_link)

print(
    """
Use <a> for navigation to a resource or URL.

Use <button> for an action.

Using a clickable <div> instead of a button often loses native keyboard,
focus, semantic, and accessibility behavior.

If a control behaves like a button, use a real <button> whenever possible.
"""
)


# ============================================================================
# 24. ACCESSIBLE TABLES
# ============================================================================

print("\n" + "=" * 80)
print("24. ACCESSIBLE TABLES")
print("=" * 80)

table_example = """<table>
    <caption>Quarterly revenue</caption>
    <thead>
        <tr>
            <th scope="col">Quarter</th>
            <th scope="col">Revenue</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <th scope="row">Q1</th>
            <td>₹10,00,000</td>
        </tr>
        <tr>
            <th scope="row">Q2</th>
            <td>₹12,50,000</td>
        </tr>
    </tbody>
</table>"""

print(table_example)

print(
    """
Tables should represent actual tabular relationships.

<caption> describes the table.

<th> identifies header cells.

scope="col" identifies a column header.

scope="row" identifies a row header.

Do not use tables solely to create page layouts.
"""
)


# ============================================================================
# 25. TIME ELEMENT
# ============================================================================

print("\n" + "=" * 80)
print("25. MACHINE-READABLE TIME")
print("=" * 80)

time_example = """<time datetime="2026-09-10">September 10, 2026</time>
<time datetime="2026-09-10T10:30:00+05:30">10:30 AM IST</time>
<time datetime="PT45M">45 minutes</time>"""

print(time_example)

print(
    """
The <time> element can associate human-readable text with a machine-readable
datetime value.

This creates a distinction between presentation and structured meaning.
"""
)


# ============================================================================
# 26. ARIA BASICS
# ============================================================================

print("\n" + "=" * 80)
print("26. ARIA BASICS")
print("=" * 80)

aria_example = """<button
    type="button"
    aria-expanded="false"
    aria-controls="navigation-menu"
>
    Menu
</button>

<nav id="navigation-menu" aria-label="Primary navigation">
    <a href="/">Home</a>
</nav>"""

print(aria_example)

print(
    """
ARIA means Accessible Rich Internet Applications.

ARIA attributes can expose roles, states, properties, and relationships to
assistive technologies.

Examples:
aria-label
    Supplies an accessible name when appropriate.

aria-labelledby
    References another element that supplies the accessible name.

aria-describedby
    References descriptive supporting content.

aria-expanded
    Communicates whether a collapsible control is expanded.

aria-controls
    Identifies content controlled by a widget.

Important rule:
Prefer native HTML semantics before adding ARIA.

For example, use <button> rather than:
<div role="button">...</div>

ARIA does not automatically implement keyboard behavior, focus management,
state changes, or interaction logic.
"""
)


# ============================================================================
# 27. ACCESSIBLE NAVIGATION
# ============================================================================

print("\n" + "=" * 80)
print("27. NAVIGATION LANDMARKS")
print("=" * 80)

navigation_example = """<nav aria-label="Primary navigation">
    <ul>
        <li><a href="/">Home</a></li>
        <li><a href="/products">Products</a></li>
        <li><a href="/contact">Contact</a></li>
    </ul>
</nav>

<nav aria-label="Footer navigation">
    <ul>
        <li><a href="/privacy">Privacy</a></li>
        <li><a href="/terms">Terms</a></li>
    </ul>
</nav>"""

print(navigation_example)

print(
    """
A page may contain multiple navigation landmarks.

When multiple <nav> elements exist, accessible labels can distinguish them.

aria-label is appropriate when the navigation regions require distinct
accessible names.
"""
)


# ============================================================================
# 28. MAIN LANDMARK
# ============================================================================

print("\n" + "=" * 80)
print("28. MAIN CONTENT")
print("=" * 80)

main_example = """<header>
    <h1>Product documentation</h1>
</header>

<main>
    <h2>Installation</h2>
    <p>Installation instructions belong to the primary content.</p>
</main>

<footer>
    <p>Copyright notice</p>
</footer>"""

print(main_example)

print(
    """
<main> represents the dominant content of the page.

Repeated navigation, site-wide headers, and site-wide footers generally do
not belong inside <main> unless they are actually part of the page's main
content.
"""
)


# ============================================================================
# 29. VISUALLY HIDDEN ACCESSIBLE TEXT
# ============================================================================

print("\n" + "=" * 80)
print("29. VISUALLY HIDDEN TEXT")
print("=" * 80)

visually_hidden_css = """/* Example technique; production CSS should be tested carefully. */
.visually-hidden {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
}"""

visually_hidden_html = """<button type="button">
    <span class="visually-hidden">Close</span>
    ×
</button>"""

print(visually_hidden_css)
print(visually_hidden_html)

print(
    """
Visually hidden content can provide information to assistive technologies
without presenting the text visually.

This technique should not be used to hide large amounts of meaningful page
content merely to manipulate search engines or users.
"""
)


# ============================================================================
# 30. ACCESSIBILITY AND FOCUS
# ============================================================================

print("\n" + "=" * 80)
print("30. KEYBOARD ACCESS AND FOCUS")
print("=" * 80)

focus_example = """<a href="/dashboard">Dashboard</a>
<button type="button">Save changes</button>
<input type="text" aria-label="Search">"""

print(focus_example)

print(
    """
Interactive elements should be usable with a keyboard.

Native links, buttons, and form controls provide built-in keyboard semantics.

A common mistake is removing focus indicators with CSS:

*:focus {
    outline: none;
}

If the default focus indicator is removed, an accessible replacement should
be supplied.

Keyboard accessibility is not equivalent to adding tabindex to everything.
"""
)


# ============================================================================
# 31. TABINDEX
# ============================================================================

print("\n" + "=" * 80)
print("31. TABINDEX")
print("=" * 80)

tabindex_examples = [
    '<button type="button">Native button</button>',
    '<div tabindex="0" role="button">Custom control</div>',
    '<div tabindex="-1">Programmatically focusable element</div>',
]

for example in tabindex_examples:
    print(example)

print(
    """
tabindex="0"
    Allows an element to participate in the normal sequential keyboard
    focus order when appropriate.

tabindex="-1"
    Allows programmatic focus without placing the element in normal tab
    navigation.

Positive tabindex values should generally be avoided because they create
a manually imposed focus order that is difficult to maintain.

Native interactive elements should normally be used instead of creating
custom keyboard behavior.
"""
)


# ============================================================================
# 32. DETAILS AND SUMMARY
# ============================================================================

print("\n" + "=" * 80)
print("32. NATIVE DISCLOSURE")
print("=" * 80)

details_example = """<details>
    <summary>Metadata explanation</summary>
    <p>
        Metadata describes properties of the HTML document and resources.
    </p>
</details>"""

print(details_example)

print(
    """
<details> and <summary> provide native disclosure behavior.

They can reduce the need to implement a custom expandable component.

Native HTML behavior is often more robust than manually recreating
interaction patterns with generic elements and JavaScript.
"""
)


# ============================================================================
# 33. DIALOG BASICS
# ============================================================================

print("\n" + "=" * 80)
print("33. DIALOG")
print("=" * 80)

dialog_example = """<dialog id="help-dialog">
    <form method="dialog">
        <h2>Help</h2>
        <p>Additional information is displayed here.</p>
        <button type="submit">Close</button>
    </form>
</dialog>"""

print(dialog_example)

print(
    """
<dialog> represents a dialog box.

Modern browser support allows native dialog behavior to be used instead of
building every dialog from generic containers.

A production dialog still requires careful attention to:
- focus management,
- accessible naming,
- keyboard behavior,
- content clarity,
- modal versus non-modal behavior,
- browser compatibility requirements.
"""
)


# ============================================================================
# 34. LANGUAGE CHANGES WITHIN DOCUMENTS
# ============================================================================

print("\n" + "=" * 80)
print("34. INLINE LANGUAGE CHANGES")
print("=" * 80)

inline_language = """<p>
    The French expression
    <span lang="fr">déjà vu</span>
    is commonly used in English.
</p>"""

print(inline_language)

print(
    """
The lang attribute can also be applied to individual elements when a piece
of content differs from the surrounding document language.
"""
)


# ============================================================================
# 35. DIRECTIONALITY
# ============================================================================

print("\n" + "=" * 80)
print("35. TEXT DIRECTION")
print("=" * 80)

direction_example = """<p dir="ltr">Left-to-right text</p>
<p dir="rtl">نص من اليمين إلى اليسار</p>
<p dir="auto">Automatically inferred direction</p>"""

print(direction_example)

print(
    """
dir controls text direction.

ltr
    Left to right.

rtl
    Right to left.

auto
    Allows direction to be inferred from the content.

Directionality matters for multilingual interfaces and bidirectional text.
"""
)


# ============================================================================
# 36. METADATA DATA MODEL
# ============================================================================

print("\n" + "=" * 80)
print("36. PYTHON METADATA MODEL")
print("=" * 80)


@dataclass
class PageMetadata:
    """Represent common document metadata."""

    title: str
    description: str
    canonical_url: str
    language: str = "en"
    author: Optional[str] = None
    favicon_path: Optional[str] = None
    og_title: Optional[str] = None
    og_description: Optional[str] = None
    og_type: str = "website"
    og_url: Optional[str] = None
    og_image: Optional[str] = None


metadata = PageMetadata(
    title="Advanced HTML Study",
    description="Metadata, structured HTML, entities, and accessibility.",
    canonical_url="https://example.com/advanced-html",
    language="en-IN",
    author="Example Author",
    favicon_path="/icons/favicon-32.png",
    og_title="Advanced HTML Study",
    og_description="Metadata, structured HTML, entities, and accessibility.",
    og_url="https://example.com/advanced-html",
    og_image="https://example.com/images/advanced-html.jpg",
)

print(metadata)


# ============================================================================
# 37. URL VALIDATION
# ============================================================================

print("\n" + "=" * 80)
print("37. URL VALIDATION")
print("=" * 80)


def is_absolute_http_url(value: str) -> bool:
    """
    Return True when value is an absolute HTTP or HTTPS URL.

    This is a structural check, not a guarantee that the URL exists.
    """
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


test_urls = [
    "https://example.com/page",
    "http://example.com",
    "/relative/page",
    "javascript:alert(1)",
    "example.com/page",
]

for url in test_urls:
    print(f"{url:35} -> {is_absolute_http_url(url)}")


# ============================================================================
# 38. METADATA VALIDATION
# ============================================================================

print("\n" + "=" * 80)
print("38. METADATA VALIDATION")
print("=" * 80)


@dataclass
class ValidationIssue:
    """Represent one metadata validation problem."""

    level: str
    message: str


def validate_metadata(page: PageMetadata) -> List[ValidationIssue]:
    """
    Validate basic metadata structure.

    This deliberately performs structural checks rather than claiming to
    perform complete SEO or social-platform validation.
    """
    issues: List[ValidationIssue] = []

    if not page.title.strip():
        issues.append(ValidationIssue("ERROR", "The page title is empty."))

    if not page.description.strip():
        issues.append(
            ValidationIssue("WARNING", "The meta description is empty.")
        )

    if not page.language.strip():
        issues.append(
            ValidationIssue("ERROR", "The document language is missing.")
        )

    if not is_absolute_http_url(page.canonical_url):
        issues.append(
            ValidationIssue(
                "ERROR",
                "The canonical URL is not an absolute HTTP/HTTPS URL.",
            )
        )

    if page.og_url and not is_absolute_http_url(page.og_url):
        issues.append(
            ValidationIssue(
                "ERROR",
                "The Open Graph URL is not an absolute HTTP/HTTPS URL.",
            )
        )

    if page.og_image and not is_absolute_http_url(page.og_image):
        issues.append(
            ValidationIssue(
                "WARNING",
                "The Open Graph image is not an absolute HTTP/HTTPS URL.",
            )
        )

    if page.og_type not in {"website", "article", "profile", "book"}:
        issues.append(
            ValidationIssue(
                "WARNING",
                f"Open Graph type '{page.og_type}' is not in this basic validator's common set.",
            )
        )

    return issues


issues = validate_metadata(metadata)

if not issues:
    print("Metadata validation passed.")
else:
    for issue in issues:
        print(f"[{issue.level}] {issue.message}")


# ============================================================================
# 39. HTML HEAD GENERATOR
# ============================================================================

print("\n" + "=" * 80)
print("39. GENERATING A COMPLETE <head>")
print("=" * 80)


def build_head(page: PageMetadata) -> str:
    """Generate a standards-oriented metadata section."""

    lines = [
        "<head>",
        '    <meta charset="UTF-8">',
        '    <meta name="viewport" content="width=device-width, initial-scale=1.0">',
        f"    <title>{escape(page.title)}</title>",
        (
            f'    <meta name="description" content="{escape(page.description, quote=True)}">'
        ),
        f'    <meta name="author" content="{escape(page.author, quote=True)}">'
        if page.author
        else "",
        (
            f'    <link rel="canonical" href="{escape(page.canonical_url, quote=True)}">'
        ),
        (
            f'    <link rel="icon" type="image/png" '
            f'href="{escape(page.favicon_path, quote=True)}">'
        )
        if page.favicon_path
        else "",
        (
            f'    <meta property="og:title" content="{escape(page.og_title or page.title, quote=True)}">'
        ),
        (
            f'    <meta property="og:description" '
            f'content="{escape(page.og_description or page.description, quote=True)}">'
        ),
        f'    <meta property="og:type" content="{escape(page.og_type, quote=True)}">',
        (
            f'    <meta property="og:url" '
            f'content="{escape(page.og_url or page.canonical_url, quote=True)}">'
        ),
        (
            f'    <meta property="og:image" '
            f'content="{escape(page.og_image, quote=True)}">'
        )
        if page.og_image
        else "",
        "</head>",
    ]

    return "\n".join(line for line in lines if line)


generated_head = build_head(metadata)
print(generated_head)


# ============================================================================
# 40. COMPLETE PAGE GENERATOR
# ============================================================================

print("\n" + "=" * 80)
print("40. GENERATING A COMPLETE ACCESSIBLE PAGE")
print("=" * 80)


def build_accessible_page(page: PageMetadata) -> str:
    """Generate a complete semantic HTML page."""

    head = build_head(page)

    return f"""<!DOCTYPE html>
<html lang="{escape(page.language, quote=True)}">
{head}
<body>
    <header>
        <nav aria-label="Primary navigation">
            <a href="/">Home</a>
            <a href="/topics">Topics</a>
            <a href="/contact">Contact</a>
        </nav>
    </header>

    <main>
        <article>
            <header>
                <h1>{escape(page.title)}</h1>
                <p>{escape(page.description)}</p>
            </header>

            <section aria-labelledby="metadata-heading">
                <h2 id="metadata-heading">Metadata</h2>
                <p>
                    This page demonstrates structured document metadata.
                </p>
            </section>

            <section aria-labelledby="accessibility-heading">
                <h2 id="accessibility-heading">Accessibility</h2>
                <p>
                    Semantic elements provide meaningful document structure.
                </p>
            </section>
        </article>
    </main>

    <footer>
        <p>&copy; 2026 Example Organization</p>
    </footer>
</body>
</html>"""


complete_page = build_accessible_page(metadata)
print(complete_page)


# ============================================================================
# 41. HTML STRUCTURE INSPECTION
# ============================================================================

print("\n" + "=" * 80)
print("41. BASIC HTML STRUCTURE INSPECTION")
print("=" * 80)


def count_tag_occurrences(html_document: str, tag_name: str) -> int:
    """
    Count simple opening-tag occurrences.

    This intentionally demonstrates basic text inspection, not full HTML
    parsing. Real HTML parsing should use an HTML parser.
    """
    token = f"<{tag_name}"
    return html_document.lower().count(token)


important_tags = [
    "html",
    "head",
    "body",
    "title",
    "main",
    "article",
    "section",
    "h1",
    "h2",
    "nav",
    "footer",
]

for tag in important_tags:
    print(f"<{tag}> occurrences: {count_tag_occurrences(complete_page, tag)}")


# ============================================================================
# 42. WHY REGEX IS NOT A FULL HTML PARSER
# ============================================================================

print("\n" + "=" * 80)
print("42. HTML INSPECTION LIMITATION")
print("=" * 80)

print(
    """
The count_tag_occurrences() function is intentionally simple.

It is useful for demonstrating string processing, but it is not a reliable
HTML parser.

HTML has:
- nested structures,
- comments,
- attributes,
- quoted attribute values,
- malformed documents,
- foreign content,
- optional tags,
- script and style content,
- browser error recovery rules.

Production HTML analysis should use an HTML-aware parser or validator rather
than relying on regular expressions or substring counts.
"""
)


# ============================================================================
# 43. BASIC ACCESSIBILITY CHECKER
# ============================================================================

print("\n" + "=" * 80)
print("43. BASIC ACCESSIBILITY CHECKER")
print("=" * 80)


@dataclass
class AccessibilityIssue:
    """Represent one basic accessibility finding."""

    severity: str
    message: str


def basic_accessibility_check(html_document: str) -> List[AccessibilityIssue]:
    """
    Perform intentionally limited static checks.

    This is an educational checker, not a complete accessibility audit.
    """
    issues: List[AccessibilityIssue] = []
    lowered = html_document.lower()

    if "<html" not in lowered:
        issues.append(
            AccessibilityIssue("ERROR", "No <html> element was detected.")
        )
    elif 'lang="' not in lowered and "lang='" not in lowered:
        issues.append(
            AccessibilityIssue("WARNING", "The <html> language may be missing.")
        )

    if "<title>" not in lowered:
        issues.append(
            AccessibilityIssue("ERROR", "No <title> element was detected.")
        )

    if "<main" not in lowered:
        issues.append(
            AccessibilityIssue("WARNING", "No <main> landmark was detected.")
        )

    if "<h1" not in lowered:
        issues.append(
            AccessibilityIssue("WARNING", "No primary heading was detected.")
        )

    if "<img" in lowered and "alt=" not in lowered:
        issues.append(
            AccessibilityIssue(
                "ERROR",
                "An image was detected without an obvious alt attribute.",
            )
        )

    if '<a href="' in lowered and ">click here<" in lowered:
        issues.append(
            AccessibilityIssue(
                "WARNING",
                "A generic 'click here' link label was detected.",
            )
        )

    return issues


accessibility_issues = basic_accessibility_check(complete_page)

if not accessibility_issues:
    print("No issues detected by the basic educational checker.")
else:
    for issue in accessibility_issues:
        print(f"[{issue.severity}] {issue.message}")


# ============================================================================
# 44. TESTING ACCESSIBILITY CHECKER WITH A BAD PAGE
# ============================================================================

print("\n" + "=" * 80)
print("44. TESTING THE CHECKER")
print("=" * 80)

bad_page = """<html>
<body>
    <div>
        <img src="chart.png">
        <a href="/pricing">Click here</a>
    </div>
</body>
</html>"""

print("Bad example:")
print(bad_page)

print("\nFindings:")

for issue in basic_accessibility_check(bad_page):
    print(f"[{issue.severity}] {issue.message}")


# ============================================================================
# 45. STRUCTURED DATA CONCEPT
# ============================================================================

print("\n" + "=" * 80)
print("45. STRUCTURED DATA DISTINCTION")
print("=" * 80)

structured_data_concept = """<script type="application/ld+json">
{
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": "Advanced HTML",
    "description": "An article about structured HTML."
}
</script>"""

print(structured_data_concept)

print(
    """
Structured data is related to metadata but is a distinct concept.

Open Graph:
    Social sharing metadata.

JSON-LD structured data:
    Machine-readable structured information describing entities and
    relationships.

Semantic HTML:
    Meaningful document structure expressed through HTML elements.

These systems can complement one another. None should be treated as a
replacement for the others.
"""
)


# ============================================================================
# 46. META ROBOTS
# ============================================================================

print("\n" + "=" * 80)
print("46. ROBOTS METADATA")
print("=" * 80)

robots_examples = [
    '<meta name="robots" content="index, follow">',
    '<meta name="robots" content="noindex, nofollow">',
    '<meta name="robots" content="noarchive">',
]

for example in robots_examples:
    print(example)

print(
    """
The robots metadata field communicates directives to compatible crawlers.

Examples include:
index
    The page may be indexed.

noindex
    Requests that the page not be indexed.

follow
    Links may be followed.

nofollow
    Requests that links not be followed for indexing purposes.

Crawler behavior is not identical across all systems. Metadata directives
should not be treated as an access-control mechanism.

If confidential information must be protected, authentication and
authorization must be implemented rather than relying on robots metadata.
"""
)


# ============================================================================
# 47. SECURITY: METADATA IS NOT ACCESS CONTROL
# ============================================================================

print("\n" + "=" * 80)
print("47. SECURITY DISTINCTION")
print("=" * 80)

print(
    """
Security principle:

A meta tag does not make private content private.

For example:

<meta name="robots" content="noindex">

does not prevent:
- direct URL access,
- authenticated users from accessing content,
- someone who already knows the URL from requesting it,
- all crawlers from ignoring the directive.

Confidential resources require server-side authorization.

Metadata controls interpretation or discovery behavior. It is not a substitute
for authentication, authorization, encryption, or server-side validation.
"""
)


# ============================================================================
# 48. REFERRER POLICY
# ============================================================================

print("\n" + "=" * 80)
print("48. REFERRER POLICY")
print("=" * 80)

referrer_policy_example = (
    '<meta name="referrer" content="strict-origin-when-cross-origin">'
)

print(referrer_policy_example)

print(
    """
The referrer policy controls what referrer information can be sent when
navigating or fetching resources.

Policies involve privacy and information-disclosure trade-offs.

A strict policy can reduce unnecessary URL information leakage while still
allowing useful origin information in cross-origin requests.
"""
)


# ============================================================================
# 49. THEME COLOR
# ============================================================================

print("\n" + "=" * 80)
print("49. THEME COLOR")
print("=" * 80)

theme_color = '<meta name="theme-color" content="#111827">'
print(theme_color)

print(
    """
theme-color can provide a browser or platform with a preferred UI color
associated with the page.

It affects browser/platform presentation where supported. It does not replace
CSS styling and should not be treated as a universal page-background rule.
"""
)


# ============================================================================
# 50. RESOURCE LINKS
# ============================================================================

print("\n" + "=" * 80)
print("50. LINK ELEMENT AND RESOURCES")
print("=" * 80)

resource_examples = [
    '<link rel="icon" href="/favicon.ico">',
    '<link rel="canonical" href="https://example.com/page">',
    '<link rel="stylesheet" href="/css/style.css">',
]

for example in resource_examples:
    print(example)

print(
    """
The <link> element establishes relationships between the current document
and external or related resources.

Its meaning depends on rel.

Common examples:
icon
    Document icon.

canonical
    Preferred URL.

stylesheet
    External CSS resource.

<link> is different from <a>:
<a> creates a navigational hyperlink in document content.
<link> expresses a document/resource relationship, normally in <head>.
"""
)


# ============================================================================
# 51. PRELOAD AND RESOURCE HINTS
# ============================================================================

print("\n" + "=" * 80)
print("51. RESOURCE HINTS")
print("=" * 80)

resource_hint = (
    '<link rel="preload" href="/fonts/main.woff2" '
    'as="font" type="font/woff2" crossorigin>'
)

print(resource_hint)

print(
    """
Resource hints can influence how the browser discovers or prioritizes
resources.

preload is powerful but should be used carefully. Preloading resources that
are not actually needed can waste bandwidth and compete with more important
resources.

Performance optimization requires measuring actual loading behavior rather
than adding hints indiscriminately.
"""
)


# ============================================================================
# 52. META REFRESH WARNING
# ============================================================================

print("\n" + "=" * 80)
print("52. META REFRESH")
print("=" * 80)

meta_refresh = '<meta http-equiv="refresh" content="5; url=/new-page">'
print(meta_refresh)

print(
    """
Meta refresh can cause timed navigation or page refreshes.

It can create accessibility, usability, and predictability problems when
used unexpectedly.

Normal application navigation should generally use appropriate links or
application/server routing rather than relying on timed meta refreshes.
"""
)


# ============================================================================
# 53. SEMANTIC VERSUS PRESENTATIONAL MARKUP
# ============================================================================

print("\n" + "=" * 80)
print("53. SEMANTIC VERSUS PRESENTATIONAL MARKUP")
print("=" * 80)

semantic_example = """<strong>Important information</strong>
<em>Emphasized information</em>
<mark>Highlighted information</mark>
<small>Legal or side information</small>"""

presentational_example = """<b>Bold-looking text</b>
<i>Italic-looking text</i>"""

print("Semantic examples:")
print(semantic_example)

print("\nPresentational-oriented examples:")
print(presentational_example)

print(
    """
<strong> conveys strong importance.
<em> conveys emphasis.
<mark> identifies relevant highlighted content.
<small> represents side comments or small print.

<b> and <i> are not automatically wrong. Their semantics differ from
<strong> and <em>. Choose an element according to meaning, not only visual
appearance.

CSS should control visual presentation when semantic meaning is not the
purpose.
"""
)


# ============================================================================
# 54. ABBREVIATIONS
# ============================================================================

print("\n" + "=" * 80)
print("54. ABBREVIATIONS")
print("=" * 80)

abbr_example = '<abbr title="HyperText Markup Language">HTML</abbr>'
print(abbr_example)

print(
    """
<abbr> identifies an abbreviation or acronym.

The title attribute can provide an expanded form.

Whether the title is exposed consistently across assistive technologies
varies, so critical information should not exist only in a title tooltip.
"""
)


# ============================================================================
# 55. BLOCKQUOTES AND QUOTATIONS
# ============================================================================

print("\n" + "=" * 80)
print("55. QUOTATIONS")
print("=" * 80)

quotation_example = """<blockquote cite="https://example.com/source">
    <p>Quoted material appears here.</p>
</blockquote>

<p>
    The term <q>semantic HTML</q> refers to markup that conveys meaning.
</p>"""

print(quotation_example)

print(
    """
<blockquote> represents a longer quotation.

<q> represents an inline quotation.

cite can identify the source URL associated with a quotation, but it does
not automatically provide visible citation text to users.
"""
)


# ============================================================================
# 56. ADDRESS ELEMENT
# ============================================================================

print("\n" + "=" * 80)
print("56. CONTACT INFORMATION")
print("=" * 80)

address_example = """<address>
    Contact the documentation team at
    <a href="mailto:docs@example.com">docs@example.com</a>.
</address>"""

print(address_example)

print(
    """
<address> represents contact information for the nearest article or body
context.

It is not a generic element for every physical postal address.
"""
)


# ============================================================================
# 57. ACCESSIBLE STATUS MESSAGES
# ============================================================================

print("\n" + "=" * 80)
print("57. STATUS COMMUNICATION")
print("=" * 80)

status_example = """<p role="status" aria-live="polite">
    Your changes have been saved.
</p>"""

alert_example = """<div role="alert">
    Payment could not be completed.
</div>"""

print("Status:")
print(status_example)

print("\nAlert:")
print(alert_example)

print(
    """
Dynamic interfaces need to communicate important changes to users who may
not see visual updates.

aria-live can identify regions whose changes should be announced.

role="status" is commonly used for non-urgent status updates.

role="alert" is intended for important, time-sensitive information.

Live-region behavior should be used carefully. Excessive announcements can
make an interface difficult to use.
"""
)


# ============================================================================
# 58. ERROR MESSAGE ASSOCIATION
# ============================================================================

print("\n" + "=" * 80)
print("58. FORM ERROR ASSOCIATION")
print("=" * 80)

error_form_example = """<label for="username">Username</label>
<input
    id="username"
    name="username"
    aria-describedby="username-error"
    aria-invalid="true"
>
<p id="username-error">Username is required.</p>"""

print(error_form_example)

print(
    """
aria-describedby associates a control with additional explanatory text.

aria-invalid communicates that the current value is invalid.

The visible error message should still be clear and understandable.
ARIA communicates state and relationships; it does not replace good content
or validation logic.
"""
)


# ============================================================================
# 59. HTML ENTITY UTILITY
# ============================================================================

print("\n" + "=" * 80)
print("59. ENTITY UTILITY")
print("=" * 80)


COMMON_ENTITIES: Dict[str, str] = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
    "©": "&copy;",
    "®": "&reg;",
    "™": "&trade;",
    "€": "&euro;",
    "£": "&pound;",
    "¥": "&yen;",
    "×": "&times;",
    "÷": "&divide;",
    "±": "&plusmn;",
    "→": "&rarr;",
    "←": "&larr;",
    "✓": "&#10003;",
}


def encode_common_entities(text: str) -> str:
    """Replace selected characters with readable HTML character references."""
    for character, entity in COMMON_ENTITIES.items():
        text = text.replace(character, entity)
    return text


entity_text = 'Price: €100 & tax < 10% "estimated" © 2026'
print("Input:")
print(entity_text)

print("\nEncoded:")
print(encode_common_entities(entity_text))


# ============================================================================
# 60. ENTITY DECODING
# ============================================================================

print("\n" + "=" * 80)
print("60. ENTITY DECODING")
print("=" * 80)

from html import unescape

encoded = "&lt;p&gt;Copyright &copy; 2026&lt;/p&gt;"
decoded = unescape(encoded)

print("Encoded:")
print(encoded)

print("\nDecoded:")
print(decoded)

print(
    """
html.unescape() converts HTML character references back into their
corresponding characters.

Encoding and decoding should be applied deliberately according to the
context in which data moves.
"""
)


# ============================================================================
# 61. COMMON HTML MISTAKES
# ============================================================================

print("\n" + "=" * 80)
print("61. COMMON MISTAKES")
print("=" * 80)

mistakes = [
    (
        "Missing lang",
        '<html>',
        '<html lang="en">'
    ),
    (
        "Missing charset",
        "<head><title>Page</title></head>",
        '<head><meta charset="UTF-8"><title>Page</title></head>'
    ),
    (
        "Generic navigation",
        '<div class="nav">...</div>',
        '<nav aria-label="Primary navigation">...</nav>'
    ),
    (
        "Image without alternative",
        '<img src="logo.png">',
        '<img src="logo.png" alt="Company name">'
    ),
    (
        "Generic action container",
        '<div onclick="save()">Save</div>',
        '<button type="button">Save</button>'
    ),
    (
        "Open Graph with name",
        '<meta name="og:title" content="Example">',
        '<meta property="og:title" content="Example">'
    ),
]

for title, bad, good in mistakes:
    print(f"\n{title}")
    print(f"  Bad:  {bad}")
    print(f"  Good: {good}")


# ============================================================================
# 62. ACCESSIBILITY CHECKLIST DATA
# ============================================================================

print("\n" + "=" * 80)
print("62. ACCESSIBILITY CHECKLIST")
print("=" * 80)


accessibility_checklist = [
    "Declare the document language.",
    "Provide a meaningful page title.",
    "Use semantic landmarks.",
    "Maintain a logical heading hierarchy.",
    "Provide appropriate alternative text for informative images.",
    "Use empty alt text for decorative images.",
    "Use real buttons for actions.",
    "Use real links for navigation.",
    "Associate form labels with controls.",
    "Group related form controls when appropriate.",
    "Provide visible and meaningful error messages.",
    "Preserve keyboard access.",
    "Do not remove focus indicators without replacement.",
    "Use ARIA only when native semantics are insufficient.",
    "Ensure dynamic status changes can be communicated appropriately.",
]

for index, item in enumerate(accessibility_checklist, start=1):
    print(f"{index:02}. {item}")


# ============================================================================
# 63. METADATA COMPARISON
# ============================================================================

print("\n" + "=" * 80)
print("63. METADATA COMPARISON")
print("=" * 80)

metadata_comparison = [
    ("title", "Document identity", "<title>"),
    ("description", "Page description", '<meta name="description">'),
    ("canonical", "Preferred URL", '<link rel="canonical">'),
    ("favicon", "Document icon", '<link rel="icon">'),
    ("Open Graph", "Social sharing", '<meta property="og:*">'),
    ("robots", "Crawler directives", '<meta name="robots">'),
    ("viewport", "Responsive viewport", '<meta name="viewport">'),
    ("theme-color", "Browser/platform UI color", '<meta name="theme-color">'),
]

print(f"{'Metadata':15} | {'Purpose':30} | {'Typical syntax'}")
print("-" * 80)

for name, purpose, syntax in metadata_comparison:
    print(f"{name:15} | {purpose:30} | {syntax}")


# ============================================================================
# 64. ACCESSIBILITY SEMANTICS COMPARISON
# ============================================================================

print("\n" + "=" * 80)
print("64. SEMANTIC ELEMENT COMPARISON")
print("=" * 80)

semantic_comparison = [
    ("<main>", "Primary document content", "Use for dominant page content"),
    ("<nav>", "Navigation links", "Use for major navigation groups"),
    ("<article>", "Self-contained content", "Use when content can stand alone"),
    ("<section>", "Thematic grouping", "Normally use with a heading"),
    ("<aside>", "Complementary content", "Use for related secondary content"),
    ("<button>", "User action", "Preferred for actions"),
    ("<a>", "Navigation", "Preferred for URLs/resources"),
    ("<label>", "Form control label", "Associate with a control"),
    ("<figure>", "Self-contained media", "Use with optional figcaption"),
]

print(f"{'Element':15} | {'Meaning':28} | {'Use'}")
print("-" * 90)

for element, meaning, use in semantic_comparison:
    print(f"{element:15} | {meaning:28} | {use}")


# ============================================================================
# 65. PERFORMANCE CONSIDERATIONS
# ============================================================================

print("\n" + "=" * 80)
print("65. PERFORMANCE CONSIDERATIONS")
print("=" * 80)

print(
    """
HTML performance considerations include:

1. Keep the document structure purposeful.
2. Avoid unnecessary resources.
3. Avoid preloading resources without evidence that they are needed.
4. Use responsive images where appropriate.
5. Use loading strategies appropriate to the resource.
6. Keep metadata concise and meaningful.
7. Avoid excessive third-party scripts.
8. Avoid duplicate resource declarations.
9. Preserve a useful document structure before optimizing visual details.
10. Measure real page performance rather than optimizing by assumption.

Metadata itself is usually small. The larger performance impact often comes
from resources referenced by the document, such as images, fonts,
stylesheets, scripts, and third-party services.
"""
)


# ============================================================================
# 66. RESPONSIVE IMAGE EXAMPLE
# ============================================================================

print("\n" + "=" * 80)
print("66. RESPONSIVE IMAGE MARKUP")
print("=" * 80)

responsive_image = """<img
    src="/images/product-800.jpg"
    srcset="
        /images/product-400.jpg 400w,
        /images/product-800.jpg 800w,
        /images/product-1200.jpg 1200w
    "
    sizes="(max-width: 600px) 100vw, 800px"
    alt="Product dashboard displayed on a laptop"
    width="1200"
    height="800"
>"""

print(responsive_image)

print(
    """
srcset provides multiple image resources.

sizes helps the browser estimate the displayed width.

width and height can help reserve layout space and reduce layout shifts.

Responsive image markup is related to HTML performance and accessibility
because resource selection and alternative text are both part of a complete
image implementation.
"""
)


# ============================================================================
# 67. LAZY LOADING
# ============================================================================

print("\n" + "=" * 80)
print("67. IMAGE LOADING STRATEGY")
print("=" * 80)

lazy_image = """<img
    src="/images/article-image.jpg"
    alt="Diagram of HTML metadata relationships"
    loading="lazy"
    width="1200"
    height="700"
>"""

eager_image = """<img
    src="/images/hero.jpg"
    alt="Main product interface"
    width="1600"
    height="900"
>"""

print("Potentially deferred image:")
print(lazy_image)

print("\nImportant above-the-fold image:")
print(eager_image)

print(
    """
loading="lazy" can defer loading of images that are not immediately needed.

It should not be applied blindly to critical above-the-fold images because
deferring important content can harm loading performance.

Performance attributes must reflect the role of the resource.
"""
)


# ============================================================================
# 68. COMPLETE HEAD WITH BROAD METADATA
# ============================================================================

print("\n" + "=" * 80)
print("68. COMPREHENSIVE <head> EXAMPLE")
print("=" * 80)

comprehensive_head = """<head>
    <meta charset="UTF-8">
    <meta name="viewport"
          content="width=device-width, initial-scale=1.0">

    <title>Advanced HTML Concepts</title>

    <meta
        name="description"
        content="A structured HTML reference covering metadata and accessibility."
    >

    <meta name="author" content="Example Author">

    <link
        rel="canonical"
        href="https://example.com/advanced-html"
    >

    <link
        rel="icon"
        type="image/png"
        href="/icons/favicon-32.png"
    >

    <meta name="theme-color" content="#111827">

    <meta
        name="robots"
        content="index, follow"
    >

    <meta
        name="referrer"
        content="strict-origin-when-cross-origin"
    >

    <meta
        property="og:title"
        content="Advanced HTML Concepts"
    >

    <meta
        property="og:description"
        content="Metadata, structure, entities, and accessibility."
    >

    <meta
        property="og:type"
        content="website"
    >

    <meta
        property="og:url"
        content="https://example.com/advanced-html"
    >

    <meta
        property="og:image"
        content="https://example.com/images/advanced-html.jpg"
    >

    <meta
        name="twitter:card"
        content="summary_large_image"
    >

    <meta
        name="twitter:title"
        content="Advanced HTML Concepts"
    >

    <meta
        name="twitter:description"
        content="Metadata, structure, entities, and accessibility."
    >

    <meta
        name="twitter:image"
        content="https://example.com/images/advanced-html.jpg"
    >

    <link rel="stylesheet" href="/css/styles.css">
</head>"""

print(comprehensive_head)


# ============================================================================
# 69. COMPLETE ACCESSIBLE ARTICLE
# ============================================================================

print("\n" + "=" * 80)
print("69. COMPLETE ACCESSIBLE ARTICLE")
print("=" * 80)

article_example = """<article>
    <header>
        <p>HTML reference</p>
        <h1>Metadata and Accessibility</h1>
        <p>
            Published
            <time datetime="2026-09-10">September 10, 2026</time>
        </p>
    </header>

    <section aria-labelledby="metadata">
        <h2 id="metadata">Metadata</h2>

        <p>
            Metadata describes properties of a document and its resources.
        </p>

        <figure>
            <img
                src="/images/head-example.png"
                alt="Example HTML head containing metadata elements"
                width="1200"
                height="700"
            >
            <figcaption>
                A typical HTML head containing metadata.
            </figcaption>
        </figure>
    </section>

    <section aria-labelledby="accessibility">
        <h2 id="accessibility">Accessibility</h2>

        <p>
            Semantic HTML communicates structure to browsers and assistive
            technologies.
        </p>

        <form>
            <label for="search">Search documentation</label>
            <input
                id="search"
                name="search"
                type="search"
            >
            <button type="submit">Search</button>
        </form>
    </section>
</article>"""

print(article_example)


# ============================================================================
# 70. EDGE CASES
# ============================================================================

print("\n" + "=" * 80)
print("70. EDGE CASES")
print("=" * 80)

edge_cases = [
    (
        "Decorative image",
        '<img src="pattern.svg" alt="">',
        "An empty alt is appropriate when the image conveys no meaningful information."
    ),
    (
        "Image containing meaningful text",
        '<img src="announcement.png" alt="Registration closes September 30.">',
        "The alternative should preserve the meaningful information."
    ),
    (
        "Icon-only button",
        '<button type="button" aria-label="Close">×</button>',
        "An accessible name is required when visible content does not identify the action."
    ),
    (
        "Multiple navigation regions",
        '<nav aria-label="Primary">...</nav><nav aria-label="Footer">...</nav>',
        "Labels distinguish similar landmarks."
    ),
    (
        "External link",
        '<a href="https://example.com">Example website</a>',
        "The link text communicates its destination."
    ),
    (
        "Empty section",
        '<section></section>',
        "A section without meaningful thematic content or heading is usually unnecessary."
    ),
]

for name, markup, explanation in edge_cases:
    print(f"\n{name}")
    print(f"Markup: {markup}")
    print(f"Reason: {explanation}")


# ============================================================================
# 71. VALIDATION TESTS
# ============================================================================

print("\n" + "=" * 80)
print("71. VALIDATION TESTS")
print("=" * 80)


def run_assertion_tests() -> None:
    """Run basic assertions for the educational utility functions."""

    assert is_absolute_http_url("https://example.com")
    assert is_absolute_http_url("http://example.com/page")
    assert not is_absolute_http_url("/relative")
    assert not is_absolute_http_url("javascript:alert(1)")

    escaped = make_paragraph("<script>alert(1)</script>")
    assert "<script>" not in escaped
    assert "&lt;script&gt;" in escaped

    escaped_attribute = make_attribute_value('" onclick="alert(1)')
    assert "&quot;" in escaped_attribute

    assert "&amp;" in encode_common_entities("&")
    assert unescape("&copy;") == "©"

    valid_metadata = PageMetadata(
        title="Test",
        description="Test description",
        canonical_url="https://example.com/test",
    )

    assert validate_metadata(valid_metadata) == []

    invalid_metadata = PageMetadata(
        title="",
        description="",
        canonical_url="/relative",
    )

    invalid_issues = validate_metadata(invalid_metadata)

    assert any(issue.level == "ERROR" for issue in invalid_issues)

    good_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <title>Test</title>
</head>
<body>
    <main>
        <h1>Test</h1>
    </main>
</body>
</html>"""

    good_issues = basic_accessibility_check(good_html)

    assert not any(
        issue.severity == "ERROR" for issue in good_issues
    )


run_assertion_tests()
print("All educational assertions passed.")


# ============================================================================
# 72. BAD VERSUS GOOD DOCUMENT
# ============================================================================

print("\n" + "=" * 80)
print("72. BAD VERSUS BETTER STRUCTURE")
print("=" * 80)

bad_structure = """<html>
<head>
    <meta name="og:title" content="Example">
</head>
<body>
    <div class="header">My website</div>
    <div class="navigation">
        <div onclick="location.href='/home'">Home</div>
    </div>
    <div class="content">
        <div class="title">Welcome</div>
        <img src="banner.jpg">
    </div>
</body>
</html>"""

better_structure = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Example Website</title>
    <meta property="og:title" content="Example Website">
</head>
<body>
    <header>
        <h1>My website</h1>
    </header>

    <nav aria-label="Primary navigation">
        <a href="/home">Home</a>
    </nav>

    <main>
        <section aria-labelledby="welcome-heading">
            <h2 id="welcome-heading">Welcome</h2>
            <img
                src="banner.jpg"
                alt="Example website banner"
            >
        </section>
    </main>
</body>
</html>"""

print("Less semantic:")
print(bad_structure)

print("\nMore semantic:")
print(better_structure)


# ============================================================================
# 73. DESIGN PRINCIPLES
# ============================================================================

print("\n" + "=" * 80)
print("73. DESIGN PRINCIPLES")
print("=" * 80)

principles = [
    "Use HTML to express meaning and structure.",
    "Use CSS to control presentation.",
    "Use JavaScript for behavior when HTML cannot provide the required behavior.",
    "Prefer native HTML semantics over custom ARIA implementations.",
    "Keep metadata accurate and consistent with page content.",
    "Treat metadata as information, not security enforcement.",
    "Escape untrusted content for its actual output context.",
    "Write meaningful accessible names.",
    "Preserve keyboard operation.",
    "Use headings to communicate hierarchy.",
    "Use links for navigation and buttons for actions.",
    "Treat performance hints as optimizations that require careful judgment.",
    "Use real parsers rather than regular expressions for production HTML analysis.",
]

for principle in principles:
    print(f"- {principle}")


# ============================================================================
# 74. PRODUCTION CONSIDERATIONS
# ============================================================================

print("\n" + "=" * 80)
print("74. PRODUCTION CONSIDERATIONS")
print("=" * 80)

print(
    """
A production HTML document should be considered as part of a larger system.

Document layer:
    Semantic structure, headings, forms, links, images, and metadata.

Presentation layer:
    CSS controls layout, typography, spacing, colors, responsive behavior,
    and visual states.

Behavior layer:
    JavaScript adds interaction that cannot be expressed through native
    HTML alone.

Server layer:
    Authentication, authorization, validation, content generation, caching,
    security headers, and response handling belong to the application/server
    architecture.

Accessibility:
    Semantic HTML is the foundation, but complete accessibility also depends
    on CSS, JavaScript, interaction design, content, testing, and assistive
    technology behavior.

Security:
    HTML escaping protects the appropriate output context. It does not
    replace server-side validation, authorization, secure headers, or safe
    application architecture.

SEO and discoverability:
    Metadata can provide useful signals, but it does not guarantee ranking,
    indexing, or search snippets.

Social sharing:
    Open Graph and related metadata can improve representation when URLs are
    shared, but the final appearance depends on the receiving platform.

Performance:
    Resource selection, loading order, image sizing, CSS, JavaScript,
    network conditions, caching, and third-party resources usually matter
    more than the small amount of metadata itself.
"""
)


# ============================================================================
# 75. FINAL INTEGRATED EXAMPLE
# ============================================================================

print("\n" + "=" * 80)
print("75. FINAL INTEGRATED HTML EXAMPLE")
print("=" * 80)

final_html = """<!DOCTYPE html>
<html lang="en-IN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport"
          content="width=device-width, initial-scale=1.0">

    <title>HTML Metadata and Accessibility</title>

    <meta
        name="description"
        content="A semantic HTML page demonstrating metadata and accessibility."
    >

    <meta name="author" content="Example Author">

    <link
        rel="canonical"
        href="https://example.com/html-accessibility"
    >

    <link
        rel="icon"
        type="image/png"
        href="/icons/favicon-32.png"
    >

    <meta name="theme-color" content="#111827">

    <meta
        name="robots"
        content="index, follow"
    >

    <meta
        property="og:title"
        content="HTML Metadata and Accessibility"
    >

    <meta
        property="og:description"
        content="Semantic HTML, metadata, entities, and accessibility."
    >

    <meta
        property="og:type"
        content="website"
    >

    <meta
        property="og:url"
        content="https://example.com/html-accessibility"
    >

    <meta
        property="og:image"
        content="https://example.com/images/html-accessibility.jpg"
    >

    <meta
        name="twitter:card"
        content="summary_large_image"
    >

    <link rel="stylesheet" href="/css/styles.css">
</head>

<body>
    <header>
        <h1>HTML Metadata and Accessibility</h1>

        <nav aria-label="Primary navigation">
            <ul>
                <li><a href="/">Home</a></li>
                <li><a href="/metadata">Metadata</a></li>
                <li><a href="/accessibility">Accessibility</a></li>
            </ul>
        </nav>
    </header>

    <main>
        <article>
            <header>
                <h2>Advanced HTML</h2>

                <p>
                    Published
                    <time datetime="2026-09-10">
                        September 10, 2026
                    </time>
                </p>
            </header>

            <section aria-labelledby="structure-heading">
                <h3 id="structure-heading">Document structure</h3>

                <p>
                    Semantic HTML communicates the role and relationships
                    of document content.
                </p>

                <figure>
                    <img
                        src="/images/document-structure.png"
                        alt="Diagram showing HTML document structure with head and body."
                        width="1200"
                        height="800"
                    >

                    <figcaption>
                        A conceptual representation of HTML document structure.
                    </figcaption>
                </figure>
            </section>

            <section aria-labelledby="entities-heading">
                <h3 id="entities-heading">HTML entities</h3>

                <p>
                    HTML can represent special characters such as
                    &copy;, &reg;, &trade;, &lt;, and &amp;.
                </p>
            </section>

            <section aria-labelledby="form-heading">
                <h3 id="form-heading">Accessible form</h3>

                <form>
                    <div>
                        <label for="email">Email address</label>
                        <input
                            id="email"
                            name="email"
                            type="email"
                            autocomplete="email"
                            required
                        >
                    </div>

                    <div>
                        <label for="message">Message</label>
                        <textarea
                            id="message"
                            name="message"
                            rows="5"
                        ></textarea>
                    </div>

                    <button type="submit">
                        Send message
                    </button>
                </form>
            </section>

            <section aria-labelledby="status-heading">
                <h3 id="status-heading">Status</h3>

                <p role="status" aria-live="polite">
                    No changes are currently pending.
                </p>
            </section>
        </article>

        <aside aria-labelledby="related-heading">
            <h2 id="related-heading">Related information</h2>

            <ul>
                <li><a href="/html-semantics">HTML semantics</a></li>
                <li><a href="/web-accessibility">Web accessibility</a></li>
            </ul>
        </aside>
    </main>

    <footer>
        <address>
            Contact:
            <a href="mailto:docs@example.com">docs@example.com</a>
        </address>

        <p>
            &copy; 2026 Example Organization
        </p>
    </footer>
</body>
</html>"""

print(final_html)


# ============================================================================
# 76. FINAL PROGRAMMATIC CHECKS
# ============================================================================

print("\n" + "=" * 80)
print("76. FINAL PROGRAMMATIC CHECKS")
print("=" * 80)

final_issues = basic_accessibility_check(final_html)

print(f"Detected basic accessibility findings: {len(final_issues)}")

for issue in final_issues:
    print(f"[{issue.severity}] {issue.message}")

print("\nFinal metadata:")
print(metadata)

print("\nFinal validation:")
final_metadata_issues = validate_metadata(metadata)

if final_metadata_issues:
    for issue in final_metadata_issues:
        print(f"[{issue.level}] {issue.message}")
else:
    print("Metadata passed the educational structural checks.")


# ============================================================================
# 77. STUDY REFERENCE
# ============================================================================

print("\n" + "=" * 80)
print("77. STUDY REFERENCE")
print("=" * 80)

reference = {
    "Document declaration": "<!DOCTYPE html>",
    "Root element": "<html>",
    "Metadata container": "<head>",
    "Visible document content": "<body>",
    "Primary heading": "<h1>",
    "Primary content": "<main>",
    "Navigation": "<nav>",
    "Independent composition": "<article>",
    "Thematic grouping": "<section>",
    "Complementary content": "<aside>",
    "Document/section footer": "<footer>",
    "Document title": "<title>",
    "Character encoding": '<meta charset="UTF-8">',
    "Responsive viewport": '<meta name="viewport" ...>',
    "Favicon": '<link rel="icon" ...>',
    "Canonical URL": '<link rel="canonical" ...>',
    "Open Graph": '<meta property="og:*" ...>',
    "Image alternative": "alt",
    "Form label": "<label>",
    "Table caption": "<caption>",
    "Table header": "<th>",
    "Machine-readable time": "<time>",
    "Disclosure": "<details>/<summary>",
    "Accessible state": "ARIA attributes when appropriate",
    "HTML escaping": "html.escape()",
}

for concept, syntax in reference.items():
    print(f"{concept:28} -> {syntax}")


print("\n" + "=" * 80)
print("END OF ADVANCED HTML STUDY SCRIPT")
print("=" * 80)
