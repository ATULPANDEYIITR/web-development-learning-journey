# Operator Laboratory: Arithmetic, Comparison, Logical, Assignment, Ternary, Nullish Coalescing, and Optional Chaining

## Scope

This learning artifact examines operators as mechanisms for constructing expressions, enforcing conditions, updating state, selecting values, and safely traversing optional data.

The six implementations deliberately use the strengths and limitations of their respective languages. Python emphasizes explicit `None` handling and comparison semantics. JavaScript demonstrates native ternary, nullish coalescing, and optional chaining. C++ uses a repository-governance case study to show strongly typed policy evaluation. Java models the same domain through explicit enterprise-oriented types and services. PostgreSQL expresses conditional and NULL-aware behavior through `CASE`, `COALESCE`, `NULLIF`, JSON operators, constraints, and transactional SQL.

The examples use repository governance because operator combinations naturally express decisions such as whether a Pull Request is mergeable, whether review requirements have been satisfied, and whether a protected branch policy is violated.

## Operator Categories

### Arithmetic operators

Arithmetic operators perform numeric calculations.

Python uses `+`, `-`, `*`, `/`, `//`, `%`, and `**`. The distinction between `/` and `//` is important because `/` produces ordinary division while `//` performs floor division.

JavaScript provides `+`, `-`, `*`, `/`, `%`, and `**`. JavaScript also exposes runtime values such as `Infinity` and `NaN`, so division by zero does not necessarily raise an exception.

C++ and Java provide conventional arithmetic operators with statically typed numeric operands. Their implementations use arithmetic to calculate Pull Request change size, such as additions plus deletions.

The SQL implementation calculates `additions + deletions` inside queries. This makes the change-size policy a database expression rather than merely an application-side calculation.

### Comparison operators

Comparison operators evaluate relationships between values.

Python uses `==`, `!=`, `<`, `<=`, `>`, and `>=`. It also has the identity operators `is` and `is not`. Equality checks whether values compare equal, while identity checks whether two references point to the same object.

JavaScript has both loose equality such as `==` and strict equality such as `===`. Strict comparison avoids many implicit type-conversion surprises. The JavaScript implementation intentionally compares the number `5` with the string `"5"` to expose this distinction.

C++ and Java comparisons operate within their static type systems. The governance implementations use comparisons to test approval counts, branch names, change sizes, and status values.

SQL comparisons use expressions such as `additions + deletions <= 500` and `state = 'PASSED'`. SQL introduces a major distinction through `NULL`: comparisons involving `NULL` do not produce ordinary true or false values. They produce SQL's third logical value, `UNKNOWN`. This is why SQL uses `IS NULL` or `IS NOT NULL` rather than `= NULL`.

### Logical operators

Logical operators combine conditions.

Python uses `and`, `or`, and `not`. JavaScript uses `&&`, `||`, and `!`. C++ and Java use `&&`, `||`, and `!`.

Short-circuit evaluation matters because the right-hand side of an expression may not execute. In the Python and JavaScript programs, this is demonstrated with an operation that would otherwise be unnecessary.

A governance rule can therefore be expressed as a conjunction of independent requirements:

`not draft AND mergeable AND enough approvals AND passing checks`

The important property is that these conditions retain separate meanings. Approval status is not the same thing as build status, and build status is not the same thing as branch policy.

SQL uses `AND`, `OR`, and `NOT`, but its three-valued logic means that `UNKNOWN` can affect a logical expression. Queries therefore need deliberate NULL handling when optional database values are involved.

## Assignment operators

Assignment changes a stored variable or database value.

Python uses `=`, `+=`, `-=`, `*=`, and related compound forms. Python also has the assignment expression operator `:=`, which assigns a value while producing that value inside an expression.

JavaScript supports ordinary assignment, compound assignment, and logical assignment operators. The file demonstrates `||=` and `??=`. Their behavior differs because `||=` treats all falsy values as triggers while `??=` reacts specifically to `null` and `undefined`.

C++ and Java provide conventional assignment and compound-assignment operators. The C++ case study keeps policy configuration in an object, allowing a policy copy to be changed without mutating the original policy.

SQL has no variable-assignment syntax identical to the general-purpose languages in the main query language. An `UPDATE` changes stored column values, while `SET` is also used to configure the current SQL session. The SQL implementation uses `UPDATE` to demonstrate state mutation at the database layer.

## Ternary and conditional expressions

A ternary expression selects one of two values based on a Boolean condition.

Python calls this a conditional expression:

`value_if_true if condition else value_if_false`

JavaScript, C++, and Java use the `condition ? value_if_true : value_if_false` form.

The implementations use conditional expressions for meaningful decisions rather than artificial syntax demonstrations. Examples include choosing a Pull Request state, selecting a merge strategy based on change size, and choosing a governance label.

PostgreSQL uses `CASE` for the equivalent conditional operation. `CASE` is more expressive than a two-branch ternary because it can represent multiple ordered conditions.

## Nullish coalescing and NULL-aware fallback

Nullish operations are concerned specifically with missing values rather than every falsy value.

JavaScript has a native `??` operator. It returns the right-hand value only when the left-hand value is `null` or `undefined`.

This distinction is important:

`0 ?? 5000` produces `0`.

`0 || 5000` produces `5000`.

The first expression preserves a legitimate zero timeout, while the second interprets zero as a falsy value.

Java uses `Objects.requireNonNullElse` and `Optional.orElse` to express explicit fallback behavior.

Python does not have a dedicated `??` operator. The Python implementation therefore uses an explicit `None` test. This is safer than blindly using `value or fallback` when zero, an empty string, or `False` is a valid configured value.

PostgreSQL provides `COALESCE`, which returns the first non-NULL expression. The database implementation also uses `NULLIF` to turn a problematic denominator into `NULL` before division.

## Optional chaining and safe traversal

Optional chaining prevents an attempt to access a property or call a method when an intermediate object is absent.

JavaScript has native optional chaining:

`user.profile?.contact?.email`

If `profile` is absent, evaluation stops safely instead of raising an ordinary property-access exception.

The JavaScript program also demonstrates optional method calls using `logger?.info(...)`.

Python does not provide JavaScript's `?.` syntax. The Python implementation therefore uses a small `safe_getattr` function that walks a sequence of attributes and returns `None` when an intermediate object is unavailable.

Java and C++ do not provide an identical general-purpose optional-chaining operator. Java can model absence with `Optional`, while C++ can use `std::optional`. Both approaches make absence explicit, but neither is syntactically equivalent to JavaScript's property-chain operator.

PostgreSQL has no object-property optional-chaining operator. JSON access operators such as `->` and `->>` retrieve JSON values, while `COALESCE` can provide a fallback when the retrieved value is NULL.

## Precedence and grouping

Operator precedence determines how an expression is parsed when parentheses are absent.

For example:

`2 + 3 * 4`

is interpreted as:

`2 + (3 * 4)`

not:

`(2 + 3) * 4`

Logical expressions also benefit from explicit parentheses when several policies are combined. The governance implementations group conditions so that the intended relationship between branch restrictions, review requirements, status checks, and change limits remains visible.

Parentheses are particularly valuable in security and governance rules because a technically valid but incorrectly grouped condition can produce an authorization decision different from the intended policy.

## Python implementation

The Python program is a progressive operator laboratory with executable behavior.

Its arithmetic section demonstrates integer division, remainder, exponentiation, compound assignment, and division failure handling. The comparison section distinguishes value equality from object identity. The logical section demonstrates operand-returning behavior and short-circuit evaluation.

The Python implementation also exposes an important language distinction: Python does not have native nullish-coalescing or optional-chaining operators. Instead, it demonstrates explicit `None` handling and safe attribute traversal. This avoids falsely presenting a JavaScript feature as if it existed in Python.

The repository-policy example combines operators into a meaningful decision engine. Change size is calculated arithmetically, review and status conditions are compared, and logical operators combine the independent rules.

The executable assertions at the end provide lightweight regression checks for the operator behavior being demonstrated.

## JavaScript implementation

The JavaScript file focuses on operators that are particularly important in web and Node.js applications.

Its comparison section exposes the difference between loose equality and strict equality. This matters when processing HTTP parameters, form values, JSON input, or other data whose runtime types may not be what the application expects.

The nullish section deliberately contrasts `??` with `||`. This is a practical distinction for configuration, cache values, timeout settings, pagination values, and other data where `0`, `false`, or an empty string may be legitimate.

Optional chaining is demonstrated across nested objects and optional method calls. This is useful when consuming partially populated API responses.

The event-driven policy example stores a Pull Request as an object, evaluates its state against a policy, and emits an event record. Optional chaining and nullish fallback are applied to the nested author account rather than being presented as isolated syntax.

## C++ case study

The C++ program models a repository governance engine.

`PullRequest` contains source and target branches, change counts, draft state, mergeability, reviews, and status checks. `BranchProtection` stores the policy applied to a protected branch.

`MergeEligibilityEngine` separates policy evaluation from the data model. Arithmetic calculates total changed lines. Comparisons test policy thresholds. Logical operators combine mandatory conditions. The engine also produces human-readable blockers so that a rejected merge can be diagnosed rather than represented only by `false`.

Reviewer eligibility is intentionally separate from review state. An approved review from an ineligible reviewer does not count toward the approval requirement. This illustrates why an approval decision should not be reduced to a simple Boolean attached to every review.

The case study contains separate failures for unresolved review discussion, failed status checks, and draft state. Those conditions are not interchangeable even though all can prevent a merge.

`std::optional` demonstrates explicit absence without a sentinel value. The policy object is copied before its approval requirement is changed, illustrating how policy configuration can be varied without altering the original protected-branch configuration.

## Java implementation

The Java implementation models the same broad governance domain through explicit enterprise-oriented abstractions rather than translating the C++ program line by line.

`ReviewState`, `CheckState`, and `MergeStrategy` are enums, which prevents arbitrary strings from representing domain states. `Reviewer` and `Review` are immutable records with validation and behavior directly related to review eligibility.

`PullRequest` owns lifecycle-related state such as draft and mergeability. Its methods represent meaningful state changes instead of exposing unrestricted field mutation.

`BranchProtectionPolicy` expresses governance configuration as a validated immutable record. The policy includes approval requirements, change limits, status-check requirements, discussion requirements, and direct-push and force-push restrictions.

`MergeEligibilityService` evaluates the Pull Request and returns a `MergeEvaluation` containing both the Boolean decision and the blockers. This separates decision logic from presentation.

Java's standard collections and streams are used for review and status evaluation. `Objects.requireNonNullElse` and `Optional` demonstrate explicit null or absence handling without pretending Java has JavaScript's `??` or `?.` operators.

## SQL relational model

The PostgreSQL implementation represents the governance domain relationally.

`repository` identifies the repository. `branch` stores repository branches and whether a branch is protected. `pull_request` connects source and target branches and records the change size and lifecycle state.

`reviewer` stores reviewer eligibility and account activity. `review` records an actual review decision. `review_comment` represents discussions that can remain unresolved independently of the review's overall state.

`status_check` stores individual automated check results. This keeps build, unit-test, and security-check outcomes separate so that a single failed check can be identified.

`branch_protection_policy` stores repository governance rules such as required approvals, maximum change size, required passing checks, conversation resolution, direct-push restrictions, force-push restrictions, branch deletion restrictions, and linear-history requirements.

Primary keys and foreign keys enforce relationships. Unique constraints prevent duplicate repository names within an owner, duplicate branch names within a repository, duplicate Pull Request numbers within a repository, duplicate reviewers, duplicate commit hashes, and duplicate status-check names for a Pull Request.

Check constraints reject negative additions and deletions, invalid Pull Request numbers, empty names, and invalid policy thresholds.

Partial indexing on unresolved comments gives the database an efficient access path for the specific governance condition that matters during merge evaluation.

## Database-level policy evaluation

The SQL report combines several independent predicates.

Approval eligibility requires both an active reviewer and `eligible_to_approve = TRUE`. The review must also have the `APPROVED` state. This prevents an approval from being counted merely because a review record exists.

Status evaluation aggregates individual checks. The database can therefore distinguish a Pull Request with all checks passing from one with a single failed security check.

Conversation evaluation uses unresolved comment rows rather than assuming that an approved review means every discussion is resolved. This preserves the distinction between a review decision and the state of individual review discussions.

`CASE` converts these conditions into a meaningful governance decision such as `MERGE ELIGIBLE`, `BLOCKED: approvals`, or `BLOCKED: unresolved discussion`.

The transaction demonstrates a state change in which an unresolved review conversation is resolved and the data is committed before the final governance report is generated.

## Approval semantics

An approval is a review decision, not merely evidence that someone viewed a Pull Request.

The examples distinguish reviewer eligibility from review state. An eligible active reviewer submitting `APPROVED` can contribute to the required approval count. An external or otherwise ineligible reviewer can submit an approval without satisfying the protected-branch approval requirement.

This distinction is important because approval requirements are policy rules. The presence of an approval record does not by itself imply merge eligibility.

The examples also separate approval requirements from status checks and unresolved discussions. A Pull Request can have sufficient approvals and still be blocked by a failed security check or an unresolved review conversation.

## Branch protection semantics

Branch protection belongs to the target branch rather than being an intrinsic property of every Pull Request.

The protected `main` branch in the database has a policy that requires approvals, passing checks, resolved discussions, and restrictions on direct pushes and force pushes. The C++ and Java models represent similar rules as explicit policy objects.

The policy is evaluated when determining merge eligibility. This creates an important relationship between the mechanisms:

A Pull Request proposes a change from a source branch to a target branch.

Code review evaluates the proposed changes and produces review decisions and discussions.

Approvals represent qualifying review decisions.

Branch protection defines which conditions must be satisfied before changes can enter a protected target branch.

These mechanisms therefore interact but should not be collapsed into one concept.

## Edge cases and failure modes

Falsy values and missing values must not be treated as identical. JavaScript's `??` is intentionally different from `||`, while Python requires an explicit `None` test when zero or an empty string must be preserved.

Floating-point arithmetic can produce values such as `0.1 + 0.2` that are not exactly equal to the mathematical value `0.3`. The Python and JavaScript implementations demonstrate tolerance-based comparison.

Division by zero behaves differently between languages. Python raises `ZeroDivisionError` for ordinary numeric division, while JavaScript produces `Infinity` for nonzero division by zero and `NaN` for `0 / 0`. SQL uses `NULLIF` in the example to prevent a zero denominator from causing an invalid division operation.

SQL's NULL semantics require special care. `NULL = NULL` is not true. `COALESCE`, `IS NULL`, `IS NOT NULL`, and `NULLIF` exist because ordinary Boolean reasoning is insufficient for nullable database values.

Operator precedence can create security and governance defects if expressions are not grouped according to policy intent. Parentheses make compound conditions auditable.

## Performance and design considerations

Simple arithmetic and comparison operations are normally inexpensive, but operator complexity can increase when expressions traverse collections, invoke functions, or trigger database aggregation.

Short-circuit evaluation can avoid unnecessary work, which is useful when the second operand performs an expensive operation. It should not be relied upon when the skipped operation is required for correctness or required side effects.

Database policy evaluation benefits from indexes on foreign keys and frequently filtered state columns. The partial index on unresolved review comments is particularly aligned with the query that determines whether conversations remain open.

A policy engine should keep independent rules separate even when the final result is one Boolean value. This makes failure diagnosis, testing, auditing, and future policy changes easier.

## Security considerations

Operators can participate directly in authorization and governance decisions, so expression correctness is a security concern.

Strict type comparisons in JavaScript reduce unexpected coercion when evaluating externally supplied values.

Database constraints provide a second enforcement layer for domain invariants such as nonnegative change counts and valid relationships. Application validation should not be treated as the only protection against malformed state.

Branch protection policy must not be bypassed merely because one condition evaluates to true. Required conditions should be combined with logical conjunction where every requirement is mandatory.

Approval eligibility must be evaluated independently of user-supplied display names or arbitrary text. The database model uses foreign keys and reviewer attributes rather than trusting an approval string supplied by an application client.

## Common implementation mistakes

Using `||` when `0`, `false`, or `""` are legitimate configuration values can silently replace valid data with a default.

Using JavaScript `==` when exact type equality is required can introduce implicit coercion.

Using Python `is` for ordinary value equality can produce incorrect logic because identity and equality are different concepts.

Writing a large Boolean expression without explicit grouping can produce a result that is difficult to audit.

Counting every `APPROVED` review without checking reviewer eligibility can incorrectly satisfy a protected-branch policy.

Treating an approved review as proof that every inline discussion is resolved conflates two separate review mechanisms.

Treating a passing build as equivalent to merge eligibility ignores approvals, branch protection, draft state, conflicts, and other policy requirements.

Ignoring SQL NULL semantics can produce filters that do not behave as ordinary two-valued Boolean logic would suggest.

## Practical relationship between the six implementations

The implementations intentionally approach the same operator family from different technical perspectives.

The Python program is an executable language laboratory that emphasizes explicit value handling and Python's absence of native `??` and `?.` operators.

The JavaScript program emphasizes the operators that are particularly useful when handling dynamic application data, optional object structures, configuration values, and event-driven workflows.

The C++ program turns operator composition into a strongly typed merge-governance engine, where policy conditions become explicit Boolean predicates.

The Java program emphasizes domain modeling, immutable policy configuration, enums, records, streams, and service-based evaluation.

The SQL program moves the governance model into relational storage, where constraints enforce invariants and queries evaluate policy against persistent data.

Across all implementations, the central technical distinction remains the same: operators are mechanisms for expressing relationships and decisions, while the meaning of a particular operator depends on the language's type system, evaluation rules, NULL model, and runtime behavior.
