# JavaScript `this`: Behavior, Methods, Constructors, `call`, `apply`, `bind`, and Arrow Functions

## Topic scope

JavaScript's `this` value identifies the receiver used by a function invocation. It is not generally determined by where a function was declared. For ordinary functions, the invocation form determines the receiver, subject to strict-mode rules and whether the function is bound.

This distinction matters when object methods become callbacks, when constructors initialize instances, and when functions are passed to event handlers or services.

The Python, C++, Java, and SQL files provide comparisons and related repository-governance examples. They do not implement JavaScript's exact `this` semantics because those languages have different object and method models.

## Core distinctions

| Mechanism | Receiver behavior | Main use |
|---|---|---|
| `object.method()` | The receiver is `object` | Invoke an object's method |
| `fn.call(receiver, a, b)` | Uses `receiver` and passes positional arguments | Invoke a function immediately with an explicit receiver |
| `fn.apply(receiver, [a, b])` | Uses `receiver` and passes an array-like argument collection | Invoke with an existing collection of arguments |
| `fn.bind(receiver, a)` | Creates a new function with a bound receiver and optional preset arguments | Preserve a receiver for later callback execution |
| `new Constructor(a)` | Creates an instance and binds it as the constructor's `this` | Initialize objects |
| `() => expression` | Inherits `this` from the surrounding lexical context | Preserve an outer receiver inside callbacks |
| `function () {}` | Receiver depends on the invocation | Define methods or standalone functions with dynamic receiver behavior |

### Method invocation

In `reviewer.describe()`, JavaScript evaluates the call with `reviewer` as the receiver. Extracting the method into another variable removes that property-call context.

For example, `const fn = reviewer.describe; fn()` does not retain `reviewer` merely because the function originated as a property. Under strict mode, an ordinary function called without a receiver has `this === undefined`. Accessing a property through that undefined value throws a `TypeError`.

The JavaScript implementation demonstrates this failure and shows how `extracted.call(reviewer)` restores the intended receiver.

### `call` and `apply`

`call` and `apply` invoke a function immediately. They differ in how they supply the function's arguments.

- `describeTask.call(engineering, "approve the patch", "high")` supplies positional arguments.
- `describeTask.apply(security, ["inspect authentication changes", "critical"])` supplies an argument collection.

These methods are useful when one function should operate on different objects that expose the properties it needs. That pattern is sometimes called borrowing a method. It should be used only when the receiver provides the expected data and behavior.

### `bind`

`bind` creates a new function. The original function is not executed when `bind` is called.

A bound function retains its bound receiver when invoked later. Extra arguments passed to `bind` are placed before arguments supplied during the later invocation.

In the JavaScript example, `describeTask.bind(engineering, "merge the validated change")` fixes the receiver and the first task argument. Calling the resulting function supplies the remaining urgency argument.

Binding is useful for callbacks passed to timers, event handlers, and application services. It also has limitations: a bound receiver cannot be replaced by calling the bound function with a different receiver. A bound function used with `new` follows constructor-specific rules, so ordinary receiver-binding assumptions should not be applied indiscriminately to constructor calls.

## Constructors and `new`

When an ordinary constructor is invoked using `new`, JavaScript creates an instance, connects its prototype, and invokes the constructor with the new instance as `this`. The constructor's own return value affects the result if it explicitly returns an object; primitive return values do not replace the newly created instance.

The JavaScript file uses `RepositoryMember` to assign instance properties and places `describe` on its prototype. The `new.target` check in `SafeMember` detects calls made without `new`.

JavaScript class constructors must be invoked with `new`. Class methods also execute in strict mode. Constructors and methods should validate required input before storing state that later governance decisions depend on.

## Arrow functions

Arrow functions do not create their own `this`. They capture the surrounding lexical value instead.

In `dashboard.makeCallbacks()`, the arrow callback retains the dashboard receiver even after the callback is extracted. Calling `arrow.call(otherObject)` does not change the captured receiver. Calling `arrow.bind(otherObject)` likewise cannot replace its lexical `this`.

Arrow functions are appropriate for callbacks that need an outer object's receiver. They are not interchangeable with ordinary methods in every situation. They cannot serve as constructors and do not provide their own `arguments` object. Rest parameters offer an explicit way to collect their arguments.

Ordinary functions remain useful when the invocation receiver is intentional, such as a method whose behavior should depend on the object through which it is called.

## Practical callback failures

A common failure occurs when a method is passed directly as a callback:

- `const handler = service.send` extracts the function.
- `handler()` no longer expresses `service.send()`.
- A receiver-dependent implementation may fail because `this` is undefined.
- `service.send.bind(service)` creates a callback that retains the service.

An alternative is an arrow wrapper such as `() => service.send()`. The wrapper invokes the method through the service object, preserving the method-call receiver. The choice between binding and wrapping depends on whether arguments, identity, and callback lifetime matter.

In browser code, ordinary DOM event handlers can have a receiver associated with the event target, while arrow handlers retain lexical `this`. Exact behavior depends on the API and invocation mechanism. Node.js does not provide browser DOM objects, so the included script models callback receiver behavior without requiring a browser.

## Python implementation

The Python script uses `JavaScriptObject` to represent receiver data and explicitly passes that object to functions. Its `js_call`, `js_apply`, and `js_bind` helpers model the broad differences between immediate invocation, argument collections, and deferred invocation.

Python's bound methods work differently: extracting `employee.describe` generally retains the instance. Python uses `self` as a conventional explicit first parameter rather than applying JavaScript's invocation-dependent `this` rules.

The Python arrow-function analogy is a closure that captures the relevant owner value. It illustrates the purpose of lexical capture, not the JavaScript runtime implementation.

## C++ case study

The C++ program models merge eligibility for repository Pull Requests. Each `PullRequest` contains a source branch, target branch, approval count, status checks, and review-conversation state.

Its `isMergeEligible() const` member function evaluates the object's stored state. Inside a non-static member function, `this` points to the current C++ object. The member function does not acquire a different receiver because its function pointer is invoked through another object.

The program uses `std::all_of` to require every configured check to pass, validates construction parameters, and rejects identical source and target branches. `GovernanceService` receives a `const PullRequest&`, making the selected object explicit.

A pointer to a member function still requires an object for invocation. The program demonstrates this with `eligible.*eligibilityMethod`. A lambda captures a reference to a chosen Pull Request to retain access to that object. Unlike JavaScript's garbage-collected references, C++ reference captures require careful lifetime management: invoking a callback after its referenced object has been destroyed would be invalid.

The case study also distinguishes merge eligibility from authorization to perform the merge. A production service would need to enforce reviewer identity, approval freshness, branch protection, and current status-check results at the time of the actual merge operation.

## Java implementation

The Java implementation defines explicit `ReviewState` and `CheckState` enums, a `Review` class, a `PullRequest` domain object, and a `MergeEligibilityService`.

Java's `this` refers to the current instance. Constructor assignments such as `this.number = number` distinguish instance fields from same-named parameters. Defensive copies created by `List.copyOf` and `Map.copyOf` prevent external changes to the supplied collections after construction.

`countEligibleApprovals()` excludes reviews by ineligible reviewers. A `CHANGES_REQUESTED` decision from an eligible reviewer blocks merging. Required checks must be present and successful, all required conversations must be resolved, and the target must be protected.

The method reference `ready::isMergeEligible` retains the receiver object. The lambda `() -> service.evaluate(ready)` captures references to the service and Pull Request. Java does not expose JavaScript's `Function.prototype.call`, `apply`, or `bind`; method references and lambdas are the normal mechanisms for passing receiver-dependent behavior as callbacks.

The model is deliberately simplified. It does not implement approval dismissal history, stale approvals after new commits, merge queues, or authorization checks for the identity initiating a merge.

## SQL implementation and database modeling

The PostgreSQL script defines relational entities for repositories, repository members, branches, branch-protection policies, Pull Requests, commits, reviews, inline comments, status checks, and merge events.

Foreign keys preserve relationships between records. Check constraints restrict valid lifecycle states, review decisions, status-check results, merge methods, and branch names. Unique constraints prevent duplicate branch names within a repository, duplicate Pull Request numbers within a repository, repeated commits in one Pull Request, and duplicate check names for a Pull Request.

The indexes support common access paths: retrieving Pull Requests by repository and lifecycle state, examining review decisions by Pull Request, and locating unresolved comments. Database constraints protect individual rows and relationships, but cross-table rules such as counting eligible approvals require queries, triggers, or application-level transactions.

A production eligibility view should evaluate the current protection policy, active reviewer membership, latest effective review states, stale approvals, all required checks, unresolved conversations, conflicts, base-branch synchronization, and permitted merge methods. Merge execution should lock or revalidate the relevant records in a transaction to reduce race conditions between checking eligibility and merging.

## Important limitations

The examples teach receiver behavior and cross-language distinctions. They are not drop-in implementations of GitHub's complete governance rules.

JavaScript `this` behavior depends on function kind, invocation form, strict mode, and binding. Python, C++, and Java use different method-binding and object-reference models. Similar-looking callback code therefore does not guarantee equivalent behavior across these languages.

The repository-governance models are educational. A production implementation must obtain authoritative review and check data, authenticate the actor requesting a merge, evaluate the current target-branch policy, and recheck eligibility immediately before committing the merge operation.
