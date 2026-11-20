"use strict";

/*
 * REACT PERFORMANCE ENGINEERING
 * Memoization, Rendering, Code Splitting, and Lazy Loading
 *
 * Runtime: Node.js 18+
 *
 * This implementation emphasizes:
 * - Event-driven state updates
 * - Component render scheduling
 * - Referential equality
 * - Bounded memoization
 * - Asynchronous lazy module loading
 * - Concurrent load deduplication
 * - Performance instrumentation
 */

const { performance } = require("node:perf_hooks");
const EventEmitter = require("node:events");

// ============================================================
// 1. VALIDATION AND COMPARISON
// ============================================================

class PerformanceError extends Error {}
class ValidationError extends PerformanceError {}

function validateObject(value, label) {
    if (
        value === null ||
        typeof value !== "object" ||
        Array.isArray(value)
    ) {
        throw new ValidationError(`${label} must be an object.`);
    }
}

function shallowEqual(first, second) {
    if (Object.is(first, second)) return true;

    if (
        first === null ||
        second === null ||
        typeof first !== "object" ||
        typeof second !== "object"
    ) {
        return false;
    }

    const firstKeys = Object.keys(first);
    const secondKeys = Object.keys(second);

    if (firstKeys.length !== secondKeys.length) return false;

    return firstKeys.every(
        key =>
            Object.hasOwn(second, key) &&
            Object.is(first[key], second[key])
    );
}

// ============================================================
// 2. PERFORMANCE METRICS
// ============================================================

class PerformanceTracker {
    constructor() {
        this.records = new Map();
    }

    measure(name, callback) {
        const start = performance.now();

        try {
            return callback();
        } finally {
            this.record(name, performance.now() - start);
        }
    }

    record(name, duration) {
        if (!this.records.has(name)) {
            this.records.set(name, []);
        }

        this.records.get(name).push(duration);
    }

    report() {
        return Object.fromEntries(
            [...this.records.entries()].map(([name, values]) => {
                const total = values.reduce((a, b) => a + b, 0);

                return [
                    name,
                    {
                        calls: values.length,
                        averageMs: Number(
                            (total / values.length).toFixed(4)
                        ),
                        maximumMs: Number(
                            Math.max(...values).toFixed(4)
                        )
                    }
                ];
            })
        );
    }
}

// ============================================================
// 3. COMPONENT RENDER ENGINE
// ============================================================

class Component {
    constructor(name, renderFunction, options = {}) {
        if (typeof name !== "string" || !name.trim()) {
            throw new ValidationError("Invalid component name.");
        }

        if (typeof renderFunction !== "function") {
            throw new ValidationError("Render function is required.");
        }

        this.name = name;
        this.renderFunction = renderFunction;
        this.memoized = options.memoized ?? false;
        this.previousProps = null;
        this.previousOutput = undefined;
        this.initialized = false;
        this.renderCount = 0;
        this.skippedCount = 0;
    }

    render(props) {
        validateObject(props, "Component props");

        if (
            this.memoized &&
            this.initialized &&
            shallowEqual(this.previousProps, props)
        ) {
            this.skippedCount++;
            return this.previousOutput;
        }

        const output = this.renderFunction(props);

        this.renderCount++;
        this.previousProps = { ...props };
        this.previousOutput = output;
        this.initialized = true;

        return output;
    }

    statistics() {
        return {
            component: this.name,
            renders: this.renderCount,
            skipped: this.skippedCount
        };
    }
}

class RenderEngine {
    constructor() {
        this.components = new Map();
        this.tracker = new PerformanceTracker();
    }

    register(component) {
        if (this.components.has(component.name)) {
            throw new ValidationError("Duplicate component.");
        }

        this.components.set(component.name, component);
    }

    render(name, props) {
        const component = this.components.get(name);

        if (!component) {
            throw new PerformanceError(`Unknown component: ${name}`);
        }

        return this.tracker.measure(
            `render:${name}`,
            () => component.render(props)
        );
    }

    report() {
        return [...this.components.values()].map(
            component => component.statistics()
        );
    }
}

// ============================================================
// 4. BOUNDED MEMOIZATION
// ============================================================

class LRUCache {
    constructor(capacity = 128) {
        if (!Number.isInteger(capacity) || capacity < 1) {
            throw new ValidationError("Invalid cache capacity.");
        }

        this.capacity = capacity;
        this.cache = new Map();
        this.hits = 0;
        this.misses = 0;
    }

    get(key, calculate) {
        if (this.cache.has(key)) {
            this.hits++;

            const value = this.cache.get(key);

            // Map insertion order provides LRU ordering.
            this.cache.delete(key);
            this.cache.set(key, value);

            return value;
        }

        this.misses++;

        const value = calculate();

        if (this.cache.size >= this.capacity) {
            const oldest = this.cache.keys().next().value;
            this.cache.delete(oldest);
        }

        this.cache.set(key, value);

        return value;
    }

    clear() {
        this.cache.clear();
    }

    statistics() {
        const total = this.hits + this.misses;

        return {
            hits: this.hits,
            misses: this.misses,
            entries: this.cache.size,
            hitRate: total ? this.hits / total : 0
        };
    }
}

// ============================================================
// 5. DERIVED APPLICATION DATA
// ============================================================

class ProductCatalog {
    constructor(products) {
        this.products = products;
        this.cache = new LRUCache(64);
    }

    search(query, category) {
        const key = JSON.stringify([
            query.trim().toLowerCase(),
            category
        ]);

        return this.cache.get(key, () => {
            const normalizedQuery = query.toLowerCase();

            return this.products.filter(product => {
                return (
                    product.name.toLowerCase().includes(normalizedQuery) &&
                    (
                        category === "all" ||
                        product.category === category
                    )
                );
            });
        });
    }
}

// ============================================================
// 6. EVENT-DRIVEN APPLICATION STATE
// ============================================================

class ApplicationStore extends EventEmitter {
    constructor() {
        super();

        this.state = Object.freeze({
            query: "",
            category: "all",
            revision: 0
        });
    }

    getState() {
        return this.state;
    }

    update(patch) {
        validateObject(patch, "State patch");

        const allowed = new Set(["query", "category"]);

        for (const key of Object.keys(patch)) {
            if (!allowed.has(key)) {
                throw new ValidationError(`Unsupported state key: ${key}`);
            }
        }

        const next = { ...this.state, ...patch };

        if (typeof next.query !== "string") {
            throw new ValidationError("Query must be text.");
        }

        if (
            typeof next.category !== "string" ||
            !next.category.trim()
        ) {
            throw new ValidationError("Invalid category.");
        }

        next.revision++;

        this.state = Object.freeze(next);

        this.emit("change", this.state);
    }
}

// ============================================================
// 7. ASYNCHRONOUS LAZY LOADING
// ============================================================

const ModuleStatus = Object.freeze({
    UNLOADED: "unloaded",
    LOADING: "loading",
    LOADED: "loaded",
    FAILED: "failed"
});

class LazyModuleRegistry {
    constructor() {
        this.modules = new Map();
    }

    register(name, loader) {
        if (this.modules.has(name)) {
            throw new ValidationError(`Duplicate module: ${name}`);
        }

        if (typeof loader !== "function") {
            throw new ValidationError("Loader must be a function.");
        }

        this.modules.set(name, {
            name,
            loader,
            status: ModuleStatus.UNLOADED,
            promise: null,
            exports: null,
            error: null,
            loadCount: 0
        });
    }

    async load(name) {
        const module = this.modules.get(name);

        if (!module) {
            throw new PerformanceError(`Unknown module: ${name}`);
        }

        if (module.status === ModuleStatus.LOADED) {
            return module.exports;
        }

        // Concurrent navigation requests share the same Promise.
        if (module.status === ModuleStatus.LOADING) {
            return module.promise;
        }

        module.status = ModuleStatus.LOADING;
        module.loadCount++;

        module.promise = Promise.resolve()
            .then(() => module.loader())
            .then(exports => {
                if (exports === null || exports === undefined) {
                    throw new PerformanceError(
                        "Module returned empty exports."
                    );
                }

                module.exports = exports;
                module.status = ModuleStatus.LOADED;

                return exports;
            })
            .catch(error => {
                module.error = error.message;
                module.status = ModuleStatus.FAILED;
                module.promise = null;

                throw error;
            });

        return module.promise;
    }

    retry(name) {
        const module = this.modules.get(name);

        if (!module) {
            throw new PerformanceError(`Unknown module: ${name}`);
        }

        if (module.status !== ModuleStatus.FAILED) {
            throw new PerformanceError(
                "Only failed modules can be retried."
            );
        }

        module.status = ModuleStatus.UNLOADED;
        module.error = null;

        return this.load(name);
    }

    report() {
        return [...this.modules.values()].map(module => ({
            name: module.name,
            status: module.status,
            loadCount: module.loadCount,
            error: module.error
        }));
    }
}

// ============================================================
// 8. RENDER SCHEDULING
// ============================================================

class RenderScheduler {
    constructor(engine) {
        this.engine = engine;
        this.pending = new Map();
        this.scheduled = false;
    }

    schedule(componentName, props) {
        // Multiple updates for one component retain the latest props.
        this.pending.set(componentName, props);

        if (!this.scheduled) {
            this.scheduled = true;

            queueMicrotask(() => {
                this.flush();
            });
        }
    }

    flush() {
        this.scheduled = false;

        const work = [...this.pending.entries()];
        this.pending.clear();

        for (const [name, props] of work) {
            this.engine.render(name, props);
        }
    }
}

// ============================================================
// 9. APPLICATION EXECUTION
// ============================================================

async function main() {
    console.log("\nREACT PERFORMANCE ENGINEERING");
    console.log("=".repeat(55));

    const products = [
        { id: 1, name: "Laptop", category: "electronics", price: 75000 },
        { id: 2, name: "Keyboard", category: "electronics", price: 2500 },
        { id: 3, name: "Office Chair", category: "furniture", price: 12000 },
        { id: 4, name: "Monitor", category: "electronics", price: 18000 },
        { id: 5, name: "Desk", category: "furniture", price: 15000 }
    ];

    const catalog = new ProductCatalog(products);
    const store = new ApplicationStore();
    const engine = new RenderEngine();
    const scheduler = new RenderScheduler(engine);

    engine.register(
        new Component(
            "ProductList",
            props => ({
                count: props.products.length,
                products: props.products
            }),
            { memoized: true }
        )
    );

    engine.register(
        new Component(
            "ProductSummary",
            props => ({
                count: props.products.length,
                category: props.category
            }),
            { memoized: true }
        )
    );

    // Store changes trigger derived data and render scheduling.
    store.on("change", state => {
        const filtered = catalog.search(
            state.query,
            state.category
        );

        scheduler.schedule("ProductList", {
            products: filtered
        });

        scheduler.schedule("ProductSummary", {
            products: filtered,
            category: state.category
        });
    });

    const initial = catalog.search("", "all");

    scheduler.schedule("ProductList", { products: initial });
    scheduler.schedule("ProductSummary", {
        products: initial,
        category: "all"
    });

    scheduler.flush();

    // A repeated render with identical references can be skipped.
    engine.render("ProductList", { products: initial });

    store.update({ query: "monitor" });

    // Allow event-driven updates to complete.
    await new Promise(resolve => queueMicrotask(resolve));

    // Lazy-loaded features are registered separately from initial UI.
    const modules = new LazyModuleRegistry();

    modules.register("analytics", async () => ({
        name: "Analytics",
        charts: ["revenue", "orders", "conversion"]
    }));

    modules.register("administration", async () => ({
        name: "Administration",
        permissions: ["read", "write"]
    }));

    console.log("\nBefore feature navigation:");
    console.log(JSON.stringify(modules.report(), null, 2));

    // Both requests share a single loading operation.
    const [first, second] = await Promise.all([
        modules.load("analytics"),
        modules.load("analytics")
    ]);

    if (first !== second) {
        throw new PerformanceError("Module cache consistency failed.");
    }

    console.log("\nLoaded analytics module:");
    console.log(first);

    console.log("\nComponent statistics:");
    console.log(JSON.stringify(engine.report(), null, 2));

    console.log("\nRendering performance:");
    console.log(JSON.stringify(engine.tracker.report(), null, 2));

    console.log("\nMemoization statistics:");
    console.log(JSON.stringify(catalog.cache.statistics(), null, 2));

    console.log("\nLazy module states:");
    console.log(JSON.stringify(modules.report(), null, 2));

    // Validation of expected behavior.
    if (modules.modules.get("analytics").loadCount !== 1) {
        throw new PerformanceError("Concurrent load was not deduplicated.");
    }

    if (engine.components.get("ProductList").skippedCount !== 1) {
        throw new PerformanceError("Memoization check failed.");
    }

    console.log("\nAll performance checks passed.");
}

main().catch(error => {
    console.error("Application failure:", error.message);
    process.exitCode = 1;
});
