import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/**
 * Enterprise repository governance model.
 *
 * Demonstrates Java's implicit this reference, constructor initialization,
 * method references, explicit receiver selection, and lambdas that capture
 * an object. Java does not support JavaScript's call/apply/bind methods.
 *
 * Compile and run:
 *   javac ThisKeywordGovernance.java
 *   java ThisKeywordGovernance
 */
public class ThisKeywordGovernance {

    enum ReviewState {
        COMMENTED,
        APPROVED,
        CHANGES_REQUESTED
    }

    enum CheckState {
        SUCCESS,
        FAILURE,
        PENDING
    }

    static final class Review {
        private final String reviewer;
        private final ReviewState state;
        private final boolean eligibleReviewer;

        Review(String reviewer, ReviewState state, boolean eligibleReviewer) {
            this.reviewer = requireText(reviewer, "reviewer");
            this.state = Objects.requireNonNull(state, "state");
            this.eligibleReviewer = eligibleReviewer;
        }

        String reviewer() {
            return reviewer;
        }

        ReviewState state() {
            return state;
        }

        boolean eligibleReviewer() {
            return eligibleReviewer;
        }
    }

    static final class PullRequest {
        private final int number;
        private final String author;
        private final String sourceBranch;
        private final String targetBranch;
        private final List<Review> reviews;
        private final Map<String, CheckState> checks;
        private final int requiredApprovals;
        private final boolean conversationsResolved;
        private final boolean protectedTarget;

        PullRequest(
                int number,
                String author,
                String sourceBranch,
                String targetBranch,
                List<Review> reviews,
                Map<String, CheckState> checks,
                int requiredApprovals,
                boolean conversationsResolved,
                boolean protectedTarget) {

            if (number <= 0) {
                throw new IllegalArgumentException("PR number must be positive");
            }

            this.number = number;
            this.author = requireText(author, "author");
            this.sourceBranch = requireText(sourceBranch, "sourceBranch");
            this.targetBranch = requireText(targetBranch, "targetBranch");

            if (this.sourceBranch.equals(this.targetBranch)) {
                throw new IllegalArgumentException(
                        "Source and target branches must differ");
            }

            if (requiredApprovals < 0) {
                throw new IllegalArgumentException(
                        "Required approvals cannot be negative");
            }

            // Defensive copies prevent callers from changing governance
            // inputs after the PullRequest object has been constructed.
            this.reviews = List.copyOf(
                    Objects.requireNonNull(reviews, "reviews"));
            this.checks = Map.copyOf(
                    Objects.requireNonNull(checks, "checks"));
            this.requiredApprovals = requiredApprovals;
            this.conversationsResolved = conversationsResolved;
            this.protectedTarget = protectedTarget;
        }

        int number() {
            return this.number;
        }

        String author() {
            return this.author;
        }

        int countEligibleApprovals() {
            // The lambda reads its Review argument. It does not need this.
            return (int) this.reviews.stream()
                    .filter(Review::eligibleReviewer)
                    .filter(review -> review.state() == ReviewState.APPROVED)
                    .count();
        }

        boolean hasChangesRequested() {
            return this.reviews.stream()
                    .filter(Review::eligibleReviewer)
                    .anyMatch(review ->
                            review.state() == ReviewState.CHANGES_REQUESTED);
        }

        boolean checksPassed() {
            // An empty required-check map is rejected by policy evaluation:
            // no configured checks must not silently mean success.
            return !this.checks.isEmpty()
                    && this.checks.values().stream()
                    .allMatch(state -> state == CheckState.SUCCESS);
        }

        List<String> blockers() {
            List<String> result = new ArrayList<>();

            if (this.hasChangesRequested()) {
                result.add("An eligible reviewer requested changes");
            }

            if (this.countEligibleApprovals() < this.requiredApprovals) {
                result.add("Required approval count has not been met");
            }

            if (!this.checksPassed()) {
                result.add("Required status checks have not all succeeded");
            }

            if (!this.conversationsResolved) {
                result.add("Review conversations remain unresolved");
            }

            if (!this.protectedTarget) {
                result.add("Target branch has no protection policy");
            }

            return List.copyOf(result);
        }

        boolean isMergeEligible() {
            return this.blockers().isEmpty();
        }

        String report() {
            return "PR #" + this.number + ": " + this.sourceBranch
                    + " -> " + this.targetBranch
                    + "\nAuthor: " + this.author
                    + "\nEligible approvals: " + this.countEligibleApprovals()
                    + "/" + this.requiredApprovals
                    + "\nMerge eligible: " + this.isMergeEligible()
                    + "\nBlockers: " + this.blockers();
        }
    }

    static final class MergeEligibilityService {
        private final String serviceName;

        MergeEligibilityService(String serviceName) {
            this.serviceName = requireText(serviceName, "serviceName");
        }

        boolean evaluate(PullRequest request) {
            // The method's this refers to the service instance, not request.
            Objects.requireNonNull(request, "request");
            System.out.println(this.serviceName
                    + " evaluating PR #" + request.number());
            return request.isMergeEligible();
        }
    }

    private static String requireText(String value, String field) {
        if (value == null || value.isBlank()) {
            throw new IllegalArgumentException(field + " cannot be blank");
        }
        return value;
    }

    public static void main(String[] args) {
        Review securityApproval =
                new Review("security-reviewer", ReviewState.APPROVED, true);

        Review authorApproval =
                new Review("author", ReviewState.APPROVED, false);

        Review requestedChanges =
                new Review("platform-reviewer",
                        ReviewState.CHANGES_REQUESTED, true);

        PullRequest ready = new PullRequest(
                42,
                "maya",
                "feature/secure-merge",
                "main",
                List.of(securityApproval, authorApproval),
                Map.of(
                        "unit-tests", CheckState.SUCCESS,
                        "security-scan", CheckState.SUCCESS,
                        "lint", CheckState.SUCCESS),
                1,
                true,
                true);

        PullRequest blocked = new PullRequest(
                43,
                "arun",
                "feature/cache-policy",
                "main",
                List.of(requestedChanges),
                Map.of(
                        "unit-tests", CheckState.SUCCESS,
                        "security-scan", CheckState.FAILURE),
                2,
                false,
                true);

        MergeEligibilityService service =
                new MergeEligibilityService("RepositoryGovernance");

        System.out.println(ready.report());
        System.out.println();
        System.out.println(blocked.report());

        // A method reference can be retained as a callback. This reference
        // retains the ready object as its receiver.
        java.util.function.BooleanSupplier readyDecision =
                ready::isMergeEligible;

        System.out.println("\nMethod reference decision: "
                + readyDecision.getAsBoolean());

        // This lambda captures service and ready. Both are effectively final.
        java.util.function.BooleanSupplier serviceDecision =
                () -> service.evaluate(ready);

        System.out.println("Captured service decision: "
                + serviceDecision.getAsBoolean());

        // Java has no Function.prototype.call/apply/bind. A method reference
        // or lambda can retain an intended receiver when passed as a callback.
        try {
            new PullRequest(
                    44, " ", "feature/x", "main",
                    List.of(), Map.of("tests", CheckState.SUCCESS),
                    1, true, true);
        } catch (IllegalArgumentException exception) {
            System.out.println("Validation rejected invalid author: "
                    + exception.getMessage());
        }
    }
}
