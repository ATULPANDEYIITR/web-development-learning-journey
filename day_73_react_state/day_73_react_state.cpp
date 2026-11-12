#include <iostream>
#include <string>
#include <vector>
#include <map>
#include <functional>
#include <stdexcept>
#include <algorithm>
#include <numeric>
#include <iomanip>
#include <optional>

using namespace std;

/*
 * REACT STATE MANAGEMENT CONCEPTS
 *
 * C++17 simulation of:
 * 1. State initialization
 * 2. State updates
 * 3. Functional updates
 * 4. Derived state
 * 5. Controlled components
 * 6. Immutable-style updates
 * 7. State validation
 * 8. State transitions
 */

class StateError : public runtime_error {
public:
    explicit StateError(const string& message)
        : runtime_error(message) {}
};

enum class InputStatus {
    Valid,
    Invalid
};

struct User {
    string name;
    string email;
    int age;
};

struct Product {
    int id;
    string name;
    double price;
    int quantity;
};

struct ShoppingSummary {
    int totalItems;
    double subtotal;
    bool isEmpty;
};

class StateManager {
private:
    map<string, int> numericState;
    unsigned long long version = 0;

public:
    explicit StateManager(
        const map<string, int>& initialState
    ) : numericState(initialState) {
        for (const auto& entry : numericState) {
            if (entry.first.empty()) {
                throw StateError("State key cannot be empty.");
            }
        }
    }

    int get(const string& key) const {
        auto iterator = numericState.find(key);

        if (iterator == numericState.end()) {
            throw StateError("State property does not exist.");
        }

        return iterator->second;
    }

    void set(const string& key, int value) {
        auto iterator = numericState.find(key);

        if (iterator == numericState.end()) {
            throw StateError("Unknown state property.");
        }

        if (iterator->second != value) {
            iterator->second = value;
            ++version;
        }
    }

    void update(
        const string& key,
        const function<int(int)>& updater
    ) {
        if (!updater) {
            throw StateError("Updater function is empty.");
        }

        int previous = get(key);
        int next = updater(previous);

        set(key, next);
    }

    unsigned long long getVersion() const {
        return version;
    }

    void print() const {
        for (const auto& entry : numericState) {
            cout << entry.first
                 << " = "
                 << entry.second
                 << '\n';
        }
    }
};


/* =========================================================
   COUNTER
   ========================================================= */

void demonstrateCounter() {
    cout << "\n--- Counter State ---\n";

    StateManager counter({
        {"count", 0}
    });

    counter.update(
        "count",
        [](int previous) {
            return previous + 1;
        }
    );

    counter.update(
        "count",
        [](int previous) {
            return previous + 1;
        }
    );

    cout << "Count: " << counter.get("count") << '\n';

    counter.update(
        "count",
        [](int previous) {
            return previous + 5;
        }
    );

    cout << "Updated count: "
         << counter.get("count")
         << '\n';

    cout << "State version: "
         << counter.getVersion()
         << '\n';
}


/* =========================================================
   CONTROLLED COMPONENT SIMULATION
   ========================================================= */

class ControlledForm {
private:
    string username;
    string email;
    int age = 0;
    bool acceptedTerms = false;

public:
    InputStatus setUsername(const string& value) {
        if (
            value.empty() ||
            value.size() > 50
        ) {
            return InputStatus::Invalid;
        }

        username = value;
        return InputStatus::Valid;
    }

    InputStatus setEmail(const string& value) {
        size_t separator = value.find('@');

        if (
            separator == string::npos ||
            separator == 0 ||
            separator == value.size() - 1 ||
            value.size() > 254
        ) {
            return InputStatus::Invalid;
        }

        email = value;
        return InputStatus::Valid;
    }

    InputStatus setAge(int value) {
        if (value < 18 || value > 120) {
            return InputStatus::Invalid;
        }

        age = value;
        return InputStatus::Valid;
    }

    void setAcceptedTerms(bool accepted) {
        acceptedTerms = accepted;
    }

    bool isValid() const {
        return (
            !username.empty() &&
            !email.empty() &&
            age >= 18 &&
            acceptedTerms
        );
    }

    void display() const {
        cout << "Username: " << username << '\n';
        cout << "Email: " << email << '\n';
        cout << "Age: " << age << '\n';

        cout << "Accepted terms: "
             << boolalpha
             << acceptedTerms
             << '\n';

        cout << "Form valid: "
             << isValid()
             << '\n';
    }
};

void demonstrateControlledForm() {
    cout << "\n--- Controlled Form ---\n";

    ControlledForm form;

    if (
        form.setUsername("Atul") ==
        InputStatus::Invalid
    ) {
        throw StateError("Invalid username.");
    }

    if (
        form.setEmail("atul@example.com") ==
        InputStatus::Invalid
    ) {
        throw StateError("Invalid email.");
    }

    form.setAge(28);
    form.setAcceptedTerms(true);

    form.display();

    if (
        form.setAge(15) ==
        InputStatus::Invalid
    ) {
        cout << "Rejected invalid age update.\n";
    }
}


/* =========================================================
   SHOPPING CART
   ========================================================= */

class ShoppingCart {
private:
    vector<Product> products;

    static void validateProduct(const Product& product) {
        if (
            product.id <= 0 ||
            product.name.empty() ||
            product.price < 0 ||
            product.quantity <= 0
        ) {
            throw StateError("Invalid product information.");
        }
    }

public:
    void addProduct(const Product& product) {
        validateProduct(product);

        auto iterator = find_if(
            products.begin(),
            products.end(),
            [&](const Product& existing) {
                return existing.id == product.id;
            }
        );

        if (iterator != products.end()) {
            if (
                iterator->quantity >
                1000000 - product.quantity
            ) {
                throw StateError("Quantity limit exceeded.");
            }

            iterator->quantity += product.quantity;
        } else {
            products.push_back(product);
        }
    }

    void removeProduct(int id) {
        auto previousSize = products.size();

        products.erase(
            remove_if(
                products.begin(),
                products.end(),
                [id](const Product& product) {
                    return product.id == id;
                }
            ),
            products.end()
        );

        if (products.size() == previousSize) {
            throw StateError("Product was not found.");
        }
    }

    ShoppingSummary derive() const {
        int totalItems = 0;
        double subtotal = 0.0;

        for (const Product& product : products) {
            totalItems += product.quantity;

            subtotal +=
                product.price * product.quantity;
        }

        return {
            totalItems,
            subtotal,
            products.empty()
        };
    }

    void display() const {
        cout << fixed << setprecision(2);

        for (const Product& product : products) {
            cout << product.name
                 << " | Price: "
                 << product.price
                 << " | Quantity: "
                 << product.quantity
                 << '\n';
        }

        ShoppingSummary summary = derive();

        cout << "Total items: "
             << summary.totalItems
             << '\n';

        cout << "Subtotal: "
             << summary.subtotal
             << '\n';

        cout << "Cart empty: "
             << boolalpha
             << summary.isEmpty
             << '\n';
    }
};

void demonstrateShoppingCart() {
    cout << "\n--- Shopping Cart ---\n";

    ShoppingCart cart;

    cart.addProduct({
        1,
        "Mechanical Keyboard",
        2499.00,
        1
    });

    cart.addProduct({
        2,
        "Wireless Mouse",
        999.00,
        2
    });

    cart.addProduct({
        1,
        "Mechanical Keyboard",
        2499.00,
        1
    });

    cart.display();

    cout << "\nRemoving mouse...\n";

    cart.removeProduct(2);

    cart.display();
}


/* =========================================================
   IMMUTABLE-STYLE STATE TRANSFORMATION
   ========================================================= */

struct Profile {
    string name;
    string city;
    string country;
};

Profile updateCity(
    const Profile& previous,
    const string& newCity
) {
    if (newCity.empty()) {
        throw StateError("City cannot be empty.");
    }

    // Construct a new value instead of mutating the old one.
    return {
        previous.name,
        newCity,
        previous.country
    };
}

void demonstrateImmutableUpdate() {
    cout << "\n--- Immutable Update ---\n";

    const Profile original = {
        "Atul",
        "Lucknow",
        "India"
    };

    Profile updated = updateCity(
        original,
        "Patna"
    );

    cout << "Original city: "
         << original.city
         << '\n';

    cout << "Updated city: "
         << updated.city
         << '\n';
}


/* =========================================================
   ERROR HANDLING
   ========================================================= */

void demonstrateErrors() {
    cout << "\n--- Error Handling ---\n";

    try {
        ShoppingCart cart;

        cart.addProduct({
            3,
            "Invalid Product",
            -500.00,
            1
        });
    }
    catch (const StateError& error) {
        cout << "Validation error: "
             << error.what()
             << '\n';
    }

    try {
        StateManager manager({
            {"count", 10}
        });

        manager.get("missing");
    }
    catch (const StateError& error) {
        cout << "State error: "
             << error.what()
             << '\n';
    }
}


/* =========================================================
   MAIN
   ========================================================= */

int main() {
    try {
        demonstrateCounter();

        demonstrateControlledForm();

        demonstrateShoppingCart();

        demonstrateImmutableUpdate();

        demonstrateErrors();

        cout << "\nReact State concepts demonstrated.\n";
    }
    catch (const exception& error) {
        cerr << "Application failure: "
             << error.what()
             << '\n';

        return 1;
    }

    return 0;
}
