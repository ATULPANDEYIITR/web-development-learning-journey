import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

/**
 * TypeScript Introduction
 * Why TypeScript, Type Annotations, Primitive Types, and Type Inference.
 *
 * Enterprise-oriented employee account and configuration management.
 *
 * Compile:
 * javac TypeScriptIntroduction.java
 *
 * Run:
 * java TypeScriptIntroduction
 */
public class TypeScriptIntroduction {

    enum AccountStatus {
        ACTIVE,
        INACTIVE,
        SUSPENDED
    }

    enum PrimitiveKind {
        STRING,
        NUMBER,
        BOOLEAN,
        NULL
    }

    static final class ValidationException extends RuntimeException {
        ValidationException(String message) {
            super(message);
        }
    }

    record ApplicationConfig(
        String applicationName,
        int port,
        boolean debug,
        String environment
    ) {
        ApplicationConfig {
            if (applicationName == null ||
                    applicationName.isBlank()) {
                throw new ValidationException(
                    "Application name is required."
                );
            }

            if (port < 1 || port > 65535) {
                throw new ValidationException(
                    "Port must be between 1 and 65535."
                );
            }

            if (!List.of(
                    "development",
                    "testing",
                    "production"
                ).contains(environment)) {
                throw new ValidationException(
                    "Unsupported environment."
                );
            }
        }
    }

    record EmployeeProfile(
        String employeeId,
        String name,
        String email,
        int age,
        boolean verified,
        Map<String, Object> metadata
    ) {
        private static final Pattern EMAIL_PATTERN =
            Pattern.compile(
                "^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$"
            );

        EmployeeProfile {
            if (employeeId == null || employeeId.isBlank()) {
                throw new ValidationException(
                    "Employee ID is required."
                );
            }

            if (name == null || name.isBlank()) {
                throw new ValidationException(
                    "Employee name is required."
                );
            }

            if (email == null ||
                    !EMAIL_PATTERN.matcher(email).matches()) {
                throw new ValidationException(
                    "Invalid employee email."
                );
            }

            if (age < 18 || age > 120) {
                throw new ValidationException(
                    "Age must be between 18 and 120."
                );
            }

            if (metadata == null) {
                throw new ValidationException(
                    "Metadata cannot be null."
                );
            }

            Map<String, Object> safeMetadata = new HashMap<>();

            metadata.forEach((key, value) -> {
                if (key == null || key.isBlank()) {
                    throw new ValidationException(
                        "Metadata keys cannot be empty."
                    );
                }

                if (!isSupportedMetadataValue(value)) {
                    throw new ValidationException(
                        "Unsupported metadata value: " + key
                    );
                }

                safeMetadata.put(key, value);
            });

            employeeId = employeeId.trim();
            name = name.trim();
            email = email.toLowerCase();
            metadata = Map.copyOf(safeMetadata);
        }

        private static boolean isSupportedMetadataValue(
            Object value
        ) {
            if (value == null ||
                    value instanceof String ||
                    value instanceof Boolean ||
                    value instanceof Integer ||
                    value instanceof Long) {
                return true;
            }

            if (value instanceof Double number) {
                return Double.isFinite(number);
            }

            return false;
        }
    }

    static final class EmployeeAccount {

        private final EmployeeProfile profile;
        private AccountStatus status;

        EmployeeAccount(EmployeeProfile profile) {
            this.profile = Objects.requireNonNull(profile);
            this.status = AccountStatus.ACTIVE;
        }

        EmployeeProfile getProfile() {
            return profile;
        }

        AccountStatus getStatus() {
            return status;
        }

        void deactivate() {
            if (status == AccountStatus.SUSPENDED) {
                throw new ValidationException(
                    "Suspended accounts require administrative review."
                );
            }

            status = AccountStatus.INACTIVE;
        }

        void suspend() {
            status = AccountStatus.SUSPENDED;
        }
    }

    static final class EmployeeService {

        private final Map<String, EmployeeAccount> accounts =
            new LinkedHashMap<>();

        private final Map<String, String> emailIndex =
            new HashMap<>();

        public void register(EmployeeProfile profile) {
            Objects.requireNonNull(profile);

            if (accounts.containsKey(profile.employeeId())) {
                throw new ValidationException(
                    "Employee ID already exists."
                );
            }

            if (emailIndex.containsKey(profile.email())) {
                throw new ValidationException(
                    "Email already exists."
                );
            }

            EmployeeAccount account =
                new EmployeeAccount(profile);

            accounts.put(profile.employeeId(), account);
            emailIndex.put(
                profile.email(),
                profile.employeeId()
            );
        }

        public Optional<EmployeeAccount> findById(String id) {
            return Optional.ofNullable(accounts.get(id));
        }

        public Optional<EmployeeAccount> findByEmail(String email) {
            if (email == null) {
                return Optional.empty();
            }

            String normalized = email.trim().toLowerCase();
            String id = emailIndex.get(normalized);

            return id == null
                ? Optional.empty()
                : findById(id);
        }

        public void deactivate(String id) {
            EmployeeAccount account = accounts.get(id);

            if (account == null) {
                throw new ValidationException(
                    "Employee does not exist."
                );
            }

            account.deactivate();
        }

        public List<EmployeeAccount> activeAccounts() {
            return accounts.values()
                .stream()
                .filter(account ->
                    account.getStatus() == AccountStatus.ACTIVE
                )
                .collect(Collectors.toUnmodifiableList());
        }

        public Map<AccountStatus, Long> statusReport() {
            return accounts.values()
                .stream()
                .collect(Collectors.groupingBy(
                    EmployeeAccount::getStatus,
                    Collectors.counting()
                ));
        }
    }

    static final class PrimitiveValidator {

        static PrimitiveKind infer(Object value) {
            if (value == null) {
                return PrimitiveKind.NULL;
            }

            if (value instanceof String) {
                return PrimitiveKind.STRING;
            }

            if (value instanceof Boolean) {
                return PrimitiveKind.BOOLEAN;
            }

            if (value instanceof Number) {
                return PrimitiveKind.NUMBER;
            }

            throw new ValidationException(
                "Unsupported primitive value."
            );
        }

        static boolean validate(
            Object value,
            PrimitiveKind expected
        ) {
            return infer(value) == expected;
        }
    }

    private static void demonstrateAnnotations() {
        System.out.println("\nTYPE DECLARATIONS");

        // Explicit Java declarations.
        String username = "Atul";
        int age = 29;
        double salary = 85000.50;
        boolean verified = true;

        // Java 10+ local-variable type inference.
        var inferredName = "Riya";
        var inferredAge = 31;
        var inferredSalary = 92000.75;
        var inferredVerified = false;

        System.out.println("Explicit string: " + username);
        System.out.println("Explicit integer: " + age);
        System.out.println("Explicit double: " + salary);
        System.out.println("Explicit boolean: " + verified);

        System.out.println("Inferred string: " + inferredName);
        System.out.println("Inferred integer: " + inferredAge);
        System.out.println("Inferred double: " + inferredSalary);
        System.out.println("Inferred boolean: " + inferredVerified);
    }

    private static void demonstratePrimitiveTypes() {
        System.out.println("\nPRIMITIVE TYPE VALIDATION");

        List<Object> values = new ArrayList<>();

        values.add("Engineering");
        values.add(42);
        values.add(42.75);
        values.add(true);
        values.add(null);

        for (Object value : values) {
            System.out.println(
                String.valueOf(value) + " => " +
                PrimitiveValidator.infer(value)
            );
        }

        if (!PrimitiveValidator.validate(
                "hello",
                PrimitiveKind.STRING
            )) {
            throw new ValidationException(
                "String validation failed."
            );
        }

        if (PrimitiveValidator.validate(
                true,
                PrimitiveKind.NUMBER
            )) {
            throw new ValidationException(
                "Boolean must not be treated as a number."
            );
        }
    }

    private static void demonstrateEnterpriseWorkflow() {
        System.out.println("\nENTERPRISE EMPLOYEE WORKFLOW");

        EmployeeService service = new EmployeeService();

        EmployeeProfile first = new EmployeeProfile(
            "EMP-001",
            "Atul Pandey",
            "ATUL@example.com",
            29,
            true,
            Map.of(
                "department", "Engineering",
                "experience", 5,
                "remote", true
            )
        );

        EmployeeProfile second = new EmployeeProfile(
            "EMP-002",
            "Riya Sharma",
            "riya@example.com",
            31,
            false,
            Map.of(
                "department", "Research",
                "experience", 7
            )
        );

        service.register(first);
        service.register(second);

        service.findByEmail("atul@example.com")
            .ifPresent(account ->
                System.out.println(
                    "Employee found: " +
                    account.getProfile().name()
                )
            );

        service.deactivate("EMP-002");

        System.out.println(
            "Active accounts: " +
            service.activeAccounts().size()
        );

        System.out.println(
            "Account report: " +
            service.statusReport()
        );

        try {
            service.register(first);
        } catch (ValidationException error) {
            System.out.println(
                "Duplicate rejected: " + error.getMessage()
            );
        }

        try {
            new EmployeeProfile(
                "EMP-003",
                "Invalid Employee",
                "not-an-email",
                25,
                false,
                Map.of()
            );
        } catch (ValidationException error) {
            System.out.println(
                "Invalid employee rejected: " +
                error.getMessage()
            );
        }
    }

    private static void demonstrateConfiguration() {
        System.out.println("\nAPPLICATION CONFIGURATION");

        ApplicationConfig configuration =
            new ApplicationConfig(
                "EnterpriseRegistry",
                8080,
                false,
                "production"
            );

        System.out.println(configuration);

        try {
            new ApplicationConfig(
                "InvalidRegistry",
                70000,
                true,
                "production"
            );
        } catch (ValidationException error) {
            System.out.println(
                "Configuration rejected: " +
                error.getMessage()
            );
        }
    }

    public static void main(String[] args) {
        demonstrateAnnotations();
        demonstratePrimitiveTypes();
        demonstrateEnterpriseWorkflow();
        demonstrateConfiguration();

        System.out.println("\nALL TESTS COMPLETED");
    }
}
