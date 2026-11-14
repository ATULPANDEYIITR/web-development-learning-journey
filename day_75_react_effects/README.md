# React Effects: useEffect, Dependency Arrays, Cleanup, and Side Effects

## 1. Technical Scope

React Effects provide a mechanism for synchronizing a component with external systems after React commits a render.

The `useEffect` Hook is commonly used for:

- Establishing subscriptions.
- Connecting to external services.
- Synchronizing browser APIs.
- Fetching external data.
- Managing timers.
- Registering and removing event listeners.
- Integrating third-party libraries.
- Synchronizing state with systems outside React.

An Effect is not a general-purpose replacement for event handlers, derived state, or ordinary rendering calculations.

The five implementations model different aspects of effect lifecycle management. They use standalone simulations to demonstrate the underlying engineering principles without requiring a React runtime in the non-JavaScript languages.

## 2. The useEffect Mechanism

The general React syntax is:

`useEffect(setup, dependencies)`

The first argument is a setup function. It executes after React commits the relevant render.

The optional second argument determines when React considers the Effect eligible to run again.

The setup function can return another function. This returned function is the cleanup function.

The lifecycle follows this sequence:

    Render
       |
       v
    Commit
       |
       v
    Execute Effect Setup
       |
       v
    External Resource Active
       |
       v
    Dependencies Change?
       |
       +---- No ----> Keep Existing Effect
       |
       +---- Yes ---> Execute Previous Cleanup
                         |
                         v
                      New Setup
                         |
                         v
                      Resource Updated

On unmount, React executes the final cleanup for each Effect.

### 2.1 Effects and rendering

React rendering calculates the user interface from the current props and state.

Effects perform synchronization after rendering has been committed.

This distinction matters because an Effect should not be used for values that can be calculated directly during rendering.

For example, if a component displays a total derived from two state variables, calculating the total in an Effect and storing it in another state variable introduces unnecessary state synchronization.

The derived value can normally be calculated directly.

## 3. Dependency Arrays

Dependency arrays determine whether an Effect needs to execute again after a committed render.

| Dependency configuration | Behavior |
|---|---|
| Dependencies omitted | Runs after every committed render |
| Empty array `[]` | Runs after initial mount |
| `[count]` | Runs when `count` changes |
| `[userId, status]` | Runs when either dependency changes |

An important distinction is that an Effect without dependencies is different from an Effect with an empty dependency array.

### 3.1 Dependency comparison

React compares each dependency with its previous value using `Object.is`.

This comparison has important consequences.

- Primitive values are compared according to their value.
- Objects are compared by reference identity.
- Arrays are compared by reference identity.
- Functions are compared by reference identity.
- `NaN` compares equal to itself under `Object.is`.
- Positive and negative zero are distinguished.

Consider an object dependency.

A newly created object has a different identity even if its properties are identical.

Consequently, an Effect depending on that object can execute again after every render that creates a new instance.

This can cause unnecessary external requests, repeated subscriptions, or excessive synchronization.

Dependency arrays should contain every reactive value referenced by the Effect setup and cleanup logic.

The dependency list must have a constant number of entries and should be written inline.

### 3.2 Missing dependencies

Omitting a reactive dependency can cause stale closures.

A stale closure occurs when an Effect continues to use values captured by an earlier render instead of the current values.

For example, a subscription callback may continue reading an old user identifier after the selected user changes.

The appropriate correction is to identify the reactive dependencies and synchronize the Effect with their changes.

Suppressing dependency-related lint warnings without understanding the behavior can conceal correctness problems.

## 4. Cleanup Functions

Cleanup functions reverse or dispose of external synchronization established by an Effect.

Typical cleanup operations include:

- Removing event listeners.
- Closing network connections.
- Unsubscribing from message channels.
- Clearing intervals and timeouts.
- Aborting obsolete requests.
- Releasing third-party resources.

React executes cleanup in two important situations:

1. Before rerunning an Effect because its dependencies changed.
2. When the component is removed.

The cleanup function belongs to the previous Effect execution.

It should therefore release the resources associated with that execution rather than relying on values from a later render.

### 4.1 Resource ownership

A useful engineering principle is to make every Effect responsible for the resources it creates.

The setup function acquires a resource.

The cleanup function releases that resource.

This creates a predictable ownership relationship:

    Effect Setup
         |
         v
    Acquire Resource
         |
         v
    Resource In Use
         |
         v
    Effect Cleanup
         |
         v
    Release Resource

A missing cleanup can cause:

- Memory leaks.
- Duplicate subscriptions.
- Repeated event handlers.
- Background operations continuing after unmount.
- Unexpected network activity.
- Multiple timers updating the same state.

### 4.2 Cleanup ordering

When dependencies change, React first executes the previous cleanup and then executes the new setup.

This prevents the old synchronization from remaining active alongside the new synchronization.

Cleanup is not simply an optional optimization. For Effects that acquire external resources, it is part of the lifecycle contract.

## 5. Side Effects and Asynchronous Operations

A side effect is an operation that interacts with something outside the component's rendering calculation.

Common examples include network communication, browser storage, subscriptions, timers, and DOM integrations.

### 5.1 Network requests

An asynchronous request introduces a timing problem.

Suppose a user searches for:

1. React
2. useEffect
3. Cleanup

The first request may finish after the third request.

If the application publishes the first response after the third response, the interface can display obsolete information.

This is a race condition.

An `AbortController` can cancel a fetch request when the relevant Effect is cleaned up.

An alternative is to use an active-request flag or request-generation identifier to prevent obsolete operations from updating state.

Cancellation and stale-result protection solve related but distinct problems:

- Cancellation attempts to stop unnecessary work.
- Stale-result protection prevents obsolete results from being applied.

A robust implementation can use both.

### 5.2 Fetch cancellation

A common React pattern is:

- Create an `AbortController` during setup.
- Pass its signal to `fetch`.
- Process the response if the request remains valid.
- Abort the request during cleanup.
- Handle cancellation separately from genuine request failures.

An aborted request should not be reported as an ordinary application failure.

### 5.3 Error handling

Effects should distinguish between:

- Network failures.
- Authorization failures.
- Invalid responses.
- Request cancellation.
- Timeouts.
- Unexpected application errors.

An Effect does not automatically convert asynchronous failures into ordinary rendering errors.

Asynchronous operations need explicit error handling and appropriate state management.

## 6. React Strict Mode and Effect Replay

React Strict Mode provides additional development-time checks.

In applicable development configurations, React performs an extra setup and cleanup cycle for Effects during initial mounting.

The simplified sequence is:

    Initial Setup
         |
         v
    Cleanup
         |
         v
    Setup Again

This behavior helps identify Effects that incorrectly assume setup will execute exactly once.

Strict Mode replay is not the same as an ordinary production remount.

It is a development mechanism for detecting lifecycle problems.

An Effect should remain correct when its setup and cleanup operations are repeated.

The correct response to Strict Mode is not to introduce arbitrary execution guards that prevent legitimate synchronization.

Instead, setup and cleanup should be designed to be reversible and safe.

## 7. Distinguishing Effects from Other React Mechanisms

| Mechanism | Responsibility |
|---|---|
| Rendering | Calculate the interface |
| State | Store component data |
| Event handlers | Respond to user interactions |
| Effects | Synchronize with external systems |
| Cleanup | Reverse external synchronization |
| Refs | Store mutable values without triggering rendering |
| Memoization | Optimize calculations or preserve references |

Effects should not be introduced merely because a value changes.

For example, a button click should normally perform its direct action through an event handler.

If clicking the button submits a form, the submission belongs in the event handler rather than in an Effect that observes a submission state.

Similarly, derived data should usually be calculated during rendering.

This separation reduces unnecessary renders and makes application behavior easier to understand.

## 8. Python Implementation

The Python file implements a standalone lifecycle simulator using standard-library functionality.

### 8.1 EffectManager

`EffectManager` manages multiple Effect records belonging to one simulated component.

Each record contains:

| Attribute | Purpose |
|---|---|
| `name` | Unique Effect identifier |
| `callback` | Setup function |
| `dependencies` | Previously observed dependencies |
| `cleanup` | Resource disposal function |
| `initialized` | Initial execution state |
| `execution_count` | Number of successful setups |

The manager supports registration, commit processing, cleanup, Strict Mode replay, and unmounting.

### 8.2 Dependency comparison

The `same_value` function approximates JavaScript `Object.is` behavior for common Python values.

Primitive values use value comparison.

Mutable objects use identity comparison.

This distinction demonstrates why creating a new object or list during rendering can cause an Effect to execute again.

The implementation also validates dependency-array length.

### 8.3 Resource management

`ConnectionService` simulates an external subscription service.

A connection is acquired during setup and closed during cleanup.

The demonstration changes the selected channel and verifies that the old connection is released before the replacement is established.

### 8.4 Asynchronous cancellation

`SearchService` uses `asyncio`.

The demonstration starts a request and cancels it before completion.

`asyncio.CancelledError` is handled separately from ordinary application exceptions.

### 8.5 Limitations

The simulator does not implement React's renderer, scheduling priorities, concurrent rendering, browser lifecycle, or actual Hook execution.

Its dependency model is intended for learning lifecycle rules rather than exact runtime equivalence.

## 9. JavaScript Implementation

The JavaScript file provides an event-driven resource-management model.

It uses Node.js standard-library functionality and does not require third-party packages.

### 9.1 EffectRuntime

`EffectRuntime` stores Effect definitions in a `Map`.

Its main operations are:

- `register()`
- `commit()`
- `replayStrictMode()`
- `unmount()`

Each Effect has a setup function, dependency snapshot, cleanup function, and execution counter.

`Object.is` provides dependency comparison consistent with React's documented comparison mechanism.

### 9.2 NotificationService

`NotificationService` extends Node.js `EventEmitter`.

The subscription method registers a listener and returns a cleanup function.

Cleanup removes the exact listener associated with the original subscription.

This is important because removing a different callback reference does not remove the original listener.

### 9.3 SearchController

`SearchController` demonstrates asynchronous request cancellation.

A new search cancels the previous request.

`AbortController` prevents obsolete work from continuing unnecessarily.

The implementation distinguishes cancellation from genuine failures.

### 9.4 ComponentState

`ComponentState` provides a small event-driven state store.

It uses `Map` for values and `Set` for listeners.

Updates notify registered listeners only when the value changes according to `Object.is`.

This is a separate state-management demonstration, not an implementation of React's state Hook.

## 10. C++17 Implementation

The C++17 program uses explicit domain modeling and deterministic resource management.

### 10.1 EffectEngine

`EffectEngine` represents the lifecycle manager for a component.

The `Effect` structure contains:

- Effect name.
- Setup callback.
- Dependency collection.
- Dependency mode.
- Cleanup callback.
- Initialization status.
- Execution count.

`std::function` provides callable setup and cleanup operations.

### 10.2 Dependency modes

The `DependencyMode` enumeration distinguishes:

| Mode | Behavior |
|---|---|
| `EveryCommit` | Execute after every commit |
| `MountOnly` | Execute during initial setup |
| `Tracked` | Execute when dependencies change |

The engine validates dependency counts and prevents commits after unmount.

### 10.3 ResourceRegistry

`ResourceRegistry` tracks acquired and released resources.

It prevents duplicate active acquisitions.

The program verifies that all resources are released after component unmount.

### 10.4 SearchCoordinator

The search coordinator uses generation numbers.

Every new request receives a higher generation identifier.

Only the latest active request can publish a result.

This is useful when cancellation alone cannot guarantee that an asynchronous operation will stop immediately.

### 10.5 Complexity

Let:

- `n` represent the number of registered Effects.
- `d` represent the number of dependencies per Effect.

The principal operations have the following costs:

| Operation | Complexity |
|---|---|
| Effect registration | O(log n) |
| Dependency comparison | O(d) |
| Commit processing | O(n × d) |
| Resource lookup | O(log r) |
| Cleanup traversal | O(n) |

Here, `r` is the number of tracked resources.

The implementation favors explicit ownership and deterministic cleanup over a full concurrent rendering model.

## 11. Java 17 Implementation

The Java implementation models Effect lifecycle management in an enterprise-oriented environment.

### 11.1 Domain types

The implementation defines:

- `ComponentStatus`
- `DependencyMode`
- `Cleanup`
- `EffectSetup`
- `Dependency`
- `EffectPolicy`
- `EffectDefinition`

Java records provide immutable dependency and policy objects.

The separation between policy and execution makes lifecycle rules explicit.

### 11.2 EffectManager

`EffectManager` coordinates Effect registration, dependency comparison, execution, cleanup, and unmounting.

It uses `LinkedHashMap` to maintain predictable registration order.

Cleanup occurs in reverse registration order during unmount.

Synchronized methods protect the manager's mutable lifecycle state against concurrent access.

### 11.3 EffectPolicy

`EffectPolicy` separates dependency behavior from cleanup requirements.

For example, a tracked subscription can require cleanup, while a simple initialization operation may not require a returned cleanup function.

Invalid policy configurations are rejected during registration.

### 11.4 ResourceManager

`ResourceManager` uses `AtomicBoolean` to track resource state.

The returned cleanup function performs an atomic transition from active to released.

This makes repeated cleanup safe for the same resource.

### 11.5 Asynchronous operations

`AsyncSearchService` uses `ExecutorService` and `Future`.

Starting a new request cancels the previous Future.

`close()` shuts down the executor and waits for termination.

The implementation demonstrates explicit task ownership and resource disposal.

It does not claim that every external operation can be forcibly terminated immediately. Cancellation depends on interruption support and the behavior of the underlying operation.

## 12. PostgreSQL Implementation

The SQL file provides a relational model for auditing component and Effect lifecycle operations.

It is intended for lifecycle observability and resource auditing rather than for executing React Effects.

### 12.1 Relational structure

The database models these relationships:

    Components
        |
        +---- Renders
        |
        +---- Effects
                 |
                 +---- Effect Dependencies
                 |
                 +---- Effect Executions
                          |
                          +---- Execution Dependencies
                          |
                          +---- Cleanup Operations
                          |
                          +---- Managed Resources

### 12.2 Components

The `components` table stores component identity and lifecycle status.

The status constraint ensures that a mounted component does not have an unmount timestamp and that an unmounted component has one.

### 12.3 Renders

The `renders` table records committed render events.

A unique constraint prevents duplicate commit numbers within a component.

The `create_render()` function calculates the next commit number while locking the relevant component row.

### 12.4 Effects

The `effects` table records Effect definitions.

The dependency mode distinguishes:

- `every_commit`
- `mount_only`
- `tracked`

The database uses triggers to prevent registration of Effects against unmounted components.

### 12.5 Dependency snapshots

`effect_dependencies` stores dependency definitions.

The `position` field preserves dependency-array ordering.

The unique constraints prevent duplicate dependency positions and names within an Effect.

`dependency_value` stores a JSONB representation.

`dependency_token` provides a separate comparison and auditing value.

JSONB does not reproduce JavaScript reference identity. Therefore, it cannot independently determine whether two JavaScript objects are the same reference.

For reliable auditing, the application should provide appropriate identity or version tokens.

### 12.6 Effect executions

`effect_executions` records individual setup operations.

It stores:

- Execution type.
- Execution status.
- Start time.
- Completion time.
- Cleanup status.
- Error details.

Check constraints prevent inconsistent combinations of execution status and completion timestamps.

### 12.7 Managed resources

The `managed_resources` table records externally managed resources.

A partial unique index prevents two active resources with the same key from being assigned to the same component.

The database retains released resources for historical auditing.

### 12.8 Cleanup operations

The `cleanup_operations` table provides a separate history of resource disposal.

The `release_resource()` procedure locks the resource, updates its state, records cleanup completion, and updates the corresponding execution.

The operation is transactional.

### 12.9 Component unmounting

`unmount_component()` releases active resources before changing the component status.

This enforces a useful lifecycle invariant:

An unmounted component should not retain active managed resources.

The procedure uses row locking to coordinate concurrent modifications.

### 12.10 Reporting and performance

The implementation provides:

- Effect execution retrieval.
- Failure identification.
- Dependency inspection.
- Resource leak detection.
- Cleanup reporting.
- Execution aggregation.
- Component lifecycle reporting.

Indexes support queries based on Effect execution time, execution status, component resource state, and active resource keys.

The lifecycle report uses aggregation to calculate execution counts, failures, and completed cleanups.

## 13. Cross-Language Implementation Comparison

| Dimension | Python | JavaScript | C++17 | Java 17 | PostgreSQL |
|---|---|---|---|---|---|
| Main perspective | Lifecycle simulation | Event-driven effects | Resource governance | Enterprise lifecycle | Lifecycle auditing |
| Dependency tracking | Tuples | Arrays | Struct collections | Immutable records | Relational snapshots |
| Resource management | Classes | EventEmitter | Registry | ResourceManager | Managed resources |
| Cleanup | Callbacks | Functions | `std::function` | Functional interface | Procedures |
| Async handling | asyncio | AbortController | Generation tracking | Future | Execution records |
| Validation | Exceptions | Runtime checks | Exceptions | Domain validation | Constraints and triggers |
| State tracking | Dataclasses | Maps | Enums and structs | Enums and records | Enumerated types |

## 14. Important Engineering Considerations

### 14.1 Avoid unnecessary Effects

An Effect should be introduced when a component needs to synchronize with an external system.

It should not be used automatically for every state change.

### 14.2 Keep dependencies accurate

Every reactive value used by an Effect must be considered when defining dependencies.

Incorrect dependency management can result in stale values, unexpected executions, or unnecessary synchronization.

### 14.3 Make cleanup reliable

Every acquired external resource should have a clear disposal mechanism.

Cleanup should be safe when repeated and should release the resource associated with its own setup execution.

### 14.4 Prevent asynchronous race conditions

Network requests may complete in a different order from the order in which they were initiated.

Use cancellation and stale-result protection to ensure that obsolete requests do not overwrite current state.

### 14.5 Avoid unnecessary object dependencies

Objects, arrays, and functions created during rendering can have new identities on subsequent renders.

This may trigger additional Effect executions.

Stabilize dependencies when appropriate, but do not introduce memoization without a genuine need.

### 14.6 Keep rendering separate from synchronization

Rendering should remain focused on calculating the interface.

Event handlers should handle direct user interactions.

Effects should handle synchronization with external systems.

This separation improves predictability and simplifies debugging.

### 14.7 Understand development behavior

Strict Mode can expose incomplete cleanup and unsafe setup logic.

Repeated setup should not create duplicate external resources or irreversible side effects.

## 15. Limitations

The standalone implementations are conceptual lifecycle models.

They do not reproduce all React runtime behavior.

| Limitation | Practical implication |
|---|---|
| No React renderer | No actual component rendering |
| No concurrent scheduler | No simulation of concurrent rendering |
| Simplified dependencies | Some JavaScript identity behavior is approximated outside JavaScript |
| No browser environment | Browser-specific APIs are represented through simulations |
| No actual network service | Asynchronous operations are controlled demonstrations |
| Database auditing model | SQL does not schedule or execute React Effects |
| Simplified Strict Mode | Does not reproduce every React development check |

The JavaScript implementation uses `Object.is`, while the other languages use domain-specific dependency representations.

These implementations demonstrate lifecycle principles rather than establishing that every language has identical runtime semantics.

## 16. Practical Verification Checklist

- [ ] Effects execute after committed rendering.
- [ ] Omitted dependencies cause execution after every commit.
- [ ] Empty dependency arrays represent mount-only synchronization.
- [ ] Tracked dependencies trigger synchronization when values change.
- [ ] Dependency arrays retain a constant length.
- [ ] Object identity is considered when comparing dependencies.
- [ ] Previous cleanup executes before replacement setup.
- [ ] Final cleanup executes during unmount.
- [ ] Event listeners are removed using their original callback references.
- [ ] Obsolete asynchronous operations cannot publish stale results.
- [ ] Cancellation is distinguished from genuine request failure.
- [ ] Strict Mode replay does not create persistent duplicate resources.
- [ ] Component state and external resource state remain distinct.
- [ ] Resource ownership is explicit.
- [ ] Failed executions remain observable.
- [ ] Cleanup failures are handled and reported.
- [ ] No active resources remain after successful component unmount.

## 17. Execution Requirements

| File | Runtime | Dependencies |
|---|---|---|
| Python | Python 3.10+ | Standard library |
| JavaScript | Node.js 18+ | Standard library |
| C++17 | C++17 compiler | Standard library |
| Java | Java 17 | Standard library |
| PostgreSQL | PostgreSQL 15+ | Built-in database features |

The five implementations provide complementary views of Effect dependency management, synchronization, asynchronous work, cleanup, lifecycle validation, and resource observability.
