#include <algorithm>
#include <chrono>
#include <functional>
#include <iomanip>
#include <iostream>
#include <map>
#include <memory>
#include <optional>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

/*
 * Repository release automation case study.
 *
 * This C++17 program uses a small expression evaluator to illustrate the
 * relationship between a JavaScript-like call stack, execution contexts,
 * lexical environments, and hoisting during a deployment-policy evaluation.
 *
 * The evaluator is deliberately limited to a small, explicit expression
 * language. It is not a complete JavaScript interpreter.
 */

class ExecutionError : public std::runtime_error {
public:
    using std::runtime_error::runtime_error;
};

class ReferenceError : public ExecutionError {
public:
    using ExecutionError::ExecutionError;
};

class TypeError : public ExecutionError {
public:
    using ExecutionError::ExecutionError;
};

class StackLimitError : public ExecutionError {
public:
    using ExecutionError::ExecutionError;
};

enum class BindingKind {
    Var,
    Let,
    Const,
    Function,
    Parameter
};

struct Value {
    std::string data;

    explicit Value(std::string value = "undefined")
        : data(std::move(value)) {}
};

struct Binding {
    BindingKind kind;
    Value value;
    bool initialized;
};

class Environment : public std::enable_shared_from_this<Environment> {
public:
    explicit Environment(
        std::string name,
        std::shared_ptr<Environment> outer = nullptr
    )
        : name_(std::move(name)), outer_(std::move(outer)) {}

    const std::string& name() const {
        return name_;
    }

    void declare(
        const std::string& name,
        BindingKind kind,
        Value value = Value{},
        bool initialized = false
    ) {
        auto found = bindings_.find(name);

        if (found != bindings_.end()) {
            const bool compatible =
                (found->second.kind == BindingKind::Var ||
                 found->second.kind == BindingKind::Function) &&
                (kind == BindingKind::Var ||
                 kind == BindingKind::Function);

            if (compatible) {
                if (kind == BindingKind::Function) {
                    found->second.kind = BindingKind::Function;
                    found->second.value = std::move(value);
                    found->second.initialized = true;
                }
                return;
            }

            throw TypeError(
                "Duplicate lexical declaration '" + name +
                "' in environment '" + name_ + "'"
            );
        }

        if (kind == BindingKind::Var || kind == BindingKind::Function) {
            initialized = true;
        }

        bindings_.emplace(
            name,
            Binding{kind, std::move(value), initialized}
        );
    }

    Value get(const std::string& name) const {
        const Environment* environment = this;

        while (environment != nullptr) {
            auto found = environment->bindings_.find(name);

            if (found != environment->bindings_.end()) {
                if (!found->second.initialized) {
                    throw ReferenceError(
                        "Cannot access '" + name +
                        "' before initialization"
                    );
                }
                return found->second.value;
            }

            environment = environment->outer_.get();
        }

        throw ReferenceError("'" + name + "' is not defined");
    }

    void initialize(const std::string& name, Value value) {
        auto found = bindings_.find(name);

        if (found == bindings_.end()) {
            throw ReferenceError(
                "Cannot initialize undeclared local binding '" + name + "'"
            );
        }

        if (found->second.initialized) {
            throw TypeError("Binding '" + name + "' is already initialized");
        }

        found->second.value = std::move(value);
        found->second.initialized = true;
    }

    void assign(const std::string& name, Value value) {
        auto found = bindings_.find(name);

        if (found != bindings_.end()) {
            if (!found->second.initialized) {
                throw ReferenceError(
                    "Cannot assign '" + name + "' before initialization"
                );
            }

            if (found->second.kind == BindingKind::Const) {
                throw TypeError(
                    "Assignment to constant binding '" + name + "'"
                );
            }

            found->second.value = std::move(value);
            return;
        }

        if (outer_) {
            outer_->assign(name, std::move(value));
            return;
        }

        throw ReferenceError("'" + name + "' is not defined");
    }

private:
    std::string name_;
    std::shared_ptr<Environment> outer_;
    std::map<std::string, Binding> bindings_;
};

struct ExecutionContext {
    std::string name;
    std::shared_ptr<Environment> lexicalEnvironment;
    std::shared_ptr<Environment> variableEnvironment;
    std::string thisValue;
};

class CallStack {
public:
    explicit CallStack(std::size_t maximumDepth = 32)
        : maximumDepth_(maximumDepth) {
        if (maximumDepth_ == 0) {
            throw std::invalid_argument("Maximum depth must be positive");
        }
    }

    void push(const ExecutionContext& context) {
        if (frames_.size() >= maximumDepth_) {
            throw StackLimitError("Maximum call stack size exceeded");
        }

        frames_.push_back(context);
        std::cout << "PUSH " << context.name
                  << " depth=" << frames_.size() << '\n';
    }

    void pop() {
        if (frames_.empty()) {
            throw std::logic_error("Cannot pop an empty stack");
        }

        std::cout << "POP  " << frames_.back().name
                  << " depth=" << frames_.size() - 1 << '\n';

        frames_.pop_back();
    }

    std::size_t depth() const {
        return frames_.size();
    }

private:
    std::size_t maximumDepth_;
    std::vector<ExecutionContext> frames_;
};

class StackFrameGuard {
public:
    StackFrameGuard(CallStack& stack, const ExecutionContext& context)
        : stack_(stack) {
        stack_.push(context);
    }

    StackFrameGuard(const StackFrameGuard&) = delete;
    StackFrameGuard& operator=(const StackFrameGuard&) = delete;

    ~StackFrameGuard() {
        stack_.pop();
    }

private:
    CallStack& stack_;
};

using FunctionBody =
    std::function<Value(const std::vector<Value>&)>;

struct FunctionObject {
    std::string name;
    std::vector<std::string> parameters;
    std::shared_ptr<Environment> closure;
    FunctionBody body;
};

class Runtime {
public:
    explicit Runtime(std::size_t maximumDepth = 32)
        : stack_(maximumDepth),
          global_(std::make_shared<Environment>("global")) {
        global_->declare(
            "service",
            BindingKind::Const,
            Value("artifact-registry"),
            true
        );
    }

    std::shared_ptr<Environment> global() const {
        return global_;
    }

    Value call(
        const FunctionObject& function,
        const std::vector<Value>& arguments
    ) {
        auto local = std::make_shared<Environment>(
            function.name + ":local",
            function.closure
        );

        for (std::size_t i = 0; i < function.parameters.size(); ++i) {
            Value argument = i < arguments.size()
                ? arguments[i]
                : Value("undefined");

            local->declare(
                function.parameters[i],
                BindingKind::Parameter,
                std::move(argument),
                true
            );
        }

        ExecutionContext context{
            function.name,
            local,
            local,
            "undefined"
        };

        StackFrameGuard guard(stack_, context);

        // The RAII guard pops the frame if the body returns or throws.
        return function.body(arguments);
    }

    std::size_t stackDepth() const {
        return stack_.depth();
    }

private:
    CallStack stack_;
    std::shared_ptr<Environment> global_;
};

void demonstrateHoisting() {
    std::cout << "\n=== Hoisting and initialization ===\n";

    auto functionEnvironment =
        std::make_shared<Environment>("releasePolicy");

    // var and function bindings are initialized during declaration setup.
    functionEnvironment->declare("retryCount", BindingKind::Var);
    functionEnvironment->declare(
        "policyName",
        BindingKind::Function,
        Value("canary-release"),
        true
    );

    std::cout << "var before assignment: "
              << functionEnvironment->get("retryCount").data << '\n';

    std::cout << "function binding: "
              << functionEnvironment->get("policyName").data << '\n';

    functionEnvironment->assign("retryCount", Value("2"));

    std::cout << "var after assignment: "
              << functionEnvironment->get("retryCount").data << '\n';

    functionEnvironment->declare(
        "deploymentRegion",
        BindingKind::Let
    );

    try {
        std::cout << functionEnvironment->get("deploymentRegion").data
                  << '\n';
    } catch (const ReferenceError& error) {
        std::cout << "TDZ failure: " << error.what() << '\n';
    }

    functionEnvironment->initialize(
        "deploymentRegion",
        Value("ap-south-1")
    );

    std::cout << "Initialized let: "
              << functionEnvironment->get("deploymentRegion").data << '\n';
}

void demonstrateLexicalLookup() {
    std::cout << "\n=== Lexical environment chain ===\n";

    auto global = std::make_shared<Environment>("global");
    global->declare(
        "organization",
        BindingKind::Const,
        Value("engineering"),
        true
    );

    auto module = std::make_shared<Environment>("release-module", global);
    module->declare(
        "region",
        BindingKind::Let,
        Value("ap-south-1"),
        true
    );

    auto block = std::make_shared<Environment>("deployment-block", module);
    block->declare(
        "region",
        BindingKind::Const,
        Value("eu-west-1"),
        true
    );

    std::cout << "Block region: " << block->get("region").data << '\n';
    std::cout << "Module region: " << module->get("region").data << '\n';
    std::cout << "Organization: "
              << block->get("organization").data << '\n';

    try {
        block->get("missingApprovalPolicy");
    } catch (const ReferenceError& error) {
        std::cout << "Unresolved identifier: " << error.what() << '\n';
    }
}

void demonstrateNestedExecution() {
    std::cout << "\n=== Nested function execution ===\n";

    Runtime runtime(16);

    FunctionObject verifyArtifact{
        "verifyArtifact",
        {"artifactId"},
        runtime.global(),
        [](const std::vector<Value>& arguments) -> Value {
            if (arguments.empty() ||
                arguments.front().data == "undefined" ||
                arguments.front().data.empty()) {
                throw TypeError("Artifact identifier is required");
            }

            std::cout << "Verifying artifact "
                      << arguments.front().data << '\n';
            return Value("signature-valid");
        }
    };

    FunctionObject publishRelease{
        "publishRelease",
        {"artifactId"},
        runtime.global(),
        [&runtime, verifyArtifact](
            const std::vector<Value>& arguments
        ) -> Value {
            if (arguments.empty()) {
                throw TypeError("Publish requires an artifact identifier");
            }

            Value verification = runtime.call(
                verifyArtifact,
                {arguments.front()}
            );

            std::cout << "Verification result: "
                      << verification.data << '\n';

            return Value("release-published");
        }
    };

    Value result = runtime.call(
        publishRelease,
        {Value("artifact-2026-104")}
    );

    std::cout << "Publish result: " << result.data << '\n';
    std::cout << "Remaining stack depth: "
              << runtime.stackDepth() << '\n';

    try {
        runtime.call(publishRelease, {Value("")});
    } catch (const TypeError& error) {
        std::cout << "Rejected operation: " << error.what() << '\n';
    }

    std::cout << "Stack after error: "
              << runtime.stackDepth() << '\n';
}

void demonstrateClosureLifetime() {
    std::cout << "\n=== Closure lifetime ===\n";

    Runtime runtime;

    // The environment survives because the function object owns a shared
    // reference to it after the factory call has completed.
    auto factoryEnvironment =
        std::make_shared<Environment>("createSequence");

    factoryEnvironment->declare(
        "nextSequence",
        BindingKind::Let,
        Value("40"),
        true
    );

    auto sequence = std::make_shared<FunctionObject>(
        FunctionObject{
            "nextSequenceValue",
            {},
            factoryEnvironment,
            [factoryEnvironment](const std::vector<Value>&) -> Value {
                int current = std::stoi(
                    factoryEnvironment->get("nextSequence").data
                );

                factoryEnvironment->assign(
                    "nextSequence",
                    Value(std::to_string(current + 1))
                );

                return Value(std::to_string(current));
            }
        }
    );

    std::cout << "Sequence A: "
              << runtime.call(*sequence, {}).data << '\n';
    std::cout << "Sequence B: "
              << runtime.call(*sequence, {}).data << '\n';
    std::cout << "Sequence C: "
              << runtime.call(*sequence, {}).data << '\n';
}

int main() {
    try {
        std::cout << "JavaScript execution semantics: C++ case study\n";

        demonstrateHoisting();
        demonstrateLexicalLookup();
        demonstrateNestedExecution();
        demonstrateClosureLifetime();

        std::cout << "\nCase study completed successfully.\n";
    } catch (const std::exception& error) {
        std::cerr << "Fatal execution error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
