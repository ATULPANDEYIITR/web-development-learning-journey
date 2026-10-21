"""
Asynchronous repository-governance workflow simulator.

The simulation models Pull Requests, Code Reviews, Approvals, Status Checks,
and Branch Protection while using Python's async/await model to represent
independent workflow events and concurrent status-check execution.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Set


class PullRequestState(Enum):
    DRAFT = "draft"
    OPEN = "open"
    CLOSED = "closed"
    MERGED = "merged"


class ReviewState(Enum):
    COMMENTED = "commented"
    CHANGES_REQUESTED = "changes_requested"
    APPROVED = "approved"
    DISMISSED = "dismissed"


@dataclass(frozen=True)
class Commit:
    sha: str
    message: str


@dataclass
class Review:
    reviewer: str
    state: ReviewState
    commit_sha: str
    comments: List[str] = field(default_factory=list)


@dataclass
class StatusCheck:
    name: str
    required: bool
    passed: bool = False
    running: bool = False
    error: str | None = None


@dataclass
class BranchProtection:
    required_reviews: int
    required_status_checks: Set[str]
    restrict_direct_push: bool = True
    restrict_force_push: bool = True
    restrict_deletion: bool = True
    require_conversation_resolution: bool = True
    require_linear_history: bool = True
    allow_admin_bypass: bool = False


@dataclass
class PullRequest:
    number: int
    source_branch: str
    target_branch: str
    commits: List[Commit]
    state: PullRequestState = PullRequestState.OPEN
    reviews: List[Review] = field(default_factory=list)
    conversations_open: int = 0
    checks: Dict[str, StatusCheck] = field(default_factory=dict)
    base_sha: str = "base-001"

    @property
    def head_sha(self) -> str:
        if not self.commits:
            raise ValueError("A Pull Request must contain at least one commit.")
        return self.commits[-1].sha


class Repository:
    def __init__(self, protection: BranchProtection) -> None:
        self.protection = protection
        self.protected_branches = {"main"}
        self.branch_heads = {"main": "base-001", "feature/review-engine": "pr-001"}
        self.pull_requests: Dict[int, PullRequest] = {}

    def create_pull_request(
        self,
        number: int,
        source: str,
        target: str,
        commits: List[Commit],
        draft: bool = False,
    ) -> PullRequest:
        if target not in self.protected_branches:
            raise ValueError("Target branch is not governed by branch protection.")
        if source == target:
            raise ValueError("Source and target branches must differ.")
        if not commits:
            raise ValueError("A Pull Request cannot be created without commits.")

        pr = PullRequest(
            number=number,
            source_branch=source,
            target_branch=target,
            commits=commits,
            state=PullRequestState.DRAFT if draft else PullRequestState.OPEN,
        )

        for check_name in self.protection.required_status_checks:
            pr.checks[check_name] = StatusCheck(check_name, required=True)

        self.pull_requests[number] = pr
        return pr

    def mark_ready(self, pr: PullRequest) -> None:
        if pr.state != PullRequestState.DRAFT:
            raise ValueError("Only draft Pull Requests can be marked ready.")
        pr.state = PullRequestState.OPEN

    def add_commit(self, pr: PullRequest, commit: Commit) -> None:
        if pr.state != PullRequestState.OPEN:
            raise ValueError("Commits can only be added to an open Pull Request.")
        pr.commits.append(commit)

        # A new head invalidates previous approvals in this simulation.
        for review in pr.reviews:
            if review.state == ReviewState.APPROVED:
                review.state = ReviewState.DISMISSED

    def request_review(self, pr: PullRequest, reviewer: str) -> None:
        if pr.state != PullRequestState.OPEN:
            raise ValueError("Review requests require an open Pull Request.")
        if not reviewer.strip():
            raise ValueError("Reviewer identity cannot be empty.")

    def submit_review(
        self,
        pr: PullRequest,
        reviewer: str,
        state: ReviewState,
        comments: List[str] | None = None,
    ) -> None:
        if pr.state != PullRequestState.OPEN:
            raise ValueError("Reviews can only be submitted on an open Pull Request.")

        pr.reviews.append(
            Review(
                reviewer=reviewer,
                state=state,
                commit_sha=pr.head_sha,
                comments=comments or [],
            )
        )

    def resolve_conversation(self, pr: PullRequest) -> None:
        if pr.conversations_open <= 0:
            raise ValueError("There are no unresolved conversations.")
        pr.conversations_open -= 1

    async def run_status_check(self, pr: PullRequest, name: str) -> None:
        check = pr.checks.get(name)
        if check is None:
            raise ValueError(f"Unknown status check: {name}")

        check.running = True
        await asyncio.sleep(0.08)

        # The checks inspect the current PR head. A real CI service would
        # execute tests against a checked-out commit rather than this simulation.
        if not pr.commits:
            check.passed = False
            check.error = "No commits available."
        elif "security" in name.lower():
            check.passed = all("secret" not in c.message.lower() for c in pr.commits)
            check.error = None if check.passed else "Potential secret reference detected."
        else:
            check.passed = True
            check.error = None

        check.running = False

    async def run_all_checks(self, pr: PullRequest) -> None:
        # Independent CI checks can run concurrently rather than serially.
        await asyncio.gather(
            *(self.run_status_check(pr, name) for name in pr.checks)
        )

    def merge_eligibility(self, pr: PullRequest) -> tuple[bool, List[str]]:
        failures: List[str] = []

        if pr.state != PullRequestState.OPEN:
            failures.append("Pull Request is not open.")

        if not pr.commits:
            failures.append("Pull Request has no commits.")

        for check_name in self.protection.required_status_checks:
            check = pr.checks.get(check_name)
            if check is None or not check.passed:
                failures.append(f"Required status check failed: {check_name}")

        approvals = {
            review.reviewer
            for review in pr.reviews
            if review.state == ReviewState.APPROVED
            and review.commit_sha == pr.head_sha
        }

        if len(approvals) < self.protection.required_reviews:
            failures.append(
                f"Requires {self.protection.required_reviews} current approval(s); "
                f"found {len(approvals)}."
            )

        if self.protection.require_conversation_resolution and pr.conversations_open:
            failures.append("Unresolved review conversations remain.")

        if self.protection.require_linear_history and len(pr.commits) > 1:
            # This simplified model treats commits whose messages contain
            # "merge commit" as non-linear history.
            if any("merge commit" in c.message.lower() for c in pr.commits):
                failures.append("Branch protection requires linear history.")

        return not failures, failures

    def merge(self, pr: PullRequest) -> None:
        eligible, failures = self.merge_eligibility(pr)
        if not eligible:
            raise RuntimeError("Merge rejected: " + "; ".join(failures))

        self.branch_heads[pr.target_branch] = pr.head_sha
        pr.state = PullRequestState.MERGED


async def main() -> None:
    protection = BranchProtection(
        required_reviews=2,
        required_status_checks={"unit-tests", "security-scan"},
    )
    repository = Repository(protection)

    pr = repository.create_pull_request(
        number=42,
        source="feature/review-engine",
        target="main",
        commits=[
            Commit("a101", "Implement merge eligibility"),
            Commit("a102", "Add security validation"),
        ],
        draft=True,
    )

    repository.mark_ready(pr)
    repository.request_review(pr, "alice")
    repository.request_review(pr, "bob")

    # Status checks are independent asynchronous operations.
    await repository.run_all_checks(pr)

    repository.submit_review(pr, "alice", ReviewState.APPROVED)

    eligible, failures = repository.merge_eligibility(pr)
    print("Before second approval:", eligible)
    for failure in failures:
        print(" -", failure)

    repository.submit_review(
        pr,
        "bob",
        ReviewState.CHANGES_REQUESTED,
        ["Please clarify the branch synchronization policy."],
    )

    eligible, failures = repository.merge_eligibility(pr)
    print("\nAfter requested changes:", eligible)
    for failure in failures:
        print(" -", failure)

    repository.submit_review(pr, "bob", ReviewState.APPROVED)
    pr.conversations_open = 1

    eligible, failures = repository.merge_eligibility(pr)
    print("\nWith unresolved conversation:", eligible)
    for failure in failures:
        print(" -", failure)

    repository.resolve_conversation(pr)

    try:
        repository.merge(pr)
        print("\nPull Request merged:", pr.number)
    except RuntimeError as exc:
        print("\nMerge failed:", exc)


if __name__ == "__main__":
    asyncio.run(main())
