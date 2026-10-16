#!/usr/bin/env python3
"""
JavaScript Execution: Call Stack, Execution Context, Lexical Environment, and Hoisting

A self-contained Python simulator for studying JavaScript execution semantics.
It models execution contexts, lexical environments, identifier resolution,
function declarations, var/let/const behavior, temporal dead zones, closures,
recursive calls, stack overflow protection, and scope-related errors.

This is an educational model of selected JavaScript semantics, not a complete
JavaScript interpreter. Run with Python 3.10 or later.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Any


class JavaScriptSimulationError(Exception):
    """Base exception for simulated JavaScript execution errors."""


class ReferenceError(JavaScriptSimulationError):
    """Raised for missing identifiers or temporal dead zone access."""


class TypeErrorJS(JavaScriptSimulationError):
    """Raised for invalid assignments or calls."""


class RangeErrorJS(JavaScriptSimulationError):
    """Raised when the simulated call stack exceeds its limit."""


class BindingKind(Enum):
    VAR = "var"
    LET = "let"
    CONST = "const"
    FUNCTION = "function"
    PARAMETER = "parameter"


@dataclass
class Binding:
    name: str
    kind: BindingKind
    value: Any = None
    initialized: bool = False

    @property
    def mutable(self) -> bool:
        return self.kind is not BindingKind.CONST


class LexicalEnvironment:
    """
    A lexical environment stores identifier bindings and links to an outer
    environment. Identifier lookup follows this chain, not the call stack.
    """

    def __init__(
        self,
        name: str,
        outer: LexicalEnvironment | None = None,
    ) -> None:
        self.name = name
        self.outer = outer
        self.bindings: dict[str, Binding] = {}

    def declare(
        self,
        name: str,
        kind: BindingKind,
        value: Any = None,
        initialized: bool | None = None,
    ) -> None:
        if not name.isidentifier():
            raise SyntaxError(f"Invalid simulated identifier: {name}")

        existing = self.bindings.get(name)

        if existing is not None:
            # var and function declarations can coexist with each other
            # in a function or global variable environment.
            compatible = (
                existing.kind in (BindingKind.VAR, BindingKind.FUNCTION)
                and kind in (BindingKind.VAR, BindingKind.FUNCTION)
            )
            if compatible:
                if kind is BindingKind.FUNCTION:
                    existing.kind = BindingKind.FUNCTION
                    existing.value = value
                    existing.initialized = True
                return
            raise SyntaxError(
                f"Identifier '{name}' has already been declared "
                f"in environment '{self.name}'."
            )

        if initialized is None:
            initialized = kind in (
                BindingKind.VAR,
                BindingKind.FUNCTION,
            )

        if kind is BindingKind.CONST and initialized and value is None:
            # None is also a valid JavaScript null-like value in this model.
            # Callers must explicitly provide initialized=True for const null.
            pass

        self.bindings[name] = Binding(
            name=name,
            kind=kind,
            value=value,
            initialized=initialized,
        )

    def resolve(self, name: str) -> Binding:
        environment: LexicalEnvironment | None = self

        while environment is not None:
            if name in environment.bindings:
                return environment.bindings[name]
            environment = environment.outer

        raise ReferenceError(f"{name} is not defined")

    def get(self, name: str) -> Any:
        binding = self.resolve(name)

        if not binding.initialized:
            raise ReferenceError(
                f"Cannot access '{name}' before initialization."
            )

        return binding.value

    def set(self, name: str, value: Any) -> None:
        binding = self.resolve(name)

        if not binding.initialized:
            raise ReferenceError(
                f"Cannot access '{name}' before initialization."
            )

        if not binding.mutable:
            raise TypeErrorJS(
                f"Assignment to constant variable '{name}'."
            )

        binding.value = value

    def initialize(self, name: str, value: Any) -> None:
        binding = self.bindings.get(name)

        if binding is None:
            raise ReferenceError(f"{name} is not declared here.")

        if binding.initialized:
            raise TypeErrorJS(f"Binding '{name}' is already initialized.")

        binding.value = value
        binding.initialized = True


@dataclass
class ExecutionContext:
    """
    Represents a simplified execution context.

    A real JavaScript execution context also tracks specification-defined
    state such as the running function, realm, and script or module state.
    """

    name: str
    lexical_environment: LexicalEnvironment
    variable_environment: LexicalEnvironment
    this_value: Any = None
    strict: bool = True


class CallStack:
    """Track nested function execution and detect excessive recursion."""

    def __init__(self, maximum_depth: int = 100) -> None:
        if maximum_depth < 1:
            raise ValueError("maximum_depth must be positive.")
        self.maximum_depth = maximum_depth
        self.frames: list[ExecutionContext] = []

    def push(self, context: ExecutionContext) -> None:
        if len(self.frames) >= self.maximum_depth:
            raise RangeErrorJS("Maximum simulated call stack size exceeded.")
        self.frames.append(context)
        print(f"  PUSH  {context.name} | depth={len(self.frames)}")

    def pop(self) -> ExecutionContext:
        if not self.frames:
            raise RuntimeError("Cannot pop an empty call stack.")
        context = self.frames.pop()
        print(f"  POP   {context.name} | depth={len(self.frames)}")
        return context

    def __len__(self) -> int:
        return len(self.frames)


@dataclass
class JavaScriptFunction:
    """
    A modeled function with a captured lexical environment.

    Its body receives the newly created execution context and the argument
    list. Capturing the environment models the basis of JavaScript closures.
    """

    name: str
    parameter_names: list[str]
    body: Callable[[ExecutionContext, list[Any]], Any]
    closure: LexicalEnvironment
    stack: CallStack

    def __call__(self, *arguments: Any) -> Any:
        local_environment = LexicalEnvironment(
            f"{self.name}:local",
            outer=self.closure,
        )

        for index, parameter in enumerate(self.parameter_names):
            value = arguments[index] if index < len(arguments) else None
            local_environment.declare(
                parameter,
                BindingKind.PARAMETER,
                value,
                initialized=True,
            )

        context = ExecutionContext(
            name=self.name,
            lexical_environment=local_environment,
            variable_environment=local_environment,
        )

        self.stack.push(context)

        try:
            return self.body(context, list(arguments))
        finally:
            # finally guarantees stack cleanup even when the function fails.
            self.stack.pop()


def demonstrate_stack_and_context() -> None:
    print("\n=== Call stack and execution contexts ===")
    stack = CallStack()

    global_environment = LexicalEnvironment("global")
    global_environment.declare(
        "application",
        BindingKind.CONST,
        "release-service",
        initialized=True,
    )

    global_context = ExecutionContext(
        "global execution",
        global_environment,
        global_environment,
    )

    stack.push(global_context)

    def database_body(
        context: ExecutionContext,
        arguments: list[Any],
    ) -> str:
        print("  Database context reads application:",
              context.lexical_environment.get("application"))
        return "database: connected"

    database = JavaScriptFunction(
        "connectDatabase",
        [],
        database_body,
        global_environment,
        stack,
    )

    def request_body(
        context: ExecutionContext,
        arguments: list[Any],
    ) -> str:
        print("  Request identifier:", context.lexical_environment.get("id"))
        return database()

    request = JavaScriptFunction(
        "handleRequest",
        ["id"],
        request_body,
        global_environment,
        stack,
    )

    try:
        print("  Result:", request("REQ-204"))
    finally:
        stack.pop()

    assert len(stack) == 0


def demonstrate_hoisting() -> None:
    print("\n=== Hoisting and declaration initialization ===")

    environment = LexicalEnvironment("function-body")

    # JavaScript var bindings exist before their assignment executes.
    environment.declare("attempts", BindingKind.VAR)
    environment.declare("sendReport", BindingKind.FUNCTION, "function-body")

    print("var before assignment:", environment.get("attempts"))
    print("function declaration before textual position:",
          environment.get("sendReport"))

    environment.set("attempts", 3)
    print("var after assignment:", environment.get("attempts"))

    # let and const bindings exist in the environment but remain uninitialized.
    environment.declare(
        "deploymentRegion",
        BindingKind.LET,
        initialized=False,
    )

    try:
        environment.get("deploymentRegion")
    except ReferenceError as error:
        print("Temporal dead zone:", error)

    environment.initialize("deploymentRegion", "ap-south-1")
    print("let after initialization:", environment.get("deploymentRegion"))

    environment.declare(
        "productionMode",
        BindingKind.CONST,
        True,
        initialized=True,
    )

    try:
        environment.set("productionMode", False)
    except TypeErrorJS as error:
        print("const reassignment:", error)


def demonstrate_lexical_scope_and_closures() -> None:
    print("\n=== Lexical scope and closures ===")

    stack = CallStack()

    global_environment = LexicalEnvironment("global")
    global_environment.declare(
        "serviceName",
        BindingKind.CONST,
        "payments-api",
        initialized=True,
    )

    def factory_body(
        context: ExecutionContext,
        arguments: list[Any],
    ) -> JavaScriptFunction:
        environment = context.lexical_environment
        environment.declare(
            "sequence",
            BindingKind.LET,
            100,
            initialized=True,
        )

        def next_id_body(
            inner_context: ExecutionContext,
            inner_arguments: list[Any],
        ) -> str:
            current = inner_context.lexical_environment.get("sequence")
            inner_context.lexical_environment.set("sequence", current + 1)
            service = inner_context.lexical_environment.get("serviceName")
            return f"{service}-{current}"

        # The returned function retains access to the factory's environment
        # even after the factory execution context has been removed.
        return JavaScriptFunction(
            "nextRequestId",
            [],
            next_id_body,
            environment,
            stack,
        )

    factory = JavaScriptFunction(
        "createRequestIdGenerator",
        [],
        factory_body,
        global_environment,
        stack,
    )

    generator = factory()
    print(generator())
    print(generator())
    print(generator())


def demonstrate_shadowing() -> None:
    print("\n=== Identifier shadowing ===")

    global_environment = LexicalEnvironment("global")
    global_environment.declare(
        "region",
        BindingKind.CONST,
        "India",
        initialized=True,
    )

    function_environment = LexicalEnvironment(
        "processDeployment",
        outer=global_environment,
    )
    function_environment.declare(
        "region",
        BindingKind.LET,
        "Singapore",
        initialized=True,
    )

    block_environment = LexicalEnvironment(
        "deployment-block",
        outer=function_environment,
    )
    block_environment.declare(
        "region",
        BindingKind.CONST,
        "Frankfurt",
        initialized=True,
    )

    print("Block scope:", block_environment.get("region"))
    print("Function scope:", function_environment.get("region"))
    print("Global scope:", global_environment.get("region"))


def demonstrate_recursive_calls() -> None:
    print("\n=== Recursive call stack ===")
    stack = CallStack(maximum_depth=12)
    environment = LexicalEnvironment("global")

    def factorial_body(
        context: ExecutionContext,
        arguments: list[Any],
    ) -> int:
        value = context.lexical_environment.get("n")

        if not isinstance(value, int) or value < 0:
            raise ValueError("Factorial requires a non-negative integer.")

        if value <= 1:
            return 1

        return value * factorial(value - 1)

    factorial = JavaScriptFunction(
        "factorial",
        ["n"],
        factorial_body,
        environment,
        stack,
    )

    print("factorial(5):", factorial(5))

    try:
        factorial(20)
    except RangeErrorJS as error:
        print("Stack limit:", error)

    assert len(stack) == 0


def demonstrate_error_cleanup() -> None:
    print("\n=== Exception-safe execution context cleanup ===")
    stack = CallStack()
    environment = LexicalEnvironment("global")

    def failing_body(
        context: ExecutionContext,
        arguments: list[Any],
    ) -> None:
        raise RuntimeError("Simulated database timeout")

    operation = JavaScriptFunction(
        "writeAuditRecord",
        [],
        failing_body,
        environment,
        stack,
    )

    try:
        operation()
    except RuntimeError as error:
        print("Operation failed:", error)

    print("Remaining stack frames:", len(stack))
    assert len(stack) == 0


def demonstrate_environment_chain() -> None:
    print("\n=== Lexical lookup and missing identifiers ===")

    global_environment = LexicalEnvironment("global")
    global_environment.declare(
        "retryLimit",
        BindingKind.CONST,
        4,
        initialized=True,
    )

    module_environment = LexicalEnvironment(
        "module",
        outer=global_environment,
    )
    module_environment.declare(
        "retryDelay",
        BindingKind.LET,
        250,
        initialized=True,
    )

    request_environment = LexicalEnvironment(
        "request",
        outer=module_environment,
    )

    print("retryLimit:", request_environment.get("retryLimit"))
    print("retryDelay:", request_environment.get("retryDelay"))

    try:
        request_environment.get("unknownPolicy")
    except ReferenceError as error:
        print("Unresolved identifier:", error)


def main() -> None:
    print("JavaScript Execution Semantics Simulator")
    print("Selected semantics modeled with Python data structures.")

    demonstrate_stack_and_context()
    demonstrate_hoisting()
    demonstrate_lexical_scope_and_closures()
    demonstrate_shadowing()
    demonstrate_recursive_calls()
    demonstrate_error_cleanup()
    demonstrate_environment_chain()

    print("\nAll simulator assertions passed.")
    print(
        "Model boundary: this program illustrates selected execution rules; "
        "it does not parse or execute JavaScript source code."
    )


if __name__ == "__main__":
    main()
