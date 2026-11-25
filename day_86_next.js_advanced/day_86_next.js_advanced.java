import java.time.Duration;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionException;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Supplier;

/*
 * Next.js Advanced Architecture
 *
 * Enterprise-oriented component rendering and lifecycle model.
 *
 * Covers:
 * - Server Components
 * - Client Components
 * - Serializable component contracts
 * - Server-side data services
 * - Loading boundaries
 * - Asynchronous execution
 * - Error boundaries and recovery
 * - Nested route management
 * - Request-level caching
 * - Rendering policy validation
 *
 * Java 17, no external dependencies.
 *
 * Compile:
 * javac NextJsAdvanced.java
 *
 * Run:
 * java NextJsAdvanced
 */

public class NextJsAdvanced {

    enum ComponentKind {
        SERVER,
        CLIENT
    }

    enum RenderState {
        CREATED,
        LOADING,
        STREAMING,
        READY,
        ERROR,
        NOT_FOUND,
        RECOVERED
    }

    enum BoundaryKind {
        SUSPENSE,
        ERROR
    }

    static class ApplicationException extends RuntimeException {
        ApplicationException(String message) {
            super(message);
        }
    }

    static class ResourceNotFoundException
            extends ApplicationException {

        ResourceNotFoundException(String message) {
            super(message);
        }
    }

    static class SerializationException
            extends ApplicationException {

        SerializationException(String message) {
            super(message);
        }
    }

    static class InvalidStateException
            extends ApplicationException {

        InvalidStateException(String message) {
            super(message);
        }
    }

    /*
     * Immutable domain record.
     * Sensitive repository fields are not exposed through this type.
     */
    record PublicUser(
            int id,
            String name,
            String role
    ) {
        PublicUser {
            if (id <= 0) {
                throw new IllegalArgumentException(
                        "User ID must be positive."
                );
            }

            Objects.requireNonNull(name);
            Objects.requireNonNull(role);

            if (name.isBlank() || role.isBlank()) {
                throw new IllegalArgumentException(
                        "User name and role are required."
                );
            }
        }
    }

    record DashboardMetrics(
            int activeProjects,
            int pendingTasks,
            int completedTasks
    ) {
        DashboardMetrics {
            if (activeProjects < 0 ||
                    pendingTasks < 0 ||
                    completedTasks < 0) {
                throw new IllegalArgumentException(
                        "Metrics cannot be negative."
                );
            }
        }
    }

    record DashboardData(
            PublicUser user,
            DashboardMetrics metrics
    ) {
        DashboardData {
            Objects.requireNonNull(user);
            Objects.requireNonNull(metrics);
        }
    }

    record ComponentDefinition(
            String name,
            ComponentKind kind,
            Map<String, Object> props
    ) {
        ComponentDefinition {
            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException(
                        "Component name is required."
                );
            }

            Objects.requireNonNull(kind);
            Objects.requireNonNull(props);

            props = Collections.unmodifiableMap(
                    new LinkedHashMap<>(props)
            );
        }
    }

    record RenderResult<T>(
            String component,
            RenderState state,
            T output,
            String error,
            long durationMillis
    ) {
        static <T> RenderResult<T> ready(
                String component,
                T output,
                long duration
        ) {
            return new RenderResult<>(
                    component,
                    RenderState.READY,
                    output,
                    null,
                    duration
            );
        }

        static <T> RenderResult<T> failed(
                String component,
                RenderState state,
                String error
        ) {
            return new RenderResult<>(
                    component,
                    state,
                    null,
                    error,
                    0
            );
        }
    }

    /*
     * Server-side data service.
     *
     * Private fields never enter the public component contract.
     */
    interface UserDataService {
        PublicUser getUser(int id);

        DashboardMetrics getMetrics();
    }

    static class InMemoryUserDataService
            implements UserDataService {

        private record InternalUser(
                int id,
                String name,
                String role,
                String privateToken
        ) {}

        private final Map<Integer, InternalUser> users;

        InMemoryUserDataService() {
            Map<Integer, InternalUser> data = new HashMap<>();

            data.put(
                    1,
                    new InternalUser(
                            1,
                            "Atul",
                            "administrator",
                            "SERVER_SECRET"
                    )
            );

            data.put(
                    2,
                    new InternalUser(
                            2,
                            "Developer",
                            "member",
                            "ANOTHER_SECRET"
                    )
            );

            users = Collections.unmodifiableMap(data);
        }

        @Override
        public PublicUser getUser(int id) {
            InternalUser user = users.get(id);

            if (user == null) {
                throw new ResourceNotFoundException(
                        "User not found: " + id
                );
            }

            return new PublicUser(
                    user.id(),
                    user.name(),
                    user.role()
            );
        }

        @Override
        public DashboardMetrics getMetrics() {
            return new DashboardMetrics(12, 8, 24);
        }
    }

    /*
     * Validates a simplified React Server Component prop contract.
     *
     * Supports:
     * - null
     * - strings
     * - booleans
     * - finite numbers
     * - lists
     * - string-keyed maps
     *
     * Functions, arbitrary class instances and cyclic structures
     * are rejected by this deliberately restrictive contract.
     */
    static class SerializableProps {

        static void validate(Object value) {
            validate(value, new java.util.IdentityHashMap<>());
        }

        private static void validate(
                Object value,
                java.util.IdentityHashMap<Object, Boolean> visited
        ) {
            if (value == null ||
                    value instanceof String ||
                    value instanceof Boolean) {
                return;
            }

            if (value instanceof Number number) {
                if (!Double.isFinite(number.doubleValue())) {
                    throw new SerializationException(
                            "Non-finite number is not supported."
                    );
                }
                return;
            }

            if (value instanceof Enum<?>) {
                return;
            }

            if (visited.containsKey(value)) {
                throw new SerializationException(
                        "Circular reference detected."
                );
            }

            visited.put(value, Boolean.TRUE);

            try {
                if (value instanceof List<?> list) {
                    for (Object item : list) {
                        validate(item, visited);
                    }
                    return;
                }

                if (value instanceof Map<?, ?> map) {
                    for (Map.Entry<?, ?> entry : map.entrySet()) {
                        if (!(entry.getKey() instanceof String)) {
                            throw new SerializationException(
                                    "Map keys must be strings."
                            );
                        }

                        validate(entry.getValue(), visited);
                    }
                    return;
                }

                throw new SerializationException(
                        "Unsupported prop type: " +
                                value.getClass().getSimpleName()
                );

            } finally {
                visited.remove(value);
            }
        }
    }

    /*
     * Request-scoped concurrent cache.
     *
     * Concurrent callers for one key share the same future.
     * Failed computations are removed to permit retries.
     */
    static class RequestCache {

        private final ConcurrentHashMap<
                String,
                CompletableFuture<Object>
        > entries = new ConcurrentHashMap<>();

        @SuppressWarnings("unchecked")
        <T> CompletableFuture<T> get(
                String key,
                Supplier<CompletableFuture<T>> loader
        ) {
            CompletableFuture<Object> future =
                    entries.computeIfAbsent(
                            key,
                            ignored -> {
                                CompletableFuture<T> created =
                                        loader.get();

                                return created.thenApply(
                                        value -> (Object) value
                                );
                            }
                    );

            return future.thenApply(value -> (T) value)
                    .whenComplete((value, error) -> {
                        if (error != null) {
                            entries.remove(key, future);
                        }
                    });
        }

        void clear() {
            entries.clear();
        }

        int size() {
            return entries.size();
        }
    }

    /*
     * Rendering service separates data retrieval from presentation.
     */
    static class ComponentRenderingService {

        private final UserDataService dataService;
        private RequestCache cache = new RequestCache();

        ComponentRenderingService(UserDataService dataService) {
            this.dataService = Objects.requireNonNull(dataService);
        }

        void beginRequest() {
            cache.clear();
            cache = new RequestCache();
        }

        CompletableFuture<RenderResult<DashboardData>>
        renderDashboard(ComponentDefinition component) {

            if (component.kind() != ComponentKind.SERVER) {
                throw new InvalidStateException(
                        "Dashboard must be a Server Component."
                );
            }

            long started = System.nanoTime();

            int userId = readUserId(component.props());

            CompletableFuture<PublicUser> user =
                    cache.get(
                            "user:" + userId,
                            () -> CompletableFuture.supplyAsync(
                                    () -> dataService.getUser(userId)
                            )
                    );

            CompletableFuture<DashboardMetrics> metrics =
                    cache.get(
                            "metrics",
                            () -> CompletableFuture.supplyAsync(
                                    dataService::getMetrics
                            )
                    );

            return user.thenCombine(
                    metrics,
                    DashboardData::new
            ).handle((data, error) -> {

                long elapsed = TimeUnit.NANOSECONDS.toMillis(
                        System.nanoTime() - started
                );

                if (error != null) {
                    Throwable cause = unwrap(error);

                    RenderState state =
                            cause instanceof ResourceNotFoundException
                                    ? RenderState.NOT_FOUND
                                    : RenderState.ERROR;

                    return RenderResult.<DashboardData>failed(
                            component.name(),
                            state,
                            cause.getMessage()
                    );
                }

                return RenderResult.ready(
                        component.name(),
                        data,
                        elapsed
                );
            });
        }

        RenderResult<Map<String, Object>> renderClient(
                ComponentDefinition component,
                Map<String, Object> serverProps
        ) {
            if (component.kind() != ComponentKind.CLIENT) {
                throw new InvalidStateException(
                        "Client Component required."
                );
            }

            try {
                Map<String, Object> combined =
                        new LinkedHashMap<>(component.props());

                if (serverProps != null) {
                    combined.putAll(serverProps);
                }

                SerializableProps.validate(combined);

                return RenderResult.ready(
                        component.name(),
                        Collections.unmodifiableMap(combined),
                        0
                );

            } catch (SerializationException error) {
                return RenderResult.failed(
                        component.name(),
                        RenderState.ERROR,
                        error.getMessage()
                );
            }
        }

        private int readUserId(Map<String, Object> props) {
            Object value = props.getOrDefault("userId", 1);

            if (!(value instanceof Integer id) || id <= 0) {
                throw new IllegalArgumentException(
                        "userId must be a positive integer."
                );
            }

            return id;
        }

        private static Throwable unwrap(Throwable error) {
            Throwable current = error;

            while (
                    current instanceof CompletionException &&
                    current.getCause() != null
            ) {
                current = current.getCause();
            }

            return current;
        }
    }

    /*
     * Suspense boundary.
     *
     * A real Next.js loading.tsx is displayed when a route segment
     * suspends. It does not itself turn failed work into success.
     */
    static class SuspenseBoundary<T> {

        private final String name;
        private final String fallback;
        private RenderState state = RenderState.CREATED;

        SuspenseBoundary(String name, String fallback) {
            this.name = Objects.requireNonNull(name);
            this.fallback = Objects.requireNonNull(fallback);
        }

        CompletableFuture<RenderResult<T>> execute(
                Supplier<CompletableFuture<T>> operation,
                Duration timeout
        ) {
            if (timeout.isZero() || timeout.isNegative()) {
                throw new IllegalArgumentException(
                        "Timeout must be positive."
                );
            }

            state = RenderState.LOADING;

            CompletableFuture<T> future = operation.get();

            return future.orTimeout(
                    timeout.toMillis(),
                    TimeUnit.MILLISECONDS
            ).handle((value, error) -> {

                if (error == null) {
                    state = RenderState.READY;

                    return RenderResult.ready(
                            name,
                            value,
                            0
                    );
                }

                state = RenderState.ERROR;

                return RenderResult.failed(
                        name,
                        RenderState.ERROR,
                        unwrap(error).getMessage()
                );
            });
        }

        RenderState state() {
            return state;
        }

        String fallback() {
            return fallback;
        }
    }

    /*
     * Error boundary with explicit retry behavior.
     */
    static class ErrorBoundary<T> {

        private final String fallback;
        private final AtomicInteger attempts = new AtomicInteger();

        ErrorBoundary(String fallback) {
            this.fallback = Objects.requireNonNull(fallback);
        }

        RenderResult<T> execute(Supplier<T> operation) {
            try {
                return RenderResult.ready(
                        "ErrorBoundary",
                        operation.get(),
                        0
                );
            } catch (Exception error) {
                return RenderResult.failed(
                        "ErrorBoundary",
                        RenderState.ERROR,
                        error.getMessage() == null
                                ? fallback
                                : error.getMessage()
                );
            }
        }

        RenderResult<T> reset(Supplier<T> operation) {
            attempts.incrementAndGet();

            RenderResult<T> result = execute(operation);

            if (result.state() == RenderState.READY) {
                return new RenderResult<>(
                        result.component(),
                        RenderState.RECOVERED,
                        result.output(),
                        null,
                        result.durationMillis()
                );
            }

            return result;
        }

        int attempts() {
            return attempts.get();
        }

        String fallback() {
            return fallback;
        }
    }

    /*
     * Nested route segment model.
     */
    static class RouteSegment {

        private final String name;
        private final String loadingFallback;
        private final String errorFallback;

        private final Map<String, RouteSegment> children =
                new LinkedHashMap<>();

        RouteSegment(
                String name,
                String loadingFallback,
                String errorFallback
        ) {
            if (name == null || name.isBlank() ||
                    name.contains("..") ||
                    name.contains("/")) {
                throw new IllegalArgumentException(
                        "Invalid route segment."
                );
            }

            this.name = name;
            this.loadingFallback = loadingFallback;
            this.errorFallback = errorFallback;
        }

        void addChild(RouteSegment child) {
            Objects.requireNonNull(child);

            if (children.putIfAbsent(child.name, child) != null) {
                throw new IllegalArgumentException(
                        "Duplicate route: " + child.name
                );
            }
        }

        RouteSegment resolve(List<String> path) {
            RouteSegment current = this;

            for (String segment : path) {
                current = current.children.get(segment);

                if (current == null) {
                    throw new ResourceNotFoundException(
                            "Route not found: " + segment
                    );
                }
            }

            return current;
        }

        String name() {
            return name;
        }

        String loadingFallback() {
            return loadingFallback;
        }

        String errorFallback() {
            return errorFallback;
        }
    }

    private static Throwable unwrap(Throwable error) {
        while (
                error instanceof CompletionException &&
                error.getCause() != null
        ) {
            error = error.getCause();
        }

        return error;
    }

    private static void require(
            boolean condition,
            String message
    ) {
        if (!condition) {
            throw new AssertionError(message);
        }
    }

    static void runTests() {
        UserDataService service =
                new InMemoryUserDataService();

        ComponentRenderingService renderer =
                new ComponentRenderingService(service);

        renderer.beginRequest();

        ComponentDefinition dashboard =
                new ComponentDefinition(
                        "Dashboard",
                        ComponentKind.SERVER,
                        Map.of("userId", 1)
                );

        RenderResult<DashboardData> valid =
                renderer.renderDashboard(dashboard)
                        .join();

        require(
                valid.state() == RenderState.READY,
                "Dashboard rendering failed."
        );

        require(
                valid.output().user().name().equals("Atul"),
                "Incorrect user data."
        );

        ComponentDefinition missing =
                new ComponentDefinition(
                        "Dashboard",
                        ComponentKind.SERVER,
                        Map.of("userId", 999)
                );

        RenderResult<DashboardData> absent =
                renderer.renderDashboard(missing)
                        .join();

        require(
                absent.state() == RenderState.NOT_FOUND,
                "Missing resource state incorrect."
        );

        ComponentDefinition invalidClient =
                new ComponentDefinition(
                        "Controls",
                        ComponentKind.CLIENT,
                        Map.of("callback", (Runnable) () -> {})
                );

        require(
                renderer.renderClient(
                        invalidClient,
                        Map.of()
                ).state() == RenderState.ERROR,
                "Non-serializable props were accepted."
        );

        ErrorBoundary<String> boundary =
                new ErrorBoundary<>("Unavailable");

        AtomicInteger counter = new AtomicInteger();

        Supplier<String> operation = () -> {
            if (counter.incrementAndGet() == 1) {
                throw new ApplicationException(
                        "Temporary failure"
                );
            }

            return "Recovered";
        };

        require(
                boundary.execute(operation).state()
                        == RenderState.ERROR,
                "Error was not captured."
        );

        require(
                boundary.reset(operation).state()
                        == RenderState.RECOVERED,
                "Error recovery failed."
        );

        RouteSegment root = new RouteSegment(
                "dashboard",
                "Loading dashboard",
                "Dashboard unavailable"
        );

        root.addChild(new RouteSegment(
                "analytics",
                "Loading analytics",
                "Analytics unavailable"
        ));

        require(
                root.resolve(List.of("analytics"))
                        .name()
                        .equals("analytics"),
                "Nested route resolution failed."
        );

        boolean rejected = false;

        try {
            SerializableProps.validate(Double.NaN);
        } catch (SerializationException error) {
            rejected = true;
        }

        require(rejected, "NaN must be rejected.");

        System.out.println("All Java 17 tests passed.");
    }

    public static void main(String[] args) {
        System.out.println("NEXT.JS ADVANCED ARCHITECTURE");
        System.out.println("==============================");

        UserDataService dataService =
                new InMemoryUserDataService();

        ComponentRenderingService renderer =
                new ComponentRenderingService(dataService);

        renderer.beginRequest();

        ComponentDefinition dashboard =
                new ComponentDefinition(
                        "Dashboard",
                        ComponentKind.SERVER,
                        Map.of("userId", 1)
                );

        RenderResult<DashboardData> result =
                renderer.renderDashboard(dashboard)
                        .join();

        System.out.println("\nSERVER COMPONENT");

        System.out.println(
                "State: " + result.state()
        );

        System.out.println(
                "Data: " + result.output()
        );

        ComponentDefinition controls =
                new ComponentDefinition(
                        "DashboardControls",
                        ComponentKind.CLIENT,
                        Map.of(
                                "theme", "dark",
                                "refreshEnabled", true
                        )
                );

        RenderResult<Map<String, Object>> client =
                renderer.renderClient(
                        controls,
                        Map.of(
                                "userName",
                                result.output().user().name()
                        )
                );

        System.out.println("\nCLIENT COMPONENT");

        System.out.println(
                "State: " + client.state()
        );

        System.out.println(
                "Props: " + client.output()
        );

        System.out.println("\nSUSPENSE BOUNDARY");

        SuspenseBoundary<String> suspense =
                new SuspenseBoundary<>(
                        "Reports",
                        "Loading reports..."
                );

        RenderResult<String> loaded =
                suspense.execute(
                        () -> CompletableFuture.supplyAsync(
                                () -> "Five reports available."
                        ),
                        Duration.ofSeconds(2)
                ).join();

        System.out.println(
                loaded.state() + ": " + loaded.output()
        );

        System.out.println("\nERROR BOUNDARY");

        ErrorBoundary<String> boundary =
                new ErrorBoundary<>(
                        "Dashboard temporarily unavailable"
                );

        AtomicInteger attempts = new AtomicInteger();

        Supplier<String> unstable = () -> {
            if (attempts.incrementAndGet() == 1) {
                throw new ApplicationException(
                        "Database connection interrupted."
                );
            }

            return "Dashboard recovered.";
        };

        System.out.println(
                boundary.execute(unstable)
        );

        System.out.println(
                boundary.reset(unstable)
        );

        runTests();
    }
}
