# Collaboration with Git

## Scope

This module models repository collaboration as a controlled process for proposing, evaluating, and integrating source-code changes. It covers four distinct mechanisms:

| Mechanism | Main responsibility | Primary result |
|---|---|---|
| Pull Request | Propose and track a changeset between branches | A reviewable change proposal |
| Code Review | Evaluate correctness, maintainability, and risk | Review comments and review decisions |
| Approvals | Record eligible reviewers' decisions | Evidence that review requirements have been satisfied |
| Branch Protection | Enforce repository-level conditions | A controlled decision about whether a merge is permitted |

These mechanisms are related but not interchangeable. A Pull Request does not automatically establish that its changes are correct. A review decision does not itself guarantee permission to merge. An approval is one input to repository governance. Branch protection evaluates the configured requirements before allowing a protected branch to change.

The implementations use an illustrative payments and enterprise-orders repository. They are executable workflow and governance models, not replacements for an actual Git implementation or a hosting platform.

## Repository and branch model

A Git repository contains commit history and references to commits. A branch is a movable reference identifying a commit. A commit records a snapshot of repository content and references its parent commit or commits.

A typical development workflow is:

    main
      |
      +---- feature/payment-validation
      |          |
      |          +---- commit A
      |          +---- commit B
      |          |
      |          +---- Pull Request targeting main
      |                     |
      |                     +---- Code Review
      |                     +---- Approvals
      |                     +---- Status Checks
      |                     +---- Merge Eligibility
      |                                |
      +--------------------------------+---- merge result

The feature branch and target branch remain separate while the proposal is being evaluated. Commits added to the feature branch change its head. Commits added to the target branch change the target's head. The Pull Request records the source revision being proposed and the target revision against which that proposal is evaluated.

A changeset describes the differences between the relevant branch snapshots. It is not itself a branch and does not replace either branch's commit history.

## Pull Requests

A Pull Request (PR) provides the workflow for proposing changes from a source branch into a target branch. It groups the proposed changes, commit history, discussion, review requests, automated results, and eventual merge decision.

### Pull Request lifecycle

The implementations represent four states:

| State | Meaning | Permitted transitions |
|---|---|---|
| Draft | Proposal is being prepared and is not ready for full review | Open or closed |
| Open | Proposal is available for review and governance evaluation | Closed or merged |
| Closed | Proposal has been closed without merging | Reopened |
| Merged | Proposal has been integrated into the target branch | Terminal state |

A draft Pull Request makes ongoing work visible without treating it as ready for approval. Marking it ready changes the lifecycle state to open. Closing a Pull Request records that the proposal is not proceeding. Reopening a closed Pull Request restores it to an active state, but does not automatically make earlier reviews or checks current.

A merged Pull Request is terminal in these implementations. A merged proposal cannot be reopened as an ordinary open proposal.

### Branch references and changesets

The source branch identifies the proposed work. The target branch identifies the branch that will receive the work. The proposed changeset is calculated from the relevant base snapshot and source snapshot.

The distinction is important:

- Source branch state is the actual current state of the feature branch.
- Target branch state is the actual current state of the destination branch.
- Proposed changes are the differences presented for integration.
- The Pull Request records the specific source and base revisions used for evaluation.

A proposal can become stale even when the visible changeset appears unchanged. For example, another contributor can update the target branch after the Pull Request was opened. The source branch must then incorporate or otherwise account for the newer target state before the model considers the proposal synchronized.

The Python and JavaScript implementations retain the target head used at the last synchronization. The C++ and Java implementations compare the recorded target head with the current target branch head. The PostgreSQL schema records `base_sha_at_open`, `base_sha_at_sync`, and `source_head_sha`.

### Synchronizing the base branch

Synchronizing the base branch incorporates newer target-branch changes into the source branch. It does not mean that the proposed feature has already been merged.

The Python and JavaScript tree models compare three snapshots:

1. The previously synchronized base.
2. The current source branch.
3. The current target branch.

A conflict is identified when both source and target changed the same path differently from the previous base. A conflict-free synchronization applies target-side changes to the source tree and records the new target head.

For example, if both branches modify `src/payment.py` differently, an automatic synchronization cannot safely select one version. The conflict must be resolved before the proposal can be considered synchronized.

After a successful synchronization, the source head changes. Approvals and status checks tied to the previous source head are therefore stale.

### Merge strategies

The three merge strategies have different history behavior:

| Strategy | Resulting history | Main consideration |
|---|---|---|
| Merge commit | Creates a commit with both source and target as parents | Preserves branch integration history but introduces a merge commit |
| Squash | Combines the proposed changes into a single commit on the target | Produces a compact target history |
| Rebase | Replays proposed commits on top of the current target history | Produces linear history when replay succeeds |

A repository policy can permit or prohibit individual merge strategies. A linear-history requirement is incompatible with a merge-commit strategy because that strategy introduces a two-parent merge commit.

The sample implementations simplify some Git mechanics. The Python model creates a single resulting commit for squash and rebase rather than reconstructing every rebased commit. The C++ and Java models simulate resulting branch state and governance decisions rather than creating Git objects. The JavaScript model creates deterministic SHA-256 identifiers for its in-memory snapshots. The SQL implementation uses deterministic 40-character identifiers for relational examples, not actual Git object hashes.

### Closing, reopening, and merge conflicts

Closing a Pull Request stops the proposal from progressing through the normal merge path. Reopening restores the proposal to an active state, subject to current branch state and policy evaluation.

A merge conflict is different from an unsuccessful review. A review disagreement concerns the quality or acceptability of a proposed change. A merge conflict concerns incompatible changes to repository content or history.

The source and target branches may continue to advance while a Pull Request is open. Therefore, merge eligibility must be evaluated against current branch state rather than inferred from the state that existed when the proposal was created.

## Code Review

Code Review evaluates the proposed changes. It is a technical examination of the changeset, not the repository-level mechanism that controls whether a protected branch may be updated.

Reviewers inspect whether the implementation is correct, understandable, maintainable, secure, adequately tested, and consistent with the repository's technical constraints.

### Review mechanics

A review can contain inline comments associated with a file path and line number. Comments may identify incorrect behavior, missing validation, security concerns, unclear logic, or missing tests.

The implementations represent review events using these states:

| Review state | Interpretation |
|---|---|
| Commented | Feedback has been recorded without approving or requesting changes |
| Approved | The reviewer accepts the reviewed revision |
| Changes requested | The reviewer identifies changes that should be addressed |
| Dismissed | A previous review decision is no longer active |

Review discussions group related comments into threads. A thread remains unresolved until an authorized participant marks the discussion as resolved. Resolution records the state of the conversation; it does not necessarily prove that the underlying code has been corrected.

### Review criteria

A useful review examines the scope of the proposal and the risks introduced by the changes. Common criteria include:

- Functional correctness and expected behavior.
- Input validation, exception handling, and boundary conditions.
- Authentication, authorization, and data-protection controls.
- Error handling and operational logging.
- Performance implications and resource usage.
- Test coverage and regression risk.
- Consistency with existing interfaces and architectural decisions.

Review scope should match the proposed changes. Reviewers should distinguish blocking defects from optional improvements. A review that expands into unrelated refactoring can delay the proposal without improving its central objective.

### Reviewer responsibilities and failure modes

Reviewers should inspect the exact revision under consideration, provide actionable comments, distinguish observations from blocking defects, and update their decision when the source changes materially.

Common review failures include:

- Approving without inspecting the complete relevant changeset.
- Treating an old approval as evidence about a newer revision.
- Failing to identify unresolved blocking discussions.
- Recording vague comments that do not describe the problem.
- Reviewing code outside the proposal's scope while missing critical changes inside it.
- Assuming that a successful review automatically authorizes a merge.

A review is a decision and discussion record. Repository merge enforcement is a separate responsibility.

## Approvals

An approval is a review decision indicating that an eligible reviewer accepts a particular proposed revision. Its meaning depends on the revision reviewed, the reviewer's eligibility, and the repository's approval policy.

### Approval semantics

In these implementations, an approval is associated with the source head that the reviewer inspected. The approval count includes the latest eligible review event for each reviewer when that event is an approval for the current source head.

This avoids counting multiple approvals from one person as separate approvals. It also prevents an older approval from being treated as current after the source branch changes.

An approval may cease to contribute to merge eligibility when:

- The source head changes after the review.
- The approval is dismissed.
- The reviewer's repository access is removed.
- The reviewer's account becomes inactive.
- The reviewer is not eligible under the configured policy.
- A later review event from that reviewer replaces the earlier approval.

The sample implementations model a new review event as superseding the reviewer's previous decision. Dismissal is represented as a later review event rather than deletion of historical evidence.

### Eligible reviewers

A reviewer must have active repository access and permission to review. The reviewer cannot approve their own Pull Request. The policy may further restrict eligible reviewers by role.

The PostgreSQL model separates repository membership, permission to review, administrative status, and eligible access roles. This allows a repository to distinguish a viewer from a developer, maintainer, or administrator.

### Required reviews and merge eligibility

Approval requirements are repository policy settings. A requirement might specify two eligible approvals before a protected branch can be updated.

Approval requirements do not independently create merge permission. They contribute one condition to the overall merge-eligibility decision.

For example, a proposal might have two current approvals but still be ineligible because:

- A required security check has failed.
- A review conversation remains unresolved.
- The target branch has advanced.
- The Pull Request is still a draft.
- The requested merge strategy violates branch policy.

Stale and dismissed approvals must be excluded from the current approval count. This is why approval evaluation is tied to the exact proposed source head.

## Branch Protection

Branch Protection is repository-level governance. It defines conditions that must be satisfied before changes can be integrated into a protected branch.

A protected branch can represent a production, release, or shared integration branch. Protection settings reduce the risk of uncontrolled changes to important repository references.

### Repository governance controls

| Control | Purpose |
|---|---|
| Required Pull Requests | Prevent changes from bypassing the proposal workflow |
| Required reviews | Require a specified number of eligible approval decisions |
| Required status checks | Require named automated checks to pass |
| Direct-push restrictions | Prevent ordinary direct updates to the protected branch |
| Force-push restrictions | Prevent non-fast-forward ref replacement |
| Branch-deletion restrictions | Prevent removal of an important branch |
| Conversation resolution | Require review discussions to be resolved |
| Linear-history requirement | Reject merge strategies that introduce merge commits |
| Merge-method restrictions | Limit how approved changes are integrated |
| Administrator bypass | Permit explicitly authorized administrators to bypass selected policy checks |

These controls must be configured deliberately. A policy that requires reviews but has no eligible reviewers can make a branch difficult or impossible to update. A policy that requires a status check with an inconsistent name can block every proposal.

### Required status checks

Automated checks are associated with a specific source revision. A passing test result for one commit does not prove that a later commit also passes.

A check may represent unit tests, integration tests, static analysis, dependency auditing, security scanning, or another automated control.

The Python, JavaScript, C++ and Java implementations associate checks with the current source head. PostgreSQL enforces uniqueness for a Pull Request, source head, and check name. The eligibility function searches for a passing result matching the exact proposed head.

Missing, pending, failed, and cancelled checks are not equivalent to passing checks. Each required check must be evaluated independently.

### Direct pushes and force pushes

A direct push updates a branch without passing through the Pull Request workflow. A force push can replace a branch reference with a non-fast-forward revision, potentially removing previously reachable commits from that branch's visible history.

Branch protection can prohibit both operations. The PostgreSQL implementation provides a validated direct-push function and a trigger that prevents ordinary SQL updates from changing a protected branch head.

A production implementation must also consider commit ancestry, authorization, concurrent updates, branch deletion, and auditability. The SQL example checks ancestry for non-force pushes using a recursive query over stored commit parents.

### Administrator and bypass behavior

An administrator bypass is an explicit governance exception. It should not be assumed to exist merely because a user has administrative access.

The Python, JavaScript, C++ and Java policies represent bypass as a separate permission. The PostgreSQL implementation requires both administrator membership and a policy that enables bypass.

In these educational models, bypass applies to selected review, check, discussion, and merge-method conditions. Pull Request state and branch synchronization remain mandatory. Real hosting platforms can apply different bypass semantics depending on their configuration.

## Merge eligibility

Merge eligibility combines independent conditions. It is not a review state and is not another name for approval.

The models evaluate these categories:

| Category | Evaluation |
|---|---|
| Pull Request lifecycle | Is the proposal open and ready? |
| Source state | Does the recorded source head match the actual source branch? |
| Target state | Has the target remained at the last synchronized revision? |
| Reviewer decisions | Are enough current approvals present? |
| Review policy | Is there a current eligible request for changes? |
| Automated validation | Have all required checks passed on the proposed head? |
| Discussion state | Are required review conversations resolved? |
| Merge policy | Is the selected merge strategy permitted? |
| Repository authorization | Is the actor permitted to perform the merge? |

The decision should provide reasons for rejection rather than a single unexplained failure flag. This helps contributors identify the exact conditions that need attention.

## Implementation architecture

### Python: repository workflow simulation

The Python implementation uses dataclasses and enumerations to represent commits, branches, reviewers, review events, discussions, checks, policies, and Pull Requests.

Its `Repository` class manages the workflow:

- Creates branches and commits.
- Opens, closes, reopens, and marks Pull Requests ready.
- Calculates a proposed changeset.
- Synchronizes the source branch with a newer target revision.
- Detects conflicting file changes.
- Records review and status-check events.
- Calculates current eligible approvals.
- Evaluates merge eligibility.
- Produces a merge result or rejects the operation.

The tree representation uses path-to-content dictionaries. Commit IDs are calculated using SHA-256 over the parent identifiers, message, and normalized tree. The model is deterministic and self-contained, but it does not implement Git's object database, index, pack files, transport protocols, or complete merge algorithms.

### JavaScript: event-driven governance

The JavaScript implementation uses Node.js standard-library capabilities, including `EventEmitter` and `crypto`.

It records lifecycle, review, discussion, status-check, and branch events in an event log. Event listeners can observe changes without coupling every consumer to the method that initiated the change.

A `Map` stores branch, review, check, and Pull Request state. A `Set` stores required checks and reviewer roles. Review decisions are retained as events, while a separate map identifies each reviewer's latest decision.

Merge evaluation is asynchronous. Required checks are evaluated concurrently with `Promise.all`, and all checks remain associated with the current source head.

The event log is an in-memory audit representation. It is not a durable event store, and the example does not provide distributed event delivery, retries, transactional message handling, or remote repository synchronization.

### C++17: governance and merge-eligibility engine

The C++ implementation uses domain structs and enumerations to represent repository governance information. The `GovernanceEngine` centralizes validation, reviewer eligibility, latest-review selection, status-check evaluation, and merge decisions.

It uses unordered maps for entity lookup, vectors for review and check histories, and sets for required status checks. Latest reviews are selected by review sequence, preventing superseded approvals from being counted.

The engine returns a `MergeDecision` containing eligibility, approval count, and failure reasons. A merge operation first evaluates the decision and only then updates the target branch state.

The implementation prioritizes explicit domain boundaries and deterministic policy evaluation. Its commit identifiers are simulation values rather than real Git hashes. The engine does not implement file-level conflict resolution or a Git object database.

### Java 17: enterprise repository governance

The Java implementation uses records for immutable domain values and service classes for controlled state transitions.

`BranchProtectionPolicy` represents repository governance settings. `PullRequest` owns lifecycle, reviews, status checks, and discussion threads. `RepositoryService` manages repositories, branch state, reviewer eligibility, and merge operations.

The implementation uses:

- Records for commit, reviewer, review, check, thread, and policy data.
- Enums for lifecycle, review, check, and merge states.
- Collections for repository entities and event histories.
- Streams for latest-review selection and approval counting.
- An `AtomicLong` for unique in-process identifiers.
- A custom exception for governance failures.

The service distinguishes a current approval from a historical approval. It also checks reviewer roles against the configured eligibility policy. The example is a single-process domain model; a production enterprise service would require durable persistence, concurrent-update controls, authentication, authorization, and integration with an actual Git hosting service.

### PostgreSQL: relational workflow and governance

The SQL implementation models the repository domain in a dedicated `git_collab` schema.

| Database object | Responsibility |
|---|---|
| `repositories` | Repository identity and settings |
| `users` | User identities |
| `repository_members` | Repository roles and reviewer permissions |
| `commits` | Commit identifiers and parent relationships |
| `branches` | Branch references and protected-branch state |
| `pull_requests` | Proposed changesets and lifecycle |
| `reviews` | Review decisions against a specific source head |
| `review_threads` | Discussion state and resolution |
| `review_comments` | Individual review comments |
| `status_checks` | Automated results tied to a source head |
| `branch_protection_policies` | Repository-level merge restrictions |
| `approval_requirements` | Required approval count and reviewer eligibility |

Primary keys and foreign keys preserve identity and relationships. Check constraints restrict valid workflow states, role values, merge methods, review states, and status-check outcomes.

Indexes support common lookup patterns, including Pull Requests by target and state, reviews by reviewer and submission time, unresolved discussions, and status checks by source head.

The `pull_request_dashboard` view aggregates current approval counts, unresolved discussion counts, and status-check information.

The `merge_eligibility` function returns separate results for each governance rule. `merge_pull_request` evaluates those rules before creating the modeled merge commit and updating the target branch. The `process_pull_request_merge` procedure provides a transaction-oriented entry point.

Triggers validate Pull Request branch ownership, reviewer eligibility, lifecycle transitions, protected branch updates, and branch deletion. Transaction-local authorization flags allow the validated merge operation to update the protected target branch while blocking ordinary updates.

The database stores a simplified representation of commit history. It does not reproduce Git tree objects, blob objects, remote transport, or the full semantics of Git merge and rebase operations.

## Edge cases and operational considerations

### Stale approvals

An approval is meaningful only for the revision reviewed. A source branch update changes the proposed revision and invalidates the current approval count for the previous head. The historical review remains available for audit purposes, but it cannot satisfy the current approval requirement.

### Stale status checks

Automated results must match the proposed source revision. A check result attached to an earlier revision cannot validate newly added source commits.

### Unresolved discussions

A discussion can remain unresolved even when a reviewer has approved the Pull Request. Whether unresolved discussions block merging is a separate repository policy setting.

### Target-branch advancement

A target branch can advance while a proposal remains open. The proposal must be synchronized or otherwise validated against the updated target before merging. A successful review of the source branch does not resolve target-branch synchronization.

### Reviewer eligibility changes

A review event can remain in history after a reviewer loses repository access. Merge evaluation should use the current membership and policy state rather than assuming that historical permission remains valid.

### Concurrent updates

A real repository service must account for race conditions between eligibility evaluation and merge execution. For example, the target branch could advance immediately after a check succeeds. A production merge service should use atomic ref updates, transaction or compare-and-swap semantics, and a final revalidation step.

### Security and auditability

Repository governance should protect credentials, restrict administrative access, log policy changes, validate webhook authenticity, and retain review and merge history.

A status check should be trusted only when its result comes from an authorized integration and is bound to the correct repository and source revision. User-supplied check results must not be treated as equivalent to results produced by trusted automation.

The examples provide policy and state validation but do not implement identity federation, signed webhook verification, secret storage, distributed locks, or a complete permissions service.

## Execution and validation

The five implementations are independent and can be tested separately.

| File | Runtime | Execution |
|---|---|---|
| Python | Python 3.10+ | Run the script directly |
| JavaScript | Node.js 18+ | Run the file with Node.js |
| C++17 | C++17 compiler | Compile as a C++17 program and execute |
| Java | Java 17 | Compile `Main.java` and execute `Main` |
| PostgreSQL | PostgreSQL 14+ | Execute the SQL script in a database where schema creation is permitted |

The sample workflows demonstrate an initially eligible proposal, stale approval and check states after source advancement, renewed approval and validation, successful merge processing, and rejected operations involving protected branches or ineligible reviewers.

The implementations share the same governance principles but use different engineering approaches: an in-memory repository simulator, an event-driven service, a C++ policy engine, a Java enterprise domain service, and a relational workflow with database-enforced integrity.
