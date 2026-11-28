import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

// ---------------------------------------------------------
// Backend Fundamentals: Java 17
//
// Enterprise-oriented REST API architecture.
//
// Compile:
// javac BackendFundamentals.java
//
// Run:
// java BackendFundamentals
// ---------------------------------------------------------

public class BackendFundamentals {

    private static final String HOST = "127.0.0.1";
    private static final int PORT = 8002;
    private static final int MAX_BODY_SIZE = 16_384;

    // -----------------------------------------------------
    // Domain types
    // -----------------------------------------------------

    enum TaskStatus {
        PENDING,
        IN_PROGRESS,
        COMPLETED
    }

    record Task(
        int id,
        String title,
        String description,
        TaskStatus status,
        Instant createdAt,
        Instant updatedAt
    ) {}

    record ApiResult(
        int status,
        String body
    ) {}

    // -----------------------------------------------------
    // Exceptions
    // -----------------------------------------------------

    static class ApiException extends RuntimeException {

        private final int status;
        private final String code;

        ApiException(
            int status,
            String code,
            String message
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

    static class ValidationException extends ApiException {

        ValidationException(String message) {
            super(400, "VALIDATION_ERROR", message);
        }
    }

    static class ResourceNotFoundException extends ApiException {

        ResourceNotFoundException(String message) {
            super(404, "NOT_FOUND", message);
        }
    }

    // -----------------------------------------------------
    // JSON serialization
    // -----------------------------------------------------

    static final class Json {

        private Json() {}

        static String escape(String value) {
            StringBuilder result = new StringBuilder();

            for (char c : value.toCharArray()) {
                switch (c) {
                    case '"':
                        result.append("\\\"");
                        break;
                    case '\\':
                        result.append("\\\\");
                        break;
                    case '\n':
                        result.append("\\n");
                        break;
                    case '\r':
                        result.append("\\r");
                        break;
                    case '\t':
                        result.append("\\t");
                        break;
                    default:
                        if (c < 32) {
                            result.append('?');
                        } else {
                            result.append(c);
                        }
                }
            }

            return result.toString();
        }

        static String quote(String value) {
            return "\"" + escape(value) + "\"";
        }

        static String task(Task task) {
            return "{"
                + "\"id\":" + task.id() + ","
                + "\"title\":" + quote(task.title()) + ","
                + "\"description\":" + quote(task.description()) + ","
                + "\"status\":" + quote(
                    task.status().name().toLowerCase()
                        .replace("_", "_")
                ) + ","
                + "\"createdAt\":" + quote(task.createdAt().toString()) + ","
                + "\"updatedAt\":" + quote(task.updatedAt().toString())
                + "}";
        }

        static String tasks(List<Task> tasks) {
            List<String> serialized = tasks.stream()
                .map(Json::task)
                .toList();

            return "{\"count\":" + tasks.size()
                + ",\"data\":["
                + String.join(",", serialized)
                + "]}";
        }

        static String error(ApiException exception) {
            return "{"
                + "\"error\":" + quote(exception.code()) + ","
                + "\"message\":" + quote(exception.getMessage())
                + "}";
        }
    }

    // -----------------------------------------------------
    // Repository interface
    // -----------------------------------------------------

    interface TaskStore {

        Task create(String title, String description);

        List<Task> findAll();

        Task findById(int id);

        Task update(int id, Map<String, String> changes);

        void delete(int id);
    }

    // -----------------------------------------------------
    // Repository implementation
    // -----------------------------------------------------

    static final class InMemoryTaskStore implements TaskStore {

        private final ConcurrentHashMap<Integer, Task> tasks =
            new ConcurrentHashMap<>();

        private final AtomicInteger sequence =
            new AtomicInteger(1);

        @Override
        public Task create(
            String title,
            String description
        ) {
            int id = sequence.getAndIncrement();

            Instant now = Instant.now();

            Task task = new Task(
                id,
                title,
                description,
                TaskStatus.PENDING,
                now,
                now
            );

            tasks.put(id, task);

            return task;
        }

        @Override
        public List<Task> findAll() {
            List<Task> result = new ArrayList<>(
                tasks.values()
            );

            result.sort(
                (first, second) ->
                    Integer.compare(first.id(), second.id())
            );

            return Collections.unmodifiableList(result);
        }

        @Override
        public Task findById(int id) {
            Task task = tasks.get(id);

            if (task == null) {
                throw new ResourceNotFoundException(
                    "Task " + id + " does not exist"
                );
            }

            return task;
        }

        @Override
        public Task update(
            int id,
            Map<String, String> changes
        ) {
            return tasks.compute(id, (key, current) -> {

                if (current == null) {
                    throw new ResourceNotFoundException(
                        "Task " + id + " does not exist"
                    );
                }

                String title = changes.getOrDefault(
                    "title",
                    current.title()
                );

                String description = changes.getOrDefault(
                    "description",
                    current.description()
                );

                TaskStatus status = changes.containsKey("status")
                    ? parseStatus(changes.get("status"))
                    : current.status();

                return new Task(
                    current.id(),
                    title,
                    description,
                    status,
                    current.createdAt(),
                    Instant.now()
                );
            });
        }

        @Override
        public void delete(int id) {
            if (tasks.remove(id) == null) {
                throw new ResourceNotFoundException(
                    "Task " + id + " does not exist"
                );
            }
        }
    }

    // -----------------------------------------------------
    // Domain validation
    // -----------------------------------------------------

    static final class TaskValidator {

        private static final int MAX_TITLE = 150;
        private static final int MAX_DESCRIPTION = 2000;

        private TaskValidator() {}

        static String title(String value) {
            if (value == null) {
                throw new ValidationException(
                    "Title is required"
                );
            }

            String result = value.strip();

            if (result.isEmpty() || result.length() > MAX_TITLE) {
                throw new ValidationException(
                    "Title must contain 1 to 150 characters"
                );
            }

            return result;
        }

        static String description(String value) {
            if (value == null) {
                return "";
            }

            if (value.length() > MAX_DESCRIPTION) {
                throw new ValidationException(
                    "Description exceeds 2000 characters"
                );
            }

            return value.strip();
        }

        static Map<String, String> validateCreate(
            Map<String, String> input
        ) {
            for (String key : input.keySet()) {
                if (
                    !key.equals("title") &&
                    !key.equals("description")
                ) {
                    throw new ValidationException(
                        "Unsupported create field: " + key
                    );
                }
            }

            if (!input.containsKey("title")) {
                throw new ValidationException(
                    "Title is required"
                );
            }

            Map<String, String> result = new LinkedHashMap<>();

            result.put(
                "title",
                title(input.get("title"))
            );

            result.put(
                "description",
                description(input.get("description"))
            );

            return Collections.unmodifiableMap(result);
        }

        static Map<String, String> validateUpdate(
            Map<String, String> input
        ) {
            if (input.isEmpty()) {
                throw new ValidationException(
                    "At least one update field is required"
                );
            }

            Map<String, String> result = new LinkedHashMap<>();

            for (Map.Entry<String, String> field : input.entrySet()) {
                String key = field.getKey();
                String value = field.getValue();

                switch (key) {
                    case "title":
                        result.put(key, title(value));
                        break;

                    case "description":
                        result.put(key, description(value));
                        break;

                    case "status":
                        parseStatus(value);
                        result.put(key, value);
                        break;

                    default:
                        throw new ValidationException(
                            "Unsupported update field: " + key
                        );
                }
            }

            return Collections.unmodifiableMap(result);
        }
    }

    static TaskStatus parseStatus(String value) {
        try {
            return TaskStatus.valueOf(
                value.toUpperCase()
            );
        } catch (IllegalArgumentException | NullPointerException error) {
            throw new ValidationException(
                "Invalid task status"
            );
        }
    }

    // -----------------------------------------------------
    // Service layer
    // -----------------------------------------------------

    static final class TaskService {

        private final TaskStore store;

        TaskService(TaskStore store) {
            this.store = Objects.requireNonNull(store);
        }

        Task create(Map<String, String> input) {
            Map<String, String> data =
                TaskValidator.validateCreate(input);

            return store.create(
                data.get("title"),
                data.get("description")
            );
        }

        List<Task> list() {
            return store.findAll();
        }

        Task get(int id) {
            return store.findById(id);
        }

        Task update(
            int id,
            Map<String, String> input
        ) {
            Map<String, String> changes =
                TaskValidator.validateUpdate(input);

            return store.update(id, changes);
        }

        void delete(int id) {
            store.delete(id);
        }
    }

    // -----------------------------------------------------
    // HTTP request and response context
    // -----------------------------------------------------

    static final class RequestContext {

        final String method;
        final String path;
        final Map<String, String> headers;
        final Map<String, String> body;
        final Map<String, String> params = new LinkedHashMap<>();

        String requestId;

        RequestContext(
            String method,
            String path,
            Map<String, String> headers,
            Map<String, String> body
        ) {
            this.method = method;
            this.path = path;
            this.headers = Map.copyOf(headers);
            this.body = Map.copyOf(body);
        }
    }

    // -----------------------------------------------------
    // Controller
    // -----------------------------------------------------

    static final class TaskController {

        private final TaskService service;

        TaskController(TaskService service) {
            this.service = service;
        }

        ApiResult list() {
            return new ApiResult(
                200,
                Json.tasks(service.list())
            );
        }

        ApiResult get(int id) {
            return new ApiResult(
                200,
                "{\"data\":" + Json.task(service.get(id)) + "}"
            );
        }

        ApiResult create(Map<String, String> body) {
            Task task = service.create(body);

            return new ApiResult(
                201,
                "{\"data\":" + Json.task(task) + "}"
            );
        }

        ApiResult update(
            int id,
            Map<String, String> body
        ) {
            Task task = service.update(id, body);

            return new ApiResult(
                200,
                "{\"data\":" + Json.task(task) + "}"
            );
        }

        ApiResult delete(int id) {
            service.delete(id);

            return new ApiResult(
                200,
                "{\"message\":\"Task deleted successfully\"}"
            );
        }
    }

    // -----------------------------------------------------
    // Routing
    // -----------------------------------------------------

    interface RouteHandler {
        ApiResult execute(RequestContext context);
    }

    record Route(
        String method,
        Pattern pattern,
        List<String> parameterNames,
        RouteHandler handler
    ) {}

    static final class Router {

        private final List<Route> routes =
            new ArrayList<>();

        void register(
            String method,
            String path,
            RouteHandler handler
        ) {
            Matcher matcher = Pattern
                .compile("\\{([a-zA-Z_][a-zA-Z0-9_]*)\\}")
                .matcher(path);

            List<String> names = new ArrayList<>();

            StringBuilder regex = new StringBuilder();

            int position = 0;

            while (matcher.find()) {
                regex.append(
                    Pattern.quote(
                        path.substring(position, matcher.start())
                    )
                );

                names.add(matcher.group(1));

                regex.append("([^/]+)");

                position = matcher.end();
            }

            regex.append(
                Pattern.quote(path.substring(position))
            );

            routes.add(
                new Route(
                    method,
                    Pattern.compile("^" + regex + "$"),
                    List.copyOf(names),
                    handler
                )
            );
        }

        ApiResult dispatch(RequestContext context) {
            boolean methodMismatch = false;

            for (Route route : routes) {
                Matcher matcher = route.pattern()
                    .matcher(context.path);

                if (!matcher.matches()) {
                    continue;
                }

                if (!route.method().equals(context.method)) {
                    methodMismatch = true;
                    continue;
                }

                context.params.clear();

                for (int i = 0; i < route.parameterNames().size(); i++) {
                    String value = matcher.group(i + 1);

                    try {
                        value = URLDecoder.decode(
                            value,
                            StandardCharsets.UTF_8
                        );
                    } catch (IllegalArgumentException error) {
                        throw new ValidationException(
                            "Invalid route parameter"
                        );
                    }

                    context.params.put(
                        route.parameterNames().get(i),
                        value
                    );
                }

                return route.handler().execute(context);
            }

            if (methodMismatch) {
                throw new ApiException(
                    405,
                    "METHOD_NOT_ALLOWED",
                    "Method is not supported"
                );
            }

            throw new ResourceNotFoundException(
                "Route does not exist"
            );
        }
    }

    // -----------------------------------------------------
    // Middleware contract
    // -----------------------------------------------------

    interface Middleware {
        ApiResult apply(
            RequestContext context,
            java.util.function.Supplier<ApiResult> next
        );
    }

    static final class RequestIdMiddleware
        implements Middleware {

        @Override
        public ApiResult apply(
            RequestContext context,
            java.util.function.Supplier<ApiResult> next
        ) {
            context.requestId = UUID.randomUUID().toString();

            ApiResult result = next.get();

            return new ApiResult(
                result.status(),
                addRequestId(result.body(), context.requestId)
            );
        }

        private String addRequestId(
            String body,
            String requestId
        ) {
            if (!body.endsWith("}")) {
                return body;
            }

            return body.substring(0, body.length() - 1)
                + ",\"requestId\":"
                + Json.quote(requestId)
                + "}";
        }
    }

    static final class LoggingMiddleware
        implements Middleware {

        @Override
        public ApiResult apply(
            RequestContext context,
            java.util.function.Supplier<ApiResult> next
        ) {
            long start = System.nanoTime();

            try {
                ApiResult result = next.get();

                long elapsed =
                    (System.nanoTime() - start) / 1_000_000;

                System.out.printf(
                    "%s %s %d %dms%n",
                    context.method,
                    context.path,
                    result.status(),
                    elapsed
                );

                return result;

            } catch (RuntimeException error) {
                System.err.println(
                    "Request failed: " + error.getMessage()
                );

                throw error;
            }
        }
    }

    // -----------------------------------------------------
    // Application composition
    // -----------------------------------------------------

    static final class Application {

        private final TaskService service;
        private final TaskController controller;
        private final Router router = new Router();

        private final List<Middleware> middleware =
            List.of(
                new RequestIdMiddleware(),
                new LoggingMiddleware()
            );

        Application() {
            TaskStore store = new InMemoryTaskStore();

            service = new TaskService(store);

            controller = new TaskController(service);

            router.register(
                "GET",
                "/health",
                context -> new ApiResult(
                    200,
                    "{\"status\":\"healthy\",\"service\":\"task-api\"}"
                )
            );

            router.register(
                "GET",
                "/api/v1/tasks",
                context -> controller.list()
            );

            router.register(
                "POST",
                "/api/v1/tasks",
                context -> controller.create(context.body)
            );

            router.register(
                "GET",
                "/api/v1/tasks/{id}",
                context -> controller.get(
                    parseId(context.params.get("id"))
                )
            );

            router.register(
                "PATCH",
                "/api/v1/tasks/{id}",
                context -> controller.update(
                    parseId(context.params.get("id")),
                    context.body
                )
            );

            router.register(
                "DELETE",
                "/api/v1/tasks/{id}",
                context -> controller.delete(
                    parseId(context.params.get("id"))
                )
            );
        }

        private static int parseId(String value) {
            if (
                value == null ||
                !value.matches("[1-9][0-9]*")
            ) {
                throw new ValidationException(
                    "Invalid task ID"
                );
            }

            try {
                return Integer.parseInt(value);
            } catch (NumberFormatException error) {
                throw new ValidationException(
                    "Task ID exceeds supported range"
                );
            }
        }

        ApiResult handle(RequestContext context) {
            try {
                java.util.function.Supplier<ApiResult> endpoint =
                    () -> router.dispatch(context);

                for (
                    int i = middleware.size() - 1;
                    i >= 0;
                    i--
                ) {
                    Middleware current = middleware.get(i);

                    java.util.function.Supplier<ApiResult> previous =
                        endpoint;

                    endpoint = () -> current.apply(
                        context,
                        previous
                    );
                }

                return endpoint.get();

            } catch (ApiException error) {
                return new ApiResult(
                    error.status(),
                    Json.error(error)
                );

            } catch (Exception error) {
                System.err.println(error);

                return new ApiResult(
                    500,
                    "{\"error\":\"INTERNAL_ERROR\","
                        + "\"message\":\"Unexpected server error\"}"
                );
            }
        }
    }

    // -----------------------------------------------------
    // HTTP adapter
    // -----------------------------------------------------

    static final class HttpAdapter {

        private final Application application;

        HttpAdapter(Application application) {
            this.application = application;
        }

        void start() throws IOException {
            HttpServer server = HttpServer.create(
                new InetSocketAddress(HOST, PORT),
                128
            );

            server.createContext("/", this::handle);

            server.setExecutor(
                Executors.newFixedThreadPool(8)
            );

            Runtime.getRuntime().addShutdownHook(
                new Thread(server::stop)
            );

            server.start();

            System.out.println(
                "Task API running at http://"
                    + HOST + ":" + PORT
            );
        }

        private void handle(HttpExchange exchange)
            throws IOException {

            Map<String, String> headers = new LinkedHashMap<>();

            exchange.getRequestHeaders().forEach(
                (key, values) -> {
                    if (!values.isEmpty()) {
                        headers.put(key.toLowerCase(), values.get(0));
                    }
                }
            );

            Map<String, String> body;

            try {
                body = readBody(exchange);

            } catch (ApiException error) {
                send(
                    exchange,
                    new ApiResult(
                        error.status(),
                        Json.error(error)
                    )
                );
                return;
            }

            RequestContext context = new RequestContext(
                exchange.getRequestMethod(),
                exchange.getRequestURI().getPath(),
                headers,
                body
            );

            ApiResult result = application.handle(context);

            send(exchange, result);
        }

        private Map<String, String> readBody(
            HttpExchange exchange
        ) throws IOException {

            String method = exchange.getRequestMethod();

            if (
                !method.equals("POST") &&
                !method.equals("PATCH") &&
                !method.equals("PUT")
            ) {
                return Map.of();
            }

            String contentType = exchange
                .getRequestHeaders()
                .getFirst("Content-Type");

            if (
                contentType == null ||
                !contentType.toLowerCase().startsWith(
                    "application/json"
                )
            ) {
                throw new ApiException(
                    415,
                    "UNSUPPORTED_MEDIA_TYPE",
                    "Expected application/json"
                );
            }

            byte[] bytes;

            try (
                InputStream input = exchange.getRequestBody()
            ) {
                bytes = input.readNBytes(MAX_BODY_SIZE + 1);
            }

            if (bytes.length > MAX_BODY_SIZE) {
                throw new ApiException(
                    413,
                    "PAYLOAD_TOO_LARGE",
                    "Request body exceeds size limit"
                );
            }

            if (bytes.length == 0) {
                throw new ValidationException(
                    "Request body cannot be empty"
                );
            }

            String raw = new String(
                bytes,
                StandardCharsets.UTF_8
            );

            return parseFlatJson(raw);
        }

        /*
         * The adapter accepts flat JSON string properties.
         * Nested objects and arrays are rejected rather than
         * silently interpreted incorrectly.
         */
        private Map<String, String> parseFlatJson(
            String raw
        ) {
            String input = raw.strip();

            if (
                !input.startsWith("{") ||
                !input.endsWith("}")
            ) {
                throw new ApiException(
                    400,
                    "INVALID_JSON",
                    "Expected JSON object"
                );
            }

            Map<String, String> result = new LinkedHashMap<>();

            String content = input.substring(
                1,
                input.length() - 1
            ).strip();

            if (content.isEmpty()) {
                return result;
            }

            Pattern field = Pattern.compile(
                "\"([^\"\\\\]+)\"\\s*:\\s*\"((?:[^\"\\\\]|\\\\.)*)\""
            );

            Matcher matcher = field.matcher(content);

            int position = 0;

            while (matcher.find()) {
                String separator = content.substring(
                    position,
                    matcher.start()
                ).strip();

                if (
                    position == 0
                        ? !separator.isEmpty()
                        : !separator.equals(",")
                ) {
                    throw new ApiException(
                        400,
                        "INVALID_JSON",
                        "Malformed JSON object"
                    );
                }

                String key = matcher.group(1);
                String value = unescape(matcher.group(2));

                if (result.containsKey(key)) {
                    throw new ApiException(
                        400,
                        "INVALID_JSON",
                        "Duplicate JSON property"
                    );
                }

                result.put(key, value);

                position = matcher.end();
            }

            if (
                !content.substring(position).strip().isEmpty()
            ) {
                throw new ApiException(
                    400,
                    "INVALID_JSON",
                    "Unsupported JSON value or malformed input"
                );
            }

            if (
                result.size() !=
                    content.split(",").length
            ) {
                throw new ApiException(
                    400,
                    "INVALID_JSON",
                    "Malformed JSON object"
                );
            }

            return result;
        }

        private String unescape(String value) {
            StringBuilder output = new StringBuilder();

            for (int i = 0; i < value.length(); i++) {
                char current = value.charAt(i);

                if (current != '\\') {
                    output.append(current);
                    continue;
                }

                if (++i >= value.length()) {
                    throw new ApiException(
                        400,
                        "INVALID_JSON",
                        "Invalid escape sequence"
                    );
                }

                char escaped = value.charAt(i);

                switch (escaped) {
                    case '"':
                    case '\\':
                    case '/':
                        output.append(escaped);
                        break;
                    case 'n':
                        output.append('\n');
                        break;
                    case 'r':
                        output.append('\r');
                        break;
                    case 't':
                        output.append('\t');
                        break;
                    default:
                        throw new ApiException(
                            400,
                            "INVALID_JSON",
                            "Unsupported escape sequence"
                        );
                }
            }

            return output.toString();
        }

        private void send(
            HttpExchange exchange,
            ApiResult result
        ) throws IOException {

            byte[] data = result.body().getBytes(
                StandardCharsets.UTF_8
            );

            exchange.getResponseHeaders().set(
                "Content-Type",
                "application/json; charset=utf-8"
            );

            exchange.getResponseHeaders().set(
                "Cache-Control",
                "no-store"
            );

            exchange.getResponseHeaders().set(
                "X-Content-Type-Options",
                "nosniff"
            );

            exchange.sendResponseHeaders(
                result.status(),
                data.length
            );

            try (
                OutputStream output = exchange.getResponseBody()
            ) {
                output.write(data);
            }
        }
    }

    // -----------------------------------------------------
    // Integration tests
    // -----------------------------------------------------

    static void runTests() {

        Application app = new Application();

        ApiResult health = app.handle(
            new RequestContext(
                "GET",
                "/health",
                Map.of(),
                Map.of()
            )
        );

        assert health.status() == 200;

        ApiResult created = app.handle(
            new RequestContext(
                "POST",
                "/api/v1/tasks",
                Map.of(),
                Map.of(
                    "title", "Design service layer",
                    "description", "Separate business logic"
                )
            )
        );

        assert created.status() == 201;

        ApiResult listed = app.handle(
            new RequestContext(
                "GET",
                "/api/v1/tasks",
                Map.of(),
                Map.of()
            )
        );

        assert listed.status() == 200;
        assert listed.body().contains("\"count\":1");

        ApiResult updated = app.handle(
            new RequestContext(
                "PATCH",
                "/api/v1/tasks/1",
                Map.of(),
                Map.of("status", "completed")
            )
        );

        assert updated.status() == 200;
        assert updated.body().contains("completed");

        ApiResult invalid = app.handle(
            new RequestContext(
                "POST",
                "/api/v1/tasks",
                Map.of(),
                Map.of("title", "")
            )
        );

        assert invalid.status() == 400;

        ApiResult missing = app.handle(
            new RequestContext(
                "GET",
                "/api/v1/tasks/999",
                Map.of(),
                Map.of()
            )
        );

        assert missing.status() == 404;

        ApiResult deleted = app.handle(
            new RequestContext(
                "DELETE",
                "/api/v1/tasks/1",
                Map.of(),
                Map.of()
            )
        );

        assert deleted.status() == 200;

        System.out.println(
            "All Java 17 backend integration tests passed."
        );
    }

    // -----------------------------------------------------
    // Entry point
    // -----------------------------------------------------

    public static void main(String[] args)
        throws IOException {

        if (args.length > 0 && args[0].equals("--test")) {
            runTests();
            return;
        }

        Application application = new Application();

        HttpAdapter adapter = new HttpAdapter(application);

        adapter.start();
    }
}
