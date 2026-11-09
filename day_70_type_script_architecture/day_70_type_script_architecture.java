import java.time.Instant;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Deque;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;

/**
 * TypeScript Architecture Enterprise Governance System.
 *
 * Models interface contracts, declaration modules, module dependencies,
 * compiler configuration, strict mode, architecture policies,
 * build ordering, and validation reports.
 *
 * Java version: 17
 * Dependencies: Java standard library.
 *
 * Compile:
 * javac TypeScriptArchitecture.java
 *
 * Execute:
 * java TypeScriptArchitecture
 */

public class TypeScriptArchitecture {

    enum ModuleKind {
        ES_MODULE,
        COMMON_JS,
        DECLARATION,
        AMBIENT
    }

    enum Severity {
        ERROR,
        WARNING,
        INFO
    }

    record Property(
        String name,
        String type,
        boolean optional,
        boolean readonly
    ) {
        Property {
            if (
                name == null || name.isBlank() ||
                type == null || type.isBlank()
            ) {
                throw new IllegalArgumentException(
                    "Property name and type are required."
                );
            }
        }
    }

    record Diagnostic(
        String code,
        Severity severity,
        String message,
        String location
    ) {}

    record ValidationReport(
        boolean valid,
        int moduleCount,
        List<Diagnostic> diagnostics,
        Instant checkedAt
    ) {
        ValidationReport {
            diagnostics = List.copyOf(diagnostics);
        }
    }

    static class ArchitectureException extends RuntimeException {
        ArchitectureException(String message) {
            super(message);
        }
    }

    static class ContractException extends ArchitectureException {
        ContractException(String message) {
            super(message);
        }
    }

    static class ConfigurationException
        extends ArchitectureException {

        ConfigurationException(String message) {
            super(message);
        }
    }

    record CompilerPolicy(
        boolean strict,
        boolean strictNullChecks,
        boolean noImplicitAny,
        boolean strictFunctionTypes,
        boolean strictPropertyInitialization,
        boolean noImplicitOverride,
        boolean noUnusedLocals,
        boolean noUnusedParameters,
        boolean noUncheckedIndexedAccess,
        boolean exactOptionalPropertyTypes
    ) {

        void validate() {
            if (
                strict &&
                (
                    !strictNullChecks ||
                    !noImplicitAny ||
                    !strictFunctionTypes ||
                    !strictPropertyInitialization
                )
            ) {
                throw new ConfigurationException(
                    "Strict mode contains disabled strict checks."
                );
            }
        }
    }

    record TypeScriptConfig(
        String target,
        String module,
        String moduleResolution,
        String rootDir,
        String outDir,
        CompilerPolicy policy,
        boolean declaration,
        boolean declarationMap,
        boolean sourceMap,
        Map<String, List<String>> paths,
        List<String> include,
        List<String> exclude
    ) {

        TypeScriptConfig {
            Objects.requireNonNull(policy);

            paths = Collections.unmodifiableMap(
                new LinkedHashMap<>(paths)
            );

            include = List.copyOf(include);
            exclude = List.copyOf(exclude);
        }

        void validate() {
            policy.validate();

            if (
                target == null || target.isBlank() ||
                module == null || module.isBlank()
            ) {
                throw new ConfigurationException(
                    "Target and module are mandatory."
                );
            }

            if (rootDir.equals(outDir)) {
                throw new ConfigurationException(
                    "Source and output directories must differ."
                );
            }

            if (include.isEmpty()) {
                throw new ConfigurationException(
                    "At least one source include pattern is required."
                );
            }

            for (Map.Entry<String, List<String>> entry :
                 paths.entrySet()) {

                if (
                    entry.getKey().isBlank() ||
                    entry.getValue().isEmpty()
                ) {
                    throw new ConfigurationException(
                        "Invalid module path alias."
                    );
                }
            }
        }
    }

    static class InterfaceDefinition {

        private final String name;
        private final List<String> parents;
        private final Map<String, Property> properties =
            new LinkedHashMap<>();

        InterfaceDefinition(
            String name,
            List<String> parents
        ) {
            if (name == null || name.isBlank()) {
                throw new ContractException(
                    "Interface name cannot be empty."
                );
            }

            this.name = name;
            this.parents = List.copyOf(parents);
        }

        void addProperty(Property property) {
            if (properties.putIfAbsent(
                property.name(),
                property
            ) != null) {
                throw new ContractException(
                    "Duplicate property: " + property.name()
                );
            }
        }

        String name() {
            return name;
        }

        List<String> parents() {
            return parents;
        }

        Map<String, Property> properties() {
            return Collections.unmodifiableMap(properties);
        }
    }

    static class InterfaceRegistry {

        private final Map<String, InterfaceDefinition> definitions =
            new LinkedHashMap<>();

        void register(InterfaceDefinition definition) {
            if (definitions.putIfAbsent(
                definition.name(),
                definition
            ) != null) {
                throw new ContractException(
                    "Duplicate interface: " + definition.name()
                );
            }
        }

        Map<String, Property> resolve(String name) {
            Map<String, Property> result = new LinkedHashMap<>();
            resolveRecursive(name, new HashSet<>(), result);
            return result;
        }

        private void resolveRecursive(
            String name,
            Set<String> visiting,
            Map<String, Property> result
        ) {
            InterfaceDefinition definition =
                definitions.get(name);

            if (definition == null) {
                throw new ContractException(
                    "Unknown interface: " + name
                );
            }

            if (!visiting.add(name)) {
                throw new ContractException(
                    "Circular interface inheritance: " + name
                );
            }

            for (String parent : definition.parents()) {
                resolveRecursive(parent, visiting, result);
            }

            for (Property property :
                 definition.properties().values()) {

                Property existing = result.get(property.name());

                if (
                    existing != null &&
                    !existing.type().equals(property.type())
                ) {
                    throw new ContractException(
                        "Conflicting inherited property: " +
                        property.name()
                    );
                }

                result.put(property.name(), property);
            }

            visiting.remove(name);
        }

        List<String> validateImplementation(
            String interfaceName,
            Map<String, Object> implementation
        ) {
            Map<String, Property> contract =
                resolve(interfaceName);

            List<String> errors = new ArrayList<>();

            for (Property property : contract.values()) {
                if (!implementation.containsKey(property.name())) {
                    if (!property.optional()) {
                        errors.add(
                            "Missing property: " + property.name()
                        );
                    }
                    continue;
                }

                if (
                    implementation.get(property.name()) == null &&
                    !property.optional()
                ) {
                    errors.add(
                        "Required property cannot be null: " +
                        property.name()
                    );
                }
            }

            return errors;
        }
    }

    record ModuleDefinition(
        String name,
        String filePath,
        ModuleKind kind,
        Set<String> exports,
        Set<String> imports,
        Set<String> interfaces,
        boolean entryPoint
    ) {
        ModuleDefinition {
            if (
                name == null || name.isBlank() ||
                filePath == null || filePath.isBlank()
            ) {
                throw new IllegalArgumentException(
                    "Module name and path are required."
                );
            }

            Objects.requireNonNull(kind);

            exports = Set.copyOf(exports);
            imports = Set.copyOf(imports);
            interfaces = Set.copyOf(interfaces);
        }
    }

    static class ModuleRegistry {

        private final Map<String, ModuleDefinition> modules =
            new LinkedHashMap<>();

        void register(ModuleDefinition module) {
            if (modules.putIfAbsent(
                module.name(),
                module
            ) != null) {
                throw new ArchitectureException(
                    "Duplicate module: " + module.name()
                );
            }
        }

        ModuleDefinition get(String name) {
            return modules.get(name);
        }

        List<ModuleDefinition> all() {
            return List.copyOf(modules.values());
        }

        void verifyExport(String moduleName, String symbol) {
            ModuleDefinition module = get(moduleName);

            if (module == null) {
                throw new ArchitectureException(
                    "Unknown module: " + moduleName
                );
            }

            if (!module.exports().contains(symbol)) {
                throw new ArchitectureException(
                    "Symbol is not exported: " + symbol
                );
            }
        }
    }

    static class DependencyService {

        private final ModuleRegistry modules;

        DependencyService(ModuleRegistry modules) {
            this.modules = modules;
        }

        List<String> buildOrder() {
            Map<String, Set<String>> graph = new LinkedHashMap<>();
            Map<String, Integer> indegree = new HashMap<>();

            for (ModuleDefinition module : modules.all()) {
                graph.put(module.name(), new LinkedHashSet<>());
                indegree.put(module.name(), 0);
            }

            for (ModuleDefinition module : modules.all()) {
                for (String dependency : module.imports()) {
                    if (!graph.containsKey(dependency)) {
                        throw new ArchitectureException(
                            "Unknown dependency: " + dependency
                        );
                    }

                    if (graph.get(module.name()).add(dependency)) {
                        indegree.merge(
                            dependency,
                            1,
                            Integer::sum
                        );
                    }
                }
            }

            Deque<String> queue = new ArrayDeque<>();

            for (Map.Entry<String, Integer> entry :
                 indegree.entrySet()) {

                if (entry.getValue() == 0) {
                    queue.add(entry.getKey());
                }
            }

            List<String> order = new ArrayList<>();

            while (!queue.isEmpty()) {
                String current = queue.removeFirst();
                order.add(current);

                for (String dependency : graph.get(current)) {
                    int updated =
                        indegree.merge(
                            dependency,
                            -1,
                            Integer::sum
                        );

                    if (updated == 0) {
                        queue.addLast(dependency);
                    }
                }
            }

            if (order.size() != graph.size()) {
                throw new ArchitectureException(
                    "Circular module dependency detected."
                );
            }

            return List.copyOf(order);
        }
    }

    static class ArchitectureService {

        private final TypeScriptConfig configuration;
        private final InterfaceRegistry interfaces;
        private final ModuleRegistry modules;
        private final DependencyService dependencies;

        ArchitectureService(
            TypeScriptConfig configuration,
            InterfaceRegistry interfaces,
            ModuleRegistry modules
        ) {
            this.configuration = configuration;
            this.interfaces = interfaces;
            this.modules = modules;
            this.dependencies = new DependencyService(modules);
        }

        ValidationReport validate() {
            List<Diagnostic> diagnostics = new ArrayList<>();

            try {
                configuration.validate();
            } catch (ConfigurationException exception) {
                diagnostics.add(new Diagnostic(
                    "CONFIG001",
                    Severity.ERROR,
                    exception.getMessage(),
                    "tsconfig.json"
                ));
            }

            for (ModuleDefinition module : modules.all()) {
                for (String dependency : module.imports()) {
                    if (modules.get(dependency) == null) {
                        diagnostics.add(new Diagnostic(
                            "MODULE001",
                            Severity.ERROR,
                            "Unknown imported module: " + dependency,
                            module.filePath()
                        ));
                    }
                }

                for (String interfaceName : module.interfaces()) {
                    try {
                        interfaces.resolve(interfaceName);
                    } catch (ContractException exception) {
                        diagnostics.add(new Diagnostic(
                            "TYPE001",
                            Severity.ERROR,
                            exception.getMessage(),
                            module.filePath()
                        ));
                    }
                }

                if (
                    module.kind() == ModuleKind.DECLARATION &&
                    module.exports().isEmpty()
                ) {
                    diagnostics.add(new Diagnostic(
                        "DECL001",
                        Severity.WARNING,
                        "Declaration module has no exports.",
                        module.filePath()
                    ));
                }
            }

            try {
                dependencies.buildOrder();
            } catch (ArchitectureException exception) {
                diagnostics.add(new Diagnostic(
                    "MODULE002",
                    Severity.ERROR,
                    exception.getMessage(),
                    ""
                ));
            }

            boolean valid = diagnostics.stream()
                .noneMatch(
                    diagnostic ->
                        diagnostic.severity() == Severity.ERROR
                );

            return new ValidationReport(
                valid,
                modules.all().size(),
                diagnostics,
                Instant.now()
            );
        }

        List<String> buildOrder() {
            return dependencies.buildOrder();
        }
    }

    private static TypeScriptConfig createConfiguration() {
        CompilerPolicy policy = new CompilerPolicy(
            true,
            true,
            true,
            true,
            true,
            true,
            true,
            true,
            true,
            true
        );

        Map<String, List<String>> paths = new LinkedHashMap<>();

        paths.put(
            "@domain/*",
            List.of("src/domain/*")
        );

        paths.put(
            "@services/*",
            List.of("src/services/*")
        );

        paths.put(
            "@infrastructure/*",
            List.of("src/infrastructure/*")
        );

        return new TypeScriptConfig(
            "ES2022",
            "NodeNext",
            "NodeNext",
            "src",
            "dist",
            policy,
            true,
            true,
            true,
            paths,
            List.of("src/**/*.ts"),
            List.of("node_modules", "dist")
        );
    }

    private static InterfaceRegistry createInterfaces() {
        InterfaceRegistry registry = new InterfaceRegistry();

        InterfaceDefinition entity =
            new InterfaceDefinition("Entity", List.of());

        entity.addProperty(
            new Property("id", "string", false, true)
        );

        InterfaceDefinition user =
            new InterfaceDefinition("User", List.of("Entity"));

        user.addProperty(
            new Property("email", "string", false, false)
        );

        user.addProperty(
            new Property("displayName", "string", false, false)
        );

        user.addProperty(
            new Property("phone", "string", true, false)
        );

        InterfaceDefinition repository =
            new InterfaceDefinition(
                "UserRepository",
                List.of()
            );

        repository.addProperty(
            new Property(
                "findById",
                "(id: string) => Promise<User | null>",
                false,
                false
            )
        );

        repository.addProperty(
            new Property(
                "save",
                "(user: User) => Promise<void>",
                false,
                false
            )
        );

        registry.register(entity);
        registry.register(user);
        registry.register(repository);

        return registry;
    }

    private static ModuleRegistry createModules() {
        ModuleRegistry registry = new ModuleRegistry();

        registry.register(new ModuleDefinition(
            "domain",
            "src/domain/user.ts",
            ModuleKind.ES_MODULE,
            Set.of("Entity", "User", "UserRepository"),
            Set.of(),
            Set.of("Entity", "User", "UserRepository"),
            false
        ));

        registry.register(new ModuleDefinition(
            "infrastructure",
            "src/infrastructure/user-repository.ts",
            ModuleKind.ES_MODULE,
            Set.of("PostgresUserRepository"),
            Set.of("domain"),
            Set.of("UserRepository"),
            false
        ));

        registry.register(new ModuleDefinition(
            "services",
            "src/services/user-service.ts",
            ModuleKind.ES_MODULE,
            Set.of("UserService"),
            Set.of("domain", "infrastructure"),
            Set.of("User"),
            false
        ));

        registry.register(new ModuleDefinition(
            "api",
            "src/api/server.ts",
            ModuleKind.ES_MODULE,
            Set.of("startServer"),
            Set.of("services"),
            Set.of(),
            true
        ));

        return registry;
    }

    private static void runTests() {
        InterfaceRegistry registry = new InterfaceRegistry();

        InterfaceDefinition base =
            new InterfaceDefinition("Base", List.of());

        base.addProperty(
            new Property("id", "string", false, false)
        );

        InterfaceDefinition child =
            new InterfaceDefinition("Child", List.of("Base"));

        child.addProperty(
            new Property("name", "string", false, false)
        );

        registry.register(base);
        registry.register(child);

        Map<String, Object> valid = Map.of(
            "id", "U-101",
            "name", "Developer"
        );

        if (!registry.validateImplementation("Child", valid).isEmpty()) {
            throw new ArchitectureException(
                "Interface compatibility test failed."
            );
        }

        Map<String, Object> invalid = Map.of(
            "id", "U-101"
        );

        if (
            registry.validateImplementation(
                "Child",
                invalid
            ).size() != 1
        ) {
            throw new ArchitectureException(
                "Missing property test failed."
            );
        }

        boolean rejected = false;

        try {
            new CompilerPolicy(
                true,
                false,
                true,
                true,
                true,
                true,
                true,
                true,
                true,
                true
            ).validate();
        } catch (ConfigurationException exception) {
            rejected = true;
        }

        if (!rejected) {
            throw new ArchitectureException(
                "Strict configuration validation failed."
            );
        }

        System.out.println(
            "All Java 17 architecture tests passed."
        );
    }

    public static void main(String[] args) {
        try {
            runTests();

            TypeScriptConfig configuration =
                createConfiguration();

            InterfaceRegistry interfaces =
                createInterfaces();

            ModuleRegistry modules =
                createModules();

            ArchitectureService service =
                new ArchitectureService(
                    configuration,
                    interfaces,
                    modules
                );

            ValidationReport report = service.validate();

            System.out.println("\nARCHITECTURE REPORT");
            System.out.println("-------------------");

            System.out.println("Valid: " + report.valid());
            System.out.println("Modules: " + report.moduleCount());
            System.out.println("Checked: " + report.checkedAt());

            if (report.diagnostics().isEmpty()) {
                System.out.println("No architecture issues detected.");
            }

            for (Diagnostic diagnostic : report.diagnostics()) {
                System.out.printf(
                    "[%s] %s: %s%n",
                    diagnostic.severity(),
                    diagnostic.code(),
                    diagnostic.message()
                );

                if (!diagnostic.location().isBlank()) {
                    System.out.println(
                        "  File: " + diagnostic.location()
                    );
                }
            }

            System.out.println("\nMODULE BUILD ORDER");

            List<String> order = service.buildOrder();

            for (int i = 0; i < order.size(); i++) {
                System.out.printf(
                    "%d. %s%n",
                    i + 1,
                    order.get(i)
                );
            }

            System.out.println("\nINTERFACE VALIDATION");

            Map<String, Object> implementation = Map.of(
                "id", "USR-101",
                "email", "developer@example.com",
                "displayName", "Development User"
            );

            List<String> errors =
                interfaces.validateImplementation(
                    "User",
                    implementation
                );

            System.out.println(
                errors.isEmpty()
                    ? "User contract is valid."
                    : String.join("\n", errors)
            );

            System.out.println("\nREGISTERED MODULES");

            for (ModuleDefinition module : modules.all()) {
                System.out.printf(
                    "%s | %s | %s%n",
                    module.name(),
                    module.filePath(),
                    module.kind()
                );
            }

            System.out.println(
                "\nTypeScript target: " + configuration.target()
            );

            if (!report.valid()) {
                System.exit(1);
            }

        } catch (ArchitectureException exception) {
            System.err.println(
                "Architecture failure: " + exception.getMessage()
            );
            System.exit(1);
        }
    }
}
