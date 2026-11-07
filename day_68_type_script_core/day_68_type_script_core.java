import java.util.*;
import java.util.function.Predicate;
import java.util.stream.Collectors;

// ============================================================
// TYPESCRIPT CORE: JAVA 17 ENTERPRISE DOMAIN MODEL
// Arrays, Objects, Tuples, Enums, Unions, Intersections, Aliases
// ============================================================

public class TypeScriptCore {

    // --------------------------------------------------------
    // 1. Type aliases
    // --------------------------------------------------------

    // Java has no native type-alias declaration.
    // Records and domain classes provide explicit alternatives.

    public record UserId(int value) {
        public UserId {
            if (value <= 0) {
                throw new IllegalArgumentException(
                    "User ID must be positive"
                );
            }
        }
    }

    public record Email(String value) {
        public Email {
            Objects.requireNonNull(value);

            if (!value.matches("^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$")) {
                throw new IllegalArgumentException("Invalid email");
            }
        }
    }

    // --------------------------------------------------------
    // 2. Enums
    // --------------------------------------------------------

    public enum UserRole {
        ADMIN,
        DEVELOPER,
        ANALYST,
        VIEWER
    }

    public enum AccountStatus {
        ACTIVE,
        SUSPENDED,
        PENDING
    }

    public enum ProjectStatus {
        PLANNED,
        IN_PROGRESS,
        COMPLETED
    }

    // --------------------------------------------------------
    // 3. Object structures
    // --------------------------------------------------------

    public record Profile(
        String displayName,
        Email email,
        String location
    ) {
        public Profile {
            Objects.requireNonNull(displayName);
            Objects.requireNonNull(email);
            Objects.requireNonNull(location);

            if (displayName.isBlank() || location.isBlank()) {
                throw new IllegalArgumentException(
                    "Profile fields cannot be empty"
                );
            }
        }
    }

    public record User(
        UserId id,
        Profile profile,
        UserRole role,
        AccountStatus status,
        List<String> tags
    ) {
        public User {
            Objects.requireNonNull(id);
            Objects.requireNonNull(profile);
            Objects.requireNonNull(role);
            Objects.requireNonNull(status);
            Objects.requireNonNull(tags);

            tags = List.copyOf(tags);

            if (tags.stream().anyMatch(String::isBlank)) {
                throw new IllegalArgumentException(
                    "Tags cannot be empty"
                );
            }

            if (new HashSet<>(tags).size() != tags.size()) {
                throw new IllegalArgumentException(
                    "Duplicate tags are not allowed"
                );
            }
        }

        public User withRole(UserRole newRole) {
            return new User(
                id,
                profile,
                newRole,
                status,
                tags
            );
        }
    }

    // --------------------------------------------------------
    // 4. Tuple representation
    // --------------------------------------------------------

    // Java does not have native tuple syntax.
    // Records provide fixed-position immutable structures.

    public record Coordinate(
        double latitude,
        double longitude
    ) {
        public Coordinate {
            if (
                !Double.isFinite(latitude) ||
                !Double.isFinite(longitude) ||
                latitude < -90 ||
                latitude > 90 ||
                longitude < -180 ||
                longitude > 180
            ) {
                throw new IllegalArgumentException(
                    "Invalid coordinates"
                );
            }
        }
    }

    public record UserSummary(
        UserId id,
        String name,
        UserRole role
    ) {}

    // --------------------------------------------------------
    // 5. Union types using sealed interfaces
    // --------------------------------------------------------

    // TypeScript:
    // type ApiResult =
    //   | SuccessResult
    //   | ErrorResult

    public sealed interface ApiResult
        permits SuccessResult, ErrorResult {}

    public record SuccessResult(
        Map<String, String> data
    ) implements ApiResult {
        public SuccessResult {
            data = Map.copyOf(data);
        }
    }

    public record ErrorResult(
        String message,
        int code
    ) implements ApiResult {
        public ErrorResult {
            Objects.requireNonNull(message);

            if (message.isBlank() || code < 400 || code > 599) {
                throw new IllegalArgumentException(
                    "Invalid error response"
                );
            }
        }
    }

    public static String handleResult(ApiResult result) {
        return switch (result) {
            case SuccessResult success ->
                "Success: " + success.data();

            case ErrorResult error ->
                "Error " + error.code() + ": " + error.message();
        };
    }

    // --------------------------------------------------------
    // 6. Union-like identifier
    // --------------------------------------------------------

    public sealed interface Identifier
        permits NumericIdentifier, StringIdentifier {}

    public record NumericIdentifier(int value)
        implements Identifier {
        public NumericIdentifier {
            if (value <= 0) {
                throw new IllegalArgumentException(
                    "Numeric identifier must be positive"
                );
            }
        }
    }

    public record StringIdentifier(String value)
        implements Identifier {
        public StringIdentifier {
            Objects.requireNonNull(value);

            if (value.isBlank()) {
                throw new IllegalArgumentException(
                    "String identifier cannot be empty"
                );
            }
        }
    }

    public static String normalizeIdentifier(Identifier id) {
        return switch (id) {
            case NumericIdentifier numeric ->
                String.valueOf(numeric.value());

            case StringIdentifier text ->
                text.value().trim();
        };
    }

    // --------------------------------------------------------
    // 7. Intersection types
    // --------------------------------------------------------

    public interface Auditable {
        UserId createdBy();
        String createdAt();
    }

    public interface PermissionControlled {
        boolean canRead();
        boolean canWrite();
        boolean canDelete();
    }

    // Implements both contracts, equivalent to a TypeScript
    // intersection of the corresponding interfaces.

    public record ManagedResource(
        int id,
        String name,
        UserId createdBy,
        String createdAt,
        boolean canRead,
        boolean canWrite,
        boolean canDelete
    ) implements Auditable, PermissionControlled {

        public ManagedResource {
            if (id <= 0 || name == null || name.isBlank()) {
                throw new IllegalArgumentException(
                    "Invalid resource"
                );
            }

            Objects.requireNonNull(createdBy);
            Objects.requireNonNull(createdAt);
        }
    }

    // --------------------------------------------------------
    // 8. Array processing
    // --------------------------------------------------------

    public record ScoreStatistics(
        double highest,
        double lowest,
        double average,
        List<Double> passed,
        List<Double> unique
    ) {}

    public static ScoreStatistics analyzeScores(
        List<Double> scores
    ) {
        Objects.requireNonNull(scores);

        if (scores.isEmpty()) {
            throw new IllegalArgumentException(
                "Scores cannot be empty"
            );
        }

        if (
            scores.stream().anyMatch(
                score -> score == null ||
                    !Double.isFinite(score) ||
                    score < 0 ||
                    score > 100
            )
        ) {
            throw new IllegalArgumentException(
                "Invalid score"
            );
        }

        List<Double> sorted = scores.stream()
            .sorted()
            .toList();

        List<Double> passed = scores.stream()
            .filter(score -> score >= 50)
            .toList();

        List<Double> unique = scores.stream()
            .distinct()
            .sorted()
            .toList();

        double average = scores.stream()
            .mapToDouble(Double::doubleValue)
            .average()
            .orElseThrow();

        return new ScoreStatistics(
            sorted.get(sorted.size() - 1),
            sorted.get(0),
            average,
            passed,
            unique
        );
    }

    // --------------------------------------------------------
    // 9. Generic repository
    // --------------------------------------------------------

    public static class Repository<T> {

        private final Map<Integer, T> records =
            new HashMap<>();

        public void add(int id, T value) {
            if (id <= 0) {
                throw new IllegalArgumentException(
                    "Invalid record ID"
                );
            }

            Objects.requireNonNull(value);

            if (records.putIfAbsent(id, value) != null) {
                throw new IllegalStateException(
                    "Duplicate record ID"
                );
            }
        }

        public Optional<T> get(int id) {
            return Optional.ofNullable(records.get(id));
        }

        public boolean remove(int id) {
            return records.remove(id) != null;
        }

        public int size() {
            return records.size();
        }

        public List<T> all() {
            return List.copyOf(records.values());
        }
    }

    // --------------------------------------------------------
    // 10. Generic utility
    // --------------------------------------------------------

    public static <T> Optional<T> firstItem(List<T> items) {
        Objects.requireNonNull(items);

        return items.stream().findFirst();
    }

    public static <T> List<T> filterItems(
        List<T> items,
        Predicate<T> condition
    ) {
        return items.stream()
            .filter(condition)
            .toList();
    }

    // --------------------------------------------------------
    // 11. Main enterprise workflow
    // --------------------------------------------------------

    public static void main(String[] args) {

        System.out.println("\n=== TYPESCRIPT CORE ===");

        // Arrays
        System.out.println("\nARRAYS");

        List<Double> scores = List.of(
            85.0, 92.0, 67.0, 48.0, 92.0
        );

        ScoreStatistics statistics = analyzeScores(scores);

        System.out.println("Highest: " + statistics.highest());
        System.out.println("Lowest: " + statistics.lowest());
        System.out.println("Average: " + statistics.average());
        System.out.println("Passed: " + statistics.passed());

        // Objects
        System.out.println("\nOBJECTS");

        Profile profile = new Profile(
            "Atul Pandey",
            new Email("atul@example.com"),
            "Lucknow"
        );

        User user = new User(
            new UserId(101),
            profile,
            UserRole.ADMIN,
            AccountStatus.ACTIVE,
            List.of("typescript", "java", "backend")
        );

        System.out.println(user);

        // Tuples
        System.out.println("\nTUPLES");

        Coordinate coordinate = new Coordinate(
            26.8467,
            80.9462
        );

        UserSummary summary = new UserSummary(
            user.id(),
            user.profile().displayName(),
            user.role()
        );

        System.out.println(coordinate);
        System.out.println(summary);

        // Enums
        System.out.println("\nENUMS");

        System.out.println(user.role());
        System.out.println(user.status());
        System.out.println(ProjectStatus.IN_PROGRESS);

        // Union types
        System.out.println("\nUNIONS");

        System.out.println(
            normalizeIdentifier(new NumericIdentifier(101))
        );

        System.out.println(
            normalizeIdentifier(
                new StringIdentifier("USER-101")
            )
        );

        // Discriminated unions
        System.out.println("\nDISCRIMINATED UNIONS");

        ApiResult success = new SuccessResult(
            Map.of("userId", "101", "status", "active")
        );

        ApiResult failure = new ErrorResult(
            "Permission denied",
            403
        );

        System.out.println(handleResult(success));
        System.out.println(handleResult(failure));

        // Intersection
        System.out.println("\nINTERSECTION TYPES");

        ManagedResource resource = new ManagedResource(
            501,
            "Project Repository",
            user.id(),
            "2026-11-07T08:00:00",
            true,
            true,
            false
        );

        System.out.println(resource);
        System.out.println("Can delete: " + resource.canDelete());

        // Generics
        System.out.println("\nGENERIC REPOSITORY");

        Repository<User> repository = new Repository<>();

        repository.add(101, user);

        System.out.println(
            repository.get(101).orElseThrow()
        );

        System.out.println("Count: " + repository.size());

        System.out.println(
            "First score: " + firstItem(scores).orElseThrow()
        );

        // Immutable object transformation
        System.out.println("\nOBJECT TRANSFORMATION");

        User updatedUser = user.withRole(UserRole.DEVELOPER);

        System.out.println("Original: " + user.role());
        System.out.println("Updated: " + updatedUser.role());

        // Failure handling
        System.out.println("\nVALIDATION");

        List<Runnable> invalidOperations = List.of(
            () -> new UserId(0),
            () -> new Email("invalid-email"),
            () -> new Coordinate(100, 20),
            () -> analyzeScores(List.of()),
            () -> repository.add(101, user)
        );

        for (Runnable operation : invalidOperations) {
            try {
                operation.run();
            } catch (RuntimeException error) {
                System.out.println(
                    "Expected error: " + error.getMessage()
                );
            }
        }

        System.out.println("\nExecution completed.");
    }
}
