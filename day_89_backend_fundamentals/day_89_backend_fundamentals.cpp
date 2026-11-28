#include <algorithm>
#include <chrono>
#include <cstdint>
#include <functional>
#include <iomanip>
#include <iostream>
#include <map>
#include <memory>
#include <mutex>
#include <optional>
#include <regex>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

using namespace std;

// ---------------------------------------------------------
// Backend Fundamentals: C++17
//
// A lightweight backend request-processing engine.
//
// Compile:
// g++ -std=c++17 -O2 -Wall -Wextra backend.cpp -o backend
//
// Run:
// ./backend
// ---------------------------------------------------------

// ---------------------------------------------------------
// Domain types
// ---------------------------------------------------------

enum class TaskStatus {
    Pending,
    InProgress,
    Completed
};

string statusToString(TaskStatus status) {
    switch (status) {
        case TaskStatus::Pending:
            return "pending";
        case TaskStatus::InProgress:
            return "in_progress";
        case TaskStatus::Completed:
            return "completed";
    }

    throw logic_error("Unknown task status");
}

TaskStatus parseStatus(const string& value) {
    if (value == "pending") {
        return TaskStatus::Pending;
    }

    if (value == "in_progress") {
        return TaskStatus::InProgress;
    }

    if (value == "completed") {
        return TaskStatus::Completed;
    }

    throw invalid_argument("Invalid task status");
}

struct Task {
    int id;
    string title;
    string description;
    TaskStatus status;
    string createdAt;
    string updatedAt;
};

struct Request {
    string method;
    string path;
    map<string, string> headers;
    map<string, string> parameters;
    map<string, string> body;
    string requestId;
};

struct Response {
    int status;
    string body;
    map<string, string> headers;
};

// ---------------------------------------------------------
// Application exceptions
// ---------------------------------------------------------

class BackendException : public runtime_error {
public:
    int status;

    BackendException(
        int code,
        const string& message
    ) : runtime_error(message), status(code) {}
};

class ValidationException : public BackendException {
public:
    explicit ValidationException(const string& message)
        : BackendException(400, message) {}
};

class NotFoundException : public BackendException {
public:
    explicit NotFoundException(const string& message)
        : BackendException(404, message) {}
};

class ConflictException : public BackendException {
public:
    explicit ConflictException(const string& message)
        : BackendException(409, message) {}
};

// ---------------------------------------------------------
// Utility functions
// ---------------------------------------------------------

string currentTimestamp() {
    using namespace chrono;

    auto now = system_clock::now();
    auto value = system_clock::to_time_t(now);

    tm utc{};

#ifdef _WIN32
    gmtime_s(&utc, &value);
#else
    gmtime_r(&value, &utc);
#endif

    ostringstream output;

    output << put_time(
        &utc,
        "%Y-%m-%dT%H:%M:%SZ"
    );

    return output.str();
}

string jsonEscape(const string& value) {
    ostringstream output;

    for (unsigned char c : value) {
        switch (c) {
            case '"':
                output << "\\\"";
                break;
            case '\\':
                output << "\\\\";
                break;
            case '\n':
                output << "\\n";
                break;
            case '\r':
                output << "\\r";
                break;
            case '\t':
                output << "\\t";
                break;
            default:
                if (c < 32) {
                    output << '?';
                } else {
                    output << static_cast<char>(c);
                }
        }
    }

    return output.str();
}

string serializeTask(const Task& task) {
    ostringstream output;

    output
        << "{"
        << "\"id\":" << task.id << ","
        << "\"title\":\"" << jsonEscape(task.title) << "\","
        << "\"description\":\""
        << jsonEscape(task.description) << "\","
        << "\"status\":\""
        << statusToString(task.status) << "\","
        << "\"createdAt\":\"" << task.createdAt << "\","
        << "\"updatedAt\":\"" << task.updatedAt << "\""
        << "}";

    return output.str();
}

// ---------------------------------------------------------
// Repository
// ---------------------------------------------------------

class TaskRepository {
private:
    unordered_map<int, Task> tasks;
    int nextId = 1;
    mutable mutex dataMutex;

public:
    Task create(
        const string& title,
        const string& description
    ) {
        lock_guard<mutex> lock(dataMutex);

        string now = currentTimestamp();

        Task task{
            nextId++,
            title,
            description,
            TaskStatus::Pending,
            now,
            now
        };

        tasks.emplace(task.id, task);

        return task;
    }

    vector<Task> findAll() const {
        lock_guard<mutex> lock(dataMutex);

        vector<Task> result;

        result.reserve(tasks.size());

        for (const auto& entry : tasks) {
            result.push_back(entry.second);
        }

        sort(
            result.begin(),
            result.end(),
            [](const Task& a, const Task& b) {
                return a.id < b.id;
            }
        );

        return result;
    }

    Task findById(int id) const {
        lock_guard<mutex> lock(dataMutex);

        auto iterator = tasks.find(id);

        if (iterator == tasks.end()) {
            throw NotFoundException(
                "Task does not exist"
            );
        }

        return iterator->second;
    }

    Task update(
        int id,
        const map<string, string>& changes
    ) {
        lock_guard<mutex> lock(dataMutex);

        auto iterator = tasks.find(id);

        if (iterator == tasks.end()) {
            throw NotFoundException(
                "Task does not exist"
            );
        }

        Task updated = iterator->second;

        for (const auto& change : changes) {
            if (change.first == "title") {
                updated.title = change.second;
            } else if (change.first == "description") {
                updated.description = change.second;
            } else if (change.first == "status") {
                updated.status = parseStatus(change.second);
            }
        }

        updated.updatedAt = currentTimestamp();

        iterator->second = updated;

        return updated;
    }

    void remove(int id) {
        lock_guard<mutex> lock(dataMutex);

        if (tasks.erase(id) == 0) {
            throw NotFoundException(
                "Task does not exist"
            );
        }
    }
};

// ---------------------------------------------------------
// Validation
// ---------------------------------------------------------

class TaskValidator {
public:
    static void validateTitle(const string& title) {
        if (title.empty() || title.size() > 150) {
            throw ValidationException(
                "Title must contain 1 to 150 characters"
            );
        }

        if (title.find_first_not_of(" \t\r\n") == string::npos) {
            throw ValidationException(
                "Title cannot contain only whitespace"
            );
        }
    }

    static void validateDescription(
        const string& description
    ) {
        if (description.size() > 2000) {
            throw ValidationException(
                "Description exceeds 2000 characters"
            );
        }
    }

    static void validateCreate(
        const map<string, string>& data
    ) {
        for (const auto& field : data) {
            if (
                field.first != "title" &&
                field.first != "description"
            ) {
                throw ValidationException(
                    "Unsupported create field: " + field.first
                );
            }
        }

        auto iterator = data.find("title");

        if (iterator == data.end()) {
            throw ValidationException(
                "Title is required"
            );
        }

        validateTitle(iterator->second);

        auto description = data.find("description");

        if (description != data.end()) {
            validateDescription(description->second);
        }
    }

    static void validateUpdate(
        const map<string, string>& data
    ) {
        if (data.empty()) {
            throw ValidationException(
                "Update must contain at least one field"
            );
        }

        for (const auto& field : data) {
            if (field.first == "title") {
                validateTitle(field.second);
            } else if (field.first == "description") {
                validateDescription(field.second);
            } else if (field.first == "status") {
                parseStatus(field.second);
            } else {
                throw ValidationException(
                    "Unsupported update field: " + field.first
                );
            }
        }
    }
};

// ---------------------------------------------------------
// Service
// ---------------------------------------------------------

class TaskService {
private:
    shared_ptr<TaskRepository> repository;

public:
    explicit TaskService(
        shared_ptr<TaskRepository> repository
    ) : repository(move(repository)) {}

    Task create(const map<string, string>& data) {
        TaskValidator::validateCreate(data);

        string title = data.at("title");

        string description = "";

        auto iterator = data.find("description");

        if (iterator != data.end()) {
            description = iterator->second;
        }

        return repository->create(
            title,
            description
        );
    }

    vector<Task> list() const {
        return repository->findAll();
    }

    Task get(int id) const {
        return repository->findById(id);
    }

    Task update(
        int id,
        const map<string, string>& changes
    ) {
        TaskValidator::validateUpdate(changes);

        return repository->update(id, changes);
    }

    void remove(int id) {
        repository->remove(id);
    }
};

// ---------------------------------------------------------
// HTTP-like routing engine
// ---------------------------------------------------------

using Controller = function<Response(Request&)>;

struct Route {
    string method;
    regex pattern;
    vector<string> parameterNames;
    Controller controller;
};

class Router {
private:
    vector<Route> routes;

public:
    void add(
        const string& method,
        const string& path,
        Controller controller
    ) {
        regex placeholder(R"(\{([a-zA-Z_][a-zA-Z0-9_]*)\})");

        vector<string> names;

        string expression;
        size_t position = 0;

        auto begin = sregex_iterator(
            path.begin(),
            path.end(),
            placeholder
        );

        auto end = sregex_iterator();

        for (auto iterator = begin; iterator != end; ++iterator) {
            smatch match = *iterator;

            expression += path.substr(
                position,
                static_cast<size_t>(match.position()) - position
            );

            names.push_back(match[1].str());

            expression += "([^/]+)";

            position = static_cast<size_t>(
                match.position() + match.length()
            );
        }

        expression += path.substr(position);

        routes.push_back({
            method,
            regex("^" + expression + "$"),
            names,
            move(controller)
        });
    }

    Response dispatch(Request& request) const {
        bool methodMismatch = false;

        for (const auto& route : routes) {
            smatch match;

            if (!regex_match(request.path, match, route.pattern)) {
                continue;
            }

            if (route.method != request.method) {
                methodMismatch = true;
                continue;
            }

            request.parameters.clear();

            for (size_t i = 0; i < route.parameterNames.size(); ++i) {
                request.parameters[
                    route.parameterNames[i]
                ] = match[i + 1].str();
            }

            return route.controller(request);
        }

        if (methodMismatch) {
            return {
                405,
                R"({"error":"METHOD_NOT_ALLOWED"})",
                {}
            };
        }

        return {
            404,
            R"({"error":"ROUTE_NOT_FOUND"})",
            {}
        };
    }
};

// ---------------------------------------------------------
// Controller
// ---------------------------------------------------------

class TaskController {
private:
    shared_ptr<TaskService> service;

    static int parseId(const string& value) {
        if (
            value.empty() ||
            !all_of(
                value.begin(),
                value.end(),
                [](unsigned char c) {
                    return c >= '0' && c <= '9';
                }
            )
        ) {
            throw ValidationException(
                "Invalid task ID"
            );
        }

        try {
            size_t processed = 0;

            long long number = stoll(value, &processed);

            if (
                processed != value.size() ||
                number <= 0 ||
                number > 2147483647LL
            ) {
                throw ValidationException(
                    "Task ID is outside supported range"
                );
            }

            return static_cast<int>(number);

        } catch (const out_of_range&) {
            throw ValidationException(
                "Task ID is outside supported range"
            );
        }
    }

public:
    explicit TaskController(
        shared_ptr<TaskService> service
    ) : service(move(service)) {}

    Response list(Request&) {
        vector<Task> tasks = service->list();

        ostringstream output;

        output << "{\"count\":" << tasks.size() << ",\"data\":[";

        for (size_t i = 0; i < tasks.size(); ++i) {
            if (i > 0) {
                output << ",";
            }

            output << serializeTask(tasks[i]);
        }

        output << "]}";

        return {
            200,
            output.str(),
            {}
        };
    }

    Response get(Request& request) {
        Task task = service->get(
            parseId(request.parameters.at("id"))
        );

        return {
            200,
            "{\"data\":" + serializeTask(task) + "}",
            {}
        };
    }

    Response create(Request& request) {
        Task task = service->create(request.body);

        return {
            201,
            "{\"data\":" + serializeTask(task) + "}",
            {}
        };
    }

    Response update(Request& request) {
        Task task = service->update(
            parseId(request.parameters.at("id")),
            request.body
        );

        return {
            200,
            "{\"data\":" + serializeTask(task) + "}",
            {}
        };
    }

    Response remove(Request& request) {
        service->remove(
            parseId(request.parameters.at("id"))
        );

        return {
            200,
            R"({"message":"Task deleted successfully"})",
            {}
        };
    }
};

// ---------------------------------------------------------
// Middleware
// ---------------------------------------------------------

using Middleware = function<Response(
    Request&,
    const function<Response(Request&)>&
)>;

class MiddlewarePipeline {
private:
    vector<Middleware> middleware;

public:
    void use(Middleware component) {
        middleware.push_back(move(component));
    }

    Response execute(
        Request& request,
        const function<Response(Request&)>& endpoint
    ) const {
        function<Response(Request&)> next = endpoint;

        for (
            auto iterator = middleware.rbegin();
            iterator != middleware.rend();
            ++iterator
        ) {
            Middleware current = *iterator;

            auto previous = next;

            next = [
                current,
                previous
            ](Request& context) {
                return current(context, previous);
            };
        }

        return next(request);
    }
};

// ---------------------------------------------------------
// Application composition
// ---------------------------------------------------------

class Application {
private:
    shared_ptr<TaskRepository> repository;
    shared_ptr<TaskService> service;
    shared_ptr<TaskController> controller;

    Router router;
    MiddlewarePipeline pipeline;

public:
    Application() {
        repository = make_shared<TaskRepository>();

        service = make_shared<TaskService>(
            repository
        );

        controller = make_shared<TaskController>(
            service
        );

        router.add(
            "GET",
            "/health",
            [](Request&) {
                return Response{
                    200,
                    R"({"status":"healthy","service":"task-api"})",
                    {}
                };
            }
        );

        router.add(
            "GET",
            "/api/v1/tasks",
            [this](Request& request) {
                return controller->list(request);
            }
        );

        router.add(
            "POST",
            "/api/v1/tasks",
            [this](Request& request) {
                return controller->create(request);
            }
        );

        router.add(
            "GET",
            "/api/v1/tasks/{id}",
            [this](Request& request) {
                return controller->get(request);
            }
        );

        router.add(
            "PATCH",
            "/api/v1/tasks/{id}",
            [this](Request& request) {
                return controller->update(request);
            }
        );

        router.add(
            "DELETE",
            "/api/v1/tasks/{id}",
            [this](Request& request) {
                return controller->remove(request);
            }
        );

        pipeline.use(
            [](Request& request,
               const function<Response(Request&)>& next) {

                request.requestId =
                    "REQ-" + to_string(
                        chrono::steady_clock::now()
                            .time_since_epoch()
                            .count()
                    );

                Response response = next(request);

                response.headers["X-Request-ID"] =
                    request.requestId;

                return response;
            }
        );

        pipeline.use(
            [](Request& request,
               const function<Response(Request&)>& next) {

                auto start = chrono::steady_clock::now();

                Response response = next(request);

                auto elapsed =
                    chrono::duration<double, milli>(
                        chrono::steady_clock::now() - start
                    ).count();

                cerr
                    << request.method << " "
                    << request.path << " "
                    << response.status << " "
                    << fixed << setprecision(2)
                    << elapsed << "ms\n";

                return response;
            }
        );
    }

    Response handle(Request& request) {
        try {
            return pipeline.execute(
                request,
                [this](Request& context) {
                    return router.dispatch(context);
                }
            );

        } catch (const BackendException& error) {
            return {
                error.status,
                "{\"error\":\"BACKEND_ERROR\",\"message\":\""
                    + jsonEscape(error.what())
                    + "\"}",
                {}
            };

        } catch (const invalid_argument& error) {
            return {
                400,
                "{\"error\":\"VALIDATION_ERROR\",\"message\":\""
                    + jsonEscape(error.what())
                    + "\"}",
                {}
            };

        } catch (const exception& error) {
            cerr << "Unexpected error: " << error.what() << "\n";

            return {
                500,
                R"({"error":"INTERNAL_ERROR"})",
                {}
            };
        }
    }
};

// ---------------------------------------------------------
// Demonstration and tests
// ---------------------------------------------------------

Request makeRequest(
    const string& method,
    const string& path,
    const map<string, string>& body = {}
) {
    return Request{
        method,
        path,
        {},
        {},
        body,
        ""
    };
}

void expect(
    bool condition,
    const string& message
) {
    if (!condition) {
        throw runtime_error(
            "Test failed: " + message
        );
    }

    cout << "[PASS] " << message << "\n";
}

int main() {
    try {
        Application application;

        auto health = makeRequest(
            "GET",
            "/health"
        );

        Response healthResponse =
            application.handle(health);

        expect(
            healthResponse.status == 200,
            "Health endpoint"
        );

        auto create = makeRequest(
            "POST",
            "/api/v1/tasks",
            {
                {"title", "Implement routing"},
                {"description", "Build backend router"}
            }
        );

        Response created = application.handle(create);

        expect(
            created.status == 201,
            "Create task"
        );

        auto list = makeRequest(
            "GET",
            "/api/v1/tasks"
        );

        Response listed = application.handle(list);

        expect(
            listed.status == 200 &&
            listed.body.find("\"count\":1") != string::npos,
            "List tasks"
        );

        auto get = makeRequest(
            "GET",
            "/api/v1/tasks/1"
        );

        Response fetched = application.handle(get);

        expect(
            fetched.status == 200,
            "Retrieve task"
        );

        auto update = makeRequest(
            "PATCH",
            "/api/v1/tasks/1",
            {{"status", "completed"}}
        );

        Response updated = application.handle(update);

        expect(
            updated.status == 200 &&
            updated.body.find("\"completed\"") != string::npos,
            "Update task"
        );

        auto invalid = makeRequest(
            "POST",
            "/api/v1/tasks",
            {{"title", ""}}
        );

        expect(
            application.handle(invalid).status == 400,
            "Reject invalid input"
        );

        auto missing = makeRequest(
            "GET",
            "/api/v1/tasks/999"
        );

        expect(
            application.handle(missing).status == 404,
            "Handle missing resource"
        );

        auto wrongMethod = makeRequest(
            "PUT",
            "/api/v1/tasks"
        );

        expect(
            application.handle(wrongMethod).status == 405,
            "Reject unsupported method"
        );

        auto deletion = makeRequest(
            "DELETE",
            "/api/v1/tasks/1"
        );

        expect(
            application.handle(deletion).status == 200,
            "Delete task"
        );

        auto missingAfterDelete = makeRequest(
            "GET",
            "/api/v1/tasks/1"
        );

        expect(
            application.handle(missingAfterDelete).status == 404,
            "Confirm deletion"
        );

        cout << "\nAll C++17 backend tests passed.\n";

        return 0;

    } catch (const exception& error) {
        cerr << error.what() << "\n";
        return 1;
    }
}
