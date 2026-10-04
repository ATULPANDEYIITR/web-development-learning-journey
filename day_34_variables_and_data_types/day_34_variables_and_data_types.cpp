#include <algorithm>
#include <cstdint>
#include <exception>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <optional>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <type_traits>
#include <unordered_map>
#include <utility>
#include <variant>
#include <vector>

/*
 * C++17 case study: repository configuration and event validation.
 *
 * The scenario models a repository service receiving configuration and
 * repository-event records containing values analogous to JavaScript's:
 *
 *   strings, numbers, booleans, null, undefined, symbols, and BigInt
 *
 * C++ has different type semantics from JavaScript. Instead of pretending that
 * C++ has JavaScript's var/let/const declarations, this program uses C++'s
 * const, mutable objects, scoped variables, std::optional, std::variant,
 * strongly typed integers, and RAII to model the underlying engineering
 * concerns.
 *
 * The system validates a repository event before accepting it into an
 * in-memory event store. It demonstrates:
 *
 *   - explicit type representation
 *   - intentional absence versus missing values
 *   - exact large-integer sequence numbers
 *   - symbolic identifiers
 *   - numeric validation
 *   - immutable configuration boundaries
 *   - duplicate-event detection
 *   - exception-safe processing
 *   - complexity and data-structure trade-offs
 *
 * Compile:
 *   g++ -std=c++17 -Wall -Wextra -pedantic repository_data_types.cpp -o repository_data_types
 */

namespace repository {

class ValidationError : public std::runtime_error {
public:
    explicit ValidationError(const std::string& message)
        : std::runtime_error(message) {}
};

/*
 * JavaScript's undefined is distinct from null. std::monostate represents an
 * explicitly missing field in a variant. std::nullopt represents an optional
 * field whose value is intentionally absent.
 */
struct Undefined {
    friend bool operator==(Undefined, Undefined) {
        return true;
    }
};

struct Null {
    friend bool operator==(Null, Null) {
        return true;
    }
};

/*
 * A Symbol-like value receives a unique process-local identifier. The
 * description is informational; identity, not description, determines
 * equality.
 */
class Symbol {
public:
    explicit Symbol(std::string description = {})
        : id_(nextId_++), description_(std::move(description)) {}

    std::uint64_t id() const noexcept {
        return id_;
    }

    const std::string& description() const noexcept {
        return description_;
    }

    friend bool operator==(const Symbol& lhs, const Symbol& rhs) {
        return lhs.id_ == rhs.id_;
    }

    friend bool operator<(const Symbol& lhs, const Symbol& rhs) {
        return lhs.id_ < rhs.id_;
    }

private:
    inline static std::uint64_t nextId_ = 1;
    std::uint64_t id_;
    std::string description_;
};

/*
 * C++17 has no built-in BigInt. This small decimal representation stores a
 * non-negative arbitrary-length integer as base-1e9 chunks.
 *
 * It is deliberately sufficient for repository event sequence numbers rather
 * than pretending to be a complete arbitrary-precision arithmetic library.
 */
class BigInt {
public:
    BigInt() : digits_{0} {}

    explicit BigInt(std::uint64_t value) {
        if (value == 0) {
            digits_.push_back(0);
            return;
        }

        while (value > 0) {
            digits_.push_back(static_cast<std::uint32_t>(value % BASE));
            value /= BASE;
        }
    }

    explicit BigInt(const std::string& decimal) {
        parse(decimal);
    }

    std::string toString() const {
        std::ostringstream output;
        output << digits_.back();

        for (std::size_t i = digits_.size() - 1; i > 0; --i) {
            output << std::setw(9)
                   << std::setfill('0')
                   << digits_[i - 1];
        }

        return output.str();
    }

    BigInt operator+(const BigInt& other) const {
        BigInt result;
        result.digits_.clear();

        const std::size_t count =
            std::max(digits_.size(), other.digits_.size());

        std::uint64_t carry = 0;

        for (std::size_t i = 0; i < count || carry != 0; ++i) {
            std::uint64_t sum = carry;

            if (i < digits_.size()) {
                sum += digits_[i];
            }

            if (i < other.digits_.size()) {
                sum += other.digits_[i];
            }

            result.digits_.push_back(
                static_cast<std::uint32_t>(sum % BASE)
            );

            carry = sum / BASE;
        }

        result.normalize();
        return result;
    }

    friend bool operator==(const BigInt& lhs, const BigInt& rhs) {
        return lhs.digits_ == rhs.digits_;
    }

    friend bool operator<(const BigInt& lhs, const BigInt& rhs) {
        if (lhs.digits_.size() != rhs.digits_.size()) {
            return lhs.digits_.size() < rhs.digits_.size();
        }

        for (std::size_t i = lhs.digits_.size(); i > 0; --i) {
            if (lhs.digits_[i - 1] != rhs.digits_[i - 1]) {
                return lhs.digits_[i - 1] < rhs.digits_[i - 1];
            }
        }

        return false;
    }

private:
    static constexpr std::uint32_t BASE = 1'000'000'000;
    std::vector<std::uint32_t> digits_;

    void parse(const std::string& decimal) {
        if (decimal.empty()) {
            throw ValidationError("BigInt cannot be constructed from an empty string");
        }

        if (decimal.front() == '-') {
            throw ValidationError("This case study accepts non-negative BigInt values only");
        }

        if (!std::all_of(
                decimal.begin(),
                decimal.end(),
                [](unsigned char character) {
                    return character >= '0' && character <= '9';
                })) {
            throw ValidationError("BigInt contains a non-decimal character");
        }

        digits_.clear();

        for (std::size_t end = decimal.size(); end > 0;) {
            const std::size_t start =
                end >= 9 ? end - 9 : 0;

            const std::string chunk =
                decimal.substr(start, end - start);

            digits_.push_back(
                static_cast<std::uint32_t>(std::stoul(chunk))
            );

            end = start;
        }

        normalize();
    }

    void normalize() {
        while (digits_.size() > 1 && digits_.back() == 0) {
            digits_.pop_back();
        }
    }
};

/*
 * A JavaScript-like value variant. The alternatives make the data type
 * explicit at compile time rather than relying on unchecked void pointers or
 * stringly typed records.
 */
using Value = std::variant<
    Undefined,
    Null,
    std::string,
    double,
    bool,
    Symbol,
    BigInt
>;

std::string typeName(const Value& value) {
    return std::visit(
        [](const auto& item) -> std::string {
            using T = std::decay_t<decltype(item)>;

            if constexpr (std::is_same_v<T, Undefined>) {
                return "undefined";
            } else if constexpr (std::is_same_v<T, Null>) {
                return "null";
            } else if constexpr (std::is_same_v<T, std::string>) {
                return "string";
            } else if constexpr (std::is_same_v<T, double>) {
                return "number";
            } else if constexpr (std::is_same_v<T, bool>) {
                return "boolean";
            } else if constexpr (std::is_same_v<T, Symbol>) {
                return "symbol";
            } else if constexpr (std::is_same_v<T, BigInt>) {
                return "bigint";
            } else {
                return "unknown";
            }
        },
        value
    );
}

std::string valueDescription(const Value& value) {
    return std::visit(
        [](const auto& item) -> std::string {
            using T = std::decay_t<decltype(item)>;

            if constexpr (std::is_same_v<T, Undefined>) {
                return "undefined";
            } else if constexpr (std::is_same_v<T, Null>) {
                return "null";
            } else if constexpr (std::is_same_v<T, std::string>) {
                return '"' + item + '"';
            } else if constexpr (std::is_same_v<T, double>) {
                std::ostringstream output;
                output << item;
                return output.str();
            } else if constexpr (std::is_same_v<T, bool>) {
                return item ? "true" : "false";
            } else if constexpr (std::is_same_v<T, Symbol>) {
                return "Symbol(" + item.description() +
                       ", id=" + std::to_string(item.id()) + ")";
            } else if constexpr (std::is_same_v<T, BigInt>) {
                return item.toString() + "n";
            } else {
                return "<unknown>";
            }
        },
        value
    );
}

struct RepositoryConfiguration {
    /*
     * const members communicate that configuration is immutable after
     * construction. This is a C++ design choice rather than a JavaScript
     * const binding, but it enforces a similar "do not rebind configuration"
     * invariant.
     */
    const std::string repository;
    const bool enabled;
    const std::uint32_t maxRetries;
    const double timeoutSeconds;
    const std::optional<std::string> description;
    const Symbol auditToken;
};

void validateConfiguration(const RepositoryConfiguration& configuration) {
    if (configuration.repository.empty()) {
        throw ValidationError("repository cannot be empty");
    }

    if (configuration.repository.size() > 100) {
        throw ValidationError("repository name exceeds 100 characters");
    }

    if (configuration.maxRetries > 10) {
        throw ValidationError("maxRetries must be at most 10");
    }

    if (!std::isfinite(configuration.timeoutSeconds) ||
        configuration.timeoutSeconds <= 0.0 ||
        configuration.timeoutSeconds > 300.0) {
        throw ValidationError(
            "timeoutSeconds must be finite, positive, and at most 300"
        );
    }

    if (configuration.description.has_value() &&
        configuration.description->empty()) {
        throw ValidationError(
            "description must be absent or contain meaningful text"
        );
    }
}

struct RepositoryEvent {
    std::string repository;
    BigInt sequence;
    bool approved;
    std::optional<std::string> description;
    Symbol eventToken;
};

class EventStore {
public:
    void append(const RepositoryEvent& event) {
        if (knownSequences_.find(event.sequence.toString()) !=
            knownSequences_.end()) {
            throw ValidationError(
                "duplicate repository event sequence: " +
                event.sequence.toString()
            );
        }

        events_.push_back(event);
        knownSequences_.insert(event.sequence.toString());
    }

    std::size_t size() const noexcept {
        return events_.size();
    }

    const RepositoryEvent& at(std::size_t index) const {
        if (index >= events_.size()) {
            throw std::out_of_range("event index outside EventStore");
        }

        return events_[index];
    }

private:
    std::vector<RepositoryEvent> events_;

    /*
     * Sequence strings are used as hash keys because the BigInt class is
     * intentionally minimal. Average duplicate detection is O(1) with
     * unordered_set-like hashing; the string conversion costs O(d), where d
     * is the number of decimal digits.
     */
    std::set<std::string> knownSequences_;
};

class RepositoryService {
public:
    explicit RepositoryService(RepositoryConfiguration configuration)
        : configuration_(std::move(configuration)) {
        validateConfiguration(configuration_);
    }

    void process(const RepositoryEvent& event) {
        validateEvent(event);

        /*
         * The event is appended only after all validation succeeds. This gives
         * the operation a simple atomicity boundary: invalid input cannot
         * partially modify the EventStore.
         */
        store_.append(event);
    }

    std::size_t acceptedEvents() const noexcept {
        return store_.size();
    }

private:
    RepositoryConfiguration configuration_;
    EventStore store_;

    void validateEvent(const RepositoryEvent& event) const {
        if (event.repository != configuration_.repository) {
            throw ValidationError(
                "event repository does not match configured repository"
            );
        }

        if (event.repository.empty()) {
            throw ValidationError("event repository cannot be empty");
        }

        /*
         * This business rule intentionally distinguishes the boolean
         * approval field from a string such as "true". Strong C++ typing makes
         * accidental string input impossible at the call site.
         */
        if (!event.approved) {
            throw ValidationError(
                "repository event requires an approved=true state"
            );
        }

        if (event.description.has_value() &&
            event.description->size() > 500) {
            throw ValidationError(
                "event description exceeds 500 characters"
            );
        }
    }
};

void demonstrateVariablesAndTypes() {
    std::cout << "\n=== C++ representation of JavaScript-like data types ===\n";

    /*
     * C++ has lexical block scope for ordinary local variables. const makes a
     * binding non-assignable after initialization.
     */
    int mutableValue = 10;
    mutableValue = 11;

    const std::string repository = "variables-and-data-types";

    std::cout << "mutableValue: " << mutableValue << '\n';
    std::cout << "const repository: " << repository << '\n';

    {
        int blockValue = 25;
        std::cout << "block-scoped local: " << blockValue << '\n';
    }

    /*
     * std::optional models a value that may intentionally be absent. This is
     * different from a JavaScript undefined value, but it provides a safer
     * typed representation of optional data in C++.
     */
    std::optional<std::string> description = std::nullopt;

    if (!description.has_value()) {
        std::cout << "description is intentionally absent\n";
    }

    description = "A typed repository configuration";
    std::cout << "description: " << *description << '\n';
}

void demonstrateNumericBoundaries() {
    std::cout << "\n=== Number and BigInt boundaries ===\n";

    const double decimal = 0.1 + 0.2;

    std::cout << std::setprecision(17);
    std::cout << "double 0.1 + 0.2: " << decimal << '\n';

    const std::uint64_t safeUnsignedLimit =
        std::numeric_limits<std::uint64_t>::max();

    std::cout << "uint64_t maximum: "
              << safeUnsignedLimit
              << '\n';

    /*
     * JavaScript Number loses integer precision beyond 2^53 - 1. C++ can use
     * wider integer types for many practical cases, but uint64_t still has a
     * finite limit. BigInt removes that fixed-width constraint in this case
     * study.
     */
    const BigInt hugeSequence("900719925474099312345");
    const BigInt additional("125000000000000000");
    const BigInt updated = hugeSequence + additional;

    std::cout << "BigInt sequence: "
              << hugeSequence.toString()
              << '\n';

    std::cout << "BigInt after addition: "
              << updated.toString()
              << '\n';
}

void demonstrateSymbols() {
    std::cout << "\n=== Symbol identity ===\n";

    const Symbol first("repositoryId");
    const Symbol second("repositoryId");

    std::cout << "first id: " << first.id() << '\n';
    std::cout << "second id: " << second.id() << '\n';
    std::cout << "same description: "
              << std::boolalpha
              << (first.description() == second.description())
              << '\n';
    std::cout << "same identity: "
              << (first == second)
              << '\n';

    /*
     * The map uses Symbol's identity ordering. Two symbols with identical
     * descriptions remain distinct keys.
     */
    std::map<Symbol, std::string> metadata;
    metadata.emplace(first, "first internal metadata");
    metadata.emplace(second, "second internal metadata");

    std::cout << "symbol-keyed metadata entries: "
              << metadata.size()
              << '\n';
}

void demonstrateVariantTypes() {
    std::cout << "\n=== Explicit runtime value representation ===\n";

    const Symbol symbol("audit");
    const std::vector<Value> values = {
        Undefined{},
        Null{},
        std::string("feature/data-types"),
        15.5,
        true,
        symbol,
        BigInt("9007199254740993")
    };

    for (const Value& value : values) {
        std::cout
            << "type=" << std::setw(10)
            << typeName(value)
            << " value=" << valueDescription(value)
            << '\n';
    }
}

RepositoryEvent createValidEvent(
    std::string repositoryName,
    const std::string& sequence,
    bool approved,
    std::optional<std::string> description
) {
    return RepositoryEvent{
        std::move(repositoryName),
        BigInt(sequence),
        approved,
        std::move(description),
        Symbol("event")
    };
}

void demonstrateRepositoryCaseStudy() {
    std::cout << "\n=== Repository configuration and event case study ===\n";

    RepositoryConfiguration configuration{
        "variables-and-data-types",
        true,
        3,
        15.5,
        std::string("Configuration for typed repository events"),
        Symbol("configuration-audit")
    };

    RepositoryService service(configuration);

    const RepositoryEvent accepted = createValidEvent(
        "variables-and-data-types",
        "900719925474099312345",
        true,
        std::string("First accepted repository event")
    );

    service.process(accepted);

    std::cout << "Accepted events: "
              << service.acceptedEvents()
              << '\n';

    /*
     * The service rejects a false boolean rather than treating a textual value
     * such as "false" as a truthy value. C++'s bool type makes this contract
     * explicit at the API boundary.
     */
    const RepositoryEvent rejectedApproval = createValidEvent(
        "variables-and-data-types",
        "900719925474099312346",
        false,
        std::nullopt
    );

    try {
        service.process(rejectedApproval);
    } catch (const ValidationError& error) {
        std::cout << "Rejected event: "
                  << error.what()
                  << '\n';
    }

    /*
     * A duplicate sequence demonstrates an idempotency guard. The store checks
     * the sequence before insertion, so retrying an already accepted event
     * cannot silently create a duplicate record.
     */
    try {
        service.process(accepted);
    } catch (const ValidationError& error) {
        std::cout << "Duplicate event rejected: "
                  << error.what()
                  << '\n';
    }

    const RepositoryEvent wrongRepository = createValidEvent(
        "another-repository",
        "900719925474099312347",
        true,
        std::nullopt
    );

    try {
        service.process(wrongRepository);
    } catch (const ValidationError& error) {
        std::cout << "Cross-repository event rejected: "
                  << error.what()
                  << '\n';
    }

    std::cout << "Final accepted event count: "
              << service.acceptedEvents()
              << '\n';
}

void demonstrateFailureModes() {
    std::cout << "\n=== Failure modes ===\n";

    try {
        RepositoryConfiguration invalid{
            "",
            true,
            3,
            15.5,
            std::nullopt,
            Symbol("invalid")
        };

        RepositoryService service(invalid);
        (void)service;
    } catch (const ValidationError& error) {
        std::cout << "Invalid configuration rejected: "
                  << error.what()
                  << '\n';
    }

    try {
        RepositoryConfiguration invalidTimeout{
            "variables-and-data-types",
            true,
            3,
            std::numeric_limits<double>::infinity(),
            std::nullopt,
            Symbol("invalid-timeout")
        };

        RepositoryService service(invalidTimeout);
        (void)service;
    } catch (const ValidationError& error) {
        std::cout << "Invalid numeric configuration rejected: "
                  << error.what()
                  << '\n';
    }

    try {
        BigInt invalidBigInt("12x34");
        (void)invalidBigInt;
    } catch (const ValidationError& error) {
        std::cout << "Invalid BigInt rejected: "
                  << error.what()
                  << '\n';
    }
}

void runSelfChecks() {
    std::cout << "\n=== Self checks ===\n";

    BigInt first("900719925474099312345");
    BigInt second("125000000000000000");
    BigInt sum = first + second;

    if (sum.toString() != "900844925474099312345") {
        throw std::runtime_error("BigInt addition check failed");
    }

    const Symbol a("same-description");
    const Symbol b("same-description");

    if (a == b) {
        throw std::runtime_error("Symbol identity check failed");
    }

    const std::vector<Value> values = {
        Undefined{},
        Null{},
        std::string("text"),
        12.5,
        true,
        Symbol("symbol"),
        BigInt("12345678901234567890")
    };

    const std::vector<std::string> expectedTypes = {
        "undefined",
        "null",
        "string",
        "number",
        "boolean",
        "symbol",
        "bigint"
    };

    if (values.size() != expectedTypes.size()) {
        throw std::runtime_error("Value type count check failed");
    }

    for (std::size_t i = 0; i < values.size(); ++i) {
        if (typeName(values[i]) != expectedTypes[i]) {
            throw std::runtime_error("Value type inspection check failed");
        }
    }

    RepositoryConfiguration configuration{
        "self-check",
        true,
        2,
        5.0,
        std::nullopt,
        Symbol("self-check")
    };

    RepositoryService service(configuration);

    service.process(
        createValidEvent(
            "self-check",
            "10000000000000000001",
            true,
            std::nullopt
        )
    );

    if (service.acceptedEvents() != 1) {
        throw std::runtime_error("Event acceptance check failed");
    }

    try {
        service.process(
            createValidEvent(
                "self-check",
                "10000000000000000001",
                true,
                std::nullopt
            )
        );

        throw std::runtime_error(
            "Duplicate event should have been rejected"
        );
    } catch (const ValidationError&) {
        // Expected failure.
    }

    std::cout << "All self checks passed.\n";
}

} // namespace repository

int main() {
    try {
        std::cout
            << "C++ repository data-type case study\n"
            << "C++17 executable implementation\n";

        repository::demonstrateVariablesAndTypes();
        repository::demonstrateNumericBoundaries();
        repository::demonstrateSymbols();
        repository::demonstrateVariantTypes();
        repository::demonstrateRepositoryCaseStudy();
        repository::demonstrateFailureModes();
        repository::runSelfChecks();

        std::cout << "\nCase study complete.\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr
            << "Fatal error: "
            << error.what()
            << '\n';
        return 1;
    }
}
