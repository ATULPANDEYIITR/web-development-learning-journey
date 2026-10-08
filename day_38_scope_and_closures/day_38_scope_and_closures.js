"use strict";

/*
 * Scope and Closures in JavaScript
 *
 * This file uses JavaScript's lexical scoping model to demonstrate:
 * global scope, function scope, block scope, shadowing, lexical lookup,
 * closures, private state, callbacks, factories, decorators through
 * higher-order functions, asynchronous callbacks, and common pitfalls.
 *
 * Run with:
 *   node scope-and-closures.js
 */

// -----------------------------------------------------------------------------
// Global scope
// -----------------------------------------------------------------------------

const APPLICATION_NAME = "ScopeLab";
let globalRequestCount = 0;

function showGlobalScope() {
    console.log("\n=== Global scope ===");
    console.log("APPLICATION_NAME:", APPLICATION_NAME);
    console.log("globalRequestCount:", globalRequestCount);
}

function incrementGlobalRequestCount() {
    globalRequestCount += 1;
    return globalRequestCount;
}

// -----------------------------------------------------------------------------
// Function scope
// -----------------------------------------------------------------------------

function demonstrateFunctionScope() {
    console.log("\n=== Function scope ===");

    function calculate(value) {
        var functionScopedValue = value * 2;
        let blockAwareValue = value + 10;
        return {
            functionScopedValue,
            blockAwareValue
        };
    }

    console.log(calculate(7));

    // var is function-scoped, so this variable is not visible here because
    // calculate() has a different function scope.
    try {
        console.log(functionScopedValue);
    } catch (error) {
        console.log("Expected ReferenceError:", error.message);
    }
}

// -----------------------------------------------------------------------------
// Block scope
// -----------------------------------------------------------------------------

function demonstrateBlockScope() {
    console.log("\n=== Block scope ===");

    if (true) {
        let blockValue = "inside block";
        const immutableBlockValue = "also inside block";
        var functionValue = "function scoped despite block";

        console.log(blockValue);
        console.log(immutableBlockValue);
    }

    console.log("var survives the block:", functionValue);

    try {
        console.log(blockValue);
    } catch (error) {
        console.log("let is block-scoped:", error.message);
    }

    try {
        console.log(immutableBlockValue);
    } catch (error) {
        console.log("const is block-scoped:", error.message);
    }

    // for-loop let creates a fresh lexical binding for each iteration.
    const callbacks = [];

    for (let index = 0; index < 3; index += 1) {
        callbacks.push(() => index);
    }

    console.log("Per-iteration lexical bindings:", callbacks.map(fn => fn()));

    // var uses one function-scoped binding, producing the classic closure issue.
    const legacyCallbacks = [];

    for (var index = 0; index < 3; index += 1) {
        legacyCallbacks.push(() => index);
    }

    console.log("Shared var binding:", legacyCallbacks.map(fn => fn()));
}

// -----------------------------------------------------------------------------
// Lexical scope and shadowing
// -----------------------------------------------------------------------------

const environment = "global environment";

function demonstrateLexicalScope() {
    const environment = "function environment";

    function inspectEnvironment() {
        const environment = "nested environment";

        // JavaScript resolves the nearest lexical binding first.
        console.log("Nearest binding:", environment);
    }

    inspectEnvironment();
    console.log("Function binding:", environment);
    console.log("Global binding:", globalThis.environment);
}

// -----------------------------------------------------------------------------
// Closures
// -----------------------------------------------------------------------------

function makeMultiplier(factor) {
    return function multiply(value) {
        // factor belongs to makeMultiplier's lexical environment. The returned
        // function retains access to that environment after makeMultiplier ends.
        return value * factor;
    };
}

function demonstrateBasicClosure() {
    console.log("\n=== Basic closure ===");

    const multiplyByThree = makeMultiplier(3);
    const multiplyByTen = makeMultiplier(10);

    console.log("3 * 8 =", multiplyByThree(8));
    console.log("10 * 8 =", multiplyByTen(8));
}

// -----------------------------------------------------------------------------
// Stateful closures
// -----------------------------------------------------------------------------

function makeCounter(start = 0) {
    let count = start;

    return function nextValue() {
        count += 1;
        return count;
    };
}

function demonstrateStatefulClosures() {
    console.log("\n=== Stateful closures ===");

    const firstCounter = makeCounter(10);
    const secondCounter = makeCounter(100);

    console.log(firstCounter());
    console.log(firstCounter());
    console.log(secondCounter());
    console.log(secondCounter());

    // Each returned function has its own lexical environment.
}

// -----------------------------------------------------------------------------
// Closure factory with private state
// -----------------------------------------------------------------------------

function createAccount(initialBalance) {
    if (!Number.isFinite(initialBalance) || initialBalance < 0) {
        throw new RangeError("initialBalance must be a non-negative number");
    }

    let balance = initialBalance;

    return Object.freeze({
        deposit(amount) {
            if (!Number.isFinite(amount) || amount <= 0) {
                throw new RangeError("deposit must be a positive number");
            }

            balance += amount;
        },

        withdraw(amount) {
            if (!Number.isFinite(amount) || amount <= 0) {
                throw new RangeError("withdrawal must be positive");
            }

            if (amount > balance) {
                throw new RangeError("insufficient funds");
            }

            balance -= amount;
        },

        getBalance() {
            return balance;
        }
    });
}

function demonstratePrivateState() {
    console.log("\n=== Closure-based private state ===");

    const account = createAccount(500);
    account.deposit(250);
    account.withdraw(100);

    console.log("Balance:", account.getBalance());
    console.log("Direct balance access:", account.balance);
}

// -----------------------------------------------------------------------------
// Configuration closures
// -----------------------------------------------------------------------------

function makeValidator(minimum, maximum) {
    if (!Number.isFinite(minimum) || !Number.isFinite(maximum)) {
        throw new TypeError("validation boundaries must be finite numbers");
    }

    if (minimum > maximum) {
        throw new RangeError("minimum cannot exceed maximum");
    }

    return value => (
        Number.isFinite(value) &&
        value >= minimum &&
        value <= maximum
    );
}

function demonstrateValidatorClosure() {
    console.log("\n=== Configuration through closures ===");

    const ageValidator = makeValidator(18, 120);
    const scoreValidator = makeValidator(0, 100);

    console.log("Age 25:", ageValidator(25));
    console.log("Age 12:", ageValidator(12));
    console.log("Score 90:", scoreValidator(90));
    console.log("Score 140:", scoreValidator(140));
}

// -----------------------------------------------------------------------------
// Higher-order function acting as a decorator
// -----------------------------------------------------------------------------

function withAudit(operationName, operation) {
    return function auditedOperation(...args) {
        console.log(`[AUDIT] start: ${operationName}`);

        try {
            const result = operation(...args);
            console.log(`[AUDIT] success: ${operationName}`, result);
            return result;
        } catch (error) {
            console.log(`[AUDIT] failure: ${operationName}: ${error.message}`);
            throw error;
        }
    };
}

function demonstrateDecoratorStyleClosure() {
    console.log("\n=== Higher-order function closure ===");

    const calculateTotal = withAudit(
        "calculateTotal",
        (price, quantity) => {
            if (price < 0 || quantity < 0) {
                throw new RangeError("price and quantity must be non-negative");
            }

            return price * quantity;
        }
    );

    console.log("Total:", calculateTotal(19.99, 3));
}

// -----------------------------------------------------------------------------
// Memoization closure
// -----------------------------------------------------------------------------

function memoizeUnary(operation) {
    const cache = new Map();

    return function memoized(value) {
        if (cache.has(value)) {
            return cache.get(value);
        }

        const result = operation(value);
        cache.set(value, result);
        return result;
    };
}

function demonstrateMemoization() {
    console.log("\n=== Memoization closure ===");

    const fibonacci = memoizeUnary(function calculateFibonacci(n) {
        if (!Number.isInteger(n) || n < 0) {
            throw new RangeError("n must be a non-negative integer");
        }

        if (n < 2) {
            return n;
        }

        return fibonacci(n - 1) + fibonacci(n - 2);
    });

    console.log("Fibonacci(35):", fibonacci(35));
    console.log("Repeated lookup:", fibonacci(35));
}

// -----------------------------------------------------------------------------
// Lexical closure with asynchronous callbacks
// -----------------------------------------------------------------------------

function delay(milliseconds) {
    return new Promise(resolve => setTimeout(resolve, milliseconds));
}

async function demonstrateAsyncClosure() {
    console.log("\n=== Asynchronous closure ===");

    const events = ["database", "cache", "queue"];

    const handlers = events.map(eventName => {
        return async function processEvent() {
            await delay(5);

            // eventName is retained by this callback even after map() finishes.
            return `Processed ${eventName}`;
        };
    });

    const results = await Promise.all(handlers.map(handler => handler()));

    for (const result of results) {
        console.log(result);
    }
}

// -----------------------------------------------------------------------------
// Late binding and its JavaScript-specific forms
// -----------------------------------------------------------------------------

function createVarCallbacks() {
    const callbacks = [];

    for (var index = 0; index < 3; index += 1) {
        callbacks.push(() => index);
    }

    return callbacks;
}

function createLetCallbacks() {
    const callbacks = [];

    for (let index = 0; index < 3; index += 1) {
        callbacks.push(() => index);
    }

    return callbacks;
}

function demonstrateLoopClosureBehavior() {
    console.log("\n=== Loop and closure behavior ===");

    console.log(
        "var callbacks:",
        createVarCallbacks().map(callback => callback())
    );

    console.log(
        "let callbacks:",
        createLetCallbacks().map(callback => callback())
    );
}

// -----------------------------------------------------------------------------
// Nested lexical environments
// -----------------------------------------------------------------------------

function makeFormatter(prefix, suffix) {
    const normalizedPrefix = String(prefix);
    const normalizedSuffix = String(suffix);

    return function format(value) {
        const text = String(value);
        return `${normalizedPrefix}${text}${normalizedSuffix}`;
    };
}

function demonstrateNestedLexicalEnvironment() {
    console.log("\n=== Nested lexical environment ===");

    const currencyFormatter = makeFormatter("$", "");
    const labelFormatter = makeFormatter("[", "]");

    console.log(currencyFormatter("125.50"));
    console.log(labelFormatter("production"));
}

// -----------------------------------------------------------------------------
// Scope-related failure modes
// -----------------------------------------------------------------------------

function demonstrateTemporalDeadZone() {
    console.log("\n=== Temporal Dead Zone ===");

    try {
        console.log(uninitializedValue);
        let uninitializedValue = 10;
    } catch (error) {
        console.log("Expected ReferenceError:", error.message);
    }

    // The declaration exists lexically but cannot be accessed before
    // initialization. This differs from var, whose binding is initialized
    // with undefined during environment creation.
}

// -----------------------------------------------------------------------------
// Event handler factory
// -----------------------------------------------------------------------------

function createSeverityHandler(eventType, minimumSeverity) {
    if (!Number.isInteger(minimumSeverity) || minimumSeverity < 0) {
        throw new RangeError("minimumSeverity must be a non-negative integer");
    }

    return event => (
        event &&
        event.type === eventType &&
        Number.isInteger(event.severity) &&
        event.severity >= minimumSeverity
    );
}

function processEvents(events, handlers) {
    if (!Array.isArray(events) || !Array.isArray(handlers)) {
        throw new TypeError("events and handlers must be arrays");
    }

    return events.filter(event =>
        handlers.some(handler => handler(event))
    );
}

function demonstrateCallbackClosures() {
    console.log("\n=== Callback closures ===");

    const events = [
        { type: "security", severity: 5, message: "login anomaly" },
        { type: "performance", severity: 2, message: "slow request" },
        { type: "security", severity: 1, message: "minor event" }
    ];

    const securityHandler = createSeverityHandler("security", 4);
    const performanceHandler = createSeverityHandler("performance", 3);

    console.log(
        processEvents(events, [securityHandler, performanceHandler])
    );
}

// -----------------------------------------------------------------------------
// Assertions
// -----------------------------------------------------------------------------

function runAssertions() {
    const multiplyByFour = makeMultiplier(4);
    console.assert(multiplyByFour(5) === 20);

    const validator = makeValidator(10, 20);
    console.assert(validator(10) === true);
    console.assert(validator(21) === false);

    const counterA = makeCounter();
    const counterB = makeCounter();

    console.assert(counterA() === 1);
    console.assert(counterA() === 2);
    console.assert(counterB() === 1);

    const account = createAccount(100);
    account.deposit(50);
    console.assert(account.getBalance() === 150);

    console.log("\nAll JavaScript scope and closure assertions passed.");
}

// -----------------------------------------------------------------------------
// Main
// -----------------------------------------------------------------------------

async function main() {
    console.log(`${APPLICATION_NAME}: Scope and Closures`);

    showGlobalScope();
    incrementGlobalRequestCount();
    demonstrateFunctionScope();
    demonstrateBlockScope();
    demonstrateLexicalScope();
    demonstrateBasicClosure();
    demonstrateStatefulClosures();
    demonstratePrivateState();
    demonstrateValidatorClosure();
    demonstrateDecoratorStyleClosure();
    demonstrateMemoization();
    await demonstrateAsyncClosure();
    demonstrateLoopClosureBehavior();
    demonstrateNestedLexicalEnvironment();
    demonstrateTemporalDeadZone();
    demonstrateCallbackClosures();
    runAssertions();
}

main().catch(error => {
    console.error("Fatal error:", error);
    process.exitCode = 1;
});
