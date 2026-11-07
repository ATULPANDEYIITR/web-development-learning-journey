from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Any,
    Callable,
    Generic,
    TypeAlias,
    TypeVar,
)


# ============================================================
# TYPESCRIPT CORE: PYTHON DOMAIN MODEL
# Arrays, Objects, Tuples, Enums, Unions, Intersections, Aliases
# ============================================================


# ------------------------------------------------------------
# 1. Type aliases
# ------------------------------------------------------------

UserId: TypeAlias = int
Email: TypeAlias = str
Score: TypeAlias = float
TagList: TypeAlias = list[str]
Coordinate: TypeAlias = tuple[float, float]


# ------------------------------------------------------------
# 2. Enums
# ------------------------------------------------------------

class UserRole(Enum):
    ADMIN = "admin"
    DEVELOPER = "developer"
    ANALYST = "analyst"
    VIEWER = "viewer"


class AccountStatus(Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING = "pending"


class ProjectStatus(Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


# ------------------------------------------------------------
# 3. Object-like structures using dataclasses
# ------------------------------------------------------------

@dataclass
class Profile:
    display_name: str
    email: Email
    location: str

    def validate(self) -> None:
        if not self.display_name.strip():
            raise ValueError("Display name cannot be empty")

        if "@" not in self.email:
            raise ValueError("Invalid email address")


@dataclass
class User:
    user_id: UserId
    profile: Profile
    role: UserRole
    status: AccountStatus
    tags: TagList = field(default_factory=list)

    def validate(self) -> None:
        if self.user_id <= 0:
            raise ValueError("User ID must be positive")

        self.profile.validate()

        if len(self.tags) != len(set(self.tags)):
            raise ValueError("Duplicate tags are not allowed")


# ------------------------------------------------------------
# 4. Tuples
# ------------------------------------------------------------

def calculate_coordinates(
    latitude: float,
    longitude: float
) -> Coordinate:
    if not -90 <= latitude <= 90:
        raise ValueError("Invalid latitude")

    if not -180 <= longitude <= 180:
        raise ValueError("Invalid longitude")

    return latitude, longitude


def process_user_summary(
    summary: tuple[UserId, str, UserRole]
) -> str:
    user_id, name, role = summary

    return f"User {user_id}: {name} ({role.value})"


# ------------------------------------------------------------
# 5. Union types
# ------------------------------------------------------------

# TypeScript equivalent:
# type Identifier = number | string

Identifier: TypeAlias = int | str


def normalize_identifier(value: Identifier) -> str:
    if isinstance(value, bool):
        raise TypeError("Boolean is not a valid identifier")

    if isinstance(value, int):
        if value <= 0:
            raise ValueError("Numeric identifier must be positive")

        return str(value)

    if isinstance(value, str):
        normalized = value.strip()

        if not normalized:
            raise ValueError("String identifier cannot be empty")

        return normalized

    raise TypeError("Unsupported identifier type")


# ------------------------------------------------------------
# 6. Discriminated unions
# ------------------------------------------------------------

@dataclass(frozen=True)
class SuccessResult:
    kind: str
    data: dict[str, Any]


@dataclass(frozen=True)
class ErrorResult:
    kind: str
    message: str
    code: int


ApiResult: TypeAlias = SuccessResult | ErrorResult


def handle_result(result: ApiResult) -> str:
    if isinstance(result, SuccessResult):
        return f"Success: {result.data}"

    if isinstance(result, ErrorResult):
        return f"Error {result.code}: {result.message}"

    raise TypeError("Unknown API result")


# ------------------------------------------------------------
# 7. Intersection types
# ------------------------------------------------------------

@dataclass
class Auditable:
    created_by: UserId
    created_at: str


@dataclass
class Permissions:
    can_read: bool
    can_write: bool
    can_delete: bool


@dataclass
class ManagedResource:
    resource_id: int
    name: str
    audit: Auditable
    permissions: Permissions

    def validate(self) -> None:
        if self.resource_id <= 0:
            raise ValueError("Resource ID must be positive")

        if not self.name.strip():
            raise ValueError("Resource name is required")


# ManagedResource combines the properties of Auditable
# and Permissions, similar to a TypeScript intersection:
# type ManagedResource = Resource & Auditable & Permissions


# ------------------------------------------------------------
# 8. Arrays and collection operations
# ------------------------------------------------------------

def process_scores(scores: list[Score]) -> dict[str, Any]:
    if not scores:
        raise ValueError("At least one score is required")

    if any(not isinstance(score, (int, float)) for score in scores):
        raise TypeError("Scores must be numeric")

    if any(not 0 <= score <= 100 for score in scores):
        raise ValueError("Scores must be between 0 and 100")

    return {
        "original": scores.copy(),
        "sorted": sorted(scores),
        "highest": max(scores),
        "lowest": min(scores),
        "average": sum(scores) / len(scores),
        "passed": [score for score in scores if score >= 50],
        "unique": sorted(set(scores)),
    }


# ------------------------------------------------------------
# 9. Generic types
# ------------------------------------------------------------

T = TypeVar("T")


@dataclass
class ApiResponse(Generic[T]):
    success: bool
    payload: T | None
    error: str | None = None

    def validate(self) -> None:
        if self.success and self.error is not None:
            raise ValueError("Successful response cannot contain an error")

        if not self.success and not self.error:
            raise ValueError("Failed response must contain an error")


def first_item(items: list[T]) -> T | None:
    return items[0] if items else None


# ------------------------------------------------------------
# 10. Generic repository
# ------------------------------------------------------------

class Repository(Generic[T]):
    def __init__(self) -> None:
        self._records: dict[int, T] = {}

    def add(self, record_id: int, record: T) -> None:
        if record_id <= 0:
            raise ValueError("Record ID must be positive")

        if record_id in self._records:
            raise ValueError("Record already exists")

        self._records[record_id] = record

    def get(self, record_id: int) -> T | None:
        return self._records.get(record_id)

    def remove(self, record_id: int) -> bool:
        return self._records.pop(record_id, None) is not None

    def all(self) -> list[T]:
        return list(self._records.values())

    def count(self) -> int:
        return len(self._records)


# ------------------------------------------------------------
# 11. Object transformation
# ------------------------------------------------------------

def update_user(
    user: User,
    **changes: Any
) -> User:
    allowed_fields = {"role", "status", "tags"}

    invalid_fields = set(changes) - allowed_fields

    if invalid_fields:
        raise ValueError(f"Unsupported fields: {invalid_fields}")

    updated = User(
        user_id=user.user_id,
        profile=user.profile,
        role=changes.get("role", user.role),
        status=changes.get("status", user.status),
        tags=changes.get("tags", user.tags.copy()),
    )

    updated.validate()
    return updated


# ------------------------------------------------------------
# 12. Main application workflow
# ------------------------------------------------------------

def main() -> None:
    print("\n=== TYPESCRIPT CORE CONCEPTS ===")

    # Arrays
    scores = [85.5, 92.0, 67.5, 48.0, 92.0]
    print("\nARRAYS")
    print(process_scores(scores))

    # Objects
    profile = Profile(
        display_name="Atul Pandey",
        email="atul@example.com",
        location="Lucknow"
    )

    user = User(
        user_id=101,
        profile=profile,
        role=UserRole.ADMIN,
        status=AccountStatus.ACTIVE,
        tags=["python", "typescript", "backend"]
    )

    user.validate()

    print("\nOBJECT")
    print(user)

    # Tuples
    coordinates = calculate_coordinates(26.8467, 80.9462)

    summary = (user.user_id, user.profile.display_name, user.role)

    print("\nTUPLES")
    print("Coordinates:", coordinates)
    print(process_user_summary(summary))

    # Enums
    print("\nENUMS")
    print("Role:", user.role.value)
    print("Status:", user.status.value)

    # Union
    print("\nUNION TYPES")
    print(normalize_identifier(101))
    print(normalize_identifier("USER-101"))

    # Discriminated union
    print("\nDISCRIMINATED UNIONS")

    results: list[ApiResult] = [
        SuccessResult("success", {"user_id": 101}),
        ErrorResult("error", "Permission denied", 403)
    ]

    for result in results:
        print(handle_result(result))

    # Intersection
    print("\nINTERSECTION TYPES")

    resource = ManagedResource(
        resource_id=501,
        name="Project Repository",
        audit=Auditable(101, "2026-11-07T08:00:00"),
        permissions=Permissions(True, True, False)
    )

    resource.validate()
    print(resource)

    # Generics
    print("\nGENERIC TYPES")

    response: ApiResponse[User] = ApiResponse(
        success=True,
        payload=user
    )

    response.validate()

    print("Response success:", response.success)
    print("First score:", first_item(scores))

    # Generic repository
    print("\nGENERIC REPOSITORY")

    repository: Repository[User] = Repository()
    repository.add(user.user_id, user)

    print("Stored users:", repository.count())
    print("Retrieved:", repository.get(101))

    # Object transformation
    print("\nOBJECT TRANSFORMATION")

    updated_user = update_user(
        user,
        role=UserRole.DEVELOPER,
        tags=["typescript", "python"]
    )

    print("Original role:", user.role.value)
    print("Updated role:", updated_user.role.value)

    # Edge cases
    print("\nVALIDATION TESTS")

    invalid_operations: list[Callable[[], Any]] = [
        lambda: normalize_identifier(0),
        lambda: calculate_coordinates(100, 80),
        lambda: process_scores([]),
        lambda: repository.add(101, user),
    ]

    for operation in invalid_operations:
        try:
            operation()
        except (ValueError, TypeError) as error:
            print("Expected validation error:", error)

    print("\nExecution completed successfully.")


if __name__ == "__main__":
    main()
