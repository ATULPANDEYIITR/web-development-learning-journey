# React Performance Engineering

## 1. Project Scope

This project examines four connected areas of React performance engineering:

1. Component rendering behavior.
2. Memoization and reuse of previously calculated results.
3. Code splitting and JavaScript bundle organization.
4. Lazy loading of application features.

The implementations use Python, JavaScript, C++17, Java 17, and PostgreSQL to model performance behavior from different engineering perspectives.

The central objective is to reduce unnecessary rendering, avoid repeated expensive calculations, limit the JavaScript required during initial application loading, and load additional features when they are needed.

## 2. React Rendering Behavior

React applications are built from components. A component receives properties (props), may use state and context, and returns a description of the interface.

A component render is not necessarily equivalent to a visible browser update.

The rendering process can be understood through these stages:

1. An event, state update, parent render, or context change schedules React work.
2. React evaluates the affected component functions.
3. React reconciles the resulting element descriptions with the previous tree.
4. React commits the required changes to the DOM.
5. The browser performs layout, painting, and compositing when required.

A component can render without producing a DOM change. Conversely, a small DOM change can trigger expensive browser work when it affects layout or painting.

### 2.1 Causes of rendering

Common causes include:

- A component's own state changes.
- A parent component renders and evaluates its children.
- A context value changes.
- External-store subscriptions notify consumers.
- A component receives different properties.

A parent render does not necessarily mean every descendant must perform expensive work. React can skip eligible component renders through memoization.

### 2.2 Rendering and reconciliation

Rendering calculates the next interface description. Reconciliation determines how the new description relates to the previous one.

React uses element types and keys to identify elements and manage component identity.

Stable keys are important when rendering lists. Unstable or index-based keys can cause incorrect state association when items are inserted, deleted, or reordered.

A render count alone is not a sufficient measure of application performance. Useful measurements also include render duration, committed updates, browser interaction latency, and the cost of DOM operations.

## 3. Memoization

Memoization stores the result of an earlier computation so that a later operation with equivalent inputs can reuse it.

React provides several mechanisms with different purposes.

| Mechanism | Purpose |
|---|---|
| `React.memo` | Skips eligible function-component renders when props are considered equal |
| `useMemo` | Reuses a calculated value while its dependencies remain equal |
| `useCallback` | Reuses a function reference while its dependencies remain equal |

These mechanisms address different sources of repeated work.

### 3.1 React.memo

`React.memo` wraps a function component and can skip rendering when its incoming props compare equal.

By default, React compares individual props using `Object.is`.

A custom comparison function can be supplied when necessary, but it must correctly account for every property that affects the rendered result.

Example concept:

`React.memo(ProductCard)`

A memoized component can still render when its own state or consumed context changes. Memoization does not freeze a component.

### 3.2 useMemo

`useMemo` caches the result of a calculation between renders.

Typical use cases include:

- Filtering large collections.
- Sorting records.
- Deriving chart datasets.
- Performing expensive transformations.
- Creating stable object values for optimized child components.

For example, a product list can be filtered using `useMemo` with the product collection and search query as dependencies.

The calculation runs again when a dependency changes.

`useMemo` is a performance optimization, not a correctness guarantee. React may discard cached values under certain conditions.

### 3.3 useCallback

`useCallback` caches a function reference.

It is useful when a function is passed to a memoized child component or used as a dependency of another Hook.

Without stable references, a parent can create a new function on every render. A child receiving that function may then render again even when the function's behavior has not changed.

`useCallback` does not automatically make the function execute faster. Its value comes from reducing unnecessary downstream work.

### 3.4 Referential equality

JavaScript objects, arrays, and functions are compared by reference.

Two separately created objects can contain identical properties while still being different references.

This distinction is important for memoization.

A component receiving a newly created object on every parent render may fail its shallow comparison even when the object's contents are unchanged.

Stable references should be maintained where they provide a measurable benefit.

### 3.5 Memoization limitations

Memoization has costs:

- Cache memory consumption.
- Dependency comparison.
- Cache maintenance.
- Additional code complexity.
- Risk of stale closures when dependencies are incorrect.

Memoization should target expensive or frequently repeated work rather than being applied indiscriminately.

The Python, JavaScript, C++17, and Java implementations demonstrate bounded caches, cached computations, render statistics, and reuse of previous component output.

## 4. Code Splitting

Code splitting divides application JavaScript into separate bundles or chunks.

Without effective code splitting, a large application may require users to download substantial JavaScript before they can use its initial interface.

A split application can load its essential functionality first and retrieve additional features when necessary.

### 4.1 Bundle structure

A representative application may have:

| Bundle | Responsibility | Loading behavior |
|---|---|---|
| Main bundle | Application bootstrap and shared layout | Initial |
| Product bundle | Product browsing and product details | Route-dependent |
| Analytics bundle | Charts and reporting | Route-dependent |
| Administration bundle | Administrative interfaces | Access-dependent |

The actual bundle structure depends on the bundler, dependency graph, and application architecture.

### 4.2 Dynamic imports

JavaScript dynamic imports allow modules to be loaded asynchronously.

A typical import expression is:

`import("./AnalyticsPage.js")`

A bundler can recognize this boundary and generate a separate chunk.

Dynamic imports return Promises. Applications must handle loading failures and asynchronous completion.

### 4.3 Route-based splitting

Route-based splitting separates features according to navigation boundaries.

For example:

- `/products` loads product functionality.
- `/analytics` loads reporting functionality.
- `/admin` loads administrative functionality.

This can reduce initial JavaScript requirements when users do not need every feature during their first visit.

### 4.4 Component-based splitting

Individual expensive components can also be split.

This is useful for:

- Large charting interfaces.
- Rich text editors.
- Maps.
- Complex reporting modules.
- Administrative tools.

Excessive splitting can produce many small requests and additional loading overhead. Chunk boundaries should reflect actual application usage.

## 5. Lazy Loading

Lazy loading postpones the loading of a component, module, or resource until it is needed.

Code splitting creates separate loading units. Lazy loading determines when those units are requested.

They are related but distinct mechanisms.

### 5.1 React.lazy

React provides `lazy` for loading components through dynamic imports.

The imported module must expose its component through a default export.

A lazy component is commonly rendered inside a `Suspense` boundary.

Conceptually:

`const AnalyticsPage = React.lazy(() => import("./AnalyticsPage"));`

The boundary can provide a loading interface while the module is unavailable.

### 5.2 Suspense

`Suspense` provides a fallback interface while supported asynchronous work is pending.

Typical fallback interfaces include:

- Loading indicators.
- Skeleton layouts.
- Placeholder content.
- Route-level loading interfaces.

A fallback should preserve the layout where possible. Large layout changes after loading can contribute to cumulative layout shift.

Error boundaries serve a different purpose. They handle rendering errors, including failures that occur after a lazy module fails to load.

### 5.3 Lazy-loading lifecycle

The lifecycle represented by the implementations is:

`UNLOADED → LOADING → LOADED`

A failure produces:

`UNLOADED → LOADING → FAILED`

A retry can return a failed module to the unloaded state.

Concurrent requests for the same module should ideally share one pending loading operation.

The JavaScript and Java implementations explicitly model this behavior using Promises and CompletableFuture objects.

### 5.4 Prefetching and preloading

Prefetching retrieves resources that may be needed later.

Preloading retrieves resources that are expected to be needed soon and can have higher loading priority.

These techniques can improve perceived navigation speed but may waste bandwidth when users never access the predicted feature.

The decision should consider user navigation patterns, network conditions, device capability, and the size of the requested resources.

## 6. Performance Metrics

Performance optimization should be based on measurements rather than assumptions.

### 6.1 Core Web Vitals

| Metric | Meaning | Good target |
|---|---|---|
| LCP | Largest Contentful Paint | At most 2.5 seconds |
| INP | Interaction to Next Paint | At most 200 milliseconds |
| CLS | Cumulative Layout Shift | At most 0.1 |

These thresholds are evaluated at the 75th percentile of page visits, separately for mobile and desktop experiences.

### 6.2 Other useful measurements

| Measurement | Purpose |
|---|---|
| Render duration | Measures component rendering cost |
| Render count | Identifies repeated component execution |
| Skipped render count | Tracks memoization effectiveness |
| Cache hit rate | Measures cache reuse |
| Initial bundle size | Tracks JavaScript required initially |
| Compressed bundle size | Measures transfer requirements |
| Chunk transfer duration | Measures lazy-loading performance |
| Failed chunk requests | Identifies loading reliability problems |
| Long tasks | Identifies extended main-thread blocking |

The database implementation stores these measurements for application-level reporting.

### 6.3 Performance budgets

A performance budget defines acceptable limits for application behavior.

Examples include:

- Maximum initial JavaScript transfer size.
- Maximum component render duration.
- Maximum route-loading duration.
- Maximum interaction latency.
- Maximum acceptable layout shift.

Budgets should be evaluated consistently against measurements collected under comparable conditions.

## 7. Implementation Architecture

### 7.1 Python: Workflow simulation

The Python implementation models a component tree and application state.

Its principal mechanisms include:

- `Component` for rendering and memoization.
- `ComponentTree` for component registration and execution.
- `MemoCache` for bounded LRU caching.
- `ApplicationState` for controlled state updates.
- `ProductService` for derived data.
- `LazyModule` for feature-loading states.
- `ModuleRegistry` for module registration and retrieval.
- `PerformanceMonitor` for execution measurements.

The script uses the standard library and includes validation, failure handling, cache statistics, and executable assertions.

Its purpose is to model the performance behavior and workflow without requiring a browser or React runtime.

### 7.2 JavaScript: Event-driven performance model

The JavaScript implementation emphasizes asynchronous execution and state-driven rendering.

Its main mechanisms include:

- `EventEmitter` for application-state notifications.
- `RenderEngine` for component execution.
- `RenderScheduler` for batching pending component updates.
- `LRUCache` for bounded memoization.
- `LazyModuleRegistry` for asynchronous loading.
- Promise sharing for concurrent module requests.
- `PerformanceTracker` for render measurements.

The lazy module registry prevents duplicate loading operations when multiple requests arrive while the same module is already loading.

Failed modules can be retried through an explicit retry operation.

The implementation is executable using Node.js and does not require third-party packages.

### 7.3 C++17: Performance-oriented engine

The C++ implementation models the component and module lifecycle using explicit domain types.

Its principal structures include:

- `Component` for rendering and cached output.
- `ComponentTree` for component management.
- `Props` for component properties.
- `MemoCache` for bounded LRU storage.
- `ProductCatalog` for filtering.
- `ModuleRegistry` for feature-loading states.
- `PerformanceAnalyzer` for elapsed-time measurement.

The implementation uses STL containers and algorithms.

The cache uses an unordered map and an access counter. Its eviction operation scans entries to identify the least recently used value, making eviction O(n). A production implementation requiring frequent eviction could use a linked list and hash map for O(1) average lookup and eviction.

The module registry models loading behavior synchronously. It demonstrates lifecycle and failure management rather than actual browser network requests.

### 7.4 Java 17: Enterprise performance model

The Java implementation uses explicit domain types and concurrency controls.

Important elements include:

- Records for immutable product and property data.
- `Component` for rendering decisions.
- `RenderEngine` for component registration and execution.
- `PerformanceMonitor` for measurements.
- `ProductService` for cached derived data.
- `LazyModule` for asynchronous feature loading.
- `ModuleRegistry` for feature management.
- `CompletableFuture` for asynchronous execution.
- `ExecutorService` for controlled background work.

The module loader shares its pending future across concurrent requests.

The executor is explicitly shut down after execution to prevent unmanaged background threads.

The implementation also demonstrates immutable collection exposure and validation of domain objects.

### 7.5 PostgreSQL: Performance monitoring database

The PostgreSQL implementation provides a relational monitoring and evaluation model.

The principal relationships are:

`Applications → Components → Component Renders`

`Applications → Code Chunks → Lazy Load Events`

`Components → Memoization Metrics`

`Applications → Performance Measurements → Performance Evaluations`

`Applications → Performance Policies`

The database separates observed performance measurements from the policies used to evaluate them.

A measurement records what happened. A policy specifies the acceptable threshold. An evaluation records the result of comparing the two.

This distinction allows historical measurements to be evaluated against explicit application policies.

## 8. PostgreSQL Database Design

### 8.1 Applications

The `applications` table identifies monitored applications and their deployment environments.

The unique application name prevents duplicate application registrations.

### 8.2 Components

The `components` table records component types, hierarchy, memoization configuration, and estimated complexity.

The self-referencing parent relationship represents component hierarchy.

The complexity value is an analytical attribute and is not a direct measurement of rendering time.

### 8.3 Component renders

The `component_renders` table records:

- Component identity.
- Session identity.
- Render sequence.
- Execution duration.
- Whether rendering was skipped.
- Property fingerprint.
- Trigger reason.

A unique constraint prevents duplicate render sequence numbers for the same component and session.

The validation trigger prevents a non-memoized component from reporting a skipped render.

### 8.4 Memoization metrics

The `memoization_metrics` table stores:

- Cache hits.
- Cache misses.
- Evictions.
- Cache memory consumption.

Cache hit rate is calculated as:

`hits / (hits + misses)`

A high hit rate is not automatically evidence of improved application performance. Cache maintenance costs and memory consumption must also be considered.

### 8.5 Code chunks

The `code_chunks` table records independently deliverable JavaScript bundles.

It distinguishes initial bundles from additional chunks and records compressed and uncompressed sizes.

The `component_chunks` table represents the many-to-many relationship between components and chunks.

### 8.6 Lazy-load events

The `lazy_load_events` table tracks module requests, their triggering events, completion states, retries, and failures.

It supports analysis of:

- Successful lazy loading.
- Failed chunk requests.
- Transfer duration.
- Retry frequency.
- Navigation-triggered loading.
- Interaction-triggered loading.

The database does not assume that a failed chunk request automatically indicates a React rendering failure.

### 8.7 Performance policies

The `performance_policies` table contains metric thresholds.

The `evaluate_measurement` function compares an individual measurement against its active policy.

The `evaluate_application` procedure processes all measurements associated with a selected application.

The evaluation table preserves the decision independently of the original measurement.

## 9. Important Technical Distinctions

| Concept | Main responsibility | What it does not guarantee |
|---|---|---|
| Rendering | Calculates component output | A DOM update |
| Reconciliation | Determines required interface changes | Faster browser execution |
| React.memo | Skips eligible component renders | No rendering under any circumstances |
| useMemo | Reuses calculated values | Permanent cache retention |
| useCallback | Reuses function references | Faster function execution |
| Code splitting | Divides application code into chunks | Automatic deferred loading |
| Lazy loading | Delays resource loading | Smaller total application code |
| Suspense | Displays a fallback for pending supported work | Handling every loading error |
| Error boundary | Handles descendant rendering failures | Recovery from every asynchronous failure |
| Prefetching | Retrieves likely future resources | Guaranteed resource usage |

These distinctions are important because applying one optimization does not automatically solve problems addressed by another.

## 10. Performance Optimization Workflow

A practical optimization process follows this sequence:

1. Measure initial application loading and user interactions.
2. Identify components with excessive rendering cost.
3. Determine whether repeated work comes from state, parent rendering, context, or unstable references.
4. Apply memoization where it reduces meaningful repeated work.
5. Measure cache effectiveness and memory overhead.
6. Identify large initial JavaScript bundles.
7. Split expensive or infrequently accessed features.
8. Introduce route-based or component-based lazy loading.
9. Provide loading fallbacks and handle chunk failures.
10. Evaluate the results against the original measurements and performance budgets.

Optimizations should be retained only when measurements demonstrate a useful improvement without introducing unacceptable complexity or memory overhead.

## 11. Edge Cases and Failure Handling

### Rendering

- Newly created objects can invalidate shallow comparisons.
- Incorrect dependency arrays can produce stale values or closures.
- State updates can trigger rendering even when props remain unchanged.
- Context changes can affect memoized consumers.
- Unstable list keys can cause incorrect component identity.
- Expensive rendering can block interaction responsiveness.

### Memoization

- A cache can grow beyond available memory if it is not bounded.
- An incorrect cache key can return unrelated results.
- Large dependency comparisons can cost more than recalculation.
- Cached values can become outdated when their dependencies are incomplete.
- Object mutation can undermine reference-based comparison.

### Code splitting

- Excessive chunk splitting can increase request overhead.
- Shared dependencies can be duplicated across chunks.
- Incorrect chunk configuration can increase the initial bundle.
- Large shared chunks can create unnecessary dependencies between routes.

### Lazy loading

- Network failures can prevent chunk retrieval.
- Concurrent requests can produce duplicate work without request deduplication.
- Loading indicators can cause layout movement.
- Retry behavior must avoid uncontrolled repeated requests.
- A failed module may require a page-level recovery strategy.

### Production monitoring

- Development rendering behavior may differ from production.
- Measurements should distinguish cold and warm cache conditions.
- Browser extensions and background processes can affect timing.
- Device and network characteristics influence results.
- Aggregate averages can conceal poor experiences at the tail of the distribution.

## 12. Security and Production Considerations

Performance optimization must not weaken application security.

Important controls include:

- Enforce authorization independently of whether an administrative module is lazy-loaded.
- Never treat a hidden or unloaded component as an access-control mechanism.
- Avoid placing credentials, access tokens, or sensitive information in chunk names and public metadata.
- Validate remote data before using it in cached computations.
- Avoid unbounded caches containing sensitive user-specific data.
- Separate cached data by tenant, identity, and authorization context when necessary.
- Use appropriate cache invalidation when permissions or user state changes.
- Avoid logging sensitive properties or complete user records in render instrumentation.
- Monitor chunk integrity and deployment consistency.

A lazy-loaded administrative feature remains publicly retrievable at the JavaScript delivery level unless the delivery system restricts access. Authorization must be enforced by the application and its backend services.

## 13. Performance and Complexity Considerations

| Operation | Typical complexity |
|---|---|
| Shallow comparison of n props | O(n) |
| Hash-map cache lookup | O(1) average |
| Bounded LRU lookup with linked-list ordering | O(1) average |
| List filtering | O(n) |
| Sorting n records | O(n log n) |
| Component registration in a hash map | O(1) average |
| SQL indexed component lookup | Depends on index and selectivity |
| SQL aggregation | Depends on rows scanned and grouping strategy |

The supplied C++ implementation uses an O(n) least-recently-used eviction scan to keep its data structure simple and explicit. The Python and JavaScript implementations maintain ordered cache entries. The Java implementation uses an access-ordered `LinkedHashMap`.

Database indexes improve selected retrieval patterns but introduce storage and write-maintenance costs.

## 14. Running the Implementations

### Python

File: `react_performance.py`

Run using Python 3:

`python react_performance.py`

The script uses standard-library modules and includes executable assertions.

### JavaScript

File: `react-performance.js`

Run using Node.js 18 or later:

`node react-performance.js`

No npm installation is required.

### C++17

File: `react_performance.cpp`

Compile:

`g++ -std=c++17 -O2 -Wall -Wextra -pedantic react_performance.cpp -o react_performance`

Execute:

`./react_performance`

### Java 17

File: `ReactPerformance.java`

Compile:

`javac ReactPerformance.java`

Execute:

`java ReactPerformance`

### PostgreSQL

File: `react_performance.sql`

Execute against a PostgreSQL 15 or later database using a role with permission to create schemas, tables, functions, procedures, and triggers.

The script creates its own schema, sample data, performance policies, evaluation functions, reporting views, and example queries.

## 15. Expected Learning Outcomes

The implementations establish the following technical distinctions:

- Rendering is different from committing DOM changes.
- Memoization is different from state management.
- Stable references influence shallow comparison.
- Component-level optimization is different from computational caching.
- Code splitting changes bundle organization.
- Lazy loading changes when a module is retrieved.
- Suspense provides loading behavior for supported asynchronous work.
- Error boundaries address rendering failures.
- Performance monitoring evaluates observed behavior rather than assumed improvements.
- Performance budgets convert optimization objectives into measurable constraints.

The four executable programs demonstrate rendering, caching, scheduling, and module-loading behavior. The PostgreSQL implementation provides persistent measurement, aggregation, policy evaluation, and reporting.
