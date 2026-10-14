"""
Error Handling in Python: From Fundamentals to Production-Oriented Design

Demonstrates exception propagation, try/except/else/finally, explicit raising,
custom exception hierarchies, defensive validation, resource cleanup, retries,
transaction-like rollback, structured logging, and fault-isolated batch processing.

Run:
    python error_handling.py

Uses only the Python standard library.
"""

from __future__ import annotations

import json
import logging
import math
import random
import tempfile
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, TypeVar


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("error_handling")
T = TypeVar("T")


# Custom exceptions let callers distinguish expected business failures from
# programming defects without parsing error-message strings.
class ApplicationError(Exception):
    """Base class for explicitly modeled application failures."""


class ValidationError(ApplicationError, ValueError):
    """Input violates a documented contract."""


class ResourceNotFoundError(ApplicationError):
    """A requested record does not exist."""


class InsufficientFundsError(ApplicationError):
    """An account cannot fund the requested withdrawal."""


class ExternalServiceError(ApplicationError):
    """A dependency failed in a way that may be recoverable."""


class RetryExhaustedError(ApplicationError):
    """All permitted attempts to call a dependency failed."""


class TransactionError(ApplicationError):
    """A transaction could not complete safely."""


class ConfigurationError(ApplicationError):
    """Configuration is absent or invalid."""


# A broad catch is useful at an application boundary for logging and cleanup,
# but normal control flow should catch the narrowest meaningful exception.
def demonstrate_basic_exceptions() -> None:
    print("\n--- Basic exception handling ---")

    try:
        result = 10 / 0
    except ZeroDivisionError as exc:
        print(f"Division failed: {exc}")

    try:
        value = int("not-a-number")
    except ValueError as exc:
        print(f"Conversion failed: {exc}")

    try:
        numbers = [10, 20]
        print(numbers[5])
    except IndexError as exc:
        print(f"Index access failed: {exc}")

    try:
        data = {"status": "ready"}
        print(data["missing"])
    except KeyError as exc:
        print(f"Dictionary lookup failed: {exc}")


def demonstrate_control_flow() -> None:
    print("\n--- try, except, else, finally ---")

    # else executes only if the try suite completes without an exception.
    # finally executes whether the operation succeeds or fails.
    for raw_value in ("42", "invalid"):
        try:
            parsed = int(raw_value)
        except ValueError:
            print(f"Rejected integer: {raw_value!r}")
        else:
            print(f"Parsed successfully: {parsed}")
        finally:
            print(f"Finished processing {raw_value!r}")


def parse_percentage(raw_value: object) -> float:
    """Convert and validate a percentage without accepting non-finite values."""
    if isinstance(raw_value, bool):
        raise ValidationError("A boolean is not a valid percentage.")

    try:
        percentage = float(raw_value)
    except (TypeError, ValueError) as exc:
        raise ValidationError("Percentage must be numeric.") from exc

    if not math.isfinite(percentage):
        raise ValidationError("Percentage must be finite.")

    if not 0.0 <= percentage <= 100.0:
        raise ValidationError("Percentage must be between 0 and 100.")

    return percentage


def calculate_discount(price: float, percentage: object) -> float:
    """Apply a validated percentage discount to a finite, nonnegative price."""
    if isinstance(price, bool) or not isinstance(price, (int, float)):
        raise ValidationError("Price must be a real number.")

    if not math.isfinite(price) or price < 0:
        raise ValidationError("Price must be finite and nonnegative.")

    rate = parse_percentage(percentage)
    return round(price * (1.0 - rate / 100.0), 2)


# Exception chaining preserves the original cause for diagnostics while
# presenting callers with an error meaningful to the application.
def load_json_file(path: Path) -> dict:
    try:
        with path.open("r", encoding="utf-8") as file:
            document = json.load(file)
    except FileNotFoundError as exc:
        raise ResourceNotFoundError(f"Configuration file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ConfigurationError(
            f"Invalid JSON at line {exc.lineno}, column {exc.colno}"
        ) from exc
    except PermissionError as exc:
        raise ConfigurationError(f"Cannot read configuration file: {path}") from exc

    if not isinstance(document, dict):
        raise ConfigurationError("The configuration root must be a JSON object.")

    return document


# Validation belongs near the boundary where untrusted input enters the system.
@dataclass(frozen=True)
class TransferRequest:
    source: str
    destination: str
    amount: float

    def __post_init__(self) -> None:
        if not isinstance(self.source, str) or not self.source.strip():
            raise ValidationError("Source account is required.")

        if not isinstance(self.destination, str) or not self.destination.strip():
            raise ValidationError("Destination account is required.")

        if self.source == self.destination:
            raise ValidationError("Source and destination must differ.")

        if isinstance(self.amount, bool) or not isinstance(self.amount, (int, float)):
            raise ValidationError("Transfer amount must be numeric.")

        if not math.isfinite(self.amount) or self.amount <= 0:
            raise ValidationError("Transfer amount must be finite and positive.")


class Bank:
    """Small in-memory transfer model with rollback on failed operations."""

    def __init__(self, balances: dict[str, float]) -> None:
        if not balances:
            raise ValidationError("At least one account is required.")

        validated: dict[str, float] = {}
        for account, balance in balances.items():
            if not isinstance(account, str) or not account.strip():
                raise ValidationError("Account identifiers must be nonempty strings.")

            if isinstance(balance, bool) or not isinstance(balance, (int, float)):
                raise ValidationError(f"Invalid balance for {account!r}.")

            if not math.isfinite(balance) or balance < 0:
                raise ValidationError(f"Invalid balance for {account!r}.")

            validated[account] = float(balance)

        self._balances = validated

    def balance(self, account: str) -> float:
        try:
            return self._balances[account]
        except KeyError as exc:
            raise ResourceNotFoundError(
                f"Account does not exist: {account}"
            ) from exc

    def transfer(self, request: TransferRequest) -> None:
        if request.source not in self._balances:
            raise ResourceNotFoundError(
                f"Source account does not exist: {request.source}"
            )

        if request.destination not in self._balances:
            raise ResourceNotFoundError(
                f"Destination account does not exist: {request.destination}"
            )

        if self._balances[request.source] < request.amount:
            raise InsufficientFundsError(
                f"Account {request.source} has insufficient funds."
            )

        # Preserve original values so a failure during the operation can
        # restore both accounts to their previous state.
        source_before = self._balances[request.source]
        destination_before = self._balances[request.destination]

        try:
            self._balances[request.source] -= request.amount
            self._balances[request.destination] += request.amount

            if not all(
                math.isfinite(value) and value >= 0
                for value in self._balances.values()
            ):
                raise TransactionError("Transfer produced an invalid balance.")
        except Exception as exc:
            self._balances[request.source] = source_before
            self._balances[request.destination] = destination_before

            if isinstance(exc, ApplicationError):
                raise

            raise TransactionError("Transfer failed and was rolled back.") from exc

    def snapshot(self) -> dict[str, float]:
        return self._balances.copy()


# A context manager gives file-like resources deterministic cleanup, including
# when the body raises an exception.
@contextmanager
def temporary_report_file():
    with tempfile.TemporaryDirectory(prefix="error_demo_") as directory:
        report_path = Path(directory) / "report.txt"
        try:
            with report_path.open("w", encoding="utf-8") as file:
                yield file
        finally:
            # The enclosing TemporaryDirectory removes its contents on exit.
            logger.debug("Report file processing finished: %s", report_path)


def retry(
    operation: Callable[[], T],
    *,
    attempts: int = 3,
    delay_seconds: float = 0.01,
    retryable: tuple[type[Exception], ...] = (ExternalServiceError,),
) -> T:
    """Retry selected transient failures with bounded exponential backoff."""
    if isinstance(attempts, bool) or not isinstance(attempts, int) or attempts < 1:
        raise ValidationError("Attempts must be a positive integer.")

    if (
        isinstance(delay_seconds, bool)
        or not isinstance(delay_seconds, (int, float))
        or not math.isfinite(delay_seconds)
        or delay_seconds < 0
    ):
        raise ValidationError("Delay must be finite and nonnegative.")

    if not retryable or not all(
        isinstance(exception_type, type)
        and issubclass(exception_type, Exception)
        for exception_type in retryable
    ):
        raise ValidationError("Retryable types must be Exception subclasses.")

    for attempt in range(attempts):
        try:
            return operation()
        except retryable as exc:
            if attempt == attempts - 1:
                raise RetryExhaustedError(
                    f"Operation failed after {attempts} attempts."
                ) from exc

            # Exponential backoff reduces repeated pressure on a failing service.
            time.sleep(delay_seconds * (2 ** attempt))

    raise AssertionError("Unreachable retry state.")


def make_unreliable_service(failures_before_success: int) -> Callable[[], str]:
    if (
        isinstance(failures_before_success, bool)
        or not isinstance(failures_before_success, int)
        or failures_before_success < 0
    ):
        raise ValidationError("Failure count must be a nonnegative integer.")

    state = {"failures": 0}

    def call_service() -> str:
        if state["failures"] < failures_before_success:
            state["failures"] += 1
            raise ExternalServiceError("Temporary service outage.")
        return "Service response received."

    return call_service


def process_batch(
    values: Iterable[object],
    processor: Callable[[object], T],
) -> tuple[list[T], list[dict[str, str]]]:
    """Isolate expected per-item failures without hiding programming defects."""
    successes: list[T] = []
    failures: list[dict[str, str]] = []

    for index, value in enumerate(values):
        try:
            successes.append(processor(value))
        except ApplicationError as exc:
            failures.append(
                {
                    "index": str(index),
                    "value": repr(value),
                    "error_type": type(exc).__name__,
                    "message": str(exc),
                }
            )
            logger.warning(
                "Batch item %d failed with %s",
                index,
                type(exc).__name__,
            )

    return successes, failures


def safe_configuration_value(
    configuration: dict[str, object],
    key: str,
    default: str,
) -> str:
    """Use a fallback for absent values while rejecting malformed values."""
    value = configuration.get(key, default)

    if not isinstance(value, str) or not value.strip():
        raise ConfigurationError(f"Configuration value {key!r} must be nonempty.")

    return value


def demonstrate_exception_propagation() -> None:
    print("\n--- Exception propagation and chaining ---")

    with tempfile.TemporaryDirectory() as directory:
        missing_path = Path(directory) / "missing.json"
        try:
            load_json_file(missing_path)
        except ResourceNotFoundError as exc:
            print(f"Application-level failure: {exc}")
            print(f"Original cause: {type(exc.__cause__).__name__}")


def demonstrate_validation() -> None:
    print("\n--- Defensive validation ---")

    for raw_value in ("15", 150, float("nan"), True, "unknown"):
        try:
            print(f"{raw_value!r} -> {parse_percentage(raw_value)}")
        except ValidationError as exc:
            print(f"Rejected {raw_value!r}: {exc}")

    print("Discounted price:", calculate_discount(250.0, 15))


def demonstrate_bank_transactions() -> None:
    print("\n--- Transaction-like error handling ---")

    bank = Bank({"OPERATIONS": 1000.0, "PROJECT": 200.0})
    print("Initial balances:", bank.snapshot())

    bank.transfer(TransferRequest("OPERATIONS", "PROJECT", 150.0))
    print("After transfer:", bank.snapshot())

    try:
        bank.transfer(TransferRequest("PROJECT", "OPERATIONS", 5000.0))
    except InsufficientFundsError as exc:
        print(f"Transfer rejected: {exc}")

    try:
        bank.transfer(TransferRequest("PROJECT", "MISSING", 10.0))
    except ResourceNotFoundError as exc:
        print(f"Transfer rejected: {exc}")

    print("Final balances:", bank.snapshot())


def demonstrate_retry() -> None:
    print("\n--- Bounded retries ---")

    service = make_unreliable_service(failures_before_success=2)
    print(retry(service, attempts=3, delay_seconds=0.001))

    failing_service = make_unreliable_service(failures_before_success=10)
    try:
        retry(failing_service, attempts=2, delay_seconds=0)
    except RetryExhaustedError as exc:
        print(f"Recovery exhausted: {exc}")
        print(f"Last failure: {type(exc.__cause__).__name__}")


def demonstrate_batch_processing() -> None:
    print("\n--- Fault-isolated batch processing ---")

    records = [
        {"name": "Database migration", "completion": "100"},
        {"name": "API integration", "completion": "75"},
        {"name": "Deployment", "completion": "invalid"},
        {"name": "Security review", "completion": "-5"},
    ]

    def normalize_record(raw_record: object) -> dict[str, object]:
        if not isinstance(raw_record, dict):
            raise ValidationError("Record must be an object.")

        name = raw_record.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ValidationError("Record name must be nonempty.")

        completion = parse_percentage(raw_record.get("completion"))
        return {"name": name.strip(), "completion": completion}

    successes, failures = process_batch(records, normalize_record)
    print("Accepted records:", json.dumps(successes, indent=2))
    print("Rejected records:", json.dumps(failures, indent=2))


def demonstrate_resource_cleanup() -> None:
    print("\n--- Resource cleanup ---")

    try:
        with temporary_report_file() as report:
            report.write("Deployment validation completed.\n")
            raise RuntimeError("Simulated report-generation failure.")
    except RuntimeError as exc:
        print(f"Report operation failed: {exc}")
        print("Temporary resources were released by the context managers.")


def run_self_tests() -> None:
    """Use assertions to verify contracts and important failure paths."""
    assert calculate_discount(100, 20) == 80.0
    assert parse_percentage("25") == 25.0

    for invalid in (True, float("nan"), float("inf"), -1, 101, "bad"):
        try:
            parse_percentage(invalid)
        except ValidationError:
            pass
        else:
            raise AssertionError(f"Expected validation failure for {invalid!r}")

    bank = Bank({"A": 500, "B": 100})
    bank.transfer(TransferRequest("A", "B", 50))
    assert bank.balance("A") == 450
    assert bank.balance("B") == 150

    before = bank.snapshot()
    try:
        bank.transfer(TransferRequest("A", "B", 5000))
    except InsufficientFundsError:
        pass
    else:
        raise AssertionError("Expected insufficient-funds failure.")

    assert bank.snapshot() == before

    service = make_unreliable_service(1)
    assert retry(service, attempts=2, delay_seconds=0) == "Service response received."

    try:
        retry(make_unreliable_service(5), attempts=2, delay_seconds=0)
    except RetryExhaustedError:
        pass
    else:
        raise AssertionError("Expected retry exhaustion.")

    print("\nAll self-tests passed.")


def main() -> None:
    random.seed(7)
    demonstrate_basic_exceptions()
    demonstrate_control_flow()
    demonstrate_validation()
    demonstrate_exception_propagation()
    demonstrate_bank_transactions()
    demonstrate_retry()
    demonstrate_batch_processing()
    demonstrate_resource_cleanup()
    run_self_tests()


if __name__ == "__main__":
    main()
