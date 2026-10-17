"use strict";

/**
 * JavaScript `this`: method invocation, constructors, call, apply, bind,
 * and arrow functions.
 *
 * Run with Node.js:
 *   node this_keyword_lab.js
 */

function heading(title) {
  console.log(`\n========== ${title} ==========`);
}

function showReceiver() {
  return {
    receiver: this,
    name: this?.name ?? "(no name)",
    department: this?.department ?? "(no department)"
  };
}

function describeTask(task, urgency = "normal") {
  return `${this.name} in ${this.department}: ${task} [${urgency}]`;
}

function demonstrateMethodInvocation() {
  heading("Method invocation");

  const reviewer = {
    name: "Maya",
    department: "Engineering",
    describe() {
      // For reviewer.describe(), this is reviewer.
      return `${this.name} reviews engineering changes.`;
    }
  };

  console.log(reviewer.describe());

  const extracted = reviewer.describe;

  // The receiver is not retained merely because a function came from
  // an object. Strict mode leaves this undefined in this invocation.
  try {
    console.log(extracted());
  } catch (error) {
    console.log("Extracted method failed:", error.name);
  }

  // Explicitly supply the intended receiver.
  console.log(extracted.call(reviewer));
}

function demonstrateCallApplyBind() {
  heading("call, apply, and bind");

  const engineering = {
    name: "Arun",
    department: "Engineering"
  };

  const security = {
    name: "Leena",
    department: "Cybersecurity"
  };

  // call passes positional arguments after the chosen receiver.
  console.log(
    "call:",
    describeTask.call(engineering, "approve the patch", "high")
  );

  // apply passes arguments as an array-like object.
  console.log(
    "apply:",
    describeTask.apply(security, [
      "inspect authentication changes",
      "critical"
    ])
  );

  // bind returns a new function. It does not invoke the original function.
  const boundReview = describeTask.bind(
    engineering,
    "merge the validated change"
  );

  console.log("bind:", boundReview("normal"));

  // A bound receiver cannot be replaced by another call's receiver.
  console.log(
    "bound receiver remains:",
    boundReview.call(security, "urgent")
  );

  // Bound arguments are supplied before later invocation arguments.
  const partiallyBound = describeTask.bind(security);
  console.log(partiallyBound("audit permissions", "high"));
}

function demonstrateConstructors() {
  heading("Constructors and new");

  function RepositoryMember(name, role) {
    // With new RepositoryMember(...), this refers to the new instance.
    this.name = name;
    this.role = role;
  }

  RepositoryMember.prototype.describe = function () {
    return `${this.name} has role ${this.role}.`;
  };

  const member = new RepositoryMember("Nina", "REVIEWER");
  console.log(member.describe());
  console.log("Instance check:", member instanceof RepositoryMember);

  // Calling a constructor without new is unsafe in strict mode because
  // this is undefined. The guard produces a clear error instead.
  function SafeMember(name) {
    if (!new.target) {
      throw new TypeError("SafeMember must be called with new");
    }
    this.name = name;
  }

  try {
    SafeMember("Incorrect invocation");
  } catch (error) {
    console.log("Constructor guard:", error.message);
  }
}

function demonstrateArrowFunctions() {
  heading("Arrow functions and lexical this");

  const dashboard = {
    owner: "Atul",

    makeCallbacks() {
      // The arrow captures this from makeCallbacks().
      const arrow = () => `Arrow owner: ${this.owner}`;

      // A normal function receives this from its invocation expression.
      function ordinary() {
        return `Ordinary receiver: ${this?.owner ?? "undefined"}`;
      }

      return { arrow, ordinary };
    }
  };

  const { arrow, ordinary } = dashboard.makeCallbacks();

  console.log(arrow());
  console.log(ordinary.call({ owner: "External Reviewer" }));

  // call, apply, and bind cannot replace an arrow's lexical this.
  console.log(
    arrow.call({ owner: "Ignored Receiver" })
  );

  const fixedArrow = arrow.bind({ owner: "Also Ignored" });
  console.log(fixedArrow());

  // Arrow functions have no own arguments object. Rest parameters provide
  // explicit access to their arguments when needed.
  const summarizeArguments = (...values) => values.join(" | ");
  console.log(summarizeArguments("pull request", "approval", "checks"));
}

function demonstrateEventHandlerContext() {
  heading("Event handlers and callback context");

  const buttonModel = {
    label: "Merge reviewed pull request",

    click() {
      return `Clicked: ${this.label}`;
    }
  };

  const handler = buttonModel.click;

  try {
    handler();
  } catch (error) {
    console.log("Detached handler:", error.name);
  }

  const safeHandler = buttonModel.click.bind(buttonModel);
  console.log(safeHandler());

  // In browsers, ordinary DOM event handlers may receive the event target
  // as this, while arrow handlers retain lexical this. Node.js has no DOM,
  // so this object models the receiver behavior without browser dependencies.
}

function demonstratePolicyCallback() {
  heading("Review policy callback");

  const pullRequest = {
    number: 42,
    title: "Require authorization for merge operations",
    approvals: 2,
    requiredApprovals: 2,
    checks: {
      lint: "success",
      tests: "success",
      security: "success"
    },

    isMergeEligible() {
      const checksPassed = Object.values(this.checks).every(
        status => status === "success"
      );

      return (
        this.approvals >= this.requiredApprovals &&
        checksPassed
      );
    }
  };

  console.log(
    `PR #${pullRequest.number}: ${pullRequest.title}`
  );
  console.log("Eligible:", pullRequest.isMergeEligible());

  const eligibility = pullRequest.isMergeEligible;
  console.log(
    "Bound policy result:",
    eligibility.bind(pullRequest)()
  );

  // Arrow callbacks used by every() do not need the outer object's this:
  // they receive each status as their argument.
}

function main() {
  demonstrateMethodInvocation();
  demonstrateCallApplyBind();
  demonstrateConstructors();
  demonstrateArrowFunctions();
  demonstrateEventHandlerContext();
  demonstratePolicyCallback();
}

main();
