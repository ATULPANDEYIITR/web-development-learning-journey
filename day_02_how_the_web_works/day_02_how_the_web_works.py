```python
"""
HOW THE WEB WORKS
=================

A detailed, executable study guide covering how the modern Web works,
from fundamental networking concepts to advanced Web architecture.

This script is intentionally written as an educational program rather
than as a collection of isolated definitions.

Topics covered
--------------
1. What the Web is
2. Internet vs Web
3. Clients and servers
4. IP addresses
5. Ports
6. MAC addresses and local networking
7. Packets
8. Routers
9. DNS
10. Domain names
11. URLs
12. HTTP and HTTPS
13. HTTP methods
14. HTTP request structure
15. HTTP response structure
16. HTTP status codes
17. Headers
18. Cookies
19. Sessions
20. Authentication
21. Authorization
22. Browser architecture
23. Rendering a webpage
24. HTML
25. CSS
26. JavaScript
27. DOM
28. Browser events
29. JavaScript execution
30. APIs
31. REST
32. JSON
33. TCP
34. UDP
35. TLS
36. HTTP/1.1
37. HTTP/2
38. HTTP/3
39. QUIC
40. Caching
41. CDNs
42. Reverse proxies
43. Load balancers
44. Web servers
45. Application servers
46. Databases
47. Authentication tokens
48. JWT
49. CORS
50. Same-origin policy
51. WebSockets
52. Server-Sent Events
53. Webhooks
54. Proxies
55. NAT
56. Firewalls
57. IPv4 and IPv6
58. Subnets
59. DHCP
60. ARP
61. Network layers
62. OSI model
63. TCP/IP model
64. Browser navigation lifecycle
65. Page loading
66. DNS lookup lifecycle
67. HTTPS connection lifecycle
68. Request-response lifecycle
69. Form submission
70. File downloads
71. Image loading
72. Video streaming
73. Authentication flow
74. API request lifecycle
75. Database-backed request
76. Cloud Web architecture
77. Microservices
78. Service discovery
79. Message queues
80. Distributed systems
81. Reliability
82. Latency
83. Throughput
84. Scalability
85. Security
86. Common Web attacks
87. XSS
88. CSRF
89. SQL injection
90. Clickjacking
91. DDoS
92. DNS attacks
93. TLS certificate concepts
94. Public-key cryptography
95. Symmetric cryptography
96. Hashing
97. Browser storage
98. LocalStorage
99. SessionStorage
100. IndexedDB
101. Service workers
102. Progressive Web Apps
103. HTTP caching semantics
104. ETags
105. Cache-Control
106. Compression
107. Content negotiation
108. MIME types
109. Content delivery
110. Web performance
111. Critical rendering path
112. Core concepts behind modern Web applications

The program does not require external libraries.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import base64
import hashlib
import ipaddress
import json
import re
import textwrap
import time
import urllib.parse
import uuid


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

WIDTH = 88


def line(char="=", width=WIDTH):
    print(char * width)


def title(text):
    print()
    line("=")
    print(text.center(WIDTH))
    line("=")


def section(text):
    print()
    line("-")
    print(text)
    line("-")


def subsection(text):
    print()
    print(text)
    print("." * len(text))


def explain(text):
    print(textwrap.fill(text, WIDTH))


def bullet(text):
    print("  • " + text)


def code_block(code):
    print()
    print("    " + code.replace("\n", "\n    "))
    print()


def pause():
    """
    Pause between major educational sections.

    Set INTERACTIVE = False near the bottom of the program if
    automatic execution is preferred.
    """
    if INTERACTIVE:
        input("\nPress Enter to continue...")


INTERACTIVE = False


# ============================================================
# 1. WHAT IS THE WEB?
# ============================================================

def topic_what_is_the_web():
    title("1. WHAT IS THE WEB?")

    explain(
        "The World Wide Web is a system of interconnected documents, "
        "applications, resources, and services that are accessed primarily "
        "through network protocols such as HTTP and HTTPS. The Web operates "
        "on top of the Internet."
    )

    explain(
        "The Internet is the underlying global network infrastructure. "
        "It connects computers, phones, servers, routers, data centers, "
        "and many other devices. The Web is one of the services that uses "
        "this infrastructure. Email, online gaming, file transfer, and "
        "many other systems can also use the Internet without being the Web."
    )

    subsection("A simple distinction")

    bullet("Internet = the global network infrastructure.")
    bullet("Web = a distributed information and application system running on that network.")
    bullet("Browser = software used to access Web resources.")
    bullet("Web server = software that responds to Web requests.")
    bullet("HTTP/HTTPS = protocols commonly used for Web communication.")
    bullet("URL = an address describing where a Web resource can be found.")

    subsection("Basic Web model")

    code_block(
        "User\n"
        "  |\n"
        "  v\n"
        "Web Browser\n"
        "  |\n"
        "  | HTTP/HTTPS\n"
        "  v\n"
        "Web Server\n"
        "  |\n"
        "  v\n"
        "Application\n"
        "  |\n"
        "  v\n"
        "Database"
    )

    explain(
        "A modern website may be considerably more complicated than this "
        "diagram. A browser may communicate with DNS infrastructure, CDNs, "
        "load balancers, reverse proxies, application servers, authentication "
        "systems, databases, object storage, caches, message brokers, and "
        "third-party services."
    )


# ============================================================
# 2. CLIENTS AND SERVERS
# ============================================================

def topic_client_server():
    title("2. CLIENTS AND SERVERS")

    explain(
        "A client is a program that initiates a request for a service or "
        "resource. A server is a program that listens for requests and "
        "provides a service or resource."
    )

    bullet("Browser = client.")
    bullet("Web server = server.")
    bullet("Mobile application = client.")
    bullet("API server = server.")
    bullet("Database server = server.")
    bullet("DNS resolver can act as a client toward authoritative DNS servers.")

    subsection("Important point")

    explain(
        "Client and server describe roles in communication. A physical "
        "computer can perform both roles. For example, a developer's "
        "computer can run a browser that acts as a client while simultaneously "
        "running a local development server that acts as a server."
    )


# ============================================================
# 3. IP ADDRESSES
# ============================================================

def topic_ip_addresses():
    title("3. IP ADDRESSES")

    explain(
        "An Internet Protocol address identifies a network interface or "
        "endpoint at the IP layer. IPv4 uses 32-bit addresses, normally "
        "written as four decimal octets. IPv6 uses 128-bit addresses."
    )

    subsection("IPv4 examples")

    addresses = [
        "192.168.1.10",
        "10.0.0.25",
        "172.16.5.20",
        "8.8.8.8",
    ]

    for address in addresses:
        try:
            ip = ipaddress.ip_address(address)
            bullet(f"{address} -> {ip.version}-bit addressing system: IPv{ip.version}")
        except ValueError:
            bullet(f"{address} -> invalid address")

    subsection("Public and private IPv4 ranges")

    bullet("10.0.0.0/8")
    bullet("172.16.0.0/12")
    bullet("192.168.0.0/16")

    explain(
        "Private addresses are normally used inside local networks. They "
        "are not globally routable across the public Internet. Network "
        "Address Translation, commonly called NAT, allows devices using "
        "private addresses to communicate through a public address."
    )

    subsection("IPv6")

    explain(
        "IPv6 was designed partly to address the exhaustion of IPv4 "
        "addresses. An IPv6 address is 128 bits and is written in hexadecimal "
        "groups separated by colons."
    )

    bullet("Example: 2001:db8::1")
    bullet("IPv6 provides a vastly larger address space than IPv4.")


# ============================================================
# 4. PORTS
# ============================================================

def topic_ports():
    title("4. PORTS")

    explain(
        "An IP address identifies a network endpoint at the IP layer, while "
        "a port identifies a logical service endpoint. TCP and UDP each "
        "provide port numbers from 0 through 65535."
    )

    common_ports = {
        20: "FTP data",
        21: "FTP control",
        22: "SSH",
        25: "SMTP",
        53: "DNS",
        80: "HTTP",
        110: "POP3",
        143: "IMAP",
        443: "HTTPS",
        3306: "MySQL",
        5432: "PostgreSQL",
        6379: "Redis",
        8080: "Common development HTTP port",
    }

    for port, service in common_ports.items():
        print(f"  {port:5} -> {service}")

    explain(
        "A connection is therefore commonly described using an IP address "
        "and a port. For example, a browser may communicate with a server "
        "at an IPv4 address on TCP port 443 for HTTPS."
    )


# ============================================================
# 5. PACKETS
# ============================================================

def topic_packets():
    title("5. PACKETS")

    explain(
        "Applications do not normally send an entire Web page as one "
        "undifferentiated physical transmission. Data is processed through "
        "multiple networking layers and transmitted using packets or frames."
    )

    subsection("Conceptual packet")

    packet = {
        "source_ip": "192.168.1.10",
        "destination_ip": "203.0.113.20",
        "protocol": "TCP",
        "source_port": 52144,
        "destination_port": 443,
        "payload": "Encrypted application data",
    }

    print(json.dumps(packet, indent=4))

    explain(
        "Real network packets contain much more information. Headers are "
        "added by different protocol layers. Routers examine relevant network "
        "information and forward packets toward their destinations."
    )


# ============================================================
# 6. ROUTERS
# ============================================================

def topic_routers():
    title("6. ROUTERS")

    explain(
        "A router forwards packets between networks. It uses routing "
        "information to determine where packets should go next."
    )

    code_block(
        "Laptop\n"
        "   |\n"
        "Home Router\n"
        "   |\n"
        "ISP Router\n"
        "   |\n"
        "Internet Routers\n"
        "   |\n"
        "Data Center Router\n"
        "   |\n"
        "Server"
    )

    explain(
        "A packet usually travels through multiple network devices before "
        "reaching its destination. The exact path can change depending on "
        "routing conditions, network policies, failures, congestion, and "
        "other factors."
    )


# ============================================================
# 7. MAC ADDRESSES AND ETHERNET
# ============================================================

def topic_mac_addresses():
    title("7. MAC ADDRESSES AND LOCAL NETWORKING")

    explain(
        "A MAC address is a link-layer address associated with a network "
        "interface. Ethernet and Wi-Fi networks use link-layer addressing "
        "to deliver frames within local network segments."
    )

    bullet("IP addresses operate at the network layer.")
    bullet("MAC addresses operate at the link layer.")
    bullet("A local device may have both an IP address and a MAC address.")

    subsection("ARP")

    explain(
        "In IPv4 local networking, ARP, or Address Resolution Protocol, "
        "helps discover the MAC address associated with an IPv4 address "
        "on the local network."
    )

    code_block(
        "Device A asks:\n"
        "\"Who has 192.168.1.1?\"\n\n"
        "Router replies:\n"
        "\"192.168.1.1 is at AA:BB:CC:DD:EE:FF\""
    )


# ============================================================
# 8. DNS
# ============================================================

def topic_dns():
    title("8. DNS: THE DOMAIN NAME SYSTEM")

    explain(
        "Humans generally use domain names such as example.com, while "
        "network communication ultimately requires IP addresses. DNS "
        "provides a distributed naming system that maps domain names to "
        "various types of records, including IP addresses."
    )

    subsection("Typical DNS lookup")

    code_block(
        "Browser\n"
        "   |\n"
        "   v\n"
        "Operating System / Local Cache\n"
        "   |\n"
        "   v\n"
        "Recursive DNS Resolver\n"
        "   |\n"
        "   v\n"
        "Root DNS Servers\n"
        "   |\n"
        "   v\n"
        "TLD DNS Servers\n"
        "   |\n"
        "   v\n"
        "Authoritative DNS Server\n"
        "   |\n"
        "   v\n"
        "IP Address"
    )

    subsection("Important DNS record types")

    records = {
        "A": "Maps a domain name to an IPv4 address.",
        "AAAA": "Maps a domain name to an IPv6 address.",
        "CNAME": "Provides an alias from one domain name to another.",
        "MX": "Specifies mail exchange servers.",
        "TXT": "Stores text information, commonly used for verification and email policies.",
        "NS": "Identifies authoritative name servers.",
        "SOA": "Contains administrative information about a DNS zone.",
    }

    for name, description in records.items():
        bullet(f"{name}: {description}")

    subsection("DNS caching")

    explain(
        "DNS responses can be cached. Caching reduces latency and reduces "
        "the number of queries that must reach authoritative infrastructure. "
        "The TTL, or Time To Live, associated with DNS records controls how "
        "long a cached answer may generally be considered valid."
    )


# ============================================================
# 9. DOMAIN NAMES
# ============================================================

def topic_domains():
    title("9. DOMAIN NAMES")

    explain(
        "A domain name is a human-readable name organized into a hierarchical "
        "namespace. Consider the example www.example.com."
    )

    code_block(
        "www.example.com\n"
        "│   │       │\n"
        "│   │       └── Top-level domain: com\n"
        "│   └────────── Registered domain: example\n"
        "└────────────── Host/subdomain label: www"
    )

    explain(
        "The exact legal and administrative structure of domains can be "
        "more complicated, especially with public suffixes and country-code "
        "domains, but the hierarchical DNS structure remains fundamental."
    )


# ============================================================
# 10. URL
# ============================================================

def topic_url():
    title("10. URL: UNIFORM RESOURCE LOCATOR")

    url = (
        "https://www.example.com:443/products/item?id=42"
        "&sort=price#reviews"
    )

    print("Example URL:")
    print(url)

    parsed = urllib.parse.urlparse(url)

    components = {
        "scheme": parsed.scheme,
        "hostname": parsed.hostname,
        "port": parsed.port,
        "path": parsed.path,
        "query": parsed.query,
        "fragment": parsed.fragment,
    }

    subsection("URL components")

    for key, value in components.items():
        print(f"{key:12}: {value}")

    explain(
        "The scheme describes the protocol family used to access the "
        "resource. The hostname identifies the destination. The path "
        "identifies a resource or route. The query contains parameters. "
        "The fragment identifies a location within the retrieved resource "
        "and is normally handled by the client rather than sent to the server "
        "as part of the HTTP request."
    )


# ============================================================
# 11. HTTP
# ============================================================

def topic_http():
    title("11. HTTP: HYPERTEXT TRANSFER PROTOCOL")

    explain(
        "HTTP is an application-layer protocol used for communication "
        "between clients and servers. It follows a request-response model."
    )

    code_block(
        "CLIENT                              SERVER\n"
        "  |                                   |\n"
        "  | ---- HTTP Request --------------> |\n"
        "  |                                   |\n"
        "  | <--- HTTP Response -------------- |\n"
        "  |                                   |"
    )

    subsection("HTTP request example")

    request = (
        "GET /index.html HTTP/1.1\n"
        "Host: example.com\n"
        "User-Agent: ExampleBrowser/1.0\n"
        "Accept: text/html\n"
        "Connection: keep-alive\n"
    )

    print(request)

    subsection("HTTP response example")

    response = (
        "HTTP/1.1 200 OK\n"
        "Content-Type: text/html\n"
        "Content-Length: 42\n"
        "Cache-Control: max-age=3600\n"
        "\n"
        "<html>Hello</html>"
    )

    print(response)


# ============================================================
# 12. HTTP METHODS
# ============================================================

def topic_http_methods():
    title("12. HTTP METHODS")

    methods = {
        "GET": "Retrieve a representation of a resource.",
        "POST": "Submit data, often causing creation or processing.",
        "PUT": "Replace or create a resource representation.",
        "PATCH": "Apply a partial modification to a resource.",
        "DELETE": "Request deletion of a resource.",
        "HEAD": "Retrieve response headers without the normal response body.",
        "OPTIONS": "Discover supported communication options.",
        "TRACE": "Diagnostic method that can reflect a request in some configurations.",
        "CONNECT": "Establish a tunnel, commonly associated with proxies.",
    }

    for method, description in methods.items():
        print(f"{method:8} -> {description}")

    explain(
        "HTTP methods have semantic meaning. GET is normally expected to be "
        "safe and idempotent. PUT and DELETE are generally idempotent in the "
        "HTTP semantic model. POST is not generally idempotent."
    )

    explain(
        "Idempotency means that performing the same operation multiple times "
        "has the same intended effect as performing it once, although the "
        "server may still record separate requests or produce different "
        "metadata."
    )


# ============================================================
# 13. STATUS CODES
# ============================================================

def topic_status_codes():
    title("13. HTTP STATUS CODES")

    statuses = {
        100: "Continue",
        200: "OK",
        201: "Created",
        202: "Accepted",
        204: "No Content",
        301: "Moved Permanently",
        302: "Found",
        304: "Not Modified",
        307: "Temporary Redirect",
        308: "Permanent Redirect",
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        405: "Method Not Allowed",
        409: "Conflict",
        410: "Gone",
        415: "Unsupported Media Type",
        422: "Unprocessable Content",
        429: "Too Many Requests",
        500: "Internal Server Error",
        501: "Not Implemented",
        502: "Bad Gateway",
        503: "Service Unavailable",
        504: "Gateway Timeout",
    }

    for status, description in statuses.items():
        print(f"{status}: {description}")

    subsection("Status code classes")

    bullet("1xx = informational")
    bullet("2xx = successful")
    bullet("3xx = redirection")
    bullet("4xx = client-side request error")
    bullet("5xx = server-side or upstream failure")


# ============================================================
# 14. HEADERS
# ============================================================

def topic_headers():
    title("14. HTTP HEADERS")

    explain(
        "Headers carry metadata about requests and responses. They influence "
        "content negotiation, caching, authentication, cookies, security "
        "policies, compression, connection behavior, and many other aspects "
        "of Web communication."
    )

    request_headers = {
        "Host": "Identifies the target host.",
        "Accept": "Indicates acceptable response media types.",
        "Accept-Encoding": "Indicates supported content encodings.",
        "Authorization": "Carries authentication credentials or tokens.",
        "Content-Type": "Describes the media type of the request body.",
        "Cookie": "Sends cookies previously associated with the domain.",
        "Origin": "Indicates the origin associated with a request.",
        "Referer": "May indicate the referring URL.",
    }

    response_headers = {
        "Content-Type": "Describes the response media type.",
        "Content-Length": "Indicates body length when applicable.",
        "Set-Cookie": "Instructs the browser to store a cookie.",
        "Cache-Control": "Controls caching behavior.",
        "ETag": "Provides an entity tag used for cache validation.",
        "Location": "Identifies a redirect or newly created resource location.",
        "Content-Encoding": "Describes content compression or encoding.",
        "Strict-Transport-Security": "Enforces HTTPS use through browser policy.",
    }

    subsection("Common request headers")

    for key, value in request_headers.items():
        print(f"{key:22} -> {value}")

    subsection("Common response headers")

    for key, value in response_headers.items():
        print(f"{key:30} -> {value}")


# ============================================================
# 15. COOKIES
# ============================================================

def topic_cookies():
    title("15. COOKIES")

    explain(
        "Cookies are small pieces of state associated with a domain and "
        "stored by the user agent. Servers can send cookies through the "
        "Set-Cookie response header. Browsers may subsequently send matching "
        "cookies through the Cookie request header."
    )

    cookie = {
        "name": "session_id",
        "value": "abc123",
        "Secure": True,
        "HttpOnly": True,
        "SameSite": "Lax",
        "Path": "/",
    }

    print(json.dumps(cookie, indent=4))

    subsection("Important cookie attributes")

    bullet("Secure: sends the cookie only over secure transport.")
    bullet("HttpOnly: prevents normal JavaScript access through document.cookie.")
    bullet("SameSite: controls cross-site cookie behavior.")
    bullet("Domain: controls applicable domains.")
    bullet("Path: controls applicable URL paths.")
    bullet("Expires/Max-Age: controls lifetime.")

    explain(
        "Cookies are often used for sessions, preferences, authentication "
        "state, and tracking. A cookie itself is not automatically an "
        "authentication mechanism. Its security depends on how the application "
        "uses and protects the value."
    )


# ============================================================
# 16. SESSIONS
# ============================================================

def topic_sessions():
    title("16. WEB SESSIONS")

    explain(
        "HTTP is fundamentally stateless: each request contains the information "
        "needed by the server to process that request. Applications often add "
        "stateful behavior using sessions."
    )

    code_block(
        "Browser                         Server\n"
        "   |                               |\n"
        "   | POST /login                   |\n"
        "   |------------------------------>|\n"
        "   |                               |\n"
        "   | Set-Cookie: session=XYZ       |\n"
        "   |<------------------------------|\n"
        "   |                               |\n"
        "   | GET /account                  |\n"
        "   | Cookie: session=XYZ           |\n"
        "   |------------------------------>|\n"
        "   |                               |\n"
        "   | Authenticated response        |\n"
        "   |<------------------------------|"
    )

    explain(
        "The server can maintain session state associated with the session "
        "identifier. The browser generally stores the identifier and sends it "
        "with subsequent requests."
    )


# ============================================================
# 17. AUTHENTICATION AND AUTHORIZATION
# ============================================================

def topic_authentication_authorization():
    title("17. AUTHENTICATION VS AUTHORIZATION")

    bullet("Authentication asks: Who are you?")
    bullet("Authorization asks: What are you allowed to do?")

    explain(
        "A user may authenticate successfully and still lack permission "
        "to access a particular resource."
    )

    code_block(
        "Login credentials\n"
        "      |\n"
        "      v\n"
        "Authentication\n"
        "      |\n"
        "      v\n"
        "Identity established\n"
        "      |\n"
        "      v\n"
        "Authorization check\n"
        "      |\n"
        "      v\n"
        "Resource access"
    )


# ============================================================
# 18. BROWSER ARCHITECTURE
# ============================================================

def topic_browser():
    title("18. BROWSER ARCHITECTURE")

    explain(
        "A modern browser is a complex software platform rather than a "
        "simple HTML viewer. It coordinates networking, rendering, JavaScript "
        "execution, graphics, storage, security isolation, media, and user input."
    )

    subsection("Conceptual browser components")

    components = [
        "User interface",
        "Browser process",
        "Renderer process",
        "JavaScript engine",
        "Networking subsystem",
        "Rendering engine",
        "Storage subsystem",
        "GPU-related components",
        "Security sandbox",
        "Cache",
        "Cookie store",
    ]

    for item in components:
        bullet(item)

    explain(
        "The exact process architecture differs between browsers, operating "
        "systems, and versions. Modern browsers commonly use process isolation "
        "to reduce the consequences of a compromised webpage or renderer."
    )


# ============================================================
# 19. HTML
# ============================================================

def topic_html():
    title("19. HTML")

    explain(
        "HTML, or HyperText Markup Language, provides the structural "
        "representation of Web documents. It describes elements such as "
        "headings, paragraphs, links, images, forms, tables, scripts, and "
        "other document structures."
    )

    html = """
<!doctype html>
<html>
<head>
    <title>Example</title>
</head>
<body>
    <h1>Hello Web</h1>
    <p>This is a paragraph.</p>
    <a href="/about">About</a>
</body>
</html>
"""

    print(html)

    explain(
        "The browser parses HTML into an internal tree structure called "
        "the DOM, or Document Object Model."
    )


# ============================================================
# 20. CSS
# ============================================================

def topic_css():
    title("20. CSS")

    explain(
        "CSS, or Cascading Style Sheets, controls presentation and layout. "
        "It can determine colors, fonts, spacing, dimensions, positioning, "
        "responsive behavior, animations, and many other visual properties."
    )

    css = """
body {
    font-family: sans-serif;
    margin: 2rem;
}

.card {
    padding: 1rem;
    border-radius: 8px;
}
"""

    print(css)

    explain(
        "The browser combines document structure with applicable CSS rules "
        "to determine how elements should be presented."
    )


# ============================================================
# 21. JAVASCRIPT
# ============================================================

def topic_javascript():
    title("21. JAVASCRIPT")

    explain(
        "JavaScript is a programming language widely used in browsers to "
        "provide dynamic behavior. It can manipulate the DOM, respond to "
        "events, communicate with servers, access browser APIs, and update "
        "application state."
    )

    javascript = """
const button = document.querySelector("#save");

button.addEventListener("click", async () => {
    const response = await fetch("/api/data");
    const data = await response.json();
    console.log(data);
});
"""

    print(javascript)

    explain(
        "Modern Web applications frequently use JavaScript to create "
        "interactive interfaces that communicate with backend APIs without "
        "requiring a full document navigation for every operation."
    )


# ============================================================
# 22. DOM
# ============================================================

def topic_dom():
    title("22. THE DOM")

    explain(
        "The Document Object Model is an object-oriented representation of "
        "the structure of an HTML document. JavaScript can inspect and modify "
        "this structure."
    )

    code_block(
        "Document\n"
        "└── html\n"
        "    ├── head\n"
        "    │   └── title\n"
        "    └── body\n"
        "        ├── h1\n"
        "        └── p"
    )

    explain(
        "When JavaScript modifies the DOM, the browser may need to recalculate "
        "styles, layout, painting, and compositing depending on what changed."
    )


# ============================================================
# 23. BROWSER EVENTS
# ============================================================

def topic_browser_events():
    title("23. BROWSER EVENTS")

    explain(
        "Browsers expose events representing user interaction and other "
        "activities. JavaScript can register handlers for these events."
    )

    events = [
        "click",
        "keydown",
        "keyup",
        "input",
        "submit",
        "load",
        "DOMContentLoaded",
        "scroll",
        "resize",
        "pointerdown",
        "pointerup",
    ]

    for event in events:
        bullet(event)


# ============================================================
# 24. API
# ============================================================

def topic_api():
    title("24. WEB APIs")

    explain(
        "An API, or Application Programming Interface, defines a way for "
        "software components to communicate. A Web API commonly exposes "
        "HTTP endpoints that clients can call."
    )

    code_block(
        "GET /api/users/42\n\n"
        "Response:\n"
        "{\n"
        "    \"id\": 42,\n"
        "    \"name\": \"Example User\"\n"
        "}"
    )

    explain(
        "The browser does not need to know how the server internally retrieves "
        "the user. It only needs to understand the API contract."
    )


# ============================================================
# 25. JSON
# ============================================================

def topic_json():
    title("25. JSON")

    explain(
        "JSON, or JavaScript Object Notation, is a text-based data interchange "
        "format widely used by Web APIs."
    )

    data = {
        "user_id": 42,
        "name": "Example User",
        "active": True,
        "roles": ["reader", "editor"],
        "profile": {
            "country": "India"
        }
    }

    print(json.dumps(data, indent=4))

    explain(
        "JSON supports objects, arrays, strings, numbers, booleans, and null. "
        "It is independent of JavaScript even though its syntax originated "
        "from JavaScript object notation."
    )


# ============================================================
# 26. REST
# ============================================================

def topic_rest():
    title("26. REST AND RESOURCE-ORIENTED APIs")

    explain(
        "REST, or Representational State Transfer, is an architectural style "
        "for distributed systems. RESTful API design commonly uses HTTP "
        "methods and resource-oriented URLs."
    )

    examples = [
        ("GET", "/users", "Retrieve users"),
        ("GET", "/users/42", "Retrieve user 42"),
        ("POST", "/users", "Create a user"),
        ("PATCH", "/users/42", "Modify user 42"),
        ("DELETE", "/users/42", "Delete user 42"),
    ]

    for method, path, meaning in examples:
        print(f"{method:7} {path:15} -> {meaning}")

    explain(
        "Not every HTTP API is RESTful, and using HTTP does not automatically "
        "make an API RESTful."
    )


# ============================================================
# 27. TCP
# ============================================================

def topic_tcp():
    title("27. TCP")

    explain(
        "Transmission Control Protocol provides a reliable, ordered byte "
        "stream between endpoints. It includes mechanisms for connection "
        "establishment, acknowledgements, retransmission, flow control, "
        "and congestion control."
    )

    subsection("Conceptual TCP connection establishment")

    code_block(
        "Client                         Server\n"
        "  |                              |\n"
        "  | -------- SYN --------------> |\n"
        "  | <------ SYN + ACK ----------- |\n"
        "  | -------- ACK --------------> |\n"
        "  |                              |\n"
        "  |      Connection ready        |"
    )

    explain(
        "This is commonly known as the TCP three-way handshake. HTTPS using "
        "traditional TCP-based HTTP versions typically involves TCP connection "
        "establishment before the encrypted application exchange."
    )


# ============================================================
# 28. UDP
# ============================================================

def topic_udp():
    title("28. UDP")

    explain(
        "User Datagram Protocol provides a lightweight datagram transport "
        "mechanism without TCP's built-in reliability and connection semantics."
    )

    bullet("Low protocol overhead.")
    bullet("No TCP-style connection establishment.")
    bullet("No built-in retransmission mechanism.")
    bullet("No guarantee of delivery.")
    bullet("No guarantee of ordering.")

    explain(
        "Applications can build their own reliability, ordering, congestion "
        "control, and other behavior over UDP. QUIC is an important modern "
        "example of this approach."
    )


# ============================================================
# 29. TLS
# ============================================================

def topic_tls():
    title("29. TLS AND HTTPS")

    explain(
        "HTTPS is HTTP carried over a secure transport using TLS, or "
        "Transport Layer Security. TLS provides encryption, integrity "
        "protection, and server authentication through certificates."
    )

    code_block(
        "Browser\n"
        "   |\n"
        "   | TLS ClientHello\n"
        "   v\n"
        "Server\n"
        "   |\n"
        "   | ServerHello + certificate + key exchange data\n"
        "   v\n"
        "Secure session established\n"
        "   |\n"
        "   v\n"
        "Encrypted HTTP traffic"
    )

    explain(
        "TLS uses asymmetric cryptographic mechanisms during establishment "
        "and symmetric cryptography for efficient bulk data protection. "
        "The exact handshake depends on the TLS version and negotiated "
        "cryptographic parameters."
    )


# ============================================================
# 30. CRYPTOGRAPHY
# ============================================================

def topic_cryptography():
    title("30. BASIC WEB CRYPTOGRAPHY")

    subsection("Symmetric encryption")

    explain(
        "Symmetric encryption uses the same secret key, or related symmetric "
        "key material, for encryption and decryption."
    )

    subsection("Asymmetric cryptography")

    explain(
        "Asymmetric cryptography uses mathematically related public and "
        "private keys. The public key can be distributed while the private "
        "key must remain protected."
    )

    subsection("Hashing")

    text = "The Web uses many forms of hashing for integrity, identifiers, "
    "password processing systems, and other purposes."

    explain(text)

    sample = "web-security"
    digest = hashlib.sha256(sample.encode()).hexdigest()

    print("Input :", sample)
    print("SHA-256:", digest)

    explain(
        "A cryptographic hash is designed to produce a fixed-size digest "
        "from input data. Hashing is not the same thing as encryption because "
        "a secure hash is not intended to provide reversible encryption."
    )


# ============================================================
# 31. HTTP/1.1
# ============================================================

def topic_http11():
    title("31. HTTP/1.1")

    explain(
        "HTTP/1.1 standardized persistent connections and a number of "
        "mechanisms that made Web communication more efficient than earlier "
        "HTTP usage patterns."
    )

    bullet("Persistent connections.")
    bullet("Host header.")
    bullet("Chunked transfer encoding.")
    bullet("Cache control mechanisms.")
    bullet("Range requests.")
    bullet("Content negotiation.")

    explain(
        "HTTP/1.1 uses textual request and response messages. Historically, "
        "multiple requests could suffer from head-of-line blocking at the "
        "HTTP layer when requests were serialized or constrained by connection "
        "behavior."
    )


# ============================================================
# 32. HTTP/2
# ============================================================

def topic_http2():
    title("32. HTTP/2")

    explain(
        "HTTP/2 introduced a binary framing layer and multiplexing of multiple "
        "streams over a single connection. This can reduce the need for "
        "multiple parallel TCP connections."
    )

    bullet("Binary framing.")
    bullet("Multiplexed streams.")
    bullet("Header compression through HPACK.")
    bullet("Stream prioritization mechanisms.")
    bullet("One TCP connection can carry multiple HTTP streams.")

    explain(
        "HTTP/2 improves application-layer multiplexing, but because it "
        "normally runs over TCP, packet loss can still produce transport-level "
        "head-of-line blocking."
    )


# ============================================================
# 33. HTTP/3 AND QUIC
# ============================================================

def topic_http3():
    title("33. HTTP/3 AND QUIC")

    explain(
        "HTTP/3 uses QUIC as its transport. QUIC is implemented over UDP and "
        "provides reliable, encrypted, multiplexed streams with transport "
        "features designed for modern Internet communication."
    )

    bullet("HTTP/3 runs over QUIC.")
    bullet("QUIC runs over UDP.")
    bullet("QUIC integrates TLS 1.3 handshake mechanisms.")
    bullet("Independent streams reduce cross-stream head-of-line blocking.")
    bullet("Connection migration can help maintain connections across network changes.")

    code_block(
        "HTTP/3\n"
        "   |\n"
        "QUIC\n"
        "   |\n"
        "UDP\n"
        "   |\n"
        "IP\n"
        "   |\n"
        "Network"
    )


# ============================================================
# 34. CACHE
# ============================================================

def topic_caching():
    title("34. WEB CACHING")

    explain(
        "Caching stores previously obtained data so that future requests "
        "can be served more quickly or without contacting the original "
        "application server."
    )

    code_block(
        "Browser\n"
        "  |\n"
        "  v\n"
        "Browser Cache\n"
        "  |\n"
        "  v\n"
        "CDN Cache\n"
        "  |\n"
        "  v\n"
        "Reverse Proxy Cache\n"
        "  |\n"
        "  v\n"
        "Application Server"
    )

    subsection("Cache-Control")

    examples = [
        "Cache-Control: public, max-age=3600",
        "Cache-Control: private, max-age=600",
        "Cache-Control: no-cache",
        "Cache-Control: no-store",
        "Cache-Control: must-revalidate",
    ]

    for item in examples:
        bullet(item)

    explain(
        "no-cache does not literally mean that the response cannot be stored. "
        "It generally means that a stored response must be validated before "
        "reuse. no-store has stronger semantics and instructs caches not to "
        "store the response."
    )


# ============================================================
# 35. ETAG
# ============================================================

def topic_etag():
    title("35. ETAG AND CONDITIONAL REQUESTS")

    explain(
        "An ETag is an identifier representing a particular representation "
        "of a resource. A client can send If-None-Match in a later request "
        "to ask whether its cached representation is still valid."
    )

    code_block(
        "First response:\n"
        "HTTP/1.1 200 OK\n"
        "ETag: \"abc123\"\n\n"
        "Later request:\n"
        "If-None-Match: \"abc123\"\n\n"
        "If unchanged:\n"
        "HTTP/1.1 304 Not Modified"
    )


# ============================================================
# 36. CDN
# ============================================================

def topic_cdn():
    title("36. CDN: CONTENT DELIVERY NETWORK")

    explain(
        "A CDN is a geographically distributed network of servers designed "
        "to deliver content closer to users. Static assets such as images, "
        "JavaScript files, stylesheets, fonts, and videos are common CDN "
        "workloads."
    )

    code_block(
        "                 Origin Server\n"
        "                       |\n"
        "             +---------+---------+\n"
        "             |         |         |\n"
        "             v         v         v\n"
        "          CDN POP    CDN POP    CDN POP\n"
        "             |         |         |\n"
        "             v         v         v\n"
        "          Users     Users     Users"
    )

    explain(
        "CDNs can reduce latency, reduce origin bandwidth usage, absorb "
        "traffic spikes, and provide additional security and traffic management "
        "capabilities."
    )


# ============================================================
# 37. REVERSE PROXY
# ============================================================

def topic_reverse_proxy():
    title("37. REVERSE PROXY")

    explain(
        "A reverse proxy sits in front of application servers. Clients "
        "communicate with the reverse proxy rather than directly with the "
        "internal application servers."
    )

    code_block(
        "Internet\n"
        "   |\n"
        "   v\n"
        "Reverse Proxy\n"
        "   |\n"
        "   +----> Application Server 1\n"
        "   |\n"
        "   +----> Application Server 2\n"
        "   |\n"
        "   +----> Application Server 3"
    )

    bullet("TLS termination.")
    bullet("Routing.")
    bullet("Caching.")
    bullet("Compression.")
    bullet("Rate limiting.")
    bullet("Load distribution.")
    bullet("Access control.")

    explain(
        "A reverse proxy can also hide internal server topology from external "
        "clients."
    )


# ============================================================
# 38. LOAD BALANCER
# ============================================================

def topic_load_balancer():
    title("38. LOAD BALANCERS")

    explain(
        "A load balancer distributes traffic across multiple backend "
        "instances. The goal can be improved capacity, availability, "
        "fault tolerance, and operational flexibility."
    )

    algorithms = {
        "Round Robin": "Distributes requests sequentially.",
        "Weighted Round Robin": "Distributes traffic according to assigned weights.",
        "Least Connections": "Prefers servers with fewer active connections.",
        "IP Hash": "Uses client address hashing to influence backend selection.",
        "Random": "Selects a backend using a random strategy.",
    }

    for name, description in algorithms.items():
        bullet(f"{name}: {description}")


# ============================================================
# 39. WEB SERVER
# ============================================================

def topic_web_server():
    title("39. WEB SERVERS")

    explain(
        "A Web server is software that listens for network requests and "
        "returns Web resources or forwards requests to application components."
    )

    bullet("Static file serving.")
    bullet("HTTP protocol handling.")
    bullet("TLS support.")
    bullet("Request routing.")
    bullet("Logging.")
    bullet("Compression.")
    bullet("Connection management.")

    explain(
        "A Web server and an application server are related but conceptually "
        "different. A Web server can serve static resources directly while "
        "an application server runs application logic."
    )


# ============================================================
# 40. APPLICATION SERVER
# ============================================================

def topic_application_server():
    title("40. APPLICATION SERVERS")

    explain(
        "An application server executes business logic. It may validate "
        "requests, authenticate users, perform authorization checks, query "
        "databases, communicate with other services, and construct responses."
    )

    code_block(
        "HTTP Request\n"
        "     |\n"
        "     v\n"
        "Routing\n"
        "     |\n"
        "     v\n"
        "Authentication\n"
        "     |\n"
        "     v\n"
        "Business Logic\n"
        "     |\n"
        "     +----> Database\n"
        "     |\n"
        "     +----> External API\n"
        "     |\n"
        "     v\n"
        "HTTP Response"
    )


# ============================================================
# 41. DATABASE
# ============================================================

def topic_database():
    title("41. DATABASES IN WEB APPLICATIONS")

    explain(
        "Web applications commonly persist structured application state "
        "in databases. A request may cause the application server to execute "
        "one or more database operations."
    )

    subsection("Relational databases")

    bullet("Tables.")
    bullet("Rows.")
    bullet("Columns.")
    bullet("Primary keys.")
    bullet("Foreign keys.")
    bullet("Indexes.")
    bullet("Transactions.")
    bullet("Constraints.")

    subsection("Non-relational databases")

    bullet("Document databases.")
    bullet("Key-value stores.")
    bullet("Wide-column databases.")
    bullet("Graph databases.")

    explain(
        "The database choice depends on the application's access patterns, "
        "consistency requirements, data model, scale, operational environment, "
        "and other engineering constraints."
    )


# ============================================================
# 42. DATABASE QUERY LIFECYCLE
# ============================================================

def topic_database_request():
    title("42. A DATABASE-BACKED WEB REQUEST")

    code_block(
        "Browser\n"
        "   |\n"
        "   | GET /users/42\n"
        "   v\n"
        "Web Server\n"
        "   |\n"
        "   v\n"
        "Application Server\n"
        "   |\n"
        "   | SELECT ...\n"
        "   v\n"
        "Database\n"
        "   |\n"
        "   | Row data\n"
        "   v\n"
        "Application Server\n"
        "   |\n"
        "   | JSON\n"
        "   v\n"
        "Browser"
    )

    explain(
        "The actual path may include connection pools, caches, service "
        "boundaries, database replicas, authorization layers, queues, "
        "observability systems, and many other components."
    )


# ============================================================
# 43. JWT
# ============================================================

def topic_jwt():
    title("43. JSON WEB TOKENS")

    explain(
        "A JSON Web Token, or JWT, is a compact representation containing "
        "claims. JWTs are commonly used in authentication and authorization "
        "systems, although they are not inherently an authentication protocol."
    )

    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": "42",
        "role": "user",
        "iat": 1700000000,
    }

    def encode_part(value):
        raw = json.dumps(value, separators=(",", ":")).encode()
        return base64.urlsafe_b64encode(raw).decode().rstrip("=")

    encoded_header = encode_part(header)
    encoded_payload = encode_part(payload)

    print("Header :", encoded_header)
    print("Payload:", encoded_payload)
    print("Signature: cryptographic verification data")

    explain(
        "JWTs can be signed so that a receiver can verify that the token "
        "was produced by a trusted party and has not been altered. A signed "
        "JWT does not automatically hide its payload. Encryption requires "
        "appropriate encryption mechanisms."
    )


# ============================================================
# 44. CORS
# ============================================================

def topic_cors():
    title("44. CORS")

    explain(
        "Cross-Origin Resource Sharing is a browser security mechanism that "
        "allows a server to declare which origins may access certain resources "
        "from browser-based cross-origin requests."
    )

    code_block(
        "Browser Origin:\n"
        "https://app.example.com\n\n"
        "Request:\n"
        "GET https://api.example.com/data\n\n"
        "Server response:\n"
        "Access-Control-Allow-Origin: https://app.example.com"
    )

    explain(
        "CORS is primarily enforced by browsers. Server-to-server HTTP "
        "requests are not restricted by the browser's CORS enforcement."
    )


# ============================================================
# 45. SAME ORIGIN POLICY
# ============================================================

def topic_same_origin():
    title("45. SAME-ORIGIN POLICY")

    explain(
        "The same-origin policy is a fundamental browser security mechanism. "
        "An origin is defined by scheme, host, and port."
    )

    origins = [
        "https://example.com",
        "http://example.com",
        "https://example.com:8443",
        "https://api.example.com",
    ]

    for origin in origins:
        parsed = urllib.parse.urlparse(origin)
        print(
            f"{origin:35} -> "
            f"scheme={parsed.scheme}, host={parsed.hostname}, port={parsed.port}"
        )

    explain(
        "Two URLs have the same origin only when their scheme, host, and port "
        "match according to the origin rules. A different subdomain is a "
        "different origin."
    )


# ============================================================
# 46. WEBSOCKETS
# ============================================================

def topic_websockets():
    title("46. WEBSOCKETS")

    explain(
        "WebSockets provide a persistent, bidirectional communication channel "
        "between a browser and a server. Unlike conventional request-response "
        "communication, either side can send messages after the connection "
        "has been established."
    )

    code_block(
        "Browser                         Server\n"
        "  |                               |\n"
        "  | HTTP Upgrade request -------->|\n"
        "  |<-------- 101 Switching -------|\n"
        "  |                               |\n"
        "  |<====== WebSocket data =======>|\n"
        "  |<====== WebSocket data =======>|\n"
        "  |                               |"
    )

    bullet("Chat applications.")
    bullet("Live dashboards.")
    bullet("Collaborative applications.")
    bullet("Multiplayer communication.")
    bullet("Real-time notifications.")


# ============================================================
# 47. SERVER-SENT EVENTS
# ============================================================

def topic_sse():
    title("47. SERVER-SENT EVENTS")

    explain(
        "Server-Sent Events provide a mechanism for a server to push a stream "
        "of events to a browser over a long-lived HTTP connection. The channel "
        "is server-to-client rather than fully bidirectional."
    )

    bullet("Useful for streaming updates.")
    bullet("Uses HTTP.")
    bullet("Browser provides EventSource API.")
    bullet("Server sends event-stream data.")


# ============================================================
# 48. WEBHOOKS
# ============================================================

def topic_webhooks():
    title("48. WEBHOOKS")

    explain(
        "A webhook allows one system to notify another system by making an "
        "HTTP request when an event occurs."
    )

    code_block(
        "Payment System\n"
        "     |\n"
        "     | POST /webhook\n"
        "     v\n"
        "Merchant Server\n"
        "     |\n"
        "     v\n"
        "Process event"
    )

    explain(
        "Webhook endpoints should generally verify authenticity, handle "
        "retries, tolerate duplicate deliveries where appropriate, and "
        "respond within the expected time limits."
    )


# ============================================================
# 49. PROXIES
# ============================================================

def topic_proxies():
    title("49. PROXIES")

    explain(
        "A forward proxy acts on behalf of clients. A reverse proxy acts "
        "on behalf of servers."
    )

    code_block(
        "Forward proxy:\n"
        "Client -> Proxy -> Internet\n\n"
        "Reverse proxy:\n"
        "Internet -> Reverse Proxy -> Server"
    )

    bullet("Forward proxy controls or represents client traffic.")
    bullet("Reverse proxy controls or represents server-side infrastructure.")


# ============================================================
# 50. NAT
# ============================================================

def topic_nat():
    title("50. NETWORK ADDRESS TRANSLATION")

    explain(
        "NAT allows private network addresses to communicate through public "
        "addresses. A home router commonly performs NAT for devices inside "
        "the local network."
    )

    code_block(
        "Laptop\n"
        "192.168.1.10:50000\n"
        "        |\n"
        "        v\n"
        "Home Router\n"
        "Public IP: 198.51.100.10\n"
        "        |\n"
        "        v\n"
        "Internet Server\n"
        "203.0.113.20:443"
    )

    explain(
        "Port translation can allow many private devices to share one public "
        "IPv4 address by tracking mappings between internal and external "
        "address-port combinations."
    )


# ============================================================
# 51. DHCP
# ============================================================

def topic_dhcp():
    title("51. DHCP")

    explain(
        "Dynamic Host Configuration Protocol allows devices to obtain network "
        "configuration automatically."
    )

    bullet("IP address.")
    bullet("Subnet mask or prefix information.")
    bullet("Default gateway.")
    bullet("DNS server information.")
    bullet("Lease information.")

    subsection("Conceptual DHCP sequence")

    code_block(
        "Client -> DHCP Discover\n"
        "Server -> DHCP Offer\n"
        "Client -> DHCP Request\n"
        "Server -> DHCP Acknowledgement"
    )


# ============================================================
# 52. SUBNETS
# ============================================================

def topic_subnets():
    title("52. SUBNETTING")

    explain(
        "A subnet divides an IP address space into a network prefix and a "
        "host portion. CIDR notation expresses the prefix length."
    )

    examples = [
        "192.168.1.0/24",
        "10.0.0.0/8",
        "172.16.0.0/16",
        "2001:db8::/32",
    ]

    for network in examples:
        try:
            net = ipaddress.ip_network(network, strict=False)
            print(
                f"{network:22} -> "
                f"network={net.network_address}, "
                f"prefix={net.prefixlen}"
            )
        except ValueError as error:
            print(network, error)

    explain(
        "Subnetting is important because routing and local network decisions "
        "depend on determining whether an address belongs to a directly "
        "connected network or requires forwarding through a router."
    )


# ============================================================
# 53. FIREWALLS
# ============================================================

def topic_firewalls():
    title("53. FIREWALLS")

    explain(
        "A firewall controls network traffic according to configured rules. "
        "Rules may consider addresses, ports, protocols, connection state, "
        "application information, or other attributes depending on the "
        "firewall architecture."
    )

    rules = [
        ("TCP", 22, "ALLOW", "Administration network"),
        ("TCP", 80, "ALLOW", "HTTP"),
        ("TCP", 443, "ALLOW", "HTTPS"),
        ("TCP", 3306, "DENY", "Database should not be public"),
    ]

    for protocol, port, action, reason in rules:
        print(f"{protocol:5} {port:5} {action:7} {reason}")


# ============================================================
# 54. NETWORK LAYERS
# ============================================================

def topic_network_layers():
    title("54. NETWORK LAYERS")

    subsection("OSI conceptual model")

    osi = [
        "7. Application",
        "6. Presentation",
        "5. Session",
        "4. Transport",
        "3. Network",
        "2. Data Link",
        "1. Physical",
    ]

    for layer in osi:
        print(layer)

    subsection("TCP/IP model")

    tcp_ip = [
        "Application",
        "Transport",
        "Internet",
        "Link",
    ]

    for layer in tcp_ip:
        print("  " + layer)

    explain(
        "The OSI model is primarily a conceptual framework. Real Internet "
        "protocol stacks do not always map perfectly onto its seven layers. "
        "The TCP/IP model is more closely aligned with the protocols used "
        "by the Internet."
    )


# ============================================================
# 55. ENCAPSULATION
# ============================================================

def topic_encapsulation():
    title("55. NETWORK ENCAPSULATION")

    explain(
        "As application data moves down the networking stack, different "
        "layers add their own metadata. At the destination, the receiving "
        "stack processes the information in the reverse direction."
    )

    code_block(
        "Application data\n"
        "      ↓\n"
        "TCP segment\n"
        "      ↓\n"
        "IP packet\n"
        "      ↓\n"
        "Ethernet/Wi-Fi frame\n"
        "      ↓\n"
        "Physical transmission"
    )

    explain(
        "The exact terminology and boundaries differ across protocols, "
        "but encapsulation is fundamental to understanding how application "
        "communication becomes network traffic."
    )


# ============================================================
# 56. BROWSER NAVIGATION LIFECYCLE
# ============================================================

def topic_navigation_lifecycle():
    title("56. WHAT HAPPENS WHEN YOU ENTER A URL?")

    steps = [
        "The browser parses the URL.",
        "The browser determines whether an existing cached result can help.",
        "The browser determines the destination host.",
        "DNS resolution may be required.",
        "The browser establishes network connectivity.",
        "TCP may be established for HTTP/1.1 or HTTP/2.",
        "TLS may be negotiated for HTTPS.",
        "HTTP request is transmitted.",
        "Server-side infrastructure processes the request.",
        "HTTP response is returned.",
        "Browser processes response headers.",
        "HTML is parsed.",
        "Additional resources are discovered.",
        "CSS is parsed.",
        "JavaScript is executed.",
        "DOM and CSSOM information are used in rendering.",
        "Layout and painting occur.",
        "The page becomes visible and interactive.",
    ]

    for index, step in enumerate(steps, 1):
        print(f"{index:2}. {step}")

    explain(
        "This is a conceptual sequence rather than a strict list of events "
        "that always occur one after another. Modern browsers perform many "
        "operations concurrently and may reuse existing connections, caches, "
        "DNS results, and other resources."
    )


# ============================================================
# 57. DNS REQUEST SIMULATION
# ============================================================

@dataclass
class DNSRecord:
    name: str
    record_type: str
    value: str
    ttl: int


class SimpleDNSCache:
    def __init__(self):
        self.records: Dict[str, tuple] = {}

    def put(self, record: DNSRecord):
        expiry = time.time() + record.ttl
        key = (record.name.lower(), record.record_type.upper())
        self.records[key] = (record.value, expiry)

    def get(self, name: str, record_type: str):
        key = (name.lower(), record_type.upper())
        item = self.records.get(key)

        if not item:
            return None

        value, expiry = item

        if time.time() >= expiry:
            del self.records[key]
            return None

        return value


def topic_dns_simulation():
    title("57. DNS CACHE SIMULATION")

    cache = SimpleDNSCache()

    record = DNSRecord(
        name="example.com",
        record_type="A",
        value="93.184.216.34",
        ttl=60,
    )

    cache.put(record)

    print("First lookup:")
    print("Resolver answer:", cache.get("example.com", "A"))

    print("\nSecond lookup:")
    print("Cached answer:", cache.get("example.com", "A"))

    explain(
        "A real recursive DNS resolver performs much more complex work, "
        "including cache management, delegation processing, DNSSEC validation "
        "when configured, transport handling, and communication with "
        "authoritative infrastructure."
    )


# ============================================================
# 58. HTTP REQUEST SIMULATION
# ============================================================

@dataclass
class HTTPRequest:
    method: str
    path: str
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[str] = None

    def serialize(self):
        lines = [
            f"{self.method} {self.path} HTTP/1.1"
        ]

        for key, value in self.headers.items():
            lines.append(f"{key}: {value}")

        lines.append("")

        if self.body:
            lines.append(self.body)

        return "\n".join(lines)


@dataclass
class HTTPResponse:
    status_code: int
    reason: str
    headers: Dict[str, str] = field(default_factory=dict)
    body: str = ""

    def serialize(self):
        lines = [
            f"HTTP/1.1 {self.status_code} {self.reason}"
        ]

        for key, value in self.headers.items():
            lines.append(f"{key}: {value}")

        lines.append("")
        lines.append(self.body)

        return "\n".join(lines)


def topic_http_simulation():
    title("58. HTTP REQUEST/RESPONSE SIMULATION")

    request = HTTPRequest(
        method="GET",
        path="/products/42",
        headers={
            "Host": "shop.example.com",
            "Accept": "application/json",
            "User-Agent": "StudyBrowser/1.0",
        },
    )

    response = HTTPResponse(
        status_code=200,
        reason="OK",
        headers={
            "Content-Type": "application/json",
            "Cache-Control": "private, max-age=60",
        },
        body=json.dumps(
            {
                "id": 42,
                "name": "Example Product",
                "available": True,
            },
            indent=2,
        ),
    )

    subsection("Request")
    print(request.serialize())

    subsection("Response")
    print(response.serialize())


# ============================================================
# 59. FORM SUBMISSION
# ============================================================

def topic_form_submission():
    title("59. WHAT HAPPENS WHEN A FORM IS SUBMITTED?")

    explain(
        "A browser form collects user input and can submit it to a server. "
        "The request may use GET or POST depending on the form configuration "
        "and application design."
    )

    code_block(
        "User enters data\n"
        "       |\n"
        "       v\n"
        "Browser validates client-side rules\n"
        "       |\n"
        "       v\n"
        "HTTP request\n"
        "       |\n"
        "       v\n"
        "Server validates again\n"
        "       |\n"
        "       v\n"
        "Business logic\n"
        "       |\n"
        "       v\n"
        "Database / service\n"
        "       |\n"
        "       v\n"
        "Response"
    )

    explain(
        "Client-side validation improves user experience but cannot be "
        "treated as a security boundary. The server must validate data "
        "independently."
    )


# ============================================================
# 60. FILE DOWNLOAD
# ============================================================

def topic_file_download():
    title("60. FILE DOWNLOADS")

    explain(
        "A file download is generally an HTTP response containing the file "
        "data. Response headers can tell the browser how the data should "
        "be interpreted."
    )

    code_block(
        "HTTP/1.1 200 OK\n"
        "Content-Type: application/pdf\n"
        "Content-Disposition: attachment; filename=\"report.pdf\"\n"
        "Content-Length: 123456\n"
        "\n"
        "[binary file data]"
    )

    explain(
        "The browser may display the file inline or treat it as a download "
        "depending on response headers, browser behavior, user preferences, "
        "and file type."
    )


# ============================================================
# 61. IMAGE LOADING
# ============================================================

def topic_image_loading():
    title("61. IMAGE LOADING")

    explain(
        "When HTML references an image, the browser may discover that resource "
        "during HTML parsing and initiate another network request."
    )

    code_block(
        "HTML\n"
        " |\n"
        " +----> GET /index.html\n"
        " |\n"
        " +----> GET /styles.css\n"
        " |\n"
        " +----> GET /app.js\n"
        " |\n"
        " +----> GET /hero.webp\n"
        " |\n"
        " +----> GET /logo.svg"
    )

    explain(
        "Resource loading can happen concurrently. The browser also applies "
        "priority decisions, caching, connection reuse, lazy loading, and "
        "other optimization strategies."
    )


# ============================================================
# 62. VIDEO STREAMING
# ============================================================

def topic_video_streaming():
    title("62. VIDEO STREAMING")

    explain(
        "Large media files are often delivered in segments rather than as "
        "one monolithic download. Adaptive streaming systems can provide "
        "multiple representations at different bitrates."
    )

    code_block(
        "Manifest\n"
        "  |\n"
        "  +--> Low bitrate segments\n"
        "  |\n"
        "  +--> Medium bitrate segments\n"
        "  |\n"
        "  +--> High bitrate segments\n"
        "             |\n"
        "             v\n"
        "       Browser media player"
    )

    explain(
        "The client can choose representations based on network conditions, "
        "device capability, buffer state, and other factors."
    )


# ============================================================
# 63. AUTHENTICATION FLOW
# ============================================================

def topic_auth_flow():
    title("63. TYPICAL LOGIN FLOW")

    code_block(
        "1. User submits credentials\n"
        "          |\n"
        "          v\n"
        "2. HTTPS request\n"
        "          |\n"
        "          v\n"
        "3. Server validates credentials\n"
        "          |\n"
        "          v\n"
        "4. Authentication state created\n"
        "          |\n"
        "          v\n"
        "5. Cookie/token returned\n"
        "          |\n"
        "          v\n"
        "6. Browser stores authentication state\n"
        "          |\n"
        "          v\n"
        "7. Future requests carry authentication information"
    )

    explain(
        "Real authentication systems may involve password hashing, "
        "multi-factor authentication, identity providers, OAuth or OpenID "
        "Connect, token rotation, session expiration, device management, "
        "risk detection, and additional security controls."
    )


# ============================================================
# 64. API REQUEST LIFECYCLE
# ============================================================

def topic_api_lifecycle():
    title("64. API REQUEST LIFECYCLE")

    code_block(
        "Client\n"
        " |\n"
        " | HTTPS\n"
        " v\n"
        "Load Balancer\n"
        " |\n"
        " v\n"
        "Reverse Proxy\n"
        " |\n"
        " v\n"
        "API Server\n"
        " |\n"
        " +--> Authentication\n"
        " |\n"
        " +--> Authorization\n"
        " |\n"
        " +--> Validation\n"
        " |\n"
        " +--> Business Logic\n"
        " |\n"
        " +--> Cache\n"
        " |\n"
        " +--> Database\n"
        " |\n"
        " v\n"
        "JSON Response\n"
        " |\n"
        " v\n"
        "Client"
    )


# ============================================================
# 65. WEB SECURITY
# ============================================================

def topic_security():
    title("65. WEB SECURITY")

    explain(
        "Web security protects users, applications, data, infrastructure, "
        "and communication channels against unauthorized access, manipulation, "
        "information disclosure, service disruption, and other threats."
    )

    subsection("Security principles")

    bullet("Confidentiality.")
    bullet("Integrity.")
    bullet("Availability.")
    bullet("Authentication.")
    bullet("Authorization.")
    bullet("Accountability.")
    bullet("Least privilege.")
    bullet("Defense in depth.")
    bullet("Secure defaults.")
    bullet("Input validation.")

    explain(
        "Security is not provided by HTTPS alone. HTTPS protects data in "
        "transit, but vulnerabilities in application logic, authentication, "
        "authorization, dependencies, configuration, or infrastructure can "
        "still compromise a Web application."
    )


# ============================================================
# 66. XSS
# ============================================================

def topic_xss():
    title("66. CROSS-SITE SCRIPTING")

    explain(
        "Cross-site scripting, or XSS, occurs when untrusted data is included "
        "in a page in a way that causes unintended script execution in a "
        "victim's browser."
    )

    subsection("Major categories")

    bullet("Stored XSS.")
    bullet("Reflected XSS.")
    bullet("DOM-based XSS.")

    explain(
        "Important defensive principles include context-aware output encoding, "
        "safe DOM APIs, appropriate content security policy, careful handling "
        "of untrusted HTML, and avoiding dangerous interpretation of user data "
        "as executable code."
    )


# ============================================================
# 67. SQL INJECTION
# ============================================================

def topic_sql_injection():
    title("67. SQL INJECTION")

    explain(
        "SQL injection occurs when untrusted input changes the intended "
        "structure of a database query."
    )

    subsection("Unsafe conceptual pattern")

    code_block(
        "query = \"SELECT * FROM users WHERE name = '\" + user_input + \"'\""
    )

    subsection("Safer pattern")

    code_block(
        "cursor.execute(\n"
        "    \"SELECT * FROM users WHERE name = %s\",\n"
        "    (user_input,)\n"
        ")"
    )

    explain(
        "Parameterized queries separate SQL instructions from user-provided "
        "data. They are one of the principal defenses against SQL injection."
    )


# ============================================================
# 68. CSRF
# ============================================================

def topic_csrf():
    title("68. CROSS-SITE REQUEST FORGERY")

    explain(
        "CSRF occurs when a user's browser is induced to make an unwanted "
        "state-changing request to a site where the browser already has "
        "relevant authentication state."
    )

    bullet("CSRF tokens.")
    bullet("SameSite cookies.")
    bullet("Origin checking.")
    bullet("Referer checking where appropriate.")
    bullet("Avoiding unsafe state changes through GET requests.")


# ============================================================
# 69. CLICKJACKING
# ============================================================

def topic_clickjacking():
    title("69. CLICKJACKING")

    explain(
        "Clickjacking involves misleading a user into interacting with "
        "a hidden or disguised interface element from another context."
    )

    bullet("Content-Security-Policy frame-ancestors.")
    bullet("X-Frame-Options in appropriate environments.")
    bullet("Careful UI security design.")


# ============================================================
# 70. DDoS
# ============================================================

def topic_ddos():
    title("70. DISTRIBUTED DENIAL OF SERVICE")

    explain(
        "A distributed denial-of-service attack attempts to make a service "
        "unavailable by overwhelming network, protocol, computational, or "
        "application resources."
    )

    bullet("Volumetric attacks.")
    bullet("Protocol-level attacks.")
    bullet("Application-layer attacks.")

    explain(
        "Mitigation may involve rate limiting, traffic filtering, CDN or "
        "edge protection, autoscaling, capacity planning, caching, and "
        "specialized DDoS mitigation infrastructure."
    )


# ============================================================
# 71. CERTIFICATES
# ============================================================

def topic_certificates():
    title("71. TLS CERTIFICATES")

    explain(
        "A TLS certificate binds a public key to an identity under a trust "
        "model based on certificate authorities. Browsers maintain trusted "
        "root certificates and validate certificate chains and other properties."
    )

    code_block(
        "Trusted Root CA\n"
        "      |\n"
        "      v\n"
        "Intermediate CA\n"
        "      |\n"
        "      v\n"
        "Website Certificate\n"
        "      |\n"
        "      v\n"
        "Website Public Key"
    )

    explain(
        "Certificate validation includes checks such as hostname matching, "
        "validity period, signature chain, and other policy constraints."
    )


# ============================================================
# 72. BROWSER STORAGE
# ============================================================

def topic_browser_storage():
    title("72. BROWSER STORAGE")

    storage = {
        "Cookies": "Small values associated with HTTP requests and browser state.",
        "LocalStorage": "Persistent key-value storage exposed to browser scripts.",
        "SessionStorage": "Key-value storage scoped to a browser tab/session context.",
        "IndexedDB": "Structured client-side database API.",
        "Cache Storage": "Storage used by service workers and related caching APIs.",
    }

    for name, description in storage.items():
        print(f"{name:18} -> {description}")

    explain(
        "These mechanisms have different security properties, lifetimes, "
        "access patterns, and browser integration. Sensitive information "
        "should not be placed in browser storage without considering the "
        "consequences of script compromise or other attacks."
    )


# ============================================================
# 73. SERVICE WORKERS
# ============================================================

def topic_service_workers():
    title("73. SERVICE WORKERS")

    explain(
        "A service worker is a browser-managed script that can operate "
        "between a Web application and network requests under defined "
        "security constraints."
    )

    bullet("Offline functionality.")
    bullet("Network request interception.")
    bullet("Caching strategies.")
    bullet("Background capabilities.")
    bullet("Push-related functionality in supported environments.")

    code_block(
        "Web Application\n"
        "      |\n"
        "      v\n"
        "Service Worker\n"
        "   |       |\n"
        "   |       +----> Cache\n"
        "   |\n"
        "   +-----------> Network"
    )


# ============================================================
# 74. PERFORMANCE
# ============================================================

def topic_performance():
    title("74. WEB PERFORMANCE")

    explain(
        "Web performance concerns how quickly and efficiently users can "
        "load, see, interact with, and use an application."
    )

    subsection("Major contributors")

    bullet("DNS latency.")
    bullet("Connection establishment.")
    bullet("TLS handshake.")
    bullet("Server processing time.")
    bullet("Network latency.")
    bullet("Response size.")
    bullet("JavaScript execution.")
    bullet("CSS processing.")
    bullet("Rendering work.")
    bullet("Image and font size.")
    bullet("Third-party scripts.")
    bullet("Cache effectiveness.")

    explain(
        "Performance is not simply bandwidth. A page with a small payload "
        "can still be slow because of latency, blocking work, server delays, "
        "rendering cost, or inefficient resource dependencies."
    )


# ============================================================
# 75. COMPRESSION
# ============================================================

def topic_compression():
    title("75. HTTP COMPRESSION")

    explain(
        "Compression reduces the number of bytes transferred over the network. "
        "Common content encodings include gzip and Brotli."
    )

    original = (
        "This is a repeated sentence. " * 100
    ).encode()

    import zlib

    compressed = zlib.compress(original)

    print("Original size :", len(original), "bytes")
    print("Compressed size:", len(compressed), "bytes")

    explain(
        "Compression is especially effective for repetitive text-based "
        "resources such as HTML, CSS, JavaScript, and JSON. Images and video "
        "often already use specialized compression."
    )


# ============================================================
# 76. CONTENT TYPES
# ============================================================

def topic_content_types():
    title("76. MIME TYPES")

    types = {
        "text/html": "HTML document",
        "text/css": "CSS stylesheet",
        "text/javascript": "JavaScript",
        "application/json": "JSON data",
        "application/pdf": "PDF document",
        "image/png": "PNG image",
        "image/jpeg": "JPEG image",
        "image/webp": "WebP image",
        "video/mp4": "MP4 video",
        "application/octet-stream": "Generic binary data",
    }

    for mime, meaning in types.items():
        print(f"{mime:35} -> {meaning}")

    explain(
        "The Content-Type header tells the recipient what media type is "
        "being represented. Correct content types are important for both "
        "functionality and security."
    )


# ============================================================
# 77. CONTENT NEGOTIATION
# ============================================================

def topic_content_negotiation():
    title("77. CONTENT NEGOTIATION")

    explain(
        "HTTP clients can communicate preferences for media types, languages, "
        "and content encodings. Servers may use these preferences when "
        "selecting a response representation."
    )

    code_block(
        "Accept: application/json\n"
        "Accept-Language: en-IN,en;q=0.9\n"
        "Accept-Encoding: br, gzip"
    )


# ============================================================
# 78. HTTP RANGE REQUESTS
# ============================================================

def topic_range_requests():
    title("78. HTTP RANGE REQUESTS")

    explain(
        "Range requests allow a client to request only a portion of a resource. "
        "They are useful for resumable downloads, media seeking, and large files."
    )

    code_block(
        "GET /large-file.zip HTTP/1.1\n"
        "Range: bytes=100000-199999"
    )

    explain(
        "A server that supports the requested range may respond with "
        "206 Partial Content and include information describing the returned "
        "range."
    )


# ============================================================
# 79. REQUEST LATENCY
# ============================================================

def topic_latency():
    title("79. LATENCY")

    explain(
        "Latency is the time required for an operation or communication step "
        "to occur. Web request latency can include DNS lookup time, connection "
        "establishment, TLS negotiation, network propagation, server processing, "
        "database operations, and response transmission."
    )

    components = {
        "DNS": 15,
        "TCP": 20,
        "TLS": 25,
        "Server": 40,
        "Network transfer": 30,
    }

    total = sum(components.values())

    for name, milliseconds in components.items():
        print(f"{name:20}: {milliseconds:4} ms")

    print(f"\nConceptual total: {total} ms")

    explain(
        "These values are illustrative rather than measurements of a real "
        "network. They demonstrate that total latency can be the sum of "
        "multiple independent stages."
    )


# ============================================================
# 80. THROUGHPUT
# ============================================================

def topic_throughput():
    title("80. THROUGHPUT")

    explain(
        "Throughput describes how much data or work can be processed during "
        "a given period. Network throughput may be measured in bits per second, "
        "while application throughput may be expressed as requests per second "
        "or transactions per second."
    )

    print("Example:")
    print("100 MB transferred in 10 seconds")
    print("Average throughput = 10 MB/s")


# ============================================================
# 81. SCALABILITY
# ============================================================

def topic_scalability():
    title("81. WEB SCALABILITY")

    subsection("Vertical scaling")

    explain(
        "Vertical scaling increases the resources of an existing machine, "
        "such as CPU, memory, or storage."
    )

    subsection("Horizontal scaling")

    explain(
        "Horizontal scaling adds additional instances and distributes workload "
        "among them."
    )

    code_block(
        "                 Load Balancer\n"
        "                 /     |     \\\n"
        "                /      |      \\\n"
        "               v       v       v\n"
        "            Server1 Server2 Server3"
    )

    explain(
        "Horizontal scaling often requires applications to minimize local "
        "state or move shared state into systems such as databases, distributed "
        "caches, object stores, or dedicated session infrastructure."
    )


# ============================================================
# 82. MICROSERVICES
# ============================================================

def topic_microservices():
    title("82. MICROSERVICES")

    explain(
        "A microservice architecture divides application functionality into "
        "multiple independently deployable services. Each service typically "
        "owns a specific business capability."
    )

    code_block(
        "API Gateway\n"
        "    |\n"
        "    +----> User Service\n"
        "    |\n"
        "    +----> Order Service\n"
        "    |\n"
        "    +----> Payment Service\n"
        "    |\n"
        "    +----> Notification Service"
    )

    explain(
        "Microservices can improve organizational and deployment independence "
        "but also introduce distributed-systems complexity, network failures, "
        "service discovery, observability requirements, data consistency "
        "challenges, and operational overhead."
    )


# ============================================================
# 83. MESSAGE QUEUES
# ============================================================

def topic_message_queues():
    title("83. MESSAGE QUEUES")

    explain(
        "Message queues allow one component to submit work for another "
        "component to process asynchronously."
    )

    code_block(
        "Web Request\n"
        "    |\n"
        "    v\n"
        "Application\n"
        "    |\n"
        "    | enqueue job\n"
        "    v\n"
        "Message Queue\n"
        "    |\n"
        "    v\n"
        "Worker\n"
        "    |\n"
        "    v\n"
        "Database / External Service"
    )

    bullet("Background processing.")
    bullet("Traffic smoothing.")
    bullet("Retry mechanisms.")
    bullet("Decoupling.")
    bullet("Asynchronous workflows.")


# ============================================================
# 84. DISTRIBUTED SYSTEMS
# ============================================================

def topic_distributed_systems():
    title("84. DISTRIBUTED WEB SYSTEMS")

    explain(
        "A distributed system consists of multiple computers communicating "
        "over a network to perform a shared function. Modern large-scale "
        "Web applications are commonly distributed."
    )

    subsection("Important distributed-system realities")

    bullet("Networks can fail.")
    bullet("Messages can be delayed.")
    bullet("Messages can be duplicated.")
    bullet("Services can become unavailable.")
    bullet("Clocks are not perfectly synchronized.")
    bullet("Partial failure is possible.")
    bullet("Retries can create duplicate operations.")
    bullet("Data replicas can temporarily disagree.")

    explain(
        "These properties explain why concepts such as idempotency, retries, "
        "timeouts, circuit breakers, distributed tracing, replication, "
        "consistency models, and durable messaging are important."
    )


# ============================================================
# 85. RELIABILITY
# ============================================================

def topic_reliability():
    title("85. WEB RELIABILITY")

    explain(
        "Reliability describes the ability of a system to perform its "
        "intended function consistently over time."
    )

    bullet("Health checks.")
    bullet("Redundant instances.")
    bullet("Load balancing.")
    bullet("Retries.")
    bullet("Timeouts.")
    bullet("Circuit breakers.")
    bullet("Graceful degradation.")
    bullet("Backups.")
    bullet("Replication.")
    bullet("Monitoring.")
    bullet("Alerting.")

    explain(
        "Retries should not be unconditional. A retry can amplify load during "
        "an outage. Systems need suitable retry limits, backoff strategies, "
        "and idempotent operation design."
    )


# ============================================================
# 86. OBSERVABILITY
# ============================================================

def topic_observability():
    title("86. WEB OBSERVABILITY")

    explain(
        "Observability is the ability to understand internal system behavior "
        "from external outputs."
    )

    bullet("Logs.")
    bullet("Metrics.")
    bullet("Distributed traces.")
    bullet("Error rates.")
    bullet("Latency measurements.")
    bullet("Resource utilization.")

    code_block(
        "Browser Request\n"
        "      |\n"
        "      v\n"
        "API Gateway [trace=abc]\n"
        "      |\n"
        "      v\n"
        "Service A [trace=abc]\n"
        "      |\n"
        "      v\n"
        "Service B [trace=abc]\n"
        "      |\n"
        "      v\n"
        "Database"
    )

    explain(
        "A trace identifier allows related operations across multiple "
        "components to be correlated."
    )


# ============================================================
# 87. WEB ARCHITECTURE
# ============================================================

def topic_web_architecture():
    title("87. MODERN WEB ARCHITECTURE")

    code_block(
        "                         USERS\n"
        "                           |\n"
        "                           v\n"
        "                    DNS / CDN / Edge\n"
        "                           |\n"
        "                           v\n"
        "                    Load Balancer\n"
        "                           |\n"
        "                           v\n"
        "                    Reverse Proxy\n"
        "                           |\n"
        "             +-------------+-------------+\n"
        "             |                           |\n"
        "             v                           v\n"
        "       Frontend Assets              API Layer\n"
        "             |                           |\n"
        "             |                    +------+------+\n"
        "             |                    |             |\n"
        "             |                    v             v\n"
        "             |                Services       Cache\n"
        "             |                    |\n"
        "             |             +------+------+\n"
        "             |             |             |\n"
        "             |             v             v\n"
        "             |          Database      Queue\n"
        "             |                           |\n"
        "             |                           v\n"
        "             |                         Workers\n"
        "             |\n"
        "             v\n"
        "          Browser"
    )

    explain(
        "This is an architectural model rather than a mandatory structure. "
        "Small websites may have only a Web server and database. Large systems "
        "may have dozens or thousands of distributed components."
    )


# ============================================================
# 88. REQUEST END-TO-END
# ============================================================

def topic_end_to_end():
    title("88. COMPLETE END-TO-END WEB REQUEST")

    steps = [
        "User enters https://shop.example.com/products/42.",
        "Browser parses the URL.",
        "Browser checks relevant caches and existing connection state.",
        "DNS resolution identifies an appropriate destination.",
        "Network packets leave the user's device.",
        "Local router forwards traffic.",
        "ISP infrastructure routes the traffic.",
        "Internet routing carries packets toward the destination.",
        "CDN or edge infrastructure may receive the connection.",
        "TLS negotiation authenticates the destination and establishes encryption.",
        "HTTP request is sent.",
        "Load balancer selects a backend.",
        "Reverse proxy routes the request.",
        "Application server validates the request.",
        "Authentication state may be checked.",
        "Authorization rules may be evaluated.",
        "Application logic processes the request.",
        "Cache may provide the requested data.",
        "If necessary, database queries are executed.",
        "Application constructs a response.",
        "Response travels back through the network.",
        "Browser receives HTTP response.",
        "Browser processes response headers.",
        "HTML is parsed.",
        "Additional CSS, JavaScript, images, and fonts are requested.",
        "CSS is parsed.",
        "JavaScript executes.",
        "DOM and styles are processed.",
        "Layout is calculated.",
        "Pixels are painted and composited.",
        "The user sees and interacts with the page.",
    ]

    for index, step in enumerate(steps, 1):
        print(f"{index:02}. {step}")


# ============================================================
# 89. BROWSER RENDERING PIPELINE
# ============================================================

def topic_rendering_pipeline():
    title("89. BROWSER RENDERING PIPELINE")

    code_block(
        "HTML\n"
        " |\n"
        " v\n"
        "DOM\n"
        " |\n"
        " +---------+\n"
        " |         |\n"
        " v         v\n"
        "CSS       JavaScript\n"
        " |         |\n"
        " v         v\n"
        "CSSOM     DOM changes\n"
        " \\         /\n"
        "  \\       /\n"
        "   v     v\n"
        "Render information\n"
        "       |\n"
        "       v\n"
        "Layout\n"
        "       |\n"
        "       v\n"
        "Paint\n"
        "       |\n"
        "       v\n"
        "Compositing\n"
        "       |\n"
        "       v\n"
        "Display"
    )

    explain(
        "The precise browser implementation is more sophisticated and can "
        "perform incremental updates, parallel work, speculative operations, "
        "and GPU-assisted rendering."
    )


# ============================================================
# 90. EVENT LOOP
# ============================================================

def topic_event_loop():
    title("90. JAVASCRIPT EVENT LOOP")

    explain(
        "JavaScript in browsers uses an event-driven execution model. "
        "The event loop coordinates execution of JavaScript tasks with "
        "asynchronous operations and rendering opportunities."
    )

    code_block(
        "Call Stack\n"
        "    |\n"
        "    v\n"
        "Web APIs / asynchronous operations\n"
        "    |\n"
        "    v\n"
        "Task queues / microtask queue\n"
        "    |\n"
        "    v\n"
        "Event Loop\n"
        "    |\n"
        "    v\n"
        "Call Stack"
    )

    explain(
        "Promises use the microtask queue. Timers, many user events, and "
        "other asynchronous sources schedule tasks. The browser also has "
        "rendering responsibilities that interact with this scheduling model."
    )


# ============================================================
# 91. ASYNCHRONOUS HTTP
# ============================================================

def topic_async_http():
    title("91. ASYNCHRONOUS WEB REQUESTS")

    explain(
        "A browser can send an HTTP request using JavaScript without navigating "
        "the entire page. The Fetch API is one common interface for this."
    )

    code_block(
        "fetch('/api/products')\n"
        "    .then(response => response.json())\n"
        "    .then(data => {\n"
        "        console.log(data);\n"
        "    });"
    )

    explain(
        "This model is fundamental to single-page applications and many "
        "interactive Web interfaces."
    )


# ============================================================
# 92. SPA
# ============================================================

def topic_spa():
    title("92. SINGLE-PAGE APPLICATIONS")

    explain(
        "A single-page application typically loads an initial application "
        "shell and then updates the visible interface dynamically using "
        "client-side JavaScript."
    )

    bullet("Initial HTML.")
    bullet("JavaScript bundle.")
    bullet("Client-side routing.")
    bullet("API requests.")
    bullet("Client-side state.")
    bullet("Dynamic DOM updates.")

    explain(
        "An SPA does not eliminate HTTP or server-side infrastructure. "
        "It changes how the browser constructs and updates the interface."
    )


# ============================================================
# 93. SSR
# ============================================================

def topic_ssr():
    title("93. SERVER-SIDE RENDERING")

    explain(
        "Server-side rendering generates HTML on the server and sends the "
        "result to the browser. The browser can then render the HTML and may "
        "load JavaScript to provide additional interaction."
    )

    code_block(
        "Browser\n"
        "   |\n"
        "   | Request\n"
        "   v\n"
        "Server\n"
        "   |\n"
        "   | Generate HTML\n"
        "   v\n"
        "Browser\n"
        "   |\n"
        "   | Hydration / JavaScript\n"
        "   v\n"
        "Interactive page"
    )


# ============================================================
# 94. STATIC SITE
# ============================================================

def topic_static_sites():
    title("94. STATIC WEBSITES")

    explain(
        "A static website can consist primarily of pre-generated HTML, CSS, "
        "JavaScript, images, and other assets. These resources can often be "
        "served efficiently through CDNs."
    )

    bullet("Simple deployment model.")
    bullet("Highly cacheable assets.")
    bullet("Low server-side computation for static requests.")
    bullet("Can scale efficiently through edge distribution.")


# ============================================================
# 95. SERVERLESS
# ============================================================

def topic_serverless():
    title("95. SERVERLESS WEB COMPUTING")

    explain(
        "Serverless computing abstracts much of the underlying server "
        "management. Developers deploy functions or managed services, "
        "while the platform manages infrastructure details."
    )

    code_block(
        "HTTP Request\n"
        "     |\n"
        "     v\n"
        "API Gateway\n"
        "     |\n"
        "     v\n"
        "Function\n"
        "     |\n"
        "     +----> Database\n"
        "     |\n"
        "     +----> Object Storage"
    )

    explain(
        "Serverless does not mean that servers do not exist. It means "
        "server management and infrastructure allocation are abstracted "
        "from the application developer."
    )


# ============================================================
# 96. OBJECT STORAGE
# ============================================================

def topic_object_storage():
    title("96. OBJECT STORAGE")

    explain(
        "Object storage systems store files or blobs as objects identified "
        "by keys. They are widely used for images, videos, backups, documents, "
        "and other large data."
    )

    code_block(
        "Application Server\n"
        "       |\n"
        "       | Upload object\n"
        "       v\n"
        "Object Storage\n"
        "       |\n"
        "       v\n"
        "CDN\n"
        "       |\n"
        "       v\n"
        "User"
    )


# ============================================================
# 97. DOMAIN TO SERVER EXAMPLE
# ============================================================

def topic_domain_to_server():
    title("97. FROM DOMAIN NAME TO APPLICATION")

    code_block(
        "https://www.example.com\n"
        "          |\n"
        "          v\n"
        "DNS\n"
        "          |\n"
        "          v\n"
        "IP address / edge endpoint\n"
        "          |\n"
        "          v\n"
        "TLS\n"
        "          |\n"
        "          v\n"
        "HTTP\n"
        "          |\n"
        "          v\n"
        "Load Balancer\n"
        "          |\n"
        "          v\n"
        "Application\n"
        "          |\n"
        "          v\n"
        "Database / Services"
    )


# ============================================================
# 98. REQUEST IDEMPOTENCY
# ============================================================

def topic_idempotency():
    title("98. IDEMPOTENCY IN WEB SYSTEMS")

    explain(
        "Idempotency is particularly important in distributed systems because "
        "clients and infrastructure may retry operations after uncertain "
        "network outcomes."
    )

    code_block(
        "Client sends payment request\n"
        "          |\n"
        "          v\n"
        "Server processes payment\n"
        "          |\n"
        "          X response lost\n"
        "          |\n"
        "          v\n"
        "Client retries\n"
        "          |\n"
        "          v\n"
        "Idempotency key prevents duplicate processing"
    )

    explain(
        "An idempotency key lets the server recognize that multiple requests "
        "belong to the same intended operation."
    )


# ============================================================
# 99. RATE LIMITING
# ============================================================

def topic_rate_limiting():
    title("99. RATE LIMITING")

    explain(
        "Rate limiting restricts how frequently a client, identity, or other "
        "traffic category may perform an operation during a period."
    )

    subsection("Token bucket concept")

    code_block(
        "Bucket capacity = 10 tokens\n"
        "Refill rate = 2 tokens/second\n\n"
        "Request arrives\n"
        "   |\n"
        "   +-- token available -> allow\n"
        "   |\n"
        "   +-- no token -> reject or delay"
    )

    explain(
        "Rate limiting protects resources, controls abuse, and can help "
        "maintain predictable service behavior."
    )


# ============================================================
# 100. RETRIES AND TIMEOUTS
# ============================================================

def topic_retries():
    title("100. TIMEOUTS AND RETRIES")

    explain(
        "Network operations cannot be assumed to complete within a fixed "
        "period. Timeouts prevent a system from waiting indefinitely."
    )

    bullet("Connection timeout.")
    bullet("Read timeout.")
    bullet("Write timeout.")
    bullet("Overall request deadline.")

    explain(
        "Retries can recover from transient failures but should use bounded "
        "attempts and appropriate backoff. Uncontrolled retries can create "
        "a retry storm and worsen an outage."
    )


# ============================================================
# 101. CONTENT DELIVERY FLOW
# ============================================================

def topic_content_delivery():
    title("101. HOW STATIC CONTENT REACHES A USER")

    code_block(
        "Developer publishes asset\n"
        "        |\n"
        "        v\n"
        "Origin storage/server\n"
        "        |\n"
        "        v\n"
        "CDN edge cache\n"
        "        |\n"
        "        v\n"
        "User's browser\n"
        "        |\n"
        "        v\n"
        "Browser cache"
    )

    explain(
        "When a CDN cache contains a valid representation, the request may "
        "be served from the edge without contacting the origin."
    )


# ============================================================
# 102. CACHE HIT/MISS
# ============================================================

def topic_cache_hit_miss():
    title("102. CACHE HIT AND CACHE MISS")

    def cache_lookup(cache, key):
        if key in cache:
            return "HIT", cache[key]
        return "MISS", None

    cache = {
        "/style.css": "cached CSS content",
        "/app.js": "cached JavaScript content",
    }

    for resource in ["/style.css", "/logo.png", "/app.js"]:
        result, value = cache_lookup(cache, resource)
        print(f"{resource:15} -> {result}")
        if value:
            print(f"                 {value}")

    explain(
        "A cache hit avoids work that would otherwise be performed by the "
        "origin or another upstream component. Cache misses require the "
        "resource to be retrieved or generated."
    )


# ============================================================
# 103. WEB STORAGE SIMULATION
# ============================================================

class SimpleStorage:
    def __init__(self):
        self.data = {}

    def set_item(self, key, value):
        self.data[str(key)] = str(value)

    def get_item(self, key):
        return self.data.get(str(key))

    def remove_item(self, key):
        self.data.pop(str(key), None)

    def clear(self):
        self.data.clear()


def topic_storage_simulation():
    title("103. SIMPLE BROWSER STORAGE SIMULATION")

    storage = SimpleStorage()

    storage.set_item("theme", "dark")
    storage.set_item("language", "en")

    print("theme    =", storage.get_item("theme"))
    print("language =", storage.get_item("language"))

    storage.remove_item("language")

    print("language after removal =", storage.get_item("language"))


# ============================================================
# 104. URL ENCODING
# ============================================================

def topic_url_encoding():
    title("104. URL ENCODING")

    value = "web development & networking"
    encoded = urllib.parse.quote(value)

    print("Original :", value)
    print("Encoded  :", encoded)

    explain(
        "URLs have syntax rules. Characters that have special meanings in "
        "URLs or cannot safely appear in particular contexts may need "
        "percent encoding."
    )


# ============================================================
# 105. BASE64
# ============================================================

def topic_base64():
    title("105. BASE64 AND WEB DATA")

    text = "Web data"
    encoded = base64.b64encode(text.encode()).decode()
    decoded = base64.b64decode(encoded).decode()

    print("Original:", text)
    print("Base64  :", encoded)
    print("Decoded :", decoded)

    explain(
        "Base64 is an encoding, not encryption. It converts binary data "
        "into a textual representation using a restricted character set. "
        "Anyone who has Base64 data can decode it."
    )


# ============================================================
# 106. DNS SECURITY
# ============================================================

def topic_dns_security():
    title("106. DNS SECURITY")

    explain(
        "DNS was originally designed without the strong authenticity "
        "properties expected of modern security systems. DNSSEC extends DNS "
        "with digital signatures that allow validating resolvers to verify "
        "the authenticity and integrity of signed DNS data."
    )

    bullet("DNSSEC uses digital signatures.")
    bullet("It provides data origin authentication and integrity.")
    bullet("DNSSEC does not encrypt ordinary DNS query content.")

    explain(
        "Encrypted DNS technologies such as DNS over HTTPS and DNS over TLS "
        "address confidentiality between a client and a DNS resolver, which "
        "is a different problem from DNSSEC's data authenticity model."
    )


# ============================================================
# 107. DNS OVER HTTPS / TLS
# ============================================================

def topic_encrypted_dns():
    title("107. ENCRYPTED DNS")

    subsection("DNS over HTTPS")

    explain(
        "DNS over HTTPS, commonly abbreviated DoH, transports DNS queries "
        "through HTTPS."
    )

    subsection("DNS over TLS")

    explain(
        "DNS over TLS, or DoT, transports DNS queries over a TLS-protected "
        "connection."
    )

    explain(
        "These mechanisms can prevent intermediate network observers from "
        "simply reading DNS messages in transit, although the resolver itself "
        "can still see the queries it processes."
    )


# ============================================================
# 108. HTTP SECURITY HEADERS
# ============================================================

def topic_security_headers():
    title("108. WEB SECURITY HEADERS")

    headers = {
        "Content-Security-Policy":
            "Restricts sources and behaviors for browser-executed content.",
        "Strict-Transport-Security":
            "Tells browsers to use HTTPS for a domain for a defined period.",
        "X-Content-Type-Options":
            "Can prevent certain MIME type sniffing behavior.",
        "Referrer-Policy":
            "Controls referrer information sent with requests.",
        "Permissions-Policy":
            "Controls access to selected browser capabilities.",
    }

    for name, meaning in headers.items():
        print(f"{name:30} -> {meaning}")


# ============================================================
# 109. HTTP CACHE SEMANTICS
# ============================================================

def topic_advanced_caching():
    title("109. ADVANCED HTTP CACHING")

    explain(
        "HTTP caching depends on the request method, response status, cache "
        "headers, validators, freshness lifetime, request directives, and "
        "the characteristics of the cache."
    )

    subsection("Freshness")

    explain(
        "A fresh cached response can generally be reused without contacting "
        "the origin under the applicable caching rules."
    )

    subsection("Validation")

    explain(
        "A stale or validation-required response may be checked against the "
        "origin using validators such as ETag or Last-Modified."
    )

    code_block(
        "Cached response\n"
        "     |\n"
        "     | If fresh -> use immediately\n"
        "     |\n"
        "     | If validation required\n"
        "     v\n"
        "Conditional request\n"
        "     |\n"
        "     +--> 304 Not Modified\n"
        "     |\n"
        "     +--> 200 New representation"
    )


# ============================================================
# 110. LAST-MODIFIED
# ============================================================

def topic_last_modified():
    title("110. LAST-MODIFIED")

    explain(
        "Servers can provide a Last-Modified response header indicating "
        "when a representation was last modified. Clients can use "
        "If-Modified-Since for conditional requests."
    )

    code_block(
        "Last-Modified: Wed, 02 Sep 2026 10:00:00 GMT\n\n"
        "Later:\n"
        "If-Modified-Since: Wed, 02 Sep 2026 10:00:00 GMT"
    )


# ============================================================
# 111. HTTP CONNECTION REUSE
# ============================================================

def topic_connection_reuse():
    title("111. CONNECTION REUSE")

    explain(
        "Opening a network connection has costs. HTTP implementations can "
        "reuse connections for multiple requests when protocol and network "
        "conditions permit."
    )

    code_block(
        "Connection established\n"
        "       |\n"
        "       +---- Request 1\n"
        "       |\n"
        "       +---- Request 2\n"
        "       |\n"
        "       +---- Request 3\n"
        "       |\n"
        "Connection reused"
    )


# ============================================================
# 112. TLS CERTIFICATE NAME MATCHING
# ============================================================

def topic_certificate_names():
    title("112. CERTIFICATE NAME VALIDATION")

    explain(
        "When connecting securely to a hostname, the browser verifies that "
        "the certificate is valid for the requested hostname according to "
        "the certificate's identity fields and matching rules."
    )

    bullet("Requested hostname: example.com")
    bullet("Certificate must cover example.com under certificate matching rules.")
    bullet("A certificate for an unrelated hostname should not be accepted.")


# ============================================================
# 113. HSTS
# ============================================================

def topic_hsts():
    title("113. HSTS")

    explain(
        "HTTP Strict Transport Security allows a site to tell a browser that "
        "the site should be accessed using HTTPS for a specified period."
    )

    code_block(
        "Strict-Transport-Security:\n"
        "max-age=31536000; includeSubDomains"
    )

    explain(
        "HSTS can reduce certain downgrade and protocol-stripping risks by "
        "preventing the browser from using HTTP for a domain after the policy "
        "has been learned."
    )


# ============================================================
# 114. COOKIES AND SECURITY
# ============================================================

def topic_cookie_security():
    title("114. COOKIE SECURITY")

    explain(
        "Authentication cookies deserve special protection because possession "
        "of a valid session identifier may grant access to an account."
    )

    bullet("Use Secure for HTTPS-only session cookies.")
    bullet("Use HttpOnly where JavaScript does not need access.")
    bullet("Choose an appropriate SameSite policy.")
    bullet("Limit Domain and Path where practical.")
    bullet("Use appropriate expiration and rotation policies.")


# ============================================================
# 115. CORS PREFLIGHT
# ============================================================

def topic_cors_preflight():
    title("115. CORS PREFLIGHT")

    explain(
        "Some cross-origin browser requests trigger a preflight request using "
        "the OPTIONS method. The browser uses the response to determine whether "
        "the actual request is permitted."
    )

    code_block(
        "Browser\n"
        "   |\n"
        "   | OPTIONS /api/data\n"
        "   | Origin: https://app.example.com\n"
        "   |\n"
        "   v\n"
        "Server\n"
        "   |\n"
        "   | Access-Control-Allow-Origin\n"
        "   | Access-Control-Allow-Methods\n"
        "   | Access-Control-Allow-Headers\n"
        "   v\n"
        "Browser decides whether to continue"
    )


# ============================================================
# 116. CONTENT SECURITY POLICY
# ============================================================

def topic_csp():
    title("116. CONTENT SECURITY POLICY")

    explain(
        "Content Security Policy provides a declarative mechanism for "
        "restricting where different classes of resources may be loaded "
        "and how certain content may execute."
    )

    code_block(
        "Content-Security-Policy:\n"
        "default-src 'self';\n"
        "img-src 'self' https://images.example.com;"
    )

    explain(
        "A carefully designed CSP can reduce the impact of certain classes "
        "of injection vulnerabilities, especially XSS, though CSP is one "
        "layer of a broader security design."
    )


# ============================================================
# 117. API AUTHORIZATION
# ============================================================

def topic_api_authorization():
    title("117. API AUTHORIZATION")

    explain(
        "An API should determine whether the authenticated identity is "
        "permitted to perform the requested operation on the requested "
        "resource."
    )

    code_block(
        "Request\n"
        "  |\n"
        "  v\n"
        "Identify caller\n"
        "  |\n"
        "  v\n"
        "Check resource ownership / role / policy\n"
        "  |\n"
        "  +---- allowed ----> Process\n"
        "  |\n"
        "  +---- denied ------> 403 Forbidden"
    )


# ============================================================
# 118. API VALIDATION
# ============================================================

def topic_api_validation():
    title("118. API INPUT VALIDATION")

    explain(
        "API input should be validated according to the expected data type, "
        "range, structure, format, and business rules."
    )

    rules = [
        "Required fields must exist.",
        "Strings should respect length constraints.",
        "Numbers should respect valid ranges.",
        "Enumerations should reject unknown values.",
        "Nested objects should follow the expected schema.",
        "Identifiers should be validated.",
        "Uploaded files should be handled according to security policy.",
    ]

    for rule in rules:
        bullet(rule)


# ============================================================
# 119. API VERSIONING
# ============================================================

def topic_api_versioning():
    title("119. API VERSIONING")

    explain(
        "APIs evolve over time. Versioning can help clients and servers "
        "manage incompatible changes."
    )

    examples = [
        "/api/v1/users",
        "/api/v2/users",
        "Accept: application/vnd.example.v2+json",
    ]

    for example in examples:
        bullet(example)

    explain(
        "Versioning strategy is an architectural decision. Compatibility "
        "management is often more important than the literal versioning "
        "mechanism."
    )


# ============================================================
# 120. HTTP ERROR HANDLING
# ============================================================

def topic_http_errors():
    title("120. HTTP ERROR HANDLING")

    explain(
        "A Web application must distinguish between different classes of "
        "failure. A malformed request, authentication failure, missing "
        "resource, rate limit, server failure, and upstream timeout represent "
        "different conditions."
    )

    cases = [
        ("400", "Malformed or invalid request"),
        ("401", "Authentication required or failed"),
        ("403", "Request understood but not permitted"),
        ("404", "Resource not found"),
        ("409", "State conflict"),
        ("429", "Rate limit exceeded"),
        ("500", "Unexpected server error"),
        ("502", "Bad upstream response"),
        ("503", "Service temporarily unavailable"),
        ("504", "Upstream timeout"),
    ]

    for status, meaning in cases:
        print(f"{status}: {meaning}")


# ============================================================
# 121. DNS RESOLUTION PROGRAMMATICALLY
# ============================================================

def topic_dns_programming():
    title("121. DNS FROM A PROGRAMMING PERSPECTIVE")

    explain(
        "Applications can use operating-system or language runtime networking "
        "APIs to resolve hostnames. The application normally does not need "
        "to implement the entire DNS protocol itself."
    )

    try:
        import socket

        host = "example.com"
        result = socket.gethostbyname(host)

        print(f"Hostname: {host}")
        print(f"Resolved IPv4 address: {result}")

    except Exception as error:
        print("DNS resolution could not be performed:", error)


# ============================================================
# 122. SOCKET CONCEPT
# ============================================================

def topic_socket():
    title("122. SOCKETS")

    explain(
        "A socket is an operating-system abstraction used by applications "
        "to communicate over networks. TCP sockets provide a byte-stream "
        "interface, while UDP sockets provide datagram-oriented communication."
    )

    code_block(
        "Application\n"
        "    |\n"
        "    v\n"
        "Socket API\n"
        "    |\n"
        "    v\n"
        "Operating System Network Stack\n"
        "    |\n"
        "    v\n"
        "Network Interface\n"
        "    |\n"
        "    v\n"
        "Network"
    )


# ============================================================
# 123. WEB SERVER SOCKET MODEL
# ============================================================

def topic_server_socket():
    title("123. WEB SERVER SOCKET MODEL")

    code_block(
        "Server creates socket\n"
        "       |\n"
        "       v\n"
        "bind(IP, port)\n"
        "       |\n"
        "       v\n"
        "listen()\n"
        "       |\n"
        "       v\n"
        "accept()\n"
        "       |\n"
        "       v\n"
        "Receive request\n"
        "       |\n"
        "       v\n"
        "Send response"
    )

    explain(
        "Production Web servers implement highly optimized versions of "
        "this conceptual model, often using asynchronous I/O, event-driven "
        "architectures, worker processes, threads, connection pools, and "
        "other mechanisms."
    )


# ============================================================
# 124. CLIENT-SERVER PORT EXAMPLE
# ============================================================

def topic_client_server_ports():
    title("124. CLIENT AND SERVER PORTS")

    explain(
        "A server usually listens on a known port while a client uses an "
        "ephemeral source port selected by the operating system."
    )

    code_block(
        "Client\n"
        "192.168.1.10:52341\n"
        "       |\n"
        "       | TCP connection\n"
        "       v\n"
        "Server\n"
        "203.0.113.20:443"
    )

    explain(
        "The combination of source and destination addresses and ports helps "
        "the operating system identify network flows."
    )


# ============================================================
# 125. HTTP HOST
# ============================================================

def topic_host_header():
    title("125. HOST HEADER AND VIRTUAL HOSTING")

    explain(
        "A single IP address can host multiple websites. The HTTP Host header "
        "allows an HTTP/1.1 server to determine which hostname the client "
        "requested."
    )

    code_block(
        "GET / HTTP/1.1\n"
        "Host: shop.example.com"
    )

    explain(
        "TLS uses the Server Name Indication extension during connection "
        "establishment to communicate the intended hostname early enough "
        "for the server to select an appropriate certificate in common "
        "multi-domain deployments."
    )


# ============================================================
# 126. SNI
# ============================================================

def topic_sni():
    title("126. SERVER NAME INDICATION")

    explain(
        "SNI is a TLS extension that allows a client to indicate the hostname "
        "it wants to connect to during the TLS handshake."
    )

    code_block(
        "One server IP\n"
        "     |\n"
        "     +---- example.com certificate\n"
        "     |\n"
        "     +---- shop.example.com certificate\n"
        "     |\n"
        "     +---- api.example.com certificate"
    )


# ============================================================
# 127. ALPN
# ============================================================

def topic_alpn():
    title("127. ALPN")

    explain(
        "Application-Layer Protocol Negotiation allows endpoints during TLS "
        "negotiation to agree on an application protocol such as HTTP/2 or "
        "HTTP/1.1."
    )

    code_block(
        "Client offers:\n"
        "h2, http/1.1\n\n"
        "Server selects:\n"
        "h2"
    )


# ============================================================
# 128. HTTP/2 MULTIPLEXING
# ============================================================

def topic_http2_multiplexing():
    title("128. HTTP/2 MULTIPLEXING")

    explain(
        "HTTP/2 divides communication into streams and frames, allowing "
        "multiple request and response streams to share a connection."
    )

    code_block(
        "One TCP connection\n"
        "==================\n"
        "| Stream 1: HTML  |\n"
        "| Stream 2: CSS   |\n"
        "| Stream 3: JS    |\n"
        "| Stream 4: Image |\n"
        "=================="
    )


# ============================================================
# 129. QUIC STREAMS
# ============================================================

def topic_quic_streams():
    title("129. QUIC STREAMS")

    explain(
        "QUIC provides independent streams. Loss affecting one stream does "
        "not necessarily prevent application progress on other streams in "
        "the same way that TCP's single ordered byte stream can."
    )

    code_block(
        "QUIC Connection\n"
        "====================\n"
        "| Stream A: HTML    |\n"
        "| Stream B: Image   |\n"
        "| Stream C: API     |\n"
        "===================="
    )


# ============================================================
# 130. HTTP/3 CONNECTION MIGRATION
# ============================================================

def topic_connection_migration():
    title("130. CONNECTION MIGRATION")

    explain(
        "QUIC can identify a connection independently from a single fixed "
        "network path. This enables connection migration in situations such "
        "as a device moving between networks, subject to protocol and "
        "implementation conditions."
    )

    code_block(
        "Wi-Fi\n"
        "  |\n"
        "  | QUIC connection\n"
        "  v\n"
        "Mobile network\n"
        "  |\n"
        "  | Same logical connection can continue\n"
        "  v\n"
        "Server"
    )


# ============================================================
# 131. WEB CACHING LAYERS
# ============================================================

def topic_cache_layers():
    title("131. MULTIPLE CACHE LAYERS")

    layers = [
        "Browser memory cache",
        "Browser disk cache",
        "Service worker cache",
        "Local network cache",
        "CDN cache",
        "Reverse proxy cache",
        "Application cache",
        "Database cache",
    ]

    for index, layer in enumerate(layers, 1):
        print(f"{index}. {layer}")

    explain(
        "A single request can interact with multiple caching systems. "
        "Correct cache invalidation and cache-control semantics therefore "
        "matter greatly in Web architecture."
    )


# ============================================================
# 132. CACHE INVALIDATION
# ============================================================

def topic_cache_invalidation():
    title("132. CACHE INVALIDATION")

    explain(
        "Cache invalidation means ensuring cached data is no longer used "
        "when the underlying representation has changed or is no longer "
        "appropriate."
    )

    bullet("Short freshness periods.")
    bullet("Versioned asset filenames.")
    bullet("ETags.")
    bullet("Explicit purge mechanisms.")
    bullet("Cache-control directives.")

    code_block(
        "app.js\n"
        "     |\n"
        "     v\n"
        "app.8f32a.js\n"
        "     |\n"
        "     v\n"
        "New filename forces a new cache key"
    )


# ============================================================
# 133. WEB PERFORMANCE WATERFALL
# ============================================================

def topic_waterfall():
    title("133. CONCEPTUAL RESOURCE WATERFALL")

    code_block(
        "HTML request       |====|\n"
        "DNS                 |==|\n"
        "TLS                 |===|\n"
        "HTML transfer          |=====|\n"
        "CSS                         |===|\n"
        "JavaScript                  |======|\n"
        "Image                           |====|\n"
        "Font                              |==|"
    )

    explain(
        "Browser developer tools commonly display a network waterfall. "
        "It helps reveal connection delays, request dependencies, server "
        "latency, transfer time, caching behavior, and resource loading order."
    )


# ============================================================
# 134. THIRD-PARTY RESOURCES
# ============================================================

def topic_third_party():
    title("134. THIRD-PARTY WEB RESOURCES")

    explain(
        "A webpage may load resources from domains other than its own. "
        "Examples include analytics systems, payment providers, fonts, "
        "advertising services, maps, video platforms, and other integrations."
    )

    bullet("Additional DNS lookups.")
    bullet("Additional connections.")
    bullet("Additional latency.")
    bullet("Additional privacy considerations.")
    bullet("Additional security dependencies.")
    bullet("Additional failure modes.")


# ============================================================
# 135. WEB ACCESSIBILITY
# ============================================================

def topic_accessibility():
    title("135. WEB ACCESSIBILITY")

    explain(
        "Accessibility means designing Web content and applications so "
        "that people with different abilities can perceive, understand, "
        "navigate, and interact with them."
    )

    bullet("Semantic HTML.")
    bullet("Keyboard accessibility.")
    bullet("Meaningful labels.")
    bullet("Accessible forms.")
    bullet("Alternative text.")
    bullet("Appropriate focus management.")
    bullet("Sufficient visual contrast.")
    bullet("Accessible dynamic updates.")


# ============================================================
# 136. PROGRESSIVE ENHANCEMENT
# ============================================================

def topic_progressive_enhancement():
    title("136. PROGRESSIVE ENHANCEMENT")

    explain(
        "Progressive enhancement starts with a functional foundation and "
        "adds more advanced capabilities when the browser and environment "
        "support them."
    )

    code_block(
        "Semantic HTML\n"
        "     |\n"
        "     +--> CSS presentation\n"
        "     |\n"
        "     +--> JavaScript interaction\n"
        "     |\n"
        "     +--> Advanced browser APIs"
    )


# ============================================================
# 137. WEB COMPONENTS
# ============================================================

def topic_web_components():
    title("137. WEB COMPONENTS")

    explain(
        "Web Components are a collection of browser technologies that allow "
        "developers to create reusable custom elements. Important pieces "
        "include Custom Elements, Shadow DOM, and HTML templates."
    )

    bullet("Custom Elements.")
    bullet("Shadow DOM.")
    bullet("HTML templates.")
    bullet("Encapsulation of component structure and styles.")


# ============================================================
# 138. STORAGE AND PRIVACY
# ============================================================

def topic_privacy():
    title("138. WEB PRIVACY")

    explain(
        "Browsers expose many mechanisms through which websites can store "
        "or access information. Privacy protections attempt to limit unwanted "
        "cross-site tracking and reduce unnecessary exposure."
    )

    bullet("Cookie controls.")
    bullet("Storage partitioning.")
    bullet("Third-party cookie restrictions.")
    bullet("Permission controls.")
    bullet("Referrer policies.")
    bullet("Browser fingerprinting defenses.")

    explain(
        "Privacy behavior differs across browsers and continues to evolve. "
        "A Web application should not assume that cross-site storage behavior "
        "is identical across all user agents."
    )


# ============================================================
# 139. HTTP COOKIES VS LOCAL STORAGE
# ============================================================

def topic_cookie_vs_storage():
    title("139. COOKIES VS LOCAL STORAGE")

    comparison = [
        ("Sent automatically with matching HTTP requests", "Cookies", "Yes"),
        ("Accessible to JavaScript", "Cookies", "Depends; HttpOnly prevents it"),
        ("Simple key-value API", "LocalStorage", "Yes"),
        ("Automatically attached to requests", "LocalStorage", "No"),
        ("Has HTTP-specific attributes", "Cookies", "Yes"),
    ]

    for description, mechanism, answer in comparison:
        print(f"{description:50} {mechanism:15} {answer}")


# ============================================================
# 140. WEB ARCHITECTURE WITH EDGE
# ============================================================

def topic_edge_computing():
    title("140. EDGE COMPUTING")

    explain(
        "Edge computing moves selected computation closer to users or "
        "network edges. This can reduce latency and decrease the distance "
        "between clients and processing infrastructure."
    )

    code_block(
        "User\n"
        " |\n"
        " v\n"
        "Nearest Edge Location\n"
        " |\n"
        " +----> Return cached response\n"
        " |\n"
        " +----> Execute edge logic\n"
        " |\n"
        " +----> Forward to origin"
    )


# ============================================================
# 141. SERVER-SIDE CACHING
# ============================================================

def topic_server_cache():
    title("141. SERVER-SIDE CACHING")

    explain(
        "Applications can cache expensive computations or frequently used "
        "data. A cache can reduce database load and improve response latency."
    )

    code_block(
        "Request\n"
        "  |\n"
        "  v\n"
        "Application\n"
        "  |\n"
        "  +--> Cache HIT --> Response\n"
        "  |\n"
        "  +--> Cache MISS\n"
        "          |\n"
        "          v\n"
        "       Database\n"
        "          |\n"
        "          v\n"
        "        Cache\n"
        "          |\n"
        "          v\n"
        "       Response"
    )


# ============================================================
# 142. DATABASE CONNECTION POOL
# ============================================================

def topic_connection_pool():
    title("142. DATABASE CONNECTION POOLS")

    explain(
        "Opening a database connection can be expensive. A connection pool "
        "maintains reusable connections so application requests can borrow "
        "and return them."
    )

    code_block(
        "Application Requests\n"
        "   |   |   |   |\n"
        "   v   v   v   v\n"
        "+------------------+\n"
        "| Connection Pool   |\n"
        "| [C1][C2][C3][C4] |\n"
        "+------------------+\n"
        "       |\n"
        "       v\n"
        "    Database"
    )


# ============================================================
# 143. DATABASE INDEXES
# ============================================================

def topic_indexes():
    title("143. DATABASE INDEXES AND WEB PERFORMANCE")

    explain(
        "A database index provides an additional data structure that can "
        "make certain lookups substantially faster. Indexes also consume "
        "storage and add work to writes."
    )

    code_block(
        "Without useful index:\n"
        "Query -> Scan many rows\n\n"
        "With suitable index:\n"
        "Query -> Index lookup -> Relevant rows"
    )

    explain(
        "A slow database query can become a major part of Web request latency, "
        "especially when it is executed frequently or scans a large dataset."
    )


# ============================================================
# 144. TRANSACTIONS
# ============================================================

def topic_transactions():
    title("144. DATABASE TRANSACTIONS")

    explain(
        "Transactions group database operations into a unit governed by "
        "transactional guarantees. Relational systems commonly discuss "
        "ACID properties."
    )

    bullet("Atomicity.")
    bullet("Consistency.")
    bullet("Isolation.")
    bullet("Durability.")

    explain(
        "Transaction behavior varies by database engine and isolation level. "
        "Web applications need to choose transaction boundaries carefully "
        "when multiple operations must remain consistent."
    )


# ============================================================
# 145. DISTRIBUTED CACHES
# ============================================================

def topic_distributed_cache():
    title("145. DISTRIBUTED CACHES")

    explain(
        "A distributed cache provides shared cached state accessible by "
        "multiple application instances."
    )

    code_block(
        "Application 1 ----+\n"
        "                   |\n"
        "Application 2 ----> Distributed Cache\n"
        "                   |\n"
        "Application 3 ----+"
    )

    explain(
        "Distributed caches are useful when multiple application servers "
        "need access to the same rapidly changing cached data."
    )


# ============================================================
# 146. SESSION STORAGE ARCHITECTURE
# ============================================================

def topic_session_architecture():
    title("146. DISTRIBUTED SESSION MANAGEMENT")

    explain(
        "When multiple application instances handle requests, session state "
        "must be available to whichever instance receives a request, unless "
        "the architecture deliberately uses another mechanism."
    )

    code_block(
        "Client\n"
        " |\n"
        " v\n"
        "Load Balancer\n"
        " |      |      |\n"
        " v      v      v\n"
        "App1   App2   App3\n"
        " \\       |      /\n"
        "  \\      |     /\n"
        "   v     v    v\n"
        " Shared Session Store"
    )


# ============================================================
# 147. STICKY SESSIONS
# ============================================================

def topic_sticky_sessions():
    title("147. STICKY SESSIONS")

    explain(
        "Sticky sessions attempt to direct a client's requests to the same "
        "backend instance. This can simplify some stateful architectures "
        "but can reduce flexibility and create uneven load or failure concerns."
    )

    code_block(
        "Client A -> Load Balancer -> Server 1 repeatedly\n"
        "Client B -> Load Balancer -> Server 2 repeatedly"
    )


# ============================================================
# 148. SERVICE DISCOVERY
# ============================================================

def topic_service_discovery():
    title("148. SERVICE DISCOVERY")

    explain(
        "In dynamic distributed environments, service instances may change "
        "frequently. Service discovery mechanisms allow components to locate "
        "available service endpoints."
    )

    code_block(
        "Service A\n"
        "   |\n"
        "   | Where is Service B?\n"
        "   v\n"
        "Service Discovery\n"
        "   |\n"
        "   v\n"
        "Service B endpoint"
    )


# ============================================================
# 149. API GATEWAY
# ============================================================

def topic_api_gateway():
    title("149. API GATEWAYS")

    explain(
        "An API gateway can provide a common entry point for multiple backend "
        "services. It may perform authentication, routing, rate limiting, "
        "request transformation, and other cross-cutting functions."
    )

    code_block(
        "Client\n"
        "  |\n"
        "  v\n"
        "API Gateway\n"
        "  |\n"
        "  +----> User Service\n"
        "  |\n"
        "  +----> Order Service\n"
        "  |\n"
        "  +----> Product Service"
    )


# ============================================================
# 150. DATABASE REPLICATION
# ============================================================

def topic_database_replication():
    title("150. DATABASE REPLICATION")

    explain(
        "Replication maintains copies of data across multiple database "
        "instances. It can improve availability, read scalability, and "
        "disaster recovery depending on the architecture."
    )

    code_block(
        "Primary\n"
        "  |\n"
        "  +----> Replica 1\n"
        "  |\n"
        "  +----> Replica 2"
    )

    explain(
        "Replication can introduce lag. A request immediately following "
        "a write may not see that write when routed to a replica depending "
        "on the replication model."
    )


# ============================================================
# 151. CONSISTENCY
# ============================================================

def topic_consistency():
    title("151. CONSISTENCY IN DISTRIBUTED WEB SYSTEMS")

    explain(
        "Consistency describes how data appears across different copies or "
        "observers. Distributed systems can provide different consistency "
        "models and guarantees."
    )

    bullet("Strong consistency.")
    bullet("Eventual consistency.")
    bullet("Read-after-write consistency.")
    bullet("Session consistency.")

    explain(
        "The appropriate consistency model depends on the application's "
        "business requirements and system architecture."
    )


# ============================================================
# 152. CAP CONCEPT
# ============================================================

def topic_cap():
    title("152. CAP THEOREM CONCEPT")

    explain(
        "CAP theorem concerns distributed data systems under network partition "
        "conditions. It states that a distributed system cannot simultaneously "
        "guarantee all three of consistency, availability, and partition "
        "tolerance in the strongest traditional CAP framing."
    )

    bullet("Consistency.")
    bullet("Availability.")
    bullet("Partition tolerance.")

    explain(
        "Partition tolerance is generally unavoidable in distributed networks. "
        "Therefore, systems make trade-offs in how they behave when partitions "
        "occur."
    )


# ============================================================
# 153. WEB SOCKET SECURITY
# ============================================================

def topic_websocket_security():
    title("153. WEBSOCKET SECURITY")

    explain(
        "WebSocket applications need authentication, authorization, input "
        "validation, origin handling, rate controls, and appropriate transport "
        "security just like other networked applications."
    )

    bullet("Use secure WebSockets where appropriate.")
    bullet("Validate messages.")
    bullet("Authenticate connections.")
    bullet("Authorize actions.")
    bullet("Limit resource consumption.")
    bullet("Handle connection lifecycle correctly.")


# ============================================================
# 154. HTTP STREAMING
# ============================================================

def topic_http_streaming():
    title("154. HTTP STREAMING")

    explain(
        "HTTP can deliver data progressively rather than requiring the "
        "complete response body to be available before transmission begins."
    )

    bullet("Large downloads.")
    bullet("Event streams.")
    bullet("Generated content.")
    bullet("AI/model response streaming.")
    bullet("Media-related workloads.")

    explain(
        "Streaming can reduce time to first byte of useful content and "
        "avoid buffering an entire response in memory."
    )


# ============================================================
# 155. TIME TO FIRST BYTE
# ============================================================

def topic_ttfb():
    title("155. TIME TO FIRST BYTE")

    explain(
        "Time to First Byte, or TTFB, measures the time from initiating a "
        "request until the first byte of the response is received."
    )

    components = [
        "DNS resolution",
        "Connection establishment",
        "TLS negotiation",
        "Request transmission",
        "Server processing",
        "First response byte",
    ]

    for item in components:
        bullet(item)

    explain(
        "A high TTFB can indicate slow network setup, distant infrastructure, "
        "slow server processing, overloaded services, or other bottlenecks."
    )


# ============================================================
# 156. CLIENT RENDERING VS SERVER RENDERING
# ============================================================

def topic_rendering_comparison():
    title("156. CLIENT-SIDE VS SERVER-SIDE RENDERING")

    print(
        f"{'Approach':25} {'Initial HTML generation':30} {'Main dynamic work':30}"
    )
    print("-" * 88)
    print(
        f"{'Client-side rendering':25} "
        f"{'Primarily browser':30} "
        f"{'Browser':30}"
    )
    print(
        f"{'Server-side rendering':25} "
        f"{'Primarily server':30} "
        f"{'Browser after delivery':30}"
    )

    explain(
        "Modern frameworks can combine server rendering, static generation, "
        "client-side rendering, streaming, partial rendering, and other "
        "techniques rather than following one pure model."
    )


# ============================================================
# 157. WEB APPLICATION STATE
# ============================================================

def topic_application_state():
    title("157. WEB APPLICATION STATE")

    explain(
        "State is information that influences application behavior or "
        "presentation. State can exist in many locations."
    )

    locations = [
        "Browser memory",
        "DOM",
        "Cookies",
        "LocalStorage",
        "SessionStorage",
        "IndexedDB",
        "Server-side session",
        "Database",
        "Distributed cache",
        "Message queue",
    ]

    for location in locations:
        bullet(location)


# ============================================================
# 158. FRONTEND AND BACKEND
# ============================================================

def topic_frontend_backend():
    title("158. FRONTEND AND BACKEND")

    explain(
        "Frontend refers to the user-facing software that runs primarily "
        "in the browser. Backend refers to server-side systems that process "
        "requests, apply business logic, access data, and provide services."
    )

    code_block(
        "Frontend\n"
        "HTML + CSS + JavaScript\n"
        "          |\n"
        "          | HTTPS / WebSocket / other protocols\n"
        "          v\n"
        "Backend\n"
        "Application + APIs + Databases + Services"
    )


# ============================================================
# 159. BROWSER SECURITY SANDBOX
# ============================================================

def topic_browser_sandbox():
    title("159. BROWSER SANDBOXING")

    explain(
        "Browsers isolate webpage code from sensitive operating-system "
        "resources. Sandboxing limits what compromised Web content can do "
        "directly."
    )

    bullet("Process isolation.")
    bullet("Origin isolation.")
    bullet("Permission controls.")
    bullet("Restricted filesystem access.")
    bullet("Controlled access to device capabilities.")

    explain(
        "Sandboxing is an important defense layer, but browser vulnerabilities "
        "and malicious applications can still attempt to exploit weaknesses "
        "in the browser or operating system."
    )


# ============================================================
# 160. SAME-ORIGIN EXAMPLE
# ============================================================

def topic_origin_examples():
    title("160. ORIGIN COMPARISON")

    pairs = [
        (
            "https://example.com/a",
            "https://example.com/b",
            True,
        ),
        (
            "https://example.com",
            "http://example.com",
            False,
        ),
        (
            "https://example.com",
            "https://api.example.com",
            False,
        ),
        (
            "https://example.com",
            "https://example.com:8443",
            False,
        ),
    ]

    for first, second, same in pairs:
        result = "same origin" if same else "different origins"
        print(f"{first}  vs  {second} -> {result}")


# ============================================================
# 161. REQUEST BODY FORMATS
# ============================================================

def topic_request_bodies():
    title("161. COMMON HTTP REQUEST BODY FORMATS")

    formats = {
        "application/json": "Structured JSON data.",
        "application/x-www-form-urlencoded": "Form-style key-value data.",
        "multipart/form-data": "Forms containing files and structured fields.",
        "text/plain": "Plain text.",
        "application/octet-stream": "Arbitrary binary data.",
    }

    for content_type, description in formats.items():
        print(f"{content_type:40} -> {description}")


# ============================================================
# 162. MULTIPART UPLOAD
# ============================================================

def topic_multipart():
    title("162. FILE UPLOADS")

    explain(
        "multipart/form-data allows a request body to contain multiple parts, "
        "including text fields and uploaded files."
    )

    code_block(
        "POST /upload HTTP/1.1\n"
        "Content-Type: multipart/form-data; boundary=XYZ\n\n"
        "--XYZ\n"
        "Content-Disposition: form-data; name=\"description\"\n\n"
        "Example file\n"
        "--XYZ\n"
        "Content-Disposition: form-data; name=\"file\"; filename=\"a.txt\"\n"
        "Content-Type: text/plain\n\n"
        "file contents\n"
        "--XYZ--"
    )

    explain(
        "Servers must validate uploaded files rather than trusting filenames, "
        "client-provided MIME types, or other untrusted metadata."
    )


# ============================================================
# 163. REQUEST SMUGGLING CONCEPT
# ============================================================

def topic_request_smuggling():
    title("163. HTTP REQUEST SMUGGLING CONCEPT")

    explain(
        "HTTP request smuggling can occur when different components in a "
        "request-processing chain interpret request boundaries differently."
    )

    code_block(
        "Client\n"
        "   |\n"
        "   v\n"
        "Front-end proxy\n"
        "   |\n"
        "   v\n"
        "Back-end server\n"
        "   |\n"
        "Different interpretations of request framing\n"
        "   |\n"
        "Potential security issue"
    )

    explain(
        "Careful protocol parsing, consistent handling of message framing, "
        "and properly maintained Web infrastructure are important defenses."
    )


# ============================================================
# 164. DNS RECURSIVE RESOLVER
# ============================================================

def topic_recursive_resolver():
    title("164. RECURSIVE DNS RESOLUTION")

    explain(
        "A recursive resolver performs DNS lookup work on behalf of a client. "
        "It may query other DNS servers and cache results."
    )

    code_block(
        "Client\n"
        "  |\n"
        "  v\n"
        "Recursive Resolver\n"
        "  |\n"
        "  +--> Root\n"
        "  |\n"
        "  +--> TLD\n"
        "  |\n"
        "  +--> Authoritative\n"
        "  |\n"
        "  v\n"
        "Answer to client"
    )


# ============================================================
# 165. AUTHORITATIVE DNS
# ============================================================

def topic_authoritative_dns():
    title("165. AUTHORITATIVE DNS")

    explain(
        "An authoritative DNS server provides the definitive DNS records "
        "for a DNS zone under its authority."
    )

    bullet("Recursive resolver asks questions.")
    bullet("Authoritative server provides authoritative answers for its zone.")
    bullet("Caching resolvers can temporarily store those answers.")


# ============================================================
# 166. DOMAIN DELEGATION
# ============================================================

def topic_dns_delegation():
    title("166. DNS DELEGATION")

    explain(
        "DNS delegation allows responsibility for a domain or subdomain "
        "to be assigned to specified authoritative name servers."
    )

    code_block(
        "Root\n"
        " |\n"
        " +--> .com\n"
        "       |\n"
        "       +--> example.com\n"
        "                |\n"
        "                +--> Authoritative DNS"
    )


# ============================================================
# 167. IPV4 ADDRESS EXHAUSTION
# ============================================================

def topic_ipv4_ipv6():
    title("167. IPV4 AND IPV6")

    explain(
        "IPv4 provides approximately 4.3 billion possible 32-bit addresses, "
        "before accounting for allocation and special-purpose ranges. "
        "IPv6 uses 128-bit addresses, providing an enormous address space."
    )

    print("IPv4 bits :", 32)
    print("IPv6 bits :", 128)
    print("IPv4 space:", 2 ** 32)
    print("IPv6 space:", 2 ** 128)

    explain(
        "IPv6 adoption does not simply replace every IPv4 component instantly. "
        "Dual-stack operation, translation technologies, and transition "
        "mechanisms are used in many environments."
    )


# ============================================================
# 168. NETWORK ADDRESSING EXAMPLE
# ============================================================

def topic_network_calculation():
    title("168. NETWORK ADDRESS CALCULATION")

    network = ipaddress.ip_network("192.168.10.0/24")

    print("Network:", network)
    print("Network address:", network.network_address)
    print("Broadcast address:", network.broadcast_address)
    print("Prefix length:", network.prefixlen)
    print("Number of addresses:", network.num_addresses)

    explain(
        "IPv4 subnets contain a network address and, for traditional subnet "
        "usage, a broadcast address. Host address availability depends on "
        "the subnet size and addressing rules."
    )


# ============================================================
# 169. HTTP REDIRECTS
# ============================================================

def topic_redirects():
    title("169. HTTP REDIRECTS")

    explain(
        "Redirect responses tell a client that the resource should be accessed "
        "at another URL or according to another location."
    )

    code_block(
        "HTTP/1.1 301 Moved Permanently\n"
        "Location: https://example.com/new-location"
    )

    bullet("301 = permanent redirect.")
    bullet("302 = temporary redirect under traditional semantics.")
    bullet("307 = temporary redirect while preserving method semantics.")
    bullet("308 = permanent redirect while preserving method semantics.")


# ============================================================
# 170. HTTP AUTHORIZATION
# ============================================================

def topic_http_auth():
    title("170. HTTP AUTHORIZATION HEADER")

    explain(
        "The Authorization header can carry credentials or an access token "
        "according to the authentication scheme."
    )

    code_block(
        "GET /api/profile HTTP/1.1\n"
        "Authorization: Bearer <access-token>"
    )

    explain(
        "Bearer tokens must be protected because possession of a valid bearer "
        "token can be sufficient to authorize requests."
    )


# ============================================================
# 171. OAUTH CONCEPT
# ============================================================

def topic_oauth():
    title("171. OAUTH CONCEPT")

    explain(
        "OAuth is an authorization framework that allows a resource owner "
        "to grant a client limited access to resources without directly "
        "sharing the resource owner's credentials with the client."
    )

    code_block(
        "User\n"
        " |\n"
        " v\n"
        "Authorization Server\n"
        " |\n"
        " | Authorization grant\n"
        " v\n"
        "Client Application\n"
        " |\n"
        " | Access token\n"
        " v\n"
        "Resource Server"
    )

    explain(
        "OAuth itself is about authorization. OpenID Connect builds an "
        "identity layer on top of OAuth 2.0."
    )


# ============================================================
# 172. OPENID CONNECT
# ============================================================

def topic_oidc():
    title("172. OPENID CONNECT")

    explain(
        "OpenID Connect is an identity protocol built on top of OAuth 2.0. "
        "It allows a client to obtain information about the authenticated "
        "user from an identity provider."
    )

    bullet("Identity Provider.")
    bullet("Client application.")
    bullet("Authorization endpoint.")
    bullet("Token endpoint.")
    bullet("ID token.")
    bullet("User information.")


# ============================================================
# 173. CSRF AND SAME-SITE
# ============================================================

def topic_csrf_samesite():
    title("173. CSRF AND SAME-SITE COOKIES")

    explain(
        "SameSite cookie behavior can reduce the conditions under which "
        "cookies are sent during cross-site requests. This can reduce CSRF "
        "risk, but cookie configuration must be understood in relation to "
        "the application's actual authentication and navigation requirements."
    )

    bullet("Strict.")
    bullet("Lax.")
    bullet("None, which generally requires Secure.")


# ============================================================
# 174. SECURITY MODEL
# ============================================================

def topic_security_model():
    title("174. WEB SECURITY MODEL")

    code_block(
        "User Input\n"
        "    |\n"
        "    v\n"
        "Browser Security\n"
        "    |\n"
        "    v\n"
        "TLS / HTTPS\n"
        "    |\n"
        "    v\n"
        "Server Authentication\n"
        "    |\n"
        "    v\n"
        "Authorization\n"
        "    |\n"
        "    v\n"
        "Input Validation\n"
        "    |\n"
        "    v\n"
        "Safe Business Logic\n"
        "    |\n"
        "    v\n"
        "Secure Data Access"
    )

    explain(
        "Security is a chain of controls. Failure at one layer can undermine "
        "protection provided by another layer."
    )


# ============================================================
# 175. HOW A BROWSER FINDS A PAGE
# ============================================================

def topic_full_browser_sequence():
    title("175. FULL BROWSER PAGE-LOAD MODEL")

    code_block(
        "URL entered\n"
        "   |\n"
        "   v\n"
        "URL parsing\n"
        "   |\n"
        "   v\n"
        "Cache checks\n"
        "   |\n"
        "   v\n"
        "DNS resolution\n"
        "   |\n"
        "   v\n"
        "Network route\n"
        "   |\n"
        "   v\n"
        "TCP / QUIC\n"
        "   |\n"
        "   v\n"
        "TLS\n"
        "   |\n"
        "   v\n"
        "HTTP\n"
        "   |\n"
        "   v\n"
        "Server infrastructure\n"
        "   |\n"
        "   v\n"
        "Response\n"
        "   |\n"
        "   v\n"
        "HTML parsing\n"
        "   |\n"
        "   +----> CSS\n"
        "   |\n"
        "   +----> JavaScript\n"
        "   |\n"
        "   +----> Images\n"
        "   |\n"
        "   +----> Fonts\n"
        "   |\n"
        "   v\n"
        "DOM + CSSOM\n"
        "   |\n"
        "   v\n"
        "Layout\n"
        "   |\n"
        "   v\n"
        "Paint\n"
        "   |\n"
        "   v\n"
        "Composite\n"
        "   |\n"
        "   v\n"
        "Interactive Web page"
    )


# ============================================================
# 176. WHY HTTPS IS IMPORTANT
# ============================================================

def topic_https_importance():
    title("176. WHY HTTPS MATTERS")

    explain(
        "Without transport encryption, network intermediaries may be able "
        "to observe or modify application data depending on the network "
        "position and protocol. HTTPS protects HTTP traffic against many "
        "forms of passive observation and active tampering during transport."
    )

    bullet("Confidentiality.")
    bullet("Integrity.")
    bullet("Server authentication.")
    bullet("Protection against many network-level modifications.")

    explain(
        "HTTPS does not prove that a website is honest or that its application "
        "logic is secure. It authenticates the server identity represented "
        "by the certificate within the applicable certificate trust model."
    )


# ============================================================
# 177. WHY DNS MATTERS
# ============================================================

def topic_dns_importance():
    title("177. WHY DNS MATTERS TO THE WEB")

    explain(
        "DNS decouples human-friendly names from specific network addresses. "
        "This allows infrastructure to change while users continue using "
        "the same domain name."
    )

    code_block(
        "example.com\n"
        "    |\n"
        "    +----> IP A today\n"
        "    |\n"
        "    +----> IP B later\n"
        "    |\n"
        "    +----> CDN endpoint\n"
        "    |\n"
        "    +----> Load balancer"
    )


# ============================================================
# 178. WHY PORTS MATTER
# ============================================================

def topic_port_importance():
    title("178. WHY PORTS MATTER")

    explain(
        "A single machine can run many network services simultaneously. "
        "Port numbers allow traffic to be delivered to the appropriate "
        "service or socket."
    )

    code_block(
        "Server IP: 203.0.113.10\n"
        " |\n"
        " +---- TCP 22  -> SSH\n"
        " +---- TCP 80  -> HTTP\n"
        " +---- TCP 443 -> HTTPS\n"
        " +---- TCP 5432 -> PostgreSQL"
    )


# ============================================================
# 179. WHY PROTOCOLS MATTER
# ============================================================

def topic_protocols():
    title("179. WHY PROTOCOLS MATTER")

    explain(
        "A protocol defines agreed rules for communication. Without shared "
        "rules, independent systems could not reliably interpret the data "
        "they exchange."
    )

    bullet("IP defines network addressing and packet forwarding behavior.")
    bullet("TCP defines reliable byte-stream transport.")
    bullet("UDP defines datagram transport.")
    bullet("TLS defines secure transport mechanisms.")
    bullet("HTTP defines Web request-response semantics.")
    bullet("DNS defines domain name resolution mechanisms.")


# ============================================================
# 180. THE COMPLETE STACK
# ============================================================

def topic_complete_stack():
    title("180. COMPLETE WEB STACK")

    code_block(
        "USER\n"
        " |\n"
        " v\n"
        "BROWSER\n"
        " |\n"
        " +-------------------------------+\n"
        " | HTML / CSS / JavaScript       |\n"
        " +-------------------------------+\n"
        " |\n"
        "HTTP / HTTP2 / HTTP3\n"
        " |\n"
        "TLS\n"
        " |\n"
        "TCP / QUIC / UDP\n"
        " |\n"
        "IP\n"
        " |\n"
        "Ethernet / Wi-Fi / Cellular\n"
        " |\n"
        "INTERNET\n"
        " |\n"
        "DNS / ROUTING / CDN / EDGE\n"
        " |\n"
        "SERVER INFRASTRUCTURE\n"
        " |\n"
        "LOAD BALANCER\n"
        " |\n"
        "REVERSE PROXY\n"
        " |\n"
        "APPLICATION SERVER\n"
        " |\n"
        "CACHE / QUEUE / SERVICES\n"
        " |\n"
        "DATABASE / OBJECT STORAGE"
    )

    explain(
        "The Web is therefore not one technology. It is an ecosystem of "
        "interacting protocols, software layers, network systems, security "
        "mechanisms, storage systems, and application architectures."
    )


# ============================================================
# MAIN PROGRAM
# ============================================================

def main():
    print()
    line("=")
    print("HOW THE WEB WORKS".center(WIDTH))
    print("From networking fundamentals to modern Web architecture".center(WIDTH))
    line("=")

    sections = [
        topic_what_is_the_web,
        topic_client_server,
        topic_ip_addresses,
        topic_ports,
        topic_packets,
        topic_routers,
        topic_mac_addresses,
        topic_dns,
        topic_domains,
        topic_url,
        topic_http,
        topic_http_methods,
        topic_status_codes,
        topic_headers,
        topic_cookies,
        topic_sessions,
        topic_authentication_authorization,
        topic_browser,
        topic_html,
        topic_css,
        topic_javascript,
        topic_dom,
        topic_browser_events,
        topic_api,
        topic_json,
        topic_rest,
        topic_tcp,
        topic_udp,
        topic_tls,
        topic_cryptography,
        topic_http11,
        topic_http2,
        topic_http3,
        topic_caching,
        topic_etag,
        topic_cdn,
        topic_reverse_proxy,
        topic_load_balancer,
        topic_web_server,
        topic_application_server,
        topic_database,
        topic_database_request,
        topic_jwt,
        topic_cors,
        topic_same_origin,
        topic_websockets,
        topic_sse,
        topic_webhooks,
        topic_proxies,
        topic_nat,
        topic_dhcp,
        topic_subnets,
        topic_firewalls,
        topic_network_layers,
        topic_encapsulation,
        topic_navigation_lifecycle,
        topic_dns_simulation,
        topic_http_simulation,
        topic_form_submission,
        topic_file_download,
        topic_image_loading,
        topic_video_streaming,
        topic_auth_flow,
        topic_api_lifecycle,
        topic_security,
        topic_xss,
        topic_sql_injection,
        topic_csrf,
        topic_clickjacking,
        topic_ddos,
        topic_certificates,
        topic_browser_storage,
        topic_service_workers,
        topic_performance,
        topic_compression,
        topic_content_types,
        topic_content_negotiation,
        topic_range_requests,
        topic_latency,
        topic_throughput,
        topic_scalability,
        topic_microservices,
        topic_message_queues,
        topic_distributed_systems,
        topic_reliability,
        topic_observability,
        topic_web_architecture,
        topic_end_to_end,
        topic_rendering_pipeline,
        topic_event_loop,
        topic_async_http,
        topic_spa,
        topic_ssr,
        topic_static_sites,
        topic_serverless,
        topic_object_storage,
        topic_domain_to_server,
        topic_idempotency,
        topic_rate_limiting,
        topic_retries,
        topic_content_delivery,
        topic_cache_hit_miss,
        topic_storage_simulation,
        topic_url_encoding,
        topic_base64,
        topic_dns_security,
        topic_encrypted_dns,
        topic_security_headers,
        topic_advanced_caching,
        topic_last_modified,
        topic_connection_reuse,
        topic_certificate_names,
        topic_hsts,
        topic_cookie_security,
        topic_cors_preflight,
        topic_csp,
        topic_api_authorization,
        topic_api_validation,
        topic_api_versioning,
        topic_http_errors,
        topic_dns_programming,
        topic_socket,
        topic_server_socket,
        topic_client_server_ports,
        topic_host_header,
        topic_sni,
        topic_alpn,
        topic_http2_multiplexing,
        topic_quic_streams,
        topic_connection_migration,
        topic_cache_layers,
        topic_cache_invalidation,
        topic_waterfall,
        topic_third_party,
        topic_accessibility,
        topic_progressive_enhancement,
        topic_web_components,
        topic_privacy,
        topic_cookie_vs_storage,
        topic_edge_computing,
        topic_server_cache,
        topic_connection_pool,
        topic_indexes,
        topic_transactions,
        topic_distributed_cache,
        topic_session_architecture,
        topic_sticky_sessions,
        topic_service_discovery,
        topic_api_gateway,
        topic_database_replication,
        topic_consistency,
        topic_cap,
        topic_websocket_security,
        topic_http_streaming,
        topic_ttfb,
        topic_rendering_comparison,
        topic_application_state,
        topic_frontend_backend,
        topic_browser_sandbox,
        topic_origin_examples,
        topic_request_bodies,
        topic_multipart,
        topic_request_smuggling,
        topic_recursive_resolver,
        topic_authoritative_dns,
        topic_dns_delegation,
        topic_ipv4_ipv6,
        topic_network_calculation,
        topic_redirects,
        topic_http_auth,
        topic_oauth,
        topic_oidc,
        topic_csrf_samesite,
        topic_security_model,
        topic_full_browser_sequence,
        topic_https_importance,
        topic_dns_importance,
        topic_port_importance,
        topic_protocols,
        topic_complete_stack,
    ]

    for function in sections:
        function()
        pause()

    print()
    line("=")
    print("END OF HOW THE WEB WORKS".center(WIDTH))
    line("=")


if __name__ == "__main__":
    main()
```

