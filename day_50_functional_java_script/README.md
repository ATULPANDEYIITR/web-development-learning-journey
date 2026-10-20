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
