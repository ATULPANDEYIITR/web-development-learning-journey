import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.function.Predicate;
import java.util.stream.Collectors;

/**
 * Enterprise repository governance model.
 *
 * Demonstrates immutable policy configuration, validated domain objects,
 * prototype-like inheritance of defaults, review-state transitions, and
 * merge eligibility for protected release branches.
 */
public class RepositoryGovernance {

    enum ReviewState {
        COMMENTED,
        APPROVED,
        CHANGES_REQUESTED,
        DISMISSED
    }

    enum PullRequestState {
        OPEN,
        CLOSED,
        MERGED
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

    record ReviewDecision(
        String reviewer,
        String reviewedHead,
        ReviewState state,
        boolean codeOwner
    ) {
        ReviewDecision {
            if (reviewer == null || reviewer.isBlank()) {
                throw new IllegalArgumentException("Reviewer is required.");
            }
            if (reviewedHead == null || reviewedHead.isBlank()) {
                throw new IllegalArgumentException("Reviewed commit is required.");
            }
            Objects.requireNonNull(state, "Review state is required.");
        }
    }

    record StatusCheck(String name, CheckState state, String commit) {
        StatusCheck {
            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException("Check name is required.");
            }
            Objects.requireNonNull(state, "Check state is required.");
            if (commit == null || commit.isBlank()) {
                throw new IllegalArgumentException("Check commit is required.");
            }
        }
    }

    static final class BranchPolicy {
        private final String branchName;
        private final int requiredApprovals;
        private final Set<String> requiredChecks;
        private final Set<String> codeOwners;
        private final Set<MergeStrategy> permittedStrategies;
        private final boolean requireResolvedConversations;
        private final boolean dismissStaleApprovals;
        private final boolean requireLinearHistory;
        private final boolean disallowForcePush;
        private final boolean disallowDeletion;

        BranchPolicy(
            String branchName,
            int requiredApprovals,
            Set<String> requiredChecks,
            Set<String> codeOwners,
            Set<MergeStrategy> permittedStrategies,
            boolean requireResolvedConversations,
            boolean dismissStaleApprovals,
            boolean requireLinearHistory,
            boolean disallowForcePush,
            boolean disallowDeletion
        ) {
            if (branchName == null || branchName.isBlank()) {
                throw new IllegalArgumentException("Protected branch is required.");
            }
            if (requiredApprovals < 0) {
                throw new IllegalArgumentException("Approval threshold cannot be negative.");
            }

            this.branchName = branchName;
            this.requiredApprovals = requiredApprovals;
            this.requiredChecks = Set.copyOf(requiredChecks);
            this.codeOwners = Set.copyOf(codeOwners);
            this.permittedStrategies = Set.copyOf(permittedStrategies);
            this.requireResolvedConversations = requireResolvedConversations;
            this.dismissStaleApprovals = dismissStaleApprovals;
            this.requireLinearHistory = requireLinearHistory;
            this.disallowForcePush = disallowForcePush;
            this.disallowDeletion = disallowDeletion;
        }

        String branchName() {
            return branchName;
        }

        int requiredApprovals() {
            return requiredApprovals;
        }

        Set<String> requiredChecks() {
            return requiredChecks;
        }

        Set<String> codeOwners() {
            return codeOwners;
        }

        Set<MergeStrategy> permittedStrategies() {
            return permittedStrategies;
        }

        boolean requireResolvedConversations() {
            return requireResolvedConversations;
        }

        boolean dismissStaleApprovals() {
            return dismissStaleApprovals;
        }

        boolean requireLinearHistory() {
            return requireLinearHistory;
        }

        boolean disallowForcePush() {
            return disallowForcePush;
        }

        boolean disallowDeletion() {
            return disallowDeletion;
        }
    }

    static final class PullRequest {
        private final long id;
        private final String sourceBranch;
        private final String targetBranch;
        private final String author;
        private String headCommit;
        private String reviewedHead;
        private PullRequestState state = PullRequestState.OPEN;
        private boolean draft;
        private boolean hasConflicts;
        private boolean conversationsResolved;

        // A reviewer has one current decision. Replacing it models a new review
        // superseding the reviewer's earlier approval or change request.
        private final Map<String, ReviewDecision> reviews = new HashMap<>();
        private final Map<String, StatusCheck> checks = new HashMap<>();

        PullRequest(
            long id,
            String sourceBranch,
            String targetBranch,
            String author,
            String headCommit
        ) {
            if (id <= 0) {
                throw new IllegalArgumentException("Pull Request ID must be positive.");
            }
            if (sourceBranch == null || sourceBranch.isBlank()
                || targetBranch == null || targetBranch.isBlank()) {
                throw new IllegalArgumentException("Source and target branches are required.");
            }
            if (sourceBranch.equals(targetBranch)) {
                throw new IllegalArgumentException("Source and target branches must differ.");
            }
            if (author == null || author.isBlank()) {
                throw new IllegalArgumentException("Author is required.");
            }

            this.id = id;
            this.sourceBranch = sourceBranch;
            this.targetBranch = targetBranch;
            this.author = author;
            updateHead(headCommit);
            this.reviewedHead = headCommit;
        }

        void updateHead(String commit) {
            if (commit == null || commit.isBlank()) {
                throw new IllegalArgumentException("Head commit is required.");
            }

            headCommit = commit;

            // New commits can invalidate approvals and status checks.
            checks.clear();
        }

        void recordReview(ReviewDecision decision) {
            if (state != PullRequestState.OPEN) {
                throw new IllegalStateException("Reviews require an open Pull Request.");
            }
            if (decision.reviewer().equals(author)) {
                throw new IllegalArgumentException("Authors cannot approve their own changes.");
            }

            reviews.put(decision.reviewer(), decision);
        }

        void recordCheck(StatusCheck check) {
            if (state != PullRequestState.OPEN) {
                throw new IllegalStateException("Checks cannot be changed on a closed request.");
            }
            checks.put(check.name(), check);
        }

        void markReviewedHead(String commit) {
            if (commit == null || commit.isBlank()) {
                throw new IllegalArgumentException("Reviewed head is required.");
            }
            reviewedHead = commit;
        }

        void setDraft(boolean draft) {
            if (state != PullRequestState.OPEN) {
                throw new IllegalStateException("Only open requests can change draft state.");
            }
            this.draft = draft;
        }

        void setConflicts(boolean conflicts) {
            this.hasConflicts = conflicts;
        }

        void setConversationsResolved(boolean resolved) {
            this.conversationsResolved = resolved;
        }

        void close() {
            if (state != PullRequestState.OPEN) {
                throw new IllegalStateException("Only open requests can be closed.");
            }
            state = PullRequestState.CLOSED;
        }

        void reopen() {
            if (state != PullRequestState.CLOSED) {
                throw new IllegalStateException("Only closed requests can be reopened.");
            }
            state = PullRequestState.OPEN;
        }

        void markMerged() {
            if (state != PullRequestState.OPEN) {
                throw new IllegalStateException("Only open requests can be merged.");
            }
            state = PullRequestState.MERGED;
        }

        long id() {
            return id;
        }

        String sourceBranch() {
            return sourceBranch;
        }

        String targetBranch() {
            return targetBranch;
        }

        String author() {
            return author;
        }

        String headCommit() {
            return headCommit;
        }

        String reviewedHead() {
            return reviewedHead;
        }

        PullRequestState state() {
            return state;
        }

        boolean draft() {
            return draft;
        }

        boolean hasConflicts() {
            return hasConflicts;
        }

        boolean conversationsResolved() {
            return conversationsResolved;
        }

        Map<String, ReviewDecision> reviews() {
            return Map.copyOf(reviews);
        }

        Map<String, StatusCheck> checks() {
            return Map.copyOf(checks);
        }
    }

    record Eligibility(boolean allowed, List<String> violations) {
        Eligibility {
            violations = List.copyOf(violations);
        }
    }

    static final class MergeEligibilityService {
        private final BranchPolicy policy;

        MergeEligibilityService(BranchPolicy policy) {
            this.policy = Objects.requireNonNull(policy);
        }

        Eligibility evaluate(PullRequest request, MergeStrategy strategy) {
            List<String> violations = new ArrayList<>();

            if (request.state() != PullRequestState.OPEN) {
                violations.add("Pull Request must be open.");
            }
            if (request.draft()) {
                violations.add("Draft requests cannot be merged.");
            }
            if (!request.targetBranch().equals(policy.branchName())) {
                violations.add("Target branch does not match branch policy.");
            }
            if (request.hasConflicts()) {
                violations.add("Merge conflicts remain.");
            }
            if (policy.requireResolvedConversations() &&
                !request.conversationsResolved()) {
                violations.add("Review conversations remain unresolved.");
            }
            if (!policy.permittedStrategies().contains(strategy)) {
                violations.add("Merge strategy is not permitted.");
            }

            Map<String, ReviewDecision> reviews = request.reviews();

            Predicate<ReviewDecision> isCurrentApproval = review ->
                review.state() == ReviewState.APPROVED
                && (!policy.dismissStaleApprovals()
                    || review.reviewedHead().equals(request.headCommit()));

            List<ReviewDecision> approvals = reviews.values().stream()
                .filter(isCurrentApproval)
                .toList();

            long independentApprovals = approvals.stream()
                .filter(review -> !review.reviewer().equals(request.author()))
                .map(ReviewDecision::reviewer)
                .distinct()
                .count();

            if (independentApprovals < policy.requiredApprovals()) {
                violations.add("Insufficient current independent approvals.");
            }

            if (!policy.codeOwners().isEmpty()) {
                boolean codeOwnerApproved = approvals.stream().anyMatch(
                    review -> policy.codeOwners().contains(review.reviewer())
                        && review.codeOwner()
                );

                if (!codeOwnerApproved) {
                    violations.add("A designated code owner must approve.");
                }
            }

            Map<String, StatusCheck> checks = request.checks();

            for (String requiredName : policy.requiredChecks()) {
                StatusCheck check = checks.get(requiredName);

                if (check == null) {
                    violations.add("Required check is missing: " + requiredName);
                } else if (check.state() != CheckState.PASSED) {
                    violations.add("Required check is not passing: " + requiredName);
                } else if (!check.commit().equals(request.headCommit())) {
                    violations.add("Required check is stale: " + requiredName);
                }
            }

            return new Eligibility(violations.isEmpty(), violations);
        }

        void merge(PullRequest request, MergeStrategy strategy) {
            Eligibility result = evaluate(request, strategy);

            if (!result.allowed()) {
                throw new IllegalStateException(
                    "Merge blocked: " + String.join("; ", result.violations())
                );
            }

            // This transition models application state only. A real hosting
            // platform must perform the Git ref update atomically.
            request.markMerged();
        }
    }

    static void printEligibility(
        PullRequest request,
        MergeEligibilityService service,
        MergeStrategy strategy
    ) {
        Eligibility eligibility = service.evaluate(request, strategy);

        System.out.println("\nPull Request #" + request.id()
            + ": " + request.sourceBranch() + " -> " + request.targetBranch());

        if (eligibility.allowed()) {
            System.out.println("Merge eligible.");
        } else {
            eligibility.violations().forEach(
                violation -> System.out.println("Blocked: " + violation)
            );
        }
    }

    public static void main(String[] args) {
        BranchPolicy policy = new BranchPolicy(
            "main",
            2,
            Set.of("ci", "security"),
            Set.of("maya", "liam"),
            Set.of(MergeStrategy.SQUASH, MergeStrategy.REBASE),
            true,
            true,
            true,
            true,
            true
        );

        MergeEligibilityService service = new MergeEligibilityService(policy);

        PullRequest release = new PullRequest(
            108,
            "feature/audit-events",
            "main",
            "noah",
            "head-108"
        );

        release.setConversationsResolved(true);
        release.markReviewedHead("head-108");

        release.recordReview(new ReviewDecision(
            "maya", "head-108", ReviewState.APPROVED, true
        ));
        release.recordReview(new ReviewDecision(
            "liam", "head-108", ReviewState.APPROVED, true
        ));

        release.recordCheck(new StatusCheck(
            "ci", CheckState.PASSED, "head-108"
        ));
        release.recordCheck(new StatusCheck(
            "security", CheckState.PASSED, "head-108"
        ));

        printEligibility(release, service, MergeStrategy.SQUASH);
        service.merge(release, MergeStrategy.SQUASH);
        System.out.println("Final state: " + release.state());

        PullRequest stale = new PullRequest(
            109,
            "feature/retry-policy",
            "main",
            "noah",
            "head-109-new"
        );

        stale.setConversationsResolved(true);
        stale.recordReview(new ReviewDecision(
            "maya", "head-109-old", ReviewState.APPROVED, true
        ));
        stale.recordReview(new ReviewDecision(
            "liam", "head-109-old", ReviewState.APPROVED, true
        ));

        stale.recordCheck(new StatusCheck(
            "ci", CheckState.PASSED, "head-109-new"
        ));
        stale.recordCheck(new StatusCheck(
            "security", CheckState.PENDING, "head-109-new"
        ));

        printEligibility(stale, service, MergeStrategy.MERGE_COMMIT);

        try {
            service.merge(stale, MergeStrategy.MERGE_COMMIT);
        } catch (IllegalStateException exception) {
            System.out.println(exception.getMessage());
        }

        try {
            stale.recordReview(new ReviewDecision(
                "noah", "head-109-new", ReviewState.APPROVED, false
            ));
        } catch (IllegalArgumentException exception) {
            System.out.println("Self-approval blocked: " + exception.getMessage());
        }

        System.out.println(
            "\nPolicy sets are immutable snapshots. Pull Request state is mutable "
            + "through validated methods, while merge eligibility remains centralized."
        );
    }
}
