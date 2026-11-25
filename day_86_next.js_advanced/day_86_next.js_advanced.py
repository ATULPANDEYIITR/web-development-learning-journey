#!/usr/bin/env python3
"""
Next.js Advanced Architecture Simulator

Demonstrates:
- Server Components and Client Components
- Server-to-client serialization boundaries
- Server-side data fetching
- Suspense-style loading states
- Streaming segment states
- Error boundaries and recovery
- Not-found handling
- Nested route segments
- Request-scoped data caching
- Rendering lifecycle and validation

Python 3.10+
Standard library only.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(message)s"
)

logger = logging.getLogger("nextjs_simulator")


class ComponentType(Enum):
    SERVER = "server"
    CLIENT = "client"


class RenderState(Enum):
    CREATED = "created"
    LOADING = "loading"
    STREAMING = "streaming"
    READY = "ready"
    ERROR = "error"
    NOT_FOUND = "not_found"
    RECOVERED = "recovered"


class BoundaryType(Enum):
    SUSPENSE = "suspense"
    ERROR = "error"


class ApplicationError(Exception):
    """Base application exception."""


class SerializationError(ApplicationError):
    """Raised when a value cannot cross the client boundary."""


class DataFetchError(ApplicationError):
    """Raised when server-side data retrieval fails."""


class NotFoundError(ApplicationError):
    """Raised when a requested resource does not exist."""


class InvalidTransitionError(ApplicationError):
    """Raised for invalid rendering state transitions."""


@dataclass(frozen=True)
class User:
    user_id: int
    name: str
    email: str
    role: str

    def public_data(self) -> dict[str, Any]:
        # Never expose internal account information unnecessarily.
        return {
            "id": self.user_id,
            "name": self.name,
            "role": self.role
        }


@dataclass
class Component:
    name: str
    component_type: ComponentType
    props: dict[str, Any] = field(default_factory=dict)
    children: list["Component"] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Component name cannot be empty.")

        if not isinstance(self.props, dict):
            raise TypeError("Component props must be a dictionary.")


@dataclass
class RenderResult:
    component_name: str
    state: RenderState
    output: Any = None
    error_message: str | None = None
    duration_ms: float = 0.0


@dataclass
class RouteSegment:
    name: str
    components: list[Component]
    loading_fallback: str
    error_fallback: str
    state: RenderState = RenderState.CREATED
    children: list["RouteSegment"] = field(default_factory=list)


class RequestCache:
    """
    Request-scoped cache.

    Data is shared within one request but is not retained
    between independent requests.
    """

    def __init__(self) -> None:
        self._values: dict[str, Any] = {}

    def get_or_load(
        self,
        key: str,
        loader: Callable[[], Any]
    ) -> Any:
        if key not in self._values:
            self._values[key] = loader()

        return self._values[key]


class SerializationBoundary:
    """
    Simulates the serializable-props restriction between
    Server Components and Client Components.
    """

    @staticmethod
    def validate(value: Any, path: str = "props") -> None:
        if value is None or isinstance(value, (str, int, float, bool)):
            if isinstance(value, float) and (
                value != value or value in (float("inf"), float("-inf"))
            ):
                raise SerializationError(
                    f"Non-finite number at {path}"
                )
            return

        if isinstance(value, list):
            for index, item in enumerate(value):
                SerializationBoundary.validate(
                    item,
                    f"{path}[{index}]"
                )
            return

        if isinstance(value, dict):
            for key, item in value.items():
                if not isinstance(key, str):
                    raise SerializationError(
                        f"Object key must be a string at {path}"
                    )

                SerializationBoundary.validate(
                    item,
                    f"{path}.{key}"
                )
            return

        raise SerializationError(
            f"Unsupported value at {path}: {type(value).__name__}"
        )

    @staticmethod
    def transfer(props: dict[str, Any]) -> dict[str, Any]:
        SerializationBoundary.validate(props)

        # JSON round-trip creates an independent transferable structure.
        return json.loads(json.dumps(props))


class ServerDataService:
    """
    Server-only data access.

    Sensitive fields remain on the server.
    """

    def __init__(self) -> None:
        self._users = {
            1: User(
                1,
                "Atul",
                "atul@example.com",
                "administrator"
            ),
            2: User(
                2,
                "Developer",
                "developer@example.com",
                "member"
            )
        }

    def get_user(self, user_id: int) -> dict[str, Any]:
        if user_id not in self._users:
            raise NotFoundError(
                f"User {user_id} does not exist."
            )

        return self._users[user_id].public_data()

    def get_dashboard(self, user_id: int) -> dict[str, Any]:
        user = self.get_user(user_id)

        return {
            "user": user,
            "metrics": {
                "projects": 12,
                "active_tasks": 8,
                "completed_tasks": 24
            }
        }


class ComponentRenderer:
    """
    Simulates component rendering and boundary enforcement.
    """

    def __init__(self, data_service: ServerDataService) -> None:
        self.data_service = data_service
        self.cache = RequestCache()
        self.results: list[RenderResult] = []

    def reset_request(self) -> None:
        self.cache = RequestCache()
        self.results.clear()

    def render_server_component(
        self,
        component: Component
    ) -> RenderResult:

        if component.component_type != ComponentType.SERVER:
            raise ValueError(
                "Expected a Server Component."
            )

        started = time.perf_counter()

        try:
            if component.name == "UserProfile":
                user_id = component.props.get("user_id", 1)

                output = self.cache.get_or_load(
                    f"user:{user_id}",
                    lambda: self.data_service.get_user(user_id)
                )

            elif component.name == "Dashboard":
                user_id = component.props.get("user_id", 1)

                output = self.cache.get_or_load(
                    f"dashboard:{user_id}",
                    lambda: self.data_service.get_dashboard(user_id)
                )

            elif component.name == "StaticContent":
                output = {
                    "content": component.props.get("content", "")
                }

            else:
                output = {
                    "component": component.name,
                    "props": component.props
                }

            result = RenderResult(
                component.name,
                RenderState.READY,
                output
            )

        except NotFoundError as exc:
            result = RenderResult(
                component.name,
                RenderState.NOT_FOUND,
                error_message=str(exc)
            )

        except Exception as exc:
            logger.exception("Server component rendering failed.")

            result = RenderResult(
                component.name,
                RenderState.ERROR,
                error_message=str(exc)
            )

        result.duration_ms = (
            time.perf_counter() - started
        ) * 1000

        self.results.append(result)
        return result

    def render_client_component(
        self,
        component: Component,
        server_output: dict[str, Any] | None = None
    ) -> RenderResult:

        if component.component_type != ComponentType.CLIENT:
            raise ValueError(
                "Expected a Client Component."
            )

        try:
            props = dict(component.props)

            if server_output is not None:
                props["server_data"] = server_output

            transferred = SerializationBoundary.transfer(props)

            return RenderResult(
                component.name,
                RenderState.READY,
                {
                    "component": component.name,
                    "serialized_props": transferred,
                    "hydration_required": True,
                    "interactive": True
                }
            )

        except SerializationError as exc:
            return RenderResult(
                component.name,
                RenderState.ERROR,
                error_message=str(exc)
            )


class SuspenseBoundary:
    """
    Represents a loading boundary around asynchronous work.
    """

    @staticmethod
    async def render(
        loader: Callable[[], Any],
        fallback: str,
        timeout: float = 3.0
    ) -> RenderResult:

        if timeout <= 0:
            raise ValueError("Timeout must be positive.")

        started = time.perf_counter()

        try:
            async def execute() -> Any:
                value = loader()

                if asyncio.iscoroutine(value):
                    return await value

                return value

            output = await asyncio.wait_for(
                execute(),
                timeout=timeout
            )

            state = RenderState.READY
            error = None

        except asyncio.TimeoutError:
            output = {"fallback": fallback}
            state = RenderState.STREAMING
            error = "Loading operation exceeded its timeout."

        except Exception as exc:
            output = None
            state = RenderState.ERROR
            error = str(exc)

        return RenderResult(
            "SuspenseBoundary",
            state,
            output,
            error,
            (time.perf_counter() - started) * 1000
        )


class ErrorBoundary:
    """
    Simulates a segment-level error boundary.

    A production Next.js error.tsx component must be a
    Client Component and uses reset() for recovery.
    """

    def __init__(self, fallback: str) -> None:
        self.fallback = fallback
        self.last_error: str | None = None
        self.recovery_attempts = 0

    def execute(
        self,
        operation: Callable[[], Any]
    ) -> RenderResult:

        try:
            output = operation()

            return RenderResult(
                "ErrorBoundary",
                RenderState.READY,
                output
            )

        except Exception as exc:
            self.last_error = str(exc)

            return RenderResult(
                "ErrorBoundary",
                RenderState.ERROR,
                {"fallback": self.fallback},
                self.last_error
            )

    def reset(
        self,
        operation: Callable[[], Any]
    ) -> RenderResult:

        self.recovery_attempts += 1

        result = self.execute(operation)

        if result.state == RenderState.READY:
            result.state = RenderState.RECOVERED
            self.last_error = None

        return result


class NextApplication:
    """
    Application-level rendering orchestration.
    """

    def __init__(self) -> None:
        self.data = ServerDataService()
        self.renderer = ComponentRenderer(self.data)

    def render_dashboard(self, user_id: int = 1) -> dict[str, Any]:
        self.renderer.reset_request()

        server_component = Component(
            "Dashboard",
            ComponentType.SERVER,
            {"user_id": user_id}
        )

        server_result = self.renderer.render_server_component(
            server_component
        )

        if server_result.state != RenderState.READY:
            return {
                "route": "/dashboard",
                "state": server_result.state.value,
                "error": server_result.error_message
            }

        client_component = Component(
            "DashboardControls",
            ComponentType.CLIENT,
            {
                "theme": "dark",
                "refresh_enabled": True
            }
        )

        client_result = self.renderer.render_client_component(
            client_component,
            server_result.output
        )

        return {
            "route": "/dashboard",
            "server_component": server_result.output,
            "client_component": client_result.output,
            "server_render_state": server_result.state.value,
            "client_render_state": client_result.state.value
        }


async def demonstrate_loading_states() -> None:
    async def successful_fetch() -> dict[str, Any]:
        await asyncio.sleep(0.05)
        return {"projects": 12}

    async def slow_fetch() -> dict[str, Any]:
        await asyncio.sleep(0.3)
        return {"reports": 5}

    successful = await SuspenseBoundary.render(
        successful_fetch,
        "Loading projects...",
        timeout=1.0
    )

    slow = await SuspenseBoundary.render(
        slow_fetch,
        "Loading reports...",
        timeout=0.05
    )

    print("\nSUSPENSE RESULTS")
    print(successful.state.value, successful.output)
    print(slow.state.value, slow.output)


def demonstrate_error_recovery() -> None:
    boundary = ErrorBoundary(
        "Something went wrong. Please retry."
    )

    attempts = {"count": 0}

    def unreliable_operation() -> str:
        attempts["count"] += 1

        if attempts["count"] == 1:
            raise DataFetchError(
                "Temporary database connection failure."
            )

        return "Dashboard data successfully recovered."

    failed = boundary.execute(unreliable_operation)
    recovered = boundary.reset(unreliable_operation)

    print("\nERROR BOUNDARY")
    print("Initial:", failed.state.value, failed.error_message)
    print("Recovery:", recovered.state.value, recovered.output)


def demonstrate_serialization_validation() -> None:
    print("\nSERIALIZATION VALIDATION")

    valid_props = {
        "user": {"id": 1, "name": "Atul"},
        "features": ["analytics", "reports"]
    }

    print(
        "Valid:",
        SerializationBoundary.transfer(valid_props)
    )

    invalid_props = {
        "callback": lambda: print("Not serializable")
    }

    try:
        SerializationBoundary.transfer(invalid_props)
    except SerializationError as exc:
        print("Rejected:", exc)


def demonstrate_nested_routes() -> None:
    dashboard = RouteSegment(
        name="dashboard",
        components=[],
        loading_fallback="Loading dashboard..."
    )

    analytics = RouteSegment(
        name="analytics",
        components=[],
        loading_fallback="Loading analytics...",
        error_fallback="Analytics unavailable."
    )

    reports = RouteSegment(
        name="reports",
        components=[],
        loading_fallback="Loading reports...",
        error_fallback="Reports unavailable."
    )

    dashboard.children.extend([analytics, reports])

    print("\nNESTED ROUTE STRUCTURE")

    for child in dashboard.children:
        print(
            f"/dashboard/{child.name} -> "
            f"{child.loading_fallback}"
        )


def run_assertions() -> None:
    # Serializable primitives and nested collections.
    SerializationBoundary.validate({
        "id": 10,
        "active": True,
        "items": [1, 2, 3]
    })

    # Unsupported callbacks must be rejected.
    try:
        SerializationBoundary.validate(
            {"handler": lambda: None}
        )
        raise AssertionError("Expected serialization failure.")
    except SerializationError:
        pass

    # Missing users must not produce successful output.
    app = NextApplication()

    missing = app.renderer.render_server_component(
        Component(
            "UserProfile",
            ComponentType.SERVER,
            {"user_id": 999}
        )
    )

    assert missing.state == RenderState.NOT_FOUND

    # Request cache must avoid duplicate loads.
    cache = RequestCache()
    calls = {"count": 0}

    def loader() -> int:
        calls["count"] += 1
        return 42

    assert cache.get_or_load("value", loader) == 42
    assert cache.get_or_load("value", loader) == 42
    assert calls["count"] == 1

    print("\nAll assertions passed.")


async def main() -> None:
    print("=" * 65)
    print("NEXT.JS ADVANCED ARCHITECTURE SIMULATOR")
    print("=" * 65)

    application = NextApplication()

    print("\nSERVER AND CLIENT COMPONENTS")

    dashboard = application.render_dashboard()

    print(json.dumps(
        dashboard,
        indent=2
    ))

    demonstrate_serialization_validation()

    await demonstrate_loading_states()

    demonstrate_error_recovery()

    demonstrate_nested_routes()

    run_assertions()

    print("\nExecution completed.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("Execution interrupted by user.")
