#!/usr/bin/env python3
"""
Package Management Engineering Simulator

Demonstrates:
- package.json structure and validation
- dependencies and devDependencies
- semantic versioning
- version-range evaluation
- dependency conflict detection
- package-lock consistency
- npm scripts and execution policies
- dependency security auditing
- package installation planning
- reproducible package management
"""

from __future__ import annotations

import json
import re
import shlex
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class PackageError(Exception):
    """Base exception for package management errors."""


class ValidationError(PackageError):
    pass


class DependencyConflict(PackageError):
    pass


class SecurityError(PackageError):
    pass


class DependencyType(Enum):
    PRODUCTION = "dependencies"
    DEVELOPMENT = "devDependencies"


@dataclass(frozen=True, order=True)
class Version:
    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, value: str) -> Version:
        match = re.fullmatch(
            r"v?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)",
            value.strip()
        )
        if not match:
            raise ValidationError(f"Invalid semantic version: {value}")

        return cls(*(int(part) for part in match.groups()))

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


@dataclass(frozen=True)
class VersionRange:
    expression: str

    def accepts(self, version: Version) -> bool:
        expression = self.expression.strip()

        if expression in ("*", "latest"):
            return True

        if expression.startswith("^"):
            base = Version.parse(expression[1:])
            if version < base:
                return False

            if base.major > 0:
                return version.major == base.major

            if base.minor > 0:
                return version.major == 0 and version.minor == base.minor

            return (
                version.major == 0
                and version.minor == 0
                and version.patch == base.patch
            )

        if expression.startswith("~"):
            base = Version.parse(expression[1:])
            return (
                version >= base
                and version.major == base.major
                and version.minor == base.minor
            )

        if expression.startswith(">="):
            return version >= Version.parse(expression[2:].strip())

        if expression.startswith(">"):
            return version > Version.parse(expression[1:].strip())

        if expression.startswith("<="):
            return version <= Version.parse(expression[2:].strip())

        if expression.startswith("<"):
            return version < Version.parse(expression[1:].strip())

        return version == Version.parse(expression)


@dataclass
class Package:
    name: str
    version: Version
    dependencies: dict[str, VersionRange] = field(default_factory=dict)


@dataclass
class Project:
    name: str
    version: Version
    dependencies: dict[str, VersionRange] = field(default_factory=dict)
    dev_dependencies: dict[str, VersionRange] = field(default_factory=dict)
    scripts: dict[str, str] = field(default_factory=dict)
    engines: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_package_json(cls, data: dict[str, Any]) -> Project:
        if not isinstance(data, dict):
            raise ValidationError("package.json must contain a JSON object.")

        name = data.get("name")
        if not isinstance(name, str) or not re.fullmatch(
            r"(?:@[a-z0-9._-]+/)?[a-z0-9._-]+", name
        ):
            raise ValidationError("Invalid or missing package name.")

        if len(name) > 214 or name.startswith((".", "_")):
            raise ValidationError("Package name violates npm naming rules.")

        version = Version.parse(data.get("version", "1.0.0"))

        def parse_dependencies(key: str) -> dict[str, VersionRange]:
            raw = data.get(key, {})
            if not isinstance(raw, dict):
                raise ValidationError(f"{key} must be an object.")

            result = {}
            for package, expression in raw.items():
                if not isinstance(package, str) or not isinstance(expression, str):
                    raise ValidationError(f"Invalid entry in {key}.")

                if not package.strip() or not expression.strip():
                    raise ValidationError(f"Empty dependency in {key}.")

                # Validate supported range syntax before storing it.
                VersionRange(expression).accepts(Version(1, 0, 0))
                result[package] = VersionRange(expression)

            return result

        scripts = data.get("scripts", {})
        if not isinstance(scripts, dict):
            raise ValidationError("scripts must be an object.")

        if not all(
            isinstance(key, str) and isinstance(value, str)
            for key, value in scripts.items()
        ):
            raise ValidationError("Script names and commands must be strings.")

        engines = data.get("engines", {})
        if not isinstance(engines, dict):
            raise ValidationError("engines must be an object.")

        return cls(
            name=name,
            version=version,
            dependencies=parse_dependencies("dependencies"),
            dev_dependencies=parse_dependencies("devDependencies"),
            scripts=scripts,
            engines=engines,
        )


class PackageRegistry:
    """In-memory package registry with version selection."""

    def __init__(self):
        self.packages: dict[str, list[Package]] = defaultdict(list)

    def publish(self, package: Package) -> None:
        versions = self.packages[package.name]

        if any(p.version == package.version for p in versions):
            raise PackageError(
                f"{package.name}@{package.version} already exists."
            )

        versions.append(package)
        versions.sort(key=lambda p: p.version)

    def resolve(self, name: str, requirement: VersionRange) -> Package:
        candidates = [
            package
            for package in self.packages.get(name, [])
            if requirement.accepts(package.version)
        ]

        if not candidates:
            raise PackageError(
                f"No version of {name} satisfies {requirement.expression}"
            )

        return candidates[-1]


@dataclass
class LockEntry:
    name: str
    version: Version
    dependency_type: DependencyType


class PackageManager:
    def __init__(self, registry: PackageRegistry):
        self.registry = registry
        self.lockfile: dict[str, LockEntry] = {}

    def install(
        self,
        project: Project,
        include_dev: bool = True
    ) -> dict[str, LockEntry]:
        """
        Resolve direct dependencies and their transitive dependencies.
        Conflicting requirements for one package are rejected.
        """
        requirements: dict[str, list[VersionRange]] = defaultdict(list)
        types: dict[str, DependencyType] = {}

        for name, requirement in project.dependencies.items():
            requirements[name].append(requirement)
            types[name] = DependencyType.PRODUCTION

        if include_dev:
            for name, requirement in project.dev_dependencies.items():
                requirements[name].append(requirement)
                types.setdefault(name, DependencyType.DEVELOPMENT)

        resolved: dict[str, LockEntry] = {}
        queue = deque(requirements.items())

        while queue:
            name, constraints = queue.popleft()

            if name in resolved:
                selected = resolved[name].version

                if not all(c.accepts(selected) for c in constraints):
                    raise DependencyConflict(
                        f"Incompatible requirements for {name}."
                    )
                continue

            candidates = self.registry.packages.get(name, [])

            valid = [
                package for package in candidates
                if all(c.accepts(package.version) for c in constraints)
            ]

            if not valid:
                raise DependencyConflict(
                    f"No compatible version for {name}: "
                    f"{[c.expression for c in constraints]}"
                )

            selected = valid[-1]

            resolved[name] = LockEntry(
                name,
                selected.version,
                types.get(name, DependencyType.PRODUCTION)
            )

            for child, requirement in selected.dependencies.items():
                if child in resolved:
                    if not requirement.accepts(resolved[child].version):
                        raise DependencyConflict(
                            f"Transitive dependency conflict: {child}"
                        )
                else:
                    requirements[child].append(requirement)
                    queue.append((child, requirements[child]))

        self.lockfile = resolved
        return resolved

    def verify_lockfile(self, project: Project) -> bool:
        """Verify direct dependency versions against the lockfile."""
        for name, requirement in project.dependencies.items():
            entry = self.lockfile.get(name)
            if entry is None or not requirement.accepts(entry.version):
                return False

        for name, requirement in project.dev_dependencies.items():
            entry = self.lockfile.get(name)
            if entry is None or not requirement.accepts(entry.version):
                return False

        return True


@dataclass(frozen=True)
class Vulnerability:
    package: str
    affected_versions: tuple[str, ...]
    severity: str
    description: str


class SecurityAuditor:
    """Demonstration audit against a local vulnerability database."""

    def __init__(self, vulnerabilities: list[Vulnerability]):
        self.vulnerabilities = vulnerabilities

    def audit(self, lockfile: dict[str, LockEntry]) -> list[str]:
        findings = []

        for entry in lockfile.values():
            for vulnerability in self.vulnerabilities:
                if vulnerability.package != entry.name:
                    continue

                affected = any(
                    VersionRange(expression).accepts(entry.version)
                    for expression in vulnerability.affected_versions
                )

                if affected:
                    findings.append(
                        f"{vulnerability.severity}: {entry.name}@"
                        f"{entry.version}: {vulnerability.description}"
                    )

        return findings


class ScriptRunner:
    """
    Safe-by-default script inspection.

    Commands are displayed but not executed automatically.
    Shell commands can execute arbitrary code and must be reviewed.
    """

    ALLOWED_COMMANDS = {"node", "npm", "npx", "python", "pytest"}

    @classmethod
    def inspect(cls, scripts: dict[str, str]) -> list[str]:
        results = []

        for name, command in scripts.items():
            try:
                tokens = shlex.split(command)
            except ValueError as exc:
                results.append(f"INVALID {name}: {exc}")
                continue

            if not tokens:
                results.append(f"INVALID {name}: Empty command")
                continue

            executable = Path(tokens[0]).name.lower()

            if executable not in cls.ALLOWED_COMMANDS:
                results.append(
                    f"REVIEW REQUIRED {name}: {executable}"
                )
            else:
                results.append(
                    f"APPROVED FOR MANUAL REVIEW {name}: {command}"
                )

        return results


def demonstrate_semver() -> None:
    print("\nSEMANTIC VERSIONING")

    current = Version.parse("2.4.1")
    print(f"Current version: {current}")

    examples = ["^2.0.0", "~2.4.0", ">=2.0.0", "2.4.1"]

    for expression in examples:
        result = VersionRange(expression).accepts(current)
        print(f"{expression:12} -> {result}")


def build_demo_registry() -> PackageRegistry:
    registry = PackageRegistry()

    registry.publish(Package("express", Version(4, 21, 0)))
    registry.publish(Package("express", Version(4, 21, 1)))
    registry.publish(Package("express", Version(5, 0, 0)))

    registry.publish(Package("typescript", Version(5, 7, 0)))
    registry.publish(Package("typescript", Version(5, 8, 0)))

    registry.publish(
        Package(
            "http-client",
            Version(2, 3, 0),
            {"express": VersionRange("^4.0.0")}
        )
    )

    return registry


def main() -> None:
    package_data = {
        "name": "team-dashboard",
        "version": "1.2.0",
        "description": "Team collaboration application",
        "dependencies": {
            "express": "^4.0.0",
            "http-client": "^2.0.0"
        },
        "devDependencies": {
            "typescript": "~5.7.0"
        },
        "scripts": {
            "start": "node server.js",
            "test": "node test.js",
            "build": "npx tsc",
            "lint": "npm run test"
        },
        "engines": {
            "node": ">=20.0.0"
        }
    }

    try:
        project = Project.from_package_json(package_data)

        print("PACKAGE VALIDATION")
        print(f"Name: {project.name}")
        print(f"Version: {project.version}")
        print(f"Production dependencies: {len(project.dependencies)}")
        print(f"Development dependencies: {len(project.dev_dependencies)}")

        demonstrate_semver()

        registry = build_demo_registry()
        manager = PackageManager(registry)

        print("\nINSTALLATION PLAN")
        lockfile = manager.install(project)

        for entry in sorted(lockfile.values(), key=lambda item: item.name):
            print(
                f"{entry.name}@{entry.version} "
                f"[{entry.dependency_type.value}]"
            )

        print("\nLOCKFILE VERIFICATION")
        print("Valid:", manager.verify_lockfile(project))

        vulnerabilities = [
            Vulnerability(
                package="express",
                affected_versions=("<4.21.1",),
                severity="HIGH",
                description="Demonstration of an outdated vulnerable version."
            )
        ]

        print("\nSECURITY AUDIT")
        findings = SecurityAuditor(vulnerabilities).audit(lockfile)

        if findings:
            for finding in findings:
                print(finding)
        else:
            print("No matching vulnerabilities found.")

        print("\nNPM SCRIPT POLICY")
        for result in ScriptRunner.inspect(project.scripts):
            print(result)

        print("\nPACKAGE.JSON SERIALIZATION")
        print(json.dumps(package_data, indent=2))

        assert VersionRange("^2.0.0").accepts(Version(2, 9, 0))
        assert not VersionRange("^2.0.0").accepts(Version(3, 0, 0))
        assert VersionRange("~2.4.0").accepts(Version(2, 4, 9))
        assert not VersionRange("~2.4.0").accepts(Version(2, 5, 0))
        assert manager.verify_lockfile(project)

        print("\nAll validation assertions passed.")

    except PackageError as exc:
        print(f"PACKAGE MANAGEMENT ERROR: {exc}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
