#include <algorithm>
#include <chrono>
#include <cmath>
#include <functional>
#include <iostream>
#include <map>
#include <memory>
#include <optional>
#include <set>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

/*
 * Next.js Advanced Architecture
 *
 * Repository-style component rendering and governance engine.
 *
 * Models:
 * 1. Server Components
 * 2. Client Components
 * 3. Serializable props
 * 4. Suspense boundaries
 * 5. Streaming loading states
 * 6. Error boundaries
 * 7. Nested route segments
 * 8. Request-scoped data caching
 * 9. Component rendering lifecycle
 *
 * Compile:
 * g++ -std=c++17 -O2 -Wall -Wextra -pedantic nextjs_engine.cpp -o nextjs_engine
 */

enum class ComponentKind {
    Server,
    Client
};

enum class RenderState {
    Created,
    Loading,
    Streaming,
    Ready,
    Error,
    NotFound,
    Recovered
};

enum class ValueType {
    Null,
    Boolean,
    Number,
    String,
    Array,
    Object,
    Function
};

/*
 * A tagged value provides a simplified model of the
 * serializable data that may cross a component boundary.
 */
struct Value {
    ValueType type = ValueType::Null;

    std::string stringValue;
    double numberValue = 0.0;
    bool booleanValue = false;

    std::vector<Value> arrayValue;
    std::map<std::string, Value> objectValue;

    static Value null() {
        return Value{};
    }

    static Value boolean(bool value) {
        Value result;
        result.type = ValueType::Boolean;
        result.booleanValue = value;
        return result;
    }

    static Value number(double value) {
        Value result;
        result.type = ValueType::Number;
        result.numberValue = value;
        return result;
    }

    static Value string(const std::string& value) {
        Value result;
        result.type = ValueType::String;
        result.stringValue = value;
        return result;
    }

    static Value array(std::vector<Value> values) {
        Value result;
        result.type = ValueType::Array;
        result.arrayValue = std::move(values);
        return result;
    }

    static Value object(std::map<std::string, Value> values) {
        Value result;
        result.type = ValueType::Object;
        result.objectValue = std::move(values);
        return result;
    }

    static Value function() {
        Value result;
        result.type = ValueType::Function;
        return result;
    }
};

using Props = std::map<std::string, Value>;

class ApplicationException : public std::runtime_error {
public:
    explicit ApplicationException(const std::string& message)
        : std::runtime_error(message) {}
};

class SerializationException : public ApplicationException {
public:
    explicit SerializationException(const std::string& message)
        : ApplicationException(message) {}
};

class MissingResourceException : public ApplicationException {
public:
    explicit MissingResourceException(const std::string& message)
        : ApplicationException(message) {}
};

class Component {
private:
    std::string name_;
    ComponentKind kind_;
    Props props_;

public:
    Component(
        std::string name,
        ComponentKind kind,
        Props props = {}
    )
        : name_(std::move(name)),
          kind_(kind),
          props_(std::move(props)) {

        if (name_.empty()) {
            throw std::invalid_argument(
                "Component name cannot be empty."
            );
        }
    }

    const std::string& name() const {
        return name_;
    }

    ComponentKind kind() const {
        return kind_;
    }

    const Props& props() const {
        return props_;
    }
};

struct RenderResult {
    std::string component;
    RenderState state;
    std::string output;
    std::string error;
    double durationMs = 0.0;
};

std::string stateName(RenderState state) {
    switch (state) {
        case RenderState::Created: return "CREATED";
        case RenderState::Loading: return "LOADING";
        case RenderState::Streaming: return "STREAMING";
        case RenderState::Ready: return "READY";
        case RenderState::Error: return "ERROR";
        case RenderState::NotFound: return "NOT_FOUND";
        case RenderState::Recovered: return "RECOVERED";
    }

    return "UNKNOWN";
}

std::string stringProperty(
    const Props& props,
    const std::string& key,
    const std::string& fallback
) {
    auto iterator = props.find(key);

    if (iterator == props.end()) {
        return fallback;
    }

    if (iterator->second.type != ValueType::String) {
        throw std::invalid_argument(
            "Property " + key + " must be a string."
        );
    }

    return iterator->second.stringValue;
}

int integerProperty(
    const Props& props,
    const std::string& key,
    int fallback
) {
    auto iterator = props.find(key);

    if (iterator == props.end()) {
        return fallback;
    }

    if (iterator->second.type != ValueType::Number) {
        throw std::invalid_argument(
            "Property " + key + " must be numeric."
        );
    }

    const double number = iterator->second.numberValue;

    if (!std::isfinite(number) ||
        std::floor(number) != number ||
        number < 0 ||
        number > 1000000000) {
        throw std::invalid_argument(
            "Invalid integer property: " + key
        );
    }

    return static_cast<int>(number);
}

/*
 * Validate the complete nested value tree.
 *
 * Functions and non-finite numbers cannot be transferred
 * through this simplified serialization contract.
 */
void validateSerializable(const Value& value) {
    switch (value.type) {
        case ValueType::Null:
        case ValueType::Boolean:
        case ValueType::String:
            return;

        case ValueType::Number:
            if (!std::isfinite(value.numberValue)) {
                throw SerializationException(
                    "Non-finite numeric value."
                );
            }
            return;

        case ValueType::Array:
            for (const auto& item : value.arrayValue) {
                validateSerializable(item);
            }
            return;

        case ValueType::Object:
            for (const auto& [key, item] : value.objectValue) {
                if (key.empty()) {
                    throw SerializationException(
                        "Empty object key."
                    );
                }

                validateSerializable(item);
            }
            return;

        case ValueType::Function:
            throw SerializationException(
                "Function cannot cross the client boundary."
            );
    }
}

/*
 * Server-only repository.
 */
struct UserRecord {
    int id;
    std::string name;
    std::string role;
    std::string privateToken;
};

class UserRepository {
private:
    std::unordered_map<int, UserRecord> users_;

public:
    UserRepository() {
        users_.emplace(
            1,
            UserRecord{
                1,
                "Atul",
                "administrator",
                "SERVER_SECRET"
            }
        );

        users_.emplace(
            2,
            UserRecord{
                2,
                "Developer",
                "member",
                "ANOTHER_SECRET"
            }
        );
    }

    Value getPublicUser(int id) const {
        auto iterator = users_.find(id);

        if (iterator == users_.end()) {
            throw MissingResourceException(
                "User not found: " + std::to_string(id)
            );
        }

        const UserRecord& user = iterator->second;

        // Explicit field selection prevents data leakage.
        return Value::object({
            {"id", Value::number(user.id)},
            {"name", Value::string(user.name)},
            {"role", Value::string(user.role)}
        });
    }
};

class RequestCache {
private:
    std::unordered_map<std::string, Value> cache_;

public:
    template <typename Loader>
    Value getOrLoad(
        const std::string& key,
        Loader loader
    ) {
        auto iterator = cache_.find(key);

        if (iterator != cache_.end()) {
            return iterator->second;
        }

        Value result = loader();
        cache_.emplace(key, result);

        return result;
    }

    void clear() {
        cache_.clear();
    }

    std::size_t size() const {
        return cache_.size();
    }
};

/*
 * Rendering engine.
 *
 * The engine evaluates rendering boundaries independently.
 * Repository-level failures become explicit render states.
 */
class RenderingEngine {
private:
    const UserRepository& repository_;
    RequestCache cache_;

public:
    explicit RenderingEngine(const UserRepository& repository)
        : repository_(repository) {}

    void beginRequest() {
        cache_.clear();
    }

    RenderResult renderServer(const Component& component) {
        if (component.kind() != ComponentKind::Server) {
            throw std::invalid_argument(
                "Server Component required."
            );
        }

        const auto start =
            std::chrono::steady_clock::now();

        try {
            Value output;

            if (component.name() == "UserProfile") {
                const int userId = integerProperty(
                    component.props(),
                    "userId",
                    1
                );

                output = cache_.getOrLoad(
                    "user:" + std::to_string(userId),
                    [&]() {
                        return repository_.getPublicUser(userId);
                    }
                );

            } else if (component.name() == "Dashboard") {
                const int userId = integerProperty(
                    component.props(),
                    "userId",
                    1
                );

                Value user = cache_.getOrLoad(
                    "user:" + std::to_string(userId),
                    [&]() {
                        return repository_.getPublicUser(userId);
                    }
                );

                output = Value::object({
                    {"user", user},
                    {
                        "metrics",
                        Value::object({
                            {"projects", Value::number(12)},
                            {"pendingTasks", Value::number(8)},
                            {"completedTasks", Value::number(24)}
                        })
                    }
                });

            } else {
                output = Value::object({
                    {
                        "content",
                        Value::string(
                            stringProperty(
                                component.props(),
                                "content",
                                ""
                            )
                        )
                    }
                });
            }

            const auto end =
                std::chrono::steady_clock::now();

            const double duration =
                std::chrono::duration<double, std::milli>(
                    end - start
                ).count();

            return RenderResult{
                component.name(),
                RenderState::Ready,
                "Server output generated",
                "",
                duration
            };

        } catch (const MissingResourceException& error) {
            return RenderResult{
                component.name(),
                RenderState::NotFound,
                "",
                error.what()
            };

        } catch (const std::exception& error) {
            return RenderResult{
                component.name(),
                RenderState::Error,
                "",
                error.what()
            };
        }
    }

    RenderResult renderClient(
        const Component& component,
        const std::optional<Value>& serverData = std::nullopt
    ) const {

        if (component.kind() != ComponentKind::Client) {
            throw std::invalid_argument(
                "Client Component required."
            );
        }

        try {
            for (const auto& [key, value] : component.props()) {
                (void)key;
                validateSerializable(value);
            }

            if (serverData.has_value()) {
                validateSerializable(serverData.value());
            }

            return RenderResult{
                component.name(),
                RenderState::Ready,
                "Serializable props transferred; hydration required",
                ""
            };

        } catch (const SerializationException& error) {
            return RenderResult{
                component.name(),
                RenderState::Error,
                "",
                error.what()
            };
        }
    }

    std::size_t cachedEntries() const {
        return cache_.size();
    }
};

/*
 * Models loading fallback behavior.
 *
 * A real streaming renderer does not block the entire route
 * until every nested component finishes.
 */
class SuspenseBoundary {
private:
    std::string name_;
    std::string fallback_;
    RenderState state_ = RenderState::Created;

public:
    SuspenseBoundary(
        std::string name,
        std::string fallback
    )
        : name_(std::move(name)),
          fallback_(std::move(fallback)) {

        if (name_.empty() || fallback_.empty()) {
            throw std::invalid_argument(
                "Boundary name and fallback are required."
            );
        }
    }

    RenderResult begin() {
        state_ = RenderState::Streaming;

        return RenderResult{
            name_,
            state_,
            fallback_,
            ""
        };
    }

    RenderResult complete(const std::string& output) {
        if (state_ != RenderState::Streaming) {
            throw std::logic_error(
                "Suspense boundary is not streaming."
            );
        }

        state_ = RenderState::Ready;

        return RenderResult{
            name_,
            state_,
            output,
            ""
        };
    }

    RenderResult fail(const std::string& error) {
        if (state_ != RenderState::Streaming) {
            throw std::logic_error(
                "Suspense boundary is not streaming."
            );
        }

        state_ = RenderState::Error;

        return RenderResult{
            name_,
            state_,
            "",
            error
        };
    }
};

/*
 * Error boundaries isolate rendering failures.
 * reset() retries the failed operation.
 */
class ErrorBoundary {
private:
    std::string fallback_;
    std::string lastError_;
    int resetCount_ = 0;

public:
    explicit ErrorBoundary(std::string fallback)
        : fallback_(std::move(fallback)) {}

    template <typename Operation>
    RenderResult execute(Operation operation) {
        try {
            const std::string output = operation();

            lastError_.clear();

            return RenderResult{
                "ErrorBoundary",
                RenderState::Ready,
                output,
                ""
            };

        } catch (const std::exception& error) {
            lastError_ = error.what();

            return RenderResult{
                "ErrorBoundary",
                RenderState::Error,
                fallback_,
                lastError_
            };
        }
    }

    template <typename Operation>
    RenderResult reset(Operation operation) {
        ++resetCount_;

        RenderResult result = execute(operation);

        if (result.state == RenderState::Ready) {
            result.state = RenderState::Recovered;
        }

        return result;
    }

    int resetCount() const {
        return resetCount_;
    }
};

/*
 * Route tree with deterministic child lookup.
 * std::map provides O(log n) lookup and ordered traversal.
 */
class RouteSegment {
private:
    std::string name_;
    std::string loading_;
    std::string error_;
    std::map<std::string, std::unique_ptr<RouteSegment>> children_;

public:
    RouteSegment(
        std::string name,
        std::string loading,
        std::string error
    )
        : name_(std::move(name)),
          loading_(std::move(loading)),
          error_(std::move(error)) {

        if (name_.empty()) {
            throw std::invalid_argument(
                "Route name cannot be empty."
            );
        }
    }

    void addChild(std::unique_ptr<RouteSegment> child) {
        if (!child) {
            throw std::invalid_argument(
                "Child route cannot be null."
            );
        }

        const std::string childName = child->name_;

        if (children_.count(childName)) {
            throw std::invalid_argument(
                "Duplicate route: " + childName
            );
        }

        children_.emplace(childName, std::move(child));
    }

    const RouteSegment& resolve(
        const std::vector<std::string>& path
    ) const {
        const RouteSegment* current = this;

        for (const auto& segment : path) {
            auto iterator = current->children_.find(segment);

            if (iterator == current->children_.end()) {
                throw MissingResourceException(
                    "Route segment not found: " + segment
                );
            }

            current = iterator->second.get();
        }

        return *current;
    }

    const std::string& name() const {
        return name_;
    }

    const std::string& loading() const {
        return loading_;
    }

    const std::string& error() const {
        return error_;
    }
};

void printResult(const RenderResult& result) {
    std::cout
        << result.component
        << " | "
        << stateName(result.state)
        << " | "
        << (result.error.empty() ? result.output : result.error)
        << '\n';
}

void runTests() {
    UserRepository repository;
    RenderingEngine engine(repository);

    engine.beginRequest();

    Component profile(
        "UserProfile",
        ComponentKind::Server,
        {{"userId", Value::number(1)}}
    );

    RenderResult valid = engine.renderServer(profile);

    if (valid.state != RenderState::Ready) {
        throw std::runtime_error(
            "Valid profile failed."
        );
    }

    Component missing(
        "UserProfile",
        ComponentKind::Server,
        {{"userId", Value::number(999)}}
    );

    RenderResult absent = engine.renderServer(missing);

    if (absent.state != RenderState::NotFound) {
        throw std::runtime_error(
            "Missing resource state incorrect."
        );
    }

    Component client(
        "DashboardControls",
        ComponentKind::Client,
        {
            {"theme", Value::string("dark")},
            {"active", Value::boolean(true)}
        }
    );

    if (engine.renderClient(client).state != RenderState::Ready) {
        throw std::runtime_error(
            "Valid client props rejected."
        );
    }

    Component invalidClient(
        "InvalidControls",
        ComponentKind::Client,
        {{"handler", Value::function()}}
    );

    if (engine.renderClient(invalidClient).state != RenderState::Error) {
        throw std::runtime_error(
            "Function prop was not rejected."
        );
    }

    SuspenseBoundary suspense(
        "Analytics",
        "Loading analytics..."
    );

    if (suspense.begin().state != RenderState::Streaming) {
        throw std::runtime_error(
            "Suspense loading state failed."
        );
    }

    if (suspense.complete("Analytics ready").state != RenderState::Ready) {
        throw std::runtime_error(
            "Suspense completion failed."
        );
    }

    ErrorBoundary boundary("Dashboard unavailable");

    int attempts = 0;

    auto operation = [&]() -> std::string {
        ++attempts;

        if (attempts == 1) {
            throw std::runtime_error("Temporary failure");
        }

        return "Recovered";
    };

    if (boundary.execute(operation).state != RenderState::Error) {
        throw std::runtime_error(
            "Error boundary did not catch failure."
        );
    }

    if (boundary.reset(operation).state != RenderState::Recovered) {
        throw std::runtime_error(
            "Error boundary recovery failed."
        );
    }

    RouteSegment root(
        "dashboard",
        "Loading dashboard",
        "Dashboard failed"
    );

    auto analytics = std::make_unique<RouteSegment>(
        "analytics",
        "Loading analytics",
        "Analytics failed"
    );

    root.addChild(std::move(analytics));

    if (root.resolve({"analytics"}).name() != "analytics") {
        throw std::runtime_error(
            "Nested route resolution failed."
        );
    }

    std::cout << "\nAll C++17 tests passed.\n";
}

int main() {
    try {
        std::cout << "NEXT.JS ADVANCED ARCHITECTURE\n";
        std::cout << "=============================\n\n";

        UserRepository repository;
        RenderingEngine engine(repository);

        engine.beginRequest();

        Component dashboard(
            "Dashboard",
            ComponentKind::Server,
            {{"userId", Value::number(1)}}
        );

        RenderResult serverResult =
            engine.renderServer(dashboard);

        printResult(serverResult);

        Component controls(
            "DashboardControls",
            ComponentKind::Client,
            {
                {"theme", Value::string("dark")},
                {"refresh", Value::boolean(true)}
            }
        );

        RenderResult clientResult =
            engine.renderClient(controls);

        printResult(clientResult);

        std::cout << "\nSUSPENSE BOUNDARY\n";

        SuspenseBoundary suspense(
            "Reports",
            "Loading reports..."
        );

        printResult(suspense.begin());
        printResult(suspense.complete("Reports loaded"));

        std::cout << "\nERROR RECOVERY\n";

        ErrorBoundary boundary(
            "Service temporarily unavailable"
        );

        int attempts = 0;

        auto unstable = [&]() -> std::string {
            ++attempts;

            if (attempts == 1) {
                throw std::runtime_error(
                    "Database connection interrupted."
                );
            }

            return "Dashboard restored.";
        };

        printResult(boundary.execute(unstable));
        printResult(boundary.reset(unstable));

        runTests();

        std::cout << "\nExecution completed.\n";

        return 0;

    } catch (const std::exception& error) {
        std::cerr
            << "Fatal error: "
            << error.what()
            << '\n';

        return 1;
    }
}
