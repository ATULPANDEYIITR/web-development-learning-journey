"use strict";

/*
 * JavaScript Execution: Call Stack, Execution Context, Lexical Environment,
 * and Hoisting.
 *
 * Run with Node.js 18 or later:
 *     node execution-semantics.js
 *
 * This program uses real JavaScript execution behavior, including closures,
 * asynchronous continuations, lexical declarations, and event-loop scheduling.
 * It does not emulate the language with a separate interpreter.
 */

const assert = require("node:assert/strict");
const { performance } = require("node:perf_hooks");

function heading(title) {
  console.log(`\n=== ${title} ===`);
}

function demonstrateCallStack() {
  heading("Call stack and nested execution");

  function persistAuditRecord(requestId) {
    console.log(`persistAuditRecord: ${requestId}`);
    return `audit:${requestId}`;
  }

  function validateRequest(request) {
    console.log(`validateRequest: ${request.id}`);
    if (!request.id) {
      throw new TypeError("Request ID is required");
    }
    return request;
  }

  function handleRequest(request) {
    console.log("handleRequest: enter");
    const validated = validateRequest(request);
    const result = persistAuditRecord(validated.id);
    console.log("handleRequest: exit");
    return result;
  }

  console.log(handleRequest({ id: "REQ-830" }));

  try {
    handleRequest({ id: "" });
  } catch (error) {
    // The thrown error unwinds the active synchronous call stack.
    console.log(`Caught after stack unwinding: ${error.message}`);
  }
}

function demonstrateDeclarationBehavior() {
  heading("Hoisting and initialization");

  console.log("var before assignment:", attempts);
  var attempts = 4;

  // Function declarations are initialized when their scope is instantiated.
  console.log("function before textual position:", describeStatus());

  function describeStatus() {
    return "deployment-ready";
  }

  console.log("var after assignment:", attempts);

  try {
    console.log(deploymentRegion);
  } catch (error) {
    console.log(`let in temporal dead zone: ${error.name}`);
  }

  let deploymentRegion = "ap-south-1";
  console.log("let after initialization:", deploymentRegion);

  try {
    console.log(releaseChannel);
  } catch (error) {
    console.log(`const in temporal dead zone: ${error.name}`);
  }

  const releaseChannel = "stable";
  console.log("const after initialization:", releaseChannel);

  // typeof does not avoid the TDZ error for a lexical binding.
  try {
    console.log(typeof uninitializedBinding);
    let uninitializedBinding = "available";
  } catch (error) {
    console.log(`typeof in temporal dead zone: ${error.name}`);
  }

  // A truly undeclared identifier differs from a lexical binding in its TDZ.
  console.log("typeof undeclared identifier:", typeof missingConfiguration);
}

function demonstrateBlockScope() {
  heading("Block scope, var scope, and shadowing");

  const region = "India";
  let activeDeployment = true;

  if (activeDeployment) {
    const region = "Singapore";
    let releaseId = "REL-2026-104";
    var auditChannel = "deployment-audit";

    console.log("Inner region:", region);
    console.log("Block-only release ID:", releaseId);
  }

  console.log("Outer region:", region);
  console.log("Function-scoped var:", auditChannel);

  try {
    console.log(releaseId);
  } catch (error) {
    console.log(`Block binding unavailable outside block: ${error.name}`);
  }
}

function demonstrateClosure() {
  heading("Lexical environments and closures");

  function createRateLimiter(maximumRequests) {
    let remaining = maximumRequests;
    const createdAt = performance.now();

    return function consumeRequest() {
      if (remaining <= 0) {
        return {
          allowed: false,
          remaining: 0,
          ageMilliseconds: Math.round(performance.now() - createdAt),
        };
      }

      remaining -= 1;

      return {
        allowed: true,
        remaining,
        ageMilliseconds: Math.round(performance.now() - createdAt),
      };
    };
  }

  const apiLimiter = createRateLimiter(2);

  // The factory has returned, but the inner function retains its lexical state.
  console.log("Request A:", apiLimiter());
  console.log("Request B:", apiLimiter());
  console.log("Request C:", apiLimiter());

  // A closure retains references to bindings, not frozen copies of values.
  function createCounter(initialValue) {
    let count = initialValue;

    return {
      increment() {
        count += 1;
        return count;
      },
      current() {
        return count;
      },
    };
  }

  const counter = createCounter(7);
  assert.equal(counter.increment(), 8);
  assert.equal(counter.current(), 8);
  console.log("Closure-backed counter:", counter.current());
}

function demonstrateLoopClosures() {
  heading("Loop closures and declaration scope");

  const varCallbacks = [];
  for (var index = 0; index < 3; index += 1) {
    varCallbacks.push(() => index);
  }

  // All callbacks reference the same function-scoped var binding.
  console.log("var closure results:", varCallbacks.map((callback) => callback()));

  const letCallbacks = [];
  for (let index = 0; index < 3; index += 1) {
    letCallbacks.push(() => index);
  }

  // A fresh per-iteration lexical binding gives each callback its own index.
  console.log("let closure results:", letCallbacks.map((callback) => callback()));

  assert.deepEqual(varCallbacks.map((callback) => callback()), [3, 3, 3]);
  assert.deepEqual(letCallbacks.map((callback) => callback()), [0, 1, 2]);
}

async function demonstrateExecutionOrder() {
  heading("Synchronous execution, promises, and the event loop");

  const order = [];

  order.push("synchronous:start");

  setTimeout(() => {
    order.push("timer:callback");
    console.log("Execution order:", order);
    assert.deepEqual(order, [
      "synchronous:start",
      "synchronous:end",
      "promise:microtask",
      "timer:callback",
    ]);
  }, 0);

  Promise.resolve().then(() => {
    order.push("promise:microtask");
  });

  order.push("synchronous:end");

  console.log("Before microtask checkpoint:", order);

  // Awaiting a resolved promise suspends this async function and schedules
  // its continuation as a microtask. It does not block the JavaScript thread.
  await Promise.resolve();
  console.log("After await continuation:", order);
}

async function demonstrateAsyncStackBoundaries() {
  heading("Execution contexts across await");

  async function loadConfiguration() {
    const requestId = "CFG-44";
    console.log(`loadConfiguration before await: ${requestId}`);

    await Promise.resolve("configuration-loaded");

    // The function resumes later with its lexical bindings preserved.
    console.log(`loadConfiguration after await: ${requestId}`);
    return requestId;
  }

  const configurationId = await loadConfiguration();
  assert.equal(configurationId, "CFG-44");
  console.log("Resolved configuration:", configurationId);
}

function demonstrateStrictModeAndErrors() {
  heading("Strict mode and invalid assignments");

  try {
    // Strict mode rejects assignment to an undeclared identifier.
    undeclaredDeploymentFlag = true;
  } catch (error) {
    console.log(`Undeclared assignment: ${error.name}`);
  }

  const policy = Object.freeze({
    maximumRetries: 3,
  });

  try {
    policy.maximumRetries = 10;
  } catch (error) {
    console.log(`Frozen object assignment: ${error.name}`);
  }

  console.log("Policy remains:", policy.maximumRetries);
}

function demonstrateArgumentEvaluation() {
  heading("Expression evaluation and call order");

  const events = [];

  function argument(label, value) {
    events.push(`argument:${label}`);
    return value;
  }

  function combine(left, right) {
    events.push("function:combine");
    return `${left}:${right}`;
  }

  const result = combine(
    argument("left", "region"),
    argument("right", "ap-south-1"),
  );

  console.log("Result:", result);
  console.log("Evaluation trace:", events);

  assert.deepEqual(events, [
    "argument:left",
    "argument:right",
    "function:combine",
  ]);
}

async function main() {
  demonstrateCallStack();
  demonstrateDeclarationBehavior();
  demonstrateBlockScope();
  demonstrateClosure();
  demonstrateLoopClosures();
  demonstrateArgumentEvaluation();
  demonstrateStrictModeAndErrors();

  await demonstrateExecutionOrder();
  await demonstrateAsyncStackBoundaries();

  console.log("\nAll JavaScript assertions passed.");
}

main().catch((error) => {
  console.error("Execution failed:", error);
  process.exitCode = 1;
});
