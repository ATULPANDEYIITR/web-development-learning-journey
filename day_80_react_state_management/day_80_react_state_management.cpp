#include <algorithm>
#include <cstdint>
#include <functional>
#include <iostream>
#include <map>
#include <optional>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

using namespace std;

/*
 * React State Management: Redux Governance Engine
 *
 * Implements:
 * - Centralized application state
 * - Strongly typed actions
 * - Reducer-based transitions
 * - Middleware pipeline
 * - Immutable-style state updates
 * - Selectors
 * - Approval and validation policies
 * - Transactional dispatch
 * - State history
 */

// ============================================================
// 1. Domain Types
// ============================================================

enum class ActionType {
    AddTask,
    ToggleTask,
    RemoveTask,
    Increment,
    SetFilter,
    RequestStarted,
    RequestSucceeded,
    RequestFailed,
    Reset
};

enum class RequestStatus {
    Idle,
    Loading,
    Succeeded,
    Failed
};

enum class TaskFilter {
    All,
    Active,
    Completed
};

struct Task {
    int id;
    string title;
    bool completed = false;
};

struct Action {
    ActionType type;
    int taskId = 0;
    string payload;
};

// ============================================================
// 2. Application State
// ============================================================

struct RequestState {
    RequestStatus status = RequestStatus::Idle;
    string error;
};

struct AppState {
    vector<Task> tasks;
    TaskFilter filter = TaskFilter::All;
    int64_t counter = 0;
    RequestState request;
    uint64_t revision = 0;
};

// ============================================================
// 3. Validation
// ============================================================

class StateException : public runtime_error {
public:
    explicit StateException(const string& message)
        : runtime_error(message) {}
};

void validateTitle(const string& title) {
    if (title.empty() || title.size() > 200) {
        throw StateException("Invalid task title length");
    }

    if (title.find_first_not_of(" \t\n\r") == string::npos) {
        throw StateException("Task title cannot contain only whitespace");
    }
}

bool containsTask(const vector<Task>& tasks, int id) {
    return any_of(
        tasks.begin(),
        tasks.end(),
        [id](const Task& task) {
            return task.id == id;
        }
    );
}

// ============================================================
// 4. Task Reducer
// ============================================================

vector<Task> taskReducer(
    const vector<Task>& current,
    const Action& action
) {
    vector<Task> next = current;

    switch (action.type) {
        case ActionType::AddTask: {
            validateTitle(action.payload);

            if (containsTask(current, action.taskId)) {
                throw StateException("Duplicate task identifier");
            }

            next.push_back({
                action.taskId,
                action.payload,
                false
            });

            break;
        }

        case ActionType::ToggleTask: {
            auto it = find_if(
                next.begin(),
                next.end(),
                [&](const Task& task) {
                    return task.id == action.taskId;
                }
            );

            if (it == next.end()) {
                throw StateException("Task does not exist");
            }

            it->completed = !it->completed;
            break;
        }

        case ActionType::RemoveTask: {
            auto oldSize = next.size();

            next.erase(
                remove_if(
                    next.begin(),
                    next.end(),
                    [&](const Task& task) {
                        return task.id == action.taskId;
                    }
                ),
                next.end()
            );

            if (next.size() == oldSize) {
                throw StateException("Cannot remove missing task");
            }

            break;
        }

        default:
            break;
    }

    return next;
}

// ============================================================
// 5. Root Reducer
// ============================================================

AppState rootReducer(
    const AppState& state,
    const Action& action
) {
    if (action.type == ActionType::Reset) {
        return AppState{};
    }

    AppState next = state;

    next.tasks = taskReducer(state.tasks, action);

    switch (action.type) {
        case ActionType::Increment:
            if (state.counter == INT64_MAX) {
                throw StateException("Counter overflow");
            }

            next.counter++;
            break;

        case ActionType::SetFilter:
            if (action.payload == "all") {
                next.filter = TaskFilter::All;
            } else if (action.payload == "active") {
                next.filter = TaskFilter::Active;
            } else if (action.payload == "completed") {
                next.filter = TaskFilter::Completed;
            } else {
                throw StateException("Unknown filter");
            }
            break;

        case ActionType::RequestStarted:
            next.request = {
                RequestStatus::Loading,
                ""
            };
            break;

        case ActionType::RequestSucceeded:
            next.request = {
                RequestStatus::Succeeded,
                ""
            };
            break;

        case ActionType::RequestFailed:
            next.request = {
                RequestStatus::Failed,
                action.payload
            };
            break;

        default:
            break;
    }

    next.revision = state.revision + 1;

    return next;
}

// ============================================================
// 6. Middleware Pipeline
// ============================================================

using NextDispatch = function<void(const Action&)>;
using Middleware = function<void(
    const AppState&,
    const Action&,
    const NextDispatch&
)>;

void loggerMiddleware(
    const AppState& state,
    const Action& action,
    const NextDispatch& next
) {
    cout << "[LOG] Action received at revision "
         << state.revision << '\n';

    next(action);
}

void validationMiddleware(
    const AppState& state,
    const Action& action,
    const NextDispatch& next
) {
    (void)state;

    if (action.type == ActionType::AddTask) {
        validateTitle(action.payload);
    }

    next(action);
}

// ============================================================
// 7. Redux Store
// ============================================================

class Store {
private:
    AppState state;
    vector<Middleware> middlewares;
    vector<function<void(const AppState&, const Action&)>> listeners;
    vector<AppState> history;

    bool dispatching = false;

public:
    Store() = default;

    const AppState& getState() const {
        return state;
    }

    void addMiddleware(Middleware middleware) {
        middlewares.push_back(move(middleware));
    }

    void subscribe(
        function<void(const AppState&, const Action&)> listener
    ) {
        listeners.push_back(move(listener));
    }

    void dispatch(const Action& action) {
        if (dispatching) {
            throw StateException("Nested reducer dispatch");
        }

        AppState previous = state;

        NextDispatch reducerDispatch = [&](const Action& currentAction) {
            if (dispatching) {
                throw StateException("Reducer dispatch is already active");
            }

            dispatching = true;

            try {
                AppState next = rootReducer(state, currentAction);

                // Commit only after the complete reducer succeeds.
                history.push_back(state);
                state = move(next);

                dispatching = false;

            } catch (...) {
                dispatching = false;
                throw;
            }
        };

        NextDispatch chain = reducerDispatch;

        for (auto it = middlewares.rbegin();
             it != middlewares.rend();
             ++it) {

            Middleware middleware = *it;
            NextDispatch next = chain;

            chain = [
                this,
                middleware,
                next
            ](const Action& currentAction) {
                middleware(state, currentAction, next);
            };
        }

        chain(action);

        if (state.revision != previous.revision) {
            for (const auto& listener : listeners) {
                listener(state, action);
            }
        }
    }

    optional<AppState> undo() {
        if (history.empty()) {
            return nullopt;
        }

        state = history.back();
        history.pop_back();

        return state;
    }
};

// ============================================================
// 8. Selectors
// ============================================================

vector<Task> selectVisibleTasks(const AppState& state) {
    vector<Task> result;

    copy_if(
        state.tasks.begin(),
        state.tasks.end(),
        back_inserter(result),
        [&](const Task& task) {
            switch (state.filter) {
                case TaskFilter::Active:
                    return !task.completed;

                case TaskFilter::Completed:
                    return task.completed;

                case TaskFilter::All:
                    return true;
            }

            return false;
        }
    );

    return result;
}

struct TaskStatistics {
    size_t total;
    size_t completed;
    size_t active;
};

TaskStatistics selectStatistics(const AppState& state) {
    size_t completed = count_if(
        state.tasks.begin(),
        state.tasks.end(),
        [](const Task& task) {
            return task.completed;
        }
    );

    return {
        state.tasks.size(),
        completed,
        state.tasks.size() - completed
    };
}

// ============================================================
// 9. Application
// ============================================================

void printTasks(const vector<Task>& tasks) {
    for (const auto& task : tasks) {
        cout << task.id << " | "
             << task.title << " | "
             << (task.completed ? "Completed" : "Active")
             << '\n';
    }
}

int main() {
    try {
        Store store;

        store.addMiddleware(validationMiddleware);
        store.addMiddleware(loggerMiddleware);

        store.subscribe(
            [](const AppState& state, const Action& action) {
                (void)action;

                cout << "[SUBSCRIBER] State revision: "
                     << state.revision << '\n';
            }
        );

        cout << "\n--- ADD TASKS ---\n";

        store.dispatch({
            ActionType::AddTask,
            1,
            "Implement Redux reducers"
        });

        store.dispatch({
            ActionType::AddTask,
            2,
            "Implement middleware"
        });

        store.dispatch({
            ActionType::AddTask,
            3,
            "Write application tests"
        });

        cout << "\n--- UPDATE TASK ---\n";

        store.dispatch({
            ActionType::ToggleTask,
            1
        });

        cout << "\n--- TASK STATISTICS ---\n";

        auto stats = selectStatistics(store.getState());

        cout << "Total: " << stats.total << '\n';
        cout << "Completed: " << stats.completed << '\n';
        cout << "Active: " << stats.active << '\n';

        cout << "\n--- FILTER TASKS ---\n";

        store.dispatch({
            ActionType::SetFilter,
            0,
            "active"
        });

        printTasks(selectVisibleTasks(store.getState()));

        cout << "\n--- INVALID ACTION ---\n";

        try {
            store.dispatch({
                ActionType::AddTask,
                1,
                "Duplicate identifier"
            });
        } catch (const StateException& error) {
            cout << "Rejected: " << error.what() << '\n';
        }

        cout << "\n--- COUNTER ---\n";

        store.dispatch({
            ActionType::Increment
        });

        cout << "Counter: "
             << store.getState().counter << '\n';

        cout << "\n--- UNDO ---\n";

        auto restored = store.undo();

        if (restored) {
            cout << "Restored revision: "
                 << restored->revision << '\n';
        }

        cout << "\n--- FINAL STATE ---\n";

        printTasks(store.getState().tasks);

    } catch (const exception& error) {
        cerr << "Application error: "
             << error.what() << '\n';

        return 1;
    }

    return 0;
}
