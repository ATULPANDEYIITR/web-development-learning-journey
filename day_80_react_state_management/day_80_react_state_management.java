import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionException;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.function.Function;
import java.util.function.UnaryOperator;
import java.util.stream.Collectors;

/*
 * React State Management: Enterprise Redux Architecture
 *
 * Demonstrates:
 * - Explicit application domain types
 * - Centralized state management
 * - Immutable records
 * - Reducer composition
 * - Action validation
 * - Middleware
 * - Asynchronous service integration
 * - Selectors
 * - Approval-style policy evaluation for state transitions
 * - Optimistic concurrency
 * - State history
 */

// ============================================================
// 1. Domain Exceptions and Enumerations
// ============================================================

class StateValidationException extends RuntimeException {
    public StateValidationException(String message) {
        super(message);
    }
}

class StateConflictException extends RuntimeException {
    public StateConflictException(String message) {
        super(message);
    }
}

enum ActionType {
    TASK_ADDED,
    TASK_COMPLETED,
    TASK_DELETED,
    FILTER_CHANGED,
    COUNTER_INCREMENTED,
    REQUEST_STARTED,
    REQUEST_SUCCEEDED,
    REQUEST_FAILED,
    RESET
}

enum TaskFilter {
    ALL,
    ACTIVE,
    COMPLETED
}

enum RequestStatus {
    IDLE,
    LOADING,
    SUCCEEDED,
    FAILED
}

// ============================================================
// 2. Immutable Domain Models
// ============================================================

record Task(
    String id,
    String title,
    boolean completed
) {
    public Task {
        Objects.requireNonNull(id);
        Objects.requireNonNull(title);

        if (id.isBlank()) {
            throw new StateValidationException(
                "Task identifier cannot be empty"
            );
        }

        if (title.isBlank() || title.length() > 200) {
            throw new StateValidationException(
                "Invalid task title"
            );
        }
    }

    Task complete() {
        return new Task(id, title, true);
    }
}

record RequestState(
    RequestStatus status,
    List<String> data,
    String error
) {
    public RequestState {
        Objects.requireNonNull(status);
        data = List.copyOf(data);
    }

    static RequestState initial() {
        return new RequestState(
            RequestStatus.IDLE,
            List.of(),
            null
        );
    }
}

record AppState(
    List<Task> tasks,
    TaskFilter filter,
    long counter,
    RequestState request,
    long version
) {
    public AppState {
        tasks = List.copyOf(tasks);
        Objects.requireNonNull(filter);
        Objects.requireNonNull(request);

        if (counter < 0) {
            throw new StateValidationException(
                "Counter cannot be negative"
            );
        }
    }

    static AppState initial() {
        return new AppState(
            List.of(),
            TaskFilter.ALL,
            0,
            RequestState.initial(),
            0
        );
    }
}

record Action(
    ActionType type,
    Object payload,
    String correlationId
) {
    public Action {
        Objects.requireNonNull(type);

        if (correlationId == null || correlationId.isBlank()) {
            correlationId = UUID.randomUUID().toString();
        }
    }

    static Action of(ActionType type, Object payload) {
        return new Action(
            type,
            payload,
            UUID.randomUUID().toString()
        );
    }
}

// ============================================================
// 3. Reducer Interface
// ============================================================

@FunctionalInterface
interface Reducer {
    AppState reduce(AppState state, Action action);
}

// ============================================================
// 4. Task Reducer
// ============================================================

class TaskReducer implements Reducer {

    @Override
    public AppState reduce(AppState state, Action action) {
        List<Task> tasks = new ArrayList<>(state.tasks());

        switch (action.type()) {

            case TASK_ADDED -> {
                if (!(action.payload() instanceof Task task)) {
                    throw new StateValidationException(
                        "TASK_ADDED requires a Task"
                    );
                }

                boolean duplicate = tasks.stream()
                    .anyMatch(existing ->
                        existing.id().equals(task.id())
                    );

                if (duplicate) {
                    throw new StateValidationException(
                        "Duplicate task identifier"
                    );
                }

                tasks.add(task);
            }

            case TASK_COMPLETED -> {
                String id = requireString(action.payload());

                int index = findTask(tasks, id);

                tasks.set(index, tasks.get(index).complete());
            }

            case TASK_DELETED -> {
                String id = requireString(action.payload());

                boolean removed = tasks.removeIf(
                    task -> task.id().equals(id)
                );

                if (!removed) {
                    throw new StateValidationException(
                        "Task not found"
                    );
                }
            }

            default -> {
                return state;
            }
        }

        return new AppState(
            tasks,
            state.filter(),
            state.counter(),
            state.request(),
            state.version() + 1
        );
    }

    private static int findTask(List<Task> tasks, String id) {
        for (int i = 0; i < tasks.size(); i++) {
            if (tasks.get(i).id().equals(id)) {
                return i;
            }
        }

        throw new StateValidationException(
            "Task does not exist"
        );
    }

    private static String requireString(Object payload) {
        if (!(payload instanceof String value) || value.isBlank()) {
            throw new StateValidationException(
                "A non-empty task identifier is required"
            );
        }

        return value;
    }
}

// ============================================================
// 5. Root Reducer
// ============================================================

class RootReducer implements Reducer {

    private final TaskReducer taskReducer = new TaskReducer();

    @Override
    public AppState reduce(AppState state, Action action) {
        if (action.type() == ActionType.RESET) {
            return AppState.initial();
        }

        AppState next = taskReducer.reduce(state, action);

        long counter = next.counter();
        TaskFilter filter = next.filter();
        RequestState request = next.request();

        switch (action.type()) {

            case COUNTER_INCREMENTED -> {
                if (counter == Long.MAX_VALUE) {
                    throw new StateValidationException(
                        "Counter overflow"
                    );
                }

                counter++;
            }

            case FILTER_CHANGED -> {
                if (!(action.payload() instanceof TaskFilter value)) {
                    throw new StateValidationException(
                        "Invalid filter payload"
                    );
                }

                filter = value;
            }

            case REQUEST_STARTED -> {
                request = new RequestState(
                    RequestStatus.LOADING,
                    request.data(),
                    null
                );
            }

            case REQUEST_SUCCEEDED -> {
                if (!(action.payload() instanceof List<?> values)) {
                    throw new StateValidationException(
                        "Request payload must be a list"
                    );
                }

                List<String> data = values.stream()
                    .map(value -> {
                        if (!(value instanceof String text)) {
                            throw new StateValidationException(
                                "Invalid request item"
                            );
                        }

                        return text;
                    })
                    .toList();

                request = new RequestState(
                    RequestStatus.SUCCEEDED,
                    data,
                    null
                );
            }

            case REQUEST_FAILED -> {
                request = new RequestState(
                    RequestStatus.FAILED,
                    request.data(),
                    String.valueOf(action.payload())
                );
            }

            default -> {
            }
        }

        return new AppState(
            next.tasks(),
            filter,
            counter,
            request,
            Math.max(state.version(), next.version()) + 1
        );
    }
}

// ============================================================
// 6. Middleware Contract
// ============================================================

interface Middleware {
    void before(AppState state, Action action);

    default void after(AppState state, Action action) {
    }
}

class AuditMiddleware implements Middleware {

    @Override
    public void before(AppState state, Action action) {
        System.out.printf(
            "[AUDIT] Action=%s Correlation=%s Version=%d%n",
            action.type(),
            action.correlationId(),
            state.version()
        );
    }

    @Override
    public void after(AppState state, Action action) {
        System.out.println(
            "[AUDIT] Committed version=" + state.version()
        );
    }
}

class ValidationMiddleware implements Middleware {

    @Override
    public void before(AppState state, Action action) {
        Objects.requireNonNull(action.payload(),
            "Action payload is required for this workflow");
    }
}

// ============================================================
// 7. Enterprise Store
// ============================================================

class EnterpriseStore {

    private final Reducer reducer;
    private final List<Middleware> middlewares =
        new CopyOnWriteArrayList<>();

    private final List<java.util.function.Consumer<AppState>>
        listeners = new CopyOnWriteArrayList<>();

    private final Deque<AppState> history = new ArrayDeque<>();

    private AppState state;
    private boolean dispatching;

    EnterpriseStore(Reducer reducer) {
        this.reducer = Objects.requireNonNull(reducer);
        this.state = AppState.initial();
    }

    public synchronized AppState getState() {
        return state;
    }

    public void addMiddleware(Middleware middleware) {
        middlewares.add(Objects.requireNonNull(middleware));
    }

    public void subscribe(
        java.util.function.Consumer<AppState> listener
    ) {
        listeners.add(listener);
    }

    public synchronized AppState dispatch(Action action) {
        Objects.requireNonNull(action);

        if (dispatching) {
            throw new StateConflictException(
                "Nested reducer dispatch is prohibited"
            );
        }

        AppState previous = state;

        try {
            dispatching = true;

            middlewares.forEach(
                middleware -> middleware.before(state, action)
            );

            AppState next = reducer.reduce(state, action);

            if (next == null) {
                throw new StateValidationException(
                    "Reducer returned null state"
                );
            }

            history.push(state);

            state = next;

            middlewares.forEach(
                middleware -> middleware.after(state, action)
            );

        } catch (RuntimeException exception) {
            state = previous;
            throw exception;

        } finally {
            dispatching = false;
        }

        listeners.forEach(listener -> listener.accept(state));

        return state;
    }

    public synchronized AppState dispatchIfVersionMatches(
        Action action,
        long expectedVersion
    ) {
        if (state.version() != expectedVersion) {
            throw new StateConflictException(
                "State changed before operation could commit"
            );
        }

        return dispatch(action);
    }

    public synchronized AppState undo() {
        if (history.isEmpty()) {
            throw new StateConflictException(
                "No previous state available"
            );
        }

        state = history.pop();

        listeners.forEach(listener -> listener.accept(state));

        return state;
    }
}

// ============================================================
// 8. Selectors
// ============================================================

class TaskSelectors {

    static List<Task> visibleTasks(AppState state) {
        return state.tasks().stream()
            .filter(task -> switch (state.filter()) {
                case ALL -> true;
                case ACTIVE -> !task.completed();
                case COMPLETED -> task.completed();
            })
            .toList();
    }

    static long completedCount(AppState state) {
        return state.tasks().stream()
            .filter(Task::completed)
            .count();
    }

    static double completionPercentage(AppState state) {
        if (state.tasks().isEmpty()) {
            return 0.0;
        }

        return completedCount(state) * 100.0
            / state.tasks().size();
    }
}

// ============================================================
// 9. Asynchronous Service
// ============================================================

class TaskService {

    public CompletableFuture<List<String>> fetchTasks() {
        return CompletableFuture.supplyAsync(() -> {
            try {
                Thread.sleep(100);
            } catch (InterruptedException exception) {
                Thread.currentThread().interrupt();

                throw new CompletionException(exception);
            }

            return List.of(
                "Review application architecture",
                "Validate reducer behavior",
                "Execute integration tests"
            );
        });
    }

    public CompletableFuture<Void> loadInto(
        EnterpriseStore store
    ) {
        store.dispatch(
            Action.of(ActionType.REQUEST_STARTED, "loading")
        );

        return fetchTasks()
            .thenAccept(data ->
                store.dispatch(
                    Action.of(ActionType.REQUEST_SUCCEEDED, data)
                )
            )
            .exceptionally(error -> {
                store.dispatch(
                    Action.of(
                        ActionType.REQUEST_FAILED,
                        error.getMessage()
                    )
                );

                return null;
            });
    }
}

// ============================================================
// 10. Application Entry Point
// ============================================================

public class ReactStateManagement {

    public static void main(String[] args) {
        EnterpriseStore store = new EnterpriseStore(
            new RootReducer()
        );

        store.addMiddleware(new AuditMiddleware());

        store.subscribe(state ->
            System.out.println(
                "[SUBSCRIBER] Version=" + state.version()
            )
        );

        System.out.println("\n--- TASK OPERATIONS ---");

        Task first = new Task(
            "T-001",
            "Implement Redux architecture",
            false
        );

        Task second = new Task(
            "T-002",
            "Write reducer tests",
            false
        );

        store.dispatch(
            Action.of(ActionType.TASK_ADDED, first)
        );

        store.dispatch(
            Action.of(ActionType.TASK_ADDED, second)
        );

        store.dispatch(
            Action.of(ActionType.TASK_COMPLETED, "T-001")
        );

        System.out.println("\n--- SELECTORS ---");

        System.out.println(
            "Visible tasks: "
            + TaskSelectors.visibleTasks(store.getState())
        );

        System.out.println(
            "Completed percentage: "
            + TaskSelectors.completionPercentage(
                store.getState()
            )
        );

        System.out.println("\n--- FILTERING ---");

        store.dispatch(
            Action.of(
                ActionType.FILTER_CHANGED,
                TaskFilter.ACTIVE
            )
        );

        System.out.println(
            TaskSelectors.visibleTasks(store.getState())
        );

        System.out.println("\n--- ASYNC SERVICE ---");

        new TaskService()
            .loadInto(store)
            .join();

        System.out.println(
            "Request status: "
            + store.getState().request().status()
        );

        System.out.println("\n--- INVALID ACTION ---");

        try {
            store.dispatch(
                Action.of(
                    ActionType.TASK_ADDED,
                    "Invalid task payload"
                )
            );
        } catch (StateValidationException exception) {
            System.out.println(
                "Rejected: " + exception.getMessage()
            );
        }

        System.out.println("\n--- OPTIMISTIC CONCURRENCY ---");

        long currentVersion = store.getState().version();

        store.dispatchIfVersionMatches(
            Action.of(ActionType.COUNTER_INCREMENTED, 1),
            currentVersion
        );

        try {
            store.dispatchIfVersionMatches(
                Action.of(ActionType.COUNTER_INCREMENTED, 1),
                currentVersion
            );
        } catch (StateConflictException exception) {
            System.out.println(
                "Conflict detected: " + exception.getMessage()
            );
        }

        System.out.println("\n--- FINAL STATE ---");

        System.out.println(store.getState());
    }
}
