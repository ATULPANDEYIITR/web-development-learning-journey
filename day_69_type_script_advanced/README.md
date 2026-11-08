# TypeScript Advanced Concepts

## Technical Scope

This project examines advanced type-system mechanisms through five complementary implementations.

The central TypeScript concepts are:

1. Generics
2. Utility types
3. Type narrowing
4. Type guards
5. Conditional types

The implementations use Python, JavaScript, C++17, Java 17, and PostgreSQL to demonstrate related concepts through their respective type systems and runtime mechanisms.

These languages do not implement TypeScript's type system identically. Their implementations are comparative engineering models, not interchangeable TypeScript compilers.

## 1. Generics

Generics allow functions, classes, interfaces, and other type constructs to operate on multiple data types while preserving relationships between inputs and outputs.

A generic repository can store users, products, invoices, or other entities without requiring a separate repository implementation for every entity type.

### Generic function

A generic identity function preserves the type of its argument.

Conceptually:

- Input: T
- Output: T
- Type relationship: output retains the input type.

This differs from using an unrestricted object or any type, where important type information may be lost.

### Generic classes

The repository implementations demonstrate:

- Type-parameterized storage.
- Key-based retrieval.
- Duplicate-key detection.
- Record deletion.
- Collection retrieval.
- Missing-record handling.

The Python implementation uses `Generic[T]` and `TypeVar`.

The JavaScript implementation uses JSDoc generic annotations and a `Map`.

The C++ implementation uses class templates.

The Java implementation uses parameterized classes and bounded type parameters.

The PostgreSQL implementation uses JSONB payloads with explicit discriminators and validation functions.

### Bounded generics

A bounded generic restricts acceptable types.

For example, a generic maximum function requires values that support comparison.

Java expresses this through `T extends Comparable<T>`.

C++ can enforce related restrictions through type traits and compile-time assertions.

Python can express comparable behavior through protocols or bounded type variables.

These restrictions improve correctness by rejecting unsupported operations.

## 2. Utility Types

TypeScript utility types transform existing types into new types without repeatedly defining their structures.

The principal utility types covered are:

| Utility type | Purpose |
|---|---|
| `Partial<T>` | Makes properties optional |
| `Required<T>` | Makes properties mandatory |
| `Readonly<T>` | Prevents property reassignment |
| `Pick<T, K>` | Selects specified properties |
| `Omit<T, K>` | Excludes specified properties |
| `Record<K, T>` | Defines an object using specified keys and value types |
| `NonNullable<T>` | Excludes null and undefined |
| `ReturnType<T>` | Extracts a function's return type |
| `Parameters<T>` | Extracts a function's parameter types |
| `Awaited<T>` | Resolves nested promise-like types |

### Partial

`Partial<T>` is useful when updating an existing record.

A user profile might contain:

- Name
- Email
- Department
- Phone

An update request may change only the department.

The implementation applies the supplied changes while retaining existing values for unspecified properties.

The Python implementation uses `TypedDict(total=False)`.

The JavaScript implementation uses object spread.

The Java implementation uses `Optional` fields in an immutable record.

The C++ implementation uses optional members in a patch structure.

The SQL implementation uses a JSONB update procedure that validates allowed properties and locks the target record.

### Pick and Omit

`Pick<T, K>` selects a subset of properties.

For example, an API response may expose a user's name and email while excluding internal fields.

`Omit<T, K>` creates the opposite projection by excluding specified properties.

These operations are useful for:

- API response design.
- Data transfer objects.
- Sensitive-field filtering.
- Database projections.
- Service boundaries.

The implementations demonstrate corresponding runtime transformations.

### Readonly

`Readonly<T>` prevents reassignment of properties through TypeScript's type system.

The JavaScript implementation uses `Object.freeze()` for shallow runtime protection.

Java uses immutable collections and records.

C++ uses const references.

Python uses frozen dataclasses for immutable record models.

A shallow immutable object does not automatically make nested objects immutable. Production systems must consider deep immutability where required.

### Record

`Record<K, T>` represents a mapping from a specified key type to a value type.

A useful application is a registry of users indexed by their unique identifiers.

The Python implementation uses dictionaries, JavaScript uses objects, and Java uses maps.

## 3. Type Narrowing

Type narrowing reduces a broad type into a more specific type after a condition has been evaluated.

For example, a function may accept:

`string | number | null`

The implementation must distinguish these possibilities before performing operations specific to one type.

### Common narrowing mechanisms

| Mechanism | Purpose |
|---|---|
| `typeof` | Checks primitive types |
| `instanceof` | Checks class instances |
| Equality checks | Removes incompatible union members |
| `in` | Checks property presence |
| Truthiness checks | Filters certain nullish or falsy values |
| Discriminant properties | Identifies union variants |
| Control-flow analysis | Tracks type changes through branches |

### Control-flow analysis

TypeScript tracks the conditions and assignments that affect a variable's possible types.

For example:

1. A parameter initially has multiple possible types.
2. A conditional statement checks its runtime type.
3. The compiler narrows the type inside the corresponding branch.
4. Operations valid for the narrowed type become available.

This improves type safety without requiring repeated type assertions.

### Discriminated unions

A discriminated union uses a shared property to distinguish related object variants.

The implementations use operation results with distinct states:

- SUCCESS
- FAILURE
- PENDING

A successful result contains result data.

A failed result contains an error message and error code.

A pending result contains neither completed result data nor failure information.

The PostgreSQL implementation enforces these combinations with a `CHECK` constraint.

The JavaScript implementation uses a `kind` property.

Java uses a sealed interface with records.

C++ uses `std::variant`.

Python uses separate dataclasses and union types.

The key design principle is that invalid combinations should not be representable or should be rejected during validation.

## 4. Type Guards

Type guards provide evidence that an unknown value satisfies a particular structure.

They are particularly important when data enters an application from an external source.

Examples include:

- HTTP API responses.
- JSON files.
- User-submitted forms.
- External service integrations.
- Message queues.
- Database JSON fields.

### Built-in type guards

TypeScript provides several mechanisms for narrowing values.

Examples include:

- `typeof`
- `instanceof`
- `in`
- Equality comparisons
- Discriminant checks

### Custom type guards

A custom TypeScript type guard uses a predicate return type.

Its general structure is:

`function isUser(value: unknown): value is User`

The return value indicates whether the supplied value satisfies the required structure.

A custom guard should verify more than property existence.

A robust validation routine should consider:

- Correct property types.
- Required properties.
- Valid identifiers.
- Non-empty strings.
- Email format.
- Numeric boundaries.
- Unexpected properties where strict schemas are required.

The JavaScript implementation uses a JSDoc predicate for static tooling and a runtime validator.

Python uses `TypeGuard`.

The SQL implementation uses immutable validation functions over JSONB values.

C++ and Java use explicit validation functions.

### Unknown versus any

`unknown` is safer than `any` when processing untrusted data.

An `unknown` value must be checked before operations requiring a specific type.

An `any` value bypasses normal compile-time restrictions.

For external data, prefer `unknown` followed by validation.

## 5. Conditional Types

Conditional types select one type or another depending on a type relationship.

Their general TypeScript structure is:

`T extends U ? X : Y`

This evaluates whether a type satisfies a specified constraint.

### Example: type-dependent output

A conditional type can express:

- String input produces a string output.
- Numeric input produces a numeric output.
- Unsupported types produce a restricted result.

The JavaScript implementation demonstrates the corresponding runtime dispatch.

The Python implementation uses overloads.

The C++ implementation uses `std::conditional_t` and `if constexpr`.

The Java implementation uses explicit runtime pattern matching through `instanceof`.

The PostgreSQL implementation uses JSONB type inspection and conditional processing.

These are functional analogues. Runtime branching does not replace TypeScript's compile-time conditional-type evaluation.

### Distributive conditional types

A conditional type distributes over union members when its checked type is a naked type parameter.

For example, a transformation applied to `string | number` can be evaluated separately for each member.

Wrapping the checked type in a tuple changes this behavior.

This distinction matters when building reusable type transformations.

### Infer

The `infer` keyword extracts a type from another type structure.

Common applications include:

- Extracting function return types.
- Extracting parameter types.
- Resolving promise results.
- Extracting array element types.
- Deconstructing nested generic structures.

`ReturnType<T>` and `Awaited<T>` are examples of utility types that use advanced type relationships.

## 6. Language Implementation Comparison

| Concept | Python | JavaScript | C++17 | Java 17 |
|---|---|---|---|---|
| Generics | `Generic`, `TypeVar` | JSDoc annotations | Templates | Generic classes |
| Bounds | Bounded type variables | Runtime checks | Type traits | `extends` |
| Partial | Optional `TypedDict` | Object spread | `optional` | Optional record fields |
| Pick | Dictionary projection | Object projection | Field selection | Map projection |
| Omit | Dictionary filtering | Object filtering | Field selection | Map filtering |
| Readonly | Frozen dataclass | `Object.freeze` | `const` | Immutable records |
| Narrowing | `isinstance` | `typeof`, `instanceof` | `variant` | `instanceof` |
| Type guards | `TypeGuard` | Predicate functions | Validation functions | Predicate functions |
| Conditional types | Overloads | Runtime dispatch | `conditional_t` | Runtime dispatch |

PostgreSQL provides a separate data-integrity perspective through constraints, JSONB validation, triggers, functions, and transactions.

## 7. PostgreSQL Implementation

The SQL implementation models typed data as relational records and validated JSONB payloads.

### Main tables

| Table | Responsibility |
|---|---|
| `users` | Stores validated user records |
| `products` | Stores product records |
| `typed_payloads` | Stores discriminator-based payloads |
| `operation_results` | Stores success, failure, and pending states |
| `entity_registry` | Stores generic entity references and attributes |

### Validation mechanisms

The database uses:

- Primary keys.
- Unique constraints.
- Check constraints.
- Enumerated types.
- JSONB type inspection.
- Regular expressions.
- Validation functions.
- Triggers.
- Transactions.

The payload trigger ensures that a USER payload satisfies user-specific validation rules, while PRODUCT and INVOICE payloads use their own validation conditions.

This provides database-level protection against malformed records submitted by different application clients.

### Partial updates

The `update_user_partial` procedure:

1. Validates the JSON object.
2. Rejects unsupported properties.
3. Locks the target user row.
4. Retains unspecified values.
5. Validates the resulting user data.
6. Applies the update.

This prevents a partial update from unintentionally replacing unrelated fields.

### Performance

Indexes support common access patterns:

- Payload discriminator lookups.
- JSONB searches.
- User status and department filtering.
- Product availability and price filtering.
- Recent operation retrieval.

Indexes improve selected queries but increase storage requirements and write overhead.

## 8. Execution

### Python

Run:

`python typescript_advanced.py`

The implementation uses standard-library modules only.

### JavaScript

Run:

`node typescript_advanced.js`

The implementation uses built-in JavaScript and Node.js capabilities.

### C++17

Compile:

`g++ -std=c++17 -O2 -Wall -Wextra -pedantic advanced.cpp -o advanced`

Run:

`./advanced`

On Windows:

`advanced.exe`

### Java 17

Compile:

`javac TypeScriptAdvanced.java`

Run:

`java TypeScriptAdvanced`

Assertions are enabled with:

`java -ea TypeScriptAdvanced`

### PostgreSQL

Execute the SQL file against a PostgreSQL 14 or newer database.

The script creates the `advanced_types` schema, tables, functions, procedures, triggers, indexes, views, and sample records.

The script uses a transaction for the schema and data setup.

## 9. Validation and Failure Handling

The implementations deliberately include invalid-input handling.

| Failure condition | Expected behavior |
|---|---|
| Duplicate repository key | Reject insertion |
| Empty collection | Return no first element or reject maximum calculation |
| Invalid user ID | Reject construction |
| Invalid email | Reject validation |
| Negative product price | Reject construction or insertion |
| Unsupported update property | Reject partial update |
| Invalid union variant | Reject processing |
| Unexpected JSON structure | Reject parsing or validation |
| Missing repository record | Return an explicit missing value |
| Invalid numeric input | Reject normalization |
| Database constraint violation | Abort the affected statement |

Assertions verify important successful and unsuccessful cases.

Assertions are suitable for development testing. Production applications should use dedicated test frameworks and structured error handling.

## 10. Security and Production Considerations

Advanced typing contributes to safer application boundaries, but static types alone do not validate untrusted runtime data.

Important controls include:

- Validate external input at application boundaries.
- Avoid unrestricted `any`.
- Prefer `unknown` for untrusted TypeScript values.
- Reject unexpected object properties where strict schemas are required.
- Avoid exposing credentials and internal attributes in API projections.
- Use parameterized SQL queries.
- Enforce database constraints independently of application validation.
- Use immutable data structures for sensitive state transitions.
- Avoid assuming shallow readonly protection provides deep immutability.
- Apply authorization checks independently of type validation.
- Limit JSON payload size.
- Handle malformed input without exposing internal stack traces.

TypeScript types are normally erased during compilation. Runtime validation remains necessary when data originates outside the application.

## 11. Important Technical Distinctions

| Mechanism | Main responsibility |
|---|---|
| Generic | Reuses logic while preserving type relationships |
| Utility type | Transforms an existing type |
| Narrowing | Reduces possible types through control flow |
| Type guard | Provides a validated type predicate |
| Conditional type | Selects a type based on a compile-time relationship |
| Runtime validation | Checks actual data values |
| Database constraint | Enforces persistent data integrity |

These mechanisms solve different problems.

A generic does not automatically validate external input.

A utility type does not create runtime validation.

A type guard does not automatically enforce database integrity.

A conditional type does not perform runtime branching.

A database constraint does not replace application-level authorization.

The most reliable architecture uses these mechanisms at their appropriate boundaries.
