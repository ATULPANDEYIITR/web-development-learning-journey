"""
JavaScript Variables and Data Types: A cross-language learning model.

This executable Python program models the major JavaScript variable and data
type concepts requested by the accompanying JavaScript implementation:
var, let, const, strings, numbers, booleans, null, undefined, symbols, and
BigInt.

Python is used as a teaching model rather than pretending that Python has
JavaScript's exact semantics. The program explicitly represents JavaScript
values that Python does not have natively, including undefined, Symbol, and
BigInt, and demonstrates the important differences between mutable bindings,
immutable bindings, primitive values, and large integers.

Run with:
    python javascript_data_types_model.py
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Any, Callable
import math
import sys


class UndefinedType:
    """Singleton-like representation of JavaScript's undefined value."""

    __slots__ = ()

    def __repr__(self) -> str:
        return "undefined"

    def __str__(self) -> str:
        return "undefined"


UNDEFINED = UndefinedType()


@dataclass(frozen=True)
class JavaScriptSymbol:
    """
    A simplified model of a JavaScript Symbol.

    Symbols are unique primitive values. Two separately created symbols with
    the same description are still different values.
    """

    description: str | None
    identity: int

    def __repr__(self) -> str:
        if self.description is None:
            return f"Symbol(<anonymous>, id={self.identity})"
        return f"Symbol({self.description!r}, id={self.identity})"


class JavaScriptBigInt:
    """
    A model of JavaScript BigInt.

    Python integers already support arbitrary precision, so this wrapper is
    needed to make the JavaScript distinction explicit. In JavaScript,
    BigInt arithmetic must not be mixed directly with Number arithmetic.
    """

    __slots__ = ("value",)

    def __init__(self, value: int | str) -> None:
        self.value = int(value)

    def __add__(self, other: "JavaScriptBigInt") -> "JavaScriptBigInt":
        self._require_bigint(other)
        return JavaScriptBigInt(self.value + other.value)

    def __sub__(self, other: "JavaScriptBigInt") -> "JavaScriptBigInt":
        self._require_bigint(other)
        return JavaScriptBigInt(self.value - other.value)

    def __mul__(self, other: "JavaScriptBigInt") -> "JavaScriptBigInt":
        self._require_bigint(other)
        return JavaScriptBigInt(self.value * other.value)

    def __floordiv__(self, other: "JavaScriptBigInt") -> "JavaScriptBigInt":
        self._require_bigint(other)
        if other.value == 0:
            raise ZeroDivisionError("BigInt division by zero")
        return JavaScriptBigInt(self.value // other.value)

    def __repr__(self) -> str:
        return f"{self.value}n"

    @staticmethod
    def _require_bigint(other: object) -> None:
        if not isinstance(other, JavaScriptBigInt):
            raise TypeError("JavaScript BigInt arithmetic requires another BigInt")


class BindingKind(Enum):
    """Variable declaration forms used by JavaScript."""

    VAR = "var"
    LET = "let"
    CONST = "const"


@dataclass
class JavaScriptBinding:
    """
    A simplified binding model.

    JavaScript's actual lexical environment and hoisting rules are more
    detailed than this educational model, so this class focuses on the
    observable distinction between declaration kind and reassignment.
    """

    name: str
    kind: BindingKind
    value: Any
    initialized: bool = True

    @property
    def mutable(self) -> bool:
        return self.kind != BindingKind.CONST

    def assign(self, value: Any) -> None:
        if not self.mutable:
            raise TypeError(
                f"Cannot reassign const binding '{self.name}'"
            )
        self.value = value

    def read(self) -> Any:
        if not self.initialized:
            raise ReferenceError(
                f"Cannot access '{self.name}' before initialization"
            )
        return self.value


class JavaScriptEnvironment:
    """
    Small environment for modeling variable declarations and lookup.

    This does not attempt to implement all ECMAScript scoping rules. It
    intentionally isolates the binding behavior relevant to var, let, and
    const.
    """

    def __init__(self) -> None:
        self.bindings: dict[str, JavaScriptBinding] = {}

    def declare(
        self,
        name: str,
        kind: BindingKind,
        value: Any = UNDEFINED,
        initialized: bool = True,
    ) -> JavaScriptBinding:
        if name in self.bindings:
            existing = self.bindings[name]
            if kind in {BindingKind.LET, BindingKind.CONST}:
                raise SyntaxError(
                    f"Cannot redeclare lexical binding '{name}'"
                )
            if existing.kind != BindingKind.VAR:
                raise SyntaxError(
                    f"Cannot redeclare '{name}' with var after let/const"
                )

        binding = JavaScriptBinding(
            name=name,
            kind=kind,
            value=value,
            initialized=initialized,
        )
        self.bindings[name] = binding
        return binding

    def get(self, name: str) -> Any:
        if name not in self.bindings:
            raise NameError(f"{name} is not defined")
        return self.bindings[name].read()

    def assign(self, name: str, value: Any) -> None:
        if name not in self.bindings:
            raise NameError(f"{name} is not defined")
        self.bindings[name].assign(value)


class SymbolFactory:
    """Creates unique JavaScript-like Symbol primitive values."""

    def __init__(self) -> None:
        self._counter = 0

    def create(self, description: str | None = None) -> JavaScriptSymbol:
        self._counter += 1
        return JavaScriptSymbol(description, self._counter)


def javascript_typeof(value: Any) -> str:
    """
    Approximate JavaScript's typeof operator for the modeled values.

    Important JavaScript behavior represented here:
    typeof null === "object"
    typeof undefined === "undefined"
    typeof Symbol() === "symbol"
    typeof 1n === "bigint"
    """

    if value is UNDEFINED:
        return "undefined"
    if value is None:
        return "object"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, JavaScriptSymbol):
        return "symbol"
    if isinstance(value, JavaScriptBigInt):
        return "bigint"
    if isinstance(value, (int, float, Decimal)):
        return "number"
    if isinstance(value, str):
        return "string"
    if callable(value):
        return "function"
    return "object"


def javascript_string(value: Any) -> str:
    """Approximate useful JavaScript String(value) conversions."""

    if value is UNDEFINED:
        return "undefined"
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, JavaScriptBigInt):
        return f"{value.value}"
    if isinstance(value, JavaScriptSymbol):
        return (
            f"Symbol({value.description})"
            if value.description is not None
            else "Symbol()"
        )
    return str(value)


def safe_number(value: str | int | float) -> float:
    """
    Convert a textual value to a JavaScript-like Number model.

    JavaScript Number uses IEEE-754 double precision. Python float is also
    normally IEEE-754 double precision, which makes it useful for this model.
    """

    if isinstance(value, bool):
        return 1.0 if value else 0.0

    if isinstance(value, (int, float)):
        return float(value)

    text = value.strip()
    if not text:
        return 0.0

    try:
        return float(text)
    except ValueError as exc:
        raise ValueError(f"Cannot convert {value!r} to a Number") from exc


def demonstrate_var_let_const() -> None:
    """Demonstrate declaration, reassignment, and binding differences."""

    print("\n=== var, let, and const ===")

    environment = JavaScriptEnvironment()

    count = environment.declare("count", BindingKind.LET, 10)
    print(f"let count = {count.value}")
    environment.assign("count", 11)
    print(f"after reassignment: count = {environment.get('count')}")

    application_name = environment.declare(
        "applicationName",
        BindingKind.CONST,
        "Repository Inspector",
    )
    print(
        "const applicationName = "
        f"{application_name.value!r}"
    )

    try:
        environment.assign("applicationName", "Changed")
    except TypeError as exc:
        print(f"const reassignment rejected: {exc}")

    score = environment.declare("score", BindingKind.VAR, 25)
    print(f"var score = {score.value}")
    environment.assign("score", 40)
    print(f"after reassignment: score = {environment.get('score')}")

    # const prevents rebinding, not mutation of an object referenced by the
    # binding. This models an important JavaScript distinction.
    config = environment.declare(
        "config",
        BindingKind.CONST,
        {"mode": "development", "debug": True},
    )
    config.value["mode"] = "production"
    print(f"const object after property mutation: {config.value}")

    try:
        environment.assign("config", {"mode": "test"})
    except TypeError as exc:
        print(f"const object rebinding rejected: {exc}")


def demonstrate_strings() -> None:
    """Demonstrate JavaScript string values and useful operations."""

    print("\n=== Strings ===")

    repository = "variable-data-types"
    owner = "ATULPANDEYIITR"

    # JavaScript strings are immutable primitive values. Operations produce
    # new string values rather than modifying the original string in place.
    display_name = f"{owner}/{repository}"
    print(f"Template-style interpolation result: {display_name}")

    message = "  Pull requests should be reviewable.  "
    normalized = message.strip().lower()
    print(f"Original: {message!r}")
    print(f"Normalized: {normalized!r}")
    print(f"Length: {len(message)}")
    print(f"Contains 'reviewable': {'reviewable' in normalized}")

    # A realistic use case is constructing a branch reference safely from
    # controlled components rather than blindly concatenating arbitrary input.
    branch_prefix = "feature"
    branch_name = "data-types"
    safe_branch = f"{branch_prefix}/{branch_name}"
    print(f"Constructed branch name: {safe_branch}")

    if "\n" in safe_branch or "\r" in safe_branch:
        raise ValueError("Branch name contains a line break")

    # Strings can contain Unicode text. JavaScript's string length is based on
    # UTF-16 code units, so some Unicode characters have length greater than 1.
    unicode_value = "JavaScript 🚀"
    utf16_code_units = len(unicode_value.encode("utf-16-le")) // 2
    print(
        f"Unicode value: {unicode_value!r}; "
        f"UTF-16 code units: {utf16_code_units}"
    )


def demonstrate_numbers() -> None:
    """Demonstrate Number values, floating-point limits, and NaN."""

    print("\n=== Numbers ===")

    integer_like = 42
    decimal_value = 19.95
    negative_value = -7

    print(f"integer-like Number: {integer_like}")
    print(f"decimal Number: {decimal_value}")
    print(f"negative Number: {negative_value}")

    # JavaScript Number cannot exactly represent every decimal fraction.
    # The same IEEE-754 behavior appears when Python uses float.
    result = 0.1 + 0.2
    print(f"0.1 + 0.2 using binary floating point: {result!r}")
    print(
        "Rounded for display: "
        f"{result:.2f}"
    )

    maximum_safe_integer = 2**53 - 1
    unsafe_integer = 2**53

    print(f"Number.MAX_SAFE_INTEGER equivalent: {maximum_safe_integer}")
    print(f"First integer beyond the safe-integer boundary: {unsafe_integer}")

    # JavaScript Number also has NaN and Infinity. Python's float supports
    # corresponding IEEE-754 values.
    not_a_number = float("nan")
    positive_infinity = float("inf")

    print(f"NaN is NaN: {math.isnan(not_a_number)}")
    print(f"Infinity is infinite: {math.isinf(positive_infinity)}")

    parsed = safe_number("384")
    print(f'Number("384") model: {parsed}')

    try:
        safe_number("not-a-number")
    except ValueError as exc:
        print(f"Invalid numeric conversion rejected: {exc}")


def demonstrate_booleans() -> None:
    """Demonstrate boolean values and explicit condition handling."""

    print("\n=== Booleans ===")

    checks = {
        "tests_pass": True,
        "has_conflicts": False,
        "review_complete": True,
    }

    for name, value in checks.items():
        print(f"{name} = {value}; typeof = {javascript_typeof(value)}")

    merge_allowed = (
        checks["tests_pass"]
        and not checks["has_conflicts"]
        and checks["review_complete"]
    )

    print(f"merge_allowed = {merge_allowed}")

    # Explicit comparisons are preferred when a value may be ambiguous. This
    # avoids accidentally treating arbitrary strings or numbers as booleans.
    raw_flag = "true"
    explicit_flag = raw_flag.lower() == "true"
    print(f"Parsed boolean flag: {explicit_flag}")


def demonstrate_null_and_undefined() -> None:
    """
    Contrast JavaScript null with undefined.

    null normally represents an intentional absence of a value, while
    undefined commonly represents a missing value or an uninitialized
    property/result.
    """

    print("\n=== null and undefined ===")

    intentionally_empty = None
    missing_value = UNDEFINED

    print(
        f"null model: {intentionally_empty!r}; "
        f"typeof = {javascript_typeof(intentionally_empty)}"
    )
    print(
        f"undefined model: {missing_value}; "
        f"typeof = {javascript_typeof(missing_value)}"
    )

    record = {
        "title": "Data Types",
        "description": None,
        "reviewer": UNDEFINED,
    }

    print(f"description exists and is intentionally empty: {record['description'] is None}")
    print(f"reviewer is missing: {record['reviewer'] is UNDEFINED}")

    # Accessing a missing dictionary key through [] raises KeyError in Python.
    # JavaScript property access instead commonly produces undefined, which is
    # why this model stores UNDEFINED explicitly.
    print(f"Missing reviewer value: {record['reviewer']}")


def demonstrate_symbols() -> None:
    """Demonstrate uniqueness and registry-like symbol behavior."""

    print("\n=== Symbols ===")

    symbols = SymbolFactory()

    first = symbols.create("repositoryId")
    second = symbols.create("repositoryId")

    print(f"first: {first}")
    print(f"second: {second}")
    print(f"Same description: {first.description == second.description}")
    print(f"Same symbol identity: {first.identity == second.identity}")

    metadata = {
        first: "internal repository metadata",
        second: "another metadata slot",
    }

    print(f"Distinct symbol keys: {len(metadata)}")

    # Symbols are useful when a property key should avoid accidental collision
    # with ordinary string property names.
    public_key = "repositoryId"
    private_key = symbols.create("repositoryId")

    object_like = {
        public_key: "public value",
        private_key: "internal value",
    }

    print(f"String-keyed property: {object_like[public_key]}")
    print(f"Symbol-keyed property: {object_like[private_key]}")


def demonstrate_bigint() -> None:
    """Demonstrate arbitrary-precision integer semantics."""

    print("\n=== BigInt ===")

    account_balance = JavaScriptBigInt("900719925474099312345")
    incoming_transfer = JavaScriptBigInt("125000000000000000")
    updated_balance = account_balance + incoming_transfer

    print(f"account balance: {account_balance}")
    print(f"incoming transfer: {incoming_transfer}")
    print(f"updated balance: {updated_balance}")

    # In JavaScript, BigInt and Number are intentionally separate numeric
    # domains. This prevents silent precision loss at large integer values.
    try:
        account_balance._require_bigint(10)
    except TypeError as exc:
        print(f"BigInt/Number mixing rejected: {exc}")

    quantity = JavaScriptBigInt(8)
    price = JavaScriptBigInt(1250)
    total = quantity * price
    print(f"8n * 1250n = {total}")

    try:
        JavaScriptBigInt(10) // JavaScriptBigInt(0)
    except ZeroDivisionError as exc:
        print(f"BigInt failure handled: {exc}")


def demonstrate_type_inspection() -> None:
    """Inspect every requested JavaScript primitive category."""

    print("\n=== Type Inspection ===")

    symbol_factory = SymbolFactory()

    values = {
        "string": "branch",
        "number": 123.5,
        "boolean": True,
        "null": None,
        "undefined": UNDEFINED,
        "symbol": symbol_factory.create("unique"),
        "bigint": JavaScriptBigInt(12345678901234567890),
    }

    for name, value in values.items():
        print(
            f"{name:10} value={javascript_string(value)!r:35} "
            f"typeof={javascript_typeof(value)}"
        )


def demonstrate_validation_pipeline() -> None:
    """
    Apply multiple data types to a realistic configuration record.

    The example shows why a program should distinguish missing values from
    intentionally empty values and why numeric ranges should be validated
    before business logic uses them.
    """

    print("\n=== Typed Configuration Validation ===")

    configuration = {
        "repository": "variable-data-types",
        "enabled": True,
        "max_retries": 3,
        "timeout_seconds": 15.5,
        "description": None,
        "external_identifier": UNDEFINED,
        "audit_token": JavaScriptSymbol("audit"),
        "event_sequence": JavaScriptBigInt(9007199254740993),
    }

    errors: list[str] = []

    if not isinstance(configuration["repository"], str):
        errors.append("repository must be a string")
    elif not configuration["repository"].strip():
        errors.append("repository must not be empty")

    if not isinstance(configuration["enabled"], bool):
        errors.append("enabled must be boolean")

    retries = configuration["max_retries"]
    if isinstance(retries, bool) or not isinstance(retries, int):
        errors.append("max_retries must be an integer")
    elif not 0 <= retries <= 10:
        errors.append("max_retries must be between 0 and 10")

    timeout = configuration["timeout_seconds"]
    if not isinstance(timeout, (int, float)) or isinstance(timeout, bool):
        errors.append("timeout_seconds must be numeric")
    elif not 0 < float(timeout) <= 300:
        errors.append("timeout_seconds must be greater than 0 and at most 300")

    if configuration["description"] is not None:
        if not isinstance(configuration["description"], str):
            errors.append("description must be string or null")

    if configuration["external_identifier"] is not UNDEFINED:
        errors.append("external_identifier was expected to be absent")

    if not isinstance(configuration["audit_token"], JavaScriptSymbol):
        errors.append("audit_token must be a Symbol")

    if not isinstance(configuration["event_sequence"], JavaScriptBigInt):
        errors.append("event_sequence must be a BigInt")

    if errors:
        print("Configuration rejected:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("Configuration passed all validation rules.")

    print(
        "Large event sequence is represented as BigInt: "
        f"{configuration['event_sequence']}"
    )


def demonstrate_edge_cases() -> None:
    """Demonstrate common mistakes and failure conditions."""

    print("\n=== Edge Cases and Failure Conditions ===")

    # Boolean is a subclass of int in Python, so validation must explicitly
    # reject bool when modeling a JavaScript numeric field.
    if isinstance(True, int):
        print(
            "Python-specific validation trap: bool is an int subclass; "
            "explicit type checks are required."
        )

    # JavaScript's null typeof result is historically surprising.
    print(f"typeof null model: {javascript_typeof(None)}")
    print("This reflects JavaScript's historical typeof null === 'object' behavior.")

    # Undefined and null should not be collapsed when their semantics matter.
    print(f"undefined is distinct from null: {UNDEFINED is not None}")

    # Symbols should not be coerced into ordinary strings implicitly in logic.
    symbol = SymbolFactory().create("securityKey")
    print(f"Symbol remains a distinct primitive: {symbol}")

    # BigInt is designed for exact integer arithmetic outside Number's safe
    # integer range.
    large_value = JavaScriptBigInt(2**53 + 1)
    print(f"Exact large integer represented by BigInt: {large_value}")


def run_self_checks() -> None:
    """Run executable assertions covering the modeled behavior."""

    print("\n=== Self Checks ===")

    environment = JavaScriptEnvironment()
    environment.declare("mutable", BindingKind.LET, 1)
    environment.assign("mutable", 2)
    assert environment.get("mutable") == 2

    environment.declare("fixed", BindingKind.CONST, 1)
    try:
        environment.assign("fixed", 2)
    except TypeError:
        pass
    else:
        raise AssertionError("const reassignment should fail")

    symbol_factory = SymbolFactory()
    assert symbol_factory.create("x") != symbol_factory.create("x")

    big_a = JavaScriptBigInt(2**100)
    big_b = JavaScriptBigInt(3)
    assert (big_a * big_b).value == 3 * 2**100

    assert javascript_typeof("text") == "string"
    assert javascript_typeof(1.5) == "number"
    assert javascript_typeof(True) == "boolean"
    assert javascript_typeof(None) == "object"
    assert javascript_typeof(UNDEFINED) == "undefined"
    assert javascript_typeof(symbol_factory.create()) == "symbol"
    assert javascript_typeof(big_a) == "bigint"

    print("All self checks passed.")


def main() -> int:
    """Execute the complete demonstration in a controlled order."""

    print("JavaScript Variables and Data Types")
    print("Executable Python model of JavaScript semantics")

    demonstrate_var_let_const()
    demonstrate_strings()
    demonstrate_numbers()
    demonstrate_booleans()
    demonstrate_null_and_undefined()
    demonstrate_symbols()
    demonstrate_bigint()
    demonstrate_type_inspection()
    demonstrate_validation_pipeline()
    demonstrate_edge_cases()
    run_self_checks()

    print("\nDemonstration complete.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nExecution interrupted.", file=sys.stderr)
        raise SystemExit(130)
