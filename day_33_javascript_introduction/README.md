# JavaScript Introduction

## Scope

This learning artifact introduces JavaScript as a programming language through four closely related areas: the JavaScript language itself, ECMAScript as its specification foundation, the execution environment in which JavaScript runs, and the syntactic distinction between statements and expressions.

The three implementations deliberately approach the subject from different directions.

The Python program builds a small executable model of JavaScript-like lexical analysis, expressions, statements, environments, and runtime behavior. Its purpose is to make the internal relationships between source text, tokens, bindings, evaluation, and execution visible.

The JavaScript program is the primary executable demonstration. It uses real JavaScript syntax and runtime behavior to demonstrate expressions, statements, declarations, scope, functions, objects, validation, errors, asynchronous execution, and host-environment detection.

The C++ program presents a developer-tool case study. It models a simplified source-processing pipeline with lexical tokens, a value system, lexical environments, expression evaluation, execution environments, and diagnostics. It demonstrates how software that analyzes a programming language can represent the concepts that JavaScript programmers encounter.

## JavaScript and ECMAScript

JavaScript is commonly described as an implementation of the ECMAScript language specification together with host-provided capabilities.

ECMAScript defines language-level behavior such as:

- lexical grammar and syntax
- primitive values and objects
- operators
- expressions
- statements
- functions
- control flow
- declarations and bindings
- lexical environments
- exceptions
- modules and other language facilities

An execution environment provides capabilities around that language.

A browser can provide objects and APIs associated with documents, user interaction, networking, storage, rendering, and browser events. Node.js provides a server-side runtime with capabilities associated with processes, files, networking, streams, and other operating-system-oriented operations.

This distinction matters because a JavaScript program is not defined solely by the APIs visible in one environment. A language feature such as an arithmetic expression belongs to JavaScript's language semantics, while an API such as `document` is supplied by a browser host.

The JavaScript implementation therefore detects whether values such as `window`, `document`, `process`, and `fetch` are available rather than assuming that every JavaScript runtime provides the same global objects.

## Source Text and Syntax

A JavaScript program begins as source text.

Consider the expression:

`price * quantity`

The source contains identifiers and an operator. When executed, the identifiers must resolve to values before the multiplication can produce a result.

A larger statement such as:

`const total = price * quantity;`

combines a declaration with an initializer expression. The declaration introduces the binding `total`, while `price * quantity` is evaluated to obtain its initial value.

The Python and C++ implementations include simplified lexical processing to expose this relationship. Their lexers recognize identifiers, keywords, numeric literals, string literals, operators, and punctuation. They are intentionally not complete JavaScript parsers. Full JavaScript syntax is considerably richer.

The important distinction is architectural: lexical structure is different from evaluation. A runtime cannot correctly evaluate arbitrary source by merely splitting it on spaces or punctuation.

## Expressions

An expression is a construct that evaluates to a value.

The JavaScript implementation demonstrates arithmetic expressions such as:

`unitPrice * quantity`

and grouped expressions such as:

`unitPrice * (quantity + 1)`

It also demonstrates logical expressions:

`quantity >= 3 && unitPrice > 100`

and string expressions:

`'Order-' + quantity`

Expressions can appear in many places. A variable initializer contains an expression, a function argument can be an expression, a condition can be an expression, and a return statement can contain an expression.

Expression evaluation can also depend on runtime state. The expression `quantity * unitPrice` cannot be evaluated correctly until the bindings for `quantity` and `unitPrice` have been resolved.

### Operators and operand types

JavaScript operators can depend on operand types.

The `+` operator illustrates this particularly clearly. With numeric operands, it performs numeric addition. When a string participates, string concatenation can occur.

The distinction between `===` and `==` is also demonstrated. Strict equality does not perform the same implicit conversions associated with loose equality. The JavaScript implementation deliberately prints both:

`10 === "10"`

and:

`10 == "10"`

This makes the runtime difference observable instead of presenting equality as a purely syntactic concept.

## Statements

Statements organize executable actions.

The JavaScript implementation demonstrates declaration statements, assignment operations, conditional statements, loop statements, and blocks.

For example:

`const price = 850;`

creates a binding.

An expression such as:

`price * quantity`

produces a value but does not by itself perform the same declaration operation.

A conditional statement:

`if (subtotal >= 2000) { ... } else { ... }`

uses an expression as its condition and then selects which statement block executes.

This relationship is central:

- expressions evaluate to values
- statements control execution or establish program actions
- expressions frequently occur inside statements

The distinction prevents a common beginner misconception that every line of JavaScript is simply an expression. JavaScript source contains several syntactic categories with different purposes.

## Declarations and Bindings

The JavaScript implementation demonstrates `const`, `let`, and `var`.

`const` creates a binding that cannot be reassigned after initialization. This does not mean that every object reachable through the binding becomes immutable. The example in the implementation modifies an object property while retaining the same `const` binding.

`let` creates a mutable lexical binding. The example changes `quantity` and `status` after their initial declarations.

`var` has historical function-scoping behavior rather than the block-scoping behavior associated with `let` and `const`. The JavaScript implementation deliberately places a `var` declaration inside a block and accesses it afterward to make that distinction observable.

Modern JavaScript code commonly favors `const` when rebinding is unnecessary and `let` when reassignment is required. The important technical issue is not stylistic preference alone. The declaration form affects binding behavior and scope.

## Lexical Scope

JavaScript uses lexical scoping for ordinary variable lookup.

The JavaScript example creates a nested block and a nested function. The nested code can access bindings from its surrounding lexical environment.

The C++ case study models this using an `Environment` class containing a pointer to a parent environment. A lookup first searches the current environment and then proceeds outward through parent environments.

This produces an important directional property:

An inner lexical environment can access an outer binding, but an outer environment cannot access a binding declared only inside the inner environment.

The Python implementation demonstrates the same relationship using an `Environment` object with a parent reference.

The JavaScript example also demonstrates a closure. `createRequestSummary` accesses `requestCount` from its surrounding scope. The function therefore retains access to the lexical environment in which it was created.

## Functions as Values

Functions are a major part of JavaScript's expression model.

The JavaScript implementation uses a function declaration for `calculateTotal` and an arrow-function expression for `formatCurrency`.

The calculator function validates its inputs before performing the calculation. This demonstrates that a function can combine:

- parameters
- validation
- local bindings
- expressions
- return behavior
- exceptions

Functions can also be assigned to variables and passed to other functions. The `map` example uses an arrow function as a callback, demonstrating that functions are first-class values.

This property becomes especially important in event-driven JavaScript because callbacks can be registered for future execution.

## Objects and Property Access

Objects provide structured data and property access.

The JavaScript example creates a repository object with properties such as `name`, `defaultBranch`, and `openIssues`, plus a nested `metadata` object.

The expression:

`repository.defaultBranch`

performs property access and produces a value.

Destructuring then extracts selected properties into local bindings.

These operations are expressions rather than independent declaration concepts. For example, the right-hand side of a declaration can contain property access:

`const branch = repository.defaultBranch;`

The binding is created by the declaration, while the property lookup supplies the value.

## Runtime Errors and Validation

Valid JavaScript syntax does not guarantee successful execution.

The JavaScript implementation distinguishes validation failures from successful execution by explicitly throwing errors when an input violates the expected contract.

`parseQuantity` rejects values that cannot represent a positive integer. The calling code catches the resulting `RangeError`.

Other runtime failures can arise from unresolved identifiers, invalid operations, or host API failures.

The Python model represents missing identifiers and invalid arithmetic as `JavaScriptRuntimeError` instances. The C++ case study uses exceptions to represent analogous failures at the boundaries of its simplified runtime.

Syntax and runtime failures should not be confused.

A syntax error prevents source from being successfully parsed according to the applicable grammar. A runtime error occurs while validly parsed code is executing.

## Asynchronous JavaScript

JavaScript execution is not limited to immediately evaluating one uninterrupted sequence of statements.

The JavaScript implementation demonstrates `setTimeout` and `Promise`/`async`/`await`.

The sequence around `setTimeout` shows that scheduling a callback does not execute the callback immediately. The current synchronous execution continues first, after which the host's scheduling machinery can invoke the callback.

The Promise example uses:

`async function demonstratePromises()`

and:

`await delayedValue(...)`

An `async` function returns a Promise. `await` allows asynchronous code to be expressed in a sequential-looking form while the surrounding JavaScript runtime remains capable of processing other work.

This is particularly relevant to JavaScript because many practical execution environments are event-driven and expose asynchronous host APIs.

## Execution Environments

The JavaScript implementation checks for environment capabilities rather than treating browser and Node.js execution as identical.

A browser commonly provides browser-specific objects such as:

`window`

and:

`document`

Node.js provides runtime capabilities such as:

`process`

The availability of `fetch` can also depend on the runtime version and environment.

The source language remains JavaScript, but the host environment changes what external capabilities the program can access.

This is why code that uses `document.querySelector(...)` is appropriate in a browser context but cannot automatically assume that a Node.js process has a DOM.

The C++ case study represents this distinction with `ExecutionEnvironment`. It models a browser and Node.js environment as different sets of host capabilities while leaving the core expression evaluator independent of those capabilities.

## Python Implementation

The Python file is an executable conceptual model rather than a JavaScript interpreter.

Its `JavaScriptLexer` converts a restricted JavaScript-like source representation into tokens. This demonstrates why lexical analysis is a separate stage from evaluation.

The `Environment` class models bindings and lexical lookup. It supports parent environments so that nested scopes can resolve names from outer scopes.

`ExpressionParser` implements recursive-descent parsing for a restricted expression grammar. It explicitly separates logical, equality, comparison, arithmetic, unary, and primary expressions. This makes operator precedence visible in executable code.

The `JavaScriptModel` then models a subset of statements, including declarations, assignments, `if`/`else`, `return`, blocks, and `console.log`.

The program also models two execution environments. The browser model exposes `window`, `document`, `fetch`, and `console`, while the Node.js model exposes `process`, `Buffer`, `fetch`, and `console`.

The implementation is deliberately smaller than ECMAScript itself. It does not attempt to reproduce the complete JavaScript grammar, object model, module system, standard library, asynchronous runtime, or engine internals.

Its educational value comes from making the relationship between source, tokens, expressions, statements, bindings, and execution environments executable.

## JavaScript Implementation

The JavaScript file uses actual JavaScript runtime semantics rather than simulating them.

Its early examples establish the distinction between expressions and statements through arithmetic, grouping, declarations, conditionals, and loops.

The scope examples demonstrate block scope and nested lexical environments. The closure example shows how a nested function can continue to access an outer binding.

The declaration section compares `const`, `let`, and `var`, including the important distinction between a `const` binding and object mutability.

The function section demonstrates validation, return values, arrow functions, callbacks, and array transformation.

The object section demonstrates property access and destructuring.

The error section shows how runtime validation can raise typed exceptions and how callers can handle known failure categories.

The asynchronous section demonstrates host scheduling with `setTimeout` and Promise-based asynchronous execution with `async`/`await`.

The program can be executed directly with Node.js, while its environment-detection logic also explains why JavaScript source can execute under different hosts.

## C++ Case Study

The C++ program represents a simplified developer tool that analyzes JavaScript source.

Its architecture separates several responsibilities.

The `Lexer` converts source text into tokens. It recognizes identifiers, keywords, numbers, strings, operators, punctuation, and the end of input.

The `Value` variant models a small set of runtime values: `undefined`, `null`, booleans, numbers, and strings. A real JavaScript runtime has a much richer value and object system, but the restricted representation is sufficient to demonstrate expression evaluation.

The `Environment` class models lexical bindings. It stores values and declaration kinds and can search parent environments. It also prevents reassignment of modeled `const` bindings.

The `ExpressionEvaluator` uses recursive-descent parsing. Its parsing layers correspond to precedence levels, allowing multiplication to bind more tightly than addition and allowing equality and logical operators to be handled at their appropriate stages.

The `ExecutionEnvironment` model separates language behavior from host capabilities. Browser and Node.js examples contain different capability sets.

The case study also includes failure handling for undefined identifiers, division by zero, and invalid constant reassignment.

The design illustrates why a production JavaScript engine cannot be reduced to a simple string evaluator. A full implementation requires comprehensive parsing, runtime objects, functions, lexical environments, coercion rules, exception semantics, garbage collection, module behavior, host integration, and many additional ECMAScript features.

## Common Technical Distinctions

| Concept | Meaning in this artifact | Concrete implementation |
| --- | --- | --- |
| ECMAScript | Specification foundation for the JavaScript language | Discussed in all three implementations; modeled independently from host APIs |
| Execution environment | Runtime host surrounding language execution | Browser and Node.js capability models |
| Syntax | Rules governing valid source structure | Lexer and parser examples |
| Token | Lexical unit extracted from source | Python `Token` and C++ `Token` |
| Expression | Construct evaluated to produce a value | Arithmetic, comparison, logical, and string expressions |
| Statement | Construct controlling execution or performing a program action | Declarations, conditionals, loops, blocks |
| Binding | Named association with a value in an environment | Python and C++ `Environment` models |
| Scope | Rules determining where bindings are accessible | Nested environments and JavaScript block/function examples |
| Runtime error | Failure occurring during execution | JavaScript exceptions, Python runtime errors, C++ exceptions |
| Host API | Capability supplied by the execution environment | Browser and Node.js examples |

## Edge Cases

String and numeric behavior requires attention because JavaScript permits operations whose results depend on operand types.

A `const` binding can prevent reassignment without making a referenced object immutable.

A variable can be syntactically valid but fail at runtime if the identifier is not available in the relevant lexical environment.

A syntactically valid program can also fail when an operation receives a value that violates the assumptions of the surrounding application.

Browser-specific global objects should not be assumed to exist in server-side JavaScript.

Asynchronous callbacks do not execute at the same point in source code where they are registered.

The simplified Python and C++ evaluators intentionally support only a restricted grammar. Treating their accepted syntax as complete JavaScript would be incorrect.

## Performance Considerations

Lexical scanning is naturally proportional to the amount of source text processed. The simplified Python and C++ lexers move through source from left to right and therefore operate approximately in O(n) time for source length n, excluding unusual implementation-level allocation behavior.

Expression parsing is proportional to the number of tokens processed for the supported grammar.

The C++ environment uses hash-based lookup for bindings. Individual lookup is average-case O(1), but lexical lookup may traverse several parent environments when a name is not present in the current scope.

Real JavaScript engines perform substantial optimization beyond this teaching implementation. They may parse source into internal representations, optimize frequently executed code, specialize operations, and use runtime strategies that are not represented here.

## Security and Reliability Considerations

Executing JavaScript source is fundamentally different from merely analyzing its text.

The Python and C++ programs do not execute arbitrary JavaScript. They process a deliberately constrained subset. This boundary prevents the examples from accidentally becoming general-purpose code execution engines.

A production system that accepts JavaScript source from an untrusted party must treat execution as a security boundary. Parsing source is not equivalent to safely executing it, and sandboxing requirements depend heavily on the runtime, host capabilities, permissions, and isolation architecture.

Input validation is demonstrated in the JavaScript calculation and quantity-processing examples because runtime correctness depends on explicit assumptions about values.

Errors should be handled at appropriate boundaries. Catching every exception without distinguishing syntax, validation, programming, and environmental failures can hide defects.

## Debugging Considerations

When debugging introductory JavaScript, separate the problem into language and environment questions.

If source cannot be parsed, inspect syntax and token structure.

If source parses but an identifier is unavailable, inspect lexical scope and declaration timing.

If an expression produces an unexpected value, inspect operand types and operator behavior.

If a browser-only API fails, inspect the execution environment rather than assuming that the language itself is missing a feature.

If asynchronous behavior appears out of order, inspect which work is synchronous and which work has been scheduled for later execution.

The three implementations support these debugging perspectives through progressively different levels of abstraction: Python models the mechanisms, JavaScript exposes real runtime behavior, and C++ models how a developer tool might represent those mechanisms.

## Practical Architectural Model

A useful mental model for the material is:

Source text → lexical structure → syntactic structure → evaluation → runtime state → observable behavior

The source contains characters.

Lexical analysis identifies meaningful units.

Parsing determines whether those units form valid language constructs and how they relate.

Expressions are evaluated to values.

Statements organize evaluation and execution.

Bindings connect identifiers to values through lexical environments.

The host execution environment supplies capabilities outside the core language.

Errors can arise at different stages, so diagnostics must preserve enough information to identify whether a failure concerns syntax, name resolution, value handling, or host behavior.

This model is reflected directly in the three implementations without requiring them to be identical. Each implementation emphasizes a different layer of the same technical subject.
