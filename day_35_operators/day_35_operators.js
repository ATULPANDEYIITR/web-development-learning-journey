"use strict";

/*
 * Operator Laboratory
 * Covers arithmetic, comparison, logical, assignment, ternary,
 * nullish coalescing, and optional chaining using JavaScript-specific
 * runtime behavior.
 */

function heading(title) {
  console.log(`\n${"=".repeat(72)}\n${title}\n${"=".repeat(72)}`);
}

function arithmeticDemo() {
  heading("Arithmetic operators");

  const a = 17;
  const b = 5;

  console.log("a + b =", a + b);
  console.log("a - b =", a - b);
  console.log("a * b =", a * b);
  console.log("a / b =", a / b);
  console.log("a % b =", a % b);
  console.log("a ** b =", a ** b);

  // JavaScript has both increment/decrement and compound assignment.
  let counter = 10;
  counter += 3;
  counter -= 2;
  counter *= 4;
  counter /= 2;
  console.log("compound assignment result =", counter);

  console.log("10 / 0 =", 10 / 0);
  console.log("0 / 0 =", 0 / 0);
}

function comparisonDemo() {
  heading("Comparison operators");

  const numberValue = 5;
  const stringValue = "5";

  console.log("5 == '5'  ->", numberValue == stringValue);
  console.log("5 === '5' ->", numberValue === stringValue);
  console.log("5 != '5'  ->", numberValue != stringValue);
  console.log("5 !== '5' ->", numberValue !== stringValue);
  console.log("5 > 3     ->", numberValue > 3);
  console.log("5 >= 5    ->", numberValue >= 5);
  console.log("5 < 8     ->", numberValue < 8);
  console.log("5 <= 5    ->", numberValue <= 5);

  // Strict equality avoids implicit type coercion.
  const input = "42";
  const expected = 42;
  console.log("strict comparison of user input:", input === expected);
}

function logicalDemo() {
  heading("Logical operators and short-circuit evaluation");

  const authenticated = true;
  const active = true;
  const administrator = false;

  console.log("authenticated && active:", authenticated && active);
  console.log("authenticated || administrator:", authenticated || administrator);
  console.log("!administrator:", !administrator);

  function expensiveAuthorizationCheck() {
    console.log("expensive authorization check executed");
    return true;
  }

  // The second operand is not evaluated because false already determines
  // the result of &&.
  const shortCircuit = false && expensiveAuthorizationCheck();
  console.log("short-circuit result:", shortCircuit);

  // && and || return operand values, not necessarily Boolean values.
  const configuredRegion = "";
  const region = configuredRegion || "IN";
  console.log("fallback with ||:", region);
}

function assignmentDemo() {
  heading("Assignment operators");

  let value = 20;

  value += 5;
  value -= 3;
  value *= 2;
  value /= 4;
  value %= 6;

  console.log("final value:", value);

  // Logical assignment operators update a variable only when the
  // corresponding logical condition requires it.
  let displayName = "";
  displayName ||= "Anonymous";
  console.log("||= result:", displayName);

  let retryCount = 0;
  retryCount ??= 3;
  console.log("??= preserves zero:", retryCount);

  let cacheValue = null;
  cacheValue ??= "loaded";
  console.log("??= replaces null:", cacheValue);
}

function ternaryDemo() {
  heading("Ternary operator");

  const score = 84;
  const classification = score >= 50 ? "pass" : "fail";
  console.log("classification:", classification);

  const environment = "production";
  const endpoint =
    environment === "production"
      ? "https://api.example.com"
      : "http://localhost:3000";

  console.log("selected endpoint:", endpoint);
}

function nullishCoalescingDemo() {
  heading("Nullish coalescing");

  const values = [null, undefined, 0, "", false, "configured"];

  for (const value of values) {
    console.log(`${JSON.stringify(value)} ?? "default" ->`, value ?? "default");
  }

  // Unlike ||, ?? treats 0, "", and false as valid values.
  const configuredTimeout = 0;
  console.log("timeout with ||:", configuredTimeout || 5000);
  console.log("timeout with ??:", configuredTimeout ?? 5000);
}

function optionalChainingDemo() {
  heading("Optional chaining");

  const user = {
    profile: {
      contact: {
        email: "engineer@example.com"
      }
    }
  };

  const userWithoutProfile = {};

  console.log("existing email:", user.profile?.contact?.email);
  console.log(
    "missing email:",
    userWithoutProfile.profile?.contact?.email ?? "not supplied"
  );

  // Optional call prevents an exception when the method does not exist.
  const logger = {
    info(message) {
      console.log("logger:", message);
    }
  };

  const unavailableLogger = null;
  logger?.info("deployment approved");
  unavailableLogger?.info("this is safely skipped");
}

function precedenceDemo() {
  heading("Precedence and explicit grouping");

  console.log("2 + 3 * 4 =", 2 + 3 * 4);
  console.log("(2 + 3) * 4 =", (2 + 3) * 4);

  const authenticated = true;
  const role = "reviewer";
  const approved = true;

  const canMerge =
    authenticated &&
    (role === "maintainer" || role === "reviewer") &&
    approved;

  console.log("can merge:", canMerge);
}

function pipelinePolicyDemo() {
  heading("Event-driven merge policy evaluation");

  const pullRequest = {
    number: 42,
    targetBranch: "main",
    draft: false,
    approvals: 2,
    failingChecks: 0,
    changedFiles: 7,
    author: {
      account: {
        active: true
      }
    }
  };

  const policy = {
    requiredApprovals: 2,
    maximumChangedFiles: 20,
    protectedBranch: "main"
  };

  const events = [];

  function evaluatePullRequest(pr) {
    const authorActive = pr.author?.account?.active ?? false;
    const branchAllowed = pr.targetBranch === policy.protectedBranch;
    const reviewAllowed = pr.approvals >= policy.requiredApprovals;
    const checksAllowed = pr.failingChecks === 0;
    const sizeAllowed = pr.changedFiles <= policy.maximumChangedFiles;

    const eligible =
      !pr.draft &&
      authorActive &&
      branchAllowed &&
      reviewAllowed &&
      checksAllowed &&
      sizeAllowed;

    events.push({
      type: "merge-policy-evaluated",
      pullRequest: pr.number,
      eligible
    });

    return eligible;
  }

  console.log("merge eligible:", evaluatePullRequest(pullRequest));
  console.log("event emitted:", events[0]);
}

function numericEdgeCasesDemo() {
  heading("Numeric edge cases");

  console.log("Number.isNaN(NaN):", Number.isNaN(NaN));
  console.log("Number.isFinite(42):", Number.isFinite(42));
  console.log("Number.isFinite(Infinity):", Number.isFinite(Infinity));

  const result = 0.1 + 0.2;
  console.log("0.1 + 0.2 =", result);
  console.log("exactly 0.3:", result === 0.3);
  console.log(
    "within tolerance:",
    Math.abs(result - 0.3) < Number.EPSILON
  );
}

function runAssertions() {
  heading("Executable checks");

  console.assert(7 + 3 === 10);
  console.assert(7 * 3 === 21);
  console.assert(10 % 3 === 1);
  console.assert(5 < 8 && 8 < 10);
  console.assert((80 >= 50 ? "pass" : "fail") === "pass");
  console.assert((null ?? "fallback") === "fallback");
  console.assert((0 ?? "fallback") === 0);

  console.log("All operator checks passed.");
}

function main() {
  arithmeticDemo();
  comparisonDemo();
  logicalDemo();
  assignmentDemo();
  ternaryDemo();
  nullishCoalescingDemo();
  optionalChainingDemo();
  precedenceDemo();
  pipelinePolicyDemo();
  numericEdgeCasesDemo();
  runAssertions();
}

main();
