"use strict";

/*
 * Control flow in JavaScript determines which statements execute and how
 * execution moves through synchronous and asynchronous operations.
 *
 * This file uses practical workflow examples rather than isolated syntax.
 */

function classifyScore(score) {
  if (!Number.isFinite(score) || score < 0 || score > 100) {
    throw new RangeError("score must be a finite number from 0 to 100");
  }

  if (score >= 90) {
    return "A";
  } else if (score >= 80) {
    return "B";
  } else if (score >= 70) {
    return "C";
  } else if (score >= 60) {
    return "D";
  }

  return "F";
}

function authorizeUser({ authenticated, active, role }) {
  if (!authenticated) {
    return "authentication-required";
  }

  if (!active) {
    return "account-disabled";
  }

  switch (role) {
    case "admin":
      return "administrative-access";
    case "editor":
    case "reviewer":
      return "collaborative-access";
    case "viewer":
      return "read-only-access";
    default:
      return "unknown-role";
  }
}

function collectEvenNumbers(numbers) {
  const result = [];

  for (const number of numbers) {
    if (!Number.isInteger(number)) {
      continue;
    }

    if (number % 2 !== 0) {
      continue;
    }

    result.push(number);
  }

  return result;
}

function findFirstOverLimit(values, limit) {
  for (const value of values) {
    if (value > limit) {
      return value;
    }
  }

  return null;
}

function boundedCountdown(start) {
  if (!Number.isInteger(start) || start < 0) {
    throw new RangeError("start must be a non-negative integer");
  }

  const values = [];
  let current = start;

  while (current > 0) {
    values.push(current);
    current -= 1;
  }

  return values;
}

function commandAction(command) {
  switch (command.trim().toLowerCase()) {
    case "build":
      return "build-project";
    case "test":
      return "run-tests";
    case "deploy":
      return "deploy-project";
    case "status":
      return "show-status";
    default:
      return "unknown-command";
  }
}

function processEvents(events) {
  const statistics = {
    processed: 0,
    ignored: 0,
    failures: 0,
  };

  for (const event of events) {
    if (!event || typeof event.type !== "string") {
      statistics.ignored += 1;
      continue;
    }

    switch (event.type) {
      case "success":
        statistics.processed += 1;
        break;

      case "failure":
        statistics.processed += 1;
        statistics.failures += 1;
        break;

      case "heartbeat":
        // A heartbeat is valid but does not represent business work.
        continue;

      default:
        statistics.ignored += 1;
    }
  }

  return statistics;
}

class Workflow {
  constructor(name) {
    if (!name || typeof name !== "string") {
      throw new TypeError("workflow name must be a non-empty string");
    }

    this.name = name;
    this.state = "pending";
  }

  transition(event) {
    /*
     * The switch expresses allowed transitions explicitly. Invalid events
     * are rejected rather than silently changing the state.
     */
    switch (this.state) {
      case "pending":
        if (event === "validate") {
          this.state = "validating";
          return this.state;
        }
        break;

      case "validating":
        if (event === "pass") {
          this.state = "approved";
          return this.state;
        }

        if (event === "fail") {
          this.state = "failed";
          return this.state;
        }
        break;

      case "approved":
        if (event === "execute") {
          this.state = "completed";
          return this.state;
        }
        break;

      case "failed":
        if (event === "retry") {
          this.state = "pending";
          return this.state;
        }
        break;

      case "completed":
        break;

      default:
        throw new Error(`Unknown state: ${this.state}`);
    }

    throw new Error(`Invalid transition: ${this.state} + ${event}`);
  }
}

async function executeWithRetry(operation, maxAttempts) {
  if (!Number.isInteger(maxAttempts) || maxAttempts <= 0) {
    throw new RangeError("maxAttempts must be positive");
  }

  let lastError;

  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    try {
      return await operation(attempt);
    } catch (error) {
      lastError = error;

      if (attempt === maxAttempts) {
        break;
      }
    }
  }

  throw new Error(
    `operation failed after ${maxAttempts} attempts: ${lastError?.message ?? "unknown error"}`
  );
}

function buildValidationPipeline(records) {
  const accepted = [];
  const rejected = [];

  for (const [index, record] of records.entries()) {
    if (!record || typeof record !== "object") {
      rejected.push({ index, reason: "record is not an object" });
      continue;
    }

    if (!Number.isInteger(record.id)) {
      rejected.push({ index, reason: "id must be an integer" });
      continue;
    }

    if (typeof record.value !== "string" || record.value.length === 0) {
      rejected.push({ index, reason: "value must be a non-empty string" });
      continue;
    }

    accepted.push(record);
  }

  return { accepted, rejected };
}

function calculateDiscount(amount, customerType, riskScore) {
  if (!Number.isFinite(amount) || amount < 0) {
    throw new RangeError("amount must be non-negative");
  }

  if (!Number.isFinite(riskScore) || riskScore < 0 || riskScore > 1) {
    throw new RangeError("riskScore must be between 0 and 1");
  }

  if (riskScore >= 0.9) {
    return { status: "blocked", discount: 0 };
  }

  if (amount === 0) {
    return { status: "no-charge", discount: 0 };
  }

  if (customerType === "enterprise") {
    if (amount >= 10000) {
      return { status: "priority", discount: 0.15 };
    }

    return { status: "standard-enterprise", discount: 0.1 };
  }

  if (customerType === "student") {
    return { status: "student", discount: 0.2 };
  }

  return { status: "standard", discount: 0 };
}

async function run() {
  console.log("Conditional branching");
  console.log(classifyScore(94));
  console.log(classifyScore(76));
  console.log(
    authorizeUser({
      authenticated: true,
      active: true,
      role: "reviewer",
    })
  );

  console.log("\nLoops with continue and early termination");
  console.log(collectEvenNumbers([2, 5, "bad", 8, 11, 14]));
  console.log(findFirstOverLimit([4, 7, 9, 18, 21], 10));
  console.log(boundedCountdown(5));

  console.log("\nSwitch-based command dispatch");
  for (const command of ["build", "test", "deploy", "unknown"]) {
    console.log(command, "->", commandAction(command));
  }

  console.log("\nEvent processing");
  console.log(
    processEvents([
      { type: "success" },
      { type: "heartbeat" },
      { type: "failure" },
      null,
      { type: "unknown" },
    ])
  );

  console.log("\nExplicit state machine");
  const workflow = new Workflow("release-validation");
  console.log(workflow.state);
  console.log(workflow.transition("validate"));
  console.log(workflow.transition("pass"));
  console.log(workflow.transition("execute"));

  console.log("\nValidation pipeline");
  console.log(
    buildValidationPipeline([
      { id: 1, value: "valid" },
      { id: "2", value: "invalid" },
      { id: 3, value: "" },
      { id: 4, value: "valid" },
      null,
    ])
  );

  console.log("\nBusiness-rule branching");
  console.log(calculateDiscount(20000, "enterprise", 0.1));
  console.log(calculateDiscount(500, "student", 0.2));
  console.log(calculateDiscount(100, "consumer", 0.95));

  console.log("\nAsynchronous control flow with retry");

  let attempts = 0;

  const result = await executeWithRetry(async (attempt) => {
    attempts = attempt;

    if (attempt < 3) {
      throw new Error("temporary failure");
    }

    return `succeeded on attempt ${attempt}`;
  }, 4);

  console.log(result);
  console.log(`attempts used: ${attempts}`);
}

run().catch((error) => {
  console.error(`Execution failed: ${error.message}`);
  process.exitCode = 1;
});
