'use strict';

/*
 * JavaScript Introduction
 *
 * This file is intentionally executable with a standard JavaScript runtime.
 * It demonstrates:
 *   - JavaScript's relationship with ECMAScript
 *   - execution environments
 *   - lexical syntax
 *   - expressions and values
 *   - statements and control flow
 *   - declarations and assignments
 *   - lexical scope
 *   - functions as expressions/values
 *   - runtime errors and validation
 *   - asynchronous host behavior
 *   - module/runtime-oriented design considerations
 *
 * Run with:
 *   node javascript-introduction.js
 *
 * Browser-specific APIs are demonstrated through feature detection instead
 * of assuming that a DOM exists.
 */


// ---------------------------------------------------------------------------
// Source syntax: expressions and values
// ---------------------------------------------------------------------------

function demonstrateExpressions() {
    console.log('\n=== Expressions and values ===');

    // An expression is evaluated to produce a value.
    const unitPrice = 1250;
    const quantity = 3;

    const subtotal = unitPrice * quantity;
    const tax = subtotal * 0.18;
    const total = subtotal + tax;

    console.log('subtotal:', subtotal);
    console.log('tax:', tax);
    console.log('total:', total);

    // The + operator has different behavior depending on operand types.
    const numericAddition = 10 + 5;
    const stringConcatenation = 'Order-' + quantity;

    console.log('numeric addition:', numericAddition);
    console.log('string concatenation:', stringConcatenation);

    // Parentheses make grouping explicit and can change evaluation order.
    const grouped = unitPrice * (quantity + 1);
    const ungrouped = unitPrice * quantity + 1;

    console.log('grouped expression:', grouped);
    console.log('ungrouped expression:', ungrouped);

    return total;
}


// ---------------------------------------------------------------------------
// Statements: declarations, assignments, and control flow
// ---------------------------------------------------------------------------

function demonstrateStatements() {
    console.log('\n=== Statements ===');

    // A declaration statement creates a binding.
    const price = 850;
    let quantity = 2;

    // An assignment expression changes an existing mutable binding.
    quantity = quantity + 1;

    const subtotal = price * quantity;

    if (subtotal >= 2000) {
        console.log('The order qualifies for the large-order path.');
    } else {
        console.log('The order uses the standard-order path.');
    }

    // A loop statement repeatedly executes a block of statements.
    let runningTotal = 0;

    for (let index = 0; index < quantity; index += 1) {
        runningTotal += price;
    }

    console.log('running total:', runningTotal);

    return {
        quantity,
        subtotal,
        runningTotal
    };
}


// ---------------------------------------------------------------------------
// ECMAScript concepts: language specification versus host environment
// ---------------------------------------------------------------------------

function describeExecutionEnvironment() {
    console.log('\n=== Execution environment ===');

    const environment = {
        node: typeof process !== 'undefined' && process.versions?.node,
        browser: typeof window !== 'undefined',
        document: typeof document !== 'undefined',
        fetch: typeof fetch === 'function',
        console: typeof console !== 'undefined'
    };

    console.log('Node.js:', Boolean(environment.node));
    console.log('Browser window:', environment.browser);
    console.log('DOM document:', environment.document);
    console.log('fetch available:', environment.fetch);
    console.log('console available:', environment.console);

    /*
     * ECMAScript specifies the language itself: grammar, values, objects,
     * functions, operators, control flow, and other language semantics.
     *
     * An execution environment supplies host capabilities. A browser exposes
     * APIs such as document and window; Node.js supplies APIs oriented toward
     * processes, files, networking, and server-side execution.
     */
}


// ---------------------------------------------------------------------------
// Lexical syntax
// ---------------------------------------------------------------------------

function demonstrateLexicalSyntax() {
    console.log('\n=== Lexical syntax ===');

    // Identifiers name bindings, functions, and other program entities.
    const customerName = 'Atul';

    // Numeric, string, boolean, null, and undefined are different values.
    const count = 4;
    const active = true;
    const missing = null;
    let notInitialized;

    console.log({
        customerName,
        count,
        active,
        missing,
        notInitialized
    });

    // Strict equality avoids implicit type conversion.
    console.log('10 === "10":', 10 === '10');
    console.log('10 == "10":', 10 == '10');

    /*
     * Automatic semicolon insertion is part of JavaScript's grammar rules.
     * Explicit semicolons make statement boundaries easier to inspect and
     * reduce ambiguity in many codebases, even though semicolons are often
     * optional.
     */
}


// ---------------------------------------------------------------------------
// Declarations and lexical scope
// ---------------------------------------------------------------------------

function demonstrateScope() {
    console.log('\n=== Declarations and lexical scope ===');

    const applicationName = 'Repository Explorer';
    let requestCount = 0;

    {
        const branchName = 'main';
        requestCount += 1;

        console.log('inside block:', {
            applicationName,
            branchName,
            requestCount
        });
    }

    /*
     * branchName exists only in the block where it was declared.
     * Attempting to read it outside that block would cause a ReferenceError.
     */
    console.log('outside block:', {
        applicationName,
        requestCount
    });

    function createRequestSummary() {
        const operation = 'load';
        requestCount += 1;

        return `${operation} request #${requestCount}`;
    }

    console.log(createRequestSummary());

    /*
     * Functions create nested lexical environments. The nested function can
     * read requestCount from its outer environment. This is a closure.
     */
}


// ---------------------------------------------------------------------------
// const, let, and var behavior
// ---------------------------------------------------------------------------

function demonstrateDeclarationSemantics() {
    console.log('\n=== Declaration semantics ===');

    const configuration = {
        retries: 3
    };

    // const prevents rebinding the variable, but does not freeze an object.
    configuration.retries = 5;

    console.log('mutable object through const binding:', configuration);

    let status = 'pending';
    status = 'ready';

    console.log('mutable let binding:', status);

    /*
     * var is function-scoped rather than block-scoped. This historical
     * behavior is one reason modern JavaScript code generally prefers const
     * and let for new declarations.
     */
    if (true) {
        var functionScopedValue = 'visible after the block';
    }

    console.log(functionScopedValue);
}


// ---------------------------------------------------------------------------
// Functions as values
// ---------------------------------------------------------------------------

function demonstrateFunctions() {
    console.log('\n=== Functions as values ===');

    // A function declaration creates a callable function.
    function calculateTotal(price, quantity, taxRate) {
        if (!Number.isFinite(price) || price < 0) {
            throw new TypeError('price must be a finite non-negative number');
        }

        if (!Number.isInteger(quantity) || quantity < 0) {
            throw new TypeError('quantity must be a non-negative integer');
        }

        if (!Number.isFinite(taxRate) || taxRate < 0) {
            throw new TypeError('taxRate must be a finite non-negative number');
        }

        const subtotal = price * quantity;
        return subtotal + subtotal * taxRate;
    }

    // An arrow function is another function expression.
    const formatCurrency = value => `₹${value.toFixed(2)}`;

    const total = calculateTotal(1250, 3, 0.18);

    console.log('calculated total:', formatCurrency(total));

    /*
     * Functions can be stored in variables and passed to other functions.
     * This is an important part of JavaScript's first-class function model.
     */
    const values = [100, 200, 300];
    const doubled = values.map(value => value * 2);

    console.log('map result:', doubled);
}


// ---------------------------------------------------------------------------
// Objects, property access, and data modeling
// ---------------------------------------------------------------------------

function demonstrateObjects() {
    console.log('\n=== Objects and property access ===');

    const repository = {
        name: 'javascript-learning-lab',
        defaultBranch: 'main',
        openIssues: 4,
        metadata: {
            language: 'JavaScript',
            active: true
        }
    };

    console.log('repository name:', repository.name);
    console.log('default branch:', repository.defaultBranch);
    console.log('nested property:', repository.metadata.language);

    /*
     * Object property access is an expression. It retrieves a value from an
     * object; it is not itself a declaration statement.
     */

    const { name, openIssues } = repository;

    console.log('destructured values:', {
        name,
        openIssues
    });
}


// ---------------------------------------------------------------------------
// Input validation and runtime failures
// ---------------------------------------------------------------------------

function demonstrateErrors() {
    console.log('\n=== Runtime errors ===');

    function parseQuantity(input) {
        const quantity = Number(input);

        if (!Number.isInteger(quantity) || quantity < 1) {
            throw new RangeError('Quantity must be a positive integer.');
        }

        return quantity;
    }

    const validInputs = ['3', 5];

    for (const input of validInputs) {
        console.log('validated quantity:', parseQuantity(input));
    }

    try {
        parseQuantity('not-a-number');
    } catch (error) {
        if (error instanceof RangeError) {
            console.log('validation failure:', error.message);
        } else {
            throw error;
        }
    }

    /*
     * JavaScript errors are runtime events. Syntax errors can prevent source
     * from being parsed at all, while runtime exceptions occur after valid
     * source has begun executing.
     */
}


// ---------------------------------------------------------------------------
// Event-driven and asynchronous execution
// ---------------------------------------------------------------------------

function demonstrateAsynchronousExecution() {
    console.log('\n=== Asynchronous execution ===');

    /*
     * setTimeout is a host-provided scheduling API. The callback is not run
     * immediately. The current synchronous call stack continues first.
     */
    console.log('synchronous: start');

    setTimeout(() => {
        console.log('timer callback: executed later');
    }, 0);

    console.log('synchronous: end');
}


async function demonstratePromises() {
    console.log('\n=== Promise and async/await ===');

    function delayedValue(value, delayMilliseconds) {
        return new Promise(resolve => {
            setTimeout(() => resolve(value), delayMilliseconds);
        });
    }

    console.log('requesting asynchronous value');

    const value = await delayedValue('ready', 10);

    console.log('resolved value:', value);

    /*
     * async functions return Promises. await pauses this async function until
     * the Promise settles, without blocking the entire JavaScript runtime.
     */
}


// ---------------------------------------------------------------------------
// A practical JavaScript execution pipeline
// ---------------------------------------------------------------------------

function demonstrateProgramPipeline() {
    console.log('\n=== Program execution pipeline ===');

    const sourceCharacteristics = {
        sourceText: 'const total = price * quantity;',
        lexicalElements: [
            'const',
            'total',
            '=',
            'price',
            '*',
            'quantity',
            ';'
        ],
        statementKind: 'variable declaration',
        expressionPart: 'price * quantity',
        resultingValue: 'depends on the current bindings'
    };

    console.table(sourceCharacteristics);

    /*
     * A JavaScript engine does much more internally than this object shows.
     * Source is parsed according to ECMAScript grammar, represented in
     * implementation-specific internal structures, and executed according to
     * ECMAScript semantics and the host environment's capabilities.
     */
}


// ---------------------------------------------------------------------------
// Main program
// ---------------------------------------------------------------------------

async function main() {
    console.log('JavaScript Introduction');
    console.log('ECMAScript, execution environments, syntax, statements, expressions');

    demonstrateExpressions();
    demonstrateStatements();
    describeExecutionEnvironment();
    demonstrateLexicalSyntax();
    demonstrateScope();
    demonstrateDeclarationSemantics();
    demonstrateFunctions();
    demonstrateObjects();
    demonstrateErrors();
    demonstrateProgramPipeline();

    /*
     * The asynchronous examples are deliberately near the end so that the
     * synchronous output demonstrates that scheduling a callback does not
     * immediately execute it.
     */
    demonstrateAsynchronousExecution();
    await demonstratePromises();

    console.log('\n=== Completed ===');
}

main().catch(error => {
    console.error('Unhandled application error:', error);
    process.exitCode = 1;
});
