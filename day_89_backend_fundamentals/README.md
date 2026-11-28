# Backend Fundamentals

## 1. Backend Architecture

Backend development concerns the server-side components responsible for receiving requests, applying business rules, accessing persistent data, enforcing security policies, and returning responses.

A backend application typically contains several cooperating layers:

| Layer | Responsibility |
|---|---|
| HTTP server | Accepts network connections and HTTP requests |
| Router | Matches HTTP methods and URL patterns |
| Middleware | Processes requests before and after endpoint execution |
| Controller | Coordinates HTTP input and output |
| Service | Implements business rules |
| Repository | Handles data access |
| Database | Stores persistent application information |

The implementations use a task-management application to demonstrate these responsibilities.

### Layered architecture

The central request-processing relationship is:

Client
  |
  v
HTTP Server
  |
  v
Middleware Pipeline
  |
  v
Router
  |
  v
Controller
  |
  v
Service
  |
  v
Repository
  |
  v
Database

The response travels back through the application layers to the HTTP server.

### Separation of concerns

Each layer has a defined responsibility.

- The HTTP server handles network communication.
- Middleware handles shared request-processing requirements.
- Routing determines which endpoint receives a request.
- Controllers translate HTTP requests into application operations.
- Services enforce business rules.
- Repositories isolate persistence operations.
- Databases enforce durable relational integrity.

This separation reduces coupling and allows individual components to be tested independently.

## 2. REST and HTTP Fundamentals

REST is an architectural style for designing networked applications around resources and their representations.

The task-management API exposes tasks as resources.

Resource collection:

`/api/v1/tasks`

Individual resource:

`/api/v1/tasks/{id}`

### HTTP methods

| Method | Endpoint | Operation | Success status |
|---|---|---|---|
| GET | `/api/v1/tasks` | Retrieve tasks | 200 |
| GET | `/api/v1/tasks/1` | Retrieve one task | 200 |
| POST | `/api/v1/tasks` | Create a task | 201 |
| PATCH | `/api/v1/tasks/1` | Partially update a task | 200 |
| DELETE | `/api/v1/tasks/1` | Delete a task | 200 |

GET retrieves resources without intentionally modifying application state.

POST creates a new resource.

PATCH modifies selected resource properties.

DELETE removes a resource.

The implementations use resource-oriented URL structures and HTTP method distinctions.

### HTTP status codes

| Status | Meaning | Application scenario |
|---|---|---|
| 200 | OK | Successful retrieval or update |
| 201 | Created | Task creation |
| 400 | Bad Request | Invalid request data |
| 404 | Not Found | Missing task or route |
| 405 | Method Not Allowed | Unsupported method |
| 409 | Conflict | Conflicting resource state |
| 413 | Content Too Large | Excessive request body |
| 415 | Unsupported Media Type | Invalid content type |
| 500 | Internal Server Error | Unexpected application failure |

A successful HTTP response does not necessarily mean that every business operation is correct. Applications must validate input and enforce business rules before committing changes.

### API versioning

The API uses the `/api/v1` prefix.

Versioning provides a way to introduce incompatible interface changes without immediately breaking existing clients.

A later version can expose `/api/v2` while maintaining the previous interface during a controlled migration.

## 3. Routing

Routing maps an incoming HTTP request to an appropriate endpoint handler.

A route generally consists of:

- HTTP method
- URL pattern
- Path parameters
- Controller or endpoint handler

Example:

`GET /api/v1/tasks/{id}`

The parameter `{id}` identifies the requested task.

### Static and dynamic routes

| Route | Type |
|---|---|
| `/health` | Static |
| `/api/v1/tasks` | Static |
| `/api/v1/tasks/{id}` | Dynamic |

The Python, JavaScript, C++17, and Java 17 implementations demonstrate route registration and parameter extraction.

### Route matching

A router compares the request method and path against registered routes.

The routing process is:

1. Receive the request.
2. Identify its HTTP method.
3. Match its URL pattern.
4. Extract path parameters.
5. Invoke the matching handler.
6. Return a not-found response when no route matches.

A path that exists with an unsupported HTTP method should produce 405 rather than being incorrectly treated as a missing resource.

### Route parameters and query parameters

Path parameters identify a resource.

Example:

`/api/v1/tasks/10`

Query parameters modify retrieval criteria.

Example:

`/api/v1/tasks?status=pending&priority=2`

A production implementation should validate query parameters, apply pagination, and restrict maximum page sizes.

## 4. Controllers

A controller coordinates HTTP input and application operations.

The TaskController exposes operations for:

- Listing tasks
- Retrieving individual tasks
- Creating tasks
- Updating tasks
- Deleting tasks

Controllers should remain relatively small.

They should not directly implement complex database queries or duplicate business rules.

### Controller responsibilities

| Responsibility | Example |
|---|---|
| Receive request | Read task creation data |
| Extract parameters | Retrieve task ID |
| Invoke service | Call `create_task` |
| Select response status | Return 201 after creation |
| Serialize output | Convert task into JSON |

The controller separates the HTTP interface from internal application behavior.

## 5. Service Layer

The service layer contains application-specific business rules.

The `TaskService` coordinates validation and repository operations.

Its operations include:

- `create_task`
- `list_tasks`
- `get_task`
- `update_task`
- `delete_task`

A service can enforce rules that are independent of HTTP.

For example, assigning a task to someone who is not a member of the associated project is a business-rule violation.

Such a rule should not exist exclusively inside an HTTP controller.

### Why services matter

A service can be called by different entry points:

- REST controllers
- Background workers
- Scheduled jobs
- Message consumers
- Internal application processes

This avoids duplicating business logic across different interfaces.

## 6. Middleware

Middleware is a reusable component executed during request processing.

A middleware pipeline allows common operations to be implemented independently of individual controllers.

The implementations demonstrate:

| Middleware | Function |
|---|---|
| Request identification | Assigns a unique request ID |
| Logging | Records request information |
| Timing | Measures execution duration |
| Error processing | Converts application failures into HTTP responses |

### Middleware execution

Request
  |
  v
Request ID Middleware
  |
  v
Logging Middleware
  |
  v
Router
  |
  v
Controller
  |
  v
Response

Middleware can execute additional operations after the downstream handler returns.

This allows request metadata to be included in the response and execution duration to be recorded.

### Middleware ordering

Middleware ordering affects application behavior.

For example, request identification should execute before logging so that the logging component can associate events with a request ID.

Other production middleware commonly handles:

- Authentication
- Authorization
- Rate limiting
- Request validation
- CORS
- Security headers
- Distributed tracing
- Response compression

Authentication identifies the caller.

Authorization determines what the authenticated caller is allowed to do.

These are separate security responsibilities.

## 7. Repository and Data Access

The repository layer isolates application services from the underlying storage mechanism.

The source implementations use in-memory repositories, while the PostgreSQL implementation provides a relational persistence model.

### Repository operations

| Operation | Responsibility |
|---|---|
| Create | Insert a new task |
| Find all | Retrieve a collection |
| Find by ID | Retrieve one task |
| Update | Modify existing data |
| Delete | Remove existing data |

The repository abstraction allows an in-memory implementation to be replaced with PostgreSQL or another persistent database without redesigning the service interface.

### In-memory storage limitations

The Python implementation uses a dictionary protected by a reentrant lock.

The JavaScript implementation uses a Map.

The C++17 implementation uses an unordered map protected by a mutex.

The Java implementation uses ConcurrentHashMap and atomic identifiers.

These structures provide efficient access, but they do not provide durable persistence.

Their contents disappear when the application process terminates.

Concurrent access also requires appropriate synchronization and atomic update behavior.

## 8. PostgreSQL Backend Design

The SQL implementation models an application containing users, projects, project memberships, tasks, routes, and request logs.

### Relational model

Users
  |
  +---- Projects
  |       |
  |       +---- Project Members
  |       |
  |       +---- Tasks
  |
  +---- Assigned Tasks
  |
  +---- Created Tasks

API Routes
  |
  +---- API Request Logs

### Main database tables

| Table | Purpose |
|---|---|
| `users` | Application identities |
| `projects` | Project information |
| `project_members` | Project membership and roles |
| `tasks` | Application tasks |
| `api_routes` | Registered endpoint metadata |
| `api_request_logs` | Request auditing and performance |

### Primary and foreign keys

Primary keys uniquely identify records.

Foreign keys enforce relationships between records.

For example, every task references an existing project and creator.

The `ON DELETE CASCADE` behavior on project tasks removes dependent tasks when their project is deleted.

The `ON DELETE RESTRICT` behavior prevents deletion of users who remain responsible for protected relationships.

These choices represent different data-retention requirements.

### Constraints

The database implements:

- NOT NULL constraints
- Primary keys
- Foreign keys
- Unique constraints
- Check constraints
- Enumerated status values

For example, task priorities must remain between 1 and 5.

Task titles cannot be empty.

Completed tasks must have a completion timestamp.

Database constraints protect data integrity even when an operation bypasses the normal HTTP application.

### Indexes

The SQL implementation includes indexes for:

- Project ownership
- Project membership
- Task status and project
- Task assignment
- Recent task creation
- Active task retrieval
- API request timestamps
- API response status

Indexes improve relevant retrieval operations but consume storage and increase write overhead.

Index selection should be based on actual query patterns and execution plans.

## 9. Database Functions, Procedures, and Triggers

### Functions

The SQL implementation provides:

`create_task`

Creates a task after validating its input and returns the generated identifier.

`update_task`

Updates selected fields using optimistic concurrency control.

`update_modified_timestamp`

Maintains the update timestamp.

`maintain_task_completion`

Maintains completion timestamp consistency.

`validate_task_membership`

Prevents unauthorized project assignments and task creation.

### Procedures

The `complete_task` procedure changes a task's status to completed.

It raises an error when the requested task does not exist.

### Triggers

Triggers automatically execute database logic when particular events occur.

The implementation uses triggers for:

- Updating modification timestamps
- Maintaining completion timestamps
- Validating project membership

These controls enforce integrity close to the data.

A production system should carefully define which business rules belong in database triggers and which belong in application services to avoid hidden or duplicated behavior.

## 10. Request Validation and Error Handling

Request validation protects application boundaries.

The implementations validate:

- Required titles
- Maximum title length
- Description length
- Supported task statuses
- Unknown input fields
- Positive task identifiers
- JSON object structure
- Request body size
- Supported content types

### Error-handling structure

Invalid request
  |
  v
Validation
  |
  +---- Invalid input
  |       |
  |       v
  |      HTTP 400
  |
  +---- Valid input
          |
          v
       Service
          |
          +---- Resource missing
          |       |
          |       v
          |      HTTP 404
          |
          +---- Unexpected failure
                  |
                  v
                 HTTP 500

Error responses should provide useful information without exposing stack traces, database credentials, internal file paths, or sensitive application details.

The JavaScript and Python implementations also limit request-body size.

## 11. Concurrency and State Management

Backend applications can process multiple requests concurrently.

This introduces potential race conditions when requests modify shared resources.

### Language-specific approaches

| Language | Mechanism |
|---|---|
| Python | Threading locks |
| JavaScript | Event loop and asynchronous operations |
| C++17 | Mutex and lock guards |
| Java 17 | ConcurrentHashMap and AtomicInteger |
| PostgreSQL | Transactions and row-level locking |

The JavaScript implementation uses asynchronous functions and Promises to organize request processing.

The C++ implementation protects shared repository operations using mutexes.

The Java implementation uses concurrent collections and atomic identifiers.

PostgreSQL provides transactional operations and optimistic concurrency control through task version numbers.

### Optimistic concurrency control

The SQL `update_task` function checks the expected version before updating a record.

If the stored version does not match the client's version, the update fails.

This prevents one client from silently overwriting a newer update made by another client.

The version increases after each successful modification.

## 12. Backend Security

The implementations demonstrate selected security controls, but they are educational backend examples rather than complete production security systems.

Important production requirements include:

| Security control | Purpose |
|---|---|
| HTTPS | Protect network communication |
| Password hashing | Protect stored credentials |
| Authentication | Verify user identity |
| Authorization | Enforce access permissions |
| Input validation | Reject invalid data |
| Parameterized SQL | Prevent SQL injection |
| Rate limiting | Reduce abusive request traffic |
| Request size limits | Reduce resource exhaustion |
| Security headers | Improve browser-side protections |
| Audit logging | Support security investigations |
| Secret management | Protect credentials and signing keys |

The SQL sample uses illustrative password-hash values. These are not valid password-storage recommendations.

Production password storage should use an established password-hashing algorithm with appropriate parameters and unique salts.

The SQL membership trigger provides an integrity check for project assignments. It is not a replacement for complete application-level authorization.

Production database access should also use appropriately restricted roles and privileges.

## 13. Implementation Comparison

| Feature | Python | JavaScript | C++17 | Java 17 | PostgreSQL |
|---|---|---|---|---|---|
| HTTP processing | Standard library server | Node.js HTTP | Simulated request engine | Java HttpServer | Database layer |
| Routing | Regex router | Regex router | Regex router | Pattern-based router | Route registry |
| Controllers | Class-based | Async class | Class-based | Enterprise service model | Not applicable |
| Middleware | Function pipeline | Promise pipeline | Function composition | Middleware interface | Triggers |
| Repository | Dictionary | Map | Unordered map | ConcurrentHashMap | Relational tables |
| Validation | Validator class | Static validator | Validator class | Validator class | Constraints and functions |
| Error handling | Exceptions | HTTP exceptions | Exceptions | Custom exceptions | SQL exceptions |
| Concurrency | Locks | Event loop | Mutex | Concurrent collections | Transactions |

The implementations share the same task-management domain but use different language capabilities and architectural approaches.

The C++17 implementation focuses on explicit resource management, domain modeling, and synchronization.

The Java 17 implementation emphasizes interfaces, immutable records, service abstractions, and enterprise-oriented component boundaries.

The JavaScript implementation emphasizes asynchronous execution and event-driven request handling.

The Python implementation demonstrates compact application composition and standard-library HTTP processing.

The PostgreSQL implementation concentrates on durable relational integrity and database-level operations.

## 14. Running the Implementations

### Python

Run:

`python backend_fundamentals.py`

The script runs its integration tests and starts the HTTP server on port 8000.

### JavaScript

Run:

`node backend_fundamentals.js`

The HTTP server listens on port 8001.

Run the test mode separately:

`node backend_fundamentals.js --test`

### C++17

Compile:

`g++ -std=c++17 -O2 -Wall -Wextra backend.cpp -o backend`

Run:

`./backend`

The program executes the routing, validation, service, and repository tests.

### Java 17

Compile:

`javac BackendFundamentals.java`

Run:

`java BackendFundamentals`

Run tests:

`java BackendFundamentals --test`

The HTTP server listens on port 8002.

### PostgreSQL

Execute:

`psql -U postgres -d postgres -f backend_fundamentals.sql`

The SQL script creates the schema, domain types, tables, constraints, indexes, functions, procedures, triggers, views, and sample records.

The transaction examples demonstrate completion, optimistic concurrency, and rollback.

## 15. API Testing

The Python, JavaScript, and Java implementations provide HTTP servers that can be tested independently.

The following examples use the Python server on port 8000.

### Health check

`GET http://127.0.0.1:8000/health`

Expected status: 200.

### Create a task

`POST http://127.0.0.1:8000/api/v1/tasks`

Request body:

`{"title":"Build REST API","description":"Implement backend routing"}`

Expected status: 201.

### Retrieve tasks

`GET http://127.0.0.1:8000/api/v1/tasks`

Expected status: 200.

### Retrieve one task

`GET http://127.0.0.1:8000/api/v1/tasks/1`

Expected status: 200 when the task exists.

### Update a task

`PATCH http://127.0.0.1:8000/api/v1/tasks/1`

Request body:

`{"status":"in_progress"}`

Expected status: 200.

### Delete a task

`DELETE http://127.0.0.1:8000/api/v1/tasks/1`

Expected status: 200.

### Invalid request

`POST http://127.0.0.1:8000/api/v1/tasks`

Request body:

`{"title":""}`

Expected status: 400.

### Missing resource

`GET http://127.0.0.1:8000/api/v1/tasks/9999`

Expected status: 404.

## 16. Limitations and Production Considerations

The source implementations intentionally use limited infrastructure to demonstrate backend architecture without external dependencies.

Important differences from production systems include:

- In-memory repositories do not provide durable persistence.
- The Java adapter uses a deliberately restricted flat JSON parser.
- The C++ implementation simulates request processing rather than providing a network-facing HTTP server.
- The Python implementation does not include production authentication.
- The JavaScript implementation does not include a persistent database adapter.
- The SQL membership trigger does not replace complete authorization.
- The SQL example uses illustrative test credentials.
- The implementations do not provide complete distributed tracing, rate limiting, or API documentation.

A production backend must integrate durable storage, authenticated identities, authorization policies, controlled configuration, secure transport, monitoring, backup procedures, and reliable deployment practices.

The central architectural principle remains the separation of HTTP communication, routing, controllers, services, repositories, and persistent data management.
