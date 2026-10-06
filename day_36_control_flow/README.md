# Control Flow: Branching, Iteration, Early Exit, and Decision Logic

## Scope

Control flow determines the order in which a program evaluates conditions, repeats work, skips work, exits loops, handles failures, and transitions between states.

This repository uses six complementary artifacts to study control flow through executable examples:

- `control_flow.py` models branching, iteration, validation pipelines, state transitions, rule evaluation, file processing, retry behavior, and early termination in Python.
- `control_flow.js` models the same broad domain from a JavaScript perspective, with switch dispatch, event processing, classes, asynchronous retry control, and explicit workflow transitions.
- `control_flow.cpp` presents a release-validation engine in which jobs move through controlled states and deployment eligibility depends on the results.
- `ControlFlowEnterpriseDemo.java` models an enterprise release service with explicit stage states, policies, validation, exceptions, generic search, and bounded processing.
- `control_flow.sql` represents control-flow decisions relationally through workflow stages, execution results, constraints, transactions, CASE expressions, CTEs, decision rules, and database-enforced state transitions.

The implementations deliberately distinguish simple branching from iteration, iteration control from state transitions, and application-level decisions from database-level integrity rules.

## Core control-flow model

A sequential program normally evaluates statements in order. Control-flow constructs change that sequence.

Conditional control flow chooses among alternatives. A condition is evaluated and the corresponding branch executes.

Iteration evaluates a body repeatedly. The number of iterations may be known before execution, as with a bounded `for` loop, or may depend on a changing condition, as with a `while` loop.

Loop-control statements modify iteration itself. `continue` skips the remainder of the current iteration. `break` terminates the nearest enclosing loop. A `return` leaves the current function entirely.

Exception handling is another form of non-linear execution. When an operation raises an exception, normal execution transfers to a matching handler instead of continuing at the statement immediately following the failure.

State machines combine these mechanisms. A state identifies the current condition of a process, while a transition defines which events can move that process into another state.

## Conditional branching

### Python

The Python implementation uses `if`, `elif`, and `else` to classify scores, authorize users, validate inputs, and apply ordered business rules.

The ordering of conditions matters. In `evaluate_rules()`, a high fraud score is evaluated before customer-specific pricing. This means a risky transaction is blocked before a customer discount can be considered.

Python also demonstrates structural pattern matching through `match`. The command classifier maps exact command values such as `start`, `stop`, and `pause` to different outcomes. The wildcard pattern handles unsupported commands.

A dictionary is used in `menu_command()` as a data-driven alternative to a long conditional chain. This is useful when the decision is a direct mapping rather than a sequence of predicates.

### JavaScript

JavaScript uses `if` and `else if` for numeric classification and authorization. Its `switch` implementation handles command values and role selection.

The JavaScript examples demonstrate an important distinction between conditional logic and dispatch. A condition such as `riskScore >= 0.9` represents a rule. A switch over a known command represents selection among discrete command values.

### C++

The C++ case study uses conditions for validation and policy decisions while using `switch` for strongly defined enumerations such as `Command` and `JobState`.

Using an enum with `switch` makes state-dependent behavior explicit. Each known state receives a controlled branch rather than relying on arbitrary strings.

### Java

Java's `switch` expressions return values directly when parsing commands and describing operations. This makes the relationship between an input value and its result explicit.

The enterprise model also uses ordinary conditional checks for validation rules, such as rejecting negative amounts or invalid risk scores.

## Iteration

Iteration is useful when the same operation must be applied to a collection, range, stream of events, validation stages, or bounded sequence.

### `for` loops

The Python implementation uses `for` loops for iterable processing, record validation, inventory searches, log processing, and retry attempts.

The JavaScript implementation uses `for...of` for arrays and other iterable collections. This avoids manual index management when an index is not part of the business rule.

C++ uses range-based `for` loops for collections of jobs and state summaries. It also uses an indexed loop when the position of the first failing check is significant.

Java uses enhanced `for` loops for validation stages and generic searches.

### `while` loops

A `while` loop is appropriate when the termination condition depends on state that changes during execution.

The Python Fibonacci and countdown examples demonstrate this directly. The loop condition is tested before each iteration, so an initially false condition causes zero iterations.

A common failure is forgetting to update the variable controlling the condition. That can produce an infinite loop.

## `break`

`break` exits the nearest enclosing loop immediately.

The Python file uses `break` when a threshold is reached and when a log-processing limit prevents unbounded input consumption.

The JavaScript implementation returns immediately when a desired value is found. Although `return` is stronger than `break`, the example demonstrates the same early-termination principle at function level.

The C++ release case study stops processing when the failure count makes continued execution unable to satisfy the release policy.

The Java release service stops executing expensive later stages after the policy becomes unsatisfiable.

The SQL implementation expresses an analogous idea through queries that locate the first failing stage. SQL does not execute procedural `break` semantics in an ordinary SELECT statement, so the database representation uses aggregation and ordering to identify the earliest failure instead.

## `continue`

`continue` skips the remaining body of the current iteration.

This is valuable when invalid or irrelevant records should not terminate an entire operation.

The Python validation pipeline uses `continue` after identifying malformed records. The next record is then processed independently.

The JavaScript event processor ignores heartbeat events without executing business-processing logic for them.

The C++ example skips odd values while retaining the loop itself, then uses `break` when a later boundary is reached.

Java filtering similarly ignores null and non-positive values before adding valid values to the result.

A common mistake is using `continue` when the invalid condition should actually terminate the entire operation. The correct choice depends on whether the failure is local to one item or invalidates the entire process.

## Nested conditions

Nested conditions are appropriate when one decision is logically dependent on another.

The Python authorization example first determines whether the user is an adult and only then checks permission. This prevents a permission decision from being evaluated independently of the age constraint.

Deep nesting can make control flow difficult to inspect. Early returns, guard clauses, extracted functions, and explicit state models can reduce unnecessary nesting when the business rules permit them.

## State machines

A state machine represents a process as a set of states and permitted transitions.

The Python deployment object begins in `PENDING`. Validation moves it into `VALIDATING`. Missing artifacts or failed tests move it to `FAILED`; satisfying both prerequisites moves it to `DEPLOYED`.

The JavaScript `Workflow` class represents `pending`, `validating`, `approved`, `failed`, and `completed` states. Its `transition()` method rejects transitions that are not legal for the current state.

The C++ release engine uses `JobState` to distinguish pending, running, passed, failed, and skipped jobs. A job cannot be considered passed unless the state transition has actually executed its validation logic.

The Java implementation separates `ValidationStage` from `StageExecution`. The immutable record describes the configured stage, while the execution object owns mutable runtime state. This separation prevents configuration and execution state from being confused.

The SQL database represents states with a PostgreSQL enum. A trigger then prevents terminal results such as `passed` or `failed` from being changed into unrelated states.

State machines are particularly useful when a process has explicit lifecycle rules. A simple `if` statement may be sufficient for a one-time decision, but explicit states become clearer when a process can transition repeatedly or when invalid transitions must be rejected.

## Validation and failure handling

Validation is control flow because invalid input changes the path through a program.

The Python record validator distinguishes accepted records from rejected records. A malformed record does not prevent later valid records from being processed.

The JavaScript validation pipeline performs the same type of per-record decision while using JavaScript's runtime type checks.

C++ throws exceptions for invalid numeric parameters while returning a structured evaluation result for expected validation outcomes.

Java uses `IllegalArgumentException` for invalid configuration and input values, while domain execution errors are represented as `IllegalStateException`.

The SQL model uses constraints to prevent invalid database states. This is important because application-level validation alone cannot guarantee that every database client follows the same rules.

## Ordered business rules

Business rules frequently depend on precedence.

The Python rule engine checks risk before customer category. The JavaScript discount function follows the same conceptual ordering but exposes its result as an object containing both status and discount.

The C++ and Java implementations demonstrate that ordering can be embedded directly in domain methods rather than scattered across output statements.

The SQL implementation uses a decision table with priorities. A lateral query selects the highest-priority rule that matches the request.

This distinction is important:

- Conditional code evaluates rules procedurally.
- A decision table represents rules as data.
- A database query can select the applicable rule using predicates and ordering.

The appropriate approach depends on how frequently rules change, who maintains them, and whether the rules must be shared by multiple applications.

## Practical control-flow patterns

### Guard clauses

A guard clause rejects an invalid situation early.

For example, checking that an amount is non-negative before applying pricing rules prevents later branches from having to account for negative amounts.

Guard clauses reduce nesting because invalid cases leave the function immediately.

### Early success or failure

Returning immediately after finding the requested item avoids unnecessary iteration.

The Python `first_even()` function returns as soon as a valid even value is found.

The C++ `findFirstFailure()` identifies the first failing index rather than continuing to inspect values after the required answer is known.

The same principle appears in Java's generic `findFirst()` method.

### Bounded work

Control flow should account for potentially unbounded input.

The Python log processor accepts a maximum number of lines and uses `break` once the limit is reached.

This is both a performance and reliability measure. A service should not accidentally process an unexpectedly large file merely because a loop has no operational boundary.

### Skip versus stop

`continue` is appropriate when one item is irrelevant but the overall operation remains valid.

`break` is appropriate when continuing the current loop is no longer useful.

`return` is appropriate when the complete function has enough information to produce its result or when the function cannot continue meaningfully.

An exception is appropriate when the current operation cannot satisfy its contract through ordinary execution.

These mechanisms should not be treated as interchangeable.

## Asynchronous control flow

The JavaScript implementation demonstrates retry behavior using `async` and `await`.

The retry loop attempts an asynchronous operation multiple times. A rejected promise transfers control to the `catch` block. The loop continues when another attempt is permitted and stops when the attempt limit is reached.

This is different from synchronous looping because the operation may suspend execution while the promise settles.

Retry logic must have a bound. An unlimited retry loop can keep a failing system busy indefinitely and can amplify load against an already unhealthy dependency.

## SQL control flow

SQL is primarily declarative rather than an imperative statement-by-statement control-flow language.

The PostgreSQL script therefore uses SQL constructs that express decisions through data relationships:

- `CASE` expressions represent conditional outcomes.
- `WHERE` predicates determine which records participate.
- `FILTER` clauses isolate subsets during aggregation.
- `ORDER BY` with `LIMIT` selects the highest-priority applicable rule.
- CTEs organize intermediate decision data.
- Transactions control whether a sequence of database changes is committed or rolled back.
- Constraints and triggers enforce state rules at the database boundary.

The workflow tables represent execution state explicitly. A result can be `passed`, `failed`, or `skipped`, and queries classify those states into operational actions.

The trigger demonstrates a database-level invariant: a terminal state cannot be changed into another state. This prevents invalid state transitions even if an application sends an incorrect update.

## Control flow and performance

The complexity of a control-flow structure depends on both the number of operations and the way the branches and loops interact.

A single loop over `n` records is generally O(n).

A nested loop over two independent collections can become O(n × m).

An early `break` can reduce actual runtime substantially when the desired result occurs near the beginning, even though the worst-case complexity remains unchanged.

Filtering before expensive work can also improve performance. The examples use `continue` to discard invalid records before subsequent processing.

Repeated linear searches inside a loop can create accidental quadratic behavior. A set or dictionary can often replace repeated scans when membership checks are the dominant operation.

The C++ implementation uses maps for state counts and structured types for domain state. The Python inventory example uses a dictionary so SKU lookup is normally constant-time on average instead of scanning every product.

## Common mistakes

### Incorrect condition ordering

If a broad condition appears before a more specific condition, the specific branch may never execute.

For example, checking `amount > 0` before an `amount >= 10000` rule would make the higher-value branch unreachable unless the ordering is corrected.

### Accidental infinite loops

A `while` loop must make progress toward its terminating condition unless another deliberate exit mechanism exists.

A loop whose controlling variable never changes can execute indefinitely.

### Misusing `continue`

Skipping an invalid item is different from abandoning the entire operation. Using `continue` for a fatal condition can silently process data that should have caused the workflow to stop.

### Misusing `break`

`break` only exits the nearest enclosing loop. It does not automatically exit a surrounding function or outer loop.

When a function should stop completely, `return` may communicate intent more clearly.

### Fall-through in switch statements

Some languages permit implicit fall-through in `switch` statements.

C++ can intentionally use fall-through, as shown in the job state machine, but such behavior should be explicit and justified. Accidental fall-through is a common source of incorrect execution.

JavaScript `switch` cases also require explicit `break` when fall-through is not intended.

Java's modern switch expression syntax reduces this particular class of accidental fall-through because each arrow branch represents a separate result expression.

### Overly complex branching

Large nested conditional structures often indicate that several responsibilities have been combined.

The examples use separate functions, state objects, policies, enums, and decision tables where that separation improves clarity.

## Relationship between the implementations

The five executable implementations approach the same control-flow domain from different language models.

| Implementation | Distinct emphasis |
| --- | --- |
| Python | Direct executable demonstrations, validation pipelines, file processing, pattern matching, retry behavior, and practical scripting |
| JavaScript | Event processing, `switch` dispatch, object-oriented state transitions, and asynchronous retry control |
| C++ | Strongly typed state modeling, enum-based dispatch, release validation, early termination, and explicit failure results |
| Java | Enterprise domain modeling, immutable records, explicit policy objects, stateful services, generics, and typed switch expressions |
| PostgreSQL | Declarative decision logic, relational state, transactions, constraints, triggers, CTEs, aggregation, and data-driven rules |

The differences are deliberate. Control flow is a language-independent programming concept, but each language provides different abstractions for expressing it.

## Database integrity versus application control flow

Application code decides what should happen during a particular execution.

Database constraints decide what states are allowed to exist in persistent storage.

For example, an application may decide that a validation stage should become `passed`. The SQL trigger provides a second layer of protection by preventing an already terminal result from being changed to an incompatible state.

This separation is important in systems with multiple application clients. Database-level integrity protects the shared state even when different clients implement their own control flow.

## Practical applications

The control-flow techniques demonstrated here map directly to systems that:

- validate incoming records and skip malformed entries while continuing with valid data;
- process event streams and ignore event types that are irrelevant to a particular consumer;
- execute release validation stages and stop when a critical failure makes continuation unsafe;
- implement retry policies with explicit attempt limits;
- select pricing or authorization outcomes from ordered business rules;
- manage lifecycle states where only specific transitions are valid;
- enforce persistent state invariants at the database layer;
- process files with bounded work to avoid uncontrolled resource consumption.

The important design decision is not simply which syntax to use. It is identifying whether the business rule requires branching, repetition, skipping, early termination, state transition, exception handling, or a combination of these mechanisms.
