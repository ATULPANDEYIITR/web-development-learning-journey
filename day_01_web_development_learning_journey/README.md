# Introduction to Web Development

## 1. What Is Web Development?

Web development is the process of creating, testing, deploying, maintaining, and improving websites and web applications.

It involves much more than writing HTML. Modern web development can involve:

* Frontend development
* Backend development
* Databases
* APIs
* Networking
* HTTP/HTTPS
* DNS
* Authentication
* Security
* Hosting
* Cloud infrastructure
* Caching
* CDNs
* Load balancing
* Monitoring
* Performance optimization

A simplified web architecture is:

```text
User
  ↓
Browser
  ↓
DNS
  ↓
Internet
  ↓
CDN / Reverse Proxy
  ↓
Web Server
  ↓
Backend Application
  ↓
Database
```

---

## 2. Internet vs Web

The **Internet** is the global network connecting computers and networks.

The **Web** is a service that operates over the Internet.

The Internet supports many services:

* Web
* Email
* File transfer
* Video communication
* Gaming
* DNS
* Messaging

Therefore:

```text
Internet = network/infrastructure

Web = service operating on that network
```

---

## 3. Website vs Web Application

A website primarily presents information.

Examples:

* Portfolio
* Blog
* Company website
* Documentation
* News website

A web application provides interactive functionality.

Examples:

* Gmail
* Google Docs
* Online banking
* E-commerce platforms
* Project management systems
* Learning platforms

The distinction is not absolute.

Modern web systems often combine website and web application characteristics.

---

# 4. Frontend Development

Frontend development concerns the part of a web application that users directly see and interact with.

The three foundational technologies are:

```text
HTML
CSS
JavaScript
```

### HTML

HTML defines structure and semantic content.

Example:

```html
<h1>Hello World</h1>
```

### CSS

CSS controls presentation and layout.

Example:

```css
h1 {
    font-size: 40px;
}
```

### JavaScript

JavaScript provides programming logic and interactivity.

Example:

```javascript
button.addEventListener("click", function () {
    alert("Hello");
});
```

Frontend responsibilities include:

* Layout
* Typography
* Colors
* Forms
* Navigation
* Animations
* Responsive design
* Accessibility
* Browser interactions
* API communication
* Client-side validation

Popular frontend technologies include:

* React
* Angular
* Vue
* Svelte
* Next.js

HTML, CSS, and JavaScript remain the fundamental concepts beneath these tools.

---

# 5. Backend Development

Backend development deals with server-side functionality.

A backend may:

* Authenticate users
* Validate data
* Apply business rules
* Query databases
* Process payments
* Send emails
* Manage files
* Expose APIs
* Generate responses

Common backend languages include:

* Python
* JavaScript/Node.js
* Java
* C#
* Go
* PHP
* Ruby
* Rust

Common frameworks include:

* Django
* Flask
* FastAPI
* Express
* Spring Boot
* ASP.NET
* Laravel

A simplified backend architecture is:

```text
Browser
   ↓
API
   ↓
Backend
   ↓
Database
```

The backend can also communicate with:

* Caches
* Payment providers
* Email services
* File storage
* External APIs
* Authentication providers

---

# 6. Full-Stack Development

Full-stack development covers multiple layers of a web system.

A typical full-stack system includes:

```text
Frontend
   ↓
Backend
   ↓
Database
   ↓
Infrastructure
```

A full-stack developer does not necessarily need to master every technology available.

The important skill is understanding how the layers interact.

---

# 7. Static Websites

A static website generally serves files that already exist.

Example:

```text
index.html
about.html
styles.css
script.js
image.jpg
```

The flow is:

```text
Browser
   ↓
GET /about.html
   ↓
Server
   ↓
about.html
   ↓
Browser
```

Static websites can be extremely fast and scalable.

---

# 8. Dynamic Websites

Dynamic websites generate or retrieve content based on requests.

Example:

```text
Browser
   ↓
GET /profile
   ↓
Backend
   ↓
Database
   ↓
User data
   ↓
Backend
   ↓
Response
   ↓
Browser
```

Dynamic systems are useful when content depends on:

* User identity
* Database information
* Search queries
* Permissions
* Transactions
* Real-time information

---

# 9. URLs

A URL identifies a resource.

Example:

```text
https://www.example.com:443/products?id=42#reviews
```

Components:

```text
https       → scheme
example.com → hostname
443         → port
/products   → path
id=42       → query
reviews     → fragment
```

---

# 10. Domains

A domain provides a human-readable name for an Internet resource.

Instead of remembering an IP address, users can remember:

```text
example.com
```

DNS connects domain names with network addresses.

Conceptually:

```text
example.com
     ↓
    DNS
     ↓
IP address
     ↓
Server
```

---

# 11. DNS

DNS stands for **Domain Name System**.

Its primary role is to translate names such as:

```text
example.com
```

into network addresses.

The simplified process is:

```text
Browser
   ↓
DNS lookup
   ↓
IP address
   ↓
Server
```

DNS is one of the foundational services of the Internet.

---

# 12. IP Addresses

An IP address identifies a network interface or host within an IP network.

IPv4 example:

```text
192.168.1.10
```

IPv6 example:

```text
2001:db8::1
```

Important categories include:

### Public IP

Routable on the public Internet.

### Private IP

Used within private networks.

Common private IPv4 ranges include:

```text
10.x.x.x
172.16.x.x - 172.31.x.x
192.168.x.x
```

### Loopback

```text
127.0.0.1
```

This refers to the local computer.

---

# 13. Ports

A computer can run multiple network services.

Ports help identify those services.

Common ports:

| Service | Port |
| ------- | ---: |
| HTTP    |   80 |
| HTTPS   |  443 |
| SSH     |   22 |

Development servers often use:

```text
3000
5000
8000
8080
```

For example:

```text
http://localhost:8000
```

Here:

```text
localhost = local machine
8000      = port
```

An IP address identifies the host.

A port identifies a service endpoint on that host.

---

# 14. Client-Server Model

The client-server model is fundamental to web development.

The client commonly refers to the browser.

Examples:

* Chrome
* Firefox
* Safari
* Edge

The server receives requests and provides responses.

The fundamental pattern is:

```text
Client
  ↓
Request
  ↓
Server
  ↓
Response
  ↓
Client
```

---

# 15. Request-Response Cycle

When a user enters:

```text
https://example.com
```

many things can happen.

Simplified sequence:

1. Browser parses the URL.
2. Browser determines the protocol.
3. DNS resolves the domain.
4. Network connection is established.
5. TLS negotiation occurs for HTTPS.
6. Browser sends an HTTP request.
7. Server receives the request.
8. Server processes the request.
9. Server sends an HTTP response.
10. Browser receives the response.
11. Browser parses HTML.
12. Browser discovers CSS, JavaScript, images, fonts, and other resources.
13. Browser requests those resources.
14. Browser renders the page.

---

# 16. HTTP

HTTP means:

**Hypertext Transfer Protocol**

HTTP defines communication between clients and servers.

Important HTTP methods include:

| Method | Typical purpose             |
| ------ | --------------------------- |
| GET    | Retrieve data               |
| POST   | Create/submit data          |
| PUT    | Replace a resource          |
| PATCH  | Partially update a resource |
| DELETE | Delete a resource           |

Example:

```http
GET /products
```

could mean:

> Return the products.

Example:

```http
POST /users
```

could mean:

> Create a new user.

---

# 17. HTTP Status Codes

HTTP responses contain status codes.

Important examples:

| Code | Meaning               |
| ---: | --------------------- |
|  200 | OK                    |
|  201 | Created               |
|  204 | No Content            |
|  301 | Moved Permanently     |
|  302 | Redirect              |
|  304 | Not Modified          |
|  400 | Bad Request           |
|  401 | Unauthorized          |
|  403 | Forbidden             |
|  404 | Not Found             |
|  409 | Conflict              |
|  429 | Too Many Requests     |
|  500 | Internal Server Error |
|  502 | Bad Gateway           |
|  503 | Service Unavailable   |

Status code classes:

```text
1xx → Informational
2xx → Successful
3xx → Redirection
4xx → Client/request errors
5xx → Server errors
```

---

# 18. Browser

A browser is much more than a page viewer.

A modern browser performs:

* Network communication
* HTTP communication
* TLS communication
* HTML parsing
* CSS parsing
* JavaScript execution
* DOM construction
* Rendering
* Image decoding
* Font handling
* Storage
* Cookie management
* Security enforcement
* Cache management

A simplified rendering pipeline is:

```text
HTML
 ↓
DOM

CSS
 ↓
CSSOM

DOM + CSSOM
 ↓
Render Tree
 ↓
Layout
 ↓
Paint
 ↓
Compositing
 ↓
Screen
```

---

# 19. Chrome Developer Tools

Chrome DevTools is one of the most important tools for web developers.

Open it with:

```text
F12
```

or:

```text
Ctrl + Shift + I
```

Important panels include:

### Elements

Inspect HTML and CSS.

### Console

Run JavaScript and inspect errors.

### Network

Inspect requests and responses.

### Sources

Inspect source code and debugging information.

### Application

Inspect cookies, storage, cache, and related browser data.

### Performance

Analyze performance.

### Security

Inspect security information.

The Network panel is particularly important because it allows you to inspect:

* Request URL
* HTTP method
* Status code
* Request headers
* Response headers
* Request payload
* Response body
* Timing

---

# 20. Web Server

A server can mean:

1. A physical/virtual computer providing services.
2. Software that listens for and processes network requests.

Examples of web servers/reverse proxies include:

* Nginx
* Apache
* Caddy

Application servers/framework runtimes include:

* Node.js
* Uvicorn
* Gunicorn
* Java application servers
* ASP.NET

Modern systems may use several of these together.

---

# 21. API

API means:

**Application Programming Interface**

A web API provides a structured method for software components to communicate.

Example:

```text
GET /api/products
```

A response might contain JSON:

```json
{
    "products": [
        {
            "id": 1,
            "name": "Laptop",
            "price": 50000
        }
    ]
}
```

Common API approaches include:

* REST
* GraphQL
* RPC
* WebSockets

---

# 22. JSON

JSON stands for:

**JavaScript Object Notation**

Example:

```json
{
    "name": "Alex",
    "role": "developer",
    "skills": [
        "HTML",
        "CSS",
        "Python"
    ]
}
```

JSON is widely used for communication between frontend and backend systems.

---

# 23. Databases

Web applications frequently require persistent data.

Examples:

* Users
* Products
* Orders
* Payments
* Posts
* Comments
* Messages

Popular relational databases include:

* PostgreSQL
* MySQL
* SQLite
* Microsoft SQL Server

Popular non-relational systems include:

* MongoDB
* Redis
* DynamoDB

A common architecture is:

```text
Browser
   ↓
Backend
   ↓
Database
```

The browser generally should not directly connect to the production database.

The backend provides controlled access.

---

# 24. Authentication

Authentication answers:

> Who are you?

Example:

```text
Username + Password
```

Authorization answers:

> What are you allowed to do?

Example:

```text
Normal User
    ↓
View profile

Administrator
    ↓
View profile
    ↓
Delete users
    ↓
Manage system
```

Authentication and authorization are different concepts.

---

# 25. Cookies

Cookies are small pieces of data associated with a website/domain.

They can be used for:

* Sessions
* Preferences
* Authentication state
* Analytics
* Personalization

Important security-related cookie attributes include:

* `Secure`
* `HttpOnly`
* `SameSite`

---

# 26. Sessions

Sessions allow a server to associate multiple requests with a particular user.

Simplified:

```text
Login
 ↓
Server creates session
 ↓
Browser receives session identifier
 ↓
Browser sends identifier with later requests
 ↓
Server identifies user
```

Modern systems can use:

* Session cookies
* JWTs
* OAuth tokens

Each approach has different architectural and security implications.

---

# 27. HTTPS

HTTPS means HTTP protected using TLS.

HTTPS provides important security properties including:

* Encryption
* Integrity protection
* Server authentication

Production websites should normally use HTTPS.

---

# 28. Hosting

Hosting means running a website or application on infrastructure that can serve users.

Hosting can involve:

* Physical servers
* Virtual machines
* Containers
* Serverless platforms
* Cloud platforms
* Static hosting services

A simplified model:

```text
Domain
 ↓
DNS
 ↓
Hosting infrastructure
 ↓
Application
```

---

# 29. Localhost

During development, applications commonly run locally.

Example:

```text
http://localhost:8000
```

This means:

```text
Protocol → HTTP
Host     → local computer
Port     → 8000
```

A local development server is not automatically publicly accessible.

---

# 30. VS Code

VS Code is a source-code editor.

Important capabilities include:

* Syntax highlighting
* Code completion
* Debugging
* Extensions
* Git integration
* Integrated terminal
* Search
* Formatting
* Refactoring

A project may look like:

```text
my-web-project/
│
├── index.html
├── style.css
├── script.js
├── images/
├── backend/
└── README.md
```

VS Code and Chrome have different purposes.

```text
VS Code → write/debug code

Chrome → run/inspect web applications
```

---

# 31. DOM

DOM means:

**Document Object Model**

Given:

```html
<body>
    <h1>Hello</h1>
    <button>Click</button>
</body>
```

the browser constructs an internal tree.

Conceptually:

```text
Document
 └── body
      ├── h1
      │    └── "Hello"
      │
      └── button
           └── "Click"
```

JavaScript can modify the DOM.

It can:

* Change text
* Add elements
* Remove elements
* Change classes
* Respond to events

---

# 32. Client-Side Rendering

Client-side rendering allows the browser to execute JavaScript and construct much of the UI.

Simplified:

```text
Server
 ↓
HTML + JavaScript
 ↓
Browser
 ↓
JavaScript executes
 ↓
UI
```

Benefits can include rich interactivity.

Tradeoffs can include:

* Larger JavaScript payloads
* Increased browser processing
* Performance considerations
* SEO complexity in some architectures

---

# 33. Server-Side Rendering

Server-side rendering generates HTML on the server.

```text
Browser
 ↓
Request
 ↓
Server
 ↓
HTML generated
 ↓
Browser
 ↓
Render
```

Modern frameworks may combine:

* Server-side rendering
* Client-side rendering
* Static generation
* Streaming
* Partial rendering

---

# 34. Caching

Caching means storing reusable data for faster retrieval.

Caching can occur at:

* Browser
* CDN
* Reverse proxy
* Application
* Database/cache layer

Simplified:

```text
Request
 ↓
Cache
 ├── HIT → Response
 │
 └── MISS → Backend → Database
```

Caching can reduce:

* Latency
* Database load
* Server load

A major challenge is determining when cached data becomes stale.

---

# 35. CDN

CDN means:

**Content Delivery Network**

A CDN distributes content through geographically distributed edge locations.

Without a CDN:

```text
User
 ↓
Origin Server
```

With a CDN:

```text
User
 ↓
Nearby CDN Edge
 ↓
Cached Content
```

CDNs are useful for:

* Images
* CSS
* JavaScript
* Videos
* Static files
* Cached pages

---

# 36. Reverse Proxy

A reverse proxy sits between clients and backend servers.

```text
Client
   ↓
Reverse Proxy
   ↓
Backend
```

A reverse proxy may handle:

* TLS termination
* Routing
* Load balancing
* Compression
* Caching
* Rate limiting
* Security filtering

---

# 37. Load Balancing

When one server cannot handle all traffic, requests can be distributed.

```text
             ┌── Server 1
             │
Client → Load Balancer
             │
             ├── Server 2
             │
             └── Server 3
```

Benefits include:

* Scalability
* Availability
* Fault tolerance

---

# 38. Scalability

Scalability means handling increasing workload.

## Vertical Scaling

Increase the power of one machine.

```text
4 CPU
 ↓
16 CPU
```

## Horizontal Scaling

Add more machines.

```text
1 server
 ↓
10 servers
```

Horizontal scaling commonly involves:

* Load balancers
* Shared state
* Caching
* Database scaling
* Monitoring
* Fault tolerance

---

# 39. Complete Production Request Flow

A sophisticated request can follow a path such as:

```text
User
 ↓
Chrome
 ↓
DNS
 ↓
Internet
 ↓
CDN
 ↓
Load Balancer
 ↓
Reverse Proxy
 ↓
Application Server
 ├── Cache
 ├── Database
 └── External APIs
 ↓
HTTP Response
 ↓
Chrome
 ↓
HTML + CSS + JavaScript
 ↓
DOM + CSSOM
 ↓
Rendering
 ↓
User
```

This is a much more accurate mental model of modern web development than:

```text
Browser → Website
```

---

# 40. Security Fundamentals

Important web security concepts include:

* HTTPS
* Authentication
* Authorization
* Input validation
* Output encoding
* Password hashing
* Secure cookies
* CSRF protection
* XSS prevention
* SQL injection prevention
* Rate limiting
* Access control
* Security headers
* Secrets management

Three important vulnerabilities are:

### XSS

Cross-Site Scripting.

Untrusted content may cause malicious JavaScript to execute in another user's browser.

### SQL Injection

Untrusted input changes the meaning of a database query.

### CSRF

Cross-Site Request Forgery attempts to cause a user's browser to perform an unwanted authenticated action.

---

# 41. Stateless Systems

Stateless architecture attempts to avoid relying on server-local memory for previous requests.

For example:

```text
Request 1 → Server A
Request 2 → Server B
Request 3 → Server C
```

This becomes easier when shared state is stored in:

* Database
* Cache
* Session store
* Appropriate client-side tokens

Stateless systems can simplify horizontal scaling.

---

# 42. WebSockets

Traditional HTTP communication often looks like:

```text
Client → Request
Server → Response
```

WebSockets allow persistent two-way communication:

```text
Client
  ⇅
Server
```

They are useful for:

* Chat
* Live notifications
* Multiplayer games
* Real-time dashboards
* Collaborative applications

---

# 43. SEO

SEO means:

**Search Engine Optimization**

Web development affects SEO through:

* Semantic HTML
* Titles
* Metadata
* Content structure
* Performance
* Mobile usability
* Accessibility
* Crawlability
* Internal linking
* Structured data

---

# 44. Accessibility

Accessible web development aims to make websites usable by people with different abilities.

Important concepts include:

* Semantic HTML
* Keyboard navigation
* Screen readers
* Color contrast
* Labels
* Alternative text
* Focus management
* Accessible forms

Prefer semantic elements such as:

```html
<button>Submit</button>
```

rather than creating something that merely looks like a button.

---

# 45. Responsive Design

Websites are accessed from:

* Desktop
* Laptop
* Tablet
* Smartphone
* Large displays

Responsive design allows layouts to adapt.

Important technologies include:

* CSS Grid
* Flexbox
* Media queries
* Relative units
* Responsive images
* Mobile-first design

Responsive design is not merely shrinking a desktop layout.

The interface may need to fundamentally change according to screen size.

---

# 46. Development vs Production

### Development

Used while building software.

Typical characteristics:

* Debugging
* Local servers
* Test data
* Developer tools
* Frequent code changes

### Production

Used by real users.

Typical requirements:

* Security
* Reliability
* Monitoring
* Logging
* Backups
* Scalability
* Performance
* Error handling
* Deployment automation

Code that works locally is not automatically production-ready.

---

# 47. Deployment

Deployment means making software available in its target environment.

A simplified pipeline:

```text
Developer
 ↓
Git
 ↓
CI/CD
 ↓
Build
 ↓
Tests
 ↓
Deployment
 ↓
Production
```

Modern web development frequently uses:

* Git
* GitHub/GitLab/Bitbucket
* CI/CD
* Docker
* Cloud platforms
* Monitoring

---

# 48. Web Application Layers

A web application can be divided into multiple conceptual layers:

```text
Presentation Layer
 ↓
Frontend
 ↓
API
 ↓
Business Logic
 ↓
Data Access
 ↓
Database
 ↓
Infrastructure
 ↓
Networking
 ↓
Security
 ↓
Observability
```

Each layer has a different responsibility.

---

# 49. Monolithic Architecture

A monolithic application packages much of the application into one deployable unit.

```text
Browser
 ↓
Application
 ↓
Database
```

Monoliths can be:

* Simple to develop
* Simple to deploy
* Easy to debug initially
* Capable of scaling

A monolith is not automatically bad architecture.

---

# 50. Microservices

A microservice architecture may separate functionality into services such as:

```text
User Service
Product Service
Order Service
Payment Service
Notification Service
```

Advantages may include:

* Independent deployment
* Team autonomy
* Independent scaling

Costs include:

* Network complexity
* Distributed failures
* Data consistency challenges
* Operational overhead
* Observability complexity

Microservices should be adopted because they solve a real architectural problem, not simply because they are popular.

---

# 51. Observability

Production systems need to answer questions such as:

* Is the application working?
* Why is it slow?
* Which requests are failing?
* Which service is causing the problem?

Three important observability components are:

### Logs

Detailed application events.

### Metrics

Numerical measurements such as:

* CPU usage
* Request rate
* Error rate
* Latency

### Traces

Track a request through multiple services.

Example:

```text
Browser
 ↓
API Gateway
 ↓
Service A
 ↓
Service B
 ↓
Database
```

---

# 52. Web Performance

Important performance concepts include:

* Page load time
* Time to first byte
* Largest Contentful Paint
* Cumulative Layout Shift
* Interaction responsiveness
* JavaScript execution
* Network latency
* Image size
* Cache efficiency

Optimization techniques include:

* Compression
* Lazy loading
* Caching
* CDN
* Code splitting
* Image optimization
* Reducing unnecessary JavaScript
* Efficient database queries

Performance is a full-stack concern.

---

# 53. Common Beginner Mistakes

Avoid these mistakes:

1. Learning frameworks before understanding HTML, CSS, and JavaScript.
2. Treating frontend and backend as unrelated worlds.
3. Thinking a domain is the same as hosting.
4. Thinking localhost means public hosting.
5. Confusing domains and IP addresses.
6. Ignoring HTTP fundamentals.
7. Ignoring browser DevTools.
8. Trusting frontend validation for security.
9. Exposing secrets in frontend code.
10. Connecting browsers directly to production databases.
11. Ignoring accessibility.
12. Ignoring performance.
13. Confusing authentication and authorization.
14. Assuming every application needs microservices.

---

# 54. Core Mental Model

The most important model to remember is:

```text
USER
 ↓
BROWSER
 ↓
URL
 ↓
DNS
 ↓
IP ADDRESS
 ↓
INTERNET
 ↓
CDN / REVERSE PROXY
 ↓
WEB SERVER
 ↓
BACKEND
 ↓
CACHE / DATABASE / APIs
 ↓
HTTP RESPONSE
 ↓
BROWSER
 ↓
HTML + CSS + JavaScript
 ↓
DOM + CSSOM
 ↓
RENDERING
 ↓
USER
```

This mental model provides the foundation for learning advanced web development.

---
