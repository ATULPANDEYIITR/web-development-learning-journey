import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Predicate;
import java.util.function.Supplier;

/*
 * Enterprise API-powered operational dashboard.
 *
 * Java 17.
 *
 * Demonstrates:
 * - Immutable domain records
 * - Asynchronous API aggregation with CompletableFuture
 * - Independent resource caches
 * - Retry and stale-data policies
 * - Explicit dashboard state transitions
 * - Domain validation
 * - Concurrent API access
 *
 * Compile and run:
 * javac DashboardApplication.java
 * java DashboardApplication
 */

public class DashboardApplication {

    enum DashboardPhase {
        IDLE,
        LOADING,
        READY,
        DEGRADED,
        FAILED
    }

    enum ServiceStatus {
        OPERATIONAL,
        DEGRADED,
        DOWN
    }

    enum IncidentSeverity {
        LOW,
        MEDIUM,
        HIGH,
        CRITICAL
    }

    enum IncidentStatus {
        OPEN,
        INVESTIGATING,
        RESOLVED
    }

    record MetricPoint(
        String serviceId,
        String name,
        double value,
        String unit,
        Instant observedAt
    ) {
        MetricPoint {
            requireText(serviceId, "serviceId");
            requireText(name, "name");
            requireText(unit, "unit");
            Objects.requireNonNull(observedAt, "observedAt");

            if (!Double.isFinite(value) || value < 0) {
                throw new IllegalArgumentException(
                    "Metric value must be finite and non-negative."
                );
            }

            if (observedAt.isAfter(Instant.now().plus(Duration.ofMinutes(5)))) {
                throw new IllegalArgumentException(
                    "Metric timestamp is in the future."
                );
            }
        }
    }

    record ServiceRecord(
        String id,
        String name,
        ServiceStatus status,
        String region
    ) {
        ServiceRecord {
            requireText(id, "service id");
            requireText(name, "service name");
            requireText(region, "service region");
            Objects.requireNonNull(status, "status");
        }
    }

    record IncidentRecord(
        String id,
        String serviceId,
        IncidentSeverity severity,
        IncidentStatus status,
        String title,
        Instant openedAt
    ) {
        IncidentRecord {
            requireText(id, "incident id");
            requireText(serviceId, "incident serviceId");
            requireText(title, "incident title");

            Objects.requireNonNull(severity, "severity");
            Objects.requireNonNull(status, "status");
            Objects.requireNonNull(openedAt, "openedAt");

            if (openedAt.isAfter(Instant.now().plus(Duration.ofMinutes(5)))) {
                throw new IllegalArgumentException(
                    "Incident timestamp is in the future."
                );
            }
        }
    }

    record ResourceResult<T>(
        List<T> rows,
        boolean stale,
        String error
    ) {
        ResourceResult {
            rows = List.copyOf(rows);
            error = error == null ? "" : error;
        }
    }

    record DashboardPolicy(
        int maxAttempts,
        long initialBackoffMillis,
        Duration cacheTtl
    ) {
        DashboardPolicy {
            if (maxAttempts < 1) {
                throw new IllegalArgumentException(
                    "maxAttempts must be positive."
                );
            }
            if (initialBackoffMillis < 0) {
                throw new IllegalArgumentException(
                    "Backoff cannot be negative."
                );
            }
            Objects.requireNonNull(cacheTtl, "cacheTtl");

            if (cacheTtl.isNegative()) {
                throw new IllegalArgumentException(
                    "Cache TTL cannot be negative."
                );
            }
        }
    }

    record DashboardSnapshot(
        DashboardPhase phase,
        List<MetricPoint> metrics,
        List<ServiceRecord> services,
        List<IncidentRecord> incidents,
        List<String> staleResources,
        List<String> errors,
        Instant updatedAt
    ) {
        DashboardSnapshot {
            Objects.requireNonNull(phase, "phase");
            metrics = List.copyOf(metrics);
            services = List.copyOf(services);
            incidents = List.copyOf(incidents);
            staleResources = List.copyOf(staleResources);
            errors = List.copyOf(errors);
            Objects.requireNonNull(updatedAt, "updatedAt");
        }
    }

    record DashboardSummary(
        int totalServices,
        int operationalServices,
        int degradedServices,
        int unavailableServices,
        long openIncidents,
        double operationalPercentage,
        Double averageErrorRate
    ) {}

    interface DashboardApi {
        List<MetricPoint> fetchMetrics();

        List<ServiceRecord> fetchServices();

        List<IncidentRecord> fetchIncidents();
    }

    static class ApiException extends RuntimeException {
        ApiException(String message) {
            super(message);
        }
    }

    static class MockDashboardApi implements DashboardApi {
        private final AtomicInteger incidentFailures = new AtomicInteger();

        @Override
        public List<MetricPoint> fetchMetrics() {
            Instant now = Instant.now();

            return List.of(
                new MetricPoint(
                    "payments", "latency", 145.2, "ms",
                    now.minusSeconds(12)
                ),
                new MetricPoint(
                    "payments", "error_rate", 0.8, "%",
                    now.minusSeconds(12)
                ),
                new MetricPoint(
                    "identity", "latency", 88.4, "ms",
                    now.minusSeconds(8)
                ),
                new MetricPoint(
                    "identity", "error_rate", 0.2, "%",
                    now.minusSeconds(8)
                ),
                new MetricPoint(
                    "notifications", "latency", 420.0, "ms",
                    now.minusSeconds(20)
                )
            );
        }

        @Override
        public List<ServiceRecord> fetchServices() {
            return List.of(
                new ServiceRecord(
                    "payments",
                    "Payment Processing",
                    ServiceStatus.OPERATIONAL,
                    "ap-south-1"
                ),
                new ServiceRecord(
                    "identity",
                    "Identity Service",
                    ServiceStatus.OPERATIONAL,
                    "ap-south-1"
                ),
                new ServiceRecord(
                    "notifications",
                    "Notification Gateway",
                    ServiceStatus.DEGRADED,
                    "ap-south-1"
                )
            );
        }

        @Override
        public List<IncidentRecord> fetchIncidents() {
            int remaining = incidentFailures.get();

            while (remaining > 0) {
                if (incidentFailures.compareAndSet(remaining, remaining - 1)) {
                    throw new ApiException("Temporary incident API failure.");
                }
                remaining = incidentFailures.get();
            }

            Instant now = Instant.now();

            return List.of(
                new IncidentRecord(
                    "INC-2041",
                    "notifications",
                    IncidentSeverity.HIGH,
                    IncidentStatus.INVESTIGATING,
                    "Elevated notification latency",
                    now.minusSeconds(1800)
                ),
                new IncidentRecord(
                    "INC-2038",
                    "payments",
                    IncidentSeverity.LOW,
                    IncidentStatus.RESOLVED,
                    "Intermittent callback delay",
                    now.minusSeconds(7200)
                )
            );
        }

        void failNextIncidents(int count) {
            if (count < 0) {
                throw new IllegalArgumentException(
                    "Failure count cannot be negative."
                );
            }
            incidentFailures.set(count);
        }
    }

    /*
     * A typed cache owns one resource type. This avoids placing unrelated
     * API payloads into an untyped shared map and removes unsafe casts.
     */
    static final class ResourceCache<T> {
        private record CacheEntry<T>(
            List<T> rows,
            Instant fetchedAt
        ) {}

        private final String resourceName;
        private final Supplier<List<T>> fetcher;
        private final Predicate<List<T>> validator;
        private final DashboardPolicy policy;

        private volatile CacheEntry<T> lastKnownGood;

        ResourceCache(
            String resourceName,
            Supplier<List<T>> fetcher,
            Predicate<List<T>> validator,
            DashboardPolicy policy
        ) {
            this.resourceName = resourceName;
            this.fetcher = fetcher;
            this.validator = validator;
            this.policy = policy;
        }

        ResourceResult<T> load(boolean forceRefresh) {
            CacheEntry<T> cached = lastKnownGood;

            if (
                !forceRefresh &&
                cached != null &&
                Duration.between(
                    cached.fetchedAt(),
                    Instant.now()
                ).compareTo(policy.cacheTtl()) <= 0
            ) {
                return new ResourceResult<>(
                    cached.rows(),
                    false,
                    ""
                );
            }

            String lastError = "Unknown API failure";

            for (int attempt = 0; attempt < policy.maxAttempts(); attempt++) {
                try {
                    List<T> received = List.copyOf(fetcher.get());

                    if (!validator.test(received)) {
                        throw new ApiException(
                            resourceName + " failed validation."
                        );
                    }

                    // Only validated responses replace the stored cache.
                    lastKnownGood = new CacheEntry<>(
                        received,
                        Instant.now()
                    );

                    return new ResourceResult<>(
                        received,
                        false,
                        ""
                    );

                } catch (RuntimeException exception) {
                    lastError = exception.getMessage();

                    if (attempt + 1 < policy.maxAttempts()) {
                        long delay = policy.initialBackoffMillis()
                            * (1L << Math.min(attempt, 10));

                        try {
                            Thread.sleep(delay);
                        } catch (InterruptedException interrupted) {
                            Thread.currentThread().interrupt();

                            return staleOrFailed(
                                cached,
                                "Retry interrupted."
                            );
                        }
                    }
                }
            }

            return staleOrFailed(cached, lastError);
        }

        private ResourceResult<T> staleOrFailed(
            CacheEntry<T> cached,
            String error
        ) {
            if (cached != null) {
                return new ResourceResult<>(
                    cached.rows(),
                    true,
                    resourceName + ": " + error
                );
            }

            return new ResourceResult<>(
                List.of(),
                false,
                resourceName + ": " + error
            );
        }
    }

    static final class DashboardService implements AutoCloseable {
        private final DashboardApi api;
        private final DashboardPolicy policy;
        private final ExecutorService executor;

        private final ResourceCache<MetricPoint> metricsCache;
        private final ResourceCache<ServiceRecord> servicesCache;
        private final ResourceCache<IncidentRecord> incidentsCache;

        private volatile DashboardSnapshot currentSnapshot =
            new DashboardSnapshot(
                DashboardPhase.IDLE,
                List.of(),
                List.of(),
                List.of(),
                List.of(),
                List.of(),
                Instant.now()
            );

        DashboardService(
            DashboardApi api,
            DashboardPolicy policy
        ) {
            this.api = Objects.requireNonNull(api);
            this.policy = Objects.requireNonNull(policy);
            this.executor = Executors.newFixedThreadPool(3);

            this.metricsCache = new ResourceCache<>(
                "metrics",
                api::fetchMetrics,
                DashboardService::validMetrics,
                policy
            );

            this.servicesCache = new ResourceCache<>(
                "services",
                api::fetchServices,
                DashboardService::validServices,
                policy
            );

            this.incidentsCache = new ResourceCache<>(
                "incidents",
                api::fetchIncidents,
                DashboardService::validIncidents,
                policy
            );
        }

        DashboardSnapshot refresh(boolean forceRefresh) {
            currentSnapshot = new DashboardSnapshot(
                DashboardPhase.LOADING,
                currentSnapshot.metrics(),
                currentSnapshot.services(),
                currentSnapshot.incidents(),
                currentSnapshot.staleResources(),
                List.of(),
                Instant.now()
            );

            CompletableFuture<ResourceResult<MetricPoint>> metricsFuture =
                CompletableFuture.supplyAsync(
                    () -> metricsCache.load(forceRefresh),
                    executor
                );

            CompletableFuture<ResourceResult<ServiceRecord>> servicesFuture =
                CompletableFuture.supplyAsync(
                    () -> servicesCache.load(forceRefresh),
                    executor
                );

            CompletableFuture<ResourceResult<IncidentRecord>> incidentsFuture =
                CompletableFuture.supplyAsync(
                    () -> incidentsCache.load(forceRefresh),
                    executor
                );

            /*
             * Each task has a typed result. allOf forms a synchronization
             * barrier; join retrieves completed values without blocking
             * the API work itself.
             */
            CompletableFuture.allOf(
                metricsFuture,
                servicesFuture,
                incidentsFuture
            ).join();

            ResourceResult<MetricPoint> metrics = metricsFuture.join();
            ResourceResult<ServiceRecord> services = servicesFuture.join();
            ResourceResult<IncidentRecord> incidents = incidentsFuture.join();

            List<String> staleResources = new ArrayList<>();
            List<String> errors = new ArrayList<>();

            collectStatus("metrics", metrics, staleResources, errors);
            collectStatus("services", services, staleResources, errors);
            collectStatus("incidents", incidents, staleResources, errors);

            int successfulResources = 0;
            if (errors.stream().noneMatch(e -> e.startsWith("metrics:"))) {
                successfulResources++;
            }
            if (errors.stream().noneMatch(e -> e.startsWith("services:"))) {
                successfulResources++;
            }
            if (errors.stream().noneMatch(e -> e.startsWith("incidents:"))) {
                successfulResources++;
            }

            DashboardPhase phase;

            if (successfulResources == 0) {
                phase = DashboardPhase.FAILED;
            } else if (!errors.isEmpty() || !staleResources.isEmpty()) {
                phase = DashboardPhase.DEGRADED;
            } else {
                phase = DashboardPhase.READY;
            }

            currentSnapshot = new DashboardSnapshot(
                phase,
                metrics.rows(),
                services.rows(),
                incidents.rows(),
                staleResources,
                errors,
                Instant.now()
            );

            return currentSnapshot;
        }

        DashboardSummary summarize() {
            List<ServiceRecord> services = currentSnapshot.services();
            List<IncidentRecord> incidents = currentSnapshot.incidents();
            List<MetricPoint> metrics = currentSnapshot.metrics();

            int operational = 0;
            int degraded = 0;
            int unavailable = 0;

            for (ServiceRecord service : services) {
                switch (service.status()) {
                    case OPERATIONAL -> operational++;
                    case DEGRADED -> degraded++;
                    case DOWN -> unavailable++;
                }
            }

            long openIncidents = incidents.stream()
                .filter(incident ->
                    incident.status() != IncidentStatus.RESOLVED
                )
                .count();

            double percentage = services.isEmpty()
                ? 0.0
                : 100.0 * operational / services.size();

            List<Double> rates = metrics.stream()
                .filter(metric -> metric.name().equals("error_rate"))
                .map(MetricPoint::value)
                .toList();

            Double averageErrorRate = rates.isEmpty()
                ? null
                : rates.stream().mapToDouble(Double::doubleValue).average()
                    .orElse(0.0);

            return new DashboardSummary(
                services.size(),
                operational,
                degraded,
                unavailable,
                openIncidents,
                percentage,
                averageErrorRate
            );
        }

        DashboardSnapshot snapshot() {
            return currentSnapshot;
        }

        private static <T> void collectStatus(
            String resourceName,
            ResourceResult<T> result,
            List<String> stale,
            List<String> errors
        ) {
            if (result.stale()) {
                stale.add(resourceName);
            }

            if (!result.error().isBlank()) {
                errors.add(result.error());
            }
        }

        private static boolean validMetrics(List<MetricPoint> rows) {
            Set<String> keys = new HashSet<>();

            for (MetricPoint metric : rows) {
                String key = metric.serviceId() + ":" + metric.name();
                if (!keys.add(key)) {
                    return false;
                }
            }

            return true;
        }

        private static boolean validServices(List<ServiceRecord> rows) {
            Set<String> ids = new HashSet<>();

            for (ServiceRecord service : rows) {
                if (!ids.add(service.id())) {
                    return false;
                }
            }

            return true;
        }

        private static boolean validIncidents(List<IncidentRecord> rows) {
            Set<String> ids = new HashSet<>();

            for (IncidentRecord incident : rows) {
                if (!ids.add(incident.id())) {
                    return false;
                }
            }

            return true;
        }

        @Override
        public void close() {
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

    private static void requireText(String value, String field) {
        if (value == null || value.isBlank()) {
            throw new IllegalArgumentException(field + " cannot be empty.");
        }
    }

    private static void printDashboard(DashboardService dashboard) {
        DashboardSnapshot snapshot = dashboard.snapshot();
        DashboardSummary summary = dashboard.summarize();

        System.out.println("\nAPI OPERATIONS DASHBOARD");
        System.out.println("=".repeat(60));
        System.out.println("State: " + snapshot.phase());
        System.out.println("Updated: " + snapshot.updatedAt());
        System.out.println("Total services: " + summary.totalServices());
        System.out.println("Operational services: " + summary.operationalServices());
        System.out.println("Degraded services: " + summary.degradedServices());
        System.out.println("Unavailable services: " + summary.unavailableServices());
        System.out.printf(
            "Operational percentage: %.1f%%%n",
            summary.operationalPercentage()
        );
        System.out.println("Open incidents: " + summary.openIncidents());

        if (summary.averageErrorRate() != null) {
            System.out.printf(
                "Average error rate: %.2f%%%n",
                summary.averageErrorRate()
            );
        }

        System.out.println("\nServices");
        for (ServiceRecord service : snapshot.services()) {
            System.out.printf(
                "  %-26s %-12s %s%n",
                service.name(),
                service.status(),
                service.region()
            );
        }

        System.out.println("\nMetrics");
        for (MetricPoint metric : snapshot.metrics()) {
            System.out.printf(
                "  %-16s %-14s %.2f %s%n",
                metric.serviceId(),
                metric.name(),
                metric.value(),
                metric.unit()
            );
        }

        System.out.println("\nIncidents");
        for (IncidentRecord incident : snapshot.incidents()) {
            System.out.printf(
                "  %s | %-8s | %-14s | %s%n",
                incident.id(),
                incident.severity(),
                incident.status(),
                incident.title()
            );
        }

        if (!snapshot.staleResources().isEmpty()) {
            System.out.println("\nStale resources: " + snapshot.staleResources());
        }

        if (!snapshot.errors().isEmpty()) {
            System.out.println("Resource errors: " + snapshot.errors());
        }
    }

    public static void main(String[] args) {
        MockDashboardApi api = new MockDashboardApi();

        DashboardPolicy policy = new DashboardPolicy(
            3,
            20,
            Duration.ofSeconds(5)
        );

        try (DashboardService dashboard = new DashboardService(api, policy)) {
            // Initial transient failure is recovered by the retry policy.
            api.failNextIncidents(1);

            DashboardSnapshot first = dashboard.refresh(true);
            printDashboard(dashboard);

            if (first.phase() != DashboardPhase.READY) {
                throw new IllegalStateException(
                    "Expected a READY dashboard after retry."
                );
            }

            // A repeated failure uses the typed cache and marks its data stale.
            api.failNextIncidents(3);

            DashboardSnapshot second = dashboard.refresh(true);
            printDashboard(dashboard);

            if (second.phase() != DashboardPhase.DEGRADED) {
                throw new IllegalStateException(
                    "Expected a DEGRADED dashboard."
                );
            }

            if (!second.staleResources().contains("incidents")) {
                throw new IllegalStateException(
                    "Incident resource should be marked stale."
                );
            }
        }
    }
}
