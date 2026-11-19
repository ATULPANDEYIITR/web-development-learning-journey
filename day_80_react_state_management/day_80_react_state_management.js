"use strict";

/*
 * React State Management: Redux and Redux Toolkit Concepts
 *
 * Node.js implementation demonstrating:
 * - Redux-style centralized state
 * - Action objects and action creators
 * - Reducers and immutable updates
 * - Middleware composition
 * - Thunk-like asynchronous dispatch
 * - Selectors and derived state
 * - Event-driven subscriptions
 * - Request lifecycle management
 * - Optimistic updates and rollback
 * - State validation
 *
 * Run:
 * node react_state_management.js
 */

const { EventEmitter } = require("node:events");
const crypto = require("node:crypto");

// ============================================================
// 1. Constants and Domain Errors
// ============================================================

const ActionTypes = Object.freeze({
    TASK_ADDED: "tasks/added",
    TASK_TOGGLED: "tasks/toggled",
    TASK_REMOVED: "tasks/removed",
    FILTER_CHANGED: "tasks/filterChanged",
    COUNTER_INCREMENTED: "counter/incremented",
    REQUEST_STARTED: "tasks/requestStarted",
    REQUEST_SUCCEEDED: "tasks/requestSucceeded",
    REQUEST_FAILED: "tasks/requestFailed",
    STATE_RESET: "app/reset"
});

class StateError extends Error {
    constructor(message) {
        super(message);
        this.name = "StateError";
    }
}

// ============================================================
// 2. Initial State
// ============================================================

function initialState() {
    return {
        tasks: [],
        filter: "all",
        counter: 0,
        request: {
            status: "idle",
            error: null
        }
    };
}

// ============================================================
// 3. Action Creators
// ============================================================

const actions = Object.freeze({
    addTask(title) {
        return {
            type: ActionTypes.TASK_ADDED,
            payload: {
                id: crypto.randomUUID(),
                title
            }
        };
    },

    toggleTask(id) {
        return {
            type: ActionTypes.TASK_TOGGLED,
            payload: { id }
        };
    },

    removeTask(id) {
        return {
            type: ActionTypes.TASK_REMOVED,
            payload: { id }
        };
    },

    setFilter(filter) {
        return {
            type: ActionTypes.FILTER_CHANGED,
            payload: filter
        };
    },

    increment() {
        return { type: ActionTypes.COUNTER_INCREMENTED };
    }
});

// ============================================================
// 4. Reducers
// ============================================================

function taskReducer(state, action) {
    switch (action.type) {
        case ActionTypes.TASK_ADDED: {
            const title = action.payload?.title;

            if (typeof title !== "string" || !title.trim()) {
                throw new StateError("Task title is required");
            }

            const id = action.payload.id;

            if (state.some(task => task.id === id)) {
                throw new StateError("Duplicate task identifier");
            }

            return [
                ...state,
                {
                    id,
                    title: title.trim(),
                    completed: false
                }
            ];
        }

        case ActionTypes.TASK_TOGGLED: {
            const id = action.payload?.id;

            if (!state.some(task => task.id === id)) {
                throw new StateError("Task does not exist");
            }

            return state.map(task =>
                task.id === id
                    ? { ...task, completed: !task.completed }
                    : task
            );
        }

        case ActionTypes.TASK_REMOVED: {
            const id = action.payload?.id;

            if (!state.some(task => task.id === id)) {
                throw new StateError("Task does not exist");
            }

            return state.filter(task => task.id !== id);
        }

        default:
            return state;
    }
}

function rootReducer(state, action) {
    if (action.type === ActionTypes.STATE_RESET) {
        return initialState();
    }

    const filter =
        action.type === ActionTypes.FILTER_CHANGED
            ? action.payload
            : state.filter;

    if (!["all", "active", "completed"].includes(filter)) {
        throw new StateError("Invalid filter");
    }

    const counter =
        action.type === ActionTypes.COUNTER_INCREMENTED
            ? state.counter + 1
            : state.counter;

    if (!Number.isSafeInteger(counter)) {
        throw new StateError("Counter exceeds safe integer range");
    }

    let request = state.request;

    switch (action.type) {
        case ActionTypes.REQUEST_STARTED:
            request = { status: "loading", error: null };
            break;

        case ActionTypes.REQUEST_SUCCEEDED:
            request = { status: "succeeded", error: null };
            break;

        case ActionTypes.REQUEST_FAILED:
            request = {
                status: "failed",
                error: String(action.payload)
            };
            break;
    }

    return {
        tasks: taskReducer(state.tasks, action),
        filter,
        counter,
        request
    };
}

// ============================================================
// 5. Store and Event-Driven Notifications
// ============================================================

class ReduxStore extends EventEmitter {
    #state;
    #reducer;
    #dispatching = false;

    constructor(reducer, state = initialState()) {
        super();

        this.#reducer = reducer;
        this.#state = state;
    }

    getState() {
        return this.#state;
    }

    dispatch(action) {
        if (
            !action ||
            typeof action !== "object" ||
            typeof action.type !== "string" ||
            !action.type
        ) {
            throw new StateError("Invalid action");
        }

        if (typeof action === "function") {
            throw new StateError("Function actions require thunk middleware");
        }

        if (this.#dispatching) {
            throw new StateError("Nested reducer dispatch is prohibited");
        }

        this.#dispatching = true;

        let nextState;

        try {
            nextState = this.#reducer(this.#state, action);

            if (!nextState || typeof nextState !== "object") {
                throw new StateError("Reducer returned invalid state");
            }

            this.#state = Object.freeze(nextState);

        } finally {
            this.#dispatching = false;
        }

        this.emit("change", this.#state, action);

        return action;
    }

    subscribe(listener) {
        this.on("change", listener);

        return () => this.off("change", listener);
    }
}

// ============================================================
// 6. Middleware Composition
// ============================================================

const loggerMiddleware = store => next => action => {
    console.log(`[ACTION] ${action.type}`);

    const previous = store.getState();

    const result = next(action);

    console.log(
        `[STATE] ${previous.counter} -> ${store.getState().counter}`
    );

    return result;
};

const validationMiddleware = () => next => action => {
    if (!action || typeof action.type !== "string") {
        throw new StateError("Action validation failed");
    }

    return next(action);
};

const thunkMiddleware = store => next => action => {
    if (typeof action === "function") {
        return action(store.dispatch, store.getState);
    }

    return next(action);
};

function applyMiddleware(store, ...middlewares) {
    const baseDispatch = store.dispatch.bind(store);

    const api = {
        getState: store.getState.bind(store),
        dispatch: action => store.dispatch(action)
    };

    const chain = middlewares.map(
        middleware => middleware(api)
    );

    const enhancedDispatch = chain
        .map(middleware => middleware)
        .reduceRight(
            (next, middleware) => middleware(next),
            baseDispatch
        );

    store.dispatch = enhancedDispatch;

    return store;
}

// ============================================================
// 7. Selectors and Memoization
// ============================================================

function createSelector(inputSelector, resultFunction) {
    let previousInput;
    let previousResult;

    return state => {
        const input = inputSelector(state);

        if (input === previousInput) {
            return previousResult;
        }

        previousInput = input;
        previousResult = resultFunction(input);

        return previousResult;
    };
}

const selectTasks = createSelector(
    state => state.tasks,
    tasks => tasks.map(task => ({ ...task }))
);

function selectVisibleTasks(state) {
    const tasks = state.tasks;

    switch (state.filter) {
        case "active":
            return tasks.filter(task => !task.completed);

        case "completed":
            return tasks.filter(task => task.completed);

        default:
            return tasks;
    }
}

const selectStatistics = createSelector(
    state => state.tasks,
    tasks => {
        const completed = tasks.filter(
            task => task.completed
        ).length;

        return {
            total: tasks.length,
            completed,
            active: tasks.length - completed
        };
    }
);

// ============================================================
// 8. Asynchronous Thunk
// ============================================================

function fetchTasks(api) {
    return async dispatch => {
        dispatch({ type: ActionTypes.REQUEST_STARTED });

        const controller = new AbortController();

        try {
            const response = await fetch(api, {
                signal: controller.signal,
                headers: {
                    Accept: "application/json"
                }
            });

            if (!response.ok) {
                throw new Error(
                    `HTTP request failed: ${response.status}`
                );
            }

            const data = await response.json();

            if (!Array.isArray(data)) {
                throw new StateError("Expected an array response");
            }

            dispatch({
                type: ActionTypes.REQUEST_SUCCEEDED,
                payload: data
            });

            return data;

        } catch (error) {
            dispatch({
                type: ActionTypes.REQUEST_FAILED,
                payload: error.message
            });

            throw error;
        }
    };
}

// ============================================================
// 9. Optimistic Update Manager
// ============================================================

class OptimisticTaskManager {
    constructor(store) {
        this.store = store;
    }

    async execute(action, remoteOperation) {
        const previousState = this.store.getState();

        this.store.dispatch(action);

        try {
            return await remoteOperation();

        } catch (error) {
            // Roll back only if the failed operation has not been
            // superseded by another state update.
            if (this.store.getState() !== previousState) {
                this.store.dispatch({
                    type: ActionTypes.STATE_RESET
                });
            }

            throw error;
        }
    }
}

// ============================================================
// 10. Application Execution
// ============================================================

async function main() {
    const store = applyMiddleware(
        new ReduxStore(rootReducer),
        validationMiddleware,
        loggerMiddleware,
        thunkMiddleware
    );

    const unsubscribe = store.subscribe(
        (state, action) => {
            console.log(
                `[EVENT] ${action.type}; tasks=${state.tasks.length}`
            );
        }
    );

    console.log("\n--- TASK MANAGEMENT ---");

    store.dispatch(actions.addTask("Study Redux Toolkit"));
    store.dispatch(actions.addTask("Implement reducers"));
    store.dispatch(actions.addTask("Write automated tests"));

    const firstTask = store.getState().tasks[0];

    store.dispatch(actions.toggleTask(firstTask.id));

    console.log("\nVisible tasks:");
    console.table(selectVisibleTasks(store.getState()));

    console.log("\nStatistics:");
    console.log(selectStatistics(store.getState()));

    console.log("\n--- FILTERING ---");

    store.dispatch(actions.setFilter("active"));

    console.log(
        selectVisibleTasks(store.getState())
    );

    console.log("\n--- COUNTER ---");

    store.dispatch(actions.increment());

    console.log("Counter:", store.getState().counter);

    console.log("\n--- VALIDATION ---");

    try {
        store.dispatch(actions.setFilter("unknown"));
    } catch (error) {
        console.log("Expected error:", error.message);
    }

    console.log("\n--- ASYNCHRONOUS ACTION ---");

    try {
        await store.dispatch(
            fetchTasks("https://jsonplaceholder.typicode.com/todos?_limit=3")
        );

        console.log("Request status:", store.getState().request.status);

    } catch (error) {
        console.log("Remote request failed:", error.message);
    }

    console.log("\n--- STATE RESET ---");

    store.dispatch({
        type: ActionTypes.STATE_RESET
    });

    unsubscribe();

    console.log("Final state:", store.getState());
}

main().catch(error => {
    console.error("Application failure:", error);
    process.exitCode = 1;
});
