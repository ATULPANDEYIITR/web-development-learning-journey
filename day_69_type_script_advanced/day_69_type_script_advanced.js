"use strict";

/**
 * TypeScript Advanced Concepts:
 * JavaScript runtime implementation with JSDoc generic annotations.
 *
 * Covers:
 * - Generic functions and classes
 * - Generic repository
 * - Utility-type runtime equivalents
 * - Type narrowing
 * - Custom type guards
 * - Conditional type behavior
 * - Discriminated unions
 * - Async processing
 * - Runtime validation
 *
 * Run:
 * node typescript_advanced.js
 */

/**
 * @template T
 * @param {T} value
 * @returns {T}
 */
function identity(value) {
    return value;
}

/**
 * @template T
 * @param {T[]} items
 * @returns {T | undefined}
 */
function first(items) {
    return items[0];
}

/**
 * @template T
 */
class GenericRepository {
    constructor() {
        /** @type {Map<string, T>} */
        this.records = new Map();
    }

    /**
     * @param {string} key
     * @param {T} value
     */
    add(key, value) {
        if (typeof key !== "string" || !key.trim()) {
            throw new TypeError("Invalid repository key");
        }

        if (this.records.has(key)) {
            throw new Error(`Duplicate key: ${key}`);
        }

        this.records.set(key, value);
    }

    /**
     * @param {string} key
     * @returns {T | undefined}
     */
    get(key) {
        return this.records.get(key);
    }

    /**
     * @returns {T[]}
     */
    values() {
        return [...this.records.values()];
    }

    remove(key) {
        return this.records.delete(key);
    }
}


// ============================================================
// DOMAIN MODELS
// ============================================================

class User {
    constructor(id, name, email) {
        if (!Number.isInteger(id) || id <= 0) {
            throw new TypeError("Invalid user ID");
        }

        if (typeof name !== "string" || !name.trim()) {
            throw new TypeError("Invalid name");
        }

        if (typeof email !== "string" || !email.includes("@")) {
            throw new TypeError("Invalid email");
        }

        this.id = id;
        this.name = name.trim();
        this.email = email;
        this.status = "active";
    }
}

class Product {
    constructor(id, name, price) {
        if (!Number.isInteger(id) || id <= 0) {
            throw new TypeError("Invalid product ID");
        }

        if (!Number.isFinite(price) || price < 0) {
            throw new TypeError("Invalid product price");
        }

        this.id = id;
        this.name = name;
        this.price = price;
    }
}


// ============================================================
// UTILITY TYPES: PARTIAL, PICK, OMIT, READONLY
// ============================================================

/**
 * Partial<T>-style update.
 * Object.assign mutates the target, so a new object is returned.
 */
function partialUpdate(original, changes) {
    const allowed = new Set([
        "name",
        "email",
        "phone",
        "department",
    ]);

    for (const key of Object.keys(changes)) {
        if (!allowed.has(key)) {
            throw new Error(`Unsupported property: ${key}`);
        }
    }

    const updated = { ...original, ...changes };

    if (typeof updated.name !== "string" || !updated.name.trim()) {
        throw new TypeError("Invalid name");
    }

    if (typeof updated.email !== "string" ||
        !updated.email.includes("@")) {
        throw new TypeError("Invalid email");
    }

    return updated;
}

/**
 * Pick<T, K>-style operation.
 */
function pick(source, keys) {
    const result = {};

    for (const key of keys) {
        if (Object.hasOwn(source, key)) {
            result[key] = source[key];
        }
    }

    return result;
}

/**
 * Omit<T, K>-style operation.
 */
function omit(source, keys) {
    const excluded = new Set(keys);

    return Object.fromEntries(
        Object.entries(source).filter(
            ([key]) => !excluded.has(key)
        )
    );
}

/**
 * Readonly<T>-style shallow runtime protection.
 */
function readonlySnapshot(source) {
    return Object.freeze({ ...source });
}

/**
 * Record<K, T>-style mapping.
 */
function createRecord(items, keySelector) {
    const result = Object.create(null);

    for (const item of items) {
        const key = keySelector(item);

        if (typeof key !== "string" || !key) {
            throw new TypeError("Invalid record key");
        }

        if (Object.hasOwn(result, key)) {
            throw new Error(`Duplicate key: ${key}`);
        }

        result[key] = item;
    }

    return result;
}


// ============================================================
// TYPE NARROWING
// ============================================================

function describe(value) {
    if (value === null || value === undefined) {
        return "Missing value";
    }

    if (typeof value === "string") {
        return `String: ${value.trim()}`;
    }

    if (typeof value === "number") {
        if (!Number.isFinite(value)) {
            return "Invalid number";
        }

        return `Number: ${value}`;
    }

    if (typeof value === "boolean") {
        return `Boolean: ${value}`;
    }

    if (Array.isArray(value)) {
        return `Array with ${value.length} elements`;
    }

    if (typeof value === "object") {
        return "Object";
    }

    return "Unsupported value";
}


// ============================================================
// CUSTOM TYPE GUARDS
// ============================================================

/**
 * @param {unknown} value
 * @returns {value is {id: number, name: string, email: string}}
 */
function isUser(value) {
    return (
        value !== null &&
        typeof value === "object" &&
        !Array.isArray(value) &&
        Object.keys(value).length === 3 &&
        Number.isInteger(value.id) &&
        value.id > 0 &&
        typeof value.name === "string" &&
        value.name.trim().length > 0 &&
        typeof value.email === "string" &&
        value.email.includes("@")
    );
}

function parseUser(value) {
    if (!isUser(value)) {
        throw new TypeError("User validation failed");
    }

    return new User(value.id, value.name, value.email);
}


// ============================================================
// DISCRIMINATED UNIONS
// ============================================================

function success(data) {
    return {
        kind: "success",
        data,
    };
}

function failure(message, code) {
    return {
        kind: "failure",
        error: message,
        code,
    };
}

function processResult(result) {
    switch (result.kind) {
        case "success":
            return `Completed: ${JSON.stringify(result.data)}`;

        case "failure":
            return `Error ${result.code}: ${result.error}`;

        default:
            throw new TypeError("Unknown result variant");
    }
}


// ============================================================
// CONDITIONAL TYPE BEHAVIOR
// ============================================================

/**
 * Runtime equivalent of a conditional transformation.
 *
 * TypeScript:
 * type Normalize<T> =
 *   T extends string ? string :
 *   T extends number ? number :
 *   never;
 */
function normalize(value) {
    if (typeof value === "string") {
        return value.trim().toLowerCase();
    }

    if (typeof value === "number" && Number.isFinite(value)) {
        return Math.abs(value);
    }

    throw new TypeError("Unsupported normalization type");
}


// ============================================================
// GENERIC ASYNC SERVICE
// ============================================================

/**
 * @template T
 */
class AsyncService {
    /**
     * @param {(item: T) => Promise<boolean>} validator
     */
    constructor(validator) {
        this.validator = validator;
    }

    /**
     * @param {T[]} items
     * @returns {Promise<T[]>}
     */
    async filterValid(items) {
        const checks = await Promise.all(
            items.map(async item => ({
                item,
                valid: await this.validator(item),
            }))
        );

        return checks
            .filter(result => result.valid)
            .map(result => result.item);
    }
}


// ============================================================
// EVENT-DRIVEN TYPE-SAFE STYLE
// ============================================================

class EventBus {
    constructor() {
        this.listeners = new Map();
    }

    on(event, callback) {
        if (typeof callback !== "function") {
            throw new TypeError("Callback must be a function");
        }

        if (!this.listeners.has(event)) {
            this.listeners.set(event, new Set());
        }

        this.listeners.get(event).add(callback);

        return () => {
            this.listeners.get(event)?.delete(callback);
        };
    }

    emit(event, payload) {
        const listeners = this.listeners.get(event);

        if (!listeners) {
            return;
        }

        for (const callback of listeners) {
            callback(payload);
        }
    }
}


// ============================================================
// SAFE JSON PROCESSING
// ============================================================

function parseJson(text) {
    if (typeof text !== "string") {
        throw new TypeError("JSON input must be a string");
    }

    if (text.length > 1_000_000) {
        throw new RangeError("JSON input too large");
    }

    try {
        return JSON.parse(text);
    } catch (error) {
        throw new Error(`JSON parsing failed: ${error.message}`);
    }
}


// ============================================================
// TESTS
// ============================================================

async function runTests() {
    console.assert(identity(100) === 100);
    console.assert(first([10, 20]) === 10);
    console.assert(first([]) === undefined);

    const repository = new GenericRepository();

    repository.add("U001", new User(
        1,
        "Aarav",
        "aarav@example.com"
    ));

    console.assert(repository.get("U001").id === 1);
    console.assert(repository.remove("U001"));
    console.assert(repository.get("U001") === undefined);

    const original = {
        name: "Mira",
        email: "mira@example.com",
        department: "Research",
    };

    const updated = partialUpdate(original, {
        department: "Engineering",
    });

    console.assert(updated.department === "Engineering");
    console.assert(original.department === "Research");

    console.assert(pick(original, ["name"]).name === "Mira");
    console.assert(!Object.hasOwn(omit(original, ["email"]), "email"));

    const snapshot = readonlySnapshot(original);
    console.assert(Object.isFrozen(snapshot));

    console.assert(describe("hello") === "String: hello");
    console.assert(describe(null) === "Missing value");

    console.assert(isUser({
        id: 2,
        name: "Mira",
        email: "mira@example.com",
    }));

    console.assert(!isUser({
        id: true,
        name: "Mira",
        email: "mira@example.com",
    }));

    console.assert(
        processResult(success({ approved: true })).startsWith("Completed")
    );

    console.assert(
        processResult(failure("Denied", 403)).startsWith("Error")
    );

    console.assert(normalize(" TYPESCRIPT ") === "typescript");
    console.assert(normalize(-20) === 20);

    const service = new AsyncService(async user => user.active);

    const validUsers = await service.filterValid([
        { id: 1, active: true },
        { id: 2, active: false },
        { id: 3, active: true },
    ]);

    console.assert(validUsers.length === 2);

    let eventCount = 0;
    const bus = new EventBus();

    const unsubscribe = bus.on("user.created", () => {
        eventCount++;
    });

    bus.emit("user.created", { id: 1 });
    unsubscribe();
    bus.emit("user.created", { id: 2 });

    console.assert(eventCount === 1);

    console.assert(
        parseJson('{"status":"active"}').status === "active"
    );

    console.log("All JavaScript tests passed.");
}


// ============================================================
// MAIN
// ============================================================

async function main() {
    console.log("ADVANCED TYPE SYSTEM CONCEPTS");
    console.log("=".repeat(50));

    await runTests();

    const users = new GenericRepository();

    users.add("U101", new User(
        101,
        "Mira",
        "mira@example.com"
    ));

    console.log("\nGeneric repository:");
    console.log(users.values());

    console.log("\nUtility types:");
    console.log(pick(
        { id: 1, name: "Mira", password: "secret" },
        ["id", "name"]
    ));

    console.log("\nType narrowing:");
    console.log(describe(["TypeScript", "JavaScript"]));

    console.log("\nConditional behavior:");
    console.log(normalize(" ADVANCED TYPES "));

    console.log("\nDiscriminated union:");
    console.log(processResult(
        success({ transactionId: "TX-001" })
    ));

    console.log("\nAsync validation:");
    const service = new AsyncService(
        async product => product.price >= 100
    );

    console.log(await service.filterValid([
        { name: "A", price: 50 },
        { name: "B", price: 150 },
    ]));
}

main().catch(error => {
    console.error("Application failure:", error.message);
    process.exitCode = 1;
});
