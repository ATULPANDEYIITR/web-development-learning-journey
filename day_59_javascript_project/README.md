# Interactive Task Management and Repository Governance

## Purpose

This project models an engineering task management workflow in which development work is connected to Pull Requests, Code Review, approvals, automated status checks, and protected repository branches.

The four governance concepts remain distinct:

| Area | Primary responsibility |
|---|---|
| Pull Requests | Propose and track a change from a source branch toward a target branch |
| Code Review | Evaluate the technical quality and correctness of the proposed changes |
| Approvals | Record reviewer decisions against a particular Pull Request revision |
| Branch Protection | Enforce repository-level conditions before a protected branch can accept a merge |

The resulting workflow is:

`Task → Feature Branch → Commits → Pull Request → Review → Approval → Status Checks → Branch Protection → Merge → Task Completion`

The implementations use different engineering perspectives rather than reproducing the same program in five languages.

## Domain Model

The repository is represented as a set of branches containing commits. A feature branch provides the source state for a Pull Request, while a protected branch such as `main` provides the merge target.

A Pull Request records:

- source branch
- target branch
- author
- lifecycle state
- current commit set
- requested reviewers
- submitted reviews
- automated status checks
- review conversations
- selected merge strategy

A task represents work that must be completed. A task can be linked to its Pull Request so that repository governance affects the task lifecycle.

The important distinction is that a task is a work-management object, while a Pull Request is a change-management object.

## Pull Request Lifecycle

The implementations support the principal Pull Request states:

| State | Meaning |
|---|---|
| Draft | Change is being prepared and is not yet presented as ready for normal review |
| Open | Change is ready for review and can be evaluated for merge |
| Closed | Change has been closed without merging |
| Merged | Change has been accepted into the target branch |

The Python, JavaScript, and Java implementations explicitly model Draft-to-Open transitions and prevent invalid review or merge operations against inappropriate states.

The Pull Request source branch contains the proposed changes. The target branch identifies where the changes are intended to land.

A Pull Request can contain multiple commits. The latest commit is important because approvals and status checks are associated with a specific revision.

This allows the implementation to represent a critical repository-governance condition: an approval made against an earlier revision should not automatically remain valid after new changes are pushed.

## Draft Pull Requests

Draft Pull Requests are represented separately from ordinary open Pull Requests.

A draft can be used while implementation is incomplete. The Python, JavaScript, and Java implementations provide an explicit operation for marking a draft as ready.

The state transition is deliberately validated so that an already-open Pull Request cannot be marked ready again.

## Base-Branch Synchronization

A feature branch can become behind its target branch while review is in progress.

The Python implementation provides a synchronization operation that incorporates target-branch commits into the source branch representation and refreshes the Pull Request commit set.

This is important because merge eligibility is evaluated against the current revision rather than an earlier snapshot.

A production implementation would normally rely on a real version-control system for ancestry, conflict detection, and merge-base calculations. The learning implementation keeps the state model explicit and deterministic.

## Merge Conflicts

A merge conflict occurs when changes from the source and target branches cannot be combined automatically.

The source files deliberately do not pretend that a simple list of commits is a complete Git conflict engine. The models instead expose branch synchronization and make merge eligibility depend on the current Pull Request state.

A real repository system must calculate common ancestors, changed paths, file-level conflicts, and the resulting merge tree.

The distinction matters: Pull Request state management can model whether a change is ready, while a complete Git implementation must also calculate whether the underlying histories can be merged.

## Merge Strategies

The implementations recognize three common strategies:

| Strategy | Resulting behavior |
|---|---|
| Merge commit | Creates a merge commit representing the integration |
| Squash | Creates one target-branch commit representing the Pull Request |
| Rebase | Replays the change onto the target history |

The examples use squash merging because it gives the task-management demonstration a compact target-branch history.

Branch protection can impose additional history requirements. The model therefore stores linear-history policy separately from the merge strategy.

## Code Review

Code Review evaluates the proposed changes rather than defining repository permissions.

The implementations model review decisions such as:

- comment
- approval
- requested changes
- dismissal

Reviewers must be different from the Pull Request author.

A reviewer can be explicitly requested before submitting a review. This makes reviewer participation a domain relationship rather than an unrestricted operation.

Review comments are attached to reviews and can be resolved independently.

The review workflow is intentionally different from Pull Request lifecycle management:

`Pull Request → Review → Review Comments → Discussion → Resolution`

A Pull Request can remain open while multiple review decisions and discussions occur.

## Review Quality and Scope

A useful engineering review should evaluate the actual change rather than merely confirm that the Pull Request exists.

The example review flow considers:

- correctness of task-state transitions
- validation behavior
- implementation quality
- test status
- security checks
- unresolved discussion items

Review scope is represented as review-specific information. Repository-wide restrictions are represented by branch protection instead of being mixed into the review object.

This separation prevents the same rule from being implemented in multiple domain layers.

## Review Discussions

Review discussions can identify a concrete problem without immediately changing the Pull Request lifecycle.

The implementations represent unresolved conversations explicitly.

A protected branch can require all relevant conversations to be resolved before merge.

This creates a relationship between review and governance:

`Review identifies issue → Conversation remains unresolved → Branch protection blocks merge`

Resolving the conversation does not itself approve the Pull Request. Approval remains a separate reviewer decision.

## Approvals

Approval is a review decision with a specific semantic meaning.

The implementations distinguish approval from a generic comment.

An approval is counted only when:

- the reviewer is not the Pull Request author
- the review has not been dismissed
- the review is associated with the current Pull Request head commit
- the reviewer is participating in the requested-review workflow where applicable

This is important because approval is not an unconditional property of a Pull Request.

## Stale Approvals

A stale approval occurs when a reviewer approved one revision and new commits subsequently change the Pull Request.

The source implementations associate approvals with the commit SHA that was reviewed.

When evaluating merge eligibility, the system compares the approval's commit SHA with the current Pull Request head SHA.

Conceptually:

`Approval at H1 + new commit H2 → approval at H1 is not current for H2`

This prevents an old approval from silently authorizing changes that the reviewer never evaluated.

## Dismissed Approvals

A dismissed approval is retained as historical review information but excluded from current approval counts.

This distinction preserves auditability while preventing the dismissed decision from contributing to merge authorization.

The Python and JavaScript models include a dismissal field, while the PostgreSQL model stores the same property directly on the review record.

## Required Reviews

Branch protection defines how many current approvals are required.

For example, the sample policy requires two approvals.

The merge engine calculates distinct eligible reviewers rather than counting duplicate approval events from the same reviewer.

This avoids treating multiple approvals from one reviewer as equivalent to independent reviewer decisions.

## Reviewer Eligibility

Reviewer identity is validated against Pull Request authorship.

Self-approval is rejected because it would undermine the independent-review condition represented by the sample governance policy.

A production system can extend this model with:

- repository teams
- ownership rules
- code ownership
- reviewer groups
- role-based permissions
- separation-of-duties rules

The example keeps reviewer eligibility explicit without introducing unrelated organizational systems.

## Branch Protection

Branch Protection is a repository-level enforcement mechanism.

The sample protected `main` branch requires:

| Policy | Sample value |
|---|---|
| Required approvals | 2 |
| Required status checks | `unit-tests`, `security-scan` |
| Direct pushes | Restricted |
| Force pushes | Restricted |
| Branch deletion | Restricted |
| Conversation resolution | Required |
| Linear history | Required |
| Administrator bypass | Disabled |

Branch protection does not perform the review itself.

It evaluates whether the accumulated evidence satisfies the repository's merge policy.

## Required Status Checks

Automated checks are represented separately from human review.

The example uses:

- `unit-tests`
- `security-scan`

A check is valid for merge only when it is passing and associated with the current Pull Request head commit.

This prevents a successful test result from an older revision from being treated as evidence for newer code.

The distinction is:

`Review = human decision`

`Status Check = automated evidence`

`Branch Protection = repository enforcement`

## Direct Push Restrictions

Direct-push restrictions prevent contributors from bypassing the Pull Request workflow when changing a protected branch.

The PostgreSQL policy stores this requirement explicitly.

The source implementations model the policy even though they do not implement a networked Git server capable of intercepting an actual Git push.

A production enforcement layer would apply this rule at the repository server or hosting platform boundary.

## Force-Push Restrictions

Force pushes can rewrite branch history.

The protection model therefore stores a separate `restrictForcePush` or equivalent property rather than treating force pushes as ordinary updates.

This is especially relevant for protected branches because rewritten history can invalidate assumptions about reviewed commits and previously evaluated changes.

## Branch Deletion Restrictions

Protected branches can also prevent deletion.

The policy models deletion restrictions independently from merge restrictions.

This matters because branch lifecycle operations and Pull Request merge operations are separate repository actions.

## Linear History

The example supports a linear-history requirement.

Linear history is a repository-level policy rather than an approval state.

A Pull Request can have sufficient approvals while still being ineligible if the selected merge behavior violates the target branch's history policy.

The actual Git history calculation is outside the scope of these in-memory examples, but the policy boundary is represented explicitly.

## Administrator Bypass

The policy includes an administrator-bypass field.

The sample configuration disables bypassing.

This makes administrative authority an explicit governance decision instead of silently allowing privileged users to ignore normal requirements.

A production system would need authenticated authorization, audit logging, role management, and a documented emergency-change procedure around any bypass capability.

## Merge Eligibility

Merge eligibility is the final decision produced by the governance model.

A simplified decision path is:

`PR open`
→ `current approvals sufficient`
→ `required checks passing`
→ `checks correspond to current head`
→ `review conversations resolved`
→ `repository policy satisfied`
→ `merge permitted`

The result includes reasons when a Pull Request is blocked.

This is preferable to returning only a boolean because a task-management interface can display actionable blocking conditions.

## Python Implementation

The Python implementation uses dataclasses to represent domain entities such as commits, reviews, branches, Pull Requests, status checks, tasks, and protection policies.

`Repository` acts as the main aggregate coordinating state changes.

Python collections provide direct representations of:

- branch registries
- Pull Request registries
- reviewer sets
- status-check dictionaries
- task dictionaries
- commit lists

The `merge_eligibility` method centralizes policy evaluation.

The demonstration includes an important stale-approval scenario. A Pull Request receives approvals, a new commit is added, and the old approvals no longer satisfy the current-head requirement.

Assertions verify expected blocked and eligible states.

The implementation uses only the Python standard library.

## JavaScript Implementation

The JavaScript implementation treats the task manager as an event-driven application.

`TaskManager` extends `EventEmitter` and emits domain events such as:

- task creation
- task updates
- Pull Request creation
- Pull Request readiness
- review submission
- merge

`Map` and `Set` are used for repositories of state such as branches, Pull Requests, reviewers, tasks, checks, and protection policies.

The event-driven structure is appropriate for an interactive task management application because a browser interface can subscribe to the same kinds of events for board updates, notifications, review indicators, and merge-status changes.

The file uses Node.js standard-library modules only.

## C++17 Implementation

The C++ implementation focuses on a repository governance and merge-eligibility engine.

Strongly typed enumerations represent workflow states, review states, check states, task states, and merge strategies.

STL containers provide:

- `unordered_map` for entity lookup
- `map` for ordered Pull Request records
- `set` for reviewers and required checks
- `vector` for ordered commits and reviews
- `optional` for values that may not exist yet

The `GovernanceEngine` explicitly validates branch existence, reviewer eligibility, review state, status checks, unresolved conversations, and merge conditions.

Exceptions are used for invalid state transitions and failed governance operations.

## Java 17 Implementation

The Java implementation models enterprise governance through records, classes, interfaces, enums, collections, and explicit policy types.

Records provide immutable value-oriented structures for:

- commits
- status checks
- reviews
- tasks
- Pull Requests
- protection policies
- eligibility results

The mutable `Repository` aggregate owns workflow transitions.

`MergePolicy` defines a policy abstraction that can be extended with different governance strategies.

The `Eligibility` record separates a decision from the reasons supporting that decision.

Java collections are used for reviewer sets, check maps, task maps, Pull Request maps, and repository branches.

The implementation therefore represents domain behavior as explicit services and state transitions rather than as a collection of unrelated examples.

## PostgreSQL Implementation

The PostgreSQL implementation provides the relational representation of the complete workflow.

The `task_governance` schema contains tables for:

- repositories
- users
- branches
- commits
- Pull Requests
- Pull Request commits
- review requests
- reviews
- review comments
- conversations
- status checks
- branch protection policies
- required status checks
- tasks

Foreign keys preserve relationships between repository entities.

Check constraints enforce local validity rules such as non-empty titles and non-negative required-review counts.

Unique constraints prevent duplicate repository names, branch names within a repository, reviewer requests, and status-check definitions.

Indexes target common access paths such as:

- repository branches
- branch commit history
- Pull Request target and state
- review state by Pull Request and commit
- status checks by Pull Request
- task state and priority

The `merge_eligibility` PostgreSQL function evaluates approval freshness, required checks, and unresolved review discussions.

The transactional example uses a transaction and advisory lock before evaluating and attempting a merge state transition. The transaction is rolled back so the demonstration database remains reusable.

## Relational Workflow

The database relationship can be represented as:

`Repository`
`  └── Branch`
`       └── Commit`
`            └── Pull Request`
`                 ├── Review Request`
`                 ├── Review`
`                 │    └── Review Comment`
`                 ├── Conversation`
`                 ├── Status Check`
`                 └── Merge Eligibility`
`                      └── Branch Protection Policy`

Task management connects to the repository workflow through a linked Pull Request:

`Task → Pull Request → Governance Evidence → Merge`

## Failure Conditions

The implementations deliberately reject several invalid operations.

| Failure | Enforcement |
|---|---|
| Empty task title | Application validation |
| Invalid task priority | Application validation |
| Unknown branch | Repository lookup validation |
| Source and target branch identical | Pull Request validation |
| Pull Request without commits | Pull Request validation |
| Author self-review | Review validation |
| Unrequested reviewer | Review validation |
| Review on closed or merged PR | State validation |
| Missing required approval | Merge eligibility |
| Dismissed approval | Merge eligibility |
| Stale approval | Commit SHA comparison |
| Missing required status check | Merge eligibility |
| Failing status check | Merge eligibility |
| Stale status check | Commit SHA comparison |
| Unresolved conversation | Branch protection |
| Invalid merge transition | Database trigger and application validation |

## Security Considerations

The examples treat repository governance as an authorization boundary.

Important controls include:

- preventing self-approval
- requiring independent reviewers
- requiring current approvals
- invalidating stale review evidence
- requiring current automated checks
- preventing unresolved review discussions from being ignored
- restricting protected-branch operations
- separating administrator bypass policy from ordinary merge authorization

These models do not implement authentication, network authorization, cryptographic commit verification, or an actual Git server.

A production implementation must enforce authorization at the service boundary rather than trusting client-side state.

The JavaScript event model should not be treated as a security boundary. Browser-visible state can be modified by a client and must be revalidated by a trusted backend.

## Performance Characteristics

The in-memory implementations use hash-based collections for common entity lookup.

Typical operations such as branch, task, Pull Request, reviewer, and status-check lookup are approximately constant-time on average when implemented with hash maps or sets.

Merge eligibility scans the relevant Pull Request reviews and required checks. If `R` is the number of reviews and `C` is the number of required checks, the principal evaluation cost is approximately `O(R + C)`.

The PostgreSQL implementation uses indexes for frequently filtered fields. Relational query planning can then avoid scanning unrelated Pull Requests, reviews, checks, and tasks.

The examples intentionally keep the model understandable. A production system handling very large repositories would also need pagination, archival strategies, event histories, concurrency control, and optimized aggregation.

## State Consistency

A critical design decision is that approval and status-check evidence is tied to a commit revision.

This prevents the system from making the unsafe assumption that:

`Approved once = always approved`

Instead:

`Approved at revision H1`

is different from:

`Approved at revision H2`

The same rule applies to automated checks.

This makes the merge decision dependent on the actual revision currently proposed by the Pull Request.

## Task Management Relationship

The interactive task-management perspective does not replace repository governance.

A task describes work.

A Pull Request describes a proposed implementation.

Code Review evaluates the implementation.

Approvals record reviewer decisions.

Status checks provide automated evidence.

Branch Protection enforces repository-level conditions.

Merge changes the target branch.

Task completion records the resulting work state.

The relationship therefore remains:

`Task`
→ `Implementation`
→ `Pull Request`
→ `Review`
→ `Approval`
→ `Checks`
→ `Protected Branch`
→ `Merge`
→ `Task Done`

This separation keeps work management and source-control governance connected without treating them as the same domain object.

## Practical Limitations

The implementations are executable learning artifacts rather than complete Git hosting systems.

They do not implement:

- actual Git object storage
- cryptographic commit hashing
- three-way merge algorithms
- file-level conflict detection
- network authentication
- repository hosting protocols
- distributed locking across application instances
- real branch permissions
- identity-provider integration
- persistent event sourcing

The PostgreSQL model provides persistence and database-level integrity, while the in-memory programs provide explicit workflow behavior.

A production architecture would normally place these responsibilities behind authenticated application services and connect them to an actual Git hosting system.

## Executable Components

| File | Engineering focus |
|---|---|
| Python | Repository workflow simulation with explicit Pull Request, review, approval, check, task, and protection state |
| JavaScript | Event-driven interactive task-management and governance model |
| C++17 | Strongly typed repository merge-eligibility engine |
| Java 17 | Enterprise-oriented domain model with records, policy abstractions, validation, and services |
| PostgreSQL | Relational repository-governance model with constraints, indexes, functions, triggers, views, and transactions |

## Core Distinctions

The project preserves four separate responsibilities throughout all implementations:

**Pull Requests** propose and track a change.

**Code Review** evaluates the proposed change and records technical discussion.

**Approvals** represent reviewer decisions about a particular revision.

**Branch Protection** determines whether repository-level merge conditions have been satisfied.

A successful merge requires these mechanisms to cooperate without collapsing them into a single state.

## Demonstrated Governance Scenario

The primary scenario begins with a protected `main` branch and a feature branch containing task-management changes.

The developer opens a Pull Request and requests two reviewers.

One reviewer initially requests changes and creates a review discussion. The discussion must be resolved before merge.

Both reviewers subsequently approve the current Pull Request revision.

The required `unit-tests` and `security-scan` checks pass against that same revision.

The branch-protection evaluator then determines that all required conditions are satisfied.

The Pull Request is merged using the squash strategy, and the associated task is moved to the completed state.

The scenario demonstrates the full relationship between work tracking, proposed changes, technical review, approval evidence, automated validation, repository policy, and final merge authorization.
