"""
React Hooks: useRef, useMemo, useCallback, and Custom Hooks.

A self-contained educational hook-runtime simulator.
Python 3.10+; standard library only.

The simulator demonstrates:
- Component render cycles and hook ordering.
- Persistent references through useRef.
- Dependency-based caching through useMemo.
- Function identity caching through useCallback.
- Custom hooks composed from primitive hooks.
- State updates and rerendering.
- Dependency comparison and invalid hook usage.
- Hook lifecycle validation and performance counters.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Generic, Optional, TypeVar
import math
import unittest


T = TypeVar("T")
U = TypeVar("U")


class HookError(RuntimeError):
    """Raised when hook lifecycle rules are violated."""


class HookOrderError(HookError):
    """Raised when hook ordering changes between renders."""


class HookTypeError(HookError):
    """Raised when a hook slot is reused for another hook type."""


def object_is(left: Any, right: Any) -> bool:
    """
    Approximate JavaScript Object.is semantics.

    Primitive values use value comparison.
    Mutable objects use identity comparison.
    NaN equals NaN and positive zero differs from negative zero.
    """
    if left is right:
        return True

    if isinstance(left, float) and isinstance(right, float):
        if math.isnan(left) and math.isnan(right):
            return True

        if left == 0.0 and right == 0.0:
            return math.copysign(1.0, left) == math.copysign(1.0, right)

    primitive_types = (str, int, float, bool, type(None))

    if type(left) is type(right) and isinstance(left, primitive_types):
        return left == right

    return False


def dependencies_equal(
    previous: Optional[tuple[Any, ...]],
    current: Optional[tuple[Any, ...]]
) -> bool:
    """Compare dependency sequences using Object.is-like semantics."""
    if previous is None or current is None:
        return False

    if len(previous) != len(current):
        raise HookError("Dependency array length must remain constant.")

    return all(
        object_is(old, new)
        for old, new in zip(previous, current)
    )


@dataclass
class Ref(Generic[T]):
    """A mutable reference whose identity survives component renders."""
    current: T


@dataclass
class HookSlot:
    kind: str
    value: Any
    dependencies: Optional[tuple[Any, ...]] = None
    initialized: bool = True


@dataclass
class RenderMetrics:
    renders: int = 0
    memo_computations: int = 0
    memo_cache_hits: int = 0
    callback_creations: int = 0
    callback_cache_hits: int = 0
    state_updates: int = 0


class HookRuntime:
    """
    Simplified hook dispatcher.

    Each component instance owns an ordered collection of hook slots.
    Hook calls must occur in the same order during every render.
    """

    def __init__(self, component_name: str):
        self.component_name = component_name
        self.slots: list[HookSlot] = []
        self.expected_order: Optional[list[str]] = None
        self.cursor = 0
        self.rendering = False
        self.metrics = RenderMetrics()

    def _next_slot(self, kind: str) -> HookSlot:
        if not self.rendering:
            raise HookError("Hooks must execute during component rendering.")

        index = self.cursor
        self.cursor += 1

        if index < len(self.slots):
            slot = self.slots[index]

            if slot.kind != kind:
                raise HookTypeError(
                    f"Hook position {index}: expected {slot.kind}, got {kind}."
                )

            return slot

        slot = HookSlot(kind=kind, value=None)
        self.slots.append(slot)
        return slot

    def use_state(
        self,
        initial: T
    ) -> tuple[T, Callable[[T | Callable[[T], T]], None]]:
        """Maintain component state across renders."""
        slot = self._next_slot("state")

        if not slot.initialized:
            slot.value = initial
            slot.initialized = True

        def set_state(
            update: T | Callable[[T], T]
        ) -> None:
            if callable(update):
                new_value = update(slot.value)
            else:
                new_value = update

            if not object_is(slot.value, new_value):
                slot.value = new_value
                self.metrics.state_updates += 1

        return slot.value, set_state

    def use_ref(self, initial: T) -> Ref[T]:
        """
        Return the same reference object on every render.

        Changing current does not trigger a render.
        """
        slot = self._next_slot("ref")

        if not slot.initialized:
            slot.value = Ref(initial)
            slot.initialized = True

        return slot.value

    def use_memo(
        self,
        factory: Callable[[], T],
        dependencies: Optional[tuple[Any, ...]]
    ) -> T:
        """Cache a computed value until dependencies change."""
        slot = self._next_slot("memo")

        if (
            not slot.initialized
            or not dependencies_equal(slot.dependencies, dependencies)
        ):
            slot.value = factory()
            slot.dependencies = dependencies
            slot.initialized = True
            self.metrics.memo_computations += 1
        else:
            self.metrics.memo_cache_hits += 1

        return slot.value

    def use_callback(
        self,
        callback: Callable[..., T],
        dependencies: Optional[tuple[Any, ...]]
    ) -> Callable[..., T]:
        """Cache a function reference using dependency comparison."""
        slot = self._next_slot("callback")

        if (
            not slot.initialized
            or not dependencies_equal(slot.dependencies, dependencies)
        ):
            slot.value = callback
            slot.dependencies = dependencies
            slot.initialized = True
            self.metrics.callback_creations += 1
        else:
            self.metrics.callback_cache_hits += 1

        return slot.value

    def render(self, component: Callable[..., T], *args: Any) -> T:
        """Execute one component render and validate hook ordering."""
        if self.rendering:
            raise HookError("Nested rendering on the same runtime is invalid.")

        self.cursor = 0
        self.rendering = True

        try:
            result = component(self, *args)

            current_order = [
                slot.kind for slot in self.slots
            ]

            if self.expected_order is None:
                self.expected_order = current_order.copy()
            elif current_order != self.expected_order:
                raise HookOrderError(
                    "Component hook order changed between renders."
                )

            if self.cursor != len(self.slots):
                raise HookOrderError(
                    "Some hooks were skipped during rendering."
                )

            self.metrics.renders += 1
            return result

        finally:
            self.rendering = False


# ---------------------------------------------------------
# Custom hooks
# ---------------------------------------------------------

def use_previous(
    runtime: HookRuntime,
    current_value: T
) -> Optional[T]:
    """Return the value observed during the previous render."""
    reference = runtime.use_ref(None)
    previous = reference.current
    reference.current = current_value
    return previous


def use_counter(
    runtime: HookRuntime,
    initial: int = 0
) -> tuple[int, Callable[[int], None], Callable[[], None]]:
    """
    A custom hook combining state and callback hooks.

    Returns current value, setter, and increment function.
    """
    count, set_count = runtime.use_state(initial)

    increment = runtime.use_callback(
        lambda: set_count(lambda previous: previous + 1),
        ()
    )

    return count, set_count, increment


def use_expensive_filter(
    runtime: HookRuntime,
    records: tuple[dict[str, Any], ...],
    minimum_score: int
) -> tuple[dict[str, Any], ...]:
    """Filter records only when inputs change."""
    return runtime.use_memo(
        lambda: tuple(
            record
            for record in records
            if record["score"] >= minimum_score
        ),
        (records, minimum_score)
    )


# ---------------------------------------------------------
# Example component
# ---------------------------------------------------------

RECORDS = (
    {"id": 1, "name": "Repository A", "score": 92},
    {"id": 2, "name": "Repository B", "score": 67},
    {"id": 3, "name": "Repository C", "score": 85},
    {"id": 4, "name": "Repository D", "score": 43},
)


def dashboard(
    runtime: HookRuntime,
    records: tuple[dict[str, Any], ...],
    minimum_score: int
) -> dict[str, Any]:
    """A component-like function demonstrating multiple hooks."""

    count, set_count, increment = use_counter(runtime)

    render_reference = runtime.use_ref(0)
    render_reference.current += 1

    previous_threshold = use_previous(
        runtime,
        minimum_score
    )

    filtered = use_expensive_filter(
        runtime,
        records,
        minimum_score
    )

    selected_ids = runtime.use_memo(
        lambda: frozenset(item["id"] for item in filtered),
        (filtered,)
    )

    select_record = runtime.use_callback(
        lambda record_id: record_id in selected_ids,
        (selected_ids,)
    )

    return {
        "count": count,
        "filtered_records": filtered,
        "selected_ids": selected_ids,
        "is_selected": select_record,
        "render_number": render_reference.current,
        "previous_threshold": previous_threshold,
        "increment": increment,
        "set_count": set_count,
    }


# ---------------------------------------------------------
# Dependency and lifecycle examples
# ---------------------------------------------------------

def demonstrate() -> None:
    runtime = HookRuntime("RepositoryDashboard")

    first = runtime.render(dashboard, RECORDS, 70)

    second = runtime.render(dashboard, RECORDS, 70)

    assert first["count"] == 0
    assert second["count"] == 0

    assert len(first["filtered_records"]) == 2
    assert first["filtered_records"] is second["filtered_records"]

    assert first["is_selected"] is second["is_selected"]

    assert first["render_number"] == 1
    assert second["render_number"] == 2

    assert first["previous_threshold"] is None
    assert second["previous_threshold"] == 70

    second["increment"]()

    third = runtime.render(dashboard, RECORDS, 70)

    assert third["count"] == 1
    assert third["render_number"] == 3

    fourth = runtime.render(dashboard, RECORDS, 80)

    assert fourth["count"] == 1
    assert fourth["previous_threshold"] == 70
    assert len(fourth["filtered_records"]) == 2

    print("Dashboard records:")
    for record in fourth["filtered_records"]:
        print(f"  {record['name']}: {record['score']}")

    print("\nRender metrics:")
    print(f"  Renders: {runtime.metrics.renders}")
    print(f"  Memo computations: {runtime.metrics.memo_computations}")
    print(f"  Memo cache hits: {runtime.metrics.memo_cache_hits}")
    print(f"  Callback creations: {runtime.metrics.callback_creations}")
    print(f"  Callback cache hits: {runtime.metrics.callback_cache_hits}")
    print(f"  State updates: {runtime.metrics.state_updates}")


# ---------------------------------------------------------
# Automated tests
# ---------------------------------------------------------

class HookRuntimeTests(unittest.TestCase):

    def test_ref_identity(self):
        runtime = HookRuntime("RefTest")

        def component(rt):
            return rt.use_ref(10)

        first = runtime.render(component)
        first.current = 50
        second = runtime.render(component)

        self.assertIs(first, second)
        self.assertEqual(second.current, 50)

    def test_memo_cache(self):
        runtime = HookRuntime("MemoTest")
        computations = {"count": 0}

        def component(rt, value):
            def calculate():
                computations["count"] += 1
                return value * 10

            return rt.use_memo(calculate, (value,))

        self.assertEqual(runtime.render(component, 5), 50)
        self.assertEqual(runtime.render(component, 5), 50)
        self.assertEqual(runtime.render(component, 6), 60)

        self.assertEqual(computations["count"], 2)

    def test_callback_identity(self):
        runtime = HookRuntime("CallbackTest")

        def component(rt, value):
            return rt.use_callback(lambda: value, (value,))

        first = runtime.render(component, 10)
        second = runtime.render(component, 10)
        third = runtime.render(component, 20)

        self.assertIs(first, second)
        self.assertIsNot(second, third)

    def test_dependency_length(self):
        runtime = HookRuntime("DependencyTest")

        def component(rt, dependencies):
            return rt.use_memo(lambda: 1, dependencies)

        runtime.render(component, (1, 2))

        with self.assertRaises(HookError):
            runtime.render(component, (1, 2, 3))

    def test_hook_order(self):
        runtime = HookRuntime("OrderTest")

        def component(rt, use_reference):
            if use_reference:
                return rt.use_ref(1)
            return rt.use_state(0)

        runtime.render(component, True)

        with self.assertRaises(HookTypeError):
            runtime.render(component, False)

    def test_hooks_outside_render(self):
        runtime = HookRuntime("InvalidTest")

        with self.assertRaises(HookError):
            runtime.use_ref(10)

    def test_nan_dependencies(self):
        runtime = HookRuntime("NaNTest")
        calls = {"count": 0}

        def component(rt):
            return rt.use_memo(
                lambda: calls.update(count=calls["count"] + 1),
                (float("nan"),)
            )

        runtime.render(component)
        runtime.render(component)

        self.assertEqual(calls["count"], 1)


if __name__ == "__main__":
    demonstrate()

    print("\nRunning hook tests...")
    unittest.main(argv=["react_hooks"], exit=False)
