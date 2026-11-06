"""
TypeScript Introduction
Why TypeScript, Type Annotations, Primitive Types, and Type Inference

This executable Python program models a typed user-registration and
configuration workflow to demonstrate concepts that TypeScript enforces
during development but JavaScript does not enforce through static types.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, TypeAlias
import json
import logging
import re
from pathlib import Path


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

logger = logging.getLogger(__name__)

JsonPrimitive: TypeAlias = str | int | float | bool | None


class ValidationError(ValueError):
    """Raised when a value violates a domain validation rule."""


class AccountStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


@dataclass(frozen=True)
class TypeDescriptor:
    """Represents a simplified programming-language type."""

    name: str
    python_type: type

    def validate(self, value: Any) -> bool:
        # bool is a subclass of int in Python, so exact checks matter.
        if self.python_type is int:
            return type(value) is int

        if self.python_type is float:
            return type(value) in (int, float)

        return type(value) is self.python_type


PRIMITIVE_TYPES = {
    "string": TypeDescriptor("string", str),
    "number": TypeDescriptor("number", float),
    "boolean": TypeDescriptor("boolean", bool),
    "integer": TypeDescriptor("integer", int),
}


def validate_primitive(
    value: Any,
    expected_type: str,
    allow_null: bool = False
) -> bool:
    """Validate a primitive value against a declared type."""

    if value is None:
        return allow_null

    descriptor = PRIMITIVE_TYPES.get(expected_type)

    if descriptor is None:
        raise ValidationError(
            f"Unsupported primitive type: {expected_type}"
        )

    return descriptor.validate(value)


def infer_type(value: Any) -> str:
    """Demonstrate runtime type inference."""

    if value is None:
        return "null"

    if type(value) is bool:
        return "boolean"

    if type(value) is int:
        return "integer"

    if type(value) is float:
        return "number"

    if isinstance(value, str):
        return "string"

    if isinstance(value, list):
        return "array"

    if isinstance(value, dict):
        return "object"

    return type(value).__name__


@dataclass
class User:
    user_id: int
    name: str
    email: str
    age: int
    active: bool = True
    status: AccountStatus = AccountStatus.ACTIVE
    metadata: dict[str, JsonPrimitive] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if type(self.user_id) is not int or self.user_id <= 0:
            raise ValidationError("User ID must be a positive integer.")

        if not isinstance(self.name, str) or not self.name.strip():
            raise ValidationError("Name cannot be empty.")

        if not isinstance(self.email, str):
            raise ValidationError("Email must be a string.")

        if not re.fullmatch(
            r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
            self.email
        ):
            raise ValidationError("Invalid email address.")

        if type(self.age) is not int or not 18 <= self.age <= 120:
            raise ValidationError("Age must be between 18 and 120.")

        if type(self.active) is not bool:
            raise ValidationError("Active must be a boolean.")

        if not isinstance(self.status, AccountStatus):
            raise ValidationError("Invalid account status.")

        if not isinstance(self.metadata, dict):
            raise ValidationError("Metadata must be a dictionary.")

        for key, value in self.metadata.items():
            if not isinstance(key, str):
                raise ValidationError("Metadata keys must be strings.")

            if value is not None and type(value) not in (
                str, int, float, bool
            ):
                raise ValidationError(
                    f"Invalid metadata value for key: {key}"
                )

            if type(value) is float:
                import math
                if not math.isfinite(value):
                    raise ValidationError(
                        f"Metadata number must be finite: {key}"
                    )

        self.name = self.name.strip()
        self.email = self.email.lower().strip()


class UserRegistry:
    """Maintains users with indexed lookup and duplicate protection."""

    def __init__(self) -> None:
        self._users: dict[int, User] = {}
        self._email_index: dict[str, int] = {}

    def register(self, user: User) -> None:
        if user.user_id in self._users:
            raise ValidationError("User ID already exists.")

        if user.email in self._email_index:
            raise ValidationError("Email already registered.")

        self._users[user.user_id] = user
        self._email_index[user.email] = user.user_id

        logger.info("Registered user %s", user.user_id)

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self._users.get(user_id)

    def get_by_email(self, email: str) -> Optional[User]:
        user_id = self._email_index.get(email.lower().strip())

        if user_id is None:
            return None

        return self._users[user_id]

    def deactivate(self, user_id: int) -> None:
        user = self.get_by_id(user_id)

        if user is None:
            raise ValidationError("User does not exist.")

        user.active = False
        user.status = AccountStatus.INACTIVE

    def active_users(self) -> list[User]:
        return [
            user
            for user in self._users.values()
            if user.active
        ]

    def export_json(self, file_path: str) -> None:
        """Export records without exposing internal registry structures."""

        data = [
            {
                "user_id": user.user_id,
                "name": user.name,
                "email": user.email,
                "age": user.age,
                "active": user.active,
                "status": user.status.value,
                "metadata": user.metadata,
            }
            for user in self._users.values()
        ]

        path = Path(file_path)
        path.write_text(
            json.dumps(data, indent=2, allow_nan=False),
            encoding="utf-8"
        )


def demonstrate_annotations() -> None:
    """Show explicit declarations and inferred runtime types."""

    username: str = "Atul"
    age: int = 29
    score: float = 94.5
    is_verified: bool = True
    optional_name: Optional[str] = None

    print("\nTYPE ANNOTATIONS")

    examples = {
        "username": username,
        "age": age,
        "score": score,
        "is_verified": is_verified,
        "optional_name": optional_name,
    }

    for variable, value in examples.items():
        print(
            f"{variable}: inferred runtime type = "
            f"{infer_type(value)}"
        )

    print("\nPRIMITIVE VALIDATION")

    test_cases = [
        ("Atul", "string"),
        (25, "integer"),
        (25.5, "number"),
        (True, "boolean"),
        (None, "string"),
    ]

    for value, expected in test_cases:
        result = validate_primitive(
            value,
            expected,
            allow_null=True
        )

        print(
            f"Value={value!r}, Expected={expected}, "
            f"Valid={result}"
        )


def demonstrate_user_workflow() -> None:
    registry = UserRegistry()

    users = [
        User(
            user_id=1,
            name="Atul Pandey",
            email="ATUL@example.com",
            age=29,
            metadata={
                "department": "Engineering",
                "experience": 5,
                "verified": True,
            },
        ),
        User(
            user_id=2,
            name="Riya Sharma",
            email="riya@example.com",
            age=31,
            metadata={
                "department": "Research",
                "experience": 7,
                "verified": False,
            },
        ),
    ]

    for user in users:
        registry.register(user)

    print("\nUSER REGISTRY")

    for user in registry.active_users():
        print(
            f"{user.user_id}: {user.name}, "
            f"{user.email}, {user.status.value}"
        )

    print("\nEMAIL LOOKUP")

    result = registry.get_by_email("atul@example.com")
    print(result)

    registry.deactivate(2)

    print("\nACTIVE USER COUNT")
    print(len(registry.active_users()))

    try:
        duplicate = User(
            user_id=3,
            name="Another User",
            email="atul@example.com",
            age=25,
        )
        registry.register(duplicate)

    except ValidationError as error:
        logger.warning("Registration rejected: %s", error)

    try:
        User(
            user_id=4,
            name="Invalid User",
            email="invalid-email",
            age=25,
        )

    except ValidationError as error:
        logger.warning("Invalid record rejected: %s", error)


def demonstrate_type_safety() -> None:
    print("\nTYPE SAFETY TESTS")

    assert validate_primitive("hello", "string")
    assert validate_primitive(42, "integer")
    assert validate_primitive(42.5, "number")
    assert validate_primitive(True, "boolean")

    # Python considers bool an integer subclass.
    # Exact validation prevents True from passing as an integer.
    assert not validate_primitive(True, "integer")
    assert not validate_primitive("42", "integer")
    assert not validate_primitive(42, "boolean")

    print("All primitive validation tests passed.")


def main() -> None:
    demonstrate_annotations()
    demonstrate_user_workflow()
    demonstrate_type_safety()

    print("\nEXECUTION COMPLETED")


if __name__ == "__main__":
    main()
