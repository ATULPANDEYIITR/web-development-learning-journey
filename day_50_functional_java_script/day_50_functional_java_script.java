import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.function.Function;
import java.util.function.Predicate;
import java.util.stream.Collectors;

public final class RepositoryGovernance {

    enum PullRequestState {
        DRAFT, OPEN, CLOSED, MERGED
    }

    enum ReviewState {
        COMMENTED, APPROVED, CHANGES_REQUESTED, DISMISSED
    }

    enum MergeStrategy {
        MERGE_COMMIT, SQUASH, REBASE
    }

    record Commit(String sha, String message) {
        public Commit {
            if (sha == null || sha.isBlank()) {
                throw new IllegalArgumentException("commit SHA is required");
            }
            if (message == null) {
                throw new IllegalArgumentException("commit message is required");
            }
        }
    }

    record Review(
        String reviewer,
        ReviewState state,
        List<String> comments
    ) {
        public Review {
            if (reviewer == null || reviewer.isBlank()) {
                throw new IllegalArgumentException("reviewer is required");
            }
            Objects.requireNonNull(state, "review state is required");
            comments = List.copyOf(comments == null ? List.of() : comments);
        }
    }

    record StatusCheck(
        String name,
        boolean passed,
        boolean required
    ) {
        public StatusCheck {
            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException("check name is required");
            }
        }
    }

    record BranchProtection(
        int requiredReviews,
        Set<String> requiredChecks,
        boolean requireConversationResolution,
        boolean requireLinearHistory,
        boolean allowDirectPush,
        boolean allowForcePush,
        boolean allowDeletion,
        boolean allowAdminBypass
    ) {
        public BranchProtection {
            if (requiredReviews < 0) {
                throw new IllegalArgumentException(
                    "requiredReviews cannot be negative"
                );
            }

            requiredChecks = Set.copyOf(requiredChecks);
        }
    }

    record PullRequest(
        int number,
        String sourceBranch,
        String targetBranch,
        List<Commit> commits,
        PullRequestState state,
        List<Review> reviews,
        List<StatusCheck> checks,
        int unresolvedConversations,
        boolean hasConflicts,
        boolean synchronizedWithBase,
        MergeStrategy mergeStrategy
    ) {
        public PullRequest {
            if (number <= 0) {
                throw new IllegalArgumentException(
                    "pull request number must be positive"
                );
            }

            if (sourceBranch == null || targetBranch == null ||
                sourceBranch.isBlank() || targetBranch.isBlank()) {
                throw new IllegalArgumentException(
                    "branches are required"
                );
            }

            if (sourceBranch.equals(targetBranch)) {
                throw new IllegalArgumentException(
                    "source and target branches must differ"
                );
            }

            if (commits == null || commits.isEmpty()) {
                throw new IllegalArgumentException(
                    "pull request requires commits"
                );
            }

            if (unresolvedConversations < 0) {
                throw new IllegalArgumentException(
                    "unresolved conversations cannot be negative"
                );
            }

            commits = List.copyOf(commits);
            reviews = List.copyOf(reviews);
            checks = List.copyOf(checks);
        }

        PullRequest withState(PullRequestState newState) {
            return new PullRequest(
                number,
                sourceBranch,
                targetBranch,
                commits,
                newState,
                reviews,
                checks,
                unresolvedConversations,
                hasConflicts,
                synchronizedWithBase,
                mergeStrategy
            );
        }

        PullRequest withReview(Review review) {
            var updated = new ArrayList<>(reviews);
            updated.add(review);

            return new PullRequest(
                number,
                sourceBranch,
                targetBranch,
                commits,
                state,
                updated,
                checks,
                unresolvedConversations,
                hasConflicts,
                synchronizedWithBase,
                mergeStrategy
            );
        }

        PullRequest withCheck(StatusCheck updatedCheck) {
            var updated = checks.stream()
                .filter(check -> !check.name().equals(updatedCheck.name()))
                .collect(Collectors.toCollection(ArrayList::new));

            updated.add(updatedCheck);

            return new PullRequest(
                number,
                sourceBranch,
                targetBranch,
                commits,
                state,
                reviews,
                updated,
                unresolvedConversations,
                hasConflicts,
                synchronizedWithBase,
                mergeStrategy
            );
        }

        PullRequest resolveConversation() {
            return new PullRequest(
                number,
                sourceBranch,
                targetBranch,
                commits,
                state,
                reviews,
                checks,
                Math.max(0, unresolvedConversations - 1),
                hasConflicts,
                synchronizedWithBase,
                mergeStrategy
            );
        }

        PullRequest synchronize() {
            return new PullRequest(
                number,
                sourceBranch,
                targetBranch,
                commits,
                state,
                reviews,
                checks,
                unresolvedConversations,
                false,
                true,
                mergeStrategy
            );
        }
    }

    static final class MergeEligibilityService {

        private final BranchProtection policy;

        MergeEligibilityService(BranchProtection policy) {
            this.policy = Objects.requireNonNull(policy);
        }

        List<String> reasons(PullRequest pr) {
            var reasons = new ArrayList<String>();

            if (pr.state() != PullRequestState.OPEN) {
                reasons.add("pull request is not open");
            }

            if (pr.commits().isEmpty()) {
                reasons.add("pull request contains no commits");
            }

            if (!pr.synchronizedWithBase()) {
                reasons.add("source branch is behind target branch");
            }

            if (pr.hasConflicts()) {
                reasons.add("merge conflicts must be resolved");
            }

            if (hasRequestedChanges(pr)) {
                reasons.add("reviewer requested changes");
            }

            if (approvalCount(pr) < policy.requiredReviews()) {
                reasons.add("required approvals are missing");
            }

            if (!requiredChecksPass(pr)) {
                reasons.add("required status checks have not passed");
            }

            if (
                policy.requireConversationResolution() &&
                pr.unresolvedConversations() > 0
            ) {
                reasons.add("review conversations remain unresolved");
            }

            return List.copyOf(reasons);
        }

        boolean canMerge(PullRequest pr) {
            return reasons(pr).isEmpty();
        }

        PullRequest merge(PullRequest pr) {
            var reasons = reasons(pr);

            if (!reasons.isEmpty()) {
                throw new IllegalStateException(
                    "merge blocked: " + String.join("; ", reasons)
                );
            }

            return pr.withState(PullRequestState.MERGED);
        }

        private int approvalCount(PullRequest pr) {
            return (int) pr.reviews().stream()
                .filter(review -> review.state() == ReviewState.APPROVED)
                .count();
        }

        private boolean hasRequestedChanges(PullRequest pr) {
            return pr.reviews().stream()
                .anyMatch(review ->
                    review.state() == ReviewState.CHANGES_REQUESTED
                );
        }

        private boolean requiredChecksPass(PullRequest pr) {
            Map<String, Boolean> checks = pr.checks().stream()
                .collect(Collectors.toUnmodifiableMap(
                    StatusCheck::name,
                    StatusCheck::passed,
                    (left, right) -> right
                ));

            return policy.requiredChecks().stream()
                .allMatch(name -> checks.getOrDefault(name, false));
        }
    }

    static <T, R> List<R> map(
        List<T> values,
        Function<T, R> function
    ) {
        return values.stream()
            .map(function)
            .toList();
    }

    static <T> List<T> filter(
        List<T> values,
        Predicate<T> predicate
    ) {
        return values.stream()
            .filter(predicate)
            .toList();
    }

    static <T> Function<T, T> compose(
        Function<T, T> first,
        Function<T, T> second
    ) {
        return value -> second.apply(first.apply(value));
    }

    static PullRequest openDraft(PullRequest pr) {
        if (pr.state() != PullRequestState.DRAFT) {
            throw new IllegalStateException(
                "only draft pull requests can be opened"
            );
        }

        return pr.withState(PullRequestState.OPEN);
    }

    static void printEvaluation(
        PullRequest pr,
        MergeEligibilityService service
    ) {
        System.out.println("Mergeable: " + service.canMerge(pr));

        if (!service.canMerge(pr)) {
            service.reasons(pr).forEach(
                reason -> System.out.println("  Blocked: " + reason)
            );
        }
    }

    public static void main(String[] args) {
        var policy = new BranchProtection(
            2,
            Set.of("unit-tests", "security-scan"),
            true,
            true,
            false,
            false,
            false,
            false
        );

        var service = new MergeEligibilityService(policy);

        var commits = List.of(
            new Commit("a1b2c3d", " add repository workflow model "),
            new Commit("b2c3d4e", "implement merge eligibility"),
            new Commit("c3d4e5f", "fix")
        );

        var pr = new PullRequest(
            42,
            "feature/governance-engine",
            "main",
            commits,
            PullRequestState.DRAFT,
            List.of(),
            List.of(
                new StatusCheck("unit-tests", true, true),
                new StatusCheck("security-scan", false, true)
            ),
            2,
            false,
            true,
            MergeStrategy.SQUASH
        );

        pr = openDraft(pr);

        pr = pr.withReview(
            new Review(
                "reviewer-alice",
                ReviewState.APPROVED,
                List.of("Policy model is clear.")
            )
        );

        pr = pr.withReview(
            new Review(
                "reviewer-bob",
                ReviewState.COMMENTED,
                List.of("Resolve the policy discussion.")
            )
        );

        var normalize = (Function<Commit, Commit>) commit ->
            new Commit(
                commit.sha(),
                commit.message().trim().replaceAll("\\s+", " ")
            );

        var meaningful = (Predicate<Commit>)
            commit -> commit.message().length() >= 8;

        var normalizedCommits = map(commits, normalize);
        var meaningfulCommits = filter(normalizedCommits, meaningful);

        System.out.println("Functional commit pipeline:");
        meaningfulCommits.forEach(
            commit -> System.out.println(
                "  " + commit.sha() + ": " + commit.message()
            )
        );

        System.out.println("\nInitial evaluation:");
        printEvaluation(pr, service);

        pr = pr.withReview(
            new Review(
                "reviewer-bob",
                ReviewState.APPROVED,
                List.of()
            )
        );

        pr = pr.withCheck(
            new StatusCheck("security-scan", true, true)
        );

        pr = pr.resolveConversation();
        pr = pr.resolveConversation();
        pr = pr.synchronize();

        System.out.println("\nFinal evaluation:");
        printEvaluation(pr, service);

        if (service.canMerge(pr)) {
            pr = service.merge(pr);
            System.out.println("Pull request state: " + pr.state());
        }

        System.out.println(
            "\nOriginal commit remains immutable: " +
            commits.get(0).message()
        );

        var uppercase = (Function<String, String>)
            String::toUpperCase;

        var trimmed = (Function<String, String>)
            String::trim;

        var normalizeText = compose(trimmed, uppercase);

        System.out.println(
            "Composed transformation: " +
            normalizeText.apply(" functional governance ")
        );
    }
}
