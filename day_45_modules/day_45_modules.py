#!/usr/bin/env python3
"""Executable module architecture laboratory.

Demonstrates module boundaries, named and default export conventions,
dependency graphs, circular dependency detection, import caching, and
dependency-injection-based application composition using Python analogues.

Run:
    python module_architecture.py

Only the Python standard library is required.
"""

from __future__ import annotations

import ast
import hashlib
import importlib
import importlib.util
import json
import sys
import tempfile
import textwrap
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Callable


def section(title: str) -> None:
    print(f"\n{'=' * 72}\n{title}\n{'=' * 72}")


# A Python module exposes names through its namespace. This models the
# explicit public API that a JavaScript ES module would expose with exports.
class CurrencyFormatter:
    def format_amount(self, amount: float, currency: str = "USD") -> str:
        if not isinstance(amount, (int, float)) or isinstance(amount, bool):
            raise TypeError("amount must be a number")
        if currency not in {"USD", "EUR", "INR"}:
            raise ValueError(f"Unsupported currency: {currency}")
        symbols = {"USD": "$", "EUR": "€", "INR": "₹"}
        return f"{symbols[currency]}{amount:,.2f}"


def calculate_subtotal(prices: list[float]) -> float:
    if not prices:
        return 0.0
    if any(
        not isinstance(price, (int, float))
        or isinstance(price, bool)
        or price < 0
        for price in prices
    ):
        raise ValueError("Prices must be non-negative numbers")
    return round(sum(prices), 2)


# This explicit public surface is analogous to named exports. Internal
# helpers remain implementation details.
def _apply_discount(subtotal: float, rate: float) -> float:
    if not 0 <= rate <= 1:
        raise ValueError("Discount rate must be between 0 and 1")
    return round(subtotal * (1 - rate), 2)


def create_invoice(
    prices: list[float],
    formatter: CurrencyFormatter,
    currency: str = "USD",
    discount_rate: float = 0.0,
) -> dict[str, Any]:
    subtotal = calculate_subtotal(prices)
    total = _apply_discount(subtotal, discount_rate)
    return {
        "item_count": len(prices),
        "subtotal": subtotal,
        "discount_rate": discount_rate,
        "total": total,
        "formatted_total": formatter.format_amount(total, currency),
    }


@dataclass(frozen=True)
class ModuleManifest:
    name: str
    path: str
    imports: tuple[str, ...]
    exports: tuple[str, ...]
    default_export: str | None = None


def analyze_es_module(source: str, name: str) -> ModuleManifest:
    """Inspect common static ES module declarations without executing code.

    This is a teaching-oriented analyzer, not a complete JavaScript parser.
    It recognizes common import/export forms and deliberately avoids claiming
    support for every valid JavaScript grammar production.
    """
    imports: list[str] = []
    exports: list[str] = []
    default_export: str | None = None

    import_patterns = (
        r"""import\s+(?:[^;]*?\s+from\s+)?["']([^"']+)["']""",
        r"""import\s*\(\s*["']([^"']+)["']\s*\)""",
    )
    export_patterns = (
        r"\bexport\s+(?:async\s+)?function\s+([A-Za-z_$][\w$]*)",
        r"\bexport\s+class\s+([A-Za-z_$][\w$]*)",
        r"\bexport\s+(?:const|let|var)\s+([A-Za-z_$][\w$]*)",
    )

    import_pattern = __import__("re").compile("|".join(import_patterns))
    for match in import_pattern.finditer(source):
        specifier = next((group for group in match.groups() if group), None)
        if specifier and specifier not in imports:
            imports.append(specifier)

    for pattern in export_patterns:
        exports.extend(__import__("re").findall(pattern, source))

    if __import__("re").search(r"\bexport\s*\{", source):
        for match in __import__("re").finditer(
            r"\bexport\s*\{([^}]+)\}", source
        ):
            for item in match.group(1).split(","):
                item = item.strip()
                if not item:
                    continue
                original = item.split(" as ")[-1].strip()
                exports.append(original)

    if __import__("re").search(r"\bexport\s+default\b", source):
        default_export = "default"

    return ModuleManifest(
        name=name,
        path=name,
        imports=tuple(imports),
        exports=tuple(dict.fromkeys(exports)),
        default_export=default_export,
    )


def build_dependency_graph(
    manifests: list[ModuleManifest],
) -> dict[str, set[str]]:
    """Resolve relative module specifiers to known manifest paths."""
    known_paths = {manifest.path for manifest in manifests}
    graph: dict[str, set[str]] = {path: set() for path in known_paths}

    for manifest in manifests:
        parent = Path(manifest.path).parent
        for specifier in manifest.imports:
            if not specifier.startswith("."):
                continue

            resolved = str((parent / specifier).as_posix())
            candidates = [
                resolved,
                resolved + ".js",
                resolved + ".mjs",
                str(Path(resolved) / "index.js"),
            ]
            target = next((item for item in candidates if item in known_paths), None)
            if target:
                graph[manifest.path].add(target)

    return graph


def find_cycles(graph: dict[str, set[str]]) -> list[list[str]]:
    """Use depth-first search to identify dependency cycles."""
    state: dict[str, int] = {node: 0 for node in graph}
    stack: list[str] = []
    cycles: list[list[str]] = []

    def visit(node: str) -> None:
        state[node] = 1
        stack.append(node)

        for neighbor in graph[node]:
            if neighbor not in graph:
                continue
            if state[neighbor] == 0:
                visit(neighbor)
            elif state[neighbor] == 1:
                start = stack.index(neighbor)
                cycle = stack[start:] + [neighbor]
                if cycle not in cycles:
                    cycles.append(cycle)

        stack.pop()
        state[node] = 2

    for node in graph:
        if state[node] == 0:
            visit(node)

    return cycles


def topological_order(graph: dict[str, set[str]]) -> list[str]:
    """Return dependencies before dependents, or reject a cyclic graph."""
    dependencies = {node: set(edges) for node, edges in graph.items()}
    reverse: dict[str, set[str]] = defaultdict(set)

    for node, edges in dependencies.items():
        for dependency in edges:
            reverse[dependency].add(node)

    ready = deque(sorted(node for node, edges in dependencies.items() if not edges))
    result: list[str] = []

    while ready:
        node = ready.popleft()
        result.append(node)

        for dependent in sorted(reverse[node]):
            dependencies[dependent].discard(node)
            if not dependencies[dependent]:
                ready.append(dependent)

    if len(result) != len(graph):
        raise ValueError("Cannot topologically order a cyclic module graph")

    return result


def demonstrate_application_composition() -> None:
    section("Public APIs and dependency injection")

    formatter = CurrencyFormatter()
    invoice = create_invoice(
        [1299.99, 249.50, 80.00],
        formatter,
        currency="INR",
        discount_rate=0.10,
    )
    print(json.dumps(invoice, indent=2, ensure_ascii=False))

    try:
        create_invoice([-10], formatter)
    except ValueError as error:
        print(f"Input validation rejected the invoice: {error}")

    try:
        formatter.format_amount(10, "GBP")
    except ValueError as error:
        print(f"Unsupported currency rejected: {error}")

    # A module should depend on a narrow contract, not a hidden global object.
    # Replacing the formatter makes the consumer independently testable.
    class TestFormatter:
        def format_amount(self, amount: float, currency: str = "USD") -> str:
            return f"TEST[{currency}:{amount:.2f}]"

    test_invoice = create_invoice([20, 30], TestFormatter())
    assert test_invoice["formatted_total"] == "TEST[USD:50.00]"
    print("Injected formatter test passed.")


def demonstrate_es_module_analysis() -> None:
    section("ES module exports and import relationships")

    sources = {
        "src/money.js": """
            export const currencies = ["USD", "EUR", "INR"];
            export function formatMoney(amount, currency) {
                return `${currency} ${amount.toFixed(2)}`;
            }
            export default formatMoney;
        """,
        "src/invoice.js": """
            import formatMoney, { currencies } from "./money.js";
            import { validateItems } from "./validation.js";
            export function createInvoice(items) {
                validateItems(items);
                return formatMoney(items.length, currencies[0]);
            }
        """,
        "src/validation.js": """
            export function validateItems(items) {
                if (!Array.isArray(items)) throw new TypeError("items required");
            }
        """,
    }

    manifests = [
        analyze_es_module(source, path)
        for path, source in sources.items()
    ]

    for manifest in manifests:
        print(
            f"{manifest.path}: imports={list(manifest.imports)}, "
            f"named_exports={list(manifest.exports)}, "
            f"default_export={manifest.default_export}"
        )

    graph = build_dependency_graph(manifests)
    print("Dependency graph:")
    for module, dependencies in sorted(graph.items()):
        print(f"  {module} -> {sorted(dependencies)}")

    print("Dependency-first order:", topological_order(graph))

    cyclic_sources = {
        "src/a.js": 'import { b } from "./b.js"; export const a = 1;',
        "src/b.js": 'import { a } from "./a.js"; export const b = 2;',
    }
    cyclic_manifests = [
        analyze_es_module(source, path)
        for path, source in cyclic_sources.items()
    ]
    cycles = find_cycles(build_dependency_graph(cyclic_manifests))
    print("Detected circular dependencies:", cycles)

    try:
        topological_order(build_dependency_graph(cyclic_manifests))
    except ValueError as error:
        print("Build-order validation:", error)


def demonstrate_real_imports_and_cache() -> None:
    section("Runtime module resolution and caching")

    # Temporary files allow the script to test Python's real import machinery
    # without modifying the user's project or leaving generated files behind.
    with tempfile.TemporaryDirectory(prefix="module_lab_") as directory:
        root = Path(directory)
        package = root / "billing_demo"
        package.mkdir()

        (package / "__init__.py").write_text(
            'from .pricing import calculate_total\n'
            '__all__ = ["calculate_total"]\n',
            encoding="utf-8",
        )
        (package / "pricing.py").write_text(
            "def calculate_total(prices):\n"
            "    if any(price < 0 for price in prices):\n"
            "        raise ValueError('negative price')\n"
            "    return round(sum(prices), 2)\n",
            encoding="utf-8",
        )

        sys.path.insert(0, str(root))
        try:
            package_module = importlib.import_module("billing_demo")
            pricing_module = importlib.import_module("billing_demo.pricing")

            first = importlib.import_module("billing_demo.pricing")
            assert first is pricing_module
            print("Package API result:", package_module.calculate_total([12.5, 7.5]))
            print("Repeated import reuses cached module:", first is pricing_module)
            print(
                "Explicit public names:",
                getattr(package_module, "__all__", []),
            )

            try:
                package_module.calculate_total([5, -1])
            except ValueError as error:
                print("Module function rejected invalid input:", error)
        finally:
            sys.path.remove(str(root))
            for name in ("billing_demo.pricing", "billing_demo"):
                sys.modules.pop(name, None)
            importlib.invalidate_caches()


def demonstrate_architecture_invariants() -> None:
    section("Architecture checks")

    source_files = {
        "src/domain/invoice.js": (
            "export function calculateTotal(items) { "
            "return items.reduce((sum, item) => sum + item.price, 0); }"
        ),
        "src/application/create-invoice.js": (
            'import { calculateTotal } from "../domain/invoice.js"; '
            "export function createInvoice(items) { "
            "return { total: calculateTotal(items) }; }"
        ),
        "src/ui/invoice-screen.js": (
            'import { createInvoice } from "../application/create-invoice.js"; '
            "export function renderInvoice(items) { return createInvoice(items); }"
        ),
    }

    manifests = [
        analyze_es_module(source, path)
        for path, source in source_files.items()
    ]
    graph = build_dependency_graph(manifests)
    order = topological_order(graph)

    # This simple layer check encodes a project-specific dependency rule.
    # Domain modules must not import application or UI modules.
    forbidden = {
        "src/domain/invoice.js": ("src/application/", "src/ui/"),
        "src/application/create-invoice.js": ("src/ui/",),
    }

    violations: list[str] = []
    for source, targets in graph.items():
        for target in targets:
            for prefix in forbidden.get(source, ()):
                if target.startswith(prefix):
                    violations.append(f"{source} must not depend on {target}")

    print("Build order:", order)
    if violations:
        raise RuntimeError("; ".join(violations))
    print("Layer dependency rules passed.")

    # Stable fingerprints help illustrate how a build tool can track changes.
    for path, source in sorted(source_files.items()):
        digest = hashlib.sha256(source.encode("utf-8")).hexdigest()[:12]
        print(f"{path}: sha256={digest}")


def run_self_tests() -> None:
    section("Executable assertions")

    formatter = CurrencyFormatter()
    assert calculate_subtotal([]) == 0.0
    assert calculate_subtotal([10.0, 2.5]) == 12.5
    assert create_invoice([100], formatter, discount_rate=0.25)["total"] == 75.0

    for invalid in ([-1], [True], ["10"], [float("nan")]):
        try:
            calculate_subtotal(invalid)  # type: ignore[arg-type]
        except (ValueError, TypeError):
            pass
        else:
            raise AssertionError(f"Invalid prices were accepted: {invalid!r}")

    assert analyze_es_module(
        'export const answer = 42; export default answer;',
        "sample.js",
    ).default_export == "default"

    assert find_cycles({"a.js": {"b.js"}, "b.js": {"a.js"}})
    assert topological_order({"domain.js": set(), "app.js": {"domain.js"}}) == [
        "domain.js",
        "app.js",
    ]

    print("All assertions passed.")


def main() -> None:
    demonstrate_application_composition()
    demonstrate_es_module_analysis()
    demonstrate_real_imports_and_cache()
    demonstrate_architecture_invariants()
    run_self_tests()


if __name__ == "__main__":
    main()
