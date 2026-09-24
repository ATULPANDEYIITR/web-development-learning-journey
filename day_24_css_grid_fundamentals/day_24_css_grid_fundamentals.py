"""
CSS Grid Fundamentals
=====================

A self-contained study program for learning:

- Grid containers
- Grid rows and columns
- Grid tracks
- Grid gaps
- Grid cells
- Grid lines
- Grid areas
- Explicit and implicit grids
- Fixed, flexible, and intrinsic sizing
- fr units
- repeat()
- minmax()
- auto-fit and auto-fill
- grid-template-areas
- item placement
- spanning
- alignment
- auto-placement
- responsive layouts
- common mistakes
- practical layout calculations

The program uses only the Python standard library. It models important
CSS Grid concepts numerically so that the relationship between CSS
declarations and the resulting layout can be observed without requiring
a browser.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import floor
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


# ---------------------------------------------------------------------------
# Section 1: Fundamental terminology
# ---------------------------------------------------------------------------

def print_section(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def explain_fundamentals() -> None:
    print_section("1. CSS Grid fundamentals")

    concepts = {
        "Grid container": "An element whose display property is set to grid or inline-grid.",
        "Grid item": "A direct child of a grid container.",
        "Grid row": "A horizontal sequence of grid cells.",
        "Grid column": "A vertical sequence of grid cells.",
        "Grid track": "A row track or column track between two adjacent grid lines.",
        "Grid cell": "The smallest rectangular unit formed by intersecting one row and one column.",
        "Grid line": "A numbered boundary separating grid tracks.",
        "Gap": "Space inserted between adjacent rows or columns.",
        "Grid area": "A rectangular region containing one or more grid cells.",
        "Explicit grid": "Rows and columns explicitly declared by grid-template-rows or grid-template-columns.",
        "Implicit grid": "Additional tracks automatically created when items require them.",
    }

    for name, definition in concepts.items():
        print(f"{name:18} : {definition}")

    print("\nThe basic relationship is:")
    print("Grid container")
    print("    -> grid rows + grid columns")
    print("    -> grid tracks")
    print("    -> grid cells")
    print("    -> grid items occupy cells or larger grid areas")


# ---------------------------------------------------------------------------
# Section 2: A simple grid representation
# ---------------------------------------------------------------------------

@dataclass
class GridItem:
    name: str
    row: Optional[int] = None
    column: Optional[int] = None
    row_span: int = 1
    column_span: int = 1
    area: Optional[str] = None

    def occupies(self) -> Tuple[int, int, int, int]:
        if self.row is None or self.column is None:
            raise ValueError(f"{self.name} has not been placed.")
        return (
            self.row,
            self.column,
            self.row + self.row_span - 1,
            self.column + self.column_span - 1,
        )


@dataclass
class Grid:
    rows: int
    columns: int
    row_gap: float = 0
    column_gap: float = 0
    items: List[GridItem] = field(default_factory=list)

    def add_item(self, item: GridItem) -> None:
        if item.row is None or item.column is None:
            raise ValueError(
                f"Item '{item.name}' needs a row and column for this explicit model."
            )

        end_row = item.row + item.row_span - 1
        end_column = item.column + item.column_span - 1

        if item.row < 1 or item.column < 1:
            raise ValueError("Grid positions are one-based in this educational model.")

        if end_row > self.rows or end_column > self.columns:
            raise ValueError(
                f"Item '{item.name}' extends outside the {self.rows}x{self.columns} grid."
            )

        self.items.append(item)

    def occupancy_matrix(self) -> List[List[str]]:
        matrix = [
            ["." for _ in range(self.columns)]
            for _ in range(self.rows)
        ]

        for item in self.items:
            start_row, start_column, end_row, end_column = item.occupies()

            for row in range(start_row - 1, end_row):
                for column in range(start_column - 1, end_column):
                    if matrix[row][column] != ".":
                        raise ValueError(
                            f"Grid collision at row {row + 1}, column {column + 1}."
                        )
                    matrix[row][column] = item.name[:8]

        return matrix

    def display(self) -> None:
        print(f"\nGrid: {self.rows} rows x {self.columns} columns")
        print(f"Row gap: {self.row_gap}")
        print(f"Column gap: {self.column_gap}")

        matrix = self.occupancy_matrix()

        header = "      " + "".join(f"{column + 1:^10}" for column in range(self.columns))
        print(header)
        print("      " + "-" * (10 * self.columns))

        for index, row in enumerate(matrix, start=1):
            print(f"{index:^5}|" + "".join(f"{cell:^10}" for cell in row))


def demonstrate_basic_grid() -> None:
    print_section("2. Basic rows, columns, cells, and placement")

    grid = Grid(rows=3, columns=4, row_gap=16, column_gap=20)

    grid.add_item(GridItem("Header", row=1, column=1, column_span=4))
    grid.add_item(GridItem("Menu", row=2, column=1))
    grid.add_item(GridItem("Main", row=2, column=2, column_span=2))
    grid.add_item(GridItem("Aside", row=2, column=4))
    grid.add_item(GridItem("Footer", row=3, column=1, column_span=4))

    grid.display()

    print("\nEquivalent conceptual CSS:")
    print("display: grid;")
    print("grid-template-columns: repeat(4, 1fr);")
    print("grid-template-rows: auto 1fr auto;")
    print("gap: 16px 20px;")


# ---------------------------------------------------------------------------
# Section 3: Grid lines
# ---------------------------------------------------------------------------

def demonstrate_grid_lines() -> None:
    print_section("3. Grid lines and track boundaries")

    rows = 3
    columns = 4

    print(f"A {rows} x {columns} grid has:")
    print(f"  {rows + 1} horizontal grid lines")
    print(f"  {columns + 1} vertical grid lines")

    print("\nVertical lines:")
    print("1 -------- 2 -------- 3 -------- 4 -------- 5")

    print("\nHorizontal lines:")
    print("1")
    print("|")
    print("2")
    print("|")
    print("3")
    print("|")
    print("4")

    print("\nFor example:")
    print("grid-column: 2 / 4;")
    print("means:")
    print("  start at column line 2")
    print("  end at column line 4")
    print("  occupy column tracks 2 and 3")

    print("\nSpanning can also be expressed as:")
    print("grid-column: 2 / span 2;")


# ---------------------------------------------------------------------------
# Section 4: Gap calculations
# ---------------------------------------------------------------------------

def available_track_space(
    container_size: float,
    track_count: int,
    gap: float,
) -> float:
    if container_size < 0:
        raise ValueError("Container size cannot be negative.")
    if track_count <= 0:
        raise ValueError("Track count must be positive.")
    if gap < 0:
        raise ValueError("Gap cannot be negative.")

    total_gaps = max(0, track_count - 1) * gap
    return container_size - total_gaps


def equal_fraction_tracks(
    container_size: float,
    track_count: int,
    gap: float,
) -> List[float]:
    remaining = available_track_space(container_size, track_count, gap)

    if remaining < 0:
        raise ValueError(
            "The fixed gaps alone are larger than the available container size."
        )

    size = remaining / track_count
    return [size] * track_count


def demonstrate_gaps_and_fr() -> None:
    print_section("4. Gaps and the fr unit")

    container_width = 1000
    columns = 4
    gap = 20

    tracks = equal_fraction_tracks(container_width, columns, gap)

    print(f"Container width: {container_width}px")
    print(f"Columns: {columns}")
    print(f"Column gap: {gap}px")
    print(f"Total gap space: {(columns - 1) * gap}px")
    print(f"Space available for tracks: {container_width - (columns - 1) * gap}px")
    print(f"Each 1fr track: {tracks[0]:.2f}px")

    print("\nFor:")
    print("grid-template-columns: repeat(4, 1fr);")
    print("gap: 20px;")

    print("the browser distributes the remaining space among the four")
    print("flexible tracks rather than treating 1fr as 25% of the raw width.")


# ---------------------------------------------------------------------------
# Section 5: Weighted fractions
# ---------------------------------------------------------------------------

def weighted_fraction_tracks(
    container_size: float,
    fractions: Sequence[float],
    gap: float,
) -> List[float]:
    if not fractions:
        raise ValueError("At least one fraction is required.")
    if any(value <= 0 for value in fractions):
        raise ValueError("Fraction values must be positive.")
    if gap < 0:
        raise ValueError("Gap cannot be negative.")

    remaining = container_size - gap * (len(fractions) - 1)

    if remaining < 0:
        raise ValueError("Insufficient space after gaps.")

    total = sum(fractions)
    return [remaining * fraction / total for fraction in fractions]


def demonstrate_weighted_fr() -> None:
    print_section("5. Multiple fr values")

    tracks = weighted_fraction_tracks(
        container_size=1200,
        fractions=[1, 2, 1],
        gap=24,
    )

    print("CSS:")
    print("grid-template-columns: 1fr 2fr 1fr;")
    print("gap: 24px;")

    print("\nCalculated track widths:")
    for index, width in enumerate(tracks, start=1):
        print(f"Track {index}: {width:.2f}px")


# ---------------------------------------------------------------------------
# Section 6: Fixed and flexible tracks
# ---------------------------------------------------------------------------

def fixed_and_fraction_tracks(
    container_size: float,
    fixed_sizes: Sequence[float],
    flexible_fractions: Sequence[float],
    gap: float,
) -> List[float]:
    track_count = len(fixed_sizes) + len(flexible_fractions)

    if track_count == 0:
        raise ValueError("At least one track is required.")

    if any(size < 0 for size in fixed_sizes):
        raise ValueError("Fixed track sizes cannot be negative.")

    if any(value <= 0 for value in flexible_fractions):
        raise ValueError("Flexible fractions must be positive.")

    total_gaps = (track_count - 1) * gap
    remaining = container_size - sum(fixed_sizes) - total_gaps

    if remaining < 0:
        raise ValueError("Fixed tracks and gaps consume too much space.")

    fraction_total = sum(flexible_fractions)
    flexible_sizes = [
        remaining * fraction / fraction_total
        for fraction in flexible_fractions
    ]

    return list(fixed_sizes) + flexible_sizes


def demonstrate_mixed_tracks() -> None:
    print_section("6. Fixed tracks mixed with flexible tracks")

    sizes = fixed_and_fraction_tracks(
        container_size=1200,
        fixed_sizes=[240],
        flexible_fractions=[1, 2],
        gap=24,
    )

    print("CSS:")
    print("grid-template-columns: 240px 1fr 2fr;")
    print("gap: 24px;")

    for index, size in enumerate(sizes, start=1):
        print(f"Track {index}: {size:.2f}px")


# ---------------------------------------------------------------------------
# Section 7: minmax()
# ---------------------------------------------------------------------------

def minmax_track_size(
    available_size: float,
    minimum: float,
    maximum: float,
) -> float:
    if minimum < 0:
        raise ValueError("Minimum cannot be negative.")
    if maximum < minimum:
        raise ValueError("Maximum must be greater than or equal to minimum.")

    return max(minimum, min(available_size, maximum))


def demonstrate_minmax() -> None:
    print_section("7. minmax()")

    print("Conceptual CSS:")
    print("grid-template-columns: minmax(200px, 1fr) 2fr;")

    for available in [150, 200, 300, 500, 800]:
        result = minmax_track_size(
            available_size=available,
            minimum=200,
            maximum=600,
        )
        print(
            f"Available={available:>3}px -> "
            f"minmax(200px, 600px) resolves to approximately {result}px"
        )

    print("\nminmax() is useful when a track should have a lower or upper bound.")
    print("It is particularly important in responsive layouts.")


# ---------------------------------------------------------------------------
# Section 8: repeat()
# ---------------------------------------------------------------------------

def repeat_tracks(pattern: Sequence[str], count: int) -> List[str]:
    if count < 0:
        raise ValueError("Repeat count cannot be negative.")
    return list(pattern) * count


def demonstrate_repeat() -> None:
    print_section("8. repeat()")

    explicit = repeat_tracks(["1fr"], 4)
    print("repeat(4, 1fr) ->", explicit)

    mixed = repeat_tracks(["minmax(180px, 1fr)", "minmax(180px, 2fr)"], 2)
    print("repeat(2, minmax(180px, 1fr) minmax(180px, 2fr))")
    print("->", mixed)


# ---------------------------------------------------------------------------
# Section 9: Auto-fit and auto-fill conceptual simulation
# ---------------------------------------------------------------------------

def maximum_auto_columns(
    container_width: float,
    minimum_card_width: float,
    gap: float,
) -> int:
    if container_width <= 0:
        raise ValueError("Container width must be positive.")
    if minimum_card_width <= 0:
        raise ValueError("Minimum card width must be positive.")
    if gap < 0:
        raise ValueError("Gap cannot be negative.")

    return max(
        1,
        floor((container_width + gap) / (minimum_card_width + gap)),
    )


def demonstrate_responsive_columns() -> None:
    print_section("9. Responsive columns with minmax() and auto-fit")

    minimum_card_width = 220
    gap = 20

    print("Typical CSS:")
    print(
        "grid-template-columns: "
        "repeat(auto-fit, minmax(220px, 1fr));"
    )

    for width in [320, 500, 700, 960, 1200, 1600]:
        columns = maximum_auto_columns(width, minimum_card_width, gap)
        print(
            f"Container {width:>4}px -> approximately {columns} "
            f"minimum-width card columns"
        )

    print("\nauto-fit generally collapses empty tracks and lets occupied")
    print("tracks expand. auto-fill preserves the conceptual empty tracks.")


# ---------------------------------------------------------------------------
# Section 10: Grid areas
# ---------------------------------------------------------------------------

@dataclass
class AreaGrid:
    template: List[List[str]]

    def __post_init__(self) -> None:
        if not self.template:
            raise ValueError("Template cannot be empty.")

        width = len(self.template[0])

        if width == 0:
            raise ValueError("Template rows cannot be empty.")

        if any(len(row) != width for row in self.template):
            raise ValueError("All template rows must have equal length.")

    @property
    def rows(self) -> int:
        return len(self.template)

    @property
    def columns(self) -> int:
        return len(self.template[0])

    def positions(self, area_name: str) -> List[Tuple[int, int]]:
        positions = []

        for row_index, row in enumerate(self.template):
            for column_index, value in enumerate(row):
                if value == area_name:
                    positions.append((row_index, column_index))

        return positions

    def validate_area(self, area_name: str) -> bool:
        positions = self.positions(area_name)

        if not positions:
            return False

        rows = [position[0] for position in positions]
        columns = [position[1] for position in positions]

        expected = {
            (row, column)
            for row in range(min(rows), max(rows) + 1)
            for column in range(min(columns), max(columns) + 1)
        }

        return set(positions) == expected

    def display(self) -> None:
        for row in self.template:
            print(" | ".join(f"{value:^10}" for value in row))


def demonstrate_grid_areas() -> None:
    print_section("10. Named grid areas")

    layout = AreaGrid(
        [
            ["header", "header", "header"],
            ["sidebar", "main", "main"],
            ["sidebar", "main", "main"],
            ["footer", "footer", "footer"],
        ]
    )

    print("Template:")
    layout.display()

    print("\nConceptual CSS:")
    print("grid-template-areas:")
    print('"header header header"')
    print('"sidebar main main"')
    print('"sidebar main main"')
    print('"footer footer footer";')

    for area in ["header", "sidebar", "main", "footer"]:
        print(
            f"Area '{area}' is rectangular: "
            f"{layout.validate_area(area)}"
        )

    print("\nA named area must form a rectangle.")
    print("A disconnected or non-rectangular shape is invalid for one named area.")


# ---------------------------------------------------------------------------
# Section 11: Auto-placement
# ---------------------------------------------------------------------------

def auto_place_items(
    rows: int,
    columns: int,
    item_names: Iterable[str],
) -> Dict[str, Tuple[int, int]]:
    if rows <= 0 or columns <= 0:
        raise ValueError("Grid dimensions must be positive.")

    result: Dict[str, Tuple[int, int]] = {}

    for index, name in enumerate(item_names):
        if index >= rows * columns:
            break

        row = index // columns + 1
        column = index % columns + 1
        result[name] = (row, column)

    return result


def demonstrate_auto_placement() -> None:
    print_section("11. Automatic placement")

    names = ["A", "B", "C", "D", "E", "F", "G"]
    placement = auto_place_items(2, 4, names)

    print("Grid: 2 rows x 4 columns")
    print("grid-auto-flow: row;")

    for name, position in placement.items():
        print(f"{name} -> row {position[0]}, column {position[1]}")

    print("\nThe browser can automatically place unpositioned grid items.")
    print("Explicitly positioned items and auto-placed items can coexist.")


# ---------------------------------------------------------------------------
# Section 12: Grid area dimensions
# ---------------------------------------------------------------------------

def area_pixel_size(
    row_sizes: Sequence[float],
    column_sizes: Sequence[float],
    row_start: int,
    row_end: int,
    column_start: int,
    column_end: int,
    row_gap: float,
    column_gap: float,
) -> Tuple[float, float]:
    if not (
        1 <= row_start <= row_end <= len(row_sizes)
        and 1 <= column_start <= column_end <= len(column_sizes)
    ):
        raise ValueError("Area boundaries are outside the grid.")

    height = sum(row_sizes[row_start - 1:row_end])
    width = sum(column_sizes[column_start - 1:column_end])

    height += max(0, row_end - row_start) * row_gap
    width += max(0, column_end - column_start) * column_gap

    return width, height


def demonstrate_spanning_area() -> None:
    print_section("12. Measuring a spanning grid area")

    row_sizes = [100, 200, 120]
    column_sizes = [200, 300, 180, 220]

    width, height = area_pixel_size(
        row_sizes=row_sizes,
        column_sizes=column_sizes,
        row_start=1,
        row_end=3,
        column_start=2,
        column_end=4,
        row_gap=20,
        column_gap=16,
    )

    print("Rows:", row_sizes)
    print("Columns:", column_sizes)
    print("Area: rows 1-3 and columns 2-4")
    print(f"Area width: {width}px")
    print(f"Area height: {height}px")

    print("\nThe area includes the tracks it spans and the internal gaps between them.")


# ---------------------------------------------------------------------------
# Section 13: Alignment
# ---------------------------------------------------------------------------

def alignment_offset(
    container_size: float,
    item_size: float,
    alignment: str,
) -> float:
    free_space = container_size - item_size

    if free_space < 0:
        return 0

    if alignment in {"start", "normal"}:
        return 0
    if alignment == "center":
        return free_space / 2
    if alignment == "end":
        return free_space
    if alignment == "space-between":
        return 0

    raise ValueError(f"Unsupported alignment: {alignment}")


def demonstrate_alignment() -> None:
    print_section("13. Alignment")

    container = 500
    item = 200

    for alignment in ["start", "center", "end"]:
        offset = alignment_offset(container, item, alignment)
        print(
            f"{alignment:>6}: free space={container - item}px, "
            f"item offset={offset}px"
        )

    print("\nImportant Grid alignment properties:")
    print("justify-items -> alignment inside each grid area horizontally")
    print("align-items   -> alignment inside each grid area vertically")
    print("justify-content -> alignment of the entire grid horizontally")
    print("align-content   -> alignment of the entire grid vertically")
    print("justify-self / align-self -> per-item overrides")


# ---------------------------------------------------------------------------
# Section 14: Validation and common mistakes
# ---------------------------------------------------------------------------

def validate_grid_area_name(area_name: str) -> None:
    if not area_name.strip():
        raise ValueError("Grid area names cannot be empty.")

    if area_name.strip() == ".":
        raise ValueError("'.' represents an intentionally empty grid-area cell.")


def demonstrate_errors() -> None:
    print_section("14. Edge cases and common mistakes")

    cases = [
        ("Negative gap", lambda: equal_fraction_tracks(500, 3, -10)),
        ("Zero columns", lambda: equal_fraction_tracks(500, 0, 10)),
        ("Invalid minmax", lambda: minmax_track_size(500, 400, 200)),
        ("Invalid area", lambda: validate_grid_area_name("")),
    ]

    for name, operation in cases:
        try:
            operation()
            print(f"{name}: unexpectedly accepted")
        except ValueError as error:
            print(f"{name}: correctly rejected -> {error}")

    print("\nCommon conceptual mistakes:")
    print("1. Confusing grid lines with grid tracks.")
    print("2. Assuming grid-column: 1 / 3 means one column.")
    print("3. Forgetting that a 4-column grid has 5 vertical grid lines.")
    print("4. Using fixed widths everywhere and then expecting responsiveness.")
    print("5. Assuming gap adds space outside the grid container.")
    print("6. Using grid-template-areas with non-rectangular named regions.")
    print("7. Confusing justify-items with justify-content.")
    print("8. Forgetting that implicit rows can be created automatically.")
    print("9. Using excessive absolute positioning where Grid is more suitable.")
    print("10. Ignoring content minimum sizes when using flexible layouts.")


# ---------------------------------------------------------------------------
# Section 15: Explicit vs implicit grids
# ---------------------------------------------------------------------------

def implicit_row_count(
    explicit_rows: int,
    highest_requested_row: int,
) -> int:
    if explicit_rows < 0:
        raise ValueError("Explicit row count cannot be negative.")
    if highest_requested_row < 1:
        raise ValueError("Requested row must be positive.")

    return max(explicit_rows, highest_requested_row)


def demonstrate_implicit_grid() -> None:
    print_section("15. Explicit and implicit grids")

    explicit_rows = 2
    requested_row = 4

    total_rows = implicit_row_count(explicit_rows, requested_row)

    print(f"Explicit rows: {explicit_rows}")
    print(f"Item requests row: {requested_row}")
    print(f"Resulting conceptual row count: {total_rows}")

    print("\nCSS might begin with:")
    print("grid-template-rows: 100px 200px;")
    print("and later contain an item placed into row 4.")

    print("\nThe browser can create implicit tracks to satisfy placement.")


# ---------------------------------------------------------------------------
# Section 16: Responsive dashboard example
# ---------------------------------------------------------------------------

@dataclass
class DashboardLayout:
    width: int
    gap: int = 20
    minimum_card_width: int = 220

    def column_count(self) -> int:
        return maximum_auto_columns(
            self.width,
            self.minimum_card_width,
            self.gap,
        )

    def card_width(self) -> float:
        columns = self.column_count()
        return (
            self.width - self.gap * (columns - 1)
        ) / columns

    def describe(self) -> None:
        columns = self.column_count()
        width = self.card_width()

        print(
            f"Dashboard width={self.width}px -> "
            f"{columns} columns -> "
            f"approximately {width:.1f}px per card"
        )


def demonstrate_dashboard() -> None:
    print_section("16. Responsive dashboard calculation")

    for width in [375, 768, 1024, 1366, 1920]:
        DashboardLayout(width).describe()

    print("\nA practical CSS strategy is:")
    print("display: grid;")
    print("grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));")
    print("gap: 20px;")

    print("\nThis avoids manually writing a separate column count for every width.")


# ---------------------------------------------------------------------------
# Section 17: Nested grids
# ---------------------------------------------------------------------------

def demonstrate_nested_grids() -> None:
    print_section("17. Nested grids")

    print("A grid item can itself become a grid container.")
    print("\nOuter layout:")
    print("grid-template-columns: 240px 1fr;")

    print("\nInner layout inside the main content:")
    print("grid-template-columns: repeat(3, 1fr);")

    print(
        "\nThis creates independent layout contexts. "
        "The inner grid does not automatically inherit the outer grid's "
        "track definitions."
    )


# ---------------------------------------------------------------------------
# Section 18: Subgrid conceptual explanation
# ---------------------------------------------------------------------------

def demonstrate_subgrid() -> None:
    print_section("18. Subgrid")

    print("subgrid allows a nested grid to participate in track sizing")
    print("from its parent grid.")

    print("\nConceptual CSS:")
    print("grid-template-columns: subgrid;")
    print("grid-template-rows: subgrid;")

    print(
        "\nThis is particularly useful when repeated components need "
        "their internal content aligned to shared parent tracks."
    )

    print(
        "\nImportant distinction: a normal nested grid creates its own "
        "independent tracks, whereas subgrid can reuse parent track sizing."
    )


# ---------------------------------------------------------------------------
# Section 19: Practical layout design
# ---------------------------------------------------------------------------

def design_practical_layout() -> None:
    print_section("19. Practical layout design")

    layout = Grid(rows=5, columns=12, row_gap=16, column_gap=16)

    layout.add_item(GridItem("Header", row=1, column=1, column_span=12))
    layout.add_item(GridItem("Nav", row=2, column=1, column_span=3))
    layout.add_item(GridItem("Main", row=2, column=4, column_span=6, row_span=3))
    layout.add_item(GridItem("Aside", row=2, column=10, column_span=3, row_span=3))
    layout.add_item(GridItem("Footer", row=5, column=1, column_span=12))

    layout.display()

    print("\nThis resembles a responsive application shell:")
    print("- Header")
    print("- Navigation")
    print("- Main content")
    print("- Secondary content")
    print("- Footer")

    print("\nThe twelve-column approach is common because it offers many")
    print("divisions while remaining easy to reason about.")


# ---------------------------------------------------------------------------
# Section 20: Performance considerations
# ---------------------------------------------------------------------------

def demonstrate_performance_considerations() -> None:
    print_section("20. Performance and production considerations")

    considerations = [
        "Avoid unnecessary deeply nested layout structures.",
        "Use Grid for two-dimensional layout rather than forcing it to replace every layout mechanism.",
        "Prefer reusable layout rules instead of hundreds of one-off placement declarations.",
        "Be aware that intrinsic sizing can require the browser to inspect content.",
        "Large dynamic grids should be tested with realistic content and viewport sizes.",
        "Avoid creating unnecessary DOM elements solely to obtain visual spacing.",
        "Use gap for grid spacing rather than margin hacks when the spacing belongs between tracks.",
        "Test long text, large images, empty states, and localization because intrinsic sizing can change track behavior.",
    ]

    for number, item in enumerate(considerations, start=1):
        print(f"{number}. {item}")


# ---------------------------------------------------------------------------
# Section 21: Accessibility considerations
# ---------------------------------------------------------------------------

def demonstrate_accessibility() -> None:
    print_section("21. Accessibility considerations")

    print("CSS Grid changes visual placement, not the semantic meaning of HTML.")
    print("\nImportant principles:")
    print("1. Use semantic HTML elements where appropriate.")
    print("2. Do not use visual reordering to create a confusing reading order.")
    print("3. Keep keyboard navigation and source order logical.")
    print("4. Ensure interactive controls remain discoverable.")
    print("5. Test layouts at narrow widths and with zoom.")
    print("6. Do not assume a visually attractive grid is automatically accessible.")


# ---------------------------------------------------------------------------
# Section 22: Complete study demonstration
# ---------------------------------------------------------------------------

def run_study() -> None:
    print_section("CSS GRID FUNDAMENTALS - PYTHON STUDY PROGRAM")
    print("This program models CSS Grid concepts without requiring a browser.")

    explain_fundamentals()
    demonstrate_basic_grid()
    demonstrate_grid_lines()
    demonstrate_gaps_and_fr()
    demonstrate_weighted_fr()
    demonstrate_mixed_tracks()
    demonstrate_minmax()
    demonstrate_repeat()
    demonstrate_responsive_columns()
    demonstrate_grid_areas()
    demonstrate_auto_placement()
    demonstrate_spanning_area()
    demonstrate_alignment()
    demonstrate_errors()
    demonstrate_implicit_grid()
    demonstrate_dashboard()
    demonstrate_nested_grids()
    demonstrate_subgrid()
    design_practical_layout()
    demonstrate_performance_considerations()
    demonstrate_accessibility()

    print_section("23. Final reference")

    print("Core properties:")
    print("display: grid")
    print("grid-template-columns")
    print("grid-template-rows")
    print("grid-template-areas")
    print("grid-column")
    print("grid-row")
    print("grid-area")
    print("gap")
    print("row-gap")
    print("column-gap")
    print("grid-auto-columns")
    print("grid-auto-rows")
    print("grid-auto-flow")
    print("justify-items")
    print("align-items")
    print("justify-content")
    print("align-content")
    print("justify-self")
    print("align-self")

    print("\nCore sizing concepts:")
    print("px       -> fixed length")
    print("%        -> percentage-based sizing")
    print("fr       -> flexible fraction of available grid space")
    print("auto     -> content/intrinsic and available-space dependent sizing")
    print("minmax() -> bounded track sizing")
    print("repeat() -> repeated track definitions")
    print("auto-fit -> responsive track fitting")
    print("auto-fill -> responsive track filling")

    print("\nThe essential mental model:")
    print("Container -> tracks -> cells -> placement -> areas -> alignment")
    print("Responsive behavior comes from combining these mechanisms with")
    print("flexible and bounded track sizing.")


if __name__ == "__main__":
    run_study()
