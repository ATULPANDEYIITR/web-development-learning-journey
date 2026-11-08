import java.util.*;
import java.util.function.*;
import java.util.stream.Collectors;

/**
 * Advanced Type System Concepts
 *
 * Java 17 implementation covering:
 * - Generics
 * - Bounded type parameters
 * - Wildcards
 * - Utility-type equivalents
 * - Type narrowing
 * - Custom type guards
 * - Conditional-type equivalents
 * - Records and sealed interfaces
 * - Immutable data
 * - Enterprise validation
 *
 * Compile:
 * javac TypeScriptAdvanced.java
 *
 * Run:
 * java TypeScriptAdvanced
 */

public class TypeScriptAdvanced {

    // ========================================================
    // 1. GENERIC FUNCTIONS
    // ========================================================

    public static <T> T identity(T value) {
        return value;
    }

    public static <T> Optional<T> first(List<T> values) {
        return values.stream().findFirst();
    }

    public static <T extends Comparable<T>> T maximum(
            List<T> values) {

        return values.stream()
                .max(Comparator.naturalOrder())
                .orElseThrow(() ->
                        new IllegalArgumentException(
                                "Empty collection"
                        )
                );
    }

    // ========================================================
    // 2. DOMAIN RECORDS
    // ========================================================

    enum AccountStatus {
        ACTIVE,
        SUSPENDED,
        CLOSED
    }

    record User(
            int id,
            String name,
            String email,
            AccountStatus status
    ) {
        public User {
            if (id <= 0) {
                throw new IllegalArgumentException(
                        "Invalid user ID"
                );
            }

            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException(
                        "Invalid name"
                );
            }

            if (email == null || !email.contains("@")) {
                throw new IllegalArgumentException(
                        "Invalid email"
                );
            }

            Objects.requireNonNull(status);
        }
    }

    record Product(
            int id,
            String name,
            double price
    ) {
        public Product {
            if (id <= 0 || name == null || name.isBlank()
                    || !Double.isFinite(price) || price < 0) {
                throw new IllegalArgumentException(
                        "Invalid product"
                );
            }
        }
    }

    // ========================================================
    // 3. GENERIC REPOSITORY
    // ========================================================

    static class Repository<K, V> {

        private final Map<K, V> records = new HashMap<>();

        public void add(K key, V value) {
            Objects.requireNonNull(key);
            Objects.requireNonNull(value);

            if (records.containsKey(key)) {
                throw new IllegalStateException(
                        "Duplicate key"
                );
            }

            records.put(key, value);
        }

        public Optional<V> find(K key) {
            return Optional.ofNullable(records.get(key));
        }

        public boolean remove(K key) {
            return records.remove(key) != null;
        }

        public List<V> all() {
            return List.copyOf(records.values());
        }

        public int size() {
            return records.size();
        }
    }

    // ========================================================
    // 4. BOUNDED GENERICS AND WILDCARDS
    // ========================================================

    interface Identifiable {
        int id();
    }

    record Customer(int id, String name)
            implements Identifiable {}

    record Employee(int id, String name)
            implements Identifiable {}

    /**
     * Upper-bounded wildcard:
     * Accepts lists of Identifiable subtypes.
     */
    static int totalIdentifiers(
            List<? extends Identifiable> items) {

        return items.stream()
                .mapToInt(Identifiable::id)
                .sum();
    }

    /**
     * Lower-bounded wildcard:
     * Accepts consumers of Employee or its parent types.
     */
    static void addEmployee(
            List<? super Employee> destination,
            Employee employee) {

        destination.add(employee);
    }

    // ========================================================
    // 5. UTILITY-TYPE EQUIVALENTS
    // ========================================================

    record UserPatch(
            Optional<String> name,
            Optional<String> email
    ) {
        public UserPatch {
            Objects.requireNonNull(name);
            Objects.requireNonNull(email);
        }
    }

    static User applyPatch(User original, UserPatch patch) {
        return new User(
                original.id(),
                patch.name().orElse(original.name()),
                patch.email().orElse(original.email()),
                original.status()
        );
    }

    /**
     * Pick<T, K>-style operation.
     */
    static <K, V> Map<K, V> pick(
            Map<K, V> source,
            Set<K> keys) {

        return source.entrySet()
                .stream()
                .filter(entry -> keys.contains(entry.getKey()))
                .collect(Collectors.toUnmodifiableMap(
                        Map.Entry::getKey,
                        Map.Entry::getValue
                ));
    }

    /**
     * Omit<T, K>-style operation.
     */
    static <K, V> Map<K, V> omit(
            Map<K, V> source,
            Set<K> excluded) {

        return source.entrySet()
                .stream()
                .filter(entry -> !excluded.contains(
                        entry.getKey()
                ))
                .collect(Collectors.toUnmodifiableMap(
                        Map.Entry::getKey,
                        Map.Entry::getValue
                ));
    }

    /**
     * Readonly<T>-style immutable snapshot.
     */
    static <K, V> Map<K, V> readonly(Map<K, V> source) {
        return Map.copyOf(source);
    }

    // ========================================================
    // 6. TYPE NARROWING
    // ========================================================

    static String describe(Object value) {

        if (value == null) {
            return "Missing value";
        }

        if (value instanceof String text) {
            return "String: " + text.trim();
        }

        if (value instanceof Integer number) {
            return "Integer: " + number;
        }

        if (value instanceof Double decimal) {
            return "Decimal: " + decimal;
        }

        if (value instanceof List<?> list) {
            return "List size: " + list.size();
        }

        return "Unsupported type: " +
                value.getClass().getSimpleName();
    }

    // ========================================================
    // 7. DISCRIMINATED UNION WITH SEALED INTERFACE
    // ========================================================

    sealed interface OperationResult
            permits Success, Failure {}

    record Success(
            String transactionId,
            double amount
    ) implements OperationResult {}

    record Failure(
            String message,
            int code
    ) implements OperationResult {}

    static String processResult(OperationResult result) {

        if (result instanceof Success success) {
            return "Approved: " + success.transactionId();
        }

        if (result instanceof Failure failure) {
            return "Rejected " + failure.code()
                    + ": " + failure.message();
        }

        throw new IllegalArgumentException(
                "Unknown operation result"
        );
    }

    // ========================================================
    // 8. CUSTOM TYPE GUARDS
    // ========================================================

    static boolean isValidUser(Object value) {

        if (!(value instanceof User user)) {
            return false;
        }

        return user.id() > 0
                && !user.name().isBlank()
                && user.email().contains("@");
    }

    static <T> List<T> filterValid(
            List<T> values,
            Predicate<? super T> validator) {

        return values.stream()
                .filter(validator)
                .toList();
    }

    // ========================================================
    // 9. CONDITIONAL-TYPE EQUIVALENTS
    // ========================================================

    /**
     * Java cannot directly express TypeScript's
     * conditional types. This generic service uses
     * explicit runtime dispatch.
     */
    static Object normalize(Object value) {

        if (value instanceof String text) {
            return text.trim().toLowerCase();
        }

        if (value instanceof Integer number) {
            return Math.abs(number);
        }

        if (value instanceof Double decimal) {
            if (!Double.isFinite(decimal)) {
                throw new IllegalArgumentException(
                        "Invalid number"
                );
            }

            return Math.abs(decimal);
        }

        throw new IllegalArgumentException(
                "Unsupported normalization type"
        );
    }

    // ========================================================
    // 10. GENERIC TRANSFORMATION PIPELINE
    // ========================================================

    static class Pipeline<T> {

        private final List<UnaryOperator<T>> operations =
                new ArrayList<>();

        public Pipeline<T> add(UnaryOperator<T> operation) {
            operations.add(Objects.requireNonNull(operation));
            return this;
        }

        public T execute(T input) {
            T result = input;

            for (UnaryOperator<T> operation : operations) {
                result = operation.apply(result);
            }

            return result;
        }
    }

    // ========================================================
    // 11. ENTERPRISE USER SERVICE
    // ========================================================

    static class UserService {

        private final Repository<Integer, User> repository =
                new Repository<>();

        public void register(User user) {

            if (!isValidUser(user)) {
                throw new IllegalArgumentException(
                        "User validation failed"
                );
            }

            repository.add(user.id(), user);
        }

        public Optional<User> find(int id) {
            if (id <= 0) {
                throw new IllegalArgumentException(
                        "Invalid user ID"
                );
            }

            return repository.find(id);
        }

        public List<User> activeUsers() {
            return repository.all()
                    .stream()
                    .filter(user ->
                            user.status() == AccountStatus.ACTIVE
                    )
                    .toList();
        }
    }

    // ========================================================
    // 12. TESTS
    // ========================================================

    static void runTests() {

        assert identity(100).equals(100);
        assert identity("Advanced").equals("Advanced");

        assert first(List.of(10, 20)).orElseThrow() == 10;
        assert first(List.of()).isEmpty();

        assert maximum(List.of(2, 8, 5)) == 8;

        Repository<String, User> repository =
                new Repository<>();

        User user = new User(
                1,
                "Aarav",
                "aarav@example.com",
                AccountStatus.ACTIVE
        );

        repository.add("U001", user);

        assert repository.find("U001").orElseThrow().id() == 1;
        assert repository.remove("U001");
        assert repository.find("U001").isEmpty();

        UserPatch patch = new UserPatch(
                Optional.of("Aarav Sharma"),
                Optional.empty()
        );

        User updated = applyPatch(user, patch);

        assert updated.name().equals("Aarav Sharma");
        assert user.name().equals("Aarav");

        Map<String, Object> data = new HashMap<>();
        data.put("name", "Mira");
        data.put("password", "secret");
        data.put("email", "mira@example.com");

        assert pick(data, Set.of("name"))
                .containsKey("name");

        assert !omit(data, Set.of("password"))
                .containsKey("password");

        assert readonly(data).size() == 3;

        assert describe("TypeScript").equals("String: TypeScript");
        assert describe(25).equals("Integer: 25");
        assert describe(null).equals("Missing value");

        assert processResult(
                new Success("TX-001", 500)
        ).startsWith("Approved");

        assert processResult(
                new Failure("Denied", 403)
        ).startsWith("Rejected");

        assert isValidUser(user);

        assert normalize(" TYPESCRIPT ").equals("typescript");
        assert normalize(-10).equals(10);

        Pipeline<String> pipeline = new Pipeline<String>()
                .add(String::trim)
                .add(String::toUpperCase);

        assert pipeline.execute(" advanced ").equals("ADVANCED");

        assert totalIdentifiers(
                List.of(
                        new Customer(1, "Mira"),
                        new Employee(2, "Aarav")
                )
        ) == 3;

        List<Object> employees = new ArrayList<>();
        addEmployee(employees, new Employee(3, "Ravi"));

        assert employees.size() == 1;

        System.out.println("All Java 17 tests passed.");
    }

    // ========================================================
    // MAIN
    // ========================================================

    public static void main(String[] args) {

        try {
            System.out.println("ADVANCED TYPE SYSTEM CONCEPTS");
            System.out.println("======================================");

            runTests();

            Repository<String, Product> products =
                    new Repository<>();

            products.add(
                    "P001",
                    new Product(
                            1,
                            "Security Platform",
                            4999.0
                    )
            );

            System.out.println("\nGeneric repository:");

            products.all().forEach(System.out::println);

            System.out.println("\nType narrowing:");

            System.out.println(describe("TypeScript"));
            System.out.println(describe(100));

            System.out.println("\nUtility-type equivalents:");

            System.out.println(pick(
                    Map.of(
                            "name", "Mira",
                            "email", "mira@example.com",
                            "password", "secret"
                    ),
                    Set.of("name", "email")
            ));

            System.out.println("\nConditional-type equivalent:");

            System.out.println(normalize(" GENERICS "));

            System.out.println("\nDiscriminated union:");

            System.out.println(processResult(
                    new Success("TX-2026", 7500)
            ));

            UserService service = new UserService();

            service.register(new User(
                    101,
                    "Mira",
                    "mira@example.com",
                    AccountStatus.ACTIVE
            ));

            System.out.println("\nActive users:");

            service.activeUsers().forEach(System.out::println);

        } catch (RuntimeException exception) {
            System.err.println(
                    "Application error: " + exception.getMessage()
            );

            System.exit(1);
        }
    }
}
