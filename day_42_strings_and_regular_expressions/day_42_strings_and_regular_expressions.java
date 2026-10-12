import java.time.Instant;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

public class RepositoryGovernanceDemo {

    enum PullRequestStatus {
        DRAFT, OPEN, CLOSED, MERGED
    }

    enum ReviewDecision {
        APPROVED, CHANGES_REQUESTED, COMMENTED, DISMISSED
    }

    enum CheckStatus {
        PENDING, SUCCESS, FAILURE, CANCELLED
    }

    enum MergeStrategy {
        MERGE_COMMIT, SQUASH, REBASE
    }

    record Commit(String sha, Instant committedAt, boolean mergeCommit) {
        Commit {
            Objects.requireNonNull(sha, "sha");
            Objects.requireNonNull(committedAt, "committedAt");
            if (!sha.matches("[a-f0-9]{7,40}")) {
                throw new IllegalArgumentException("Invalid commit SHA");
            }
        }
    }

    record ReviewComment(
            String author,
            String path,
            int line,
            String body,
            boolean resolved) {

        ReviewComment {
            Objects.requireNonNull(author, "author");
            Objects.requireNonNull(path, "path");
            Objects.requireNonNull(body, "body");

            if (line < 1) {
                throw new IllegalArgumentException("Comment line must be positive");
            }
            if (body.isBlank()) {
                throw new IllegalArgumentException("Review comment cannot be empty");
            }
        }
    }

    record Review(
            String reviewer,
            ReviewDecision decision,
            Instant submittedAt,
            String commitSha,
            List<ReviewComment> comments) {

        Review {
            Objects.requireNonNull(reviewer, "reviewer");
            Objects.requireNonNull(decision, "decision");
            Objects.requireNonNull(submittedAt, "submittedAt");
            Objects.requireNonNull(commitSha, "commitSha");
            comments = List.copyOf(comments);

            if (reviewer.isBlank()) {
                throw new IllegalArgumentException("Reviewer identity is required");
            }
        }
    }

    record StatusCheck(String name, CheckStatus status, String commitSha) {
        StatusCheck {
            Objects.requireNonNull(name, "name");
            Objects.requireNonNull(status, "status");
            Objects.requireNonNull(commitSha, "commitSha");

            if (name.isBlank()) {
                throw new IllegalArgumentException("Check name is required");
            }
        }
    }

    static final class BranchProtectionPolicy {
        private final String protectedBranch;
        private final int requiredApprovals;
        private final Set<String> eligibleReviewers;
        private final Set<String> requiredChecks;
        private final boolean requireResolvedConversations;
        private final boolean requireLinearHistory;
        private final boolean restrictDirectPushes;
        private final boolean prohibitForcePushes;
        private final boolean prohibitDeletion;
        private final boolean dismissStaleApprovals;
        private final boolean requireApprovalFromCodeOwner;

        BranchProtectionPolicy(
                String protectedBranch,
                int requiredApprovals,
                Set<String> eligibleReviewers,
                Set<String> requiredChecks,
                boolean requireResolvedConversations,
                boolean requireLinearHistory,
                boolean restrictDirectPushes,
                boolean prohibitForcePushes,
                boolean prohibitDeletion,
                boolean dismissStaleApprovals,
                boolean requireApprovalFromCodeOwner) {

            this.protectedBranch = Objects.requireNonNull(protectedBranch);
            if (requiredApprovals < 0) {
                throw new IllegalArgumentException("Approval count cannot be negative");
            }

            this.requiredApprovals = requiredApprovals;
            this.eligibleReviewers = Set.copyOf(eligibleReviewers);
            this.requiredChecks = Set.copyOf(requiredChecks);
            this.requireResolvedConversations = requireResolvedConversations;
            this.requireLinearHistory = requireLinearHistory;
            this.restrictDirectPushes = restrictDirectPushes;
            this.prohibitForcePushes = prohibitForcePushes;
            this.prohibitDeletion = prohibitDeletion;
            this.dismissStaleApprovals = dismissStaleApprovals;
            this.requireApprovalFromCodeOwner = requireApprovalFromCodeOwner;
        }
    }

    static final class PullRequest {
        private final int number;
        private final String title;
        private final String author;
        private final String sourceBranch;
        private final String targetBranch;
        private final Set<String> codeOwners;
        private final List<Commit> commits = new ArrayList<>();
        private final List<Review> reviews = new ArrayList<>();
        private final List<StatusCheck> checks = new ArrayList<>();
        private PullRequestStatus status;
        private String mergeBaseSha;
        private boolean baseBranchSynchronized;
        private boolean mergeConflict;
        private String mergedCommitSha;

        PullRequest(
                int number,
                String title,
                String author,
                String sourceBranch,
                String targetBranch,
                Set<String> codeOwners,
                PullRequestStatus initialStatus,
                String mergeBaseSha) {

            if (number <= 0) {
                throw new IllegalArgumentException("Pull request number must be positive");
            }

            this.number = number;
            this.title = requireNonBlank(title, "title");
            this.author = requireNonBlank(author, "author");
            this.sourceBranch = requireNonBlank(sourceBranch, "source branch");
            this.targetBranch = requireNonBlank(targetBranch, "target branch");
            if (sourceBranch.equals(targetBranch)) {
                throw new IllegalArgumentException("Source and target must differ");
            }

            this.codeOwners = Set.copyOf(codeOwners);
            this.status = Objects.requireNonNull(initialStatus);
            this.mergeBaseSha = requireNonBlank(mergeBaseSha, "merge base");
        }

        private static String requireNonBlank(String value, String field) {
            Objects.requireNonNull(value, field);
            if (value.isBlank()) {
                throw new IllegalArgumentException(field + " cannot be blank");
            }
            return value;
        }

        void addCommit(Commit commit) {
            ensureMutable();
            commits.add(Objects.requireNonNull(commit));
            baseBranchSynchronized = false;
        }

        void addReview(Review review) {
            ensureMutable();
            reviews.add(Objects.requireNonNull(review));
        }

        void addStatusCheck(StatusCheck check) {
            ensureMutable();
            checks.add(Objects.requireNonNull(check));
        }

        void synchronizeWithBase(String newMergeBaseSha) {
            ensureMutable();
            mergeBaseSha = requireNonBlank(newMergeBaseSha, "merge base");
            baseBranchSynchronized = true;
        }

        void setMergeConflict(boolean mergeConflict) {
            ensureMutable();
            this.mergeConflict = mergeConflict;
        }

        void markReadyForReview() {
            if (status != PullRequestStatus.DRAFT) {
                throw new IllegalStateException("Only draft pull requests can become ready");
            }
            status = PullRequestStatus.OPEN;
        }

        void reopen() {
            if (status != PullRequestStatus.CLOSED) {
                throw new IllegalStateException("Only closed pull requests can be reopened");
            }
            status = PullRequestStatus.OPEN;
        }

        void close() {
            if (status != PullRequestStatus.OPEN && status != PullRequestStatus.DRAFT) {
                throw new IllegalStateException("Only open or draft pull requests can be closed");
            }
            status = PullRequestStatus.CLOSED;
        }

        void markMerged(String mergeSha) {
            if (status != PullRequestStatus.OPEN) {
                throw new IllegalStateException("Only open pull requests can be merged");
            }
            mergedCommitSha = requireNonBlank(mergeSha, "merge SHA");
            status = PullRequestStatus.MERGED;
        }

        private void ensureMutable() {
            if (status == PullRequestStatus.MERGED || status == PullRequestStatus.CLOSED) {
                throw new IllegalStateException("Closed or merged pull request is immutable");
            }
        }
    }

    record Eligibility(boolean eligible, List<String> blockers) {
        Eligibility {
            blockers = List.copyOf(blockers);
        }
    }

    static final class MergeEligibilityService {
        private final BranchProtectionPolicy policy;

        MergeEligibilityService(BranchProtectionPolicy policy) {
            this.policy = Objects.requireNonNull(policy);
        }

        Eligibility evaluate(PullRequest pr) {
            List<String> blockers = new ArrayList<>();

            if (pr.status != PullRequestStatus.OPEN) {
                blockers.add("Pull request must be open");
            }
            if (!pr.targetBranch.equals(policy.protectedBranch)) {
                blockers.add("Target is not the configured protected branch");
            }
            if (pr.commits.isEmpty()) {
                blockers.add("No commits are present");
            }
            if (pr.mergeConflict) {
                blockers.add("Merge conflicts must be resolved");
            }
            if (!pr.baseBranchSynchronized) {
                blockers.add("Source branch has not been synchronized with the base");
            }
            if (policy.requireLinearHistory &&
                    pr.commits.stream().anyMatch(Commit::mergeCommit)) {
                blockers.add("Merge commit found under linear-history policy");
            }

            Map<String, Review> latestReviews = new HashMap<>();
            for (Review review : pr.reviews) {
                if (!policy.eligibleReviewers.contains(review.reviewer())) {
                    blockers.add("Ineligible reviewer: " + review.reviewer());
                    continue;
                }

                Review previous = latestReviews.get(review.reviewer());
                if (previous == null ||
                        review.submittedAt().isAfter(previous.submittedAt())) {
                    latestReviews.put(review.reviewer(), review);
                }
            }

            long approvals = latestReviews.values().stream()
                    .filter(review -> review.decision() == ReviewDecision.APPROVED)
                    .filter(review -> !policy.dismissStaleApprovals ||
                            pr.commits.stream().anyMatch(
                                    commit -> commit.sha().equals(review.commitSha())))
                    .count();

            boolean changesRequested = latestReviews.values().stream()
                    .anyMatch(review ->
                            review.decision() == ReviewDecision.CHANGES_REQUESTED);

            if (approvals < policy.requiredApprovals) {
                blockers.add("Approval threshold not met");
            }
            if (changesRequested) {
                blockers.add("Latest review requests changes");
            }

            if (policy.requireApprovalFromCodeOwner) {
                boolean ownerApproved = latestReviews.values().stream()
                        .anyMatch(review ->
                                pr.codeOwners.contains(review.reviewer()) &&
                                review.decision() == ReviewDecision.APPROVED);
                if (!ownerApproved) {
                    blockers.add("A code-owner approval is required");
                }
            }

            if (policy.requireResolvedConversations) {
                boolean unresolved = latestReviews.values().stream()
                        .flatMap(review -> review.comments().stream())
                        .anyMatch(comment -> !comment.resolved());
                if (unresolved) {
                    blockers.add("Review conversations remain unresolved");
                }
            }

            Map<String, StatusCheck> latestChecks = new HashMap<>();
            for (StatusCheck check : pr.checks) {
                latestChecks.put(check.name(), check);
            }

            for (String required : policy.requiredChecks) {
                StatusCheck check = latestChecks.get(required);
                if (check == null || check.status() != CheckStatus.SUCCESS) {
                    blockers.add("Required check missing or unsuccessful: " + required);
                }
            }

            return new Eligibility(blockers.isEmpty(), blockers);
        }
    }

    static final class RepositoryPolicyService {
        private final BranchProtectionPolicy policy;

        RepositoryPolicyService(BranchProtectionPolicy policy) {
            this.policy = policy;
        }

        void requireDirectPushAllowed(boolean administrator) {
            if (policy.restrictDirectPushes && administrator) {
                throw new SecurityException(
                        "Administrator must use an explicitly authorized bypass");
            }
            if (policy.restrictDirectPushes) {
                throw new SecurityException("Direct pushes are restricted");
            }
        }

        void requireForcePushAllowed() {
            if (policy.prohibitForcePushes) {
                throw new SecurityException("Force pushes are prohibited");
            }
        }

        void requireDeletionAllowed() {
            if (policy.prohibitDeletion) {
                throw new SecurityException("Protected branch deletion is prohibited");
            }
        }
    }

    private static final Pattern TITLE_PATTERN =
            Pattern.compile("[A-Za-z0-9][A-Za-z0-9 :._-]{4,119}");

    private static void printEligibility(
            PullRequest pr, MergeEligibilityService service) {

        Eligibility eligibility = service.evaluate(pr);
        System.out.printf(
                "%nPR #%d: %s%nState: %s%nMerge eligible: %s%n",
                pr.number, pr.title, pr.status, eligibility.eligible());

        for (String blocker : eligibility.blockers()) {
            System.out.println("  - " + blocker);
        }
    }

    private static Commit commit(String sha, boolean mergeCommit) {
        return new Commit(sha, Instant.parse("2026-10-12T08:30:00Z"), mergeCommit);
    }

    private static Review review(
            String reviewer,
            ReviewDecision decision,
            String commitSha,
            List<ReviewComment> comments) {

        return new Review(
                reviewer,
                decision,
                Instant.parse("2026-10-12T09:00:00Z"),
                commitSha,
                comments);
    }

    public static void main(String[] args) {
        BranchProtectionPolicy policy = new BranchProtectionPolicy(
                "main",
                2,
                Set.of("ana", "raj", "meera", "owner-lee"),
                Set.of("build", "unit-tests", "security-scan"),
                true,
                true,
                true,
                true,
                true,
                true,
                true);

        MergeEligibilityService eligibilityService =
                new MergeEligibilityService(policy);

        PullRequest valid = new PullRequest(
                184,
                "Improve supplier validation",
                "developer-kiran",
                "feature/supplier-validation",
                "main",
                Set.of("owner-lee"),
                PullRequestStatus.OPEN,
                "base-100");

        valid.addCommit(commit("a1b2c3d", false));
        valid.addCommit(commit("d4e5f6a", false));
        valid.synchronizeWithBase("base-101");

        valid.addReview(review(
                "ana", ReviewDecision.APPROVED, "a1b2c3d", List.of()));
        valid.addReview(review(
                "owner-lee", ReviewDecision.APPROVED, "d4e5f6a", List.of()));

        valid.addStatusCheck(new StatusCheck("build", CheckStatus.SUCCESS, "d4e5f6a"));
        valid.addStatusCheck(new StatusCheck("unit-tests", CheckStatus.SUCCESS, "d4e5f6a"));
        valid.addStatusCheck(new StatusCheck("security-scan", CheckStatus.SUCCESS, "d4e5f6a"));

        PullRequest blocked = new PullRequest(
                185,
                "Repair payment signature verification",
                "developer-ravi",
                "feature/payment-signature",
                "main",
                Set.of("owner-lee"),
                PullRequestStatus.OPEN,
                "base-100");

        blocked.addCommit(commit("e7f8a9b", false));
        blocked.synchronizeWithBase("base-101");
        blocked.addReview(review(
                "ana",
                ReviewDecision.CHANGES_REQUESTED,
                "e7f8a9b",
                List.of(new ReviewComment(
                        "ana",
                        "src/payment/SignatureVerifier.java",
                        42,
                        "Reject unsigned callbacks",
                        false))));

        blocked.addReview(review(
                "owner-lee", ReviewDecision.APPROVED, "e7f8a9b", List.of()));

        blocked.addStatusCheck(new StatusCheck("build", CheckStatus.SUCCESS, "e7f8a9b"));
        blocked.addStatusCheck(new StatusCheck("unit-tests", CheckStatus.FAILURE, "e7f8a9b"));
        blocked.addStatusCheck(new StatusCheck("security-scan", CheckStatus.SUCCESS, "e7f8a9b"));

        if (!TITLE_PATTERN.matcher(valid.title).matches()) {
            throw new IllegalArgumentException("Invalid pull request title");
        }

        printEligibility(valid, eligibilityService);
        printEligibility(blocked, eligibilityService);

        RepositoryPolicyService repositoryPolicy = new RepositoryPolicyService(policy);

        try {
            repositoryPolicy.requireDirectPushAllowed(false);
        } catch (SecurityException error) {
            System.out.println("\nDirect-push denial: " + error.getMessage());
        }

        try {
            repositoryPolicy.requireForcePushAllowed();
        } catch (SecurityException error) {
            System.out.println("Force-push denial: " + error.getMessage());
        }

        // An explicit state transition prevents merging a draft without first
        // moving it to the review-ready state.
        PullRequest draft = new PullRequest(
                186,
                "Document supplier API contract",
                "developer-meera",
                "docs/supplier-api",
                "main",
                Set.of(),
                PullRequestStatus.DRAFT,
                "base-100");

        try {
            draft.markMerged("f0e1d2c");
        } catch (IllegalStateException error) {
            System.out.println("Invalid transition: " + error.getMessage());
        }

        draft.markReadyForReview();
        draft.close();

        try {
            draft.markMerged("f0e1d2c");
        } catch (IllegalStateException error) {
            System.out.println("Closed PR cannot merge: " + error.getMessage());
        }

        // The merge strategy is a repository operation selected only after
        // eligibility has been established.
        MergeStrategy strategy = MergeStrategy.SQUASH;
        if (eligibilityService.evaluate(valid).eligible()) {
            valid.markMerged("f0e1d2c");
            System.out.println("PR #184 merged using " + strategy +
                    "; merge SHA recorded as " + valid.mergedCommitSha);
        }

        System.out.println("\nReview decisions: " +
                java.util.Arrays.stream(ReviewDecision.values())
                        .map(Enum::name)
                        .collect(Collectors.joining(", ")));
    }
}
