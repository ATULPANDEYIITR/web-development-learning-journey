"use strict";

/*
 * Package Management Policy Engine
 *
 * Node.js implementation covering:
 * - package.json inspection
 * - npm dependency classification
 * - semantic versioning
 * - dependency policies
 * - script lifecycle
 * - package-lock validation
 * - production installation policies
 * - asynchronous package audit events
 * - dependency inventory and reporting
 */

const fs = require("node:fs");
const path = require("node:path");
const { EventEmitter } = require("node:events");
const crypto = require("node:crypto");

class PackagePolicyError extends Error {
    constructor(message) {
        super(message);
        this.name = "PackagePolicyError";
    }
}

function parseVersion(value) {
    if (typeof value !== "string") {
        throw new PackagePolicyError("Version must be a string.");
    }

    const match = value.match(
        /^v?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-([0-9A-Za-z.-]+))?(?:\+[0-9A-Za-z.-]+)?$/
    );

    if (!match) {
        throw new PackagePolicyError(`Invalid version: ${value}`);
    }

    return {
        major: Number(match[1]),
        minor: Number(match[2]),
        patch: Number(match[3]),
        prerelease: match[4] || null
    };
}

function compareVersions(a, b) {
    for (const key of ["major", "minor", "patch"]) {
        if (a[key] !== b[key]) {
            return a[key] < b[key] ? -1 : 1;
        }
    }

    if (a.prerelease && !b.prerelease) return -1;
    if (!a.prerelease && b.prerelease) return 1;

    return String(a.prerelease || "").localeCompare(
        String(b.prerelease || "")
    );
}

function satisfies(versionText, expression) {
    const version = parseVersion(versionText);
    const range = expression.trim();

    if (range === "*" || range === "latest") return true;

    const operator = range[0];

    if (operator === "^" || operator === "~") {
        const base = parseVersion(range.slice(1));

        if (compareVersions(version, base) < 0) return false;

        if (operator === "~") {
            return (
                version.major === base.major &&
                version.minor === base.minor
            );
        }

        if (base.major > 0) {
            return version.major === base.major;
        }

        if (base.minor > 0) {
            return version.major === 0 &&
                version.minor === base.minor;
        }

        return version.major === 0 &&
            version.minor === 0 &&
            version.patch === base.patch;
    }

    const match = range.match(/^(>=|<=|>|<|=)?\s*(.+)$/);

    if (!match) {
        throw new PackagePolicyError(`Invalid range: ${range}`);
    }

    const expected = parseVersion(match[2]);
    const comparison = compareVersions(version, expected);

    switch (match[1] || "=") {
        case ">=": return comparison >= 0;
        case "<=": return comparison <= 0;
        case ">": return comparison > 0;
        case "<": return comparison < 0;
        case "=": return comparison === 0;
        default: throw new PackagePolicyError("Unsupported operator.");
    }
}

class PackageManifest {
    constructor(data) {
        if (!data || typeof data !== "object" || Array.isArray(data)) {
            throw new PackagePolicyError("Invalid package.json object.");
        }

        this.name = data.name;
        this.version = data.version;
        this.dependencies = new Map(
            Object.entries(data.dependencies || {})
        );
        this.devDependencies = new Map(
            Object.entries(data.devDependencies || {})
        );
        this.optionalDependencies = new Map(
            Object.entries(data.optionalDependencies || {})
        );
        this.peerDependencies = new Map(
            Object.entries(data.peerDependencies || {})
        );
        this.scripts = new Map(
            Object.entries(data.scripts || {})
        );
        this.engines = data.engines || {};

        this.validate();
    }

    validate() {
        if (
            typeof this.name !== "string" ||
            !/^(?:@[a-z0-9._-]+\/)?[a-z0-9._-]+$/.test(this.name) ||
            this.name.length > 214 ||
            this.name.startsWith(".") ||
            this.name.startsWith("_")
        ) {
            throw new PackagePolicyError("Invalid npm package name.");
        }

        parseVersion(this.version);

        for (const collection of [
            this.dependencies,
            this.devDependencies,
            this.optionalDependencies,
            this.peerDependencies
        ]) {
            for (const [name, range] of collection) {
                if (
                    !name ||
                    typeof range !== "string" ||
                    !range.trim()
                ) {
                    throw new PackagePolicyError(
                        "Invalid dependency declaration."
                    );
                }
            }
        }

        for (const [name, command] of this.scripts) {
            if (!name || typeof command !== "string" || !command.trim()) {
                throw new PackagePolicyError(
                    `Invalid npm script: ${name}`
                );
            }
        }
    }

    inventory() {
        return {
            production: [...this.dependencies.keys()],
            development: [...this.devDependencies.keys()],
            optional: [...this.optionalDependencies.keys()],
            peer: [...this.peerDependencies.keys()]
        };
    }
}

class LockfileInspector {
    static inspect(manifest, lockfile) {
        if (!lockfile || !lockfile.packages) {
            throw new PackagePolicyError(
                "Unsupported or missing package-lock.json structure."
            );
        }

        const errors = [];
        const root = lockfile.packages[""];

        if (!root) {
            errors.push("Root package metadata is missing.");
        } else {
            for (const [name, range] of manifest.dependencies) {
                const installed = root.dependencies?.[name];

                if (!installed || !satisfies(installed, range)) {
                    errors.push(
                        `Production lock mismatch: ${name}@${range}`
                    );
                }
            }

            for (const [name, range] of manifest.devDependencies) {
                const installed = root.devDependencies?.[name];

                if (!installed || !satisfies(installed, range)) {
                    errors.push(
                        `Development lock mismatch: ${name}@${range}`
                    );
                }
            }
        }

        return {
            valid: errors.length === 0,
            errors
        };
    }
}

class InstallPolicy {
    constructor(options = {}) {
        this.productionOnly = options.productionOnly ?? false;
        this.allowWildcard = options.allowWildcard ?? false;
        this.requireLockfile = options.requireLockfile ?? true;
        this.allowedProtocols = new Set(
            options.allowedProtocols || ["https:"]
        );
    }

    evaluate(manifest, lockfile) {
        const violations = [];

        if (this.requireLockfile && !lockfile) {
            violations.push("A package-lock.json file is required.");
        }

        const collections = [
            manifest.dependencies,
            manifest.devDependencies
        ];

        for (const collection of collections) {
            for (const [name, range] of collection) {
                if (!this.allowWildcard && range === "*") {
                    violations.push(
                        `Unbounded dependency range: ${name}`
                    );
                }
            }
        }

        if (this.productionOnly && manifest.devDependencies.size > 0) {
            violations.push(
                "Development dependencies must not enter production."
            );
        }

        return {
            accepted: violations.length === 0,
            violations
        };
    }
}

class ScriptLifecycle extends EventEmitter {
    constructor(scripts) {
        super();
        this.scripts = scripts;
        this.executed = [];
    }

    async run(name, executor) {
        if (!this.scripts.has(name)) {
            throw new PackagePolicyError(
                `Unknown npm script: ${name}`
            );
        }

        const command = this.scripts.get(name);
        const event = {
            name,
            command,
            timestamp: new Date().toISOString()
        };

        this.emit("script:start", event);

        try {
            const result = await executor(command);

            this.executed.push({
                ...event,
                status: "SUCCESS"
            });

            this.emit("script:success", {
                ...event,
                result
            });

            return result;
        } catch (error) {
            this.executed.push({
                ...event,
                status: "FAILED",
                error: error.message
            });

            this.emit("script:failure", {
                ...event,
                error
            });

            throw error;
        }
    }
}

class DependencyAuditor {
    constructor(advisories = []) {
        this.advisories = advisories;
    }

    audit(installedPackages) {
        const findings = [];

        for (const installed of installedPackages) {
            for (const advisory of this.advisories) {
                if (installed.name !== advisory.name) continue;

                if (
                    satisfies(
                        installed.version,
                        advisory.affectedRange
                    )
                ) {
                    findings.push({
                        package: installed.name,
                        version: installed.version,
                        severity: advisory.severity,
                        advisoryId: advisory.id
                    });
                }
            }
        }

        return findings;
    }
}

function createIntegrityFingerprint(manifest, lockfile) {
    const input = JSON.stringify({
        manifest,
        lockfile
    });

    return crypto
        .createHash("sha256")
        .update(input)
        .digest("hex");
}

async function main() {
    const packageData = {
        name: "enterprise-api",
        version: "2.1.0",
        dependencies: {
            express: "^4.21.0",
            pg: "^8.13.0"
        },
        devDependencies: {
            eslint: "^9.0.0",
            jest: "^29.0.0"
        },
        scripts: {
            start: "node server.js",
            test: "jest",
            lint: "eslint .",
            build: "node build.js"
        },
        engines: {
            node: ">=20"
        }
    };

    try {
        const manifest = new PackageManifest(packageData);

        console.log("PACKAGE INVENTORY");
        console.log(manifest.inventory());

        console.log("\nSEMANTIC VERSIONING");

        for (const [version, range] of [
            ["4.21.1", "^4.21.0"],
            ["4.22.0", "~4.21.0"],
            ["5.0.0", "^4.21.0"]
        ]) {
            console.log(
                `${version} satisfies ${range}:`,
                satisfies(version, range)
            );
        }

        const lockfile = {
            name: "enterprise-api",
            lockfileVersion: 3,
            packages: {
                "": {
                    name: "enterprise-api",
                    version: "2.1.0",
                    dependencies: {
                        express: "^4.21.0",
                        pg: "^8.13.0"
                    },
                    devDependencies: {
                        eslint: "^9.0.0",
                        jest: "^29.0.0"
                    }
                },
                "node_modules/express": {
                    version: "4.21.1"
                }
            }
        };

        console.log("\nLOCKFILE INSPECTION");
        console.log(
            LockfileInspector.inspect(manifest, lockfile)
        );

        console.log("\nINSTALL POLICY");

        const policy = new InstallPolicy({
            productionOnly: false,
            allowWildcard: false,
            requireLockfile: true
        });

        console.log(policy.evaluate(manifest, lockfile));

        console.log("\nSECURITY AUDIT");

        const auditor = new DependencyAuditor([
            {
                id: "DEMO-2026-001",
                name: "express",
                affectedRange: "<4.21.1",
                severity: "HIGH"
            }
        ]);

        console.log(
            auditor.audit([
                { name: "express", version: "4.21.1" },
                { name: "pg", version: "8.13.0" }
            ])
        );

        console.log("\nSCRIPT LIFECYCLE");

        const lifecycle = new ScriptLifecycle(manifest.scripts);

        lifecycle.on("script:start", event => {
            console.log("START:", event.name);
        });

        lifecycle.on("script:success", event => {
            console.log("SUCCESS:", event.name);
        });

        lifecycle.on("script:failure", event => {
            console.error("FAILURE:", event.name);
        });

        // Demonstration executor. Production systems should use
        // reviewed commands and controlled subprocess environments.
        await lifecycle.run("test", async command => {
            if (command !== "jest") {
                throw new PackagePolicyError("Unexpected test command.");
            }
            return "Tests completed successfully.";
        });

        console.log("\nEXECUTION HISTORY");
        console.log(lifecycle.executed);

        console.log("\nINTEGRITY FINGERPRINT");
        console.log(
            createIntegrityFingerprint(packageData, lockfile)
        );

        console.log("\nAll package management checks completed.");

    } catch (error) {
        console.error(
            `${error.name}: ${error.message}`
        );
        process.exitCode = 1;
    }
}

if (require.main === module) {
    main();
}

module.exports = {
    parseVersion,
    compareVersions,
    satisfies,
    PackageManifest,
    LockfileInspector,
    InstallPolicy,
    ScriptLifecycle,
    DependencyAuditor,
    createIntegrityFingerprint
};
