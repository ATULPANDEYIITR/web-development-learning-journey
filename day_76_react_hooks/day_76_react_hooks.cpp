/*
 * React Hooks: C++17 Hook Lifecycle and Dependency Engine.
 *
 * This program models:
 * - Ordered hook slots.
 * - Persistent references.
 * - Memoized values.
 * - Cached callbacks.
 * - Custom hook composition.
 * - Component rendering and state updates.
 * - Dependency comparisons.
 * - Hook-order validation.
 * - Cache statistics.
 *
 * This is a deterministic simulation of hook semantics,
 * not an implementation of the React rendering engine.
 *
 * Compile:
 * g++ -std=c++17 -O2 -Wall -Wextra -pedantic react_hooks.cpp -o react_hooks
 */

#include <algorithm>
#include <cmath>
#include <functional>
#include <iomanip>
#include <iostream>
#include <memory>
#include <optional>
#include <stdexcept>
#include <string>
#include <typeindex>
#include <unordered_map>
#include <utility>
#include <variant>
#include <vector>

using namespace std;


class HookError : public runtime_error {
public:
    explicit HookError(const string& message)
        : runtime_error(message) {}
};


enum class HookKind {
    State,
    Reference,
    Memo,
    Callback
};


string hookName(HookKind kind) {
    switch (kind) {
        case HookKind::State: return "State";
        case HookKind::Reference: return "Reference";
        case HookKind::Memo: return "Memo";
        case HookKind::Callback: return "Callback";
    }

    throw HookError("Unknown hook type.");
}


using Dependency = variant<int, double, string, bool>;


bool sameDependency(
    const Dependency& left,
    const Dependency& right
) {
    if (left.index() != right.index()) {
        return false;
    }

    if (holds_alternative<double>(left)) {
        const double a = get<double>(left);
        const double b = get<double>(right);

        if (isnan(a) && isnan(b)) {
            return true;
        }

        if (a == 0.0 && b == 0.0) {
            return signbit(a) == signbit(b);
        }
    }

    return left == right;
}


bool dependenciesEqual(
    const vector<Dependency>& previous,
    const vector<Dependency>& current
) {
    if (previous.size() != current.size()) {
        throw HookError(
            "Dependency count changed between renders."
        );
    }

    for (size_t i = 0; i < previous.size(); ++i) {
        if (!sameDependency(previous[i], current[i])) {
            return false;
        }
    }

    return true;
}


struct Metrics {
    size_t renders = 0;
    size_t memoComputations = 0;
    size_t memoHits = 0;
    size_t callbackCreations = 0;
    size_t callbackHits = 0;
    size_t stateUpdates = 0;
};


struct HookSlot {
    HookKind kind;
    any value;
    vector<Dependency> dependencies;
    bool initialized = false;
};


template<typename T>
struct Ref {
    T current;

    explicit Ref(T initial)
        : current(move(initial)) {}
};


class HookRuntime {
private:
    string componentName;
    vector<HookSlot> slots;
    vector<HookKind> expectedOrder;

    size_t cursor = 0;
    bool rendering = false;
    bool orderEstablished = false;

    HookSlot& nextSlot(HookKind kind) {
        if (!rendering) {
            throw HookError(
                "Hooks must be called during rendering."
            );
        }

        if (cursor < slots.size()) {
            HookSlot& slot = slots[cursor++];

            if (slot.kind != kind) {
                throw HookError(
                    "Hook type changed at position " +
                    to_string(cursor - 1)
                );
            }

            return slot;
        }

        slots.push_back({
            kind,
            any{},
            {},
            false
        });

        ++cursor;
        return slots.back();
    }

public:
    Metrics metrics;

    explicit HookRuntime(string name)
        : componentName(move(name)) {}

    HookRuntime(const HookRuntime&) = delete;
    HookRuntime& operator=(const HookRuntime&) = delete;

    template<typename T>
    pair<T, function<void(T)>> useState(T initial) {
        HookSlot& slot = nextSlot(HookKind::State);

        if (!slot.initialized) {
            slot.value = initial;
            slot.initialized = true;
        }

        T value = any_cast<T>(slot.value);

        // State slots remain stable because slots are appended
        // before setters are used in subsequent renders.
        const size_t index = cursor - 1;

        function<void(T)> setter =
            [this, index](T nextValue) {
                if (index >= slots.size()) {
                    throw HookError("Invalid state slot.");
                }

                HookSlot& target = slots[index];

                if (target.kind != HookKind::State) {
                    throw HookError("State slot was corrupted.");
                }

                const T previous = any_cast<T>(target.value);

                if (!(previous == nextValue)) {
                    target.value = move(nextValue);
                    ++metrics.stateUpdates;
                }
            };

        return {value, setter};
    }

    template<typename T>
    shared_ptr<Ref<T>> useRef(T initial) {
        HookSlot& slot = nextSlot(HookKind::Reference);

        if (!slot.initialized) {
            slot.value = make_shared<Ref<T>>(move(initial));
            slot.initialized = true;
        }

        try {
            return any_cast<shared_ptr<Ref<T>>>(slot.value);
        } catch (const bad_any_cast&) {
            throw HookError("Reference type mismatch.");
        }
    }

    template<typename T, typename Factory>
    T useMemo(
        Factory factory,
        const vector<Dependency>& dependencies
    ) {
        HookSlot& slot = nextSlot(HookKind::Memo);

        bool recompute = !slot.initialized;

        if (slot.initialized) {
            recompute = !dependenciesEqual(
                slot.dependencies,
                dependencies
            );
        }

        if (recompute) {
            slot.value = factory();
            slot.dependencies = dependencies;
            slot.initialized = true;
            ++metrics.memoComputations;
        } else {
            ++metrics.memoHits;
        }

        try {
            return any_cast<T>(slot.value);
        } catch (const bad_any_cast&) {
            throw HookError("Memoized value type mismatch.");
        }
    }

    template<typename Function>
    Function useCallback(
        Function callback,
        const vector<Dependency>& dependencies
    ) {
        HookSlot& slot = nextSlot(HookKind::Callback);

        bool recreate = !slot.initialized;

        if (slot.initialized) {
            recreate = !dependenciesEqual(
                slot.dependencies,
                dependencies
            );
        }

        if (recreate) {
            slot.value = callback;
            slot.dependencies = dependencies;
            slot.initialized = true;
            ++metrics.callbackCreations;
        } else {
            ++metrics.callbackHits;
        }

        try {
            return any_cast<Function>(slot.value);
        } catch (const bad_any_cast&) {
            throw HookError("Callback type mismatch.");
        }
    }

    template<typename Component, typename... Args>
    auto render(Component component, Args&&... args)
        -> decltype(component(*this, forward<Args>(args)...)) {

        if (rendering) {
            throw HookError("Recursive rendering is not supported.");
        }

        rendering = true;
        cursor = 0;

        try {
            auto result = component(
                *this,
                forward<Args>(args)...
            );

            vector<HookKind> currentOrder;

            for (const HookSlot& slot : slots) {
                currentOrder.push_back(slot.kind);
            }

            if (!orderEstablished) {
                expectedOrder = currentOrder;
                orderEstablished = true;
            } else if (expectedOrder != currentOrder) {
                throw HookError("Hook ordering changed.");
            }

            if (cursor != slots.size()) {
                throw HookError("Some hooks were skipped.");
            }

            ++metrics.renders;
            rendering = false;
            return result;

        } catch (...) {
            rendering = false;
            throw;
        }
    }

    const string& name() const {
        return componentName;
    }
};


// ---------------------------------------------------------
// Repository domain
// ---------------------------------------------------------

struct Repository {
    int id;
    string name;
    int score;
};


vector<Repository> sampleRepositories() {
    return {
        {1, "Repository A", 94},
        {2, "Repository B", 72},
        {3, "Repository C", 85},
        {4, "Repository D", 41},
        {5, "Repository E", 91}
    };
}


// ---------------------------------------------------------
// Custom hooks
// ---------------------------------------------------------

struct CounterResult {
    int value;
    function<void(int)> setValue;
    function<void()> increment;
};


CounterResult useCounter(
    HookRuntime& runtime,
    int initial
) {
    auto [count, setCount] = runtime.useState<int>(initial);

    auto increment = runtime.useCallback<function<void()>>(
        [setCount]() mutable {
            // State updates are explicit and do not mutate
            // the value captured by the previous render.
            // The application supplies the next value.
            setCount(1);
        },
        {}
    );

    return {
        count,
        setCount,
        increment
    };
}


optional<int> usePrevious(
    HookRuntime& runtime,
    int current
) {
    auto reference = runtime.useRef<optional<int>>(nullopt);

    optional<int> previous = reference->current;
    reference->current = current;

    return previous;
}


vector<Repository> useFilteredRepositories(
    HookRuntime& runtime,
    const vector<Repository>& repositories,
    int minimumScore
) {
    return runtime.useMemo<vector<Repository>>(
        [&repositories, minimumScore]() {
            vector<Repository> result;

            copy_if(
                repositories.begin(),
                repositories.end(),
                back_inserter(result),
                [minimumScore](const Repository& repository) {
                    return repository.score >= minimumScore;
                }
            );

            return result;
        },
        {
            minimumScore,
            static_cast<int>(repositories.size())
        }
    );
}


// ---------------------------------------------------------
// Component model
// ---------------------------------------------------------

struct Dashboard {
    int count;
    int renderNumber;
    optional<int> previousThreshold;
    vector<Repository> visibleRepositories;
    set<int> visibleIds;
};


Dashboard repositoryDashboard(
    HookRuntime& runtime,
    const vector<Repository>& repositories,
    int minimumScore
) {
    auto [count, setCount] = runtime.useState<int>(0);

    auto renderReference = runtime.useRef<int>(0);
    ++renderReference->current;

    auto previousThreshold = usePrevious(
        runtime,
        minimumScore
    );

    auto filtered = useFilteredRepositories(
        runtime,
        repositories,
        minimumScore
    );

    set<int> ids = runtime.useMemo<set<int>>(
        [&filtered]() {
            set<int> result;

            for (const auto& repository : filtered) {
                result.insert(repository.id);
            }

            return result;
        },
        {
            minimumScore,
            static_cast<int>(filtered.size())
        }
    );

    auto isSelected = runtime.useCallback<
        function<bool(int)>
    >(
        [ids](int id) {
            return ids.find(id) != ids.end();
        },
        {
            minimumScore,
            static_cast<int>(ids.size())
        }
    );

    (void)isSelected;
    (void)setCount;

    return {
        count,
        renderReference->current,
        previousThreshold,
        filtered,
        ids
    };
}


// ---------------------------------------------------------
// Tests and execution
// ---------------------------------------------------------

void require(bool condition, const string& message) {
    if (!condition) {
        throw runtime_error("Test failed: " + message);
    }
}


void testReferenceIdentity() {
    HookRuntime runtime("ReferenceTest");

    auto component = [](HookRuntime& rt) {
        return rt.useRef<int>(10);
    };

    auto first = runtime.render(component);
    first->current = 99;

    auto second = runtime.render(component);

    require(first == second, "Reference identity");
    require(second->current == 99, "Reference persistence");
}


void testMemoization() {
    HookRuntime runtime("MemoTest");
    int computations = 0;

    auto component = [&computations](
        HookRuntime& rt,
        int value
    ) {
        return rt.useMemo<int>(
            [&computations, value]() {
                ++computations;
                return value * 10;
            },
            {value}
        );
    };

    require(runtime.render(component, 5) == 50, "First memo");
    require(runtime.render(component, 5) == 50, "Cached memo");
    require(runtime.render(component, 8) == 80, "Changed memo");

    require(computations == 2, "Memo computation count");
}


void testHookOrder() {
    HookRuntime runtime("OrderTest");

    auto component = [](HookRuntime& rt, bool reference) {
        if (reference) {
            return rt.useRef<int>(1)->current;
        }

        return rt.useState<int>(0).first;
    };

    runtime.render(component, true);

    bool detected = false;

    try {
        runtime.render(component, false);
    } catch (const HookError&) {
        detected = true;
    }

    require(detected, "Hook ordering violation detection");
}


void runTests() {
    testReferenceIdentity();
    testMemoization();
    testHookOrder();

    cout << "All C++17 tests passed.\n";
}


int main() {
    try {
        runTests();

        HookRuntime runtime("RepositoryDashboard");

        const auto repositories = sampleRepositories();

        cout << "\nRepository Dashboard\n";

        for (int threshold : {70, 70, 85, 85}) {
            Dashboard dashboard = runtime.render(
                repositoryDashboard,
                repositories,
                threshold
            );

            cout << "\nRender " << dashboard.renderNumber
                 << " | Minimum score: " << threshold
                 << " | Counter: " << dashboard.count
                 << '\n';

            if (dashboard.previousThreshold.has_value()) {
                cout << "Previous threshold: "
                     << *dashboard.previousThreshold << '\n';
            } else {
                cout << "Previous threshold: unavailable\n";
            }

            for (const auto& repository : dashboard.visibleRepositories) {
                cout << "  " << repository.name
                     << " | Score: " << repository.score << '\n';
            }
        }

        const Metrics& metrics = runtime.metrics;

        cout << "\nHook Metrics\n";
        cout << "Renders: " << metrics.renders << '\n';
        cout << "Memo computations: " << metrics.memoComputations << '\n';
        cout << "Memo cache hits: " << metrics.memoHits << '\n';
        cout << "Callback creations: " << metrics.callbackCreations << '\n';
        cout << "Callback cache hits: " << metrics.callbackHits << '\n';
        cout << "State updates: " << metrics.stateUpdates << '\n';

        return 0;

    } catch (const exception& error) {
        cerr << "Execution error: " << error.what() << '\n';
        return 1;
    }
}
