#!/usr/bin/env python3
"""
Production-Style Admin Dashboard
Repository Governance and Development Operations

A self-contained Python application that simulates the backend
workflow of a repository governance administration dashboard.

Features:
- Repository and branch management
- Pull Request lifecycle
- Code review management
- Reviewer approvals
- Branch protection policies
- CI/CD status checks
- Merge eligibility evaluation
- Audit logging
- JSON persistence
- Input validation and error handling
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("repository_dashboard")


class ValidationError(Exception):
    pass


class WorkflowError(Exception):
    pass


class PRState(str, Enum):
    DRAFT = "draft"
    OPEN = "open"
    CLOSED = "closed"
    MERGED = "merged"


class ReviewState(str, Enum):
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"
    COMMENTED = "commented"
    DISMISSED = "dismissed"


class CheckState(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILURE = "failure"
    CANCELLED = "cancelled"


@dataclass
class Commit:
    commit_id: str
    message: str
    author: str
    timestamp: str


@dataclass
class Branch:
    name: str
    head_commit: str
    protected: bool = False
    commits: list[str] = field(default_factory=list)


@dataclass
class Review:
    reviewer: str
    state: ReviewState
    commit_id: str
    comment: str
    submitted_at: str


@dataclass
class StatusCheck:
    name: str
    state: CheckState
    details: str = ""


@dataclass
class PullRequest:
    pr_id: int
    title: str
    author: str
    source_branch: str
    target_branch: str
    state: PRState
    base_commit: str
    head_commit: str
    reviews: list[Review] = field(default_factory=list)
    checks: list[StatusCheck] = field(default_factory=list)
    unresolved_comments: int = 0
    draft: bool = False


@dataclass
class ProtectionPolicy:
    required_approvals: int = 2
    required_checks: tuple[str, ...] = (
        "build",
        "tests",
        "security"
    )
    require_resolved_conversations: bool = True
    require_up_to_date_branch: bool = True
    allow_direct_push: bool = False
    allow_force_push: bool = False
    allow_deletion: bool = False
    require_linear_history: bool = True
    allow_admin_bypass: bool = False


@dataclass
class AuditEvent:
    event_id: str
    action: str
    actor: str
    resource: str
    timestamp: str
    details: str


class Repository:
    def __init__(self, name: str, owner: str):
        if not name.strip() or not owner.strip():
            raise ValidationError("Repository name and owner are required.")

        self.name = name
        self.owner = owner
        self.commits: dict[str, Commit] = {}
        self.branches: dict[str, Branch] = {}
        self.pull_requests: dict[int, PullRequest] = {}
        self.protection: dict[str, ProtectionPolicy] = {}
        self.reviewers: set[str] = set()
        self.audit_log: list[AuditEvent] = []
        self.next_pr_id = 1

    @staticmethod
    def now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def audit(
        self,
        action: str,
        actor: str,
        resource: str,
        details: str
    ) -> None:
        self.audit_log.append(
            AuditEvent(
                event_id=str(uuid.uuid4()),
                action=action,
                actor=actor,
                resource=resource,
                timestamp=self.now(),
                details=details
            )
        )

    def add_commit(
        self,
        message: str,
        author: str,
        commit_id: Optional[str] = None
    ) -> Commit:
        if not message.strip() or not author.strip():
            raise ValidationError("Commit message and author are required.")

        commit_id = commit_id or uuid.uuid4().hex[:12]

        if commit_id in self.commits:
            raise ValidationError("Commit already exists.")

        commit = Commit(
            commit_id=commit_id,
            message=message,
            author=author,
            timestamp=self.now()
        )

        self.commits[commit_id] = commit
        return commit

    def create_branch(
        self,
        name: str,
        commit_id: str,
        actor: str
    ) -> Branch:
        if name in self.branches:
            raise ValidationError("Branch already exists.")

        if commit_id not in self.commits:
            raise ValidationError("Unknown starting commit.")

        branch = Branch(
            name=name,
            head_commit=commit_id,
            commits=[commit_id]
        )

        self.branches[name] = branch
        self.audit("BRANCH_CREATED", actor, name, commit_id)

        return branch

    def push_commit(
        self,
        branch_name: str,
        commit_id: str,
        actor: str,
        force: bool = False
    ) -> None:
        branch = self.branches.get(branch_name)

        if branch is None:
            raise ValidationError("Branch does not exist.")

        if commit_id not in self.commits:
            raise ValidationError("Unknown commit.")

        if branch.protected:
            policy = self.protection[branch_name]

            if not policy.allow_direct_push:
                raise WorkflowError("Direct pushes are prohibited.")

            if force and not policy.allow_force_push:
                raise WorkflowError("Force pushes are prohibited.")

        branch.head_commit = commit_id
        branch.commits.append(commit_id)

        self.audit(
            "COMMIT_PUSHED",
            actor,
            branch_name,
            commit_id
        )

    def protect_branch(
        self,
        branch_name: str,
        policy: ProtectionPolicy,
        actor: str
    ) -> None:
        if branch_name not in self.branches:
            raise ValidationError("Unknown branch.")

        if policy.required_approvals < 0:
            raise ValidationError("Invalid approval requirement.")

        self.branches[branch_name].protected = True
        self.protection[branch_name] = policy

        self.audit(
            "BRANCH_PROTECTED",
            actor,
            branch_name,
            "Protection policy configured"
        )

    def register_reviewer(self, reviewer: str) -> None:
        if not reviewer.strip():
            raise ValidationError("Reviewer identity is required.")

        self.reviewers.add(reviewer)

    def create_pull_request(
        self,
        title: str,
        author: str,
        source: str,
        target: str,
        draft: bool = False
    ) -> PullRequest:
        if not title.strip():
            raise ValidationError("Pull Request title is required.")

        if source == target:
            raise ValidationError("Source and target must differ.")

        if source not in self.branches or target not in self.branches:
            raise ValidationError("Source or target branch does not exist.")

        if self.branches[source].head_commit == self.branches[target].head_commit:
            raise WorkflowError("No new changes are available.")

        pr = PullRequest(
            pr_id=self.next_pr_id,
            title=title,
            author=author,
            source_branch=source,
            target_branch=target,
            state=PRState.DRAFT if draft else PRState.OPEN,
            base_commit=self.branches[target].head_commit,
            head_commit=self.branches[source].head_commit,
            draft=draft
        )

        self.pull_requests[pr.pr_id] = pr
        self.next_pr_id += 1

        self.audit(
            "PULL_REQUEST_CREATED",
            author,
            str(pr.pr_id),
            title
        )

        return pr

    def publish_draft(self, pr_id: int, actor: str) -> None:
        pr = self._get_open_pr(pr_id)

        if pr.state != PRState.DRAFT:
            raise WorkflowError("Pull Request is not a draft.")

        pr.state = PRState.OPEN
        pr.draft = False

        self.audit("DRAFT_PUBLISHED", actor, str(pr_id), "Published")

    def add_review(
        self,
        pr_id: int,
        reviewer: str,
        state: ReviewState,
        comment: str = ""
    ) -> Review:
        pr = self._get_open_pr(pr_id)

        if reviewer not in self.reviewers:
            raise WorkflowError("Reviewer is not eligible.")

        if reviewer == pr.author:
            raise WorkflowError("Authors cannot approve their own changes.")

        if pr.draft:
            raise WorkflowError("Draft Pull Requests cannot be approved.")

        review = Review(
            reviewer=reviewer,
            state=state,
            commit_id=pr.head_commit,
            comment=comment,
            submitted_at=self.now()
        )

        # A new review supersedes the reviewer's previous decision.
        pr.reviews = [
            item for item in pr.reviews
            if item.reviewer != reviewer
        ]

        pr.reviews.append(review)

        self.audit(
            "REVIEW_SUBMITTED",
            reviewer,
            str(pr_id),
            state.value
        )

        return review

    def update_check(
        self,
        pr_id: int,
        name: str,
        state: CheckState,
        details: str = ""
    ) -> None:
        pr = self._get_open_pr(pr_id)

        if not name.strip():
            raise ValidationError("Check name is required.")

        pr.checks = [
            check for check in pr.checks
            if check.name != name
        ]

        pr.checks.append(
            StatusCheck(name, state, details)
        )

        self.audit(
            "STATUS_CHECK_UPDATED",
            "ci-system",
            str(pr_id),
            f"{name}: {state.value}"
        )

    def add_conversation(self, pr_id: int) -> None:
        pr = self._get_open_pr(pr_id)
        pr.unresolved_comments += 1

    def resolve_conversation(self, pr_id: int) -> None:
        pr = self._get_open_pr(pr_id)

        if pr.unresolved_comments == 0:
            raise WorkflowError("No unresolved conversation exists.")

        pr.unresolved_comments -= 1

    def synchronize_base(self, pr_id: int) -> None:
        pr = self._get_open_pr(pr_id)

        target = self.branches[pr.target_branch]
        source = self.branches[pr.source_branch]

        # Synchronization updates the proposed changeset.
        # A real Git operation must resolve conflicts before this step.
        pr.base_commit = target.head_commit
        pr.head_commit = source.head_commit

        # Reviews and checks attached to the previous commit are stale.
        pr.reviews.clear()
        pr.checks.clear()

        self.audit(
            "BASE_SYNCHRONIZED",
            "repository-system",
            str(pr_id),
            "Previous reviews and checks invalidated"
        )

    def evaluate_merge(self, pr_id: int) -> tuple[bool, list[str]]:
        pr = self._get_open_pr(pr_id)
        reasons: list[str] = []

        if pr.draft:
            reasons.append("Pull Request is still a draft.")

        if pr.state != PRState.OPEN:
            reasons.append("Pull Request is not open.")

        policy = self.protection.get(
            pr.target_branch,
            ProtectionPolicy()
        )

        if policy.require_up_to_date_branch:
            target_head = self.branches[pr.target_branch].head_commit

            if pr.base_commit != target_head:
                reasons.append("Target branch has advanced.")

        # Only reviews of the current proposed commit count.
        valid_reviews = [
            review for review in pr.reviews
            if review.commit_id == pr.head_commit
        ]

        approved_reviewers = {
            review.reviewer
            for review in valid_reviews
            if review.state == ReviewState.APPROVED
        }

        blocked_reviewers = [
            review.reviewer
            for review in valid_reviews
            if review.state == ReviewState.CHANGES_REQUESTED
        ]

        if blocked_reviewers:
            reasons.append(
                "Changes requested by: "
                + ", ".join(blocked_reviewers)
            )

        if len(approved_reviewers) < policy.required_approvals:
            reasons.append(
                f"Requires {policy.required_approvals} distinct approvals; "
                f"received {len(approved_reviewers)}."
            )

        checks = {
            check.name: check.state
            for check in pr.checks
        }

        for required in policy.required_checks:
            if checks.get(required) != CheckState.SUCCESS:
                reasons.append(
                    f"Required check '{required}' has not succeeded."
                )

        if (
            policy.require_resolved_conversations
            and pr.unresolved_comments > 0
        ):
            reasons.append("Unresolved review conversations remain.")

        return not reasons, reasons

    def merge(self, pr_id: int, actor: str) -> None:
        pr = self._get_open_pr(pr_id)

        eligible, reasons = self.evaluate_merge(pr_id)

        if not eligible:
            raise WorkflowError(
                "Merge rejected: " + "; ".join(reasons)
            )

        target = self.branches[pr.target_branch]

        # The merge creates a new commit representing the integrated state.
        merge_commit = self.add_commit(
            message=f"Merge PR #{pr_id}: {pr.title}",
            author=actor
        )

        target.head_commit = merge_commit.commit_id
        target.commits.append(merge_commit.commit_id)

        pr.state = PRState.MERGED

        self.audit(
            "PULL_REQUEST_MERGED",
            actor,
            str(pr_id),
            merge_commit.commit_id
        )

    def close_pull_request(self, pr_id: int, actor: str) -> None:
        pr = self._get_open_pr(pr_id)

        pr.state = PRState.CLOSED

        self.audit(
            "PULL_REQUEST_CLOSED",
            actor,
            str(pr_id),
            "Closed without merging"
        )

    def reopen_pull_request(self, pr_id: int, actor: str) -> None:
        pr = self.pull_requests.get(pr_id)

        if pr is None or pr.state != PRState.CLOSED:
            raise WorkflowError("Only closed Pull Requests can be reopened.")

        pr.state = PRState.OPEN

        self.audit(
            "PULL_REQUEST_REOPENED",
            actor,
            str(pr_id),
            "Reopened"
        )

    def _get_open_pr(self, pr_id: int) -> PullRequest:
        pr = self.pull_requests.get(pr_id)

        if pr is None:
            raise ValidationError("Pull Request does not exist.")

        if pr.state not in (PRState.OPEN, PRState.DRAFT):
            raise WorkflowError("Pull Request is not active.")

        return pr

    def dashboard_metrics(self) -> dict:
        prs = list(self.pull_requests.values())

        eligible = sum(
            1
            for pr in prs
            if pr.state == PRState.OPEN
            and self.evaluate_merge(pr.pr_id)[0]
        )

        return {
            "repository": self.name,
            "branches": len(self.branches),
            "commits": len(self.commits),
            "total_pull_requests": len(prs),
            "open_pull_requests": sum(
                pr.state == PRState.OPEN for pr in prs
            ),
            "draft_pull_requests": sum(
                pr.state == PRState.DRAFT for pr in prs
            ),
            "merged_pull_requests": sum(
                pr.state == PRState.MERGED for pr in prs
            ),
            "closed_pull_requests": sum(
                pr.state == PRState.CLOSED for pr in prs
            ),
            "merge_eligible": eligible,
            "audit_events": len(self.audit_log)
        }

    def save(self, path: str) -> None:
        payload = {
            "name": self.name,
            "owner": self.owner,
            "commits": {
                key: asdict(value)
                for key, value in self.commits.items()
            },
            "branches": {
                key: asdict(value)
                for key, value in self.branches.items()
            },
            "pull_requests": [
                {
                    **asdict(pr),
                    "state": pr.state.value,
                    "reviews": [
                        {
                            **asdict(review),
                            "state": review.state.value
                        }
                        for review in pr.reviews
                    ],
                    "checks": [
                        {
                            **asdict(check),
                            "state": check.state.value
                        }
                        for check in pr.checks
                    ]
                }
                for pr in self.pull_requests.values()
            ],
            "reviewers": sorted(self.reviewers),
            "audit_log": [
                asdict(event) for event in self.audit_log
            ]
        }

        destination = Path(path)
        temporary = destination.with_suffix(".tmp")

        try:
            temporary.write_text(
                json.dumps(payload, indent=2),
                encoding="utf-8"
            )
            temporary.replace(destination)
        except OSError:
            logger.exception("Unable to persist repository state.")
            raise


def demonstration() -> None:
    repository = Repository(
        name="enterprise-admin-platform",
        owner="engineering"
    )

    initial = repository.add_commit(
        "Initial application release",
        "platform-team",
        "a10000000001"
    )

    repository.create_branch(
        "main",
        initial.commit_id,
        "platform-team"
    )

    repository.create_branch(
        "feature/dashboard-analytics",
        initial.commit_id,
        "developer"
    )

    feature_commit = repository.add_commit(
        "Add repository analytics",
        "developer",
        "b20000000002"
    )

    repository.push_commit(
        "feature/dashboard-analytics",
        feature_commit.commit_id,
        "developer"
    )

    repository.protect_branch(
        "main",
        ProtectionPolicy(
            required_approvals=2,
            required_checks=("build", "tests", "security"),
            require_resolved_conversations=True,
            require_up_to_date_branch=True
        ),
        "administrator"
    )

    for reviewer in ("reviewer-1", "reviewer-2"):
        repository.register_reviewer(reviewer)

    pr = repository.create_pull_request(
        "Implement repository analytics dashboard",
        "developer",
        "feature/dashboard-analytics",
        "main"
    )

    repository.add_review(
        pr.pr_id,
        "reviewer-1",
        ReviewState.APPROVED,
        "Architecture and implementation verified."
    )

    repository.add_review(
        pr.pr_id,
        "reviewer-2",
        ReviewState.APPROVED,
        "Tests and error handling verified."
    )

    for check in ("build", "tests", "security"):
        repository.update_check(
            pr.pr_id,
            check,
            CheckState.SUCCESS
        )

    repository.add_conversation(pr.pr_id)
    repository.resolve_conversation(pr.pr_id)

    eligible, reasons = repository.evaluate_merge(pr.pr_id)

    print("\nMERGE EVALUATION")
    print("Eligible:", eligible)
    print("Reasons:", reasons)

    if eligible:
        repository.merge(pr.pr_id, "release-manager")

    print("\nADMIN DASHBOARD METRICS")
    print(json.dumps(repository.dashboard_metrics(), indent=2))

    repository.save("repository_dashboard_state.json")

    assert pr.state == PRState.MERGED
    assert repository.dashboard_metrics()["merged_pull_requests"] == 1

    print("\nAll workflow assertions passed.")


if __name__ == "__main__":
    try:
        demonstration()
    except (ValidationError, WorkflowError, OSError) as error:
        logger.error("Application failure: %s", error)
        raise SystemExit(1)
