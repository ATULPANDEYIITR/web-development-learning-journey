from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable


class WorkflowError(Exception):
    """Raised when a repository operation violates a workflow rule."""


class PullRequestState(str, Enum):
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
    PASSED = "passed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MergeStrategy(str, Enum):
    MERGE_COMMIT = "merge_commit"
    SQUASH = "squash"
    REBASE = "rebase"


@dataclass(frozen=True)
class Commit:
    sha: str
    parents: tuple[str, ...]
    message: str
    tree: dict[str, str]


@dataclass
class Branch:
    name: str
    head_sha: str
    protected: bool = False
    deleted: bool = False


@dataclass(frozen=True)
class Reviewer:
    username: str
    active: bool = True
    can_review: bool = True
    is_admin: bool = False


@dataclass(frozen=True)
class Review:
    reviewer: str
    state: ReviewState
    reviewed_head: str
    sequence: int


@dataclass
class ReviewThread:
    thread_id: str
    path: str
    line: int
    created_by: str
    resolved: bool = False
    resolved_by: str | None = None


@dataclass(frozen=True)
class StatusCheck:
    name: str
    head_sha: str
    state: CheckState
    details: str = ""


@dataclass(frozen=True)
class ProtectionPolicy:
    minimum_approvals: int = 1
    required_checks: frozenset[str] = frozenset()
    require_conversation_resolution: bool = True
    require_linear_history: bool = False
    require_pull_request: bool = True
    allow_merge_commit: bool = True
    allow_squash: bool = True
    allow_rebase: bool = True
    allow_direct_push: bool = False
    allow_force_push: bool = False
    prohibit_branch_deletion: bool = True
    allow_admin_bypass: bool = False


@dataclass
class PullRequest:
    number: int
    author: str
    source_branch: str
    target_branch: str
    base_sha_at_open: str
    base_sha_at_sync: str
    source_head_sha: str
    state: PullRequestState
    draft: bool
    reviews: list[Review] = field(default_factory=list)
    threads: dict[str, ReviewThread] = field(default_factory=dict)
    checks: dict[tuple[str, str], StatusCheck] = field(default_factory=dict)
    merge_strategy: MergeStrategy | None = None
    merged_sha: str | None = None


@dataclass(frozen=True)
class MergeDecision:
    eligible: bool
    reasons: tuple[str, ...]
    approvals: int


class Repository:
    """
    In-memory repository workflow simulator.

    Commit identifiers are deterministic SHA-256 values. Trees are simple
    path-to-content mappings; this is a workflow model, not a Git object store.
    """

    def __init__(self, name: str, initial_files: dict[str, str]) -> None:
        if not name.strip():
            raise ValueError("Repository name cannot be empty.")

        self.name = name
        self.commits: dict[str, Commit] = {}
        self.branches: dict[str, Branch] = {}
        self.reviewers: dict[str, Reviewer] = {}
        self.pull_requests: dict[int, PullRequest] = {}
        self.policies: dict[str, ProtectionPolicy] = {}
        self._review_sequence = 0

        root = self._create_commit((), "Initial repository state", initial_files)
        self.branches["main"] = Branch("main", root.sha, protected=True)

    def _create_commit(
        self,
        parents: Iterable[str],
        message: str,
        tree: dict[str, str],
    ) -> Commit:
        parent_tuple = tuple(parents)
        for parent in parent_tuple:
            if parent not in self.commits:
                raise WorkflowError(f"Unknown parent commit: {parent}")

        normalized_tree = dict(sorted(tree.items()))
        payload = {
            "parents": parent_tuple,
            "message": message,
            "tree": normalized_tree,
        }
        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        sha = hashlib.sha256(serialized.encode("utf-8")).hexdigest()

        commit = Commit(
            sha=sha,
            parents=parent_tuple,
            message=message,
            tree=normalized_tree,
        )
        self.commits[sha] = commit
        return commit

    def add_reviewer(self, reviewer: Reviewer) -> None:
        if not reviewer.username.strip():
            raise ValueError("Reviewer username cannot be empty.")
        self.reviewers[reviewer.username] = reviewer

    def set_protection(
        self,
        branch_name: str,
        policy: ProtectionPolicy,
    ) -> None:
        self._require_branch(branch_name)
        if policy.minimum_approvals < 0:
            raise ValueError("Minimum approvals cannot be negative.")
        self.policies[branch_name] = policy
        self.branches[branch_name].protected = True

    def _require_branch(self, branch_name: str) -> Branch:
        branch = self.branches.get(branch_name)
        if branch is None or branch.deleted:
            raise WorkflowError(f"Branch does not exist: {branch_name}")
        return branch

    def create_branch(self, name: str, from_branch: str = "main") -> None:
        if not name.strip() or name in self.branches:
            raise WorkflowError(f"Invalid or duplicate branch name: {name}")
        source = self._require_branch(from_branch)
        self.branches[name] = Branch(name, source.head_sha)

    def commit(
        self,
        branch_name: str,
        author: str,
        message: str,
        changes: dict[str, str | None],
    ) -> str:
        """
        Create a commit on a branch.

        A value of None deletes a path. Empty paths and absolute paths are
        rejected to avoid ambiguous or unsafe repository paths.
        """
        branch = self._require_branch(branch_name)
        if not author.strip() or not message.strip():
            raise ValueError("Commit author and message are required.")

        if branch.protected:
            policy = self.policies.get(branch_name, ProtectionPolicy())
            if policy.require_pull_request or not policy.allow_direct_push:
                raise WorkflowError(
                    f"Direct pushes to protected branch '{branch_name}' are blocked."
                )

        tree = dict(self.commits[branch.head_sha].tree)
        for path, content in changes.items():
            self._validate_path(path)
            if content is None:
                tree.pop(path, None)
            else:
                tree[path] = content

        commit = self._create_commit((branch.head_sha,), message, tree)
        branch.head_sha = commit.sha
        self._refresh_source_pull_requests(branch_name, commit.sha)
        return commit.sha

    @staticmethod
    def _validate_path(path: str) -> None:
        if not path or path.startswith("/") or "\\" in path:
            raise ValueError(f"Invalid repository path: {path!r}")
        parts = path.split("/")
        if any(part in {"", ".", ".."} for part in parts):
            raise ValueError(f"Unsafe repository path: {path!r}")

    def open_pull_request(
        self,
        number: int,
        author: str,
        source_branch: str,
        target_branch: str = "main",
        draft: bool = True,
    ) -> PullRequest:
        if number <= 0 or number in self.pull_requests:
            raise WorkflowError("Pull Request number must be unique and positive.")
        if not author.strip():
            raise ValueError("Pull Request author is required.")

        source = self._require_branch(source_branch)
        target = self._require_branch(target_branch)
        if source_branch == target_branch:
            raise WorkflowError("Source and target branches must differ.")

        pr = PullRequest(
            number=number,
            author=author,
            source_branch=source_branch,
            target_branch=target_branch,
            base_sha_at_open=target.head_sha,
            base_sha_at_sync=target.head_sha,
            source_head_sha=source.head_sha,
            state=PullRequestState.DRAFT if draft else PullRequestState.OPEN,
            draft=draft,
        )
        self.pull_requests[number] = pr
        return pr

    def _get_pr(self, number: int) -> PullRequest:
        pr = self.pull_requests.get(number)
        if pr is None:
            raise WorkflowError(f"Pull Request #{number} does not exist.")
        return pr

    def mark_ready(self, number: int) -> None:
        pr = self._get_pr(number)
        if pr.state != PullRequestState.DRAFT:
            raise WorkflowError("Only a draft Pull Request can be marked ready.")
        pr.draft = False
        pr.state = PullRequestState.OPEN

    def close_pull_request(self, number: int) -> None:
        pr = self._get_pr(number)
        if pr.state not in {PullRequestState.OPEN, PullRequestState.DRAFT}:
            raise WorkflowError("Only open or draft Pull Requests can be closed.")
        pr.state = PullRequestState.CLOSED

    def reopen_pull_request(self, number: int) -> None:
        pr = self._get_pr(number)
        if pr.state != PullRequestState.CLOSED:
            raise WorkflowError("Only a closed, unmerged Pull Request can be reopened.")
        pr.state = PullRequestState.OPEN
        pr.draft = False

    def _refresh_source_pull_requests(self, branch_name: str, new_sha: str) -> None:
        for pr in self.pull_requests.values():
            if (
                pr.source_branch == branch_name
                and pr.state in {PullRequestState.OPEN, PullRequestState.DRAFT}
            ):
                # Existing reviews and checks remain recorded but become stale.
                pr.source_head_sha = new_sha

    def _diff(
        self,
        old_tree: dict[str, str],
        new_tree: dict[str, str],
    ) -> dict[str, tuple[str | None, str | None]]:
        result: dict[str, tuple[str | None, str | None]] = {}
        for path in old_tree.keys() | new_tree.keys():
            old_value = old_tree.get(path)
            new_value = new_tree.get(path)
            if old_value != new_value:
                result[path] = (old_value, new_value)
        return result

    def proposed_changeset(self, number: int) -> dict[str, tuple[str | None, str | None]]:
        pr = self._get_pr(number)
        base_tree = self.commits[pr.base_sha_at_sync].tree
        source_tree = self.commits[pr.source_head_sha].tree
        return self._diff(base_tree, source_tree)

    def synchronize_base(self, number: int) -> tuple[str, ...]:
        """
        Merge the current target snapshot into the source branch.

        Conflicts are detected when both sides changed a path differently
        from the last synchronized base. No branch is modified on conflict.
        """
        pr = self._get_pr(number)
        if pr.state not in {PullRequestState.OPEN, PullRequestState.DRAFT}:
            raise WorkflowError("Only an open or draft Pull Request can be synchronized.")

        source = self._require_branch(pr.source_branch)
        target = self._require_branch(pr.target_branch)

        base_tree = self.commits[pr.base_sha_at_sync].tree
        source_tree = self.commits[source.head_sha].tree
        target_tree = self.commits[target.head_sha].tree

        conflicts: list[str] = []
        merged_tree = dict(source_tree)

        for path in base_tree.keys() | source_tree.keys() | target_tree.keys():
            base_value = base_tree.get(path)
            source_value = source_tree.get(path)
            target_value = target_tree.get(path)

            source_changed = source_value != base_value
            target_changed = target_value != base_value

            if source_changed and target_changed and source_value != target_value:
                conflicts.append(path)
            elif target_changed:
                if target_value is None:
                    merged_tree.pop(path, None)
                else:
                    merged_tree[path] = target_value

        if conflicts:
            return tuple(sorted(conflicts))

        sync_commit = self._create_commit(
            (source.head_sha, target.head_sha),
            f"Synchronize {pr.target_branch} into {pr.source_branch}",
            merged_tree,
        )
        source.head_sha = sync_commit.sha
        pr.source_head_sha = sync_commit.sha
        pr.base_sha_at_sync = target.head_sha
        return ()

    def submit_review(
        self,
        number: int,
        reviewer_name: str,
        state: ReviewState,
    ) -> Review:
        pr = self._get_pr(number)
        reviewer = self.reviewers.get(reviewer_name)

        if reviewer is None or not reviewer.active or not reviewer.can_review:
            raise WorkflowError(f"{reviewer_name} is not an eligible reviewer.")
        if reviewer_name == pr.author:
            raise WorkflowError("An author cannot approve their own Pull Request.")
        if pr.state != PullRequestState.OPEN or pr.draft:
            raise WorkflowError("Reviews require an open, non-draft Pull Request.")
        if state == ReviewState.DISMISSED:
            raise WorkflowError("Use dismiss_review to dismiss an existing review.")

        self._review_sequence += 1
        review = Review(
            reviewer=reviewer_name,
            state=state,
            reviewed_head=pr.source_head_sha,
            sequence=self._review_sequence,
        )
        pr.reviews.append(review)
        return review

    def dismiss_review(self, number: int, reviewer_name: str) -> None:
        pr = self._get_pr(number)
        latest = self._latest_reviews(pr).get(reviewer_name)
        if latest is None:
            raise WorkflowError("No review exists for this reviewer.")

        self._review_sequence += 1
        pr.reviews.append(
            Review(
                reviewer=reviewer_name,
                state=ReviewState.DISMISSED,
                reviewed_head=latest.reviewed_head,
                sequence=self._review_sequence,
            )
        )

    @staticmethod
    def _latest_reviews(pr: PullRequest) -> dict[str, Review]:
        latest: dict[str, Review] = {}
        for review in pr.reviews:
            previous = latest.get(review.reviewer)
            if previous is None or review.sequence > previous.sequence:
                latest[review.reviewer] = review
        return latest

    def add_review_thread(
        self,
        number: int,
        thread_id: str,
        path: str,
        line: int,
        created_by: str,
    ) -> None:
        pr = self._get_pr(number)
        self._validate_path(path)
        if not thread_id.strip() or line < 1:
            raise ValueError("A thread ID and positive line number are required.")
        if thread_id in pr.threads:
            raise WorkflowError(f"Duplicate review thread: {thread_id}")
        pr.threads[thread_id] = ReviewThread(
            thread_id=thread_id,
            path=path,
            line=line,
            created_by=created_by,
        )

    def resolve_thread(
        self,
        number: int,
        thread_id: str,
        resolved_by: str,
    ) -> None:
        pr = self._get_pr(number)
        thread = pr.threads.get(thread_id)
        if thread is None:
            raise WorkflowError(f"Review thread does not exist: {thread_id}")
        if not resolved_by.strip():
            raise ValueError("Resolver identity is required.")
        thread.resolved = True
        thread.resolved_by = resolved_by

    def record_check(
        self,
        number: int,
        check_name: str,
        state: CheckState,
        details: str = "",
    ) -> None:
        pr = self._get_pr(number)
        if not check_name.strip():
            raise ValueError("Status check name cannot be empty.")

        check = StatusCheck(
            name=check_name,
            head_sha=pr.source_head_sha,
            state=state,
            details=details,
        )
        pr.checks[(pr.source_head_sha, check_name)] = check

    def _eligible_approvals(self, pr: PullRequest) -> tuple[int, list[str]]:
        approvals: list[str] = []
        current_reviews = self._latest_reviews(pr)

        for reviewer_name, review in current_reviews.items():
            reviewer = self.reviewers.get(reviewer_name)
            if (
                reviewer is not None
                and reviewer.active
                and reviewer.can_review
                and reviewer_name != pr.author
                and review.state == ReviewState.APPROVED
                and review.reviewed_head == pr.source_head_sha
            ):
                approvals.append(reviewer_name)

        return len(approvals), sorted(approvals)

    def evaluate_merge(
        self,
        number: int,
        strategy: MergeStrategy,
        actor: str,
    ) -> MergeDecision:
        pr = self._get_pr(number)
        source = self._require_branch(pr.source_branch)
        target = self._require_branch(pr.target_branch)
        policy = self.policies.get(pr.target_branch, ProtectionPolicy())

        reasons: list[str] = []
        approvals, _ = self._eligible_approvals(pr)

        if pr.state != PullRequestState.OPEN or pr.draft:
            reasons.append("Pull Request must be open and ready for review.")
        if source.head_sha != pr.source_head_sha:
            reasons.append("Pull Request source head is not current.")
        if target.head_sha != pr.base_sha_at_sync:
            reasons.append("Target branch advanced; synchronize the base branch.")

        actor_record = self.reviewers.get(actor)
        bypass = bool(
            actor_record
            and actor_record.active
            and actor_record.is_admin
            and policy.allow_admin_bypass
        )

        latest = self._latest_reviews(pr)
        current_changes_requested = any(
            review.state == ReviewState.CHANGES_REQUESTED
            and review.reviewed_head == pr.source_head_sha
            for review in latest.values()
        )

        if not bypass:
            if approvals < policy.minimum_approvals:
                reasons.append(
                    f"Requires {policy.minimum_approvals} current approvals; "
                    f"found {approvals}."
                )

            if current_changes_requested:
                reasons.append("A current review requests changes.")

            for check_name in sorted(policy.required_checks):
                check = pr.checks.get((pr.source_head_sha, check_name))
                if check is None or check.state != CheckState.PASSED:
                    reasons.append(
                        f"Required check '{check_name}' has not passed on the current head."
                    )

            if policy.require_conversation_resolution:
                unresolved = [
                    thread.thread_id
                    for thread in pr.threads.values()
                    if not thread.resolved
                ]
                if unresolved:
                    reasons.append(
                        "Unresolved review conversations: " + ", ".join(sorted(unresolved))
                    )

            if strategy == MergeStrategy.MERGE_COMMIT:
                allowed = policy.allow_merge_commit
            elif strategy == MergeStrategy.SQUASH:
                allowed = policy.allow_squash
            else:
                allowed = policy.allow_rebase

            if not allowed:
                reasons.append(f"Merge strategy '{strategy.value}' is not permitted.")

            if policy.require_linear_history and strategy == MergeStrategy.MERGE_COMMIT:
                reasons.append("A merge commit violates the linear-history requirement.")

        return MergeDecision(
            eligible=not reasons,
            reasons=tuple(reasons),
            approvals=approvals,
        )

    def merge_pull_request(
        self,
        number: int,
        strategy: MergeStrategy,
        actor: str,
    ) -> str:
        decision = self.evaluate_merge(number, strategy, actor)
        if not decision.eligible:
            raise WorkflowError(
                "Merge blocked:\n- " + "\n- ".join(decision.reasons)
            )

        pr = self._get_pr(number)
        source = self._require_branch(pr.source_branch)
        target = self._require_branch(pr.target_branch)

        if strategy == MergeStrategy.MERGE_COMMIT:
            parents = (target.head_sha, source.head_sha)
        else:
            # The simulator applies the source tree as a single new target commit.
            # It does not reconstruct individual rebased Git commits.
            parents = (target.head_sha,)

        merge_commit = self._create_commit(
            parents,
            f"Merge PR #{number} using {strategy.value}",
            dict(self.commits[source.head_sha].tree),
        )
        target.head_sha = merge_commit.sha
        pr.state = PullRequestState.MERGED
        pr.merge_strategy = strategy
        pr.merged_sha = merge_commit.sha
        return merge_commit.sha

    def delete_branch(self, branch_name: str, actor: str) -> None:
        branch = self._require_branch(branch_name)
        if branch_name == "main":
            raise WorkflowError("The default branch cannot be deleted.")

        policy = self.policies.get(branch_name, ProtectionPolicy())
        actor_record = self.reviewers.get(actor)

        if branch.protected and policy.prohibit_branch_deletion:
            raise WorkflowError(f"Deletion of protected branch '{branch_name}' is blocked.")
        if not actor_record or not actor_record.active:
            raise WorkflowError("An active repository member is required.")

        branch.deleted = True


def run_demo() -> None:
    repository = Repository(
        "payments-service",
        {
            "README.md": "Payments service",
            "src/payment.py": "def pay(amount): return amount",
        },
    )

    repository.add_reviewer(Reviewer("alice", is_admin=True))
    repository.add_reviewer(Reviewer("bob"))
    repository.add_reviewer(Reviewer("carol"))
    repository.add_reviewer(Reviewer("dave", can_review=False))

    repository.set_protection(
        "main",
        ProtectionPolicy(
            minimum_approvals=2,
            required_checks=frozenset({"unit-tests", "security-scan"}),
            require_conversation_resolution=True,
            require_linear_history=True,
            allow_merge_commit=False,
            allow_squash=True,
            allow_rebase=True,
            allow_direct_push=False,
            allow_force_push=False,
            prohibit_branch_deletion=True,
        ),
    )

    repository.create_branch("feature/payment-validation")
    repository.commit(
        "feature/payment-validation",
        "alice",
        "Validate payment amount",
        {"src/payment.py": "def pay(amount):\n    if amount <= 0:\n        raise ValueError('amount must be positive')\n    return amount"},
    )

    pr = repository.open_pull_request(
        42,
        author="alice",
        source_branch="feature/payment-validation",
        draft=True,
    )

    print(f"PR #{pr.number}: {pr.state.value}")
    repository.mark_ready(42)

    repository.add_review_thread(
        42, "thread-1", "src/payment.py", 2, "bob"
    )

    repository.submit_review(42, "bob", ReviewState.APPROVED)
    repository.submit_review(42, "carol", ReviewState.APPROVED)
    repository.record_check(42, "unit-tests", CheckState.PASSED)
    repository.record_check(42, "security-scan", CheckState.PASSED)

    # A new source commit makes earlier approvals and checks stale.
    repository.commit(
        "feature/payment-validation",
        "alice",
        "Add payment boundary test",
        {"tests/test_payment.py": "assert pay(10) == 10"},
    )

    stale_decision = repository.evaluate_merge(
        42, MergeStrategy.SQUASH, actor="alice"
    )
    print("\nAfter source branch changes:")
    print("Eligible:", stale_decision.eligible)
    for reason in stale_decision.reasons:
        print(" -", reason)

    # Reviewers must inspect the new head, and CI must test that exact head.
    repository.submit_review(42, "bob", ReviewState.APPROVED)
    repository.submit_review(42, "carol", ReviewState.APPROVED)
    repository.record_check(42, "unit-tests", CheckState.PASSED)
    repository.record_check(42, "security-scan", CheckState.PASSED)
    repository.resolve_thread(42, "thread-1", "alice")

    decision = repository.evaluate_merge(
        42, MergeStrategy.SQUASH, actor="alice"
    )
    print("\nAfter current approvals, checks, and resolved discussion:")
    print("Eligible:", decision.eligible)
    print("Current approvals:", decision.approvals)

    if decision.eligible:
        merge_sha = repository.merge_pull_request(
            42, MergeStrategy.SQUASH, actor="alice"
        )
        print("Merged commit:", merge_sha)
        print("PR state:", repository.pull_requests[42].state.value)

    # A protected branch cannot be modified through an ordinary direct push.
    try:
        repository.commit("main", "alice", "Bypass Pull Request", {"README.md": "Changed"})
    except WorkflowError as error:
        print("\nExpected protection failure:", error)

    # Review eligibility is validated before a review event is recorded.
    try:
        repository.submit_review(42, "dave", ReviewState.APPROVED)
    except WorkflowError as error:
        print("Expected reviewer failure:", error)

    # A merged Pull Request is terminal and cannot be reopened.
    try:
        repository.reopen_pull_request(42)
    except WorkflowError as error:
        print("Expected lifecycle failure:", error)


if __name__ == "__main__":
    run_demo()
