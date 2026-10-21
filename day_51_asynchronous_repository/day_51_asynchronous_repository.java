import java.time.Duration;
import java.util.ArrayList;
import java.util.EnumSet;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

/*
 * Enterprise repository governance model.
 *
 * CompletableFuture represents asynchronous CI and policy operations.
 * The domain model deliberately separates:
 *
 * Pull Request: change-proposal lifecycle
 * Code Review: evaluation of a changeset
 * Approval: an explicit review decision
 * Branch Protection: repository-level merge constraints
 */

public class RepositoryGovernanceDemo {

    enum PullRequestState {
        DRAFT, OPEN, CLOSED, MERGED
    }

    enum ReviewState {
        COMMENTED, CHANGES_REQUESTED, APPROVED, DISMISSED
    }

    enum CheckState {
        QUEUED, RUNNING, PASSED, FAILED
    }

    record Commit(String sha, String message) {
        Commit {
            if (sha == null || sha.isBlank()) {
                throw new IllegalArgumentException("Commit SHA is required");
            }
            if (message == null || message.isBlank()) {
                throw new IllegalArgumentException("Commit message is required");
            }
        }
    }

    record Review(
            String reviewer,
            ReviewState state,
            String reviewedCommit,
            List<String> comments) {

        Review {
            if (reviewer == null || reviewer.isBlank()) {
                throw new IllegalArgumentException("Reviewer is required");
            }
            comments = List.copyOf(comments == null ? List.of() : comments);
        }
    }

    static final class StatusCheck {
        private final String name;
        private volatile CheckState state = CheckState.QUEUED;

        StatusCheck(String name) {
            this.name = name;
        }

        String name() {
            return name;
        }

        CheckState state() {
            return state;
        }

        void running() {
            state = CheckState.RUNNING;
        }

        void complete(boolean passed) {
            state = passed ? CheckState.PASSED : CheckState.FAILED;
        }
    }

    record BranchProtectionPolicy(
            int requiredReviews,
            Set<String> requiredStatusChecks,
            boolean requireConversationResolution,
            boolean requireLinearHistory,
            boolean restrictDirectPush,
            boolean restrictForcePush,
            boolean restrictBranchDeletion) {

        BranchProtectionPolicy {
            if (requiredReviews < 0) {
                throw new IllegalArgumentException(
                        "Required reviews cannot be negative");
            }
            requiredStatusChecks = Set.copyOf(requiredStatusChecks);
        }
    }

    static final class PullRequest {
        private final int number;
        private final String sourceBranch;
        private final String targetBranch;
        private final List<Commit> commits = new ArrayList<>();
        private final List<Review> reviews = new ArrayList<>();
        private final Map<String, StatusCheck> checks = new HashMap<>();

        private PullRequestState state;
        private int unresolvedConversations;

        PullRequest(
                int number,
                String sourceBranch,
                String targetBranch,
                List<Commit> commits,
                boolean draft) {

            if (sourceBranch.equals(targetBranch)) {
                throw new IllegalArgumentException(
                        "Source and target branches must differ");
            }
            if (commits == null || commits.isEmpty()) {
                throw new IllegalArgumentException(
                        "A Pull Request needs at least one commit");
            }

            this.number = number;
            this.sourceBranch = sourceBranch;
            this.targetBranch = targetBranch;
            this.commits.addAll(commits);
            this.state = draft
                    ? PullRequestState.DRAFT
                    : PullRequestState.OPEN;
        }

        int number() {
            return number;
        }

        PullRequestState state() {
            return state;
        }

        String headSha() {
            return commits.get(commits.size() - 1).sha();
        }

        void markReady() {
            if (state != PullRequestState.DRAFT) {
                throw new IllegalStateException(
                        "Only draft Pull Requests can become ready");
            }
            state = PullRequestState.OPEN;
        }

        void addCheck(String name) {
            checks.put(name, new StatusCheck(name));
        }

        StatusCheck check(String name) {
            StatusCheck check = checks.get(name);
            if (check == null) {
                throw new IllegalArgumentException(
                        "Unknown status check: " + name);
            }
            return check;
        }

        Map<String, StatusCheck> checks() {
            return Map.copyOf(checks);
        }

        void addReview(
                String reviewer,
                ReviewState state,
                List<String> comments) {

            if (this.state != PullRequestState.OPEN) {
                throw new IllegalStateException(
                        "Review requires an open Pull Request");
            }

            reviews.add(
                    new Review(
                            reviewer,
                            state,
                            headSha(),
                            comments));
        }

        void addCommit(Commit commit) {
            if (state != PullRequestState.OPEN) {
                throw new IllegalStateException(
                        "Commit requires an open Pull Request");
            }

            commits.add(commit);

            // New commits invalidate approvals tied to the previous head.
            for (int i = 0; i < reviews.size(); i++) {
                Review review = reviews.get(i);

                if (review.state() == ReviewState.APPROVED) {
                    reviews.set(
                            i,
                            new Review(
                                    review.reviewer(),
                                    ReviewState.DISMISSED,
                                    review.reviewedCommit(),
                                    review.comments()));
                }
            }
        }

        List<Review> reviews() {
            return List.copyOf(reviews);
        }

        void openConversation() {
            unresolvedConversations++;
        }

        void resolveConversation() {
            if (unresolvedConversations == 0) {
                throw new IllegalStateException(
                        "No unresolved conversation exists");
            }
            unresolvedConversations--;
        }

        int unresolvedConversations() {
            return unresolvedConversations;
        }

        void markMerged() {
            if (state != PullRequestState.OPEN) {
                throw new IllegalStateException(
                        "Only open Pull Requests can be merged");
            }
            state = PullRequestState.MERGED;
        }
    }

    static final class MergeDecision {
        private final boolean eligible;
        private final List<String> failures;

        MergeDecision(boolean eligible, List<String> failures) {
            this.eligible = eligible;
            this.failures = List.copyOf(failures);
        }

        boolean eligible() {
            return eligible;
        }

        List<String> failures() {
            return failures;
        }
    }

    static final class GovernanceService {
        private final BranchProtectionPolicy policy;
        private final ExecutorService executor;

        GovernanceService(
                BranchProtectionPolicy policy,
                ExecutorService executor) {
            this.policy = policy;
            this.executor = executor;
        }

        void configureChecks(PullRequest pr) {
            policy.requiredStatusChecks()
                    .forEach(pr::addCheck);
        }

        CompletableFuture<Boolean> executeCheck(
                PullRequest pr,
                String checkName) {

            StatusCheck check = pr.check(checkName);

            return CompletableFuture.supplyAsync(
                    () -> {
                        check.running();

                        try {
                            Thread.sleep(
                                    checkName.equals("security-scan")
                                            ? 140
                                            : 80);
                        } catch (InterruptedException error) {
                            Thread.currentThread().interrupt();
                            check.complete(false);
                            throw new IllegalStateException(
                                    "Status check interrupted",
                                    error);
                        }

                        boolean passed =
                                !pr.headSha().isBlank();

                        check.complete(passed);
                        return passed;
                    },
                    executor);
        }

        CompletableFuture<Void> executeRequiredChecks(
                PullRequest pr) {

            List<CompletableFuture<Boolean>> futures =
                    policy.requiredStatusChecks()
                            .stream()
                            .map(name -> executeCheck(pr, name))
                            .toList();

            /*
             * allOf waits for independent asynchronous checks without
             * blocking the initiating workflow thread while they run.
             */
            return CompletableFuture.allOf(
                    futures.toArray(new CompletableFuture[0]));
        }

        MergeDecision evaluate(PullRequest pr) {
            List<String> failures = new ArrayList<>();

            if (pr.state() != PullRequestState.OPEN) {
                failures.add("Pull Request is not open");
            }

            for (String required : policy.requiredStatusChecks()) {
                StatusCheck check = pr.check(required);

                if (check.state() != CheckState.PASSED) {
                    failures.add(
                            "Required status check failed: " + required);
                }
            }

            Set<String> eligibleApprovers = new HashSet<>();

            for (Review review : pr.reviews()) {
                if (review.state() == ReviewState.APPROVED
                        && review.reviewedCommit().equals(pr.headSha())) {
                    eligibleApprovers.add(review.reviewer());
                }
            }

            if (eligibleApprovers.size() < policy.requiredReviews()) {
                failures.add(
                        "Required current approvals are missing");
            }

            if (policy.requireConversationResolution()
                    && pr.unresolvedConversations() > 0) {
                failures.add("Unresolved review conversations remain");
            }

            return new MergeDecision(
                    failures.isEmpty(),
                    failures);
        }

        void merge(PullRequest pr) {
            MergeDecision decision = evaluate(pr);

            if (!decision.eligible()) {
                throw new IllegalStateException(
                        "Merge rejected: "
                                + String.join(
                                        "; ",
                                        decision.failures()));
            }

            pr.markMerged();
        }
    }

    public static void main(String[] args) {
        ExecutorService executor = Executors.newFixedThreadPool(2);

        try {
            BranchProtectionPolicy policy =
                    new BranchProtectionPolicy(
                            2,
                            Set.of("unit-tests", "security-scan"),
                            true,
                            true,
                            true,
                            true,
                            true);

            GovernanceService governance =
                    new GovernanceService(policy, executor);

            PullRequest pr =
                    new PullRequest(
                            501,
                            "feature/enterprise-governance",
                            "main",
                            List.of(
                                    new Commit(
                                            "e501",
                                            "Implement governance service"),
                                    new Commit(
                                            "e502",
                                            "Add asynchronous CI workflow")),
                            true);

            governance.configureChecks(pr);
            pr.markReady();

            pr.addReview(
                    "alice",
                    ReviewState.APPROVED,
                    List.of("Review completed against current head"));

            pr.addReview(
                    "bob",
                    ReviewState.APPROVED,
                    List.of("Policy evaluation is correct"));

            pr.openConversation();

            CompletableFuture<Void> checks =
                    governance.executeRequiredChecks(pr);

            checks.orTimeout(2, TimeUnit.SECONDS).join();

            MergeDecision blocked =
                    governance.evaluate(pr);

            System.out.println(
                    "Eligible before conversation resolution: "
                            + blocked.eligible());

            blocked.failures().forEach(
                    failure -> System.out.println(" - " + failure));

            pr.resolveConversation();

            MergeDecision ready =
                    governance.evaluate(pr);

            System.out.println(
                    "\nEligible after conversation resolution: "
                            + ready.eligible());

            if (ready.eligible()) {
                governance.merge(pr);
                System.out.println(
                        "Pull Request #" + pr.number() + " merged");
            }

            /*
             * Demonstrate stale approval behavior after a new changeset.
             */
            pr = new PullRequest(
                    502,
                    "feature/stale-approval",
                    "main",
                    List.of(
                            new Commit(
                                    "s501",
                                    "Initial repository change")),
                    false);

            governance.configureChecks(pr);
            pr.addReview(
                    "alice",
                    ReviewState.APPROVED,
                    List.of());

            pr.addCommit(
                    new Commit(
                            "s502",
                            "Modify implementation after review"));

            MergeDecision stale =
                    governance.evaluate(pr);

            System.out.println(
                    "\nAfter the Pull Request head changes:");
            stale.failures().forEach(
                    failure -> System.out.println(" - " + failure));

        } finally {
            executor.shutdown();
            try {
                if (!executor.awaitTermination(
                        Duration.ofSeconds(2).toMillis(),
                        TimeUnit.MILLISECONDS)) {
                    executor.shutdownNow();
                }
            } catch (InterruptedException error) {
                executor.shutdownNow();
                Thread.currentThread().interrupt();
            }
        }
    }
}
