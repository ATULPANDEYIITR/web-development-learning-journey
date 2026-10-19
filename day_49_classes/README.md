# Classes: Constructors, Inheritance, Private Fields, and Static Members

## Scope

This project examines object-oriented classes through four closely related mechanisms:

- **Classes** define the structure and behavior shared by objects.
- **Constructors** establish valid initial state when an object is created.
- **Inheritance** allows a derived class to reuse and specialize behavior from a base class.
- **Private fields** protect internal state from uncontrolled external mutation.
- **Static members** belong to the class itself rather than to an individual object.

The six deliverables approach these mechanisms from different technical perspectives. Python focuses on executable object modeling and class-level state. JavaScript emphasizes modern class semantics, private fields, static members, and event-driven behavior. C++ develops an enterprise asset registry using inheritance, virtual dispatch, ownership, and static state. Java models an enterprise employee domain with explicit types, interfaces, immutable records, validation, and service logic. PostgreSQL represents class definitions, members, inheritance relationships, object instances, and class-level values relationally.

The central distinction is that an **instance member describes one object**, while a **static member describes the class as a whole**. Inheritance connects classes into a hierarchy, while private fields define which parts of an object's representation are directly accessible from outside the class.

## Core Object Model

A class can be viewed as a contract containing state and behavior.

An object is a runtime instance of that class. If a class called `Account` defines an owner and balance, two account objects can contain different owners and balances while sharing the same operations.

Constructors are responsible for establishing the initial invariant of the object. A constructor should reject invalid state rather than allowing an object to exist in a form that later methods cannot safely handle.

For example, the Python `Account` constructor validates the owner and initial balance before storing them. `SavingsAccount` then adds a stronger rule requiring a minimum balance. This demonstrates an important inheritance property: the base constructor can establish common invariants while the derived constructor establishes additional invariants specific to the derived type.

Private state serves a different purpose. It is not simply another naming convention for a field. It establishes an access boundary around implementation details. In the Python example, `__balance` uses name mangling, while JavaScript uses the language-level `#salary` syntax. Java and C++ use private fields enforced by their access-control systems.

Static members represent class-level state or behavior. The Python `Account._active_accounts`, JavaScript `Employee.activeEmployees`, C++ `Asset::active_assets_`, and Java `Employee.activeEmployeeCount` all track information associated with the class rather than with a particular instance.

## Constructors and Object Invariants

A constructor should leave an object ready for legitimate use.

The Python account hierarchy demonstrates constructor chaining. `SavingsAccount` calls `super().__init__()` to establish the common account state before applying its minimum-balance rule. The subclass therefore does not duplicate the parent constructor's identity and balance initialization.

The JavaScript employee hierarchy follows the same conceptual model through `super(name, salary)`. JavaScript derived constructors must invoke `super()` before using `this`, because the parent constructor establishes the derived object's initialized instance context.

The C++ asset hierarchy uses constructor initialization lists. `Laptop` and `Server` invoke the protected `Asset` constructor before initializing their own fields. This is significant in C++ because base-class construction occurs before derived-class construction.

The Java implementation uses constructor validation and an immutable `EmployeeBadge` record. A badge is treated as a value object, so its constructor rejects an empty identifier and a missing department.

A constructor should validate values that are essential to the object's identity or invariants. Delaying such validation creates objects that can fail much later and makes debugging harder.

## Inheritance

Inheritance expresses an **is-a** relationship.

A `SavingsAccount` is an `Account`. A `BusinessAccount` is an `Account`. A `Laptop` is an `Asset`. An `Engineer` is an `Employee`.

The base class should contain behavior genuinely common to its derived classes. Specialized behavior belongs in the derived class.

The Python implementation uses `Account` as an abstract base class. `monthly_charge()` is abstract because the base class cannot provide a meaningful account-specific implementation. `SavingsAccount` and `BusinessAccount` implement the operation according to their own domain rules.

The C++ implementation uses a pure virtual interface through `Asset::category()`, `Asset::annualCost()`, and `Asset::printDetails()`. Calls through an `Asset*` or `Asset&` therefore use virtual dispatch to reach the appropriate derived implementation.

Java uses an abstract `Employee` class with abstract `roleDescription()` and `annualBonus()` methods. `Engineer` and `Manager` provide different implementations while sharing salary, identity, lifecycle, and badge behavior.

JavaScript demonstrates inheritance through `extends`. `Engineer` and `Manager` reuse `Employee` behavior and override `describe()` where their domain-specific description differs.

Inheritance should not be used merely to avoid typing duplicate code. It is most appropriate when the derived type genuinely satisfies the behavioral contract of the base type.

## Private Fields and Encapsulation

Private fields protect invariants by controlling how internal state can be changed.

The Python account's `__balance` is private through Python's name-mangling convention. The public `balance` property exposes controlled read access, while balance changes occur through methods such as `deposit()` and `_change_balance()`.

The JavaScript implementation uses true language-level private fields such as `#salary`, `#name`, `#active`, and `#team`. These cannot be accessed with normal property syntax outside the declaring class.

Java declares fields such as `employeeId`, `name`, `salary`, and `status` as `private`. Public methods expose specific operations without exposing unrestricted mutation.

C++ uses private data members such as `id_`, `owner_`, and `active_`. The class exposes controlled methods such as `deactivate()` instead of permitting callers to directly modify lifecycle state.

Encapsulation is particularly useful when a field has an invariant. A balance cannot safely be changed to an arbitrary negative number. An employee status cannot safely transition from `TERMINATED` back to `ACTIVE`. A registry identifier should not be arbitrarily replaced after construction.

## Static Members

Static members exist at class scope.

An instance field creates separate storage or state for every object. A static field is associated with the class and is shared by its instances.

The examples use static members for information such as:

- ID generation, where the next identifier is shared by every object.
- Active-object counters, where the class tracks how many objects are currently active.
- Configuration values such as an interest rate or transaction fee.
- Utility operations that do not require instance state.

The Python `Account.normalize_currency()` method is a static method because it needs neither a particular account nor the `Account` class state. The Python `Account.active_accounts()` method is a class method because it operates on class-level state.

JavaScript uses `static normalizeSalary()` and static properties such as `Employee.nextId`. Static methods are called on the class rather than on an employee object.

C++ uses `inline static` data members, which are initialized as class-level storage and accessed through the class name.

Java uses private static counters and public static accessor methods. The counter belongs to the `Employee` class, not to one employee.

Static state must be treated carefully because every object shares it. A bug in a static counter can affect the behavior observed by every instance.

## Python Implementation

The Python program develops a banking domain model.

`Account` is the base abstraction. Its constructor creates an account identifier, validates the owner and starting balance, and increments the class-level active-account counter.

`SavingsAccount` inherits from `Account` and introduces a minimum balance and interest rate. Its `apply_interest()` method changes the private balance through a controlled protected helper.

`BusinessAccount` introduces a transaction fee and a transfer operation. This behavior is intentionally different from the savings-account interest mechanism, so inheritance does not become a repetition of the same operation under different names.

`AuditedAccount` adds a second inheritance level. It extends business-account transfer behavior and records an audit event after a successful transfer.

The `Customer` dataclass demonstrates composition. A customer owns a tuple of account objects, and `total_balance` derives information from those objects.

The script also demonstrates constructor failure, invalid deposits, insufficient funds, operations on closed accounts, static normalization, class-level counters, and polymorphic calls to `monthly_charge()`.

## JavaScript Implementation

The JavaScript program models employees.

`Employee` owns private identity, salary, and lifecycle fields. Its constructor validates input and establishes the initial active state.

`Engineer` inherits from `Employee` and adds a private specialization. `Manager` inherits from the same base class but introduces a private `Set` containing direct reports.

The use of `Set` is important in the manager model because it prevents the same employee object from being inserted repeatedly into the team.

Static members include the organization name, employee identifier sequence, active employee count, and salary-normalization behavior.

The program also introduces an event bus using a private `Map` of event handlers. This complements the class model by showing how objects can publish domain events without exposing their internal fields.

The event-driven example emits a `salaryChanged` event after a raise. The employee object remains responsible for its salary invariant, while the event bus is responsible for dispatching notifications.

Validation covers empty names, invalid salaries, missing engineering specialization, and incorrect event-handler values.

## C++ Enterprise Case Study

The C++ program models an enterprise equipment registry.

`Asset` is an abstract base class. Its private identity, owner, and lifecycle fields cannot be directly modified by registry users. A protected constructor establishes the shared asset state, while derived classes provide asset-specific behavior.

`Laptop` contains an operating system and memory capacity. `Server` contains CPU cores and storage capacity. Their annual costs are calculated differently, demonstrating meaningful polymorphism rather than superficial inheritance.

The `AssetRegistry` owns assets through `std::unique_ptr`. This is a deliberate ownership decision: the registry controls the lifetime of the objects, and automatic destruction prevents manual memory-management errors.

An `unordered_map` provides efficient identifier-based lookup. The inventory is copied into a temporary vector and sorted by asset identifier for deterministic output.

Static members track the next identifier and active-asset count. The active count changes when assets are constructed or deactivated.

The case study also demonstrates deleted copy construction and assignment for `Asset`. An asset has identity and controlled lifecycle state, so accidental copying would be undesirable.

Validation rejects empty owners, invalid server capacity, null assets, unknown identifiers, and repeated lifecycle transitions.

## Java Enterprise Domain Model

The Java implementation models employees as an enterprise domain.

`Employee` is an abstract base class containing common identity, salary, lifecycle, and badge state. Its fields are private and its lifecycle methods enforce valid state transitions.

`Engineer` and `Manager` provide specialized role behavior. Both implement the `Reviewable` interface, but their production-approval capabilities depend on different organizational rules.

The `EmployeeBadge` record is an immutable value object. Records are appropriate when identity is based on the contained values rather than on mutable object lifecycle.

`Manager` uses a mutable `List<Employee>` for direct reports but exposes it through `Collections.unmodifiableList()`. The manager therefore controls how assignments are changed without exposing unrestricted modification of its internal collection.

`PayrollService` demonstrates service-oriented behavior outside the entity classes. It calculates aggregate bonuses and checks whether an eligible production approver exists.

The implementation uses Java 17 language and standard-library features without third-party dependencies.

## PostgreSQL Representation

The SQL implementation treats object-oriented metadata as relational data.

`class_definition` stores class identity, parent-class relationships, abstract status, and descriptions. The self-referencing `parent_class_id` represents inheritance.

`class_member` distinguishes instance fields, static fields, instance methods, and static methods. Visibility is stored separately so that private, protected, and public members are not confused with their storage scope.

`object_instance` represents objects created from concrete classes.

`instance_field_value` stores values associated with individual objects. `static_field_value` stores values associated with a class. This separation directly models the difference between instance state and class state.

The `class_method` table records whether a method is static and whether it is abstract.

A recursive common table expression constructs the inheritance hierarchy. The `effective_class_members` view then exposes inherited members without physically duplicating the parent members into every child class.

The schema uses primary keys, foreign keys, unique constraints, check constraints, and indexes. Foreign keys prevent references to nonexistent classes or objects. Unique constraints prevent duplicate member names within the same class. Check constraints ensure that fields requiring a data type have one.

The transaction near the end of the script demonstrates a controlled object lifecycle change. The business-account object is moved to an inactive state and its stored balance is changed within one transaction.

## Relationship Between the Four Core Mechanisms

These mechanisms solve different problems.

| Mechanism | Main responsibility | Example |
| --- | --- | --- |
| Class | Defines shared structure and behavior | `Account`, `Employee`, `Asset` |
| Constructor | Establishes valid initial state | `SavingsAccount("Asha Sharma", 5000)` |
| Inheritance | Reuses and specializes a compatible base contract | `SavingsAccount` extends `Account` |
| Private field | Protects internal representation | `#salary`, `__balance`, `private salary` |
| Static member | Stores class-level state or behavior | `Employee.activeEmployees` |

A constructor does not make a member static. A private field does not imply inheritance. Inheritance does not automatically make derived fields private. Static members are shared independently of the number of instances.

The mechanisms can work together. A derived-class constructor can call a base constructor, initialize private derived state, and rely on inherited methods. A static counter can track instances while private instance fields preserve the state of each individual object.

## State and Lifecycle Rules

Good class design is closely connected to state validity.

The banking model does not allow a closed account to accept deposits. The employee model does not allow a terminated employee to receive a salary increase. The asset model does not permit an already inactive asset to be deactivated again.

These restrictions are implemented as methods rather than as unrestricted field assignments.

A lifecycle method therefore represents a permitted state transition:

`ACTIVE -> INACTIVE`

or:

`ACTIVE -> TERMINATED`

The reverse transition is intentionally absent where the domain does not permit it. This makes illegal states harder to create.

## Polymorphism

Polymorphism allows client code to operate through a base abstraction while the runtime selects the appropriate derived implementation.

In Python, a list of `Account` objects can contain `SavingsAccount`, `BusinessAccount`, and `AuditedAccount` objects. Calling `monthly_charge()` invokes the implementation associated with the actual object.

C++ uses virtual functions for runtime dispatch through the `Asset` abstraction.

Java uses abstract methods in `Employee` and dispatches `roleDescription()` and `annualBonus()` according to the concrete subclass.

JavaScript uses overridden methods such as `describe()` and calls them through employee references.

Polymorphism is valuable when the caller needs a common capability but should not depend on every concrete implementation.

## Validation and Failure Handling

Class invariants should be enforced close to the state they protect.

The implementations reject:

- Empty identity values where identity is required.
- Negative monetary values.
- Invalid minimum balances.
- Missing specialization information.
- Invalid hardware capacity.
- Invalid lifecycle transitions.
- Attempts to operate on inactive objects.
- Unknown objects in registries.
- Duplicate relationships where the domain prohibits them.

Exceptions are used where an operation cannot be completed while preserving the domain invariant.

Validation should not be limited to user-interface input. Domain classes themselves need validation because they may be called from multiple parts of an application.

## Design Trade-offs

Inheritance is useful when the derived type genuinely conforms to the base abstraction. Excessive inheritance can create rigid hierarchies in which unrelated behavior becomes coupled.

Private fields improve control over state, but excessive encapsulation can produce classes with large numbers of trivial accessors. A useful design exposes meaningful domain operations rather than exposing every internal variable.

Static members are appropriate for class-wide constants, counters, and utility operations. Mutable static state can become difficult to test because multiple objects share it.

Constructors are effective for mandatory initialization. Complex workflows that require many external dependencies are often better represented by factories or services rather than by constructors that perform substantial application work.

The SQL model demonstrates another trade-off: relational databases do not directly provide the same object model as an object-oriented language. The schema therefore represents classes, inheritance, fields, methods, and instances explicitly as relational entities.

## Performance Considerations

Class construction is normally inexpensive, but constructors that perform database access, network operations, or expensive computation can make object creation unpredictable.

Private fields themselves are primarily an encapsulation mechanism. Performance should not be assumed from their visibility level alone.

Inheritance introduces a hierarchy that can simplify polymorphic design but may increase conceptual complexity. In C++, virtual dispatch has runtime implications, though the cost should be evaluated against the actual workload rather than assumed to be significant.

The C++ registry uses `unordered_map` for average constant-time identifier lookup and `unique_ptr` for ownership. Sorting the inventory for presentation requires `O(n log n)` time, while registry insertion and lookup are expected `O(1)` on average.

The SQL indexes target actual access patterns: parent-class traversal, member lookup, object status filtering, and field-value lookup.

## Security and Robustness

Private fields are useful for preventing accidental state modification, but application-level privacy should not be confused with security boundaries.

Sensitive values should not be exposed merely because a getter exists. Domain methods should expose only the operations appropriate to the caller's responsibility.

Static mutable state should also be treated carefully in concurrent applications. Shared counters require appropriate synchronization when multiple threads can construct or deactivate objects concurrently.

The Java and C++ examples deliberately centralize lifecycle changes inside methods. This reduces the number of locations that can create inconsistent state.

Database constraints provide another enforcement layer. Application validation is useful, but relational integrity should not depend exclusively on every application path remembering the same rule.

## Practical Distinctions

A **constructor** answers: "How does this object become valid when created?"

A **private field** answers: "Who is allowed to manipulate this internal representation directly?"

An **inherited method** answers: "Which behavior can a derived type reuse or specialize from its parent?"

A **static member** answers: "Which state or behavior belongs to the class rather than one particular object?"

Keeping these questions separate produces clearer class designs. A constructor establishes state, private members protect state, inheritance organizes compatible types, and static members represent class-wide behavior or information.
