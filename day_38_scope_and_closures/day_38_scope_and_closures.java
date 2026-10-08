import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.function.Predicate;

/**
 * Scope and Closures through an enterprise repository-governance model.
 *
 * Java closures are implemented through lambdas and captured variables.
 * Local variables captured by lambdas must be final or effectively final.
 * Mutable state can instead live inside an object owned by the lambda.
 */
public class ScopeAndClosures {

    private static final String SYSTEM_NAME = "Enterprise Repository Governance";
    private static int globalEvaluationCount = 0;

    public static void main(String[] args) {
        System.out.println(SYSTEM_NAME);

        demonstrateGlobalAndMethodScope();
        demonstrateBlockScope();
        demonstrateLexicalCapture();
        demonstratePolicyFactories();
        demonstrateStatefulClosure();
        demonstrateFunctionalComposition();
        demonstrateEnterpriseWorkflow();
        runAssertions();
    }

    // -------------------------------------------------------------------------
    // Global/static scope and method-local scope
    // -------------------------------------------------------------------------

    private static void demonstrateGlobalAndMethodScope() {
        System.out.println("\n=== Global/static and method scope ===");

        globalEvaluationCount++;
        System.out.println("Global evaluation count: " + globalEvaluationCount);

        String methodValue = "visible only in this method";
        System.out.println(methodValue);

        {
            String blockValue = "visible only inside this block";
            System.out.println(blockValue);
        }

        // blockValue cannot be referenced here because Java block scope ends
        // at the closing brace.
    }

    // -------------------------------------------------------------------------
    // Block scope
    // -------------------------------------------------------------------------

    private static void demonstrateBlockScope() {
        System.out.println("\n=== Block scope ===");

        int outerThreshold = 70;

        if (outerThreshold >= 70) {
            int approvalThreshold = 2;
            System.out.println(
                "Approval threshold inside block: " + approvalThreshold
            );
        }

        // approvalThreshold is unavailable here.
        System.out.println("Outer threshold: " + outerThreshold);

        for (int index = 0; index < 3; index++) {
            System.out.println("Loop-local index: " + index);
        }

        // index is unavailable after the for block.
    }

    // -------------------------------------------------------------------------
    // Lexical capture
    // -------------------------------------------------------------------------

    private static void demonstrateLexicalCapture() {
        System.out.println("\n=== Lexical capture ===");

        String repository = "production-api";

        Predicate<PullRequest> repositoryPolicy = request ->
            request.repository().equals(repository);

        PullRequest matching = new PullRequest(
            "PR-101",
            repository,
            "feature/scopes",
            "main",
            true,
            List.of()
        );

        PullRequest different = new PullRequest(
            "PR-102",
            "analytics-api",
            "feature/scopes",
            "main",
            true,
            List.of()
        );

        System.out.println("Matching repository: " +
            repositoryPolicy.test(matching));

        System.out.println("Different repository: " +
            repositoryPolicy.test(different));

        /*
         * repository is effectively final. Java does not allow a lambda to
         * capture a local variable that is later reassigned because doing so
         * would make the captured local's semantics ambiguous.
         */
    }

    // -------------------------------------------------------------------------
    // Domain model
    // -------------------------------------------------------------------------

    enum ReviewDecision {
        APPROVED,
        CHANGES_REQUESTED,
        COMMENTED
    }

    record Review(
        String reviewer,
        ReviewDecision decision,
        int qualityScore
    ) {
        Review {
            Objects.requireNonNull(reviewer, "reviewer");
            Objects.requireNonNull(decision, "decision");

            if (qualityScore < 0 || qualityScore > 100) {
                throw new IllegalArgumentException(
                    "qualityScore must be between 0 and 100"
                );
            }
        }
    }

    record PullRequest(
        String id,
        String repository,
        String sourceBranch,
        String targetBranch,
        boolean statusChecksPassed,
        List<Review> reviews
    ) {
        PullRequest {
            Objects.requireNonNull(id, "id");
            Objects.requireNonNull(repository, "repository");
            Objects.requireNonNull(sourceBranch, "sourceBranch");
            Objects.requireNonNull(targetBranch, "targetBranch");
            Objects.requireNonNull(reviews, "reviews");

            if (sourceBranch.isBlank() || targetBranch.isBlank()) {
                throw new IllegalArgumentException(
                    "branch names cannot be blank"
                );
            }

            reviews = List.copyOf(reviews);
        }
    }

    // -------------------------------------------------------------------------
    // Explicit policy abstractions
    // -------------------------------------------------------------------------

    @FunctionalInterface
    interface Policy {
        boolean evaluate(PullRequest request);
    }

    record NamedPolicy(String name, Policy policy) {
        NamedPolicy {
            Objects.requireNonNull(name, "name");
            Objects.requireNonNull(policy, "policy");
        }
    }

    static final class GovernanceService {

        private final List<NamedPolicy> policies;

        GovernanceService(List<NamedPolicy> policies) {
            this.policies = List.copyOf(policies);
        }

        boolean eligible(PullRequest request) {
            for (NamedPolicy namedPolicy : policies) {
                boolean passed = namedPolicy.policy().evaluate(request);

                System.out.printf(
                    "%-30s %s%n",
                    namedPolicy.name(),
                    passed ? "PASS" : "FAIL"
                );

                if (!passed) {
                    return false;
                }
            }

            return true;
        }
    }

    // -------------------------------------------------------------------------
    // Closure factories
    // -------------------------------------------------------------------------

    private static Policy branchPolicy(String protectedBranch) {
        String capturedBranch = Objects.requireNonNull(protectedBranch);

        /*
         * capturedBranch is effectively final and becomes part of the lambda's
         * captured lexical environment.
         */
        return request -> request.targetBranch().equals(capturedBranch);
    }

    private static Policy statusPolicy(boolean checksRequired) {
        return request -> !checksRequired || request.statusChecksPassed();
    }

    private static Policy approvalPolicy(int requiredApprovals) {
        if (requiredApprovals < 1) {
            throw new IllegalArgumentException(
                "requiredApprovals must be positive"
            );
        }

        return request -> request.reviews().stream()
            .filter(review -> review.decision() == ReviewDecision.APPROVED)
            .count() >= requiredApprovals;
    }

    private static Policy qualityPolicy(int minimumQuality) {
        if (minimumQuality < 0 || minimumQuality > 100) {
            throw new IllegalArgumentException(
                "minimumQuality must be between 0 and 100"
            );
        }

        return request -> request.reviews().stream()
            .mapToInt(Review::qualityScore)
            .average()
            .orElse(0.0) >= minimumQuality;
    }

    private static void demonstratePolicyFactories() {
        System.out.println("\n=== Policy closures ===");

        PullRequest request = new PullRequest(
            "PR-200",
            "production-api",
            "feature/closure-model",
            "main",
            true,
            List.of(
                new Review("alice", ReviewDecision.APPROVED, 94),
                new Review("bob", ReviewDecision.APPROVED, 88)
            )
        );

        List<NamedPolicy> policies = List.of(
            new NamedPolicy(
                "Protected target branch",
                branchPolicy("main")
            ),
            new NamedPolicy(
                "Required status checks",
                statusPolicy(true)
            ),
            new NamedPolicy(
                "Required approvals",
                approvalPolicy(2)
            ),
            new NamedPolicy(
                "Minimum review quality",
                qualityPolicy(80)
            )
        );

        GovernanceService service = new GovernanceService(policies);

        System.out.println(
            "Merge eligible: " + service.eligible(request)
        );
    }

    // -------------------------------------------------------------------------
    // Stateful closure through object-owned mutable state
    // -------------------------------------------------------------------------

    private static void demonstrateStatefulClosure() {
        System.out.println("\n=== Stateful lambda ===");

        class Counter {
            private int value;

            int next() {
                return ++value;
            }
        }

        Counter counter = new Counter();

        java.util.function.Supplier<Integer> nextValue = counter::next;

        System.out.println(nextValue.get());
        System.out.println(nextValue.get());
        System.out.println(nextValue.get());

        /*
         * Java local variables captured by lambdas cannot be reassigned.
         * Mutable state can still be modeled safely by capturing an object
         * whose internal fields change.
         */
    }

    // -------------------------------------------------------------------------
    // Functional composition
    // -------------------------------------------------------------------------

    private static void demonstrateFunctionalComposition() {
        System.out.println("\n=== Functional composition ===");

        Predicate<PullRequest> targetIsMain =
            request -> request.targetBranch().equals("main");

        Predicate<PullRequest> checksPassed =
            PullRequest::statusChecksPassed;

        Predicate<PullRequest> hasApproval =
            request -> request.reviews().stream()
                .anyMatch(
                    review ->
                        review.decision() == ReviewDecision.APPROVED
                );

        Predicate<PullRequest> eligibleForReview =
            targetIsMain
                .and(checksPassed)
                .and(hasApproval);

        PullRequest request = new PullRequest(
            "PR-300",
            "orders-api",
            "feature/payment",
            "main",
            true,
            List.of(
                new Review(
                    "reviewer",
                    ReviewDecision.APPROVED,
                    91
                )
            )
        );

        System.out.println(
            "Composed predicate result: " +
            eligibleForReview.test(request)
        );
    }

    // -------------------------------------------------------------------------
    // Enterprise workflow
    // -------------------------------------------------------------------------

    private static void demonstrateEnterpriseWorkflow() {
        System.out.println("\n=== Enterprise workflow ===");

        List<PullRequest> requests = new ArrayList<>();

        requests.add(new PullRequest(
            "PR-401",
            "payments",
            "feature/refund",
            "main",
            true,
            List.of(
                new Review("alice", ReviewDecision.APPROVED, 93),
                new Review("bob", ReviewDecision.APPROVED, 90)
            )
        ));

        requests.add(new PullRequest(
            "PR-402",
            "payments",
            "feature/risky-change",
            "main",
            false,
            List.of(
                new Review(
                    "alice",
                    ReviewDecision.CHANGES_REQUESTED,
                    75
                )
            )
        ));

        Policy productionRepository = request ->
            request.repository().equals("payments");

        Policy noChangeRequests = request ->
            request.reviews().stream().noneMatch(
                review ->
                    review.decision() == ReviewDecision.CHANGES_REQUESTED
            );

        Policy twoApprovals = approvalPolicy(2);

        for (PullRequest request : requests) {
            boolean accepted =
                productionRepository.evaluate(request)
                && noChangeRequests.evaluate(request)
                && twoApprovals.evaluate(request);

            System.out.printf(
                "%s -> %s%n",
                request.id(),
                accepted ? "ACCEPTED" : "BLOCKED"
            );
        }

        /*
         * A policy object captures the rule itself. The service does not need
         * to know how the rule was constructed, which separates policy
         * configuration from workflow evaluation.
         */
    }

    // -------------------------------------------------------------------------
    // Executable checks
    // -------------------------------------------------------------------------

    private static void runAssertions() {
        Policy branch = branchPolicy("main");

        PullRequest validRequest = new PullRequest(
            "PR-TEST",
            "test-repository",
            "feature/test",
            "main",
            true,
            List.of(
                new Review("a", ReviewDecision.APPROVED, 95),
                new Review("b", ReviewDecision.APPROVED, 90)
            )
        );

        assert branch.evaluate(validRequest);

        Policy approvals = approvalPolicy(2);
        assert approvals.evaluate(validRequest);

        Policy quality = qualityPolicy(90);
        assert quality.evaluate(validRequest);

        System.out.println("\nAll Java scope and closure assertions passed.");
    }
}
