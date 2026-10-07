# Functions: Declarations, Expressions, Arrow Functions, Parameters, Return Values, and Scope

## Topic Scope

This learning artifact focuses on functions as reusable units of behavior and on the mechanisms that determine how functions receive input, produce output, access variables, and participate in larger programs.

The central concepts are:

- function declarations
- function expressions
- arrow functions and equivalent function-value patterns
- required and optional parameters
- default parameter values
- return values
- functions passed as arguments
- functions returned from other functions
- callbacks and higher-order functions
- local, enclosing, and outer scope
- closures
- validation and failure handling
- function composition and pipelines
- object methods
- recursive and iterative function design
- database functions and set-returning functions

The six implementations deliberately use different approaches. Python emphasizes first-class functions, closures, callable typing, and practical data processing. JavaScript emphasizes function values, arrow functions, lexical behavior, callbacks, and asynchronous return values. C++ focuses on function objects, `std::function`, lambdas, captures, composition, and explicit resource-safe design. Java models functions through methods, functional interfaces, lambdas, method references, records, and enterprise-style services. PostgreSQL demonstrates typed database functions, default parameters, set-returning functions, volatility, validation, and transactional execution.

## Core Function Model

A function establishes a contract between its caller and its implementation.

A useful abstract model is:

`input parameters -> function body -> return value`

Parameters define the data that a caller may or must provide. The return value defines the result exposed to the caller. A function can also fail instead of returning normally, typically through an exception in Python, JavaScript, C++, and Java or an exception raised by a PostgreSQL function.

A good function has a clear responsibility. The examples avoid functions whose only purpose is to demonstrate syntax. Each function performs a concrete operation such as calculating a total, validating a value, transforming a number, calculating payroll, composing operations, or summarizing data.

## Function Declarations

Python, C++, and Java demonstrate named functions or methods using declarations that give the callable a stable name.

Python uses:

`def calculate_total(price: float, quantity: int = 1) -> float:`

C++ uses:

`double calculateTotal(double price, int quantity = 1)`

Java uses methods such as:

`static double calculateTotal(double price, int quantity)`

The important property is that the caller can invoke a named operation without knowing its internal implementation.

A declaration is useful when an operation has a meaningful domain name and may be called from several places. The name becomes part of the interface between different parts of the program.

## Function Expressions

JavaScript makes the distinction especially visible because a function expression can be assigned directly to a variable:

`const calculateDiscount = function (amount, rate) { ... };`

The function itself becomes a value stored in `calculateDiscount`.

This is different from treating a function only as a named block of code. Because functions are values, they can be stored in arrays, maps, object properties, passed to other functions, or returned from functions.

Python, C++, and Java support the same broad idea through first-class callable values, function objects, lambdas, and functional interfaces, although the syntax and type systems differ.

## Arrow Functions and Lambdas

JavaScript arrow functions provide concise function expressions:

`const square = (number) => number * number;`

They are particularly useful for callbacks and short transformations.

The Java implementation uses lambdas such as:

`value -> value * 3`

C++ uses lambdas such as:

`[factor](double value) { return value * factor; }`

Python uses lambda expressions where a short anonymous operation is appropriate:

`lambda value: value * 2`

These constructs are not merely shorter versions of named functions. Their language-specific semantics matter.

JavaScript arrow functions do not create their own `this`, which makes them useful for callbacks where lexical `this` behavior is desirable.

C++ lambdas can explicitly capture local variables by value or reference. The C++ example captures `factor` by value so that the returned callable owns the value it needs.

Java lambdas implement functional interfaces such as `DoubleFunction<Double>` and `DoublePredicate`.

Python functions and lambdas are objects and can be stored directly in variables, dictionaries, lists, and other data structures.

## Parameters

Parameters define the data accepted by a function.

The Python and JavaScript examples demonstrate default parameter values. A call such as `calculateTotal(100)` uses the default quantity of `1`.

C++ also supports default arguments:

`double calculateTotal(double price, int quantity = 1)`

Java does not have default method parameters. The Java implementation therefore uses method overloading:

`calculateTotal(double price)`

delegates to:

`calculateTotal(double price, int quantity)`

This distinction is important because similar business behavior can be implemented through different language mechanisms.

Parameters should be validated when invalid input would violate the function's contract. The examples reject negative prices, invalid tax rates, negative quantities, empty names, and invalid numeric ranges.

## Return Values

A return statement transfers a value from the function back to its caller.

For example, the Python implementation returns:

`return price * quantity`

The caller can immediately use that result in another calculation.

Functions can return simple values, collections, objects, records, or even other functions. The examples deliberately demonstrate this progression.

`make_multiplier(3)` returns a function that multiplies future inputs by three.

The JavaScript equivalent uses a closure returned from `makeMultiplier`.

The C++ implementation returns `std::function<double(double)>`.

The Java implementation returns `Function<Double, Double>`.

This pattern is useful when behavior must be configured once and applied many times.

## Functions as Arguments

A higher-order function accepts another function as an argument.

Python's `apply_operation` accepts a `Callable`.

JavaScript's `applyOperation` checks that the supplied value is a function before invoking it.

C++ uses `std::function<double(double)>`.

Java uses `DoubleFunction<Double>`.

This design separates the operation being performed from the mechanism that invokes it.

For example, a data-processing function can accept `square`, `absolute`, or a custom transformation without implementing each transformation separately.

This is the basis of many callback and functional programming patterns.

## Functions Returning Functions

A function can construct behavior dynamically.

The multiplier examples demonstrate this pattern:

`make_multiplier(3)` produces a function equivalent to a configured multiplication-by-three operation.

The returned function retains access to the factor that existed when the factory function executed.

That retained relationship is a closure.

Closures are useful for configurable validation, transformation, authorization, filtering, formatting, and other behaviors where configuration should remain private to the generated function.

## Scope

Scope determines which variables are accessible at a particular location.

The Python example demonstrates module-level, enclosing, and local values.

The JavaScript example demonstrates lexical scope, where an inner function can access variables declared in an enclosing function.

Java demonstrates a similar relationship through local variables captured by lambdas and through a nested class accessing an enclosing method's effectively final variable.

C++ makes capture explicit. A lambda can capture a variable by value or reference, and that decision affects lifetime and behavior.

Scope is important because a function should not depend on hidden mutable state unless that dependency is deliberate.

## Closures

A closure is a function together with access to variables from its surrounding lexical environment.

The counter implementations show a practical use.

In Python, `counter_factory()` creates `count` and returns `next_count`. The inner function uses `nonlocal count` to update the retained state.

In JavaScript, the returned arrow function retains access to `count`.

In C++, a lambda can capture state explicitly.

In Java, lambdas can capture local variables when those variables are final or effectively final. Mutable state can instead be represented through an object when the design requires it.

Closures are powerful but should be used deliberately. Capturing large objects or long-lived resources can extend their lifetime and increase memory usage.

## Function Composition

Composition connects the output of one function to the input of another.

The implementations define a `compose` operation representing:

`second(first(value))`

For example:

`addTen -> multiplyTwo`

means that an input of `5` first becomes `15` and then becomes `30`.

Composition allows small functions to be combined into larger transformations without embedding all logic in one large function.

The pipeline examples extend the idea by applying a sequence of functions to a value.

## Validation and Failure Handling

Functions define contracts, so invalid arguments should not silently produce misleading results.

The implementations validate conditions such as:

- negative monetary values
- negative quantities
- invalid percentage ranges
- division by zero
- empty collections
- non-finite numeric values
- missing callable values
- invalid payroll tax rates
- invalid range boundaries

Python raises `ValueError`, `TypeError`, or `ZeroDivisionError`.

JavaScript uses `TypeError` and `RangeError`.

C++ uses standard exceptions such as `std::invalid_argument` and `std::domain_error`.

Java uses `IllegalArgumentException` and `ArithmeticException`.

PostgreSQL uses `RAISE EXCEPTION` inside PL/pgSQL functions.

The exact mechanism differs, but the design principle is the same: invalid input should be handled explicitly at a boundary where the violated contract is understood.

## Python Implementation

The Python program starts with ordinary named functions and progresses to callable values, lambda expressions, closures, stateful counters, data processing, object methods, composition, pipelines, recursion, and generated validators.

`apply_operation` demonstrates a function accepting another function through `Callable`.

`make_multiplier` demonstrates a closure that retains `factor`.

`counter_factory` demonstrates persistent function-local state using `nonlocal`.

`compose` and `execute_pipeline` show how functions can become reusable transformation components.

`PayrollService` demonstrates that methods are also callable behavior associated with an object.

The script also contrasts recursive and iterative factorial implementations. The recursive implementation is useful for understanding recursive function calls, while the iterative implementation avoids additional call-stack growth.

## JavaScript Implementation

The JavaScript implementation emphasizes the language's treatment of functions as values.

It includes a traditional function declaration, a function expression, arrow functions, default parameters, callbacks, a `Map` containing functions, closures, function composition, pipelines, class methods, and an asynchronous function returning a `Promise`.

The asynchronous example demonstrates an important distinction: an asynchronous function can return a promise representing a future result rather than returning the final value synchronously.

The file also validates callback arguments before invoking them. This prevents confusing failures where a non-callable value is treated as a function.

## C++ Case Study

The C++ program demonstrates function behavior using a strongly typed function-object model.

`std::function<double(double)>` provides a common callable interface that can store ordinary functions, lambdas, and other compatible callable objects.

`makeMultiplier` returns a lambda with an explicit value capture. The captured `factor` is stored with the callable, so it remains available after the factory function returns.

`compose` stores two callable objects inside another callable. This demonstrates how higher-order behavior can be implemented while retaining static typing.

`executePipeline` applies a sequence of functions to a value. The vector of `std::function` objects provides a runtime-configurable sequence of operations.

The program also includes a `PayrollService` class to demonstrate the distinction between free functions, callable objects, and member functions.

The implementation uses exceptions for invalid function arguments and division failures. Numeric inputs are checked with `std::isfinite`, preventing non-finite values from silently entering calculations.

## Java Implementation

The Java program uses the standard functional interfaces from `java.util.function`.

`DoubleFunction<Double>` represents a function that accepts a primitive `double` and returns a `Double`.

`DoublePredicate` represents a boolean test over a numeric value.

`Function<Double, Double>` is used when the example needs a general function object that can be composed or returned from another method.

Method references such as `FunctionsDemo::square` connect an existing named method to a functional interface without creating a separate wrapper method.

The `PayrollService` demonstrates enterprise-oriented encapsulation. Validation is performed when domain objects and services are created, while calculations remain in methods with clearly defined responsibilities.

The `Employee` record provides immutable domain data. Its compact constructor validates the employee name and salary at construction time.

## SQL Implementation

The PostgreSQL script demonstrates functions as database-level reusable operations.

`calculate_total` accepts typed parameters and defines a default value for quantity.

`calculate_discount` validates a percentage before performing the calculation.

`net_salary` shows a function combining several parameters into a domain calculation.

`employees_above_salary` is a set-returning function. Instead of returning one scalar value, it exposes a relational result that can be queried like a table.

`valid_salary` is marked `IMMUTABLE` because its result depends only on its input parameter. `employees_above_salary` is marked `STABLE` because it reads database state but does not modify it.

The script also demonstrates a transaction in which a temporary employee is inserted, queried through a function, and then removed with `ROLLBACK`.

The database examples show that functions are not limited to application programming languages. A database function can enforce business behavior close to the data and can be combined with joins, common table expressions, filtering, and aggregation.

## Recursion and Iteration

A recursive function invokes itself with a smaller problem.

The factorial example has a base case for `0` and `1`. Without a base case, recursive execution would continue until the runtime's recursion or stack limit was reached.

The iterative version stores intermediate state in a loop rather than creating a new function call for every step.

Recursion can provide a direct representation of naturally recursive structures, but it can also increase stack usage. Iteration is often preferable when the problem does not benefit from recursive structure.

## Performance Considerations

Function calls have some execution overhead, although the practical cost depends strongly on language, compiler, runtime, optimization level, and workload.

Passing functions as values can introduce additional indirection. In C++, templates and inlineable callable objects may allow more aggressive compile-time optimization than type-erased `std::function` in performance-sensitive paths.

JavaScript function allocation and closures can affect memory behavior when large numbers of short-lived functions are created.

Python function calls have relatively high interpreter overhead compared with low-level compiled operations, so excessive tiny function calls inside very large numerical loops can matter.

Java functional abstractions are optimized by the runtime in many ordinary workloads, but allocation and boxing can matter when using generic types such as `Function<Double, Double>` instead of primitive-specialized interfaces.

PostgreSQL functions can improve reuse and encapsulation, but a function invoked for every row of a very large query may affect execution cost. Query plans, function volatility, data volume, and whether computation can be performed set-wise all matter.

## Security Considerations

Function parameters should be treated as untrusted input at system boundaries.

The application-language examples validate numeric ranges and reject invalid values before performing calculations.

Database functions should use parameters rather than constructing SQL statements by concatenating untrusted strings. Parameterized function arguments do not automatically make dynamic SQL safe, but they provide the correct foundation for avoiding SQL injection when used normally.

Functions that perform privileged database operations require particular care around ownership, execution privileges, and `SECURITY DEFINER` behavior. The example does not use elevated execution privileges, avoiding unnecessary privilege expansion.

Closures and callbacks should also be treated as executable behavior. A design that accepts arbitrary functions should only do so when the caller is trusted or when the available operations are explicitly constrained.

## Common Function Design Errors

A function with too many unrelated responsibilities becomes difficult to test and reason about. The examples instead keep calculations, validation, composition, and orchestration separate.

Ignoring invalid parameters creates hidden assumptions. The implementations validate inputs at the function boundary where the contract is established.

Using mutable shared state can make repeated calls depend on execution order. The counter examples intentionally preserve state through a closure so that the behavior is explicit rather than accidental.

Capturing variables without considering their lifetime can produce subtle bugs. C++ requires particular attention to reference captures because a captured reference can become invalid if the referenced object no longer exists.

Using an arrow function in JavaScript when dynamic `this` behavior is required can be incorrect because arrow functions use lexical `this`.

Assuming Java supports default parameters like Python or C++ is also incorrect. Java method overloading is used instead.

## Relationship Between the Concepts

A function declaration gives behavior a stable name.

A function expression treats behavior as a value.

An arrow function or lambda provides a compact way to construct a function value.

Parameters define what information enters the function.

A return value defines what information leaves it.

Scope determines which variables the function can access.

A closure extends that access relationship beyond the execution of the enclosing function.

Higher-order functions use these properties to accept or return other functions.

Composition uses higher-order functions to build larger behavior from smaller operations.

Validation defines what inputs are acceptable before the function performs its main operation.

These mechanisms form a connected design model rather than isolated syntax features.
