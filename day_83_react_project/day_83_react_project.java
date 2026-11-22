import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.stream.Collectors;

/**
 * Enterprise Repository Administration and Governance System.
 *
 * Java 17 implementation featuring:
 * - Explicit domain types
 * - Immutable records
 * - Review policy objects
 * - Branch protection
 * - State transitions
 * - Approval evaluation
 * - CI/CD status validation
 * - Merge strategies
 * - Audit events
 * - Dashboard reporting
 */
public class RepositoryAdmin {

    enum PullRequestState {
        DRAFT,
        OPEN,
        CLOSED,
        MERGED
    }

    enum ReviewDecision {
        APPROVED,
        CHANGES_REQUESTED,
        COMMENTED,
        DISMISSED
    }

    enum CheckStatus {
        PENDING,
        SUCCESS,
        FAILURE,
        CANCELLED
    }

    enum MergeStrategy {
        MERGE_COMMIT,
        SQUASH,
        REBASE
    }

    enum ActorRole {
        DEVELOPER,
        REVIEWER,
        MAINTAINER,
        ADMINISTRATOR,
        CI_SYSTEM
    }

    record Commit(
        String id,
        String message,
        String author,
        Instant createdAt
    ) {
        Commit {
            Objects.requireNonNull(id);
            Objects.requireNonNull(message);
            Objects.requireNonNull(author);

            if (message.isBlank() || author.isBlank()) {
                throw new IllegalArgumentException(
                    "Commit fields cannot be empty."
                );
            }
        }
    }

    record ReviewPolicy(
        int requiredApprovals,
        boolean dismissStaleApprovals,
        boolean requireDifferentAuthor,
        Set<String> requiredChecks,
        boolean requireResolvedConversations,
        boolean requireUpToDateBranch,
        boolean requireLinearHistory
    ) {
        ReviewPolicy {
            if (requiredApprovals < 0) {
                throw new IllegalArgumentException(
                    "Approval count cannot be negative."
                );
            }

            requiredChecks = Set.copyOf(requiredChecks);
        }

        static ReviewPolicy enterpriseDefault() {
            return new ReviewPolicy(
                2,
                true,
                true,
                Set.of("build", "tests", "security"),
                true,
                true,
                true
            );
        }
    }

    record Review(
        String reviewer,
        ReviewDecision decision,
        String reviewedCommit,
        String comment,
        Instant submittedAt
    ) {}

    record StatusCheck(
        String name,
        CheckStatus status,
        String commitId,
        Instant updatedAt
    ) {}

    record AuditEvent(
        String actor,
        String action,
        String resource,
        Instant timestamp
    ) {}

    record EligibilityResult(
        boolean eligible,
        List<String> reasons,
        int approvalsReceived,
        int approvalsRequired
    ) {
        EligibilityResult {
            reasons = List.copyOf(reasons);
        }
    }

    record DashboardMetrics(
        int repositoryCount,
        int branchCount,
        int totalPullRequests,
        int openPullRequests,
        int draftPullRequests,
        int mergedPullRequests,
        int closedPullRequests,
        int eligiblePullRequests,
        int auditEvents
    ) {}

    static class DomainException extends RuntimeException {
        DomainException(String message) {
            super(message);
        }
    }

    static class Branch {
        private final String name;
        private final boolean protectedBranch;
        private String headCommit;
        private final List<String> history = new ArrayList<>();

        Branch(
            String name,
            String initialCommit,
            boolean protectedBranch
        ) {
            this.name = name;
            this.headCommit = initialCommit;
            this.protectedBranch = protectedBranch;
            history.add(initialCommit);
        }

        String name() {
            return name;
        }

        String headCommit() {
            return headCommit;
        }

        boolean isProtected() {
            return protectedBranch;
        }

        void advance(String commitId) {
            history.add(commitId);
            headCommit = commitId;
        }

        List<String> history() {
            return List.copyOf(history);
        }
    }

    static class PullRequest {
        private final int id;
        private final String title;
        private final String author;
        private final String sourceBranch;
        private final String targetBranch;

        private String baseCommit;
        private String headCommit;

        private PullRequestState state;
        private final Map<String, Review> reviews = new HashMap<>();
        private final Map<String, StatusCheck> checks = new HashMap<>();

        private int unresolvedConversations;

        PullRequest(
            int id,
            String title,
            String author,
            String sourceBranch,
            String targetBranch,
            String baseCommit,
            String headCommit,
            boolean draft
        ) {
            this.id = id;
            this.title = title;
            this.author = author;
            this.sourceBranch = sourceBranch;
            this.targetBranch = targetBranch;
            this.baseCommit = baseCommit;
            this.headCommit = headCommit;
            this.state = draft
                ? PullRequestState.DRAFT
                : PullRequestState.OPEN;
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

        String sourceBranch() {
            return sourceBranch;
        }

        String targetBranch() {
            return targetBranch;
        }

        String baseCommit() {
            return baseCommit;
        }

        String headCommit() {
            return headCommit;
        }

        PullRequestState state() {
            return state;
        }

        void publish() {
            if (state != PullRequestState.DRAFT) {
                throw new DomainException("PR is not a draft.");
            }

            state = PullRequestState.OPEN;
        }

        void close() {
            if (state != PullRequestState.OPEN &&
                state != PullRequestState.DRAFT) {
                throw new DomainException("PR cannot be closed.");
            }

            state = PullRequestState.CLOSED;
        }

        void reopen() {
            if (state != PullRequestState.CLOSED) {
                throw new DomainException(
                    "Only closed PRs can be reopened."
                );
            }

            state = PullRequestState.OPEN;
        }

        void addReview(Review review) {
            reviews.put(review.reviewer(), review);
        }

        void updateCheck(StatusCheck check) {
            checks.put(check.name(), check);
        }

        void addConversation() {
            unresolvedConversations++;
        }

        void resolveConversation() {
            if (unresolvedConversations == 0) {
                throw new DomainException(
                    "No unresolved conversation exists."
                );
            }

            unresolvedConversations--;
        }

        void synchronize(
            String latestBase,
            String latestHead,
            boolean dismissStale
        ) {
            baseCommit = latestBase;
            headCommit = latestHead;

            if (dismissStale) {
                reviews.clear();
            }

            checks.clear();
        }

        int unresolvedConversations() {
            return unresolvedConversations;
        }

        List<Review> reviews() {
            return List.copyOf(reviews.values());
        }

        List<StatusCheck> checks() {
            return List.copyOf(checks.values());
        }

        void markMerged() {
            if (state != PullRequestState.OPEN) {
                throw new DomainException("PR is not open.");
            }

            state = PullRequestState.MERGED;
        }
    }

    static class RepositoryService {
        private final String repositoryName;

        private final Map<String, Commit> commits = new HashMap<>();
        private final Map<String, Branch> branches = new HashMap<>();
        private final Map<Integer, PullRequest> pullRequests =
            new HashMap<>();

        private final Map<String, ReviewPolicy> policies = new HashMap<>();
        private final Map<String, ActorRole> actors = new HashMap<>();

        private final List<AuditEvent> auditLog = new ArrayList<>();

        private final AtomicInteger prSequence = new AtomicInteger(1001);
        private final AtomicInteger commitSequence = new AtomicInteger(1);

        RepositoryService(String repositoryName) {
            if (repositoryName == null || repositoryName.isBlank()) {
                throw new IllegalArgumentException(
                    "Repository name is required."
                );
            }

            this.repositoryName = repositoryName;
        }

        private void audit(
            String actor,
            String action,
            String resource
        ) {
            auditLog.add(
                new AuditEvent(
                    actor,
                    action,
                    resource,
                    Instant.now()
                )
            );
        }

        void registerActor(String username, ActorRole role) {
            if (username == null || username.isBlank()) {
                throw new IllegalArgumentException(
                    "Username is required."
                );
            }

            actors.put(username, role);
        }

        private void requireRole(
            String username,
            ActorRole... allowedRoles
        ) {
            ActorRole actual = actors.get(username);

            if (actual == null) {
                throw new DomainException("Unknown actor.");
            }

            for (ActorRole role : allowedRoles) {
                if (actual == role) {
                    return;
                }
            }

            throw new DomainException("Insufficient permissions.");
        }

        String createCommit(String message, String author) {
            if (!actors.containsKey(author)) {
                throw new DomainException("Unknown commit author.");
            }

            String id = "C" + commitSequence.getAndIncrement();

            Commit commit = new Commit(
                id,
                message,
                author,
                Instant.now()
            );

            commits.put(id, commit);
            audit(author, "COMMIT_CREATED", id);

            return id;
        }

        void createBranch(String name, String commitId) {
            if (!commits.containsKey(commitId)) {
                throw new DomainException("Unknown starting commit.");
            }

            if (branches.containsKey(name)) {
                throw new DomainException("Branch already exists.");
            }

            branches.put(
                name,
                new Branch(name, commitId, false)
            );

            audit("system", "BRANCH_CREATED", name);
        }

        void protectBranch(
            String branchName,
            ReviewPolicy policy,
            String administrator
        ) {
            requireRole(administrator, ActorRole.ADMINISTRATOR);

            Branch branch = branches.get(branchName);

            if (branch == null) {
                throw new DomainException("Branch does not exist.");
            }

            // Protection is represented by immutable policy association.
            policies.put(branchName, policy);

            audit(
                administrator,
                "BRANCH_PROTECTION_UPDATED",
                branchName
            );
        }

        int createPullRequest(
            String title,
            String author,
            String source,
            String target,
            boolean draft
        ) {
            requireRole(
                author,
                ActorRole.DEVELOPER,
                ActorRole.MAINTAINER,
                ActorRole.ADMINISTRATOR
            );

            Branch sourceBranch = branches.get(source);
            Branch targetBranch = branches.get(target);

            if (sourceBranch == null || targetBranch == null) {
                throw new DomainException("Unknown branch.");
            }

            if (source.equals(target)) {
                throw new DomainException(
                    "Source and target branches must differ."
                );
            }

            if (sourceBranch.headCommit().equals(targetBranch.headCommit())) {
                throw new DomainException("No proposed changes exist.");
            }

            int id = prSequence.getAndIncrement();

            PullRequest pr = new PullRequest(
                id,
                title,
                author,
                source,
                target,
                targetBranch.headCommit(),
                sourceBranch.headCommit(),
                draft
            );

            pullRequests.put(id, pr);

            audit(author, "PULL_REQUEST_CREATED", "#" + id);

            return id;
        }

        void publishDraft(int id, String actor) {
            PullRequest pr = getPullRequest(id);

            requireRole(
                actor,
                ActorRole.DEVELOPER,
                ActorRole.MAINTAINER,
                ActorRole.ADMINISTRATOR
            );

            pr.publish();

            audit(actor, "DRAFT_PUBLISHED", "#" + id);
        }

        private PullRequest getPullRequest(int id) {
            PullRequest pr = pullRequests.get(id);

            if (pr == null) {
                throw new DomainException(
                    "Pull Request does not exist."
                );
            }

            return pr;
        }

        void submitReview(
            int id,
            String reviewer,
            ReviewDecision decision,
            String comment
        ) {
            requireRole(
                reviewer,
                ActorRole.REVIEWER,
                ActorRole.MAINTAINER,
                ActorRole.ADMINISTRATOR
            );

            PullRequest pr = getPullRequest(id);

            if (pr.state() != PullRequestState.OPEN) {
                throw new DomainException("PR is not open.");
            }

            if (pr.author().equals(reviewer)) {
                throw new DomainException("Self-approval is prohibited.");
            }

            Review review = new Review(
                reviewer,
                decision,
                pr.headCommit(),
                comment,
                Instant.now()
            );

            pr.addReview(review);

            audit(reviewer, "REVIEW_SUBMITTED", "#" + id);
        }

        void updateStatusCheck(
            int id,
            String name,
            CheckStatus status,
            String ciActor
        ) {
            requireRole(ciActor, ActorRole.CI_SYSTEM);

            PullRequest pr = getPullRequest(id);

            pr.updateCheck(
                new StatusCheck(
                    name,
                    status,
                    pr.headCommit(),
                    Instant.now()
                )
            );

            audit(ciActor, "STATUS_CHECK_UPDATED", "#" + id);
        }

        void addConversation(int id) {
            getPullRequest(id).addConversation();
        }

        void resolveConversation(int id, String maintainer) {
            requireRole(
                maintainer,
                ActorRole.MAINTAINER,
                ActorRole.ADMINISTRATOR
            );

            getPullRequest(id).resolveConversation();

            audit(maintainer, "CONVERSATION_RESOLVED", "#" + id);
        }

        void synchronizeBase(int id) {
            PullRequest pr = getPullRequest(id);

            if (pr.state() != PullRequestState.OPEN) {
                throw new DomainException("PR is not open.");
            }

            Branch source = branches.get(pr.sourceBranch());
            Branch target = branches.get(pr.targetBranch());

            ReviewPolicy policy = policies.getOrDefault(
                pr.targetBranch(),
                ReviewPolicy.enterpriseDefault()
            );

            pr.synchronize(
                target.headCommit(),
                source.headCommit(),
                policy.dismissStaleApprovals()
            );

            audit("system", "BASE_SYNCHRONIZED", "#" + id);
        }

        EligibilityResult evaluate(int id) {
            PullRequest pr = getPullRequest(id);

            ReviewPolicy policy = policies.getOrDefault(
                pr.targetBranch(),
                ReviewPolicy.enterpriseDefault()
            );

            List<String> reasons = new ArrayList<>();

            if (pr.state() != PullRequestState.OPEN) {
                reasons.add("Pull Request is not open.");
            }

            Branch target = branches.get(pr.targetBranch());

            if (policy.requireUpToDateBranch() &&
                !pr.baseCommit().equals(target.headCommit())) {
                reasons.add("Target branch has advanced.");
            }

            Set<String> approvedReviewers = new HashSet<>();
            boolean changesRequested = false;

            for (Review review : pr.reviews()) {
                if (!review.reviewedCommit().equals(pr.headCommit())) {
                    continue;
                }

                if (review.decision() == ReviewDecision.APPROVED) {
                    approvedReviewers.add(review.reviewer());
                }

                if (review.decision() ==
                    ReviewDecision.CHANGES_REQUESTED) {
                    changesRequested = true;
                }
            }

            if (changesRequested) {
                reasons.add("Changes have been requested.");
            }

            if (approvedReviewers.size() < policy.requiredApprovals()) {
                reasons.add("Required approvals are missing.");
            }

            Map<String, StatusCheck> checks = pr.checks().stream()
                .collect(Collectors.toMap(
                    StatusCheck::name,
                    check -> check
                ));

            for (String required : policy.requiredChecks()) {
                StatusCheck check = checks.get(required);

                if (check == null ||
                    check.status() != CheckStatus.SUCCESS ||
                    !check.commitId().equals(pr.headCommit())) {
                    reasons.add(
                        "Check not successful for current commit: " + required
                    );
                }
            }

            if (policy.requireResolvedConversations() &&
                pr.unresolvedConversations() > 0) {
                reasons.add("Unresolved conversations remain.");
            }

            return new EligibilityResult(
                reasons.isEmpty(),
                reasons,
                approvedReviewers.size(),
                policy.requiredApprovals()
            );
        }

        void merge(
            int id,
            String actor,
            MergeStrategy strategy
        ) {
            requireRole(
                actor,
                ActorRole.MAINTAINER,
                ActorRole.ADMINISTRATOR
            );

            PullRequest pr = getPullRequest(id);
            EligibilityResult result = evaluate(id);

            if (!result.eligible()) {
                throw new DomainException(
                    "Merge rejected: " + String.join("; ", result.reasons())
                );
            }

            String mergeMessage = switch (strategy) {
                case MERGE_COMMIT -> "Merge commit";
                case SQUASH -> "Squash merge";
                case REBASE -> "Rebase merge";
            };

            String commitId = createCommit(
                mergeMessage + " for PR #" + id,
                actor
            );

            branches.get(pr.targetBranch()).advance(commitId);

            pr.markMerged();

            audit(actor, "PULL_REQUEST_MERGED", "#" + id);
        }

        void closePullRequest(int id, String actor) {
            requireRole(
                actor,
                ActorRole.DEVELOPER,
                ActorRole.MAINTAINER,
                ActorRole.ADMINISTRATOR
            );

            getPullRequest(id).close();

            audit(actor, "PULL_REQUEST_CLOSED", "#" + id);
        }

        void reopenPullRequest(int id, String actor) {
            requireRole(
                actor,
                ActorRole.MAINTAINER,
                ActorRole.ADMINISTRATOR
            );

            getPullRequest(id).reopen();

            audit(actor, "PULL_REQUEST_REOPENED", "#" + id);
        }

        DashboardMetrics dashboard() {
            int open = 0;
            int draft = 0;
            int merged = 0;
            int closed = 0;
            int eligible = 0;

            for (PullRequest pr : pullRequests.values()) {
                switch (pr.state()) {
                    case OPEN -> {
                        open++;
                        if (evaluate(pr.id()).eligible()) {
                            eligible++;
                        }
                    }
                    case DRAFT -> draft++;
                    case MERGED -> merged++;
                    case CLOSED -> closed++;
                }
            }

            return new DashboardMetrics(
                1,
                branches.size(),
                pullRequests.size(),
                open,
                draft,
                merged,
                closed,
                eligible,
                auditLog.size()
            );
        }

        List<AuditEvent> auditHistory() {
            return auditLog.stream()
                .sorted(Comparator.comparing(AuditEvent::timestamp).reversed())
                .toList();
        }

        void printDashboard() {
            DashboardMetrics metrics = dashboard();

            System.out.println("\n========== ENTERPRISE DASHBOARD ==========");
            System.out.println("Repository: " + repositoryName);
            System.out.println("Repositories: " + metrics.repositoryCount());
            System.out.println("Branches: " + metrics.branchCount());
            System.out.println("Pull Requests: " + metrics.totalPullRequests());
            System.out.println("Open: " + metrics.openPullRequests());
            System.out.println("Draft: " + metrics.draftPullRequests());
            System.out.println("Merged: " + metrics.mergedPullRequests());
            System.out.println("Closed: " + metrics.closedPullRequests());
            System.out.println("Merge Eligible: " + metrics.eligiblePullRequests());
            System.out.println("Audit Events: " + metrics.auditEvents());
            System.out.println("==========================================");
        }
    }

    public static void main(String[] args) {
        try {
            RepositoryService service =
                new RepositoryService("enterprise-admin-platform");

            service.registerActor("platform-team", ActorRole.ADMINISTRATOR);
            service.registerActor("developer", ActorRole.DEVELOPER);
            service.registerActor("reviewer-1", ActorRole.REVIEWER);
            service.registerActor("reviewer-2", ActorRole.REVIEWER);
            service.registerActor("ci", ActorRole.CI_SYSTEM);
            service.registerActor("release-manager", ActorRole.MAINTAINER);

            String initial = service.createCommit(
                "Initial release",
                "platform-team"
            );

            service.createBranch("main", initial);
            service.createBranch("feature/admin-dashboard", initial);

            String feature = service.createCommit(
                "Implement enterprise dashboard",
                "developer"
            );

            // The feature branch advances to the proposed commit.
            // A separate production adapter would apply the Git push.
            // The service models branch movement through branch synchronization.
            service.branches.get("feature/admin-dashboard").advance(feature);

            service.protectBranch(
                "main",
                ReviewPolicy.enterpriseDefault(),
                "platform-team"
            );

            int pr = service.createPullRequest(
                "Implement production admin dashboard",
                "developer",
                "feature/admin-dashboard",
                "main",
                false
            );

            service.submitReview(
                pr,
                "reviewer-1",
                ReviewDecision.APPROVED,
                "Implementation verified."
            );

            service.submitReview(
                pr,
                "reviewer-2",
                ReviewDecision.APPROVED,
                "Security and tests reviewed."
            );

            for (String check : List.of("build", "tests", "security")) {
                service.updateStatusCheck(
                    pr,
                    check,
                    CheckStatus.SUCCESS,
                    "ci"
                );
            }

            service.addConversation(pr);
            service.resolveConversation(pr, "release-manager");

            EligibilityResult result = service.evaluate(pr);

            System.out.println("Merge eligible: " + result.eligible());
            result.reasons().forEach(System.out::println);

            service.merge(
                pr,
                "release-manager",
                MergeStrategy.SQUASH
            );

            service.printDashboard();

        } catch (DomainException | IllegalArgumentException exception) {
            System.err.println("Governance failure: " + exception.getMessage());
            System.exit(1);
        }
    }
}
