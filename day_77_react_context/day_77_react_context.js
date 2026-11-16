/**
 * React Context API: Providers, Consumers, and Global State
 *
 * Application-level state management using:
 * - createContext
 * - Context.Provider
 * - useContext
 * - useReducer
 * - Custom hooks
 * - Split contexts
 * - useMemo
 * - useCallback
 * - Nested providers
 * - Error boundaries
 *
 * Requires React 18 or later.
 * Save as ReactContext.jsx.
 */

import React, {
    createContext,
    useCallback,
    useContext,
    useMemo,
    useReducer,
    useState,
    useEffect
} from "react";

import { createRoot } from "react-dom/client";

import "./styles.css";


/* =========================================================
   1. Context Definitions
   ========================================================= */

const AuthContext = createContext(undefined);
const PreferencesContext = createContext(undefined);
const AppDispatchContext = createContext(undefined);

const initialState = {
    authenticated: false,
    profile: null,
    theme: "light",
    language: "en"
};


/* =========================================================
   2. Validation
   ========================================================= */

function validateUser(user) {
    if (!user || typeof user !== "object") {
        throw new Error("A valid user object is required.");
    }

    if (
        typeof user.id !== "string" ||
        !user.id.trim()
    ) {
        throw new Error("User ID is required.");
    }

    if (
        typeof user.name !== "string" ||
        !user.name.trim()
    ) {
        throw new Error("User name is required.");
    }

    return Object.freeze({
        id: user.id.trim(),
        name: user.name.trim(),
        email: String(user.email ?? "")
    });
}


/* =========================================================
   3. Reducer
   ========================================================= */

function appReducer(state, action) {
    switch (action.type) {
        case "LOGIN": {
            const profile = validateUser(action.payload);

            return {
                ...state,
                authenticated: true,
                profile
            };
        }

        case "LOGOUT":
            return {
                ...state,
                authenticated: false,
                profile: null
            };

        case "UPDATE_PROFILE": {
            if (!state.authenticated) {
                throw new Error(
                    "Authentication required for profile updates."
                );
            }

            const allowed = ["name", "email"];
            const updates = action.payload;

            if (
                !updates ||
                typeof updates !== "object" ||
                Object.keys(updates).length === 0 ||
                Object.keys(updates).some(
                    key => !allowed.includes(key)
                )
            ) {
                throw new Error("Invalid profile update.");
            }

            const profile = validateUser({
                ...state.profile,
                ...updates
            });

            return {
                ...state,
                profile
            };
        }

        case "SET_THEME": {
            const validThemes = ["light", "dark", "system"];

            if (!validThemes.includes(action.payload)) {
                throw new Error("Invalid theme.");
            }

            return {
                ...state,
                theme: action.payload
            };
        }

        case "SET_LANGUAGE": {
            const languages = ["en", "hi", "fr", "de"];

            if (!languages.includes(action.payload)) {
                throw new Error("Unsupported language.");
            }

            return {
                ...state,
                language: action.payload
            };
        }

        case "RESET":
            return initialState;

        default:
            throw new Error(
                `Unsupported action: ${action.type}`
            );
    }
}


/* =========================================================
   4. Provider
   ========================================================= */

export function AppStateProvider({ children }) {
    const [state, dispatch] = useReducer(
        appReducer,
        initialState
    );

    const authValue = useMemo(
        () => ({
            authenticated: state.authenticated,
            profile: state.profile
        }),
        [state.authenticated, state.profile]
    );

    const preferencesValue = useMemo(
        () => ({
            theme: state.theme,
            language: state.language
        }),
        [state.theme, state.language]
    );

    return (
        <AppDispatchContext.Provider value={dispatch}>
            <AuthContext.Provider value={authValue}>
                <PreferencesContext.Provider
                    value={preferencesValue}
                >
                    {children}
                </PreferencesContext.Provider>
            </AuthContext.Provider>
        </AppDispatchContext.Provider>
    );
}


/* =========================================================
   5. Custom Consumer Hooks
   ========================================================= */

function requireContext(value, name) {
    if (value === undefined) {
        throw new Error(
            `${name} must be used inside AppStateProvider.`
        );
    }

    return value;
}

export function useAuth() {
    return requireContext(
        useContext(AuthContext),
        "useAuth"
    );
}

export function usePreferences() {
    return requireContext(
        useContext(PreferencesContext),
        "usePreferences"
    );
}

export function useAppDispatch() {
    return requireContext(
        useContext(AppDispatchContext),
        "useAppDispatch"
    );
}


/* =========================================================
   6. Authentication Consumer
   ========================================================= */

function LoginPanel() {
    const auth = useAuth();
    const dispatch = useAppDispatch();

    const login = useCallback(() => {
        dispatch({
            type: "LOGIN",
            payload: {
                id: "USR-1001",
                name: "Aarav Sharma",
                email: "aarav@example.com"
            }
        });
    }, [dispatch]);

    const logout = useCallback(() => {
        dispatch({ type: "LOGOUT" });
    }, [dispatch]);

    return (
        <section>
            <h2>Authentication Context</h2>

            {auth.authenticated ? (
                <>
                    <p>
                        Signed in as {auth.profile.name}
                    </p>

                    <button onClick={logout}>
                        Logout
                    </button>
                </>
            ) : (
                <button onClick={login}>
                    Login
                </button>
            )}
        </section>
    );
}


/* =========================================================
   7. Preferences Consumer
   ========================================================= */

function PreferencesPanel() {
    const preferences = usePreferences();
    const dispatch = useAppDispatch();

    return (
        <section>
            <h2>Preferences Context</h2>

            <label>
                Theme

                <select
                    value={preferences.theme}
                    onChange={event =>
                        dispatch({
                            type: "SET_THEME",
                            payload: event.target.value
                        })
                    }
                >
                    <option value="light">Light</option>
                    <option value="dark">Dark</option>
                    <option value="system">System</option>
                </select>
            </label>

            <label>
                Language

                <select
                    value={preferences.language}
                    onChange={event =>
                        dispatch({
                            type: "SET_LANGUAGE",
                            payload: event.target.value
                        })
                    }
                >
                    <option value="en">English</option>
                    <option value="hi">Hindi</option>
                    <option value="fr">French</option>
                    <option value="de">German</option>
                </select>
            </label>
        </section>
    );
}


/* =========================================================
   8. Context Monitoring Consumer
   ========================================================= */

function Dashboard() {
    const auth = useAuth();
    const preferences = usePreferences();

    return (
        <main
            className={`dashboard ${preferences.theme}`}
        >
            <h1>Application Dashboard</h1>

            <p>
                Authentication:
                {auth.authenticated ? " Active" : " Inactive"}
            </p>

            <p>Theme: {preferences.theme}</p>
            <p>Language: {preferences.language}</p>

            {auth.profile && (
                <p>Current user: {auth.profile.name}</p>
            )}

            <LoginPanel />
            <PreferencesPanel />
        </main>
    );
}


/* =========================================================
   9. Nested Provider
   ========================================================= */

const LocalThemeContext = createContext("light");

function LocalThemeProvider({ children }) {
    const [theme, setTheme] = useState("dark");

    const value = useMemo(
        () => ({ theme, setTheme }),
        [theme]
    );

    return (
        <LocalThemeContext.Provider value={value}>
            {children}
        </LocalThemeContext.Provider>
    );
}

function LocalThemeConsumer() {
    const context = useContext(LocalThemeContext);

    return (
        <section>
            <h2>Nested Provider</h2>

            <p>Local theme: {context.theme}</p>

            <button
                onClick={() =>
                    context.setTheme(
                        context.theme === "dark"
                            ? "light"
                            : "dark"
                    )
                }
            >
                Toggle Local Theme
            </button>
        </section>
    );
}


/* =========================================================
   10. Provider Error Boundary
   ========================================================= */

class ContextErrorBoundary extends React.Component {
    constructor(props) {
        super(props);

        this.state = {
            hasError: false,
            message: ""
        };
    }

    static getDerivedStateFromError(error) {
        return {
            hasError: true,
            message: error.message
        };
    }

    componentDidCatch(error, info) {
        console.error("Context rendering error:", error, info);
    }

    render() {
        if (this.state.hasError) {
            return (
                <div role="alert">
                    <h2>Application rendering error</h2>
                    <p>{this.state.message}</p>
                </div>
            );
        }

        return this.props.children;
    }
}


/* =========================================================
   11. Complete Application
   ========================================================= */

function App() {
    return (
        <ContextErrorBoundary>
            <AppStateProvider>
                <Dashboard />

                <LocalThemeProvider>
                    <LocalThemeConsumer />
                </LocalThemeProvider>
            </AppStateProvider>
        </ContextErrorBoundary>
    );
}


/* =========================================================
   12. Mount Application
   ========================================================= */

const rootElement = document.getElementById("root");

if (!rootElement) {
    throw new Error("Missing root element.");
}

createRoot(rootElement).render(
    <React.StrictMode>
        <App />
    </React.StrictMode>
);
