"use strict";

/**
 * TypeScript Architecture: Event-driven module and policy analyzer.
 *
 * Covers:
 * - Runtime interface contract validation.
 * - Module registration and export resolution.
 * - Declaration-file metadata.
 * - Dependency graph analysis.
 * - Circular dependency detection.
 * - Strict TypeScript compiler settings.
 * - Configuration policy evaluation.
 * - Asynchronous project validation.
 *
 * Runtime: Node.js 20+
 * Dependencies: None.
 */

const fs = require("node:fs/promises");
const path = require("node:path");
const EventEmitter = require("node:events");

class ArchitectureError extends Error {
    constructor(message, code = "ARCHITECTURE_ERROR") {
        super(message);
        this.name = "ArchitectureError";
        this.code = code;
    }
}

class ContractError extends ArchitectureError {
    constructor(message) {
        super(message, "CONTRACT_ERROR");
        this.name = "ContractError";
    }
}

class ConfigurationError extends ArchitectureError {
    constructor(message) {
        super(message, "CONFIGURATION_ERROR");
        this.name = "ConfigurationError";
    }
}

class ModuleRegistry {
    #modules = new Map();

    register(moduleDefinition) {
        const {
            name,
            file,
            kind = "esm",
            exports = [],
            imports = [],
            interfaces = [],
        } = moduleDefinition;

        if (!name || !file) {
            throw new ArchitectureError(
                "Module name and file path are required."
            );
        }

        if (this.#modules.has(name)) {
            throw new ArchitectureError(
                `Duplicate module: ${name}`
            );
        }

        const allowedKinds = new Set([
            "esm",
            "commonjs",
            "declaration",
            "ambient",
        ]);

        if (!allowedKinds.has(kind)) {
            throw new ArchitectureError(
                `Unsupported module kind: ${kind}`
            );
        }

        this.#modules.set(name, Object.freeze({
            name,
            file,
            kind,
            exports: new Set(exports),
            imports: new Set(imports),
            interfaces: new Set(interfaces),
        }));
    }

    get(name) {
        return this.#modules.get(name);
    }

    values() {
        return [...this.#modules.values()];
    }

    resolveImport(source, target) {
        const sourceModule = this.get(source);
        const targetModule = this.get(target);

        if (!sourceModule || !targetModule) {
            throw new ArchitectureError(
                `Cannot resolve ${source} -> ${target}`,
                "UNRESOLVED_MODULE"
            );
        }

        return targetModule;
    }

    resolveExport(moduleName, symbol) {
        const moduleDefinition = this.get(moduleName);

        if (!moduleDefinition) {
            throw new ArchitectureError(
                `Unknown module: ${moduleName}`
            );
        }

        if (!moduleDefinition.exports.has(symbol)) {
            throw new ArchitectureError(
                `${symbol} is not exported by ${moduleName}`,
                "UNEXPORTED_SYMBOL"
            );
        }

        return symbol;
    }
}

class InterfaceContract {
    constructor(name, properties, parents = []) {
        if (!name || !Array.isArray(properties)) {
            throw new ContractError(
                "Invalid interface definition."
            );
        }

        this.name = name;
        this.parents = [...parents];
        this.properties = new Map();

        for (const property of properties) {
            if (
                !property.name ||
                !property.type ||
                this.properties.has(property.name)
            ) {
                throw new ContractError(
                    `Invalid or duplicate property in ${name}.`
                );
            }

            this.properties.set(property.name, Object.freeze({
                name: property.name,
                type: property.type,
                optional: Boolean(property.optional),
                readonly: Boolean(property.readonly),
            }));
        }
    }
}

class ContractRegistry {
    #contracts = new Map();

    register(contract) {
        if (this.#contracts.has(contract.name)) {
            throw new ContractError(
                `Contract already exists: ${contract.name}`
            );
        }

        this.#contracts.set(contract.name, contract);
    }

    resolve(name, visiting = new Set()) {
        const contract = this.#contracts.get(name);

        if (!contract) {
            throw new ContractError(
                `Unknown interface: ${name}`
            );
        }

        if (visiting.has(name)) {
            throw new ContractError(
                `Circular interface inheritance at ${name}`
            );
        }

        const nextVisiting = new Set(visiting);
        nextVisiting.add(name);

        const properties = new Map();

        for (const parentName of contract.parents) {
            const inherited = this.resolve(
                parentName,
                nextVisiting
            );

            for (const [key, value] of inherited) {
                properties.set(key, value);
            }
        }

        for (const [key, value] of contract.properties) {
            const inherited = properties.get(key);

            if (
                inherited &&
                inherited.type !== value.type
            ) {
                throw new ContractError(
                    `Conflicting inherited property: ${key}`
                );
            }

            properties.set(key, value);
        }

        return properties;
    }

    validate(name, implementation) {
        const contract = this.resolve(name);
        const errors = [];

        if (
            implementation === null ||
            typeof implementation !== "object"
        ) {
            throw new ContractError(
                "Implementation must be an object."
            );
        }

        for (const [propertyName, property] of contract) {
            if (
                !Object.prototype.hasOwnProperty.call(
                    implementation,
                    propertyName
                )
            ) {
                if (!property.optional) {
                    errors.push(
                        `Missing property: ${propertyName}`
                    );
                }
                continue;
            }

            const actual = implementation[propertyName];

            if (
                actual === null &&
                !property.optional &&
                property.type !== "null"
            ) {
                errors.push(
                    `${propertyName} cannot be null.`
                );
            }
        }

        return errors;
    }
}

class DependencyAnalyzer {
    constructor(registry) {
        this.registry = registry;
    }

    analyze() {
        const modules = this.registry.values();
        const graph = new Map();
        const diagnostics = [];

        for (const module of modules) {
            graph.set(module.name, new Set());
        }

        for (const module of modules) {
            for (const dependency of module.imports) {
                if (!graph.has(dependency)) {
                    diagnostics.push({
                        severity: "error",
                        code: "MODULE001",
                        message:
                            `${module.name} imports unknown module ${dependency}`,
                    });
                    continue;
                }

                graph.get(module.name).add(dependency);
            }
        }

        const state = new Map();
        const stack = [];
        const cycles = [];

        const visit = (node) => {
            const currentState = state.get(node) || 0;

            if (currentState === 2) return;

            if (currentState === 1) {
                const start = stack.indexOf(node);
                cycles.push([
                    ...stack.slice(start),
                    node,
                ]);
                return;
            }

            state.set(node, 1);
            stack.push(node);

            for (const dependency of graph.get(node)) {
                visit(dependency);
            }

            stack.pop();
            state.set(node, 2);
        };

        for (const node of graph.keys()) {
            visit(node);
        }

        for (const cycle of cycles) {
            diagnostics.push({
                severity: "error",
                code: "MODULE002",
                message:
                    `Circular dependency: ${cycle.join(" -> ")}`,
            });
        }

        return { graph, diagnostics, cycles };
    }

    topologicalOrder(graph) {
        const indegree = new Map();

        for (const node of graph.keys()) {
            indegree.set(node, 0);
        }

        for (const dependencies of graph.values()) {
            for (const dependency of dependencies) {
                indegree.set(
                    dependency,
                    indegree.get(dependency) + 1
                );
            }
        }

        const queue = [];

        for (const [node, degree] of indegree) {
            if (degree === 0) queue.push(node);
        }

        const result = [];

        while (queue.length) {
            const current = queue.shift();
            result.push(current);

            for (const dependency of graph.get(current)) {
                const updated = indegree.get(dependency) - 1;
                indegree.set(dependency, updated);

                if (updated === 0) queue.push(dependency);
            }
        }

        if (result.length !== graph.size) {
            throw new ArchitectureError(
                "Topological ordering is impossible because the graph contains a cycle."
            );
        }

        return result;
    }
}

class TypeScriptConfiguration {
    constructor() {
        this.compilerOptions = {
            target: "ES2022",
            module: "NodeNext",
            moduleResolution: "NodeNext",
            strict: true,
            strictNullChecks: true,
            noImplicitAny: true,
            strictFunctionTypes: true,
            strictPropertyInitialization: true,
            noImplicitOverride: true,
            noUnusedLocals: true,
            noUnusedParameters: true,
            noFallthroughCasesInSwitch: true,
            noUncheckedIndexedAccess: true,
            exactOptionalPropertyTypes: true,
            declaration: true,
            declarationMap: true,
            sourceMap: true,
            esModuleInterop: true,
            forceConsistentCasingInFileNames: true,
            skipLibCheck: false,
            rootDir: "./src",
            outDir: "./dist",
            baseUrl: ".",
            paths: {
                "@domain/*": ["src/domain/*"],
                "@services/*": ["src/services/*"],
            },
        };

        this.include = ["src/**/*.ts"];
        this.exclude = ["node_modules", "dist"];
    }

    validate() {
        const options = this.compilerOptions;

        if (
            options.strict &&
            (
                !options.strictNullChecks ||
                !options.noImplicitAny ||
                !options.strictFunctionTypes ||
                !options.strictPropertyInitialization
            )
        ) {
            throw new ConfigurationError(
                "Strict mode conflicts with disabled strict checks."
            );
        }

        if (options.rootDir === options.outDir) {
            throw new ConfigurationError(
                "rootDir and outDir must differ."
            );
        }

        if (!this.include.length) {
            throw new ConfigurationError(
                "At least one include pattern is required."
            );
        }

        return true;
    }

    toJSON() {
        this.validate();

        return {
            compilerOptions: this.compilerOptions,
            include: this.include,
            exclude: this.exclude,
        };
    }
}

class ArchitectureEngine extends EventEmitter {
    constructor() {
        super();

        this.modules = new ModuleRegistry();
        this.contracts = new ContractRegistry();
        this.configuration = new TypeScriptConfiguration();
        this.analyzer = new DependencyAnalyzer(this.modules);
        this.running = false;
    }

    async validateProject() {
        if (this.running) {
            throw new ArchitectureError(
                "A validation run is already active."
            );
        }

        this.running = true;

        try {
            this.emit("validationStarted");

            // Independent validation stages run concurrently.
            const [dependencyResult, configurationResult] =
                await Promise.all([
                    Promise.resolve().then(
                        () => this.analyzer.analyze()
                    ),
                    Promise.resolve().then(
                        () => this.configuration.validate()
                    ),
                ]);

            const diagnostics = [
                ...dependencyResult.diagnostics,
            ];

            for (const module of this.modules.values()) {
                for (const contractName of module.interfaces) {
                    try {
                        this.contracts.resolve(contractName);
                    } catch (error) {
                        diagnostics.push({
                            severity: "error",
                            code: "TYPE001",
                            message:
                                `${module.name}: ${error.message}`,
                        });
                    }
                }
            }

            const report = Object.freeze({
                valid: diagnostics.every(
                    item => item.severity !== "error"
                ),
                diagnostics,
                moduleCount: this.modules.values().length,
                configurationValid: configurationResult,
                checkedAt: new Date().toISOString(),
            });

            this.emit("validationCompleted", report);

            return report;
        } catch (error) {
            this.emit("validationFailed", error);
            throw error;
        } finally {
            this.running = false;
        }
    }

    async exportConfiguration(directory) {
        const config = this.configuration.toJSON();

        const absoluteDirectory = path.resolve(directory);
        await fs.mkdir(absoluteDirectory, {
            recursive: true,
        });

        const destination = path.join(
            absoluteDirectory,
            "tsconfig.json"
        );

        await fs.writeFile(
            destination,
            JSON.stringify(config, null, 2),
            {
                encoding: "utf8",
                flag: "w",
                mode: 0o600,
            }
        );

        return destination;
    }
}

function buildExample() {
    const engine = new ArchitectureEngine();

    const entity = new InterfaceContract(
        "Entity",
        [
            {
                name: "id",
                type: "string",
                readonly: true,
            },
        ]
    );

    const user = new InterfaceContract(
        "User",
        [
            { name: "email", type: "string" },
            { name: "displayName", type: "string" },
            {
                name: "phone",
                type: "string",
                optional: true,
            },
        ],
        ["Entity"]
    );

    engine.contracts.register(entity);
    engine.contracts.register(user);

    engine.modules.register({
        name: "domain",
        file: "src/domain/user.ts",
        exports: ["Entity", "User"],
        interfaces: ["Entity", "User"],
    });

    engine.modules.register({
        name: "infrastructure",
        file: "src/infrastructure/user-repository.ts",
        imports: ["domain"],
        exports: ["PostgresUserRepository"],
    });

    engine.modules.register({
        name: "services",
        file: "src/services/user-service.ts",
        imports: ["domain", "infrastructure"],
        exports: ["UserService"],
        interfaces: ["User"],
    });

    engine.modules.register({
        name: "api",
        file: "src/api/server.ts",
        imports: ["services"],
        exports: ["startServer"],
    });

    return engine;
}

async function runTests() {
    const registry = new ContractRegistry();

    registry.register(
        new InterfaceContract("Base", [
            { name: "id", type: "string" },
        ])
    );

    registry.register(
        new InterfaceContract("Child", [
            { name: "name", type: "string" },
        ], ["Base"])
    );

    const valid = registry.validate("Child", {
        id: "U-101",
        name: "Developer",
    });

    const invalid = registry.validate("Child", {
        id: "U-101",
    });

    if (valid.length !== 0 || invalid.length !== 1) {
        throw new Error("Interface contract test failed.");
    }

    const badConfig = new TypeScriptConfiguration();
    badConfig.compilerOptions.strictNullChecks = false;

    let configurationRejected = false;

    try {
        badConfig.validate();
    } catch (error) {
        configurationRejected =
            error instanceof ConfigurationError;
    }

    if (!configurationRejected) {
        throw new Error("Strict configuration test failed.");
    }

    console.log("All JavaScript architecture tests passed.");
}

async function main() {
    await runTests();

    const engine = buildExample();

    engine.on("validationStarted", () => {
        console.log("\nArchitecture validation started.");
    });

    engine.on("validationCompleted", report => {
        console.log("\nARCHITECTURE REPORT");
        console.log(JSON.stringify(report, null, 2));
    });

    engine.on("validationFailed", error => {
        console.error("Validation failed:", error.message);
    });

    const report = await engine.validateProject();

    const graphResult = engine.analyzer.analyze();

    if (graphResult.cycles.length === 0) {
        const order = engine.analyzer.topologicalOrder(
            graphResult.graph
        );

        console.log("\nMODULE BUILD ORDER");
        order.forEach((module, index) => {
            console.log(`${index + 1}. ${module}`);
        });
    }

    const outputPath = await engine.exportConfiguration(
        "./typescript_architecture_output"
    );

    console.log(`\nConfiguration written to ${outputPath}`);

    const contractErrors = engine.contracts.validate(
        "User",
        {
            id: "USR-101",
            email: "developer@example.com",
            displayName: "Development User",
        }
    );

    console.log(
        "\nUser interface:",
        contractErrors.length === 0 ? "VALID" : "INVALID"
    );

    if (!report.valid) {
        process.exitCode = 1;
    }
}

main().catch(error => {
    console.error(
        `[${error.code || "RUNTIME_ERROR"}] ${error.message}`
    );
    process.exitCode = 1;
});
