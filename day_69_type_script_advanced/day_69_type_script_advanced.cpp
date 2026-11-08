#include <algorithm>
#include <cassert>
#include <cmath>
#include <functional>
#include <iostream>
#include <map>
#include <memory>
#include <optional>
#include <set>
#include <stdexcept>
#include <string>
#include <type_traits>
#include <utility>
#include <variant>
#include <vector>

using namespace std;

// ============================================================
// 1. GENERIC FUNCTIONS
// ============================================================

template <typename T>
T identity(const T& value) {
    return value;
}

template <typename T>
optional<T> firstItem(const vector<T>& values) {
    if (values.empty()) {
        return nullopt;
    }

    return values.front();
}

template <typename T>
T maximumValue(const vector<T>& values) {
    if (values.empty()) {
        throw invalid_argument("Cannot find maximum of empty vector");
    }

    return *max_element(values.begin(), values.end());
}

// ============================================================
// 2. GENERIC CLASSES
// ============================================================

template <typename T>
class Repository {
private:
    map<string, T> records;

public:
    void add(const string& key, const T& value) {
        if (key.empty()) {
            throw invalid_argument("Empty repository key");
        }

        auto result = records.emplace(key, value);

        if (!result.second) {
            throw runtime_error("Duplicate repository key");
        }
    }

    optional<T> get(const string& key) const {
        auto it = records.find(key);

        if (it == records.end()) {
            return nullopt;
        }

        return it->second;
    }

    bool remove(const string& key) {
        return records.erase(key) > 0;
    }

    size_t size() const {
        return records.size();
    }

    vector<T> all() const {
        vector<T> result;

        for (const auto& [key, value] : records) {
            result.push_back(value);
        }

        return result;
    }
};

// ============================================================
// 3. DOMAIN MODEL
// ============================================================

enum class AccountStatus {
    ACTIVE,
    SUSPENDED,
    CLOSED
};

struct User {
    int id;
    string name;
    string email;
    AccountStatus status;

    User(
        int id,
        string name,
        string email,
        AccountStatus status = AccountStatus::ACTIVE
    )
        : id(id),
          name(move(name)),
          email(move(email)),
          status(status) {

        if (id <= 0) {
            throw invalid_argument("Invalid user ID");
        }

        if (this->name.empty()) {
            throw invalid_argument("Name cannot be empty");
        }

        if (this->email.find('@') == string::npos) {
            throw invalid_argument("Invalid email");
        }
    }
};

struct Product {
    int id;
    string name;
    double price;

    Product(int id, string name, double price)
        : id(id), name(move(name)), price(price) {

        if (id <= 0 || this->name.empty() ||
            !isfinite(price) || price < 0) {
            throw invalid_argument("Invalid product");
        }
    }
};

// ============================================================
// 4. UTILITY-TYPE EQUIVALENTS
// ============================================================

// Partial<T>-style optional update fields.
struct UserPatch {
    optional<string> name;
    optional<string> email;
};

User applyPatch(const User& original, const UserPatch& patch) {
    string name = patch.name.value_or(original.name);
    string email = patch.email.value_or(original.email);

    return User(
        original.id,
        name,
        email,
        original.status
    );
}

// Pick<T, K>-style selection.
template <typename T>
vector<T> pickFields(
    const vector<T>& source,
    const vector<size_t>& indices
) {
    vector<T> result;

    for (size_t index : indices) {
        if (index >= source.size()) {
            throw out_of_range("Field index outside source");
        }

        result.push_back(source[index]);
    }

    return result;
}

// Readonly<T>-style interface.
template <typename T>
class ReadOnlyView {
private:
    const T& value;

public:
    explicit ReadOnlyView(const T& value) : value(value) {}

    const T& get() const {
        return value;
    }
};

// ============================================================
// 5. TYPE TRAITS AND CONDITIONAL TYPES
// ============================================================

// C++ compile-time conditional selection.
template <typename T>
using NormalizedType = conditional_t<
    is_integral_v<T>,
    long long,
    double
>;

template <typename T>
NormalizedType<T> normalizeNumber(T value) {
    static_assert(
        is_arithmetic_v<T>,
        "Numeric type required"
    );

    if constexpr (is_integral_v<T>) {
        return static_cast<long long>(
            value < 0 ? -value : value
        );
    } else {
        return abs(static_cast<double>(value));
    }
}

// Enable_if-style constrained function.
template <
    typename T,
    enable_if_t<is_arithmetic_v<T>, int> = 0
>
T doubleValue(T value) {
    return value * 2;
}

// ============================================================
// 6. TYPE NARROWING THROUGH VARIANT
// ============================================================

using InputValue = variant<int, double, string>;

string describeValue(const InputValue& value) {
    if (holds_alternative<int>(value)) {
        return "Integer: " +
            to_string(get<int>(value));
    }

    if (holds_alternative<double>(value)) {
        return "Decimal: " +
            to_string(get<double>(value));
    }

    if (holds_alternative<string>(value)) {
        return "String: " +
            get<string>(value);
    }

    throw runtime_error("Unknown variant");
}

// ============================================================
// 7. DISCRIMINATED UNION
// ============================================================

struct Success {
    string transactionId;
    double amount;
};

struct Failure {
    string message;
    int code;
};

using OperationResult = variant<Success, Failure>;

string processResult(const OperationResult& result) {
    if (holds_alternative<Success>(result)) {
        const auto& success = get<Success>(result);

        return "Approved: " + success.transactionId;
    }

    const auto& failure = get<Failure>(result);

    return "Rejected " + to_string(failure.code) +
           ": " + failure.message;
}

// ============================================================
// 8. TYPE GUARDS
// ============================================================

bool isValidUser(const User& user) {
    return user.id > 0 &&
           !user.name.empty() &&
           user.email.find('@') != string::npos;
}

template <typename T, typename Predicate>
vector<T> filterByGuard(
    const vector<T>& values,
    Predicate predicate
) {
    vector<T> result;

    copy_if(
        values.begin(),
        values.end(),
        back_inserter(result),
        predicate
    );

    return result;
}

// ============================================================
// 9. GENERIC TRANSFORMATION PIPELINE
// ============================================================

template <typename T>
class Pipeline {
private:
    vector<function<T(T)>> steps;

public:
    void addStep(function<T(T)> step) {
        steps.push_back(move(step));
    }

    T execute(T value) const {
        for (const auto& step : steps) {
            value = step(move(value));
        }

        return value;
    }
};

// ============================================================
// 10. ENTERPRISE VALIDATION SERVICE
// ============================================================

class UserService {
private:
    Repository<User> repository;

public:
    void registerUser(const User& user) {
        if (!isValidUser(user)) {
            throw invalid_argument("User validation failed");
        }

        repository.add(
            "U" + to_string(user.id),
            user
        );
    }

    optional<User> findUser(int id) const {
        if (id <= 0) {
            throw invalid_argument("Invalid user ID");
        }

        return repository.get("U" + to_string(id));
    }

    size_t userCount() const {
        return repository.size();
    }
};

// ============================================================
// 11. TESTS
// ============================================================

void runTests() {
    assert(identity(100) == 100);
    assert(identity(string("Advanced")) == "Advanced");

    assert(firstItem(vector<int>{10, 20}) == 10);
    assert(!firstItem(vector<int>{}).has_value());

    assert(maximumValue(vector<int>{2, 9, 5}) == 9);

    Repository<User> repository;

    User user(1, "Aarav", "aarav@example.com");
    repository.add("U001", user);

    assert(repository.get("U001").has_value());
    assert(repository.remove("U001"));
    assert(!repository.get("U001").has_value());

    User original(2, "Mira", "mira@example.com");

    UserPatch patch;
    patch.name = "Mira Sharma";

    User updated = applyPatch(original, patch);

    assert(updated.name == "Mira Sharma");
    assert(original.name == "Mira");

    vector<int> numbers{10, 20, 30};

    assert(pickFields(numbers, {0, 2}).size() == 2);

    assert(normalizeNumber(-10) == 10);
    assert(normalizeNumber(-5.5) == 5.5);

    assert(doubleValue(10) == 20);

    assert(describeValue(42) == "Integer: 42");
    assert(describeValue(string("Test")) == "String: Test");

    assert(
        processResult(Success{"TX-001", 500.0}) ==
        "Approved: TX-001"
    );

    assert(isValidUser(user));

    vector<User> users{
        user,
        User(3, "Ravi", "ravi@example.com")
    };

    assert(filterByGuard(users, isValidUser).size() == 2);

    Pipeline<string> pipeline;

    pipeline.addStep([](string value) {
        transform(
            value.begin(),
            value.end(),
            value.begin(),
            ::toupper
        );

        return value;
    });

    assert(pipeline.execute("advanced") == "ADVANCED");

    UserService service;
    service.registerUser(user);

    assert(service.findUser(1).has_value());
    assert(service.userCount() == 1);

    cout << "All C++17 tests passed.\n";
}

// ============================================================
// MAIN
// ============================================================

int main() {
    try {
        cout << "ADVANCED TYPE SYSTEM CONCEPTS\n";
        cout << "========================================\n";

        runTests();

        Repository<Product> products;

        products.add(
            "P001",
            Product(1, "Security Platform", 4999.0)
        );

        cout << "\nGeneric repository:\n";

        for (const auto& product : products.all()) {
            cout << product.name
                 << " | Price: "
                 << product.price << '\n';
        }

        cout << "\nType narrowing:\n";
        cout << describeValue(125) << '\n';
        cout << describeValue(string("TypeScript")) << '\n';

        cout << "\nConditional type equivalent:\n";
        cout << normalizeNumber(-125.5) << '\n';

        cout << "\nDiscriminated union:\n";
        cout << processResult(
            Failure{"Insufficient permissions", 403}
        ) << '\n';

        ReadOnlyView<User> view(
            User(10, "Mira", "mira@example.com")
        );

        cout << "\nReadonly view:\n";
        cout << view.get().name << '\n';

    } catch (const exception& error) {
        cerr << "Application error: "
             << error.what() << '\n';

        return 1;
    }

    return 0;
}
