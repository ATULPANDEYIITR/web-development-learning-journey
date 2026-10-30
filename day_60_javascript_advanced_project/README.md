# API-Powered Operational Dashboard

## System purpose

This project implements an operational dashboard that retrieves data from multiple API resources, validates incoming payloads, manages asynchronous loading, retains previously valid data when an upstream API fails, and produces a consolidated view of service health.

The example domain is an enterprise application environment containing payment processing, identity management, notification delivery, and analytics services.

The dashboard works with three principal API resources:

| API resource | Data returned | Dashboard purpose |
|---|---|---|
| `/api/metrics` | Latency, error rate, and measurement timestamps | Quantitative service monitoring |
| `/api/services` | Service identity, region, and operational state | Service inventory and availability |
| `/api/incidents` | Incident severity, status, and affected service | Operational incident monitoring |

The implementations use deterministic sample API providers. This makes the examples executable without external credentials, API keys, or network dependencies.

## Architecture

The system separates API communication, validation, state management, and presentation.

```text
                API PROVIDERS
                     |
          +----------+----------+
          |          |          |
       Metrics    Services   Incidents
          |          |          |
          +----------+----------+
                     |
              API Data Layer
                     |
          +----------+----------+
          |          |          |
       Validate    Retry      Timeout
          |          |          |
          +----------+----------+
                     |
              Resource Cache
                     |
          +----------+----------+
          |          |          |
        Fresh      Stale     Unavailable
          |          |          |
          +----------+----------+
                     |
             Dashboard State
                     |
          +----------+----------+
          |          |          |
       Metrics    Service     Incident
        Panels    Overview      Panel
                     |
               Dashboard View
```

The architecture distinguishes three kinds of information:

- Source data: Records received from an API.
- Resource state: Whether a resource is loading, available, stale, or unavailable.
- Dashboard state: Whether the combined dashboard is ready, degraded, or in an error condition.

A failed API request does not automatically mean that the entire dashboard must become unavailable. Each resource has an independent retrieval and validation process.

## Asynchronous API processing

### Request lifecycle

A dashboard refresh initiates retrieval of metrics, services, and incidents.

The requests are independent and can run concurrently. Each result is collected separately so that one failed endpoint does not discard successful responses from other endpoints.

The resource loading lifecycle is:

```
                REFRESH REQUEST
                       |
                 Set LOADING
                       |
              Start API requests
                       |
              Validate responses
                       |
               +-------+-------+
               |               |
            Valid            Invalid
               |               |
          Update cache      Retry request
               |               |
          Return fresh      Retry exhausted
                               |
                       +-------+-------+
                       |               |
                  Cache exists     No cache
                       |               |
                  Return stale    Return error
                       |               |
                       +-------+-------+
                               |
                      Update dashboard
                               |
                    READY / DEGRADED / ERROR
```

### Concurrency and synchronization

The three API resources do not depend on each other for retrieval. Running them concurrently reduces the total refresh duration.

The implementations use different concurrency mechanisms:

| Language   | Mechanism                              | Application                                           |
| ---------- | -------------------------------------- | ----------------------------------------------------- |
| Python     | `asyncio`, `asyncio.gather`            | Concurrent asynchronous resource retrieval            |
| JavaScript | `Promise.allSettled`                   | Independent request completion and failure collection |
| C++17      | `std::async`, `std::future`            | Parallel resource acquisition                         |
| Java 17    | `CompletableFuture`, `ExecutorService` | Enterprise-oriented asynchronous service aggregation  |
| PostgreSQL | Transactions and set-based queries     | Consistent storage and reporting                      |

Concurrency does not imply that every operation should share mutable state. The examples keep resource caches separate and consolidate completed results at the dashboard service boundary.

## API validation

API responses are external input. A successful HTTP response does not guarantee that its data is valid.

The implementations validate records before accepting them into the dashboard.

| Resource  | Validation requirements                                                                                                   |
| --------- | ------------------------------------------------------------------------------------------------------------------------- |
| Metrics   | Required identifiers, numeric values, non-negative measurements, valid timestamps, unique service and metric combinations |
| Services  | Unique service identifiers, non-empty names, valid regions, supported service states                                      |
| Incidents | Unique incident identifiers, valid severity, supported incident states, non-empty titles, valid timestamps                |

Metric validation rejects negative values, `NaN`, and infinite values where numerical validation is supported.

Timestamp validation requires a valid time representation and rejects timestamps unreasonably far into the future.

Duplicate resource identifiers are rejected because they create ambiguous dashboard state and unreliable aggregation.

Validation occurs before a new response replaces its resource's last-known-good data.

## Retry and cache policies

### Bounded retries

Temporary API failures can result from service overload, network interruptions, gateway errors, or rate limiting.

The implementations apply bounded retries rather than retrying indefinitely.

The retry delay grows exponentially:

\\[ d_n = d_0 \times 2^n \\]

Where:

- \\(d_0\\) is the initial retry delay.
- \\(n\\) is the retry attempt number.
- \\(d_n\\) is the delay before the next attempt.

A retry policy must have a maximum attempt count. Unlimited retries can amplify upstream failures, consume connections, and delay dashboard recovery.

The JavaScript implementation retries network errors, HTTP 429 responses, and server-side HTTP errors. Other HTTP client errors are not automatically retried.

### Resource caching

The dashboard uses a resource-specific cache.

A cached record set is updated only after the received response has passed validation.

This prevents malformed or incomplete API data from replacing previously valid information.

A cache entry has two relevant properties:

- Its previously validated resource data.
- The time at which that data was successfully retrieved.

The cache has a configurable time-to-live. A fresh resource can be reused without a new network request. An explicit refresh bypasses the normal TTL check.

### Stale-data fallback

When an upstream request fails after all retry attempts, the dashboard can retain the last-known-good response.

That response is not presented as fresh.

Stale resources are explicitly identified in the dashboard state. This distinction matters because a dashboard displaying old operational measurements without a freshness indicator can lead to incorrect operational decisions.

A resource without valid cached data is marked as unavailable rather than populated with fabricated default measurements.

## Dashboard state management

The dashboard lifecycle is represented using explicit states.

| State              | Meaning                                                   |
| ------------------ | --------------------------------------------------------- |
| `IDLE`             | No refresh has started                                    |
| `LOADING`          | Resource requests are being processed                     |
| `READY`            | All required resources were retrieved successfully        |
| `DEGRADED`         | At least one resource failed, is stale, or is unavailable |
| `ERROR` / `FAILED` | No usable dashboard resources were obtained               |

The JavaScript and Python implementations use `ERROR` for an entirely unsuccessful refresh. The C++ and Java implementations use their respective `FAILED` state names.

A dashboard can be degraded while still providing useful information. For example, its metrics and service inventory may be current even when the incident API is temporarily unavailable.

This is a resource-level failure model rather than an all-or-nothing loading model.

### State transition considerations

The JavaScript controller associates refresh operations with generation numbers. A result from an older refresh must not overwrite the state established by a more recent refresh.

The controller also aborts a superseded refresh. Cancellation prevents unnecessary work, while the generation check protects state consistency even when a request completes close to the cancellation point.

The Python controller serializes refresh operations using `asyncio.Lock`. This ensures that its snapshots are assembled in a controlled order.

The C++ implementation collects future results before updating the consolidated snapshot.

The Java implementation uses separate typed caches and joins the asynchronous resource futures before constructing the immutable snapshot.

## Operational metrics and incidents

### Metric observations

A metric is a time-stamped measurement associated with a service.

The demonstration uses:

| Metric              | Unit            | Interpretation                             |
| ------------------- | --------------- | ------------------------------------------ |
| Latency             | Milliseconds    | Time taken to process a request            |
| Error rate          | Percentage      | Proportion of requests resulting in errors |
| Requests per minute | Requests/minute | Approximate request throughput             |

Metrics must be interpreted together with their observation timestamps.

A low error rate measured several hours ago cannot establish that a service is currently healthy. Freshness is therefore an independent property of metric availability.

### Service status

Service status represents the operational condition reported by the service inventory API.

The domain uses three states:

- `OPERATIONAL`
- `DEGRADED`
- `DOWN`

A service status and a metric observation are not interchangeable. A service may be marked operational while reporting elevated latency, or it may have a recent metric observation while its declared status is down.

### Incident state

Incidents have independent severity and lifecycle fields.

| Field              | Meaning                             |
| ------------------ | ----------------------------------- |
| Severity           | Operational impact classification   |
| Status             | Incident lifecycle state            |
| Service identifier | Service affected by the incident    |
| Opened timestamp   | Time the incident was reported      |
| Title              | Human-readable incident description |

An incident with `RESOLVED` status does not count as an open incident.

The examples distinguish incident state from service state. A service can be operational while a low-severity incident remains under investigation.

## Python implementation

File: `dashboard.py`

The Python application models the dashboard as an asynchronous resource orchestration service.

### Implemented mechanisms

Data classes and enumerations

`Metric`, `Service`, `Incident`, and `DashboardSnapshot` define the dashboard's domain objects.

`DashboardPhase` and `ServiceStatus` represent finite sets of states and reduce ambiguity in status handling.

Asynchronous resource retrieval

`DemoApiClient` provides an asynchronous API interface. `DashboardController` concurrently requests the three dashboard resources through `asyncio.gather`.

The use of `return_exceptions=True` enables independent error handling for each resource.

Validation

Separate validation functions process metric, service, and incident payloads. They return typed domain objects rather than leaving raw dictionaries throughout the dashboard.

TTL cache

`CacheEntry` records the last valid payload and its retrieval timestamp. The controller checks the cache before using previously stored data.

Failure handling

`_load_resource` implements bounded exponential retries. After retry exhaustion, it uses previously validated data when available.

Serialized refresh operations

`asyncio.Lock` prevents overlapping refresh operations from producing competing snapshots.

Atomic JSON export

`export_json` writes to a temporary file, flushes the file, and then replaces the destination. This avoids exposing a partially written dashboard snapshot.

The output file is `dashboard_snapshot.json`.

### Execution

Run:

`python dashboard.py`

Python 3.10 or later is required. The implementation uses only the standard library.

## JavaScript implementation

File: `dashboard.js`

The JavaScript implementation places event-driven state handling and asynchronous API communication at the centre of the design.

It runs with Node.js 18 or later.

### Mock API server

`startMockApiServer` creates a local HTTP server using the Node.js `http` module.

It exposes three GET endpoints and returns JSON responses with request identifiers and response timestamps.

The server can simulate HTTP 503 errors for incident requests. This gives the client a repeatable way to exercise retry and stale-data behaviour without relying on an external service.

### Fetch-based API client

`DashboardApiClient` uses the built-in `fetch` interface.

Its responsibilities include:

- Building API requests.
- Applying request timeouts.
- Forwarding cancellation signals.
- Validating response envelopes.
- Applying bounded retries.
- Caching validated resource data.
- Falling back to stale data after request failures.

The in-flight request map ensures that concurrent requests for the same resource can share one network operation.

This is request coalescing. It reduces duplicate calls when multiple dashboard components request the same resource at nearly the same time.

### Event-driven state

`DashboardStore` extends `EventEmitter`.

When the dashboard state is replaced, subscribers receive a `change` event with the updated state.

The application does not directly modify nested resource collections through event listeners. State updates are performed by the controller and exposed as complete state snapshots.

### Promise-based aggregation

`Promise.allSettled` collects independent endpoint outcomes.

Unlike `Promise.all`, which rejects when one promise rejects, `Promise.allSettled` allows the controller to inspect every resource result.

This is appropriate when individual dashboard panels should continue working after another API endpoint fails.

### Refresh cancellation and polling

The controller aborts an older refresh when a new refresh begins. A generation counter prevents outdated results from updating the current dashboard.

`startPolling` supports periodic refreshes. `stopPolling` and `cancel` clear timers and abort outstanding work.

The example uses explicit refresh operations so that its failure-handling behaviour is visible and deterministic.

### Execution

Run:

`node dashboard.js`

The program starts a local API server, refreshes the dashboard, simulates repeated incident API failures, and shuts down the server.

## C++17 implementation

File: `dashboard.cpp`

The C++ implementation emphasizes typed resource handling, concurrent acquisition, validation, and aggregation.

### Domain modeling

The program defines structures for:

- `Metric`
- `Service`
- `Incident`
- `DashboardSnapshot`
- `DashboardSummary`

Enumerations represent dashboard phase, service status, incident severity, and incident lifecycle.

### Concurrent retrieval

`DashboardService` uses `std::async` to retrieve metrics, services, and incidents concurrently.

Each task produces a typed `ResourceResult<T>`.

The caller obtains the results through `std::future` before changing the consolidated snapshot. This reduces the amount of shared mutable state.

### Typed resource caching

Each resource has its own cache.

A response is stored only after its validator accepts the complete result. A failed request returns cached data with a stale flag when a previously valid result exists.

The separate caches prevent metrics, services, and incidents from being accidentally mixed.

### Policy-driven retry logic

`DashboardPolicy` contains the retry count and retry delay.

The generic `loadWithRetry` template uses a fetch function and a validation function. This allows the retrieval mechanism to be reused without removing the compile-time type distinction between resource categories.

### Aggregation

`DashboardSummary` calculates:

- Total services.
- Operational services.
- Degraded services.
- Unavailable services.
- Open incidents.
- Operational service percentage.
- Average observed error rate.

The summary is derived from the current snapshot and does not replace the original measurements.

### Execution

Compile:

`g++ -std=c++17 -O2 -Wall -Wextra -pedantic dashboard.cpp -o dashboard`

Run:

`./dashboard`

The program uses only the C++ standard library.

## Java 17 implementation

File: `DashboardApplication.java`

The Java implementation uses explicit domain records and a service-oriented design suitable for an enterprise application.

### Immutable records

`MetricPoint`, `ServiceRecord`, and `IncidentRecord` represent domain data as Java records.

Their compact constructors validate required fields and invalid values.

`DashboardSnapshot` and `ResourceResult<T>` use immutable collection copies. This limits accidental modification of data after the dashboard state has been constructed.

### Typed resource cache

`ResourceCache<T>` is a generic cache associated with a single resource type.

Each cache owns:

- Its resource name.
- Its API retrieval function.
- Its validation function.
- Its cache entry.
- Its freshness policy.

It retains valid data after upstream failures and reports whether the returned result is stale.

### CompletableFuture orchestration

`DashboardService` retrieves the three resources through separate `CompletableFuture.supplyAsync` operations.

An `ExecutorService` provides a bounded thread pool with three worker threads.

`CompletableFuture.allOf` acts as the completion barrier. The service then joins the individual typed results and constructs one immutable dashboard snapshot.

### Enterprise-oriented domain validation

The implementation separates domain validation from API retrieval.

The record constructors enforce basic field-level rules. Resource-level validators enforce uniqueness across each collection.

This separation makes it possible to apply different validation rules to different types of information.

### Summary service

`DashboardSummary` is calculated from the current snapshot. It aggregates service states, open incidents, operational percentage, and average error rate.

The summary is a derived result and does not alter the stored metric records.

### Execution

Compile:

`javac DashboardApplication.java`

Run:

`java DashboardApplication`

Java 17 is required. No third-party dependencies are used.

## PostgreSQL implementation

File: `dashboard.sql`

The database implementation represents the dashboard as a relational operational data model.

It stores API configurations, synchronization results, service inventory, metric observations, incidents, widget configuration, and dashboard snapshots.

### Relational model

| Table                 | Responsibility                                   |
| --------------------- | ------------------------------------------------ |
| `api_sources`         | Defines upstream API sources                     |
| `services`            | Maintains the canonical service inventory        |
| `api_sync_runs`       | Tracks synchronization attempts                  |
| `api_sync_endpoints`  | Tracks individual endpoint outcomes              |
| `metric_definitions`  | Defines accepted measurement types and units     |
| `metric_observations` | Stores time-stamped service measurements         |
| `incidents`           | Stores operational incidents                     |
| `dashboard_widgets`   | Stores dashboard layout and widget configuration |
| `dashboard_snapshots` | Persists evaluated dashboard state               |

The foreign keys ensure that observations and incidents reference registered services and that synchronization runs reference known API sources.

### Data integrity

The script uses:

- Primary keys.
- Foreign keys.
- Unique constraints.
- Check constraints.
- Enumerated domain types.
- Referential integrity.
- Timestamp validation.
- JSONB type validation.

The `metric_observation_unique` constraint prevents duplicate observations for the same service, metric, and timestamp.

The incident resolution constraint requires a resolution timestamp when an incident is resolved and prohibits that timestamp for unresolved incidents.

### Synchronization lifecycle

An API synchronization starts with the `RUNNING` state.

The `finish_sync_run` function permits a transition to `SUCCEEDED`, `PARTIAL`, or `FAILED`.

The function rejects attempts to finalize a non-running synchronization or to use an invalid completion state.

Endpoint-level records are stored separately from the overall synchronization result. This distinction supports partial API failures where some resources succeed and others fail.

### Dashboard evaluation

`evaluate_dashboard` uses common table expressions to combine recent metrics and active incidents.

It calculates the latest latency, latest error rate, last observation timestamp, data age, and incident counts for each registered service.

The evaluation rules are:

| Condition                                                                | Evaluated state |
| ------------------------------------------------------------------------ | --------------- |
| Registered status is `DOWN`                                              | `DOWN`          |
| At least one critical incident is active                                 | `DOWN`          |
| No recent metric observations exist                                      | `STALE`         |
| Latest observations are older than ten minutes                           | `STALE`         |
| Service is degraded, incidents remain open, or error rate is at least 5% | `DEGRADED`      |
| None of the above conditions apply                                       | `HEALTHY`       |

The original service status is retained as a separate field. The evaluated state is a dashboard assessment, not a replacement for the value supplied by the service inventory.

### Query and aggregation design

The `idx_metric_latest_lookup` index supports retrieval of recent measurements for individual services and metrics.

The partial index `idx_incidents_open_by_service` supports queries that retrieve unresolved incidents without indexing every resolved record in the same way.

`dashboard_service_health` provides the current evaluated view. `dashboard_status_counts` aggregates the number of services in each evaluated state.

### Snapshot persistence

`refresh_dashboard_snapshot` evaluates the dashboard and saves its result as JSONB.

The snapshot contains the service-level assessment, generation timestamp, evaluation window, and recent synchronization error count.

The sample script calls this function within a transaction so that the snapshot insertion is committed atomically.

### Execution

Run the script using PostgreSQL:

`psql -U postgres -d your_database -f dashboard.sql`

The script drops and recreates its demonstration schema. It should therefore be run against a database where replacing the `ops_dashboard` schema is acceptable.

PostgreSQL 14 or later is required.

## Performance considerations

### Concurrent retrieval

Independent API calls should execute concurrently rather than sequentially when their responses do not depend on each other.

The expected retrieval duration is approximately the slowest resource request rather than the sum of all resource request durations, subject to concurrency limits and network conditions.

### Request coalescing

The JavaScript client shares an in-flight request for the same endpoint. This prevents duplicate calls when multiple consumers request identical resources at the same time.

### Cache sizing

A production cache should have limits on both entry age and memory consumption.

TTL alone is not a complete cache management policy. Resource size, update frequency, eviction behaviour, and the cost of retrieving the data must also be considered.

### Database queries

The PostgreSQL model uses a composite time-oriented index for metric retrieval and a partial index for unresolved incidents.

Time-series datasets can grow rapidly. Production installations may need partitioning by observation time, retention policies, archival storage, or a specialized time-series storage strategy.

### Thread and task management

The C++ and Java implementations use bounded concurrency mechanisms rather than creating an unrestricted number of workers.

Python's asynchronous approach is suitable for I/O-bound workloads. Increasing the number of asynchronous tasks without controlling upstream concurrency can still overload an API provider.

## Security and operational considerations

The demonstration uses local fixtures and does not contain credentials.

A production API integration should implement:

- TLS for external API communication.
- Authentication and authorization for protected endpoints.
- Secrets stored outside source files.
- Strict request and response size limits.
- Input validation before database writes.
- API rate limiting and concurrency limits.
- Request identifiers for tracing.
- Structured logs that avoid exposing access tokens or sensitive payloads.
- Role-based access for dashboard configuration and administrative operations.
- Defined data retention and deletion policies.
- Monitoring of API failures, retry counts, stale resources, and refresh latency.

A stale-data indicator is particularly important for operational dashboards. An old measurement must not appear equivalent to a freshly collected measurement.

The demonstration's local HTTP server and mock API adapters are test infrastructure, not production security boundaries.

## Limitations and engineering boundaries

The sample applications focus on resource orchestration and dashboard state rather than implementing a complete web frontend.

The JavaScript interface is a Node.js terminal dashboard. It does not include a browser component framework, charting library, or user authentication system.

The API fixtures are deterministic and do not reproduce every behaviour of a real distributed service. Real API integrations also need pagination, schema versioning, rate-limit handling, connection-pool management, and provider-specific authentication.

The examples use in-process caches. Those caches are not shared between application instances and are not persistent across process restarts. A multi-instance deployment would require an appropriate shared cache or a database-backed freshness strategy.

The PostgreSQL model stores dashboard snapshots as JSONB while maintaining the underlying operational records in relational tables. The snapshot is an evaluated representation, not a substitute for the source observations.

The implementations deliberately report degraded conditions instead of silently treating old or unavailable API data as current information.

## Cross-language implementation comparison

| Concern                | Python              | JavaScript                  | C++17                      | Java 17                                | PostgreSQL                           |
| ---------------------- | ------------------- | --------------------------- | -------------------------- | -------------------------------------- | ------------------------------------ |
| Asynchronous execution | `asyncio`           | Promises                    | `std::async`               | `CompletableFuture`                    | Transactional database execution     |
| State representation   | Dataclass and enum  | Event-driven store          | Struct and enum            | Immutable records and enum             | Tables and enum types                |
| Validation             | Dedicated functions | Schema validation functions | Typed validation functions | Constructors and collection validators | Constraints and functions            |
| Cache                  | Resource dictionary | `Map`                       | Typed resource vectors     | Generic typed cache                    | Persistent relational records        |
| Retry                  | Async backoff       | Fetch retry policy          | Generic retry template     | Generic typed cache policy             | Synchronization lifecycle            |
| Stale data             | `ResourceResult`    | Resource result object      | Typed result structure     | `ResourceResult<T>`                    | Observation timestamps and snapshots |
| Reporting              | Snapshot rendering  | State rendering             | Aggregate summary          | Summary record                         | Views and SQL aggregation            |

The languages implement the same operational problem through different engineering models. The Python implementation emphasizes asynchronous orchestration, JavaScript emphasizes event-driven state and request coordination, C++ emphasizes typed concurrent retrieval, Java emphasizes immutable enterprise domain modeling, and PostgreSQL provides durable storage, integrity enforcement, and set-based evaluation.
