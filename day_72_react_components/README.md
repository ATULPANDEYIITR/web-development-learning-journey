# React Components: Functional Components, Props, Composition and Reusability

## 1. Domain and Architecture

React components are independent, reusable units of interface construction. A component receives input properties, produces an interface description, and can participate in a larger component hierarchy.

The functional component model uses JavaScript functions to define interface elements. Components can receive properties, manage state, respond to events, and compose other components.

The five source implementations explore component architecture through different engineering perspectives:

| File | Implementation perspective | Main responsibility |
|---|---|---|
| Python | Component-system simulation | Definitions, property validation and recursive rendering |
| JavaScript | React application architecture | Functional components, props, hooks and interactive composition |
| C++17 | Component engine | Registry, type checking and composition validation |
| Java 17 | Enterprise component architecture | Immutable domain types, services and lifecycle management |
| PostgreSQL | Relational component catalog | Versions, properties, dependencies and usage reporting |

The implementations share a component-oriented domain model but are not intended to be identical implementations of the same runtime.

## 2. Functional Components

A functional component is a JavaScript function that receives properties and returns React elements.

A conceptual component hierarchy is:

    Application
       |
       +-- Dashboard
              |
              +-- Card
              |     |
              |     +-- Text
              |     +-- Badge
              |     +-- Button
              |
              +-- ProjectList
                     |
                     +-- ProjectCard
                            |
                            +-- StatusBadge
                            +-- ActionButton

Each component has a defined responsibility.

For example:

- `Text` displays textual content.
- `Badge` communicates a status.
- `Button` represents an interactive action.
- `Card` groups related interface elements.
- `ProjectCard` combines smaller components into a meaningful application element.
- `ProjectDashboard` coordinates the application state and component hierarchy.

Functional components encourage separation of presentation and application logic.

A component should have a clear responsibility, predictable inputs, and controlled side effects.

### Component characteristics

| Characteristic | Meaning |
|---|---|
| Function-based | Defined using a JavaScript function |
| Reusable | Can appear in multiple interface locations |
| Composable | Can contain other components |
| Declarative | Describes the desired interface |
| Parameterized | Receives information through props |
| Stateful when necessary | Can manage local state using hooks |
| Testable | Can be checked independently |

## 3. Props: Component Inputs

Props, short for properties, are the inputs supplied by a parent component to a child component.

They allow the same component implementation to represent different information.

For example, a `Badge` component can represent:

- Active
- Paused
- Pending
- Failed

The component implementation remains reusable while its properties determine the displayed information.

### Important prop characteristics

**1. Data passing**

A parent component supplies values to a child component.

**2. One-way data flow**

Props flow from parent to child. A child should not directly modify the parent's properties.

**3. Default values**

A component can define fallback values when optional properties are not supplied.

**4. Required properties**

Components can require specific properties to operate correctly.

**5. Property validation**

Validation checks whether supplied values meet the component contract.

**6. Callback properties**

A parent can pass a function to a child, allowing the child to communicate user interactions to the parent.

### Props and state are different

| Props | State |
|---|---|
| Supplied by the parent | Managed by the component |
| Read-only from the receiving component's perspective | Updated through state-management mechanisms |
| Communicate external input | Represent changing component data |
| Support parent-child communication | Support interactive behavior |

Props should not be used as a substitute for state.

For example, a project card receives its project information through props, while the dashboard manages whether that project is active.

## 4. Component Composition

Composition means building larger components from smaller components.

Instead of creating one large component responsible for an entire application, developers combine focused components.

The Python, C++17 and Java implementations model this using component nodes, definitions, registries and recursive rendering.

The JavaScript implementation uses actual React element composition.

### Example composition structure

    ProjectDashboard
        |
        +-- Card
        |    |
        |    +-- Text
        |    +-- Badge
        |    +-- Button
        |
        +-- ProjectList
             |
             +-- ProjectCard
                  |
                  +-- Badge
                  +-- Button

### Parent and child relationships

A parent component owns the composition of its children.

A child component can receive:

- Display information
- Configuration properties
- Callback functions
- Children supplied by its parent

The parent controls the larger composition, while each child handles its own defined responsibility.

### Children property

React supports composition through the special `children` property.

A container component can accept different content without needing to know the implementation details of that content.

This makes components more flexible than components that contain fixed internal layouts.

### Conditional composition

Conditional rendering determines whether a component or part of a component hierarchy should appear.

Typical conditions include:

- Whether a user is authenticated
- Whether a record exists
- Whether a project is active
- Whether an operation is loading
- Whether an error has occurred

The JavaScript implementation uses a `Conditional` component to demonstrate this behavior.

The Python and Java models also demonstrate conditional content selection.

## 5. Reusable Components

A reusable component provides a consistent interface for multiple application locations.

For example, a common `Button` component can be reused for:

- Saving information
- Opening records
- Submitting forms
- Activating projects
- Cancelling operations

The behavior and appearance can be configured through properties.

### Reusability principles

- Keep component responsibilities focused.
- Prefer explicit property contracts.
- Use composition rather than unnecessary duplication.
- Avoid unnecessary application-specific assumptions.
- Provide sensible defaults.
- Keep state ownership clear.
- Use stable keys when rendering collections.
- Avoid modifying properties received from parents.

### Component reuse and abstraction

Reusability does not mean every component should support every possible behavior.

Excessive configuration makes components difficult to understand and maintain.

A reusable component should expose only the properties required by its intended responsibility.

For example, a status badge should not contain project database operations or application navigation logic.

## 6. Component Registry and Contracts

The Python, C++17 and Java programs implement a component registry.

A registry stores component definitions and allows the rendering engine to locate them by name.

A component definition contains:

- Component name
- Description
- Property schema
- Required-property rules
- Default values
- Child composition rules
- Rendering behavior
- Lifecycle status where applicable

The registry separates component registration from component usage.

### Property contract

A property contract specifies the accepted inputs.

| Property type | Example | Purpose |
|---|---|---|
| String | `"Save"` | Text and labels |
| Number | `12` | Numeric values |
| Boolean | `true` | Conditions and flags |
| Object | `{}` | Structured information |
| Array | `[]` | Collections |
| Function | Callback | Event communication |
| Node | React element | Composable interface content |
| Any | Variable type | Flexible input |

The Python implementation supports strings, numbers, booleans, objects and arrays.

The C++17 implementation uses a `std::variant` for string, numeric and boolean values.

The Java implementation uses explicit property types and immutable records.

The PostgreSQL implementation stores property definitions and values using relational columns and JSONB.

### Default and required properties

A required property must be supplied.

An optional property may be omitted.

A property with a default value receives that value when no explicit value is supplied.

The implementations reject conflicting required and default configurations.

## 7. React Hooks and State Management

React Hooks allow functional components to use state and other React capabilities.

The JavaScript implementation demonstrates three important hooks.

### useState

`useState` manages component state.

The dashboard uses it to maintain project records and the selected filter.

When a state update occurs, React schedules a new render.

State should be updated through its setter rather than by directly modifying existing objects.

### useCallback

`useCallback` preserves a function reference between renders when its dependencies have not changed.

The project dashboard uses it for the project activation handler.

It is useful when stable function references matter, such as when passing callbacks to memoized children.

### useMemo

`useMemo` caches a calculated value between renders when its dependencies remain unchanged.

The dashboard uses it to calculate filtered project records.

Memoization should be applied when it provides a practical performance benefit. It is not required for every calculation.

### State ownership

State should normally be maintained by the lowest common ancestor that needs to coordinate the affected components.

For the project dashboard:

    ProjectDashboard
         |
         +-- Project state
         |
         +-- Filter state
         |
         +-- ProjectCard
                |
                +-- Receives project props
                +-- Sends action callback

The parent owns project state. Individual cards receive project information and communicate actions through callback properties.

## 8. Event Handling and Interaction

React components can receive event-handler functions through props.

The JavaScript implementation demonstrates event handling using button callbacks.

The project card does not directly modify the dashboard's project collection.

Instead:

1. The user activates a button.
2. The child invokes the supplied callback.
3. The parent identifies the relevant project.
4. The parent creates an updated state value.
5. React renders the updated component hierarchy.

This structure separates event initiation from state ownership.

### Event-handling considerations

- Use the correct event handler.
- Avoid modifying state directly.
- Keep callback responsibilities focused.
- Validate external input.
- Disable unavailable actions where appropriate.
- Handle asynchronous failures when components perform network operations.
- Avoid duplicate submissions when an operation is already running.

The sample project dashboard uses local state and does not perform network requests.

## 9. Lists and Component Identity

React applications frequently render collections of reusable components.

For example, a project dashboard can render multiple project cards from an array.

Each rendered item should have a stable and unique key.

A key allows React to identify elements between renders and reconcile changes correctly.

The JavaScript `List` component uses the project identifier as the key.

Avoid using array indexes as keys when collection ordering or membership can change.

Keys are reconciliation identifiers. They are not automatically supplied as ordinary component props.

## 10. Component Validation and Error Handling

Component contracts help detect incorrect usage before rendering.

The implementations demonstrate several failure conditions.

| Failure | Example | Expected handling |
|---|---|---|
| Missing property | Button without label | Reject validation |
| Invalid type | Boolean supplied as text | Reject validation |
| Unknown property | Unsupported configuration | Reject validation |
| Missing component | Unregistered component name | Raise an error |
| Invalid composition | Child added to a component that rejects children | Reject composition |
| Circular dependency | Component recursively contains itself | Reject composition |
| Deprecated component | Attempt to activate a deprecated component | Reject lifecycle transition |

### Property immutability

Props should be treated as read-only inputs.

The Java implementation uses immutable maps and records.

The Python component definitions use dataclasses, including frozen property definitions.

The C++ implementation separates component definitions from supplied properties.

The JavaScript implementation uses immutable state-update patterns.

### Circular composition

Circular composition occurs when component dependencies eventually refer back to an ancestor.

For example:

    Component A
        |
        +-- Component B
                |
                +-- Component C
                        |
                        +-- Component A

Such a structure cannot be rendered safely using ordinary recursive traversal.

The Python, C++17 and Java implementations detect circular component composition.

The PostgreSQL implementation uses a recursive query in its composition trigger to reject dependency cycles.

## 11. Component Lifecycle and Version Management

The Java implementation models component lifecycle states:

| State | Meaning |
|---|---|
| REGISTERED | Definition exists in the registry |
| ACTIVE | Component is available for rendering |
| DEPRECATED | Component should not be used for new development |

The PostgreSQL implementation provides a more detailed catalog lifecycle:

- Draft
- Registered
- Active
- Deprecated
- Retired

Version management is important when reusable components are shared across applications.

A component update may introduce:

- New optional properties
- New default values
- Changed rendering behavior
- Removed properties
- Changed property types
- Breaking interface changes

A versioned component catalog helps applications identify which implementation they depend on.

A breaking change should not silently alter the behavior of applications that depend on an earlier version.

## 12. Implementation Architecture

### Python

The Python program provides a component-system simulator.

Its principal classes are:

| Class | Responsibility |
|---|---|
| `PropDefinition` | Defines a property contract |
| `ComponentNode` | Represents a component instance |
| `ComponentDefinition` | Describes a reusable component |
| `ComponentRegistry` | Stores component definitions |
| `ComponentRenderer` | Validates and renders component trees |

The renderer recursively processes child nodes.

It checks component registration, validates supplied properties, applies defaults and rejects invalid composition.

The program also writes the rendered component hierarchy to a JSON file.

### JavaScript

The JavaScript program provides an actual React application architecture.

It contains:

| Component or class | Responsibility |
|---|---|
| `Text` | Displays text |
| `Badge` | Displays status |
| `Button` | Handles user actions |
| `Card` | Composes content |
| `Conditional` | Controls conditional rendering |
| `List` | Renders collections |
| `ProjectCard` | Represents a project |
| `ProjectDashboard` | Owns application state |
| `ComponentRegistry` | Registers reusable component definitions |

The application demonstrates React functional components, property passing, callbacks, state updates, filtering and nested composition.

The registry and validation factory provide an additional component-contract demonstration. They are application-level validation mechanisms rather than replacements for React's own rendering and validation behavior.

### C++17

The C++17 program models a component engine.

Its main structures include:

- `PropDefinition`
- `ComponentNode`
- `ComponentDefinition`
- `RenderedNode`

Its main classes are:

- `ComponentRegistry`
- `ComponentEngine`

The property system uses `std::variant` for supported property values.

A recursive rendering engine processes the component tree and maintains an ancestor set for cycle detection.

This implementation emphasizes explicit types, deterministic validation and controlled memory ownership through smart pointers.

### Java 17

The Java program models enterprise component architecture.

Its important types include:

- `PropDefinition` record
- `ComponentNode` record
- `RenderedComponent` record
- `ComponentDefinition`
- `ComponentRegistry`
- `PropValidator`
- `ComponentService`
- `ComponentRenderer` interface

The implementation uses immutable collections, explicit lifecycle states, custom exceptions and service-based validation.

The component service separates component registration, property validation and rendering responsibilities.

### PostgreSQL

The SQL implementation models a persistent component catalog.

Its principal tables are:

| Table | Responsibility |
|---|---|
| `components` | Component identity and lifecycle |
| `component_versions` | Versioned definitions |
| `component_props` | Property contracts |
| `component_compositions` | Parent-child dependencies |
| `applications` | Application registration |
| `component_instances` | Actual component configurations |
| `component_usage_events` | Rendering and performance events |

Additional database mechanisms include:

- Primary and foreign keys
- Unique and check constraints
- JSONB property storage
- Indexes for catalog retrieval
- Timestamp triggers
- Version validation triggers
- Circular dependency prevention
- Property validation functions
- Instance validation procedures
- Recursive dependency queries
- Usage and performance views
- Transactional sample-data setup

## 13. Database Validation and Workflow

The database workflow separates component definitions from component instances.

A component definition describes what can be instantiated.

A component instance contains the configuration supplied by an application.

The validation process follows:

    Component Definition
           |
           v
    Component Version
           |
           v
    Property Schema
           |
           v
    Component Instance
           |
           v
    Supplied Properties
           |
           v
    Property Validation
           |
           +---- Invalid ----> Failed
           |
           v
       Validated
           |
           v
        Rendered

The database procedure resolves default properties and rejects missing required properties, incorrect JSON types and unknown properties.

The sample transaction creates valid component instances and an intentionally invalid instance to demonstrate failure handling.

## 14. Performance Considerations

Component performance depends on rendering frequency, component-tree size, property processing, state ownership and reconciliation.

Important considerations include:

- Keep component trees reasonably shallow.
- Avoid unnecessary component duplication.
- Use stable keys for collection rendering.
- Avoid unnecessary state updates.
- Apply memoization when measurements justify it.
- Keep expensive calculations outside frequently executed rendering paths where appropriate.
- Avoid excessive component configuration.
- Keep registry lookups efficient.
- Avoid repeatedly validating unchanged static definitions.
- Index frequently accessed component versions and dependencies.

The Python, C++17 and Java implementations use map-based registries for efficient component lookup.

The PostgreSQL implementation indexes component identity, versions, dependencies, instances and usage events.

For a component tree with \(V\) nodes and \(E\) parent-child relationships, recursive tree traversal takes \(O(V+E)\) time. For a tree, \(E=V-1\), so traversal is linear in the number of nodes.

Registry lookup using a hash map is expected \(O(1)\), while ordered map lookup is \(O(\log V)\).

Cycle detection depends on the graph traversal strategy and the number of dependencies examined.

## 15. Security and Reliability

Reusable components are part of the application interface and should follow secure implementation practices.

Important controls include:

- Validate externally supplied property values.
- Do not assume browser input is trustworthy.
- Avoid rendering untrusted HTML.
- Do not construct executable code from property values.
- Avoid placing confidential information in client-side props.
- Keep authorization decisions in trusted application services.
- Validate callback inputs before performing sensitive actions.
- Avoid exposing internal error details to end users.
- Use database constraints to protect persistent component definitions.
- Apply appropriate database privileges.
- Keep version updates controlled and traceable.

The JavaScript implementation uses React's normal text rendering behavior and does not use raw HTML injection.

The SQL implementation validates property structure and types. Production deployments should further constrain JSON values, use parameterized application queries and apply appropriate database permissions.

The Python and native implementations are architectural simulators. They do not replace a browser security model or a production React runtime.

## 16. Limitations and Design Boundaries

The implementations intentionally have different scopes.

| Implementation | Important limitation |
|---|---|
| Python | Simulates component rendering rather than using React |
| JavaScript | Uses React but does not implement a production backend |
| C++17 | Models component structures without browser rendering |
| Java 17 | Simulates enterprise component services rather than React execution |
| PostgreSQL | Stores and validates component metadata rather than rendering interfaces |

The JavaScript implementation requires React and React DOM. The Python, C++17 and Java implementations do not require third-party dependencies.

The database schema stores function and node property categories as metadata. Executable JavaScript functions and live React elements must remain in the application runtime rather than being serialized as ordinary JSON values.

The database's component composition model is a catalog-level dependency model, not a complete replacement for React's runtime component tree.

## 17. Execution and Testing

### Python

Run the script using Python 3:

- Executes the component registry.
- Validates component properties.
- Builds a nested dashboard.
- Runs invalid-property and circular-composition tests.
- Prints the rendered component tree.
- Writes `component_output.json` in the working directory.

### JavaScript

Install React and React DOM in a Node.js project.

The application requires a browser page containing an element with the ID `root`.

The script runs validation tests and mounts the dashboard using React DOM's `createRoot`.

It can also export the component definitions and registry for use in other modules.

### C++17

Compile using a C++17-compatible compiler.

The program:

- Registers component definitions.
- Validates property types.
- Tests missing and unknown properties.
- Detects invalid child composition.
- Detects circular dependencies.
- Prints the component hierarchy.

### Java 17

Compile the `ReactComponentArchitecture.java` file with Java 17.

Run the `ReactComponentArchitecture` class.

The program registers components, activates definitions, validates component instances and displays the enterprise component hierarchy.

### PostgreSQL

Execute the SQL script against a PostgreSQL database.

The script creates the `react_catalog` schema, tables, constraints, functions, procedures, triggers, views and sample data inside a transaction.

The validation workflow intentionally records an invalid component instance as failed while preserving valid component instances.

## 18. Practical Engineering Principles

The implementations establish several important distinctions:

| Concept | Responsibility |
|---|---|
| Functional component | Defines a reusable interface unit |
| Props | Supplies input to a component |
| State | Maintains changing component data |
| Composition | Builds larger interfaces from smaller components |
| Children | Supplies nested content to a parent |
| Callback | Communicates an event or action |
| Registry | Stores component definitions |
| Property schema | Defines accepted component inputs |
| Component instance | Represents a configured use of a component |
| Component version | Identifies a particular component definition |
| Validation | Rejects invalid component configuration |
| Lifecycle | Controls component availability |

The central architectural principle is separation of responsibilities.

Components should have focused behavior, explicit inputs and predictable composition. Parent components should coordinate shared state, while reusable child components should remain independent of unrelated application logic.

This approach supports maintainable interfaces, consistent component behavior, controlled changes and systematic validation across application boundaries.
