/**
 * TypeScript Introduction
 * Why TypeScript, Type Annotations, Primitive Types, and Type Inference
 *
 * Node.js implementation of a configuration and account-management
 * service using JavaScript runtime validation.
 *
 * Run:
 * node typescript_introduction.js
 */

"use strict";

const fs = require("node:fs/promises");
const path = require("node:path");
const { EventEmitter } = require("node:events");
const { randomUUID } = require("node:crypto");


class ValidationError extends Error {
    constructor(message) {
        super(message);
        this.name = "ValidationError";
    }
}


const PrimitiveType = Object.freeze({
    STRING: "string",
    NUMBER: "number",
    BOOLEAN: "boolean",
    BIGINT: "bigint",
    SYMBOL: "symbol",
    UNDEFINED: "undefined"
});


function inferType(value) {
    if (value === null) {
        return "null";
    }

    if (Array.isArray(value)) {
        return "array";
    }

    if (Number.isNaN(value)) {
        return "NaN";
    }

    return typeof value;
}


function validatePrimitive(value, expectedType, options = {}) {
    const { nullable = false } = options;

    if (value === null) {
        return nullable;
    }

    if (!Object.values(PrimitiveType).includes(expectedType)) {
        throw new ValidationError(
            `Unsupported type: ${expectedType}`
        );
    }

    if (expectedType === PrimitiveType.NUMBER) {
        return typeof value === "number" &&
            Number.isFinite(value);
    }

    return typeof value === expectedType;
}


function validateEmail(email) {
    if (typeof email !== "string") {
        throw new ValidationError("Email must be a string.");
    }

    const normalized = email.trim().toLowerCase();

    const pattern =
        /^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/;

    if (!pattern.test(normalized)) {
        throw new ValidationError("Invalid email address.");
    }

    return normalized;
}


class Account {
    #id;
    #name;
    #email;
    #age;
    #status;
    #metadata;

    constructor({
        id,
        name,
        email,
        age,
        metadata = {}
    }) {
        if (typeof id !== "string" || id.length === 0) {
            throw new ValidationError("Account ID is required.");
        }

        if (typeof name !== "string" || !name.trim()) {
            throw new ValidationError("Name is required.");
        }

        if (!Number.isInteger(age) || age < 18 || age > 120) {
            throw new ValidationError(
                "Age must be an integer between 18 and 120."
            );
        }

        if (
            metadata === null ||
            typeof metadata !== "object" ||
            Array.isArray(metadata)
        ) {
            throw new ValidationError(
                "Metadata must be a plain object."
            );
        }

        const safeMetadata = {};

        for (const [key, value] of Object.entries(metadata)) {
            if (
                ![
                    "string",
                    "number",
                    "boolean"
                ].includes(typeof value) &&
                value !== null
            ) {
                throw new ValidationError(
                    `Unsupported metadata value: ${key}`
                );
            }

            if (
                typeof value === "number" &&
                !Number.isFinite(value)
            ) {
                throw new ValidationError(
                    `Metadata number must be finite: ${key}`
                );
            }

            safeMetadata[key] = value;
        }

        this.#id = id;
        this.#name = name.trim();
        this.#email = validateEmail(email);
        this.#age = age;
        this.#status = "ACTIVE";
        this.#metadata = Object.freeze(safeMetadata);
    }

    get id() {
        return this.#id;
    }

    get name() {
        return this.#name;
    }

    get email() {
        return this.#email;
    }

    get age() {
        return this.#age;
    }

    get status() {
        return this.#status;
    }

    get metadata() {
        return this.#metadata;
    }

    deactivate() {
        if (this.#status === "SUSPENDED") {
            throw new ValidationError(
                "Suspended accounts cannot be deactivated."
            );
        }

        this.#status = "INACTIVE";
    }

    suspend() {
        this.#status = "SUSPENDED";
    }

    toJSON() {
        return {
            id: this.#id,
            name: this.#name,
            email: this.#email,
            age: this.#age,
            status: this.#status,
            metadata: this.#metadata
        };
    }
}


class AccountService extends EventEmitter {
    #accounts = new Map();
    #emailIndex = new Map();

    register(account) {
        if (!(account instanceof Account)) {
            throw new ValidationError(
                "Expected an Account instance."
            );
        }

        if (this.#accounts.has(account.id)) {
            throw new ValidationError(
                "Account ID already exists."
            );
        }

        if (this.#emailIndex.has(account.email)) {
            throw new ValidationError(
                "Email already registered."
            );
        }

        this.#accounts.set(account.id, account);
        this.#emailIndex.set(account.email, account.id);

        this.emit("account:registered", {
            accountId: account.id,
            timestamp: new Date().toISOString()
        });

        return account;
    }

    findById(id) {
        return this.#accounts.get(id) ?? null;
    }

    findByEmail(email) {
        const normalized = validateEmail(email);
        const id = this.#emailIndex.get(normalized);

        return id ? this.findById(id) : null;
    }

    deactivate(id) {
        const account = this.findById(id);

        if (!account) {
            throw new ValidationError("Account not found.");
        }

        account.deactivate();

        this.emit("account:deactivated", {
            accountId: id
        });
    }

    listActive() {
        return [...this.#accounts.values()].filter(
            account => account.status === "ACTIVE"
        );
    }

    get statistics() {
        const counts = {
            ACTIVE: 0,
            INACTIVE: 0,
            SUSPENDED: 0
        };

        for (const account of this.#accounts.values()) {
            counts[account.status]++;
        }

        return Object.freeze({
            total: this.#accounts.size,
            ...counts
        });
    }
}


class ConfigurationService {
    #configuration;

    constructor(configuration) {
        const schema = {
            applicationName: "string",
            port: "number",
            debug: "boolean",
            environment: "string"
        };

        for (const [key, type] of Object.entries(schema)) {
            if (!validatePrimitive(configuration[key], type)) {
                throw new ValidationError(
                    `Invalid configuration property: ${key}`
                );
            }
        }

        if (
            !Number.isInteger(configuration.port) ||
            configuration.port < 1 ||
            configuration.port > 65535
        ) {
            throw new ValidationError("Invalid network port.");
        }

        if (
            !["development", "testing", "production"].includes(
                configuration.environment
            )
        ) {
            throw new ValidationError(
                "Unsupported environment."
            );
        }

        this.#configuration = Object.freeze({
            ...configuration
        });
    }

    getConfiguration() {
        return this.#configuration;
    }
}


async function exportAccounts(accounts, destination) {
    const absolutePath = path.resolve(destination);

    const content = JSON.stringify(
        accounts.map(account => account.toJSON()),
        null,
        2
    );

    // Write to a temporary file before replacing the destination.
    const temporaryPath = `${absolutePath}.${randomUUID()}.tmp`;

    try {
        await fs.writeFile(
            temporaryPath,
            content,
            {
                encoding: "utf8",
                flag: "wx",
                mode: 0o600
            }
        );

        await fs.rename(temporaryPath, absolutePath);

    } catch (error) {
        await fs.rm(temporaryPath, { force: true }).catch(() => {});
        throw new Error(`Account export failed: ${error.message}`);
    }
}


function demonstrateTypeInference() {
    console.log("\nTYPE INFERENCE");

    const username = "Atul";
    const accountAge = 29;
    const balance = 15000.75;
    const verified = true;
    const optionalValue = null;
    const identifiers = ["A101", "A102"];

    const variables = {
        username,
        accountAge,
        balance,
        verified,
        optionalValue,
        identifiers
    };

    for (const [name, value] of Object.entries(variables)) {
        console.log(`${name}: ${inferType(value)}`);
    }
}


function demonstratePrimitiveTypes() {
    console.log("\nPRIMITIVE TYPES");

    const tests = [
        ["hello", "string"],
        [100, "number"],
        [true, "boolean"],
        [100n, "bigint"],
        [Symbol("id"), "symbol"],
        [undefined, "undefined"],
        [null, "string"]
    ];

    for (const [value, expected] of tests) {
        console.log(
            `${String(value)} => ${expected}: ` +
            validatePrimitive(value, expected, {
                nullable: false
            })
        );
    }

    console.log(
        "Nullable string:",
        validatePrimitive(null, "string", {
            nullable: true
        })
    );
}


async function main() {
    demonstrateTypeInference();
    demonstratePrimitiveTypes();

    console.log("\nACCOUNT MANAGEMENT");

    const service = new AccountService();

    service.on("account:registered", event => {
        console.log("Registration event:", event);
    });

    service.on("account:deactivated", event => {
        console.log("Deactivation event:", event);
    });

    const first = new Account({
        id: "USR-001",
        name: "Atul Pandey",
        email: "ATUL@example.com",
        age: 29,
        metadata: {
            department: "Engineering",
            verified: true,
            experience: 5
        }
    });

    const second = new Account({
        id: "USR-002",
        name: "Riya Sharma",
        email: "riya@example.com",
        age: 31
    });

    service.register(first);
    service.register(second);

    console.log(
        "Email lookup:",
        service.findByEmail("atul@example.com")?.name
    );

    service.deactivate("USR-002");

    console.log("Statistics:", service.statistics);

    console.log("\nCONFIGURATION VALIDATION");

    const configuration = new ConfigurationService({
        applicationName: "TypeSafeRegistry",
        port: 8080,
        debug: false,
        environment: "production"
    });

    console.log(configuration.getConfiguration());

    try {
        new ConfigurationService({
            applicationName: "InvalidService",
            port: "8080",
            debug: false,
            environment: "production"
        });
    } catch (error) {
        console.error("Configuration rejected:", error.message);
    }

    try {
        service.register(first);
    } catch (error) {
        console.error("Duplicate rejected:", error.message);
    }

    console.log("\nASYNCHRONOUS EXPORT");

    const exportPath = path.join(
        process.cwd(),
        "typescript-introduction-users.json"
    );

    await exportAccounts(
        [first, second],
        exportPath
    );

    console.log("Export completed:", exportPath);

    console.log("\nALL OPERATIONS COMPLETED");
}


main().catch(error => {
    console.error("Application failure:", error.message);
    process.exitCode = 1;
});
