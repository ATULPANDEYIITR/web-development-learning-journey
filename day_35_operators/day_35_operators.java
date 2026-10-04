import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/*
 * Enterprise Repository Governance Model
 *
 * The program models Pull Requests, review decisions, approval eligibility,
 * status checks, and protected-branch policies. Java's type system is used
 * to keep domain states explicit instead of representing them as arbitrary
 * strings.
 */
public class OperatorGovernanceDemo {

    enum ReviewState {
        PENDING,
        APPROVED,
        CHANGES_REQUESTED,
        COMMENTED
    }

    enum CheckState {
        PENDING,
        PASSED,
        FAILED
    }

    enum MergeStrategy {
        MERGE_COMMIT,
        SQUASH,
        REBASE
    }

    record Reviewer(String username, boolean eligible) {
        Reviewer {
            if (username == null || username.isBlank()) {
                throw new IllegalArgumentException("Reviewer name is required");
            }
        }
    }

    record Review(
            Reviewer reviewer,
            ReviewState state,
            List<String> comments) {

        Review {
            Objects.requireNonNull(reviewer);
            Objects.requireNonNull(state);
            comments = List.copyOf(comments);
        }

        boolean countsAsApproval() {
            return reviewer.eligible() && state == ReviewState.APPROVED;
        }

        boolean hasUnresolvedDiscussion() {
            return comments.stream()
                    .anyMatch(comment -> comment.startsWith("[unresolved]"));
        }
    }

    static final class PullRequest {
        private final int number;
        private final String sourceBranch;
        private final String targetBranch;
        private final int additions;
        private final int deletions;
        private final List<Review> reviews;
        private final Map<String, CheckState> checks;
        private boolean draft;
        private boolean mergeable;

        PullRequest(
                int number,
                String sourceBranch,
                String targetBranch,
                int additions,
                int deletions,
                boolean draft,
                boolean mergeable,
                List<Review> reviews,
                Map<String, CheckState> checks) {

            if (number <= 0) {
                throw new IllegalArgumentException("Pull Request number must be positive");
            }
            if (additions < 0 || deletions < 0) {
                throw new IllegalArgumentException("Change counts cannot be negative");
            }

            this.number = number;
            this.sourceBranch = Objects.requireNonNull(sourceBranch);
            this.targetBranch = Objects.requireNonNull(targetBranch);
            this.additions = additions;
            this.deletions = deletions;
            this.draft = draft;
            this.mergeable = mergeable;
            this.reviews = new ArrayList<>(reviews);
            this.checks = Map.copyOf(checks);
        }

        int number() {
            return number;
        }

        String targetBranch() {
            return targetBranch;
        }

        int changedLines() {
            return additions + deletions;
        }

        boolean draft() {
            return draft;
        }

        boolean mergeable() {
            return mergeable;
        }

        List<Review> reviews() {
            return List.copyOf(reviews);
        }

        Map<String, CheckState> checks() {
            return checks;
        }

        void markReadyForReview() {
            draft = false;
        }

        void markConflicted() {
            mergeable = false;
        }
    }

    record BranchProtectionPolicy(
            String protectedBranch,
            int requiredApprovals,
            int maximumChangedLines,
            boolean requirePassingChecks,
            boolean requireResolvedDiscussions,
            boolean allowForcePush,
            boolean allowDirectPush) {

        BranchProtectionPolicy {
            if (protectedBranch == null || protectedBranch.isBlank()) {
                throw new IllegalArgumentException("Protected branch is required");
            }
            if (requiredApprovals < 0) {
                throw new IllegalArgumentException("Approval count cannot be negative");
            }
            if (maximumChangedLines <= 0) {
                throw new IllegalArgumentException(
                        "Maximum changed lines must be positive");
            }
        }
    }

    record MergeEvaluation(
            boolean eligible,
            List<String> blockers) {

        MergeEvaluation {
            blockers = List.copyOf(blockers);
        }
    }

    static final class MergeEligibilityService {
        private final BranchProtectionPolicy policy;

        MergeEligibilityService(BranchProtectionPolicy policy) {
            this.policy = Objects.requireNonNull(policy);
        }

        MergeEvaluation evaluate(PullRequest pullRequest) {
            List<String> blockers = new ArrayList<>();

            if (!pullRequest.targetBranch()
                    .equals(policy.protectedBranch())) {
                blockers.add("Target branch is outside the protected policy");
            }

            if (pullRequest.draft()) {
                blockers.add("Pull Request is still a draft");
            }

            if (!pullRequest.mergeable()) {
                blockers.add("Pull Request has an unresolved merge conflict");
            }

            if (pullRequest.changedLines()
                    > policy.maximumChangedLines()) {
                blockers.add("Change exceeds the protected branch size limit");
            }

            long approvals = pullRequest.reviews().stream()
                    .filter(Review::countsAsApproval)
                    .count();

            if (approvals < policy.requiredApprovals()) {
                blockers.add(
                        "Required approvals are not satisfied: "
                                + approvals
                                + "/"
                                + policy.requiredApprovals());
            }

            if (policy.requirePassingChecks()
                    && !allChecksPassed(pullRequest)) {
                blockers.add("A required status check is not passing");
            }

            if (policy.requireResolvedDiscussions()
                    && hasUnresolvedDiscussion(pullRequest)) {
                blockers.add("An inline review discussion is unresolved");
            }

            return new MergeEvaluation(blockers.isEmpty(), blockers);
        }

        private boolean allChecksPassed(PullRequest pullRequest) {
            return !pullRequest.checks().isEmpty()
                    && pullRequest.checks().values().stream()
                    .allMatch(state -> state == CheckState.PASSED);
        }

        private boolean hasUnresolvedDiscussion(PullRequest pullRequest) {
            return pullRequest.reviews().stream()
                    .anyMatch(Review::hasUnresolvedDiscussion);
        }
    }

    static String conditionalMergeLabel(boolean eligible) {
        return eligible ? "MERGE ALLOWED" : "MERGE BLOCKED";
    }

    public static void main(String[] args) {
        BranchProtectionPolicy policy = new BranchProtectionPolicy(
                "main",
                2,
                500,
                true,
                true,
                false,
                false
        );

        Reviewer alice = new Reviewer("alice", true);
        Reviewer bob = new Reviewer("bob", true);
        Reviewer external = new Reviewer("external-contributor", false);

        PullRequest paymentRequest = new PullRequest(
                201,
                "feature/payment-timeout",
                "main",
                140,
                60,
                false,
                true,
                List.of(
                        new Review(alice, ReviewState.APPROVED, List.of()),
                        new Review(bob, ReviewState.APPROVED, List.of()),
                        new Review(
                                external,
                                ReviewState.APPROVED,
                                List.of("External approval does not count"))
                ),
                Map.of(
                        "build", CheckState.PASSED,
                        "unit-tests", CheckState.PASSED,
                        "security-scan", CheckState.PASSED
                )
        );

        PullRequest auditRequest = new PullRequest(
                202,
                "feature/audit-log",
                "main",
                60,
                30,
                false,
                true,
                List.of(
                        new Review(
                                alice,
                                ReviewState.APPROVED,
                                List.of("Audit structure is correct.")),
                        new Review(
                                bob,
                                ReviewState.CHANGES_REQUESTED,
                                List.of(
                                        "[unresolved] Retention policy needs review."
                                ))
                ),
                Map.of(
                        "build", CheckState.PASSED,
                        "unit-tests", CheckState.PASSED,
                        "security-scan", CheckState.PASSED
                )
        );

        MergeEligibilityService service =
                new MergeEligibilityService(policy);

        evaluateAndPrint(paymentRequest, service);
        evaluateAndPrint(auditRequest, service);

        /*
         * Java does not have a built-in ternary-free nullish coalescing
         * operator. Objects.requireNonNullElse expresses an explicit
         * null fallback for object references.
         */
        String configuredQueue = null;
        String queueName =
                Objects.requireNonNullElse(configuredQueue, "merge-queue");

        System.out.println("\nNull fallback queue: " + queueName);

        /*
         * Optional models a possibly absent value. orElse supplies the
         * default only when the Optional is empty.
         */
        java.util.Optional<Integer> configuredApprovals =
                java.util.Optional.empty();

        int approvalLimit = configuredApprovals.orElse(2);
        System.out.println("Optional approval limit: " + approvalLimit);

        MergeStrategy strategy =
                paymentRequest.changedLines() > 300
                        ? MergeStrategy.SQUASH
                        : MergeStrategy.MERGE_COMMIT;

        System.out.println("Selected merge strategy: " + strategy);

        /*
         * Assignment is explicit in Java. Compound assignments are useful
         * for counters while preserving a strongly typed variable.
         */
        int reviewedFiles = 4;
        reviewedFiles += 3;
        reviewedFiles *= 2;
        System.out.println("Reviewed-file calculation: " + reviewedFiles);
    }

    private static void evaluateAndPrint(
            PullRequest pullRequest,
            MergeEligibilityService service) {

        MergeEvaluation evaluation = service.evaluate(pullRequest);

        System.out.println(
                "\nPull Request #"
                        + pullRequest.number()
                        + " -> "
                        + conditionalMergeLabel(evaluation.eligible()));

        if (evaluation.blockers().isEmpty()) {
            System.out.println("All governance conditions are satisfied.");
        } else {
            evaluation.blockers().forEach(
                    blocker -> System.out.println("Blocked by: " + blocker));
        }
    }
}
