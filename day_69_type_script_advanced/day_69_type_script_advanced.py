"""
TypeScript Advanced Concepts: Python Runtime and Static-Typing Equivalents

Concepts:
- Generic functions and classes
- Type variables and bounded generics
- Utility-type equivalents
- Type narrowing
- Type guards
- Conditional types through overloads and generics
- Protocols and structural typing
- Validation and serialization
- Error handling and tests

Run:
    python typescript_advanced.py
"""

from __future__ import annotations

from dataclasses import dataclass, asdict, replace
from typing import (
    Any,
    Callable,
    Generic,
    TypeVar,
    Protocol,
    TypeGuard,
    Optional,
    Union,
    Literal,
    TypedDict,
    overload,
)
from enum import Enum
import json
from pathlib import Path


# ============================================================
# 1. GENERICS AND TYPE VARIABLES
# ============================================================

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")
Number = TypeVar("Number", int, float)


def identity(value: T) -> T:
    """Return the same value while preserving its type."""
    return value


def first_item(items: list[T]) -> Optional[T]:
    if not items:
        return None
    return items[0]


def maximum(values: list[Number]) -> Number:
    if not values:
        raise ValueError("Cannot calculate maximum of an empty list")
    return max(values)


class Repository(Generic[T]):
    """A generic in-memory repository."""

    def __init__(self) -> None:
        self._records: dict[str, T] = {}

    def add(self, key: str, value: T) -> None:
        if not key.strip():
            raise ValueError("Repository key cannot be empty")
        if key in self._records:
            raise ValueError(f"Duplicate key: {key}")
        self._records[key] = value

    def get(self, key: str) -> Optional[T]:
        return self._records.get(key)

    def remove(self, key: str) -> bool:
        return self._records.pop(key, None) is not None

    def all(self) -> list[T]:
        return list(self._records.values())


# ============================================================
# 2. DOMAIN MODELS
# ============================================================

class AccountStatus(Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CLOSED = "closed"


@dataclass(frozen=True)
class User:
    user_id: int
    name: str
    email: str
    status: AccountStatus = AccountStatus.ACTIVE

    def __post_init__(self) -> None:
        if self.user_id <= 0:
            raise ValueError("User ID must be positive")
        if not self.name.strip():
            raise ValueError("Name cannot be empty")
        if "@" not in self.email:
            raise ValueError("Invalid email address")


@dataclass(frozen=True)
class Product:
    product_id: int
    name: str
    price: float

    def __post_init__(self) -> None:
        if self.product_id <= 0:
            raise ValueError("Product ID must be positive")
        if self.price < 0:
            raise ValueError("Price cannot be negative")


# ============================================================
# 3. UTILITY-TYPE EQUIVALENTS
# ============================================================

@dataclass
class UserProfile:
    user_id: int
    name: str
    email: str
    phone: Optional[str] = None
    department: Optional[str] = None


class UserPatch(TypedDict, total=False):
    """Partial<UserProfile>-style update structure."""
    name: str
    email: str
    phone: Optional[str]
    department: Optional[str]


def partial_update(
    profile: UserProfile,
    changes: UserPatch
) -> UserProfile:
    """Partial update with explicit field validation."""

    allowed = {"name", "email", "phone", "department"}

    unknown = set(changes) - allowed
    if unknown:
        raise ValueError(f"Unknown fields: {sorted(unknown)}")

    if "name" in changes and not changes["name"].strip():
        raise ValueError("Name cannot be empty")

    if "email" in changes and "@" not in changes["email"]:
        raise ValueError("Invalid email")

    return replace(profile, **changes)


def pick_fields(
    data: dict[str, Any],
    fields: set[str]
) -> dict[str, Any]:
    """Pick<T, K>-style operation."""
    return {key: data[key] for key in fields if key in data}


def omit_fields(
    data: dict[str, Any],
    fields: set[str]
) -> dict[str, Any]:
    """Omit<T, K>-style operation."""
    return {
        key: value
        for key, value in data.items()
        if key not in fields
    }


def readonly_snapshot(data: dict[str, Any]) -> tuple:
    """Readonly<T>-style immutable snapshot."""
    return tuple(sorted(data.items()))


def record_fields(
    data: list[T],
    key_function: Callable[[T], str]
) -> dict[str, T]:
    """Record<K, T>-style dictionary construction."""
    result: dict[str, T] = {}

    for item in data:
        key = key_function(item)
        if key in result:
            raise ValueError(f"Duplicate generated key: {key}")
        result[key] = item

    return result


# ============================================================
# 4. TYPE NARROWING
# ============================================================

def describe_value(value: Union[int, str, None]) -> str:
    """Narrow a union using runtime checks."""

    if value is None:
        return "No value supplied"

    if isinstance(value, bool):
        return "Boolean value"

    if isinstance(value, int):
        return f"Integer: {value}"

    if isinstance(value, str):
        return f"String: {value.strip()}"

    raise TypeError("Unsupported value")


@dataclass
class Success:
    data: dict[str, Any]


@dataclass
class Failure:
    error: str
    code: int


ApiResult = Union[Success, Failure]


def process_result(result: ApiResult) -> str:
    """Narrow a discriminated-union equivalent."""

    if isinstance(result, Success):
        return f"Success: {result.data}"

    if isinstance(result, Failure):
        return f"Failure {result.code}: {result.error}"

    raise TypeError("Unknown result type")


# ============================================================
# 5. CUSTOM TYPE GUARDS
# ============================================================

class UserPayload(TypedDict):
    user_id: int
    name: str
    email: str


def is_user_payload(value: Any) -> TypeGuard[UserPayload]:
    """Validate untrusted dictionary data."""

    if not isinstance(value, dict):
        return False

    if set(value) != {"user_id", "name", "email"}:
        return False

    return (
        isinstance(value["user_id"], int)
        and not isinstance(value["user_id"], bool)
        and value["user_id"] > 0
        and isinstance(value["name"], str)
        and bool(value["name"].strip())
        and isinstance(value["email"], str)
        and "@" in value["email"]
    )


def parse_user_payload(value: Any) -> User:
    if not is_user_payload(value):
        raise ValueError("Invalid user payload")

    return User(
        user_id=value["user_id"],
        name=value["name"],
        email=value["email"],
    )


# ============================================================
# 6. CONDITIONAL-TYPE EQUIVALENTS
# ============================================================

@overload
def normalize(value: str) -> str:
    ...


@overload
def normalize(value: int) -> int:
    ...


@overload
def normalize(value: None) -> None:
    ...


def normalize(value: str | int | None) -> str | int | None:
    """
    Overloads express input/output relationships.

    Python does not implement TypeScript conditional types
    directly; overloads provide static typing alternatives.
    """

    if isinstance(value, str):
        return value.strip().lower()

    if isinstance(value, int) and not isinstance(value, bool):
        return abs(value)

    return None


# ============================================================
# 7. STRUCTURAL TYPING AND PROTOCOLS
# ============================================================

class Serializable(Protocol):
    def to_dict(self) -> dict[str, Any]:
        ...


@dataclass
class Invoice:
    invoice_id: str
    amount: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "invoice_id": self.invoice_id,
            "amount": self.amount,
        }


def serialize(item: Serializable) -> str:
    return json.dumps(item.to_dict(), sort_keys=True)


# ============================================================
# 8. GENERIC PROCESSING PIPELINE
# ============================================================

class Pipeline(Generic[T]):
    def __init__(self, steps: list[Callable[[Any], Any]]) -> None:
        self.steps = steps

    def execute(self, initial: T) -> Any:
        result: Any = initial

        for step in self.steps:
            result = step(result)

        return result


def remove_whitespace(value: str) -> str:
    return value.strip()


def convert_to_uppercase(value: str) -> str:
    return value.upper()


# ============================================================
# 9. JSON VALIDATION AND SECURE FILE HANDLING
# ============================================================

def load_users(path: Path) -> list[User]:
    """Load JSON while validating every untrusted record."""

    if not path.is_file():
        raise FileNotFoundError(path)

    if path.stat().st_size > 1_000_000:
        raise ValueError("Input file exceeds 1 MB limit")

    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    if not isinstance(payload, list):
        raise ValueError("Expected a JSON array")

    return [parse_user_payload(item) for item in payload]


def save_users(path: Path, users: list[User]) -> None:
    """Write validated records as JSON."""

    payload = [
        {
            "user_id": user.user_id,
            "name": user.name,
            "email": user.email,
        }
        for user in users
    ]

    temporary = path.with_suffix(path.suffix + ".tmp")

    try:
        with temporary.open("w", encoding="utf-8") as file:
            json.dump(payload, file, indent=2)
            file.flush()

        temporary.replace(path)

    except OSError:
        temporary.unlink(missing_ok=True)
        raise


# ============================================================
# 10. EXECUTABLE TESTS
# ============================================================

def run_tests() -> None:
    assert identity(100) == 100
    assert identity("TypeScript") == "TypeScript"

    assert first_item([10, 20, 30]) == 10
    assert first_item([]) is None

    assert maximum([10, 20, 30]) == 30

    users: Repository[User] = Repository()
    user = User(1, "Aarav", "aarav@example.com")
    users.add("U001", user)

    assert users.get("U001") == user
    assert users.remove("U001")
    assert users.get("U001") is None

    profile = UserProfile(
        1,
        "Aarav",
        "aarav@example.com"
    )

    updated = partial_update(
        profile,
        {"department": "Engineering"}
    )

    assert updated.department == "Engineering"
    assert profile.department is None

    data = {
        "name": "Aarav",
        "email": "aarav@example.com",
        "password": "secret",
    }

    assert pick_fields(data, {"name"}) == {"name": "Aarav"}
    assert "password" not in omit_fields(data, {"password"})

    assert describe_value(25) == "Integer: 25"
    assert describe_value(None) == "No value supplied"

    assert process_result(
        Success({"status": "approved"})
    ).startswith("Success")

    assert process_result(
        Failure("Invalid input", 400)
    ).startswith("Failure")

    assert is_user_payload({
        "user_id": 2,
        "name": "Mira",
        "email": "mira@example.com",
    })

    assert not is_user_payload({
        "user_id": True,
        "name": "Mira",
        "email": "mira@example.com",
    })

    assert normalize(" TYPESCRIPT ") == "typescript"
    assert normalize(-10) == 10
    assert normalize(None) is None

    invoice = Invoice("INV-001", 2500.0)
    assert json.loads(serialize(invoice))["amount"] == 2500.0

    pipeline = Pipeline[str]([
        remove_whitespace,
        convert_to_uppercase,
    ])

    assert pipeline.execute(" typescript ") == "TYPESCRIPT"

    print("All Python tests passed.")


def main() -> None:
    print("TYPE SYSTEM ADVANCED CONCEPTS")
    print("=" * 55)

    run_tests()

    print("\nGeneric repository:")
    repository: Repository[Product] = Repository()

    repository.add(
        "P001",
        Product(1, "Security Platform", 4999.0)
    )

    for product in repository.all():
        print(product)

    print("\nUtility-type equivalents:")
    profile = UserProfile(
        101,
        "Mira",
        "mira@example.com"
    )

    print(partial_update(
        profile,
        {"department": "Security"}
    ))

    print("\nType narrowing:")
    print(describe_value("Advanced TypeScript"))
    print(describe_value(42))
    print(describe_value(None))

    print("\nConditional-type equivalent:")
    print(normalize(" GENERICS "))

    print("\nStructural typing:")
    print(serialize(Invoice("INV-002", 7500.0)))

    print("\nPipeline:")
    print(Pipeline[str]([
        remove_whitespace,
        convert_to_uppercase,
    ]).execute(" advanced typing "))


if __name__ == "__main__":
    main()
