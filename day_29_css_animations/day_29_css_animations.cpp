/*
    CSS Animations: Browser-Style Motion Engine Case Study
    =======================================================

    This C++17 program models a realistic animation engine for a dashboard
    component. It demonstrates:

      - keyframes
      - interpolation
      - easing
      - transforms
      - opacity
      - animation duration
      - delay
      - iteration count
      - animation direction
      - fill modes
      - animation playback
      - performance budgeting
      - property classification
      - reduced-motion policy
      - validation
      - rendering-frame simulation
      - complexity considerations

    The program intentionally models the concepts instead of implementing a
    browser. A browser has substantially more sophisticated style,
    layout, paint, compositing, and rendering systems.

    Compile:
        g++ -std=c++17 -O2 animation_case_study.cpp -o animation_case_study

    Run:
        ./animation_case_study
*/

#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <numeric>
#include <optional>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace animation {

constexpr double EPSILON = 1e-9;

// ============================================================================
// 1. BASIC UTILITIES
// ============================================================================

double clamp(double value, double minimum = 0.0, double maximum = 1.0) {
    return std::max(minimum, std::min(maximum, value));
}

double lerp(double start, double end, double progress) {
    return start + (end - start) * clamp(progress);
}

double degreesToRadians(double degrees) {
    constexpr double PI = 3.14159265358979323846;
    return degrees * PI / 180.0;
}

// ============================================================================
// 2. EASING FUNCTIONS
// ============================================================================

using EasingFunction = double (*)(double);

double linear(double progress) {
    return progress;
}

double easeIn(double progress) {
    return progress * progress;
}

double easeOut(double progress) {
    return 1.0 - std::pow(1.0 - progress, 2.0);
}

double easeInOut(double progress) {
    if (progress < 0.5) {
        return 2.0 * progress * progress;
    }

    return 1.0 - std::pow(-2.0 * progress + 2.0, 2.0) / 2.0;
}

double easeInCubic(double progress) {
    return std::pow(progress, 3.0);
}

double easeOutCubic(double progress) {
    return 1.0 - std::pow(1.0 - progress, 3.0);
}

double easeOutBack(double progress) {
    const double c1 = 1.70158;
    const double c3 = c1 + 1.0;

    return (
        1.0 +
        c3 * std::pow(progress - 1.0, 3.0) +
        c1 * std::pow(progress - 1.0, 2.0)
    );
}

// ============================================================================
// 3. TRANSFORM
// ============================================================================

struct Transform {
    double x = 0.0;
    double y = 0.0;
    double scaleX = 1.0;
    double scaleY = 1.0;
    double rotationDegrees = 0.0;
    double skewXDegrees = 0.0;
    double skewYDegrees = 0.0;

    Transform interpolate(
        const Transform& other,
        double progress
    ) const {
        return Transform{
            lerp(x, other.x, progress),
            lerp(y, other.y, progress),
            lerp(scaleX, other.scaleX, progress),
            lerp(scaleY, other.scaleY, progress),
            lerp(rotationDegrees, other.rotationDegrees, progress),
            lerp(skewXDegrees, other.skewXDegrees, progress),
            lerp(skewYDegrees, other.skewYDegrees, progress)
        };
    }

    std::string toString() const {
        std::ostringstream output;

        bool hasTransform = false;

        if (std::abs(x) > EPSILON || std::abs(y) > EPSILON) {
            output
                << "translate("
                << std::fixed << std::setprecision(2)
                << x << "px, "
                << y << "px)";

            hasTransform = true;
        }

        if (
            std::abs(scaleX - 1.0) > EPSILON ||
            std::abs(scaleY - 1.0) > EPSILON
        ) {
            if (hasTransform) {
                output << " ";
            }

            output
                << "scale("
                << std::fixed << std::setprecision(3)
                << scaleX << ", "
                << scaleY << ")";

            hasTransform = true;
        }

        if (std::abs(rotationDegrees) > EPSILON) {
            if (hasTransform) {
                output << " ";
            }

            output
                << "rotate("
                << std::fixed << std::setprecision(2)
                << rotationDegrees
                << "deg)";

            hasTransform = true;
        }

        if (std::abs(skewXDegrees) > EPSILON) {
            if (hasTransform) {
                output << " ";
            }

            output
                << "skewX("
                << std::fixed << std::setprecision(2)
                << skewXDegrees
                << "deg)";

            hasTransform = true;
        }

        if (std::abs(skewYDegrees) > EPSILON) {
            if (hasTransform) {
                output << " ";
            }

            output
                << "skewY("
                << std::fixed << std::setprecision(2)
                << skewYDegrees
                << "deg)";

            hasTransform = true;
        }

        return hasTransform ? output.str() : "none";
    }
};

// ============================================================================
// 4. MATRIX FOR TRANSFORM COMPOSITION
// ============================================================================

struct Matrix3 {
    double values[3][3] = {
        {1, 0, 0},
        {0, 1, 0},
        {0, 0, 1}
    };

    static Matrix3 translation(double x, double y) {
        Matrix3 matrix;
        matrix.values[0][2] = x;
        matrix.values[1][2] = y;
        return matrix;
    }

    static Matrix3 rotation(double degrees) {
        Matrix3 matrix;

        const double radians = degreesToRadians(degrees);
        const double cosine = std::cos(radians);
        const double sine = std::sin(radians);

        matrix.values[0][0] = cosine;
        matrix.values[0][1] = -sine;
        matrix.values[1][0] = sine;
        matrix.values[1][1] = cosine;

        return matrix;
    }

    Matrix3 operator*(const Matrix3& other) const {
        Matrix3 result;

        for (int row = 0; row < 3; ++row) {
            for (int column = 0; column < 3; ++column) {
                result.values[row][column] = 0;

                for (int k = 0; k < 3; ++k) {
                    result.values[row][column] +=
                        values[row][k] * other.values[k][column];
                }
            }
        }

        return result;
    }

    std::pair<double, double> apply(
        double x,
        double y
    ) const {
        const double outputX =
            values[0][0] * x +
            values[0][1] * y +
            values[0][2];

        const double outputY =
            values[1][0] * x +
            values[1][1] * y +
            values[1][2];

        return {outputX, outputY};
    }
};

// ============================================================================
// 5. KEYFRAME
// ============================================================================

struct Keyframe {
    double offset = 0.0;
    Transform transform{};
    double opacity = 1.0;

    Keyframe(
        double keyframeOffset,
        const Transform& keyframeTransform,
        double keyframeOpacity = 1.0
    )
        : offset(keyframeOffset),
          transform(keyframeTransform),
          opacity(keyframeOpacity) {
        if (offset < 0.0 || offset > 1.0) {
            throw std::invalid_argument(
                "Keyframe offset must be between 0 and 1."
            );
        }

        if (opacity < 0.0 || opacity > 1.0) {
            throw std::invalid_argument(
                "Opacity must be between 0 and 1."
            );
        }
    }
};

// ============================================================================
// 6. ANIMATION ENUMERATIONS
// ============================================================================

enum class Direction {
    Normal,
    Reverse,
    Alternate,
    AlternateReverse
};

enum class FillMode {
    None,
    Forwards,
    Backwards,
    Both
};

enum class Phase {
    Before,
    Active,
    After
};

std::string directionName(Direction direction) {
    switch (direction) {
        case Direction::Normal:
            return "normal";
        case Direction::Reverse:
            return "reverse";
        case Direction::Alternate:
            return "alternate";
        case Direction::AlternateReverse:
            return "alternate-reverse";
    }

    return "unknown";
}

std::string fillModeName(FillMode fillMode) {
    switch (fillMode) {
        case FillMode::None:
            return "none";
        case FillMode::Forwards:
            return "forwards";
        case FillMode::Backwards:
            return "backwards";
        case FillMode::Both:
            return "both";
    }

    return "unknown";
}

// ============================================================================
// 7. ANIMATION STATE
// ============================================================================

struct AnimationState {
    Transform transform{};
    double opacity = 1.0;
    Phase phase = Phase::Active;
    int iteration = 0;
};

// ============================================================================
// 8. ANIMATION ENGINE
// ============================================================================

class Animation {
private:
    std::string name_;
    double durationSeconds_;
    double delaySeconds_;
    EasingFunction easing_;
    std::optional<double> iterationCount_;
    Direction direction_;
    FillMode fillMode_;
    std::vector<Keyframe> keyframes_;

    std::pair<double, int> calculateIterationProgress(
        double activeTime
    ) const {
        if (activeTime <= 0.0) {
            return {0.0, 0};
        }

        const double activeDuration =
            iterationCount_.has_value()
                ? durationSeconds_ * iterationCount_.value()
                : std::numeric_limits<double>::infinity();

        if (activeTime >= activeDuration) {
            const int finalIteration =
                iterationCount_.has_value()
                    ? std::max(
                          0,
                          static_cast<int>(
                              std::ceil(iterationCount_.value())
                          ) - 1
                      )
                    : 0;

            return {1.0, finalIteration};
        }

        const double rawIteration =
            activeTime / durationSeconds_;

        const int iteration =
            static_cast<int>(std::floor(rawIteration));

        double progress =
            rawIteration - static_cast<double>(iteration);

        switch (direction_) {
            case Direction::Normal:
                break;

            case Direction::Reverse:
                progress = 1.0 - progress;
                break;

            case Direction::Alternate:
                if (iteration % 2 == 1) {
                    progress = 1.0 - progress;
                }
                break;

            case Direction::AlternateReverse:
                if (iteration % 2 == 0) {
                    progress = 1.0 - progress;
                }
                break;
        }

        return {progress, iteration};
    }

    AnimationState interpolateKeyframes(
        double normalizedProgress,
        Phase phase,
        int iteration
    ) const {
        if (keyframes_.empty()) {
            throw std::logic_error(
                "Animation must contain keyframes."
            );
        }

        const double eased =
            clamp(easing_(clamp(normalizedProgress)));

        if (eased <= keyframes_.front().offset) {
            return {
                keyframes_.front().transform,
                keyframes_.front().opacity,
                phase,
                iteration
            };
        }

        if (eased >= keyframes_.back().offset) {
            return {
                keyframes_.back().transform,
                keyframes_.back().opacity,
                phase,
                iteration
            };
        }

        for (std::size_t index = 0;
             index + 1 < keyframes_.size();
             ++index) {
            const Keyframe& left = keyframes_[index];
            const Keyframe& right = keyframes_[index + 1];

            if (
                eased >= left.offset &&
                eased <= right.offset
            ) {
                const double interval =
                    right.offset - left.offset;

                const double localProgress =
                    std::abs(interval) < EPSILON
                        ? 1.0
                        : (eased - left.offset) / interval;

                return {
                    left.transform.interpolate(
                        right.transform,
                        localProgress
                    ),
                    lerp(
                        left.opacity,
                        right.opacity,
                        localProgress
                    ),
                    phase,
                    iteration
                };
            }
        }

        throw std::logic_error(
            "Could not resolve keyframe interval."
        );
    }

public:
    Animation(
        std::string name,
        double durationSeconds,
        double delaySeconds,
        EasingFunction easing,
        std::optional<double> iterationCount,
        Direction direction,
        FillMode fillMode,
        std::vector<Keyframe> keyframes
    )
        : name_(std::move(name)),
          durationSeconds_(durationSeconds),
          delaySeconds_(delaySeconds),
          easing_(easing),
          iterationCount_(iterationCount),
          direction_(direction),
          fillMode_(fillMode),
          keyframes_(std::move(keyframes)) {
        if (name_.empty()) {
            throw std::invalid_argument(
                "Animation name cannot be empty."
            );
        }

        if (durationSeconds_ <= 0.0) {
            throw std::invalid_argument(
                "Animation duration must be positive."
            );
        }

        if (!easing_) {
            throw std::invalid_argument(
                "An easing function is required."
            );
        }

        if (iterationCount_.has_value() &&
            iterationCount_.value() <= 0.0) {
            throw std::invalid_argument(
                "Iteration count must be positive."
            );
        }

        if (keyframes_.empty()) {
            throw std::invalid_argument(
                "Animation requires at least one keyframe."
            );
        }

        std::sort(
            keyframes_.begin(),
            keyframes_.end(),
            [](const Keyframe& left, const Keyframe& right) {
                return left.offset < right.offset;
            }
        );
    }

    const std::string& name() const {
        return name_;
    }

    double duration() const {
        return durationSeconds_;
    }

    double delay() const {
        return delaySeconds_;
    }

    AnimationState stateAt(double timeSeconds) const {
        if (timeSeconds < delaySeconds_) {
            if (
                fillMode_ == FillMode::Backwards ||
                fillMode_ == FillMode::Both
            ) {
                return {
                    keyframes_.front().transform,
                    keyframes_.front().opacity,
                    Phase::Before,
                    0
                };
            }

            return {
                Transform{},
                1.0,
                Phase::Before,
                0
            };
        }

        const double activeTime =
            timeSeconds - delaySeconds_;

        const double activeDuration =
            iterationCount_.has_value()
                ? durationSeconds_ * iterationCount_.value()
                : std::numeric_limits<double>::infinity();

        if (activeTime >= activeDuration) {
            if (
                fillMode_ == FillMode::Forwards ||
                fillMode_ == FillMode::Both
            ) {
                const auto [progress, iteration] =
                    calculateIterationProgress(activeTime);

                return interpolateKeyframes(
                    progress,
                    Phase::After,
                    iteration
                );
            }

            return {
                Transform{},
                1.0,
                Phase::After,
                0
            };
        }

        const auto [progress, iteration] =
            calculateIterationProgress(activeTime);

        return interpolateKeyframes(
            progress,
            Phase::Active,
            iteration
        );
    }
};

// ============================================================================
// 9. PERFORMANCE MODEL
// ============================================================================

enum class PropertyCategory {
    CompositorFriendly,
    PaintRelated,
    LayoutRelated
};

std::string categoryName(PropertyCategory category) {
    switch (category) {
        case PropertyCategory::CompositorFriendly:
            return "compositor-friendly";
        case PropertyCategory::PaintRelated:
            return "paint-related";
        case PropertyCategory::LayoutRelated:
            return "layout-related";
    }

    return "unknown";
}

PropertyCategory classifyProperty(
    const std::string& property
) {
    if (
        property == "transform" ||
        property == "opacity"
    ) {
        return PropertyCategory::CompositorFriendly;
    }

    if (
        property == "background-color" ||
        property == "box-shadow" ||
        property == "filter"
    ) {
        return PropertyCategory::PaintRelated;
    }

    return PropertyCategory::LayoutRelated;
}

struct PerformanceSample {
    double layoutMs;
    double paintMs;
    double compositeMs;

    double totalMs() const {
        return layoutMs + paintMs + compositeMs;
    }
};

class PerformanceSimulator {
private:
    std::vector<PerformanceSample> samples_;

public:
    void addSample(
        const PerformanceSample& sample
    ) {
        if (
            sample.layoutMs < 0 ||
            sample.paintMs < 0 ||
            sample.compositeMs < 0
        ) {
            throw std::invalid_argument(
                "Performance costs cannot be negative."
            );
        }

        samples_.push_back(sample);
    }

    double averageFrameTime() const {
        if (samples_.empty()) {
            return 0;
        }

        const double total =
            std::accumulate(
                samples_.begin(),
                samples_.end(),
                0.0,
                [](double sum, const PerformanceSample& sample) {
                    return sum + sample.totalMs();
                }
            );

        return total / samples_.size();
    }

    double percentageAboveBudget(
        double budgetMs
    ) const {
        if (samples_.empty()) {
            return 0;
        }

        const std::size_t slowFrames =
            std::count_if(
                samples_.begin(),
                samples_.end(),
                [budgetMs](const PerformanceSample& sample) {
                    return sample.totalMs() > budgetMs;
                }
            );

        return (
            static_cast<double>(slowFrames) /
            samples_.size()
        ) * 100.0;
    }
};

PerformanceSimulator simulateProperty(
    const std::string& property,
    int frameCount
) {
    PerformanceSimulator simulator;

    const PropertyCategory category =
        classifyProperty(property);

    double layoutCost = 0;
    double paintCost = 0;
    double compositeCost = 1.5;

    switch (category) {
        case PropertyCategory::CompositorFriendly:
            layoutCost = 0.2;
            paintCost = 0.3;
            break;

        case PropertyCategory::PaintRelated:
            layoutCost = 0.4;
            paintCost = 6.0;
            break;

        case PropertyCategory::LayoutRelated:
            layoutCost = 7.0;
            paintCost = 6.0;
            break;
    }

    for (int frame = 0; frame < frameCount; ++frame) {
        const double variation =
            std::sin(static_cast<double>(frame) / 5.0) * 0.3;

        simulator.addSample({
            layoutCost,
            paintCost,
            std::max(
                0.1,
                compositeCost + variation
            )
        });
    }

    return simulator;
}

// ============================================================================
// 10. REDUCED MOTION POLICY
// ============================================================================

struct MotionPolicy {
    bool prefersReducedMotion = false;

    bool shouldAnimate() const {
        return !prefersReducedMotion;
    }

    double effectiveDuration(
        double normalDuration
    ) const {
        if (normalDuration < 0) {
            throw std::invalid_argument(
                "Duration cannot be negative."
            );
        }

        return prefersReducedMotion
            ? 1.0
            : normalDuration;
    }
};

// ============================================================================
// 11. DASHBOARD CARD MODEL
// ============================================================================

struct DashboardCard {
    int id;
    std::string title;
    double targetX;
    double targetY;
    double scale;
    double opacity;
};

class DashboardAnimationSystem {
private:
    std::vector<DashboardCard> cards_;

public:
    void addCard(const DashboardCard& card) {
        if (card.id <= 0) {
            throw std::invalid_argument(
                "Card ID must be positive."
            );
        }

        if (card.title.empty()) {
            throw std::invalid_argument(
                "Card title cannot be empty."
            );
        }

        if (
            card.scale <= 0 ||
            card.opacity < 0 ||
            card.opacity > 1
        ) {
            throw std::invalid_argument(
                "Invalid card scale or opacity."
            );
        }

        const bool duplicate =
            std::any_of(
                cards_.begin(),
                cards_.end(),
                [&card](const DashboardCard& existing) {
                    return existing.id == card.id;
                }
            );

        if (duplicate) {
            throw std::invalid_argument(
                "Duplicate card ID."
            );
        }

        cards_.push_back(card);
    }

    std::size_t size() const {
        return cards_.size();
    }

    const DashboardCard& cardAt(
        std::size_t index
    ) const {
        if (index >= cards_.size()) {
            throw std::out_of_range(
                "Dashboard card index out of range."
            );
        }

        return cards_[index];
    }
};

// ============================================================================
// 12. REPORTING
// ============================================================================

void printState(
    double time,
    const AnimationState& state
) {
    std::string phase;

    switch (state.phase) {
        case Phase::Before:
            phase = "before";
            break;
        case Phase::Active:
            phase = "active";
            break;
        case Phase::After:
            phase = "after";
            break;
    }

    std::cout
        << "t=" << std::fixed << std::setprecision(2)
        << time
        << "s"
        << " | phase=" << std::setw(6) << phase
        << " | iteration=" << state.iteration
        << " | transform=" << state.transform.toString()
        << " | opacity=" << std::setprecision(3)
        << state.opacity
        << '\n';
}

// ============================================================================
// 13. CASE STUDY
// ============================================================================

void runDashboardCaseStudy() {
    std::cout
        << "\n============================================================\n"
        << "CSS Animation Dashboard Case Study\n"
        << "============================================================\n";

    /*
        Scenario:

        A financial analytics dashboard contains cards that enter the viewport.
        Each card begins slightly below its final position, fades in, reaches
        full opacity, and settles into its normal scale.

        The visual motion is represented by transform and opacity because the
        intended effect does not require changing document layout.
    */

    MotionPolicy userPolicy{
        false
    };

    const double normalDuration = 0.75;

    const double duration =
        userPolicy.effectiveDuration(normalDuration);

    Animation cardEntrance(
        "dashboard-card-enter",
        duration,
        0.0,
        easeOutCubic,
        1.0,
        Direction::Normal,
        FillMode::Forwards,
        {
            Keyframe{
                0.0,
                Transform{
                    0,
                    28,
                    0.96,
                    0.96,
                    0,
                    0,
                    0
                },
                0.0
            },

            Keyframe{
                0.70,
                Transform{
                    0,
                    -3,
                    1.01,
                    1.01,
                    0,
                    0,
                    0
                },
                0.85
            },

            Keyframe{
                1.0,
                Transform{
                    0,
                    0,
                    1,
                    1,
                    0,
                    0,
                    0
                },
                1.0
            }
        }
    );

    std::cout << "\nAnimation timeline:\n";

    for (
        double time = 0.0;
        time <= duration + EPSILON;
        time += 0.125
    ) {
        printState(
            time,
            cardEntrance.stateAt(time)
        );
    }

    std::cout
        << "\nThe equivalent CSS structure would conceptually be:\n"
        << "  @keyframes dashboard-card-enter { ... }\n"
        << "  .card { animation: dashboard-card-enter "
        << duration << "s ease-out forwards; }\n";
}

// ============================================================================
// 14. PERFORMANCE CASE STUDY
// ============================================================================

void runPerformanceCaseStudy() {
    std::cout
        << "\n============================================================\n"
        << "Performance Case Study\n"
        << "============================================================\n";

    const std::vector<std::string> properties{
        "transform",
        "opacity",
        "box-shadow",
        "width",
        "left"
    };

    constexpr double budget60Hz = 16.67;
    constexpr double budget120Hz = 8.33;

    for (const auto& property : properties) {
        const PropertyCategory category =
            classifyProperty(property);

        const auto simulator =
            simulateProperty(property, 120);

        std::cout
            << std::left
            << std::setw(18)
            << property
            << " category="
            << std::setw(20)
            << categoryName(category)
            << " avg="
            << std::fixed
            << std::setprecision(2)
            << simulator.averageFrameTime()
            << "ms"
            << " >60Hz budget="
            << std::setprecision(1)
            << simulator.percentageAboveBudget(
                   budget60Hz
               )
            << "%"
            << " >120Hz budget="
            << simulator.percentageAboveBudget(
                   budget120Hz
               )
            << "%\n";
    }

    std::cout
        << "\nA 60Hz display provides approximately "
        << budget60Hz
        << "ms per frame.\n";

    std::cout
        << "A 120Hz display provides approximately "
        << budget120Hz
        << "ms per frame.\n";

    std::cout
        << "These budgets cover the entire frame, not just animation work.\n";
}

// ============================================================================
// 15. TRANSFORM ORDER CASE STUDY
// ============================================================================

void runTransformCompositionCaseStudy() {
    std::cout
        << "\n============================================================\n"
        << "Transform Composition Case Study\n"
        << "============================================================\n";

    const Matrix3 translation =
        Matrix3::translation(100, 0);

    const Matrix3 rotation =
        Matrix3::rotation(90);

    /*
        Matrix multiplication is order-sensitive.

        In CSS, transform functions are composed in a defined order. Changing
        the order can change the coordinate system in which later operations
        are applied.
    */

    const Matrix3 translateThenRotate =
        rotation * translation;

    const Matrix3 rotateThenTranslate =
        translation * rotation;

    const auto firstResult =
        translateThenRotate.apply(1, 0);

    const auto secondResult =
        rotateThenTranslate.apply(1, 0);

    std::cout
        << "translate then rotate -> ("
        << firstResult.first
        << ", "
        << firstResult.second
        << ")\n";

    std::cout
        << "rotate then translate -> ("
        << secondResult.first
        << ", "
        << secondResult.second
        << ")\n";

    std::cout
        << "\nThe results differ because matrix multiplication is not "
        << "generally commutative.\n";
}

// ============================================================================
// 16. ITERATION CASE STUDY
// ============================================================================

void runIterationCaseStudy() {
    std::cout
        << "\n============================================================\n"
        << "Iteration and Direction Case Study\n"
        << "============================================================\n";

    const std::vector<Direction> directions{
        Direction::Normal,
        Direction::Reverse,
        Direction::Alternate,
        Direction::AlternateReverse
    };

    for (Direction direction : directions) {
        Animation animation(
            directionName(direction),
            1.0,
            0.0,
            linear,
            3.0,
            direction,
            FillMode::Forwards,
            {
                Keyframe{
                    0,
                    Transform{0, 0, 1, 1, 0, 0, 0},
                    1
                },
                Keyframe{
                    1,
                    Transform{100, 0, 1, 1, 0, 0, 0},
                    1
                }
            }
        );

        std::cout
            << "\n"
            << directionName(direction)
            << ":\n";

        for (
            double time = 0;
            time < 3.0;
            time += 0.5
        ) {
            const auto state =
                animation.stateAt(time);

            std::cout
                << "  t="
                << time
                << " x="
                << state.transform.x
                << " iteration="
                << state.iteration
                << '\n';
        }
    }
}

// ============================================================================
// 17. VALIDATION
// ============================================================================

void runValidationTests() {
    std::cout
        << "\n============================================================\n"
        << "Validation and Failure Conditions\n"
        << "============================================================\n";

    try {
        Animation invalidAnimation(
            "",
            -1.0,
            0.0,
            linear,
            1.0,
            Direction::Normal,
            FillMode::None,
            {
                Keyframe{
                    0,
                    Transform{},
                    1
                }
            }
        );

        (void)invalidAnimation;
    }
    catch (const std::exception& error) {
        std::cout
            << "Invalid animation rejected: "
            << error.what()
            << '\n';
    }

    try {
        Keyframe invalidKeyframe(
            1.5,
            Transform{},
            1
        );

        (void)invalidKeyframe;
    }
    catch (const std::exception& error) {
        std::cout
            << "Invalid keyframe rejected: "
            << error.what()
            << '\n';
    }

    try {
        DashboardAnimationSystem dashboard;

        dashboard.addCard({
            1,
            "Revenue",
            100,
            0,
            1,
            1
        });

        dashboard.addCard({
            1,
            "Duplicate",
            0,
            0,
            1,
            1
        });
    }
    catch (const std::exception& error) {
        std::cout
            << "Invalid dashboard operation rejected: "
            << error.what()
            << '\n';
    }
}

// ============================================================================
// 18. ACCESSIBILITY CASE STUDY
// ============================================================================

void runAccessibilityCaseStudy() {
    std::cout
        << "\n============================================================\n"
        << "Reduced Motion Case Study\n"
        << "============================================================\n";

    MotionPolicy normal{
        false
    };

    MotionPolicy reduced{
        true
    };

    const double duration = 800;

    std::cout
        << "Normal motion duration: "
        << normal.effectiveDuration(duration)
        << "ms\n";

    std::cout
        << "Reduced-motion duration policy: "
        << reduced.effectiveDuration(duration)
        << "ms\n";

    std::cout
        << "Normal animation enabled: "
        << std::boolalpha
        << normal.shouldAnimate()
        << '\n';

    std::cout
        << "Reduced animation enabled: "
        << reduced.shouldAnimate()
        << '\n';

    std::cout
        << "\nIn a browser, a production implementation should normally use "
        << "the prefers-reduced-motion media feature rather than assuming "
        << "a user's preference.\n";
}

// ============================================================================
// 19. ARCHITECTURAL DISCUSSION
// ============================================================================

void printArchitectureNotes() {
    std::cout
        << "\n============================================================\n"
        << "Architecture and Production Notes\n"
        << "============================================================\n";

    std::cout
        << R"(
The modeled rendering path is:

1. Animation configuration
2. Timeline evaluation
3. Iteration and direction resolution
4. Easing calculation
5. Keyframe interval lookup
6. Property interpolation
7. Final transform/opacity state
8. Rendering/compositing

A browser performs many more steps around this process.

Important production distinctions:

- transform and opacity are commonly suitable for independent visual motion.
- layout-related properties may trigger layout recalculation.
- paint-heavy effects can consume substantial rendering time.
- will-change is a hint, not a guarantee of faster animation.
- layer creation can have memory and compositing costs.
- high-refresh-rate displays reduce the available frame budget.
- reduced-motion preferences should be respected.
- animation should not interfere with focus, keyboard navigation, or essential
  content.
- performance should be measured on representative hardware.

The animation engine's keyframe lookup is O(K) per state evaluation, where K
is the number of keyframes. A browser can use more sophisticated internal
structures and optimized rendering pipelines.

For a fixed animation, precomputing interval metadata can reduce repeated
search work. For very large numbers of simultaneously animated objects,
memory allocation and data locality also become relevant.
)";
}

// ============================================================================
// 20. MAIN
// ============================================================================

int main() {
    std::cout
        << "CSS Animations Technical Case Study\n"
        << "C++17\n";

    try {
        runDashboardCaseStudy();
        runPerformanceCaseStudy();
        runTransformCompositionCaseStudy();
        runIterationCaseStudy();
        runValidationTests();
        runAccessibilityCaseStudy();
        printArchitectureNotes();

        std::cout
            << "\n============================================================\n"
            << "Case study completed successfully.\n"
            << "============================================================\n";
    }
    catch (const std::exception& error) {
        std::cerr
            << "Fatal error: "
            << error.what()
            << '\n';

        return 1;
    }

    return 0;
}
