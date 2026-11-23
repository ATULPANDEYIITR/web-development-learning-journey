"use strict";

/*
 * UI Engineering: Design Systems and Component Libraries.
 *
 * Event-driven JavaScript implementation featuring:
 * - Token registry and theme switching
 * - Component registration
 * - Runtime property validation
 * - Accessibility audits
 * - Component lifecycle events
 * - Dependency management
 * - Versioned component definitions
 *
 * Runtime: Node.js 18+
 */

const { EventEmitter } = require("node:events");
const crypto = require("node:crypto");

class UIEngineeringError extends Error {
    constructor(message, code = "UI_ENGINEERING_ERROR") {
        super(message);
        this.name = "UIEngineeringError";
        this.code = code;
    }
}

const ComponentState = Object.freeze({
    DRAFT: "draft",
    REVIEW: "review",
    APPROVED: "approved",
    DEPRECATED: "deprecated"
});

const TokenCategory = Object.freeze({
    COLOR: "color",
    SPACING: "spacing",
    TYPOGRAPHY: "typography",
    RADIUS: "radius",
    ELEVATION: "elevation",
    MOTION: "motion"
});

function validateIdentifier(value) {
    return typeof value === "string" &&
        /^[a-z][a-z0-9-]*(?:\.[a-z][a-z0-9-]*)*$/.test(value);
}

function validateVersion(version) {
    return typeof version === "string" &&
        /^\d+\.\d+\.\d+$/.test(version);
}

function validateColor(color) {
    return typeof color === "string" &&
        /^#[0-9a-fA-F]{6}$/.test(color);
}

function luminance(color) {
    if (!validateColor(color)) {
        throw new UIEngineeringError(
            `Invalid hexadecimal color: ${color}`,
            "INVALID_COLOR"
        );
    }

    const channels = [1, 3, 5].map(
        index => parseInt(color.slice(index, index + 2), 16) / 255
    );

    const linear = channels.map(channel =>
        channel <= 0.04045
            ? channel / 12.92
            : Math.pow((channel + 0.055) / 1.055, 2.4)
    );

    return (
        0.2126 * linear[0] +
        0.7152 * linear[1] +
        0.0722 * linear[2]
    );
}

function contrastRatio(first, second) {
    const light = Math.max(luminance(first), luminance(second));
    const dark = Math.min(luminance(first), luminance(second));

    return (light + 0.05) / (dark + 0.05);
}

class TokenRegistry extends EventEmitter {
    #tokens = new Map();
    #themes = new Map();
    #activeTheme = null;

    register(token) {
        const { name, category, value, alias = null } = token;

        if (!validateIdentifier(name)) {
            throw new UIEngineeringError("Invalid token name");
        }

        if (!Object.values(TokenCategory).includes(category)) {
            throw new UIEngineeringError("Unknown token category");
        }

        if (this.#tokens.has(name)) {
            throw new UIEngineeringError(
                `Token already exists: ${name}`,
                "DUPLICATE_TOKEN"
            );
        }

        if (typeof value !== "string" || !value.trim()) {
            throw new UIEngineeringError("Token value is required");
        }

        if (category === TokenCategory.COLOR && !alias &&
            !validateColor(value)) {
            throw new UIEngineeringError("Invalid color token");
        }

        if (alias && alias === name) {
            throw new UIEngineeringError("Self-referencing token");
        }

        const stored = Object.freeze({
            name,
            category,
            value,
            alias
        });

        this.#tokens.set(name, stored);
        this.emit("token:registered", stored);

        return stored;
    }

    resolve(name, theme = this.#activeTheme) {
        const visited = new Set();
        let current = name;

        while (true) {
            if (visited.has(current)) {
                throw new UIEngineeringError(
                    `Circular token reference: ${current}`,
                    "TOKEN_CYCLE"
                );
            }

            visited.add(current);

            const themedValue = theme
                ? this.#themes.get(theme)?.get(current)
                : undefined;

            const token = this.#tokens.get(current);

            if (!token && themedValue === undefined) {
                throw new UIEngineeringError(
                    `Unknown token: ${current}`,
                    "UNKNOWN_TOKEN"
                );
            }

            if (themedValue !== undefined) {
                return themedValue;
            }

            if (!token.alias) {
                return token.value;
            }

            current = token.alias;
        }
    }

    registerTheme(name, overrides) {
        if (!/^[a-z][a-z0-9-]*$/.test(name)) {
            throw new UIEngineeringError("Invalid theme name");
        }

        if (this.#themes.has(name)) {
            throw new UIEngineeringError("Theme already exists");
        }

        const theme = new Map();

        for (const [tokenName, value] of Object.entries(overrides)) {
            const token = this.#tokens.get(tokenName);

            if (!token) {
                throw new UIEngineeringError(
                    `Unknown theme token: ${tokenName}`
                );
            }

            if (typeof value !== "string" || !value.trim()) {
                throw new UIEngineeringError(
                    `Invalid override for ${tokenName}`
                );
            }

            if (token.category === TokenCategory.COLOR &&
                !validateColor(value)) {
                throw new UIEngineeringError(
                    `Invalid theme color: ${tokenName}`
                );
            }

            theme.set(tokenName, value);
        }

        this.#themes.set(name, theme);
        this.emit("theme:registered", name);
    }

    activateTheme(name) {
        if (!this.#themes.has(name)) {
            throw new UIEngineeringError(`Unknown theme: ${name}`);
        }

        const previous = this.#activeTheme;
        this.#activeTheme = name;

        this.emit("theme:changed", {
            previous,
            current: name
        });
    }

    get activeTheme() {
        return this.#activeTheme;
    }

    snapshot() {
        return {
            tokens: Object.fromEntries(this.#tokens),
            activeTheme: this.#activeTheme,
            themes: Object.fromEntries(
                [...this.#themes].map(([name, values]) => [
                    name,
                    Object.fromEntries(values)
                ])
            )
        };
    }
}

class ComponentDefinition {
    constructor({
        name,
        version,
        category,
        properties,
        dependencies = [],
        tokenDependencies = [],
        accessibility
    }) {
        if (!/^[A-Z][A-Za-z0-9]*$/.test(name)) {
            throw new UIEngineeringError("Invalid component name");
        }

        if (!validateVersion(version)) {
            throw new UIEngineeringError("Invalid semantic version");
        }

        if (!category) {
            throw new UIEngineeringError("Component category is required");
        }

        if (!accessibility || !accessibility.role) {
            throw new UIEngineeringError("Accessibility role is required");
        }

        this.name = name;
        this.version = version;
        this.category = category;
        this.properties = Object.freeze({ ...properties });
        this.dependencies = Object.freeze([...dependencies]);
        this.tokenDependencies = Object.freeze([...tokenDependencies]);
        this.accessibility = Object.freeze({ ...accessibility });
        this.id = crypto.randomUUID();
        this.state = ComponentState.DRAFT;
        this.createdAt = new Date().toISOString();
    }
}

class ComponentLibrary extends EventEmitter {
    #components = new Map();
    #tokens;

    constructor(tokenRegistry) {
        super();
        this.#tokens = tokenRegistry;
    }

    register(definition) {
        if (!(definition instanceof ComponentDefinition)) {
            throw new UIEngineeringError("Invalid component definition");
        }

        if (this.#components.has(definition.name)) {
            throw new UIEngineeringError(
                `Component already registered: ${definition.name}`
            );
        }

        this.#components.set(definition.name, definition);

        this.emit("component:registered", {
            name: definition.name,
            version: definition.version
        });

        return definition;
    }

    get(name) {
        const component = this.#components.get(name);

        if (!component) {
            throw new UIEngineeringError(
                `Component not found: ${name}`
            );
        }

        return component;
    }

    validateProps(name, input) {
        const component = this.get(name);
        const errors = [];

        if (!input || typeof input !== "object" || Array.isArray(input)) {
            throw new UIEngineeringError(
                "Component properties must be an object"
            );
        }

        for (const key of Object.keys(input)) {
            if (!Object.hasOwn(component.properties, key)) {
                errors.push(`Unsupported property: ${key}`);
            }
        }

        for (const [key, rule] of Object.entries(component.properties)) {
            const value = input[key];

            if (rule.required && value === undefined) {
                errors.push(`Missing required property: ${key}`);
                continue;
            }

            if (value === undefined) {
                continue;
            }

            if (rule.type === "string" && typeof value !== "string") {
                errors.push(`${key} must be a string`);
            }

            if (rule.type === "boolean" && typeof value !== "boolean") {
                errors.push(`${key} must be a boolean`);
            }

            if (rule.type === "number" &&
                (typeof value !== "number" || !Number.isFinite(value))) {
                errors.push(`${key} must be a finite number`);
            }

            if (rule.enum && !rule.enum.includes(value)) {
                errors.push(`${key} has an unsupported value`);
            }
        }

        return errors;
    }

    auditAccessibility(name, context = {}) {
        const component = this.get(name);
        const rules = component.accessibility;
        const findings = [];

        if (!rules.nameRequired && !context.accessibleName) {
            findings.push("Accessible name must be provided");
        }

        if (rules.nameRequired && !context.accessibleName) {
            findings.push("Accessible name is missing");
        }

        if (rules.keyboardRequired && !context.keyboardOperable) {
            findings.push("Keyboard operation is not supported");
        }

        if (rules.focusRequired && !context.visibleFocus) {
            findings.push("Visible focus indicator is missing");
        }

        if (context.contrastRatio !== undefined) {
            if (!Number.isFinite(context.contrastRatio) ||
                context.contrastRatio < 0 ||
                context.contrastRatio > 21) {
                findings.push("Invalid contrast ratio");
            } else if (context.contrastRatio < 4.5) {
                findings.push("Text contrast is below WCAG AA");
            }
        }

        return findings;
    }

    validateDependencies(name) {
        const component = this.get(name);
        const errors = [];

        for (const dependency of component.dependencies) {
            if (!this.#components.has(dependency)) {
                errors.push(`Missing component dependency: ${dependency}`);
            }
        }

        for (const dependency of component.tokenDependencies) {
            try {
                this.#tokens.resolve(dependency);
            } catch (error) {
                errors.push(error.message);
            }
        }

        return errors;
    }

    transition(name, nextState) {
        const component = this.get(name);

        const allowed = {
            draft: ["review"],
            review: ["draft", "approved"],
            approved: ["deprecated"],
            deprecated: []
        };

        if (!allowed[component.state].includes(nextState)) {
            throw new UIEngineeringError(
                `Invalid transition: ${component.state} -> ${nextState}`
            );
        }

        if (nextState === ComponentState.APPROVED) {
            const dependencyErrors = this.validateDependencies(name);
            const accessibilityErrors = this.auditAccessibility(
                name,
                component.accessibility.baseline || {}
            );

            if (dependencyErrors.length || accessibilityErrors.length) {
                throw new UIEngineeringError(
                    [
                        ...dependencyErrors,
                        ...accessibilityErrors
                    ].join("; "),
                    "APPROVAL_REJECTED"
                );
            }
        }

        const previous = component.state;
        component.state = nextState;

        this.emit("component:state-changed", {
            name,
            previous,
            current: nextState
        });
    }

    listByCategory(category) {
        return [...this.#components.values()]
            .filter(component => component.category === category)
            .map(component => ({
                name: component.name,
                version: component.version,
                state: component.state
            }));
    }

    auditAll() {
        const report = [];

        for (const component of this.#components.values()) {
            report.push({
                component: component.name,
                dependencyErrors: this.validateDependencies(
                    component.name
                ),
                accessibilityErrors: this.auditAccessibility(
                    component.name,
                    component.accessibility.baseline || {}
                )
            });
        }

        return report;
    }
}

async function processDesignSystem(library, componentName, properties) {
    await Promise.resolve();

    const errors = library.validateProps(componentName, properties);

    if (errors.length) {
        throw new UIEngineeringError(
            errors.join("; "),
            "PROPERTY_VALIDATION_FAILED"
        );
    }

    return {
        component: componentName,
        properties,
        renderedAt: new Date().toISOString()
    };
}

async function main() {
    const tokens = new TokenRegistry();

    tokens.on("token:registered", token => {
        console.log(`Registered token: ${token.name}`);
    });

    tokens.on("theme:changed", event => {
        console.log(
            `Theme changed: ${event.previous} -> ${event.current}`
        );
    });

    tokens.register({
        name: "color.brand.primary",
        category: TokenCategory.COLOR,
        value: "#2457C5"
    });

    tokens.register({
        name: "color.text.primary",
        category: TokenCategory.COLOR,
        value: "#172033"
    });

    tokens.register({
        name: "color.action.primary",
        category: TokenCategory.COLOR,
        value: "color.brand.primary",
        alias: "color.brand.primary"
    });

    tokens.register({
        name: "spacing.medium",
        category: TokenCategory.SPACING,
        value: "16px"
    });

    tokens.registerTheme("dark", {
        "color.brand.primary": "#8CAFFF",
        "color.text.primary": "#FFFFFF"
    });

    const library = new ComponentLibrary(tokens);

    library.on("component:registered", event => {
        console.log(`Registered component: ${event.name}`);
    });

    library.on("component:state-changed", event => {
        console.log(
            `${event.name}: ${event.previous} -> ${event.current}`
        );
    });

    library.register(new ComponentDefinition({
        name: "Button",
        version: "1.0.0",
        category: "Actions",
        properties: {
            label: { type: "string", required: true },
            variant: {
                type: "string",
                enum: ["primary", "secondary", "danger"]
            },
            disabled: { type: "boolean" }
        },
        tokenDependencies: [
            "color.action.primary",
            "spacing.medium"
        ],
        accessibility: {
            role: "button",
            nameRequired: true,
            keyboardRequired: true,
            focusRequired: true,
            baseline: {
                accessibleName: true,
                keyboardOperable: true,
                visibleFocus: true,
                contrastRatio: contrastRatio("#FFFFFF", "#2457C5")
            }
        }
    }));

    library.register(new ComponentDefinition({
        name: "IconButton",
        version: "1.0.0",
        category: "Actions",
        properties: {
            icon: { type: "string", required: true },
            label: { type: "string", required: true }
        },
        dependencies: ["Button"],
        tokenDependencies: ["color.text.primary"],
        accessibility: {
            role: "button",
            nameRequired: true,
            keyboardRequired: true,
            focusRequired: true,
            baseline: {
                accessibleName: true,
                keyboardOperable: true,
                visibleFocus: true
            }
        }
    }));

    library.transition("Button", ComponentState.REVIEW);
    library.transition("Button", ComponentState.APPROVED);

    library.transition("IconButton", ComponentState.REVIEW);
    library.transition("IconButton", ComponentState.APPROVED);

    const rendered = await processDesignSystem(
        library,
        "Button",
        {
            label: "Save changes",
            variant: "primary",
            disabled: false
        }
    );

    console.log("\nValidated component instance:");
    console.log(rendered);

    console.log("\nAccessibility audit:");
    console.log(
        library.auditAccessibility("Button", {
            accessibleName: true,
            keyboardOperable: true,
            visibleFocus: true,
            contrastRatio: contrastRatio("#FFFFFF", "#2457C5")
        })
    );

    console.log("\nTheme switching:");
    tokens.activateTheme("dark");

    console.log(
        "Primary color:",
        tokens.resolve("color.brand.primary")
    );

    console.log("\nComponent audit:");
    console.dir(library.auditAll(), { depth: null });

    console.log("\nCategory listing:");
    console.log(library.listByCategory("Actions"));

    console.log("\nRuntime failure test:");

    try {
        await processDesignSystem(library, "Button", {
            label: 42,
            variant: "unknown"
        });
    } catch (error) {
        console.log(`${error.code}: ${error.message}`);
    }
}

main().catch(error => {
    console.error("Design system execution failed:", error);
    process.exitCode = 1;
});
