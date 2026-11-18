"use strict";

/*
 * React Data Fetching: Event-driven API Client
 *
 * Features:
 * - Fetch API integration
 * - Request deduplication
 * - AbortController cancellation
 * - Loading and error states
 * - Retry policies
 * - Memory caching
 * - Stale-while-revalidate behavior
 * - Cache invalidation
 * - Observable state changes
 * - Optional React hook adapter
 *
 * Runtime: Node.js 18+ or modern browsers.
 */

const { setTimeout: delay } = require("node:timers/promises");

// -------------------------------------------------------
// 1. Custom errors
// -------------------------------------------------------

class FetchError extends Error {
    constructor(message, status = null, code = "FETCH_ERROR") {
        super(message);
        this.name = "FetchError";
        this.status = status;
        this.code = code;
    }
}

class RequestCancelledError extends FetchError {
    constructor() {
        super("Request was cancelled.", null, "CANCELLED");
        this.name = "RequestCancelledError";
    }
}

// -------------------------------------------------------
// 2. Request state
// -------------------------------------------------------

function createInitialState() {
    return {
        status: "idle",
        data: undefined,
        error: null,
        isLoading: false,
        isFetching: false,
        updatedAt: null,
        requestId: 0
    };
}

// -------------------------------------------------------
// 3. Query key generation
// -------------------------------------------------------

function stableSerialize(value) {
    if (value === null || typeof value !== "object") {
        return JSON.stringify(value);
    }

    if (Array.isArray(value)) {
        return `[${value.map(stableSerialize).join(",")}]`;
    }

    const keys = Object.keys(value).sort();

    return `{${keys.map(key =>
        `${JSON.stringify(key)}:${stableSerialize(value[key])}`
    ).join(",")}}`;
}

// -------------------------------------------------------
// 4. Query cache
// -------------------------------------------------------

class QueryCache {
    constructor({
        staleTime = 30000,
        maxEntries = 100
    } = {}) {
        if (staleTime < 0 || maxEntries < 1) {
            throw new Error("Invalid cache configuration.");
        }

        this.staleTime = staleTime;
        this.maxEntries = maxEntries;
        this.entries = new Map();
    }

    get(key) {
        const entry = this.entries.get(key);

        if (!entry) return null;

        // Refresh insertion order for LRU eviction.
        this.entries.delete(key);
        this.entries.set(key, entry);

        return {
            data: entry.data,
            isStale: Date.now() - entry.updatedAt > this.staleTime,
            updatedAt: entry.updatedAt
        };
    }

    set(key, data) {
        this.entries.delete(key);

        this.entries.set(key, {
            data,
            updatedAt: Date.now()
        });

        while (this.entries.size > this.maxEntries) {
            const oldestKey = this.entries.keys().next().value;
            this.entries.delete(oldestKey);
        }
    }

    invalidate(key) {
        if (key === undefined) {
            this.entries.clear();
        } else {
            this.entries.delete(key);
        }
    }
}

// -------------------------------------------------------
// 5. HTTP API client
// -------------------------------------------------------

class APIClient {
    constructor({
        baseURL,
        defaultHeaders = {},
        timeout = 10000,
        fetchImplementation = globalThis.fetch
    }) {
        if (!baseURL || !/^https?:\/\//i.test(baseURL)) {
            throw new Error("A valid HTTP baseURL is required.");
        }

        if (typeof fetchImplementation !== "function") {
            throw new Error("Fetch API is unavailable.");
        }

        this.baseURL = baseURL.replace(/\/+$/, "");
        this.defaultHeaders = defaultHeaders;
        this.timeout = timeout;
        this.fetchImplementation = fetchImplementation;
    }

    async request(path, options = {}) {
        const {
            method = "GET",
            params = {},
            body,
            headers = {},
            signal
        } = options;

        if (typeof path !== "string" || !path.startsWith("/")) {
            throw new Error("API path must begin with /.");
        }

        const url = new URL(this.baseURL + path);

        for (const [key, value] of Object.entries(params)) {
            if (value !== undefined && value !== null) {
                url.searchParams.set(key, String(value));
            }
        }

        const controller = new AbortController();

        const abort = () => controller.abort();

        if (signal) {
            if (signal.aborted) {
                throw new RequestCancelledError();
            }

            signal.addEventListener("abort", abort, { once: true });
        }

        const timeoutId = setTimeout(
            () => controller.abort(),
            this.timeout
        );

        try {
            const response = await this.fetchImplementation(url, {
                method,
                headers: {
                    Accept: "application/json",
                    ...this.defaultHeaders,
                    ...headers,
                    ...(body !== undefined
                        ? { "Content-Type": "application/json" }
                        : {})
                },
                body: body === undefined
                    ? undefined
                    : JSON.stringify(body),
                signal: controller.signal
            });

            if (!response.ok) {
                throw new FetchError(
                    `HTTP ${response.status}: ${response.statusText}`,
                    response.status,
                    "HTTP_ERROR"
                );
            }

            if (response.status === 204) {
                return null;
            }

            const contentType =
                response.headers.get("content-type") || "";

            if (!contentType.includes("application/json")) {
                throw new FetchError(
                    "Expected a JSON response.",
                    response.status,
                    "INVALID_CONTENT_TYPE"
                );
            }

            try {
                return await response.json();
            } catch (error) {
                throw new FetchError(
                    "The server returned invalid JSON.",
                    response.status,
                    "INVALID_JSON"
                );
            }
        } catch (error) {
            if (controller.signal.aborted) {
                throw new RequestCancelledError();
            }

            if (error instanceof FetchError) {
                throw error;
            }

            throw new FetchError(
                error.message || "Network request failed.",
                null,
                "NETWORK_ERROR"
            );
        } finally {
            clearTimeout(timeoutId);

            if (signal) {
                signal.removeEventListener("abort", abort);
            }
        }
    }
}

// -------------------------------------------------------
// 6. Query manager
// -------------------------------------------------------

class QueryManager {
    constructor(apiClient, cache = new QueryCache()) {
        this.api = apiClient;
        this.cache = cache;
        this.queries = new Map();
        this.listeners = new Map();
        this.inFlight = new Map();
        this.controllers = new Map();
    }

    key(path, params = {}) {
        return stableSerialize({ path, params });
    }

    getState(key) {
        if (!this.queries.has(key)) {
            this.queries.set(key, createInitialState());
        }

        return this.queries.get(key);
    }

    subscribe(key, listener) {
        if (!this.listeners.has(key)) {
            this.listeners.set(key, new Set());
        }

        this.listeners.get(key).add(listener);

        return () => {
            this.listeners.get(key)?.delete(listener);
        };
    }

    publish(key, changes) {
        const previous = this.getState(key);

        const next = {
            ...previous,
            ...changes
        };

        this.queries.set(key, next);

        for (const listener of this.listeners.get(key) || []) {
            try {
                listener(next);
            } catch (error) {
                console.error("State listener failed:", error);
            }
        }

        return next;
    }

    async fetch(path, {
        params = {},
        force = false,
        retries = 2,
        retryDelay = 250,
        signal
    } = {}) {
        if (!Number.isInteger(retries) || retries < 0) {
            throw new Error("Retries must be a non-negative integer.");
        }

        const key = this.key(path, params);

        const cached = this.cache.get(key);

        if (cached && !force && !cached.isStale) {
            this.publish(key, {
                status: "success",
                data: cached.data,
                error: null,
                isLoading: false,
                isFetching: false,
                updatedAt: cached.updatedAt
            });

            return cached.data;
        }

        // Multiple consumers share one network request.
        if (this.inFlight.has(key)) {
            return this.inFlight.get(key);
        }

        const requestId = this.getState(key).requestId + 1;
        const controller = new AbortController();

        this.controllers.set(key, controller);

        const existingData = cached?.data;

        this.publish(key, {
            status: existingData === undefined ? "loading" : "success",
            data: existingData,
            error: null,
            isLoading: existingData === undefined,
            isFetching: true,
            requestId
        });

        const execute = async () => {
            let lastError;

            for (let attempt = 0; attempt <= retries; attempt++) {
                if (controller.signal.aborted) {
                    throw new RequestCancelledError();
                }

                try {
                    const data = await this.api.request(path, {
                        params,
                        signal: controller.signal
                    });

                    this.cache.set(key, data);

                    this.publish(key, {
                        status: "success",
                        data,
                        error: null,
                        isLoading: false,
                        isFetching: false,
                        updatedAt: Date.now()
                    });

                    return data;
                } catch (error) {
                    lastError = error;

                    if (
                        error instanceof RequestCancelledError ||
                        error.code === "CANCELLED"
                    ) {
                        throw error;
                    }

                    const permanentClientError =
                        error.status >= 400 &&
                        error.status < 500 &&
                        error.status !== 429;

                    if (
                        permanentClientError ||
                        attempt === retries
                    ) {
                        break;
                    }

                    await delay(
                        retryDelay * (2 ** attempt),
                        undefined,
                        { signal: controller.signal }
                    );
                }
            }

            throw lastError;
        };

        const task = execute()
            .catch(error => {
                if (error.code === "CANCELLED") {
                    this.publish(key, {
                        status: existingData === undefined
                            ? "idle"
                            : "success",
                        error: null,
                        isLoading: false,
                        isFetching: false
                    });
                } else {
                    this.publish(key, {
                        status: "error",
                        error: error.message,
                        isLoading: false,
                        isFetching: false
                    });
                }

                throw error;
            })
            .finally(() => {
                if (this.inFlight.get(key) === task) {
                    this.inFlight.delete(key);
                }

                if (this.controllers.get(key) === controller) {
                    this.controllers.delete(key);
                }
            });

        this.inFlight.set(key, task);

        return task;
    }

    cancel(path, params = {}) {
        const key = this.key(path, params);
        this.controllers.get(key)?.abort();
    }

    invalidate(path, params = {}) {
        const key = this.key(path, params);
        this.cache.invalidate(key);
    }

    clear() {
        this.cache.invalidate();
    }
}

// -------------------------------------------------------
// 7. React integration adapter
// -------------------------------------------------------

/*
 * Pass the React namespace to createReactHooks.
 *
 * This keeps the core implementation independent of React.
 * The adapter uses useState, useEffect, and useCallback.
 *
 * Example:
 *
 * const { useQuery } = createReactHooks(React, manager);
 *
 * function Users() {
 *     const query = useQuery("/users");
 *
 *     if (query.isLoading) return <p>Loading...</p>;
 *     if (query.error) return <p>{query.error}</p>;
 *
 *     return query.data.map(user =>
 *         <p key={user.id}>{user.name}</p>
 *     );
 * }
 */

function createReactHooks(React, manager) {
    if (
        !React ||
        typeof React.useState !== "function" ||
        typeof React.useEffect !== "function"
    ) {
        throw new Error("A valid React namespace is required.");
    }

    function useQuery(path, options = {}) {
        const {
            params = {},
            enabled = true,
            refetchOnMount = true
        } = options;

        const paramsKey = stableSerialize(params);
        const key = manager.key(path, params);

        const [state, setState] = React.useState(
            () => manager.getState(key)
        );

        const refetch = React.useCallback(() => {
            return manager.fetch(path, {
                params,
                force: true
            });
        }, [path, paramsKey]);

        React.useEffect(() => {
            if (!enabled) return undefined;

            let active = true;

            setState(manager.getState(key));

            const unsubscribe = manager.subscribe(
                key,
                nextState => {
                    if (active) setState({ ...nextState });
                }
            );

            if (refetchOnMount) {
                manager.fetch(path, { params })
                    .catch(() => {
                        // Error state is already published.
                    });
            }

            return () => {
                active = false;
                unsubscribe();
            };
        }, [key, enabled, refetchOnMount]);

        return {
            ...state,
            refetch
        };
    }

    return { useQuery };
}

// -------------------------------------------------------
// 8. Demonstration with a simulated API
// -------------------------------------------------------

async function demonstration() {
    let requestCount = 0;

    const mockFetch = async (url, options) => {
        requestCount++;

        if (options.signal?.aborted) {
            throw new Error("Request aborted.");
        }

        await delay(30);

        if (url.pathname === "/users") {
            return {
                ok: true,
                status: 200,
                statusText: "OK",
                headers: new Headers({
                    "content-type": "application/json"
                }),
                json: async () => [
                    { id: 1, name: "Aarav" },
                    { id: 2, name: "Meera" }
                ]
            };
        }

        if (url.pathname === "/empty") {
            return {
                ok: true,
                status: 200,
                statusText: "OK",
                headers: new Headers({
                    "content-type": "application/json"
                }),
                json: async () => []
            };
        }

        return {
            ok: false,
            status: 404,
            statusText: "Not Found",
            headers: new Headers(),
            json: async () => ({})
        };
    };

    const api = new APIClient({
        baseURL: "https://example.test",
        fetchImplementation: mockFetch
    });

    const manager = new QueryManager(
        api,
        new QueryCache({
            staleTime: 10000,
            maxEntries: 50
        })
    );

    const usersKey = manager.key("/users");

    manager.subscribe(usersKey, state => {
        console.log(
            "State:",
            state.status,
            "| Loading:",
            state.isLoading,
            "| Fetching:",
            state.isFetching
        );
    });

    console.log("\n1. Fetch users");

    const users = await manager.fetch("/users");

    console.log("Users:", users);

    console.log("\n2. Read cached users");

    const cached = await manager.fetch("/users");

    console.log("Cached records:", cached.length);
    console.log("Network calls:", requestCount);

    console.log("\n3. Concurrent request deduplication");

    manager.invalidate("/users");

    const [first, second] = await Promise.all([
        manager.fetch("/users"),
        manager.fetch("/users")
    ]);

    console.log("Identical results:", first === second);
    console.log("Network calls:", requestCount);

    console.log("\n4. Empty API response");

    const empty = await manager.fetch("/empty");

    console.log("Empty data:", empty);
    console.log("Is an empty response an error:", false);

    console.log("\n5. HTTP error");

    try {
        await manager.fetch("/missing", { retries: 0 });
    } catch (error) {
        console.log("Caught:", error.message);
        console.log(
            "State:",
            manager.getState(
                manager.key("/missing")
            ).status
        );
    }

    console.log("\n6. Final state");

    console.log(manager.getState(usersKey));

    console.log("\nDemonstration completed.");
}

if (typeof module !== "undefined" && require.main === module) {
    demonstration().catch(error => {
        console.error("Application failed:", error);
        process.exitCode = 1;
    });
}

if (typeof module !== "undefined") {
    module.exports = {
        APIClient,
        QueryCache,
        QueryManager,
        FetchError,
        RequestCancelledError,
        createReactHooks
    };
}
