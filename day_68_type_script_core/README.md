# TypeScript Core: Arrays, Objects, Tuples, Enums, Unions, Intersections and Aliases

## 1. Technical Scope

This module examines the core TypeScript type system through six connected concepts:

- Arrays
- Objects
- Tuples
- Enums
- Union types
- Intersection types
- Type aliases

The implementations use Python, JavaScript, C++17, Java 17 and PostgreSQL to demonstrate corresponding data structures, validation mechanisms, domain models and operational behavior.

TypeScript is a statically checked superset of JavaScript. Its type system describes the permitted structure and operations of values. Type annotations and interfaces are primarily compile-time constructs. They do not automatically provide runtime validation.

The central distinction is between describing a data contract and enforcing that contract when an application executes.

## 2. Arrays

An array stores an ordered collection of values. TypeScript supports arrays whose elements share a specified type.

The notation `number[]` represents an array of numbers. The equivalent generic notation is `Array<number>`.

For example, an assessment system can maintain:

- Individual assessment scores.
- Project identifiers.
- User tags.
- Permission assignments.
- Collections of API response records.

Typical operations include:

| Operation | TypeScript mechanism | Purpose |
|---|---|---|
| Add an element | `push()` | Append an element |
| Remove an element | `pop()` | Remove the final element |
| Transform | `map()` | Produce a transformed array |
| Filter | `filter()` | Select matching elements |
| Search | `find()` | Retrieve the first matching element |
| Aggregate | `reduce()` | Calculate a combined result |
| Sort | `sort()` | Arrange elements |
| Check | `every()` | Validate all elements |
| Search membership | `includes()` | Check element existence |

The implementations calculate minimum, maximum and average assessment scores, identify passing scores and remove duplicate values.

Array validation should consider:

- Empty collections.
- Incorrect element types.
- Invalid numerical ranges.
- Duplicate values where uniqueness is required.
- Unexpected null or undefined values.
- Excessively large collections.

JavaScript arrays are mutable. Copying an array before sorting or transforming it avoids unintended modification of the original collection.

For large datasets, repeated sorting and unnecessary copying can increase memory consumption and execution time.

## 3. Objects

An object represents a collection of named properties.

A TypeScript object type describes the expected property names and their associated types.

For example, a user profile can contain:

| Property | Type | Constraint |
|---|---|---|
| `displayName` | `string` | Must not be empty |
| `email` | `string` | Must have a valid format |
| `location` | `string` | Must not be empty |

An application-level user object combines the profile with a user identifier, role, account status and tags.

The implementations represent objects differently:

- Python uses dataclasses.
- JavaScript uses classes and validated object construction.
- C++17 uses structures.
- Java 17 uses immutable records.
- PostgreSQL uses relational tables and composite types.

Objects support structured data exchange, domain modeling, API payloads and application state.

A useful design separates the identity of an entity from its descriptive attributes.

For example, `UserId` identifies a user, while `Profile` stores descriptive information.

This separation makes validation, updates and persistence more manageable.

### Object validation

A TypeScript object declaration does not guarantee that external JSON data satisfies the declared structure.

Data received from an HTTP request, file or database must be validated before use.

Relevant checks include:

- Required properties.
- Correct property types.
- Missing properties.
- Unexpected properties.
- Valid email formats.
- Valid identifiers.
- Nested object validity.

The JavaScript implementation demonstrates explicit runtime validation before constructing domain objects.

## 4. Tuples

A tuple is an ordered collection with a fixed structure and potentially different types at different positions.

For example:

`[number, string, UserRole]`

represents a three-element tuple containing:

1. A numeric identifier.
2. A string name.
3. A user role.

A coordinate tuple can represent latitude and longitude.

Tuples are useful when the position of each value has a defined meaning.

They differ from ordinary arrays because their positions have specific type contracts.

| Property | Array | Tuple |
|---|---|---|
| Element types | Usually homogeneous | Can be heterogeneous |
| Length | Generally variable | Defined by its type |
| Position meaning | Usually collection-based | Position-specific |
| Example | `number[]` | `[number, string]` |

The TypeScript syntax can also express optional and rest elements in tuple definitions.

For example, an optional third element can be represented using `?`.

The Python implementation uses typed tuples, C++17 uses `std::pair` and `std::tuple`, and Java 17 uses records.

Java does not provide native tuple syntax. Records provide an alternative with named components and explicit structure.

PostgreSQL uses a composite type to represent a coordinate pair.

Tuple validation should enforce both element types and position-specific constraints.

## 5. Enums

An enum defines a finite set of named values.

The application uses three separate enums.

### UserRole

- `ADMIN`
- `DEVELOPER`
- `ANALYST`
- `VIEWER`

### AccountStatus

- `ACTIVE`
- `SUSPENDED`
- `PENDING`

### ProjectStatus

- `PLANNED`
- `IN_PROGRESS`
- `COMPLETED`

Enums reduce the possibility of inconsistent values.

Without an enum, an application might receive inconsistent role strings such as:

- `admin`
- `Admin`
- `administrator`
- `ADMINISTRATOR`

An enum restricts the accepted values to a known set.

TypeScript supports numeric and string enums. String enums are particularly useful when values must be exchanged through JSON APIs or stored in databases.

The implementations use:

| Language | Representation |
|---|---|
| TypeScript | `enum` |
| Python | `Enum` |
| JavaScript | Frozen object |
| C++17 | `enum class` |
| Java 17 | `enum` |
| PostgreSQL | Enum type |

JavaScript has no native runtime enum construct. A frozen object provides a practical representation, although it does not provide TypeScript's compile-time enum checking.

Database enums restrict stored values, but changing an established enum requires a database migration.

## 6. Union Types

A union allows a variable or property to contain one of several permitted types.

The TypeScript declaration:

`type Identifier = number | string`

allows either a number or a string.

This is useful when an external system accepts different identifier formats.

The application implements identifier normalization:

- Positive numeric identifiers are converted to strings.
- Non-empty string identifiers are accepted.
- Invalid values are rejected.

Union types are particularly useful for:

- API response variations.
- Multiple identifier formats.
- Optional input formats.
- State transitions.
- Alternative domain representations.

### Discriminated unions

A discriminated union uses a common property to identify which variant is present.

The application uses two API response variants.

| Variant | Discriminator | Required data |
|---|---|---|
| Success | `success` | Data object |
| Error | `error` | Message and error code |

The discriminator enables safe branching.

The application checks the `kind` property before accessing variant-specific fields.

This avoids assuming that every response contains the same properties.

C++17 represents these alternatives using `std::variant`.

Java 17 uses sealed interfaces and records.

PostgreSQL uses a discriminator column combined with a check constraint.

These mechanisms provide similar domain modeling capabilities, but their type checking and runtime behavior are different.

### Exhaustive handling

A discriminated union should have an explicit handler for every permitted variant.

If a new variant is introduced, the relevant processing logic should be reviewed and updated.

This prevents incomplete response handling.

## 7. Intersection Types

An intersection combines multiple types into one type that must satisfy all included contracts.

The TypeScript notation uses the `&` operator.

For example:

`type ManagedResource = Resource & Auditable & Permissions`

means that a managed resource must satisfy all three structures.

The implementation combines:

### Resource

- Resource identifier.
- Resource name.

### Auditable

- Creator identifier.
- Creation timestamp.

### Permissions

- Read permission.
- Write permission.
- Delete permission.

A resource therefore carries its descriptive information, audit information and authorization-related attributes.

Intersection types differ from union types:

| Property | Union | Intersection |
|---|---|---|
| Operator | `\|` | `&` |
| Meaning | Either permitted type | All required types |
| Example | `string \| number` | `Resource & Auditable` |
| Typical use | Alternative data variants | Combined contracts |

The C++17 implementation combines structures as members.

The Java implementation uses multiple interface implementations.

The Python implementation combines dataclass fields.

PostgreSQL represents the combined properties in one relational table.

These are equivalent domain-modeling approaches, not identical implementations of TypeScript's structural type system.

## 8. Type Aliases

A type alias assigns a descriptive name to an existing type or type expression.

For example:

`type UserId = number`

`type Email = string`

`type Coordinate = [number, number]`

Aliases improve readability and reduce repetition.

They are particularly useful for:

- Domain identifiers.
- Complex object structures.
- Union types.
- Intersection types.
- Tuples.
- Generic type expressions.

A type alias does not create a new runtime object or a new JavaScript primitive.

Two aliases can describe the same underlying type without providing nominal type separation.

For example, `UserId` and `ProjectId` may both be aliases of `number`. TypeScript can still permit one to be assigned to the other.

For stronger separation, branded types or wrapper objects can be used.

The other implementations use different mechanisms:

| Language | Comparable mechanism |
|---|---|
| Python | `TypeAlias` |
| JavaScript | No native alias; runtime conventions |
| C++17 | `using` |
| Java 17 | Wrapper records |
| PostgreSQL | `DOMAIN` |

PostgreSQL domains are stronger than ordinary TypeScript aliases because they can enforce constraints at the database level.

## 9. Generic Types

Generics allow reusable components to operate on multiple types while retaining type information.

A TypeScript generic function can accept an array of type `T` and return a value of the same type.

For example:

`function firstItem<T>(items: T[]): T | undefined`

The return type reflects the element type.

The implementations provide generic repositories with:

- Record insertion.
- Identifier-based retrieval.
- Duplicate detection.
- Record removal.
- Collection counting.

The repository separates storage behavior from the type of stored objects.

The language implementations use:

- Python `Generic` and `TypeVar`.
- JavaScript `Map` with runtime validation.
- C++17 class templates.
- Java generic classes and `Optional`.

JavaScript does not provide compile-time generic checking without TypeScript. Its implementation therefore uses runtime validation and JavaScript's native collection mechanisms.

## 10. Implementation Architecture

The five source files demonstrate different engineering approaches.

| File | Main design approach |
|---|---|
| Python | Dataclasses, typed collections and generic repositories |
| JavaScript | Runtime validation, immutable objects, events and asynchronous processing |
| C++17 | STL containers, variants, templates and explicit validation |
| Java 17 | Records, sealed interfaces, enums and generic services |
| PostgreSQL | Domains, composite types, arrays, JSONB, constraints and functions |

### Python

The Python program uses dataclasses to define structured objects.

Enums restrict accepted domain values. Type aliases describe reusable structures.

Generic repositories use dictionaries for identifier-based retrieval.

Dictionary lookup and insertion are expected to operate in constant time, while iteration depends on the number of stored records.

### JavaScript

The JavaScript implementation emphasizes runtime behavior.

Classes validate incoming data, frozen objects protect selected structures from modification, and private class fields protect repository internals.

`Map` supports identifier-based storage.

`Set` prevents duplicate listener registrations and provides efficient membership checks.

The event bus demonstrates subscription, event dispatch and unsubscription.

Asynchronous processing uses `async` and `await` with explicit failure propagation.

### C++17

The C++ implementation emphasizes explicit data representation and controlled resource usage.

`std::variant` provides a type-safe representation of alternative values.

`std::tuple` and `std::pair` represent fixed-position structures.

Templates provide reusable generic operations.

STL algorithms perform sorting, filtering, copying and aggregation.

`std::optional` represents the absence of a retrieved record without requiring a special sentinel value.

### Java 17

The Java implementation emphasizes immutable domain objects and enterprise-oriented contracts.

Records provide concise immutable data carriers.

Sealed interfaces restrict the permitted implementations of a union-like type.

Enums represent finite domain values.

Generic repositories separate storage operations from entity types.

`Optional` represents potentially absent values.

Stream operations perform filtering, sorting, transformation and aggregation.

### PostgreSQL

The SQL implementation focuses on persistence and database-level integrity.

It uses:

- Domains for reusable constrained types.
- Enums for finite value sets.
- Composite types for structured values.
- Native arrays for collections.
- JSONB for flexible object properties.
- Foreign keys for entity relationships.
- Check constraints for data validation.
- Triggers for derived-value calculation.
- Functions for reusable database operations.
- Procedures for database workflows.
- Views for reporting.
- CTEs for analytical queries.
- Indexes for frequently accessed data.

The database is an independent enforcement layer. Application-level validation does not replace database constraints.

## 11. Database Data Model

The PostgreSQL implementation follows this relationship structure:

    Users
      |
      |-- Projects
      |
      |-- Assessments
      |
      |-- Managed Resources

    API Results

Users are the central identity records.

Projects reference their owners and maintain member identifiers.

Assessments reference users and maintain arrays of validated scores.

Managed resources combine audit attributes, permissions and JSONB metadata.

API results use a discriminator to distinguish successful and failed responses.

### PostgreSQL arrays

The `tags` column stores a collection of user tags.

The `member_ids` column stores project membership identifiers.

GIN indexes support suitable array containment and membership queries.

Arrays are appropriate for relatively simple collections. When individual members need independent attributes, foreign keys, or complex lifecycle management, a separate relational table is generally preferable.

### JSONB objects

The resource metadata column stores structured JSON.

JSONB supports key extraction, containment operations and indexing.

It is useful for flexible attributes that do not justify a separate relational column.

Frequently queried or integrity-critical properties should normally be represented using explicit columns and constraints.

### Domain constraints

The database defines reusable constraints for:

- Positive identifiers.
- Email formats.
- Non-empty text.
- Score ranges.

The assessment trigger calculates an average when an assessment is inserted or its score array is updated.

The database therefore maintains the calculated value without requiring every application client to implement the same calculation.

## 12. Validation and Failure Handling

Type declarations and runtime validation serve different purposes.

| Situation | Appropriate control |
|---|---|
| Invalid static assignment | TypeScript compiler |
| Invalid API payload | Runtime schema validation |
| Missing required object property | Runtime validation |
| Invalid enum value | Runtime validation and database constraint |
| Duplicate identifier | Unique constraint or repository check |
| Invalid numerical range | Validation and database constraint |
| Missing database relationship | Foreign key |
| Invalid union variant | Discriminator validation |
| Invalid permission configuration | Domain and policy validation |

A production application should validate data at trust boundaries.

Typical trust boundaries include:

- HTTP request bodies.
- Query parameters.
- External API responses.
- Database records.
- Imported files.
- Message queue events.

Never assume that external JSON is safe merely because the application has a TypeScript interface describing its expected structure.

Type assertions and compile-time annotations do not validate untrusted data.

## 13. Performance Considerations

The examples use collection structures suited to their workloads.

| Structure | Typical operation | Expected complexity |
|---|---|---|
| Array indexing | Access by position | O(1) |
| Array search | Find an element | O(n) |
| Array sorting | Comparison sorting | O(n log n) |
| Hash map | Identifier lookup | Expected O(1) |
| Ordered map | Lookup | O(log n) |
| Set membership | Check uniqueness | Expected O(1) |
| Database B-tree index | Indexed lookup | O(log n) |
| Database GIN index | Suitable array and JSONB queries | Workload-dependent |

These are typical complexity expectations rather than universal execution guarantees.

Performance depends on collection size, data distribution, memory allocation, indexing strategy and access patterns.

Avoid unnecessary array copies and repeated sorting.

Use immutable structures where predictable state management is more important than frequent in-place modification.

For large collections, consider pagination and bounded processing instead of loading every record into memory.

## 14. Security and Production Considerations

The examples include basic validation, identifier constraints and permission attributes.

Production systems require stronger controls.

Important considerations include:

- Validate all externally supplied values.
- Do not trust client-side role or permission claims.
- Perform authorization checks on the server.
- Use parameterized SQL statements.
- Apply least-privilege database permissions.
- Avoid exposing sensitive fields in API responses.
- Validate JSON structures before processing.
- Use explicit state transitions for account status.
- Protect immutable domain data from accidental modification.
- Apply database constraints to critical invariants.
- Use migrations when changing established database types.
- Avoid treating a resource's permission flags as a complete authorization policy.

The permission example demonstrates domain-level permission representation. It is not a complete authentication or authorization system.

Similarly, an enum restricts permitted values but does not establish whether a user is authorized to perform an operation.

## 15. Execution

| Deliverable | Execution |
|---|---|
| Python | `python typescript_core.py` |
| JavaScript | `node typescript_core.js` |
| C++17 | Compile with `g++ -std=c++17 -O2 -Wall -Wextra` |
| Java 17 | Compile with `javac --release 17 TypeScriptCore.java` |
| Java 17 | Run with `java TypeScriptCore` |
| PostgreSQL | Execute using `psql -d database_name -f typescript_core.sql` |

The PostgreSQL script creates a dedicated schema named `typescript_core`.

The script uses transactional DDL and DML. Its database objects can be removed by dropping that schema when the exercise is no longer required.

## 16. Conceptual Comparison

| Concept | TypeScript | Main purpose |
|---|---|---|
| Array | `T[]` | Ordered collection of values |
| Object | `{ id: number }` | Named properties |
| Tuple | `[number, string]` | Fixed-position heterogeneous values |
| Enum | `enum Role` | Finite named values |
| Union | `A \| B` | Alternative permitted types |
| Intersection | `A & B` | Combined type requirements |
| Alias | `type UserId = number` | Reusable type expression |
| Generic | `Repository<T>` | Reusable type-safe components |

These concepts are complementary rather than interchangeable.

Arrays and tuples describe collection structure.

Objects describe named properties.

Enums define finite sets of values.

Unions describe alternatives.

Intersections combine requirements.

Aliases provide reusable names.

Generics allow these structures to be parameterized by other types.

Together, they support precise data contracts, predictable application state and maintainable domain models.
