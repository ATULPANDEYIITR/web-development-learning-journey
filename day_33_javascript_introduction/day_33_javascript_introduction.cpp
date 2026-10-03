/*
 * JavaScript Introduction — C++ conceptual case study
 *
 * This C++17 program models a simplified JavaScript source-processing
 * pipeline for a developer tool. It is not a JavaScript engine. Instead,
 * it demonstrates how a host application can distinguish:
 *
 *   source text
 *       -> lexical tokens
 *       -> expressions and statements
 *       -> execution environment
 *       -> evaluated values
 *
 * The case study focuses on JavaScript's introductory language concepts:
 * ECMAScript terminology, syntax, statements, expressions, identifiers,
 * literals, operators, environments, diagnostics, and runtime validation.
 *
 * Compile:
 *   g++ -std=c++17 -Wall -Wextra -pedantic javascript_introduction.cpp -o javascript_introduction
 *
 * Run:
 *   ./javascript_introduction
 */

#include <cctype>
#include <iomanip>
#include <iostream>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <variant>
#include <vector>


// ---------------------------------------------------------------------------
// Runtime value model
// ---------------------------------------------------------------------------

struct Undefined {
    bool operator==(const Undefined&) const = default;
};

using Value = std::variant<
    Undefined,
    std::nullptr_t,
    bool,
    double,
    std::string
>;

std::string valueToString(const Value& value) {
    return std::visit(
        [](const auto& item) -> std::string {
            using T = std::decay_t<decltype(item)>;

            if constexpr (std::is_same_v<T, Undefined>) {
                return "undefined";
            } else if constexpr (std::is_same_v<T, std::nullptr_t>) {
                return "null";
            } else if constexpr (std::is_same_v<T, bool>) {
                return item ? "true" : "false";
            } else if constexpr (std::is_same_v<T, double>) {
                std::ostringstream output;
                output << item;
                return output.str();
            } else {
                return item;
            }
        },
        value
    );
}


// ---------------------------------------------------------------------------
// Lexical token model
// ---------------------------------------------------------------------------

enum class TokenKind {
    Identifier,
    Keyword,
    Number,
    String,
    Operator,
    Punctuation,
    EndOfFile
};

struct Token {
    TokenKind kind;
    std::string text;
    std::size_t position;
};

std::string tokenKindName(TokenKind kind) {
    switch (kind) {
        case TokenKind::Identifier:
            return "Identifier";
        case TokenKind::Keyword:
            return "Keyword";
        case TokenKind::Number:
            return "Number";
        case TokenKind::String:
            return "String";
        case TokenKind::Operator:
            return "Operator";
        case TokenKind::Punctuation:
            return "Punctuation";
        case TokenKind::EndOfFile:
            return "EOF";
    }

    return "Unknown";
}


// ---------------------------------------------------------------------------
// Lexer
// ---------------------------------------------------------------------------

class Lexer {
public:
    std::vector<Token> tokenize(const std::string& source) const {
        std::vector<Token> tokens;

        std::size_t index = 0;

        while (index < source.size()) {
            const char current = source[index];

            if (std::isspace(static_cast<unsigned char>(current))) {
                ++index;
                continue;
            }

            if (isIdentifierStart(current)) {
                const std::size_t start = index;

                while (
                    index < source.size() &&
                    isIdentifierPart(source[index])
                ) {
                    ++index;
                }

                std::string text = source.substr(start, index - start);

                tokens.push_back({
                    isKeyword(text)
                        ? TokenKind::Keyword
                        : TokenKind::Identifier,
                    text,
                    start
                });

                continue;
            }

            if (std::isdigit(static_cast<unsigned char>(current))) {
                const std::size_t start = index;

                while (
                    index < source.size() &&
                    (std::isdigit(static_cast<unsigned char>(source[index])) ||
                     source[index] == '.')
                ) {
                    ++index;
                }

                tokens.push_back({
                    TokenKind::Number,
                    source.substr(start, index - start),
                    start
                });

                continue;
            }

            if (current == '\'' || current == '"') {
                const char quote = current;
                const std::size_t start = index++;
                std::string value;

                bool closed = false;

                while (index < source.size()) {
                    char character = source[index++];

                    if (character == '\\') {
                        if (index >= source.size()) {
                            throw std::runtime_error(
                                "Unterminated escape sequence in string literal"
                            );
                        }

                        const char escaped = source[index++];

                        switch (escaped) {
                            case 'n':
                                value.push_back('\n');
                                break;
                            case 't':
                                value.push_back('\t');
                                break;
                            case '\\':
                                value.push_back('\\');
                                break;
                            default:
                                value.push_back(escaped);
                                break;
                        }
                    } else if (character == quote) {
                        closed = true;
                        break;
                    } else {
                        value.push_back(character);
                    }
                }

                if (!closed) {
                    throw std::runtime_error(
                        "Unterminated JavaScript string literal"
                    );
                }

                tokens.push_back({
                    TokenKind::String,
                    value,
                    start
                });

                continue;
            }

            const std::string threeCharacter =
                source.substr(index, 3);

            const std::string twoCharacter =
                source.substr(index, 2);

            if (
                threeCharacter == "===" ||
                threeCharacter == "!=="
            ) {
                tokens.push_back({
                    TokenKind::Operator,
                    threeCharacter,
                    index
                });

                index += 3;
                continue;
            }

            if (
                twoCharacter == "==" ||
                twoCharacter == "!=" ||
                twoCharacter == "<=" ||
                twoCharacter == ">=" ||
                twoCharacter == "&&" ||
                twoCharacter == "||" ||
                twoCharacter == "++" ||
                twoCharacter == "--"
            ) {
                tokens.push_back({
                    TokenKind::Operator,
                    twoCharacter,
                    index
                });

                index += 2;
                continue;
            }

            if (
                std::string("+-*/%=<>!").find(current) !=
                std::string::npos
            ) {
                tokens.push_back({
                    TokenKind::Operator,
                    std::string(1, current),
                    index
                });

                ++index;
                continue;
            }

            if (
                std::string("{}();,.").find(current) !=
                std::string::npos
            ) {
                tokens.push_back({
                    TokenKind::Punctuation,
                    std::string(1, current),
                    index
                });

                ++index;
                continue;
            }

            throw std::runtime_error(
                "Unexpected source character at position " +
                std::to_string(index)
            );
        }

        tokens.push_back({
            TokenKind::EndOfFile,
            "",
            source.size()
        });

        return tokens;
    }

private:
    static bool isIdentifierStart(char character) {
        return std::isalpha(static_cast<unsigned char>(character)) ||
               character == '_' ||
               character == '$';
    }

    static bool isIdentifierPart(char character) {
        return std::isalnum(static_cast<unsigned char>(character)) ||
               character == '_' ||
               character == '$';
    }

    static bool isKeyword(const std::string& value) {
        return value == "const" ||
               value == "let" ||
               value == "var" ||
               value == "if" ||
               value == "else" ||
               value == "return" ||
               value == "true" ||
               value == "false" ||
               value == "null" ||
               value == "undefined";
    }
};


// ---------------------------------------------------------------------------
// Lexical environment
// ---------------------------------------------------------------------------

class Environment {
public:
    explicit Environment(Environment* parent = nullptr)
        : parent_(parent) {}

    void declare(
        const std::string& name,
        Value value,
        const std::string& declarationKind
    ) {
        if (bindings_.contains(name)) {
            throw std::runtime_error(
                "Duplicate declaration: " + name
            );
        }

        bindings_.emplace(
            name,
            Binding{std::move(value), declarationKind}
        );
    }

    Value get(const std::string& name) const {
        auto iterator = bindings_.find(name);

        if (iterator != bindings_.end()) {
            return iterator->second.value;
        }

        if (parent_ != nullptr) {
            return parent_->get(name);
        }

        throw std::runtime_error(
            "ReferenceError: " + name + " is not defined"
        );
    }

    void assign(const std::string& name, Value value) {
        auto iterator = bindings_.find(name);

        if (iterator != bindings_.end()) {
            if (iterator->second.kind == "const") {
                throw std::runtime_error(
                    "TypeError: Assignment to constant '" +
                    name + "'"
                );
            }

            iterator->second.value = std::move(value);
            return;
        }

        if (parent_ != nullptr) {
            parent_->assign(name, std::move(value));
            return;
        }

        throw std::runtime_error(
            "ReferenceError: Cannot assign to undeclared '" +
            name + "'"
        );
    }

private:
    struct Binding {
        Value value;
        std::string kind;
    };

    std::unordered_map<std::string, Binding> bindings_;
    Environment* parent_;
};


// ---------------------------------------------------------------------------
// Execution environment model
// ---------------------------------------------------------------------------

struct ExecutionEnvironment {
    std::string name;
    std::vector<std::string> hostCapabilities;

    void print() const {
        std::cout << name << " host capabilities:\n";

        for (const auto& capability : hostCapabilities) {
            std::cout << "  " << capability << '\n';
        }
    }
};


// ---------------------------------------------------------------------------
// Expression evaluator for a practical subset
// ---------------------------------------------------------------------------

class ExpressionEvaluator {
public:
    explicit ExpressionEvaluator(
        const std::vector<Token>& tokens,
        Environment& environment
    )
        : tokens_(tokens),
          environment_(environment) {}

    Value evaluate() {
        Value result = parseLogicalOr();

        if (current().kind != TokenKind::EndOfFile) {
            throw std::runtime_error(
                "Unexpected token '" + current().text + "'"
            );
        }

        return result;
    }

private:
    const std::vector<Token>& tokens_;
    Environment& environment_;
    std::size_t index_ = 0;

    const Token& current() const {
        return tokens_[index_];
    }

    const Token& advance() {
        return tokens_[index_++];
    }

    bool match(const std::string& text) {
        if (current().text == text) {
            ++index_;
            return true;
        }

        return false;
    }

    Value parseLogicalOr() {
        Value left = parseLogicalAnd();

        while (match("||")) {
            Value right = parseLogicalAnd();

            if (truthy(left)) {
                left = left;
            } else {
                left = right;
            }
        }

        return left;
    }

    Value parseLogicalAnd() {
        Value left = parseEquality();

        while (match("&&")) {
            Value right = parseEquality();

            if (truthy(left)) {
                left = right;
            } else {
                left = left;
            }
        }

        return left;
    }

    Value parseEquality() {
        Value left = parseComparison();

        while (
            current().text == "===" ||
            current().text == "!==" ||
            current().text == "==" ||
            current().text == "!="
        ) {
            const std::string operation = advance().text;
            Value right = parseComparison();

            const bool equal =
                operation == "===" || operation == "=="
                    ? looselyEqual(left, right, operation == "===")
                    : !looselyEqual(left, right, operation == "!==");

            left = equal;
        }

        return left;
    }

    Value parseComparison() {
        Value left = parseTerm();

        while (
            current().text == "<" ||
            current().text == "<=" ||
            current().text == ">" ||
            current().text == ">="
        ) {
            const std::string operation = advance().text;
            const double right = toNumber(parseTerm());
            const double leftNumber = toNumber(left);

            if (operation == "<") {
                left = leftNumber < right;
            } else if (operation == "<=") {
                left = leftNumber <= right;
            } else if (operation == ">") {
                left = leftNumber > right;
            } else {
                left = leftNumber >= right;
            }
        }

        return left;
    }

    Value parseTerm() {
        Value left = parseFactor();

        while (
            current().text == "+" ||
            current().text == "-"
        ) {
            const std::string operation = advance().text;
            Value right = parseFactor();

            if (operation == "+") {
                if (
                    std::holds_alternative<std::string>(left) ||
                    std::holds_alternative<std::string>(right)
                ) {
                    left =
                        toString(left) +
                        toString(right);
                } else {
                    left =
                        toNumber(left) +
                        toNumber(right);
                }
            } else {
                left =
                    toNumber(left) -
                    toNumber(right);
            }
        }

        return left;
    }

    Value parseFactor() {
        Value left = parseUnary();

        while (
            current().text == "*" ||
            current().text == "/" ||
            current().text == "%"
        ) {
            const std::string operation = advance().text;
            const double right = toNumber(parseUnary());
            const double leftNumber = toNumber(left);

            if (operation == "*") {
                left = leftNumber * right;
            } else if (operation == "/") {
                if (right == 0.0) {
                    throw std::runtime_error(
                        "RangeError: division by zero"
                    );
                }

                left = leftNumber / right;
            } else {
                if (right == 0.0) {
                    throw std::runtime_error(
                        "RangeError: modulo by zero"
                    );
                }

                left = std::fmod(leftNumber, right);
            }
        }

        return left;
    }

    Value parseUnary() {
        if (match("!")) {
            return !truthy(parseUnary());
        }

        if (match("-")) {
            return -toNumber(parseUnary());
        }

        if (match("+")) {
            return toNumber(parseUnary());
        }

        return parsePrimary();
    }

    Value parsePrimary() {
        const Token token = advance();

        if (token.kind == TokenKind::Number) {
            return std::stod(token.text);
        }

        if (token.kind == TokenKind::String) {
            return token.text;
        }

        if (
            token.kind == TokenKind::Identifier ||
            token.kind == TokenKind::Keyword
        ) {
            if (token.text == "true") {
                return true;
            }

            if (token.text == "false") {
                return false;
            }

            if (token.text == "null") {
                return nullptr;
            }

            if (token.text == "undefined") {
                return Undefined{};
            }

            return environment_.get(token.text);
        }

        if (token.text == "(") {
            Value result = parseLogicalOr();

            if (!match(")")) {
                throw std::runtime_error(
                    "SyntaxError: expected ')'"
                );
            }

            return result;
        }

        throw std::runtime_error(
            "SyntaxError: unexpected token '" +
            token.text + "'"
        );
    }

    static bool truthy(const Value& value) {
        return std::visit(
            [](const auto& item) -> bool {
                using T = std::decay_t<decltype(item)>;

                if constexpr (std::is_same_v<T, Undefined>) {
                    return false;
                } else if constexpr (std::is_same_v<T, std::nullptr_t>) {
                    return false;
                } else if constexpr (std::is_same_v<T, bool>) {
                    return item;
                } else if constexpr (std::is_same_v<T, double>) {
                    return item != 0.0;
                } else {
                    return !item.empty();
                }
            },
            value
        );
    }

    static double toNumber(const Value& value) {
        return std::visit(
            [](const auto& item) -> double {
                using T = std::decay_t<decltype(item)>;

                if constexpr (std::is_same_v<T, Undefined>) {
                    throw std::runtime_error(
                        "TypeError: undefined cannot be converted to a number"
                    );
                } else if constexpr (std::is_same_v<T, std::nullptr_t>) {
                    return 0.0;
                } else if constexpr (std::is_same_v<T, bool>) {
                    return item ? 1.0 : 0.0;
                } else if constexpr (std::is_same_v<T, double>) {
                    return item;
                } else {
                    try {
                        std::size_t consumed = 0;
                        double result = std::stod(item, &consumed);

                        if (consumed != item.size()) {
                            throw std::runtime_error(
                                "invalid numeric conversion"
                            );
                        }

                        return result;
                    } catch (...) {
                        throw std::runtime_error(
                            "TypeError: invalid numeric conversion"
                        );
                    }
                }
            },
            value
        );
    }

    static std::string toString(const Value& value) {
        return valueToString(value);
    }

    static bool looselyEqual(
        const Value& left,
        const Value& right,
        bool strict
    ) {
        if (strict && left.index() != right.index()) {
            return false;
        }

        if (left.index() == right.index()) {
            return left == right;
        }

        try {
            return toNumber(left) == toNumber(right);
        } catch (...) {
            return toString(left) == toString(right);
        }
    }
};


// ---------------------------------------------------------------------------
// Case-study application
// ---------------------------------------------------------------------------

class JavaScriptLearningAnalyzer {
public:
    void run() {
        printTitle();
        demonstrateSourcePipeline();
        demonstrateEnvironment();
        demonstrateScopeAndBindings();
        demonstrateExpressionEvaluation();
        demonstrateFailureHandling();
        demonstrateDesignTradeoffs();
    }

private:
    static void printTitle() {
        std::cout
            << "JavaScript Introduction: Developer Tool Case Study\n"
            << "====================================================\n";
    }

    static void demonstrateSourcePipeline() {
        std::cout << "\nSource pipeline\n";
        std::cout << "---------------\n";

        const std::string source =
            "const quantity = 4; "
            "const price = 299; "
            "const total = quantity * price;";

        Lexer lexer;
        const auto tokens = lexer.tokenize(source);

        std::cout << "Source: " << source << "\n";
        std::cout << "Tokens:\n";

        for (const auto& token : tokens) {
            std::cout
                << std::setw(14)
                << tokenKindName(token.kind)
                << "  "
                << std::quoted(token.text)
                << "  position="
                << token.position
                << '\n';
        }

        std::cout
            << "\nThe lexer separates lexical structure from later "
            << "parsing and evaluation.\n";
    }

    static void demonstrateEnvironment() {
        std::cout << "\nExecution environments\n";
        std::cout << "----------------------\n";

        const ExecutionEnvironment browser{
            "Browser",
            {
                "window",
                "document",
                "fetch",
                "DOM events"
            }
        };

        const ExecutionEnvironment node{
            "Node.js",
            {
                "process",
                "filesystem APIs",
                "networking APIs",
                "fetch"
            }
        };

        browser.print();
        std::cout << '\n';
        node.print();

        std::cout
            << "\nThe ECMAScript language rules are distinct from "
            << "the host APIs supplied by the execution environment.\n";
    }

    static void demonstrateScopeAndBindings() {
        std::cout << "\nBindings and lexical scope\n";
        std::cout << "-------------------------\n";

        Environment global;

        global.declare(
            "application",
            std::string("Repository Explorer"),
            "const"
        );

        global.declare(
            "requestCount",
            0.0,
            "let"
        );

        Environment functionScope(&global);

        functionScope.declare(
            "operation",
            std::string("load"),
            "const"
        );

        std::cout
            << "Inner scope reads outer binding: "
            << valueToString(functionScope.get("application"))
            << '\n';

        std::cout
            << "Inner scope owns local binding: "
            << valueToString(functionScope.get("operation"))
            << '\n';

        try {
            global.get("operation");
        } catch (const std::exception& error) {
            std::cout
                << "Outer scope lookup failure: "
                << error.what()
                << '\n';
        }

        /*
         * The parent pointer models lexical lookup. A nested environment can
         * search outward, but an outer environment cannot search inward.
         */
    }

    static void demonstrateExpressionEvaluation() {
        std::cout << "\nExpression evaluation\n";
        std::cout << "---------------------\n";

        Environment environment;

        environment.declare(
            "price",
            1250.0,
            "const"
        );

        environment.declare(
            "quantity",
            3.0,
            "const"
        );

        environment.declare(
            "taxRate",
            0.18,
            "const"
        );

        evaluateAndPrint(
            "price * quantity",
            environment
        );

        evaluateAndPrint(
            "price * quantity * (1 + taxRate)",
            environment
        );

        evaluateAndPrint(
            "quantity >= 3 && price > 1000",
            environment
        );

        evaluateAndPrint(
            "\"Order\" + quantity",
            environment
        );
    }

    static void evaluateAndPrint(
        const std::string& expression,
        Environment& environment
    ) {
        Lexer lexer;
        auto tokens = lexer.tokenize(expression);

        ExpressionEvaluator evaluator(tokens, environment);
        Value result = evaluator.evaluate();

        std::cout
            << expression
            << " => "
            << valueToString(result)
            << '\n';
    }

    static void demonstrateFailureHandling() {
        std::cout << "\nFailure handling\n";
        std::cout << "----------------\n";

        Environment environment;

        environment.declare(
            "price",
            500.0,
            "const"
        );

        const std::vector<std::string> failingExpressions{
            "unknownValue + 10",
            "price / 0"
        };

        for (const auto& expression : failingExpressions) {
            try {
                Lexer lexer;
                auto tokens = lexer.tokenize(expression);

                ExpressionEvaluator evaluator(
                    tokens,
                    environment
                );

                const Value result = evaluator.evaluate();

                std::cout
                    << expression
                    << " unexpectedly produced "
                    << valueToString(result)
                    << '\n';
            } catch (const std::exception& error) {
                std::cout
                    << expression
                    << " -> "
                    << error.what()
                    << '\n';
            }
        }

        try {
            environment.assign(
                "price",
                750.0
            );

            /*
             * A real JavaScript const binding cannot be reassigned. The
             * environment implementation intentionally preserves that rule.
             */
        } catch (const std::exception& error) {
            std::cout
                << "const assignment failure: "
                << error.what()
                << '\n';
        }
    }

    static void demonstrateDesignTradeoffs() {
        std::cout << "\nDesign considerations\n";
        std::cout << "---------------------\n";

        std::cout
            << "Lexing isolates source-character handling from evaluation.\n"
            << "Environments isolate bindings from expression parsing.\n"
            << "The Value variant makes runtime value categories explicit.\n"
            << "Exceptions represent syntax and runtime failures at the "
            << "case-study boundary.\n"
            << "A production JavaScript engine requires a substantially "
            << "richer parser, runtime, object model, garbage collector, "
            << "module system, and host integration layer.\n";

        std::cout
            << "\nComplexity note: lexical scanning is approximately O(n) "
            << "for source length n in this simplified implementation. "
            << "Hash-based environment lookup is average-case O(1), "
            << "with lexical parent traversal adding a factor based on "
            << "scope depth.\n";
    }
};


int main() {
    try {
        JavaScriptLearningAnalyzer analyzer;
        analyzer.run();

        std::cout
            << "\nCase study completed successfully.\n";

        return 0;
    } catch (const std::exception& error) {
        std::cerr
            << "Fatal error: "
            << error.what()
            << '\n';

        return 1;
    }
}
