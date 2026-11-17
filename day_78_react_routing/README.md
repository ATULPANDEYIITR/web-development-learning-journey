# React Routing: SPA Navigation, Nested Routes, Parameters, and Protected Routes

## 1. Project Overview

React Routing is the process of connecting application URLs to the components displayed in a React application.

A traditional multi-page website requests a new document from the server when the user navigates between pages. A Single Page Application (SPA) loads the main application document and changes the displayed interface through client-side navigation.

Routing provides the structure required to manage these URL changes.

This project implements five independent engineering perspectives:

| File | Implementation | Primary purpose |
|---|---|---|
| Python | Routing simulator | Route matching, validation, navigation, and access evaluation |
| JavaScript | Event-driven router | Asynchronous navigation and event notifications |
| C++17 | Routing engine | Structured route resolution and authorization |
| Java 17 | Enterprise routing model | Immutable domain objects and access policies |
| PostgreSQL | Relational routing system | Persistent route definitions, permissions, and navigation records |

The implementations are independent programs. They model related routing concepts but do not require one another to execute.

## 2. Single Page Application Routing

### 2.1 What is a Single Page Application?

A Single Page Application loads an initial HTML document and uses JavaScript to update the displayed content without requiring a complete document reload for every navigation action.

For example:

- `/` displays the home page.
- `/about` displays the about page.
- `/products` displays the product listing.
- `/dashboard` displays the authenticated dashboard.

The browser URL changes while the application remains loaded.

### 2.2 Client-side navigation

Client-side navigation generally involves:

1. The user selects a navigation link.
2. The application receives the navigation event.
3. The router examines the requested URL.
4. The router identifies the matching route.
5. The application renders the corresponding component.
6. The browser history is updated.

A React application can implement this behavior using React Router.

The browser History API provides the underlying navigation mechanisms:

- `pushState()` adds a history entry.
- `replaceState()` replaces the current history entry.
- `popstate` detects browser back and forward navigation.

React Router provides application-level routing abstractions around these browser capabilities.

### 2.3 SPA routing versus traditional navigation

| Property | Traditional navigation | SPA navigation |
|---|---|---|
| Main document | Usually requested again | Usually retained |
| Page transition | Server-driven | Client-driven |
| URL | Changes | Changes |
| Component state | Often reset | Can be retained |
| Routing responsibility | Commonly server | Client router |
| Initial loading | Server response | Application bundle |

Client-side navigation does not eliminate server responsibilities. The web server must still serve the SPA entry document when a user directly opens a supported application URL.

For example, opening `/products/501` directly must return the application entry document rather than an unrelated server-side 404.

## 3. Route Definitions

A route connects a URL pattern with an application component.

A route definition generally contains:

| Property | Purpose |
|---|---|
| `path` | URL pattern |
| `element` or component | Interface displayed |
| `children` | Nested route definitions |
| `loader` | Data-loading operation |
| `action` | Data-changing operation |
| `errorElement` | Route-level error interface |

A basic React Router configuration can use:

- `BrowserRouter`
- `Routes`
- `Route`
- `Link`
- `NavLink`
- `Navigate`
- `Outlet`
- `useNavigate`
- `useParams`
- `useLocation`

These APIs serve different purposes.

### 3.1 BrowserRouter

`BrowserRouter` enables browser-based client-side routing using the History API.

It allows an application to use normal URL paths instead of requiring hash-based URLs.

### 3.2 Routes and Route

`Routes` selects the appropriate route for the current location.

`Route` defines the URL pattern and the corresponding component.

### 3.3 Link and NavLink

`Link` provides navigation without requiring a full document reload.

`NavLink` provides navigation with information about whether the link represents the active route.

This is useful for navigation menus and sidebars.

### 3.4 Navigate

`Navigate` performs declarative redirection.

Typical uses include:

- Redirecting unauthenticated users to login.
- Redirecting users after successful login.
- Redirecting obsolete paths.
- Redirecting users away from unavailable pages.

### 3.5 useNavigate

`useNavigate` provides programmatic navigation.

Typical uses include:

- Navigating after submitting a form.
- Returning to a previous location.
- Redirecting after a successful operation.
- Navigating after completing a user action.

## 4. Nested Routes

Nested routing represents a hierarchy of application interfaces.

A parent route provides a shared layout, while child routes provide the content displayed inside that layout.

Consider an application with the following structure:

ApplicationLayout
|
|-- Home
|
|-- About
|
|-- ProductsLayout
|   |
|   |-- ProductList
|   |
|   |-- ProductDetails
|
|-- UsersLayout
|   |
|   |-- UserProfile
|
|-- Dashboard
|
|-- AdminPanel

The parent layout can contain:

- Navigation bar
- Sidebar
- Header
- Footer
- Shared application state
- Common page structure

The child route changes according to the selected URL.

### 4.1 Outlet

`Outlet` identifies where the matched child route should appear inside its parent layout.

For example, a products layout can display a common product navigation interface while the selected child displays either a product list or individual product details.

The important distinction is that the parent layout and child content are separate components.

### 4.2 Benefits of nested routing

- Shared layouts are implemented once.
- Navigation structures remain consistent.
- Child pages are easier to organize.
- Route-level loading and error handling can be separated.
- Complex application structures become easier to maintain.

### 4.3 Route hierarchy versus URL hierarchy

A nested route configuration does not always need to use a URL with additional path segments.

A parent layout can provide a shared component structure even when the URL structure is not a direct reflection of the component hierarchy.

The component hierarchy and URL hierarchy are related design decisions, not necessarily identical structures.

## 5. Route Parameters

Route parameters allow a URL to contain values that identify particular application resources.

Examples:

| URL | Parameter | Value |
|---|---|---|
| `/products/501` | `productId` | `501` |
| `/users/101` | `userId` | `101` |
| `/orders/9001` | `orderId` | `9001` |
| `/departments/finance` | `department` | `finance` |

A dynamic route can use the following pattern:

`/products/:productId`

The colon identifies a dynamic parameter.

### 5.1 useParams

`useParams` retrieves the dynamic parameters associated with the matched route.

For `/products/501`, the application receives:

- Parameter name: `productId`
- Parameter value: `501`

The application can use this value to request the corresponding product.

### 5.2 Route parameters versus query parameters

These mechanisms serve different purposes.

| Property | Route parameter | Query parameter |
|---|---|---|
| Location | URL path | URL query string |
| Example | `/products/501` | `/products?category=books` |
| Typical purpose | Identify a resource | Filter or configure a view |
| Retrieval | `useParams` | `useSearchParams` |

Query parameters are useful for:

- Search terms
- Sorting
- Filtering
- Pagination
- Selected tabs
- Optional display settings

Multiple query parameters can exist in one URL.

For example:

`/products?category=books&page=2&sort=price`

### 5.3 Parameter validation

Route parameters should not automatically be trusted.

A product identifier should be checked before it is used in a database query or API request.

Validation should consider:

- Expected data type
- Permitted length
- Valid character set
- Resource existence
- User authorization
- Malformed URL encoding

A valid-looking identifier does not establish that the current user can access the requested resource.

## 6. Protected Routes

Protected routes restrict access to application pages.

Examples include:

- User dashboards
- Administrative interfaces
- Account management
- Personal records
- Internal business applications

A protected route generally requires authentication or a specific authorization policy.

### 6.1 Authentication

Authentication determines whether the user has established an identity.

Examples include:

- Username and password authentication
- Single sign-on
- Multi-factor authentication
- External identity providers

An unauthenticated visitor may be redirected to a login page.

### 6.2 Authorization

Authorization determines whether an authenticated user is permitted to perform a particular operation or access a particular resource.

For example:

| Role | Home | Dashboard | Administration |
|---|---|---|---|
| Guest | Yes | No | No |
| User | Yes | Yes | No |
| Admin | Yes | Yes | Yes |

Authentication and authorization are separate decisions.

A user can be authenticated but still lack permission to access the administration page.

### 6.3 Protected route behavior

A typical protected navigation process is:

1. The user requests a protected URL.
2. The application checks authentication state.
3. If authentication is missing, navigation redirects to login.
4. If authentication exists, the authorization policy is evaluated.
5. If the policy permits access, the requested component is displayed.
6. Otherwise, an access-denied interface is displayed.

### 6.4 Preserving the requested destination

When a visitor is redirected to login, the original requested URL can be preserved.

For example:

`/dashboard` → `/login`

After successful login:

`/login` → `/dashboard`

The application should validate the return destination to prevent open-redirect vulnerabilities.

Only permitted internal destinations should be accepted.

## 7. Authentication Is Not a Complete Security Boundary

Client-side protected routes improve navigation and user experience. They do not replace server-side authorization.

A user can manually change a URL, modify browser state, or call an API without using the application's interface.

Therefore:

- API endpoints must enforce authentication.
- Server operations must enforce authorization.
- Sensitive records must be checked against the requesting user's permissions.
- Client-side role information must not be treated as authoritative.
- Session expiration must be handled.
- Access tokens and session credentials must be protected.

A hidden administration link does not make an administrative API secure.

The backend must independently verify the user's permissions for every sensitive operation.

## 8. Route Matching and Resolution

Route matching determines whether a requested URL corresponds to a registered route.

The implementations use several matching strategies:

| Implementation | Matching mechanism |
|---|---|
| Python | Compiled regular expressions |
| JavaScript | Regular expressions and parameter extraction |
| C++17 | Segment-based matching |
| Java 17 | Segment-based matching |
| PostgreSQL | Stored route patterns and segment comparisons |

For example:

Pattern: `/products/:productId`

Requested URL: `/products/501`

Result:

`productId = 501`

### 8.1 Static and dynamic segments

A static segment must match its configured value.

A dynamic segment captures a URL value.

For example:

- `/products` is a static path.
- `/products/:productId` contains a dynamic segment.
- `/users/:userId` contains a different dynamic segment.

### 8.2 Not-found handling

When no route matches the requested URL, the application should display a not-found interface.

This is different from an authorization failure.

| Condition | Appropriate response |
|---|---|
| No matching route | Not found |
| No valid authentication | Login redirect |
| Insufficient permission | Forbidden |
| Valid route and permission | Render component |

The distinction improves error handling and prevents authorization failures from being confused with missing resources.

## 9. Navigation History

Browser navigation history stores previously visited locations.

The main operations are:

- Push: Add a new location.
- Replace: Change the current location.
- Back: Navigate to the previous entry.
- Forward: Navigate to the next entry.

Example:

`/` → `/products` → `/products/501`

Using Back returns to `/products`.

Using Forward returns to `/products/501`.

The Python, JavaScript, C++17, and Java 17 implementations include independent navigation-history models.

In actual browser applications, the browser History API and router coordinate these operations.

The router must also handle browser-generated back and forward events rather than assuming every navigation originates from an application button.

## 10. React Router Implementation Architecture

A typical React application can organize routing into the following structure:

Application
|
|-- Router Configuration
|   |
|   |-- Public Routes
|   |-- Nested Routes
|   |-- Dynamic Routes
|   |-- Protected Routes
|
|-- Layout Components
|   |
|   |-- Main Layout
|   |-- Dashboard Layout
|   |-- Administration Layout
|
|-- Authentication Services
|
|-- Authorization Policies
|
|-- Page Components
|
|-- Error Boundaries
|
|-- API Services

A practical application separates route definitions from business logic.

This prevents page components from becoming responsible for every navigation and security decision.

## 11. Python Implementation

The Python program provides a standalone routing simulator.

### Main components

| Component | Responsibility |
|---|---|
| `Route` | Represents a route definition |
| `User` | Represents an authenticated user |
| `UserRole` | Defines access roles |
| `Router` | Resolves registered routes |
| `RouteMatch` | Stores matching information |
| `NavigationResult` | Stores navigation outcomes |
| `NavigationHistory` | Maintains navigation history |
| `RouteGuard` | Evaluates access permissions |

### Implemented mechanisms

- Static route matching
- Dynamic route parameters
- Query-string parsing
- Nested component chains
- Protected routes
- Role-based access
- Redirect behavior
- Not-found handling
- Navigation history
- Unit tests

The implementation uses dataclasses to represent structured domain objects.

Regular expressions provide URL pattern matching.

Dictionaries store extracted parameters, while sets represent permitted roles.

The test suite verifies successful navigation, denied access, missing routes, and navigation-history behavior.

The simulator uses simplified route definitions to demonstrate the mechanics. It is not a replacement for React Router or a production HTTP server.

## 12. JavaScript Implementation

The JavaScript program provides an event-driven navigation model.

### Main components

| Component | Responsibility |
|---|---|
| `RouteDefinition` | Defines route metadata |
| `RouteMatcher` | Identifies matching routes |
| `AuthorizationService` | Evaluates access policies |
| `ApplicationRouter` | Coordinates navigation |
| `EventEmitter` | Publishes navigation events |

### Event-driven behavior

The implementation uses Node.js `EventEmitter`.

It emits events when:

- Navigation completes.
- Authentication state changes.

Consumers can subscribe to these events without directly modifying the router.

### Asynchronous navigation

The `navigate()` method uses asynchronous execution.

This makes the architecture suitable for extending route transitions with operations such as:

- Fetching user information
- Loading application configuration
- Retrieving remote permissions
- Performing route-level validation

The implementation also includes:

- Permission caching
- Navigation history
- Redirect handling
- Authentication checks
- Role restrictions
- Error handling

The permission cache is deliberately invalidated when the user changes.

In production, permission caching must also account for session changes, permission updates, and token expiration.

The demonstration uses Node.js rather than a browser. It models the routing logic without rendering React components.

## 13. C++17 Implementation

The C++ program provides a structured routing and access-evaluation engine.

### Main domain structures

| Structure | Responsibility |
|---|---|
| `User` | Represents the current user |
| `Route` | Stores route definitions |
| `RouteMatch` | Stores matching parameters |
| `NavigationResult` | Represents navigation outcomes |
| `Router` | Resolves route patterns |
| `NavigationHistory` | Tracks navigation entries |

### Design decisions

The implementation uses:

- `vector` for ordered route definitions.
- `map` for extracted route parameters.
- `set` for permitted roles.
- `optional` for values that may not exist.
- `enum class` for controlled states.
- Exceptions for invalid configuration.

The segment-based matching approach avoids requiring an external routing library.

The route hierarchy is traversed recursively.

The implementation also validates route definitions before navigation.

### Performance considerations

Let:

- R represent the number of registered routes.
- S represent the average number of path segments.

The basic route-resolution approach has approximately O(R × S) matching cost for a flat collection of routes.

Recursive nested-route traversal adds the cost of visiting the applicable route hierarchy.

For larger systems, a prefix tree or indexed route structure can reduce the number of candidates examined.

## 14. Java 17 Implementation

The Java implementation provides an enterprise-oriented routing model.

### Main domain types

| Type | Responsibility |
|---|---|
| `User` | Immutable user representation |
| `Route` | Route definition and access policy |
| `RouteMatch` | Route-resolution result |
| `NavigationResult` | Navigation outcome |
| `RouteRegistry` | Route registration and lookup |
| `AuthorizationService` | Permission evaluation |
| `NavigationService` | Navigation and history management |

### Immutable domain modeling

Java records represent structured information that should not be modified after creation.

The route definitions use immutable child collections and permission sets.

This reduces accidental modifications to application configuration.

### Access policy separation

The implementation distinguishes three route policies:

| Policy | Meaning |
|---|---|
| `PUBLIC` | Available without authentication |
| `AUTHENTICATED` | Requires an authenticated user |
| `ROLE_RESTRICTED` | Requires an authenticated user with an allowed role |

This provides a reusable policy structure rather than embedding separate authorization rules into every navigation operation.

### Enterprise implications

A larger Java application can extend the model with:

- Identity-provider integration
- Central permission services
- Audit events
- Session validation
- Route configuration versioning
- Role hierarchies
- Resource-level authorization

The demonstration focuses on client-side route-resolution concepts rather than implementing a complete identity-management system.

## 15. PostgreSQL Implementation

The SQL implementation provides persistent storage for routing definitions and navigation activity.

### Relational data model

applications
    |
    |-- routes
    |     |
    |     |-- route_role_permissions
    |
    |-- navigation_requests
          |
          |-- navigation_parameters
          |
          |-- navigation_query_parameters

app_users
    |
    |-- navigation_requests

### Table responsibilities

| Table | Purpose |
|---|---|
| `applications` | Stores SPA application definitions |
| `app_users` | Stores application user information |
| `routes` | Stores route definitions |
| `route_role_permissions` | Stores permitted roles |
| `navigation_requests` | Records navigation attempts |
| `navigation_parameters` | Stores dynamic route values |
| `navigation_query_parameters` | Stores query-string values |

### Database integrity

The database uses:

- Primary keys
- Foreign keys
- Unique constraints
- Check constraints
- Indexes
- Triggers
- Stored functions
- Stored procedures
- Views
- Recursive CTEs

These mechanisms protect the consistency of persistent routing information.

### Nested route relationships

The `parent_route_id` column represents parent-child relationships.

A route can reference another route within the same application.

The trigger checks that parent and child routes belong to the same application and rejects circular ancestry.

### Permission enforcement

The `route_role_permissions` table separates role assignments from route definitions.

The `evaluate_route_access()` function evaluates whether a user can access a particular route.

The result distinguishes:

- Successful access
- Authentication redirect
- Permission denial
- Missing route

### Navigation processing

The `process_navigation` procedure:

1. Receives an application identifier.
2. Receives an optional user identifier.
3. Receives a requested path.
4. Resolves the registered route.
5. Evaluates the route's access policy.
6. Determines the navigation status.
7. Records the navigation request.

The database stores navigation history for reporting and analysis.

### Reporting

The SQL script includes queries for:

- Route retrieval
- Nested route hierarchy
- User access evaluation
- Navigation statistics
- Failed requests
- Route usage frequency
- Parameter storage
- Permission validation
- Recent navigation activity

### Database limitations

The SQL model represents route definitions and navigation decisions as persistent records.

It does not render React components or replace the browser's client-side router.

Its route matching function is a simplified implementation. It does not implement every matching, ranking, optional-segment, basename, and wildcard behavior available in React Router.

The example database stores simplified user authentication information. Production applications should integrate with an established identity system rather than treating a database boolean as sufficient proof of authentication.

## 16. Important Distinctions

Several routing concepts are closely related but should not be treated as interchangeable.

| Concept | Main responsibility |
|---|---|
| SPA routing | Controls client-side URL navigation |
| Route definition | Connects a URL pattern to an application component |
| Nested routing | Organizes components into parent-child layouts |
| Route parameters | Identifies dynamic values in URL paths |
| Query parameters | Supplies optional URL configuration values |
| Authentication | Establishes the user's identity |
| Authorization | Determines permitted operations and resources |
| Protected routes | Applies access checks before displaying restricted interfaces |
| Navigation history | Maintains previous and future locations |
| Route matching | Determines which route corresponds to a URL |

A route parameter does not establish permission.

A protected route does not replace backend security.

A nested route does not necessarily require a completely separate page.

A successful route match does not guarantee that the requested resource exists.

These distinctions are important when designing secure and maintainable applications.

## 17. Error Handling and Edge Cases

A reliable routing implementation must account for conditions beyond successful navigation.

| Condition | Expected behavior |
|---|---|
| Unknown URL | Display not-found interface |
| Missing authentication | Redirect to login |
| Insufficient role | Display forbidden interface |
| Invalid route definition | Reject route configuration |
| Duplicate sibling routes | Reject ambiguous configuration |
| Missing parameter | Reject the route match |
| Invalid URL encoding | Handle decoding failure |
| Expired session | Revalidate authentication |
| Invalid return destination | Reject unsafe redirect |
| Browser back operation | Restore previous location |
| Browser forward operation | Restore next location |
| Direct URL access | Return SPA entry document from server |
| Inactive account | Reject protected access |

Production implementations should also consider:

- Route-level loading states
- API failures
- Error boundaries
- Concurrent navigation
- Cancellation of outdated requests
- Permission changes during an active session
- Deep-link refresh behavior
- URL normalization
- Sensitive information in query strings

## 18. Performance and Security Considerations

### Performance

- Avoid unnecessary route definitions.
- Use lazy loading for large page components.
- Separate application layouts from individual page components.
- Avoid repeatedly evaluating expensive authorization operations.
- Use route indexing when the route collection becomes large.
- Cancel obsolete data requests when navigation changes.
- Avoid excessive component remounting.

### Security

- Enforce authorization on backend endpoints.
- Validate all route parameters.
- Validate redirect destinations.
- Avoid storing sensitive information in URLs.
- Protect authentication credentials.
- Handle session expiration.
- Apply resource-level access checks.
- Do not trust client-side role information.
- Record important authentication and authorization failures.

### Lazy loading

Lazy loading allows page components to be downloaded when needed instead of loading every application component immediately.

This can reduce initial application loading time.

React supports this behavior through `React.lazy()` and `Suspense`.

### Error boundaries

Error boundaries help prevent failures in one part of the component tree from breaking the entire application interface.

They are useful for handling rendering failures in complex nested layouts.

## 19. Execution Requirements

| File | Runtime | Execution |
|---|---|---|
| Python | Python 3.10+ | `python routing.py` |
| JavaScript | Node.js 18+ | `node routing.js` |
| C++17 | C++17 compiler | Compile and execute the program |
| Java | Java 17 | `javac Main.java` followed by `java Main` |
| PostgreSQL | PostgreSQL 15+ | Execute the SQL script using `psql` |

The Python, JavaScript, C++17, and Java implementations use standard language capabilities without third-party dependencies.

The PostgreSQL script creates its own schema, domain tables, constraints, sample records, stored routines, triggers, and reporting views.

## 20. Practical Application Scenarios

The implemented routing concepts apply to several application types.

| Application | Routing requirements |
|---|---|
| E-commerce | Product listings, product IDs, filters, shopping pages |
| Banking portal | Account pages, authenticated dashboards, administrative access |
| Learning platform | Courses, lessons, learner profiles |
| Enterprise dashboard | Nested modules, role restrictions, reporting pages |
| Healthcare portal | Patient-facing pages, restricted records, authorized access |
| Project management | Projects, tasks, team pages, user-specific dashboards |

The same routing architecture can support different application domains by changing route definitions, components, and access policies.

The central design principle is to keep URL resolution, component organization, authentication, authorization, and backend security as separate responsibilities.
