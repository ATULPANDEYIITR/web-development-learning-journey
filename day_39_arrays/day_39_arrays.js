"use strict";

/*
 * Array processing for a deployment monitoring service.
 * Run with Node.js 18 or later. No external packages are required.
 */

function heading(title) {
  console.log(`\n========== ${title} ==========`);
}

function creationAndIndexing() {
  heading("Array creation and indexing");

  const empty = [];
  const latencies = [42, 75, 31, 108, 64];
  const fixedSlots = Array(4).fill(null);
  const generated = Array.from({ length: 5 }, (_, index) => index ** 2);

  console.log({ empty, latencies, fixedSlots, generated });
  console.log("First:", latencies[0]);
  console.log("Last:", latencies.at(-1));
  console.log("Slice:", latencies.slice(1, 4));
  console.log("Reversed copy:", latencies.toReversed());

  // Array(4) contains empty slots. Array.from creates actual values.
  const sparse = Array(3);
  console.log("Sparse array length:", sparse.length);
  console.log("Sparse map:", sparse.map(() => "visited"));
  console.log("Dense array:", Array.from({ length: 3 }, () => "visited"));
}

function mutationAndCopies() {
  heading("Mutation and copy semantics");

  const tasks = ["compile", "test", "package"];
  tasks[1] = "integration-test";
  tasks.push("publish");
  tasks.unshift("checkout");
  const removed = tasks.pop();

  console.log("Tasks:", tasks);
  console.log("Removed:", removed);

  const original = [{ name: "gateway" }, { name: "billing" }];
  const shallowCopy = original.slice();
  shallowCopy[0].name = "edge-gateway";

  console.log("Nested object mutation affects original:", original);

  // structuredClone makes an independent copy for supported data types.
  const deepCopy = structuredClone(original);
  deepCopy[0].name = "isolated-gateway";
  console.log("Original after deep-copy mutation:", original);
  console.log("Deep copy:", deepCopy);

  // Mutating a const array is allowed; reassigning its binding is not.
  original.push({ name: "inventory" });
  console.log("After push:", original);
}

function mapAndFilter() {
  heading("Map and filter");

  const services = [
    { name: "gateway", latency: 45, healthy: true },
    { name: "billing", latency: 130, healthy: true },
    { name: "inventory", latency: 88, healthy: false },
    { name: "search", latency: 160, healthy: true },
  ];

  const summaries = services.map((service) => ({
    service: service.name,
    latencySeconds: service.latency / 1000,
  }));

  const slowServices = services.filter((service) => service.latency > 100);
  const unhealthyServices = services.filter((service) => !service.healthy);

  console.log("Summaries:", summaries);
  console.log("Slow:", slowServices);
  console.log("Unhealthy:", unhealthyServices);

  // map preserves element count; filter selects matching elements.
  console.log("Input count:", services.length);
  console.log("Mapped count:", summaries.length);
  console.log("Filtered count:", slowServices.length);
}

function reduceAndFind() {
  heading("Reduce and find");

  const buildDurations = [42, 67, 91, 38, 110];

  const total = buildDurations.reduce((sum, duration) => sum + duration, 0);
  const average = buildDurations.length ? total / buildDurations.length : 0;
  const firstSlow = buildDurations.find((duration) => duration > 90);
  const firstCriticalIndex = buildDurations.findIndex(
    (duration) => duration >= 100,
  );
  const missing = buildDurations.find((duration) => duration > 500);

  console.log({ total, average, firstSlow, firstCriticalIndex, missing });

  // Supplying an initial accumulator avoids an exception on an empty array.
  const emptyTotal = [].reduce((sum, value) => sum + value, 0);
  console.log("Empty total:", emptyTotal);

  try {
    [].reduce((sum, value) => sum + value);
  } catch (error) {
    console.log("Reduce without initial value:", error.name);
  }
}

function someAndEvery() {
  heading("Some and every");

  const releaseChecks = [
    { name: "unit-tests", passed: true },
    { name: "integration-tests", passed: true },
    { name: "security-scan", passed: false },
  ];

  const anyFailed = releaseChecks.some((check) => !check.passed);
  const allPassed = releaseChecks.every((check) => check.passed);
  const allNamed = releaseChecks.every((check) => check.name.trim().length > 0);

  console.log({ anyFailed, allPassed, allNamed });

  // Empty-array every() is true and some() is false.
  // Validate non-empty requirements separately when policy demands checks.
  console.log("Empty some:", [].some(Boolean));
  console.log("Empty every:", [].every(Boolean));
  console.log(
    "At least one check and all passed:",
    releaseChecks.length > 0 && releaseChecks.every((check) => check.passed),
  );
}

function validateService(service) {
  if (!service || typeof service !== "object") {
    throw new TypeError("Service must be an object");
  }
  if (typeof service.name !== "string" || !service.name.trim()) {
    throw new TypeError("Service name must be a non-empty string");
  }
  if (!Number.isFinite(service.latency) || service.latency < 0) {
    throw new RangeError("Latency must be finite and non-negative");
  }
  if (typeof service.healthy !== "boolean") {
    throw new TypeError("Health state must be boolean");
  }
}

function buildHealthReport(input) {
  if (!Array.isArray(input)) {
    throw new TypeError("Expected an array of services");
  }

  input.forEach(validateService);

  const totalLatency = input.reduce(
    (sum, service) => sum + service.latency,
    0,
  );

  return {
    serviceCount: input.length,
    allHealthy: input.length > 0 && input.every((service) => service.healthy),
    hasSlowService: input.some((service) => service.latency > 100),
    firstUnhealthy: input.find((service) => !service.healthy)?.name ?? null,
    slowServiceNames: input
      .filter((service) => service.latency > 100)
      .map((service) => service.name),
    averageLatency: input.length ? totalLatency / input.length : 0,
  };
}

function stableUnique(values) {
  const seen = new Set();
  return values.filter((value) => {
    if (seen.has(value)) return false;
    seen.add(value);
    return true;
  });
}

async function collectHealthReports() {
  heading("Asynchronous array processing");

  // Promise.all preserves input order even when operations complete out of order.
  const serviceNames = ["gateway", "billing", "inventory"];

  const reports = await Promise.all(
    serviceNames.map(async (name, index) => {
      await new Promise((resolve) => setTimeout(resolve, (2 - index) * 5));
      return { name, latency: 40 + index * 35, healthy: index !== 1 };
    }),
  );

  console.log("Reports in source order:", reports);
  console.log("Aggregate:", buildHealthReport(reports));
}

async function main() {
  creationAndIndexing();
  mutationAndCopies();
  mapAndFilter();
  reduceAndFind();
  someAndEvery();

  heading("Validation and stable uniqueness");
  const services = [
    { name: "gateway", latency: 45, healthy: true },
    { name: "billing", latency: 130, healthy: true },
    { name: "inventory", latency: 88, healthy: false },
  ];

  console.log("Report:", buildHealthReport(services));
  console.log("Stable unique names:", stableUnique(["api", "db", "api", "cache"]));
  console.log("Empty report:", buildHealthReport([]));

  try {
    buildHealthReport([{ name: "gateway", latency: Infinity, healthy: true }]);
  } catch (error) {
    console.log("Invalid record rejected:", error.message);
  }

  await collectHealthReports();
}

main().catch((error) => {
  console.error("Monitoring failed:", error);
  process.exitCode = 1;
});
