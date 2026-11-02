# Git Advanced: Merge, Rebase, Cherry-Pick, Stash, Reset, Revert, and Tags

## Scope

This project models advanced Git history manipulation as explicit repository state transitions.

The seven operations are deliberately separated because they solve different problems:

| Operation | Primary purpose | History effect |
|---|---|---|
| Merge | Combine divergent histories | Creates a merge commit or performs fast-forward movement |
| Rebase | Replay commits onto another base | Creates new commit identities |
| Cherry-pick | Copy one selected change onto another history | Creates a new commit |
| Stash | Temporarily save uncommitted work | Moves working changes outside the branch history |
| Reset | Move a branch reference | Can change branch history without creating a commit |
| Revert | Undo a committed change safely | Creates a new inverse commit |
| Tag | Give a stable name to a commit | Adds a named reference |

The implementations use a common conceptual model:

Repository → Branches → Commits → Working Tree → History Operations → Tags

A commit records a tree, parent commit references, a message, and operation metadata. This makes ancestry and state transitions observable without depending on an installed Git executable.

## Domain Model

A branch is a movable reference to one commit. A commit is an immutable historical object. The working tree represents changes that have not yet become a commit.

The central distinction is between moving references and creating history.

`reset` moves a branch reference. It does not create an inverse commit.

`revert` preserves existing history and creates another commit whose tree represents the inverse of a previous commit.

`rebase` changes the ancestry of selected commits by replaying them on a different parent. The replayed commits therefore receive new identities.

`cherry-pick` selects the change introduced by a particular commit and applies that change to the current branch.

`stash` temporarily removes local working changes from the working tree without committing them to the branch.

`tag` names a specific commit so a release or other important historical point can be referenced independently of branch movement.

## Merge

The implementations model a three-way merge using:

- the current branch tip
- the source branch tip
- their merge base

For each path, the merge compares the base, current version, and source version.

A change is accepted automatically when only one side changed relative to the base. When both sides changed the same path differently, the operation reports a conflict instead of silently choosing one version.

The Python, JavaScript, and C++ implementations also recognize fast-forward situations. If the current branch is an ancestor of the source branch, the branch reference can move directly to the source tip.

A merge commit has two parents. This is distinct from an ordinary commit, which has one parent.

## Rebase

The Python implementation includes an explicit rebase operation. It identifies the common ancestor, collects commits unique to the current branch, and recreates them sequentially on the target branch.

The recreated commits retain their logical tree and message but receive new identities and metadata identifying the original commit.

Conceptually:

    A---B---C  feature
         \
          D---E  main

After rebasing feature onto main:

    A---D---E---B'---C'

The original `B` and `C` are not moved. New commits `B'` and `C'` represent their replayed versions.

Rebase therefore changes ancestry and should be distinguished from merge, which preserves the divergent histories and joins them with a merge commit.

## Cherry-Pick

Cherry-pick is implemented as a patch-oriented operation.

The source commit is compared with its first parent. Only paths whose values changed between those two commits are candidates for application.

The current branch must still contain the expected pre-change value for each affected path. A different current value is treated as a conflict.

This models an important distinction:

- merge combines histories
- cherry-pick copies a selected change

Cherry-pick therefore creates a new commit rather than transferring the original commit object to another branch.

## Stash

The stash model stores:

- a descriptive message
- the complete working tree
- the commit that served as the stash base

The working tree is then restored to the current committed state.

The JavaScript implementation uses a stack of stash entries. The Python implementation uses an explicit list. The Java implementation uses `ArrayDeque`.

A stash is not equivalent to a normal branch commit. It is temporary work preservation intended to allow the working tree to be changed or another branch to be checked out before returning to the unfinished work.

The implementations reject a simple stash restoration when the current committed tree has diverged from the recorded stash base. Real Git can perform more sophisticated three-way application and may require conflict resolution.

## Reset

Reset is modeled with three modes:

| Mode | Branch reference | Working tree |
|---|---|---|
| `soft` | Moves | Preserves working changes |
| `mixed` | Moves | Resets working tree to target commit |
| `hard` | Moves | Resets working tree to target commit |

The important distinction is that reset changes the branch reference rather than recording an inverse commit.

A hard reset can therefore make commits unreachable from the branch being reset. It is substantially different from `revert` when a branch has already been shared.

## Revert

Revert preserves the original commit and creates a new commit that reverses its change.

The implementation compares the target commit with its first parent, then applies the inverse transition to the current tree.

This creates an auditable history:

    A---B---C
         \
          R

where `R` records that the effect of `B` was intentionally reversed.

The operation detects conflicts when the current tree no longer contains the expected state introduced by the target commit.

## Tags

Tags provide stable names for commits.

The PostgreSQL model stores tags as rows referencing immutable commit records. The application implementations maintain a tag-to-commit mapping.

The example uses `v1.0.0` as a release reference.

A tag is not a branch. A branch normally moves as development progresses, while a release tag identifies a specific historical commit.

## Python Implementation

The Python program uses:

- `dataclass` for commit and stash records
- `Enum` for commit types
- dictionaries for commit, branch, and tag indexes
- sets for ancestry traversal
- explicit exceptions for invalid transitions
- SHA-1-derived short identifiers for deterministic in-process object identity
- complete logical trees for simplified content modeling

The repository class implements merge, rebase, cherry-pick, stash, reset, revert, and tag operations.

The demonstration creates divergent development, merges a feature, cherry-picks a commit into a maintenance branch, stashes local configuration, reverts a commit, and tags the resulting release point.

Assertions provide a basic integrity check for the final state.

## JavaScript Implementation

The JavaScript implementation uses Node.js standard-library facilities and represents repository trees with `Map`.

The repository is event-oriented in structure because each operation changes observable repository state and can fail independently. The `main` function is asynchronous-capable and uses a Promise-compatible process boundary through normal Node.js execution.

JavaScript-specific characteristics include:

- `Map` for repository indexes
- `Set` for ancestry and path collection
- immutable-style copies for commit trees
- `crypto.createHash` for commit identifiers
- explicit error propagation
- object-based stash records
- `Object.freeze` for operation constants

The implementation does not require npm packages.

## C++17 Implementation

The C++ program treats the repository as a stateful domain object with explicit ownership of commit and branch structures.

It uses:

- `std::unordered_map` for commit lookup
- `std::map` for ordered branch and tree state
- `std::set` for ancestry and path unions
- `std::optional` for files that may not exist
- `enum class` for commit types
- exceptions for invalid repository transitions

The merge algorithm performs a three-way comparison and refuses ambiguous conflicting changes.

The program also separates commit storage from branch references. This reflects Git's essential model: a branch is a reference to a commit, not a container holding a sequence of files.

## Java 17 Implementation

The Java implementation uses an enterprise-oriented service design.

The domain contains:

- `Commit` records for immutable commit state
- `StashEntry` records for temporary work
- `CommitType` and `ResetMode` enums
- `RepositoryPolicy` for validation rules
- `RepositoryService` for repository operations
- `GitException` for domain failures

The service separates validation from state transitions. Branch names, commit messages, and tags are validated by a policy object rather than being embedded throughout the repository workflow.

Collections are copied at commit boundaries so historical commit data cannot be accidentally changed through a caller's mutable map.

The implementation also uses streams for history selection and explicit service methods for merge, cherry-pick, stash, reset, revert, and tag behavior.

## PostgreSQL Implementation

The PostgreSQL model represents Git concepts relationally.

Core entities include:

| Table | Responsibility |
|---|---|
| `repositories` | Repository identity and default branch |
| `branches` | Branch references and protection state |
| `commits` | Immutable commit metadata |
| `commit_parents` | Commit ancestry |
| `repository_tags` | Named commit references |
| `pull_requests` | Change integration workflow |
| `pull_request_commits` | Commits included in a Pull Request |
| `developers` | Repository participants |
| `reviews` | Review decisions |
| `review_comments` | Line-level review discussions |
| `status_checks` | Automated validation state |
| `branch_protection` | Repository-level merge restrictions |

The schema deliberately separates commit ancestry from branches. This allows a branch to move to a different commit without modifying historical commit records.

Foreign keys enforce repository relationships. Check constraints validate states such as tag names, review counts, line numbers, and Pull Request status.

Indexes target common access paths such as repository history, Pull Request review state, status-check state, unresolved comments, and target-branch workflow status.

## Database Workflow

The database implementation includes functions for:

- counting unresolved review conversations
- counting active approvals
- counting failed status checks
- evaluating merge eligibility

`merge_eligibility` evaluates:

1. Pull Request state
2. required approval count
3. status-check completion
4. unresolved review conversations
5. required merge strategy

The procedure `merge_pull_request` locks the Pull Request with `pg_advisory_xact_lock`, evaluates eligibility inside the transaction, and changes the Pull Request to `merged` only when all policy conditions pass.

This models transactional workflow enforcement rather than treating merge eligibility as a display-only calculation.

## Failure Conditions

The implementations explicitly handle several unsafe operations.

| Failure | Reason |
|---|---|
| Merge conflict | Both sides changed the same path incompatibly |
| Cherry-pick conflict | Current content differs from the expected pre-change content |
| Revert conflict | Current content no longer matches the target commit's introduced state |
| Empty commit | No working-tree change exists |
| Empty stash | There is no local work to preserve |
| Invalid reset mode | Reset mode is outside `soft`, `mixed`, or `hard` |
| Unknown commit | Referenced history object does not exist |
| Duplicate tag | Tag name already identifies another commit |
| Invalid branch or tag name | Repository naming rule is violated |

These checks prevent the examples from silently converting ambiguous states into incorrect history.

## Performance Characteristics

Commit lookup is indexed by identifier in the application implementations.

Ancestry traversal is proportional to the number of reachable commits from the starting reference. The three-way merge examines the union of paths present in the base, current tree, and source tree.

The PostgreSQL schema uses indexes for high-frequency relational access but does not index every column. This avoids unnecessary write and storage overhead.

The examples represent complete logical trees for clarity. A production Git implementation stores content using object databases and deltas rather than copying a complete file tree into every commit object.

## Security Considerations

Repository history operations have different risk profiles.

`reset --hard` can discard branch-visible work, so it should be controlled carefully on shared branches.

`revert` is safer for published history because the corrective action is represented as a new commit.

Force-pushing a rebased shared branch can invalidate collaborators' references and should normally be restricted by repository policy.

Tags used for releases should be protected where release integrity matters.

The PostgreSQL implementation prevents direct updates to protected branch heads unless the policy explicitly permits them. Merge eligibility is evaluated inside a transaction, reducing the risk of a concurrent policy decision becoming stale before the merge state transition.

Commit messages, branch names, tag names, and repository paths are validated rather than accepted without constraints.

## Relationship Between the Operations

The operations can be grouped by their effect on history.

    Preserve existing history
        |
        +-- merge
        +-- revert
        +-- tag
        +-- stash

    Recreate or copy changes
        |
        +-- rebase
        +-- cherry-pick

    Move a reference
        |
        +-- reset

Merge joins histories. Rebase recreates selected commits on another base. Cherry-pick copies a selected change. Stash temporarily preserves unfinished work. Reset moves a branch reference. Revert records an inverse change. Tags name stable historical points.

Keeping these semantics separate is essential when selecting a safe Git operation for a repository state.
