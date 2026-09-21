/*
 * CSS Positioning — C++17 Case Study
 *
 * Case study:
 * A web-application interface contains:
 *   - normal document content,
 *   - a card with an absolute status badge,
 *   - a sticky section navigation bar,
 *   - a fixed support button,
 *   - modal and notification layers,
 *   - nested stacking contexts.
 *
 * C++ does not render CSS. This program therefore implements a simplified
 * layout and stacking engine that models the concepts needed to reason about
 * CSS positioning.
 *
 * Compile:
 *   g++ -std=c++17 -Wall -Wextra -pedantic css_positioning.cpp -o css_positioning
 *
 * Run:
 *   ./css_positioning
 */

#include <algorithm>
#include <cassert>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <memory>
#include <optional>
#include <stdexcept>
#include <string>
#include <tuple>
#include <utility>
#include <vector>

using namespace std;


// ============================================================================
// 1. ENUMERATIONS
// ============================================================================

enum class Position {
    Static,
    Relative,
    Absolute,
    Fixed,
    Sticky
};

string toString(Position position) {
    switch (position) {
        case Position::Static:
            return "static";
        case Position::Relative:
            return "relative";
        case Position::Absolute:
            return "absolute";
        case Position::Fixed:
            return "fixed";
        case Position::Sticky:
            return "sticky";
    }

    return "unknown";
}


// ============================================================================
// 2. GEOMETRY
// ============================================================================

struct Rectangle {
    double x{0};
    double y{0};
    double width{0};
    double height{0};

    double right() const {
        return x + width;
    }

    double bottom() const {
        return y + height;
    }
};

struct Viewport {
    double width;
    double height;
    double scrollX{0};
    double scrollY{0};
};


// ============================================================================
// 3. CSS-LIKE ELEMENT MODEL
// ============================================================================

struct Element {
    string name;
    Position position{Position::Static};

    // CSS z-index can be "auto" or an integer. optional<int> models that.
    optional<int> zIndex;

    optional<double> top;
    optional<double> right;
    optional<double> bottom;
    optional<double> left;

    double width{100};
    double height{40};

    // Location determined by ordinary flow before positioning offsets.
    double normalX{0};
    double normalY{0};

    bool establishesStackingContext{false};

    Element* parent{nullptr};
    vector<unique_ptr<Element>> children;

    void addChild(unique_ptr<Element> child) {
        child->parent = this;
        children.push_back(move(child));
    }

    int effectiveZIndex() const {
        return zIndex.value_or(0);
    }
};


// ============================================================================
// 4. VALIDATION
// ============================================================================

void validateElement(const Element& element) {
    if (element.width < 0 || element.height < 0) {
        throw invalid_argument(
            "Element dimensions cannot be negative: " + element.name
        );
    }

    const vector<pair<string, optional<double>>> offsets = {
        {"top", element.top},
        {"right", element.right},
        {"bottom", element.bottom},
        {"left", element.left},
    };

    for (const auto& [name, value] : offsets) {
        if (value.has_value() &&
            (!isfinite(*value))) {
            throw invalid_argument(
                "Offset " + name + " is not finite."
            );
        }
    }
}


// ============================================================================
// 5. RELATIVE POSITIONING
// ============================================================================

Rectangle resolveRelative(const Element& element) {
    validateElement(element);

    Rectangle result{
        element.normalX,
        element.normalY,
        element.width,
        element.height
    };

    // This simplified physical-coordinate model uses left before right
    // and top before bottom. Real CSS also considers writing direction and
    // the rules for opposing insets.
    if (element.left.has_value()) {
        result.x += *element.left;
    } else if (element.right.has_value()) {
        result.x -= *element.right;
    }

    if (element.top.has_value()) {
        result.y += *element.top;
    } else if (element.bottom.has_value()) {
        result.y -= *element.bottom;
    }

    return result;
}


// ============================================================================
// 6. ABSOLUTE CONTAINING BLOCK
// ============================================================================

Element* findAbsoluteContainingBlock(Element* element) {
    if (element == nullptr) {
        return nullptr;
    }

    Element* ancestor = element->parent;

    while (ancestor != nullptr) {
        if (ancestor->position != Position::Static) {
            return ancestor;
        }

        if (ancestor->establishesStackingContext) {
            return ancestor;
        }

        ancestor = ancestor->parent;
    }

    return nullptr;
}


// ============================================================================
// 7. ABSOLUTE POSITIONING
// ============================================================================

Rectangle resolveAbsolute(const Element& element) {
    validateElement(element);

    Element* mutableElement = const_cast<Element*>(&element);
    Element* containingBlock =
        findAbsoluteContainingBlock(mutableElement);

    Rectangle result{
        0,
        0,
        element.width,
        element.height
    };

    if (containingBlock == nullptr) {
        // Simplified initial containing block.
        if (element.left.has_value()) {
            result.x = *element.left;
        } else if (element.right.has_value()) {
            result.x = -*element.right - element.width;
        }

        if (element.top.has_value()) {
            result.y = *element.top;
        } else if (element.bottom.has_value()) {
            result.y = -*element.bottom - element.height;
        }

        return result;
    }

    if (element.left.has_value()) {
        result.x =
            containingBlock->normalX + *element.left;
    } else if (element.right.has_value()) {
        result.x =
            containingBlock->normalX
            + containingBlock->width
            - element.width
            - *element.right;
    } else {
        result.x = containingBlock->normalX;
    }

    if (element.top.has_value()) {
        result.y =
            containingBlock->normalY + *element.top;
    } else if (element.bottom.has_value()) {
        result.y =
            containingBlock->normalY
            + containingBlock->height
            - element.height
            - *element.bottom;
    } else {
        result.y = containingBlock->normalY;
    }

    return result;
}


// ============================================================================
// 8. FIXED POSITIONING
// ============================================================================

Rectangle resolveFixed(const Element& element, const Viewport& viewport) {
    validateElement(element);

    Rectangle result{
        0,
        0,
        element.width,
        element.height
    };

    // In the ordinary fixed model, document scrolling does not change the
    // viewport-relative coordinates.
    if (element.left.has_value()) {
        result.x = *element.left;
    } else if (element.right.has_value()) {
        result.x =
            viewport.width
            - element.width
            - *element.right;
    } else {
        result.x = element.normalX;
    }

    if (element.top.has_value()) {
        result.y = *element.top;
    } else if (element.bottom.has_value()) {
        result.y =
            viewport.height
            - element.height
            - *element.bottom;
    } else {
        result.y = element.normalY;
    }

    return result;
}


// ============================================================================
// 9. STICKY POSITIONING
// ============================================================================

double resolveStickyY(
    double normalY,
    optional<double> top,
    double scrollY,
    double containingBlockEnd,
    double elementHeight
) {
    // Without a vertical inset, there is no threshold for sticky behavior.
    if (!top.has_value()) {
        return normalY - scrollY;
    }

    const double naturalViewportY = normalY - scrollY;

    // Sticky cannot move upward beyond its threshold.
    const double thresholdPosition =
        max(naturalViewportY, *top);

    // Sticky cannot leave the bottom boundary of its containing block.
    const double maximumViewportY =
        containingBlockEnd - scrollY - elementHeight;

    return min(thresholdPosition, maximumViewportY);
}


// ============================================================================
// 10. STACKING CONTEXT
// ============================================================================

struct StackingContext {
    string name;
    int zIndex{0};
    vector<const Element*> members;
};

bool createsCommonStackingContext(
    const Element& element,
    bool opacityLessThanOne,
    bool hasTransform,
    bool hasFilter,
    bool isolationIsolate,
    bool nonNormalBlendMode
) {
    if (element.establishesStackingContext) {
        return true;
    }

    if (element.position == Position::Fixed ||
        element.position == Position::Sticky) {
        return true;
    }

    if (
        (element.position == Position::Relative ||
         element.position == Position::Absolute) &&
        element.zIndex.has_value()
    ) {
        return true;
    }

    if (opacityLessThanOne) {
        return true;
    }

    if (hasTransform) {
        return true;
    }

    if (hasFilter) {
        return true;
    }

    if (isolationIsolate) {
        return true;
    }

    if (nonNormalBlendMode) {
        return true;
    }

    return false;
}


// ============================================================================
// 11. STACKING ORDER
// ============================================================================

vector<const Element*> approximateStackingOrder(
    const vector<const Element*>& siblings
) {
    vector<const Element*> result = siblings;

    // This is deliberately a simplified model. The real CSS painting order
    // contains multiple categories and phases and cannot be reduced to a
    // single integer sort across arbitrary DOM trees.
    stable_sort(
        result.begin(),
        result.end(),
        [](const Element* a, const Element* b) {
            return a->effectiveZIndex() < b->effectiveZIndex();
        }
    );

    return result;
}


// ============================================================================
// 12. CARD COMPONENT
// ============================================================================

class ProductCard {
public:
    ProductCard(
        double x,
        double y,
        double width,
        double height
    )
        : x_(x),
          y_(y),
          width_(width),
          height_(height) {
        if (width < 0 || height < 0) {
            throw invalid_argument("Card dimensions cannot be negative.");
        }
    }

    pair<double, double> badgePosition(
        double badgeWidth,
        double badgeHeight,
        double top,
        double right
    ) const {
        if (badgeWidth < 0 || badgeHeight < 0) {
            throw invalid_argument(
                "Badge dimensions cannot be negative."
            );
        }

        return {
            x_ + width_ - badgeWidth - right,
            y_ + top
        };
    }

private:
    double x_;
    double y_;
    double width_;
    double height_;
};


// ============================================================================
// 13. LAYER MANAGER
// ============================================================================

class LayerManager {
public:
    void defineLayer(const string& name, int zIndex) {
        if (zIndex < 0) {
            throw invalid_argument(
                "This application layer policy requires non-negative z-index values."
            );
        }

        if (layers_.contains(name)) {
            throw invalid_argument(
                "Layer already exists: " + name
            );
        }

        layers_[name] = zIndex;
    }

    int zIndexFor(const string& name) const {
        auto it = layers_.find(name);

        if (it == layers_.end()) {
            throw out_of_range(
                "Unknown layer: " + name
            );
        }

        return it->second;
    }

    void print() const {
        for (const auto& [name, value] : layers_) {
            cout << "  " << left
                 << setw(24) << name
                 << " z-index=" << value << '\n';
        }
    }

private:
    map<string, int> layers_;
};


// ============================================================================
// 14. SCROLL CONTAINER
// ============================================================================

class ScrollContainer {
public:
    ScrollContainer(double viewportHeight, double contentHeight)
        : viewportHeight_(viewportHeight),
          contentHeight_(contentHeight) {
        if (viewportHeight < 0 || contentHeight < 0) {
            throw invalid_argument(
                "Scroll dimensions cannot be negative."
            );
        }
    }

    double maxScrollY() const {
        return max(0.0, contentHeight_ - viewportHeight_);
    }

    void scrollTo(double requestedScrollY) {
        scrollY_ = clamp(
            requestedScrollY,
            0.0,
            maxScrollY()
        );
    }

    double scrollY() const {
        return scrollY_;
    }

private:
    double viewportHeight_;
    double contentHeight_;
    double scrollY_{0};
};


// ============================================================================
// 15. POSITIONING REPORT
// ============================================================================

void printElementReport(const Element& element) {
    cout << "\nElement: " << element.name << '\n';
    cout << "  position: " << toString(element.position) << '\n';

    cout << "  z-index: ";
    if (element.zIndex.has_value()) {
        cout << *element.zIndex;
    } else {
        cout << "auto";
    }
    cout << '\n';

    cout << "  size: "
         << element.width
         << " x "
         << element.height
         << '\n';

    if (element.position == Position::Relative) {
        Rectangle rect = resolveRelative(element);

        cout << "  relative result: ("
             << rect.x << ", "
             << rect.y << ")\n";
    }

    if (element.position == Position::Absolute) {
        Element* containingBlock =
            findAbsoluteContainingBlock(
                const_cast<Element*>(&element)
            );

        cout << "  containing block: "
             << (
                 containingBlock
                     ? containingBlock->name
                     : "initial containing block"
             )
             << '\n';

        Rectangle rect = resolveAbsolute(element);

        cout << "  absolute result: ("
             << rect.x << ", "
             << rect.y << ")\n";
    }
}


// ============================================================================
// 16. APPLICATION MODEL
// ============================================================================

class DashboardApplication {
public:
    DashboardApplication()
        : viewport_{1440, 900, 0, 0},
          scrollContainer_{900, 4000} {}

    void configureLayers() {
        layers_.defineLayer("base-content", 0);
        layers_.defineLayer("dropdown", 100);
        layers_.defineLayer("sticky-navigation", 200);
        layers_.defineLayer("overlay", 500);
        layers_.defineLayer("modal", 1000);
        layers_.defineLayer("toast", 1100);
    }

    void configureElements() {
        root_ = make_unique<Element>();

        root_->name = "application-root";
        root_->position = Position::Static;
        root_->width = 1440;
        root_->height = 4000;
        root_->establishesStackingContext = true;

        auto content = make_unique<Element>();
        content->name = "content";
        content->position = Position::Static;
        content->normalX = 80;
        content->normalY = 120;
        content->width = 1000;
        content->height = 3000;

        auto card = make_unique<Element>();
        card->name = "product-card";
        card->position = Position::Relative;
        card->normalX = 120;
        card->normalY = 300;
        card->width = 500;
        card->height = 280;

        auto badge = make_unique<Element>();
        badge->name = "product-badge";
        badge->position = Position::Absolute;
        badge->top = 16;
        badge->right = 18;
        badge->width = 90;
        badge->height = 32;
        badge->zIndex = 10;

        card->addChild(move(badge));
        content->addChild(move(card));

        auto sticky = make_unique<Element>();
        sticky->name = "section-navigation";
        sticky->position = Position::Sticky;
        sticky->top = 0;
        sticky->normalY = 500;
        sticky->width = 1000;
        sticky->height = 56;
        sticky->zIndex = layers_.zIndexFor("sticky-navigation");

        root_->addChild(move(content));
        root_->addChild(move(sticky));
    }

    void configureViewportControls() {
        fixedSupport_.name = "support-button";
        fixedSupport_.position = Position::Fixed;
        fixedSupport_.right = 24;
        fixedSupport_.bottom = 24;
        fixedSupport_.width = 160;
        fixedSupport_.height = 52;
        fixedSupport_.zIndex = layers_.zIndexFor("overlay");
    }

    void printFixedControl() const {
        cout << "\nFixed support button:\n";

        Rectangle before =
            resolveFixed(fixedSupport_, viewport_);

        viewport_.scrollY = 2500;

        Rectangle after =
            resolveFixed(fixedSupport_, viewport_);

        cout << "  before scroll: ("
             << before.x << ", "
             << before.y << ")\n";

        cout << "  after scroll:  ("
             << after.x << ", "
             << after.y << ")\n";
    }

    void printStickyControl() {
        cout << "\nSticky navigation simulation:\n";

        const double containingEnd = 3500;
        const double elementHeight = 56;

        for (double scrollY : {0.0, 200.0, 500.0, 800.0, 2000.0, 3400.0}) {
            double y = resolveStickyY(
                500,
                0,
                scrollY,
                containingEnd,
                elementHeight
            );

            cout << "  scrollY="
                 << setw(6)
                 << scrollY
                 << " -> viewportY="
                 << setw(8)
                 << y
                 << '\n';
        }
    }

    void printLayerPolicy() const {
        cout << "\nApplication layer policy:\n";
        layers_.print();
    }

    void printApplicationTree() const {
        cout << "\nApplication element tree:\n";

        if (root_) {
            printTree(*root_, 0);
        }
    }

private:
    static void printTree(
        const Element& element,
        int depth
    ) {
        cout << string(depth * 2, ' ')
             << element.name
             << " position="
             << toString(element.position)
             << " z-index=";

        if (element.zIndex.has_value()) {
            cout << *element.zIndex;
        } else {
            cout << "auto";
        }

        if (element.establishesStackingContext) {
            cout << " [stacking-context]";
        }

        cout << '\n';

        for (const auto& child : element.children) {
            printTree(*child, depth + 1);
        }
    }

    Viewport viewport_;
    ScrollContainer scrollContainer_;
    LayerManager layers_;
    unique_ptr<Element> root_;
    Element fixedSupport_;
};


// ============================================================================
// 17. COMPLEXITY DISCUSSION
// ============================================================================

void printComplexityAnalysis() {
    cout << "\nComplexity considerations:\n";
    cout << "  Containing-block ancestor search: O(h), where h is ancestor depth.\n";
    cout << "  Sorting n siblings by z-index: O(n log n).\n";
    cout << "  Traversing the element tree: O(n).\n";
    cout << "  Layer lookup using std::map: O(log n).\n";
    cout << "  Sticky coordinate calculation: O(1) per evaluated element.\n";
    cout << "  Real browser rendering is considerably more complex because layout,\n";
    cout << "  style calculation, painting, compositing, clipping, and scrolling\n";
    cout << "  interact across the rendering pipeline.\n";
}


// ============================================================================
// 18. EDGE CASES
// ============================================================================

void demonstrateEdgeCases() {
    cout << "\nEdge cases:\n";

    Element staticBox;
    staticBox.name = "static-box";
    staticBox.position = Position::Static;
    staticBox.top = 100;
    staticBox.left = 100;

    cout << "  static with top/left -> offsets do not reposition the element.\n";

    Element noParentAbsolute;
    noParentAbsolute.name = "orphan-absolute";
    noParentAbsolute.position = Position::Absolute;
    noParentAbsolute.top = 20;
    noParentAbsolute.left = 30;

    Rectangle orphanResult = resolveAbsolute(noParentAbsolute);

    cout << "  absolute without modeled positioned ancestor -> ("
         << orphanResult.x
         << ", "
         << orphanResult.y
         << ") in this simplified initial-containing-block model.\n";

    Element stickyWithoutInset;
    stickyWithoutInset.name = "sticky-without-inset";
    stickyWithoutInset.position = Position::Sticky;
    stickyWithoutInset.normalY = 400;

    double stickyResult = resolveStickyY(
        stickyWithoutInset.normalY,
        stickyWithoutInset.top,
        300,
        1500,
        50
    );

    cout << "  sticky without top -> normal viewport-relative result: "
         << stickyResult
         << '\n';

    try {
        Element invalid;
        invalid.name = "invalid";
        invalid.width = -1;
        validateElement(invalid);
    } catch (const exception& error) {
        cout << "  invalid dimensions -> caught error: "
             << error.what()
             << '\n';
    }
}


// ============================================================================
// 19. TESTS
// ============================================================================

void runTests() {
    assert(toString(Position::Static) == "static");
    assert(toString(Position::Relative) == "relative");
    assert(toString(Position::Absolute) == "absolute");
    assert(toString(Position::Fixed) == "fixed");
    assert(toString(Position::Sticky) == "sticky");

    Element relative;
    relative.name = "relative-test";
    relative.position = Position::Relative;
    relative.normalX = 100;
    relative.normalY = 200;
    relative.left = 15;
    relative.top = 10;

    Rectangle relativeResult = resolveRelative(relative);

    assert(relativeResult.x == 115);
    assert(relativeResult.y == 210);

    auto parent = make_unique<Element>();
    parent->name = "parent";
    parent->position = Position::Relative;

    auto child = make_unique<Element>();
    child->name = "child";
    child->position = Position::Absolute;

    Element* childRaw = child.get();
    parent->addChild(move(child));

    assert(findAbsoluteContainingBlock(childRaw) == parent.get());

    Element fixed;
    fixed.name = "fixed-test";
    fixed.position = Position::Fixed;
    fixed.right = 10;
    fixed.bottom = 20;
    fixed.width = 100;
    fixed.height = 50;

    Rectangle fixedResult =
        resolveFixed(fixed, Viewport{800, 600});

    assert(fixedResult.x == 690);
    assert(fixedResult.y == 530);

    double stickyResult = resolveStickyY(
        500,
        0,
        500,
        1500,
        50
    );

    assert(stickyResult == 0);

    assert(
        createsCommonStackingContext(
            fixed,
            false,
            false,
            false,
            false,
            false
        )
    );

    cout << "All C++ tests passed.\n";
}


// ============================================================================
// 20. MAIN CASE STUDY
// ============================================================================

int main() {
    cout << fixed << setprecision(2);

    cout << string(78, '=') << '\n';
    cout << "CSS POSITIONING — C++ TECHNICAL CASE STUDY\n";
    cout << string(78, '=') << '\n';

    cout << "\nPositioning fundamentals:\n";
    cout << "  static   -> normal flow\n";
    cout << "  relative -> normal flow + visual offset\n";
    cout << "  absolute -> removed from normal flow + containing block\n";
    cout << "  fixed    -> removed from normal flow + viewport-oriented positioning\n";
    cout << "  sticky   -> flow-based positioning constrained during scrolling\n";

    // ------------------------------------------------------------------------
    // Build a realistic dashboard.
    // ------------------------------------------------------------------------

    DashboardApplication application;

    application.configureLayers();
    application.configureElements();
    application.configureViewportControls();

    application.printApplicationTree();
    application.printLayerPolicy();
    application.printFixedControl();
    application.printStickyControl();

    // ------------------------------------------------------------------------
    // Card overlay.
    // ------------------------------------------------------------------------

    ProductCard productCard(
        120,
        300,
        500,
        280
    );

    auto [badgeX, badgeY] =
        productCard.badgePosition(
            90,
            32,
            16,
            18
        );

    cout << "\nProduct card badge:\n";
    cout << "  x=" << badgeX
         << ", y=" << badgeY
         << '\n';

    // ------------------------------------------------------------------------
    // Layer sorting demonstration.
    // ------------------------------------------------------------------------

    Element content;
    content.name = "content";
    content.position = Position::Static;

    Element dropdown;
    dropdown.name = "dropdown";
    dropdown.position = Position::Absolute;
    dropdown.zIndex = 100;

    Element modal;
    modal.name = "modal";
    modal.position = Position::Fixed;
    modal.zIndex = 1000;

    Element toast;
    toast.name = "toast";
    toast.position = Position::Fixed;
    toast.zIndex = 1100;

    vector<const Element*> layers{
        &toast,
        &content,
        &modal,
        &dropdown
    };

    vector<const Element*> sortedLayers =
        approximateStackingOrder(layers);

    cout << "\nApproximate stacking order:\n";

    for (const Element* element : sortedLayers) {
        cout << "  "
             << setw(12)
             << element->name
             << " z-index=";

        if (element->zIndex.has_value()) {
            cout << *element->zIndex;
        } else {
            cout << "auto";
        }

        cout << '\n';
    }

    // ------------------------------------------------------------------------
    // Scroll constraints.
    // ------------------------------------------------------------------------

    ScrollContainer scrollContainer(
        800,
        3000
    );

    cout << "\nScroll container:\n";
    cout << "  max scrollY="
         << scrollContainer.maxScrollY()
         << '\n';

    scrollContainer.scrollTo(5000);

    cout << "  requested scrollY=5000\n";
    cout << "  clamped scrollY="
         << scrollContainer.scrollY()
         << '\n';

    // ------------------------------------------------------------------------
    // Edge cases and complexity.
    // ------------------------------------------------------------------------

    demonstrateEdgeCases();
    printComplexityAnalysis();

    // ------------------------------------------------------------------------
    // Tests.
    // ------------------------------------------------------------------------

    cout << "\nRunning tests...\n";
    runTests();

    cout << "\nCase study completed successfully.\n";

    return 0;
}
