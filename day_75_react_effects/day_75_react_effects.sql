-- ============================================================
-- REACT EFFECTS: PostgreSQL lifecycle and resource audit model
-- PostgreSQL 15+
--
-- Models:
-- Components -> Renders -> Effect Definitions
-- -> Effect Executions -> Dependency Snapshots
-- -> Cleanup Operations -> Managed Resources
--
-- The database provides an auditable lifecycle model.
-- Actual React scheduling remains the responsibility of React.
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS react_effects;

SET search_path TO react_effects, public;

-- ------------------------------------------------------------
-- 1. Enumerated domain states
-- ------------------------------------------------------------

CREATE TYPE component_status AS ENUM (
    'mounted',
    'unmounted'
);

CREATE TYPE dependency_mode AS ENUM (
    'every_commit',
    'mount_only',
    'tracked'
);

CREATE TYPE execution_status AS ENUM (
    'running',
    'succeeded',
    'failed',
    'cancelled'
);

CREATE TYPE cleanup_status AS ENUM (
    'pending',
    'completed',
    'failed',
    'not_required'
);

CREATE TYPE resource_status AS ENUM (
    'active',
    'released',
    'failed'
);

CREATE TYPE effect_execution_type AS ENUM (
    'setup',
    'strict_mode_setup',
    'cleanup'
);

-- ------------------------------------------------------------
-- 2. Components
-- ------------------------------------------------------------

CREATE TABLE components (
    component_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    component_name VARCHAR(150) NOT NULL UNIQUE,

    status component_status NOT NULL DEFAULT 'mounted',

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    unmounted_at TIMESTAMPTZ,

    CONSTRAINT component_unmount_consistency
        CHECK (
            (status = 'mounted' AND unmounted_at IS NULL)
            OR
            (status = 'unmounted' AND unmounted_at IS NOT NULL)
        )
);

-- ------------------------------------------------------------
-- 3. Render commits
-- ------------------------------------------------------------

CREATE TABLE renders (
    render_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    component_id BIGINT NOT NULL
        REFERENCES components(component_id),

    commit_number INTEGER NOT NULL CHECK (commit_number > 0),

    committed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_component_commit
        UNIQUE (component_id, commit_number)
);

-- ------------------------------------------------------------
-- 4. Effect definitions
-- ------------------------------------------------------------

CREATE TABLE effects (
    effect_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    component_id BIGINT NOT NULL
        REFERENCES components(component_id),

    effect_name VARCHAR(150) NOT NULL,

    mode dependency_mode NOT NULL,

    enabled BOOLEAN NOT NULL DEFAULT TRUE,

    requires_cleanup BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_component_effect
        UNIQUE (component_id, effect_name)
);

-- ------------------------------------------------------------
-- 5. Dependency definitions
--
-- position preserves dependency-array order.
-- dependency_value stores a JSON representation for auditing.
-- dependency_token provides a stable comparison token.
-- Object identity cannot be reconstructed from JSON alone.
-- ------------------------------------------------------------

CREATE TABLE effect_dependencies (
    dependency_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    effect_id BIGINT NOT NULL
        REFERENCES effects(effect_id) ON DELETE CASCADE,

    position INTEGER NOT NULL CHECK (position >= 0),

    dependency_name VARCHAR(150) NOT NULL,

    dependency_value JSONB NOT NULL,

    dependency_token TEXT NOT NULL,

    CONSTRAINT unique_dependency_position
        UNIQUE (effect_id, position),

    CONSTRAINT unique_dependency_name
        UNIQUE (effect_id, dependency_name)
);

-- ------------------------------------------------------------
-- 6. Effect executions
-- ------------------------------------------------------------

CREATE TABLE effect_executions (
    execution_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    effect_id BIGINT NOT NULL
        REFERENCES effects(effect_id),

    render_id BIGINT NOT NULL
        REFERENCES renders(render_id),

    execution_type effect_execution_type NOT NULL DEFAULT 'setup',

    status execution_status NOT NULL DEFAULT 'running',

    cleanup_state cleanup_status NOT NULL DEFAULT 'pending',

    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    finished_at TIMESTAMPTZ,

    error_message TEXT,

    CONSTRAINT execution_finish_consistency
        CHECK (
            (status = 'running' AND finished_at IS NULL)
            OR
            (status <> 'running' AND finished_at IS NOT NULL)
        ),

    CONSTRAINT execution_cleanup_consistency
        CHECK (
            status <> 'succeeded'
            OR cleanup_state <> 'completed'
            OR finished_at IS NOT NULL
        )
);

CREATE INDEX idx_effect_executions_effect_time
    ON effect_executions(effect_id, started_at DESC);

CREATE INDEX idx_effect_executions_status
    ON effect_executions(status, started_at DESC);

-- ------------------------------------------------------------
-- 7. Dependency snapshots
-- ------------------------------------------------------------

CREATE TABLE execution_dependencies (
    execution_id BIGINT NOT NULL
        REFERENCES effect_executions(execution_id)
        ON DELETE CASCADE,

    position INTEGER NOT NULL CHECK (position >= 0),

    dependency_name VARCHAR(150) NOT NULL,

    dependency_value JSONB NOT NULL,

    dependency_token TEXT NOT NULL,

    PRIMARY KEY (execution_id, position)
);

-- ------------------------------------------------------------
-- 8. Managed external resources
-- ------------------------------------------------------------

CREATE TABLE managed_resources (
    resource_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    component_id BIGINT NOT NULL
        REFERENCES components(component_id),

    effect_id BIGINT NOT NULL
        REFERENCES effects(effect_id),

    execution_id BIGINT NOT NULL
        REFERENCES effect_executions(execution_id),

    resource_key VARCHAR(200) NOT NULL,

    status resource_status NOT NULL DEFAULT 'active',

    acquired_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    released_at TIMESTAMPTZ,

    CONSTRAINT resource_release_consistency
        CHECK (
            (status = 'active' AND released_at IS NULL)
            OR
            (status <> 'active' AND released_at IS NOT NULL)
        )
);

CREATE UNIQUE INDEX idx_active_resource_key
    ON managed_resources(component_id, resource_key)
    WHERE status = 'active';

CREATE INDEX idx_resource_component_status
    ON managed_resources(component_id, status);

-- ------------------------------------------------------------
-- 9. Cleanup execution history
-- ------------------------------------------------------------

CREATE TABLE cleanup_operations (
    cleanup_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    execution_id BIGINT NOT NULL
        REFERENCES effect_executions(execution_id),

    resource_id BIGINT
        REFERENCES managed_resources(resource_id),

    status cleanup_status NOT NULL DEFAULT 'pending',

    attempted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    completed_at TIMESTAMPTZ,

    error_message TEXT,

    CONSTRAINT cleanup_completion_consistency
        CHECK (
            (status = 'completed' AND completed_at IS NOT NULL)
            OR
            (status <> 'completed' AND completed_at IS NULL)
        )
);

-- ------------------------------------------------------------
-- 10. Validate component lifecycle
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_effect_component()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    current_status component_status;
BEGIN
    SELECT status
    INTO current_status
    FROM components
    WHERE component_id = NEW.component_id
    FOR UPDATE;

    IF current_status IS DISTINCT FROM 'mounted' THEN
        RAISE EXCEPTION
            'Cannot add an effect to an unmounted component';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_effect_component
BEFORE INSERT ON effects
FOR EACH ROW
EXECUTE FUNCTION validate_effect_component();

-- ------------------------------------------------------------
-- 11. Validate dependency mode
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_dependency_mode()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    selected_mode dependency_mode;
    selected_enabled BOOLEAN;
BEGIN
    SELECT mode, enabled
    INTO selected_mode, selected_enabled
    FROM effects
    WHERE effect_id = NEW.effect_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Effect does not exist';
    END IF;

    IF NOT selected_enabled THEN
        RAISE EXCEPTION 'Cannot modify a disabled effect';
    END IF;

    IF selected_mode = 'mount_only'
       AND EXISTS (
           SELECT 1
           FROM effect_dependencies
           WHERE effect_id = NEW.effect_id
       )
    THEN
        RAISE EXCEPTION
            'Mount-only effects cannot have dependencies';
    END IF;

    IF selected_mode = 'every_commit'
       AND EXISTS (
           SELECT 1
           FROM effect_dependencies
           WHERE effect_id = NEW.effect_id
       )
    THEN
        RAISE EXCEPTION
            'Every-commit effects cannot have tracked dependencies';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_dependency_mode
BEFORE INSERT ON effect_dependencies
FOR EACH ROW
EXECUTE FUNCTION validate_dependency_mode();

-- ------------------------------------------------------------
-- 12. Validate dependency array ordering
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_dependency_position()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    existing_count INTEGER;
BEGIN
    SELECT COUNT(*)
    INTO existing_count
    FROM effect_dependencies
    WHERE effect_id = NEW.effect_id;

    IF NEW.position <> existing_count THEN
        RAISE EXCEPTION
            'Dependencies must be inserted in sequential order';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_dependency_position
BEFORE INSERT ON effect_dependencies
FOR EACH ROW
EXECUTE FUNCTION validate_dependency_position();

-- ------------------------------------------------------------
-- 13. Prevent invalid execution records
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_effect_execution()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    component_state component_status;
    effect_component BIGINT;
    render_component BIGINT;
    effect_enabled BOOLEAN;
BEGIN
    SELECT component_id, enabled
    INTO effect_component, effect_enabled
    FROM effects
    WHERE effect_id = NEW.effect_id;

    SELECT component_id
    INTO render_component
    FROM renders
    WHERE render_id = NEW.render_id;

    IF effect_component IS DISTINCT FROM render_component THEN
        RAISE EXCEPTION
            'Effect and render must belong to the same component';
    END IF;

    SELECT status
    INTO component_state
    FROM components
    WHERE component_id = effect_component;

    IF component_state <> 'mounted' THEN
        RAISE EXCEPTION
            'Cannot execute effects after component unmount';
    END IF;

    IF NOT effect_enabled THEN
        RAISE EXCEPTION 'Effect is disabled';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_execution
BEFORE INSERT ON effect_executions
FOR EACH ROW
EXECUTE FUNCTION validate_effect_execution();

-- ------------------------------------------------------------
-- 14. Effect lifecycle reporting view
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW effect_lifecycle_report AS
SELECT
    c.component_name,
    c.status AS component_status,
    e.effect_name,
    e.mode,
    COUNT(x.execution_id) AS execution_count,
    COUNT(*) FILTER (
        WHERE x.status = 'failed'
    ) AS failed_executions,
    COUNT(*) FILTER (
        WHERE x.cleanup_state = 'completed'
    ) AS completed_cleanups,
    MAX(x.started_at) AS last_execution
FROM components c
JOIN effects e
    ON e.component_id = c.component_id
LEFT JOIN effect_executions x
    ON x.effect_id = e.effect_id
GROUP BY
    c.component_name,
    c.status,
    e.effect_name,
    e.mode;

-- ------------------------------------------------------------
-- 15. Create a new render commit
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION create_render(
    p_component_id BIGINT
)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    next_number INTEGER;
    new_render_id BIGINT;
BEGIN
    PERFORM 1
    FROM components
    WHERE component_id = p_component_id
      AND status = 'mounted'
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Component is missing or unmounted';
    END IF;

    SELECT COALESCE(MAX(commit_number), 0) + 1
    INTO next_number
    FROM renders
    WHERE component_id = p_component_id;

    INSERT INTO renders (
        component_id,
        commit_number
    )
    VALUES (
        p_component_id,
        next_number
    )
    RETURNING render_id INTO new_render_id;

    RETURN new_render_id;
END;
$$;

-- ------------------------------------------------------------
-- 16. Complete an execution
-- ------------------------------------------------------------

CREATE OR REPLACE PROCEDURE complete_execution(
    p_execution_id BIGINT,
    p_status execution_status,
    p_error TEXT DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF p_status = 'running' THEN
        RAISE EXCEPTION
            'Final status cannot be running';
    END IF;

    UPDATE effect_executions
    SET
        status = p_status,
        error_message = p_error,
        finished_at = CURRENT_TIMESTAMP,
        cleanup_state = CASE
            WHEN p_status = 'failed'
                THEN 'pending'::cleanup_status
            ELSE cleanup_state
        END
    WHERE execution_id = p_execution_id
      AND status = 'running';

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Execution not found or already finalized';
    END IF;
END;
$$;

-- ------------------------------------------------------------
-- 17. Release a managed resource transactionally
-- ------------------------------------------------------------

CREATE OR REPLACE PROCEDURE release_resource(
    p_resource_id BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    selected_execution BIGINT;
    selected_status resource_status;
    new_cleanup_id BIGINT;
BEGIN
    SELECT execution_id, status
    INTO selected_execution, selected_status
    FROM managed_resources
    WHERE resource_id = p_resource_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Resource not found';
    END IF;

    IF selected_status = 'released' THEN
        RETURN;
    END IF;

    UPDATE managed_resources
    SET
        status = 'released',
        released_at = CURRENT_TIMESTAMP
    WHERE resource_id = p_resource_id;

    INSERT INTO cleanup_operations (
        execution_id,
        resource_id,
        status,
        completed_at
    )
    VALUES (
        selected_execution,
        p_resource_id,
        'completed',
        CURRENT_TIMESTAMP
    )
    RETURNING cleanup_id INTO new_cleanup_id;

    UPDATE effect_executions
    SET cleanup_state = 'completed'
    WHERE execution_id = selected_execution;

    RAISE NOTICE
        'Resource % released; cleanup record % created',
        p_resource_id,
        new_cleanup_id;
END;
$$;

-- ------------------------------------------------------------
-- 18. Unmount a component
-- ------------------------------------------------------------

CREATE OR REPLACE PROCEDURE unmount_component(
    p_component_id BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    active_resource RECORD;
BEGIN
    PERFORM 1
    FROM components
    WHERE component_id = p_component_id
      AND status = 'mounted'
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Component not found or already unmounted';
    END IF;

    -- Release resources before changing component state.
    FOR active_resource IN
        SELECT resource_id
        FROM managed_resources
        WHERE component_id = p_component_id
          AND status = 'active'
        ORDER BY resource_id DESC
    LOOP
        CALL release_resource(active_resource.resource_id);
    END LOOP;

    UPDATE components
    SET
        status = 'unmounted',
        unmounted_at = CURRENT_TIMESTAMP
    WHERE component_id = p_component_id;
END;
$$;

-- ============================================================
-- 19. SAMPLE DATA
-- ============================================================

INSERT INTO components(component_name)
VALUES
    ('AnalyticsDashboard'),
    ('SecurityMonitor'),
    ('SearchPanel');

INSERT INTO effects (
    component_id,
    effect_name,
    mode,
    requires_cleanup
)
SELECT
    component_id,
    'channel-subscription',
    'tracked',
    TRUE
FROM components
WHERE component_name = 'AnalyticsDashboard';

INSERT INTO effects (
    component_id,
    effect_name,
    mode,
    requires_cleanup
)
SELECT
    component_id,
    'initialization',
    'mount_only',
    FALSE
FROM components
WHERE component_name = 'AnalyticsDashboard';

INSERT INTO effects (
    component_id,
    effect_name,
    mode,
    requires_cleanup
)
SELECT
    component_id,
    'render-audit',
    'every_commit',
    FALSE
FROM components
WHERE component_name = 'AnalyticsDashboard';

INSERT INTO effects (
    component_id,
    effect_name,
    mode,
    requires_cleanup
)
SELECT
    component_id,
    'security-event-listener',
    'tracked',
    TRUE
FROM components
WHERE component_name = 'SecurityMonitor';

INSERT INTO effects (
    component_id,
    effect_name,
    mode,
    requires_cleanup
)
SELECT
    component_id,
    'search-request',
    'tracked',
    TRUE
FROM components
WHERE component_name = 'SearchPanel';

-- Dependency definitions.
INSERT INTO effect_dependencies (
    effect_id,
    position,
    dependency_name,
    dependency_value,
    dependency_token
)
SELECT
    effect_id,
    0,
    'channel',
    '"system-events"'::JSONB,
    'channel:system-events'
FROM effects
WHERE effect_name = 'channel-subscription';

INSERT INTO effect_dependencies (
    effect_id,
    position,
    dependency_name,
    dependency_value,
    dependency_token
)
SELECT
    effect_id,
    0,
    'severity',
    '"critical"'::JSONB,
    'severity:critical'
FROM effects
WHERE effect_name = 'security-event-listener';

INSERT INTO effect_dependencies (
    effect_id,
    position,
    dependency_name,
    dependency_value,
    dependency_token
)
SELECT
    effect_id,
    0,
    'query',
    '"useEffect"'::JSONB,
    'query:useEffect'
FROM effects
WHERE effect_name = 'search-request';

-- Create commits.
SELECT create_render(component_id)
FROM components
WHERE component_name = 'AnalyticsDashboard';

SELECT create_render(component_id)
FROM components
WHERE component_name = 'AnalyticsDashboard';

SELECT create_render(component_id)
FROM components
WHERE component_name = 'SecurityMonitor';

SELECT create_render(component_id)
FROM components
WHERE component_name = 'SearchPanel';

-- Create effect executions.
INSERT INTO effect_executions (
    effect_id,
    render_id,
    execution_type,
    status,
    cleanup_state,
    finished_at
)
SELECT
    e.effect_id,
    r.render_id,
    'setup',
    'succeeded',
    'pending',
    CURRENT_TIMESTAMP
FROM effects e
JOIN renders r
    ON r.component_id = e.component_id
WHERE e.effect_name = 'channel-subscription'
  AND r.commit_number = 1;

INSERT INTO effect_executions (
    effect_id,
    render_id,
    execution_type,
    status,
    cleanup_state,
    finished_at
)
SELECT
    e.effect_id,
    r.render_id,
    'setup',
    'succeeded',
    'not_required',
    CURRENT_TIMESTAMP
FROM effects e
JOIN renders r
    ON r.component_id = e.component_id
WHERE e.effect_name = 'initialization'
  AND r.commit_number = 1;

-- A failed asynchronous request.
INSERT INTO effect_executions (
    effect_id,
    render_id,
    execution_type,
    status,
    cleanup_state,
    finished_at,
    error_message
)
SELECT
    e.effect_id,
    r.render_id,
    'setup',
    'failed',
    'pending',
    CURRENT_TIMESTAMP,
    'Request timed out'
FROM effects e
JOIN renders r
    ON r.component_id = e.component_id
WHERE e.effect_name = 'search-request';

-- Record the dependency snapshot.
INSERT INTO execution_dependencies (
    execution_id,
    position,
    dependency_name,
    dependency_value,
    dependency_token
)
SELECT
    x.execution_id,
    d.position,
    d.dependency_name,
    d.dependency_value,
    d.dependency_token
FROM effect_executions x
JOIN effects e
    ON e.effect_id = x.effect_id
JOIN effect_dependencies d
    ON d.effect_id = e.effect_id
WHERE e.effect_name = 'channel-subscription';

-- Register a resource owned by the successful subscription.
INSERT INTO managed_resources (
    component_id,
    effect_id,
    execution_id,
    resource_key
)
SELECT
    c.component_id,
    e.effect_id,
    x.execution_id,
    'system-events'
FROM components c
JOIN effects e
    ON e.component_id = c.component_id
JOIN effect_executions x
    ON x.effect_id = e.effect_id
WHERE c.component_name = 'AnalyticsDashboard'
  AND e.effect_name = 'channel-subscription'
  AND x.status = 'succeeded';

-- ============================================================
-- 20. RETRIEVAL AND VALIDATION QUERIES
-- ============================================================

-- Retrieve component and effect configuration.
SELECT
    c.component_name,
    c.status,
    e.effect_name,
    e.mode,
    e.requires_cleanup
FROM components c
JOIN effects e
    ON e.component_id = c.component_id
ORDER BY c.component_name, e.effect_name;

-- Retrieve dependencies in array order.
SELECT
    e.effect_name,
    d.position,
    d.dependency_name,
    d.dependency_value,
    d.dependency_token
FROM effects e
JOIN effect_dependencies d
    ON d.effect_id = e.effect_id
ORDER BY e.effect_id, d.position;

-- Identify failed executions.
SELECT
    e.effect_name,
    x.execution_id,
    x.error_message,
    x.started_at
FROM effect_executions x
JOIN effects e
    ON e.effect_id = x.effect_id
WHERE x.status = 'failed';

-- Identify active resources.
SELECT
    c.component_name,
    e.effect_name,
    r.resource_key,
    r.acquired_at
FROM managed_resources r
JOIN components c
    ON c.component_id = r.component_id
JOIN effects e
    ON e.effect_id = r.effect_id
WHERE r.status = 'active';

-- Identify cleanup failures or pending cleanup.
SELECT
    execution_id,
    status,
    error_message
FROM cleanup_operations
WHERE status IN ('pending', 'failed');

-- Aggregate execution reliability.
SELECT
    e.effect_name,
    COUNT(x.execution_id) AS total_executions,
    COUNT(*) FILTER (
        WHERE x.status = 'succeeded'
    ) AS successful_executions,
    COUNT(*) FILTER (
        WHERE x.status = 'failed'
    ) AS failed_executions
FROM effects e
LEFT JOIN effect_executions x
    ON x.effect_id = e.effect_id
GROUP BY e.effect_name
ORDER BY e.effect_name;

-- Full lifecycle report.
SELECT *
FROM effect_lifecycle_report
ORDER BY component_name, effect_name;

-- ============================================================
-- 21. CTE: DETECT RESOURCE LEAKS
-- ============================================================

WITH resource_audit AS (
    SELECT
        c.component_name,
        c.status AS component_status,
        COUNT(r.resource_id) FILTER (
            WHERE r.status = 'active'
        ) AS active_resources,
        COUNT(r.resource_id) FILTER (
            WHERE r.status = 'released'
        ) AS released_resources
    FROM components c
    LEFT JOIN managed_resources r
        ON r.component_id = c.component_id
    GROUP BY c.component_id
)
SELECT *
FROM resource_audit
WHERE (
    component_status = 'unmounted'
    AND active_resources > 0
)
OR (
    component_status = 'mounted'
    AND active_resources >= 0
);

-- ============================================================
-- 22. TRANSACTIONAL CLEANUP DEMONSTRATION
-- ============================================================

BEGIN;

DO $$
DECLARE
    target_resource BIGINT;
BEGIN
    SELECT resource_id
    INTO target_resource
    FROM managed_resources
    WHERE resource_key = 'system-events'
      AND status = 'active'
    FOR UPDATE;

    IF target_resource IS NOT NULL THEN
        CALL release_resource(target_resource);
    END IF;
END;
$$;

COMMIT;

-- Verify cleanup.
SELECT
    resource_key,
    status,
    acquired_at,
    released_at
FROM managed_resources
ORDER BY resource_id;

-- ============================================================
-- 23. UNMOUNT A COMPONENT
-- ============================================================

BEGIN;

CALL unmount_component(
    (
        SELECT component_id
        FROM components
        WHERE component_name = 'SecurityMonitor'
    )
);

COMMIT;

-- ============================================================
-- 24. FINAL STATE VALIDATION
-- ============================================================

-- Unmounted components must not retain active resources.
SELECT
    c.component_name,
    r.resource_key
FROM components c
JOIN managed_resources r
    ON r.component_id = c.component_id
WHERE c.status = 'unmounted'
  AND r.status = 'active';

-- Execution health.
SELECT
    component_name,
    effect_name,
    execution_count,
    failed_executions,
    completed_cleanups,
    last_execution
FROM effect_lifecycle_report
ORDER BY component_name, effect_name;

-- Component state.
SELECT
    component_name,
    status,
    created_at,
    unmounted_at
FROM components
ORDER BY component_id;

COMMIT;
