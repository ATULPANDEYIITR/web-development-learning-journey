-- Scope and Closures
-- PostgreSQL-compatible relational model for lexical-scope and closure
-- concepts represented as executable educational data.
--
-- The model treats a closure as a reusable behavior definition that retains
-- configuration from its defining lexical environment. The database cannot
-- reproduce a programming language's runtime lexical environment directly,
-- so it stores the defining scope, captured bindings, and resulting behavior
-- as relational state.

DROP SCHEMA IF EXISTS scope_closure_lab CASCADE;

CREATE SCHEMA scope_closure_lab;

SET search_path TO scope_closure_lab;

-- A scope is the environment in which a binding is visible.
CREATE TYPE scope_kind AS ENUM (
    'GLOBAL',
    'FUNCTION',
    'BLOCK',
    'LEXICAL',
    'CLOSURE'
);

CREATE TYPE binding_kind AS ENUM (
    'VARIABLE',
    'CONSTANT',
    'FUNCTION',
    'PARAMETER'
);

CREATE TYPE value_type AS ENUM (
    'TEXT',
    'INTEGER',
    'BOOLEAN',
    'DECIMAL'
);

CREATE TABLE lexical_scopes (
    scope_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    scope_name TEXT NOT NULL,
    scope_kind scope_kind NOT NULL,
    parent_scope_id BIGINT REFERENCES lexical_scopes(scope_id),
    description TEXT NOT NULL,
    UNIQUE (scope_name, parent_scope_id)
);

CREATE TABLE bindings (
    binding_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    scope_id BIGINT NOT NULL REFERENCES lexical_scopes(scope_id)
        ON DELETE CASCADE,
    binding_name TEXT NOT NULL,
    binding_kind binding_kind NOT NULL,
    value_type value_type NOT NULL,
    text_value TEXT,
    integer_value BIGINT,
    boolean_value BOOLEAN,
    decimal_value NUMERIC(18, 4),
    mutable BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (scope_id, binding_name),
    CHECK (
        (value_type = 'TEXT'
            AND text_value IS NOT NULL
            AND integer_value IS NULL
            AND boolean_value IS NULL
            AND decimal_value IS NULL)
        OR
        (value_type = 'INTEGER'
            AND text_value IS NULL
            AND integer_value IS NOT NULL
            AND boolean_value IS NULL
            AND decimal_value IS NULL)
        OR
        (value_type = 'BOOLEAN'
            AND text_value IS NULL
            AND integer_value IS NULL
            AND boolean_value IS NOT NULL
            AND decimal_value IS NULL)
        OR
        (value_type = 'DECIMAL'
            AND text_value IS NULL
            AND integer_value IS NULL
            AND boolean_value IS NULL
            AND decimal_value IS NOT NULL)
    )
);

-- A closure is tied to the lexical scope in which its function was created.
CREATE TABLE closures (
    closure_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    closure_name TEXT NOT NULL UNIQUE,
    defining_scope_id BIGINT NOT NULL REFERENCES lexical_scopes(scope_id),
    function_name TEXT NOT NULL,
    description TEXT NOT NULL
);

-- A captured binding records the environment retained by a closure.
CREATE TABLE closure_captures (
    closure_id BIGINT NOT NULL REFERENCES closures(closure_id)
        ON DELETE CASCADE,
    binding_id BIGINT NOT NULL REFERENCES bindings(binding_id),
    capture_mode TEXT NOT NULL CHECK (
        capture_mode IN ('VALUE', 'REFERENCE')
    ),
    PRIMARY KEY (closure_id, binding_id)
);

CREATE TABLE closure_invocations (
    invocation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    closure_id BIGINT NOT NULL REFERENCES closures(closure_id),
    input_value NUMERIC(18, 4),
    output_value NUMERIC(18, 4),
    invoked_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN NOT NULL,
    error_message TEXT
);

-- Global scope is the root lexical environment.
INSERT INTO lexical_scopes (
    scope_name,
    scope_kind,
    parent_scope_id,
    description
)
VALUES (
    'module',
    'GLOBAL',
    NULL,
    'Root environment containing application-level bindings'
);

-- Function scope is nested under the global environment.
INSERT INTO lexical_scopes (
    scope_name,
    scope_kind,
    parent_scope_id,
    description
)
SELECT
    'make_multiplier',
    'FUNCTION',
    scope_id,
    'Function environment containing the multiplier factor'
FROM lexical_scopes
WHERE scope_name = 'module';

-- Block scope is represented explicitly even though Python does not create
-- an ordinary block scope for if/for statements. This lets the relational
-- model contrast language-specific scope rules.
INSERT INTO lexical_scopes (
    scope_name,
    scope_kind,
    parent_scope_id,
    description
)
SELECT
    'validation_block',
    'BLOCK',
    scope_id,
    'Nested lexical region used to represent block-scoped bindings'
FROM lexical_scopes
WHERE scope_name = 'make_multiplier';

INSERT INTO lexical_scopes (
    scope_name,
    scope_kind,
    parent_scope_id,
    description
)
SELECT
    'multiplier_closure_environment',
    'CLOSURE',
    scope_id,
    'Environment retained by the returned multiplier function'
FROM lexical_scopes
WHERE scope_name = 'make_multiplier';

INSERT INTO bindings (
    scope_id,
    binding_name,
    binding_kind,
    value_type,
    text_value,
    mutable
)
SELECT
    scope_id,
    'APPLICATION_NAME',
    'CONSTANT',
    'TEXT',
    'Scope Closure Laboratory',
    FALSE
FROM lexical_scopes
WHERE scope_name = 'module';

INSERT INTO bindings (
    scope_id,
    binding_name,
    binding_kind,
    value_type,
    integer_value,
    mutable
)
SELECT
    scope_id,
    'factor',
    'PARAMETER',
    'INTEGER',
    10,
    FALSE
FROM lexical_scopes
WHERE scope_name = 'make_multiplier';

INSERT INTO bindings (
    scope_id,
    binding_name,
    binding_kind,
    value_type,
    integer_value,
    mutable
)
SELECT
    scope_id,
    'temporary_limit',
    'VARIABLE',
    'INTEGER',
    100,
    TRUE
FROM lexical_scopes
WHERE scope_name = 'validation_block';

INSERT INTO closures (
    closure_name,
    defining_scope_id,
    function_name,
    description
)
SELECT
    'multiply_by_ten',
    scope_id,
    'multiply',
    'Multiplies an input using the retained factor binding'
FROM lexical_scopes
WHERE scope_name = 'multiplier_closure_environment';

INSERT INTO closure_captures (
    closure_id,
    binding_id,
    capture_mode
)
SELECT
    c.closure_id,
    b.binding_id,
    'VALUE'
FROM closures c
JOIN bindings b
    ON b.binding_name = 'factor'
JOIN lexical_scopes s
    ON s.scope_id = b.scope_id
WHERE c.closure_name = 'multiply_by_ten'
  AND s.scope_name = 'make_multiplier';

-- A function demonstrates closure behavior by retaining a captured value.
CREATE OR REPLACE FUNCTION invoke_multiplier(
    p_closure_name TEXT,
    p_input NUMERIC
)
RETURNS NUMERIC
LANGUAGE plpgsql
AS $$
DECLARE
    captured_factor NUMERIC;
    result NUMERIC;
    selected_closure_id BIGINT;
BEGIN
    SELECT c.closure_id
    INTO selected_closure_id
    FROM closures c
    WHERE c.closure_name = p_closure_name;

    IF selected_closure_id IS NULL THEN
        RAISE EXCEPTION 'Unknown closure: %', p_closure_name;
    END IF;

    SELECT b.integer_value
    INTO captured_factor
    FROM closure_captures cc
    JOIN bindings b
        ON b.binding_id = cc.binding_id
    WHERE cc.closure_id = selected_closure_id
      AND b.binding_name = 'factor';

    IF captured_factor IS NULL THEN
        RAISE EXCEPTION 'Closure % has no integer factor',
            p_closure_name;
    END IF;

    result := captured_factor * p_input;

    INSERT INTO closure_invocations (
        closure_id,
        input_value,
        output_value,
        success
    )
    VALUES (
        selected_closure_id,
        p_input,
        result,
        TRUE
    );

    RETURN result;
EXCEPTION
    WHEN OTHERS THEN
        IF selected_closure_id IS NOT NULL THEN
            INSERT INTO closure_invocations (
                closure_id,
                input_value,
                success,
                error_message
            )
            VALUES (
                selected_closure_id,
                p_input,
                FALSE,
                SQLERRM
            );
        END IF;

        RAISE;
END;
$$;

-- Successful closure invocation.
SELECT invoke_multiplier('multiply_by_ten', 7) AS closure_result;

-- Scope hierarchy exposes lexical nesting.
SELECT
    child.scope_name AS child_scope,
    child.scope_kind AS child_kind,
    parent.scope_name AS parent_scope,
    parent.scope_kind AS parent_kind
FROM lexical_scopes child
LEFT JOIN lexical_scopes parent
    ON parent.scope_id = child.parent_scope_id
ORDER BY child.scope_id;

-- Bindings demonstrate that the same name can exist in different scopes
-- without representing the same binding.
SELECT
    s.scope_name,
    s.scope_kind,
    b.binding_name,
    b.binding_kind,
    b.value_type,
    b.mutable
FROM bindings b
JOIN lexical_scopes s
    ON s.scope_id = b.scope_id
ORDER BY s.scope_id, b.binding_name;

-- Closure captures show which lexical binding survives the function return.
SELECT
    c.closure_name,
    c.function_name,
    s.scope_name AS defining_scope,
    b.binding_name AS captured_binding,
    cc.capture_mode
FROM closures c
JOIN lexical_scopes s
    ON s.scope_id = c.defining_scope_id
JOIN closure_captures cc
    ON cc.closure_id = c.closure_id
JOIN bindings b
    ON b.binding_id = cc.binding_id;

-- Invocation history demonstrates state associated with closure execution.
SELECT
    c.closure_name,
    ci.input_value,
    ci.output_value,
    ci.success,
    ci.invoked_at
FROM closure_invocations ci
JOIN closures c
    ON c.closure_id = ci.closure_id
ORDER BY ci.invoked_at;

-- The index supports lookup of bindings by lexical scope and name.
CREATE INDEX idx_bindings_scope_name
    ON bindings(scope_id, binding_name);

CREATE INDEX idx_closure_invocations_closure_time
    ON closure_invocations(closure_id, invoked_at DESC);

-- A view exposes the effective captured environment without exposing
-- unrelated bindings from other scopes.
CREATE VIEW closure_environment AS
SELECT
    c.closure_name,
    c.function_name,
    b.binding_name,
    b.value_type,
    b.text_value,
    b.integer_value,
    b.boolean_value,
    b.decimal_value,
    cc.capture_mode
FROM closures c
JOIN closure_captures cc
    ON cc.closure_id = c.closure_id
JOIN bindings b
    ON b.binding_id = cc.binding_id;

SELECT *
FROM closure_environment
ORDER BY closure_name, binding_name;

-- Transactional demonstration:
-- an attempted invalid capture is rolled back rather than leaving a partial
-- closure environment.
BEGIN;

INSERT INTO closures (
    closure_name,
    defining_scope_id,
    function_name,
    description
)
SELECT
    'invalid_demo_closure',
    scope_id,
    'invalid_function',
    'Temporary transaction test'
FROM lexical_scopes
WHERE scope_name = 'module';

SAVEPOINT invalid_capture;

-- This intentionally references a nonexistent binding and therefore fails.
-- The savepoint allows the transaction to continue for demonstration.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM bindings
        WHERE binding_name = 'nonexistent_binding'
    ) THEN
        RAISE EXCEPTION 'Cannot capture nonexistent lexical binding';
    END IF;
END;
$$;

ROLLBACK TO SAVEPOINT invalid_capture;

-- The invalid closure row can be removed before committing the valid state.
DELETE FROM closures
WHERE closure_name = 'invalid_demo_closure';

COMMIT;

-- Final integrity view.
SELECT
    c.closure_name,
    COUNT(cc.binding_id) AS captured_binding_count
FROM closures c
LEFT JOIN closure_captures cc
    ON cc.closure_id = c.closure_id
GROUP BY c.closure_id, c.closure_name
ORDER BY c.closure_name;
