# JavaScript Execution Semantics: Call Stack, Execution Context, Lexical Environment, and Hoisting

## Technical scope

JavaScript execution depends on several mechanisms that interact but serve different purposes. The call stack tracks active synchronous execution. An execution context represents the state associated with running a script or function. A lexical environment stores identifier bindings and links to an outer environment. Hoisting describes observable declaration behavior that results from environment setup before ordinary statement execution.

These mechanisms explain why a function can read a variable declared outside its body, why a `var` binding can be read before its assignment, why a `let` binding can exist but remain inaccessible, and why recursive calls consume stack space even when their functions share the same outer environment.

The five implementations approach these concepts from different perspectives:

| Deliverable | Technical emphasis |
|---|---|
| Python | Explicit simulation of bindings, environment chains, execution contexts, closures, and bounded stack behavior |
| JavaScript | Actual language behavior, including temporal dead zones, closures, loop bindings, promises, and event-loop ordering |
| C++ | A repository deployment case study using explicit environments, function objects, nested calls, and exception-safe stack frames |
| Java | An enterprise-oriented execution model with typed domain objects, explicit state transitions, and closure lifetime |
| PostgreSQL | Relational storage of environments, bindings, contexts, stack frames, and execution events with integrity constraints |

The Python, C++, and Java programs are educational models of selected semantics. They do not parse or execute arbitrary JavaScript source code. The JavaScript program runs the language mechanisms directly.

## Call stack and execution contexts

### Call stack

The call stack records active synchronous function calls. When a function is invoked, execution enters that function. When it returns, its active call is removed from the stack. Nested calls create nested execution frames.

Consider a request-processing sequence:

`handleRequest()` calls `validateRequest()`, which may call `persistAuditRecord()`.

While the innermost function runs, its caller remains suspended below it. Once the inner call returns, execution continues in the caller. An exception can unwind several frames before a matching handler catches the error.

The call stack is not the same as the lexical scope chain. A caller's local variables do not become accessible to a callee simply because the caller remains on the stack. Identifier resolution follows lexical environment links.

Deep recursion can exhaust the available stack. The precise stack limit depends on the runtime, execution environment, and call structure. JavaScript does not guarantee a universal numeric limit.

### Execution context

An execution context represents the runtime state associated with a running unit of JavaScript. At a conceptual level, it includes the running code, the relevant lexical environment, the variable environment, and `this`-related state.

Execution contexts are specification concepts rather than ordinary JavaScript objects that programs can inspect directly.

A function call creates the context needed to execute that function. The context is associated with its parameters and local declarations. The function's lexical environment also links to the environment in which the function was defined.

The distinction between lexical and variable environments matters when examining declarations. In simplified cases, both can refer to the same environment. In more complex language constructs, their roles differ. The exact behavior depends on whether code is executing as a script, module, function, or block and on the declarations involved.

The Python, C++, and Java models expose these relationships through explicit objects. The JavaScript file instead demonstrates their observable effects.

## Lexical environments and identifier resolution

A lexical environment consists conceptually of an environment record and a reference to an outer environment. Environment records hold bindings for identifiers. The outer reference makes nested lexical scopes possible.

For example:

- A global or module environment can hold an application-wide service configuration.
- A function environment can hold parameters and local bindings for a request.
- A block environment can hold a temporary deployment region that shadows an outer binding.

When an identifier is evaluated, the runtime searches the relevant environment and then its outer environment chain. The first matching binding determines the result. If no matching binding exists, an unresolved identifier produces a `ReferenceError` when evaluated.

Shadowing occurs when a nested scope declares an identifier with the same name as an outer binding. The inner binding takes precedence within its scope without changing the outer binding.

The Python implementation uses `LexicalEnvironment.outer` and `resolve()` to make the search process explicit. The C++ implementation uses shared environment objects so function objects can retain references to captured environments. The Java implementation uses `LexicalEnvironment.resolve()` and typed bindings to make lookup and initialization failures explicit.

The PostgreSQL model represents environment parentage with `outer_environment_id`. Its `read_binding()` function follows the parent chain until it finds a binding or reaches the root.

## Hoisting, initialization, and the temporal dead zone

Hoisting is a useful description of observable declaration behavior, but it should not be interpreted as JavaScript physically moving source lines.

Declaration instantiation establishes bindings before ordinary statements execute. Different declaration forms have different initialization and redeclaration rules.

### `var`

A `var` binding is initialized to `undefined` during the relevant declaration setup. Its later assignment is a separate operation.

For example, the following source produces `undefined` before the assignment executes:

`console.log(retryCount); var retryCount = 4;`

The declaration is available, but the assignment has not yet executed.

Function-scoped `var` declarations are not block-scoped. A declaration inside an ordinary block belongs to the containing function or applicable script-level variable environment. This behavior is one reason `var` can produce surprising results in loops and nested blocks.

### Function declarations

Function declarations are generally initialized during declaration instantiation, allowing calls before their textual position in the relevant scope.

This rule is not equivalent to saying every function expression is hoisted as an initialized callable value. A variable declared with `var` and assigned a function expression still has an initial `undefined` value until the assignment executes.

Block-level function declaration behavior has additional rules, so examples involving functions inside blocks should be interpreted according to the relevant language mode and specification semantics.

### `let` and `const`

Lexical declarations create bindings that cannot be accessed before initialization. The period from scope entry until the declaration's initialization is called the temporal dead zone.

For example:

`console.log(deploymentRegion); let deploymentRegion = "ap-south-1";`

The access throws a `ReferenceError`. The binding is not absent; it exists but is uninitialized.

A `const` declaration must also be initialized when declared. Reassigning an initialized `const` binding produces a `TypeError`.

`const` does not make an object deeply immutable. It prevents reassignment of the binding. Properties of the referenced object can still be changed unless another mechanism, such as `Object.freeze()`, prevents those changes.

The JavaScript implementation demonstrates the difference between a lexical binding in its temporal dead zone and a genuinely undeclared identifier. It also shows that `typeof` does not bypass a temporal dead zone.

## Closures and environment lifetime

A closure is a function together with access to its surrounding lexical environment. It allows a function to continue using captured bindings after the outer function has returned.

The JavaScript implementation uses `createRateLimiter()` to create a function that retains a private request counter. Each call changes the captured `remaining` binding. A later invocation observes the updated value.

This behavior demonstrates that closures retain access to bindings, not simply copies of their values. The captured environment remains reachable while the closure needs it.

Closures are useful for:

- Keeping internal state private without exposing a mutable global variable.
- Creating request counters and rate-limiting functions.
- Retaining configuration for a callback.
- Implementing event handlers that depend on the environment in which they were created.

A closure can also retain objects longer than intended. A long-lived callback that captures a large object graph can increase memory usage. The relevant production concern is the lifetime of reachable objects, not merely whether the function that created them has returned.

### Loop closures

The JavaScript implementation contrasts callbacks created inside `var` and `let` loops.

With `var`, callbacks generally refer to the same function-scoped binding. When the loop completes, each callback observes the final value of that binding.

With a `let` declaration in a loop initializer, JavaScript creates per-iteration lexical bindings for the loop's iteration semantics. Each callback can therefore retain its corresponding iteration value.

This distinction is a consequence of lexical binding behavior, not a special feature of arrow functions.

## JavaScript execution and asynchronous work

The JavaScript event loop introduces a distinction between synchronous call-stack execution and queued work.

A synchronous function runs until it returns or throws. A promise reaction runs as a microtask after the current synchronous execution reaches a suitable checkpoint. A timer callback is scheduled through the host's timer mechanisms and is not guaranteed to run at an exact wall-clock time.

In the JavaScript file, the execution trace distinguishes:

- Synchronous statements executed immediately.
- A promise reaction queued as a microtask.
- A timer callback scheduled for later execution.
- An `async` function continuation after `await`.

An `await` expression suspends the current async function's continuation. It does not block the JavaScript thread while waiting for the awaited promise. When the promise settles, the continuation is scheduled for later execution.

The function's lexical bindings remain available after suspension. The original synchronous call-stack frame does not remain continuously active while the function is suspended. This distinction is important when debugging asynchronous call paths.

The exact ordering of timers and asynchronous callbacks depends on the host environment and scheduling conditions. The program's assertion tests a controlled Node.js scenario rather than claiming a universal timing guarantee.

## Python implementation

The Python file models the language concepts with explicit data structures.

`Binding` records the declaration kind, value, initialization state, and mutability. `LexicalEnvironment` stores local bindings and references to an outer environment. Its `resolve()` method implements lexical lookup, while `get()`, `set()`, and `initialize()` distinguish reading, assignment, and initialization.

`ExecutionContext` separates the lexical environment from the variable environment. `CallStack` tracks active contexts and enforces a configurable maximum depth.

`JavaScriptFunction` creates a local environment for each invocation, initializes parameter bindings, pushes a context, and removes the context in a `finally` block. This cleanup is important because an exception must not leave a simulated frame on the stack.

The closure demonstration creates a request-ID generator that retains its sequence counter after the factory returns. The recursive factorial example shows nested contexts and bounded stack behavior. Additional cases cover shadowing, unresolved identifiers, temporal dead zones, and constant reassignment.

The simulator intentionally uses a limited value model. It does not reproduce JavaScript's full coercion rules, objects, prototypes, modules, `this` binding semantics, or complete grammar. Its value is the explicit separation of concepts that the actual runtime normally manages internally.

## JavaScript implementation

The JavaScript file demonstrates real runtime behavior instead of simulating the environment machinery.

The call-stack example uses nested request-processing functions and shows exception propagation. The declaration example compares `var`, function declarations, `let`, and `const`. The scope example shows that block-level `let` and `const` bindings do not escape their block while `var` can.

The rate limiter and counter demonstrate closures that retain mutable state. The loop callback example exposes the difference between shared `var` bindings and per-iteration `let` bindings.

The asynchronous examples use promises, timers, and `await` to distinguish synchronous execution from scheduled continuations. Assertions verify important results, and the top-level rejection handler reports unexpected failures and sets a failing process exit code.

These examples should be run with Node.js rather than through a simulated interpreter because their purpose is to demonstrate native JavaScript execution behavior.

## C++ case study: deployment-policy evaluation

The C++ program models a deployment orchestrator that checks artifact identifiers and verifies an artifact before publication.

Its architecture separates:

- `Environment`, which stores bindings and links to outer environments.
- `ExecutionContext`, which associates a function with its lexical and variable environments.
- `CallStack`, which tracks active execution contexts and applies a depth limit.
- `Runtime`, which creates function-local environments and invokes function bodies.
- `FunctionObject`, which stores parameters, a callable body, and a captured environment.

The artifact-publication function invokes the signature-verification function through the runtime. This creates nested frames, illustrating how function calls affect the stack while identifier access follows environment links.

`StackFrameGuard` applies C++ RAII. It pushes a frame when constructed and pops the frame when destroyed. Because destruction also occurs during exception unwinding, a failed verification does not leave a stale frame behind.

The closure example stores a shared pointer to an environment containing a sequence counter. The returned function retains that environment, so later invocations continue the sequence after the factory has completed.

The implementation uses `std::map` for binding lookup and `std::shared_ptr` for environment lifetime. These choices make the model easy to inspect, although a production interpreter would require more elaborate memory management, value representations, and language semantics.

The program is compiled with C++17. Its explicit error classes and stack limits represent selected runtime failures without claiming to reproduce a particular JavaScript engine's exact stack limit or exception messages.

## Java implementation

The Java implementation models the same broad execution concepts using explicit domain types and a release-service scenario.

`BindingKind` distinguishes declaration types. `Binding` manages initialization and assignment rules. `LexicalEnvironment` owns local bindings and resolves identifiers through outer environments. `ExecutionContext` records the active function and its associated environments. `CallStack` tracks nested calls.

`JsFunction` combines parameter names, a captured lexical environment, a function body, and a stack. When invoked, it creates a local environment, binds the supplied arguments, constructs an execution context, and ensures stack cleanup in a `finally` block.

The closure demonstration creates an artifact-ID generator whose sequence counter survives the factory call. The nested-call demonstration verifies an artifact before publishing it and checks that invalid identifiers are rejected without corrupting the call stack.

The Java model uses an explicit `Undefined` enum value to distinguish an uninitialized modeled binding from an initialized value. This is an implementation choice for the simulator, not a representation required by JavaScript itself.

Java's static type system makes the model's state transitions and error paths explicit. The trade-off is that the Java code must represent runtime concepts manually, whereas JavaScript engines already implement those semantics.

## PostgreSQL data model

The SQL implementation stores execution information in a relational schema named `execution_lab`.

### Environment and binding relationships

`runtime_sessions` identifies each simulated run and stores a maximum stack depth.

`lexical_environments` stores environment type and parent links. The composite foreign key ensures that a parent belongs to the same session. The self-reference check prevents an environment from directly parenting itself, although additional cycle detection would be needed to prevent longer cycles.

`identifier_bindings` stores the declaration kind, textual value, and initialization state. Its unique constraint prevents duplicate identifiers within the same environment. This allows the same name in different nested environments, as lexical shadowing requires.

The initialization constraint ensures that an initialized binding has an initialization timestamp and that an uninitialized binding does not. The declaration check prevents modeled `var` and function bindings from remaining uninitialized.

### Initialization and lookup

`declare_binding()` creates a binding with declaration-specific initialization behavior. A `var` binding receives the modeled value `undefined` when it is created without an explicit initialized value. A lexical binding can remain uninitialized.

`initialize_binding()` locks the binding row and rejects attempts to initialize a binding that is already initialized. The row lock helps prevent competing transactions from both observing the same binding as uninitialized and successfully initializing it.

`read_binding()` walks the environment-parent chain. It raises an error for a temporal-dead-zone access and reports an unresolved identifier when the root environment is reached without a match.

The `binding_initialization_guard` trigger prevents an initialized constant from being reassigned through ordinary updates and prevents a binding from returning to an uninitialized state. This is database-level enforcement for the modeled rules, not a complete implementation of ECMAScript.

### Execution contexts and stack frames

`execution_contexts` associates each function execution with its lexical environment, variable environment, `this` description, status, and timestamps.

`call_stack_frames` records active stack positions. The partial index on unpopped frames supports queries that inspect the current stack.

`push_context()` locks the session row, checks the configured depth limit, creates an active context, and appends a frame. The session lock serializes competing pushes for the same session, while the depth check rejects calls beyond the configured limit.

`pop_context()` enforces last-in, first-out behavior by requiring the requested context to be the current top frame. It records the final status and exit time.

The demonstration uses a transaction to show nested frames and their removal. The schema does not implement a complete JavaScript runtime, and production deployment would require additional safeguards around transaction failures, concurrent session ownership, and environment-cycle detection.

### Execution traces and diagnostic queries

`runtime_events` provides an event log for declaration, initialization, reads, assignments, calls, returns, throws, suspension, and resumption. Its indexes support chronological inspection and filtering by identifier.

The final queries expose execution contexts alongside their lexical and variable environments, list event traces, and identify bindings that remain uninitialized.

These records make it possible to examine whether an observed failure came from an unresolved identifier, an uninitialized lexical binding, an invalid assignment, or a stack-management violation.

## Important distinctions and implementation boundaries

| Concept | Governing question | Common mistake |
|---|---|---|
| Call stack | Which synchronous function calls are active? | Assuming callers' local variables are automatically visible to callees |
| Execution context | What execution state belongs to the running code? | Treating the context as an ordinary inspectable JavaScript object |
| Lexical environment | Where does identifier lookup find a binding? | Assuming lookup searches the call stack |
| Hoisting | What bindings are established before statement execution? | Assuming all declarations behave like initialized variables |
| Temporal dead zone | Has a lexical binding been initialized yet? | Treating an uninitialized `let` binding as undeclared |
| Closure | Which outer bindings remain accessible to a function? | Assuming captured values are always frozen copies |
| Asynchronous continuation | When does suspended code resume? | Assuming an `await` keeps the original synchronous frame active |

The distinction between a declaration and its initialization is especially important. Hoisting does not mean assignments happen early. A binding can exist before the source statement that initializes it executes.

Similarly, the lexical environment is not simply a snapshot of variables at function-creation time. Closures can observe changes to captured mutable bindings. The lifetime of a captured environment depends on reachability and runtime memory management.

The Python, C++, Java, and SQL implementations deliberately expose a selected set of these mechanisms. Their models use simplified values and declaration rules. JavaScript behavior involving modules, classes, direct evaluation, parameter environments, named function expressions, block-level function declarations, and host-specific asynchronous scheduling requires more complete treatment than these models provide.

## Debugging and production considerations

When a variable appears to have an unexpected value, inspect its declaration type, initialization point, scope, and any shadowing binding. A `ReferenceError` may indicate either an unresolved name or a temporal-dead-zone access, and those cases require different fixes.

When a recursive operation fails, inspect the call chain and determine whether recursion has a terminating condition. A stack limit is not a substitute for correcting an unbounded recursive algorithm.

When a closure retains state unexpectedly, inspect which bindings and objects the closure references and how long the callback remains reachable. Long-lived timers, event listeners, and caches can keep captured objects alive.

When debugging asynchronous code, distinguish synchronous frames from asynchronous continuations. Promise reactions and timer callbacks execute after the current synchronous work reaches appropriate scheduling points. A stack trace may therefore show only part of the causal sequence.

Finally, avoid using `var` merely because it permits reads before assignment. Prefer declaration forms whose scope and initialization behavior are explicit. Use `let` for reassignable lexical bindings and `const` when the binding should not be reassigned. These choices do not replace careful initialization, error handling, or scope design, but they make common execution mistakes easier to detect.
