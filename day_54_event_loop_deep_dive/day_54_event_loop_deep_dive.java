import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.Deque;
import java.util.List;
import java.util.Objects;
import java.util.Optional;

/**
 * Deterministic event-loop simulator for Java 17.
 *
 * Execution model:
 * synchronous call stack
 *       |
 *       v
 * microtask checkpoint
 *       |
 *       v
 * one task
 *       |
 *       v
 * microtask checkpoint
 *       |
 *       v
 * rendering opportunity
 */
public class EventLoopDeepDive {

    enum TaskType {
        TIMER,
        IO,
        USER_EVENT,
        RENDER
    }

    record Task(
        String name,
        Runnable callback,
        TaskType type,
        long scheduledAt,
        long sequence
    ) {
        Task {
            Objects.requireNonNull(name);
            Objects.requireNonNull(callback);
            Objects.requireNonNull(type);
            if (scheduledAt < 0 || sequence <= 0) {
                throw new IllegalArgumentException("Invalid task metadata");
            }
        }
    }

    static final class EventLoopException extends RuntimeException {
        EventLoopException(String message) {
            super(message);
        }
    }

    static final class EventLoop {
        private final long frameInterval;
        private final int maxMicrotasks;

        private long now;
        private long nextFrame;
        private long sequence;

        private final Deque<String> stack = new ArrayDeque<>();
        private final Deque<Task> microtasks = new ArrayDeque<>();
        private final List<Task> tasks = new ArrayList<>();
        private final Deque<Task> renderCallbacks = new ArrayDeque<>();
        private final List<String> trace = new ArrayList<>();

        EventLoop(long frameInterval, int maxMicrotasks) {
            if (frameInterval <= 0 || maxMicrotasks <= 0) {
                throw new IllegalArgumentException(
                    "Event-loop limits must be positive"
                );
            }

            this.frameInterval = frameInterval;
            this.maxMicrotasks = maxMicrotasks;
            this.nextFrame = frameInterval;
        }

        void runSync(String name, Runnable callback) {
            Objects.requireNonNull(callback);

            stack.push(name);
            log("stack-enter " + name);

            try {
                callback.run();
            } catch (RuntimeException | Error error) {
                log("stack-exception " + name);
                throw error;
            } finally {
                if (!stack.isEmpty() && stack.peek().equals(name)) {
                    stack.pop();
                }
            }

            log("stack-exit " + name);
        }

        void queueMicrotask(String name, Runnable callback) {
            microtasks.addLast(new Task(
                name,
                callback,
                TaskType.IO,
                now,
                ++sequence
            ));

            log("microtask-queued " + name);
        }

        void queueTask(
            String name,
            Runnable callback,
            TaskType type,
            long delay
        ) {
            if (delay < 0) {
                throw new IllegalArgumentException(
                    "Task delay cannot be negative"
                );
            }

            tasks.add(new Task(
                name,
                callback,
                type,
                now + delay,
                ++sequence
            ));

            log("task-queued " + name + " delay=" + delay + "ms");
        }

        void requestRender(String name, Runnable callback) {
            renderCallbacks.addLast(new Task(
                name,
                callback,
                TaskType.RENDER,
                now,
                ++sequence
            ));

            log("render-requested " + name);
        }

        private void runMicrotasks() {
            int processed = 0;

            while (!microtasks.isEmpty()) {
                if (processed >= maxMicrotasks) {
                    throw new EventLoopException(
                        "Microtask checkpoint exceeded safety limit"
                    );
                }

                Task task = microtasks.removeFirst();
                processed++;

                runSync(task.name(), task.callback());
                log("microtask-complete " + task.name());
            }
        }

        private Optional<Task> nextReadyTask() {
            return tasks.stream()
                .filter(task -> task.scheduledAt() <= now)
                .min(
                    Comparator
                        .comparingLong(Task::scheduledAt)
                        .thenComparingLong(Task::sequence)
                );
        }

        private void advanceTime() {
            long candidate = nextFrame;

            for (Task task : tasks) {
                if (task.scheduledAt() > now) {
                    candidate = Math.min(candidate, task.scheduledAt());
                }
            }

            now = candidate;
        }

        private void renderIfDue() {
            if (now < nextFrame) {
                return;
            }

            log("rendering-opportunity");

            while (!renderCallbacks.isEmpty()) {
                Task task = renderCallbacks.removeFirst();

                runSync(task.name(), task.callback());
                log("render-complete " + task.name());
            }

            nextFrame += frameInterval;
        }

        List<String> run(int maxTurns) {
            if (maxTurns <= 0) {
                throw new IllegalArgumentException(
                    "maxTurns must be positive"
                );
            }

            int turns = 0;

            while (
                !tasks.isEmpty() ||
                !microtasks.isEmpty() ||
                !renderCallbacks.isEmpty()
            ) {
                if (++turns > maxTurns) {
                    throw new EventLoopException(
                        "Maximum event-loop turns exceeded"
                    );
                }

                runMicrotasks();

                Optional<Task> selected = nextReadyTask();

                if (selected.isEmpty()) {
                    advanceTime();
                    renderIfDue();
                    continue;
                }

                Task task = selected.get();
                tasks.remove(task);

                runSync(task.name(), task.callback());
                log("task-complete " + task.name());

                runMicrotasks();
                renderIfDue();
            }

            return List.copyOf(trace);
        }

        private void log(String message) {
            trace.add(
                String.format("%04dms | %s", now, message)
            );
        }
    }

    interface MergeLikePolicy {
        boolean accepts(Task task);
    }

    record ExecutionPolicy(
        boolean allowRendering,
        int maxTurns
    ) implements MergeLikePolicy {
        @Override
        public boolean accepts(Task task) {
            return allowRendering || task.type() != TaskType.RENDER;
        }
    }

    private static EventLoop createScenario() {
        EventLoop loop = new EventLoop(16, 1000);

        loop.queueTask(
            "application-start",
            () -> {
                loop.queueMicrotask(
                    "promise-reaction",
                    () -> loop.queueMicrotask(
                        "nested-promise-reaction",
                        () -> {}
                    )
                );

                loop.queueTask(
                    "zero-delay-timer",
                    () -> {},
                    TaskType.TIMER,
                    0
                );

                loop.requestRender("paint", () -> {});
            },
            TaskType.USER_EVENT,
            0
        );

        loop.queueTask(
            "network-response",
            () -> loop.queueMicrotask(
                "response-microtask",
                () -> {}
            ),
            TaskType.IO,
            5
        );

        return loop;
    }

    private static void testOrdering() {
        EventLoop loop = new EventLoop(16, 100);

        List<String> observed = new ArrayList<>();

        loop.queueTask(
            "test",
            () -> {
                observed.add("sync");

                loop.queueMicrotask(
                    "microtask",
                    () -> observed.add("microtask")
                );

                loop.queueTask(
                    "task",
                    () -> observed.add("task"),
                    TaskType.IO,
                    0
                );
            },
            TaskType.USER_EVENT,
            0
        );

        loop.run(20);

        List<String> expected = List.of(
            "sync",
            "microtask",
            "task"
        );

        if (!observed.equals(expected)) {
            throw new AssertionError(
                "Expected " + expected + ", received " + observed
            );
        }
    }

    private static void demonstrateStarvationProtection() {
        EventLoop loop = new EventLoop(16, 5);
        int[] count = {0};

        Runnable[] recursive = new Runnable[1];

        recursive[0] = () -> {
            count[0]++;

            loop.queueMicrotask(
                "recursive-" + count[0],
                recursive[0]
            );
        };

        loop.queueMicrotask("recursive-0", recursive[0]);

        try {
            loop.run(20);
            throw new AssertionError(
                "Expected microtask starvation protection"
            );
        } catch (EventLoopException expected) {
            System.out.println(
                "Starvation protection triggered after "
                    + count[0]
                    + " callbacks: "
                    + expected.getMessage()
            );
        }
    }

    public static void main(String[] args) {
        EventLoop loop = createScenario();

        for (String entry : loop.run(100)) {
            System.out.println(entry);
        }

        demonstrateStarvationProtection();
        testOrdering();

        System.out.println("Ordering assertion passed.");
    }
}
