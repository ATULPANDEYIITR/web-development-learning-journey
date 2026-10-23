import asyncio
import random
from dataclasses import dataclass
from typing import Awaitable, Callable


@dataclass(frozen=True)
class JobResult:
    job_id: str
    status: str
    value: object | None = None
    error: str | None = None


async def fetch_service(service: str, delay: float, fail: bool = False) -> str:
    """Simulate an I/O-bound operation without blocking the event loop."""
    await asyncio.sleep(delay)

    if fail:
        raise RuntimeError(f"{service} failed")

    return f"{service} response"


async def run_sequential() -> list[str]:
    """Await operations one after another."""
    results = []

    results.append(await fetch_service("users", 0.30))
    results.append(await fetch_service("orders", 0.20))
    results.append(await fetch_service("inventory", 0.25))

    return results


async def run_parallel() -> list[str]:
    """Create independent coroutines and await them together."""
    tasks = [
        fetch_service("users", 0.30),
        fetch_service("orders", 0.20),
        fetch_service("inventory", 0.25),
    ]

    return await asyncio.gather(*tasks)


async def run_with_error_handling() -> list[JobResult]:
    """Capture individual failures without cancelling unrelated operations."""
    jobs = [
        ("profile", fetch_service("profile", 0.20)),
        ("payments", fetch_service("payments", 0.15, fail=True)),
        ("notifications", fetch_service("notifications", 0.10)),
    ]

    results: list[JobResult] = []

    for job_id, coroutine in jobs:
        try:
            value = await coroutine
            results.append(JobResult(job_id, "completed", value=value))
        except Exception as exc:
            results.append(JobResult(job_id, "failed", error=str(exc)))

    return results


async def run_parallel_with_isolated_errors() -> list[JobResult]:
    """Use return_exceptions=True so one failed task does not hide other results."""
    jobs = {
        "profile": fetch_service("profile", 0.20),
        "payments": fetch_service("payments", 0.15, fail=True),
        "notifications": fetch_service("notifications", 0.10),
    }

    names = list(jobs)
    outcomes = await asyncio.gather(
        *(jobs[name] for name in names),
        return_exceptions=True,
    )

    results = []

    for name, outcome in zip(names, outcomes):
        if isinstance(outcome, Exception):
            results.append(JobResult(name, "failed", error=str(outcome)))
        else:
            results.append(JobResult(name, "completed", value=outcome))

    return results


async def with_timeout(
    operation: Awaitable[str],
    timeout: float,
) -> JobResult:
    """Prevent a slow dependency from holding a workflow indefinitely."""
    try:
        value = await asyncio.wait_for(operation, timeout)
        return JobResult("timeout-protected", "completed", value=value)
    except asyncio.TimeoutError:
        return JobResult("timeout-protected", "timed_out")
    except Exception as exc:
        return JobResult("timeout-protected", "failed", error=str(exc))


async def retry_async(
    operation_factory: Callable[[], Awaitable[str]],
    attempts: int = 3,
    base_delay: float = 0.05,
) -> str:
    """Retry transient asynchronous failures with exponential backoff."""
    if attempts < 1:
        raise ValueError("attempts must be at least 1")

    last_error: Exception | None = None

    for attempt in range(attempts):
        try:
            return await operation_factory()
        except Exception as exc:
            last_error = exc

            if attempt == attempts - 1:
                break

            delay = base_delay * (2 ** attempt)
            await asyncio.sleep(delay)

    assert last_error is not None
    raise last_error


async def cancellation_demo() -> str:
    """Cancellation is cooperative and should be handled explicitly."""

    async def long_operation() -> str:
        try:
            await asyncio.sleep(5)
            return "completed"
        except asyncio.CancelledError:
            # Cleanup belongs here when the operation owns resources.
            raise

    task = asyncio.create_task(long_operation())

    await asyncio.sleep(0.05)
    task.cancel()

    try:
        await task
    except asyncio.CancelledError:
        return "operation cancelled safely"

    return "unexpected completion"


async def retryable_service() -> str:
    """A deterministic example that succeeds after transient failures."""
    state = {"attempt": 0}

    async def operation() -> str:
        state["attempt"] += 1

        if state["attempt"] < 3:
            raise ConnectionError("temporary network failure")

        return f"succeeded on attempt {state['attempt']}"

    return await retry_async(operation)


async def bounded_parallelism() -> list[str]:
    """A semaphore limits concurrent work against an external dependency."""
    semaphore = asyncio.Semaphore(2)

    async def worker(index: int) -> str:
        async with semaphore:
            await asyncio.sleep(random.uniform(0.03, 0.08))
            return f"worker-{index} completed"

    return await asyncio.gather(*(worker(i) for i in range(6)))


async def main() -> None:
    print("Sequential:")
    print(await run_sequential())

    print("\nParallel:")
    print(await run_parallel())

    print("\nSequential error isolation:")
    for result in await run_with_error_handling():
        print(result)

    print("\nParallel error isolation:")
    for result in await run_parallel_with_isolated_errors():
        print(result)

    print("\nTimeout:")
    print(await with_timeout(fetch_service("slow-service", 0.20), 0.05))

    print("\nRetry:")
    print(await retryable_service())

    print("\nCancellation:")
    print(await cancellation_demo())

    print("\nBounded parallelism:")
    print(await bounded_parallelism())


if __name__ == "__main__":
    asyncio.run(main())
