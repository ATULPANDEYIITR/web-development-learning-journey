"""Scope and Closures: a progressive, executable Python study.

The examples move from global, function, and block scope into lexical
scope and closures, then apply closures to factories, decorators,
state encapsulation, callbacks, memoization, validation, and testing.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import wraps
from typing import Callable, Iterable, Any
import time


# ---------------------------------------------------------------------------
# Global scope
# ---------------------------------------------------------------------------

APPLICATION_NAME = "ScopeLab"
DEFAULT_TIMEOUT_SECONDS = 30


def show_global_scope() -> None:
    """Read names defined in module/global scope."""
    print("\n=== Global scope ===")
    print("APPLICATION_NAME:", APPLICATION_NAME)
    print("DEFAULT_TIMEOUT_SECONDS:", DEFAULT_TIMEOUT_SECONDS)


def demonstrate_global_mutation() -> None:
    """Demonstrate why explicit global declaration is required for rebinding."""
    counter = 0

    def local_increment() -> None:
        # This creates a new local variable named counter.
        counter = 1
        print("Local counter:", counter)

    local_increment()
    print("Outer counter remains:", counter)

    global global_request_count
    global_request_count += 1
    print("Global request count:", global_request_count)


global_request_count = 0


# ---------------------------------------------------------------------------
# Function scope
# ---------------------------------------------------------------------------

def function_scope_example(value: int) -> int:
    """Names created inside a function belong to that function's local scope."""
    doubled = value * 2
    temporary_message = f"{value} doubled is {doubled}"

    print(temporary_message)
    return doubled


def demonstrate_function_scope() -> None:
    print("\n=== Function scope ===")
    function_scope_example(7)

    # temporary_message and doubled do not exist here because their
    # function-local scope ended when function_scope_example returned.
    try:
        print(doubled)  # type: ignore[name-defined]
    except NameError as exc:
        print("Expected NameError:", exc)


# ---------------------------------------------------------------------------
# Block scope versus Python's function scope
# ---------------------------------------------------------------------------

def demonstrate_python_block_behavior() -> None:
    print("\n=== Block behavior in Python ===")

    if True:
        branch_value = "created inside an if block"

    # Python does not create a separate lexical scope for ordinary if/for/while
    # blocks. The name remains available in the surrounding function scope.
    print("After if block:", branch_value)

    for loop_value in range(3):
        pass

    print("After for loop, loop_value:", loop_value)

    # A comprehension does have its own iteration-variable scope in Python 3.
    values = [number * number for number in range(3)]
    print("Comprehension result:", values)

    try:
        print(number)  # type: ignore[name-defined]
    except NameError as exc:
        print("Comprehension variable is isolated:", exc)


# ---------------------------------------------------------------------------
# LEGB and lexical name resolution
# ---------------------------------------------------------------------------

lexical_demo = "global value"


def demonstrate_legb() -> None:
    lexical_demo = "enclosing function value"

    def inspect_name() -> None:
        lexical_demo = "local value"
        print("Local lexical_demo:", lexical_demo)

    inspect_name()
    print("Enclosing lexical_demo:", lexical_demo)
    print("Module lexical_demo:", globals()["lexical_demo"])


def demonstrate_nonlocal() -> None:
    print("\n=== nonlocal and enclosing scope ===")

    message = "outer"

    def modify_outer() -> None:
        nonlocal message
        message = "changed by nested function"

    modify_outer()
    print("After nested function:", message)


# ---------------------------------------------------------------------------
# Closures
# ---------------------------------------------------------------------------

def make_multiplier(factor: int) -> Callable[[int], int]:
    """Return a function that remembers factor after this function returns."""

    def multiply(value: int) -> int:
        # factor is not local to multiply. It is resolved from the enclosing
        # function's lexical scope and retained by the returned closure.
        return value * factor

    return multiply


def demonstrate_basic_closure() -> None:
    print("\n=== Basic closure ===")

    multiply_by_three = make_multiplier(3)
    multiply_by_ten = make_multiplier(10)

    print("3 * 8 =", multiply_by_three(8))
    print("10 * 8 =", multiply_by_ten(8))

    print("Captured closure cells:", multiply_by_three.__closure__)
    print("Captured value:", multiply_by_three.__closure__[0].cell_contents)


# ---------------------------------------------------------------------------
# Stateful closures
# ---------------------------------------------------------------------------

def make_counter(start: int = 0) -> Callable[[], int]:
    """Create isolated mutable state without exposing the state variable."""

    count = start

    def next_value() -> int:
        nonlocal count
        count += 1
        return count

    return next_value


def demonstrate_stateful_closure() -> None:
    print("\n=== Stateful closures ===")

    first_counter = make_counter(10)
    second_counter = make_counter(100)

    print(first_counter())
    print(first_counter())
    print(second_counter())
    print(second_counter())

    print(
        "Independent closure state:",
        first_counter.__closure__[0].cell_contents,
        second_counter.__closure__[0].cell_contents,
    )


# ---------------------------------------------------------------------------
# Classic late-binding issue
# ---------------------------------------------------------------------------

def create_bad_multipliers() -> list[Callable[[int], int]]:
    """Demonstrate late binding of a shared loop variable."""
    functions = []

    for factor in range(1, 4):
        # Every closure looks up factor when called, rather than freezing
        # the current loop value.
        functions.append(lambda value: value * factor)

    return functions


def create_good_multipliers() -> list[Callable[[int], int]]:
    """Freeze each factor using a function parameter/default argument."""
    functions = []

    for factor in range(1, 4):
        functions.append(lambda value, factor=factor: value * factor)

    return functions


def demonstrate_late_binding() -> None:
    print("\n=== Closure late binding ===")

    bad = create_bad_multipliers()
    good = create_good_multipliers()

    print("Late-bound results:", [function(10) for function in bad])
    print("Captured-default results:", [function(10) for function in good])


# ---------------------------------------------------------------------------
# Closure-based configuration
# ---------------------------------------------------------------------------

def make_validator(
    minimum: int,
    maximum: int,
) -> Callable[[int], bool]:
    """Create a validator whose policy is captured lexically."""

    if minimum > maximum:
        raise ValueError("minimum cannot exceed maximum")

    def validate(value: int) -> bool:
        return minimum <= value <= maximum

    return validate


def demonstrate_validator_closures() -> None:
    print("\n=== Configuration through closures ===")

    age_validator = make_validator(18, 120)
    score_validator = make_validator(0, 100)

    print("Age 25 valid:", age_validator(25))
    print("Age 12 valid:", age_validator(12))
    print("Score 87 valid:", score_validator(87))
    print("Score 150 valid:", score_validator(150))


# ---------------------------------------------------------------------------
# Closures as decorators
# ---------------------------------------------------------------------------

def audit_calls(function: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator closure that retains the wrapped function."""

    @wraps(function)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        print(f"[AUDIT] Calling {function.__name__}")
        result = function(*args, **kwargs)
        print(f"[AUDIT] Result: {result}")
        return result

    return wrapper


@audit_calls
def calculate_total(price: float, quantity: int) -> float:
    if price < 0 or quantity < 0:
        raise ValueError("price and quantity must be non-negative")
    return price * quantity


def demonstrate_decorator_closure() -> None:
    print("\n=== Decorator closure ===")
    calculate_total(19.99, 3)


# ---------------------------------------------------------------------------
# Parameterized decorator factory
# ---------------------------------------------------------------------------

def retry_on_failure(
    attempts: int,
    delay_seconds: float = 0.0,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Return a decorator configured through a closure."""

    if attempts < 1:
        raise ValueError("attempts must be at least 1")

    def decorator(function: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(function)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_error: Exception | None = None

            for attempt in range(1, attempts + 1):
                try:
                    return function(*args, **kwargs)
                except Exception as exc:
                    last_error = exc
                    print(
                        f"[RETRY] {function.__name__}: "
                        f"attempt {attempt}/{attempts} failed: {exc}"
                    )
                    if attempt < attempts and delay_seconds:
                        time.sleep(delay_seconds)

            assert last_error is not None
            raise last_error

        return wrapper

    return decorator


unstable_attempts = 0


@retry_on_failure(attempts=3)
def simulated_external_operation() -> str:
    global unstable_attempts
    unstable_attempts += 1

    if unstable_attempts < 3:
        raise RuntimeError("temporary service failure")

    return "operation completed"


def demonstrate_parameterized_decorator() -> None:
    print("\n=== Parameterized decorator closure ===")
    print(simulated_external_operation())


# ---------------------------------------------------------------------------
# Memoization with a closure
# ---------------------------------------------------------------------------

def memoize(function: Callable[[int], int]) -> Callable[[int], int]:
    """Cache function results inside a closure-owned dictionary."""

    cache: dict[int, int] = {}

    @wraps(function)
    def wrapper(value: int) -> int:
        if value not in cache:
            cache[value] = function(value)
        return cache[value]

    return wrapper


@memoize
def fibonacci(n: int) -> int:
    if n < 0:
        raise ValueError("n must be non-negative")
    if n < 2:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)


def demonstrate_memoization() -> None:
    print("\n=== Closure-based memoization ===")
    print("Fibonacci(35):", fibonacci(35))
    print("Cache retained by closure:", fibonacci.__closure__)


# ---------------------------------------------------------------------------
# Closure versus object state
# ---------------------------------------------------------------------------

@dataclass
class Account:
    balance: float


def make_private_account(initial_balance: float) -> tuple[
    Callable[[float], None],
    Callable[[], float],
]:
    """Encapsulate balance in a closure rather than exposing an object field."""

    if initial_balance < 0:
        raise ValueError("initial balance cannot be negative")

    balance = initial_balance

    def deposit(amount: float) -> None:
        nonlocal balance
        if amount <= 0:
            raise ValueError("deposit must be positive")
        balance += amount

    def get_balance() -> float:
        return balance

    return deposit, get_balance


def demonstrate_encapsulation() -> None:
    print("\n=== Closure-based encapsulation ===")

    deposit, get_balance = make_private_account(500)
    deposit(125)
    deposit(75)

    print("Private balance:", get_balance())

    # A normal object exposes its declared attribute directly.
    account = Account(500)
    account.balance += 200
    print("Object balance:", account.balance)


# ---------------------------------------------------------------------------
# Closures with callbacks and event processing
# ---------------------------------------------------------------------------

def make_event_handler(
    event_name: str,
    minimum_severity: int,
) -> Callable[[dict[str, Any]], bool]:
    """Create a callback configured for one event type and severity policy."""

    def handle(event: dict[str, Any]) -> bool:
        return (
            event.get("type") == event_name
            and int(event.get("severity", 0)) >= minimum_severity
        )

    return handle


def process_events(
    events: Iterable[dict[str, Any]],
    handlers: Iterable[Callable[[dict[str, Any]], bool]],
) -> list[dict[str, Any]]:
    matched: list[dict[str, Any]] = []

    for event in events:
        if any(handler(event) for handler in handlers):
            matched.append(event)

    return matched


def demonstrate_callback_closures() -> None:
    print("\n=== Callback closures ===")

    events = [
        {"type": "security", "severity": 5, "message": "login anomaly"},
        {"type": "performance", "severity": 2, "message": "slow request"},
        {"type": "security", "severity": 1, "message": "minor event"},
    ]

    security_handler = make_event_handler("security", 4)
    performance_handler = make_event_handler("performance", 3)

    matches = process_events(
        events,
        [security_handler, performance_handler],
    )

    for event in matches:
        print(event)


# ---------------------------------------------------------------------------
# Scope inspection
# ---------------------------------------------------------------------------

def demonstrate_scope_inspection() -> None:
    print("\n=== Runtime scope inspection ===")

    local_value = "local"

    def nested() -> None:
        nested_value = "nested"
        print("nested locals:", locals())

    nested()

    print("Current locals:", locals())
    print("Global APPLICATION_NAME:", globals()["APPLICATION_NAME"])
    print("Current function name:", demonstrate_scope_inspection.__name__)
    print("Local value:", local_value)


# ---------------------------------------------------------------------------
# Common closure failure: mutable captured state
# ---------------------------------------------------------------------------

def make_message_collector() -> Callable[[str], list[str]]:
    """A mutable object can be changed without nonlocal for its mutation."""

    messages: list[str] = []

    def collect(message: str) -> list[str]:
        # append mutates the captured list. Rebinding messages would require
        # nonlocal, but mutating the existing object does not.
        messages.append(message)
        return list(messages)

    return collect


def demonstrate_mutable_capture() -> None:
    print("\n=== Mutable captured state ===")

    collector = make_message_collector()
    print(collector("first"))
    print(collector("second"))


# ---------------------------------------------------------------------------
# Testing lexical isolation
# ---------------------------------------------------------------------------

def run_assertions() -> None:
    """Small executable checks for the key scope and closure invariants."""

    multiplier = make_multiplier(4)
    assert multiplier(5) == 20

    validator = make_validator(10, 20)
    assert validator(10)
    assert validator(20)
    assert not validator(21)

    counter_a = make_counter()
    counter_b = make_counter()
    assert counter_a() == 1
    assert counter_a() == 2
    assert counter_b() == 1

    good = create_good_multipliers()
    assert [fn(5) for fn in good] == [5, 10, 15]

    collector = make_message_collector()
    assert collector("x") == ["x"]
    assert collector("y") == ["x", "y"]

    print("\nAll scope and closure assertions passed.")


def main() -> None:
    print(f"{APPLICATION_NAME}: Scope and Closures")

    show_global_scope()
    demonstrate_global_mutation()
    demonstrate_function_scope()
    demonstrate_python_block_behavior()
    demonstrate_legb()
    demonstrate_nonlocal()
    demonstrate_basic_closure()
    demonstrate_stateful_closure()
    demonstrate_late_binding()
    demonstrate_validator_closures()
    demonstrate_decorator_closure()
    demonstrate_parameterized_decorator()
    demonstrate_memoization()
    demonstrate_encapsulation()
    demonstrate_callback_closures()
    demonstrate_scope_inspection()
    demonstrate_mutable_capture()
    run_assertions()


if __name__ == "__main__":
    main()
