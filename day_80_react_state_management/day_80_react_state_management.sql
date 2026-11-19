-- ============================================================
-- REACT STATE MANAGEMENT
-- Redux Concepts, Reducers, Actions, Middleware and RTK Model
--
-- PostgreSQL 14+
--
-- Models:
-- 1. Application instances
-- 2. Normalized application state
-- 3. Actions and action history
-- 4. Reducer executions
-- 5. Middleware execution
-- 6. Asynchronous request lifecycle
-- 7. State subscriptions
-- 8. State revisions and optimistic concurrency
-- 9. Selectors and derived state
-- 10. Transactional state updates
--
-- Execute as a database owner or a role permitted to create schemas.
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS redux_demo;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

SET search_path TO redux_demo, public;

-- ============================================================
-- 1. ENUMERATIONS
-- ============================================================

CREATE TYPE action_status AS ENUM (
    'received',
    'processing',
    'succeeded',
    'failed',
    'rejected'
);

CREATE TYPE request_status AS ENUM (
    'idle',
    'loading',
    'succeeded',
    'failed'
);

CREATE TYPE task_filter AS ENUM (
    'all',
    'active',
    'completed'
);

CREATE TYPE middleware_status AS ENUM (
    'executed',
    'skipped',
    'failed'
);

-- ============================================================
-- 2. APPLICATION INSTANCES
-- ============================================================

CREATE TABLE applications (
    application_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    application_name VARCHAR(150) NOT NULL UNIQUE,

    environment VARCHAR(20) NOT NULL
        CHECK (
            environment IN (
                'development',
                'testing',
                'staging',
                'production'
            )
        ),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- 3. ACTION TYPE REGISTRY
-- ============================================================

CREATE TABLE action_types (
    action_type_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    action_name VARCHAR(120) NOT NULL UNIQUE,

    description TEXT NOT NULL,

    is_async BOOLEAN NOT NULL DEFAULT FALSE,

    is_enabled BOOLEAN NOT NULL DEFAULT TRUE
);

INSERT INTO action_types (
    action_name,
    description,
    is_async
)
VALUES
    ('tasks/added', 'Adds a task to application state', FALSE),
    ('tasks/toggled', 'Changes task completion status', FALSE),
    ('tasks/deleted', 'Deletes an existing task', FALSE),
    ('tasks/filterChanged', 'Changes the task selector filter', FALSE),
    ('counter/incremented', 'Increments application counter', FALSE),
    ('tasks/requested', 'Starts an asynchronous request', TRUE),
    ('tasks/succeeded', 'Completes an asynchronous request', TRUE),
    ('tasks/failed', 'Records an asynchronous request failure', TRUE),
    ('app/reset', 'Resets application state', FALSE);

-- ============================================================
-- 4. APPLICATION STATE
-- ============================================================

CREATE TABLE application_state (
    application_id UUID PRIMARY KEY
        REFERENCES applications(application_id)
        ON DELETE CASCADE,

    counter_value BIGINT NOT NULL DEFAULT 0
        CHECK (counter_value >= 0),

    selected_filter task_filter NOT NULL DEFAULT 'all',

    revision BIGINT NOT NULL DEFAULT 0
        CHECK (revision >= 0),

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- 5. NORMALIZED TASK STATE
-- ============================================================

CREATE TABLE tasks (
    task_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    application_id UUID NOT NULL
        REFERENCES applications(application_id)
        ON DELETE CASCADE,

    title VARCHAR(200) NOT NULL
        CHECK (LENGTH(TRIM(title)) > 0),

    is_completed BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (application_id, task_id)
);

CREATE INDEX idx_tasks_application_status
ON tasks(application_id, is_completed);

CREATE INDEX idx_tasks_created
ON tasks(application_id, created_at DESC);

-- ============================================================
-- 6. ACTION LOG
-- ============================================================

CREATE TABLE action_log (
    action_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    application_id UUID NOT NULL
        REFERENCES applications(application_id)
        ON DELETE CASCADE,

    action_type_id BIGINT NOT NULL
        REFERENCES action_types(action_type_id),

    payload JSONB NOT NULL DEFAULT '{}'::JSONB,

    status action_status NOT NULL DEFAULT 'received',

    correlation_id UUID NOT NULL DEFAULT gen_random_uuid(),

    error_message TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    completed_at TIMESTAMPTZ,

    UNIQUE (application_id, correlation_id)
);

CREATE INDEX idx_action_application_time
ON action_log(application_id, created_at DESC);

CREATE INDEX idx_action_status
ON action_log(status, created_at);

CREATE INDEX idx_action_payload
ON action_log USING GIN(payload);

-- ============================================================
-- 7. REDUCER EXECUTION HISTORY
-- ============================================================

CREATE TABLE reducer_executions (
    execution_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    action_id UUID NOT NULL UNIQUE
        REFERENCES action_log(action_id)
        ON DELETE CASCADE,

    application_id UUID NOT NULL
        REFERENCES applications(application_id),

    previous_revision BIGINT NOT NULL,

    resulting_revision BIGINT,

    previous_counter BIGINT NOT NULL,

    resulting_counter BIGINT,

    execution_succeeded BOOLEAN NOT NULL,

    error_message TEXT,

    executed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_reducer_application_revision
ON reducer_executions(application_id, resulting_revision);

-- ============================================================
-- 8. MIDDLEWARE REGISTRY
-- ============================================================

CREATE TABLE middleware_registry (
    middleware_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    application_id UUID NOT NULL
        REFERENCES applications(application_id)
        ON DELETE CASCADE,

    middleware_name VARCHAR(120) NOT NULL,

    execution_order INTEGER NOT NULL
        CHECK (execution_order >= 0),

    is_enabled BOOLEAN NOT NULL DEFAULT TRUE,

    UNIQUE (application_id, middleware_name),

    UNIQUE (application_id, execution_order)
);

INSERT INTO middleware_registry (
    application_id,
    middleware_name,
    execution_order
)
SELECT
    application_id,
    middleware_name,
    execution_order
FROM (
    SELECT
        application_id,
        'validation'::VARCHAR AS middleware_name,
        1 AS execution_order
    FROM applications

    UNION ALL

    SELECT
        application_id,
        'logging'::VARCHAR,
        2
    FROM applications

    UNION ALL

    SELECT
        application_id,
        'analytics'::VARCHAR,
        3
    FROM applications
) AS configured;

CREATE TABLE middleware_executions (
    middleware_execution_id BIGINT
        GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    action_id UUID NOT NULL
        REFERENCES action_log(action_id)
        ON DELETE CASCADE,

    middleware_id BIGINT NOT NULL
        REFERENCES middleware_registry(middleware_id),

    execution_status middleware_status NOT NULL,

    execution_message TEXT,

    executed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_middleware_action
ON middleware_executions(action_id);

-- ============================================================
-- 9. ASYNCHRONOUS REQUEST STATE
-- ============================================================

CREATE TABLE async_requests (
    request_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    application_id UUID NOT NULL
        REFERENCES applications(application_id)
        ON DELETE CASCADE,

    initiating_action_id UUID NOT NULL
        REFERENCES action_log(action_id),

    request_status request_status NOT NULL DEFAULT 'idle',

    response_payload JSONB,

    error_message TEXT,

    started_at TIMESTAMPTZ,

    completed_at TIMESTAMPTZ
);

CREATE INDEX idx_async_request_status
ON async_requests(application_id, request_status);

-- ============================================================
-- 10. STATE SNAPSHOTS
-- ============================================================

CREATE TABLE state_snapshots (
    snapshot_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    application_id UUID NOT NULL
        REFERENCES applications(application_id)
        ON DELETE CASCADE,

    revision BIGINT NOT NULL,

    state_payload JSONB NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (application_id, revision)
);

CREATE INDEX idx_snapshots_application
ON state_snapshots(application_id, revision DESC);

-- ============================================================
-- 11. STATE SUBSCRIPTIONS
-- ============================================================

CREATE TABLE state_subscriptions (
    subscription_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    application_id UUID NOT NULL
        REFERENCES applications(application_id)
        ON DELETE CASCADE,

    subscriber_name VARCHAR(120) NOT NULL,

    subscribed_to VARCHAR(120) NOT NULL,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (
        application_id,
        subscriber_name,
        subscribed_to
    )
);

-- ============================================================
-- 12. APPLICATION INITIALIZATION
-- ============================================================

CREATE OR REPLACE FUNCTION initialize_application_state()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO application_state (
        application_id,
        counter_value,
        selected_filter,
        revision
    )
    VALUES (
        NEW.application_id,
        0,
        'all',
        0
    );

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_initialize_application_state
AFTER INSERT ON applications
FOR EACH ROW
EXECUTE FUNCTION initialize_application_state();

-- ============================================================
-- 13. TASK UPDATE TIMESTAMP
-- ============================================================

CREATE OR REPLACE FUNCTION update_task_timestamp()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_task_timestamp
BEFORE UPDATE ON tasks
FOR EACH ROW
EXECUTE FUNCTION update_task_timestamp();

-- ============================================================
-- 14. APPLICATION STATE TIMESTAMP
-- ============================================================

CREATE OR REPLACE FUNCTION update_state_timestamp()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_state_timestamp
BEFORE UPDATE ON application_state
FOR EACH ROW
EXECUTE FUNCTION update_state_timestamp();

-- ============================================================
-- 15. ACTION DISPATCH FUNCTION
--
-- Uses row locking and a transaction.
-- A failed action does not leave partially committed state.
-- ============================================================

CREATE OR REPLACE FUNCTION dispatch_action(
    p_application_id UUID,
    p_action_name VARCHAR,
    p_payload JSONB DEFAULT '{}'::JSONB,
    p_expected_revision BIGINT DEFAULT NULL
)
RETURNS TABLE (
    dispatched_action_id UUID,
    resulting_revision BIGINT,
    result_status action_status
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_action_id UUID;
    v_action_type_id BIGINT;
    v_current_revision BIGINT;
    v_previous_counter BIGINT;
    v_resulting_counter BIGINT;
    v_task_id UUID;
    v_title TEXT;
    v_task_exists BOOLEAN;
    v_status action_status := 'processing';
BEGIN
    -- Confirm that the action is registered and enabled.
    SELECT action_type_id
    INTO v_action_type_id
    FROM action_types
    WHERE action_name = p_action_name
      AND is_enabled = TRUE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Unknown or disabled action: %',
            p_action_name;
    END IF;

    -- Lock the state row to serialize updates.
    SELECT revision, counter_value
    INTO v_current_revision, v_previous_counter
    FROM application_state
    WHERE application_id = p_application_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Application state does not exist';
    END IF;

    -- Optimistic concurrency control.
    IF p_expected_revision IS NOT NULL
       AND p_expected_revision <> v_current_revision THEN

        RAISE EXCEPTION
            'Revision conflict. Expected %, actual %',
            p_expected_revision,
            v_current_revision;
    END IF;

    v_action_id := gen_random_uuid();

    INSERT INTO action_log (
        action_id,
        application_id,
        action_type_id,
        payload,
        status
    )
    VALUES (
        v_action_id,
        p_application_id,
        v_action_type_id,
        COALESCE(p_payload, '{}'::JSONB),
        'processing'
    );

    v_resulting_counter := v_previous_counter;

    CASE p_action_name

        WHEN 'tasks/added' THEN

            v_title := p_payload ->> 'title';

            IF v_title IS NULL
               OR LENGTH(TRIM(v_title)) = 0
               OR LENGTH(v_title) > 200 THEN

                RAISE EXCEPTION 'Invalid task title';
            END IF;

            v_task_id := COALESCE(
                (p_payload ->> 'id')::UUID,
                gen_random_uuid()
            );

            INSERT INTO tasks (
                task_id,
                application_id,
                title
            )
            VALUES (
                v_task_id,
                p_application_id,
                TRIM(v_title)
            );

        WHEN 'tasks/toggled' THEN

            v_task_id := (p_payload ->> 'id')::UUID;

            UPDATE tasks
            SET is_completed = NOT is_completed
            WHERE task_id = v_task_id
              AND application_id = p_application_id;

            IF NOT FOUND THEN
                RAISE EXCEPTION 'Task not found';
            END IF;

        WHEN 'tasks/deleted' THEN

            v_task_id := (p_payload ->> 'id')::UUID;

            DELETE FROM tasks
            WHERE task_id = v_task_id
              AND application_id = p_application_id;

            IF NOT FOUND THEN
                RAISE EXCEPTION 'Task not found';
            END IF;

        WHEN 'tasks/filterChanged' THEN

            UPDATE application_state
            SET selected_filter =
                (p_payload ->> 'filter')::task_filter
            WHERE application_id = p_application_id;

        WHEN 'counter/incremented' THEN

            IF v_previous_counter = 9223372036854775807 THEN
                RAISE EXCEPTION 'Counter overflow';
            END IF;

            v_resulting_counter := v_previous_counter + 1;

            UPDATE application_state
            SET counter_value = v_resulting_counter
            WHERE application_id = p_application_id;

        WHEN 'tasks/requested' THEN

            INSERT INTO async_requests (
                application_id,
                initiating_action_id,
                request_status,
                started_at
            )
            VALUES (
                p_application_id,
                v_action_id,
                'loading',
                NOW()
            );

        WHEN 'tasks/succeeded' THEN

            UPDATE async_requests
            SET request_status = 'succeeded',
                response_payload = p_payload,
                completed_at = NOW()
            WHERE request_id =
                (p_payload ->> 'request_id')::UUID
              AND application_id = p_application_id
              AND request_status = 'loading';

            IF NOT FOUND THEN
                RAISE EXCEPTION 'No active request found';
            END IF;

        WHEN 'tasks/failed' THEN

            UPDATE async_requests
            SET request_status = 'failed',
                error_message = p_payload ->> 'error',
                completed_at = NOW()
            WHERE request_id =
                (p_payload ->> 'request_id')::UUID
              AND application_id = p_application_id
              AND request_status = 'loading';

            IF NOT FOUND THEN
                RAISE EXCEPTION 'No active request found';
            END IF;

        WHEN 'app/reset' THEN

            DELETE FROM tasks
            WHERE application_id = p_application_id;

            UPDATE application_state
            SET counter_value = 0,
                selected_filter = 'all'
            WHERE application_id = p_application_id;

            UPDATE async_requests
            SET request_status = 'failed',
                error_message = 'Application state reset',
                completed_at = NOW()
            WHERE application_id = p_application_id
              AND request_status = 'loading';

        ELSE
            RAISE EXCEPTION 'Unsupported action';
    END CASE;

    UPDATE application_state
    SET revision = revision + 1
    WHERE application_id = p_application_id
    RETURNING revision INTO v_current_revision;

    SELECT counter_value
    INTO v_resulting_counter
    FROM application_state
    WHERE application_id = p_application_id;

    INSERT INTO reducer_executions (
        action_id,
        application_id,
        previous_revision,
        resulting_revision,
        previous_counter,
        resulting_counter,
        execution_succeeded
    )
    VALUES (
        v_action_id,
        p_application_id,
        v_current_revision - 1,
        v_current_revision,
        v_previous_counter,
        v_resulting_counter,
        TRUE
    );

    INSERT INTO state_snapshots (
        application_id,
        revision,
        state_payload
    )
    SELECT
        p_application_id,
        v_current_revision,
        jsonb_build_object(
            'counter', s.counter_value,
            'filter', s.selected_filter,
            'tasks', COALESCE(
                (
                    SELECT jsonb_agg(
                        jsonb_build_object(
                            'id', t.task_id,
                            'title', t.title,
                            'completed', t.is_completed
                        )
                        ORDER BY t.created_at
                    )
                    FROM tasks t
                    WHERE t.application_id = p_application_id
                ),
                '[]'::JSONB
            )
        )
    FROM application_state s
    WHERE s.application_id = p_application_id;

    UPDATE action_log
    SET status = 'succeeded',
        completed_at = NOW()
    WHERE action_id = v_action_id;

    dispatched_action_id := v_action_id;
    resulting_revision := v_current_revision;
    result_status := 'succeeded';

    RETURN NEXT;
END;
$$;

-- ============================================================
-- 16. ASYNCHRONOUS REQUEST VIEW
-- ============================================================

CREATE OR REPLACE VIEW async_request_report AS
SELECT
    r.request_id,
    a.application_name,
    r.request_status,
    r.started_at,
    r.completed_at,
    r.error_message,
    CASE
        WHEN r.completed_at IS NOT NULL
        THEN EXTRACT(
            EPOCH FROM (r.completed_at - r.started_at)
        )
        ELSE NULL
    END AS duration_seconds
FROM async_requests r
JOIN applications a
    ON a.application_id = r.application_id;

-- ============================================================
-- 17. DERIVED TASK SELECTOR
-- ============================================================

CREATE OR REPLACE FUNCTION get_visible_tasks(
    p_application_id UUID
)
RETURNS TABLE (
    task_id UUID,
    title VARCHAR,
    is_completed BOOLEAN
)
LANGUAGE sql
STABLE
AS $$
    SELECT
        t.task_id,
        t.title,
        t.is_completed
    FROM tasks t
    JOIN application_state s
        ON s.application_id = t.application_id
    WHERE t.application_id = p_application_id
      AND (
          s.selected_filter = 'all'
          OR (
              s.selected_filter = 'active'
              AND t.is_completed = FALSE
          )
          OR (
              s.selected_filter = 'completed'
              AND t.is_completed = TRUE
          )
      )
    ORDER BY t.created_at, t.task_id;
$$;

-- ============================================================
-- 18. STATE STATISTICS
-- ============================================================

CREATE OR REPLACE VIEW task_statistics AS
SELECT
    a.application_id,
    a.application_name,
    COUNT(t.task_id) AS total_tasks,

    COUNT(t.task_id) FILTER (
        WHERE t.is_completed = TRUE
    ) AS completed_tasks,

    COUNT(t.task_id) FILTER (
        WHERE t.is_completed = FALSE
    ) AS active_tasks,

    CASE
        WHEN COUNT(t.task_id) = 0 THEN 0
        ELSE ROUND(
            100.0 *
            COUNT(t.task_id) FILTER (
                WHERE t.is_completed = TRUE
            ) / COUNT(t.task_id),
            2
        )
    END AS completion_percentage

FROM applications a
LEFT JOIN tasks t
    ON t.application_id = a.application_id
GROUP BY
    a.application_id,
    a.application_name;

-- ============================================================
-- 19. ACTION EXECUTION REPORT
-- ============================================================

CREATE OR REPLACE VIEW action_execution_report AS
SELECT
    a.application_name,
    at.action_name,
    al.status,
    COUNT(*) AS action_count,
    MAX(al.created_at) AS latest_execution
FROM action_log al
JOIN applications a
    ON a.application_id = al.application_id
JOIN action_types at
    ON at.action_type_id = al.action_type_id
GROUP BY
    a.application_name,
    at.action_name,
    al.status;

-- ============================================================
-- 20. SAMPLE APPLICATIONS
-- ============================================================

INSERT INTO applications (
    application_name,
    environment
)
VALUES
    ('task-management-frontend', 'development'),
    ('enterprise-dashboard', 'testing');

-- ============================================================
-- 21. SAMPLE ACTION TRANSACTIONS
-- ============================================================

DO $$
DECLARE
    v_application UUID;
    v_first_task UUID := gen_random_uuid();
    v_second_task UUID := gen_random_uuid();
BEGIN
    SELECT application_id
    INTO v_application
    FROM applications
    WHERE application_name = 'task-management-frontend';

    -- Add task records through the reducer-style dispatch function.
    PERFORM dispatch_action(
        v_application,
        'tasks/added',
        jsonb_build_object(
            'id', v_first_task,
            'title', 'Understand Redux reducers'
        )
    );

    PERFORM dispatch_action(
        v_application,
        'tasks/added',
        jsonb_build_object(
            'id', v_second_task,
            'title', 'Implement middleware'
        )
    );

    -- Change a task's completion status.
    PERFORM dispatch_action(
        v_application,
        'tasks/toggled',
        jsonb_build_object(
            'id', v_first_task
        )
    );

    -- Increment application state.
    PERFORM dispatch_action(
        v_application,
        'counter/incremented'
    );

    -- Change the active selector.
    PERFORM dispatch_action(
        v_application,
        'tasks/filterChanged',
        '{"filter":"active"}'::JSONB
    );

    -- Demonstrate a request lifecycle.
    DECLARE
        v_action UUID;
        v_request UUID;
    BEGIN
        SELECT dispatched_action_id
        INTO v_action
        FROM dispatch_action(
            v_application,
            'tasks/requested',
            '{}'::JSONB
        );

        SELECT request_id
        INTO v_request
        FROM async_requests
        WHERE initiating_action_id = v_action;

        PERFORM dispatch_action(
            v_application,
            'tasks/succeeded',
            jsonb_build_object(
                'request_id', v_request,
                'data', jsonb_build_array(
                    'Remote task one',
                    'Remote task two'
                )
            )
        );
    END;

END;
$$;

-- ============================================================
-- 22. VALIDATION EXAMPLES
-- ============================================================

-- A. Application state.
SELECT
    a.application_name,
    s.counter_value,
    s.selected_filter,
    s.revision
FROM applications a
JOIN application_state s
    ON s.application_id = a.application_id;

-- B. Tasks.
SELECT
    a.application_name,
    t.task_id,
    t.title,
    t.is_completed
FROM tasks t
JOIN applications a
    ON a.application_id = t.application_id
ORDER BY t.created_at;

-- C. Derived selector.
SELECT *
FROM get_visible_tasks(
    (
        SELECT application_id
        FROM applications
        WHERE application_name = 'task-management-frontend'
    )
);

-- D. Aggregation.
SELECT *
FROM task_statistics;

-- E. Action execution report.
SELECT *
FROM action_execution_report
ORDER BY application_name, action_name;

-- F. Middleware configuration.
SELECT
    a.application_name,
    m.middleware_name,
    m.execution_order,
    m.is_enabled
FROM middleware_registry m
JOIN applications a
    ON a.application_id = m.application_id
ORDER BY
    a.application_name,
    m.execution_order;

-- G. Snapshot history.
SELECT
    a.application_name,
    s.revision,
    s.state_payload,
    s.created_at
FROM state_snapshots s
JOIN applications a
    ON a.application_id = s.application_id
ORDER BY s.revision;

-- H. Async request reporting.
SELECT *
FROM async_request_report;

-- ============================================================
-- 23. VALIDATION FAILURE DEMONSTRATION
--
-- Each failed dispatch rolls back its own changes.
-- ============================================================

DO $$
DECLARE
    v_application UUID;
BEGIN
    SELECT application_id
    INTO v_application
    FROM applications
    WHERE application_name = 'task-management-frontend';

    BEGIN
        PERFORM dispatch_action(
            v_application,
            'tasks/added',
            '{"title":"   "}'::JSONB
        );
    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE 'Expected validation failure: %',
                SQLERRM;
    END;

    BEGIN
        PERFORM dispatch_action(
            v_application,
            'unknown/action',
            '{}'::JSONB
        );
    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE 'Expected unknown-action failure: %',
                SQLERRM;
    END;
END;
$$;

-- ============================================================
-- 24. OPTIMISTIC CONCURRENCY DEMONSTRATION
-- ============================================================

DO $$
DECLARE
    v_application UUID;
    v_revision BIGINT;
BEGIN
    SELECT
        application_id,
        revision
    INTO
        v_application,
        v_revision
    FROM applications a
    JOIN application_state s
        ON s.application_id = a.application_id
    WHERE a.application_name = 'task-management-frontend';

    -- Valid revision.
    PERFORM dispatch_action(
        v_application,
        'counter/incremented',
        '{}'::JSONB,
        v_revision
    );

    -- An outdated revision is rejected.
    BEGIN
        PERFORM dispatch_action(
            v_application,
            'counter/incremented',
            '{}'::JSONB,
            v_revision
        );
    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE 'Expected concurrency conflict: %',
                SQLERRM;
    END;
END;
$$;

-- ============================================================
-- 25. PERFORMANCE AND DIAGNOSTIC QUERIES
-- ============================================================

EXPLAIN ANALYZE
SELECT *
FROM tasks
WHERE application_id = (
    SELECT application_id
    FROM applications
    WHERE application_name = 'task-management-frontend'
)
AND is_completed = FALSE;

SELECT
    application_name,
    total_tasks,
    completed_tasks,
    active_tasks,
    completion_percentage
FROM task_statistics
ORDER BY application_name;

SELECT
    status,
    COUNT(*) AS total_actions
FROM action_log
GROUP BY status
ORDER BY status;

COMMIT;

-- ============================================================
-- END OF REDUX STATE MANAGEMENT DATABASE MODEL
-- ============================================================
