#include <algorithm>
#include <chrono>
#include <cmath>
#include <functional>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <set>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

using namespace std;

// ============================================================
// REACT PERFORMANCE AND REPOSITORY-SCALE UI GOVERNANCE
// Component rendering, memoization, and lazy loading
// ============================================================

class PerformanceError : public runtime_error {
public:
    explicit PerformanceError(const string& message)
        : runtime_error(message) {}
};

enum class ModuleStatus {
    Unloaded,
    Loading,
    Loaded,
    Failed
};

string statusName(ModuleStatus status) {
    switch (status) {
        case ModuleStatus::Unloaded: return "UNLOADED";
        case ModuleStatus::Loading: return "LOADING";
        case ModuleStatus::Loaded: return "LOADED";
        case ModuleStatus::Failed: return "FAILED";
    }

    return "UNKNOWN";
}

// ============================================================
// 1. COMPONENT DOMAIN MODEL
// ============================================================

struct Props {
    map<string, string> values;

    bool operator==(const Props& other) const {
        return values == other.values;
    }
};

struct RenderResult {
    string component;
    string output;
    bool skipped;
};

class Component {
private:
    string name;
    bool memoized;
    bool initialized = false;

    optional<Props> previousProps;
    string previousOutput;

    size_t renderCount = 0;
    size_t skippedCount = 0;

    function<string(const Props&)> renderFunction;

public:
    Component(
        string componentName,
        bool enableMemoization,
        function<string(const Props&)> renderer
    )
        : name(move(componentName)),
          memoized(enableMemoization),
          renderFunction(move(renderer)) {

        if (name.empty() || !renderFunction) {
            throw PerformanceError("Invalid component definition.");
        }
    }

    RenderResult render(const Props& props) {
        if (
            memoized &&
            initialized &&
            previousProps.has_value() &&
            previousProps.value() == props
        ) {
            skippedCount++;

            return {
                name,
                previousOutput,
                true
            };
        }

        string output = renderFunction(props);

        previousProps = props;
        previousOutput = output;
        initialized = true;
        renderCount++;

        return {
            name,
            output,
            false
        };
    }

    void report() const {
        cout << left << setw(20) << name
             << " renders=" << renderCount
             << " skipped=" << skippedCount << '\n';
    }

    size_t getRenderCount() const {
        return renderCount;
    }

    size_t getSkippedCount() const {
        return skippedCount;
    }
};

// ============================================================
// 2. COMPONENT TREE
// ============================================================

class ComponentTree {
private:
    map<string, Component> components;

public:
    void add(Component component, const string& name) {
        if (components.count(name)) {
            throw PerformanceError("Duplicate component.");
        }

        components.emplace(name, move(component));
    }

    RenderResult render(const string& name, const Props& props) {
        auto it = components.find(name);

        if (it == components.end()) {
            throw PerformanceError("Unknown component: " + name);
        }

        return it->second.render(props);
    }

    void report() const {
        for (const auto& [name, component] : components) {
            component.report();
        }
    }
};

// ============================================================
// 3. MEMOIZATION CACHE
// ============================================================

class MemoCache {
private:
    struct Entry {
        string value;
        size_t lastUsed;
    };

    unordered_map<string, Entry> entries;
    size_t capacity;
    size_t clock = 0;

    size_t hits = 0;
    size_t misses = 0;

public:
    explicit MemoCache(size_t maximumEntries = 128)
        : capacity(maximumEntries) {

        if (capacity == 0) {
            throw PerformanceError("Cache capacity cannot be zero.");
        }
    }

    string compute(
        const string& key,
        const function<string()>& calculation
    ) {
        auto it = entries.find(key);

        if (it != entries.end()) {
            hits++;
            it->second.lastUsed = ++clock;
            return it->second.value;
        }

        misses++;

        string value = calculation();

        if (entries.size() >= capacity) {
            auto oldest = min_element(
                entries.begin(),
                entries.end(),
                [](const auto& first, const auto& second) {
                    return first.second.lastUsed <
                           second.second.lastUsed;
                }
            );

            entries.erase(oldest);
        }

        entries.emplace(
            key,
            Entry{value, ++clock}
        );

        return value;
    }

    void report() const {
        cout << "Cache hits: " << hits << '\n';
        cout << "Cache misses: " << misses << '\n';
        cout << "Cache entries: " << entries.size() << '\n';

        size_t total = hits + misses;

        double hitRate = total
            ? static_cast<double>(hits) / total
            : 0.0;

        cout << "Hit rate: "
             << fixed << setprecision(2)
             << hitRate * 100 << "%\n";
    }
};

// ============================================================
// 4. APPLICATION DATA AND FILTERING
// ============================================================

struct Product {
    int id;
    string name;
    string category;
    double price;
};

class ProductCatalog {
private:
    vector<Product> products;

public:
    explicit ProductCatalog(vector<Product> data)
        : products(move(data)) {}

    vector<Product> filter(
        const string& query,
        const string& category
    ) const {
        vector<Product> result;

        for (const Product& product : products) {
            bool nameMatches =
                product.name.find(query) != string::npos;

            bool categoryMatches =
                category == "all" ||
                product.category == category;

            if (nameMatches && categoryMatches) {
                result.push_back(product);
            }
        }

        return result;
    }

    size_t size() const {
        return products.size();
    }
};

// ============================================================
// 5. LAZY MODULE REGISTRY
// ============================================================

struct LazyModule {
    string name;
    ModuleStatus status = ModuleStatus::Unloaded;
    string content;
    size_t loadCount = 0;
    string failureReason;
};

class ModuleRegistry {
private:
    map<string, LazyModule> modules;

public:
    void registerModule(const string& name) {
        if (name.empty() || modules.count(name)) {
            throw PerformanceError("Invalid or duplicate module.");
        }

        modules.emplace(
            name,
            LazyModule{name}
        );
    }

    string load(const string& name) {
        auto it = modules.find(name);

        if (it == modules.end()) {
            throw PerformanceError("Unknown module: " + name);
        }

        LazyModule& module = it->second;

        if (module.status == ModuleStatus::Loaded) {
            return module.content;
        }

        if (module.status == ModuleStatus::Loading) {
            throw PerformanceError("Recursive module loading.");
        }

        if (module.status == ModuleStatus::Failed) {
            throw PerformanceError(
                "Module failed: " + module.failureReason
            );
        }

        module.status = ModuleStatus::Loading;
        module.loadCount++;

        try {
            // The registry simulates an independently loaded feature.
            // A browser bundler performs the actual network chunk request.
            if (name == "analytics") {
                module.content =
                    "Analytics dashboard: revenue, orders, conversion";
            } else if (name == "administration") {
                module.content =
                    "Administration dashboard: roles and permissions";
            } else {
                throw PerformanceError("No module implementation.");
            }

            module.status = ModuleStatus::Loaded;

            return module.content;
        } catch (const exception& error) {
            module.status = ModuleStatus::Failed;
            module.failureReason = error.what();
            throw;
        }
    }

    void retry(const string& name) {
        auto it = modules.find(name);

        if (it == modules.end()) {
            throw PerformanceError("Unknown module.");
        }

        if (it->second.status != ModuleStatus::Failed) {
            throw PerformanceError("Module is not in failed state.");
        }

        it->second.status = ModuleStatus::Unloaded;
        it->second.failureReason.clear();
    }

    void report() const {
        for (const auto& [name, module] : modules) {
            cout << name
                 << " | " << statusName(module.status)
                 << " | loads=" << module.loadCount << '\n';
        }
    }
};

// ============================================================
// 6. PERFORMANCE ANALYZER
// ============================================================

class PerformanceAnalyzer {
private:
    using Clock = chrono::steady_clock;

public:
    template<typename Function>
    static double measure(Function operation) {
        auto start = Clock::now();

        operation();

        auto end = Clock::now();

        return chrono::duration<double, milli>(
            end - start
        ).count();
    }
};

// ============================================================
// 7. MAIN APPLICATION
// ============================================================

int main() {
    try {
        cout << "\nREACT PERFORMANCE ENGINEERING\n";
        cout << string(55, '=') << "\n\n";

        vector<Product> products = {
            {1, "Laptop", "electronics", 75000},
            {2, "Keyboard", "electronics", 2500},
            {3, "Office Chair", "furniture", 12000},
            {4, "Monitor", "electronics", 18000},
            {5, "Desk", "furniture", 15000}
        };

        ProductCatalog catalog(products);

        ComponentTree tree;

        tree.add(
            Component(
                "ProductList",
                true,
                [](const Props& props) {
                    return "Product list with " +
                        props.values.at("count") +
                        " items";
                }
            ),
            "ProductList"
        );

        tree.add(
            Component(
                "ProductSummary",
                true,
                [](const Props& props) {
                    return "Category: " +
                        props.values.at("category");
                }
            ),
            "ProductSummary"
        );

        MemoCache cache(32);

        auto initial = catalog.filter("", "all");

        Props listProps{
            {{"count", to_string(initial.size())}}
        };

        Props summaryProps{
            {{"category", "all"}}
        };

        tree.render("ProductList", listProps);
        tree.render("ProductSummary", summaryProps);

        // Unchanged props permit memoized rendering.
        tree.render("ProductList", listProps);

        cout << "Initial product count: "
             << catalog.size() << '\n';

        cout << "\nFiltered products:\n";

        auto filtered = catalog.filter("Monitor", "electronics");

        for (const auto& product : filtered) {
            cout << product.id << " | "
                 << product.name << " | "
                 << product.price << '\n';
        }

        // Expensive derived data is cached by a stable key.
        string first = cache.compute(
            "electronics-count",
            [&]() {
                return to_string(
                    catalog.filter("", "electronics").size()
                );
            }
        );

        string second = cache.compute(
            "electronics-count",
            [&]() {
                return "unexpected";
            }
        );

        if (first != second) {
            throw PerformanceError("Memoization failed.");
        }

        cout << "\nCached electronics count: " << first << '\n';

        ModuleRegistry registry;

        registry.registerModule("analytics");
        registry.registerModule("administration");

        cout << "\nModules before navigation:\n";
        registry.report();

        string analytics = registry.load("analytics");

        cout << "\nLoaded feature:\n";
        cout << analytics << '\n';

        // Loading the same module again reuses its cached exports.
        registry.load("analytics");

        cout << "\nModule states after navigation:\n";
        registry.report();

        cout << "\nComponent statistics:\n";
        tree.report();

        cout << "\nMemoization statistics:\n";
        cache.report();

        double elapsed = PerformanceAnalyzer::measure([&]() {
            volatile size_t count =
                catalog.filter("", "all").size();
            (void)count;
        });

        cout << "\nFiltering execution time: "
             << fixed << setprecision(4)
             << elapsed << " ms\n";

        if (filtered.size() != 1) {
            throw PerformanceError("Unexpected filtering result.");
        }

        cout << "\nAll performance checks passed.\n";

    } catch (const exception& error) {
        cerr << "Execution error: "
             << error.what() << '\n';

        return 1;
    }

    return 0;
}
