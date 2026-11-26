import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionException;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;
import java.util.stream.Collectors;

/*
 * Next.js Data Architecture
 *
 * Enterprise model for server-side fetching, caching,
 * revalidation, dynamic rendering and route-level data policies.
 *
 * Java 17, no third-party dependencies.
 */

public class NextDataArchitecture {

    enum FetchPolicy {
        CACHED,
        NO_STORE
    }

    enum RenderMode {
        STATIC,
        DYNAMIC,
        PARTIAL
    }

    enum CacheStatus {
        HIT,
        MISS,
        STALE
    }

    enum RevalidationMode {
        TAG,
        PATH
    }

    static class ArchitectureException extends RuntimeException {
        ArchitectureException(String message) {
            super(message);
        }
    }

    static class NotFoundException extends ArchitectureException {
        NotFoundException(String message) {
            super(message);
        }
    }

    record Product(
        int id,
        String name,
        double price,
        String category,
        int stock,
        int version
    ) {
        Product {
            if (id <= 0) {
                throw new IllegalArgumentException(
                    "Product ID must be positive."
                );
            }

            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException(
                    "Product name is required."
                );
            }

            if (!Double.isFinite(price) || price < 0) {
                throw new IllegalArgumentException(
                    "Invalid product price."
                );
            }

            if (stock < 0 || version <= 0) {
                throw new IllegalArgumentException(
                    "Invalid stock or version."
                );
            }
        }
    }

    record CacheStatistics(
        long hits,
        long misses,
        long staleHits,
        long writes,
        long invalidations,
        int entries
    ) {
        double hitRatio() {
            long total = hits + misses + staleHits;

            return total == 0
                ? 0.0
                : (double) (hits + staleHits) / total;
        }
    }

    record RequestContext(
        Optional<String> userId,
        boolean readsCookies,
        boolean readsHeaders,
        boolean usesUncachedData
    ) {
        RequestContext {
            userId = Objects.requireNonNull(userId);
        }

        boolean isPersonalized() {
            return userId.isPresent();
        }
    }

    record CachePolicy(
        Duration ttl,
        Set<String> tags,
        Set<String> paths
    ) {
        CachePolicy {
            Objects.requireNonNull(ttl);
            tags = Set.copyOf(tags);
            paths = Set.copyOf(paths);

            if (ttl.isZero() || ttl.isNegative()) {
                throw new IllegalArgumentException(
                    "Cache TTL must be positive."
                );
            }

            if (tags.stream().anyMatch(String::isBlank)) {
                throw new IllegalArgumentException(
                    "Cache tags cannot be empty."
                );
            }

            if (paths.stream().anyMatch(
                path -> !path.startsWith("/")
            )) {
                throw new IllegalArgumentException(
                    "Cache paths must be absolute."
                );
            }
        }
    }

    static final class CacheEntry<T> {
        final T value;
        final Instant createdAt;
        final Instant expiresAt;
        final Set<String> tags;
        final Set<String> paths;
        final long version;

        CacheEntry(
            T value,
            CachePolicy policy,
            long version
        ) {
            this.value = value;
            this.createdAt = Instant.now();
            this.expiresAt = createdAt.plus(policy.ttl());
            this.tags = policy.tags();
            this.paths = policy.paths();
            this.version = version;
        }

        boolean isExpired() {
            return !Instant.now().isBefore(expiresAt);
        }
    }

    static final class Repository {
        private final Map<Integer, Product> products =
            new ConcurrentHashMap<>();

        Repository() {
            insert(new Product(
                101, "Laptop", 75000, "Electronics", 12, 1
            ));

            insert(new Product(
                102, "Keyboard", 2500, "Accessories", 45, 1
            ));

            insert(new Product(
                103, "Monitor", 18000, "Electronics", 8, 1
            ));
        }

        private void insert(Product product) {
            products.put(product.id(), product);
        }

        Product findById(int id) {
            if (id <= 0) {
                throw new IllegalArgumentException(
                    "Invalid product ID."
                );
            }

            Product product = products.get(id);

            if (product == null) {
                throw new NotFoundException(
                    "Product " + id + " does not exist."
                );
            }

            return product;
        }

        List<Product> findAll() {
            return products.values()
                .stream()
                .sorted((a, b) -> Integer.compare(a.id(), b.id()))
                .toList();
        }

        synchronized Product update(
            int id,
            Optional<Double> price,
            Optional<Integer> stock
        ) {
            Product existing = findById(id);

            double newPrice = price.orElse(existing.price());
            int newStock = stock.orElse(existing.stock());

            Product updated = new Product(
                id,
                existing.name(),
                newPrice,
                existing.category(),
                newStock,
                existing.version() + 1
            );

            products.put(id, updated);

            return updated;
        }
    }

    static final class CacheManager {
        private final Map<String, CacheEntry<?>> entries =
            new ConcurrentHashMap<>();

        private final Map<String, Set<String>> tagIndex =
            new ConcurrentHashMap<>();

        private final Map<String, Set<String>> pathIndex =
            new ConcurrentHashMap<>();

        private final AtomicLong sequence = new AtomicLong();

        private final AtomicLong hits = new AtomicLong();
        private final AtomicLong misses = new AtomicLong();
        private final AtomicLong staleHits = new AtomicLong();
        private final AtomicLong writes = new AtomicLong();
        private final AtomicLong invalidations = new AtomicLong();

        private void addIndex(
            Map<String, Set<String>> index,
            String identifier,
            String key
        ) {
            index.computeIfAbsent(
                identifier,
                ignored -> ConcurrentHashMap.newKeySet()
            ).add(key);
        }

        private void removeEntry(String key) {
            CacheEntry<?> entry = entries.remove(key);

            if (entry == null) return;

            for (String tag : entry.tags) {
                removeIndex(tagIndex, tag, key);
            }

            for (String path : entry.paths) {
                removeIndex(pathIndex, path, key);
            }
        }

        private void removeIndex(
            Map<String, Set<String>> index,
            String identifier,
            String key
        ) {
            Set<String> keys = index.get(identifier);

            if (keys == null) return;

            keys.remove(key);

            if (keys.isEmpty()) {
                index.remove(identifier, keys);
            }
        }

        @SuppressWarnings("unchecked")
        synchronized <T> Optional<T> get(String key) {
            CacheEntry<?> entry = entries.get(key);

            if (entry == null) {
                misses.incrementAndGet();
                return Optional.empty();
            }

            if (entry.isExpired()) {
                staleHits.incrementAndGet();
                return Optional.empty();
            }

            hits.incrementAndGet();

            return Optional.of((T) entry.value);
        }

        synchronized <T> void put(
            String key,
            T value,
            CachePolicy policy
        ) {
            Objects.requireNonNull(value);

            removeEntry(key);

            CacheEntry<T> entry = new CacheEntry<>(
                value,
                policy,
                sequence.incrementAndGet()
            );

            entries.put(key, entry);

            for (String tag : entry.tags) {
                addIndex(tagIndex, tag, key);
            }

            for (String path : entry.paths) {
                addIndex(pathIndex, path, key);
            }

            writes.incrementAndGet();
        }

        synchronized int invalidate(
            RevalidationMode mode,
            String identifier
        ) {
            Map<String, Set<String>> index =
                mode == RevalidationMode.TAG
                ? tagIndex
                : pathIndex;

            Set<String> indexed = index.get(identifier);

            if (indexed == null) return 0;

            List<String> keys = new ArrayList<>(indexed);

            for (String key : keys) {
                removeEntry(key);
            }

            invalidations.addAndGet(keys.size());

            return keys.size();
        }

        synchronized int cleanupExpired() {
            List<String> expired = entries.entrySet()
                .stream()
                .filter(entry -> entry.getValue().isExpired())
                .map(Map.Entry::getKey)
                .toList();

            expired.forEach(this::removeEntry);

            return expired.size();
        }

        CacheStatistics statistics() {
            return new CacheStatistics(
                hits.get(),
                misses.get(),
                staleHits.get(),
                writes.get(),
                invalidations.get(),
                entries.size()
            );
        }
    }

    static final class DataAccessService {
        private final Repository repository;
        private final CacheManager cache;

        DataAccessService(
            Repository repository,
            CacheManager cache
        ) {
            this.repository = repository;
            this.cache = cache;
        }

        Product getProduct(
            int id,
            FetchPolicy fetchPolicy
        ) {
            if (fetchPolicy == FetchPolicy.NO_STORE) {
                return repository.findById(id);
            }

            String key = "product:" + id;

            Optional<Product> cached = cache.get(key);

            if (cached.isPresent()) {
                return cached.get();
            }

            Product product = repository.findById(id);

            cache.put(
                key,
                product,
                new CachePolicy(
                    Duration.ofMinutes(5),
                    Set.of("products", "product:" + id),
                    Set.of("/products", "/products/" + id)
                )
            );

            return product;
        }

        List<Product> getCatalog() {
            String key = "catalog:products";

            Optional<List<Product>> cached = cache.get(key);

            if (cached.isPresent()) {
                return cached.get();
            }

            List<Product> products = List.copyOf(
                repository.findAll()
            );

            cache.put(
                key,
                products,
                new CachePolicy(
                    Duration.ofMinutes(10),
                    Set.of("products"),
                    Set.of("/products")
                )
            );

            return products;
        }

        Product updateProduct(
            int id,
            Optional<Double> price,
            Optional<Integer> stock
        ) {
            Product updated = repository.update(id, price, stock);

            cache.invalidate(
                RevalidationMode.TAG,
                "product:" + id
            );

            cache.invalidate(
                RevalidationMode.TAG,
                "products"
            );

            return updated;
        }
    }

    interface RenderPolicy {
        RenderMode determine(RequestContext context);
    }

    static final class EnterpriseRenderPolicy
        implements RenderPolicy {

        @Override
        public RenderMode determine(RequestContext context) {
            if (
                context.isPersonalized() ||
                context.readsCookies() ||
                context.readsHeaders() ||
                context.usesUncachedData()
            ) {
                return RenderMode.DYNAMIC;
            }

            return RenderMode.PARTIAL;
        }
    }

    record RenderedPage(
        String path,
        RenderMode mode,
        Product product,
        Optional<String> userId,
        Instant generatedAt
    ) {}

    static final class PageService {
        private final DataAccessService dataService;
        private final RenderPolicy renderPolicy;

        PageService(
            DataAccessService dataService,
            RenderPolicy renderPolicy
        ) {
            this.dataService = dataService;
            this.renderPolicy = renderPolicy;
        }

        RenderedPage render(
            int productId,
            RequestContext context
        ) {
            Product product = dataService.getProduct(
                productId,
                FetchPolicy.CACHED
            );

            return new RenderedPage(
                "/products/" + productId,
                renderPolicy.determine(context),
                product,
                context.userId(),
                Instant.now()
            );
        }
    }

    record RouteRule(
        String path,
        boolean personalized,
        boolean sharedCaching,
        Duration ttl,
        Set<String> tags
    ) {
        RouteRule {
            if (path == null || !path.startsWith("/")) {
                throw new IllegalArgumentException(
                    "Route must be absolute."
                );
            }

            if (ttl.isNegative()) {
                throw new IllegalArgumentException(
                    "TTL cannot be negative."
                );
            }

            tags = Set.copyOf(tags);

            if (personalized && sharedCaching) {
                throw new IllegalArgumentException(
                    "Personalized routes cannot use shared caching."
                );
            }
        }
    }

    static final class RouteGovernanceService {
        private final Map<String, RouteRule> rules =
            new LinkedHashMap<>();

        void register(RouteRule rule) {
            if (rules.containsKey(rule.path())) {
                throw new ArchitectureException(
                    "Duplicate route policy: " + rule.path()
                );
            }

            rules.put(rule.path(), rule);
        }

        boolean isSharedCacheAllowed(String path) {
            RouteRule rule = rules.get(path);

            if (rule == null) {
                throw new NotFoundException(
                    "No route policy for " + path
                );
            }

            return rule.sharedCaching() &&
                   !rule.personalized();
        }

        List<RouteRule> allRules() {
            return Collections.unmodifiableList(
                new ArrayList<>(rules.values())
            );
        }
    }

    static void runTests() {
        Repository repository = new Repository();
        CacheManager cache = new CacheManager();

        DataAccessService service =
            new DataAccessService(repository, cache);

        Product first = service.getProduct(
            101,
            FetchPolicy.CACHED
        );

        Product second = service.getProduct(
            101,
            FetchPolicy.CACHED
        );

        if (!first.equals(second)) {
            throw new AssertionError("Cache retrieval failed.");
        }

        Product updated = service.updateProduct(
            101,
            Optional.of(72000.0),
            Optional.of(20)
        );

        if (updated.version() != 2) {
            throw new AssertionError("Version check failed.");
        }

        Product refreshed = service.getProduct(
            101,
            FetchPolicy.CACHED
        );

        if (refreshed.price() != 72000.0) {
            throw new AssertionError("Revalidation failed.");
        }

        EnterpriseRenderPolicy policy =
            new EnterpriseRenderPolicy();

        RenderMode dynamic = policy.determine(
            new RequestContext(
                Optional.of("user-501"),
                true,
                false,
                false
            )
        );

        if (dynamic != RenderMode.DYNAMIC) {
            throw new AssertionError("Dynamic rendering failed.");
        }

        try {
            new RouteRule(
                "/account",
                true,
                true,
                Duration.ofMinutes(5),
                Set.of("account")
            );

            throw new AssertionError(
                "Unsafe cache policy was accepted."
            );
        } catch (IllegalArgumentException expected) {
            // Expected policy rejection.
        }

        System.out.println("All Java 17 tests passed.");
    }

    public static void main(String[] args) {
        runTests();

        System.out.println(
            "\nNEXT.JS ENTERPRISE DATA ARCHITECTURE"
        );

        Repository repository = new Repository();
        CacheManager cache = new CacheManager();

        DataAccessService dataService =
            new DataAccessService(repository, cache);

        EnterpriseRenderPolicy renderPolicy =
            new EnterpriseRenderPolicy();

        PageService pageService =
            new PageService(dataService, renderPolicy);

        System.out.println("\n1. Server-side data fetching");

        Product product = dataService.getProduct(
            101,
            FetchPolicy.CACHED
        );

        System.out.println(product);

        System.out.println("\n2. Parallel data access");

        CompletableFuture<Product> laptop = CompletableFuture.supplyAsync(
            () -> dataService.getProduct(101, FetchPolicy.CACHED)
        );

        CompletableFuture<Product> keyboard = CompletableFuture.supplyAsync(
            () -> dataService.getProduct(102, FetchPolicy.CACHED)
        );

        CompletableFuture<List<Product>> catalog = CompletableFuture.supplyAsync(
            dataService::getCatalog
        );

        CompletableFuture.allOf(
            laptop,
            keyboard,
            catalog
        ).join();

        System.out.println(
            "Parallel operations completed."
        );

        System.out.println("\n3. Dynamic rendering");

        RequestContext publicRequest = new RequestContext(
            Optional.empty(),
            false,
            false,
            false
        );

        RequestContext privateRequest = new RequestContext(
            Optional.of("customer-501"),
            true,
            false,
            true
        );

        System.out.println(
            "Public page: " +
            pageService.render(101, publicRequest).mode()
        );

        System.out.println(
            "Private page: " +
            pageService.render(101, privateRequest).mode()
        );

        System.out.println("\n4. Cache policy registration");

        RouteGovernanceService governance =
            new RouteGovernanceService();

        governance.register(new RouteRule(
            "/products",
            false,
            true,
            Duration.ofMinutes(10),
            Set.of("products")
        ));

        governance.register(new RouteRule(
            "/account",
            true,
            false,
            Duration.ZERO,
            Set.of("account")
        ));

        for (RouteRule rule : governance.allRules()) {
            System.out.println(rule);
        }

        System.out.println("\n5. Policy evaluation");

        System.out.println(
            "/products shared cache: " +
            governance.isSharedCacheAllowed("/products")
        );

        System.out.println(
            "/account shared cache: " +
            governance.isSharedCacheAllowed("/account")
        );

        System.out.println("\n6. Mutation and revalidation");

        Product changed = dataService.updateProduct(
            101,
            Optional.of(70000.0),
            Optional.of(25)
        );

        System.out.println("Updated: " + changed);

        System.out.println(
            "Fresh data: " +
            dataService.getProduct(
                101,
                FetchPolicy.CACHED
            )
        );

        System.out.println("\n7. Cache statistics");

        CacheStatistics statistics = cache.statistics();

        System.out.println(statistics);
        System.out.printf(
            "Hit ratio: %.2f%%%n",
            statistics.hitRatio() * 100
        );

        System.out.println("\n8. Error handling");

        try {
            dataService.getProduct(999, FetchPolicy.CACHED);
        } catch (NotFoundException error) {
            System.out.println(
                "Handled missing record: " + error.getMessage()
            );
        }

        System.out.println("\n9. Cleanup");

        System.out.println(
            "Expired entries removed: " +
            cache.cleanupExpired()
        );

        System.out.println("\nExecution completed.");
    }
}
