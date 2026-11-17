import java.net.URI;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collections;
import java.util.EnumSet;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * React Routing enterprise model.
 *
 * Covers SPA routing, nested routes, dynamic parameters,
 * authentication, authorization, navigation history,
 * redirects, and route access policies.
 *
 * Java 17, standard library only.
 */
public class Main {

    enum Role {
        GUEST, USER, ADMIN
    }

    enum NavigationStatus {
        SUCCESS, NOT_FOUND, REDIRECT, FORBIDDEN
    }

    enum AccessPolicy {
        PUBLIC, AUTHENTICATED, ROLE_RESTRICTED
    }

    record User(
        long id,
        String username,
        Role role,
        boolean authenticated
    ) {
        User {
            if (id <= 0) {
                throw new IllegalArgumentException("Invalid user ID.");
            }

            if (username == null || username.isBlank()) {
                throw new IllegalArgumentException("Username is required.");
            }

            if (role == null) {
                throw new IllegalArgumentException("User role is required.");
            }
        }
    }

    record RouteMatch(
        Route route,
        Map<String, String> parameters,
        List<String> componentChain,
        Map<String, List<String>> queryParameters
    ) {}

    record NavigationResult(
        NavigationStatus status,
        String pathname,
        List<String> components,
        Map<String, String> parameters,
        String message
    ) {}

    static class RoutingException extends RuntimeException {
        RoutingException(String message) {
            super(message);
        }
    }

    static class AccessDeniedException extends RoutingException {
        AccessDeniedException(String message) {
            super(message);
        }
    }

    static class Route {

        private final String path;
        private final String component;
        private final List<Route> children;
        private final AccessPolicy policy;
        private final Set<Role> allowedRoles;
        private final String redirect;

        Route(
            String path,
            String component,
            List<Route> children,
            AccessPolicy policy,
            Set<Role> allowedRoles,
            String redirect
        ) {
            this.path = normalize(path);
            this.component = component;
            this.children = List.copyOf(children);
            this.policy = policy;
            this.allowedRoles = Collections.unmodifiableSet(
                new HashSet<>(allowedRoles)
            );
            this.redirect = redirect;

            if (component == null || component.isBlank()) {
                throw new IllegalArgumentException(
                    "Component name is required."
                );
            }

            if (policy == AccessPolicy.ROLE_RESTRICTED
                && allowedRoles.isEmpty()) {
                throw new IllegalArgumentException(
                    "Role-restricted routes require allowed roles."
                );
            }
        }

        String path() {
            return path;
        }

        String component() {
            return component;
        }

        List<Route> children() {
            return children;
        }

        AccessPolicy policy() {
            return policy;
        }

        Set<Role> allowedRoles() {
            return allowedRoles;
        }

        String redirect() {
            return redirect;
        }
    }

    static String normalize(String path) {
        if (path == null || !path.startsWith("/")) {
            throw new IllegalArgumentException("Invalid route path.");
        }

        String normalized = path.replaceAll("/{2,}", "/");

        if (normalized.length() > 1) {
            normalized = normalized.replaceAll("/+$", "");
        }

        return normalized;
    }

    static List<String> segments(String path) {
        if (path.equals("/")) {
            return List.of();
        }

        return List.of(path.substring(1).split("/"));
    }

    static Optional<Map<String, String>> matchPattern(
        String pattern,
        String pathname
    ) {
        List<String> expected = segments(pattern);
        List<String> actual = segments(pathname);

        if (expected.size() != actual.size()) {
            return Optional.empty();
        }

        Map<String, String> parameters = new LinkedHashMap<>();

        for (int i = 0; i < expected.size(); i++) {
            String segment = expected.get(i);
            String value = actual.get(i);

            if (segment.startsWith(":")) {
                String name = segment.substring(1);

                if (!name.matches("[A-Za-z_][A-Za-z0-9_]*")
                    || parameters.containsKey(name)) {
                    return Optional.empty();
                }

                parameters.put(
                    name,
                    URLDecoder.decode(
                        value,
                        StandardCharsets.UTF_8
                    )
                );
            } else if (segment.equals("*")) {
                parameters.put("wildcard", value);
            } else if (!segment.equals(value)) {
                return Optional.empty();
            }
        }

        return Optional.of(parameters);
    }

    static class RouteRegistry {

        private final List<Route> routes;

        RouteRegistry(List<Route> routes) {
            this.routes = List.copyOf(routes);
            validate(routes);
        }

        private void validate(List<Route> candidates) {
            Set<String> siblingPaths = new HashSet<>();

            for (Route route : candidates) {
                if (!siblingPaths.add(route.path())) {
                    throw new RoutingException(
                        "Duplicate sibling route: " + route.path()
                    );
                }

                validate(route.children());
            }
        }

        Optional<RouteMatch> find(String url) {
            URI uri = URI.create(url);
            String pathname = normalize(uri.getPath());

            Map<String, List<String>> query = parseQuery(uri.getRawQuery());

            return resolve(
                routes,
                pathname,
                new ArrayList<>(),
                new LinkedHashMap<>(),
                query
            );
        }

        private Optional<RouteMatch> resolve(
            List<Route> candidates,
            String pathname,
            List<String> parents,
            Map<String, String> parentParams,
            Map<String, List<String>> query
        ) {
            for (Route route : candidates) {
                Optional<Map<String, String>> matched =
                    matchPattern(route.path(), pathname);

                if (matched.isEmpty()) {
                    continue;
                }

                Map<String, String> parameters =
                    new LinkedHashMap<>(parentParams);

                parameters.putAll(matched.get());

                List<String> components = new ArrayList<>(parents);
                components.add(route.component());

                if (!route.children().isEmpty()) {
                    Optional<RouteMatch> nested = resolve(
                        route.children(),
                        pathname,
                        components,
                        parameters,
                        query
                    );

                    if (nested.isPresent()) {
                        return nested;
                    }
                }

                return Optional.of(new RouteMatch(
                    route,
                    Map.copyOf(parameters),
                    List.copyOf(components),
                    query
                ));
            }

            return Optional.empty();
        }

        private Map<String, List<String>> parseQuery(String rawQuery) {
            Map<String, List<String>> query = new LinkedHashMap<>();

            if (rawQuery == null || rawQuery.isBlank()) {
                return query;
            }

            for (String pair : rawQuery.split("&")) {
                String[] parts = pair.split("=", 2);

                String key = URLDecoder.decode(
                    parts[0],
                    StandardCharsets.UTF_8
                );

                String value = parts.length == 2
                    ? URLDecoder.decode(
                        parts[1],
                        StandardCharsets.UTF_8
                    )
                    : "";

                query.computeIfAbsent(
                    key,
                    ignored -> new ArrayList<>()
                ).add(value);
            }

            Map<String, List<String>> immutable = new LinkedHashMap<>();

            query.forEach((key, values) ->
                immutable.put(key, List.copyOf(values))
            );

            return Collections.unmodifiableMap(immutable);
        }
    }

    static class AuthorizationService {

        boolean authorize(Route route, User user) {
            if (route.policy() == AccessPolicy.PUBLIC) {
                return true;
            }

            if (user == null || !user.authenticated()) {
                return false;
            }

            if (route.policy() == AccessPolicy.AUTHENTICATED) {
                return true;
            }

            return route.allowedRoles().contains(user.role());
        }
    }

    static class NavigationService {

        private final RouteRegistry registry;
        private final AuthorizationService authorization;
        private final List<String> history = new ArrayList<>();
        private int historyIndex = -1;

        NavigationService(
            RouteRegistry registry,
            AuthorizationService authorization
        ) {
            this.registry = registry;
            this.authorization = authorization;
        }

        NavigationResult navigate(
            String url,
            User user,
            boolean replace
        ) {
            URI uri = URI.create(url);
            String pathname = normalize(uri.getPath());

            Optional<RouteMatch> optionalMatch = registry.find(url);

            if (optionalMatch.isEmpty()) {
                return new NavigationResult(
                    NavigationStatus.NOT_FOUND,
                    pathname,
                    List.of("NotFound"),
                    Map.of(),
                    "No route matches this location."
                );
            }

            RouteMatch match = optionalMatch.get();
            Route route = match.route();

            if (route.redirect() != null) {
                return navigate(route.redirect(), user, replace);
            }

            if (!authorization.authorize(route, user)) {
                if (user == null || !user.authenticated()) {
                    return new NavigationResult(
                        NavigationStatus.REDIRECT,
                        "/login",
                        List.of("Login"),
                        Map.of("returnTo", pathname),
                        "Authentication required."
                    );
                }

                return new NavigationResult(
                    NavigationStatus.FORBIDDEN,
                    pathname,
                    List.of("Forbidden"),
                    match.parameters(),
                    "Insufficient role permissions."
                );
            }

            if (replace && historyIndex >= 0) {
                history.set(historyIndex, url);
            } else {
                while (history.size() > historyIndex + 1) {
                    history.remove(history.size() - 1);
                }

                history.add(url);
                historyIndex++;
            }

            return new NavigationResult(
                NavigationStatus.SUCCESS,
                pathname,
                match.componentChain(),
                match.parameters(),
                "Navigation completed."
            );
        }

        Optional<String> back() {
            if (historyIndex <= 0) {
                return Optional.empty();
            }

            historyIndex--;
            return Optional.of(history.get(historyIndex));
        }

        Optional<String> forward() {
            if (historyIndex + 1 >= history.size()) {
                return Optional.empty();
            }

            historyIndex++;
            return Optional.of(history.get(historyIndex));
        }

        List<String> history() {
            return List.copyOf(history);
        }
    }

    static RouteRegistry createRegistry() {
        Route application = new Route(
            "/",
            "ApplicationLayout",
            List.of(
                new Route(
                    "/", "Home", List.of(),
                    AccessPolicy.PUBLIC, Set.of(), null
                ),
                new Route(
                    "/about", "About", List.of(),
                    AccessPolicy.PUBLIC, Set.of(), null
                ),
                new Route(
                    "/products",
                    "ProductsLayout",
                    List.of(
                        new Route(
                            "/products", "ProductList", List.of(),
                            AccessPolicy.PUBLIC, Set.of(), null
                        ),
                        new Route(
                            "/products/:productId",
                            "ProductDetails",
                            List.of(),
                            AccessPolicy.PUBLIC, Set.of(), null
                        )
                    ),
                    AccessPolicy.PUBLIC, Set.of(), null
                ),
                new Route(
                    "/users",
                    "UsersLayout",
                    List.of(
                        new Route(
                            "/users/:userId",
                            "UserProfile",
                            List.of(),
                            AccessPolicy.PUBLIC, Set.of(), null
                        )
                    ),
                    AccessPolicy.PUBLIC, Set.of(), null
                ),
                new Route(
                    "/dashboard",
                    "Dashboard",
                    List.of(),
                    AccessPolicy.ROLE_RESTRICTED,
                    EnumSet.of(Role.USER, Role.ADMIN),
                    null
                ),
                new Route(
                    "/admin",
                    "AdminPanel",
                    List.of(),
                    AccessPolicy.ROLE_RESTRICTED,
                    EnumSet.of(Role.ADMIN),
                    null
                ),
                new Route(
                    "/login", "Login", List.of(),
                    AccessPolicy.PUBLIC, Set.of(), null
                )
            ),
            AccessPolicy.PUBLIC,
            Set.of(),
            null
        );

        return new RouteRegistry(List.of(application));
    }

    static void display(NavigationResult result) {
        System.out.println("\nStatus: " + result.status());
        System.out.println("Path: " + result.pathname());
        System.out.println(
            "Components: " + String.join(" -> ", result.components())
        );
        System.out.println("Parameters: " + result.parameters());
        System.out.println("Message: " + result.message());
    }

    public static void main(String[] args) {
        try {
            RouteRegistry registry = createRegistry();

            AuthorizationService authorization =
                new AuthorizationService();

            NavigationService navigation = new NavigationService(
                registry,
                authorization
            );

            User user = new User(
                101, "alice", Role.USER, true
            );

            User admin = new User(
                102, "root", Role.ADMIN, true
            );

            System.out.println("REACT ROUTING ENTERPRISE MODEL");

            display(navigation.navigate("/", null, false));

            display(navigation.navigate(
                "/products", null, false
            ));

            display(navigation.navigate(
                "/products/501", null, false
            ));

            display(navigation.navigate(
                "/users/101?tab=activity", user, false
            ));

            display(navigation.navigate(
                "/dashboard", null, false
            ));

            display(navigation.navigate(
                "/dashboard", user, false
            ));

            display(navigation.navigate(
                "/admin", user, false
            ));

            display(navigation.navigate(
                "/admin", admin, false
            ));

            display(navigation.navigate(
                "/unknown", user, false
            ));

            System.out.println("\nNAVIGATION HISTORY");
            navigation.history().forEach(System.out::println);

            System.out.println(
                "Back: " + navigation.back().orElse("Unavailable")
            );

            System.out.println(
                "Forward: " + navigation.forward().orElse("Unavailable")
            );

        } catch (Exception exception) {
            System.err.println(
                "Routing error: " + exception.getMessage()
            );
            System.exit(1);
        }
    }
}
