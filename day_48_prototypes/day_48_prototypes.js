"use strict";

/*
 * Prototype chains, constructor functions, inheritance, and Object.create.
 * Run with Node.js or in a browser console.
 */

function printHeading(title) {
  console.log(`\n${title}`);
}

function inspectProperty(object, property) {
  const descriptor = Object.getOwnPropertyDescriptor(object, property);

  return {
    value: object[property],
    own: Object.hasOwn(object, property),
    enumerable: descriptor ? descriptor.enumerable : null,
  };
}

function demonstrateObjectCreate() {
  printHeading("Object.create and inherited properties");

  const devicePrototype = {
    category: "network-device",
    describe() {
      return `${this.name} is a ${this.category}`;
    },
  };

  const router = Object.create(devicePrototype);
  router.name = "Router-01";

  console.log(router.describe());
  console.log("Own name:", Object.hasOwn(router, "name"));
  console.log("Own category:", Object.hasOwn(router, "category"));
  console.log(
    "Prototype matches:",
    Object.getPrototypeOf(router) === devicePrototype
  );

  router.category = "wireless-router";

  console.log("Shadowed category:", router.category);
  console.log("Prototype category:", devicePrototype.category);
}

function demonstrateConstructorFunctions() {
  printHeading("Constructor functions and prototype methods");

  function Employee(employeeId, role) {
    if (!new.target) {
      throw new TypeError("Employee must be called with new");
    }

    if (typeof employeeId !== "string" || employeeId.trim() === "") {
      throw new TypeError("Employee ID must be a non-empty string");
    }

    this.employeeId = employeeId;
    this.role = role;
  }

  Employee.prototype.describe = function () {
    return `${this.employeeId}: ${this.role}`;
  };

  const engineer = new Employee("EMP-104", "Engineer");
  const analyst = new Employee("EMP-205", "Analyst");

  console.log(engineer.describe());
  console.log(analyst.describe());

  console.log(
    "Shared method:",
    engineer.describe === analyst.describe
  );

  console.log(
    "Prototype relationship:",
    Object.getPrototypeOf(engineer) === Employee.prototype
  );

  try {
    Employee("EMP-999", "Unsupported direct call");
  } catch (error) {
    console.log("Invalid invocation:", error.message);
  }
}

function demonstrateInheritance() {
  printHeading("Constructor-function inheritance");

  function Device(assetTag, manufacturer) {
    if (!new.target) {
      throw new TypeError("Device requires new");
    }

    this.assetTag = assetTag;
    this.manufacturer = manufacturer;
  }

  Device.prototype.describe = function () {
    return `${this.assetTag} by ${this.manufacturer}`;
  };

  function Server(assetTag, manufacturer, cpuCores) {
    if (!new.target) {
      throw new TypeError("Server requires new");
    }

    // Calling the parent constructor initializes instance-specific fields.
    Device.call(this, assetTag, manufacturer);
    this.cpuCores = cpuCores;
  }

  // This links Server instances to Device.prototype through the chain.
  // Replacing Server.prototype this way also requires restoring constructor.
  Server.prototype = Object.create(Device.prototype);

  Object.defineProperty(Server.prototype, "constructor", {
    value: Server,
    writable: true,
    configurable: true,
    enumerable: false,
  });

  Server.prototype.describe = function () {
    return `${Device.prototype.describe.call(this)} | ${this.cpuCores} cores`;
  };

  const server = new Server("SRV-001", "Example Systems", 32);

  console.log(server.describe());
  console.log("Is Device:", server instanceof Device);
  console.log("Is Server:", server instanceof Server);
  console.log(
    "Parent prototype:",
    Object.getPrototypeOf(Server.prototype) === Device.prototype
  );
  console.log(
    "Constructor restored:",
    server.constructor === Server
  );
}

function demonstrateClassesAndDescriptors() {
  printHeading("Classes and property descriptors");

  class Account {
    constructor(owner, balance = 0) {
      if (typeof owner !== "string" || owner.trim() === "") {
        throw new TypeError("Owner must be a non-empty string");
      }

      if (!Number.isFinite(balance) || balance < 0) {
        throw new RangeError("Balance must be finite and non-negative");
      }

      this.owner = owner;
      this.balance = balance;
    }

    deposit(amount) {
      if (!Number.isFinite(amount) || amount <= 0) {
        throw new RangeError("Deposit must be a positive finite number");
      }

      this.balance += amount;
      return this.balance;
    }
  }

  const first = new Account("Asha", 500);
  const second = new Account("Ravi", 200);

  first.deposit(75);

  console.log("First balance:", first.balance);
  console.log("Second balance:", second.balance);
  console.log(
    "Shared class method:",
    first.deposit === second.deposit
  );

  const descriptor = Object.getOwnPropertyDescriptor(
    Account.prototype,
    "deposit"
  );

  console.log("Method descriptor:", descriptor);
  console.log("Own balance:", Object.hasOwn(first, "balance"));
  console.log(
    "Inherited deposit:",
    Object.hasOwn(first, "deposit") === false
  );
}

function demonstrateNullPrototypeAndSafety() {
  printHeading("Null prototypes and safe dictionaries");

  // A null-prototype object has no inherited Object.prototype methods.
  const settings = Object.create(null);
  settings.theme = "dark";
  settings.enabled = true;

  console.log("Theme:", settings.theme);
  console.log("Prototype:", Object.getPrototypeOf(settings));

  // This is useful for dictionaries, but use own-property checks rather than
  // assuming methods such as hasOwnProperty exist on the object.
  console.log("Own theme:", Object.hasOwn(settings, "theme"));
  console.log("Own inherited-looking name:", Object.hasOwn(settings, "toString"));

  const ordinary = {};
  ordinary["__proto__"] = { compromised: true };

  console.log(
    "Prototype mutation risk in ordinary objects:",
    Object.getPrototypeOf(ordinary).compromised === true
  );

  const safeDictionary = Object.create(null);
  safeDictionary["__proto__"] = "ordinary data";

  console.log(
    "Safe dictionary value:",
    safeDictionary["__proto__"]
  );
  console.log(
    "Safe dictionary has no polluted prototype:",
    Object.getPrototypeOf(safeDictionary) === null
  );
}

function demonstratePrototypeLookup() {
  printHeading("Prototype-chain traversal");

  const base = { region: "India" };
  const middle = Object.create(base);
  middle.department = "Engineering";

  const employee = Object.create(middle);
  employee.name = "Asha";

  let current = employee;

  while (current !== null) {
    console.log(
      Object.keys(current),
      "has region:",
      Object.hasOwn(current, "region")
    );
    current = Object.getPrototypeOf(current);
  }

  console.log("Resolved region:", employee.region);
  console.log("Region owner:", Object.hasOwn(employee, "region"));
  console.log("Region inherited:", "region" in employee);
}

function main() {
  demonstrateObjectCreate();
  demonstrateConstructorFunctions();
  demonstrateInheritance();
  demonstrateClassesAndDescriptors();
  demonstrateNullPrototypeAndSafety();
  demonstratePrototypeLookup();
}

main();
