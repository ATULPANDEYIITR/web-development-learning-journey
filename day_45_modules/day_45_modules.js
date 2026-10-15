/**
 * ES module architecture laboratory.
 *
 * Run with:
 *   node --input-type=module < module_architecture.mjs
 *
 * Or save this file as module_architecture.mjs and run:
 *   node module_architecture.mjs
 *
 * The examples use Node.js built-ins only.
 */

import assert from "node:assert/strict";
import { EventEmitter } from "node:events";
import { pathToFileURL } from "node:url";
import { resolve } from "node:path";
import { readFile, mkdtemp, mkdir, writeFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { createHash } from "node:crypto";

export const SUPPORTED_CURRENCIES = Object.freeze(["USD", "EUR", "INR"]);

export function validateInvoiceItems(items) {
  if (!Array.isArray(items)) {
    throw new TypeError("Invoice items must be an array.");
  }

  for (const [index, item] of items.entries()) {
    if (!item || typeof item !== "object" || Array.isArray(item)) {
      throw new TypeError(`Item ${index} must be an object.`);
    }

    if (typeof item.name !== "string" || item.name.trim() === "") {
      throw new TypeError(`Item ${index} must have a non-empty name.`);
    }

    if (!Number.isSafeInteger(item.quantity) || item.quantity <= 0) {
      throw new RangeError(`Item ${index} quantity must be a positive integer.`);
    }

    if (
      typeof item.unitPrice !== "number" ||
      !Number.isFinite(item.unitPrice) ||
      item.unitPrice < 0
    ) {
      throw new RangeError(`Item ${index} unitPrice must be finite and non-negative.`);
    }
  }

  return items;
}

export function calculateInvoice(items, { currency = "USD", discountRate = 0 } = {}) {
  validateInvoiceItems(items);

  if (!SUPPORTED_CURRENCIES.includes(currency)) {
    throw new RangeError(`Unsupported currency: ${currency}`);
  }

  if (
    typeof discountRate !== "number" ||
    !Number.isFinite(discountRate) ||
    discountRate < 0 ||
    discountRate > 1
  ) {
    throw new RangeError("discountRate must be between 0 and 1.");
  }

  const subtotalCents = items.reduce((sum, item) => {
    // Integer cents avoid accumulating most binary floating-point currency errors.
    const unitCents = Math.round(item.unitPrice * 100);
    return sum + unitCents * item.quantity;
  }, 0);

  if (!Number.isSafeInteger(subtotalCents)) {
    throw new RangeError("Invoice exceeds the safe integer range.");
  }

  const totalCents = Math.round(subtotalCents * (1 - discountRate));
  const symbols = { USD: "$", EUR: "€", INR: "₹" };

  return Object.freeze({
    itemCount: items.reduce((sum, item) => sum + item.quantity, 0),
    subtotalCents,
    discountRate,
    totalCents,
    currency,
    formattedTotal: `${symbols[currency]}${(totalCents / 100).toFixed(2)}`,
  });
}

// A default export represents the module's primary capability. Consumers can
// choose any local name when importing it; named exports retain their names.
export default calculateInvoice;

export class ModuleRegistry extends EventEmitter {
  #modules = new Map();
  #dependents = new Map();

  register({ id, dependencies = [], factory }) {
    if (typeof id !== "string" || id.trim() === "") {
      throw new TypeError("Module id must be a non-empty string.");
    }

    if (this.#modules.has(id)) {
      throw new Error(`Module '${id}' is already registered.`);
    }

    if (typeof factory !== "function") {
      throw new TypeError(`Module '${id}' requires a factory function.`);
    }

    if (!Array.isArray(dependencies) || dependencies.includes(id)) {
      throw new TypeError("Dependencies must be an array and cannot include self.");
    }

    this.#modules.set(id, {
      id,
      dependencies: [...new Set(dependencies)],
      factory,
      state: "registered",
      value: undefined,
    });

    this.emit("registered", { id });
  }

  inspect() {
    return [...this.#modules.values()].map(({ id, dependencies, state }) => ({
      id,
      dependencies: [...dependencies],
      state,
    }));
  }

  async initialize(id, ancestry = []) {
    const module = this.#modules.get(id);

    if (!module) {
      throw new Error(`Unknown module '${id}'.`);
    }

    if (module.state === "initialized") {
      return module.value;
    }

    if (ancestry.includes(id)) {
      throw new Error(`Circular dependency: ${[...ancestry, id].join(" -> ")}`);
    }

    if (module.state === "initializing") {
      throw new Error(`Module '${id}' is already being initialized.`);
    }

    module.state = "initializing";

    try {
      const dependencies = {};

      // Resolve dependencies before invoking the factory. This makes module
      // startup order explicit and exposes missing dependencies early.
      for (const dependencyId of module.dependencies) {
        dependencies[dependencyId] = await this.initialize(dependencyId, [
          ...ancestry,
          id,
        ]);
      }

      module.value = await module.factory(Object.freeze(dependencies));
      module.state = "initialized";
      this.emit("initialized", { id });
      return module.value;
    } catch (error) {
      module.state = "failed";
      module.value = undefined;
      this.emit("initializationFailed", { id, message: error.message });
      throw error;
    }
  }
}

export async function demonstrateModuleArchitecture() {
  console.log("\nES module exports and runtime behavior");

  const items = [
    { name: "Security assessment", quantity: 1, unitPrice: 1200 },
    { name: "Monitoring service", quantity: 3, unitPrice: 49.95 },
  ];

  const invoice = calculateInvoice(items, {
    currency: "INR",
    discountRate: 0.1,
  });

  console.log("Default export result:", invoice);
  assert.equal(invoice.totalCents, 25587);
  assert.throws(
    () => calculateInvoice([{ name: "Bad item", quantity: 0, unitPrice: 5 }]),
    /quantity/,
  );

  const registry = new ModuleRegistry();

  registry.on("initialized", ({ id }) => console.log(`Initialized: ${id}`));
  registry.on("initializationFailed", ({ id, message }) => {
    console.error(`Failed to initialize ${id}: ${message}`);
  });

  registry.register({
    id: "configuration",
    factory: async () =>
      Object.freeze({ taxRate: 0.18, region: "IN" }),
  });

  registry.register({
    id: "pricing",
    dependencies: ["configuration"],
    factory: async ({ configuration }) => ({
      calculateTax: (amount) => {
        if (!Number.isFinite(amount) || amount < 0) {
          throw new RangeError("Taxable amount must be non-negative.");
        }
        return Math.round(amount * configuration.taxRate * 100) / 100;
      },
      region: configuration.region,
    }),
  });

  registry.register({
    id: "invoice-service",
    dependencies: ["configuration", "pricing"],
    factory: async ({ configuration, pricing }) => ({
      create(amount) {
        return {
          region: configuration.region,
          tax: pricing.calculateTax(amount),
          amount,
        };
      },
    }),
  });

  const service = await registry.initialize("invoice-service");
  console.log("Composed service:", service.create(1000));
  console.log("Repeated initialization reuses instance:",
    service === await registry.initialize("invoice-service"));

  assert.equal(service.create(1000).tax, 180);
  assert.equal(registry.inspect().every((item) => item.state === "initialized"), true);

  const cyclic = new ModuleRegistry();
  cyclic.register({ id: "alpha", dependencies: ["beta"], factory: () => ({}) });
  cyclic.register({ id: "beta", dependencies: ["alpha"], factory: () => ({}) });

  await assert.rejects(cyclic.initialize("alpha"), /Circular dependency/);

  const missing = new ModuleRegistry();
  missing.register({
    id: "reports",
    dependencies: ["database"],
    factory: () => ({}),
  });
  await assert.rejects(missing.initialize("reports"), /Unknown module/);

  await demonstrateNativeModuleResolution();
}

async function demonstrateNativeModuleResolution() {
  console.log("\nNative Node.js ES module resolution");

  const directory = await mkdtemp(resolve(tmpdir(), "es-module-lab-"));

  try {
    await mkdir(resolve(directory, "services"));

    await writeFile(
      resolve(directory, "services", "money.mjs"),
      [
        "export const currency = 'INR';",
        "export function format(amount) {",
        "  if (!Number.isFinite(amount)) throw new TypeError('amount must be finite');",
        "  return `${currency} ${amount.toFixed(2)}`;",
        "}",
        "export default format;",
      ].join("\n"),
      "utf8",
    );

    await writeFile(
      resolve(directory, "consumer.mjs"),
      [
        "import formatDefault, { currency } from './services/money.mjs';",
        "export const invoiceTotal = formatDefault(250.5);",
        "export const invoiceCurrency = currency;",
      ].join("\n"),
      "utf8",
    );

    const consumerUrl = pathToFileURL(resolve(directory, "consumer.mjs")).href;
    const firstImport = await import(consumerUrl);
    const secondImport = await import(consumerUrl);

    assert.equal(firstImport.invoiceTotal, "INR 250.50");
    assert.strictEqual(firstImport, secondImport);

    console.log("Resolved consumer:", firstImport.invoiceTotal);
    console.log("Repeated dynamic import shares module namespace:",
      firstImport === secondImport);

    const source = await readFile(resolve(directory, "consumer.mjs"), "utf8");
    console.log(
      "Consumer source fingerprint:",
      createHash("sha256").update(source).digest("hex").slice(0, 16),
    );
  } finally {
    // The temporary module tree is removed even if an assertion fails.
    await rm(directory, { recursive: true, force: true });
  }
}

const executedDirectly =
  process.argv[1] !== undefined &&
  import.meta.url === pathToFileURL(resolve(process.argv[1])).href;

if (executedDirectly) {
  demonstrateModuleArchitecture().catch((error) => {
    console.error(error);
    process.exitCode = 1;
  });
}
