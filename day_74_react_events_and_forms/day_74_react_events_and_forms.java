import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionException;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

/*
 * React Events and Forms
 *
 * Enterprise-oriented form management and validation system.
 *
 * Features:
 * - Typed form fields
 * - Immutable field definitions
 * - Event listener registration
 * - Event dispatch
 * - Controlled and uncontrolled inputs
 * - Validation policies
 * - Cross-field validation
 * - Asynchronous validation
 * - Submission service
 * - Explicit state transitions
 * - Concurrency protection
 * - Error recovery
 *
 * Compile: javac ReactEventsForms.java
 * Run: java ReactEventsForms
 */

public class ReactEventsForms {

    enum EventType {
        CLICK,
        INPUT,
        CHANGE,
        BLUR,
        FOCUS,
        SUBMIT,
        RESET
    }

    enum FormStatus {
        IDLE,
        DIRTY,
        VALIDATING,
        INVALID,
        SUBMITTING,
        SUBMITTED
    }

    enum InputType {
        TEXT,
        EMAIL,
        PASSWORD,
        NUMBER,
        CHECKBOX
    }

    record FormEvent(
        EventType type,
        String target,
        Object value,
        boolean bubbles
    ) {}

    record ValidationIssue(
        String field,
        String message,
        String code
    ) {}

    record SubmissionResult(
        UUID id,
        String username,
        String email,
        boolean successful
    ) {}

    static class FormException extends RuntimeException {
        FormException(String message) {
            super(message);
        }
    }

    static class ValidationException extends FormException {
        private final List<ValidationIssue> issues;

        ValidationException(List<ValidationIssue> issues) {
            super("Form validation failed");
            this.issues = List.copyOf(issues);
        }

        public List<ValidationIssue> getIssues() {
            return issues;
        }
    }

    static class SubmissionException extends FormException {
        SubmissionException(String message) {
            super(message);
        }
    }

    @FunctionalInterface
    interface EventHandler {
        void handle(FormEvent event);
    }

    interface EventSource {
        void addListener(EventType type, EventHandler handler);

        void removeListener(EventType type, EventHandler handler);

        void dispatch(FormEvent event);
    }

    static final class EventBus implements EventSource {

        private final Map<EventType, List<EventHandler>> handlers =
            new ConcurrentHashMap<>();

        @Override
        public void addListener(
            EventType type,
            EventHandler handler
        ) {
            Objects.requireNonNull(type);
            Objects.requireNonNull(handler);

            handlers.computeIfAbsent(
                type,
                key -> Collections.synchronizedList(
                    new ArrayList<>()
                )
            ).add(handler);
        }

        @Override
        public void removeListener(
            EventType type,
            EventHandler handler
        ) {
            List<EventHandler> listeners = handlers.get(type);

            if (listeners != null) {
                listeners.remove(handler);
            }
        }

        @Override
        public void dispatch(FormEvent event) {
            List<EventHandler> listeners = handlers.get(event.type());

            if (listeners == null) {
                return;
            }

            List<EventHandler> snapshot;

            synchronized (listeners) {
                snapshot = List.copyOf(listeners);
            }

            for (EventHandler handler : snapshot) {
                handler.handle(event);
            }
        }
    }

    record FieldDefinition(
        String name,
        InputType type,
        boolean required,
        boolean controlled,
        int maxLength,
        Object initialValue
    ) {
        FieldDefinition {
            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException(
                    "Field name is required"
                );
            }

            Objects.requireNonNull(type);

            if (maxLength < 1) {
                throw new IllegalArgumentException(
                    "Maximum length must be positive"
                );
            }

            if (initialValue == null) {
                throw new IllegalArgumentException(
                    "Initial value cannot be null"
                );
            }

            if (
                type == InputType.CHECKBOX &&
                !(initialValue instanceof Boolean)
            ) {
                throw new IllegalArgumentException(
                    "Checkbox initial value must be Boolean"
                );
            }
        }
    }

    static final class FieldState {

        private final FieldDefinition definition;

        private Object value;
        private boolean touched;

        FieldState(FieldDefinition definition) {
            this.definition = definition;
            this.value = definition.initialValue();
        }

        FieldDefinition definition() {
            return definition;
        }

        Object value() {
            return value;
        }

        boolean touched() {
            return touched;
        }

        void update(Object value) {
            validateType(value);
            this.value = value;
            this.touched = true;
        }

        void reset() {
            value = definition.initialValue();
            touched = false;
        }

        private void validateType(Object value) {
            Objects.requireNonNull(value);

            if (
                definition.type() == InputType.CHECKBOX &&
                !(value instanceof Boolean)
            ) {
                throw new IllegalArgumentException(
                    "Checkbox requires Boolean"
                );
            }

            if (
                definition.type() != InputType.CHECKBOX &&
                !(value instanceof String)
            ) {
                throw new IllegalArgumentException(
                    "Text input requires String"
                );
            }

            if (
                value instanceof String text &&
                text.length() > definition.maxLength()
            ) {
                throw new IllegalArgumentException(
                    "Maximum length exceeded"
                );
            }
        }
    }

    record ValidationPolicy(
        int minimumLength,
        boolean email,
        Double minimum,
        Double maximum
    ) {
        ValidationPolicy {
            if (minimumLength < 0) {
                throw new IllegalArgumentException(
                    "Minimum length cannot be negative"
                );
            }

            if (
                minimum != null &&
                maximum != null &&
                minimum > maximum
            ) {
                throw new IllegalArgumentException(
                    "Invalid numeric range"
                );
            }
        }
    }

    static final class ValidationService {

        private static final Pattern EMAIL_PATTERN =
            Pattern.compile(
                "^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$"
            );

        List<ValidationIssue> validate(
            Map<String, FieldState> fields,
            Map<String, ValidationPolicy> policies
        ) {
            List<ValidationIssue> issues = new ArrayList<>();

            for (FieldState state : fields.values()) {
                FieldDefinition definition = state.definition();
                Object value = state.value();

                if (value instanceof Boolean) {
                    continue;
                }

                String text = (String) value;

                if (
                    definition.required() &&
                    text.isBlank()
                ) {
                    issues.add(new ValidationIssue(
                        definition.name(),
                        "This field is required",
                        "REQUIRED"
                    ));

                    continue;
                }

                if (text.isBlank()) {
                    continue;
                }

                ValidationPolicy policy =
                    policies.get(definition.name());

                if (policy == null) {
                    continue;
                }

                if (
                    policy.minimumLength() > 0 &&
                    text.length() < policy.minimumLength()
                ) {
                    issues.add(new ValidationIssue(
                        definition.name(),
                        "Minimum length not satisfied",
                        "MIN_LENGTH"
                    ));
                }

                if (
                    policy.email() &&
                    !EMAIL_PATTERN.matcher(text).matches()
                ) {
                    issues.add(new ValidationIssue(
                        definition.name(),
                        "Invalid email address",
                        "EMAIL"
                    ));
                }

                if (
                    policy.minimum() != null ||
                    policy.maximum() != null
                ) {
                    try {
                        double number = Double.parseDouble(text);

                        if (!Double.isFinite(number)) {
                            throw new NumberFormatException();
                        }

                        if (
                            policy.minimum() != null &&
                            number < policy.minimum()
                        ) {
                            issues.add(new ValidationIssue(
                                definition.name(),
                                "Value below minimum",
                                "MINIMUM"
                            ));
                        }

                        if (
                            policy.maximum() != null &&
                            number > policy.maximum()
                        ) {
                            issues.add(new ValidationIssue(
                                definition.name(),
                                "Value above maximum",
                                "MAXIMUM"
                            ));
                        }

                    } catch (NumberFormatException exception) {
                        issues.add(new ValidationIssue(
                            definition.name(),
                            "Finite numeric value required",
                            "NUMBER"
                        ));
                    }
                }
            }

            FieldState password = fields.get("password");
            FieldState confirmation = fields.get("confirmPassword");

            if (
                password != null &&
                confirmation != null &&
                !password.value().equals(confirmation.value())
            ) {
                issues.add(new ValidationIssue(
                    "confirmPassword",
                    "Passwords do not match",
                    "PASSWORD_MISMATCH"
                ));
            }

            return List.copyOf(issues);
        }
    }

    interface RegistrationRepository {
        SubmissionResult register(Map<String, Object> values);
    }

    static final class InMemoryRegistrationRepository
        implements RegistrationRepository {

        private final Set<String> registeredEmails =
            ConcurrentHashMap.newKeySet();

        @Override
        public SubmissionResult register(
            Map<String, Object> values
        ) {
            String email = (String) values.get("email");
            String username = (String) values.get("username");

            if (
                email.equalsIgnoreCase("failure@example.com")
            ) {
                throw new SubmissionException(
                    "Registration service unavailable"
                );
            }

            if (!registeredEmails.add(email.toLowerCase())) {
                throw new SubmissionException(
                    "Email already registered"
                );
            }

            return new SubmissionResult(
                UUID.randomUUID(),
                username,
                email,
                true
            );
        }
    }

    static final class FormService implements EventSource {

        private final Map<String, FieldState> fields =
            new LinkedHashMap<>();

        private final Map<String, ValidationPolicy> policies =
            new HashMap<>();

        private final EventBus eventBus = new EventBus();

        private final ValidationService validator =
            new ValidationService();

        private final AtomicInteger submissions =
            new AtomicInteger();

        private final Object lock = new Object();

        private FormStatus status = FormStatus.IDLE;

        private long revision = 0;

        private static final Map<FormStatus, Set<FormStatus>>
            TRANSITIONS = Map.of(
                FormStatus.IDLE,
                Set.of(FormStatus.DIRTY, FormStatus.VALIDATING),

                FormStatus.DIRTY,
                Set.of(
                    FormStatus.DIRTY,
                    FormStatus.IDLE,
                    FormStatus.VALIDATING
                ),

                FormStatus.VALIDATING,
                Set.of(
                    FormStatus.INVALID,
                    FormStatus.IDLE,
                    FormStatus.DIRTY
                ),

                FormStatus.INVALID,
                Set.of(
                    FormStatus.DIRTY,
                    FormStatus.IDLE,
                    FormStatus.VALIDATING
                ),

                FormStatus.SUBMITTING,
                Set.of(
                    FormStatus.SUBMITTED,
                    FormStatus.DIRTY,
                    FormStatus.INVALID
                ),

                FormStatus.SUBMITTED,
                Set.of(
                    FormStatus.DIRTY,
                    FormStatus.IDLE,
                    FormStatus.VALIDATING
                )
            );

        FormService(
            List<FieldDefinition> definitions,
            Map<String, ValidationPolicy> policies
        ) {
            for (FieldDefinition definition : definitions) {
                if (fields.containsKey(definition.name())) {
                    throw new IllegalArgumentException(
                        "Duplicate field: " + definition.name()
                    );
                }

                fields.put(
                    definition.name(),
                    new FieldState(definition)
                );
            }

            for (String name : policies.keySet()) {
                if (!fields.containsKey(name)) {
                    throw new IllegalArgumentException(
                        "Unknown validation field: " + name
                    );
                }
            }

            this.policies.putAll(policies);
        }

        private void transition(FormStatus next) {
            if (!TRANSITIONS.get(status).contains(next)) {
                throw new FormException(
                    "Invalid state transition: " +
                    status + " -> " + next
                );
            }

            FormStatus previous = status;
            status = next;

            eventBus.dispatch(new FormEvent(
                EventType.CHANGE,
                "form-status",
                next,
                false
            ));
        }

        void setValue(String name, Object value) {
            synchronized (lock) {
                if (status == FormStatus.SUBMITTING) {
                    throw new FormException(
                        "Cannot modify form during submission"
                    );
                }

                FieldState field = fields.get(name);

                if (field == null) {
                    throw new IllegalArgumentException(
                        "Unknown field: " + name
                    );
                }

                if (!field.definition().controlled()) {
                    throw new FormException(
                        "Field is uncontrolled: " + name
                    );
                }

                update(field, value);
            }
        }

        void setUncontrolledValue(String name, Object value) {
            synchronized (lock) {
                if (status == FormStatus.SUBMITTING) {
                    throw new FormException(
                        "Cannot modify form during submission"
                    );
                }

                FieldState field = fields.get(name);

                if (field == null) {
                    throw new IllegalArgumentException(
                        "Unknown field: " + name
                    );
                }

                if (field.definition().controlled()) {
                    throw new FormException(
                        "Field is controlled: " + name
                    );
                }

                update(field, value);
            }
        }

        private void update(FieldState field, Object value) {
            field.update(value);
            revision++;

            transition(FormStatus.DIRTY);

            eventBus.dispatch(new FormEvent(
                EventType.CHANGE,
                field.definition().name(),
                value,
                true
            ));
        }

        private Map<String, Object> snapshot() {
            return fields.entrySet()
                .stream()
                .collect(Collectors.toUnmodifiableMap(
                    Map.Entry::getKey,
                    entry -> entry.getValue().value()
                ));
        }

        private List<ValidationIssue> validateInternal() {
            return validator.validate(fields, policies);
        }

        CompletableFuture<List<ValidationIssue>> validateAsync() {
            synchronized (lock) {
                if (status == FormStatus.SUBMITTING) {
                    return CompletableFuture.failedFuture(
                        new FormException(
                            "Cannot validate during submission"
                        )
                    );
                }

                transition(FormStatus.VALIDATING);
            }

            long validationRevision;

            synchronized (lock) {
                validationRevision = revision;
            }

            return CompletableFuture.supplyAsync(() -> {
                synchronized (lock) {
                    if (validationRevision != revision) {
                        throw new CompletionException(
                            new FormException(
                                "Form changed during validation"
                            )
                        );
                    }

                    List<ValidationIssue> issues =
                        validateInternal();

                    transition(
                        issues.isEmpty()
                            ? FormStatus.IDLE
                            : FormStatus.INVALID
                    );

                    return issues;
                }
            });
        }

        CompletableFuture<SubmissionResult> submitAsync(
            RegistrationRepository repository
        ) {
            return validateAsync().thenCompose(issues -> {
                if (!issues.isEmpty()) {
                    return CompletableFuture.failedFuture(
                        new ValidationException(issues)
                    );
                }

                Map<String, Object> payload;
                long submittedRevision;

                synchronized (lock) {
                    submittedRevision = revision;
                    payload = snapshot();

                    transition(FormStatus.SUBMITTING);

                    eventBus.dispatch(new FormEvent(
                        EventType.SUBMIT,
                        "form",
                        payload,
                        false
                    ));
                }

                return CompletableFuture.supplyAsync(() -> {
                    try {
                        SubmissionResult result =
                            repository.register(payload);

                        synchronized (lock) {
                            if (revision != submittedRevision) {
                                throw new FormException(
                                    "Form revision changed"
                                );
                            }

                            submissions.incrementAndGet();
                            transition(FormStatus.SUBMITTED);
                        }

                        return result;

                    } catch (RuntimeException exception) {
                        synchronized (lock) {
                            if (
                                status == FormStatus.SUBMITTING
                            ) {
                                transition(FormStatus.DIRTY);
                            }
                        }

                        throw exception;
                    }
                });
            });
        }

        void reset() {
            synchronized (lock) {
                if (status == FormStatus.SUBMITTING) {
                    throw new FormException(
                        "Cannot reset during submission"
                    );
                }

                fields.values().forEach(FieldState::reset);
                revision++;

                transition(FormStatus.IDLE);

                eventBus.dispatch(new FormEvent(
                    EventType.RESET,
                    "form",
                    snapshot(),
                    false
                ));
            }
        }

        FormStatus getStatus() {
            return status;
        }

        int getSubmissionCount() {
            return submissions.get();
        }

        Map<String, Object> getValues() {
            synchronized (lock) {
                return snapshot();
            }
        }

        @Override
        public void addListener(
            EventType type,
            EventHandler handler
        ) {
            eventBus.addListener(type, handler);
        }

        @Override
        public void removeListener(
            EventType type,
            EventHandler handler
        ) {
            eventBus.removeListener(type, handler);
        }

        @Override
        public void dispatch(FormEvent event) {
            eventBus.dispatch(event);
        }
    }

    static FormService createRegistrationForm() {
        List<FieldDefinition> fields = List.of(
            new FieldDefinition(
                "username",
                InputType.TEXT,
                true,
                true,
                30,
                ""
            ),
            new FieldDefinition(
                "email",
                InputType.EMAIL,
                true,
                true,
                100,
                ""
            ),
            new FieldDefinition(
                "password",
                InputType.PASSWORD,
                true,
                true,
                128,
                ""
            ),
            new FieldDefinition(
                "confirmPassword",
                InputType.PASSWORD,
                true,
                true,
                128,
                ""
            ),
            new FieldDefinition(
                "newsletter",
                InputType.CHECKBOX,
                false,
                false,
                1,
                false
            )
        );

        Map<String, ValidationPolicy> policies = Map.of(
            "username",
            new ValidationPolicy(3, false, null, null),

            "email",
            new ValidationPolicy(0, true, null, null),

            "password",
            new ValidationPolicy(8, false, null, null)
        );

        return new FormService(fields, policies);
    }

    public static void main(String[] args) {
        try {
            System.out.println("REACT EVENTS AND FORMS");

            FormService form = createRegistrationForm();

            form.addListener(
                EventType.CHANGE,
                event -> System.out.println(
                    "Event: " + event.target()
                )
            );

            form.setValue("username", "atul");
            form.setValue("email", "atul@example.com");
            form.setValue("password", "SecurePass123");
            form.setValue(
                "confirmPassword",
                "SecurePass123"
            );

            form.setUncontrolledValue("newsletter", true);

            System.out.println("\nForm values:");
            System.out.println(form.getValues());

            RegistrationRepository repository =
                new InMemoryRegistrationRepository();

            System.out.println("\nSuccessful submission:");

            SubmissionResult result = form
                .submitAsync(repository)
                .join();

            System.out.println(result);

            System.out.println(
                "Status: " + form.getStatus()
            );

            System.out.println("\nValidation failure:");

            FormService invalidForm = createRegistrationForm();

            invalidForm.setValue("username", "ab");
            invalidForm.setValue("email", "invalid");
            invalidForm.setValue("password", "SecurePass123");
            invalidForm.setValue(
                "confirmPassword",
                "DifferentPassword"
            );

            try {
                invalidForm.submitAsync(repository).join();

            } catch (CompletionException exception) {
                Throwable cause = exception.getCause();

                if (cause instanceof ValidationException validation) {
                    validation.getIssues().forEach(issue ->
                        System.out.println(
                            issue.field() + ": " + issue.message()
                        )
                    );
                } else {
                    throw exception;
                }
            }

            System.out.println("\nReset:");

            form.reset();

            System.out.println(form.getValues());
            System.out.println(form.getStatus());

            System.out.println("\nAssertion tests:");

            if (form.getStatus() != FormStatus.IDLE) {
                throw new AssertionError("Reset failed");
            }

            if (form.getSubmissionCount() != 1) {
                throw new AssertionError(
                    "Submission counter incorrect"
                );
            }

            try {
                form.setValue("unknown", "value");
                throw new AssertionError(
                    "Unknown field was accepted"
                );

            } catch (IllegalArgumentException expected) {
                System.out.println("Unknown field rejected");
            }

            System.out.println("All tests passed.");

        } catch (Exception exception) {
            System.err.println(
                "Application failure: " + exception.getMessage()
            );

            System.exitCodePlaceholder();
        }
    }

    private static final class System {
        static void exitCodePlaceholder() {
            java.lang.System.exit(1);
        }
    }
}
