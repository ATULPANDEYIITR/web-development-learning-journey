from __future__ import annotations

from dataclasses import dataclass, field
from http.cookies import SimpleCookie
from typing import Dict, List, Optional
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


class StorageError(Exception):
    """Raised when browser-like storage operations are invalid."""


class CookieError(Exception):
    """Raised when cookie operations violate validation rules."""


@dataclass
class StorageArea:
    """A small browser-storage model with string-only keys and values."""

    name: str
    quota: int = 4096
    _data: Dict[str, str] = field(default_factory=dict)

    def _validate(self, key: str, value: Optional[str] = None) -> None:
        if not isinstance(key, str) or not key:
            raise StorageError(f"{self.name}: key must be a non-empty string")
        if value is not None and not isinstance(value, str):
            raise StorageError(f"{self.name}: value must be a string")

    def _size(self) -> int:
        return sum(len(k) + len(v) for k, v in self._data.items())

    def set_item(self, key: str, value: str) -> None:
        self._validate(key, value)
        old = self._data.get(key)
        old_size = len(key) + len(old) if old is not None else 0
        new_size = self._size() - old_size + len(key) + len(value)

        if new_size > self.quota:
            raise StorageError(
                f"{self.name}: quota exceeded ({new_size}/{self.quota} characters)"
            )

        self._data[key] = value

    def get_item(self, key: str) -> Optional[str]:
        self._validate(key)
        return self._data.get(key)

    def remove_item(self, key: str) -> None:
        self._validate(key)
        self._data.pop(key, None)

    def clear(self) -> None:
        self._data.clear()

    def keys(self) -> List[str]:
        return list(self._data.keys())

    def __len__(self) -> int:
        return len(self._data)


@dataclass
class Cookie:
    name: str
    value: str
    path: str = "/"
    secure: bool = True
    http_only: bool = True
    same_site: str = "Lax"
    max_age: Optional[int] = None

    def serialize(self) -> str:
        if not self.name:
            raise CookieError("Cookie name cannot be empty")
        if self.path != "/" and not self.path.startswith("/"):
            raise CookieError("Cookie path must start with '/'")
        if self.same_site not in {"Strict", "Lax", "None"}:
            raise CookieError("same_site must be Strict, Lax, or None")
        if self.same_site == "None" and not self.secure:
            raise CookieError("SameSite=None requires Secure in modern browsers")
        if self.max_age is not None and self.max_age < 0:
            raise CookieError("max_age cannot be negative")

        parts = [f"{self.name}={self.value}", f"Path={self.path}"]
        if self.secure:
            parts.append("Secure")
        if self.http_only:
            parts.append("HttpOnly")
        parts.append(f"SameSite={self.same_site}")
        if self.max_age is not None:
            parts.append(f"Max-Age={self.max_age}")
        return "; ".join(parts)


class CookieJar:
    """Simplified cookie jar for demonstrating cookie state and attributes."""

    def __init__(self) -> None:
        self._cookies: Dict[str, Cookie] = {}

    def set_cookie(self, cookie: Cookie) -> str:
        serialized = cookie.serialize()
        self._cookies[cookie.name] = cookie
        return serialized

    def get_cookie_header(self) -> str:
        return "; ".join(
            f"{cookie.name}={cookie.value}" for cookie in self._cookies.values()
        )

    def delete_cookie(self, name: str) -> None:
        if name:
            self._cookies.pop(name, None)


class BrowserHistory:
    """Models pushState, replaceState, back, forward, and history length."""

    def __init__(self, initial_url: str) -> None:
        self._validate_url(initial_url)
        self._entries = [initial_url]
        self._index = 0

    @staticmethod
    def _validate_url(url: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("History URLs must be absolute HTTP(S) URLs")

    def push_state(self, url: str) -> None:
        self._validate_url(url)
        self._entries = self._entries[: self._index + 1]
        self._entries.append(url)
        self._index += 1

    def replace_state(self, url: str) -> None:
        self._validate_url(url)
        self._entries[self._index] = url

    def back(self) -> str:
        if self._index > 0:
            self._index -= 1
        return self.current

    def forward(self) -> str:
        if self._index + 1 < len(self._entries):
            self._index += 1
        return self.current

    @property
    def current(self) -> str:
        return self._entries[self._index]

    @property
    def length(self) -> int:
        return len(self._entries)


class URLModel:
    """URL API operations using urllib.parse."""

    def __init__(self, raw_url: str) -> None:
        parsed = urlparse(raw_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("URL must be an absolute HTTP(S) URL")
        self._parts = parsed

    @property
    def href(self) -> str:
        return urlunparse(self._parts)

    @property
    def origin(self) -> str:
        return f"{self._parts.scheme}://{self._parts.netloc}"

    @property
    def pathname(self) -> str:
        return self._parts.path or "/"

    @property
    def search_params(self) -> Dict[str, List[str]]:
        result: Dict[str, List[str]] = {}
        for key, value in parse_qsl(self._parts.query, keep_blank_values=True):
            result.setdefault(key, []).append(value)
        return result

    def set_query_parameter(self, key: str, value: str) -> None:
        if not key:
            raise ValueError("Query parameter name cannot be empty")

        pairs = parse_qsl(self._parts.query, keep_blank_values=True)
        pairs = [(k, v) for k, v in pairs if k != key]
        pairs.append((key, value))
        self._parts = self._parts._replace(query=urlencode(pairs))

    def remove_query_parameter(self, key: str) -> None:
        pairs = parse_qsl(self._parts.query, keep_blank_values=True)
        self._parts = self._parts._replace(
            query=urlencode([(k, v) for k, v in pairs if k != key])
        )


def demonstrate_url_api() -> None:
    url = URLModel("https://example.test/products?page=2&sort=price")
    print("URL origin:", url.origin)
    print("URL path:", url.pathname)
    print("Initial parameters:", url.search_params)

    url.set_query_parameter("filter", "available")
    url.remove_query_parameter("sort")
    print("Updated URL:", url.href)


def demonstrate_storage() -> None:
    local = StorageArea("localStorage", quota=100)
    session = StorageArea("sessionStorage", quota=100)

    local.set_item("theme", "dark")
    local.set_item("language", "en")
    session.set_item("checkoutStep", "payment")

    print("localStorage keys:", local.keys())
    print("theme:", local.get_item("theme"))
    print("sessionStorage checkoutStep:", session.get_item("checkoutStep"))

    local.remove_item("language")

    try:
        local.set_item("large", "x" * 200)
    except StorageError as exc:
        print("Expected storage failure:", exc)


def demonstrate_cookies() -> None:
    jar = CookieJar()

    session_cookie = Cookie(
        name="session_id",
        value="opaque-server-generated-value",
        secure=True,
        http_only=True,
        same_site="Lax",
    )

    preference_cookie = Cookie(
        name="consent",
        value="essential",
        secure=True,
        http_only=False,
        same_site="Lax",
        max_age=86400,
    )

    print("Set-Cookie:", jar.set_cookie(session_cookie))
    print("Set-Cookie:", jar.set_cookie(preference_cookie))
    print("Request Cookie header:", jar.get_cookie_header())

    jar.delete_cookie("consent")
    print("After deletion:", jar.get_cookie_header())


def demonstrate_history() -> None:
    history = BrowserHistory("https://example.test/dashboard")
    history.push_state("https://example.test/dashboard?tab=activity")
    history.push_state("https://example.test/dashboard?tab=settings")

    print("History length:", history.length)
    print("Current URL:", history.current)
    print("Back:", history.back())
    print("Forward:", history.forward())

    history.replace_state("https://example.test/dashboard?tab=security")
    print("After replaceState:", history.current)


def run_assertions() -> None:
    storage = StorageArea("test", quota=50)
    storage.set_item("a", "1")
    assert storage.get_item("a") == "1"

    url = URLModel("https://example.test/search?q=browser")
    url.set_query_parameter("page", "3")
    assert url.search_params["page"] == ["3"]

    history = BrowserHistory("https://example.test/")
    history.push_state("https://example.test/a")
    assert history.back() == "https://example.test/"
    assert history.forward() == "https://example.test/a"

    try:
        URLModel("javascript:alert(1)")
    except ValueError:
        pass
    else:
        raise AssertionError("Unsafe URL scheme was accepted")

    print("Assertions passed.")


if __name__ == "__main__":
    print("=== URL API ===")
    demonstrate_url_api()

    print("\n=== localStorage / sessionStorage ===")
    demonstrate_storage()

    print("\n=== Cookies ===")
    demonstrate_cookies()

    print("\n=== History API ===")
    demonstrate_history()

    print("\n=== Validation ===")
    run_assertions()
