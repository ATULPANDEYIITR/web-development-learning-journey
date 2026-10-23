import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import java.util.function.Supplier;

public class AsyncWorkflow {

    enum Status {
        COMPLETED,
        FAILED,
        TIMED_OUT
    }

    record OperationResult(
        String operation,
        Status status,
        String value,
        String error
    ) {
        static OperationResult completed(String operation, String value) {
            return new OperationResult(
                operation,
                Status.COMPLETED,
                value,
                null
            );
        }

        static OperationResult failed(String operation, Throwable error) {
            return new OperationResult(
                operation,
                Status.FAILED,
                null,
                errorMessage(error)
            );
        }

        static OperationResult timedOut(String operation) {
            return new OperationResult(
                operation,
                Status.TIMED_OUT,
                null,
                "operation timed out"
            );
        }

        private static String errorMessage(Throwable error) {
            Throwable current = error;

            while (current.getCause() != null
                    && current instanceof CompletionException) {
                current = current.getCause();
            }

            return current.getMessage() == null
                ? current.getClass().getSimpleName()
                : current.getMessage();
        }
    }

    interface AsyncOperation {
        CompletableFuture<String> execute();
    }

    static final class RemoteService implements AsyncOperation {
        private final String name;
        private final Duration delay;
        private final boolean fail;
        private final ExecutorService executor;

        RemoteService(
            String name,
            Duration delay,
            boolean fail,
            ExecutorService executor
        ) {
            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException("service name is required");
            }
            if (delay.isNegative()) {
                throw new IllegalArgumentException("delay cannot be negative");
            }

            this.name = name;
            this.delay = delay;
            this.fail = fail;
            this.executor = executor;
        }

        @Override
        public CompletableFuture<String> execute() {
            return CompletableFuture.supplyAsync(() -> {
                try {
                    Thread.sleep(delay.toMillis());

                    if (fail) {
                        throw new IllegalStateException(
                            name + " dependency failed"
                        );
                    }

                    return name + " response";
                } catch (InterruptedException ex) {
                    Thread.currentThread().interrupt();
                    throw new CompletionException(
                        new IllegalStateException(
                            name + " interrupted",
                            ex
                        )
                    );
                }
            }, executor);
        }
    }

    static CompletableFuture<OperationResult> safelyExecute(
        String name,
        AsyncOperation operation
    ) {
        return operation.execute()
            .thenApply(value ->
                OperationResult.completed(name, value)
            )
            .exceptionally(error ->
                OperationResult.failed(name, error)
            );
    }

    static CompletableFuture<OperationResult> withTimeout(
        String name,
        AsyncOperation operation,
        Duration timeout
    ) {
        return operation.execute()
            .orTimeout(
                timeout.toMillis(),
                TimeUnit.MILLISECONDS
            )
            .thenApply(value ->
                OperationResult.completed(name, value)
            )
            .exceptionally(error -> {
                Throwable cause = error;

                while (cause instanceof CompletionException
                        && cause.getCause() != null) {
                    cause = cause.getCause();
                }

                if (cause instanceof TimeoutException) {
                    return OperationResult.timedOut(name);
                }

                return OperationResult.failed(name, cause);
            });
    }

    static <T> CompletableFuture<T> retry(
        Supplier<CompletableFuture<T>> operation,
        int attempts,
        Duration delay
    ) {
        if (attempts < 1) {
            throw new IllegalArgumentException(
                "attempts must be at least one"
            );
        }

        if (delay.isNegative()) {
            throw new IllegalArgumentException(
                "retry delay cannot be negative"
            );
        }

        return retryInternal(operation, attempts, delay);
    }

    private static <T> CompletableFuture<T> retryInternal(
        Supplier<CompletableFuture<T>> operation,
        int remaining,
        Duration delay
    ) {
        return operation.get().handle((value, error) -> {
            if (error == null) {
                return CompletableFuture.completedFuture(value);
            }

            if (remaining == 1) {
                return CompletableFuture.<T>failedFuture(error);
            }

            return CompletableFuture
                .delayedExecutor(
                    delay.toMillis(),
                    TimeUnit.MILLISECONDS
                )
                .supplyAsync(
                    () -> null
                )
                .thenCompose(ignored ->
                    retryInternal(
                        operation,
                        remaining - 1,
                        delay.multipliedBy(2)
                    )
                );
        }).thenCompose(future -> future);
    }

    static CompletableFuture<List<OperationResult>> runParallel(
        List<AsyncOperationEntry> entries
    ) {
        List<CompletableFuture<OperationResult>> futures =
            entries.stream()
                .map(entry ->
                    safelyExecute(entry.name(), entry.operation())
                )
                .toList();

        return CompletableFuture.allOf(
            futures.toArray(CompletableFuture[]::new)
        ).thenApply(ignored ->
            futures.stream()
                .map(CompletableFuture::join)
                .toList()
        );
    }

    record AsyncOperationEntry(
        String name,
        AsyncOperation operation
    ) {}

    public static void main(String[] args)
        throws InterruptedException {

        ExecutorService executor =
            Executors.newFixedThreadPool(3);

        try {
            List<AsyncOperationEntry> operations = List.of(
                new AsyncOperationEntry(
                    "database",
                    new RemoteService(
                        "database",
                        Duration.ofMillis(150),
                        false,
                        executor
                    )
                ),
                new AsyncOperationEntry(
                    "payments",
                    new RemoteService(
                        "payments",
                        Duration.ofMillis(100),
                        true,
                        executor
                    )
                ),
                new AsyncOperationEntry(
                    "inventory",
                    new RemoteService(
                        "inventory",
                        Duration.ofMillis(120),
                        false,
                        executor
                    )
                )
            );

            System.out.println("Parallel operations:");

            runParallel(operations)
                .thenAccept(results ->
                    results.forEach(System.out::println)
                )
                .join();

            System.out.println("\nTimeout:");

            withTimeout(
                "slow-service",
                new RemoteService(
                    "slow-service",
                    Duration.ofMillis(300),
                    false,
                    executor
                ),
                Duration.ofMillis(50)
            ).thenAccept(System.out::println).join();

            System.out.println("\nRetry:");

            int[] attempts = {0};

            String retryResult = retry(
                () -> CompletableFuture.supplyAsync(() -> {
                    attempts[0]++;

                    if (attempts[0] < 3) {
                        throw new IllegalStateException(
                            "temporary dependency failure"
                        );
                    }

                    return "succeeded on attempt " + attempts[0];
                }, executor),
                3,
                Duration.ofMillis(50)
            ).join();

            System.out.println(retryResult);

        } finally {
            executor.shutdown();

            if (!executor.awaitTermination(2, TimeUnit.SECONDS)) {
                executor.shutdownNow();
            }
        }
    }
}
