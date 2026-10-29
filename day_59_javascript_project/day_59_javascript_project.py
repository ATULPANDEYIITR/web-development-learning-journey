from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, timezone
import json
import uuid


class PRState(Enum):
    DRAFT = "draft"
    OPEN = "open"
    CLOSED = "closed"
    MERGED = "merged"


class ReviewState(Enum):
    COMMENTED = "commented"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"
    DISMISSED = "dismissed"


class CheckState(Enum):
    PENDING = "pending"
    PASSING = "passing"
    FAILING = "failing"


class TaskState(Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class MergeStrategy(Enum):
    MERGE_COMMIT = "merge_commit"
    SQUASH = "squash"
    REBASE = "rebase"


@dataclass
class Commit:
    sha: str
    message: str
    author: str
    timestamp: str


@dataclass
class ReviewComment:
    id: str
    reviewer: str
    body: str
    resolved: bool = False


@dataclass
class Review:
    id: str
    reviewer: str
    state: ReviewState
    submitted_at: str
    commit_sha: str
    comments: List[ReviewComment] = field(default_factory=list)
    dismissed: bool = False


@dataclass
class StatusCheck:
    name: str
    state: CheckState
    commit_sha: str


@dataclass
class BranchProtection:
    required_reviews: int = 1
    required_status_checks: Set[str] = field(default_factory=set)
    restrict_direct_push: bool = True
    restrict_force_push: bool = True
    restrict_deletion: bool = True
    require_conversation_resolution: bool = True
    require_linear_history: bool = False
    allow_administrator_bypass: bool = False


@dataclass
class Branch:
    name: str
    protected: bool = False
    commits: List[Commit] = field(default_factory=list)


@dataclass
class PullRequest:
    number: int
    title: str
    source_branch: str
    target_branch: str
    author: str
    state: PRState
    commits: List[Commit] = field(default_factory=list)
    reviewers_requested: Set[str] = field(default_factory=set)
    reviews: List[Review] = field(default_factory=list)
    checks: Dict[str, StatusCheck] = field(default_factory=dict)
    merge_strategy: Optional[MergeStrategy] = None
    reopened_count: int = 0

    @property
    def head_sha(self) -> Optional[str]:
        return self.commits[-1].sha if self.commits else None


@dataclass
class Task:
    id: str
    title: str
    description: str
    state: TaskState
    priority: str
    linked_pr: Optional[int] = None


class Repository:
    def __init__(self, name: str, owner: str):
        self.name = name
        self.owner = owner
        self.branches: Dict[str, Branch] = {}
        self.pull_requests: Dict[int, PullRequest] = {}
        self.protection: Dict[str, BranchProtection] = {}
        self.tasks: Dict[str, Task] = {}
        self.next_pr_number = 1

    @staticmethod
    def now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def new_sha() -> str:
        return uuid.uuid4().hex[:12]

    def create_branch(self, name: str, base: Optional[str] = None) -> None:
        if name in self.branches:
            raise ValueError(f"Branch already exists: {name}")

        commits = list(self.branches[base].commits) if base else []
        self.branches[name] = Branch(name=name, commits=commits)

    def protect_branch(self, name: str, policy: BranchProtection) -> None:
        if name not in self.branches:
            raise ValueError("Cannot protect a nonexistent branch.")
        self.protection[name] = policy
        self.branches[name].protected = True

    def commit(self, branch_name: str, author: str, message: str) -> Commit:
        branch = self._branch(branch_name)
        if not message.strip():
            raise ValueError("Commit message cannot be empty.")

        commit = Commit(
            sha=self.new_sha(),
            message=message.strip(),
            author=author,
            timestamp=self.now(),
        )
        branch.commits.append(commit)
        return commit

    def create_pull_request(
        self,
        title: str,
        source: str,
        target: str,
        author: str,
        draft: bool = False,
    ) -> PullRequest:
        self._branch(source)
        self._branch(target)

        if source == target:
            raise ValueError("Source and target branches must differ.")

        if not self.branches[source].commits:
            raise ValueError("A pull request requires at least one source commit.")

        pr = PullRequest(
            number=self.next_pr_number,
            title=title.strip(),
            source_branch=source,
            target_branch=target,
            author=author,
            state=PRState.DRAFT if draft else PRState.OPEN,
            commits=list(self.branches[source].commits),
        )
        self.pull_requests[pr.number] = pr
        self.next_pr_number += 1
        return pr

    def mark_ready(self, pr_number: int) -> None:
        pr = self._pr(pr_number)
        if pr.state != PRState.DRAFT:
            raise ValueError("Only draft pull requests can be marked ready.")
        pr.state = PRState.OPEN

    def request_review(self, pr_number: int, reviewer: str) -> None:
        pr = self._pr(pr_number)
        if pr.state not in {PRState.DRAFT, PRState.OPEN}:
            raise ValueError("Reviews cannot be requested on a closed or merged PR.")
        if reviewer == pr.author:
            raise ValueError("The author cannot be the sole requested reviewer.")
        pr.reviewers_requested.add(reviewer)

    def submit_review(
        self,
        pr_number: int,
        reviewer: str,
        state: ReviewState,
        body: str = "",
    ) -> Review:
        pr = self._pr(pr_number)

        if pr.state != PRState.OPEN:
            raise ValueError("Only open pull requests can receive reviews.")

        if reviewer == pr.author:
            raise ValueError("Authors cannot approve their own pull request.")

        if reviewer not in pr.reviewers_requested:
            raise ValueError("Reviewer was not requested for this pull request.")

        if not body.strip() and state == ReviewState.COMMENTED:
            raise ValueError("A comment review requires a non-empty body.")

        review = Review(
            id=uuid.uuid4().hex[:10],
            reviewer=reviewer,
            state=state,
            submitted_at=self.now(),
            commit_sha=pr.head_sha or "",
        )
        pr.reviews.append(review)
        return review

    def add_comment(
        self,
        pr_number: int,
        review_id: str,
        body: str,
    ) -> ReviewComment:
        pr = self._pr(pr_number)
        review = next((r for r in pr.reviews if r.id == review_id), None)
        if review is None:
            raise ValueError("Review not found.")
        if not body.strip():
            raise ValueError("Comment cannot be empty.")

        comment = ReviewComment(
            id=uuid.uuid4().hex[:10],
            reviewer=review.reviewer,
            body=body.strip(),
        )
        review.comments.append(comment)
        return comment

    def resolve_comment(self, pr_number: int, comment_id: str) -> None:
        pr = self._pr(pr_number)
        for review in pr.reviews:
            for comment in review.comments:
                if comment.id == comment_id:
                    comment.resolved = True
                    return
        raise ValueError("Review comment not found.")

    def set_status(self, pr_number: int, name: str, state: CheckState) -> None:
        pr = self._pr(pr_number)
        if pr.head_sha is None:
            raise ValueError("Pull request has no commits.")
        pr.checks[name] = StatusCheck(name, state, pr.head_sha)

    def synchronize(self, pr_number: int) -> Commit:
        pr = self._pr(pr_number)
        source = self._branch(pr.source_branch)
        target = self._branch(pr.target_branch)

        if not target.commits:
            raise ValueError("Target branch has no base commit.")

        existing = {commit.sha for commit in source.commits}
        additions = [c for c in target.commits if c.sha not in existing]

        if additions:
            source.commits.extend(additions)

        pr.commits = list(source.commits)
        return pr.commits[-1]

    def close(self, pr_number: int) -> None:
        pr = self._pr(pr_number)
        if pr.state == PRState.MERGED:
            raise ValueError("Merged pull requests cannot be closed again.")
        pr.state = PRState.CLOSED

    def reopen(self, pr_number: int) -> None:
        pr = self._pr(pr_number)
        if pr.state != PRState.CLOSED:
            raise ValueError("Only closed pull requests can be reopened.")
        pr.state = PRState.OPEN
        pr.reopened_count += 1

    def merge(
        self,
        pr_number: int,
        actor: str,
        strategy: MergeStrategy = MergeStrategy.SQUASH,
        administrator: bool = False,
    ) -> Commit:
        pr = self._pr(pr_number)
        target = self._branch(pr.target_branch)

        eligible, reasons = self.merge_eligibility(pr_number, actor, administrator)
        if not eligible:
            raise PermissionError("Merge blocked: " + "; ".join(reasons))

        if strategy == MergeStrategy.REBASE:
            if self.protection.get(pr.target_branch, BranchProtection()).require_linear_history:
                new_commit = Commit(
                    sha=self.new_sha(),
                    message=f"Rebased PR #{pr.number}: {pr.title}",
                    author=actor,
                    timestamp=self.now(),
                )
            else:
                new_commit = Commit(
                    sha=self.new_sha(),
                    message=f"Rebased PR #{pr.number}: {pr.title}",
                    author=actor,
                    timestamp=self.now(),
                )
        elif strategy == MergeStrategy.SQUASH:
            new_commit = Commit(
                sha=self.new_sha(),
                message=f"Squash merge PR #{pr.number}: {pr.title}",
                author=actor,
                timestamp=self.now(),
            )
        else:
            new_commit = Commit(
                sha=self.new_sha(),
                message=f"Merge PR #{pr.number}: {pr.title}",
                author=actor,
                timestamp=self.now(),
            )

        target.commits.append(new_commit)
        pr.merge_strategy = strategy
        pr.state = PRState.MERGED
        return new_commit

    def merge_eligibility(
        self,
        pr_number: int,
        actor: str,
        administrator: bool = False,
    ) -> Tuple[bool, List[str]]:
        pr = self._pr(pr_number)
        target = self._branch(pr.target_branch)
        policy = self.protection.get(pr.target_branch)

        reasons: List[str] = []

        if pr.state != PRState.OPEN:
            reasons.append(f"PR state is {pr.state.value}")

        if not pr.commits:
            reasons.append("PR has no commits")

        if policy is None:
            return len(reasons) == 0, reasons

        if actor == pr.author:
            reasons.append("author cannot merge its own PR under this governance policy")

        if not administrator or not policy.allow_administrator_bypass:
            latest_sha = pr.head_sha

            approvals = {
                review.reviewer
                for review in pr.reviews
                if (
                    review.state == ReviewState.APPROVED
                    and not review.dismissed
                    and review.commit_sha == latest_sha
                )
            }

            if len(approvals) < policy.required_reviews:
                reasons.append(
                    f"requires {policy.required_reviews} current approval(s), "
                    f"found {len(approvals)}"
                )

            for check_name in policy.required_status_checks:
                check = pr.checks.get(check_name)
                if check is None or check.state != CheckState.PASSING:
                    reasons.append(f"required status check is not passing: {check_name}")
                elif check.commit_sha != latest_sha:
                    reasons.append(f"status check is stale: {check_name}")

            unresolved = [
                comment
                for review in pr.reviews
                for comment in review.comments
                if not comment.resolved
            ]
            if policy.require_conversation_resolution and unresolved:
                reasons.append(f"{len(unresolved)} review conversation(s) unresolved")

        return len(reasons) == 0, reasons

    def create_task(
        self,
        title: str,
        description: str,
        priority: str = "medium",
    ) -> Task:
        if priority not in {"low", "medium", "high", "critical"}:
            raise ValueError("Invalid priority.")
        if not title.strip():
            raise ValueError("Task title cannot be empty.")

        task = Task(
            id=uuid.uuid4().hex[:8],
            title=title.strip(),
            description=description.strip(),
            state=TaskState.TODO,
            priority=priority,
        )
        self.tasks[task.id] = task
        return task

    def link_task_to_pr(self, task_id: str, pr_number: int) -> None:
        if task_id not in self.tasks:
            raise KeyError("Task not found.")
        self._pr(pr_number)
        self.tasks[task_id].linked_pr = pr_number

    def update_task(self, task_id: str, state: TaskState) -> None:
        if task_id not in self.tasks:
            raise KeyError("Task not found.")
        self.tasks[task_id].state = state

    def dashboard(self) -> dict:
        return {
            "repository": self.name,
            "branches": {
                name: {
                    "protected": branch.protected,
                    "commits": len(branch.commits),
                    "head": branch.commits[-1].sha if branch.commits else None,
                }
                for name, branch in self.branches.items()
            },
            "pull_requests": [
                {
                    "number": pr.number,
                    "title": pr.title,
                    "state": pr.state.value,
                    "source": pr.source_branch,
                    "target": pr.target_branch,
                    "reviews": len(pr.reviews),
                    "checks": {
                        name: check.state.value
                        for name, check in pr.checks.items()
                    },
                    "eligible": self.merge_eligibility(pr.number, "release-manager")[0],
                }
                for pr in self.pull_requests.values()
            ],
            "tasks": [
                {
                    "id": task.id,
                    "title": task.title,
                    "state": task.state.value,
                    "priority": task.priority,
                    "linked_pr": task.linked_pr,
                }
                for task in self.tasks.values()
            ],
        }

    def _branch(self, name: str) -> Branch:
        if name not in self.branches:
            raise KeyError(f"Unknown branch: {name}")
        return self.branches[name]

    def _pr(self, number: int) -> PullRequest:
        if number not in self.pull_requests:
            raise KeyError(f"Unknown pull request: {number}")
        return self.pull_requests[number]


def run_demo() -> None:
    repo = Repository("engineering-task-manager", "acme")

    repo.create_branch("main")
    initial = repo.commit("main", "platform-admin", "Initialize application")
    repo.protect_branch(
        "main",
        BranchProtection(
            required_reviews=2,
            required_status_checks={"unit-tests", "security-scan"},
            restrict_direct_push=True,
            restrict_force_push=True,
            restrict_deletion=True,
            require_conversation_resolution=True,
            require_linear_history=True,
            allow_administrator_bypass=False,
        ),
    )

    repo.create_branch("feature/task-board", "main")
    repo.commit("feature/task-board", "developer", "Add task board domain model")
    repo.commit("feature/task-board", "developer", "Add task filtering and persistence adapter")

    task = repo.create_task(
        "Implement protected task workflow",
        "Require review and passing checks before production merge.",
        "high",
    )

    pr = repo.create_pull_request(
        "Implement protected task workflow",
        "feature/task-board",
        "main",
        "developer",
        draft=True,
    )
    repo.link_task_to_pr(task.id, pr.number)
    repo.mark_ready(pr.number)

    repo.request_review(pr.number, "reviewer-one")
    repo.request_review(pr.number, "reviewer-two")

    review_one = repo.submit_review(
        pr.number,
        "reviewer-one",
        ReviewState.CHANGES_REQUESTED,
        "The task state transition needs an explicit validation rule.",
    )
    comment = repo.add_comment(
        pr.number,
        review_one.id,
        "Please reject invalid state transitions.",
    )

    blocked, reasons = repo.merge_eligibility(pr.number, "release-manager")
    assert not blocked
    assert any("approval" in reason for reason in reasons)

    repo.resolve_comment(pr.number, comment.id)

    repo.submit_review(
        pr.number,
        "reviewer-one",
        ReviewState.APPROVED,
        "State transition validation is now acceptable.",
    )
    repo.submit_review(
        pr.number,
        "reviewer-two",
        ReviewState.APPROVED,
        "Reviewed implementation and tests.",
    )

    repo.set_status(pr.number, "unit-tests", CheckState.PASSING)
    repo.set_status(pr.number, "security-scan", CheckState.PASSING)

    eligible, reasons = repo.merge_eligibility(pr.number, "release-manager")
    assert eligible, reasons

    merged_commit = repo.merge(
        pr.number,
        "release-manager",
        MergeStrategy.SQUASH,
    )
    repo.update_task(task.id, TaskState.DONE)

    # Demonstrate stale-approval behavior on a second PR.
    repo.create_branch("feature/stale-approval", "main")
    repo.commit("feature/stale-approval", "developer-two", "Add notification preferences")
    pr2 = repo.create_pull_request(
        "Add notification preferences",
        "feature/stale-approval",
        "main",
        "developer-two",
    )
    repo.request_review(pr2.number, "reviewer-one")
    repo.request_review(pr2.number, "reviewer-two")
    repo.submit_review(pr2.number, "reviewer-one", ReviewState.APPROVED, "Approved.")
    repo.submit_review(pr2.number, "reviewer-two", ReviewState.APPROVED, "Approved.")
    repo.set_status(pr2.number, "unit-tests", CheckState.PASSING)
    repo.set_status(pr2.number, "security-scan", CheckState.PASSING)

    repo.commit(
        "feature/stale-approval",
        "developer-two",
        "Change notification validation",
    )
    pr2.commits = list(repo.branches["feature/stale-approval"].commits)

    stale_ok, stale_reasons = repo.merge_eligibility(
        pr2.number,
        "release-manager",
    )
    assert not stale_ok
    assert any("approval" in reason for reason in stale_reasons)

    print(json.dumps(repo.dashboard(), indent=2))
    print(f"Merged commit: {merged_commit.sha}")
    print(f"Initial main commit: {initial.sha}")


if __name__ == "__main__":
    run_demo()
