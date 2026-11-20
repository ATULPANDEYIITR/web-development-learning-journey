from __future__ import annotations

import hashlib
import json
import statistics
import time
from collections import defaultdict
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Callable, Optional


# ============================================================
# REACT PERFORMANCE ENGINEERING
# Memoization, Rendering, Code Splitting, and Lazy Loading
# ============================================================

class PerformanceError(Exception):
    pass


class ValidationError(PerformanceError):
    pass


def validate_component_name(name: str) -> None:
    if not isinstance(name, str) or not name.strip():
        raise ValidationError("Component name must be a non-empty string.")


def shallow_equal(first: dict, second: dict) -> bool:
    """Compare property keys and their immediate values."""
    if first.keys() != second.keys():
        return False

    return all(first[key] is second[key] or first[key] == second[key]
               for key in first)


def stable_key(value: Any) -> str:
    """Create a deterministic key for memoized computations."""
    try:
        serialized = json.dumps(value, sort_keys=True, default=str)
    except (TypeError, ValueError) as exc:
        raise ValidationError("Value cannot be serialized.") from exc

    return hashlib.sha256(serialized.encode()).hexdigest()


# ============================================================
# 1. COMPONENT RENDERING
# ============================================================

@dataclass
class Component:
    name: str
    render_function: Callable[[dict], Any]
    memoized: bool = False
    previous_props: Optional[dict] = None
    previous_output: Any = None
    render_count: int = 0
    skipped_count: int = 0

    def render(self, props: dict) -> Any:
        validate_component_name(self.name)

        if not isinstance(props, dict):
            raise ValidationError("Component props must be a dictionary.")

        if self.memoized and self.previous_props is not None:
            if shallow_equal(self.previous_props, props):
                self.skipped_count += 1
                return self.previous_output

        self.render_count += 1
        output = self.render_function(props)

        self.previous_props = props.copy()
        self.previous_output = output

        return output


class ComponentTree:
    """Simulates parent-child rendering and memoization."""

    def __init__(self):
        self.components: dict[str, Component] = {}

    def register(self, component: Component) -> None:
        if component.name in self.components:
            raise ValidationError(
                f"Component already registered: {component.name}"
            )
        self.components[component.name] = component

    def render(self, name: str, props: dict) -> Any:
        if name not in self.components:
            raise ValidationError(f"Unknown component: {name}")

        return self.components[name].render(props)

    def report(self) -> list[dict]:
        return [
            {
                "component": component.name,
                "renders": component.render_count,
                "skipped": component.skipped_count,
            }
            for component in self.components.values()
        ]


# ============================================================
# 2. MEMOIZED COMPUTATION
# ============================================================

class MemoCache:
    """Bounded cache with least-recently-used eviction."""

    def __init__(self, max_entries: int = 128):
        if max_entries < 1:
            raise ValidationError("Cache capacity must be positive.")

        self.max_entries = max_entries
        self.cache: dict[str, Any] = {}
        self.order: list[str] = []
        self.hits = 0
        self.misses = 0

    def compute(self, key: Any, function: Callable[[], Any]) -> Any:
        cache_key = stable_key(key)

        if cache_key in self.cache:
            self.hits += 1
            self.order.remove(cache_key)
            self.order.append(cache_key)
            return self.cache[cache_key]

        self.misses += 1
        result = function()

        if len(self.cache) >= self.max_entries:
            oldest = self.order.pop(0)
            del self.cache[oldest]

        self.cache[cache_key] = result
        self.order.append(cache_key)

        return result

    def clear(self) -> None:
        self.cache.clear()
        self.order.clear()

    def statistics(self) -> dict:
        total = self.hits + self.misses
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(self.hits / total, 3) if total else 0,
            "entries": len(self.cache),
        }


@lru_cache(maxsize=128)
def expensive_tax_calculation(price: float, tax_rate: float) -> float:
    return round(price * tax_rate, 2)


# ============================================================
# 3. APPLICATION STATE AND RENDERING
# ============================================================

@dataclass
class ApplicationState:
    search_query: str = ""
    selected_category: str = "all"
    items: list[dict] = field(default_factory=list)
    revision: int = 0

    def update_search(self, query: str) -> None:
        if not isinstance(query, str):
            raise ValidationError("Search query must be text.")

        self.search_query = query.strip()
        self.revision += 1

    def update_category(self, category: str) -> None:
        if not isinstance(category, str) or not category.strip():
            raise ValidationError("Invalid category.")

        self.selected_category = category
        self.revision += 1


class ProductService:
    """Separates data processing from component rendering."""

    def __init__(self, items: list[dict]):
        self.items = items
        self.cache = MemoCache(max_entries=64)

    def filter_products(self, query: str, category: str) -> list[dict]:
        key = (query.casefold(), category)

        def calculate():
            return [
                item for item in self.items
                if query.casefold() in item["name"].casefold()
                and (
                    category == "all"
                    or item["category"] == category
                )
            ]

        return self.cache.compute(key, calculate)


# ============================================================
# 4. CODE SPLITTING AND LAZY LOADING
# ============================================================

class ModuleState:
    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    FAILED = "failed"


@dataclass
class LazyModule:
    name: str
    loader: Callable[[], Any]
    state: str = ModuleState.UNLOADED
    result: Any = None
    error: Optional[str] = None
    load_count: int = 0

    def load(self) -> Any:
        if self.state == ModuleState.LOADED:
            return self.result

        if self.state == ModuleState.LOADING:
            raise PerformanceError("Module loading is already in progress.")

        if self.state == ModuleState.FAILED:
            raise PerformanceError(
                f"Module previously failed: {self.error}"
            )

        self.state = ModuleState.LOADING
        self.load_count += 1

        try:
            self.result = self.loader()
            self.state = ModuleState.LOADED
            return self.result
        except Exception as exc:
            self.state = ModuleState.FAILED
            self.error = str(exc)
            raise PerformanceError(
                f"Unable to load module {self.name}: {exc}"
            ) from exc


class ModuleRegistry:
    def __init__(self):
        self.modules: dict[str, LazyModule] = {}

    def register(self, module: LazyModule) -> None:
        if module.name in self.modules:
            raise ValidationError("Duplicate module registration.")

        self.modules[module.name] = module

    def load(self, name: str) -> Any:
        if name not in self.modules:
            raise ValidationError(f"Unknown module: {name}")

        return self.modules[name].load()

    def report(self) -> list[dict]:
        return [
            {
                "module": module.name,
                "state": module.state,
                "loads": module.load_count,
            }
            for module in self.modules.values()
        ]


# ============================================================
# 5. RENDER PERFORMANCE MEASUREMENT
# ============================================================

class PerformanceMonitor:
    def __init__(self):
        self.measurements = defaultdict(list)

    def measure(self, name: str, function: Callable, *args, **kwargs):
        start = time.perf_counter()

        try:
            return function(*args, **kwargs)
        finally:
            elapsed = (time.perf_counter() - start) * 1000
            self.measurements[name].append(elapsed)

    def report(self) -> dict:
        result = {}

        for name, values in self.measurements.items():
            result[name] = {
                "calls": len(values),
                "average_ms": round(statistics.mean(values), 4),
                "maximum_ms": round(max(values), 4),
            }

        return result


# ============================================================
# 6. APPLICATION SIMULATION
# ============================================================

def build_application():
    products = [
        {"id": 1, "name": "Laptop", "category": "electronics",
         "price": 75000},
        {"id": 2, "name": "Keyboard", "category": "electronics",
         "price": 2500},
        {"id": 3, "name": "Office Chair", "category": "furniture",
         "price": 12000},
        {"id": 4, "name": "Monitor", "category": "electronics",
         "price": 18000},
        {"id": 5, "name": "Desk", "category": "furniture",
         "price": 15000},
    ]

    state = ApplicationState(items=products)
    service = ProductService(products)
    tree = ComponentTree()
    monitor = PerformanceMonitor()

    def product_list(props):
        return {
            "products": props["products"],
            "count": len(props["products"]),
        }

    def product_summary(props):
        return {
            "total": len(props["products"]),
            "selected_category": props["category"],
        }

    tree.register(
        Component("ProductList", product_list, memoized=True)
    )
    tree.register(
        Component("ProductSummary", product_summary, memoized=True)
    )

    return state, service, tree, monitor


def demonstrate():
    print("\nREACT PERFORMANCE ENGINEERING")
    print("=" * 55)

    state, service, tree, monitor = build_application()

    # Initial render.
    filtered = service.filter_products("", "all")

    monitor.measure(
        "product_list",
        tree.render,
        "ProductList",
        {"products": filtered},
    )

    monitor.measure(
        "product_summary",
        tree.render,
        "ProductSummary",
        {"products": filtered, "category": "all"},
    )

    # An unchanged render can reuse memoized component output.
    tree.render("ProductList", {"products": filtered})

    # State changes cause new derived values and rendering.
    state.update_search("monitor")
    filtered = service.filter_products(
        state.search_query,
        state.selected_category,
    )

    tree.render("ProductList", {"products": filtered})
    tree.render(
        "ProductSummary",
        {"products": filtered, "category": state.selected_category},
    )

    # Repeated expensive calculations reuse cached results.
    tax_one = expensive_tax_calculation(1000.0, 0.18)
    tax_two = expensive_tax_calculation(1000.0, 0.18)

    assert tax_one == tax_two == 180.0

    # Lazy modules represent independently loaded application features.
    registry = ModuleRegistry()

    registry.register(
        LazyModule(
            "analytics",
            lambda: {
                "feature": "analytics",
                "charts": ["revenue", "orders", "conversion"],
            },
        )
    )

    registry.register(
        LazyModule(
            "admin",
            lambda: {
                "feature": "admin",
                "permissions": ["read", "write"],
            },
        )
    )

    print("\nLazy loading before navigation:")
    print(json.dumps(registry.report(), indent=2))

    analytics = registry.load("analytics")
    registry.load("analytics")

    assert analytics["feature"] == "analytics"

    print("\nLoaded analytics:")
    print(analytics)

    print("\nComponent rendering:")
    print(json.dumps(tree.report(), indent=2))

    print("\nMemoization cache:")
    print(json.dumps(service.cache.statistics(), indent=2))

    print("\nLazy module states:")
    print(json.dumps(registry.report(), indent=2))

    print("\nPerformance measurements:")
    print(json.dumps(monitor.report(), indent=2))

    print("\nValidation:")
    assert state.revision == 1
    assert len(filtered) == 1
    assert tree.components["ProductList"].render_count == 2
    assert tree.components["ProductList"].skipped_count == 1

    print("All assertions passed.")


if __name__ == "__main__":
    demonstrate()
