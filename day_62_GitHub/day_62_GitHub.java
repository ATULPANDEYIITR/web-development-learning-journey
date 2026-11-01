import java.time.Instant;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

public class GitHubRepositoryGovernance {

    enum PullRequestState {
        DRAFT, OPEN, CLOSED, MERGED
    }

    enum ReviewState {
        COMMENTED, APPROVED, CHANGES_REQUESTED, DISMISSED
    }

    enum CheckState {
        PENDING, PASSED, FAILED
    }

    enum MergeStrategy {
        MERGE, SQUASH, REBASE
    }

    record Commit(String sha, String message, String author) {
        Commit {
            if (sha == null || !sha.matches("[A-Za-z0-9._-]+")) {
                throw new IllegalArgumentException("Invalid commit SHA");
            }
            if (message == null || message.isBlank()) {
                throw new IllegalArgumentException("Commit message is required");
            }
            if (author == null || author.isBlank()) {
                throw new IllegalArgumentException("Commit author is required");
            }
        }
    }

    record ReviewComment(
        String reviewer,
        String file,
        int line,
        String body,
        boolean resolved
    ) {}

    record Review(
        String reviewer,
        ReviewState state,
        Instant submittedAt
    ) {}

    record StatusCheck(
        String name,
        CheckState state
    ) {}

    record BranchProtectionPolicy(
        int requiredReviews,
        Set<String> requiredChecks,
        boolean dismissStaleApprovals,
        boolean requireConversationResolution,
        boolean allowDirectPush,
        boolean allowForcePush,
        boolean requireLinearHistory
    ) {
        BranchProtectionPolicy {
            if (requiredReviews < 0) {
                throw new IllegalArgumentException(
                    "Required reviews cannot be negative"
                );
            }
            requiredChecks = Set.copyOf(requiredChecks);
        }
    }

    static final class Branch {
        private final String name;
        private final List<Commit> commits = new ArrayList<>();
        private boolean protectedBranch;

        Branch(String name) {
            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException("Branch name required");
            }
            this.name = name;
        }

        String name() {
            return name;
        }

        String head() {
            return commits.isEmpty()
                ? null
                : commits.getLast().sha();
        }

        List<Commit> commits() {
            return List.copyOf(commits);
        }

        void setProtected(boolean value) {
            protectedBranch = value;
        }

        boolean isProtected() {
            return protectedBranch;
        }

        void addCommit(Commit commit) {
            if (commits.stream()
                .anyMatch(existing -> existing.sha().equals(commit.sha()))) {
                throw new IllegalArgumentException(
                    "Duplicate commit: " + commit.sha()
                );
            }
            commits.add(commit);
        }

        void replaceCommits(List<Commit> source) {
            commits.clear();
            commits.addAll(source);
        }
    }

    static final class PullRequest {
        private final int number;
        private final String title;
        private final String sourceBranch;
        private final String targetBranch;
        private final String author;
        private PullRequestState state;
        private boolean draft;
        private final List<Commit> commits = new ArrayList<>();
        private final List<Review> reviews = new ArrayList<>();
        private final List<ReviewComment> comments = new ArrayList<>();
        private final Map<String, StatusCheck> checks = new HashMap<>();
        private String baseHead;

        PullRequest(
            int number,
            String title,
            String sourceBranch,
            String targetBranch,
            String author,
            boolean draft
        ) {
            this.number = number;
            this.title = title;
            this.sourceBranch = sourceBranch;
            this.targetBranch = targetBranch;
            this.author = author;
            this.draft = draft;
            this.state = draft
                ? PullRequestState.DRAFT
                : PullRequestState.OPEN;
        }

        int number() {
            return number;
        }

        String title() {
            return title;
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

        PullRequestState state() {
            return state;
        }

        boolean draft() {
            return draft;
        }

        void setState(PullRequestState state) {
            this.state = state;
        }

        void publish() {
            draft = false;
            state = PullRequestState.OPEN;
        }

        void setCommits(List<Commit> source) {
            commits.clear();
            commits.addAll(source);
        }

        List<Commit> commits() {
            return List.copyOf(commits);
        }

        void setBaseHead(String head) {
            baseHead = head;
        }

        String baseHead() {
            return baseHead;
        }

        void addReview(Review review) {
            if (state != PullRequestState.OPEN) {
                throw new IllegalStateException(
                    "Only open pull requests can receive reviews"
                );
            }
            reviews.add(review);
        }

        List<Review> reviews() {
            return List.copyOf(reviews);
        }

        void addComment(ReviewComment comment) {
            if (comment.body() == null || comment.body().isBlank()) {
                throw new IllegalArgumentException(
                    "Review comment cannot be empty"
                );
            }
            comments.add(comment);
        }

        List<ReviewComment> comments() {
            return List.copyOf(comments);
        }

        void resolveAllComments() {
            for (int i = 0; i < comments.size(); i++) {
                ReviewComment old = comments.get(i);
                comments.set(
                    i,
                    new ReviewComment(
                        old.reviewer(),
                        old.file(),
                        old.line(),
                        old.body(),
                        true
                    )
                );
            }
        }

        void setCheck(String name, CheckState state) {
            checks.put(name, new StatusCheck(name, state));
        }

        Map<String, StatusCheck> checks() {
            return Map.copyOf(checks);
        }
    }

    record MergeEvaluation(
        boolean eligible,
        List<String> reasons
    ) {}

    static final class MergeBlockedException extends Exception {
        MergeBlockedException(String message) {
            super(message);
        }
    }

    static final class Repository {
        private final String name;
        private final Map<String, Branch> branches = new HashMap<>();
        private final Map<Integer, PullRequest> pullRequests = new HashMap<>();
        private final Map<String, BranchProtectionPolicy> policies =
            new HashMap<>();

        private int nextPullRequest = 1;

        Repository(String name) {
            this.name = name;
        }

        Branch createBranch(String name, String fromBranch) {
            if (branches.containsKey(name)) {
                throw new IllegalArgumentException(
                    "Branch already exists: " + name
                );
            }

            Branch branch = new Branch(name);

            if (fromBranch != null) {
                Branch base = branch(fromBranch);
                branch.replaceCommits(base.commits());
            }

            branches.put(name, branch);
            return branch;
        }

        Branch branch(String name) {
            Branch branch = branches.get(name);
            if (branch == null) {
                throw new IllegalArgumentException(
                    "Unknown branch: " + name
                );
            }
            return branch;
        }

        void configureProtection(
            String branchName,
            BranchProtectionPolicy policy
        ) {
            Branch branch = branch(branchName);
            branch.setProtected(true);
            policies.put(branchName, policy);
        }

        PullRequest openPullRequest(
            String title,
            String source,
            String target,
            String author
        ) {
            Branch sourceBranch = branch(source);
            Branch targetBranch = branch(target);

            if (source.equals(target)) {
                throw new IllegalArgumentException(
                    "Source and target must differ"
                );
            }

            PullRequest pr = new PullRequest(
                nextPullRequest++,
                title,
                source,
                target,
                author,
                false
            );

            pr.setCommits(sourceBranch.commits());
            pr.setBaseHead(targetBranch.head());

            pullRequests.put(pr.number(), pr);
            return pr;
        }

        MergeEvaluation evaluateMerge(PullRequest pr) {
            List<String> reasons = new ArrayList<>();

            if (pr.state() != PullRequestState.OPEN) {
                reasons.add("Pull request is not open");
            }

            if (pr.draft()) {
                reasons.add("Pull request is a draft");
            }

            if (pr.commits().isEmpty()) {
                reasons.add("Pull request contains no commits");
            }

            BranchProtectionPolicy policy =
                policies.get(pr.targetBranch());

            if (policy != null) {
                Set<String> approvals = new HashSet<>();

                for (Review review : pr.reviews()) {
                    if (review.state() == ReviewState.APPROVED &&
                        !review.reviewer().equals(pr.author())) {
                        approvals.add(review.reviewer());
                    }

                    if (review.state() == ReviewState.CHANGES_REQUESTED) {
                        reasons.add(
                            "Reviewer " + review.reviewer() +
                            " requested changes"
                        );
                    }
                }

                if (approvals.size() < policy.requiredReviews()) {
                    reasons.add(
                        "Required approvals: " +
                        policy.requiredReviews() +
                        ", current approvals: " +
                        approvals.size()
                    );
                }

                for (String required : policy.requiredChecks()) {
                    StatusCheck check = pr.checks().get(required);

                    if (check == null ||
                        check.state() != CheckState.PASSED) {
                        reasons.add(
                            "Required check is not passing: " + required
                        );
                    }
                }

                if (policy.requireConversationResolution() &&
                    pr.comments().stream().anyMatch(
                        comment -> !comment.resolved()
                    )) {
                    reasons.add(
                        "Unresolved review conversations remain"
                    );
                }
            }

            return new MergeEvaluation(
                reasons.isEmpty(),
                List.copyOf(reasons)
            );
        }

        void merge(
            PullRequest pr,
            MergeStrategy strategy
        ) throws MergeBlockedException {
            MergeEvaluation evaluation = evaluateMerge(pr);

            if (!evaluation.eligible()) {
                throw new MergeBlockedException(
                    String.join("; ", evaluation.reasons())
                );
            }

            Branch target = branch(pr.targetBranch());

            if (strategy == MergeStrategy.SQUASH) {
                target.addCommit(
                    new Commit(
                        "squash-" + pr.number(),
                        "Squash merge PR #" +
                            pr.number() + ": " + pr.title(),
                        pr.author()
                    )
                );
            } else if (strategy == MergeStrategy.MERGE) {
                target.addCommit(
                    new Commit(
                        "merge-" + pr.number(),
                        "Merge PR #" +
                            pr.number() + ": " + pr.title(),
                        pr.author()
                    )
                );
            } else {
                for (Commit commit : pr.commits()) {
                    target.addCommit(
                        new Commit(
                            "rebased-" + commit.sha(),
                            commit.message(),
                            commit.author()
                        )
                    );
                }
            }

            pr.setState(PullRequestState.MERGED);
        }

        void directPush(
            String branchName,
            List<Commit> commits
        ) {
            Branch branch = branch(branchName);
            BranchProtectionPolicy policy = policies.get(branchName);

            if (branch.isProtected() &&
                policy != null &&
                !policy.allowDirectPush()) {
                throw new SecurityException(
                    "Direct push to protected branch is blocked"
                );
            }

            commits.forEach(branch::addCommit);
        }

        Repository cloneRepository() {
            Repository copy = new Repository(name);

            for (Map.Entry<String, Branch> entry : branches.entrySet()) {
                Branch original = entry.getValue();
                Branch cloned = new Branch(original.name());
                cloned.replaceCommits(original.commits());
                cloned.setProtected(original.isProtected());
                copy.branches.put(entry.getKey(), cloned);
            }

            copy.policies.putAll(policies);
            return copy;
        }

        void pullFrom(Repository remote, String branchName) {
            Branch remoteBranch = remote.branch(branchName);
            Branch localBranch = branch(branchName);
            localBranch.replaceCommits(remoteBranch.commits());
        }

        void printState() {
            System.out.println("\nRepository: " + name);

            branches.forEach((name, branch) ->
                System.out.println(
                    "  " + name +
                    " head=" + branch.head() +
                    " protected=" + branch.isProtected() +
                    " commits=" + branch.commits().size()
                )
            );
        }
    }

    public static void main(String[] args) {
        try {
            Repository remote = new Repository("enterprise-service");

            Branch main = remote.createBranch("main", null);
            main.addCommit(
                new Commit(
                    "a1",
                    "Initial enterprise repository",
                    "alice"
                )
            );

            remote.configureProtection(
                "main",
                new BranchProtectionPolicy(
                    2,
                    Set.of("tests", "security-scan"),
                    true,
                    true,
                    false,
                    false,
                    true
                )
            );

            Repository local = remote.cloneRepository();

            local.createBranch(
                "feature/repository-documentation",
                "main"
            );

            local.branch("feature/repository-documentation").addCommit(
                new Commit(
                    "b1",
                    "Document clone pull push and README operations",
                    "bob"
                )
            );

            local.branch("feature/repository-documentation").addCommit(
                new Commit(
                    "b2",
                    "Document issue tracking workflow",
                    "bob"
                )
            );

            PullRequest pr = remote.openPullRequest(
                "Document repository workflow",
                "feature/repository-documentation",
                "main",
                "bob"
            );

            pr.addComment(
                new ReviewComment(
                    "carol",
                    "README.md",
                    30,
                    "Clarify protected branch behavior.",
                    false
                )
            );

            pr.addReview(
                new Review(
                    "carol",
                    ReviewState.APPROVED,
                    Instant.now()
                )
            );

            pr.addReview(
                new Review(
                    "david",
                    ReviewState.APPROVED,
                    Instant.now()
                )
            );

            pr.setCheck("tests", CheckState.PASSED);
            pr.setCheck("security-scan", CheckState.PASSED);

            MergeEvaluation first =
                remote.evaluateMerge(pr);

            System.out.println(
                "Merge eligible before resolution: " +
                first.eligible()
            );

            pr.resolveAllComments();

            MergeEvaluation second =
                remote.evaluateMerge(pr);

            System.out.println(
                "Merge eligible after resolution: " +
                second.eligible()
            );

            remote.merge(pr, MergeStrategy.SQUASH);

            try {
                local.branch("main").addCommit(
                    new Commit(
                        "unauthorized",
                        "Unauthorized direct push",
                        "eve"
                    )
                );

                remote.directPush(
                    "main",
                    List.of(local.branch("main").commits().getLast())
                );
            } catch (SecurityException error) {
                System.out.println(
                    "Expected protection failure: " +
                    error.getMessage()
                );
            }

            local.pullFrom(remote, "main");

            if (!local.branch("main").head().equals(
                remote.branch("main").head()
            )) {
                throw new IllegalStateException(
                    "Pull synchronization failed"
                );
            }

            remote.printState();

        } catch (Exception error) {
            System.err.println(
                "Workflow failed: " + error.getMessage()
            );
            System.exit(1);
        }
    }
}
