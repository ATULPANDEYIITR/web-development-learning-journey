#include <algorithm>
#include <cassert>
#include <cstdint>
#include <deque>
#include <exception>
#include <functional>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

enum class TaskType {
    Timer,
    IO,
    UserEvent,
    Render
};

struct Task {
    std::string name;
    std::function<void()> callback;
    TaskType type;
    std::int64_t scheduledAt;
    std::uint64_t sequence;
};

class EventLoopError : public std::runtime_error {
public:
    explicit EventLoopError(const std::string& message)
        : std::runtime_error(message) {}
};

class EventLoop {
private:
    std::int64_t now_ = 0;
    std::int64_t frameInterval_;
    std::int64_t nextFrame_;
    std::size_t maxMicrotasks_;

    std::vector<std::string> stack_;
    std::deque<Task> tasks_;
    std::deque<Task> microtasks_;
    std::deque<Task> renderCallbacks_;
    std::vector<std::string> log_;
    std::uint64_t sequence_ = 0;

    void log(const std::string& message) {
        std::ostringstream oss;
        oss << std::setw(4) << std::setfill('0') << now_
            << "ms | " << message;
        log_.push_back(oss.str());
    }

    void runSync(const std::string& name, const std::function<void()>& callback) {
        stack_.push_back(name);
        log("stack-enter " + name);

        try {
            callback();
        } catch (...) {
            log("stack-exception " + name);
            stack_.pop_back();
            throw;
        }

        log("stack-exit " + name);
        stack_.pop_back();
    }

    void runMicrotasks() {
        std::size_t processed = 0;

        while (!microtasks_.empty()) {
            if (processed >= maxMicrotasks_) {
                throw EventLoopError(
                    "Microtask checkpoint exceeded safety limit."
                );
            }

            Task task = microtasks_.front();
            microtasks_.pop_front();

            ++processed;
            runSync(task.name, task.callback);
            log("microtask-complete " + task.name);
        }
    }

    Task* findReadyTask() {
        auto iterator = std::min_element(
            tasks_.begin(),
            tasks_.end(),
            [](const Task& a, const Task& b) {
                if (a.scheduledAt != b.scheduledAt) {
                    return a.scheduledAt < b.scheduledAt;
                }
                return a.sequence < b.sequence;
            }
        );

        if (iterator == tasks_.end() || iterator->scheduledAt > now_) {
            return nullptr;
        }

        return &(*iterator);
    }

    void advanceTime() {
        std::int64_t nextTaskTime = nextFrame_;
        bool foundFutureTask = false;

        for (const auto& task : tasks_) {
            if (task.scheduledAt > now_) {
                nextTaskTime = std::min(nextTaskTime, task.scheduledAt);
                foundFutureTask = true;
            }
        }

        if (!foundFutureTask && tasks_.empty()) {
            now_ = nextFrame_;
        } else {
            now_ = nextTaskTime;
        }
    }

    void renderIfDue() {
        if (now_ < nextFrame_) {
            return;
        }

        log("rendering-opportunity");

        while (!renderCallbacks_.empty()) {
            Task task = renderCallbacks_.front();
            renderCallbacks_.pop_front();

            runSync(task.name, task.callback);
            log("render-complete " + task.name);
        }

        nextFrame_ += frameInterval_;
    }

public:
    explicit EventLoop(
        std::int64_t frameInterval = 16,
        std::size_t maxMicrotasks = 1000
    )
        : frameInterval_(frameInterval),
          nextFrame_(frameInterval),
          maxMicrotasks_(maxMicrotasks) {
        if (frameInterval <= 0 || maxMicrotasks == 0) {
            throw std::invalid_argument("Invalid event-loop limits.");
        }
    }

    void queueMicrotask(
        const std::string& name,
        std::function<void()> callback
    ) {
        microtasks_.push_back({
            name,
            std::move(callback),
            TaskType::IO,
            now_,
            ++sequence_
        });

        log("microtask-queued " + name);
    }

    void queueTask(
        const std::string& name,
        std::function<void()> callback,
        TaskType type,
        std::int64_t delay = 0
    ) {
        if (delay < 0) {
            throw std::invalid_argument("Task delay cannot be negative.");
        }

        tasks_.push_back({
            name,
            std::move(callback),
            type,
            now_ + delay,
            ++sequence_
        });

        log("task-queued " + name);
    }

    void requestRender(
        const std::string& name,
        std::function<void()> callback
    ) {
        renderCallbacks_.push_back({
            name,
            std::move(callback),
            TaskType::Render,
            now_,
            ++sequence_
        });

        log("render-requested " + name);
    }

    std::vector<std::string> run(std::size_t maxTurns = 100) {
        if (maxTurns == 0) {
            throw std::invalid_argument("maxTurns must be positive.");
        }

        std::size_t turns = 0;

        while (
            !tasks_.empty() ||
            !microtasks_.empty() ||
            !renderCallbacks_.empty()
        ) {
            if (++turns > maxTurns) {
                throw EventLoopError("Maximum event-loop turns exceeded.");
            }

            runMicrotasks();

            Task* selected = findReadyTask();

            if (selected == nullptr) {
                advanceTime();
                renderIfDue();
                continue;
            }

            Task task = std::move(*selected);

            auto iterator = std::find_if(
                tasks_.begin(),
                tasks_.end(),
                [&](const Task& candidate) {
                    return candidate.sequence == task.sequence;
                }
            );

            tasks_.erase(iterator);

            runSync(task.name, task.callback);
            log("task-complete " + task.name);

            runMicrotasks();
            renderIfDue();
        }

        return log_;
    }

    std::size_t stackDepth() const {
        return stack_.size();
    }
};

int main() {
    EventLoop loop;

    loop.queueTask(
        "application-start",
        [&loop]() {
            loop.queueMicrotask(
                "promise-reaction",
                [&loop]() {
                    // Microtasks execute after the current stack unwinds.
                    (void)loop;
                }
            );

            loop.queueTask(
                "zero-delay-timer",
                [&loop]() {},
                TaskType::Timer
            );

            loop.requestRender(
                "paint",
                [&loop]() {}
            );
        },
        TaskType::UserEvent
    );

    loop.queueTask(
        "network-response",
        [&loop]() {
            loop.queueMicrotask(
                "response-microtask",
                []() {}
            );
        },
        TaskType::IO,
        5
    );

    const auto trace = loop.run();

    for (const auto& entry : trace) {
        std::cout << entry << '\n';
    }

    // Independent starvation test.
    EventLoop starvationLoop(16, 5);
    int callbackCount = 0;

    std::function<void()> recursive;
    recursive = [&]() {
        ++callbackCount;
        starvationLoop.queueMicrotask(
            "recursive-" + std::to_string(callbackCount),
            recursive
        );
    };

    starvationLoop.queueMicrotask("recursive-0", recursive);

    bool protected = false;

    try {
        starvationLoop.run();
    } catch (const EventLoopError& error) {
        protected = true;
        std::cout << "\nStarvation protection triggered after "
                  << callbackCount << " callbacks: "
                  << error.what() << '\n';
    }

    assert(protected);

    // Ordering invariant: synchronous work precedes its microtask,
    // and that microtask checkpoint precedes the next task.
    EventLoop testLoop;
    std::vector<std::string> observed;

    testLoop.queueTask(
        "test",
        [&]() {
            observed.push_back("sync");

            testLoop.queueMicrotask(
                "microtask",
                [&]() { observed.push_back("microtask"); }
            );

            testLoop.queueTask(
                "task",
                [&]() { observed.push_back("task"); },
                TaskType::IO
            );
        },
        TaskType::UserEvent
    );

    testLoop.run();

    const std::vector<std::string> expected = {
        "sync", "microtask", "task"
    };

    assert(observed == expected);

    std::cout << "Ordering assertion passed.\n";
    return 0;
}
