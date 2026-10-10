"use strict";

/*
 * Objects in JavaScript: properties, methods, nested objects,
 * destructuring, spread syntax, computed properties, and safe updates.
 *
 * Run with Node.js 18 or later:
 *     node objects_workshop.js
 */

function heading(title) {
  console.log(`\n${"=".repeat(68)}\n${title}\n${"=".repeat(68)}`);
}

function show(label, value) {
  console.log(`${label}:`, value);
}

heading("Properties, methods, and the receiver");

const repository = {
  owner: "platform",
  name: "checkout-api",
  stars: 12,

  // Method shorthand defines a function-valued property.
  // `this` refers to the receiver when called as repository.fullName().
  get fullName() {
    return `${this.owner}/${this.name}`;
  },

  addStars(count = 1) {
    if (!Number.isInteger(count) || count <= 0) {
      throw new RangeError("count must be a positive integer");
    }
    this.stars += count;
    return this.stars;
  },
};

show("Repository", repository.fullName);
show("Stars after increment", repository.addStars(3));

// Extracting a method loses its receiver unless it is explicitly bound.
const unboundMethod = repository.addStars;
try {
  unboundMethod(1);
} catch (error) {
  show("Unbound method behavior", error.name);
}

const boundMethod = repository.addStars.bind(repository);
show("Bound method result", boundMethod(2));

heading("Property descriptors and controlled mutation");

const deployment = {
  service: "inventory",
  replicas: 3,
};

Object.defineProperty(deployment, "productionReady", {
  enumerable: true,
  configurable: false,
  get() {
    return this.replicas >= 3;
  },
});

show("Computed property", deployment.productionReady);
show(
  "Descriptor",
  Object.getOwnPropertyDescriptor(deployment, "productionReady")
);

// Object.freeze is shallow: it prevents changes to this object's own
// properties but does not recursively freeze referenced nested objects.
Object.freeze(deployment);
try {
  deployment.replicas = 10;
} catch (error) {
  show("Frozen object assignment", error.name);
}
show("Replicas after attempted mutation", deployment.replicas);

heading("Nested objects and aliasing");

const pullRequest = {
  number: 107,
  title: "Validate webhook signatures",
  branches: {
    source: "feature/signature-validation",
    target: "main",
  },
  review: {
    required: true,
    approvals: [],
  },
  checks: {
    unitTests: "passed",
    securityScan: "passed",
  },
};

const sameReview = pullRequest.review;
sameReview.approvals.push({
  reviewer: "lee",
  state: "APPROVED",
});

show("Approval through original reference", pullRequest.review.approvals);
show("Nested branch", pullRequest.branches.source);

heading("Destructuring, defaults, and rest properties");

const {
  number,
  title,
  branches: { source, target },
  review: { approvals },
  draft = false,
  ...remainingFields
} = pullRequest;

show("Destructured fields", { number, title, source, target, approvals, draft });
show("Remaining top-level properties", remainingFields);

// A default applies to missing or undefined values, not to null.
const { reviewer = "unassigned" } = { reviewer: undefined };
const { reviewer: explicitNull = "unassigned" } = { reviewer: null };
show("Default for undefined", reviewer);
show("Default for null", explicitNull);

// Destructuring nested data should not assume that optional objects exist.
const externalPayload = { number: 108 };
const externalBranches = externalPayload.branches ?? {};
const { source: safeSource = "not-provided" } = externalBranches;
show("Safe optional extraction", safeSource);

heading("Spread syntax and shallow-copy semantics");

const baseConfiguration = {
  timeoutMs: 5000,
  retries: 2,
  headers: {
    accept: "application/json",
  },
};

const environmentOverrides = {
  timeoutMs: 10000,
  retries: 4,
};

// Properties appearing later take precedence when keys collide.
const effectiveConfiguration = {
  ...baseConfiguration,
  ...environmentOverrides,
};
show("Merged configuration", effectiveConfiguration);

// Spread copies the top level only; both configurations still reference
// the same headers object.
const shallowConfiguration = { ...baseConfiguration };
shallowConfiguration.headers.traceId = "trace-204";
show("Nested mutation visible in original", baseConfiguration.headers);

// structuredClone recursively copies supported structured-cloneable data.
// It does not preserve arbitrary prototypes, methods, or functions.
const isolatedConfiguration = structuredClone(baseConfiguration);
isolatedConfiguration.headers.traceId = "isolated";
show("Original headers after deep copy mutation", baseConfiguration.headers);
show("Isolated headers", isolatedConfiguration.headers);

heading("Computed property names and dynamic access");

const selectedMetric = "latencyMs";
const threshold = 250;

const metrics = {
  service: "checkout",
  [selectedMetric]: 184,
  [`${selectedMetric}Threshold`]: threshold,
  [`observedAt_${new Date().toISOString().slice(0, 10)}`]: 184,
};

show("Computed metric keys", metrics);

const permittedProperties = new Set(["name", "owner", "defaultBranch"]);

function readRepositoryProperty(object, propertyName) {
  if (!permittedProperties.has(propertyName)) {
    throw new Error(`Property is not permitted: ${propertyName}`);
  }
  if (!Object.hasOwn(object, propertyName)) {
    throw new Error(`Property does not exist: ${propertyName}`);
  }
  return object[propertyName];
}

const repositoryMetadata = {
  name: "checkout-api",
  owner: "platform",
  defaultBranch: "main",
};

show(
  "Dynamic property lookup",
  readRepositoryProperty(repositoryMetadata, "defaultBranch")
);

try {
  readRepositoryProperty(repositoryMetadata, "__proto__");
} catch (error) {
  show("Rejected dynamic lookup", error.message);
}

heading("Object construction and prototype behavior");

const servicePrototype = {
  describe() {
    return `${this.name} runs ${this.environment}`;
  },
};

const serviceInstance = Object.create(servicePrototype);
serviceInstance.name = "ledger";
serviceInstance.environment = "production";

show("Inherited method", serviceInstance.describe());
show("Own properties", Object.keys(serviceInstance));
show("Prototype relationship", Object.getPrototypeOf(serviceInstance) === servicePrototype);

// Object.assign mutates its first argument, unlike creating a new object
// with spread syntax. Keep the target isolated when mutation is undesirable.
const destination = { status: "pending" };
Object.assign(destination, { status: "validated", attempts: 2 });
show("Object.assign destination", destination);

heading("Object validation and serialization");

function validatePullRequest(candidate) {
  if (candidate === null || typeof candidate !== "object" || Array.isArray(candidate)) {
    throw new TypeError("Pull request must be a non-array object");
  }

  if (!Number.isSafeInteger(candidate.number) || candidate.number <= 0) {
    throw new TypeError("Pull request number must be a positive safe integer");
  }

  if (typeof candidate.title !== "string" || candidate.title.trim() === "") {
    throw new TypeError("Pull request title is required");
  }

  if (!candidate.branches || typeof candidate.branches !== "object") {
    throw new TypeError("Branch information is required");
  }

  if (
    typeof candidate.branches.source !== "string" ||
    typeof candidate.branches.target !== "string" ||
    candidate.branches.source === candidate.branches.target
  ) {
    throw new TypeError("Distinct source and target branches are required");
  }

  return true;
}

show("Valid payload", validatePullRequest(pullRequest));

try {
  validatePullRequest({
    number: -1,
    title: "",
    branches: { source: "main", target: "main" },
  });
} catch (error) {
  show("Invalid payload rejected", error.message);
}

const serializableView = {
  number: pullRequest.number,
  title: pullRequest.title,
  branches: { ...pullRequest.branches },
  approvalCount: pullRequest.review.approvals.length,
};

const serialized = JSON.stringify(serializableView, null, 2);
show("JSON representation", serialized);
show("Parsed title", JSON.parse(serialized).title);

heading("Asynchronous object updates");

class ReviewStore {
  #pullRequests = new Map();

  add(pullRequestRecord) {
    validatePullRequest(pullRequestRecord);
    if (this.#pullRequests.has(pullRequestRecord.number)) {
      throw new Error("Pull request number already exists");
    }

    // Store an isolated snapshot so callers cannot mutate internal state
    // by retaining a reference to the input object.
    this.#pullRequests.set(
      pullRequestRecord.number,
      structuredClone(pullRequestRecord)
    );
  }

  async approve(number, reviewer) {
    // The await point makes this API asynchronous even though the sample
    // uses an in-memory store. A remote implementation could await a request.
    await Promise.resolve();

    if (!Number.isSafeInteger(number) || number <= 0) {
      throw new TypeError("Invalid pull request number");
    }
    if (typeof reviewer !== "string" || reviewer.trim() === "") {
      throw new TypeError("Reviewer is required");
    }

    const record = this.#pullRequests.get(number);
    if (!record) {
      throw new Error(`Pull request ${number} does not exist`);
    }

    const existing = record.review.approvals.some(
      (entry) => entry.reviewer === reviewer
    );

    if (!existing) {
      record.review.approvals.push({
        reviewer,
        state: "APPROVED",
        submittedAt: new Date().toISOString(),
      });
    }

    return structuredClone(record);
  }

  get(number) {
    const record = this.#pullRequests.get(number);
    return record ? structuredClone(record) : undefined;
  }
}

async function main() {
  const store = new ReviewStore();
  store.add(pullRequest);

  const updated = await store.approve(107, "mira");
  show("Stored approval count", updated.review.approvals.length);

  const exposedSnapshot = store.get(107);
  exposedSnapshot.review.approvals.push({
    reviewer: "external",
    state: "APPROVED",
  });

  show(
    "Stored count remains isolated",
    store.get(107).review.approvals.length
  );

  try {
    await store.approve(999, "mira");
  } catch (error) {
    show("Missing record handled", error.message);
  }
}

main().catch((error) => {
  console.error("Unexpected execution failure:", error);
  process.exitCode = 1;
});
