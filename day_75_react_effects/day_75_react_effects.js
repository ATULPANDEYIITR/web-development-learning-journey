"use strict";

/**
 * React Effects: Event-driven effect lifecycle and resource management.
 *
 * Runtime: Node.js 18+
 *
 * Demonstrates:
 * - Dependency tracking with Object.is.
 * - Commit-based effect scheduling.
 * - Cleanup ordering.
 * - Event-driven subscriptions.
 * - AbortController for asynchronous work.
 * - Strict Mode lifecycle replay.
 * - Error isolation and resource disposal.
 *
 * This is a standalone lifecycle simulator, not a replacement
 * for React's actual rendering and scheduling implementation.
 */

const { EventEmitter } = require("node:events");
const { setTimeout: sleep } = require("node:timers/promises");

class EffectLifecycleError extends Error {}

class EffectRuntime {
    #effects = new Map();
    #mounted = true;
    #commitNumber = 0;

    constructor(name) {
        if (!name) {
            throw new TypeError("Component name is required.");
        }

        this.name = name;
    }

    register(name, setup, dependencies = undefined) {
        this.#assertMounted();

        if (this.#effects.has(name)) {
            throw new EffectLifecycleError(
                `Effect already registered: ${name}`
            );
        }

        if (typeof setup !== "function") {
            throw new TypeError("Effect setup must be a function.");
        }

        this.#effects.set(name, {
            setup,
            dependencies: normalizeDependencies(dependencies),
            cleanup: undefined,
            initialized: false,
            executions: 0
        });
    }

    commit(updates = new Map()) {
        this.#assertMounted();
        this.#commitNumber++;

        for (const [name, effect] of this.#effects) {
            const nextDependencies = updates.has(name)
                ? normalizeDependencies(updates.get(name))
                : effect.dependencies;

            const changed =
                !effect.initialized ||
                dependenciesChanged(
                    effect.dependencies,
                    nextDependencies
                );

            if (!changed) {
                continue;
            }

            this.#runCleanup(effect);

            try {
                const cleanup = effect.setup();

                if (
                    cleanup !== undefined &&
                    typeof cleanup !== "function"
                ) {
                    throw new TypeError(
                        `Effect ${name} returned an invalid cleanup.`
                    );
                }

                effect.cleanup = cleanup;
                effect.dependencies = nextDependencies;
                effect.initialized = true;
                effect.executions++;

                console.log(
                    `[${this.name}] effect executed: ${name}`
                );
            } catch (error) {
                effect.cleanup = undefined;
                effect.dependencies = nextDependencies;
                effect.initialized = true;
                throw new EffectLifecycleError(
                    `${name}: ${error.message}`
                );
            }
        }
    }

    replayStrictMode() {
        this.#assertMounted();

        for (const effect of this.#effects.values()) {
            if (effect.initialized) {
                this.#runCleanup(effect);
                effect.initialized = false;
            }
        }

        this.commit();
    }

    unmount() {
        if (!this.#mounted) {
            return;
        }

        const effects = [...this.#effects.values()].reverse();

        for (const effect of effects) {
            this.#runCleanup(effect);
        }

        this.#mounted = false;
        console.log(`[${this.name}] unmounted`);
    }

    #runCleanup(effect) {
        const cleanup = effect.cleanup;
        effect.cleanup = undefined;

        if (cleanup) {
            cleanup();
        }
    }

    #assertMounted() {
        if (!this.#mounted) {
            throw new EffectLifecycleError(
                "Component is already unmounted."
            );
        }
    }

    get commitNumber() {
        return this.#commitNumber;
    }
}

function normalizeDependencies(dependencies) {
    if (dependencies === undefined) {
        return undefined;
    }

    if (!Array.isArray(dependencies)) {
        throw new TypeError(
            "Dependencies must be an array or undefined."
        );
    }

    return [...dependencies];
}

function dependenciesChanged(previous, current) {
    // Missing dependencies cause execution after every commit.
    if (previous === undefined || current === undefined) {
        return true;
    }

    if (previous.length !== current.length) {
        throw new EffectLifecycleError(
            "Dependency array size must remain constant."
        );
    }

    return previous.some(
        (value, index) => !Object.is(value, current[index])
    );
}

/**
 * An event-driven service demonstrates how subscriptions
 * are created and removed through effect cleanup.
 */
class NotificationService extends EventEmitter {
    subscribe(topic, handler) {
        if (!topic || typeof handler !== "function") {
            throw new TypeError("Invalid subscription.");
        }

        this.on(topic, handler);

        let active = true;

        return () => {
            if (!active) {
                return;
            }

            active = false;
            this.off(topic, handler);
        };
    }

    publish(topic, payload) {
        this.emit(topic, Object.freeze({ ...payload }));
    }
}

/**
 * An asynchronous effect uses AbortController to prevent
 * obsolete requests from updating application state.
 */
class SearchController {
    #controller = null;
    #results = [];

    async execute(query) {
        this.cancel();

        const controller = new AbortController();
        this.#controller = controller;

        try {
            const results = await this.#request(
                query,
                controller.signal
            );

            if (!controller.signal.aborted) {
                this.#results = results;
            }

            return this.#results;
        } catch (error) {
            if (error.name === "AbortError") {
                console.log("Search request cancelled.");
                return this.#results;
            }

            throw error;
        } finally {
            if (this.#controller === controller) {
                this.#controller = null;
            }
        }
    }

    async #request(query, signal) {
        if (!query.trim()) {
            return [];
        }

        await sleep(100, undefined, { signal });

        return [
            `${query}: result 1`,
            `${query}: result 2`,
            `${query}: result 3`
        ];
    }

    cancel() {
        this.#controller?.abort();
    }

    get results() {
        return [...this.#results];
    }
}

/**
 * Models independent state updates without tying them
 * to an actual React renderer.
 */
class ComponentState {
    #values = new Map();
    #listeners = new Map();

    get(key) {
        return this.#values.get(key);
    }

    set(key, value) {
        const previous = this.#values.get(key);

        if (Object.is(previous, value)) {
            return false;
        }

        this.#values.set(key, value);

        for (const listener of this.#listeners.get(key) || []) {
            listener(value, previous);
        }

        return true;
    }

    subscribe(key, listener) {
        if (!this.#listeners.has(key)) {
            this.#listeners.set(key, new Set());
        }

        const listeners = this.#listeners.get(key);
        listeners.add(listener);

        return () => listeners.delete(listener);
    }
}

async function main() {
    const notifications = new NotificationService();
    const runtime = new EffectRuntime("Dashboard");
    const state = new ComponentState();

    let topic = "system-alerts";
    const received = [];

    runtime.register(
        "notification-subscription",
        () => {
            console.log(`Subscribing to ${topic}`);

            return notifications.subscribe(topic, message => {
                received.push(message);
            });
        },
        [topic]
    );

    runtime.commit();

    notifications.publish(topic, { message: "Service online" });

    topic = "security-alerts";

    runtime.commit(
        new Map([
            ["notification-subscription", [topic]]
        ])
    );

    notifications.publish("system-alerts", {
        message: "Ignored old topic"
    });

    notifications.publish(topic, {
        message: "Security event detected"
    });

    if (received.length !== 2) {
        throw new Error("Subscription cleanup failed.");
    }

    // Strict Mode performs an additional setup-cleanup-setup cycle.
    runtime.replayStrictMode();

    runtime.unmount();

    const search = new SearchController();

    const firstSearch = search.execute("React");

    await sleep(10);

    const secondSearch = search.execute("useEffect");

    await firstSearch;
    await secondSearch;

    console.log("Search results:", search.results);

    state.set("count", 1);

    const unsubscribe = state.subscribe(
        "count",
        (next, previous) => {
            console.log(`Count changed: ${previous} -> ${next}`);
        }
    );

    state.set("count", 2);
    unsubscribe();

    console.log("All lifecycle checks completed.");
}

main().catch(error => {
    console.error("Application failure:", error);
    process.exitCode = 1;
});
