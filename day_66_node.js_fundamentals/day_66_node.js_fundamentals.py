#!/usr/bin/env python3
"""
Node.js Fundamentals: Runtime, Modules, Filesystem, Process, Environment.

This Python program models a Node.js application deployment inspector.
It demonstrates module dependency validation, environment configuration,
filesystem security, runtime compatibility, and deployment readiness.
"""

from __future__ import annotations

import json
import os
import platform
import re
import tempfile
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class Severity(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass
class Finding:
    severity: Severity
    category: str
    message: str


@dataclass
class Module:
    name: str
    version: str
    dependencies: list[str] = field(default_factory=list)
    is_builtin: bool = False


@dataclass
class RuntimeManifest:
    application: str
    required_node_version: str
    entry_point: str
    modules: list[Module]
    required_environment: list[str]
    production: bool = False


class ConfigurationError(Exception):
    pass


class ModuleResolutionError(Exception):
    pass


class FilesystemSecurityError(Exception):
    pass


class Version:
    """Compare semantic version numbers without external dependencies."""

    @staticmethod
    def parse(value: str) -> tuple[int, int, int]:
        match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", value.strip())

        if not match:
            raise ValueError(f"Invalid version: {value}")

        return tuple(map(int, match.groups()))

    @staticmethod
    def satisfies(actual: str, required: str) -> bool:
        return Version.parse(actual) >= Version.parse(required)


class EnvironmentManager:
    """Validate environment configuration without exposing secret values."""

    def __init__(self, environment: dict[str, str]):
        self.environment = environment

    def validate(self, required: list[str]) -> list[Finding]:
        findings = []

        for key in required:
            value = self.environment.get(key)

            if value is None or not value.strip():
                findings.append(
                    Finding(
                        Severity.ERROR,
                        "ENVIRONMENT",
                        f"Required variable {key} is missing or empty."
                    )
                )
            else:
                findings.append(
                    Finding(
                        Severity.INFO,
                        "ENVIRONMENT",
                        f"Required variable {key} is configured."
                    )
                )

        return findings

    def get_integer(
        self,
        key: str,
        default: int,
        minimum: int,
        maximum: int
    ) -> int:
        raw = self.environment.get(key)

        if raw is None:
            return default

        try:
            value = int(raw)
        except ValueError as exc:
            raise ConfigurationError(
                f"{key} must contain an integer."
            ) from exc

        if not minimum <= value <= maximum:
            raise ConfigurationError(
                f"{key} must be between {minimum} and {maximum}."
            )

        return value


class ModuleRegistry:
    """Model built-in and application module resolution."""

    BUILTIN_MODULES = {
        "fs",
        "path",
        "os",
        "http",
        "https",
        "events",
        "crypto",
        "process",
        "util",
        "url",
        "stream",
        "buffer",
        "assert",
        "timers",
    }

    def __init__(self, modules: list[Module]):
        self.modules = {module.name: module for module in modules}

    def resolve(self, name: str) -> Module:
        if name in self.BUILTIN_MODULES:
            return Module(name, "builtin", is_builtin=True)

        module = self.modules.get(name)

        if module is None:
            raise ModuleResolutionError(
                f"Cannot resolve module: {name}"
            )

        return module

    def validate_dependencies(self) -> list[Finding]:
        findings = []

        for module in self.modules.values():
            for dependency in module.dependencies:
                try:
                    self.resolve(dependency)
                except ModuleResolutionError:
                    findings.append(
                        Finding(
                            Severity.ERROR,
                            "MODULE",
                            f"{module.name} requires missing module "
                            f"{dependency}."
                        )
                    )

        return findings


class SecureFileManager:
    """Restrict filesystem operations to an application directory."""

    def __init__(self, root: Path):
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def resolve(self, relative_path: str) -> Path:
        candidate = (self.root / relative_path).resolve()

        if not candidate.is_relative_to(self.root):
            raise FilesystemSecurityError(
                "Path traversal outside the application directory."
            )

        return candidate

    def write_json(self, relative_path: str, data: Any) -> Path:
        target = self.resolve(relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)

        # Atomic replacement prevents partially written JSON files.
        temporary = target.with_suffix(target.suffix + ".tmp")

        try:
            temporary.write_text(
                json.dumps(data, indent=2),
                encoding="utf-8"
            )
            temporary.replace(target)
        except OSError:
            temporary.unlink(missing_ok=True)
            raise

        return target

    def read_json(self, relative_path: str) -> Any:
        target = self.resolve(relative_path)

        if not target.is_file():
            raise FileNotFoundError(target)

        return json.loads(target.read_text(encoding="utf-8"))

    def list_files(self) -> list[str]:
        return sorted(
            str(path.relative_to(self.root))
            for path in self.root.rglob("*")
            if path.is_file()
        )


class DeploymentInspector:
    def __init__(
        self,
        manifest: RuntimeManifest,
        actual_node_version: str,
        environment: dict[str, str],
        project_directory: Path
    ):
        self.manifest = manifest
        self.actual_node_version = actual_node_version
        self.environment = EnvironmentManager(environment)
        self.modules = ModuleRegistry(manifest.modules)
        self.files = SecureFileManager(project_directory)

    def inspect(self) -> list[Finding]:
        findings = []

        try:
            compatible = Version.satisfies(
                self.actual_node_version,
                self.manifest.required_node_version
            )

            findings.append(
                Finding(
                    Severity.INFO if compatible else Severity.ERROR,
                    "RUNTIME",
                    f"Node.js {self.actual_node_version}; "
                    f"minimum required: "
                    f"{self.manifest.required_node_version}."
                )
            )

        except ValueError as exc:
            findings.append(
                Finding(Severity.ERROR, "RUNTIME", str(exc))
            )

        findings.extend(
            self.environment.validate(
                self.manifest.required_environment
            )
        )

        findings.extend(self.modules.validate_dependencies())

        try:
            entry = self.files.resolve(self.manifest.entry_point)

            if not entry.is_file():
                findings.append(
                    Finding(
                        Severity.ERROR,
                        "ENTRY_POINT",
                        f"Entry point does not exist: "
                        f"{self.manifest.entry_point}"
                    )
                )
            else:
                findings.append(
                    Finding(
                        Severity.INFO,
                        "ENTRY_POINT",
                        "Application entry point exists."
                    )
                )

        except FilesystemSecurityError as exc:
            findings.append(
                Finding(Severity.ERROR, "FILESYSTEM", str(exc))
            )

        return findings

    def ready(self) -> bool:
        return not any(
            finding.severity == Severity.ERROR
            for finding in self.inspect()
        )


def demonstrate_process_information() -> None:
    """Display process information without printing secret environment data."""

    print("\nPROCESS INFORMATION")
    print("-" * 55)
    print("Python executable:", os.sys.executable)
    print("Operating system:", platform.system())
    print("Platform:", platform.platform())
    print("Process ID:", os.getpid())
    print("Current directory:", Path.cwd())
    print("Python version:", platform.python_version())


def demonstrate_filesystem(manager: SecureFileManager) -> None:
    print("\nFILESYSTEM OPERATIONS")
    print("-" * 55)

    configuration = {
        "application": "node-fundamentals-demo",
        "port": 3000,
        "mode": "development",
        "modules": ["fs", "path", "events"]
    }

    manager.write_json("config/application.json", configuration)

    loaded = manager.read_json("config/application.json")

    print("Written and retrieved configuration:")
    print(json.dumps(loaded, indent=2))

    print("Files:", manager.list_files())

    try:
        manager.resolve("../../outside.json")
    except FilesystemSecurityError as exc:
        print("Security control:", exc)


def main() -> None:
    print("=" * 65)
    print("NODE.JS FUNDAMENTALS: RUNTIME AND APPLICATION INSPECTOR")
    print("=" * 65)

    modules = [
        Module("express", "5.1.0", ["http", "path"]),
        Module("application-core", "1.0.0", ["express", "crypto"]),
        Module("logger", "2.0.0", ["fs", "path"]),
    ]

    manifest = RuntimeManifest(
        application="inventory-api",
        required_node_version="18.0.0",
        entry_point="src/index.js",
        modules=modules,
        required_environment=[
            "NODE_ENV",
            "PORT",
            "DATABASE_URL"
        ],
        production=False
    )

    environment = {
        "NODE_ENV": "development",
        "PORT": "3000",
        "DATABASE_URL": "postgresql://localhost/inventory"
    }

    demonstrate_process_information()

    print("\nENVIRONMENT VALIDATION")
    print("-" * 55)

    manager = EnvironmentManager(environment)

    for finding in manager.validate(
        manifest.required_environment
    ):
        print(f"{finding.severity.value}: {finding.message}")

    print("\nPORT VALIDATION")
    print("-" * 55)

    try:
        port = manager.get_integer("PORT", 3000, 1, 65535)
        print("Validated application port:", port)
    except ConfigurationError as exc:
        print("Configuration error:", exc)

    print("\nMODULE RESOLUTION")
    print("-" * 55)

    registry = ModuleRegistry(modules)

    for name in ["fs", "path", "express", "application-core"]:
        resolved = registry.resolve(name)
        print(
            f"{resolved.name}: "
            f"{'built-in' if resolved.is_builtin else 'application package'}"
        )

    print("\nDEPLOYMENT INSPECTION")
    print("-" * 55)

    with tempfile.TemporaryDirectory() as temporary:
        project = Path(temporary)

        source = project / "src" / "index.js"
        source.parent.mkdir(parents=True)
        source.write_text(
            "console.log('Inventory API started');\n",
            encoding="utf-8"
        )

        inspector = DeploymentInspector(
            manifest,
            "22.0.0",
            environment,
            project
        )

        findings = inspector.inspect()

        for finding in findings:
            print(
                f"{finding.severity.value:7} "
                f"[{finding.category}] {finding.message}"
            )

        print(
            "\nDeployment status:",
            "READY" if inspector.ready() else "BLOCKED"
        )

        demonstrate_filesystem(inspector.files)

    print("\nEDGE CASE VALIDATION")
    print("-" * 55)

    try:
        manager.get_integer("INVALID_PORT", 3000, 1, 65535)
        print("Default port accepted.")
    except ConfigurationError as exc:
        print(exc)

    try:
        Version.parse("invalid-version")
    except ValueError as exc:
        print("Version validation:", exc)

    try:
        registry.resolve("missing-package")
    except ModuleResolutionError as exc:
        print("Module resolution:", exc)

    print("\nINSPECTION COMPLETED")


if __name__ == "__main__":
    main()
