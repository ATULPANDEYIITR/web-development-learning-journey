#include <algorithm>
#include <iostream>
#include <map>
#include <memory>
#include <optional>
#include <regex>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

using namespace std;

enum class Role {
    Guest,
    User,
    Admin
};

enum class RouteStatus {
    Success,
    NotFound,
    Redirect,
    Forbidden
};

string roleName(Role role) {
    switch (role) {
        case Role::Guest: return "Guest";
        case Role::User: return "User";
        case Role::Admin: return "Admin";
    }
    return "Unknown";
}

string statusName(RouteStatus status) {
    switch (status) {
        case RouteStatus::Success: return "SUCCESS";
        case RouteStatus::NotFound: return "NOT_FOUND";
        case RouteStatus::Redirect: return "REDIRECT";
        case RouteStatus::Forbidden: return "FORBIDDEN";
    }
    return "UNKNOWN";
}

struct User {
    int id;
    string username;
    Role role;
    bool authenticated;
};

struct Route {
    string path;
    string component;
    vector<Route> children;
    bool protectedRoute = false;
    set<Role> allowedRoles;
    optional<string> redirect;
};

struct RouteMatch {
    const Route* route = nullptr;
    map<string, string> params;
    vector<string> components;
};

struct NavigationResult {
    RouteStatus status;
    string pathname;
    vector<string> components;
    map<string, string> params;
    string message;
};

class Router {
private:
    vector<Route> routes;

    static string normalize(const string& path) {
        if (path.empty() || path.front() != '/') {
            throw invalid_argument("Path must begin with /.");
        }

        string result;
        bool previousSlash = false;

        for (char ch : path) {
            if (ch == '/') {
                if (!previousSlash) {
                    result += ch;
                }
                previousSlash = true;
            } else {
                result += ch;
                previousSlash = false;
            }
        }

        if (result.size() > 1 && result.back() == '/') {
            result.pop_back();
        }

        return result;
    }

    static bool matchPattern(
        const string& pattern,
        const string& pathname,
        map<string, string>& params
    ) {
        vector<string> patternParts;
        vector<string> pathParts;

        stringstream patternStream(normalize(pattern));
        stringstream pathStream(normalize(pathname));

        string part;

        while (getline(patternStream, part, '/')) {
            if (!part.empty()) patternParts.push_back(part);
        }

        while (getline(pathStream, part, '/')) {
            if (!part.empty()) pathParts.push_back(part);
        }

        if (patternParts.size() != pathParts.size()) {
            return false;
        }

        map<string, string> temporary;

        for (size_t i = 0; i < patternParts.size(); ++i) {
            const string& expected = patternParts[i];
            const string& actual = pathParts[i];

            if (!expected.empty() && expected.front() == ':') {
                string name = expected.substr(1);

                if (name.empty() || temporary.count(name)) {
                    return false;
                }

                temporary[name] = actual;
            } else if (expected == "*") {
                temporary["wildcard"] = actual;
            } else if (expected != actual) {
                return false;
            }
        }

        params = move(temporary);
        return true;
    }

    optional<RouteMatch> resolveRoutes(
        const vector<Route>& candidates,
        const string& pathname,
        vector<string> parents = {},
        map<string, string> parentParams = {}
    ) const {

        for (const Route& route : candidates) {
            map<string, string> localParams;

            if (!matchPattern(route.path, pathname, localParams)) {
                continue;
            }

            for (const auto& item : localParams) {
                parentParams[item.first] = item.second;
            }

            vector<string> components = parents;
            components.push_back(route.component);

            if (!route.children.empty()) {
                auto nested = resolveRoutes(
                    route.children,
                    pathname,
                    components,
                    parentParams
                );

                if (nested) return nested;
            }

            return RouteMatch{
                &route,
                parentParams,
                components
            };
        }

        return nullopt;
    }

    static void validateRoutes(const vector<Route>& candidates) {
        set<string> seen;

        for (const auto& route : candidates) {
            if (!seen.insert(route.path).second) {
                throw invalid_argument("Duplicate sibling route.");
            }

            normalize(route.path);

            if (route.component.empty()) {
                throw invalid_argument("Component name cannot be empty.");
            }

            if (route.protectedRoute && route.allowedRoles.empty()) {
                throw invalid_argument(
                    "Protected routes require allowed roles."
                );
            }

            validateRoutes(route.children);
        }
    }

public:
    explicit Router(vector<Route> definitions)
        : routes(move(definitions)) {
        validateRoutes(routes);
    }

    NavigationResult navigate(
        const string& pathname,
        const optional<User>& user = nullopt
    ) const {

        string normalized = normalize(pathname);
        auto match = resolveRoutes(routes, normalized);

        if (!match) {
            return {
                RouteStatus::NotFound,
                normalized,
                {"NotFound"},
                {},
                "No route matches the requested path."
            };
        }

        const Route& route = *match->route;

        if (route.redirect) {
            return {
                RouteStatus::Redirect,
                *route.redirect,
                {"Redirect"},
                {},
                "Route redirects to another location."
            };
        }

        if (route.protectedRoute) {
            if (!user || !user->authenticated) {
                return {
                    RouteStatus::Redirect,
                    "/login",
                    {"Login"},
                    {},
                    "Authentication is required."
                };
            }

            if (!route.allowedRoles.count(user->role)) {
                return {
                    RouteStatus::Forbidden,
                    normalized,
                    {"Forbidden"},
                    match->params,
                    "The current role cannot access this route."
                };
            }
        }

        return {
            RouteStatus::Success,
            normalized,
            match->components,
            match->params,
            "Route resolved successfully."
        };
    }
};

class NavigationHistory {
private:
    vector<string> entries;
    int currentIndex = -1;

public:
    void push(const string& path) {
        entries.resize(currentIndex + 1);
        entries.push_back(path);
        currentIndex = static_cast<int>(entries.size()) - 1;
    }

    void replace(const string& path) {
        if (currentIndex < 0) {
            push(path);
        } else {
            entries[currentIndex] = path;
        }
    }

    optional<string> back() {
        if (currentIndex <= 0) return nullopt;
        return entries[--currentIndex];
    }

    optional<string> forward() {
        if (currentIndex + 1 >= static_cast<int>(entries.size())) {
            return nullopt;
        }

        return entries[++currentIndex];
    }

    void print() const {
        for (size_t i = 0; i < entries.size(); ++i) {
            cout << (static_cast<int>(i) == currentIndex ? " -> " : "    ")
                 << entries[i] << '\n';
        }
    }
};

Router createRouter() {
    Route application{
        "/",
        "ApplicationLayout",
        {
            Route{"/", "Home"},
            Route{"/about", "About"},
            Route{
                "/products",
                "ProductsLayout",
                {
                    Route{"/products", "ProductList"},
                    Route{"/products/:productId", "ProductDetails"}
                }
            },
            Route{
                "/users",
                "UsersLayout",
                {
                    Route{"/users/:userId", "UserProfile"}
                }
            },
            Route{
                "/dashboard",
                "Dashboard",
                {},
                true,
                {Role::User, Role::Admin}
            },
            Route{
                "/admin",
                "AdminPanel",
                {},
                true,
                {Role::Admin}
            },
            Route{"/login", "Login"}
        }
    };

    return Router({application});
}

void printResult(const NavigationResult& result) {
    cout << "\nPath: " << result.pathname << '\n';
    cout << "Status: " << statusName(result.status) << '\n';
    cout << "Components: ";

    for (size_t i = 0; i < result.components.size(); ++i) {
        if (i) cout << " -> ";
        cout << result.components[i];
    }

    cout << "\nParameters:\n";

    for (const auto& [key, value] : result.params) {
        cout << "  " << key << " = " << value << '\n';
    }

    cout << "Message: " << result.message << '\n';
}

int main() {
    try {
        Router router = createRouter();

        User regularUser{
            101,
            "alice",
            Role::User,
            true
        };

        User administrator{
            102,
            "root",
            Role::Admin,
            true
        };

        cout << "REPOSITORY ROUTING ENGINE\n";
        cout << "=========================\n";

        printResult(router.navigate("/"));
        printResult(router.navigate("/products"));
        printResult(router.navigate("/products/501"));
        printResult(router.navigate("/users/25"));
        printResult(router.navigate("/dashboard"));
        printResult(router.navigate("/dashboard", regularUser));
        printResult(router.navigate("/admin", regularUser));
        printResult(router.navigate("/admin", administrator));
        printResult(router.navigate("/unknown"));

        NavigationHistory history;

        history.push("/");
        history.push("/products");
        history.push("/products/501");

        cout << "\nNAVIGATION HISTORY\n";
        history.print();

        cout << "\nBack: "
             << history.back().value_or("No previous route")
             << '\n';

        cout << "Forward: "
             << history.forward().value_or("No next route")
             << '\n';

    } catch (const exception& error) {
        cerr << "Routing failure: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
