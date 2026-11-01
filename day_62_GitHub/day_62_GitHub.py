from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Set, Tuple


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


class CheckState(Enum):
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"


class MergeStrategy(Enum):
    MERGE = "merge"
    SQUASH = "squash"
    REBASE = "rebase"


@dataclass(frozen=True)
class Commit:
    sha: str
    message: str
    author: str


@dataclass
class Branch:
    name: str
    protected: bool = False
    commits: List[Commit] = field(default_factory=list)

    @property
    def head(self) -> str | None:
        return self.commits[-1].sha if self.commits else None

    def add_commit(self, commit: Commit) -> None:
        if any(existing.sha == commit.sha for existing in self.commits):
            raise ValueError(f"Commit {commit.sha} already exists")
        self.commits.append(commit)


@dataclass
class ReviewComment:
    reviewer: str
    file_path: str
    line: int
    body: str
    resolved: bool = False


@dataclass
class Review:
    reviewer: str
    state: ReviewState
    comments: List[ReviewComment] = field(default_factory=list)


@dataclass
class StatusCheck:
    name: str
    state: CheckState


@dataclass
class BranchProtection:
    required_reviews: int = 1
    required_checks: Set[str] = field(default_factory=set)
    dismiss_stale_approvals: bool = True
    require_conversation_resolution: bool = True
    allow_force_push: bool = False
    allow_direct_push: bool = False
    require_linear_history: bool = False


@dataclass
class PullRequest:
    number: int
    title: str
    source_branch: str
    target_branch: str
    author: str
    state: PullRequestState = PullRequestState.OPEN
    draft: bool = False
    commits: List[Commit] = field(default_factory=list)
    reviews: List[Review] = field(default_factory=list)
    checks: List[StatusCheck] = field(default_factory=list)
    comments: List[ReviewComment] = field(default_factory=list)
    base_head_at_creation: str | None = None

    def add_commit(self, commit: Commit) -> None:
        if self.state != PullRequestState.OPEN:
            raise ValueError("Commits cannot be added to a non-open pull request")
        self.commits.append(commit)

    def add_review(self, review: Review) -> None:
        if self.state != PullRequestState.OPEN:
            raise ValueError("Reviews cannot be added to a closed or merged pull request")
        self.reviews.append(review)

    def add_check(self, check: StatusCheck) -> None:
        self.checks = [c for c in self.checks if c.name != check.name]
        self.checks.append(check)

    def unresolved_comments(self) -> List[ReviewComment]:
        return [c for c in self.comments if not c.resolved]


@dataclass
class Issue:
    number: int
    title: str
    author: str
    labels: Set[str] = field(default_factory=set)
    closed: bool = False


@dataclass
class Repository:
    name: str
    default_branch: str = "main"
    branches: Dict[str, Branch] = field(default_factory=dict)
    pull_requests: Dict[int, PullRequest] = field(default_factory=dict)
    issues: Dict[int, Issue] = field(default_factory=dict)
    protection: Dict[str, BranchProtection] = field(default_factory=dict)
    next_pr_number: int = 1
    next_issue_number: int = 1

    def create_branch(self, name: str, from_branch: str | None = None) -> Branch:
        if name in self.branches:
            raise ValueError(f"Branch {name} already exists")

        branch = Branch(name)
        if from_branch:
            if from_branch not in self.branches:
                raise ValueError(f"Base branch {from_branch} does not exist")
            branch.commits = list(self.branches[from_branch].commits)

        self.branches[name] = branch
        return branch

    def configure_protection(self, branch_name: str, policy: BranchProtection) -> None:
        if branch_name not in self.branches:
            raise ValueError(f"Unknown branch: {branch_name}")
        self.branches[branch_name].protected = True
        self.protection[branch_name] = policy

    def create_issue(self, title: str, author: str, labels: Set[str]) -> Issue:
        issue = Issue(self.next_issue_number, title, author, labels)
        self.issues[issue.number] = issue
        self.next_issue_number += 1
        return issue

    def create_pull_request(
        self,
        title: str,
        source: str,
        target: str,
        author: str,
        draft: bool = False,
    ) -> PullRequest:
        if source not in self.branches or target not in self.branches:
            raise ValueError("Both source and target branches must exist")
        if source == target:
            raise ValueError("Source and target branches must differ")

        pr = PullRequest(
            number=self.next_pr_number,
            title=title,
            source_branch=source,
            target_branch=target,
            author=author,
            state=PullRequestState.DRAFT if draft else PullRequestState.OPEN,
            draft=draft,
            commits=list(self.branches[source].commits),
            base_head_at_creation=self.branches[target].head,
        )
        self.pull_requests[pr.number] = pr
        self.next_pr_number += 1
        return pr

    def publish_draft(self, pr_number: int) -> None:
        pr = self.pull_requests[pr_number]
        if not pr.draft:
            return
        pr.draft = False
        pr.state = PullRequestState.OPEN

    def synchronize_pull_request(self, pr_number: int) -> None:
        pr = self.pull_requests[pr_number]
        target = self.branches[pr.target_branch]
        source = self.branches[pr.source_branch]

        if pr.base_head_at_creation != target.head:
            pr.base_head_at_creation = target.head
            pr.commits = list(source.commits)

            policy = self.protection.get(pr.target_branch)
            if policy and policy.dismiss_stale_approvals:
                pr.reviews = [
                    review
                    for review in pr.reviews
                    if review.state not in {
                        ReviewState.APPROVED,
                        ReviewState.CHANGES_REQUESTED,
                    }
                ]

    def _approved_reviewers(self, pr: PullRequest) -> Set[str]:
        return {
            review.reviewer
            for review in pr.reviews
            if review.state == ReviewState.APPROVED
        }

    def merge_eligibility(self, pr_number: int) -> Tuple[bool, List[str]]:
        pr = self.pull_requests[pr_number]
        reasons: List[str] = []

        if pr.state != PullRequestState.OPEN:
            reasons.append("Pull request is not open")

        if pr.draft:
            reasons.append("Pull request is still a draft")

        if not pr.commits:
            reasons.append("Pull request contains no commits")

        policy = self.protection.get(pr.target_branch)
        if policy:
            approvals = self._approved_reviewers(pr)

            if len(approvals) < policy.required_reviews:
                reasons.append(
                    f"Requires {policy.required_reviews} eligible approval(s); "
                    f"currently has {len(approvals)}"
                )

            for required_check in policy.required_checks:
                matching = next(
                    (c for c in pr.checks if c.name == required_check),
                    None,
                )
                if matching is None or matching.state != CheckState.PASSED:
                    reasons.append(f"Required check '{required_check}' has not passed")

            if policy.require_conversation_resolution and pr.unresolved_comments():
                reasons.append("Unresolved review conversations remain")

            for review in pr.reviews:
                if review.state == ReviewState.CHANGES_REQUESTED:
                    reasons.append(f"Reviewer {review.reviewer} requested changes")

        return not reasons, reasons

    def merge(
        self,
        pr_number: int,
        strategy: MergeStrategy = MergeStrategy.SQUASH,
    ) -> str:
        eligible, reasons = self.merge_eligibility(pr_number)
        if not eligible:
            raise RuntimeError("Merge blocked: " + "; ".join(reasons))

        pr = self.pull_requests[pr_number]
        target = self.branches[pr.target_branch]

        if strategy == MergeStrategy.SQUASH:
            source_shas = [commit.sha for commit in pr.commits]
            sha = f"squash-{pr.number}-{len(source_shas)}"
            target.add_commit(
                Commit(
                    sha=sha,
                    message=f"Squash merge PR #{pr.number}: {pr.title}",
                    author=pr.author,
                )
            )
        elif strategy == MergeStrategy.MERGE:
            target.add_commit(
                Commit(
                    sha=f"merge-{pr.number}",
                    message=f"Merge PR #{pr.number}: {pr.title}",
                    author=pr.author,
                )
            )
        elif strategy == MergeStrategy.REBASE:
            for commit in pr.commits:
                target.add_commit(
                    Commit(
                        sha=f"rebased-{commit.sha}",
                        message=commit.message,
                        author=commit.author,
                    )
                )

        pr.state = PullRequestState.MERGED
        return target.head or ""


def clone_repository(remote: Repository) -> Repository:
    clone = Repository(name=remote.name, default_branch=remote.default_branch)
    for name, branch in remote.branches.items():
        clone.branches[name] = Branch(
            name=name,
            protected=branch.protected,
            commits=list(branch.commits),
        )
    clone.protection = {
        name: BranchProtection(
            required_reviews=policy.required_reviews,
            required_checks=set(policy.required_checks),
            dismiss_stale_approvals=policy.dismiss_stale_approvals,
            require_conversation_resolution=policy.require_conversation_resolution,
            allow_force_push=policy.allow_force_push,
            allow_direct_push=policy.allow_direct_push,
            require_linear_history=policy.require_linear_history,
        )
        for name, policy in remote.protection.items()
    }
    return clone


def push_branch(local: Repository, remote: Repository, branch_name: str) -> None:
    if branch_name not in local.branches:
        raise ValueError("Local branch does not exist")
    if branch_name not in remote.branches:
        remote.branches[branch_name] = Branch(branch_name)

    remote_branch = remote.branches[branch_name]
    if remote_branch.protected:
        policy = remote.protection[branch_name]
        if not policy.allow_direct_push:
            raise PermissionError(
                f"Direct push to protected branch '{branch_name}' is blocked"
            )

    remote.branches[branch_name].commits = list(local.branches[branch_name].commits)


def pull_branch(local: Repository, remote: Repository, branch_name: str) -> None:
    if branch_name not in remote.branches:
        raise ValueError("Remote branch does not exist")
    local.branches[branch_name] = Branch(
        name=branch_name,
        protected=remote.branches[branch_name].protected,
        commits=list(remote.branches[branch_name].commits),
    )


def print_repository_status(repo: Repository) -> None:
    print(f"\nRepository: {repo.name}")
    for branch in repo.branches.values():
        print(
            f"  {branch.name}: head={branch.head}, "
            f"protected={branch.protected}, commits={len(branch.commits)}"
        )

    for pr in repo.pull_requests.values():
        eligible, reasons = repo.merge_eligibility(pr.number)
        print(
            f"  PR #{pr.number} [{pr.state.value}] "
            f"{pr.title}: mergeable={eligible}"
        )
        if reasons:
            for reason in reasons:
                print(f"    - {reason}")


def main() -> None:
    remote = Repository("secure-service")
    main_branch = remote.create_branch("main")
    main_branch.add_commit(
        Commit("a1", "Initial service implementation", "alice")
    )

    remote.configure_protection(
        "main",
        BranchProtection(
            required_reviews=2,
            required_checks={"unit-tests", "security-scan"},
            dismiss_stale_approvals=True,
            require_conversation_resolution=True,
            allow_direct_push=False,
            allow_force_push=False,
            require_linear_history=True,
        ),
    )

    local = clone_repository(remote)
    local.create_branch("feature/remote-workflow", "main")
    local.branches["feature/remote-workflow"].add_commit(
        Commit("b1", "Document remote repository workflow", "bob")
    )
    local.branches["feature/remote-workflow"].add_commit(
        Commit("b2", "Add repository operations validation", "bob")
    )

    pr = remote.create_pull_request(
        title="Document remote repository workflow",
        source="feature/remote-workflow",
        target="main",
        author="bob",
    )

    for commit in local.branches["feature/remote-workflow"].commits:
        if commit.sha != main_branch.head:
            pr.add_commit(commit)

    pr.comments.append(
        ReviewComment(
            reviewer="carol",
            file_path="README.md",
            line=18,
            body="Clarify the difference between clone and pull.",
        )
    )

    pr.add_review(
        Review(
            reviewer="carol",
            state=ReviewState.APPROVED,
        )
    )
    pr.add_review(
        Review(
            reviewer="david",
            state=ReviewState.APPROVED,
        )
    )

    pr.add_check(StatusCheck("unit-tests", CheckState.PASSED))
    pr.add_check(StatusCheck("security-scan", CheckState.PASSED))

    eligible, reasons = remote.merge_eligibility(pr.number)
    print(f"Before resolving conversation: eligible={eligible}")
    for reason in reasons:
        print(f"  {reason}")

    for comment in pr.comments:
        comment.resolved = True

    eligible, reasons = remote.merge_eligibility(pr.number)
    print(f"After resolving conversation: eligible={eligible}")

    if eligible:
        remote.merge(pr.number, MergeStrategy.SQUASH)

    issue = remote.create_issue(
        "Document remote clone and synchronization behavior",
        "alice",
        {"documentation", "git"},
    )
    print(f"Created issue #{issue.number}: {issue.title}")

    print_repository_status(remote)

    # Security and operational assertions.
    assert remote.branches["main"].protected
    assert remote.pull_requests[pr.number].state == PullRequestState.MERGED
    assert remote.branches["main"].head is not None

    # A protected branch rejects a direct push.
    local.branches["main"].add_commit(
        Commit("unauthorized", "Attempt direct protected-branch push", "eve")
    )
    try:
        push_branch(local, remote, "main")
    except PermissionError as exc:
        print(f"Expected security control: {exc}")

    # Pull refreshes a local branch from the remote repository.
    pull_branch(local, remote, "main")
    assert local.branches["main"].head == remote.branches["main"].head

    print("\nRemote clone/push/pull workflow completed successfully.")


if __name__ == "__main__":
    main()
