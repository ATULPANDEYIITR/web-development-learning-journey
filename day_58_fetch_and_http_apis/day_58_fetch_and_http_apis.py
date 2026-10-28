#!/usr/bin/env python3

"""
Fetch and HTTP APIs: a self-contained HTTP client and request-lifecycle model.

The implementation uses only Python's standard library. It demonstrates:
- HTTP methods and request construction
- headers and JSON payloads
- status-code classification
- response parsing and validation
- timeouts and retries
- authentication-header handling
- request/response lifecycle tracking
- local mock HTTP server for executable examples
"""

from __future__ import annotations

import json
import logging
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)


class HttpMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


class RequestPhase(str, Enum):
    CREATED = "created"
    SENT = "sent"
    RECEIVED = "received"
    FAILED = "failed"


@dataclass(frozen=True)
class ApiRequest:
    method: HttpMethod
    url: str
    headers: dict[str, str] = field(default_factory=dict)
    query: dict[str, str] = field(default_factory=dict)
    json_body: dict[str, Any] | list[Any] | None = None

    def validate(self) -> None:
        parsed = urlparse(self.url)
        if parsed.scheme not in {"http", "https"}:
            raise ValueError("URL must use HTTP or HTTPS")
        if not parsed.netloc:
            raise ValueError("URL must contain a host")

        for name, value in self.headers.items():
            if not name.strip():
                raise ValueError("Header names cannot be empty")
            if "\r" in name or "\n" in name or "\r" in value or "\n" in value:
                raise ValueError("CR/LF characters are forbidden in headers")

        if self.method in {HttpMethod.GET, HttpMethod.DELETE} and self.json_body is not None:
            raise ValueError(f"{self.method.value} requests should not contain this JSON body")


@dataclass
class ApiResponse:
    status_code: int
    reason: str
    headers: dict[str, str]
    body: bytes
    elapsed_seconds: float
    phase: RequestPhase

    @property
    def text(self) -> str:
        return self.body.decode("utf-8", errors="replace")

    @property
    def is_success(self) -> bool:
        return 200 <= self.status_code < 300

    def json(self) -> Any:
        content_type = self.headers.get("Content-Type", "")
        if "application/json" not in content_type:
            raise ValueError("Response is not declared as JSON")
        return json.loads(self.body.decode("utf-8"))


class ApiError(Exception):
    """Base API client exception."""


class ApiTransportError(ApiError):
    """Raised when an HTTP request cannot reach its destination."""


class ApiStatusError(ApiError):
    """Raised for an unexpected HTTP status."""

    def __init__(self, response: ApiResponse):
        super().__init__(f"HTTP {response.status_code} {response.reason}")
        self.response = response


class ApiClient:
    RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504}

    def __init__(
        self,
        *,
        timeout: float = 5.0,
        max_retries: int = 2,
        user_agent: str = "FetchHttpLearningClient/1.0",
    ) -> None:
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        if max_retries < 0:
            raise ValueError("max_retries cannot be negative")

        self.timeout = timeout
        self.max_retries = max_retries
        self.user_agent = user_agent

    def request(self, api_request: ApiRequest) -> ApiResponse:
        api_request.validate()

        headers = {
            "Accept": "application/json",
            "User-Agent": self.user_agent,
            **api_request.headers,
        }

        url = api_request.url
        if api_request.query:
            separator = "&" if "?" in url else "?"
            url += separator + urlencode(api_request.query)

        body: bytes | None = None
        if api_request.json_body is not None:
            body = json.dumps(
                api_request.json_body,
                separators=(",", ":"),
                ensure_ascii=False,
            ).encode("utf-8")
            headers.setdefault("Content-Type", "application/json")

        attempt = 0

        while True:
            attempt += 1
            started = time.monotonic()

            request = Request(
                url=url,
                data=body,
                headers=headers,
                method=api_request.method.value,
            )

            try:
                with urlopen(request, timeout=self.timeout) as raw:
                    response = ApiResponse(
                        status_code=raw.status,
                        reason=raw.reason,
                        headers=dict(raw.headers.items()),
                        body=raw.read(),
                        elapsed_seconds=time.monotonic() - started,
                        phase=RequestPhase.RECEIVED,
                    )

                if (
                    response.status_code in self.RETRYABLE_STATUS_CODES
                    and attempt <= self.max_retries
                ):
                    self._sleep_before_retry(attempt)
                    continue

                return response

            except HTTPError as exc:
                response = ApiResponse(
                    status_code=exc.code,
                    reason=exc.reason or "",
                    headers=dict(exc.headers.items()) if exc.headers else {},
                    body=exc.read(),
                    elapsed_seconds=time.monotonic() - started,
                    phase=RequestPhase.RECEIVED,
                )

                if (
                    exc.code in self.RETRYABLE_STATUS_CODES
                    and attempt <= self.max_retries
                ):
                    self._sleep_before_retry(attempt)
                    continue

                return response

            except (URLError, TimeoutError, OSError) as exc:
                if attempt <= self.max_retries:
                    self._sleep_before_retry(attempt)
                    continue
                raise ApiTransportError(str(exc)) from exc

    def _sleep_before_retry(self, attempt: int) -> None:
        delay = min(2 ** (attempt - 1) * 0.1, 2.0)
        logging.warning("Retrying request after %.2f seconds", delay)
        time.sleep(delay)

    def request_json(self, api_request: ApiRequest) -> Any:
        response = self.request(api_request)

        if not response.is_success:
            raise ApiStatusError(response)

        return response.json()


class DemoHandler(BaseHTTPRequestHandler):
    """Small local API so the script is runnable without an external service."""

    server_version = "FetchDemo/1.0"

    def _send_json(self, status: int, payload: Any) -> None:
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _read_json(self) -> Any:
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length > 1_000_000:
            raise ValueError("Request body exceeds 1 MB")
        raw = self.rfile.read(content_length)
        return json.loads(raw.decode("utf-8")) if raw else None

    def do_GET(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path == "/users":
            self._send_json(
                200,
                {
                    "users": [
                        {"id": 1, "name": "Anita"},
                        {"id": 2, "name": "Rahul"},
                    ]
                },
            )
            return

        if parsed.path == "/health":
            self._send_json(200, {"status": "ok"})
            return

        self._send_json(404, {"error": "resource_not_found"})

    def do_POST(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path != "/users":
            self._send_json(404, {"error": "resource_not_found"})
            return

        try:
            payload = self._read_json()
        except (ValueError, json.JSONDecodeError):
            self._send_json(400, {"error": "invalid_json"})
            return

        if not isinstance(payload, dict) or not payload.get("name"):
            self._send_json(422, {"error": "name_is_required"})
            return

        self._send_json(
            201,
            {
                "id": 3,
                "name": payload["name"],
                "created": True,
            },
        )

    def do_DELETE(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path.startswith("/users/"):
            self._send_json(204, None)
            return
        self._send_json(404, {"error": "resource_not_found"})

    def log_message(self, format: str, *args: Any) -> None:
        logging.debug(format, *args)


def run_demo_server() -> tuple[ThreadingHTTPServer, threading.Thread]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), DemoHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def demonstrate_request_lifecycle(base_url: str) -> None:
    client = ApiClient(timeout=3, max_retries=1)

    get_request = ApiRequest(
        method=HttpMethod.GET,
        url=f"{base_url}/users",
        query={"active": "true"},
        headers={"X-Request-ID": "demo-001"},
    )

    response = client.request(get_request)
    print("GET")
    print("status:", response.status_code)
    print("content type:", response.headers.get("Content-Type"))
    print("body:", response.json())
    print("elapsed:", round(response.elapsed_seconds, 6), "seconds")

    post_request = ApiRequest(
        method=HttpMethod.POST,
        url=f"{base_url}/users",
        headers={"X-Request-ID": "demo-002"},
        json_body={"name": "Priya"},
    )

    created = client.request_json(post_request)
    print("\nPOST")
    print("created:", created)

    invalid_request = ApiRequest(
        method=HttpMethod.POST,
        url=f"{base_url}/users",
        json_body={"name": ""},
    )

    invalid_response = client.request(invalid_request)
    print("\nValidation failure response")
    print("status:", invalid_response.status_code)
    print("body:", invalid_response.json())

    missing_request = ApiRequest(
        method=HttpMethod.GET,
        url=f"{base_url}/missing",
    )

    missing_response = client.request(missing_request)
    print("\nNot found")
    print("status:", missing_response.status_code)
    print("body:", missing_response.json())

    delete_request = ApiRequest(
        method=HttpMethod.DELETE,
        url=f"{base_url}/users/3",
    )

    delete_response = client.request(delete_request)
    print("\nDELETE")
    print("status:", delete_response.status_code)


def demonstrate_validation() -> None:
    invalid = ApiRequest(
        method=HttpMethod.GET,
        url="ftp://example.com/resource",
    )

    try:
        invalid.validate()
    except ValueError as exc:
        print("\nValidation caught:", exc)

    try:
        ApiRequest(
            method=HttpMethod.GET,
            url="http://example.com",
            headers={"X-Bad": "safe\r\nInjected: value"},
        ).validate()
    except ValueError as exc:
        print("Header injection prevented:", exc)


def main() -> None:
    server, _ = run_demo_server()
    host, port = server.server_address
    base_url = f"http://{host}:{port}"

    try:
        print("Local API:", base_url)
        demonstrate_request_lifecycle(base_url)
        demonstrate_validation()
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
