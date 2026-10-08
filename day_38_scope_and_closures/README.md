# Scope and Closures

This repository is a language-oriented study of **global scope, function scope, block scope, lexical scope, and closures**. The six artifacts are deliberately different: Python emphasizes executable closure behavior and introspection, JavaScript focuses on lexical environments and asynchronous callbacks, C++ uses lambdas as configurable policy objects, Java models closure-driven enterprise policies with explicit domain types, and PostgreSQL represents lexical environments and captured bindings relationally.

The central relationship is simple but important:

- A **scope** determines where a name can be resolved.
- **Lexical scope** means name resolution is determined by where code is written, rather than by the caller that eventually executes it.
- A **closure** is a function together with access to bindings from its surrounding lexical environment.
- A closure can therefore preserve configuration or state after the function that created it has returned.
- Global, function, and block scope describe different visibility and lifetime boundaries. They are not interchangeable concepts.

## Core terminology

### Global scope

Global scope is the outermost environment available to application code. A global binding can often be reached from many parts of a program, which makes global state convenient but also increases coupling.

The Python implementation uses module-level names such as `APPLICATION_NAME` and `global_request_count`. The JavaScript implementation uses top-level `const` and `let` bindings in the module. The C++ implementation uses namespace-level configuration and a global counter. Java represents application-wide configuration with `static` class members.

Global state is particularly sensitive when mutable. A closure that owns isolated state can often provide a narrower and safer boundary than a mutable global variable.

### Function scope

Function scope is created by a function invocation. Local variables are normally unavailable outside that function.

Python's local variables such as `doubled` exist only inside their defining function. Java creates method-local variables with the same basic visibility property. JavaScript is more nuanced because `var` is function-scoped while `let` and `const` are block-scoped.

Function scope is important for preventing temporary computation variables from becoming part of a wider program environment.

### Block scope

A block is a delimited region, usually represented by braces in languages such as JavaScript, C++, and Java.

JavaScript `let` and `const` are block-scoped. Java and C++ local variables declared inside braces also cease to be accessible after the block.

Python differs significantly here. Ordinary `if`, `for`, and `while` blocks do not create a separate local scope. A variable assigned in an `if` block can remain available in the surrounding function. Python 3 comprehensions have their own iteration-variable behavior, which the Python implementation demonstrates explicitly.

This distinction is important because the phrase "block scope" does not mean exactly the same thing in every programming language.

### Lexical scope

Lexical scope is determined by the physical nesting of declarations in source code.

Consider the conceptual structure `outer -> middle -> inner`. If `inner` refers to a name that it does not define locally, lookup proceeds through its enclosing lexical environments.

A caller does not normally change which enclosing variable an inner function resolves. This is why lexical scoping makes code easier to reason about than dynamic name resolution.

The Python implementation demonstrates this through nested functions and LEGB resolution. JavaScript demonstrates lexical shadowing directly. C++ and Java demonstrate lexical capture through lambdas.

### Closure

A closure combines executable behavior with access to bindings from its defining lexical environment.

The Python function `make_multiplier()` returns `multiply`, which continues to access `factor` after `make_multiplier()` has returned.

The JavaScript `makeMultiplier()` performs the same conceptual operation using a returned function. Java and C++ implement the same broad mechanism through lambdas, although their language rules for captured local variables differ.

The important property is not merely that a function is returned. The returned function retains access to relevant surrounding state.

## Python implementation

The Python program begins with global and function-local bindings before moving into lexical lookup and closures.

`make_multiplier()` demonstrates a minimal closure. Each call creates an independent environment, so `make_multiplier(3)` and `make_multiplier(10)` produce functions with different retained factors.

`make_counter()` demonstrates mutable closure state. The nested function uses `nonlocal` to rebind the variable belonging to its enclosing function. Two counters created by separate factory calls do not share the same `count`.

Python's `nonlocal` is specifically important when a nested function needs to reassign an enclosing binding. Mutating an object captured by a closure is different from rebinding the name. The message collector demonstrates this distinction with a captured list.

The Python program also demonstrates a common closure error involving loop variables. The functions produced by `create_bad_multipliers()` all resolve the same late-bound loop variable when eventually called. `create_good_multipliers()` captures the current value through a default parameter.

Decorators are naturally closure-oriented in Python. `audit_calls()` returns a wrapper that retains the original function. `retry_on_failure()` is a decorator factory, so the returned decorator itself retains configuration such as the permitted attempt count.

The memoization example stores a cache inside a closure. The cache is inaccessible through the ordinary function interface but remains available to the wrapper across calls.

Python-specific runtime inspection is also included through `locals()`, `globals()`, and function `__closure__` information. These mechanisms make the relationship between a function and its captured environment observable.

## JavaScript implementation

JavaScript has a particularly important distinction between `var`, `let`, and `const`.

`var` is function-scoped. A variable declared with `var` inside an `if` block remains accessible within the containing function. `let` and `const` are block-scoped, so their bindings disappear from visibility after the block ends.

The JavaScript implementation uses loop callbacks to expose a classic closure difference. A loop using `var` creates callbacks that reference one shared function-scoped binding. A loop using `let` creates per-iteration lexical bindings, allowing callbacks to retain the expected individual values.

The Temporal Dead Zone example demonstrates another lexical-environment rule. A `let` binding exists in the lexical environment before its initialization is executed, but accessing it before initialization produces a `ReferenceError`. This differs from the historical `var` behavior involving initialization to `undefined`.

`createAccount()` demonstrates closure-based encapsulation. The `balance` variable is not exposed as a property. The returned operations retain access to it and control the permitted mutations.

The asynchronous example demonstrates why closures matter in event-driven JavaScript. Each generated handler retains the `eventName` belonging to its lexical environment, even though the callback executes after the surrounding `map()` operation has completed.

`memoizeUnary()` uses a `Map` retained by the returned function. This demonstrates that a closure can preserve not only scalar configuration but also mutable collections.

## C++ case study

The C++ program models a repository-governance engine because configurable predicates provide a realistic reason to retain lexical configuration.

`GovernanceEngine::Policy` is represented by `std::function<bool(const PullRequest&)>`. Policy factories such as `makeBranchPolicy()`, `makeScorePolicy()`, and `makeStatusPolicy()` return lambdas containing captured configuration.

`makeBranchPolicy("main")` creates a closure that retains the protected branch value. The caller does not need to pass `"main"` every time the policy executes.

The value-capture example shows that `[requiredApprovals]` copies the configuration into the lambda. Reassigning the original variable does not change the copied value stored by the closure.

The reference-capture example uses `[&requiredApprovals]`. The closure refers to the original variable, so later changes to that variable affect policy behavior. This creates a lifetime obligation: the referenced object must remain alive whenever the closure is invoked.

The program deliberately avoids returning a lambda containing a dangling reference to a local variable. Such a closure would produce undefined behavior if invoked after the referenced local had ceased to exist.

The `mutable` lambda in the assertions demonstrates closure-owned state. A lambda that captures a value normally treats the captured member as non-modifiable unless it is declared `mutable`.

The policy engine also demonstrates an important design advantage of closures: policy construction and policy execution are separate operations. The engine can execute a collection of policies without knowing how each policy captured its configuration.

## Java implementation

Java lambdas provide closure behavior through captured local variables. A local variable referenced by a lambda must be final or effectively final.

This restriction is demonstrated through policy construction. `branchPolicy()` captures a protected branch, while `approvalPolicy()` captures a required approval count. The returned `Policy` objects retain those values.

Java's explicit `Policy` functional interface gives the domain model a clear type. `NamedPolicy` associates a human-readable policy name with the executable rule, and `GovernanceService` evaluates the configured rules without embedding each rule directly into the service.

The `Review` and `PullRequest` records provide immutable domain values. Defensive copying through `List.copyOf()` prevents callers from changing the review collection behind a `PullRequest`.

`Predicate<PullRequest>` is used to demonstrate functional composition. Independent lexical rules can be combined with `.and()` to form a larger condition without copying the implementation of each rule.

Java does not permit the same unrestricted local-variable rebinding pattern demonstrated by Python's `nonlocal`. When mutable state is needed, the example uses an object whose internal field changes and a method reference that accesses that state. This is a useful distinction between language-level closure rules.

## SQL data model

The PostgreSQL script represents scope and closure behavior as relational metadata.

`lexical_scopes` stores nested environments and records the relationship between a scope and its parent. The root `module` scope represents a global environment. The `make_multiplier` scope represents a function environment, and the closure environment records the retained environment associated with the returned function.

`bindings` represents named values belonging to scopes. The table deliberately separates the binding's name from its owning scope because two different scopes may legally contain bindings with the same name.

The typed value columns and check constraint ensure that a binding stores a value appropriate to its declared `value_type`. This moves part of the data-integrity rule into PostgreSQL rather than depending entirely on application code.

`closures` represents executable behavior associated with a defining scope. `closure_captures` connects a closure to the bindings it retains and records whether the conceptual capture is by value or reference.

The `invoke_multiplier()` PostgreSQL function demonstrates closure-like behavior at the database representation level. It locates the captured factor, applies it to an input, records the invocation, and raises an exception when the closure or captured configuration is invalid.

The relational representation is intentionally not presented as a literal implementation of a programming language runtime. PostgreSQL does not provide Python-style lexical environments simply by creating these tables. The schema models the relevant concepts so that scope ownership, captured bindings, and invocation history can be queried and constrained.

## Scope relationships

A useful way to distinguish the concepts is to ask different questions.

| Concept | Primary question | Typical lifetime or boundary |
|---|---|---|
| Global scope | Where can application-wide bindings be reached? | Program/module environment |
| Function scope | Which bindings belong to this function invocation? | Function execution |
| Block scope | Which bindings are visible only within this block? | Block execution |
| Lexical scope | Which surrounding declarations can this source location resolve? | Determined by source nesting |
| Closure | Which enclosing bindings remain accessible to this function after its creator returns? | As long as the closure retains them |

Lexical scope explains *which environment* a nested function searches. A closure explains *how the nested function can continue to use that environment after the creating function has completed*.

## Shadowing and name resolution

Shadowing occurs when an inner scope declares a binding with the same name as a binding in an outer scope.

The inner binding normally wins during lexical lookup. The outer binding has not necessarily disappeared. It is simply hidden by the nearer declaration from that particular lexical location.

The examples deliberately use separate names and nested environments to make this relationship visible rather than relying on accidental name collisions.

Shadowing can be useful for narrow transformations, but excessive shadowing makes lexical lookup harder to understand. Configuration values that have materially different meanings should normally have distinct names.

## Closure state and lifetime

A closure may capture immutable configuration, mutable state, or references to existing state.

Value capture is particularly useful when the closure should own an independent copy of configuration. C++ demonstrates this explicitly with value capture.

Reference capture can avoid copying and can intentionally provide shared state, but it introduces lifetime and synchronization concerns. A reference must remain valid for the entire period during which the closure can execute.

Python's `nonlocal` and JavaScript's lexical mutable bindings provide another model: the closure retains access to the original environment rather than creating a simple independent value copy.

The practical design question is whether the closure should own its state or observe external state.

## Common failure modes

### Assuming every block creates a new scope

This is incorrect across languages. Python's ordinary `if`, `for`, and `while` statements do not behave like JavaScript `let` blocks or Java/C++ brace blocks.

### Confusing lexical scope with caller scope

A nested function does not normally search the caller's local variables simply because the caller invoked it. Lexical lookup follows the function's defining environment.

### Capturing a changing loop variable incorrectly

This is one of the most common closure mistakes. JavaScript's `var` example demonstrates shared function-scoped state, while Python's late-binding example demonstrates deferred lookup of the loop variable.

### Rebinding versus mutating

Changing the object referenced by a captured name is not necessarily the same as rebinding the name itself. Python's `nonlocal` keyword is required for rebinding an enclosing local variable.

### Allowing a reference to outlive its owner

C++ reference-capturing lambdas can become unsafe when the referenced object is destroyed before the lambda executes. The safe alternative is often value capture or an explicitly managed ownership model.

### Expecting Java lambdas to capture arbitrarily changing locals

Java requires captured local variables to be final or effectively final. Mutable state must be represented through an object or another suitable state holder.

## Performance considerations

Closures are not inherently expensive enough to avoid categorically. Their cost depends on the language runtime and the captured state.

A closure that captures a large object by value may require copying. A closure that captures by reference may avoid copying but introduces lifetime concerns.

Memoization can improve computational performance by avoiding repeated work, but its cache consumes memory. The Python and JavaScript implementations use closure-owned caches to make that trade-off explicit.

Deeply nested closures can make debugging and memory ownership harder to reason about. In long-lived applications, a closure that retains a large object graph can prevent those objects from becoming eligible for reclamation.

Performance decisions should therefore consider both execution cost and the lifetime of captured objects.

## Security considerations

Closures are not automatically security boundaries.

A closure can hide state from ordinary callers, as demonstrated by the account factories, but code with access to the closure can still execute its retained behavior.

Closure-based encapsulation is useful for reducing accidental mutation, but authorization must still be enforced at an appropriate system boundary.

Captured configuration can also become stale. If a security policy changes after a closure has been created, an old closure may continue using the configuration it retained. Systems with dynamic security policies should explicitly decide whether policies capture immutable snapshots or read current policy state.

## Debugging considerations

When debugging a closure, inspect both the function and the values it can access.

Python exposes useful runtime information through function closure cells. JavaScript debugging tools can show lexical environments associated with paused execution. C++ debugging requires attention to lambda capture lists and object lifetimes. Java requires understanding which effectively-final locals were captured by a lambda.

A useful debugging question is:

> Is this function reading a local binding, an enclosing binding, a global binding, or mutable state owned by the closure?

That question often identifies scope-related defects faster than inspecting the function body alone.

## Design implications

Closures are especially useful when behavior and configuration belong together.

A validator factory can retain its validation boundaries. A formatter can retain formatting configuration. A memoized function can retain its cache. An event handler can retain the event category it processes. A policy factory can retain the policy threshold that applies to the returned predicate.

The key design boundary is that the caller receives behavior rather than repeatedly supplying configuration.

This can reduce parameter passing and isolate state, but it can also make hidden dependencies less obvious. Good closure design therefore balances encapsulation with readability.

## Cross-language distinctions

Python uses nested lexical functions, `nonlocal`, default arguments, and decorators to make closure behavior explicit.

JavaScript's closure model is deeply connected to its lexical environments, `let` and `const`, asynchronous callbacks, and higher-order functions. The difference between `var` and `let` is especially important when closures are created inside loops.

C++ lambdas expose capture semantics directly through capture lists such as `[value]`, `[&value]`, and mutable closure objects. Lifetime correctness is therefore a major consideration.

Java lambdas capture final or effectively-final local variables and integrate closely with functional interfaces such as `Predicate` and `Supplier`. Mutable state generally belongs in an object rather than through direct local-variable rebinding.

PostgreSQL does not reproduce a language runtime's lexical environment. Its implementation instead models scopes, bindings, captures, and invocations as relational entities so their relationships can be queried and constrained.

The shared concept across these implementations is lexical visibility combined with retained environmental state, while the exact mechanisms differ substantially by language.
