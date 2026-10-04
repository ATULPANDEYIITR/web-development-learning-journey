# Variables and Data Types in JavaScript

## Scope

This repository studies JavaScript's variable declarations and primitive data types through three complementary implementations.

The central JavaScript mechanisms are:

- `var`, `let`, and `const`
- strings
- numbers
- booleans
- `null`
- `undefined`
- `Symbol`
- `BigInt`

The implementations deliberately distinguish declaration semantics from value semantics. A variable declaration determines how a binding behaves, while a data type describes the kind of value stored in or produced by an expression.

The Python implementation builds an executable model of JavaScript-specific behavior. The JavaScript implementation uses actual ECMAScript semantics and Node.js facilities. The C++ implementation takes a systems-oriented approach by designing a strongly typed repository-event validation service that represents the same conceptual categories using C++ types.

## Variable Bindings

JavaScript provides three declaration keywords with materially different behavior.

### `var`

`var` is function-scoped rather than block-scoped. A declaration inside an `if`, `for`, or other block remains accessible throughout the containing function.

`var` declarations are also hoisted. Before the assignment is reached, the binding has the value `undefined`. This differs from `let` and `const`, which are subject to the temporal dead zone.

The JavaScript implementation demonstrates this through `varScopeExample()` and `varHoistingExample()`.

`var` is generally avoided in modern application code when lexical scoping is preferred because block-level reasoning becomes harder when declarations escape their local blocks.

### `let`

`let` creates a block-scoped binding and permits reassignment.

For example, a retry counter is a natural `let` binding when its value changes during execution. The binding can be reassigned without creating a new declaration.

A `let` declaration cannot be redeclared in the same lexical scope, and accessing it before initialization produces a `ReferenceError`.

### `const`

`const` creates a block-scoped binding that must be initialized when declared and cannot subsequently be reassigned.

The important distinction is between rebinding and mutation. If a `const` variable refers to an object, the reference cannot be replaced, but properties of the object can still be changed unless the object is separately protected.

The JavaScript implementation demonstrates this with a configuration object whose `mode` and `retries` properties are mutated while the `configuration` binding remains unchanged.

`const` therefore does not mean that an object is deeply immutable. It means that the variable binding cannot be reassigned.

## Scope and the Temporal Dead Zone

`let` and `const` participate in lexical scoping. Their bindings are established for the relevant lexical environment but remain inaccessible until execution reaches their initialization.

This interval is called the temporal dead zone.

The JavaScript implementation deliberately evaluates an expression that attempts to read a lexical binding before its declaration. The resulting `ReferenceError` demonstrates why the temporal dead zone is observable behavior rather than merely a documentation concept.

This is different from `var`, whose hoisted binding has the value `undefined` before its assignment.

## Strings

JavaScript strings are primitive immutable values.

Operations such as `trim()`, `toLowerCase()`, `replace()`, `split()`, and template-literal interpolation produce values without mutating the original primitive string.

The implementation uses repository and branch names as realistic string data. It normalizes a branch name, constructs a repository identifier with a template literal, splits a commit message into words, and validates text before accepting it as a branch-like identifier.

The branch validation example rejects control whitespace and a path traversal sequence. This illustrates an important boundary rule: string values may be syntactically valid JavaScript strings while still being invalid for a particular application domain.

### UTF-16 behavior

JavaScript strings are represented using UTF-16 code units. Consequently, the `.length` of a string does not necessarily equal the number of Unicode code points.

The JavaScript implementation compares the UTF-16 length of `JavaScript 🚀` with its code-point count using `Array.from()`.

This distinction matters when code performs character limits, cursor positioning, slicing, or protocol validation involving non-BMP Unicode characters.

## Numbers

JavaScript has one primary ordinary numeric type: `Number`.

`Number` uses IEEE-754 double-precision floating-point representation. It supports integers and fractional values but does not provide exact representation for every decimal fraction.

The familiar result of `0.1 + 0.2` demonstrates the consequences of binary floating-point representation. Formatting the result with `toFixed()` can control presentation, but formatting does not change the underlying numeric representation.

### Safe integers

JavaScript provides exact integer representation only within the safe-integer range:

`Number.MAX_SAFE_INTEGER` is `2^53 - 1`.

Beyond this boundary, distinct mathematical integers can map to the same floating-point representation. `Number.isSafeInteger()` should therefore be used when exact integer identity matters.

This becomes important for identifiers, counters, sequence numbers, monetary subunits, database keys, and event offsets.

### `NaN` and infinity

`Number` also represents special IEEE-754 values such as `NaN` and positive or negative infinity.

`NaN` is unusual because it is not equal to itself. The implementation uses `Number.isNaN()` instead of equality testing.

`Number.isFinite()` is used when application logic requires a real finite numeric value.

Explicit numeric validation is safer than allowing arbitrary coercion at configuration or API boundaries.

## Booleans

The boolean primitive has exactly two values:

- `true`
- `false`

The JavaScript implementation uses booleans to represent independent repository conditions and combines them into a `mergeAllowed` decision.

This is distinct from truthy and falsy coercion.

A particularly common error is parsing a string such as `"false"` with `Boolean("false")`. Because the string is non-empty, the result is `true`.

The implementation instead compares the normalized string with `"true"` when parsing a textual configuration flag. This keeps textual parsing separate from JavaScript's general truthiness rules.

## `null`

`null` represents an intentional absence of a value.

For example, a record can contain a `description` property whose value is intentionally empty. The property exists, but its application-level value is absent.

JavaScript has the historically surprising behavior:

`typeof null === "object"`

The implementation explicitly displays this behavior.

When property existence itself matters, checking the value is not sufficient. `Object.hasOwn()` distinguishes an existing property whose value is `null` from a property that does not exist.

## `undefined`

`undefined` is a separate primitive value.

It commonly appears when:

- a `var` binding has been hoisted but not assigned
- a function does not explicitly return a value
- an object property does not exist
- a variable has been declared without an initializer

The implementation demonstrates a missing object property producing `undefined` while a separate property explicitly containing `null` remains present.

This distinction is useful at data boundaries. A missing field and an explicitly empty field can carry different business meanings.

### Nullish coalescing

The `??` operator provides a concise fallback for `null` and `undefined`.

This differs from `||`, which also replaces valid falsy values such as `0`, `false`, and an empty string.

The JavaScript implementation compares `0 ?? 100` with `0 || 100` to demonstrate the distinction.

## Symbols

A `Symbol` is a unique primitive value.

Two expressions such as `Symbol("repositoryId")` produce different symbols even though they have the same description.

The description is metadata for humans and debugging. It is not the identity of the symbol.

Symbols are useful as object property keys when an application needs a key that should not accidentally collide with ordinary string-named properties.

The implementation stores symbol-keyed metadata on an object and compares:

- `Object.keys()`, which returns ordinary enumerable string keys
- `Reflect.ownKeys()`, which can include symbol keys

### Global symbol registry

`Symbol.for("name")` uses the global symbol registry.

Two calls with the same registry key return the same symbol, unlike independent calls to `Symbol("name")`.

`Symbol.keyFor()` can retrieve the registry key for a registry symbol.

This distinction is important when choosing between local unique identity and intentionally shared symbol identity.

## BigInt

`BigInt` represents arbitrary-precision integers.

The literal `9007199254740993n` is a BigInt literal. The trailing `n` distinguishes it from a `Number`.

BigInt is particularly useful when an application requires exact integer values beyond the safe range of `Number`.

BigInt arithmetic is a separate numeric domain. Expressions such as `10n + 1` throw a `TypeError` rather than silently converting between `BigInt` and `Number`.

Division also behaves differently from floating-point division. `7n / 2n` produces `3n` because the result must remain an integer.

### BigInt and JSON

`JSON.stringify()` does not directly serialize BigInt values.

The JavaScript implementation demonstrates this failure and then provides an explicit serialization policy that converts BigInt values to decimal strings.

That conversion is a protocol decision. Converting a large BigInt to `Number` would potentially lose integer precision, so a string representation is safer when exactness must survive a JSON boundary.

## Python Implementation

The Python program is an executable semantic model rather than an attempt to claim that Python and JavaScript have identical type systems.

`JavaScriptEnvironment` and `JavaScriptBinding` model declaration kinds and reassignment behavior for `var`, `let`, and `const`.

`UndefinedType` represents JavaScript's `undefined`, which Python does not have as an equivalent primitive.

`JavaScriptSymbol` provides unique symbol identities. Two objects with the same description still have different identities.

`JavaScriptBigInt` wraps Python's arbitrary-precision integer support so that the distinction between JavaScript `Number` and `BigInt` remains visible.

The `javascript_typeof()` function models the requested runtime categories, including the historically surprising `typeof null` result.

The configuration validation section applies the modeled values to a structured record. It distinguishes `null` from `undefined`, checks boolean and numeric fields explicitly, validates ranges, and ensures that large sequence values use the BigInt representation.

The self-check function makes the Python artifact executable as a small verification suite rather than only a collection of printed examples.

## JavaScript Implementation

The JavaScript file is the authoritative implementation of the requested language behavior because it executes actual ECMAScript operations.

The variable section demonstrates:

- function scope for `var`
- block scope for `let` and `const`
- reassignment of `let`
- non-reassignment of `const`
- object mutation through a `const` binding
- temporal dead zone behavior
- `var` hoisting

The string section works with repository and branch names and includes UTF-16 behavior and input validation.

The number section demonstrates floating-point representation, safe integers, `NaN`, infinity, integer parsing, and finite-number validation.

The `null` and `undefined` section uses object-property existence and nullish coalescing to show why the two values should not automatically be treated as interchangeable.

The symbol section demonstrates unique identity, symbol-keyed properties, `Reflect.ownKeys()`, and the global symbol registry.

The BigInt section demonstrates exact large integer arithmetic, type separation from Number, integer division, division-by-zero failure, and explicit JSON serialization.

The event-driven section uses Node.js `EventEmitter` to validate typed event payloads before processing them. A `Set` tracks BigInt sequence identifiers and prevents duplicate events.

## C++ Case Study

The C++ program approaches the same subject from a strongly typed systems perspective.

The scenario is a repository configuration and event service. Repository events contain:

- a repository string
- an exact large sequence number
- an approval boolean
- an optional description
- a symbolic event identifier

`std::variant` creates a closed set of explicitly typed value alternatives representing `undefined`, `null`, string, number, boolean, symbol, and BigInt.

`std::optional` represents an optional field whose absence is intentional. This is a typed C++ representation rather than a claim that `std::optional` and JavaScript `undefined` are identical.

The custom `Symbol` class assigns process-local identities, so two symbols with the same description remain distinct.

The custom `BigInt` class stores decimal integer data in base-1,000,000,000 chunks. It supports construction, addition, comparison, and exact decimal output. This is enough for the repository sequence-number case study without depending on an external arbitrary-precision library.

`RepositoryConfiguration` uses `const` members to make configuration immutable after construction. This is conceptually related to JavaScript `const` but is implemented through C++'s own type system and object model.

`RepositoryService` validates configuration and events before storing them. Invalid approval states, repository mismatches, invalid configuration ranges, and duplicate sequence identifiers are rejected through exceptions.

The event store separates validation from persistence and checks duplicate sequence numbers before insertion. This gives retries a deterministic failure path instead of silently creating duplicate events.

## Relationship Between the Implementations

The three files intentionally use different approaches.

| Area | Python | JavaScript | C++ |
| --- | --- | --- | --- |
| `var`, `let`, `const` | Explicit semantic model | Native ECMAScript behavior | C++ `const` and scope provide a contrasting model |
| Strings | Python string plus JavaScript-style wrapper behavior | Native JavaScript strings and UTF-16 | `std::string` |
| Numbers | Python float as an IEEE-754-oriented model | Native `Number` | `double` and fixed-width integer types |
| Booleans | Explicit modeled boolean | Native boolean | Native `bool` |
| `null` | `None` mapped to JavaScript `null` | Native `null` | `Null` variant alternative |
| `undefined` | Dedicated singleton object | Native `undefined` | `Undefined` variant alternative |
| Symbols | Explicit unique symbol class | Native `Symbol` | Identity-based `Symbol` class |
| BigInt | Wrapper around Python arbitrary-precision integers | Native `BigInt` | Custom arbitrary-length integer representation |
| Validation | Dictionary-based validation | Runtime type validation | Compile-time types plus runtime validation |
| Event processing | Configuration-oriented demonstration | Node.js event-driven processing | Repository event service |

The JavaScript implementation should be treated as the direct reference for JavaScript semantics. The Python and C++ implementations are deliberately designed to expose how other languages model similar engineering requirements differently.

## Common Mistakes

Using `var` when block scope is required can make a variable visible farther than intended.

Assuming `const` makes an object immutable is incorrect. `const` protects the binding from reassignment; it does not recursively freeze the referenced object.

Using `Boolean("false")` as a configuration parser is incorrect because any non-empty string is truthy.

Treating `null` and `undefined` as universally interchangeable can erase useful information about whether a field is intentionally empty or absent.

Using `typeof value === "object"` as a complete object validator is insufficient because `null` also produces `"object"` and arrays are objects as well.

Using `Number` for exact integers above `Number.MAX_SAFE_INTEGER` can silently lose precision.

Mixing `BigInt` and `Number` directly in arithmetic throws a `TypeError`.

Assuming a string's `.length` always equals its Unicode character count can produce incorrect limits for characters represented by multiple UTF-16 code units.

Serializing BigInt directly with `JSON.stringify()` fails. A deliberate wire-format representation is required.

## Validation and Boundary Design

The examples treat validation as a boundary concern rather than scattering implicit coercion throughout application logic.

A string field is checked as a string before string operations are performed.

A numeric field is checked for finite numeric status and an acceptable range.

A boolean field must actually be boolean rather than a string that happens to contain `"true"` or `"false"`.

An optional field is interpreted according to whether it is absent or intentionally empty.

A symbol field is required to have symbol identity rather than a descriptive string.

A BigInt sequence field remains a BigInt through arithmetic and is converted to a string only when crossing a JSON serialization boundary.

These rules reduce ambiguity at configuration, persistence, and event-processing boundaries.

## Performance Considerations

Primitive values are generally inexpensive to store and operate on, but their specific representation affects performance and correctness.

`Number` operations are efficient and broadly supported by JavaScript engines, but safe-integer limits must be respected when exact integer identity matters.

BigInt arithmetic requires arbitrary-precision work and is therefore not a drop-in replacement for Number in performance-sensitive floating-point calculations.

Symbol creation provides unique identity but should be used when identity semantics are actually useful rather than as a replacement for ordinary strings.

Repeated string normalization or parsing at high-throughput boundaries can create unnecessary allocations. Normalization rules should therefore be applied at defined input boundaries.

The C++ event store uses a collection for duplicate sequence tracking. Duplicate detection has a cost associated with converting the arbitrary-precision sequence into its canonical string representation, while the store itself keeps accepted events in insertion order.

## Security Considerations

Data type validation is part of application security because unexpected coercion can alter authorization, configuration, logging, and protocol behavior.

Textual booleans should not be interpreted through general truthiness when a security decision depends on the exact value.

Large identifiers should not be converted through floating-point Number when precision matters because distinct identifiers can collapse into the same numeric representation.

Strings used as identifiers, branch names, filenames, or command parameters should be validated against the grammar of their destination rather than merely checking that JavaScript considers them strings.

Symbol keys can reduce accidental property-name collisions, but they are not a security boundary. Symbol properties should not be treated as confidential merely because ordinary `Object.keys()` does not enumerate them.

BigInt values crossing JSON or other serialization boundaries need an explicit representation policy. Precision must not be sacrificed merely to fit a narrower numeric type.

## Debugging Considerations

When debugging a JavaScript value, `typeof` is useful for the broad primitive category but should not be treated as a complete type system.

The following cases deserve special attention:

- `typeof null` returns `"object"`
- arrays also return `"object"` from `typeof`
- `NaN` is a number even though it does not represent a valid numeric result
- `Number.isSafeInteger()` is necessary when integer precision matters
- `typeof 10n` is `"bigint"`
- symbols have identity independent of their descriptions
- missing object properties commonly evaluate to `undefined`

The examples intentionally print these edge cases so that runtime behavior can be observed rather than inferred from variable names.

## Production Considerations

Use `let` for bindings that genuinely need reassignment and `const` for bindings that should not be rebound. Reserve `var` for situations where its function-scoped and hoisting behavior is deliberately required.

Keep data validation close to external boundaries such as configuration loading, HTTP requests, message consumption, and database adapters.

Use `Number` for ordinary numeric calculations when its floating-point and safe-integer properties match the domain.

Use `BigInt` when exact integer arithmetic outside the Number safe-integer range is a real domain requirement, and define an explicit serialization strategy before values cross JSON boundaries.

Use `null` and `undefined` consistently within an application's data model. The important requirement is not that one value always replace the other, but that their meanings remain predictable.

Use symbols for identity-sensitive property keys rather than as a generic substitute for string identifiers.

Keep JavaScript's dynamic runtime behavior visible at integration boundaries while using explicit validation to prevent accidental coercion from becoming application logic.
