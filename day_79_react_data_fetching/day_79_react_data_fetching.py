"""
React Data Fetching: API Integration, Loading States, Errors, and Caching

A self-contained Python implementation demonstrating the data-fetching
lifecycle, HTTP integration, request cancellation, retries, caching,
request deduplication, stale data, and failure handling.

Run:
    python react_data_fetching.py
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Generic, TypeVar
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

logger = logging.getLogger("data_fetching")

T = TypeVar("T")


# ---------------------------------------------------------
# 1. Request states
# ---------------------------------------------------------

class FetchStatus(Enum):
    IDLE = "idle"
    LOADING = "loading"
    SUCCESS = "success"
    ERROR = "error"


@dataclass
class FetchState(Generic[T]):
    status: FetchStatus = FetchStatus.IDLE
    data: T | None = None
    error: str | None = None
    is_fetching: bool = False
    updated_at: float | None = None

    @property
    def is_loading(self) -> bool:
        return self.status == FetchStatus.LOADING

    @property
    def is_error(self) -> bool:
        return self.status == FetchStatus.ERROR

    @property
    def is_success(self) -> bool:
        return self.status == FetchStatus.SUCCESS


# ---------------------------------------------------------
# 2. Custom exceptions
# ---------------------------------------------------------

class FetchError(Exception):
    pass


class NetworkError(FetchError):
    pass


class HTTPResponseError(FetchError):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(message)


class ResponseValidationError(FetchError):
    pass


class RequestCancelled(FetchError):
    pass


# ---------------------------------------------------------
# 3. Request configuration
# ---------------------------------------------------------

@dataclass(frozen=True)
class RequestConfig:
    url: str
    method: str = "GET"
    headers: dict[str, str] = field(default_factory=dict)
    params: dict[str, Any] = field(default_factory=dict)
    timeout: float = 5.0

    def __post_init__(self):
        if not self.url.startswith(("http://", "https://")):
            raise ValueError("Only HTTP and HTTPS URLs are supported.")

        if self.method.upper() not in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
            raise ValueError("Unsupported HTTP method.")

        if self.timeout <= 0:
            raise ValueError("Timeout must be positive.")


# ---------------------------------------------------------
# 4. HTTP transport
# ---------------------------------------------------------

class HTTPClient:

    def request(self, config: RequestConfig) -> Any:
        url = config.url

        if config.params and config.method.upper() == "GET":
            query = urlencode(config.params)
            url += ("&" if "?" in url else "?") + query

        headers = {
            "Accept": "application/json",
            **config.headers
        }

        request = Request(
            url=url,
            headers=headers,
            method=config.method.upper()
        )

        try:
            with urlopen(request, timeout=config.timeout) as response:
                content = response.read()

                if not content:
                    return None

                try:
                    return json.loads(content.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise ResponseValidationError(
                        "Server returned invalid JSON."
                    ) from exc

        except HTTPError as exc:
            message = exc.read().decode("utf-8", errors="replace")[:300]
            raise HTTPResponseError(
                exc.code,
                f"HTTP {exc.code}: {message}"
            ) from exc

        except (URLError, TimeoutError, OSError) as exc:
            raise NetworkError(str(exc)) from exc


# ---------------------------------------------------------
# 5. Cache implementation
# ---------------------------------------------------------

@dataclass
class CacheEntry:
    data: Any
    created_at: float
    expires_at: float


class QueryCache:

    def __init__(
        self,
        ttl: float = 30.0,
        max_entries: int = 100
    ):
        if ttl < 0 or max_entries < 1:
            raise ValueError("Invalid cache configuration.")

        self.ttl = ttl
        self.max_entries = max_entries
        self.entries: OrderedDict[str, CacheEntry] = OrderedDict()

    def get(self, key: str) -> Any | None:
        entry = self.entries.get(key)

        if entry is None:
            return None

        if time.monotonic() >= entry.expires_at:
            del self.entries[key]
            return None

        self.entries.move_to_end(key)
        return entry.data

    def set(self, key: str, data: Any) -> None:
        now = time.monotonic()

        self.entries[key] = CacheEntry(
            data=data,
            created_at=now,
            expires_at=now + self.ttl
        )

        self.entries.move_to_end(key)

        while len(self.entries) > self.max_entries:
            self.entries.popitem(last=False)

    def invalidate(self, key: str | None = None) -> None:
        if key is None:
            self.entries.clear()
        else:
            self.entries.pop(key, None)

    def contains(self, key: str) -> bool:
        return self.get(key) is not None


# ---------------------------------------------------------
# 6. Request manager
# ---------------------------------------------------------

class DataFetcher:

    def __init__(
        self,
        transport: HTTPClient | None = None,
        cache: QueryCache | None = None
    ):
        self.transport = transport or HTTPClient()
        self.cache = cache or QueryCache()

        self.states: dict[str, FetchState] = {}
        self.in_flight: dict[str, asyncio.Task] = {}
        self.listeners: dict[str, list[Callable]] = {}

    @staticmethod
    def create_key(config: RequestConfig) -> str:
        return json.dumps(
            {
                "url": config.url,
                "method": config.method.upper(),
                "params": config.params
            },
            sort_keys=True,
            default=str
        )

    def get_state(self, key: str) -> FetchState:
        return self.states.setdefault(key, FetchState())

    def subscribe(
        self,
        key: str,
        callback: Callable[[FetchState], None]
    ) -> Callable[[], None]:

        self.listeners.setdefault(key, []).append(callback)

        def unsubscribe():
            if callback in self.listeners.get(key, []):
                self.listeners[key].remove(callback)

        return unsubscribe

    def _notify(self, key: str) -> None:
        state = self.get_state(key)

        for callback in list(self.listeners.get(key, [])):
            try:
                callback(state)
            except Exception:
                logger.exception("Subscriber callback failed.")

    async def _execute(
        self,
        config: RequestConfig,
        key: str
    ) -> Any:

        loop = asyncio.get_running_loop()

        return await loop.run_in_executor(
            None,
            self.transport.request,
            config
        )

    async def fetch(
        self,
        config: RequestConfig,
        force: bool = False,
        retries: int = 2,
        retry_delay: float = 0.2
    ) -> Any:

        if retries < 0 or retry_delay < 0:
            raise ValueError("Invalid retry configuration.")

        key = self.create_key(config)
        state = self.get_state(key)

        cached = self.cache.get(key)

        if cached is not None and not force:
            state.status = FetchStatus.SUCCESS
            state.data = cached
            state.error = None
            state.is_fetching = False
            self._notify(key)
            return cached

        if key in self.in_flight:
            return await self.in_flight[key]

        state.status = FetchStatus.LOADING
        state.is_fetching = True
        state.error = None
        self._notify(key)

        async def execute_with_retry():

            last_error = None

            for attempt in range(retries + 1):
                try:
                    result = await self._execute(config, key)

                    state.status = FetchStatus.SUCCESS
                    state.data = result
                    state.error = None
                    state.is_fetching = False
                    state.updated_at = time.time()

                    self.cache.set(key, result)
                    return result

                except (NetworkError, HTTPResponseError, FetchError) as exc:
                    last_error = exc

                    # Client errors are normally not transient.
                    if (
                        isinstance(exc, HTTPResponseError)
                        and 400 <= exc.status_code < 500
                        and exc.status_code != 429
                    ):
                        break

                    if attempt < retries:
                        await asyncio.sleep(
                            retry_delay * (2 ** attempt)
                        )

            state.status = FetchStatus.ERROR
            state.error = str(last_error)
            state.is_fetching = False

            raise last_error

        task = asyncio.create_task(execute_with_retry())
        self.in_flight[key] = task

        self._notify(key)

        try:
            return await task

        except Exception:
            raise

        finally:
            if self.in_flight.get(key) is task:
                del self.in_flight[key]

            self._notify(key)

    def invalidate(self, config: RequestConfig | None = None):
        if config is None:
            self.cache.invalidate()
        else:
            self.cache.invalidate(self.create_key(config))


# ---------------------------------------------------------
# 7. Stale-while-revalidate cache
# ---------------------------------------------------------

class StaleQueryCache:

    def __init__(self, stale_time: float = 30.0):
        self.stale_time = stale_time
        self.data: dict[str, tuple[Any, float]] = {}

    def read(self, key: str) -> tuple[Any | None, bool]:
        entry = self.data.get(key)

        if entry is None:
            return None, True

        value, timestamp = entry

        is_stale = (
            time.monotonic() - timestamp > self.stale_time
        )

        return value, is_stale

    def write(self, key: str, value: Any):
        self.data[key] = (value, time.monotonic())


# ---------------------------------------------------------
# 8. Simulated API for deterministic demonstrations
# ---------------------------------------------------------

class MockAPI(HTTPClient):

    def __init__(self):
        self.calls = 0

        self.users = [
            {"id": 1, "name": "Aarav", "role": "Developer"},
            {"id": 2, "name": "Meera", "role": "Reviewer"},
            {"id": 3, "name": "Rohan", "role": "Administrator"}
        ]

    def request(self, config: RequestConfig) -> Any:
        self.calls += 1

        if "/users" in config.url:
            return self.users

        if "/failure" in config.url:
            raise HTTPResponseError(503, "Service unavailable")

        if "/empty" in config.url:
            return []

        raise HTTPResponseError(404, "Endpoint not found")


# ---------------------------------------------------------
# 9. Application workflow
# ---------------------------------------------------------

async def main():

    print("\nREACT DATA FETCHING SIMULATION")
    print("=" * 45)

    api = MockAPI()

    fetcher = DataFetcher(
        transport=api,
        cache=QueryCache(ttl=10, max_entries=20)
    )

    config = RequestConfig(
        url="https://api.example.com/users"
    )

    key = fetcher.create_key(config)

    # Observe loading, success, and error transitions.
    unsubscribe = fetcher.subscribe(
        key,
        lambda state: print(
            f"State: {state.status.value}, "
            f"Fetching: {state.is_fetching}"
        )
    )

    print("\n1. Initial API request")

    users = await fetcher.fetch(config)

    for user in users:
        print(user)

    print("\n2. Cached request")

    cached_users = await fetcher.fetch(config)

    print("Returned records:", len(cached_users))
    print("Actual HTTP calls:", api.calls)

    print("\n3. Forced refresh")

    await fetcher.fetch(config, force=True)

    print("Actual HTTP calls:", api.calls)

    print("\n4. Concurrent request deduplication")

    fetcher.invalidate(config)

    first, second = await asyncio.gather(
        fetcher.fetch(config),
        fetcher.fetch(config)
    )

    print("Same result:", first == second)
    print("Actual HTTP calls:", api.calls)

    print("\n5. Empty response handling")

    empty_config = RequestConfig(
        url="https://api.example.com/empty"
    )

    empty_result = await fetcher.fetch(empty_config)

    print("Empty list:", empty_result)
    print("Empty response is valid data.")

    print("\n6. Error handling")

    failure_config = RequestConfig(
        url="https://api.example.com/failure"
    )

    try:
        await fetcher.fetch(
            failure_config,
            retries=1,
            retry_delay=0.01
        )
    except FetchError as exc:
        error_state = fetcher.get_state(
            fetcher.create_key(failure_config)
        )

        print("Caught:", exc)
        print("Error state:", error_state.status.value)

    print("\n7. Stale cache")

    stale_cache = StaleQueryCache(stale_time=10)

    stale_cache.write("users", users)

    data, is_stale = stale_cache.read("users")

    print("Cached data available:", data is not None)
    print("Is stale:", is_stale)

    # An empty array is a successful response, not an error.
    assert empty_result == []
    assert fetcher.get_state(key).status == FetchStatus.SUCCESS

    unsubscribe()

    print("\nAll demonstrations completed successfully.")


if __name__ == "__main__":
    asyncio.run(main())
