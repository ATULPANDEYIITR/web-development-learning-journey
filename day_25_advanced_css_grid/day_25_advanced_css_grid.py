"""
Advanced CSS Grid Study and Demonstration
==========================================

This standalone Python script teaches advanced CSS Grid concepts by:
1. Explaining the conceptual model through executable examples.
2. Generating CSS Grid declarations and complete responsive examples.
3. Simulating responsive track calculations such as minmax().
4. Demonstrating auto-fit, auto-fill, explicit and implicit grids.
5. Modeling complex dashboard layouts.
6. Validating common Grid configurations.
7. Measuring layout-planning performance.
8. Providing progressively more advanced practical examples.

The generated CSS is intentionally kept in Python strings so that the
script remains self-contained and requires no external packages.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import floor
from textwrap import dedent
from typing import Iterable


# ---------------------------------------------------------------------------
# 1. FUNDAMENTAL DATA TYPES
# ---------------------------------------------------------------------------

@dataclass
class GridItem:
    """Represents an item that participates in a CSS Grid layout."""

    name: str
    column_start: int | str = "auto"
    column_end: int | str = "auto"
    row_start: int | str = "auto"
    row_end: int | str = "auto"

    def placement_css(self) -> str:
        """Return the item's explicit placement declarations."""
        return (
            f".{self.name} {{\n"
            f"  grid-column: {self.column_start} / {self.column_end};\n"
            f"  grid-row: {self.row_start} / {self.row_end};\n"
            f"}}"
        )


@dataclass
class GridConfiguration:
    """A small model of the most important Grid container properties."""

    width_px: int
    gap_px: int
    min_track_px: int
    max_track_px: int | str = "1fr"
    item_count: int = 0

    def auto_fit_columns(self) -> int:
        """
        Approximate how many minimum-sized tracks fit into the container.

        This is a conceptual calculation rather than a browser layout engine.
        The browser also considers intrinsic sizing, min-content constraints,
        borders, padding, and the exact track-sizing algorithm.
        """
        if self.width_px <= 0 or self.min_track_px <= 0:
            return 0

        return max(
            1,
            floor((self.width_px + self.gap_px) /
                  (self.min_track_px + self.gap_px))
        )

    def describe(self) -> str:
        columns = self.auto_fit_columns()
        return (
            f"Container: {self.width_px}px\n"
            f"Gap: {self.gap_px}px\n"
            f"Minimum track: {self.min_track_px}px\n"
            f"Approximate fitting tracks: {columns}\n"
            f"Grid definition: "
            f"repeat(auto-fit, minmax({self.min_track_px}px, "
            f"{self.max_track_px}))"
        )


# ---------------------------------------------------------------------------
# 2. CSS GENERATION HELPERS
# ---------------------------------------------------------------------------

def make_grid_css(
    columns: str,
    rows: str = "auto",
    gap: str = "1rem",
    auto_flow: str = "row",
    align_items: str = "stretch",
    justify_items: str = "stretch",
) -> str:
    """Generate a reusable CSS Grid container rule."""
    return dedent(
        f"""
        .grid {{
          display: grid;
          grid-template-columns: {columns};
          grid-template-rows: {rows};
          gap: {gap};
          grid-auto-flow: {auto_flow};
          align-items: {align_items};
          justify-items: {justify_items};
        }}
        """
    ).strip()


def generate_responsive_card_grid() -> str:
    """
    minmax() prevents cards from becoming narrower than 16rem while allowing
    each track to grow when extra space is available.

    auto-fit collapses empty repeated tracks, allowing existing cards to grow.
    """
    return dedent(
        """
        .card-grid {
          display: grid;
          grid-template-columns: repeat(
            auto-fit,
            minmax(16rem, 1fr)
          );
          gap: 1rem;
        }
        """
    ).strip()


def generate_auto_fill_grid() -> str:
    """
    auto-fill preserves the conceptual repeated track structure even when
    there are fewer items than the available number of tracks.
    """
    return dedent(
        """
        .card-grid {
          display: grid;
          grid-template-columns: repeat(
            auto-fill,
            minmax(16rem, 1fr)
          );
          gap: 1rem;
        }
        """
    ).strip()


def generate_implicit_grid() -> str:
    """
    Explicit rows are declared by grid-template-rows.
    Extra rows created because more items exist are implicit rows.
    grid-auto-rows controls their size.
    """
    return dedent(
        """
        .implicit-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          grid-template-rows: 100px;
          grid-auto-rows: minmax(80px, auto);
          gap: 1rem;
        }
        """
    ).strip()


# ---------------------------------------------------------------------------
# 3. minmax() EXAMPLES
# ---------------------------------------------------------------------------

def demonstrate_minmax() -> None:
    print("\n=== minmax() ===")

    examples = [
        "minmax(200px, 1fr)",
        "minmax(12rem, 30rem)",
        "minmax(min-content, 1fr)",
        "minmax(0, 1fr)",
    ]

    for expression in examples:
        print(f"Track sizing function: {expression}")

    print(
        """
minmax(minimum, maximum) defines a lower and upper sizing limit.

Examples:
  minmax(200px, 1fr)
    -> The track should not shrink below 200px.
    -> Remaining space can be distributed through 1fr.

  minmax(12rem, 30rem)
    -> The track has a bounded maximum.

  minmax(0, 1fr)
    -> Useful when long content should not force a flexible track
       beyond the intended grid width.

Important distinction:
  1fr is a flexible maximum when used inside minmax().
  minmax() is not itself a breakpoint mechanism.
        """
    )


# ---------------------------------------------------------------------------
# 4. auto-fit VS auto-fill
# ---------------------------------------------------------------------------

def demonstrate_auto_fit_vs_auto_fill() -> None:
    print("\n=== auto-fit versus auto-fill ===")

    print(
        """
Both keywords are commonly used with repeat().

Typical pattern:

  repeat(auto-fit, minmax(16rem, 1fr))
  repeat(auto-fill, minmax(16rem, 1fr))

auto-fit:
  - Creates as many tracks as can fit.
  - Empty repeated tracks are collapsed.
  - Existing items can expand into the freed space.

auto-fill:
  - Creates as many tracks as can fit.
  - Empty tracks remain conceptually available.
  - This can preserve track geometry even when there are fewer items.

The difference becomes visible when the container can hold more columns
than there are grid items.
        """
    )

    for width in [320, 640, 960, 1280]:
        configuration = GridConfiguration(
            width_px=width,
            gap_px=16,
            min_track_px=240,
            item_count=5,
        )
        print(
            f"{width:4}px -> "
            f"approximately {configuration.auto_fit_columns()} minimum tracks"
        )


# ---------------------------------------------------------------------------
# 5. EXPLICIT AND IMPLICIT GRIDS
# ---------------------------------------------------------------------------

def demonstrate_implicit_grid() -> None:
    print("\n=== Explicit and implicit grids ===")

    print(
        """
Explicit grid:
  The developer defines tracks directly using:
    grid-template-columns
    grid-template-rows

Implicit grid:
  The browser creates additional rows or columns when placement requires
  tracks that were not explicitly declared.

Useful properties:
  grid-auto-rows
  grid-auto-columns
  grid-auto-flow

Example:
        """
    )

    print(generate_implicit_grid())

    print(
        """
If the explicit grid contains three columns but ten items are inserted,
the first three items occupy the first row, the next three occupy the
second row, and so on, unless explicit placement changes the result.

grid-auto-flow: row
  Fills available columns before creating another row.

grid-auto-flow: column
  Fills available rows before creating another column.

grid-auto-flow: dense
  Allows later smaller items to backfill earlier holes.

The dense mode can improve visual packing but can create a visual ordering
that differs from source/document order, which matters for accessibility.
        """
    )


# ---------------------------------------------------------------------------
# 6. RESPONSIVE GRID MODEL
# ---------------------------------------------------------------------------

def estimate_grid_columns(
    container_width: int,
    minimum_card_width: int,
    gap: int,
) -> int:
    """
    Estimate the number of columns a browser can fit.

    This is deliberately approximate. Real CSS Grid uses the complete track
    sizing algorithm and considers intrinsic sizing constraints.
    """
    if container_width <= 0 or minimum_card_width <= 0:
        raise ValueError("Widths must be positive.")

    if gap < 0:
        raise ValueError("Gap cannot be negative.")

    return max(
        1,
        (container_width + gap) // (minimum_card_width + gap)
    )


def demonstrate_responsive_behavior() -> None:
    print("\n=== Responsive Grid ===")

    widths = [360, 480, 768, 1024, 1440, 1920]
    minimum = 240
    gap = 24

    for width in widths:
        columns = estimate_grid_columns(width, minimum, gap)
        print(
            f"Viewport {width:4}px -> approximately "
            f"{columns} column(s)"
        )

    print(
        """
A content-driven responsive grid can often avoid explicit media queries:

  grid-template-columns:
    repeat(auto-fit, minmax(240px, 1fr));

This means the layout responds to available inline space instead of requiring
a separate breakpoint for every viewport size.
        """
    )


# ---------------------------------------------------------------------------
# 7. COMPLEX NAMED-AREA LAYOUT
# ---------------------------------------------------------------------------

def generate_dashboard_layout() -> str:
    """Generate a practical named-area dashboard layout."""
    return dedent(
        """
        .dashboard {
          display: grid;
          grid-template-columns:
            minmax(14rem, 18rem)
            minmax(0, 1fr)
            minmax(16rem, 24rem);

          grid-template-rows:
            auto
            minmax(20rem, 1fr)
            auto;

          grid-template-areas:
            "sidebar header header"
            "sidebar main   aside"
            "sidebar footer footer";

          min-height: 100vh;
          gap: 1rem;
        }

        .dashboard-header { grid-area: header; }
        .dashboard-sidebar { grid-area: sidebar; }
        .dashboard-main { grid-area: main; }
        .dashboard-aside { grid-area: aside; }
        .dashboard-footer { grid-area: footer; }

        @media (max-width: 900px) {
          .dashboard {
            grid-template-columns: 1fr;
            grid-template-areas:
              "header"
              "main"
              "aside"
              "sidebar"
              "footer";
          }
        }
        """
    ).strip()


def demonstrate_named_areas() -> None:
    print("\n=== Complex named-area layout ===")
    print(generate_dashboard_layout())


# ---------------------------------------------------------------------------
# 8. GRID ITEM PLACEMENT
# ---------------------------------------------------------------------------

def demonstrate_item_placement() -> None:
    print("\n=== Grid item placement ===")

    items = [
        GridItem("header", 1, -1, 1, 2),
        GridItem("sidebar", 1, 2, 2, -1),
        GridItem("content", 2, 4, 2, 3),
        GridItem("aside", 4, 5, 2, 3),
        GridItem("footer", 1, -1, 3, 4),
    ]

    for item in items:
        print(item.placement_css())
        print()


# ---------------------------------------------------------------------------
# 9. SUBGRID
# ---------------------------------------------------------------------------

def demonstrate_subgrid() -> None:
    print("\n=== subgrid ===")

    print(
        """
subgrid allows a nested grid to participate in the track sizing of its
parent grid.

Example:

  .cards {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
  }

  .card {
    display: grid;
    grid-template-rows: subgrid;
    grid-row: span 3;
  }

This is useful when repeated components must align internal headings,
content, and actions across multiple cards.

subgrid is different from simply declaring another independent grid:
the nested grid can inherit the relevant track sizing from its parent.
        """
    )


# ---------------------------------------------------------------------------
# 10. EDGE CASES
# ---------------------------------------------------------------------------

def demonstrate_edge_cases() -> None:
    print("\n=== Edge cases ===")

    test_cases = [
        (0, 240, 16),
        (500, 0, 16),
        (500, 240, -1),
        (500, 240, 16),
        (1200, 240, 24),
    ]

    for width, minimum, gap in test_cases:
        try:
            columns = estimate_grid_columns(width, minimum, gap)
            print(
                f"width={width}, min={minimum}, gap={gap} "
                f"-> {columns} column(s)"
            )
        except ValueError as error:
            print(
                f"width={width}, min={minimum}, gap={gap} "
                f"-> validation error: {error}"
            )

    print(
        """
Important CSS edge cases:

1. A long unbreakable string can create overflow.
2. A flexible track can interact with intrinsic minimum sizes.
3. minmax(0, 1fr) is often useful for preventing content from imposing
   an unexpectedly large minimum.
4. Spanning items can influence track sizing.
5. Percentage tracks interact with the grid container's definite size.
6. Implicit tracks can appear unexpectedly when placement exceeds the
   explicit grid.
7. Dense auto-placement can alter visual placement without changing
   source order.
8. Negative line numbers count from the end of the explicit grid.
        """
    )


# ---------------------------------------------------------------------------
# 11. COMMON MISTAKES
# ---------------------------------------------------------------------------

def demonstrate_common_mistakes() -> None:
    print("\n=== Common mistakes ===")

    mistakes = {
        "Using fixed widths everywhere":
            "Prefer flexible tracks where content and viewport size vary.",
        "Ignoring intrinsic content":
            "Consider minmax(0, 1fr) when long content causes overflow.",
        "Confusing auto-fit with auto-fill":
            "Test both with fewer items than available tracks.",
        "Overusing media queries":
            "Try content-driven repeat(auto-fit, minmax(...)) first.",
        "Forgetting implicit tracks":
            "Inspect grid-auto-rows and grid-auto-columns.",
        "Using dense without considering reading order":
            "Visual packing must not create a confusing interaction order.",
        "Hard-coding every item":
            "Use Grid's automatic placement when repeated content is involved.",
    }

    for mistake, correction in mistakes.items():
        print(f"- {mistake}: {correction}")


# ---------------------------------------------------------------------------
# 12. PERFORMANCE CONSIDERATIONS
# ---------------------------------------------------------------------------

def benchmark_track_estimation(iterations: int = 100_000) -> None:
    """
    Benchmark the small mathematical model.

    This does not benchmark the browser's CSS engine. It demonstrates why
    developers should distinguish their own application calculations from
    browser layout performance.
    """
    import time

    start = time.perf_counter()

    total = 0

    for index in range(iterations):
        width = 320 + (index % 1800)
        total += estimate_grid_columns(width, 240, 16)

    elapsed = time.perf_counter() - start

    print("\n=== Performance demonstration ===")
    print(f"Iterations: {iterations:,}")
    print(f"Calculated result checksum: {total:,}")
    print(f"Python calculation time: {elapsed:.6f} seconds")

    print(
        """
Browser performance considerations:

- Avoid unnecessary DOM mutations.
- Batch changes when updating many grid items.
- Prefer CSS-driven responsiveness over JavaScript resize handlers when
  possible.
- Use CSS containment carefully when isolating large layout regions.
- Avoid repeatedly reading layout properties immediately after writes,
  because mixing reads and writes can contribute to layout thrashing.
- Large complex grids can require substantial layout work, especially when
  content has intrinsic sizing constraints.
        """
    )


# ---------------------------------------------------------------------------
# 13. ACCESSIBILITY
# ---------------------------------------------------------------------------

def demonstrate_accessibility() -> None:
    print("\n=== Accessibility considerations ===")

    print(
        """
CSS Grid changes visual placement but does not inherently change DOM order.

Good practice:
  - Keep logical content order in the HTML.
  - Use grid-area and placement primarily for visual layout.
  - Do not use Grid to create a confusing keyboard sequence.
  - Test keyboard navigation.
  - Test screen-reader interpretation.
  - Be careful with grid-auto-flow: dense.
  - Ensure focus indicators remain visible.
  - Do not communicate essential meaning solely through spatial placement.
        """
    )


# ---------------------------------------------------------------------------
# 14. PRODUCTION-STYLE CSS
# ---------------------------------------------------------------------------

def generate_production_example() -> str:
    """Return a production-oriented responsive component grid."""
    return dedent(
        """
        :root {
          --content-max-width: 90rem;
          --grid-gap: clamp(0.75rem, 2vw, 1.5rem);
          --card-min-width: 16rem;
        }

        .content-grid {
          width: min(100% - 2rem, var(--content-max-width));
          margin-inline: auto;

          display: grid;
          grid-template-columns:
            repeat(
              auto-fit,
              minmax(
                min(var(--card-min-width), 100%),
                1fr
              )
            );

          gap: var(--grid-gap);
        }

        .content-card {
          min-width: 0;
          display: grid;
          grid-template-rows: auto 1fr auto;
          gap: 0.75rem;
        }

        .content-card__body {
          overflow-wrap: anywhere;
        }

        .content-card__action {
          justify-self: start;
        }
        """
    ).strip()


# ---------------------------------------------------------------------------
# 15. COMPLETE STUDY CSS COLLECTION
# ---------------------------------------------------------------------------

def print_css_library() -> None:
    print("\n=== CSS Grid study library ===")

    snippets = {
        "Basic flexible grid": make_grid_css(
            "repeat(3, 1fr)",
            gap="1rem",
        ),
        "Responsive auto-fit": generate_responsive_card_grid(),
        "Responsive auto-fill": generate_auto_fill_grid(),
        "Implicit tracks": generate_implicit_grid(),
        "Production card grid": generate_production_example(),
    }

    for title, css in snippets.items():
        print(f"\n--- {title} ---")
        print(css)


# ---------------------------------------------------------------------------
# 16. MINI TEST SUITE
# ---------------------------------------------------------------------------

def run_tests() -> None:
    """Run basic assertions so the study file validates its own model."""

    assert estimate_grid_columns(500, 240, 16) == 1
    assert estimate_grid_columns(800, 240, 16) == 3
    assert estimate_grid_columns(1200, 240, 16) == 4

    configuration = GridConfiguration(
        width_px=1000,
        gap_px=20,
        min_track_px=200,
    )

    assert configuration.auto_fit_columns() >= 1

    try:
        estimate_grid_columns(-1, 240, 16)
    except ValueError:
        pass
    else:
        raise AssertionError("Negative container width should fail.")

    try:
        estimate_grid_columns(800, 240, -1)
    except ValueError:
        pass
    else:
        raise AssertionError("Negative gap should fail.")

    print("\n=== Tests ===")
    print("All Python model tests passed.")


# ---------------------------------------------------------------------------
# 17. STUDY CHECKLIST
# ---------------------------------------------------------------------------

def print_study_checklist() -> None:
    print("\n=== Advanced CSS Grid checklist ===")

    checklist = [
        "Understand grid container versus grid item.",
        "Understand grid lines, tracks, cells, and areas.",
        "Use repeat() effectively.",
        "Use minmax() to express minimum and flexible maximum sizes.",
        "Understand fr units.",
        "Understand auto-fit.",
        "Understand auto-fill.",
        "Understand explicit tracks.",
        "Understand implicit rows and columns.",
        "Use grid-auto-rows and grid-auto-columns.",
        "Understand grid-auto-flow.",
        "Use named grid areas.",
        "Use line-based placement.",
        "Understand spanning.",
        "Use minmax(0, 1fr) when appropriate.",
        "Consider intrinsic sizing and overflow.",
        "Understand dense placement and source order.",
        "Use subgrid where supported and appropriate.",
        "Keep HTML source order logical.",
        "Prefer CSS-driven responsiveness where practical.",
        "Inspect performance for very large or complex grids.",
    ]

    for number, item in enumerate(checklist, start=1):
        print(f"{number:02d}. {item}")


# ---------------------------------------------------------------------------
# 18. MAIN PROGRAM
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 78)
    print("ADVANCED CSS GRID: COMPLETE PYTHON STUDY FILE")
    print("=" * 78)

    demonstrate_minmax()
    demonstrate_auto_fit_vs_auto_fill()
    demonstrate_implicit_grid()
    demonstrate_responsive_behavior()
    demonstrate_named_areas()
    demonstrate_item_placement()
    demonstrate_subgrid()
    demonstrate_edge_cases()
    demonstrate_common_mistakes()
    benchmark_track_estimation()
    demonstrate_accessibility()
    print_css_library()
    run_tests()
    print_study_checklist()

    print("\n=== Final generated responsive Grid rule ===")
    print(generate_responsive_card_grid())

    print("\nStudy execution completed successfully.")


if __name__ == "__main__":
    main()
