import java.util.ArrayList;
import java.util.Collections;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.TreeSet;

/**
 * Enterprise repository module governance.
 *
 * Java 17 or later.
 * Save as ModuleArchitecture.java and run:
 *   javac ModuleArchitecture.java
 *   java ModuleArchitecture
 *
 * The program models module contracts, export visibility, dependency
 * validation, architecture layers, and release-readiness checks.
 */
public class ModuleArchitecture {

    enum ExportKind {
        NAMED,
        DEFAULT
    }

    enum Layer {
        DOMAIN,
        APPLICATION,
        INFRASTRUCTURE,
        PRESENTATION
    }

    enum ModuleStatus {
        REGISTERED,
        VALIDATED,
        FAILED
    }

    record ExportDefinition(String name, ExportKind kind) {
        ExportDefinition {
            Objects.requireNonNull(name, "Export name is required");
            Objects.requireNonNull(kind, "Export kind is required");

            if (kind == ExportKind.NAMED && name.isBlank()) {
                throw new IllegalArgumentException("Named exports require a name");
            }

            if (kind == ExportKind.DEFAULT && !name.equals("default")) {
                throw new IllegalArgumentException(
                    "Default export must use the canonical name 'default'"
                );
            }
        }
    }

    record ImportDefinition(
        String sourcePath,
        String importedName,
        boolean defaultImport
    ) {
        ImportDefinition {
            if (sourcePath == null || sourcePath.isBlank()) {
                throw new IllegalArgumentException("Import path is required");
            }
            if (importedName == null || importedName.isBlank()) {
                throw new IllegalArgumentException("Imported name is required");
            }
            if (defaultImport && !importedName.equals("default")) {
                throw new IllegalArgumentException(
                    "Default imports must identify the default export"
                );
            }
        }
    }

    static final class ModuleDefinition {
        private final String path;
        private final Layer layer;
        private final List<ExportDefinition> exports;
        private final List<ImportDefinition> imports;
        private ModuleStatus status = ModuleStatus.REGISTERED;

        ModuleDefinition(
            String path,
            Layer layer,
            List<ExportDefinition> exports,
            List<ImportDefinition> imports
        ) {
            if (path == null || path.isBlank() || path.startsWith("/")) {
                throw new IllegalArgumentException(
                    "Module path must be a non-empty relative path"
                );
            }

            this.path = path;
            this.layer = Objects.requireNonNull(layer);
            this.exports = List.copyOf(exports);
            this.imports = List.copyOf(imports);
            validateExportUniqueness();
        }

        private void validateExportUniqueness() {
            Set<String> names = new HashSet<>();
            boolean defaultSeen = false;

            for (ExportDefinition export : exports) {
                if (export.kind() == ExportKind.DEFAULT) {
                    if (defaultSeen) {
                        throw new IllegalArgumentException(
                            path + " declares more than one default export"
                        );
                    }
                    defaultSeen = true;
                } else if (!names.add(export.name())) {
                    throw new IllegalArgumentException(
                        path + " duplicates named export " + export.name()
                    );
                }
            }
        }

        boolean exports(String name, boolean defaultImport) {
            return exports.stream().anyMatch(export ->
                defaultImport
                    ? export.kind() == ExportKind.DEFAULT
                    : export.kind() == ExportKind.NAMED && export.name().equals(name)
            );
        }

        String path() {
            return path;
        }

        Layer layer() {
            return layer;
        }

        List<ExportDefinition> exports() {
            return exports;
        }

        List<ImportDefinition> imports() {
            return imports;
        }

        ModuleStatus status() {
            return status;
        }

        void setStatus(ModuleStatus status) {
            this.status = status;
        }
    }

    static final class ArchitectureException extends RuntimeException {
        ArchitectureException(String message) {
            super(message);
        }
    }

    static final class ModuleCatalog {
        private final Map<String, ModuleDefinition> modules = new LinkedHashMap<>();
        private final Map<String, Set<String>> dependencies = new LinkedHashMap<>();
        private final Map<Layer, Set<Layer>> allowedDependencies =
            new EnumMap<>(Layer.class);

        ModuleCatalog() {
            // Domain owns business rules. It must not depend on application,
            // infrastructure, or presentation layers.
            allowedDependencies.put(Layer.DOMAIN, Set.of());
            allowedDependencies.put(
                Layer.APPLICATION,
                Set.of(Layer.DOMAIN, Layer.INFRASTRUCTURE)
            );
            allowedDependencies.put(
                Layer.INFRASTRUCTURE,
                Set.of(Layer.DOMAIN)
            );
            allowedDependencies.put(
                Layer.PRESENTATION,
                Set.of(Layer.APPLICATION, Layer.DOMAIN)
            );
        }

        void register(ModuleDefinition module) {
            if (modules.putIfAbsent(module.path(), module) != null) {
                throw new ArchitectureException(
                    "Duplicate module path: " + module.path()
                );
            }
            dependencies.put(module.path(), new TreeSet<>());
        }

        void validateAll() {
            List<String> errors = new ArrayList<>();

            for (ModuleDefinition module : modules.values()) {
                for (ImportDefinition binding : module.imports()) {
                    String targetPath = resolve(module.path(), binding.sourcePath());
                    ModuleDefinition target = modules.get(targetPath);

                    if (target == null) {
                        errors.add(
                            module.path() + " imports missing module " + targetPath
                        );
                        continue;
                    }

                    if (!target.exports(
                        binding.importedName(),
                        binding.defaultImport()
                    )) {
                        errors.add(
                            module.path() + " imports missing export '" +
                            binding.importedName() + "' from " + targetPath
                        );
                        continue;
                    }

                    if (!allowedDependencies.get(module.layer()).contains(target.layer())) {
                        errors.add(
                            "Forbidden layer dependency: " + module.path() +
                            " (" + module.layer() + ") -> " + target.path() +
                            " (" + target.layer() + ")"
                        );
                    }

                    dependencies.get(module.path()).add(target.path());
                }

                module.setStatus(ModuleStatus.VALIDATED);
            }

            if (!errors.isEmpty()) {
                modules.values().forEach(module ->
                    module.setStatus(ModuleStatus.FAILED)
                );
                throw new ArchitectureException(String.join("\n", errors));
            }

            topologicalOrder();
        }

        private String resolve(String importer, String specifier) {
            if (!specifier.startsWith(".")) {
                throw new ArchitectureException(
                    "This catalog expects relative imports: " + specifier
                );
            }

            String parent = "";
            int slash = importer.lastIndexOf('/');
            if (slash >= 0) {
                parent = importer.substring(0, slash + 1);
            }

            List<String> parts = new ArrayList<>();
            for (String part : (parent + specifier).split("/")) {
                if (part.isBlank() || part.equals(".")) {
                    continue;
                }
                if (part.equals("..")) {
                    if (parts.isEmpty()) {
                        throw new ArchitectureException(
                            "Import escapes source root: " + specifier
                        );
                    }
                    parts.remove(parts.size() - 1);
                } else {
                    parts.add(part);
                }
            }

            return String.join("/", parts);
        }

        List<String> topologicalOrder() {
            Map<String, Integer> remaining = new HashMap<>();
            Map<String, Set<String>> dependents = new HashMap<>();

            dependencies.forEach((module, deps) -> {
                remaining.put(module, deps.size());
                deps.forEach(dependency ->
                    dependents.computeIfAbsent(
                        dependency,
                        ignored -> new TreeSet<>()
                    ).add(module)
                );
            });

            TreeSet<String> ready = new TreeSet<>();
            remaining.forEach((module, count) -> {
                if (count == 0) {
                    ready.add(module);
                }
            });

            List<String> result = new ArrayList<>();

            while (!ready.isEmpty()) {
                String current = ready.pollFirst();
                result.add(current);

                for (String dependent :
                    dependents.getOrDefault(current, Collections.emptySet())) {
                    int count = remaining.merge(dependent, -1, Integer::sum);
                    if (count == 0) {
                        ready.add(dependent);
                    }
                }
            }

            if (result.size() != modules.size()) {
                throw new ArchitectureException(
                    "Circular dependency detected; modules cannot be ordered"
                );
            }

            return List.copyOf(result);
        }

        void printCatalog() {
            modules.values().forEach(module -> {
                System.out.println(
                    module.path() + " [" + module.layer() + ", " +
                    module.status() + "]"
                );
                System.out.println("  exports: " + module.exports());
                System.out.println(
                    "  dependencies: " +
                    dependencies.getOrDefault(module.path(), Set.of())
                );
            });
        }
    }

    static ModuleDefinition module(
        String path,
        Layer layer,
        List<ExportDefinition> exports,
        List<ImportDefinition> imports
    ) {
        return new ModuleDefinition(path, layer, exports, imports);
    }

    static ExportDefinition named(String name) {
        return new ExportDefinition(name, ExportKind.NAMED);
    }

    static ExportDefinition defaultExport() {
        return new ExportDefinition("default", ExportKind.DEFAULT);
    }

    static ImportDefinition namedImport(String path, String name) {
        return new ImportDefinition(path, name, false);
    }

    static ImportDefinition defaultImport(String path) {
        return new ImportDefinition(path, "default", true);
    }

    public static void main(String[] args) {
        ModuleCatalog catalog = new ModuleCatalog();

        catalog.register(module(
            "src/domain/pricing.js",
            Layer.DOMAIN,
            List.of(named("calculateTotal"), defaultExport()),
            List.of()
        ));

        catalog.register(module(
            "src/domain/tax.js",
            Layer.DOMAIN,
            List.of(named("calculateTax")),
            List.of()
        ));

        catalog.register(module(
            "src/application/invoice.js",
            Layer.APPLICATION,
            List.of(named("createInvoice")),
            List.of(
                namedImport("../domain/pricing.js", "calculateTotal"),
                namedImport("../domain/tax.js", "calculateTax")
            )
        ));

        catalog.register(module(
            "src/presentation/invoice-screen.js",
            Layer.PRESENTATION,
            List.of(named("renderInvoice")),
            List.of(
                namedImport("../application/invoice.js", "createInvoice")
            )
        ));

        System.out.println("Enterprise module catalog");
        catalog.validateAll();
        catalog.printCatalog();
        System.out.println("Dependency-first order: " + catalog.topologicalOrder());

        System.out.println("\nInvalid import contract");
        ModuleCatalog broken = new ModuleCatalog();
        broken.register(module(
            "src/domain/money.js",
            Layer.DOMAIN,
            List.of(named("formatMoney")),
            List.of()
        ));
        broken.register(module(
            "src/application/report.js",
            Layer.APPLICATION,
            List.of(named("createReport")),
            List.of(namedImport("../domain/money.js", "formatDate"))
        ));

        try {
            broken.validateAll();
        } catch (ArchitectureException error) {
            System.out.println(error.getMessage());
        }

        System.out.println("\nInvalid architectural dependency");
        ModuleCatalog layerViolation = new ModuleCatalog();
        layerViolation.register(module(
            "src/presentation/widget.js",
            Layer.PRESENTATION,
            List.of(named("renderWidget")),
            List.of()
        ));
        layerViolation.register(module(
            "src/domain/widget-model.js",
            Layer.DOMAIN,
            List.of(named("widgetModel")),
            List.of(namedImport("../presentation/widget.js", "renderWidget"))
        ));

        try {
            layerViolation.validateAll();
        } catch (ArchitectureException error) {
            System.out.println(error.getMessage());
        }
    }
}
