/*
 * React Hooks: Java 17 Enterprise Hook Lifecycle Model.
 *
 * This program models the concepts behind:
 * - useRef
 * - useMemo
 * - useCallback
 * - Custom Hooks
 * - State management
 * - Dependency tracking
 * - Component rendering
 * - Hook-order enforcement
 * - Cache lifecycle
 *
 * This is a Java simulation of React hook semantics,
 * not a replacement for the React runtime.
 *
 * Compile:
 * javac ReactHooksEnterprise.java
 *
 * Run:
 * java ReactHooksEnterprise
 */

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import java.util.function.Function;
import java.util.function.IntUnaryOperator;
import java.util.function.Supplier;
import java.util.stream.Collectors;


public class ReactHooksEnterprise {

    // -----------------------------------------------------
    // Domain exceptions
    // -----------------------------------------------------

    static class HookException extends RuntimeException {
        HookException(String message) {
            super(message);
        }
    }

    static class HookOrderException extends HookException {
        HookOrderException(String message) {
            super(message);
        }
    }


    // -----------------------------------------------------
    // Hook types and metrics
    // -----------------------------------------------------

    enum HookType {
        STATE,
        REF,
        MEMO,
        CALLBACK
    }

    static final class Metrics {
        long renders;
        long memoComputations;
        long memoHits;
        long callbackCreations;
        long callbackHits;
        long stateUpdates;

        @Override
        public String toString() {
            return """
                Renders: %d
                Memo computations: %d
                Memo cache hits: %d
                Callback creations: %d
                Callback cache hits: %d
                State updates: %d
                """.formatted(
                    renders,
                    memoComputations,
                    memoHits,
                    callbackCreations,
                    callbackHits,
                    stateUpdates
                );
        }
    }


    // -----------------------------------------------------
    // Dependency handling
    // -----------------------------------------------------

    static final class Dependencies {
        private final List<Object> values;

        Dependencies(Object... values) {
            this.values = Collections.unmodifiableList(
                Arrays.asList(values.clone())
            );
        }

        boolean sameAs(Dependencies other) {
            if (other == null) {
                return false;
            }

            if (values.size() != other.values.size()) {
                throw new HookException(
                    "Dependency count changed between renders."
                );
            }

            for (int i = 0; i < values.size(); i++) {
                if (!sameDependency(values.get(i), other.values.get(i))) {
                    return false;
                }
            }

            return true;
        }

        private static boolean sameDependency(Object left, Object right) {
            if (left == right) {
                return true;
            }

            if (left == null || right == null) {
                return false;
            }

            if (left instanceof Double a && right instanceof Double b) {
                return Double.doubleToLongBits(a) ==
                       Double.doubleToLongBits(b);
            }

            if (
                left instanceof String ||
                left instanceof Number ||
                left instanceof Boolean ||
                left instanceof Enum<?>
            ) {
                return left.equals(right);
            }

            // Mutable objects use reference identity.
            return false;
        }
    }


    // -----------------------------------------------------
    // Hook slot
    // -----------------------------------------------------

    static final class HookSlot {
        final HookType type;
        Object value;
        Dependencies dependencies;
        boolean initialized;

        HookSlot(HookType type) {
            this.type = type;
            this.initialized = false;
        }
    }


    // -----------------------------------------------------
    // Persistent reference
    // -----------------------------------------------------

    static final class Ref<T> {
        private T current;

        Ref(T initial) {
            current = initial;
        }

        T get() {
            return current;
        }

        void set(T value) {
            current = value;
        }
    }


    // -----------------------------------------------------
    // State management
    // -----------------------------------------------------

    static final class State<T> {
        private T value;

        State(T initial) {
            value = initial;
        }

        T get() {
            return value;
        }

        void set(T next) {
            value = next;
        }

        void update(Function<T, T> updater) {
            value = updater.apply(value);
        }
    }


    // -----------------------------------------------------
    // Hook runtime
    // -----------------------------------------------------

    static final class HookRuntime {

        private final String componentName;
        private final List<HookSlot> slots = new ArrayList<>();

        private List<HookType> expectedOrder;

        private int cursor;
        private boolean rendering;

        final Metrics metrics = new Metrics();

        HookRuntime(String componentName) {
            this.componentName = Objects.requireNonNull(componentName);
        }

        private HookSlot next(HookType type) {
            if (!rendering) {
                throw new HookException(
                    "Hooks must execute during rendering."
                );
            }

            int index = cursor++;

            if (index < slots.size()) {
                HookSlot slot = slots.get(index);

                if (slot.type != type) {
                    throw new HookOrderException(
                        "Expected " + slot.type + " but received " + type
                    );
                }

                return slot;
            }

            HookSlot slot = new HookSlot(type);
            slots.add(slot);

            return slot;
        }


        <T> State<T> useState(T initial) {
            HookSlot slot = next(HookType.STATE);

            if (!slot.initialized) {
                slot.value = new State<>(initial);
                slot.initialized = true;
            }

            @SuppressWarnings("unchecked")
            State<T> state = (State<T>) slot.value;

            return state;
        }


        <T> Ref<T> useRef(T initial) {
            HookSlot slot = next(HookType.REF);

            if (!slot.initialized) {
                slot.value = new Ref<>(initial);
                slot.initialized = true;
            }

            @SuppressWarnings("unchecked")
            Ref<T> reference = (Ref<T>) slot.value;

            return reference;
        }


        <T> T useMemo(
            Supplier<T> factory,
            Dependencies dependencies
        ) {
            HookSlot slot = next(HookType.MEMO);

            boolean recompute =
                !slot.initialized ||
                !dependencies.sameAs(slot.dependencies);

            if (recompute) {
                slot.value = Objects.requireNonNull(
                    factory.get(),
                    "Memoized result cannot be null."
                );

                slot.dependencies = dependencies;
                slot.initialized = true;

                metrics.memoComputations++;

            } else {
                metrics.memoHits++;
            }

            @SuppressWarnings("unchecked")
            T result = (T) slot.value;

            return result;
        }


        <T, R> Function<T, R> useCallback(
            Function<T, R> callback,
            Dependencies dependencies
        ) {
            HookSlot slot = next(HookType.CALLBACK);

            boolean recreate =
                !slot.initialized ||
                !dependencies.sameAs(slot.dependencies);

            if (recreate) {
                slot.value = callback;
                slot.dependencies = dependencies;
                slot.initialized = true;

                metrics.callbackCreations++;

            } else {
                metrics.callbackHits++;
            }

            @SuppressWarnings("unchecked")
            Function<T, R> result =
                (Function<T, R>) slot.value;

            return result;
        }


        void validateOrder() {
            List<HookType> actual = slots.stream()
                .map(slot -> slot.type)
                .collect(Collectors.toList());

            if (expectedOrder == null) {
                expectedOrder = List.copyOf(actual);
            } else if (!expectedOrder.equals(actual)) {
                throw new HookOrderException(
                    "Hook ordering changed in " + componentName
                );
            }

            if (cursor != slots.size()) {
                throw new HookOrderException(
                    "Not all registered hooks executed."
                );
            }
        }


        <T> T render(Supplier<T> component) {
            if (rendering) {
                throw new HookException(
                    "Nested rendering is not supported."
                );
            }

            rendering = true;
            cursor = 0;

            try {
                T result = component.get();

                validateOrder();

                metrics.renders++;

                return result;

            } finally {
                rendering = false;
            }
        }

        String getComponentName() {
            return componentName;
        }
    }


    // -----------------------------------------------------
    // Repository domain
    // -----------------------------------------------------

    record Repository(
        int id,
        String name,
        int score
    ) {
        Repository {
            if (id <= 0) {
                throw new IllegalArgumentException(
                    "Repository ID must be positive."
                );
            }

            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException(
                    "Repository name is required."
                );
            }

            if (score < 0 || score > 100) {
                throw new IllegalArgumentException(
                    "Score must be between 0 and 100."
                );
            }
        }
    }


    record DashboardResult(
        int counter,
        int renderNumber,
        Integer previousThreshold,
        List<Repository> repositories,
        Set<Integer> repositoryIds
    ) {}


    // -----------------------------------------------------
    // Custom hooks
    // -----------------------------------------------------

    static int usePrevious(
        HookRuntime runtime,
        int current
    ) {
        Ref<Integer> reference = runtime.useRef(null);

        Integer previous = reference.get();

        reference.set(current);

        return previous == null ? -1 : previous;
    }


    static final class CounterResult {
        final int count;
        final State<Integer> state;
        final Function<Integer, Integer> increment;

        CounterResult(
            int count,
            State<Integer> state,
            Function<Integer, Integer> increment
        ) {
            this.count = count;
            this.state = state;
            this.increment = increment;
        }
    }


    static CounterResult useCounter(
        HookRuntime runtime,
        int initial
    ) {
        State<Integer> state = runtime.useState(initial);

        Function<Integer, Integer> increment =
            runtime.useCallback(
                value -> value + 1,
                new Dependencies()
            );

        return new CounterResult(
            state.get(),
            state,
            increment
        );
    }


    static List<Repository> useFilteredRepositories(
        HookRuntime runtime,
        List<Repository> repositories,
        int minimumScore
    ) {
        return runtime.useMemo(
            () -> repositories.stream()
                .filter(repository ->
                    repository.score() >= minimumScore
                )
                .toList(),

            new Dependencies(
                repositories,
                minimumScore
            )
        );
    }


    // -----------------------------------------------------
    // Enterprise dashboard component
    // -----------------------------------------------------

    static DashboardResult repositoryDashboard(
        HookRuntime runtime,
        List<Repository> repositories,
        int minimumScore
    ) {
        if (minimumScore < 0 || minimumScore > 100) {
            throw new IllegalArgumentException(
                "Minimum score must be between 0 and 100."
            );
        }

        CounterResult counter = useCounter(runtime, 0);

        Ref<Integer> renderNumber = runtime.useRef(0);
        renderNumber.set(renderNumber.get() + 1);

        int previousThreshold = usePrevious(
            runtime,
            minimumScore
        );

        List<Repository> filtered =
            useFilteredRepositories(
                runtime,
                repositories,
                minimumScore
            );

        Set<Integer> ids = runtime.useMemo(
            () -> filtered.stream()
                .map(Repository::id)
                .collect(Collectors.toUnmodifiableSet()),

            new Dependencies(filtered)
        );

        Function<Integer, Boolean> isVisible =
            runtime.useCallback(
                ids::contains,
                new Dependencies(ids)
            );

        // Demonstrate an explicit policy evaluation.
        for (Repository repository : filtered) {
            if (!isVisible.apply(repository.id())) {
                throw new HookException(
                    "Repository visibility policy failed."
                );
            }
        }

        return new DashboardResult(
            counter.count,
            renderNumber.get(),
            previousThreshold == -1 ? null : previousThreshold,
            filtered,
            ids
        );
    }


    // -----------------------------------------------------
    // Tests
    // -----------------------------------------------------

    static void require(boolean condition, String message) {
        if (!condition) {
            throw new AssertionError(message);
        }
    }


    static void testReferencePersistence() {
        HookRuntime runtime = new HookRuntime("RefTest");

        Ref<Integer> first = runtime.render(
            () -> runtime.useRef(10)
        );

        first.set(99);

        Ref<Integer> second = runtime.render(
            () -> runtime.useRef(10)
        );

        require(first == second, "Reference identity failed.");
        require(second.get() == 99, "Reference value failed.");
    }


    static void testMemoization() {
        HookRuntime runtime = new HookRuntime("MemoTest");

        int[] calculations = {0};

        Supplier<Integer> firstComponent = () ->
            runtime.useMemo(
                () -> {
                    calculations[0]++;
                    return 500;
                },
                new Dependencies(10)
            );

        runtime.render(firstComponent);
        runtime.render(firstComponent);

        require(calculations[0] == 1, "Memo cache failed.");
        require(runtime.metrics.memoHits == 1, "Memo hit failed.");
    }


    static void testCallbackIdentity() {
        HookRuntime runtime = new HookRuntime("CallbackTest");

        Function<Integer, Integer> first = runtime.render(
            () -> runtime.useCallback(
                value -> value * 2,
                new Dependencies(5)
            )
        );

        Function<Integer, Integer> second = runtime.render(
            () -> runtime.useCallback(
                value -> value * 2,
                new Dependencies(5)
            )
        );

        require(first == second, "Callback identity failed.");
        require(first.apply(10) == 20, "Callback result failed.");
    }


    static void testDependencyValidation() {
        HookRuntime runtime = new HookRuntime("DependencyTest");

        runtime.render(
            () -> runtime.useMemo(
                () -> 10,
                new Dependencies(1, 2)
            )
        );

        boolean detected = false;

        try {
            runtime.render(
                () -> runtime.useMemo(
                    () -> 10,
                    new Dependencies(1, 2, 3)
                )
            );
        } catch (HookException exception) {
            detected = true;
        }

        require(detected, "Dependency length validation failed.");
    }


    static void testHookOrder() {
        HookRuntime runtime = new HookRuntime("OrderTest");

        runtime.render(
            () -> runtime.useRef(1)
        );

        boolean detected = false;

        try {
            runtime.render(
                () -> runtime.useState(1)
            );
        } catch (HookOrderException exception) {
            detected = true;
        }

        require(detected, "Hook-order validation failed.");
    }


    static void runTests() {
        testReferencePersistence();
        testMemoization();
        testCallbackIdentity();
        testDependencyValidation();
        testHookOrder();

        System.out.println("All Java 17 tests passed.");
    }


    // -----------------------------------------------------
    // Application entry point
    // -----------------------------------------------------

    public static void main(String[] args) {
        try {
            runTests();

            HookRuntime runtime = new HookRuntime(
                "EnterpriseRepositoryDashboard"
            );

            List<Repository> repositories = List.of(
                new Repository(1, "Portfolio Manager", 95),
                new Repository(2, "Security Monitor", 83),
                new Repository(3, "Data Pipeline", 76),
                new Repository(4, "Research Engine", 61),
                new Repository(5, "Analytics Service", 91)
            );

            for (int threshold : List.of(70, 70, 85, 85)) {
                DashboardResult result = runtime.render(
                    () -> repositoryDashboard(
                        runtime,
                        repositories,
                        threshold
                    )
                );

                System.out.println(
                    "\nDashboard render " + result.renderNumber()
                );

                System.out.println(
                    "Minimum score: " + threshold
                );

                System.out.println(
                    "Previous threshold: " +
                    result.previousThreshold()
                );

                result.repositories().forEach(repository ->
                    System.out.printf(
                        "  %-24s %3d%n",
                        repository.name(),
                        repository.score()
                    )
                );
            }

            System.out.println("\nRuntime metrics:");
            System.out.println(runtime.metrics);

        } catch (Exception exception) {
            System.err.println(
                "Application failure: " + exception.getMessage()
            );

            System.exit(1);
        }
    }
}
