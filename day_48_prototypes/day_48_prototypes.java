import java.util.Collections;
import java.util.HashMap;
import java.util.IdentityHashMap;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;

/*
 * Enterprise configuration inheritance using explicit prototype delegation.
 *
 * Java class inheritance describes types and behavior. This model separately
 * implements JavaScript-inspired object delegation for runtime configuration.
 */
public class Main {

    static final class PrototypeNode {
        private final Map<String, String> ownProperties;
        private PrototypeNode prototype;

        PrototypeNode(Map<String, String> properties, PrototypeNode prototype) {
            this.ownProperties = new HashMap<>(
                Objects.requireNonNull(properties, "properties")
            );
            this.prototype = prototype;
        }

        synchronized void setOwn(String key, String value) {
            requireKey(key);
            ownProperties.put(key, Objects.requireNonNull(value, "value"));
        }

        synchronized boolean hasOwn(String key) {
            requireKey(key);
            return ownProperties.containsKey(key);
        }

        synchronized Optional<String> get(String key) {
            requireKey(key);

            Set<PrototypeNode> visited =
                Collections.newSetFromMap(new IdentityHashMap<>());

            PrototypeNode current = this;

            while (current != null) {
                if (!visited.add(current)) {
                    throw new IllegalStateException(
                        "Prototype cycle detected while resolving " + key
                    );
                }

                synchronized (current) {
                    if (current.ownProperties.containsKey(key)) {
                        return Optional.of(current.ownProperties.get(key));
                    }

                    current = current.prototype;
                }
            }

            return Optional.empty();
        }

        synchronized void setPrototype(PrototypeNode prototype) {
            this.prototype = prototype;
        }

        private static void requireKey(String key) {
            if (key == null || key.isBlank()) {
                throw new IllegalArgumentException(
                    "Property name must not be blank"
                );
            }
        }
    }

    enum Environment {
        DEVELOPMENT,
        STAGING,
        PRODUCTION
    }

    static final class ServiceConfiguration {
        private final String serviceName;
        private final Environment environment;
        private final PrototypeNode settings;

        ServiceConfiguration(
            String serviceName,
            Environment environment,
            PrototypeNode settings
        ) {
            if (serviceName == null || serviceName.isBlank()) {
                throw new IllegalArgumentException(
                    "Service name must not be blank"
                );
            }

            this.serviceName = serviceName;
            this.environment = Objects.requireNonNull(
                environment,
                "environment"
            );
            this.settings = Objects.requireNonNull(settings, "settings");
        }

        String serviceName() {
            return serviceName;
        }

        Environment environment() {
            return environment;
        }

        Optional<String> setting(String name) {
            return settings.get(name);
        }

        void override(String name, String value) {
            settings.setOwn(name, value);
        }

        boolean owns(String name) {
            return settings.hasOwn(name);
        }
    }

    static final class ConfigurationService {
        void validate(ServiceConfiguration configuration) {
            String endpoint = configuration.setting("endpoint")
                .orElseThrow(() -> new IllegalStateException(
                    "Endpoint is missing"
                ));

            if (!endpoint.startsWith("https://")) {
                throw new IllegalStateException(
                    "Production endpoint must use HTTPS"
                );
            }

            int timeout;
            try {
                timeout = Integer.parseInt(
                    configuration.setting("timeoutSeconds")
                        .orElseThrow(() -> new IllegalStateException(
                            "Timeout is missing"
                        ))
                );
            } catch (NumberFormatException error) {
                throw new IllegalStateException(
                    "Timeout must be an integer",
                    error
                );
            }

            if (timeout < 1 || timeout > 120) {
                throw new IllegalStateException(
                    "Timeout must be between 1 and 120 seconds"
                );
            }
        }

        void printEffectiveConfiguration(
            ServiceConfiguration configuration
        ) {
            System.out.println(
                configuration.serviceName() + " [" +
                configuration.environment() + "]"
            );

            for (String key : new String[] {
                "endpoint",
                "timeoutSeconds",
                "logLevel",
                "region"
            }) {
                System.out.println(
                    key + " = " +
                    configuration.setting(key).orElse("<missing>") +
                    " (own = " + configuration.owns(key) + ")"
                );
            }
        }
    }

    public static void main(String[] args) {
        PrototypeNode organizationDefaults = new PrototypeNode(
            Map.of(
                "region", "ap-south-1",
                "logLevel", "INFO",
                "timeoutSeconds", "30"
            ),
            null
        );

        PrototypeNode serviceDefaults = new PrototypeNode(
            Map.of(
                "endpoint", "https://api.internal.example",
                "logLevel", "WARN"
            ),
            organizationDefaults
        );

        PrototypeNode productionOverrides = new PrototypeNode(
            Map.of(
                "timeoutSeconds", "45"
            ),
            serviceDefaults
        );

        ServiceConfiguration payments = new ServiceConfiguration(
            "payments-api",
            Environment.PRODUCTION,
            productionOverrides
        );

        ConfigurationService service = new ConfigurationService();

        service.printEffectiveConfiguration(payments);
        service.validate(payments);
        System.out.println("Configuration validation passed.");

        // An own property shadows an inherited value without changing defaults.
        payments.override("logLevel", "ERROR");

        System.out.println(
            "Effective log level: " +
            payments.setting("logLevel").orElseThrow()
        );

        System.out.println(
            "Shared service default remains: " +
            serviceDefaults.get("logLevel").orElseThrow()
        );

        try {
            payments.override("endpoint", "http://insecure.internal");

            service.validate(payments);
        } catch (IllegalStateException error) {
            System.out.println(
                "Rejected configuration: " + error.getMessage()
            );
        }

        try {
            PrototypeNode first = new PrototypeNode(
                Map.of("name", "first"),
                null
            );

            PrototypeNode second = new PrototypeNode(
                Map.of("name", "second"),
                first
            );

            first.setPrototype(second);
            first.get("missing");
        } catch (IllegalStateException error) {
            System.out.println(
                "Prototype integrity failure: " + error.getMessage()
            );
        }
    }
}
