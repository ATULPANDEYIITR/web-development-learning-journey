from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Iterable


# Control flow determines which statements execute, how often they execute,
# and when execution leaves or skips part of a loop. The examples below move
# from basic branching to reusable decision engines and file processing.


def demonstrate_if_else(score: int) -> str:
    """Use conditional branching to classify a score."""
    if not 0 <= score <= 100:
        raise ValueError("score must be between 0 and 100")

    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"


def demonstrate_nested_conditions(age: int, has_permission: bool) -> str:
    """Show why nested conditions should represent genuinely dependent decisions."""
    if age < 0:
        raise ValueError("age cannot be negative")

    if age >= 18:
        if has_permission:
            return "adult-access-granted"
        return "adult-access-denied"

    return "minor-access-denied"


def demonstrate_boolean_control_flow(
    authenticated: bool,
    account_active: bool,
    role: str,
) -> str:
    """Combine conditions when several facts jointly determine an outcome."""
    if not authenticated:
        return "authentication-required"

    if not account_active:
        return "account-disabled"

    if role == "admin":
        return "administrative-access"

    if role in {"editor", "reviewer"}:
        return "collaborative-access"

    return "read-only-access"


def demonstrate_for_loop(values: Iterable[int]) -> list[int]:
    """Process every item in an iterable using a for loop."""
    doubled = []

    for value in values:
        doubled.append(value * 2)

    return doubled


def demonstrate_range_loop(limit: int) -> list[int]:
    """range() generates integer sequences useful for bounded iteration."""
    if limit < 0:
        raise ValueError("limit cannot be negative")

    squares = []

    for number in range(limit):
        squares.append(number * number)

    return squares


def demonstrate_break(values: Iterable[int], threshold: int) -> list[int]:
    """
    Stop scanning once the first value above the threshold is found.

    break terminates the nearest enclosing loop immediately.
    """
    observed = []

    for value in values:
        if value > threshold:
            break
        observed.append(value)

    return observed


def demonstrate_continue(values: Iterable[int]) -> list[int]:
    """
    Skip invalid or unwanted values while continuing the same loop.

    continue jumps directly to the next iteration.
    """
    accepted = []

    for value in values:
        if value < 0:
            continue

        accepted.append(value)

    return accepted


def classify_with_match(command: str) -> str:
    """
    Python's match statement provides structural pattern matching.

    It is useful when several distinct shapes or exact command values must
    be handled. The default case is represented by the wildcard pattern.
    """
    match command.strip().lower():
        case "start":
            return "starting"
        case "stop":
            return "stopping"
        case "pause":
            return "pausing"
        case "resume":
            return "resuming"
        case _:
            return "unknown-command"


def demonstrate_while_loop(start: int) -> list[int]:
    """
    A while loop continues while its condition remains true.

    Updating the control variable is essential. Without progress toward the
    terminating condition, a loop can become infinite.
    """
    if start < 0:
        raise ValueError("start cannot be negative")

    values = []
    current = start

    while current > 0:
        values.append(current)
        current -= 1

    return values


def first_even(numbers: Iterable[int]) -> int | None:
    """Use a loop with continue and break to find one relevant value."""
    for number in numbers:
        if number % 2 != 0:
            continue

        return number

    return None


def safe_integer_input(raw_value: str) -> int | None:
    """
    Convert external text into an integer.

    try/except is itself a form of control flow because execution moves into
    the exception handler when conversion fails.
    """
    try:
        return int(raw_value.strip())
    except ValueError:
        return None


def retry_operation(
    operation: Callable[[], str],
    max_attempts: int,
) -> str:
    """
    Retry an operation until it succeeds or the attempt limit is reached.

    The example intentionally keeps the retry mechanism deterministic and
    independent of network services.
    """
    if max_attempts <= 0:
        raise ValueError("max_attempts must be positive")

    last_error: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            result = operation()
            return result
        except Exception as exc:
            last_error = exc

            if attempt == max_attempts:
                break

    raise RuntimeError("operation failed after all attempts") from last_error


class DeploymentState(Enum):
    PENDING = "pending"
    VALIDATING = "validating"
    DEPLOYED = "deployed"
    FAILED = "failed"


@dataclass
class Deployment:
    name: str
    tests_passed: bool
    artifact_exists: bool
    state: DeploymentState = DeploymentState.PENDING

    def validate(self) -> DeploymentState:
        """
        Model a state transition with explicit branching.

        A failed prerequisite stops further processing. This is preferable to
        continuing into deployment with invalid state.
        """
        if self.state is not DeploymentState.PENDING:
            return self.state

        self.state = DeploymentState.VALIDATING

        if not self.artifact_exists:
            self.state = DeploymentState.FAILED
            return self.state

        if not self.tests_passed:
            self.state = DeploymentState.FAILED
            return self.state

        self.state = DeploymentState.DEPLOYED
        return self.state


def validate_records(records: Iterable[dict]) -> dict[str, list]:
    """
    Validate records with continue for recoverable invalid records.

    A malformed record is skipped rather than terminating validation of every
    remaining record.
    """
    accepted = []
    rejected = []

    for index, record in enumerate(records):
        if not isinstance(record, dict):
            rejected.append((index, "record is not an object"))
            continue

        if "id" not in record or "value" not in record:
            rejected.append((index, "missing required field"))
            continue

        if not isinstance(record["id"], int):
            rejected.append((index, "id must be an integer"))
            continue

        if record["value"] is None:
            rejected.append((index, "value cannot be null"))
            continue

        accepted.append(record)

    return {"accepted": accepted, "rejected": rejected}


def process_log_file(path: Path, maximum_lines: int = 10000) -> dict[str, int]:
    """
    Process a text file with bounded iteration.

    break protects the process from reading an unexpectedly huge file.
    continue ignores blank lines without nesting the remaining logic.
    """
    if maximum_lines <= 0:
        raise ValueError("maximum_lines must be positive")

    counts = {"INFO": 0, "WARNING": 0, "ERROR": 0, "OTHER": 0}

    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if line_number > maximum_lines:
                break

            stripped = line.strip()

            if not stripped:
                continue

            if stripped.startswith("INFO"):
                counts["INFO"] += 1
                continue

            if stripped.startswith("WARNING"):
                counts["WARNING"] += 1
                continue

            if stripped.startswith("ERROR"):
                counts["ERROR"] += 1
                continue

            counts["OTHER"] += 1

    return counts


def evaluate_rules(
    amount: float,
    customer_type: str,
    fraud_score: float,
) -> str:
    """
    Apply ordered business rules.

    The ordering is meaningful: a fraud block takes precedence over normal
    pricing decisions, and customer type is considered only after safety
    validation has passed.
    """
    if amount < 0:
        raise ValueError("amount cannot be negative")

    if not 0 <= fraud_score <= 1:
        raise ValueError("fraud_score must be between 0 and 1")

    if fraud_score >= 0.9:
        return "blocked"

    if amount == 0:
        return "no-charge"

    if customer_type == "enterprise":
        if amount >= 10000:
            return "enterprise-priority"
        return "enterprise-standard"

    if customer_type == "student":
        return "discounted"

    return "standard"


def search_inventory(
    inventory: dict[str, int],
    requested_skus: Iterable[str],
) -> list[str]:
    """
    Search requested SKUs.

    continue skips unknown or unavailable products, while the caller receives
    only actionable matches.
    """
    available = []

    for sku in requested_skus:
        quantity = inventory.get(sku)

        if quantity is None:
            continue

        if quantity <= 0:
            continue

        available.append(sku)

    return available


def menu_command(command: str) -> str:
    """
    A dictionary can act as a data-driven alternative to a long if/elif chain.

    This is useful when the control decision is simply an exact lookup.
    """
    actions = {
        "build": "build-project",
        "test": "run-tests",
        "deploy": "deploy-project",
        "status": "show-status",
    }

    return actions.get(command.lower(), "unknown-command")


def demonstrate_comprehension_control(values: Iterable[int]) -> list[int]:
    """
    A comprehension embeds a filtering condition into collection construction.

    It is appropriate when the operation is short and has no complex side
    effects. A normal loop is clearer when multiple decisions are involved.
    """
    return [value * value for value in values if value >= 0]


def fibonacci_until_limit(limit: int) -> list[int]:
    """
    Generate Fibonacci values using a loop and an early termination condition.
    """
    if limit < 0:
        raise ValueError("limit cannot be negative")

    values = []
    first, second = 0, 1

    while first <= limit:
        values.append(first)
        first, second = second, first + second

    return values


def run_demo() -> None:
    print("Conditional branching")
    print(demonstrate_if_else(93))
    print(demonstrate_if_else(74))
    print(demonstrate_nested_conditions(25, True))
    print(demonstrate_boolean_control_flow(True, True, "reviewer"))

    print("\nIteration")
    print(demonstrate_for_loop([2, 4, 6]))
    print(demonstrate_range_loop(6))
    print(demonstrate_while_loop(5))

    print("\nbreak and continue")
    print(demonstrate_break([2, 4, 6, 12, 8], 10))
    print(demonstrate_continue([4, -1, 8, -3, 10]))
    print(first_even([1, 3, 5, 12, 14]))

    print("\nPattern matching and data-driven dispatch")
    for command in ("start", "pause", "unknown"):
        print(command, "->", classify_with_match(command))
    print(menu_command("deploy"))

    print("\nValidation and exception control flow")
    print(safe_integer_input("42"))
    print(safe_integer_input("not-a-number"))

    records = [
        {"id": 1, "value": "valid"},
        {"id": "2", "value": "invalid id"},
        {"id": 3},
        {"id": 4, "value": "valid"},
        None,
    ]
    print(validate_records(records))

    print("\nState-machine example")
    deployments = [
        Deployment("release-a", tests_passed=True, artifact_exists=True),
        Deployment("release-b", tests_passed=False, artifact_exists=True),
        Deployment("release-c", tests_passed=True, artifact_exists=False),
    ]

    for deployment in deployments:
        print(deployment.name, "->", deployment.validate().value)

    print("\nRule engine")
    examples = [
        (25000, "enterprise", 0.1),
        (500, "student", 0.2),
        (100, "consumer", 0.95),
        (0, "consumer", 0.0),
    ]

    for amount, customer_type, fraud_score in examples:
        print(
            amount,
            customer_type,
            fraud_score,
            "->",
            evaluate_rules(amount, customer_type, fraud_score),
        )

    print("\nInventory control flow")
    inventory = {"CPU-01": 4, "RAM-32": 0, "SSD-02": 12}
    print(search_inventory(inventory, ["CPU-01", "UNKNOWN", "RAM-32", "SSD-02"]))

    print("\nComprehension and bounded sequence")
    print(demonstrate_comprehension_control([4, -2, 7, 9]))
    print(fibonacci_until_limit(50))


if __name__ == "__main__":
    run_demo()
