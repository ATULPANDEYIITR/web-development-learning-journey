# Error Handling: Reliable Programs and Controlled Failure

## Purpose and scope

Error handling defines how software detects invalid conditions, communicates failures, preserves system state, releases resources, and decides whether an operation can be retried. It is not limited to catching exceptions. A reliable implementation also establishes clear input contracts, distinguishes recoverable failures from programming defects, prevents invalid state transitions, and preserves useful diagnostic information.

The six artifacts in this collection examine these responsibilities through Python, JavaScript, C++, Java, and PostgreSQL. Their examples use data validation, deployment operations, financial transfers, and repository governance to illustrate the practical consequences of error-handling decisions.

## Errors, exceptions, and failure contracts

An **error condition** is any situation in which an operation cannot produce its intended result. An **exception** is a mechanism for transferring control from the point of failure to code that can handle or propagate it. A **failure contract** specifies which conditions an operation can report, what state remains valid after failure, and which recovery actions are permitted.

Several distinct categories matter in production systems:

| Failure category | Example | Appropriate response |
|---|---|---|
| Invalid input | A deployment port is outside the valid range | Reject the input before changing state |
| Missing resource | A requested pull request does not exist | Report a not-found failure |
| Policy violation | A protected branch lacks required approvals | Reject the operation and explain the blockers |
| Transient dependency failure | A service temporarily refuses a request | Retry only when the operation and error are suitable |
| Resource failure | A file cannot be opened | Release acquired resources and report the failure |
| Programming defect | An unexpected attribute or invariant violation | Preserve diagnostic information and avoid silently treating the defect as normal |
| State-transition failure | A merged pull request is reopened | Reject the transition without modifying the state |

These categories should remain distinguishable. If every failure becomes a generic message such as `Operation failed`, callers cannot reliably determine whether to correct input, request access, retry, or escalate a defect.

## Exception propagation and handling

An exception propagates through the call stack until a compatible handler is found. A handler should normally catch the narrowest exception type for which it has a meaningful recovery action.

Catching a broad exception is appropriate at selected boundaries, such as a command-line entry point that must log a fatal error and return a nonzero exit code. The same approach inside ordinary business logic can conceal unrelated defects.

### Python exception flow

Python's `try`, `except`, `else`, and `finally` clauses serve different purposes:

- `try` contains operations that may fail.
- `except` handles matching exception types.
- `else` executes only when the protected operations finish without raising an exception.
- `finally` executes during normal completion and exception propagation, making it suitable for cleanup that must not be skipped.

The Python implementation demonstrates this control flow and uses `raise ... from exc` to preserve the original cause when translating low-level errors into application-specific exceptions. A missing file, for example, becomes a `ResourceNotFoundError`, while the original `FileNotFoundError` remains available through the exception's cause.

### JavaScript exception flow

JavaScript supports synchronous exceptions through `throw` and `try`/`catch`/`finally`. Asynchronous code introduces an important distinction: a rejected Promise must be awaited inside the relevant `try` block or handled through Promise rejection methods.

A synchronous `try` block does not automatically catch a failure that occurs later in an unawaited Promise callback. The JavaScript implementation therefore awaits asynchronous service operations inside its handlers. Its top-level `main().catch(...)` also provides a final failure boundary and sets `process.exitCode` so automation can detect an unsuccessful run.

### C++ exception flow

C++ exceptions are propagated by throwing an object and selecting a compatible `catch` clause. The repository governance case study defines a base `GovernanceError` and specialized subclasses for validation failures, missing resources, policy violations, and invalid transitions.

Catching by reference to `const std::exception&` avoids slicing the exception object and preserves its polymorphic diagnostic information. The outermost handler catches unexpected standard exceptions, writes a diagnostic to standard error, and returns a failure status.

Resource acquisition should be paired with automatic resource management. C++'s RAII pattern ties resource lifetime to object lifetime, allowing destructors to release resources during exception unwinding. This is safer than relying on a manually executed cleanup statement after every potentially failing operation.

### Java exception flow

Java separates unchecked exceptions from checked exceptions. Checked exceptions must be caught or declared, while unchecked exceptions extend `RuntimeException` and do not impose that compile-time requirement.

The enterprise governance model uses a domain-specific runtime exception hierarchy because validation and policy failures are part of the application's operational contract. Its `catch` clauses distinguish expected policy rejection from unexpected failures. The `cause` field preserves an underlying exception when a lower-level failure is translated into a higher-level error.

### PostgreSQL error flow

PostgreSQL reports SQL failures through SQLSTATE codes and error messages. PL/pgSQL supports exception handlers that can respond to specific conditions, including uniqueness violations, check violations, insufficient privileges, and custom application errors.

An exception block establishes a subtransaction boundary. Database modifications performed in its protected section are rolled back if an error occurs there, while the handler can record or report the failure. This behavior differs from catching an exception in an ordinary programming-language function because it interacts directly with database transactional state.

## Custom exceptions and domain meaning

Custom exceptions express failure meaning through types instead of requiring callers to interpret message text.

The Python and JavaScript implementations define validation, missing-resource, external-service, and retry-exhaustion errors. The C++ and Java governance models distinguish invalid state transitions from policy rejection. PostgreSQL uses custom SQLSTATE values for selected application-level failures.

A useful hierarchy remains relatively small. Types should represent distinctions that change caller behavior, not every individual error message. For example, `InsufficientFundsError` is useful because a caller may respond differently from the way it responds to an unavailable account.

Exception messages should describe the failure without exposing credentials, tokens, private data, or sensitive configuration. Logs should preserve enough context to diagnose the incident without turning error reporting into a data-disclosure risk.

## Defensive programming and validation

Defensive programming establishes invariants at system boundaries. It does not mean wrapping every statement in `try`/`catch`. It means making invalid states difficult to create and ensuring that assumptions are checked before they influence important operations.

The implementations apply several concrete rules:

- Numeric values must be finite when the domain does not permit infinity or `NaN`.
- Monetary or percentage-like inputs must satisfy their domain constraints before calculations proceed.
- Resource identifiers and branch names must be nonempty.
- Source and target branches must differ.
- Reviewer eligibility must be checked before a review influences merge policy.
- Required checks must correspond to the current pull request head commit.
- State transitions must be validated before updating the stored state.

The Python `TransferRequest` validates a transfer before it reaches the bank. The C++ and Java models validate pull request metadata and governance policies. PostgreSQL adds `CHECK`, `UNIQUE`, foreign-key, and trigger-based enforcement so that database invariants are not dependent solely on application code.

Validation should happen as close as practical to the boundary where data enters the system. Critical invariants should also be enforced at the layer that owns the data, because other application paths may bypass a particular validator.

## Exception translation and causal diagnostics

Lower-level exceptions often reveal implementation details that callers should not need to understand. Exception translation converts these details into errors meaningful to the current layer while preserving the original cause.

The Python JSON loader converts parsing and filesystem failures into configuration-specific errors. JavaScript wraps service transport failures in `ExternalServiceError` while retaining the original exception in `cause`. Java supports the same pattern through exception constructors that accept a cause. C++ retains exception types in its inheritance hierarchy and reports the selected domain failure to callers.

Translation should not discard information needed for debugging. It should also avoid repeatedly wrapping the same exception without adding meaning. A good boundary translates when it changes the abstraction, such as converting a network timeout into a deployment-service failure.

## Retries, transient failures, and idempotency

Retries can recover from temporary service failures, but indiscriminate retries can amplify an outage or repeat an operation that already succeeded.

The Python and JavaScript examples implement bounded retries with exponential backoff. Their delays grow between attempts, and they retry only selected exception types. Validation failures and policy violations are not transient, so repeating them does not correct the underlying condition.

A production retry policy should define:

- Which failures are eligible for retry, based on the dependency's documented behavior.
- A maximum attempt count and total time budget.
- A backoff strategy, often with jitter when many clients may retry together.
- Cancellation and timeout behavior.
- Whether the operation is idempotent or protected by an idempotency key.

A read-only metadata request is usually easier to retry safely than a payment, deployment, or transfer operation. If the first request succeeds remotely but the response is lost, a second attempt can duplicate the side effect unless the operation has a deduplication mechanism.

Retry exhaustion should retain the final failure as its cause. It should not turn a persistent dependency outage into an apparently successful result.

## Resource cleanup and failure isolation

Resource cleanup must run on both successful and unsuccessful paths. The Python implementation uses context managers for temporary files, while Java's corresponding production pattern is `try`-with-resources. C++ normally uses RAII, which binds resource release to object lifetime.

The JavaScript implementation uses `Promise.allSettled` to process independent asynchronous checks. Unlike `Promise.all`, which rejects when one member rejects, `Promise.allSettled` preserves the outcome of every task. This is useful for health checks or parallel validation when a complete failure report matters more than immediate rejection.

Failure isolation should be applied carefully. A batch-processing system may legitimately reject one malformed record and continue with other records. A database transaction or financial transfer may instead require an all-or-nothing result. The correct behavior depends on the operation's consistency requirements.

## Repository governance as a case study

The C++ and Java programs model a repository governance engine. They treat merge eligibility as a collection of explicit conditions rather than a single Boolean flag supplied by an external caller.

A protected-branch policy may require independent reviewer approvals, successful status checks, resolved discussions, and the absence of merge conflicts. The engine evaluates these conditions against the pull request's current head commit. A review or status check attached to an older commit may no longer satisfy the policy when stale approvals or current-head checks are required.

The distinction between the workflow and the policy is important:

- A pull request provides the lifecycle for proposing and tracking a changeset.
- Code review records reviewer feedback and the evaluation of the proposed changes.
- An approval represents a review decision made by an eligible reviewer.
- Branch protection determines which conditions must hold before a change can enter a protected branch.
- Error handling ensures that failed conditions produce explicit, actionable rejections instead of silently changing repository state.

The C++ implementation reports multiple blockers in one eligibility report, which is more useful than failing on only the first policy condition. The Java implementation uses immutable records for review and status-check values, defensive copies for returned collections, and a service class for policy evaluation. Both prevent invalid transitions from changing the pull request state.

These programs model policy decisions rather than communicating with a Git hosting provider. A production integration must obtain authoritative review, check, commit, permission, and branch-protection data from that provider.

## Database integrity and transactional errors

The PostgreSQL implementation stores repositories, members, branches, pull requests, commits, reviews, inline comments, status checks, branch-protection policies, and governance events in related tables.

Foreign keys prevent dependent records from referencing nonexistent parent records. Unique constraints prevent duplicate repository names, duplicate branch names within a repository, and duplicate check results for the same pull request, check name, and tested commit. Check constraints reject malformed values and invalid counts.

The review-validation trigger checks whether a reviewer is eligible and rejects self-review. The pull request transition trigger prevents a merged request from returning to an earlier state. The `merge_blockers` function evaluates modeled policy conditions, while `attempt_merge` locks the target record and performs the merge decision inside the transaction.

Locking matters because two concurrent requests may otherwise evaluate the same eligibility state and both attempt to change it. In a production implementation, the relevant policy and review data must also be protected against concurrent changes, using an appropriate transaction isolation strategy or additional locking. A successful application-level check alone is not a guarantee that the database state remains unchanged until commit.

The demonstration uses an exception block to isolate a rejected merge attempt. This permits the surrounding script to continue after a modeled policy failure. Its governance event table provides an audit trail for merge decisions. Audit requirements in production may require a separate durable logging strategy, particularly when the surrounding transaction is rolled back.

## Testing failure paths

Successful execution does not establish that an error-handling implementation is correct. Tests must verify both the reported failure and the state that remains afterward.

The Python self-tests validate percentage inputs, confirm successful transfers, ensure an insufficient-funds error leaves balances unchanged, and verify retry exhaustion. The JavaScript assertions cover invalid ports, valid configuration, retry recovery, concurrent task outcomes, and invalid workflow transitions. The Java program checks that a changed head commit invalidates previously accepted evidence. The SQL script demonstrates policy evaluation, review eligibility enforcement, and transaction-scoped error handling.

A thorough test suite should also exercise missing resources, duplicate identifiers, stale checks, repeated requests, unexpected dependency failures, invalid state transitions, and concurrent operations. For transactional workflows, compare the complete relevant state before and after a rejected operation. An error message alone cannot prove that a failed operation left the system consistent.

## Production considerations

Error-handling design affects observability, security, reliability, and maintainability.

**Observability:** Record the operation, affected resource identifier, error category, correlation identifier, and relevant state. Preserve exception causes and stack traces where available. Use structured logs so incidents can be searched and aggregated.

**Security:** Do not return internal stack traces, database connection details, authentication tokens, or secrets to external callers. Separate detailed internal diagnostics from safe client-facing messages. Validate untrusted data before using it in database queries, file paths, or command arguments.

**Reliability:** Define transaction boundaries, cleanup behavior, retry limits, timeout budgets, and idempotency rules explicitly. Never report a successful operation merely because an exception was caught.

**Consistency:** Place invariants in domain objects and enforce critical relational constraints in the database. For distributed workflows, account for the possibility that a remote side effect succeeds even when the local process observes a timeout.

**Maintainability:** Use stable error types and documented contracts. Avoid relying on error-message matching for program logic, suppressing exceptions without a recovery action, or catching every exception at every layer.

**Performance:** Exception handling is appropriate for exceptional control flow, not ordinary high-volume branching. Validate common conditions directly, avoid repeated expensive diagnostic work, and bound retries so that failure recovery does not overload a degraded dependency.
