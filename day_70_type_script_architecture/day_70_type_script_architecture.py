#!/usr/bin/env python3
"""
TypeScript Architecture: Interfaces, Declarations, Modules, tsconfig, and Strict Mode.

A self-contained architecture analyzer that models:
- Interface contracts and structural compatibility.
- Declaration files and ambient declarations.
- Module exports and imports.
- Dependency graph validation and circular dependency detection.
- TypeScript compiler configuration.
- Strict-mode compiler policies.
- Architecture diagnostics and validation.
- Project manifests and JSON configuration files.

Requires Python 3.10 or later.
Uses only the Python standard library.
"""

from __future__ import annotations

import json
import logging
from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
logger = logging.getLogger("typescript_architecture")


class ArchitectureError(Exception):
    """Base exception for architecture validation failures."""


class ConfigurationError(ArchitectureError):
    """Invalid compiler configuration."""


class DependencyError(ArchitectureError):
    """Invalid module dependency."""


class CompatibilityError(ArchitectureError):
    """Incompatible interface contracts."""


class ModuleKind(str, Enum):
    ES_MODULE = "es-module"
    COMMON_JS = "commonjs"
    DECLARATION = "declaration"
    AMBIENT = "ambient"


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True)
class Property:
    name: str
    type_name: str
    optional: bool = False
    readonly: bool = False

    def __post_init__(self) -> None:
        if not self.name.strip() or not self.type_name.strip():
            raise ValueError("Property name and type cannot be empty.")


@dataclass
class Interface:
    name: str
    properties: dict[str, Property] = field(default_factory=dict)
    extends: list[str] = field(default_factory=list)

    def add_property(self, prop: Property) -> None:
        if prop.name in self.properties:
            raise ArchitectureError(
                f"Duplicate property '{prop.name}' in {self.name}."
            )
        self.properties[prop.name] = prop


@dataclass
class Module:
    name: str
    path: str
    kind: ModuleKind = ModuleKind.ES_MODULE
    exports: set[str] = field(default_factory=set)
    imports: set[str] = field(default_factory=set)
    interfaces: set[str] = field(default_factory=set)
    is_entry_point: bool = False

    def export(self, symbol: str) -> None:
        if not symbol.strip():
            raise ValueError("Export name cannot be empty.")
        self.exports.add(symbol)

    def import_from(self, module_name: str) -> None:
        if not module_name.strip():
            raise ValueError("Module name cannot be empty.")
        self.imports.add(module_name)


@dataclass(frozen=True)
class Diagnostic:
    code: str
    severity: Severity
    message: str
    location: str = ""


@dataclass
class CompilerConfig:
    target: str = "ES2022"
    module: str = "NodeNext"
    module_resolution: str = "NodeNext"
    strict: bool = True
    strict_null_checks: bool = True
    no_implicit_any: bool = True
    strict_function_types: bool = True
    strict_property_initialization: bool = True
    no_implicit_override: bool = True
    no_unused_locals: bool = True
    no_unused_parameters: bool = True
    no_fallthrough_cases: bool = True
    no_unchecked_indexed_access: bool = True
    exact_optional_property_types: bool = True
    declaration: bool = True
    declaration_map: bool = True
    source_map: bool = True
    es_module_interop: bool = True
    force_consistent_casing: bool = True
    skip_lib_check: bool = False
    root_dir: str = "src"
    out_dir: str = "dist"
    base_url: str = "."
    paths: dict[str, list[str]] = field(default_factory=dict)
    include: list[str] = field(
        default_factory=lambda: ["src/**/*.ts"]
    )
    exclude: list[str] = field(
        default_factory=lambda: ["node_modules", "dist"]
    )

    def validate(self) -> None:
        if self.strict:
            required = [
                self.strict_null_checks,
                self.no_implicit_any,
                self.strict_function_types,
                self.strict_property_initialization,
            ]
            if not all(required):
                raise ConfigurationError(
                    "Strict mode is enabled but one or more "
                    "strict compiler checks are disabled."
                )

        if self.root_dir == self.out_dir:
            raise ConfigurationError(
                "Source and output directories must differ."
            )

        if not self.target.strip() or not self.module.strip():
            raise ConfigurationError(
                "Target and module settings cannot be empty."
            )

        for alias, destinations in self.paths.items():
            if not alias.strip() or not destinations:
                raise ConfigurationError(
                    "Path aliases require a name and destinations."
                )

    def to_typescript_json(self) -> dict[str, Any]:
        return {
            "compilerOptions": {
                "target": self.target,
                "module": self.module,
                "moduleResolution": self.module_resolution,
                "strict": self.strict,
                "strictNullChecks": self.strict_null_checks,
                "noImplicitAny": self.no_implicit_any,
                "strictFunctionTypes": self.strict_function_types,
                "strictPropertyInitialization":
                    self.strict_property_initialization,
                "noImplicitOverride": self.no_implicit_override,
                "noUnusedLocals": self.no_unused_locals,
                "noUnusedParameters": self.no_unused_parameters,
                "noFallthroughCasesInSwitch":
                    self.no_fallthrough_cases,
                "noUncheckedIndexedAccess":
                    self.no_unchecked_indexed_access,
                "exactOptionalPropertyTypes":
                    self.exact_optional_property_types,
                "declaration": self.declaration,
                "declarationMap": self.declaration_map,
                "sourceMap": self.source_map,
                "esModuleInterop": self.es_module_interop,
                "forceConsistentCasingInFileNames":
                    self.force_consistent_casing,
                "skipLibCheck": self.skip_lib_check,
                "rootDir": self.root_dir,
                "outDir": self.out_dir,
                "baseUrl": self.base_url,
                "paths": self.paths,
            },
            "include": self.include,
            "exclude": self.exclude,
        }


class InterfaceRegistry:
    """Stores interfaces and validates inherited contracts."""

    def __init__(self) -> None:
        self.interfaces: dict[str, Interface] = {}

    def register(self, interface: Interface) -> None:
        if interface.name in self.interfaces:
            raise ArchitectureError(
                f"Interface '{interface.name}' already exists."
            )
        self.interfaces[interface.name] = interface

    def resolve(self, name: str) -> dict[str, Property]:
        if name not in self.interfaces:
            raise ArchitectureError(
                f"Unknown interface: {name}"
            )

        resolved: dict[str, Property] = {}
        visiting: set[str] = set()

        def visit(current: str) -> None:
            if current in visiting:
                raise ArchitectureError(
                    f"Circular interface inheritance: {current}"
                )

            if current not in self.interfaces:
                raise ArchitectureError(
                    f"Unknown parent interface: {current}"
                )

            visiting.add(current)
            interface = self.interfaces[current]

            for parent in interface.extends:
                visit(parent)

            for prop_name, prop in interface.properties.items():
                if prop_name in resolved:
                    inherited = resolved[prop_name]
                    if inherited.type_name != prop.type_name:
                        raise CompatibilityError(
                            f"Conflicting inherited property: {prop_name}"
                        )
                resolved[prop_name] = prop

            visiting.remove(current)

        visit(name)
        return resolved

    def check_implementation(
        self,
        interface_name: str,
        implementation: dict[str, Any],
    ) -> list[str]:
        contract = self.resolve(interface_name)
        errors = []

        for name, prop in contract.items():
            if name not in implementation:
                if not prop.optional:
                    errors.append(f"Missing required property: {name}")
                continue

            value = implementation[name]

            if value is None and not prop.optional:
                errors.append(
                    f"Required property '{name}' cannot be null."
                )

        return errors


class DependencyGraph:
    """Directed graph of module imports."""

    def __init__(self) -> None:
        self.graph: dict[str, set[str]] = defaultdict(set)

    def add_module(self, name: str) -> None:
        self.graph[name]

    def add_dependency(self, source: str, target: str) -> None:
        if source not in self.graph or target not in self.graph:
            raise DependencyError(
                f"Unknown dependency endpoint: {source} -> {target}"
            )
        self.graph[source].add(target)

    def topological_sort(self) -> list[str]:
        indegree = {node: 0 for node in self.graph}

        for dependencies in self.graph.values():
            for dependency in dependencies:
                indegree[dependency] += 1

        queue = deque(
            node for node, degree in indegree.items()
            if degree == 0
        )

        result = []

        while queue:
            current = queue.popleft()
            result.append(current)

            for dependency in sorted(self.graph[current]):
                indegree[dependency] -= 1
                if indegree[dependency] == 0:
                    queue.append(dependency)

        if len(result) != len(self.graph):
            raise DependencyError(
                "Circular module dependency detected."
            )

        return result

    def find_unreachable(
        self,
        entry_points: set[str]
    ) -> set[str]:
        reachable = set()
        queue = deque(entry_points)

        while queue:
            current = queue.popleft()

            if current in reachable:
                continue

            reachable.add(current)
            queue.extend(self.graph[current] - reachable)

        return set(self.graph) - reachable


class ArchitectureAnalyzer:
    def __init__(self, config: CompilerConfig) -> None:
        config.validate()

        self.config = config
        self.modules: dict[str, Module] = {}
        self.interfaces = InterfaceRegistry()
        self.dependencies = DependencyGraph()
        self.diagnostics: list[Diagnostic] = []

    def add_module(self, module: Module) -> None:
        if module.name in self.modules:
            raise ArchitectureError(
                f"Module already registered: {module.name}"
            )

        self.modules[module.name] = module
        self.dependencies.add_module(module.name)

    def add_interface(self, interface: Interface) -> None:
        self.interfaces.register(interface)

    def validate_modules(self) -> None:
        for module in self.modules.values():
            for dependency in module.imports:
                if dependency not in self.modules:
                    self.diagnostics.append(
                        Diagnostic(
                            "MODULE001",
                            Severity.ERROR,
                            f"Unknown imported module: {dependency}",
                            module.path,
                        )
                    )
                    continue

                self.dependencies.add_dependency(
                    module.name, dependency
                )

            for symbol in module.interfaces:
                if symbol not in self.interfaces.interfaces:
                    self.diagnostics.append(
                        Diagnostic(
                            "TYPE001",
                            Severity.ERROR,
                            f"Unknown interface: {symbol}",
                            module.path,
                        )
                    )

        try:
            self.dependencies.topological_sort()
        except DependencyError as error:
            self.diagnostics.append(
                Diagnostic(
                    "MODULE002",
                    Severity.ERROR,
                    str(error)
                )
            )

        entry_points = {
            name for name, module in self.modules.items()
            if module.is_entry_point
        }

        if entry_points:
            unreachable = self.dependencies.find_unreachable(
                entry_points
            )

            for module_name in sorted(unreachable):
                self.diagnostics.append(
                    Diagnostic(
                        "MODULE003",
                        Severity.WARNING,
                        f"Module is unreachable: {module_name}",
                        self.modules[module_name].path,
                    )
                )

    def validate_declarations(self) -> None:
        for module in self.modules.values():
            if module.kind == ModuleKind.DECLARATION:
                if module.imports and not module.exports:
                    self.diagnostics.append(
                        Diagnostic(
                            "DECL001",
                            Severity.WARNING,
                            "Declaration module has imports but no exports.",
                            module.path,
                        )
                    )

    def run(self) -> list[Diagnostic]:
        self.diagnostics.clear()
        self.validate_modules()
        self.validate_declarations()
        return list(self.diagnostics)

    def report(self) -> None:
        diagnostics = self.run()

        print("\nARCHITECTURE VALIDATION")
        print("=" * 55)

        if not diagnostics:
            print("No architecture issues detected.")
            return

        for diagnostic in diagnostics:
            print(
                f"[{diagnostic.severity.value.upper()}] "
                f"{diagnostic.code}: {diagnostic.message}"
            )
            if diagnostic.location:
                print(f"  Location: {diagnostic.location}")


class ProjectExporter:
    """Writes validated architecture metadata and tsconfig.json."""

    @staticmethod
    def export(
        analyzer: ArchitectureAnalyzer,
        destination: Path
    ) -> None:
        destination.mkdir(parents=True, exist_ok=True)

        config_path = destination / "tsconfig.json"
        config_path.write_text(
            json.dumps(
                analyzer.config.to_typescript_json(),
                indent=2
            ),
            encoding="utf-8"
        )

        architecture = {
            "modules": [
                {
                    "name": module.name,
                    "path": module.path,
                    "kind": module.kind.value,
                    "exports": sorted(module.exports),
                    "imports": sorted(module.imports),
                    "interfaces": sorted(module.interfaces),
                }
                for module in analyzer.modules.values()
            ],
            "interfaces": {
                name: {
                    "properties": [
                        asdict(prop)
                        for prop in interface.properties.values()
                    ],
                    "extends": interface.extends,
                }
                for name, interface in
                analyzer.interfaces.interfaces.items()
            },
        }

        (destination / "architecture.json").write_text(
            json.dumps(architecture, indent=2),
            encoding="utf-8"
        )


def build_example() -> ArchitectureAnalyzer:
    config = CompilerConfig(
        paths={
            "@domain/*": ["src/domain/*"],
            "@services/*": ["src/services/*"],
            "@infrastructure/*": ["src/infrastructure/*"],
        }
    )

    analyzer = ArchitectureAnalyzer(config)

    entity = Interface("Entity")
    entity.add_property(
        Property("id", "string", readonly=True)
    )

    user = Interface(
        "User",
        extends=["Entity"]
    )
    user.add_property(Property("email", "string"))
    user.add_property(Property("displayName", "string"))
    user.add_property(Property("phone", "string", optional=True))

    repository = Interface("UserRepository")
    repository.add_property(
        Property("findById", "(id: string) => Promise<User | null>")
    )
    repository.add_property(
        Property("save", "(user: User) => Promise<void>")
    )

    analyzer.add_interface(entity)
    analyzer.add_interface(user)
    analyzer.add_interface(repository)

    modules = [
        Module(
            "domain",
            "src/domain/user.ts",
            exports={"User", "Entity", "UserRepository"},
            interfaces={"User", "Entity", "UserRepository"},
        ),
        Module(
            "infrastructure",
            "src/infrastructure/user-repository.ts",
            imports={"domain"},
            exports={"PostgresUserRepository"},
            interfaces={"UserRepository"},
        ),
        Module(
            "services",
            "src/services/user-service.ts",
            imports={"domain", "infrastructure"},
            exports={"UserService"},
            interfaces={"User", "UserRepository"},
        ),
        Module(
            "api",
            "src/api/server.ts",
            imports={"services"},
            exports={"startServer"},
            is_entry_point=True,
        ),
    ]

    for module in modules:
        analyzer.add_module(module)

    return analyzer


def run_tests() -> None:
    registry = InterfaceRegistry()

    base = Interface("Base")
    base.add_property(Property("id", "string"))

    child = Interface("Child", extends=["Base"])
    child.add_property(Property("name", "string"))

    registry.register(base)
    registry.register(child)

    assert not registry.check_implementation(
        "Child",
        {"id": "U-101", "name": "Atul"}
    )

    assert registry.check_implementation(
        "Child",
        {"id": "U-101"}
    )

    graph = DependencyGraph()
    graph.add_module("application")
    graph.add_module("domain")
    graph.add_module("database")
    graph.add_dependency("application", "domain")
    graph.add_dependency("application", "database")

    assert len(graph.topological_sort()) == 3

    cyclic = DependencyGraph()
    cyclic.add_module("A")
    cyclic.add_module("B")
    cyclic.add_dependency("A", "B")
    cyclic.add_dependency("B", "A")

    try:
        cyclic.topological_sort()
    except DependencyError:
        pass
    else:
        raise AssertionError("Cycle detection failed.")

    try:
        CompilerConfig(
            strict=True,
            strict_null_checks=False
        ).validate()
    except ConfigurationError:
        pass
    else:
        raise AssertionError("Strict configuration validation failed.")

    print("All architecture tests passed.")


def main() -> None:
    run_tests()

    analyzer = build_example()
    analyzer.report()

    try:
        order = analyzer.dependencies.topological_sort()
        print("\nVALID MODULE BUILD ORDER")
        for index, module_name in enumerate(order, start=1):
            print(f"{index}. {module_name}")
    except DependencyError as error:
        logger.error("Build ordering failed: %s", error)

    implementation = {
        "id": "USR-101",
        "email": "developer@example.com",
        "displayName": "Development User",
    }

    errors = analyzer.interfaces.check_implementation(
        "User",
        implementation
    )

    print("\nINTERFACE VALIDATION")
    print("Valid" if not errors else "\n".join(errors))

    ProjectExporter.export(
        analyzer,
        Path("typescript_architecture_output")
    )

    print("\nConfiguration and architecture metadata exported.")


if __name__ == "__main__":
    try:
        main()
    except (ArchitectureError, OSError, ValueError) as error:
        logger.error("Execution failed: %s", error)
        raise SystemExit(1)
