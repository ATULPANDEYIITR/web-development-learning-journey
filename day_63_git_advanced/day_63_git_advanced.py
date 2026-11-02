#!/usr/bin/env python3

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple
import copy
import hashlib
import time


class GitError(Exception):
    """Raised when a simulated Git operation violates repository state."""


class CommitType(Enum):
    NORMAL = "normal"
    MERGE = "merge"
    REVERT = "revert"


@dataclass
class Commit:
    hash: str
    message: str
    parents: Tuple[str, ...]
    tree: Dict[str, str]
    kind: CommitType = CommitType.NORMAL
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class StashEntry:
    message: str
    tree: Dict[str, str]
    base_commit: str


class GitRepository:
    """
    In-memory Git model covering:
    merge, rebase, cherry-pick, stash, reset, revert, and tags.

    A commit stores a complete logical tree rather than filesystem deltas.
    This keeps the example deterministic while preserving the important
    ancestry and state-transition behavior of Git workflows.
    """

    def __init__(self) -> None:
        self.commits: Dict[str, Commit] = {}
        self.branches: Dict[str, str] = {}
        self.tags: Dict[str, str] = {}
        self.stashes: List[StashEntry] = []
        self.working_tree: Dict[str, str] = {}
        self.head_branch = "main"
        self._counter = 0

        initial = self._commit(
            "Initial application",
            {},
            parents=(),
        )
        self.branches["main"] = initial.hash
        self.working_tree = copy.deepcopy(initial.tree)

    def _new_hash(self, message: str, parents: Tuple[str, ...]) -> str:
        self._counter += 1
        payload = f"{self._counter}|{message}|{parents}|{time.time_ns()}"
        return hashlib.sha1(payload.encode()).hexdigest()[:10]

    def _commit(
        self,
        message: str,
        tree: Dict[str, str],
        parents: Tuple[str, ...],
        kind: CommitType = CommitType.NORMAL,
        metadata: Optional[Dict[str, str]] = None,
    ) -> Commit:
        commit_hash = self._new_hash(message, parents)
        commit = Commit(
            hash=commit_hash,
            message=message,
            parents=parents,
            tree=copy.deepcopy(tree),
            kind=kind,
            metadata=metadata or {},
        )
        self.commits[commit_hash] = commit
        return commit

    @property
    def head(self) -> str:
        return self.branches[self.head_branch]

    def checkout(self, branch: str) -> None:
        if branch not in self.branches:
            raise GitError(f"Unknown branch: {branch}")
        self.head_branch = branch
        self.working_tree = copy.deepcopy(self.commits[self.head].tree)

    def create_branch(self, branch: str, start: Optional[str] = None) -> None:
        if branch in self.branches:
            raise GitError(f"Branch already exists: {branch}")
        start_hash = start or self.head
        if start_hash not in self.commits:
            raise GitError("Invalid branch starting commit")
        self.branches[branch] = start_hash

    def write(self, path: str, content: str) -> None:
        if not path or path.startswith("/"):
            raise GitError("Invalid repository-relative path")
        if "\x00" in content:
            raise GitError("NUL bytes are not permitted")
        self.working_tree[path] = content

    def delete(self, path: str) -> None:
        self.working_tree.pop(path, None)

    def status(self) -> Dict[str, str]:
        committed = self.commits[self.head].tree
        paths = set(committed) | set(self.working_tree)
        return {
            path: (
                "modified"
                if path in committed and path in self.working_tree
                and committed[path] != self.working_tree[path]
                else "added"
                if path not in committed and path in self.working_tree
                else "deleted"
            )
            for path in sorted(paths)
            if committed.get(path) != self.working_tree.get(path)
        }

    def commit(self, message: str) -> str:
        if not message.strip():
            raise GitError("Commit message cannot be empty")
        if not self.status():
            raise GitError("Nothing to commit")
        commit = self._commit(message, self.working_tree, (self.head,))
        self.branches[self.head_branch] = commit.hash
        return commit.hash

    def _ancestors(self, commit_hash: str) -> Set[str]:
        seen: Set[str] = set()
        stack = [commit_hash]
        while stack:
            current = stack.pop()
            if current in seen:
                continue
            seen.add(current)
            stack.extend(self.commits[current].parents)
        return seen

    def _first_parent_chain(self, commit_hash: str) -> List[str]:
        result = []
        current = commit_hash
        while current:
            result.append(current)
            parents = self.commits[current].parents
            current = parents[0] if parents else ""
        return result

    def _find_merge_base(self, left: str, right: str) -> str:
        left_ancestors = self._ancestors(left)
        for candidate in self._first_parent_chain(right):
            if candidate in left_ancestors:
                return candidate
        raise GitError("No common ancestor")

    def merge(self, source_branch: str, message: Optional[str] = None) -> str:
        if source_branch not in self.branches:
            raise GitError(f"Unknown branch: {source_branch}")

        source = self.branches[source_branch]
        target = self.head

        if source == target:
            return target

        if target in self._ancestors(source):
            self.branches[self.head_branch] = source
            self.working_tree = copy.deepcopy(self.commits[source].tree)
            return source

        if source in self._ancestors(target):
            return target

        base = self._find_merge_base(target, source)
        base_tree = self.commits[base].tree
        ours = self.commits[target].tree
        theirs = self.commits[source].tree

        merged = copy.deepcopy(ours)
        conflicts = []

        for path in set(base_tree) | set(ours) | set(theirs):
            b = base_tree.get(path)
            o = ours.get(path)
            t = theirs.get(path)

            if o == t:
                if o is None:
                    merged.pop(path, None)
                else:
                    merged[path] = o
            elif o == b:
                if t is None:
                    merged.pop(path, None)
                else:
                    merged[path] = t
            elif t == b:
                continue
            else:
                conflicts.append(path)

        if conflicts:
            raise GitError(
                "Merge conflict in: " + ", ".join(sorted(conflicts))
            )

        commit = self._commit(
            message or f"Merge {source_branch} into {self.head_branch}",
            merged,
            (target, source),
            CommitType.MERGE,
        )
        self.branches[self.head_branch] = commit.hash
        self.working_tree = copy.deepcopy(merged)
        return commit.hash

    def rebase(self, onto_branch: str) -> List[str]:
        if onto_branch not in self.branches:
            raise GitError(f"Unknown branch: {onto_branch}")
        if onto_branch == self.head_branch:
            raise GitError("Cannot rebase a branch onto itself")

        current_tip = self.head
        onto = self.branches[onto_branch]
        base = self._find_merge_base(current_tip, onto)

        chain = []
        current = current_tip
        while current != base:
            chain.append(current)
            parents = self.commits[current].parents
            if not parents:
                break
            current = parents[0]

        chain.reverse()
        new_parent = onto
        new_hashes = []

        for old_hash in chain:
            old = self.commits[old_hash]
            new_commit = self._commit(
                old.message,
                old.tree,
                (new_parent,),
                old.kind,
                {"rebased-from": old.hash},
            )
            new_parent = new_commit.hash
            new_hashes.append(new_parent)

        self.branches[self.head_branch] = new_parent
        self.working_tree = copy.deepcopy(self.commits[new_parent].tree)
        return new_hashes

    def cherry_pick(self, commit_hash: str) -> str:
        if commit_hash not in self.commits:
            raise GitError("Unknown commit")

        source = self.commits[commit_hash]
        if not source.parents:
            raise GitError("Cannot cherry-pick the root commit")

        parent = self.commits[source.parents[0]]
        current = self.commits[self.head].tree
        new_tree = copy.deepcopy(current)

        changes = set(parent.tree) | set(source.tree)
        for path in changes:
            before = parent.tree.get(path)
            after = source.tree.get(path)

            if before == after:
                continue

            current_value = current.get(path)
            if current_value != before:
                raise GitError(f"Cherry-pick conflict in {path}")

            if after is None:
                new_tree.pop(path, None)
            else:
                new_tree[path] = after

        commit = self._commit(
            f"Cherry-pick: {source.message}",
            new_tree,
            (self.head,),
            CommitType.NORMAL,
            {"cherry-picked-from": source.hash},
        )
        self.branches[self.head_branch] = commit.hash
        self.working_tree = copy.deepcopy(new_tree)
        return commit.hash

    def stash_push(self, message: str) -> None:
        changes = self.status()
        if not changes:
            raise GitError("No local changes to stash")

        self.stashes.append(
            StashEntry(
                message=message,
                tree=copy.deepcopy(self.working_tree),
                base_commit=self.head,
            )
        )
        self.working_tree = copy.deepcopy(self.commits[self.head].tree)

    def stash_pop(self) -> None:
        if not self.stashes:
            raise GitError("No stash entries")

        entry = self.stashes[-1]
        committed = self.commits[self.head].tree
        if committed != self.commits[entry.base_commit].tree:
            raise GitError("Stash cannot be applied cleanly to current branch")

        self.working_tree = copy.deepcopy(entry.tree)
        self.stashes.pop()

    def reset(self, target: str, mode: str = "mixed") -> None:
        if target not in self.commits:
            raise GitError("Unknown reset target")
        if mode not in {"soft", "mixed", "hard"}:
            raise GitError("Mode must be soft, mixed, or hard")

        old_tree = copy.deepcopy(self.working_tree)
        self.branches[self.head_branch] = target

        if mode == "hard":
            self.working_tree = copy.deepcopy(self.commits[target].tree)
        elif mode == "mixed":
            self.working_tree = copy.deepcopy(self.commits[target].tree)
        elif mode == "soft":
            self.working_tree = old_tree

    def revert(self, commit_hash: str) -> str:
        if commit_hash not in self.commits:
            raise GitError("Unknown commit")

        target = self.commits[commit_hash]
        if not target.parents:
            raise GitError("Cannot revert the root commit")

        parent = self.commits[target.parents[0]]
        current = self.commits[self.head].tree
        new_tree = copy.deepcopy(current)

        for path in set(parent.tree) | set(target.tree):
            before = parent.tree.get(path)
            after = target.tree.get(path)

            if before == after:
                continue

            if current.get(path) != after:
                raise GitError(
                    f"Revert conflict in {path}: current content differs"
                )

            if before is None:
                new_tree.pop(path, None)
            else:
                new_tree[path] = before

        commit = self._commit(
            f"Revert: {target.message}",
            new_tree,
            (self.head,),
            CommitType.REVERT,
            {"reverts": target.hash},
        )
        self.branches[self.head_branch] = commit.hash
        self.working_tree = copy.deepcopy(new_tree)
        return commit.hash

    def tag(self, name: str, commit_hash: Optional[str] = None) -> None:
        if not name or name.startswith("-") or " " in name:
            raise GitError("Invalid tag name")
        if name in self.tags:
            raise GitError("Tag already exists")
        target = commit_hash or self.head
        if target not in self.commits:
            raise GitError("Tag target does not exist")
        self.tags[name] = target

    def log(self, branch: Optional[str] = None) -> List[str]:
        tip = self.branches[branch or self.head_branch]
        return [
            f"{h} {self.commits[h].message}"
            for h in self._first_parent_chain(tip)
        ]


def demonstration() -> None:
    repo = GitRepository()

    repo.write("app.py", "print('v1')\n")
    first_feature = repo.commit("Add application entry point")

    repo.create_branch("feature/cache")
    repo.checkout("feature/cache")
    repo.write("cache.py", "CACHE_SIZE = 256\n")
    feature_commit = repo.commit("Add cache configuration")

    repo.write("cache.py", "CACHE_SIZE = 512\n")
    repo.commit("Tune cache size")

    repo.checkout("main")
    repo.write("README.md", "# Deployment Guide\n")
    repo.commit("Document deployment")

    # Merge demonstrates a non-linear history.
    repo.merge("feature/cache")

    # Create an isolated maintenance branch and cherry-pick one change.
    repo.create_branch("hotfix", repo.branches["main"])
    repo.checkout("hotfix")
    repo.cherry_pick(first_feature)

    # Stash preserves unfinished work while changing branches.
    repo.write("config.ini", "timeout=30\n")
    repo.stash_push("Temporary production configuration")
    repo.stash_pop()

    # Revert creates a new commit and preserves public history.
    revert_target = repo.head
    repo.revert(revert_target)

    # A tag names an immutable release point.
    repo.tag("v1.0.0")

    print("=== Git Advanced Workflow ===")
    print(f"Current branch: {repo.head_branch}")
    print(f"HEAD: {repo.head}")
    print(f"Tags: {repo.tags}")
    print("Status:", repo.status())
    print("Log:")
    for line in repo.log():
        print(" ", line)

    assert "v1.0.0" in repo.tags
    assert repo.stashes == []


if __name__ == "__main__":
    demonstration()
