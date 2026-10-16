-- PostgreSQL 15+
-- JavaScript execution semantics laboratory.
--
-- The schema records simulated execution contexts, lexical environments,
-- identifier bindings, and call-stack frames. It distinguishes declaration
-- creation from initialization and stores lexical parent relationships.
-- It is a data model for analysis, not a JavaScript runtime.

BEGIN;

DROP SCHEMA IF EXISTS execution_lab CASCADE;
CREATE SCHEMA execution_lab;
SET search_path TO execution_lab, public;

CREATE TYPE environment_kind AS ENUM (
    'GLOBAL',
    'MODULE',
    'FUNCTION',
    'BLOCK',
    'CATCH'
);

CREATE TYPE binding_kind AS ENUM (
    'VAR',
    'LET',
    'CONST',
    'FUNCTION',
    'PARAMETER'
);

CREATE TYPE execution_status AS ENUM (
    'ACTIVE',
    'RETURNED',
    'THREW',
    'SUSPENDED'
);

CREATE TYPE event_kind AS ENUM (
    'DECLARE',
    'INITIALIZE',
    'READ',
    'ASSIGN',
    'CALL',
    'RETURN',
    'THROW',
    'SUSPEND',
    'RESUME'
);

CREATE TABLE runtime_sessions (
    session_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    program_name TEXT NOT NULL,
    runtime_version TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    maximum_stack_depth INTEGER NOT NULL DEFAULT 100,
    CHECK (length(trim(program_name)) > 0),
    CHECK (length(trim(runtime_version)) > 0),
    CHECK (maximum_stack_depth > 0)
);

CREATE TABLE lexical_environments (
    environment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    session_id BIGINT NOT NULL
        REFERENCES runtime_sessions(session_id) ON DELETE CASCADE,
    environment_name TEXT NOT NULL,
    environment_type environment_kind NOT NULL,
    outer_environment_id BIGINT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (session_id, environment_id),
    FOREIGN KEY (session_id, outer_environment_id)
        REFERENCES lexical_environments(session_id, environment_id)
        DEFERRABLE INITIALLY DEFERRED,
    CHECK (outer_environment_id IS NULL
           OR outer_environment_id <> environment_id),
    CHECK (length(trim(environment_name)) > 0)
);

CREATE INDEX lexical_environment_outer_idx
    ON lexical_environments(session_id, outer_environment_id);

CREATE TABLE execution_contexts (
    context_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    session_id BIGINT NOT NULL
        REFERENCES runtime_sessions(session_id) ON DELETE CASCADE,
    function_name TEXT NOT NULL,
    lexical_environment_id BIGINT NOT NULL,
    variable_environment_id BIGINT NOT NULL,
    this_description TEXT NOT NULL DEFAULT 'undefined',
    status execution_status NOT NULL DEFAULT 'ACTIVE',
    entered_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    exited_at TIMESTAMPTZ,
    FOREIGN KEY (session_id, lexical_environment_id)
        REFERENCES lexical_environments(session_id, environment_id),
    FOREIGN KEY (session_id, variable_environment_id)
        REFERENCES lexical_environments(session_id, environment_id),
    CHECK (length(trim(function_name)) > 0),
    CHECK (exited_at IS NULL OR exited_at >= entered_at),
    CHECK (
        (status = 'ACTIVE' AND exited_at IS NULL)
        OR
        (status <> 'ACTIVE' AND exited_at IS NOT NULL)
    )
);

CREATE INDEX execution_context_active_idx
    ON execution_contexts(session_id, entered_at)
    WHERE status = 'ACTIVE';

CREATE TABLE identifier_bindings (
    binding_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    environment_id BIGINT NOT NULL
        REFERENCES lexical_environments(environment_id) ON DELETE CASCADE,
    identifier_name TEXT NOT NULL,
    declaration_kind binding_kind NOT NULL,
    value_text TEXT,
    is_initialized BOOLEAN NOT NULL DEFAULT FALSE,
    declared_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    initialized_at TIMESTAMPTZ,
    UNIQUE (environment_id, identifier_name),
    CHECK (length(trim(identifier_name)) > 0),
    CHECK (
        (is_initialized AND initialized_at IS NOT NULL)
        OR
        (NOT is_initialized AND initialized_at IS NULL)
    ),
    CHECK (
        declaration_kind NOT IN ('VAR', 'FUNCTION')
        OR is_initialized
    )
);

CREATE INDEX identifier_bindings_name_idx
    ON identifier_bindings(identifier_name);

CREATE TABLE runtime_events (
    event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    session_id BIGINT NOT NULL
        REFERENCES runtime_sessions(session_id) ON DELETE CASCADE,
    context_id BIGINT
        REFERENCES execution_contexts(context_id) ON DELETE SET NULL,
    environment_id BIGINT
        REFERENCES lexical_environments(environment_id) ON DELETE SET NULL,
    binding_id BIGINT
        REFERENCES identifier_bindings(binding_id) ON DELETE SET NULL,
    event_type event_kind NOT NULL,
    identifier_name TEXT,
    event_detail TEXT NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX runtime_events_timeline_idx
    ON runtime_events(session_id, occurred_at, event_id);

CREATE INDEX runtime_events_identifier_idx
    ON runtime_events(session_id, identifier_name, event_type);

CREATE TABLE call_stack_frames (
    session_id BIGINT NOT NULL
        REFERENCES runtime_sessions(session_id) ON DELETE CASCADE,
    stack_depth INTEGER NOT NULL,
    context_id BIGINT NOT NULL
        REFERENCES execution_contexts(context_id) ON DELETE CASCADE,
    pushed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    popped_at TIMESTAMPTZ,
    PRIMARY KEY (session_id, stack_depth),
    UNIQUE (context_id),
    CHECK (stack_depth >= 0),
    CHECK (popped_at IS NULL OR popped_at >= pushed_at)
);

CREATE INDEX active_stack_frames_idx
    ON call_stack_frames(session_id, stack_depth DESC)
    WHERE popped_at IS NULL;

-- This trigger prevents a lexical declaration from being silently
-- reinitialized. It does not implement all ECMAScript declaration rules.
CREATE FUNCTION enforce_binding_initialization()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'UPDATE' THEN
        IF OLD.is_initialized AND NOT NEW.is_initialized THEN
            RAISE EXCEPTION
                'Initialized binding % cannot return to TDZ state',
                OLD.identifier_name;
        END IF;

        IF OLD.declaration_kind = 'CONST'
           AND OLD.is_initialized
           AND NEW.value_text IS DISTINCT FROM OLD.value_text THEN
            RAISE EXCEPTION
                'Cannot reassign initialized const binding %',
                OLD.identifier_name;
        END IF;

        IF NOT OLD.is_initialized AND NEW.is_initialized THEN
            NEW.initialized_at := CURRENT_TIMESTAMP;
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER binding_initialization_guard
BEFORE UPDATE ON identifier_bindings
FOR EACH ROW
EXECUTE FUNCTION enforce_binding_initialization();

-- Declaration setup models the important initialization distinction:
-- var and function bindings are available before assignment, while let and
-- const bindings remain inaccessible until initialized.
CREATE FUNCTION declare_binding(
    p_environment_id BIGINT,
    p_identifier TEXT,
    p_kind binding_kind,
    p_initial_value TEXT DEFAULT NULL,
    p_initialize_now BOOLEAN DEFAULT FALSE
)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    v_binding_id BIGINT;
    v_initialized BOOLEAN;
BEGIN
    IF p_identifier IS NULL OR length(trim(p_identifier)) = 0 THEN
        RAISE EXCEPTION 'Identifier must not be empty';
    END IF;

    v_initialized :=
        p_kind IN ('VAR', 'FUNCTION')
        OR p_initialize_now;

    INSERT INTO identifier_bindings (
        environment_id,
        identifier_name,
        declaration_kind,
        value_text,
        is_initialized,
        initialized_at
    )
    VALUES (
        p_environment_id,
        p_identifier,
        p_kind,
        CASE
            WHEN p_kind = 'VAR' AND NOT p_initialize_now THEN 'undefined'
            WHEN p_kind = 'FUNCTION' THEN COALESCE(p_initial_value, '[function]')
            WHEN v_initialized THEN p_initial_value
            ELSE NULL
        END,
        v_initialized,
        CASE WHEN v_initialized THEN CURRENT_TIMESTAMP ELSE NULL END
    )
    RETURNING binding_id INTO v_binding_id;

    RETURN v_binding_id;
END;
$$;

CREATE FUNCTION initialize_binding(
    p_binding_id BIGINT,
    p_value TEXT
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    v_initialized BOOLEAN;
BEGIN
    SELECT is_initialized
    INTO v_initialized
    FROM identifier_bindings
    WHERE binding_id = p_binding_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Binding % does not exist', p_binding_id;
    END IF;

    IF v_initialized THEN
        RAISE EXCEPTION 'Binding % is already initialized', p_binding_id;
    END IF;

    UPDATE identifier_bindings
    SET value_text = p_value,
        is_initialized = TRUE,
        initialized_at = CURRENT_TIMESTAMP
    WHERE binding_id = p_binding_id;
END;
$$;

CREATE FUNCTION read_binding(
    p_environment_id BIGINT,
    p_identifier TEXT
)
RETURNS TEXT
LANGUAGE plpgsql
AS $$
DECLARE
    v_environment_id BIGINT := p_environment_id;
    v_binding identifier_bindings%ROWTYPE;
    v_outer_environment_id BIGINT;
BEGIN
    -- Identifier lookup follows lexical parent links. It does not search
    -- for a same-named binding merely because its function is on the stack.
    LOOP
        SELECT *
        INTO v_binding
        FROM identifier_bindings
        WHERE environment_id = v_environment_id
          AND identifier_name = p_identifier;

        IF FOUND THEN
            IF NOT v_binding.is_initialized THEN
                RAISE EXCEPTION
                    'Cannot access % before initialization',
                    p_identifier
                    USING ERRCODE = '55000';
            END IF;

            RETURN v_binding.value_text;
        END IF;

        SELECT outer_environment_id
        INTO v_outer_environment_id
        FROM lexical_environments
        WHERE environment_id = v_environment_id;

        IF NOT FOUND THEN
            RAISE EXCEPTION
                'Environment % does not exist',
                v_environment_id;
        END IF;

        IF v_outer_environment_id IS NULL THEN
            RAISE EXCEPTION
                'Identifier % is not defined',
                p_identifier
                USING ERRCODE = '42703';
        END IF;

        v_environment_id := v_outer_environment_id;
    END LOOP;
END;
$$;

CREATE FUNCTION push_context(
    p_session_id BIGINT,
    p_function_name TEXT,
    p_lexical_environment_id BIGINT,
    p_variable_environment_id BIGINT,
    p_this_description TEXT DEFAULT 'undefined'
)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    v_context_id BIGINT;
    v_depth INTEGER;
    v_maximum_depth INTEGER;
BEGIN
    SELECT maximum_stack_depth
    INTO v_maximum_depth
    FROM runtime_sessions
    WHERE session_id = p_session_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Session % does not exist', p_session_id;
    END IF;

    SELECT COALESCE(MAX(stack_depth), -1) + 1
    INTO v_depth
    FROM call_stack_frames
    WHERE session_id = p_session_id
      AND popped_at IS NULL;

    IF v_depth >= v_maximum_depth THEN
        RAISE EXCEPTION 'Maximum simulated call stack size exceeded';
    END IF;

    INSERT INTO execution_contexts (
        session_id,
        function_name,
        lexical_environment_id,
        variable_environment_id,
        this_description
    )
    VALUES (
        p_session_id,
        p_function_name,
        p_lexical_environment_id,
        p_variable_environment_id,
        p_this_description
    )
    RETURNING context_id INTO v_context_id;

    INSERT INTO call_stack_frames (
        session_id,
        stack_depth,
        context_id
    )
    VALUES (
        p_session_id,
        v_depth,
        v_context_id
    );

    RETURN v_context_id;
END;
$$;

CREATE FUNCTION pop_context(
    p_session_id BIGINT,
    p_context_id BIGINT,
    p_final_status execution_status DEFAULT 'RETURNED'
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    v_top_context_id BIGINT;
BEGIN
    IF p_final_status = 'ACTIVE' THEN
        RAISE EXCEPTION 'Final status cannot be ACTIVE';
    END IF;

    SELECT context_id
    INTO v_top_context_id
    FROM call_stack_frames
    WHERE session_id = p_session_id
      AND popped_at IS NULL
    ORDER BY stack_depth DESC
    LIMIT 1
    FOR UPDATE;

    IF v_top_context_id IS NULL THEN
        RAISE EXCEPTION 'Call stack is empty';
    END IF;

    IF v_top_context_id <> p_context_id THEN
        RAISE EXCEPTION
            'LIFO violation: context % is not the active top frame',
            p_context_id;
    END IF;

    UPDATE call_stack_frames
    SET popped_at = CURRENT_TIMESTAMP
    WHERE session_id = p_session_id
      AND context_id = p_context_id
      AND popped_at IS NULL;

    UPDATE execution_contexts
    SET status = p_final_status,
        exited_at = CURRENT_TIMESTAMP
    WHERE context_id = p_context_id
      AND session_id = p_session_id
      AND status = 'ACTIVE';

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Context % is not active in session %',
            p_context_id,
            p_session_id;
    END IF;
END;
$$;

-- Example runtime: deployment configuration inspection.
INSERT INTO runtime_sessions (
    program_name,
    runtime_version,
    maximum_stack_depth
)
VALUES ('deployment-policy-inspector', 'ECMAScript-style model', 8);

INSERT INTO lexical_environments (
    session_id,
    environment_name,
    environment_type,
    outer_environment_id
)
VALUES (
    1,
    'global',
    'GLOBAL',
    NULL
);

INSERT INTO lexical_environments (
    session_id,
    environment_name,
    environment_type,
    outer_environment_id
)
VALUES (
    1,
    'deploymentModule',
    'MODULE',
    1
);

INSERT INTO lexical_environments (
    session_id,
    environment_name,
    environment_type,
    outer_environment_id
)
VALUES (
    1,
    'evaluateDeployment',
    'FUNCTION',
    2
);

SELECT declare_binding(1, 'serviceName', 'CONST', 'artifact-registry', TRUE);
SELECT declare_binding(1, 'defaultRegion', 'LET', 'ap-south-1', TRUE);
SELECT declare_binding(2, 'retryCount', 'VAR', NULL, FALSE);
SELECT declare_binding(2, 'verifySignature', 'FUNCTION', '[function]', TRUE);
SELECT declare_binding(3, 'deploymentRegion', 'LET', NULL, FALSE);
SELECT declare_binding(3, 'releaseVersion', 'CONST', NULL, FALSE);

INSERT INTO runtime_events (
    session_id,
    environment_id,
    binding_id,
    event_type,
    identifier_name,
    event_detail
)
SELECT
    1,
    environment_id,
    binding_id,
    'DECLARE',
    identifier_name,
    'Binding created during declaration setup'
FROM identifier_bindings
JOIN lexical_environments USING (environment_id);

-- Read initialized declarations through the lexical chain.
SELECT
    'serviceName' AS identifier,
    read_binding(3, 'serviceName') AS resolved_value
UNION ALL
SELECT
    'defaultRegion',
    read_binding(3, 'defaultRegion')
UNION ALL
SELECT
    'retryCount',
    read_binding(3, 'retryCount');

-- Initialize lexical bindings at their simulated declaration points.
SELECT initialize_binding(
    binding_id,
    'ap-south-1'
)
FROM identifier_bindings
WHERE identifier_name = 'deploymentRegion';

SELECT initialize_binding(
    binding_id,
    '2026.10'
)
FROM identifier_bindings
WHERE identifier_name = 'releaseVersion';

SELECT
    identifier_name,
    declaration_kind,
    is_initialized,
    value_text,
    declared_at,
    initialized_at
FROM identifier_bindings
ORDER BY environment_id, binding_id;

-- Demonstrate nested call frames in a transaction.
BEGIN;

SELECT push_context(1, 'handleDeployment', 3, 3, 'undefined')
    AS parent_context_id;

-- The parent is context 1 in this clean demonstration.
SELECT push_context(1, 'verifySignature', 3, 3, 'undefined')
    AS child_context_id;

SELECT
    stack_depth,
    context_id,
    pushed_at,
    popped_at
FROM call_stack_frames
WHERE session_id = 1
ORDER BY stack_depth;

SELECT pop_context(1, 2, 'RETURNED');
SELECT pop_context(1, 1, 'RETURNED');

COMMIT;

-- Useful execution-trace queries.
SELECT
    c.function_name,
    c.status,
    c.entered_at,
    c.exited_at,
    e.environment_name AS lexical_environment,
    v.environment_name AS variable_environment
FROM execution_contexts AS c
JOIN lexical_environments AS e
  ON e.environment_id = c.lexical_environment_id
JOIN lexical_environments AS v
  ON v.environment_id = c.variable_environment_id
ORDER BY c.context_id;

SELECT
    session_id,
    event_type,
    identifier_name,
    event_detail,
    occurred_at
FROM runtime_events
ORDER BY occurred_at, event_id;

-- Inspect uninitialized lexical bindings. Such bindings exist but cannot
-- be read before initialization.
SELECT
    identifier_name,
    declaration_kind,
    environment_id,
    declared_at
FROM identifier_bindings
WHERE NOT is_initialized
ORDER BY environment_id, identifier_name;

-- The schema enforces one binding per identifier per environment and
-- prevents const reassignment through its trigger. It does not fully enforce
-- JavaScript grammar, cyclic-scope prevention, or every ECMAScript rule.

COMMIT;
