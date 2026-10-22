# Promise States and Promise Combinators

This project studies JavaScript Promises as a stateful abstraction for asynchronous computation. It focuses on the transition from a pending operation to a fulfilled or rejected operation, the propagation of results and errors through chains, and the distinct coordination semantics provided by `Promise.all`, `Promise.race`, `Promise.allSettled`, and `Promise.any`.

The five implementations deliberately use different perspectives:

| File | Primary perspective | Main implementation |
|---|---|---|
| Python | Asynchronous workflow simulation | `asyncio`, tasks, cancellation, result modeling |
| JavaScript | Native Promise behavior | Promises, microtasks, chaining, combinators |
| C++17 | Concurrent service engine | Threads, condition variables, explicit state machine |
| Java 17 | Enterprise deployment workflow | `CompletableFuture`, domain records, policies |
| PostgreSQL | Persistent asynchronous-operation model | State constraints, triggers, functions, reporting |

The implementations model the same conceptual domain without simply translating one program into another.

## Promise State Model

A Promise represents an eventual outcome rather than an immediately available value.

Its fundamental lifecycle is:

    ┌──────────────┐
    │    pending   │
    └──────┬───────┘
           │
    ┌──────┴──────────┐
    │                 │
    ▼                 ▼
┌────────────┐  ┌────────────┐
│ fulfilled  │  │  rejected  │
└────────────┘  └────────────┘

A Promise begins in the `pending` state. It may transition once to `fulfilled` with a value or once to `rejected` with a reason.

A settled Promise does not transition back to `pending`, and it cannot subsequently change from fulfillment to rejection or from rejection to fulfillment.

The JavaScript runtime enforces this behavior for native Promises. The Python, C++, and PostgreSQL implementations explicitly model the same one-way settlement rule.

## Chaining

Promise chaining connects asynchronous operations so that the result of one operation becomes the input to another.

Conceptually:

    Operation A
        │
        │ fulfillment value
        ▼
    Operation B
        │
        │ transformed value
        ▼
    Operation C

In JavaScript, `.then()` creates a new Promise. A fulfillment handler can return a normal value, causing the next Promise to fulfill, or return another Promise, causing the next Promise to adopt that Promise's eventual state.

An exception thrown inside a `.then()` handler produces a rejected Promise.

This makes a chain a mechanism for both data transformation and error propagation.

The Java implementation expresses a similar workflow with `CompletableFuture.thenCompose()`. The deployment example validates a deployment, authorizes it, and only then starts deployment. A failure at an earlier stage prevents later stages from executing normally.

The Python implementation uses `await` to express sequential asynchronous dependencies while explicitly catching failure conditions.

## Error Propagation

A rejected Promise represents an unsuccessful asynchronous operation.

For a chain such as:

    load configuration
           │
           ▼
    authorize deployment
           │
           ▼
    start deployment

a failure in an earlier operation can prevent dependent operations from receiving a valid value.

Error handling can be attached at the point where the failure occurs or at a later point in the chain.

This distinction is important:

- A handled rejection can become a successful recovery value.
- An unhandled rejection remains a failure.
- Throwing from a fulfillment handler creates a rejection for the next stage.
- Throwing from a rejection handler also creates a rejection unless the handler returns normally.
- A combinator may propagate one rejection, preserve all outcomes, or ignore rejections depending on its semantics.

The JavaScript implementation explicitly demonstrates rejection handlers and exceptions thrown inside chains. The Java `CompletableFuture` implementation unwraps `CompletionException` to expose the underlying domain failure.

## `Promise.all`

`Promise.all` is an all-or-nothing coordination mechanism.

Given:

    A ───── fulfilled
    B ───── fulfilled
    C ───── fulfilled

the aggregate fulfills after all inputs fulfill.

If one input rejects:

    A ───── fulfilled
    B ───── rejected
    C ───── pending

the aggregate rejects rather than producing a complete result collection.

This is appropriate when every operation is required for the overall operation to be considered successful.

Examples include:

- loading all mandatory application configuration;
- waiting for multiple required service checks;
- executing independent required data retrieval operations;
- completing all required initialization tasks.

`Promise.all` does not mean that the underlying operations are magically cancelled when the aggregate rejects. Other operations may continue executing unless the application separately implements cancellation or abort behavior.

The JavaScript implementation demonstrates this distinction by using service Promises with different completion times. The C++ and SQL implementations model all-operation evaluation explicitly.

## `Promise.race`

`Promise.race` settles according to the first input Promise that settles.

The first settlement may be either fulfillment or rejection.

    Primary       ──────────────── fulfilled
    Replica       ───── fulfilled
    Fallback      ──────────── pending

                   │
                   ▼
               Replica wins

If the first completed operation rejects, the race rejects even if another operation would have fulfilled later.

This makes `race` fundamentally different from `any`.

Typical uses include:

- timeout enforcement;
- selecting the first available response;
- racing a primary service against a fallback;
- implementing latency-sensitive selection.

A timeout pattern commonly combines the real operation with a timer Promise:

    real operation ──────────────── result
    timer          ───── timeout

                   │
                   ▼
                 race

The JavaScript implementation includes an explicit timeout wrapper and clears its timer after completion to avoid retaining unnecessary timer activity.

## `Promise.allSettled`

`Promise.allSettled` waits for every input operation and reports the individual outcome of each operation.

Its conceptual result contains records equivalent to:

| Operation | State | Result |
|---|---|---|
| metrics | fulfilled | successful value |
| audit | rejected | error |
| cache | fulfilled | successful value |

Unlike `Promise.all`, a single rejection does not reject the aggregate.

This makes `allSettled` suitable when the application needs a complete operational report regardless of individual failures.

Examples include:

- batch maintenance;
- independent telemetry operations;
- bulk notification attempts;
- cleanup tasks;
- diagnostic health checks.

The JavaScript implementation uses native `Promise.allSettled()`. The C++ implementation creates explicit `ServiceResult` records so successful and failed operations can coexist in one result collection. The SQL model persists both states and reports them separately.

## `Promise.any`

`Promise.any` is success-oriented.

It fulfills when the first input Promise fulfills. Rejections are ignored while other candidates remain available.

    Region A ───── rejected
    Region B ───── fulfilled
    Region C ───── rejected

                   │
                   ▼
               Region B wins

If every input rejects, `Promise.any` rejects with an `AggregateError` containing the individual errors.

This behavior is useful for redundant services where any successful provider is sufficient.

Typical scenarios include:

- replicated service endpoints;
- multiple geographic regions;
- redundant cache providers;
- multiple independent discovery mechanisms.

The distinction from `Promise.race` is critical:

| Behavior | `race` | `any` |
|---|---|---|
| First fulfillment | Settles | Settles |
| First rejection | Settles with rejection | Does not settle aggregate |
| Later fulfillment after early rejection | Too late | Can still win |
| All rejected | First rejection wins | Aggregate rejection |

The JavaScript implementation uses native `Promise.any()`. The C++ implementation maintains a successful winner while counting completed failures. The Java implementation builds a `firstSuccessful()` service because `CompletableFuture.anyOf()` has race-like rather than exact `Promise.any` semantics.

## Python Implementation

The Python script uses `asyncio` to model asynchronous Promise-like behavior.

`asyncio.create_task()` starts concurrent operations. `asyncio.gather()` provides behavior similar to aggregation with configurable exception handling. `asyncio.wait()` is used where first-completion behavior must be observed explicitly.

The script also contains a small `PromiseLike` class.

That class demonstrates the underlying state machine:

- `pending` accepts settlement;
- `fulfilled` stores a value;
- `rejected` stores an exception;
- handlers are invoked after settlement;
- a second settlement raises `PromiseStateError`.

The asynchronous examples cover:

- basic resolution;
- sequential chaining;
- exception propagation;
- all-success aggregation;
- fail-fast aggregation;
- first-completion behavior;
- all-settled collection;
- first-successful behavior;
- cancellation of remaining tasks after a winner is selected.

The Python implementation intentionally does not claim that `asyncio` is identical to JavaScript Promises. Its purpose is to model equivalent asynchronous coordination patterns while respecting Python's task and exception semantics.

## JavaScript Implementation

The JavaScript file is the primary native implementation because Promises are part of the language platform.

It demonstrates:

- Promise construction;
- fulfillment;
- rejection;
- `.then()` chaining;
- rejection handlers;
- `Promise.all()`;
- `Promise.race()`;
- `Promise.allSettled()`;
- `Promise.any()`;
- `AggregateError`;
- timeout handling;
- microtask ordering.

The microtask example is important because Promise callbacks do not execute synchronously merely because the Promise is already fulfilled.

A simplified event ordering is:

    synchronous-start
    synchronous-end
    promise-microtask
    timer-task

This explains why Promise handlers can execute after the current synchronous JavaScript execution context has completed but before a later timer callback.

The timeout implementation also demonstrates an important production concern: `Promise.race()` selects the observable winner but does not automatically cancel the losing operation.

## C++17 Implementation

C++ does not provide JavaScript-compatible native Promises in the standard library. The C++ program therefore implements a focused Promise abstraction around threads, mutexes, condition variables, and explicit state.

The `Promise<T>` class supports:

- pending state;
- fulfillment;
- rejection;
- settlement handlers;
- blocking retrieval;
- one-time settlement enforcement.

The program then constructs service operations with different completion times.

The aggregation functions represent the major Promise combinator semantics:

| Function | Purpose |
|---|---|
| `allSettled` | Preserve every successful and failed result |
| `race` | Select the first completed result |
| `any` | Select the first successful result |

The implementation uses `std::condition_variable` to avoid busy waiting. Worker threads notify waiting code when operations complete.

The main trade-off is resource management. Detached threads would be unsafe for an application that requires strict lifetime control, so the aggregation functions use joinable worker threads and wait for their completion.

The example is intentionally explicit about concurrency because C++ requires the programmer to manage synchronization and object lifetime directly.

## Java 17 Implementation

The Java implementation uses `CompletableFuture`, which provides a standard library abstraction for asynchronous computation and composition.

The domain model represents deployment operations rather than generic Promise examples.

`Deployment` is an immutable record with constructor validation. Deployment validation, authorization, and execution form an asynchronous workflow:

    Deployment
        │
        ▼
    Validation
        │
        ▼
    Authorization
        │
        ▼
    Deployment

`thenCompose()` expresses dependent asynchronous operations.

The program also implements:

- `CompletableFuture.allOf()` for required operations;
- `CompletableFuture.anyOf()` for race-like behavior;
- explicit all-settled result conversion;
- a custom first-successful operation for `Promise.any` semantics;
- exception unwrapping;
- executor lifecycle management.

The distinction between `anyOf()` and JavaScript `Promise.any()` is particularly important. `CompletableFuture.anyOf()` completes when the first future completes, including exceptional completion. Therefore, the Java implementation does not incorrectly use `anyOf()` as a direct replacement for `Promise.any()`.

## PostgreSQL Implementation

The SQL script models asynchronous operations as persistent state.

The central table stores:

- workflow;
- operation name;
- current Promise state;
- start time;
- settlement time;
- result;
- rejection message;
- latency.

PostgreSQL constraints enforce the consistency relationship between state and stored data.

For example, a fulfilled operation must have:

- `state = 'fulfilled'`;
- a result;
- no rejection message;
- a settlement timestamp.

A rejected operation must instead contain a rejection message and no successful result.

The `prevent_invalid_promise_transition()` trigger prevents a settled operation from changing its state or settlement information.

The settlement functions provide controlled database operations:

- `settle_fulfilled()`;
- `settle_rejected()`.

Both functions update only pending operations.

This gives the relational model the same one-way settlement property as a Promise.

## Transactional Workflow

The SQL examples use transactions when settling related operations.

A chained workflow demonstrates:

    configuration
          │
          ▼
    authorization
          │
          ▼
    deployment

Each operation is persisted independently, while transaction boundaries ensure that a group of related changes is committed atomically.

The database also records state transitions in `operation_events`, creating an audit trail.

This makes it possible to distinguish current state from historical state.

## Failure and Edge Conditions

The implementations deliberately cover several failure conditions.

| Condition | Relevant behavior |
|---|---|
| Second settlement | Rejected by explicit state protection |
| Chain operation throws | Downstream chain becomes rejected |
| `Promise.all` member rejects | Aggregate rejects |
| `Promise.race` first result rejects | Aggregate rejects |
| `Promise.allSettled` member rejects | Failure is retained as data |
| `Promise.any` member rejects | Other candidates continue |
| `Promise.any` all reject | Aggregate failure |
| Timeout wins a race | Operation may still be running |
| Invalid production deployment | Java domain validation rejects workflow |
| Database state inconsistency | PostgreSQL constraints reject invalid data |

One particularly important distinction is between **aggregate settlement** and **underlying operation cancellation**. Promise combinators determine the state of the aggregate Promise. They do not automatically terminate arbitrary external work.

For example, if three requests participate in `Promise.race()` and the second request wins, the first and third requests may still consume network, CPU, or database resources.

Production systems should therefore pair Promise coordination with appropriate cancellation mechanisms where the underlying operation supports them.

## Performance Considerations

Promise combinators primarily coordinate existing asynchronous operations. Their performance depends heavily on the operations being coordinated.

`Promise.all` and `Promise.allSettled` must retain references to their input operations and their resulting values or outcomes.

`Promise.any` must track failures until either one operation fulfills or every operation rejects.

`Promise.race` can settle as soon as the first input settles, but the losing operations may continue running.

The C++ implementation creates worker threads for its simulation. Thread creation is substantially heavier than JavaScript microtasks, so a production C++ implementation would normally use a managed thread pool or asynchronous I/O model rather than creating a thread for every small operation.

The Java implementation uses a bounded `ExecutorService` rather than creating unrestricted threads.

The PostgreSQL indexes target workflow-state lookup and operation-event retrieval. They are useful for reporting queries that repeatedly filter by workflow, state, operation, and event time.

## Security and Reliability Considerations

Promise state does not itself provide security. The surrounding application must validate inputs and enforce authorization independently.

The Java deployment example therefore separates validation from authorization and execution.

Asynchronous failures should not be silently discarded. Unhandled rejections, lost exceptions, and incomplete error reporting can make distributed failures difficult to diagnose.

Sensitive data should not be inserted into Promise rejection messages, logs, or persistent operation records without appropriate controls. Error messages should expose enough information for diagnosis without unnecessarily disclosing credentials, tokens, personal information, or internal security details.

Timeouts should be accompanied by cancellation where possible. Otherwise, a timeout can merely stop waiting while the underlying operation continues.

## Relationship Between the Combinators

The four major combinators solve different coordination problems:

    Multiple asynchronous operations
                   │
        ┌──────────┼──────────────┐
        │          │              │
        ▼          ▼              ▼
      all()      race()      allSettled()
        │          │              │
   every must   first must    every outcome
     succeed      settle       is retained
        │
        └──────────────┐
                       ▼
                     any()
                       │
                first success wins

The choice should be driven by the required business semantics rather than by the superficial similarity of the APIs.

Use `all` when every result is required.

Use `race` when the earliest settlement determines the outcome.

Use `allSettled` when every outcome must be inspected.

Use `any` when the first successful alternative is sufficient.

These distinctions are the central design principle represented across the five implementations.
