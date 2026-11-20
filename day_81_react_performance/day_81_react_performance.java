import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicLong;
import java.util.function.Function;
import java.util.stream.Collectors;

/*
 * REACT PERFORMANCE ENGINEERING
 *
 * Enterprise-oriented performance model:
 * - Component rendering
 * - Memoization and referential equality
 * - Derived-state caching
 * - Asynchronous feature loading
 * - Concurrent request deduplication
 * - Render scheduling
 * - Performance monitoring
 *
 * Runtime: Java 17
 */

public class ReactPerformance {

    // ========================================================
    // 1. EXCEPTIONS AND DOMAIN TYPES
    // ========================================================

    static class PerformanceException extends RuntimeException {
        PerformanceException(String message) {
            super(message);
        }
    }

    enum ModuleStatus {
        UNLOADED,
        LOADING,
        LOADED,
        FAILED
    }

    enum RenderDecision {
        EXECUTED,
        SKIPPED
    }

    record Product(
        int id,
        String name,
        String category,
        double price
    ) {
        Product {
            if (id <= 0 || name == null || name.isBlank()) {
                throw new IllegalArgumentException(
                    "Invalid product identity."
                );
            }

            if (category == null || category.isBlank() || price < 0) {
                throw new IllegalArgumentException(
                    "Invalid product attributes."
                );
            }
        }
    }

    // ========================================================
    // 2. COMPONENT PROPERTIES
    // ========================================================

    record ComponentProps(
        Map<String, Object> values
    ) {
        ComponentProps {
            Objects.requireNonNull(values, "Properties are required.");

            values = Collections.unmodifiableMap(
                new HashMap<>(values)
            );
        }

        Object get(String key) {
            return values.get(key);
        }

        boolean shallowEquals(ComponentProps other) {
            if (other == null) {
                return false;
            }

            if (!values.keySet().equals(other.values.keySet())) {
                return false;
            }

            for (String key : values.keySet()) {
                if (values.get(key) != other.values.get(key)) {
                    return false;
                }
            }

            return true;
        }
    }

    record RenderOutput(
        String componentName,
        String content,
        RenderDecision decision
    ) {}

    // ========================================================
    // 3. COMPONENT SERVICE
    // ========================================================

    static final class Component {

        private final String name;
        private final boolean memoized;
        private final Function<ComponentProps, String> renderer;

        private ComponentProps previousProps;
        private String previousOutput;

        private long renderCount;
        private long skippedCount;
        private boolean initialized;

        Component(
            String name,
            boolean memoized,
            Function<ComponentProps, String> renderer
        ) {
            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException(
                    "Component name is required."
                );
            }

            this.name = name;
            this.memoized = memoized;
            this.renderer = Objects.requireNonNull(renderer);
        }

        synchronized RenderOutput render(ComponentProps props) {
            Objects.requireNonNull(props);

            if (
                memoized &&
                initialized &&
                props.shallowEquals(previousProps)
            ) {
                skippedCount++;

                return new RenderOutput(
                    name,
                    previousOutput,
                    RenderDecision.SKIPPED
                );
            }

            String output = renderer.apply(props);

            previousProps = props;
            previousOutput = output;
            initialized = true;
            renderCount++;

            return new RenderOutput(
                name,
                output,
                RenderDecision.EXECUTED
            );
        }

        synchronized Map<String, Object> statistics() {
            return Map.of(
                "component", name,
                "renders", renderCount,
                "skipped", skippedCount
            );
        }
    }

    // ========================================================
    // 4. RENDER ENGINE
    // ========================================================

    static final class RenderEngine {

        private final Map<String, Component> components =
            new ConcurrentHashMap<>();

        private final PerformanceMonitor monitor =
            new PerformanceMonitor();

        void register(Component component) {
            Component previous = components.putIfAbsent(
                component.name,
                component
            );

            if (previous != null) {
                throw new PerformanceException(
                    "Duplicate component registration."
                );
            }
        }

        RenderOutput render(
            String name,
            ComponentProps props
        ) {
            Component component = components.get(name);

            if (component == null) {
                throw new PerformanceException(
                    "Unknown component: " + name
                );
            }

            long start = System.nanoTime();

            try {
                return component.render(props);
            } finally {
                monitor.record(
                    "render:" + name,
                    (System.nanoTime() - start) / 1_000_000.0
                );
            }
        }

        List<Map<String, Object>> report() {
            return components.values()
                .stream()
                .map(Component::statistics)
                .sorted(Comparator.comparing(
                    item -> item.get("component").toString()
                ))
                .toList();
        }

        PerformanceMonitor monitor() {
            return monitor;
        }
    }

    // ========================================================
    // 5. PERFORMANCE MONITORING
    // ========================================================

    static final class PerformanceMonitor {

        private final Map<String, List<Double>> measurements =
            new ConcurrentHashMap<>();

        void record(String name, double milliseconds) {
            measurements.computeIfAbsent(
                name,
                ignored -> new CopyOnWriteArrayList<>()
            ).add(milliseconds);
        }

        Map<String, Map<String, Double>> report() {
            Map<String, Map<String, Double>> result =
                new TreeMap<>();

            measurements.forEach((name, values) -> {
                double average = values.stream()
                    .mapToDouble(Double::doubleValue)
                    .average()
                    .orElse(0);

                double maximum = values.stream()
                    .mapToDouble(Double::doubleValue)
                    .max()
                    .orElse(0);

                result.put(
                    name,
                    Map.of(
                        "calls", (double) values.size(),
                        "averageMs", average,
                        "maximumMs", maximum
                    )
                );
            });

            return result;
        }
    }

    // ========================================================
    // 6. DERIVED DATA AND MEMOIZATION
    // ========================================================

    static final class ProductService {

        private final List<Product> products;

        private final Map<String, List<Product>> cache =
            new LinkedHashMap<>(16, 0.75f, true) {
                @Override
                protected boolean removeEldestEntry(
                    Map.Entry<String, List<Product>> eldest
                ) {
                    return size() > 64;
                }
            };

        private long hits;
        private long misses;

        ProductService(List<Product> products) {
            this.products = List.copyOf(products);
        }

        synchronized List<Product> search(
            String query,
            String category
        ) {
            String normalizedQuery = query
                .trim()
                .toLowerCase(Locale.ROOT);

            String key = normalizedQuery + "|" + category;

            if (cache.containsKey(key)) {
                hits++;
                return cache.get(key);
            }

            misses++;

            List<Product> filtered = products.stream()
                .filter(product ->
                    product.name()
                        .toLowerCase(Locale.ROOT)
                        .contains(normalizedQuery)
                )
                .filter(product ->
                    category.equals("all") ||
                    product.category().equals(category)
                )
                .toList();

            cache.put(key, filtered);

            return filtered;
        }

        synchronized Map<String, Object> statistics() {
            long total = hits + misses;

            return Map.of(
                "hits", hits,
                "misses", misses,
                "entries", cache.size(),
                "hitRate", total == 0
                    ? 0.0
                    : (double) hits / total
            );
        }
    }

    // ========================================================
    // 7. ASYNCHRONOUS LAZY MODULE LOADING
    // ========================================================

    static final class LazyModule {

        private final String name;
        private final SupplierWithFailure<Map<String, Object>> loader;

        private ModuleStatus status = ModuleStatus.UNLOADED;
        private CompletableFuture<Map<String, Object>> future;
        private Map<String, Object> exports;
        private String error;
        private long loadCount;

        LazyModule(
            String name,
            SupplierWithFailure<Map<String, Object>> loader
        ) {
            this.name = Objects.requireNonNull(name);
            this.loader = Objects.requireNonNull(loader);
        }

        synchronized CompletableFuture<Map<String, Object>> load(
            Executor executor
        ) {
            if (status == ModuleStatus.LOADED) {
                return CompletableFuture.completedFuture(exports);
            }

            if (status == ModuleStatus.LOADING) {
                return future;
            }

            if (status == ModuleStatus.FAILED) {
                throw new PerformanceException(
                    "Module requires an explicit retry: " + error
                );
            }

            status = ModuleStatus.LOADING;
            loadCount++;

            future = CompletableFuture.supplyAsync(() -> {
                try {
                    Map<String, Object> loaded = loader.get();

                    if (loaded == null) {
                        throw new PerformanceException(
                            "Module returned null exports."
                        );
                    }

                    return Map.copyOf(loaded);

                } catch (Exception exception) {
                    throw new CompletionException(exception);
                }
            }, executor);

            future.whenComplete((result, failure) -> {
                synchronized (LazyModule.this) {
                    if (failure == null) {
                        exports = result;
                        status = ModuleStatus.LOADED;
                    } else {
                        error = failure.getMessage();
                        status = ModuleStatus.FAILED;
                    }
                }
            });

            return future;
        }

        synchronized void retry() {
            if (status != ModuleStatus.FAILED) {
                throw new PerformanceException(
                    "Only failed modules can be retried."
                );
            }

            status = ModuleStatus.UNLOADED;
            error = null;
            future = null;
        }

        synchronized Map<String, Object> statistics() {
            return Map.of(
                "module", name,
                "status", status.toString(),
                "loads", loadCount,
                "error", error == null ? "" : error
            );
        }
    }

    @FunctionalInterface
    interface SupplierWithFailure<T> {
        T get() throws Exception;
    }

    static final class ModuleRegistry {

        private final Map<String, LazyModule> modules =
            new ConcurrentHashMap<>();

        private final Executor executor;

        ModuleRegistry(Executor executor) {
            this.executor = executor;
        }

        void register(LazyModule module) {
            if (modules.putIfAbsent(module.name, module) != null) {
                throw new PerformanceException(
                    "Duplicate module."
                );
            }
        }

        CompletableFuture<Map<String, Object>> load(String name) {
            LazyModule module = modules.get(name);

            if (module == null) {
                throw new PerformanceException(
                    "Unknown module: " + name
                );
            }

            return module.load(executor);
        }

        List<Map<String, Object>> report() {
            return modules.values()
                .stream()
                .map(LazyModule::statistics)
                .toList();
        }
    }

    // ========================================================
    // 8. RENDER SCHEDULING
    // ========================================================

    static final class RenderScheduler {

        private final RenderEngine engine;

        private final Map<String, ComponentProps> pending =
            new LinkedHashMap<>();

        RenderScheduler(RenderEngine engine) {
            this.engine = engine;
        }

        synchronized void schedule(
            String component,
            ComponentProps props
        ) {
            // Latest props replace earlier pending props.
            pending.put(component, props);
        }

        synchronized List<RenderOutput> flush() {
            List<RenderOutput> results = new ArrayList<>();

            for (Map.Entry<String, ComponentProps> entry :
                pending.entrySet()) {

                results.add(
                    engine.render(entry.getKey(), entry.getValue())
                );
            }

            pending.clear();

            return results;
        }
    }

    // ========================================================
    // 9. APPLICATION EXECUTION
    // ========================================================

    public static void main(String[] args) {

        ExecutorService executor =
            Executors.newFixedThreadPool(2);

        try {
            System.out.println(
                "\nREACT PERFORMANCE ENGINEERING"
            );

            List<Product> products = List.of(
                new Product(1, "Laptop", "electronics", 75000),
                new Product(2, "Keyboard", "electronics", 2500),
                new Product(3, "Office Chair", "furniture", 12000),
                new Product(4, "Monitor", "electronics", 18000),
                new Product(5, "Desk", "furniture", 15000)
            );

            ProductService productService =
                new ProductService(products);

            RenderEngine engine = new RenderEngine();

            engine.register(
                new Component(
                    "ProductList",
                    true,
                    props -> {
                        List<?> items =
                            (List<?>) props.get("products");

                        return "Product count: " + items.size();
                    }
                )
            );

            engine.register(
                new Component(
                    "ProductSummary",
                    true,
                    props ->
                        "Category: " + props.get("category")
                )
            );

            RenderScheduler scheduler =
                new RenderScheduler(engine);

            List<Product> initial =
                productService.search("", "all");

            ComponentProps initialList =
                new ComponentProps(Map.of(
                    "products", initial
                ));

            ComponentProps initialSummary =
                new ComponentProps(Map.of(
                    "category", "all"
                ));

            scheduler.schedule("ProductList", initialList);
            scheduler.schedule("ProductSummary", initialSummary);

            scheduler.flush();

            // Identical property references allow a render skip.
            RenderOutput unchanged =
                engine.render("ProductList", initialList);

            if (unchanged.decision() != RenderDecision.SKIPPED) {
                throw new PerformanceException(
                    "Expected memoized rendering."
                );
            }

            List<Product> filtered =
                productService.search("monitor", "electronics");

            scheduler.schedule(
                "ProductList",
                new ComponentProps(Map.of("products", filtered))
            );

            scheduler.schedule(
                "ProductSummary",
                new ComponentProps(Map.of("category", "electronics"))
            );

            scheduler.flush();

            // Lazy features are not loaded during initial rendering.
            ModuleRegistry registry =
                new ModuleRegistry(executor);

            registry.register(
                new LazyModule(
                    "analytics",
                    () -> Map.of(
                        "feature", "analytics",
                        "charts", List.of(
                            "revenue",
                            "orders",
                            "conversion"
                        )
                    )
                )
            );

            registry.register(
                new LazyModule(
                    "administration",
                    () -> Map.of(
                        "feature", "administration",
                        "permissions", List.of("read", "write")
                    )
                )
            );

            System.out.println("\nModules before navigation:");
            System.out.println(registry.report());

            CompletableFuture<Map<String, Object>> first =
                registry.load("analytics");

            CompletableFuture<Map<String, Object>> second =
                registry.load("analytics");

            CompletableFuture.allOf(first, second).join();

            if (first.get() != second.get()) {
                throw new PerformanceException(
                    "Concurrent module loading was not deduplicated."
                );
            }

            System.out.println("\nLoaded analytics:");
            System.out.println(first.join());

            System.out.println("\nComponent statistics:");
            System.out.println(engine.report());

            System.out.println("\nPerformance metrics:");
            System.out.println(engine.monitor().report());

            System.out.println("\nMemoization statistics:");
            System.out.println(productService.statistics());

            System.out.println("\nModule statistics:");
            System.out.println(registry.report());

            if (filtered.size() != 1) {
                throw new PerformanceException(
                    "Product filtering failed."
                );
            }

            System.out.println("\nAll performance checks passed.");

        } catch (Exception exception) {
            System.err.println(
                "Application failure: " + exception.getMessage()
            );

            System.exitCode = 1;
        } finally {
            executor.shutdown();

            try {
                if (!executor.awaitTermination(5, TimeUnit.SECONDS)) {
                    executor.shutdownNow();
                }
            } catch (InterruptedException exception) {
                executor.shutdownNow();
                Thread.currentThread().interrupt();
            }
        }
    }
}
