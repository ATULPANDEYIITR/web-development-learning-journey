# Asynchronous JavaScript for Repository Governance Workflows

This project uses asynchronous JavaScript as the primary technical subject while applying it to a realistic repository-governance workflow. The examples model Pull Requests, Code Review, Approvals, and Branch Protection as distinct mechanisms.

The central asynchronous problem is practical: repository operations do not complete at the same time. A Pull Request can receive review events while CI checks are running, timers can schedule follow-up work, and independent status checks can finish in different event-loop turns. Merge eligibility must therefore be evaluated only after the required asynchronous work has reached a valid state.

## Governance Model

The four governance concepts have different responsibilities.

| Area | Responsibility | Modelled mechanism |
|---|---|---|
| Pull Request | Proposes a changeset from a source branch toward a target branch | PR lifecycle, commits, draft state, synchronization, merge state |
| Code Review | Evaluates the proposed changes | Review states, comments, conversations, reviewer actions |
| Approvals | Records qualifying review decisions | Current-head approval tracking and stale approval invalidation |
| Branch Protection | Enforces repository-level merge conditions | Required reviews, required checks, conversation rules, history restrictions |

The relationship can be represented as:

`Source Branch → Pull Request → Code Review → Approval Decisions → Branch Protection → Merge`

Asynchronous execution sits underneath this workflow. CI checks and repository events are operations whose completion is not guaranteed to occur in source-code order.

## JavaScript Event Loop Model

JavaScript normally executes application code on a single main thread. Synchronous statements execute on the current call stack. Asynchronous APIs arrange later work for subsequent event-loop processing.

The JavaScript implementation deliberately demonstrates several different mechanisms:

- `setTimeout()` schedules a callback for a future event-loop turn.
- A Promise continuation is placed in the microtask queue.
- `Promise` objects represent future completion.
- `async` and `await` provide structured syntax for consuming Promise results.
- `Promise.all()` waits for multiple independent asynchronous operations.
- `EventEmitter` models domain events without forcing consumers to poll object state.

A simplified execution relationship is:

`Call Stack → asynchronous API → queued callback / Promise continuation → Event Loop → callback execution`

The important distinction is that `setTimeout(fn, 0)` does not mean that `fn` executes immediately. It schedules the callback after the current synchronous work has completed and after eligible higher-priority microtasks have been processed.

The example deliberately prints synchronous messages, a Promise continuation, and a timer callback so that this ordering can be observed.

## Pull Request Lifecycle

The Pull Request model contains an explicit lifecycle:

`DRAFT → OPEN → MERGED`

A Pull Request may also become `CLOSED`.

A draft does not represent a mergeable proposal. Calling `markReady()` changes the draft into an open Pull Request. The source branch supplies commits, while the target branch identifies the branch governed by repository policy.

The implementation validates:

- source and target branches must differ;
- a Pull Request must contain at least one commit;
- reviews require an open Pull Request;
- merge operations require the open state;
- a Pull Request cannot be treated as mergeable merely because it contains commits.

Base-branch synchronization is represented by changing the Pull Request head. A new head matters because approvals and status checks are associated with a particular changeset.

## Changesets and Stale Approvals

Reviews are attached to the commit SHA that was reviewed.

This is essential for approval correctness. If a reviewer approves commit `c101` and the Pull Request later receives `c102`, the approval may no longer represent an evaluation of the current changeset.

The implementations model this by dismissing approvals when a new commit is added.

The state transition is:

`OPEN + approved(c101) → new commit(c102) → previous approval dismissed`

This prevents a repository from treating an approval for an older changeset as an approval for the current one.

The PostgreSQL implementation enforces the same concept through a trigger. Updating the Pull Request head causes approvals associated with an older head to become dismissed.

## Code Review

Code Review is deliberately separated from Pull Request mechanics.

A Pull Request transports a proposed changeset. A review evaluates it.

The JavaScript model supports:

- commented reviews;
- requested changes;
- approvals;
- dismissed reviews;
- reviewer identity;
- review comments;
- unresolved conversations.

An inline comment can identify a file and line in the SQL representation. Its `resolved` state is separate from the review state because resolving a discussion does not automatically mean that the reviewer has approved the complete changeset.

A useful distinction is:

`Comment → discussion about a change`

`Changes Requested → reviewer requires modification`

`Approved → reviewer accepts the current head under the review policy`

These states have different governance meanings and are not interchangeable.

## Approval Semantics

An approval is considered current only when:

- the reviewer is active;
- the reviewer is eligible to approve;
- the review state is `APPROVED`;
- the reviewed commit equals the current Pull Request head.

The C++ and Java implementations calculate a set of unique current approvers. This avoids counting multiple approvals from the same reviewer as multiple independent approvals.

The SQL model applies the same rule through a filtered aggregation.

This produces an important distinction between review activity and approval eligibility. A Pull Request can have many historical reviews while still having insufficient current approvals.

## Reviewer Eligibility

Reviewer identity is represented explicitly rather than as an arbitrary string attached to a merge decision.

The relational model stores:

- reviewer account;
- active status;
- approval eligibility.

This allows the merge calculation to exclude inactive or ineligible reviewers.

The policy therefore evaluates:

`Eligible current approvers >= Required approvals`

rather than simply counting every review row.

This prevents historical or invalid reviewer records from satisfying a branch-protection requirement.

## Branch Protection

Branch Protection is the repository-level enforcement layer.

The model supports rules for:

- protected branches;
- required reviews;
- required status checks;
- direct-push restrictions;
- force-push restrictions;
- branch-deletion restrictions;
- required conversation resolution;
- linear-history requirements;
- administrator bypass policy.

The implementations do not treat these controls as review decisions. A reviewer can approve a Pull Request while branch protection still prevents merging because a required CI check has failed or an unresolved discussion remains.

This separation is central to the architecture:

`Review approval = reviewer decision`

`Branch protection = repository policy`

## Status Checks and Asynchronous Execution

Status checks represent independent external work such as tests or security validation.

The JavaScript implementation creates a separate asynchronous operation for each required check:

`unit-tests`
`security-scan`

They are started through Promises and consumed with `Promise.all()`.

This is preferable to unnecessarily serial execution when the checks are independent. If two checks require 100 ms and 150 ms respectively, concurrent scheduling can approach the duration of the slowest operation rather than the sum of both durations, subject to the actual CI infrastructure.

The callback version demonstrates the lower-level pattern:

`runCheck → setTimeout → callback(error, result)`

The Promise wrapper converts that callback API into:

`runCheck → Promise → async/await`

This is a common migration pattern when integrating older callback-based Node.js infrastructure with newer asynchronous application code.

## Failure Handling

The JavaScript implementation uses callback error-first conventions in the callback API:

`callback(error, result)`

The Promise wrapper converts an error into rejection:

`reject(error)`

and successful completion into:

`resolve(result)`

The top-level `main()` function uses `try/catch` through Promise rejection handling.

This prevents asynchronous failures from being mistaken for successful workflow completion.

A governance system should not evaluate a Pull Request as mergeable while a required check is still running or has failed. The model therefore waits for required checks before performing the merge decision.

## Event-Driven Review Activity

`EventEmitter` is used for domain notifications such as:

- Pull Request becoming ready;
- review submission;
- source-branch synchronization;
- conversation activity;
- merge completion.

The event mechanism separates the operation that changes repository state from consumers that react to that state.

For example, submitting a review can emit a `reviewSubmitted` event without requiring the review operation itself to know whether another subsystem needs to update a dashboard, audit log, or notification queue.

Events should not replace authoritative state. The Pull Request and review objects remain the source of truth. Events communicate that something happened.

## C++ Governance Engine

The C++ implementation uses explicit domain types and `std::future`.

`std::async(std::launch::async, ...)` models independently running CI jobs. This is deliberately different from JavaScript's event-loop model. C++ may execute the asynchronous tasks on separate worker threads.

The governance engine waits on the returned futures before calculating merge eligibility.

The implementation also demonstrates stale approvals by attaching each review to a specific commit SHA. Adding a new commit changes the Pull Request head and dismisses previous approvals.

The design emphasizes deterministic merge evaluation:

`status checks complete → current approvals calculated → conversations checked → merge decision`

## Java Enterprise Model

The Java implementation uses domain-oriented types and `CompletableFuture`.

Records are used for immutable value objects such as:

- `Commit`;
- `Review`;
- `BranchProtectionPolicy`.

Mutable domain state is kept in `PullRequest` and `StatusCheck`, where explicit state transitions are required.

`CompletableFuture.supplyAsync()` represents asynchronous CI execution. Multiple futures are combined with `CompletableFuture.allOf()` so the governance service can wait for all required checks before evaluating the merge.

The Java model also introduces an explicit `MergeDecision` object containing both the Boolean result and the reasons for failure. This makes policy failures inspectable instead of reducing them to an unexplained Boolean.

The enterprise workflow is therefore:

`Configure Policy → Create PR → Ready PR → Execute Checks → Review → Resolve Conversations → Evaluate Policy → Merge`

## PostgreSQL Relational Model

The SQL implementation stores governance state relationally.

The primary relationships are:

`repositories → branches`

`repositories → pull_requests`

`pull_requests → pull_request_commits`

`pull_requests → reviews → review_comments`

`pull_requests → status_checks`

`branches → branch_protection_rules`

The schema uses PostgreSQL-specific enum types for Pull Request, review, and status-check states.

Constraints enforce fundamental data integrity:

- unique repository names;
- unique branch names within repositories;
- unique Pull Request numbers within repositories;
- non-negative required review counts;
- valid branch relationships;
- non-empty commit identifiers;
- non-negative unresolved conversation counts;
- valid review dismissal state.

Partial indexing is used for unresolved review comments because unresolved discussions are a specific operational query rather than every historical comment.

## Database-Level Approval Invalidation

The `invalidate_stale_approvals()` trigger demonstrates why approval freshness should not depend entirely on application code.

When a Pull Request head changes, the trigger searches for approvals associated with an older head and dismisses them.

This protects the invariant:

`approved review head = current Pull Request head`

The trigger provides database-level enforcement even if a different application component updates the Pull Request.

## Transactional Workflow

The SQL script uses transactions when changing governance state.

Conversation resolution and Pull Request state are updated within a transaction before merge eligibility is evaluated.

The script also demonstrates a rollback around a simulated head change. This makes it possible to inspect stale-approval behavior without permanently changing the sample dataset.

Transactions are particularly important for repository governance because a merge decision should not be calculated from a partially updated representation of a Pull Request.

## Merge Eligibility

The common merge rule can be expressed as:

`Merge Eligible = Open PR ∧ Required Checks Passed ∧ Current Approvals Sufficient ∧ Conversations Resolved`

Branch-protection configuration determines which conditions are required.

The implementations intentionally do not treat an approval as sufficient by itself.

A Pull Request may be blocked because:

- a required status check has not passed;
- a required status check failed;
- approval count is insufficient;
- approvals belong to an older head;
- a reviewer is inactive;
- a reviewer is not eligible to approve;
- conversations remain unresolved;
- the Pull Request is not open;
- protected-branch restrictions prohibit the operation.

## Merge Strategies and History

Merge behavior is a repository policy concern rather than a review state.

The governance models recognize linear-history requirements as a branch-protection condition. A merge strategy that introduces a prohibited history shape must not be treated as valid merely because the review and CI requirements passed.

A production implementation would connect this rule to actual Git commit ancestry rather than relying on a message-based simulation. The educational implementations keep the domain deterministic without requiring a Git repository or external command execution.

## Merge Conflicts and Base Synchronization

A Pull Request is based on a particular target-branch state. If the target branch advances, the Pull Request may require synchronization before it can safely merge.

The JavaScript and Python workflow models expose source synchronization as an explicit event or operation.

A production governance engine should obtain authoritative Git ancestry information to determine whether a conflict exists. The sample programs intentionally do not pretend that a string comparison can perform a real three-way Git merge.

This is an important limitation: repository governance can enforce merge conditions, but actual merge-conflict detection belongs to Git's object and merge machinery.

## Reopening and Closing Pull Requests

Closing a Pull Request changes its lifecycle state and prevents normal review or merge operations from being treated as active workflow actions.

Reopening is conceptually different from creating a new Pull Request because the original proposal, conversations, reviews, and history may still be relevant.

The examples focus on merge eligibility and use explicit lifecycle validation rather than silently allowing operations on closed or merged objects.

## Performance Characteristics

The JavaScript status checks are initiated concurrently with `Promise.all()`. If independent checks have durations `t1`, `t2`, and `t3`, the idealized elapsed time approaches:

`max(t1, t2, t3)`

rather than:

`t1 + t2 + t3`

The actual result depends on the underlying asynchronous services.

The C++ model uses asynchronous futures, potentially involving worker threads. That introduces different resource costs and scheduling behavior from JavaScript's event-loop approach.

The Java implementation uses a fixed-size executor. This prevents unlimited creation of worker threads but introduces a queue when the workload exceeds executor capacity.

The SQL reporting indexes focus on access paths used by Pull Request state, review freshness, status-check state, and unresolved comments.

## Security Considerations

Repository governance is security-sensitive because an incorrect merge decision can bypass controls intended to protect production code.

The examples therefore treat the following as security-relevant:

- reviewer eligibility;
- stale approval invalidation;
- required status checks;
- protected target branches;
- direct-push restrictions;
- force-push restrictions;
- branch deletion restrictions;
- administrator bypass configuration;
- unresolved review discussions.

Asynchronous execution also introduces a consistency concern. A merge decision must not be made from stale asynchronous results. Status-check results should be associated with the exact commit they evaluated.

The SQL schema explicitly stores `commit_sha` with each status check and review.

## Debugging Asynchronous Workflows

Asynchronous bugs often arise from incorrect assumptions about ordering.

A useful debugging sequence is:

`Identify operation → identify completion signal → identify state mutation → identify dependent operation`

For the status-check workflow:

`Start check → check runs asynchronously → check completes → result recorded → merge eligibility evaluated`

A common error is evaluating merge eligibility immediately after starting a check. The check may still be queued or running.

Another failure is associating a completed result with a newer Pull Request head. Commit identity therefore belongs in the status-check and review records.

## Cross-Language Design Comparison

| Implementation | Asynchronous mechanism | Governance emphasis |
|---|---|---|
| Python | `asyncio`, `await`, `gather` | Workflow simulation and concurrent checks |
| JavaScript | callbacks, timers, Promises, `async/await`, `EventEmitter` | Event loop and event-driven repository activity |
| C++17 | `std::async`, `std::future` | Concurrent governance evaluation and explicit value types |
| Java 17 | `CompletableFuture`, executor service | Enterprise domain model and policy services |
| PostgreSQL | Transactional state and triggers | Persistent integrity and merge-policy evaluation |

The implementations are intentionally not line-for-line translations. Each uses the concurrency and domain-modeling mechanisms that are natural for its environment.

## Practical State Model

A simplified repository workflow is:

`Draft PR`
↓
`Open PR`
↓
`Status Checks Running`
↓
`Code Review`
↓
`Review Decisions`
↓
`Resolve Discussions`
↓
`Current Approvals + Passed Checks`
↓
`Branch Protection Evaluation`
↓
`Merge`

An important property is that these stages are not all strictly sequential internally. Status checks can run concurrently, reviewers can inspect a Pull Request while checks are executing, and event handlers can react to state transitions independently.

The final merge operation remains gated by the repository's authoritative conditions.

## Limitations of the Simulation

The programs model repository governance without connecting to an actual Git hosting service.

They therefore do not implement:

- real Git object negotiation;
- three-way merge algorithms;
- network authentication;
- actual webhook delivery;
- remote CI infrastructure;
- signed commits;
- repository-host-specific permission APIs;
- real branch ancestry computation.

The examples instead provide executable domain behavior around the most important distinction: asynchronous work can happen independently, but merge eligibility must be evaluated against a consistent and current repository state.
