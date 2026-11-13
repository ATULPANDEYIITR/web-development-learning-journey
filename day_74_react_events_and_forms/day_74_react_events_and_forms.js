"use strict";

/*
 * React Events and Forms
 * Node.js implementation of event-driven form management.
 *
 * Features:
 * - EventEmitter-based event handling
 * - Event propagation and cancellation
 * - Controlled and uncontrolled fields
 * - Immutable snapshots of form state
 * - Validation pipelines
 * - Asynchronous validation
 * - Submission locking
 * - Event-driven state transitions
 * - Cross-field validation
 * - Error recovery
 *
 * Run: node react_events_forms.js
 */

const { EventEmitter } = require("node:events");
const crypto = require("node:crypto");

const EventType = Object.freeze({
    CLICK: "click",
    INPUT: "input",
    CHANGE: "change",
    BLUR: "blur",
    FOCUS: "focus",
    SUBMIT: "submit",
    RESET: "reset"
});

const FormStatus = Object.freeze({
    IDLE: "idle",
    DIRTY: "dirty",
    VALIDATING: "validating",
    INVALID: "invalid",
    SUBMITTING: "submitting",
    SUBMITTED: "submitted"
});

class FormError extends Error {}
class ValidationError extends FormError {}
class SubmissionError extends FormError {}

/*
 * Represents a browser-style event.
 * preventDefault and stopPropagation have separate purposes.
 */
class UIEvent {
    constructor(type, target, detail = {}) {
        this.type = type;
        this.target = target;
        this.detail = detail;
        this.defaultPrevented = false;
        this.propagationStopped = false;
        this.timestamp = Date.now();
    }

    preventDefault() {
        this.defaultPrevented = true;
    }

    stopPropagation() {
        this.propagationStopped = true;
    }
}

/*
 * Event delegation model.
 */
class ComponentNode {
    constructor(name, parent = null) {
        this.name = name;
        this.parent = parent;
        this.handlers = new Map();
    }

    addEventListener(type, handler) {
        if (typeof handler !== "function") {
            throw new TypeError("Handler must be a function");
        }

        if (!this.handlers.has(type)) {
            this.handlers.set(type, new Set());
        }

        this.handlers.get(type).add(handler);
    }

    removeEventListener(type, handler) {
        this.handlers.get(type)?.delete(handler);
    }

    dispatchEvent(event) {
        let current = this;

        while (current) {
            const handlers = current.handlers.get(event.type);

            if (handlers) {
                for (const handler of [...handlers]) {
                    handler(event);

                    if (event.propagationStopped) {
                        return !event.defaultPrevented;
                    }
                }
            }

            current = current.parent;
        }

        return !event.defaultPrevented;
    }
}

class Field {
    constructor({
        name,
        value = "",
        required = false,
        controlled = true,
        type = "text",
        maxLength = 255
    }) {
        if (typeof name !== "string" || !name.trim()) {
            throw new TypeError("Invalid field name");
        }

        if (!Number.isInteger(maxLength) || maxLength < 1) {
            throw new RangeError("Invalid maximum length");
        }

        this.name = name;
        this.value = value;
        this.initialValue = value;
        this.required = required;
        this.controlled = controlled;
        this.type = type;
        this.maxLength = maxLength;
        this.touched = false;
    }

    reset() {
        this.value = this.initialValue;
        this.touched = false;
    }
}

class ValidationEngine {
    static validate(value, rules = {}) {
        const errors = [];

        if (value === null || value === undefined) {
            value = "";
        }

        const text = String(value);

        if (rules.required && !text.trim()) {
            return ["This field is required."];
        }

        if (!text.trim()) {
            return errors;
        }

        if (text.length > (rules.maxLength ?? 255)) {
            errors.push("Maximum length exceeded.");
        }

        if (
            rules.email &&
            !/^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/.test(text)
        ) {
            errors.push("Invalid email address.");
        }

        if (rules.minLength && text.length < rules.minLength) {
            errors.push(`Minimum length is ${rules.minLength}.`);
        }

        if (rules.pattern && !rules.pattern.test(text)) {
            errors.push("Value does not match the required pattern.");
        }

        if (rules.numeric) {
            const number = Number(text);

            if (!Number.isFinite(number)) {
                errors.push("A finite number is required.");
            } else {
                if (rules.minimum !== undefined && number < rules.minimum) {
                    errors.push("Value is below the minimum.");
                }

                if (rules.maximum !== undefined && number > rules.maximum) {
                    errors.push("Value exceeds the maximum.");
                }
            }
        }

        return errors;
    }
}

class FormController extends EventEmitter {
    constructor(fields, rules = {}) {
        super();

        this.fields = new Map();
        this.rules = new Map(Object.entries(rules));
        this.errors = new Map();

        this.status = FormStatus.IDLE;
        this.revision = 0;
        this.submissionCount = 0;
        this.pendingSubmission = null;
        this.validationController = null;

        for (const field of fields) {
            if (!(field instanceof Field)) {
                throw new TypeError("Expected Field instances");
            }

            if (this.fields.has(field.name)) {
                throw new FormError(`Duplicate field: ${field.name}`);
            }

            this.fields.set(field.name, field);
        }

        for (const name of this.rules.keys()) {
            if (!this.fields.has(name)) {
                throw new FormError(`Unknown validation field: ${name}`);
            }
        }
    }

    get values() {
        return Object.freeze(
            Object.fromEntries(
                [...this.fields].map(([name, field]) => [
                    name,
                    field.value
                ])
            )
        );
    }

    transition(nextStatus) {
        const allowed = {
            idle: ["dirty", "validating"],
            dirty: ["dirty", "validating", "idle"],
            validating: ["validating", "invalid", "idle", "dirty"],
            invalid: ["dirty", "validating", "idle"],
            submitting: ["submitted", "dirty", "invalid"],
            submitted: ["dirty", "validating", "idle"]
        };

        if (!allowed[this.status]?.includes(nextStatus)) {
            throw new FormError(
                `Invalid transition: ${this.status} -> ${nextStatus}`
            );
        }

        const previous = this.status;
        this.status = nextStatus;

        this.emit("stateChange", {
            previous,
            current: nextStatus,
            revision: this.revision
        });
    }

    setValue(name, value) {
        const field = this.fields.get(name);

        if (!field) {
            throw new FormError(`Unknown field: ${name}`);
        }

        if (!field.controlled) {
            throw new FormError(
                `${name} is uncontrolled. Use setUncontrolledValue().`
            );
        }

        this.updateField(field, value);
    }

    setUncontrolledValue(name, value) {
        const field = this.fields.get(name);

        if (!field) {
            throw new FormError(`Unknown field: ${name}`);
        }

        if (field.controlled) {
            throw new FormError(`${name} is controlled.`);
        }

        this.updateField(field, value);
    }

    updateField(field, value) {
        if (typeof value === "string" && value.length > field.maxLength) {
            throw new RangeError(
                `${field.name} exceeds its maximum length`
            );
        }

        field.value = value;
        field.touched = true;

        this.revision++;
        this.errors.delete(field.name);

        if (this.status === FormStatus.SUBMITTING) {
            throw new FormError("Cannot modify a submitting form");
        }

        this.transition(FormStatus.DIRTY);

        this.emit(EventType.CHANGE, {
            name: field.name,
            value,
            revision: this.revision
        });
    }

    validate() {
        if (this.status !== FormStatus.VALIDATING) {
            this.transition(FormStatus.VALIDATING);
        }

        this.errors.clear();

        for (const [name, field] of this.fields) {
            const rules = {
                required: field.required,
                maxLength: field.maxLength,
                ...this.rules.get(name)
            };

            const errors = ValidationEngine.validate(
                field.value,
                rules
            );

            if (errors.length) {
                this.errors.set(name, errors);
            }
        }

        const password = this.fields.get("password");
        const confirmation = this.fields.get("confirmPassword");

        if (
            password &&
            confirmation &&
            password.value !== confirmation.value
        ) {
            this.errors.set("confirmPassword", [
                "Passwords do not match."
            ]);
        }

        this.transition(
            this.errors.size
                ? FormStatus.INVALID
                : FormStatus.IDLE
        );

        return this.errors.size === 0;
    }

    async validateAsync() {
        if (this.validationController) {
            this.validationController.abort();
        }

        const controller = new AbortController();
        this.validationController = controller;

        const revision = this.revision;

        this.transition(FormStatus.VALIDATING);

        await new Promise(resolve => setTimeout(resolve, 15));

        if (controller.signal.aborted || revision !== this.revision) {
            return false;
        }

        if (!this.validate()) {
            return false;
        }

        const email = this.fields.get("email")?.value;

        if (
            typeof email === "string" &&
            email.toLowerCase() === "taken@example.com"
        ) {
            this.errors.set("email", [
                "Email address is already registered."
            ]);

            this.transition(FormStatus.INVALID);
            return false;
        }

        return true;
    }

    async submit(handler) {
        if (typeof handler !== "function") {
            throw new TypeError("Submission handler is required");
        }

        // Multiple calls share one pending submission.
        if (this.pendingSubmission) {
            return this.pendingSubmission;
        }

        this.pendingSubmission = this.performSubmission(handler);

        try {
            return await this.pendingSubmission;
        } finally {
            this.pendingSubmission = null;
        }
    }

    async performSubmission(handler) {
        const submittedRevision = this.revision;

        try {
            const valid = await this.validateAsync();

            if (!valid) {
                throw new ValidationError(
                    JSON.stringify(Object.fromEntries(this.errors))
                );
            }

            if (submittedRevision !== this.revision) {
                throw new SubmissionError(
                    "Form changed during validation"
                );
            }

            this.transition(FormStatus.SUBMITTING);

            const payload = this.values;

            this.emit(EventType.SUBMIT, {
                payload,
                revision: submittedRevision
            });

            const result = await handler(payload);

            if (submittedRevision !== this.revision) {
                throw new SubmissionError(
                    "Form changed during submission"
                );
            }

            this.submissionCount++;
            this.transition(FormStatus.SUBMITTED);

            this.emit("submitted", {
                result,
                count: this.submissionCount
            });

            return result;

        } catch (error) {
            if (
                this.status === FormStatus.SUBMITTING ||
                this.status === FormStatus.VALIDATING
            ) {
                this.transition(
                    this.errors.size
                        ? FormStatus.INVALID
                        : FormStatus.DIRTY
                );
            }

            if (error instanceof ValidationError) {
                throw error;
            }

            throw new SubmissionError(error.message);

        } finally {
            this.validationController = null;
        }
    }

    reset() {
        if (this.pendingSubmission) {
            throw new FormError("Cannot reset during submission");
        }

        this.validationController?.abort();

        for (const field of this.fields.values()) {
            field.reset();
        }

        this.errors.clear();
        this.revision++;

        this.transition(FormStatus.IDLE);

        this.emit(EventType.RESET, {
            values: this.values
        });
    }
}

async function registrationService(data) {
    await new Promise(resolve => setTimeout(resolve, 20));

    if (data.email === "failure@example.com") {
        throw new Error("Registration API unavailable");
    }

    // Do not expose passwords in responses.
    return {
        id: crypto.randomUUID(),
        username: data.username,
        email: data.email,
        registered: true
    };
}

async function main() {
    console.log("REACT EVENTS AND FORMS");

    console.log("\n1. Event propagation");

    const formNode = new ComponentNode("form");
    const buttonNode = new ComponentNode("button", formNode);

    formNode.addEventListener("click", () => {
        console.log("Form received click");
    });

    buttonNode.addEventListener("click", event => {
        console.log("Button received click");
        event.preventDefault();
    });

    const event = new UIEvent(EventType.CLICK, "button");

    console.log(
        "Default allowed:",
        buttonNode.dispatchEvent(event)
    );

    console.log("\n2. Controlled and uncontrolled forms");

    const form = new FormController(
        [
            new Field({
                name: "username",
                required: true,
                maxLength: 30
            }),
            new Field({
                name: "email",
                required: true,
                maxLength: 100
            }),
            new Field({
                name: "password",
                required: true,
                maxLength: 128
            }),
            new Field({
                name: "confirmPassword",
                required: true,
                maxLength: 128
            }),
            new Field({
                name: "newsletter",
                value: false,
                controlled: false,
                type: "checkbox"
            })
        ],
        {
            username: { minLength: 3 },
            email: { email: true },
            password: { minLength: 8 }
        }
    );

    form.on("stateChange", state => {
        console.log(
            `State: ${state.previous} -> ${state.current}`
        );
    });

    form.on("change", change => {
        console.log(`Changed: ${change.name}`);
    });

    form.setValue("username", "atul");
    form.setValue("email", "atul@example.com");
    form.setValue("password", "SecurePass123");
    form.setValue("confirmPassword", "SecurePass123");
    form.setUncontrolledValue("newsletter", true);

    console.log("Form values:", form.values);

    console.log("\n3. Successful submission");

    const result = await form.submit(registrationService);

    console.log("Registration:", result);

    console.log("\n4. Validation errors");

    form.setValue("email", "invalid");
    form.setValue("confirmPassword", "different");

    try {
        await form.submit(registrationService);
    } catch (error) {
        console.log(error.name, error.message);
        console.log("Errors:", Object.fromEntries(form.errors));
    }

    console.log("\n5. Reset");

    form.reset();
    console.log("Values:", form.values);

    console.log("\n6. Assertion tests");

    console.assert(
        ValidationEngine.validate(
            "person@example.com",
            { email: true }
        ).length === 0
    );

    console.assert(
        ValidationEngine.validate(
            "invalid",
            { email: true }
        ).length > 0
    );

    console.assert(form.status === FormStatus.IDLE);

    console.log("Tests completed.");
}

main().catch(error => {
    console.error("Application failure:", error);
    process.exitCode = 1;
});"use strict";

/*
 * React Events and Forms
 * Node.js implementation of event-driven form management.
 *
 * Features:
 * - EventEmitter-based event handling
 * - Event propagation and cancellation
 * - Controlled and uncontrolled fields
 * - Immutable snapshots of form state
 * - Validation pipelines
 * - Asynchronous validation
 * - Submission locking
 * - Event-driven state transitions
 * - Cross-field validation
 * - Error recovery
 *
 * Run: node react_events_forms.js
 */

const { EventEmitter } = require("node:events");
const crypto = require("node:crypto");

const EventType = Object.freeze({
    CLICK: "click",
    INPUT: "input",
    CHANGE: "change",
    BLUR: "blur",
    FOCUS: "focus",
    SUBMIT: "submit",
    RESET: "reset"
});

const FormStatus = Object.freeze({
    IDLE: "idle",
    DIRTY: "dirty",
    VALIDATING: "validating",
    INVALID: "invalid",
    SUBMITTING: "submitting",
    SUBMITTED: "submitted"
});

class FormError extends Error {}
class ValidationError extends FormError {}
class SubmissionError extends FormError {}

/*
 * Represents a browser-style event.
 * preventDefault and stopPropagation have separate purposes.
 */
class UIEvent {
    constructor(type, target, detail = {}) {
        this.type = type;
        this.target = target;
        this.detail = detail;
        this.defaultPrevented = false;
        this.propagationStopped = false;
        this.timestamp = Date.now();
    }

    preventDefault() {
        this.defaultPrevented = true;
    }

    stopPropagation() {
        this.propagationStopped = true;
    }
}

/*
 * Event delegation model.
 */
class ComponentNode {
    constructor(name, parent = null) {
        this.name = name;
        this.parent = parent;
        this.handlers = new Map();
    }

    addEventListener(type, handler) {
        if (typeof handler !== "function") {
            throw new TypeError("Handler must be a function");
        }

        if (!this.handlers.has(type)) {
            this.handlers.set(type, new Set());
        }

        this.handlers.get(type).add(handler);
    }

    removeEventListener(type, handler) {
        this.handlers.get(type)?.delete(handler);
    }

    dispatchEvent(event) {
        let current = this;

        while (current) {
            const handlers = current.handlers.get(event.type);

            if (handlers) {
                for (const handler of [...handlers]) {
                    handler(event);

                    if (event.propagationStopped) {
                        return !event.defaultPrevented;
                    }
                }
            }

            current = current.parent;
        }

        return !event.defaultPrevented;
    }
}

class Field {
    constructor({
        name,
        value = "",
        required = false,
        controlled = true,
        type = "text",
        maxLength = 255
    }) {
        if (typeof name !== "string" || !name.trim()) {
            throw new TypeError("Invalid field name");
        }

        if (!Number.isInteger(maxLength) || maxLength < 1) {
            throw new RangeError("Invalid maximum length");
        }

        this.name = name;
        this.value = value;
        this.initialValue = value;
        this.required = required;
        this.controlled = controlled;
        this.type = type;
        this.maxLength = maxLength;
        this.touched = false;
    }

    reset() {
        this.value = this.initialValue;
        this.touched = false;
    }
}

class ValidationEngine {
    static validate(value, rules = {}) {
        const errors = [];

        if (value === null || value === undefined) {
            value = "";
        }

        const text = String(value);

        if (rules.required && !text.trim()) {
            return ["This field is required."];
        }

        if (!text.trim()) {
            return errors;
        }

        if (text.length > (rules.maxLength ?? 255)) {
            errors.push("Maximum length exceeded.");
        }

        if (
            rules.email &&
            !/^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/.test(text)
        ) {
            errors.push("Invalid email address.");
        }

        if (rules.minLength && text.length < rules.minLength) {
            errors.push(`Minimum length is ${rules.minLength}.`);
        }

        if (rules.pattern && !rules.pattern.test(text)) {
            errors.push("Value does not match the required pattern.");
        }

        if (rules.numeric) {
            const number = Number(text);

            if (!Number.isFinite(number)) {
                errors.push("A finite number is required.");
            } else {
                if (rules.minimum !== undefined && number < rules.minimum) {
                    errors.push("Value is below the minimum.");
                }

                if (rules.maximum !== undefined && number > rules.maximum) {
                    errors.push("Value exceeds the maximum.");
                }
            }
        }

        return errors;
    }
}

class FormController extends EventEmitter {
    constructor(fields, rules = {}) {
        super();

        this.fields = new Map();
        this.rules = new Map(Object.entries(rules));
        this.errors = new Map();

        this.status = FormStatus.IDLE;
        this.revision = 0;
        this.submissionCount = 0;
        this.pendingSubmission = null;
        this.validationController = null;

        for (const field of fields) {
            if (!(field instanceof Field)) {
                throw new TypeError("Expected Field instances");
            }

            if (this.fields.has(field.name)) {
                throw new FormError(`Duplicate field: ${field.name}`);
            }

            this.fields.set(field.name, field);
        }

        for (const name of this.rules.keys()) {
            if (!this.fields.has(name)) {
                throw new FormError(`Unknown validation field: ${name}`);
            }
        }
    }

    get values() {
        return Object.freeze(
            Object.fromEntries(
                [...this.fields].map(([name, field]) => [
                    name,
                    field.value
                ])
            )
        );
    }

    transition(nextStatus) {
        const allowed = {
            idle: ["dirty", "validating"],
            dirty: ["dirty", "validating", "idle"],
            validating: ["validating", "invalid", "idle", "dirty"],
            invalid: ["dirty", "validating", "idle"],
            submitting: ["submitted", "dirty", "invalid"],
            submitted: ["dirty", "validating", "idle"]
        };

        if (!allowed[this.status]?.includes(nextStatus)) {
            throw new FormError(
                `Invalid transition: ${this.status} -> ${nextStatus}`
            );
        }

        const previous = this.status;
        this.status = nextStatus;

        this.emit("stateChange", {
            previous,
            current: nextStatus,
            revision: this.revision
        });
    }

    setValue(name, value) {
        const field = this.fields.get(name);

        if (!field) {
            throw new FormError(`Unknown field: ${name}`);
        }

        if (!field.controlled) {
            throw new FormError(
                `${name} is uncontrolled. Use setUncontrolledValue().`
            );
        }

        this.updateField(field, value);
    }

    setUncontrolledValue(name, value) {
        const field = this.fields.get(name);

        if (!field) {
            throw new FormError(`Unknown field: ${name}`);
        }

        if (field.controlled) {
            throw new FormError(`${name} is controlled.`);
        }

        this.updateField(field, value);
    }

    updateField(field, value) {
        if (typeof value === "string" && value.length > field.maxLength) {
            throw new RangeError(
                `${field.name} exceeds its maximum length`
            );
        }

        field.value = value;
        field.touched = true;

        this.revision++;
        this.errors.delete(field.name);

        if (this.status === FormStatus.SUBMITTING) {
            throw new FormError("Cannot modify a submitting form");
        }

        this.transition(FormStatus.DIRTY);

        this.emit(EventType.CHANGE, {
            name: field.name,
            value,
            revision: this.revision
        });
    }

    validate() {
        if (this.status !== FormStatus.VALIDATING) {
            this.transition(FormStatus.VALIDATING);
        }

        this.errors.clear();

        for (const [name, field] of this.fields) {
            const rules = {
                required: field.required,
                maxLength: field.maxLength,
                ...this.rules.get(name)
            };

            const errors = ValidationEngine.validate(
                field.value,
                rules
            );

            if (errors.length) {
                this.errors.set(name, errors);
            }
        }

        const password = this.fields.get("password");
        const confirmation = this.fields.get("confirmPassword");

        if (
            password &&
            confirmation &&
            password.value !== confirmation.value
        ) {
            this.errors.set("confirmPassword", [
                "Passwords do not match."
            ]);
        }

        this.transition(
            this.errors.size
                ? FormStatus.INVALID
                : FormStatus.IDLE
        );

        return this.errors.size === 0;
    }

    async validateAsync() {
        if (this.validationController) {
            this.validationController.abort();
        }

        const controller = new AbortController();
        this.validationController = controller;

        const revision = this.revision;

        this.transition(FormStatus.VALIDATING);

        await new Promise(resolve => setTimeout(resolve, 15));

        if (controller.signal.aborted || revision !== this.revision) {
            return false;
        }

        if (!this.validate()) {
            return false;
        }

        const email = this.fields.get("email")?.value;

        if (
            typeof email === "string" &&
            email.toLowerCase() === "taken@example.com"
        ) {
            this.errors.set("email", [
                "Email address is already registered."
            ]);

            this.transition(FormStatus.INVALID);
            return false;
        }

        return true;
    }

    async submit(handler) {
        if (typeof handler !== "function") {
            throw new TypeError("Submission handler is required");
        }

        // Multiple calls share one pending submission.
        if (this.pendingSubmission) {
            return this.pendingSubmission;
        }

        this.pendingSubmission = this.performSubmission(handler);

        try {
            return await this.pendingSubmission;
        } finally {
            this.pendingSubmission = null;
        }
    }

    async performSubmission(handler) {
        const submittedRevision = this.revision;

        try {
            const valid = await this.validateAsync();

            if (!valid) {
                throw new ValidationError(
                    JSON.stringify(Object.fromEntries(this.errors))
                );
            }

            if (submittedRevision !== this.revision) {
                throw new SubmissionError(
                    "Form changed during validation"
                );
            }

            this.transition(FormStatus.SUBMITTING);

            const payload = this.values;

            this.emit(EventType.SUBMIT, {
                payload,
                revision: submittedRevision
            });

            const result = await handler(payload);

            if (submittedRevision !== this.revision) {
                throw new SubmissionError(
                    "Form changed during submission"
                );
            }

            this.submissionCount++;
            this.transition(FormStatus.SUBMITTED);

            this.emit("submitted", {
                result,
                count: this.submissionCount
            });

            return result;

        } catch (error) {
            if (
                this.status === FormStatus.SUBMITTING ||
                this.status === FormStatus.VALIDATING
            ) {
                this.transition(
                    this.errors.size
                        ? FormStatus.INVALID
                        : FormStatus.DIRTY
                );
            }

            if (error instanceof ValidationError) {
                throw error;
            }

            throw new SubmissionError(error.message);

        } finally {
            this.validationController = null;
        }
    }

    reset() {
        if (this.pendingSubmission) {
            throw new FormError("Cannot reset during submission");
        }

        this.validationController?.abort();

        for (const field of this.fields.values()) {
            field.reset();
        }

        this.errors.clear();
        this.revision++;

        this.transition(FormStatus.IDLE);

        this.emit(EventType.RESET, {
            values: this.values
        });
    }
}

async function registrationService(data) {
    await new Promise(resolve => setTimeout(resolve, 20));

    if (data.email === "failure@example.com") {
        throw new Error("Registration API unavailable");
    }

    // Do not expose passwords in responses.
    return {
        id: crypto.randomUUID(),
        username: data.username,
        email: data.email,
        registered: true
    };
}

async function main() {
    console.log("REACT EVENTS AND FORMS");

    console.log("\n1. Event propagation");

    const formNode = new ComponentNode("form");
    const buttonNode = new ComponentNode("button", formNode);

    formNode.addEventListener("click", () => {
        console.log("Form received click");
    });

    buttonNode.addEventListener("click", event => {
        console.log("Button received click");
        event.preventDefault();
    });

    const event = new UIEvent(EventType.CLICK, "button");

    console.log(
        "Default allowed:",
        buttonNode.dispatchEvent(event)
    );

    console.log("\n2. Controlled and uncontrolled forms");

    const form = new FormController(
        [
            new Field({
                name: "username",
                required: true,
                maxLength: 30
            }),
            new Field({
                name: "email",
                required: true,
                maxLength: 100
            }),
            new Field({
                name: "password",
                required: true,
                maxLength: 128
            }),
            new Field({
                name: "confirmPassword",
                required: true,
                maxLength: 128
            }),
            new Field({
                name: "newsletter",
                value: false,
                controlled: false,
                type: "checkbox"
            })
        ],
        {
            username: { minLength: 3 },
            email: { email: true },
            password: { minLength: 8 }
        }
    );

    form.on("stateChange", state => {
        console.log(
            `State: ${state.previous} -> ${state.current}`
        );
    });

    form.on("change", change => {
        console.log(`Changed: ${change.name}`);
    });

    form.setValue("username", "atul");
    form.setValue("email", "atul@example.com");
    form.setValue("password", "SecurePass123");
    form.setValue("confirmPassword", "SecurePass123");
    form.setUncontrolledValue("newsletter", true);

    console.log("Form values:", form.values);

    console.log("\n3. Successful submission");

    const result = await form.submit(registrationService);

    console.log("Registration:", result);

    console.log("\n4. Validation errors");

    form.setValue("email", "invalid");
    form.setValue("confirmPassword", "different");

    try {
        await form.submit(registrationService);
    } catch (error) {
        console.log(error.name, error.message);
        console.log("Errors:", Object.fromEntries(form.errors));
    }

    console.log("\n5. Reset");

    form.reset();
    console.log("Values:", form.values);

    console.log("\n6. Assertion tests");

    console.assert(
        ValidationEngine.validate(
            "person@example.com",
            { email: true }
        ).length === 0
    );

    console.assert(
        ValidationEngine.validate(
            "invalid",
            { email: true }
        ).length > 0
    );

    console.assert(form.status === FormStatus.IDLE);

    console.log("Tests completed.");
}

main().catch(error => {
    console.error("Application failure:", error);
    process.exitCode = 1;
});
