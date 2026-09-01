# ============================================================
# DAY 00: INTERNET AND WEB FUNDAMENTALS
# ============================================================

print("DAY 01 - INTERNET AND WEB FUNDAMENTALS")


# ============================================================
# 1. WHAT IS THE INTERNET?
# ============================================================

print("\n1. WHAT IS THE INTERNET?")

print("The Internet is a global network of interconnected")
print("computers and devices that communicate using standard")
print("networking protocols.")


# ============================================================
# 2. INTERNET VS WORLD WIDE WEB
# ============================================================

print("\n2. INTERNET VS WORLD WIDE WEB")

internet = "Global network infrastructure"
web = "System of websites and web resources accessed through the Internet"

print("Internet:", internet)
print("World Wide Web:", web)

print("\nThe Web is a service that operates over the Internet.")


# ============================================================
# 3. CLIENT AND SERVER
# ============================================================

print("\n3. CLIENT AND SERVER")

client = "Web Browser"
server = "Web Server"

print("Client:", client)
print("Server:", server)

print("\nBasic communication:")
print("Client -> Request -> Server")
print("Client <- Response <- Server")


# ============================================================
# 4. WEBSITE AND WEB APPLICATION
# ============================================================

print("\n4. WEBSITE AND WEB APPLICATION")

website = "Primarily provides information or content"
web_application = "Allows users to perform actions and interact with data"

print("Website:", website)
print("Web Application:", web_application)


# ============================================================
# 5. IP ADDRESS
# ============================================================

print("\n5. IP ADDRESS")

ip_address = "192.168.1.10"

print("Example IP Address:", ip_address)

print("\nAn IP address identifies a device or network interface")
print("within an IP network.")


# ============================================================
# 6. DOMAIN NAME
# ============================================================

print("\n6. DOMAIN NAME")

domain = "example.com"

print("Domain:", domain)

print("\nDomain names provide human-readable names")
print("for Internet resources.")


# ============================================================
# 7. DNS
# ============================================================

print("\n7. DOMAIN NAME SYSTEM (DNS)")

domain = "example.com"
ip_address = "93.184.216.34"

print("Domain:", domain)
print("Resolved IP:", ip_address)

print("\nDNS translates domain names into IP addresses")
print("that computers can use for communication.")


# ============================================================
# 8. URL
# ============================================================

print("\n8. URL")

url = "https://example.com/products?id=10"

print("URL:", url)

url_parts = {
    "Protocol": "https",
    "Domain": "example.com",
    "Path": "/products",
    "Query": "id=10"
}

for part, value in url_parts.items():
    print(part, "->", value)


# ============================================================
# 9. HTTP AND HTTPS
# ============================================================

print("\n9. HTTP AND HTTPS")

print("HTTP  -> Hypertext Transfer Protocol")
print("HTTPS -> HTTP secured using TLS")

print("\nHTTPS helps protect data exchanged between")
print("a client and server from interception and tampering.")


# ============================================================
# 10. HTTP METHODS
# ============================================================

print("\n10. HTTP METHODS")

http_methods = {
    "GET": "Retrieve data",
    "POST": "Create or submit data",
    "PUT": "Replace or update data",
    "PATCH": "Partially update data",
    "DELETE": "Delete data"
}

for method, purpose in http_methods.items():
    print(method, "->", purpose)


# ============================================================
# 11. HTTP STATUS CODES
# ============================================================

print("\n11. HTTP STATUS CODES")

status_codes = {
    200: "OK",
    201: "Created",
    301: "Moved Permanently",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    500: "Internal Server Error"
}

for code, meaning in status_codes.items():
    print(code, "->", meaning)


# ============================================================
# 12. HTML
# ============================================================

print("\n12. HTML")

html = """
<h1>Welcome</h1>
<p>This is a web page.</p>
"""

print(html)

print("HTML defines the structure and content of web pages.")


# ============================================================
# 13. CSS
# ============================================================

print("\n13. CSS")

css = """
h1 {
    font-size: 32px;
}
"""

print(css)

print("CSS controls the presentation and visual styling")
print("of web pages.")


# ============================================================
# 14. JAVASCRIPT
# ============================================================

print("\n14. JAVASCRIPT")

javascript = """
function greet() {
    console.log("Hello");
}
"""

print(javascript)

print("JavaScript adds behavior and interactivity")
print("to web pages and applications.")


# ============================================================
# 15. API
# ============================================================

print("\n15. API")

api_request = {
    "method": "GET",
    "endpoint": "/users",
    "parameter": "id=10"
}

print("API Request:")

for key, value in api_request.items():
    print(key, "->", value)

print("\nAn API provides a defined way for software")
print("components to communicate with each other.")


# ============================================================
# 16. COOKIES AND SESSIONS
# ============================================================

print("\n16. COOKIES AND SESSIONS")

cookie = {
    "name": "session_id",
    "value": "abc123"
}

session = {
    "user": "Atul",
    "authenticated": True
}

print("Cookie:", cookie)
print("Session:", session)

print("\nCookies can store information in the browser.")
print("Sessions allow applications to maintain user state.")


# ============================================================
# 17. FRONTEND AND BACKEND
# ============================================================

print("\n17. FRONTEND AND BACKEND")

frontend = [
    "HTML",
    "CSS",
    "JavaScript",
    "User Interface"
]

backend = [
    "Server",
    "Business Logic",
    "Database",
    "API"
]

print("Frontend:")

for item in frontend:
    print("-", item)

print("\nBackend:")

for item in backend:
    print("-", item)


# ============================================================
# 18. WEB REQUEST FLOW
# ============================================================

print("\n18. WEB REQUEST FLOW")

print("""
User
  ↓
Web Browser
  ↓
DNS
  ↓
Internet
  ↓
Web Server
  ↓
Application
  ↓
Database
  ↓
Response
  ↓
Web Browser
  ↓
User
""")


# ============================================================
# 19. BASIC NETWORKING PROTOCOLS
# ============================================================

print("\n19. BASIC NETWORKING PROTOCOLS")

protocols = {
    "HTTP/HTTPS": "Web communication",
    "DNS": "Domain name resolution",
    "TCP": "Reliable transport",
    "IP": "Addressing and packet routing",
    "SSH": "Secure remote access",
    "SMTP": "Email transmission"
}

for protocol, purpose in protocols.items():
    print(protocol, "->", purpose)


# ============================================================
# 20. WEB SECURITY BASICS
# ============================================================

print("\n20. WEB SECURITY BASICS")

security_concepts = [
    "HTTPS/TLS",
    "Authentication",
    "Authorization",
    "Input Validation",
    "Secure Password Storage",
    "Access Control",
    "Session Security"
]

for concept in security_concepts:
    print("-", concept)


# ============================================================
# 21. COMMON WEB CONCEPTS
# ============================================================

print("\n21. COMMON WEB CONCEPTS")

concepts = [
    "Browser",
    "Web Server",
    "Domain",
    "DNS",
    "IP Address",
    "URL",
    "HTTP",
    "HTTPS",
    "API",
    "Frontend",
    "Backend",
    "Database",
    "Cookie",
    "Session"
]

for concept in concepts:
    print("-", concept)


# ============================================================
# SUMMARY
# ============================================================

print("\n" + "=" * 60)
print("DAY 01 COMPLETED")
print("=" * 60)

print("""
Today you learned:

1. Internet
2. World Wide Web
3. Client and Server
4. Websites and Web Applications
5. IP Addresses
6. Domain Names
7. DNS
8. URLs
9. HTTP and HTTPS
10. HTTP Methods
11. HTTP Status Codes
12. HTML
13. CSS
14. JavaScript
15. APIs
16. Cookies and Sessions
17. Frontend and Backend
18. Web Request Flow
19. Networking Protocols
20. Web Security Basics
21. Common Web Concepts
""")

