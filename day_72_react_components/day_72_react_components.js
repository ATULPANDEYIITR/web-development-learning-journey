"use strict";

/*
 * React Components
 *
 * Functional components, props, composition, reusable UI,
 * state management, validation, conditional rendering,
 * component registries and event-driven interactions.
 *
 * Runtime: Node.js with React 18 or later.
 * Dependencies: react, react-dom for browser rendering.
 */

const React = require("react");
const { useState, useMemo, useCallback } = React;
const { createRoot } = require("react-dom/client");


class ComponentValidationError extends Error {
    constructor(message) {
        super(message);
        this.name = "ComponentValidationError";
    }
}

class ComponentRegistry {
    constructor() {
        this.components = new Map();
    }

    register(name, component, schema) {
        if (!/^[A-Z][A-Za-z0-9]*$/.test(name)) {
            throw new ComponentValidationError(
                `Invalid component name: ${name}`
            );
        }

        if (typeof component !== "function") {
            throw new ComponentValidationError(
                `${name} must be a functional component`
            );
        }

        if (this.components.has(name)) {
            throw new ComponentValidationError(
                `${name} is already registered`
            );
        }

        this.components.set(name, {
            component,
            schema: Object.freeze({ ...schema })
        });
    }

    get(name) {
        const entry = this.components.get(name);

        if (!entry) {
            throw new ComponentValidationError(
                `Component not found: ${name}`
            );
        }

        return entry;
    }

    list() {
        return [...this.components.keys()].sort();
    }
}


function validateProps(name, props, schema) {
    for (const [property, rules] of Object.entries(schema)) {
        const value = props[property];

        if (rules.required && value === undefined) {
            throw new ComponentValidationError(
                `${name}: ${property} is required`
            );
        }

        if (value === undefined) {
            continue;
        }

        if (rules.type === "string" && typeof value !== "string") {
            throw new ComponentValidationError(
                `${name}: ${property} must be a string`
            );
        }

        if (rules.type === "number" &&
            (typeof value !== "number" || !Number.isFinite(value))) {
            throw new ComponentValidationError(
                `${name}: ${property} must be a finite number`
            );
        }

        if (rules.type === "boolean" && typeof value !== "boolean") {
            throw new ComponentValidationError(
                `${name}: ${property} must be boolean`
            );
        }

        if (rules.type === "array" && !Array.isArray(value)) {
            throw new ComponentValidationError(
                `${name}: ${property} must be an array`
            );
        }
    }

    for (const property of Object.keys(props)) {
        if (property !== "children" &&
            !Object.hasOwn(schema, property)) {
            throw new ComponentValidationError(
                `${name}: unexpected property ${property}`
            );
        }
    }
}


// Reusable functional components.

function Text({ children, tone = "normal" }) {
    const colors = {
        normal: "#263238",
        muted: "#607D8B",
        success: "#237A45",
        danger: "#B42318"
    };

    return React.createElement(
        "p",
        { style: { color: colors[tone] || colors.normal } },
        children
    );
}


function Badge({ label, status = "neutral" }) {
    const colors = {
        success: "#D1FAE5",
        warning: "#FEF3C7",
        danger: "#FEE2E2",
        neutral: "#E2E8F0"
    };

    return React.createElement(
        "span",
        {
            style: {
                background: colors[status] || colors.neutral,
                padding: "4px 10px",
                borderRadius: "12px",
                display: "inline-block"
            }
        },
        label
    );
}


function Button({
    children,
    variant = "primary",
    disabled = false,
    onClick
}) {
    const colors = {
        primary: "#175CD3",
        secondary: "#475467",
        danger: "#B42318"
    };

    return React.createElement(
        "button",
        {
            type: "button",
            disabled,
            onClick,
            style: {
                color: "white",
                background: colors[variant] || colors.primary,
                border: 0,
                padding: "9px 16px",
                borderRadius: "6px",
                cursor: disabled ? "not-allowed" : "pointer"
            }
        },
        children
    );
}


function Card({ title, description, children }) {
    return React.createElement(
        "section",
        {
            style: {
                border: "1px solid #D0D5DD",
                borderRadius: "10px",
                padding: "18px",
                margin: "12px 0"
            }
        },
        React.createElement("h2", null, title),
        description
            ? React.createElement(Text, { tone: "muted" }, description)
            : null,
        children
    );
}


function Conditional({ when, children }) {
    return when ? React.createElement(React.Fragment, null, children) : null;
}


function List({ items, renderItem }) {
    if (!Array.isArray(items) || typeof renderItem !== "function") {
        throw new ComponentValidationError("Invalid List properties");
    }

    return React.createElement(
        "ul",
        null,
        items.map((item) =>
            React.createElement(
                "li",
                { key: item.id },
                renderItem(item)
            )
        )
    );
}


// Component registry for runtime validation.

const registry = new ComponentRegistry();

registry.register("Text", Text, {
    tone: { type: "string" }
});

registry.register("Badge", Badge, {
    label: { type: "string", required: true },
    status: { type: "string" }
});

registry.register("Button", Button, {
    variant: { type: "string" },
    disabled: { type: "boolean" }
});

registry.register("Card", Card, {
    title: { type: "string", required: true },
    description: { type: "string" }
});

registry.register("Conditional", Conditional, {
    when: { type: "boolean", required: true }
});


// Validated component factory.

function createComponent(name, props = {}) {
    const entry = registry.get(name);
    validateProps(name, props, entry.schema);

    return React.createElement(entry.component, props);
}


// Application-specific components.

function ProjectCard({ project, onToggle }) {
    return React.createElement(
        Card,
        {
            title: project.name,
            description: project.description
        },
        React.createElement(
            "div",
            { style: { display: "flex", gap: "12px", alignItems: "center" } },
            React.createElement(Badge, {
                label: project.active ? "Active" : "Paused",
                status: project.active ? "success" : "warning"
            }),
            React.createElement(Button, {
                variant: project.active ? "secondary" : "primary",
                onClick: () => onToggle(project.id)
            }, project.active ? "Pause" : "Activate")
        )
    );
}


function ProjectDashboard() {
    const [projects, setProjects] = useState([
        {
            id: 1,
            name: "Customer Portal",
            description: "Reusable customer interface",
            active: true
        },
        {
            id: 2,
            name: "Analytics Platform",
            description: "Business reporting components",
            active: false
        },
        {
            id: 3,
            name: "Administration Console",
            description: "Internal management interface",
            active: true
        }
    ]);

    const [filter, setFilter] = useState("all");

    const toggleProject = useCallback((projectId) => {
        setProjects((current) =>
            current.map((project) =>
                project.id === projectId
                    ? { ...project, active: !project.active }
                    : project
            )
        );
    }, []);

    const filteredProjects = useMemo(() => {
        if (filter === "active") {
            return projects.filter((project) => project.active);
        }

        if (filter === "paused") {
            return projects.filter((project) => !project.active);
        }

        return projects;
    }, [projects, filter]);

    return React.createElement(
        "main",
        {
            style: {
                maxWidth: "760px",
                margin: "30px auto",
                fontFamily: "Arial, sans-serif",
                padding: "16px"
            }
        },
        React.createElement("h1", null, "Project Dashboard"),

        React.createElement(
            "label",
            null,
            "Filter projects: ",
            React.createElement(
                "select",
                {
                    value: filter,
                    onChange: (event) => setFilter(event.target.value)
                },
                React.createElement("option", { value: "all" }, "All"),
                React.createElement("option", { value: "active" }, "Active"),
                React.createElement("option", { value: "paused" }, "Paused")
            )
        ),

        React.createElement(
            Text,
            { tone: "muted" },
            `Showing ${filteredProjects.length} of ${projects.length} projects`
        ),

        React.createElement(List, {
            items: filteredProjects,
            renderItem: (project) =>
                React.createElement(ProjectCard, {
                    project,
                    onToggle: toggleProject
                })
        }),

        React.createElement(
            Conditional,
            { when: projects.length === 0 },
            React.createElement(Text, null, "No projects available.")
        )
    );
}


// Standalone validation tests.

function runTests() {
    const assert = require("node:assert/strict");

    assert.equal(registry.list().length, 5);

    assert.throws(
        () => createComponent("Button", { disabled: "yes" }),
        ComponentValidationError
    );

    assert.throws(
        () => createComponent("Badge", {}),
        ComponentValidationError
    );

    assert.throws(
        () => createComponent("UnknownComponent", {}),
        ComponentValidationError
    );

    assert.throws(
        () => validateProps(
            "Text",
            { unknown: true },
            { tone: { type: "string" } }
        ),
        ComponentValidationError
    );

    assert.doesNotThrow(
        () => createComponent("Button", { disabled: true })
    );

    console.log("All component validation tests passed.");
}


function startApplication() {
    runTests();

    const rootElement = document.getElementById("root");

    if (!rootElement) {
        throw new Error("Missing application root element");
    }

    createRoot(rootElement).render(
        React.createElement(
            React.StrictMode,
            null,
            React.createElement(ProjectDashboard)
        )
    );
}


// Browser entry point.
if (typeof document !== "undefined") {
    startApplication();
}

// Node.js export for testing and component reuse.
module.exports = {
    ComponentRegistry,
    ComponentValidationError,
    validateProps,
    createComponent,
    Text,
    Badge,
    Button,
    Card,
    Conditional,
    List,
    ProjectCard,
    ProjectDashboard,
    registry,
    runTests
};
