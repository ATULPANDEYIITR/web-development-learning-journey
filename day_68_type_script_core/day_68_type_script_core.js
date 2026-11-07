"use strict";

/*
 * TYPESCRIPT CORE: JAVASCRIPT RUNTIME MODEL
 *
 * Arrays, objects, tuples, enums, unions,
 * intersections, aliases, generics and validation.
 *
 * Run: node typescript_core.js
 */

// ============================================================
// 1. Type aliases and runtime validation
// ============================================================

// JavaScript does not enforce TypeScript aliases at runtime.
// Runtime validators enforce the corresponding contracts.

const isNonEmptyString = (value) =>
    typeof value === "string" && value.trim().length > 0;

const isPositiveInteger = (value) =>
    Number.isSafeInteger(value) && value > 0;

const isEmail = (value) =>
    typeof value === "string" &&
    /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);


// ============================================================
// 2. Enums
// ============================================================

const UserRole = Object.freeze({
    ADMIN: "ADMIN",
    DEVELOPER: "DEVELOPER",
    ANALYST: "ANALYST",
    VIEWER: "VIEWER"
});

const AccountStatus = Object.freeze({
    ACTIVE: "ACTIVE",
    SUSPENDED: "SUSPENDED",
    PENDING: "PENDING"
});

const ProjectStatus = Object.freeze({
    PLANNED: "PLANNED",
    IN_PROGRESS: "IN_PROGRESS",
    COMPLETED: "COMPLETED"
});


// ============================================================
// 3. Arrays
// ============================================================

function analyzeScores(scores) {
    if (!Array.isArray(scores)) {
        throw new TypeError("Scores must be an array");
    }

    if (scores.length === 0) {
        throw new RangeError("Scores cannot be empty");
    }

    if (!scores.every(
        score => typeof score === "number" &&
            Number.isFinite(score) &&
            score >= 0 &&
            score <= 100
    )) {
        throw new RangeError("Invalid score");
    }

    const sorted = [...scores].sort((a, b) => a - b);

    return {
        original: [...scores],
        sorted,
        highest: sorted[sorted.length - 1],
        lowest: sorted[0],
        average: scores.reduce((sum, value) => sum + value, 0)
            / scores.length,
        passed: scores.filter(score => score >= 50),
        unique: [...new Set(scores)]
    };
}


// ============================================================
// 4. Tuple validation
// ============================================================

// TypeScript tuple:
// type Coordinate = [number, number]

function createCoordinate(latitude, longitude) {
    if (
        typeof latitude !== "number" ||
        typeof longitude !== "number" ||
        !Number.isFinite(latitude) ||
        !Number.isFinite(longitude)
    ) {
        throw new TypeError("Coordinates must be finite numbers");
    }

    if (latitude < -90 || latitude > 90) {
        throw new RangeError("Invalid latitude");
    }

    if (longitude < -180 || longitude > 180) {
        throw new RangeError("Invalid longitude");
    }

    return Object.freeze([latitude, longitude]);
}

function processUserTuple(tuple) {
    if (
        !Array.isArray(tuple) ||
        tuple.length !== 3 ||
        !isPositiveInteger(tuple[0]) ||
        !isNonEmptyString(tuple[1]) ||
        !Object.values(UserRole).includes(tuple[2])
    ) {
        throw new TypeError("Invalid user tuple");
    }

    const [id, name, role] = tuple;

    return `${id}: ${name} (${role})`;
}


// ============================================================
// 5. Objects and classes
// ============================================================

class Profile {
    constructor(displayName, email, location) {
        if (!isNonEmptyString(displayName)) {
            throw new TypeError("Display name is required");
        }

        if (!isEmail(email)) {
            throw new TypeError("Invalid email");
        }

        if (!isNonEmptyString(location)) {
            throw new TypeError("Location is required");
        }

        this.displayName = displayName;
        this.email = email;
        this.location = location;

        Object.freeze(this);
    }
}

class User {
    constructor({
        id,
        profile,
        role,
        status,
        tags = []
    }) {
        if (!isPositiveInteger(id)) {
            throw new TypeError("Invalid user ID");
        }

        if (!(profile instanceof Profile)) {
            throw new TypeError("Invalid profile object");
        }

        if (!Object.values(UserRole).includes(role)) {
            throw new TypeError("Invalid user role");
        }

        if (!Object.values(AccountStatus).includes(status)) {
            throw new TypeError("Invalid account status");
        }

        if (
            !Array.isArray(tags) ||
            !tags.every(isNonEmptyString) ||
            new Set(tags).size !== tags.length
        ) {
            throw new TypeError("Invalid user tags");
        }

        this.id = id;
        this.profile = profile;
        this.role = role;
        this.status = status;
        this.tags = Object.freeze([...tags]);
    }

    toJSON() {
        return {
            id: this.id,
            profile: {
                displayName: this.profile.displayName,
                email: this.profile.email,
                location: this.profile.location
            },
            role: this.role,
            status: this.status,
            tags: [...this.tags]
        };
    }
}


// ============================================================
// 6. Union types
// ============================================================

// TypeScript:
// type Identifier = number | string

function normalizeIdentifier(value) {
    if (typeof value === "number") {
        if (!isPositiveInteger(value)) {
            throw new RangeError("Numeric ID must be positive");
        }

        return String(value);
    }

    if (typeof value === "string") {
        if (!isNonEmptyString(value)) {
            throw new TypeError("String ID cannot be empty");
        }

        return value.trim();
    }

    throw new TypeError("Unsupported identifier");
}


// ============================================================
// 7. Discriminated unions
// ============================================================

// TypeScript:
// type ApiResult =
//   | { kind: "success"; data: object }
//   | { kind: "error"; message: string; code: number }

function handleApiResult(result) {
    if (!result || typeof result !== "object") {
        throw new TypeError("Invalid API result");
    }

    switch (result.kind) {
        case "success":
            if (
                !result.data ||
                typeof result.data !== "object" ||
                Array.isArray(result.data)
            ) {
                throw new TypeError("Invalid success payload");
            }

            return {
                success: true,
                data: result.data
            };

        case "error":
            if (
                !isNonEmptyString(result.message) ||
                !Number.isInteger(result.code)
            ) {
                throw new TypeError("Invalid error payload");
            }

            return {
                success: false,
                message: result.message,
                code: result.code
            };

        default:
            throw new TypeError("Unknown result discriminator");
    }
}


// ============================================================
// 8. Intersection types
// ============================================================

// TypeScript:
// type ManagedResource = Resource & Auditable & Permissions

class ManagedResource {
    constructor(resource, audit, permissions) {
        if (!isPositiveInteger(resource.id)) {
            throw new TypeError("Invalid resource ID");
        }

        if (!isNonEmptyString(resource.name)) {
            throw new TypeError("Resource name is required");
        }

        if (!isPositiveInteger(audit.createdBy)) {
            throw new TypeError("Invalid creator ID");
        }

        if (!isNonEmptyString(audit.createdAt)) {
            throw new TypeError("Creation timestamp is required");
        }

        for (const permission of ["read", "write", "delete"]) {
            if (typeof permissions[permission] !== "boolean") {
                throw new TypeError(`Invalid ${permission} permission`);
            }
        }

        this.id = resource.id;
        this.name = resource.name;
        this.createdBy = audit.createdBy;
        this.createdAt = audit.createdAt;
        this.permissions = Object.freeze({ ...permissions });

        Object.freeze(this);
    }
}


// ============================================================
// 9. Generic-style repository
// ============================================================

class Repository {
    #records = new Map();

    add(id, value) {
        if (!isPositiveInteger(id)) {
            throw new TypeError("Invalid record ID");
        }

        if (this.#records.has(id)) {
            throw new Error("Duplicate record ID");
        }

        this.#records.set(id, value);
    }

    get(id) {
        return this.#records.get(id) ?? null;
    }

    remove(id) {
        return this.#records.delete(id);
    }

    get size() {
        return this.#records.size;
    }

    values() {
        return [...this.#records.values()];
    }
}


// ============================================================
// 10. Asynchronous processing
// ============================================================

async function loadUser(repository, id) {
    await Promise.resolve();

    const user = repository.get(id);

    if (!user) {
        throw new Error(`User ${id} not found`);
    }

    return user;
}


// ============================================================
// 11. Event-driven state management
// ============================================================

class EventBus {
    #listeners = new Map();

    subscribe(eventName, listener) {
        if (!isNonEmptyString(eventName)) {
            throw new TypeError("Invalid event name");
        }

        if (typeof listener !== "function") {
            throw new TypeError("Listener must be a function");
        }

        if (!this.#listeners.has(eventName)) {
            this.#listeners.set(eventName, new Set());
        }

        this.#listeners.get(eventName).add(listener);

        return () => this.#listeners.get(eventName)?.delete(listener);
    }

    emit(eventName, payload) {
        const listeners = this.#listeners.get(eventName);

        if (!listeners) {
            return;
        }

        // Snapshot prevents listener modifications from affecting
        // the current dispatch.
        for (const listener of [...listeners]) {
            listener(payload);
        }
    }
}


// ============================================================
// 12. Application execution
// ============================================================

async function main() {
    console.log("\n=== TYPESCRIPT CORE ===");

    // Arrays
    const scores = [85, 92, 67, 48, 92];
    console.log("\nARRAYS");
    console.log(analyzeScores(scores));

    // Tuples
    console.log("\nTUPLES");
    const coordinate = createCoordinate(26.8467, 80.9462);
    console.log(coordinate);

    console.log(
        processUserTuple([101, "Atul", UserRole.ADMIN])
    );

    // Objects
    console.log("\nOBJECTS");

    const profile = new Profile(
        "Atul Pandey",
        "atul@example.com",
        "Lucknow"
    );

    const user = new User({
        id: 101,
        profile,
        role: UserRole.ADMIN,
        status: AccountStatus.ACTIVE,
        tags: ["typescript", "backend"]
    });

    console.log(user.toJSON());

    // Enums
    console.log("\nENUMS");
    console.log(UserRole.ADMIN);
    console.log(ProjectStatus.IN_PROGRESS);

    // Union
    console.log("\nUNIONS");
    console.log(normalizeIdentifier(101));
    console.log(normalizeIdentifier("USER-101"));

    // Discriminated unions
    console.log("\nDISCRIMINATED UNIONS");

    console.log(handleApiResult({
        kind: "success",
        data: { userId: 101 }
    }));

    console.log(handleApiResult({
        kind: "error",
        message: "Access denied",
        code: 403
    }));

    // Intersections
    console.log("\nINTERSECTION TYPES");

    const resource = new ManagedResource(
        { id: 501, name: "Project Repository" },
        {
            createdBy: 101,
            createdAt: "2026-11-07T08:00:00"
        },
        {
            read: true,
            write: true,
            delete: false
        }
    );

    console.log(resource);

    // Generic-style repository
    console.log("\nREPOSITORY");

    const repository = new Repository();
    repository.add(user.id, user);

    console.log("Count:", repository.size);

    // Asynchronous workflow
    console.log("\nASYNC WORKFLOW");

    const loadedUser = await loadUser(repository, 101);
    console.log("Loaded:", loadedUser.profile.displayName);

    // Events
    console.log("\nEVENT-DRIVEN WORKFLOW");

    const bus = new EventBus();

    const unsubscribe = bus.subscribe("user.updated", event => {
        console.log("User updated:", event.id, event.role);
    });

    bus.emit("user.updated", {
        id: 101,
        role: UserRole.DEVELOPER
    });

    unsubscribe();

    // Failure handling
    console.log("\nVALIDATION");

    const invalidInputs = [
        () => normalizeIdentifier(0),
        () => createCoordinate(100, 20),
        () => analyzeScores([]),
        () => repository.add(101, user),
        () => handleApiResult({ kind: "unknown" })
    ];

    for (const operation of invalidInputs) {
        try {
            operation();
        } catch (error) {
            console.log("Expected error:", error.message);
        }
    }

    console.log("\nExecution completed.");
}

main().catch(error => {
    console.error("Application failure:", error.message);
    process.exitCode = 1;
});
