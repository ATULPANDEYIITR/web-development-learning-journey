DROP SCHEMA IF EXISTS control_flow_demo CASCADE;
CREATE SCHEMA control_flow_demo;

SET search_path TO control_flow_demo;

-- The relational model represents decisions that commonly require control
-- flow: ordered rules, task states, validation results, and execution runs.

CREATE TYPE execution_state AS ENUM (
    'pending',
    'running',
    'passed',
    'failed',
    'skipped'
);

CREATE TABLE workflow (
    workflow_id BIGSERIAL PRIMARY KEY,
    workflow_name TEXT NOT NULL UNIQUE,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    maximum_failures INTEGER NOT NULL DEFAULT 0,
    CONSTRAINT workflow_failure_limit_ck
        CHECK (maximum_failures >= 0)
);

CREATE TABLE workflow_step (
    step_id BIGSERIAL PRIMARY KEY,
    workflow_id BIGINT NOT NULL
        REFERENCES workflow(workflow_id)
        ON DELETE CASCADE,
    step_name TEXT NOT NULL,
    execution_order INTEGER NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    expected_result BOOLEAN NOT NULL,
    state execution_state NOT NULL DEFAULT 'pending',
    CONSTRAINT workflow_step_name_uq
        UNIQUE (workflow_id, step_name),
    CONSTRAINT workflow_step_order_uq
        UNIQUE (workflow_id, execution_order),
    CONSTRAINT workflow_step_order_ck
        CHECK (execution_order > 0)
);

CREATE TABLE execution_run (
    run_id BIGSERIAL PRIMARY KEY,
    workflow_id BIGINT NOT NULL
        REFERENCES workflow(workflow_id)
        ON DELETE CASCADE,
    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ,
    successful BOOLEAN,
    CONSTRAINT execution_time_ck
        CHECK (
            completed_at IS NULL
            OR completed_at >= started_at
        )
);

CREATE TABLE step_result (
    result_id BIGSERIAL PRIMARY KEY,
    run_id BIGINT NOT NULL
        REFERENCES execution_run(run_id)
        ON DELETE CASCADE,
    step_id BIGINT NOT NULL
        REFERENCES workflow_step(step_id)
        ON DELETE RESTRICT,
    state execution_state NOT NULL,
    message TEXT,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT run_step_uq
        UNIQUE (run_id, step_id)
);

CREATE INDEX workflow_step_lookup_idx
    ON workflow_step(workflow_id, execution_order);

CREATE INDEX step_result_run_state_idx
    ON step_result(run_id, state);

INSERT INTO workflow (
    workflow_name,
    enabled,
    maximum_failures
)
VALUES
    ('release-validation', TRUE, 0),
    ('data-quality-check', TRUE, 1),
    ('disabled-workflow', FALSE, 0);

INSERT INTO workflow_step (
    workflow_id,
    step_name,
    execution_order,
    enabled,
    expected_result
)
SELECT
    workflow_id,
    step_name,
    execution_order,
    enabled,
    expected_result
FROM (
    VALUES
        (
            'release-validation',
            'compile',
            1,
            TRUE,
            TRUE
        ),
        (
            'release-validation',
            'unit-tests',
            2,
            TRUE,
            TRUE
        ),
        (
            'release-validation',
            'security-scan',
            3,
            TRUE,
            FALSE
        ),
        (
            'release-validation',
            'documentation',
            4,
            FALSE,
            TRUE
        ),
        (
            'release-validation',
            'package',
            5,
            TRUE,
            TRUE
        ),
        (
            'data-quality-check',
            'schema-validation',
            1,
            TRUE,
            TRUE
        ),
        (
            'data-quality-check',
            'null-check',
            2,
            TRUE,
            TRUE
        ),
        (
            'data-quality-check',
            'range-check',
            3,
            TRUE,
            TRUE
        )
) AS source(
    workflow_name,
    step_name,
    execution_order,
    enabled,
    expected_result
)
JOIN workflow
    ON workflow.workflow_name = source.workflow_name;

-- A transaction models the all-or-nothing portion of an execution record.
BEGIN;

INSERT INTO execution_run (workflow_id)
SELECT workflow_id
FROM workflow
WHERE workflow_name = 'release-validation';

INSERT INTO step_result (
    run_id,
    step_id,
    state,
    message
)
SELECT
    current_run.run_id,
    step.step_id,
    CASE
        WHEN NOT step.enabled THEN 'skipped'::execution_state
        WHEN step.expected_result THEN 'passed'::execution_state
        ELSE 'failed'::execution_state
    END,
    CASE
        WHEN NOT step.enabled THEN 'step disabled'
        WHEN step.expected_result THEN 'validation passed'
        ELSE 'validation failed'
    END
FROM execution_run AS current_run
JOIN workflow_step AS step
    ON step.workflow_id = current_run.workflow_id
WHERE current_run.run_id = (
    SELECT MAX(run_id)
    FROM execution_run
    WHERE workflow_id = (
        SELECT workflow_id
        FROM workflow
        WHERE workflow_name = 'release-validation'
    )
);

COMMIT;

-- CASE expressions provide SQL-level branching. This query classifies each
-- result without pretending that all states are equivalent.

SELECT
    step.step_name,
    result.state,
    CASE
        WHEN result.state = 'passed' THEN 'continue'
        WHEN result.state = 'failed' THEN 'stop-or-escalate'
        WHEN result.state = 'skipped' THEN 'skip-work'
        ELSE 'state-requires-review'
    END AS control_action
FROM step_result AS result
JOIN workflow_step AS step
    ON step.step_id = result.step_id
ORDER BY step.execution_order;

-- A CTE calculates whether a run is eligible to finish successfully. The
-- FILTER clauses isolate failures without losing the complete run context.

WITH run_summary AS (
    SELECT
        run_id,
        COUNT(*) AS total_steps,
        COUNT(*) FILTER (WHERE state = 'passed') AS passed_steps,
        COUNT(*) FILTER (WHERE state = 'failed') AS failed_steps,
        COUNT(*) FILTER (WHERE state = 'skipped') AS skipped_steps
    FROM step_result
    GROUP BY run_id
)
SELECT
    run_id,
    total_steps,
    passed_steps,
    failed_steps,
    skipped_steps,
    CASE
        WHEN failed_steps = 0 THEN 'eligible'
        ELSE 'blocked'
    END AS execution_decision
FROM run_summary
ORDER BY run_id;

-- The following query finds the first failing step. The MIN operation plays
-- the role of early failure detection at query level.

SELECT
    run_id,
    MIN(step.execution_order) AS first_failed_order
FROM step_result AS result
JOIN workflow_step AS step
    ON step.step_id = result.step_id
WHERE result.state = 'failed'
GROUP BY run_id;

-- This query demonstrates a data-driven decision table. Instead of encoding
-- customer policy as application-only branching, policy conditions are
-- represented as rows and evaluated by SQL predicates.

CREATE TABLE pricing_rule (
    rule_id BIGSERIAL PRIMARY KEY,
    customer_type TEXT NOT NULL,
    minimum_amount NUMERIC(12, 2) NOT NULL,
    maximum_risk NUMERIC(5, 4) NOT NULL,
    discount_rate NUMERIC(5, 4) NOT NULL,
    priority INTEGER NOT NULL,
    CONSTRAINT pricing_amount_ck
        CHECK (minimum_amount >= 0),
    CONSTRAINT pricing_risk_ck
        CHECK (maximum_risk BETWEEN 0 AND 1),
    CONSTRAINT pricing_discount_ck
        CHECK (discount_rate BETWEEN 0 AND 1),
    CONSTRAINT pricing_priority_ck
        CHECK (priority > 0)
);

INSERT INTO pricing_rule (
    customer_type,
    minimum_amount,
    maximum_risk,
    discount_rate,
    priority
)
VALUES
    ('enterprise', 10000, 0.89, 0.15, 1),
    ('enterprise', 0, 0.89, 0.10, 2),
    ('student', 0, 0.89, 0.20, 3),
    ('consumer', 0, 0.89, 0.00, 4);

WITH request AS (
    SELECT
        'enterprise'::TEXT AS customer_type,
        25000.00::NUMERIC AS amount,
        0.10::NUMERIC AS risk_score
)
SELECT
    request.customer_type,
    request.amount,
    request.risk_score,
    CASE
        WHEN request.risk_score >= 0.90 THEN 'blocked'
        WHEN request.amount = 0 THEN 'no-charge'
        WHEN rule.rule_id IS NOT NULL THEN 'approved'
        ELSE 'no-matching-rule'
    END AS decision,
    COALESCE(rule.discount_rate, 0) AS discount_rate
FROM request
LEFT JOIN LATERAL (
    SELECT pricing_rule.*
    FROM pricing_rule
    WHERE pricing_rule.customer_type = request.customer_type
      AND request.amount >= pricing_rule.minimum_amount
      AND request.risk_score <= pricing_rule.maximum_risk
    ORDER BY pricing_rule.priority
    LIMIT 1
) AS rule ON TRUE;

-- A view makes the operational control decision reusable.

CREATE VIEW workflow_run_status AS
SELECT
    run.run_id,
    workflow.workflow_name,
    COUNT(result.result_id) AS recorded_steps,
    COUNT(result.result_id)
        FILTER (WHERE result.state = 'failed') AS failures,
    CASE
        WHEN NOT workflow.enabled THEN 'disabled'
        WHEN COUNT(result.result_id)
             FILTER (WHERE result.state = 'failed')
             > workflow.maximum_failures
            THEN 'blocked'
        WHEN COUNT(result.result_id) = 0
            THEN 'not-started'
        ELSE 'evaluated'
    END AS workflow_decision
FROM execution_run AS run
JOIN workflow
    ON workflow.workflow_id = run.workflow_id
LEFT JOIN step_result AS result
    ON result.run_id = run.run_id
GROUP BY
    run.run_id,
    workflow.workflow_name,
    workflow.enabled,
    workflow.maximum_failures;

SELECT *
FROM workflow_run_status
ORDER BY run_id;

-- A trigger prevents an invalid terminal-state transition. The database
-- therefore enforces a control-flow invariant instead of trusting callers.

CREATE OR REPLACE FUNCTION prevent_invalid_step_state_change()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.state IN ('passed', 'failed', 'skipped')
       AND NEW.state <> OLD.state THEN
        RAISE EXCEPTION
            'terminal step state % cannot transition to %',
            OLD.state,
            NEW.state;
    END IF;

    IF NEW.state = 'running' AND OLD.state NOT IN ('pending') THEN
        RAISE EXCEPTION
            'only pending steps can transition to running';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER step_state_transition_guard
BEFORE UPDATE OF state
ON step_result
FOR EACH ROW
EXECUTE FUNCTION prevent_invalid_step_state_change();

-- This valid transition is permitted because the row starts in a nonterminal
-- state in the demonstration run.
UPDATE step_result
SET state = 'running'
WHERE result_id = (
    SELECT MIN(result_id)
    FROM step_result
);

-- This report exposes records that would require application-level handling
-- because a skipped step does not represent successful execution.

SELECT
    workflow.workflow_name,
    step.step_name,
    result.state,
    CASE
        WHEN result.state = 'passed' THEN 'continue'
        WHEN result.state = 'skipped' THEN 'do-not-count-as-success'
        WHEN result.state = 'failed' THEN 'halt-or-escalate'
        ELSE 'continue-evaluation'
    END AS recommended_flow
FROM step_result AS result
JOIN workflow_step AS step
    ON step.step_id = result.step_id
JOIN workflow
    ON workflow.workflow_id = step.workflow_id
ORDER BY
    workflow.workflow_name,
    step.execution_order;
