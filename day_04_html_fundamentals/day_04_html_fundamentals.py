"""
HTML FUNDAMENTALS
=================

This Python script is an interactive academic learning module covering:

1. The purpose of HTML
2. HTML document structure
3. Elements
4. Tags
5. Attributes
6. Headings
7. Paragraphs
8. Comments

The script demonstrates HTML concepts through explanations, examples,
validation exercises, parsing demonstrations, and progressively constructed
HTML documents.

No external Python packages are required.
The script uses only Python's standard library.
"""

from html.parser import HTMLParser
from textwrap import dedent
import re


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def line(character="=", length=90):
    """Print a horizontal separator."""
    print(character * length)


def section(title):
    """Print a formatted section heading."""
    print()
    line("=")
    print(title.upper())
    line("=")
    print()


def subsection(title):
    """Print a formatted subsection heading."""
    print()
    line("-")
    print(title)
    line("-")
    print()


def show_code(code, language="HTML"):
    """Display formatted source code."""
    print(f"\n--- {language} CODE ---")
    print(code)
    print(f"--- END {language} CODE ---\n")


def show_concept(title, explanation):
    """Display an academic explanation."""
    subsection(title)
    print(dedent(explanation).strip())
    print()


# =============================================================================
# INTRODUCTION TO HTML
# =============================================================================

section("1. Introduction to HTML")


show_concept(
    "What HTML Means",
    """
    HTML stands for HyperText Markup Language.

    HTML is the standard markup language used to structure content for the web.
    It describes the meaning and organization of information contained in a web
    document. A web browser reads HTML and interprets its elements to construct
    the document that a user sees.

    HTML is not generally classified as a programming language because HTML does
    not primarily contain computational instructions such as conditional logic,
    loops, or algorithmic control flow. Instead, HTML is a markup language. Its
    primary purpose is to mark different parts of a document according to their
    meaning and structural role.

    For example:

        <h1>University Research Portal</h1>

    indicates a top-level heading.

        <p>This portal contains academic research material.</p>

    indicates a paragraph.

    The browser uses this markup to understand the intended structure of the
    document.
    """
)


show_concept(
    "The Meaning of HyperText",
    """
    The term "hypertext" refers to text that can connect to other resources.

    On the web, hyperlinks allow users to move from one document or resource to
    another. HTML provides the <a> element for creating hyperlinks.

    Example:

        <a href="https://example.com">Visit Example</a>

    The href attribute specifies the destination of the hyperlink.

    Hypertext transformed documents from isolated pieces of information into
    interconnected resources. This interconnected structure is one of the
    fundamental characteristics of the World Wide Web.
    """
)


show_concept(
    "The Purpose of HTML",
    """
    HTML provides structure and meaning to web content.

    Consider a simple academic article. The document may contain:

    - A title
    - Section headings
    - Paragraphs
    - Lists
    - Images
    - Tables
    - Links
    - Navigation areas
    - Forms

    HTML identifies these different components.

    HTML is therefore concerned primarily with questions such as:

    "What is this content?"

    rather than:

    "Exactly how should this content look?"

    For example, HTML can identify something as a paragraph:

        <p>Research findings are presented below.</p>

    CSS can later determine its visual appearance, such as font size, spacing,
    colour, alignment, and layout.

    JavaScript can add behavior and interaction.

    The three technologies therefore have distinct responsibilities:

        HTML       -> Structure and meaning
        CSS        -> Presentation and visual appearance
        JavaScript -> Behavior and interaction
    """
)


# =============================================================================
# HTML, CSS, AND JAVASCRIPT
# =============================================================================

section("2. HTML in the Context of Web Development")


comparison = """
WEB TECHNOLOGY COMPARISON

Technology      Primary Responsibility
-------------------------------------------------------------
HTML            Structure and semantic meaning
CSS             Visual presentation and layout
JavaScript      Dynamic behavior and interaction
"""

print(dedent(comparison))


show_code(
    dedent("""\
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Academic Example</title>
    </head>

    <body>
        <h1>Climate Research</h1>

        <p>
            This paragraph represents structured content created using HTML.
        </p>
    </body>
    </html>
    """)
)


print(
    dedent(
        """
        In the example above:

        HTML identifies the document title, heading, and paragraph.

        CSS could determine whether the heading is large, blue, centered, or
        displayed with a particular font.

        JavaScript could add behavior, such as displaying additional information
        when a user interacts with an element.

        HTML should therefore be understood as the structural foundation of a
        web page.
        """
    )
)


# =============================================================================
# BASIC HTML DOCUMENT STRUCTURE
# =============================================================================

section("3. HTML Document Structure")


show_concept(
    "A Complete HTML Document",
    """
    A typical modern HTML document contains a defined structural hierarchy.

    The fundamental structure is:

        <!DOCTYPE html>
        <html>
            <head>
                ...
            </head>

            <body>
                ...
            </body>
        </html>

    Each part has a specific purpose.
    """
)


html_document = dedent("""\
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HTML Fundamentals</title>
</head>

<body>
    <h1>Introduction to HTML</h1>

    <p>
        HTML provides structure and meaning to web documents.
    </p>
</body>

</html>
""")

show_code(html_document)


# =============================================================================
# DOCTYPE
# =============================================================================

section("4. The DOCTYPE Declaration")


show_concept(
    "What <!DOCTYPE html> Does",
    """
    The declaration:

        <!DOCTYPE html>

    appears at the beginning of a modern HTML document.

    It informs the browser that the document is intended to follow modern HTML
    standards.

    Although it appears similar to a tag, the DOCTYPE declaration is not an
    ordinary HTML element. It is an instruction used by the browser to determine
    how the document should be interpreted.

    Modern HTML uses the short declaration:

        <!DOCTYPE html>

    This simplicity is one of the characteristics of the current HTML standard.
    """
)


# =============================================================================
# HTML ROOT ELEMENT
# =============================================================================

section("5. The HTML Root Element")


show_concept(
    "The <html> Element",
    """
    The <html> element is the root element of an HTML document.

    Almost all document content is contained inside it.

    Example:

        <html>
            <head>
                ...
            </head>

            <body>
                ...
            </body>
        </html>

    The opening <html> tag establishes the beginning of the HTML document, and
    the closing </html> tag establishes its end.

    The html element often contains a lang attribute:

        <html lang="en">

    The lang attribute indicates the primary language of the document.

    This information can assist:

    - Search engines
    - Screen readers
    - Translation systems
    - Browser tools
    - Accessibility technologies
    """
)


# =============================================================================
# HEAD
# =============================================================================

section("6. The Head Element")


show_concept(
    "Purpose of the <head> Element",
    """
    The <head> element contains information about the document rather than the
    main content normally displayed as part of the page.

    It can contain:

    - The document title
    - Character encoding information
    - Viewport information
    - Links to CSS files
    - Metadata
    - Scripts
    - Search-related metadata

    Example:

        <head>
            <meta charset="UTF-8">
            <title>Research Portal</title>
        </head>
    """
)


show_concept(
    "The <title> Element",
    """
    The <title> element defines the title of the document.

    Example:

        <title>Introduction to HTML</title>

    The title is commonly displayed in the browser tab and can also be used by
    search engines and bookmarking systems.

    The <title> element belongs inside the <head> section rather than the main
    <body> content.
    """
)


show_concept(
    "Character Encoding",
    """
    Character encoding determines how textual characters are represented and
    interpreted.

    A common modern declaration is:

        <meta charset="UTF-8">

    UTF-8 supports a very large range of characters and languages.

    Correct character encoding is important because incorrectly interpreted
    encodings can cause text to appear corrupted or unreadable.
    """
)


# =============================================================================
# BODY
# =============================================================================

section("7. The Body Element")


show_concept(
    "Purpose of the <body> Element",
    """
    The <body> element contains the main content of the HTML document.

    Content that users normally see and interact with belongs inside the body.

    Examples include:

    - Headings
    - Paragraphs
    - Images
    - Links
    - Lists
    - Forms
    - Tables
    - Navigation

    Example:

        <body>
            <h1>Academic Research</h1>
            <p>This page contains research information.</p>
        </body>
    """
)


# =============================================================================
# ELEMENTS
# =============================================================================

section("8. HTML Elements")


show_concept(
    "What Is an HTML Element?",
    """
    An HTML element is a structural unit used to represent a particular type of
    content.

    Many HTML elements contain:

        1. An opening tag
        2. Content
        3. A closing tag

    Example:

        <p>
            This is a paragraph.
        </p>

    The complete structure is the paragraph element.

    Opening tag:

        <p>

    Content:

        This is a paragraph.

    Closing tag:

        </p>
    """
)


element_structure = """
            HTML ELEMENT STRUCTURE

        Opening Tag
             |
             v
        <p>Paragraph content</p>
                         ^
                         |
                    Closing Tag
"""

print(dedent(element_structure))


show_concept(
    "Nested Elements",
    """
    HTML elements can be placed inside other HTML elements. This is called
    nesting.

    Example:

        <p>
            This is a <strong>very important</strong> statement.
        </p>

    In this structure:

        <p>       -> Parent element
        <strong>  -> Nested child element

    The strong element exists inside the paragraph.

    Proper nesting is important. Elements should generally close in the reverse
    order in which they were opened.
    """
)


correct_nesting = dedent("""\
Correct nesting:

<p>
    This is <strong>important</strong> information.
</p>
""")

incorrect_nesting = dedent("""\
Incorrect nesting:

<p>
    This is <strong>important</p></strong>
""")

show_code(correct_nesting)
show_code(incorrect_nesting)


# =============================================================================
# TAGS
# =============================================================================

section("9. HTML Tags")


show_concept(
    "Tags and Elements Are Related but Not Identical",
    """
    The terms "tag" and "element" are often used informally as though they mean
    exactly the same thing. Technically, they describe related but different
    concepts.

    A tag is the markup syntax enclosed in angle brackets.

    Examples:

        <p>
        </p>
        <h1>
        </h1>

    An element represents the complete conceptual structure created using the
    tags and, where applicable, its content.

    Example:

        <p>HTML provides structure.</p>

    This complete unit is a paragraph element.

    The opening tag is:

        <p>

    The closing tag is:

        </p>
    """
)


show_concept(
    "Opening Tags",
    """
    An opening tag begins an element.

    Example:

        <h1>

    The tag name identifies the type of element.
    """
)


show_concept(
    "Closing Tags",
    """
    A closing tag usually marks the end of an element.

    Example:

        </h1>

    The forward slash distinguishes the closing tag from the opening tag.
    """
)


# =============================================================================
# VOID ELEMENTS
# =============================================================================

section("10. Void Elements")


show_concept(
    "Elements Without Closing Tags",
    """
    Some HTML elements do not contain content and therefore do not use a normal
    closing tag. These are commonly known as void elements.

    Examples include:

        <br>
        <hr>
        <meta>
        <img>
        <input>

    For example:

        <br>

    represents a line break.

    Since the element does not contain nested textual content between an opening
    and closing boundary, it does not require a separate closing tag.
    """
)


# =============================================================================
# ATTRIBUTES
# =============================================================================

section("11. HTML Attributes")


show_concept(
    "Purpose of Attributes",
    """
    Attributes provide additional information about an HTML element.

    Attributes are generally written inside the opening tag.

    Example:

        <a href="https://example.com">Example</a>

    In this example:

        Element: a
        Attribute: href
        Attribute value: https://example.com

    Attributes extend the information associated with an element.
    """
)


attribute_example = """
<a href="https://example.com" title="Example Website">
    Visit Example
</a>
"""

show_code(attribute_example)


show_concept(
    "Attribute Structure",
    """
    A typical attribute follows this pattern:

        attribute_name="attribute_value"

    For example:

        lang="en"

    The name identifies the property being specified.

    The value provides the specific information assigned to that property.
    """
)


show_concept(
    "Multiple Attributes",
    """
    An element can contain more than one attribute.

    Example:

        <img
            src="research.jpg"
            alt="Scientific research laboratory"
            width="600"
        >

    Each attribute provides different information.

    src   -> Resource location
    alt   -> Alternative text
    width -> Display width

    Attributes should be chosen according to the purpose and requirements of the
    particular HTML element.
    """
)


# =============================================================================
# GLOBAL ATTRIBUTES
# =============================================================================

section("12. Global Attributes")


show_concept(
    "Attributes Available Across Many Elements",
    """
    Some attributes can be applied to a wide range of HTML elements. These are
    often referred to as global attributes.

    Important examples include:

        id
        class
        title
        style
        hidden
        lang

    Example:

        <p id="introduction" class="content-section">
            HTML provides document structure.
        </p>

    The id attribute can provide an identifier.

    The class attribute can associate an element with a group or category.

    These attributes become particularly useful when CSS and JavaScript are used
    with HTML.
    """
)


# =============================================================================
# ATTRIBUTE QUOTING
# =============================================================================

section("13. Attribute Values and Quotation Marks")


show_concept(
    "Why Attribute Values Are Commonly Quoted",
    """
    Attribute values are commonly enclosed in quotation marks.

    Example:

        <p class="academic-text">

    Double quotation marks are widely used, although single quotation marks can
    also be used in valid contexts.

    Quoting attribute values improves readability and prevents ambiguity,
    particularly when attribute values contain spaces or special characters.

    Example:

        title="Introduction to HTML Fundamentals"
    """
)


# =============================================================================
# HEADINGS
# =============================================================================

section("14. HTML Headings")


show_concept(
    "Heading Elements",
    """
    HTML provides six heading levels:

        <h1>
        <h2>
        <h3>
        <h4>
        <h5>
        <h6>

    These represent a hierarchy of importance.

    <h1> is generally the highest-level heading.

    <h6> is the lowest heading level.
    """
)


headings_example = dedent("""\
<h1>Main Document Title</h1>

<h2>Chapter One</h2>

<h3>Section One</h3>

<h4>Subsection</h4>

<h5>Detailed Topic</h5>

<h6>Minor Classification</h6>
""")

show_code(headings_example)


show_concept(
    "Heading Hierarchy",
    """
    Headings should represent the logical structure of a document.

    Consider an academic document:

        <h1>Artificial Intelligence</h1>

            <h2>Machine Learning</h2>

                <h3>Supervised Learning</h3>

                <h3>Unsupervised Learning</h3>

            <h2>Deep Learning</h2>

    This structure communicates the relationship between sections.

    Heading levels should therefore be selected based on document hierarchy
    rather than purely on visual size.

    CSS should be used when visual size needs to be changed.
    """
)


hierarchy_example = dedent("""\
<h1>Computer Science</h1>

<h2>Programming</h2>

<h3>Python</h3>
<p>Python is widely used for software development and data analysis.</p>

<h3>JavaScript</h3>
<p>JavaScript is widely used for web development.</p>

<h2>Data Structures</h2>

<h3>Arrays</h3>
<p>Arrays store collections of values.</p>
""")

show_code(hierarchy_example)


# =============================================================================
# PARAGRAPHS
# =============================================================================

section("15. HTML Paragraphs")


show_concept(
    "The <p> Element",
    """
    The paragraph element represents a paragraph of textual content.

    Syntax:

        <p>
            Paragraph content goes here.
        </p>

    Example:

        <p>
            HTML provides the structural foundation for web documents.
        </p>

    Browsers generally display paragraphs as separate blocks of text with
    spacing between them, although the precise visual appearance can be modified
    using CSS.
    """
)


paragraph_example = dedent("""\
<p>
    HTML is a markup language used to structure web content.
</p>

<p>
    CSS is used to control presentation and layout.
</p>

<p>
    JavaScript is used to introduce dynamic behavior and interaction.
</p>
""")

show_code(paragraph_example)


show_concept(
    "Paragraphs and Meaning",
    """
    Paragraph elements should represent genuine paragraphs of related content.

    HTML should not use the paragraph element merely as a generic spacing tool.

    For example, this is structurally meaningful:

        <p>
            The experiment produced consistent results across multiple tests.
        </p>

    The paragraph communicates that the enclosed text forms a coherent unit of
    written content.

    Spacing and layout should normally be controlled using CSS rather than by
    inserting unnecessary HTML elements.
    """
)


# =============================================================================
# WHITESPACE
# =============================================================================

section("16. Whitespace in HTML")


show_concept(
    "How Browsers Treat Ordinary Whitespace",
    """
    HTML source code may contain spaces, tabs, and line breaks for readability.

    For example:

        <p>
            HTML
            provides
            structure.
        </p>

    In normal HTML rendering, browsers generally collapse sequences of ordinary
    whitespace into a smaller amount of displayed whitespace.

    Therefore, the source code can be formatted for human readability without
    necessarily creating the same number of visible spaces and line breaks in
    the browser.
    """
)


show_code(
    dedent("""\
    <p>
        This source code contains
        multiple lines and spaces,
        but ordinary HTML whitespace
        is generally collapsed during rendering.
    </p>
    """)
)


# =============================================================================
# HTML COMMENTS
# =============================================================================

section("17. HTML Comments")


show_concept(
    "Purpose of Comments",
    """
    HTML comments allow developers to place notes inside source code.

    Standard HTML comment syntax is:

        <!-- Comment text -->

    Example:

        <!-- Main page heading -->

        <h1>Research Portal</h1>

    Comments are intended primarily for people reading or maintaining the source
    code. They are not normally rendered as visible content on the page.
    """
)


comments_example = dedent("""\
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <title>Comments Example</title>
</head>

<body>

    <!-- Main page heading -->
    <h1>HTML Fundamentals</h1>

    <!-- Introduction section -->
    <p>
        This paragraph introduces the purpose of HTML.
    </p>

    <!-- End of introductory content -->

</body>

</html>
""")

show_code(comments_example)


show_concept(
    "Appropriate Use of Comments",
    """
    Comments are useful when they provide meaningful information that improves
    code understanding.

    Appropriate examples include:

    - Identifying major sections of a large document
    - Explaining non-obvious structural decisions
    - Temporarily documenting unfinished development work
    - Providing maintenance information where necessary

    Comments should not be used to explain every obvious line of HTML.

    Excessive comments can make source code difficult to read, just as missing
    documentation can make complex code difficult to maintain.
    """
)


show_concept(
    "Comments Are Not a Security Mechanism",
    """
    HTML comments are part of the document source.

    Users can often inspect the HTML source received by their browser.

    Therefore, sensitive information should never be stored in HTML comments.

    Information such as passwords, private keys, confidential database
    credentials, or security mechanisms must not be considered protected merely
    because they are placed inside a comment.
    """
)


# =============================================================================
# COMPLETE DOCUMENT CONSTRUCTION
# =============================================================================

section("18. Constructing an HTML Document Step by Step")


print("STEP 1: Begin with the DOCTYPE declaration.\n")

step_1 = "<!DOCTYPE html>"
show_code(step_1)


print("STEP 2: Add the HTML root element.\n")

step_2 = dedent("""\
<!DOCTYPE html>
<html lang="en">

</html>
""")

show_code(step_2)


print("STEP 3: Add the head and body sections.\n")

step_3 = dedent("""\
<!DOCTYPE html>
<html lang="en">

<head>

</head>

<body>

</body>

</html>
""")

show_code(step_3)


print("STEP 4: Add document metadata and a title.\n")

step_4 = dedent("""\
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <title>HTML Fundamentals</title>
</head>

<body>

</body>

</html>
""")

show_code(step_4)


print("STEP 5: Add structured content.\n")

step_5 = dedent("""\
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <title>HTML Fundamentals</title>
</head>

<body>

    <h1>HTML Fundamentals</h1>

    <h2>Purpose of HTML</h2>

    <p>
        HTML provides structure and semantic meaning to web content.
    </p>

</body>

</html>
""")

show_code(step_5)


# =============================================================================
# ACADEMIC EXAMPLE
# =============================================================================

section("19. Academic HTML Document Example")


academic_document = dedent("""\
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <!-- Document title displayed by the browser -->
    <title>Introduction to HTML Fundamentals</title>
</head>

<body>

    <!-- Main document heading -->
    <h1>Introduction to HTML</h1>

    <p>
        HTML is a markup language used to structure information for the World
        Wide Web.
    </p>

    <h2>The Purpose of HTML</h2>

    <p>
        HTML identifies the structural role and meaning of content within a web
        document. It can represent headings, paragraphs, links, images, lists,
        forms, and many other types of content.
    </p>

    <h2>HTML Document Structure</h2>

    <p>
        A standard HTML document contains a document declaration, an HTML root
        element, metadata within the head section, and visible document content
        within the body section.
    </p>

    <h3>Elements and Tags</h3>

    <p>
        HTML elements are constructed using markup tags and may contain text,
        other elements, and additional information through attributes.
    </p>

    <h3>Attributes</h3>

    <p id="attributes-section">
        Attributes provide additional information about an HTML element.
    </p>

    <!-- End of document content -->

</body>

</html>
""")

show_code(academic_document)


# =============================================================================
# HTML PARSER DEMONSTRATION
# =============================================================================

section("20. Understanding HTML Through Python Parsing")


show_concept(
    "Why Parse HTML?",
    """
    A browser must interpret HTML markup to understand the structure of a
    document.

    Python provides tools that can inspect HTML programmatically.

    The html.parser module from Python's standard library can identify:

    - Opening tags
    - Closing tags
    - Attributes
    - Text data
    - Comments

    The following parser demonstrates these concepts.
    """
)


class EducationalHTMLParser(HTMLParser):
    """
    A custom parser that prints the structural components encountered while
    processing an HTML document.
    """

    def handle_starttag(self, tag, attrs):
        print(f"OPENING TAG: <{tag}>")

        if attrs:
            print("ATTRIBUTES:")

            for name, value in attrs:
                print(f"    {name} = {value}")

    def handle_endtag(self, tag):
        print(f"CLOSING TAG: </{tag}>")

    def handle_data(self, data):
        cleaned_data = data.strip()

        if cleaned_data:
            print(f"TEXT CONTENT: {cleaned_data}")

    def handle_comment(self, data):
        print(f"COMMENT: {data.strip()}")


parser_demo = dedent("""\
<!-- Educational demonstration -->
<h1 id="main-title">HTML Fundamentals</h1>
<p>HTML provides structure.</p>
""")

print("HTML SOURCE TO BE PARSED:")
show_code(parser_demo)

print("PARSER OUTPUT:\n")

parser = EducationalHTMLParser()
parser.feed(parser_demo)


# =============================================================================
# ANALYZING HTML TAGS
# =============================================================================

section("21. Programmatic Identification of HTML Tags")


html_sample = dedent("""\
<!DOCTYPE html>
<html>
<head>
    <title>Sample</title>
</head>
<body>
    <h1>Main Heading</h1>
    <p>First paragraph.</p>
    <p>Second paragraph.</p>
</body>
</html>
""")

show_code(html_sample)


tag_pattern = r"</?([a-zA-Z][a-zA-Z0-9-]*)[^>]*>"

tags_found = re.findall(tag_pattern, html_sample)

print("TAG NAMES IDENTIFIED:")
print()

for index, tag_name in enumerate(tags_found, start=1):
    print(f"{index}. {tag_name}")


unique_tags = sorted(set(tags_found))

print("\nUNIQUE TAG TYPES:")
print()

for tag_name in unique_tags:
    print(f"- {tag_name}")


# =============================================================================
# ELEMENT CLASSIFICATION
# =============================================================================

section("22. Structural Classification of HTML Components")


classification = {
    "Document Declaration": "<!DOCTYPE html>",
    "Root Element": "<html>",
    "Metadata Container": "<head>",
    "Document Title": "<title>",
    "Main Content Container": "<body>",
    "Primary Heading": "<h1>",
    "Secondary Heading": "<h2>",
    "Paragraph": "<p>",
    "Comment": "<!-- ... -->",
}

for category, example in classification.items():
    print(f"{category:<25} -> {example}")


# =============================================================================
# ATTRIBUTE EXTRACTION
# =============================================================================

section("23. Programmatic Extraction of Attributes")


attribute_html = dedent("""\
<a
    href="https://example.com"
    title="Example Website"
    class="external-link"
>
    Visit Example
</a>
""")

show_code(attribute_html)


class AttributeExtractor(HTMLParser):
    """Extract attributes from HTML elements."""

    def handle_starttag(self, tag, attrs):
        print(f"ELEMENT: <{tag}>")

        for attribute_name, attribute_value in attrs:
            print(
                f"    Attribute: {attribute_name}"
                f" | Value: {attribute_value}"
            )


extractor = AttributeExtractor()
extractor.feed(attribute_html)


# =============================================================================
# HEADING HIERARCHY ANALYSIS
# =============================================================================

section("24. Analyzing Heading Hierarchy")


heading_document = dedent("""\
<h1>Computer Science</h1>

<h2>Programming Languages</h2>

<h3>Python</h3>
<p>Python is a high-level programming language.</p>

<h3>JavaScript</h3>
<p>JavaScript is commonly used for web development.</p>

<h2>Algorithms</h2>

<h3>Sorting</h3>

<h3>Searching</h3>
""")

show_code(heading_document)


class HeadingAnalyzer(HTMLParser):
    """Identify headings and their hierarchical levels."""

    def __init__(self):
        super().__init__()
        self.current_heading = None

    def handle_starttag(self, tag, attrs):
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self.current_heading = tag

    def handle_data(self, data):
        if self.current_heading:
            text = data.strip()

            if text:
                level = int(self.current_heading[1])
                indentation = "    " * (level - 1)

                print(
                    f"{indentation}"
                    f"Level {level}: {text}"
                )

    def handle_endtag(self, tag):
        if tag == self.current_heading:
            self.current_heading = None


print("HEADING STRUCTURE:\n")

heading_analyzer = HeadingAnalyzer()
heading_analyzer.feed(heading_document)


# =============================================================================
# VALIDATION CONCEPTS
# =============================================================================

section("25. Basic HTML Validation Concepts")


show_concept(
    "Why Structural Correctness Matters",
    """
    HTML documents should follow valid structural conventions.

    Common structural problems include:

    - Missing closing tags where closing tags are required
    - Incorrectly nested elements
    - Misspelled attribute names
    - Incorrect document hierarchy
    - Duplicate identifiers where unique identifiers are required
    - Using elements for purposes unrelated to their meaning

    Browsers are often designed to recover from malformed HTML. This does not
    mean malformed HTML should be considered good practice.

    A document may appear acceptable in one browser while still containing
    structural problems that affect:

    - Accessibility
    - Maintainability
    - Browser consistency
    - Search interpretation
    - Programmatic processing
    """
)


# =============================================================================
# SIMPLE STACK-BASED TAG CHECKER
# =============================================================================

section("26. Simplified Tag Balance Analysis")


def check_tag_balance(html):
    """
    Perform a simplified analysis of opening and closing tags.

    This is an educational demonstration rather than a complete HTML validator.
    HTML contains rules and special cases that require more sophisticated parsing.
    """

    void_elements = {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }

    token_pattern = r"<(/?)([a-zA-Z][a-zA-Z0-9-]*)[^>]*>"

    tokens = re.findall(token_pattern, html)

    stack = []
    errors = []

    for slash, tag in tokens:

        tag = tag.lower()

        if tag in void_elements:
            continue

        if slash == "":
            stack.append(tag)

        else:

            if not stack:
                errors.append(
                    f"Closing tag </{tag}> has no corresponding opening tag."
                )

            elif stack[-1] != tag:
                errors.append(
                    f"Expected closing tag </{stack[-1]}> "
                    f"but found </{tag}>."
                )

            else:
                stack.pop()

    while stack:
        unclosed = stack.pop()
        errors.append(
            f"Opening tag <{unclosed}> has no corresponding closing tag."
        )

    return errors


valid_html = dedent("""\
<div>
    <p>
        Properly structured paragraph.
    </p>
</div>
""")

invalid_html = dedent("""\
<div>
    <p>
        Incorrectly structured paragraph.
</div>
""")

print("VALID STRUCTURE EXAMPLE:")
show_code(valid_html)

valid_errors = check_tag_balance(valid_html)

if not valid_errors:
    print("No structural imbalance detected by the simplified checker.\n")
else:
    for error in valid_errors:
        print(error)


print("INVALID STRUCTURE EXAMPLE:")
show_code(invalid_html)

invalid_errors = check_tag_balance(invalid_html)

for error in invalid_errors:
    print(f"STRUCTURAL ISSUE: {error}")


# =============================================================================
# BUILDING HTML WITH PYTHON
# =============================================================================

section("27. Generating HTML Using Python")


show_concept(
    "HTML as Text Generated by a Program",
    """
    HTML files are textual documents. Python can therefore generate HTML by
    constructing strings and writing them into files.

    This is useful for educational demonstrations, reporting systems, static
    site generation, templating systems, and automated document creation.
    """
)


def create_html_document(title, main_heading, paragraphs):
    """
    Create a basic HTML document from Python values.
    """

    paragraph_html = "\n".join(
        f"    <p>{paragraph}</p>"
        for paragraph in paragraphs
    )

    document = f"""<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <title>{title}</title>
</head>

<body>

    <h1>{main_heading}</h1>

{paragraph_html}

</body>

</html>
"""

    return document


generated_html = create_html_document(
    title="Python Generated HTML",
    main_heading="HTML Generated Through Python",
    paragraphs=[
        "HTML documents can be created programmatically.",
        "Python can construct structured HTML text.",
        "The generated output can be written to an HTML file.",
    ],
)

show_code(generated_html)


# =============================================================================
# WRITING HTML TO A FILE
# =============================================================================

section("28. Writing HTML to a File")


show_concept(
    "Creating a Physical HTML File",
    """
    Python can write generated HTML content to a file with the .html extension.

    When the file is opened by a web browser, the browser interprets the HTML
    structure and renders the document.

    The following operation creates a file named:

        html_fundamentals_example.html
    """
)


filename = "html_fundamentals_example.html"

with open(filename, "w", encoding="utf-8") as file:
    file.write(generated_html)

print(f"HTML file created successfully: {filename}")


# =============================================================================
# SEMANTIC THINKING
# =============================================================================

section("29. Structural and Semantic Thinking in HTML")


show_concept(
    "Choosing Elements According to Meaning",
    """
    Effective HTML is not merely a collection of visual containers.

    HTML elements should be selected according to the meaning and role of the
    content.

    A heading should normally be represented using a heading element.

    A paragraph should normally be represented using a paragraph element.

    This structural approach provides several benefits.

    Accessibility technologies can interpret the document more effectively.

    Search engines can understand document structure.

    Developers can maintain the document more easily.

    CSS can target meaningful structural components.

    JavaScript can interact with logically identified elements.
    """
)


semantic_example = dedent("""\
<h1>Research Findings</h1>

<h2>Methodology</h2>

<p>
    The study used structured data collection methods.
</p>

<h2>Results</h2>

<p>
    The analysis identified significant patterns in the collected data.
</p>
""")

show_code(semantic_example)


# =============================================================================
# CASE SENSITIVITY AND MODERN CONVENTIONS
# =============================================================================

section("30. Modern HTML Writing Conventions")


show_concept(
    "Lowercase Element and Attribute Names",
    """
    Modern HTML code is commonly written using lowercase element names and
    attribute names.

    Example:

        <p class="content">

    Lowercase markup improves consistency and readability.

    Maintaining a consistent writing style is important when documents become
    larger and are developed by multiple people.
    """
)


show_concept(
    "Indentation",
    """
    Indentation does not normally define the semantic hierarchy of HTML.

    The actual hierarchy is determined by element nesting.

    Nevertheless, indentation is important for human readability.

    Example:

        <body>
            <section>
                <h1>Heading</h1>
                <p>Paragraph</p>
            </section>
        </body>

    The indentation visually represents the structural relationship between
    elements.
    """
)


# =============================================================================
# COMPLETE INTEGRATED EXAMPLE
# =============================================================================

section("31. Complete Integrated Example")


integrated_example = dedent("""\
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <!-- The browser uses this title for the document tab -->
    <title>HTML Fundamentals Academic Document</title>
</head>

<body>

    <!-- Main document title -->
    <h1>HTML Fundamentals</h1>

    <p>
        HTML is a markup language used to structure and describe information
        presented through web documents.
    </p>

    <h2>Document Structure</h2>

    <p>
        A standard HTML document contains a DOCTYPE declaration, an HTML root
        element, a head section containing metadata, and a body section
        containing the main document content.
    </p>

    <h2>Elements and Tags</h2>

    <p>
        HTML elements define structural components. Most elements use opening
        and closing tags surrounding their content.
    </p>

    <h3>Attributes</h3>

    <p id="attributes" class="important-content">
        Attributes provide additional information about elements and are usually
        written within opening tags.
    </p>

    <h2>Headings and Paragraphs</h2>

    <h3>Heading Hierarchy</h3>

    <p>
        HTML provides six heading levels, ranging from h1 through h6, allowing
        documents to represent logical structural hierarchy.
    </p>

    <h3>Paragraph Content</h3>

    <p>
        Paragraph elements represent coherent units of written content and
        contribute to the meaningful organization of a document.
    </p>

    <!-- Document content ends here -->

</body>

</html>
""")

show_code(integrated_example)


# =============================================================================
# CONCEPT REFERENCE
# =============================================================================

section("32. HTML Fundamentals Concept Reference")


concept_reference = {
    "HTML": (
        "A markup language used to structure and describe web content."
    ),
    "DOCTYPE": (
        "A declaration indicating that the document follows modern HTML standards."
    ),
    "html element": (
        "The root element containing the main HTML document structure."
    ),
    "head element": (
        "A container for document metadata and related information."
    ),
    "body element": (
        "A container for the main content displayed as part of the document."
    ),
    "element": (
        "A structural HTML component representing a type of content."
    ),
    "opening tag": (
        "Markup that begins an element."
    ),
    "closing tag": (
        "Markup that marks the end of many HTML elements."
    ),
    "attribute": (
        "Additional information associated with an HTML element."
    ),
    "heading": (
        "A structural title represented by h1 through h6."
    ),
    "paragraph": (
        "A coherent unit of textual content represented by the p element."
    ),
    "comment": (
        "A source-code note written using <!-- and --> syntax."
    ),
}


for concept, definition in concept_reference.items():
    print(f"{concept.upper()}")
    print(f"    {definition}\n")


# =============================================================================
# PRACTICAL STRUCTURE INSPECTION
# =============================================================================

section("33. Inspecting a Complete HTML Document")


inspection_html = dedent("""\
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <title>Document Inspection</title>
</head>

<body>

    <!-- Introduction -->
    <h1 id="document-title">Document Structure</h1>

    <p class="introduction">
        This paragraph demonstrates the relationship between HTML elements,
        attributes, headings, paragraphs, and comments.
    </p>

</body>

</html>
""")

show_code(inspection_html)


class CompleteInspector(HTMLParser):
    """
    Inspect HTML and count structural components.
    """

    def __init__(self):
        super().__init__()

        self.start_tags = 0
        self.end_tags = 0
        self.comments = 0
        self.text_nodes = 0
        self.attributes = 0

    def handle_starttag(self, tag, attrs):
        self.start_tags += 1
        self.attributes += len(attrs)

    def handle_endtag(self, tag):
        self.end_tags += 1

    def handle_comment(self, data):
        self.comments += 1

    def handle_data(self, data):
        if data.strip():
            self.text_nodes += 1


inspector = CompleteInspector()
inspector.feed(inspection_html)

print("DOCUMENT INSPECTION RESULTS:\n")

print(f"Opening tags encountered : {inspector.start_tags}")
print(f"Closing tags encountered : {inspector.end_tags}")
print(f"Comments encountered     : {inspector.comments}")
print(f"Text nodes encountered   : {inspector.text_nodes}")
print(f"Attributes encountered   : {inspector.attributes}")


# =============================================================================
# FINAL DOCUMENT MODEL
# =============================================================================

section("34. Conceptual Model of an HTML Document")


document_model = """
HTML DOCUMENT
|
|-- <!DOCTYPE html>
|
|-- <html>
    |
    |-- <head>
    |   |
    |   |-- <meta>
    |   |
    |   |-- <title>
    |
    |-- <body>
        |
        |-- <h1>
        |
        |-- <p>
        |
        |-- <h2>
        |
        |-- <p>
        |
        |-- <!-- Comment -->
"""

print(dedent(document_model))


print("\nHTML Fundamentals learning module completed.\n")
