import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;

/**
 * Enterprise-oriented model of selected JavaScript execution semantics.
 *
 * The scenario is a deployment orchestrator whose policy functions depend on
 * lexical bindings, closure state, and nested function execution.
 *
 * Compile and run:
 *   javac ExecutionSemantics.java
 *   java ExecutionSemantics
 *
 * This is a Java model of selected semantics, not a JavaScript interpreter.
 */
public class ExecutionSemantics {

    enum BindingKind {
        VAR,
        LET,
        CONST,
        FUNCTION,
        PARAMETER
    }

    static class ExecutionException extends RuntimeException {
        ExecutionException(String message) {
            super(message);
        }
    }

    static final class ReferenceError extends ExecutionException {
        ReferenceError(String message) {
            super(message);
        }
    }

    static final class AssignmentError extends ExecutionException {
        AssignmentError(String message) {
            super(message);
        }
    }

    static final class StackLimitError extends ExecutionException {
        StackLimitError(String message) {
            super(message);
        }
    }

    static final class Binding {
        private final String name;
        private BindingKind kind;
        private Object value;
        private boolean initialized;

        Binding(
                String name,
                BindingKind kind,
                Object value,
                boolean initialized
        ) {
            this.name = Objects.requireNonNull(name);
            this.kind = Objects.requireNonNull(kind);
            this.value = value;
            this.initialized = initialized;
        }

        Object read() {
            if (!initialized) {
                throw new ReferenceError(
                        "Cannot access '" + name + "' before initialization"
                );
            }
            return value;
        }

        void initialize(Object newValue) {
            if (initialized) {
                throw new AssignmentError(
                        "Binding '" + name + "' is already initialized"
                );
            }
            value = newValue;
            initialized = true;
        }

        void assign(Object newValue) {
            if (!initialized) {
                throw new ReferenceError(
                        "Cannot assign '" + name + "' before initialization"
                );
            }

            if (kind == BindingKind.CONST) {
                throw new AssignmentError(
                        "Assignment to constant binding '" + name + "'"
                );
            }

            value = newValue;
        }

        boolean isInitialized() {
            return initialized;
        }

        BindingKind kind() {
            return kind;
        }

        void promoteToFunction(Object functionValue) {
            kind = BindingKind.FUNCTION;
            value = functionValue;
            initialized = true;
        }
    }

    static final class LexicalEnvironment {
        private final String name;
        private final LexicalEnvironment outer;
        private final Map<String, Binding> bindings = new LinkedHashMap<>();

        LexicalEnvironment(String name, LexicalEnvironment outer) {
            this.name = Objects.requireNonNull(name);
            this.outer = outer;
        }

        void declare(
                String identifier,
                BindingKind kind,
                Object value,
                boolean initialized
        ) {
            Objects.requireNonNull(identifier);
            Objects.requireNonNull(kind);

            Binding existing = bindings.get(identifier);

            if (existing != null) {
                boolean compatible =
                        (existing.kind() == BindingKind.VAR
                                || existing.kind() == BindingKind.FUNCTION)
                        && (kind == BindingKind.VAR
                                || kind == BindingKind.FUNCTION);

                if (!compatible) {
                    throw new ExecutionException(
                            "Duplicate declaration of '" + identifier
                                    + "' in " + name
                    );
                }

                if (kind == BindingKind.FUNCTION) {
                    existing.promoteToFunction(value);
                }
                return;
            }

            if (kind == BindingKind.VAR
                    || kind == BindingKind.FUNCTION) {
                initialized = true;
            }

            bindings.put(
                    identifier,
                    new Binding(
                            identifier,
                            kind,
                            value,
                            initialized
                    )
            );
        }

        Binding resolve(String identifier) {
            LexicalEnvironment current = this;

            while (current != null) {
                Binding found = current.bindings.get(identifier);

                if (found != null) {
                    return found;
                }

                current = current.outer;
            }

            throw new ReferenceError(
                    "Identifier '" + identifier + "' is not defined"
            );
        }

        Object get(String identifier) {
            return resolve(identifier).read();
        }

        void assign(String identifier, Object value) {
            resolve(identifier).assign(value);
        }

        void initialize(String identifier, Object value) {
            Binding binding = bindings.get(identifier);

            if (binding == null) {
                throw new ReferenceError(
                        "Cannot initialize missing local binding '" + identifier
                                + "'"
                );
            }

            binding.initialize(value);
        }

        String name() {
            return name;
        }
    }

    static final class ExecutionContext {
        private final String name;
        private final LexicalEnvironment lexicalEnvironment;
        private final LexicalEnvironment variableEnvironment;
        private final Object thisValue;

        ExecutionContext(
                String name,
                LexicalEnvironment lexicalEnvironment,
                LexicalEnvironment variableEnvironment,
                Object thisValue
        ) {
            this.name = name;
            this.lexicalEnvironment = lexicalEnvironment;
            this.variableEnvironment = variableEnvironment;
            this.thisValue = thisValue;
        }

        String name() {
            return name;
        }

        LexicalEnvironment lexicalEnvironment() {
            return lexicalEnvironment;
        }

        LexicalEnvironment variableEnvironment() {
            return variableEnvironment;
        }

        Object thisValue() {
            return thisValue;
        }
    }

    static final class CallStack {
        private final int maximumDepth;
        private final Deque<ExecutionContext> frames = new ArrayDeque<>();

        CallStack(int maximumDepth) {
            if (maximumDepth < 1) {
                throw new IllegalArgumentException(
                        "maximumDepth must be positive"
                );
            }
            this.maximumDepth = maximumDepth;
        }

        void push(ExecutionContext context) {
            if (frames.size() >= maximumDepth) {
                throw new StackLimitError(
                        "Maximum simulated call stack size exceeded"
                );
            }

            frames.push(context);
            System.out.printf(
                    "PUSH %-28s depth=%d%n",
                    context.name(),
                    frames.size()
            );
        }

        void pop() {
            if (frames.isEmpty()) {
                throw new IllegalStateException("Call stack is empty");
            }

            ExecutionContext removed = frames.pop();
            System.out.printf(
                    "POP  %-28s depth=%d%n",
                    removed.name(),
                    frames.size()
            );
        }

        int depth() {
            return frames.size();
        }
    }

    @FunctionalInterface
    interface FunctionBody {
        Object execute(ExecutionContext context, List<Object> arguments);
    }

    static final class JsFunction {
        private final String name;
        private final List<String> parameters;
        private final LexicalEnvironment closure;
        private final FunctionBody body;
        private final CallStack stack;

        JsFunction(
                String name,
                List<String> parameters,
                LexicalEnvironment closure,
                FunctionBody body,
                CallStack stack
        ) {
            this.name = Objects.requireNonNull(name);
            this.parameters = List.copyOf(parameters);
            this.closure = Objects.requireNonNull(closure);
            this.body = Objects.requireNonNull(body);
            this.stack = Objects.requireNonNull(stack);
        }

        Object call(Object... suppliedArguments) {
            LexicalEnvironment local =
                    new LexicalEnvironment(name + ":local", closure);

            List<Object> arguments = new ArrayList<>();

            for (Object argument : suppliedArguments) {
                arguments.add(argument);
            }

            for (int index = 0; index < parameters.size(); index++) {
                Object value = index < arguments.size()
                        ? arguments.get(index)
                        : Undefined.VALUE;

                local.declare(
                        parameters.get(index),
                        BindingKind.PARAMETER,
                        value,
                        true
                );
            }

            ExecutionContext context = new ExecutionContext(
                    name,
                    local,
                    local,
                    Undefined.VALUE
            );

            stack.push(context);

            try {
                return body.execute(context, List.copyOf(arguments));
            } finally {
                // Preserve call-stack integrity if business logic throws.
                stack.pop();
            }
        }
    }

    enum Undefined {
        VALUE
    }

    static void demonstrateHoisting() {
        System.out.println("\n=== Hoisting and initialization ===");

        LexicalEnvironment functionEnvironment =
                new LexicalEnvironment("deploymentPolicy", null);

        functionEnvironment.declare(
                "retryCount",
                BindingKind.VAR,
                Undefined.VALUE,
                false
        );

        functionEnvironment.declare(
                "releasePolicy",
                BindingKind.FUNCTION,
                "canary",
                true
        );

        System.out.println(
                "var before assignment: "
                        + functionEnvironment.get("retryCount")
        );

        System.out.println(
                "function binding: "
                        + functionEnvironment.get("releasePolicy")
        );

        functionEnvironment.assign("retryCount", 3);

        System.out.println(
                "var after assignment: "
                        + functionEnvironment.get("retryCount")
        );

        functionEnvironment.declare(
                "targetRegion",
                BindingKind.LET,
                Undefined.VALUE,
                false
        );

        try {
            functionEnvironment.get("targetRegion");
        } catch (ReferenceError error) {
            System.out.println("Temporal dead zone: " + error.getMessage());
        }

        functionEnvironment.initialize("targetRegion", "ap-south-1");

        System.out.println(
                "Initialized let: "
                        + functionEnvironment.get("targetRegion")
        );

        functionEnvironment.declare(
                "immutableRelease",
                BindingKind.CONST,
                "2026.10",
                true
        );

        try {
            functionEnvironment.assign("immutableRelease", "2026.11");
        } catch (AssignmentError error) {
            System.out.println("Const reassignment: " + error.getMessage());
        }
    }

    static void demonstrateClosureState() {
        System.out.println("\n=== Closure state in a release service ===");

        CallStack stack = new CallStack(20);
        LexicalEnvironment global = new LexicalEnvironment("global", null);

        global.declare(
                "serviceName",
                BindingKind.CONST,
                "artifact-service",
                true
        );

        JsFunction generatorFactory = new JsFunction(
                "createArtifactIdGenerator",
                List.of("prefix"),
                global,
                (context, arguments) -> {
                    String prefix = String.valueOf(
                            context.lexicalEnvironment().get("prefix")
                    );

                    context.lexicalEnvironment().declare(
                            "sequence",
                            BindingKind.LET,
                            500,
                            true
                    );

                    LexicalEnvironment captured =
                            context.lexicalEnvironment();

                    return new JsFunction(
                            "nextArtifactId",
                            List.of(),
                            captured,
                            (innerContext, innerArguments) -> {
                                int sequence = (int) innerContext
                                        .lexicalEnvironment()
                                        .get("sequence");

                                innerContext.lexicalEnvironment().assign(
                                        "sequence",
                                        sequence + 1
                                );

                                String service = String.valueOf(
                                        innerContext.lexicalEnvironment()
                                                .get("serviceName")
                                );

                                return prefix + "-" + service + "-" + sequence;
                            },
                            stack
                    );
                },
                stack
        );

        Object created = generatorFactory.call("REL");
        JsFunction nextArtifactId = (JsFunction) created;

        System.out.println(nextArtifactId.call());
        System.out.println(nextArtifactId.call());
        System.out.println(nextArtifactId.call());

        System.out.println("Remaining stack depth: " + stack.depth());
    }

    static void demonstrateScopeResolution() {
        System.out.println("\n=== Scope resolution and shadowing ===");

        LexicalEnvironment global = new LexicalEnvironment("global", null);
        global.declare("region", BindingKind.CONST, "India", true);

        LexicalEnvironment module =
                new LexicalEnvironment("releaseModule", global);
        module.declare("region", BindingKind.LET, "Singapore", true);

        LexicalEnvironment block =
                new LexicalEnvironment("releaseBlock", module);
        block.declare("region", BindingKind.CONST, "Frankfurt", true);

        System.out.println("Block: " + block.get("region"));
        System.out.println("Module: " + module.get("region"));
        System.out.println("Global: " + global.get("region"));

        try {
            block.get("missingReviewPolicy");
        } catch (ReferenceError error) {
            System.out.println("Unresolved name: " + error.getMessage());
        }
    }

    static void demonstrateNestedCallsAndFailure() {
        System.out.println("\n=== Nested execution and failure cleanup ===");

        CallStack stack = new CallStack(12);
        LexicalEnvironment global = new LexicalEnvironment("global", null);

        JsFunction verify = new JsFunction(
                "verifySignature",
                List.of("artifact"),
                global,
                (context, arguments) -> {
                    Object artifact =
                            context.lexicalEnvironment().get("artifact");

                    if (artifact == Undefined.VALUE
                            || String.valueOf(artifact).isBlank()) {
                        throw new IllegalArgumentException(
                                "Artifact ID is required"
                        );
                    }

                    return "verified:" + artifact;
                },
                stack
        );

        JsFunction publish = new JsFunction(
                "publishRelease",
                List.of("artifact"),
                global,
                (context, arguments) -> {
                    Object artifact =
                            context.lexicalEnvironment().get("artifact");

                    Object result = verify.call(artifact);
                    System.out.println("Verification: " + result);

                    return "published:" + artifact;
                },
                stack
        );

        System.out.println(publish.call("artifact-804"));

        try {
            publish.call("");
        } catch (IllegalArgumentException error) {
            System.out.println("Publish rejected: " + error.getMessage());
        }

        System.out.println("Stack after failure: " + stack.depth());
    }

    public static void main(String[] args) {
        demonstrateHoisting();
        demonstrateClosureState();
        demonstrateScopeResolution();
        demonstrateNestedCallsAndFailure();

        System.out.println("\nExecution semantics case study completed.");
    }
}
