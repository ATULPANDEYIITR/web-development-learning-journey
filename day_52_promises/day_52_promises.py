from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass
from typing import Any, Awaitable, Callable


class PromiseStateError(Exception):
    """Raised when an operation violates Promise settlement rules."""


@dataclass(frozen=True)
class Result:
    name: str
    value: Any = None
    error: BaseException | None = None


async def delayed_value(name: str, delay: float, value: Any) -> Result:
    await asyncio.sleep(delay)
    return Result(name=name, value=value)


async def delayed_failure(name: str, delay: float, message: str) -> Result:
    await asyncio.sleep(delay)
    raise RuntimeError(f"{name}: {message}")


async def demonstrate_basic_coroutine() -> None:
    result = await delayed_value("configuration", 0.05, {"timeout": 30})
    print("basic resolution:", result)


async def demonstrate_chaining() -> None:
    async def load_user() -> dict[str, Any]:
        await asyncio.sleep(0.03)
        return {"id": 42, "name": "Asha"}

    async def load_permissions(user: dict[str, Any]) -> set[str]:
        await asyncio.sleep(0.03)
        return {"read", "deploy"} if user["id"] == 42 else {"read"}

    async def authorize(permissions: set[str]) -> str:
        await asyncio.sleep(0.03)
        if "deploy" not in permissions:
            raise PermissionError("deploy permission is required")
        return "deployment authorized"

    try:
        user = await load_user()
        permissions = await load_permissions(user)
        decision = await authorize(permissions)
        print("chained result:", decision)
    except (RuntimeError, PermissionError) as exc:
        print("chained error:", exc)


async def demonstrate_error_propagation() -> None:
    async def failing_operation() -> str:
        await asyncio.sleep(0.02)
        raise ValueError("invalid deployment configuration")

    try:
        await failing_operation()
    except ValueError as exc:
        print("error propagated to handler:", exc)


async def promise_all_like() -> list[Result]:
    tasks = [
        asyncio.create_task(delayed_value("database", 0.08, "ready")),
        asyncio.create_task(delayed_value("cache", 0.04, "ready")),
        asyncio.create_task(delayed_value("queue", 0.06, "ready")),
    ]
    return list(await asyncio.gather(*tasks))


async def promise_all_failure_like() -> None:
    tasks = [
        asyncio.create_task(delayed_value("database", 0.08, "ready")),
        asyncio.create_task(
            delayed_failure("cache", 0.03, "connection refused")
        ),
        asyncio.create_task(delayed_value("queue", 0.06, "ready")),
    ]

    try:
        await asyncio.gather(*tasks)
    except RuntimeError as exc:
        print("all-like fail-fast behavior:", exc)
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


async def promise_race_like() -> Result:
    async def first_completed() -> Result:
        tasks = [
            asyncio.create_task(delayed_value("primary", 0.12, "primary response")),
            asyncio.create_task(delayed_value("replica", 0.04, "replica response")),
            asyncio.create_task(delayed_value("fallback", 0.08, "fallback response")),
        ]

        done, pending = await asyncio.wait(
            tasks,
            return_when=asyncio.FIRST_COMPLETED,
        )

        winner = next(iter(done))
        result = await winner

        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)
        return result

    return await first_completed()


async def promise_all_settled_like() -> list[Result]:
    tasks: dict[str, asyncio.Task[Result]] = {
        "metrics": asyncio.create_task(
            delayed_value("metrics", 0.04, "accepted")
        ),
        "audit": asyncio.create_task(
            delayed_failure("audit", 0.02, "service unavailable")
        ),
        "cache": asyncio.create_task(
            delayed_value("cache", 0.06, "updated")
        ),
    }

    settled: list[Result] = []
    for name, task in tasks.items():
        try:
            settled.append(await task)
        except BaseException as exc:
            settled.append(Result(name=name, error=exc))
    return settled


async def promise_any_like() -> str:
    async def attempt(name: str, delay: float, succeeds: bool) -> str:
        await asyncio.sleep(delay)
        if not succeeds:
            raise ConnectionError(f"{name} unavailable")
        return f"{name} accepted request"

    tasks = [
        asyncio.create_task(attempt("region-a", 0.08, False)),
        asyncio.create_task(attempt("region-b", 0.03, True)),
        asyncio.create_task(attempt("region-c", 0.06, False)),
    ]

    done, pending = await asyncio.wait(
        tasks,
        return_when=asyncio.FIRST_COMPLETED,
    )

    # FIRST_COMPLETED is not sufficient for Promise.any semantics:
    # a rejection must not stop the search for a successful result.
    failures: list[BaseException] = []

    while True:
        for task in done:
            try:
                value = task.result()
                for pending_task in pending:
                    pending_task.cancel()
                await asyncio.gather(*pending, return_exceptions=True)
                return value
            except BaseException as exc:
                failures.append(exc)

        if not pending:
            raise ExceptionGroup("all attempts failed", failures)

        done, pending = await asyncio.wait(
            pending,
            return_when=asyncio.FIRST_COMPLETED,
        )


class PromiseLike:
    """
    Small synchronous model of the core Promise state machine.

    A promise settles exactly once:
        pending -> fulfilled
        pending -> rejected
    """

    def __init__(self) -> None:
        self.state = "pending"
        self.value: Any = None
        self.reason: BaseException | None = None
        self._handlers: list[Callable[["PromiseLike"], None]] = []

    def then(
        self,
        on_fulfilled: Callable[[Any], Any] | None = None,
        on_rejected: Callable[[BaseException], Any] | None = None,
    ) -> "PromiseLike":
        next_promise = PromiseLike()

        def handle(_: PromiseLike) -> None:
            try:
                if self.state == "fulfilled":
                    if on_fulfilled is None:
                        next_promise.resolve(self.value)
                    else:
                        next_promise.resolve(on_fulfilled(self.value))
                elif self.state == "rejected":
                    if on_rejected is None:
                        next_promise.reject(self.reason or RuntimeError())
                    else:
                        next_promise.resolve(on_rejected(self.reason or RuntimeError()))
            except BaseException as exc:
                next_promise.reject(exc)

        self._handlers.append(handle)

        if self.state != "pending":
            handle(self)

        return next_promise

    def catch(
        self,
        on_rejected: Callable[[BaseException], Any],
    ) -> "PromiseLike":
        return self.then(None, on_rejected)

    def resolve(self, value: Any) -> None:
        if self.state != "pending":
            raise PromiseStateError("a settled promise cannot be resolved again")
        self.state = "fulfilled"
        self.value = value
        self._flush()

    def reject(self, reason: BaseException) -> None:
        if self.state != "pending":
            raise PromiseStateError("a settled promise cannot be rejected again")
        self.state = "rejected"
        self.reason = reason
        self._flush()

    def _flush(self) -> None:
        handlers = self._handlers
        self._handlers = []
        for handler in handlers:
            handler(self)


def demonstrate_state_machine() -> None:
    promise = PromiseLike()

    chained = (
        promise
        .then(lambda value: value * 2)
        .then(lambda value: value + 10)
        .then(lambda value: print("state-machine result:", value))
    )

    promise.resolve(20)

    if chained.state != "fulfilled":
        raise AssertionError("terminal handler should have fulfilled")

    try:
        promise.reject(RuntimeError("second settlement"))
    except PromiseStateError as exc:
        print("settlement protection:", exc)


async def main() -> None:
    print("=== Promise state and execution model ===")
    demonstrate_state_machine()

    print("\n=== Basic resolution ===")
    await demonstrate_basic_coroutine()

    print("\n=== Chaining ===")
    await demonstrate_chaining()

    print("\n=== Error propagation ===")
    await demonstrate_error_propagation()

    print("\n=== Promise.all-like success ===")
    print(await promise_all_like())

    print("\n=== Promise.all-like failure ===")
    await promise_all_failure_like()

    print("\n=== Promise.race-like behavior ===")
    print(await promise_race_like())

    print("\n=== Promise.allSettled-like behavior ===")
    for result in await promise_all_settled_like():
        if result.error is None:
            print(result.name, "fulfilled:", result.value)
        else:
            print(result.name, "rejected:", result.error)

    print("\n=== Promise.any-like behavior ===")
    try:
        print(await promise_any_like())
    except ExceptionGroup as exc:
        print("all candidates rejected:", exc.exceptions)


if __name__ == "__main__":
    asyncio.run(main())
