"use strict";

/*
 * Functions in JavaScript are first-class values.
 * This file progresses from declarations to expressions, arrow functions,
 * parameters, return values, scope, closures, callbacks, composition,
 * asynchronous functions, validation, and practical error handling.
 */

function greet(name) {
    return `Hello, ${name}!`;
}

function calculateTotal(price, quantity = 1) {
    if (!Number.isFinite(price) || price < 0) {
        throw new RangeError("price must be a non-negative finite number");
    }

    if (!Number.isInteger(quantity) || quantity < 0) {
        throw new RangeError("quantity must be a non-negative integer");
    }

    return price * quantity;
}

// Function expression: the function is assigned to a variable.
const calculateDiscount = function (amount, rate) {
    if (!Number.isFinite(amount) || !Number.isFinite(rate)) {
        throw new TypeError("amount and rate must be finite numbers");
    }

    if (rate < 0 || rate > 1) {
        throw new RangeError("rate must be between 0 and 1");
    }

    return amount * (1 - rate);
};

// Arrow function: concise syntax for functions that do not need their own `this`.
const square = (number) => number * number;

const applyOperation = (value, operation) => {
    if (typeof operation !== "function") {
        throw new TypeError("operation must be a function");
    }

    return operation(value);
};

function makeMultiplier(factor) {
    if (!Number.isFinite(factor)) {
        throw new TypeError("factor must be finite");
    }

    // The returned function closes over factor.
    return (value) => value * factor;
}

function demonstrateScope() {
    const outerValue = "outer scope";

    function inner() {
        const innerValue = "inner scope";
        return `${outerValue} | ${innerValue}`;
    }

    return inner();
}

function createCounter() {
    let count = 0;

    return () => {
        count += 1;
        return count;
    };
}

function summarizeNumbers(numbers) {
    if (!Array.isArray(numbers) || numbers.length === 0) {
        throw new TypeError("numbers must be a non-empty array");
    }

    if (!numbers.every(Number.isFinite)) {
        throw new TypeError("all values must be finite numbers");
    }

    const total = numbers.reduce((sum, value) => sum + value, 0);

    return {
        count: numbers.length,
        minimum: Math.min(...numbers),
        maximum: Math.max(...numbers),
        average: total / numbers.length
    };
}

function divide(dividend, divisor) {
    if (!Number.isFinite(dividend) || !Number.isFinite(divisor)) {
        throw new TypeError("operands must be finite numbers");
    }

    if (divisor === 0) {
        throw new RangeError("division by zero is not allowed");
    }

    return dividend / divisor;
}

function safeCall(fn, ...args) {
    if (typeof fn !== "function") {
        throw new TypeError("fn must be a function");
    }

    try {
        return {
            success: true,
            value: fn(...args)
        };
    } catch (error) {
        return {
            success: false,
            error: error instanceof Error ? error.message : String(error)
        };
    }
}

function compose(first, second) {
    if (typeof first !== "function" || typeof second !== "function") {
        throw new TypeError("both arguments must be functions");
    }

    return (value) => second(first(value));
}

function pipeline(value, ...functions) {
    return functions.reduce((currentValue, fn) => {
        if (typeof fn !== "function") {
            throw new TypeError("every pipeline element must be a function");
        }

        return fn(currentValue);
    }, value);
}

class PayrollService {
    constructor(taxRate) {
        if (!Number.isFinite(taxRate) || taxRate < 0 || taxRate > 1) {
            throw new RangeError("taxRate must be between 0 and 1");
        }

        this.taxRate = taxRate;
    }

    grossPay(employee, bonus = 0) {
        if (!employee || typeof employee !== "object") {
            throw new TypeError("employee must be an object");
        }

        if (!Number.isFinite(employee.salary) || employee.salary < 0) {
            throw new RangeError("salary must be non-negative");
        }

        if (!Number.isFinite(bonus) || bonus < 0) {
            throw new RangeError("bonus must be non-negative");
        }

        return employee.salary + bonus;
    }

    netPay(employee, bonus = 0) {
        return this.grossPay(employee, bonus) * (1 - this.taxRate);
    }
}

function createRangeValidator(minimum, maximum) {
    if (!Number.isFinite(minimum) || !Number.isFinite(maximum)) {
        throw new TypeError("bounds must be finite numbers");
    }

    if (minimum > maximum) {
        throw new RangeError("minimum cannot exceed maximum");
    }

    return (value) => Number.isFinite(value) &&
        value >= minimum &&
        value <= maximum;
}

function delayedValue(value, milliseconds) {
    return new Promise((resolve, reject) => {
        if (!Number.isFinite(milliseconds) || milliseconds < 0) {
            reject(new RangeError("delay must be non-negative"));
            return;
        }

        setTimeout(() => resolve(value), milliseconds);
    });
}

async function runAsyncExample() {
    const value = await delayedValue("asynchronous return value", 10);
    return value.toUpperCase();
}

function runExamples() {
    console.log("=== Function declaration ===");
    console.log(greet("Atul"));

    console.log("\n=== Parameters and return values ===");
    console.log(calculateTotal(250, 3));
    console.log(calculateTotal(100));
    console.log(calculateDiscount(1000, 0.15));

    console.log("\n=== Arrow functions and callbacks ===");
    console.log(square(8));
    console.log(applyOperation(7, square));
    console.log(applyOperation(5, (value) => value * 3));

    console.log("\n=== Function collections ===");
    const operations = new Map([
        ["square", square],
        ["double", (value) => value * 2],
        ["absolute", Math.abs]
    ]);

    for (const [name, operation] of operations) {
        console.log(name, "->", applyOperation(-5, operation));
    }

    console.log("\n=== Scope and closures ===");
    console.log(demonstrateScope());

    const triple = makeMultiplier(3);
    console.log(triple(10));

    const counter = createCounter();
    console.log(counter());
    console.log(counter());
    console.log(counter());

    console.log("\n=== Data processing ===");
    console.log(summarizeNumbers([10, 20, 30, 40]));

    console.log("\n=== Error handling ===");
    console.log(safeCall(divide, 10, 2));
    console.log(safeCall(divide, 10, 0));
    console.log(safeCall(calculateTotal, -10, 2));

    console.log("\n=== Function composition ===");
    const addTen = (value) => value + 10;
    const multiplyTwo = (value) => value * 2;
    const composed = compose(addTen, multiplyTwo);
    console.log(composed(5));

    console.log("\n=== Pipeline ===");
    console.log(
        pipeline(
            5,
            (value) => value + 10,
            (value) => value * 2,
            square
        )
    );

    console.log("\n=== Enterprise-style method functions ===");
    const employee = { name: "Ravi", salary: 60000 };
    const payroll = new PayrollService(0.20);
    console.log("Gross:", payroll.grossPay(employee, 5000));
    console.log("Net:", payroll.netPay(employee, 5000));

    console.log("\n=== Generated validation function ===");
    const percentageValidator = createRangeValidator(0, 100);
    for (const value of [-5, 25, 100, 110]) {
        console.log(value, "->", percentageValidator(value));
    }

    console.log("\n=== Asynchronous function return value ===");
    runAsyncExample()
        .then((result) => console.log(result))
        .catch((error) => console.error(error.message));
}

runExamples();
