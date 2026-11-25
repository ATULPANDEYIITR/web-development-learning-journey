"use strict";

/**
 * Next.js Advanced Architecture
 *
 * Event-driven model of:
 * - Server and Client Component boundaries
 * - Asynchronous data access
 * - Suspense and loading fallbacks
 * - Error boundary recovery
 * - Nested route execution
 * - Request deduplication
 * - Serializable props
 * - Rendering lifecycle
 *
 * Runtime: Node.js 18+
 * Dependencies: None
 */

const { EventEmitter } = require("node:events");
const crypto = require("node:crypto");
const assert = require("node:assert/strict");

const ComponentKind = Object.freeze({
    SERVER: "server",
    CLIENT: "client"
});

const State = Object.freeze({
    CREATED: "created",
    LOADING: "loading",
    STREAMING: "streaming",
    READY: "ready",
    ERROR: "error",
    NOT_FOUND: "not_found",
    RECOVERED: "recovered"
});

class ApplicationError extends Error {
    constructor(message, code = "APPLICATION_ERROR") {
        super(message);
        this.name = this.constructor.name;
        this.code = code;
    }
}

class SerializationError extends ApplicationError {
    constructor(message) {
        super(message, "SERIALIZATION_ERROR");
    }
}

class ResourceNotFoundError extends ApplicationError {
    constructor(resource) {
        super(`Resource not found: ${resource}`);
        this.code = "NOT_FOUND";
    }
}

class ComponentContract {
    static validate(component) {
        if (!component || typeof component !== "object") {
            throw new TypeError("Component must be an object.");
        }

        if (!component.name || typeof component.name !== "string") {
            throw new TypeError("Component requires a name.");
        }

        if (!Object.values(ComponentKind).includes(component.kind)) {
            throw new TypeError("Invalid component kind.");
        }

        if (
            component.props === null ||
            typeof component.props !== "object" ||
            Array.isArray(component.props)
        ) {
            throw new TypeError("Component props must be an object.");
        }
    }
}

class SerializableProps {
    static validate(value, path = "props", seen = new WeakSet()) {
        if (
            value === null ||
            typeof value === "string" ||
            typeof value === "boolean"
        ) {
            return;
        }

        if (typeof value === "number") {
            if (!Number.isFinite(value)) {
                throw new SerializationError(
                    `Non-finite number at ${path}`
                );
            }
            return;
        }

        if (typeof value !== "object") {
            throw new SerializationError(
                `Unsupported value at ${path}: ${typeof value}`
            );
        }

        if (seen.has(value)) {
            throw new SerializationError(
                `Circular reference at ${path}`
            );
        }

        if (
            !Array.isArray(value) &&
            Object.getPrototypeOf(value) !== Object.prototype &&
            Object.getPrototypeOf(value) !== null
        ) {
            throw new SerializationError(
                `Unsupported object type at ${path}`
            );
        }

        seen.add(value);

        for (const key of Object.keys(value)) {
            const descriptor = Object.getOwnPropertyDescriptor(value, key);

            if (!descriptor || !("value" in descriptor)) {
                throw new SerializationError(
                    `Accessor property rejected at ${path}.${key}`
                );
            }

            this.validate(
                descriptor.value,
                `${path}.${key}`,
                seen
            );
        }

        seen.delete(value);
    }

    static transfer(props) {
        this.validate(props);

        return JSON.parse(JSON.stringify(props));
    }
}

/**
 * Request-local asynchronous memoization.
 *
 * Concurrent consumers of the same key share one Promise.
 * Failed requests are removed so a later attempt can retry.
 */
class RequestDataCache {
    #entries = new Map();

    async get(key, loader) {
        if (this.#entries.has(key)) {
            return this.#entries.get(key);
        }

        const pending = Promise.resolve().then(loader);

        this.#entries.set(key, pending);

        try {
            return await pending;
        } catch (error) {
            this.#entries.delete(key);
            throw error;
        }
    }

    clear() {
        this.#entries.clear();
    }
}

class DataRepository {
    #records = new Map();

    constructor() {
        this.#records.set(1, {
            id: 1,
            name: "Atul",
            email: "atul@example.com",
            role: "administrator",
            internalToken: "SERVER_ONLY_SECRET"
        });

        this.#records.set(2, {
            id: 2,
            name: "Developer",
            email: "developer@example.com",
            role: "member",
            internalToken: "ANOTHER_SECRET"
        });
    }

    async getUser(id) {
        await new Promise(resolve => setTimeout(resolve, 20));

        const user = this.#records.get(id);

        if (!user) {
            throw new ResourceNotFoundError(`user:${id}`);
        }

        // Whitelist public fields rather than serializing the full record.
        return Object.freeze({
            id: user.id,
            name: user.name,
            role: user.role
        });
    }

    async getMetrics() {
        await new Promise(resolve => setTimeout(resolve, 30));

        return Object.freeze({
            activeProjects: 12,
            pendingTasks: 8,
            completedTasks: 24
        });
    }
}

class RenderEngine extends EventEmitter {
    constructor(repository) {
        super();
        this.repository = repository;
        this.cache = new RequestDataCache();
    }

    beginRequest() {
        this.cache.clear();
        this.emit("request:start");
    }

    async renderServerComponent(component) {
        ComponentContract.validate(component);

        if (component.kind !== ComponentKind.SERVER) {
            throw new TypeError("Server Component required.");
        }

        const started = performance.now();

        this.emit("component:start", component.name);

        try {
            let output;

            if (component.name === "Dashboard") {
                const userId = component.props.userId ?? 1;

                const [user, metrics] = await Promise.all([
                    this.cache.get(
                        `user:${userId}`,
                        () => this.repository.getUser(userId)
                    ),
                    this.cache.get(
                        "dashboard:metrics",
                        () => this.repository.getMetrics()
                    )
                ]);

                output = { user, metrics };
            } else if (component.name === "UserProfile") {
                const userId = component.props.userId ?? 1;

                output = await this.cache.get(
                    `user:${userId}`,
                    () => this.repository.getUser(userId)
                );
            } else {
                output = { content: component.props.content ?? "" };
            }

            const result = {
                component: component.name,
                state: State.READY,
                output,
                durationMs: performance.now() - started
            };

            this.emit("component:ready", result);
            return result;

        } catch (error) {
            const state = error.code === "NOT_FOUND"
                ? State.NOT_FOUND
                : State.ERROR;

            const result = {
                component: component.name,
                state,
                error: error.message,
                durationMs: performance.now() - started
            };

            this.emit("component:error", result);
            return result;
        }
    }

    renderClientComponent(component, serverData = null) {
        ComponentContract.validate(component);

        if (component.kind !== ComponentKind.CLIENT) {
            throw new TypeError("Client Component required.");
        }

        try {
            const props = {
                ...component.props
            };

            if (serverData !== null) {
                props.serverData = serverData;
            }

            const transferred = SerializableProps.transfer(props);

            return {
                component: component.name,
                state: State.READY,
                props: transferred,
                hydrationRequired: true,
                interactive: true
            };

        } catch (error) {
            return {
                component: component.name,
                state: State.ERROR,
                error: error.message
            };
        }
    }
}

/**
 * Suspense-style asynchronous boundary.
 *
 * Returns a loading fallback immediately while the underlying
 * operation remains observable through the pending Promise.
 */
class StreamingBoundary {
    constructor(label, fallback) {
        this.label = label;
        this.fallback = fallback;
        this.state = State.CREATED;
    }

    async execute(operation, timeoutMs = 2000) {
        if (timeoutMs <= 0) {
            throw new RangeError("Timeout must be positive.");
        }

        this.state = State.LOADING;

        let timer;

        const task = Promise.resolve().then(operation);

        const timeout = new Promise(resolve => {
            timer = setTimeout(() => {
                resolve({
                    timedOut: true
                });
            }, timeoutMs);
        });

        try {
            const outcome = await Promise.race([
                task.then(value => ({
                    timedOut: false,
                    value
                })),
                timeout
            ]);

            if (outcome.timedOut) {
                this.state = State.STREAMING;

                // Attach a rejection handler even after timeout.
                // This prevents an unhandled rejection.
                const pending = task.then(
                    value => ({
                        state: State.READY,
                        value
                    }),
                    error => ({
                        state: State.ERROR,
                        error: error.message
                    })
                );

                return {
                    boundary: this.label,
                    state: State.STREAMING,
                    fallback: this.fallback,
                    pending
                };
            }

            this.state = State.READY;

            return {
                boundary: this.label,
                state: State.READY,
                value: outcome.value
            };

        } catch (error) {
            this.state = State.ERROR;

            return {
                boundary: this.label,
                state: State.ERROR,
                fallback: this.fallback,
                error: error.message
            };
        } finally {
            clearTimeout(timer);
        }
    }
}

/**
 * Error boundaries handle rendering failures, not arbitrary
 * failures in event handlers or unrelated asynchronous callbacks.
 */
class SegmentErrorBoundary {
    constructor(fallback) {
        this.fallback = fallback;
        this.lastError = null;
        this.resetCount = 0;
    }

    async execute(operation) {
        try {
            const value = await operation();

            this.lastError = null;

            return {
                state: State.READY,
                value
            };

        } catch (error) {
            this.lastError = error;

            return {
                state: State.ERROR,
                fallback: this.fallback,
                error: error.message
            };
        }
    }

    async reset(operation) {
        this.resetCount++;

        const result = await this.execute(operation);

        if (result.state === State.READY) {
            result.state = State.RECOVERED;
        }

        return result;
    }
}

class RouteSegment {
    constructor(name, options = {}) {
        if (!name || name.includes("..")) {
            throw new TypeError("Invalid route segment name.");
        }

        this.name = name;
        this.loading = options.loading ?? "Loading...";
        this.error = options.error ?? "Something went wrong.";
        this.children = new Map();
    }

    addChild(segment) {
        if (this.children.has(segment.name)) {
            throw new Error(
                `Duplicate route segment: ${segment.name}`
            );
        }

        this.children.set(segment.name, segment);
    }

    resolve(path) {
        const parts = path
            .split("/")
            .filter(Boolean);

        let current = this;

        for (const part of parts) {
            current = current.children.get(part);

            if (!current) {
                throw new ResourceNotFoundError(
                    `route:${path}`
                );
            }
        }

        return current;
    }
}

class Application {
    constructor() {
        this.repository = new DataRepository();
        this.engine = new RenderEngine(this.repository);

        this.engine.on("component:start", name => {
            console.log(`[START] ${name}`);
        });

        this.engine.on("component:ready", result => {
            console.log(
                `[READY] ${result.component} ` +
                `${result.durationMs.toFixed(2)}ms`
            );
        });

        this.engine.on("component:error", result => {
            console.error(
                `[ERROR] ${result.component}: ${result.error}`
            );
        });
    }

    async renderDashboard() {
        this.engine.beginRequest();

        const server = await this.engine.renderServerComponent({
            name: "Dashboard",
            kind: ComponentKind.SERVER,
            props: { userId: 1 }
        });

        if (server.state !== State.READY) {
            return server;
        }

        const client = this.engine.renderClientComponent({
            name: "DashboardControls",
            kind: ComponentKind.CLIENT,
            props: {
                theme: "dark",
                refreshEnabled: true
            }
        }, server.output);

        return {
            route: "/dashboard",
            server,
            client
        };
    }
}

async function runTests() {
    const repository = new DataRepository();
    const engine = new RenderEngine(repository);

    // Server Component execution.
    const server = await engine.renderServerComponent({
        name: "UserProfile",
        kind: ComponentKind.SERVER,
        props: { userId: 1 }
    });

    assert.equal(server.state, State.READY);
    assert.equal(server.output.name, "Atul");
    assert.equal(
        Object.hasOwn(server.output, "internalToken"),
        false
    );

    // Missing data.
    const missing = await engine.renderServerComponent({
        name: "UserProfile",
        kind: ComponentKind.SERVER,
        props: { userId: 999 }
    });

    assert.equal(missing.state, State.NOT_FOUND);

    // Function props cannot cross the boundary.
    const invalidClient = engine.renderClientComponent({
        name: "InvalidControls",
        kind: ComponentKind.CLIENT,
        props: {
            onClick: () => {}
        }
    });

    assert.equal(invalidClient.state, State.ERROR);

    // Concurrent request caching.
    const cache = new RequestDataCache();
    let calls = 0;

    const loader = async () => {
        calls++;
        return 100;
    };

    const values = await Promise.all([
        cache.get("shared", loader),
        cache.get("shared", loader),
        cache.get("shared", loader)
    ]);

    assert.deepEqual(values, [100, 100, 100]);
    assert.equal(calls, 1);

    // Suspense timeout.
    const boundary = new StreamingBoundary(
        "Analytics",
        "Loading analytics..."
    );

    const streamed = await boundary.execute(
        () => new Promise(resolve => {
            setTimeout(() => resolve("Loaded"), 100);
        }),
        5
    );

    assert.equal(streamed.state, State.STREAMING);

    const completion = await streamed.pending;
    assert.equal(completion.state, State.READY);

    // Error boundary recovery.
    const errorBoundary = new SegmentErrorBoundary(
        "Service unavailable"
    );

    let attempt = 0;

    const operation = async () => {
        attempt++;

        if (attempt === 1) {
            throw new Error("Temporary failure");
        }

        return "Recovered";
    };

    const failed = await errorBoundary.execute(operation);
    const recovered = await errorBoundary.reset(operation);

    assert.equal(failed.state, State.ERROR);
    assert.equal(recovered.state, State.RECOVERED);

    // Nested route lookup.
    const root = new RouteSegment("dashboard");

    root.addChild(new RouteSegment("analytics"));
    root.addChild(new RouteSegment("reports"));

    assert.equal(
        root.resolve("analytics").name,
        "analytics"
    );

    console.log("\nAll JavaScript tests passed.");
}

async function main() {
    console.log("NEXT.JS ADVANCED ARCHITECTURE");
    console.log("================================");

    const application = new Application();

    const dashboard = await application.renderDashboard();

    console.log(
        "\nDASHBOARD:",
        JSON.stringify(dashboard, null, 2)
    );

    const loadingBoundary = new StreamingBoundary(
        "Reports",
        "Loading reports..."
    );

    const loading = await loadingBoundary.execute(
        async () => {
            await new Promise(resolve => setTimeout(resolve, 30));
            return { reportCount: 5 };
        }
    );

    console.log("\nLOADING:", loading);

    await runTests();
}

main().catch(error => {
    console.error("Fatal application error:", error.message);
    process.exitCode = 1;
});
