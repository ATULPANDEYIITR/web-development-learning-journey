"""
Operator Laboratory: Arithmetic, comparison, logical, assignment,
ternary-style expressions, nullish coalescing, and optional chaining.

Self-contained Python 3 program.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


def heading(title: str) -> None:
    print(f"\n{'=' * 72}\n{title}\n{'=' * 72}")


def arithmetic_demo() -> None:
    heading("Arithmetic operators")

    a = 17
    b = 5

    print(f"a + b  = {a + b}")
    print(f"a - b  = {a - b}")
    print(f"a * b  = {a * b}")
    print(f"a / b  = {a / b}")
    print(f"a // b = {a // b}")
    print(f"a % b  = {a % b}")
    print(f"a ** b = {a ** b}")

    # Python has no ++ or -- operators. Assignment must be explicit.
    counter = 10
    counter += 3
    counter -= 2
    counter *= 4
    counter //= 5
    print(f"compound assignment result = {counter}")

    try:
        print(10 / 0)
    except ZeroDivisionError as exc:
        print(f"division failure handled: {exc}")


def comparison_demo() -> None:
    heading("Comparison operators")

    left = 42
    right = 30

    comparisons = {
        "left == right": left == right,
        "left != right": left != right,
        "left > right": left > right,
        "left >= right": left >= right,
        "left < right": left < right,
        "left <= right": left <= right,
    }

    for expression, result in comparisons.items():
        print(f"{expression:20} -> {result}")

    # Identity and equality are different operations.
    first = [1, 2, 3]
    second = [1, 2, 3]
    alias = first

    print(f"first == second -> {first == second}")
    print(f"first is second -> {first is second}")
    print(f"first is alias  -> {first is alias}")


def logical_demo() -> None:
    heading("Logical operators and short-circuit evaluation")

    is_authenticated = True
    is_active = True
    has_admin_role = False

    print("authenticated AND active:", is_authenticated and is_active)
    print("authenticated OR admin:", is_authenticated or has_admin_role)
    print("NOT admin:", not has_admin_role)

    # "and" and "or" return operands rather than forcing a Boolean result.
    configured_name = ""
    fallback_name = "production"
    selected_name = configured_name or fallback_name
    print(f"selected name using OR fallback: {selected_name}")

    def expensive_check() -> bool:
        print("expensive check executed")
        return True

    # Because the first operand is False, Python does not call the function.
    result = False and expensive_check()
    print("short-circuit result:", result)


def conditional_expression_demo() -> None:
    heading("Conditional expression: Python's ternary form")

    score = 84
    classification = "pass" if score >= 50 else "fail"
    print(f"score={score}, classification={classification}")

    temperature = 38
    state = "hot" if temperature >= 35 else "moderate"
    print(f"temperature={temperature}, state={state}")


def nullish_style_demo() -> None:
    heading("Nullish-style fallback with None")

    # Python has no ?? operator. The explicit None check is safer than
    # "value or fallback" when valid falsy values such as 0 or "" matter.
    def coalesce(value: Any, fallback: Any) -> Any:
        return fallback if value is None else value

    values = [None, 0, "", False, "configured"]

    for value in values:
        print(
            f"value={value!r:12} -> "
            f"coalesce(value, 'default')={coalesce(value, 'default')!r}"
        )

    print("This preserves 0, empty strings, and False because only None is replaced.")


@dataclass
class Contact:
    email: str | None = None


@dataclass
class Profile:
    contact: Contact | None = None


@dataclass
class User:
    profile: Profile | None = None


def optional_chaining_style_demo() -> None:
    heading("Optional-chaining-style safe traversal")

    # Python does not have JavaScript's ?. operator. getattr with a default
    # can model safe traversal when the object structure is dynamic.
    def safe_getattr(obj: Any, *attributes: str) -> Any:
        current = obj
        for attribute in attributes:
            if current is None:
                return None
            current = getattr(current, attribute, None)
        return current

    user_with_email = User(Profile(Contact("engineer@example.com")))
    user_without_profile = User()

    print(
        safe_getattr(
            user_with_email,
            "profile",
            "contact",
            "email",
        )
    )
    print(
        safe_getattr(
            user_without_profile,
            "profile",
            "contact",
            "email",
        )
    )


def operator_precedence_demo() -> None:
    heading("Precedence and explicit grouping")

    expression_without_parentheses = 2 + 3 * 4
    expression_with_parentheses = (2 + 3) * 4

    print("2 + 3 * 4 =", expression_without_parentheses)
    print("(2 + 3) * 4 =", expression_with_parentheses)

    # Parentheses make mixed logical conditions easier to audit.
    age = 27
    verified = True
    country = "IN"

    eligible = verified and (age >= 18 and country in {"IN", "US"})
    print("eligible:", eligible)


def assignment_expression_demo() -> None:
    heading("Assignment expression")

    # Python's := operator assigns and returns a value inside an expression.
    if (length := len("repository")) >= 8:
        print(f"length={length}; long identifier")


def collection_operator_demo() -> None:
    heading("Operators with collections")

    permissions = {"read", "write"}
    required = {"read"}

    print("membership:", "read" in permissions)
    print("subset:", required <= permissions)
    print("intersection:", permissions & {"write", "delete"})
    print("union:", permissions | {"admin"})
    print("difference:", permissions - {"write"})


def real_world_policy_demo() -> None:
    heading("Realistic operator-based policy evaluation")

    @dataclass
    class PullRequest:
        changed_files: int
        additions: int
        deletions: int
        approved_reviews: int
        failing_checks: int
        draft: bool
        branch: str

    pull_request = PullRequest(
        changed_files=8,
        additions=145,
        deletions=31,
        approved_reviews=2,
        failing_checks=0,
        draft=False,
        branch="main",
    )

    size_ok = pull_request.changed_files <= 20 and (
        pull_request.additions + pull_request.deletions
    ) <= 500

    reviews_ok = pull_request.approved_reviews >= 2
    checks_ok = pull_request.failing_checks == 0
    target_ok = pull_request.branch == "main"
    merge_allowed = (
        not pull_request.draft
        and size_ok
        and reviews_ok
        and checks_ok
        and target_ok
    )

    print("size policy:", size_ok)
    print("review policy:", reviews_ok)
    print("status policy:", checks_ok)
    print("target policy:", target_ok)
    print("merge allowed:", merge_allowed)


def safe_divide(numerator: float, denominator: float) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator


def operator_edge_cases() -> None:
    heading("Edge cases")

    print("10 / 4 =", safe_divide(10, 4))
    print("10 / 0 =", safe_divide(10, 0))

    # Floating-point equality can be surprising because binary floating-point
    # cannot exactly represent many decimal fractions.
    calculation = 0.1 + 0.2
    print("0.1 + 0.2 =", calculation)
    print("exact equality with 0.3:", calculation == 0.3)
    print("tolerance comparison:", abs(calculation - 0.3) < 1e-9)

    # Chained comparisons are interpreted as a logical conjunction.
    score = 76
    print("50 <= score <= 100:", 50 <= score <= 100)


def mini_tests() -> None:
    heading("Executable checks")

    assert 7 + 3 == 10
    assert 7 * 3 == 21
    assert 10 // 3 == 3
    assert 10 % 3 == 1
    assert 5 < 8 and 8 < 10
    assert ("pass" if 80 >= 50 else "fail") == "pass"

    def coalesce(value: Any, fallback: Any) -> Any:
        return fallback if value is None else value

    assert coalesce(None, "fallback") == "fallback"
    assert coalesce(0, "fallback") == 0

    print("All operator checks passed.")


def main() -> None:
    arithmetic_demo()
    comparison_demo()
    logical_demo()
    conditional_expression_demo()
    nullish_style_demo()
    optional_chaining_style_demo()
    operator_precedence_demo()
    assignment_expression_demo()
    collection_operator_demo()
    real_world_policy_demo()
    operator_edge_cases()
    mini_tests()


if __name__ == "__main__":
    main()
