# Async/Await and Concurrent Asynchronous Workflows

## Scope

This project studies asynchronous programming through four related mechanisms:

| Mechanism | Purpose |
|---|---|
| `async` functions | Define operations that can suspend while waiting for external or delayed work |
| `await` | Suspend the current asynchronous operation until a result is available without blocking the event-loop or asynchronous task model |
| Error handling | Convert failures, timeouts, cancellations, and retry exhaustion into explicit outcomes |
| Parallel operations | Start independent asynchronous work together and collect their results without unnecessary sequential waiting |

The five implementations use a common operational scenario: several application services must be contacted while a workflow coordinates dependencies, failures, time limits, retries, and concurrency.

The central distinction is between **asynchronous execution** and **parallel execution**. An asynchronous function can wait without blocking its execution environment. Parallel operations are achieved when independent asynchronous tasks are started before awaiting their combined results.

A useful relationship is:

**operation → suspension point → independent work → completion or failure → workflow decision**

The implementations deliberately use different models:

- Python uses `asyncio`, coroutines, task aggregation, cancellation, timeouts, retries, and semaphores.
- JavaScript uses promises, `async`/`await`, `Promise.all`, `Promise.allSettled`, `Promise.race`, `AbortController`, and bounded worker consumption.
- C++ uses `std::async`, futures, exceptions, threads, and a bounded executor.
- Java uses `CompletableFuture`, explicit domain records, an executor, timeout handling, delayed retry execution, and asynchronous composition.
- PostgreSQL represents asynchronous workflow state as persistent jobs, operations, dependencies, attempts, events, and transactional state transitions.

## Asynchronous Execution Model

An asynchronous function does not imply that every operation runs simultaneously.

Consider three independent operations:

**Sequential**

`A → wait → B → wait → C → wait`

**Concurrent asynchronous scheduling**

`A ─────────→ result`  
`B ───────→ result`  
`C ──────────→ result`

The second model reduces total waiting time when operations spend significant time waiting for I/O or other external events.

For independent operations, the useful completion time is approximately:

`max(duration(A), duration(B), duration(C))`

rather than:

`duration(A) + duration(B) + duration(C)`

This relationship assumes that the runtime, dependencies, and external services can support concurrent work.

## Python Implementation

The Python program models service orchestration using `asyncio`.

`fetch_service` uses `await asyncio.sleep(...)` to simulate I/O waiting. The sleep is important because it gives the event loop an opportunity to execute other ready coroutines.

`run_sequential` intentionally awaits each operation before starting the next one. This provides a baseline for understanding why independent operations should not be unnecessarily serialized.

`run_parallel` passes several coroutines to `asyncio.gather`. Their execution can overlap while they are waiting.

`run_parallel_with_isolated_errors` uses `return_exceptions=True`. This is different from ordinary `gather` behavior because an individual failure becomes a result that can be inspected rather than preventing the caller from receiving the complete collection.

The program also implements:

- `asyncio.wait_for` for time limits.
- Exponential retry delays for transient failures.
- Explicit `CancelledError` handling for cooperative cancellation.
- `asyncio.Semaphore` for bounded concurrency.
- `JobResult` as an immutable result model.
- Type annotations and validation for operational parameters.

### Python failure behavior

An exception raised by an awaited coroutine propagates to the awaiting function unless explicitly handled. This makes `try`/`except` part of asynchronous control flow rather than an optional logging mechanism.

Timeouts and cancellation should not be treated as ordinary successful results. They represent different operational states and may require cleanup, retry, compensation, or termination.

The semaphore example prevents unrestricted fan-out. Without such a limit, a large workload could create too many concurrent requests and exhaust connection pools, remote service quotas, file descriptors, memory, or other resources.

## JavaScript Implementation

The JavaScript implementation treats asynchronous operations as promises.

`callService` is an `async` function. Its returned promise represents a future result.

`sequentialChecks` demonstrates sequential awaiting, while `parallelChecks` creates multiple promises before calling `Promise.all`.

`Promise.all` has an important failure property: rejection of one promise rejects the aggregate promise. It is appropriate when the complete operation is considered unsuccessful if any required dependency fails.

`Promise.allSettled` provides a different semantic model. The `parallelWithFailureIsolation` function uses it when each operation should report its own success or failure.

This distinction is important in real systems:

| Requirement | Suitable mechanism |
|---|---|
| Every dependency must succeed | `Promise.all` |
| Collect every independent outcome | `Promise.allSettled` |
| First completed result or timeout | `Promise.race` |
| Cancel an application-controlled operation | `AbortController` |

The timeout implementation uses `Promise.race`. The cancellation example uses `AbortSignal` and removes the timer when cancellation occurs.

The bounded concurrency implementation does not create an unlimited number of active workers. It maintains a small set of consumers that acquire the next available item. This pattern is appropriate for large queues where starting every operation simultaneously would create excessive resource pressure.

## C++ Implementation

The C++ program uses futures as explicit representations of asynchronous results.

`std::async` launches work asynchronously and returns a `std::future`. Calling `future.get()` retrieves the result and rethrows an exception generated by the asynchronous operation.

The `NamedAsyncService` class encapsulates service-specific behavior and converts exceptions into a `TaskResult`. This allows the example to report successful and failed operations independently.

The bounded executor uses:

- a work queue,
- a mutex,
- worker threads,
- a configurable concurrency limit,
- result storage indexed by original task position.

This differs from the Python and JavaScript implementations by making scheduling resources more explicit.

The retry function uses a callable returning a future. Failed attempts are retried with increasing delays.

C++ exception propagation through futures is significant. A worker can fail independently, but the exception becomes visible when its future is consumed.

### C++ resource considerations

Unrestricted asynchronous work is not automatically safe. Every asynchronous operation consumes resources such as:

- threads or scheduler capacity,
- memory,
- sockets,
- database connections,
- CPU time,
- operating-system handles.

The bounded executor demonstrates why concurrency limits are a resource-governance mechanism rather than merely a performance feature.

## Java Implementation

The Java program models asynchronous workflows with `CompletableFuture`.

`RemoteService` implements an `AsyncOperation` interface, separating domain behavior from workflow coordination.

The `OperationResult` record provides an immutable representation of:

- completed operations,
- failed operations,
- timed-out operations.

`runParallel` creates independent futures and combines them with `CompletableFuture.allOf`.

The program deliberately converts individual operation failures into `OperationResult` values before aggregation. This prevents one failed service from hiding the outcome of other independent operations.

`withTimeout` uses `orTimeout` to impose an upper bound on asynchronous completion.

The retry implementation uses `delayedExecutor` and recursively composes asynchronous attempts. The delay grows after each failure, reducing pressure on a dependency that may be temporarily unavailable.

The fixed thread pool provides explicit control over the execution resources used by the example. In an enterprise service, executor sizing should account for workload type, blocking behavior, dependency capacity, and application resource limits.

## PostgreSQL Workflow Model

The PostgreSQL implementation treats asynchronous processing as persistent state rather than as an in-memory coroutine mechanism.

The primary entities are:

| Table | Responsibility |
|---|---|
| `async_job` | Represents a complete asynchronous workflow |
| `async_operation` | Represents an individual unit of work |
| `operation_dependency` | Defines which operations must complete first |
| `operation_attempt` | Records execution attempts and failures |
| `async_event` | Provides an audit trail of state transitions |

The model distinguishes job-level state from operation-level state.

An operation can be:

`pending → running → completed`

or:

`pending → running → failed`

and may also reach:

`running → timed_out`

or:

`running → cancelled`

The database does not attempt to behave like an application event loop. Instead, it provides durable coordination and integrity rules that an asynchronous application can rely on.

## Dependency-Aware Execution

Dependencies are represented separately from operations.

For example:

`load-customer ─┐`  
`              ├→ calculate-total → send-receipt`  
`load-inventory ┘`

`calculate-total` is not eligible to start until both prerequisite operations are completed.

The `start_operation` function evaluates dependency state before changing an operation from `pending` to `running`.

This prevents application code from accidentally starting a dependent operation too early.

The same concept appears in application code as a promise or future dependency, but the SQL representation has a durable advantage: the dependency relationship survives process restarts.

## Error Handling

Asynchronous failures have several distinct meanings.

### Ordinary failure

A dependency returns an error or an operation throws an exception.

This should normally produce an explicit failed state.

### Timeout

An operation exceeds an agreed time boundary.

A timeout is not necessarily proof that the remote system failed. The remote operation may still be executing. Systems that retry after a timeout therefore need to consider duplicate effects and idempotency.

### Cancellation

The caller no longer wants the result.

Cancellation should normally release resources and stop work where the runtime and operation support cooperative cancellation.

### Retry exhaustion

A transient operation can be retried a limited number of times. After the retry budget is exhausted, the operation should become a durable failure rather than retry indefinitely.

## Parallel Operations

Parallelism is appropriate only when operations are independent or when their dependencies have already been satisfied.

The implementations distinguish:

**Independent work**

`A ─────→ result`  
`B ───→ result`  
`C ───────→ result`

from:

**Dependent work**

`A → B → C`

Starting `B` before `A` completes would violate the dependency relationship.

Parallelism also has capacity limits. If an application sends 10,000 requests simultaneously, the theoretical reduction in waiting time can be outweighed by connection exhaustion, rate limits, memory pressure, CPU scheduling, and downstream overload.

Bounded concurrency therefore provides a practical middle ground:

`queue → limited workers → external operations → results`

## Error Aggregation

A key design decision is whether one failure should fail the complete workflow.

For an all-or-nothing operation, aggregate failure is appropriate.

For independent diagnostics, monitoring checks, batch processing, or multiple optional services, individual results are more useful.

The source implementations expose both patterns rather than treating them as interchangeable.

A robust result model should preserve:

- operation identity,
- success or failure state,
- result data when successful,
- error information when unsuccessful,
- timeout information when applicable,
- attempt information when retries are used.

## Retry and Backoff

Retries are useful for transient failures such as temporary network errors or overloaded dependencies.

They are unsafe when applied blindly to operations that are not idempotent.

For example, retrying a read request is usually simpler than retrying an operation that charges a payment account. If the first request succeeded but its response was lost, a naive retry could duplicate the side effect.

The examples use exponential delays:

`base delay × 2^attempt`

This reduces immediate repeated pressure on an unavailable dependency.

Production retry policies may also require:

- maximum elapsed retry time,
- jitter,
- error classification,
- idempotency keys,
- circuit breakers,
- dependency-specific limits.

## Timeouts

Timeouts establish a boundary for how long a caller is willing to wait.

They should be applied at appropriate levels. A very short global timeout can cancel valid slow operations, while an unlimited timeout can cause requests and resources to accumulate indefinitely.

A timeout should also be distinguished from cancellation. A timeout means the configured time budget expired. Cancellation means the caller explicitly no longer requires the operation.

## Cancellation

Cancellation is cooperative in the featured implementations.

Python handles `CancelledError` around an awaited operation.

JavaScript uses `AbortController` and `AbortSignal`.

Java's future-based model supports cancellation-oriented future operations, although application-specific cancellation semantics still need to be designed.

C++ requires explicit coordination between threads and operations when cooperative cancellation is needed.

Cancellation is especially important for operations holding external resources. Cleanup should occur even when the caller stops waiting.

## Database Integrity

The PostgreSQL schema uses constraints to prevent invalid state combinations.

Examples include:

- positive concurrency limits,
- positive timeout values,
- positive retry counts,
- unique operation names within a job,
- foreign-key enforcement,
- prevention of an operation depending directly on itself,
- timestamp consistency.

The `operation_attempt` table prevents duplicate attempt numbers for a single operation.

The status-change trigger records operation transitions in `async_event`, creating an auditable history without requiring every application path to write a separate audit record.

## Transactional Behavior

The SQL workflow uses a transaction to coordinate multiple state changes.

A transaction makes the sequence atomic from the database perspective. If an error occurs before `COMMIT`, the transaction can be rolled back instead of leaving a partially updated workflow.

This is separate from asynchronous execution itself.

An asynchronous application may perform work concurrently while using short database transactions to protect individual state transitions.

Long-running database transactions should generally be avoided for external asynchronous work because they can hold locks and resources while waiting for unrelated systems.

## Performance Considerations

The major performance distinction is waiting time versus execution capacity.

For I/O-heavy workloads, asynchronous concurrency can improve utilization because one operation can make progress while another waits.

For CPU-heavy workloads, asynchronous syntax alone does not make computation faster. CPU-bound work can still monopolize execution resources and may require worker threads, processes, or specialized computation strategies.

Concurrency should therefore be bounded according to:

- downstream capacity,
- connection-pool size,
- memory usage,
- CPU availability,
- expected latency,
- rate limits,
- failure-retry behavior.

A useful operational model is:

**throughput = concurrency × useful work rate**

until another bottleneck becomes dominant.

## Security Considerations

Asynchronous workflows can amplify security problems because high concurrency can magnify the number of requests made to a dependency.

Relevant controls include:

- validating operation parameters before scheduling work,
- enforcing concurrency limits,
- enforcing timeouts,
- limiting retries,
- avoiding sensitive information in exception messages,
- protecting credentials outside application data structures,
- using authenticated and encrypted service connections,
- preventing untrusted input from controlling unbounded fan-out,
- ensuring retries do not duplicate privileged side effects.

Database functions also require deliberate privilege design. Application roles should receive only the permissions required to perform their workflow operations.

## Failure Modes

| Failure mode | Consequence | Appropriate control |
|---|---|---|
| Sequential awaits for independent work | Unnecessary latency | Start independent operations before awaiting |
| One rejected promise hides other results | Incomplete batch visibility | `Promise.allSettled` or explicit result conversion |
| Unlimited concurrency | Resource exhaustion | Semaphore, worker pool, or bounded executor |
| No timeout | Requests remain active indefinitely | Timeout policy |
| Unlimited retries | Dependency overload | Attempt and time budgets |
| Retry of non-idempotent operation | Duplicate side effects | Idempotency strategy |
| Ignored cancellation | Resource leakage | Cooperative cleanup |
| Shared mutable state | Race conditions | Controlled ownership and synchronization |
| Long database transaction | Lock and resource retention | Short transactional state transitions |
| Hidden dependency ordering | Invalid workflow state | Explicit dependency representation |

## Cross-Implementation Relationship

The implementations intentionally use different abstractions for the same core workflow:

| Concern | Python | JavaScript | C++ | Java | PostgreSQL |
|---|---|---|---|---|---|
| Async operation | Coroutine | Promise | Future | `CompletableFuture` | Persistent operation row |
| Waiting | `await` | `await` | `future.get()` | future composition | Transactional state |
| Parallel aggregation | `asyncio.gather` | `Promise.all` / `allSettled` | Multiple futures | `CompletableFuture.allOf` | Dependency queries |
| Timeout | `asyncio.wait_for` | `Promise.race` | Application-controlled future strategy | `orTimeout` | Timeout state |
| Retry | Coroutine factory | Promise factory | Future factory | Future supplier | Attempt records |
| Concurrency limit | Semaphore | Worker consumers | Bounded executor | Fixed executor | Job policy |
| Cancellation | `CancelledError` | `AbortController` | Thread coordination | Future cancellation model | Cancelled state |
| Audit | Application results | Promise outcomes | Result objects | Immutable records | Event table |

The common principle is that asynchronous programming separates **starting work**, **waiting for completion**, **handling failure**, and **deciding what work can proceed next**.

Those responsibilities should remain explicit as workflows become more complex.
