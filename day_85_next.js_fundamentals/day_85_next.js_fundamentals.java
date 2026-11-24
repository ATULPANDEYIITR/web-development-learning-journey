import java.net.URI;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.TreeMap;

/**
 * Next.js Fundamentals
 *
 * Enterprise-oriented application architecture model.
 *
 * Demonstrates:
 * - App Router file-system route definitions
 * - Dynamic route parameters
 * - Nested layouts
 * - Server and Client Component policies
 * - Module dependency validation
 * - Authentication and authorization
 * - Navigation state
 * - Rendering eligibility
 *
 * Java version: 17+
 *
 * Run:
 * javac NextJsFundamentals.java
 * java NextJsFundamentals
 */
public class NextJsFundamentals {

    enum ComponentKind {
        SERVER,
        CLIENT
    }

    enum RenderStatus {
        SUCCESS,
        NOT_FOUND,
        UNAUTHORIZED,
        INVALID_COMPONENT
    }

    enum SegmentKind {
        STATIC,
        DYNAMIC,
        CATCH_ALL
    }

    static class ApplicationException extends RuntimeException {
        ApplicationException(String message) {
            super(message);
        }
    }

    record Segment(String name, SegmentKind kind) {
        Segment {
            Objects.requireNonNull(name);
            Objects.requireNonNull(kind);
        }
    }

    record Layout(
        String name,
        boolean preservesState,
        ComponentKind kind
    ) {}

    record Page(
        String name,
        boolean authenticationRequired,
        String content
    ) {}

    record RouteDefinition(
        String pattern,
        Page page,
        List<Layout> layouts,
        List<Segment> segments
    ) {
        RouteDefinition {
            Objects.requireNonNull(pattern);
            Objects.requireNonNull(page);
            layouts = List.copyOf(layouts);
            segments = List.copyOf(segments);
        }
    }

    record RouteMatch(
        RouteDefinition route,
        Map<String, String> parameters,
        Map<String, String> queryParameters
    ) {
        RouteMatch {
            parameters = Map.copyOf(parameters);
            queryParameters = Map.copyOf(queryParameters);
        }
    }

    record Component(
        String name,
        ComponentKind kind,
        Set<String> dependencies,
        Set<String> features
    ) {
        Component {
            dependencies = Set.copyOf(dependencies);
            features = Set.copyOf(features);
        }
    }

    record RequestContext(
        boolean authenticated,
        Set<String> roles
    ) {
        RequestContext {
            roles = Set.copyOf(roles);
        }
    }

    record RenderResult(
        RenderStatus status,
        String content,
        RouteMatch match
    ) {}

    static final class RouteParser {

        static List<Segment> parse(String pattern) {
            if (pattern == null || !pattern.startsWith("/")) {
                throw new ApplicationException(
                    "Route must start with '/'"
                );
            }

            if (pattern.equals("/")) {
                return List.of();
            }

            List<Segment> segments = new ArrayList<>();

            for (String part : pattern.substring(1).split("/")) {
                if (part.isBlank()) {
                    throw new ApplicationException(
                        "Empty route segment"
                    );
                }

                if (part.startsWith("[...") && part.endsWith("]")) {
                    segments.add(new Segment(
                        part.substring(4, part.length() - 1),
                        SegmentKind.CATCH_ALL
                    ));
                } else if (
                    part.startsWith("[") && part.endsWith("]")
                ) {
                    segments.add(new Segment(
                        part.substring(1, part.length() - 1),
                        SegmentKind.DYNAMIC
                    ));
                } else {
                    if (part.contains("[") || part.contains("]")) {
                        throw new ApplicationException(
                            "Malformed dynamic route segment"
                        );
                    }

                    segments.add(new Segment(
                        part,
                        SegmentKind.STATIC
                    ));
                }
            }

            long catchAllCount = segments.stream()
                .filter(s -> s.kind() == SegmentKind.CATCH_ALL)
                .count();

            if (catchAllCount > 1 ||
                (!segments.isEmpty() &&
                 segments.subList(0, segments.size() - 1)
                    .stream()
                    .anyMatch(s -> s.kind() == SegmentKind.CATCH_ALL))) {
                throw new ApplicationException(
                    "Catch-all must occur once at the end"
                );
            }

            return List.copyOf(segments);
        }

        static List<String> normalize(String path) {
            if (path == null || path.length() > 2048) {
                throw new ApplicationException("Invalid request path");
            }

            URI uri;

            try {
                uri = URI.create(path);
            } catch (IllegalArgumentException error) {
                throw new ApplicationException("Malformed URL");
            }

            if (uri.isAbsolute() || uri.getRawAuthority() != null) {
                throw new ApplicationException(
                    "Only relative paths are accepted"
                );
            }

            String rawPath = uri.getRawPath();

            if (rawPath == null || rawPath.isEmpty() ||
                rawPath.equals("/")) {
                return List.of();
            }

            List<String> result = new ArrayList<>();

            for (String part : rawPath.substring(1).split("/")) {
                String decoded;

                try {
                    decoded = URLDecoder.decode(
                        part.replace("+", "%2B"),
                        StandardCharsets.UTF_8
                    );
                } catch (IllegalArgumentException error) {
                    throw new ApplicationException(
                        "Invalid URL encoding"
                    );
                }

                if (decoded.equals(".") ||
                    decoded.equals("..") ||
                    decoded.contains("\\") ||
                    decoded.contains("\0")) {
                    throw new ApplicationException(
                        "Unsafe path segment"
                    );
                }

                result.add(decoded);
            }

            return List.copyOf(result);
        }
    }

    static final class Router {
        private final List<RouteDefinition> routes =
            new ArrayList<>();

        void register(
            String pattern,
            Page page,
            List<Layout> layouts
        ) {
            if (routes.stream().anyMatch(
                route -> route.pattern().equals(pattern)
            )) {
                throw new ApplicationException(
                    "Duplicate route: " + pattern
                );
            }

            RouteDefinition definition = new RouteDefinition(
                pattern,
                page,
                layouts,
                RouteParser.parse(pattern)
            );

            routes.add(definition);

            routes.sort(
                Comparator
                    .comparingLong((RouteDefinition r) ->
                        r.segments().stream()
                            .filter(s -> s.kind() == SegmentKind.STATIC)
                            .count()
                    )
                    .reversed()
                    .thenComparing(
                        Comparator.comparingInt(
                            (RouteDefinition r) ->
                                r.segments().size()
                        ).reversed()
                    )
            );
        }

        RouteMatch resolve(String path) {
            List<String> parts = RouteParser.normalize(path);

            Map<String, String> query = new LinkedHashMap<>();

            URI uri = URI.create(path);
            if (uri.getRawQuery() != null) {
                for (String item : uri.getRawQuery().split("&")) {
                    String[] pair = item.split("=", 2);

                    String key = URLDecoder.decode(
                        pair[0],
                        StandardCharsets.UTF_8
                    );

                    String value = pair.length > 1
                        ? URLDecoder.decode(
                            pair[1],
                            StandardCharsets.UTF_8
                        )
                        : "";

                    query.put(key, value);
                }
            }

            for (RouteDefinition route : routes) {
                List<Segment> segments = route.segments();

                boolean catchAll =
                    !segments.isEmpty() &&
                    segments.get(segments.size() - 1).kind()
                        == SegmentKind.CATCH_ALL;

                if (catchAll) {
                    if (parts.size() < segments.size()) continue;
                } else if (parts.size() != segments.size()) {
                    continue;
                }

                Map<String, String> params = new HashMap<>();
                boolean valid = true;

                for (int i = 0; i < segments.size(); i++) {
                    Segment segment = segments.get(i);

                    if (segment.kind() == SegmentKind.STATIC) {
                        if (!segment.name().equals(parts.get(i))) {
                            valid = false;
                            break;
                        }
                    } else if (
                        segment.kind() == SegmentKind.DYNAMIC
                    ) {
                        params.put(segment.name(), parts.get(i));
                    } else {
                        params.put(
                            segment.name(),
                            String.join("/", parts.subList(i, parts.size()))
                        );
                    }
                }

                if (valid) {
                    return new RouteMatch(route, params, query);
                }
            }

            return null;
        }

        List<String> list() {
            return routes.stream()
                .map(RouteDefinition::pattern)
                .toList();
        }
    }

    static final class ComponentGovernance {
        private final Map<String, Component> components =
            new TreeMap<>();

        void register(Component component) {
            if (components.containsKey(component.name())) {
                throw new ApplicationException(
                    "Duplicate component: " + component.name()
                );
            }

            Set<String> browserFeatures = Set.of(
                "state",
                "effect",
                "browser-api",
                "event-handler"
            );

            boolean interactive = component.features().stream()
                .anyMatch(browserFeatures::contains);

            if (interactive &&
                component.kind() == ComponentKind.SERVER) {
                throw new ApplicationException(
                    "Server Component cannot directly use browser features: "
                        + component.name()
                );
            }

            components.put(component.name(), component);
        }

        Set<String> dependencyGraph(String entry) {
            Set<String> visited = new HashSet<>();
            Set<String> active = new HashSet<>();

            visit(entry, visited, active);

            return Collections.unmodifiableSet(visited);
        }

        private void visit(
            String name,
            Set<String> visited,
            Set<String> active
        ) {
            if (active.contains(name)) {
                throw new ApplicationException(
                    "Circular component dependency: " + name
                );
            }

            if (visited.contains(name)) return;

            Component component = components.get(name);

            if (component == null) {
                throw new ApplicationException(
                    "Missing component: " + name
                );
            }

            active.add(name);
            visited.add(name);

            for (String dependency : component.dependencies()) {
                visit(dependency, visited, active);
            }

            active.remove(name);
        }
    }

    static final class RenderingService {

        RenderResult render(
            RouteMatch match,
            RequestContext context
        ) {
            if (match == null) {
                return new RenderResult(
                    RenderStatus.NOT_FOUND,
                    "404 Not Found",
                    null
                );
            }

            Page page = match.route().page();

            if (page.authenticationRequired() &&
                !context.authenticated()) {
                return new RenderResult(
                    RenderStatus.UNAUTHORIZED,
                    "Authentication required",
                    match
                );
            }

            String content = page.content();

            for (Map.Entry<String, String> entry :
                match.parameters().entrySet()) {
                content = content.replace(
                    "{{" + entry.getKey() + "}}",
                    entry.getValue()
                );
            }

            List<Layout> layouts = match.route().layouts();

            for (int i = layouts.size() - 1; i >= 0; i--) {
                content = layouts.get(i).name() +
                    "(" + content + ")";
            }

            return new RenderResult(
                RenderStatus.SUCCESS,
                content,
                match
            );
        }
    }

    static final class NavigationSession {
        private String currentPath = "/";
        private final Map<String, Map<String, Object>> state =
            new HashMap<>();

        void updateLayoutState(
            String layout,
            String key,
            Object value
        ) {
            state.computeIfAbsent(
                layout,
                ignored -> new HashMap<>()
            ).put(key, value);
        }

        Object getLayoutState(String layout, String key) {
            return state.getOrDefault(layout, Map.of()).get(key);
        }

        void navigate(String destination, RouteDefinition route) {
            Objects.requireNonNull(route);

            String previous = currentPath;
            currentPath = destination;

            System.out.println(
                "Navigation: " + previous + " -> " + destination
            );

            System.out.println(
                "Shared layouts: " +
                    route.layouts().stream()
                        .filter(Layout::preservesState)
                        .map(Layout::name)
                        .toList()
            );
        }

        String currentPath() {
            return currentPath;
        }
    }

    static Router createApplication() {
        Router router = new Router();

        Layout root = new Layout(
            "RootLayout", true, ComponentKind.SERVER
        );

        Layout blog = new Layout(
            "BlogLayout", true, ComponentKind.SERVER
        );

        Layout dashboard = new Layout(
            "DashboardLayout", true, ComponentKind.SERVER
        );

        router.register(
            "/",
            new Page("HomePage", false, "Home"),
            List.of(root)
        );

        router.register(
            "/about",
            new Page("AboutPage", false, "About"),
            List.of(root)
        );

        router.register(
            "/blog",
            new Page("BlogIndex", false, "Blog articles"),
            List.of(root, blog)
        );

        router.register(
            "/blog/[slug]",
            new Page(
                "BlogPost",
                false,
                "Article: {{slug}}"
            ),
            List.of(root, blog)
        );

        router.register(
            "/dashboard",
            new Page(
                "Dashboard",
                true,
                "Private dashboard"
            ),
            List.of(root, dashboard)
        );

        router.register(
            "/docs/[...slug]",
            new Page(
                "Documentation",
                false,
                "Documentation: {{slug}}"
            ),
            List.of(root)
        );

        return router;
    }

    public static void main(String[] args) {
        Router router = createApplication();

        System.out.println("NEXT.JS FUNDAMENTALS");
        System.out.println("====================");

        System.out.println("\nREGISTERED ROUTES");
        router.list().forEach(System.out::println);

        System.out.println("\nROUTE RESOLUTION");

        for (String path : List.of(
            "/",
            "/about",
            "/blog",
            "/blog/server-components",
            "/docs/app/routing/dynamic",
            "/dashboard"
        )) {
            RouteMatch match = router.resolve(path);

            System.out.println(
                path + " -> " +
                match.route().page().name() +
                " | " + match.parameters()
            );
        }

        System.out.println("\nCOMPONENT GOVERNANCE");

        ComponentGovernance governance =
            new ComponentGovernance();

        governance.register(new Component(
            "Logo",
            ComponentKind.SERVER,
            Set.of(),
            Set.of()
        ));

        governance.register(new Component(
            "SearchBox",
            ComponentKind.CLIENT,
            Set.of(),
            Set.of("state", "event-handler")
        ));

        governance.register(new Component(
            "Navigation",
            ComponentKind.SERVER,
            Set.of("Logo", "SearchBox"),
            Set.of()
        ));

        System.out.println(
            "Navigation dependencies: " +
            governance.dependencyGraph("Navigation")
        );

        try {
            governance.register(new Component(
                "InvalidCounter",
                ComponentKind.SERVER,
                Set.of(),
                Set.of("state")
            ));
        } catch (ApplicationException error) {
            System.out.println(
                "Boundary rejected: " + error.getMessage()
            );
        }

        System.out.println("\nRENDERING");

        RenderingService rendering = new RenderingService();

        RequestContext anonymous =
            new RequestContext(false, Set.of());

        RenderResult home = rendering.render(
            router.resolve("/"),
            anonymous
        );

        System.out.println(home.content());

        RenderResult privatePage = rendering.render(
            router.resolve("/dashboard"),
            anonymous
        );

        System.out.println(
            privatePage.status() + ": " + privatePage.content()
        );

        RequestContext developer =
            new RequestContext(true, Set.of("developer"));

        RenderResult authorized = rendering.render(
            router.resolve("/dashboard"),
            developer
        );

        System.out.println(
            authorized.status() + ": " + authorized.content()
        );

        System.out.println("\nNAVIGATION STATE");

        NavigationSession session = new NavigationSession();

        session.updateLayoutState(
            "RootLayout",
            "theme",
            "dark"
        );

        session.navigate(
            "/blog/server-components",
            router.resolve("/blog/server-components").route()
        );

        System.out.println(
            "Theme: " +
            session.getLayoutState("RootLayout", "theme")
        );

        System.out.println("\nFAILURE CASES");

        for (String path : List.of(
            "/missing",
            "/../private"
        )) {
            try {
                RouteMatch match = router.resolve(path);

                System.out.println(
                    match == null ? "404" : match.route().pattern()
                );
            } catch (ApplicationException error) {
                System.out.println(error.getMessage());
            }
        }

        System.out.println("\nASSERTIONS");

        assert router.resolve("/blog/post").parameters()
            .get("slug").equals("post");

        assert router.resolve("/docs/app/router").parameters()
            .get("slug").equals("app/router");

        assert router.resolve("/missing") == null;

        assert privatePage.status() == RenderStatus.UNAUTHORIZED;

        assert authorized.status() == RenderStatus.SUCCESS;

        assert session.getLayoutState(
            "RootLayout",
            "theme"
        ).equals("dark");

        System.out.println("All tests passed.");
    }
}
