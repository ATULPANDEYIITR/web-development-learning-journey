#include <algorithm>
#include <chrono>
#include <exception>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

enum class HttpMethod {
    GET,
    POST,
    PUT,
    PATCH,
    DELETE_METHOD
};

std::string to_string(HttpMethod method) {
    switch (method) {
        case HttpMethod::GET: return "GET";
        case HttpMethod::POST: return "POST";
        case HttpMethod::PUT: return "PUT";
        case HttpMethod::PATCH: return "PATCH";
        case HttpMethod::DELETE_METHOD: return "DELETE";
    }
    throw std::logic_error("Unknown HTTP method");
}

enum class RequestState {
    CREATED,
    VALIDATED,
    SENT,
    RECEIVED,
    FAILED
};

struct HttpRequest {
    HttpMethod method;
    std::string url;
    std::map<std::string, std::string> headers;
    std::string body;
    RequestState state{RequestState::CREATED};

    void validate() {
        if (url.rfind("http://", 0) != 0 &&
            url.rfind("https://", 0) != 0) {
            throw std::invalid_argument(
                "Only HTTP and HTTPS URLs are supported"
            );
        }

        if (url.find('\r') != std::string::npos ||
            url.find('\n') != std::string::npos) {
            throw std::invalid_argument("Invalid characters in URL");
        }

        for (const auto& [name, value] : headers) {
            if (name.empty()) {
                throw std::invalid_argument("Header name cannot be empty");
            }

            if (name.find('\r') != std::string::npos ||
                name.find('\n') != std::string::npos ||
                value.find('\r') != std::string::npos ||
                value.find('\n') != std::string::npos) {
                throw std::invalid_argument(
                    "CR/LF characters are forbidden in headers"
                );
            }
        }

        if ((method == HttpMethod::GET ||
             method == HttpMethod::DELETE_METHOD) &&
            !body.empty()) {
            throw std::invalid_argument(
                "GET and DELETE requests cannot carry this request body"
            );
        }

        state = RequestState::VALIDATED;
    }
};

struct HttpResponse {
    int status{};
    std::string reason;
    std::map<std::string, std::string> headers;
    std::string body;
    long long duration_ms{};
    RequestState state{RequestState::RECEIVED};

    bool successful() const {
        return status >= 200 && status < 300;
    }
};

class ApiError : public std::runtime_error {
public:
    explicit ApiError(const std::string& message)
        : std::runtime_error(message) {}
};

class MergeEligibilityStyleException : public ApiError {
public:
    explicit MergeEligibilityStyleException(const std::string& message)
        : ApiError(message) {}
};

class RepositoryApi {
private:
    std::map<std::string, std::string> users_{
        {"1", "Anita"},
        {"2", "Rahul"}
    };

    int next_id_{3};

    static std::string json_escape(const std::string& value) {
        std::string result;
        for (char ch : value) {
            if (ch == '"') {
                result += "\\\"";
            } else if (ch == '\\') {
                result += "\\\\";
            } else {
                result += ch;
            }
        }
        return result;
    }

    static std::string extract_name(const std::string& body) {
        const std::string key = "\"name\"";
        const auto key_pos = body.find(key);

        if (key_pos == std::string::npos) {
            return {};
        }

        const auto colon = body.find(':', key_pos + key.size());
        if (colon == std::string::npos) {
            return {};
        }

        const auto first_quote = body.find('"', colon + 1);
        if (first_quote == std::string::npos) {
            return {};
        }

        const auto second_quote = body.find('"', first_quote + 1);
        if (second_quote == std::string::npos) {
            return {};
        }

        return body.substr(
            first_quote + 1,
            second_quote - first_quote - 1
        );
    }

public:
    HttpResponse execute(HttpRequest request) {
        request.validate();
        request.state = RequestState::SENT;

        const auto started = std::chrono::steady_clock::now();

        HttpResponse response;

        switch (request.method) {
            case HttpMethod::GET:
                if (request.url == "/users") {
                    std::ostringstream json;
                    json << "{\"users\":[";
                    bool first = true;

                    for (const auto& [id, name] : users_) {
                        if (!first) {
                            json << ',';
                        }
                        first = false;
                        json << "{\"id\":" << id
                             << ",\"name\":\""
                             << json_escape(name) << "\"}";
                    }

                    json << "]}";

                    response.status = 200;
                    response.reason = "OK";
                    response.headers["Content-Type"] =
                        "application/json";
                    response.body = json.str();
                } else if (request.url == "/health") {
                    response.status = 200;
                    response.reason = "OK";
                    response.headers["Content-Type"] =
                        "application/json";
                    response.body = "{\"status\":\"ok\"}";
                } else {
                    response.status = 404;
                    response.reason = "Not Found";
                    response.headers["Content-Type"] =
                        "application/json";
                    response.body = "{\"error\":\"resource_not_found\"}";
                }
                break;

            case HttpMethod::POST:
                if (request.url != "/users") {
                    response.status = 404;
                    response.reason = "Not Found";
                    response.body =
                        "{\"error\":\"resource_not_found\"}";
                    break;
                }

                {
                    const std::string name = extract_name(request.body);

                    if (name.empty()) {
                        response.status = 422;
                        response.reason = "Unprocessable Entity";
                        response.body =
                            "{\"error\":\"name_is_required\"}";
                    } else {
                        const int id = next_id_++;
                        users_[std::to_string(id)] = name;

                        response.status = 201;
                        response.reason = "Created";
                        response.headers["Content-Type"] =
                            "application/json";

                        std::ostringstream json;
                        json << "{\"id\":" << id
                             << ",\"name\":\""
                             << json_escape(name)
                             << "\",\"created\":true}";
                        response.body = json.str();
                    }
                }
                break;

            case HttpMethod::DELETE_METHOD:
                if (request.url.rfind("/users/", 0) == 0) {
                    const std::string id =
                        request.url.substr(std::string("/users/").size());

                    if (users_.erase(id) == 0) {
                        response.status = 404;
                        response.reason = "Not Found";
                        response.body =
                            "{\"error\":\"user_not_found\"}";
                    } else {
                        response.status = 204;
                        response.reason = "No Content";
                    }
                } else {
                    response.status = 404;
                    response.reason = "Not Found";
                }
                break;

            case HttpMethod::PUT:
            case HttpMethod::PATCH:
                response.status = 405;
                response.reason = "Method Not Allowed";
                response.body =
                    "{\"error\":\"method_not_allowed\"}";
                break;
        }

        const auto finished = std::chrono::steady_clock::now();
        response.duration_ms =
            std::chrono::duration_cast<std::chrono::milliseconds>(
                finished - started
            ).count();

        return response;
    }
};

class ApiGateway {
private:
    RepositoryApi repository_;

    static bool retryable(int status) {
        return status == 408 ||
               status == 429 ||
               status == 500 ||
               status == 502 ||
               status == 503 ||
               status == 504;
    }

public:
    HttpResponse send(HttpRequest request, int max_retries = 2) {
        if (max_retries < 0) {
            throw std::invalid_argument(
                "max_retries cannot be negative"
            );
        }

        for (int attempt = 0; attempt <= max_retries; ++attempt) {
            HttpResponse response = repository_.execute(request);

            if (!retryable(response.status) ||
                attempt == max_retries) {
                return response;
            }
        }

        throw MergeEligibilityStyleException(
            "Request execution unexpectedly ended"
        );
    }
};

void print_response(
    const std::string& operation,
    const HttpResponse& response
) {
    std::cout << operation
              << " -> HTTP "
              << response.status
              << ' '
              << response.reason
              << " ("
              << response.duration_ms
              << " ms)\n";

    if (!response.body.empty()) {
        std::cout << "Body: " << response.body << "\n";
    }
}

int main() {
    try {
        ApiGateway gateway;

        HttpRequest get_users{
            HttpMethod::GET,
            "/users",
            {
                {"Accept", "application/json"},
                {"X-Request-ID", "cpp-001"}
            },
            "",
            RequestState::CREATED
        };

        print_response(
            "GET /users",
            gateway.send(get_users)
        );

        HttpRequest create_user{
            HttpMethod::POST,
            "/users",
            {
                {"Accept", "application/json"},
                {"Content-Type", "application/json"},
                {"X-Request-ID", "cpp-002"}
            },
            "{\"name\":\"Priya\"}",
            RequestState::CREATED
        };

        print_response(
            "POST /users",
            gateway.send(create_user)
        );

        HttpRequest invalid_user{
            HttpMethod::POST,
            "/users",
            {
                {"Content-Type", "application/json"}
            },
            "{\"name\":\"\"}",
            RequestState::CREATED
        };

        print_response(
            "POST /users invalid",
            gateway.send(invalid_user)
        );

        HttpRequest missing_resource{
            HttpMethod::GET,
            "/missing",
            {
                {"Accept", "application/json"}
            },
            "",
            RequestState::CREATED
        };

        print_response(
            "GET /missing",
            gateway.send(missing_resource)
        );

        try {
            HttpRequest unsafe_header{
                HttpMethod::GET,
                "/health",
                {
                    {"X-Unsafe", "good\r\nInjected: true"}
                },
                "",
                RequestState::CREATED
            };

            gateway.send(unsafe_header);
        } catch (const std::exception& error) {
            std::cout
                << "Security validation blocked request: "
                << error.what()
                << '\n';
        }

        try {
            HttpRequest invalid_url{
                HttpMethod::GET,
                "ftp://example.com",
                {},
                "",
                RequestState::CREATED
            };

            gateway.send(invalid_url);
        } catch (const std::exception& error) {
            std::cout
                << "URL validation blocked request: "
                << error.what()
                << '\n';
        }

        return 0;
    } catch (const std::exception& error) {
        std::cerr
            << "Fatal error: "
            << error.what()
            << '\n';
        return 1;
    }
}
