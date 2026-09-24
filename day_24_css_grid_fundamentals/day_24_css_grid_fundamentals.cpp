/*
 * CSS Grid Fundamentals - C++ Technical Case Study
 *
 * Scenario:
 * ---------
 * A web application dashboard must calculate and validate a responsive
 * twelve-column CSS Grid layout before its configuration is sent to a
 * frontend renderer.
 *
 * The C++ program models:
 *
 * - Grid containers
 * - Rows and columns
 * - Grid tracks
 * - Grid cells
 * - Grid lines
 * - Gaps
 * - Explicit placement
 * - Spanning
 * - Named grid areas
 * - Responsive column calculation
 * - Track sizing
 * - Collision detection
 * - Layout validation
 * - Error handling
 * - Complexity analysis
 *
 * The program does not render HTML or CSS. It models the layout engine
 * decisions that a frontend system could use when producing CSS.
 *
 * Compile:
 *   g++ -std=c++17 -O2 css_grid_case_study.cpp -o css_grid_case_study
 */

#include <algorithm>
#include <cmath>
#include <exception>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <tuple>
#include <utility>
#include <vector>

using namespace std;


// -----------------------------------------------------------------------------
// Basic data structures
// -----------------------------------------------------------------------------

struct Track {
    double size = 0.0;
    string sizingFunction;

    Track() = default;

    Track(double sizeValue, string function)
        : size(sizeValue), sizingFunction(std::move(function)) {}
};


struct GridItem {
    string id;
    string areaName;

    int rowStart = 0;
    int columnStart = 0;
    int rowSpan = 1;
    int columnSpan = 1;

    bool explicitlyPositioned = false;

    GridItem(
        string itemId,
        int row,
        int column,
        int rows = 1,
        int columns = 1,
        string area = "",
        bool explicitPlacement = true
    )
        : id(std::move(itemId)),
          areaName(std::move(area)),
          rowStart(row),
          columnStart(column),
          rowSpan(rows),
          columnSpan(columns),
          explicitlyPositioned(explicitPlacement) {}
};


struct Cell {
    int row = 0;
    int column = 0;

    bool operator<(const Cell& other) const {
        return tie(row, column) < tie(other.row, other.column);
    }

    bool operator==(const Cell& other) const {
        return row == other.row && column == other.column;
    }
};


// -----------------------------------------------------------------------------
// Grid layout engine
// -----------------------------------------------------------------------------

class GridLayoutEngine {
private:
    int explicitRows;
    int explicitColumns;

    double containerWidth;
    double containerHeight;

    double rowGap;
    double columnGap;

    vector<Track> rows;
    vector<Track> columns;
    vector<GridItem> items;

    set<Cell> occupiedCells;

public:
    GridLayoutEngine(
        int rowCount,
        int columnCount,
        double width,
        double height,
        double rowGapValue,
        double columnGapValue
    )
        : explicitRows(rowCount),
          explicitColumns(columnCount),
          containerWidth(width),
          containerHeight(height),
          rowGap(rowGapValue),
          columnGap(columnGapValue) {

        if (rowCount <= 0 || columnCount <= 0) {
            throw invalid_argument(
                "Grid must contain at least one row and one column."
            );
        }

        if (width <= 0 || height <= 0) {
            throw invalid_argument(
                "Container dimensions must be positive."
            );
        }

        if (rowGapValue < 0 || columnGapValue < 0) {
            throw invalid_argument(
                "Grid gaps cannot be negative."
            );
        }
    }


    // -------------------------------------------------------------------------
    // Equal 1fr track calculation
    // -------------------------------------------------------------------------

    vector<Track> createEqualFractionTracks(
        double availableSize,
        int trackCount,
        double gap
    ) const {
        if (trackCount <= 0) {
            throw invalid_argument(
                "Track count must be positive."
            );
        }

        if (availableSize < 0 || gap < 0) {
            throw invalid_argument(
                "Available size and gap cannot be negative."
            );
        }

        const double totalGap =
            static_cast<double>(trackCount - 1) * gap;

        const double remaining =
            availableSize - totalGap;

        if (remaining < -1e-9) {
            throw invalid_argument(
                "Gaps consume more space than the container provides."
            );
        }

        const double size =
            max(0.0, remaining) /
            static_cast<double>(trackCount);

        vector<Track> result;

        for (int i = 0; i < trackCount; ++i) {
            result.emplace_back(size, "1fr");
        }

        return result;
    }


    // -------------------------------------------------------------------------
    // Weighted fr track calculation
    // -------------------------------------------------------------------------

    vector<Track> createWeightedFractionTracks(
        double availableSize,
        const vector<double>& fractions,
        double gap
    ) const {
        if (fractions.empty()) {
            throw invalid_argument(
                "At least one fraction is required."
            );
        }

        if (gap < 0 || availableSize < 0) {
            throw invalid_argument(
                "Available size and gap cannot be negative."
            );
        }

        double fractionTotal = 0.0;

        for (double fraction : fractions) {
            if (!isfinite(fraction) || fraction <= 0) {
                throw invalid_argument(
                    "Every fr value must be positive."
                );
            }

            fractionTotal += fraction;
        }

        const double totalGap =
            static_cast<double>(fractions.size() - 1) * gap;

        const double remaining =
            availableSize - totalGap;

        if (remaining < -1e-9) {
            throw invalid_argument(
                "Gaps consume too much available space."
            );
        }

        vector<Track> result;

        for (double fraction : fractions) {
            const double size =
                max(0.0, remaining) *
                fraction /
                fractionTotal;

            ostringstream functionName;
            functionName << fraction << "fr";

            result.emplace_back(
                size,
                functionName.str()
            );
        }

        return result;
    }


    // -------------------------------------------------------------------------
    // Explicit track setup
    // -------------------------------------------------------------------------

    void configureEqualTracks() {
        const double rowTrackSpace =
            containerHeight -
            static_cast<double>(explicitRows - 1) * rowGap;

        const double columnTrackSpace =
            containerWidth -
            static_cast<double>(explicitColumns - 1) * columnGap;

        rows = createEqualFractionTracks(
            rowTrackSpace + (explicitRows - 1) * rowGap,
            explicitRows,
            rowGap
        );

        columns = createEqualFractionTracks(
            columnTrackSpace + (explicitColumns - 1) * columnGap,
            explicitColumns,
            columnGap
        );
    }


    // -------------------------------------------------------------------------
    // Placement validation
    // -------------------------------------------------------------------------

    bool isInsideExplicitGrid(const GridItem& item) const {
        if (item.rowStart < 1 ||
            item.columnStart < 1 ||
            item.rowSpan <= 0 ||
            item.columnSpan <= 0) {
            return false;
        }

        const int rowEnd =
            item.rowStart + item.rowSpan - 1;

        const int columnEnd =
            item.columnStart + item.columnSpan - 1;

        return rowEnd <= explicitRows &&
               columnEnd <= explicitColumns;
    }


    vector<Cell> cellsFor(const GridItem& item) const {
        vector<Cell> cells;

        for (
            int row = item.rowStart;
            row < item.rowStart + item.rowSpan;
            ++row
        ) {
            for (
                int column = item.columnStart;
                column < item.columnStart + item.columnSpan;
                ++column
            ) {
                cells.push_back({row, column});
            }
        }

        return cells;
    }


    void placeItem(const GridItem& item) {
        if (!isInsideExplicitGrid(item)) {
            throw out_of_range(
                "Item '" + item.id +
                "' extends outside the explicit grid."
            );
        }

        const vector<Cell> cells = cellsFor(item);

        for (const Cell& cell : cells) {
            if (occupiedCells.count(cell) != 0) {
                throw logic_error(
                    "Grid collision detected for item '" +
                    item.id + "'."
                );
            }
        }

        for (const Cell& cell : cells) {
            occupiedCells.insert(cell);
        }

        items.push_back(item);
    }


    // -------------------------------------------------------------------------
    // Automatic placement
    // -------------------------------------------------------------------------

    pair<int, int> findNextFreeCell() const {
        for (int row = 1; row <= explicitRows; ++row) {
            for (int column = 1; column <= explicitColumns; ++column) {
                Cell cell{row, column};

                if (occupiedCells.count(cell) == 0) {
                    return {row, column};
                }
            }
        }

        throw overflow_error(
            "No free cell remains in the explicit grid."
        );
    }


    void autoPlaceItem(
        const string& itemId,
        const string& area = ""
    ) {
        const auto [row, column] = findNextFreeCell();

        GridItem item(
            itemId,
            row,
            column,
            1,
            1,
            area,
            false
        );

        placeItem(item);
    }


    // -------------------------------------------------------------------------
    // Grid rendering
    // -------------------------------------------------------------------------

    vector<vector<string>> occupancyMap() const {
        vector<vector<string>> grid(
            explicitRows,
            vector<string>(explicitColumns, ".")
        );

        for (const GridItem& item : items) {
            for (const Cell& cell : cellsFor(item)) {
                grid[cell.row - 1][cell.column - 1] =
                    item.id;
            }
        }

        return grid;
    }


    void printGrid() const {
        const auto grid = occupancyMap();

        cout << "\nGrid occupancy:\n\n";

        cout << "      ";

        for (int column = 1; column <= explicitColumns; ++column) {
            cout
                << setw(12)
                << ("C" + to_string(column));
        }

        cout << "\n";

        for (int row = 0; row < explicitRows; ++row) {
            cout << setw(5)
                 << ("R" + to_string(row + 1))
                 << " ";

            for (int column = 0;
                 column < explicitColumns;
                 ++column) {

                string label = grid[row][column];

                if (label.size() > 10) {
                    label = label.substr(0, 10);
                }

                cout
                    << setw(12)
                    << label;
            }

            cout << "\n";
        }
    }


    // -------------------------------------------------------------------------
    // CSS generation
    // -------------------------------------------------------------------------

    string generateCSS() const {
        ostringstream css;

        css << fixed << setprecision(2);

        css << ".dashboard {\n";
        css << "    display: grid;\n";
        css << "    grid-template-columns: repeat("
            << explicitColumns
            << ", minmax(0, 1fr));\n";

        css << "    grid-template-rows: repeat("
            << explicitRows
            << ", minmax(0, 1fr));\n";

        css << "    column-gap: "
            << columnGap
            << "px;\n";

        css << "    row-gap: "
            << rowGap
            << "px;\n";

        css << "}\n\n";

        for (const GridItem& item : items) {
            css << ".dashboard ." << item.id << " {\n";
            css << "    grid-column: "
                << item.columnStart
                << " / span "
                << item.columnSpan
                << ";\n";

            css << "    grid-row: "
                << item.rowStart
                << " / span "
                << item.rowSpan
                << ";\n";

            css << "}\n\n";
        }

        return css.str();
    }


    // -------------------------------------------------------------------------
    // Track information
    // -------------------------------------------------------------------------

    void printTrackInformation() const {
        cout << "\nColumn tracks:\n";

        for (size_t index = 0; index < columns.size(); ++index) {
            cout
                << "  Column "
                << index + 1
                << ": "
                << fixed
                << setprecision(2)
                << columns[index].size
                << "px ("
                << columns[index].sizingFunction
                << ")\n";
        }

        cout << "\nRow tracks:\n";

        for (size_t index = 0; index < rows.size(); ++index) {
            cout
                << "  Row "
                << index + 1
                << ": "
                << fixed
                << setprecision(2)
                << rows[index].size
                << "px ("
                << rows[index].sizingFunction
                << ")\n";
        }
    }


    // -------------------------------------------------------------------------
    // Grid-line explanation
    // -------------------------------------------------------------------------

    void printGridLines() const {
        cout << "\nGrid line counts:\n";
        cout << "  Horizontal lines: "
             << explicitRows + 1
             << "\n";

        cout << "  Vertical lines: "
             << explicitColumns + 1
             << "\n";

        cout << "\nExample:\n";
        cout << "  grid-column: 2 / 5;\n";
        cout << "  occupies column tracks 2, 3, and 4.\n";
    }


    // -------------------------------------------------------------------------
    // Responsive auto-fit calculation
    // -------------------------------------------------------------------------

    static int responsiveColumnCount(
        double containerWidth,
        double minimumTrackWidth,
        double gap
    ) {
        if (containerWidth <= 0 ||
            minimumTrackWidth <= 0 ||
            gap < 0) {
            throw invalid_argument(
                "Invalid responsive grid dimensions."
            );
        }

        const double numerator =
            containerWidth + gap;

        const double denominator =
            minimumTrackWidth + gap;

        return max(
            1,
            static_cast<int>(
                floor(numerator / denominator)
            )
        );
    }


    // -------------------------------------------------------------------------
    // Debug information
    // -------------------------------------------------------------------------

    void printItemDetails() const {
        cout << "\nPlaced grid items:\n";

        for (const GridItem& item : items) {
            cout
                << "  "
                << item.id
                << ": row "
                << item.rowStart
                << ", column "
                << item.columnStart
                << ", row span "
                << item.rowSpan
                << ", column span "
                << item.columnSpan;

            if (!item.areaName.empty()) {
                cout
                    << ", area='"
                    << item.areaName
                    << "'";
            }

            cout << "\n";
        }
    }
};


// -----------------------------------------------------------------------------
// Named grid-area validation
// -----------------------------------------------------------------------------

class GridAreaTemplate {
private:
    vector<vector<string>> cells;

public:
    explicit GridAreaTemplate(
        vector<vector<string>> values
    )
        : cells(std::move(values)) {

        if (cells.empty()) {
            throw invalid_argument(
                "Grid-area template cannot be empty."
            );
        }

        const size_t width = cells.front().size();

        if (width == 0) {
            throw invalid_argument(
                "Grid-area rows cannot be empty."
            );
        }

        for (const auto& row : cells) {
            if (row.size() != width) {
                throw invalid_argument(
                    "All grid-area rows must have equal width."
                );
            }
        }
    }


    bool isRectangular(const string& areaName) const {
        vector<pair<int, int>> positions;

        for (size_t row = 0; row < cells.size(); ++row) {
            for (size_t column = 0;
                 column < cells[row].size();
                 ++column) {

                if (cells[row][column] == areaName) {
                    positions.emplace_back(
                        static_cast<int>(row),
                        static_cast<int>(column)
                    );
                }
            }
        }

        if (positions.empty()) {
            return false;
        }

        int minRow = numeric_limits<int>::max();
        int maxRow = numeric_limits<int>::min();
        int minColumn = numeric_limits<int>::max();
        int maxColumn = numeric_limits<int>::min();

        for (const auto& [row, column] : positions) {
            minRow = min(minRow, row);
            maxRow = max(maxRow, row);
            minColumn = min(minColumn, column);
            maxColumn = max(maxColumn, column);
        }

        const int expectedArea =
            (maxRow - minRow + 1) *
            (maxColumn - minColumn + 1);

        return static_cast<int>(positions.size()) ==
               expectedArea;
    }


    void print() const {
        cout << "\nNamed grid-area template:\n\n";

        for (const auto& row : cells) {
            for (const auto& cell : row) {
                cout
                    << setw(12)
                    << cell;
            }

            cout << "\n";
        }
    }
};


// -----------------------------------------------------------------------------
// Responsive dashboard case study
// -----------------------------------------------------------------------------

void runResponsiveDashboardCaseStudy() {
    cout << "\n"
         << "============================================================\n"
         << "RESPONSIVE DASHBOARD CASE STUDY\n"
         << "============================================================\n";

    const double desktopWidth = 1440;
    const double desktopHeight = 900;

    GridLayoutEngine dashboard(
        6,
        12,
        desktopWidth,
        desktopHeight,
        16,
        16
    );

    dashboard.configureEqualTracks();

    /*
     * A twelve-column dashboard provides enough subdivisions for
     * different widget widths while remaining easy to reason about.
     *
     * Header:
     *   twelve columns
     *
     * Main analytics panel:
     *   six columns
     *
     * Secondary panels:
     *   three columns each
     *
     * Footer:
     *   twelve columns
     */

    dashboard.placeItem(
        GridItem(
            "header",
            1,
            1,
            1,
            12
        )
    );

    dashboard.placeItem(
        GridItem(
            "navigation",
            2,
            1,
            4,
            2
        )
    );

    dashboard.placeItem(
        GridItem(
            "analytics",
            2,
            3,
            3,
            6
        )
    );

    dashboard.placeItem(
        GridItem(
            "revenue",
            2,
            9,
            1,
            2
        )
    );

    dashboard.placeItem(
        GridItem(
            "users",
            2,
            11,
            1,
            2
        )
    );

    dashboard.placeItem(
        GridItem(
            "operations",
            5,
            3,
            1,
            4
        )
    );

    dashboard.placeItem(
        GridItem(
            "alerts",
            5,
            7,
            1,
            6
        )
    );

    dashboard.placeItem(
        GridItem(
            "footer",
            6,
            1,
            1,
            12
        )
    );

    dashboard.printGrid();
    dashboard.printGridLines();
    dashboard.printTrackInformation();
    dashboard.printItemDetails();

    cout << "\nGenerated CSS:\n";
    cout << dashboard.generateCSS();

    cout << "\nResponsive column calculations:\n";

    const vector<double> viewportWidths = {
        360,
        480,
        768,
        1024,
        1366,
        1440,
        1920
    };

    for (double width : viewportWidths) {
        const int columns =
            GridLayoutEngine::responsiveColumnCount(
                width,
                220,
                16
            );

        cout
            << "  "
            << setw(4)
            << width
            << "px -> "
            << columns
            << " minimum-width columns\n";
    }
}


// -----------------------------------------------------------------------------
// Grid-area case study
// -----------------------------------------------------------------------------

void runGridAreaCaseStudy() {
    cout << "\n"
         << "============================================================\n"
         << "NAMED GRID-AREA CASE STUDY\n"
         << "============================================================\n";

    GridAreaTemplate templateGrid({
        {"header", "header", "header", "header"},
        {"sidebar", "main", "main", "aside"},
        {"sidebar", "main", "main", "aside"},
        {"footer", "footer", "footer", "footer"}
    });

    templateGrid.print();

    const vector<string> areas = {
        "header",
        "sidebar",
        "main",
        "aside",
        "footer"
    };

    cout << "\nArea validation:\n";

    for (const string& area : areas) {
        cout
            << "  "
            << setw(8)
            << area
            << " -> rectangular="
            << boolalpha
            << templateGrid.isRectangular(area)
            << "\n";
    }

    cout << "\nCorresponding CSS concept:\n";
    cout << "grid-template-areas:\n";
    cout << "    \"header header header header\"\n";
    cout << "    \"sidebar main main aside\"\n";
    cout << "    \"sidebar main main aside\"\n";
    cout << "    \"footer footer footer footer\";\n";
}


// -----------------------------------------------------------------------------
// Edge cases
// -----------------------------------------------------------------------------

void runEdgeCases() {
    cout << "\n"
         << "============================================================\n"
         << "EDGE CASES AND FAILURE CONDITIONS\n"
         << "============================================================\n";

    cout << "\nCase 1: Invalid grid dimensions\n";

    try {
        GridLayoutEngine invalid(
            0,
            4,
            1000,
            800,
            16,
            16
        );

        (void)invalid;
    }
    catch (const exception& error) {
        cout << "  Rejected safely: "
             << error.what()
             << "\n";
    }


    cout << "\nCase 2: Negative gap\n";

    try {
        GridLayoutEngine invalid(
            4,
            4,
            1000,
            800,
            -10,
            16
        );

        (void)invalid;
    }
    catch (const exception& error) {
        cout << "  Rejected safely: "
             << error.what()
             << "\n";
    }


    cout << "\nCase 3: Item outside grid\n";

    try {
        GridLayoutEngine grid(
            4,
            4,
            1000,
            800,
            16,
            16
        );

        grid.placeItem(
            GridItem(
                "invalid",
                4,
                4,
                2,
                1
            )
        );
    }
    catch (const exception& error) {
        cout << "  Rejected safely: "
             << error.what()
             << "\n";
    }


    cout << "\nCase 4: Overlapping items\n";

    try {
        GridLayoutEngine grid(
            4,
            4,
            1000,
            800,
            16,
            16
        );

        grid.placeItem(
            GridItem(
                "first",
                1,
                1,
                2,
                2
            )
        );

        grid.placeItem(
            GridItem(
                "second",
                2,
                2,
                2,
                2
            )
        );
    }
    catch (const exception& error) {
        cout << "  Rejected safely: "
             << error.what()
             << "\n";
    }


    cout << "\nCase 5: Automatic placement after explicit placement\n";

    try {
        GridLayoutEngine grid(
            2,
            3,
            900,
            500,
            12,
            12
        );

        grid.placeItem(
            GridItem(
                "reserved",
                1,
                2,
                1,
                1
            )
        );

        grid.autoPlaceItem("auto1");
        grid.autoPlaceItem("auto2");
        grid.autoPlaceItem("auto3");

        grid.printGrid();
    }
    catch (const exception& error) {
        cout << "  Error: "
             << error.what()
             << "\n";
    }
}


// -----------------------------------------------------------------------------
// Complexity analysis
// -----------------------------------------------------------------------------

void printComplexityAnalysis() {
    cout << "\n"
         << "============================================================\n"
         << "COMPLEXITY ANALYSIS\n"
         << "============================================================\n";

    cout << "\nNotation:\n";
    cout << "  R = number of rows\n";
    cout << "  C = number of columns\n";
    cout << "  I = number of grid items\n";
    cout << "  S = number of cells occupied by one item\n";

    cout << "\nOperations:\n";
    cout << "  Occupancy rendering: O(R * C + I * S)\n";
    cout << "  Collision check:     O(S log(R*C)) using std::set\n";
    cout << "  First free cell:     O(R * C)\n";
    cout << "  Equal fr sizing:     O(R + C)\n";
    cout << "  Area validation:      O(R * C)\n";

    cout << "\nBrowser CSS Grid itself is substantially more sophisticated than this"
         << " educational model because real layout includes intrinsic sizing,"
         << " min-content/max-content constraints, spanning, automatic minimum"
         << " sizes, writing modes, replaced elements, percentages, and other"
         << " browser layout rules.\n";
}


// -----------------------------------------------------------------------------
// Architecture explanation through program output
// -----------------------------------------------------------------------------

void printArchitecture() {
    cout << "\n"
         << "============================================================\n"
         << "SYSTEM ARCHITECTURE\n"
         << "============================================================\n";

    cout << "\n1. GridLayoutEngine\n";
    cout << "   Owns dimensions, tracks, items, gaps, and occupancy state.\n";

    cout << "\n2. Track\n";
    cout << "   Represents a row or column track and its calculated size.\n";

    cout << "\n3. GridItem\n";
    cout << "   Represents an item with starting position and span.\n";

    cout << "\n4. Cell\n";
    cout << "   Represents an individual row/column coordinate.\n";

    cout << "\n5. GridAreaTemplate\n";
    cout << "   Validates named rectangular areas.\n";

    cout << "\n6. CSS generation\n";
    cout << "   Converts the internal layout model into CSS declarations.\n";

    cout << "\nThis separation resembles an application that calculates a layout"
         << " configuration on a backend before passing it to a frontend renderer.\n";
}


// -----------------------------------------------------------------------------
// Main
// -----------------------------------------------------------------------------

int main() {
    try {
        cout
            << "CSS GRID FUNDAMENTALS\n"
            << "Technical case study: responsive dashboard layout engine\n";

        printArchitecture();

        runResponsiveDashboardCaseStudy();

        runGridAreaCaseStudy();

        runEdgeCases();

        printComplexityAnalysis();

        cout << "\n"
             << "============================================================\n"
             << "KEY CSS GRID RELATIONSHIPS\n"
             << "============================================================\n";

        cout << "\nContainer -> rows + columns\n";
        cout << "Rows/columns -> tracks\n";
        cout << "Tracks intersect -> cells\n";
        cout << "Cells combine -> grid areas\n";
        cout << "Items occupy cells or span multiple cells\n";
        cout << "Gaps separate adjacent tracks\n";
        cout << "fr distributes flexible remaining space\n";
        cout << "minmax() constrains track size\n";
        cout << "auto-fit/auto-fill support responsive track creation\n";
        cout << "grid-template-areas provides semantic named placement\n";

        cout << "\nProgram completed successfully.\n";
    }
    catch (const exception& error) {
        cerr
            << "\nFatal error: "
            << error.what()
            << "\n";

        return 1;
    }

    return 0;
}
