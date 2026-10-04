'use strict';

/*
 * JavaScript Variables and Data Types
 *
 * This file is intentionally JavaScript-native rather than a translation of
 * the accompanying Python model. It demonstrates:
 *
 *   var, let, const
 *   strings
 *   numbers
 *   booleans
 *   null
 *   undefined
 *   symbols
 *   BigInt
 *
 * It also uses JavaScript-specific mechanisms such as block scope, temporal
 * dead zones, property keys, typeof behavior, Number.isSafeInteger, BigInt
 * arithmetic, structured validation, and event-driven processing.
 *
 * Run with:
 *   node javascript_data_types.js
 */

const OUTPUT_PREFIX = '[data-types]';

function logHeading(title) {
    console.log(`\n${OUTPUT_PREFIX} ${title}`);
    console.log('-'.repeat(title.length + OUTPUT_PREFIX.length + 1));
}

/*
 * var is function-scoped, while let and const are block-scoped.
 * This example intentionally keeps the declarations in separate functions
 * so that the difference can be observed without creating invalid duplicate
 * declarations in the same lexical scope.
 */
function demonstrateVarLetConst() {
    logHeading('var, let, and const');

    function varScopeExample() {
        if (true) {
            var functionScoped = 'visible outside the block';
        }

        // var escaped the if block because its scope is the surrounding
        // function rather than the block.
        return functionScoped;
    }

    function lexicalScopeExample() {
        let blockScoped = 'visible only inside this block';
        const immutableBinding = 'cannot be rebound';

        if (true) {
            blockScoped = 'reassigned inside the same lexical scope';
            console.log(`let inside block: ${blockScoped}`);
            console.log(`const inside block: ${immutableBinding}`);
        }

        return blockScoped;
    }

    console.log(`var result: ${varScopeExample()}`);
    console.log(`let result: ${lexicalScopeExample()}`);

    let retryCount = 2;
    retryCount += 1;
    console.log(`let retryCount after reassignment: ${retryCount}`);

    const repositoryName = 'variables-and-data-types';
    console.log(`const repositoryName: ${repositoryName}`);

    try {
        // Assignment to a const binding is rejected at runtime.
        // eval is avoided because the invalid assignment would otherwise make
        // this demonstration harder to keep in a single executable program.
        const fixedValue = 10;
        Object.defineProperty(
            { fixedValue },
            'fixedValue',
            { writable: false }
        );
        console.log(`const binding remains: ${fixedValue}`);
    } catch (error) {
        console.error(`const demonstration failed: ${error.message}`);
    }

    /*
     * const protects the binding, not the object referred to by that binding.
     * The object's properties can still change unless the object itself is
     * frozen or otherwise protected.
     */
    const configuration = {
        mode: 'development',
        retries: 2
    };

    configuration.mode = 'production';
    configuration.retries += 1;

    console.log('const object after property mutation:', configuration);
}

/*
 * The temporal dead zone means a let/const binding exists in its lexical
 * scope but cannot be read before initialization.
 */
function demonstrateTemporalDeadZone() {
    logHeading('Temporal dead zone');

    try {
        {
            // Reading lexicalBinding before its declaration would throw a
            // ReferenceError. eval lets this failure be demonstrated without
            // making the entire source file invalid.
            eval('console.log(lexicalBinding); let lexicalBinding = 10;');
        }
    } catch (error) {
        console.log(`TDZ access rejected with ${error.name}: ${error.message}`);
    }

    /*
     * var behaves differently: its declaration is hoisted and its binding is
     * initialized with undefined before the assignment is reached.
     */
    function varHoistingExample() {
        console.log(`var before assignment: ${hoistedValue}`);
        var hoistedValue = 'assigned later';
        return hoistedValue;
    }

    console.log(`var after assignment: ${varHoistingExample()}`);
}

/*
 * Strings are primitive immutable values. Methods such as trim, replace,
 * split, and toUpperCase return new strings rather than mutating the original.
 */
function demonstrateStrings() {
    logHeading('Strings');

    const owner = 'ATULPANDEYIITR';
    const repository = 'variables-and-data-types';

    const repositoryPath = `${owner}/${repository}`;
    console.log(`Template literal: ${repositoryPath}`);

    const rawBranchName = '  feature/data-types  ';
    const normalizedBranchName = rawBranchName.trim().toLowerCase();

    console.log(`Original branch name: ${JSON.stringify(rawBranchName)}`);
    console.log(`Normalized branch name: ${normalizedBranchName}`);
    console.log(`String length: ${normalizedBranchName.length}`);
    console.log(
        `Starts with feature/: ${normalizedBranchName.startsWith('feature/')}`
    );

    const commitMessage = 'Use const for immutable bindings';
    const words = commitMessage.split(/\s+/);

    console.log(`Commit message words: ${JSON.stringify(words)}`);

    /*
     * JavaScript strings use UTF-16 code units. Therefore a character such as
     * the rocket emoji occupies two UTF-16 code units even though it is one
     * Unicode code point.
     */
    const unicodeText = 'JavaScript 🚀';
    console.log(`Unicode text: ${unicodeText}`);
    console.log(`UTF-16 length: ${unicodeText.length}`);
    console.log(
        `Code point count: ${Array.from(unicodeText).length}`
    );

    /*
     * User-controlled text should be validated before it becomes a branch,
     * identifier, or command argument. This simple rule rejects control
     * characters and path separators that are not allowed by this model.
     */
    function validateBranchName(name) {
        if (typeof name !== 'string') {
            throw new TypeError('Branch name must be a string');
        }

        if (name.length === 0 || name.length > 100) {
            throw new RangeError('Branch name length is outside the allowed range');
        }

        if (/[\r\n\t]/.test(name)) {
            throw new Error('Branch name contains control whitespace');
        }

        if (name.includes('..')) {
            throw new Error('Branch name contains a path traversal sequence');
        }

        return name;
    }

    console.log(
        `Validated branch: ${validateBranchName(normalizedBranchName)}`
    );
}

/*
 * JavaScript Number is an IEEE-754 double-precision floating-point value.
 * It can represent fractional values but has a finite exact-integer range.
 */
function demonstrateNumbers() {
    logHeading('Numbers');

    const reviewCount = 42;
    const approvalRate = 0.875;
    const negativeOffset = -12;

    console.log(`reviewCount: ${reviewCount}`);
    console.log(`approvalRate: ${approvalRate}`);
    console.log(`negativeOffset: ${negativeOffset}`);

    const floatingPointResult = 0.1 + 0.2;
    console.log(`0.1 + 0.2: ${floatingPointResult}`);
    console.log(
        `Rounded for display: ${floatingPointResult.toFixed(2)}`
    );

    console.log(`Number.MAX_SAFE_INTEGER: ${Number.MAX_SAFE_INTEGER}`);
    console.log(`Number.MIN_SAFE_INTEGER: ${Number.MIN_SAFE_INTEGER}`);

    const safeInteger = Number.MAX_SAFE_INTEGER;
    const unsafeInteger = safeInteger + 1;

    console.log(`Safe integer check: ${Number.isSafeInteger(safeInteger)}`);
    console.log(`Unsafe integer check: ${Number.isSafeInteger(unsafeInteger)}`);

    /*
     * Number can represent NaN and positive/negative Infinity. These values
     * require explicit checks because NaN does not equal itself.
     */
    const invalidNumber = Number('not-a-number');
    const positiveInfinity = Number.POSITIVE_INFINITY;

    console.log(`Number('not-a-number') is NaN: ${Number.isNaN(invalidNumber)}`);
    console.log(
        `Infinity is finite: ${Number.isFinite(positiveInfinity)}`
    );
    console.log(`NaN !== NaN: ${invalidNumber !== invalidNumber}`);

    const parsedRetryCount = Number.parseInt('3', 10);
    const parsedTimeout = Number.parseFloat('15.5');

    if (!Number.isInteger(parsedRetryCount) || parsedRetryCount < 0) {
        throw new RangeError('Retry count is invalid');
    }

    if (!Number.isFinite(parsedTimeout) || parsedTimeout <= 0) {
        throw new RangeError('Timeout must be a positive finite number');
    }

    console.log(`Parsed retry count: ${parsedRetryCount}`);
    console.log(`Parsed timeout: ${parsedTimeout}`);
}

/*
 * Booleans have exactly two primitive values: true and false.
 * Business decisions should generally use explicit conditions instead of
 * relying on accidental truthiness.
 */
function demonstrateBooleans() {
    logHeading('Booleans');

    const testsPassed = true;
    const hasConflicts = false;
    const requiredReviewComplete = true;

    const mergeAllowed =
        testsPassed &&
        !hasConflicts &&
        requiredReviewComplete;

    console.log(`testsPassed: ${testsPassed}`);
    console.log(`hasConflicts: ${hasConflicts}`);
    console.log(`requiredReviewComplete: ${requiredReviewComplete}`);
    console.log(`mergeAllowed: ${mergeAllowed}`);

    const rawFlag = 'true';
    const parsedFlag = rawFlag.toLowerCase() === 'true';

    console.log(`Parsed string flag: ${parsedFlag}`);

    /*
     * Avoid Boolean("false") when parsing textual configuration:
     * Boolean("false") is true because every non-empty string is truthy.
     */
    console.log(`Boolean("false"): ${Boolean('false')}`);
    console.log(`Explicit "false" parsing: ${'false'.toLowerCase() === 'true'}`);
}

/*
 * null represents an intentional absence of a value. undefined commonly
 * represents an absent property, an uninitialized var, or a function that
 * returns without a value.
 */
function demonstrateNullAndUndefined() {
    logHeading('null and undefined');

    const intentionallyEmpty = null;
    let missingValue;

    console.log(`null value: ${intentionallyEmpty}`);
    console.log(`undefined value: ${missingValue}`);

    console.log(`typeof null: ${typeof intentionallyEmpty}`);
    console.log(`typeof undefined: ${typeof missingValue}`);

    const record = {
        title: 'Variable declaration review',
        description: null
    };

    console.log(`Existing property: ${record.title}`);
    console.log(`Intentional empty property: ${record.description}`);
    console.log(`Missing property: ${record.reviewer}`);

    console.log(
        `Object.hasOwn(record, "description"): ${
            Object.hasOwn(record, 'description')
        }`
    );
    console.log(
        `Object.hasOwn(record, "reviewer"): ${
            Object.hasOwn(record, 'reviewer')
        }`
    );

    /*
     * Nullish coalescing treats only null and undefined as absent, unlike ||
     * which also treats 0, false, and "" as falsy.
     */
    const reviewer = record.reviewer ?? 'unassigned';
    const description = record.description ?? 'No description supplied';

    console.log(`Reviewer fallback: ${reviewer}`);
    console.log(`Description fallback: ${description}`);

    const zeroValue = 0;
    console.log(`0 ?? 100: ${zeroValue ?? 100}`);
    console.log(`0 || 100: ${zeroValue || 100}`);
}

/*
 * Symbols are unique primitive values. Their uniqueness makes them useful for
 * object property keys that should not collide with ordinary string keys.
 */
function demonstrateSymbols() {
    logHeading('Symbols');

    const first = Symbol('repositoryId');
    const second = Symbol('repositoryId');

    console.log(`typeof first: ${typeof first}`);
    console.log(`Same description: ${first.description === second.description}`);
    console.log(`Same identity: ${first === second}`);

    const metadata = {
        repositoryId: 'public-id'
    };

    const internalKey = Symbol('repositoryId');
    metadata[internalKey] = 'private metadata';

    console.log(`String property: ${metadata.repositoryId}`);
    console.log(`Symbol property: ${metadata[internalKey]}`);
    console.log(
        `Object.keys excludes symbol keys: ${Object.keys(metadata).join(', ')}`
    );
    console.log(
        `Reflect.ownKeys includes symbol keys: ${
            Reflect.ownKeys(metadata).length
        }`
    );

    /*
     * Symbol.for creates a shared symbol from the global symbol registry.
     * Symbol("x") and Symbol.for("x") do not use the same mechanism.
     */
    const registryA = Symbol.for('sharedRepositoryMarker');
    const registryB = Symbol.for('sharedRepositoryMarker');

    console.log(`Global registry symbols match: ${registryA === registryB}`);
    console.log(`Registry key: ${Symbol.keyFor(registryA)}`);
}

/*
 * BigInt represents arbitrary-precision integers. It is appropriate when exact
 * integer arithmetic is required beyond Number's safe-integer range.
 */
function demonstrateBigInt() {
    logHeading('BigInt');

    const accountBalance = 900719925474099312345n;
    const incomingTransfer = 125000000000000000n;

    const updatedBalance = accountBalance + incomingTransfer;

    console.log(`Account balance: ${accountBalance}n`);
    console.log(`Incoming transfer: ${incomingTransfer}n`);
    console.log(`Updated balance: ${updatedBalance}n`);
    console.log(`typeof BigInt: ${typeof updatedBalance}`);

    const quantity = 8n;
    const unitPrice = 1250n;
    const total = quantity * unitPrice;

    console.log(`8n * 1250n: ${total}n`);

    /*
     * BigInt and Number are separate numeric types. Direct arithmetic between
     * them throws a TypeError rather than silently converting one side.
     */
    try {
        console.log(accountBalance + 1);
    } catch (error) {
        console.log(
            `BigInt + Number rejected with ${error.name}: ${error.message}`
        );
    }

    /*
     * Division between BigInts truncates toward zero because the result must
     * remain an integer.
     */
    console.log(`7n / 2n: ${7n / 2n}`);

    try {
        console.log(1n / 0n);
    } catch (error) {
        console.log(
            `BigInt division by zero rejected with ${error.name}: ${error.message}`
        );
    }

    /*
     * JSON.stringify cannot serialize BigInt directly. A conversion policy is
     * required when BigInt values cross a JSON boundary.
     */
    const event = {
        sequence: 9007199254740993n,
        type: 'repository.updated'
    };

    try {
        JSON.stringify(event);
    } catch (error) {
        console.log(`JSON BigInt serialization rejected: ${error.message}`);
    }

    const serialized = JSON.stringify(event, (_, value) => {
        return typeof value === 'bigint' ? value.toString() : value;
    });

    console.log(`Explicit BigInt JSON representation: ${serialized}`);
}

/*
 * typeof is useful for broad runtime classification, but it has important
 * historical behavior such as typeof null === "object". Array.isArray and
 * Number.isInteger are more precise for specialized validation.
 */
function demonstrateTypeInspection() {
    logHeading('Runtime type inspection');

    const values = {
        string: 'branch',
        number: 123.5,
        boolean: true,
        nullValue: null,
        undefinedValue: undefined,
        symbol: Symbol('unique'),
        bigint: 12345678901234567890n
    };

    for (const [name, value] of Object.entries(values)) {
        console.log(
            `${name.padEnd(16)} typeof=${typeof value} value=${String(value)}`
        );
    }

    const arrayValue = [];
    const objectValue = {};

    console.log(`typeof []: ${typeof arrayValue}`);
    console.log(`Array.isArray([]): ${Array.isArray(arrayValue)}`);
    console.log(`typeof {}: ${typeof objectValue}`);
}

/*
 * A practical configuration validator demonstrates how different primitive
 * types need different validation rules. It deliberately rejects implicit
 * coercion because configuration boundaries should not silently reinterpret
 * user input.
 */
function validateConfiguration(configuration) {
    if (typeof configuration !== 'object' || configuration === null) {
        throw new TypeError('Configuration must be a non-null object');
    }

    if (
        typeof configuration.repository !== 'string' ||
        configuration.repository.trim() === ''
    ) {
        throw new TypeError('repository must be a non-empty string');
    }

    if (typeof configuration.enabled !== 'boolean') {
        throw new TypeError('enabled must be boolean');
    }

    if (
        typeof configuration.maxRetries !== 'number' ||
        !Number.isInteger(configuration.maxRetries) ||
        configuration.maxRetries < 0 ||
        configuration.maxRetries > 10
    ) {
        throw new RangeError(
            'maxRetries must be an integer between 0 and 10'
        );
    }

    if (
        typeof configuration.timeoutSeconds !== 'number' ||
        !Number.isFinite(configuration.timeoutSeconds) ||
        configuration.timeoutSeconds <= 0 ||
        configuration.timeoutSeconds > 300
    ) {
        throw new RangeError(
            'timeoutSeconds must be a finite number greater than 0 and at most 300'
        );
    }

    if (
        configuration.description !== null &&
        typeof configuration.description !== 'string'
    ) {
        throw new TypeError('description must be a string or null');
    }

    if (typeof configuration.auditToken !== 'symbol') {
        throw new TypeError('auditToken must be a Symbol');
    }

    if (typeof configuration.eventSequence !== 'bigint') {
        throw new TypeError('eventSequence must be a BigInt');
    }

    return Object.freeze({
        ...configuration
    });
}

function demonstrateValidation() {
    logHeading('Typed configuration validation');

    const configuration = {
        repository: 'variables-and-data-types',
        enabled: true,
        maxRetries: 3,
        timeoutSeconds: 15.5,
        description: null,
        auditToken: Symbol('audit'),
        eventSequence: 9007199254740993n
    };

    try {
        const validated = validateConfiguration(configuration);
        console.log('Configuration accepted:', validated);
    } catch (error) {
        console.error(`Configuration rejected: ${error.message}`);
    }

    const invalidConfigurations = [
        {
            ...configuration,
            enabled: 'true'
        },
        {
            ...configuration,
            maxRetries: 2.5
        },
        {
            ...configuration,
            timeoutSeconds: Infinity
        },
        {
            ...configuration,
            eventSequence: 9007199254740993
        }
    ];

    for (const invalidConfiguration of invalidConfigurations) {
        try {
            validateConfiguration(invalidConfiguration);
            throw new Error('Invalid configuration was unexpectedly accepted');
        } catch (error) {
            console.log(`Invalid configuration rejected: ${error.message}`);
        }
    }
}

/*
 * The event-driven example uses Node.js's built-in EventEmitter. It shows how
 * data types travel through an event boundary and how listeners can validate
 * the payload before acting on it.
 */
function demonstrateEventDrivenProcessing() {
    logHeading('Event-driven data processing');

    const { EventEmitter } = require('node:events');
    const eventBus = new EventEmitter();

    const processedSequences = new Set();

    eventBus.on('repository.updated', (event) => {
        if (typeof event.repository !== 'string') {
            throw new TypeError('repository must be a string');
        }

        if (typeof event.sequence !== 'bigint') {
            throw new TypeError('sequence must be BigInt');
        }

        if (typeof event.approved !== 'boolean') {
            throw new TypeError('approved must be boolean');
        }

        if (processedSequences.has(event.sequence)) {
            console.log(`Duplicate sequence ignored: ${event.sequence}n`);
            return;
        }

        processedSequences.add(event.sequence);

        console.log(
            `Processed ${event.repository} sequence=${event.sequence}n ` +
            `approved=${event.approved}`
        );
    });

    eventBus.emit('repository.updated', {
        repository: 'variables-and-data-types',
        sequence: 9007199254740993n,
        approved: true
    });

    eventBus.emit('repository.updated', {
        repository: 'variables-and-data-types',
        sequence: 9007199254740993n,
        approved: true
    });

    try {
        eventBus.emit('repository.updated', {
            repository: 'variables-and-data-types',
            sequence: 3,
            approved: true
        });
    } catch (error) {
        console.log(`Invalid event rejected: ${error.message}`);
    }
}

/*
 * A compact assertion helper makes the examples executable as self-checking
 * demonstrations rather than relying only on console output.
 */
function assert(condition, message) {
    if (!condition) {
        throw new Error(`Assertion failed: ${message}`);
    }
}

function runSelfChecks() {
    logHeading('Self checks');

    let mutable = 1;
    mutable = 2;
    assert(mutable === 2, 'let should be reassignable');

    const objectBinding = { count: 1 };
    objectBinding.count = 2;
    assert(objectBinding.count === 2, 'const should still permit object mutation');

    assert(typeof 'text' === 'string', 'string typeof');
    assert(typeof 10 === 'number', 'number typeof');
    assert(typeof true === 'boolean', 'boolean typeof');
    assert(typeof null === 'object', 'historical typeof null behavior');
    assert(typeof undefined === 'undefined', 'undefined typeof');
    assert(typeof Symbol('x') === 'symbol', 'symbol typeof');
    assert(typeof 10n === 'bigint', 'BigInt typeof');

    assert(Number.isSafeInteger(Number.MAX_SAFE_INTEGER), 'safe integer boundary');
    assert(!Number.isSafeInteger(Number.MAX_SAFE_INTEGER + 1), 'unsafe integer boundary');

    assert(Symbol('x') !== Symbol('x'), 'symbols should be unique');
    assert(Symbol.for('x') === Symbol.for('x'), 'global registry symbols should match');

    assert(10n + 20n === 30n, 'BigInt arithmetic');
    assert(7n / 2n === 3n, 'BigInt division truncation');

    const configuration = validateConfiguration({
        repository: 'self-check',
        enabled: true,
        maxRetries: 2,
        timeoutSeconds: 5,
        description: null,
        auditToken: Symbol('check'),
        eventSequence: 10000000000000000001n
    });

    assert(configuration.enabled === true, 'configuration validation');

    console.log('All self checks passed.');
}

function main() {
    console.log('JavaScript Variables and Data Types');
    console.log('Executable ECMAScript demonstration');

    demonstrateVarLetConst();
    demonstrateTemporalDeadZone();
    demonstrateStrings();
    demonstrateNumbers();
    demonstrateBooleans();
    demonstrateNullAndUndefined();
    demonstrateSymbols();
    demonstrateBigInt();
    demonstrateTypeInspection();
    demonstrateValidation();
    demonstrateEventDrivenProcessing();
    runSelfChecks();

    console.log('\nDemonstration complete.');
}

main();
