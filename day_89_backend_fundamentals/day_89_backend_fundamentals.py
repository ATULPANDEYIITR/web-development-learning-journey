#!/usr/bin/env python3
"""
Backend Fundamentals
REST API, routing, controllers, services, middleware, validation,
HTTP status codes, error handling, and layered architecture.

Run:
    python backend_fundamentals.py

API:
    GET    /health
    GET    /api/v1/tasks
    GET    /api/v1/tasks/{id}
    POST   /api/v1/tasks
    PATCH  /api/v1/tasks/{id}
    DELETE /api/v1/tasks/{id}
"""

from __future__ import annotations

import json
import logging
import re
import threading
import time
import uuid

from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from enum import Enum
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable
from urllib.parse import urlparse, parse_qs


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

HOST = "127.0.0.1"
PORT = 8000
MAX_BODY_SIZE = 16_384

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

logger = logging.getLogger("backend")


# ---------------------------------------------------------
# Domain models
# ---------------------------------------------------------

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


@dataclass
class Task:
    id: int
    title: str
    description: str
    status: TaskStatus
    created_at: str
    updated_at: str


@dataclass
class APIResponse:
    status_code: int
    body: dict[str, Any]


@dataclass
class RequestContext:
    method: str
    path: str
    query: dict[str, list[str]]
    headers: dict[str, str]
    body: dict[str, Any] = field(default_factory=dict)
    request_id: str = ""
    params: dict[str, str] = field(default_factory=dict)


# ---------------------------------------------------------
# Application exceptions
# ---------------------------------------------------------

class BackendError(Exception):
    status_code = 500
    error_code = "INTERNAL_ERROR"

    def __init__(self, message: str):
        super().__init__(message)


class NotFoundError(BackendError):
    status_code = 404
    error_code = "NOT_FOUND"


class ValidationError(BackendError):
    status_code = 400
    error_code = "VALIDATION_ERROR"


class ConflictError(BackendError):
    status_code = 409
    error_code = "CONFLICT"


class PayloadTooLargeError(BackendError):
    status_code = 413
    error_code = "PAYLOAD_TOO_LARGE"


# ---------------------------------------------------------
# Repository layer
# ---------------------------------------------------------

class TaskRepository:
    """
    Repository owns data access.

    A lock protects shared in-memory state when multiple
    HTTP request threads execute concurrently.
    """

    def __init__(self):
        self._tasks: dict[int, Task] = {}
        self._next_id = 1
        self._lock = threading.RLock()

    def create(
        self,
        title: str,
        description: str
    ) -> Task:

        with self._lock:
            now = datetime.now(timezone.utc).isoformat()

            task = Task(
                id=self._next_id,
                title=title,
                description=description,
                status=TaskStatus.PENDING,
                created_at=now,
                updated_at=now
            )

            self._tasks[task.id] = task
            self._next_id += 1

            return task

    def find_all(self) -> list[Task]:
        with self._lock:
            return list(self._tasks.values())

    def find_by_id(self, task_id: int) -> Task:
        with self._lock:
            task = self._tasks.get(task_id)

            if task is None:
                raise NotFoundError(
                    f"Task {task_id} does not exist"
                )

            return task

    def update(
        self,
        task_id: int,
        changes: dict[str, Any]
    ) -> Task:

        with self._lock:
            task = self.find_by_id(task_id)

            if "title" in changes:
                task.title = changes["title"]

            if "description" in changes:
                task.description = changes["description"]

            if "status" in changes:
                task.status = TaskStatus(changes["status"])

            task.updated_at = datetime.now(
                timezone.utc
            ).isoformat()

            return task

    def delete(self, task_id: int) -> None:
        with self._lock:
            if task_id not in self._tasks:
                raise NotFoundError(
                    f"Task {task_id} does not exist"
                )

            del self._tasks[task_id]


# ---------------------------------------------------------
# Validation layer
# ---------------------------------------------------------

class TaskValidator:

    ALLOWED_CREATE_FIELDS = {
        "title",
        "description"
    }

    ALLOWED_UPDATE_FIELDS = {
        "title",
        "description",
        "status"
    }

    @staticmethod
    def validate_title(value: Any) -> str:
        if not isinstance(value, str):
            raise ValidationError(
                "Title must be a string"
            )

        value = value.strip()

        if not value:
            raise ValidationError(
                "Title cannot be empty"
            )

        if len(value) > 150:
            raise ValidationError(
                "Title cannot exceed 150 characters"
            )

        return value

    @staticmethod
    def validate_description(value: Any) -> str:
        if not isinstance(value, str):
            raise ValidationError(
                "Description must be a string"
            )

        if len(value) > 2000:
            raise ValidationError(
                "Description cannot exceed 2000 characters"
            )

        return value.strip()

    @classmethod
    def validate_create(
        cls,
        data: dict[str, Any]
    ) -> dict[str, str]:

        if not isinstance(data, dict):
            raise ValidationError(
                "Request body must be a JSON object"
            )

        unknown = set(data) - cls.ALLOWED_CREATE_FIELDS

        if unknown:
            raise ValidationError(
                f"Unknown fields: {sorted(unknown)}"
            )

        if "title" not in data:
            raise ValidationError(
                "Title is required"
            )

        return {
            "title": cls.validate_title(data["title"]),
            "description": cls.validate_description(
                data.get("description", "")
            )
        }

    @classmethod
    def validate_update(
        cls,
        data: dict[str, Any]
    ) -> dict[str, Any]:

        if not isinstance(data, dict) or not data:
            raise ValidationError(
                "At least one update field is required"
            )

        unknown = set(data) - cls.ALLOWED_UPDATE_FIELDS

        if unknown:
            raise ValidationError(
                f"Unknown fields: {sorted(unknown)}"
            )

        result = {}

        if "title" in data:
            result["title"] = cls.validate_title(
                data["title"]
            )

        if "description" in data:
            result["description"] = (
                cls.validate_description(data["description"])
            )

        if "status" in data:
            try:
                result["status"] = TaskStatus(
                    data["status"]
                )
            except (ValueError, TypeError):
                raise ValidationError(
                    "Invalid task status"
                )

        return result


# ---------------------------------------------------------
# Service layer
# ---------------------------------------------------------

class TaskService:
    """
    Business rules belong in services, not HTTP controllers.
    """

    def __init__(self, repository: TaskRepository):
        self.repository = repository

    def create_task(self, data: dict[str, Any]) -> Task:
        validated = TaskValidator.validate_create(data)

        return self.repository.create(**validated)

    def list_tasks(self) -> list[Task]:
        return self.repository.find_all()

    def get_task(self, task_id: int) -> Task:
        return self.repository.find_by_id(task_id)

    def update_task(
        self,
        task_id: int,
        data: dict[str, Any]
    ) -> Task:

        validated = TaskValidator.validate_update(data)

        return self.repository.update(
            task_id,
            validated
        )

    def delete_task(self, task_id: int) -> None:
        self.repository.delete(task_id)


# ---------------------------------------------------------
# Middleware
# ---------------------------------------------------------

Middleware = Callable[
    [RequestContext, Callable],
    APIResponse
]


def request_id_middleware(
    request: RequestContext,
    next_handler: Callable
) -> APIResponse:

    request.request_id = str(uuid.uuid4())

    response = next_handler(request)

    response.body["request_id"] = request.request_id

    return response


def logging_middleware(
    request: RequestContext,
    next_handler: Callable
) -> APIResponse:

    started = time.perf_counter()

    try:
        response = next_handler(request)

        duration = (
            time.perf_counter() - started
        ) * 1000

        logger.info(
            "%s %s %s %.2fms",
            request.method,
            request.path,
            response.status_code,
            duration
        )

        return response

    except Exception:
        logger.exception(
            "Unhandled request failure: %s %s",
            request.method,
            request.path
        )
        raise


# ---------------------------------------------------------
# Router
# ---------------------------------------------------------

@dataclass
class Route:
    method: str
    pattern: re.Pattern
    parameter_names: list[str]
    handler: Callable


class Router:

    def __init__(self):
        self.routes: list[Route] = []

    def add(
        self,
        method: str,
        path: str,
        handler: Callable
    ) -> None:

        names = re.findall(r"\{(\w+)\}", path)

        regex = re.sub(
            r"\{(\w+)\}",
            r"(?P<\1>[^/]+)",
            path
        )

        self.routes.append(
            Route(
                method=method.upper(),
                pattern=re.compile("^" + regex + "$"),
                parameter_names=names,
                handler=handler
            )
        )

    def dispatch(
        self,
        request: RequestContext
    ) -> APIResponse:

        method_matched = False

        for route in self.routes:

            match = route.pattern.match(request.path)

            if not match:
                continue

            if route.method != request.method:
                method_matched = True
                continue

            request.params = match.groupdict()

            return route.handler(request)

        if method_matched:
            return APIResponse(
                405,
                {"error": "METHOD_NOT_ALLOWED"}
            )

        return APIResponse(
            404,
            {"error": "ROUTE_NOT_FOUND"}
        )


# ---------------------------------------------------------
# Controllers
# ---------------------------------------------------------

class TaskController:

    def __init__(self, service: TaskService):
        self.service = service

    @staticmethod
    def serialize(task: Task) -> dict[str, Any]:
        return asdict(task) | {
            "status": task.status.value
        }

    def list_tasks(
        self,
        request: RequestContext
    ) -> APIResponse:

        tasks = self.service.list_tasks()

        return APIResponse(
            200,
            {
                "count": len(tasks),
                "data": [
                    self.serialize(task)
                    for task in tasks
                ]
            }
        )

    def get_task(
        self,
        request: RequestContext
    ) -> APIResponse:

        task_id = int(request.params["id"])

        task = self.service.get_task(task_id)

        return APIResponse(
            200,
            {"data": self.serialize(task)}
        )

    def create_task(
        self,
        request: RequestContext
    ) -> APIResponse:

        task = self.service.create_task(
            request.body
        )

        return APIResponse(
            201,
            {"data": self.serialize(task)}
        )

    def update_task(
        self,
        request: RequestContext
    ) -> APIResponse:

        task = self.service.update_task(
            int(request.params["id"]),
            request.body
        )

        return APIResponse(
            200,
            {"data": self.serialize(task)}
        )

    def delete_task(
        self,
        request: RequestContext
    ) -> APIResponse:

        self.service.delete_task(
            int(request.params["id"])
        )

        return APIResponse(
            200,
            {"message": "Task deleted successfully"}
        )


# ---------------------------------------------------------
# Application and middleware pipeline
# ---------------------------------------------------------

class BackendApplication:

    def __init__(self):
        self.repository = TaskRepository()
        self.service = TaskService(self.repository)
        self.controller = TaskController(self.service)

        self.router = Router()

        self.router.add(
            "GET",
            "/health",
            self.health
        )

        self.router.add(
            "GET",
            "/api/v1/tasks",
            self.controller.list_tasks
        )

        self.router.add(
            "POST",
            "/api/v1/tasks",
            self.controller.create_task
        )

        self.router.add(
            "GET",
            "/api/v1/tasks/{id}",
            self.controller.get_task
        )

        self.router.add(
            "PATCH",
            "/api/v1/tasks/{id}",
            self.controller.update_task
        )

        self.router.add(
            "DELETE",
            "/api/v1/tasks/{id}",
            self.controller.delete_task
        )

        self.middleware = [
            request_id_middleware,
            logging_middleware
        ]

    @staticmethod
    def health(request: RequestContext) -> APIResponse:
        return APIResponse(
            200,
            {
                "status": "healthy",
                "service": "task-api"
            }
        )

    def handle(
        self,
        request: RequestContext
    ) -> APIResponse:

        def endpoint(ctx):
            return self.router.dispatch(ctx)

        handler = endpoint

        for middleware in reversed(self.middleware):

            next_handler = handler

            handler = (
                lambda ctx, m=middleware, n=next_handler:
                m(ctx, n)
            )

        try:
            response = handler(request)

        except BackendError as error:
            response = APIResponse(
                error.status_code,
                {
                    "error": error.error_code,
                    "message": str(error)
                }
            )

        except ValueError:
            response = APIResponse(
                400,
                {
                    "error": "INVALID_PARAMETER",
                    "message": "Invalid route parameter"
                }
            )

        except Exception:
            logger.exception("Unexpected application error")

            response = APIResponse(
                500,
                {
                    "error": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred"
                }
            )

        return response


# ---------------------------------------------------------
# HTTP adapter
# ---------------------------------------------------------

application = BackendApplication()


class RequestHandler(BaseHTTPRequestHandler):

    server_version = "TaskBackend/1.0"

    def send_json(
        self,
        status: int,
        body: dict[str, Any]
    ) -> None:

        encoded = json.dumps(
            body,
            default=lambda obj: obj.value
            if isinstance(obj, Enum)
            else str(obj)
        ).encode("utf-8")

        self.send_response(status)

        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8"
        )

        self.send_header(
            "Content-Length",
            str(len(encoded))
        )

        self.send_header(
            "Cache-Control",
            "no-store"
        )

        self.end_headers()

        self.wfile.write(encoded)

    def handle_request(self):

        parsed = urlparse(self.path)

        content_length = self.headers.get(
            "Content-Length",
            "0"
        )

        try:
            length = int(content_length)

            if length < 0:
                raise ValueError

        except ValueError:
            self.send_json(
                400,
                {"error": "INVALID_CONTENT_LENGTH"}
            )
            return

        if length > MAX_BODY_SIZE:
            self.send_json(
                413,
                {"error": "PAYLOAD_TOO_LARGE"}
            )
            return

        body = {}

        if length:
            if self.headers.get(
                "Content-Type", ""
            ).split(";")[0].strip().lower() != "application/json":

                self.send_json(
                    415,
                    {"error": "UNSUPPORTED_MEDIA_TYPE"}
                )
                return

            try:
                body = json.loads(
                    self.rfile.read(length).decode("utf-8")
                )

                if not isinstance(body, dict):
                    raise ValueError

            except (ValueError, UnicodeDecodeError):
                self.send_json(
                    400,
                    {"error": "INVALID_JSON"}
                )
                return

        request = RequestContext(
            method=self.command,
            path=parsed.path,
            query=parse_qs(parsed.query),
            headers=dict(self.headers.items()),
            body=body
        )

        response = application.handle(request)

        self.send_json(
            response.status_code,
            response.body
        )

    def do_GET(self):
        self.handle_request()

    def do_POST(self):
        self.handle_request()

    def do_PATCH(self):
        self.handle_request()

    def do_DELETE(self):
        self.handle_request()

    def log_message(self, format, *args):
        logger.info(
            "%s - %s",
            self.client_address[0],
            format % args
        )


# ---------------------------------------------------------
# Integration tests
# ---------------------------------------------------------

def run_tests():

    app = BackendApplication()

    def request(method, path, body=None):

        return app.handle(
            RequestContext(
                method=method,
                path=path,
                query={},
                headers={},
                body=body or {}
            )
        )

    # Health endpoint
    assert request("GET", "/health").status_code == 200

    # Create
    created = request(
        "POST",
        "/api/v1/tasks",
        {
            "title": "Implement REST API",
            "description": "Build backend service"
        }
    )

    assert created.status_code == 201

    task_id = created.body["data"]["id"]

    # Retrieve
    assert request(
        "GET",
        f"/api/v1/tasks/{task_id}"
    ).status_code == 200

    # Update
    updated = request(
        "PATCH",
        f"/api/v1/tasks/{task_id}",
        {"status": "completed"}
    )

    assert updated.status_code == 200
    assert updated.body["data"]["status"] == "completed"

    # Validation
    assert request(
        "POST",
        "/api/v1/tasks",
        {"title": ""}
    ).status_code == 400

    # Missing resource
    assert request(
        "GET",
        "/api/v1/tasks/9999"
    ).status_code == 404

    # Method mismatch
    assert request(
        "PUT",
        "/api/v1/tasks"
    ).status_code == 405

    # Delete
    assert request(
        "DELETE",
        f"/api/v1/tasks/{task_id}"
    ).status_code == 200

    print("All backend integration tests passed.")


# ---------------------------------------------------------
# Entry point
# ---------------------------------------------------------

if __name__ == "__main__":

    run_tests()

    server = ThreadingHTTPServer(
        (HOST, PORT),
        RequestHandler
    )

    logger.info(
        "Backend server running at http://%s:%s",
        HOST,
        PORT
    )

    try:
        server.serve_forever()

    except KeyboardInterrupt:
        logger.info("Server shutdown requested")

    finally:
        server.server_close()
