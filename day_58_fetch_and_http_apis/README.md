# Fetch and HTTP APIs

## Scope

This project models the complete lifecycle of HTTP API requests using five complementary implementations:

| File | Primary perspective | Main focus |
|---|---|---|
| Python | HTTP client and local API simulation | Request construction, JSON, status handling, retries, validation |
| JavaScript | Asynchronous event-driven client | Fetch, Promises, `AbortController`, instrumentation, retries |
| C++17 | Systems-oriented API engine | Domain modeling, request validation, response classification |
| Java 17 | Enterprise HTTP client | `HttpClient`, immutable records, policies, asynchronous execution |
| PostgreSQL | Persistent API workflow model | Requests, responses, policies, status rules, reporting, transactions |

The central relationship is:

`HTTP request → validation → transmission → server processing → HTTP response → status evaluation → application decision`

The four domain areas are intentionally distinct:

- An HTTP method expresses the intended operation.
- Headers carry request and response metadata.
- JSON represents structured application data.
- Status codes communicate protocol-level outcomes.

## HTTP Request Model

An HTTP request consists of a method, target URI, headers, optional body, and protocol metadata.

Typical methods have different semantic purposes:

| Method | Typical purpose | Body commonly used |
|---|---|---|
| `GET` | Retrieve a resource | No |
| `POST` | Create or trigger an operation | Yes |
| `PUT` | Replace a resource representation | Yes |
| `PATCH` | Partially modify a resource | Yes |
| `DELETE` | Remove a resource | Usually no |

The implementations validate method-specific behavior rather than treating every request as an interchangeable operation.

The Python client represents the method with `HttpMethod`. The JavaScript client validates supported methods before calling `fetch`. The C++ request object uses an enum and explicit validation. Java models the method as an enum inside an immutable request record. PostgreSQL uses a dedicated `http_method` enum.

## Headers

Headers are metadata fields associated with HTTP messages.

Examples include:

- `Accept`
- `Content-Type`
- `User-Agent`
- `Authorization`
- `Cache-Control`
- `Retry-After`
- application-specific tracing headers such as `X-Request-ID`

`Accept: application/json` indicates that the client expects JSON.

`Content-Type: application/json` describes a JSON request body.

The implementations also treat header validation as a security boundary. Carriage-return and line-feed characters are rejected to prevent malformed or injected HTTP header values.

The Python, JavaScript, C++, Java, and PostgreSQL implementations all include this validation concept in their request-processing paths.

## JSON

JSON is used as the structured representation for API payloads.

A request can contain:

`{"name":"Priya"}`

A response can contain:

`{"id":3,"name":"Priya","created":true}`

JSON processing has two separate concerns:

1. Serialization converts application data into a request representation.
2. Parsing converts the response representation back into application data.

The Python implementation uses the standard `json` module.

The JavaScript implementation uses `JSON.stringify()` and `JSON.parse()`.

The C++ implementation uses a deliberately small JSON extraction mechanism because the program avoids third-party libraries. It is sufficient for the constrained demonstration payloads but is not a general JSON parser.

The Java implementation sends JSON strings through `HttpRequest.BodyPublishers`.

PostgreSQL stores structured request and response data in `JSONB`, allowing indexed and operator-based inspection of headers and bodies.

## HTTP Status Codes

Status codes belong to five broad classes:

| Range | Class | Meaning |
|---|---|---|
| `100–199` | Informational | Protocol-level information |
| `200–299` | Success | Request was successfully processed |
| `300–399` | Redirection | Further action or location information |
| `400–499` | Client error | Request could not be processed as submitted |
| `500–599` | Server error | Server-side failure |

The PostgreSQL function `classify_status()` centralizes this classification.

The implementations treat successful responses as `200–299` rather than checking only for `200`. This matters because successful operations can legitimately return `201 Created` or `204 No Content`.

Common failure examples include:

- `400 Bad Request`
- `404 Not Found`
- `408 Request Timeout`
- `422 Unprocessable Entity`
- `429 Too Many Requests`
- `500 Internal Server Error`
- `503 Service Unavailable`

## Request Lifecycle

The request lifecycle is explicitly modeled as:

`CREATED → VALIDATED → SENT → RECEIVED`

A failed transport or validation operation enters a failure path rather than being represented as a successful response.

The Python implementation stores this state in `RequestPhase`.

The C++ implementation uses `RequestState`.

The Java implementation uses `LifecycleState`.

The PostgreSQL model persists request state and records state changes in `request_events`.

This separation prevents an application from confusing a successfully transmitted HTTP request with a successful business operation. A request can reach a server and still receive `404`, `409`, `422`, or `500`.

## Python Implementation

The Python program builds an `ApiRequest` dataclass containing:

- HTTP method
- URL
- headers
- query parameters
- optional JSON body

Validation occurs before network transmission.

`ApiClient` uses `urllib.request`, so no third-party HTTP package is required. It adds standard `Accept` and `User-Agent` headers and serializes JSON bodies when present.

The client also implements bounded retries for transient conditions such as:

- `408`
- `429`
- `500`
- `502`
- `503`
- `504`

Retry delays use exponential backoff with a maximum delay.

A local `ThreadingHTTPServer` supplies `/health`, `/users`, and error responses. This makes the script executable without requiring an external API.

The server limits request bodies to 1 MB and rejects invalid JSON or missing required fields.

## JavaScript Implementation

The JavaScript program uses the Node.js Fetch API.

`FetchClient` demonstrates:

- URL construction with `URL`
- HTTP method selection
- header validation
- JSON serialization
- `AbortController` timeouts
- asynchronous `Promise` handling
- bounded retries
- response instrumentation

`RequestMetrics` extends `EventEmitter`.

It emits request-start and response events while tracking:

- completed requests
- failures
- total response duration
- average response duration

This represents an event-driven API client rather than a direct translation of the Python implementation.

The local Node.js HTTP server provides deterministic API responses for GET and POST operations.

## C++17 Implementation

The C++ program treats the API as a small systems-oriented domain.

`HttpRequest` owns request state and validation.

`HttpResponse` represents the protocol result.

`RepositoryApi` provides an in-memory application service with users and request-specific behavior.

`ApiGateway` applies retry classification.

The implementation deliberately avoids external HTTP libraries. Its focus is request modeling, validation, status evaluation, and separation of transport-like behavior from application behavior.

The program also demonstrates security validation for:

- unsupported URL schemes
- newline characters in URLs
- CR/LF characters in headers
- invalid request bodies for selected methods

The JSON handling is intentionally constrained. It should not be mistaken for a production JSON parser.

## Java 17 Implementation

The Java program models an enterprise-style HTTP client around Java's standard `HttpClient`.

`ApiRequest` is an immutable record containing:

- method
- URI
- headers
- optional JSON body

`ResponsePolicy` separates response evaluation from transport behavior.

`SuccessPolicy` defines the rule that only `2xx` responses are accepted.

`EnterpriseApiClient` provides:

- connection timeouts
- request timeouts
- asynchronous `sendAsync`
- response classification
- bounded retries
- exponential retry delay
- transport exception handling

Java's immutable records make request data explicit, while enums provide controlled method and lifecycle states.

The example also demonstrates validation failures without requiring successful access to an external service.

## PostgreSQL Implementation

The PostgreSQL model treats API execution as persistent operational data.

The main entities are:

`api_clients → api_requests → api_responses`

Supporting entities provide:

`api_requests → request_events`

and:

`api_policies → status_rules`

This separates observed HTTP behavior from policy.

A request stores method, endpoint, headers, body, lifecycle state, attempt count, and timestamps.

A response stores:

- status code
- reason
- headers
- body
- duration
- receipt timestamp

`api_policies` defines client-independent rules such as retry limits and timeout values.

`status_rules` permits explicit policy decisions for individual HTTP status codes.

## Database Integrity

The database enforces important constraints directly.

Examples include:

- unique client names
- valid HTTP methods through an enum
- valid lifecycle states through an enum
- status codes limited to `100–599`
- non-negative attempt counts
- positive timeout values
- positive retry limits
- non-negative response durations

A trigger rejects CR/LF characters in HTTP headers.

Another trigger records lifecycle changes in `request_events`.

A response trigger moves its associated request to the `received` state.

This keeps critical integrity rules at the database boundary rather than relying only on application code.

## Retry Semantics

Not every failure should be retried.

The implementations classify several statuses as potentially transient:

`408, 429, 500, 502, 503, 504`

A retry policy should also consider:

- maximum attempts
- request idempotency
- server-provided retry timing
- request timeout
- rate limiting
- duplicate side effects

A retry of a `GET` is generally less dangerous than blindly retrying a non-idempotent operation such as a payment-creating `POST`.

The examples use bounded retries rather than infinite retry loops.

The PostgreSQL model represents this distinction through `status_rules` and policy-specific attempt limits.

## Error Handling

HTTP failures and transport failures are different.

An HTTP failure means the server returned a response such as `404` or `503`.

A transport failure means the client could not obtain an HTTP response because of a timeout, connection failure, DNS failure, or another network-level problem.

The implementations preserve this distinction:

| Failure | Example | Client interpretation |
|---|---|---|
| Validation | Invalid URL | Reject before transmission |
| Transport | Connection timeout | Retry according to policy |
| HTTP client error | `404` | Response received, operation rejected |
| HTTP server error | `503` | Response received, possibly retry |
| Parsing | Invalid JSON | Response received but unusable |

## Security Controls

HTTP clients should treat externally supplied URLs, headers, payloads, and responses as untrusted.

The implementations demonstrate several controls:

- restrict URL schemes to HTTP and HTTPS
- reject CR/LF in header names and values
- validate request methods
- bound retry counts
- impose timeouts
- limit demonstration request-body sizes
- validate JSON application fields
- avoid treating every status as success

Real systems should also protect credentials, validate TLS certificates, avoid logging secrets, enforce authorization, apply rate limits, and restrict outbound destinations where SSRF is a concern.

The example clients intentionally do not hard-code credentials.

## Performance Considerations

HTTP performance is affected by:

- connection establishment
- DNS resolution
- TLS negotiation
- server processing time
- response size
- network latency
- serialization and parsing
- retry delays

The JavaScript implementation records request duration through `performance.now()`.

The Python implementation records elapsed time with `time.monotonic()`.

The C++ implementation uses `std::chrono::steady_clock`.

The Java implementation records elapsed time using `System.nanoTime()`.

PostgreSQL stores response duration and provides aggregate endpoint performance reporting.

Indexes are applied to request state, client/time access, response status, request event history, and JSON headers where those access patterns provide useful lookup paths.

## Query and Reporting Model

The PostgreSQL script provides queries for:

- complete request lifecycle reporting
- status classification
- policy-based request evaluation
- endpoint performance
- JSON header extraction
- failure reporting
- transactional retry-state updates
- success and failure aggregation

The `evaluate_request()` function distinguishes:

`accepted`

from:

`retry`

and:

`rejected`

This prevents HTTP status classification from being confused with the final application decision.

## Edge Cases

The implementations account for several important edge cases:

- empty header names
- header injection characters
- unsupported URL schemes
- missing hosts
- invalid JSON
- empty required fields
- nonexistent resources
- successful `204 No Content`
- client errors
- transient server errors
- excessive retry attempts
- request timeouts
- empty response bodies
- malformed response JSON
- GET or DELETE requests carrying disallowed bodies

These cases demonstrate why an HTTP API client needs explicit lifecycle and validation logic rather than only a method call that sends bytes over the network.

## Practical Distinctions

The central concepts should not be collapsed into one abstraction.

| Concept | Responsibility |
|---|---|
| HTTP method | States the intended operation |
| URL | Identifies the target resource or endpoint |
| Request headers | Communicate request metadata |
| Request body | Carries application data when applicable |
| JSON | Encodes structured application data |
| Status code | Reports protocol-level result |
| Response headers | Communicate response metadata |
| Response body | Carries returned application data |
| Retry policy | Determines whether another attempt is appropriate |
| Application policy | Determines whether the response satisfies business requirements |

The implementations keep these responsibilities separate so that request construction, transport behavior, protocol interpretation, and application decisions can evolve independently.

## File Relationship

The five implementations describe the same technical domain from different engineering perspectives:

`Python`
`  ↓`
`HTTP client + local executable API`

`JavaScript`
`  ↓`
`Fetch + asynchronous event-driven lifecycle`

`C++17`
`  ↓`
`Request/response domain engine`

`Java 17`
`  ↓`
`Enterprise HTTP client + response policy`

`PostgreSQL`
`  ↓`
`Persistent request, response, policy, and reporting model`

The shared domain is HTTP API communication, while each implementation emphasizes different mechanisms rather than duplicating the same program structure.
