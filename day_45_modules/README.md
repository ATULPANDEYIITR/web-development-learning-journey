# ES Modules and Module Architecture

## Purpose and scope

ECMAScript modules, commonly called ES modules or ESM, define how JavaScript source files expose functionality, consume dependencies, and establish boundaries between parts of an application. The `import` and `export` syntax provides a language-level module contract. A module architecture organizes those contracts into a dependency structure that can be validated, tested, and maintained.

This project examines four connected concerns:

- **Exports** determine which declarations a module makes available to consumers.
- **Imports** specify the dependencies a module expects from other modules.
- **Module architecture** defines which modules may depend on which other modules.
- **Dependency validation** detects unresolved imports, missing exports, circular relationships, and violations of architectural boundaries.

The examples use a billing application with pricing, tax calculation, invoice creation, and presentation modules. The scenario is intentionally consistent across the implementations, while each language uses its own capabilities to investigate a different part of module design.

## ES module contracts

### Named exports

Named exports expose specific declarations under explicit names.

A module might expose `calculateTotal` and `calculateTax`. Consumers select those names:

`import { calculateTotal } from "./pricing.js";`

The exported name is part of the module's public contract. If the producer renames `calculateTotal` without updating its consumers, the import contract is broken.

Named exports work well when a module provides several related operations. They make the intended dependency visible and allow consumers to import only the declarations they need.

An export can also be renamed at the import boundary:

`import { calculateTotal as sumInvoiceItems } from "./pricing.js";`

The local identifier changes, but the producer's exported name does not.

### Default exports

A module may declare one default export:

`export default calculateInvoice;`

A consumer can choose a local name:

`import createInvoice from "./invoice.js";`

The local name does not have to match the name used in the exporting module. This flexibility is useful when a file represents one primary capability, such as a factory or service.

A module may combine a default export with named exports. The default export does not replace the named-export contract, and a consumer must use the corresponding import syntax. A module cannot declare multiple default exports.

### Import forms and their purposes

| Form | Meaning | Appropriate use |
|---|---|---|
| `import { calculateTotal } from "./pricing.js"` | Imports a named binding | A consumer needs a specific public operation |
| `import calculateInvoice from "./invoice.js"` | Imports the default binding | A module has one primary exported capability |
| `import * as pricing from "./pricing.js"` | Imports a module namespace | A consumer deliberately works with a group of exports |
| `export { calculateTotal }` | Re-exports an existing local binding | A public entry point exposes a selected API |
| `export { calculateTotal } from "./pricing.js"` | Re-exports directly from another module | A package entry point composes a public interface |
| `export * from "./pricing.js"` | Re-exports eligible named exports | A barrel module aggregates APIs, provided its export surface remains unambiguous |
| `import "./register.js"` | Loads a module for its side effects | A module intentionally performs registration during evaluation |

A default import and a named import can appear in the same statement. Namespace imports provide a single object-like view of a module's exports, but they do not turn the module into a mutable configuration object.

## Module evaluation and dependency behavior

ES modules use static import and export declarations. The runtime can inspect these declarations before executing the module body. Static imports must appear at module top level, rather than inside an ordinary function or conditional block.

When a module imports another module, the dependency must be resolved before the importing module can complete evaluation. The runtime maintains module records, and repeated imports of the same resolved module generally reuse the same module instance within that module-loading context.

Imported bindings are live bindings. An importer observes changes to an exported binding when the exporting module updates it, subject to the language's binding rules. An imported binding cannot be reassigned by the consumer.

Dynamic `import()` is different from a static import declaration. It returns a promise for the module namespace and can be called conditionally or from asynchronous code. It is useful when a feature should be loaded only when needed, such as a reporting interface that is rarely opened.

Module caching and evaluation behavior depend on the runtime and resolved module identity. Different URLs can identify different module instances, and CommonJS and ESM use different loading systems. Code should not assume that all syntactically similar paths necessarily refer to the same instance.

## Architecture and dependency direction

A module can have a valid import statement and still violate the design of the application. For example, a domain pricing module should not depend on a user-interface component simply because the runtime can resolve that file.

The case study uses these layers:

| Layer | Responsibility | Allowed dependencies in the model |
|---|---|---|
| Domain | Pricing rules and tax calculations | No higher-level layer |
| Application | Coordinates invoice creation | Domain and infrastructure |
| Infrastructure | Implements technical adapters | Domain |
| Presentation | Displays invoice information | Application and domain |

The rules are enforced by the examples, not by JavaScript's import syntax itself. ES modules define the available contracts; project-specific checks define which dependency relationships are acceptable.

A useful dependency direction is:

`Presentation → Application → Domain`

Infrastructure adapters may implement contracts required by application services, while domain rules remain independent of presentation details. This reduces the chance that changes to a screen or a storage mechanism force changes to pricing rules.

## Python implementation

The Python script is an executable architecture laboratory. It uses Python's module and namespace mechanisms as practical analogies for understanding ES module contracts, while providing additional analysis tools.

### Public interfaces and composition

`CurrencyFormatter`, `calculate_subtotal`, and `create_invoice` represent a small billing domain. The `_apply_discount` helper is deliberately internal by naming convention. Python does not enforce JavaScript-style export declarations, so a module's public interface must be established through conventions, `__all__`, package structure, or explicit facade functions.

`create_invoice` receives its formatter as a dependency. This avoids a hidden global formatter and allows a test formatter to be injected. The example shows how an explicit dependency contract can make application code easier to test.

Input validation rejects negative prices, booleans masquerading as numeric values, unsupported currencies, and invalid discount rates. These checks are part of the billing domain rather than module syntax itself; they demonstrate why a module's contract includes meaningful behavioral expectations as well as exported names.

### Static ES module analysis

`analyze_es_module` recognizes common import declarations, named function and class exports, variable exports, export lists, and default exports. It produces `ModuleManifest` records that can be inspected without executing JavaScript.

This parser is intentionally limited. Regular expressions cannot correctly parse every valid JavaScript construct, including all comments, template literals, nested syntax, and unusual formatting. It is suitable for the controlled examples in this project, not as a replacement for a production JavaScript parser.

`build_dependency_graph` resolves known relative specifiers to module paths. `find_cycles` uses depth-first traversal to identify back edges, while `topological_order` uses dependency counts and a queue to place dependencies before their consumers.

For a graph with \(V\) modules and \(E\) dependency edges, standard graph traversal and topological sorting take \(O(V+E)\) time. Sorting ready nodes for deterministic output introduces additional sorting costs.

### Runtime imports and testing

`demonstrate_real_imports_and_cache` creates a temporary Python package and imports it through `importlib`. The test checks the package's explicit `__all__` declaration and verifies that repeated imports reuse the cached module object.

Temporary files are removed when the demonstration finishes. Import cache entries and search paths are also cleaned up, preventing the demonstration from contaminating unrelated code running in the same interpreter.

`demonstrate_architecture_invariants` evaluates a simple dependency-layer policy and fingerprints source files with SHA-256. The fingerprints illustrate a basic mechanism for identifying source changes. They are not a complete build cache: a production build system must also account for dependencies, compiler or bundler configuration, environment inputs, and relevant tool versions.

Run the script with `python module_architecture.py`.

## JavaScript implementation

The JavaScript file uses actual ES module syntax, including named exports, a default export, immutable exported currency configuration, and Node.js native module loading.

### Invoice validation and default export

`validateInvoiceItems` checks the structure of invoice line items before calculations proceed. `calculateInvoice` accepts an options object for currency and discount settings, returning a frozen invoice result.

The implementation calculates line totals in integer cents to reduce common binary floating-point errors in currency calculations. It checks safe integer limits because JavaScript's ordinary `Number` type cannot represent every integer exactly.

The default export makes invoice calculation the module's primary operation, while named exports expose the validation function and supported currencies. The file demonstrates how consumers can use the same module through either export form.

### Event-driven module registry

`ModuleRegistry` is an application-level dependency container, not a replacement for the ESM loader. It demonstrates explicit initialization of application services and makes dependency order observable.

Each registered module has dependencies, a factory, and a lifecycle state. Initialization resolves dependencies before invoking the factory. Successfully initialized values are reused on subsequent requests, and events report successful initialization or failure.

The registry rejects missing modules and circular initialization chains. It also resets the current module's value after a factory fails. The implementation is intentionally sequential; a production container that supports parallel initialization must coordinate concurrent requests to the same module and distinguish a shared in-flight promise from a genuine cycle.

Native module resolution is tested by writing a temporary `.mjs` module and dynamically importing its consumer. The same module URL is imported twice to verify reuse of the module namespace within that runtime context.

Run the file with `node module_architecture.mjs`. Saving it with the `.mjs` extension ensures Node.js treats it as an ES module without relying on a project-specific package configuration.

## C++ build-planning case study

The C++ program models a repository build planner for a JavaScript application. It focuses on validating contracts and deriving a safe, deterministic build order rather than performing billing calculations.

### Module representation

`Module` stores a source path, export symbols, and import bindings. `ExportKind` distinguishes named exports from default exports, while `ImportBinding` retains the original specifier and the importer's local identifier.

`ModuleBuildPlanner` maintains a catalog of modules and a dependency graph. A dependency edge points from an importing module to the module it consumes. The graph representation makes relationships explicit and allows the planner to identify broken contracts before build ordering begins.

### Resolution and contract validation

The resolver accepts relative imports and normalizes `.` and `..` path components. It rejects paths that escape the source root and reports unresolved module paths.

Validation confirms that every imported named or default export exists. It also rejects duplicate module paths and duplicate export declarations. The implementation intentionally does not attempt full Node.js package resolution, TypeScript path aliases, extension inference, or package `exports` processing.

### Dependency-first build order

`buildOrder` uses Kahn's topological sorting algorithm. It counts each module's unresolved dependencies and places modules with zero dependencies into a sorted ready set.

When a dependency is processed, its consumers' counts decrease. A consumer becomes ready when every dependency has been processed. The sorted set makes the resulting order deterministic for a given graph.

If the number of processed modules is smaller than the number of registered modules, a cycle exists. The planner reports the modules that remain blocked. The reported set identifies the unresolved portion of the graph; it is not necessarily a minimal cycle path.

The algorithm takes \(O(V+E)\) time for graph processing, with extra logarithmic costs for ordered-set operations. Its central practical value is early failure: a repository should not proceed with a build plan that assumes an impossible dependency order.

Compile with a C++17-compatible compiler:

`g++ -std=c++17 -Wall -Wextra -pedantic module_architecture.cpp -o module_architecture`

Then execute `./module_architecture` on Unix-like systems or `module_architecture.exe` on Windows.

## Java enterprise architecture model

The Java program treats the module catalog as an enterprise architecture registry. It makes export definitions, import bindings, layers, and validation states explicit domain types.

### Immutable module contracts

The `ExportDefinition` and `ImportDefinition` records are immutable value objects. Their compact constructors validate required fields and enforce the distinction between named and default imports.

`ModuleDefinition` copies incoming lists with `List.copyOf`, preventing callers from changing the module's contract through a retained mutable collection. It also rejects multiple default exports and duplicate named exports at construction time.

This validation is separate from graph validation. A module can have a structurally valid declaration and still import a nonexistent module or an unavailable export.

### Catalog and layer policies

`ModuleCatalog` registers unique module paths and resolves relative import specifiers. During validation, it checks module existence, export compatibility, and allowed layer dependencies.

The layer policy is represented as an `EnumMap` of allowed dependency sets. This is easier to audit than scattering architecture rules across unrelated conditionals. A violation produces an `ArchitectureException` containing a specific diagnostic.

The example uses `ModuleStatus` to distinguish registered, validated, and failed modules. The catalog marks the modules as failed when aggregate validation reports errors. A larger service would normally preserve per-module diagnostic states instead of marking every module failed because one module contains an error.

### Dependency ordering and limitations

The Java topological sorter uses dependency counts and a sorted ready set. It returns an immutable order and raises an architecture exception when not every module can be processed.

The example illustrates the value of a dedicated validation service: module construction checks local invariants, while the catalog checks relationships among modules. Keeping those responsibilities separate makes the model easier to test and extend.

The path resolver is deliberately restricted to relative source paths. A production registry must define exact rules for package names, extensions, symlinks, aliases, and platform-specific path behavior. A production implementation should also avoid sharing mutable catalog state across concurrent validation operations without appropriate synchronization.

Compile and run with Java 17 or later:

`javac ModuleArchitecture.java`

`java ModuleArchitecture`

## PostgreSQL relational model

The SQL script stores module architecture as relational data so that import contracts, dependencies, and validation failures can be queried independently of the application process.

### Schema and relationships

`source_modules` identifies source modules by unique path and records their architecture layer, validation status, and source fingerprint.

`module_exports` stores named and default exports. Its constraints prevent empty names and invalid combinations of export kind and export name. Unique constraints prevent duplicate export declarations for a module.

`module_imports` records the importer, original specifier, imported name, local name, import kind, and resolved target. The separate import kind is necessary because a default import and a named import have different contract semantics even when both use local identifiers.

`module_dependencies` stores the resolved graph edges. The composite primary key prevents duplicate edges, and the self-dependency constraint blocks direct self-imports in the graph model.

`module_validation_errors` records failures such as missing exports and forbidden layer dependencies. Keeping diagnostics in a table permits reporting, auditing, and comparison across validation runs.

### Constraints and indexes

Foreign keys prevent import and export rows from referring to nonexistent module records. Cascading deletion removes module-owned declarations and diagnostics, while resolved imports use restrictive deletion behavior so referenced modules cannot be removed without addressing those imports.

Indexes on importer and resolved-target identifiers support common dependency lookups. The report view joins modules, dependencies, and exports to present a compact catalog.

The path constraint rejecting strings containing `..` is deliberately conservative and not a complete path-security policy. It can reject legitimate filenames containing two dots and does not establish filesystem canonicality. Production validation should normalize paths in the application or a dedicated database function and verify the resulting path against a controlled source root.

### Contract validation

The SQL validation queries compare named imports against the target module's named exports. Default imports are represented separately. A further query checks whether a source and target layer combination violates the declared architecture policy.

The sample `report.js` module intentionally requests an unavailable export. This row produces a `missing_export` diagnostic, and the module is marked failed. The example demonstrates how invalid contracts remain visible as queryable data instead of being silently accepted.

### Transactions and graph analysis

The script runs its DDL, sample data, and validation queries in a transaction. The final `DO` block emits a notice when validation errors exist. A notice is not a failed transaction or a deployment gate: a deployment pipeline that requires a hard failure must explicitly raise an exception when diagnostics remain.

The recursive graph query illustrates reachability-based cycle analysis. Recursive SQL can become expensive for dense graphs, and path tracking can consume substantial memory. For large repositories, a dedicated graph validator or a carefully bounded recursive query may be more appropriate.

The dependency-order query is diagnostic rather than a complete implementation of Kahn's algorithm. It reports dependency counts and illustrates recursive SQL, but a production database build planner should iteratively decrement dependency counts or call a tested graph-ordering routine. SQL constraints alone do not guarantee an acyclic dependency graph.

Execute the script using a PostgreSQL client, for example:

`psql -v ON_ERROR_STOP=1 -d module_lab -f module_architecture.sql`

The database role must have permission to create and drop the tables and view used by the script.

## Circular dependencies and live bindings

A circular dependency exists when module A depends on module B and module B can reach module A through one or more dependency edges. Longer cycles may involve several intermediate modules.

A cycle does not automatically make every ES module invalid. ESM supports cyclic graphs, but the result depends on evaluation order and when imported bindings are accessed. Accessing a lexical binding before its initialization can produce a temporal dead zone error. Modules that rely on side effects during partially completed initialization can also become difficult to reason about.

The graph checks in this project apply a stricter architecture policy: cycles are rejected because they prevent a simple dependency-first build order and often signal unclear responsibility boundaries. This is a project design decision, not a claim that the JavaScript language forbids all cycles.

Live bindings and circular evaluation are related but distinct. Live bindings allow importers to observe the exporting module's binding, while cyclic evaluation determines whether the binding is initialized at the moment it is accessed.

A practical way to reduce cycles is to move a shared contract into a lower-level module that both consumers can import. The shared module should contain the genuinely shared responsibility rather than re-exporting entire layers without a clear public API.

## Re-exporting and public entry points

A package can provide a deliberate public entry point that re-exports selected operations from internal modules. This prevents consumers from depending on internal directory structure.

For example, a billing package might expose `createInvoice` and `calculateTotal` while keeping implementation-specific helpers private. The public entry point becomes the supported interface, allowing internal files to be reorganized without forcing every consumer to update its imports.

Barrel modules should be designed carefully. Broad `export *` declarations can create ambiguous names when multiple source modules export the same identifier. Explicit re-exports make the package contract easier to inspect and reduce accidental exposure of internal implementation details.

Re-exporting also does not automatically make a module tree smaller. Bundlers need to analyze reachable exports and side effects to eliminate unused code safely. A module that performs observable work during evaluation can constrain tree-shaking.

## Testing, diagnostics, and production implications

Module architecture failures should be detected at the boundary where they are easiest to explain.

- **Unresolved specifiers** indicate a path, package, alias, or extension-resolution problem.
- **Missing named exports** often result from a rename, an incorrect import form, or an outdated consumer.
- **Default-export mismatches** arise when a producer and consumer disagree about whether the primary export is default or named.
- **Circular dependencies** can indicate overlapping responsibilities or unsafe evaluation-time side effects.
- **Layer violations** indicate that a technically resolvable dependency conflicts with the project's intended architecture.
- **Import-time failures** may be caused by environment access, missing configuration, or a side effect that runs before application startup is ready.

Static validation should be combined with runtime tests. A static graph can reveal a missing export or a cycle, while runtime tests can reveal failures caused by initialization order, unavailable environment variables, or invalid service configuration.

Production module architecture should use explicit public APIs, predictable module paths, well-defined dependency direction, and controlled initialization behavior. Build tooling should validate the same module-resolution rules used by the runtime. When the build system and runtime interpret specifiers differently, a successful static check may still produce a runtime failure.

Performance depends on more than the number of source files. Excessively fine-grained modules can add resolution and tooling overhead, while oversized modules can create broad coupling and reduce test isolation. Dynamic imports can defer the cost of rarely used features, but introduce asynchronous loading and failure handling that consumers must account for.

The examples intentionally separate language-level module contracts from application-level architecture policies. That distinction is essential: valid import syntax establishes how modules connect, while explicit validation and governance determine whether those connections form a maintainable system.
