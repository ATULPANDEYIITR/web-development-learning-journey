DROP SCHEMA IF EXISTS async_workflow CASCADE;
CREATE SCHEMA async_workflow;
SET search_path TO async_workflow;

-- The model represents asynchronous jobs, independent operations,
-- dependencies, attempts, and terminal states.

CREATE TYPE job_status AS ENUM (
    'queued',
    'running',
    'completed',
    'failed',
    'timed_out',
    'cancelled'
);

CREATE TYPE operation_status AS ENUM (
    'pending',
    'running',
    'completed',
    'failed',
    'timed_out',
    'cancelled'
);

CREATE TABLE async_job (
    job_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    job_name TEXT NOT NULL,
    status job_status NOT NULL DEFAULT 'queued',
    max_concurrency INTEGER NOT NULL DEFAULT 3
        CHECK (max_concurrency > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    CHECK (
        completed_at IS NULL
        OR started_at IS NULL
        OR completed_at >= started_at
    )
);

CREATE TABLE async_operation (
    operation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    job_id BIGINT NOT NULL
        REFERENCES async_job(job_id)
        ON DELETE CASCADE,
    operation_name TEXT NOT NULL,
    status operation_status NOT NULL DEFAULT 'pending',
    timeout_ms INTEGER NOT NULL
        CHECK (timeout_ms > 0),
    max_attempts INTEGER NOT NULL DEFAULT 3
        CHECK (max_attempts > 0),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    result_value JSONB,
    error_message TEXT,
    UNIQUE (job_id, operation_name),
    CHECK (
        completed_at IS NULL
        OR started_at IS NULL
        OR completed_at >= started_at
    )
);

CREATE TABLE operation_dependency (
    operation_id BIGINT NOT NULL
        REFERENCES async_operation(operation_id)
        ON DELETE CASCADE,
    depends_on_operation_id BIGINT NOT NULL
        REFERENCES async_operation(operation_id)
        ON DELETE CASCADE,
    PRIMARY KEY (operation_id, depends_on_operation_id),
    CHECK (operation_id <> depends_on_operation_id)
);

CREATE TABLE operation_attempt (
    attempt_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    operation_id BIGINT NOT NULL
        REFERENCES async_operation(operation_id)
        ON DELETE CASCADE,
    attempt_number INTEGER NOT NULL
        CHECK (attempt_number > 0),
    status operation_status NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    UNIQUE (operation_id, attempt_number)
);

CREATE INDEX idx_async_operation_job_status
    ON async_operation (job_id, status);

CREATE INDEX idx_operation_attempt_operation
    ON operation_attempt (operation_id, attempt_number DESC);

CREATE TABLE async_event (
    event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    job_id BIGINT NOT NULL REFERENCES async_job(job_id) ON DELETE CASCADE,
    operation_id BIGINT REFERENCES async_operation(operation_id)
        ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    event_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE OR REPLACE FUNCTION record_operation_event()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'UPDATE'
       AND OLD.status IS DISTINCT FROM NEW.status THEN
        INSERT INTO async_event (
            job_id,
            operation_id,
            event_type,
            event_data
        )
        SELECT
            NEW.job_id,
            NEW.operation_id,
            'operation_status_changed',
            jsonb_build_object(
                'from', OLD.status::text,
                'to', NEW.status::text
            )
        FROM async_operation
        WHERE operation_id = NEW.operation_id;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_operation_status_event
AFTER UPDATE OF status ON async_operation
FOR EACH ROW
EXECUTE FUNCTION record_operation_event();

CREATE OR REPLACE FUNCTION start_operation(
    p_operation_id BIGINT
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    v_blocked INTEGER;
BEGIN
    SELECT count(*)
    INTO v_blocked
    FROM operation_dependency d
    JOIN async_operation dependency
      ON dependency.operation_id = d.depends_on_operation_id
    WHERE d.operation_id = p_operation_id
      AND dependency.status <> 'completed';

    IF v_blocked > 0 THEN
        RAISE EXCEPTION
            'operation % has incomplete dependencies',
            p_operation_id;
    END IF;

    UPDATE async_operation
    SET
        status = 'running',
        started_at = COALESCE(started_at, clock_timestamp())
    WHERE operation_id = p_operation_id
      AND status = 'pending';

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'operation % is not pending',
            p_operation_id;
    END IF;

    INSERT INTO operation_attempt (
        operation_id,
        attempt_number,
        status
    )
    SELECT
        p_operation_id,
        COALESCE(MAX(attempt_number), 0) + 1,
        'running'
    FROM operation_attempt
    WHERE operation_id = p_operation_id;
END;
$$;

CREATE OR REPLACE FUNCTION finish_operation(
    p_operation_id BIGINT,
    p_success BOOLEAN,
    p_result JSONB DEFAULT NULL,
    p_error TEXT DEFAULT NULL
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    v_status operation_status;
BEGIN
    v_status :=
        CASE
            WHEN p_success THEN 'completed'::operation_status
            ELSE 'failed'::operation_status
        END;

    UPDATE async_operation
    SET
        status = v_status,
        completed_at = clock_timestamp(),
        result_value = CASE
            WHEN p_success THEN p_result
            ELSE result_value
        END,
        error_message = CASE
            WHEN p_success THEN NULL
            ELSE p_error
        END
    WHERE operation_id = p_operation_id
      AND status = 'running';

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'operation % is not running',
            p_operation_id;
    END IF;

    UPDATE operation_attempt
    SET
        status = v_status,
        completed_at = clock_timestamp(),
        error_message = CASE
            WHEN p_success THEN NULL
            ELSE p_error
        END
    WHERE operation_id = p_operation_id
      AND status = 'running';
END;
$$;

INSERT INTO async_job (job_name, max_concurrency)
VALUES
    ('checkout-processing', 3),
    ('report-generation', 2);

INSERT INTO async_operation (
    job_id,
    operation_name,
    timeout_ms,
    max_attempts
)
SELECT
    j.job_id,
    operation_name,
    timeout_ms,
    max_attempts
FROM async_job j
CROSS JOIN (
    VALUES
        ('load-customer', 1000, 2),
        ('load-inventory', 1000, 3),
        ('calculate-total', 1500, 2),
        ('send-receipt', 2000, 3)
) AS operations(operation_name, timeout_ms, max_attempts)
WHERE j.job_name = 'checkout-processing';

INSERT INTO async_operation (
    job_id,
    operation_name,
    timeout_ms,
    max_attempts
)
SELECT
    j.job_id,
    operation_name,
    timeout_ms,
    max_attempts
FROM async_job j
CROSS JOIN (
    VALUES
        ('collect-sales', 5000, 3),
        ('calculate-metrics', 5000, 2),
        ('publish-report', 3000, 3)
) AS operations(operation_name, timeout_ms, max_attempts)
WHERE j.job_name = 'report-generation';

-- calculate-total cannot begin until customer and inventory work completes.
INSERT INTO operation_dependency (
    operation_id,
    depends_on_operation_id
)
SELECT
    total.operation_id,
    dependency.operation_id
FROM async_operation total
JOIN async_operation dependency
  ON dependency.job_id = total.job_id
WHERE total.operation_name = 'calculate-total'
  AND dependency.operation_name IN (
      'load-customer',
      'load-inventory'
  );

-- send-receipt depends on the calculated result.
INSERT INTO operation_dependency (
    operation_id,
    depends_on_operation_id
)
SELECT
    receipt.operation_id,
    total.operation_id
FROM async_operation receipt
JOIN async_operation total
  ON total.job_id = receipt.job_id
WHERE receipt.operation_name = 'send-receipt'
  AND total.operation_name = 'calculate-total';

-- The following transaction demonstrates a complete asynchronous
-- state transition with database-level integrity.
BEGIN;

SELECT start_operation(operation_id)
FROM async_operation
WHERE operation_name IN ('load-customer', 'load-inventory');

SELECT finish_operation(
    operation_id,
    TRUE,
    jsonb_build_object('records', 120)
)
FROM async_operation
WHERE operation_name = 'load-customer';

SELECT finish_operation(
    operation_id,
    TRUE,
    jsonb_build_object('records', 85)
)
FROM async_operation
WHERE operation_name = 'load-inventory';

SELECT start_operation(operation_id)
FROM async_operation
WHERE operation_name = 'calculate-total';

SELECT finish_operation(
    operation_id,
    TRUE,
    jsonb_build_object('total', 18450.75)
)
FROM async_operation
WHERE operation_name = 'calculate-total';

SELECT start_operation(operation_id)
FROM async_operation
WHERE operation_name = 'send-receipt';

SELECT finish_operation(
    operation_id,
    TRUE,
    jsonb_build_object('message_id', 'msg-7842')
)
FROM async_operation
WHERE operation_name = 'send-receipt';

COMMIT;

-- A failed operation remains distinct from successful parallel work.
BEGIN;

SELECT start_operation(operation_id)
FROM async_operation
WHERE operation_name = 'collect-sales';

SELECT finish_operation(
    operation_id,
    FALSE,
    NULL,
    'analytics database temporarily unavailable'
)
FROM async_operation
WHERE operation_name = 'collect-sales';

ROLLBACK;

-- Inspect current operation states.
SELECT
    j.job_name,
    o.operation_name,
    o.status,
    o.timeout_ms,
    o.max_attempts,
    o.result_value,
    o.error_message
FROM async_job j
JOIN async_operation o
  ON o.job_id = j.job_id
ORDER BY j.job_name, o.operation_id;

-- Determine which operations are currently eligible to start.
WITH dependency_state AS (
    SELECT
        o.operation_id,
        o.operation_name,
        o.status,
        COUNT(d.depends_on_operation_id) AS dependency_count,
        COUNT(*) FILTER (
            WHERE dependency.status = 'completed'
        ) AS completed_dependencies
    FROM async_operation o
    LEFT JOIN operation_dependency d
      ON d.operation_id = o.operation_id
    LEFT JOIN async_operation dependency
      ON dependency.operation_id = d.depends_on_operation_id
    GROUP BY o.operation_id, o.operation_name, o.status
)
SELECT
    operation_id,
    operation_name
FROM dependency_state
WHERE status = 'pending'
  AND dependency_count = completed_dependencies;

-- Aggregate success and failure rates by job.
SELECT
    j.job_name,
    COUNT(*) AS operation_count,
    COUNT(*) FILTER (
        WHERE o.status = 'completed'
    ) AS completed_count,
    COUNT(*) FILTER (
        WHERE o.status = 'failed'
    ) AS failed_count,
    ROUND(
        100.0
        * COUNT(*) FILTER (WHERE o.status = 'completed')
        / NULLIF(COUNT(*), 0),
        2
    ) AS completion_percentage
FROM async_job j
JOIN async_operation o
  ON o.job_id = j.job_id
GROUP BY j.job_name
ORDER BY j.job_name;

-- Event history makes asynchronous state transitions auditable.
SELECT
    event_id,
    job_id,
    operation_id,
    event_type,
    event_data,
    created_at
FROM async_event
ORDER BY event_id;
