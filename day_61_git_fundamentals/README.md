# Git Fundamentals: Repository State, Commits, Staging, Branches, and HEAD

## Scope

This project models Git fundamentals as an executable repository-state system rather than as a collection of isolated commands. The five implementations represent the same core domain from different engineering perspectives:

| Implementation | Primary perspective | Main mechanisms |
|---|---|---|
| Python | Repository workflow simulation | Dataclasses, dictionaries, validation, object storage, commit graph |
| JavaScript | Event-driven repository model | Maps, Sets, asynchronous auditing, object hashing |
| C++17 | Repository state engine | STL containers, graph traversal, merge-base calculation, exception handling |
| Java 17 | Enterprise domain model | Records, services, policies, immutable domain values, explicit state |
| PostgreSQL | Relational repository model | Constraints, foreign keys, triggers, functions, views, transactional queries |

The central distinction is between the working tree, staging area, committed history, branches, and `HEAD`.

```text
Working Tree
     |
     | git add
     v
Staging Area / Index
     |
     | git commit
     v
Commit Object
     |
     +--------------------+
     |                    |
     v                    v
 Branch Reference       HEAD
     |                    |
     +----------+---------+
                |
                v
          Current Commit
```

## Core Repository Model

A repository contains versioned project history and references that identify the current line of development.

The model used by the source files separates these states:

- **Working tree**: files currently being edited.
- **Index**: the proposed contents of the next commit.
- **Commit**: an immutable historical snapshot with metadata and parent relationships.
- **Branch**: a movable reference to a commit.
- **HEAD**: the current branch reference or a specific commit when detached.
- **Object database**: content-addressed representations of repository data.

This separation is important because editing a file does not automatically stage it, and staging a file does not automatically create a commit.

## Repository Initialization

The examples begin with an empty `main` branch and then create an initial commit.

The first commit has no parent. Later commits point to earlier commits through parent references.

```text
Commit A
   |
   v
Commit B
   |
   v
Commit C
```

The branch reference does not contain the entire history. It points to the current tip:

```text
main
 |
 v
Commit C -> Commit B -> Commit A
```

Moving the branch reference to another commit changes the branch's current position without rewriting the commit objects themselves.

## Working Tree

The working tree represents files currently present in the checkout.

The implementations allow files to be created and modified before staging.

For example:

```text
README.md       unchanged
service.py      modified
notes.txt       untracked
```

A clean working tree means the working contents correspond to the staged contents and the current committed state.

The Python implementation exposes this through `Repository.status()`. The JavaScript implementation returns a structured object containing `staged`, `modified`, and `untracked` paths. The C++ implementation uses `FileState`, while Java uses an `EnumMap<FileState, List<String>>`.

## Staging Area

The staging area is represented by the `index` collection in the Python, JavaScript, C++, and Java implementations.

The important state transition is:

```text
working file
    |
    | add
    v
index
    |
    | commit
    v
commit tree
```

A file can be modified after it has been staged:

```text
working tree: version 3
index:        version 2
commit:       version 1
```

The source implementations detect this distinction as a `modified` working-tree state rather than silently including the latest contents in the next commit.

This reflects an important Git property: the commit is constructed from the index, not directly from whatever happens to be in the working directory.

## Commits

A commit in the implementations contains:

- An identifier.
- Author information.
- A commit message.
- Parent commit identifiers.
- A snapshot of tracked file contents.

The Python implementation creates Git-like blob and commit objects using SHA-1 framing.

The JavaScript implementation also constructs content-addressed object identifiers and stores objects in a `Map`.

The C++ and Java implementations use deterministic identifiers for the educational model while retaining the same architectural distinction between content objects and commits.

A commit is immutable after creation. Branches move; historical commits do not.

## Commit Graph

Commit history is a directed acyclic graph rather than merely a list.

A linear history looks like:

```text
A <- B <- C
```

A branch creates another line:

```text
          D
         /
A <- B
         \
          E
```

The implementations traverse this graph when determining ancestry and merge bases.

The Python implementation uses `_ancestor_distances()` and `find_merge_base()`.

The JavaScript implementation uses `ancestors()` and `mergeBase()`.

The C++ implementation uses breadth-first traversal with `queue`, `unordered_map`, and `unordered_set`.

The Java implementation separates ancestor-distance calculation from merge behavior, making graph traversal a reusable domain operation.

## Branches

A branch is a named reference to a commit.

The source implementations model branches as mappings such as:

```text
main           -> commit B
feature/audit  -> commit E
```

Creating a branch does not duplicate the commit history. It creates another reference to an existing commit.

When a commit is made on a branch, that branch moves to the new commit:

```text
Before:

main -> B

After commit:

main -> C -> B
```

The other branches remain unchanged.

## HEAD

`HEAD` identifies the current checkout context.

When attached to a branch:

```text
HEAD
 |
 v
main
 |
 v
Commit C
```

When detached:

```text
HEAD
 |
 v
Commit B
```

The Python, JavaScript, C++, and Java programs explicitly represent detached HEAD state.

The examples also demonstrate checking out an historical commit and then returning to `main`.

Detached HEAD is useful for inspecting or testing a historical state, but a new commit made there is not automatically attached to a named branch.

## Checkout State Safety

The implementations prevent branch switching when local changes are present.

This protects the current working state from being overwritten by another branch's snapshot.

The rule is:

```text
dirty working tree
       |
       X
    checkout

clean working tree
       |
       v
    checkout
```

The Python implementation raises `RepositoryStateError`.

The JavaScript implementation raises `RepositoryStateError`.

The C++ implementation throws `RepositoryStateError`.

The Java implementation throws `StateException`.

This is a domain-level invariant rather than merely a user-interface preference.

## Branch Creation and Validation

Branch names are validated before references are created.

The implementations reject unsafe names containing path traversal patterns and invalid characters.

This is important when repository references eventually map to filesystem paths or are exposed through automation.

The Python implementation validates branch names with regular expressions.

The JavaScript implementation uses a regular expression and explicit path checks.

C++ performs character-level validation.

Java uses a compiled `Pattern`.

The PostgreSQL schema enforces a branch-name format with a `CHECK` constraint.

## Merge Mechanics

Merging combines two histories.

The source implementations first identify simple cases:

```text
same commit
    -> nothing to merge

source is ancestor of current
    -> current branch already contains source

current is ancestor of source
    -> fast-forward

diverged histories
    -> three-way merge
```

Three-way merging compares:

```text
base
 /  \
ours theirs
```

For each file:

- If both sides agree, the shared value is retained.
- If only one side changed relative to the base, that change is selected.
- If both sides changed differently, the file is reported as a conflict.

The Python implementation raises a repository-state error containing conflicting paths.

The JavaScript implementation performs the same three-way comparison using `Map`.

The C++ implementation uses ordered STL maps and records conflicting paths before rejecting the merge.

The Java implementation explicitly transitions the repository to a `MERGING` state when conflicts are detected.

## Merge Base

A merge base is a common ancestor used as the comparison point for a three-way merge.

For:

```text
        C
       / \
      D   E
```

`C` is the merge base of `D` and `E`.

The implementations compute ancestor distances and select a common ancestor with the smallest combined traversal distance.

This is a graph problem. It is not equivalent to comparing only the two branch-tip snapshots.

## Merge Conflicts

A conflict occurs when both branches independently modify the same logical file relative to the common base and the resulting values differ.

Example:

```text
Base:   timeout=30

Ours:   timeout=60
Theirs: timeout=90
```

Neither side can be selected automatically without losing one branch's change.

The implementations reject such merges rather than silently choosing one value.

This failure behavior is safer for repository automation because an incorrect automatic choice can produce a valid-looking but semantically wrong commit.

## Python Implementation

The Python program uses:

- `dataclass` objects for repository entities.
- `Enum` values for object types.
- Dictionaries for repository state.
- Sets for graph traversal.
- Exceptions for invalid state transitions.
- `pathlib` for snapshot output.
- SHA-1 hashing for Git-like object identifiers.
- Assertions for important state invariants.

The `Repository` class provides operations corresponding to fundamental repository behavior.

The `status()` method compares three states:

```text
HEAD tree
index
working tree
```

This permits separate identification of staged, modified, and untracked content.

The `commit()` method serializes commit metadata and creates a content-addressed commit object.

The `find_merge_base()` method treats history as a graph rather than a flat sequence.

The snapshot method writes the working tree, index, and references to temporary files without exposing repository paths outside the selected directory.

The program also rejects path traversal such as `../outside.txt`.

## JavaScript Implementation

The JavaScript program models repository state with `Map` and `Set`.

The choice of `Map` is significant because repository paths and commit identifiers are explicit keys rather than object-property names.

The implementation also includes asynchronous behavior through `auditAsync()`.

The asynchronous audit reports:

- Current HEAD.
- Current branch.
- Object count.
- Commit count.
- Working-tree cleanliness.

The snapshot operation uses Node.js `fs/promises` and a temporary directory.

This creates a complementary perspective in which repository state can be inspected asynchronously without introducing third-party dependencies.

The JavaScript merge implementation uses `Set` to construct the union of files participating in a three-way merge.

## C++17 Implementation

The C++ implementation treats the repository as a state engine.

It uses:

- `std::map` for deterministic file and branch ordering.
- `std::unordered_map` for object and commit lookup.
- `std::unordered_set` for graph traversal.
- `std::queue` for breadth-first ancestry analysis.
- Enumerations for object and file states.
- Custom exception classes for domain failures.

The `Repository` class separates:

- Object creation.
- Path validation.
- Status calculation.
- Commit creation.
- Branch creation.
- Checkout.
- Ancestry checks.
- Merge-base selection.
- Three-way merge.

The implementation deliberately avoids external libraries.

## Java 17 Implementation

The Java implementation represents repository behavior as an enterprise-oriented domain model.

Java records are used for immutable values such as:

- `GitObject`.
- `Commit`.
- `Branch`.
- `ReviewPolicy`.

`Repository` owns state transitions, while `MergeEligibilityService` demonstrates how repository policy evaluation can be separated into a service layer.

The `ReviewPolicy` represents a repository-governance concept that is adjacent to Git fundamentals without changing the definition of a commit or branch.

Its policy includes:

- Required approval count.
- Required status checks.
- Clean-tree requirement.

The `mergeEligible()` operation demonstrates that repository state and policy state can be evaluated independently.

This distinction is useful in enterprise systems because the existence of a technically valid Git merge does not necessarily mean an organization permits the merge.

## PostgreSQL Model

The PostgreSQL implementation treats repository information as relational state.

The primary entities are:

```text
repositories
    |
    +-- repository_members
    |
    +-- branches
    |      |
    |      +-- commits
    |
    +-- pull_requests
           |
           +-- pull_request_commits
           +-- reviews
           |     |
           |     +-- review_comments
           |
           +-- status_checks
           |
           +-- branch_protection_policies
                  |
                  +-- required_status_checks
                  +-- approval_requirements
```

The relational design separates Git history from governance information.

A branch stores its current commit reference.

A commit stores its parent reference.

A Pull Request identifies a source branch, target branch, source tip, and target base.

Reviews record decisions against a specific commit.

Status checks record automated validation against a specific commit.

Branch protection policies specify repository-level merge requirements.

## Database Integrity

The schema uses foreign keys to prevent references to nonexistent repositories, branches, commits, reviews, and policies.

`CHECK` constraints validate:

- Repository names.
- Branch names.
- Commit identifiers.
- Non-empty commit messages.
- Positive review-comment line numbers.
- Non-negative approval requirements.

The Pull Request trigger verifies that source and target branches belong to the same repository.

The protected-branch trigger prevents deletion when branch protection disallows deletion.

These constraints move important invariants into the database rather than relying solely on application code.

## Database Workflow

The sample database creates:

- An `acme/platform-service` repository.
- Repository members.
- `main`.
- `feature/audit`.
- Initial commits.
- An audit Pull Request.
- Two eligible approvals.
- Resolved review conversation data.
- Passing unit tests.
- A passing security scan.
- A protected target branch.

The `merge_eligibility()` function evaluates the current Pull Request against its target branch policy.

The decision checks:

1. Pull Request existence.
2. Pull Request state.
3. Required approval count.
4. Reviewer eligibility.
5. Approval freshness against the current source commit.
6. Unresolved conversations.
7. Failed status checks.
8. Missing required status checks.

The result is returned as a Boolean decision and an explicit reason.

## Relationship Between Git State and Governance State

Git fundamentals and repository governance should not be conflated.

The fundamental Git state is:

```text
working tree
    |
    v
index
    |
    v
commit graph
    |
    v
branch references
    |
    v
HEAD
```

Governance adds another layer:

```text
commit / branch state
        |
        v
review decisions
        |
        v
automated checks
        |
        v
repository policy
        |
        v
merge eligibility
```

A commit can be technically valid while still being ineligible for a protected branch.

Likewise, a branch can point to a valid commit even when a repository policy requires reviews or checks that have not yet passed.

## Pull Requests, Code Review, Approvals, and Branch Protection

These concepts have different responsibilities.

| Area | Primary responsibility |
|---|---|
| Pull Request | Proposes integration of one branch into another |
| Code Review | Evaluates the proposed changes |
| Approvals | Records review decisions that satisfy approval requirements |
| Branch Protection | Enforces repository-level conditions before integration |

The Git fundamentals implementations focus on repository state, branches, commits, staging, checkout, and merging.

The PostgreSQL model extends that foundation with Pull Requests, reviews, status checks, and protection policies.

This separation prevents an approval from being treated as equivalent to a branch or a status check.

## Pull Request Lifecycle

A Pull Request connects a source branch with a target branch.

A representative lifecycle is:

```text
source branch
     |
     v
Pull Request opened
     |
     v
commits updated
     |
     v
review + automated checks
     |
     +---- changes requested ----+
     |                           |
     |                           v
     |                       new commits
     |                           |
     +---------------------------+
     |
     v
merge eligibility
     |
     v
merge
```

Draft state represents work that is not yet intended for final review.

An open Pull Request can receive new commits. When the source branch advances, previous approvals may no longer be applicable to the new source commit.

Closing a Pull Request without merging is distinct from merging it.

Reopening restores an integration workflow without implying that previous review decisions automatically remain valid.

## Code Review

Code review evaluates the proposed change rather than merely checking whether a branch exists.

The database represents individual reviews separately from review comments.

A review can be:

- `commented`
- `approved`
- `changes_requested`
- `dismissed`

Review comments identify the affected file and optionally a line number.

A comment can remain unresolved until the author or reviewer explicitly resolves the discussion.

Review quality depends on scope and evidence. Useful review criteria include:

- Correctness.
- Regression risk.
- Security impact.
- Test coverage.
- Maintainability.
- Compatibility.
- Operational behavior.

A review is not the same thing as an approval. A reviewer can participate in a discussion without approving the change.

## Approvals

An approval is a decision associated with a particular review and commit.

The PostgreSQL model requires approvals to correspond to the current Pull Request source commit when evaluating eligibility.

This models stale-approval behavior:

```text
commit A
  |
  +-- approval
  |
  v
commit B
```

An approval recorded against `A` does not automatically satisfy a policy evaluated against `B`.

Approval requirements can also identify eligible reviewers explicitly.

This prevents an arbitrary review count from being treated as equivalent to a valid approval requirement.

## Branch Protection

Branch protection operates at the repository-policy level.

The PostgreSQL policy can require:

- A minimum number of reviews.
- Particular reviewers.
- Successful status checks.
- Resolved conversations.
- No direct pushes.
- No force pushes.
- No branch deletion.
- Linear history.

These are enforcement conditions, not properties of the commit object itself.

The branch-protection model therefore sits above the Git commit graph.

```text
Commit validity
       |
       v
Branch state
       |
       v
Pull Request state
       |
       +--> reviews
       |
       +--> approvals
       |
       +--> status checks
       |
       v
Branch protection policy
       |
       v
Merge eligibility
```

## Failure Modes

The implementations intentionally reject unsafe or ambiguous operations.

| Failure | Protection |
|---|---|
| Empty commit message | Validation |
| Empty staging area | State validation |
| Invalid branch name | Branch validation |
| Unknown branch | Lookup validation |
| Unknown commit | Commit validation |
| Checkout with local changes | State protection |
| Merge with local changes | State protection |
| Divergent conflicting changes | Three-way conflict detection |
| Detached-HEAD merge | Repository state validation |
| Path traversal | Path validation |
| Missing required approval | Policy evaluation |
| Stale approval | Commit-specific approval evaluation |
| Failed status check | Merge eligibility failure |
| Unresolved review conversation | Policy evaluation |
| Protected branch deletion | Database trigger |

## Performance Considerations

The educational implementations favor clarity and explicit state over the storage and indexing optimizations used by production Git.

Commit lookup is generally constant-time in the Python, JavaScript, C++, and Java hash-based collections.

File-tree comparisons are approximately `O(F log F)` when sorted traversal is used or `O(F)` for hash-based set construction, where `F` is the number of paths considered.

Ancestor traversal is proportional to the number of reachable commits.

Three-way merging requires examination of the union of paths present in the base, current branch, and source branch.

The PostgreSQL model adds indexes to the access paths used by Pull Request, review, status-check, and commit reporting queries.

Indexes are deliberately placed on workflow predicates rather than on every column.

## Security Considerations

Repository tooling should treat file paths, branch names, commit identifiers, and workflow state as untrusted input.

The implementations therefore reject path traversal patterns.

The PostgreSQL model uses foreign keys and constraints to prevent invalid references.

Governance decisions should be evaluated against the exact source commit being merged. This reduces the risk of treating an earlier reviewed state as equivalent to a later unreviewed state.

Direct-push and force-push restrictions in branch protection are represented as explicit policy fields.

Administrator bypass is represented separately from ordinary permissions because an administrative override is a governance decision, not an ordinary developer operation.

## Practical Distinctions

The most important operational distinctions are:

| Mechanism | What it controls |
|---|---|
| Working tree | Current local file contents |
| Staging area | Exact contents proposed for the next commit |
| Commit | Immutable historical snapshot |
| Branch | Named reference to a commit |
| HEAD | Current checkout reference |
| Pull Request | Proposed integration between branches |
| Review | Evaluation of proposed changes |
| Approval | Explicit positive review decision |
| Status check | Automated validation result |
| Branch protection | Repository-level merge enforcement |

Confusing these states causes common workflow errors. For example, modifying a file does not move a branch, approving a Pull Request does not change the commit graph, and branch protection does not itself create commits.

## Executable Scenarios

The Python, JavaScript, C++, and Java programs all construct a repository with an initial state, create a feature branch, add feature work, make a separate main-branch change, and perform a merge.

They also inspect historical state through detached HEAD behavior.

The PostgreSQL script constructs a repository and a protected Pull Request workflow, then evaluates whether the current state satisfies the configured policy.

Together, the implementations provide separate views of the same repository concepts:

```text
files
  |
  v
working tree
  |
  | stage
  v
index
  |
  | commit
  v
commit graph
  |
  | branch references
  v
HEAD / branches
  |
  | proposed integration
  v
Pull Request
  |
  +--> review
  +--> approval
  +--> status checks
  |
  v
branch protection
  |
  v
merge eligibility
```

## Limitations of the Model

The implementations intentionally model core repository behavior rather than every internal detail of production Git.

They do not attempt to reproduce:

- Git pack files.
- Loose-object compression.
- Reflogs.
- Garbage collection.
- Index file binary format.
- Rename detection heuristics.
- Recursive merge strategies.
- Octopus merges.
- Submodules.
- Sparse checkout.
- Git LFS.
- Remote transport protocols.
- Cryptographic commit signing.

The merge algorithm is a deliberately constrained three-way file-content model. Production merge systems use substantially more sophisticated algorithms and repository metadata.

The JavaScript, C++, and Java identifiers are deterministic educational representations rather than complete implementations of Git's production object-format guarantees.

The PostgreSQL model stores governance and repository metadata relationally rather than implementing a complete Git object database.

These limitations keep the implementations focused on the fundamental relationships between repository state, staging, commits, branches, HEAD, and merge eligibility.
