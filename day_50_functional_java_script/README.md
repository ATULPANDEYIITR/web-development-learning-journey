# Functional JavaScript: Pure Functions, Immutability, Higher-Order Functions, and Composition

## Scope

This project uses a repository-development governance scenario to demonstrate functional JavaScript concepts through concrete workflow behavior.

The governance model separates four related mechanisms:

| Area | Responsibility |
|---|---|
| Pull Request | Proposes a changeset from a source branch toward a target branch |
| Code Review | Evaluates the proposed changes through review states and discussions |
| Approvals | Records review decisions that satisfy required-review policy |
| Branch Protection | Enforces repository-level conditions before a merge is permitted |

The implementations deliberately keep these mechanisms distinct. A Pull Request is the workflow object. A review is an evaluation of its changes. An approval is a specific review decision. Branch Protection supplies the repository policy that determines which conditions must be satisfied.

The JavaScript implementation focuses on functional programming rather than simply reproducing an object-oriented repository simulator.

---

## Functional Programming Model

The central data-flow model is:

```text
Immutable repository state
       |
       v
Pure transformation
       |
       v
New immutable state
       |
       v
Pure policy evaluation
       |
       v
Merge eligibility
```

The implementation avoids changing an existing Pull Request in place. Operations such as opening a draft, adding a review, updating a status check, resolving a discussion, synchronizing a branch, and merging return new objects.

This gives the workflow a predictable state-transition model:

```text
DRAFT
  |
  v
OPEN
  |
  +----> CLOSED
  |
  v
MERGED
```

A closed Pull Request can be reopened in a fuller workflow model, while a merged Pull Request is treated as a terminal state for the simulation.

---

## Pure Functions

A pure function has no observable side effects and produces the same result when supplied with the same input.

Examples in the JavaScript implementation include:

- `countApprovals`
- `hasRequestedChanges`
- `requiredChecksPassed`
- `mergeReasons`
- `canMerge`
- `normalizeCommit`
- `meaningfulCommit`
- `commitLabel`

For example, merge eligibility is calculated from the Pull Request and Branch Protection policy rather than being stored as mutable state.

The eligibility function evaluates:

- Pull Request state
- existence of commits
- source and target branches
- synchronization with the base branch
- merge conflicts
- requested changes
- approval count
- required status checks
- unresolved review conversations

This means a Pull Request does not need a mutable `mergeable` flag that could become stale.

---

## Immutability

The JavaScript model uses object spread, array copying, and `Object.freeze()` to prevent accidental mutation.

An operation such as adding a review conceptually performs:

```text
old Pull Request
       |
       +---- existing reviews
       |
       +---- new review
       |
       v
new Pull Request
```

The original value remains available.

This is important for workflow systems because a state transition can otherwise create difficult debugging problems. If an operation mutates an object shared by several parts of an application, historical state and current state can become indistinguishable.

The example also freezes policy, review, status-check, and Pull Request structures after construction.

Immutability does not automatically make every nested JavaScript structure safe. The implementation therefore copies arrays before freezing the containing objects. Production systems with deeper object graphs may require a more systematic immutable-data strategy.

---

## Higher-Order Functions

Higher-order functions accept functions as arguments or return functions.

The JavaScript implementation defines reusable functional operations:

- `map`
- `filter`
- `reduce`
- `pipe`
- `compose`

The repository example uses them to process commits.

A commit pipeline performs:

```text
commits
  |
  v
normalize messages
  |
  v
remove insignificant messages
  |
  v
create human-readable descriptions
```

The important distinction is that the pipeline describes transformations rather than prescribing mutable control flow.

Policy factories are another higher-order-function example.

`approvalPolicy(policy)` returns a function that evaluates a Pull Request against the configured approval requirement. Similar functions are created for status checks and conversation resolution.

These functions can then be combined into a larger policy evaluator.

---

## Composition

Composition combines small functions into a larger operation.

`pipe` applies transformations from left to right:

```text
input
 -> normalize
 -> validate
 -> filter
 -> transform
```

`compose` applies functions from right to left.

This allows repository policies to be represented as combinations of independent predicates instead of one large function containing every rule.

The benefit is separation of concerns. Approval eligibility does not need to know how status checks are evaluated, and status-check evaluation does not need to know how review conversations work.

---

## Pull Request Lifecycle

A Pull Request identifies:

- source branch
- target branch
- commits
- state
- reviews
- status checks
- unresolved conversations
- synchronization state
- merge strategy

A draft Pull Request can be opened before it participates in normal review.

Once open, reviews can be submitted and status checks can be evaluated.

Synchronization with the base branch matters because the proposed changes may become outdated after the target branch changes. A synchronized Pull Request is therefore represented explicitly rather than assuming that the original changeset remains current.

Merge conflicts are also represented separately. A Pull Request may have approvals and successful checks but still be unable to merge because its branches conflict.

Closing a Pull Request is different from rejecting a review. Closing changes the Pull Request lifecycle state. A review requesting changes is a review decision and does not itself close the Pull Request.

---

## Code Review

Code Review evaluates the proposed changes rather than enforcing repository-wide merge policy.

The model supports review states:

| Review state | Meaning |
|---|---|
| `commented` | Reviewer has provided feedback without an approval decision |
| `approved` | Reviewer accepts the changes for the purpose of the review |
| `changes_requested` | Reviewer identifies changes that must be addressed |
| `dismissed` | Existing review decision is no longer active |

Review comments are associated with specific review activity in the SQL model.

A useful review process is concerned with correctness, scope, maintainability, security implications, tests, and compatibility. It should not treat approval as a substitute for technical evaluation.

A Pull Request can therefore contain several conversations while still having insufficient approvals.

---

## Approvals

An approval is a review decision.

The implementation counts approvals independently from ordinary comments. This prevents a comment such as “looks interesting” from accidentally satisfying a required-review rule.

The branch policy defines how many approvals are required.

A production system must also account for reviewer eligibility. Possible policy dimensions include:

- repository membership
- team membership
- ownership rules
- reviewer activity status
- required reviewer groups
- self-approval restrictions
- stale-approval rules
- approval dismissal

The executable examples keep reviewer eligibility simple while the data model separates developers, repository membership, and reviews so that eligibility rules can be expanded without changing the conceptual model.

Stale approvals are an important production concern. If the Pull Request changes after an approval, the approval may no longer represent the exact changes that were evaluated. A real governance system therefore needs a policy for whether approvals remain valid after new commits.

---

## Branch Protection

Branch Protection is repository-level enforcement.

The SQL and application models include policy controls for:

| Policy | Effect |
|---|---|
| Required reviews | Sets the minimum approval count |
| Required checks | Requires specified checks to pass |
| Conversation resolution | Blocks merging while required discussions remain unresolved |
| Linear history | Expresses a history requirement |
| Direct pushes | Controls whether changes can bypass Pull Requests |
| Force pushes | Controls destructive history rewriting |
| Branch deletion | Controls deletion of protected branches |
| Administrator bypass | Represents an explicit governance exception |

Branch Protection is not another name for Code Review.

The relationship is:

```text
Pull Request
    |
    v
Code Review
    |
    v
Approval decisions
    |
    v
Branch Protection policy
    |
    v
Merge eligibility
```

A repository may require two approvals even when three reviewers have commented. The approval count is therefore a policy evaluation rather than a simple measure of review activity.

---

## Merge Eligibility

The merge engine uses a conjunction of independent conditions.

A simplified model is:

```text
OPEN
AND commits exist
AND source is synchronized
AND no conflicts
AND no requested changes
AND required approvals exist
AND required checks pass
AND required conversations are resolved
```

If any required condition fails, the engine returns a blocking reason.

Returning explicit reasons is useful for debugging and operations. A Boolean value alone says that a merge is blocked but does not explain why.

The JavaScript model therefore exposes `mergeReasons` separately from `canMerge`.

This also allows interfaces to display actionable policy failures without duplicating the governance rules.

---

## Python Implementation

The Python program models the workflow with frozen dataclasses and pure transformations.

Important mechanisms include:

- immutable dataclasses
- tuples for immutable collections
- dictionaries for check lookup
- higher-order functions
- `map` and `filter`
- explicit exceptions
- pure merge-policy evaluation
- state-transition functions

`replace()` creates updated dataclass instances rather than modifying the original Pull Request.

The commit pipeline normalizes commit messages, filters insignificant messages, and creates descriptions.

The merge engine returns specific reasons when policy requirements are not satisfied.

---

## JavaScript Implementation

The JavaScript file is the primary functional-programming artifact.

It uses:

- arrow functions
- object spread
- immutable array transformations
- `Object.freeze`
- higher-order functions
- function factories
- `map`
- `filter`
- `reduce`
- `pipe`
- `compose`
- predicate composition

The implementation is event-friendly because each event can be interpreted as a function from one immutable state to another.

For example:

```text
openDraft(pr)
addReview(pr, review)
updateCheck(pr, check)
resolveConversation(pr)
synchronize(pr)
merge(pr, policy)
```

Each operation receives state and returns state.

This style fits event-driven systems because events can be replayed against immutable state transitions.

---

## C++ Implementation

The C++17 implementation uses value semantics to model immutable-style transformations.

The governance engine returns copies of Pull Requests for state transitions instead of exposing uncontrolled mutation.

Functional utilities provide:

- transformation through `functionalMap`
- selection through `functionalFilter`
- pure message normalization

The merge engine uses standard-library algorithms such as `count_if`, `any_of`, `all_of`, and `copy_if`.

The C++ implementation emphasizes deterministic value-based processing and explicit error handling through exceptions.

---

## Java Implementation

The Java 17 implementation uses records for immutable domain values.

The main domain types are:

- `Commit`
- `Review`
- `StatusCheck`
- `BranchProtection`
- `PullRequest`

The `MergeEligibilityService` isolates governance policy from the domain data.

Java Streams provide functional operations for:

- counting approvals
- detecting requested changes
- evaluating status checks
- transforming commit collections
- filtering meaningful commits

`Function` and `Predicate` represent reusable transformations and policy conditions.

The records provide structural immutability for the main workflow objects, while state transitions create new Pull Request instances.

---

## PostgreSQL Model

The SQL implementation treats repository governance as relational state.

The primary entities are:

```text
repositories
    |
    +-- branches
    |
    +-- repository_members
    |
    +-- pull_requests
             |
             +-- pull_request_commits
             |
             +-- reviews
             |      |
             |      +-- review_comments
             |
             +-- status_checks

branches
    |
    +-- branch_protection
    |
    +-- required_status_checks
```

Foreign keys enforce relationships.

Check constraints enforce basic validity such as positive Pull Request numbers and non-negative unresolved-conversation counts.

Indexes target queries that repeatedly evaluate Pull Requests by target branch and state, reviews by Pull Request and state, and status checks by Pull Request.

---

## SQL Merge Evaluation

The `pull_request_merge_eligibility` view uses common table expressions to calculate:

- approval count
- requested-change presence
- required-check count
- passed required-check count
- commit count
- unresolved discussions
- final merge eligibility

This keeps derived eligibility separate from stored workflow state.

The database therefore avoids storing a mutable `mergeable` column that could become stale when reviews or checks change.

The `merge_pull_request` function evaluates the view before changing the Pull Request to `merged`.

The merge operation is executed inside a transaction in the example, demonstrating that governance state changes can be treated as an atomic database operation.

---

## Failure Conditions

The implementations intentionally model several independent failure states.

### Missing approvals

A Pull Request with fewer approvals than required remains blocked.

### Requested changes

A reviewer can explicitly request changes even when another reviewer has approved the Pull Request.

### Failed required check

A failed security or test check prevents merging.

### Unresolved conversation

A required unresolved discussion prevents merging when the policy enables conversation resolution.

### Branch synchronization failure

A Pull Request that is behind the target branch can remain ineligible until synchronized.

### Merge conflicts

Conflict state is independent of approvals and status checks.

### Invalid lifecycle transition

Opening a Pull Request that is not a draft is rejected by the application models.

### Invalid reviewer

Empty reviewer identities are rejected.

### Invalid branch relationship

A Pull Request cannot use the same branch as both source and target.

---

## Stale Approvals and Dismissal

The examples distinguish approval state from branch synchronization, but a production implementation should explicitly connect approval validity to the reviewed changeset.

A robust policy can associate an approval with:

- the commit SHA reviewed
- the Pull Request revision
- the reviewer identity
- the review timestamp

When new commits arrive, the policy can decide whether existing approvals remain valid.

Dismissal should also be represented as a state transition rather than silently deleting review history. Historical review decisions are useful for auditing and governance.

---

## Performance Considerations

The application-level merge checks are designed around linear scans of the relevant review and status-check collections.

For a Pull Request with:

- `R` reviews
- `C` required checks

the core policy evaluation is approximately `O(R + C)`.

The SQL model uses indexes on frequently filtered relationships so that evaluation remains practical as the number of Pull Requests and reviews grows.

Functional transformations allocate new collections. This increases memory usage compared with in-place mutation, but the trade-off is easier reasoning about state and fewer aliasing-related defects.

For very large collections, streaming or lazy evaluation can reduce unnecessary intermediate allocations.

---

## Security and Governance Considerations

Repository governance is security-sensitive because merge permissions can determine which code reaches a protected branch.

Important controls include:

- restricting direct pushes
- restricting force pushes
- requiring trusted reviewers
- requiring successful security checks
- resolving required conversations
- preserving review history
- preventing unauthorized branch deletion
- controlling administrator bypass
- validating reviewer eligibility
- invalidating stale approvals where policy requires it

A functional programming style does not replace access control. Immutability and pure evaluation improve state reasoning, while authorization must still be enforced at the repository and service boundaries.

---

## Relationship Between the Five Implementations

| File | Primary perspective |
|---|---|
| Python | Immutable repository workflow simulation |
| JavaScript | Functional transformations, composition, and policy predicates |
| C++ | Value-oriented governance and merge-eligibility engine |
| Java | Enterprise domain modeling and explicit policy services |
| PostgreSQL | Relational governance state and database-enforced workflow |

The implementations use the same governance concepts but deliberately emphasize different programming models.

The JavaScript implementation is the central artifact for pure functions, immutability, higher-order functions, and composition. The other implementations provide contrasting ways to represent the same repository-governance problem without reducing functional programming to syntax-only examples.
