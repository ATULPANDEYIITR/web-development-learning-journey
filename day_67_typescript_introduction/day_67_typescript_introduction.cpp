#include <algorithm>
#include <cmath>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <optional>
#include <regex>
#include <set>
#include <stdexcept>
#include <string>
#include <type_traits>
#include <variant>
#include <vector>

using namespace std;

/*
 * TypeScript Introduction:
 * Why TypeScript, Type Annotations, Primitive Types, and Type Inference.
 *
 * This C++17 program models a typed service configuration registry.
 * It demonstrates static declarations, type deduction, primitive
 * validation, domain constraints, and controlled state transitions.
 */

class ValidationError : public runtime_error {
public:
    explicit ValidationError(const string& message)
        : runtime_error(message) {}
};


enum class AccountStatus {
    Active,
    Inactive,
    Suspended
};


string statusToString(AccountStatus status) {
    switch (status) {
        case AccountStatus::Active:
            return "ACTIVE";

        case AccountStatus::Inactive:
            return "INACTIVE";

        case AccountStatus::Suspended:
            return "SUSPENDED";
    }

    throw ValidationError("Unknown account status.");
}


// A variant provides a closed set of allowed metadata types.
using Primitive = variant<
    string,
    int64_t,
    double,
    bool,
    monostate
>;


struct User {
    int64_t id;
    string name;
    string email;
    int age;
    bool verified;
    AccountStatus status;
    map<string, Primitive> metadata;
};


class TypeValidator {
public:
    template <typename T>
    static bool isValidType(const Primitive& value) {
        return holds_alternative<T>(value);
    }

    static bool isFiniteNumber(const Primitive& value) {
        if (holds_alternative<double>(value)) {
            return isfinite(get<double>(value));
        }

        return holds_alternative<int64_t>(value);
    }

    static string inferPrimitiveType(const Primitive& value) {
        if (holds_alternative<string>(value)) {
            return "string";
        }

        if (holds_alternative<int64_t>(value)) {
            return "integer";
        }

        if (holds_alternative<double>(value)) {
            return "number";
        }

        if (holds_alternative<bool>(value)) {
            return "boolean";
        }

        return "null";
    }
};


class UserValidator {
private:
    static const regex EMAIL_PATTERN;

public:
    static void validate(const User& user) {
        if (user.id <= 0) {
            throw ValidationError(
                "User ID must be positive."
            );
        }

        if (user.name.empty() ||
            user.name.find_first_not_of(" \t\n") == string::npos) {
            throw ValidationError(
                "User name cannot be empty."
            );
        }

        if (!regex_match(user.email, EMAIL_PATTERN)) {
            throw ValidationError(
                "Invalid email address."
            );
        }

        if (user.age < 18 || user.age > 120) {
            throw ValidationError(
                "Age must be between 18 and 120."
            );
        }

        for (const auto& [key, value] : user.metadata) {
            if (key.empty()) {
                throw ValidationError(
                    "Metadata key cannot be empty."
                );
            }

            if (!TypeValidator::isFiniteNumber(value)) {
                if (holds_alternative<double>(value)) {
                    throw ValidationError(
                        "Metadata numbers must be finite."
                    );
                }
            }
        }
    }
};

const regex UserValidator::EMAIL_PATTERN(
    R"([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})"
);


class UserRegistry {
private:
    map<int64_t, User> users;
    map<string, int64_t> emailIndex;

public:
    void registerUser(const User& user) {
        UserValidator::validate(user);

        if (users.count(user.id)) {
            throw ValidationError(
                "Duplicate user ID."
            );
        }

        if (emailIndex.count(user.email)) {
            throw ValidationError(
                "Duplicate email address."
            );
        }

        users.emplace(user.id, user);
        emailIndex.emplace(user.email, user.id);
    }

    optional<User> findById(int64_t id) const {
        auto iterator = users.find(id);

        if (iterator == users.end()) {
            return nullopt;
        }

        return iterator->second;
    }

    optional<User> findByEmail(const string& email) const {
        auto iterator = emailIndex.find(email);

        if (iterator == emailIndex.end()) {
            return nullopt;
        }

        return findById(iterator->second);
    }

    void deactivate(int64_t id) {
        auto iterator = users.find(id);

        if (iterator == users.end()) {
            throw ValidationError(
                "Cannot deactivate an unknown user."
            );
        }

        if (iterator->second.status == AccountStatus::Suspended) {
            throw ValidationError(
                "Suspended users require administrative review."
            );
        }

        iterator->second.status = AccountStatus::Inactive;
    }

    vector<User> activeUsers() const {
        vector<User> result;

        for (const auto& [id, user] : users) {
            if (user.status == AccountStatus::Active) {
                result.push_back(user);
            }
        }

        return result;
    }

    size_t size() const {
        return users.size();
    }
};


void demonstrateTypeDeclarations() {
    cout << "\nTYPE DECLARATIONS AND INFERENCE\n";

    // Explicit declarations.
    string username = "Atul";
    int age = 29;
    double balance = 25000.75;
    bool verified = true;

    // C++17 type deduction.
    auto inferredName = string("Riya");
    auto inferredAge = 31;
    auto inferredBalance = 1200.50;
    auto inferredVerified = false;

    cout << "username: " << username << '\n';
    cout << "age: " << age << '\n';
    cout << "balance: " << balance << '\n';
    cout << "verified: " << boolalpha << verified << '\n';

    cout << "Inferred name type: "
         << typeid(inferredName).name() << '\n';

    cout << "Inferred age type: "
         << typeid(inferredAge).name() << '\n';

    cout << "Inferred balance type: "
         << typeid(inferredBalance).name() << '\n';

    cout << "Inferred verified type: "
         << typeid(inferredVerified).name() << '\n';
}


void demonstratePrimitiveTypes() {
    cout << "\nPRIMITIVE VALUE VALIDATION\n";

    vector<Primitive> values = {
        string("Engineering"),
        int64_t(42),
        42.75,
        true,
        monostate{}
    };

    for (const auto& value : values) {
        cout << TypeValidator::inferPrimitiveType(value)
             << '\n';
    }

    Primitive numericValue = 99.5;

    if (!TypeValidator::isFiniteNumber(numericValue)) {
        throw ValidationError("Invalid numeric value.");
    }

    Primitive invalidNumber = numeric_limits<double>::infinity();

    try {
        if (!TypeValidator::isFiniteNumber(invalidNumber)) {
            throw ValidationError(
                "Infinite values are not accepted."
            );
        }
    } catch (const ValidationError& error) {
        cout << "Rejected: " << error.what() << '\n';
    }
}


void demonstrateRegistry() {
    cout << "\nUSER REGISTRY WORKFLOW\n";

    UserRegistry registry;

    User first{
        1,
        "Atul Pandey",
        "atul@example.com",
        29,
        true,
        AccountStatus::Active,
        {
            {"department", string("Engineering")},
            {"experience", int64_t(5)},
            {"verified", true}
        }
    };

    User second{
        2,
        "Riya Sharma",
        "riya@example.com",
        31,
        false,
        AccountStatus::Active,
        {
            {"department", string("Research")},
            {"experience", int64_t(7)}
        }
    };

    registry.registerUser(first);
    registry.registerUser(second);

    for (const User& user : registry.activeUsers()) {
        cout << user.id << " | "
             << user.name << " | "
             << user.email << " | "
             << statusToString(user.status)
             << '\n';
    }

    auto found = registry.findByEmail("atul@example.com");

    if (found.has_value()) {
        cout << "Found user: " << found->name << '\n';
    }

    registry.deactivate(2);

    cout << "Active users: "
         << registry.activeUsers().size()
         << '\n';

    try {
        registry.registerUser(first);
    } catch (const ValidationError& error) {
        cout << "Duplicate rejected: "
             << error.what() << '\n';
    }

    try {
        User invalid{
            3,
            "Invalid",
            "invalid-email",
            25,
            false,
            AccountStatus::Active,
            {}
        };

        registry.registerUser(invalid);

    } catch (const ValidationError& error) {
        cout << "Invalid user rejected: "
             << error.what() << '\n';
    }

    cout << "Total registered users: "
         << registry.size() << '\n';
}


int main() {
    try {
        demonstrateTypeDeclarations();
        demonstratePrimitiveTypes();
        demonstrateRegistry();

        cout << "\nALL TESTS COMPLETED SUCCESSFULLY\n";

    } catch (const exception& error) {
        cerr << "Application error: "
             << error.what() << '\n';

        return 1;
    }

    return 0;
}
