# Advanced Objects: Property Descriptors, Accessors, Integrity Levels, and Prototypes

## Technical scope

JavaScript objects are property collections with rules governing how properties are stored, accessed, enumerated, modified, and inherited. Those rules are defined through property descriptors and the object model rather than through the values alone.

This project examines five connected mechanisms:

- **Property descriptors** define whether a property is writable, enumerable, and configurable, or whether it is controlled by getter and setter functions.
- **Getters and setters** provide controlled property access, including validation and computed values.
- **Object integrity levels** determine whether an object can acquire new properties, lose existing properties, or change data-property values.
- **Prototypes** provide inherited behavior through a lookup chain and allow objects to share methods and default properties.
- **Descriptor-aware copying** preserves property metadata that ordinary value copying may discard.

The Python, JavaScript, C++, Java, and SQL implementations examine these concepts through different technical perspectives. The repository-governance case studies use immutable configuration, inherited policy defaults, and controlled state transitions as practical applications. Repository governance is a domain example, not a claim that Git Pull Requests themselves are JavaScript objects.

## Property descriptors

A property descriptor defines the behavior of an individual own property.

### Data descriptors

A data descriptor contains a value and a writable flag. The other important flags are enumerable and configurable.

| Attribute | Meaning |
|---|---|
| `value` | The property's stored value. |
| `writable` | Whether ordinary assignment may change the stored value. |
| `enumerable` | Whether the property participates in operations such as `Object.keys()`. |
| `configurable` | Whether the property can normally be deleted or reconfigured. |

`Object.defineProperty()` is the primary mechanism for defining these attributes explicitly.

The JavaScript implementation creates a release object whose version cannot be reassigned or deleted. A second property is non-enumerable, so it appears in `Object.getOwnPropertyNames()` but not in `Object.keys()`.

This distinction is useful for metadata and internal-facing properties, although non-enumerability is not a security boundary. Code with access to the object can still inspect its own properties.

### Accessor descriptors

An accessor descriptor defines a getter, a setter, or both. It does not use the data descriptor's `value` and `writable` fields.

A getter computes or retrieves a value when the property is read. A setter intercepts assignments and can validate input before changing internal state.

The JavaScript account example accepts only finite, non-negative balances. Invalid assignments raise an exception instead of corrupting the account state. The property remains syntactically accessible as `account.balance`, while its behavior is implemented by accessor functions.

A property cannot simultaneously be a data descriptor and an accessor descriptor. Attempts to redefine a non-configurable property incompatibly are rejected.

## Getters and setters as domain boundaries

Accessors are most useful when a property's apparent simplicity hides an invariant.

For example, an account balance must not become negative, a retry count must be an integer within an accepted range, and a release identifier must follow a defined format. A setter can enforce these conditions at the point where the value enters the object.

The Python implementation uses `@property` and a corresponding setter for an account balance. Python's property mechanism is related to JavaScript accessors, but the languages do not share the same descriptor semantics. Python's data model also includes descriptor methods such as `__get__`, `__set__`, and `__delete__`.

The JavaScript example uses `Number.isFinite()` to reject `NaN`, positive infinity, and negative infinity. A simple comparison such as `amount < 0` would not reject `NaN`, because comparisons involving `NaN` do not behave like ordinary numeric comparisons.

Accessors require care when copying objects, serializing data, or invoking them with a different receiver. A getter may perform computation, throw an exception, or depend on `this`. Reading a property is not necessarily a passive operation.

## Object integrity levels

JavaScript provides three integrity-related operations with different effects.

| Operation | Add properties | Delete existing properties | Change writable data values |
|---|---|---|---|
| `Object.preventExtensions()` | No | Yes, if configurable | Yes, if writable |
| `Object.seal()` | No | No | Yes, if writable |
| `Object.freeze()` | No | No | No, for ordinary data properties |

These operations affect the object's own properties. They do not recursively freeze referenced objects.

### Preventing extensions

`Object.preventExtensions()` prevents new own properties from being added. Existing configurable properties may still be removed, and existing writable data properties may still be changed.

The JavaScript implementation uses a release-related object to demonstrate that an object can become non-extensible without becoming fully immutable.

### Sealing

`Object.seal()` prevents extensions and makes existing own properties non-configurable. Existing writable data properties remain writable.

The C++ `PolicyObject` model includes a `seal()` operation that locks property configuration while preserving writable values. It is an educational model rather than an implementation of the JavaScript specification.

### Freezing

`Object.freeze()` prevents extensions, makes own properties non-configurable, and makes ordinary own data properties non-writable.

Freezing is shallow. If an object contains a nested configuration object, that nested object remains mutable unless it is frozen separately. The JavaScript example demonstrates this by freezing a deployment object and then changing a nested region property.

Accessor properties require special attention. Freezing an accessor property prevents its reconfiguration, but does not remove its setter. A setter that updates external or closure-held state can still change that state. Therefore, `Object.isFrozen()` does not guarantee that every observable behavior associated with an object is immutable.

The Python implementation uses `MappingProxyType` to provide a read-only mapping interface and `__slots__` to restrict instance attributes. These features do not make Python objects universally equivalent to frozen JavaScript objects. Their protections apply to specific interfaces and attribute mechanisms.

## Prototypes and property lookup

JavaScript uses prototype inheritance. An object's own properties take precedence over properties found on its prototype. If the property is not found, lookup continues through the prototype chain until the property is found or the chain ends.

The JavaScript example creates a service object with `Object.create()`. The object inherits its category and health-check method from a shared prototype while keeping its own service name.

Assigning a new `category` property to the instance shadows the inherited value. It does not change the prototype's property.

The important distinctions are:

- `Object.hasOwn(object, property)` checks whether a property belongs directly to the object.
- The `in` operator checks the object and its prototype chain.
- `Object.getPrototypeOf(object)` returns the object's prototype.
- `Object.create(prototype)` creates an object with the specified prototype.
- `Object.setPrototypeOf()` changes an object's prototype, but changing prototypes dynamically can complicate optimization and should be avoided in performance-sensitive application paths.

Prototype inheritance also introduces risks. If untrusted keys are copied into ordinary objects without validation, keys such as `__proto__`, `constructor`, or `prototype` may interact with application logic in unexpected ways. The exact behavior depends on the operation used. Safer approaches include validating accepted keys, using `Object.hasOwn()` for own-property checks, and considering `Object.create(null)` for dictionaries that do not need inherited methods.

## JavaScript implementation

The JavaScript file is an executable study of the language's native object model.

It includes:

- Explicit data descriptors for immutable version metadata and non-enumerable internal properties.
- Descriptor inspection with `Object.getOwnPropertyDescriptor()`.
- Accessor validation for financial state.
- Separate demonstrations of non-extensible, sealed, and frozen objects.
- Shallow-freeze behavior and accessors that update closure-held state.
- Prototype inheritance, own-property checks, and shadowing.
- Reconfiguration failures for non-configurable properties.
- A comparison between `Object.assign()` and descriptor-preserving copying.

`Object.assign()` copies enumerable own values into a destination object. It does not preserve the source property's complete descriptor. `Object.getOwnPropertyDescriptors()` combined with `Object.create()` provides a way to create a copy that retains the source's own property descriptors and prototype.

Descriptor-preserving copying is not automatically deep cloning. Nested references remain shared unless a separate cloning strategy is applied.

## Python implementation

The Python script provides a small `DescriptorObject` model with explicitly represented property metadata.

The model supports:

- Reading and writing properties through controlled methods.
- Distinguishing enumerable properties from all own properties.
- Preventing incompatible redefinition of non-configurable properties.
- Applying non-extensible, sealed, and frozen states.
- Rejecting writes and deletions when the modeled descriptor prohibits them.
- Demonstrating validated accessors through Python's `property` decorator.
- Demonstrating inherited lookup with a simple parent chain.
- Exposing a read-only mapping through `MappingProxyType`.

The model is intentionally explicit because Python does not offer JavaScript's `Object.defineProperty()` API for ordinary instances. It approximates selected JavaScript descriptor rules rather than reproducing the entire specification. For example, Python's runtime does not automatically route normal attribute access through the model's `get()` and `set()` methods.

The account class demonstrates a more idiomatic Python approach: validation occurs through a property setter, while the computed account summary is implemented as a getter-only property.

## C++ case study: release governance

The C++17 program models a release governance engine that evaluates whether a repository Pull Request is eligible for merging into a protected branch.

The `PolicyObject` class stores descriptor-like property metadata in a `std::map`. Its `preventExtensions()`, `seal()`, and `freeze()` operations demonstrate the distinction between prohibiting new properties, locking property configuration, and prohibiting changes to stored values. These operations are application-defined and do not have JavaScript's automatic object semantics.

The `PolicyPrototype` class performs explicit lookup through a parent chain. Repository-specific policy values can override organization-level defaults without modifying the defaults themselves.

The merge engine evaluates several independent conditions:

- The Pull Request must be open and not a draft.
- Its source and target branches must differ.
- The target must match the protected branch.
- Merge conflicts and unresolved review conversations must be absent.
- Current approvals must meet the configured threshold.
- A designated code owner must approve when required.
- Required checks must be passing.
- The reviewed commit must match the current head when stale approvals are dismissed.
- The requested merge strategy must be permitted.

The program is a policy simulation. It does not connect to a Git host, update branch references, perform atomic merges, or enforce permissions on a real repository. Its main purpose is to make the policy decision explicit and testable.

## Java implementation: enterprise policy model

The Java 17 program models repository governance with explicit domain types and a centralized merge-eligibility service.

`BranchPolicy` holds immutable policy settings. Its sets are copied using `Set.copyOf()`, preventing callers from modifying the policy through a collection reference they supplied during construction.

`PullRequest` models the lifecycle states `OPEN`, `CLOSED`, and `MERGED`. Its methods enforce valid transitions, such as permitting a closed request to reopen but rejecting an attempt to close an already merged request.

`ReviewDecision` and `StatusCheck` are records with constructor validation. Review history is represented by a map containing each reviewer's latest decision, making replacement of an earlier approval explicit. The review model rejects self-approval and identifies whether a review is associated with the current head commit.

`MergeEligibilityService` centralizes the policy rules rather than scattering them across unrelated print statements. It checks independent current approvals, code-owner eligibility, required status checks, target-branch restrictions, unresolved conversations, and allowed merge strategies.

The program also distinguishes evaluation from state transition. A successful eligibility evaluation permits the modeled merge operation, while a failed evaluation produces explicit violations. A production implementation would still need transactional integration with the repository hosting service.

## SQL data model

The PostgreSQL script represents repository governance as relational data with enforceable integrity rules.

### Repositories and branches

`repositories` stores repository identity and default-branch metadata. `branches` associates branch names and head commit identifiers with a repository. A unique constraint prevents duplicate branch names within one repository.

The Pull Request trigger verifies that both branch references belong to the declared repository. Foreign keys prevent references to nonexistent branches or users.

### Protection policies

`branch_protection_policies` stores the required approval count, code-owner requirement, status-check requirement, conversation-resolution requirement, direct-push restriction, force-push restriction, deletion restriction, linear-history requirement, stale-approval behavior, administrator enforcement, bypass configuration, and permitted merge strategies.

These fields describe intended policy. Recording a restriction in a database does not enforce Git hosting permissions by itself. Enforcement must be implemented by a trusted service or the repository hosting platform.

### Reviews and comments

`reviews` preserves review history, including the reviewer, review state, reviewed commit, and submission time. An index supports retrieval of each reviewer's most recent decision.

`review_comments` stores inline and general review discussions. The inline-comment constraint requires a line number, and a partial index helps retrieve unresolved discussions efficiently.

The review trigger rejects approvals submitted by the Pull Request author. The merge-eligibility function uses the latest decision per reviewer so that a newer change request or dismissal supersedes an earlier approval.

### Status checks and merge eligibility

`status_checks` associates check results with a specific Pull Request head commit. A successful check on an older commit cannot satisfy a policy requiring checks for the current head.

`required_status_checks` defines the checks required by each protection policy. The `evaluate_merge_eligibility()` function combines review, status-check, conversation, and Pull Request state into a Boolean eligibility result and an array of blocking reasons.

The function is a read-only evaluator, not a merge executor. A production merge operation would need transaction isolation, appropriate row locks, current branch-head verification, authorization checks, and coordination with the Git hosting service.

The demonstration uses a savepoint to show how a constraint violation can be handled without abandoning the entire transaction. The invalid approval threshold is rejected by the table's `CHECK` constraint.

## Important distinctions

### Descriptors versus integrity levels

Descriptors govern individual properties. Integrity operations change which mutations are permitted across an object's own properties. A non-writable property does not imply that its containing object is frozen, and a frozen object can still reference mutable nested values.

### Prototype inheritance versus copying

Prototype lookup shares behavior through delegation. Copying creates another object's own properties. Copying enumerable values does not preserve non-enumerable properties or their descriptor flags unless descriptor-aware operations are used.

### Application immutability versus security

A frozen configuration object is useful for preventing accidental changes through ordinary JavaScript operations. It is not a substitute for authorization, server-side validation, secret management, or database constraints.

Likewise, an application-level policy object cannot replace branch protection enforced by the hosting platform. Repository governance must be enforced at the trusted boundary that controls the actual merge.

## Performance and debugging considerations

Property descriptors introduce behavior that can be less obvious than ordinary assignments. A getter may compute a value or throw an exception. A setter may reject input. An inherited property may be shadowed by an own property. A non-enumerable property may be absent from `Object.keys()` while remaining accessible.

For debugging, inspect the descriptor directly rather than inferring behavior from the displayed value. Compare `Object.keys()`, `Object.getOwnPropertyNames()`, and `Object.getOwnPropertyDescriptor()` when an expected property appears to be missing or immutable.

In high-throughput JavaScript code, stable object shapes and predictable property access can help runtime optimization. Repeatedly redefining descriptors or changing prototypes may make optimization more difficult. Use explicit descriptors where their behavioral guarantees are useful, not as a default replacement for ordinary object properties.
