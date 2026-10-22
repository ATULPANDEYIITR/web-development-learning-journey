#include <algorithm>
#include <chrono>
#include <condition_variable>
#include <exception>
#include <functional>
#include <iostream>
#include <mutex>
#include <optional>
#include <stdexcept>
#include <string>
#include <thread>
#include <utility>
#include <vector>

using namespace std::chrono_literals;

enum class PromiseState {
    Pending,
    Fulfilled,
    Rejected
};

template <typename T>
class Promise {
public:
    using FulfilledHandler = std::function<void(const T&)>;
    using RejectedHandler = std::function<void(const std::exception_ptr&)>;

    Promise() = default;

    void resolve(T value) {
        std::vector<FulfilledHandler> handlers;

        {
            std::lock_guard<std::mutex> lock(mutex_);

            if (state_ != PromiseState::Pending) {
                throw std::logic_error("Promise can be settled only once");
            }

            value_ = std::move(value);
            state_ = PromiseState::Fulfilled;
            handlers = fulfilled_handlers_;
            fulfilled_handlers_.clear();
            rejected_handlers_.clear();
        }

        condition_.notify_all();

        for (auto& handler : handlers) {
            handler(*value_);
        }
    }

    void reject(std::exception_ptr error) {
        std::vector<RejectedHandler> handlers;

        {
            std::lock_guard<std::mutex> lock(mutex_);

            if (state_ != PromiseState::Pending) {
                throw std::logic_error("Promise can be settled only once");
            }

            error_ = error;
            state_ = PromiseState::Rejected;
            handlers = rejected_handlers_;
            fulfilled_handlers_.clear();
            rejected_handlers_.clear();
        }

        condition_.notify_all();

        for (auto& handler : handlers) {
            handler(error_);
        }
    }

    void then(
        FulfilledHandler on_fulfilled,
        RejectedHandler on_rejected
    ) {
        std::optional<T> value;
        std::exception_ptr error;
        PromiseState current_state;

        {
            std::lock_guard<std::mutex> lock(mutex_);
            current_state = state_;

            if (current_state == PromiseState::Pending) {
                fulfilled_handlers_.push_back(std::move(on_fulfilled));
                rejected_handlers_.push_back(std::move(on_rejected));
                return;
            }

            value = value_;
            error = error_;
        }

        if (current_state == PromiseState::Fulfilled) {
            on_fulfilled(*value);
        } else {
            on_rejected(error);
        }
    }

    T get() {
        std::unique_lock<std::mutex> lock(mutex_);
        condition_.wait(lock, [this] {
            return state_ != PromiseState::Pending;
        });

        if (state_ == PromiseState::Rejected) {
            std::rethrow_exception(error_);
        }

        return *value_;
    }

    PromiseState state() const {
        std::lock_guard<std::mutex> lock(mutex_);
        return state_;
    }

private:
    mutable std::mutex mutex_;
    std::condition_variable condition_;

    PromiseState state_ = PromiseState::Pending;
    std::optional<T> value_;
    std::exception_ptr error_;

    std::vector<FulfilledHandler> fulfilled_handlers_;
    std::vector<RejectedHandler> rejected_handlers_;
};

struct ServiceResult {
    std::string service;
    bool success;
    std::string value;
    std::string error;
};

Promise<std::string> asyncService(
    std::string service,
    int delay_ms,
    bool should_fail
) {
    Promise<std::string> promise;

    std::thread([promise = std::move(promise),
                 service = std::move(service),
                 delay_ms,
                 should_fail]() mutable {
        std::this_thread::sleep_for(std::chrono::milliseconds(delay_ms));

        try {
            if (should_fail) {
                throw std::runtime_error(service + " failed");
            }

            promise.resolve(service + " completed");
        } catch (...) {
            promise.reject(std::current_exception());
        }
    }).detach();

    return promise;
}

ServiceResult waitForService(
    const std::string& name,
    int delay,
    bool failure
) {
    try {
        auto promise = asyncService(name, delay, failure);
        return {name, true, promise.get(), ""};
    } catch (const std::exception& ex) {
        return {name, false, "", ex.what()};
    }
}

std::vector<ServiceResult> allSettled(
    const std::vector<std::tuple<std::string, int, bool>>& requests
) {
    std::vector<std::thread> workers;
    std::vector<ServiceResult> results(requests.size());

    for (std::size_t i = 0; i < requests.size(); ++i) {
        auto [name, delay, failure] = requests[i];

        workers.emplace_back(
            [&, i, name, delay, failure] {
                results[i] = waitForService(name, delay, failure);
            }
        );
    }

    for (auto& worker : workers) {
        worker.join();
    }

    return results;
}

ServiceResult race(
    const std::vector<std::tuple<std::string, int, bool>>& requests
) {
    std::mutex mutex;
    std::condition_variable condition;
    bool finished = false;
    ServiceResult winner{};

    std::vector<std::thread> workers;

    for (const auto& [name, delay, failure] : requests) {
        workers.emplace_back(
            [&, name, delay, failure] {
                ServiceResult result = waitForService(name, delay, failure);

                {
                    std::lock_guard<std::mutex> lock(mutex);

                    if (!finished) {
                        finished = true;
                        winner = result;
                    }
                }

                condition.notify_one();
            }
        );
    }

    {
        std::unique_lock<std::mutex> lock(mutex);
        condition.wait(lock, [&] { return finished; });
    }

    for (auto& worker : workers) {
        worker.join();
    }

    return winner;
}

std::optional<ServiceResult> any(
    const std::vector<std::tuple<std::string, int, bool>>& requests
) {
    std::mutex mutex;
    std::condition_variable condition;

    std::size_t completed = 0;
    std::optional<ServiceResult> winner;

    std::vector<std::thread> workers;

    for (const auto& [name, delay, failure] : requests) {
        workers.emplace_back(
            [&, name, delay, failure] {
                ServiceResult result = waitForService(name, delay, failure);

                {
                    std::lock_guard<std::mutex> lock(mutex);

                    ++completed;

                    if (result.success && !winner.has_value()) {
                        winner = result;
                    }
                }

                condition.notify_one();
            }
        );
    }

    {
        std::unique_lock<std::mutex> lock(mutex);
        condition.wait(lock, [&] {
            return winner.has_value() || completed == requests.size();
        });
    }

    for (auto& worker : workers) {
        worker.join();
    }

    return winner;
}

void demonstratePromiseStateMachine() {
    Promise<int> promise;

    promise.then(
        [](const int& value) {
            std::cout << "fulfilled handler: " << value << '\n';
        },
        [](const std::exception_ptr& error) {
            try {
                std::rethrow_exception(error);
            } catch (const std::exception& ex) {
                std::cout << "rejected handler: " << ex.what() << '\n';
            }
        }
    );

    promise.resolve(42);

    try {
        promise.reject(std::make_exception_ptr(
            std::runtime_error("second settlement")
        ));
    } catch (const std::logic_error& ex) {
        std::cout << "settlement protection: " << ex.what() << '\n';
    }
}

int main() {
    try {
        std::cout << "=== Promise state ===\n";
        demonstratePromiseStateMachine();

        std::cout << "\n=== Promise.all-like aggregation ===\n";
        auto all_results = allSettled({
            {"database", 80, false},
            {"cache", 30, false},
            {"queue", 50, false}
        });

        bool all_success = std::all_of(
            all_results.begin(),
            all_results.end(),
            [](const ServiceResult& result) {
                return result.success;
            }
        );

        std::cout << "all successful: "
                  << std::boolalpha << all_success << '\n';

        std::cout << "\n=== Promise.allSettled-like aggregation ===\n";
        auto settled = allSettled({
            {"metrics", 20, false},
            {"audit", 40, true},
            {"cache", 10, false}
        });

        for (const auto& result : settled) {
            if (result.success) {
                std::cout << result.service << ": fulfilled -> "
                          << result.value << '\n';
            } else {
                std::cout << result.service << ": rejected -> "
                          << result.error << '\n';
            }
        }

        std::cout << "\n=== Promise.race-like aggregation ===\n";
        auto race_result = race({
            {"primary", 90, false},
            {"replica", 25, false},
            {"fallback", 60, false}
        });

        std::cout << "race winner: " << race_result.service
                  << " -> " << race_result.value << '\n';

        std::cout << "\n=== Promise.any-like aggregation ===\n";
        auto any_result = any({
            {"region-a", 50, true},
            {"region-b", 30, false},
            {"region-c", 40, true}
        });

        if (any_result.has_value()) {
            std::cout << "any winner: "
                      << any_result->service
                      << " -> "
                      << any_result->value
                      << '\n';
        } else {
            std::cout << "any: all operations rejected\n";
        }

        std::cout << "\n=== Error propagation ===\n";
        auto failing = asyncService("authorization", 20, true);

        try {
            std::cout << failing.get() << '\n';
        } catch (const std::exception& ex) {
            std::cout << "propagated error: " << ex.what() << '\n';
        }

    } catch (const std::exception& ex) {
        std::cerr << "fatal error: " << ex.what() << '\n';
        return 1;
    }

    return 0;
}
