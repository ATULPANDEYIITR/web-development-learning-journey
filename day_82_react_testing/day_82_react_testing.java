/*
 * React Testing: Unit Tests, Component Tests, Mocking,
 * User Interaction Testing, and Test Governance.
 *
 * Java 17 enterprise testing model.
 *
 * Compile:
 *   javac ReactTesting.java
 *
 * Run:
 *   java ReactTesting
 *
 * This program models test organization, dependency isolation,
 * component contracts, execution policies, and test reporting.
 */

import java.time.Duration;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.concurrent.Callable;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Predicate;
import java.util.stream.Collectors;


// ============================================================
// 1. MAIN APPLICATION
// ============================================================

public class ReactTesting {

    public static void main(String[] args) {

        TestRegistry registry = new TestRegistry();

        registerUnitTests(registry);
        registerComponentTests(registry);
        registerInteractionTests(registry);
        registerMockingTests(registry);

        TestReport report = registry.execute();

        System.out.println("\nENTERPRISE TEST REPORT");
        System.out.println("======================");

        System.out.println("Executed: " + report.total());
        System.out.println("Passed: " + report.passed());
        System.out.println("Failed: " + report.failed());
        System.out.println("Duration: " + report.duration());

        System.out.println(
            "Result: " +
            (report.successful() ? "PASSED" : "FAILED")
        );

        if (!report.successful()) {
            System.exit(1);
        }
    }


// ============================================================
// 2. DOMAIN TYPES
// ============================================================

    enum TestCategory {
        UNIT,
        COMPONENT,
        INTERACTION,
        MOCKING
    }

    enum ComponentStatus {
        IDLE,
        LOADING,
        SUCCESS,
        ERROR
    }

    enum TestStatus {
        PASSED,
        FAILED
    }

    record User(
        int id,
        String name,
        String email,
        boolean active
    ) {
        User {
            if (id <= 0) {
                throw new IllegalArgumentException(
                    "User ID must be positive"
                );
            }

            Objects.requireNonNull(name);
            Objects.requireNonNull(email);

            if (name.isBlank()) {
                throw new IllegalArgumentException(
                    "Name cannot be empty"
                );
            }
        }
    }

    record TestResult(
        String name,
        TestCategory category,
        TestStatus status,
        String message,
        Duration duration
    ) {}

    record TestReport(
        int total,
        int passed,
        int failed,
        Duration duration,
        List<TestResult> results
    ) {
        boolean successful() {
            return failed == 0;
        }
    }


// ============================================================
// 3. CUSTOM EXCEPTIONS
// ============================================================

    static class TestExecutionException
        extends RuntimeException {

        TestExecutionException(
            String message,
            Throwable cause
        ) {
            super(message, cause);
        }
    }

    static class DependencyException
        extends RuntimeException {

        DependencyException(String message) {
            super(message);
        }
    }


// ============================================================
// 4. ASSERTION FRAMEWORK
// ============================================================

    @FunctionalInterface
    interface TestOperation {
        void execute() throws Exception;
    }

    static class Assertions {

        static void assertTrue(
            boolean condition,
            String message
        ) {
            if (!condition) {
                throw new AssertionError(message);
            }
        }

        static void assertFalse(
            boolean condition,
            String message
        ) {
            assertTrue(!condition, message);
        }

        static void assertEquals(
            Object actual,
            Object expected,
            String message
        ) {
            if (!Objects.equals(actual, expected)) {
                throw new AssertionError(
                    message +
                    " | expected=" + expected +
                    ", actual=" + actual
                );
            }
        }

        static void assertThrows(
            Class<? extends Throwable> expected,
            TestOperation operation
        ) {
            try {
                operation.execute();
            } catch (Throwable actual) {
                if (expected.isInstance(actual)) {
                    return;
                }

                throw new AssertionError(
                    "Unexpected exception: " +
                    actual.getClass().getName()
                );
            }

            throw new AssertionError(
                "Expected exception was not thrown"
            );
        }
    }


// ============================================================
// 5. TEST REGISTRY AND RUNNER
// ============================================================

    record RegisteredTest(
        String name,
        TestCategory category,
        TestOperation operation
    ) {}

    static class TestRegistry {

        private final List<RegisteredTest> tests =
            new ArrayList<>();

        void register(
            String name,
            TestCategory category,
            TestOperation operation
        ) {
            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException(
                    "Test name is required"
                );
            }

            Objects.requireNonNull(category);
            Objects.requireNonNull(operation);

            if (tests.stream().anyMatch(
                test -> test.name().equals(name)
            )) {
                throw new IllegalArgumentException(
                    "Duplicate test name: " + name
                );
            }

            tests.add(
                new RegisteredTest(name, category, operation)
            );
        }

        TestReport execute() {
            long start = System.nanoTime();

            List<TestResult> results = new ArrayList<>();

            for (RegisteredTest test : tests) {
                long testStart = System.nanoTime();

                try {
                    test.operation().execute();

                    results.add(new TestResult(
                        test.name(),
                        test.category(),
                        TestStatus.PASSED,
                        "Passed",
                        Duration.ofNanos(
                            System.nanoTime() - testStart
                        )
                    ));

                } catch (Throwable error) {
                    results.add(new TestResult(
                        test.name(),
                        test.category(),
                        TestStatus.FAILED,
                        error.getMessage(),
                        Duration.ofNanos(
                            System.nanoTime() - testStart
                        )
                    ));
                }
            }

            int passed = (int) results.stream()
                .filter(r -> r.status() == TestStatus.PASSED)
                .count();

            int failed = results.size() - passed;

            return new TestReport(
                results.size(),
                passed,
                failed,
                Duration.ofNanos(System.nanoTime() - start),
                Collections.unmodifiableList(results)
            );
        }
    }


// ============================================================
// 6. PURE FUNCTIONS
// ============================================================

    static boolean validateEmail(String email) {
        if (email == null || email.isBlank()) {
            return false;
        }

        if (email.length() > 254 ||
            email.contains(" ")) {
            return false;
        }

        String[] parts = email.split("@", -1);

        if (parts.length != 2 ||
            parts[0].isEmpty() ||
            parts[0].length() > 64) {
            return false;
        }

        String domain = parts[1];

        return domain.contains(".") &&
               !domain.startsWith(".") &&
               !domain.endsWith(".");
    }

    static List<User> searchUsers(
        List<User> users,
        String query
    ) {
        Objects.requireNonNull(users);
        Objects.requireNonNull(query);

        String normalized = query
            .trim()
            .toLowerCase();

        if (normalized.isEmpty()) {
            return List.copyOf(users);
        }

        return users.stream()
            .filter(user ->
                user.name().toLowerCase().contains(normalized) ||
                user.email().toLowerCase().contains(normalized)
            )
            .collect(Collectors.toUnmodifiableList());
    }


// ============================================================
// 7. DEPENDENCY CONTRACT
// ============================================================

    interface UserRepository {
        List<User> fetchUsers();
    }


// ============================================================
// 8. MOCK IMPLEMENTATION
// ============================================================

    static class MockUserRepository
        implements UserRepository {

        private final List<User> users;
        private final boolean shouldFail;
        private final AtomicInteger calls =
            new AtomicInteger();

        MockUserRepository(
            List<User> users,
            boolean shouldFail
        ) {
            this.users = List.copyOf(users);
            this.shouldFail = shouldFail;
        }

        @Override
        public List<User> fetchUsers() {
            calls.incrementAndGet();

            if (shouldFail) {
                throw new DependencyException(
                    "Mock repository unavailable"
                );
            }

            return new ArrayList<>(users);
        }

        int getCallCount() {
            return calls.get();
        }
    }


// ============================================================
// 9. COMPONENT BEHAVIOR MODEL
// ============================================================

    static class UserDirectory {

        private final UserRepository repository;

        private List<User> users = List.of();

        private ComponentStatus status =
            ComponentStatus.IDLE;

        private String searchQuery = "";
        private String error = "";

        private java.util.function.Consumer<User> onSelect =
            user -> {};

        UserDirectory(UserRepository repository) {
            this.repository = Objects.requireNonNull(
                repository,
                "Repository cannot be null"
            );
        }

        void setSelectionHandler(
            java.util.function.Consumer<User> handler
        ) {
            this.onSelect = Objects.requireNonNull(handler);
        }

        void mount() {
            status = ComponentStatus.LOADING;
            error = "";

            try {
                List<User> response = repository.fetchUsers();

                if (response == null) {
                    throw new DependencyException(
                        "Repository returned null"
                    );
                }

                users = List.copyOf(response);
                status = ComponentStatus.SUCCESS;

            } catch (RuntimeException exception) {
                status = ComponentStatus.ERROR;
                error = exception.getMessage();
            }
        }

        void search(String query) {
            if (query == null) {
                throw new IllegalArgumentException(
                    "Search query cannot be null"
                );
            }

            searchQuery = query;
        }

        List<User> getVisibleUsers() {
            return searchUsers(users, searchQuery);
        }

        void selectUser(int userId) {
            Optional<User> selected =
                getVisibleUsers().stream()
                    .filter(user -> user.id() == userId)
                    .findFirst();

            if (selected.isEmpty()) {
                throw new IllegalArgumentException(
                    "User is not available in current results"
                );
            }

            onSelect.accept(selected.get());
        }

        ComponentStatus getStatus() {
            return status;
        }

        String getError() {
            return error;
        }

        String render() {
            return switch (status) {
                case IDLE -> "Not mounted";
                case LOADING -> "Loading users...";
                case ERROR -> "Error: " + error;
                case SUCCESS -> getVisibleUsers().isEmpty()
                    ? "No users found"
                    : "User list rendered";
            };
        }
    }


// ============================================================
// 10. TEST FIXTURES
// ============================================================

    static List<User> sampleUsers() {
        return List.of(
            new User(
                1,
                "Alice Johnson",
                "alice@example.com",
                true
            ),
            new User(
                2,
                "Bob Smith",
                "bob@example.com",
                true
            ),
            new User(
                3,
                "Charlie Brown",
                "charlie@example.com",
                false
            )
        );
    }


// ============================================================
// 11. UNIT TESTS
// ============================================================

    static void registerUnitTests(TestRegistry registry) {

        registry.register(
            "Valid email",
            TestCategory.UNIT,
            () -> Assertions.assertTrue(
                validateEmail("alice@example.com"),
                "Valid email rejected"
            )
        );

        registry.register(
            "Invalid email",
            TestCategory.UNIT,
            () -> Assertions.assertFalse(
                validateEmail("alice@@example.com"),
                "Invalid email accepted"
            )
        );

        registry.register(
            "Null email",
            TestCategory.UNIT,
            () -> Assertions.assertFalse(
                validateEmail(null),
                "Null email accepted"
            )
        );

        registry.register(
            "Search by name",
            TestCategory.UNIT,
            () -> Assertions.assertEquals(
                searchUsers(sampleUsers(), "alice").size(),
                1,
                "Search by name failed"
            )
        );

        registry.register(
            "Case insensitive search",
            TestCategory.UNIT,
            () -> Assertions.assertEquals(
                searchUsers(sampleUsers(), "BOB").size(),
                1,
                "Case insensitive search failed"
            )
        );

        registry.register(
            "Empty search",
            TestCategory.UNIT,
            () -> Assertions.assertEquals(
                searchUsers(sampleUsers(), "").size(),
                3,
                "Empty search failed"
            )
        );

        registry.register(
            "No matching users",
            TestCategory.UNIT,
            () -> Assertions.assertTrue(
                searchUsers(sampleUsers(), "unknown").isEmpty(),
                "Unexpected result"
            )
        );
    }


// ============================================================
// 12. COMPONENT TESTS
// ============================================================

    static void registerComponentTests(TestRegistry registry) {

        registry.register(
            "Component initial state",
            TestCategory.COMPONENT,
            () -> {
                UserDirectory component =
                    new UserDirectory(
                        new MockUserRepository(sampleUsers(), false)
                    );

                Assertions.assertEquals(
                    component.getStatus(),
                    ComponentStatus.IDLE,
                    "Incorrect initial state"
                );
            }
        );

        registry.register(
            "Successful component mount",
            TestCategory.COMPONENT,
            () -> {
                UserDirectory component =
                    new UserDirectory(
                        new MockUserRepository(sampleUsers(), false)
                    );

                component.mount();

                Assertions.assertEquals(
                    component.getStatus(),
                    ComponentStatus.SUCCESS,
                    "Component failed to load"
                );

                Assertions.assertEquals(
                    component.getVisibleUsers().size(),
                    3,
                    "Incorrect user count"
                );
            }
        );

        registry.register(
            "Component error state",
            TestCategory.COMPONENT,
            () -> {
                UserDirectory component =
                    new UserDirectory(
                        new MockUserRepository(List.of(), true)
                    );

                component.mount();

                Assertions.assertEquals(
                    component.getStatus(),
                    ComponentStatus.ERROR,
                    "Error state missing"
                );

                Assertions.assertTrue(
                    component.getError().contains("unavailable"),
                    "Error details missing"
                );
            }
        );

        registry.register(
            "Empty component state",
            TestCategory.COMPONENT,
            () -> {
                UserDirectory component =
                    new UserDirectory(
                        new MockUserRepository(List.of(), false)
                    );

                component.mount();

                Assertions.assertEquals(
                    component.render(),
                    "No users found",
                    "Empty state incorrect"
                );
            }
        );

        registry.register(
            "Reject null dependency",
            TestCategory.COMPONENT,
            () -> Assertions.assertThrows(
                NullPointerException.class,
                () -> new UserDirectory(null)
            )
        );
    }


// ============================================================
// 13. INTERACTION TESTS
// ============================================================

    static void registerInteractionTests(TestRegistry registry) {

        registry.register(
            "Search interaction",
            TestCategory.INTERACTION,
            () -> {
                UserDirectory component =
                    new UserDirectory(
                        new MockUserRepository(sampleUsers(), false)
                    );

                component.mount();
                component.search("alice");

                Assertions.assertEquals(
                    component.getVisibleUsers().size(),
                    1,
                    "Search did not filter results"
                );
            }
        );

        registry.register(
            "Clear search interaction",
            TestCategory.INTERACTION,
            () -> {
                UserDirectory component =
                    new UserDirectory(
                        new MockUserRepository(sampleUsers(), false)
                    );

                component.mount();

                component.search("alice");
                component.search("");

                Assertions.assertEquals(
                    component.getVisibleUsers().size(),
                    3,
                    "Clearing search failed"
                );
            }
        );

        registry.register(
            "Selection callback",
            TestCategory.INTERACTION,
            () -> {
                UserDirectory component =
                    new UserDirectory(
                        new MockUserRepository(sampleUsers(), false)
                    );

                AtomicInteger selectedId =
                    new AtomicInteger(-1);

                component.setSelectionHandler(
                    user -> selectedId.set(user.id())
                );

                component.mount();
                component.selectUser(2);

                Assertions.assertEquals(
                    selectedId.get(),
                    2,
                    "Incorrect selection callback"
                );
            }
        );

        registry.register(
            "Filtered-out user cannot be selected",
            TestCategory.INTERACTION,
            () -> {
                UserDirectory component =
                    new UserDirectory(
                        new MockUserRepository(sampleUsers(), false)
                    );

                component.mount();
                component.search("alice");

                Assertions.assertThrows(
                    IllegalArgumentException.class,
                    () -> component.selectUser(2)
                );
            }
        );
    }


// ============================================================
// 14. MOCKING TESTS
// ============================================================

    static void registerMockingTests(TestRegistry registry) {

        registry.register(
            "Mock invocation count",
            TestCategory.MOCKING,
            () -> {
                MockUserRepository mock =
                    new MockUserRepository(sampleUsers(), false);

                UserDirectory component =
                    new UserDirectory(mock);

                component.mount();

                Assertions.assertEquals(
                    mock.getCallCount(),
                    1,
                    "Unexpected repository call count"
                );
            }
        );

        registry.register(
            "Mocked failure handling",
            TestCategory.MOCKING,
            () -> {
                MockUserRepository mock =
                    new MockUserRepository(List.of(), true);

                UserDirectory component =
                    new UserDirectory(mock);

                component.mount();

                Assertions.assertEquals(
                    component.getStatus(),
                    ComponentStatus.ERROR,
                    "Mocked failure was not handled"
                );
            }
        );

        registry.register(
            "Mock response isolation",
            TestCategory.MOCKING,
            () -> {
                MockUserRepository mock =
                    new MockUserRepository(sampleUsers(), false);

                List<User> first = mock.fetchUsers();
                first.clear();

                Assertions.assertEquals(
                    mock.fetchUsers().size(),
                    3,
                    "Mock data was unexpectedly modified"
                );
            }
        );
    }
}
