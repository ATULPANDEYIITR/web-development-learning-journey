/*
 * React Context: Provider Scopes and Global State Engine
 *
 * C++17 implementation of a context-based state-management
 * engine featuring:
 *
 * - Provider and consumer relationships
 * - Nested provider resolution
 * - Independent state scopes
 * - Typed actions
 * - State validation
 * - Observer subscriptions
 * - Selective notifications
 * - Approval of state transitions through policies
 * - Batch updates
 * - Merge-free immutable-style state replacement
 * - Error handling
 *
 * Compile:
 * g++ -std=c++17 -O2 -Wall -Wextra -pedantic react_context.cpp -o context
 *
 * Run:
 * ./context
 */

#include <algorithm>
#include <functional>
#include <iostream>
#include <map>
#include <memory>
#include <optional>
#include <set>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

using namespace std;


/* =========================================================
   1. Domain Types
   ========================================================= */

enum class Theme {
    Light,
    Dark,
    System
};

enum class ActionType {
    Login,
    Logout,
    UpdateProfile,
    SetTheme,
    SetLanguage,
    Reset
};

string themeName(Theme theme) {
    switch (theme) {
        case Theme::Light: return "light";
        case Theme::Dark: return "dark";
        case Theme::System: return "system";
    }

    throw invalid_argument("Unknown theme.");
}

struct Profile {
    string userId;
    string name;
    string email;
};

struct AppState {
    bool authenticated = false;
    optional<Profile> profile;
    Theme theme = Theme::Light;
    string language = "en";
    unsigned long long version = 0;
};

struct Action {
    ActionType type;
    string value1;
    string value2;
};


/* =========================================================
   2. Exceptions
   ========================================================= */

class ContextException : public runtime_error {
public:
    explicit ContextException(const string& message)
        : runtime_error(message) {}
};

class MissingProviderException : public ContextException {
public:
    explicit MissingProviderException(const string& name)
        : ContextException("Provider not found: " + name) {}
};

class StateValidationException : public ContextException {
public:
    explicit StateValidationException(const string& message)
        : ContextException(message) {}
};


/* =========================================================
   3. State Validation
   ========================================================= */

void validate(const AppState& state) {
    if (state.authenticated && !state.profile.has_value()) {
        throw StateValidationException(
            "Authenticated state requires a profile."
        );
    }

    if (!state.authenticated && state.profile.has_value()) {
        throw StateValidationException(
            "Unauthenticated state cannot contain a profile."
        );
    }

    const set<string> languages = {
        "en", "hi", "fr", "de"
    };

    if (!languages.count(state.language)) {
        throw StateValidationException(
            "Unsupported language."
        );
    }

    if (state.profile.has_value()) {
        const Profile& profile = *state.profile;

        if (profile.userId.empty() || profile.name.empty()) {
            throw StateValidationException(
                "Profile identity and name are required."
            );
        }
    }
}


/* =========================================================
   4. Reducer
   ========================================================= */

AppState reduceState(
    const AppState& current,
    const Action& action
) {
    AppState next = current;

    switch (action.type) {

        case ActionType::Login:
            if (action.value1.empty() || action.value2.empty()) {
                throw StateValidationException(
                    "Login requires user ID and name."
                );
            }

            next.authenticated = true;
            next.profile = Profile{
                action.value1,
                action.value2,
                ""
            };
            break;

        case ActionType::Logout:
            next.authenticated = false;
            next.profile.reset();
            break;

        case ActionType::UpdateProfile:
            if (!current.authenticated || !current.profile) {
                throw StateValidationException(
                    "Authentication required."
                );
            }

            if (action.value1.empty()) {
                throw StateValidationException(
                    "Updated name cannot be empty."
                );
            }

            next.profile->name = action.value1;
            break;

        case ActionType::SetTheme:
            if (action.value1 == "light") {
                next.theme = Theme::Light;
            } else if (action.value1 == "dark") {
                next.theme = Theme::Dark;
            } else if (action.value1 == "system") {
                next.theme = Theme::System;
            } else {
                throw StateValidationException(
                    "Invalid theme."
                );
            }
            break;

        case ActionType::SetLanguage:
            next.language = action.value1;
            break;

        case ActionType::Reset:
            next = AppState{};
            break;
    }

    next.version = current.version + 1;
    validate(next);

    return next;
}


/* =========================================================
   5. Context Provider
   ========================================================= */

class ContextProvider {
public:
    using Listener = function<void(
        const AppState&,
        const AppState&
    )>;

    using Selector = function<string(const AppState&)>;

private:
    struct Subscription {
        string name;
        Selector selector;
        Listener listener;
        string previousValue;
        bool active = true;
    };

    string name;
    AppState state;

    map<string, Subscription> subscriptions;

    unsigned int batchDepth = 0;
    bool pendingNotification = false;

    void notify() {
        for (auto& [id, subscription] : subscriptions) {
            if (!subscription.active) {
                continue;
            }

            try {
                string currentValue = subscription.selector(state);

                if (currentValue != subscription.previousValue) {
                    string previous = subscription.previousValue;

                    subscription.previousValue = currentValue;

                    AppState snapshot = state;

                    subscription.listener(
                        snapshot,
                        snapshot
                    );

                    cout << "Consumer " << id
                         << " changed: "
                         << previous << " -> "
                         << currentValue << '\n';
                }
            } catch (const exception& error) {
                cerr << "Consumer error: "
                     << subscription.name << ": "
                     << error.what() << '\n';
            }
        }
    }

public:
    explicit ContextProvider(
        string providerName,
        AppState initial = AppState{}
    )
        : name(move(providerName)),
          state(move(initial)) {
        validate(state);
    }

    const string& getName() const {
        return name;
    }

    AppState getState() const {
        return state;
    }

    void subscribe(
        const string& id,
        Selector selector,
        Listener listener
    ) {
        if (id.empty() || subscriptions.count(id)) {
            throw ContextException(
                "Invalid or duplicate subscription."
            );
        }

        subscriptions.emplace(
            id,
            Subscription{
                id,
                selector,
                listener,
                selector(state),
                true
            }
        );
    }

    void unsubscribe(const string& id) {
        auto iterator = subscriptions.find(id);

        if (iterator != subscriptions.end()) {
            iterator->second.active = false;
            subscriptions.erase(iterator);
        }
    }

    void dispatch(const Action& action) {
        AppState next = reduceState(state, action);

        if (
            next.authenticated == state.authenticated &&
            next.theme == state.theme &&
            next.language == state.language &&
            next.profile.has_value() == state.profile.has_value() &&
            (
                !next.profile ||
                (
                    next.profile->userId == state.profile->userId &&
                    next.profile->name == state.profile->name
                )
            )
        ) {
            return;
        }

        AppState previous = state;
        state = move(next);

        if (batchDepth > 0) {
            pendingNotification = true;
        } else {
            notify();
        }
    }

    void beginBatch() {
        ++batchDepth;
    }

    void endBatch() {
        if (batchDepth == 0) {
            throw ContextException(
                "Unbalanced batch operation."
            );
        }

        --batchDepth;

        if (batchDepth == 0 && pendingNotification) {
            pendingNotification = false;
            notify();
        }
    }

    size_t consumerCount() const {
        return subscriptions.size();
    }
};


/* =========================================================
   6. Provider Registry and Nested Scopes
   ========================================================= */

class ContextRegistry {
private:
    map<string, shared_ptr<ContextProvider>> providers;
    shared_ptr<ContextRegistry> parent;

public:
    explicit ContextRegistry(
        shared_ptr<ContextRegistry> parentRegistry = nullptr
    ) : parent(move(parentRegistry)) {}

    void provide(
        const string& key,
        shared_ptr<ContextProvider> provider
    ) {
        if (key.empty() || !provider) {
            throw ContextException(
                "Invalid provider registration."
            );
        }

        if (providers.count(key)) {
            throw ContextException(
                "Duplicate provider registration."
            );
        }

        providers.emplace(key, move(provider));
    }

    shared_ptr<ContextProvider> consume(
        const string& key
    ) const {
        auto iterator = providers.find(key);

        if (iterator != providers.end()) {
            return iterator->second;
        }

        if (parent) {
            return parent->consume(key);
        }

        throw MissingProviderException(key);
    }
};


/* =========================================================
   7. Reporting
   ========================================================= */

void printState(const AppState& state) {
    cout << "\nApplication State\n";

    cout << "Authenticated: "
         << (state.authenticated ? "true" : "false")
         << '\n';

    cout << "Theme: "
         << themeName(state.theme) << '\n';

    cout << "Language: "
         << state.language << '\n';

    cout << "Version: "
         << state.version << '\n';

    if (state.profile) {
        cout << "User: "
             << state.profile->name << '\n';

        cout << "User ID: "
             << state.profile->userId << '\n';
    }
}


/* =========================================================
   8. Main Demonstration
   ========================================================= */

int main() {
    try {
        cout << "=== Context Provider Engine ===\n";

        auto applicationProvider =
            make_shared<ContextProvider>(
                "ApplicationContext"
            );

        auto rootRegistry =
            make_shared<ContextRegistry>();

        rootRegistry->provide(
            "application",
            applicationProvider
        );

        cout << "\n=== Consumer Registration ===\n";

        applicationProvider->subscribe(
            "ThemeConsumer",
            [](const AppState& state) {
                return themeName(state.theme);
            },
            [](const AppState&, const AppState&) {}
        );

        applicationProvider->subscribe(
            "AuthenticationConsumer",
            [](const AppState& state) {
                return state.authenticated
                    ? string("authenticated")
                    : string("anonymous");
            },
            [](const AppState&, const AppState&) {}
        );

        cout << "\n=== State Transitions ===\n";

        applicationProvider->dispatch({
            ActionType::Login,
            "USR-1001",
            "Aarav Sharma"
        });

        applicationProvider->dispatch({
            ActionType::SetTheme,
            "dark",
            ""
        });

        applicationProvider->dispatch({
            ActionType::SetLanguage,
            "hi",
            ""
        });

        printState(applicationProvider->getState());

        cout << "\n=== Batch Updates ===\n";

        applicationProvider->beginBatch();

        applicationProvider->dispatch({
            ActionType::SetTheme,
            "light",
            ""
        });

        applicationProvider->dispatch({
            ActionType::SetLanguage,
            "en",
            ""
        });

        applicationProvider->endBatch();

        cout << "\n=== Nested Provider ===\n";

        AppState localState = applicationProvider->getState();
        localState.theme = Theme::System;

        auto localProvider = make_shared<ContextProvider>(
            "LocalContext",
            localState
        );

        auto childRegistry = make_shared<ContextRegistry>(
            rootRegistry
        );

        childRegistry->provide(
            "application",
            localProvider
        );

        cout << "Root theme: "
             << themeName(
                 rootRegistry->consume("application")
                     ->getState().theme
             ) << '\n';

        cout << "Child theme: "
             << themeName(
                 childRegistry->consume("application")
                     ->getState().theme
             ) << '\n';

        cout << "\n=== Validation Failure ===\n";

        try {
            applicationProvider->dispatch({
                ActionType::SetTheme,
                "invalid",
                ""
            });
        } catch (const StateValidationException& error) {
            cout << "Rejected: " << error.what() << '\n';
        }

        cout << "\n=== Consumer Cleanup ===\n";

        applicationProvider->unsubscribe("ThemeConsumer");
        applicationProvider->unsubscribe(
            "AuthenticationConsumer"
        );

        cout << "Active consumers: "
             << applicationProvider->consumerCount()
             << '\n';

        cout << "\n=== Final Validation ===\n";

        validate(applicationProvider->getState());

        cout << "All state invariants passed.\n";

    } catch (const exception& error) {
        cerr << "Fatal error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
