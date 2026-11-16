/*
 * React Context: Enterprise Application State Management
 *
 * Java 17 implementation of provider scopes, consumers,
 * typed state transitions, validation, subscriptions,
 * state isolation, and centralized policy enforcement.
 *
 * Compile:
 * javac ReactContextEnterprise.java
 *
 * Run:
 * java ReactContextEnterprise
 */

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.function.Consumer;
import java.util.function.Function;
import java.util.stream.Collectors;


/* =========================================================
   1. Main Application
   ========================================================= */

public class ReactContextEnterprise {

    public static void main(String[] args) {

        System.out.println("=== Enterprise Context Management ===");

        ContextProvider provider = new ContextProvider(
            "ApplicationContext",
            AppState.initial()
        );

        ContextScope root = new ContextScope(null);

        root.register("application", provider);

        System.out.println("\n=== Consumer Registration ===");

        provider.subscribe(
            "ThemeConsumer",
            state -> state.theme().name(),
            (current, previous) ->
                System.out.println(
                    "Theme changed: "
                    + previous.theme()
                    + " -> "
                    + current.theme()
                )
        );

        provider.subscribe(
            "AuthenticationConsumer",
            AppState::authenticated,
            (current, previous) ->
                System.out.println(
                    "Authentication changed: "
                    + previous.authenticated()
                    + " -> "
                    + current.authenticated()
                )
        );

        System.out.println("\n=== User Authentication ===");

        provider.dispatch(new Action(
            ActionType.LOGIN,
            Map.of(
                "userId", "USR-1001",
                "name", "Aarav Sharma",
                "email", "aarav@example.com"
            )
        ));

        System.out.println("\n=== Preferences Update ===");

        provider.dispatch(new Action(
            ActionType.SET_THEME,
            Map.of("theme", "DARK")
        ));

        provider.dispatch(new Action(
            ActionType.SET_LANGUAGE,
            Map.of("language", "hi")
        ));

        printState(provider.getState());

        System.out.println("\n=== Profile Update ===");

        provider.dispatch(new Action(
            ActionType.UPDATE_PROFILE,
            Map.of("name", "Aarav Kumar")
        ));

        System.out.println("\n=== Nested Context ===");

        ContextProvider localProvider = new ContextProvider(
            "LocalThemeContext",
            provider.getState().withTheme(Theme.SYSTEM)
        );

        ContextScope child = new ContextScope(root);

        child.register("application", localProvider);

        System.out.println(
            "Root theme: "
            + root.resolve("application").getState().theme()
        );

        System.out.println(
            "Child theme: "
            + child.resolve("application").getState().theme()
        );

        System.out.println("\n=== Policy Validation ===");

        try {
            provider.dispatch(new Action(
                ActionType.SET_THEME,
                Map.of("theme", "INVALID")
            ));
        } catch (ContextException error) {
            System.out.println(
                "Rejected: " + error.getMessage()
            );
        }

        System.out.println("\n=== State Isolation ===");

        ContextProvider secondProvider = new ContextProvider(
            "IndependentContext",
            AppState.initial()
        );

        secondProvider.dispatch(new Action(
            ActionType.SET_THEME,
            Map.of("theme", "DARK")
        ));

        System.out.println(
            "Application theme: "
            + provider.getState().theme()
        );

        System.out.println(
            "Independent theme: "
            + secondProvider.getState().theme()
        );

        System.out.println("\n=== Cleanup ===");

        provider.unsubscribe("ThemeConsumer");
        provider.unsubscribe("AuthenticationConsumer");

        System.out.println(
            "Active subscriptions: "
            + provider.consumerCount()
        );

        System.out.println("\nAll assertions passed.");

        assert provider.getState().authenticated();
        assert provider.getState().profile().isPresent();
        assert provider.getState().language().equals("hi");
        assert secondProvider.getState().theme() == Theme.DARK;
        assert provider.consumerCount() == 0;
    }

    private static void printState(AppState state) {
        System.out.println("Authenticated: " + state.authenticated());
        System.out.println("Theme: " + state.theme());
        System.out.println("Language: " + state.language());
        System.out.println("Version: " + state.version());

        state.profile().ifPresent(profile -> {
            System.out.println("User ID: " + profile.userId());
            System.out.println("Name: " + profile.name());
        });
    }
}


/* =========================================================
   2. Domain Types
   ========================================================= */

enum Theme {
    LIGHT,
    DARK,
    SYSTEM
}

enum ActionType {
    LOGIN,
    LOGOUT,
    UPDATE_PROFILE,
    SET_THEME,
    SET_LANGUAGE,
    RESET
}

record Profile(
    String userId,
    String name,
    String email
) {
    Profile {
        userId = Objects.requireNonNull(userId).trim();
        name = Objects.requireNonNull(name).trim();
        email = Objects.requireNonNull(email).trim();

        if (userId.isEmpty() || name.isEmpty()) {
            throw new ContextException(
                "Profile identity and name are required."
            );
        }
    }
}

record Action(
    ActionType type,
    Map<String, String> payload
) {
    Action {
        Objects.requireNonNull(type);
        Objects.requireNonNull(payload);

        payload = Map.copyOf(payload);
    }
}


/* =========================================================
   3. Exceptions
   ========================================================= */

class ContextException extends RuntimeException {

    ContextException(String message) {
        super(message);
    }
}


/* =========================================================
   4. Immutable Application State
   ========================================================= */

record AppState(
    boolean authenticated,
    Optional<Profile> profile,
    Theme theme,
    String language,
    long version
) {

    AppState {
        Objects.requireNonNull(profile);
        Objects.requireNonNull(theme);
        Objects.requireNonNull(language);

        validate();
    }

    static AppState initial() {
        return new AppState(
            false,
            Optional.empty(),
            Theme.LIGHT,
            "en",
            0
        );
    }

    void validate() {

        if (authenticated != profile.isPresent()) {
            throw new ContextException(
                "Authentication and profile state conflict."
            );
        }

        Set<String> languages = Set.of(
            "en", "hi", "fr", "de"
        );

        if (!languages.contains(language)) {
            throw new ContextException(
                "Unsupported language."
            );
        }
    }

    AppState withTheme(Theme newTheme) {
        return new AppState(
            authenticated,
            profile,
            newTheme,
            language,
            version + 1
        );
    }
}


/* =========================================================
   5. Reducer Service
   ========================================================= */

final class StateReducer {

    private StateReducer() {}

    static AppState apply(
        AppState current,
        Action action
    ) {

        Map<String, String> payload = action.payload();

        return switch (action.type()) {

            case LOGIN -> {

                String id = required(payload, "userId");
                String name = required(payload, "name");

                String email = payload.getOrDefault(
                    "email", ""
                );

                Profile profile = new Profile(
                    id, name, email
                );

                yield new AppState(
                    true,
                    Optional.of(profile),
                    current.theme(),
                    current.language(),
                    current.version() + 1
                );
            }

            case LOGOUT -> new AppState(
                false,
                Optional.empty(),
                current.theme(),
                current.language(),
                current.version() + 1
            );

            case UPDATE_PROFILE -> {

                if (!current.authenticated()) {
                    throw new ContextException(
                        "Authentication required."
                    );
                }

                Set<String> allowed = Set.of(
                    "name", "email"
                );

                if (
                    payload.isEmpty() ||
                    !allowed.containsAll(payload.keySet())
                ) {
                    throw new ContextException(
                        "Invalid profile fields."
                    );
                }

                Profile old = current.profile().orElseThrow();

                Profile updated = new Profile(
                    old.userId(),
                    payload.getOrDefault("name", old.name()),
                    payload.getOrDefault("email", old.email())
                );

                yield new AppState(
                    true,
                    Optional.of(updated),
                    current.theme(),
                    current.language(),
                    current.version() + 1
                );
            }

            case SET_THEME -> {

                Theme theme;

                try {
                    theme = Theme.valueOf(
                        required(payload, "theme").toUpperCase()
                    );
                } catch (IllegalArgumentException error) {
                    throw new ContextException(
                        "Unsupported theme."
                    );
                }

                yield new AppState(
                    current.authenticated(),
                    current.profile(),
                    theme,
                    current.language(),
                    current.version() + 1
                );
            }

            case SET_LANGUAGE -> new AppState(
                current.authenticated(),
                current.profile(),
                current.theme(),
                required(payload, "language"),
                current.version() + 1
            );

            case RESET -> AppState.initial();
        };
    }

    private static String required(
        Map<String, String> payload,
        String key
    ) {
        String value = payload.get(key);

        if (value == null || value.isBlank()) {
            throw new ContextException(
                "Missing required field: " + key
            );
        }

        return value.trim();
    }
}


/* =========================================================
   6. Consumer Contract
   ========================================================= */

interface ContextListener {
    void onChange(AppState current, AppState previous);
}


/* =========================================================
   7. Provider Service
   ========================================================= */

final class ContextProvider {

    private record Subscription<T>(
        Function<AppState, T> selector,
        ContextListener listener,
        T previousValue
    ) {}

    private final String name;

    private AppState state;

    private final Map<String, Subscription<?>> subscriptions =
        new HashMap<>();

    ContextProvider(
        String name,
        AppState initialState
    ) {
        this.name = Objects.requireNonNull(name);
        this.state = Objects.requireNonNull(initialState);
    }

    synchronized String getName() {
        return name;
    }

    synchronized AppState getState() {
        return state;
    }

    synchronized int consumerCount() {
        return subscriptions.size();
    }

    synchronized <T> void subscribe(
        String consumerId,
        Function<AppState, T> selector,
        ContextListener listener
    ) {

        if (
            consumerId == null ||
            consumerId.isBlank() ||
            subscriptions.containsKey(consumerId)
        ) {
            throw new ContextException(
                "Invalid or duplicate consumer."
            );
        }

        T initialValue = selector.apply(state);

        subscriptions.put(
            consumerId,
            new Subscription<>(
                selector,
                listener,
                initialValue
            )
        );
    }

    synchronized void unsubscribe(String consumerId) {
        subscriptions.remove(consumerId);
    }

    synchronized void dispatch(Action action) {

        AppState previous = state;

        AppState next = StateReducer.apply(
            previous,
            action
        );

        state = next;

        notifyConsumers(previous, next);
    }

    private void notifyConsumers(
        AppState previous,
        AppState current
    ) {

        List<String> remove = new ArrayList<>();

        subscriptions.forEach((id, raw) -> {
            notifyOne(id, raw, previous, current);
        });

        remove.forEach(subscriptions::remove);
    }

    private <T> void notifyOne(
        String id,
        Subscription<T> subscription,
        AppState previous,
        AppState current
    ) {

        T oldValue = subscription.previousValue();
        T newValue;

        try {
            newValue = subscription.selector().apply(current);

            if (!Objects.equals(oldValue, newValue)) {
                subscription.listener().onChange(
                    current,
                    previous
                );

                subscriptions.put(
                    id,
                    new Subscription<>(
                        subscription.selector(),
                        subscription.listener(),
                        newValue
                    )
                );
            }

        } catch (Exception error) {
            System.err.println(
                "Consumer notification failed: "
                + id + ": " + error.getMessage()
            );
        }
    }
}


/* =========================================================
   8. Nested Provider Scope
   ========================================================= */

final class ContextScope {

    private final ContextScope parent;

    private final Map<String, ContextProvider> providers =
        new HashMap<>();

    ContextScope(ContextScope parent) {
        this.parent = parent;
    }

    void register(
        String key,
        ContextProvider provider
    ) {

        if (
            key == null ||
            key.isBlank() ||
            provider == null
        ) {
            throw new ContextException(
                "Invalid provider registration."
            );
        }

        if (providers.putIfAbsent(key, provider) != null) {
            throw new ContextException(
                "Duplicate provider: " + key
            );
        }
    }

    ContextProvider resolve(String key) {

        ContextProvider provider = providers.get(key);

        if (provider != null) {
            return provider;
        }

        if (parent != null) {
            return parent.resolve(key);
        }

        throw new ContextException(
            "No provider available for: " + key
        );
    }
}
