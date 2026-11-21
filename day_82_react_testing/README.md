# React Testing: Unit Tests, Component Tests, Mocking, and User Interaction Testing

## 1. Introduction

React Testing is the process of verifying that React applications behave correctly under defined inputs, application states, external dependency responses, and user interactions.

A React application consists of components, state, props, hooks, event handlers, asynchronous operations, and interactions with external services. Testing evaluates these mechanisms independently and together.

The four principal testing areas covered in this project are:

1. Unit testing
2. Component testing
3. Mocking
4. User interaction testing

These areas serve different purposes and should not be treated as interchangeable.

| Testing area | Primary objective | Typical test target |
|---|---|---|
| Unit testing | Verify isolated logic | Functions and utilities |
| Component testing | Verify component behavior and rendering | React components |
| Mocking | Isolate external dependencies | APIs, services and callbacks |
| User interaction testing | Verify behavior resulting from user actions | Inputs, buttons, forms and navigation |

The implementations use a shared business scenario: a user directory that retrieves user records, displays loading and error states, filters users, and supports user selection.

---

## 2. Testing Architecture

The application follows a dependency-oriented structure.

**Logical architecture**

    React Application
          |
          v
    UserDirectory Component
          |
          +----------------------+
          |                      |
          v                      v
      Component State       User Interaction
          |                      |
          v                      v
      API Dependency         Search Input
          |                  Selection Action
          v
      Mock API Service
          |
          v
      Controlled Test Data

The testing architecture separates application behavior from the external systems on which that behavior depends.

The component receives an API dependency through a property. Tests can therefore replace the production implementation with a controlled mock.

This approach improves test isolation and makes failures easier to investigate.

---

## 3. Unit Testing

### 3.1 Definition

Unit testing verifies a small, independently testable part of an application.

A unit generally represents a function, method, utility, or isolated business rule.

Unit tests should focus on:

- Input validation.
- Expected output.
- Invalid input.
- Boundary conditions.
- Exceptional conditions.
- Deterministic behavior.

For React applications, common unit-testing targets include:

- Form validation functions.
- Date and currency formatting.
- Search and filtering utilities.
- Data transformation functions.
- Permission calculations.
- Business rules.
- Reducer functions.

### 3.2 Example: Email Validation

The user directory includes an email-validation function.

Its expected behavior includes:

| Input | Expected result |
|---|---|
| `alice@example.com` | Valid |
| `alice@@example.com` | Invalid |
| `alice@` | Invalid |
| Empty string | Invalid |
| Null value | Invalid |

A unit test evaluates the function directly without rendering a React component.

This distinction matters because the function's correctness should not depend on component rendering, browser events, or network availability.

### 3.3 Search Utility Testing

The search utility accepts a user collection and a search term.

It supports:

- Name matching.
- Email matching.
- Case-insensitive comparison.
- Empty search queries.
- No-match results.
- Invalid argument handling.

For a collection containing Alice, Bob, and Charlie:

| Search query | Matching records |
|---|---|
| `alice` | Alice |
| `BOB` | Bob |
| `example.com` | All users |
| Empty string | All users |
| `unknown` | No users |

### 3.4 Test Isolation

Unit tests should avoid unnecessary dependencies.

For example, testing `filterUsers()` should not require:

- A browser.
- A React rendering environment.
- An HTTP server.
- A database.
- Authentication credentials.

This reduces execution time and limits unrelated failure sources.

---

## 4. Component Testing

### 4.1 Definition

Component testing verifies a React component as a functional unit.

Unlike pure unit testing, component testing evaluates the relationship between:

- Props.
- State.
- Hooks.
- Rendering.
- Child components.
- Event handlers.
- Asynchronous operations.
- External dependencies.

The objective is to establish that the component produces the expected observable behavior.

### 4.2 UserDirectory Component

The central component implements a user directory.

Its responsibilities include:

1. Retrieving user records.
2. Managing loading state.
3. Displaying retrieved users.
4. Managing search input.
5. Filtering records.
6. Handling API failures.
7. Displaying empty results.
8. Supporting user selection.

### 4.3 Component State

The component uses React state to represent its current condition.

| State | Meaning | Expected interface |
|---|---|---|
| `idle` | Initial state | Component has not loaded |
| `loading` | Request in progress | Loading indicator |
| `success` | Request completed | User directory |
| `error` | Request failed | Error message |
| Empty results | Successful request with no matching users | No-results message |

The empty-results condition is different from an API failure.

An empty collection can represent a valid successful response. A network failure represents an unsuccessful operation.

### 4.4 State Transitions

    IDLE
      |
      v
    LOADING
      |
      +----------------------+
      |                      |
      v                      v
    SUCCESS                ERROR
      |
      v
    USER LIST
      |
      +----------------------+
      |                      |
      v                      v
    MATCHES             NO RESULTS

The tests verify the component's visible behavior at these transitions.

### 4.5 Component Test Cases

| Test case | Expected behavior |
|---|---|
| Initial rendering | Loading indicator appears |
| Successful API response | User records appear |
| Failed API request | Error message appears |
| Empty API response | Empty-state message appears |
| Initial search property | Matching records appear |
| Delayed response | Loading state remains visible |
| Component unmount | Pending updates are ignored |

### 4.6 Observable Behavior

Component tests should prioritize what users can observe rather than implementation details.

For example, a test should verify that a user can see Alice in the rendered directory.

It should not depend unnecessarily on:

- Internal state variable names.
- Hook execution counts.
- Private implementation methods.
- Internal component structure.

React Testing Library supports this approach by encouraging queries based on accessible roles, labels, and visible content.

---

## 5. Mocking

### 5.1 Definition

Mocking replaces an external dependency with a controlled implementation during testing.

A mock provides predictable behavior without requiring the actual external service.

In React applications, common dependencies requiring mocks include:

- REST APIs.
- GraphQL services.
- Authentication providers.
- Payment services.
- Browser storage.
- Third-party SDKs.
- Event listeners.
- Time-dependent operations.

### 5.2 Why Mocking Is Necessary

Consider a component that retrieves user information from an API.

Using the production API in every component test introduces several problems:

- Network dependency.
- Variable response times.
- External service outages.
- Changing production records.
- Authentication complexity.
- Difficult failure reproduction.

A mock removes these dependencies from the component test.

### 5.3 Mock API Behaviors

The implementations support several simulated responses.

| Mock behavior | Purpose |
|---|---|
| Success | Return valid user records |
| Error | Simulate network failure |
| Timeout | Simulate delayed or unavailable service |
| Empty response | Return an empty collection |
| Malformed response | Return an unexpected data structure |

These conditions allow tests to evaluate both normal and abnormal behavior.

### 5.4 Dependency Injection

The React component accepts an API function through a property.

Conceptually:

    UserDirectory
          |
          v
       API Property
          |
          +------------------+
          |                  |
          v                  v
      Production API      Mock API
          |                  |
          v                  v
      Real Service       Controlled Data

The production API and mock API implement the same expected interface.

The component does not need to know which implementation it receives.

### 5.5 Mocking Versus Stubbing

These techniques are related but have different purposes.

| Technique | Purpose |
|---|---|
| Stub | Supplies predefined responses |
| Mock | Supplies controlled responses and verifies interactions |
| Spy | Observes calls to an existing function |
| Fake | Provides a simplified working implementation |

For example:

- A stub returns three users.
- A mock returns three users and records the number of API calls.
- A spy observes whether a callback was invoked.
- A fake repository provides an in-memory implementation.

### 5.6 Mocking Limitations

A passing test using a mock does not establish that the real API works correctly.

Mocks can reproduce an incorrect contract and allow a component test to pass even when the production integration is broken.

Integration tests should therefore verify the actual boundaries between application components and external services.

---

## 6. User Interaction Testing

### 6.1 Definition

User interaction testing verifies application behavior resulting from actions performed by users.

These tests evaluate the relationship between an event and the resulting visible application behavior.

Typical interactions include:

- Clicking buttons.
- Typing into inputs.
- Clearing fields.
- Selecting options.
- Submitting forms.
- Navigating between screens.
- Keyboard interactions.
- Opening and closing dialogs.

### 6.2 Controlled Inputs

A controlled React input obtains its value from React state.

The event handler updates that state when the user enters or removes text.

    User Input
         |
         v
    Change Event
         |
         v
    Event Handler
         |
         v
    State Update
         |
         v
    Component Re-render
         |
         v
    Updated Interface

The user directory implements this mechanism through its search input.

### 6.3 Search Interaction

The search workflow is:

1. The component displays all users.
2. The user enters a search term.
3. React updates the search state.
4. The filtering function evaluates the records.
5. The component renders matching users.
6. The result count changes.

Example:

| Action | Visible users |
|---|---|
| Initial display | Alice, Bob, Charlie |
| Enter `alice` | Alice |
| Replace with `bob` | Bob |
| Enter unknown name | No users found |
| Clear input | Alice, Bob, Charlie |

### 6.4 Selection Interaction

The user directory includes a selection button for each record.

Selecting a user invokes a callback containing that user's data.

A meaningful interaction test verifies:

- The correct button is available.
- The user can activate it.
- The callback executes.
- The correct user record is supplied.

This tests the behavior across rendering, event handling, and callback execution.

### 6.5 Accessible Queries

React Testing Library provides several useful query methods.

| Query | Purpose |
|---|---|
| `getByRole` | Finds an element by accessible role |
| `getByLabelText` | Finds a control using its associated label |
| `getByText` | Finds visible text |
| `getByPlaceholderText` | Finds an input by placeholder |
| `getByTestId` | Finds an element using a testing identifier |
| `queryByRole` | Checks for an element that may be absent |
| `findByRole` | Waits for an asynchronously appearing element |

Prefer accessible queries when possible.

For example, a search field should have a meaningful label. Tests can then locate it using its accessible name rather than relying on an internal CSS class.

### 6.6 User Event Testing

`userEvent` simulates user-level interactions.

It is generally preferable to directly invoking internal event handlers because it exercises the interaction through the rendered interface.

Examples include:

- Typing text.
- Clearing an input.
- Clicking a button.
- Selecting an option.
- Keyboard navigation.

The tests should verify the resulting interface rather than merely verifying that an event handler executed.

---

## 7. Asynchronous Testing

React applications frequently perform asynchronous operations.

Common examples include:

- API requests.
- Search suggestions.
- Authentication checks.
- Data loading.
- Form submissions.
- Delayed validation.

Asynchronous tests must account for the time required for an operation and its resulting component update.

### 7.1 Waiting for Results

React Testing Library provides asynchronous queries such as `findByRole`.

These queries wait for an element to appear within a defined timeout.

`waitFor` can also repeatedly evaluate an assertion until it succeeds or the timeout expires.

### 7.2 Loading-State Validation

A useful asynchronous test verifies two separate conditions:

1. The loading indicator is initially visible.
2. The expected content appears after the request completes.

Testing only the final state would miss incorrect loading behavior.

### 7.3 Race Conditions

A race condition can occur when multiple asynchronous requests overlap.

For example:

- Request A starts.
- Request B starts.
- Request B completes first.
- Request A completes later.

If both responses update the same component state, the older response can overwrite newer information.

The JavaScript implementation uses an effect cleanup flag to prevent updates after component unmounting.

Production implementations may use `AbortController` to cancel unnecessary requests.

---

## 8. Test Organization and Execution

A structured test suite separates different levels of testing.

| Test category | Main concern | Typical execution |
|---|---|---|
| Unit | Function correctness | Frequent |
| Component | Component behavior | Frequent |
| Mocking | Dependency behavior | Frequent |
| Interaction | User workflows | Frequent |
| Integration | Connected system behavior | Before release |
| Regression | Previously detected failures | Continuous |

### 8.1 Test Fixtures

A fixture is reusable test data or setup logic.

The implementations use predefined user records to avoid repeating data initialization.

Fixtures should be:

- Predictable.
- Independent between tests.
- Easy to understand.
- Representative of realistic inputs.

Mutable test data should be isolated to prevent one test from affecting another.

### 8.2 Assertions

Assertions compare actual behavior with expected behavior.

Common assertions include:

- Equality.
- Inequality.
- Boolean conditions.
- Element presence.
- Element absence.
- Expected exceptions.
- Callback invocation.
- Dependency call counts.
- State values.

A test should fail when its expected behavior is not satisfied.

### 8.3 Test Runner

The C++ and Java implementations provide lightweight test registries.

The Python implementation uses `unittest`.

The JavaScript implementation uses Node.js built-in test execution with React Testing Library.

The PostgreSQL implementation stores test definitions, execution records, assertion results, and reports.

---

## 9. Implementation Across the Five Source Files

### 9.1 Python

**File:** `react_testing.py`

The Python implementation models the underlying testing concepts independently of React.

It includes:

- Dataclasses for user records and component state.
- Enumerations for component status.
- Pure functions for validation and search.
- An asynchronous API interface.
- A mock API implementation.
- Component lifecycle simulation.
- Asynchronous state transitions.
- Automated unit and component tests.
- Failure reporting.

`unittest.IsolatedAsyncioTestCase` is used for asynchronous test execution.

The implementation also demonstrates stale-response protection through request versioning.

This is a conceptual testing model, not a React runtime or a substitute for testing actual React components.

### 9.2 JavaScript

**File:** `react-testing.test.mjs`

The JavaScript implementation provides the actual React component-testing perspective.

It uses:

| Package or module | Responsibility |
|---|---|
| React | Component rendering and state |
| React DOM | Browser-oriented rendering support |
| React Testing Library | Component rendering and DOM queries |
| user-event | User-level interactions |
| Node.js `node:test` | Automated test execution |
| Node.js `assert` | Assertions |

The component uses:

- `useState` for component state.
- `useEffect` for asynchronous loading.
- Props for dependency injection.
- Event handlers for user interactions.
- Conditional rendering for loading and error states.

The mock API provides deterministic responses.

The test suite covers unit tests, component tests, mocking, user interactions, asynchronous behavior, and cleanup.

The file uses `React.createElement` rather than JSX so it can be executed directly without a JSX transformation step.

Required dependencies must be installed in the JavaScript project.

### 9.3 C++17

**File:** `react_testing.cpp`

The C++ implementation emphasizes test execution architecture and dependency isolation.

Its principal structures include:

| Structure | Responsibility |
|---|---|
| `User` | Domain record |
| `IUserRepository` | Dependency contract |
| `MockUserRepository` | Controlled dependency |
| `UserDirectory` | Component behavior model |
| `TestCase` | Registered test |
| `TestRunner` | Test execution |
| `TestFailure` | Assertion failure |

The program uses:

- STL vectors.
- Shared pointers.
- Lambda expressions.
- Function objects.
- Virtual interfaces.
- Exception handling.
- Standard algorithms.

The implementation distinguishes between component state, dependency behavior, and user interaction.

### 9.4 Java 17

**File:** `ReactTesting.java`

The Java implementation demonstrates an enterprise-oriented testing architecture.

It uses:

- Records for immutable domain objects.
- Enums for test categories and execution states.
- Interfaces for dependency abstraction.
- Custom exceptions.
- Generic collections.
- Streams for filtering.
- Atomic counters for mock invocation tracking.
- A centralized test registry.
- Structured execution reports.

The registry prevents duplicate test names and captures individual execution results.

The architecture separates test registration from test execution and reporting.

### 9.5 PostgreSQL

**File:** `react_testing.sql`

The PostgreSQL implementation models the administrative and reporting side of a testing environment.

It maintains relational records for:

- Test projects.
- Test suites.
- Components.
- Test cases.
- Mock dependencies.
- Mock-to-test relationships.
- User interaction scenarios.
- Assertions.
- Test runs.
- Execution results.
- Assertion results.

It also includes:

- Foreign keys.
- Unique constraints.
- Check constraints.
- Indexes.
- JSONB mock responses.
- PL/pgSQL functions.
- Validation views.
- Execution reporting views.
- Transaction handling.

The database records test execution metadata. It does not execute React components or browser interactions itself.

---

## 10. Database Workflow

The PostgreSQL schema follows this relationship:

    TEST PROJECT
         |
         v
     TEST SUITES
         |
         v
     TEST CASES
         |
         +--------------------+
         |                    |
         v                    v
     COMPONENTS          ASSERTIONS
         |
         +--------------------+
         |                    |
         v                    v
     MOCK DEPENDENCIES   INTERACTION SCENARIOS
         |
         v
      TEST RUNS
         |
         v
     TEST RESULTS
         |
         v
   ASSERTION RESULTS
         |
         v
    REPORTING VIEWS

### 10.1 Test Readiness

The `test_case_readiness` view evaluates whether a test case contains the necessary supporting information.

Examples:

- A mocking test should have a mock dependency.
- An interaction test should have interaction scenarios.
- A test case should have at least one assertion.
- Disabled test cases should not be treated as ready.

The view classifies test cases into readiness states.

### 10.2 Test Execution

The execution workflow uses three principal operations:

1. `start_test_run`
2. `record_test_result`
3. `complete_test_run`

The first operation creates an execution record.

The second stores an individual test result and updates the execution counters.

The third determines the final execution status.

### 10.3 Execution Status

| Status | Meaning |
|---|---|
| `PENDING` | Execution has not started |
| `RUNNING` | Test execution is in progress |
| `PASSED` | All expected tests completed successfully |
| `FAILED` | At least one test failed |
| `BLOCKED` | Required execution records are missing |
| `SKIPPED` | A test was not executed |

The database distinguishes failed tests from incomplete executions.

This is important because missing execution results should not be interpreted as successful tests.

### 10.4 Database Integrity

The schema enforces relationships and data consistency.

Examples:

- A test result must reference an existing test run.
- A test result must reference an existing test case.
- A test cannot have duplicate results in the same run.
- Execution times cannot be negative.
- A failed test requires an error message.
- Completed runs must have valid timestamps.

The execution functions also verify that a test case belongs to the project associated with the execution run.

---

## 11. Test Quality and Failure Analysis

A high-quality testing strategy should evaluate more than the number of passing tests.

Important considerations include:

| Quality dimension | Evaluation |
|---|---|
| Functional correctness | Does the component behave as expected? |
| Boundary coverage | Are unusual and invalid inputs tested? |
| State coverage | Are loading, success, error and empty states tested? |
| Interaction coverage | Are user actions tested through the interface? |
| Dependency isolation | Can external failures be reproduced? |
| Asynchronous correctness | Are delayed and outdated responses handled? |
| Maintainability | Are tests readable and independently executable? |
| Reliability | Are tests deterministic across repeated runs? |

### 11.1 False Positives

A false positive occurs when a test passes even though the application behavior is incorrect.

Possible causes include:

- Assertions that are too weak.
- Incorrect mock responses.
- Tests that check implementation details rather than user-visible behavior.
- Tests that do not wait for asynchronous operations.
- Shared mutable data between tests.

### 11.2 False Negatives

A false negative occurs when a test fails even though the application behavior is correct.

Possible causes include:

- Unstable timing assumptions.
- Incorrect test fixtures.
- Unnecessary dependencies.
- Environment differences.
- Overly restrictive assertions.

### 11.3 Flaky Tests

A flaky test produces inconsistent results across repeated executions without a corresponding application change.

Common causes include:

- Uncontrolled asynchronous operations.
- Shared global state.
- Unmanaged timers.
- Network dependence.
- Incorrect cleanup.
- Execution-order dependencies.

Deterministic fixtures, dependency injection, cleanup, and explicit asynchronous waiting reduce these problems.

---

## 12. Performance and Security Considerations

### 12.1 Performance

Test execution time can be improved through:

- Isolated unit tests.
- Reusable fixtures.
- Controlled mocks.
- Avoiding unnecessary network requests.
- Limiting redundant rendering.
- Running independent tests concurrently when safe.
- Selecting appropriate test timeouts.

Unit tests should generally execute faster than full integration or end-to-end tests.

### 12.2 Security

Testing environments should not expose production credentials or sensitive records.

Important controls include:

- Using synthetic test data.
- Avoiding real user credentials.
- Keeping secrets outside source files.
- Validating external API responses.
- Avoiding sensitive values in failure messages.
- Cleaning up test-created records.
- Restricting access to execution reports.
- Preventing test endpoints from accessing production resources.

Mock payloads should not contain real customer information.

---

## 13. Limitations and Technical Distinctions

The implementations serve different educational and engineering purposes.

| Implementation | What it demonstrates | What it does not provide |
|---|---|---|
| Python | Behavioral testing concepts and asynchronous component simulation | A React runtime |
| JavaScript | Actual React component testing with React Testing Library | Full browser end-to-end infrastructure |
| C++17 | Dependency isolation and test-runner design | JavaScript DOM rendering |
| Java 17 | Enterprise test registration and reporting | Native React execution |
| PostgreSQL | Test metadata, execution records and reporting | Execution of React tests |

The JavaScript file is the implementation that directly tests a React component.

The other four implementations model complementary testing mechanisms, execution concepts, and test-management structures.

React component testing is also distinct from browser end-to-end testing. A component test does not establish that an entire application works correctly across real navigation, authentication, server infrastructure, and browser environments.

A complete quality strategy uses different testing levels according to the behavior being verified.
