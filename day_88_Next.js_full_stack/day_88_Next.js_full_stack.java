import java.net.URI;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentMap;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Function;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

/*
 * Next.js Full-Stack Architecture
 *
 * Enterprise-oriented Java 17 implementation.
 *
 * Covers:
 * - Environment configuration
 * - Route handler architecture
 * - Middleware
 * - Server action semantics
 * - Authentication and authorization
 * - Validation
 * - Repository abstraction
 * - Cache invalidation
 * - Request lifecycle
 *
 * Compile:
 * javac NextJsFullStack.java
 *
 * Run:
 * java NextJsFullStack
 */

public class NextJsFullStack {

    // ---------------------------------------------------
    // Exceptions
    // ---------------------------------------------------

    static class ApplicationException extends RuntimeException {
        private final int status;
        private final String code;

        ApplicationException(
                String message,
                int status,
                String code
        ) {
            super(message);
            this.status = status;
            this.code = code;
        }

        int status() {
            return status;
        }

        String code() {
            return code;
        }
    }

    static class ConfigurationException
            extends RuntimeException {

        ConfigurationException(String message) {
            super(message);
        }
    }

    // ---------------------------------------------------
    // Environment Configuration
    // ---------------------------------------------------

    record AppConfig(
            URI databaseUri,
            String sessionSecret,
            String environment,
            String publicAppName
    ) {
        AppConfig {
            Objects.requireNonNull(databaseUri);
            Objects.requireNonNull(sessionSecret);
            Objects.requireNonNull(environment);
            Objects.requireNonNull(publicAppName);
        }
    }

    static final class EnvironmentManager {

        private static final List<String> REQUIRED =
                List.of(
                        "DATABASE_URL",
                        "SESSION_SECRET",
                        "APP_ENV"
                );

        static AppConfig load(Map<String, String> source) {

            List<String> missing = REQUIRED.stream()
                    .filter(key -> {
                        String value = source.get(key);
                        return value == null || value.isBlank();
                    })
                    .toList();

            if (!missing.isEmpty()) {
                throw new ConfigurationException(
                        "Missing configuration: " + missing
                );
            }

            String secret = source.get("SESSION_SECRET");

            if (secret.length() < 32) {
                throw new ConfigurationException(
                        "SESSION_SECRET requires 32 characters"
                );
            }

            String environment = source.get("APP_ENV");

            if (!List.of(
                    "development",
                    "production",
                    "test"
            ).contains(environment)) {
                throw new ConfigurationException(
                        "Invalid application environment"
                );
            }

            URI database;

            try {
                database = URI.create(source.get("DATABASE_URL"));
            } catch (IllegalArgumentException error) {
                throw new ConfigurationException(
                        "Malformed DATABASE_URL"
                );
            }

            if (!List.of("postgres", "postgresql")
                    .contains(database.getScheme())) {
                throw new ConfigurationException(
                        "PostgreSQL connection required"
                );
            }

            return new AppConfig(
                    database,
                    secret,
                    environment,
                    source.getOrDefault(
                            "NEXT_PUBLIC_APP_NAME",
                            "Application"
                    )
            );
        }
    }

    // ---------------------------------------------------
    // Domain Types
    // ---------------------------------------------------

    enum Role {
        USER,
        ADMIN
    }

    record User(
            int id,
            String username,
            Role role,
            boolean active
    ) {
        User {
            if (id <= 0) {
                throw new IllegalArgumentException(
                        "Invalid user ID"
                );
            }

            if (username == null || username.isBlank()) {
                throw new IllegalArgumentException(
                        "Username required"
                );
            }

            Objects.requireNonNull(role);
        }
    }

    record Task(
            int id,
            int userId,
            String title,
            boolean completed,
            Instant createdAt
    ) {}

    record Request(
            String requestId,
            String method,
            String path,
            Optional<User> user,
            Map<String, Object> body
    ) {
        Request {
            Objects.requireNonNull(requestId);
            Objects.requireNonNull(method);
            Objects.requireNonNull(path);
            Objects.requireNonNull(user);

            body = Collections.unmodifiableMap(
                    new HashMap<>(body)
            );
        }

        static Request create(
                String method,
                String path,
                User user,
                Map<String, Object> body
        ) {
            return new Request(
                    UUID.randomUUID().toString(),
                    method,
                    path,
                    Optional.ofNullable(user),
                    body
            );
        }
    }

    record Response(
            int status,
            Map<String, Object> body,
            Map<String, String> headers
    ) {
        static Response of(
                int status,
                String message
        ) {
            return new Response(
                    status,
                    Map.of("message", message),
                    Map.of("Content-Type", "application/json")
            );
        }

        static Response error(
                int status,
                String message,
                String code
        ) {
            return new Response(
                    status,
                    Map.of(
                            "error", message,
                            "code", code
                    ),
                    Map.of("Content-Type", "application/json")
            );
        }
    }

    // ---------------------------------------------------
    // Validation Service
    // ---------------------------------------------------

    static final class ValidationService {

        private static final Pattern INVALID_CONTROL =
                Pattern.compile(
                        "[\\x00-\\x08\\x0B\\x0C\\x0E-\\x1F]"
                );

        static String title(Object value) {

            if (!(value instanceof String text)) {
                throw new ApplicationException(
                        "Title must be a string",
                        400,
                        "INVALID_TITLE"
                );
            }

            String result = text.strip();

            if (
                    result.isEmpty() ||
                    result.length() > 120 ||
                    INVALID_CONTROL.matcher(result).find()
            ) {
                throw new ApplicationException(
                        "Invalid task title",
                        400,
                        "INVALID_TITLE"
                );
            }

            return result;
        }

        static int positiveId(String value) {
            try {
                int id = Integer.parseInt(value);

                if (id <= 0) {
                    throw new NumberFormatException();
                }

                return id;

            } catch (NumberFormatException error) {
                throw new ApplicationException(
                        "Invalid resource ID",
                        400,
                        "INVALID_ID"
                );
            }
        }

        static boolean booleanValue(Object value) {
            if (!(value instanceof Boolean result)) {
                throw new ApplicationException(
                        "Expected boolean value",
                        400,
                        "INVALID_BOOLEAN"
                );
            }

            return result;
        }
    }

    // ---------------------------------------------------
    // Repository Interface
    // ---------------------------------------------------

    interface TaskStore {
        Task create(int userId, String title);

        List<Task> findByUser(int userId);

        Task update(
                int taskId,
                int userId,
                boolean completed
        );

        boolean delete(int taskId, int userId);
    }

    // ---------------------------------------------------
    // Repository Implementation
    // ---------------------------------------------------

    static final class InMemoryTaskStore
            implements TaskStore {

        private final ConcurrentMap<Integer, Task> tasks =
                new ConcurrentHashMap<>();

        private final AtomicInteger sequence =
                new AtomicInteger(1);

        private final Map<Integer, User> users =
                new ConcurrentHashMap<>();

        void register(User user) {
            User previous = users.putIfAbsent(user.id(), user);

            if (previous != null) {
                throw new IllegalArgumentException(
                        "Duplicate user ID"
                );
            }
        }

        Optional<User> findUser(int id) {
            return Optional.ofNullable(users.get(id));
        }

        @Override
        public Task create(int userId, String title) {
            if (!users.containsKey(userId)) {
                throw new ApplicationException(
                        "User not found",
                        404,
                        "USER_NOT_FOUND"
                );
            }

            int id = sequence.getAndIncrement();

            Task task = new Task(
                    id,
                    userId,
                    title,
                    false,
                    Instant.now()
            );

            tasks.put(id, task);

            return task;
        }

        @Override
        public List<Task> findByUser(int userId) {
            return tasks.values()
                    .stream()
                    .filter(task -> task.userId() == userId)
                    .sorted(
                            java.util.Comparator.comparingInt(
                                    Task::id
                            )
                    )
                    .toList();
        }

        @Override
        public Task update(
                int taskId,
                int userId,
                boolean completed
        ) {
            Task current = tasks.get(taskId);

            if (current == null) {
                throw new ApplicationException(
                        "Task not found",
                        404,
                        "TASK_NOT_FOUND"
                );
            }

            if (current.userId() != userId) {
                throw new ApplicationException(
                        "Task ownership violation",
                        403,
                        "FORBIDDEN"
                );
            }

            Task updated = new Task(
                    current.id(),
                    current.userId(),
                    current.title(),
                    completed,
                    current.createdAt()
            );

            tasks.replace(taskId, current, updated);

            return Objects.requireNonNull(
                    tasks.get(taskId)
            );
        }

        @Override
        public boolean delete(int taskId, int userId) {
            Task current = tasks.get(taskId);

            if (current == null) {
                return false;
            }

            if (current.userId() != userId) {
                throw new ApplicationException(
                        "Task ownership violation",
                        403,
                        "FORBIDDEN"
                );
            }

            return tasks.remove(taskId, current);
        }
    }

    // ---------------------------------------------------
    // Cache Service
    // ---------------------------------------------------

    static final class CacheService {

        private final ConcurrentMap<String, List<Task>> cache =
                new ConcurrentHashMap<>();

        Optional<List<Task>> get(String key) {
            return Optional.ofNullable(cache.get(key));
        }

        void put(String key, List<Task> tasks) {
            cache.put(key, List.copyOf(tasks));
        }

        void invalidate(String key) {
            cache.remove(key);
        }
    }

    // ---------------------------------------------------
    // Middleware
    // ---------------------------------------------------

    interface Middleware {
        Optional<Response> execute(Request request);
    }

    static final class AuthenticationMiddleware
            implements Middleware {

        private final List<String> protectedPaths =
                List.of(
                        "/dashboard",
                        "/api/tasks"
                );

        @Override
        public Optional<Response> execute(Request request) {

            if (
                    request.path().contains("..") ||
                    request.path().contains("\0")
            ) {
                return Optional.of(
                        Response.error(
                                400,
                                "Invalid path",
                                "INVALID_PATH"
                        )
                );
            }

            boolean protectedRoute = protectedPaths.stream()
                    .anyMatch(prefix ->
                            request.path().equals(prefix) ||
                            request.path().startsWith(prefix + "/")
                    );

            if (protectedRoute && request.user().isEmpty()) {
                return Optional.of(
                        Response.error(
                                401,
                                "Authentication required",
                                "UNAUTHENTICATED"
                        )
                );
            }

            if (
                    request.user().isPresent() &&
                    !request.user().get().active()
            ) {
                return Optional.of(
                        Response.error(
                                403,
                                "Inactive account",
                                "ACCOUNT_DISABLED"
                        )
                );
            }

            return Optional.empty();
        }
    }

    // ---------------------------------------------------
    // Route Handler Service
    // ---------------------------------------------------

    static final class RouteHandlerService {

        private final TaskStore store;
        private final CacheService cache;

        private static final Pattern SINGLE_TASK =
                Pattern.compile(
                        "^/api/tasks/([1-9][0-9]*)$"
                );

        RouteHandlerService(
                TaskStore store,
                CacheService cache
        ) {
            this.store = store;
            this.cache = cache;
        }

        Response dispatch(Request request) {

            User user = request.user().orElseThrow(
                    () -> new ApplicationException(
                            "Authentication required",
                            401,
                            "UNAUTHENTICATED"
                    )
            );

            String method = request.method();

            if (request.path().equals("/api/tasks")) {

                if (method.equals("GET")) {
                    return getTasks(user);
                }

                if (method.equals("POST")) {
                    return createTask(user, request.body());
                }

                return Response.error(
                        405,
                        "Method not allowed",
                        "METHOD_NOT_ALLOWED"
                );
            }

            var matcher = SINGLE_TASK.matcher(
                    request.path()
            );

            if (matcher.matches()) {
                int id = ValidationService.positiveId(
                        matcher.group(1)
                );

                if (method.equals("PATCH")) {
                    return updateTask(
                            user,
                            id,
                            request.body()
                    );
                }

                if (method.equals("DELETE")) {
                    return deleteTask(user, id);
                }
            }

            return Response.error(
                    404,
                    "Route not found",
                    "NOT_FOUND"
            );
        }

        private Response getTasks(User user) {
            String key = "tasks:" + user.id();

            List<Task> tasks = cache.get(key)
                    .orElseGet(() -> {
                        List<Task> result =
                                store.findByUser(user.id());

                        cache.put(key, result);

                        return result;
                    });

            return new Response(
                    200,
                    Map.of("tasks", tasks),
                    Map.of(
                            "Content-Type",
                            "application/json"
                    )
            );
        }

        private Response createTask(
                User user,
                Map<String, Object> body
        ) {
            String title = ValidationService.title(
                    body.get("title")
            );

            Task task = store.create(user.id(), title);

            cache.invalidate("tasks:" + user.id());

            return new Response(
                    201,
                    Map.of("task", task),
                    Map.of("Content-Type", "application/json")
            );
        }

        private Response updateTask(
                User user,
                int taskId,
                Map<String, Object> body
        ) {
            boolean completed =
                    ValidationService.booleanValue(
                            body.get("completed")
                    );

            Task task = store.update(
                    taskId,
                    user.id(),
                    completed
            );

            cache.invalidate("tasks:" + user.id());

            return new Response(
                    200,
                    Map.of("task", task),
                    Map.of("Content-Type", "application/json")
            );
        }

        private Response deleteTask(
                User user,
                int taskId
        ) {
            boolean deleted = store.delete(
                    taskId,
                    user.id()
            );

            if (!deleted) {
                return Response.error(
                        404,
                        "Task not found",
                        "TASK_NOT_FOUND"
                );
            }

            cache.invalidate("tasks:" + user.id());

            return Response.of(
                    200,
                    "Task deleted"
            );
        }
    }

    // ---------------------------------------------------
    // Server Action Service
    // ---------------------------------------------------

    static final class ServerActionService {

        private final TaskStore store;
        private final CacheService cache;

        ServerActionService(
                TaskStore store,
                CacheService cache
        ) {
            this.store = store;
            this.cache = cache;
        }

        Response createTask(
                Optional<User> authenticatedUser,
                Map<String, Object> formData
        ) {
            User user = authenticatedUser.orElseThrow(
                    () -> new ApplicationException(
                            "Authentication required",
                            401,
                            "UNAUTHENTICATED"
                    )
            );

            if (!user.active()) {
                throw new ApplicationException(
                        "Inactive account",
                        403,
                        "ACCOUNT_DISABLED"
                );
            }

            String title = ValidationService.title(
                    formData.get("title")
            );

            Task task = store.create(user.id(), title);

            cache.invalidate("tasks:" + user.id());

            return new Response(
                    201,
                    Map.of(
                            "success", true,
                            "task", task,
                            "revalidatedPath", "/dashboard"
                    ),
                    Map.of("Content-Type", "application/json")
            );
        }
    }

    // ---------------------------------------------------
    // Application Service
    // ---------------------------------------------------

    static final class Application {

        private final AppConfig config;
        private final InMemoryTaskStore store;
        private final CacheService cache;
        private final List<Middleware> middleware;
        private final RouteHandlerService routes;
        private final ServerActionService actions;

        Application(AppConfig config) {
            this.config = config;

            this.store = new InMemoryTaskStore();
            this.cache = new CacheService();

            this.middleware = List.of(
                    new AuthenticationMiddleware()
            );

            this.routes = new RouteHandlerService(
                    store,
                    cache
            );

            this.actions = new ServerActionService(
                    store,
                    cache
            );
        }

        void register(User user) {
            store.register(user);
        }

        Response handle(Request request) {
            try {
                for (Middleware layer : middleware) {
                    Optional<Response> response =
                            layer.execute(request);

                    if (response.isPresent()) {
                        return response.get();
                    }
                }

                return routes.dispatch(request);

            } catch (ApplicationException error) {
                return Response.error(
                        error.status(),
                        error.getMessage(),
                        error.code()
                );

            } catch (RuntimeException error) {
                System.err.println(
                        "Request failure: " + error.getMessage()
                );

                return Response.error(
                        500,
                        "Internal server error",
                        "INTERNAL_ERROR"
                );
            }
        }

        Response executeAction(
                User user,
                Map<String, Object> formData
        ) {
            return actions.createTask(
                    Optional.ofNullable(user),
                    formData
            );
        }

        String applicationName() {
            return config.publicAppName();
        }
    }

    // ---------------------------------------------------
    // Demonstration
    // ---------------------------------------------------

    public static void main(String[] args) {

        try {
            Map<String, String> environment = Map.of(
                    "DATABASE_URL",
                    "postgresql://app:secret@localhost:5432/tasks",
                    "SESSION_SECRET",
                    "0123456789abcdef0123456789abcdef",
                    "APP_ENV",
                    "development",
                    "NEXT_PUBLIC_APP_NAME",
                    "Enterprise Task Manager"
            );

            AppConfig config =
                    EnvironmentManager.load(environment);

            Application application =
                    new Application(config);

            User alice = new User(
                    1,
                    "alice",
                    Role.USER,
                    true
            );

            User bob = new User(
                    2,
                    "bob",
                    Role.USER,
                    true
            );

            application.register(alice);
            application.register(bob);

            System.out.println(
                    "Application: " +
                    application.applicationName()
            );

            // Authentication failure.
            Response unauthorized = application.handle(
                    Request.create(
                            "GET",
                            "/api/tasks",
                            null,
                            Map.of()
                    )
            );

            System.out.println(
                    "\nUnauthenticated request: " +
                    unauthorized.status()
            );

            // Route handler creates a task.
            Response created = application.handle(
                    Request.create(
                            "POST",
                            "/api/tasks",
                            alice,
                            Map.of(
                                    "title",
                                    "Implement route handlers"
                            )
                    )
            );

            System.out.println(
                    "\nCreate task: " + created.status()
            );

            System.out.println(created.body());

            // Retrieve user tasks.
            Response retrieved = application.handle(
                    Request.create(
                            "GET",
                            "/api/tasks",
                            alice,
                            Map.of()
                    )
            );

            System.out.println(
                    "\nRetrieved tasks: " +
                    retrieved.body()
            );

            // Cross-user update.
            Response forbidden = application.handle(
                    Request.create(
                            "PATCH",
                            "/api/tasks/1",
                            bob,
                            Map.of("completed", true)
                    )
            );

            System.out.println(
                    "\nOwnership violation: " +
                    forbidden.status()
            );

            // Server action.
            Response action = application.executeAction(
                    alice,
                    Map.of(
                            "title",
                            "Implement server actions"
                    )
            );

            System.out.println(
                    "\nServer action: " +
                    action.body()
            );

            // Invalid request.
            Response invalid = application.handle(
                    Request.create(
                            "POST",
                            "/api/tasks",
                            alice,
                            Map.of("title", "")
                    )
            );

            System.out.println(
                    "\nInvalid input: " +
                    invalid.status()
            );

            // Missing resource.
            Response missing = application.handle(
                    Request.create(
                            "PATCH",
                            "/api/tasks/999",
                            alice,
                            Map.of("completed", true)
                    )
            );

            System.out.println(
                    "\nMissing task: " +
                    missing.status()
            );

            System.out.println(
                    "\nEnterprise workflow completed."
            );

        } catch (ConfigurationException error) {
            System.err.println(
                    "Configuration error: " +
                    error.getMessage()
            );

            System.exit(1);
        }
    }
}
