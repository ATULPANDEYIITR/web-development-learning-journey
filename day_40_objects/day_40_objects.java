import java.time.Instant;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.TreeMap;
import java.util.stream.Collectors;

/**
 * Repository governance modeled through Java domain objects.
 *
 * Compile and run:
 *   javac RepositoryGovernance.java
 *   java RepositoryGovernance
 */
public class RepositoryGovernance {

    enum PullRequestState {
        DRAFT, OPEN, CLOSED, MERGED
    }

    enum ReviewState {
        PENDING, COMMENTED, APPROVED, CHANGES_REQUESTED, DISMISSED
    }

    enum MergeStrategy {
        MERGE_COMMIT, SQUASH, REBASE
    }

    record Reviewer(String username, boolean active, boolean eligible) {
        Reviewer {
            if (username == null || username.isBlank()) {
                throw new IllegalArgumentException("Reviewer username is required");
            }
        }
    }

    record ReviewComment(
        String path,
        int line,
        String body,
        boolean resolved
    ) {
        ReviewComment {
            if (path == null || path.isBlank()) {
                throw new IllegalArgumentException("Comment path is required");
            }
            if (line < 1) {
                throw new IllegalArgumentException("Line numbers begin at one");
            }
            if (body == null || body.isBlank()) {
                throw new IllegalArgumentException("Comment body is required");
            }
        }
    }

    record Review(
        Reviewer reviewer,
        ReviewState state,
        String commitSha,
        List<ReviewComment> comments,
        Instant submittedAt
    ) {
        Review {
            Objects.requireNonNull(reviewer, "reviewer");
            Objects.requireNonNull(state, "state");
            if (commitSha == null || commitSha.isBlank()) {
                throw new IllegalArgumentException("Reviewed commit is required");
            }
            comments = List.copyOf(comments);
            Objects.requireNonNull(submittedAt, "submittedAt");
        }
    }

    record BranchProtection(
        String branch,
        int requiredApprovals,
        Set<String> requiredChecks,
        boolean requireResolvedConversations,
        boolean requireLinearHistory,
        boolean restrictDirectPushes,
        boolean restrictForcePushes,
        boolean preventDeletion,
        boolean dismissStaleApprovals,
        boolean administratorsMustComply
    ) {
        BranchProtection {
            if (branch == null || branch.isBlank()) {
                throw new IllegalArgumentException("Protected branch is required");
            }
            if (requiredApprovals < 0) {
                throw new IllegalArgumentException("Approval count cannot be negative");
            }
            requiredChecks = Set.copyOf(requiredChecks);
        }
    }

    static final class PullRequest {
        private final int number;
        private final String title;
        private final String sourceBranch;
        private final String targetBranch;
        private final Set<String> requestedReviewers = new HashSet<>();
        private final Map<String, Boolean> statusChecks = new HashMap<>();
        private final List<Review> reviews = new ArrayList<>();
        private final List<ReviewComment> comments = new ArrayList<>();

        private PullRequestState state;
        private String headSha;
        private String baseSha;
        private boolean hasConflicts;

        PullRequest(
            int number,
            String title,
            String sourceBranch,
            String targetBranch,
            String headSha,
            String baseSha,
            boolean draft
        ) {
            if (number < 1) {
                throw new IllegalArgumentException("Pull request number must be positive");
            }
            if (title == null || title.isBlank()) {
                throw new IllegalArgumentException("Title is required");
            }
            if (sourceBranch == null || sourceBranch.isBlank()
                    || targetBranch == null || targetBranch.isBlank()) {
                throw new IllegalArgumentException("Both branches are required");
            }
            if (sourceBranch.equals(targetBranch)) {
                throw new IllegalArgumentException("Source and target must differ");
            }
            this.number = number;
            this.title = title;
            this.sourceBranch = sourceBranch;
            this.targetBranch = targetBranch;
            this.headSha = Objects.requireNonNull(headSha);
            this.baseSha = Objects.requireNonNull(baseSha);
            this.state = draft ? PullRequestState.DRAFT : PullRequestState.OPEN;
        }

        int number() {
            return number;
        }

        String title() {
            return title;
        }

        PullRequestState state() {
            return state;
        }

        String headSha() {
            return headSha;
        }

        String baseSha() {
            return baseSha;
        }

        String sourceBranch() {
            return sourceBranch;
        }

        String targetBranch() {
            return targetBranch;
        }

        boolean hasConflicts() {
            return hasConflicts;
        }

        void setConflicts(boolean value) {
            requireOpen();
            hasConflicts = value;
        }

        void requestReview(Reviewer reviewer) {
            requireOpen();
            if (!reviewer.active() || !reviewer.eligible()) {
                throw new IllegalArgumentException("Reviewer is not eligible");
            }
            requestedReviewers.add(reviewer.username());
        }

        Set<String> requestedReviewers() {
            return Collections.unmodifiableSet(requestedReviewers);
        }

        void recordCheck(String name, boolean passed) {
            requireOpen();
            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException("Check name is required");
            }
            statusChecks.put(name, passed);
        }

        Map<String, Boolean> statusChecks() {
            return Collections.unmodifiableMap(statusChecks);
        }

        void submitReview(Review review) {
            requireOpen();
            if (!review.reviewer().active() || !review.reviewer().eligible()) {
                throw new IllegalArgumentException("Ineligible reviewer cannot submit a decision");
            }

            // Replace the current decision from the same reviewer. This
            // models the latest submitted state rather than counting every
            // historical approval as an independent vote.
            reviews.removeIf(existing ->
                existing.reviewer().username().equals(review.reviewer().username())
            );
            reviews.add(review);
            requestedReviewers.remove(review.reviewer().username());
        }

        List<Review> reviews() {
            return List.copyOf(reviews);
        }

        void addComment(ReviewComment comment) {
            requireOpen();
            comments.add(Objects.requireNonNull(comment));
        }

        List<ReviewComment> comments() {
            return List.copyOf(comments);
        }

        void synchronizeBase(String newBaseSha, boolean approvalsBecomeStale) {
            requireOpen();
            if (newBaseSha == null || newBaseSha.isBlank()) {
                throw new IllegalArgumentException("New base SHA is required");
            }
            if (!baseSha.equals(newBaseSha)) {
                baseSha = newBaseSha;
                if (approvalsBecomeStale) {
                    reviews.removeIf(review -> review.state() == ReviewState.APPROVED);
                }
            }
        }

        void pushCommit(String newHeadSha, boolean dismissStaleApprovals) {
            requireOpen();
            if (newHeadSha == null || newHeadSha.isBlank()) {
                throw new IllegalArgumentException("New head SHA is required");
            }
            if (!headSha.equals(newHeadSha)) {
                headSha = newHeadSha;
                if (dismissStaleApprovals) {
                    reviews.removeIf(review ->
                        review.state() == ReviewState.APPROVED
                    );
                }
            }
        }

        void reopen() {
            if (state != PullRequestState.CLOSED) {
                throw new IllegalStateException("Only a closed pull request can be reopened");
            }
            state = PullRequestState.OPEN;
        }

        void close() {
            requireOpen();
            state = PullRequestState.CLOSED;
        }

        void markMerged() {
            requireOpen();
            state = PullRequestState.MERGED;
        }

        private void requireOpen() {
            if (state != PullRequestState.OPEN) {
                throw new IllegalStateException("Operation requires an open pull request");
            }
        }
    }

    record MergeDecision(boolean eligible, List<String> blockers) {
        MergeDecision {
            blockers = List.copyOf(blockers);
        }

        String describe() {
            return eligible
                ? "Eligible to merge"
                : "Blocked: " + String.join("; ", blockers);
        }
    }

    static final class GovernanceService {
        MergeDecision evaluate(
            PullRequest pullRequest,
            BranchProtection policy,
            String currentHeadSha,
            boolean administrator
        ) {
            List<String> blockers = new ArrayList<>();

            if (pullRequest.state() != PullRequestState.OPEN) {
                blockers.add("Pull request is not open");
            }
            if (!pullRequest.targetBranch().equals(policy.branch())) {
                blockers.add("Target branch is not the protected branch");
            }
            if (pullRequest.hasConflicts()) {
                blockers.add("Merge conflicts remain");
            }
            if (!pullRequest.headSha().equals(currentHeadSha)) {
                blockers.add("Source commit has changed");
            }

            if (administrator && !policy.administratorsMustComply()) {
                return new MergeDecision(blockers.isEmpty(), blockers);
            }

            for (String required : policy.requiredChecks()) {
                if (!Boolean.TRUE.equals(pullRequest.statusChecks().get(required))) {
                    blockers.add("Required check failed or is missing: " + required);
                }
            }

            long approvals = pullRequest.reviews().stream()
                .filter(review -> review.state() == ReviewState.APPROVED)
                .filter(review -> review.reviewer().active())
                .filter(review -> review.reviewer().eligible())
                .filter(review -> !policy.dismissStaleApprovals()
                    || review.commitSha().equals(currentHeadSha))
                .count();

            if (approvals < policy.requiredApprovals()) {
                blockers.add("Eligible approvals: " + approvals + "/"
                    + policy.requiredApprovals());
            }

            boolean changesRequested = pullRequest.reviews().stream()
                .filter(review -> review.reviewer().active() && review.reviewer().eligible())
                .filter(review -> !policy.dismissStaleApprovals()
                    || review.commitSha().equals(currentHeadSha))
                .anyMatch(review -> review.state() == ReviewState.CHANGES_REQUESTED);

            if (changesRequested) {
                blockers.add("A current review requests changes");
            }

            if (policy.requireResolvedConversations()) {
                boolean unresolvedGeneral = pullRequest.comments().stream()
                    .anyMatch(comment -> !comment.resolved());

                boolean unresolvedInline = pullRequest.reviews().stream()
                    .flatMap(review -> review.comments().stream())
                    .anyMatch(comment -> !comment.resolved());

                if (unresolvedGeneral || unresolvedInline) {
                    blockers.add("Review conversations remain unresolved");
                }
            }

            return new MergeDecision(blockers.isEmpty(), blockers);
        }

        void merge(
            PullRequest pullRequest,
            BranchProtection policy,
            String currentHeadSha,
            MergeStrategy strategy,
            boolean administrator
        ) {
            MergeDecision decision = evaluate(
                pullRequest, policy, currentHeadSha, administrator
            );

            if (!decision.eligible()) {
                throw new IllegalStateException(decision.describe());
            }

            // The strategy affects the resulting commit graph in a real VCS.
            // This domain model records the chosen strategy for the operation
            // while keeping commit-graph manipulation outside its scope.
            System.out.println("Merge strategy: " + strategy);
            pullRequest.markMerged();
        }
    }

    public static void main(String[] args) {
        Reviewer alice = new Reviewer("alice", true, true);
        Reviewer ben = new Reviewer("ben", true, true);

        BranchProtection policy = new BranchProtection(
            "main",
            2,
            Set.of("unit-tests", "security-scan"),
            true,
            true,
            true,
            true,
            true,
            true,
            true
        );

        PullRequest pr = new PullRequest(
            315,
            "Enforce webhook signature validation",
            "feature/webhook-validation",
            "main",
            "sha-a12",
            "sha-base-8",
            false
        );

        pr.requestReview(alice);
        pr.requestReview(ben);
        pr.recordCheck("unit-tests", true);
        pr.recordCheck("security-scan", true);

        pr.submitReview(new Review(
            alice,
            ReviewState.APPROVED,
            "sha-a12",
            List.of(new ReviewComment(
                "src/WebhookVerifier.java",
                72,
                "Reject empty signature headers.",
                true
            )),
            Instant.now()
        ));

        pr.submitReview(new Review(
            ben,
            ReviewState.APPROVED,
            "sha-a12",
            List.of(),
            Instant.now()
        ));

        pr.addComment(new ReviewComment(
            "docs/security.md",
            18,
            "Clarify how keys are rotated.",
            false
        ));

        GovernanceService service = new GovernanceService();
        System.out.println("PR #" + pr.number() + ": " + pr.title());
        System.out.println(service.evaluate(pr, policy, "sha-a12", false).describe());

        // Resolving a conversation satisfies a separate policy condition.
        PullRequest updated = pr;
        List<ReviewComment> originalComments = updated.comments();
        System.out.println("Comment snapshot size: " + originalComments.size());

        // Reconstruct the comment state through a dedicated replacement flow
        // in production; this sample closes and reopens to demonstrate state
        // transitions independently of review approval semantics.
        pr.close();
        try {
            pr.requestReview(alice);
        } catch (IllegalStateException ex) {
            System.out.println("Invalid transition rejected: " + ex.getMessage());
        }
        pr.reopen();
        System.out.println("State after reopening: " + pr.state());

        // Stale approval behavior is explicit when the source branch advances.
        pr.pushCommit("sha-b27", true);
        System.out.println(
            "Eligibility after source update: "
            + service.evaluate(pr, policy, "sha-b27", false).describe()
        );

        // The new source version must be reviewed before it can be merged.
        pr.submitReview(new Review(
            alice, ReviewState.APPROVED, "sha-b27", List.of(), Instant.now()
        ));
        pr.submitReview(new Review(
            ben, ReviewState.APPROVED, "sha-b27", List.of(), Instant.now()
        ));

        // A read-only computed property map provides controlled dynamic access.
        Map<String, String> repositoryProperties = Map.of(
            "owner", "platform",
            "defaultBranch", "main"
        );
        String requestedProperty = "defaultBranch";
        if (!repositoryProperties.containsKey(requestedProperty)) {
            throw new IllegalArgumentException("Unknown repository property");
        }
        System.out.println(
            "Computed property: " + repositoryProperties.get(requestedProperty)
        );

        // Java maps preserve the distinction between immutable snapshots and
        // mutable state; TreeMap makes exported dynamic keys deterministic.
        Map<String, Object> exported = new TreeMap<>();
        exported.put("number", pr.number());
        exported.put("state", pr.state().name());
        exported.put("sourceBranch", pr.sourceBranch());
        exported.put("targetBranch", pr.targetBranch());
        exported.put("reviewerCount", pr.reviews().size());
        exported.put("requestedReviewers", pr.requestedReviewers());
        System.out.println(exported.entrySet().stream()
            .map(entry -> entry.getKey() + "=" + entry.getValue())
            .collect(Collectors.joining(", ")));
    }
}
