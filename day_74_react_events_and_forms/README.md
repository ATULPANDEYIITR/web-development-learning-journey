# React Events and Forms

## 1. Domain and Technical Scope

React Events and Forms cover the mechanisms through which a user interacts with an application interface, changes input values, triggers application behavior, receives validation feedback, and submits data.

The implementations model a registration workflow containing:

- Username
- Email address
- Password
- Password confirmation
- Newsletter subscription

The five implementations approach the domain from different engineering perspectives:

| Implementation | Primary responsibility |
|---|---|
| Python | Form simulation, validation, and workflow testing |
| JavaScript | Event-driven form controller and asynchronous state management |
| C++17 | Type-safe event and form management engine |
| Java 17 | Enterprise form service and validation architecture |
| PostgreSQL | Persistent form definitions, events, submissions, and audit records |

The central design principle is to distinguish input events, application state, validation decisions, and submission processing.

## 2. React Event Fundamentals

An event represents an occurrence associated with an interface interaction.

Examples include:

| Event | Purpose |
|---|---|
| `onClick` | Responds to a click |
| `onChange` | Responds to a changed input value |
| `onInput` | Responds to input modification |
| `onSubmit` | Handles form submission |
| `onBlur` | Handles loss of input focus |
| `onFocus` | Handles input focus |

React event handlers are normally registered through JSX properties.

A conceptual registration form might contain:

- A username input with `onChange`.
- An email input with `onBlur`.
- A checkbox with `onChange`.
- A submit button that triggers form submission.

The event handler receives an event object containing information about the interaction.

Important event properties include:

| Property or method | Purpose |
|---|---|
| `target` | Element that originated the event |
| `currentTarget` | Element whose handler is executing |
| `preventDefault()` | Prevents the browser's default action |
| `stopPropagation()` | Stops further propagation |
| `type` | Identifies the event type |

`preventDefault()` and `stopPropagation()` are different operations.

Preventing the default action does not automatically stop propagation. Stopping propagation does not automatically prevent the default browser action.

The Python, JavaScript, and C++ implementations model these distinctions through explicit event objects.

### Event propagation

In a nested interface, an event can travel through a hierarchy of elements.

Conceptual structure:

    Form
      |
      +-- Registration Section
             |
             +-- Submit Button

A click originating from the submit button can reach its parent elements.

The event-handling implementations demonstrate:

- Handler registration.
- Handler execution.
- Parent-child event relationships.
- Event propagation.
- Propagation cancellation.
- Default-action cancellation.

### Event delegation

Event delegation places a handler on a common parent instead of attaching independent handlers to every child element.

It is useful when:

- Many similar elements exist.
- Elements are dynamically created.
- Event handling should be centralized.
- Handler registration overhead needs to be reduced.

The JavaScript `ComponentNode` and C++ `EventTarget` provide simplified event-propagation models.

These are educational event systems rather than complete replacements for React's synthetic event implementation.

## 3. Controlled Inputs

A controlled input obtains its displayed value from application state.

The application owns the current value and updates it through an event handler.

Conceptual React structure:

    const [email, setEmail] = useState("");

    function handleChange(event) {
        setEmail(event.target.value);
    }

    <input
        type="email"
        value={email}
        onChange={handleChange}
    />

The relationship is:

    User interaction
          |
          v
    onChange handler
          |
          v
    State update
          |
          v
    Component rendering
          |
          v
    Updated input value

The displayed input value follows the state maintained by the component.

### Characteristics

- Application state is authoritative.
- Input values can be inspected at any time.
- Validation can run during input changes.
- Conditional rendering can depend on field values.
- Reset behavior can be managed centrally.
- Submission payloads can be constructed from application state.

### Advantages

Controlled inputs are useful when the application requires:

- Immediate validation.
- Dynamic form behavior.
- Conditional fields.
- Input normalization.
- Dependent form controls.
- Predictable state management.

### Tradeoffs

Every input update can trigger state processing and rendering.

Large forms should avoid unnecessary updates and expensive validation operations.

Appropriate techniques include:

- Component separation.
- Field-level state.
- Memoization.
- Debounced validation.
- Selective subscriptions.

The Python `Form`, JavaScript `FormController`, C++ `Form`, and Java `FormService` model controlled input ownership.

## 4. Uncontrolled Inputs

An uncontrolled input maintains its current value through the input element rather than treating component state as its authoritative value.

A conceptual React implementation uses a reference:

    const inputRef = useRef(null);

    function handleSubmit(event) {
        event.preventDefault();

        const value = inputRef.current.value;

        console.log(value);
    }

    <input ref={inputRef} defaultValue="" />

### Characteristics

- The DOM maintains the current input value.
- Initial values can be supplied through `defaultValue`.
- A reference can retrieve the current value.
- The application does not need to update state on every keystroke.

### Advantages

Uncontrolled inputs can be useful for:

- Simple forms.
- Integrations with existing DOM libraries.
- File inputs.
- Forms that do not require continuous state synchronization.

### Limitations

- Application state does not automatically reflect every input change.
- Dependent UI behavior requires additional coordination.
- Validation and reset logic need careful handling.
- Reading values generally requires DOM references or form submission data.

### Controlled versus uncontrolled

| Characteristic | Controlled | Uncontrolled |
|---|---|---|
| Value ownership | Application state | DOM element |
| Main value property | `value` | `defaultValue` |
| Checkbox property | `checked` | `defaultChecked` |
| Update mechanism | State update | DOM input behavior |
| Value retrieval | Application state | DOM reference |
| Continuous validation | Straightforward | Requires additional coordination |
| Reset | State reset | DOM reset or reference management |

The two approaches are different input-management strategies.

They should not be mixed accidentally for the same input. React applications should also avoid switching an input between controlled and uncontrolled modes during its lifecycle.

The implementations enforce this distinction by maintaining separate update methods.

## 5. Form State Management

A form has more state than its current input values.

A practical form controller needs to track:

- Field values.
- Initial values.
- Touched fields.
- Validation errors.
- Current status.
- Submission attempts.
- Current revision.

The implementations use the following state model:

| State | Meaning |
|---|---|
| `IDLE` | No active modification or submission |
| `DIRTY` | At least one field has changed |
| `VALIDATING` | Validation is executing |
| `INVALID` | One or more validation errors exist |
| `SUBMITTING` | Submission is being processed |
| `SUBMITTED` | Submission completed successfully |

Conceptual state flow:

    IDLE
      |
      v
    DIRTY
      |
      v
    VALIDATING
      |
      +----------> INVALID
      |                |
      |                v
      |              DIRTY
      |
      v
    SUBMITTING
      |
      +----------> DIRTY
      |
      v
    SUBMITTED

The transition model prevents arbitrary changes between states.

For example, an application should not mark a form as successfully submitted before validation and submission processing have completed.

The implementations maintain a revision counter to detect changes occurring during asynchronous operations.

A revision identifies a particular version of form data.

This is useful when validation or submission takes time and the underlying values might change.

## 6. Form Validation

Validation checks whether user-provided values satisfy application requirements.

Validation should be separated into distinct layers.

### 6.1 Required-field validation

Checks whether a required field contains a meaningful value.

Examples:

- Username must not be empty.
- Email must not be empty.
- Password must not be empty.

Whitespace-only strings should not satisfy a required text field.

### 6.2 Length validation

Checks the permitted input length.

Examples:

| Field | Minimum | Maximum |
|---|---:|---:|
| Username | 3 | 30 |
| Email | Application-defined | 100 |
| Password | 8 | 128 |

Length limits help maintain consistent application data and reduce excessive input.

### 6.3 Format validation

Checks whether a value follows an expected format.

Email validation uses a regular expression in the implementations.

Regular expressions are useful for basic format checking, but they cannot establish that an email address exists or that its owner controls it.

### 6.4 Numeric validation

Checks:

- Numeric conversion.
- Finite numeric values.
- Minimum permitted values.
- Maximum permitted values.

A numeric field should reject values such as `NaN` and infinity when finite values are required.

### 6.5 Cross-field validation

Some validation rules depend on multiple fields.

The registration workflow contains one example:

    password == confirm_password

Both fields can independently satisfy their required-field rules while still failing cross-field validation.

The error belongs to the confirmation field because that field is where the mismatch is resolved.

### 6.6 Asynchronous validation

Some checks require external information.

Examples include:

- Email uniqueness.
- Username availability.
- Remote eligibility checks.
- Verification against an external service.

Asynchronous validation introduces additional concerns:

- Network delays.
- Service failures.
- Stale responses.
- Concurrent requests.
- Duplicate submissions.

The Python and JavaScript implementations simulate an email-availability check.

The Java implementation uses `CompletableFuture` for asynchronous execution.

In a production application, remote validation should use authenticated server endpoints and should not replace final server-side validation.

## 7. Validation Responsibilities

Validation should be performed at more than one application boundary.

| Layer | Responsibility |
|---|---|
| Browser input | Immediate user feedback |
| Component or form controller | Form-state consistency |
| Backend service | Authoritative business validation |
| Database | Persistent data integrity |

Client-side validation improves usability but is not a security boundary.

A user can bypass browser-side checks by directly submitting HTTP requests.

The backend must independently validate all relevant values.

Database constraints should enforce persistent invariants wherever possible.

Password handling requires additional security controls:

- Never log passwords.
- Never return passwords in API responses.
- Never store plaintext passwords.
- Use a suitable password-hashing algorithm with an appropriate work factor.
- Apply server-side length and complexity policies.
- Protect registration endpoints against abuse.

The sample implementations deliberately avoid printing password values.

## 8. Form Submission Lifecycle

Form submission combines validation, state management, and communication with a backend service.

The expected workflow is:

    User enters data
          |
          v
    Submit event
          |
          v
    Prevent default browser behavior
          |
          v
    Read current form values
          |
          v
    Validate fields
          |
          +------> Validation failed
          |              |
          |              v
          |         Display errors
          |
          v
    Validate business rules
          |
          v
    Send request
          |
          v
    Backend processing
          |
          +------> Failure
          |           |
          |           v
          |      Display failure
          |
          v
    Success response
          |
          v
    Submitted state

An important distinction exists between form validation and successful submission.

A valid form is eligible for submission. It is not necessarily a successfully submitted form.

Submission can still fail because of:

- Network errors.
- Authentication failures.
- Duplicate records.
- Server errors.
- Database constraints.
- External service unavailability.

The implementations model this distinction through separate validation and submission operations.

## 9. Python Implementation

The Python script provides an object-oriented simulation of form management.

### Main components

| Component | Responsibility |
|---|---|
| `Event` | Stores event information |
| `EventEmitter` | Registers and executes handlers |
| `EventNode` | Models event propagation |
| `Field` | Represents an input |
| `Validator` | Performs field validation |
| `Form` | Maintains form state |
| `register_user` | Simulates backend registration |

### Important mechanisms

The implementation uses:

- Dataclasses for structured field and event information.
- Enums for event types and form states.
- Dictionaries for field and error management.
- Lists for validation messages.
- Regular expressions for email validation.
- Exceptions for invalid operations.
- `asyncio` for asynchronous processing.

The form controller exposes separate methods for controlled and uncontrolled fields.

`validate()` performs local validation.

`validate_async()` simulates an external validation operation.

`submit()` coordinates validation and submission.

`reset()` restores initial values and clears errors.

### Failure handling

The implementation rejects:

- Unknown field names.
- Duplicate field names.
- Invalid validation configuration.
- Controlled-field updates through the uncontrolled interface.
- Uncontrolled-field updates through the controlled interface.
- Invalid input values.
- Failed submissions.

Assertions verify basic validation, state reset, and field lookup behavior.

## 10. JavaScript Implementation

The JavaScript implementation uses Node.js event-driven programming rather than a direct line-by-line translation of the Python implementation.

### Main components

| Component | Responsibility |
|---|---|
| `UIEvent` | Represents an interface event |
| `ComponentNode` | Models event propagation |
| `Field` | Maintains field information |
| `ValidationEngine` | Executes validation rules |
| `FormController` | Manages application state |
| `registrationService` | Simulates an asynchronous API |

### Event-driven architecture

The `FormController` extends Node.js `EventEmitter`.

It publishes events such as:

- `change`
- `stateChange`
- `submit`
- `submitted`
- `reset`

This allows separate components to react to form changes without requiring direct dependencies between them.

### State transitions

The `transition()` method checks permitted state changes.

Invalid transitions raise an exception.

The `revision` counter identifies changes to the form.

The submission process captures a revision before validation and checks whether the form has changed before accepting the result.

### Asynchronous behavior

JavaScript uses Promises and `async/await`.

`validateAsync()` simulates remote validation.

`submit()` prevents concurrent duplicate submission operations by sharing the pending Promise.

`AbortController` provides a mechanism for cancelling an outdated validation operation.

A production application should also handle network cancellation, server idempotency, request timeouts, and retry policies.

## 11. C++17 Implementation

The C++ program emphasizes type safety and explicit domain modeling.

### Main components

| Component | Responsibility |
|---|---|
| `UIEvent` | Event data |
| `EventTarget` | Handler registration and propagation |
| `Field` | Input state |
| `FieldRules` | Validation configuration |
| `ValidationEngine` | Field validation |
| `Form` | State and submission management |

### Type-safe input values

The implementation uses `std::variant` to represent different value types:

- String.
- Boolean.
- Double.

This allows checkbox values to remain Boolean instead of representing them as arbitrary strings.

### STL usage

The program uses:

- `std::map` for predictable field lookup.
- `std::vector` for validation messages.
- `std::set` for allowed state transitions.
- `std::function` for event callbacks.
- `std::shared_ptr` for parent event relationships.
- `std::variant` for typed values.
- `std::regex` for format validation.

### Engineering considerations

The program validates input before updating state.

The event system uses ordered handlers.

The form prevents modification during active submission.

The state-transition model explicitly rejects invalid transitions.

The implementation is a standalone form engine and does not require a browser or React runtime.

## 12. Java 17 Implementation

The Java implementation models an enterprise-oriented form-management service.

### Architecture

    FieldDefinition
          |
          v
    FieldState
          |
          v
    FormService
          |
          +---- EventBus
          |
          +---- ValidationService
          |
          +---- RegistrationRepository
          |
          v
    SubmissionResult

### Domain types

The implementation uses Java records for immutable structures:

- `FormEvent`
- `ValidationIssue`
- `SubmissionResult`
- `FieldDefinition`
- `ValidationPolicy`

Enums define input types, event types, and form states.

`FieldState` maintains mutable values separately from immutable field definitions.

### Service separation

`ValidationService` evaluates validation rules.

`FormService` owns state transitions and field updates.

`EventBus` distributes events to registered listeners.

`RegistrationRepository` defines the registration persistence boundary.

`InMemoryRegistrationRepository` supplies a runnable implementation.

### Asynchronous processing

`CompletableFuture` provides asynchronous validation and submission.

The form service uses synchronization around shared state.

The repository uses a concurrent set to prevent duplicate email registration within the running process.

The in-memory repository is suitable for demonstrating the service boundary but does not provide durable persistence.

The PostgreSQL implementation provides the corresponding relational data model.

## 13. PostgreSQL Implementation

The SQL script models the persistent lifecycle of a form.

The `react_forms` schema separates form-related tables from unrelated application objects.

### Relational structure

    Forms
      |
      +---- Form Fields
      |         |
      |         +---- Validation Policies
      |
      +---- Form Sessions
                 |
                 +---- Field Values
                 |
                 +---- Form Events
                 |
                 +---- Form Submissions
                            |
                            +---- Validation Errors

### Table responsibilities

| Table | Purpose |
|---|---|
| `forms` | Defines form configurations |
| `form_fields` | Defines individual input fields |
| `validation_policies` | Stores validation requirements |
| `form_sessions` | Tracks individual form interactions |
| `field_values` | Stores session-specific field values |
| `form_events` | Stores interaction events |
| `form_submissions` | Records submission attempts |
| `validation_errors` | Stores validation failures |
| `form_state_history` | Records state changes |

### Constraints

The database uses:

- Primary keys.
- Foreign keys.
- Unique constraints.
- Check constraints.
- Enum types.
- JSONB type checks.
- Validation triggers.

These mechanisms prevent several classes of inconsistent persistent data.

For example, the field-value trigger checks that a field belongs to the form associated with the current session.

It also checks basic value types and maximum lengths.

### State-transition enforcement

The `validate_form_transition()` function enforces permitted form-state changes.

The `audit_form_transition()` function records state and revision changes.

This provides a persistent record of important workflow transitions.

### Submission processing

The `process_form_submission()` function performs the following operations:

1. Locks the relevant session row.
2. Checks whether the session exists.
3. Prevents duplicate processing of completed sessions.
4. Changes the session state to validation.
5. Executes field validation.
6. Constructs a JSONB submission payload.
7. Records the submission attempt.
8. Persists validation errors when validation fails.
9. Marks valid submissions as processing.
10. Records successful completion.

The function executes within the caller's PostgreSQL transaction.

The sample script demonstrates both valid and invalid submissions.

### Reporting

The database provides:

- Submission counts.
- Completed and rejected submissions.
- Event-frequency reporting.
- Validation-error aggregation.
- Current session status.
- Submission eligibility evaluation.

Indexes support common retrieval patterns involving session status, event timestamps, form relationships, and submission status.

## 14. React Events and Forms: Important Distinctions

| Concept | Meaning |
|---|---|
| Event | An occurrence caused by an interaction |
| Event handler | A function responding to an event |
| Event propagation | Movement of an event through an element hierarchy |
| Controlled input | Input value managed by application state |
| Uncontrolled input | Input value maintained by the DOM |
| Form state | Current application representation of form data |
| Validation | Evaluation of input against defined rules |
| Submission | Processing a completed form |
| Asynchronous validation | Validation involving delayed or external operations |
| State transition | Movement between permitted application states |
| Reset | Restoration of initial form values |
| Revision | Identifier for a particular form-data version |

These concepts have different responsibilities.

An event handler does not automatically validate data.

Validation does not automatically submit a form.

A successful local validation does not establish that a backend operation succeeded.

A controlled input does not automatically guarantee valid data.

Each mechanism must be designed and tested independently.

## 15. Performance Considerations

### Event handling

Avoid unnecessary handler registration and repeated expensive operations.

Event delegation can reduce the number of independently registered handlers.

### Controlled inputs

Large controlled forms can produce frequent component updates.

Use appropriate component boundaries and selective state updates.

### Validation

Avoid expensive validation on every keystroke when it is not necessary.

Debouncing can reduce repeated remote requests.

### Asynchronous operations

Cancel outdated requests where possible.

Use revision checks to reject stale validation results.

Prevent duplicate submissions through application-level request management and server-side idempotency.

### Database

Use indexes according to actual query patterns.

Avoid unnecessary indexes because they increase storage and write costs.

Keep transactions short when processing submissions.

For larger systems, external API processing should generally be separated from database transactions using a durable job or transactional outbox pattern.

## 16. Security Considerations

Forms are a common entry point for untrusted data.

Important controls include:

- Server-side validation.
- Parameterized SQL operations.
- Input-size limits.
- Authentication and authorization.
- CSRF protection where applicable.
- Output encoding.
- Secure password hashing.
- Rate limiting.
- Duplicate-submission protection.
- Safe error messages.
- Restricted access to sensitive records.

Client-side validation must never be treated as sufficient protection.

The SQL script demonstrates relational constraints and validation triggers, but a production application also requires database permissions and an authenticated application service.

The JavaScript and Python examples simulate service interactions and do not implement production authentication or network security.

## 17. Edge Cases and Failure Conditions

| Scenario | Expected handling |
|---|---|
| Empty required field | Reject validation |
| Invalid email | Reject validation |
| Password mismatch | Reject cross-field validation |
| Excessive input length | Reject field update |
| Unknown field | Raise an error |
| Duplicate field definition | Reject configuration |
| Incorrect checkbox type | Reject input |
| Remote validation failure | Preserve failure state |
| Duplicate submission | Prevent concurrent processing |
| Stale asynchronous result | Reject outdated result |
| Backend failure | Return to recoverable state |
| Reset during submission | Reject reset operation |
| Invalid state transition | Raise an error |

These cases demonstrate why form processing requires explicit state management rather than a single submit handler.

## 18. Implementation Limitations

The five implementations provide complementary educational models, not complete browser-based React applications.

| Implementation | Deliberate limitation |
|---|---|
| Python | Simulates events without a browser DOM |
| JavaScript | Uses Node.js event handling rather than React rendering |
| C++17 | Models event propagation without browser integration |
| Java 17 | Uses an in-memory repository |
| PostgreSQL | Provides a relational workflow without an HTTP application layer |

The event systems do not reproduce every React-specific behavior, including the complete synthetic event lifecycle, component reconciliation, hook scheduling, or DOM rendering.

The database validation functions demonstrate basic rules rather than a complete production validation framework.

These distinctions matter when transferring the models into an actual React application.

## 19. Execution

### Python

Requirements: Python 3.10 or later.

- Save the first source file as `react_events_forms.py`.
- Run `python react_events_forms.py`.

### JavaScript

Requirements: Node.js 18 or later.

- Save the second source file as `react_events_forms.js`.
- Run `node react_events_forms.js`.

### C++17

Requirements: C++17-compatible compiler.

- Save the third source file as `react_events_forms.cpp`.
- Compile using `g++ -std=c++17 -Wall -Wextra -O2 react_events_forms.cpp -o react_events_forms`.
- Run `./react_events_forms` or `.\react_events_forms.exe` on Windows.

### Java 17

Requirements: Java Development Kit 17.

- Save the fourth source file as `ReactEventsForms.java`.
- Compile using `javac ReactEventsForms.java`.
- Run `java ReactEventsForms`.

### PostgreSQL

Requirements: PostgreSQL 16 or later.

- Save the fifth source file as `react_events_forms.sql`.
- Execute using `psql -U postgres -d your_database -f react_events_forms.sql`.

The database script creates the `react_forms` schema, its database objects, sample registration sessions, validation records, and reporting queries.

The PostgreSQL account executing the script must have the required schema and database privileges. The `gen_random_uuid()` function must be available.

**Java source correction for standalone execution:** The Java implementation's final error-handling block uses a nested exit helper to avoid naming conflicts with the form domain. It can be replaced with the conventional `java.lang.System.exit(1)` directly in the catch block without changing application behavior.

## 20. Technical Learning Outcomes

The implementations establish the relationship between:

- Event-driven interaction.
- Controlled and uncontrolled input management.
- Form-state ownership.
- Validation policies.
- Cross-field dependencies.
- Asynchronous processing.
- Submission lifecycle management.
- Typed domain modeling.
- Persistent relational workflows.
- Failure recovery.
- Application and database security.

The central architectural distinction is that events communicate what happened, form state records the application's current values, validation determines whether those values satisfy defined rules, and submission processing determines whether the backend operation succeeds.
