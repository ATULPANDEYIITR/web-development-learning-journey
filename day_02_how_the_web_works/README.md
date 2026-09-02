# How the Web Works

## Introduction

The Web is a large system made from many different technologies working together. A web page that appears simple in a browser can involve domain names, DNS, IP addresses, routers, TCP or QUIC, TLS, HTTP, Web servers, application servers, databases, caches, CDNs, JavaScript, browser rendering engines, authentication systems, and security mechanisms.

This study material explains how these parts connect to each other and what happens when a user opens a website, submits a form, loads an image, calls an API, logs into an account, or interacts with a modern Web application.

The Python program is organized from fundamental networking concepts toward more advanced Web architecture. The examples are designed to show the relationship between the different layers instead of treating each technology as an isolated subject.

---

## 1. The Internet and the Web

The Internet and the Web are not the same thing.

The Internet is the underlying global network infrastructure that connects computers and other devices. The Web is a system of resources and applications that uses this network.

The Web commonly uses HTTP and HTTPS for communication. A browser acts as a client, while Web servers and application servers provide resources and services.

Other Internet services, such as email, file transfer, online gaming, and various communication systems, can operate without being part of the Web.

---

## 2. Clients and Servers

The client-server model is one of the basic ideas behind Web communication.

A client initiates a request. A server receives the request and provides a response or service.

A browser is normally a client when it requests a Web page. A Web server is a server when it receives that request. A mobile application can also act as a client, while an API server can act as the server.

The same physical computer can perform both roles. A development computer can run a browser while also running a local Web server.

---

## 3. IP Addresses

IP addresses identify endpoints at the network layer.

IPv4 uses 32-bit addresses and is commonly written in four decimal sections, such as:

`192.168.1.10`

IPv6 uses 128-bit addresses and is normally represented using hexadecimal notation, such as:

`2001:db8::1`

Private IPv4 address ranges are commonly used inside local networks. Important private ranges include:

- `10.0.0.0/8`
- `172.16.0.0/12`
- `192.168.0.0/16`

Private addresses are not normally routed directly across the public Internet. Network Address Translation allows many devices on a private network to communicate through public IPv4 addresses.

---

## 4. Ports

An IP address identifies a network endpoint, while a port identifies a logical service endpoint.

Ports range from 0 to 65535 for TCP and UDP.

Common examples include:

- Port 22: SSH
- Port 53: DNS
- Port 80: HTTP
- Port 443: HTTPS
- Port 3306: MySQL
- Port 5432: PostgreSQL
- Port 6379: Redis
- Port 8080: commonly used development HTTP port

A server can run several network services on the same IP address because each service can listen on a different port.

---

## 5. Packets

Data transmitted across networks is processed through multiple protocol layers.

A Web request is not simply sent as one large object directly from a browser to a server. Application data is encapsulated by different networking layers and transmitted using packets and frames.

A simplified representation is:

Application data → TCP segment → IP packet → Ethernet/Wi-Fi frame → physical transmission.

At the receiving side, the process is interpreted in the opposite direction.

---

## 6. Routers

Routers connect different networks and forward packets toward their destinations.

A packet leaving a user's device may pass through:

- The local router
- The Internet Service Provider
- Several Internet routers
- Data center networking infrastructure
- The destination network

The exact path is not necessarily fixed. Routing decisions can change because of network configuration, failures, congestion, and other conditions.

---

## 7. MAC Addresses and ARP

MAC addresses operate at the link layer and are associated with network interfaces.

IP addresses and MAC addresses serve different purposes.

IP addresses help identify network-level destinations. MAC addresses are used for delivery within local link-layer networks.

In IPv4 networks, ARP can be used to discover the MAC address associated with an IPv4 address on the local network.

---

## 8. DNS

The Domain Name System translates human-readable domain names into network information.

People normally remember names such as:

`example.com`

Computers ultimately communicate using network addresses.

A typical DNS resolution process can involve:

1. Browser or application cache
2. Operating-system resolver
3. Recursive DNS resolver
4. Root DNS servers
5. Top-level domain servers
6. Authoritative DNS servers

The recursive resolver may cache the result so that future requests can be answered without repeating the entire lookup process.

Important DNS record types include:

- A
- AAAA
- CNAME
- MX
- TXT
- NS
- SOA

DNS therefore acts as an important naming layer for the Web.

---

## 9. Domain Names

Domain names use a hierarchical naming system.

For:

`www.example.com`

the components can be viewed conceptually as:

- `www` as a host or subdomain label
- `example` as the registered domain
- `com` as the top-level domain

DNS delegation allows different authorities to manage different portions of the DNS namespace.

---

## 10. URLs

A URL identifies the location and access method of a Web resource.

For example:

`https://www.example.com:443/products/item?id=42#reviews`

A URL can contain:

- Scheme
- Hostname
- Port
- Path
- Query string
- Fragment

The scheme identifies the protocol family.

The hostname identifies the destination.

The port identifies a service endpoint when explicitly specified.

The path identifies the requested resource or application route.

The query contains parameters.

The fragment identifies a location within the retrieved resource and is normally handled by the browser rather than being transmitted to the server as part of the HTTP request.

---

## 11. HTTP

HTTP stands for Hypertext Transfer Protocol.

It is an application-layer protocol used extensively by the Web.

The fundamental model is:

Client → HTTP request → Server

Server → HTTP response → Client

A request normally contains:

- HTTP method
- Request target
- Headers
- Optional body

A response normally contains:

- Status code
- Reason phrase in older HTTP representations
- Headers
- Optional body

---

## 12. HTTP Methods

HTTP methods communicate the intended operation.

Common methods include:

### GET

Used to retrieve a representation of a resource.

### POST

Used to submit data or request processing that may create or modify state.

### PUT

Used to create or replace a resource representation.

### PATCH

Used to apply a partial modification.

### DELETE

Used to request deletion of a resource.

### HEAD

Requests response headers without the normal response body.

### OPTIONS

Used to discover communication options and is important in some CORS preflight requests.

HTTP methods have defined semantics. Some methods are safe or idempotent under the HTTP model, which is important when designing retries and distributed systems.

---

## 13. HTTP Status Codes

HTTP status codes are divided into five broad classes:

- `1xx`: informational
- `2xx`: successful
- `3xx`: redirection
- `4xx`: client-side request problems
- `5xx`: server-side or upstream problems

Important examples include:

- `200 OK`
- `201 Created`
- `204 No Content`
- `301 Moved Permanently`
- `304 Not Modified`
- `307 Temporary Redirect`
- `308 Permanent Redirect`
- `400 Bad Request`
- `401 Unauthorized`
- `403 Forbidden`
- `404 Not Found`
- `409 Conflict`
- `429 Too Many Requests`
- `500 Internal Server Error`
- `502 Bad Gateway`
- `503 Service Unavailable`
- `504 Gateway Timeout`

Understanding the distinction between these responses is important when designing and debugging Web applications.

---

## 14. HTTP Headers

HTTP headers carry metadata.

Request headers can describe:

- Accepted response formats
- Supported compression
- Authentication information
- Cookies
- Origin
- User-agent information
- Content type

Response headers can describe:

- Content type
- Content length
- Cookies
- Caching instructions
- Redirect destinations
- Compression
- Security policies

Examples include:

- `Content-Type`
- `Content-Length`
- `Cache-Control`
- `ETag`
- `Location`
- `Set-Cookie`
- `Authorization`
- `Cookie`
- `Origin`
- `Accept-Encoding`

Headers are an important part of HTTP behavior rather than merely optional descriptive information.

---

## 15. Cookies

Cookies are small pieces of state associated with Web domains.

A server can send a cookie using:

`Set-Cookie`

The browser can later send matching cookies using:

`Cookie`

Cookies are commonly used for:

- Login sessions
- Preferences
- Application state
- Tracking

Important cookie attributes include:

- `Secure`
- `HttpOnly`
- `SameSite`
- `Domain`
- `Path`
- `Expires`
- `Max-Age`

An `HttpOnly` cookie cannot normally be accessed through JavaScript. A `Secure` cookie is intended to be sent only over secure connections.

---

## 16. Sessions

HTTP itself is fundamentally stateless.

This means that each HTTP request can be processed independently. Web applications often add stateful behavior through sessions.

A typical session system works like this:

1. The user logs in.
2. The server creates authentication state.
3. The server provides a session identifier.
4. The browser stores the identifier.
5. The browser sends it with later requests.
6. The server uses it to identify the associated session.

The actual session data may be stored in server memory, a database, a distributed cache, or another storage system.

---

## 17. Authentication and Authorization

Authentication and authorization are different concepts.

Authentication answers:

**Who are you?**

Authorization answers:

**What are you allowed to do?**

A user can be successfully authenticated and still be forbidden from accessing a particular resource.

A secure application therefore needs both identity verification and permission checking.

---

## 18. Browser Architecture

A modern browser is a complex application.

It contains systems responsible for:

- Networking
- HTML parsing
- CSS processing
- JavaScript execution
- DOM management
- Rendering
- Storage
- Cookies
- Security isolation
- Graphics
- Media
- User interaction

Browsers also use process isolation and sandboxing to limit the consequences of malicious or compromised Web content.

---

## 19. HTML

HTML provides the structural representation of Web documents.

It describes elements such as:

- Headings
- Paragraphs
- Links
- Images
- Forms
- Tables
- Scripts
- Lists
- Sections

The browser parses HTML into a Document Object Model.

---

## 20. CSS

CSS controls presentation and layout.

It can control:

- Fonts
- Colors
- Spacing
- Dimensions
- Positioning
- Responsive behavior
- Animations
- Layout systems

The browser combines HTML structure with CSS rules when determining how the page should appear.

---

## 21. JavaScript

JavaScript provides programming capabilities inside the browser.

It can:

- Modify the DOM
- Respond to user events
- Call APIs
- Manage application state
- Use browser APIs
- Update page content
- Perform asynchronous operations

Modern Web applications use JavaScript extensively for interactive interfaces.

---

## 22. DOM

The Document Object Model represents a document as a tree of objects.

A simplified document may look like:

- Document
  - html
    - head
      - title
    - body
      - h1
      - p

JavaScript can inspect and modify this tree.

DOM modifications may cause the browser to recalculate styles, layout, painting, or compositing depending on what changed.

---

## 23. Browser Events

Browsers expose events for user and system activity.

Examples include:

- `click`
- `keydown`
- `keyup`
- `input`
- `submit`
- `load`
- `DOMContentLoaded`
- `scroll`
- `resize`
- `pointerdown`
- `pointerup`

JavaScript can register event handlers to respond to these events.

---

## 24. APIs

An API defines how software components communicate.

A Web API commonly exposes HTTP endpoints.

For example:

`GET /api/users/42`

may return:

```json
{
  "id": 42,
  "name": "Example User"
}
````

The client does not need to know how the server internally obtains the data. It only needs to understand the API contract.

---

## 25. JSON

JSON is a widely used data interchange format.

It supports:

* Objects
* Arrays
* Strings
* Numbers
* Booleans
* Null

A JSON response can represent structured application data in a form that both browsers and backend systems can process.

JSON originated from JavaScript object notation but is an independent data format and is used by many programming languages.

---

## 26. REST

REST stands for Representational State Transfer.

It is an architectural style rather than a specific protocol.

REST-style APIs commonly use HTTP methods and resource-oriented URLs.

Examples include:

* `GET /users`
* `GET /users/42`
* `POST /users`
* `PATCH /users/42`
* `DELETE /users/42`

Using HTTP does not automatically make an API RESTful. REST concerns architectural constraints and resource representation.

---

## 27. TCP

TCP provides a reliable, ordered byte stream between endpoints.

It includes mechanisms for:

* Connection establishment
* Acknowledgements
* Retransmission
* Flow control
* Congestion control

A traditional TCP connection begins with the three-way handshake:

1. SYN
2. SYN-ACK
3. ACK

HTTP/1.1 and HTTP/2 commonly use TCP as their transport.

---

## 28. UDP

UDP provides a lightweight datagram transport mechanism.

It does not provide TCP's built-in:

* Reliability
* Ordering
* Retransmission
* Connection semantics

Applications can build additional functionality on top of UDP.

QUIC is a major example of a modern transport protocol implemented over UDP.

---

## 29. TLS and HTTPS

HTTPS means HTTP communication protected by TLS.

TLS provides:

* Confidentiality
* Integrity
* Authentication of the server under the certificate trust model

A simplified HTTPS sequence is:

1. Establish transport connectivity.
2. Negotiate TLS.
3. Validate the server certificate.
4. Establish cryptographic session keys.
5. Exchange encrypted HTTP traffic.

HTTPS protects traffic while it is being transported, but it does not automatically make the Web application itself secure.

---

## 30. Cryptography

Three important cryptographic concepts are:

### Symmetric encryption

Uses secret key material for efficient encryption and decryption.

### Asymmetric cryptography

Uses mathematically related public and private keys.

### Hashing

Produces a fixed-size digest from input data.

Hashing is not encryption. A cryptographic hash is designed to be difficult to reverse.

TLS uses a combination of cryptographic techniques rather than relying on one mechanism for every purpose.

---

## 31. HTTP/1.1

HTTP/1.1 introduced important improvements including persistent connections and standardized host-based virtual hosting.

Important concepts include:

* Persistent connections
* Host header
* Cache controls
* Chunked transfer encoding
* Range requests
* Content negotiation

HTTP/1.1 represents HTTP messages primarily as textual protocol structures.

---

## 32. HTTP/2

HTTP/2 introduced a binary framing layer and multiplexing.

Multiple HTTP streams can share a connection.

Important features include:

* Binary framing
* Multiplexed streams
* Header compression
* Stream management

HTTP/2 generally runs over TCP, so TCP-level packet loss can still affect the shared connection.

---

## 33. HTTP/3 and QUIC

HTTP/3 uses QUIC.

QUIC runs over UDP and provides:

* Reliable streams
* Encryption
* Multiplexing
* Modern congestion control
* Connection migration capabilities

QUIC integrates TLS 1.3 mechanisms into its connection establishment.

One important advantage is that independent streams can avoid some forms of cross-stream head-of-line blocking associated with a single TCP byte stream.

---

## 34. Web Caching

Caching stores previously obtained information so that it can be reused.

Caching can exist at several levels:

* Browser
* Service worker
* CDN
* Reverse proxy
* Application
* Database
* Distributed cache

A cache hit means that the requested data is already available in the cache.

A cache miss means that the system must retrieve or generate the data from an upstream source.

---

## 35. Cache-Control

`Cache-Control` controls important aspects of HTTP caching.

Examples include:

* `public`
* `private`
* `max-age`
* `no-cache`
* `no-store`
* `must-revalidate`

`no-cache` does not necessarily mean that the response cannot be stored. It generally means that a stored representation must be validated before reuse.

`no-store` has stronger semantics and instructs caches not to store the response.

---

## 36. ETags

An ETag identifies a particular representation of a resource.

A server might return:

`ETag: "abc123"`

The browser can later send:

`If-None-Match: "abc123"`

If the representation has not changed, the server can respond:

`304 Not Modified`

This allows the browser to reuse its cached copy rather than downloading the complete representation again.

---

## 37. Last-Modified

Servers can also provide:

`Last-Modified`

Clients can later send:

`If-Modified-Since`

This provides another mechanism for conditional requests and cache validation.

---

## 38. CDNs

A Content Delivery Network distributes content through geographically distributed edge locations.

A simplified architecture is:

User → CDN edge → Origin server

If the CDN already has a valid cached copy, it can serve the content directly.

CDNs can reduce:

* Latency
* Origin bandwidth usage
* Origin request volume

They can also provide traffic management and security functions.

---

## 39. Reverse Proxies

A reverse proxy sits between clients and backend servers.

It can perform:

* TLS termination
* Routing
* Caching
* Compression
* Rate limiting
* Access control
* Traffic management

The client sees the reverse proxy rather than necessarily seeing the internal application servers.

---

## 40. Load Balancers

A load balancer distributes traffic among backend instances.

Common strategies include:

* Round robin
* Weighted round robin
* Least connections
* IP hashing
* Random selection

Load balancing can improve capacity, availability, and fault tolerance.

---

## 41. Web Servers

A Web server handles HTTP communication and can serve static resources.

Typical responsibilities include:

* HTTP processing
* Static file serving
* TLS
* Routing
* Logging
* Compression
* Connection handling

Web servers can forward dynamic requests to application servers.

---

## 42. Application Servers

Application servers execute business logic.

A request may pass through:

1. Routing
2. Authentication
3. Authorization
4. Validation
5. Business logic
6. Database access
7. External services
8. Response generation

The application server is where much of the application's actual behavior is implemented.

---

## 43. Databases

Web applications commonly use databases to persist information.

Relational databases use concepts such as:

* Tables
* Rows
* Columns
* Primary keys
* Foreign keys
* Indexes
* Transactions
* Constraints

Non-relational systems include:

* Document databases
* Key-value stores
* Wide-column databases
* Graph databases

The choice depends on the application's data model and operational requirements.

---

## 44. Database-Backed Requests

A request for a resource may trigger a database query.

A simplified flow is:

Browser → Web server → Application → Database → Application → Browser

The application server may transform database data into JSON or HTML before returning it to the browser.

Caching can sometimes eliminate the database query entirely.

---

## 45. JWT

JSON Web Tokens are compact representations containing claims.

A JWT commonly has:

* Header
* Payload
* Signature

A signed JWT allows a receiver to verify that the token was produced by a trusted party and was not modified.

A signed JWT does not automatically encrypt its payload.

---

## 46. CORS

Cross-Origin Resource Sharing controls certain browser-based cross-origin requests.

A browser page from:

`https://app.example.com`

may request:

`https://api.example.com`

The API server can provide CORS headers describing whether the browser should allow the requesting page to access the response.

CORS is primarily a browser enforcement mechanism.

Server-to-server HTTP requests are not restricted by browser CORS rules.

---

## 47. Same-Origin Policy

The same-origin policy is a fundamental browser security mechanism.

An origin consists of:

* Scheme
* Host
* Port

For example:

`https://example.com`

and

`http://example.com`

are different origins because the schemes differ.

Similarly:

`https://example.com`

and

`https://api.example.com`

are different origins because the hosts differ.

---

## 48. WebSockets

WebSockets provide a persistent, bidirectional communication channel.

After the initial HTTP-based upgrade, both the client and server can send messages.

WebSockets are useful for:

* Chat
* Real-time dashboards
* Collaboration
* Multiplayer communication
* Live notifications

They are different from ordinary request-response HTTP communication because the connection remains available for two-way messaging.

---

## 49. Server-Sent Events

Server-Sent Events provide a long-lived server-to-browser event stream.

The server can continuously send updates over an HTTP connection.

They are useful when communication is primarily:

Server → Browser

Unlike WebSockets, they are not designed as a fully bidirectional communication channel.

---

## 50. Webhooks

A webhook allows one system to notify another by making an HTTP request.

For example:

Payment system → POST webhook → Merchant application

Webhook receivers should be designed to deal with:

* Authentication
* Signature verification
* Retries
* Duplicate deliveries
* Timeouts
* Invalid payloads

---

## 51. NAT

Network Address Translation allows private network devices to communicate through public addresses.

A home network may contain:

* `192.168.1.10`
* `192.168.1.11`
* `192.168.1.12`

while the router has a public address.

The router tracks address and port mappings so that responses can be returned to the correct internal device.

---

## 52. DHCP

DHCP automatically provides network configuration to devices.

It can provide:

* IP address
* Network prefix
* Default gateway
* DNS servers
* Lease information

A simplified DHCP exchange is:

1. Discover
2. Offer
3. Request
4. Acknowledgement

---

## 53. Subnets

A subnet divides an address space into a network portion and a host portion.

CIDR notation represents the prefix length.

Examples include:

* `192.168.1.0/24`
* `10.0.0.0/8`
* `172.16.0.0/16`
* `2001:db8::/32`

Subnetting is important for local networking and routing decisions.

---

## 54. Firewalls

Firewalls control traffic based on defined rules.

Rules may consider:

* IP address
* Port
* Protocol
* Connection state
* Application information

For example, a public Web server might expose TCP 443 while a database server remains inaccessible from the public Internet.

---

## 55. Network Models

The OSI model contains seven conceptual layers:

1. Physical
2. Data Link
3. Network
4. Transport
5. Session
6. Presentation
7. Application

The TCP/IP model is commonly represented using fewer layers:

* Link
* Internet
* Transport
* Application

These models help explain how protocols at different levels work together.

---

## 56. Encapsulation

As data moves down the networking stack, each layer can add its own metadata.

A simplified process is:

Application data
↓
TCP segment
↓
IP packet
↓
Link-layer frame
↓
Physical transmission

The receiving system processes these layers in the opposite direction.

---

## 57. What Happens When a URL Is Entered

When a user enters a URL, many operations can occur.

The browser may:

1. Parse the URL.
2. Check relevant caches.
3. Resolve the hostname.
4. Determine network connectivity.
5. Establish transport connectivity.
6. Establish TLS for HTTPS.
7. Send the HTTP request.
8. Receive the response.
9. Parse HTML.
10. Discover additional resources.
11. Load CSS and JavaScript.
12. Construct the DOM and style information.
13. Perform layout.
14. Paint the page.
15. Composite graphical layers.
16. Make the page interactive.

Modern browsers perform many of these operations concurrently.

---

## 58. Form Submission

When a form is submitted:

1. The user enters information.
2. The browser may perform client-side validation.
3. The browser creates an HTTP request.
4. The server receives the request.
5. The server validates the data.
6. Authentication and authorization may be checked.
7. Business logic executes.
8. Data may be stored in a database.
9. A response is returned.

Client-side validation is useful for user experience, but it cannot be treated as a security boundary.

---

## 59. File Downloads

A file can be returned as an HTTP response.

Important headers include:

* `Content-Type`
* `Content-Length`
* `Content-Disposition`

For example, a PDF may be identified using:

`Content-Type: application/pdf`

A browser may display the file or download it depending on response headers and browser behavior.

---

## 60. Image Loading

When HTML contains an image reference, the browser can initiate another HTTP request.

A page may therefore require separate requests for:

* HTML
* CSS
* JavaScript
* Images
* Fonts
* Videos
* API data

The browser can perform many resource requests concurrently.

Caching and connection reuse can reduce the cost of these requests.

---

## 61. Video Streaming

Large media files are commonly delivered in segments.

A streaming system may provide multiple quality levels.

The browser can select a suitable representation based on:

* Network conditions
* Available bandwidth
* Device capability
* Buffer state

This allows video quality to adapt while playback continues.

---

## 62. Authentication Flow

A typical login process is:

1. User submits credentials.
2. Browser sends an HTTPS request.
3. Server validates credentials.
4. Server creates authentication state.
5. Cookie or token is returned.
6. Browser stores the authentication information.
7. Future requests contain authentication state.
8. Server authenticates and authorizes those requests.

Real authentication systems may also use multi-factor authentication, identity providers, token rotation, session expiration, and other controls.

---

## 63. API Request Lifecycle

An API request can pass through several components:

Browser
↓
HTTPS
↓
Load balancer
↓
Reverse proxy
↓
API server
↓
Authentication
↓
Authorization
↓
Validation
↓
Business logic
↓
Cache or database
↓
JSON response
↓
Browser

Large systems can introduce additional services and infrastructure.

---

## 64. Web Security

Web security protects:

* Users
* Accounts
* Data
* Applications
* Infrastructure
* Communication channels

Important security principles include:

* Confidentiality
* Integrity
* Availability
* Authentication
* Authorization
* Least privilege
* Defense in depth
* Input validation
* Secure defaults

HTTPS is important but does not solve every Web security problem.

---

## 65. Cross-Site Scripting

XSS occurs when untrusted data is interpreted as executable content in a user's browser.

Major categories include:

* Stored XSS
* Reflected XSS
* DOM-based XSS

Defenses include:

* Context-aware output encoding
* Safe DOM APIs
* Careful handling of HTML
* Content Security Policy
* Avoiding unsafe interpretation of user-controlled content

---

## 66. SQL Injection

SQL injection occurs when untrusted input changes the intended structure of a database query.

Unsafe query construction can allow input to become part of the SQL command itself.

Parameterized queries separate SQL instructions from user-provided values.

This is one of the main defenses against SQL injection.

---

## 67. CSRF

Cross-Site Request Forgery occurs when a user's browser is induced to perform an unwanted state-changing request while the browser has relevant authentication state.

Common defenses include:

* CSRF tokens
* SameSite cookies
* Origin checking
* Referer checking where appropriate
* Avoiding state-changing operations through GET

---

## 68. Clickjacking

Clickjacking attempts to deceive users into interacting with an interface element they did not intend to use.

Relevant defenses include:

* Content Security Policy `frame-ancestors`
* Appropriate frame restrictions
* `X-Frame-Options` where suitable
* Careful interface design

---

## 69. DDoS

Distributed denial-of-service attacks attempt to make a service unavailable by overwhelming resources.

Attacks may target:

* Network bandwidth
* Network protocols
* Application endpoints

Mitigation can involve:

* Rate limiting
* CDN infrastructure
* Traffic filtering
* Caching
* Autoscaling
* DDoS protection systems
* Capacity planning

---

## 70. TLS Certificates

TLS certificates associate a public key with an identity under a certificate authority trust model.

A simplified certificate chain is:

Root CA
↓
Intermediate CA
↓
Website certificate

Browsers validate certificate properties such as:

* Validity period
* Hostname
* Certificate chain
* Cryptographic signatures
* Applicable policy requirements

---

## 71. Browser Storage

Browsers provide several storage mechanisms.

### Cookies

Integrated directly with HTTP behavior.

### LocalStorage

Provides persistent client-side key-value storage.

### SessionStorage

Provides key-value storage associated with a browser session context.

### IndexedDB

Provides structured client-side database capabilities.

### Cache Storage

Supports cache storage used by service workers and Web applications.

Each mechanism has different lifetime and security characteristics.

---

## 72. Service Workers

Service workers are browser-managed scripts that can participate in network request handling.

They can support:

* Offline functionality
* Request interception
* Caching
* Background operations
* Push-related features

A service worker can allow an application to continue providing functionality even when network connectivity is unavailable or limited.

---

## 73. Web Performance

Web performance depends on many factors.

Important contributors include:

* DNS latency
* Network latency
* TCP or QUIC connection establishment
* TLS negotiation
* Server processing
* Database processing
* Response size
* JavaScript execution
* CSS processing
* Rendering
* Images
* Fonts
* Third-party resources
* Cache effectiveness

A page can be slow even when the total amount of data is relatively small.

Latency, processing time, and resource dependencies are also important.

---

## 74. Compression

Compression reduces the number of bytes transferred.

Common Web content encodings include:

* gzip
* Brotli

Compression is particularly useful for:

* HTML
* CSS
* JavaScript
* JSON

Images and videos often already use specialized compression formats.

---

## 75. MIME Types

The `Content-Type` header identifies the media type of a resource.

Examples include:

* `text/html`
* `text/css`
* `text/javascript`
* `application/json`
* `application/pdf`
* `image/png`
* `image/jpeg`
* `image/webp`
* `video/mp4`

Correct content types are important for browser processing and security.

---

## 76. Content Negotiation

HTTP allows clients to communicate preferences.

Examples include:

`Accept: application/json`

`Accept-Language: en-IN,en;q=0.9`

`Accept-Encoding: br, gzip`

Servers can use these preferences when selecting an appropriate representation.

---

## 77. Range Requests

HTTP range requests allow clients to request part of a resource.

For example:

`Range: bytes=100000-199999`

Range requests are useful for:

* Large downloads
* Resumable downloads
* Media seeking
* Partial retrieval

A server may return `206 Partial Content`.

---

## 78. Latency and Throughput

Latency describes how long an operation takes.

Throughput describes how much work or data can be processed during a period.

A Web request can contain several latency components:

* DNS
* TCP
* TLS
* Server processing
* Network transfer

Throughput can be measured as:

* Requests per second
* Transactions per second
* Bits per second
* Bytes per second

Latency and throughput are different characteristics.

---

## 79. Scalability

Vertical scaling increases the resources of a machine.

Horizontal scaling adds additional instances.

A horizontally scaled Web application might use:

Load Balancer → Server 1
Load Balancer → Server 2
Load Balancer → Server 3

Horizontal scaling often requires careful handling of shared state.

---

## 80. Microservices

Microservices divide an application into independently deployable services.

For example:

* User service
* Order service
* Payment service
* Notification service

This can improve deployment independence but introduces distributed-system concerns such as:

* Network failures
* Service discovery
* Distributed tracing
* Data consistency
* Inter-service communication
* Operational complexity

---

## 81. Message Queues

Message queues allow systems to perform work asynchronously.

A Web request can place a task into a queue rather than waiting for all processing to finish.

The flow becomes:

Application → Queue → Worker → Database or external service

Queues can help with:

* Background processing
* Traffic smoothing
* Retries
* Decoupling
* Asynchronous workflows

---

## 82. Distributed Systems

Modern Web applications often operate as distributed systems.

Distributed systems must account for the fact that:

* Networks can fail.
* Messages can be delayed.
* Messages can be duplicated.
* Services can become unavailable.
* Clocks are not perfectly synchronized.
* Partial failures occur.
* Retries can duplicate operations.
* Replicas can temporarily disagree.

This is why concepts such as timeouts, retries, idempotency, circuit breakers, replication, and distributed tracing matter.

---

## 83. Reliability

Reliable Web systems use several layers of protection.

Common mechanisms include:

* Health checks
* Redundant servers
* Load balancing
* Timeouts
* Retries
* Circuit breakers
* Graceful degradation
* Replication
* Backups
* Monitoring
* Alerting

Retries must be controlled because excessive retries can increase load during an outage.

---

## 84. Observability

Observability helps engineers understand what is happening inside a distributed system.

Three important forms are:

* Logs
* Metrics
* Traces

Distributed tracing can connect operations across several services.

A trace identifier can follow a request through:

API gateway → Service A → Service B → Database

This makes it easier to understand latency and failures across a distributed architecture.

---

## 85. Modern Web Architecture

A large Web application may contain:

User
↓
DNS / CDN / Edge
↓
Load Balancer
↓
Reverse Proxy
↓
API Layer
↓
Services
↓
Cache
↓
Database
↓
Queue
↓
Workers

Static frontend resources can be delivered separately through a CDN.

There is no single mandatory Web architecture. Small websites can use only a few components, while large systems can contain many independent services.

---

## 86. End-to-End Web Request

A complete request can involve all of the following:

1. User enters a URL.
2. Browser parses it.
3. Browser checks caches.
4. DNS resolves the hostname.
5. Packets leave the device.
6. Routers forward traffic.
7. TLS is established.
8. HTTP request is transmitted.
9. Edge infrastructure receives the request.
10. Load balancer selects a backend.
11. Reverse proxy routes the request.
12. Application validates the request.
13. Authentication may be checked.
14. Authorization may be checked.
15. Business logic executes.
16. Cache may be checked.
17. Database may be queried.
18. Response is generated.
19. Response travels back to the browser.
20. Browser parses the response.
21. Additional resources are requested.
22. CSS and JavaScript are processed.
23. Layout is calculated.
24. Content is painted.
25. Layers are composited.
26. The user interacts with the page.

This demonstrates that a Web page is the visible result of many systems working together.

---

## 87. Browser Rendering Pipeline

A simplified rendering process is:

HTML
↓
DOM

CSS
↓
CSSOM

DOM + CSSOM
↓
Rendering information
↓
Layout
↓
Paint
↓
Compositing
↓
Display

JavaScript can modify the DOM and cause additional browser work.

Modern browsers perform many optimizations and may execute parts of this pipeline incrementally.

---

## 88. JavaScript Event Loop

Browser JavaScript uses an event-driven execution model.

Important concepts include:

* Call stack
* Browser APIs
* Tasks
* Microtasks
* Event loop
* Rendering opportunities

Promises use the microtask queue.

Timers and many browser events result in tasks.

The event loop coordinates JavaScript execution with asynchronous operations and browser work.

---

## 89. Asynchronous HTTP

JavaScript can communicate with backend systems without performing a full page navigation.

The Fetch API is a common mechanism.

A typical pattern is:

```text
Browser JavaScript
       |
       v
fetch()
       |
       v
HTTP request
       |
       v
API server
       |
       v
JSON response
       |
       v
JavaScript
       |
       v
DOM update
```

This model is fundamental to interactive Web applications.

---

## 90. Single-Page Applications

A single-page application typically loads an initial application shell and then updates the interface dynamically.

It can contain:

* Client-side routing
* JavaScript bundles
* API communication
* Client-side state
* Dynamic DOM updates

An SPA still relies on servers, networks, HTTP, APIs, databases, and other infrastructure.

---

## 91. Server-Side Rendering

Server-side rendering generates HTML on the server.

The browser receives HTML and can then use JavaScript to add additional interaction.

Modern frameworks can combine server-side rendering with client-side behavior, streaming, static generation, and other techniques.

---

## 92. Static Websites

A static website can consist mainly of pre-generated:

* HTML
* CSS
* JavaScript
* Images
* Fonts
* Other assets

Static resources can often be served efficiently through CDNs because they are highly cacheable.

---

## 93. Serverless Computing

Serverless computing abstracts infrastructure management.

Developers can deploy functions or managed services without directly managing the underlying server fleet.

The underlying servers still exist. The term describes the abstraction of server management rather than the physical absence of servers.

---

## 94. Object Storage

Object storage is commonly used for large files such as:

* Images
* Videos
* Documents
* Backups
* Data files

A common architecture is:

Application → Object Storage → CDN → User

This separates large static objects from the application server.

---

## 95. Idempotency

Idempotency becomes especially important when network operations can be retried.

Consider a payment request where the server processes the payment but the response is lost.

The client may retry.

Without protection, the operation might be processed twice.

An idempotency key allows the server to recognize repeated attempts belonging to the same intended operation.

---

## 96. Rate Limiting

Rate limiting restricts how frequently requests can be performed.

A token bucket is one common conceptual model.

For example:

* Bucket capacity: 10 tokens
* Refill: 2 tokens per second

Each accepted request consumes a token.

Rate limiting helps control:

* Abuse
* Resource consumption
* Traffic spikes
* API usage

---

## 97. Timeouts and Retries

A Web system should not wait forever for a network operation.

Timeouts can exist at different levels:

* Connection timeout
* Read timeout
* Write timeout
* Overall request deadline

Retries can recover from transient failures, but excessive retries can produce retry storms.

Bounded retries and suitable backoff are therefore important.

---

## 98. Static Content Delivery

A typical static content delivery path is:

Developer
↓
Origin server or object storage
↓
CDN
↓
User

The browser may also store the resource in its own cache.

This creates multiple opportunities to serve the resource without contacting the original server.

---

## 99. URL Encoding

URLs have reserved characters and syntax.

Characters that cannot safely appear in a particular URL context may need percent encoding.

For example:

`web development & networking`

can be encoded as:

`web%20development%20%26%20networking`

URL encoding is different from encryption.

---

## 100. Base64

Base64 converts binary data into a text representation.

For example:

`Web data`

can be represented as Base64 text.

Base64 is encoding, not encryption.

Anyone who receives Base64 data can decode it.

---

## 101. DNS Security

DNSSEC adds digital signatures to DNS data.

It provides:

* Data origin authentication
* Data integrity

DNSSEC does not encrypt ordinary DNS queries.

DNS over HTTPS and DNS over TLS address confidentiality between a client and its DNS resolver, which is a different security problem.

---

## 102. Encrypted DNS

DNS over HTTPS carries DNS queries through HTTPS.

DNS over TLS carries DNS queries through TLS.

These technologies can prevent intermediate network observers from simply reading DNS queries in transit.

The DNS resolver itself still processes the queries.

---

## 103. Web Security Headers

Important security headers include:

### Content-Security-Policy

Controls permitted resource and execution sources.

### Strict-Transport-Security

Instructs browsers to use HTTPS for a domain for a defined period.

### X-Content-Type-Options

Helps prevent certain MIME type sniffing behavior.

### Referrer-Policy

Controls referrer information sent with requests.

### Permissions-Policy

Controls access to selected browser capabilities.

---

## 104. API Authorization

An API should determine whether the authenticated caller is permitted to perform an operation.

The process can involve:

1. Identify caller.
2. Determine identity.
3. Check permissions.
4. Check resource ownership.
5. Check roles or policies.
6. Allow or reject the operation.

Authentication alone is not authorization.

---

## 105. API Validation

API input should be validated on the server.

Validation can cover:

* Required fields
* String lengths
* Numeric ranges
* Enumerations
* Object structure
* Identifiers
* File handling
* Business rules

The server should not trust data simply because it came from a browser.

---

## 106. API Versioning

APIs change over time.

Possible approaches include:

* URL versions
* Header-based versions
* Media-type versions

Examples include:

`/api/v1/users`

and:

`/api/v2/users`

Versioning is primarily about managing compatibility between independently changing clients and servers.

---

## 107. HTTP Error Handling

Different errors represent different conditions.

For example:

* `400`: invalid request
* `401`: authentication problem
* `403`: permission problem
* `404`: resource not found
* `409`: state conflict
* `429`: rate limit
* `500`: server failure
* `502`: upstream failure
* `503`: service unavailable
* `504`: upstream timeout

Clear status handling allows clients and infrastructure to respond appropriately.

---

## 108. Sockets

A socket is an operating-system abstraction for network communication.

Applications use socket APIs rather than directly controlling the physical network.

A simplified structure is:

Application
↓
Socket API
↓
Operating system network stack
↓
Network interface
↓
Network

TCP sockets provide a byte-stream interface.

UDP sockets provide datagram-oriented communication.

---

## 109. Web Server Socket Model

A simplified server can:

1. Create a socket.
2. Bind it to an address and port.
3. Listen.
4. Accept connections.
5. Receive requests.
6. Process requests.
7. Send responses.

Production Web servers use much more sophisticated approaches, including asynchronous I/O, worker processes, threads, event loops, and optimized connection management.

---

## 110. Client and Server Ports

A server usually listens on a known port such as 443.

A client normally uses an ephemeral source port selected by the operating system.

A connection can therefore look conceptually like:

`192.168.1.10:52341 → 203.0.113.20:443`

The combination of source and destination addresses and ports helps identify a network flow.

---

## 111. Host Header

One IP address can host multiple websites.

HTTP/1.1 uses the `Host` header to identify the requested hostname.

For example:

```text
GET / HTTP/1.1
Host: shop.example.com
```

This allows Web servers to use virtual hosting.

---

## 112. SNI

Server Name Indication is a TLS extension that allows a client to communicate the intended hostname during TLS negotiation.

This is important when multiple HTTPS websites share the same IP address.

The server can use the requested hostname to select the appropriate certificate.

---

## 113. ALPN

Application-Layer Protocol Negotiation allows endpoints to negotiate an application protocol during TLS setup.

For example, the client may offer:

* `h2`
* `http/1.1`

The server may select:

`h2`

This allows the endpoints to agree on HTTP/2 rather than HTTP/1.1.

---

## 114. HTTP/2 Multiplexing

HTTP/2 can carry multiple streams over one TCP connection.

Conceptually:

```text
One TCP connection
-------------------------
Stream 1: HTML
Stream 2: CSS
Stream 3: JavaScript
Stream 4: Image
-------------------------
```

This reduces the need for multiple independent TCP connections.

---

## 115. QUIC Streams

QUIC supports independent streams within one connection.

Conceptually:

```text
QUIC connection
---------------------
Stream A: HTML
Stream B: Image
Stream C: API data
---------------------
```

Loss affecting one stream does not necessarily block progress on unrelated streams in the same way as a single ordered TCP byte stream.

---

## 116. Connection Migration

QUIC can support connection migration.

This can be useful when a device changes its network path, such as moving between network interfaces, subject to the protocol and implementation conditions.

The logical QUIC connection can continue without necessarily requiring the application to establish an entirely new connection.

---

## 117. Cache Layers

A Web request may interact with several caches.

Possible layers include:

1. Browser memory cache
2. Browser disk cache
3. Service worker cache
4. CDN cache
5. Reverse proxy cache
6. Application cache
7. Database cache

Understanding cache hierarchy is important when debugging stale content and performance problems.

---

## 118. Cache Invalidation

When data changes, previously cached data may become outdated.

Common strategies include:

* Short cache lifetimes
* ETags
* Cache purge mechanisms
* Versioned asset names
* Appropriate cache-control directives

Versioned static assets are especially common.

For example:

`app.8f32a.js`

can represent a specific version of an application bundle.

---

## 119. Network Waterfalls

Browser developer tools commonly show a resource loading waterfall.

It can reveal:

* DNS time
* Connection time
* TLS time
* Server response time
* Transfer time
* Resource dependencies
* Caching behavior

A waterfall provides a useful representation of how different Web resources contribute to page loading.

---

## 120. Third-Party Resources

A Web page can load resources from external domains.

Examples include:

* Analytics
* Payment systems
* Maps
* Fonts
* Video services
* Advertising systems
* External APIs

Third-party resources introduce additional:

* Network requests
* DNS lookups
* Latency
* Privacy considerations
* Security dependencies
* Failure possibilities

---

## 121. Web Accessibility

Accessibility means making Web content usable by people with different abilities.

Important concepts include:

* Semantic HTML
* Keyboard navigation
* Labels
* Alternative text
* Focus management
* Form accessibility
* Sufficient contrast
* Accessible dynamic content

Accessibility is closely connected to the way browsers and assistive technologies interpret Web documents.

---

## 122. Progressive Enhancement

Progressive enhancement starts with a functional foundation and adds more advanced behavior when the environment supports it.

A common conceptual progression is:

HTML
↓
CSS
↓
JavaScript
↓
Advanced browser capabilities

This approach emphasizes functionality and compatibility rather than relying entirely on advanced client-side behavior.

---

## 123. Web Components

Web Components provide browser technologies for building reusable custom elements.

Important technologies include:

* Custom Elements
* Shadow DOM
* HTML templates

Shadow DOM can provide encapsulation for component structure and styles.

---

## 124. Web Privacy

Browsers provide many forms of storage and communication that can affect user privacy.

Relevant concepts include:

* Cookie controls
* Storage partitioning
* Third-party cookie restrictions
* Permission controls
* Referrer policies
* Browser fingerprinting defenses

Privacy behavior can differ between browsers, so Web applications should not assume identical behavior across all user agents.

---

## 125. Cookies Compared with LocalStorage

Cookies and LocalStorage are not interchangeable.

Cookies:

* Can be automatically sent with HTTP requests.
* Have HTTP-specific attributes.
* Can be protected with `HttpOnly`.
* Can be configured with `Secure`.
* Can use `SameSite`.

LocalStorage:

* Is accessed through browser JavaScript.
* Is not automatically included in HTTP requests.
* Provides a simple key-value interface.
* Can persist beyond a single browser session.

The choice depends on the purpose and security requirements of the data.

---

## 126. Edge Computing

Edge computing moves selected computation closer to users.

A request can be processed at a nearby edge location rather than always being sent to a distant origin.

An edge system may:

* Serve a cached response.
* Execute edge logic.
* Forward the request to an origin server.

This can reduce latency for appropriate workloads.

---

## 127. Server-Side Caching

An application can cache frequently requested or expensive data.

A simplified flow is:

Request
↓
Application
↓
Cache hit → Response

or:

Request
↓
Application
↓
Cache miss
↓
Database
↓
Cache
↓
Response

Server-side caching can reduce database load and response latency.

---

## 128. Database Connection Pools

Creating a database connection can be relatively expensive.

A connection pool maintains reusable database connections.

Application requests borrow a connection from the pool, execute operations, and return the connection.

This allows multiple application requests to share a controlled collection of database connections.

---

## 129. Database Indexes

Indexes can make certain database queries substantially faster.

Without a useful index, the database may need to inspect many rows.

With an appropriate index, it can locate relevant data more efficiently.

Indexes also have costs:

* Storage
* Additional write work
* Maintenance

Database design therefore directly affects Web application performance.

---

## 130. Database Transactions

Transactions group operations into a unit governed by database consistency rules.

ACID is commonly used to describe:

* Atomicity
* Consistency
* Isolation
* Durability

Transaction behavior depends on the database engine and isolation level.

Web applications need to choose transaction boundaries according to their consistency requirements.

---

## 131. Distributed Caches

A distributed cache allows multiple application instances to share cached state.

For example:

Application 1
Application 2 → Distributed Cache
Application 3

This is useful when horizontally scaled application instances need common cached information.

---

## 132. Distributed Session Management

When multiple application servers process requests, authentication state must be available to whichever server receives the request.

A shared session store can provide this.

This allows:

Load Balancer → Application 1
Load Balancer → Application 2
Load Balancer → Application 3

with all instances accessing a shared session system.

---

## 133. Sticky Sessions

Sticky sessions attempt to route a user's requests to the same backend server.

This can simplify some stateful applications but can also produce:

* Uneven traffic
* Reduced flexibility
* More complicated failover behavior

Shared state is often used when the application needs to scale across many instances without depending on one specific server.

---

## 134. Service Discovery

Distributed services need to locate one another.

Service discovery provides information about available service instances.

A service can ask:

"Where is the User Service?"

The discovery system returns one or more available endpoints.

---

## 135. API Gateways

An API gateway provides a common entry point to backend services.

It can handle:

* Routing
* Authentication
* Authorization
* Rate limiting
* Request transformation
* Traffic management

It can route requests to different backend services based on paths, methods, identities, or other information.

---

## 136. Database Replication

Database replication maintains copies of data on multiple database instances.

Replication can improve:

* Availability
* Read scalability
* Disaster recovery

Replication can also introduce replication lag.

A recently written record might not immediately be visible from a replica.

---

## 137. Consistency

Distributed systems can use different consistency models.

Examples include:

* Strong consistency
* Eventual consistency
* Read-after-write consistency
* Session consistency

The appropriate model depends on application requirements.

Not every application needs every reader to observe the newest value immediately.

---

## 138. CAP Concept

CAP theorem concerns distributed systems under network partition conditions.

The three concepts are:

* Consistency
* Availability
* Partition tolerance

When a network partition occurs, a distributed system cannot simultaneously provide the strongest traditional guarantees for all three properties.

This is one reason distributed data systems involve architectural trade-offs.

---

## 139. WebSocket Security

WebSocket applications require the same broad security principles as other networked systems.

Important controls include:

* Secure transport
* Authentication
* Authorization
* Input validation
* Rate limiting
* Resource limits
* Correct connection lifecycle handling

A persistent connection does not automatically make an application secure.

---

## 140. HTTP Streaming

HTTP can stream response data progressively.

Streaming can be useful for:

* Large files
* Generated responses
* Event streams
* Model-generated output
* Long-running operations

Streaming avoids requiring the entire response to be generated or buffered before the client receives useful data.

---

## 141. Time to First Byte

Time to First Byte measures the time between initiating a request and receiving the first response byte.

It can include:

* DNS
* Connection setup
* TLS
* Request transmission
* Server processing
* Network delays

A high TTFB can indicate a slow backend, distant infrastructure, network delays, or overloaded services.

---

## 142. Client-Side and Server-Side Rendering

Client-side rendering places more rendering work in the browser.

Server-side rendering generates HTML on the server.

Modern Web frameworks can combine:

* Server-side rendering
* Client-side rendering
* Static generation
* Streaming
* Hydration
* Partial rendering

The distinction is about where and when the HTML and interface work is performed.

---

## 143. Web Application State

State can exist in many places:

* Browser memory
* DOM
* Cookies
* LocalStorage
* SessionStorage
* IndexedDB
* Server sessions
* Databases
* Distributed caches
* Message queues

Understanding where state lives is important for security, scalability, reliability, and application behavior.

---

## 144. Frontend and Backend

The frontend is primarily the user-facing software running in the browser.

The backend contains server-side systems that perform operations such as:

* Authentication
* Authorization
* Business logic
* Data processing
* Database access
* External service communication

The frontend and backend communicate using protocols such as HTTPS and WebSockets.

---

## 145. Browser Sandboxing

Browsers isolate Web content from sensitive system resources.

Important security mechanisms include:

* Process isolation
* Origin isolation
* Permissions
* Restricted filesystem access
* Controlled device APIs

Sandboxing limits the ability of Web content to directly interact with the operating system.

---

## 146. Origins

An origin is based on:

* Scheme
* Host
* Port

Examples:

`https://example.com/a`

and

`https://example.com/b`

have the same origin.

But:

`https://example.com`

and

`http://example.com`

do not.

Neither do:

`https://example.com`

and

`https://api.example.com`

Understanding origins is essential for browser security and CORS.

---

## 147. HTTP Request Bodies

Common request body formats include:

* `application/json`
* `application/x-www-form-urlencoded`
* `multipart/form-data`
* `text/plain`
* `application/octet-stream`

The `Content-Type` header tells the server how the request body should be interpreted.

---

## 148. File Uploads

`multipart/form-data` allows forms to contain both fields and files.

A server receiving an uploaded file must not blindly trust:

* Filename
* Client-provided MIME type
* File extension
* Other client-supplied metadata

Uploaded content should be validated and handled according to the application's security requirements.

---

## 149. HTTP Request Smuggling

HTTP request smuggling can occur when different components in a Web request chain interpret message boundaries differently.

For example:

Client → Proxy → Backend

If the proxy and backend disagree about request framing, security problems can occur.

Consistent protocol parsing and correctly configured infrastructure are important defenses.

---

## 150. Recursive DNS Resolution

A recursive DNS resolver performs DNS lookup work for clients.

It may:

1. Receive a query.
2. Check its cache.
3. Query root infrastructure if necessary.
4. Query the relevant TLD infrastructure.
5. Query the authoritative server.
6. Cache the answer.
7. Return the answer to the client.

---

## 151. Authoritative DNS

An authoritative DNS server provides authoritative information for the zones it manages.

The recursive resolver asks questions.

The authoritative server provides the official records for its zone.

The recursive resolver can then cache those records according to their TTL.

---

## 152. DNS Delegation

DNS delegation allows responsibility for part of the namespace to be assigned to another set of name servers.

Conceptually:

Root
↓
`.com`
↓
`example.com`
↓
Authoritative DNS servers

This distributed hierarchy allows DNS to operate at global scale.

---

## 153. IPv4 and IPv6

IPv4 uses 32-bit addresses.

IPv6 uses 128-bit addresses.

The theoretical address-space sizes are:

* IPv4: `2^32`
* IPv6: `2^128`

IPv6 provides a vastly larger address space.

The transition from IPv4 to IPv6 involves technologies such as:

* Dual stack
* Translation
* Tunneling
* Other transition mechanisms

---

## 154. Network Calculation

For a network such as:

`192.168.10.0/24`

the network has a prefix length of 24 bits.

The Python program demonstrates how the network address, broadcast address, prefix length, and total address count can be inspected programmatically.

Subnet understanding is important for routing and local network design.

---

## 155. HTTP Redirects

Redirects tell clients to access a different location.

Examples include:

* `301`
* `302`
* `307`
* `308`

The distinction between these codes matters because redirect semantics can affect how clients handle the original HTTP method.

---

## 156. Authorization Header

The HTTP `Authorization` header can carry credentials or tokens.

A common example is:

```text
Authorization: Bearer <access-token>
```

Bearer tokens must be protected because possession of a valid token may be sufficient to authorize access.

---

## 157. OAuth

OAuth is an authorization framework.

It allows an application to obtain controlled access to resources without requiring the user to give the application their primary credentials.

A simplified model involves:

* User
* Authorization server
* Client application
* Resource server

OAuth should be understood as an authorization framework rather than simply as a login mechanism.

---

## 158. OpenID Connect

OpenID Connect provides an identity layer on top of OAuth 2.0.

It allows applications to obtain information about an authenticated user from an identity provider.

Important concepts include:

* Identity provider
* Client
* Authorization endpoint
* Token endpoint
* ID token
* User information

---

## 159. SameSite Cookies and CSRF

SameSite cookie behavior can reduce the conditions under which cookies are sent in cross-site situations.

The main SameSite values are:

* Strict
* Lax
* None

`SameSite=None` generally requires the `Secure` attribute.

Cookie policy should match the application's authentication and navigation requirements.

---

## 160. The Web Security Model

Web security is layered.

A simplified model is:

User input
↓
Browser security
↓
HTTPS
↓
Server authentication
↓
Authorization
↓
Input validation
↓
Business logic
↓
Secure data access

No single mechanism provides complete Web security.

---

## 161. Full Browser Page-Load Model

A browser page load can be understood as:

URL
↓
URL parsing
↓
Cache checks
↓
DNS
↓
Network routing
↓
TCP/QUIC
↓
TLS
↓
HTTP
↓
Server infrastructure
↓
Response
↓
HTML parsing
↓
CSS
↓
JavaScript
↓
Images and fonts
↓
DOM and CSSOM
↓
Layout
↓
Paint
↓
Compositing
↓
Interactive page

The browser performs many of these operations concurrently and can reuse existing connections and cached information.

---

## 162. Why HTTPS Matters

HTTPS provides protection for HTTP traffic while it is being transported.

It provides:

* Confidentiality
* Integrity
* Server authentication

It helps protect against network-level observation and modification.

HTTPS does not prove that the application itself is trustworthy or free from vulnerabilities.

A malicious or vulnerable application can still operate over HTTPS.

---

## 163. Why DNS Matters

DNS separates human-friendly names from network addresses.

This allows infrastructure to change while the public domain name remains stable.

A domain can point toward:

* A server
* A load balancer
* A CDN
* Multiple addresses
* Different infrastructure over time

DNS is therefore a critical abstraction layer for the Web.

---

## 164. Why Ports Matter

One machine can run many network services.

For example:

```text
Server IP
|
+-- TCP 22   -> SSH
+-- TCP 80   -> HTTP
+-- TCP 443  -> HTTPS
+-- TCP 5432 -> PostgreSQL
```

Ports allow the operating system to deliver network traffic to the appropriate service.

---

## 165. Why Protocols Matter

Protocols are shared rules for communication.

Important protocols in the Web ecosystem include:

* IP
* TCP
* UDP
* QUIC
* TLS
* HTTP
* DNS
* Ethernet
* Wi-Fi

Each protocol addresses a different part of communication.

Together they form a layered system.

---

## 166. The Complete Web Stack

A simplified complete stack can be represented as:

```text
User
 |
Browser
 |
HTML / CSS / JavaScript
 |
HTTP / HTTP/2 / HTTP/3
 |
TLS
 |
TCP / QUIC / UDP
 |
IP
 |
Ethernet / Wi-Fi / Cellular
 |
Internet
 |
DNS / Routing / CDN / Edge
 |
Server Infrastructure
 |
Load Balancer
 |
Reverse Proxy
 |
Application Server
 |
Cache / Queue / Services
 |
Database / Object Storage
```

The important point is that the Web is not a single technology.

It is a layered system.

A browser opening a page can involve application code, network protocols, cryptography, DNS infrastructure, routing, servers, storage, databases, caches, and rendering systems.

Understanding how these layers interact explains what actually happens between the moment a user enters a URL and the moment a Web page becomes visible and interactive.

```
```

