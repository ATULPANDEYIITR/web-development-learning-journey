#include <algorithm>
#include <chrono>
#include <cctype>
#include <exception>
#include <iostream>
#include <map>
#include <optional>
#include <regex>
#include <set>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

/*
 * Next.js Full-Stack Architecture
 *
 * C++17 implementation of a server request-processing engine.
 *
 * Models:
 * - Environment configuration
 * - Middleware
 * - Route handlers
 * - Server actions
 * - Authentication and authorization
 * - Request validation
 * - Response generation
 * - Cache invalidation
 *
 * Compile:
 * g++ -std=c++17 -O2 -Wall -Wextra -pedantic nextjs_fullstack.cpp -o nextjs_fullstack
 */

namespace nextjs {

enum class HttpMethod {
    GET,
    POST,
    PATCH,
    DELETE
};

enum class UserRole {
    USER,
    ADMIN
};

struct EnvironmentConfig {
    std::string databaseUrl;
    std::string sessionSecret;
    std::string appEnvironment;
    std::string publicAppName;
};

class ConfigurationError : public std::runtime_error {
public:
    using std::runtime_error::runtime_error;
};

class ValidationError : public std::runtime_error {
public:
    using std::runtime_error::runtime_error;
};

class AuthorizationError : public std::runtime_error {
public:
    using std::runtime_error::runtime_error;
};

// -----------------------------------------------------
// Environment Configuration
// -----------------------------------------------------

class EnvironmentManager {
public:
    explicit EnvironmentManager(
        std::map<std::string, std::string> values
    ) : values_(std::move(values)) {}

    EnvironmentConfig load() const {
        const std::vector<std::string> required = {
            "DATABASE_URL",
            "SESSION_SECRET",
            "APP_ENV"
        };

        for (const auto& key : required) {
            if (!values_.count(key) || values_.at(key).empty()) {
                throw ConfigurationError(
                    "Missing environment variable: " + key
                );
            }
        }

        const auto& secret = values_.at("SESSION_SECRET");

        if (secret.size() < 32) {
            throw ConfigurationError(
                "SESSION_SECRET must contain at least 32 characters"
            );
        }

        const std::string& database =
            values_.at("DATABASE_URL");

        if (
            database.rfind("postgresql://", 0) != 0 &&
            database.rfind("postgres://", 0) != 0
        ) {
            throw ConfigurationError(
                "DATABASE_URL must use PostgreSQL"
            );
        }

        const std::string& environment =
            values_.at("APP_ENV");

        if (
            environment != "development" &&
            environment != "production" &&
            environment != "test"
        ) {
            throw ConfigurationError(
                "Unsupported application environment"
            );
        }

        auto publicName = values_.find("NEXT_PUBLIC_APP_NAME");

        return EnvironmentConfig{
            database,
            secret,
            environment,
            publicName == values_.end()
                ? "Application"
                : publicName->second
        };
    }

private:
    std::map<std::string, std::string> values_;
};

// -----------------------------------------------------
// Domain Models
// -----------------------------------------------------

struct User {
    int id;
    std::string username;
    UserRole role;
    bool active = true;
};

struct Task {
    int id;
    int userId;
    std::string title;
    bool completed = false;
};

struct Request {
    HttpMethod method;
    std::string path;
    std::optional<int> authenticatedUser;
    std::map<std::string, std::string> body;
    std::string requestId;
};

struct Response {
    int status;
    std::string message;
    std::vector<Task> tasks;
};

std::string methodName(HttpMethod method) {
    switch (method) {
        case HttpMethod::GET: return "GET";
        case HttpMethod::POST: return "POST";
        case HttpMethod::PATCH: return "PATCH";
        case HttpMethod::DELETE: return "DELETE";
    }

    return "UNKNOWN";
}

// -----------------------------------------------------
// Input Validation
// -----------------------------------------------------

std::string validateTitle(const std::string& input) {
    auto begin = input.find_first_not_of(" \t\n\r");

    if (begin == std::string::npos) {
        throw ValidationError("Title cannot be empty");
    }

    auto end = input.find_last_not_of(" \t\n\r");

    std::string title = input.substr(
        begin,
        end - begin + 1
    );

    if (title.size() > 120) {
        throw ValidationError("Title exceeds 120 characters");
    }

    for (unsigned char c : title) {
        if (c < 32 && c != '\t') {
            throw ValidationError(
                "Title contains invalid control characters"
            );
        }
    }

    return title;
}

int validatePositiveId(const std::string& value) {
    if (value.empty()) {
        throw ValidationError("ID cannot be empty");
    }

    int result = 0;

    for (char c : value) {
        if (!std::isdigit(static_cast<unsigned char>(c))) {
            throw ValidationError("Invalid numeric ID");
        }

        if (result > (2147483647 - (c - '0')) / 10) {
            throw ValidationError("ID exceeds integer range");
        }

        result = result * 10 + (c - '0');
    }

    if (result <= 0) {
        throw ValidationError("ID must be positive");
    }

    return result;
}

// -----------------------------------------------------
// Task Repository
// -----------------------------------------------------

class TaskRepository {
public:
    int create(int userId, const std::string& title) {
        if (!users_.count(userId)) {
            throw std::invalid_argument("Unknown user");
        }

        int id = nextId_++;

        tasks_.emplace(
            id,
            Task{id, userId, validateTitle(title), false}
        );

        return id;
    }

    std::vector<Task> findByUser(int userId) const {
        std::vector<Task> result;

        for (const auto& [id, task] : tasks_) {
            if (task.userId == userId) {
                result.push_back(task);
            }
        }

        return result;
    }

    Task update(
        int taskId,
        int userId,
        bool completed
    ) {
        auto it = tasks_.find(taskId);

        if (it == tasks_.end()) {
            throw std::out_of_range("Task not found");
        }

        if (it->second.userId != userId) {
            throw AuthorizationError(
                "Task ownership violation"
            );
        }

        it->second.completed = completed;

        return it->second;
    }

    bool remove(int taskId, int userId) {
        auto it = tasks_.find(taskId);

        if (it == tasks_.end()) {
            return false;
        }

        if (it->second.userId != userId) {
            throw AuthorizationError(
                "Task ownership violation"
            );
        }

        tasks_.erase(it);
        return true;
    }

    void registerUser(const User& user) {
        if (user.id <= 0 || user.username.empty()) {
            throw ValidationError("Invalid user");
        }

        if (users_.count(user.id)) {
            throw ValidationError("Duplicate user ID");
        }

        users_.emplace(user.id, user);
    }

    bool userExists(int id) const {
        return users_.count(id) != 0;
    }

    bool userActive(int id) const {
        auto it = users_.find(id);

        return it != users_.end() && it->second.active;
    }

private:
    std::map<int, User> users_;
    std::map<int, Task> tasks_;
    int nextId_ = 1;
};

// -----------------------------------------------------
// Cache Management
// -----------------------------------------------------

class CacheManager {
public:
    void invalidate(const std::string& key) {
        cache_.erase(key);
    }

    void store(
        const std::string& key,
        const std::vector<Task>& tasks
    ) {
        cache_[key] = tasks;
    }

    std::optional<std::vector<Task>> retrieve(
        const std::string& key
    ) const {
        auto it = cache_.find(key);

        if (it == cache_.end()) {
            return std::nullopt;
        }

        return it->second;
    }

private:
    std::unordered_map<std::string, std::vector<Task>> cache_;
};

// -----------------------------------------------------
// Middleware
// -----------------------------------------------------

class Middleware {
public:
    Response execute(const Request& request) const {
        if (
            request.path.empty() ||
            request.path.find('\0') != std::string::npos ||
            request.path.find("..") != std::string::npos
        ) {
            return {400, "Invalid request path", {}};
        }

        bool protectedRoute =
            request.path == "/dashboard" ||
            request.path.rfind("/dashboard/", 0) == 0 ||
            request.path == "/api/tasks" ||
            request.path.rfind("/api/tasks/", 0) == 0;

        if (
            protectedRoute &&
            !request.authenticatedUser.has_value()
        ) {
            return {401, "Authentication required", {}};
        }

        return {200, "Middleware passed", {}};
    }
};

// -----------------------------------------------------
// Route Handler Engine
// -----------------------------------------------------

class RouteHandlerEngine {
public:
    RouteHandlerEngine(
        TaskRepository& repository,
        CacheManager& cache
    ) : repository_(repository), cache_(cache) {}

    Response handle(const Request& request) {
        try {
            if (!request.authenticatedUser.has_value()) {
                return {401, "Authentication required", {}};
            }

            int userId = *request.authenticatedUser;

            if (!repository_.userExists(userId)) {
                return {401, "Unknown user", {}};
            }

            if (!repository_.userActive(userId)) {
                return {403, "Inactive account", {}};
            }

            if (request.path == "/api/tasks") {
                return collection(request, userId);
            }

            std::regex pattern(
                R"(^/api/tasks/([1-9][0-9]*)$)"
            );

            std::smatch match;

            if (std::regex_match(
                request.path,
                match,
                pattern
            )) {
                return single(
                    request,
                    userId,
                    validatePositiveId(match[1].str())
                );
            }

            return {404, "Route not found", {}};

        } catch (const ValidationError& error) {
            return {400, error.what(), {}};

        } catch (const AuthorizationError& error) {
            return {403, error.what(), {}};

        } catch (const std::out_of_range& error) {
            return {404, error.what(), {}};

        } catch (const std::exception&) {
            return {500, "Internal server error", {}};
        }
    }

private:
    TaskRepository& repository_;
    CacheManager& cache_;

    Response collection(
        const Request& request,
        int userId
    ) {
        if (request.method == HttpMethod::GET) {
            const std::string key =
                "tasks:" + std::to_string(userId);

            auto cached = cache_.retrieve(key);

            if (cached.has_value()) {
                return {200, "Cached tasks retrieved", *cached};
            }

            auto tasks = repository_.findByUser(userId);

            cache_.store(key, tasks);

            return {200, "Tasks retrieved", tasks};
        }

        if (request.method == HttpMethod::POST) {
            auto it = request.body.find("title");

            if (it == request.body.end()) {
                throw ValidationError("Missing title");
            }

            int id = repository_.create(userId, it->second);

            cache_.invalidate(
                "tasks:" + std::to_string(userId)
            );

            return {
                201,
                "Task created with ID " + std::to_string(id),
                {}
            };
        }

        return {405, "Method not allowed", {}};
    }

    Response single(
        const Request& request,
        int userId,
        int taskId
    ) {
        if (request.method == HttpMethod::PATCH) {
            auto it = request.body.find("completed");

            if (
                it == request.body.end() ||
                (it->second != "true" && it->second != "false")
            ) {
                throw ValidationError(
                    "completed must be true or false"
                );
            }

            Task task = repository_.update(
                taskId,
                userId,
                it->second == "true"
            );

            cache_.invalidate(
                "tasks:" + std::to_string(userId)
            );

            return {200, "Task updated", {task}};
        }

        if (request.method == HttpMethod::DELETE) {
            if (!repository_.remove(taskId, userId)) {
                return {404, "Task not found", {}};
            }

            cache_.invalidate(
                "tasks:" + std::to_string(userId)
            );

            return {200, "Task deleted", {}};
        }

        return {405, "Method not allowed", {}};
    }
};

// -----------------------------------------------------
// Server Actions
// -----------------------------------------------------

class ServerActionService {
public:
    ServerActionService(
        TaskRepository& repository,
        CacheManager& cache
    ) : repository_(repository), cache_(cache) {}

    Response createTask(
        const std::optional<int>& authenticatedUser,
        const std::string& title
    ) {
        if (!authenticatedUser.has_value()) {
            return {401, "Authentication required", {}};
        }

        try {
            int userId = *authenticatedUser;

            if (
                !repository_.userExists(userId) ||
                !repository_.userActive(userId)
            ) {
                return {403, "Unauthorized account", {}};
            }

            int id = repository_.create(
                userId,
                validateTitle(title)
            );

            cache_.invalidate(
                "tasks:" + std::to_string(userId)
            );

            return {
                201,
                "Server action created task " + std::to_string(id),
                {}
            };

        } catch (const std::exception& error) {
            return {400, error.what(), {}};
        }
    }

private:
    TaskRepository& repository_;
    CacheManager& cache_;
};

// -----------------------------------------------------
// Application Runtime
// -----------------------------------------------------

class Application {
public:
    explicit Application(EnvironmentConfig config)
        : config_(std::move(config)),
          middleware_(),
          routes_(repository_, cache_),
          actions_(repository_, cache_) {}

    void registerUser(const User& user) {
        repository_.registerUser(user);
    }

    Response handle(const Request& request) {
        auto middlewareResponse = middleware_.execute(request);

        if (middlewareResponse.status != 200) {
            return middlewareResponse;
        }

        return routes_.handle(request);
    }

    Response createTaskAction(
        const std::optional<int>& userId,
        const std::string& title
    ) {
        return actions_.createTask(userId, title);
    }

private:
    EnvironmentConfig config_;
    TaskRepository repository_;
    CacheManager cache_;
    Middleware middleware_;
    RouteHandlerEngine routes_;
    ServerActionService actions_;
};

} // namespace nextjs

// -----------------------------------------------------
// Program Entry Point
// -----------------------------------------------------

int main() {
    using namespace nextjs;

    try {
        std::map<std::string, std::string> variables = {
            {"DATABASE_URL",
             "postgresql://app:secret@localhost:5432/tasks"},
            {"SESSION_SECRET",
             "0123456789abcdef0123456789abcdef"},
            {"APP_ENV", "development"},
            {"NEXT_PUBLIC_APP_NAME", "Task Manager"}
        };

        EnvironmentManager environment(variables);

        EnvironmentConfig config = environment.load();

        Application application(config);

        application.registerUser({
            1, "alice", UserRole::USER, true
        });

        application.registerUser({
            2, "bob", UserRole::USER, true
        });

        std::cout << "Application: "
                  << config.publicAppName << '\n';

        // Authentication failure.
        Response unauthorized = application.handle({
            HttpMethod::GET,
            "/api/tasks",
            std::nullopt,
            {},
            "req-001"
        });

        std::cout << "\nUnauthenticated request: "
                  << unauthorized.status << " "
                  << unauthorized.message << '\n';

        // Create task using route handler.
        Response created = application.handle({
            HttpMethod::POST,
            "/api/tasks",
            1,
            {{"title", "Implement Next.js route handlers"}},
            "req-002"
        });

        std::cout << "\nCreate route: "
                  << created.status << " "
                  << created.message << '\n';

        // Retrieve tasks.
        Response retrieved = application.handle({
            HttpMethod::GET,
            "/api/tasks",
            1,
            {},
            "req-003"
        });

        std::cout << "\nRetrieved tasks: "
                  << retrieved.tasks.size() << '\n';

        for (const auto& task : retrieved.tasks) {
            std::cout
                << "ID=" << task.id
                << " User=" << task.userId
                << " Title=" << task.title
                << " Completed=" << std::boolalpha
                << task.completed << '\n';
        }

        // Ownership enforcement.
        Response forbidden = application.handle({
            HttpMethod::PATCH,
            "/api/tasks/1",
            2,
            {{"completed", "true"}},
            "req-004"
        });

        std::cout << "\nCross-user update: "
                  << forbidden.status << " "
                  << forbidden.message << '\n';

        // Server action.
        Response action = application.createTaskAction(
            1,
            "Implement server actions"
        );

        std::cout << "\nServer action: "
                  << action.status << " "
                  << action.message << '\n';

        // Invalid input.
        Response invalid = application.handle({
            HttpMethod::POST,
            "/api/tasks",
            1,
            {{"title", "   "}},
            "req-005"
        });

        std::cout << "\nInvalid input: "
                  << invalid.status << " "
                  << invalid.message << '\n';

        // Invalid route.
        Response missing = application.handle({
            HttpMethod::GET,
            "/api/unknown",
            1,
            {},
            "req-006"
        });

        std::cout << "\nUnknown route: "
                  << missing.status << " "
                  << missing.message << '\n';

        std::cout << "\nAll demonstrations completed.\n";

        return 0;

    } catch (const ConfigurationError& error) {
        std::cerr << "Configuration failure: "
                  << error.what() << '\n';

        return 1;

    } catch (const std::exception& error) {
        std::cerr << "Application failure: "
                  << error.what() << '\n';

        return 1;
    }
}
