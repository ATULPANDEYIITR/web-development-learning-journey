"use strict";

/**
 * Advanced object model: descriptors, accessors, integrity levels, prototypes.
 * Run with Node.js 18 or later. No third-party dependencies are required.
 */

function attempt(label, operation) {
  try {
    const result = operation();
    console.log(`${label}:`, result);
  } catch (error) {
    console.log(`${label}: ${error.name}: ${error.message}`);
  }
}

function inspectDescriptor(object, property) {
  const descriptor = Object.getOwnPropertyDescriptor(object, property);

  if (descriptor === undefined) {
    console.log(`${property}: property does not exist`);
    return;
  }

  // Accessor descriptors expose get/set; data descriptors expose value/writable.
  console.log(`${property} descriptor:`, {
    enumerable: descriptor.enumerable,
    configurable: descriptor.configurable,
    hasGetter: typeof descriptor.get === "function",
    hasSetter: typeof descriptor.set === "function",
    writable: Object.hasOwn(descriptor, "writable")
      ? descriptor.writable
      : undefined,
    value: Object.hasOwn(descriptor, "value")
      ? descriptor.value
      : undefined,
  });
}

function demonstrateDataDescriptors() {
  console.log("\nData property descriptors");

  const release = {};

  Object.defineProperty(release, "version", {
    value: "3.2.1",
    writable: false,
    enumerable: true,
    configurable: false,
  });

  Object.defineProperty(release, "buildToken", {
    value: "internal-build-82",
    writable: true,
    enumerable: false,
    configurable: true,
  });

  console.log("Enumerable keys:", Object.keys(release));
  console.log("All own string keys:", Object.getOwnPropertyNames(release));
  inspectDescriptor(release, "version");
  inspectDescriptor(release, "buildToken");

  attempt("Modify immutable version", () => {
    release.version = "3.2.2";
    return release.version;
  });

  attempt("Delete non-configurable version", () => {
    return delete release.version;
  });
}

function demonstrateAccessors() {
  console.log("\nValidated accessors");

  const account = {
    owner: "Operations",
    _balance: 2500,

    get balance() {
      return this._balance;
    },

    set balance(amount) {
      if (typeof amount !== "number" || !Number.isFinite(amount)) {
        throw new TypeError("Balance must be a finite number.");
      }

      if (amount < 0) {
        throw new RangeError("Balance cannot be negative.");
      }

      this._balance = amount;
    },

    get summary() {
      return `${this.owner}: ${this.balance.toFixed(2)}`;
    },
  };

  account.balance += 450;
  console.log(account.summary);
  inspectDescriptor(account, "balance");
  inspectDescriptor(Object.getPrototypeOf(account), "balance");

  attempt("Assign negative balance", () => {
    account.balance = -10;
  });

  attempt("Assign NaN", () => {
    account.balance = Number.NaN;
  });

  // Object literal methods and accessors normally live on the instance here.
  console.log("Own accessor:", Object.hasOwn(account, "balance"));
}

function demonstrateIntegrityLevels() {
  console.log("\nObject integrity levels");

  const ordinary = { state: "draft" };
  Object.preventExtensions(ordinary);

  console.log("Extensible:", Object.isExtensible(ordinary));
  attempt("Add property", () => {
    ordinary.owner = "release-team";
    return ordinary.owner;
  });

  const sealed = { state: "draft" };
  Object.seal(sealed);

  sealed.state = "approved";
  console.log("Sealed value remains writable:", sealed.state);
  console.log("Sealed:", Object.isSealed(sealed));

  attempt("Add sealed property", () => {
    sealed.approver = "reviewer-1";
  });

  const frozen = { version: "3.2.1" };
  Object.freeze(frozen);

  console.log("Frozen:", Object.isFrozen(frozen));
  attempt("Update frozen property", () => {
    frozen.version = "3.2.2";
  });

  // Object.freeze is shallow. The nested object has its own integrity state.
  const deployment = Object.freeze({
    metadata: { region: "ap-south-1" },
  });

  deployment.metadata.region = "eu-west-1";
  console.log("Nested value remains mutable:", deployment.metadata.region);

  // Freezing the outer object does not freeze accessor setter behavior either.
  let privateCount = 0;
  const counter = Object.freeze({
    get count() {
      return privateCount;
    },
    set count(value) {
      if (!Number.isInteger(value) || value < 0) {
        throw new RangeError("Count must be a non-negative integer.");
      }
      privateCount = value;
    },
  });

  counter.count = 7;
  console.log("Frozen accessor with external state:", counter.count);
}

function demonstratePrototypeInheritance() {
  console.log("\nPrototype inheritance and shadowing");

  const servicePrototype = {
    category: "internal-service",
    healthCheck() {
      return `${this.name}: healthy`;
    },
  };

  const service = Object.create(servicePrototype);
  service.name = "inventory-api";

  console.log("Inherited method:", service.healthCheck());
  console.log("Own name:", Object.hasOwn(service, "name"));
  console.log("Own category:", Object.hasOwn(service, "category"));
  console.log("Category:", service.category);

  // An own property shadows, but does not modify, the prototype property.
  service.category = "public-service";
  console.log("Shadowed category:", service.category);
  console.log("Prototype category:", servicePrototype.category);

  console.log(
    "Prototype relation:",
    Object.getPrototypeOf(service) === servicePrototype,
  );

  attempt("Prototype lookup for missing property", () => service.region);
}

function demonstratePropertyDefinitionRules() {
  console.log("\nDescriptor redefinition rules");

  const policy = {};

  Object.defineProperty(policy, "requiredApprovals", {
    value: 2,
    writable: false,
    enumerable: true,
    configurable: false,
  });

  attempt("Make non-configurable property writable", () => {
    Object.defineProperty(policy, "requiredApprovals", {
      writable: true,
    });
  });

  attempt("Change non-configurable value", () => {
    Object.defineProperty(policy, "requiredApprovals", {
      value: 3,
    });
  });

  // A compatible descriptor can be supplied without changing locked fields.
  Object.defineProperty(policy, "requiredApprovals", {
    enumerable: true,
  });

  console.log("Required approvals:", policy.requiredApprovals);
}

function demonstrateCopyingAndDescriptors() {
  console.log("\nCopying objects and descriptors");

  const source = {};

  Object.defineProperty(source, "secret", {
    value: "deployment-key-reference",
    writable: false,
    enumerable: false,
    configurable: false,
  });

  source.name = "release-policy";

  // Object.assign copies enumerable values, not their original descriptors.
  const assigned = Object.assign({}, source);

  // This method preserves property descriptors, including non-enumerability.
  const descriptorCopy = Object.create(
    Object.getPrototypeOf(source),
    Object.getOwnPropertyDescriptors(source),
  );

  console.log("Assigned keys:", Object.keys(assigned));
  console.log("Assigned secret descriptor:");
  inspectDescriptor(assigned, "secret");

  console.log("Descriptor-copy own names:", Object.getOwnPropertyNames(descriptorCopy));
  inspectDescriptor(descriptorCopy, "secret");
}

function main() {
  demonstrateDataDescriptors();
  demonstrateAccessors();
  demonstrateIntegrityLevels();
  demonstratePrototypeInheritance();
  demonstratePropertyDefinitionRules();
  demonstrateCopyingAndDescriptors();
  console.log("\nAdvanced object demonstrations completed.");
}

main();
