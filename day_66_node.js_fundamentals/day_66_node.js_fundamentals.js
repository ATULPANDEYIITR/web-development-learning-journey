"use strict";

/*
 * Node.js Fundamentals
 *
 * Demonstrates:
 * - Node.js runtime and process lifecycle
 * - CommonJS module system
 * - Built-in and application modules
 * - Filesystem operations
 * - Asynchronous programming
 * - EventEmitter
 * - Environment variables
 * - Configuration validation
 * - Graceful shutdown and error handling
 *
 * Requirements: Node.js 18+
 * Run: node node_fundamentals.js
 */

const fs = require("node:fs");
const fsp = require("node:fs/promises");
const path = require("node:path");
const os = require("node:os");
const crypto = require("node:crypto");
const process = require("node:process");
const EventEmitter = require("node:events");

const APP_NAME = "inventory-runtime";
const REQUIRED_NODE_MAJOR = 18;

class ApplicationError extends Error {
    constructor(message, code = "APPLICATION_ERROR") {
        super(message);
        this.name = "ApplicationError";
        this.code = code;
    }
}

class Configuration {
    constructor(environment = process.env) {
        this.environment = environment;
    }

    getString(name, defaultValue = undefined) {
        const value = this.environment[name];

        if (value === undefined || value.trim() === "") {
            if (defaultValue !== undefined) {
                return defaultValue;
            }

            throw new ApplicationError(
                `Missing environment variable: ${name}`,
                "CONFIGURATION_MISSING"
            );
        }

        return value.trim();
    }

    getInteger(name, defaultValue, min, max) {
        const raw = this.environment[name];

        if (raw === undefined) {
            return defaultValue;
        }

        if (!/^-?\d+$/.test(raw.trim())) {
            throw new ApplicationError(
                `${name} must be an integer.`,
                "CONFIGURATION_INVALID"
            );
        }

        const value = Number(raw);

        if (!Number.isSafeInteger(value) || value < min || value > max) {
            throw new ApplicationError(
                `${name} must be between ${min} and ${max}.`,
                "CONFIGURATION_OUT_OF_RANGE"
            );
        }

        return value;
    }

    getMode() {
        const mode = this.getString("NODE_ENV", "development");
        const allowed = new Set([
            "development",
            "test",
            "production"
        ]);

        if (!allowed.has(mode)) {
            throw new ApplicationError(
                `Unsupported NODE_ENV: ${mode}`
            );
        }

        return mode;
    }

    validateDatabaseUrl() {
        const value = this.getString("DATABASE_URL");

        let parsed;

        try {
            parsed = new URL(value);
        } catch {
            throw new ApplicationError(
                "DATABASE_URL is not a valid URL."
            );
        }

        if (!["postgres:", "postgresql:"].includes(parsed.protocol)) {
            throw new ApplicationError(
                "Only PostgreSQL connection URLs are supported."
            );
        }

        return parsed;
    }
}

class ModuleRegistry {
    constructor() {
        this.modules = new Map();
    }

    register(name, exportedValue) {
        if (this.modules.has(name)) {
            throw new ApplicationError(
                `Module already registered: ${name}`
            );
        }

        this.modules.set(name, exportedValue);
    }

    import(name) {
        if (!this.modules.has(name)) {
            throw new ApplicationError(
                `Application module not found: ${name}`,
                "MODULE_NOT_FOUND"
            );
        }

        return this.modules.get(name);
    }

    list() {
        return [...this.modules.keys()].sort();
    }
}

class FileRepository {
    constructor(directory) {
        this.root = path.resolve(directory);
    }

    resolve(relativePath) {
        if (
            typeof relativePath !== "string" ||
            relativePath.trim() === ""
        ) {
            throw new ApplicationError("Invalid filesystem path.");
        }

        const target = path.resolve(this.root, relativePath);
        const relative = path.relative(this.root, target);

        if (
            relative === ".." ||
            relative.startsWith(`..${path.sep}`) ||
            path.isAbsolute(relative)
        ) {
            throw new ApplicationError(
                "Filesystem path escapes application directory.",
                "PATH_TRAVERSAL"
            );
        }

        return target;
    }

    async initialize() {
        await fsp.mkdir(this.root, { recursive: true });
    }

    async writeJson(relativePath, data) {
        const target = this.resolve(relativePath);

        await fsp.mkdir(path.dirname(target), {
            recursive: true
        });

        const temporary = `${target}.${crypto.randomUUID()}.tmp`;

        try {
            await fsp.writeFile(
                temporary,
                JSON.stringify(data, null, 2),
                {
                    encoding: "utf8",
                    flag: "wx",
                    mode: 0o600
                }
            );

            await fsp.rename(temporary, target);
        } catch (error) {
            await fsp.rm(temporary, { force: true }).catch(() => {});
            throw error;
        }

        return target;
    }

    async readJson(relativePath) {
        const target = this.resolve(relativePath);
        const contents = await fsp.readFile(target, "utf8");

        try {
            return JSON.parse(contents);
        } catch {
            throw new ApplicationError(
                `Invalid JSON file: ${relativePath}`
            );
        }
    }

    async listFiles() {
        const results = [];

        async function walk(directory, root, output) {
            const entries = await fsp.readdir(directory, {
                withFileTypes: true
            });

            for (const entry of entries) {
                const absolute = path.join(directory, entry.name);

                if (entry.isSymbolicLink()) {
                    continue;
                }

                if (entry.isDirectory()) {
                    await walk(absolute, root, output);
                } else if (entry.isFile()) {
                    output.push(path.relative(root, absolute));
                }
            }
        }

        await walk(this.root, this.root, results);
        return results.sort();
    }
}

class ApplicationEvents extends EventEmitter {
    constructor() {
        super();

        this.setMaxListeners(20);

        this.on("application:started", (details) => {
            console.log("EVENT: Application started:", details.name);
        });

        this.on("file:written", (details) => {
            console.log("EVENT: File written:", details.filename);
        });

        this.on("application:error", (error) => {
            console.error("EVENT: Application error:", error.message);
        });
    }
}

class RuntimeInspector {
    static inspect() {
        const major = Number(process.versions.node.split(".")[0]);

        if (major < REQUIRED_NODE_MAJOR) {
            throw new ApplicationError(
                `Node.js ${REQUIRED_NODE_MAJOR}+ is required.`
            );
        }

        return {
            nodeVersion: process.version,
            nodeAbi: process.versions.modules,
            v8Version: process.versions.v8,
            platform: process.platform,
            architecture: process.arch,
            processId: process.pid,
            currentDirectory: process.cwd(),
            executable: process.execPath,
            memory: process.memoryUsage(),
            cpuCount: os.availableParallelism(),
            uptimeSeconds: process.uptime()
        };
    }
}

async function main() {
    const configuration = new Configuration();

    const mode = configuration.getMode();
    const port = configuration.getInteger("PORT", 3000, 1, 65535);

    const runtime = RuntimeInspector.inspect();

    console.log("\nNODE.JS RUNTIME");
    console.log(JSON.stringify(runtime, null, 2));

    console.log("\nAPPLICATION CONFIGURATION");
    console.log({
        application: APP_NAME,
        mode,
        port,
        databaseConfigured: Boolean(process.env.DATABASE_URL)
    });

    if (process.env.DATABASE_URL) {
        const databaseUrl = configuration.validateDatabaseUrl();

        // Never log the complete database URL because it can contain credentials.
        console.log("Database protocol:", databaseUrl.protocol);
        console.log("Database hostname:", databaseUrl.hostname);
    }

    console.log("\nCOMMONJS MODULE SYSTEM");

    const registry = new ModuleRegistry();

    registry.register("inventory", {
        name: "Inventory",
        version: "1.0.0"
    });

    registry.register("configuration", configuration);

    console.log("Registered modules:", registry.list());
    console.log("Imported module:", registry.import("inventory"));

    console.log("Built-in module:", typeof fs.readFileSync);
    console.log("Path module:", path.basename(process.argv[1]));
    console.log("Crypto module:", crypto.randomUUID());

    console.log("\nPROCESS ARGUMENTS");
    console.log("Node executable:", process.argv[0]);
    console.log("Application entry point:", process.argv[1]);
    console.log("Additional arguments:", process.argv.slice(2));

    console.log("\nEVENT-DRIVEN EXECUTION");

    const events = new ApplicationEvents();

    events.emit("application:started", {
        name: APP_NAME
    });

    console.log("\nASYNC FILESYSTEM OPERATIONS");

    // Use an isolated temporary directory rather than modifying project files.
    const directory = await fsp.mkdtemp(
        path.join(os.tmpdir(), "node-fundamentals-")
    );

    const files = new FileRepository(directory);

    try {
        await files.initialize();

        const record = {
            id: crypto.randomUUID(),
            name: "Industrial Sensor",
            quantity: 25,
            createdAt: new Date().toISOString()
        };

        const filename = await files.writeJson(
            "data/inventory.json",
            record
        );

        events.emit("file:written", {
            filename: path.basename(filename)
        });

        const retrieved = await files.readJson(
            "data/inventory.json"
        );

        console.log("Retrieved record:", retrieved);

        console.log("Filesystem inventory:", await files.listFiles());

        try {
            files.resolve("../../outside.json");
        } catch (error) {
            console.log("Path security validation:", error.message);
        }

        // Promise.all executes independent asynchronous reads concurrently.
        const results = await Promise.all([
            files.readJson("data/inventory.json"),
            fsp.stat(filename)
        ]);

        console.log("Concurrent operation results:", {
            recordId: results[0].id,
            fileSize: results[1].size
        });

    } finally {
        await fsp.rm(directory, {
            recursive: true,
            force: true
        });
    }

    console.log("\nENVIRONMENT VARIABLE SECURITY");

    const secretKeys = Object.keys(process.env).filter(
        key => /SECRET|PASSWORD|TOKEN|API_KEY/i.test(key)
    );

    console.log("Potential secret variable names:", secretKeys);
    console.log("Secret values are not displayed.");

    console.log("\nPROCESS MEMORY");

    const memory = process.memoryUsage();

    for (const [key, value] of Object.entries(memory)) {
        console.log(
            `${key}: ${(value / (1024 * 1024)).toFixed(2)} MB`
        );
    }

    console.log("\nAPPLICATION COMPLETED");
}

main().catch((error) => {
    console.error("APPLICATION FAILURE:", error.message);

    if (process.env.NODE_ENV !== "production") {
        console.error(error.stack);
    }

    process.exitCode = 1;
});
