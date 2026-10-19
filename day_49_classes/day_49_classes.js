"use strict";

/*
 * Classes in JavaScript are built on prototypes, but the class syntax provides
 * constructor-based object creation, inheritance, private fields, and static
 * members in a form suitable for domain modeling.
 */

class ValidationError extends Error {
    constructor(message) {
        super(message);
        this.name = "ValidationError";
    }
}

class Employee {
    static nextId = 1;
    static activeEmployees = 0;
    static organization = "Northstar Systems";

    #id;
    #name;
    #salary;
    #active;

    constructor(name, salary) {
        const normalizedName = String(name).trim();

        if (!normalizedName) {
            throw new ValidationError("Employee name cannot be empty.");
        }

        if (!Number.isFinite(salary) || salary < 0) {
            throw new ValidationError("Salary must be a non-negative number.");
        }

        this.#id = Employee.nextId++;
        this.#name = normalizedName;
        this.#salary = salary;
        this.#active = true;

        Employee.activeEmployees++;
    }

    get id() {
        return this.#id;
    }

    get name() {
        return this.#name;
    }

    get salary() {
        return this.#salary;
    }

    get active() {
        return this.#active;
    }

    giveRaise(amount) {
        if (!this.#active) {
            throw new ValidationError("Inactive employees cannot receive raises.");
        }

        if (!Number.isFinite(amount) || amount <= 0) {
            throw new ValidationError("Raise must be positive.");
        }

        this.#salary = Math.round((this.#salary + amount) * 100) / 100;
    }

    deactivate() {
        if (!this.#active) {
            throw new ValidationError("Employee is already inactive.");
        }

        this.#active = false;
        Employee.activeEmployees--;
    }

    describe() {
        return `${this.#name} earns ${this.#salary.toFixed(2)}`;
    }

    static normalizeSalary(value) {
        if (!Number.isFinite(value) || value < 0) {
            throw new ValidationError("Salary must be a valid non-negative number.");
        }

        return Math.round(value * 100) / 100;
    }

    static getOrganizationStatus() {
        return `${Employee.organization}: ${Employee.activeEmployees} active employees`;
    }
}

class Engineer extends Employee {
    static defaultDepartment = "Engineering";
    #specialization;

    constructor(name, salary, specialization) {
        super(name, salary);

        const normalizedSpecialization = String(specialization).trim();

        if (!normalizedSpecialization) {
            // The parent constructor has already allocated an employee. Since
            // construction is failing, compensate for that class-level count.
            Employee.activeEmployees--;
            throw new ValidationError("Engineering specialization is required.");
        }

        this.#specialization = normalizedSpecialization;
    }

    get specialization() {
        return this.#specialization;
    }

    describe() {
        return `${super.describe()} as a ${this.#specialization} engineer`;
    }

    buildCapability() {
        return `${this.name} contributes to ${Engineer.defaultDepartment}`;
    }
}

class Manager extends Employee {
    #team = new Set();

    constructor(name, salary) {
        super(name, salary);
    }

    addReport(employee) {
        if (!(employee instanceof Employee)) {
            throw new ValidationError("A manager can only manage Employee objects.");
        }

        if (employee === this) {
            throw new ValidationError("A manager cannot report to itself.");
        }

        this.#team.add(employee);
    }

    get teamSize() {
        return this.#team.size;
    }

    payrollResponsibility() {
        let total = 0;

        for (const employee of this.#team) {
            total += employee.salary;
        }

        return Math.round(total * 100) / 100;
    }

    describe() {
        return `${super.describe()} and manages ${this.teamSize} employees`;
    }
}

function demonstrateConstructionAndPrivateFields() {
    console.log("=== Construction and private fields ===");

    const engineer = new Engineer(
        "Aarav Mehta",
        95000,
        "Platform Engineering"
    );

    console.log(engineer.describe());

    // JavaScript private fields cannot be accessed as engineer.#salary outside
    // the declaring class. The public getter provides controlled read access.
    console.log("Salary through getter:", engineer.salary);

    console.log("Static organization:", Employee.organization);
    console.log(Employee.getOrganizationStatus());
}

function demonstrateInheritanceAndPolymorphism() {
    console.log("\n=== Inheritance and polymorphism ===");

    const engineer = new Engineer("Priya Rao", 105000, "Cloud");
    const manager = new Manager("Daniel Wong", 130000);

    manager.addReport(engineer);

    const staff = [engineer, manager];

    for (const employee of staff) {
        console.log(employee.describe());
    }

    console.log(engineer.buildCapability());
    console.log("Manager payroll responsibility:", manager.payrollResponsibility());
}

function demonstrateStaticMembers() {
    console.log("\n=== Static members ===");

    console.log("Next employee ID:", Employee.nextId);
    console.log("Default engineering department:", Engineer.defaultDepartment);

    const normalized = Employee.normalizeSalary(87342.789);
    console.log("Normalized salary:", normalized);

    const employee = new Employee("Static Member Test", normalized);
    console.log(Employee.getOrganizationStatus());

    employee.deactivate();
    console.log(Employee.getOrganizationStatus());
}

async function demonstrateEventDrivenClassBehavior() {
    console.log("\n=== Event-driven class behavior ===");

    class EmployeeEventBus {
        #handlers = new Map();

        on(eventName, handler) {
            if (typeof handler !== "function") {
                throw new TypeError("Event handler must be a function.");
            }

            if (!this.#handlers.has(eventName)) {
                this.#handlers.set(eventName, new Set());
            }

            this.#handlers.get(eventName).add(handler);
        }

        emit(eventName, payload) {
            const handlers = this.#handlers.get(eventName) ?? [];

            for (const handler of handlers) {
                handler(payload);
            }
        }
    }

    const bus = new EmployeeEventBus();

    bus.on("salaryChanged", ({ employee, oldSalary, newSalary }) => {
        console.log(
            `${employee.name}: salary ${oldSalary.toFixed(2)} -> ${newSalary.toFixed(2)}`
        );
    });

    const engineer = new Engineer("Kabir Shah", 88000, "Security");
    const oldSalary = engineer.salary;

    engineer.giveRaise(7000);

    bus.emit("salaryChanged", {
        employee: engineer,
        oldSalary,
        newSalary: engineer.salary,
    });

    await Promise.resolve();
    console.log("Event processing completed asynchronously.");
}

function demonstrateValidation() {
    console.log("\n=== Validation ===");

    const attempts = [
        () => new Employee("", 50000),
        () => new Employee("Invalid Salary", -500),
        () => new Engineer("Missing Specialization", 70000, ""),
    ];

    for (const attempt of attempts) {
        try {
            attempt();
        } catch (error) {
            console.log(`${error.name}: ${error.message}`);
        }
    }
}

async function main() {
    demonstrateConstructionAndPrivateFields();
    demonstrateInheritanceAndPolymorphism();
    demonstrateStaticMembers();
    await demonstrateEventDrivenClassBehavior();
    demonstrateValidation();

    console.log("\n=== Final class state ===");
    console.log(Employee.getOrganizationStatus());
}

main().catch((error) => {
    console.error("Application failure:", error);
    process.exitCode = 1;
});
