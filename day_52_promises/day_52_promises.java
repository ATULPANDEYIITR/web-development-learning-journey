import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

public class PromiseWorkflow {

    enum DeploymentState {
        VALIDATING,
        READY,
        DEPLOYING,
        SUCCEEDED,
        FAILED
    }

    record Deployment(String service, String environment, int version) {
        Deployment {
            if (service == null || service.isBlank()) {
                throw new IllegalArgumentException("service is required");
            }
            if (environment == null || environment.isBlank()) {
                throw new IllegalArgumentException("environment is required");
            }
            if (version <= 0) {
                throw new IllegalArgumentException("version must be positive");
            }
        }
    }

    record ServiceResult(
        String service,
        boolean successful,
        String value,
        Throwable error
    ) {
        static ServiceResult success(String service, String value) {
            return new ServiceResult(service, true, value, null);
        }

        static ServiceResult failure(String service, Throwable error) {
            return new ServiceResult(service, false, null, error);
        }
    }

    static final class DeploymentException extends RuntimeException {
        DeploymentException(String message) {
            super(message);
        }
    }

    static CompletableFuture<Deployment> validate(
        Deployment deployment,
        ExecutorService executor
    ) {
        return CompletableFuture.supplyAsync(() -> {
            if ("production".equalsIgnoreCase(deployment.environment())
                    && deployment.version() < 100) {
                throw new DeploymentException(
                    "production deployments require version 100 or newer"
                );
            }

            return deployment;
        }, executor);
    }

    static CompletableFuture<String> authorize(
        Deployment deployment,
        ExecutorService executor
    ) {
        return CompletableFuture.supplyAsync(() -> {
            if ("production".equalsIgnoreCase(deployment.environment())
                    && deployment.service().equals("experimental-service")) {
                throw new DeploymentException(
                    "experimental-service is not authorized for production"
                );
            }

            return "authorized:" + deployment.service();
        }, executor);
    }

    static CompletableFuture<String> deploy(
        Deployment deployment,
        ExecutorService executor
    ) {
        return CompletableFuture.supplyAsync(() -> {
            sleep(50);

            return "deployed "
                + deployment.service()
                + " v"
                + deployment.version()
                + " to "
                + deployment.environment();
        }, executor);
    }

    static CompletableFuture<String> chainedDeployment(
        Deployment deployment,
        ExecutorService executor
    ) {
        return validate(deployment, executor)
            .thenCompose(validated ->
                authorize(validated, executor)
                    .thenCompose(ignored -> deploy(validated, executor))
            )
            .exceptionally(error -> {
                Throwable cause = unwrap(error);
                return "deployment rejected: " + cause.getMessage();
            });
    }

    static CompletableFuture<String> service(
        String name,
        long delayMs,
        boolean fail,
        ExecutorService executor
    ) {
        return CompletableFuture.supplyAsync(() -> {
            sleep(delayMs);

            if (fail) {
                throw new CompletionException(
                    new DeploymentException(name + " failed")
                );
            }

            return name + " completed";
        }, executor);
    }

    static void demonstrateAll(ExecutorService executor) {
        CompletableFuture<String> database =
            service("database", 60, false, executor);

        CompletableFuture<String> cache =
            service("cache", 30, false, executor);

        CompletableFuture<String> queue =
            service("queue", 45, false, executor);

        CompletableFuture<Void> all =
            CompletableFuture.allOf(database, cache, queue);

        all.thenRun(() -> {
            System.out.println("all completed:");
            System.out.println(database.join());
            System.out.println(cache.join());
            System.out.println(queue.join());
        }).join();

        CompletableFuture<String> failingAll =
            CompletableFuture.allOf(
                service("database", 60, false, executor),
                service("audit", 20, true, executor),
                service("queue", 45, false, executor)
            );

        try {
            failingAll.join();
        } catch (CompletionException error) {
            System.out.println(
                "all rejection: " + unwrap(error).getMessage()
            );
        }
    }

    static void demonstrateRace(ExecutorService executor) {
        CompletableFuture<String> race =
            CompletableFuture.anyOf(
                service("primary", 100, false, executor),
                service("replica", 25, false, executor),
                service("fallback", 60, false, executor)
            ).thenApply(Object::toString);

        System.out.println("race result: " + race.join());

        try {
            CompletableFuture.anyOf(
                service("unhealthy-primary", 10, true, executor),
                service("slow-backup", 80, false, executor)
            ).join();
        } catch (CompletionException error) {
            // anyOf is race-like: the first completion can be exceptional.
            System.out.println(
                "race-like failure: " + unwrap(error).getMessage()
            );
        }
    }

    static void demonstrateAllSettled(ExecutorService executor) {
        List<CompletableFuture<String>> futures = List.of(
            service("metrics", 20, false, executor),
            service("audit", 35, true, executor),
            service("cache", 15, false, executor)
        );

        List<CompletableFuture<ServiceResult>> settled = futures.stream()
            .map(future ->
                future.thenApply(value ->
                    ServiceResult.success("operation", value)
                ).exceptionally(error ->
                    ServiceResult.failure("operation", unwrap(error))
                )
            )
            .toList();

        CompletableFuture.allOf(
            settled.toArray(CompletableFuture[]::new)
        ).join();

        settled.stream()
            .map(CompletableFuture::join)
            .forEach(result -> {
                if (result.successful()) {
                    System.out.println("fulfilled: " + result.value());
                } else {
                    System.out.println(
                        "rejected: " + result.error().getMessage()
                    );
                }
            });
    }

    static void demonstrateAny(ExecutorService executor) {
        CompletableFuture<String> firstSuccess =
            firstSuccessful(List.of(
                service("region-a", 50, true, executor),
                service("region-b", 30, false, executor),
                service("region-c", 40, true, executor)
            ));

        System.out.println("first successful result: " + firstSuccess.join());

        try {
            firstSuccessful(List.of(
                service("backup-a", 10, true, executor),
                service("backup-b", 20, true, executor)
            )).join();
        } catch (CompletionException error) {
            System.out.println(
                "all candidates failed: " + unwrap(error).getMessage()
            );
        }
    }

    static CompletableFuture<String> firstSuccessful(
        List<CompletableFuture<String>> futures
    ) {
        CompletableFuture<String> result = new CompletableFuture<>();
        List<Throwable> failures = new ArrayList<>();

        for (CompletableFuture<String> future : futures) {
            future.whenComplete((value, error) -> {
                if (error == null) {
                    result.complete(value);
                    return;
                }

                synchronized (failures) {
                    failures.add(unwrap(error));

                    if (failures.size() == futures.size()) {
                        result.completeExceptionally(
                            new DeploymentException(
                                "all candidates rejected: "
                                    + failures.stream()
                                        .map(Throwable::getMessage)
                                        .toList()
                            )
                        );
                    }
                }
            });
        }

        return result;
    }

    static Throwable unwrap(Throwable error) {
        Throwable current = error;

        while ((current instanceof CompletionException)
                && current.getCause() != null) {
            current = current.getCause();
        }

        return current;
    }

    static void sleep(long milliseconds) {
        try {
            Thread.sleep(Duration.ofMillis(milliseconds));
        } catch (InterruptedException error) {
            Thread.currentThread().interrupt();
            throw new CompletionException(error);
        }
    }

    public static void main(String[] args) {
        ExecutorService executor = Executors.newFixedThreadPool(6);

        try {
            Deployment development =
                new Deployment("billing-service", "development", 42);

            Deployment production =
                new Deployment("billing-service", "production", 120);

            Deployment invalidProduction =
                new Deployment("billing-service", "production", 12);

            System.out.println(
                "development: "
                    + chainedDeployment(development, executor).join()
            );

            System.out.println(
                "production: "
                    + chainedDeployment(production, executor).join()
            );

            System.out.println(
                "invalid production: "
                    + chainedDeployment(invalidProduction, executor).join()
            );

            demonstrateAll(executor);
            demonstrateRace(executor);
            demonstrateAllSettled(executor);
            demonstrateAny(executor);

        } finally {
            executor.shutdown();

            try {
                if (!executor.awaitTermination(5, TimeUnit.SECONDS)) {
                    executor.shutdownNow();
                }
            } catch (InterruptedException error) {
                Thread.currentThread().interrupt();
                executor.shutdownNow();
            }
        }
    }
}
