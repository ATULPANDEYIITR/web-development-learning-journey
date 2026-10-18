# Prototype Chains, Inheritance, Constructor Functions, and Object.create

## Topic and scope

JavaScript objects can inherit properties and methods from other objects. This behavior is based on prototype delegation rather than requiring every object to be created from a class.

Four related mechanisms explain this model:

- **Prototype chain:** The sequence of objects JavaScript searches when resolving a property.
- **Constructor functions:** Functions conventionally used with `new` to initialize instances and connect them to a prototype.
- **Inheritance:** The reuse of behavior through delegation between prototypes or through class syntax built on JavaScript's prototype system.
- **Object.create:** A method that creates an object with a specified prototype, including `null` when an object should have no prototype.

The implementations use Python to model explicit lookup, JavaScript to examine native prototype behavior, C++ to represent configuration delegation in a catalog, Java to model enterprise configuration inheritance, and PostgreSQL to represent inherited configuration relationally.

## The prototype chain

Every ordinary JavaScript object has an internal prototype reference. Property access begins with the object itself. If the property is absent, JavaScript searches the object's prototype and continues until it finds the property or reaches `null`.

Consider an object created with `Object.create`:

- `devicePrototype` owns the `category` property.
- `router` owns the `name` property.
- `router` delegates unresolved property lookups to `devicePrototype`.

Consequently, `router.category` returns the inherited value even though `Object.hasOwn(router, "category")` returns `false`.

The `in` operator checks whether a property exists on the object or anywhere in its prototype chain. `Object.hasOwn` checks only the object itself. These operations answer different questions and should not be used interchangeably.

### Property shadowing

When an object defines a property with the same name as an inherited property, the own property takes precedence. This is called shadowing.

If a prototype defines `category: "network-device"` and an instance defines `category: "wireless-router"`, reading `instance.category` returns `"wireless-router"`. The prototype remains unchanged.

Assigning a property to an object does not automatically update its prototype. This separation permits instances to override defaults without modifying shared behavior.

### Lookup complexity

If the prototype chain contains `h` objects, a property lookup may examine up to `h` objects before finding the property or concluding that it is missing. Typical lookups are optimized by JavaScript engines, but deep or frequently modified prototype structures can complicate optimization.

A prototype chain should represent genuine shared behavior or defaults rather than serve as an unrestricted configuration mechanism.

## Constructor functions and the `new` operator

A constructor function is an ordinary JavaScript function used with `new`.

When `new Employee(id, role)` executes, JavaScript creates a new object, connects its prototype to `Employee.prototype`, calls the function with the new object as `this`, and returns the resulting instance unless the constructor explicitly returns another object.

The JavaScript implementation uses `Employee.prototype.describe` to define a method shared by employee instances. Each instance stores its own identifier and role, while the shared method resides on the prototype.

This is more memory-efficient than creating a separate method function for every instance.

### The distinction between a constructor and its prototype

`Employee` is a function object. `Employee.prototype` is an object used as the prototype for instances created with `new Employee(...)`.

These references serve different purposes:

- `Employee.prototype` supplies inherited instance properties.
- `Object.getPrototypeOf(employee)` returns the instance's actual prototype.
- `employee.constructor` normally resolves to the `constructor` property inherited from that prototype.

The `constructor` property is a conventional reference, not a guarantee about an object's true origin. It can be reassigned, shadowed, or absent.

Calling a constructor without `new` can leave `this` undefined in strict mode or produce unexpected behavior in other contexts. The JavaScript example uses `new.target` to reject direct invocation.

## Inheritance with constructor functions

Constructor-function inheritance requires two distinct operations.

The parent constructor initializes instance-specific state. The prototype link establishes inherited behavior.

The JavaScript example calls `Device.call(this, ...)` from `Server` to initialize the server's asset tag and manufacturer. It separately uses `Object.create(Device.prototype)` to establish the inheritance relationship.

Replacing `Server.prototype` also replaces its original own `constructor` property. The implementation restores that property with `Object.defineProperty`.

After this setup, a server inherits methods from `Device.prototype` while retaining methods specific to `Server.prototype`.

`instanceof` checks whether a constructor's current prototype appears in an object's prototype chain. It does not simply compare constructor names, and its result can be affected by changes to prototype references.

## Object.create

`Object.create(proto)` creates an object whose prototype is exactly `proto`.

This allows developers to create objects that delegate to a selected prototype without calling a constructor function.

For example, a router can be created from a shared device prototype:

- The prototype contains reusable descriptive behavior.
- The router stores its own name.
- The inherited category can be overridden locally.

`Object.create(null)` creates an object with no prototype. It does not inherit methods such as `toString` or `hasOwnProperty` from `Object.prototype`.

Null-prototype objects can be useful for dictionaries containing arbitrary keys. The JavaScript implementation demonstrates safe own-property checks and explains why ordinary objects need care when keys such as `__proto__` are handled.

For untrusted dictionary keys, `Object.create(null)` or `Map` can avoid particular prototype-pollution hazards. Neither removes the need to validate inputs and define clear data-handling rules.

## Modern JavaScript classes

JavaScript class syntax provides a structured way to define constructors and prototype methods.

A method declared inside a class body is normally placed on the class's prototype rather than recreated as an own property on every instance. Thus, separate `Account` instances can share the same `deposit` function while maintaining independent balances.

Classes use prototype inheritance under the hood, but they also impose stricter invocation rules than traditional constructor functions. A class constructor cannot be called without `new`.

Class syntax does not make instances identical to plain records, and it does not eliminate the need to understand property ownership. Inherited methods and own data properties remain distinct.

## Python implementation

The Python script builds a small `PrototypeObject` abstraction with a property dictionary and an optional prototype reference.

Its `get` method searches the current object first, then follows prototype references. A visited-object set detects cycles so malformed structures cannot cause an infinite lookup loop.

The script also demonstrates Python's native class inheritance through `Device` and `Server`, including method overriding with `super()`. Python class inheritance is related conceptually to prototype delegation, but Python does not use JavaScript's object prototype mechanism.

The account example distinguishes per-instance state from methods shared through a Python class. The edge-case demonstrations cover missing attributes, shadowing, own-property checks, and prototype cycles.

## JavaScript implementation

The JavaScript file focuses on native runtime behavior rather than simulating the mechanism.

Its examples cover `Object.create`, constructor invocation, prototype method sharing, constructor-function inheritance, method descriptors, class inheritance, and prototype-chain traversal.

The property-descriptor example shows that a class method is typically non-enumerable, writable, and configurable on the prototype. These attributes influence reflection and property enumeration.

The null-prototype dictionary example illustrates a security-relevant design decision: ordinary object property assignment involving special keys can have surprising effects, while a null-prototype dictionary treats such keys as ordinary own properties.

The file runs directly in Node.js or a browser console and requires no third-party package.

## C++ case study: delegated asset configuration

C++ does not provide JavaScript-style prototype inheritance for individual objects. The C++ program therefore implements explicit delegation for a realistic infrastructure asset catalog.

A catalog prototype holds default properties and an optional reference to another prototype. An asset record stores its own properties and delegates unresolved lookups to the selected prototype.

The sample configuration contains organization-wide defaults, server defaults, and production-specific defaults. An API server overrides its owner and CPU count while inheriting the region, asset type, monitoring configuration, and backup policy.

The `get` operation checks own properties before delegation. It returns an `optional` value so missing properties are represented explicitly instead of being confused with empty strings.

Cycle detection prevents unbounded traversal. The example also breaks a deliberately created `shared_ptr` ownership cycle before exiting because shared ownership cycles can prevent automatic memory reclamation.

This design is an explicit model of delegation, not a replacement for ordinary C++ class inheritance. It is useful when runtime configuration must vary independently of a C++ type hierarchy.

## Java implementation: enterprise configuration

The Java program models configuration inheritance for a payments service.

`PrototypeNode` stores a map of local properties and a reference to another node. `ServiceConfiguration` associates a service with an environment and provides controlled access to its effective settings.

`ConfigurationService` resolves required values and validates production configuration. The endpoint must use HTTPS, and the timeout must be an integer between 1 and 120 seconds.

The hierarchy separates organization-wide settings from service defaults and production overrides. Changing a local logging level shadows an inherited value without mutating the shared service defaults.

An identity-based visited set detects prototype cycles. Identity comparison matters because cycle detection must distinguish actual objects, not objects that merely compare equal.

The synchronized methods protect individual property operations, but the example does not claim to provide an atomic snapshot across an entire multi-property validation. Production systems requiring concurrent configuration updates should use immutable configuration snapshots or an explicit locking strategy around the complete validation operation.

## SQL implementation: relational configuration inheritance

PostgreSQL represents the configuration hierarchy using `configuration_profiles` and `configuration_overrides`.

Each profile may reference a parent profile. Each override stores a property name and value, with a composite primary key preventing duplicate definitions of the same property in one profile.

The recursive query follows parent references and records the depth of each profile. A window function ranks definitions by depth so the closest definition wins. This implements relational shadowing without pretending that SQL tables possess JavaScript prototypes.

The `resolve_configuration` function retrieves one effective property and reports the profile that supplied it. The `effective_configuration` view calculates all effective properties for each profile.

Indexes support parent traversal and property lookup. Foreign keys prevent profiles from referencing nonexistent parents, while the check constraint rejects direct self-reference.

The schema does not, by itself, prevent every possible multi-profile cycle. The script demonstrates cycle detection and explains why longer-cycle prevention needs a trigger or a controlled update procedure. The configuration-validation query checks the resolved endpoint scheme and timeout range.

The SQL implementation is a database model of configuration delegation. It does not provide JavaScript's dynamic property access, functions as properties, getters, setters, or native object identity.

## Design and security considerations

### Shared mutable prototypes

Changing a shared prototype can affect many objects that inherit from it. Shared prototypes should contain stable defaults or reusable methods. Per-instance state belongs on the instance unless shared mutation is intentional.

### Prototype pollution

Prototype pollution occurs when untrusted input changes an object prototype or introduces properties that unexpectedly influence inherited lookups. Validate external keys and values. Use `Map` or null-prototype dictionaries where appropriate, and avoid blindly merging untrusted objects into ordinary configuration objects.

### Cycles

A valid JavaScript prototype chain cannot be cyclic. JavaScript prevents direct creation of such a chain through normal prototype-setting operations. Explicit prototype models in other languages or database hierarchies need their own cycle checks.

### Method receiver behavior

An inherited method can use `this` to refer to the object on which it was invoked. Extracting a method into a standalone variable may change its receiver. Where a fixed receiver is required, use `bind` deliberately rather than assuming the method retains its original object.

### Choosing between classes and Object.create

Use classes when objects represent instances of a well-defined domain type with a constructor and stable behavior. Use `Object.create` when the desired prototype relationship is explicit and constructor execution is unnecessary.

For plain data dictionaries with untrusted keys, consider `Map` or `Object.create(null)` rather than relying on inherited properties.

The right choice depends on whether the design requires type-oriented construction, direct object delegation, mutable shared behavior, or isolated data storage.
