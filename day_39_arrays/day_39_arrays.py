"""Array operations from foundational usage to practical data processing.

Run with Python 3.10 or later. The examples use only the standard library.
Python lists are dynamic sequences; they provide array-like behavior but are
not identical to fixed-size arrays or NumPy arrays.
"""

from dataclasses import dataclass
from functools import reduce
from itertools import islice
from math import isfinite
from random import Random
from typing import Callable, Iterable, TypeVar

T = TypeVar("T")
U = TypeVar("U")


def heading(title: str) -> None:
    print(f"\n{'=' * 12} {title} {'=' * 12}")


def create_arrays() -> None:
    heading("Creation and initialization")

    empty: list[int] = []
    scores = [82, 91, 76, 91, 88]
    repeated = [0] * 5
    generated = [number * number for number in range(6)]
    mixed = ["release", 4, True]

    print("Empty:", empty)
    print("Scores:", scores)
    print("Repeated zeros:", repeated)
    print("Generated squares:", generated)
    print("Mixed values:", mixed)

    # Nested lists model a two-dimensional grid.
    matrix = [[0 for _ in range(3)] for _ in range(2)]
    matrix[1][2] = 7
    print("Matrix:", matrix)

    # Multiplying a nested list repeats references to the same inner list.
    shared_rows = [[0] * 3] * 2
    shared_rows[0][0] = 9
    print("Shared-reference pitfall:", shared_rows)
    print("Independent rows:", matrix)


def indexing_and_slicing() -> None:
    heading("Indexing and slicing")

    temperatures = [18.5, 20.0, 23.5, 22.0, 19.5]

    print("First:", temperatures[0])
    print("Last:", temperatures[-1])
    print("Middle range:", temperatures[1:4])
    print("Every second reading:", temperatures[::2])
    print("Reversed copy:", temperatures[::-1])

    try:
        print(temperatures[20])
    except IndexError as error:
        print("Invalid index handled:", error)

    # Slices create a new outer list, not a deep copy of nested objects.
    original = [[1, 2], [3, 4]]
    shallow_copy = original[:]
    shallow_copy[0][0] = 99
    print("Original after nested mutation:", original)


def mutate_arrays() -> None:
    heading("Mutation")

    tasks = ["design", "implement", "test"]
    tasks[1] = "implement API"
    tasks.append("document")
    tasks.extend(["review", "deploy"])
    tasks.insert(1, "plan")
    removed_last = tasks.pop()
    tasks.remove("review")
    tasks[0:2] = ["scope", "architecture"]

    print("Tasks:", tasks)
    print("Popped item:", removed_last)

    del tasks[-1]
    print("After deletion:", tasks)

    # Sorting in place changes the original list.
    numbers = [8, 2, 5, 2, 9]
    numbers.sort()
    print("Sorted in place:", numbers)

    # sorted() returns a new list.
    descending = sorted(numbers, reverse=True)
    print("Descending copy:", descending)
    print("Original remains sorted ascending:", numbers)


def iterate_arrays() -> None:
    heading("Iteration")

    services = ["gateway", "billing", "inventory"]

    for service in services:
        print("Service:", service)

    for index, service in enumerate(services, start=0):
        print(f"services[{index}] = {service}")

    latency_ms = [42, 75, 31]
    for service, latency in zip(services, latency_ms):
        print(f"{service}: {latency} ms")

    # Iterate over a snapshot when removing elements during traversal.
    pending = ["valid", "", "invalid", "ready", ""]
    for item in pending[:]:
        if not item:
            pending.remove(item)
    print("Cleaned values:", pending)


def transform_with_map() -> None:
    heading("Map and transformation")

    prices = [120.0, 80.0, 250.0, 40.0]
    discounted = list(map(lambda price: round(price * 0.9, 2), prices))
    tax_inclusive = list(map(lambda price: round(price * 1.18, 2), prices))

    print("Prices:", prices)
    print("Ten percent discount:", discounted)
    print("Tax-inclusive prices:", tax_inclusive)

    # Comprehensions are often more readable for straightforward transformations.
    labels = [f"item-{index:03d}" for index in range(len(prices))]
    print("Labels:", labels)


def filter_arrays() -> None:
    heading("Filter and selection")

    readings = [12.2, 0.0, 18.4, -1.0, 23.1, 18.4]
    positive = list(filter(lambda value: value > 0, readings))
    threshold = [value for value in readings if value >= 18]

    print("Positive readings:", positive)
    print("Readings at least 18:", threshold)

    # Filtering retains the original order and does not mutate the input.
    print("Original readings:", readings)


def reduce_arrays() -> None:
    heading("Reduce and aggregation")

    durations = [15, 22, 18, 35, 10]
    total = reduce(lambda accumulator, value: accumulator + value, durations, 0)
    product = reduce(lambda accumulator, value: accumulator * value, [2, 3, 4], 1)

    average = total / len(durations) if durations else 0.0
    print("Total duration:", total)
    print("Average duration:", average)
    print("Product:", product)

    # A loop or sum() is clearer for simple numeric totals.
    print("Equivalent sum:", sum(durations))

    # Build multiple aggregate metrics in one traversal.
    metrics = {"count": 0, "total": 0, "minimum": None, "maximum": None}
    for duration in durations:
        metrics["count"] += 1
        metrics["total"] += duration
        metrics["minimum"] = (
            duration if metrics["minimum"] is None
            else min(metrics["minimum"], duration)
        )
        metrics["maximum"] = (
            duration if metrics["maximum"] is None
            else max(metrics["maximum"], duration)
        )
    print("Metrics:", metrics)


def find_some_every() -> None:
    heading("Find, some, and every")

    build_times = [42, 88, 65, 105, 73]

    first_slow = next((time for time in build_times if time > 90), None)
    any_slow = any(time > 90 for time in build_times)
    all_successful = all(time < 120 for time in build_times)

    print("First build over 90 seconds:", first_slow)
    print("Any build over 90 seconds:", any_slow)
    print("All builds under 120 seconds:", all_successful)

    # Python's next(generator, default) is analogous to JavaScript find().
    missing = next((time for time in build_times if time > 500), None)
    print("Missing match:", missing)

    # any() and all() short-circuit when the result is determined.
    checked = []
    result = any(checked.append(value) or value > 50 for value in build_times)
    print("Any value over 50:", result)
    print("Values evaluated before short-circuit:", checked)

    # Empty iterable semantics matter in validation logic.
    print("any([]):", any([]))
    print("all([]):", all([]))


@dataclass(frozen=True)
class Deployment:
    service: str
    version: str
    healthy: bool
    latency_ms: float
    errors: int


def validate_deployment(item: Deployment) -> None:
    if not item.service.strip():
        raise ValueError("Service name cannot be empty")
    if not item.version.strip():
        raise ValueError("Version cannot be empty")
    if not isfinite(item.latency_ms) or item.latency_ms < 0:
        raise ValueError("Latency must be finite and non-negative")
    if item.errors < 0:
        raise ValueError("Error count cannot be negative")


def deployment_report(deployments: Iterable[Deployment]) -> dict[str, object]:
    records = list(deployments)

    for record in records:
        validate_deployment(record)

    healthy = list(filter(lambda record: record.healthy, records))
    slow = [record for record in records if record.latency_ms > 100]
    first_unhealthy = next(
        (record for record in records if not record.healthy), None
    )

    total_errors = reduce(
        lambda total, record: total + record.errors, records, 0
    )
    average_latency = (
        reduce(lambda total, record: total + record.latency_ms, records, 0.0)
        / len(records)
        if records else 0.0
    )

    return {
        "service_count": len(records),
        "healthy_count": len(healthy),
        "all_healthy": all(record.healthy for record in records),
        "any_slow": any(record.latency_ms > 100 for record in records),
        "slow_services": [record.service for record in slow],
        "first_unhealthy": (
            first_unhealthy.service if first_unhealthy else None
        ),
        "total_errors": total_errors,
        "average_latency_ms": round(average_latency, 2),
        "healthy_versions": [
            {"service": record.service, "version": record.version}
            for record in healthy
        ],
    }


def validation_and_edge_cases() -> None:
    heading("Validation and edge cases")

    # Empty collections need explicit policy decisions for averages and defaults.
    print("Empty report:", deployment_report([]))

    valid = Deployment("billing", "2.4.1", True, 42.5, 0)
    invalid = Deployment("gateway", "2.4.1", True, float("nan"), 0)

    print("Valid deployment:", deployment_report([valid]))

    try:
        deployment_report([invalid])
    except ValueError as error:
        print("Invalid deployment rejected:", error)

    values = [1, 2, 3]
    alias = values
    alias.append(4)
    print("Aliasing changes original:", values)

    independent = values.copy()
    independent.append(5)
    print("Shallow copy:", independent)
    print("Original after shallow-copy mutation:", values)

    # Removing repeated values while preserving order requires tracking seen values.
    repeated = ["api", "worker", "api", "scheduler", "worker"]
    seen: set[str] = set()
    unique = []
    for item in repeated:
        if item not in seen:
            seen.add(item)
            unique.append(item)
    print("Unique values in original order:", unique)


def file_processing_example() -> None:
    heading("Practical data processing")

    # Process structured records without requiring a file or external package.
    records = [
        {"service": "api", "requests": 100, "failures": 3},
        {"service": "worker", "requests": 80, "failures": 0},
        {"service": "search", "requests": 150, "failures": 12},
    ]

    failure_rates = list(
        map(
            lambda record: {
                "service": record["service"],
                "failure_rate": (
                    record["failures"] / record["requests"]
                    if record["requests"] > 0 else None
                ),
            },
            records,
        )
    )

    high_failure = list(
        filter(
            lambda item: (
                item["failure_rate"] is not None
                and item["failure_rate"] >= 0.05
            ),
            failure_rates,
        )
    )

    total_requests = reduce(
        lambda total, record: total + record["requests"], records, 0
    )
    total_failures = reduce(
        lambda total, record: total + record["failures"], records, 0
    )

    print("Failure rates:", failure_rates)
    print("Services needing investigation:", high_failure)
    print("Total requests:", total_requests)
    print("Total failures:", total_failures)


def deterministic_simulation() -> None:
    heading("Deterministic simulation")

    random = Random(17)
    response_times = [random.randint(20, 180) for _ in range(12)]

    slow_samples = list(filter(lambda value: value > 120, response_times))
    normalized = list(map(lambda value: round(value / 1000, 3), response_times))
    first_critical = next(
        (value for value in response_times if value >= 170), None
    )

    print("Response times in milliseconds:", response_times)
    print("Slow samples:", slow_samples)
    print("Seconds:", normalized)
    print("First critical sample:", first_critical)
    print("Any critical sample:", any(value >= 170 for value in response_times))
    print("All samples non-negative:", all(value >= 0 for value in response_times))


def performance_notes() -> None:
    heading("Performance and safe iteration")

    values = list(range(100_000))

    # Building a transformed list consumes O(n) additional memory.
    doubled = list(map(lambda value: value * 2, values))
    print("Transformed element count:", len(doubled))

    # Generator expressions defer work and can reduce peak memory.
    doubled_stream = (value * 2 for value in values)
    first_values = list(islice(doubled_stream, 5))
    print("First transformed values:", first_values)

    # Membership in a list is O(n); a set offers average O(1) membership.
    lookup_values = [10, 20, 30, 40]
    lookup_set = set(lookup_values)
    print("List membership:", 30 in lookup_values)
    print("Set membership:", 30 in lookup_set)

    # Never mutate a list's structure while directly iterating over it unless
    # the algorithm explicitly accounts for skipped or shifted elements.
    queue = ["compile", "test", "deploy"]
    queue = [task for task in queue if task != "test"]
    print("Queue after safe filtering:", queue)


def main() -> None:
    create_arrays()
    indexing_and_slicing()
    mutate_arrays()
    iterate_arrays()
    transform_with_map()
    filter_arrays()
    reduce_arrays()
    find_some_every()
    validation_and_edge_cases()
    file_processing_example()
    deterministic_simulation()
    performance_notes()


if __name__ == "__main__":
    main()
