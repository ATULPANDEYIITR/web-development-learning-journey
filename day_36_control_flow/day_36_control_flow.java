import java.util.ArrayList;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.function.Predicate;

/*
 * Enterprise-oriented case study:
 * a release orchestration service evaluates validation stages before a
 * production operation can proceed.
 *
 * The domain model makes control-flow rules explicit through states,
 * policies, validation, loops, early termination, and exception handling.
 */
public class ControlFlowEnterpriseDemo {

    enum StageState {
        PENDING,
        RUNNING,
        PASSED,
        FAILED,
        SKIPPED
    }

    enum Command {
        BUILD,
        TEST,
        DEPLOY,
        STATUS
    }

    record ValidationStage(
        String name,
        boolean enabled,
        boolean expectedToPass
    ) {
        ValidationStage {
            Objects.requireNonNull(name, "name");

            if (name.isBlank()) {
                throw new IllegalArgumentException("stage name cannot be blank");
            }
        }
    }

    static final class StageExecution {
        private final ValidationStage definition;
        private StageState state = StageState.PENDING;

        StageExecution(ValidationStage definition) {
            this.definition = Objects.requireNonNull(definition);
        }

        StageState state() {
            return state;
        }

        String name() {
            return definition.name();
        }

        void execute() {
            /*
             * State transitions are guarded. A completed stage cannot be
             * accidentally executed again.
             */
            switch (state) {
                case PENDING -> {
                    if (!definition.enabled()) {
                        state = StageState.SKIPPED;
                        return;
                    }

                    state = StageState.RUNNING;
                }

                case RUNNING -> throw new IllegalStateException(
                    "stage is already running: " + name()
                );

                case PASSED, FAILED, SKIPPED -> throw new IllegalStateException(
                    "stage is already completed: " + name()
                );
            }

            if (definition.expectedToPass()) {
                state = StageState.PASSED;
            } else {
                state = StageState.FAILED;
            }
        }
    }

    static final class ReleasePolicy {
        private final int maximumFailures;
        private final boolean requireAllEnabledStages;

        ReleasePolicy(int maximumFailures, boolean requireAllEnabledStages) {
            if (maximumFailures < 0) {
                throw new IllegalArgumentException(
                    "maximumFailures cannot be negative"
                );
            }

            this.maximumFailures = maximumFailures;
            this.requireAllEnabledStages = requireAllEnabledStages;
        }

        boolean allows(List<StageExecution> stages) {
            int failures = 0;

            for (StageExecution stage : stages) {
                if (stage.state() == StageState.FAILED) {
                    failures++;

                    if (failures > maximumFailures) {
                        return false;
                    }
                }

                if (
                    requireAllEnabledStages &&
                    stage.state() == StageState.PENDING
                ) {
                    return false;
                }
            }

            return true;
        }
    }

    static final class ReleaseService {
        private final ReleasePolicy policy;

        ReleaseService(ReleasePolicy policy) {
            this.policy = Objects.requireNonNull(policy);
        }

        boolean execute(List<StageExecution> stages) {
            int failures = 0;

            for (StageExecution stage : stages) {
                if (stage.state() == StageState.SKIPPED) {
                    continue;
                }

                try {
                    stage.execute();
                } catch (IllegalStateException error) {
                    System.err.println(
                        "Stage execution error: " + error.getMessage()
                    );
                    return false;
                }

                if (stage.state() == StageState.FAILED) {
                    failures++;

                    if (failures > 1) {
                        /*
                         * Once the policy cannot be satisfied, there is no
                         * value in executing expensive later stages.
                         */
                        break;
                    }
                }
            }

            return policy.allows(stages);
        }
    }

    static Command parseCommand(String value) {
        Objects.requireNonNull(value, "command");

        return switch (value.trim().toLowerCase()) {
            case "build" -> Command.BUILD;
            case "test" -> Command.TEST;
            case "deploy" -> Command.DEPLOY;
            case "status" -> Command.STATUS;
            default -> throw new IllegalArgumentException(
                "unknown command: " + value
            );
        };
    }

    static String commandDescription(Command command) {
        return switch (command) {
            case BUILD -> "compile application artifacts";
            case TEST -> "execute validation suite";
            case DEPLOY -> "release validated artifact";
            case STATUS -> "inspect release state";
        };
    }

    static List<Integer> filterPositive(List<Integer> values) {
        List<Integer> result = new ArrayList<>();

        for (Integer value : values) {
            if (value == null) {
                continue;
            }

            if (value <= 0) {
                continue;
            }

            result.add(value);
        }

        return result;
    }

    static <T> T findFirst(
        Iterable<T> values,
        Predicate<T> condition
    ) {
        Objects.requireNonNull(values);
        Objects.requireNonNull(condition);

        for (T value : values) {
            if (condition.test(value)) {
                return value;
            }
        }

        return null;
    }

    static double determineDiscount(
        double amount,
        String customerType,
        double riskScore
    ) {
        if (amount < 0) {
            throw new IllegalArgumentException("amount cannot be negative");
        }

        if (riskScore < 0 || riskScore > 1) {
            throw new IllegalArgumentException(
                "riskScore must be between zero and one"
            );
        }

        if (riskScore >= 0.9) {
            return 0.0;
        }

        if (amount == 0) {
            return 0.0;
        }

        if ("enterprise".equals(customerType)) {
            if (amount >= 10000) {
                return 0.15;
            }

            return 0.10;
        }

        if ("student".equals(customerType)) {
            return 0.20;
        }

        return 0.0;
    }

    static Map<StageState, Integer> summarizeStages(
        List<StageExecution> stages
    ) {
        Map<StageState, Integer> result = new EnumMap<>(StageState.class);

        for (StageState state : StageState.values()) {
            result.put(state, 0);
        }

        for (StageExecution stage : stages) {
            StageState state = stage.state();
            result.put(state, result.get(state) + 1);
        }

        return result;
    }

    public static void main(String[] args) {
        System.out.println("Command dispatch");

        for (String commandText : List.of(
            "build",
            "test",
            "deploy",
            "status"
        )) {
            Command command = parseCommand(commandText);

            System.out.println(
                command + " -> " + commandDescription(command)
            );
        }

        System.out.println("\nRelease orchestration");

        List<StageExecution> stages = List.of(
            new StageExecution(
                new ValidationStage("compile", true, true)
            ),
            new StageExecution(
                new ValidationStage("unit-tests", true, true)
            ),
            new StageExecution(
                new ValidationStage("security-scan", true, false)
            ),
            new StageExecution(
                new ValidationStage("documentation", false, true)
            ),
            new StageExecution(
                new ValidationStage("package", true, true)
            )
        );

        ReleasePolicy policy = new ReleasePolicy(1, true);
        ReleaseService service = new ReleaseService(policy);

        boolean releaseAllowed = service.execute(stages);

        for (StageExecution stage : stages) {
            System.out.println(
                stage.name() + " -> " + stage.state()
            );
        }

        System.out.println("Release allowed: " + releaseAllowed);

        System.out.println("\nStage state distribution");
        summarizeStages(stages).forEach(
            (state, count) -> System.out.println(state + ": " + count)
        );

        System.out.println("\nLoop filtering");
        System.out.println(
            filterPositive(List.of(4, -2, 7, 0, 11, null, 14))
        );

        System.out.println("\nEarly search");
        Integer firstLargeValue = findFirst(
            List.of(2, 4, 8, 15, 22, 30),
            value -> value > 20
        );

        System.out.println("First value above twenty: " + firstLargeValue);

        System.out.println("\nBusiness rules");
        System.out.println(
            "Enterprise discount: " +
            determineDiscount(25000, "enterprise", 0.1)
        );
        System.out.println(
            "Student discount: " +
            determineDiscount(500, "student", 0.2)
        );
        System.out.println(
            "High-risk discount: " +
            determineDiscount(500, "consumer", 0.95)
        );

        System.out.println("\nBounded processing");

        int processed = 0;

        for (int value = 1; value <= 30; value++) {
            if (value % 2 != 0) {
                continue;
            }

            if (value > 12) {
                break;
            }

            processed++;
            System.out.println("Processed: " + value);
        }

        System.out.println("Processed count: " + processed);
    }
}
