#!/usr/bin/env python3

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Iterable
import hashlib
import json
import re
import tempfile


class GitError(Exception):
    """Base exception for repository workflow errors."""


class ValidationError(GitError):
    pass


class RepositoryStateError(GitError):
    pass


class BranchNotFoundError(GitError):
    pass


class CommitNotFoundError(GitError):
    pass


class ObjectType(str, Enum):
    BLOB = "blob"
    TREE = "tree"
    COMMIT = "commit"


@dataclass(frozen=True)
class GitObject:
    object_type: ObjectType
    content: bytes

    @property
    def object_id(self) -> str:
        header = f"{self.object_type.value} {len(self.content)}\0".encode()
        return hashlib.sha1(header + self.content).hexdigest()


@dataclass
class Commit:
    object_id: str
    message: str
    parents: tuple[str, ...]
    tree: dict[str, str]
    author: str


@dataclass
class Branch:
    name: str
    commit_id: str


@dataclass
class Repository:
    working_tree: dict[str, str] = field(default_factory=dict)
    index: dict[str, str] = field(default_factory=dict)
    objects: dict[str, GitObject] = field(default_factory=dict)
    commits: dict[str, Commit] = field(default_factory=dict)
    branches: dict[str, Branch] = field(default_factory=dict)
    head_branch: str = "main"
    head_detached: bool = False
    head_commit_id: str | None = None

    def __post_init__(self) -> None:
        if not self.branches:
            self.branches["main"] = Branch("main", "")
        self.validate_state()

    @property
    def head(self) -> str | None:
        if self.head_detached:
            return self.head_commit_id
        branch = self.branches.get(self.head_branch)
        return branch.commit_id if branch else None

    def validate_state(self) -> None:
        if self.head_branch not in self.branches and not self.head_detached:
            raise RepositoryStateError("HEAD references a missing branch.")
        if self.head is not None and self.head not in self.commits:
            raise RepositoryStateError("HEAD references an unknown commit.")
        for name, branch in self.branches.items():
            if not re.fullmatch(r"[A-Za-z0-9._/-]+", name):
                raise ValidationError(f"Invalid branch name: {name}")
            if branch.commit_id and branch.commit_id not in self.commits:
                raise RepositoryStateError(
                    f"Branch {name} references an unknown commit."
                )

    def add_object(self, obj: GitObject) -> str:
        object_id = obj.object_id
        self.objects.setdefault(object_id, obj)
        return object_id

    def add(self, paths: Iterable[str]) -> None:
        for path in paths:
            self._validate_path(path)
            if path not in self.working_tree:
                raise FileNotFoundError(f"Working-tree file does not exist: {path}")
            self.index[path] = self.working_tree[path]
        self.validate_state()

    def add_all(self) -> None:
        self.index = dict(self.working_tree)
        self.validate_state()

    def restore_staged(self, path: str) -> None:
        if path not in self.index:
            raise RepositoryStateError(f"{path} is not staged.")
        if self.head is None:
            del self.index[path]
            return
        previous = self.commits[self.head].tree.get(path)
        if previous is None:
            del self.index[path]
        else:
            self.index[path] = previous

    def write_file(self, path: str, content: str) -> None:
        self._validate_path(path)
        self.working_tree[path] = content

    def delete_file(self, path: str) -> None:
        self._validate_path(path)
        if path not in self.working_tree:
            raise FileNotFoundError(path)
        del self.working_tree[path]

    def status(self) -> dict[str, list[str]]:
        committed = self.commits[self.head].tree if self.head else {}

        staged = []
        modified = []
        untracked = []

        for path in sorted(set(committed) | set(self.index)):
            if committed.get(path) != self.index.get(path):
                staged.append(path)

        for path in sorted(set(self.index) | set(self.working_tree)):
            if self.index.get(path) != self.working_tree.get(path):
                if path in self.working_tree:
                    modified.append(path)
                elif path in self.index:
                    modified.append(path)

        for path in sorted(set(self.working_tree) - set(committed) - set(self.index)):
            untracked.append(path)

        return {
            "staged": staged,
            "modified": modified,
            "untracked": untracked,
        }

    def commit(self, message: str, author: str) -> str:
        message = message.strip()
        author = author.strip()

        if not message:
            raise ValidationError("Commit message cannot be empty.")
        if not author:
            raise ValidationError("Commit author cannot be empty.")
        if not self.index:
            raise RepositoryStateError("Nothing is staged for commit.")

        tree = dict(self.index)

        # Store file contents as Git-like blob objects.
        for path, content in tree.items():
            self.add_object(GitObject(ObjectType.BLOB, content.encode("utf-8")))

        payload = {
            "author": author,
            "message": message,
            "parents": [self.head] if self.head else [],
            "tree": tree,
        }
        encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
        commit_object = GitObject(ObjectType.COMMIT, encoded)
        commit_id = self.add_object(commit_object)

        self.commits[commit_id] = Commit(
            object_id=commit_id,
            message=message,
            parents=tuple(payload["parents"]),
            tree=tree,
            author=author,
        )

        if self.head_detached:
            self.head_commit_id = commit_id
        else:
            self.branches[self.head_branch].commit_id = commit_id

        self.index = dict(tree)
        self.validate_state()
        return commit_id

    def create_branch(self, name: str, start_point: str | None = None) -> None:
        self._validate_branch_name(name)
        if name in self.branches:
            raise ValidationError(f"Branch already exists: {name}")

        commit_id = start_point if start_point is not None else self.head
        if commit_id and commit_id not in self.commits:
            raise CommitNotFoundError(commit_id)

        self.branches[name] = Branch(name, commit_id or "")
        self.validate_state()

    def checkout(self, target: str) -> None:
        if target in self.branches:
            commit_id = self.branches[target].commit_id
            if self._has_uncommitted_changes():
                raise RepositoryStateError(
                    "Cannot switch branches with uncommitted changes."
                )
            self.head_branch = target
            self.head_detached = False
            self.head_commit_id = None
            self._checkout_tree(commit_id)
            return

        if target not in self.commits:
            raise CommitNotFoundError(target)

        if self._has_uncommitted_changes():
            raise RepositoryStateError(
                "Cannot detach HEAD with uncommitted changes."
            )

        self.head_detached = True
        self.head_commit_id = target
        self._checkout_tree(target)

    def merge(self, source: str, message: str | None = None) -> str:
        if self.head_detached:
            raise RepositoryStateError("Cannot merge while HEAD is detached.")
        if source not in self.branches:
            raise BranchNotFoundError(source)
        if self._has_uncommitted_changes():
            raise RepositoryStateError("Commit or stash changes before merging.")

        target_id = self.head
        source_id = self.branches[source].commit_id

        if not source_id:
            raise RepositoryStateError("Source branch has no commits.")
        if not target_id:
            self.branches[self.head_branch].commit_id = source_id
            self._checkout_tree(source_id)
            return source_id
        if target_id == source_id:
            return target_id

        if self.is_ancestor(target_id, source_id):
            self.branches[self.head_branch].commit_id = source_id
            self._checkout_tree(source_id)
            return source_id

        if self.is_ancestor(source_id, target_id):
            return target_id

        target_tree = self.commits[target_id].tree
        source_tree = self.commits[source_id].tree
        base_id = self.find_merge_base(target_id, source_id)

        if base_id is None:
            raise RepositoryStateError("No merge base found.")

        base_tree = self.commits[base_id].tree
        merged = {}
        conflicts = []

        for path in sorted(set(base_tree) | set(target_tree) | set(source_tree)):
            base = base_tree.get(path)
            ours = target_tree.get(path)
            theirs = source_tree.get(path)

            if ours == theirs:
                if ours is not None:
                    merged[path] = ours
            elif ours == base:
                if theirs is not None:
                    merged[path] = theirs
            elif theirs == base:
                if ours is not None:
                    merged[path] = ours
            else:
                conflicts.append(path)

        if conflicts:
            raise RepositoryStateError(
                "Merge conflict in: " + ", ".join(conflicts)
            )

        self.index = merged
        self.working_tree = dict(merged)
        return self.commit(
            message or f"Merge branch '{source}' into {self.head_branch}",
            "merge-bot",
        )

    def is_ancestor(self, ancestor: str, descendant: str) -> bool:
        stack = [descendant]
        seen = set()

        while stack:
            current = stack.pop()
            if current in seen:
                continue
            seen.add(current)
            if current == ancestor:
                return True
            stack.extend(self.commits[current].parents)

        return False

    def find_merge_base(self, left: str, right: str) -> str | None:
        left_ancestors = self._ancestor_distances(left)
        right_ancestors = self._ancestor_distances(right)
        common = set(left_ancestors) & set(right_ancestors)

        if not common:
            return None

        return min(
            common,
            key=lambda commit_id: (
                left_ancestors[commit_id] + right_ancestors[commit_id],
                -len(self.commits[commit_id].parents),
            ),
        )

    def log(self, start: str | None = None) -> list[Commit]:
        current = start or self.head
        result = []

        while current:
            commit = self.commits[current]
            result.append(commit)
            current = commit.parents[0] if commit.parents else None

        return result

    def diff_head(self) -> dict[str, str]:
        committed = self.commits[self.head].tree if self.head else {}
        paths = sorted(set(committed) | set(self.working_tree))
        diff = {}

        for path in paths:
            old = committed.get(path)
            new = self.working_tree.get(path)
            if old != new:
                diff[path] = f"{old!r} -> {new!r}"

        return diff

    def save_snapshot(self, directory: Path) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "working-tree.json").write_text(
            json.dumps(self.working_tree, indent=2), encoding="utf-8"
        )
        (directory / "index.json").write_text(
            json.dumps(self.index, indent=2), encoding="utf-8"
        )
        (directory / "refs.json").write_text(
            json.dumps(
                {
                    "head_branch": self.head_branch,
                    "head_detached": self.head_detached,
                    "head_commit_id": self.head_commit_id,
                    "branches": {
                        name: branch.commit_id
                        for name, branch in self.branches.items()
                    },
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    def _checkout_tree(self, commit_id: str | None) -> None:
        tree = self.commits[commit_id].tree if commit_id else {}
        self.working_tree = dict(tree)
        self.index = dict(tree)

    def _has_uncommitted_changes(self) -> bool:
        status = self.status()
        return any(status.values())

    @staticmethod
    def _validate_path(path: str) -> None:
        if not path or path.startswith("/") or ".." in Path(path).parts:
            raise ValidationError(f"Unsafe repository path: {path}")

    @staticmethod
    def _validate_branch_name(name: str) -> None:
        if not name or not re.fullmatch(r"[A-Za-z0-9._/-]+", name):
            raise ValidationError(f"Invalid branch name: {name}")
        if name.startswith("/") or name.endswith("/") or ".." in name:
            raise ValidationError(f"Invalid branch name: {name}")

    def _ancestor_distances(self, start: str) -> dict[str, int]:
        distances = {start: 0}
        queue = [start]

        while queue:
            current = queue.pop(0)
            distance = distances[current]

            for parent in self.commits[current].parents:
                if parent not in distances:
                    distances[parent] = distance + 1
                    queue.append(parent)

        return distances


def print_status(repo: Repository) -> None:
    print("\nSTATUS")
    status = repo.status()
    for category, paths in status.items():
        print(f"  {category:10}: {paths or '-'}")


def run_demo() -> None:
    repo = Repository()

    repo.write_file("README.md", "# Repository\n")
    repo.write_file("app.py", 'print("version 1")\n')
    repo.add_all()
    first = repo.commit("Initialize repository", "developer@example.com")

    repo.write_file("app.py", 'print("version 2")\n')
    repo.write_file("notes.txt", "Local work not yet staged.\n")
    print_status(repo)

    repo.add(["app.py"])
    print_status(repo)

    second = repo.commit("Update application", "developer@example.com")

    repo.create_branch("feature/audit")
    repo.checkout("feature/audit")
    repo.write_file("audit.log", "audit enabled\n")
    repo.add(["audit.log"])
    feature_commit = repo.commit(
        "Add audit artifact",
        "security@example.com",
    )

    repo.checkout("main")
    repo.write_file("README.md", "# Repository\nGit fundamentals\n")
    repo.add(["README.md"])
    main_commit = repo.commit("Document repository workflow", "developer@example.com")

    merged = repo.merge("feature/audit")
    print("\nCOMMITS")
    for commit in repo.log():
        print(
            f"{commit.object_id[:10]} "
            f"{commit.author} "
            f"{commit.message}"
        )

    print("\nBRANCHES")
    for name, branch in repo.branches.items():
        print(f"{name:15} {branch.commit_id[:10] if branch.commit_id else '(empty)'}")

    print("\nGRAPH RELATIONSHIPS")
    print(f"initial: {first[:10]}")
    print(f"main update: {second[:10]}")
    print(f"feature: {feature_commit[:10]}")
    print(f"main side change: {main_commit[:10]}")
    print(f"merge: {merged[:10]}")

    print("\nHEAD")
    print(repo.head[:10] if repo.head else "(empty)")

    with tempfile.TemporaryDirectory() as temp:
        snapshot = Path(temp) / "repo-state"
        repo.save_snapshot(snapshot)
        print(f"\nSnapshot written to {snapshot}")

    # Detached HEAD is useful for inspecting an exact historical state.
    repo.checkout(second)
    assert repo.head == second
    assert repo.head_detached

    repo.checkout("main")
    assert repo.head == repo.branches["main"].commit_id
    assert not repo.head_detached

    # Security-oriented path validation must reject traversal attempts.
    try:
        repo.write_file("../outside.txt", "blocked")
    except ValidationError:
        print("\nPath traversal correctly rejected.")

    print("\nRepository state validated successfully.")


if __name__ == "__main__":
    run_demo()
