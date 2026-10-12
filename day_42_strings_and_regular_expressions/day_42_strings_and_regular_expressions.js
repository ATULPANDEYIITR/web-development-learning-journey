"use strict";

/*
 * String processing and regular expressions in Node.js.
 * Run with: node strings_regex.js
 *
 * This implementation focuses on event-driven input processing, Unicode,
 * replacement callbacks, and asynchronous validation pipelines.
 */

const { EventEmitter } = require("node:events");
const assert = require("node:assert/strict");

function normalizeSearchText(value) {
    if (typeof value !== "string") {
        throw new TypeError("Search text must be a string");
    }

    // Unicode normalization makes canonically equivalent strings comparable.
    return value.normalize("NFC").trim().toLocaleLowerCase("en");
}

function tokenizeDocument(text) {
    const normalized = normalizeSearchText(text);

    // Unicode property escapes match letters and numbers beyond ASCII.
    return normalized.match(/[\p{L}\p{N}]+(?:['’-][\p{L}\p{N}]+)*/gu) ?? [];
}

function demonstrateStringOperations() {
    console.log("\n=== String operations ===");

    const raw = "  Procurement   Review  ";
    console.log("Trim:", raw.trim());
    console.log("Case:", raw.toUpperCase());
    console.log("Replacement:", raw.replace(/\s+/g, " "));
    console.log("Split:", "PO-1001,PO-1002;PO-1003".split(/[,;]/));
    console.log("Includes:", raw.includes("Review"));
    console.log("Starts with:", raw.trimStart().startsWith("Procurement"));

    const order = {
        id: "PO-2026-0184",
        supplier: "Northstar Components",
        quantity: 240,
        unitPrice: 875.5
    };

    // Template literals support embedded expressions and multiline reports.
    const report = `
Purchase order: ${order.id}
Supplier: ${order.supplier}
Quantity: ${order.quantity.toLocaleString("en-IN")}
Total: ₹${(order.quantity * order.unitPrice).toLocaleString("en-IN", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    })}`.trim();

    console.log(report);
    console.log("Tokens:", tokenizeDocument("Café equipment: routers, switches & storage."));
}

function demonstrateMatching() {
    console.log("\n=== Matching and replacement ===");

    const text = "Build #184 completed; build #185 failed; build #186 pending.";
    const buildPattern = /\bbuild #(\d+)\b/gi;

    // matchAll() exposes captures and match positions without manual indexing.
    for (const match of text.matchAll(buildPattern)) {
        console.log({
            matchedText: match[0],
            buildNumber: Number(match[1]),
            position: match.index
        });
    }

    // A global regular expression is stateful when test() is called repeatedly.
    const stateful = /PO-\d+/g;
    console.log("First stateful test:", stateful.test("PO-1001"));
    console.log("Second stateful test on same input:", stateful.test("PO-1001"));
    stateful.lastIndex = 0;
    console.log("Reset test:", stateful.test("PO-1001"));

    const sanitized = text.replace(/\bfailed\b/gi, "requires investigation");
    console.log("Sanitized text:", sanitized);

    const invoiceText = "INV-000125 INV-000126 INV-ABC127";
    console.log("Invoice IDs:", invoiceText.match(/\bINV-\d{6}\b/g) ?? []);

    // Escape user-supplied text when searching for literal characters.
    function escapeRegExp(literal) {
        return literal.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    }

    const userSearch = "rack[2]";
    const literalSearch = new RegExp(escapeRegExp(userSearch), "g");
    console.log("Literal search:", "rack[2] rack2".match(literalSearch));
}

class ValidationError extends Error {
    constructor(field, message) {
        super(`${field}: ${message}`);
        this.name = "ValidationError";
        this.field = field;
    }
}

class ProcurementInputValidator {
    constructor() {
        this.rules = new Map([
            ["orderId", /^PO-\d{4}-\d{4}$/],
            ["username", /^[A-Za-z][A-Za-z0-9_]{2,19}$/],
            ["postalCode", /^\d{6}$/],
            ["mobile", /^\+91[6-9]\d{9}$/]
        ]);
    }

    validate(field, value) {
        if (typeof value !== "string") {
            throw new ValidationError(field, "value must be a string");
        }

        const normalized = value.trim();
        const pattern = this.rules.get(field);

        if (!pattern) {
            throw new ValidationError(field, "unknown validation field");
        }

        if (!pattern.test(normalized)) {
            throw new ValidationError(field, "format is invalid");
        }

        return Object.freeze({ field, value: normalized, valid: true });
    }

    validateEmail(value) {
        if (typeof value !== "string") {
            throw new ValidationError("email", "value must be a string");
        }

        const normalized = value.trim();
        if (normalized.length > 254) {
            throw new ValidationError("email", "address is too long");
        }

        const pattern =
            /^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,63}$/;

        if (!pattern.test(normalized)) {
            throw new ValidationError("email", "syntax is invalid");
        }

        const localPart = normalized.split("@")[0];
        if (localPart.length > 64) {
            throw new ValidationError("email", "local part is too long");
        }

        return Object.freeze({
            field: "email",
            value: normalized,
            valid: true,
            ownershipVerified: false
        });
    }
}

async function validateBatch(records, validator) {
    // Promise.allSettled preserves every result even when some records fail.
    return Promise.allSettled(
        records.map(async (record) => {
            // Yield to the event loop to model an asynchronous ingestion pipeline.
            await Promise.resolve();
            return {
                orderId: validator.validate("orderId", record.orderId),
                postalCode: validator.validate("postalCode", record.postalCode)
            };
        })
    );
}

class OrderIngestionPipeline extends EventEmitter {
    constructor(validator) {
        super();
        this.validator = validator;
        this.accepted = [];
        this.rejected = [];
    }

    ingest(record) {
        try {
            const validatedOrder = this.validator.validate("orderId", record.orderId);
            const validatedPostal = this.validator.validate("postalCode", record.postalCode);

            const normalized = Object.freeze({
                orderId: validatedOrder.value,
                postalCode: validatedPostal.value,
                supplier: String(record.supplier ?? "").trim()
            });

            if (normalized.supplier.length === 0) {
                throw new ValidationError("supplier", "must not be empty");
            }

            this.accepted.push(normalized);
            this.emit("accepted", normalized);
            return normalized;
        } catch (error) {
            const rejection = Object.freeze({
                orderId: record?.orderId ?? null,
                reason: error instanceof Error ? error.message : "Unknown failure"
            });

            this.rejected.push(rejection);
            this.emit("rejected", rejection);
            return null;
        }
    }
}

async function demonstratePipeline() {
    console.log("\n=== Asynchronous validation and events ===");

    const validator = new ProcurementInputValidator();

    const pipeline = new OrderIngestionPipeline(validator);
    pipeline.on("accepted", (record) => {
        console.log("Accepted:", record.orderId);
    });
    pipeline.on("rejected", (record) => {
        console.log("Rejected:", record.reason);
    });

    pipeline.ingest({
        orderId: "PO-2026-0184",
        postalCode: "226001",
        supplier: "Northstar Components"
    });

    pipeline.ingest({
        orderId: "PO-26-184",
        postalCode: "226001",
        supplier: "Invalid Supplier"
    });

    pipeline.ingest({
        orderId: "PO-2026-0185",
        postalCode: "22600A",
        supplier: "Malformed Postal Record"
    });

    console.log("Accepted count:", pipeline.accepted.length);
    console.log("Rejected count:", pipeline.rejected.length);

    const records = [
        { orderId: "PO-2026-0001", postalCode: "226001" },
        { orderId: "invalid", postalCode: "226001" },
        { orderId: "PO-2026-0003", postalCode: "000000" }
    ];

    const results = await validateBatch(records, validator);
    console.log("Batch outcomes:", results.map((result) => result.status));

    for (const result of results) {
        if (result.status === "rejected") {
            console.log("Batch failure:", result.reason.message);
        }
    }

    try {
        validator.validate("username", "7invalid");
    } catch (error) {
        console.log("Expected validation failure:", error.message);
    }

    try {
        validator.validate("unknownField", "anything");
    } catch (error) {
        console.log("Unknown rule:", error.message);
    }
}

function runAssertions() {
    const validator = new ProcurementInputValidator();

    assert.equal(normalizeSearchText("  CAFÉ  "), "café");
    assert.deepEqual(tokenizeDocument("Café routers 42"), ["café", "routers", "42"]);
    assert.equal(validator.validate("orderId", " PO-2026-0184 ").valid, true);
    assert.throws(() => validator.validate("orderId", "PO-2026-18"), ValidationError);
    assert.equal(validator.validateEmail("ops@example.com").ownershipVerified, false);

    const globalPattern = /a/g;
    assert.equal(globalPattern.test("a"), true);
    assert.equal(globalPattern.test("a"), false);

    console.log("\nAll JavaScript assertions passed.");
}

async function main() {
    demonstrateStringOperations();
    demonstrateMatching();
    await demonstratePipeline();
    runAssertions();
}

main().catch((error) => {
    console.error("Execution failed:", error);
    process.exitCode = 1;
});
