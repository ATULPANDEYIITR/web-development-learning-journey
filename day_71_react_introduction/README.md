# React Introduction: Component Architecture, JSX, Virtual DOM and Rendering

## 1. Technical Scope

React is a JavaScript library for building user interfaces through reusable components. It organizes interface functionality into smaller units, manages changing application data, and coordinates updates to the browser DOM.

This project examines four connected concepts:

| Concept | Primary responsibility |
|---|---|
| Component architecture | Organizes an interface into reusable units |
| JSX | Provides declarative syntax for describing interface structures |
| Virtual DOM | Represents interface output as an in-memory tree |
| Rendering | Converts component output into browser-visible interface elements |

These concepts operate together but perform different functions.

A component defines a portion of the interface. JSX describes the structure produced by components. React evaluates component output and reconciles changes. The rendering system applies the resulting updates to the appropriate browser or rendering environment.

## 2. Component Architecture

### 2.1 Components

A component is a reusable unit of interface functionality.

Typical components include:

- Application headers
- Navigation bars
- Forms
- Buttons
- Tables
- Cards
- Search interfaces
- Dialogs
- Dashboards
- Interactive counters

Components allow large interfaces to be divided into smaller units with defined responsibilities.

A well-designed component generally has:

- A clear purpose.
- A predictable input contract.
- Controlled access to its data.
- A defined rendering responsibility.
- Limited dependence on unrelated components.

### 2.2 Component composition

Composition means combining smaller components to create larger interface structures.

Example architecture:

    App
    |
    +-- Header
    |
    +-- ConceptList
    |   |
    |   +-- ConceptCard
    |   +-- ConceptCard
    |   +-- ConceptCard
    |   +-- ConceptCard
    |
    +-- Counter
    |
    +-- SearchableConcepts

The root component coordinates the application. The header displays application information. The concept list organizes multiple cards. The counter maintains interactive state.

This approach avoids placing an entire application inside one large component.

### 2.3 Functional components

Modern React applications commonly use function components.

A function component receives properties and returns React elements.

Important characteristics:

- Components are reusable.
- Components can receive properties.
- Components can contain other components.
- Components can use Hooks.
- Components participate in React rendering.

A component should normally remain focused on a specific interface responsibility.

### 2.4 Props

Props are inputs passed from a parent component to a child component.

For example:

    App
      |
      +-- ConceptCard
              |
              +-- title
              +-- description
              +-- category

The parent supplies the values. The child uses them to determine its output.

Props are read-only from the receiving component's perspective. A child should not directly modify its parent's properties.

### 2.5 Component reuse

A single component definition can render multiple instances.

For example, a `ConceptCard` component can display:

| Instance | Title |
|---|---|
| 1 | Component Architecture |
| 2 | JSX |
| 3 | Virtual DOM |
| 4 | Rendering |

Each instance receives different properties while sharing the same component implementation.

Reuse improves consistency and reduces duplicated interface logic.

## 3. JSX

### 3.1 Meaning

JSX stands for JavaScript XML.

It is a syntax extension that allows developers to describe interface structures using markup-like expressions inside JavaScript.

JSX is not HTML. It is transformed into JavaScript expressions that create React elements.

For example, a JSX heading describes a React element. The corresponding JavaScript can use `React.createElement`.

Conceptually:

    JSX
      |
      v
    JavaScript transformation
      |
      v
    React element
      |
      v
    Component rendering

### 3.2 JSX characteristics

JSX supports:

- Nested elements.
- JavaScript expressions.
- Component references.
- Conditional rendering.
- List rendering.
- Attribute expressions.
- Fragment syntax.

JavaScript expressions are enclosed in curly braces.

For example, an expression can supply a component property or determine which content is displayed.

### 3.3 JSX and HTML differences

| JSX | HTML |
|---|---|
| Uses `className` for CSS classes | Uses `class` |
| Uses `htmlFor` for label association | Uses `for` |
| Supports JavaScript expressions | Does not directly support JavaScript expressions in markup |
| Components can be represented with capitalized identifiers | HTML elements use standard element names |
| Supports React fragments | HTML does not have a general component fragment syntax |
| Event handlers use JavaScript functions | HTML event attributes have different conventions |

JSX attributes generally follow JavaScript naming conventions.

### 3.4 Expressions and conditional rendering

JSX can incorporate expressions to determine rendered content.

Conditional rendering allows components to display different output depending on application state.

Common approaches include:

- Conditional expressions.
- Logical AND expressions.
- Early returns.
- Separate components for different interface states.

For example, a counter can display a notification after its value reaches a specified threshold.

### 3.5 Rendering lists

JavaScript array methods, particularly `map()`, are commonly used to generate repeated elements.

Each rendered item should have a stable key.

Keys help React identify items across renders.

A stable database identifier is generally preferable to an array index when list entries can be inserted, deleted, or reordered.

## 4. Virtual DOM

### 4.1 Definition

The Virtual DOM is an in-memory representation of the interface structure.

React elements describe what should be rendered. React uses this information as part of its rendering and reconciliation process.

A conceptual virtual DOM node can contain:

| Field | Purpose |
|---|---|
| Type | Element, text, or fragment |
| Tag | Element type such as `div` or `section` |
| Props | Attributes and other element properties |
| Children | Nested elements or text nodes |
| Key | Identity information for elements in lists |

The Python, C++ and Java implementations explicitly model these structures.

### 4.2 Virtual DOM tree

Consider an application with a header, a list of cards, and a counter.

    Application
    |
    +-- Header
    |   |
    |   +-- Heading
    |
    +-- Section
    |   |
    |   +-- Article
    |   +-- Article
    |   +-- Article
    |
    +-- Counter
         |
         +-- Paragraph

This hierarchy represents the logical structure of the interface.

It is distinct from the actual browser DOM.

### 4.3 React elements and virtual DOM

React elements are lightweight descriptions of intended interface output.

They are not themselves browser DOM nodes.

The browser DOM contains actual document elements, attributes, and text nodes.

React uses element descriptions and its internal rendering mechanisms to determine how the browser DOM should change.

### 4.4 Reconciliation

Reconciliation is the process React uses to determine how a newly rendered element tree relates to the previous rendered tree.

The implementations in this project demonstrate a simplified comparison algorithm.

The comparison examines:

- Node types.
- Element types.
- Properties.
- Text content.
- Child positions.
- Added children.
- Removed children.

Conceptual operations include:

| Operation | Meaning |
|---|---|
| INSERT | Add a new child |
| REMOVE | Remove an existing child |
| REPLACE | Replace an incompatible node |
| UPDATE_TEXT | Change text content |
| UPDATE_PROPS | Change element properties |

The implementations use positional child comparison for instructional purposes. Production React reconciliation includes additional rules for component identity, element types, keys, and scheduling.

### 4.5 Keys and identity

Keys help React identify which list items remain the same between renders.

Consider:

    Before: A, B, C
    After:  C, A, B

Stable keys allow React to associate each item with its previous identity.

Without suitable keys, changes in list ordering can lead to incorrect state association or unnecessary work.

Array indexes are not suitable keys for many dynamic lists.

## 5. Rendering

### 5.1 Rendering definition

Rendering is the process through which React determines the interface output associated with a component.

A simplified workflow is:

    Application State
          |
          v
    Component Execution
          |
          v
    React Elements
          |
          v
    Reconciliation
          |
          v
    Rendering Updates
          |
          v
    Browser DOM

The browser DOM is the actual document structure displayed by the browser.

### 5.2 Initial rendering

Initial rendering creates the application interface inside a designated root element.

Modern React applications commonly use `createRoot()` from `react-dom/client`.

The root is responsible for managing the React application mounted within that container.

The JavaScript implementation uses this approach.

### 5.3 Subsequent rendering

A component can render again when relevant inputs change.

Common reasons include:

- Its state changes.
- Its parent renders with updated properties.
- A context value changes.
- An external subscription used by the component changes.

A render does not necessarily mean every browser DOM element is replaced.

React determines the required updates through reconciliation and its rendering system.

### 5.4 State-driven rendering

State represents information maintained by a component or another state-management mechanism.

The counter example demonstrates this relationship:

    User clicks button
          |
          v
    Event handler executes
          |
          v
    State update requested
          |
          v
    Component renders again
          |
          v
    Updated interface appears

In React, `useState` provides component state.

State updates should use the appropriate setter rather than modifying state variables directly.

When the next value depends on the previous value, the functional updater form is useful.

### 5.5 Event handling

React supports event-driven interfaces.

Common events include:

- Click.
- Change.
- Submit.
- Keyboard interaction.
- Focus.
- Blur.

The JavaScript implementation demonstrates click handlers, search input, category selection, and counter updates.

Event handlers should validate untrusted input and avoid unnecessary side effects during rendering.

## 6. React Hooks

Hooks provide access to React features from function components.

The JavaScript implementation uses three Hooks.

| Hook | Responsibility |
|---|---|
| `useState` | Maintains component state |
| `useMemo` | Caches a calculated value between renders when dependencies remain unchanged |
| `useCallback` | Caches a function reference between renders when dependencies remain unchanged |

### 6.1 useState

`useState` maintains a state value.

The counter uses this Hook to maintain its current number.

Calling its setter requests an update. React schedules the relevant rendering work.

### 6.2 useMemo

`useMemo` can cache the result of a calculation.

The searchable concept list uses it for:

- Building category options.
- Filtering concepts.

Memoization should be used when it provides a meaningful benefit. It does not automatically make every component faster.

### 6.3 useCallback

`useCallback` caches a function reference.

The counter uses it for increment, decrement, and reset operations.

This can be useful when stable function references matter to memoized child components or dependency-sensitive Hooks.

### 6.4 Hook rules

Hooks must follow React's Rules of Hooks.

- Call Hooks at the top level of function components or custom Hooks.
- Do not call Hooks conditionally.
- Do not call Hooks inside loops.
- Do not call Hooks inside ordinary nested functions.
- Keep Hook calls consistent between renders.

These rules allow React to associate Hook state with the correct component.

## 7. Detailed Implementation Architecture

The five source files provide different engineering perspectives on the same subject.

| File | Implementation responsibility |
|---|---|
| Python | Component registry, immutable virtual nodes, rendering and testing |
| JavaScript | Actual React components, JSX, Hooks and browser mounting |
| C++17 | Explicit virtual DOM representation and reconciliation |
| Java 17 | Enterprise-oriented component contracts and immutable rendering structures |
| PostgreSQL | Relational component registry, virtual DOM persistence and render operations |

### 7.1 Python implementation

The Python program provides an executable model of component composition and rendering.

Its principal structures are:

| Structure | Responsibility |
|---|---|
| `VNode` | Represents an immutable virtual node |
| `NodeType` | Distinguishes element, text and fragment nodes |
| `ComponentRegistry` | Registers and resolves components |
| `ComponentState` | Maintains application state |
| `RenderResult` | Stores rendered output and tree statistics |
| `compare_nodes()` | Identifies conceptual tree changes |
| `render_to_html()` | Produces escaped HTML |

The implementation uses dataclasses to represent virtual nodes and application state.

The component registry separates component definitions from application construction.

The HTML renderer escapes text and attribute values to prevent untrusted strings from being interpreted as executable markup.

The test suite checks:

- HTML escaping.
- Component rendering.
- State transitions.
- Virtual DOM comparison.
- Invalid component results.
- Invalid void-element children.
- Attribute escaping.

The Python implementation is an educational rendering simulation. It is not a replacement for the React runtime.

### 7.2 JavaScript implementation

The JavaScript file uses React directly.

Its application contains:

- `Header`
- `ConceptCard`
- `ConceptList`
- `Counter`
- `SearchableConcepts`
- `ApplicationErrorBoundary`
- `App`

The component tree demonstrates parent-child composition.

`ConceptCard` uses `memo()` to demonstrate component memoization.

`Counter` uses state and event handlers.

`SearchableConcepts` uses derived data and controlled input elements.

The application validates its concept records before using them.

An error boundary provides fallback interface output for rendering errors in descendant components.

The application mounts through `createRoot()`.

Unlike the other language implementations, this file uses the actual React rendering system rather than implementing a separate virtual DOM engine.

### 7.3 C++17 implementation

The C++ implementation emphasizes explicit data structures and controlled state management.

Its main structures include:

| Structure | Responsibility |
|---|---|
| `VNode` | Virtual DOM node |
| `NodeType` | Node classification |
| `Patch` | Reconciliation operation |
| `ComponentRegistry` | Component lookup and invocation |
| `CounterState` | Controlled application state |
| `Props` | Component property collection |

The program uses:

- `shared_ptr` for shared node ownership.
- `map` for deterministic property ordering.
- `unordered_map` for component lookup.
- `vector` for child collections.
- `set` for void HTML element identification.
- Exceptions for invalid operations.

The reconciliation engine compares two virtual trees and produces a list of conceptual patches.

This makes the difference between an interface description and a browser DOM update explicit.

### 7.4 Java 17 implementation

The Java implementation models a component system using explicit contracts and immutable data structures.

Its main structures include:

- `VNode`
- `Component`
- `ComponentRegistry`
- `CounterState`
- `Patch`
- `NodeType`
- `PatchType`

Java records represent patch operations.

The virtual node uses immutable property and child collections.

The component interface defines a consistent rendering contract.

The registry provides controlled component registration and lookup.

The counter uses synchronized state transitions to demonstrate basic thread-safe state access.

Java Streams are used for fragment rendering, component composition, and node counting.

The implementation also includes custom exceptions for component, rendering, and state failures.

### 7.5 PostgreSQL implementation

The database models the structural and operational information associated with a component-based application.

Its principal entities are:

| Table | Purpose |
|---|---|
| `applications` | Stores application metadata |
| `components` | Stores registered components |
| `component_props` | Defines component property contracts |
| `virtual_dom_trees` | Stores tree versions |
| `virtual_dom_nodes` | Stores virtual tree nodes |
| `component_dependencies` | Stores component composition relationships |
| `component_state` | Stores component state |
| `render_operations` | Records rendering operations |
| `dom_patches` | Stores conceptual reconciliation operations |

The database uses primary keys, foreign keys, unique constraints, checks, indexes, views, triggers, functions, procedures, and transactions.

The `update_component_state()` function implements optimistic concurrency through an expected version number.

The `complete_render()` procedure controls the transition from pending rendering to successful rendering.

The recursive dependency query demonstrates component hierarchy retrieval.

The dependency-cycle query identifies circular component relationships.

The performance view provides successful render counts, failure counts, and rendering duration statistics.

The SQL model is a persistence and reporting representation. It does not execute React or manipulate an actual browser DOM.

## 8. Distinguishing the Four Main Concepts

The four central concepts should not be treated as interchangeable.

| Dimension | Component Architecture | JSX | Virtual DOM | Rendering |
|---|---|---|---|---|
| Main purpose | Organize interface functionality | Describe interface structure | Represent interface output | Produce visible interface changes |
| Primary abstraction | Components | Syntax | In-memory representation | Rendering process |
| Main inputs | Component responsibilities and data | JavaScript expressions | React elements | Component output and application state |
| Main result | Reusable component hierarchy | Element descriptions | Element tree | Updated rendering environment |
| Primary concern | Maintainability and reuse | Declarative expression | Structural comparison | Interface updates |

Their relationship is sequential but not strictly linear in every React operation.

Components produce elements. JSX provides one way to describe those elements. React evaluates the resulting structures and coordinates rendering through its reconciliation and rendering systems.

## 9. State, Props and Derived Data

These three concepts have different responsibilities.

| Concept | Meaning | Example |
|---|---|---|
| Props | Inputs supplied to a component | Card title |
| State | Data maintained by a component | Counter value |
| Derived data | Values calculated from existing data | Filtered concept list |

A component should not use state when a value can be calculated reliably from existing props or state.

For example, the number of filtered concepts can be derived from the filtered array instead of being maintained as a separate state variable.

This avoids unnecessary synchronization problems.

## 10. Error Handling and Security

### 10.1 Input validation

Application data should be validated before rendering.

The JavaScript implementation verifies that concept records contain the expected fields and that identifiers are unique.

The Python, C++, and Java implementations validate component definitions, element tags, and rendering inputs.

### 10.2 Output escaping

Untrusted text should not be inserted into HTML without appropriate escaping.

For example:

    <script>alert(1)</script>

If treated as ordinary text, this content must not become an executable script element.

The Python, C++, and Java rendering simulations escape HTML-sensitive characters.

In React, ordinary text children are escaped by React's normal rendering mechanisms. Direct HTML insertion APIs require separate security controls.

### 10.3 Rendering errors

Component rendering can fail because of:

- Invalid input.
- Missing properties.
- Invalid element structures.
- Runtime exceptions.
- Unexpected application data.

React error boundaries can provide fallback UI for errors occurring during descendant rendering.

They do not replace validation, ordinary exception handling, or asynchronous error handling.

### 10.4 Resource management

Large component trees and repeated calculations can increase rendering costs.

Practical controls include:

- Keeping components focused.
- Avoiding unnecessary state.
- Using stable list keys.
- Avoiding expensive calculations during every render.
- Applying memoization selectively.
- Avoiding unnecessarily deep component hierarchies.
- Profiling before introducing optimization.

## 11. Performance Considerations

### 11.1 Component rendering

A component may render again when its relevant inputs change.

Unnecessary rendering can occur when parent components repeatedly create new object or function references.

`memo`, `useMemo`, and `useCallback` can help in appropriate situations, but they have their own comparison and memory costs.

### 11.2 Reconciliation complexity

The educational implementations compare corresponding nodes recursively.

For two similarly structured trees containing approximately N nodes, a complete comparison has a worst-case time complexity of O(N), excluding the cost of processing individual property collections.

The C++ and Java implementations use positional comparison.

They do not implement React's complete keyed reconciliation algorithm.

### 11.3 Large lists

Large lists can increase rendering and reconciliation work.

Useful techniques include:

- Stable keys.
- Pagination.
- List virtualization.
- Avoiding unnecessary list-level state.
- Filtering before rendering when appropriate.

### 11.4 Database performance

The PostgreSQL implementation includes indexes for:

- Component lookup.
- Tree hierarchy retrieval.
- Sibling positions.
- Render status reporting.
- Patch retrieval.

The component registry uses application-scoped component identifiers.

The state table supports efficient retrieval by component and state key.

Indexes should be selected according to actual query patterns because they increase storage and write costs.

## 12. Important React Distinctions

### 12.1 React element versus DOM element

A React element is a description of intended interface output.

A DOM element is an actual browser document node.

They are different objects with different responsibilities.

### 12.2 Rendering versus committing

Rendering determines the output associated with components.

The commit phase applies the necessary changes to the rendering environment.

A render does not imply that every element is recreated.

### 12.3 State update versus direct mutation

React state should be updated through the appropriate state setter.

Directly changing an existing state object or array without following the relevant update mechanism can prevent React from recognizing the intended change.

### 12.4 Component versus element

A component is a reusable definition.

An element is a description of a particular interface instance.

One component can produce many elements with different properties.

### 12.5 Virtual DOM versus browser DOM

The virtual representation is an in-memory description.

The browser DOM is the document structure managed by the browser.

React coordinates changes between its rendering model and the actual rendering environment.

## 13. Execution Requirements

### Python

| Requirement | Value |
|---|---|
| Runtime | Python 3.10 or later |
| External dependencies | None |
| Entry point | `main()` |
| Execution | `python react_introduction.py` |

The program renders a component tree, compares two versions, and executes its built-in tests.

### JavaScript

| Requirement | Value |
|---|---|
| Runtime | Browser with ES module and JSX build support |
| React | React 18 or later |
| React DOM | Matching React DOM version |
| External packages | React and React DOM |
| Entry point | `main.jsx` |

The application requires a browser document containing an element with the ID `root`.

The source uses JSX, so it must be processed by a JSX-compatible build environment before the browser can execute it.

The required dependencies can be installed with:

`npm install react react-dom`

### C++17

| Requirement | Value |
|---|---|
| Standard | C++17 |
| External dependencies | None |
| Entry point | `main()` |

Compilation:

`g++ -std=c++17 -O2 -Wall -Wextra -pedantic react_introduction.cpp -o react_introduction`

Execution:

`./react_introduction`

### Java 17

| Requirement | Value |
|---|---|
| Runtime | Java 17 |
| External dependencies | None |
| Main class | `ReactIntroduction` |

Compilation:

`javac ReactIntroduction.java`

Execution:

`java ReactIntroduction`

### PostgreSQL

| Requirement | Value |
|---|---|
| Database | PostgreSQL 14 or later |
| External extensions | None |
| Schema | `react_learning` |

Execute the SQL script using a PostgreSQL client.

The script creates its own schema, domain types, tables, constraints, indexes, functions, procedures, views, triggers, sample records, and reporting queries.

## 14. Limitations of the Educational Models

The implementations intentionally differ in scope.

| Implementation | Limitation |
|---|---|
| Python | Simulates component and virtual DOM behavior; it is not React |
| JavaScript | Uses React directly and demonstrates a browser-based application |
| C++17 | Implements a simplified positional reconciliation algorithm |
| Java 17 | Models component registration and rendering without React's runtime |
| PostgreSQL | Persists component and rendering information without performing browser rendering |

The Python, C++, and Java implementations are conceptual models.

Their reconciliation algorithms are not implementations of React Fiber, concurrent rendering, hydration, server components, or the full keyed reconciliation process.

The SQL schema represents a simplified persistence model. It is not intended to replace React's internal element and fiber structures.

The JavaScript implementation is the actual React application in this collection.

## 15. Practical Engineering Applications

The concepts demonstrated in this project apply to several types of software systems.

| Application | Relevant React concept |
|---|---|
| Enterprise dashboards | Reusable components and composition |
| Financial reporting interfaces | Props and data-driven rendering |
| Administrative portals | Component architecture and state |
| Search interfaces | Controlled inputs and derived data |
| Monitoring dashboards | State-driven updates |
| Inventory applications | Reusable lists and component properties |
| Data management interfaces | Rendering, filtering, and conditional output |
| Interactive forms | Event handling and validation |

A component-oriented architecture allows these interfaces to be developed and maintained as collections of smaller, independently understandable units.

The separation between component definitions, properties, application state, and rendering behavior provides the foundation for building larger React applications.
