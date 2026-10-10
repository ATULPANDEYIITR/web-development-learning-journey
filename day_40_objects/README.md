# Object Properties, Methods, Nested Objects, Destructuring, Spread, and Computed Properties

## Scope

Objects combine related data and behavior into a single structure. Understanding how properties are stored, how methods access object state, and how nested references behave is essential when designing maintainable applications, processing API payloads, and managing mutable configuration.

This project examines object behavior in Python, JavaScript, C++, Java, and PostgreSQL. The implementations share a conceptual foundation while demonstrating language-specific approaches to state, copying, dynamic property access, validation, and structured data.

The examples use repository metadata, Pull Requests, code reviews, deployment configurations, and service operations. These scenarios illustrate how objects represent real application entities rather than isolated collections of unrelated values.

## Core concepts

### Properties and methods

A property associates a name with a value or a computed result. A method is behavior associated with an object, typically implemented as a function that reads or changes the object's state.

Python exposes ordinary attributes and supports managed properties through `@property`. JavaScript objects support ordinary properties, getters, setters, and methods. C++ and Java generally express state through class members and expose controlled operations through member functions.

The distinction between stored and computed properties matters when data can change. A repository's full name can be calculated from its owner and repository name. Storing a second, independent full-name field creates a risk that it will become inconsistent with those source values.

Methods also have different access rules across languages. JavaScript's `this` depends on how a function is called, while Python instance methods receive their instance through `self`. C++ and Java member functions operate on an instance through their respective object models.

### Nested objects and references

An object can contain references to other objects. A Pull Request may contain a branch description, review records, status checks, and labels. These nested structures provide a natural representation of related domain data.

A nested object is not necessarily a copy. Assigning a Python reference or JavaScript object property to another variable normally preserves the same underlying object. Mutating that shared object changes what every reference observes.

This behavior differs from the assumption that a new outer object automatically creates a fully independent structure. A shallow copy duplicates only the outer container. Nested dictionaries, lists, and objects can remain shared.

Deep copying recursively duplicates supported mutable structures, although it requires care around custom classes, identity, external resources, and objects that cannot be copied safely. The appropriate strategy depends on whether the application needs shared state, an independent snapshot, or an immutable representation.

### Destructuring and property extraction

Destructuring extracts named values from a structured object. JavaScript supports native object destructuring, including nested patterns, default values, and rest properties. Python supports unpacking sequences and mappings, although dictionary extraction commonly uses explicit key access, `.get()`, or mapping operations.

Destructuring improves readability when the required fields are known. It does not remove the need for validation. An API payload may omit a nested object, provide an unexpected type, or contain an invalid value. Safe extraction establishes sensible defaults where appropriate and validates required fields before using them.

### Spread and copying

JavaScript object spread, written as `{ ...source }`, copies enumerable own properties into a new object. When several objects are spread into one result, later properties replace earlier properties with the same key.

Python dictionary unpacking, written as `{**defaults, **overrides}`, provides similar merge precedence. Python dictionaries also support the union operator on modern Python versions.

Neither operation automatically performs a recursive copy. If a nested `headers` object is shared between the original and merged configuration, changing that nested object may affect both.

`Object.assign()` is another JavaScript mechanism for copying enumerable properties, but it mutates its target. Choosing between a fresh object and a mutated destination should be an explicit design decision.

### Computed properties

A computed property name derives a key from an expression evaluated at runtime. JavaScript uses bracketed expressions in object literals, such as `{ [metricName]: value }`. Python dictionaries use expressions as keys, and attribute names can be accessed dynamically with `getattr()` or changed with `setattr()`.

Computed keys are useful for metric records, configuration maps, dynamically named fields, and property-based transformations. External input must not automatically be treated as a trusted property name. Allowlisting supported fields prevents callers from accessing or modifying unintended attributes.

Computed values should also be distinguished from computed keys. A getter may calculate a value when accessed, whereas a computed key determines the name under which a value is stored.

## Python implementation

The Python script builds domain objects with explicit validation and behavior.

The `Repository` class defines ordinary attributes for identity, managed properties for stars and archival state, a read-only computed full name, and methods that enforce valid state changes. Its dictionary export provides a controlled representation rather than exposing the internal object directly.

The `PullRequest` class contains a nested repository reference, labels, review metadata, and status-check data. Its mergeability method combines several independent conditions. This demonstrates how a domain object can calculate a result from multiple properties rather than maintaining a potentially stale Boolean field.

The dictionary extraction example uses named assignments, optional-key defaults, and mapping checks. The copying example compares dictionary unpacking with `deepcopy()`, showing why nested mutable values require special attention.

The `Deployment` dataclass demonstrates structured initialization, post-construction validation, a computed readiness property, recursive conversion through `asdict()`, and creation of a modified instance with `replace()`.

The audit and deployment-service example demonstrates composition. A service receives an audit object instead of creating its own logging dependency. Deployment acceptance or rejection produces an event, while `__len__()` and `__iter__()` give the audit object useful collection behavior.

The serialization example deliberately converts objects into JSON-compatible dictionaries. JSON is a data interchange format, not a universal representation of arbitrary Python object identity, methods, or custom types.

## JavaScript implementation

The JavaScript program emphasizes property descriptors, receiver binding, object construction, and asynchronous state access.

The repository object uses a getter for `fullName`. Its `addStars()` method depends on `this`, illustrating why extracting a method and invoking it as an ordinary function can change its receiver. Binding the function explicitly preserves the intended receiver.

`Object.defineProperty()` creates a computed property whose behavior is described by a getter and whose descriptor controls enumerability and configurability. `Object.freeze()` prevents changes to the object's own properties, but does not recursively freeze nested objects.

The Pull Request object contains branch information, review decisions, and check results. The destructuring example extracts nested fields and collects remaining top-level properties. Defaults apply to missing or undefined values, while explicit `null` remains a distinct value.

The spread example merges configuration layers and demonstrates shallow-copy aliasing. `structuredClone()` creates an isolated copy of supported structured-cloneable data, but does not preserve arbitrary prototypes, methods, or functions.

Computed property names construct metric records dynamically. A separate allowlist-based lookup illustrates how property access can be restricted when a property name comes from external input.

The `ReviewStore` uses a private class field and a `Map` to encapsulate records. It validates incoming Pull Requests, stores isolated snapshots, performs an asynchronous approval operation, and returns independent snapshots to callers. The asynchronous interface makes the boundary explicit, even though the demonstration uses in-memory storage instead of a remote service.

## C++ case study: Repository governance

The C++ program models a governance engine that decides whether a Pull Request satisfies a protected branch's merge conditions.

The architecture separates repository changes, reviewers, review comments, review decisions, branch protection policy, and merge evaluation. This separation makes each object responsible for a distinct part of the domain.

`PullRequest` stores source and target branches, commit identifiers, lifecycle state, status checks, reviews, and discussion records. Methods validate review requests and submissions before changing state. `BranchProtection` holds policy settings, while `GovernanceEngine` evaluates whether the current Pull Request satisfies those settings.

The implementation uses `enum class` for explicit lifecycle and review states, `vector` for ordered review records, `set` for unique reviewer requests and required checks, and `map` for named status checks. These structures reflect the operations the domain needs: iteration over reviews, uniqueness of requested reviewers, and lookup by check name.

Merge eligibility depends on several independent conditions. The Pull Request must be open, must not be a draft, must have no merge conflicts, must target the protected branch, and must reference the expected head commit. Required checks must pass, eligible reviewers must provide enough current approvals, and mandatory review conversations must be resolved.

The stale-approval policy compares the commit associated with each review against the current Pull Request head. A source update can therefore invalidate previous approvals without deleting the underlying changeset.

The engine returns a structured decision containing blockers instead of stopping at the first failure. This approach makes governance outcomes easier to inspect and allows a user interface or audit system to display multiple reasons for rejection.

The example uses a simplified in-memory state model. It does not implement Git's commit graph, server-side concurrency control, or actual merge algorithms. A production service would also need transactional persistence, authenticated identities, permission checks, and a reliable relationship between the evaluated commit and the commit eventually merged.

## Java implementation: Enterprise domain modeling

The Java program expresses repository governance through explicit domain types and controlled state transitions.

Records represent immutable value objects such as reviewers, review comments, individual review submissions, branch protection rules, and merge decisions. Constructor validation rejects malformed values early. Collection snapshots use `List.copyOf()` and `Set.copyOf()` to prevent callers from mutating those collections through retained references.

The mutable `PullRequest` class encapsulates its lifecycle state, branch identifiers, requested reviewers, checks, reviews, and comments. Methods such as `requestReview()`, `submitReview()`, `pushCommit()`, `close()`, and `reopen()` enforce different rules at the point where a state change is requested.

Review decisions are represented by an enum instead of loosely controlled strings. The service calculates approval counts from current review records, checks reviewer eligibility, evaluates status checks, and identifies unresolved discussions.

The implementation replaces an earlier decision from the same reviewer rather than counting repeated approvals as independent votes. It also supports stale-approval handling when the source commit changes.

`GovernanceService` separates policy evaluation from the Pull Request's stored state. Its `MergeDecision` value object provides both an eligibility result and explicit blockers. This makes policy evaluation easier to test and reduces the risk of mixing persistence operations with decision rules.

The merge operation checks eligibility before transitioning the Pull Request to `MERGED`. The sample models the selected merge strategy as a domain decision, but does not manipulate actual Git commits.

A production implementation would persist review history separately from the current effective decision, define reviewer independence rules, and enforce atomicity between the final policy check and the merge operation.

## SQL implementation: Relational representation

The PostgreSQL schema represents repository governance through related tables rather than a single nested object document.

`repositories` defines repository identity. `reviewers` stores reviewer eligibility and administrative status. `repository_members` connects people to repositories and assigns repository roles. `branches` tracks branch names and head commit identifiers, while `commits` records repository commit metadata.

`branch_protection` associates policy with a repository and target branch. Its fields distinguish approval thresholds, conversation-resolution requirements, linear-history requirements, direct-push restrictions, force-push restrictions, deletion restrictions, stale-approval behavior, and administrator compliance.

`pull_requests` references source and base commit identifiers and stores lifecycle state. `reviews` records reviewer decisions against specific commits. `review_comments` represents inline and general discussion, while `status_checks` records the result of each check against a specific commit. `review_requests`, `pull_request_labels`, and `merge_events` capture other workflow relationships.

Primary keys and foreign keys establish identity and referential integrity. Unique constraints prevent duplicate repository names, duplicate branch names within a repository, repeated labels, and duplicate status results for the same Pull Request, check name, and commit. Check constraints reject invalid states, empty identifiers, invalid approval counts, and identical source and target branches.

Indexes support common access paths, including repository Pull Requests by target branch and state, reviews by reviewer and submission time, checks by Pull Request and commit, and unresolved review discussions.

The merge-eligibility function derives a current review decision for each reviewer by selecting the latest submitted review. It counts only eligible approvals that apply to the current source commit when stale approvals must be dismissed. It also checks the configured approval threshold, required status checks, unresolved conversations, and current requests for changes.

The eligibility view presents these results alongside repository and Pull Request metadata. This keeps the decision query available to reporting clients without requiring each client to recreate its logic.

The branch-update trigger blocks direct branch-head changes and protected branch deletion when the applicable policy forbids those operations. It illustrates database-level enforcement, although a production deployment must also secure table ownership, permissions, force-push workflows, and bypass authorization.

The demonstration script includes an unresolved discussion, a draft Pull Request, successful and incomplete checks, and approvals that become stale after a new commit. The resulting queries expose how independent policy conditions combine to determine merge eligibility.

## Important design distinctions

| Mechanism | Responsibility | Example |
|---|---|---|
| Stored property | Retains an object's state | A Pull Request's source branch |
| Computed property | Derives a value from existing state | A repository's full name |
| Method | Performs behavior or a state transition | Submitting a review |
| Nested object | Represents a related entity | A Pull Request's branch metadata |
| Destructuring | Extracts selected values | Reading a reviewer name from a payload |
| Spread or unpacking | Combines properties into a new outer structure | Applying deployment overrides |
| Deep copy | Separates supported nested mutable data | Returning an independent configuration snapshot |
| Computed key | Determines a property name at runtime | Storing a metric under its selected name |
| Validation | Rejects invalid state before use | Preventing identical source and target branches |
| Policy evaluation | Calculates whether a set of conditions is satisfied | Determining whether a protected-branch merge is eligible |

These mechanisms are related but not interchangeable. A copied object may still contain shared nested references. A computed property may be read-only without making the whole object immutable. A review record may be valid without being current, and an approval may exist without satisfying repository merge policy.

## Edge cases and production implications

### Missing fields and unexpected values

External payloads must be treated as untrusted input. Required identifiers, nested structures, types, and allowed values should be validated before business logic accesses them. Defaults are appropriate only when omission has a defined meaning.

### Mutation and aliasing

Shallow copying can cause configuration changes to leak between requests or service instances. Deep copying is appropriate for supported data structures when an independent snapshot is required, but copying everything indiscriminately can waste memory and obscure intentional shared state.

Immutable value objects and controlled update methods often provide a clearer design than unrestricted nested mutation.

### Dynamic property access

Computed names are useful when fields genuinely depend on runtime data. Arbitrary external property names should not be passed directly into dynamic attribute reads or writes. An explicit allowlist provides a clear security boundary and helps prevent accidental modification of internal state.

### Serialization

Object serialization should define which properties are public, which fields are omitted, how dates and numeric values are represented, and how nested collections are handled. Runtime methods, object identity, prototypes, and database relationships are not automatically preserved by JSON serialization.

### Consistency and concurrency

An in-memory merge evaluator can become stale immediately after checking eligibility. In a production repository service, new commits, changed reviews, or updated status checks may arrive before the merge completes.

The final policy check and merge must be coordinated with the version of the Pull Request being merged. Database transactions, concurrency controls, commit-SHA verification, and server-enforced branch rules reduce the risk of accepting a change based on obsolete state.

### Policy enforcement boundaries

Application-level validation improves error messages and domain clarity, while database constraints protect relational integrity. Neither alone replaces authorization. A production implementation must establish who may submit reviews, dismiss approvals, change protection rules, push commits, and bypass restrictions.

Repository governance works reliably when object behavior, review records, approval semantics, and branch policies remain distinct but are evaluated together at the point of a sensitive state transition.
