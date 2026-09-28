/*
 * CSS Transitions — C++17 Technical Case Study
 *
 * Scenario:
 *     A design-system team needs a reusable specification engine for
 *     interactive dashboard components. The engine models CSS transition
 *     definitions, validates them, calculates timing curves, simulates
 *     property interpolation, evaluates performance concerns, and generates
 *     production-oriented CSS.
 *
 * This is intentionally a C++ systems-style case study rather than a
 * browser implementation. Browsers perform the actual CSS rendering, while
 * this program models the concepts needed by a component system that could
 * generate or validate CSS.
 *
 * Compile:
 *     g++ -std=c++17 -Wall -Wextra -pedantic css_transitions.cpp -o transitions
 */

#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>


// ============================================================================
// 1. GENERAL UTILITIES
// ============================================================================

double clamp(double value, double minimum = 0.0, double maximum = 1.0) {
    return std::max(minimum, std::min(maximum, value));
}

double interpolate(double start, double end, double progress) {
    const double t = clamp(progress);
    return start + (end - start) * t;
}

std::string formatMilliseconds(int milliseconds) {
    if (milliseconds < 0) {
        throw std::invalid_argument(
            "CSS time cannot be negative in this helper."
        );
    }

    return std::to_string(milliseconds) + "ms";
}


// ============================================================================
// 2. TIMING FUNCTION ABSTRACTION
// ============================================================================

class TimingFunction {
public:
    virtual ~TimingFunction() = default;

    virtual double evaluate(double progress) const = 0;
    virtual std::string name() const = 0;
};


class LinearTiming final : public TimingFunction {
public:
    double evaluate(double progress) const override {
        return clamp(progress);
    }

    std::string name() const override {
        return "linear";
    }
};


class EaseInTiming final : public TimingFunction {
public:
    double evaluate(double progress) const override {
        const double t = clamp(progress);
        return t * t * t;
    }

    std::string name() const override {
        return "ease-in";
    }
};


class EaseOutTiming final : public TimingFunction {
public:
    double evaluate(double progress) const override {
        const double t = clamp(progress);
        return 1.0 - std::pow(1.0 - t, 3.0);
    }

    std::string name() const override {
        return "ease-out";
    }
};


class EaseInOutTiming final : public TimingFunction {
public:
    double evaluate(double progress) const override {
        const double t = clamp(progress);

        if (t < 0.5) {
            return 4.0 * t * t * t;
        }

        return 1.0 - std::pow(-2.0 * t + 2.0, 3.0) / 2.0;
    }

    std::string name() const override {
        return "ease-in-out";
    }
};


// ============================================================================
// 3. CUBIC-BEZIER TIMING
// ============================================================================

class CubicBezierTiming final : public TimingFunction {
private:
    double p1x_;
    double p1y_;
    double p2x_;
    double p2y_;

    static double coordinate(
        double t,
        double first,
        double second
    ) {
        return
            3.0 * std::pow(1.0 - t, 2.0) * t * first +
            3.0 * (1.0 - t) * std::pow(t, 2.0) * second +
            std::pow(t, 3.0);
    }

public:
    CubicBezierTiming(
        double p1x,
        double p1y,
        double p2x,
        double p2y
    )
        : p1x_(p1x),
          p1y_(p1y),
          p2x_(p2x),
          p2y_(p2y) {

        if (p1x < 0.0 || p1x > 1.0 ||
            p2x < 0.0 || p2x > 1.0) {
            throw std::invalid_argument(
                "Cubic-bezier x control points must be between 0 and 1."
            );
        }
    }

    double evaluate(double progress) const override {
        const double targetX = clamp(progress);

        double low = 0.0;
        double high = 1.0;

        /*
         * CSS cubic-bezier timing functions map time through x(t) and output
         * visual progress through y(t). Since x(t) is not necessarily equal
         * to the requested time, numerically invert x(t) using binary search.
         */
        for (int iteration = 0; iteration < 40; ++iteration) {
            const double middle = (low + high) / 2.0;
            const double currentX =
                coordinate(middle, p1x_, p2x_);

            if (currentX < targetX) {
                low = middle;
            } else {
                high = middle;
            }
        }

        const double parameter = (low + high) / 2.0;

        return coordinate(
            parameter,
            p1y_,
            p2y_
        );
    }

    std::string name() const override {
        std::ostringstream output;

        output << std::fixed << std::setprecision(3)
               << "cubic-bezier("
               << p1x_ << ", "
               << p1y_ << ", "
               << p2x_ << ", "
               << p2y_ << ")";

        return output.str();
    }
};


// ============================================================================
// 4. TRANSITION SPECIFICATION
// ============================================================================

struct Transition {
    std::string property;
    int durationMilliseconds;
    std::shared_ptr<TimingFunction> timingFunction;
    int delayMilliseconds;

    Transition(
        std::string propertyName,
        int duration,
        std::shared_ptr<TimingFunction> timing,
        int delay = 0
    )
        : property(std::move(propertyName)),
          durationMilliseconds(duration),
          timingFunction(std::move(timing)),
          delayMilliseconds(delay) {

        if (property.empty()) {
            throw std::invalid_argument(
                "Transition property cannot be empty."
            );
        }

        if (duration < 0) {
            throw std::invalid_argument(
                "Transition duration cannot be negative."
            );
        }

        if (delay < 0) {
            throw std::invalid_argument(
                "This model expects non-negative delays."
            );
        }

        if (!timingFunction) {
            throw std::invalid_argument(
                "A timing function is required."
            );
        }
    }

    std::string toCSS() const {
        std::ostringstream output;

        output << property
               << " "
               << formatMilliseconds(durationMilliseconds)
               << " "
               << timingFunction->name()
               << " "
               << formatMilliseconds(delayMilliseconds);

        return output.str();
    }

    int totalTime() const {
        return durationMilliseconds + delayMilliseconds;
    }
};


// ============================================================================
// 5. DESIGN SYSTEM
// ============================================================================

struct MotionToken {
    std::string name;
    int durationMilliseconds;
    std::shared_ptr<TimingFunction> timingFunction;
};


class MotionDesignSystem {
private:
    std::map<std::string, MotionToken> tokens_;

public:
    void addToken(MotionToken token) {
        if (token.name.empty()) {
            throw std::invalid_argument(
                "Motion token name cannot be empty."
            );
        }

        if (token.durationMilliseconds < 0) {
            throw std::invalid_argument(
                "Motion token duration cannot be negative."
            );
        }

        tokens_[token.name] = std::move(token);
    }

    const MotionToken& getToken(
        const std::string& tokenName
    ) const {
        const auto iterator = tokens_.find(tokenName);

        if (iterator == tokens_.end()) {
            throw std::out_of_range(
                "Unknown motion token: " + tokenName
            );
        }

        return iterator->second;
    }

    Transition createTransition(
        const std::string& tokenName,
        const std::string& property
    ) const {
        const MotionToken& token = getToken(tokenName);

        return Transition(
            property,
            token.durationMilliseconds,
            token.timingFunction
        );
    }
};


// ============================================================================
// 6. PERFORMANCE CLASSIFICATION
// ============================================================================

enum class PerformanceCategory {
    CompositingFriendly,
    LayoutSensitive,
    PaintSensitive,
    Unknown
};


std::string performanceCategoryName(
    PerformanceCategory category
) {
    switch (category) {
        case PerformanceCategory::CompositingFriendly:
            return "compositing-friendly";

        case PerformanceCategory::LayoutSensitive:
            return "layout-sensitive";

        case PerformanceCategory::PaintSensitive:
            return "paint-sensitive";

        case PerformanceCategory::Unknown:
            return "unknown";
    }

    return "unknown";
}


PerformanceCategory classifyProperty(
    const std::string& property
) {
    if (
        property == "transform" ||
        property == "opacity"
    ) {
        return PerformanceCategory::CompositingFriendly;
    }

    if (
        property == "width" ||
        property == "height" ||
        property == "margin" ||
        property == "padding" ||
        property == "top" ||
        property == "left"
    ) {
        return PerformanceCategory::LayoutSensitive;
    }

    if (
        property == "box-shadow" ||
        property == "filter"
    ) {
        return PerformanceCategory::PaintSensitive;
    }

    return PerformanceCategory::Unknown;
}


// ============================================================================
// 7. VALIDATION
// ============================================================================

struct ValidationIssue {
    std::string severity;
    std::string message;
};


std::vector<ValidationIssue> validateTransition(
    const Transition& transition
) {
    std::vector<ValidationIssue> issues;

    if (transition.durationMilliseconds > 1000) {
        issues.push_back({
            "warning",
            "Duration exceeds one second."
        });
    }

    const PerformanceCategory category =
        classifyProperty(transition.property);

    if (category == PerformanceCategory::LayoutSensitive) {
        issues.push_back({
            "performance",
            "Property changes can affect layout."
        });
    }

    if (category == PerformanceCategory::PaintSensitive) {
        issues.push_back({
            "performance",
            "Property may increase paint cost."
        });
    }

    if (transition.delayMilliseconds > 500) {
        issues.push_back({
            "warning",
            "Long delays can make interaction feel unresponsive."
        });
    }

    return issues;
}


// ============================================================================
// 8. COMPONENT MODEL
// ============================================================================

enum class ButtonState {
    Idle,
    Hover,
    Focus,
    Active,
    Disabled
};


std::string buttonStateName(ButtonState state) {
    switch (state) {
        case ButtonState::Idle:
            return "idle";

        case ButtonState::Hover:
            return "hover";

        case ButtonState::Focus:
            return "focus";

        case ButtonState::Active:
            return "active";

        case ButtonState::Disabled:
            return "disabled";
    }

    return "unknown";
}


struct ButtonVisualState {
    double scale = 1.0;
    double translateY = 0.0;
    double opacity = 1.0;
    bool focusRing = false;
};


class InteractiveButton {
private:
    ButtonState state_ = ButtonState::Idle;

public:
    void setState(ButtonState state) {
        state_ = state;
    }

    ButtonState state() const {
        return state_;
    }

    ButtonVisualState visualState() const {
        ButtonVisualState visual;

        switch (state_) {
            case ButtonState::Idle:
                break;

            case ButtonState::Hover:
                visual.translateY = -2.0;
                break;

            case ButtonState::Focus:
                visual.focusRing = true;
                break;

            case ButtonState::Active:
                visual.scale = 0.98;
                break;

            case ButtonState::Disabled:
                visual.opacity = 0.55;
                break;
        }

        return visual;
    }
};


// ============================================================================
// 9. CSS GENERATION
// ============================================================================

std::string generateButtonCSS(
    const std::vector<Transition>& transitions
) {
    if (transitions.empty()) {
        throw std::invalid_argument(
            "At least one transition is required."
        );
    }

    std::ostringstream output;

    output
        << ".button {\n"
        << "    background-color: #1f2937;\n"
        << "    color: white;\n"
        << "    transform: translateY(0) scale(1);\n"
        << "    transition: ";

    for (std::size_t index = 0; index < transitions.size(); ++index) {
        if (index > 0) {
            output << ", ";
        }

        output << transitions[index].toCSS();
    }

    output
        << ";\n"
        << "}\n\n"
        << ".button:hover {\n"
        << "    transform: translateY(-2px) scale(1);\n"
        << "    background-color: #334155;\n"
        << "}\n\n"
        << ".button:focus-visible {\n"
        << "    outline: 3px solid currentColor;\n"
        << "    outline-offset: 3px;\n"
        << "}\n\n"
        << ".button:active {\n"
        << "    transform: translateY(0) scale(0.98);\n"
        << "}\n\n"
        << "@media (prefers-reduced-motion: reduce) {\n"
        << "    .button {\n"
        << "        transition-duration: 0.01ms;\n"
        << "    }\n"
        << "}\n";

    return output.str();
}


// ============================================================================
// 10. TRANSITION SIMULATION
// ============================================================================

struct SimulationPoint {
    double timeProgress;
    double visualProgress;
    double value;
};


std::vector<SimulationPoint> simulateTransition(
    double start,
    double end,
    const Transition& transition,
    int samples = 11
) {
    if (samples < 2) {
        throw std::invalid_argument(
            "At least two samples are required."
        );
    }

    std::vector<SimulationPoint> result;

    result.reserve(static_cast<std::size_t>(samples));

    for (int index = 0; index < samples; ++index) {
        const double timeProgress =
            static_cast<double>(index) /
            static_cast<double>(samples - 1);

        const double visualProgress =
            transition.timingFunction->evaluate(
                timeProgress
            );

        const double value =
            interpolate(
                start,
                end,
                visualProgress
            );

        result.push_back({
            timeProgress,
            visualProgress,
            value
        });
    }

    return result;
}


// ============================================================================
// 11. TRANSITION TIMELINE
// ============================================================================

struct TimelinePoint {
    int elapsedMilliseconds;
    double progress;
};


std::vector<TimelinePoint> createTimeline(
    int duration,
    int delay,
    int samples = 8
) {
    if (duration < 0 || delay < 0) {
        throw std::invalid_argument(
            "Duration and delay must be non-negative."
        );
    }

    if (samples < 2) {
        throw std::invalid_argument(
            "At least two timeline samples are required."
        );
    }

    const int total = duration + delay;

    if (total == 0) {
        return {{0, 1.0}};
    }

    std::vector<TimelinePoint> result;

    for (int index = 0; index < samples; ++index) {
        const double ratio =
            static_cast<double>(index) /
            static_cast<double>(samples - 1);

        const int elapsed = static_cast<int>(
            std::round(total * ratio)
        );

        double progress = 0.0;

        if (elapsed <= delay) {
            progress = 0.0;
        } else if (duration == 0) {
            progress = 1.0;
        } else {
            progress = clamp(
                static_cast<double>(elapsed - delay) /
                static_cast<double>(duration)
            );
        }

        result.push_back({
            elapsed,
            progress
        });
    }

    return result;
}


// ============================================================================
// 12. ACCESSIBILITY POLICY
// ============================================================================

struct AccessibilityPolicy {
    bool provideFocusVisible = true;
    bool respectReducedMotion = true;
    bool avoidHoverOnlyInteraction = true;
    bool avoidColorOnlyState = true;
};


std::vector<std::string> auditAccessibility(
    const AccessibilityPolicy& policy
) {
    std::vector<std::string> findings;

    if (!policy.provideFocusVisible) {
        findings.push_back(
            "Keyboard focus does not have a dedicated visual treatment."
        );
    }

    if (!policy.respectReducedMotion) {
        findings.push_back(
            "prefers-reduced-motion is not respected."
        );
    }

    if (!policy.avoidHoverOnlyInteraction) {
        findings.push_back(
            "The design may depend exclusively on hover."
        );
    }

    if (!policy.avoidColorOnlyState) {
        findings.push_back(
            "State may be communicated only through color."
        );
    }

    if (findings.empty()) {
        findings.push_back(
            "No issues found in the configured accessibility policy."
        );
    }

    return findings;
}


// ============================================================================
// 13. CASE STUDY: DASHBOARD CARD
// ============================================================================

class DashboardCard {
private:
    bool highlighted_ = false;

public:
    void setHighlighted(bool highlighted) {
        highlighted_ = highlighted;
    }

    bool isHighlighted() const {
        return highlighted_;
    }

    std::string transformCSS() const {
        return highlighted_
            ? "translateY(-6px) scale(1.02)"
            : "translateY(0) scale(1)";
    }

    std::string backgroundCSS() const {
        return highlighted_
            ? "#1f2937"
            : "#111827";
    }

    std::string borderCSS() const {
        return highlighted_
            ? "#60a5fa"
            : "#374151";
    }
};


std::string generateDashboardCardCSS(
    const MotionDesignSystem& designSystem
) {
    const Transition transformTransition =
        designSystem.createTransition(
            "standard",
            "transform"
        );

    const Transition backgroundTransition =
        designSystem.createTransition(
            "standard",
            "background-color"
        );

    const Transition borderTransition =
        designSystem.createTransition(
            "standard",
            "border-color"
        );

    const Transition shadowTransition(
        "box-shadow",
        300,
        std::make_shared<EaseOutTiming>()
    );

    std::vector<Transition> transitions = {
        transformTransition,
        backgroundTransition,
        borderTransition,
        shadowTransition
    };

    std::ostringstream output;

    output
        << ".dashboard-card {\n"
        << "    padding: 24px;\n"
        << "    border: 1px solid #374151;\n"
        << "    border-radius: 16px;\n"
        << "    background: #111827;\n"
        << "    transform: translateY(0) scale(1);\n"
        << "    transition: ";

    for (std::size_t index = 0; index < transitions.size(); ++index) {
        if (index > 0) {
            output << ", ";
        }

        output << transitions[index].toCSS();
    }

    output
        << ";\n"
        << "}\n\n"
        << ".dashboard-card:hover {\n"
        << "    transform: translateY(-6px) scale(1.02);\n"
        << "    background: #1f2937;\n"
        << "    border-color: #60a5fa;\n"
        << "    box-shadow: 0 18px 40px rgb(0 0 0 / 0.35);\n"
        << "}\n\n"
        << ".dashboard-card:focus-visible {\n"
        << "    outline: 3px solid #60a5fa;\n"
        << "    outline-offset: 4px;\n"
        << "}\n\n"
        << "@media (prefers-reduced-motion: reduce) {\n"
        << "    .dashboard-card {\n"
        << "        transition-duration: 0.01ms;\n"
        << "    }\n"
        << "}\n";

    return output.str();
}


// ============================================================================
// 14. PERFORMANCE REPORT
// ============================================================================

struct PerformanceReport {
    std::string property;
    PerformanceCategory category;
    std::string recommendation;
};


PerformanceReport createPerformanceReport(
    const std::string& property
) {
    const PerformanceCategory category =
        classifyProperty(property);

    std::string recommendation;

    switch (category) {
        case PerformanceCategory::CompositingFriendly:
            recommendation =
                "Often a suitable choice for interactive visual movement "
                "or fading.";
            break;

        case PerformanceCategory::LayoutSensitive:
            recommendation =
                "Test layout impact; consider whether transform can express "
                "the visual movement instead.";
            break;

        case PerformanceCategory::PaintSensitive:
            recommendation =
                "Keep effects simple and measure rendering cost.";
            break;

        case PerformanceCategory::Unknown:
            recommendation =
                "Verify the property's interpolation and rendering behavior.";
            break;
    }

    return {
        property,
        category,
        recommendation
    };
}


// ============================================================================
// 15. SECURITY / ROBUSTNESS CONSIDERATIONS
// ============================================================================

bool isSafePropertyName(const std::string& property) {
    /*
     * The case study accepts only a conservative property-name grammar.
     * This matters if CSS is generated from external configuration.
     *
     * Production systems should not blindly concatenate untrusted strings
     * into CSS. The whitelist approach below prevents characters that could
     * change the structure of a generated declaration.
     */
    if (property.empty()) {
        return false;
    }

    for (unsigned char character : property) {
        const bool valid =
            std::isalnum(character) ||
            character == '-';

        if (!valid) {
            return false;
        }
    }

    return true;
}


// ============================================================================
// 16. UNIT TESTS
// ============================================================================

void require(
    bool condition,
    const std::string& message
) {
    if (!condition) {
        throw std::runtime_error(
            "Test failed: " + message
        );
    }
}


void runTests() {
    require(
        clamp(-1.0) == 0.0,
        "clamp lower boundary"
    );

    require(
        clamp(0.5) == 0.5,
        "clamp middle"
    );

    require(
        clamp(2.0) == 1.0,
        "clamp upper boundary"
    );

    require(
        interpolate(0.0, 100.0, 0.5) == 50.0,
        "interpolation"
    );

    const auto linear =
        std::make_shared<LinearTiming>();

    Transition transition(
        "opacity",
        300,
        linear,
        100
    );

    require(
        transition.totalTime() == 400,
        "transition total time"
    );

    require(
        transition.toCSS() ==
            "opacity 300ms linear 100ms",
        "transition CSS generation"
    );

    require(
        isSafePropertyName("background-color"),
        "safe CSS property"
    );

    require(
        !isSafePropertyName("color;body{display:none}"),
        "unsafe CSS property rejected"
    );

    const auto timeline =
        createTimeline(300, 100);

    require(
        timeline.front().progress == 0.0,
        "timeline starts at zero"
    );

    require(
        timeline.back().progress == 1.0,
        "timeline ends at one"
    );

    const auto cubic =
        std::make_shared<CubicBezierTiming>(
            0.25,
            0.1,
            0.25,
            1.0
        );

    require(
        std::abs(cubic->evaluate(0.0)) < 1e-9,
        "cubic start"
    );

    require(
        std::abs(cubic->evaluate(1.0) - 1.0) < 1e-9,
        "cubic end"
    );

    std::cout << "\nAll C++ tests passed.\n";
}


// ============================================================================
// 17. MAIN CASE STUDY
// ============================================================================

int main() {
    try {
        std::cout
            << "============================================================\n"
            << "CSS TRANSITIONS - C++ DESIGN-SYSTEM CASE STUDY\n"
            << "============================================================\n";

        // --------------------------------------------------------------------
        // Create the design system.
        // --------------------------------------------------------------------

        MotionDesignSystem designSystem;

        designSystem.addToken({
            "instant",
            0,
            std::make_shared<LinearTiming>()
        });

        designSystem.addToken({
            "quick",
            120,
            std::make_shared<EaseOutTiming>()
        });

        designSystem.addToken({
            "standard",
            220,
            std::make_shared<CubicBezierTiming>(
                0.2,
                0.8,
                0.2,
                1.0
            )
        });

        designSystem.addToken({
            "emphasis",
            400,
            std::make_shared<EaseInOutTiming>()
        });

        // --------------------------------------------------------------------
        // Generate the transition specification for a button.
        // --------------------------------------------------------------------

        const Transition buttonTransform =
            designSystem.createTransition(
                "quick",
                "transform"
            );

        const Transition buttonOpacity =
            designSystem.createTransition(
                "quick",
                "opacity"
            );

        std::cout
            << "\nButton transitions:\n"
            << "  " << buttonTransform.toCSS() << "\n"
            << "  " << buttonOpacity.toCSS() << "\n";

        // --------------------------------------------------------------------
        // Validate transitions.
        // --------------------------------------------------------------------

        const Transition expensiveTransition(
            "width",
            1200,
            std::make_shared<EaseInOutTiming>(),
            100
        );

        std::cout
            << "\nValidation report for width transition:\n";

        for (const ValidationIssue& issue :
             validateTransition(expensiveTransition)) {
            std::cout
                << "  ["
                << issue.severity
                << "] "
                << issue.message
                << "\n";
        }

        // --------------------------------------------------------------------
        // Model button states.
        // --------------------------------------------------------------------

        InteractiveButton button;

        std::cout << "\nButton visual states:\n";

        const std::vector<ButtonState> states = {
            ButtonState::Idle,
            ButtonState::Hover,
            ButtonState::Focus,
            ButtonState::Active,
            ButtonState::Disabled
        };

        for (ButtonState state : states) {
            button.setState(state);

            const ButtonVisualState visual =
                button.visualState();

            std::cout
                << "  "
                << std::setw(8)
                << buttonStateName(state)
                << " | translateY="
                << std::setw(5)
                << visual.translateY
                << "px"
                << " | scale="
                << std::fixed
                << std::setprecision(2)
                << visual.scale
                << " | opacity="
                << visual.opacity
                << " | focusRing="
                << std::boolalpha
                << visual.focusRing
                << "\n";
        }

        // --------------------------------------------------------------------
        // Simulate an ease-out transform.
        // --------------------------------------------------------------------

        std::cout
            << "\nTransform simulation: 0px -> -6px\n";

        const Transition cardMovement(
            "transform",
            240,
            std::make_shared<EaseOutTiming>()
        );

        const auto samples =
            simulateTransition(
                0.0,
                -6.0,
                cardMovement,
                9
            );

        std::cout
            << std::left
            << std::setw(14)
            << "time"
            << std::setw(14)
            << "progress"
            << "value\n";

        for (const SimulationPoint& point : samples) {
            std::cout
                << std::fixed
                << std::setprecision(3)
                << std::setw(14)
                << point.timeProgress
                << std::setw(14)
                << point.visualProgress
                << point.value
                << "px\n";
        }

        // --------------------------------------------------------------------
        // Delay model.
        // --------------------------------------------------------------------

        std::cout
            << "\nTransition timeline: 200ms delay + 400ms duration\n";

        const auto timeline =
            createTimeline(400, 200, 9);

        for (const TimelinePoint& point : timeline) {
            std::cout
                << "  "
                << std::setw(4)
                << point.elapsedMilliseconds
                << "ms | progress="
                << std::fixed
                << std::setprecision(2)
                << point.progress
                << "\n";
        }

        // --------------------------------------------------------------------
        // Dashboard card case study.
        // --------------------------------------------------------------------

        DashboardCard card;

        std::cout
            << "\nDashboard card states:\n";

        card.setHighlighted(false);

        std::cout
            << "  normal transform: "
            << card.transformCSS()
            << "\n"
            << "  normal background: "
            << card.backgroundCSS()
            << "\n"
            << "  normal border: "
            << card.borderCSS()
            << "\n";

        card.setHighlighted(true);

        std::cout
            << "  hover transform: "
            << card.transformCSS()
            << "\n"
            << "  hover background: "
            << card.backgroundCSS()
            << "\n"
            << "  hover border: "
            << card.borderCSS()
            << "\n";

        // --------------------------------------------------------------------
        // Generate production-oriented CSS.
        // --------------------------------------------------------------------

        std::cout
            << "\nGenerated dashboard-card CSS:\n\n"
            << generateDashboardCardCSS(designSystem)
            << "\n";

        // --------------------------------------------------------------------
        // Performance report.
        // --------------------------------------------------------------------

        std::cout
            << "Performance classifications:\n";

        for (const std::string& property : {
            std::string("transform"),
            std::string("opacity"),
            std::string("width"),
            std::string("height"),
            std::string("box-shadow")
        }) {
            const PerformanceReport report =
                createPerformanceReport(property);

            std::cout
                << "  "
                << std::setw(12)
                << report.property
                << " | "
                << std::setw(22)
                << performanceCategoryName(
                    report.category
                )
                << " | "
                << report.recommendation
                << "\n";
        }

        // --------------------------------------------------------------------
        // Accessibility audit.
        // --------------------------------------------------------------------

        std::cout
            << "\nAccessibility audit:\n";

        AccessibilityPolicy accessibilityPolicy;

        for (const std::string& finding :
             auditAccessibility(accessibilityPolicy)) {
            std::cout
                << "  "
                << finding
                << "\n";
        }

        // --------------------------------------------------------------------
        // Security-oriented CSS property validation.
        // --------------------------------------------------------------------

        std::cout
            << "\nCSS property validation:\n";

        const std::vector<std::string> properties = {
            "background-color",
            "transform",
            "opacity",
            "color;body{display:none}"
        };

        for (const std::string& property : properties) {
            std::cout
                << "  "
                << property
                << " -> "
                << (
                    isSafePropertyName(property)
                        ? "accepted"
                        : "rejected"
                )
                << "\n";
        }

        // --------------------------------------------------------------------
        // Tests.
        // --------------------------------------------------------------------

        runTests();

        std::cout
            << "\n============================================================\n"
            << "CASE STUDY COMPLETE\n"
            << "============================================================\n";

        return 0;
    }
    catch (const std::exception& error) {
        std::cerr
            << "\nERROR: "
            << error.what()
            << "\n";

        return 1;
    }
}
