import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.TreeSet;

/*
 * Enterprise repository governance with explicit error contracts.
 *
 * Compile:
 *     javac ErrorHandlingEnterprise.java
 *
 * Run:
 *     java ErrorHandlingEnterprise
 *
 * Requires Java 17 or later. No external dependencies.
 */
public class ErrorHandlingEnterprise {

    static class ApplicationException extends RuntimeException {
        ApplicationException(String message) {
            super(message);
        }

        ApplicationException(String message, Throwable cause) {
            super(message, cause);
        }
    }

    static final class ValidationException extends ApplicationException {
        ValidationException(String message) {
            super(message);
        }

        ValidationException(String message, Throwable cause) {
            super(message, cause);
        }
    }

    static final class NotFoundException extends ApplicationException {
        NotFoundException(String message) {
            super(message);
        }
    }

    static final class PolicyViolationException extends ApplicationException {
        PolicyViolationException(String message) {
            super(message);
        }
    }

    static final class InvalidTransitionException extends ApplicationException {
        InvalidTransitionException(String message) {
            super(message);
        }
    }

    enum PullRequestState {
        DRAFT, OPEN, CLOSED, MERGED
    }

    enum ReviewState {
        COMMENTED, APPROVED, CHANGES_REQUESTED, DISMISSED
    }

    enum CheckState {
        PENDING, PASSED, FAILED, CANCELLED
    }

    record Review(
            String reviewer,
            ReviewState state,
            String reviewedCommit,
            boolean eligibleReviewer
    ) {
        Review {
            requireText(reviewer, "Reviewer");
            Objects.requireNonNull(state, "Review state is required.");
            requireText(reviewedCommit, "Reviewed commit");
        }
    }

    record StatusCheck(String name, CheckState state, String commit) {
        StatusCheck {
            requireText(name, "Status check name");
            Objects.requireNonNull(state, "Check state is required.");
            requireText(commit, "Check commit");
        }
    }

    record BranchPolicy(
            String branch,
            int requiredApprovals,
            Set<String> requiredChecks,
            boolean requireResolvedConversations,
            boolean dismissStaleApprovals,
            boolean prohibitDirectPush,
            boolean prohibitForcePush,
            boolean prohibitDeletion,
            boolean administratorBypass
    ) {
        BranchPolicy {
            requireText(branch, "Protected branch");

            if (requiredApprovals < 0) {
                throw new ValidationException("Approval requirement cannot be negative.");
            }

            Objects.requireNonNull(requiredChecks, "Required checks cannot be null.");
            requiredChecks = Set.copyOf(requiredChecks);

            for (String check : requiredChecks) {
                requireText(check, "Required check name");
            }
        }
    }

    record Eligibility(boolean eligible, List<String> blockers) {
        Eligibility {
            blockers = List.copyOf(blockers);
        }
    }

    static final class PullRequest {
        private final int id;
        private final String title;
        private final String author;
        private final String sourceBranch;
        private final String targetBranch;
        private final List<Review> reviews = new ArrayList<>();
        private final Map<String, StatusCheck> checks = new HashMap<>();
        private PullRequestState state = PullRequestState.DRAFT;
        private String headCommit;
        private boolean mergeConflict;
        private int unresolvedConversations;

        PullRequest(
                int id,
                String title,
                String author,
                String sourceBranch,
                String targetBranch,
                String headCommit
        ) {
            if (id <= 0) {
                throw new ValidationException("Pull request ID must be positive.");
            }

            this.id = id;
            this.title = requireText(title, "Title");
            this.author = requireText(author, "Author");
            this.sourceBranch = requireText(sourceBranch, "Source branch");
            this.targetBranch = requireText(targetBranch, "Target branch");
            this.headCommit = requireText(headCommit, "Head commit");

            if (sourceBranch.equals(targetBranch)) {
                throw new ValidationException("Source and target branches must differ.");
            }
        }

        void open() {
            transition(PullRequestState.OPEN);
        }

        void close() {
            transition(PullRequestState.CLOSED);
        }

        void reopen() {
            transition(PullRequestState.OPEN);
        }

        void setMergeConflict(boolean value) {
            mergeConflict = value;
        }

        void setUnresolvedConversations(int count) {
            if (count < 0) {
                throw new ValidationException("Conversation count cannot be negative.");
            }
            unresolvedConversations = count;
        }

        void addReview(Review review) {
            Objects.requireNonNull(review, "Review is required.");

            // One effective review per reviewer keeps the example's policy
            // calculation unambiguous. Real systems preserve review history.
            reviews.removeIf(existing -> existing.reviewer().equals(review.reviewer()));
            reviews.add(review);
        }

        void recordCheck(StatusCheck check) {
            Objects.requireNonNull(check, "Status check is required.");
            checks.put(check.name(), check);
        }

        void updateHeadCommit(String newCommit) {
            requireText(newCommit, "New head commit");
            headCommit = newCommit;
            // Checks remain stored for audit purposes, but their old commit
            // no longer satisfies the current-head requirement.
        }

        private void transition(PullRequestState next) {
            boolean permitted = switch (state) {
                case DRAFT -> next == PullRequestState.OPEN
                        || next == PullRequestState.CLOSED;
                case OPEN -> next == PullRequestState.CLOSED;
                case CLOSED -> next == PullRequestState.OPEN;
                case MERGED -> false;
            };

            if (!permitted) {
                throw new InvalidTransitionException(
                        "Invalid transition from " + state + " to " + next + "."
                );
            }

            state = next;
        }

        void markMerged() {
            if (state != PullRequestState.OPEN) {
                throw new InvalidTransitionException("Only an open pull request can merge.");
            }
            state = PullRequestState.MERGED;
        }

        int id() {
            return id;
        }

        String title() {
            return title;
        }

        String author() {
            return author;
        }

        String targetBranch() {
            return targetBranch;
        }

        String headCommit() {
            return headCommit;
        }

        PullRequestState state() {
            return state;
        }

        boolean hasMergeConflict() {
            return mergeConflict;
        }

        int unresolvedConversations() {
            return unresolvedConversations;
        }

        List<Review> reviews() {
            return List.copyOf(reviews);
        }

        Map<String, StatusCheck> checks() {
            return Map.copyOf(checks);
        }
    }

    static final class GovernanceService {
        private final Map<Integer, PullRequest> requests = new HashMap<>();
        private final Map<String, BranchPolicy> policies = new HashMap<>();

        void registerPolicy(BranchPolicy policy) {
            Objects.requireNonNull(policy, "Policy is required.");
            policies.put(policy.branch(), policy);
        }

        void register(PullRequest request) {
            Objects.requireNonNull(request, "Pull request is required.");

            if (requests.putIfAbsent(request.id(), request) != null) {
                throw new ValidationException(
                        "Pull request ID already exists: " + request.id()
                );
            }
        }

        PullRequest find(int id) {
            PullRequest request = requests.get(id);
            if (request == null) {
                throw new NotFoundException("Pull request not found: " + id);
            }
            return request;
        }

        Eligibility evaluate(int id) {
            PullRequest request = find(id);
            List<String> blockers = new ArrayList<>();
            BranchPolicy policy = policies.get(request.targetBranch());

            if (policy == null) {
                blockers.add("No branch protection policy is registered.");
                return new Eligibility(false, blockers);
            }

            if (request.state() != PullRequestState.OPEN) {
                blockers.add("Pull request is not open.");
            }

            if (request.hasMergeConflict()) {
                blockers.add("Merge conflicts remain.");
            }

            Set<String> approvedReviewers = new HashSet<>();
            boolean changesRequested = false;

            for (Review review : request.reviews()) {
                if (!review.eligibleReviewer()
                        || review.reviewer().equals(request.author())) {
                    continue;
                }

                if (policy.dismissStaleApprovals()
                        && !review.reviewedCommit().equals(request.headCommit())) {
                    continue;
                }

                if (review.state() == ReviewState.CHANGES_REQUESTED) {
                    changesRequested = true;
                } else if (review.state() == ReviewState.APPROVED) {
                    approvedReviewers.add(review.reviewer());
                }
            }

            if (changesRequested) {
                blockers.add("An eligible reviewer requests changes.");
            }

            if (approvedReviewers.size() < policy.requiredApprovals()) {
                blockers.add(
                        "Eligible approvals: " + approvedReviewers.size()
                                + " of " + policy.requiredApprovals() + "."
                );
            }

            for (String requiredCheck : new TreeSet<>(policy.requiredChecks())) {
                StatusCheck check = request.checks().get(requiredCheck);

                if (check == null || !check.commit().equals(request.headCommit())) {
                    blockers.add("Required check is missing or stale: " + requiredCheck);
                } else if (check.state() != CheckState.PASSED) {
                    blockers.add(
                            "Required check " + requiredCheck + " is " + check.state() + "."
                    );
                }
            }

            if (policy.requireResolvedConversations()
                    && request.unresolvedConversations() > 0) {
                blockers.add(
                        request.unresolvedConversations()
                                + " review conversation(s) remain unresolved."
                );
            }

            return new Eligibility(blockers.isEmpty(), blockers);
        }

        void merge(int id) {
            PullRequest request = find(id);
            Eligibility eligibility = evaluate(id);

            if (!eligibility.eligible()) {
                throw new PolicyViolationException(
                        "Merge denied for PR #" + id + ": "
                                + String.join("; ", eligibility.blockers())
                );
            }

            request.markMerged();
        }
    }

    private static String requireText(String value, String field) {
        if (value == null || value.isBlank()) {
            throw new ValidationException(field + " must not be blank.");
        }
        return value;
    }

    private static void printEligibility(
            GovernanceService service,
            int id
    ) {
        Eligibility result = service.evaluate(id);
        System.out.println("\nPR #" + id + " eligible: " + result.eligible());

        for (String blocker : result.blockers()) {
            System.out.println("  Blocker: " + blocker);
        }
    }

    private static void runAssertions() {
        BranchPolicy policy = new BranchPolicy(
                "main",
                1,
                Set.of("build"),
                true,
                true,
                true,
                true,
                true,
                false
        );

        GovernanceService service = new GovernanceService();
        service.registerPolicy(policy);

        PullRequest request = new PullRequest(
                200,
                "Validate release artifacts",
                "author-one",
                "feature/release",
                "main",
                "commit-200"
        );
        request.open();
        request.addReview(new Review(
                "reviewer-one",
                ReviewState.APPROVED,
                "commit-200",
                true
        ));
        request.recordCheck(new StatusCheck(
                "build",
                CheckState.PASSED,
                "commit-200"
        ));
        service.register(request);

        if (!service.evaluate(200).eligible()) {
            throw new AssertionError("Expected eligible request.");
        }

        request.updateHeadCommit("commit-201");

        if (service.evaluate(200).eligible()) {
            throw new AssertionError("Stale check and approval must block the merge.");
        }

        boolean notFound = false;
        try {
            service.find(999);
        } catch (NotFoundException expected) {
            notFound = true;
        }

        if (!notFound) {
            throw new AssertionError("Missing request should throw NotFoundException.");
        }

        System.out.println("Enterprise governance assertions passed.");
    }

    public static void main(String[] args) {
        GovernanceService service = new GovernanceService();

        service.registerPolicy(new BranchPolicy(
                "main",
                2,
                Set.of("build", "unit-tests", "security-scan"),
                true,
                true,
                true,
                true,
                true,
                false
        ));

        PullRequest ready = new PullRequest(
                108,
                "Validate release configuration",
                "developer-alex",
                "feature/release-validation",
                "main",
                "commit-a91"
        );
        ready.open();
        ready.addReview(new Review(
                "reviewer-mira", ReviewState.APPROVED, "commit-a91", true
        ));
        ready.addReview(new Review(
                "reviewer-sam", ReviewState.APPROVED, "commit-a91", true
        ));
        ready.recordCheck(new StatusCheck(
                "build", CheckState.PASSED, "commit-a91"
        ));
        ready.recordCheck(new StatusCheck(
                "unit-tests", CheckState.PASSED, "commit-a91"
        ));
        ready.recordCheck(new StatusCheck(
                "security-scan", CheckState.PASSED, "commit-a91"
        ));
        service.register(ready);

        PullRequest blocked = new PullRequest(
                109,
                "Update deployment credentials",
                "developer-jules",
                "feature/credential-update",
                "main",
                "commit-b72"
        );
        blocked.open();
        blocked.setMergeConflict(true);
        blocked.setUnresolvedConversations(2);
        blocked.addReview(new Review(
                "reviewer-mira", ReviewState.APPROVED, "commit-b70", true
        ));
        blocked.addReview(new Review(
                "reviewer-sam", ReviewState.CHANGES_REQUESTED, "commit-b72", true
        ));
        blocked.addReview(new Review(
                "developer-jules", ReviewState.APPROVED, "commit-b72", true
        ));
        blocked.recordCheck(new StatusCheck(
                "build", CheckState.PASSED, "commit-b72"
        ));
        blocked.recordCheck(new StatusCheck(
                "unit-tests", CheckState.PENDING, "commit-b72"
        ));
        service.register(blocked);

        printEligibility(service, 108);
        printEligibility(service, 109);

        try {
            service.merge(109);
        } catch (PolicyViolationException error) {
            System.err.println("\nExpected policy rejection: " + error.getMessage());
        }

        try {
            service.merge(108);
            System.out.println("\nPR #108 merged successfully.");
        } catch (ApplicationException error) {
            System.err.println("Unexpected merge failure: " + error.getMessage());
        }

        try {
            service.find(999);
        } catch (NotFoundException error) {
            System.err.println("Expected lookup failure: " + error.getMessage());
        }

        try {
            PullRequest invalid = new PullRequest(
                    110, "Invalid branch request", "author", "main", "main", "commit-x"
            );
            service.register(invalid);
        } catch (ValidationException error) {
            System.err.println("Expected validation failure: " + error.getMessage());
        }

        runAssertions();
    }
}
