# Event Loop Deep Dive

## Scope

This project models the execution mechanics behind an event-driven runtime:

- call stack execution
- task queue processing
- microtask checkpoints
- rendering opportunities
- delayed work
- callback ordering
- nested scheduling
- starvation and failure protection

The five implementations use the same conceptual model while deliberately emphasizing different engineering perspectives.

The central execution relationship is:

`Synchronous code → Call stack → Microtask checkpoint → Task → Microtask checkpoint → Rendering opportunity`

The model is intentionally simplified. Real browser runtimes contain additional scheduling policies, rendering constraints, networking layers, worker contexts, garbage collection, and host-specific behavior. The implementations isolate the core ordering rules so that the mechanisms can be inspected and tested directly.

## Core Concepts

### Call Stack

The call stack represents currently executing synchronous JavaScript functions.

A function call adds a frame. Returning from the function removes that frame. Nested synchronous calls therefore increase stack depth without creating a separate task.

For example:

`event handler → function A → function B`

is one continuous synchronous execution path.

A queued callback does not execute immediately merely because it was scheduled. It waits until the current stack has completed and the runtime reaches an appropriate scheduling point.

The Python, C++17, and Java 17 implementations explicitly model stack entry and exit. The JavaScript implementation records the same state in an array.

### Task Queue

Tasks represent independently scheduled units of host work such as:

- timer callbacks
- user-event callbacks
- network-related callbacks
- other host-provided event sources

A task is not the same thing as a function call. The callback eventually executes on the call stack, but the task determines when the runtime can begin that callback.

The implementations attach a scheduled timestamp and sequence number to tasks. This permits deterministic ordering without depending on an operating system scheduler.

A simplified task-selection rule is:

`ready tasks → earliest scheduled time → earliest insertion sequence`

Actual browser scheduling can involve additional priorities and rendering considerations.

### Microtask Queue

Microtasks are processed at a microtask checkpoint.

Typical JavaScript examples include Promise reactions and callbacks scheduled through `queueMicrotask()`.

The important distinction is that microtasks are not simply another task queue with equal scheduling priority. Once a microtask checkpoint begins, queued microtasks are normally drained before the runtime proceeds to another task.

Microtasks can enqueue more microtasks:

`microtask A → microtask B → microtask C`

This creates a potential starvation condition if application code continuously adds new microtasks.

Each implementation therefore includes a configurable safety limit for its simulation.

### Rendering Cycle

Rendering is modeled as a separate opportunity rather than as an ordinary task.

The simulation uses a 16 ms frame interval, corresponding to a simplified 60 Hz frame cadence.

The conceptual relationship is:

`JavaScript execution → microtask checkpoint → rendering opportunity`

A long synchronous task can delay a rendering opportunity. A large microtask chain can also delay rendering because the checkpoint must finish before the event loop can proceed.

Real browsers use substantially more detailed rendering pipelines, so the simulation should not be interpreted as an exact browser implementation.

## Execution Model

A simplified event-loop iteration used by the implementations is:

`1. Execute synchronous work`
`2. Reach a microtask checkpoint`
`3. Drain microtasks`
`4. Select a ready task`
`5. Execute the task on the call stack`
`6. Drain microtasks created by that task`
`7. Consider a rendering opportunity`
`8. Continue with the next event-loop iteration`

The important property is that task execution and microtask execution have different scheduling semantics.

A Promise reaction created during a task can execute before another ready task.

A timer callback cannot interrupt currently executing synchronous JavaScript.

## Repository-Like Domain Relationship

The implementation domain is intentionally structured as:

`Event Loop`
`├── Call Stack`
`│   └── Execution Contexts`
`├── Task Queue`
`│   ├── Timer Tasks`
`│   ├── Network Tasks`
`│   └── User Event Tasks`
`├── Microtask Queue`
`│   └── Promise / Microtask Reactions`
`└── Rendering Opportunities`
`    └── Frame Callbacks`

These are distinct mechanisms.

The call stack describes what is executing now.

The task queue describes host work waiting for execution.

The microtask queue describes checkpoint work that receives special draining semantics.

The rendering cycle describes opportunities to update the visual output.

## Python Implementation

The Python file implements a deterministic `EventLoop` class.

### Main Structures

`Task` is a dataclass containing:

- callback name
- callback function
- task type
- scheduled timestamp
- sequence number

`TaskType` distinguishes timers, I/O, user events, and rendering.

The event loop maintains:

- a list representing the call stack
- a deque for tasks
- a deque for microtasks
- a deque for rendering callbacks
- a textual execution trace

### Scheduling

`queue_task()` records delayed or immediately eligible work.

`queue_microtask()` inserts checkpoint work.

`request_render()` schedules rendering work independently from ordinary tasks.

The implementation uses sequence numbers to make same-time scheduling deterministic.

### Error Handling

Negative task delays are rejected.

Invalid event-loop limits are rejected.

The simulator raises an exception when a microtask checkpoint exceeds its configured maximum.

This protects the simulation from an infinite recursive microtask chain.

### Testing

The Python implementation includes an assertion that establishes this ordering:

`sync → microtask → task`

It also explicitly exercises recursive microtask scheduling to demonstrate starvation protection.

## JavaScript Implementation

The JavaScript implementation models the same execution semantics using JavaScript-specific structures.

### State Representation

The `EventLoop` class stores:

- stack frames in an array
- microtasks in an array
- tasks in an array
- render callbacks in an array
- an execution sequence counter
- simulated time

The implementation does not depend on browser APIs or Node.js-specific modules, making the scheduling model portable across JavaScript runtimes.

### Event-Driven Design

Callbacks are represented as functions and executed only by the scheduler.

The scheduler therefore separates:

`callback definition`

from:

`callback execution`

This is useful when reasoning about asynchronous JavaScript because registering a callback does not mean the callback immediately executes.

### Promise-Like Ordering

The `queueMicrotask()` mechanism models the important scheduling property of Promise reactions: checkpoint work runs before the scheduler selects another ordinary task.

The implementation also permits microtasks to enqueue additional microtasks, exposing the possibility of starvation.

### Validation

The JavaScript implementation rejects:

- invalid callback values
- negative delays
- invalid execution-loop limits

It uses a dedicated `EventLoopError` class for scheduling failures.

## C++17 Implementation

The C++17 program treats the event loop as a systems-oriented scheduling engine.

### Data Structures

The implementation uses:

- `std::vector` for stack frames and task storage
- `std::deque` for FIFO microtasks and rendering callbacks
- `std::function` for executable callbacks
- strongly typed enums for task categories
- sequence numbers for deterministic ordering

The design avoids external dependencies.

### Task Selection

Ready tasks are selected using STL algorithms.

The comparator orders candidates by:

1. scheduled time
2. insertion sequence

This produces deterministic behavior while preserving a clear separation between scheduling policy and callback execution.

### Exception Safety

Synchronous callback execution is wrapped so that stack state is restored when a callback throws.

The scheduler also has explicit limits for:

- microtasks per checkpoint
- total event-loop turns

These limits prevent a faulty simulation from becoming unbounded.

### Engineering Perspective

The C++ version emphasizes explicit ownership of scheduler state and predictable resource boundaries.

Its primary trade-off is that a linear scan is used to locate the next ready task. For a teaching-scale simulation this is straightforward and transparent. A production scheduler handling very large numbers of delayed timers could use a priority queue or timer wheel.

## Java 17 Implementation

The Java implementation models the runtime using explicit domain types and immutable task metadata.

### Domain Modeling

`Task` is represented as a Java record.

`TaskType` is an enum.

`EventLoopException` represents scheduler-specific failures.

The `EventLoop` class owns queue state and execution policy.

This separates domain data from scheduling behavior.

### Collections

The implementation uses:

- `ArrayDeque` for stack and FIFO queues
- `ArrayList` for delayed task storage
- streams and comparators for selecting the next ready task
- immutable `List.copyOf()` for returning the execution trace

### State Transitions

A task moves conceptually through:

`queued → running → completed`

The simulator also has a failure path when scheduling limits are violated.

Stack execution is represented explicitly so nested function execution remains distinguishable from independently queued work.

### Policy Modeling

The Java file includes an `ExecutionPolicy` record implementing a small policy interface. This illustrates how scheduling decisions can be separated from the scheduler itself.

The policy distinction is useful for larger enterprise systems where execution rules may differ by environment or execution context.

## PostgreSQL Implementation

The PostgreSQL script models event-loop state as relational data.

### Main Tables

`event_loop` stores runtime-level configuration and simulated time.

`execution_context` stores stack contexts and parent-child relationships.

`queue_item` stores tasks, microtasks, and rendering work.

`stack_event` records stack transitions.

`microtask_checkpoint` records checkpoint execution.

`rendering_opportunity` records frame boundaries.

This produces a relational representation of:

`runtime → execution context → queued work → checkpoints → rendering`

### Constraints

The database enforces important invariants with:

- primary keys
- foreign keys
- unique constraints
- check constraints
- enum types
- trigger validation

For example, a microtask cannot be represented as a delayed timer task because its scheduled time must equal its creation time in this simplified model.

Render queue entries must use the `render` source.

A running queue item must have a start timestamp.

Failed queue items must contain an error message.

### Indexes

The queue indexes focus on the access patterns needed to locate ready work:

`loop_id + scheduled_at_ms + sequence_no`

Partial indexes restrict those structures to queued task or microtask records.

This avoids indexing completed work that does not participate in ready-queue selection.

### Functions

`enqueue_microtask()` creates a microtask while obtaining the current event-loop clock under a row lock.

`advance_loop_clock()` prevents time from moving backward.

These functions demonstrate that important scheduler invariants can be enforced at the database boundary rather than being left entirely to application code.

### Transactional Task Claiming

The transaction using `FOR UPDATE SKIP LOCKED` demonstrates safe claiming of ready tasks.

The pattern is relevant to systems where multiple workers might inspect the same logical queue.

The transaction prevents two workers from simultaneously claiming the same queue record.

## Microtask Starvation

Microtask starvation occurs when microtasks continually enqueue more microtasks.

A simplified sequence is:

`microtask A`
`  ↓`
`queues B`
`  ↓`
`microtask B`
`  ↓`
`queues C`
`  ↓`
`microtask C`
`  ↓`
`...`

If the checkpoint never becomes empty, ordinary tasks and rendering opportunities can be delayed indefinitely.

The implementations deliberately detect this condition with a configurable checkpoint limit.

This is a simulation safety mechanism rather than a claim that browsers impose the same numeric limit.

## Long Synchronous Tasks

A synchronous callback cannot normally be interrupted by another JavaScript callback simply because that callback has become ready.

Therefore:

`long synchronous function`
`        ↓`
`blocks`
`        ↓`
`task processing`
`        ↓`
`microtask checkpoint`
`        ↓`
`rendering opportunity`

This explains why CPU-heavy JavaScript can make an interface appear unresponsive.

The event loop is concurrent with respect to scheduling of independent work, but JavaScript execution on a single main thread is not automatically parallel.

## Concurrency Model

The central distinction is:

`Concurrency ≠ parallel execution`

An event loop can coordinate many waiting operations without executing all of their JavaScript callbacks simultaneously.

For example:

`Network request A ───────┐`
`Network request B ────┐  │`
`Timer ──────────────┐ │  │`
`                    ↓ ↓  ↓`
`                 Event Loop`
`                    ↓`
`              Call Stack`

The host can make progress on external operations while JavaScript callbacks wait for execution.

When a callback becomes eligible, the event loop schedules it for execution.

Actual parallelism can be introduced through separate workers or threads, but that is a different execution mechanism from the main event loop.

## Failure Modes

| Failure | Mechanism | Effect |
|---|---|---|
| Long synchronous task | Call stack remains occupied | Tasks and rendering are delayed |
| Infinite recursion | Stack keeps growing | Stack overflow |
| Endless microtasks | Checkpoint never drains | Task and rendering starvation |
| Excessive task count | Scheduler repeatedly processes work | High event-loop latency |
| Invalid scheduling state | Inconsistent queue metadata | Incorrect ordering |
| Clock regression | Time moves backward | Invalid timer semantics |
| Concurrent queue claim | Multiple consumers select one task | Duplicate execution risk |

The implementations explicitly handle several of these cases so that failure behavior is visible rather than hidden.

## Performance Considerations

The simulations prioritize clarity and deterministic behavior.

The task queues in the Python and C++ implementations can require linear scanning to find the next ready task. The Java implementation similarly searches the task collection using a comparator.

For a small learning model, this keeps the scheduling algorithm easy to inspect.

A production scheduler with large numbers of timers could use:

- priority queues
- timer wheels
- indexed heaps
- event-source-specific queues
- priority scheduling
- deadline-aware scheduling

Microtask queues generally need efficient FIFO behavior because checkpoint draining is frequent.

Rendering work also benefits from explicit frame/deadline handling rather than treating rendering as an ordinary delayed callback.

## Security Considerations

Event-loop security is primarily about controlling untrusted or excessive work.

Relevant risks include:

- denial of service through endless microtask creation
- CPU exhaustion through long synchronous callbacks
- excessive callback registration
- memory growth from unbounded queues
- unsafe execution of untrusted callbacks
- incorrect isolation between independent execution contexts

The implementations do not execute arbitrary external code or access external systems. Callback functions are registered locally and executed under explicit scheduler control.

The PostgreSQL model reinforces queue integrity through constraints and triggers rather than trusting every application-level write.

## Important Distinctions

| Mechanism | Primary role | Can execute immediately? | Scheduling characteristic |
|---|---|---:|---|
| Call stack | Current synchronous execution | Yes | LIFO function frames |
| Task queue | Host-scheduled work | No | Selected after current execution and checkpoint |
| Microtask queue | Checkpoint work | No | Drained at microtask checkpoints |
| Rendering opportunity | Visual update opportunity | No | Associated with frame timing |

These mechanisms interact but should not be treated as interchangeable queues.

A timer callback is a task.

A Promise reaction is typically a microtask.

A function called directly by another function uses the existing call stack.

A browser rendering opportunity is part of the host's rendering pipeline rather than an ordinary JavaScript function call.

## Practical Trace

A simplified trace from the implementations can be represented as:

`application-start`
`    ↓`
`stack-enter`
`    ↓`
`queue Promise reaction`
`queue timer`
`request render`
`    ↓`
`stack-exit`
`    ↓`
`microtask checkpoint`
`    ↓`
`Promise reaction`
`    ↓`
`timer task`
`    ↓`
`microtask checkpoint`
`    ↓`
`network task when ready`
`    ↓`
`microtasks created by network task`
`    ↓`
`rendering opportunity`

The exact order of unrelated host events can vary in real environments. The implementations intentionally use simulated timestamps and sequence numbers where deterministic ordering is required.

## Design Limitations

These artifacts model the conceptual event-loop mechanisms rather than implementing a browser.

They do not attempt to reproduce:

- browser-specific task-source prioritization
- networking internals
- compositor threads
- GPU scheduling
- layout and paint internals
- garbage collector scheduling
- Web Worker execution
- operating-system event notification APIs
- browser-specific timer clamping
- every rendering optimization
- every ECMAScript host integration detail

The purpose of the model is to make execution ordering, queue separation, state transitions, starvation, and scheduling boundaries explicit.

## Cross-Language Comparison

| Implementation | Primary emphasis | Core structures |
|---|---|---|
| Python | Deterministic simulation | dataclasses, deques, enums, callbacks |
| JavaScript | Event-driven callback model | classes, arrays, functions, custom errors |
| C++17 | Systems-oriented scheduler | STL containers, `std::function`, algorithms |
| Java 17 | Explicit enterprise domain model | records, enums, interfaces, collections |
| PostgreSQL | Persistent relational state | constraints, indexes, functions, triggers, transactions |

The implementations share the same conceptual domain but do not mechanically translate one another.

Python emphasizes rapid modeling and assertions.

JavaScript emphasizes callback-oriented event behavior.

C++17 emphasizes explicit scheduler state and resource control.

Java 17 emphasizes domain types and policy boundaries.

PostgreSQL emphasizes durable state, relational integrity, and transactional queue operations.
