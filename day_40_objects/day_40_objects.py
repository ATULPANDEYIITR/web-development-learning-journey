"""
Objects in Python: properties, methods, nested objects, destructuring,
spread-style copying, and computed properties.

Run with:
    python objects_workshop.py

Uses only the Python standard library.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
from pprint import pprint
from typing import Any, Callable, Iterable, Mapping


def heading(title: str) -> None:
    print(f"\n{'=' * 72}\n{title}\n{'=' * 72}")


# Python objects store state in attributes and expose behavior through methods.
class Repository:
    def __init__(
        self,
        name: str,
        owner: str,
        default_branch: str = "main",
    ) -> None:
        if not name.strip():
            raise ValueError("Repository name cannot be empty.")
        if not owner.strip():
            raise ValueError("Repository owner cannot be empty.")
        if not default_branch.strip():
            raise ValueError("Default branch cannot be empty.")

        self.name = name
        self.owner = owner
        self.default_branch = default_branch
        self._stars = 0
        self._archived = False

    @property
    def full_name(self) -> str:
        """A computed, read-only property."""
        return f"{self.owner}/{self.name}"

    @property
    def stars(self) -> int:
        return self._stars

    @stars.setter
    def stars(self, value: int) -> None:
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError("Stars must be an integer.")
        if value < 0:
            raise ValueError("Stars cannot be negative.")
        self._stars = value

    @property
    def archived(self) -> bool:
        return self._archived

    def add_stars(self, count: int = 1) -> int:
        if isinstance(count, bool) or not isinstance(count, int):
            raise TypeError("Count must be an integer.")
        if count <= 0:
            raise ValueError("Count must be positive.")
        self.stars += count
        return self.stars

    def archive(self) -> None:
        self._archived = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "owner": self.owner,
            "full_name": self.full_name,
            "default_branch": self.default_branch,
            "stars": self.stars,
            "archived": self.archived,
        }

    def __repr__(self) -> str:
        return f"Repository({self.full_name!r}, stars={self.stars})"


def basic_properties_and_methods() -> None:
    heading("Object properties and methods")

    repo = Repository("release-service", "engineering")
    print("Name:", repo.name)
    print("Owner:", repo.owner)
    print("Computed full name:", repo.full_name)
    print("Initial stars:", repo.stars)
    print("After adding stars:", repo.add_stars(4))
    print("Representation:", repo)
    pprint(repo.to_dict())

    try:
        repo.stars = -1
    except ValueError as exc:
        print("Validation caught:", exc)

    try:
        repo.full_name = "forged/name"
    except AttributeError as exc:
        print("Read-only property caught:", exc)


# A nested object is a reference to another object, not an automatic copy.
class PullRequest:
    def __init__(
        self,
        number: int,
        title: str,
        source_branch: str,
        target_branch: str,
        repository: Repository,
    ) -> None:
        if number <= 0:
            raise ValueError("Pull request number must be positive.")
        if not title.strip():
            raise ValueError("Pull request title cannot be empty.")
        if source_branch == target_branch:
            raise ValueError("Source and target branches must differ.")

        self.number = number
        self.title = title
        self.source_branch = source_branch
        self.target_branch = target_branch
        self.repository = repository
        self.labels: list[str] = []
        self.metadata: dict[str, Any] = {
            "review": {"required": True, "approvals": 0},
            "checks": {"passed": False},
        }

    @property
    def url(self) -> str:
        return f"https://example.invalid/{self.repository.full_name}/pull/{self.number}"

    def add_label(self, label: str) -> None:
        normalized = label.strip().lower()
        if not normalized:
            raise ValueError("Label cannot be empty.")
        if normalized not in self.labels:
            self.labels.append(normalized)

    def record_approval(self, reviewer: str) -> None:
        if not reviewer.strip():
            raise ValueError("Reviewer name cannot be empty.")
        self.metadata["review"]["approvals"] += 1
        self.metadata["review"].setdefault("reviewers", []).append(reviewer)

    def mergeable(self) -> bool:
        review = self.metadata["review"]
        checks = self.metadata["checks"]
        return (
            not self.repository.archived
            and (not review["required"] or review["approvals"] >= 1)
            and checks["passed"]
        )


def nested_objects_and_mutation() -> None:
    heading("Nested objects and shared references")

    repo = Repository("payment-api", "platform")
    pr = PullRequest(
        42,
        "Validate payment webhook signatures",
        "feature/webhook-signatures",
        "main",
        repo,
    )
    pr.add_label("Security")
    pr.record_approval("reviewer-lee")
    pr.metadata["checks"]["passed"] = True

    print("Nested repository:", pr.repository.full_name)
    print("Pull request URL:", pr.url)
    print("Labels:", pr.labels)
    print("Nested metadata:")
    pprint(pr.metadata)
    print("Mergeable:", pr.mergeable())

    # Both variables refer to the same repository instance.
    same_repo = pr.repository
    same_repo.archive()
    print("Archived through shared reference:", repo.archived)
    print("Mergeable after archival:", pr.mergeable())


def dictionary_destructuring() -> None:
    heading("Destructuring-style extraction")

    payload = {
        "number": 84,
        "title": "Improve deployment validation",
        "author": {"login": "mira", "team": "platform"},
        "labels": ["deployment", "reliability"],
        "draft": False,
    }

    # Mapping unpacking binds named values without modifying the original.
    number, title, author, labels, draft = (
        payload["number"],
        payload["title"],
        payload["author"],
        payload["labels"],
        payload["draft"],
    )
    print(number, title, author["login"], labels, draft)

    # .get() provides explicit defaults for optional mapping fields.
    reviewer = payload.get("reviewer", "unassigned")
    print("Reviewer:", reviewer)

    # The walrus operator can bind a value while testing whether it exists.
    if (team := payload.get("team")) is not None:
        print("Team:", team)
    else:
        print("No top-level team property exists.")

    # Nested extraction should account for absent keys and wrong value types.
    author_data = payload.get("author")
    if isinstance(author_data, Mapping):
        login = author_data.get("login", "unknown")
        print("Safely extracted login:", login)


def dictionary_spread_and_copying() -> None:
    heading("Dictionary unpacking and copying")

    defaults = {
        "timeout_seconds": 20,
        "retries": 2,
        "headers": {"Accept": "application/json"},
    }
    overrides = {
        "timeout_seconds": 45,
        "retries": 4,
    }

    # Later dictionary unpackings overwrite earlier keys.
    effective_config = {**defaults, **overrides}
    print("Merged configuration:")
    pprint(effective_config)

    # Dictionary unpacking creates a shallow copy. Nested objects are shared.
    shallow = {**defaults}
    shallow["headers"]["X-Trace"] = "trace-001"
    print("Original after nested shallow-copy mutation:")
    pprint(defaults)

    # Deep copying recursively separates nested mutable containers.
    isolated = deepcopy(defaults)
    isolated["headers"]["X-Trace"] = "isolated-trace"
    print("Original after deep-copy mutation:")
    pprint(defaults)
    print("Deep copy:")
    pprint(isolated)

    # The union operator also merges dictionaries on Python 3.9 and later.
    merged_with_union = defaults | {"retries": 5}
    print("Union result:", merged_with_union)


def computed_properties() -> None:
    heading("Computed properties and dynamic dictionary keys")

    metrics = {"requests": 1250, "errors": 15}
    error_rate = metrics["errors"] / metrics["requests"]
    print(f"Error rate: {error_rate:.2%}")

    # A computed key is evaluated at runtime.
    metric_name = "latency_ms"
    measurement = 87
    record = {
        "service": "checkout",
        metric_name: measurement,
        f"{metric_name}_threshold": 120,
    }
    pprint(record)

    # Computed attribute access uses getattr and must be validated when
    # the attribute name originates from external input.
    repo = Repository("catalog", "commerce")
    requested_property = "default_branch"

    if requested_property not in {"name", "owner", "default_branch", "stars"}:
        raise ValueError("Unsupported property requested.")

    print("Computed attribute access:", getattr(repo, requested_property))

    # setattr changes an attribute dynamically. Use an allowlist to avoid
    # accidentally overwriting internal state or methods.
    permitted_updates = {"name", "default_branch"}
    update = {"default_branch": "stable"}
    for key, value in update.items():
        if key not in permitted_updates:
            raise ValueError(f"Property update not permitted: {key}")
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Invalid value for {key}")
        setattr(repo, key, value)

    print("Updated repository:", repo.to_dict())


@dataclass
class Deployment:
    """Dataclasses provide generated initialization and representation."""

    service: str
    environment: str
    replicas: int
    tags: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.service.strip():
            raise ValueError("Service is required.")
        if self.environment not in {"development", "staging", "production"}:
            raise ValueError("Unsupported environment.")
        if self.replicas < 1:
            raise ValueError("At least one replica is required.")

    @property
    def production_ready(self) -> bool:
        return self.environment == "production" and self.replicas >= 3


def dataclass_objects() -> None:
    heading("Structured objects with dataclasses")

    deployment = Deployment(
        service="inventory",
        environment="production",
        replicas=4,
        tags={"region": "ap-south-1", "owner": "platform"},
    )

    print(deployment)
    print("Production ready:", deployment.production_ready)

    # asdict recursively converts dataclasses into dictionaries.
    print("Serialized structure:")
    pprint(asdict(deployment))

    # replace constructs a new dataclass instance with selected changes.
    scaled = replace(deployment, replicas=6)
    print("Original replicas:", deployment.replicas)
    print("Scaled replicas:", scaled.replicas)


def object_serialization_and_validation() -> None:
    heading("Serialization boundaries and validation")

    repository = Repository("identity-service", "security")
    repository.stars = 18
    exported = repository.to_dict()

    print("JSON-compatible object:")
    pprint(exported)

    # JSON serialization supports ordinary dictionaries and JSON-compatible
    # values, but arbitrary Python instances require explicit conversion.
    import json

    encoded = json.dumps(exported, sort_keys=True)
    print("Encoded JSON:", encoded)
    print("Decoded full name:", json.loads(encoded)["full_name"])

    untrusted_payload = {
        "name": "identity-service",
        "owner": "security",
        "stars": "18",
    }

    try:
        if not isinstance(untrusted_payload.get("stars"), int):
            raise TypeError("Incoming stars must be an integer.")
        repository.stars = untrusted_payload["stars"]
    except (TypeError, ValueError) as exc:
        print("Rejected untrusted payload:", exc)

    # JSON round-tripping is not a universal deep-copy technique: it loses
    # custom Python types, tuples, datetime values, and object identity.
    timestamp = datetime.now(timezone.utc)
    print("Timestamp requires an explicit serialization policy:", timestamp.isoformat())


def object_composition_and_protocols() -> None:
    heading("Composition and object protocols")

    class AuditLog:
        def __init__(self) -> None:
            self.events: list[dict[str, Any]] = []

        def record(self, event: str, **details: Any) -> None:
            self.events.append({
                "event": event,
                "details": details,
                "recorded_at": datetime.now(timezone.utc).isoformat(),
            })

        def __len__(self) -> int:
            return len(self.events)

        def __iter__(self):
            return iter(self.events)

    class DeploymentService:
        def __init__(self, audit: AuditLog) -> None:
            self.audit = audit

        def deploy(self, deployment: Deployment) -> dict[str, Any]:
            if deployment.environment == "production" and deployment.replicas < 3:
                self.audit.record(
                    "deployment_rejected",
                    service=deployment.service,
                    reason="insufficient_replicas",
                )
                raise ValueError("Production deployments require three replicas.")

            result = {
                "service": deployment.service,
                "environment": deployment.environment,
                "replicas": deployment.replicas,
                "status": "accepted",
            }
            self.audit.record("deployment_accepted", **result)
            return result

    audit = AuditLog()
    service = DeploymentService(audit)

    service.deploy(Deployment("search", "staging", 1))
    try:
        service.deploy(Deployment("billing", "production", 1))
    except ValueError as exc:
        print("Deployment rejected:", exc)

    print("Audit event count:", len(audit))
    for event in audit:
        pprint(event)


def main() -> None:
    basic_properties_and_methods()
    nested_objects_and_mutation()
    dictionary_destructuring()
    dictionary_spread_and_copying()
    computed_properties()
    dataclass_objects()
    object_serialization_and_validation()
    object_composition_and_protocols()


if __name__ == "__main__":
    main()
