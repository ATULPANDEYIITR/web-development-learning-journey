#!/usr/bin/env python3
"""
React Routing: SPA Routing, Nested Routes, Route Parameters,
Protected Routes, Navigation, and Route Resolution.

This standalone program simulates the core behavior of a React-style
client-side routing system using Python's standard library.
"""

from __future__ import annotations

import re
import unittest
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional
from urllib.parse import parse_qs, unquote, urlsplit


class RouteError(Exception):
    """Base exception for routing errors."""


class InvalidRouteError(RouteError):
    pass


class AccessDeniedError(RouteError):
    pass


class NotFoundError(RouteError):
    pass


class UserRole(Enum):
    GUEST = "guest"
    USER = "user"
    ADMIN = "admin"


@dataclass(frozen=True)
class User:
    user_id: int
    username: str
    role: UserRole
    authenticated: bool = True


@dataclass
class Route:
    path: str
    component: str
    children: list["Route"] = field(default_factory=list)
    protected: bool = False
    allowed_roles: set[UserRole] = field(default_factory=set)
    redirect: Optional[str] = None
    exact: bool = True


@dataclass
class RouteMatch:
    route: Route
    params: dict[str, str]
    query: dict[str, list[str]]
    pathname: str
    component_chain: list[str]


@dataclass
class NavigationResult:
    requested_url: str
    resolved_url: str
    status: str
    component_chain: list[str]
    params: dict[str, str]
    query: dict[str, list[str]]
    message: str


def normalize_path(path: str) -> str:
    """Normalize repeated slashes and trailing slashes."""
    if not path or not path.startswith("/"):
        raise InvalidRouteError("Route paths must start with '/'.")

    path = re.sub(r"/+", "/", path)

    if path != "/":
        path = path.rstrip("/")

    return path or "/"


def compile_route_pattern(pattern: str) -> tuple[re.Pattern, list[str]]:
    """
    Convert /users/:userId into a regular expression with named parameters.
    """
    pattern = normalize_path(pattern)
    names = []
    parts = []

    for segment in pattern.strip("/").split("/") if pattern != "/" else []:
        if segment.startswith(":"):
            name = segment[1:]

            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
                raise InvalidRouteError(f"Invalid parameter: {name}")

            if name in names:
                raise InvalidRouteError(f"Duplicate parameter: {name}")

            names.append(name)
            parts.append(f"(?P<{name}>[^/]+)")
        elif segment == "*":
            names.append("wildcard")
            parts.append("(?P<wildcard>.*)")
        else:
            parts.append(re.escape(segment))

    expression = "/" + "/".join(parts)

    return re.compile("^" + expression + "$"), names


def match_path(pattern: str, pathname: str) -> Optional[dict[str, str]]:
    regex, _ = compile_route_pattern(pattern)
    match = regex.fullmatch(pathname)

    if not match:
        return None

    return {
        key: unquote(value)
        for key, value in match.groupdict().items()
    }


class Router:
    def __init__(self, routes: list[Route]):
        self.routes = routes
        self._validate_routes(routes)

    def _validate_routes(self, routes: list[Route]) -> None:
        seen = set()

        for route in routes:
            route.path = normalize_path(route.path)

            if route.path in seen:
                raise InvalidRouteError(
                    f"Duplicate sibling route: {route.path}"
                )

            seen.add(route.path)
            compile_route_pattern(route.path)

            if route.protected and not route.allowed_roles:
                raise InvalidRouteError(
                    f"Protected route {route.path} needs allowed roles."
                )

            self._validate_routes(route.children)

    def _resolve(
        self,
        routes: list[Route],
        pathname: str,
        parent_components: Optional[list[str]] = None,
        parent_params: Optional[dict[str, str]] = None,
    ) -> Optional[RouteMatch]:

        parent_components = parent_components or []
        parent_params = parent_params or {}

        for route in routes:
            params = match_path(route.path, pathname)

            if params is None:
                continue

            combined_params = {**parent_params, **params}
            components = parent_components + [route.component]

            if route.children:
                nested = self._resolve(
                    route.children,
                    pathname,
                    components,
                    combined_params,
                )

                if nested:
                    return nested

            return RouteMatch(
                route=route,
                params=combined_params,
                query={},
                pathname=pathname,
                component_chain=components,
            )

        return None

    def resolve(self, url: str, user: Optional[User] = None) -> NavigationResult:
        parsed = urlsplit(url)
        pathname = normalize_path(parsed.path)
        query = parse_qs(parsed.query, keep_blank_values=True)

        match = self._resolve(self.routes, pathname)

        if not match:
            return NavigationResult(
                url, pathname, "NOT_FOUND", ["NotFound"],
                {}, query, "No matching route."
            )

        match.query = query

        route = match.route

        if route.redirect:
            return self.resolve(route.redirect, user)

        if route.protected:
            if not user or not user.authenticated:
                return NavigationResult(
                    url, "/login", "REDIRECT",
                    ["Login"], {}, query,
                    "Authentication required."
                )

            if user.role not in route.allowed_roles:
                return NavigationResult(
                    url, pathname, "FORBIDDEN",
                    ["Forbidden"], match.params, query,
                    "User does not have the required role."
                )

        return NavigationResult(
            url,
            pathname,
            "OK",
            match.component_chain,
            match.params,
            query,
            "Route resolved successfully.",
        )


class NavigationHistory:
    """Maintain browser-like navigation history."""

    def __init__(self):
        self.entries: list[str] = []
        self.index = -1

    def push(self, url: str) -> None:
        self.entries = self.entries[:self.index + 1]
        self.entries.append(url)
        self.index += 1

    def replace(self, url: str) -> None:
        if self.index < 0:
            self.push(url)
        else:
            self.entries[self.index] = url

    def back(self) -> Optional[str]:
        if self.index > 0:
            self.index -= 1
            return self.entries[self.index]
        return None

    def forward(self) -> Optional[str]:
        if self.index + 1 < len(self.entries):
            self.index += 1
            return self.entries[self.index]
        return None

    @property
    def current(self) -> Optional[str]:
        if self.index < 0:
            return None
        return self.entries[self.index]


class RouteGuard:
    """Reusable authentication and authorization policy."""

    @staticmethod
    def can_access(
        user: Optional[User],
        roles: set[UserRole],
    ) -> bool:
        return bool(
            user
            and user.authenticated
            and user.role in roles
        )


def build_application_router() -> Router:
    return Router([
        Route("/", "ApplicationLayout", children=[
            Route("/", "HomePage"),
            Route("/about", "AboutPage"),
            Route("/products", "ProductsLayout", children=[
                Route("/products", "ProductList"),
                Route("/products/:productId", "ProductDetails"),
            ]),
            Route("/users", "UsersLayout", children=[
                Route("/users/:userId", "UserProfile"),
            ]),
            Route(
                "/dashboard",
                "DashboardLayout",
                protected=True,
                allowed_roles={UserRole.USER, UserRole.ADMIN},
            ),
            Route(
                "/admin",
                "AdminLayout",
                protected=True,
                allowed_roles={UserRole.ADMIN},
            ),
            Route("/login", "LoginPage"),
        ]),
    ])


class RoutingTests(unittest.TestCase):

    def setUp(self):
        self.router = build_application_router()
        self.user = User(1, "alice", UserRole.USER)
        self.admin = User(2, "root", UserRole.ADMIN)

    def test_home(self):
        result = self.router.resolve("/")
        self.assertEqual(result.status, "OK")

    def test_nested_route(self):
        result = self.router.resolve("/products")
        self.assertEqual(
            result.component_chain,
            ["ApplicationLayout", "ProductsLayout", "ProductList"],
        )

    def test_parameters(self):
        result = self.router.resolve("/products/105")
        self.assertEqual(result.params["productId"], "105")

    def test_query_parameters(self):
        result = self.router.resolve("/products?category=books")
        self.assertEqual(result.query["category"], ["books"])

    def test_protected_guest(self):
        result = self.router.resolve("/dashboard")
        self.assertEqual(result.status, "REDIRECT")

    def test_protected_user(self):
        result = self.router.resolve("/dashboard", self.user)
        self.assertEqual(result.status, "OK")

    def test_admin_restriction(self):
        result = self.router.resolve("/admin", self.user)
        self.assertEqual(result.status, "FORBIDDEN")

    def test_admin_access(self):
        result = self.router.resolve("/admin", self.admin)
        self.assertEqual(result.status, "OK")

    def test_not_found(self):
        result = self.router.resolve("/missing")
        self.assertEqual(result.status, "NOT_FOUND")

    def test_history(self):
        history = NavigationHistory()
        history.push("/")
        history.push("/products")
        self.assertEqual(history.back(), "/")
        self.assertEqual(history.forward(), "/products")


def demonstrate():
    router = build_application_router()

    user = User(
        user_id=101,
        username="alice",
        role=UserRole.USER,
    )

    admin = User(
        user_id=102,
        username="administrator",
        role=UserRole.ADMIN,
    )

    examples = [
        ("/", None),
        ("/products", None),
        ("/products/501", None),
        ("/users/101?tab=activity", user),
        ("/dashboard", None),
        ("/dashboard", user),
        ("/admin", user),
        ("/admin", admin),
        ("/unknown", None),
    ]

    print("REACT ROUTING SIMULATION")
    print("=" * 65)

    for url, current_user in examples:
        result = router.resolve(url, current_user)

        print(f"\nURL: {url}")
        print(f"Status: {result.status}")
        print(f"Components: {' -> '.join(result.component_chain)}")
        print(f"Parameters: {result.params}")
        print(f"Query: {result.query}")
        print(f"Message: {result.message}")

    history = NavigationHistory()
    history.push("/")
    history.push("/products")
    history.push("/products/501")

    print("\nNAVIGATION HISTORY")
    print(history.entries)
    print("Back:", history.back())
    print("Current:", history.current)


if __name__ == "__main__":
    demonstrate()
    print("\nRUNNING TESTS")
    unittest.main(argv=["routing.py"], exit=False)
