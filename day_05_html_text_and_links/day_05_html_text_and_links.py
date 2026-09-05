"""
HTML TEXT AND LINKS
===================

A comprehensive, executable study guide covering:

1. HTML text content and semantic text elements
2. Text formatting and inline elements
3. Block-level versus inline structure
4. Headings, paragraphs, quotations, code, lists, and emphasis
5. Hyperlinks and the <a> element
6. Absolute versus relative URLs
7. URL paths, query strings, fragments, and URL encoding
8. Anchors and fragment navigation
9. Internal page navigation
10. Cross-page navigation
11. Mail links and telephone links
12. Download links
13. Targeting browsing contexts
14. rel attributes and security implications
15. Accessible link text
16. Links around images and other content
17. HTML escaping and safe text insertion
18. URL validation and normalization
19. Common mistakes and edge cases
20. Practical document generation
21. Testing and validation
22. Production-oriented considerations

The script intentionally uses only Python's standard library.
It generates HTML examples as strings and demonstrates the concepts
programmatically rather than requiring external files or packages.
"""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import Iterable, Optional
from urllib.parse import (
    parse_qs,
    quote,
    urlencode,
    urljoin,
    urlparse,
    urlunparse,
)
import re
import tempfile
import unittest


# ============================================================================
# 1. FUNDAMENTAL HTML CONCEPTS
# ============================================================================

def print_section(title: str) -> None:
    """Print a visually clear section heading."""
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


print_section("1. HTML TEXT AND DOCUMENT STRUCTURE")

# HTML represents content using elements.
#
# Example:
#
# <p>Hello world</p>
#
# <p> is the opening tag.
# Hello world is the text content.
# </p> is the closing tag.
#
# Some elements are void elements and do not have closing tags.
# Examples include <br>, <hr>, <img>, <meta>, and <input>.

basic_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Text Example</title>
</head>
<body>
    <h1>Main Heading</h1>
    <p>This is a paragraph containing ordinary text.</p>
</body>
</html>
""".strip()

print(basic_html)


# ============================================================================
# 2. TEXT ELEMENTS
# ============================================================================

print_section("2. SEMANTIC TEXT ELEMENTS")

semantic_text_example = """
<h1>HTML Text</h1>
<h2>Semantic Structure</h2>

<p>
    HTML describes the <strong>meaning and structure</strong> of content,
    not merely its visual appearance.
</p>

<p>
    The <em>emphasis</em> element communicates stress emphasis.
</p>

<p>
    A <mark>highlighted phrase</mark> can be represented with mark.
</p>

<p>
    A short quotation can use <q>quotation markup</q>.
</p>

<p>
    Chemical formula: H<sub>2</sub>O
</p>

<p>
    Mathematical expression: x<sup>2</sup>
</p>

<p>
    <small>Small-print information can be represented semantically.</small>
</p>
""".strip()

print(semantic_text_example)

# Important distinctions:
#
# <strong> means strong importance.
# <b> means stylistically offset text without implying strong importance.
#
# <em> means stress emphasis.
# <i> represents text in an alternate voice or mood, terminology, etc.
#
# <mark> identifies text relevant in the current context.
# <small> represents side comments or small print.
#
# <del> represents deleted content.
# <ins> represents inserted content.
#
# Semantic HTML is preferable when the meaning of the text matters.


# ============================================================================
# 3. HEADINGS
# ============================================================================

print_section("3. HEADINGS")

headings = """
<h1>Page Title</h1>
<h2>Major Section</h2>
<h3>Subsection</h3>
<h4>Nested Section</h4>
<h5>Detailed Section</h5>
<h6>Lowest Heading Level</h6>
""".strip()

print(headings)

# There are six heading levels.
#
# Heading levels describe document hierarchy. They should not be selected
# merely because a particular level looks visually attractive.
#
# CSS should normally control visual appearance.
#
# A document should generally have a coherent hierarchy:
#
# h1
#   h2
#     h3
#     h3
#   h2
#
# Skipping levels is not always invalid, but arbitrary heading jumps can
# make document structure harder to understand.


# ============================================================================
# 4. PARAGRAPHS AND LINE BREAKS
# ============================================================================

print_section("4. PARAGRAPHS AND LINE BREAKS")

paragraph_example = """
<p>First paragraph.</p>
<p>Second paragraph.</p>

<p>
    This line ends here.<br>
    This line begins after a forced line break.
</p>

<hr>

<p>The horizontal rule represents a thematic break.</p>
""".strip()

print(paragraph_example)

# <p> represents a paragraph.
# <br> represents a line break.
# <hr> represents a thematic break.
#
# Repeated <br> elements should not be used to create page layout.
# CSS handles spacing and layout.


# ============================================================================
# 5. QUOTATIONS
# ============================================================================

print_section("5. QUOTATIONS")

quotation_example = """
<blockquote cite="https://example.com/source">
    <p>This is a longer quotation represented as a block quotation.</p>
</blockquote>

<p>
    The specification uses <q>short inline quotations</q>.
</p>

<p>
    <cite>Example Publication</cite>
</p>
""".strip()

print(quotation_example)

# <blockquote> is intended for extended quotations.
# <q> is intended for short inline quotations.
# <cite> identifies the title of a creative work or cited source.
#
# A cite attribute on blockquote can contain the source URL, but browsers
# do not normally display it as visible citation text automatically.


# ============================================================================
# 6. CODE AND PREFORMATTED TEXT
# ============================================================================

print_section("6. CODE AND PREFORMATTED TEXT")

code_example = """
<p>Use <code>print()</code> to display text in Python.</p>

<pre><code>
def greet(name):
    return f"Hello, {name}"
</code></pre>

<p>
    Press <kbd>Ctrl</kbd> + <kbd>S</kbd> to save a file.
</p>

<p>
    The program returned <samp>Hello, Atul</samp>.
</p>

<p>
    The variable <var>x</var> contains a value.
</p>
""".strip()

print(code_example)

# <code> represents a fragment of computer code.
# <pre> preserves whitespace and line breaks.
# <kbd> represents user input, commonly keyboard input.
# <samp> represents sample output.
# <var> represents a mathematical or programming variable.


# ============================================================================
# 7. LISTS
# ============================================================================

print_section("7. TEXT LISTS")

list_example = """
<h2>Unordered List</h2>
<ul>
    <li>Python</li>
    <li>SQL</li>
    <li>HTML</li>
</ul>

<h2>Ordered List</h2>
<ol>
    <li>Open the document.</li>
    <li>Edit the content.</li>
    <li>Save the document.</li>
</ol>

<h2>Description List</h2>
<dl>
    <dt>HTML</dt>
    <dd>Markup language for structuring web documents.</dd>

    <dt>URL</dt>
    <dd>Uniform Resource Locator.</dd>
</dl>
""".strip()

print(list_example)

# <ul> represents an unordered list.
# <ol> represents an ordered list.
# <li> represents a list item.
# <dl>, <dt>, and <dd> represent description-list relationships.


# ============================================================================
# 8. INLINE VERSUS BLOCK-LEVEL THINKING
# ============================================================================

print_section("8. INLINE AND STRUCTURAL CONTENT")

inline_example = """
<p>
    This paragraph contains
    <strong>important</strong>,
    <em>emphasized</em>,
    and <a href="/contact">linked</a>
    inline content.
</p>
""".strip()

print(inline_example)

# HTML elements have different content models and semantics.
#
# It is useful to think of:
#
# Structural/block-oriented elements:
#   p, h1-h6, section, article, nav, ul, ol, div
#
# Inline phrasing elements:
#   a, em, strong, span, code, q, mark
#
# Modern HTML is better understood through content categories and permitted
# content models rather than relying only on the old "block vs inline"
# terminology.


# ============================================================================
# 9. THE ANCHOR ELEMENT
# ============================================================================

print_section("9. HYPERLINKS AND THE <a> ELEMENT")

anchor_examples = """
<a href="https://example.com">Visit Example</a>

<a href="/about">About this website</a>

<a href="about.html">About</a>

<a href="#contact">Jump to Contact</a>
""".strip()

print(anchor_examples)

# The fundamental syntax is:
#
# <a href="DESTINATION">LINK TEXT</a>
#
# href identifies the destination.
#
# The visible text between the opening and closing tags is the link's
# accessible name in the common case.


# ============================================================================
# 10. ABSOLUTE URLS
# ============================================================================

print_section("10. ABSOLUTE URLS")

absolute_urls = [
    "https://example.com",
    "https://example.com/products",
    "https://example.com/products?id=42",
    "https://example.com/products#pricing",
    "mailto:user@example.com",
    "tel:+919876543210",
]

for url in absolute_urls:
    parsed = urlparse(url)
    print(f"URL:      {url}")
    print(f"scheme:   {parsed.scheme}")
    print(f"netloc:   {parsed.netloc}")
    print(f"path:     {parsed.path}")
    print(f"query:    {parsed.query}")
    print(f"fragment: {parsed.fragment}")
    print("-" * 50)

# An absolute HTTP(S) URL normally includes a scheme and host:
#
# https://example.com/path/page.html
#
# Absolute URLs are useful when linking to a specific external website or
# when a destination must not depend on the current document's location.


# ============================================================================
# 11. RELATIVE URLS
# ============================================================================

print_section("11. RELATIVE URLS")

relative_urls = [
    "about.html",
    "./about.html",
    "../about.html",
    "/about.html",
    "images/logo.png",
    "#contact",
    "?page=2",
]

base_url = "https://example.com/products/catalog/index.html"

for relative_url in relative_urls:
    resolved = urljoin(base_url, relative_url)
    print(f"{relative_url:25} -> {resolved}")

# Important distinction:
#
# "about.html"
#   Relative to the current document's directory.
#
# "../about.html"
#   Moves one directory upward.
#
# "/about.html"
#   Root-relative URL. It begins at the site's origin root.
#
# "#contact"
#   Fragment-only URL. It targets an element in the current document.
#
# "?page=2"
#   Query-only reference. It changes the query while retaining the base path.


# ============================================================================
# 12. ABSOLUTE VS RELATIVE URL COMPARISON
# ============================================================================

print_section("12. ABSOLUTE VS RELATIVE URL COMPARISON")

comparison_base = "https://example.com/docs/tutorial/page.html"

url_comparison = {
    "absolute": "https://example.org/about.html",
    "root-relative": "/about.html",
    "directory-relative": "about.html",
    "parent-relative": "../about.html",
    "fragment": "#examples",
    "query": "?page=2",
}

for category, value in url_comparison.items():
    print(
        f"{category:20} {value:35} -> "
        f"{urljoin(comparison_base, value)}"
    )

# Practical trade-off:
#
# Absolute:
#   + Explicit destination
#   + Suitable for external domains
#   - Can become outdated if the domain changes
#
# Root-relative:
#   + Independent of current directory
#   + Useful within one website
#   - Depends on the site's root structure
#
# Directory-relative:
#   + Convenient for closely related pages
#   + Portable within a directory hierarchy
#   - Moving the source file can change its meaning
#
# Fragment:
#   + Excellent for same-page navigation
#   - Requires a matching target


# ============================================================================
# 13. URL COMPONENTS
# ============================================================================

print_section("13. URL COMPONENTS")

complex_url = (
    "https://example.com:443/products/view"
    "?category=books&sort=price#reviews"
)

parsed_url = urlparse(complex_url)

print(f"Scheme:   {parsed_url.scheme}")
print(f"Network:  {parsed_url.netloc}")
print(f"Path:     {parsed_url.path}")
print(f"Query:    {parsed_url.query}")
print(f"Fragment: {parsed_url.fragment}")

query_parameters = parse_qs(parsed_url.query)

print("Parsed query parameters:")
for key, values in query_parameters.items():
    print(f"  {key} = {values}")

# A URL may contain:
#
# scheme://authority/path?query#fragment
#
# Example:
#
# https://example.com/products?id=10#details
#
# scheme   = https
# authority = example.com
# path      = /products
# query    = id=10
# fragment = details
#
# The fragment is normally interpreted by the browser after the resource
# has been retrieved and is not normally sent to the HTTP server as part
# of the HTTP request.


# ============================================================================
# 14. FRAGMENTS AND ANCHORS
# ============================================================================

print_section("14. FRAGMENTS AND PAGE ANCHORS")

fragment_navigation = """
<nav>
    <a href="#introduction">Introduction</a>
    <a href="#syntax">Syntax</a>
    <a href="#examples">Examples</a>
    <a href="#contact">Contact</a>
</nav>

<main>
    <section id="introduction">
        <h2>Introduction</h2>
        <p>Introduction content.</p>
    </section>

    <section id="syntax">
        <h2>Syntax</h2>
        <p>Syntax content.</p>
    </section>

    <section id="examples">
        <h2>Examples</h2>
        <p>Examples content.</p>
    </section>

    <section id="contact">
        <h2>Contact</h2>
        <p>Contact content.</p>
    </section>
</main>
""".strip()

print(fragment_navigation)

# Modern HTML does not require:
#
# <a name="contact"></a>
#
# for ordinary fragment targets.
#
# An element with:
#
# id="contact"
#
# can be targeted with:
#
# href="#contact"
#
# IDs should be unique within the document.


# ============================================================================
# 15. CROSS-PAGE ANCHOR NAVIGATION
# ============================================================================

print_section("15. CROSS-PAGE FRAGMENT NAVIGATION")

cross_page_navigation = """
<a href="documentation.html#installation">
    Installation instructions
</a>

<a href="/docs/api.html#authentication">
    Authentication section
</a>
""".strip()

print(cross_page_navigation)

# The browser loads the destination document and then attempts to position
# the viewport at the element whose ID matches the fragment.


# ============================================================================
# 16. NAVIGATION MENUS
# ============================================================================

print_section("16. NAVIGATION")

navigation_example = """
<nav aria-label="Primary navigation">
    <ul>
        <li><a href="/">Home</a></li>
        <li><a href="/products">Products</a></li>
        <li><a href="/services">Services</a></li>
        <li><a href="/about">About</a></li>
        <li><a href="/contact">Contact</a></li>
    </ul>
</nav>
""".strip()

print(navigation_example)

# <nav> semantically identifies a navigation section.
#
# A navigation list is often preferable to a collection of unrelated links
# because the list communicates grouping and structure.
#
# aria-label can distinguish multiple navigation landmarks when necessary.


# ============================================================================
# 17. MAILTO LINKS
# ============================================================================

print_section("17. MAIL LINKS")

mailto_basic = "mailto:contact@example.com"
mailto_subject = "mailto:contact@example.com?subject=Project%20Inquiry"
mailto_multiple = (
    "mailto:contact@example.com"
    "?cc=manager@example.com"
    "&subject=Project%20Inquiry"
)

print(mailto_basic)
print(mailto_subject)
print(mailto_multiple)

mailto_html = """
<a href="mailto:contact@example.com">Email us</a>

<a href="mailto:contact@example.com?subject=Project%20Inquiry">
    Email about the project
</a>
""".strip()

print(mailto_html)

# mailto links request that the browser hand the address to an available
# mail-handling application.
#
# They do not guarantee that a particular mail client is installed.
#
# User-controlled email fields should be encoded correctly.
#
# Do not construct mailto URLs by concatenating arbitrary unescaped input.


# ============================================================================
# 18. TELEPHONE LINKS
# ============================================================================

print_section("18. TELEPHONE LINKS")

telephone_examples = [
    "tel:+919876543210",
    "tel:+12125550123",
]

for telephone_url in telephone_examples:
    print(telephone_url)

telephone_html = """
<a href="tel:+919876543210">Call +91 98765 43210</a>
""".strip()

print(telephone_html)

# tel: links are especially useful on mobile devices.
#
# The exact handling depends on the user's operating system and installed
# applications.
#
# Displayed telephone text should remain understandable to users even when
# the device cannot initiate a call.


# ============================================================================
# 19. DOWNLOAD LINKS
# ============================================================================

print_section("19. DOWNLOAD LINKS")

download_example = """
<a href="/files/report.pdf" download>
    Download the report
</a>

<a href="/files/report.pdf" download="annual-report.pdf">
    Download Annual Report
</a>
""".strip()

print(download_example)

# The download attribute indicates that the linked resource is intended
# to be downloaded rather than navigated to.
#
# Browser behavior can depend on:
# - origin
# - HTTP response headers
# - browser policy
# - resource type
# - security restrictions


# ============================================================================
# 20. TARGET ATTRIBUTE
# ============================================================================

print_section("20. TARGETING BROWSING CONTEXTS")

target_example = """
<a href="https://example.org" target="_blank">
    Open external website
</a>
""".strip()

print(target_example)

# Common target values:
#
# _self   -> current browsing context
# _blank  -> new browsing context
# _parent -> parent browsing context
# _top    -> top-level browsing context
#
# Named targets can also be used:
#
# target="documentation"
#
# Excessive use of _blank can make navigation harder to understand.
#
# When opening a new context, rel="noopener" is a useful defensive practice.
# Modern browsers have changed some default behaviors, but explicit security
# intent is still clearer in source code.


# ============================================================================
# 21. REL ATTRIBUTE AND LINK RELATIONSHIPS
# ============================================================================

print_section("21. RELATIONSHIPS AND SECURITY")

rel_example = """
<a
    href="https://example.org"
    target="_blank"
    rel="noopener noreferrer"
>
    Open external resource
</a>
""".strip()

print(rel_example)

# Important rel values:
#
# noopener
#   Prevents the new browsing context from receiving a reference to the
#   opener through window.opener.
#
# noreferrer
#   Requests that referrer information not be sent and generally also
#   implies noopener behavior in modern browser implementations.
#
# nofollow
#   Provides a hint concerning search-engine crawling/ranking behavior.
#   It is not an access-control mechanism.
#
# sponsored
#   Identifies links associated with paid advertisements or sponsorship.
#
# ugc
#   Identifies links in user-generated content.
#
# rel values should communicate the actual relationship rather than being
# added mechanically.


# ============================================================================
# 22. ACCESSIBLE LINK TEXT
# ============================================================================

print_section("22. ACCESSIBLE LINK TEXT")

good_link_examples = """
<a href="/annual-report">Read the 2026 annual report</a>

<a href="/pricing">View pricing plans</a>

<a href="/contact">Contact the support team</a>
""".strip()

bad_link_examples = """
<a href="/annual-report">Click here</a>
<a href="/pricing">Read more</a>
<a href="/contact">Here</a>
""".strip()

print("Preferred:")
print(good_link_examples)

print("\nWeak link text:")
print(bad_link_examples)

# Link text should communicate destination or purpose.
#
# A user should often be able to understand a link from the link text itself.
#
# "Click here" is weak because it provides little information about where
# the link leads.
#
# This matters especially when links are encountered independently by
# assistive technology or when users scan a page.


# ============================================================================
# 23. LINKS AND IMAGES
# ============================================================================

print_section("23. LINKS CONTAINING IMAGES")

image_link = """
<a href="/profile">
    <img src="/images/profile.png" alt="View profile">
</a>
""".strip()

print(image_link)

# When an image is the meaningful content of a link, its alternative text
# should communicate the link's purpose.
#
# If the image is purely decorative and the link has visible adjacent text,
# the image may have empty alt text:
#
# <a href="/profile">
#     <img src="/images/profile-icon.svg" alt="">
#     <span>Profile</span>
# </a>
#
# Avoid duplicating the same accessible name unnecessarily.


# ============================================================================
# 24. SPAN VERSUS LINK
# ============================================================================

print_section("24. <span> IS NOT A LINK")

span_example = """
<p>
    <span>Ordinary inline text</span>
</p>

<p>
    <a href="/details">Actual hyperlink</a>
</p>
""".strip()

print(span_example)

# <span> has no built-in navigation behavior.
#
# JavaScript can make arbitrary elements interactive, but replacing a native
# <a> with a clickable <span> can introduce accessibility, keyboard,
# semantics, focus, and browser-behavior problems.
#
# Use <a> for navigation.
# Use <button> for actions.
#
# This distinction is fundamental.


# ============================================================================
# 25. URL ENCODING
# ============================================================================

print_section("25. URL ENCODING")

unsafe_path_segment = "HTML Text & Links"
encoded_path_segment = quote(unsafe_path_segment, safe="")

print(f"Original path segment: {unsafe_path_segment}")
print(f"Encoded path segment:  {encoded_path_segment}")

query_data = {
    "topic": "HTML Text & Links",
    "level": "advanced",
    "page": 2,
}

encoded_query = urlencode(query_data)
generated_url = "https://example.com/search?" + encoded_query

print(f"Encoded query: {encoded_query}")
print(f"Generated URL: {generated_url}")

# URLs have syntax rules.
#
# Characters such as spaces and ampersands can have special meanings.
#
# urlencode() is useful for query parameters.
# quote() is useful for individual path components.
#
# Encoding an entire URL blindly is usually wrong because it can encode
# structural characters such as :, /, ?, and &.


# ============================================================================
# 26. HTML ESCAPING
# ============================================================================

print_section("26. HTML ESCAPING")

user_text = '<script>alert("unsafe")</script> & "quoted"'
escaped_text = escape(user_text)

print("Original:")
print(user_text)

print("\nEscaped:")
print(escaped_text)

safe_text_html = f"<p>{escaped_text}</p>"
print("\nHTML containing escaped text:")
print(safe_text_html)

# HTML special characters include:
#
# &   -> &amp;
# <   -> &lt;
# >   -> &gt;
# "   -> &quot;
# '   -> &#x27;
#
# Context matters.
#
# html.escape() protects ordinary HTML text contexts.
#
# It is not a universal security solution for every possible context.
# JavaScript strings, CSS, URLs, and HTML attributes can have different
# escaping requirements.


# ============================================================================
# 27. SAFE HTML ATTRIBUTE CONSTRUCTION
# ============================================================================

print_section("27. SAFE ATTRIBUTE CONSTRUCTION")

def make_anchor(href: str, text: str) -> str:
    """
    Construct an anchor with HTML-escaped attribute and text content.

    This function demonstrates context-aware HTML escaping.
    """
    safe_href = escape(href, quote=True)
    safe_text = escape(text)
    return f'<a href="{safe_href}">{safe_text}</a>'


safe_anchor = make_anchor(
    'https://example.com/search?q="HTML"',
    'Search for HTML',
)

print(safe_anchor)

# Never assume user-provided values are safe merely because they are placed
# into an href attribute.
#
# Correct HTML escaping protects the HTML syntax, but applications should
# also validate whether a URL scheme or destination is acceptable.


# ============================================================================
# 28. URL SCHEME VALIDATION
# ============================================================================

print_section("28. URL SCHEME VALIDATION")

ALLOWED_WEB_SCHEMES = {"http", "https"}


def is_http_url(url: str) -> bool:
    """
    Return True only when the URL uses HTTP or HTTPS.

    This is useful when an application expects ordinary web URLs.
    """
    parsed = urlparse(url)
    return parsed.scheme.lower() in ALLOWED_WEB_SCHEMES and bool(parsed.netloc)


test_urls = [
    "https://example.com",
    "http://example.com",
    "mailto:test@example.com",
    "tel:+919876543210",
    "javascript:alert(1)",
    "/local/path",
]

for test_url in test_urls:
    print(f"{test_url:40} -> {is_http_url(test_url)}")

# Security-sensitive applications may need to reject dangerous or unexpected
# schemes such as javascript: when accepting arbitrary URLs.
#
# The exact validation policy depends on the application's requirements.
#
# A validator that accepts only https:// URLs is usually safer than one that
# attempts to enumerate every possible protocol.


# ============================================================================
# 29. RELATIVE URL SAFETY
# ============================================================================

print_section("29. RELATIVE URL VALIDATION")

def is_relative_url(url: str) -> bool:
    """
    Determine whether a reference has no URL scheme and no network location.

    This accepts references such as:
        about.html
        /about.html
        #section
        ?page=2

    It rejects:
        https://example.com
        javascript:...
    """
    parsed = urlparse(url)
    return not parsed.scheme and not parsed.netloc


relative_test_urls = [
    "about.html",
    "/about.html",
    "../about.html",
    "#section",
    "?page=2",
    "https://example.com",
    "javascript:alert(1)",
]

for test_url in relative_test_urls:
    print(f"{test_url:35} -> {is_relative_url(test_url)}")


# ============================================================================
# 30. URL NORMALIZATION
# ============================================================================

print_section("30. URL PARSING AND NORMALIZATION")

def normalize_http_url(url: str) -> str:
    """
    Normalize basic HTTP(S) URL components without attempting to implement
    the complete URL Standard.

    The function:
    - strips surrounding whitespace
    - lowercases the scheme
    - lowercases the hostname
    - removes the default HTTP/HTTPS port
    - preserves path, query, and fragment
    """
    url = url.strip()
    parsed = urlparse(url)

    scheme = parsed.scheme.lower()

    if scheme not in {"http", "https"}:
        raise ValueError("Only HTTP and HTTPS URLs are supported.")

    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL must contain a hostname.")

    port = parsed.port

    if port is None:
        netloc = hostname.lower()
    elif (scheme == "http" and port == 80) or (
        scheme == "https" and port == 443
    ):
        netloc = hostname.lower()
    else:
        netloc = f"{hostname.lower()}:{port}"

    return urlunparse(
        (
            scheme,
            netloc,
            parsed.path,
            parsed.params,
            parsed.query,
            parsed.fragment,
        )
    )


normalization_examples = [
    " HTTPS://EXAMPLE.COM:443/docs/page.html ",
    "http://example.com:80/index.html",
    "https://example.com:8443/app",
]

for example in normalization_examples:
    print(f"{example!r}")
    print(" ->", normalize_http_url(example))


# ============================================================================
# 31. URL RESOLUTION
# ============================================================================

print_section("31. URL RESOLUTION WITH urljoin")

base = "https://example.com/a/b/page.html"

references = [
    "next.html",
    "../index.html",
    "/contact",
    "#top",
    "?sort=price",
    "https://other.example/page",
]

for reference in references:
    print(f"{reference:35} -> {urljoin(base, reference)}")


# ============================================================================
# 32. LINK DATA MODEL
# ============================================================================

print_section("32. REPRESENTING LINKS AS PYTHON OBJECTS")


@dataclass(frozen=True)
class Link:
    """
    A small model representing an HTML hyperlink.

    The model keeps destination and visible text separate, which makes it
    easier to validate URLs and generate HTML consistently.
    """

    href: str
    text: str
    target: Optional[str] = None
    rel: Optional[str] = None

    def to_html(self) -> str:
        """Render this link as safely escaped HTML."""
        attributes = [
            f'href="{escape(self.href, quote=True)}"'
        ]

        if self.target:
            attributes.append(
                f'target="{escape(self.target, quote=True)}"'
            )

        if self.rel:
            attributes.append(
                f'rel="{escape(self.rel, quote=True)}"'
            )

        safe_text = escape(self.text)

        return (
            "<a "
            + " ".join(attributes)
            + ">"
            + safe_text
            + "</a>"
        )


example_link = Link(
    href="https://example.com",
    text="Visit Example",
    target="_blank",
    rel="noopener noreferrer",
)

print(example_link.to_html())


# ============================================================================
# 33. LINK VALIDATION
# ============================================================================

print_section("33. LINK VALIDATION")

@dataclass(frozen=True)
class LinkValidationResult:
    """Result of validating a hyperlink."""

    valid: bool
    errors: tuple[str, ...]


def validate_link(link: Link) -> LinkValidationResult:
    """
    Validate basic properties of a Link.

    This is not a complete HTML or URL validator. It demonstrates application
    level checks that are commonly useful before rendering links.
    """
    errors: list[str] = []

    if not link.href.strip():
        errors.append("href must not be empty.")

    if not link.text.strip():
        errors.append("Link text must not be empty.")

    parsed = urlparse(link.href)

    if parsed.scheme.lower() == "javascript":
        errors.append("javascript: URLs are not permitted.")

    if link.target == "_blank":
        if link.rel is None:
            errors.append(
                "Links using target=_blank should explicitly consider rel."
            )

    return LinkValidationResult(
        valid=not errors,
        errors=tuple(errors),
    )


links_to_validate = [
    Link("https://example.com", "Example"),
    Link("", "Missing destination"),
    Link("javascript:alert(1)", "Unsafe"),
    Link("https://example.com", "", "_blank", "noopener"),
    Link("https://example.com", "New tab", "_blank", "noopener"),
]

for link in links_to_validate:
    result = validate_link(link)
    print(link)
    print("Valid:", result.valid)
    if result.errors:
        for error in result.errors:
            print("  -", error)


# ============================================================================
# 34. GENERATING A COMPLETE HTML DOCUMENT
# ============================================================================

print_section("34. GENERATING A COMPLETE HTML DOCUMENT")

def build_html_document(
    title: str,
    body_content: str,
    language: str = "en",
) -> str:
    """
    Build a minimal standards-oriented HTML document.

    body_content is assumed to already be trusted HTML markup.
    Ordinary user text must be escaped before being inserted.
    """
    safe_title = escape(title)

    return f"""<!DOCTYPE html>
<html lang="{escape(language, quote=True)}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{safe_title}</title>
</head>
<body>
{body_content}
</body>
</html>"""


body = """
<nav aria-label="Primary navigation">
    <a href="#introduction">Introduction</a>
    <a href="#links">Links</a>
    <a href="#contact">Contact</a>
</nav>

<main>
    <h1 id="introduction">HTML Text and Links</h1>

    <p>
        HTML gives structure and meaning to web content.
    </p>

    <section id="links">
        <h2>Links</h2>
        <p>
            Visit the
            <a href="https://example.com">example website</a>.
        </p>
    </section>

    <section id="contact">
        <h2>Contact</h2>
        <p>
            <a href="mailto:contact@example.com">Email the team</a>
        </p>
        <p>
            <a href="tel:+919876543210">Call the team</a>
        </p>
    </section>
</main>
""".strip()

complete_document = build_html_document(
    "HTML Text and Links",
    body,
)

print(complete_document)


# ============================================================================
# 35. BUILDING A NAVIGATION MENU PROGRAMMATICALLY
# ============================================================================

print_section("35. PROGRAMMATIC NAVIGATION GENERATION")

@dataclass(frozen=True)
class NavigationItem:
    """One item in a navigation menu."""

    label: str
    href: str


def render_navigation(
    items: Iterable[NavigationItem],
    aria_label: str = "Primary navigation",
) -> str:
    """Render navigation items using semantic HTML."""
    safe_label = escape(aria_label, quote=True)

    rendered_items = []

    for item in items:
        safe_href = escape(item.href, quote=True)
        safe_label_text = escape(item.label)

        rendered_items.append(
            f'        <li><a href="{safe_href}">'
            f'{safe_label_text}</a></li>'
        )

    return (
        f'<nav aria-label="{safe_label}">\n'
        "    <ul>\n"
        + "\n".join(rendered_items)
        + "\n    </ul>\n"
        "</nav>"
    )


navigation_items = [
    NavigationItem("Home", "/"),
    NavigationItem("Documentation", "/docs"),
    NavigationItem("Pricing", "/pricing"),
    NavigationItem("Contact", "/contact"),
]

print(render_navigation(navigation_items))


# ============================================================================
# 36. ANCHOR GENERATOR
# ============================================================================

print_section("36. REUSABLE ANCHOR GENERATION")

def anchor(
    href: str,
    text: str,
    *,
    target: Optional[str] = None,
    rel: Optional[str] = None,
) -> str:
    """Generate a safely escaped anchor element."""
    attributes = [f'href="{escape(href, quote=True)}"']

    if target is not None:
        attributes.append(
            f'target="{escape(target, quote=True)}"'
        )

    if rel is not None:
        attributes.append(
            f'rel="{escape(rel, quote=True)}"'
        )

    return (
        "<a "
        + " ".join(attributes)
        + ">"
        + escape(text)
        + "</a>"
    )


print(anchor("/about", "About"))
print(anchor("#contact", "Contact"))
print(
    anchor(
        "https://example.com",
        "External website",
        target="_blank",
        rel="noopener noreferrer",
    )
)


# ============================================================================
# 37. MAILTO GENERATION
# ============================================================================

print_section("37. SAFE MAILTO GENERATION")

def build_mailto(
    address: str,
    *,
    subject: Optional[str] = None,
    body: Optional[str] = None,
    cc: Optional[Iterable[str]] = None,
    bcc: Optional[Iterable[str]] = None,
) -> str:
    """
    Construct a mailto URL using URL encoding for query parameters.

    This does not validate whether an email address actually exists.
    """
    if not address or "@" not in address:
        raise ValueError("A basic email address is required.")

    query: list[tuple[str, str]] = []

    if subject is not None:
        query.append(("subject", subject))

    if body is not None:
        query.append(("body", body))

    if cc:
        query.append(("cc", ",".join(cc)))

    if bcc:
        query.append(("bcc", ",".join(bcc)))

    if query:
        return f"mailto:{address}?{urlencode(query)}"

    return f"mailto:{address}"


generated_mailto = build_mailto(
    "contact@example.com",
    subject="Project Inquiry",
    body="Hello,\n\nI would like to discuss the project.",
)

print(generated_mailto)


# ============================================================================
# 38. TELEPHONE LINK GENERATION
# ============================================================================

print_section("38. TELEPHONE LINK GENERATION")

def build_tel(phone_number: str) -> str:
    """
    Create a tel: URL.

    This simple implementation retains digits and a leading plus sign.
    Production systems may need locale-aware telephone normalization.
    """
    cleaned = re.sub(r"[^\d+]", "", phone_number)

    if cleaned.count("+") > 1:
        raise ValueError("Invalid telephone number.")

    if "+" in cleaned and not cleaned.startswith("+"):
        raise ValueError("The plus sign must appear at the beginning.")

    if not re.search(r"\d", cleaned):
        raise ValueError("Telephone number must contain digits.")

    return f"tel:{cleaned}"


print(build_tel("+91 98765 43210"))
print(build_tel("+1 (212) 555-0123"))


# ============================================================================
# 39. SAME-PAGE TABLE OF CONTENTS
# ============================================================================

print_section("39. TABLE OF CONTENTS")

toc_sections = [
    ("introduction", "Introduction"),
    ("terminology", "Terminology"),
    ("examples", "Examples"),
    ("edge-cases", "Edge Cases"),
    ("contact", "Contact"),
]

toc_html = "\n".join(
    f'<li><a href="#{escape(section_id, quote=True)}">'
    f'{escape(label)}</a></li>'
    for section_id, label in toc_sections
)

print(
    "<nav aria-label=\"Table of contents\">\n"
    "    <ol>\n"
    f"{toc_html}\n"
    "    </ol>\n"
    "</nav>"
)


# ============================================================================
# 40. EDGE CASE: FRAGMENT IDS
# ============================================================================

print_section("40. EDGE CASES WITH FRAGMENT IDS")

fragment_ids = [
    "introduction",
    "advanced-topics",
    "section_2",
    "section.2",
    "123",
    "spaces are awkward",
]

for fragment_id in fragment_ids:
    href = "#" + fragment_id
    print(f"ID: {fragment_id!r:25} href: {href}")

# HTML id values have broad character support, but simple IDs are easier
# to reference, maintain, style, and debug.
#
# Prefer:
#   id="installation"
#   href="#installation"
#
# over unnecessarily complicated identifiers.


# ============================================================================
# 41. EDGE CASE: URL QUERY PARAMETERS
# ============================================================================

print_section("41. QUERY PARAMETER EDGE CASES")

parameters = {
    "search": "HTML & CSS",
    "page": "2",
    "sort": "price ascending",
    "empty": "",
}

encoded = urlencode(parameters)

print("Encoded:", encoded)
print("Decoded:", parse_qs(encoded, keep_blank_values=True))

# Important:
# urlencode() handles spaces and reserved characters in parameter values.
#
# Manually writing:
#
# ?search=HTML & CSS
#
# is ambiguous because & separates query parameters.
#
# Correct encoding produces a value such as:
#
# search=HTML+%26+CSS


# ============================================================================
# 42. EDGE CASE: AMPERSANDS IN HTML ATTRIBUTES
# ============================================================================

print_section("42. AMPERSANDS IN HTML")

query_url = "https://example.com/search?topic=html&sort=latest"

# In HTML source, an ampersand can be written as &amp; for a standards-friendly
# representation:
html_href = escape(query_url, quote=True)

print("URL value:", query_url)
print("HTML attribute value:", html_href)

print(
    f'<a href="{html_href}">Search results</a>'
)


# ============================================================================
# 43. EDGE CASE: QUOTE CHARACTERS IN ATTRIBUTES
# ============================================================================

print_section("43. QUOTES IN ATTRIBUTES")

attribute_value = 'https://example.com/search?q="HTML links"'
safe_attribute = escape(attribute_value, quote=True)

print(f'<a href="{safe_attribute}">Search</a>')


# ============================================================================
# 44. TEXT FORMATTING COMPARISON
# ============================================================================

print_section("44. TEXT FORMATTING COMPARISON")

formatting_comparison = """
<strong>Important</strong>
<b>Stylistically bold</b>

<em>Emphasized</em>
<i>Alternate voice or term</i>

<del>Removed text</del>
<ins>Inserted text</ins>

<mark>Relevant highlighted text</mark>
<small>Small print</small>

<s>Text that is no longer accurate or relevant</s>
<u>Text with an annotation-like underline</u>
""".strip()

print(formatting_comparison)

# The key principle is semantics.
#
# CSS can make text bold or italic visually, but semantic elements provide
# information about why the text has that distinction.


# ============================================================================
# 45. ENTITY REFERENCES
# ============================================================================

print_section("45. HTML CHARACTER REFERENCES")

entity_examples = """
<p>&lt; means less than.</p>
<p>&gt; means greater than.</p>
<p>&amp; represents an ampersand.</p>
<p>&quot; represents a quotation mark.</p>
<p>&copy; represents the copyright symbol.</p>
""".strip()

print(entity_examples)

# Character references are useful when literal characters could otherwise be
# interpreted as HTML markup or when representing characters through named
# or numeric references.


# ============================================================================
# 46. WHITESPACE
# ============================================================================

print_section("46. HTML WHITESPACE")

whitespace_example = """
<p>
    HTML generally collapses ordinary sequences of whitespace in normal
    text rendering.
</p>

<pre>
    This whitespace is preserved.
</pre>
""".strip()

print(whitespace_example)

# Source formatting does not necessarily determine visual spacing.
#
# For example:
#
# <p>Hello      world</p>
#
# normally renders with collapsed whitespace between the words.
#
# CSS controls visual spacing.
# <pre> preserves whitespace as part of its semantics.


# ============================================================================
# 47. LINK PURPOSE AND DESTINATION
# ============================================================================

print_section("47. LINK PURPOSE")

links_with_purpose = [
    Link("/reports/2026.pdf", "Download the 2026 annual report"),
    Link("/pricing", "View pricing plans"),
    Link("#faq", "Jump to frequently asked questions"),
    Link("mailto:support@example.com", "Email customer support"),
    Link("tel:+919876543210", "Call customer support"),
]

for item in links_with_purpose:
    print(item.to_html())


# ============================================================================
# 48. EXTERNAL LINKS
# ============================================================================

print_section("48. EXTERNAL LINKS")

external_link = anchor(
    "https://developer.example.org/documentation",
    "Read the external documentation",
)

print(external_link)

# External links should make their destination understandable.
#
# If a link opens a new browsing context, users should not be surprised.
# Visual indicators can be added through CSS or accessible text where
# appropriate.


# ============================================================================
# 49. INTERNAL LINKS
# ============================================================================

print_section("49. INTERNAL LINKS")

internal_links = [
    anchor("/", "Home"),
    anchor("/products", "Products"),
    anchor("/products/phones", "Phones"),
    anchor("../about.html", "About"),
    anchor("#features", "Features"),
]

for link_html in internal_links:
    print(link_html)


# ============================================================================
# 50. RELATIVE URL MECHANISM
# ============================================================================

print_section("50. RELATIVE URL MECHANISM")

def demonstrate_relative_resolution(
    base: str,
    references: Iterable[str],
) -> None:
    """Show how references resolve against a base URL."""
    for reference in references:
        print(
            f"Base: {base}\n"
            f"Ref:  {reference}\n"
            f"URL:  {urljoin(base, reference)}\n"
        )


demonstrate_relative_resolution(
    "https://example.com/docs/reference/index.html",
    [
        "intro.html",
        "../guide/index.html",
        "../../",
        "/contact",
        "#top",
    ],
)


# ============================================================================
# 51. LINK COLLECTION
# ============================================================================

print_section("51. LINK COLLECTION")

class LinkCollection:
    """
    Store and render multiple links.

    This demonstrates a small reusable abstraction for applications that
    generate HTML navigation or lists.
    """

    def __init__(self, links: Optional[Iterable[Link]] = None) -> None:
        self._links: list[Link] = list(links or [])

    def add(self, link: Link) -> None:
        """Add one link."""
        self._links.append(link)

    def validate(self) -> list[LinkValidationResult]:
        """Validate every stored link."""
        return [validate_link(link) for link in self._links]

    def render_list(self) -> str:
        """Render the links as an unordered HTML list."""
        items = "\n".join(
            f"    <li>{link.to_html()}</li>"
            for link in self._links
        )

        return f"<ul>\n{items}\n</ul>"


collection = LinkCollection()

collection.add(Link("/", "Home"))
collection.add(Link("/about", "About"))
collection.add(Link("/contact", "Contact"))

print(collection.render_list())


# ============================================================================
# 52. VALIDATING A GENERATED DOCUMENT
# ============================================================================

print_section("52. BASIC HTML STRUCTURE CHECKING")

def basic_html_structure_checks(html_document: str) -> list[str]:
    """
    Perform lightweight structural checks.

    This is intentionally not a replacement for a complete HTML parser or
    standards validator. It demonstrates useful sanity checks.
    """
    errors: list[str] = []

    if "<!DOCTYPE html>" not in html_document:
        errors.append("Missing HTML5 doctype.")

    if "<html" not in html_document:
        errors.append("Missing html element.")

    if "<head>" not in html_document:
        errors.append("Missing head element.")

    if "<body>" not in html_document:
        errors.append("Missing body element.")

    if "<title>" not in html_document:
        errors.append("Missing title element.")

    return errors


checks = basic_html_structure_checks(complete_document)

if checks:
    for error in checks:
        print("ERROR:", error)
else:
    print("Basic HTML structure checks passed.")


# ============================================================================
# 53. CHECKING FRAGMENT TARGETS
# ============================================================================

print_section("53. CHECKING INTERNAL FRAGMENT LINKS")

def extract_ids(html_document: str) -> set[str]:
    """Extract simple id attribute values for demonstration purposes."""
    pattern = re.compile(
        r'\bid\s*=\s*["\']([^"\']+)["\']',
        re.IGNORECASE,
    )
    return set(pattern.findall(html_document))


def extract_fragment_links(html_document: str) -> set[str]:
    """
    Extract simple href values beginning with '#'.

    This deliberately handles common educational examples rather than trying
    to implement a complete HTML tokenizer.
    """
    pattern = re.compile(
        r'\bhref\s*=\s*["\']#([^"\']+)["\']',
        re.IGNORECASE,
    )
    return set(pattern.findall(html_document))


def find_broken_fragments(html_document: str) -> set[str]:
    """Return fragment references whose IDs do not exist."""
    ids = extract_ids(html_document)
    fragments = extract_fragment_links(html_document)
    return fragments - ids


fragment_test_document = """
<nav>
    <a href="#intro">Introduction</a>
    <a href="#missing">Missing section</a>
</nav>

<section id="intro">
    <h2>Introduction</h2>
</section>
""".strip()

broken_fragments = find_broken_fragments(fragment_test_document)

print("IDs:", extract_ids(fragment_test_document))
print("Fragments:", extract_fragment_links(fragment_test_document))
print("Broken fragments:", broken_fragments)


# ============================================================================
# 54. DUPLICATE ID DETECTION
# ============================================================================

print_section("54. DUPLICATE ID DETECTION")

def find_duplicate_ids(html_document: str) -> set[str]:
    """Find duplicate id attributes in a simple HTML document."""
    ids = extract_ids(html_document)

    pattern = re.compile(
        r'\bid\s*=\s*["\']([^"\']+)["\']',
        re.IGNORECASE,
    )

    occurrences: dict[str, int] = {}

    for identifier in pattern.findall(html_document):
        occurrences[identifier] = occurrences.get(identifier, 0) + 1

    return {
        identifier
        for identifier, count in occurrences.items()
        if count > 1
    }


duplicate_id_document = """
<section id="products">
    <h2>Products</h2>
</section>

<section id="products">
    <h2>Another Products Section</h2>
</section>
""".strip()

print(
    "Duplicate IDs:",
    find_duplicate_ids(duplicate_id_document),
)

# Duplicate IDs make fragment navigation ambiguous and can cause problems
# for scripts, styles, accessibility APIs, and DOM methods that expect a
# unique identifier.


# ============================================================================
# 55. SECURITY: DANGEROUS URL SCHEMES
# ============================================================================

print_section("55. SECURITY CHECK FOR LINK DESTINATIONS")

DANGEROUS_SCHEMES = {
    "javascript",
    "vbscript",
    "data",
}


def has_dangerous_scheme(url: str) -> bool:
    """Check whether a URL uses a potentially dangerous scheme."""
    scheme = urlparse(url).scheme.lower()
    return scheme in DANGEROUS_SCHEMES


security_test_urls = [
    "https://example.com",
    "mailto:test@example.com",
    "tel:+919876543210",
    "javascript:alert(1)",
    "data:text/html,<h1>Hello</h1>",
]

for url in security_test_urls:
    print(
        f"{url:50} "
        f"dangerous={has_dangerous_scheme(url)}"
    )

# Important security principle:
#
# If users can supply arbitrary link destinations, do not simply insert those
# destinations into HTML.
#
# A secure system normally applies:
#   1. URL parsing
#   2. scheme validation
#   3. host/domain policy where necessary
#   4. HTML escaping
#   5. appropriate security headers
#   6. output encoding for the exact context


# ============================================================================
# 56. SECURITY: OPENER RELATIONSHIP
# ============================================================================

print_section("56. SECURITY WITH target=_blank")

def secure_external_link(url: str, text: str) -> str:
    """
    Create a new-context external link with explicit defensive rel values.
    """
    return anchor(
        url,
        text,
        target="_blank",
        rel="noopener noreferrer",
    )


print(
    secure_external_link(
        "https://example.org",
        "Open external resource",
    )
)


# ============================================================================
# 57. SECURITY: HTML INJECTION
# ============================================================================

print_section("57. HTML INJECTION EXAMPLE")

attacker_supplied_text = '<img src=x onerror="alert(1)">'

unsafe_html = f"<p>{attacker_supplied_text}</p>"
safe_html = f"<p>{escape(attacker_supplied_text)}</p>"

print("Unsafe construction:")
print(unsafe_html)

print("\nEscaped construction:")
print(safe_html)

# The unsafe version interprets the input as HTML.
# The escaped version represents it as text.
#
# This is the basic distinction behind many HTML injection and XSS
# vulnerabilities.


# ============================================================================
# 58. SECURITY: ATTRIBUTE INJECTION
# ============================================================================

print_section("58. ATTRIBUTE INJECTION")

malicious_href = '" onmouseover="alert(1)" data-x="'

unsafe_anchor = f'<a href="{malicious_href}">Open</a>'
safe_anchor = make_anchor(malicious_href, "Open")

print("Unsafe:")
print(unsafe_anchor)

print("\nSafe HTML escaping:")
print(safe_anchor)

# Attribute escaping prevents attacker-controlled quotation marks from
# prematurely terminating the HTML attribute.
#
# URL policy validation is still separate from HTML escaping.


# ============================================================================
# 59. PERFORMANCE CONSIDERATIONS
# ============================================================================

print_section("59. PERFORMANCE CONSIDERATIONS")

# For ordinary static HTML, link rendering is inexpensive.
#
# Performance issues usually arise from:
# - very large DOM trees
# - thousands of unnecessary links
# - excessive client-side JavaScript attached to links
# - slow navigation endpoints
# - large external resources
# - inefficient server-side HTML generation
#
# Native <a> navigation is generally preferable to implementing navigation
# through JavaScript event handlers because the browser already understands
# the semantics and behavior of hyperlinks.


# ============================================================================
# 60. STATIC VERSUS DYNAMIC HTML
# ============================================================================

print_section("60. STATIC AND DYNAMIC LINK GENERATION")

def render_article(
    title: str,
    sections: Iterable[tuple[str, str, str]],
) -> str:
    """
    Render an article from trusted section structure.

    Each tuple contains:
        (section_id, heading, paragraph_text)

    Text values are escaped before insertion.
    """
    rendered_sections = []

    for section_id, heading, paragraph_text in sections:
        rendered_sections.append(
            f'<section id="{escape(section_id, quote=True)}">\n'
            f'    <h2>{escape(heading)}</h2>\n'
            f'    <p>{escape(paragraph_text)}</p>\n'
            "</section>"
        )

    return (
        f"<article>\n"
        f"    <h1>{escape(title)}</h1>\n"
        + "\n".join(rendered_sections)
        + "\n</article>"
    )


article_html = render_article(
    "HTML Links",
    [
        (
            "absolute",
            "Absolute URLs",
            "Absolute URLs identify a destination explicitly.",
        ),
        (
            "relative",
            "Relative URLs",
            "Relative URLs resolve against a base URL.",
        ),
        (
            "fragments",
            "Fragments",
            "Fragments target an element within a document.",
        ),
    ],
)

print(article_html)


# ============================================================================
# 61. LINK CRAWLING CONCEPT
# ============================================================================

print_section("61. LINK EXTRACTION CONCEPT")

def extract_href_values(html_document: str) -> list[str]:
    """
    Extract basic href values.

    This regular-expression implementation is educational only. Real HTML
    parsing should use an HTML parser because HTML syntax is considerably
    more complex than this pattern.
    """
    pattern = re.compile(
        r"<a\b[^>]*\bhref\s*=\s*[\"']([^\"']+)[\"']",
        re.IGNORECASE,
    )

    return pattern.findall(html_document)


crawl_example = """
<a href="/home">Home</a>
<a href="/products">Products</a>
<a href="https://example.org">External</a>
<a href="#contact">Contact</a>
""".strip()

print(extract_href_values(crawl_example))

# Important implementation lesson:
#
# Regular expressions can be useful for controlled demonstrations and
# narrow patterns, but HTML is not generally safe to parse with a regex-only
# approach.


# ============================================================================
# 62. RESOLVING EXTRACTED LINKS
# ============================================================================

print_section("62. RESOLVING EXTRACTED LINKS")

page_url = "https://example.com/docs/page.html"

for href in extract_href_values(crawl_example):
    print(
        f"{href:30} -> {urljoin(page_url, href)}"
    )


# ============================================================================
# 63. CLASSIFICATION OF LINK TYPES
# ============================================================================

print_section("63. CLASSIFYING LINKS")

def classify_link(href: str) -> str:
    """
    Classify common hyperlink forms.
    """
    parsed = urlparse(href)

    if href.startswith("#"):
        return "same-page fragment"

    if parsed.scheme == "mailto":
        return "email link"

    if parsed.scheme == "tel":
        return "telephone link"

    if parsed.scheme in {"http", "https"}:
        return "absolute web URL"

    if href.startswith("/"):
        return "root-relative URL"

    if href.startswith("../") or href.startswith("./"):
        return "path-relative URL"

    if href.startswith("?"):
        return "query reference"

    if not parsed.scheme and not parsed.netloc:
        return "relative reference"

    return "other"


classification_examples = [
    "https://example.com",
    "/about",
    "../about",
    "./about",
    "about.html",
    "#contact",
    "?page=2",
    "mailto:person@example.com",
    "tel:+919876543210",
]

for href in classification_examples:
    print(f"{href:35} -> {classify_link(href)}")


# ============================================================================
# 64. ACCESSIBLE NAVIGATION STRUCTURE
# ============================================================================

print_section("64. ACCESSIBLE NAVIGATION STRUCTURE")

accessible_navigation = """
<nav aria-label="Documentation">
    <h2>Documentation</h2>
    <ul>
        <li>
            <a href="/docs/getting-started">
                Getting started
            </a>
        </li>
        <li>
            <a href="/docs/reference">
                API reference
            </a>
        </li>
        <li>
            <a href="/docs/examples">
                Examples
            </a>
        </li>
    </ul>
</nav>
""".strip()

print(accessible_navigation)

# Good navigation structure should consider:
# - meaningful link text
# - keyboard operation
# - visible focus
# - semantic landmarks
# - logical heading hierarchy
# - sufficient distinction between interactive and ordinary text
#
# CSS should preserve a clearly visible focus indicator.


# ============================================================================
# 65. BUTTON VS LINK
# ============================================================================

print_section("65. BUTTON VERSUS LINK")

button_vs_link = """
<a href="/settings">Open settings</a>

<button type="button">
    Save settings
</button>
""".strip()

print(button_vs_link)

# Use a link when the user is navigating to a resource or location.
# Use a button when the user is performing an action.
#
# Examples:
#
# Link:
#   View profile
#   Open report
#   Go to dashboard
#
# Button:
#   Save
#   Delete
#   Submit
#   Open modal
#
# This distinction improves semantics and browser behavior.


# ============================================================================
# 66. LINK STATE AND CSS
# ============================================================================

print_section("66. LINK STATES")

css_example = """
a:link {
    text-decoration: underline;
}

a:visited {
    text-decoration: underline;
}

a:hover {
    text-decoration: none;
}

a:focus-visible {
    outline: 2px solid currentColor;
}

a:active {
    text-decoration: underline;
}
""".strip()

print(css_example)

# Common link pseudo-classes:
#
# :link
# :visited
# :hover
# :focus
# :focus-visible
# :active
#
# Focus styling is particularly important for keyboard users.
#
# Removing the default outline without providing a visible replacement can
# make keyboard navigation difficult.


# ============================================================================
# 67. SAME-PAGE NAVIGATION WITH A BACK LINK
# ============================================================================

print_section("67. BACK-TO-TOP NAVIGATION")

back_to_top = """
<a href="#top">Back to top</a>

<h1 id="top">HTML Text and Links</h1>
""".strip()

print(back_to_top)


# ============================================================================
# 68. FRAGMENT URL WITH QUERY STRING
# ============================================================================

print_section("68. QUERY AND FRAGMENT TOGETHER")

query_fragment_url = "/search?query=html&page=2#results"

parsed = urlparse(query_fragment_url)

print("Path:", parsed.path)
print("Query:", parsed.query)
print("Fragment:", parsed.fragment)

# The ordering is:
#
# /path?query=value#fragment
#
# The fragment follows the query string.
#
# A fragment is not another query parameter.


# ============================================================================
# 69. URL CONSTRUCTION FROM COMPONENTS
# ============================================================================

print_section("69. URL CONSTRUCTION FROM COMPONENTS")

components = (
    "https",
    "example.com",
    "/search",
    "",
    urlencode({"q": "HTML links", "page": 2}),
    "results",
)

constructed_url = urlunparse(components)

print(constructed_url)


# ============================================================================
# 70. BASE URL CONCEPT
# ============================================================================

print_section("70. BASE URL RESOLUTION")

base_document = "https://example.com/a/b/index.html"

relative_reference = "../images/logo.svg"

print(
    "Resolved:",
    urljoin(base_document, relative_reference),
)

# Browsers resolve relative URLs against the document's base URL.
#
# A document can also use a <base href="..."> element to change the base URL
# used for resolving relative URLs.
#
# Example:
#
# <base href="https://example.com/docs/">
#
# This can have broad effects on all relative links and resource references,
# so it should be used deliberately.


# ============================================================================
# 71. ABSOLUTE URL POLICY
# ============================================================================

print_section("71. URL POLICY")

@dataclass(frozen=True)
class URLPolicy:
    """Simple policy for validating links."""

    allow_http: bool = True
    allow_https: bool = True
    allow_mailto: bool = True
    allow_tel: bool = True
    allow_relative: bool = True


def is_allowed_url(url: str, policy: URLPolicy) -> bool:
    """Evaluate a URL against a basic application policy."""
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()

    if not scheme:
        return policy.allow_relative

    if scheme == "http":
        return policy.allow_http

    if scheme == "https":
        return policy.allow_https

    if scheme == "mailto":
        return policy.allow_mailto

    if scheme == "tel":
        return policy.allow_tel

    return False


policy = URLPolicy()

for url in [
    "https://example.com",
    "http://example.com",
    "/local",
    "mailto:user@example.com",
    "tel:+919876543210",
    "javascript:alert(1)",
]:
    print(
        f"{url:40} -> {is_allowed_url(url, policy)}"
    )


# ============================================================================
# 72. EXTERNAL HOST VALIDATION
# ============================================================================

print_section("72. HOST ALLOWLISTING")

def is_allowed_host(url: str, allowed_hosts: set[str]) -> bool:
    """
    Allow HTTP(S) URLs only when their hostname belongs to an allowlist.
    """
    parsed = urlparse(url)

    if parsed.scheme.lower() not in {"http", "https"}:
        return False

    hostname = parsed.hostname

    if not hostname:
        return False

    return hostname.lower() in {
        host.lower()
        for host in allowed_hosts
    }


allowed_hosts = {"example.com", "docs.example.com"}

for url in [
    "https://example.com/page",
    "https://docs.example.com/api",
    "https://evil.example/page",
]:
    print(
        f"{url:45} -> "
        f"{is_allowed_host(url, allowed_hosts)}"
    )


# ============================================================================
# 73. LINK TEXT DUPLICATION
# ============================================================================

print_section("73. AVOIDING UNNECESSARY LINK TEXT DUPLICATION")

duplicated_content = """
<a href="/report">
    <img src="/icons/pdf.svg" alt="PDF report">
    Download the report
</a>
""".strip()

better_content = """
<a href="/report">
    <img src="/icons/pdf.svg" alt="">
    Download the report
</a>
""".strip()

print("Potentially redundant:")
print(duplicated_content)

print("\nBetter when the icon is decorative:")
print(better_content)

# The correct choice depends on what information the image contributes.
# Decorative images inside meaningful links often use alt="" so the link's
# visible text supplies the accessible name.


# ============================================================================
# 74. LINK LIST GENERATOR WITH VALIDATION
# ============================================================================

print_section("74. PRODUCTION-STYLE LINK LIST")

def render_validated_links(
    links: Iterable[Link],
) -> str:
    """
    Render only valid links.

    In production, silently dropping invalid data may not be desirable.
    An application may instead reject the entire operation or log errors.
    """
    rendered = []

    for link in links:
        result = validate_link(link)

        if not result.valid:
            continue

        rendered.append(f"<li>{link.to_html()}</li>")

    return "<ul>\n" + "\n".join(rendered) + "\n</ul>"


validated_links = [
    Link("/", "Home"),
    Link("/about", "About"),
    Link("", "Invalid link"),
]

print(render_validated_links(validated_links))


# ============================================================================
# 75. FILE URL CONSIDERATIONS
# ============================================================================

print_section("75. FILE LINKS")

file_links = [
    "/documents/report.pdf",
    "/downloads/data.csv",
    "/assets/manual.html",
]

for file_link in file_links:
    print(anchor(file_link, f"Open {Path(file_link).name}"))

# HTML does not guarantee that every linked file will behave identically.
# Server response headers such as Content-Type and Content-Disposition can
# affect whether a browser displays or downloads a resource.


# ============================================================================
# 76. HTTP STATUS CODES AND LINKS
# ============================================================================

print_section("76. LINK DESTINATION AVAILABILITY")

# HTML creates a hyperlink but does not guarantee that its destination exists.
#
# A production website should monitor:
#
# 200 -> successful resource
# 301 -> permanent redirect
# 302 -> temporary redirect
# 304 -> cached representation still valid
# 403 -> forbidden
# 404 -> not found
# 410 -> permanently gone
# 500 -> server error
#
# Broken links can arise from renamed files, removed pages, incorrect paths,
# expired external resources, or configuration changes.


# ============================================================================
# 77. REDIRECT CONSIDERATIONS
# ============================================================================

print_section("77. REDIRECTS")

redirect_example = """
<a href="/old-page">
    Old page
</a>
""".strip()

print(redirect_example)

# A link can point to a URL that redirects elsewhere.
#
# Excessive redirect chains can:
# - increase latency
# - complicate debugging
# - create fragile navigation
# - complicate caching
#
# Production links should preferably point directly to canonical destinations
# when the destination is known.


# ============================================================================
# 78. LINK MAINTENANCE
# ============================================================================

print_section("78. LINK MAINTENANCE")

maintenance_principles = [
    "Use stable URLs where practical.",
    "Use meaningful link text.",
    "Prefer semantic HTML.",
    "Validate internally generated destinations.",
    "Encode query parameters correctly.",
    "Escape HTML output.",
    "Treat user-provided URLs as untrusted input.",
    "Check internal fragment targets.",
    "Avoid duplicate IDs.",
    "Use explicit security relationships for new browsing contexts.",
    "Preserve visible keyboard focus.",
]

for principle in maintenance_principles:
    print("-", principle)


# ============================================================================
# 79. COMPLETE MINI WEBSITE EXAMPLE
# ============================================================================

print_section("79. COMPLETE MINI WEBSITE")

mini_site_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HTML Text and Links</title>
</head>
<body id="top">

<header>
    <h1>HTML Text and Links</h1>

    <nav aria-label="Primary navigation">
        <ul>
            <li><a href="#text">Text</a></li>
            <li><a href="#links">Links</a></li>
            <li><a href="#contact">Contact</a></li>
        </ul>
    </nav>
</header>

<main>
    <section id="text">
        <h2>Text</h2>

        <p>
            HTML uses semantic elements to structure text.
        </p>

        <p>
            <strong>Strong importance</strong> and
            <em>stress emphasis</em> communicate different meanings.
        </p>

        <p>
            Inline code:
            <code>urljoin(base, reference)</code>
        </p>
    </section>

    <section id="links">
        <h2>Links</h2>

        <p>
            <a href="https://example.com">
                External website
            </a>
        </p>

        <p>
            <a href="/documentation">
                Internal documentation
            </a>
        </p>

        <p>
            <a href="#contact">
                Jump to contact
            </a>
        </p>
    </section>

    <section id="contact">
        <h2>Contact</h2>

        <p>
            <a href="mailto:contact@example.com">
                Email us
            </a>
        </p>

        <p>
            <a href="tel:+919876543210">
                Call us
            </a>
        </p>
    </section>
</main>

<footer>
    <a href="#top">Back to top</a>
</footer>

</body>
</html>
""".strip()

print(mini_site_html)


# ============================================================================
# 80. WRITING THE GENERATED DOCUMENT TO A FILE
# ============================================================================

print_section("80. WRITING HTML TO A FILE")

def write_html_file(
    output_path: Path,
    title: str,
    body_content: str,
) -> Path:
    """Write a generated HTML document using UTF-8."""
    document = build_html_document(title, body_content)
    output_path.write_text(document, encoding="utf-8")
    return output_path


with tempfile.TemporaryDirectory() as temporary_directory:
    output_file = Path(temporary_directory) / "html_links_example.html"
    write_html_file(
        output_file,
        "HTML Text and Links",
        body,
    )

    print("Generated file:", output_file)
    print("File exists:", output_file.exists())
    print("File size:", output_file.stat().st_size, "bytes")


# ============================================================================
# 81. TESTS
# ============================================================================

print_section("81. AUTOMATED TESTS")


class HTMLTextAndLinksTests(unittest.TestCase):
    """Tests for the educational implementations above."""

    def test_anchor_escapes_text(self) -> None:
        result = anchor(
            "/search",
            '<script>alert("x")</script>',
        )

        self.assertNotIn("<script>", result)
        self.assertIn("&lt;script&gt;", result)

    def test_anchor_escapes_attribute(self) -> None:
        result = anchor(
            'https://example.com/?q="test"',
            "Search",
        )

        self.assertIn("&quot;", result)

    def test_relative_resolution(self) -> None:
        base = "https://example.com/docs/page.html"

        self.assertEqual(
            urljoin(base, "../index.html"),
            "https://example.com/index.html",
        )

    def test_fragment_resolution(self) -> None:
        base = "https://example.com/docs/page.html"

        self.assertEqual(
            urljoin(base, "#section"),
            "https://example.com/docs/page.html#section",
        )

    def test_mailto_encoding(self) -> None:
        result = build_mailto(
            "contact@example.com",
            subject="HTML & Links",
        )

        self.assertTrue(
            result.startswith("mailto:contact@example.com?")
        )
        self.assertIn("HTML+%26+Links", result)

    def test_tel_generation(self) -> None:
        self.assertEqual(
            build_tel("+91 98765 43210"),
            "tel:+919876543210",
        )

    def test_dangerous_scheme(self) -> None:
        self.assertTrue(
            has_dangerous_scheme("javascript:alert(1)")
        )

    def test_safe_http_url(self) -> None:
        self.assertTrue(
            is_http_url("https://example.com")
        )

    def test_non_http_url(self) -> None:
        self.assertFalse(
            is_http_url("mailto:test@example.com")
        )

    def test_link_validation(self) -> None:
        result = validate_link(
            Link("https://example.com", "Example")
        )

        self.assertTrue(result.valid)
        self.assertEqual(result.errors, ())

    def test_invalid_link_validation(self) -> None:
        result = validate_link(
            Link("", "Example")
        )

        self.assertFalse(result.valid)

    def test_fragment_checker(self) -> None:
        document = """
        <a href="#existing">Existing</a>
        <a href="#missing">Missing</a>

        <section id="existing"></section>
        """

        self.assertEqual(
            find_broken_fragments(document),
            {"missing"},
        )

    def test_duplicate_ids(self) -> None:
        document = """
        <section id="same"></section>
        <section id="same"></section>
        """

        self.assertEqual(
            find_duplicate_ids(document),
            {"same"},
        )

    def test_url_policy(self) -> None:
        policy = URLPolicy()

        self.assertTrue(
            is_allowed_url("https://example.com", policy)
        )

        self.assertTrue(
            is_allowed_url("/local", policy)
        )

        self.assertFalse(
            is_allowed_url("javascript:alert(1)", policy)
        )


test_suite = unittest.defaultTestLoader.loadTestsFromTestCase(
    HTMLTextAndLinksTests
)

test_result = unittest.TextTestRunner(
    verbosity=1
).run(test_suite)

print(
    f"Tests run: {test_result.testsRun}, "
    f"failures: {len(test_result.failures)}, "
    f"errors: {len(test_result.errors)}"
)


# ============================================================================
# 82. FINAL REFERENCE EXAMPLES
# ============================================================================

print_section("82. REFERENCE: COMMON LINK PATTERNS")

common_patterns = {
    "External": '<a href="https://example.com">Example</a>',
    "Internal": '<a href="/about">About</a>',
    "Relative": '<a href="about.html">About</a>',
    "Parent": '<a href="../about.html">About</a>',
    "Fragment": '<a href="#contact">Contact</a>',
    "Cross-page fragment": (
        '<a href="/docs/api.html#authentication">'
        "Authentication"
        "</a>"
    ),
    "Email": (
        '<a href="mailto:contact@example.com">'
        "Email us"
        "</a>"
    ),
    "Telephone": (
        '<a href="tel:+919876543210">'
        "Call us"
        "</a>"
    ),
    "Download": (
        '<a href="/files/report.pdf" download>'
        "Download report"
        "</a>"
    ),
    "New context": (
        '<a href="https://example.com" '
        'target="_blank" rel="noopener noreferrer">'
        "External"
        "</a>"
    ),
}

for category, pattern in common_patterns.items():
    print(f"\n{category}:\n{pattern}")


# ============================================================================
# 83. PRACTICAL RULES
# ============================================================================

print_section("83. PRACTICAL RULES")

rules = [
    "Use headings to express document hierarchy.",
    "Use paragraphs for paragraphs rather than repeated line breaks.",
    "Use semantic formatting elements when meaning matters.",
    "Use <a> for navigation.",
    "Use <button> for actions.",
    "Use absolute URLs for explicit external destinations.",
    "Use relative URLs when the destination should follow the site's structure.",
    "Use root-relative URLs when referencing paths from the site root.",
    "Use fragments for navigation within a document.",
    "Give fragment targets unique IDs.",
    "Write descriptive link text.",
    "Encode query parameters instead of concatenating raw values.",
    "Escape dynamic HTML text and attribute values.",
    "Validate untrusted URL schemes.",
    "Treat external destinations as untrusted unless explicitly allowed.",
    "Use rel=noopener when appropriate with target=_blank.",
    "Maintain visible keyboard focus.",
    "Do not use JavaScript merely to imitate ordinary hyperlink behavior.",
    "Test generated links and fragment targets.",
    "Monitor production links for broken destinations.",
]

for index, rule in enumerate(rules, start=1):
    print(f"{index:02d}. {rule}")


# ============================================================================
# 84. EXECUTION INFORMATION
# ============================================================================

print_section("84. SCRIPT EXECUTION COMPLETE")

print(
    "This script demonstrated HTML text semantics, hyperlink structure, "
    "URL resolution, fragments, mail and telephone links, URL encoding, "
    "HTML escaping, accessibility, security, validation, testing, and "
    "programmatic HTML generation."
)
