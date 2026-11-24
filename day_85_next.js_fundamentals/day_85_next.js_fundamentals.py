"""
Next.js Fundamentals: Architecture, Routing, Layouts, Pages, and
Server/Client Components.

Executable with Python 3.10+.
This program models an App Router application, resolves static and
dynamic routes, composes nested layouts, and validates component
execution boundaries.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from urllib.parse import unquote, urlsplit
import re


class ComponentType(Enum):
    SERVER = "server"
    CLIENT = "client"


class RouteError(Exception):
    pass


class BoundaryError(Exception):
    pass


@dataclass(frozen=True)
class RouteSegment:
    name: str
    dynamic: bool = False
    catch_all: bool = False

    def matches(self, value: str) -> bool:
        if self.catch_all:
            return bool(value)
        if self.dynamic:
            return bool(value) and "/" not in value
        return self.name == value


@dataclass
class Layout:
    name: str
    segment: str
    component_type: ComponentType = ComponentType.SERVER
    preserves_state: bool = True


@dataclass
class Page:
    name: str
    template: str
    component_type: ComponentType = ComponentType.SERVER
    requires_authentication: bool = False


@dataclass
class Route:
    pattern: str
    page: Page
    layouts: list[Layout]
    segments: list[RouteSegment] = field(default_factory=list)

    def __post_init__(self):
        if not self.segments:
            self.segments = self.parse_pattern(self.pattern)

    @staticmethod
    def parse_pattern(pattern: str) -> list[RouteSegment]:
        if not pattern.startswith("/"):
            raise ValueError("Routes must start with '/'")

        if pattern == "/":
            return []

        result = []
        for part in pattern.strip("/").split("/"):
            if part.startswith("[...") and part.endswith("]"):
                result.append(
                    RouteSegment(part[4:-1], dynamic=True, catch_all=True)
                )
            elif part.startswith("[") and part.endswith("]"):
                result.append(
                    RouteSegment(part[1:-1], dynamic=True)
                )
            elif "[" in part or "]" in part:
                raise ValueError(f"Invalid dynamic segment: {part}")
            else:
                result.append(RouteSegment(part))

        return result


class RouteRegistry:
    """Maintains route definitions and performs deterministic matching."""

    def __init__(self):
        self.routes: list[Route] = []

    def register(self, route: Route):
        if any(r.pattern == route.pattern for r in self.routes):
            raise RouteError(f"Duplicate route: {route.pattern}")

        self.routes.append(route)

        # Static routes take precedence over dynamic routes.
        self.routes.sort(
            key=lambda r: (
                -sum(not s.dynamic for s in r.segments),
                -len(r.segments),
                r.pattern
            )
        )

    @staticmethod
    def normalize(path: str) -> list[str]:
        parsed = urlsplit(path)

        if parsed.scheme or parsed.netloc:
            raise RouteError("Only relative application paths are accepted")

        decoded = unquote(parsed.path)

        if "\\" in decoded or "\x00" in decoded:
            raise RouteError("Invalid path characters")

        parts = decoded.strip("/").split("/")
        if parts == [""]:
            return []

        if any(p in (".", "..") for p in parts):
            raise RouteError("Path traversal is not allowed")

        return parts

    def resolve(self, path: str):
        parts = self.normalize(path)

        for route in self.routes:
            params = {}
            segments = route.segments

            if segments and segments[-1].catch_all:
                fixed_count = len(segments) - 1
                if len(parts) < fixed_count + 1:
                    continue
            elif len(parts) != len(segments):
                continue

            matched = True

            for index, segment in enumerate(segments):
                if segment.catch_all:
                    value = parts[index:]
                    if not value:
                        matched = False
                        break
                    params[segment.name] = value
                elif segment.dynamic:
                    if not segment.matches(parts[index]):
                        matched = False
                        break
                    params[segment.name] = parts[index]
                elif not segment.matches(parts[index]):
                    matched = False
                    break

            if matched:
                return route, params

        raise RouteError(f"No route found for {path}")


@dataclass
class Component:
    name: str
    component_type: ComponentType
    imports: list[str] = field(default_factory=list)
    uses_state: bool = False
    uses_effect: bool = False
    uses_browser_api: bool = False
    event_handlers: bool = False

    def validate(self):
        interactive = (
            self.uses_state
            or self.uses_effect
            or self.uses_browser_api
            or self.event_handlers
        )

        if interactive and self.component_type != ComponentType.CLIENT:
            raise BoundaryError(
                f"{self.name} requires a Client Component boundary"
            )


class ModuleGraph:
    """Tracks the transitive client bundle boundary."""

    def __init__(self):
        self.components: dict[str, Component] = {}

    def add(self, component: Component):
        if component.name in self.components:
            raise ValueError(f"Duplicate component: {component.name}")
        component.validate()
        self.components[component.name] = component

    def client_bundle(self, entry: str) -> set[str]:
        if entry not in self.components:
            raise KeyError(entry)

        visited = set()
        stack = [entry]

        while stack:
            name = stack.pop()
            if name in visited:
                continue

            component = self.components.get(name)
            if component is None:
                raise KeyError(f"Unknown imported component: {name}")

            visited.add(name)
            stack.extend(component.imports)

        return visited


class Renderer:
    def render(self, route: Route, params: dict[str, Any]) -> str:
        content = route.page.template

        for key, value in params.items():
            content = content.replace(
                "{{" + key + "}}",
                "/".join(value) if isinstance(value, list) else str(value)
            )

        # Nested layouts wrap the page from the innermost to outermost.
        for layout in reversed(route.layouts):
            content = f"{layout.name}({content})"

        return content


class NavigationSession:
    """Simulates client navigation and shared-layout state preservation."""

    def __init__(self):
        self.current_path = "/"
        self.layout_state: dict[str, dict[str, Any]] = {}

    def set_layout_state(self, layout: str, key: str, value: Any):
        self.layout_state.setdefault(layout, {})[key] = value

    def navigate(self, destination: str, route: Route):
        old_path = self.current_path
        old_segments = old_path.strip("/").split("/") if old_path != "/" else []
        new_segments = destination.strip("/").split("/") if destination != "/" else []

        shared = []
        for layout in route.layouts:
            if layout.preserves_state:
                shared.append(layout.name)

        self.current_path = destination

        return {
            "previous": old_path,
            "current": destination,
            "shared_layouts": shared,
            "segment_depth_changed": len(old_segments) != len(new_segments)
        }


def build_application() -> RouteRegistry:
    registry = RouteRegistry()

    root = Layout("RootLayout", "/")
    blog = Layout("BlogLayout", "/blog")
    dashboard = Layout("DashboardLayout", "/dashboard")

    definitions = [
        Route(
            "/",
            Page("HomePage", "Home"),
            [root]
        ),
        Route(
            "/about",
            Page("AboutPage", "About"),
            [root]
        ),
        Route(
            "/blog",
            Page("BlogIndex", "Blog articles"),
            [root, blog]
        ),
        Route(
            "/blog/[slug]",
            Page("BlogPost", "Article: {{slug}}"),
            [root, blog]
        ),
        Route(
            "/dashboard",
            Page(
                "DashboardPage",
                "Dashboard",
                requires_authentication=True
            ),
            [root, dashboard]
        ),
        Route(
            "/docs/[...slug]",
            Page("DocumentationPage", "Documentation: {{slug}}"),
            [root]
        )
    ]

    for route in definitions:
        registry.register(route)

    return registry


def demonstrate_routing(registry):
    renderer = Renderer()

    examples = [
        "/",
        "/about",
        "/blog",
        "/blog/nextjs-fundamentals",
        "/dashboard",
        "/docs/app/routing/dynamic-segments"
    ]

    print("\nROUTE RESOLUTION")

    for path in examples:
        route, params = registry.resolve(path)
        print(
            f"{path:40} -> {route.page.name:20} "
            f"params={params}"
        )
        print("Rendered:", renderer.render(route, params))


def demonstrate_component_boundaries():
    graph = ModuleGraph()

    graph.add(
        Component(
            "Logo",
            ComponentType.SERVER
        )
    )

    graph.add(
        Component(
            "SearchBox",
            ComponentType.CLIENT,
            uses_state=True,
            event_handlers=True
        )
    )

    graph.add(
        Component(
            "Navigation",
            ComponentType.SERVER,
            imports=["Logo", "SearchBox"]
        )
    )

    print("\nCLIENT MODULE GRAPH")
    print(graph.client_bundle("Navigation"))

    try:
        Component(
            "InvalidCounter",
            ComponentType.SERVER,
            uses_state=True
        ).validate()
    except BoundaryError as error:
        print("Expected boundary error:", error)


def demonstrate_navigation(registry):
    session = NavigationSession()

    session.set_layout_state(
        "RootLayout", "theme", "dark"
    )

    session.set_layout_state(
        "DashboardLayout", "sidebar", "expanded"
    )

    route, _ = registry.resolve("/dashboard")

    print("\nNAVIGATION")
    print(session.navigate("/dashboard", route))
    print("Preserved state:", session.layout_state)


def demonstrate_edge_cases(registry):
    print("\nEDGE CASES")

    invalid_paths = [
        "/unknown",
        "/blog/",
        "/../../etc/passwd",
        "https://example.com/blog",
        "/blog/%2e%2e/admin"
    ]

    for path in invalid_paths:
        try:
            route, params = registry.resolve(path)
            print(path, "->", route.page.name, params)
        except (RouteError, ValueError) as error:
            print(path, "-> REJECTED:", error)


def main():
    print("NEXT.JS FUNDAMENTALS SIMULATOR")
    print("=" * 55)

    registry = build_application()

    demonstrate_routing(registry)
    demonstrate_component_boundaries()
    demonstrate_navigation(registry)
    demonstrate_edge_cases(registry)

    print("\nVALIDATION")
    assert registry.resolve("/")[0].page.name == "HomePage"
    assert registry.resolve("/blog/python")[1]["slug"] == "python"

    docs = registry.resolve("/docs/app/routing")
    assert docs[1]["slug"] == ["app", "routing"]

    assert len(registry.routes) == 6

    print("All assertions passed.")


if __name__ == "__main__":
    main()
