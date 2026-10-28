import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpHeaders;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionException;

public class HttpApiEnterpriseDemo {

    enum Method {
        GET, POST, PUT, PATCH, DELETE
    }

    enum LifecycleState {
        CREATED, VALIDATED, SENT, RECEIVED, FAILED
    }

    enum Decision {
        ACCEPT,
        REJECT
    }

    record ApiRequest(
            Method method,
            URI uri,
            Map<String, String> headers,
            Optional<String> jsonBody
    ) {
        ApiRequest {
            Objects.requireNonNull(method);
            Objects.requireNonNull(uri);
            Objects.requireNonNull(headers);
            Objects.requireNonNull(jsonBody);
        }

        void validate() {
            String scheme = uri.getScheme();

            if (!"http".equalsIgnoreCase(scheme)
                    && !"https".equalsIgnoreCase(scheme)) {
                throw new ValidationException(
                        "Only HTTP and HTTPS URLs are supported"
                );
            }

            if (uri.getHost() == null || uri.getHost().isBlank()) {
                throw new ValidationException("URL must contain a host");
            }

            for (Map.Entry<String, String> entry : headers.entrySet()) {
                if (entry.getKey().isBlank()
                        || entry.getKey().contains("\r")
                        || entry.getKey().contains("\n")
                        || entry.getValue().contains("\r")
                        || entry.getValue().contains("\n")) {
                    throw new ValidationException(
                            "Invalid HTTP header"
                    );
                }
            }

            if ((method == Method.GET || method == Method.DELETE)
                    && jsonBody.isPresent()) {
                throw new ValidationException(
                        method + " cannot carry this JSON body"
                );
            }
        }
    }

    record ApiResult(
            int statusCode,
            String reason,
            HttpHeaders headers,
            String body,
            long durationMillis,
            LifecycleState state
    ) {
        boolean successful() {
            return statusCode >= 200 && statusCode < 300;
        }

        boolean retryable() {
            return switch (statusCode) {
                case 408, 429, 500, 502, 503, 504 -> true;
                default -> false;
            };
        }
    }

    interface ResponsePolicy {
        Decision evaluate(ApiResult result);
    }

    static final class SuccessPolicy implements ResponsePolicy {
        @Override
        public Decision evaluate(ApiResult result) {
            return result.successful()
                    ? Decision.ACCEPT
                    : Decision.REJECT;
        }
    }

    static final class ValidationException
            extends RuntimeException {
        ValidationException(String message) {
            super(message);
        }
    }

    static final class ApiException extends RuntimeException {
        ApiException(String message) {
            super(message);
        }

        ApiException(String message, Throwable cause) {
            super(message, cause);
        }
    }

    static final class EnterpriseApiClient {
        private final HttpClient client;
        private final Duration timeout;
        private final int maxRetries;
        private final ResponsePolicy policy;

        EnterpriseApiClient(
                Duration timeout,
                int maxRetries,
                ResponsePolicy policy
        ) {
            if (timeout.isNegative() || timeout.isZero()) {
                throw new IllegalArgumentException(
                        "Timeout must be positive"
                );
            }

            if (maxRetries < 0) {
                throw new IllegalArgumentException(
                        "maxRetries cannot be negative"
                );
            }

            this.client = HttpClient.newBuilder()
                    .connectTimeout(timeout)
                    .build();

            this.timeout = timeout;
            this.maxRetries = maxRetries;
            this.policy = Objects.requireNonNull(policy);
        }

        CompletableFuture<ApiResult> execute(ApiRequest request) {
            request.validate();

            HttpRequest.Builder builder = HttpRequest.newBuilder()
                    .uri(request.uri())
                    .timeout(timeout);

            request.headers().forEach(builder::header);

            HttpRequest.BodyPublisher bodyPublisher =
                    request.jsonBody()
                            .map(HttpRequest.BodyPublishers::ofString)
                            .orElseGet(
                                    HttpRequest.BodyPublishers::noBody
                            );

            builder.method(
                    request.method().name(),
                    bodyPublisher
            );

            HttpRequest httpRequest = builder.build();

            return sendWithRetry(httpRequest, 0);
        }

        private CompletableFuture<ApiResult> sendWithRetry(
                HttpRequest request,
                int attempt
        ) {
            long started = System.nanoTime();

            return client
                    .sendAsync(
                            request,
                            HttpResponse.BodyHandlers.ofString()
                    )
                    .handle((response, error) -> {
                        if (error != null) {
                            throw new CompletionException(
                                    new ApiException(
                                            "HTTP transport failed",
                                            error
                                    )
                            );
                        }

                        long duration =
                                (System.nanoTime() - started)
                                        / 1_000_000;

                        return new ApiResult(
                                response.statusCode(),
                                reason(response.statusCode()),
                                response.headers(),
                                response.body(),
                                duration,
                                LifecycleState.RECEIVED
                        );
                    })
                    .thenCompose(result -> {
                        if (result.retryable()
                                && attempt < maxRetries) {
                            long delay =
                                    Math.min(
                                            100L * (1L << attempt),
                                            1000L
                                    );

                            return CompletableFuture
                                    .delayedExecutor(
                                            delay,
                                            java.util.concurrent.TimeUnit.MILLISECONDS
                                    )
                                    .supplyAsync(() -> null)
                                    .thenCompose(
                                            ignored ->
                                                    sendWithRetry(
                                                            request,
                                                            attempt + 1
                                                    )
                                    );
                        }

                        return CompletableFuture.completedFuture(
                                result
                        );
                    });
        }

        ApiResult executeAndValidate(ApiRequest request) {
            ApiResult result = execute(request).join();

            if (policy.evaluate(result) == Decision.REJECT) {
                throw new ApiException(
                        "HTTP request rejected: "
                                + result.statusCode()
                                + " "
                                + result.reason()
                );
            }

            return result;
        }

        private static String reason(int status) {
            return switch (status) {
                case 200 -> "OK";
                case 201 -> "Created";
                case 204 -> "No Content";
                case 400 -> "Bad Request";
                case 404 -> "Not Found";
                case 409 -> "Conflict";
                case 422 -> "Unprocessable Entity";
                case 500 -> "Internal Server Error";
                case 503 -> "Service Unavailable";
                default -> "HTTP Status";
            };
        }
    }

    private static URI uri(String value) {
        try {
            return URI.create(value);
        } catch (IllegalArgumentException error) {
            throw new ValidationException("Invalid URI: " + value);
        }
    }

    private static void printResult(
            String operation,
            ApiResult result
    ) {
        System.out.printf(
                "%s -> HTTP %d %s (%d ms)%n",
                operation,
                result.statusCode(),
                result.reason(),
                result.durationMillis()
        );

        if (!result.body().isBlank()) {
            System.out.println("Body: " + result.body());
        }
    }

    public static void main(String[] args) {
        EnterpriseApiClient api = new EnterpriseApiClient(
                Duration.ofSeconds(3),
                2,
                new SuccessPolicy()
        );

        ApiRequest health = new ApiRequest(
                Method.GET,
                uri("https://example.com/health"),
                Map.of(
                        "Accept",
                        "application/json",
                        "User-Agent",
                        "EnterpriseHttpClient/1.0"
                ),
                Optional.empty()
        );

        /*
         * The example below uses a public endpoint only to illustrate
         * request construction. Runtime environments may restrict network
         * access, so the failure path is intentionally handled.
         */
        try {
            ApiResult result = api.executeAndValidate(health);
            printResult("GET /health", result);
        } catch (CompletionException | ApiException error) {
            System.out.println(
                    "Network example failed safely: "
                            + rootMessage(error)
            );
        }

        ApiRequest invalidHeader = new ApiRequest(
                Method.GET,
                uri("https://example.com/data"),
                Map.of(
                        "X-Request-ID",
                        "safe\r\nInjected: true"
                ),
                Optional.empty()
        );

        try {
            api.executeAndValidate(invalidHeader);
        } catch (ValidationException error) {
            System.out.println(
                    "Header validation blocked request: "
                            + error.getMessage()
            );
        }

        ApiRequest invalidBodyMethod = new ApiRequest(
                Method.GET,
                uri("https://example.com/data"),
                Map.of("Accept", "application/json"),
                Optional.of("{\"name\":\"Priya\"}")
        );

        try {
            api.executeAndValidate(invalidBodyMethod);
        } catch (ValidationException error) {
            System.out.println(
                    "Method validation blocked request: "
                            + error.getMessage()
            );
        }
    }

    private static String rootMessage(Throwable error) {
        Throwable current = error;

        while (current.getCause() != null) {
            current = current.getCause();
        }

        return current.getMessage() == null
                ? current.getClass().getSimpleName()
                : current.getMessage();
    }
}
