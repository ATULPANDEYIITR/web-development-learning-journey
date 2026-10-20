from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from functools import reduce
from typing import Callable, Iterable, Mapping, Sequence


class PullRequestState(Enum):
    DRAFT = "draft"
    OPEN = "open"
    CLOSED = "closed"
    MERGED = "merged"


class ReviewState(Enum):
    COMMENTED = "commented"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"
    DISMISSED = "dismissed"


class MergeStrategy(Enum):
    MERGE_COMMIT = "merge_commit"
    SQUASH = "squash"
    REBASE = "rebase"


@dataclass(frozen=True)
class Commit:
    sha: str
    message: str


@dataclass(frozen=True)
class Review:
    reviewer: str
    state: ReviewState
    comments: tuple[str, ...] = ()


@dataclass(frozen=True)
class StatusCheck:
    name: str
    passed: bool
    required: bool = True


@dataclass(frozen=True)
class BranchProtection:
    required_reviews: int = 1
    required_checks: tuple[str, ...] = ()
    require_conversation_resolution: bool = True
    require_linear_history: bool = False
    allow_direct_push: bool = False
    allow_force_push: bool = False
    allow_deletion: bool = False
    allow_admin_bypass: bool = False


@dataclass(frozen=True)
class PullRequest:
    number: int
    source_branch: str
    target_branch: str
    commits: tuple[Commit, ...]
    state: PullRequestState = PullRequestState.DRAFT
    reviews: tuple[Review, ...] = ()
    checks: tuple[StatusCheck, ...] = ()
    unresolved_conversations: int = 0
    has_conflicts: bool = False
    synchronized_with_base: bool = True
    merge_strategy: MergeStrategy = MergeStrategy.SQUASH


@dataclass(frozen=True)
class Repository:
    name: str
    branches: Mapping[str, tuple[Commit, ...]]
    protected: Mapping[str, BranchProtection]
    pull_requests: tuple[PullRequest, ...] = ()


def compose(*functions: Callable) -> Callable:
    """Compose unary functions from right to left."""
    def composed(value):
        return reduce(lambda current, fn: fn(current), reversed(functions), value)

    return composed


def pipe(value, *functions: Callable):
    """Apply unary functions from left to right."""
    return reduce(lambda current, fn: fn(current), functions, value)


def map_commits(
    commits: Sequence[Commit],
    transform: Callable[[Commit], Commit],
) -> tuple[Commit, ...]:
    return tuple(map(transform, commits))


def filter_commits(
    commits: Sequence[Commit],
    predicate: Callable[[Commit], bool],
) -> tuple[Commit, ...]:
    return tuple(filter(predicate, commits))


def count_approvals(reviews: Iterable[Review]) -> int:
    return sum(
        1 for review in reviews
        if review.state == ReviewState.APPROVED
    )


def required_checks_passed(
    checks: Sequence[StatusCheck],
    policy: BranchProtection,
) -> bool:
    check_map = {check.name: check.passed for check in checks}
    return all(check_map.get(name, False) for name in policy.required_checks)


def has_requested_changes(reviews: Iterable[Review]) -> bool:
    return any(
        review.state == ReviewState.CHANGES_REQUESTED
        for review in reviews
    )


def merge_reasons(pr: PullRequest, policy: BranchProtection) -> tuple[str, ...]:
    reasons: list[str] = []

    if pr.state != PullRequestState.OPEN:
        reasons.append("pull request is not open")

    if not pr.commits:
        reasons.append("pull request contains no commits")

    if pr.source_branch == pr.target_branch:
        reasons.append("source and target branches are identical")

    if not pr.synchronized_with_base:
        reasons.append("source branch is behind the target branch")

    if pr.has_conflicts:
        reasons.append("merge conflicts must be resolved")

    if has_requested_changes(pr.reviews):
        reasons.append("a reviewer has requested changes")

    if count_approvals(pr.reviews) < policy.required_reviews:
        reasons.append("required approvals are missing")

    if not required_checks_passed(pr.checks, policy):
        reasons.append("required status checks have not passed")

    if (
        policy.require_conversation_resolution
        and pr.unresolved_conversations > 0
    ):
        reasons.append("review conversations remain unresolved")

    return tuple(reasons)


def can_merge(pr: PullRequest, policy: BranchProtection) -> bool:
    return not merge_reasons(pr, policy)


def open_draft(pr: PullRequest) -> PullRequest:
    if pr.state != PullRequestState.DRAFT:
        raise ValueError("only a draft pull request can be opened")
    return replace(pr, state=PullRequestState.OPEN)


def synchronize(pr: PullRequest) -> PullRequest:
    return replace(pr, synchronized_with_base=True, has_conflicts=False)


def add_review(pr: PullRequest, review: Review) -> PullRequest:
    if pr.state != PullRequestState.OPEN:
        raise ValueError("reviews can only be added to an open pull request")
    if not review.reviewer.strip():
        raise ValueError("reviewer name cannot be empty")
    return replace(pr, reviews=(*pr.reviews, review))


def update_check(
    pr: PullRequest,
    name: str,
    passed: bool,
) -> PullRequest:
    if not name.strip():
        raise ValueError("status-check name cannot be empty")

    updated = tuple(
        replace(check, passed=passed) if check.name == name
        else check
        for check in pr.checks
    )

    if all(check.name != name for check in pr.checks):
        updated = (*updated, StatusCheck(name=name, passed=passed))

    return replace(pr, checks=updated)


def resolve_conversation(pr: PullRequest) -> PullRequest:
    if pr.unresolved_conversations <= 0:
        return pr
    return replace(
        pr,
        unresolved_conversations=pr.unresolved_conversations - 1,
    )


def merge(pr: PullRequest, policy: BranchProtection) -> PullRequest:
    reasons = merge_reasons(pr, policy)
    if reasons:
        raise RuntimeError("cannot merge: " + "; ".join(reasons))
    return replace(pr, state=PullRequestState.MERGED)


def close(pr: PullRequest) -> PullRequest:
    if pr.state not in (PullRequestState.OPEN, PullRequestState.DRAFT):
        raise ValueError("only open or draft pull requests can be closed")
    return replace(pr, state=PullRequestState.CLOSED)


def reopen(pr: PullRequest) -> PullRequest:
    if pr.state != PullRequestState.CLOSED:
        raise ValueError("only closed pull requests can be reopened")
    return replace(pr, state=PullRequestState.OPEN)


def summarize(pr: PullRequest, policy: BranchProtection) -> dict:
    return {
        "number": pr.number,
        "state": pr.state.value,
        "source": pr.source_branch,
        "target": pr.target_branch,
        "commits": len(pr.commits),
        "approvals": count_approvals(pr.reviews),
        "required_approvals": policy.required_reviews,
        "checks_passed": required_checks_passed(pr.checks, policy),
        "unresolved_conversations": pr.unresolved_conversations,
        "mergeable": can_merge(pr, policy),
        "blocking_reasons": merge_reasons(pr, policy),
    }


def functional_commit_pipeline(
    commits: Sequence[Commit],
) -> tuple[str, ...]:
    normalize = lambda commit: replace(
        commit,
        message=" ".join(commit.message.strip().split()),
    )

    meaningful = lambda commit: len(commit.message.strip()) >= 8
    describe = lambda commit: f"{commit.sha}: {commit.message}"

    return pipe(
        commits,
        lambda values: map_commits(values, normalize),
        lambda values: filter_commits(values, meaningful),
        lambda values: tuple(map(describe, values)),
    )


def main() -> None:
    policy = BranchProtection(
        required_reviews=2,
        required_checks=("unit-tests", "security-scan"),
        require_conversation_resolution=True,
        require_linear_history=True,
        allow_direct_push=False,
        allow_force_push=False,
        allow_deletion=False,
    )

    commits = (
        Commit("a1b2c3d", " add repository workflow model "),
        Commit("b2c3d4e", "implement merge eligibility"),
        Commit("c3d4e5f", "fix"),
    )

    pr = PullRequest(
        number=42,
        source_branch="feature/governance-engine",
        target_branch="main",
        commits=commits,
        state=PullRequestState.DRAFT,
        unresolved_conversations=2,
        checks=(
            StatusCheck("unit-tests", True),
            StatusCheck("security-scan", False),
        ),
    )

    pr = open_draft(pr)

    pr = add_review(
        pr,
        Review(
            reviewer="reviewer-alice",
            state=ReviewState.APPROVED,
            comments=("Policy model is clear.",),
        ),
    )

    pr = add_review(
        pr,
        Review(
            reviewer="reviewer-bob",
            state=ReviewState.COMMENTED,
            comments=("Please resolve the policy discussion.",),
        ),
    )

    pr = update_check(pr, "security-scan", True)

    print("Functional commit pipeline:")
    for item in functional_commit_pipeline(pr.commits):
        print(" ", item)

    print("\nInitial merge evaluation:")
    print(summarize(pr, policy))

    pr = add_review(
        pr,
        Review(
            reviewer="reviewer-bob",
            state=ReviewState.APPROVED,
        ),
    )

    pr = resolve_conversation(pr)
    pr = resolve_conversation(pr)
    pr = synchronize(pr)

    print("\nAfter approvals, synchronization, and discussion resolution:")
    print(summarize(pr, policy))

    if can_merge(pr, policy):
        pr = merge(pr, policy)
        print("\nMerged:", pr.state.value)
    else:
        print("\nStill blocked:", merge_reasons(pr, policy))

    print("\nImmutability check:")
    print("Original commit message:", commits[0].message)
    print("Normalized commit message:", functional_commit_pipeline(commits)[0])


if __name__ == "__main__":
    main()
