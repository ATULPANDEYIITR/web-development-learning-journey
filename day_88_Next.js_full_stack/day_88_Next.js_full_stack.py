#!/usr/bin/env python3
"""
Next.js Full-Stack Architecture Simulator
Topics:
- Route handlers
- Server actions
- Middleware
- Environment variables
- Request lifecycle
- Authentication and authorization
- Validation and error handling
- Server-side data access
- Security and configuration management

Requires: Python 3.10+
Uses only the Python standard library.
"""

from __future__ import annotations

import json
import logging
import os
import re
import secrets
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional
from urllib.parse import urlparse, parse_qs


# ---------------------------------------------------------
# Logging
# ---------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

logger = logging.getLogger("nextjs_simulator")


# ---------------------------------------------------------
# Environment Configuration
# ---------------------------------------------------------

class ConfigurationError(Exception):
    pass


class Environment:
    """Validates and manages application environment variables."""

    REQUIRED = {
        "DATABASE_URL",
        "SESSION_SECRET",
        "APP_ENV"
    }

    SECRET_NAMES = {
        "DATABASE_URL",
        "SESSION_SECRET",
        "API_SECRET"
    }

    def __init__(self, values: Optional[dict[str, str]] = None):
        self.values = dict(os.environ if values is None else values)

    def validate(self) -> None:
        missing = self.REQUIRED - self.values.keys()

        if missing:
            raise ConfigurationError(
                f"Missing required environment variables: "
                f"{', '.join(sorted(missing))}"
            )

        if len(self.values["SESSION_SECRET"]) < 32:
            raise ConfigurationError(
                "SESSION_SECRET must contain at least 32 characters"
            )

        if self.values["APP_ENV"] not in {
            "development", "production", "test"
        }:
            raise ConfigurationError("Invalid APP_ENV")

        database_url = self.values["DATABASE_URL"]

        if not database_url.startswith(("postgresql://", "postgres://")):
            raise ConfigurationError("DATABASE_URL must use PostgreSQL")

    def get(self, name: str, default: Optional[str] = None) -> Optional[str]:
        return self.values.get(name, default)

    def public_values(self) -> dict[str, str]:
        """Expose only explicitly public configuration."""
        return {
            key: value
            for key, value in self.values.items()
            if key.startswith("NEXT_PUBLIC_")
        }

    def safe_report(self) -> dict[str, str]:
        return {
            key: (
                "[REDACTED]"
                if key in self.SECRET_NAMES
                else value
            )
            for key, value in self.values.items()
        }


# ---------------------------------------------------------
# Domain Models
# ---------------------------------------------------------

class HTTPMethod(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


class UserRole(Enum):
    USER = "user"
    ADMIN = "admin"


@dataclass(frozen=True)
class User:
    user_id: int
    username: str
    role: UserRole
    active: bool = True


@dataclass
class Request:
    method: HTTPMethod
    path: str
    headers: dict[str, str] = field(default_factory=dict)
    body: dict[str, Any] = field(default_factory=dict)
    user: Optional[User] = None
    request_id: str = field(
        default_factory=lambda: secrets.token_hex(8)
    )


@dataclass
class Response:
    status: int
    body: dict[str, Any]
    headers: dict[str, str] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(self.body, default=str, indent=2)


# ---------------------------------------------------------
# Application Database
# ---------------------------------------------------------

class InMemoryDatabase:
    """Simulates server-only database operations."""

    def __init__(self):
        self.users: dict[int, User] = {}
        self.tasks: dict[int, dict[str, Any]] = {}
        self.next_task_id = 1

    def add_user(self, user: User) -> None:
        if user.user_id in self.users:
            raise ValueError("User already exists")

        self.users[user.user_id] = user

    def create_task(self, user_id: int, title: str) -> dict[str, Any]:
        if user_id not in self.users:
            raise ValueError("User does not exist")

        task = {
            "id": self.next_task_id,
            "user_id": user_id,
            "title": title,
            "completed": False,
            "created_at": time.time()
        }

        self.tasks[self.next_task_id] = task
        self.next_task_id += 1

        return task.copy()

    def get_tasks(self, user_id: int) -> list[dict[str, Any]]:
        return [
            task.copy()
            for task in self.tasks.values()
            if task["user_id"] == user_id
        ]

    def update_task(
        self,
        task_id: int,
        user_id: int,
        completed: bool
    ) -> dict[str, Any]:
        task = self.tasks.get(task_id)

        if task is None:
            raise KeyError("Task not found")

        if task["user_id"] != user_id:
            raise PermissionError("Task ownership violation")

        task["completed"] = completed
        return task.copy()


# ---------------------------------------------------------
# Middleware
# ---------------------------------------------------------

class Middleware:
    """Processes requests before route handlers."""

    def __init__(self, protected_prefixes: Optional[list[str]] = None):
        self.protected_prefixes = protected_prefixes or ["/dashboard", "/api/tasks"]

    def process(self, request: Request) -> Optional[Response]:
        request.headers.setdefault("X-Request-ID", request.request_id)

        # Reject suspicious path traversal.
        if "\x00" in request.path or ".." in request.path.split("/"):
            return Response(400, {"error": "Invalid request path"})

        # Protect application routes.
        protected = any(
            request.path == prefix
            or request.path.startswith(prefix + "/")
            for prefix in self.protected_prefixes
        )

        if protected and request.user is None:
            return Response(
                401,
                {"error": "Authentication required"}
            )

        if request.user is not None and not request.user.active:
            return Response(
                403,
                {"error": "Inactive account"}
            )

        return None


# ---------------------------------------------------------
# Input Validation
# ---------------------------------------------------------

class ValidationError(Exception):
    pass


def validate_task_title(value: Any) -> str:
    if not isinstance(value, str):
        raise ValidationError("Title must be a string")

    title = value.strip()

    if not title:
        raise ValidationError("Title cannot be empty")

    if len(title) > 120:
        raise ValidationError("Title cannot exceed 120 characters")

    if any(ord(char) < 32 and char not in "\t" for char in title):
        raise ValidationError("Title contains invalid control characters")

    return title


def validate_boolean(value: Any) -> bool:
    if type(value) is not bool:
        raise ValidationError("Value must be a boolean")

    return value


# ---------------------------------------------------------
# Route Handlers
# ---------------------------------------------------------

class RouteHandlers:
    """
    Simulates Next.js App Router route handlers.

    Corresponding Next.js structure:

    app/api/tasks/route.ts
    app/api/tasks/[id]/route.ts

    Supported HTTP methods:
    GET, POST, PATCH, DELETE
    """

    def __init__(self, database: InMemoryDatabase):
        self.database = database

    def handle(self, request: Request) -> Response:
        try:
            if request.path == "/api/tasks":
                return self.collection(request)

            match = re.fullmatch(r"/api/tasks/([1-9][0-9]*)", request.path)

            if match:
                return self.single_task(request, int(match.group(1)))

            return Response(404, {"error": "Route not found"})

        except ValidationError as exc:
            return Response(400, {"error": str(exc)})

        except PermissionError:
            return Response(403, {"error": "Forbidden"})

        except KeyError:
            return Response(404, {"error": "Task not found"})

        except Exception:
            logger.exception("Unhandled route handler failure")
            return Response(500, {"error": "Internal server error"})

    def collection(self, request: Request) -> Response:
        if request.user is None:
            return Response(401, {"error": "Authentication required"})

        if request.method == HTTPMethod.GET:
            return Response(
                200,
                {"tasks": self.database.get_tasks(request.user.user_id)}
            )

        if request.method == HTTPMethod.POST:
            title = validate_task_title(request.body.get("title"))

            task = self.database.create_task(
                request.user.user_id,
                title
            )

            return Response(201, {"task": task})

        return Response(405, {"error": "Method not allowed"})

    def single_task(
        self,
        request: Request,
        task_id: int
    ) -> Response:
        if request.user is None:
            return Response(401, {"error": "Authentication required"})

        if request.method == HTTPMethod.PATCH:
            completed = validate_boolean(
                request.body.get("completed")
            )

            task = self.database.update_task(
                task_id,
                request.user.user_id,
                completed
            )

            return Response(200, {"task": task})

        if request.method == HTTPMethod.DELETE:
            task = self.database.tasks.get(task_id)

            if task is None:
                return Response(404, {"error": "Task not found"})

            if task["user_id"] != request.user.user_id:
                return Response(403, {"error": "Forbidden"})

            del self.database.tasks[task_id]

            return Response(200, {"deleted": True})

        return Response(405, {"error": "Method not allowed"})


# ---------------------------------------------------------
# Server Actions
# ---------------------------------------------------------

class ServerActions:
    """
    Models Next.js server actions.

    Server actions are server-side functions invoked through
    framework-managed action requests. They are not ordinary
    public HTTP endpoints.
    """

    def __init__(self, database: InMemoryDatabase):
        self.database = database

    def create_task(
        self,
        user: Optional[User],
        form_data: dict[str, Any]
    ) -> dict[str, Any]:

        if user is None or not user.active:
            raise PermissionError("Authentication required")

        title = validate_task_title(form_data.get("title"))

        task = self.database.create_task(user.user_id, title)

        return {
            "success": True,
            "message": "Task created",
            "task": task,
            "revalidate_path": "/dashboard"
        }

    def complete_task(
        self,
        user: Optional[User],
        task_id: int
    ) -> dict[str, Any]:

        if user is None or not user.active:
            raise PermissionError("Authentication required")

        task = self.database.update_task(
            task_id,
            user.user_id,
            True
        )

        return {
            "success": True,
            "task": task,
            "revalidate_path": "/dashboard"
        }


# ---------------------------------------------------------
# Request Pipeline
# ---------------------------------------------------------

class Application:
    def __init__(
        self,
        environment: Environment,
        database: InMemoryDatabase
    ):
        environment.validate()

        self.environment = environment
        self.database = database
        self.middleware = Middleware()
        self.routes = RouteHandlers(database)
        self.actions = ServerActions(database)

    def handle_request(self, request: Request) -> Response:
        started = time.perf_counter()

        try:
            middleware_response = self.middleware.process(request)

            if middleware_response:
                return middleware_response

            return self.routes.handle(request)

        finally:
            duration = (time.perf_counter() - started) * 1000

            logger.info(
                "request_id=%s method=%s path=%s duration_ms=%.2f",
                request.request_id,
                request.method.value,
                request.path,
                duration
            )


# ---------------------------------------------------------
# Demonstration and Tests
# ---------------------------------------------------------

def run_demo() -> None:
    environment = Environment({
        "DATABASE_URL": "postgresql://app:password@localhost:5432/tasks",
        "SESSION_SECRET": secrets.token_urlsafe(48),
        "APP_ENV": "development",
        "NEXT_PUBLIC_APP_NAME": "Task Manager"
    })

    database = InMemoryDatabase()

    alice = User(1, "alice", UserRole.USER)
    admin = User(2, "admin", UserRole.ADMIN)

    database.add_user(alice)
    database.add_user(admin)

    application = Application(environment, database)

    # Unauthenticated request.
    unauthenticated = application.handle_request(
        Request(
            HTTPMethod.GET,
            "/api/tasks"
        )
    )

    assert unauthenticated.status == 401

    # Middleware protects dashboard routes.
    dashboard_response = application.handle_request(
        Request(
            HTTPMethod.GET,
            "/dashboard"
        )
    )

    assert dashboard_response.status == 401

    # Create a task through a route handler.
    created = application.handle_request(
        Request(
            HTTPMethod.POST,
            "/api/tasks",
            user=alice,
            body={"title": "Implement Next.js route handlers"}
        )
    )

    assert created.status == 201

    task_id = created.body["task"]["id"]

    # Retrieve tasks.
    retrieved = application.handle_request(
        Request(
            HTTPMethod.GET,
            "/api/tasks",
            user=alice
        )
    )

    assert retrieved.status == 200
    assert len(retrieved.body["tasks"]) == 1

    # Update a task through a route handler.
    updated = application.handle_request(
        Request(
            HTTPMethod.PATCH,
            f"/api/tasks/{task_id}",
            user=alice,
            body={"completed": True}
        )
    )

    assert updated.status == 200

    # Server action.
    action_result = application.actions.create_task(
        alice,
        {"title": "Implement server actions"}
    )

    assert action_result["success"] is True

    # Server action authorization.
    try:
        application.actions.create_task(
            None,
            {"title": "Unauthorized task"}
        )
    except PermissionError:
        logger.info("Unauthorized server action rejected")

    # Ownership enforcement.
    try:
        database.update_task(task_id, admin.user_id, False)
        raise AssertionError("Ownership enforcement failed")
    except PermissionError:
        logger.info("Cross-user modification rejected")

    # Invalid input.
    invalid = application.handle_request(
        Request(
            HTTPMethod.POST,
            "/api/tasks",
            user=alice,
            body={"title": ""}
        )
    )

    assert invalid.status == 400

    # Invalid route.
    missing = application.handle_request(
        Request(
            HTTPMethod.GET,
            "/api/unknown",
            user=alice
        )
    )

    assert missing.status == 404

    print("\nNEXT.JS FULL-STACK SIMULATION")
    print("=" * 45)

    print("\nPublic environment configuration:")
    print(environment.public_values())

    print("\nProtected environment configuration:")
    print(environment.safe_report())

    print("\nTask retrieval:")
    print(retrieved.to_json())

    print("\nServer action:")
    print(json.dumps(action_result, indent=2, default=str))

    print("\nHTTP status results:")
    print({
        "unauthenticated": unauthenticated.status,
        "dashboard": dashboard_response.status,
        "created": created.status,
        "updated": updated.status,
        "invalid_input": invalid.status,
        "missing_route": missing.status
    })

    print("\nAll assertions passed.")


if __name__ == "__main__":
    run_demo()
