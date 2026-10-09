import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.stream.Collectors;

public class ArrayOperationsEnterprise {

    record Service(String name, String version, double latencyMs,
                   boolean healthy, int failedRequests) {
        Service {
            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException("Service name is required");
            }
            if (version == null || version.isBlank()) {
                throw new IllegalArgumentException("Version is required");
            }
            if (!Double.isFinite(latencyMs) || latencyMs < 0) {
                throw new IllegalArgumentException(
                    "Latency must be finite and non-negative"
                );
            }
            if (failedRequests < 0) {
                throw new IllegalArgumentException(
                    "Failed request count cannot be negative"
                );
            }
        }
    }

    record ServiceSummary(
        String name,
        String version,
        double latencyMs,
        boolean healthy
    ) {}

    record HealthReport(
        int serviceCount,
        int healthyCount,
        double averageLatencyMs,
        int totalFailures,
        List<String> slowServices,
        Optional<String> firstUnhealthy,
        boolean allHealthy,
        boolean hasCriticalLatency
    ) {
        HealthReport {
            slowServices = List.copyOf(slowServices);
            firstUnhealthy = Objects.requireNonNull(firstUnhealthy);
        }
    }

    static final class MonitoringService {
        private final List<Service> services;

        MonitoringService(List<Service> input) {
            Objects.requireNonNull(input, "Input list cannot be null");

            // Defensive copying prevents callers from changing the collection
            // after validation, though each Service record is already immutable.
            this.services = List.copyOf(input);
        }

        List<ServiceSummary> summaries() {
            return services.stream()
                .map(service -> new ServiceSummary(
                    service.name(),
                    service.version(),
                    service.latencyMs(),
                    service.healthy()
                ))
                .toList();
        }

        List<Service> slowServices(double thresholdMs) {
            if (!Double.isFinite(thresholdMs) || thresholdMs < 0) {
                throw new IllegalArgumentException(
                    "Threshold must be finite and non-negative"
                );
            }

            return services.stream()
                .filter(service -> service.latencyMs() > thresholdMs)
                .toList();
        }

        Optional<Service> firstUnhealthy() {
            return services.stream()
                .filter(service -> !service.healthy())
                .findFirst();
        }

        boolean anyCriticalLatency(double thresholdMs) {
            if (!Double.isFinite(thresholdMs) || thresholdMs < 0) {
                throw new IllegalArgumentException(
                    "Threshold must be finite and non-negative"
                );
            }

            return services.stream()
                .anyMatch(service -> service.latencyMs() >= thresholdMs);
        }

        HealthReport report() {
            int count = services.size();

            double totalLatency = services.stream()
                .mapToDouble(Service::latencyMs)
                .sum();

            int totalFailures = services.stream()
                .mapToInt(Service::failedRequests)
                .sum();

            long healthyCount = services.stream()
                .filter(Service::healthy)
                .count();

            List<String> slowNames = slowServices(100.0).stream()
                .map(Service::name)
                .toList();

            Optional<String> firstUnhealthyName = firstUnhealthy()
                .map(Service::name);

            // Empty streams return true for allMatch. The business policy
            // requires at least one service before claiming all are healthy.
            boolean allHealthy = !services.isEmpty()
                && services.stream().allMatch(Service::healthy);

            return new HealthReport(
                count,
                Math.toIntExact(healthyCount),
                count == 0 ? 0.0 : totalLatency / count,
                totalFailures,
                slowNames,
                firstUnhealthyName,
                allHealthy,
                anyCriticalLatency(150.0)
            );
        }

        List<String> distinctNames() {
            // LinkedHashSet preserves encounter order while removing duplicates.
            Set<String> names = services.stream()
                .map(Service::name)
                .collect(Collectors.toCollection(java.util.LinkedHashSet::new));

            return List.copyOf(names);
        }

        List<Service> sortedByLatency() {
            return services.stream()
                .sorted(Comparator.comparingDouble(Service::latencyMs))
                .toList();
        }
    }

    public static void main(String[] args) {
        List<Service> productionServices = List.of(
            new Service("gateway", "3.2.0", 45.5, true, 2),
            new Service("billing", "2.8.1", 135.0, true, 8),
            new Service("inventory", "1.9.4", 88.0, false, 0),
            new Service("search", "4.1.0", 172.5, true, 15),
            new Service("gateway", "3.2.0", 52.0, true, 1)
        );

        MonitoringService monitoring =
            new MonitoringService(productionServices);

        System.out.println("Service summaries:");
        monitoring.summaries().forEach(System.out::println);

        System.out.println("\nHealth report:");
        System.out.println(monitoring.report());

        System.out.println("\nServices sorted by latency:");
        monitoring.sortedByLatency().forEach(System.out::println);

        System.out.println("\nDistinct service names:");
        System.out.println(monitoring.distinctNames());

        System.out.println("\nEmpty input behavior:");
        System.out.println(new MonitoringService(new ArrayList<>()).report());

        System.out.println("\nValidation behavior:");
        try {
            new Service("gateway", "3.2.0", Double.NaN, true, 0);
        } catch (IllegalArgumentException exception) {
            System.out.println("Rejected: " + exception.getMessage());
        }

        System.out.println("\nInvalid threshold behavior:");
        try {
            monitoring.slowServices(-10.0);
        } catch (IllegalArgumentException exception) {
            System.out.println("Rejected: " + exception.getMessage());
        }
    }
}
