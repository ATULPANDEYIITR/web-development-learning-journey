"use strict";

/*
 * Error Handling in JavaScript
 *
 * Demonstrates synchronous and asynchronous exceptions, custom error classes,
 * Promise rejection, try/catch/finally, defensive validation, event-driven
 * failure reporting, bounded retries, and fault-isolated concurrent tasks.
 *
 * Run with Node.js 18 or later:
 *     node error_handling.js
 */

class ApplicationError extends Error {
  constructor(message, options = {}) {
    super(message, options);
    this.name = new.target.name;
  }
}

class ValidationError extends ApplicationError {}
class ResourceNotFoundError extends ApplicationError {}
class ExternalServiceError extends ApplicationError {}
class RetryExhaustedError extends ApplicationError {}
class StateTransitionError extends ApplicationError {}

// JavaScript Error objects retain stack traces and can preserve causes through
// the standard Error options object.
function parsePort(value) {
  if (
    typeof value !== "number" ||
    !Number.isInteger(value) ||
    value < 1 ||
    value > 65535
  ) {
    throw new ValidationError("Port must be an integer from 1 through 65535.");
  }

  return value;
}

function demonstrateSynchronousHandling() {
  console.log("\n--- Synchronous errors ---");

  try {
    parsePort(70000);
  } catch (error) {
    if (error instanceof ValidationError) {
      console.error("Invalid configuration:", error.message);
    } else {
      throw error;
    }
  } finally {
    console.log("Port validation finished.");
  }

  try {
    JSON.parse("{invalid json}");
  } catch (error) {
    console.log(`JSON parsing failed: ${error.name}`);
  }
}

// A wrapper translates low-level failures into domain errors while retaining
// the original cause for debugging.
function parseDeploymentConfiguration(rawText) {
  let configuration;

  try {
    configuration = JSON.parse(rawText);
  } catch (error) {
    throw new ValidationError("Deployment configuration is not valid JSON.", {
      cause: error,
    });
  }

  if (
    configuration === null ||
    typeof configuration !== "object" ||
    Array.isArray(configuration)
  ) {
    throw new ValidationError("Configuration must be a JSON object.");
  }

  if (typeof configuration.environment !== "string" ||
      configuration.environment.trim() === "") {
    throw new ValidationError("Environment name is required.");
  }

  configuration.port = parsePort(configuration.port);
  return configuration;
}

function demonstrateErrorCauses() {
  console.log("\n--- Error causes ---");

  try {
    parseDeploymentConfiguration('{"environment":"production","port":70000}');
  } catch (error) {
    console.error(error.name, error.message);
    if (error.cause) {
      console.error("Underlying cause:", error.cause.message);
    }
  }
}

// Never assume a rejected Promise is handled by a surrounding synchronous
// try/catch unless the Promise is awaited inside that try block.
async function fetchReleaseMetadata(releaseId, transport) {
  if (typeof releaseId !== "string" || releaseId.trim() === "") {
    throw new ValidationError("Release identifier is required.");
  }

  try {
    const response = await transport(releaseId);

    if (!response || response.status !== 200) {
      throw new ExternalServiceError("Release service returned an invalid status.");
    }

    if (!response.data || typeof response.data !== "object") {
      throw new ExternalServiceError("Release service returned invalid data.");
    }

    return response.data;
  } catch (error) {
    if (error instanceof ValidationError || error instanceof ExternalServiceError) {
      throw error;
    }

    throw new ExternalServiceError("Unable to retrieve release metadata.", {
      cause: error,
    });
  }
}

async function demonstrateAsyncHandling() {
  console.log("\n--- Asynchronous error handling ---");

  const transport = async (releaseId) => {
    if (releaseId === "release-500") {
      throw new Error("Connection reset by peer.");
    }

    return {
      status: 200,
      data: { id: releaseId, state: "ready" },
    };
  };

  console.log(await fetchReleaseMetadata("release-42", transport));

  try {
    await fetchReleaseMetadata("release-500", transport);
  } catch (error) {
    console.error(error.name, error.message);
    console.error("Cause:", error.cause?.message);
  }
}

function sleep(milliseconds) {
  if (!Number.isFinite(milliseconds) || milliseconds < 0) {
    throw new ValidationError("Sleep duration must be finite and nonnegative.");
  }

  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

async function retryAsync(
  operation,
  {
    attempts = 3,
    initialDelayMs = 20,
    retryIf = (error) => error instanceof ExternalServiceError,
  } = {}
) {
  if (typeof operation !== "function") {
    throw new ValidationError("Retry operation must be a function.");
  }

  if (!Number.isInteger(attempts) || attempts < 1 || attempts > 10) {
    throw new ValidationError("Attempts must be an integer between 1 and 10.");
  }

  if (!Number.isFinite(initialDelayMs) || initialDelayMs < 0) {
    throw new ValidationError("Initial delay must be finite and nonnegative.");
  }

  if (typeof retryIf !== "function") {
    throw new ValidationError("retryIf must be a function.");
  }

  for (let attempt = 0; attempt < attempts; attempt += 1) {
    try {
      return await operation();
    } catch (error) {
      if (!retryIf(error)) {
        throw error;
      }

      if (attempt === attempts - 1) {
        throw new RetryExhaustedError(
          `Operation failed after ${attempts} attempts.`,
          { cause: error }
        );
      }

      await sleep(initialDelayMs * 2 ** attempt);
    }
  }

  throw new Error("Unreachable retry state.");
}

function createFlakyDeploymentService(failuresBeforeSuccess) {
  if (!Number.isInteger(failuresBeforeSuccess) || failuresBeforeSuccess < 0) {
    throw new ValidationError("Failure count must be a nonnegative integer.");
  }

  let failures = 0;

  return async () => {
    if (failures < failuresBeforeSuccess) {
      failures += 1;
      throw new ExternalServiceError("Deployment service temporarily unavailable.");
    }

    return { deploymentId: "deploy-204", state: "complete" };
  };
}

async function demonstrateRetries() {
  console.log("\n--- Bounded retries ---");

  const result = await retryAsync(createFlakyDeploymentService(2), {
    attempts: 3,
    initialDelayMs: 1,
  });

  console.log("Recovered:", result);

  try {
    await retryAsync(createFlakyDeploymentService(5), {
      attempts: 2,
      initialDelayMs: 1,
    });
  } catch (error) {
    console.error(error.name, error.message);
  }
}

// Promise.all rejects as soon as one member rejects. allSettled is preferable
// when every independent task must report its own outcome.
async function runIndependentChecks(checks) {
  if (!Array.isArray(checks) || checks.some((check) => typeof check !== "function")) {
    throw new ValidationError("Checks must be an array of functions.");
  }

  const outcomes = await Promise.allSettled(
    checks.map(async (check, index) => ({
      index,
      result: await check(),
    }))
  );

  return outcomes.map((outcome, index) => {
    if (outcome.status === "fulfilled") {
      return {
        index,
        status: "fulfilled",
        result: outcome.value.result,
      };
    }

    return {
      index,
      status: "rejected",
      errorType: outcome.reason?.name ?? "UnknownError",
      message: outcome.reason?.message ?? "Unknown failure",
    };
  });
}

async function demonstrateConcurrentChecks() {
  console.log("\n--- Independent concurrent checks ---");

  const outcomes = await runIndependentChecks([
    async () => "Database reachable",
    async () => {
      throw new ExternalServiceError("Build service unavailable.");
    },
    async () => "Security scan passed",
  ]);

  for (const outcome of outcomes) {
    console.log(outcome);
  }
}

// An event emitter makes error observation explicit. The listener handles
// reporting; the producer still determines whether the operation can continue.
class DeploymentMonitor extends EventTarget {
  reportFailure(deploymentId, error) {
    const event = new CustomEvent("deployment-error", {
      detail: {
        deploymentId,
        errorName: error.name,
        message: error.message,
      },
    });

    this.dispatchEvent(event);
  }
}

function demonstrateEventDrivenErrors() {
  console.log("\n--- Event-driven error reporting ---");

  const monitor = new DeploymentMonitor();

  monitor.addEventListener("deployment-error", (event) => {
    console.error("Deployment incident:", event.detail);
  });

  monitor.reportFailure(
    "deploy-205",
    new ExternalServiceError("Artifact registry rejected the request.")
  );
}

// State transitions are validated centrally so that a failed transition
// cannot silently corrupt the workflow state.
class PullRequestWorkflow {
  static transitions = Object.freeze({
    draft: new Set(["open", "closed"]),
    open: new Set(["merged", "closed"]),
    closed: new Set(["open"]),
    merged: new Set(),
  });

  constructor(id) {
    if (typeof id !== "string" || id.trim() === "") {
      throw new ValidationError("Pull request ID is required.");
    }

    this.id = id;
    this.state = "draft";
  }

  transition(nextState) {
    if (!Object.hasOwn(PullRequestWorkflow.transitions, this.state)) {
      throw new StateTransitionError(`Unknown current state: ${this.state}`);
    }

    const permitted = PullRequestWorkflow.transitions[this.state];

    if (!permitted.has(nextState)) {
      throw new StateTransitionError(
        `Cannot transition pull request ${this.id} from ${this.state} to ${nextState}.`
      );
    }

    this.state = nextState;
    return this.state;
  }
}

function demonstrateStateErrors() {
  console.log("\n--- Invalid state transitions ---");

  const pullRequest = new PullRequestWorkflow("PR-108");
  pullRequest.transition("open");
  pullRequest.transition("merged");
  console.log("Final state:", pullRequest.state);

  try {
    pullRequest.transition("open");
  } catch (error) {
    console.error(error.name, error.message);
  }
}

// Assertions make executable contracts visible. They are not a replacement
// for production input validation because Node.js can disable assertions.
function assert(condition, message) {
  if (!condition) {
    throw new Error(`Assertion failed: ${message}`);
  }
}

async function runSelfTests() {
  assert(parsePort(8080) === 8080, "valid port");
  assert(
    (() => {
      try {
        parsePort(0);
        return false;
      } catch (error) {
        return error instanceof ValidationError;
      }
    })(),
    "invalid port rejected"
  );

  const config = parseDeploymentConfiguration(
    '{"environment":"staging","port":8081}'
  );
  assert(config.port === 8081, "configuration parsed");

  let attempts = 0;
  const recovered = await retryAsync(
    async () => {
      attempts += 1;
      if (attempts < 2) {
        throw new ExternalServiceError("Temporary failure.");
      }
      return "ok";
    },
    { attempts: 2, initialDelayMs: 0 }
  );
  assert(recovered === "ok", "retry recovered");

  const outcomes = await runIndependentChecks([
    async () => 1,
    async () => {
      throw new Error("expected");
    },
  ]);
  assert(outcomes[0].status === "fulfilled", "successful task retained");
  assert(outcomes[1].status === "rejected", "failed task retained");

  const workflow = new PullRequestWorkflow("PR-109");
  workflow.transition("open");

  let transitionRejected = false;
  try {
    workflow.transition("merged");
  } catch (error) {
    transitionRejected = error instanceof StateTransitionError;
  }
  assert(transitionRejected, "draft cannot merge without opening");

  console.log("\nAll JavaScript self-tests passed.");
}

async function main() {
  demonstrateSynchronousHandling();
  demonstrateErrorCauses();
  await demonstrateAsyncHandling();
  await demonstrateRetries();
  await demonstrateConcurrentChecks();
  demonstrateEventDrivenErrors();
  demonstrateStateErrors();
  await runSelfTests();
}

main().catch((error) => {
  // This final boundary prevents an unhandled rejection from disappearing
  // without diagnostics. It also sets a failure exit code for automation.
  console.error("Fatal application failure:", error);
  process.exitCode = 1;
});
