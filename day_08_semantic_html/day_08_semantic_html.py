"""
Semantic HTML: A Comprehensive Python Study Script

This script teaches Semantic HTML from beginner to advanced level.

Semantic HTML is fundamentally an HTML topic rather than a Python topic.
Python is used here to:

1. Store and explain semantic HTML examples.
2. Validate structural rules in simplified HTML documents.
3. Analyze semantic element usage.
4. Compare semantic and non-semantic markup.
5. Demonstrate accessibility-related document structure.
6. Build progressively more advanced HTML analysis tools.

The script uses only Python's standard library and can be executed directly.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Dict, List, Optional, Set, Tuple


# =============================================================================
# 1. INTRODUCTION TO SEMANTIC HTML
# =============================================================================

print("=" * 80)
print("SEMANTIC HTML: FUNDAMENTALS TO ADVANCED CONCEPTS")
print("=" * 80)

print(
    """
HTML stands for HyperText Markup Language.

Semantic HTML means choosing HTML elements according to the meaning and
purpose of their content rather than choosing elements only for appearance.

For example:

A non-semantic container:

    <div class="navigation">...</div>

A semantic alternative:

    <nav>...</nav>

Both may be styled similarly with CSS, but <nav> communicates the purpose
of the content to browsers, assistive technologies, search engines, and
developers reading the source code.

Semantic HTML improves:

- Accessibility
- Document structure
- Maintainability
- Search engine understanding
- Code readability
- Navigation by assistive technologies
- Long-term application quality
"""
)


# =============================================================================
# 2. SEMANTIC VS NON-SEMANTIC ELEMENTS
# =============================================================================

NON_SEMANTIC_ELEMENTS = {
    "div": "Generic block-level container with no inherent meaning.",
    "span": "Generic inline container with no inherent meaning.",
}

SEMANTIC_ELEMENTS = {
    "header": "Introductory content for a page or section.",
    "nav": "Major navigation links.",
    "main": "The dominant, unique content of the document.",
    "section": "A thematic grouping of content.",
    "article": "Self-contained, independently distributable content.",
    "aside": "Content indirectly related to surrounding content.",
    "footer": "Footer information for a page or section.",
    "figure": "Self-contained content such as an image, diagram, or code example.",
    "figcaption": "Caption or explanation for a figure.",
}

print("\nSEMANTIC ELEMENTS:")
for element, meaning in SEMANTIC_ELEMENTS.items():
    print(f"<{element}>: {meaning}")

print("\nNON-SEMANTIC ELEMENTS:")
for element, meaning in NON_SEMANTIC_ELEMENTS.items():
    print(f"<{element}>: {meaning}")


# =============================================================================
# 3. BASIC SEMANTIC PAGE STRUCTURE
# =============================================================================

basic_semantic_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Semantic HTML Example</title>
</head>
<body>

    <header>
        <h1>Technology Journal</h1>
        <p>Articles about software and technology.</p>
    </header>

    <nav aria-label="Primary navigation">
        <a href="/">Home</a>
        <a href="/articles">Articles</a>
        <a href="/about">About</a>
    </nav>

    <main>
        <section>
            <h2>Featured Articles</h2>

            <article>
                <h3>Understanding Semantic HTML</h3>
                <p>Semantic elements describe the purpose of content.</p>
            </article>
        </section>
    </main>

    <aside>
        <h2>Related Topics</h2>
        <ul>
            <li>Accessibility</li>
            <li>HTML Structure</li>
        </ul>
    </aside>

    <footer>
        <p>Copyright 2026 Technology Journal</p>
    </footer>

</body>
</html>
"""

print("\nBASIC SEMANTIC PAGE EXAMPLE:")
print(basic_semantic_html)


# =============================================================================
# 4. THE HEADER ELEMENT
# =============================================================================

header_example = """
<header>
    <h1>Company Name</h1>
    <p>Professional software services.</p>
</header>
"""

print("\nHEADER EXAMPLE:")
print(header_example)

print(
    """
The <header> element represents introductory content.

It commonly contains:

- Headings
- Branding
- Logos
- Introductory text
- Navigation
- Search controls

A document can contain more than one <header>.

For example, an entire page can have a header and an article inside that
page can also have its own header.
"""
)

nested_header_example = """
<body>

    <header>
        <h1>News Website</h1>
    </header>

    <main>
        <article>
            <header>
                <h2>Semantic HTML Improves Document Structure</h2>
                <p>Published on September 8, 2026</p>
            </header>

            <p>Article content appears here.</p>
        </article>
    </main>

</body>
"""

print("\nPAGE HEADER AND ARTICLE HEADER:")
print(nested_header_example)


# =============================================================================
# 5. THE NAV ELEMENT
# =============================================================================

print(
    """
The <nav> element represents a section containing major navigation links.

Not every group of links should automatically be placed inside <nav>.

Good use cases:

- Primary site navigation
- Major application navigation
- Table of contents
- Pagination navigation

Less appropriate use cases:

- A random collection of links inside article text
- Every small set of links on a page
"""
)

nav_example = """
<nav aria-label="Primary navigation">
    <ul>
        <li><a href="/">Home</a></li>
        <li><a href="/products">Products</a></li>
        <li><a href="/contact">Contact</a></li>
    </ul>
</nav>
"""

print("\nNAVIGATION EXAMPLE:")
print(nav_example)

multiple_nav_example = """
<header>
    <nav aria-label="Primary navigation">
        <a href="/">Home</a>
        <a href="/services">Services</a>
    </nav>
</header>

<footer>
    <nav aria-label="Footer navigation">
        <a href="/privacy">Privacy</a>
        <a href="/terms">Terms</a>
    </nav>
</footer>
"""

print("\nMULTIPLE NAVIGATION REGIONS:")
print(multiple_nav_example)


# =============================================================================
# 6. THE MAIN ELEMENT
# =============================================================================

print(
    """
The <main> element represents the primary content of the document.

Important principle:

A document normally contains one visible <main> element representing the
dominant content.

Content that usually belongs outside <main> includes:

- Repeated site navigation
- Repeated site-wide headers
- Repeated site-wide footers
- Content duplicated across pages

The main content should be meaningful and unique to the current page.
"""
)

main_example = """
<body>

    <header>
        <h1>Learning Platform</h1>
    </header>

    <nav aria-label="Primary navigation">
        <a href="/">Home</a>
        <a href="/courses">Courses</a>
    </nav>

    <main>
        <h2>Python Programming Course</h2>
        <p>This page contains the primary course content.</p>
    </main>

    <footer>
        <p>Copyright 2026</p>
    </footer>

</body>
"""

print("\nMAIN ELEMENT EXAMPLE:")
print(main_example)


# =============================================================================
# 7. THE SECTION ELEMENT
# =============================================================================

print(
    """
The <section> element represents a thematic grouping of content.

A section is appropriate when the content forms a meaningful part of a
larger document.

A section commonly has a heading.

Good example:

    <section>
        <h2>Course Curriculum</h2>
        ...
    </section>

Poor use:

Using <section> only as a generic styling wrapper when no thematic meaning
exists. A <div> is often more appropriate for purely visual grouping.
"""
)

section_example = """
<main>

    <section>
        <h2>Introduction</h2>
        <p>Semantic HTML describes the purpose of content.</p>
    </section>

    <section>
        <h2>Core Elements</h2>
        <p>HTML provides elements such as header, nav, main, and article.</p>
    </section>

</main>
"""

print("\nSECTION EXAMPLE:")
print(section_example)


# =============================================================================
# 8. THE ARTICLE ELEMENT
# =============================================================================

print(
    """
The <article> element represents self-contained content that could make
sense independently.

Typical examples include:

- Blog posts
- News stories
- Forum posts
- Product reviews
- User comments
- Knowledge base articles

A useful test:

"Would this content still make sense if it were extracted and shown somewhere
else?"

If yes, <article> may be appropriate.
"""
)

article_example = """
<article>

    <header>
        <h2>Why Semantic HTML Matters</h2>
        <p>Published by Technical Editor</p>
    </header>

    <p>
        Semantic HTML provides structural meaning that improves accessibility
        and maintainability.
    </p>

    <footer>
        <p>Tags: HTML, Accessibility</p>
    </footer>

</article>
"""

print("\nARTICLE EXAMPLE:")
print(article_example)

article_list_example = """
<main>

    <h1>Latest Articles</h1>

    <article>
        <h2>Article One</h2>
        <p>Independent article content.</p>
    </article>

    <article>
        <h2>Article Two</h2>
        <p>Another independent article.</p>
    </article>

</main>
"""

print("\nMULTIPLE ARTICLES:")
print(article_list_example)


# =============================================================================
# 9. THE ASIDE ELEMENT
# =============================================================================

print(
    """
The <aside> element represents content indirectly related to the surrounding
content.

Common examples include:

- Sidebars
- Related articles
- Author information
- Advertising
- Supplemental notes
- Supporting resources

An aside is not simply "anything placed on the side of the screen".

Semantic meaning depends on the relationship between the content and its
surrounding context.
"""
)

aside_example = """
<article>

    <h1>Introduction to Semantic HTML</h1>

    <p>
        Semantic elements provide meaning to the structure of a document.
    </p>

    <aside>
        <h2>Related Concept</h2>
        <p>
            ARIA attributes can provide additional accessibility information
            when native HTML semantics are insufficient.
        </p>
    </aside>

</article>
"""

print("\nASIDE EXAMPLE:")
print(aside_example)


# =============================================================================
# 10. THE FOOTER ELEMENT
# =============================================================================

print(
    """
The <footer> element represents footer content for its nearest sectioning
context or for the entire page.

A footer can contain:

- Copyright information
- Author information
- Related links
- Contact information
- Publication metadata

Like <header>, <footer> can appear at page level and within elements such
as <article>.
"""
)

footer_example = """
<article>

    <header>
        <h2>Understanding HTML</h2>
    </header>

    <p>Article content.</p>

    <footer>
        <p>Written by Alex Smith</p>
        <p>Published: September 8, 2026</p>
    </footer>

</article>
"""

print("\nARTICLE FOOTER EXAMPLE:")
print(footer_example)


# =============================================================================
# 11. FIGURE AND FIGCAPTION
# =============================================================================

print(
    """
The <figure> element represents self-contained content such as:

- Images
- Charts
- Diagrams
- Illustrations
- Code examples
- Tables when presented as referenced content

The <figcaption> element provides a caption or explanation.

The important relationship is that the figure and caption belong together.
"""
)

figure_example = """
<figure>

    <img
        src="semantic-layout.png"
        alt="Diagram showing header, navigation, main content, aside, and footer"
    >

    <figcaption>
        A simplified example of a semantic HTML page layout.
    </figcaption>

</figure>
"""

print("\nFIGURE EXAMPLE:")
print(figure_example)


# =============================================================================
# 12. ACCESSIBILITY BENEFITS
# =============================================================================

print(
    """
Semantic HTML provides important accessibility benefits.

Assistive technologies can use semantic information to understand document
structure.

Examples:

<nav>
    Identifies a navigation region.

<main>
    Identifies the primary page content.

<header>
    Identifies introductory content.

<article>
    Identifies independent content.

Headings such as <h1>, <h2>, and <h3> create a navigable document hierarchy.

A semantic structure reduces unnecessary dependence on custom accessibility
metadata.
"""
)

accessibility_example = """
<body>

    <header>
        <h1>Digital Library</h1>
    </header>

    <nav aria-label="Primary navigation">
        <a href="/books">Books</a>
        <a href="/authors">Authors</a>
    </nav>

    <main>

        <h2>Featured Book</h2>

        <article>
            <h3>Introduction to Web Standards</h3>
            <p>Book description.</p>
        </article>

    </main>

    <footer>
        <p>Library information</p>
    </footer>

</body>
"""

print("\nACCESSIBLE DOCUMENT STRUCTURE:")
print(accessibility_example)


# =============================================================================
# 13. SEMANTIC HTML VS ARIA
# =============================================================================

print(
    """
HTML semantics and ARIA are related but not interchangeable.

Native semantic HTML should generally be preferred when an appropriate
native element exists.

Prefer:

    <button>Submit</button>

instead of:

    <div role="button">Submit</div>

The native button already provides important built-in behavior and semantics.

A custom element with role="button" may require additional work for:

- Keyboard interaction
- Focus management
- Enter key behavior
- Space key behavior
- Accessibility states
- Disabled behavior

General principle:

Use native HTML semantics first.
Use ARIA when native HTML cannot express the required accessibility meaning
or behavior.
"""
)

native_vs_aria = """
GOOD:

<button type="button">
    Save
</button>


MORE COMPLEX CUSTOM APPROACH:

<div
    role="button"
    tabindex="0"
    aria-label="Save"
>
    Save
</div>
"""

print("\nNATIVE HTML VS CUSTOM ARIA:")
print(native_vs_aria)


# =============================================================================
# 14. SEMANTIC DOCUMENT ANALYZER
# =============================================================================

SEMANTIC_TAGS: Set[str] = {
    "article",
    "aside",
    "details",
    "figcaption",
    "figure",
    "footer",
    "header",
    "main",
    "mark",
    "nav",
    "section",
    "summary",
    "time",
}

LANDMARK_TAGS: Set[str] = {
    "header",
    "nav",
    "main",
    "aside",
    "footer",
}


@dataclass
class SemanticAnalysis:
    """Stores semantic analysis results for an HTML document."""

    tag_counts: Counter = field(default_factory=Counter)
    semantic_tag_counts: Counter = field(default_factory=Counter)
    heading_counts: Counter = field(default_factory=Counter)
    navigation_labels: List[str] = field(default_factory=list)
    main_count: int = 0
    figure_count: int = 0
    figcaption_count: int = 0
    warnings: List[str] = field(default_factory=list)


class SemanticHTMLParser(HTMLParser):
    """
    Simplified HTML parser for educational semantic analysis.

    This parser does not replace a production HTML validator. Its purpose is
    to demonstrate how Python can inspect HTML structure.
    """

    def __init__(self) -> None:
        super().__init__()
        self.analysis = SemanticAnalysis()
        self.open_tags: List[str] = []
        self.figure_stack: List[bool] = []

    def handle_starttag(
        self,
        tag: str,
        attrs: List[Tuple[str, Optional[str]]],
    ) -> None:
        tag = tag.lower()
        attributes = dict(attrs)

        self.analysis.tag_counts[tag] += 1

        if tag in SEMANTIC_TAGS:
            self.analysis.semantic_tag_counts[tag] += 1

        if tag.startswith("h") and len(tag) == 2 and tag[1].isdigit():
            heading_level = int(tag[1])
            if 1 <= heading_level <= 6:
                self.analysis.heading_counts[tag] += 1

        if tag == "main":
            self.analysis.main_count += 1

        if tag == "figure":
            self.analysis.figure_count += 1
            self.figure_stack.append(False)

        if tag == "figcaption":
            self.analysis.figcaption_count += 1

            if not self.figure_stack:
                self.analysis.warnings.append(
                    "<figcaption> appears outside a currently open <figure>."
                )
            else:
                self.figure_stack[-1] = True

        if tag == "nav":
            label = (
                attributes.get("aria-label")
                or attributes.get("aria-labelledby")
            )

            if label:
                self.analysis.navigation_labels.append(label)
            else:
                self.analysis.warnings.append(
                    "<nav> has no explicit accessible label. "
                    "A label can help distinguish multiple navigation regions."
                )

        self.open_tags.append(tag)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()

        if tag == "figure" and self.figure_stack:
            has_caption = self.figure_stack.pop()

            if not has_caption:
                self.analysis.warnings.append(
                    "<figure> does not contain a <figcaption>. "
                    "A caption is optional, but may improve context."
                )

        if tag in self.open_tags:
            last_index = len(self.open_tags) - 1 - self.open_tags[::-1].index(tag)
            self.open_tags.pop(last_index)

    def finalize(self) -> SemanticAnalysis:
        """
        Perform simplified document-level checks.
        """

        if self.analysis.main_count == 0:
            self.analysis.warnings.append(
                "No <main> element was found. "
                "Consider identifying the dominant page content."
            )

        if self.analysis.main_count > 1:
            self.analysis.warnings.append(
                f"{self.analysis.main_count} <main> elements were found. "
                "A standard document should normally expose one primary <main>."
            )

        heading_total = sum(self.analysis.heading_counts.values())

        if heading_total == 0:
            self.analysis.warnings.append(
                "No heading elements were found. "
                "Headings help define navigable document structure."
            )

        if self.analysis.tag_counts["div"] > 10:
            self.analysis.warnings.append(
                "The document contains many <div> elements. "
                "Review whether some containers have a meaningful semantic role."
            )

        return self.analysis


def analyze_html(html_document: str) -> SemanticAnalysis:
    """
    Parse an HTML string and return semantic analysis information.
    """

    parser = SemanticHTMLParser()
    parser.feed(html_document)
    parser.close()
    return parser.finalize()


def print_analysis(analysis: SemanticAnalysis) -> None:
    """Display analysis results in a readable format."""

    print("\n" + "=" * 80)
    print("SEMANTIC HTML ANALYSIS")
    print("=" * 80)

    print("\nAll HTML tags found:")
    for tag, count in sorted(analysis.tag_counts.items()):
        print(f"  <{tag}>: {count}")

    print("\nSemantic tags found:")
    if analysis.semantic_tag_counts:
        for tag, count in sorted(analysis.semantic_tag_counts.items()):
            print(f"  <{tag}>: {count}")
    else:
        print("  No recognized semantic tags found.")

    print("\nHeading structure:")
    if analysis.heading_counts:
        for heading, count in sorted(analysis.heading_counts.items()):
            print(f"  <{heading}>: {count}")
    else:
        print("  No headings found.")

    print(f"\nNumber of <main> elements: {analysis.main_count}")
    print(f"Number of <figure> elements: {analysis.figure_count}")
    print(f"Number of <figcaption> elements: {analysis.figcaption_count}")

    print("\nNavigation labels:")
    if analysis.navigation_labels:
        for label in analysis.navigation_labels:
            print(f"  {label}")
    else:
        print("  No explicit navigation labels found.")

    print("\nWarnings:")
    if analysis.warnings:
        for warning in analysis.warnings:
            print(f"  WARNING: {warning}")
    else:
        print("  No simplified structural warnings found.")


analysis = analyze_html(basic_semantic_html)
print_analysis(analysis)


# =============================================================================
# 15. COMPARING NON-SEMANTIC AND SEMANTIC DOCUMENTS
# =============================================================================

non_semantic_document = """
<div class="page">

    <div class="top">
        <div class="title">Technology Journal</div>
    </div>

    <div class="menu">
        <a href="/">Home</a>
        <a href="/articles">Articles</a>
    </div>

    <div class="content">
        <div class="article">
            <div class="heading">Semantic HTML</div>
            <div class="text">
                Semantic HTML gives structure meaning.
            </div>
        </div>
    </div>

    <div class="bottom">
        Copyright information
    </div>

</div>
"""

semantic_document = """
<header>
    <h1>Technology Journal</h1>
</header>

<nav aria-label="Primary navigation">
    <a href="/">Home</a>
    <a href="/articles">Articles</a>
</nav>

<main>
    <article>
        <h2>Semantic HTML</h2>
        <p>Semantic HTML gives structure meaning.</p>
    </article>
</main>

<footer>
    Copyright information
</footer>
"""

print("\n" + "=" * 80)
print("COMPARISON: NON-SEMANTIC DOCUMENT")
print("=" * 80)

print_analysis(analyze_html(non_semantic_document))

print("\n" + "=" * 80)
print("COMPARISON: SEMANTIC DOCUMENT")
print("=" * 80)

print_analysis(analyze_html(semantic_document))


# =============================================================================
# 16. HEADING HIERARCHY ANALYSIS
# =============================================================================

class HeadingParser(HTMLParser):
    """Extract headings and their text from HTML."""

    def __init__(self) -> None:
        super().__init__()
        self.headings: List[Tuple[int, str]] = []
        self.current_level: Optional[int] = None
        self.current_text_parts: List[str] = []

    def handle_starttag(
        self,
        tag: str,
        attrs: List[Tuple[str, Optional[str]]],
    ) -> None:
        if len(tag) == 2 and tag.startswith("h") and tag[1].isdigit():
            level = int(tag[1])

            if 1 <= level <= 6:
                self.current_level = level
                self.current_text_parts = []

    def handle_data(self, data: str) -> None:
        if self.current_level is not None:
            self.current_text_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if (
            self.current_level is not None
            and tag == f"h{self.current_level}"
        ):
            text = " ".join(
                part.strip()
                for part in self.current_text_parts
                if part.strip()
            )

            self.headings.append((self.current_level, text))
            self.current_level = None
            self.current_text_parts = []


def analyze_heading_hierarchy(html_document: str) -> List[str]:
    """
    Check a simplified heading hierarchy.

    Heading hierarchy is contextual. This function detects large level jumps,
    such as moving directly from h1 to h4.
    """

    parser = HeadingParser()
    parser.feed(html_document)

    warnings: List[str] = []
    previous_level: Optional[int] = None

    for level, text in parser.headings:
        if previous_level is not None and level > previous_level + 1:
            warnings.append(
                f"Heading jump detected: h{previous_level} to h{level} "
                f"before heading '{text}'."
            )

        previous_level = level

    return warnings


good_heading_structure = """
<main>
    <h1>Web Development</h1>

    <section>
        <h2>HTML</h2>

        <section>
            <h3>Semantic HTML</h3>
        </section>
    </section>

    <section>
        <h2>CSS</h2>
    </section>
</main>
"""

problematic_heading_structure = """
<main>
    <h1>Web Development</h1>
    <h4>Semantic HTML</h4>
</main>
"""

print("\n" + "=" * 80)
print("HEADING HIERARCHY ANALYSIS")
print("=" * 80)

print("\nGood structure warnings:")
good_warnings = analyze_heading_hierarchy(good_heading_structure)
print(good_warnings if good_warnings else "No large heading jumps detected.")

print("\nProblematic structure warnings:")
bad_warnings = analyze_heading_hierarchy(problematic_heading_structure)
print(bad_warnings if bad_warnings else "No large heading jumps detected.")


# =============================================================================
# 17. SECTION VS ARTICLE
# =============================================================================

print(
    """
SECTION VS ARTICLE

<section>

Represents a thematic grouping within a larger document.

Example:

    <section>
        <h2>Customer Reviews</h2>
        ...
    </section>

<article>

Represents self-contained content that could potentially be independently
distributed or reused.

Example:

    <article>
        <h2>Review by Customer A</h2>
        ...
    </article>

A section can contain multiple articles.
An article can contain multiple sections.
"""
)

section_article_example = """
<main>

    <section>

        <h1>Latest News</h1>

        <article>
            <h2>Company Announces New Product</h2>
            <p>Independent news story.</p>
        </article>

        <article>
            <h2>Industry Trends for 2026</h2>
            <p>Another independent news story.</p>
        </article>

    </section>

</main>
"""

print("\nSECTION CONTAINING ARTICLES:")
print(section_article_example)


# =============================================================================
# 18. FIGURE, IMAGE, AND ALT TEXT
# =============================================================================

print(
    """
A <figure> and an <img> serve different purposes.

<img>

Represents an image.

<figure>

Groups self-contained content and optionally associates it with a caption.

The alt attribute serves a different purpose from <figcaption>.

alt text:
    Alternative textual representation of the image.

figcaption:
    Visible caption or contextual explanation associated with the figure.

They are not interchangeable.
"""
)

image_accessibility_example = """
<figure>

    <img
        src="sales-chart.png"
        alt="Bar chart showing sales increasing from January to June"
    >

    <figcaption>
        Monthly sales performance during the first half of 2026.
    </figcaption>

</figure>
"""

print("\nIMAGE ACCESSIBILITY EXAMPLE:")
print(image_accessibility_example)


# =============================================================================
# 19. A SEMANTIC PAGE MODEL
# =============================================================================

@dataclass
class SemanticNode:
    """
    A simplified representation of an HTML element.

    This demonstrates how a document can be represented as a semantic tree.
    """

    tag: str
    text: str = ""
    children: List["SemanticNode"] = field(default_factory=list)

    def add_child(self, child: "SemanticNode") -> None:
        self.children.append(child)

    def describe(self, depth: int = 0) -> str:
        indentation = "    " * depth
        description = f"{indentation}<{self.tag}>"

        if self.text:
            description += f" {self.text}"

        lines = [description]

        for child in self.children:
            lines.append(child.describe(depth + 1))

        return "\n".join(lines)


page = SemanticNode("body")

page_header = SemanticNode("header")
page_header.add_child(SemanticNode("h1", "Example Website"))

navigation = SemanticNode("nav")
navigation.add_child(SemanticNode("a", "Home"))
navigation.add_child(SemanticNode("a", "Articles"))

main_content = SemanticNode("main")

content_section = SemanticNode("section")
content_section.add_child(SemanticNode("h2", "Featured Content"))

featured_article = SemanticNode("article")
featured_article.add_child(SemanticNode("h3", "Semantic HTML"))
featured_article.add_child(
    SemanticNode("p", "Meaningful elements describe content purpose.")
)

content_section.add_child(featured_article)
main_content.add_child(content_section)

page_footer = SemanticNode("footer")
page_footer.add_child(SemanticNode("p", "Copyright 2026"))

page.add_child(page_header)
page.add_child(navigation)
page.add_child(main_content)
page.add_child(page_footer)

print("\n" + "=" * 80)
print("SEMANTIC DOCUMENT TREE")
print("=" * 80)
print(page.describe())


# =============================================================================
# 20. COMMON SEMANTIC HTML MISTAKES
# =============================================================================

COMMON_MISTAKES = [
    (
        "Using <div> for meaningful regions",
        "Prefer semantic elements such as <nav>, <main>, or <article> "
        "when their meaning matches the content.",
    ),
    (
        "Using <section> as a generic wrapper",
        "Use <section> for thematic content. Use <div> for purely generic "
        "layout or styling containers.",
    ),
    (
        "Using <article> for content that is not self-contained",
        "Use <article> when the content represents an independent unit.",
    ),
    (
        "Using multiple primary <main> regions",
        "Expose one primary <main> element for the dominant page content.",
    ),
    (
        "Using navigation markup for every group of links",
        "Reserve <nav> for major navigation groups.",
    ),
    (
        "Ignoring heading hierarchy",
        "Use headings to represent logical document structure.",
    ),
    (
        "Replacing native elements with generic ARIA roles",
        "Prefer native semantic elements because they provide built-in "
        "semantics and behavior.",
    ),
    (
        "Treating visual position as semantic meaning",
        "<aside> does not simply mean content displayed at the side.",
    ),
    (
        "Confusing figcaption with alt text",
        "Alt text provides an alternative for image content; figcaption "
        "provides a caption or contextual explanation.",
    ),
]

print("\n" + "=" * 80)
print("COMMON SEMANTIC HTML MISTAKES")
print("=" * 80)

for index, (mistake, correction) in enumerate(COMMON_MISTAKES, start=1):
    print(f"\n{index}. {mistake}")
    print(f"   Correct principle: {correction}")


# =============================================================================
# 21. SIMPLE SEMANTIC SCORING SYSTEM
# =============================================================================

def calculate_semantic_score(html_document: str) -> Dict[str, object]:
    """
    Produce a simplified educational semantic score.

    This is not an official accessibility score or HTML validation system.
    It demonstrates how structural heuristics can be implemented.
    """

    analysis = analyze_html(html_document)

    score = 0
    reasons: List[str] = []

    if analysis.main_count == 1:
        score += 20
        reasons.append("One primary <main> element was found.")
    elif analysis.main_count == 0:
        reasons.append("No <main> element was found.")
    else:
        reasons.append("Multiple <main> elements were found.")

    semantic_count = sum(analysis.semantic_tag_counts.values())

    semantic_points = min(semantic_count * 5, 30)
    score += semantic_points

    reasons.append(
        f"{semantic_count} recognized semantic element instances contributed "
        f"{semantic_points} points."
    )

    heading_total = sum(analysis.heading_counts.values())

    if heading_total > 0:
        score += 15
        reasons.append("Heading structure was detected.")
    else:
        reasons.append("No heading structure was detected.")

    if analysis.tag_counts["nav"] > 0:
        score += 10
        reasons.append("Navigation semantics were detected.")

    if analysis.tag_counts["article"] > 0:
        score += 10
        reasons.append("Article semantics were detected.")

    if analysis.tag_counts["figure"] > 0:
        score += 5
        reasons.append("Figure semantics were detected.")

    penalty = min(len(analysis.warnings) * 5, 25)
    score -= penalty

    if penalty:
        reasons.append(
            f"{len(analysis.warnings)} structural warning(s) caused a "
            f"{penalty}-point penalty."
        )

    score = max(0, min(score, 100))

    return {
        "score": score,
        "reasons": reasons,
        "warnings": analysis.warnings,
    }


print("\n" + "=" * 80)
print("SIMPLIFIED SEMANTIC SCORING")
print("=" * 80)

for document_name, document in [
    ("Non-semantic document", non_semantic_document),
    ("Semantic document", semantic_document),
]:
    result = calculate_semantic_score(document)

    print(f"\n{document_name}")
    print(f"Score: {result['score']}/100")

    print("Reasons:")
    for reason in result["reasons"]:
        print(f"  - {reason}")

    if result["warnings"]:
        print("Warnings:")
        for warning in result["warnings"]:
            print(f"  - {warning}")


# =============================================================================
# 22. REAL-WORLD ARTICLE PAGE EXAMPLE
# =============================================================================

real_world_article_page = """
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta
        name="description"
        content="An article explaining the importance of semantic HTML."
    >
    <title>Understanding Semantic HTML</title>
</head>

<body>

    <header>

        <h1>Web Standards Journal</h1>

        <nav aria-label="Primary navigation">
            <a href="/">Home</a>
            <a href="/articles">Articles</a>
            <a href="/guides">Guides</a>
        </nav>

    </header>

    <main>

        <article>

            <header>

                <h2>Understanding Semantic HTML</h2>

                <p>
                    Published
                    <time datetime="2026-09-08">
                        September 8, 2026
                    </time>
                </p>

            </header>

            <section>

                <h3>Introduction</h3>

                <p>
                    Semantic HTML uses elements whose names communicate the
                    purpose of their content.
                </p>

            </section>

            <section>

                <h3>Document Landmarks</h3>

                <figure>

                    <img
                        src="layout.png"
                        alt="Diagram showing the major semantic regions of a web page"
                    >

                    <figcaption>
                        Common semantic regions in a structured web document.
                    </figcaption>

                </figure>

                <p>
                    Landmarks such as navigation and main content improve
                    structural understanding.
                </p>

            </section>

            <footer>

                <p>
                    Written by the Web Standards Editorial Team.
                </p>

            </footer>

        </article>

        <aside>

            <h2>Related Articles</h2>

            <ul>
                <li>
                    <a href="/accessibility">
                        Introduction to Web Accessibility
                    </a>
                </li>

                <li>
                    <a href="/headings">
                        Designing Heading Hierarchies
                    </a>
                </li>
            </ul>

        </aside>

    </main>

    <footer>

        <nav aria-label="Footer navigation">
            <a href="/privacy">Privacy</a>
            <a href="/contact">Contact</a>
        </nav>

        <p>Copyright 2026 Web Standards Journal</p>

    </footer>

</body>
</html>
"""

print("\n" + "=" * 80)
print("REAL-WORLD SEMANTIC PAGE ANALYSIS")
print("=" * 80)

print_analysis(analyze_html(real_world_article_page))

score_result = calculate_semantic_score(real_world_article_page)

print(f"\nSimplified semantic score: {score_result['score']}/100")


# =============================================================================
# 23. PERFORMANCE AND MAINTAINABILITY CONSIDERATIONS
# =============================================================================

print(
    """
PERFORMANCE AND MAINTAINABILITY

Semantic HTML does not automatically make every application faster, but
meaningful structure can improve maintainability.

Maintainability benefits include:

- Easier source code comprehension
- Reduced dependence on descriptive CSS class names for document meaning
- Clearer separation between content structure and visual presentation
- Easier accessibility review
- More predictable component structure

Performance considerations:

- Semantic elements generally have minimal structural overhead.
- Correct semantic elements do not replace performance optimization.
- Large documents still require efficient CSS, JavaScript, image handling,
  caching, and rendering strategies.
- A semantic document should still avoid unnecessary DOM complexity.

Production consideration:

Use semantic HTML as the structural foundation. Apply CSS for presentation
and JavaScript for behavior rather than using styling classes as the only
source of structural meaning.
"""
)


# =============================================================================
# 24. SECURITY CONSIDERATIONS
# =============================================================================

print(
    """
SECURITY CONSIDERATIONS

Semantic HTML itself is not a security mechanism.

A document using <article>, <section>, or <nav> can still contain security
vulnerabilities if untrusted content is inserted without proper handling.

Important production concerns include:

- Escaping untrusted user input
- Preventing cross-site scripting vulnerabilities
- Sanitizing user-generated HTML when HTML input is permitted
- Validating URLs where appropriate
- Applying browser security controls such as Content Security Policy
- Avoiding unsafe direct HTML insertion

Semantic correctness and security correctness are separate requirements.
"""
)


# =============================================================================
# 25. EDGE CASES AND DESIGN DECISIONS
# =============================================================================

EDGE_CASES = [
    (
        "Should every page have a <header>?",
        "Not necessarily. Use <header> when introductory content exists.",
    ),
    (
        "Should every group of links use <nav>?",
        "No. <nav> is intended for major navigation groups.",
    ),
    (
        "Must every <section> have a heading?",
        "A heading is commonly appropriate because sections represent "
        "thematic regions, although exact document context matters.",
    ),
    (
        "Can an <article> contain a <section>?",
        "Yes. An independent article can contain thematic subsections.",
    ),
    (
        "Can a <section> contain an <article>?",
        "Yes. A thematic group can contain multiple independent articles.",
    ),
    (
        "Can a page contain multiple <header> elements?",
        "Yes. Different sections and articles can have their own headers.",
    ),
    (
        "Can a page contain multiple <footer> elements?",
        "Yes. Articles and sections can have their own footer content.",
    ),
    (
        "Does semantic HTML eliminate the need for CSS?",
        "No. HTML provides structure and meaning; CSS controls presentation.",
    ),
    (
        "Does semantic HTML eliminate the need for JavaScript?",
        "No. JavaScript provides behavior where dynamic interaction is needed.",
    ),
]

print("\n" + "=" * 80)
print("EDGE CASES AND DESIGN DECISIONS")
print("=" * 80)

for question, answer in EDGE_CASES:
    print(f"\nQuestion: {question}")
    print(f"Answer:   {answer}")


# =============================================================================
# 26. PRODUCTION-ORIENTED CHECKLIST
# =============================================================================

PRODUCTION_CHECKLIST = {
    "Document language": "Use the lang attribute on the root html element.",
    "Primary content": "Identify dominant page content with an appropriate main region.",
    "Navigation": "Use nav for major navigation groups.",
    "Headings": "Maintain a meaningful heading hierarchy.",
    "Independent content": "Use article for self-contained content.",
    "Thematic content": "Use section for meaningful thematic grouping.",
    "Supplementary content": "Use aside for tangential or supporting information.",
    "Figures": "Use figure and figcaption when self-contained media needs contextual captioning.",
    "Native controls": "Prefer native semantic controls over generic elements with ARIA roles.",
    "Images": "Provide appropriate alternative text when an image conveys information.",
    "Validation": "Check HTML structure and accessibility with appropriate production tooling.",
    "Security": "Treat untrusted HTML and text as a security concern independent of semantics.",
}

print("\n" + "=" * 80)
print("PRODUCTION-ORIENTED CHECKLIST")
print("=" * 80)

for topic, guidance in PRODUCTION_CHECKLIST.items():
    print(f"\n{topic}:")
    print(f"  {guidance}")


# =============================================================================
# 27. FINAL INTEGRATED DEMONSTRATION
# =============================================================================

integrated_example = """
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <title>Integrated Semantic HTML Demonstration</title>
</head>

<body>

    <header>

        <h1>Knowledge Center</h1>

        <p>
            Structured technical articles and reference material.
        </p>

        <nav aria-label="Primary navigation">
            <a href="/">Home</a>
            <a href="/topics">Topics</a>
            <a href="/contact">Contact</a>
        </nav>

    </header>

    <main>

        <section>

            <h2>Featured Articles</h2>

            <article>

                <header>
                    <h3>Semantic HTML Fundamentals</h3>
                    <p>
                        Published
                        <time datetime="2026-09-08">
                            September 8, 2026
                        </time>
                    </p>
                </header>

                <section>

                    <h4>Document Meaning</h4>

                    <p>
                        Semantic elements describe the role of content within
                        the document.
                    </p>

                </section>

                <figure>

                    <img
                        src="semantic-document.png"
                        alt="A diagram showing semantic HTML regions"
                    >

                    <figcaption>
                        A document divided into meaningful semantic regions.
                    </figcaption>

                </figure>

                <footer>
                    <p>Article category: Web Standards</p>
                </footer>

            </article>

        </section>

        <aside>

            <h2>Related Topics</h2>

            <ul>
                <li>Accessibility</li>
                <li>HTML Document Structure</li>
                <li>Native Web Controls</li>
            </ul>

        </aside>

    </main>

    <footer>

        <nav aria-label="Footer navigation">
            <a href="/privacy">Privacy</a>
            <a href="/terms">Terms</a>
        </nav>

        <p>Copyright 2026 Knowledge Center</p>

    </footer>

</body>
</html>
"""

print("\n" + "=" * 80)
print("FINAL INTEGRATED DEMONSTRATION")
print("=" * 80)

integrated_analysis = analyze_html(integrated_example)
print_analysis(integrated_analysis)

integrated_score = calculate_semantic_score(integrated_example)

print(f"\nFinal simplified semantic score: {integrated_score['score']}/100")

print("\nHeading hierarchy warnings:")
heading_warnings = analyze_heading_hierarchy(integrated_example)

if heading_warnings:
    for warning in heading_warnings:
        print(f"  WARNING: {warning}")
else:
    print("  No large heading-level jumps detected.")

print("\nSemantic HTML study script completed.")
