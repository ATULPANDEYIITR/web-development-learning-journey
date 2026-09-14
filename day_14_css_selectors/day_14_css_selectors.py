"""
CSS Selectors: A Comprehensive Beginner-to-Advanced Study Script

This standalone Python script teaches CSS selectors from absolute beginner
level through advanced concepts.

CSS itself is not executed by Python. Python is used here as an executable
teaching environment to model selector concepts, inspect HTML-like structures,
demonstrate selector matching logic, compare selector types, validate common
selector patterns, and simulate how selectors identify elements.

Core topic:
    CSS Selectors
    - Element selectors
    - Class selectors
    - ID selectors
    - Attribute selectors
    - Descendant selectors
    - Child selectors
    - Sibling selectors
    - Pseudo-class selectors

The examples progressively move from basic selectors to combinators,
attribute matching, pseudo-classes, specificity, selector composition,
edge cases, performance considerations, and practical CSS design.

The script uses only Python's standard library.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable, Optional
import re


# =============================================================================
# 1. FUNDAMENTALS: WHAT IS A CSS SELECTOR?
# =============================================================================

print("=" * 78)
print("CSS SELECTORS: BEGINNER TO ADVANCED")
print("=" * 78)

print(
    """
A CSS selector identifies HTML elements to which CSS declarations can apply.

Basic example:

    p {
        color: blue;
    }

The selector is `p`.
The declaration is `color: blue`.

This script models selector behavior using Python so that selector concepts
can be demonstrated without requiring a browser.
"""
)


# =============================================================================
# 2. HTML-LIKE ELEMENT MODEL
# =============================================================================

@dataclass
class Element:
    """
    A minimal representation of an HTML element.

    Real browsers maintain a much richer DOM. This model contains the
    information needed for the selector concepts demonstrated here.
    """

    tag: str
    id: Optional[str] = None
    classes: set[str] = field(default_factory=set)
    attributes: dict[str, str] = field(default_factory=dict)
    children: list["Element"] = field(default_factory=list)
    parent: Optional["Element"] = field(default=None, repr=False)

    def add_child(self, child: "Element") -> "Element":
        """Add a child and establish the parent relationship."""
        child.parent = self
        self.children.append(child)
        return child

    def descendants(self) -> Iterable["Element"]:
        """Yield every descendant in depth-first order."""
        for child in self.children:
            yield child
            yield from child.descendants()

    def ancestors(self) -> Iterable["Element"]:
        """Yield ancestors from parent toward the document root."""
        current = self.parent
        while current is not None:
            yield current
            current = current.parent

    def siblings(self) -> list["Element"]:
        """Return elements sharing the same parent."""
        if self.parent is None:
            return []
        return [
            sibling
            for sibling in self.parent.children
            if sibling is not self
        ]

    def next_siblings(self) -> list["Element"]:
        """Return siblings appearing after this element."""
        if self.parent is None:
            return []
        siblings = self.parent.children
        try:
            index = siblings.index(self)
        except ValueError:
            return []
        return siblings[index + 1 :]

    def previous_siblings(self) -> list["Element"]:
        """Return siblings appearing before this element."""
        if self.parent is None:
            return []
        siblings = self.parent.children
        try:
            index = siblings.index(self)
        except ValueError:
            return []
        return siblings[:index]

    def has_class(self, class_name: str) -> bool:
        """Check whether the element has a particular class."""
        return class_name in self.classes

    def get_attribute(self, name: str) -> Optional[str]:
        """Return an attribute value, or None if the attribute is absent."""
        return self.attributes.get(name)

    def has_attribute(self, name: str) -> bool:
        """Check whether an attribute exists."""
        return name in self.attributes

    def description(self) -> str:
        """Return a compact CSS-like representation."""
        parts = [self.tag]

        if self.id:
            parts.append(f"#{self.id}")

        for class_name in sorted(self.classes):
            parts.append(f".{class_name}")

        return "".join(parts)


# =============================================================================
# 3. BUILD A SMALL HTML TREE
# =============================================================================

root = Element("html")

body = root.add_child(Element("body", classes={"page"}))

header = body.add_child(
    Element(
        "header",
        id="site-header",
        classes={"site-header", "dark"},
        attributes={"data-section": "header"},
    )
)

nav = header.add_child(
    Element(
        "nav",
        classes={"navigation"},
        attributes={"aria-label": "Primary navigation"},
    )
)

home_link = nav.add_child(
    Element(
        "a",
        id="home-link",
        classes={"nav-link", "active"},
        attributes={
            "href": "/",
            "data-page": "home",
            "aria-current": "page",
        },
    )
)

products_link = nav.add_child(
    Element(
        "a",
        classes={"nav-link"},
        attributes={
            "href": "/products",
            "data-page": "products",
        },
    )
)

contact_link = nav.add_child(
    Element(
        "a",
        classes={"nav-link"},
        attributes={
            "href": "/contact",
            "data-page": "contact",
        },
    )
)

main = body.add_child(
    Element(
        "main",
        id="main-content",
        classes={"content"},
        attributes={"data-layout": "two-column"},
    )
)

article = main.add_child(
    Element(
        "article",
        classes={"article", "featured"},
        attributes={"data-type": "post"},
    )
)

heading = article.add_child(
    Element(
        "h1",
        id="article-title",
        classes={"title", "featured-title"},
        attributes={"data-level": "primary"},
    )
)

intro = article.add_child(
    Element(
        "p",
        classes={"intro", "lead"},
        attributes={"data-priority": "high"},
    )
)

content_section = article.add_child(
    Element(
        "section",
        classes={"content-section"},
        attributes={"data-section": "body"},
    )
)

paragraph_one = content_section.add_child(
    Element(
        "p",
        classes={"text"},
        attributes={"data-kind": "paragraph"},
    )
)

paragraph_two = content_section.add_child(
    Element(
        "p",
        classes={"text", "highlight"},
        attributes={
            "data-kind": "paragraph",
            "data-status": "important",
        },
    )
)

footer = body.add_child(
    Element(
        "footer",
        id="site-footer",
        classes={"footer"},
        attributes={"data-section": "footer"},
    )
)

footer_link = footer.add_child(
    Element(
        "a",
        classes={"footer-link"},
        attributes={"href": "/privacy"},
    )
)


ALL_ELEMENTS = [root, *list(root.descendants())]


def show_elements(elements: Iterable[Element], title: str) -> None:
    """Display matched elements in a consistent format."""
    print(f"\n{title}")
    print("-" * len(title))

    elements = list(elements)

    if not elements:
        print("(no matches)")
        return

    for element in elements:
        print(element.description())


# =============================================================================
# 4. BASIC SELECTOR MATCHING
# =============================================================================

def select_all(
    elements: Iterable[Element],
    predicate: Callable[[Element], bool],
) -> list[Element]:
    """Return elements satisfying a selector predicate."""
    return [element for element in elements if predicate(element)]


# -----------------------------------------------------------------------------
# 4.1 UNIVERSAL SELECTOR
# -----------------------------------------------------------------------------

print("\n" + "=" * 78)
print("1. UNIVERSAL SELECTOR")
print("=" * 78)

print(
    """
The universal selector is:

    *

It matches every element.

Example:

    * {
        box-sizing: border-box;
    }

Universal selectors are useful for broad normalization and global rules.
"""
)

universal_matches = select_all(ALL_ELEMENTS, lambda element: True)
show_elements(universal_matches, "Selector: *")


# -----------------------------------------------------------------------------
# 4.2 ELEMENT SELECTOR
# -----------------------------------------------------------------------------

print("\n" + "=" * 78)
print("2. ELEMENT SELECTOR")
print("=" * 78)

print(
    """
An element selector uses an HTML tag name.

Examples:

    p
    h1
    article
    a
    button

The selector:

    p {
        line-height: 1.6;
    }

matches every paragraph element.
"""
)

paragraph_matches = select_all(
    ALL_ELEMENTS,
    lambda element: element.tag == "p",
)
show_elements(paragraph_matches, "Selector: p")

heading_matches = select_all(
    ALL_ELEMENTS,
    lambda element: element.tag == "h1",
)
show_elements(heading_matches, "Selector: h1")


# =============================================================================
# 5. CLASS SELECTORS
# =============================================================================

print("\n" + "=" * 78)
print("3. CLASS SELECTOR")
print("=" * 78)

print(
    """
A class selector begins with a period.

Example:

    .button {
        padding: 10px;
    }

HTML:

    <button class="button">Save</button>

A class is reusable. Many elements can share the same class.

An element may also have multiple classes:

    <p class="text highlight">Important content</p>
"""
)


def class_selector(class_name: str) -> Callable[[Element], bool]:
    """Create a predicate equivalent to a CSS .class selector."""
    return lambda element: element.has_class(class_name)


text_matches = select_all(ALL_ELEMENTS, class_selector("text"))
show_elements(text_matches, "Selector: .text")

highlight_matches = select_all(ALL_ELEMENTS, class_selector("highlight"))
show_elements(highlight_matches, "Selector: .highlight")


# =============================================================================
# 6. ID SELECTORS
# =============================================================================

print("\n" + "=" * 78)
print("4. ID SELECTOR")
print("=" * 78)

print(
    """
An ID selector begins with #.

Example:

    #main-content {
        max-width: 1200px;
    }

HTML:

    <main id="main-content">

An ID is intended to uniquely identify one element within a document.

Important distinction:

    .content       -> class selector
    #main-content  -> ID selector

Classes are normally preferred for reusable styling.
IDs have higher specificity and can make CSS harder to override when
overused for styling.
"""
)


def id_selector(identifier: str) -> Callable[[Element], bool]:
    """Create a predicate equivalent to a CSS #id selector."""
    return lambda element: element.id == identifier


main_matches = select_all(
    ALL_ELEMENTS,
    id_selector("main-content"),
)
show_elements(main_matches, "Selector: #main-content")


# =============================================================================
# 7. COMBINING ELEMENT, CLASS, AND ID SELECTORS
# =============================================================================

print("\n" + "=" * 78)
print("5. COMPOUND SELECTORS")
print("=" * 78)

print(
    """
Multiple simple selectors can be combined without a space.

Examples:

    p.text
    article.featured
    a.nav-link
    h1#article-title

The lack of a space is important.

    p.text

means:

    a p element that also has the class text

It does NOT mean all p elements and all .text elements separately.
"""
)


def compound_selector(
    tag: Optional[str] = None,
    identifier: Optional[str] = None,
    classes: Optional[set[str]] = None,
) -> Callable[[Element], bool]:
    """Create a simple compound-selector predicate."""
    classes = classes or set()

    def matches(element: Element) -> bool:
        if tag is not None and element.tag != tag:
            return False

        if identifier is not None and element.id != identifier:
            return False

        if not classes.issubset(element.classes):
            return False

        return True

    return matches


article_featured = select_all(
    ALL_ELEMENTS,
    compound_selector(tag="article", classes={"featured"}),
)
show_elements(article_featured, "Selector: article.featured")

text_highlight = select_all(
    ALL_ELEMENTS,
    compound_selector(tag="p", classes={"text", "highlight"}),
)
show_elements(text_highlight, "Selector: p.text.highlight")

title_selector = select_all(
    ALL_ELEMENTS,
    compound_selector(
        tag="h1",
        identifier="article-title",
        classes={"title"},
    ),
)
show_elements(title_selector, "Selector: h1#article-title.title")


# =============================================================================
# 8. DESCENDANT SELECTOR
# =============================================================================

print("\n" + "=" * 78)
print("6. DESCENDANT SELECTOR")
print("=" * 78)

print(
    """
A descendant selector contains whitespace.

Example:

    article p

This means:

    Select every p that is somewhere inside article.

The paragraph does not have to be a direct child.

Structure:

    article
      section
        p

The p is still a descendant of article.
"""
)


def is_descendant_of(element: Element, ancestor: Element) -> bool:
    """Return True when ancestor appears anywhere above element."""
    return any(parent is ancestor for parent in element.ancestors())


def descendant_selector(
    ancestor_tag: str,
    descendant_tag: str,
) -> Callable[[Element], bool]:
    """
    Model a simple `ancestor descendant` selector.

    This implementation uses tag names for clarity.
    """
    def matches(element: Element) -> bool:
        if element.tag != descendant_tag:
            return False

        return any(
            ancestor.tag == ancestor_tag
            for ancestor in element.ancestors()
        )

    return matches


article_paragraphs = select_all(
    ALL_ELEMENTS,
    descendant_selector("article", "p"),
)
show_elements(article_paragraphs, "Selector: article p")

print(
    """
Important:
    `article p` can match deeply nested paragraphs.

That is different from:

    article > p

which only matches direct children.
"""
)


# =============================================================================
# 9. CHILD SELECTOR
# =============================================================================

print("\n" + "=" * 78)
print("7. CHILD SELECTOR")
print("=" * 78)

print(
    """
The child combinator is >.

Example:

    nav > a

This selects a elements that are direct children of nav.

It does not match:

    nav
      div
        a

because that a is not a direct child of nav.
"""
)


def child_selector(
    parent_tag: str,
    child_tag: str,
) -> Callable[[Element], bool]:
    """Model `parent > child`."""
    def matches(element: Element) -> bool:
        return (
            element.tag == child_tag
            and element.parent is not None
            and element.parent.tag == parent_tag
        )

    return matches


direct_nav_links = select_all(
    ALL_ELEMENTS,
    child_selector("nav", "a"),
)
show_elements(direct_nav_links, "Selector: nav > a")


# =============================================================================
# 10. DESCENDANT VERSUS CHILD
# =============================================================================

print("\n" + "=" * 78)
print("8. DESCENDANT VS CHILD")
print("=" * 78)

print(
    """
Comparison:

    article p
        Matches p elements at any descendant depth.

    article > p
        Matches only p elements directly inside article.

This distinction is one of the most common sources of CSS selector
misunderstanding.
"""
)

article_direct_paragraphs = select_all(
    ALL_ELEMENTS,
    child_selector("article", "p"),
)

show_elements(
    article_paragraphs,
    "article p -> all paragraph descendants",
)

show_elements(
    article_direct_paragraphs,
    "article > p -> direct paragraph children",
)


# =============================================================================
# 11. ADJACENT SIBLING SELECTOR
# =============================================================================

print("\n" + "=" * 78)
print("9. ADJACENT SIBLING SELECTOR")
print("=" * 78)

print(
    """
The adjacent sibling combinator is +.

Example:

    h1 + p

It selects a p element immediately following an h1 under the same parent.

The elements must share a parent and the target must be the next sibling.
"""
)


def adjacent_sibling_selector(
    first_tag: str,
    second_tag: str,
) -> Callable[[Element], bool]:
    """Model `first + second`."""
    def matches(element: Element) -> bool:
        if element.tag != second_tag or element.parent is None:
            return False

        siblings = element.parent.children
        index = siblings.index(element)

        return (
            index > 0
            and siblings[index - 1].tag == first_tag
        )

    return matches


heading_followed_by_paragraph = select_all(
    ALL_ELEMENTS,
    adjacent_sibling_selector("h1", "p"),
)
show_elements(heading_followed_by_paragraph, "Selector: h1 + p")


# =============================================================================
# 12. GENERAL SIBLING SELECTOR
# =============================================================================

print("\n" + "=" * 78)
print("10. GENERAL SIBLING SELECTOR")
print("=" * 78)

print(
    """
The general sibling combinator is ~.

Example:

    h1 ~ p

It selects p elements that appear later than an h1 and share the same parent.

Unlike +, the target does not have to be immediately adjacent.
"""
)


def general_sibling_selector(
    first_tag: str,
    second_tag: str,
) -> Callable[[Element], bool]:
    """Model `first ~ second`."""
    def matches(element: Element) -> bool:
        if element.tag != second_tag or element.parent is None:
            return False

        siblings_before = element.previous_siblings()

        return any(
            sibling.tag == first_tag
            for sibling in siblings_before
        )

    return matches


general_sibling_matches = select_all(
    ALL_ELEMENTS,
    general_sibling_selector("h1", "p"),
)
show_elements(general_sibling_matches, "Selector: h1 ~ p")


# =============================================================================
# 13. ATTRIBUTE SELECTORS
# =============================================================================

print("\n" + "=" * 78)
print("11. ATTRIBUTE SELECTORS")
print("=" * 78)

print(
    """
Attribute selectors target elements according to HTML attributes.

Common forms:

    [disabled]
    [type="email"]
    [href^="https"]
    [href$=".pdf"]
    [class*="button"]
    [data-role~="admin"]
    [lang|="en"]

Attribute selectors are especially useful for semantic HTML, forms,
links, accessibility states, data attributes, and component APIs.
"""
)


def attribute_exists(
    attribute_name: str,
) -> Callable[[Element], bool]:
    """Model `[attribute]`."""
    return lambda element: element.has_attribute(attribute_name)


def attribute_equals(
    attribute_name: str,
    expected: str,
) -> Callable[[Element], bool]:
    """Model `[attribute="value"]`."""
    return lambda element: (
        element.get_attribute(attribute_name) == expected
    )


href_matches = select_all(
    ALL_ELEMENTS,
    attribute_exists("href"),
)
show_elements(href_matches, "Selector: [href]")

home_attribute = select_all(
    ALL_ELEMENTS,
    attribute_equals("data-page", "home"),
)
show_elements(home_attribute, 'Selector: [data-page="home"]')


# -----------------------------------------------------------------------------
# 13.1 ATTRIBUTE PREFIX MATCH
# -----------------------------------------------------------------------------

def attribute_prefix(
    attribute_name: str,
    prefix: str,
) -> Callable[[Element], bool]:
    """Model `[attribute^="prefix"]`."""
    return lambda element: (
        (value := element.get_attribute(attribute_name)) is not None
        and value.startswith(prefix)
    )


https_links = select_all(
    ALL_ELEMENTS,
    attribute_prefix("href", "https"),
)
show_elements(https_links, 'Selector: [href^="https"]')


# -----------------------------------------------------------------------------
# 13.2 ATTRIBUTE SUFFIX MATCH
# -----------------------------------------------------------------------------

def attribute_suffix(
    attribute_name: str,
    suffix: str,
) -> Callable[[Element], bool]:
    """Model `[attribute$="suffix"]`."""
    return lambda element: (
        (value := element.get_attribute(attribute_name)) is not None
        and value.endswith(suffix)
    )


pdf_links = select_all(
    ALL_ELEMENTS,
    attribute_suffix("href", ".pdf"),
)
show_elements(pdf_links, 'Selector: [href$=".pdf"]')


# -----------------------------------------------------------------------------
# 13.3 ATTRIBUTE SUBSTRING MATCH
# -----------------------------------------------------------------------------

def attribute_contains(
    attribute_name: str,
    substring: str,
) -> Callable[[Element], bool]:
    """Model `[attribute*="substring"]`."""
    return lambda element: (
        (value := element.get_attribute(attribute_name)) is not None
        and substring in value
    )


navigation_attributes = select_all(
    ALL_ELEMENTS,
    attribute_contains("data-page", "pro"),
)
show_elements(
    navigation_attributes,
    '[data-page*="pro"]',
)


# -----------------------------------------------------------------------------
# 13.4 ATTRIBUTE WORD MATCH
# -----------------------------------------------------------------------------

def attribute_word(
    attribute_name: str,
    word: str,
) -> Callable[[Element], bool]:
    """
    Model `[attribute~="word"]`.

    The CSS ~= operator treats the attribute as a whitespace-separated
    list of words.
    """
    return lambda element: (
        (value := element.get_attribute(attribute_name)) is not None
        and word in value.split()
    )


# Add an example multi-word attribute.
article.attributes["data-role"] = "post featured"


role_featured = select_all(
    ALL_ELEMENTS,
    attribute_word("data-role", "featured"),
)
show_elements(
    role_featured,
    '[data-role~="featured"]',
)


# -----------------------------------------------------------------------------
# 13.5 ATTRIBUTE LANGUAGE RANGE MATCH
# -----------------------------------------------------------------------------

print(
    """
The |= operator has special semantics commonly used with language-like
values.

Example:

    [lang|="en"]

can match `en` and values beginning with `en-`, such as `en-US`.
"""
)


def attribute_dash_prefix(
    attribute_name: str,
    value: str,
) -> Callable[[Element], bool]:
    """Model `[attribute|="value"]`."""
    def matches(element: Element) -> bool:
        actual = element.get_attribute(attribute_name)

        if actual is None:
            return False

        return actual == value or actual.startswith(value + "-")

    return matches


paragraph_one.attributes["lang"] = "en-US"

english_elements = select_all(
    ALL_ELEMENTS,
    attribute_dash_prefix("lang", "en"),
)
show_elements(
    english_elements,
    '[lang|="en"]',
)


# =============================================================================
# 14. CASE SENSITIVITY AND ATTRIBUTE VALUES
# =============================================================================

print("\n" + "=" * 78)
print("12. ATTRIBUTE MATCHING AND CASE")
print("=" * 78)

print(
    """
CSS attribute matching has nuanced case behavior.

For ordinary HTML attribute names, matching attribute names is generally
case-insensitive in HTML documents. Attribute values depend on the attribute
and matching rules.

CSS also supports explicit case modifiers in attribute selectors:

    [data-value="abc" i]
        ASCII case-insensitive comparison.

    [data-value="abc" s]
        Explicit ASCII case-sensitive comparison.

Browser behavior, HTML semantics, and the definition of a particular
attribute can affect the details. Avoid assuming that every attribute value
is universally case-insensitive.
"""
)


# =============================================================================
# 15. PSEUDO-CLASSES
# =============================================================================

print("\n" + "=" * 78)
print("13. PSEUDO-CLASSES")
print("=" * 78)

print(
    """
A pseudo-class begins with a single colon.

Examples:

    :hover
    :focus
    :active
    :visited
    :first-child
    :last-child
    :nth-child(2)
    :not(...)
    :is(...)
    :where(...)
    :has(...)

Pseudo-classes select elements according to a state, relationship, position,
or logical condition rather than requiring an actual class attribute.
"""
)


# =============================================================================
# 16. STRUCTURAL PSEUDO-CLASSES
# =============================================================================

print("\n" + "=" * 78)
print("14. :first-child")
print("=" * 78)

print(
    """
:first-child matches an element that is the first child of its parent.

Example:

    li:first-child {
        margin-top: 0;
    }
"""
)


def first_child(element: Element) -> bool:
    """Model `:first-child`."""
    return (
        element.parent is not None
        and bool(element.parent.children)
        and element.parent.children[0] is element
    )


first_children = select_all(ALL_ELEMENTS, first_child)
show_elements(first_children, "Pseudo-class: :first-child")


# -----------------------------------------------------------------------------
# :last-child
# -----------------------------------------------------------------------------

def last_child(element: Element) -> bool:
    """Model `:last-child`."""
    return (
        element.parent is not None
        and bool(element.parent.children)
        and element.parent.children[-1] is element
    )


last_children = select_all(ALL_ELEMENTS, last_child)
show_elements(last_children, "Pseudo-class: :last-child")


# -----------------------------------------------------------------------------
# :only-child
# -----------------------------------------------------------------------------

def only_child(element: Element) -> bool:
    """Model `:only-child`."""
    return (
        element.parent is not None
        and len(element.parent.children) == 1
    )


only_children = select_all(ALL_ELEMENTS, only_child)
show_elements(only_children, "Pseudo-class: :only-child")


# =============================================================================
# 17. :nth-child()
# =============================================================================

print("\n" + "=" * 78)
print("15. :nth-child()")
print("=" * 78)

print(
    """
:nth-child() selects children according to their position.

Examples:

    :nth-child(1)
    :nth-child(2)
    :nth-child(odd)
    :nth-child(even)
    :nth-child(3n)
    :nth-child(2n + 1)

CSS uses one-based child positions.
"""
)


def nth_child(element: Element, position: int) -> bool:
    """Model `:nth-child(position)` using one-based indexing."""
    if element.parent is None:
        return False

    try:
        index = element.parent.children.index(element) + 1
    except ValueError:
        return False

    return index == position


second_children = select_all(
    ALL_ELEMENTS,
    lambda element: nth_child(element, 2),
)
show_elements(second_children, "Pseudo-class: :nth-child(2)")


def nth_pattern(element: Element, a: int, b: int) -> bool:
    """
    Model the mathematical CSS An+B form.

    A position matches if:
        position = A*n + B
    for some integer n >= 0.

    CSS additionally permits special keywords such as odd and even.
    """
    if element.parent is None:
        return False

    position = element.parent.children.index(element) + 1

    if a == 0:
        return position == b

    difference = position - b

    if a > 0:
        return difference >= 0 and difference % a == 0

    # Negative A values produce finite sequences.
    return difference <= 0 and difference % a == 0


odd_children = select_all(
    ALL_ELEMENTS,
    lambda element: nth_pattern(element, 2, 1),
)
show_elements(odd_children, "Pseudo-class: :nth-child(2n + 1)")


even_children = select_all(
    ALL_ELEMENTS,
    lambda element: nth_pattern(element, 2, 0),
)
show_elements(even_children, "Pseudo-class: :nth-child(2n)")


# =============================================================================
# 18. :nth-of-type()
# =============================================================================

print("\n" + "=" * 78)
print("16. :nth-of-type()")
print("=" * 78)

print(
    """
:nth-of-type() counts only siblings of the same element type.

This differs from :nth-child(), which counts all element children.

For example:

    p:nth-of-type(2)

means the second p among the p siblings, not necessarily the second child.
"""
)


def nth_of_type(element: Element, position: int) -> bool:
    """Model `:nth-of-type(position)`."""
    if element.parent is None:
        return False

    same_type = [
        child
        for child in element.parent.children
        if child.tag == element.tag
    ]

    return element in same_type and same_type.index(element) + 1 == position


second_paragraph_of_type = select_all(
    ALL_ELEMENTS,
    lambda element: nth_of_type(element, 2),
)
show_elements(
    second_paragraph_of_type,
    "Pseudo-class: :nth-of-type(2)",
)


# =============================================================================
# 19. :first-of-type AND :last-of-type
# =============================================================================

def first_of_type(element: Element) -> bool:
    """Model `:first-of-type`."""
    if element.parent is None:
        return False

    same_type = [
        child
        for child in element.parent.children
        if child.tag == element.tag
    ]

    return bool(same_type) and same_type[0] is element


def last_of_type(element: Element) -> bool:
    """Model `:last-of-type`."""
    if element.parent is None:
        return False

    same_type = [
        child
        for child in element.parent.children
        if child.tag == element.tag
    ]

    return bool(same_type) and same_type[-1] is element


show_elements(
    select_all(ALL_ELEMENTS, first_of_type),
    "Pseudo-class: :first-of-type",
)

show_elements(
    select_all(ALL_ELEMENTS, last_of_type),
    "Pseudo-class: :last-of-type",
)


# =============================================================================
# 20. STATE PSEUDO-CLASSES
# =============================================================================

print("\n" + "=" * 78)
print("17. STATE PSEUDO-CLASSES")
print("=" * 78)

print(
    """
Common state pseudo-classes include:

    :hover
        Pointer is over the element.

    :focus
        Element currently has focus.

    :focus-visible
        Focus indication should be presented according to browser heuristics.

    :active
        Element is being activated.

    :visited
        Link has been visited.

    :checked
        Checkbox, radio button, or compatible control is checked.

    :disabled
        Form control is disabled.

    :enabled
        Form control is enabled.

    :required
        Form control is required.

    :optional
        Form control is not required.

    :valid
        Form control currently satisfies validation constraints.

    :invalid
        Form control currently fails validation constraints.
"""
)

print(
    """
State pseudo-classes are dynamic. Their match can change without changing
the HTML source.

For example:

    button:hover {
        transform: translateY(-2px);
    }

A Python data model cannot reproduce browser pointer and focus behavior,
so these states are represented conceptually rather than simulated as real
browser events.
"""
)


# =============================================================================
# 21. LOGICAL PSEUDO-CLASSES
# =============================================================================

print("\n" + "=" * 78)
print("18. LOGICAL PSEUDO-CLASSES")
print("=" * 78)

print(
    """
CSS provides powerful logical selectors.

:is(...)
    Matches an element matching at least one selector in the list.

:not(...)
    Matches an element that does not match the supplied selector.

:where(...)
    Similar to :is(), but contributes zero specificity.

:has(...)
    Relational pseudo-class. It selects an element based on what it contains
    or what is related to it.
"""
)


def logical_is(
    *predicates: Callable[[Element], bool],
) -> Callable[[Element], bool]:
    """Model `:is(selector1, selector2, ...)`."""
    return lambda element: any(
        predicate(element)
        for predicate in predicates
    )


def logical_not(
    predicate: Callable[[Element], bool],
) -> Callable[[Element], bool]:
    """Model `:not(selector)`."""
    return lambda element: not predicate(element)


is_heading_or_article = logical_is(
    lambda element: element.tag == "h1",
    lambda element: element.tag == "article",
)

show_elements(
    select_all(ALL_ELEMENTS, is_heading_or_article),
    "Logical selector concept: :is(h1, article)",
)

not_paragraph = logical_not(lambda element: element.tag == "p")

show_elements(
    select_all(ALL_ELEMENTS, not_paragraph),
    "Logical selector concept: :not(p)",
)


# =============================================================================
# 22. :HAS() RELATIONAL SELECTOR
# =============================================================================

print("\n" + "=" * 78)
print("19. :has()")
print("=" * 78)

print(
    """
:has() is a relational pseudo-class.

Example:

    article:has(h1)

This selects articles containing an h1 descendant.

Another example:

    nav:has(a.active)

This selects a nav containing an active link.

This is powerful because traditional CSS selection was primarily based on
matching an element itself or moving from an ancestor to a descendant.
:has() allows conditions based on related elements.
"""
)


def has_descendant_tag(tag_name: str) -> Callable[[Element], bool]:
    """Model `:has(tag)` using descendant tags."""
    def matches(element: Element) -> bool:
        return any(
            descendant.tag == tag_name
            for descendant in element.descendants()
        )

    return matches


articles_with_heading = select_all(
    ALL_ELEMENTS,
    lambda element: (
        element.tag == "article"
        and has_descendant_tag("h1")(element)
    ),
)
show_elements(
    articles_with_heading,
    "Relational selector concept: article:has(h1)",
)


# =============================================================================
# 23. MULTIPLE SELECTORS / SELECTOR LISTS
# =============================================================================

print("\n" + "=" * 78)
print("20. SELECTOR LISTS")
print("=" * 78)

print(
    """
A comma creates a selector list.

Example:

    h1, h2, h3 {
        font-family: sans-serif;
    }

This applies the same rule to all three selector groups.

The selectors remain logically separate.

A selector list is different from:

    h1 h2

which means an h2 descendant of an h1.
"""
)


def selector_list(
    *predicates: Callable[[Element], bool],
) -> Callable[[Element], bool]:
    """Model a comma-separated selector list."""
    return logical_is(*predicates)


heading_or_paragraph = selector_list(
    lambda element: element.tag == "h1",
    lambda element: element.tag == "p",
)

show_elements(
    select_all(ALL_ELEMENTS, heading_or_paragraph),
    "Selector list: h1, p",
)


# =============================================================================
# 24. NESTED COMBINATIONS
# =============================================================================

print("\n" + "=" * 78)
print("21. COMBINING SELECTORS")
print("=" * 78)

print(
    """
Selectors can be combined to describe precise relationships.

Examples:

    nav a
        Any a inside nav.

    nav > a
        Direct child a elements of nav.

    article.featured p
        Paragraph descendants of featured articles.

    .navigation > .nav-link.active
        Direct child with both classes.

    #main-content article > h1
        h1 elements directly inside article elements inside #main-content.

The more specific the selector, the more carefully it should be designed.
"""
)


def matches_tag_and_class(element: Element, tag: str, class_name: str) -> bool:
    return element.tag == tag and class_name in element.classes


navigation_active_links = select_all(
    ALL_ELEMENTS,
    lambda element: (
        element.parent is nav
        and matches_tag_and_class(element, "a", "active")
    ),
)
show_elements(
    navigation_active_links,
    "Conceptual selector: .navigation > .nav-link.active",
)


# =============================================================================
# 25. CSS SPECIFICITY
# =============================================================================

print("\n" + "=" * 78)
print("22. CSS SPECIFICITY")
print("=" * 78)

print(
    """
Specificity determines which competing declarations are preferred when
selectors match the same element and the declarations are otherwise in the
same cascade context.

A useful conceptual four-part representation is:

    (inline, IDs, classes/attributes/pseudo-classes, elements/pseudo-elements)

Examples:

    p
        (0, 0, 0, 1)

    .text
        (0, 0, 1, 0)

    #article-title
        (0, 1, 0, 0)

    article.featured p
        (0, 0, 1, 2)

    #main-content article.featured p
        (0, 1, 1, 2)

Comparison is lexicographic from left to right.
An ID component outweighs any number of class components only within the
specificity comparison model and relevant cascade context.

Modern CSS also has cascade layers, scoping, nesting, and other mechanisms
that interact with the complete cascade. Specificity alone is not the entire
cascade.
"""
)


def specificity(
    inline: int = 0,
    ids: int = 0,
    classes_attributes_pseudo: int = 0,
    elements_pseudo_elements: int = 0,
) -> tuple[int, int, int, int]:
    """Return a simplified specificity tuple."""
    return (
        inline,
        ids,
        classes_attributes_pseudo,
        elements_pseudo_elements,
    )


specificity_examples = {
    "p": specificity(elements_pseudo_elements=1),
    ".text": specificity(classes_attributes_pseudo=1),
    "#article-title": specificity(ids=1),
    "article.featured p": specificity(
        classes_attributes_pseudo=1,
        elements_pseudo_elements=2,
    ),
    "#main-content article.featured p": specificity(
        ids=1,
        classes_attributes_pseudo=1,
        elements_pseudo_elements=2,
    ),
}

for selector, value in specificity_examples.items():
    print(f"{selector:<35} -> {value}")


# =============================================================================
# 26. :WHERE() AND :IS() SPECIFICITY
# =============================================================================

print("\n" + "=" * 78)
print("23. :is() VS :where()")
print("=" * 78)

print(
    """
:is() and :where() both allow grouped selector logic.

Example:

    :is(article, section) p

    :where(article, section) p

The important specificity distinction is:

    :is()
        Takes the specificity of the most specific argument.

    :where()
        Always has zero specificity for the pseudo-class itself and its
        arguments.

This makes :where() particularly useful for low-specificity defaults that
should be easy to override.
"""
)

print("Conceptual specificity:")
print(":is(.card, #featured) -> influenced by the most specific argument")
print(":where(.card, #featured) -> zero specificity from :where()")


# =============================================================================
# 27. :NOT() AND SPECIFICITY
# =============================================================================

print("\n" + "=" * 78)
print("24. :not()")
print("=" * 78)

print(
    """
:not() excludes matches.

Example:

    button:not(.primary)

This means buttons that do not have the primary class.

Important:
:not() does not automatically mean low specificity. Modern CSS specificity
rules take the specificity of its argument into account.
"""
)

button_not_primary = logical_not(
    lambda element: (
        element.tag == "button"
        and element.has_class("primary")
    )
)

print(
    "Conceptual predicate result for an article:",
    button_not_primary(article),
)


# =============================================================================
# 28. FORM-RELATED PSEUDO-CLASSES
# =============================================================================

print("\n" + "=" * 78)
print("25. FORM PSEUDO-CLASSES")
print("=" * 78)

print(
    """
Common form selectors include:

    :required
    :optional
    :valid
    :invalid
    :in-range
    :out-of-range
    :placeholder-shown
    :read-only
    :read-write
    :checked
    :indeterminate
    :disabled
    :enabled

Example:

    input:invalid {
        border-color: red;
    }

These selectors are especially useful for user feedback and validation
states.
"""
)

email_input = Element(
    "input",
    attributes={
        "type": "email",
        "required": "required",
        "value": "not-an-email",
    },
)

print("Form element:", email_input.description())
print("Required:", email_input.has_attribute("required"))
print(
    "Invalid conceptually:",
    "@" not in email_input.get_attribute("value", ""),
)


# =============================================================================
# 29. LINK PSEUDO-CLASSES
# =============================================================================

print("\n" + "=" * 78)
print("26. LINK PSEUDO-CLASSES")
print("=" * 78)

print(
    """
Common link-related states include:

    :link
        Unvisited links.

    :visited
        Visited links.

    :hover
        Pointer interaction.

    :focus
        Keyboard or programmatic focus.

    :active
        Activation state.

A conventional interactive rule may use:

    a:hover
    a:focus-visible

Do not rely only on hover because keyboard and touch users may not have
hover interaction.
"""
)


# =============================================================================
# 30. ACCESSIBILITY AND :FOCUS-VISIBLE
# =============================================================================

print("\n" + "=" * 78)
print("27. :focus-visible AND ACCESSIBILITY")
print("=" * 78)

print(
    """
A strong keyboard-accessible interface should provide a visible focus
indicator.

Example:

    button:focus-visible {
        outline: 3px solid currentColor;
        outline-offset: 2px;
    }

Avoid removing outlines globally with:

    *:focus {
        outline: none;
    }

unless an equally effective visible focus treatment replaces it.

Selectors therefore affect accessibility directly, not merely visual design.
"""
)


# =============================================================================
# 31. NEGATION AND FILTERING
# =============================================================================

print("\n" + "=" * 78)
print("28. SELECTIVE STYLING WITH :NOT()")
print("=" * 78)

print(
    """
A useful pattern is:

    .nav-link:not(.active)

This means every .nav-link except those also matching .active.

The concept can be modeled as:
"""
)


def nav_link_not_active(element: Element) -> bool:
    return (
        element.has_class("nav-link")
        and not element.has_class("active")
    )


show_elements(
    select_all(ALL_ELEMENTS, nav_link_not_active),
    "Conceptual selector: .nav-link:not(.active)",
)


# =============================================================================
# 32. UNIVERSAL SELECTOR WITH OTHER SELECTORS
# =============================================================================

print("\n" + "=" * 78)
print("29. UNIVERSAL SELECTOR IN COMPOUND CONTEXTS")
print("=" * 78)

print(
    """
The universal selector can appear in combinations.

Examples:

    .card *
        Any descendant of .card.

    div > *
        Every direct child of a div.

    [data-theme] *
        Any descendant of an element carrying data-theme.

A universal selector is not inherently bad. Its usefulness depends on
context and browser workload.
"""
)


# =============================================================================
# 33. EMPTY AND ABSENT ATTRIBUTES
# =============================================================================

print("\n" + "=" * 78)
print("30. ATTRIBUTE EDGE CASES")
print("=" * 78)

print(
    """
These selectors have different meanings:

    [disabled]
        Attribute exists.

    [disabled="true"]
        Attribute exists and its value equals "true".

    [disabled=""]
        Attribute exists with an empty value.

Presence and value are not interchangeable.
"""
)

disabled_button = Element(
    "button",
    attributes={"disabled": "disabled"},
)

empty_attribute = Element(
    "div",
    attributes={"data-state": ""},
)

print("disabled_button [disabled]:", disabled_button.has_attribute("disabled"))
print(
    '[data-state=""]:',
    empty_attribute.get_attribute("data-state") == "",
)


# =============================================================================
# 34. WHITESPACE MATTERS
# =============================================================================

print("\n" + "=" * 78)
print("31. WHITESPACE: A CRITICAL DISTINCTION")
print("=" * 78)

print(
    """
Compare:

    .card.title
        One element having both classes.

    .card .title
        A .title descendant inside a .card.

Compare:

    nav > a
        Direct children.

    nav a
        Any descendant.

Compare:

    h1 + p
        Immediately following sibling.

    h1 ~ p
        Any later sibling.

Whitespace changes selector meaning.
"""
)


# =============================================================================
# 35. SELECTOR PARSING: SIMPLE EDUCATIONAL TOKENIZER
# =============================================================================

print("\n" + "=" * 78)
print("32. SIMPLE SELECTOR TOKENIZATION")
print("=" * 78)

print(
    """
A browser's CSS parser is much more sophisticated than the small tokenizer
below. This implementation is intentionally educational.

It identifies common selector components without attempting to implement the
entire CSS grammar.
"""
)


SELECTOR_TOKEN_PATTERN = re.compile(
    r"""
    (?P<id>\#[A-Za-z_][\w-]*)
    |(?P<class>\.[A-Za-z_][\w-]*)
    |(?P<attribute>\[[^\]]+\])
    |(?P<pseudo>:[A-Za-z-]+(?:\([^)]*\))?)
    |(?P<tag>[A-Za-z][\w-]*|\*)
    |(?P<combinator>[>+~])
    """,
    re.VERBOSE,
)


def tokenize_selector(selector: str) -> list[tuple[str, str]]:
    """
    Tokenize common selector components.

    This is deliberately not a complete CSS parser.
    """
    tokens: list[tuple[str, str]] = []

    for match in SELECTOR_TOKEN_PATTERN.finditer(selector):
        kind = match.lastgroup
        value = match.group()

        if kind is not None:
            tokens.append((kind, value))

    return tokens


sample_selectors = [
    "p",
    ".card",
    "#main",
    "article.featured p",
    "nav > a.active",
    "[data-state='open']",
    "li:nth-child(2)",
    "button:not(.primary)",
    "article:has(h1)",
]

for selector in sample_selectors:
    print(f"{selector:<35} -> {tokenize_selector(selector)}")


# =============================================================================
# 36. SIMPLE SELECTOR VALIDATION
# =============================================================================

print("\n" + "=" * 78)
print("33. BASIC SELECTOR VALIDATION")
print("=" * 78)

print(
    """
CSS identifiers have syntax rules.

Typical class and ID names should be valid CSS identifiers. HTML allows some
attribute and ID values that require escaping when used in CSS selectors.

For example, an ID containing unusual characters may require CSS escaping.

The validator below intentionally covers common identifiers rather than the
full CSS escape grammar.
"""
)


CSS_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*$")


def valid_css_identifier(value: str) -> bool:
    """Check a common subset of valid CSS identifiers."""
    return bool(CSS_IDENTIFIER.fullmatch(value))


identifier_examples = [
    "card",
    "main-content",
    "_private",
    "2column",
    "button!",
    "user_name",
]

for value in identifier_examples:
    print(f"{value!r:<20} valid common identifier: {valid_css_identifier(value)}")


# =============================================================================
# 37. CSS ESCAPING CONCEPT
# =============================================================================

print("\n" + "=" * 78)
print("34. CSS ESCAPING")
print("=" * 78)

print(
    """
CSS identifiers can contain characters that need escaping.

For example, an HTML element may have:

    id="item:123"

A selector may need escaping when targeting it:

    #item\\:123

The exact escaping rules are part of CSS syntax. JavaScript's
document.querySelector() and CSS stylesheets use CSS selector syntax, so
escaping matters when selector strings are generated dynamically.
"""
)


# =============================================================================
# 38. SELECTOR INJECTION AND SECURITY
# =============================================================================

print("\n" + "=" * 78)
print("35. SECURITY: DYNAMIC SELECTORS")
print("=" * 78)

print(
    """
CSS selectors themselves are not normally a direct code-execution mechanism,
but dynamically constructed selector strings can create correctness,
injection, or unexpected DOM-selection problems.

Unsafe conceptual pattern:

    selector = "#" + user_supplied_id

If the value contains selector syntax, it may change what is selected.

In browser JavaScript, a safer approach is often:

    document.querySelector("#" + CSS.escape(userSuppliedId))

The Python example below demonstrates the principle rather than reproducing
the complete browser CSS.escape algorithm.
"""
)


def conceptual_css_escape(identifier: str) -> str:
    """
    Educational approximation of escaping characters significant to CSS.

    This is not a replacement for the browser's CSS.escape() implementation.
    """
    result = []

    for character in identifier:
        if character.isalnum() or character in "_-":
            result.append(character)
        else:
            result.append("\\" + character)

    return "".join(result)


unsafe_id = "item:123"
print("Original ID:", unsafe_id)
print("Conceptually escaped:", conceptual_css_escape(unsafe_id))


# =============================================================================
# 39. SELECTOR PERFORMANCE
# =============================================================================

print("\n" + "=" * 78)
print("36. PERFORMANCE CONSIDERATIONS")
print("=" * 78)

print(
    """
Browsers optimize selector matching heavily, so simple rules are not
automatically faster in every practical case.

Still, selector design affects maintainability and potentially matching work.

Generally useful principles:

    Prefer clear, stable selectors.

    Avoid unnecessarily deep descendant chains.

    Avoid selectors that encode too much DOM structure.

    Prefer reusable classes for component styling.

    Avoid excessive ID specificity when it is not needed.

    Use attribute selectors when the attribute has semantic value.

    Use :has() thoughtfully in large or frequently changing structures.

Example of brittle structural CSS:

    body main section article div ul li a span

A small HTML restructuring could break it.

A component-oriented alternative might be:

    .product-card__title

The second selector expresses intent rather than depending on many ancestor
elements.
"""
)


# =============================================================================
# 40. SPECIFICITY COMPARISON FUNCTION
# =============================================================================

print("\n" + "=" * 78)
print("37. SPECIFICITY COMPARISON")
print("=" * 78)


def compare_specificity(
    first: tuple[int, int, int, int],
    second: tuple[int, int, int, int],
) -> str:
    """Compare two simplified specificity tuples."""
    if first > second:
        return "first selector has greater specificity"
    if second > first:
        return "second selector has greater specificity"
    return "selectors have equal specificity"


pairs = [
    (
        "p",
        specificity(elements_pseudo_elements=1),
        ".text",
        specificity(classes_attributes_pseudo=1),
    ),
    (
        ".card",
        specificity(classes_attributes_pseudo=1),
        "#featured",
        specificity(ids=1),
    ),
    (
        "article.featured p",
        specificity(
            classes_attributes_pseudo=1,
            elements_pseudo_elements=2,
        ),
        ".featured p",
        specificity(
            classes_attributes_pseudo=1,
            elements_pseudo_elements=1,
        ),
    ),
]

for first_name, first_value, second_name, second_value in pairs:
    print(
        f"{first_name} {first_value} vs "
        f"{second_name} {second_value}: "
        f"{compare_specificity(first_value, second_value)}"
    )


# =============================================================================
# 41. CASCADE CONCEPT
# =============================================================================

print("\n" + "=" * 78)
print("38. SELECTORS AND THE CASCADE")
print("=" * 78)

print(
    """
Selector matching is only one part of CSS.

When several declarations can apply, the browser evaluates the cascade,
which includes concepts such as:

    origin
    importance
    cascade layers
    specificity
    scoping proximity
    source order

Therefore:

    "The more specific selector always wins"

is an incomplete rule.

Specificity matters after earlier cascade decisions determine that the
competing declarations should be compared on specificity.

!important also changes the cascade and should not be used merely as a
routine way to defeat poor selector architecture.
"""
)


# =============================================================================
# 42. SOURCE ORDER
# =============================================================================

print("\n" + "=" * 78)
print("39. SOURCE ORDER")
print("=" * 78)

print(
    """
When competing declarations have equal relevance and specificity within
the applicable cascade context, later declarations can win.

Example:

    .message {
        color: black;
    }

    .message {
        color: blue;
    }

The second declaration wins for the same element and property under the same
cascade conditions.
"""
)


# =============================================================================
# 43. PSEUDO-CLASS VS PSEUDO-ELEMENT
# =============================================================================

print("\n" + "=" * 78)
print("40. PSEUDO-CLASS VS PSEUDO-ELEMENT")
print("=" * 78)

print(
    """
Pseudo-class:

    :hover
    :focus
    :first-child

Pseudo-element:

    ::before
    ::after
    ::first-letter
    ::first-line
    ::selection

A pseudo-class describes a state or condition of an existing element.

A pseudo-element represents a conceptual subpart or generated content of
an element.

Modern syntax generally uses double colons for pseudo-elements.
"""
)


# =============================================================================
# 44. COMBINATOR TABLE
# =============================================================================

print("\n" + "=" * 78)
print("41. COMBINATOR REFERENCE")
print("=" * 78)

combinator_reference = [
    (" ", "Descendant", "article p", "p anywhere inside article"),
    (">", "Child", "article > p", "p directly inside article"),
    ("+", "Adjacent sibling", "h1 + p", "p immediately after h1"),
    ("~", "General sibling", "h1 ~ p", "p after h1 under same parent"),
]

print(f"{'Symbol':<10}{'Relationship':<22}{'Example':<22}Meaning")
print("-" * 78)

for symbol, relationship, example, meaning in combinator_reference:
    print(
        f"{symbol:<10}{relationship:<22}{example:<22}{meaning}"
    )


# =============================================================================
# 45. SELECTOR REFERENCE TABLE
# =============================================================================

print("\n" + "=" * 78)
print("42. SELECTOR REFERENCE")
print("=" * 78)

selector_reference = [
    ("*", "Universal", "All elements"),
    ("p", "Element", "All p elements"),
    (".card", "Class", "Elements with class card"),
    ("#main", "ID", "Element with ID main"),
    ("[disabled]", "Attribute presence", "Elements with disabled attribute"),
    ('[type="email"]', "Attribute equality", "Exact attribute value"),
    ('[href^="https"]', "Attribute prefix", "Value starts with https"),
    ('[href$=".pdf"]', "Attribute suffix", "Value ends with .pdf"),
    ('[data-id*="user"]', "Attribute substring", "Value contains user"),
    (":first-child", "Pseudo-class", "First child"),
    (":last-child", "Pseudo-class", "Last child"),
    (":nth-child(2)", "Pseudo-class", "Second child"),
    (":hover", "Pseudo-class", "Pointer hover state"),
    (":focus-visible", "Pseudo-class", "Visible focus state"),
    (":not(.active)", "Logical pseudo-class", "Excludes active elements"),
    (":is(h1, h2)", "Logical pseudo-class", "Matches either selector"),
    (":where(h1, h2)", "Logical pseudo-class", "Grouped selector with zero specificity"),
    (":has(img)", "Relational pseudo-class", "Element containing an img"),
]

print(f"{'Selector':<26}{'Type':<28}Description")
print("-" * 78)

for selector, selector_type, description in selector_reference:
    print(f"{selector:<26}{selector_type:<28}{description}")


# =============================================================================
# 46. REAL-WORLD COMPONENT EXAMPLE
# =============================================================================

print("\n" + "=" * 78)
print("43. REAL-WORLD COMPONENT SELECTORS")
print("=" * 78)

print(
    """
A component-oriented design might use selectors such as:

    .card
    .card__title
    .card__description
    .card--featured
    .card:hover
    .card:focus-within
    .card:has(.badge)

This approach keeps selectors tied to component meaning rather than to
fragile HTML nesting.

The following conceptual CSS demonstrates a coherent component strategy:

    .card {
        padding: 1rem;
    }

    .card__title {
        margin: 0;
    }

    .card--featured {
        border-width: 2px;
    }

    .card:hover {
        transform: translateY(-2px);
    }

    .card:focus-within {
        outline: 2px solid currentColor;
    }
"""
)


# =============================================================================
# 47. SELECTOR DESIGN: GOOD VS BRITTLE
# =============================================================================

print("\n" + "=" * 78)
print("44. GOOD VS BRITTLE SELECTOR DESIGN")
print("=" * 78)

selector_comparisons = [
    (
        "body main section article div p",
        ".article-text",
        "Class expresses purpose and is less dependent on DOM depth.",
    ),
    (
        "#page .content .article .title",
        ".article-title",
        "Avoid unnecessary ID and ancestor specificity.",
    ),
    (
        "ul li a",
        ".nav-link",
        "A semantic component class is easier to reuse.",
    ),
    (
        "div > div > span",
        ".badge",
        "Structural selectors can break after markup changes.",
    ),
]

print(f"{'Brittle or structural':<38}{'Preferred':<24}Reason")
print("-" * 78)

for brittle, preferred, reason in selector_comparisons:
    print(f"{brittle:<38}{preferred:<24}{reason}")


# =============================================================================
# 48. COMMON MISTAKES
# =============================================================================

print("\n" + "=" * 78)
print("45. COMMON CSS SELECTOR MISTAKES")
print("=" * 78)

mistakes = [
    (
        "Writing `.card title` when the intention is an element with two classes.",
        "Use `.card.title` for the same element or `.card .title` for a descendant.",
    ),
    (
        "Confusing `>` with a descendant space.",
        "Use `>` only when direct parent-child structure matters.",
    ),
    (
        "Using `+` when any later sibling should match.",
        "Use `~` for general following siblings.",
    ),
    (
        "Using IDs everywhere for styling.",
        "Prefer reusable classes for component styles.",
    ),
    (
        "Assuming `:nth-child(2)` means the second element of a type.",
        "Use `:nth-of-type(2)` when counting only that element type.",
    ),
    (
        "Removing focus outlines without replacement.",
        "Maintain a visible keyboard focus indicator.",
    ),
    (
        "Assuming specificity alone decides every conflict.",
        "Understand the complete cascade.",
    ),
    (
        "Constructing selector strings from arbitrary user input.",
        "Escape dynamic identifiers and prefer APIs that avoid selector construction.",
    ),
]

for mistake, correction in mistakes:
    print(f"Mistake:    {mistake}")
    print(f"Correction: {correction}")
    print()


# =============================================================================
# 49. EDGE CASE: nth-child VS nth-of-type
# =============================================================================

print("\n" + "=" * 78)
print("46. EDGE CASE: :nth-child VS :nth-of-type")
print("=" * 78)

mixed_parent = Element("div")
mixed_parent.add_child(Element("h2"))
mixed_p = mixed_parent.add_child(Element("p"))
mixed_parent.add_child(Element("div"))
second_mixed_p = mixed_parent.add_child(Element("p"))

mixed_elements = mixed_parent.children

print("Children:")
for index, element in enumerate(mixed_elements, start=1):
    print(f"  child {index}: {element.description()}")

print(
    "\nFor the first p:"
    f" :nth-child(2) = {nth_child(mixed_p, 2)}"
    f", :nth-of-type(1) = {nth_of_type(mixed_p, 1)}"
)

print(
    "For the second p:"
    f" :nth-child(4) = {nth_child(second_mixed_p, 4)}"
    f", :nth-of-type(2) = {nth_of_type(second_mixed_p, 2)}"
)


# =============================================================================
# 50. EDGE CASE: EMPTY ELEMENTS
# =============================================================================

print("\n" + "=" * 78)
print("47. :EMPTY CONCEPT")
print("=" * 78)

print(
    """
:empty matches an element with no children according to CSS's definition
of emptiness.

Whitespace and text-node details matter in real HTML/CSS parsing.

The simplified Element model only stores element children, so this example
demonstrates the structural idea rather than the complete browser rule.
"""
)


def empty_element(element: Element) -> bool:
    """Simplified structural model of :empty."""
    return len(element.children) == 0


show_elements(
    select_all(ALL_ELEMENTS, empty_element),
    "Simplified :empty matches",
)


# =============================================================================
# 51. EDGE CASE: DIRECT CHILD SELECTORS
# =============================================================================

print("\n" + "=" * 78)
print("48. DIRECT CHILD EDGE CASE")
print("=" * 78)

wrapper = Element("div", classes={"wrapper"})
inner = wrapper.add_child(Element("section"))
inner_paragraph = inner.add_child(Element("p"))

print("Structure:")
print("div.wrapper")
print("  section")
print("    p")

print(
    "\nConceptual results:"
    "\n  .wrapper p     -> matches the p"
    "\n  .wrapper > p   -> does not match the p"
)


# =============================================================================
# 52. CSS SELECTORS AND JAVASCRIPT
# =============================================================================

print("\n" + "=" * 78)
print("49. CSS SELECTORS AND JAVASCRIPT")
print("=" * 78)

print(
    """
CSS selector syntax is also used by JavaScript DOM APIs such as:

    document.querySelector()
    document.querySelectorAll()
    element.matches()
    element.closest()

Examples:

    document.querySelector(".card")
    document.querySelectorAll("nav a")
    element.matches(".active")
    element.closest(".card")

This means understanding CSS selectors is useful beyond writing stylesheets.
"""
)


# =============================================================================
# 53. QUERYSELECTOR CONCEPTUAL EXAMPLE
# =============================================================================

print("\n" + "=" * 78)
print("50. QUERYSELECTOR CONCEPT")
print("=" * 78)


def query_by_class(elements: Iterable[Element], class_name: str) -> Optional[Element]:
    """Model querySelector by returning the first class match."""
    for element in elements:
        if class_name in element.classes:
            return element
    return None


first_nav_link = query_by_class(ALL_ELEMENTS, "nav-link")

print(
    "Conceptual querySelector('.nav-link'):",
    first_nav_link.description() if first_nav_link else None,
)


# =============================================================================
# 54. QUERYSELECTORALL CONCEPTUAL EXAMPLE
# =============================================================================

def query_all_by_tag(
    elements: Iterable[Element],
    tag_name: str,
) -> list[Element]:
    """Model querySelectorAll for a simple tag selector."""
    return [
        element
        for element in elements
        if element.tag == tag_name
    ]


print(
    "Conceptual querySelectorAll('p'):",
    [element.description() for element in query_all_by_tag(ALL_ELEMENTS, "p")],
)


# =============================================================================
# 55. MATCHING COMPLEXITY
# =============================================================================

print("\n" + "=" * 78)
print("51. CONCEPTUAL MATCHING COMPLEXITY")
print("=" * 78)

print(
    """
A naive selector engine may inspect many elements and relationships.

For N DOM elements, a simple scan can be O(N).

Relationship selectors may require traversing:

    ancestors
    parents
    siblings
    descendants

Real browsers use sophisticated indexing, matching strategies, caching,
style invalidation, and other optimizations.

When CSS changes dynamically, the browser may need to recalculate styles for
affected elements. Efficient selector architecture can therefore contribute
to responsive rendering, especially in very large or frequently changing
documents.
"""
)

print(f"Current teaching DOM size: {len(ALL_ELEMENTS)} elements")


# =============================================================================
# 56. SELECTOR REUSABILITY
# =============================================================================

print("\n" + "=" * 78)
print("52. REUSABILITY")
print("=" * 78)

print(
    """
Classes are usually the main tool for reusable styling.

Example:

    .button {
        ...
    }

The same class can style:

    <button class="button">
    <a class="button">
    <div class="button">

The exact semantic appropriateness of each element still matters. A class
does not transform one HTML element into another semantic element.
"""
)


# =============================================================================
# 57. SEMANTIC HTML AND SELECTORS
# =============================================================================

print("\n" + "=" * 78)
print("53. SEMANTIC HTML")
print("=" * 78)

print(
    """
Selectors work best when the HTML structure itself communicates meaning.

Examples of semantic elements:

    header
    nav
    main
    article
    section
    footer
    button
    form
    label

An element selector such as `nav` can be meaningful when the style truly
applies to navigation containers.

Avoid selecting generic div elements solely because they happen to appear
at a particular DOM depth.
"""
)


# =============================================================================
# 58. DATA ATTRIBUTES
# =============================================================================

print("\n" + "=" * 78)
print("54. DATA ATTRIBUTES")
print("=" * 78)

print(
    """
Custom data attributes use the `data-*` naming convention.

Example:

    <article data-status="published">

CSS can select them:

    article[data-status="published"] {
        ...
    }

Data attributes can be useful when the state is genuinely represented in
the document and styling depends on that state.

They should not replace semantic classes when a class is the clearer
representation of a reusable visual state.
"""
)

published_article = Element(
    "article",
    attributes={"data-status": "published"},
)

print(
    "Published article matches [data-status='published']:",
    published_article.get_attribute("data-status") == "published",
)


# =============================================================================
# 59. ACCESSIBILITY ATTRIBUTE SELECTORS
# =============================================================================

print("\n" + "=" * 78)
print("55. ACCESSIBILITY-RELATED ATTRIBUTES")
print("=" * 78)

print(
    """
ARIA attributes can sometimes be selected with attribute selectors.

Example:

    [aria-expanded="true"]

This can be useful for visual state synchronization.

The important principle is that CSS styling should not be the only mechanism
for communicating an accessibility state. The underlying semantics and
behavior must also be correct.
"""
)


expanded_menu = Element(
    "button",
    attributes={"aria-expanded": "true"},
)

print(
    "Matches [aria-expanded='true']:",
    expanded_menu.get_attribute("aria-expanded") == "true",
)


# =============================================================================
# 60. SELECTOR ARCHITECTURE
# =============================================================================

print("\n" + "=" * 78)
print("56. SELECTOR ARCHITECTURE")
print("=" * 78)

print(
    """
A maintainable stylesheet often separates responsibilities:

    Element selectors
        Broad semantic defaults.

    Classes
        Reusable component and utility styles.

    IDs
        Usually reserved for unique document relationships or situations
        where high specificity is intentionally required.

    Attributes
        Semantic state and data-driven conditions.

    Combinators
        Relationship-based styling.

    Pseudo-classes
        State and structural conditions.

A selector should communicate why an element receives a style, not merely
how the current HTML happens to be nested.
"""
)


# =============================================================================
# 61. CSS SELECTOR DECISION PROCESS
# =============================================================================

print("\n" + "=" * 78)
print("57. CHOOSING THE RIGHT SELECTOR")
print("=" * 78)

decision_rules = [
    ("All paragraphs", "p"),
    ("Reusable visual component", ".component"),
    ("One unique document target", "#unique-id"),
    ("Element with an attribute", "[disabled]"),
    ("Exact attribute value", '[type="email"]'),
    ("Nested relationship", ".card .title"),
    ("Direct relationship", ".card > .title"),
    ("Immediately following sibling", "h2 + p"),
    ("Later sibling", "h2 ~ p"),
    ("Interaction state", ":hover / :focus-visible"),
    ("Position among children", ":nth-child(...)"),
    ("Position among same type", ":nth-of-type(...)"),
    ("Exclude condition", ":not(...)"),
    ("Either of several patterns", ":is(...)"),
    ("Low-specificity grouping", ":where(...)"),
    ("Condition based on related content", ":has(...)"),
]

for need, selector in decision_rules:
    print(f"{need:<42} -> {selector}")


# =============================================================================
# 62. TESTING SELECTOR INTENT
# =============================================================================

print("\n" + "=" * 78)
print("58. TESTING SELECTOR INTENT")
print("=" * 78)

print(
    """
A useful CSS debugging question is:

    "Which elements does this selector actually match?"

Before changing declarations, verify selector scope.

A selector can be syntactically valid but semantically wrong.

Examples:

    .card p
        May affect paragraphs in nested components.

    .card > p
        Restricts the relationship.

    .card__description
        Expresses a specific component role.

Selector testing is therefore a key debugging technique.
"""
)


# =============================================================================
# 63. SIMPLE ASSERTION-BASED TESTS
# =============================================================================

print("\n" + "=" * 78)
print("59. SELECTOR TESTS")
print("=" * 78)


def assert_matches(
    elements: Iterable[Element],
    predicate: Callable[[Element], bool],
    expected: set[str],
    description: str,
) -> None:
    """Assert that a selector model returns expected descriptions."""
    actual = {
        element.description()
        for element in elements
        if predicate(element)
    }

    if actual != expected:
        raise AssertionError(
            f"{description}\nExpected: {expected}\nActual: {actual}"
        )


assert_matches(
    ALL_ELEMENTS,
    lambda element: element.tag == "h1",
    {"h1#article-title.featured-title.title"},
    "Element selector test failed",
)

assert_matches(
    ALL_ELEMENTS,
    lambda element: element.has_class("highlight"),
    {"p.highlight.text"},
    "Class selector test failed",
)

assert_matches(
    ALL_ELEMENTS,
    lambda element: element.id == "main-content",
    {"main#main-content.content"},
    "ID selector test failed",
)

print("Basic selector tests passed.")


# =============================================================================
# 64. ERROR HANDLING FOR INVALID SELECTOR INPUT
# =============================================================================

print("\n" + "=" * 78)
print("60. VALIDATION AND ERROR HANDLING")
print("=" * 78)


class SelectorSyntaxError(ValueError):
    """Raised when a simplified selector input is invalid."""


def validate_simple_class_selector(selector: str) -> None:
    """
    Validate a simplified class selector such as `.card`.

    This is intentionally much narrower than the complete CSS grammar.
    """
    if not selector.startswith("."):
        raise SelectorSyntaxError("Class selector must start with '.'.")

    name = selector[1:]

    if not name:
        raise SelectorSyntaxError("Class selector cannot have an empty name.")

    if not valid_css_identifier(name):
        raise SelectorSyntaxError(
            f"Invalid common CSS class identifier: {name!r}"
        )


test_selectors = [
    ".card",
    ".main-content",
    "",
    "card",
    ".2column",
]

for selector in test_selectors:
    try:
        validate_simple_class_selector(selector)
        print(f"{selector!r}: valid simplified class selector")
    except SelectorSyntaxError as error:
        print(f"{selector!r}: invalid -> {error}")


# =============================================================================
# 65. SELECTOR GROUPING WITH FUNCTIONS
# =============================================================================

print("\n" + "=" * 78)
print("61. FUNCTIONAL SELECTOR CONSTRUCTION")
print("=" * 78)

print(
    """
A selector can be represented as a reusable function in this teaching model.

For example, we can create:

    is_article
    has_featured_class
    is_featured_article

and combine them.

This resembles how complex selector logic can be reasoned about as smaller
conditions.
"""
)


is_article = lambda element: element.tag == "article"
has_featured = lambda element: element.has_class("featured")

is_featured_article = lambda element: is_article(element) and has_featured(element)

show_elements(
    select_all(ALL_ELEMENTS, is_featured_article),
    "Functional model of article.featured",
)


# =============================================================================
# 66. ATTRIBUTE SELECTOR FACTORY
# =============================================================================

print("\n" + "=" * 78)
print("62. REUSABLE ATTRIBUTE SELECTOR FACTORIES")
print("=" * 78)


def attribute_selector(
    name: str,
    operator: Optional[str] = None,
    expected: Optional[str] = None,
) -> Callable[[Element], bool]:
    """
    Create several common attribute selector behaviors.

    Supported operators:
        None -> presence
        "="  -> exact
        "^=" -> prefix
        "$=" -> suffix
        "*=" -> substring
        "~=" -> whitespace-separated word
        "|=" -> exact or dash-prefixed value
    """
    if operator not in {None, "=", "^=", "$=", "*=", "~=", "|="}:
        raise SelectorSyntaxError(f"Unsupported attribute operator: {operator}")

    if operator is not None and expected is None:
        raise SelectorSyntaxError(
            "An expected value is required for an attribute operator."
        )

    def matches(element: Element) -> bool:
        actual = element.get_attribute(name)

        if operator is None:
            return actual is not None

        if actual is None:
            return False

        if operator == "=":
            return actual == expected

        if operator == "^=":
            return actual.startswith(expected or "")

        if operator == "$=":
            return actual.endswith(expected or "")

        if operator == "*=":
            return (expected or "") in actual

        if operator == "~=":
            return (expected or "") in actual.split()

        if operator == "|=":
            expected_value = expected or ""
            return actual == expected_value or actual.startswith(
                expected_value + "-"
            )

        return False

    return matches


data_type_post = attribute_selector(
    "data-type",
    "=",
    "post",
)

show_elements(
    select_all(ALL_ELEMENTS, data_type_post),
    '[data-type="post"]',
)


# =============================================================================
# 67. COMPLEX REAL-WORLD SELECTOR EXAMPLES
# =============================================================================

print("\n" + "=" * 78)
print("63. COMPLEX REAL-WORLD SELECTOR EXAMPLES")
print("=" * 78)

complex_examples = [
    (
        ".product-card",
        "Select reusable product card components.",
    ),
    (
        ".product-card > .product-card__title",
        "Select a direct title child.",
    ),
    (
        ".product-card[data-stock='low']",
        "Select low-stock cards using semantic state.",
    ),
    (
        ".product-card:not(.disabled)",
        "Select enabled cards that do not carry disabled.",
    ),
    (
        ".product-card:has(.discount)",
        "Select cards containing a discount indicator.",
    ),
    (
        "form input:invalid",
        "Select invalid inputs inside forms.",
    ),
    (
        "nav > a[aria-current='page']",
        "Select the active navigation link using ARIA state.",
    ),
    (
        ".table-row:nth-child(even)",
        "Select alternating rows.",
    ),
]

for selector, purpose in complex_examples:
    print(f"{selector:<48} {purpose}")


# =============================================================================
# 68. SELECTOR LIMITATIONS
# =============================================================================

print("\n" + "=" * 78)
print("64. LIMITATIONS OF CSS SELECTORS")
print("=" * 78)

print(
    """
CSS selectors are powerful but have boundaries.

They are not a general programming language.

Selectors do not directly perform arbitrary calculations, database queries,
network requests, or application business logic.

CSS selection is also not the same thing as DOM traversal in a general
programming environment.

For example, if an application needs to calculate whether an order is
profitable, that belongs in application logic. CSS may style the result once
the relevant state is represented in the DOM.
"""
)


# =============================================================================
# 69. MAINTAINABILITY
# =============================================================================

print("\n" + "=" * 78)
print("65. MAINTAINABILITY")
print("=" * 78)

print(
    """
Good selector design generally has these properties:

    Predictable
    Reusable
    Readable
    Low unnecessary specificity
    Resistant to markup changes
    Compatible with component boundaries
    Accessible
    Explicit about state

A maintainable selector is not necessarily the shortest selector. It is the
selector whose meaning remains clear as the application grows.
"""
)


# =============================================================================
# 70. PRODUCTION CONSIDERATIONS
# =============================================================================

print("\n" + "=" * 78)
print("66. PRODUCTION CONSIDERATIONS")
print("=" * 78)

print(
    """
For production CSS:

    Use semantic HTML where appropriate.

    Prefer classes for reusable styling.

    Keep selector specificity controlled.

    Avoid unnecessary nesting depth.

    Use :focus-visible for keyboard-accessible interaction states.

    Use attribute selectors when attributes carry meaningful state.

    Use :is(), :where(), :not(), and :has() when they make the selector
    clearer rather than merely shorter.

    Be careful with generated selectors.

    Test selectors against realistic DOM structures.

    Consider browser compatibility when using newer selector features.

    Keep component boundaries clear.

    Avoid using !important as the normal solution to specificity problems.
"""
)


# =============================================================================
# 71. MINI SELECTOR EXAM
# =============================================================================

print("\n" + "=" * 78)
print("67. MINI KNOWLEDGE CHECK")
print("=" * 78)

questions = [
    (
        "Which selector targets all elements with class `card`?",
        ".card",
    ),
    (
        "Which selector targets the element with ID `main`?",
        "#main",
    ),
    (
        "Which combinator selects direct children?",
        ">",
    ),
    (
        "Which combinator selects an immediately following sibling?",
        "+",
    ),
    (
        "Which combinator selects later siblings?",
        "~",
    ),
    (
        "Which selector selects an attribute that exists?",
        "[disabled]",
    ),
    (
        "Which pseudo-class selects the first child?",
        ":first-child",
    ),
    (
        "Which pseudo-class selects the second child?",
        ":nth-child(2)",
    ),
    (
        "Which pseudo-class counts only elements of the same type?",
        ":nth-of-type(...)",
    ),
    (
        "Which pseudo-class excludes a selector?",
        ":not(...)",
    ),
    (
        "Which pseudo-class groups alternatives with normal specificity rules?",
        ":is(...)",
    ),
    (
        "Which pseudo-class groups selectors with zero specificity?",
        ":where(...)",
    ),
    (
        "Which pseudo-class selects based on related content?",
        ":has(...)",
    ),
]

for question, answer in questions:
    print(f"Q: {question}")
    print(f"A: {answer}")
    print()


# =============================================================================
# 72. FINAL PRACTICAL REFERENCE
# =============================================================================

print("\n" + "=" * 78)
print("68. PRACTICAL CSS SELECTOR CHEAT SHEET")
print("=" * 78)

cheat_sheet = """
Universal:
    *

Element:
    p
    button
    article

Class:
    .card
    .active

ID:
    #main

Compound:
    button.primary
    p.text.highlight

Descendant:
    article p

Child:
    article > p

Adjacent sibling:
    h2 + p

General sibling:
    h2 ~ p

Attribute presence:
    [disabled]

Attribute equality:
    [type="email"]

Attribute prefix:
    [href^="https"]

Attribute suffix:
    [href$=".pdf"]

Attribute substring:
    [data-id*="user"]

Attribute word:
    [data-role~="admin"]

Attribute language:
    [lang|="en"]

First child:
    :first-child

Last child:
    :last-child

Only child:
    :only-child

Nth child:
    :nth-child(2)
    :nth-child(odd)
    :nth-child(2n)

Nth of type:
    :nth-of-type(2)

State:
    :hover
    :focus
    :focus-visible
    :active
    :checked
    :disabled
    :valid
    :invalid

Logical:
    :not(...)
    :is(...)
    :where(...)
    :has(...)

Selector list:
    h1, h2, h3
"""

print(cheat_sheet)


# =============================================================================
# 73. FINAL VALIDATION
# =============================================================================

print("\n" + "=" * 78)
print("69. FINAL VALIDATION")
print("=" * 78)

assert root.tag == "html"
assert body.parent is root
assert main.parent is body
assert article.parent is main
assert heading.parent is article
assert paragraph_one.parent is content_section
assert paragraph_two.parent is content_section

assert "featured" in article.classes
assert article.id is None
assert heading.id == "article-title"
assert home_link.get_attribute("href") == "/"
assert paragraph_two.get_attribute("data-status") == "important"

assert first_child(home_link)
assert last_child(contact_link)
assert nth_child(products_link, 2)
assert nth_of_type(paragraph_two, 2)

assert valid_css_identifier("main-content")
assert not valid_css_identifier("2column")

print("DOM relationships: PASS")
print("Class matching: PASS")
print("ID matching: PASS")
print("Attribute matching: PASS")
print("Child/descendant concepts: PASS")
print("Sibling concepts: PASS")
print("Structural pseudo-class concepts: PASS")
print("Selector tokenization: PASS")
print("Specificity modeling: PASS")
print("Validation checks: PASS")


# =============================================================================
# 74. IMPORTANT DISTINCTIONS
# =============================================================================

print("\n" + "=" * 78)
print("70. IMPORTANT DISTINCTIONS TO REMEMBER")
print("=" * 78)

distinctions = [
    ("p", ".p", "Element selector vs class selector"),
    (".card.title", ".card .title", "Same element vs descendant"),
    ("article p", "article > p", "Any descendant vs direct child"),
    ("h1 + p", "h1 ~ p", "Immediate sibling vs later siblings"),
    (":nth-child(2)", ":nth-of-type(2)", "All children vs same element type"),
    (":is(...)", ":where(...)", "Grouped specificity vs zero specificity"),
    (":hover", ".hover", "Browser state vs ordinary class"),
    ("[disabled]", '[disabled="true"]', "Attribute presence vs exact value"),
    ("#main", ".main", "Unique ID vs reusable class"),
    (":not(...)", ":has(...)", "Exclusion vs relational condition"),
]

for first, second, meaning in distinctions:
    print(f"{first:<28} | {second:<28} | {meaning}")


# =============================================================================
# 75. STUDY CHECKLIST
# =============================================================================

print("\n" + "=" * 78)
print("71. STUDY CHECKLIST")
print("=" * 78)

checklist = [
    "Understand what a selector does.",
    "Recognize universal selectors.",
    "Write element selectors.",
    "Write class selectors.",
    "Write ID selectors.",
    "Combine simple selectors.",
    "Distinguish descendant and child selectors.",
    "Distinguish adjacent and general sibling selectors.",
    "Use attribute presence and value selectors.",
    "Understand attribute prefix, suffix, substring, word, and language matching.",
    "Understand structural pseudo-classes.",
    "Understand state pseudo-classes.",
    "Understand :nth-child() and :nth-of-type().",
    "Understand :not(), :is(), :where(), and :has().",
    "Understand selector lists.",
    "Understand specificity.",
    "Understand the broader cascade.",
    "Avoid unnecessary selector complexity.",
    "Design selectors for maintainability.",
    "Preserve keyboard focus visibility.",
    "Treat dynamically generated selectors carefully.",
    "Test selector scope when debugging.",
]

for number, item in enumerate(checklist, start=1):
    print(f"{number:02d}. {item}")


# =============================================================================
# 76. SCRIPT END
# =============================================================================

print("\n" + "=" * 78)
print("CSS SELECTOR STUDY SCRIPT COMPLETED")
print("=" * 78)

print(
    """
The executable demonstrations covered selector syntax, relationships,
attributes, pseudo-classes, logical selection, specificity, accessibility,
security considerations, debugging, performance concepts, maintainability,
and production-oriented selector design.
"""
)
