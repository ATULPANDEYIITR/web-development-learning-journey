/*
 * React Testing: Unit Tests, Component Tests, Mocking,
 * User Interaction Testing, and Test Execution.
 *
 * C++17 standalone testing engine.
 *
 * Compile:
 *   g++ -std=c++17 -O2 -Wall -Wextra -pedantic react_testing.cpp -o react_testing
 *
 * Run:
 *   ./react_testing
 *
 * The program implements a component-testing model and a lightweight
 * automated test runner. It models the behavioral contracts tested
 * around React components without depending on a JavaScript runtime.
 */

#include <algorithm>
#include <functional>
#include <iostream>
#include <map>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>
#include <sstream>
#include <utility>


// ============================================================
// 1. TEST FRAMEWORK
// ============================================================

class TestFailure : public std::runtime_error {
public:
    explicit TestFailure(const std::string& message)
        : std::runtime_error(message) {}
};


struct TestCase {
    std::string name;
    std::function<void()> execute;
};


class TestRunner {
private:
    std::vector<TestCase> tests;
    int passed = 0;
    int failed = 0;

public:
    void add(const std::string& name,
             std::function<void()> execute) {
        tests.push_back({name, std::move(execute)});
    }

    void run() {
        std::cout << "\nAUTOMATED TEST EXECUTION\n";
        std::cout << "=======================\n";

        for (const auto& test : tests) {
            try {
                test.execute();
                ++passed;

                std::cout << "[PASS] "
                          << test.name << '\n';

            } catch (const std::exception& error) {
                ++failed;

                std::cout << "[FAIL] "
                          << test.name
                          << " | "
                          << error.what()
                          << '\n';

            } catch (...) {
                ++failed;

                std::cout << "[FAIL] "
                          << test.name
                          << " | Unknown exception\n";
            }
        }

        std::cout << "\nTEST REPORT\n";
        std::cout << "===========\n";
        std::cout << "Total: " << tests.size() << '\n';
        std::cout << "Passed: " << passed << '\n';
        std::cout << "Failed: " << failed << '\n';

        std::cout << "Result: "
                  << (failed == 0 ? "PASSED" : "FAILED")
                  << '\n';
    }

    bool successful() const {
        return failed == 0;
    }
};


// ============================================================
// 2. ASSERTION UTILITIES
// ============================================================

void require(bool condition, const std::string& message) {
    if (!condition) {
        throw TestFailure(message);
    }
}

template <typename T>
void requireEqual(
    const T& actual,
    const T& expected,
    const std::string& message
) {
    if (!(actual == expected)) {
        throw TestFailure(message);
    }
}


// ============================================================
// 3. DOMAIN MODEL
// ============================================================

struct User {
    int id;
    std::string name;
    std::string email;
    bool active;

    bool operator==(const User& other) const {
        return id == other.id &&
               name == other.name &&
               email == other.email &&
               active == other.active;
    }
};


enum class ComponentStatus {
    IDLE,
    LOADING,
    SUCCESS,
    ERROR
};


enum class TestCategory {
    UNIT,
    COMPONENT,
    INTERACTION,
    MOCKING,
    ASYNC_BEHAVIOR
};


std::string statusName(ComponentStatus status) {
    switch (status) {
        case ComponentStatus::IDLE:
            return "IDLE";
        case ComponentStatus::LOADING:
            return "LOADING";
        case ComponentStatus::SUCCESS:
            return "SUCCESS";
        case ComponentStatus::ERROR:
            return "ERROR";
    }

    return "UNKNOWN";
}


// ============================================================
// 4. UNIT-TESTED FUNCTIONS
// ============================================================

bool validateEmail(const std::string& email) {
    if (email.empty() || email.size() > 254) {
        return false;
    }

    const auto at = email.find('@');

    if (at == std::string::npos ||
        at == 0 ||
        at != email.rfind('@')) {
        return false;
    }

    const auto dot = email.find('.', at + 1);

    if (dot == std::string::npos ||
        dot == at + 1 ||
        dot == email.size() - 1) {
        return false;
    }

    if (email.find(' ') != std::string::npos) {
        return false;
    }

    return true;
}


std::string normalizeSearch(std::string value) {
    std::transform(
        value.begin(),
        value.end(),
        value.begin(),
        [](unsigned char ch) {
            return static_cast<char>(std::tolower(ch));
        }
    );

    return value;
}


std::vector<User> filterUsers(
    const std::vector<User>& users,
    const std::string& query
) {
    const std::string normalized = normalizeSearch(query);

    if (normalized.empty()) {
        return users;
    }

    std::vector<User> result;

    for (const auto& user : users) {
        const std::string name = normalizeSearch(user.name);
        const std::string email = normalizeSearch(user.email);

        if (name.find(normalized) != std::string::npos ||
            email.find(normalized) != std::string::npos) {
            result.push_back(user);
        }
    }

    return result;
}


// ============================================================
// 5. MOCK API
// ============================================================

class IUserRepository {
public:
    virtual ~IUserRepository() = default;

    virtual std::vector<User> fetchUsers() = 0;
};


class MockUserRepository : public IUserRepository {
private:
    std::vector<User> users;
    bool shouldFail;
    int calls = 0;

public:
    MockUserRepository(
        std::vector<User> data,
        bool failure = false
    )
        : users(std::move(data)),
          shouldFail(failure) {}

    std::vector<User> fetchUsers() override {
        ++calls;

        if (shouldFail) {
            throw std::runtime_error(
                "Mock API connection failed"
            );
        }

        return users;
    }

    int getCalls() const {
        return calls;
    }
};


// ============================================================
// 6. COMPONENT MODEL
// ============================================================

class UserDirectory {
private:
    std::shared_ptr<IUserRepository> repository;

    std::vector<User> users;
    ComponentStatus status = ComponentStatus::IDLE;

    std::string searchQuery;
    std::string errorMessage;

    std::function<void(const User&)> onSelect;

public:
    explicit UserDirectory(
        std::shared_ptr<IUserRepository> source
    )
        : repository(std::move(source)) {

        if (!repository) {
            throw std::invalid_argument(
                "Repository cannot be null"
            );
        }
    }

    void setSelectionHandler(
        std::function<void(const User&)> handler
    ) {
        onSelect = std::move(handler);
    }

    void mount() {
        status = ComponentStatus::LOADING;
        errorMessage.clear();

        try {
            users = repository->fetchUsers();
            status = ComponentStatus::SUCCESS;
        } catch (const std::exception& error) {
            errorMessage = error.what();
            status = ComponentStatus::ERROR;
        }
    }

    void search(const std::string& query) {
        searchQuery = query;
    }

    std::vector<User> visibleUsers() const {
        return filterUsers(users, searchQuery);
    }

    void selectUser(int id) {
        const auto found = std::find_if(
            visibleUsers().begin(),
            visibleUsers().end(),
            [id](const User& user) {
                return user.id == id;
            }
        );

        // Resolve against a stable local collection.
        const auto visible = visibleUsers();

        const auto selected = std::find_if(
            visible.begin(),
            visible.end(),
            [id](const User& user) {
                return user.id == id;
            }
        );

        if (selected == visible.end()) {
            throw std::out_of_range(
                "Selected user does not exist in results"
            );
        }

        if (onSelect) {
            onSelect(*selected);
        }
    }

    ComponentStatus getStatus() const {
        return status;
    }

    const std::string& getError() const {
        return errorMessage;
    }

    std::string render() const {
        switch (status) {
            case ComponentStatus::IDLE:
                return "NOT MOUNTED";

            case ComponentStatus::LOADING:
                return "Loading users...";

            case ComponentStatus::ERROR:
                return "ERROR: " + errorMessage;

            case ComponentStatus::SUCCESS:
                if (visibleUsers().empty()) {
                    return "No users found";
                }

                return "User list rendered";
        }

        return "Unknown state";
    }
};


// ============================================================
// 7. TEST DATA
// ============================================================

std::vector<User> sampleUsers() {
    return {
        {1, "Alice Johnson", "alice@example.com", true},
        {2, "Bob Smith", "bob@example.com", true},
        {3, "Charlie Brown", "charlie@example.com", false}
    };
}


// ============================================================
// 8. UNIT TESTS
// ============================================================

void registerUnitTests(TestRunner& runner) {

    runner.add("Valid email", [] {
        require(
            validateEmail("alice@example.com"),
            "Valid email rejected"
        );
    });

    runner.add("Invalid email", [] {
        require(
            !validateEmail("alice@@example.com"),
            "Malformed email accepted"
        );
    });

    runner.add("Missing email domain", [] {
        require(
            !validateEmail("alice@"),
            "Missing domain accepted"
        );
    });

    runner.add("Empty email", [] {
        require(
            !validateEmail(""),
            "Empty email accepted"
        );
    });

    runner.add("Search by name", [] {
        const auto result = filterUsers(
            sampleUsers(),
            "alice"
        );

        requireEqual(
            result.size(),
            static_cast<std::size_t>(1),
            "Unexpected search result count"
        );

        requireEqual(
            result[0].id,
            1,
            "Wrong user returned"
        );
    });

    runner.add("Case insensitive search", [] {
        const auto result = filterUsers(
            sampleUsers(),
            "BOB"
        );

        requireEqual(
            result.size(),
            static_cast<std::size_t>(1),
            "Case insensitive search failed"
        );
    });

    runner.add("Empty search returns all records", [] {
        requireEqual(
            filterUsers(sampleUsers(), "").size(),
            static_cast<std::size_t>(3),
            "Empty search did not return all users"
        );
    });

    runner.add("Unknown search result", [] {
        require(
            filterUsers(sampleUsers(), "unknown").empty(),
            "Unexpected matching user"
        );
    });
}


// ============================================================
// 9. COMPONENT TESTS
// ============================================================

void registerComponentTests(TestRunner& runner) {

    runner.add("Initial component state", [] {
        auto repository =
            std::make_shared<MockUserRepository>(sampleUsers());

        UserDirectory component(repository);

        requireEqual(
            component.getStatus(),
            ComponentStatus::IDLE,
            "Incorrect initial state"
        );
    });

    runner.add("Successful component mount", [] {
        auto repository =
            std::make_shared<MockUserRepository>(sampleUsers());

        UserDirectory component(repository);

        component.mount();

        requireEqual(
            component.getStatus(),
            ComponentStatus::SUCCESS,
            "Component did not reach success state"
        );

        requireEqual(
            component.visibleUsers().size(),
            static_cast<std::size_t>(3),
            "Users not loaded"
        );
    });

    runner.add("Component loading and rendering", [] {
        auto repository =
            std::make_shared<MockUserRepository>(sampleUsers());

        UserDirectory component(repository);

        requireEqual(
            component.render(),
            std::string("NOT MOUNTED"),
            "Incorrect initial rendering"
        );

        component.mount();

        requireEqual(
            component.render(),
            std::string("User list rendered"),
            "Incorrect successful rendering"
        );
    });

    runner.add("Component API failure", [] {
        auto repository =
            std::make_shared<MockUserRepository>(
                std::vector<User>{},
                true
            );

        UserDirectory component(repository);
        component.mount();

        requireEqual(
            component.getStatus(),
            ComponentStatus::ERROR,
            "API failure was not represented"
        );

        require(
            component.getError().find("Mock API") !=
            std::string::npos,
            "Missing error information"
        );
    });

    runner.add("Empty API response", [] {
        auto repository =
            std::make_shared<MockUserRepository>(
                std::vector<User>{}
            );

        UserDirectory component(repository);
        component.mount();

        requireEqual(
            component.render(),
            std::string("No users found"),
            "Empty response not handled"
        );
    });

    runner.add("Invalid repository dependency", [] {
        bool rejected = false;

        try {
            UserDirectory component(nullptr);
        } catch (const std::invalid_argument&) {
            rejected = true;
        }

        require(
            rejected,
            "Null dependency should be rejected"
        );
    });
}


// ============================================================
// 10. INTERACTION TESTS
// ============================================================

void registerInteractionTests(TestRunner& runner) {

    runner.add("Search interaction", [] {
        auto repository =
            std::make_shared<MockUserRepository>(sampleUsers());

        UserDirectory component(repository);

        component.mount();
        component.search("alice");

        const auto results = component.visibleUsers();

        requireEqual(
            results.size(),
            static_cast<std::size_t>(1),
            "Search interaction failed"
        );

        requireEqual(
            results[0].id,
            1,
            "Incorrect search result"
        );
    });

    runner.add("Clear search interaction", [] {
        auto repository =
            std::make_shared<MockUserRepository>(sampleUsers());

        UserDirectory component(repository);

        component.mount();

        component.search("alice");
        component.search("");

        requireEqual(
            component.visibleUsers().size(),
            static_cast<std::size_t>(3),
            "Clearing search did not restore users"
        );
    });

    runner.add("No-result interaction", [] {
        auto repository =
            std::make_shared<MockUserRepository>(sampleUsers());

        UserDirectory component(repository);

        component.mount();
        component.search("unknown");

        requireEqual(
            component.render(),
            std::string("No users found"),
            "No-result state incorrect"
        );
    });

    runner.add("Selection callback", [] {
        auto repository =
            std::make_shared<MockUserRepository>(sampleUsers());

        UserDirectory component(repository);

        int selectedId = -1;

        component.setSelectionHandler(
            [&selectedId](const User& user) {
                selectedId = user.id;
            }
        );

        component.mount();
        component.selectUser(2);

        requireEqual(
            selectedId,
            2,
            "Selection callback received incorrect user"
        );
    });

    runner.add("Reject selection outside filtered results", [] {
        auto repository =
            std::make_shared<MockUserRepository>(sampleUsers());

        UserDirectory component(repository);

        component.mount();
        component.search("alice");

        bool rejected = false;

        try {
            component.selectUser(2);
        } catch (const std::out_of_range&) {
            rejected = true;
        }

        require(
            rejected,
            "Filtered-out user was incorrectly selectable"
        );
    });
}


// ============================================================
// 11. MOCKING TESTS
// ============================================================

void registerMockingTests(TestRunner& runner) {

    runner.add("Mock dependency call count", [] {
        auto repository =
            std::make_shared<MockUserRepository>(sampleUsers());

        UserDirectory component(repository);

        component.mount();

        requireEqual(
            repository->getCalls(),
            1,
            "Unexpected dependency invocation count"
        );
    });

    runner.add("Mock API failure isolation", [] {
        auto repository =
            std::make_shared<MockUserRepository>(
                std::vector<User>{},
                true
            );

        UserDirectory component(repository);

        component.mount();

        requireEqual(
            component.getStatus(),
            ComponentStatus::ERROR,
            "Mocked failure was not isolated"
        );
    });
}


// ============================================================
// 12. EXECUTION
// ============================================================

int main() {
    TestRunner runner;

    registerUnitTests(runner);
    registerComponentTests(runner);
    registerInteractionTests(runner);
    registerMockingTests(runner);

    runner.run();

    return runner.successful() ? 0 : 1;
}
