# GitHub Remote Repository and Repository Governance Workflow

## Scope

This learning artifact models a repository workflow centered on GitHub-style remote repository operations and repository governance.

The implementations cover:

- Remote repository cloning
- Local and remote branch synchronization
- Push and pull behavior
- Repository README and issue workflows
- Pull Requests
- Code Review
- Approval decisions
- Branch Protection
- Status checks
- Merge eligibility
- Merge strategies
- Review conversations
- Failure handling and validation

The four governance areas are deliberately separated:

| Area | Primary responsibility |
|---|---|
| Pull Request | Proposes a set of changes from one branch toward another |
| Code Review | Evaluates the proposed changes and records review discussion |
| Approvals | Records explicit review decisions that contribute to merge eligibility |
| Branch Protection | Defines repository-level conditions that must be satisfied before protected-branch merging |

The repository synchronization workflow is related but operates at a different level:

`Remote Repository → Clone → Local Branch → Commit → Push/Pull → Pull Request → Review → Approval → Status Checks → Branch Protection → Merge`

## Domain Model

The implementations use a repository-development scenario containing a protected `main` branch and a feature branch.

The main relationships are:

`Repository`
`  ├── Branches`
`  │    └── Commits`
`  ├── Issues`
`  └── Pull Requests`
`       ├── Proposed Commits`
`       ├── Reviews`
`       │    └── Review Decisions`
`       ├── Review Comments`
`       ├── Status Checks`
`       └── Target Branch Protection`
`              └── Merge Eligibility`

A repository is the remote project boundary. A branch identifies an independent line of development. Commits represent immutable changes. A Pull Request connects a source branch with a target branch and provides the collaboration boundary for evaluating those changes.

## Remote Repository Operations

### Clone

Cloning creates a local working copy based on the remote repository's recorded branches and commits.

The Python, JavaScript, C++17, and Java 17 implementations copy branch state into a separate repository object. This distinguishes cloning from simply creating a new empty repository.

The model preserves:

- Branch names
- Commit history
- Protected-branch state
- Protection policies

A real Git clone also establishes remote-tracking information. The educational model focuses on the repository and branch state required to reason about synchronization.

### Push

Push transfers local branch changes toward a remote repository.

The implementations explicitly test protected-branch behavior. A direct push to `main` is rejected when branch protection does not permit direct pushes.

This creates an important distinction:

`Local commit → Push → Remote branch`

is different from:

`Local commit → Pull Request → Review → Approval → Protected merge`

A protected branch can therefore accept changes through an approved Pull Request while rejecting an unauthorized direct push.

### Pull

Pull synchronizes a local branch with the remote branch state.

The implementations use explicit branch replacement to model the resulting synchronization state. This keeps the example focused on the relationship between local and remote repository state rather than implementing Git's complete object-transfer and merge machinery.

A real Git pull can involve fetch plus merge or rebase. The simplified model represents the resulting branch state.

### Branches and Commits

The feature branch is created from `main` and receives additional commits.

The example history is conceptually:

`main: a1`

`feature/remote-workflow: a1 → b1 → b2`

The Pull Request proposes the feature branch changes against `main`.

This makes source and target branch responsibilities explicit:

| Element | Example | Role |
|---|---|---|
| Remote repository | `secure-service` | Shared project |
| Target branch | `main` | Protected integration branch |
| Source branch | `feature/remote-workflow` | Proposed change line |
| Base commit | `a1` | Common starting point |
| Feature commits | `b1`, `b2` | Proposed changes |

## README Workflow

The repository README is represented as part of the repository's documentation workflow.

The implementations treat README changes as ordinary repository changes rather than a separate repository mechanism. A README can therefore be:

- Created in the repository
- Modified on a feature branch
- Included in a commit
- Proposed through a Pull Request
- Reviewed through inline comments
- Approved by eligible reviewers
- Merged into the protected target branch

This reflects an important GitHub workflow principle: documentation changes can use the same source-control and governance mechanisms as application code.

## Issues

Issues provide a separate tracking mechanism for work, defects, questions, and documentation requirements.

The examples create an issue for clarifying repository synchronization behavior.

An issue is not itself a Pull Request.

| Mechanism | Purpose |
|---|---|
| Issue | Tracks work, defect, question, or discussion |
| Commit | Records a repository change |
| Branch | Isolates a line of development |
| Pull Request | Proposes branch changes for integration |
| Review | Evaluates proposed changes |
| Approval | Records an eligible review decision |
| Branch Protection | Enforces target-branch conditions |

The Python, JavaScript, and PostgreSQL models represent issue creation explicitly.

## Pull Requests

A Pull Request contains a source branch, target branch, author, proposed commits, review activity, status checks, and merge state.

The lifecycle modeled by the implementations is:

`Draft → Open → Review → Checks → Approval → Eligible → Merged`

A Pull Request may also be:

`Open → Closed`

A closed Pull Request is not automatically a merged Pull Request.

### Source and Target Branches

The source branch contains the proposed work.

The target branch identifies where the work is intended to be integrated.

The source and target branches must be different. The implementations validate this condition.

### Changesets and Commits

A Pull Request is associated with commits from its source branch. The commits provide the actual repository changes being proposed.

The models retain commit identity through a SHA-like identifier and preserve author and commit-message information.

### Draft Pull Requests

The Python and JavaScript models explicitly support draft Pull Requests.

A draft is not considered mergeable until it is published as an active Pull Request.

The state distinction prevents an unfinished proposal from satisfying ordinary merge conditions.

### Base-Branch Synchronization

The Pull Request records the target branch's head at creation.

The Python implementation provides explicit synchronization behavior and can invalidate stale review decisions when the target branch advances.

This is important because review decisions can become stale after the reviewed branch relationship changes.

### Merge Conflicts

The source implementations do not attempt to implement Git's complete three-way merge algorithm. Instead, branch synchronization and merge eligibility are represented separately.

A real merge conflict occurs when Git cannot automatically reconcile changes. The governance engine should treat an unresolved conflict as a condition preventing safe integration rather than pretending that approval alone resolves it.

### Reopening and Closing

A Pull Request can be closed without merging. Reopening requires the workflow state to return to an active review state.

The domain model keeps merge and closure distinct because a merged Pull Request represents completed integration while a closed Pull Request may represent abandoned or superseded work.

## Code Review

Code Review evaluates the proposed changes rather than defining the repository itself.

A review may contain:

- Reviewer identity
- Review state
- Inline comments
- Review timestamp
- Requested changes
- Approval

The review state model contains:

| State | Meaning |
|---|---|
| `commented` | Reviewer provided feedback without an approval decision |
| `approved` | Reviewer accepts the proposed changes |
| `changes_requested` | Reviewer requires changes before integration |
| `dismissed` | Existing review decision is no longer active |

### Inline Comments

The implementations associate comments with:

- Reviewer
- File
- Line
- Comment body
- Resolution state

An unresolved review conversation can prevent merging when the target branch requires conversation resolution.

This is different from approval. A reviewer can approve a Pull Request while a separate unresolved discussion still prevents merge eligibility under the repository policy.

### Review Quality and Scope

The model separates review activity from repository-level enforcement.

Reviewers evaluate the changes. Branch protection determines which review outcomes are required for integration.

A reviewer should not be treated as an unrestricted merge authority merely because they can submit a review.

## Approvals

An approval is a review decision rather than a generic indication that someone interacted with a Pull Request.

The implementations count distinct eligible reviewers whose review state is `approved`.

Self-approval is explicitly rejected.

This produces the rule:

`Eligible approvals = distinct eligible reviewers with an active approval`

The JavaScript, C++, and Java implementations exclude the Pull Request author from approval counting. The PostgreSQL trigger rejects self-approval at database level.

### Required Reviews

A protected branch can require multiple approvals.

The example requires two approvals:

`required reviews = 2`

The example uses Carol and David as reviewers.

If only one eligible reviewer approves, merge eligibility remains false.

### Stale Approvals

The Python model supports dismissal of stale approvals after target-branch synchronization.

This reflects the governance concern that approval should correspond to the reviewed state. When the underlying branch relationship changes, previously recorded approval may no longer represent the current changes.

### Dismissed Approvals

A dismissed approval is not counted as an active approval.

This keeps review history separate from the current approval decision.

## Branch Protection

Branch Protection is the repository-level enforcement layer.

The example protects `main` with:

| Rule | Example |
|---|---|
| Required approvals | 2 |
| Required checks | `tests`, `security-scan` |
| Direct pushes | Blocked |
| Force pushes | Blocked |
| Conversation resolution | Required |
| Stale approval handling | Enabled |
| Linear history | Required |

The protection policy is evaluated against the target branch rather than against the source branch.

### Direct Push Restrictions

A protected branch rejects direct pushes when the policy disallows them.

This prevents a user from bypassing Pull Request governance through:

`Local main → Direct push → Remote main`

The intended path is:

`Feature branch → Pull Request → Review → Approval → Checks → Protected merge`

### Force Push Restrictions

The models store a force-push policy flag.

Force pushing can rewrite branch history, so protected branches commonly restrict this operation. The examples represent the policy even though they do not implement Git's complete object-rewrite mechanism.

### Branch Deletion

Branch protection can be treated as part of repository lifecycle governance. The PostgreSQL schema records branch identity and deletion state, allowing repository logic to distinguish active and deleted branches.

A production system should prevent deletion of the default or protected branch unless an explicit administrative policy permits it.

### Required Status Checks

Status checks represent automated validation.

The example requires:

- `tests`
- `security-scan`

A Pull Request is not eligible when either check is missing or has failed.

This creates a separate validation channel from human review:

`Human review → Approval`

`Automated validation → Status check`

Both can be required by the target branch policy.

### Conversation Resolution

The branch policy can require all review conversations to be resolved before merging.

This prevents a Pull Request from being considered complete merely because enough reviewers approved it.

### Linear History

The policy records a linear-history requirement.

The actual Git graph is outside the simplified simulation, but the governance model keeps the requirement explicit because merge strategy and commit topology affect repository history.

### Administrator and Bypass Behavior

The examples deliberately default to restrictive behavior.

The policy model contains explicit direct-push and force-push controls. A production governance implementation should treat administrator bypass as a separate privileged authorization path rather than silently allowing administrators to bypass normal controls.

## Merge Eligibility

Merge eligibility is calculated from independent conditions.

The general decision structure is:

`Open`
`AND not Draft`
`AND required Approvals`
`AND required Status Checks Passed`
`AND no Blocking Review Decision`
`AND Required Conversations Resolved`
`AND branch policy satisfied`
`= Merge Eligible`

The implementations return failure reasons rather than a single unexplained boolean.

Example failure conditions include:

- Pull Request is not open
- Pull Request is still a draft
- Required approval count is not satisfied
- Required status check is missing
- Required status check has failed
- Reviewer requested changes
- Unresolved review conversations remain
- Direct push is prohibited

This makes the governance engine suitable for debugging and operational reporting.

## Merge Strategies

The models represent three merge strategies:

| Strategy | Modeled behavior |
|---|---|
| Merge | Creates a merge commit |
| Squash | Creates one integration commit representing the Pull Request |
| Rebase | Replays source commits onto the target branch |

The Python, C++, and Java implementations use these strategies in the merge service.

The JavaScript implementation uses the same policy evaluation while exposing the merge operation through an event-driven repository object.

## Python Implementation

The Python implementation models repository behavior using dataclasses and enumerations.

Important mechanisms include:

- `Repository` as the aggregate root
- `Branch` for branch state
- `Commit` as immutable commit data
- `PullRequest` for change proposals
- `Review` and `ReviewComment` for review activity
- `StatusCheck` for automated validation
- `BranchProtection` for target-branch policy
- `merge_eligibility()` for governance evaluation
- `clone_repository()` for remote-to-local cloning
- `push_branch()` for push authorization
- `pull_branch()` for synchronization

The implementation also uses assertions for important workflow invariants and explicitly exercises an unauthorized protected-branch push.

## JavaScript Implementation

The JavaScript implementation uses Node.js standard-library behavior and an event-driven repository model.

`EventEmitter` produces events for:

- Branch creation
- Pull Request creation
- Review submission
- Pull Request merging
- Direct pushes
- Pull completion
- Issue creation

`Map` and `Set` provide efficient lookup and uniqueness handling for branches, status checks, approval identities, and policies.

The implementation uses asynchronous-compatible application structure while keeping the current repository operations in memory and deterministic.

Its policy evaluator returns an object containing both:

- `eligible`
- `reasons`

This makes the model suitable for an interactive repository-management interface.

## C++17 Implementation

The C++ implementation treats repository governance as a strongly typed merge-eligibility engine.

The design uses:

- `enum class` for lifecycle states
- Classes for branches, Pull Requests, and repositories
- STL `map`, `set`, and `vector`
- Explicit eligibility results
- Exceptions for invalid operations
- Value-oriented commit records
- Separate merge strategies

The repository evaluates approvals, status checks, review requests, unresolved conversations, and protected-branch conditions before performing a merge.

This implementation emphasizes deterministic state management and explicit ownership of domain data.

## Java 17 Implementation

The Java implementation models repository governance as an enterprise-oriented domain service.

Java records provide immutable representations for:

- Commits
- Reviews
- Review comments
- Status checks
- Branch protection policies
- Merge evaluation results

The `Repository` class acts as a domain service for:

- Branch management
- Pull Request creation
- Protection configuration
- Merge eligibility
- Merge execution
- Direct-push authorization
- Clone behavior
- Pull synchronization

Custom exceptions distinguish merge failure from security failure.

The explicit state transitions make it possible to extend the model toward a service-oriented repository governance application.

## PostgreSQL Implementation

The PostgreSQL implementation uses a relational model that separates repository objects and governance decisions.

Core tables include:

- `users`
- `repositories`
- `branches`
- `commits`
- `branch_commits`
- `issues`
- `pull_requests`
- `pull_request_commits`
- `reviews`
- `review_comments`
- `status_checks`
- `branch_protection`
- `required_checks`
- `merge_events`

Foreign keys preserve relationships between repository entities.

Unique constraints prevent duplicate repository names, branch names within a repository, commit identifiers within a repository, and duplicate positional relationships.

Check constraints validate values such as:

- Non-empty branch names
- Positive commit positions
- Positive issue numbers
- Non-empty Pull Request titles
- Non-negative required review counts

## Database-Level Governance

The PostgreSQL trigger `prevent_self_approval()` enforces a review rule at the database boundary.

This matters because application-level validation alone can be bypassed by another database client or service.

The `merge_eligibility()` function evaluates:

- Pull Request state
- Required approvals
- Reviewer eligibility
- Required status checks
- Unresolved conversations
- Change-request reviews

The `pull_request_status` view provides reporting-oriented aggregation.

The indexes target common operational lookups:

- Repository branches
- Repository commit identifiers
- Pull Requests by target branch and state
- Reviews by Pull Request and state
- Status checks by Pull Request and state
- Unresolved review comments

## Transactional Merge Workflow

The PostgreSQL script demonstrates a transaction around the final merge recording.

The intended sequence is:

`Validate eligibility`
`→ Record merge event`
`→ Change Pull Request state`
`→ Commit transaction`

If a transactional operation fails, PostgreSQL can roll back the complete unit of work instead of leaving the merge history partially recorded.

## Failure Conditions

The implementations intentionally exercise failure scenarios.

### Unauthorized Protected Push

A direct push to protected `main` is rejected when `allowDirectPush` is false.

### Insufficient Approvals

A Pull Request requiring two approvals remains ineligible when fewer than two distinct eligible reviewers have approved it.

### Unresolved Conversation

A Pull Request can remain blocked even after approvals when a required review conversation has not been resolved.

### Failed Status Check

A required failed or missing status check prevents merging.

### Requested Changes

A review with `changes_requested` creates an explicit blocking condition.

### Self-Approval

The author cannot use their own approval to satisfy the review requirement.

### Invalid Branch Relationship

Creating a Pull Request with identical source and target branches is rejected.

### Invalid Repository State

Unknown branches, duplicate branches, duplicate commits, invalid commit identifiers, and invalid policy values are rejected by the relevant implementations.

## Security Controls

The domain model treats repository governance as an authorization boundary.

Important controls include:

- Protected target branches
- Direct-push restrictions
- Force-push restrictions
- Reviewer eligibility
- Self-approval prevention
- Required status checks
- Required review counts
- Conversation resolution
- Explicit merge eligibility
- Immutable-style commit records
- Database-level constraints
- Database-level self-approval trigger

The controls are complementary rather than interchangeable.

A successful status check does not replace a required approval. An approval does not override branch protection. A Pull Request does not itself guarantee merge eligibility.

## Performance Considerations

The in-memory implementations use hash-based or ordered collections according to language capabilities.

Typical operations are designed around efficient lookup of:

- Branches by name
- Pull Requests by number
- Status checks by name
- Protection policies by target branch
- Approval identities

The PostgreSQL implementation indexes the access paths most relevant to governance queries.

Merge eligibility involves aggregation across reviews, checks, and comments. At larger scale, this evaluation can be optimized through materialized state, carefully designed indexes, or event-derived mergeability data while preserving authoritative repository state.

## Conceptual Distinctions

The complete workflow can be understood as a sequence of distinct responsibilities:

`Commit`
`  ↓`
`Branch`
`  ↓`
`Pull Request`
`  ↓`
`Code Review`
`  ↓`
`Approval Decision`
`  ↓`
`Automated Status Checks`
`  ↓`
`Branch Protection Evaluation`
`  ↓`
`Merge Eligibility`
`  ↓`
`Merge`

Remote synchronization operates around the source-control state:

`Remote Repository`
`  ↓ clone`
`Local Repository`
`  ↓ commit`
`Feature Branch`
`  ↓ push`
`Remote Feature Branch`
`  ↓ Pull Request`
`Governance Workflow`
`  ↓ merge`
`Protected Main Branch`

This separation prevents several common conceptual errors:

- A Pull Request is not an approval.
- A review is not automatically an approval.
- An approval is not branch protection.
- Branch protection is not code review.
- A status check is not a human review.
- An issue is not a Pull Request.
- A clone is not the same operation as a pull.
- A pull does not itself mean that a Pull Request has been merged.
- A protected branch does not necessarily reject every merge; it rejects operations that violate its configured rules.

## Practical Repository Scenario

The five source implementations use a consistent engineering scenario:

1. Alice owns a repository named `secure-service` or its equivalent.
2. `main` contains the initial commit.
3. `main` is protected.
4. Bob clones the repository.
5. Bob creates a feature branch.
6. Bob adds documentation-oriented commits covering remote repository operations.
7. The feature branch becomes the source of a Pull Request.
8. Carol and David review the Pull Request.
9. Both provide approvals.
10. Automated tests and a security scan pass.
11. A review conversation is resolved.
12. Branch protection evaluates the combined conditions.
13. The Pull Request becomes merge eligible.
14. The Pull Request is merged using a controlled strategy.
15. A direct protected-branch push is attempted and rejected.
16. The local repository pulls the resulting remote state.

This scenario connects repository synchronization with collaborative governance without treating the mechanisms as identical.

## Implementation Comparison

| Implementation | Primary perspective | Key mechanisms |
|---|---|---|
| Python | Repository workflow simulation | Dataclasses, enums, validation, synchronization, merge evaluation |
| JavaScript | Event-driven repository model | `EventEmitter`, `Map`, `Set`, policy evaluation, events |
| C++17 | Governance and merge engine | Strong typing, STL containers, explicit eligibility results |
| Java 17 | Enterprise domain model | Records, domain services, immutable values, policies, exceptions |
| PostgreSQL | Persistent relational governance model | Constraints, indexes, triggers, functions, views, transactions |

## Limitations

The implementations are governance and learning models rather than implementations of the complete Git or GitHub protocol.

They intentionally do not reproduce:

- Git object storage
- Pack files
- Network authentication protocols
- Full three-way merge algorithms
- Complete merge-conflict detection
- GitHub's complete REST or GraphQL API
- Webhook delivery guarantees
- GitHub organization-level permission inheritance
- CODEOWNERS evaluation
- Complete administrator bypass auditing
- Full Git commit graph topology
- Distributed synchronization protocols

The simplified models preserve the relationships required to understand repository operations and governance while keeping the state transitions inspectable.

## Repository Governance State

The central decision can be represented as:

`Proposed Changes`
`        +`
`Source Branch State`
`        +`
`Review Decisions`
`        +`
`Approval Requirements`
`        +`
`Automated Checks`
`        +`
`Review Conversation State`
`        +`
`Target Branch Protection`
`        ↓`
`Merge Eligibility`
`        ↓`
`Integration`

This structure keeps repository synchronization, collaboration, review, approval, and enforcement as separate mechanisms that cooperate to produce a controlled merge workflow.
