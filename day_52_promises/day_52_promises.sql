DROP SCHEMA IF EXISTS promise_demo CASCADE;
CREATE SCHEMA promise_demo;
SET search_path TO promise_demo;

-- A database representation of asynchronous operations.
-- promise_state models the one-way settlement transition:
-- pending -> fulfilled
-- pending -> rejected.

CREATE TYPE promise_state AS ENUM (
    'pending',
    'fulfilled',
    'rejected'
);

CREATE TYPE combinator_type AS ENUM (
    'single',
    'all',
    'race',
    'all_settled',
    'any'
);

CREATE TABLE promise_workflows (
    workflow_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    workflow_name TEXT NOT NULL UNIQUE,
    combinator combinator_type NOT NULL DEFAULT 'single',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ
);

CREATE TABLE promise_operations (
    operation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    workflow_id BIGINT NOT NULL
        REFERENCES promise_workflows(workflow_id)
        ON DELETE CASCADE,
    operation_name TEXT NOT NULL,
    state promise_state NOT NULL DEFAULT 'pending',
    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    settled_at TIMESTAMPTZ,
    result_value JSONB,
    rejection_message TEXT,
    latency_ms INTEGER CHECK (latency_ms IS NULL OR latency_ms >= 0),
    UNIQUE (workflow_id, operation_name),
    CHECK (
        (state = 'fulfilled'
            AND result_value IS NOT NULL
            AND rejection_message IS NULL
            AND settled_at IS NOT NULL)
        OR
        (state = 'rejected'
            AND result_value IS NULL
            AND rejection_message IS NOT NULL
            AND settled_at IS NOT NULL)
        OR
        (state = 'pending'
            AND result_value IS NULL
            AND rejection_message IS NULL
            AND settled_at IS NULL)
    )
);

CREATE TABLE operation_events (
    event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    operation_id BIGINT NOT NULL
        REFERENCES promise_operations(operation_id)
        ON DELETE CASCADE,
    old_state promise_state,
    new_state promise_state NOT NULL,
    event_time TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    details JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX idx_promise_operations_workflow_state
    ON promise_operations (workflow_id, state);

CREATE INDEX idx_operation_events_operation_time
    ON operation_events (operation_id, event_time);

CREATE OR REPLACE FUNCTION prevent_invalid_promise_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.state <> 'pending' AND NEW.state <> OLD.state THEN
        RAISE EXCEPTION
            'promise % cannot transition from % to %',
            OLD.operation_id,
            OLD.state,
            NEW.state;
    END IF;

    IF OLD.state <> 'pending' THEN
        IF NEW.result_value IS DISTINCT FROM OLD.result_value
           OR NEW.rejection_message IS DISTINCT FROM OLD.rejection_message
           OR NEW.settled_at IS DISTINCT FROM OLD.settled_at THEN
            RAISE EXCEPTION
                'settled promise % cannot change its settlement data',
                OLD.operation_id;
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_promise_transition
BEFORE UPDATE ON promise_operations
FOR EACH ROW
EXECUTE FUNCTION prevent_invalid_promise_transition();

CREATE OR REPLACE FUNCTION record_operation_event()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.state IS DISTINCT FROM NEW.state THEN
        INSERT INTO operation_events (
            operation_id,
            old_state,
            new_state,
            details
        )
        VALUES (
            NEW.operation_id,
            OLD.state,
            NEW.state,
            jsonb_build_object(
                'result', NEW.result_value,
                'error', NEW.rejection_message
            )
        );
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_operation_event
AFTER UPDATE ON promise_operations
FOR EACH ROW
EXECUTE FUNCTION record_operation_event();

CREATE OR REPLACE FUNCTION settle_fulfilled(
    p_operation_id BIGINT,
    p_result JSONB,
    p_latency_ms INTEGER
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE promise_operations
    SET state = 'fulfilled',
        settled_at = CURRENT_TIMESTAMP,
        result_value = p_result,
        latency_ms = p_latency_ms
    WHERE operation_id = p_operation_id
      AND state = 'pending';

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'operation % is already settled or does not exist',
            p_operation_id;
    END IF;
END;
$$;

CREATE OR REPLACE FUNCTION settle_rejected(
    p_operation_id BIGINT,
    p_error TEXT,
    p_latency_ms INTEGER
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    IF p_error IS NULL OR btrim(p_error) = '' THEN
        RAISE EXCEPTION 'rejection message cannot be empty';
    END IF;

    UPDATE promise_operations
    SET state = 'rejected',
        settled_at = CURRENT_TIMESTAMP,
        rejection_message = p_error,
        latency_ms = p_latency_ms
    WHERE operation_id = p_operation_id
      AND state = 'pending';

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'operation % is already settled or does not exist',
            p_operation_id;
    END IF;
END;
$$;

INSERT INTO promise_workflows (workflow_name, combinator)
VALUES
    ('configuration-chain', 'single'),
    ('service-health-all', 'all'),
    ('nearest-region-race', 'race'),
    ('batch-observability', 'all_settled'),
    ('regional-failover-any', 'any');

INSERT INTO promise_operations (workflow_id, operation_name)
SELECT workflow_id, operation_name
FROM (
    SELECT
        w.workflow_id,
        x.operation_name
    FROM promise_workflows w
    CROSS JOIN LATERAL (
        VALUES
            ('configuration'),
            ('authorization'),
            ('deployment')
    ) AS x(operation_name)
    WHERE w.workflow_name = 'configuration-chain'

    UNION ALL

    SELECT
        w.workflow_id,
        x.operation_name
    FROM promise_workflows w
    CROSS JOIN LATERAL (
        VALUES
            ('database'),
            ('cache'),
            ('queue')
    ) AS x(operation_name)
    WHERE w.workflow_name = 'service-health-all'

    UNION ALL

    SELECT
        w.workflow_id,
        x.operation_name
    FROM promise_workflows w
    CROSS JOIN LATERAL (
        VALUES
            ('primary'),
            ('replica'),
            ('fallback')
    ) AS x(operation_name)
    WHERE w.workflow_name = 'nearest-region-race'

    UNION ALL

    SELECT
        w.workflow_id,
        x.operation_name
    FROM promise_workflows w
    CROSS JOIN LATERAL (
        VALUES
            ('metrics'),
            ('audit'),
            ('cache')
    ) AS x(operation_name)
    WHERE w.workflow_name = 'batch-observability'

    UNION ALL

    SELECT
        w.workflow_id,
        x.operation_name
    FROM promise_workflows w
    CROSS JOIN LATERAL (
        VALUES
            ('region-a'),
            ('region-b'),
            ('region-c')
    ) AS x(operation_name)
    WHERE w.workflow_name = 'regional-failover-any'
) AS seed;

-- Chained operations settle in dependency order.
BEGIN;

SELECT settle_fulfilled(
    operation_id,
    '{"timeout":30,"retries":3}'::jsonb,
    12
)
FROM promise_operations p
JOIN promise_workflows w USING (workflow_id)
WHERE w.workflow_name = 'configuration-chain'
  AND p.operation_name = 'configuration';

SELECT settle_fulfilled(
    operation_id,
    '{"authorized":true}'::jsonb,
    8
)
FROM promise_operations p
JOIN promise_workflows w USING (workflow_id)
WHERE w.workflow_name = 'configuration-chain'
  AND p.operation_name = 'authorization';

SELECT settle_fulfilled(
    operation_id,
    '{"deployment":"completed"}'::jsonb,
    45
)
FROM promise_operations p
JOIN promise_workflows w USING (workflow_id)
WHERE w.workflow_name = 'configuration-chain'
  AND p.operation_name = 'deployment';

COMMIT;

-- Promise.all: every member must fulfill for the aggregate to fulfill.
BEGIN;

SELECT settle_fulfilled(
    operation_id,
    jsonb_build_object('status', 'ready'),
    30
)
FROM promise_operations p
JOIN promise_workflows w USING (workflow_id)
WHERE w.workflow_name = 'service-health-all'
  AND p.operation_name = 'database';

SELECT settle_fulfilled(
    operation_id,
    jsonb_build_object('status', 'ready'),
    15
)
FROM promise_operations p
JOIN promise_workflows w USING (workflow_id)
WHERE w.workflow_name = 'service-health-all'
  AND p.operation_name = 'cache';

SELECT settle_rejected(
    operation_id,
    'queue unavailable',
    20
)
FROM promise_operations p
JOIN promise_workflows w USING (workflow_id)
WHERE w.workflow_name = 'service-health-all'
  AND p.operation_name = 'queue';

COMMIT;

-- Promise.race settles according to the first settlement, whether
-- that settlement is fulfillment or rejection.
BEGIN;

SELECT settle_fulfilled(
    operation_id,
    '{"response":"replica"}'::jsonb,
    25
)
FROM promise_operations p
JOIN promise_workflows w USING (workflow_id)
WHERE w.workflow_name = 'nearest-region-race'
  AND p.operation_name = 'replica';

SELECT settle_fulfilled(
    operation_id,
    '{"response":"fallback"}'::jsonb,
    60
)
FROM promise_operations p
JOIN promise_workflows w USING (workflow_id)
WHERE w.workflow_name = 'nearest-region-race'
  AND p.operation_name = 'fallback';

SELECT settle_rejected(
    operation_id,
    'primary timeout',
    90
)
FROM promise_operations p
JOIN promise_workflows w USING (workflow_id)
WHERE w.workflow_name = 'nearest-region-race'
  AND p.operation_name = 'primary';

COMMIT;

-- Promise.allSettled retains every outcome rather than rejecting the
-- aggregate when one operation fails.
BEGIN;

SELECT settle_fulfilled(
    operation_id,
    '{"records":1200}'::jsonb,
    20
)
FROM promise_operations p
JOIN promise_workflows w USING (workflow_id)
WHERE w.workflow_name = 'batch-observability'
  AND p.operation_name = 'metrics';

SELECT settle_rejected(
    operation_id,
    'audit service unavailable',
    35
)
FROM promise_operations p
JOIN promise_workflows w USING (workflow_id)
WHERE w.workflow_name = 'batch-observability'
  AND p.operation_name = 'audit';

SELECT settle_fulfilled(
    operation_id,
    '{"entries":450}'::jsonb,
    12
)
FROM promise_operations p
JOIN promise_workflows w USING (workflow_id)
WHERE w.workflow_name = 'batch-observability'
  AND p.operation_name = 'cache';

COMMIT;

-- Promise.any ignores rejections until a fulfillment is available.
BEGIN;

SELECT settle_rejected(
    operation_id,
    'region-a unavailable',
    50
)
FROM promise_operations p
JOIN promise_workflows w USING (workflow_id)
WHERE w.workflow_name = 'regional-failover-any'
  AND p.operation_name = 'region-a';

SELECT settle_fulfilled(
    operation_id,
    '{"region":"region-b"}'::jsonb,
    30
)
FROM promise_operations p
JOIN promise_workflows w USING (workflow_id)
WHERE w.workflow_name = 'regional-failover-any'
  AND p.operation_name = 'region-b';

SELECT settle_rejected(
    operation_id,
    'region-c unavailable',
    40
)
FROM promise_operations p
JOIN promise_workflows w USING (workflow_id)
WHERE w.workflow_name = 'regional-failover-any'
  AND p.operation_name = 'region-c';

COMMIT;

CREATE VIEW promise_operation_report AS
SELECT
    w.workflow_name,
    w.combinator,
    p.operation_name,
    p.state,
    p.latency_ms,
    p.result_value,
    p.rejection_message,
    p.started_at,
    p.settled_at
FROM promise_workflows w
JOIN promise_operations p
    ON p.workflow_id = w.workflow_id;

-- Aggregate evaluation for Promise.all semantics.
WITH workflow_status AS (
    SELECT
        w.workflow_id,
        w.workflow_name,
        COUNT(*) AS operation_count,
        COUNT(*) FILTER (
            WHERE p.state = 'fulfilled'
        ) AS fulfilled_count,
        COUNT(*) FILTER (
            WHERE p.state = 'rejected'
        ) AS rejected_count
    FROM promise_workflows w
    JOIN promise_operations p
        ON p.workflow_id = w.workflow_id
    WHERE w.combinator = 'all'
    GROUP BY w.workflow_id, w.workflow_name
)
SELECT
    workflow_name,
    operation_count,
    fulfilled_count,
    rejected_count,
    CASE
        WHEN rejected_count > 0 THEN 'rejected'
        WHEN fulfilled_count = operation_count THEN 'fulfilled'
        ELSE 'pending'
    END AS aggregate_state
FROM workflow_status;

-- Promise.allSettled reporting keeps both successful and failed outcomes.
SELECT
    workflow_name,
    COUNT(*) FILTER (WHERE state = 'fulfilled') AS fulfilled,
    COUNT(*) FILTER (WHERE state = 'rejected') AS rejected,
    COUNT(*) AS total
FROM promise_operation_report
WHERE combinator = 'all_settled'
GROUP BY workflow_name;

-- Promise.any reporting succeeds when at least one operation fulfills.
SELECT
    workflow_name,
    COUNT(*) FILTER (WHERE state = 'fulfilled') AS successful_candidates,
    CASE
        WHEN COUNT(*) FILTER (WHERE state = 'fulfilled') > 0
            THEN 'fulfilled'
        WHEN COUNT(*) FILTER (WHERE state = 'rejected') = COUNT(*)
            THEN 'rejected'
        ELSE 'pending'
    END AS aggregate_state
FROM promise_operation_report
WHERE combinator = 'any'
GROUP BY workflow_name;

-- Promise.race reporting uses the earliest settlement timestamp.
SELECT DISTINCT ON (workflow_name)
    workflow_name,
    operation_name AS first_settled_operation,
    state AS first_settled_state,
    settled_at
FROM promise_operation_report
WHERE combinator = 'race'
ORDER BY workflow_name, settled_at;

-- Event history makes settlement transitions auditable.
SELECT
    p.operation_name,
    e.old_state,
    e.new_state,
    e.event_time,
    e.details
FROM operation_events e
JOIN promise_operations p
    ON p.operation_id = e.operation_id
ORDER BY e.event_time, p.operation_name;

-- Demonstrate that a settled promise cannot be settled again.
DO $$
DECLARE
    operation_id_to_test BIGINT;
BEGIN
    SELECT p.operation_id
    INTO operation_id_to_test
    FROM promise_operations p
    JOIN promise_workflows w USING (workflow_id)
    WHERE w.workflow_name = 'configuration-chain'
      AND p.operation_name = 'deployment';

    BEGIN
        PERFORM settle_rejected(
            operation_id_to_test,
            'illegal second settlement',
            100
        );
    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE 'expected settlement failure: %', SQLERRM;
    END;
END;
$$;
