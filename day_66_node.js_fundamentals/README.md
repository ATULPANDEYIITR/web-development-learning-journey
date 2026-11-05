# Node.js Fundamentals

## 1. Node.js Runtime Architecture

Node.js is a JavaScript runtime that executes JavaScript outside a web browser. It combines the V8 JavaScript engine with native runtime capabilities and an event-driven architecture.

The runtime provides access to operating-system resources, filesystem operations, networking, cryptography, streams, and process management.

### Main architectural components

| Component | Responsibility |
|---|---|
| V8 | Compiles and executes JavaScript |
| Node.js runtime | Provides application execution facilities |
| libuv | Supports asynchronous I/O and the event loop |
| Event loop | Coordinates asynchronous callbacks |
| Thread pool | Handles selected operations such as filesystem and DNS work |
| Node.js APIs | Expose filesystem, networking, process, and other capabilities |
| Module system | Organizes and loads application dependencies |

### Runtime execution model

The general execution flow is:

Application source code → Node.js runtime → V8 execution → asynchronous operations → event loop → callbacks and Promise continuations.

Node.js uses an event-driven, non-blocking I/O model. This allows applications to handle many concurrent I/O operations without creating a separate JavaScript execution thread for each request.

JavaScript execution on the main isolate is generally single-threaded. This does not mean every operation is executed on one operating-system thread. Node.js uses additional runtime facilities for selected asynchronous operations.

### Event loop

The event loop coordinates asynchronous operations and their callbacks.

Important phases include:

- Timers: Executes eligible timer callbacks.
- Pending callbacks: Executes certain deferred system callbacks.
- Poll: Retrieves and processes I/O events.
- Check: Executes `setImmediate()` callbacks.
- Close callbacks: Processes certain resource-close events.

Promise callbacks and other microtasks have scheduling behavior associated with the event loop. `process.nextTick()` has its own queue and can affect scheduling priority.

Long-running synchronous operations block the JavaScript execution thread. This can delay unrelated requests and callbacks.

---

## 2. Node.js Installation and Execution

Node.js applications can be executed directly from the terminal.

A JavaScript file can be executed using:

`node filename.js`

The runtime exposes information about the current execution environment.

| Command | Purpose |
|---|---|
| `node --version` | Displays the Node.js version |
| `node --help` | Displays runtime options |
| `node --check app.js` | Checks JavaScript syntax |
| `node --inspect app.js` | Starts debugging support |
| `node --watch app.js` | Restarts execution when files change |
| `node --trace-warnings app.js` | Provides warning diagnostics |
| `node --max-old-space-size=512 app.js` | Configures the V8 old-generation memory limit |

Node.js version compatibility should be established before deployment.

An application may depend on specific JavaScript language features, runtime APIs, native modules, or package versions.

The Python, C++17, and Java 17 programs model runtime compatibility checks. They do not execute Node.js themselves.

---

## 3. Module System

Modules divide an application into reusable and independently maintainable components.

Node.js supports two major JavaScript module systems.

### CommonJS

CommonJS is the traditional Node.js module system.

Its main mechanisms are:

- `require()` for importing modules.
- `module.exports` for exporting module functionality.
- `exports` as a reference to the module's export object.
- `__filename` for the current module filename.
- `__dirname` for the current module directory.

Example structure:

- `app.js`
- `services/inventory.js`
- `config/database.js`

CommonJS modules are loaded and evaluated through the CommonJS module loader. Their exports are cached by resolved module identity.

The JavaScript implementation uses CommonJS to import built-in Node.js modules.

### ECMAScript Modules

ECMAScript Modules are the standardized JavaScript module system.

Their principal mechanisms are:

- `import` for importing dependencies.
- `export` for exposing functions, classes, and values.
- `export default` for default exports.
- `import()` for dynamic asynchronous module loading.

A project can declare ECMAScript Module behavior through the `type` field in `package.json` or use the `.mjs` extension.

The `.cjs` extension explicitly identifies CommonJS files.

Example package configuration:

| Property | Meaning |
|---|---|
| `name` | Package name |
| `version` | Application version |
| `type` | Module interpretation |
| `main` | Traditional package entry point |
| `exports` | Public package entry points |
| `scripts` | Executable project commands |
| `dependencies` | Production dependencies |
| `devDependencies` | Development dependencies |
| `engines` | Runtime compatibility requirements |

### Built-in modules

Node.js provides built-in modules without requiring separate npm installation.

| Module | Purpose |
|---|---|
| `node:fs` | Filesystem access |
| `node:path` | Path manipulation |
| `node:os` | Operating-system information |
| `node:http` | HTTP server and client functionality |
| `node:https` | HTTPS functionality |
| `node:events` | EventEmitter implementation |
| `node:crypto` | Cryptographic operations |
| `node:util` | Utility functionality |
| `node:stream` | Streaming data |
| `node:buffer` | Binary data handling |
| `node:url` | URL processing |
| `node:process` | Process information and control |

The `node:` prefix explicitly identifies built-in modules.

### Module resolution

When a module is imported, Node.js determines its location using the applicable module-resolution rules.

For CommonJS, resolution can involve:

- Core modules.
- Relative paths.
- Absolute paths.
- Package directories.
- Package metadata.
- `node_modules` directories.

ECMAScript Modules use different resolution rules and require explicit relative file extensions in many import scenarios.

Circular dependencies require careful design. CommonJS and ECMAScript Modules have different initialization and evaluation behavior.

The C++ and Java implementations model module dependency graphs and detect unresolved dependencies and circular references.

---

## 4. Filesystem Operations

The filesystem module provides access to files and directories.

Node.js supports synchronous, callback-based, and Promise-based filesystem APIs.

### Important operations

| Operation | API |
|---|---|
| Read file | `fs.readFile()` |
| Write file | `fs.writeFile()` |
| Append content | `fs.appendFile()` |
| Delete file | `fs.unlink()` |
| Create directory | `fs.mkdir()` |
| Read directory | `fs.readdir()` |
| Inspect file metadata | `fs.stat()` |
| Rename file | `fs.rename()` |
| Remove directory | `fs.rm()` |
| Check file access | `fs.access()` |

### Synchronous and asynchronous operations

Synchronous operations block JavaScript execution until completion.

Asynchronous operations allow the event loop to process other work while I/O is pending.

The `node:fs/promises` API provides Promise-based filesystem operations.

The JavaScript implementation uses asynchronous functions and `await` to manage filesystem operations.

### Path handling

The `node:path` module provides platform-aware path manipulation.

Important functions include:

- `path.join()`
- `path.resolve()`
- `path.basename()`
- `path.dirname()`
- `path.extname()`
- `path.relative()`

A filesystem path should not be trusted merely because it comes from an application request.

Path traversal attacks attempt to access resources outside an authorized directory using paths containing parent-directory references.

The JavaScript, C++, Python, and Java implementations validate resolved paths against an application root.

Filesystem security also requires attention to symbolic links, permissions, file ownership, and race conditions.

A path-validation check alone does not eliminate every filesystem race condition. Applications processing untrusted paths should use restrictive directory permissions and carefully controlled file operations.

### Atomic file operations

The JavaScript and Python implementations use temporary files followed by rename operations to reduce the risk of exposing partially written configuration files.

Atomic replacement depends on filesystem behavior and operating-system support.

---

## 5. Process Management

Every Node.js application executes within an operating-system process.

The global `process` object exposes information and controls associated with that process.

### Important process properties

| Property | Purpose |
|---|---|
| `process.argv` | Command-line arguments |
| `process.env` | Environment variables |
| `process.pid` | Process identifier |
| `process.cwd()` | Current working directory |
| `process.execPath` | Node.js executable path |
| `process.version` | Node.js version |
| `process.versions` | Runtime dependency versions |
| `process.platform` | Operating-system platform |
| `process.arch` | CPU architecture |
| `process.memoryUsage()` | Memory usage statistics |
| `process.uptime()` | Process uptime |
| `process.exitCode` | Process exit status |

### Command-line arguments

`process.argv` contains the executable path, application entry point, and additional command-line arguments.

For example, an application can receive:

- A configuration filename.
- A deployment environment.
- A listening port.
- An operational command.

Arguments should be validated before being used.

### Process lifecycle

A typical application lifecycle is:

Startup → Configuration loading → Runtime validation → Resource initialization → Application execution → Shutdown.

Node.js applications can listen for process signals.

Important signals include:

- `SIGINT`: Commonly associated with terminal interruption.
- `SIGTERM`: Commonly used to request process termination.

A graceful shutdown should stop accepting new requests, complete or cancel active work, close database connections, and release resources.

The JavaScript implementation demonstrates process inspection and sets a non-zero exit status when an application failure occurs.

Calling `process.exit()` immediately can terminate pending asynchronous operations. Using `process.exitCode` is generally preferable when the event loop should finish naturally.

---

## 6. Environment Variables

Environment variables provide configuration independently of application source code.

They are useful for separating deployment configuration from executable application logic.

Examples include:

| Variable | Purpose |
|---|---|
| `NODE_ENV` | Application environment |
| `PORT` | Network listening port |
| `DATABASE_URL` | Database connection configuration |
| `LOG_LEVEL` | Logging verbosity |
| `NODE_OPTIONS` | Runtime configuration options |
| `PATH` | Executable search paths |

### Accessing environment variables

Node.js exposes environment variables through `process.env`.

Environment-variable values are strings and must be converted and validated when numerical or Boolean configuration is expected.

For example, a port value should be checked for:

- Numeric format.
- Integer representation.
- Valid range.
- Missing or empty values.

### Configuration separation

A production application should avoid embedding credentials in source code.

Sensitive configuration should be supplied through controlled deployment mechanisms or a dedicated secrets manager.

Environment variables are not automatically encrypted. Their exposure depends on process permissions, diagnostic tooling, operating-system controls, container configuration, and deployment practices.

The implementations avoid displaying complete database connection strings or secret values.

---

## 7. Asynchronous Programming

Node.js supports several mechanisms for asynchronous execution.

### Callbacks

Callbacks are functions supplied to operations that execute later.

They are commonly found in older Node.js APIs.

Excessively nested callbacks can make error handling and program flow difficult to maintain.

### Promises

Promises represent the eventual completion or failure of asynchronous operations.

Their states are:

- Pending.
- Fulfilled.
- Rejected.

A Promise can be processed using `.then()`, `.catch()`, and `.finally()`.

### Async and await

`async` and `await` provide a structured syntax for Promise-based operations.

They make asynchronous workflows easier to read and maintain.

The JavaScript implementation uses asynchronous filesystem functions and `Promise.all()` to execute independent operations concurrently.

### Error handling

Asynchronous errors should be handled at the correct boundary.

Important mechanisms include:

- `try...catch` for awaited operations.
- `.catch()` for Promise rejection handling.
- Centralized application error handling.
- Explicit process exit codes.
- Resource cleanup through `finally`.

Uncaught exceptions and unhandled Promise rejections should not be treated as normal application control flow.

---

## 8. Event-Driven Programming

The `node:events` module provides the `EventEmitter` class.

An event emitter allows one part of an application to publish an event while other components subscribe to it.

Important methods include:

| Method | Purpose |
|---|---|
| `on()` | Registers an event listener |
| `once()` | Registers a listener for one execution |
| `emit()` | Publishes an event |
| `off()` | Removes a listener |
| `removeListener()` | Removes a registered listener |
| `removeAllListeners()` | Removes listeners |

The JavaScript implementation creates application lifecycle events for startup, file creation, and error reporting.

Event-driven architecture is useful for decoupling application components.

Event listeners must be managed carefully. Unnecessary listeners can create memory leaks or unexpected repeated execution.

---

## 9. Deployment and Runtime Governance

The implementations model a deployment-validation workflow.

The objective is to establish whether an application satisfies its declared runtime and configuration requirements before deployment.

### Deployment validation sequence

Application registration
→ Runtime compatibility
→ Environment validation
→ Module dependency validation
→ Entry-point verification
→ Filesystem validation
→ Deployment readiness.

### Validation categories

| Category | Validation |
|---|---|
| Runtime | Installed Node.js version meets minimum requirement |
| Environment | Required variables are available |
| Modules | Required dependencies can be resolved |
| Filesystem | Application resources exist and are accessible |
| Configuration | Values satisfy expected formats and ranges |
| Deployment | All mandatory checks pass |

A warning does not necessarily prevent deployment. A failed mandatory check should block deployment.

The Python implementation provides a deployment inspector with structured findings.

The C++ implementation uses a module dependency graph and recursive validation.

The Java implementation uses explicit domain records, a policy interface, and a deployment service.

The PostgreSQL implementation stores runtime inventory and validation results in relational tables.

---

## 10. Implementation Architecture

The five executable source files approach the topic from different engineering perspectives.

| Deliverable | Main implementation | Engineering perspective |
|---|---|---|
| Python | Runtime deployment inspector | Configuration and filesystem validation |
| JavaScript | Node.js application | Native runtime and asynchronous execution |
| C++17 | Runtime governance engine | Dependency graphs and resource management |
| Java 17 | Enterprise deployment governance | Domain models and policy-based validation |
| PostgreSQL | Runtime configuration registry | Relational integrity and operational reporting |

### Python architecture

The Python script uses:

- Dataclasses for runtime and module definitions.
- Enums for validation severity.
- Dictionaries for environment configuration.
- A module registry for dependency resolution.
- `pathlib` for filesystem management.
- Temporary directories for isolated testing.
- Structured findings for deployment decisions.

### JavaScript architecture

The JavaScript file uses actual Node.js capabilities.

Its architecture includes:

- CommonJS module loading.
- Built-in modules.
- Promise-based filesystem access.
- EventEmitter.
- Process inspection.
- Environment configuration.
- Asynchronous execution.
- Graceful resource cleanup.

This is the implementation that directly exercises the Node.js runtime.

### C++17 architecture

The C++ program models deployment governance using:

- Structs for runtime versions and validation results.
- Classes for environment management.
- A module dependency graph.
- Recursive dependency traversal.
- Filesystem path validation.
- Exception-based failure handling.

Its module graph traversal has a time complexity of \(O(V+E)\), where \(V\) represents modules and \(E\) represents dependency relationships, assuming efficient map and set operations.

### Java 17 architecture

The Java program uses:

- Records for immutable domain data.
- Enums for application modes and validation states.
- Interfaces for deployment policies.
- Collections for dependency management.
- Custom exceptions for configuration failures.
- Service classes for deployment evaluation.
- NIO for filesystem operations.

The policy interface separates deployment rules from deployment execution.

### PostgreSQL architecture

The database schema uses separate entities for:

- Applications.
- Runtime instances.
- Modules.
- Application-module relationships.
- Module dependencies.
- Environment variable definitions.
- Environment configurations.
- Filesystem resources.
- Deployments.
- Validation checks.

Foreign keys preserve relational integrity.

Unique constraints prevent duplicate module versions and application configurations.

Check constraints restrict invalid values.

Indexes support application lookup, runtime history, deployment status, and validation reporting.

The validation function evaluates runtime compatibility, environment configuration, module metadata, and entry-point registration.

The deployment procedure stores validation outcomes and determines whether a deployment is ready or blocked.

---

## 11. Security Considerations

Node.js applications interact with operating-system resources and external dependencies. Security controls must therefore cover both application code and runtime configuration.

| Risk | Control |
|---|---|
| Path traversal | Validate resolved paths against an authorized root |
| Secret exposure | Keep credentials outside source code and logs |
| Dependency compromise | Validate package provenance and versions |
| Excessive permissions | Apply least-privilege filesystem and process permissions |
| Invalid configuration | Validate types, formats, and permitted ranges |
| Memory exhaustion | Monitor memory and configure appropriate limits |
| Event-loop blocking | Avoid expensive synchronous operations in request handlers |
| Unhandled asynchronous failures | Implement structured error handling |
| Dependency vulnerabilities | Maintain and review dependency inventories |
| Unsafe shutdown | Close resources and handle termination signals |

A dependency registry does not prove that a package is trustworthy. Package integrity, vulnerability analysis, licensing, and supply-chain controls require separate verification.

The PostgreSQL schema stores secret configuration metadata rather than actual credential-bearing values. Its metadata checks are not a substitute for a secrets manager.

---

## 12. Performance and Operational Considerations

### Runtime performance

Node.js performs well for applications involving substantial asynchronous I/O.

CPU-intensive workloads can block the main JavaScript execution thread.

Possible architectural responses include:

- Worker threads for suitable CPU-intensive tasks.
- Child processes for process isolation.
- Streams for large data processing.
- Asynchronous filesystem APIs.
- Bounded concurrency for external operations.

### Filesystem performance

Repeated synchronous filesystem operations can reduce application responsiveness.

Large files should generally be processed with streams when loading the complete file into memory would be inefficient.

Atomic file replacement can improve consistency but does not guarantee durability across every filesystem failure.

### Module performance

Module loading and initialization contribute to application startup time.

Unnecessary dependencies increase installation size, maintenance requirements, and potential security exposure.

### Process monitoring

Production monitoring should examine:

- CPU utilization.
- Heap usage.
- Resident memory.
- Event-loop delay.
- Request latency.
- Error rates.
- Process restarts.
- Open handles.
- Dependency health.

The Node.js runtime exposes memory and process information, while external monitoring systems can collect additional operating-system and application metrics.

---

## 13. Execution Instructions

### Python

Run the Python implementation using:

`python node_fundamentals.py`

It uses only the Python standard library.

### JavaScript

Run the Node.js implementation using:

`node node_fundamentals.js`

The JavaScript implementation requires Node.js 18 or newer.

It uses built-in Node.js modules and does not require npm packages.

### C++17

Compile using:

`g++ -std=c++17 -O2 -Wall -Wextra -pedantic node_fundamentals.cpp -o node_fundamentals`

Run using:

`./node_fundamentals`

On Windows, execute `node_fundamentals.exe`.

### Java 17

Compile using:

`javac NodeFundamentals.java`

Run using:

`java NodeFundamentals`

### PostgreSQL

Execute the SQL script using PostgreSQL 15 or newer.

The script creates the `node_runtime` schema and its associated objects.

The deployment-validation procedure demonstrates successful and unsuccessful configuration scenarios.

The script uses transactions to demonstrate rollback behavior and preserves the final successful deployment-validation records.

---

## 14. Technical Limitations

The implementations intentionally model selected Node.js runtime and deployment mechanisms rather than reproducing the complete Node.js execution environment.

- The Python, C++17, and Java 17 programs are governance simulations, not JavaScript runtimes.
- The JavaScript program uses CommonJS and built-in modules; it does not implement a complete production HTTP server.
- The module registries model dependency resolution but do not reproduce every Node.js package-resolution rule.
- Filesystem validation cannot eliminate every symbolic-link or time-of-check/time-of-use race.
- Runtime compatibility checks do not guarantee that native dependencies are compatible with a particular operating system.
- The PostgreSQL database records configuration metadata but does not execute Node.js processes.
- A deployment marked ready has passed the modeled checks, not every possible production-readiness or security assessment.

These distinctions are important when applying the examples to actual Node.js application development and deployment.
