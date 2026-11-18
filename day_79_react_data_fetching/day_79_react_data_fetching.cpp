#include <algorithm>
#include <chrono>
#include <cstdint>
#include <functional>
#include <iostream>
#include <map>
#include <memory>
#include <optional>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

using namespace std;

using Clock = chrono::steady_clock;

// ---------------------------------------------------------
// 1. Domain types
// ---------------------------------------------------------

enum class QueryStatus {
    Idle,
    Loading,
    Success,
    Error
};

enum class HttpMethod {
    Get,
    Post,
    Put,
    Patch,
    Delete
};

string statusName(QueryStatus status) {
    switch (status) {
        case QueryStatus::Idle: return "IDLE";
        case QueryStatus::Loading: return "LOADING";
        case QueryStatus::Success: return "SUCCESS";
        case QueryStatus::Error: return "ERROR";
    }

    return "UNKNOWN";
}

struct APIResponse {
    int statusCode;
    string body;
    string contentType = "application/json";
};

struct QueryState {
    QueryStatus status = QueryStatus::Idle;
    optional<string> data;
    optional<string> error;
    bool isFetching = false;
    uint64_t requestVersion = 0;
};

// ---------------------------------------------------------
// 2. Exceptions
// ---------------------------------------------------------

class FetchException : public runtime_error {
public:
    using runtime_error::runtime_error;
};

class HTTPException : public FetchException {
private:
    int statusCode;

public:
    HTTPException(int code, const string& message)
        : FetchException(message), statusCode(code) {}

    int getStatusCode() const {
        return statusCode;
    }
};

// ---------------------------------------------------------
// 3. Request model
// ---------------------------------------------------------

struct APIRequest {
    string path;
    HttpMethod method = HttpMethod::Get;
    map<string, string> params;
    string body;

    void validate() const {
        if (path.empty() || path.front() != '/') {
            throw invalid_argument(
                "API path must begin with /."
            );
        }

        if (method == HttpMethod::Get && !body.empty()) {
            throw invalid_argument(
                "GET requests cannot contain a request body."
            );
        }
    }

    string cacheKey() const {
        string key = path;

        for (const auto& [name, value] : params) {
            key += "|" + name + "=" + value;
        }

        return key;
    }
};

// ---------------------------------------------------------
// 4. HTTP transport interface
// ---------------------------------------------------------

class Transport {
public:
    virtual ~Transport() = default;

    virtual APIResponse execute(
        const APIRequest& request
    ) = 0;
};

// ---------------------------------------------------------
// 5. Simulated API transport
// ---------------------------------------------------------

class RepositoryAPI : public Transport {
private:
    int calls = 0;

public:
    APIResponse execute(
        const APIRequest& request
    ) override {
        ++calls;

        if (request.path == "/users") {
            return {
                200,
                R"([{"id":1,"name":"Aarav"},{"id":2,"name":"Meera"}])"
            };
        }

        if (request.path == "/empty") {
            return {200, "[]"};
        }

        if (request.path == "/server-error") {
            return {
                503,
                R"({"message":"Service unavailable"})"
            };
        }

        if (request.path == "/unauthorized") {
            return {
                401,
                R"({"message":"Authentication required"})"
            };
        }

        return {
            404,
            R"({"message":"Endpoint not found"})"
        };
    }

    int getCallCount() const {
        return calls;
    }
};

// ---------------------------------------------------------
// 6. Cache entry
// ---------------------------------------------------------

struct CacheEntry {
    string data;
    Clock::time_point updatedAt;
};

// ---------------------------------------------------------
// 7. Cache manager
// ---------------------------------------------------------

class QueryCache {
private:
    unordered_map<string, CacheEntry> entries;
    chrono::milliseconds staleTime;
    size_t maximumEntries;

public:
    QueryCache(
        chrono::milliseconds stale = chrono::seconds(30),
        size_t maximum = 100
    ) : staleTime(stale), maximumEntries(maximum) {
        if (stale.count() < 0 || maximum == 0) {
            throw invalid_argument(
                "Invalid cache configuration."
            );
        }
    }

    optional<string> get(const string& key) {
        auto it = entries.find(key);

        if (it == entries.end()) {
            return nullopt;
        }

        auto age = chrono::duration_cast<
            chrono::milliseconds
        >(
            Clock::now() - it->second.updatedAt
        );

        if (age > staleTime) {
            entries.erase(it);
            return nullopt;
        }

        return it->second.data;
    }

    void set(const string& key, const string& data) {
        if (entries.find(key) == entries.end() &&
            entries.size() >= maximumEntries) {

            auto oldest = entries.begin();

            for (auto it = entries.begin();
                 it != entries.end(); ++it) {

                if (it->second.updatedAt <
                    oldest->second.updatedAt) {
                    oldest = it;
                }
            }

            entries.erase(oldest);
        }

        entries[key] = {
            data,
            Clock::now()
        };
    }

    void invalidate(const string& key) {
        entries.erase(key);
    }

    void clear() {
        entries.clear();
    }
};

// ---------------------------------------------------------
// 8. Query engine
// ---------------------------------------------------------

class QueryEngine {
private:
    shared_ptr<Transport> transport;
    QueryCache cache;

    unordered_map<string, QueryState> states;

    unordered_map<
        string,
        vector<function<void(const QueryState&)>>
    > listeners;

    void notify(const string& key) {
        const QueryState& state = states.at(key);

        for (const auto& callback : listeners[key]) {
            callback(state);
        }
    }

    bool isRetryable(int statusCode) const {
        return statusCode == 408 ||
               statusCode == 429 ||
               statusCode >= 500;
    }

public:
    explicit QueryEngine(
        shared_ptr<Transport> api,
        QueryCache queryCache = QueryCache()
    )
        : transport(move(api)),
          cache(move(queryCache)) {

        if (!transport) {
            throw invalid_argument(
                "Transport cannot be null."
            );
        }
    }

    const QueryState& getState(const string& key) {
        return states[key];
    }

    void subscribe(
        const string& key,
        function<void(const QueryState&)> callback
    ) {
        listeners[key].push_back(move(callback));
    }

    optional<string> getCached(
        const string& key
    ) {
        return cache.get(key);
    }

    string fetch(
        const APIRequest& request,
        bool forceRefresh = false,
        int retries = 2
    ) {
        request.validate();

        if (retries < 0) {
            throw invalid_argument(
                "Retry count cannot be negative."
            );
        }

        const string key = request.cacheKey();

        if (!forceRefresh) {
            auto cached = cache.get(key);

            if (cached.has_value()) {
                QueryState& state = states[key];

                state.status = QueryStatus::Success;
                state.data = cached.value();
                state.error.reset();
                state.isFetching = false;

                notify(key);

                return cached.value();
            }
        }

        QueryState& state = states[key];

        state.status = QueryStatus::Loading;
        state.isFetching = true;
        state.error.reset();
        ++state.requestVersion;

        notify(key);

        string result;
        bool successful = false;
        string lastError;

        for (int attempt = 0; attempt <= retries; ++attempt) {
            try {
                APIResponse response =
                    transport->execute(request);

                if (response.statusCode < 200 ||
                    response.statusCode >= 300) {

                    throw HTTPException(
                        response.statusCode,
                        "HTTP " +
                        to_string(response.statusCode)
                    );
                }

                if (
                    response.contentType.find(
                        "application/json"
                    ) == string::npos
                ) {
                    throw FetchException(
                        "Invalid response content type."
                    );
                }

                result = response.body;
                successful = true;
                break;

            } catch (const HTTPException& error) {
                lastError = error.what();

                if (!isRetryable(error.getStatusCode())) {
                    break;
                }

            } catch (const exception& error) {
                lastError = error.what();
            }
        }

        state.isFetching = false;

        if (successful) {
            state.status = QueryStatus::Success;
            state.data = result;
            state.error.reset();

            cache.set(key, result);

            notify(key);

            return result;
        }

        state.status = QueryStatus::Error;
        state.error = lastError;

        notify(key);

        throw FetchException(lastError);
    }

    void invalidate(const APIRequest& request) {
        cache.invalidate(request.cacheKey());
    }
};

// ---------------------------------------------------------
// 9. Application workflow
// ---------------------------------------------------------

int main() {
    try {
        cout << "REACT DATA FETCHING ENGINE\n";
        cout << "==========================\n";

        auto api = make_shared<RepositoryAPI>();

        QueryEngine engine(
            api,
            QueryCache(chrono::seconds(30), 50)
        );

        APIRequest users{
            "/users",
            HttpMethod::Get,
            {},
            ""
        };

        string key = users.cacheKey();

        // Subscribe to state changes.
        engine.subscribe(
            key,
            [](const QueryState& state) {
                cout << "State: "
                     << statusName(state.status)
                     << " | Fetching: "
                     << boolalpha
                     << state.isFetching
                     << '\n';
            }
        );

        cout << "\n1. Initial request\n";

        string response = engine.fetch(users);

        cout << "Response: " << response << '\n';

        cout << "\n2. Cached request\n";

        string cachedResponse = engine.fetch(users);

        cout << "Cache returned: "
             << cachedResponse << '\n';

        cout << "Transport calls: "
             << api->getCallCount() << '\n';

        cout << "\n3. Forced refresh\n";

        engine.fetch(users, true);

        cout << "Transport calls: "
             << api->getCallCount() << '\n';

        cout << "\n4. Empty response\n";

        APIRequest empty{
            "/empty",
            HttpMethod::Get,
            {},
            ""
        };

        cout << "Empty response: "
             << engine.fetch(empty)
             << '\n';

        cout << "\n5. Unauthorized response\n";

        APIRequest unauthorized{
            "/unauthorized",
            HttpMethod::Get,
            {},
            ""
        };

        try {
            engine.fetch(unauthorized);
        } catch (const FetchException& error) {
            cout << "Handled error: "
                 << error.what()
                 << '\n';
        }

        cout << "\n6. Server failure\n";

        APIRequest serverError{
            "/server-error",
            HttpMethod::Get,
            {},
            ""
        };

        try {
            engine.fetch(serverError, true, 2);
        } catch (const FetchException& error) {
            cout << "Handled error: "
                 << error.what()
                 << '\n';
        }

        cout << "\n7. Final state\n";

        cout << "Users: "
             << statusName(engine.getState(key).status)
             << '\n';

        cout << "\nExecution completed.\n";

    } catch (const exception& error) {
        cerr << "Fatal error: "
             << error.what()
             << '\n';

        return 1;
    }

    return 0;
}
