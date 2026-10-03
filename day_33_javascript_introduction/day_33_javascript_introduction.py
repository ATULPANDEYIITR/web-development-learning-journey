"""
JavaScript Introduction — companion learning model

This Python program models the execution concepts introduced by JavaScript:
ECMAScript as the language specification, execution environments, source text,
tokens, statements, expressions, values, scope, evaluation, and runtime errors.

The implementation deliberately uses Python as a teaching model rather than
pretending that Python executes JavaScript. It provides:
- a small JavaScript-like lexer
- expression evaluation for a useful subset
- statement execution
- an environment with lexical bindings
- browser and Node-style execution environments
- validation and diagnostics
- a small REPL-like demonstration

The actual JavaScript implementation should be used to execute JavaScript.
This Python program provides an executable conceptual model of the mechanisms.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Callable


# ---------------------------------------------------------------------------
# JavaScript-like source representation
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Token:
    kind: str
    value: str
    position: int


class JavaScriptSyntaxError(Exception):
    """Raised when the small teaching parser cannot understand source code."""


class JavaScriptRuntimeError(Exception):
    """Raised when a modeled JavaScript operation fails at runtime."""


# ---------------------------------------------------------------------------
# Lexer
# ---------------------------------------------------------------------------

class JavaScriptLexer:
    """
    Tokenizes a deliberately small JavaScript subset.

    This demonstrates a fundamental language-processing distinction:
    source code is first represented as lexical tokens before a parser can
    reason about expressions and statements.
    """

    TOKEN_RULES = [
        ("WHITESPACE", r"\s+"),
        ("NUMBER", r"(?:\d+\.\d+|\d+)"),
        ("STRING", r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\''),
        ("IDENTIFIER", r"[A-Za-z_$][A-Za-z0-9_$]*"),
        ("OPERATOR", r"===|!==|==|!=|<=|>=|\+\+|--|&&|\|\||[+\-*/%=<>!]"),
        ("PUNCTUATION", r"[{}();,.]"),
    ]

    KEYWORDS = {
        "const",
        "let",
        "var",
        "if",
        "else",
        "return",
        "true",
        "false",
        "null",
        "undefined",
    }

    def __init__(self) -> None:
        self.pattern = re.compile(
            "|".join(f"(?P<{name}>{pattern})" for name, pattern in self.TOKEN_RULES)
        )

    def tokenize(self, source: str) -> list[Token]:
        tokens: list[Token] = []
        position = 0

        while position < len(source):
            match = self.pattern.match(source, position)

            if match is None:
                raise JavaScriptSyntaxError(
                    f"Unexpected character {source[position]!r} at position {position}"
                )

            kind = match.lastgroup
            value = match.group()

            if kind != "WHITESPACE":
                if kind == "IDENTIFIER" and value in self.KEYWORDS:
                    kind = "KEYWORD"
                tokens.append(Token(kind, value, position))

            position = match.end()

        tokens.append(Token("EOF", "", position))
        return tokens


# ---------------------------------------------------------------------------
# Expressions
# ---------------------------------------------------------------------------

class Environment:
    """
    Models lexical bindings.

    JavaScript distinguishes declarations from ordinary expression values.
    A binding also belongs to an environment, which is why scope matters.
    """

    def __init__(self, parent: Environment | None = None) -> None:
        self.parent = parent
        self.values: dict[str, Any] = {}

    def declare(self, name: str, value: Any, kind: str) -> None:
        if name in self.values:
            if kind == "const":
                raise JavaScriptRuntimeError(
                    f"Identifier '{name}' has already been declared in this scope"
                )
            raise JavaScriptRuntimeError(
                f"Duplicate declaration of '{name}' in modeled scope"
            )

        self.values[name] = value

    def get(self, name: str) -> Any:
        if name in self.values:
            return self.values[name]

        if self.parent is not None:
            return self.parent.get(name)

        raise JavaScriptRuntimeError(f"{name} is not defined")

    def set(self, name: str, value: Any) -> None:
        if name in self.values:
            self.values[name] = value
            return

        if self.parent is not None:
            self.parent.set(name, value)
            return

        raise JavaScriptRuntimeError(f"Cannot assign to undeclared identifier '{name}'")


class ExpressionParser:
    """
    Recursive-descent parser for a small expression subset.

    Operator precedence is represented explicitly rather than evaluating
    expressions from left to right. This mirrors why programming languages
    need grammatical rules for expressions.
    """

    def __init__(self, tokens: list[Token], environment: Environment) -> None:
        self.tokens = tokens
        self.environment = environment
        self.index = 0

    def current(self) -> Token:
        return self.tokens[self.index]

    def advance(self) -> Token:
        token = self.current()
        self.index += 1
        return token

    def match(self, value: str) -> bool:
        if self.current().value == value:
            self.advance()
            return True
        return False

    def parse(self) -> Any:
        value = self.parse_logical_or()

        if self.current().kind != "EOF":
            raise JavaScriptSyntaxError(
                f"Unexpected token {self.current().value!r} at position "
                f"{self.current().position}"
            )

        return value

    def parse_logical_or(self) -> Any:
        left = self.parse_logical_and()

        while self.match("||"):
            right = self.parse_logical_and()
            left = left if self.truthy(left) else right

        return left

    def parse_logical_and(self) -> Any:
        left = self.parse_equality()

        while self.match("&&"):
            right = self.parse_equality()
            left = right if self.truthy(left) else left

        return left

    def parse_equality(self) -> Any:
        left = self.parse_comparison()

        while self.current().value in {"==", "===", "!=", "!=="}:
            operator = self.advance().value
            right = self.parse_comparison()

            if operator in {"===", "=="}:
                left = self.equals(left, right, strict=operator == "===")
            else:
                left = not self.equals(left, right, strict=operator == "!==")

        return left

    def parse_comparison(self) -> Any:
        left = self.parse_term()

        while self.current().value in {"<", "<=", ">", ">="}:
            operator = self.advance().value
            right = self.parse_term()

            try:
                if operator == "<":
                    left = left < right
                elif operator == "<=":
                    left = left <= right
                elif operator == ">":
                    left = left > right
                else:
                    left = left >= right
            except TypeError as exc:
                raise JavaScriptRuntimeError(
                    f"Cannot compare {left!r} and {right!r}"
                ) from exc

        return left

    def parse_term(self) -> Any:
        left = self.parse_factor()

        while self.current().value in {"+", "-"}:
            operator = self.advance().value
            right = self.parse_factor()

            if operator == "+":
                if isinstance(left, str) or isinstance(right, str):
                    left = self.to_string(left) + self.to_string(right)
                else:
                    left = self.to_number(left) + self.to_number(right)
            else:
                left = self.to_number(left) - self.to_number(right)

        return left

    def parse_factor(self) -> Any:
        left = self.parse_unary()

        while self.current().value in {"*", "/", "%"}:
            operator = self.advance().value
            right = self.parse_unary()

            left_number = self.to_number(left)
            right_number = self.to_number(right)

            if operator == "*":
                left = left_number * right_number
            elif operator == "/":
                if right_number == 0:
                    raise JavaScriptRuntimeError("Division by zero")
                left = left_number / right_number
            else:
                if right_number == 0:
                    raise JavaScriptRuntimeError("Modulo by zero")
                left = left_number % right_number

        return left

    def parse_unary(self) -> Any:
        if self.match("!"):
            return not self.truthy(self.parse_unary())

        if self.match("-"):
            return -self.to_number(self.parse_unary())

        if self.match("+"):
            return self.to_number(self.parse_unary())

        return self.parse_primary()

    def parse_primary(self) -> Any:
        token = self.advance()

        if token.kind == "NUMBER":
            return float(token.value) if "." in token.value else int(token.value)

        if token.kind == "STRING":
            return self.decode_string(token.value)

        if token.kind in {"IDENTIFIER", "KEYWORD"}:
            if token.value == "true":
                return True
            if token.value == "false":
                return False
            if token.value == "null":
                return None
            if token.value == "undefined":
                return Undefined
            return self.environment.get(token.value)

        if token.value == "(":
            value = self.parse_logical_or()

            if not self.match(")"):
                raise JavaScriptSyntaxError("Expected ')'")

            return value

        raise JavaScriptSyntaxError(
            f"Unexpected token {token.value!r} at position {token.position}"
        )

    @staticmethod
    def decode_string(value: str) -> str:
        quote = value[0]
        content = value[1:-1]
        content = content.replace("\\" + quote, quote)
        content = content.replace("\\n", "\n").replace("\\t", "\t")
        content = content.replace("\\\\", "\\")
        return content

    @staticmethod
    def truthy(value: Any) -> bool:
        if value is Undefined or value is None or value is False:
            return False

        if value == 0 or value == "":
            return False

        return True

    @staticmethod
    def to_number(value: Any) -> float:
        if value is Undefined:
            raise JavaScriptRuntimeError("Cannot convert undefined to a number")

        if value is None:
            return 0

        if value is True:
            return 1

        if value is False:
            return 0

        if isinstance(value, (int, float)):
            return value

        if isinstance(value, str):
            try:
                return float(value.strip())
            except ValueError as exc:
                raise JavaScriptRuntimeError(
                    f"Cannot convert {value!r} to a number"
                ) from exc

        raise JavaScriptRuntimeError(f"Cannot convert {value!r} to a number")

    @staticmethod
    def to_string(value: Any) -> str:
        if value is Undefined:
            return "undefined"

        if value is None:
            return "null"

        if value is True:
            return "true"

        if value is False:
            return "false"

        return str(value)

    @staticmethod
    def equals(left: Any, right: Any, strict: bool) -> bool:
        if strict:
            if type(left) is not type(right):
                return False
            return left == right

        if left is None and right is Undefined:
            return True

        if left is Undefined and right is None:
            return True

        if type(left) is type(right):
            return left == right

        try:
            return ExpressionParser.to_number(left) == ExpressionParser.to_number(right)
        except JavaScriptRuntimeError:
            return ExpressionParser.to_string(left) == ExpressionParser.to_string(right)


class _Undefined:
    def __repr__(self) -> str:
        return "undefined"


Undefined = _Undefined()


def evaluate_expression(source: str, environment: Environment) -> Any:
    lexer = JavaScriptLexer()
    tokens = lexer.tokenize(source)
    parser = ExpressionParser(tokens, environment)
    return parser.parse()


# ---------------------------------------------------------------------------
# Statement execution
# ---------------------------------------------------------------------------

class JavaScriptModel:
    """
    Executes a practical subset of JavaScript statements.

    Supported statements:
    - const / let / var declarations
    - assignments
    - expression statements
    - console.log(...)
    - if / else
    - return
    - blocks

    The implementation is intentionally limited so that the underlying
    distinction between statements and expressions remains visible.
    """

    def __init__(self) -> None:
        self.global_environment = Environment()
        self.output: list[str] = []
        self.returned = False
        self.return_value: Any = Undefined

        self.global_environment.declare(
            "undefined", Undefined, "var"
        )

    def execute(self, source: str) -> list[str]:
        statements = self.split_statements(source)

        for statement in statements:
            statement = statement.strip()

            if not statement:
                continue

            self.execute_statement(statement)

            if self.returned:
                break

        return self.output

    def execute_statement(self, statement: str) -> None:
        if statement.startswith("{") and statement.endswith("}"):
            inner = statement[1:-1]
            child = JavaScriptModel()
            child.global_environment = Environment(self.global_environment)
            child.execute(inner)
            self.output.extend(child.output)
            return

        if statement.startswith("if"):
            self.execute_if(statement)
            return

        if statement.startswith("return"):
            expression = statement[len("return"):].strip()
            self.return_value = (
                Undefined
                if not expression
                else evaluate_expression(expression, self.global_environment)
            )
            self.returned = True
            return

        declaration = re.match(
            r"^(const|let|var)\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*(?:=\s*(.*))?$",
            statement,
            flags=re.DOTALL,
        )

        if declaration:
            kind, name, expression = declaration.groups()

            if expression is None:
                value = Undefined
            else:
                value = evaluate_expression(expression, self.global_environment)

            self.global_environment.declare(name, value, kind)
            return

        console_match = re.match(
            r"^console\.log\((.*)\)$",
            statement,
            flags=re.DOTALL,
        )

        if console_match:
            expression = console_match.group(1)
            value = evaluate_expression(expression, self.global_environment)
            rendered = ExpressionParser.to_string(value)
            self.output.append(rendered)
            return

        assignment = re.match(
            r"^([A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*(.*)$",
            statement,
            flags=re.DOTALL,
        )

        if assignment:
            name, expression = assignment.groups()
            value = evaluate_expression(expression, self.global_environment)
            self.global_environment.set(name, value)
            return

        evaluate_expression(statement, self.global_environment)

    def execute_if(self, statement: str) -> None:
        match = re.match(
            r"^if\s*\((.*?)\)\s*(.*)$",
            statement,
            flags=re.DOTALL,
        )

        if not match:
            raise JavaScriptSyntaxError("Malformed if statement")

        condition_source, body = match.groups()
        condition = evaluate_expression(
            condition_source,
            self.global_environment,
        )

        true_body, false_body = self.split_if_body(body)

        selected = true_body if ExpressionParser.truthy(condition) else false_body

        if selected:
            self.execute(selected)

    @staticmethod
    def split_if_body(body: str) -> tuple[str, str | None]:
        body = body.strip()

        if not body.startswith("{"):
            raise JavaScriptSyntaxError(
                "This model requires braces around if statement bodies"
            )

        depth = 0
        closing_index = None

        for index, character in enumerate(body):
            if character == "{":
                depth += 1
            elif character == "}":
                depth -= 1
                if depth == 0:
                    closing_index = index
                    break

        if closing_index is None:
            raise JavaScriptSyntaxError("Unclosed if block")

        true_body = body[1:closing_index]
        remaining = body[closing_index + 1:].strip()

        if not remaining:
            return true_body, None

        if not remaining.startswith("else"):
            raise JavaScriptSyntaxError("Unexpected content after if block")

        false_body = remaining[len("else"):].strip()

        if not false_body.startswith("{") or not false_body.endswith("}"):
            raise JavaScriptSyntaxError("This model requires braces around else bodies")

        return true_body, false_body[1:-1]

    @staticmethod
    def split_statements(source: str) -> list[str]:
        statements: list[str] = []
        current: list[str] = []
        depth = 0
        quote: str | None = None
        escaped = False

        for character in source:
            if quote is not None:
                current.append(character)

                if escaped:
                    escaped = False
                elif character == "\\":
                    escaped = True
                elif character == quote:
                    quote = None

                continue

            if character in {"'", '"'}:
                quote = character
                current.append(character)
            elif character == "{":
                depth += 1
                current.append(character)
            elif character == "}":
                depth -= 1
                current.append(character)

                if depth < 0:
                    raise JavaScriptSyntaxError("Unexpected closing brace")
            elif character == ";" and depth == 0:
                statements.append("".join(current))
                current = []
            else:
                current.append(character)

        if quote is not None:
            raise JavaScriptSyntaxError("Unterminated string literal")

        if depth != 0:
            raise JavaScriptSyntaxError("Unbalanced braces")

        if "".join(current).strip():
            statements.append("".join(current))

        return statements


# ---------------------------------------------------------------------------
# Execution environments
# ---------------------------------------------------------------------------

class ExecutionEnvironment:
    """
    Represents environmental capabilities surrounding ECMAScript execution.

    ECMAScript defines language behavior, while hosts provide capabilities.
    A browser and Node.js therefore expose different host APIs even though
    both execute JavaScript.
    """

    def __init__(
        self,
        name: str,
        globals_available: set[str],
        description: str,
    ) -> None:
        self.name = name
        self.globals_available = globals_available
        self.description = description

    def has_global(self, name: str) -> bool:
        return name in self.globals_available

    def describe(self) -> str:
        return (
            f"{self.name}: {self.description}; "
            f"host globals = {', '.join(sorted(self.globals_available))}"
        )


BROWSER_ENVIRONMENT = ExecutionEnvironment(
    name="Browser",
    globals_available={"window", "document", "fetch", "console"},
    description="Provides web APIs and a document-oriented environment",
)

NODE_ENVIRONMENT = ExecutionEnvironment(
    name="Node.js",
    globals_available={"process", "Buffer", "console", "fetch"},
    description="Provides server-side and operating-system-oriented APIs",
)


# ---------------------------------------------------------------------------
# Practical demonstrations
# ---------------------------------------------------------------------------

def demonstrate_lexical_analysis() -> None:
    print("\n=== Source text and lexical tokens ===")

    source = """
        const taxRate = 0.18;
        const price = 1250;
        const total = price * (1 + taxRate);
    """

    lexer = JavaScriptLexer()

    for token in lexer.tokenize(source):
        if token.kind != "EOF":
            print(f"{token.kind:<12} {token.value!r} @ {token.position}")


def demonstrate_expressions() -> None:
    print("\n=== Expressions produce values ===")

    environment = Environment()
    environment.declare("price", 1250, "const")
    environment.declare("quantity", 3, "const")
    environment.declare("taxRate", 0.18, "const")

    expressions = {
        "price * quantity": 3750,
        "price * quantity * (1 + taxRate)": 4425.0,
        "quantity >= 3": True,
        '"Order-" + quantity': "Order-3",
        "quantity === 3": True,
    }

    for source, expected in expressions.items():
        actual = evaluate_expression(source, environment)
        print(f"{source} => {actual!r}")
        assert actual == expected


def demonstrate_statements() -> None:
    print("\n=== Statements perform actions ===")

    program = """
        const price = 1250;
        const quantity = 3;
        const subtotal = price * quantity;
        const tax = subtotal * 0.18;
        const total = subtotal + tax;
        if (total > 4000) {
            console.log("Large order");
        } else {
            console.log("Standard order");
        }
        console.log(total);
    """

    model = JavaScriptModel()
    output = model.execute(program)

    for line in output:
        print(f"console.log -> {line}")


def demonstrate_scope() -> None:
    print("\n=== Lexical environment and scope ===")

    global_scope = Environment()
    global_scope.declare("repository", "learning-lab", "const")

    function_like_scope = Environment(global_scope)
    function_like_scope.declare("branch", "main", "const")

    print("Inner scope can read outer binding:", function_like_scope.get("repository"))
    print("Inner scope has its own binding:", function_like_scope.get("branch"))

    try:
        global_scope.get("branch")
    except JavaScriptRuntimeError as exc:
        print("Outer scope cannot read inner binding:", exc)


def demonstrate_environment_difference() -> None:
    print("\n=== ECMAScript language versus execution environment ===")

    print(BROWSER_ENVIRONMENT.describe())
    print(NODE_ENVIRONMENT.describe())

    print(
        "The same JavaScript language can run in both environments, "
        "while host-provided globals differ."
    )


def demonstrate_validation_and_failures() -> None:
    print("\n=== Syntax and runtime failures ===")

    failures = {
        "const value = ;": JavaScriptSyntaxError,
        "missingName + 10": JavaScriptRuntimeError,
        "10 / 0": JavaScriptRuntimeError,
        '"abc" * 2': None,
    }

    for source, expected_exception in failures.items():
        try:
            environment = Environment()
            value = evaluate_expression(
                source.removeprefix("const value = "),
                environment,
            )
            print(f"{source!r} evaluated as {value!r}")

        except (JavaScriptSyntaxError, JavaScriptRuntimeError) as exc:
            print(f"{source!r} -> {type(exc).__name__}: {exc}")

            if expected_exception is not None:
                assert isinstance(exc, expected_exception)


def demonstrate_runtime_design() -> None:
    print("\n=== A small execution pipeline ===")

    source = """
        const basePrice = 850;
        const quantity = 4;
        const discount = 0.10;
        const subtotal = basePrice * quantity;
        const finalPrice = subtotal * (1 - discount);
        console.log(finalPrice);
    """

    print("Source")
    print(source.strip())

    lexer = JavaScriptLexer()
    tokens = lexer.tokenize(source)

    print(f"Lexical stage: {len(tokens) - 1} non-EOF tokens")

    model = JavaScriptModel()
    output = model.execute(source)

    print("Execution result:", output[0])


def demonstrate_beginner_to_advanced_progression() -> None:
    print("\n=== Progressive JavaScript concepts ===")

    environment = Environment()

    environment.declare("userName", "Atul", "const")
    environment.declare("items", 4, "let")
    environment.declare("unitPrice", 299, "const")

    basic = evaluate_expression("items", environment)
    arithmetic = evaluate_expression("items * unitPrice", environment)
    conditional = evaluate_expression("items >= 3 && unitPrice > 100", environment)
    formatted = evaluate_expression('"User: " + userName', environment)

    print("Identifier lookup:", basic)
    print("Arithmetic expression:", arithmetic)
    print("Logical expression:", conditional)
    print("String expression:", formatted)

    environment.set("items", 5)

    print("After let assignment:", environment.get("items"))

    try:
        environment.set("userName", "Changed")
    except JavaScriptRuntimeError as exc:
        print("const reassignment is rejected by the model:", exc)


def main() -> None:
    print("JavaScript Introduction — executable conceptual model")
    print("ECMAScript, execution environments, syntax, statements, and expressions")

    demonstrate_lexical_analysis()
    demonstrate_expressions()
    demonstrate_statements()
    demonstrate_scope()
    demonstrate_environment_difference()
    demonstrate_validation_and_failures()
    demonstrate_runtime_design()
    demonstrate_beginner_to_advanced_progression()

    print("\n=== Completed ===")
    print(
        "The Python program models a JavaScript-like language pipeline; "
        "the JavaScript deliverable is the executable JavaScript implementation."
    )


if __name__ == "__main__":
    main()
