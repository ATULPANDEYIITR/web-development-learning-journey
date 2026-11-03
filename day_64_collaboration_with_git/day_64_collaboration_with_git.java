import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.concurrent.atomic.AtomicLong;
import java.util.stream.Collectors;

public class Main {

    enum PullRequestState {
        DRAFT, OPEN, CLOSED, MERGED
    }

    enum ReviewState {
        APPROVED, CHANGES_REQUESTED, COMMENTED, DISMISSED
    }

    enum CheckState {
        PENDING, PASSED, FAILED, CANCELLED
    }

    enum MergeStrategy {
        MERGE_COMMIT, SQUASH, REBASE
    }

    static final class GovernanceException extends RuntimeException {
        GovernanceException(String message) {
            super(message);
        }
    }

    record Commit(
        String sha,
        List<String> parents,
        String message,
        Instant createdAt
    ) {
        Commit {
            Objects.requireNonNull(sha);
            parents = List.copyOf(parents);
            Objects.requireNonNull(message);
            Objects.requireNonNull(createdAt);
        }
    }

    record Reviewer(
        String username,
        boolean active,
        boolean canReview,
        boolean administrator,
        Set<String> roles
    ) {
        Reviewer {
            if (username == null || username.isBlank()) {
                throw new IllegalArgumentException("Reviewer username is required.");
            }
            roles = Set.copyOf(roles);
        }
    }

    record ReviewEvent(
        long id,
        String reviewer,
        ReviewState state,
        String reviewedHead,
        Instant submittedAt
    ) {
        ReviewEvent {
            Objects.requireNonNull(reviewer);
            Objects.requireNonNull(state);
            Objects.requireNonNull(reviewedHead);
            Objects.requireNonNull(submittedAt);
        }
    }

    record StatusCheck(
        String name,
        String head,
        CheckState state,
        String details,
        Instant recordedAt
    ) {
        StatusCheck {
            Objects.requireNonNull(name);
            Objects.requireNonNull(head);
            Objects.requireNonNull(state);
            Objects.requireNonNull(details);
            Objects.requireNonNull(recordedAt);
        }
    }

    record ReviewThread(
        String id,
        String filePath,
        int line,
        boolean resolved,
        String resolvedBy
    ) {
        ReviewThread {
            if (id == null || id.isBlank()) {
                throw new IllegalArgumentException("Thread identifier is required.");
            }
            validatePath(filePath);
            if (line < 1) {
                throw new IllegalArgumentException("Thread line must be positive.");
            }
        }

        ReviewThread resolve(String actor) {
            if (actor == null || actor.isBlank()) {
                throw new IllegalArgumentException("Resolver is required.");
            }
            return new ReviewThread(id, filePath, line, true, actor);
        }
    }

    record BranchProtectionPolicy(
        boolean requirePullRequest,
        int minimumApprovals,
        Set<String> requiredChecks,
        boolean requireConversationResolution,
        boolean requireLinearHistory,
        boolean allowMergeCommit,
        boolean allowSquash,
        boolean allowRebase,
        boolean allowDirectPush,
        boolean allowForcePush,
        boolean prohibitBranchDeletion,
        boolean allowAdministratorBypass,
        Set<String> eligibleReviewerRoles
    ) {
        BranchProtectionPolicy {
            if (minimumApprovals < 0) {
                throw new IllegalArgumentException("Minimum approvals cannot be negative.");
            }
            requiredChecks = Set.copyOf(requiredChecks);
            eligibleReviewerRoles = Set.copyOf(eligibleReviewerRoles);
        }

        boolean permits(MergeStrategy strategy) {
            return switch (strategy) {
                case MERGE_COMMIT -> allowMergeCommit;
                case SQUASH -> allowSquash;
                case REBASE -> allowRebase;
            };
        }
    }

    record EligibilityResult(
        boolean eligible,
        int currentApprovals,
        List<String> failures,
        boolean administratorBypass
    ) {
        EligibilityResult {
            failures = List.copyOf(failures);
        }
    }

    static final class Branch {
        private final String name;
        private String head;
        private final boolean protectedBranch;
        private boolean deleted;

        Branch(String name, String head, boolean protectedBranch) {
            if (name == null || name.isBlank() || head == null || head.isBlank()) {
                throw new IllegalArgumentException("Branch name and head are required.");
            }
            this.name = name;
            this.head = head;
            this.protectedBranch = protectedBranch;
        }

        String name() {
            return name;
        }

        String head() {
            return head;
        }

        boolean protectedBranch() {
            return protectedBranch;
        }

        boolean deleted() {
            return deleted;
        }

        void setHead(String head) {
            if (head == null || head.isBlank()) {
                throw new IllegalArgumentException("Branch head cannot be empty.");
            }
            this.head = head;
        }

        void markDeleted() {
            deleted = true;
        }
    }

    static final class PullRequest {
        private final long id;
        private final int number;
        private final String author;
        private final String sourceBranch;
        private final String targetBranch;
        private final String baseHeadAtOpen;
        private String baseHeadAtSync;
        private String sourceHead;
        private PullRequestState state;
        private boolean draft;

        private final List<ReviewEvent> reviews = new ArrayList<>();
        private final Map<String, ReviewThread> threads = new LinkedHashMap<>();
        private final Map<String, StatusCheck> checks = new HashMap<>();
        private MergeStrategy mergeStrategy;
        private String mergedCommit;

        PullRequest(
            long id,
            int number,
            String author,
            String sourceBranch,
            String targetBranch,
            String sourceHead,
            String baseHead,
            boolean draft
        ) {
            if (number <= 0 || author == null || author.isBlank()) {
                throw new IllegalArgumentException("Invalid Pull Request identity.");
            }
            if (sourceBranch.equals(targetBranch)) {
                throw new IllegalArgumentException("Source and target branches must differ.");
            }

            this.id = id;
            this.number = number;
            this.author = author;
            this.sourceBranch = sourceBranch;
            this.targetBranch = targetBranch;
            this.sourceHead = sourceHead;
            this.baseHeadAtOpen = baseHead;
            this.baseHeadAtSync = baseHead;
            this.draft = draft;
            this.state = draft ? PullRequestState.DRAFT : PullRequestState.OPEN;
        }

        long id() {
            return id;
        }

        int number() {
            return number;
        }

        String author() {
            return author;
        }

        String sourceBranch() {
            return sourceBranch;
        }

        String targetBranch() {
            return targetBranch;
        }

        String sourceHead() {
            return sourceHead;
        }

        String baseHeadAtOpen() {
            return baseHeadAtOpen;
        }

        String baseHeadAtSync() {
            return baseHeadAtSync;
        }

        PullRequestState state() {
            return state;
        }

        boolean draft() {
            return draft;
        }

        List<ReviewEvent> reviews() {
            return List.copyOf(reviews);
        }

        Map<String, ReviewThread> threads() {
            return Map.copyOf(threads);
        }

        Map<String, StatusCheck> checks() {
            return Map.copyOf(checks);
        }

        void markReady() {
            if (state != PullRequestState.DRAFT) {
                throw new GovernanceException("Only a draft Pull Request can become ready.");
            }
            state = PullRequestState.OPEN;
            draft = false;
        }

        void close() {
            if (state != PullRequestState.OPEN && state != PullRequestState.DRAFT) {
                throw new GovernanceException("Only an active Pull Request can be closed.");
            }
            state = PullRequestState.CLOSED;
        }

        void reopen() {
            if (state != PullRequestState.CLOSED) {
                throw new GovernanceException("Only a closed Pull Request can be reopened.");
            }
            state = PullRequestState.OPEN;
            draft = false;
        }

        void updateSourceHead(String newHead) {
            if (state != PullRequestState.OPEN && state != PullRequestState.DRAFT) {
                throw new GovernanceException("A terminal Pull Request cannot change its source.");
            }
            sourceHead = newHead;
        }

        void synchronizeBase(String newBaseHead) {
            baseHeadAtSync = newBaseHead;
        }

        void addReview(ReviewEvent review) {
            reviews.add(review);
        }

        void addThread(ReviewThread thread) {
            if (threads.putIfAbsent(thread.id(), thread) != null) {
                throw new GovernanceException("Duplicate review thread: " + thread.id());
            }
        }

        void resolveThread(String threadId, String actor) {
            ReviewThread thread = threads.get(threadId);
            if (thread == null) {
                throw new GovernanceException("Review thread does not exist: " + threadId);
            }
            threads.put(threadId, thread.resolve(actor));
        }

        void recordCheck(StatusCheck check) {
            checks.put(check.head() + ":" + check.name(), check);
        }

        void markMerged(MergeStrategy strategy, String commitSha) {
            if (state != PullRequestState.OPEN || draft) {
                throw new GovernanceException("Only an open, ready Pull Request can be merged.");
            }
            state = PullRequestState.MERGED;
            mergeStrategy = strategy;
            mergedCommit = commitSha;
        }
    }

    static final class RepositoryService {
        private final String repositoryName;
        private final Map<String, Branch> branches = new HashMap<>();
        private final Map<String, Reviewer> reviewers = new HashMap<>();
        private final Map<Long, PullRequest> pullRequests = new HashMap<>();
        private final Map<String, BranchProtectionPolicy> protectionPolicies = new HashMap<>();
        private final AtomicLong ids = new AtomicLong(0);
        private final AtomicLong reviewIds = new AtomicLong(0);
        private final AtomicLong commitIds = new AtomicLong(100);

        RepositoryService(String repositoryName, String initialHead) {
            if (repositoryName == null || repositoryName.isBlank()) {
                throw new IllegalArgumentException("Repository name is required.");
            }
            this.repositoryName = repositoryName;
            branches.put("main", new Branch("main", initialHead, true));
        }

        void registerReviewer(Reviewer reviewer) {
            reviewers.put(reviewer.username(), reviewer);
        }

        void configureProtection(
            String branchName,
            BranchProtectionPolicy policy
        ) {
            requireBranch(branchName);
            protectionPolicies.put(branchName, policy);
        }

        Branch requireBranch(String name) {
            Branch branch = branches.get(name);
            if (branch == null || branch.deleted()) {
                throw new GovernanceException("Branch does not exist: " + name);
            }
            return branch;
        }

        PullRequest requirePullRequest(long id) {
            PullRequest pr = pullRequests.get(id);
            if (pr == null) {
                throw new GovernanceException("Pull Request does not exist: " + id);
            }
            return pr;
        }

        void createBranch(String name, String from) {
            requireBranch(from);
            if (name == null || name.isBlank() || branches.containsKey(name)) {
                throw new GovernanceException("Branch name is invalid or already used.");
            }
            branches.put(name, new Branch(name, requireBranch(from).head(), false));
        }

        PullRequest openPullRequest(
            int number,
            String author,
            String source,
            String target,
            boolean draft
        ) {
            Branch sourceBranch = requireBranch(source);
            Branch targetBranch = requireBranch(target);

            boolean duplicate = pullRequests.values().stream()
                .anyMatch(pr -> pr.number() == number);
            if (duplicate) {
                throw new GovernanceException("Pull Request number must be unique.");
            }

            long id = ids.incrementAndGet();
            PullRequest pr = new PullRequest(
                id,
                number,
                author,
                source,
                target,
                sourceBranch.head(),
                targetBranch.head(),
                draft
            );
            pullRequests.put(id, pr);
            return pr;
        }

        void markReady(long prId) {
            requirePullRequest(prId).markReady();
        }

        void closePullRequest(long prId) {
            requirePullRequest(prId).close();
        }

        void reopenPullRequest(long prId) {
            requirePullRequest(prId).reopen();
        }

        void advanceSourceHead(String branchName, String newHead) {
            Branch branch = requireBranch(branchName);
            if (branch.protectedBranch()) {
                throw new GovernanceException("Protected branches cannot be advanced directly.");
            }

            branch.setHead(newHead);
            pullRequests.values().stream()
                .filter(pr -> pr.sourceBranch().equals(branchName))
                .filter(pr -> pr.state() == PullRequestState.OPEN ||
                              pr.state() == PullRequestState.DRAFT)
                .forEach(pr -> pr.updateSourceHead(newHead));
        }

        void advanceTargetBranch(String branchName, String newHead) {
            Branch branch = requireBranch(branchName);
            if (branch.protectedBranch()) {
                throw new GovernanceException("Protected target branches require a governed merge.");
            }
            branch.setHead(newHead);
        }

        void submitReview(
            long prId,
            String reviewerName,
            ReviewState state
        ) {
            PullRequest pr = requirePullRequest(prId);
            Reviewer reviewer = reviewers.get(reviewerName);

            if (reviewer == null || !reviewer.active() || !reviewer.canReview()) {
                throw new GovernanceException("Reviewer is not active or lacks review permission.");
            }
            if (reviewerName.equals(pr.author())) {
                throw new GovernanceException("An author cannot review their own Pull Request.");
            }
            if (pr.state() != PullRequestState.OPEN || pr.draft()) {
                throw new GovernanceException("Reviews require an open, non-draft Pull Request.");
            }
            if (state == ReviewState.DISMISSED) {
                throw new GovernanceException("Dismissals must reference an existing review.");
            }

            pr.addReview(new ReviewEvent(
                reviewIds.incrementAndGet(),
                reviewerName,
                state,
                pr.sourceHead(),
                Instant.now()
            ));
        }

        void dismissLatestReview(long prId, String reviewerName) {
            PullRequest pr = requirePullRequest(prId);
            ReviewEvent latest = latestReviews(pr).get(reviewerName);
            if (latest == null) {
                throw new GovernanceException("No review exists for this reviewer.");
            }

            pr.addReview(new ReviewEvent(
                reviewIds.incrementAndGet(),
                reviewerName,
                ReviewState.DISMISSED,
                latest.reviewedHead(),
                Instant.now()
            ));
        }

        void addReviewThread(
            long prId,
            String threadId,
            String path,
            int line
        ) {
            requirePullRequest(prId).addThread(
                new ReviewThread(threadId, path, line, false, null)
            );
        }

        void resolveReviewThread(long prId, String threadId, String actor) {
            requirePullRequest(prId).resolveThread(threadId, actor);
        }

        void recordStatusCheck(
            long prId,
            String name,
            CheckState state,
            String details
        ) {
            PullRequest pr = requirePullRequest(prId);
            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException("Status-check name is required.");
            }

            pr.recordCheck(new StatusCheck(
                name,
                pr.sourceHead(),
                state,
                details == null ? "" : details,
                Instant.now()
            ));
        }

        Map<String, ReviewEvent> latestReviews(PullRequest pr) {
            return pr.reviews().stream()
                .sorted(Comparator.comparingLong(ReviewEvent::id))
                .collect(Collectors.toMap(
                    ReviewEvent::reviewer,
                    review -> review,
                    (earlier, later) -> later,
                    LinkedHashMap::new
                ));
        }

        boolean isEligibleReviewer(
            String username,
            PullRequest pr,
            BranchProtectionPolicy policy
        ) {
            Reviewer reviewer = reviewers.get(username);
            if (
                reviewer == null ||
                !reviewer.active() ||
                !reviewer.canReview() ||
                username.equals(pr.author())
            ) {
                return false;
            }

            return policy.eligibleReviewerRoles().isEmpty() ||
                reviewer.roles().stream().anyMatch(policy.eligibleReviewerRoles()::contains);
        }

        EligibilityResult evaluateMerge(
            long prId,
            MergeStrategy strategy,
            String actor
        ) {
            PullRequest pr = requirePullRequest(prId);
            Branch source = requireBranch(pr.sourceBranch());
            Branch target = requireBranch(pr.targetBranch());

            BranchProtectionPolicy policy = protectionPolicies.get(pr.targetBranch());
            if (policy == null) {
                throw new GovernanceException("Target branch has no configured protection policy.");
            }

            List<String> failures = new ArrayList<>();

            if (pr.state() != PullRequestState.OPEN || pr.draft()) {
                failures.add("Pull Request must be open and ready.");
            }
            if (!source.head().equals(pr.sourceHead())) {
                failures.add("Pull Request source head is not current.");
            }
            if (!target.head().equals(pr.baseHeadAtSync())) {
                failures.add("Target branch advanced; synchronize the base branch.");
            }

            Reviewer actorRecord = reviewers.get(actor);
            boolean bypass = actorRecord != null &&
                actorRecord.active() &&
                actorRecord.administrator() &&
                policy.allowAdministratorBypass();

            Map<String, ReviewEvent> latest = latestReviews(pr);
            long approvals = latest.values().stream()
                .filter(review -> review.state() == ReviewState.APPROVED)
                .filter(review -> review.reviewedHead().equals(pr.sourceHead()))
                .filter(review -> isEligibleReviewer(review.reviewer(), pr, policy))
                .count();

            if (!bypass) {
                if (approvals < policy.minimumApprovals()) {
                    failures.add(
                        "Insufficient current approvals: " + approvals +
                        "/" + policy.minimumApprovals()
                    );
                }

                boolean changesRequested = latest.values().stream()
                    .anyMatch(review ->
                        review.state() == ReviewState.CHANGES_REQUESTED &&
                        review.reviewedHead().equals(pr.sourceHead()) &&
                        isEligibleReviewer(review.reviewer(), pr, policy)
                    );

                if (changesRequested) {
                    failures.add("A current eligible review requests changes.");
                }

                for (String requiredCheck : policy.requiredChecks()) {
                    StatusCheck check = pr.checks().get(
                        pr.sourceHead() + ":" + requiredCheck
                    );
                    if (check == null || check.state() != CheckState.PASSED) {
                        failures.add(
                            "Required check has not passed on current head: " +
                            requiredCheck
                        );
                    }
                }

                if (policy.requireConversationResolution()) {
                    boolean unresolved = pr.threads().values().stream()
                        .anyMatch(thread -> !thread.resolved());
                    if (unresolved) {
                        failures.add("Review conversations remain unresolved.");
                    }
                }

                if (!policy.permits(strategy)) {
                    failures.add("Selected merge strategy is not permitted.");
                }
                if (
                    policy.requireLinearHistory() &&
                    strategy == MergeStrategy.MERGE_COMMIT
                ) {
                    failures.add("Merge commits violate the linear-history requirement.");
                }
            }

            return new EligibilityResult(
                failures.isEmpty(),
                Math.toIntExact(approvals),
                failures,
                bypass
            );
        }

        String mergePullRequest(
            long prId,
            MergeStrategy strategy,
            String actor
        ) {
            EligibilityResult result = evaluateMerge(prId, strategy, actor);
            if (!result.eligible()) {
                throw new GovernanceException(
                    "Merge blocked: " + String.join("; ", result.failures())
                );
            }

            PullRequest pr = requirePullRequest(prId);
            Branch target = requireBranch(pr.targetBranch());
            String newHead = "enterprise-merge-" + commitIds.incrementAndGet();

            // The service models the merge decision and branch state transition.
            // Git object construction and remote ref updates belong to a Git host.
            target.setHead(newHead);
            pr.markMerged(strategy, newHead);
            return newHead;
        }

        void directPush(String branchName, String newHead, boolean force) {
            Branch branch = requireBranch(branchName);
            BranchProtectionPolicy policy = protectionPolicies.get(branchName);

            if (branch.protectedBranch()) {
                if (
                    policy == null ||
                    policy.requirePullRequest() ||
                    !policy.allowDirectPush()
                ) {
                    throw new GovernanceException("Direct push is blocked by branch protection.");
                }
                if (force && !policy.allowForcePush()) {
                    throw new GovernanceException("Force push is prohibited.");
                }
            }

            branch.setHead(newHead);
        }

        void deleteBranch(String branchName) {
            Branch branch = requireBranch(branchName);
            if (branchName.equals("main")) {
                throw new GovernanceException("Default branch deletion is prohibited.");
            }

            BranchProtectionPolicy policy = protectionPolicies.get(branchName);
            if (
                branch.protectedBranch() &&
                policy != null &&
                policy.prohibitBranchDeletion()
            ) {
                throw new GovernanceException("Protected branch deletion is prohibited.");
            }

            branch.markDeleted();
        }

        String repositoryName() {
            return repositoryName;
        }

        Branch branch(String name) {
            return requireBranch(name);
        }
    }

    static void validatePath(String path) {
        if (path == null || path.isBlank() ||
            path.startsWith("/") || path.contains("\\")) {
            throw new IllegalArgumentException("Invalid repository path.");
        }

        for (String part : path.split("/")) {
            if (part.isBlank() || part.equals(".") || part.equals("..")) {
                throw new IllegalArgumentException("Unsafe repository path.");
            }
        }
    }

    public static void main(String[] args) {
        try {
            RepositoryService service = new RepositoryService(
                "enterprise-orders",
                "commit-main-001"
            );

            service.registerReviewer(new Reviewer(
                "alice", true, true, true, Set.of("maintainer")
            ));
            service.registerReviewer(new Reviewer(
                "bob", true, true, false, Set.of("senior-developer")
            ));
            service.registerReviewer(new Reviewer(
                "carol", true, true, false, Set.of("developer")
            ));
            service.registerReviewer(new Reviewer(
                "eve", true, false, false, Set.of("viewer")
            ));

            BranchProtectionPolicy policy = new BranchProtectionPolicy(
                true,
                2,
                Set.of("unit-tests", "dependency-audit"),
                true,
                true,
                false,
                true,
                true,
                false,
                false,
                true,
                false,
                Set.of("senior-developer", "developer", "maintainer")
            );

            service.configureProtection("main", policy);
            service.createBranch("feature/order-controls", "main");

            PullRequest pr = service.openPullRequest(
                310,
                "alice",
                "feature/order-controls",
                "main",
                true
            );

            service.markReady(pr.id());
            service.addReviewThread(
                pr.id(),
                "thread-42",
                "src/order/OrderService.java",
                88
            );

            service.submitReview(pr.id(), "bob", ReviewState.APPROVED);
            service.submitReview(pr.id(), "carol", ReviewState.APPROVED);
            service.recordStatusCheck(
                pr.id(), "unit-tests", CheckState.PASSED, "All tests passed."
            );
            service.recordStatusCheck(
                pr.id(), "dependency-audit", CheckState.PASSED, "No blocking advisories."
            );

            // A new commit invalidates approvals and checks on the previous head.
            service.advanceSourceHead(
                "feature/order-controls",
                "commit-feature-002"
            );

            EligibilityResult stale = service.evaluateMerge(
                pr.id(),
                MergeStrategy.SQUASH,
                "alice"
            );

            System.out.println("Eligibility after source advancement: " + stale.eligible());
            stale.failures().forEach(reason -> System.out.println(" - " + reason));

            service.submitReview(pr.id(), "bob", ReviewState.APPROVED);
            service.submitReview(pr.id(), "carol", ReviewState.APPROVED);
            service.recordStatusCheck(
                pr.id(), "unit-tests", CheckState.PASSED, "Current head passed."
            );
            service.recordStatusCheck(
                pr.id(), "dependency-audit", CheckState.PASSED, "Current head passed."
            );
            service.resolveReviewThread(pr.id(), "thread-42", "alice");

            EligibilityResult decision = service.evaluateMerge(
                pr.id(),
                MergeStrategy.SQUASH,
                "alice"
            );

            System.out.println("\nFinal eligibility: " + decision.eligible());
            System.out.println("Current approvals: " + decision.currentApprovals());

            if (decision.eligible()) {
                String mergeHead = service.mergePullRequest(
                    pr.id(),
                    MergeStrategy.SQUASH,
                    "alice"
                );
                System.out.println("Merged head: " + mergeHead);
                System.out.println("Pull Request state: " + pr.state());
            }

            try {
                service.submitReview(pr.id(), "eve", ReviewState.APPROVED);
            } catch (GovernanceException exception) {
                System.out.println("\nExpected reviewer failure: " + exception.getMessage());
            }

            try {
                service.directPush("main", "unauthorized-commit", false);
            } catch (GovernanceException exception) {
                System.out.println("Expected direct-push failure: " + exception.getMessage());
            }

            System.out.println("\nRepository: " + service.repositoryName());

        } catch (RuntimeException exception) {
            System.err.println("Governance failure: " + exception.getMessage());
            System.exitCode = 1;
        }
    }
}
