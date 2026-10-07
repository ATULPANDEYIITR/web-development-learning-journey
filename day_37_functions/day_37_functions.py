from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Optional


def greet(name: str) -> str:
    """A standard function declaration with one parameter and one return value."""
    return f"Hello, {name}!"


def calculate_total(price: float, quantity: int = 1) -> float:
    """Demonstrates parameters, a default value, validation, and a return value."""
    if price < 0:
        raise ValueError("price cannot be negative")
    if quantity < 0:
        raise ValueError("quantity cannot be negative")
    return price * quantity


# A function can be stored in a variable because Python functions are first-class objects.
discounted_total = lambda amount, rate: amount * (1 - rate)


def apply_operation(
    value: float,
    operation: Callable[[float], float],
) -> float:
    """Accept a function as an argument and return the function's result."""
    return operation(value)


def square(number: float) -> float:
    return number * number


def make_multiplier(factor: float) -> Callable[[float], float]:
    """Return a new function that remembers factor through a closure."""
    def multiplier(value: float) -> float:
        return value * factor

    return multiplier


def demonstrate_scope() -> tuple[str, str, str]:
    """Demonstrate local, enclosing, and global scope."""
    global_message = "module-level value"

    def outer() -> str:
        enclosing_message = "enclosing value"

        def inner() -> str:
            local_message = "local value"
            return f"{global_message} | {enclosing_message} | {local_message}"

        return inner()

    return global_message, "function-local scope exists only during the call", outer()


def counter_factory() -> Callable[[], int]:
    """A closure can preserve state between function calls."""
    count = 0

    def next_count() -> int:
        nonlocal count
        count += 1
        return count

    return next_count


def summarize_numbers(numbers: Iterable[float]) -> dict[str, float]:
    """Process an iterable without requiring the caller to provide a list."""
    values = list(numbers)
    if not values:
        raise ValueError("at least one number is required")

    return {
        "count": len(values),
        "minimum": min(values),
        "maximum": max(values),
        "average": sum(values) / len(values),
    }


def divide(dividend: float, divisor: float) -> float:
    """Explicitly handle a common failure condition."""
    if divisor == 0:
        raise ZeroDivisionError("division by zero is not allowed")
    return dividend / divisor


def safe_call(
    function: Callable[..., object],
    *args: object,
    **kwargs: object,
) -> Optional[object]:
    """Execute a function while converting expected runtime failures to None."""
    try:
        return function(*args, **kwargs)
    except (ValueError, TypeError, ZeroDivisionError) as error:
        print(f"Function call failed: {error}")
        return None


@dataclass
class Employee:
    name: str
    salary: float


class PayrollService:
    """Use methods as functions bound to an object."""

    def __init__(self, tax_rate: float) -> None:
        if not 0 <= tax_rate <= 1:
            raise ValueError("tax_rate must be between 0 and 1")
        self.tax_rate = tax_rate

    def gross_pay(self, employee: Employee, bonus: float = 0.0) -> float:
        if employee.salary < 0 or bonus < 0:
            raise ValueError("salary and bonus cannot be negative")
        return employee.salary + bonus

    def net_pay(self, employee: Employee, bonus: float = 0.0) -> float:
        gross = self.gross_pay(employee, bonus)
        return gross * (1 - self.tax_rate)


def compose(
    first: Callable[[float], float],
    second: Callable[[float], float],
) -> Callable[[float], float]:
    """Return a function representing second(first(x))."""

    def composed(value: float) -> float:
        return second(first(value))

    return composed


def execute_pipeline(
    values: Iterable[float],
    *functions: Callable[[float], float],
) -> list[float]:
    """Apply an arbitrary sequence of functions to every value."""
    result = list(values)

    for function in functions:
        result = [function(value) for value in result]

    return result


def recursive_factorial(number: int) -> int:
    """Recursive functions need a base case to prevent infinite recursion."""
    if number < 0:
        raise ValueError("factorial requires a non-negative integer")
    if number in (0, 1):
        return 1
    return number * recursive_factorial(number - 1)


def iterative_factorial(number: int) -> int:
    """The iterative alternative avoids recursive call-stack growth."""
    if number < 0:
        raise ValueError("factorial requires a non-negative integer")

    result = 1
    for current in range(2, number + 1):
        result *= current
    return result


def create_validator(
    minimum: float,
    maximum: float,
) -> Callable[[float], bool]:
    """Generate a reusable validation function from configuration."""
    if minimum > maximum:
        raise ValueError("minimum cannot exceed maximum")

    def validator(value: float) -> bool:
        return minimum <= value <= maximum

    return validator


def demonstrate_mutable_default_safely(
    value: str,
    items: Optional[list[str]] = None,
) -> list[str]:
    """
    Use None instead of a mutable default argument.
    A new list is created for each call when items is omitted.
    """
    if items is None:
        items = []
    items.append(value)
    return items


def run_examples() -> None:
    print("=== Function declarations and return values ===")
    print(greet("Atul"))
    print(calculate_total(250.0, 3))
    print(calculate_total(100.0))

    print("\n=== Function expressions and lambda functions ===")
    print(discounted_total(1000, 0.15))
    print(apply_operation(7, square))

    print("\n=== Functions as arguments ===")
    operations = {
        "square": square,
        "absolute": abs,
        "double": lambda value: value * 2,
    }

    for name, operation in operations.items():
        print(name, "->", apply_operation(-5, operation))

    print("\n=== Closures ===")
    triple = make_multiplier(3)
    print(triple(10))

    counter = counter_factory()
    print(counter())
    print(counter())
    print(counter())

    print("\n=== Scope ===")
    print(demonstrate_scope())

    print("\n=== Data processing ===")
    print(summarize_numbers([10, 20, 30, 40]))

    print("\n=== Error handling ===")
    print(safe_call(divide, 10, 2))
    print(safe_call(divide, 10, 0))
    print(safe_call(calculate_total, -10, 2))

    print("\n=== Object methods ===")
    employee = Employee("Ravi", 60000)
    payroll = PayrollService(0.20)
    print("Gross:", payroll.gross_pay(employee, 5000))
    print("Net:", payroll.net_pay(employee, 5000))

    print("\n=== Function composition ===")
    add_ten = lambda value: value + 10
    multiply_two = lambda value: value * 2
    composed = compose(add_ten, multiply_two)
    print(composed(5))

    print("\n=== Function pipeline ===")
    results = execute_pipeline(
        [1, 2, 3, 4],
        lambda value: value * 2,
        lambda value: value + 1,
        square,
    )
    print(results)

    print("\n=== Recursion versus iteration ===")
    print("Recursive:", recursive_factorial(6))
    print("Iterative:", iterative_factorial(6))

    print("\n=== Generated validators ===")
    percentage_validator = create_validator(0, 100)
    for percentage in (-5, 25, 100, 110):
        print(percentage, percentage_validator(percentage))

    print("\n=== Safe mutable state ===")
    print(demonstrate_mutable_default_safely("first"))
    print(demonstrate_mutable_default_safely("second"))


if __name__ == "__main__":
    run_examples()
