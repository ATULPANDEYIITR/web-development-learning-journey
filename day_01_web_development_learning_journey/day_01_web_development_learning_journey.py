"""
===============================================================================
INTRODUCTION TO WEB DEVELOPMENT
===============================================================================

This Python script is an educational, interactive guide to understanding
Web Development from absolute beginner concepts to advanced fundamentals.

TOPICS COVERED
---------------
1. What is Web Development?
2. Internet vs Web
3. Websites vs Web Applications
4. Frontend Development
5. Backend Development
6. Full-Stack Development
7. Static vs Dynamic Websites
8. Client-Server Architecture
9. Request-Response Cycle
10. HTTP and HTTPS
11. Browsers
12. Servers
13. Domains
14. DNS
15. Hosting
16. URLs
17. IP Addresses
18. Ports
19. HTML, CSS and JavaScript
20. APIs
21. Databases
22. Cookies and Sessions
23. Authentication
24. Web Application Architecture
25. CDN and Caching
26. Reverse Proxies
27. Load Balancing
28. Scalability
29. Development Environments
30. VS Code and Chrome
31. Practical Simulations
32. Advanced Web Development Concepts
33. Final Knowledge Check

IMPORTANT
---------
This script does NOT require external libraries.
It uses Python to simulate web concepts rather than actually creating
a production web server.

Run:
    python introduction_to_web_development.py

===============================================================================
"""

# =============================================================================
# SECTION 0 - HELPER FUNCTIONS
# =============================================================================

import time
import random
from urllib.parse import urlparse


def title(text):
    print("\n" + "=" * 80)
    print(text.upper())
    print("=" * 80)


def subtitle(text):
    print("\n" + "-" * 70)
    print(text)
    print("-" * 70)


def explain(text):
    print("\n" + text)


def pause():
    input("\nPress Enter to continue...")


def slow_print(text, delay=0.01):
    for character in text:
        print(character, end="", flush=True)
        time.sleep(delay)
    print()


# =============================================================================
# SECTION 1 - WHAT IS WEB DEVELOPMENT?
# =============================================================================

title("1. What is Web Development?")

explain("""
Web development is the process of creating, building, testing, deploying,
maintaining, and improving websites and web applications.

A web developer works with technologies that allow users to interact with
software through a web browser.

Examples include:

    - Google Search
    - YouTube
    - Amazon
    - Gmail
    - Facebook
    - Banking portals
    - Online learning platforms
    - E-commerce applications
    - SaaS products
    - Government portals

Web development is much larger than simply writing HTML.

A modern web system may involve:

    User
      |
      v
    Browser
      |
      v
    DNS
      |
      v
    Internet
      |
      v
    CDN / Reverse Proxy
      |
      v
    Web Server
      |
      v
    Backend Application
      |
      v
    Database
      |
      v
    External APIs / Services

Web development therefore combines programming, networking, security,
databases, user interfaces, infrastructure, and software architecture.
""")

pause()


# =============================================================================
# SECTION 2 - INTERNET VS WEB
# =============================================================================

title("2. Internet vs World Wide Web")

explain("""
The Internet and the Web are NOT the same thing.

THE INTERNET
------------

The Internet is a global network of interconnected computers and networks.

It supports many services:

    - Web
    - Email
    - File transfer
    - Video calls
    - Online gaming
    - DNS
    - Messaging
    - Remote access

THE WEB
-------

The World Wide Web is a service that operates over the Internet.

Websites and web applications generally use:

    - HTTP
    - HTTPS
    - HTML
    - URLs
    - Browsers
    - Web servers

Think about it like this:

    Internet = infrastructure/network

    Web = one major service running on that infrastructure

A browser accesses the Web through the Internet.
""")

pause()


# =============================================================================
# SECTION 3 - WEBSITE VS WEB APPLICATION
# =============================================================================

title("3. Website vs Web Application")

explain("""
A WEBSITE primarily presents information to users.

Examples:

    - Company website
    - Portfolio
    - Blog
    - Documentation
    - News website

A WEB APPLICATION provides interactive functionality.

Examples:

    - Gmail
    - Google Docs
    - Online banking
    - Shopping cart
    - Project management software
    - Learning management systems

The distinction is not always absolute.

Modern websites often contain application-like functionality.

For example:

    A news website:
        mostly content

    An e-commerce website:
        content + accounts + search + cart + payments

    Google Docs:
        highly interactive application

The important idea is:

    Website
        -> primarily information/content

    Web Application
        -> primarily functionality/interactivity

Modern web systems often combine both.
""")

pause()


# =============================================================================
# SECTION 4 - FRONTEND
# =============================================================================

title("4. Frontend Development")

explain("""
Frontend development deals with the part of a web system that users
directly see and interact with.

Typical frontend technologies include:

    HTML
    CSS
    JavaScript

HTML
----
Defines structure.

Example:

    <h1>Hello World</h1>

CSS
---
Defines presentation.

Example:

    h1 {
        font-size: 40px;
    }

JavaScript
----------
Defines behavior.

Example:

    button.addEventListener("click", function() {
        alert("Hello");
    });

Frontend responsibilities include:

    - Layout
    - Typography
    - Colors
    - Buttons
    - Forms
    - Navigation
    - Animations
    - Accessibility
    - Responsive design
    - Browser interactions
    - API communication
    - Client-side validation

Popular frontend ecosystems include:

    React
    Angular
    Vue
    Svelte
    Next.js

But frameworks are NOT prerequisites for understanding frontend development.

HTML + CSS + JavaScript are fundamental.
""")

pause()


# =============================================================================
# SECTION 5 - BACKEND
# =============================================================================

title("5. Backend Development")

explain("""
Backend development deals with server-side functionality.

A backend may:

    - Authenticate users
    - Process requests
    - Validate data
    - Apply business rules
    - Query databases
    - Process payments
    - Send emails
    - Generate responses
    - Manage files
    - Expose APIs

Common backend languages include:

    Python
    JavaScript / Node.js
    Java
    C#
    Go
    PHP
    Ruby
    Rust
    Kotlin

Common backend frameworks include:

    Django
    Flask
    FastAPI
    Express
    Spring Boot
    ASP.NET
    Laravel
    Ruby on Rails

A backend usually communicates with:

    Browser
       |
       v
    API
       |
       v
    Backend
       |
       +------> Database
       |
       +------> Cache
       |
       +------> External APIs
       |
       +------> File Storage
""")

pause()


# =============================================================================
# SECTION 6 - FULL STACK
# =============================================================================

title("6. Full-Stack Development")

explain("""
A full-stack developer understands multiple layers of a web application.

Typical stack:

    FRONTEND
        HTML
        CSS
        JavaScript
        React / Vue / Angular

    BACKEND
        Python / Node.js / Java / etc.
        API
        Business logic

    DATABASE
        PostgreSQL
        MySQL
        MongoDB
        Redis

    INFRASTRUCTURE
        Linux
        Cloud
        Docker
        Reverse proxy
        CI/CD

Full-stack does NOT mean that one person must know every technology
perfectly.

It means understanding how the major layers connect.
""")

pause()


# =============================================================================
# SECTION 7 - STATIC VS DYNAMIC
# =============================================================================

title("7. Static vs Dynamic Websites")

explain("""
STATIC WEBSITE
--------------

A static website usually serves files that already exist.

Example:

    index.html
    about.html
    styles.css
    script.js
    image.jpg

The server can simply return these files.

Conceptually:

    Browser
       |
       | GET /about.html
       v
    Server
       |
       | read file
       v
    about.html
       |
       v
    Browser

DYNAMIC WEBSITE
---------------

A dynamic website generates or retrieves content based on a request.

Example:

    User logs in.

    Backend:
        identifies user
        queries database
        generates response

Conceptually:

    Browser
       |
       | GET /profile
       v
    Backend
       |
       | query database
       v
    Database
       |
       | user data
       v
    Backend
       |
       | HTML / JSON
       v
    Browser

Static does not necessarily mean "simple".

Modern static-site architectures can be extremely sophisticated.
""")

pause()


# =============================================================================
# SECTION 8 - URL
# =============================================================================

title("8. Understanding a URL")

url = "https://www.example.com:443/products?id=42#reviews"

parsed = urlparse(url)

print("Example URL:")
print(url)

print("\nParsed components:")
print("Scheme      :", parsed.scheme)
print("Hostname    :", parsed.hostname)
print("Port        :", parsed.port)
print("Path        :", parsed.path)
print("Query       :", parsed.query)
print("Fragment    :", parsed.fragment)

explain("""
A URL may contain:

    Scheme
        https

    Hostname
        www.example.com

    Port
        443

    Path
        /products

    Query string
        ?id=42

    Fragment
        #reviews

The browser uses these components to determine what resource is requested
and how the connection should be established.
""")

pause()


# =============================================================================
# SECTION 9 - DOMAIN
# =============================================================================

title("9. What is a Domain?")

explain("""
A domain is a human-readable name used to identify an Internet resource.

Examples:

    example.com
    google.com
    wikipedia.org

Computers communicate using IP addresses.

Humans prefer names.

Instead of remembering:

    142.250.x.x

users can type:

    google.com

DNS connects the domain name to the appropriate IP address.

Conceptually:

    google.com
        |
        v
       DNS
        |
        v
    IP address
        |
        v
    Server
""")

pause()


# =============================================================================
# SECTION 10 - DNS SIMULATION
# =============================================================================

title("10. DNS Simulation")

dns_table = {
    "example.com": "93.184.216.34",
    "myshop.com": "203.0.113.10",
    "myapp.com": "203.0.113.20",
    "api.myapp.com": "203.0.113.30"
}


def dns_lookup(domain):
    print(f"\nDNS lookup for: {domain}")

    if domain in dns_table:
        print("DNS result:", dns_table[domain])
        return dns_table[domain]

    print("Domain not found in simulated DNS.")
    return None


domain = input("\nEnter a simulated domain (or press Enter for example.com): ")

if not domain:
    domain = "example.com"

dns_lookup(domain)

pause()


# =============================================================================
# SECTION 11 - IP ADDRESSES
# =============================================================================

title("11. IP Addresses")

explain("""
An IP address identifies a network interface or host within an IP network.

IPv4 example:

    192.168.1.10

IPv6 example:

    2001:db8::1

There are several important distinctions.

PUBLIC IP
---------
Routable on the public Internet.

PRIVATE IP
----------
Used inside private networks.

Examples:

    10.x.x.x
    172.16.x.x - 172.31.x.x
    192.168.x.x

LOOPBACK
--------
Usually:

    127.0.0.1

This refers to the local machine.

When developing locally, you may access:

    http://localhost

or:

    http://127.0.0.1

This does NOT mean the website is publicly available.
""")

pause()


# =============================================================================
# SECTION 12 - PORTS
# =============================================================================

title("12. Ports")

explain("""
A computer can run many network services simultaneously.

Ports help distinguish services.

Common examples:

    HTTP       -> 80
    HTTPS      -> 443
    SSH        -> 22

Development servers often use ports such as:

    3000
    5000
    8000
    8080

Example:

    http://localhost:8000

Here:

    localhost = computer
    8000       = network port

A port is NOT the same thing as an IP address.

IP address identifies the host.

Port identifies a service/application endpoint on that host.
""")

pause()


# =============================================================================
# SECTION 13 - CLIENT SERVER MODEL
# =============================================================================

title("13. Client-Server Model")

explain("""
The client-server model is one of the fundamental concepts of web
development.

CLIENT
------

Usually the browser.

Examples:

    Chrome
    Firefox
    Safari
    Edge

SERVER
------

A computer/process that receives requests and provides services.

The client asks.

The server responds.

Conceptually:

    CLIENT
       |
       | Request
       v
    SERVER
       |
       | Response
       v
    CLIENT

The client and server may be physically located thousands of kilometers
apart.
""")

pause()


# =============================================================================
# SECTION 14 - REQUEST RESPONSE CYCLE
# =============================================================================

title("14. Request-Response Cycle")

explain("""
Suppose you type:

    https://example.com

A simplified process is:

STEP 1
------
Browser parses the URL.

STEP 2
------
Browser determines that HTTPS is required.

STEP 3
------
Browser resolves the domain through DNS.

STEP 4
------
Browser establishes a network connection.

STEP 5
------
For HTTPS, TLS negotiation takes place.

STEP 6
------
Browser sends an HTTP request.

Example:

    GET / HTTP/1.1
    Host: example.com

STEP 7
------
Server processes the request.

STEP 8
------
Server returns an HTTP response.

Example:

    HTTP/1.1 200 OK
    Content-Type: text/html

STEP 9
------
Browser receives the response.

STEP 10
-------
Browser parses HTML.

STEP 11
-------
Browser discovers CSS, JavaScript, images, fonts, etc.

STEP 12
-------
Browser requests those resources.

STEP 13
-------
Browser constructs the page and displays it.

This process can involve many additional layers in a real production system.
""")

pause()


# =============================================================================
# SECTION 15 - HTTP
# =============================================================================

title("15. HTTP")

explain("""
HTTP means:

    Hypertext Transfer Protocol

It defines how web clients and servers communicate.

Common HTTP methods:

    GET
        Retrieve data.

    POST
        Submit/create data.

    PUT
        Replace a resource.

    PATCH
        Partially update a resource.

    DELETE
        Delete a resource.

Example:

    GET /products

Could mean:

    "Give me the products."

Example:

    POST /users

Could mean:

    "Create a new user."
""")

pause()


# =============================================================================
# SECTION 16 - HTTP STATUS CODES
# =============================================================================

title("16. HTTP Status Codes")

status_codes = {
    200: "OK",
    201: "Created",
    204: "No Content",
    301: "Moved Permanently",
    302: "Found / Redirect",
    304: "Not Modified",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    409: "Conflict",
    429: "Too Many Requests",
    500: "Internal Server Error",
    502: "Bad Gateway",
    503: "Service Unavailable"
}

for code, meaning in status_codes.items():
    print(f"{code} -> {meaning}")

explain("""
Status codes are grouped into classes:

    1xx -> Informational
    2xx -> Successful
    3xx -> Redirection
    4xx -> Client-side/request errors
    5xx -> Server-side errors
""")

pause()


# =============================================================================
# SECTION 17 - HTTP REQUEST SIMULATION
# =============================================================================

title("17. HTTP Request Simulation")


class HttpRequest:
    def __init__(self, method, url, headers=None, body=None):
        self.method = method
        self.url = url
        self.headers = headers or {}
        self.body = body

    def display(self):
        print("\n--- HTTP REQUEST ---")
        print("Method :", self.method)
        print("URL    :", self.url)
        print("Headers:")

        for key, value in self.headers.items():
            print(f"    {key}: {value}")

        print("Body   :", self.body)


request = HttpRequest(
    method="GET",
    url="/products",
    headers={
        "Host": "example.com",
        "User-Agent": "Chrome",
        "Accept": "text/html"
    }
)

request.display()

pause()


# =============================================================================
# SECTION 18 - HTTP RESPONSE SIMULATION
# =============================================================================

title("18. HTTP Response Simulation")


class HttpResponse:
    def __init__(self, status_code, headers=None, body=""):
        self.status_code = status_code
        self.headers = headers or {}
        self.body = body

    def display(self):
        print("\n--- HTTP RESPONSE ---")
        print(
            self.status_code,
            status_codes.get(self.status_code, "Unknown Status")
        )

        print("\nHeaders:")

        for key, value in self.headers.items():
            print(f"    {key}: {value}")

        print("\nBody:")
        print(self.body)


response = HttpResponse(
    status_code=200,
    headers={
        "Content-Type": "text/html",
        "Content-Length": "42"
    },
    body="<html><body>Hello Web!</body></html>"
)

response.display()

pause()


# =============================================================================
# SECTION 19 - BROWSER
# =============================================================================

title("19. What Does a Browser Actually Do?")

explain("""
A browser is much more than an application that displays websites.

A modern browser performs:

    - DNS-related networking
    - HTTP communication
    - TLS communication
    - HTML parsing
    - CSS parsing
    - JavaScript execution
    - DOM construction
    - Rendering
    - Image decoding
    - Font handling
    - Storage
    - Cookie management
    - Security enforcement
    - Cache management
    - Developer tooling

When the browser receives:

    <h1>Hello</h1>

it does not simply print the text.

It parses HTML and constructs an internal representation called the DOM.

DOM means:

    Document Object Model

JavaScript can interact with the DOM.

Example concept:

    HTML
      |
      v
    Parser
      |
      v
    DOM
      |
      v
    CSS + JavaScript
      |
      v
    Rendering
      |
      v
    Pixels on screen
""")

pause()


# =============================================================================
# SECTION 20 - CHROME DEVTOOLS
# =============================================================================

title("20. Chrome Developer Tools")

explain("""
Chrome Developer Tools are one of the most important tools for web
development.

Open them using:

    F12

or:

    Ctrl + Shift + I

Important tabs include:

    Elements
        Inspect HTML and CSS.

    Console
        Run JavaScript and inspect errors.

    Network
        Inspect HTTP requests and responses.

    Sources
        Inspect JavaScript and source files.

    Application
        Inspect cookies, storage, cache, etc.

    Performance
        Analyze browser performance.

    Security
        Inspect security information.

The Network tab is especially important.

It can show:

    Request URL
    Method
    Status code
    Request headers
    Response headers
    Payload
    Timing
    Response body
""")

pause()


# =============================================================================
# SECTION 21 - SERVER
# =============================================================================

title("21. What is a Server?")

explain("""
A server can mean two related things.

SERVER AS A COMPUTER
--------------------

A machine that provides services.

SERVER AS SOFTWARE
------------------

A program that listens for requests and sends responses.

For example:

    Browser
       |
       v
    Web Server
       |
       v
    Response

Popular web servers include:

    Nginx
    Apache
    Caddy

Application servers/frameworks include:

    Node.js
    Gunicorn
    Uvicorn
    Java application servers
    ASP.NET servers

In modern architecture, multiple server components may work together.
""")

pause()


# =============================================================================
# SECTION 22 - SIMPLE SERVER SIMULATION
# =============================================================================

title("22. Simple Web Server Simulation")


class SimpleServer:
    def __init__(self):
        self.routes = {
            "/": "<h1>Home Page</h1>",
            "/about": "<h1>About Page</h1>",
            "/contact": "<h1>Contact Page</h1>"
        }

    def handle_request(self, path):
        if path in self.routes:
            return HttpResponse(
                status_code=200,
                headers={"Content-Type": "text/html"},
                body=self.routes[path]
            )

        return HttpResponse(
            status_code=404,
            headers={"Content-Type": "text/html"},
            body="<h1>404 - Page Not Found</h1>"
        )


server = SimpleServer()

paths = ["/", "/about", "/contact", "/does-not-exist"]

for path in paths:
    print(f"\nRequesting: {path}")
    result = server.handle_request(path)
    result.display()

pause()


# =============================================================================
# SECTION 23 - BACKEND BUSINESS LOGIC
# =============================================================================

title("23. Backend Business Logic")

explain("""
Backend code does more than return pages.

Suppose an online store receives:

    POST /checkout

The backend may:

    1. Authenticate the user.
    2. Validate the cart.
    3. Check inventory.
    4. Calculate price.
    5. Calculate taxes.
    6. Apply discounts.
    7. Create an order.
    8. Process payment.
    9. Update inventory.
    10. Send confirmation.
    11. Return the result.

This is called business logic.

The frontend should not be trusted to make critical business decisions.

For example:

    frontend says:
        "The price is ₹100."

The backend should verify the price.

Security principle:

    Never trust client-controlled data.
""")

pause()


# =============================================================================
# SECTION 24 - DATABASE
# =============================================================================

title("24. Databases in Web Development")

explain("""
Most useful web applications need persistent data.

Examples:

    Users
    Products
    Orders
    Messages
    Payments
    Posts
    Comments

A database stores this information.

Popular relational databases:

    PostgreSQL
    MySQL
    SQLite
    Microsoft SQL Server

Popular non-relational systems:

    MongoDB
    Redis
    DynamoDB

Typical architecture:

    Browser
       |
       v
    Backend
       |
       v
    Database

The browser generally should NOT connect directly to the production
database.

The backend acts as a controlled intermediary.
""")

pause()


# =============================================================================
# SECTION 25 - API
# =============================================================================

title("25. APIs")

explain("""
API means:

    Application Programming Interface

A web API provides a structured way for software components to communicate.

Example:

    GET /api/products

Could return:

    {
        "products": [
            {
                "id": 1,
                "name": "Laptop",
                "price": 50000
            }
        ]
    }

The frontend can then display the information.

Common API styles:

    REST
    GraphQL
    RPC
    WebSockets

Modern web applications frequently use JSON.

JSON example:

    {
        "name": "Atul",
        "role": "developer"
    }
""")

pause()


# =============================================================================
# SECTION 26 - JSON SIMULATION
# =============================================================================

title("26. JSON Data Simulation")

import json

user = {
    "id": 101,
    "name": "Alex",
    "skills": [
        "HTML",
        "CSS",
        "JavaScript",
        "Python"
    ],
    "is_active": True
}

json_data = json.dumps(user, indent=4)

print(json_data)

decoded = json.loads(json_data)

print("\nDecoded Python object:")
print(decoded)

pause()


# =============================================================================
# SECTION 27 - AUTHENTICATION
# =============================================================================

title("27. Authentication and Authorization")

explain("""
AUTHENTICATION
--------------

Answers:

    "Who are you?"

Example:

    Username + password

AUTHORIZATION
-------------

Answers:

    "What are you allowed to do?"

Example:

    Normal user:
        Can view profile.

    Administrator:
        Can delete users.

A simplified flow:

    Browser
       |
       | Login credentials
       v
    Backend
       |
       | Verify credentials
       v
    Database
       |
       | User valid
       v
    Backend
       |
       | Session/token
       v
    Browser

Authentication is one of the most important areas of web security.
""")

pause()


# =============================================================================
# SECTION 28 - COOKIES
# =============================================================================

title("28. Cookies")

explain("""
Cookies are small pieces of data associated with a website/domain.

They can be used for:

    - Sessions
    - Preferences
    - Authentication state
    - Analytics
    - Personalization

Example conceptual flow:

    Browser -> Login -> Server

    Server:
        "Set a session cookie."

    Browser stores cookie.

    Future request:

        Browser
            |
            | Cookie
            v
        Server

Cookies have security-related attributes such as:

    Secure
    HttpOnly
    SameSite

These attributes matter significantly for web security.
""")

pause()


# =============================================================================
# SECTION 29 - SESSION
# =============================================================================

title("29. Sessions")

explain("""
A session allows a server to associate multiple requests with a user.

For example:

    Request 1:
        POST /login

    Response:
        session identifier

    Request 2:
        GET /profile
        session identifier included

Server:

    session ID
       |
       v
    user = 123

The server can therefore recognize the user.

Modern applications may also use token-based approaches.

Examples:

    Session cookies
    JWT
    OAuth tokens

Each mechanism has different security and architectural tradeoffs.
""")

pause()


# =============================================================================
# SECTION 30 - HTTPS
# =============================================================================

title("30. HTTPS")

explain("""
HTTPS is HTTP transported over TLS.

TLS provides security properties such as:

    - Encryption
    - Authentication of the server
    - Integrity protection

Without encryption, network traffic can potentially be observed or
modified by attackers in hostile network environments.

HTTPS uses certificates and cryptographic protocols to establish trust.

Typical production websites should use HTTPS.
""")

pause()


# =============================================================================
# SECTION 31 - HOSTING
# =============================================================================

title("31. Web Hosting")

explain("""
Hosting means making your web application or website available on
infrastructure that can serve users.

Hosting can involve:

    - Physical servers
    - Virtual machines
    - Containers
    - Serverless platforms
    - Cloud platforms
    - Static hosting platforms

Typical flow:

    Domain
       |
       v
    DNS
       |
       v
    Hosting infrastructure
       |
       v
    Application
""")

pause()


# =============================================================================
# SECTION 32 - LOCALHOST
# =============================================================================

title("32. Local Development")

explain("""
During development, applications are often run locally.

Example:

    http://localhost:8000

This means:

    Protocol = HTTP
    Host     = local machine
    Port     = 8000

A local server might run:

    FastAPI
    Django
    Flask
    Node.js
    React development server
    Vite

Local development allows developers to test software before deployment.
""")

pause()


# =============================================================================
# SECTION 33 - DEVELOPMENT ENVIRONMENT
# =============================================================================

title("33. VS Code")

explain("""
VS Code is a source-code editor widely used for web development.

Useful capabilities include:

    - Syntax highlighting
    - Code completion
    - Debugging
    - Extensions
    - Git integration
    - Integrated terminal
    - File explorer
    - Search
    - Formatting
    - Refactoring

A typical project might look like:

    my-web-project/
    |
    +-- index.html
    +-- style.css
    +-- script.js
    +-- images/
    +-- backend/
    +-- README.md

VS Code is an editor.

It is NOT the browser.

Chrome is used to execute and inspect web applications from the browser side.
""")

pause()


# =============================================================================
# SECTION 34 - FRONTEND FILES
# =============================================================================

title("34. Basic Frontend Files")

html = """
<!DOCTYPE html>
<html>
<head>
    <title>My Website</title>
</head>
<body>
    <h1>Hello Web!</h1>
    <button id="helloButton">Click Me</button>
</body>
</html>
"""

css = """
body {
    font-family: Arial, sans-serif;
}

h1 {
    font-size: 40px;
}
"""

javascript = """
document
    .getElementById("helloButton")
    .addEventListener("click", function () {
        alert("Hello!");
    });
"""

print("HTML:")
print(html)

print("\nCSS:")
print(css)

print("\nJavaScript:")
print(javascript)

pause()


# =============================================================================
# SECTION 35 - DOM
# =============================================================================

title("35. DOM - Document Object Model")

explain("""
Consider:

    <body>
        <h1>Hello</h1>
        <button>Click</button>
    </body>

The browser converts this into a tree-like structure.

Conceptually:

    Document
       |
       +-- body
            |
            +-- h1
            |    |
            |    +-- "Hello"
            |
            +-- button
                 |
                 +-- "Click"

JavaScript can modify this structure.

For example:

    Change text
    Add elements
    Remove elements
    Change classes
    Respond to events

This is one of the foundations of interactive web development.
""")

pause()


# =============================================================================
# SECTION 36 - CLIENT-SIDE RENDERING
# =============================================================================

title("36. Client-Side Rendering")

explain("""
In client-side rendering, the browser executes JavaScript and constructs
much of the UI on the client.

Simplified:

    Server
       |
       | HTML + JavaScript
       v
    Browser
       |
       | JavaScript executes
       v
    UI

Frameworks such as React can use this model extensively.

Benefits can include:

    - Rich interactions
    - Application-like behavior
    - Dynamic UI updates

Tradeoffs can include:

    - Larger JavaScript payloads
    - More browser work
    - Potential SEO/performance complexity
""")

pause()


# =============================================================================
# SECTION 37 - SERVER-SIDE RENDERING
# =============================================================================

title("37. Server-Side Rendering")

explain("""
In server-side rendering, the server generates HTML before sending it
to the browser.

Conceptually:

    Browser
       |
       | Request
       v
    Server
       |
       | Generate HTML
       v
    Browser
       |
       v
    Render page

SSR can improve initial rendering and can be useful for SEO.

Modern frameworks can combine:

    SSR
    CSR
    Static generation
    Streaming
    Partial rendering

The boundary between frontend and backend is therefore more flexible
than simple beginner diagrams suggest.
""")

pause()


# =============================================================================
# SECTION 38 - CACHING
# =============================================================================

title("38. Caching")

explain("""
Caching means storing reusable data so that it can be served faster.

Caching can happen at many levels:

    Browser cache
    CDN cache
    Reverse proxy cache
    Application cache
    Database cache

Example:

    Without cache:

    Browser
       |
       v
    Server
       |
       v
    Database

    With cache:

    Browser
       |
       v
    Cache
       |
       +----> HIT -> response
       |
       +----> MISS -> server/database

Caching can reduce latency and server/database load.

But caching creates complexity.

The classic problem is:

    "How do we know when cached data is stale?"
""")

pause()


# =============================================================================
# SECTION 39 - CDN
# =============================================================================

title("39. CDN")

explain("""
CDN means:

    Content Delivery Network

A CDN distributes content through geographically distributed edge
locations.

Instead of:

    User in India
       |
       v
    Origin server in USA

a CDN may allow:

    User in India
       |
       v
    Nearby CDN edge
       |
       v
    Cached content

CDNs are especially useful for:

    - Images
    - CSS
    - JavaScript
    - Videos
    - Static files
    - Cached web pages

Benefits include:

    Lower latency
    Reduced origin load
    Better global distribution
""")

pause()


# =============================================================================
# SECTION 40 - REVERSE PROXY
# =============================================================================

title("40. Reverse Proxy")

explain("""
A reverse proxy sits in front of backend servers.

Conceptually:

    Client
       |
       v
    Reverse Proxy
       |
       +------> Backend 1
       |
       +------> Backend 2
       |
       +------> Backend 3

Responsibilities can include:

    - TLS termination
    - Routing
    - Load balancing
    - Compression
    - Caching
    - Security filtering
    - Rate limiting

Nginx is a popular reverse proxy/web server.
""")

pause()


# =============================================================================
# SECTION 41 - LOAD BALANCING
# =============================================================================

title("41. Load Balancing")

explain("""
Suppose one backend server cannot handle all requests.

Instead:

             +--> Server 1
             |
    Client -> Load Balancer
             |
             +--> Server 2
             |
             +--> Server 3

The load balancer distributes traffic.

Benefits:

    - Scalability
    - Availability
    - Fault tolerance

If Server 1 fails, the load balancer may route traffic to healthy servers.

Large web applications frequently use multiple layers of infrastructure.
""")

pause()


# =============================================================================
# SECTION 42 - SCALABILITY
# =============================================================================

title("42. Scalability")

explain("""
Scalability means the ability of a system to handle increasing workload.

VERTICAL SCALING
----------------

Make one machine more powerful.

Example:

    4 CPU -> 16 CPU

HORIZONTAL SCALING
------------------

Add more machines.

Example:

    1 server
        ->
    10 servers

Horizontal scaling often requires:

    Load balancing
    Shared state management
    Distributed caching
    Database scaling
    Observability
    Fault tolerance

Web development therefore eventually becomes distributed systems engineering.
""")

pause()


# =============================================================================
# SECTION 43 - DATABASE FLOW
# =============================================================================

title("43. Complete Request Flow")

explain("""
Consider:

    User opens:

        https://shop.example/products

A simplified production architecture could be:

    USER
      |
      v
    CHROME
      |
      v
    DNS
      |
      v
    CDN
      |
      v
    LOAD BALANCER
      |
      v
    REVERSE PROXY
      |
      v
    APPLICATION SERVER
      |
      +----------> CACHE
      |
      +----------> DATABASE
      |
      +----------> PAYMENT API
      |
      +----------> EMAIL SERVICE

The response then travels back toward the browser.

This is why "building a website" can involve a very large engineering
ecosystem.
""")

pause()


# =============================================================================
# SECTION 44 - REQUEST FLOW SIMULATOR
# =============================================================================

title("44. Request Flow Simulator")


def simulate_request():
    steps = [
        "User enters URL in Chrome",
        "Browser parses URL",
        "Browser checks cache",
        "Browser performs DNS resolution",
        "Browser establishes network connection",
        "TLS negotiation occurs",
        "Browser sends HTTP request",
        "CDN / reverse proxy receives request",
        "Request is routed to application",
        "Backend validates request",
        "Backend checks cache",
        "Backend queries database if required",
        "Backend creates response",
        "Server sends HTTP response",
        "Browser receives response",
        "Browser parses HTML",
        "Browser downloads CSS/JavaScript/images",
        "Browser constructs DOM and CSSOM",
        "Browser performs rendering",
        "User sees the page"
    ]

    for number, step in enumerate(steps, start=1):
        print(f"{number:02d}. {step}")
        time.sleep(0.05)


simulate_request()

pause()


# =============================================================================
# SECTION 45 - STATIC SITE ARCHITECTURE
# =============================================================================

title("45. Static Website Architecture")

explain("""
A simple static architecture:

    User
      |
      v
    DNS
      |
      v
    CDN / Static Host
      |
      +-- index.html
      +-- style.css
      +-- script.js
      +-- images

There may be no traditional application server.

Static hosting is often:

    fast
    simple
    inexpensive
    highly cacheable

But interactive functionality may require APIs or backend services.
""")

pause()


# =============================================================================
# SECTION 46 - DYNAMIC APPLICATION ARCHITECTURE
# =============================================================================

title("46. Dynamic Web Application Architecture")

explain("""
A dynamic application might use:

    Browser
       |
       v
    CDN
       |
       v
    Reverse Proxy
       |
       v
    Backend
       |
       +----> Database
       |
       +----> Redis
       |
       +----> External APIs

For example:

    /products

might query a database.

    /login

might authenticate a user.

    /checkout

might interact with payment infrastructure.

    /dashboard

might aggregate information from multiple sources.
""")

pause()


# =============================================================================
# SECTION 47 - SECURITY
# =============================================================================

title("47. Web Security Fundamentals")

explain("""
Important web security concepts include:

    HTTPS
    Authentication
    Authorization
    Input validation
    Output encoding
    Password hashing
    Secure cookies
    CSRF protection
    XSS prevention
    SQL injection prevention
    Rate limiting
    Access control
    Security headers
    Secrets management

Three especially important attack categories:

XSS
---
Cross-Site Scripting.

Attacker-controlled content is executed as JavaScript in another user's
browser.

SQL INJECTION
-------------

Untrusted input changes the meaning of a database query.

CSRF
----

Cross-Site Request Forgery.

An attacker attempts to cause a victim's browser to perform an unwanted
authenticated action.

Security should be considered from the beginning rather than added at
the end.
""")

pause()


# =============================================================================
# SECTION 48 - DATABASE INJECTION SIMULATION
# =============================================================================

title("48. Why Input Validation Matters")

explain("""
Imagine a dangerous application constructing SQL using raw user input:

    query = "SELECT * FROM users WHERE name = '" + user_input + "'"

This is unsafe.

The correct general approach is to use:

    Parameterized queries
    Prepared statements
    ORM protections

The important lesson:

    Never assume user input is trustworthy.

This principle applies to:

    Forms
    URLs
    Cookies
    Headers
    JSON
    File uploads
    API requests
""")

pause()


# =============================================================================
# SECTION 49 - STATELESS VS STATEFUL
# =============================================================================

title("49. Stateless vs Stateful Systems")

explain("""
HTTP itself is fundamentally request/response oriented.

A stateless backend attempts to process each request without relying
on server-local memory of previous requests.

State can instead be stored in:

    Database
    Cache
    Session store
    Client-side token

Stateless architectures can make horizontal scaling easier.

Example:

    Request 1 -> Server A
    Request 2 -> Server B
    Request 3 -> Server C

All servers can still understand the user if shared state is available
through appropriate mechanisms.
""")

pause()


# =============================================================================
# SECTION 50 - WEB SOCKETS
# =============================================================================

title("50. Real-Time Web Applications")

explain("""
Traditional HTTP commonly follows:

    Client -> Request
    Server -> Response

For real-time systems, technologies such as WebSockets allow a persistent
two-way communication channel.

Useful for:

    - Chat applications
    - Live notifications
    - Multiplayer games
    - Real-time dashboards
    - Collaborative applications

Conceptually:

    Client <=================> Server

Both sides can exchange messages after the connection is established.
""")

pause()


# =============================================================================
# SECTION 51 - REST API SIMULATION
# =============================================================================

title("51. REST API Simulation")


class ProductAPI:
    def __init__(self):
        self.products = [
            {"id": 1, "name": "Laptop", "price": 70000},
            {"id": 2, "name": "Phone", "price": 50000},
            {"id": 3, "name": "Keyboard", "price": 3000}
        ]

    def get_products(self):
        return HttpResponse(
            200,
            {"Content-Type": "application/json"},
            json.dumps(self.products, indent=4)
        )

    def get_product(self, product_id):
        for product in self.products:
            if product["id"] == product_id:
                return HttpResponse(
                    200,
                    {"Content-Type": "application/json"},
                    json.dumps(product, indent=4)
                )

        return HttpResponse(
            404,
            {"Content-Type": "application/json"},
            json.dumps({"error": "Product not found"})
        )


api = ProductAPI()

print("\nGET /api/products")
api.get_products().display()

print("\nGET /api/products/2")
api.get_product(2).display()

print("\nGET /api/products/99")
api.get_product(99).display()

pause()


# =============================================================================
# SECTION 52 - DOMAIN TO SERVER SIMULATION
# =============================================================================

title("52. Domain-to-Server Simulation")


class WebInfrastructure:
    def __init__(self):
        self.dns = {
            "example.com": "203.0.113.10",
            "api.example.com": "203.0.113.20"
        }

        self.servers = {
            "203.0.113.10": "Static Web Server",
            "203.0.113.20": "API Application Server"
        }

    def request(self, domain):
        print(f"\n1. Browser requests domain: {domain}")

        ip = self.dns.get(domain)

        if not ip:
            print("2. DNS resolution failed.")
            return

        print(f"2. DNS resolves {domain} -> {ip}")

        server = self.servers.get(ip)

        print(f"3. Browser connects to: {server}")
        print("4. Server receives HTTP request")
        print("5. Server sends HTTP response")
        print("6. Browser renders result")


infrastructure = WebInfrastructure()

infrastructure.request("example.com")
infrastructure.request("api.example.com")
infrastructure.request("unknown.example.com")

pause()


# =============================================================================
# SECTION 53 - BROWSER RENDERING PIPELINE
# =============================================================================

title("53. Browser Rendering Pipeline")

explain("""
A simplified browser rendering process:

    HTML
      |
      v
    DOM
      |
      |
    CSS
      |
      v
    CSSOM
      |
      +------+
             |
             v
       Render Tree
             |
             v
          Layout
             |
             v
          Paint
             |
             v
        Compositing
             |
             v
          Screen

Modern browsers perform many optimizations.

JavaScript can affect rendering and performance.

This is why frontend development is partly about understanding how the
browser actually works.
""")

pause()


# =============================================================================
# SECTION 54 - SEO
# =============================================================================

title("54. SEO and Web Development")

explain("""
SEO means:

    Search Engine Optimization

Web development affects SEO through:

    - Semantic HTML
    - Page titles
    - Metadata
    - Content structure
    - Performance
    - Mobile usability
    - Accessibility
    - Crawlability
    - Internal linking
    - Structured data

Search engines need to discover, crawl, understand, and index content.

Rendering strategy can therefore influence discoverability.
""")

pause()


# =============================================================================
# SECTION 55 - ACCESSIBILITY
# =============================================================================

title("55. Accessibility")

explain("""
Accessible web development aims to make websites usable by people with
different abilities.

Important concepts:

    Semantic HTML
    Keyboard navigation
    Screen readers
    Color contrast
    Labels
    Alternative text
    Focus management
    Accessible forms

For example:

Prefer:

    <button>Submit</button>

over using a generic element that merely looks like a button.

Semantic HTML communicates meaning to browsers, assistive technologies,
developers, and search engines.
""")

pause()


# =============================================================================
# SECTION 56 - RESPONSIVE DESIGN
# =============================================================================

title("56. Responsive Web Design")

explain("""
A website may be accessed from:

    Desktop
    Laptop
    Tablet
    Phone
    Large monitor
    Small screen

Responsive design allows interfaces to adapt.

Important concepts:

    Flexible layouts
    CSS Grid
    Flexbox
    Media queries
    Relative units
    Responsive images
    Mobile-first design

The goal is not simply to shrink desktop websites.

The layout may fundamentally change based on available screen space.
""")

pause()


# =============================================================================
# SECTION 57 - DEVELOPMENT VS PRODUCTION
# =============================================================================

title("57. Development vs Production")

explain("""
DEVELOPMENT
-----------

Environment used while building software.

Characteristics:

    Debugging enabled
    Local servers
    Test data
    Developer tools
    Frequent code changes

PRODUCTION
----------

Environment used by real users.

Requirements often include:

    Security
    Reliability
    Monitoring
    Logging
    Backups
    Scalability
    Performance
    Error handling
    Deployment automation

Never assume that code that works locally is automatically production-ready.
""")

pause()


# =============================================================================
# SECTION 58 - DEPLOYMENT
# =============================================================================

title("58. Deployment")

explain("""
Deployment means making a software version available in its target
environment.

A simplified pipeline:

    Developer
       |
       v
    Git
       |
       v
    CI/CD
       |
       v
    Build
       |
       v
    Tests
       |
       v
    Deployment
       |
       v
    Production

Modern web development commonly uses:

    Git
    GitHub/GitLab/Bitbucket
    CI/CD
    Docker
    Cloud platforms
    Monitoring
""")

pause()


# =============================================================================
# SECTION 59 - WEB APPLICATION LAYERS
# =============================================================================

title("59. Layers of a Web Application")

layers = [
    "Presentation Layer",
    "Frontend Application",
    "API Layer",
    "Business Logic Layer",
    "Data Access Layer",
    "Database",
    "Infrastructure",
    "Networking",
    "Security",
    "Observability"
]

for i, layer in enumerate(layers, 1):
    print(f"{i:02d}. {layer}")

explain("""
A sophisticated web application can be understood as multiple layers.

The layers provide separation of concerns.

For example:

    Presentation
        -> what users see

    Business logic
        -> what the system does

    Data access
        -> how information is retrieved

    Database
        -> where persistent information lives

    Infrastructure
        -> where software runs
""")

pause()


# =============================================================================
# SECTION 60 - MICROSERVICES
# =============================================================================

title("60. Microservices Concept")

explain("""
A traditional application might be:

    One large application

A microservice architecture might contain:

    User Service
    Product Service
    Order Service
    Payment Service
    Notification Service

These services communicate through APIs or messaging systems.

Benefits may include:

    Independent deployment
    Team autonomy
    Independent scaling

Costs include:

    Network complexity
    Distributed failures
    Observability challenges
    Data consistency challenges
    Operational overhead

Microservices are NOT automatically better.

Architecture should match actual requirements.
""")

pause()


# =============================================================================
# SECTION 61 - MONOLITH
# =============================================================================

title("61. Monolithic Architecture")

explain("""
A monolith packages much of the application into one deployable unit.

Example:

    Browser
       |
       v
    One application
       |
       +---- Database

Monoliths can be:

    Easy to develop
    Easy to deploy
    Easy to debug initially

A monolith can also be highly scalable if designed properly.

"Monolith" does not automatically mean "bad architecture."
""")

pause()


# =============================================================================
# SECTION 62 - OBSERVABILITY
# =============================================================================

title("62. Observability")

explain("""
Production web systems need to answer:

    Is the system working?

    Why is it slow?

    Which requests are failing?

    Which service is causing the problem?

Important observability components:

    Logs
    Metrics
    Traces

LOGS
----

Events and messages generated by applications.

METRICS
-------

Numerical measurements.

Examples:

    CPU usage
    Request rate
    Error rate
    Latency

TRACES
------

Follow a request through distributed components.

Example:

    Browser
       |
       v
    API Gateway
       |
       v
    Service A
       |
       v
    Service B
       |
       v
    Database
""")

pause()


# =============================================================================
# SECTION 63 - PERFORMANCE
# =============================================================================

title("63. Web Performance")

explain("""
Important performance concepts include:

    Page load time
    Time to first byte
    Largest Contentful Paint
    Cumulative Layout Shift
    Interaction responsiveness
    JavaScript execution
    Network latency
    Image size
    Cache efficiency

Optimization strategies include:

    Compressing assets
    Lazy loading
    Caching
    CDN usage
    Code splitting
    Image optimization
    Reducing unnecessary JavaScript
    Efficient database queries

Performance is a full-stack concern.
""")

pause()


# =============================================================================
# SECTION 64 - COMMON MISTAKES
# =============================================================================

title("64. Common Beginner Mistakes")

mistakes = [
    "Thinking HTML is a programming language in the same sense as Python",
    "Learning a framework before understanding HTML/CSS/JavaScript",
    "Thinking frontend and backend are completely separate worlds",
    "Thinking a domain is the same thing as hosting",
    "Thinking localhost is public Internet hosting",
    "Thinking an IP address is the same thing as a domain",
    "Ignoring HTTP fundamentals",
    "Ignoring browser developer tools",
    "Trusting frontend validation for security",
    "Putting secrets in frontend JavaScript",
    "Connecting browsers directly to production databases",
    "Ignoring accessibility",
    "Ignoring performance",
    "Ignoring authentication and authorization differences",
    "Thinking every application needs microservices"
]

for number, mistake in enumerate(mistakes, 1):
    print(f"{number:02d}. {mistake}")

pause()


# =============================================================================
# SECTION 65 - MENTAL MODEL
# =============================================================================

title("65. The Complete Mental Model")

explain("""
Memorize this mental model:

    USER
      |
      v
    BROWSER
      |
      v
    URL
      |
      v
    DNS
      |
      v
    IP ADDRESS
      |
      v
    INTERNET
      |
      v
    CDN / REVERSE PROXY
      |
      v
    WEB SERVER
      |
      v
    APPLICATION / BACKEND
      |
      +------> CACHE
      |
      +------> DATABASE
      |
      +------> EXTERNAL APIs
      |
      v
    HTTP RESPONSE
      |
      v
    BROWSER
      |
      v
    HTML + CSS + JS
      |
      v
    DOM + CSSOM
      |
      v
    RENDERING
      |
      v
    USER

This is the conceptual foundation for everything that follows in web
development.
""")

pause()


# =============================================================================
# SECTION 66 - KNOWLEDGE CHECK
# =============================================================================

title("66. Knowledge Check")

questions = [
    {
        "question": "What does HTML primarily define?",
        "answer": "The structure and semantic content of a webpage."
    },
    {
        "question": "What does CSS primarily control?",
        "answer": "Presentation, layout, and visual styling."
    },
    {
        "question": "What does JavaScript primarily provide?",
        "answer": "Programming logic and interactive behavior."
    },
    {
        "question": "What is DNS?",
        "answer": "A system that maps domain names to network addresses."
    },
    {
        "question": "What is the purpose of a domain?",
        "answer": "To provide a human-readable name for an Internet resource."
    },
    {
        "question": "What is a server?",
        "answer": "A system or software process that provides services or responses."
    },
    {
        "question": "What is the client?",
        "answer": "The system making a request, commonly the browser."
    },
    {
        "question": "What does HTTP define?",
        "answer": "Rules for communication between HTTP clients and servers."
    },
    {
        "question": "What is HTTPS?",
        "answer": "HTTP protected by TLS."
    },
    {
        "question": "What does 404 mean?",
        "answer": "The requested resource was not found."
    },
    {
        "question": "What does 500 mean?",
        "answer": "The server encountered an internal error."
    },
    {
        "question": "What is an API?",
        "answer": "An interface that allows software components to communicate."
    },
    {
        "question": "What is frontend development?",
        "answer": "Development of the browser-side user interface and behavior."
    },
    {
        "question": "What is backend development?",
        "answer": "Development of server-side logic and services."
    },
    {
        "question": "What is full-stack development?",
        "answer": "Working across frontend, backend, data, and related infrastructure."
    }
]

score = 0

for i, item in enumerate(questions, 1):
    print(f"\nQuestion {i}: {item['question']}")
    user_answer = input("Your answer: ")

    print("\nExpected concept:")
    print(item["answer"])

    # This is an educational script, so scoring is manual.
    if user_answer.strip():
        score += 1

print("\nKnowledge-check participation score:", score, "/", len(questions))


# =============================================================================
# SECTION 67 - FINAL SUMMARY
# =============================================================================

title("67. Final Summary")

explain("""
You have now covered the conceptual foundation of Web Development.

The most important chain to remember is:

    Domain
       |
       v
    DNS
       |
       v
    IP
       |
       v
    Server
       |
       v
    HTTP Request
       |
       v
    Backend
       |
       +------> Database
       |
       +------> APIs
       |
       v
    HTTP Response
       |
       v
    Browser
       |
       v
    HTML
       +
    CSS
       +
    JavaScript
       |
       v
    DOM
       |
       v
    Rendering
       |
       v
    User

You should now understand:

    Web development
    Internet vs Web
    Websites
    Web applications
    Frontend
    Backend
    Full-stack
    Static websites
    Dynamic websites
    Client-server architecture
    URLs
    Domains
    DNS
    IP addresses
    Ports
    HTTP
    HTTPS
    Requests
    Responses
    Status codes
    Browsers
    Servers
    Hosting
    APIs
    Databases
    Authentication
    Cookies
    Sessions
    Caching
    CDNs
    Reverse proxies
    Load balancing
    Scalability
    Security
    Accessibility
    SEO
    Performance
    Deployment
    Observability
    Monoliths
    Microservices

The next logical step is to begin practical web development:

    HTML
      ->
    CSS
      ->
    JavaScript
      ->
    Git/GitHub
      ->
    Frontend framework
      ->
    Backend
      ->
    APIs
      ->
    SQL/PostgreSQL
      ->
    Authentication
      ->
    Deployment
      ->
    Cloud
      ->
    System design
""")

print("\n" + "=" * 80)
print("END OF INTRODUCTION TO WEB DEVELOPMENT")
print("=" * 80)
