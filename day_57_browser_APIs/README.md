# Browser APIs: Storage, Cookies, History, and URLs

## Scope

This project models five browser-facing API families:

| API | Primary purpose | Lifetime or scope | Main implementation concern |
|---|---|---|---|
| `localStorage` | Persistent key-value data | Browser origin | Persistence and quota |
| `sessionStorage` | Tab/session-scoped key-value data | Browser tab/session | Isolation from persistent state |
| Cookies | Small HTTP-associated state | Configurable lifetime | Security attributes and server interaction |
| History API | Client-side navigation state | Current browsing context | URL/state transitions without full navigation |
| URL API | Structured URL manipulation | Current application state | Parsing, validation, and query parameters |

The implementations deliberately distinguish these mechanisms rather than treating all browser state as interchangeable.

## Conceptual Model

The central relationship is:

    Origin
      |
      +-- localStorage
      |      |
      |      +-- persistent key/value state
      |
      +-- sessionStorage
      |      |
      |      +-- temporary tab/session state
      |
      +-- Cookies
      |      |
      |      +-- request-associated state
      |      +-- Secure / HttpOnly / SameSite policies
      |
      +-- History API
      |      |
      |      +-- pushState
      |      +-- replaceState
      |      +-- back / forward
      |
      +-- URL API
             |
             +-- origin
             +-- pathname
             +-- query parameters
             +-- fragments

These APIs solve different problems. Storage APIs maintain key-value state, cookies participate in HTTP state management, the History API controls entries in the session history, and the URL API provides structured access to URL components.

## `localStorage`

`localStorage` provides string-based key-value storage associated with a browser origin.

The Python implementation uses the `StorageArea` class to model:

- Key validation.
- String-only values.
- Persistent state.
- Explicit quota checking.
- Replacement of an existing value without double-counting its previous size.
- Removal and clearing.
- Missing-key behavior.

The JavaScript implementation uses the actual browser `localStorage` object. Values are written under an application prefix so the example does not intentionally collide with unrelated application keys.

The Java implementation represents the same concept as an enterprise `StorageService`. It separates the storage scope from the storage key and performs explicit quota validation.

The PostgreSQL implementation stores the equivalent state in `browser_storage` with a `storage_scope` enum. A unique constraint prevents two values with the same repository, scope, and key from existing simultaneously.

### Important distinction

`localStorage` is not an encrypted secret store. Sensitive credentials, session secrets, or authentication tokens should not be placed there merely because the API is convenient. JavaScript executing in the origin can normally read the stored values.

## `sessionStorage`

`sessionStorage` has a different lifetime model from `localStorage`.

The examples use it for temporary workflow state such as:

- Checkout step.
- Current workflow state.
- Tab-specific application state.

The Python and Java implementations explicitly distinguish `local` and `session` scopes. The JavaScript implementation calls the browser's `sessionStorage` directly.

The PostgreSQL schema represents the distinction through the `storage_scope` enum rather than maintaining two unrelated tables.

This design makes the lifetime distinction visible in queries and constraints.

## Storage Validation and Quotas

Browser storage quotas are browser-dependent and should not be represented as one universal numeric limit. The source implementations therefore use explicit logical quotas only as validation models.

The Python `StorageArea` rejects writes that exceed its configured quota.

The JavaScript implementation allows the browser to enforce its actual storage policy and catches failures caused by the environment.

The Java implementation performs deterministic logical quota checks for its enterprise model.

The PostgreSQL trigger calculates logical key/value size and rejects writes above its deliberately defined 5 KiB demonstration quota.

This distinction is important: an application-defined logical quota is not the same thing as a browser's implementation-specific storage quota.

## Cookies

Cookies differ substantially from Web Storage.

A cookie can participate in HTTP requests and responses. Its behavior can be controlled through attributes such as:

| Attribute | Purpose |
|---|---|
| `Secure` | Restricts transmission to secure connections |
| `HttpOnly` | Prevents normal JavaScript access through `document.cookie` |
| `SameSite` | Controls cross-site cookie sending behavior |
| `Path` | Limits the URL path for which the cookie applies |
| `Max-Age` | Controls cookie lifetime |

The Python implementation models cookie serialization and validates combinations such as `SameSite=None` with `Secure`.

The JavaScript implementation demonstrates `document.cookie`. It also explicitly recognizes that `HttpOnly` cannot be created from JavaScript. An `HttpOnly` cookie must be configured by the server through an HTTP response.

The Java implementation models cookie policy as an immutable record. This separates policy validation from the service that stores cookie values.

The PostgreSQL trigger enforces important cookie invariants at database level, including the rule that `SameSite=None` must be paired with `Secure`.

### Cookie security distinction

A cookie and a Web Storage item are not equivalent.

A session cookie can be configured with `Secure`, `HttpOnly`, and `SameSite` properties. A `localStorage` value does not provide an equivalent `HttpOnly` mechanism.

## History API

The History API manages entries in the browser's session history.

The primary operations represented in the implementations are:

- `history.pushState()`
- `history.replaceState()`
- `history.back()`
- `history.forward()`
- `history.length`
- `popstate`

`pushState` creates a new history entry.

`replaceState` changes the current entry without creating another entry.

`back` and `forward` move through existing entries.

The JavaScript implementation registers a `popstate` listener so navigation state can be observed when the user moves through history.

The Python `BrowserHistory` and C++ `HistoryManager` use an indexed sequence to model the same behavior. When a new state is pushed after moving backward, entries ahead of the current position are discarded. This mirrors the important branch behavior of session history.

The Java `HistoryService` uses a mutable list with an explicit current index.

## URL API

The URL API provides structured access to URLs instead of requiring applications to manipulate raw strings.

The JavaScript implementation uses:

- `URL`
- `URLSearchParams`
- `location.origin`
- `location.pathname`
- `location.search`
- `location.hash`

The Python implementation uses `urllib.parse` to provide an equivalent structured model.

The Java implementation uses `java.net.URI` and explicit query parsing.

The C++ implementation creates a focused URL model for HTTP and HTTPS URLs.

The database implementation stores canonical URL strings and uses PostgreSQL functions to perform origin comparisons.

A structured URL operation is preferable to ad hoc string concatenation because components such as query parameters and origins have distinct semantics.

## URL Query Parameters

The JavaScript implementation uses `URLSearchParams.set()` to replace a parameter value.

The Python implementation parses query pairs and reconstructs the query string.

The Java implementation uses URL encoding and decoding through `URLEncoder` and `URLDecoder`.

The C++ implementation maintains a map of query parameters for its technical case study.

The PostgreSQL model records URL operations and uses a dedicated `same_origin` function for policy evaluation.

The examples intentionally keep URL parsing separate from navigation policy. Parsing a URL does not automatically mean that navigation to that URL should be permitted by an application.

## Same-Origin Considerations

The browser's same-origin model is fundamental to application security.

The source files demonstrate a simplified application policy that compares:

- Scheme.
- Host.
- Effective port.

The Java implementation has a dedicated `NavigationPolicy` service.

The C++ program uses `BrowserPolicy::isSafeNavigation`.

The PostgreSQL implementation provides `same_origin()` for reporting and policy evaluation.

These application-level models do not replace the browser's actual security enforcement. They demonstrate how an application can make an explicit policy decision before accepting a URL or state transition.

## Python Implementation

The Python file is a self-contained simulation rather than a browser program.

Its main components are:

| Component | Responsibility |
|---|---|
| `StorageArea` | Models local and session storage behavior |
| `Cookie` | Validates and serializes cookie attributes |
| `CookieJar` | Maintains cookie values and request-header representation |
| `BrowserHistory` | Models history entries and navigation |
| `URLModel` | Parses and updates URL components |
| Assertions | Validate normal and failure cases |

The implementation uses only the Python standard library.

It includes explicit failures for:

- Empty storage keys.
- Non-string storage values.
- Storage quota violations.
- Invalid URL schemes.
- Invalid cookie paths.
- Invalid SameSite combinations.
- Negative cookie lifetimes.

## JavaScript Implementation

The JavaScript file is the most browser-native implementation.

It uses the actual browser objects:

- `localStorage`
- `sessionStorage`
- `document.cookie`
- `window.history`
- `window.location`
- `URL`
- `URLSearchParams`

`BrowserStateManager` centralizes application behavior while preserving the native browser APIs.

The implementation also demonstrates asynchronous workflow processing with Promises. A session value is written first, followed by a persistent timestamp.

The event subscription mechanism uses a `Set` of listeners and an unsubscribe function, providing a lightweight event-driven state model without external dependencies.

## C++17 Implementation

The C++ program takes a systems-oriented perspective.

Its domain objects include:

- `StorageArea`
- `Cookie`
- `URL`
- `HistoryManager`
- `BrowserPolicy`

The implementation uses STL containers such as `unordered_map`, `map`, and `vector`.

Exceptions represent invalid operations and quota failures.

The history implementation uses a vector plus an index. This provides direct access to the current entry and predictable navigation behavior.

The C++ URL parser intentionally supports a constrained HTTP(S) model rather than attempting to reproduce the entire browser URL parser. This makes the engineering boundary explicit.

## Java 17 Implementation

The Java implementation represents an enterprise application service model.

Important domain types include:

- `StorageScope`
- `SameSite`
- `NavigationAction`
- `StorageEntry`
- `NavigationState`
- `CookiePolicy`

Records provide immutable value-oriented representations for navigation state and cookie policies.

Service classes separate responsibilities:

- `StorageService`
- `UrlService`
- `CookieService`
- `HistoryService`
- `NavigationPolicy`

This separation makes validation and policy decisions explicit rather than embedding every rule inside one application class.

The navigation policy compares origin components and rejects cross-origin targets.

## PostgreSQL Implementation

The PostgreSQL model represents browser-related state relationally.

The main tables are:

| Table | Purpose |
|---|---|
| `repositories` | Stores application origins |
| `browser_storage` | Stores local/session key-value state |
| `browser_cookies` | Stores cookie metadata and values |
| `navigation_sessions` | Groups browser history for a session |
| `history_entries` | Stores ordered history entries |
| `url_operations` | Records navigation and policy decisions |

The database uses:

- Primary keys.
- Foreign keys.
- Unique constraints.
- Check constraints.
- Enum types.
- Indexes.
- Triggers.
- Functions.
- Views.
- CTE-compatible relational structure.
- Transactions.
- JSONB for navigation state.

The database does not attempt to reproduce the browser's internal implementation. It provides a persistent relational model for application-level state, validation, auditing, and reporting.

## Database Enforcement

The `validate_cookie` trigger rejects invalid cookie configurations.

The `validate_storage_value` trigger applies the demonstration logical quota.

The `same_origin` function provides reusable origin comparison logic.

The `storage_state` view exposes storage records without requiring every consumer to repeat the repository join.

The `cookie_security_report` view identifies potentially weak session-cookie configurations.

The `navigation_report` view aggregates history entries by navigation session.

These mechanisms demonstrate the difference between application logic and database-enforced invariants.

## Transactional Workflow

The PostgreSQL script contains a transaction that changes a stored preference and records the corresponding URL state operation.

The transaction ensures that both operations succeed together or can be rolled back together.

This is useful when browser-related state is represented by persistent server-side application records. The browser itself does not provide PostgreSQL transaction semantics, so the database transaction is an application persistence concern rather than a browser API feature.

## Failure Cases

The implementations intentionally cover failure conditions rather than only successful operations.

| Failure | Handling |
|---|---|
| Empty storage key | Validation exception |
| Storage quota exceeded | Write rejected |
| Invalid URL scheme | URL validation failure |
| Invalid cookie path | Cookie validation failure |
| `SameSite=None` without `Secure` | Cookie rejected |
| Invalid cookie name | Validation failure |
| Cross-origin navigation | Policy rejection |
| Invalid history URL | Navigation validation failure |
| Invalid query parameter name | URL validation failure |

These cases are important because browser state often sits on security and application-state boundaries.

## Security Considerations

### Storage

Do not treat Web Storage as a secure secret vault. JavaScript running with access to the origin can normally read Web Storage values.

Applications should avoid storing highly sensitive authentication material in `localStorage` merely for convenience.

### Cookies

Authentication cookies should be evaluated using appropriate attributes.

`Secure` reduces exposure over insecure transport.

`HttpOnly` prevents ordinary JavaScript access.

`SameSite` can reduce unwanted cross-site cookie transmission.

Cookie configuration should be determined according to the application's authentication and cross-site requirements rather than copied blindly.

### URLs

URL values should be parsed structurally and validated before being used for sensitive operations.

Application-generated navigation should avoid accepting arbitrary schemes or untrusted destinations.

The example policies accept HTTP(S) URLs and demonstrate same-origin checks, but they are intentionally narrower than the browser's full navigation security model.

### History State

History entries can contain application state through the `state` argument to `pushState` and `replaceState`.

Sensitive information should not be placed into URLs or history state merely because it is convenient. URLs can appear in browser history, logs, analytics systems, copied links, and other application surfaces.

## Performance Considerations

Web Storage operations are synchronous browser APIs. Large or frequent operations can affect responsiveness, so applications should keep stored values appropriately small.

URL parsing is generally inexpensive for ordinary application navigation, but repeated parsing in high-frequency workflows should be avoided when the same structured URL can be reused.

History operations are lightweight state transitions, but excessive history entries can make navigation behavior confusing.

The Python and Java quota models calculate logical size by scanning stored entries. That is suitable for demonstration and validation but is not an optimal production implementation for very large storage maps.

The C++ implementation uses hash-based lookup for storage, giving expected constant-time key lookup.

The PostgreSQL indexes target common access paths such as repository/scope storage lookups, repository cookie retrieval, and navigation-session history ordering.

## API Distinctions

The four major state mechanisms should not be collapsed into one abstraction.

| Mechanism | Read by JavaScript | Sent automatically with HTTP requests | Typical lifetime | Primary role |
|---|---:|---:|---|---|
| `localStorage` | Yes | No | Persistent | Client-side application state |
| `sessionStorage` | Yes | No | Session/tab | Temporary client-side state |
| Cookie | Usually, unless `HttpOnly` | Yes, subject to cookie rules | Configurable | HTTP-associated state |
| History state | Yes through history APIs | No | Session history | Navigation state |

The URL API is different from all four. It does not serve as a general storage mechanism. It provides structured manipulation and inspection of URL data.

## Practical Workflow

A realistic single-page application can combine the APIs without confusing their responsibilities:

    User opens application
          |
          v
    URL parsed with URL API
          |
          v
    Application reads localStorage preferences
          |
          v
    sessionStorage restores temporary workflow state
          |
          v
    Server-associated cookie participates in HTTP state
          |
          v
    User changes application view
          |
          v
    URLSearchParams updates query state
          |
          v
    history.pushState() creates navigation entry
          |
          v
    User presses Back
          |
          v
    popstate restores application navigation state

The important design decision is that each API carries the state for which it is intended.

## Limitations

The Python, C++, and Java implementations are models of browser behavior, not replacements for a browser engine.

Their URL parsing is intentionally narrower than a complete standards-compliant browser URL parser.

Their storage quotas are logical demonstration limits rather than universal browser limits.

The PostgreSQL schema represents persistent application records rather than the browser's internal storage implementation.

The JavaScript implementation runs in an actual browser and therefore depends on browser security rules, origin configuration, storage availability, cookie policy, and document context.

These boundaries are deliberate. They keep the implementation technically useful without pretending that a general-purpose programming language can reproduce the complete browser security and storage stack.
