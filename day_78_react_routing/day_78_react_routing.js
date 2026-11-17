/*
 * React Routing: SPA navigation, nested routes, parameters,
 * authentication, authorization, redirects, and navigation history.
 *
 * Runtime: Node.js 18+
 * No third-party dependencies.
 */

"use strict";

const { EventEmitter } = require("node:events");

class RoutingError extends Error {}
class InvalidRouteError extends RoutingError {}
class AuthenticationError extends RoutingError {}
class AuthorizationError extends RoutingError {}

const Role = Object.freeze({
    GUEST: "guest",
    USER: "user",
    ADMIN: "admin"
});

class RouteDefinition {
    constructor({
        path,
        component,
        children = [],
        protectedRoute = false,
        allowedRoles = [],
        redirect = null
    }) {
        this.path = normalizePath(path);
        this.component = component;
        this.children = children;
        this.protectedRoute = protectedRoute;
        this.allowedRoles = new Set(allowedRoles);
        this.redirect = redirect;

        if (!component || typeof component !== "string") {
            throw new InvalidRouteError("A route requires a component name.");
        }

        if (protectedRoute && allowedRoles.length === 0) {
            throw new InvalidRouteError(
                "Protected routes must define allowed roles."
            );
        }
    }
}

function normalizePath(path) {
    if (typeof path !== "string" || !path.startsWith("/")) {
        throw new InvalidRouteError("Invalid route path.");
    }

    const normalized = path.replace(/\/+/g, "/");

    return normalized.length > 1
        ? normalized.replace(/\/+$/, "")
        : "/";
}

function compilePattern(pattern) {
    const normalized = normalizePath(pattern);
    const parameters = [];

    const expression = normalized === "/"
        ? "^/$"
        : "^" + normalized.split("/").map(segment => {
            if (segment.startsWith(":")) {
                const name = segment.slice(1);

                if (!/^[A-Za-z_][A-Za-z0-9_]*$/.test(name)) {
                    throw new InvalidRouteError("Invalid route parameter.");
                }

                if (parameters.includes(name)) {
                    throw new InvalidRouteError("Duplicate route parameter.");
                }

                parameters.push(name);
                return "([^/]+)";
            }

            if (segment === "*") {
                parameters.push("wildcard");
                return "(.*)";
            }

            return segment.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
        }).join("/") + "$";

    return {
        regex: new RegExp(expression),
        parameters
    };
}

class RouteMatcher {
    constructor(routes) {
        this.routes = routes;
        this.validateRoutes(routes);
    }

    validateRoutes(routes) {
        const paths = new Set();

        for (const route of routes) {
            if (paths.has(route.path)) {
                throw new InvalidRouteError(
                    `Duplicate route: ${route.path}`
                );
            }

            paths.add(route.path);
            compilePattern(route.path);
            this.validateRoutes(route.children);
        }
    }

    match(pathname, routes = this.routes, parentComponents = [], parentParams = {}) {
        for (const route of routes) {
            const { regex, parameters } = compilePattern(route.path);
            const match = pathname.match(regex);

            if (!match) {
                continue;
            }

            const params = { ...parentParams };

            parameters.forEach((name, index) => {
                params[name] = decodeURIComponent(match[index + 1]);
            });

            const components = [...parentComponents, route.component];

            if (route.children.length > 0) {
                const nested = this.match(
                    pathname,
                    route.children,
                    components,
                    params
                );

                if (nested) {
                    return nested;
                }
            }

            return {
                route,
                params,
                components
            };
        }

        return null;
    }
}

class AuthorizationService {
    constructor() {
        this.permissionCache = new Map();
    }

    canAccess(user, allowedRoles) {
        if (!user || user.authenticated !== true) {
            return false;
        }

        const cacheKey = `${user.id}:${user.role}:${allowedRoles.join(",")}`;

        if (this.permissionCache.has(cacheKey)) {
            return this.permissionCache.get(cacheKey);
        }

        const result = allowedRoles.includes(user.role);
        this.permissionCache.set(cacheKey, result);

        return result;
    }

    clearCache() {
        this.permissionCache.clear();
    }
}

class ApplicationRouter extends EventEmitter {
    constructor(routes, authorization = new AuthorizationService()) {
        super();
        this.matcher = new RouteMatcher(routes);
        this.authorization = authorization;
        this.currentUser = null;
        this.history = [];
        this.historyIndex = -1;
        this.transitionInProgress = false;
    }

    setUser(user) {
        this.currentUser = user;
        this.authorization.clearCache();
        this.emit("authenticationChanged", user);
    }

    async navigate(url, options = {}) {
        if (this.transitionInProgress) {
            throw new RoutingError("Navigation already in progress.");
        }

        this.transitionInProgress = true;

        try {
            const parsed = new URL(url, "http://localhost");
            const pathname = normalizePath(parsed.pathname);

            const match = this.matcher.match(pathname);

            if (!match) {
                return this.finish({
                    status: 404,
                    pathname,
                    components: ["NotFound"],
                    params: {},
                    query: Object.fromEntries(parsed.searchParams),
                    message: "Route not found."
                });
            }

            const route = match.route;

            if (route.redirect) {
                return this.navigate(route.redirect, options);
            }

            if (route.protectedRoute) {
                if (!this.currentUser ||
                    this.currentUser.authenticated !== true) {

                    return this.finish({
                        status: 302,
                        pathname: "/login",
                        components: ["Login"],
                        params: {},
                        query: {
                            returnTo: pathname
                        },
                        message: "Authentication required."
                    });
                }

                if (!this.authorization.canAccess(
                    this.currentUser,
                    [...route.allowedRoles]
                )) {
                    return this.finish({
                        status: 403,
                        pathname,
                        components: ["Forbidden"],
                        params: match.params,
                        query: Object.fromEntries(parsed.searchParams),
                        message: "Insufficient permissions."
                    });
                }
            }

            const result = {
                status: 200,
                pathname,
                components: match.components,
                params: match.params,
                query: Object.fromEntries(parsed.searchParams),
                message: "Navigation successful."
            };

            if (options.replace && this.historyIndex >= 0) {
                this.history[this.historyIndex] = url;
            } else if (options.recordHistory !== false) {
                this.history = this.history.slice(
                    0,
                    this.historyIndex + 1
                );
                this.history.push(url);
                this.historyIndex++;
            }

            return this.finish(result);

        } finally {
            this.transitionInProgress = false;
        }
    }

    finish(result) {
        this.emit("navigation", result);
        return result;
    }

    async back() {
        if (this.historyIndex <= 0) {
            return null;
        }

        this.historyIndex--;
        return this.navigate(this.history[this.historyIndex], {
            recordHistory: false
        });
    }

    async forward() {
        if (this.historyIndex >= this.history.length - 1) {
            return null;
        }

        this.historyIndex++;
        return this.navigate(this.history[this.historyIndex], {
            recordHistory: false
        });
    }
}

function createRoutes() {
    return [
        new RouteDefinition({
            path: "/",
            component: "AppLayout",
            children: [
                new RouteDefinition({
                    path: "/",
                    component: "Home"
                }),
                new RouteDefinition({
                    path: "/about",
                    component: "About"
                }),
                new RouteDefinition({
                    path: "/products",
                    component: "ProductsLayout",
                    children: [
                        new RouteDefinition({
                            path: "/products",
                            component: "ProductList"
                        }),
                        new RouteDefinition({
                            path: "/products/:productId",
                            component: "ProductDetails"
                        })
                    ]
                }),
                new RouteDefinition({
                    path: "/users",
                    component: "UsersLayout",
                    children: [
                        new RouteDefinition({
                            path: "/users/:userId",
                            component: "UserProfile"
                        })
                    ]
                }),
                new RouteDefinition({
                    path: "/dashboard",
                    component: "Dashboard",
                    protectedRoute: true,
                    allowedRoles: [Role.USER, Role.ADMIN]
                }),
                new RouteDefinition({
                    path: "/admin",
                    component: "AdminPanel",
                    protectedRoute: true,
                    allowedRoles: [Role.ADMIN]
                }),
                new RouteDefinition({
                    path: "/login",
                    component: "Login"
                })
            ]
        })
    ];
}

async function runDemo() {
    const router = new ApplicationRouter(createRoutes());

    router.on("navigation", result => {
        console.log(
            `[NAVIGATION ${result.status}] ${result.pathname}`
        );
    });

    router.on("authenticationChanged", user => {
        console.log(
            "Authentication updated:",
            user ? user.username : "Anonymous"
        );
    });

    const scenarios = [
        "/",
        "/products",
        "/products/501",
        "/users/25?tab=activity",
        "/dashboard"
    ];

    for (const path of scenarios) {
        const result = await router.navigate(path);
        console.log(JSON.stringify(result, null, 2));
    }

    router.setUser({
        id: 10,
        username: "alice",
        role: Role.USER,
        authenticated: true
    });

    console.log(
        "\nUser dashboard:",
        await router.navigate("/dashboard")
    );

    console.log(
        "\nUser attempting admin:",
        await router.navigate("/admin")
    );

    router.setUser({
        id: 1,
        username: "root",
        role: Role.ADMIN,
        authenticated: true
    });

    console.log(
        "\nAdmin dashboard:",
        await router.navigate("/admin")
    );

    console.log(
        "\nInvalid route:",
        await router.navigate("/unknown")
    );

    console.log("\nNavigation history:", router.history);
}

runDemo().catch(error => {
    console.error("Application routing failure:", error.message);
    process.exitCode = 1;
});
