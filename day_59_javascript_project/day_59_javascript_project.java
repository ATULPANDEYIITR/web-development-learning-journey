import java.time.Instant;
import java.util.*;
import java.util.function.Predicate;
import java.util.stream.Collectors;

public class TaskGovernanceApplication {

    enum PullRequestState {
        DRAFT, OPEN, CLOSED, MERGED
    }

    enum ReviewState {
        COMMENTED, APPROVED, CHANGES_REQUESTED, DISMISSED
    }

    enum CheckState {
        PENDING, PASSING, FAILING
    }

    enum TaskState {
        TODO, IN_PROGRESS, DONE
    }

    enum MergeStrategy {
        MERGE_COMMIT, SQUASH, REBASE
    }

    record Commit(
        String sha,
        String author,
        String message,
        Instant createdAt
    ) {}

    record StatusCheck(
        String name,
        CheckState state,
        String commitSha
    ) {}

    record ReviewComment(
        String id,
        String reviewer,
        String body,
        boolean resolved
    ) {}

    record Review(
        String id,
        String reviewer,
        ReviewState state,
        String commitSha,
        boolean dismissed,
        List<ReviewComment> comments
    ) {
        Review withDismissed(boolean value) {
            return new Review(
                id,
                reviewer,
                state,
                commitSha,
                value,
                comments
            );
        }
    }

    record Task(
        String id,
        String title,
        String description,
        TaskState state,
        String priority,
        Integer linkedPullRequest
    ) {}

    record BranchProtectionPolicy(
        int requiredReviews,
        Set<String> requiredStatusChecks,
        boolean restrictDirectPush,
        boolean restrictForcePush,
        boolean restrictDeletion,
        boolean requireConversationResolution,
        boolean requireLinearHistory,
        boolean administratorBypass
    ) {
        BranchProtectionPolicy {
            if (requiredReviews < 0) {
                throw new IllegalArgumentException(
                    "Required reviews cannot be negative."
                );
            }

            requiredStatusChecks =
                Set.copyOf(requiredStatusChecks);
        }
    }

    record PullRequest(
        int number,
        String title,
        String sourceBranch,
        String targetBranch,
        String author,
        PullRequestState state,
        List<Commit> commits,
        Set<String> requestedReviewers,
        List<Review> reviews,
        Map<String, StatusCheck> checks,
        List<String> conversations,
        MergeStrategy mergeStrategy
    ) {
        PullRequest withState(PullRequestState newState) {
            return new PullRequest(
                number,
                title,
                sourceBranch,
                targetBranch,
                author,
                newState,
                commits,
                requestedReviewers,
                reviews,
                checks,
                conversations,
                mergeStrategy
            );
        }

        PullRequest withCommits(List<Commit> newCommits) {
            return new PullRequest(
                number,
                title,
                sourceBranch,
                targetBranch,
                author,
                state,
                List.copyOf(newCommits),
                requestedReviewers,
                reviews,
                checks,
                conversations,
                mergeStrategy
            );
        }

        PullRequest withMergeStrategy(MergeStrategy strategy) {
            return new PullRequest(
                number,
                title,
                sourceBranch,
                targetBranch,
                author,
                PullRequestState.MERGED,
                commits,
                requestedReviewers,
                reviews,
                checks,
                conversations,
                strategy
            );
        }
    }

    static final class DomainException extends RuntimeException {
        DomainException(String message) {
            super(message);
        }
    }

    interface MergePolicy {
        Eligibility evaluate(
            PullRequest pullRequest,
            BranchProtectionPolicy policy,
            String actor
        );
    }

    record Eligibility(
        boolean eligible,
        List<String> reasons
    ) {}

    static final class Branch {
        private final String name;
        private final List<Commit> commits;
        private boolean protectedBranch;

        Branch(String name, List<Commit> commits) {
            this.name = name;
            this.commits = new ArrayList<>(commits);
        }

        String name() {
            return name;
        }

        List<Commit> commits() {
            return commits;
        }

        boolean protectedBranch() {
            return protectedBranch;
        }

        void protect() {
            protectedBranch = true;
        }
    }

    static final class Repository {
        private final String name;
        private final Map<String, Branch> branches = new HashMap<>();
        private final Map<Integer, PullRequest> pullRequests =
            new LinkedHashMap<>();
        private final Map<String, Task> tasks = new LinkedHashMap<>();
        private final Map<String, BranchProtectionPolicy> policies =
            new HashMap<>();

        private int nextPrNumber = 1;

        Repository(String name) {
            this.name = name;
        }

        void createBranch(String name, String base) {
            if (branches.containsKey(name)) {
                throw new DomainException(
                    "Branch already exists: " + name
                );
            }

            List<Commit> commits = base == null
                ? List.of()
                : List.copyOf(requireBranch(base).commits());

            branches.put(name, new Branch(name, commits));
        }

        Commit commit(
            String branchName,
            String author,
            String message
        ) {
            if (author == null || author.isBlank()) {
                throw new DomainException(
                    "Commit author is required."
                );
            }

            if (message == null || message.isBlank()) {
                throw new DomainException(
                    "Commit message is required."
                );
            }

            Commit commit = new Commit(
                UUID.randomUUID().toString().substring(0, 12),
                author,
                message,
                Instant.now()
            );

            requireBranch(branchName).commits().add(commit);
            return commit;
        }

        void protect(
            String branchName,
            BranchProtectionPolicy policy
        ) {
            Branch branch = requireBranch(branchName);
            branch.protect();
            policies.put(branchName, policy);
        }

        Task createTask(
            String title,
            String description,
            String priority
        ) {
            Set<String> validPriorities = Set.of(
                "low",
                "medium",
                "high",
                "critical"
            );

            if (title == null || title.isBlank()) {
                throw new DomainException(
                    "Task title is required."
                );
            }

            if (!validPriorities.contains(priority)) {
                throw new DomainException(
                    "Invalid task priority."
                );
            }

            Task task = new Task(
                UUID.randomUUID().toString().substring(0, 8),
                title.trim(),
                description == null ? "" : description.trim(),
                TaskState.TODO,
                priority,
                null
            );

            tasks.put(task.id(), task);
            return task;
        }

        void updateTask(String taskId, TaskState state) {
            Task task = requireTask(taskId);

            tasks.put(
                task.id(),
                new Task(
                    task.id(),
                    task.title(),
                    task.description(),
                    state,
                    task.priority(),
                    task.linkedPullRequest()
                )
            );
        }

        PullRequest createPullRequest(
            String title,
            String source,
            String target,
            String author,
            boolean draft
        ) {
            Branch sourceBranch = requireBranch(source);
            requireBranch(target);

            if (source.equals(target)) {
                throw new DomainException(
                    "Source and target must differ."
                );
            }

            if (sourceBranch.commits().isEmpty()) {
                throw new DomainException(
                    "A PR needs at least one commit."
                );
            }

            PullRequest request = new PullRequest(
                nextPrNumber++,
                title,
                source,
                target,
                author,
                draft
                    ? PullRequestState.DRAFT
                    : PullRequestState.OPEN,
                List.copyOf(sourceBranch.commits()),
                new HashSet<>(),
                new ArrayList<>(),
                new HashMap<>(),
                new ArrayList<>(),
                null
            );

            pullRequests.put(request.number(), request);
            return request;
        }

        void markReady(int number) {
            PullRequest request = requirePullRequest(number);

            if (request.state() != PullRequestState.DRAFT) {
                throw new DomainException(
                    "Only draft PRs can become ready."
                );
            }

            pullRequests.put(
                number,
                request.withState(PullRequestState.OPEN)
            );
        }

        void requestReviewer(int number, String reviewer) {
            PullRequest request = requirePullRequest(number);

            if (reviewer.equals(request.author())) {
                throw new DomainException(
                    "Author cannot be requested as the reviewer."
                );
            }

            request.requestedReviewers().add(reviewer);
        }

        Review submitReview(
            int number,
            String reviewer,
            ReviewState state
        ) {
            PullRequest request = requirePullRequest(number);

            if (request.state() != PullRequestState.OPEN) {
                throw new DomainException(
                    "Only open PRs accept reviews."
                );
            }

            if (!request.requestedReviewers().contains(reviewer)) {
                throw new DomainException(
                    "Reviewer was not requested."
                );
            }

            if (reviewer.equals(request.author())) {
                throw new DomainException(
                    "Self-review is not permitted."
                );
            }

            Review review = new Review(
                UUID.randomUUID().toString().substring(0, 10),
                reviewer,
                state,
                head(request),
                false,
                new ArrayList<>()
            );

            request.reviews().add(review);
            return review;
        }

        void addConversation(
            int number,
            String body
        ) {
            if (body == null || body.isBlank()) {
                throw new DomainException(
                    "Conversation cannot be empty."
                );
            }

            requirePullRequest(number)
                .conversations()
                .add(body.trim());
        }

        void resolveConversation(
            int number,
            int index
        ) {
            PullRequest request = requirePullRequest(number);

            if (index < 0 ||
                index >= request.conversations().size()) {
                throw new DomainException(
                    "Conversation index is invalid."
                );
            }

            request.conversations().set(
                index,
                "[RESOLVED] " + request.conversations().get(index)
            );
        }

        void setCheck(
            int number,
            String name,
            CheckState state
        ) {
            PullRequest request = requirePullRequest(number);

            request.checks().put(
                name,
                new StatusCheck(
                    name,
                    state,
                    head(request)
                )
            );
        }

        Eligibility evaluate(
            int number,
            String actor
        ) {
            PullRequest request = requirePullRequest(number);
            BranchProtectionPolicy policy =
                policies.get(request.targetBranch());

            List<String> reasons = new ArrayList<>();

            if (request.state() != PullRequestState.OPEN) {
                reasons.add("PR is not open.");
            }

            if (request.commits().isEmpty()) {
                reasons.add("PR has no commits.");
            }

            if (policy == null) {
                return new Eligibility(
                    reasons.isEmpty(),
                    List.copyOf(reasons)
                );
            }

            if (actor.equals(request.author())) {
                reasons.add("Author cannot merge its own PR.");
            }

            String currentHead = head(request);

            Set<String> currentApprovers =
                request.reviews()
                    .stream()
                    .filter(review ->
                        review.state() == ReviewState.APPROVED &&
                        !review.dismissed() &&
                        review.commitSha().equals(currentHead)
                    )
                    .map(Review::reviewer)
                    .collect(Collectors.toSet());

            if (currentApprovers.size() <
                policy.requiredReviews()) {
                reasons.add(
                    "Required current approvals are missing."
                );
            }

            for (String required :
                policy.requiredStatusChecks()) {

                StatusCheck check =
                    request.checks().get(required);

                if (check == null ||
                    check.state() != CheckState.PASSING) {
                    reasons.add(
                        "Required check is not passing: " +
                        required
                    );
                } else if (!check.commitSha().equals(currentHead)) {
                    reasons.add(
                        "Required check is stale: " +
                        required
                    );
                }
            }

            if (policy.requireConversationResolution()) {
                boolean unresolved =
                    request.conversations()
                        .stream()
                        .anyMatch(text ->
                            !text.startsWith("[RESOLVED]"));

                if (unresolved) {
                    reasons.add(
                        "Unresolved review conversations exist."
                    );
                }
            }

            return new Eligibility(
                reasons.isEmpty(),
                List.copyOf(reasons)
            );
        }

        Commit merge(
            int number,
            String actor,
            MergeStrategy strategy
        ) {
            PullRequest request = requirePullRequest(number);
            Eligibility eligibility = evaluate(number, actor);

            if (!eligibility.eligible()) {
                throw new DomainException(
                    "Merge blocked: " +
                    String.join("; ", eligibility.reasons())
                );
            }

            Commit merged = new Commit(
                UUID.randomUUID().toString().substring(0, 12),
                actor,
                strategy.name().toLowerCase(Locale.ROOT) +
                    " merge PR #" +
                    number +
                    ": " +
                    request.title(),
                Instant.now()
            );

            requireBranch(request.targetBranch())
                .commits()
                .add(merged);

            pullRequests.put(
                number,
                request.withMergeStrategy(strategy)
            );

            return merged;
        }

        void linkTask(String taskId, int prNumber) {
            Task task = requireTask(taskId);
            requirePullRequest(prNumber);

            tasks.put(
                task.id(),
                new Task(
                    task.id(),
                    task.title(),
                    task.description(),
                    task.state(),
                    task.priority(),
                    prNumber
                )
            );
        }

        private String head(PullRequest request) {
            return request.commits().get(
                request.commits().size() - 1
            ).sha();
        }

        private Branch requireBranch(String name) {
            Branch branch = branches.get(name);

            if (branch == null) {
                throw new DomainException(
                    "Unknown branch: " + name
                );
            }

            return branch;
        }

        private PullRequest requirePullRequest(int number) {
            PullRequest request = pullRequests.get(number);

            if (request == null) {
                throw new DomainException(
                    "Unknown pull request: " + number
                );
            }

            return request;
        }

        private Task requireTask(String id) {
            Task task = tasks.get(id);

            if (task == null) {
                throw new DomainException(
                    "Unknown task: " + id
                );
            }

            return task;
        }

        void printDashboard() {
            System.out.println(
                "\n=== Enterprise Task Governance ==="
            );

            System.out.println("\nTasks:");
            tasks.values().forEach(task ->
                System.out.printf(
                    "%s | %s | %s | %s | PR=%s%n",
                    task.id(),
                    task.title(),
                    task.state(),
                    task.priority(),
                    task.linkedPullRequest()
                )
            );

            System.out.println("\nPull Requests:");

            pullRequests.values().forEach(request -> {
                Eligibility result =
                    evaluate(
                        request.number(),
                        "release-manager"
                    );

                System.out.printf(
                    "#%d | %s | %s | %s -> %s | eligible=%s%n",
                    request.number(),
                    request.title(),
                    request.state(),
                    request.sourceBranch(),
                    request.targetBranch(),
                    result.eligible()
                );

                result.reasons().forEach(reason ->
                    System.out.println("  - " + reason)
                );
            });
        }
    }

    public static void main(String[] args) {
        try {
            Repository repository =
                new Repository("enterprise-task-manager");

            repository.createBranch("main", null);

            repository.commit(
                "main",
                "platform-admin",
                "Initialize task management platform"
            );

            repository.protect(
                "main",
                new BranchProtectionPolicy(
                    2,
                    Set.of("unit-tests", "security-scan"),
                    true,
                    true,
                    true,
                    true,
                    true,
                    false
                )
            );

            repository.createBranch(
                "feature/task-board",
                "main"
            );

            repository.commit(
                "feature/task-board",
                "developer",
                "Add task state transitions"
            );

            repository.commit(
                "feature/task-board",
                "developer",
                "Add repository governance rules"
            );

            Task task = repository.createTask(
                "Build governed task workflow",
                "Link implementation tasks to review-controlled changes.",
                "high"
            );

            PullRequest pr =
                repository.createPullRequest(
                    "Build governed task workflow",
                    "feature/task-board",
                    "main",
                    "developer",
                    true
                );

            repository.linkTask(task.id(), pr.number());
            repository.markReady(pr.number());

            repository.requestReviewer(
                pr.number(),
                "reviewer-one"
            );

            repository.requestReviewer(
                pr.number(),
                "reviewer-two"
            );

            Review firstReview =
                repository.submitReview(
                    pr.number(),
                    "reviewer-one",
                    ReviewState.CHANGES_REQUESTED
                );

            repository.addConversation(
                pr.number(),
                "Validate task transitions."
            );

            Eligibility blocked =
                repository.evaluate(
                    pr.number(),
                    "release-manager"
                );

            if (blocked.eligible()) {
                throw new IllegalStateException(
                    "PR should initially be blocked."
                );
            }

            repository.resolveConversation(
                pr.number(),
                0
            );

            repository.submitReview(
                pr.number(),
                "reviewer-one",
                ReviewState.APPROVED
            );

            repository.submitReview(
                pr.number(),
                "reviewer-two",
                ReviewState.APPROVED
            );

            repository.setCheck(
                pr.number(),
                "unit-tests",
                CheckState.PASSING
            );

            repository.setCheck(
                pr.number(),
                "security-scan",
                CheckState.PASSING
            );

            Eligibility eligible =
                repository.evaluate(
                    pr.number(),
                    "release-manager"
                );

            if (!eligible.eligible()) {
                throw new IllegalStateException(
                    "PR should be merge eligible: " +
                    String.join(", ", eligible.reasons())
                );
            }

            repository.merge(
                pr.number(),
                "release-manager",
                MergeStrategy.SQUASH
            );

            repository.updateTask(
                task.id(),
                TaskState.DONE
            );

            repository.printDashboard();

        } catch (DomainException | IllegalStateException ex) {
            System.err.println(
                "Application error: " + ex.getMessage()
            );
            System.exit(1);
        }
    }
}
