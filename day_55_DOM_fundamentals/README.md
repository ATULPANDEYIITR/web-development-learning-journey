# DOM Fundamentals: Tree Structure, Selectors, Traversal, and Mutation

## Purpose

The Document Object Model (DOM) represents a document as a tree of nodes. Browser JavaScript uses this structure to locate elements, inspect content, modify attributes, create new elements, and remove existing nodes.

The implementations in this project use a repository dashboard containing a heading, a status message, and a list of pull requests. This scenario makes tree navigation and mutation concrete while keeping the core DOM mechanisms separate from application-specific behavior.

The Python, JavaScript, C++17, and Java 17 files implement in-memory element trees. The PostgreSQL script represents the tree relationally and demonstrates recursive traversal, selector-like retrieval, mutation logging, and integrity constraints.

## Core DOM Concepts

### The DOM tree

A document contains nodes connected through parent-child relationships.

- **Document node:** The root representing the document.
- **Element node:** A structured element such as `main`, `ul`, or `li`.
- **Text content:** The readable content associated with an element or represented by a text node in a full browser DOM.
- **Parent:** The element that directly contains a child.
- **Children:** The nodes directly contained by a parent.
- **Descendants:** All nodes reachable by repeatedly following child relationships.
- **Attributes:** Named values such as `id`, `class`, and `data-number`.

The in-memory language implementations store text directly on elements to keep the example manageable. PostgreSQL defines a separate text-node kind, although its sample dashboard primarily stores display text in element rows.

A simplified dashboard has this structure:

    document
      └── main#repository.dashboard
          ├── h1
          ├── p.status
          └── ul#pull-requests
              ├── li.pull-request[data-number="101"]
              │   └── span.title
              ├── li.pull-request[data-number="102"]
              │   └── span.title
              └── li.pull-request[data-number="103"]
                  └── span.title

The tree preserves containment and document order. An element's position among its siblings is different from its depth in the tree.

### Selectors

Selectors identify elements by characteristics rather than requiring callers to know each node's internal position.

| Selector | Meaning | Example |
|---|---|---|
| `main` | Element tag | Locate a `main` element |
| `#repository` | ID attribute | Locate the repository container |
| `.pull-request` | Class membership | Find pull-request items |
| `[data-state]` | Attribute presence | Find an element with a state attribute |

`querySelector()` returns the first matching descendant or no result. `querySelectorAll()` returns all matching descendants in document order.

In these implementations, the selector methods search descendants and exclude the receiver itself, matching the behavior of element-level browser DOM queries. The supported selector grammar is intentionally limited to simple selectors. Full browser CSS selector support also includes combinations, pseudo-classes, attribute comparisons, and other constructs.

IDs are useful for unique structural targets. Classes describe reusable categories of elements. `data-*` attributes store application-specific information, such as a pull-request number or review state.

## Traversal

Traversal follows relationships in the tree.

- **Parent traversal** moves toward the root.
- **Child traversal** inspects direct children.
- **Descendant traversal** explores nested elements.
- **Selector traversal** visits descendants and evaluates a matching rule.

A complete scan of a tree containing \(n\) nodes takes \(O(n)\) time. The supplied in-memory selectors use this approach. Repeating multiple full scans can become expensive on large documents.

The PostgreSQL implementation uses a recursive common table expression to follow `parent_id` relationships from the document root. The recursive query is the relational equivalent of a depth-first tree traversal.

## Element Creation and Modification

### Creation

Creating an element constructs a node that is not yet part of the displayed tree. Appending it connects the node to its parent.

The dashboard adds a fourth request, numbered `104`, with the title `Add audit logging`. The code checks the identifier and title before adding the element. The JavaScript, C++, and Java examples reject duplicate request numbers.

In a browser, the equivalent native operations are `document.createElement()` and `parent.appendChild()`. The in-memory implementations use their own element constructors and append methods because they are designed to run without a browser.

### Text and attribute changes

Text modification changes an element's displayed content. Attribute modification changes its metadata.

The dashboard updates the first request's title to `Validate API input and reject unsafe payloads` and marks it with `data-review-state="in-review"`.

The distinction matters because changing text should not be confused with changing element identity, parent relationships, or application state. In a real browser, `textContent` is appropriate for inserting untrusted text. Assigning untrusted input to `innerHTML` can interpret it as markup and introduce cross-site scripting vulnerabilities.

The in-memory implementations escape text and attribute values during HTML serialization. This is a useful output-safety measure, not a replacement for browser security controls or context-specific sanitization.

### Removal

Removing an element disconnects it from its parent. The sample workflow removes request `103` after it is treated as completed.

The Python, JavaScript, and Java implementations update both sides of the relationship. The C++ implementation uses `std::unique_ptr` to own children and erase a node safely from its parent's child collection.

In browser JavaScript, `element.remove()` performs the corresponding operation. A detached node may remain accessible if application code still holds a reference to it.

## Python Implementation

The Python script defines an `Element` dataclass with attributes, text, children, and a parent reference.

Its important mechanisms are:

- `append()` validates node types and prevents cycles or accidental reparenting.
- `descendants()` provides recursive traversal.
- `matches()` evaluates simple tag, ID, class, and attribute selectors.
- `query_selector()` and `query_selector_all()` expose first-match and all-match retrieval.
- `set_attribute()` and `set_text()` perform validated mutations.
- `remove()` disconnects an element from its parent.
- `to_html()` serializes the tree with HTML escaping.

The `DOMError` exception makes invalid operations explicit. Assertions check the final request count, selector behavior, parent relationships, and escaping of potentially unsafe text.

The model is intentionally smaller than a browser DOM. Text and child elements are stored separately, and the script does not implement event propagation, layout, computed styles, or the complete CSS selector language.

## JavaScript Implementation

The JavaScript file uses a `MiniElement` class and `Map` objects for attributes. It includes a small asynchronous status-refresh operation to illustrate how a DOM update can be coordinated with asynchronous work.

The `addPullRequest()` function validates request numbers, rejects duplicate identifiers, and appends a newly created list item. The status refresh updates text and an attribute after a resolved promise. Errors are handled through a top-level rejection handler that sets the process exit code.

In a browser application, native DOM elements already provide selector and mutation APIs. A real interface should generally use those APIs rather than replace the browser DOM with a custom tree.

The standalone model is useful for studying tree invariants without a browser runtime. Its selector engine supports only the explicitly implemented grammar. The asynchronous example illustrates sequencing but does not make rendering or network requests automatic.

## C++17 Implementation

The C++ program treats the dashboard as a repository-oriented data structure with explicit ownership.

- `Element` stores a tag, attributes, text, parent pointer, and owned children.
- `std::unique_ptr` gives each child a single owning parent.
- `Selector` separates selector parsing from matching.
- `RepositoryDashboard` manages request creation, title changes, and removal.
- Exceptions report invalid operations and missing elements.

The design uses a vector for ordered children and a map for deterministic attribute serialization. Selector scans remain linear in the number of visited nodes. Searching for an item by request number also requires a scan because this implementation does not maintain a separate index.

The parent pointer is non-owning. Child ownership remains with the parent, so removal destroys the owned subtree. Code must not use a raw pointer to a removed element after that operation. The example completes all reads before removing the corresponding node.

## Java 17 Implementation

The Java program adds an explicit review-state model to the dashboard.

`PullRequest` is a record that validates request numbers and titles. `ReviewState` defines the states `OPEN`, `IN_REVIEW`, `APPROVED`, and `MERGED`. `DashboardService` controls request creation, state transitions, and removal.

The transition rules allow:

- `OPEN` to `IN_REVIEW`
- `IN_REVIEW` to `APPROVED` or `OPEN`
- `APPROVED` to `MERGED` or back to `IN_REVIEW`

A merged request cannot transition further. The service also prevents removal of merged requests. These rules demonstrate the distinction between modifying the DOM tree and changing application-domain state.

The Java implementation uses an unmodifiable view of selector results to prevent callers from changing the internal child collection through the returned list. Elements remain mutable through their defined methods. The example is a single-process model, not a thread-safe shared document service.

## PostgreSQL Implementation

The SQL script stores the DOM in relational tables rather than nested language objects.

### Relational model

| Table | Responsibility |
|---|---|
| `dom_documents` | Identifies each document |
| `dom_nodes` | Stores node kind, parent, tag, text, and sibling position |
| `dom_attributes` | Stores named attribute values |
| `dom_mutations` | Records selected structural changes |

The `dom_nodes` table uses a self-referencing foreign key for parent-child relationships. The foreign key is deferred so that eligible multi-row changes can be checked at transaction boundaries. A partial unique index allows only one document-root row per document.

A validation trigger rejects parents from another document and prevents text nodes from containing children. A separate trigger rejects a parent change that would create a cycle. These checks help preserve the tree structure, although production-grade concurrent tree mutation requires careful locking and transactional coordination.

The mutation audit trigger records inserted nodes. Attribute values are stored separately to avoid repeating attribute columns for every possible HTML attribute.

### Recursive retrieval and selector-like queries

The recursive CTE starts at the document node and repeatedly joins children by `parent_id`. It returns node depth and content in a form suitable for inspecting the tree.

The `find_elements()` function implements a restricted lookup by tag and exact attribute name-value pair. It validates the tag format and requires attribute names and values to be supplied together. It is not a complete CSS selector engine.

The `dom_element_inventory` view counts direct children for each element. The attribute index supports lookups by attribute name and value, while the parent-position index supports common tree navigation patterns.

### Mutations and transactions

The script creates the dashboard, queries its structure, updates a title, sets a review-state attribute, and deletes request `103`. A final report shows the resulting elements and recorded node insertions.

The sample uses a transaction so that its initial construction and changes can be committed together. Savepoints are available for isolating operations that might need to be rolled back after an error. PostgreSQL aborts the current transaction after many statement errors unless the client uses a savepoint or starts a new transaction.

The SQL model is not a complete browser implementation. It does not execute JavaScript, calculate styles, perform layout, or implement browser event behavior. It demonstrates how tree structure, attributes, traversal, constraints, and mutation history can be represented in a relational database.

## Cross-Implementation Workflow

All five source files use the same core sequence:

1. Build a document tree.
2. Locate request elements using selectors.
3. Change a title and an attribute.
4. Create another request element.
5. Remove a completed request.
6. Validate the final structure and handle invalid operations.

The implementations differ in how they represent and enforce the tree:

| Language | Main design emphasis |
|---|---|
| Python | Dataclasses, generators, assertions, and explicit exceptions |
| JavaScript | Event-oriented mutation, promises, and map-backed attributes |
| C++17 | Unique ownership, explicit selector parsing, and deterministic containers |
| Java 17 | Records, domain states, immutable result lists, and service-level transitions |
| PostgreSQL | Relational integrity, recursive CTEs, triggers, indexes, and transactions |

## Edge Cases and Limitations

The code covers several important failure conditions:

- Missing selector results
- Invalid element or attribute names
- Empty titles and invalid identifiers
- Duplicate request numbers
- Attempts to create cycles
- Attempts to append an already attached node
- Removal of a root or detached element
- Invalid application-state transitions
- Unsafe text and attribute values during serialization
- Unsupported selector syntax

A full browser DOM has additional behavior, including live document integration, event dispatch, mutation observers, namespace-aware nodes, document fragments, shadow DOM, browser parsing rules, and layout-related APIs. These implementations deliberately focus on the foundational tree operations.

When applying these principles to real interfaces, prefer stable identifiers for application records, validate data at system boundaries, use `textContent` for plain untrusted text, and avoid retaining references to elements after their ownership or lifecycle has ended.
