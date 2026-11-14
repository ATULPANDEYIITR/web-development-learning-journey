#!/usr/bin/env python3
"""
React Effects: useEffect, dependency arrays, cleanup, and side effects.

A dependency-aware effect lifecycle simulator demonstrating:
- Effect execution after committed state changes.
- Dependency comparison using identity/value semantics.
- Cleanup before rerunning an effect.
- Empty and omitted dependency arrays.
- Component unmount behavior.
- Strict Mode development replay.
- Asynchronous task cancellation.
- Resource management and lifecycle validation.

Run: python react_effects.py
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

logger = logging.getLogger("react-effects")

Cleanup = Optional[Callable[[], None]]
Effect = Callable[[], Cleanup]


class LifecycleState(Enum):
    MOUNTED = "mounted"
    UNMOUNTED = "unmounted"


class EffectError(Exception):
    """Base exception for effect lifecycle failures."""


class InvalidDependencyError(EffectError):
    """Raised when dependency configuration is invalid."""


@dataclass
class EffectRecord:
    name: str
    callback: Effect
    dependencies: Optional[tuple[Any, ...]]
    cleanup: Cleanup = None
    initialized: bool = False
    execution_count: int = 0


def same_value(first: Any, second: Any) -> bool:
    """
    Approximate JavaScript Object.is semantics for common Python values.

    Primitive values use value comparison.
    Objects use identity comparison.
    """
    if type(first) is not type(second):
        return False

    if isinstance(first, float):
        if first != first and second != second:
            return True
        if first == 0.0 and second == 0.0:
            return (
                first.hex().startswith("-")
                == second.hex().startswith("-")
            )

    if isinstance(first, (str, int, float, bool, type(None))):
        return first == second

    return first is second


def dependencies_changed(
    previous: Optional[tuple[Any, ...]],
    current: Optional[tuple[Any, ...]]
) -> bool:
    """
    None means dependencies were omitted: execute after every commit.
    An empty tuple means execute only on initial mount.
    """
    if previous is None or current is None:
        return True

    if len(previous) != len(current):
        raise InvalidDependencyError(
            "Dependency array length must remain constant."
        )

    return any(
        not same_value(old, new)
        for old, new in zip(previous, current)
    )


class EffectManager:
    """Manages effect execution and cleanup for one simulated component."""

    def __init__(self, component_name: str):
        self.component_name = component_name
        self.effects: list[EffectRecord] = []
        self.state = LifecycleState.MOUNTED
        self.commit_count = 0

    def register(
        self,
        name: str,
        callback: Effect,
        dependencies: Optional[list[Any]] = None
    ) -> None:
        if self.state is LifecycleState.UNMOUNTED:
            raise EffectError("Cannot register effects after unmount.")

        if not callable(callback):
            raise TypeError("Effect callback must be callable.")

        if any(record.name == name for record in self.effects):
            raise EffectError(f"Duplicate effect name: {name}")

        normalized = (
            None if dependencies is None
            else tuple(dependencies)
        )

        self.effects.append(
            EffectRecord(name, callback, normalized)
        )

    def commit(
        self,
        dependency_updates: Optional[
            dict[str, Optional[list[Any]]]
        ] = None
    ) -> None:
        if self.state is LifecycleState.UNMOUNTED:
            raise EffectError("Cannot commit an unmounted component.")

        updates = dependency_updates or {}
        self.commit_count += 1

        for record in self.effects:
            if record.name in updates:
                new_dependencies = updates[record.name]
                new_dependencies = (
                    None if new_dependencies is None
                    else tuple(new_dependencies)
                )
            else:
                new_dependencies = record.dependencies

            changed = (
                not record.initialized
                or dependencies_changed(
                    record.dependencies,
                    new_dependencies
                )
            )

            if not changed:
                continue

            self._cleanup(record)

            try:
                cleanup = record.callback()

                if cleanup is not None and not callable(cleanup):
                    raise TypeError(
                        "An effect must return a callable cleanup "
                        "or None."
                    )

                record.cleanup = cleanup
                record.execution_count += 1
                record.initialized = True
                record.dependencies = new_dependencies

                logger.info(
                    "%s: executed effect '%s'",
                    self.component_name,
                    record.name
                )

            except Exception:
                record.cleanup = None
                record.initialized = True
                record.dependencies = new_dependencies
                logger.exception(
                    "Effect '%s' failed",
                    record.name
                )
                raise

    @staticmethod
    def _cleanup(record: EffectRecord) -> None:
        if record.cleanup is not None:
            cleanup = record.cleanup
            record.cleanup = None

            logger.info("Cleaning up effect '%s'", record.name)
            cleanup()

    def strict_mode_replay(self) -> None:
        """
        Simulate React development Strict Mode's initial
        setup -> cleanup -> setup cycle.
        """
        if self.state is LifecycleState.UNMOUNTED:
            raise EffectError("Component is unmounted.")

        for record in self.effects:
            if not record.initialized:
                continue

            self._cleanup(record)

            record.initialized = False

        self.commit()

    def unmount(self) -> None:
        if self.state is LifecycleState.UNMOUNTED:
            return

        for record in reversed(self.effects):
            self._cleanup(record)

        self.state = LifecycleState.UNMOUNTED
        logger.info("%s unmounted", self.component_name)


@dataclass
class Subscription:
    channel: str
    active: bool = True

    def close(self) -> None:
        if self.active:
            self.active = False
            logger.info("Closed subscription: %s", self.channel)


class ConnectionService:
    """Simulates a resource that requires explicit cleanup."""

    def __init__(self):
        self.connections: dict[str, Subscription] = {}

    def connect(self, channel: str) -> Subscription:
        if not channel.strip():
            raise ValueError("Channel cannot be empty.")

        existing = self.connections.get(channel)

        if existing and existing.active:
            raise EffectError(
                f"Connection already active: {channel}"
            )

        subscription = Subscription(channel)
        self.connections[channel] = subscription

        logger.info("Connected to %s", channel)
        return subscription

    def active_count(self) -> int:
        return sum(
            connection.active
            for connection in self.connections.values()
        )


class SearchService:
    """Demonstrates asynchronous cancellation with asyncio."""

    async def search(
        self,
        query: str,
        delay: float = 0.2
    ) -> list[str]:
        if not query.strip():
            return []

        await asyncio.sleep(delay)

        return [
            f"Result for {query}: {index}"
            for index in range(1, 4)
        ]


async def demonstrate_async_cleanup() -> None:
    """
    Cancellation prevents an obsolete asynchronous operation
    from publishing a result.
    """
    service = SearchService()
    current_task = asyncio.create_task(
        service.search("react")
    )

    await asyncio.sleep(0.05)

    current_task.cancel()

    try:
        await current_task
    except asyncio.CancelledError:
        logger.info("Obsolete search operation cancelled.")


def demonstrate_dependencies() -> None:
    manager = EffectManager("DependencyDemo")

    count = {"value": 0}

    manager.register(
        "count-effect",
        lambda: (
            count.update(value=count["value"] + 1),
            lambda: logger.info("Count effect cleanup")
        )[1],
        [0]
    )

    manager.commit()
    manager.commit()

    manager.commit({
        "count-effect": [1]
    })

    assert count["value"] == 2

    manager.unmount()


def demonstrate_subscription() -> None:
    service = ConnectionService()
    manager = EffectManager("ChatComponent")

    channel = {"value": "engineering"}

    def subscribe() -> Cleanup:
        subscription = service.connect(channel["value"])
        return subscription.close

    manager.register(
        "chat-subscription",
        subscribe,
        [channel["value"]]
    )

    manager.commit()
    assert service.active_count() == 1

    channel["value"] = "security"

    manager.commit({
        "chat-subscription": [channel["value"]]
    })

    assert service.active_count() == 1

    manager.unmount()
    assert service.active_count() == 0


def demonstrate_omitted_dependencies() -> None:
    executions = {"count": 0}
    manager = EffectManager("EveryCommit")

    manager.register(
        "every-render",
        lambda: executions.update(
            count=executions["count"] + 1
        ),
        None
    )

    manager.commit()
    manager.commit()
    manager.commit()

    assert executions["count"] == 3

    manager.unmount()


def demonstrate_empty_dependencies() -> None:
    executions = {"count": 0}
    manager = EffectManager("MountOnly")

    manager.register(
        "mount-effect",
        lambda: executions.update(
            count=executions["count"] + 1
        ),
        []
    )

    manager.commit()
    manager.commit()
    manager.commit()

    assert executions["count"] == 1

    manager.unmount()


def demonstrate_strict_mode() -> None:
    manager = EffectManager("StrictModeDemo")
    events: list[str] = []

    def effect() -> Cleanup:
        events.append("setup")

        def cleanup() -> None:
            events.append("cleanup")

        return cleanup

    manager.register("strict-effect", effect, [])
    manager.commit()

    manager.strict_mode_replay()

    assert events == [
        "setup",
        "cleanup",
        "setup"
    ]

    manager.unmount()

    assert events[-1] == "cleanup"


def demonstrate_validation() -> None:
    manager = EffectManager("ValidationDemo")

    try:
        manager.register(
            "invalid-effect",
            lambda: "not a cleanup function",
            []
        )
        manager.commit()
    except TypeError:
        logger.info("Invalid cleanup return value rejected.")

    manager.unmount()


def main() -> None:
    logger.info("Starting React Effects lifecycle demonstrations")

    demonstrate_dependencies()
    demonstrate_subscription()
    demonstrate_omitted_dependencies()
    demonstrate_empty_dependencies()
    demonstrate_strict_mode()
    demonstrate_validation()

    asyncio.run(demonstrate_async_cleanup())

    logger.info("All assertions passed.")


if __name__ == "__main__":
    main()
