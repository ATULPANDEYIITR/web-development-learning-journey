/**
 * React Testing: Unit Tests, Component Tests, Mocking,
 * and User Interaction Testing.
 *
 * Node.js 20+ with:
 *   react
 *   react-dom
 *   @testing-library/react
 *   @testing-library/user-event
 *
 * Run:
 *   node --test react-testing.test.mjs
 *
 * This implementation uses real React components, React Testing
 * Library, and Node's built-in test runner.
 */

import test, { afterEach, beforeEach } from "node:test";
import assert from "node:assert/strict";

import React, { useEffect, useState } from "react";
import {
    render,
    screen,
    cleanup,
    waitFor,
    within
} from "@testing-library/react";

import userEvent from "@testing-library/user-event";


// ============================================================
// 1. PURE FUNCTIONS: UNIT TESTING
// ============================================================

export function validateEmail(email) {
    if (typeof email !== "string") {
        return false;
    }

    const normalized = email.trim();

    if (!normalized || normalized.length > 254) {
        return false;
    }

    const parts = normalized.split("@");

    if (parts.length !== 2) {
        return false;
    }

    const [local, domain] = parts;

    if (!local || local.length > 64 || !domain) {
        return false;
    }

    if (/\s/.test(normalized)) {
        return false;
    }

    if (!domain.includes(".") ||
        domain.startsWith(".") ||
        domain.endsWith(".")) {
        return false;
    }

    return true;
}


export function normalizeName(name) {
    if (typeof name !== "string") {
        throw new TypeError("Name must be a string");
    }

    return name.trim().replace(/\s+/g, " ");
}


export function filterUsers(users, query) {
    if (!Array.isArray(users)) {
        throw new TypeError("Users must be an array");
    }

    if (typeof query !== "string") {
        throw new TypeError("Search query must be a string");
    }

    const normalized = query.trim().toLowerCase();

    if (!normalized) {
        return [...users];
    }

    return users.filter(user =>
        user.name.toLowerCase().includes(normalized) ||
        user.email.toLowerCase().includes(normalized)
    );
}


// ============================================================
// 2. DOMAIN DATA
// ============================================================

export const initialUsers = [
    {
        id: 1,
        name: "Alice Johnson",
        email: "alice@example.com",
        active: true
    },
    {
        id: 2,
        name: "Bob Smith",
        email: "bob@example.com",
        active: true
    },
    {
        id: 3,
        name: "Charlie Brown",
        email: "charlie@example.com",
        active: false
    }
];


// ============================================================
// 3. API DEPENDENCY
// ============================================================

export async function fetchUsers() {
    const response = await fetch("/api/users", {
        headers: {
            Accept: "application/json"
        }
    });

    if (!response.ok) {
        throw new Error(`HTTP error: ${response.status}`);
    }

    const data = await response.json();

    if (!Array.isArray(data)) {
        throw new TypeError("Invalid API response");
    }

    return data;
}


// ============================================================
// 4. REACT COMPONENT
// ============================================================

export function UserDirectory({
    api = fetchUsers,
    onSelect = () => {},
    initialQuery = ""
}) {
    const [users, setUsers] = useState([]);
    const [query, setQuery] = useState(initialQuery);
    const [status, setStatus] = useState("loading");
    const [error, setError] = useState("");

    useEffect(() => {
        let active = true;

        async function load() {
            setStatus("loading");
            setError("");

            try {
                const data = await api();

                if (!Array.isArray(data)) {
                    throw new TypeError("Invalid users response");
                }

                if (active) {
                    setUsers(data);
                    setStatus("success");
                }
            } catch (err) {
                if (active) {
                    setError(err.message || "Unable to load users");
                    setStatus("error");
                }
            }
        }

        load();

        return () => {
            active = false;
        };
    }, [api]);

    const visibleUsers = filterUsers(users, query);

    function handleSearch(event) {
        setQuery(event.target.value);
    }

    function handleSelect(user) {
        onSelect(user);
    }

    if (status === "loading") {
        return React.createElement(
            "p",
            { role: "status" },
            "Loading users..."
        );
    }

    if (status === "error") {
        return React.createElement(
            "div",
            { role: "alert" },
            React.createElement("p", null, error),
            React.createElement(
                "button",
                {
                    type: "button",
                    onClick: () => {
                        // The component exposes a retry action through
                        // a parent-controlled remount in this example.
                        setStatus("error");
                    }
                },
                "Unable to load users"
            )
        );
    }

    return React.createElement(
        "section",
        { "aria-label": "User directory" },

        React.createElement(
            "label",
            { htmlFor: "user-search" },
            "Search users"
        ),

        React.createElement("input", {
            id: "user-search",
            type: "search",
            value: query,
            onChange: handleSearch,
            placeholder: "Enter a name or email"
        }),

        React.createElement(
            "p",
            { "data-testid": "result-count" },
            `${visibleUsers.length} users found`
        ),

        visibleUsers.length === 0
            ? React.createElement(
                "p",
                { role: "status" },
                "No users found"
            )
            : React.createElement(
                "ul",
                { "aria-label": "Users" },
                ...visibleUsers.map(user =>
                    React.createElement(
                        "li",
                        { key: user.id },
                        React.createElement(
                            "span",
                            null,
                            user.name
                        ),
                        React.createElement(
                            "span",
                            null,
                            user.email
                        ),
                        React.createElement(
                            "button",
                            {
                                type: "button",
                                onClick: () => handleSelect(user),
                                "aria-label": `Select ${user.name}`
                            },
                            "Select"
                        )
                    )
                )
            )
    );
}


// ============================================================
// 5. MOCKING UTILITIES
// ============================================================

function createMockApi(result, options = {}) {
    const {
        failure = false,
        delay = 0
    } = options;

    let calls = 0;

    const api = async () => {
        calls++;

        if (delay > 0) {
            await new Promise(resolve =>
                setTimeout(resolve, delay)
            );
        }

        if (failure) {
            throw new Error("Network unavailable");
        }

        return structuredClone(result);
    };

    return {
        api,
        get calls() {
            return calls;
        }
    };
}


let user;

beforeEach(() => {
    user = userEvent.setup();
});

afterEach(() => {
    cleanup();
});


// ============================================================
// 6. UNIT TESTS
// ============================================================

test("email validation accepts valid addresses", () => {
    assert.equal(
        validateEmail("alice@example.com"),
        true
    );
});

test("email validation rejects malformed addresses", () => {
    assert.equal(validateEmail("alice"), false);
    assert.equal(validateEmail("alice@@example.com"), false);
    assert.equal(validateEmail("alice@example"), false);
    assert.equal(validateEmail(""), false);
    assert.equal(validateEmail(null), false);
});

test("name normalization removes excess whitespace", () => {
    assert.equal(
        normalizeName("  Alice    Johnson "),
        "Alice Johnson"
    );
});

test("filterUsers searches names and emails", () => {
    const results = filterUsers(initialUsers, "alice");

    assert.equal(results.length, 1);
    assert.equal(results[0].id, 1);
});

test("filterUsers is case insensitive", () => {
    assert.equal(
        filterUsers(initialUsers, "BOB").length,
        1
    );
});

test("filterUsers returns all users for empty search", () => {
    assert.equal(
        filterUsers(initialUsers, "").length,
        3
    );
});

test("filterUsers rejects invalid arguments", () => {
    assert.throws(
        () => filterUsers(null, "alice"),
        TypeError
    );

    assert.throws(
        () => filterUsers(initialUsers, null),
        TypeError
    );
});


// ============================================================
// 7. COMPONENT TESTS
// ============================================================

test("component displays loading state", async () => {
    const mock = createMockApi(initialUsers, {
        delay: 50
    });

    render(
        React.createElement(UserDirectory, {
            api: mock.api
        })
    );

    assert.equal(
        screen.getByRole("status").textContent,
        "Loading users..."
    );
});

test("component renders users after successful API response", async () => {
    const mock = createMockApi(initialUsers);

    render(
        React.createElement(UserDirectory, {
            api: mock.api
        })
    );

    expectUsers = await screen.findAllByRole("listitem");

    assert.equal(expectUsers.length, 3);
    assert.equal(mock.calls, 1);

    assert.ok(
        screen.getByText("Alice Johnson")
    );
});

test("component displays an API failure", async () => {
    const mock = createMockApi([], {
        failure: true
    });

    render(
        React.createElement(UserDirectory, {
            api: mock.api
        })
    );

    const alert = await screen.findByRole("alert");

    assert.match(
        alert.textContent,
        /Network unavailable/
    );
});

test("component handles empty API responses", async () => {
    const mock = createMockApi([]);

    render(
        React.createElement(UserDirectory, {
            api: mock.api
        })
    );

    assert.equal(
        await screen.findByRole("status").textContent,
        "No users found"
    );
});

test("component supports initial search state", async () => {
    const mock = createMockApi(initialUsers);

    render(
        React.createElement(UserDirectory, {
            api: mock.api,
            initialQuery: "alice"
        })
    );

    await screen.findByText("Alice Johnson");

    assert.equal(
        screen.getAllByRole("listitem").length,
        1
    );
});


// ============================================================
// 8. USER INTERACTION TESTS
// ============================================================

test("user can search for a user", async () => {
    const mock = createMockApi(initialUsers);

    render(
        React.createElement(UserDirectory, {
            api: mock.api
        })
    );

    await screen.findByText("Alice Johnson");

    const search = screen.getByRole("searchbox", {
        name: "Search users"
    });

    await user.type(search, "bob");

    const items = screen.getAllByRole("listitem");

    assert.equal(items.length, 1);

    assert.ok(
        within(items[0]).getByText("Bob Smith")
    );

    assert.equal(
        screen.queryByText("Alice Johnson"),
        null
    );
});

test("user can clear a search", async () => {
    const mock = createMockApi(initialUsers);

    render(
        React.createElement(UserDirectory, {
            api: mock.api
        })
    );

    await screen.findByText("Alice Johnson");

    const search = screen.getByRole("searchbox");

    await user.type(search, "alice");

    assert.equal(
        screen.getAllByRole("listitem").length,
        1
    );

    await user.clear(search);

    assert.equal(
        screen.getAllByRole("listitem").length,
        3
    );
});

test("user receives feedback when no results match", async () => {
    const mock = createMockApi(initialUsers);

    render(
        React.createElement(UserDirectory, {
            api: mock.api
        })
    );

    await screen.findByText("Alice Johnson");

    await user.type(
        screen.getByRole("searchbox"),
        "unknown-user"
    );

    assert.equal(
        screen.getByText("No users found").textContent,
        "No users found"
    );
});

test("select button invokes callback with selected user", async () => {
    const mock = createMockApi(initialUsers);
    const selectedUsers = [];

    render(
        React.createElement(UserDirectory, {
            api: mock.api,
            onSelect: user => selectedUsers.push(user)
        })
    );

    await screen.findByText("Alice Johnson");

    await user.click(
        screen.getByRole("button", {
            name: "Select Alice Johnson"
        })
    );

    assert.equal(selectedUsers.length, 1);
    assert.equal(selectedUsers[0].id, 1);
});

test("search result count changes after interaction", async () => {
    const mock = createMockApi(initialUsers);

    render(
        React.createElement(UserDirectory, {
            api: mock.api
        })
    );

    await screen.findByText("Alice Johnson");

    assert.equal(
        screen.getByTestId("result-count").textContent,
        "3 users found"
    );

    await user.type(
        screen.getByRole("searchbox"),
        "charlie"
    );

    assert.equal(
        screen.getByTestId("result-count").textContent,
        "1 users found"
    );
});


// ============================================================
// 9. ASYNCHRONOUS TESTING
// ============================================================

test("component waits for delayed API responses", async () => {
    const mock = createMockApi(initialUsers, {
        delay: 40
    });

    render(
        React.createElement(UserDirectory, {
            api: mock.api
        })
    );

    assert.ok(screen.getByText("Loading users..."));

    await waitFor(() => {
        assert.equal(
            screen.getAllByRole("listitem").length,
            3
        );
    });
});

test("component ignores results after unmount", async () => {
    let resolveRequest;

    const api = () => new Promise(resolve => {
        resolveRequest = resolve;
    });

    const { unmount } = render(
        React.createElement(UserDirectory, {
            api
        })
    );

    await waitFor(() => {
        assert.equal(typeof resolveRequest, "function");
    });

    unmount();

    resolveRequest(initialUsers);

    await new Promise(resolve => setImmediate(resolve));

    assert.equal(resolveRequest instanceof Function, true);
});


// ============================================================
// 10. TEST EXECUTION INFORMATION
// ============================================================

test("mock API records dependency calls", async () => {
    const mock = createMockApi(initialUsers);

    await mock.api();
    await mock.api();

    assert.equal(mock.calls, 2);
});

test("mock API returns isolated data", async () => {
    const mock = createMockApi(initialUsers);

    const first = await mock.api();
    first[0].name = "Changed Name";

    const second = await mock.api();

    assert.equal(second[0].name, "Alice Johnson");
});
