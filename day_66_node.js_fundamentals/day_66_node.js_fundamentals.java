import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Collections;
import java.util.EnumSet;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.UUID;
import java.util.function.Predicate;
import java.util.stream.Collectors;

/*
 * Node.js Fundamentals
 *
 * Enterprise Node.js Runtime and Configuration Governance.
 *
 * Java 17 implementation covering:
 * - Runtime compatibility
 * - Application module dependencies
 * - Filesystem operations
 * - Environment configuration
 * - Deployment policies
 * - Startup validation
 * - Error management
 */

public class NodeFundamentals {

    enum EnvironmentMode {
        DEVELOPMENT,
        TEST,
        PRODUCTION
    }

    enum ValidationStatus {
        PASSED,
        WARNING,
        FAILED
    }

    enum ModuleType {
        BUILTIN,
        COMMONJS,
        ES_MODULE,
        THIRD_PARTY
    }

    record RuntimeVersion(int major, int minor, int patch)
            implements Comparable<RuntimeVersion> {

        public RuntimeVersion {
            if (major < 0 || minor < 0 || patch < 0) {
                throw new IllegalArgumentException(
                    "Invalid runtime version."
                );
            }
        }

        @Override
        public int compareTo(RuntimeVersion other) {
            int result = Integer.compare(major, other.major);

            if (result != 0) return result;

            result = Integer.compare(minor, other.minor);

            if (result != 0) return result;

            return Integer.compare(patch, other.patch);
        }

        public static RuntimeVersion parse(String version) {
            String normalized = version.startsWith("v")
                    ? version.substring(1)
                    : version;

            String[] parts = normalized.split("\\.");

            if (parts.length != 3) {
                throw new IllegalArgumentException(
                    "Version must use major.minor.patch."
                );
            }

            try {
                return new RuntimeVersion(
                    Integer.parseInt(parts[0]),
                    Integer.parseInt(parts[1]),
                    Integer.parseInt(parts[2])
                );
            } catch (NumberFormatException exception) {
                throw new IllegalArgumentException(
                    "Invalid runtime version.",
                    exception
                );
            }
        }
    }

    record ModuleDefinition(
        String name,
        String version,
        ModuleType type,
        Set<String> dependencies
    ) {
        public ModuleDefinition {
            Objects.requireNonNull(name);
            Objects.requireNonNull(version);
            Objects.requireNonNull(type);

            if (name.isBlank() || version.isBlank()) {
                throw new IllegalArgumentException(
                    "Module name and version are required."
                );
            }

            dependencies = Set.copyOf(dependencies);
        }
    }

    record ValidationResult(
        String category,
        String message,
        ValidationStatus status
    ) {}

    static class GovernanceException extends Exception {
        GovernanceException(String message) {
            super(message);
        }
    }

    static class EnvironmentConfiguration {

        private final Map<String, String> values;

        EnvironmentConfiguration(Map<String, String> values) {
            this.values = Map.copyOf(values);
        }

        String required(String key) throws GovernanceException {
            String value = values.get(key);

            if (value == null || value.isBlank()) {
                throw new GovernanceException(
                    "Missing environment variable: " + key
                );
            }

            return value.trim();
        }

        int integer(
            String key,
            int defaultValue,
            int minimum,
            int maximum
        ) throws GovernanceException {

            String raw = values.get(key);

            if (raw == null) {
                return defaultValue;
            }

            try {
                int value = Integer.parseInt(raw.trim());

                if (value < minimum || value > maximum) {
                    throw new GovernanceException(
                        key + " is outside the permitted range."
                    );
                }

                return value;

            } catch (NumberFormatException exception) {
                throw new GovernanceException(
                    key + " must be an integer."
                );
            }
        }

        EnvironmentMode mode() throws GovernanceException {
            try {
                return EnvironmentMode.valueOf(
                    values.getOrDefault(
                        "NODE_ENV",
                        "development"
                    ).toUpperCase()
                );
            } catch (IllegalArgumentException exception) {
                throw new GovernanceException(
                    "Unsupported NODE_ENV value."
                );
            }
        }

        List<ValidationResult> validate(
            Set<String> requiredKeys
        ) {
            return requiredKeys.stream()
                .map(key -> {
                    String value = values.get(key);

                    boolean valid =
                        value != null && !value.isBlank();

                    return new ValidationResult(
                        "ENVIRONMENT",
                        valid
                            ? key + " is configured."
                            : key + " is missing.",
                        valid
                            ? ValidationStatus.PASSED
                            : ValidationStatus.FAILED
                    );
                })
                .toList();
        }
    }

    static class ModuleResolver {

        private static final Set<String> BUILTIN_MODULES = Set.of(
            "fs",
            "path",
            "os",
            "http",
            "https",
            "events",
            "crypto",
            "util",
            "stream",
            "buffer",
            "url",
            "assert"
        );

        private final Map<String, ModuleDefinition> modules =
            new HashMap<>();

        void register(ModuleDefinition module) {
            if (modules.containsKey(module.name())
                    || BUILTIN_MODULES.contains(module.name())) {
                throw new IllegalArgumentException(
                    "Duplicate module: " + module.name()
                );
            }

            modules.put(module.name(), module);
        }

        void resolve(String moduleName)
                throws GovernanceException {

            if (BUILTIN_MODULES.contains(moduleName)) {
                return;
            }

            if (!modules.containsKey(moduleName)) {
                throw new GovernanceException(
                    "Cannot resolve module: " + moduleName
                );
            }
        }

        void validateGraph(String entryModule)
                throws GovernanceException {

            Set<String> visiting = new HashSet<>();
            Set<String> visited = new HashSet<>();

            visit(entryModule, visiting, visited);
        }

        private void visit(
            String name,
            Set<String> visiting,
            Set<String> visited
        ) throws GovernanceException {

            if (BUILTIN_MODULES.contains(name) ||
                    visited.contains(name)) {
                return;
            }

            if (visiting.contains(name)) {
                throw new GovernanceException(
                    "Circular module dependency: " + name
                );
            }

            ModuleDefinition module = modules.get(name);

            if (module == null) {
                throw new GovernanceException(
                    "Unresolved dependency: " + name
                );
            }

            visiting.add(name);

            for (String dependency : module.dependencies()) {
                visit(dependency, visiting, visited);
            }

            visiting.remove(name);
            visited.add(name);
        }

        List<String> registeredModules() {
            return modules.keySet()
                .stream()
                .sorted()
                .toList();
        }
    }

    static class ApplicationFileService {

        private final Path root;

        ApplicationFileService(Path root) throws IOException {
            Files.createDirectories(root);
            this.root = root.toRealPath();
        }

        private Path resolve(String relative)
                throws IOException, GovernanceException {

            Path requested = Paths.get(relative);

            if (requested.isAbsolute()) {
                throw new GovernanceException(
                    "Absolute paths are not permitted."
                );
            }

            Path target = root.resolve(requested).normalize();

            if (!target.startsWith(root)) {
                throw new GovernanceException(
                    "Filesystem path escapes application root."
                );
            }

            return target;
        }

        void write(String relative, String content)
                throws IOException, GovernanceException {

            Path target = resolve(relative);

            Files.createDirectories(target.getParent());

            Path temporary = target.resolveSibling(
                target.getFileName() + "." +
                UUID.randomUUID() + ".tmp"
            );

            try {
                Files.writeString(
                    temporary,
                    content,
                    StandardCharsets.UTF_8
                );

                try {
                    Files.move(
                        temporary,
                        target,
                        java.nio.file.StandardCopyOption.REPLACE_EXISTING,
                        java.nio.file.StandardCopyOption.ATOMIC_MOVE
                    );
                } catch (java.nio.file.AtomicMoveNotSupportedException exception) {
                    Files.move(
                        temporary,
                        target,
                        java.nio.file.StandardCopyOption.REPLACE_EXISTING
                    );
                }

            } finally {
                Files.deleteIfExists(temporary);
            }
        }

        String read(String relative)
                throws IOException, GovernanceException {

            Path target = resolve(relative);

            if (!Files.isRegularFile(target)) {
                throw new GovernanceException(
                    "Requested application file does not exist."
                );
            }

            return Files.readString(
                target,
                StandardCharsets.UTF_8
            );
        }

        List<String> listFiles() throws IOException {
            try (var paths = Files.walk(root)) {
                return paths
                    .filter(Files::isRegularFile)
                    .map(path -> root.relativize(path).toString())
                    .sorted()
                    .toList();
            }
        }
    }

    interface DeploymentPolicy {
        List<ValidationResult> evaluate(
            RuntimeVersion actual,
            RuntimeVersion required,
            EnvironmentConfiguration environment,
            ModuleResolver modules
        );
    }

    static class ProductionPolicy implements DeploymentPolicy {

        @Override
        public List<ValidationResult> evaluate(
            RuntimeVersion actual,
            RuntimeVersion required,
            EnvironmentConfiguration environment,
            ModuleResolver modules
        ) {
            List<ValidationResult> results = new ArrayList<>();

            boolean compatible = actual.compareTo(required) >= 0;

            results.add(new ValidationResult(
                "RUNTIME",
                "Node.js version compatibility.",
                compatible
                    ? ValidationStatus.PASSED
                    : ValidationStatus.FAILED
            ));

            results.addAll(environment.validate(Set.of(
                "NODE_ENV",
                "PORT",
                "DATABASE_URL"
            )));

            try {
                if (environment.mode() != EnvironmentMode.PRODUCTION) {
                    results.add(new ValidationResult(
                        "POLICY",
                        "Production deployment requires NODE_ENV=production.",
                        ValidationStatus.FAILED
                    ));
                } else {
                    results.add(new ValidationResult(
                        "POLICY",
                        "Production environment policy satisfied.",
                        ValidationStatus.PASSED
                    ));
                }
            } catch (GovernanceException exception) {
                results.add(new ValidationResult(
                    "POLICY",
                    exception.getMessage(),
                    ValidationStatus.FAILED
                ));
            }

            try {
                modules.validateGraph("inventory-api");

                results.add(new ValidationResult(
                    "MODULES",
                    "All application module dependencies resolved.",
                    ValidationStatus.PASSED
                ));

            } catch (GovernanceException exception) {
                results.add(new ValidationResult(
                    "MODULES",
                    exception.getMessage(),
                    ValidationStatus.FAILED
                ));
            }

            return List.copyOf(results);
        }
    }

    static class DeploymentService {

        private final DeploymentPolicy policy;

        DeploymentService(DeploymentPolicy policy) {
            this.policy = Objects.requireNonNull(policy);
        }

        boolean eligible(
            RuntimeVersion actual,
            RuntimeVersion required,
            EnvironmentConfiguration environment,
            ModuleResolver modules
        ) {
            List<ValidationResult> results = policy.evaluate(
                actual,
                required,
                environment,
                modules
            );

            results.forEach(result ->
                System.out.printf(
                    "%-7s [%s] %s%n",
                    result.status(),
                    result.category(),
                    result.message()
                )
            );

            return results.stream().noneMatch(
                result -> result.status() == ValidationStatus.FAILED
            );
        }
    }

    public static void main(String[] args) {

        try {
            System.out.println("NODE.JS ENTERPRISE RUNTIME GOVERNANCE");
            System.out.println("======================================");

            RuntimeVersion actual =
                RuntimeVersion.parse("22.11.0");

            RuntimeVersion required =
                RuntimeVersion.parse("18.0.0");

            System.out.println("\nRUNTIME INFORMATION");

            System.out.println("Java runtime: " +
                System.getProperty("java.version"));

            System.out.println("Operating system: " +
                System.getProperty("os.name"));

            System.out.println("Process ID: " +
                ProcessHandle.current().pid());

            System.out.println("Actual Node.js version: " +
                actual);

            System.out.println("Required Node.js version: " +
                required);

            Map<String, String> values = new HashMap<>();

            values.put("NODE_ENV", "production");
            values.put("PORT", "8080");
            values.put(
                "DATABASE_URL",
                "postgresql://localhost/inventory"
            );

            EnvironmentConfiguration environment =
                new EnvironmentConfiguration(values);

            System.out.println("\nAPPLICATION CONFIGURATION");

            System.out.println("Mode: " + environment.mode());
            System.out.println(
                "Port: " +
                environment.integer("PORT", 3000, 1, 65535)
            );

            System.out.println(
                "Database configuration: " +
                (values.containsKey("DATABASE_URL")
                    ? "Available"
                    : "Missing")
            );

            System.out.println("\nMODULE REGISTRY");

            ModuleResolver resolver = new ModuleResolver();

            resolver.register(new ModuleDefinition(
                "database",
                "2.0.0",
                ModuleType.THIRD_PARTY,
                Set.of("crypto", "events")
            ));

            resolver.register(new ModuleDefinition(
                "inventory-service",
                "1.0.0",
                ModuleType.COMMONJS,
                Set.of("database", "fs")
            ));

            resolver.register(new ModuleDefinition(
                "inventory-api",
                "1.0.0",
                ModuleType.ES_MODULE,
                Set.of("inventory-service", "http", "path")
            ));

            resolver.register(new ModuleDefinition(
                "logger",
                "1.0.0",
                ModuleType.COMMONJS,
                Set.of("fs")
            ));

            resolver.registeredModules().forEach(
                System.out::println
            );

            System.out.println("\nFILESYSTEM OPERATIONS");

            Path temporaryDirectory = Files.createTempDirectory(
                "node-enterprise-"
            );

            try {
                ApplicationFileService fileService =
                    new ApplicationFileService(temporaryDirectory);

                fileService.write(
                    "config/runtime.json",
                    "{\"mode\":\"production\",\"port\":8080}"
                );

                System.out.println(
                    "Configuration: " +
                    fileService.read("config/runtime.json")
                );

                System.out.println("Files:");

                fileService.listFiles().forEach(
                    System.out::println
                );

                try {
                    fileService.read("../../outside.json");
                } catch (GovernanceException exception) {
                    System.out.println(
                        "Security validation: " +
                        exception.getMessage()
                    );
                }

            } finally {
                try (var paths = Files.walk(temporaryDirectory)) {
                    paths.sorted(Collections.reverseOrder())
                        .forEach(path -> {
                            try {
                                Files.deleteIfExists(path);
                            } catch (IOException exception) {
                                System.err.println(
                                    "Cleanup failure: " +
                                    exception.getMessage()
                                );
                            }
                        });
                }
            }

            System.out.println("\nDEPLOYMENT POLICY");

            DeploymentService deployment = new DeploymentService(
                new ProductionPolicy()
            );

            boolean eligible = deployment.eligible(
                actual,
                required,
                environment,
                resolver
            );

            System.out.println(
                "\nDeployment status: " +
                (eligible ? "READY" : "BLOCKED")
            );

            System.out.println("\nINVALID CONFIGURATION TEST");

            try {
                environment.integer(
                    "PORT",
                    3000,
                    9000,
                    10000
                );
            } catch (GovernanceException exception) {
                System.out.println(exception.getMessage());
            }

            System.out.println("\nAPPLICATION COMPLETED");

        } catch (Exception exception) {
            System.err.println(
                "APPLICATION FAILURE: " +
                exception.getMessage()
            );

            System.exitCode = 1;
        }
    }
}
