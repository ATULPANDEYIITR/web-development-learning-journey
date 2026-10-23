#include <algorithm>
#include <chrono>
#include <future>
#include <iomanip>
#include <iostream>
#include <mutex>
#include <optional>
#include <queue>
#include <random>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>

using namespace std;
using namespace std::chrono_literals;

struct TaskResult {
    string name;
    bool success;
    string value;
    string error;
};

class AsyncService {
public:
    explicit AsyncService(string service_name)
        : name_(move(service_name)) {}

    string execute(int delay_ms, bool fail = false) const {
        this_thread::sleep_for(chrono::milliseconds(delay_ms));

        if (fail) {
            throw runtime_error(name_ + " failed");
        }

        return name_ + " response";
    }

private:
    string name_;
};

future<TaskResult> submit(
    const AsyncService& service,
    int delay_ms,
    bool fail = false
) {
    return async(
        launch::async,
        [&service, delay_ms, fail]() -> TaskResult {
            try {
                return {
                    service_name(service),
                    true,
                    service.execute(delay_ms, fail),
                    ""
                };
            } catch (const exception& ex) {
                return {
                    service_name(service),
                    false,
                    "",
                    ex.what()
                };
            }
        }
    );
}

string service_name(const AsyncService& service) {
    // The example keeps result naming separate from service execution.
    // The public API below avoids exposing internal implementation state.
    return typeid(service).name();
}

class NamedAsyncService {
public:
    explicit NamedAsyncService(string name)
        : name_(move(name)) {}

    TaskResult run(int delay_ms, bool fail = false) const {
        try {
            this_thread::sleep_for(chrono::milliseconds(delay_ms));

            if (fail) {
                throw runtime_error(name_ + " failed");
            }

            return {name_, true, name_ + " response", ""};
        } catch (const exception& ex) {
            return {name_, false, "", ex.what()};
        }
    }

private:
    string name_;
};

future<TaskResult> launch_service(
    const NamedAsyncService& service,
    int delay_ms,
    bool fail = false
) {
    return async(
        launch::async,
        [&service, delay_ms, fail] {
            return service.run(delay_ms, fail);
        }
    );
}

vector<TaskResult> execute_parallel() {
    NamedAsyncService database("database");
    NamedAsyncService payments("payments");
    NamedAsyncService inventory("inventory");

    vector<future<TaskResult>> futures;
    futures.push_back(launch_service(database, 150));
    futures.push_back(launch_service(payments, 100, true));
    futures.push_back(launch_service(inventory, 120));

    vector<TaskResult> results;

    for (auto& future : futures) {
        results.push_back(future.get());
    }

    return results;
}

template <typename Function>
auto retry_async_style(Function operation, int attempts)
    -> decltype(operation()) {
    if (attempts < 1) {
        throw invalid_argument("attempts must be positive");
    }

    exception_ptr last_error;

    for (int attempt = 0; attempt < attempts; ++attempt) {
        try {
            return operation().get();
        } catch (...) {
            last_error = current_exception();

            if (attempt + 1 < attempts) {
                this_thread::sleep_for(
                    chrono::milliseconds(30 * (1 << attempt))
                );
            }
        }
    }

    rethrow_exception(last_error);
}

class BoundedExecutor {
public:
    explicit BoundedExecutor(size_t concurrency)
        : concurrency_(concurrency) {
        if (concurrency_ == 0) {
            throw invalid_argument("concurrency must be greater than zero");
        }
    }

    vector<TaskResult> execute(
        const vector<NamedAsyncService>& services
    ) const {
        vector<TaskResult> results(services.size());
        mutex mutex;
        queue<size_t> work;

        for (size_t i = 0; i < services.size(); ++i) {
            work.push(i);
        }

        vector<thread> workers;

        const size_t worker_count =
            min(concurrency_, services.size());

        for (size_t worker = 0; worker < worker_count; ++worker) {
            workers.emplace_back([&]() {
                while (true) {
                    optional<size_t> index;

                    {
                        lock_guard<mutex> lock(mutex);

                        if (work.empty()) {
                            return;
                        }

                        index = work.front();
                        work.pop();
                    }

                    results[*index] = services[*index].run(60);
                }
            });
        }

        for (auto& worker : workers) {
            worker.join();
        }

        return results;
    }

private:
    size_t concurrency_;
};

void print_results(const vector<TaskResult>& results) {
    for (const auto& result : results) {
        cout << left << setw(14) << result.name
             << (result.success ? "SUCCESS" : "FAILED");

        if (result.success) {
            cout << " " << result.value;
        } else {
            cout << " " << result.error;
        }

        cout << '\n';
    }
}

int main() {
    try {
        cout << "Parallel service execution\n";
        print_results(execute_parallel());

        cout << "\nRetrying transient operation\n";

        int attempts = 0;

        auto retry_result = retry_async_style(
            [&attempts]() {
                return async(
                    launch::async,
                    [&attempts]() -> string {
                        ++attempts;

                        if (attempts < 3) {
                            throw runtime_error(
                                "temporary dependency failure"
                            );
                        }

                        return "succeeded after retry";
                    }
                );
            },
            3
        );

        cout << retry_result << '\n';

        cout << "\nBounded concurrency\n";

        vector<NamedAsyncService> services = {
            NamedAsyncService("service-a"),
            NamedAsyncService("service-b"),
            NamedAsyncService("service-c"),
            NamedAsyncService("service-d"),
            NamedAsyncService("service-e")
        };

        BoundedExecutor executor(2);
        print_results(executor.execute(services));

    } catch (const exception& ex) {
        cerr << "Fatal error: " << ex.what() << '\n';
        return 1;
    }

    return 0;
}
