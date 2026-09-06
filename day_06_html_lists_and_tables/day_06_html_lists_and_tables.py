"""
HTML Lists and Tables
=====================

A standalone, executable study script covering HTML lists and tables from
absolute beginner through advanced practical usage.

Topics covered:
- Ordered lists (<ol>)
- Unordered lists (<ul>)
- List items (<li>)
- Ordered-list numbering types, start, reversed, and value
- Nested lists
- Definition/description lists (<dl>, <dt>, <dd>)
- Tables (<table>)
- Table rows (<tr>)
- Table header/data cells (<th>, <td>)
- Captions (<caption>)
- thead, tbody, tfoot
- rowspan and colspan
- scope and accessibility
- headers and id for complex tables
- colgroup and col
- table semantics
- complete table examples
- validation and escaping
- programmatic HTML generation
- common mistakes
- edge cases
- security considerations
- maintainability and production practices
- testing and debugging
- comparison examples
"""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from typing import Iterable, Sequence
import re


# ============================================================================
# 1. FUNDAMENTAL HTML CONCEPTS
# ============================================================================

def section(title: str) -> None:
    """Print a clearly separated educational section."""
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def show_example(title: str, html: str) -> None:
    """Display an example without requiring an HTML file or browser."""
    print(f"\n--- {title} ---")
    print(html)


section("1. HTML LISTS AND TABLES: FUNDAMENTALS")

print("""
HTML (HyperText Markup Language) represents the structure and meaning of
content.

Lists represent collections of related items.

Tables represent structured data arranged into rows and columns.

The central distinction is semantic:

    <ul> / <ol> / <dl>  -> collections of related content
    <table>              -> tabular data

A table should not normally be used merely to position unrelated content.
CSS layout systems such as Flexbox and Grid are intended for page layout.

Important list elements:

    <ol>  Ordered list
    <ul>  Unordered list
    <li>  List item
    <dl>  Description/definition list
    <dt>  Description-list term
    <dd>  Description-list description

Important table elements:

    <table>    Table container
    <caption>  Table title/caption
    <tr>       Table row
    <th>       Header cell
    <td>       Data cell
    <thead>    Header-row group
    <tbody>    Body-row group
    <tfoot>    Footer/summary-row group
    <colgroup> Column grouping
    <col>      Column metadata
""")


# ============================================================================
# 2. UNORDERED LISTS
# ============================================================================

section("2. UNORDERED LISTS")

unordered_list = """
<ul>
    <li>Python</li>
    <li>JavaScript</li>
    <li>SQL</li>
</ul>
"""

show_example("Basic unordered list", unordered_list)

print("""
An unordered list is appropriate when the order of the items is not
intrinsically meaningful.

The <ul> element is the container.
Each direct list item is normally represented by <li>.

The browser normally renders unordered-list items with bullets, but the
visual marker is a presentation choice. CSS can change the appearance.

Semantic meaning comes from <ul>, not from the bullet character.
""")

show_example(
    "Unordered list with meaningful content",
    """<ul>
    <li>Install the application.</li>
    <li>Create an account.</li>
    <li>Configure the profile.</li>
</ul>"""
)

print("""
Important rule:

Do not manually create a list by placing bullet characters such as "•" in
ordinary paragraphs when the content is semantically a list.

Prefer:

    <ul>
        <li>Item</li>
    </ul>

rather than:

    <p>• Item</p>
    <p>• Item</p>
""")


# ============================================================================
# 3. ORDERED LISTS
# ============================================================================

section("3. ORDERED LISTS")

ordered_list = """
<ol>
    <li>Collect requirements.</li>
    <li>Design the solution.</li>
    <li>Implement the solution.</li>
    <li>Test the solution.</li>
</ol>
"""

show_example("Basic ordered list", ordered_list)

print("""
An ordered list is appropriate when sequence, ranking, procedure, or another
meaningful order matters.

Typical uses:
- step-by-step procedures
- instructions
- rankings
- chronological sequences
- priority-ordered items
""")


# ============================================================================
# 4. ORDERED-LIST ATTRIBUTES
# ============================================================================

section("4. ORDERED-LIST ATTRIBUTES")

print("""
Important <ol> attributes include:

type
----
Controls the numbering style.

Common values:
    1    Decimal numbers
    A    Uppercase letters
    a    Lowercase letters
    I    Uppercase Roman numerals
    i    Lowercase Roman numerals

start
-----
Specifies the starting number for an ordered list.

reversed
--------
Makes the list count downward.

The <li> element has a value attribute that can explicitly set the number
associated with an individual item in an ordered list.
""")

show_example(
    "Different numbering styles",
    """<ol type="A">
    <li>First category</li>
    <li>Second category</li>
    <li>Third category</li>
</ol>

<ol type="i">
    <li>Introduction</li>
    <li>Method</li>
    <li>Results</li>
</ol>"""
)

show_example(
    "Starting from a specific number",
    """<ol start="5">
    <li>Fifth item</li>
    <li>Sixth item</li>
    <li>Seventh item</li>
</ol>"""
)

show_example(
    "Descending order",
    """<ol reversed>
    <li>Third</li>
    <li>Second</li>
    <li>First</li>
</ol>"""
)

show_example(
    "Explicit list-item value",
    """<ol>
    <li>Chapter One</li>
    <li value="5">Chapter Five</li>
    <li>Chapter Six</li>
</ol>"""
)

print("""
Important subtlety:

The numeric value represented by an ordered-list item and its visual marker
are related, but the marker should not be treated as ordinary text.

Use the semantic HTML attributes when the numbering itself has meaning.
""")


# ============================================================================
# 5. NESTED LISTS
# ============================================================================

section("5. NESTED LISTS")

nested_list = """
<ul>
    <li>Programming
        <ul>
            <li>Python</li>
            <li>JavaScript</li>
            <li>C++</li>
        </ul>
    </li>
    <li>Databases
        <ul>
            <li>PostgreSQL</li>
            <li>MySQL</li>
        </ul>
    </li>
</ul>
"""

show_example("Nested unordered lists", nested_list)

print("""
A nested list is a list placed inside a list item.

The important structural relationship is:

    <ul>
        <li>
            Parent item
            <ul>
                <li>Child item</li>
            </ul>
        </li>
    </ul>

The nested <ul> belongs to the parent <li>.

A common structural mistake is to put a nested list directly inside <ul>
without a containing <li>.
""")

show_example(
    "Nested ordered and unordered lists",
    """<ol>
    <li>Planning
        <ul>
            <li>Requirements</li>
            <li>Scope</li>
        </ul>
    </li>
    <li>Execution
        <ol>
            <li>Development</li>
            <li>Testing</li>
        </ol>
    </li>
</ol>"""
)


# ============================================================================
# 6. DEFINITION / DESCRIPTION LISTS
# ============================================================================

section("6. DESCRIPTION LISTS")

description_list = """
<dl>
    <dt>HTML</dt>
    <dd>Markup language used to structure web documents.</dd>

    <dt>CSS</dt>
    <dd>Language used to describe presentation and visual styling.</dd>

    <dt>HTTP</dt>
    <dd>Protocol used for communication between clients and servers.</dd>
</dl>
"""

show_example("Basic description list", description_list)

print("""
A <dl> is useful for groups of terms and associated descriptions.

    <dl> -> description list
    <dt> -> term
    <dd> -> description/details

The relationship does not have to be a dictionary definition. It can
represent labels and corresponding descriptions.

A term can have multiple descriptions, and a description can be associated
with multiple terms when the content structure calls for it.
""")

show_example(
    "Multiple descriptions for a term",
    """<dl>
    <dt>HTML</dt>
    <dd>Markup language.</dd>
    <dd>Defines document structure.</dd>
</dl>"""
)

show_example(
    "Multiple terms associated with one description",
    """<dl>
    <dt>HTTP</dt>
    <dt>HTTPS</dt>
    <dd>Protocols used for transferring web resources.</dd>
</dl>"""
)

print("""
Do not use <dl> simply because its visual appearance resembles a two-column
layout. Its semantic meaning should match the content relationship.
""")


# ============================================================================
# 7. BASIC TABLES
# ============================================================================

section("7. TABLE FUNDAMENTALS")

basic_table = """
<table>
    <tr>
        <th>Name</th>
        <th>Department</th>
        <th>Score</th>
    </tr>
    <tr>
        <td>Asha</td>
        <td>Data</td>
        <td>91</td>
    </tr>
    <tr>
        <td>Rahul</td>
        <td>Security</td>
        <td>87</td>
    </tr>
</table>
"""

show_example("Basic table", basic_table)

print("""
A table consists conceptually of:

    Table
      |
      +-- Row
      |    +-- Header cell
      |    +-- Header cell
      |
      +-- Row
           +-- Data cell
           +-- Data cell

<tr> represents a row.

<th> represents a header cell.

<td> represents an ordinary data cell.

The browser determines the table structure from the markup, not from the
visual alignment of the text.
""")


# ============================================================================
# 8. TABLE CAPTIONS
# ============================================================================

section("8. TABLE CAPTIONS")

caption_example = """
<table>
    <caption>Employee Performance Scores</caption>
    <tr>
        <th>Name</th>
        <th>Score</th>
    </tr>
    <tr>
        <td>Asha</td>
        <td>91</td>
    </tr>
</table>
"""

show_example("Table with caption", caption_example)

print("""
<caption> gives a table its caption or title.

It should normally appear as a child of <table>, commonly before table-row
groups.

A caption is more meaningful than using a random paragraph above the table
when the text specifically labels the table.

Captions can be useful for accessibility and document comprehension.
""")


# ============================================================================
# 9. THEAD, TBODY, TFOOT
# ============================================================================

section("9. TABLE ROW GROUPS")

structured_table = """
<table>
    <caption>Quarterly Revenue</caption>

    <thead>
        <tr>
            <th scope="col">Quarter</th>
            <th scope="col">Revenue</th>
        </tr>
    </thead>

    <tbody>
        <tr>
            <td>Q1</td>
            <td>120000</td>
        </tr>
        <tr>
            <td>Q2</td>
            <td>145000</td>
        </tr>
    </tbody>

    <tfoot>
        <tr>
            <th scope="row">Total</th>
            <td>265000</td>
        </tr>
    </tfoot>
</table>
"""

show_example("Structured table", structured_table)

print("""
<thead> groups header rows.

<tbody> groups the primary body rows.

<tfoot> groups footer or summary rows.

These elements improve semantic organization and can make complex tables
easier to understand and style.

A table may have multiple <tbody> elements when the data naturally divides
into row groups.

The browser may also insert a <tbody> into the DOM when one is omitted,
which can matter when manipulating tables programmatically.
""")


# ============================================================================
# 10. HEADER CELLS AND SCOPE
# ============================================================================

section("10. TABLE HEADERS AND ACCESSIBILITY")

print("""
<th> indicates a header cell.

scope helps communicate what a header describes.

Common scope values:

    scope="col"   -> header describes a column
    scope="row"   -> header describes a row

For a simple table, this is a strong pattern:

    <th scope="col">Name</th>
    <th scope="col">Score</th>

For a row label:

    <th scope="row">Q1</th>

This is semantic information, not merely visual styling.
""")

show_example(
    "Column headers",
    """<table>
    <tr>
        <th scope="col">Product</th>
        <th scope="col">Price</th>
        <th scope="col">Stock</th>
    </tr>
</table>"""
)

show_example(
    "Row header",
    """<table>
    <tr>
        <th scope="row">Monday</th>
        <td>25°C</td>
    </tr>
</table>"""
)


# ============================================================================
# 11. ROWSPAN
# ============================================================================

section("11. ROWSPAN")

rowspan_example = """
<table>
    <caption>Project Assignments</caption>
    <tr>
        <th scope="col">Team</th>
        <th scope="col">Member</th>
        <th scope="col">Role</th>
    </tr>
    <tr>
        <th scope="rowgroup" rowspan="2">Data</th>
        <td>Asha</td>
        <td>Analyst</td>
    </tr>
    <tr>
        <td>Ravi</td>
        <td>Engineer</td>
    </tr>
</table>
"""

show_example("rowspan example", rowspan_example)

print("""
rowspan makes a cell occupy multiple rows.

For example:

    rowspan="2"

means that the cell spans two rows vertically.

When a cell spans rows, the following rows must contain fewer cells because
the spanning cell already occupies a position in those rows.

This is a frequent source of table-structure errors.
""")


# ============================================================================
# 12. COLSPAN
# ============================================================================

section("12. COLSPAN")

colspan_example = """
<table>
    <tr>
        <th colspan="3">Employee Performance</th>
    </tr>
    <tr>
        <th>Name</th>
        <th>Department</th>
        <th>Score</th>
    </tr>
</table>
"""

show_example("colspan example", colspan_example)

print("""
colspan makes a cell occupy multiple columns.

    colspan="3"

means the cell spans three columns horizontally.

It is useful for:
- grouped headings
- section labels
- totals
- multi-column summaries
""")


# ============================================================================
# 13. COMBINING ROWSPAN AND COLSPAN
# ============================================================================

section("13. COMBINING ROWSPAN AND COLSPAN")

complex_span_table = """
<table>
    <caption>Training Results</caption>
    <thead>
        <tr>
            <th rowspan="2" scope="col">Name</th>
            <th colspan="2">Training</th>
            <th rowspan="2" scope="col">Final Score</th>
        </tr>
        <tr>
            <th scope="col">Theory</th>
            <th scope="col">Practical</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <th scope="row">Asha</th>
            <td>88</td>
            <td>94</td>
            <td>91</td>
        </tr>
    </tbody>
</table>
"""

show_example("Combined rowspan and colspan", complex_span_table)

print("""
When rowspan and colspan are combined, table structure must be calculated
carefully.

For each row, the number of occupied columns must remain consistent with the
intended table grid.

The following conceptual grid has four columns:

    Name | Training | Training | Final Score
         | Theory   | Practical |

The first "Training" header spans two columns.
The Name and Final Score headers span two rows.
""")


# ============================================================================
# 14. COMPLEX TABLES AND HEADERS/ID
# ============================================================================

section("14. COMPLEX TABLE ACCESSIBILITY")

complex_accessibility = """
<table>
    <caption>Regional Sales</caption>
    <thead>
        <tr>
            <th id="region" scope="col">Region</th>
            <th id="q1" scope="col">Q1</th>
            <th id="q2" scope="col">Q2</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <th id="north" scope="row">North</th>
            <td headers="north q1">120</td>
            <td headers="north q2">135</td>
        </tr>
        <tr>
            <th id="south" scope="row">South</th>
            <td headers="south q1">110</td>
            <td headers="south q2">128</td>
        </tr>
    </tbody>
</table>
"""

show_example(
    "Explicit header relationships",
    complex_accessibility
)

print("""
For simple tables, scope is often sufficient.

For complex tables containing multiple levels of headers, the headers and id
attributes can explicitly associate data cells with the header cells that
describe them.

The pattern is:

    <th id="sales_q1">Q1 Sales</th>
    <td headers="sales_q1">120</td>

A data cell can reference multiple header IDs:

    headers="region q1"

This is useful when the relationship cannot be adequately represented using
simple scope relationships.
""")


# ============================================================================
# 15. COLGROUP AND COL
# ============================================================================

section("15. COLGROUP AND COL")

column_metadata = """
<table>
    <colgroup>
        <col>
        <col span="2">
        <col>
    </colgroup>

    <thead>
        <tr>
            <th>Product</th>
            <th>Q1</th>
            <th>Q2</th>
            <th>Total</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>Keyboard</td>
            <td>100</td>
            <td>120</td>
            <td>220</td>
        </tr>
    </tbody>
</table>
"""

show_example("Column groups", column_metadata)

print("""
<colgroup> groups columns.

<col> represents column metadata.

The span attribute can apply a <col> definition to multiple columns.

These elements are useful when column-level structure or styling metadata is
required.

They do not replace table cells and do not contain <td> or <th> elements.
""")


# ============================================================================
# 16. TABLE DATA TYPES
# ============================================================================

section("16. DATA TYPES IN TABLE CELLS")

print("""
HTML itself does not provide database-style data types for <td>.

A cell can contain:
- text
- numbers
- dates
- links
- images
- buttons
- other appropriate phrasing or flow content

The semantic meaning comes from the surrounding structure and the content.

For machine-readable information, additional semantic technologies may be
appropriate depending on the application.

Example:
""")

show_example(
    "Mixed cell content",
    """<table>
    <tr>
        <th scope="col">Product</th>
        <th scope="col">Website</th>
        <th scope="col">Status</th>
    </tr>
    <tr>
        <td>Application</td>
        <td><a href="/application">Open application</a></td>
        <td>Active</td>
    </tr>
</table>"""
)


# ============================================================================
# 17. EMPTY CELLS
# ============================================================================

section("17. EMPTY TABLE CELLS")

print("""
An empty <td> is different from a missing <td>.

Correct:

    <tr>
        <td>Asha</td>
        <td></td>
        <td>91</td>
    </tr>

The empty cell occupies a structural position.

Removing the cell changes the table structure.

If a value is genuinely unavailable, the application should distinguish
between:
- zero
- unknown
- not applicable
- intentionally blank

Do not use a missing cell as a substitute for semantic meaning.
""")


# ============================================================================
# 18. LIST STRUCTURE VALIDATION
# ============================================================================

section("18. VALIDATING LIST STRUCTURE")

print("""
A useful conceptual rule for lists:

    <ul> or <ol>
        -> <li>
            -> optional nested list

The following is structurally problematic:

    <ul>
        <p>Item</p>
    </ul>

The direct list content should be represented using list items.

Correct:

    <ul>
        <li>Item</li>
    </ul>

Description lists have their own structure:

    <dl>
        <dt>Term</dt>
        <dd>Description</dd>
    </dl>
""")


# ============================================================================
# 19. TABLE STRUCTURE VALIDATION
# ============================================================================

section("19. VALIDATING TABLE STRUCTURE")

print("""
For a conceptual four-column table:

    Row 1: 4 occupied columns
    Row 2: 4 occupied columns
    Row 3: 4 occupied columns

If colspan or rowspan is used, calculate occupied positions rather than
simply counting literal <td> elements.

Example:

    <td colspan="2">A</td>
    <td>B</td>

contains two cell elements but occupies three columns.

This distinction is essential when debugging complex tables.
""")


# ============================================================================
# 20. A PROGRAMMATIC TABLE GRID MODEL
# ============================================================================

section("20. PROGRAMMATIC TABLE GRID VALIDATION")

@dataclass(frozen=True)
class Cell:
    """Represents one logical HTML table cell."""
    content: str
    row_span: int = 1
    col_span: int = 1
    is_header: bool = False

    def __post_init__(self) -> None:
        if self.row_span < 1:
            raise ValueError("row_span must be at least 1")
        if self.col_span < 1:
            raise ValueError("col_span must be at least 1")


def place_cells(
    rows: Sequence[Sequence[Cell]],
    column_count: int,
) -> list[list[str | None]]:
    """
    Place cells into a conceptual grid.

    This is not an HTML parser. It is an educational model showing why
    rowspan and colspan complicate table structure.
    """
    if column_count < 1:
        raise ValueError("column_count must be positive")

    grid: list[list[str | None]] = [
        [None for _ in range(column_count)]
        for _ in range(len(rows))
    ]

    for row_index, row in enumerate(rows):
        column_index = 0

        for cell in row:
            while (
                column_index < column_count
                and grid[row_index][column_index] is not None
            ):
                column_index += 1

            if column_index + cell.col_span > column_count:
                raise ValueError(
                    f"Cell '{cell.content}' exceeds the table width"
                )

            if row_index + cell.row_span > len(rows):
                raise ValueError(
                    f"Cell '{cell.content}' exceeds the table height"
                )

            for r in range(row_index, row_index + cell.row_span):
                for c in range(
                    column_index,
                    column_index + cell.col_span,
                ):
                    if grid[r][c] is not None:
                        raise ValueError(
                            f"Cell '{cell.content}' overlaps "
                            f"an existing cell at row {r}, column {c}"
                        )

                    grid[r][c] = cell.content

            column_index += cell.col_span

    return grid


grid_rows = [
    [
        Cell("Name", is_header=True),
        Cell("Training", col_span=2, is_header=True),
        Cell("Score", is_header=True),
    ],
    [
        Cell("Asha", is_header=True),
        Cell("Theory"),
        Cell("Practical"),
        Cell("91"),
    ],
]

grid = place_cells(grid_rows, column_count=4)

for row in grid:
    print(row)

print("""
The grid model demonstrates that a colspan of 2 occupies two physical
positions even though it is represented by one HTML cell.
""")


# ============================================================================
# 21. GENERATING HTML SAFELY
# ============================================================================

section("21. SAFE HTML GENERATION")

print("""
When generating HTML from external or user-controlled data, text must be
escaped before being inserted into HTML.

For example, a value such as:

    <script>alert("test")</script>

must not accidentally become executable markup.

Python's html.escape() can escape characters such as:

    <  -> &lt;
    >  -> &gt;
    &  -> &amp;
    "  -> &quot;
    '  -> &#x27;

Escaping is context-dependent. HTML text content, HTML attributes,
JavaScript, CSS, and URLs have different security requirements.
""")

unsafe_name = '<img src=x onerror="alert(\'XSS\')">'
safe_name = escape(unsafe_name)

show_example(
    "Escaping user-controlled text",
    f"""<td>{safe_name}</td>"""
)


# ============================================================================
# 22. SAFE LIST GENERATOR
# ============================================================================

section("22. PYTHON FUNCTION FOR AN UNORDERED LIST")

def html_unordered_list(items: Iterable[str]) -> str:
    """Generate an unordered HTML list with escaped item content."""
    escaped_items = [f"    <li>{escape(item)}</li>" for item in items]

    return "<ul>\n" + "\n".join(escaped_items) + "\n</ul>"


items = [
    "HTML",
    "CSS",
    "SQL",
    '<script>alert("unsafe")</script>',
]

generated_list = html_unordered_list(items)
show_example("Generated safe unordered list", generated_list)


# ============================================================================
# 23. SAFE ORDERED LIST GENERATOR
# ============================================================================

section("23. PYTHON FUNCTION FOR AN ORDERED LIST")

def html_ordered_list(items: Iterable[str], start: int = 1) -> str:
    """Generate an ordered list and validate its start value."""
    if not isinstance(start, int):
        raise TypeError("start must be an integer")

    escaped_items = [
        f"    <li>{escape(item)}</li>"
        for item in items
    ]

    attributes = "" if start == 1 else f' start="{start}"'

    return (
        f"<ol{attributes}>\n"
        + "\n".join(escaped_items)
        + "\n</ol>"
    )


show_example(
    "Generated ordered list",
    html_ordered_list(["Install", "Configure", "Test"], start=3)
)


# ============================================================================
# 24. DESCRIPTION LIST GENERATOR
# ============================================================================

section("24. PYTHON FUNCTION FOR A DESCRIPTION LIST")

def html_description_list(
    definitions: Sequence[tuple[str, str]],
) -> str:
    """Generate a description list with escaped terms and descriptions."""
    lines = ["<dl>"]

    for term, description in definitions:
        lines.append(f"    <dt>{escape(term)}</dt>")
        lines.append(f"    <dd>{escape(description)}</dd>")

    lines.append("</dl>")
    return "\n".join(lines)


definitions = [
    ("HTML", "A markup language for document structure."),
    ("CSS", "A stylesheet language for presentation."),
    ("HTTP", "A protocol for transferring web resources."),
]

show_example(
    "Generated description list",
    html_description_list(definitions)
)


# ============================================================================
# 25. DATA-DRIVEN TABLE GENERATION
# ============================================================================

section("25. DATA-DRIVEN TABLE GENERATION")

def html_table(
    headers: Sequence[str],
    rows: Sequence[Sequence[str]],
    caption: str | None = None,
) -> str:
    """
    Generate a simple accessible table.

    This generator deliberately targets a simple rectangular table. Complex
    rowspan/colspan relationships should use a richer data model rather than
    being inferred from arbitrary nested lists.
    """
    if not headers:
        raise ValueError("A table must have at least one header")

    width = len(headers)

    for index, row in enumerate(rows):
        if len(row) != width:
            raise ValueError(
                f"Row {index} contains {len(row)} cells; "
                f"expected {width}"
            )

    lines = ["<table>"]

    if caption is not None:
        lines.append(f"    <caption>{escape(caption)}</caption>")

    lines.append("    <thead>")
    lines.append("        <tr>")

    for header in headers:
        lines.append(
            f'            <th scope="col">{escape(header)}</th>'
        )

    lines.append("        </tr>")
    lines.append("    </thead>")

    lines.append("    <tbody>")

    for row in rows:
        lines.append("        <tr>")

        for value in row:
            lines.append(f"            <td>{escape(value)}</td>")

        lines.append("        </tr>")

    lines.append("    </tbody>")
    lines.append("</table>")

    return "\n".join(lines)


employee_headers = ["Name", "Department", "Score"]

employee_rows = [
    ["Asha", "Data", "91"],
    ["Rahul", "Security", "87"],
    ["Meera", "Engineering", "94"],
]

employee_table = html_table(
    employee_headers,
    employee_rows,
    caption="Employee Performance",
)

show_example("Generated data-driven table", employee_table)


# ============================================================================
# 26. VALIDATION AND ERROR HANDLING
# ============================================================================

section("26. TABLE VALIDATION")

try:
    html_table(
        ["Name", "Score"],
        [
            ["Asha", "91"],
            ["Rahul"],  # Deliberately invalid row length.
        ],
    )
except ValueError as error:
    print("Caught expected validation error:")
    print(error)

print("""
Failing early is preferable to silently producing malformed or misleading
data.

For production HTML generation, validation should check:
- expected column count
- required values
- allowed values
- correct escaping
- correct semantic headers
- valid span relationships
- appropriate data types
""")


# ============================================================================
# 27. COMPLETE REAL-WORLD TABLE
# ============================================================================

section("27. COMPLETE REAL-WORLD STYLE TABLE")

complete_table = """
<table>
    <caption>Quarterly Employee Performance</caption>

    <thead>
        <tr>
            <th rowspan="2" scope="col">Employee</th>
            <th colspan="2" scope="colgroup">Performance</th>
            <th rowspan="2" scope="col">Final Rating</th>
        </tr>
        <tr>
            <th scope="col">Quality</th>
            <th scope="col">Delivery</th>
        </tr>
    </thead>

    <tbody>
        <tr>
            <th scope="row">Asha</th>
            <td>94</td>
            <td>91</td>
            <td>Excellent</td>
        </tr>
        <tr>
            <th scope="row">Rahul</th>
            <td>88</td>
            <td>90</td>
            <td>Very Good</td>
        </tr>
        <tr>
            <th scope="row">Meera</th>
            <td>96</td>
            <td>95</td>
            <td>Excellent</td>
        </tr>
    </tbody>

    <tfoot>
        <tr>
            <th scope="row">Average</th>
            <td>92.7</td>
            <td>92.0</td>
            <td>Excellent</td>
        </tr>
    </tfoot>
</table>
"""

show_example("Complete semantic table", complete_table)


# ============================================================================
# 28. TABLES WITH GROUPED DATA
# ============================================================================

section("28. MULTIPLE TBODY GROUPS")

grouped_table = """
<table>
    <caption>Department Performance</caption>

    <thead>
        <tr>
            <th scope="col">Employee</th>
            <th scope="col">Score</th>
        </tr>
    </thead>

    <tbody>
        <tr>
            <th colspan="2" scope="rowgroup">Engineering</th>
        </tr>
        <tr>
            <th scope="row">Asha</th>
            <td>95</td>
        </tr>
    </tbody>

    <tbody>
        <tr>
            <th colspan="2" scope="rowgroup">Security</th>
        </tr>
        <tr>
            <th scope="row">Rahul</th>
            <td>89</td>
        </tr>
    </tbody>
</table>
"""

show_example("Multiple tbody groups", grouped_table)

print("""
Multiple <tbody> elements can represent separate row groups.

This can be useful when data naturally contains categories such as:
- departments
- regions
- product categories
- time periods
""")


# ============================================================================
# 29. LISTS INSIDE TABLE CELLS
# ============================================================================

section("29. LISTS INSIDE TABLE CELLS")

table_with_list = """
<table>
    <caption>Project Responsibilities</caption>
    <tr>
        <th scope="col">Team</th>
        <th scope="col">Responsibilities</th>
    </tr>
    <tr>
        <th scope="row">Engineering</th>
        <td>
            <ul>
                <li>Implementation</li>
                <li>Testing</li>
                <li>Maintenance</li>
            </ul>
        </td>
    </tr>
</table>
"""

show_example("List inside a table cell", table_with_list)

print("""
A table cell can contain a list when the list is genuinely part of that
cell's data.

The table still represents the outer relationship, while the list represents
a collection within one cell.
""")


# ============================================================================
# 30. TABLES INSIDE LIST ITEMS
# ============================================================================

section("30. TABLES INSIDE LIST ITEMS")

list_with_table = """
<ol>
    <li>
        Review the following results:
        <table>
            <tr>
                <th scope="col">Metric</th>
                <th scope="col">Value</th>
            </tr>
            <tr>
                <th scope="row">Accuracy</th>
                <td>94%</td>
            </tr>
        </table>
    </li>
</ol>
"""

show_example("Table nested within list-item content", list_with_table)

print("""
HTML permits appropriate flow content within list items.

The key semantic principle remains the same:
the <li> represents one list item, and the table represents structured data
associated with that item.
""")


# ============================================================================
# 31. LISTS VS TABLES
# ============================================================================

section("31. LISTS VS TABLES")

print("""
Use an unordered list when:
    - items form a collection
    - order is not inherently meaningful

Use an ordered list when:
    - sequence matters
    - ranking matters
    - steps matter

Use a description list when:
    - terms and descriptions form meaningful pairs/groups

Use a table when:
    - values have meaningful relationships across rows and columns
    - users need to compare multiple dimensions of structured data

Do not choose an element solely because its default visual appearance looks
right.
""")


# ============================================================================
# 32. ORDERED LIST VS UNORDERED LIST
# ============================================================================

section("32. ORDERED VS UNORDERED LIST COMPARISON")

comparison = [
    ("Semantic purpose", "Sequence/rank", "Collection without required order"),
    ("Element", "<ol>", "<ul>"),
    ("Item", "<li>", "<li>"),
    ("Default marker", "Numbers", "Bullets"),
    ("Can customize markers", "Yes", "Yes"),
    ("Sequence meaningful", "Yes", "Usually no"),
]

for row in comparison:
    print(f"{row[0]:25} | {row[1]:30} | {row[2]}")


# ============================================================================
# 33. DESCRIPTION LIST VS TABLE
# ============================================================================

section("33. DESCRIPTION LIST VS TABLE")

print("""
Description list:

    Term -> Description

Table:

    Row/column relationships among multiple dimensions

Example that fits a description list:

    CPU -> Central Processing Unit
    RAM -> Random Access Memory

Example that fits a table:

    Product | Price | Stock | Rating

If several attributes must be compared horizontally across many records, a
table is generally the appropriate semantic structure.
""")


# ============================================================================
# 34. COMMON LIST MISTAKES
# ============================================================================

section("34. COMMON LIST MISTAKES")

mistakes = [
    (
        "Using <p> instead of <li>",
        "Use list-item elements inside ordered/unordered lists."
    ),
    (
        "Using <br> to create a list",
        "Represent the collection semantically with <ul>, <ol>, or <dl>."
    ),
    (
        "Putting nested <ul> directly inside <ul>",
        "Put nested lists inside the relevant parent <li>."
    ),
    (
        "Using <ol> when sequence has no meaning",
        "Use <ul> when ordering is not semantically important."
    ),
    (
        "Using <dl> as a generic two-column layout",
        "Use description lists only for term/description relationships."
    ),
]

for mistake, correction in mistakes:
    print(f"\nMistake: {mistake}\nBetter:  {correction}")


# ============================================================================
# 35. COMMON TABLE MISTAKES
# ============================================================================

section("35. COMMON TABLE MISTAKES")

table_mistakes = [
    (
        "Using tables for page layout",
        "Use CSS layout techniques for page structure."
    ),
    (
        "Using <td> for every heading",
        "Use <th> for cells that semantically label rows or columns."
    ),
    (
        "Omitting meaningful headers",
        "Provide appropriate header cells."
    ),
    (
        "Ignoring colspan/rowspan arithmetic",
        "Validate the logical grid."
    ),
    (
        "Putting unrelated content into one table",
        "Use separate semantic structures when relationships differ."
    ),
    (
        "Using empty cells to hide information",
        "Represent missing or unavailable values meaningfully."
    ),
    (
        "Using visual alignment instead of semantics",
        "Use semantic elements first and CSS for presentation."
    ),
]

for mistake, correction in table_mistakes:
    print(f"\nMistake: {mistake}\nBetter:  {correction}")


# ============================================================================
# 36. TABLE ACCESSIBILITY PRINCIPLES
# ============================================================================

section("36. ACCESSIBILITY PRINCIPLES")

print("""
Important accessibility practices include:

1. Provide a meaningful caption when a table needs a title.
2. Use <th> for semantic headers.
3. Use scope="col" for column headers where appropriate.
4. Use scope="row" for row headers where appropriate.
5. Use more explicit headers/id relationships for genuinely complex tables.
6. Keep tables logically structured.
7. Avoid excessive spanning that makes relationships difficult to follow.
8. Do not use tables solely for visual layout.
9. Ensure important information is not communicated only through visual
   positioning.
10. Consider how assistive technology will interpret header relationships.
""")


# ============================================================================
# 37. RESPONSIVE TABLE CONSIDERATIONS
# ============================================================================

section("37. RESPONSIVE TABLE CONSIDERATIONS")

print("""
Tables can become difficult to read on narrow screens because their
two-dimensional structure may require more horizontal space.

Possible production strategies include:

- horizontal scrolling for genuinely tabular data
- carefully reducing unnecessary columns
- responsive CSS
- alternative presentations for especially complex datasets

Do not destroy meaningful relationships merely to force every table into a
narrow screen.

A table is still a table even when its presentation changes across viewport
sizes.
""")


# ============================================================================
# 38. PERFORMANCE CONSIDERATIONS
# ============================================================================

section("38. PERFORMANCE CONSIDERATIONS")

print("""
For normal tables and lists, semantic HTML itself is usually not the primary
performance bottleneck.

Performance concerns become significant with very large datasets.

Potential issues include:
- very large DOM trees
- expensive client-side rendering
- repeated DOM manipulation
- excessive nested structures
- large amounts of duplicated markup

For large datasets, applications may need:
- pagination
- server-side filtering
- server-side sorting
- incremental rendering
- virtualization where appropriate

The correct optimization depends on the application architecture.
""")


# ============================================================================
# 39. SECURITY CONSIDERATIONS
# ============================================================================

section("39. SECURITY CONSIDERATIONS")

print("""
HTML lists and tables are generally low-risk elements, but dynamically
generated content can create security problems.

The main concern is injection of untrusted content into HTML.

Example dangerous input:

    <img src=x onerror="alert('XSS')">

If inserted as raw HTML, the browser may interpret it as markup.

If it is intended to be text, escape it.

Python example:

    escape(user_input)

Important distinction:

    Text content      -> HTML escaping
    HTML attribute    -> context-aware attribute escaping
    URL               -> validate URL scheme and context
    JavaScript string -> JavaScript-specific escaping
    CSS value         -> CSS-specific handling

Do not assume that one generic escaping operation is safe for every output
context.

Also:
- validate input
- avoid unnecessary raw HTML construction
- use trusted templating systems where appropriate
- apply Content Security Policy as part of a broader web security strategy
""")


# ============================================================================
# 40. ATTRIBUTE ESCAPING
# ============================================================================

section("40. SAFE HTML ATTRIBUTE GENERATION")

def safe_html_attribute(name: str, value: str) -> str:
    """
    Create a basic escaped HTML attribute.

    This demonstrates HTML escaping. It is not a substitute for URL
    validation, especially when generating href/src attributes.
    """
    if not re.fullmatch(r"[A-Za-z_:][A-Za-z0-9:._-]*", name):
        raise ValueError("Invalid HTML attribute name")

    return f'{name}="{escape(value, quote=True)}"'


attribute = safe_html_attribute(
    "title",
    'Employee "Asha" & performance',
)

print(attribute)


# ============================================================================
# 41. URL SECURITY DISTINCTION
# ============================================================================

section("41. URL VALUES REQUIRE ADDITIONAL VALIDATION")

print("""
HTML escaping alone does not make an untrusted URL safe.

For example, a dangerous URL scheme can still be dangerous even if the text
is escaped.

A production application should validate URLs according to its requirements,
often allowing only expected schemes such as:

    https
    http

and sometimes:

    mailto

The exact policy depends on the application.

The general lesson is:

    escaping != validation

Escaping protects syntax in an output context.
Validation determines whether a value is acceptable for the application.
""")


# ============================================================================
# 42. DEBUGGING LISTS
# ============================================================================

section("42. DEBUGGING LIST MARKUP")

debug_list = """
<ul>
    <li>Parent
        <ol>
            <li>Child A</li>
            <li>Child B</li>
        </ol>
    </li>
    <li>Second parent</li>
</ul>
"""

print(debug_list)

print("""
When debugging a list:

1. Identify the list container.
2. Check every list item.
3. Check indentation in source code.
4. Check whether nested lists are inside the intended <li>.
5. Check whether ordering is semantically correct.
6. Inspect the browser DOM, not just the source text.
7. Inspect CSS if markers or spacing appear incorrect.

A visual problem can be caused by CSS even when the HTML structure is valid.
""")


# ============================================================================
# 43. DEBUGGING TABLES
# ============================================================================

section("43. DEBUGGING TABLE MARKUP")

print("""
When debugging a table:

1. Identify the intended number of logical columns.
2. Count cells in each row.
3. Account for colspan.
4. Account for rowspan.
5. Check header relationships.
6. Check <thead>, <tbody>, and <tfoot> grouping.
7. Inspect the browser's DOM.
8. Check CSS separately from HTML.
9. Test the table with realistic and edge-case data.

For complicated tables, draw a conceptual grid on paper or model it
programmatically, as demonstrated earlier.
""")


# ============================================================================
# 44. TESTING HTML GENERATORS
# ============================================================================

section("44. TESTING HTML GENERATORS")

def test_html_unordered_list() -> None:
    """Basic unit tests for the list generator."""
    result = html_unordered_list(["A", "B"])

    assert result == (
        "<ul>\n"
        "    <li>A</li>\n"
        "    <li>B</li>\n"
        "</ul>"
    )


def test_html_escaping() -> None:
    """Verify that user content is escaped."""
    result = html_unordered_list(["<script>"])

    assert "&lt;script&gt;" in result
    assert "<script>" not in result


def test_html_table() -> None:
    """Verify rectangular table generation."""
    result = html_table(
        ["Name", "Score"],
        [["Asha", "95"]],
        caption="Results",
    )

    assert "<caption>Results</caption>" in result
    assert '<th scope="col">Name</th>' in result
    assert "<td>95</td>" in result


def test_html_table_rejects_invalid_width() -> None:
    """Verify malformed rectangular data is rejected."""
    try:
        html_table(
            ["Name", "Score"],
            [["Asha"]],
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError")


test_html_unordered_list()
test_html_escaping()
test_html_table()
test_html_table_rejects_invalid_width()

print("All built-in tests passed.")


# ============================================================================
# 45. EDGE CASES
# ============================================================================

section("45. EDGE CASES")

edge_cases = [
    ("Empty unordered list", "<ul></ul>"),
    ("Empty ordered list", "<ol></ol>"),
    ("Empty description list", "<dl></dl>"),
    ("Empty table", "<table></table>"),
    ("One-cell table", "<table><tr><td>One value</td></tr></table>"),
    ("Long list item", "<li>" + "A" * 100 + "</li>"),
    ("Special characters", "<td>&lt; &amp; &gt;</td>"),
]

for name, markup in edge_cases:
    print(f"\n{name}:")
    print(markup)

print("""
An empty structure may be technically representable but often has little
practical value.

Application code should determine whether empty data should produce:
- an empty structure
- a meaningful "No data available" message
- no component at all

Do not confuse an empty dataset with a dataset containing a blank value.
""")


# ============================================================================
# 46. LARGE LIST GENERATION
# ============================================================================

section("46. GENERATING LARGE LISTS EFFICIENTLY")

large_items = [f"Item {index}" for index in range(1, 11)]

large_list = html_unordered_list(large_items)

print(large_list)

print("""
For large generated collections, constructing a list of strings and joining
once is generally clearer and can avoid repeated string concatenation.

For extremely large output, streaming or incremental rendering may be more
appropriate depending on the application.
""")


# ============================================================================
# 47. COMPLETE HTML DOCUMENT
# ============================================================================

section("47. COMPLETE HTML DOCUMENT CONTAINING LISTS AND TABLES")

complete_document = """<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Lists and Tables</title>
</head>
<body>

    <header>
        <h1>Training Information</h1>
    </header>

    <main>
        <section>
            <h2>Learning Topics</h2>

            <ol>
                <li>HTML fundamentals</li>
                <li>CSS fundamentals</li>
                <li>JavaScript fundamentals</li>
            </ol>
        </section>

        <section>
            <h2>Technologies</h2>

            <ul>
                <li>Frontend
                    <ul>
                        <li>HTML</li>
                        <li>CSS</li>
                    </ul>
                </li>
                <li>Backend
                    <ul>
                        <li>Python</li>
                        <li>SQL</li>
                    </ul>
                </li>
            </ul>
        </section>

        <section>
            <h2>Terminology</h2>

            <dl>
                <dt>HTML</dt>
                <dd>Markup for document structure.</dd>

                <dt>CSS</dt>
                <dd>Stylesheet language for presentation.</dd>
            </dl>
        </section>

        <section>
            <h2>Scores</h2>

            <table>
                <caption>Assessment Results</caption>

                <thead>
                    <tr>
                        <th scope="col">Student</th>
                        <th scope="col">Theory</th>
                        <th scope="col">Practical</th>
                        <th scope="col">Final</th>
                    </tr>
                </thead>

                <tbody>
                    <tr>
                        <th scope="row">Asha</th>
                        <td>88</td>
                        <td>94</td>
                        <td>91</td>
                    </tr>
                    <tr>
                        <th scope="row">Rahul</th>
                        <td>84</td>
                        <td>90</td>
                        <td>87</td>
                    </tr>
                </tbody>
            </table>
        </section>
    </main>

    <footer>
        <p>Training records</p>
    </footer>

</body>
</html>
"""

print(complete_document)


# ============================================================================
# 48. SEMANTIC DOCUMENT STRUCTURE
# ============================================================================

section("48. SEMANTIC HTML AND PRESENTATION")

print("""
A useful architecture is:

    HTML
      -> structure and meaning

    CSS
      -> presentation and layout

    JavaScript
      -> behavior and interaction

Lists and tables belong primarily to the HTML structural layer.

For example, the fact that content is an ordered procedure belongs in HTML:

    <ol>
        <li>...</li>
    </ol>

How the numbers look belongs in CSS.

Likewise, the fact that information has row/column relationships belongs in
<table>. The visual colors, borders, spacing, typography, and responsive
presentation belong primarily to CSS.
""")


# ============================================================================
# 49. PRODUCTION CHECKLIST
# ============================================================================

section("49. PRODUCTION CHECKLIST")

checklist = [
    "Choose list type based on semantic meaning.",
    "Use <li> for list items.",
    "Place nested lists within the appropriate <li>.",
    "Use <dl>, <dt>, and <dd> for genuine term/description relationships.",
    "Use tables for genuine tabular data.",
    "Use <caption> when a table needs a descriptive title.",
    "Use <th> for meaningful row or column headers.",
    "Use scope for simple header relationships.",
    "Use headers/id relationships when simple scope is insufficient.",
    "Validate rowspan and colspan carefully.",
    "Use thead/tbody/tfoot to communicate row-group structure.",
    "Escape untrusted text before placing it in HTML.",
    "Validate URLs separately from escaping them.",
    "Do not use tables for page layout.",
    "Test unusual and empty datasets.",
    "Inspect the actual browser DOM during debugging.",
    "Consider responsive behavior for wide tables.",
    "Consider DOM size for very large datasets.",
]

for number, item in enumerate(checklist, start=1):
    print(f"{number:02d}. {item}")


# ============================================================================
# 50. FINAL PRACTICAL EXERCISES
# ============================================================================

section("50. PRACTICAL EXERCISES")

print("""
Exercise 1
----------
Create an unordered list of five programming languages.

Exercise 2
----------
Convert the same content to an ordered list and decide whether the ordering
has semantic meaning.

Exercise 3
----------
Create a nested list representing:
    Technology
        Frontend
            HTML
            CSS
        Backend
            Python
            SQL

Exercise 4
----------
Create a description list containing five HTML terms and descriptions.

Exercise 5
----------
Create a table with:
    Product | Category | Price | Stock

Add a caption and column headers.

Exercise 6
----------
Add a table footer containing a total.

Exercise 7
----------
Create a two-level table header using colspan and rowspan.

Exercise 8
----------
Add scope attributes to the headers.

Exercise 9
----------
Generate a table programmatically using the html_table() function.

Exercise 10
-----------
Pass user-controlled text containing HTML markup into the generator and verify
that the output is escaped.

Exercise 11
-----------
Create a table with two separate tbody groups representing two departments.

Exercise 12
-----------
Design a complex table with multiple header dimensions and determine whether
scope is sufficient or headers/id relationships are more appropriate.
""")


# ============================================================================
# 51. EXECUTABLE RECAP
# ============================================================================

section("51. EXECUTABLE RECAP")

print("""
Core syntax patterns:

Unordered list:
    <ul>
        <li>Item</li>
    </ul>

Ordered list:
    <ol>
        <li>Step</li>
    </ol>

Nested list:
    <ul>
        <li>
            Parent
            <ul>
                <li>Child</li>
            </ul>
        </li>
    </ul>

Description list:
    <dl>
        <dt>Term</dt>
        <dd>Description</dd>
    </dl>

Basic table:
    <table>
        <tr>
            <th>Header</th>
            <td>Value</td>
        </tr>
    </table>

Structured table:
    <table>
        <caption>Title</caption>
        <thead>...</thead>
        <tbody>...</tbody>
        <tfoot>...</tfoot>
    </table>

Column spanning:
    <th colspan="2">Group</th>

Row spanning:
    <th rowspan="2">Group</th>

Column header:
    <th scope="col">Name</th>

Row header:
    <th scope="row">Asha</th>
""")


# ============================================================================
# 52. SCRIPT COMPLETION
# ============================================================================

section("52. SCRIPT COMPLETED")

print("""
The examples above form a progression from basic list and table syntax to
nested structures, semantic grouping, accessibility, spanning cells,
programmatic generation, validation, security, testing, debugging, and
production considerations.
""")
