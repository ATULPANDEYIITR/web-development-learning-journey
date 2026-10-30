#!/usr/bin/env python3
"""
API-powered operational dashboard.

Demonstrates asynchronous API retrieval, input validation, retries,
TTL caching, stale-data fallback, independent resource loading,
dashboard state management, and atomic JSON export.

Requires Python 3.10 or later. Uses only the standard library.
"""

from __future__ import annotations

import asyncio
import json
import math
import os
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable


class DashboardError(Exception):
    """Base exception for dashboard operations."""


class ApiError(DashboardError):
    """Raised when an API request fails."""


class ValidationError(DashboardError):
    """Raised when an API payload violates the expected contract."""


class DashboardPhase(str, Enum):
    IDLE = "IDLE"
    LOADING = "LOADING"
    READY = "READY"
    DEGRADED = "DEGRADED"
    ERROR = "ERROR"


class ServiceStatus(str, Enum):
    OPERATIONAL = "OPERATIONAL"
    DEGRADED = "DEGRADED"
    DOWN = "DOWN"


@dataclass(frozen=True)
class Metric:
    name: str
    value: float
    unit: str
    observed_at: datetime


@dataclass(frozen=True)
class Service:
    service_id: str
    name: str
    status: ServiceStatus
    region: str


@dataclass(frozen=True)
class Incident:
    incident_id: str
    service_id: str
    severity: str
    title: str
    status: str
    opened_at: datetime


@dataclass(frozen=True)
class CacheEntry:
    value: list[dict[str, Any]]
    fetched_at: datetime


@dataclass(frozen=True)
class ResourceResult:
    data: list[Any]
    stale: bool = False
    error: str | None = None


@dataclass
class DashboardSnapshot:
    phase: DashboardPhase = DashboardPhase.IDLE
    metrics: list[Metric] = field(default_factory=list)
    services: list[Service] = field(default_factory=list)
    incidents: list[Incident] = field(default_factory=list)
    stale_resources: list[str] = field(default_factory=list)
    errors: dict[str, str] = field(default_factory=dict)
    updated_at: datetime | None = None

    @property
    def open_incidents(self) -> int:
        return sum(incident.status != "RESOLVED" for incident in self.incidents)

    @property
    def unavailable_services(self) -> int:
        return sum(
            service.status == ServiceStatus.DOWN
            for service in self.services
        )


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_timestamp(value: Any) -> datetime:
    if not isinstance(value, str):
        raise ValidationError("Timestamp must be an ISO-8601 string.")

    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValidationError(f"Invalid timestamp: {value}") from exc

    if parsed.tzinfo is None:
        raise ValidationError("Timestamp must include a timezone.")

    if parsed > utc_now() + timedelta(minutes=5):
        raise ValidationError("Timestamp is unexpectedly far in the future.")

    return parsed


def validate_metrics(payload: Any) -> list[Metric]:
    if not isinstance(payload, list):
        raise ValidationError("Metrics response must be a list.")

    results: list[Metric] = []
    seen: set[tuple[str, str]] = set()

    for item in payload:
        if not isinstance(item, dict):
            raise ValidationError("Each metric must be an object.")

        name = item.get("name")
        unit = item.get("unit")
        service_id = item.get("service_id")
        value = item.get("value")

        if not all(isinstance(v, str) and v.strip() for v in
                   (name, unit, service_id)):
            raise ValidationError("Metric identifiers and units are required.")

        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValidationError(f"Metric {name} must have a numeric value.")

        if not math.isfinite(value) or value < 0:
            raise ValidationError(f"Metric {name} has an invalid value.")

        key = (service_id, name)
        if key in seen:
            raise ValidationError(f"Duplicate metric: {key}")
        seen.add(key)

        results.append(
            Metric(
                name=name,
                value=float(value),
                unit=unit,
                observed_at=parse_timestamp(item.get("observed_at")),
            )
        )

    return results


def validate_services(payload: Any) -> list[Service]:
    if not isinstance(payload, list):
        raise ValidationError("Services response must be a list.")

    results: list[Service] = []
    seen: set[str] = set()

    for item in payload:
        if not isinstance(item, dict):
            raise ValidationError("Each service must be an object.")

        service_id = item.get("service_id")
        name = item.get("name")
        region = item.get("region")

        if not all(isinstance(v, str) and v.strip() for v in
                   (service_id, name, region)):
            raise ValidationError("Service identifiers and names are required.")

        if service_id in seen:
            raise ValidationError(f"Duplicate service: {service_id}")
        seen.add(service_id)

        try:
            status = ServiceStatus(item.get("status"))
        except ValueError as exc:
            raise ValidationError(
                f"Unsupported status for service {service_id}."
            ) from exc

        results.append(Service(service_id, name, status, region))

    return results


def validate_incidents(payload: Any) -> list[Incident]:
    if not isinstance(payload, list):
        raise ValidationError("Incidents response must be a list.")

    results: list[Incident] = []
    seen: set[str] = set()
    valid_severities = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
    valid_statuses = {"OPEN", "INVESTIGATING", "RESOLVED"}

    for item in payload:
        if not isinstance(item, dict):
            raise ValidationError("Each incident must be an object.")

        incident_id = item.get("incident_id")
        service_id = item.get("service_id")
        severity = item.get("severity")
        title = item.get("title")
        status = item.get("status")

        if not all(isinstance(v, str) and v.strip() for v in
                   (incident_id, service_id, severity, title, status)):
            raise ValidationError("Incident fields cannot be empty.")

        if incident_id in seen:
            raise ValidationError(f"Duplicate incident: {incident_id}")
        seen.add(incident_id)

        if severity not in valid_severities:
            raise ValidationError(f"Invalid severity: {severity}")

        if status not in valid_statuses:
            raise ValidationError(f"Invalid incident status: {status}")

        results.append(
            Incident(
                incident_id,
                service_id,
                severity,
                title,
                status,
                parse_timestamp(item.get("opened_at")),
            )
        )

    return results


class DemoApiClient:
    """
    Deterministic asynchronous API adapter.

    The adapter simulates HTTP latency and temporary server failures.
    A real implementation can replace this class with an HTTP transport.
    """

    def __init__(self) -> None:
        now = utc_now()
        recent = lambda seconds: (now - timedelta(seconds=seconds)).isoformat()

        self._payloads: dict[str, list[dict[str, Any]]] = {
            "/api/metrics": [
                {
                    "service_id": "payments",
                    "name": "latency",
                    "value": 145.2,
                    "unit": "ms",
                    "observed_at": recent(12),
                },
                {
                    "service_id": "payments",
                    "name": "error_rate",
                    "value": 0.8,
                    "unit": "%",
                    "observed_at": recent(12),
                },
                {
                    "service_id": "identity",
                    "name": "latency",
                    "value": 88.4,
                    "unit": "ms",
                    "observed_at": recent(8),
                },
                {
                    "service_id": "identity",
                    "name": "error_rate",
                    "value": 0.2,
                    "unit": "%",
                    "observed_at": recent(8),
                },
                {
                    "service_id": "notifications",
                    "name": "latency",
                    "value": 420.0,
                    "unit": "ms",
                    "observed_at": recent(20),
                },
            ],
            "/api/services": [
                {
                    "service_id": "payments",
                    "name": "Payment Processing",
                    "status": "OPERATIONAL",
                    "region": "ap-south-1",
                },
                {
                    "service_id": "identity",
                    "name": "Identity Service",
                    "status": "OPERATIONAL",
                    "region": "ap-south-1",
                },
                {
                    "service_id": "notifications",
                    "name": "Notification Gateway",
                    "status": "DEGRADED",
                    "region": "ap-south-1",
                },
            ],
            "/api/incidents": [
                {
                    "incident_id": "INC-2041",
                    "service_id": "notifications",
                    "severity": "HIGH",
                    "title": "Elevated notification latency",
                    "status": "INVESTIGATING",
                    "opened_at": recent(1800),
                },
                {
                    "incident_id": "INC-2038",
                    "service_id": "payments",
                    "severity": "LOW",
                    "title": "Intermittent callback delay",
                    "status": "RESOLVED",
                    "opened_at": recent(7200),
                },
            ],
        }

        self._failures: dict[str, int] = {}

    def fail_next(self, endpoint: str, count: int = 1) -> None:
        if endpoint not in self._payloads:
            raise ValueError(f"Unknown endpoint: {endpoint}")
        if count < 0:
            raise ValueError("Failure count cannot be negative.")
        self._failures[endpoint] = count

    async def get(self, endpoint: str) -> list[dict[str, Any]]:
        if endpoint not in self._payloads:
            raise ApiError(f"Endpoint not found: {endpoint}")

        await asyncio.sleep(0.025)

        remaining = self._failures.get(endpoint, 0)
        if remaining:
            self._failures[endpoint] = remaining - 1
            raise ApiError(f"Temporary upstream failure: {endpoint}")

        # Return a defensive copy so callers cannot mutate provider fixtures.
        return json.loads(json.dumps(self._payloads[endpoint]))


class DashboardController:
    def __init__(
        self,
        api: DemoApiClient,
        cache_ttl_seconds: float = 0.01,
        max_attempts: int = 3,
    ) -> None:
        if cache_ttl_seconds < 0:
            raise ValueError("Cache TTL cannot be negative.")
        if max_attempts < 1:
            raise ValueError("At least one API attempt is required.")

        self.api = api
        self.cache_ttl = timedelta(seconds=cache_ttl_seconds)
        self.max_attempts = max_attempts
        self.cache: dict[str, CacheEntry] = {}
        self.snapshot = DashboardSnapshot()
        self._refresh_lock = asyncio.Lock()

        self._validators: dict[str, Callable[[Any], list[Any]]] = {
            "/api/metrics": validate_metrics,
            "/api/services": validate_services,
            "/api/incidents": validate_incidents,
        }

    async def _load_resource(self, endpoint: str) -> ResourceResult:
        now = utc_now()
        cached = self.cache.get(endpoint)

        if (
            cached is not None
            and now - cached.fetched_at <= self.cache_ttl
        ):
            return ResourceResult(
                self._validators[endpoint](cached.value),
                stale=False,
            )

        last_error: Exception | None = None

        for attempt in range(self.max_attempts):
            try:
                payload = await self.api.get(endpoint)
                parsed = self._validators[endpoint](payload)

                self.cache[endpoint] = CacheEntry(
                    value=payload,
                    fetched_at=utc_now(),
                )
                return ResourceResult(parsed)

            except (ApiError, ValidationError) as exc:
                last_error = exc
                if attempt + 1 < self.max_attempts:
                    await asyncio.sleep(0.02 * (2 ** attempt))

        # A failed refresh does not erase a previously valid resource.
        if cached is not None:
            return ResourceResult(
                self._validators[endpoint](cached.value),
                stale=True,
                error=str(last_error),
            )

        raise DashboardError(
            f"{endpoint} failed after {self.max_attempts} attempts: "
            f"{last_error}"
        )

    async def refresh(self, force: bool = False) -> DashboardSnapshot:
        """
        Load independent resources concurrently.

        The lock prevents overlapping refreshes from producing competing
        snapshots. Each endpoint can fail independently.
        """
        async with self._refresh_lock:
            self.snapshot.phase = DashboardPhase.LOADING
            self.snapshot.errors = {}

            endpoints = list(self._validators)

            if force:
                # An explicit refresh bypasses the normal TTL check.
                previous_ttl = self.cache_ttl
                self.cache_ttl = timedelta(0)
            else:
                previous_ttl = self.cache_ttl

            try:
                outcomes = await asyncio.gather(
                    *(self._load_resource(path) for path in endpoints),
                    return_exceptions=True,
                )
            finally:
                self.cache_ttl = previous_ttl

            values: dict[str, ResourceResult] = {}
            errors: dict[str, str] = {}
            stale: list[str] = []

            for endpoint, outcome in zip(endpoints, outcomes):
                key = endpoint.rsplit("/", 1)[-1]

                if isinstance(outcome, BaseException):
                    errors[key] = str(outcome)
                    continue

                values[key] = outcome

                if outcome.stale:
                    stale.append(key)
                    if outcome.error:
                        errors[key] = outcome.error

            if "metrics" in values:
                self.snapshot.metrics = values["metrics"].data

            if "services" in values:
                self.snapshot.services = values["services"].data

            if "incidents" in values:
                self.snapshot.incidents = values["incidents"].data

            self.snapshot.stale_resources = stale
            self.snapshot.errors = errors
            self.snapshot.updated_at = utc_now()

            successful_resources = len(values)
            if successful_resources == 0:
                self.snapshot.phase = DashboardPhase.ERROR
            elif errors or stale or successful_resources < len(endpoints):
                self.snapshot.phase = DashboardPhase.DEGRADED
            else:
                self.snapshot.phase = DashboardPhase.READY

            return self.snapshot

    def export_json(self, destination: Path) -> None:
        """
        Atomically export the current snapshot.

        A temporary file in the destination directory avoids exposing a
        partially written JSON file if the process stops during export.
        """
        destination = destination.resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "phase": self.snapshot.phase.value,
            "metrics": [asdict(item) for item in self.snapshot.metrics],
            "services": [
                {
                    **asdict(item),
                    "status": item.status.value,
                }
                for item in self.snapshot.services
            ],
            "incidents": [asdict(item) for item in self.snapshot.incidents],
            "stale_resources": self.snapshot.stale_resources,
            "errors": self.snapshot.errors,
            "updated_at": (
                self.snapshot.updated_at.isoformat()
                if self.snapshot.updated_at
                else None
            ),
        }

        def serialize(value: Any) -> Any:
            if isinstance(value, datetime):
                return value.isoformat()
            if isinstance(value, Enum):
                return value.value
            raise TypeError(f"Unsupported JSON value: {type(value).__name__}")

        temporary_path: Path | None = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=destination.parent,
                prefix=f".{destination.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary_file:
                temporary_path = Path(temporary_file.name)
                json.dump(
                    payload,
                    temporary_file,
                    indent=2,
                    default=serialize,
                    allow_nan=False,
                )
                temporary_file.flush()
                os.fsync(temporary_file.fileno())

            os.replace(temporary_path, destination)

        except OSError as exc:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
            raise DashboardError(
                f"Could not export dashboard to {destination}: {exc}"
            ) from exc


def print_dashboard(snapshot: DashboardSnapshot) -> None:
    print("\nAPI OPERATIONS DASHBOARD")
    print("=" * 55)
    print(f"State: {snapshot.phase.value}")
    print(
        "Last update:",
        snapshot.updated_at.isoformat() if snapshot.updated_at else "Never",
    )
    print(f"Services: {len(snapshot.services)}")
    print(f"Unavailable services: {snapshot.unavailable_services}")
    print(f"Open incidents: {snapshot.open_incidents}")

    print("\nService status")
    for service in snapshot.services:
        print(
            f"  {service.name:<25} "
            f"{service.status.value:<12} {service.region}"
        )

    print("\nMetrics")
    for metric in snapshot.metrics:
        print(
            f"  {metric.name:<15} "
            f"{metric.value:>9.2f} {metric.unit}"
        )

    print("\nIncidents")
    for incident in snapshot.incidents:
        print(
            f"  {incident.incident_id} | {incident.severity:<8} "
            f"| {incident.status:<14} | {incident.title}"
        )

    if snapshot.stale_resources:
        print("\nStale resources:", ", ".join(snapshot.stale_resources))

    if snapshot.errors:
        print("\nResource errors")
        for resource, error in snapshot.errors.items():
            print(f"  {resource}: {error}")


async def main() -> None:
    api = DemoApiClient()
    dashboard = DashboardController(api)

    # First refresh demonstrates concurrent loading and transient retry.
    api.fail_next("/api/incidents", count=1)
    snapshot = await dashboard.refresh()
    print_dashboard(snapshot)

    # Second refresh demonstrates fallback to previously validated data.
    api.fail_next("/api/incidents", count=3)
    snapshot = await dashboard.refresh(force=True)
    print_dashboard(snapshot)

    export_path = Path("dashboard_snapshot.json")
    dashboard.export_json(export_path)
    print(f"\nSnapshot exported to: {export_path.resolve()}")

    assert snapshot.phase == DashboardPhase.DEGRADED
    assert "incidents" in snapshot.stale_resources
    assert snapshot.open_incidents >= 1


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nDashboard execution interrupted.")
    except DashboardError as exc:
        print(f"Dashboard error: {exc}")
        raise SystemExit(1)
