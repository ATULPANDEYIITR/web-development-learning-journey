#include <algorithm>
#include <iostream>
#include <map>
#include <memory>
#include <optional>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;

/*
 * Next.js Fundamentals
 *
 * C++17 repository-independent model of:
 * - File-system routing
 * - Static and dynamic route matching
 * - Nested layouts
 * - Server/client component boundaries
 * - Route access policies
 * - Rendering composition
 * - Merge-free route registration and validation
 */

enum class SegmentType {
    Static,
    Dynamic,
    CatchAll
};

enum class ComponentType {
    Server,
    Client
};

enum class RenderStatus {
    Success,
    NotFound,
    Forbidden,
    InvalidBoundary
};

struct Segment {
    string name;
    SegmentType type;
};

struct RouteMatch {
    string pattern;
    string page;
    map<string, string> parameters;
    vector<string> layouts;
    bool requiresAuthentication = false;
};

struct Route {
    string pattern;
    string page;
    vector<Segment> segments;
    vector<string> layouts;
    bool requiresAuthentication = false;
};

class RouteException : public runtime_error {
public:
    explicit RouteException(const string& message)
        : runtime_error(message) {}
};

class Router {
private:
    vector<Route> routes;

    static vector<string> split(const string& value, char delimiter) {
        vector<string> result;
        string item;
        stringstream stream(value);

        while (getline(stream, item, delimiter)) {
            if (!item.empty()) result.push_back(item);
        }

        return result;
    }

    static vector<Segment> parsePattern(const string& pattern) {
        if (pattern.empty() || pattern[0] != '/') {
            throw RouteException("Route must begin with '/'");
        }

        vector<Segment> result;

        if (pattern == "/") return result;

        for (const string& part : split(pattern.substr(1), '/')) {
            if (part.size() >= 5 &&
                part.substr(0, 4) == "[..." &&
                part.back() == ']') {
                result.push_back({
                    part.substr(4, part.size() - 5),
                    SegmentType::CatchAll
                });
            } else if (
                part.size() >= 3 &&
                part.front() == '[' &&
                part.back() == ']'
            ) {
                result.push_back({
                    part.substr(1, part.size() - 2),
                    SegmentType::Dynamic
                });
            } else {
                if (part.find('[') != string::npos ||
                    part.find(']') != string::npos) {
                    throw RouteException("Malformed route segment");
                }

                result.push_back({part, SegmentType::Static});
            }
        }

        if (count_if(
            result.begin(),
            result.end(),
            [](const Segment& s) {
                return s.type == SegmentType::CatchAll;
            }) > 1) {
            throw RouteException("Only one catch-all segment is supported");
        }

        for (size_t i = 0; i + 1 < result.size(); ++i) {
            if (result[i].type == SegmentType::CatchAll) {
                throw RouteException("Catch-all must be the final segment");
            }
        }

        return result;
    }

    static vector<string> normalize(const string& path) {
        if (path.empty() || path.front() != '/') {
            throw RouteException("Invalid relative route path");
        }

        if (path.find('\\') != string::npos ||
            path.find('\0') != string::npos ||
            path.find("://") != string::npos) {
            throw RouteException("Unsafe route path");
        }

        vector<string> parts = split(path.substr(1), '/');

        for (const string& part : parts) {
            if (part == "." || part == "..") {
                throw RouteException("Path traversal rejected");
            }
        }

        return parts;
    }

public:
    void registerRoute(
        const string& pattern,
        const string& page,
        const vector<string>& layouts,
        bool requiresAuthentication = false
    ) {
        for (const auto& route : routes) {
            if (route.pattern == pattern) {
                throw RouteException("Duplicate route: " + pattern);
            }
        }

        Route route;
        route.pattern = pattern;
        route.page = page;
        route.layouts = layouts;
        route.requiresAuthentication = requiresAuthentication;
        route.segments = parsePattern(pattern);

        routes.push_back(move(route));

        sort(routes.begin(), routes.end(),
            [](const Route& a, const Route& b) {
                auto score = [](const Route& route) {
                    int staticCount = 0;

                    for (const auto& segment : route.segments) {
                        if (segment.type == SegmentType::Static) {
                            ++staticCount;
                        }
                    }

                    return pair<int, int>(
                        staticCount,
                        static_cast<int>(route.segments.size())
                    );
                };

                return score(a) > score(b);
            }
        );
    }

    optional<RouteMatch> resolve(const string& path) const {
        vector<string> parts = normalize(path);

        for (const Route& route : routes) {
            const auto& segments = route.segments;

            bool catchAll =
                !segments.empty() &&
                segments.back().type == SegmentType::CatchAll;

            if (catchAll) {
                if (parts.size() < segments.size()) continue;
            } else if (parts.size() != segments.size()) {
                continue;
            }

            RouteMatch match;
            match.pattern = route.pattern;
            match.page = route.page;
            match.layouts = route.layouts;
            match.requiresAuthentication =
                route.requiresAuthentication;

            bool valid = true;

            for (size_t i = 0; i < segments.size(); ++i) {
                const Segment& segment = segments[i];

                if (segment.type == SegmentType::Static) {
                    if (segment.name != parts[i]) {
                        valid = false;
                        break;
                    }
                } else if (segment.type == SegmentType::Dynamic) {
                    match.parameters[segment.name] = parts[i];
                } else {
                    string value;

                    for (size_t j = i; j < parts.size(); ++j) {
                        if (!value.empty()) value += "/";
                        value += parts[j];
                    }

                    if (value.empty()) {
                        valid = false;
                        break;
                    }

                    match.parameters[segment.name] = value;
                }
            }

            if (valid) return match;
        }

        return nullopt;
    }

    size_t size() const {
        return routes.size();
    }
};

struct Component {
    string name;
    ComponentType type;
    bool usesState = false;
    bool usesEffects = false;
    bool usesBrowserAPI = false;
    bool hasEventHandlers = false;
    vector<string> imports;
};

class ComponentRegistry {
private:
    map<string, Component> components;

public:
    void add(const Component& component) {
        if (components.count(component.name)) {
            throw RouteException("Duplicate component");
        }

        bool requiresClient =
            component.usesState ||
            component.usesEffects ||
            component.usesBrowserAPI ||
            component.hasEventHandlers;

        if (requiresClient && component.type == ComponentType::Server) {
            throw RouteException(
                "Interactive functionality requires a Client Component: " +
                component.name
            );
        }

        components.emplace(component.name, component);
    }

    set<string> clientDependencyGraph(const string& entry) const {
        set<string> visited;
        set<string> active;

        function<void(const string&)> visit =
            [&](const string& name) {
                if (active.count(name)) {
                    throw RouteException("Circular module dependency");
                }

                if (visited.count(name)) return;

                auto it = components.find(name);

                if (it == components.end()) {
                    throw RouteException(
                        "Missing component dependency: " + name
                    );
                }

                active.insert(name);
                visited.insert(name);

                for (const string& dependency : it->second.imports) {
                    visit(dependency);
                }

                active.erase(name);
            };

        visit(entry);
        return visited;
    }
};

class LayoutRenderer {
public:
    static string compose(
        const RouteMatch& route,
        const string& pageContent
    ) {
        string result = pageContent;

        for (auto it = route.layouts.rbegin();
             it != route.layouts.rend(); ++it) {
            result = *it + "(" + result + ")";
        }

        return result;
    }
};

class RequestContext {
public:
    bool authenticated = false;
    set<string> roles;
};

class RenderingEngine {
private:
    const Router& router;

public:
    explicit RenderingEngine(const Router& value) : router(value) {}

    pair<RenderStatus, string> render(
        const string& path,
        const RequestContext& context
    ) const {
        try {
            auto result = router.resolve(path);

            if (!result.has_value()) {
                return {RenderStatus::NotFound, "404 Not Found"};
            }

            const RouteMatch& route = result.value();

            if (route.requiresAuthentication &&
                !context.authenticated) {
                return {
                    RenderStatus::Forbidden,
                    "Authentication required"
                };
            }

            string content = route.page;

            for (const auto& [key, value] : route.parameters) {
                content += " [" + key + "=" + value + "]";
            }

            return {
                RenderStatus::Success,
                LayoutRenderer::compose(route, content)
            };
        } catch (const exception& error) {
            return {RenderStatus::InvalidBoundary, error.what()};
        }
    }
};

int main() {
    try {
        Router router;

        router.registerRoute("/", "HomePage", {"RootLayout"});
        router.registerRoute("/about", "AboutPage", {"RootLayout"});
        router.registerRoute(
            "/blog",
            "BlogIndex",
            {"RootLayout", "BlogLayout"}
        );
        router.registerRoute(
            "/blog/[slug]",
            "BlogPost",
            {"RootLayout", "BlogLayout"}
        );
        router.registerRoute(
            "/dashboard",
            "DashboardPage",
            {"RootLayout", "DashboardLayout"},
            true
        );
        router.registerRoute(
            "/docs/[...slug]",
            "DocumentationPage",
            {"RootLayout"}
        );

        cout << "NEXT.JS ROUTING ENGINE\n";
        cout << "Registered routes: " << router.size() << "\n\n";

        vector<string> paths = {
            "/",
            "/about",
            "/blog",
            "/blog/architecture",
            "/dashboard",
            "/docs/app/routing/dynamic"
        };

        for (const string& path : paths) {
            auto match = router.resolve(path);

            if (match) {
                cout << path << " -> " << match->page << "\n";

                for (const auto& [key, value] : match->parameters) {
                    cout << "  " << key << " = " << value << "\n";
                }
            }
        }

        cout << "\nCOMPONENT BOUNDARY VALIDATION\n";

        ComponentRegistry registry;

        registry.add({
            "Logo",
            ComponentType::Server
        });

        registry.add({
            "SearchBox",
            ComponentType::Client,
            true,
            false,
            false,
            true
        });

        registry.add({
            "Navigation",
            ComponentType::Server,
            false,
            false,
            false,
            false,
            {"Logo", "SearchBox"}
        });

        auto dependencies =
            registry.clientDependencyGraph("Navigation");

        cout << "Navigation module graph:\n";

        for (const auto& name : dependencies) {
            cout << "  " << name << "\n";
        }

        try {
            registry.add({
                "InvalidCounter",
                ComponentType::Server,
                true
            });
        } catch (const exception& error) {
            cout << "Rejected: " << error.what() << "\n";
        }

        cout << "\nRENDERING AND ACCESS CONTROL\n";

        RenderingEngine engine(router);
        RequestContext anonymous;

        auto home = engine.render("/", anonymous);
        cout << "Home: " << home.second << "\n";

        auto dashboard = engine.render("/dashboard", anonymous);
        cout << "Dashboard: " << dashboard.second << "\n";

        RequestContext authenticated;
        authenticated.authenticated = true;
        authenticated.roles.insert("developer");

        auto authorizedDashboard =
            engine.render("/dashboard", authenticated);

        cout << "Authorized: "
             << authorizedDashboard.second << "\n";

        cout << "\nFAILURE TESTS\n";

        for (const string& invalid : {
            "/unknown",
            "/../private",
            "/blog/../admin"
        }) {
            auto result = engine.render(invalid, anonymous);

            cout << invalid << " -> "
                 << result.second << "\n";
        }

        cout << "\nASSERTIONS\n";

        auto blog = router.resolve("/blog/nextjs");
        if (!blog || blog->parameters.at("slug") != "nextjs") {
            throw runtime_error("Dynamic route test failed");
        }

        auto docs = router.resolve("/docs/app/router");
        if (!docs ||
            docs->parameters.at("slug") != "app/router") {
            throw runtime_error("Catch-all route test failed");
        }

        if (router.resolve("/missing")) {
            throw runtime_error("Unknown route was incorrectly resolved");
        }

        if (dashboard.first != RenderStatus::Forbidden) {
            throw runtime_error("Access control test failed");
        }

        cout << "All tests passed.\n";

    } catch (const exception& error) {
        cerr << "Application error: " << error.what() << "\n";
        return 1;
    }

    return 0;
}
