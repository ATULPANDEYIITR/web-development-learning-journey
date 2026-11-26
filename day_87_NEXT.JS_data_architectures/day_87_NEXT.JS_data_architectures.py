#!/usr/bin/env python3
"""
Next.js Data Architecture: Server-Side Fetching, Caching,
Revalidation, and Dynamic Rendering.

A standalone simulation of a production-oriented data architecture.
Python 3.10+; standard library only.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Callable, Optional
from collections import defaultdict


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger("next-data-architecture")


class CacheMode(str, Enum):
    CACHE = "cache"
    NO_STORE = "no-store"


class RenderMode(str, Enum):
    STATIC = "static"
    DYNAMIC = "dynamic"
    PARTIAL = "partial"


class CacheState(str, Enum):
    MISS = "miss"
    HIT = "hit"
    STALE = "stale"


class DataAccessError(Exception):
    pass


class ValidationError(ValueError):
    pass


@dataclass(frozen=True)
class Product:
    product_id: int
    name: str
    price: float
    category: str
    stock: int
    version: int = 1

    def __post_init__(self):
        if self.product_id <= 0:
            raise ValidationError("Product ID must be positive.")
        if not self.name.strip():
            raise ValidationError("Product name is required.")
        if self.price < 0:
            raise ValidationError("Price cannot be negative.")
        if self.stock < 0:
            raise ValidationError("Stock cannot be negative.")


@dataclass
class CacheEntry:
    value: Any
    created_at: float
    expires_at: float
    tags: set[str] = field(default_factory=set)
    version: int = 1

    @property
    def is_expired(self) -> bool:
        return time.monotonic() >= self.expires_at


@dataclass
class CacheMetrics:
    hits: int = 0
    misses: int = 0
    stale_hits: int = 0
    writes: int = 0
    invalidations: int = 0
    refresh_failures: int = 0

    @property
    def requests(self) -> int:
        return self.hits + self.misses + self.stale_hits

    @property
    def hit_ratio(self) -> float:
        if not self.requests:
            return 0.0
        return (self.hits + self.stale_hits) / self.requests


class ProductRepository:
    """Simulates a database-backed product repository."""

    def __init__(self):
        self._products: dict[int, Product] = {
            101: Product(101, "Laptop", 75000, "Electronics", 12),
            102: Product(102, "Keyboard", 2500, "Accessories", 45),
            103: Product(103, "Monitor", 18000, "Electronics", 8),
            104: Product(104, "Mouse", 900, "Accessories", 0),
        }

    def get_product(self, product_id: int) -> Product:
        if product_id not in self._products:
            raise DataAccessError(f"Product {product_id} not found.")
        return self._products[product_id]

    def get_all_products(self) -> list[Product]:
        return list(self._products.values())

    def update_product(
        self,
        product_id: int,
        price: Optional[float] = None,
        stock: Optional[int] = None
    ) -> Product:
        current = self.get_product(product_id)

        updated = Product(
            product_id=current.product_id,
            name=current.name,
            price=current.price if price is None else price,
            category=current.category,
            stock=current.stock if stock is None else stock,
            version=current.version + 1
        )

        self._products[product_id] = updated
        return updated


class CacheManager:
    """
    In-memory cache with:
    - TTL expiration
    - Tag-based invalidation
    - Path-based invalidation
    - Stale-while-revalidate behavior
    - Request coalescing
    - Cache metrics

    This is an educational single-process cache, not a distributed
    replacement for Next.js persistent caching.
    """

    def __init__(self):
        self.entries: dict[str, CacheEntry] = {}
        self.tag_index: dict[str, set[str]] = defaultdict(set)
        self.path_index: dict[str, set[str]] = defaultdict(set)
        self.metrics = CacheMetrics()
        self.locks: dict[str, asyncio.Lock] = {}

    @staticmethod
    def make_key(namespace: str, parameters: dict) -> str:
        serialized = json.dumps(
            parameters,
            sort_keys=True,
            separators=(",", ":")
        )
        digest = hashlib.sha256(
            serialized.encode("utf-8")
        ).hexdigest()
        return f"{namespace}:{digest}"

    def get(self, key: str) -> tuple[CacheState, Any]:
        entry = self.entries.get(key)

        if entry is None:
            self.metrics.misses += 1
            return CacheState.MISS, None

        if entry.is_expired:
            self.metrics.stale_hits += 1
            return CacheState.STALE, entry.value

        self.metrics.hits += 1
        return CacheState.HIT, entry.value

    def set(
        self,
        key: str,
        value: Any,
        ttl: float,
        tags: Optional[set[str]] = None,
        paths: Optional[set[str]] = None
    ) -> None:
        if ttl <= 0:
            raise ValidationError("Cache TTL must be positive.")

        tags = tags or set()
        paths = paths or set()

        if any(not tag.strip() for tag in tags):
            raise ValidationError("Cache tags cannot be empty.")

        if any(not path.startswith("/") for path in paths):
            raise ValidationError("Cache paths must start with '/'.")

        old = self.entries.pop(key, None)
        if old:
            for tag in old.tags:
                self.tag_index[tag].discard(key)

        entry = CacheEntry(
            value=value,
            created_at=time.monotonic(),
            expires_at=time.monotonic() + ttl,
            tags=set(tags)
        )

        self.entries[key] = entry

        for tag in tags:
            self.tag_index[tag].add(key)

        for path in paths:
            self.path_index[path].add(key)

        self.metrics.writes += 1

    def invalidate_tag(self, tag: str) -> int:
        keys = set(self.tag_index.get(tag, set()))

        for key in keys:
            self.entries.pop(key, None)

        self.tag_index.pop(tag, None)
        self.metrics.invalidations += len(keys)

        logger.info("Invalidated tag %s: %d entries", tag, len(keys))
        return len(keys)

    def invalidate_path(self, path: str) -> int:
        keys = set(self.path_index.pop(path, set()))

        for key in keys:
            self.entries.pop(key, None)

        self.metrics.invalidations += len(keys)

        logger.info("Invalidated path %s: %d entries", path, len(keys))
        return len(keys)

    async def get_or_load(
        self,
        key: str,
        loader: Callable,
        ttl: float,
        tags: Optional[set[str]] = None,
        paths: Optional[set[str]] = None
    ) -> Any:
        state, value = self.get(key)

        if state == CacheState.HIT:
            return value

        if state == CacheState.STALE:
            # Stale content remains available while a refresh occurs.
            # A real distributed implementation needs shared refresh
            # coordination and durable cache storage.
            if key not in self.locks:
                asyncio.create_task(
                    self._refresh(
                        key, loader, ttl, tags, paths
                    )
                )
            return value

        lock = self.locks.setdefault(key, asyncio.Lock())

        async with lock:
            # Another request may have populated the cache while
            # this request was waiting for the lock.
            state, value = self.get(key)

            if state != CacheState.MISS:
                return value

            value = await loader()

            self.set(
                key,
                value,
                ttl,
                tags=tags,
                paths=paths
            )
            return value

    async def _refresh(
        self,
        key: str,
        loader: Callable,
        ttl: float,
        tags: Optional[set[str]],
        paths: Optional[set[str]]
    ) -> None:
        lock = self.locks.setdefault(key, asyncio.Lock())

        try:
            async with lock:
                current = self.entries.get(key)

                if current is None or not current.is_expired:
                    return

                fresh_value = await loader()

                self.set(
                    key,
                    fresh_value,
                    ttl,
                    tags=tags,
                    paths=paths
                )

                logger.info("Background refresh completed: %s", key)

        except Exception:
            self.metrics.refresh_failures += 1
            logger.exception("Background cache refresh failed: %s", key)

        finally:
            self.locks.pop(key, None)

    def remove_expired(self) -> int:
        expired = [
            key for key, entry in self.entries.items()
            if entry.is_expired
        ]

        for key in expired:
            entry = self.entries.pop(key)
            for tag in entry.tags:
                self.tag_index[tag].discard(key)

        return len(expired)

    def report(self) -> dict:
        return {
            "entries": len(self.entries),
            "hits": self.metrics.hits,
            "misses": self.metrics.misses,
            "stale_hits": self.metrics.stale_hits,
            "writes": self.metrics.writes,
            "invalidations": self.metrics.invalidations,
            "refresh_failures": self.metrics.refresh_failures,
            "hit_ratio": round(self.metrics.hit_ratio, 4)
        }


class DataService:
    """Separates data access from rendering decisions."""

    def __init__(
        self,
        repository: ProductRepository,
        cache: CacheManager
    ):
        self.repository = repository
        self.cache = cache

    async def get_product(
        self,
        product_id: int,
        mode: CacheMode = CacheMode.CACHE
    ) -> Product:
        if product_id <= 0:
            raise ValidationError("Invalid product ID.")

        if mode == CacheMode.NO_STORE:
            return self.repository.get_product(product_id)

        key = self.cache.make_key(
            "product",
            {"id": product_id}
        )

        async def loader():
            await asyncio.sleep(0.02)
            return self.repository.get_product(product_id)

        return await self.cache.get_or_load(
            key=key,
            loader=loader,
            ttl=5,
            tags={f"product:{product_id}", "products"},
            paths={f"/products/{product_id}", "/products"}
        )

    async def get_products(self) -> list[Product]:
        key = self.cache.make_key("products", {"scope": "all"})

        async def loader():
            await asyncio.sleep(0.02)
            return self.repository.get_all_products()

        return await self.cache.get_or_load(
            key,
            loader,
            ttl=10,
            tags={"products"},
            paths={"/products"}
        )

    async def update_product(
        self,
        product_id: int,
        price: Optional[float] = None,
        stock: Optional[int] = None
    ) -> Product:
        # Production systems should authorize the user before mutation.
        updated = self.repository.update_product(
            product_id,
            price,
            stock
        )

        # Invalidate all views that depend on product data.
        self.cache.invalidate_tag(f"product:{product_id}")
        self.cache.invalidate_tag("products")

        return updated


@dataclass
class RenderResult:
    route: str
    mode: RenderMode
    data: Any
    generated_at: float
    personalized: bool = False


class RenderingEngine:
    """
    Demonstrates the distinction between static, dynamic,
    and partially cached server rendering.
    """

    def __init__(self, data_service: DataService):
        self.data_service = data_service

    async def render_product_page(
        self,
        product_id: int,
        authenticated_user: Optional[str] = None
    ) -> RenderResult:

        product = await self.data_service.get_product(product_id)

        if authenticated_user:
            # User-specific information must not be placed in a
            # shared public cache without an appropriate cache key
            # and authorization boundary.
            return RenderResult(
                route=f"/products/{product_id}",
                mode=RenderMode.DYNAMIC,
                data={
                    "product": asdict(product),
                    "user": authenticated_user
                },
                generated_at=time.time(),
                personalized=True
            )

        return RenderResult(
            route=f"/products/{product_id}",
            mode=RenderMode.PARTIAL,
            data=asdict(product),
            generated_at=time.time()
        )


class RepositorySimulator:
    """Models Next.js-style route and data cache relationships."""

    def __init__(self):
        self.cache = CacheManager()
        self.route_generation: dict[str, float] = {}

    def record_route(self, path: str):
        if not path.startswith("/"):
            raise ValidationError("Route must be absolute.")
        self.route_generation[path] = time.time()

    def revalidate_path(self, path: str) -> int:
        self.route_generation.pop(path, None)
        return self.cache.invalidate_path(path)

    def revalidate_tag(self, tag: str) -> int:
        return self.cache.invalidate_tag(tag)


async def run_demonstration():
    print("\nNEXT.JS DATA ARCHITECTURE SIMULATION")
    print("=" * 55)

    repository = ProductRepository()
    cache = CacheManager()
    service = DataService(repository, cache)
    renderer = RenderingEngine(service)

    print("\n1. Initial server-side data fetching")

    product = await service.get_product(101)
    print(json.dumps(asdict(product), indent=2))

    print("\n2. Repeated request and cache hit")

    cached_product = await service.get_product(101)
    print("Product:", cached_product.name)

    print("\n3. Uncached request")

    fresh_product = await service.get_product(
        101,
        CacheMode.NO_STORE
    )
    print("Fresh database result:", fresh_product.version)

    print("\n4. Parallel server-side fetching")

    results = await asyncio.gather(
        service.get_product(101),
        service.get_product(102),
        service.get_products()
    )

    print("Parallel operations completed:", len(results))

    print("\n5. Static versus dynamic rendering")

    static_result = await renderer.render_product_page(101)
    dynamic_result = await renderer.render_product_page(
        101,
        authenticated_user="user-501"
    )

    print("Public route:", static_result.mode.value)
    print("Personalized route:", dynamic_result.mode.value)

    print("\n6. Mutation and tag-based revalidation")

    updated = await service.update_product(
        101,
        price=72000,
        stock=15
    )

    print("Updated version:", updated.version)

    refreshed = await service.get_product(101)
    print("Refreshed price:", refreshed.price)

    print("\n7. Path-based invalidation")

    simulator = RepositorySimulator()
    simulator.record_route("/products")
    simulator.record_route("/products/101")

    simulator.revalidate_path("/products")

    print(
        "Route cache after invalidation:",
        simulator.route_generation
    )

    print("\n8. Cache metrics")

    print(json.dumps(cache.report(), indent=2))

    print("\n9. Validation and failure handling")

    try:
        await service.get_product(-10)
    except ValidationError as exc:
        print("Validation correctly rejected request:", exc)

    try:
        await service.get_product(999)
    except DataAccessError as exc:
        print("Repository error handled:", exc)

    print("\n10. Cache cleanup")

    print("Expired entries removed:", cache.remove_expired())

    print("\nAll demonstrations completed.")


def run_unit_tests():
    """Small deterministic tests for important invariants."""

    repository = ProductRepository()
    cache = CacheManager()

    assert repository.get_product(101).price == 75000

    cache.set(
        "test:1",
        {"value": 10},
        ttl=60,
        tags={"test"},
        paths={"/test"}
    )

    state, value = cache.get("test:1")
    assert state == CacheState.HIT
    assert value["value"] == 10

    assert cache.invalidate_tag("test") == 1

    state, value = cache.get("test:1")
    assert state == CacheState.MISS

    updated = repository.update_product(101, price=70000)
    assert updated.version == 2
    assert updated.price == 70000

    try:
        Product(0, "Invalid", 10, "Test", 1)
        raise AssertionError("Invalid product was accepted.")
    except ValidationError:
        pass

    print("All unit assertions passed.")


if __name__ == "__main__":
    run_unit_tests()
    asyncio.run(run_demonstration())
