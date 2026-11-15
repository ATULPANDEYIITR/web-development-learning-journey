/*
 * React Hooks: PostgreSQL Hook Execution and Performance Registry.
 *
 * This database models observable hook usage within a React
 * application. It is an observability and governance data model,
 * not an implementation of React's in-memory hook dispatcher.
 *
 * Tracks:
 * - Applications and components.
 * - Hook definitions and hook categories.
 * - Custom hook composition.
 * - Component render sessions.
 * - Hook execution sequences.
 * - Dependency snapshots.
 * - Memoization cache hits and misses.
 * - Callback recreation.
 * - Mutable reference operations.
 * - State updates.
 * - Performance measurements.
 * - Hook lifecycle violations.
 * - Aggregated performance reporting.
 *
 * PostgreSQL 14+
 */

BEGIN;

CREATE SCHEMA IF NOT EXISTS react_observability;

SET search_path TO react_observability, public;


-- =========================================================
-- 1. ENUM TYPES
-- =========================================================

CREATE TYPE hook_category AS ENUM (
    'useRef',
    'useMemo',
    'useCallback',
    'useState',
    'custom'
);

CREATE TYPE execution_outcome AS ENUM (
    'success',
    'cache_hit',
    'cache_miss',
    'error',
    'skipped'
);

CREATE TYPE render_status AS ENUM (
    'started',
    'completed',
    'failed',
    'cancelled'
);

CREATE TYPE violation_severity AS ENUM (
    'low',
    'medium',
    'high',
    'critical'
);


-- =========================================================
-- 2. APPLICATIONS
-- =========================================================

CREATE TABLE applications (
    application_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    application_name VARCHAR(150) NOT NULL UNIQUE,
    environment VARCHAR(30) NOT NULL
        CHECK (
            environment IN (
                'development',
                'testing',
                'staging',
                'production'
            )
        ),
    application_version VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- =========================================================
-- 3. COMPONENTS
-- =========================================================

CREATE TABLE components (
    component_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    application_id BIGINT NOT NULL
        REFERENCES applications(application_id)
        ON DELETE CASCADE,

    component_name VARCHAR(200) NOT NULL,

    source_path TEXT NOT NULL,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (application_id, component_name)
);


-- =========================================================
-- 4. HOOK DEFINITIONS
-- =========================================================

CREATE TABLE hook_definitions (
    hook_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    component_id BIGINT NOT NULL
        REFERENCES components(component_id)
        ON DELETE CASCADE,

    hook_name VARCHAR(200) NOT NULL,

    category hook_category NOT NULL,

    description TEXT,

    expected_dependency_count INTEGER
        CHECK (
            expected_dependency_count IS NULL
            OR expected_dependency_count >= 0
        ),

    is_custom BOOLEAN GENERATED ALWAYS AS (
        category = 'custom'
    ) STORED,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (component_id, hook_name)
);


-- =========================================================
-- 5. CUSTOM HOOK COMPOSITION
-- =========================================================

CREATE TABLE custom_hook_composition (
    parent_hook_id BIGINT NOT NULL
        REFERENCES hook_definitions(hook_id)
        ON DELETE CASCADE,

    child_hook_id BIGINT NOT NULL
        REFERENCES hook_definitions(hook_id)
        ON DELETE RESTRICT,

    composition_order INTEGER NOT NULL
        CHECK (composition_order > 0),

    PRIMARY KEY (parent_hook_id, composition_order),

    UNIQUE (parent_hook_id, child_hook_id),

    CHECK (parent_hook_id <> child_hook_id)
);


-- =========================================================
-- 6. RENDER SESSIONS
-- =========================================================

CREATE TABLE render_sessions (
    render_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    component_id BIGINT NOT NULL
        REFERENCES components(component_id)
        ON DELETE CASCADE,

    render_sequence BIGINT NOT NULL
        CHECK (render_sequence > 0),

    status render_status NOT NULL DEFAULT 'started',

    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    completed_at TIMESTAMPTZ,

    duration_ms NUMERIC(12, 3)
        CHECK (
            duration_ms IS NULL OR duration_ms >= 0
        ),

    trigger_reason VARCHAR(100) NOT NULL,

    props_fingerprint VARCHAR(128),

    error_message TEXT,

    UNIQUE (component_id, render_sequence),

    CHECK (
        completed_at IS NULL
        OR completed_at >= started_at
    ),

    CHECK (
        status <> 'completed'
        OR (
            completed_at IS NOT NULL
            AND duration_ms IS NOT NULL
        )
    )
);


-- =========================================================
-- 7. HOOK EXECUTIONS
-- =========================================================

CREATE TABLE hook_executions (
    execution_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    render_id BIGINT NOT NULL
        REFERENCES render_sessions(render_id)
        ON DELETE CASCADE,

    hook_id BIGINT NOT NULL
        REFERENCES hook_definitions(hook_id)
        ON DELETE RESTRICT,

    execution_order INTEGER NOT NULL
        CHECK (execution_order > 0),

    outcome execution_outcome NOT NULL,

    execution_duration_us NUMERIC(14, 3)
        CHECK (
            execution_duration_us IS NULL
            OR execution_duration_us >= 0
        ),

    dependency_count INTEGER NOT NULL DEFAULT 0
        CHECK (dependency_count >= 0),

    cache_reused BOOLEAN NOT NULL DEFAULT FALSE,

    error_message TEXT,

    UNIQUE (render_id, execution_order),

    CHECK (
        NOT cache_reused
        OR outcome = 'cache_hit'
    )
);


-- =========================================================
-- 8. DEPENDENCY SNAPSHOTS
-- =========================================================

CREATE TABLE dependency_snapshots (
    snapshot_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    execution_id BIGINT NOT NULL
        REFERENCES hook_executions(execution_id)
        ON DELETE CASCADE,

    dependency_position INTEGER NOT NULL
        CHECK (dependency_position >= 0),

    dependency_type VARCHAR(40) NOT NULL,

    dependency_fingerprint VARCHAR(128) NOT NULL,

    is_mutable_reference BOOLEAN NOT NULL DEFAULT FALSE,

    captured_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (execution_id, dependency_position)
);


-- =========================================================
-- 9. REFERENCE OPERATIONS
-- =========================================================

CREATE TABLE reference_operations (
    reference_operation_id BIGINT
        GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    execution_id BIGINT NOT NULL
        REFERENCES hook_executions(execution_id)
        ON DELETE CASCADE,

    reference_key VARCHAR(200) NOT NULL,

    operation VARCHAR(20) NOT NULL
        CHECK (
            operation IN (
                'initialize',
                'read',
                'mutate'
            )
        ),

    mutation_fingerprint VARCHAR(128),

    operation_time TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- =========================================================
-- 10. STATE UPDATE EVENTS
-- =========================================================

CREATE TABLE state_update_events (
    state_event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    execution_id BIGINT NOT NULL
        REFERENCES hook_executions(execution_id)
        ON DELETE CASCADE,

    state_key VARCHAR(200) NOT NULL,

    previous_fingerprint VARCHAR(128),

    next_fingerprint VARCHAR(128) NOT NULL,

    update_origin VARCHAR(50) NOT NULL
        CHECK (
            update_origin IN (
                'direct',
                'functional',
                'external'
            )
        ),

    update_time TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- =========================================================
-- 11. LIFECYCLE VIOLATIONS
-- =========================================================

CREATE TABLE hook_violations (
    violation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    render_id BIGINT NOT NULL
        REFERENCES render_sessions(render_id)
        ON DELETE CASCADE,

    hook_id BIGINT
        REFERENCES hook_definitions(hook_id)
        ON DELETE SET NULL,

    severity violation_severity NOT NULL,

    violation_code VARCHAR(80) NOT NULL,

    description TEXT NOT NULL,

    resolved BOOLEAN NOT NULL DEFAULT FALSE,

    detected_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    resolved_at TIMESTAMPTZ,

    CHECK (
        (NOT resolved AND resolved_at IS NULL)
        OR
        (resolved AND resolved_at IS NOT NULL)
    )
);


-- =========================================================
-- 12. INDEXES
-- =========================================================

CREATE INDEX idx_components_application
    ON components(application_id, is_active);

CREATE INDEX idx_hooks_component_category
    ON hook_definitions(component_id, category);

CREATE INDEX idx_renders_component_time
    ON render_sessions(component_id, started_at DESC);

CREATE INDEX idx_renders_status
    ON render_sessions(status, started_at DESC);

CREATE INDEX idx_executions_render_order
    ON hook_executions(render_id, execution_order);

CREATE INDEX idx_executions_hook_outcome
    ON hook_executions(hook_id, outcome);

CREATE INDEX idx_dependencies_execution
    ON dependency_snapshots(execution_id);

CREATE INDEX idx_violations_unresolved
    ON hook_violations(severity, detected_at DESC)
    WHERE resolved = FALSE;

CREATE INDEX idx_state_events_key_time
    ON state_update_events(state_key, update_time DESC);


-- =========================================================
-- 13. AUDIT TRIGGER
-- =========================================================

CREATE OR REPLACE FUNCTION validate_render_completion()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.status = 'completed' THEN

        IF NEW.completed_at IS NULL THEN
            RAISE EXCEPTION
                'Completed render requires completed_at';
        END IF;

        IF NEW.duration_ms IS NULL THEN
            RAISE EXCEPTION
                'Completed render requires duration_ms';
        END IF;

        IF NEW.completed_at < NEW.started_at THEN
            RAISE EXCEPTION
                'Completion cannot precede render start';
        END IF;

    END IF;

    IF NEW.status = 'failed'
       AND NEW.error_message IS NULL THEN
        RAISE EXCEPTION
            'Failed render requires an error message';
    END IF;

    RETURN NEW;
END;
$$;


CREATE TRIGGER trg_validate_render_completion
BEFORE INSERT OR UPDATE ON render_sessions
FOR EACH ROW
EXECUTE FUNCTION validate_render_completion();


-- =========================================================
-- 14. HOOK EXECUTION VALIDATION
-- =========================================================

CREATE OR REPLACE FUNCTION validate_hook_execution()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    expected_count INTEGER;
    actual_count INTEGER;
    expected_category hook_category;
    render_state render_status;
BEGIN
    SELECT status
    INTO render_state
    FROM render_sessions
    WHERE render_id = NEW.render_id;

    IF render_state <> 'started' THEN
        RAISE EXCEPTION
            'Hooks can only execute during a started render';
    END IF;

    SELECT
        expected_dependency_count,
        category
    INTO
        expected_count,
        expected_category
    FROM hook_definitions
    WHERE hook_id = NEW.hook_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Unknown hook definition';
    END IF;

    IF expected_count IS NOT NULL
       AND expected_count <> NEW.dependency_count THEN
        RAISE EXCEPTION
            'Dependency count mismatch: expected %, received %',
            expected_count,
            NEW.dependency_count;
    END IF;

    IF NEW.cache_reused
       AND expected_category NOT IN ('useMemo', 'useCallback') THEN
        RAISE EXCEPTION
            'Only memo and callback hooks can report cache reuse';
    END IF;

    SELECT COUNT(*)
    INTO actual_count
    FROM hook_executions
    WHERE render_id = NEW.render_id
      AND execution_order = NEW.execution_order;

    IF actual_count > 0 THEN
        RAISE EXCEPTION 'Duplicate hook execution order';
    END IF;

    RETURN NEW;
END;
$$;


CREATE TRIGGER trg_validate_hook_execution
BEFORE INSERT ON hook_executions
FOR EACH ROW
EXECUTE FUNCTION validate_hook_execution();


-- =========================================================
-- 15. DEPENDENCY SNAPSHOT VALIDATION
-- =========================================================

CREATE OR REPLACE FUNCTION validate_dependency_snapshot()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    expected_count INTEGER;
BEGIN
    SELECT dependency_count
    INTO expected_count
    FROM hook_executions
    WHERE execution_id = NEW.execution_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Unknown hook execution';
    END IF;

    IF NEW.dependency_position >= expected_count THEN
        RAISE EXCEPTION
            'Dependency position exceeds declared dependency count';
    END IF;

    RETURN NEW;
END;
$$;


CREATE TRIGGER trg_validate_dependency_snapshot
BEFORE INSERT ON dependency_snapshots
FOR EACH ROW
EXECUTE FUNCTION validate_dependency_snapshot();


-- =========================================================
-- 16. REPORTING VIEW: COMPONENT RENDER PERFORMANCE
-- =========================================================

CREATE OR REPLACE VIEW component_render_performance AS
SELECT
    c.component_id,
    c.component_name,
    a.application_name,
    a.environment,

    COUNT(r.render_id) AS total_renders,

    COUNT(*) FILTER (
        WHERE r.status = 'completed'
    ) AS successful_renders,

    COUNT(*) FILTER (
        WHERE r.status = 'failed'
    ) AS failed_renders,

    ROUND(
        AVG(r.duration_ms) FILTER (
            WHERE r.status = 'completed'
        ),
        3
    ) AS average_render_ms,

    ROUND(
        MAX(r.duration_ms),
        3
    ) AS maximum_render_ms

FROM components c

JOIN applications a
    ON a.application_id = c.application_id

LEFT JOIN render_sessions r
    ON r.component_id = c.component_id

GROUP BY
    c.component_id,
    c.component_name,
    a.application_name,
    a.environment;


-- =========================================================
-- 17. REPORTING VIEW: HOOK CACHE EFFECTIVENESS
-- =========================================================

CREATE OR REPLACE VIEW hook_cache_performance AS
SELECT
    h.hook_id,
    h.hook_name,
    h.category,
    c.component_name,

    COUNT(e.execution_id) AS executions,

    COUNT(*) FILTER (
        WHERE e.outcome = 'cache_hit'
    ) AS cache_hits,

    COUNT(*) FILTER (
        WHERE e.outcome = 'cache_miss'
    ) AS cache_misses,

    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE e.outcome = 'cache_hit'
        ) / NULLIF(
            COUNT(*) FILTER (
                WHERE e.outcome IN ('cache_hit', 'cache_miss')
            ),
            0
        ),
        2
    ) AS cache_hit_percentage,

    ROUND(
        AVG(e.execution_duration_us),
        3
    ) AS average_execution_us

FROM hook_definitions h

JOIN components c
    ON c.component_id = h.component_id

LEFT JOIN hook_executions e
    ON e.hook_id = h.hook_id

GROUP BY
    h.hook_id,
    h.hook_name,
    h.category,
    c.component_name;


-- =========================================================
-- 18. FUNCTION: CHECK COMPONENT HOOK ORDER
-- =========================================================

CREATE OR REPLACE FUNCTION validate_component_hook_order(
    p_render_id BIGINT
)
RETURNS TABLE (
    render_id BIGINT,
    expected_executions BIGINT,
    actual_executions BIGINT,
    ordering_valid BOOLEAN
)
LANGUAGE sql
STABLE
AS $$
    SELECT
        p_render_id,

        COUNT(*)::BIGINT,

        COUNT(*) FILTER (
            WHERE execution_order > 0
        )::BIGINT,

        COUNT(*) = COUNT(*) FILTER (
            WHERE execution_order > 0
        )

    FROM hook_executions

    WHERE hook_executions.render_id = p_render_id;
$$;


-- =========================================================
-- 19. FUNCTION: COMPONENT CACHE REPORT
-- =========================================================

CREATE OR REPLACE FUNCTION component_cache_report(
    p_component_id BIGINT
)
RETURNS TABLE (
    hook_name VARCHAR,
    category hook_category,
    executions BIGINT,
    hits BIGINT,
    misses BIGINT
)
LANGUAGE sql
STABLE
AS $$
    SELECT
        h.hook_name,
        h.category,

        COUNT(e.execution_id),

        COUNT(*) FILTER (
            WHERE e.outcome = 'cache_hit'
        ),

        COUNT(*) FILTER (
            WHERE e.outcome = 'cache_miss'
        )

    FROM hook_definitions h

    LEFT JOIN hook_executions e
        ON e.hook_id = h.hook_id

    LEFT JOIN render_sessions r
        ON r.render_id = e.render_id

    WHERE h.component_id = p_component_id

    GROUP BY
        h.hook_name,
        h.category

    ORDER BY h.hook_name;
$$;


-- =========================================================
-- 20. PROCEDURE: COMPLETE A RENDER
-- =========================================================

CREATE OR REPLACE PROCEDURE complete_render(
    p_render_id BIGINT,
    p_duration_ms NUMERIC
)
LANGUAGE plpgsql
AS $$
DECLARE
    current_status render_status;
BEGIN
    IF p_duration_ms IS NULL OR p_duration_ms < 0 THEN
        RAISE EXCEPTION 'Duration must be non-negative';
    END IF;

    SELECT status
    INTO current_status
    FROM render_sessions
    WHERE render_id = p_render_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Render session does not exist';
    END IF;

    IF current_status <> 'started' THEN
        RAISE EXCEPTION
            'Only started renders can be completed';
    END IF;

    UPDATE render_sessions
    SET
        status = 'completed',
        completed_at = CURRENT_TIMESTAMP,
        duration_ms = p_duration_ms
    WHERE render_id = p_render_id;

END;
$$;


-- =========================================================
-- 21. SAMPLE APPLICATION DATA
-- =========================================================

INSERT INTO applications (
    application_name,
    environment,
    application_version
)
VALUES (
    'Repository Management Platform',
    'development',
    '2.4.0'
);


INSERT INTO components (
    application_id,
    component_name,
    source_path
)
SELECT
    application_id,
    'RepositoryDashboard',
    'src/components/RepositoryDashboard.js'
FROM applications
WHERE application_name = 'Repository Management Platform';


INSERT INTO hook_definitions (
    component_id,
    hook_name,
    category,
    description,
    expected_dependency_count
)
SELECT
    component_id,
    'repositoryCounter',
    'useState',
    'Maintains the current repository interaction count.',
    0
FROM components
WHERE component_name = 'RepositoryDashboard';


INSERT INTO hook_definitions (
    component_id,
    hook_name,
    category,
    description,
    expected_dependency_count
)
SELECT
    component_id,
    'searchInputRef',
    'useRef',
    'Maintains a persistent DOM reference.',
    0
FROM components
WHERE component_name = 'RepositoryDashboard';


INSERT INTO hook_definitions (
    component_id,
    hook_name,
    category,
    description,
    expected_dependency_count
)
SELECT
    component_id,
    'filteredRepositories',
    'useMemo',
    'Caches filtered repository records.',
    2
FROM components
WHERE component_name = 'RepositoryDashboard';


INSERT INTO hook_definitions (
    component_id,
    hook_name,
    category,
    description,
    expected_dependency_count
)
SELECT
    component_id,
    'selectRepository',
    'useCallback',
    'Caches repository selection handler.',
    1
FROM components
WHERE component_name = 'RepositoryDashboard';


INSERT INTO hook_definitions (
    component_id,
    hook_name,
    category,
    description,
    expected_dependency_count
)
SELECT
    component_id,
    'useRepositoryMetrics',
    'custom',
    'Combines reference and memoization logic.',
    NULL
FROM components
WHERE component_name = 'RepositoryDashboard';


-- =========================================================
-- 22. SAMPLE CUSTOM HOOK COMPOSITION
-- =========================================================

INSERT INTO custom_hook_composition (
    parent_hook_id,
    child_hook_id,
    composition_order
)
SELECT
    parent.hook_id,
    child.hook_id,
    1
FROM hook_definitions parent
JOIN hook_definitions child
    ON child.component_id = parent.component_id
WHERE parent.hook_name = 'useRepositoryMetrics'
  AND child.hook_name = 'searchInputRef';


INSERT INTO custom_hook_composition (
    parent_hook_id,
    child_hook_id,
    composition_order
)
SELECT
    parent.hook_id,
    child.hook_id,
    2
FROM hook_definitions parent
JOIN hook_definitions child
    ON child.component_id = parent.component_id
WHERE parent.hook_name = 'useRepositoryMetrics'
  AND child.hook_name = 'filteredRepositories';


-- =========================================================
-- 23. SAMPLE RENDER SESSIONS
-- =========================================================

INSERT INTO render_sessions (
    component_id,
    render_sequence,
    status,
    trigger_reason,
    props_fingerprint
)
SELECT
    component_id,
    1,
    'started',
    'initial_mount',
    'props-initial-001'
FROM components
WHERE component_name = 'RepositoryDashboard';


INSERT INTO render_sessions (
    component_id,
    render_sequence,
    status,
    trigger_reason,
    props_fingerprint
)
SELECT
    component_id,
    2,
    'started',
    'state_update',
    'props-initial-001'
FROM components
WHERE component_name = 'RepositoryDashboard';


INSERT INTO render_sessions (
    component_id,
    render_sequence,
    status,
    trigger_reason,
    props_fingerprint
)
SELECT
    component_id,
    3,
    'started',
    'props_update',
    'props-updated-002'
FROM components
WHERE component_name = 'RepositoryDashboard';


-- =========================================================
-- 24. SAMPLE HOOK EXECUTIONS
-- =========================================================

-- Render 1: initial computation.

INSERT INTO hook_executions (
    render_id,
    hook_id,
    execution_order,
    outcome,
    execution_duration_us,
    dependency_count,
    cache_reused
)
SELECT
    r.render_id,
    h.hook_id,
    1,
    'success',
    3.5,
    0,
    FALSE
FROM render_sessions r
JOIN components c
    ON c.component_id = r.component_id
JOIN hook_definitions h
    ON h.component_id = c.component_id
WHERE r.render_sequence = 1
  AND h.hook_name = 'repositoryCounter';


INSERT INTO hook_executions (
    render_id,
    hook_id,
    execution_order,
    outcome,
    execution_duration_us,
    dependency_count,
    cache_reused
)
SELECT
    r.render_id,
    h.hook_id,
    2,
    'success',
    1.2,
    0,
    FALSE
FROM render_sessions r
JOIN components c
    ON c.component_id = r.component_id
JOIN hook_definitions h
    ON h.component_id = c.component_id
WHERE r.render_sequence = 1
  AND h.hook_name = 'searchInputRef';


INSERT INTO hook_executions (
    render_id,
    hook_id,
    execution_order,
    outcome,
    execution_duration_us,
    dependency_count,
    cache_reused
)
SELECT
    r.render_id,
    h.hook_id,
    3,
    'cache_miss',
    120.5,
    2,
    FALSE
FROM render_sessions r
JOIN components c
    ON c.component_id = r.component_id
JOIN hook_definitions h
    ON h.component_id = c.component_id
WHERE r.render_sequence = 1
  AND h.hook_name = 'filteredRepositories';


INSERT INTO hook_executions (
    render_id,
    hook_id,
    execution_order,
    outcome,
    execution_duration_us,
    dependency_count,
    cache_reused
)
SELECT
    r.render_id,
    h.hook_id,
    4,
    'cache_miss',
    5.2,
    1,
    FALSE
FROM render_sessions r
JOIN components c
    ON c.component_id = r.component_id
JOIN hook_definitions h
    ON h.component_id = c.component_id
WHERE r.render_sequence = 1
  AND h.hook_name = 'selectRepository';


-- Render 2: unchanged dependencies.

INSERT INTO hook_executions (
    render_id,
    hook_id,
    execution_order,
    outcome,
    execution_duration_us,
    dependency_count,
    cache_reused
)
SELECT
    r.render_id,
    h.hook_id,
    CASE h.hook_name
        WHEN 'repositoryCounter' THEN 1
        WHEN 'searchInputRef' THEN 2
        WHEN 'filteredRepositories' THEN 3
        WHEN 'selectRepository' THEN 4
    END,
    CASE h.hook_name
        WHEN 'filteredRepositories' THEN 'cache_hit'
        WHEN 'selectRepository' THEN 'cache_hit'
        ELSE 'success'
    END,
    1.5,
    h.expected_dependency_count,
    h.category IN ('useMemo', 'useCallback')
FROM render_sessions r
JOIN components c
    ON c.component_id = r.component_id
JOIN hook_definitions h
    ON h.component_id = c.component_id
WHERE r.render_sequence = 2
  AND h.hook_name IN (
      'repositoryCounter',
      'searchInputRef',
      'filteredRepositories',
      'selectRepository'
  );


-- Render 3: changed dependencies.

INSERT INTO hook_executions (
    render_id,
    hook_id,
    execution_order,
    outcome,
    execution_duration_us,
    dependency_count,
    cache_reused
)
SELECT
    r.render_id,
    h.hook_id,
    CASE h.hook_name
        WHEN 'repositoryCounter' THEN 1
        WHEN 'searchInputRef' THEN 2
        WHEN 'filteredRepositories' THEN 3
        WHEN 'selectRepository' THEN 4
    END,
    CASE h.hook_name
        WHEN 'filteredRepositories' THEN 'cache_miss'
        WHEN 'selectRepository' THEN 'cache_miss'
        ELSE 'success'
    END,
    CASE h.hook_name
        WHEN 'filteredRepositories' THEN 135.2
        ELSE 2.0
    END,
    h.expected_dependency_count,
    FALSE
FROM render_sessions r
JOIN components c
    ON c.component_id = r.component_id
JOIN hook_definitions h
    ON h.component_id = c.component_id
WHERE r.render_sequence = 3
  AND h.hook_name IN (
      'repositoryCounter',
      'searchInputRef',
      'filteredRepositories',
      'selectRepository'
  );


-- =========================================================
-- 25. SAMPLE DEPENDENCY SNAPSHOTS
-- =========================================================

INSERT INTO dependency_snapshots (
    execution_id,
    dependency_position,
    dependency_type,
    dependency_fingerprint
)
SELECT
    e.execution_id,
    0,
    'object',
    'repository-array-v1'
FROM hook_executions e
JOIN hook_definitions h
    ON h.hook_id = e.hook_id
JOIN render_sessions r
    ON r.render_id = e.render_id
WHERE h.hook_name = 'filteredRepositories'
  AND r.render_sequence = 1;


INSERT INTO dependency_snapshots (
    execution_id,
    dependency_position,
    dependency_type,
    dependency_fingerprint
)
SELECT
    e.execution_id,
    1,
    'number',
    '70'
FROM hook_executions e
JOIN hook_definitions h
    ON h.hook_id = e.hook_id
JOIN render_sessions r
    ON r.render_id = e.render_id
WHERE h.hook_name = 'filteredRepositories'
  AND r.render_sequence = 1;


-- =========================================================
-- 26. SAMPLE REFERENCE OPERATIONS
-- =========================================================

INSERT INTO reference_operations (
    execution_id,
    reference_key,
    operation,
    mutation_fingerprint
)
SELECT
    e.execution_id,
    'searchInputRef',
    'initialize',
    NULL
FROM hook_executions e
JOIN hook_definitions h
    ON h.hook_id = e.hook_id
WHERE h.hook_name = 'searchInputRef'
  AND e.render_id = (
      SELECT render_id
      FROM render_sessions
      WHERE render_sequence = 1
  );


INSERT INTO reference_operations (
    execution_id,
    reference_key,
    operation,
    mutation_fingerprint
)
SELECT
    e.execution_id,
    'searchInputRef',
    'read',
    NULL
FROM hook_executions e
JOIN hook_definitions h
    ON h.hook_id = e.hook_id
WHERE h.hook_name = 'searchInputRef'
  AND e.render_id = (
      SELECT render_id
      FROM render_sessions
      WHERE render_sequence = 2
  );


-- =========================================================
-- 27. SAMPLE STATE UPDATES
-- =========================================================

INSERT INTO state_update_events (
    execution_id,
    state_key,
    previous_fingerprint,
    next_fingerprint,
    update_origin
)
SELECT
    e.execution_id,
    'repositoryCounter',
    '0',
    '1',
    'functional'
FROM hook_executions e
JOIN hook_definitions h
    ON h.hook_id = e.hook_id
WHERE h.hook_name = 'repositoryCounter'
  AND e.render_id = (
      SELECT render_id
      FROM render_sessions
      WHERE render_sequence = 2
  );


-- =========================================================
-- 28. SAMPLE FAILURE CASE
-- =========================================================

INSERT INTO render_sessions (
    component_id,
    render_sequence,
    status,
    trigger_reason,
    error_message
)
SELECT
    component_id,
    4,
    'failed',
    'invalid_hook_order',
    'Hook sequence changed between renders.'
FROM components
WHERE component_name = 'RepositoryDashboard';


INSERT INTO hook_violations (
    render_id,
    severity,
    violation_code,
    description
)
SELECT
    render_id,
    'high',
    'HOOK_ORDER_CHANGED',
    'A hook was conditionally skipped, changing the hook sequence.'
FROM render_sessions
WHERE render_sequence = 4;


-- =========================================================
-- 29. COMPLETE VALID RENDERS
-- =========================================================

CALL complete_render(
    (
        SELECT render_id
        FROM render_sessions
        WHERE render_sequence = 1
    ),
    2.8
);

CALL complete_render(
    (
        SELECT render_id
        FROM render_sessions
        WHERE render_sequence = 2
    ),
    1.7
);

CALL complete_render(
    (
        SELECT render_id
        FROM render_sessions
        WHERE render_sequence = 3
    ),
    3.1
);


-- =========================================================
-- 30. RETRIEVAL QUERIES
-- =========================================================

-- Applications and their components.

SELECT
    a.application_name,
    a.environment,
    c.component_name,
    c.source_path
FROM applications a
JOIN components c
    ON c.application_id = a.application_id
ORDER BY c.component_name;


-- Hook definitions and categories.

SELECT
    c.component_name,
    h.hook_name,
    h.category,
    h.expected_dependency_count
FROM hook_definitions h
JOIN components c
    ON c.component_id = h.component_id
ORDER BY h.hook_id;


-- Hook executions for each render.

SELECT
    r.render_sequence,
    h.hook_name,
    h.category,
    e.execution_order,
    e.outcome,
    e.cache_reused
FROM hook_executions e
JOIN render_sessions r
    ON r.render_id = e.render_id
JOIN hook_definitions h
    ON h.hook_id = e.hook_id
ORDER BY r.render_sequence, e.execution_order;


-- =========================================================
-- 31. VALIDATION QUERIES
-- =========================================================

-- Detect renders with duplicate or missing execution positions.

SELECT
    render_id,
    COUNT(*) AS execution_count,
    MIN(execution_order) AS first_position,
    MAX(execution_order) AS last_position,
    COUNT(DISTINCT execution_order) AS unique_positions
FROM hook_executions
GROUP BY render_id
HAVING COUNT(*) <> COUNT(DISTINCT execution_order);


-- Detect unresolved high-severity violations.

SELECT
    violation_id,
    violation_code,
    severity,
    description,
    detected_at
FROM hook_violations
WHERE resolved = FALSE
  AND severity IN ('high', 'critical')
ORDER BY detected_at DESC;


-- Validate declared dependency counts.

SELECT
    e.execution_id,
    h.hook_name,
    e.dependency_count,
    COUNT(d.snapshot_id) AS recorded_dependencies
FROM hook_executions e
JOIN hook_definitions h
    ON h.hook_id = e.hook_id
LEFT JOIN dependency_snapshots d
    ON d.execution_id = e.execution_id
GROUP BY
    e.execution_id,
    h.hook_name,
    e.dependency_count
HAVING COUNT(d.snapshot_id) <> e.dependency_count;


-- =========================================================
-- 32. AGGREGATION AND EVALUATION
-- =========================================================

SELECT *
FROM component_render_performance;


SELECT *
FROM hook_cache_performance
ORDER BY cache_hit_percentage DESC NULLS LAST;


-- Compare memo and callback behavior.

SELECT
    h.category,
    COUNT(*) AS total_executions,

    COUNT(*) FILTER (
        WHERE e.outcome = 'cache_hit'
    ) AS cache_hits,

    COUNT(*) FILTER (
        WHERE e.outcome = 'cache_miss'
    ) AS cache_misses,

    ROUND(
        AVG(e.execution_duration_us),
        3
    ) AS average_duration_us

FROM hook_executions e
JOIN hook_definitions h
    ON h.hook_id = e.hook_id

WHERE h.category IN ('useMemo', 'useCallback')

GROUP BY h.category;


-- =========================================================
-- 33. CTE: RENDER PERFORMANCE RANKING
-- =========================================================

WITH render_metrics AS (
    SELECT
        component_id,
        render_id,
        render_sequence,
        duration_ms,

        AVG(duration_ms) OVER (
            PARTITION BY component_id
        ) AS component_average,

        ROW_NUMBER() OVER (
            PARTITION BY component_id
            ORDER BY duration_ms DESC
        ) AS performance_rank

    FROM render_sessions

    WHERE status = 'completed'
)

SELECT
    c.component_name,
    m.render_sequence,
    m.duration_ms,
    ROUND(m.component_average, 3) AS component_average_ms,
    m.performance_rank
FROM render_metrics m
JOIN components c
    ON c.component_id = m.component_id
ORDER BY m.performance_rank;


-- =========================================================
-- 34. CUSTOM HOOK COMPOSITION REPORT
-- =========================================================

SELECT
    parent.hook_name AS custom_hook,
    child.hook_name AS internal_hook,
    child.category AS internal_category,
    composition.composition_order
FROM custom_hook_composition composition
JOIN hook_definitions parent
    ON parent.hook_id = composition.parent_hook_id
JOIN hook_definitions child
    ON child.hook_id = composition.child_hook_id
ORDER BY parent.hook_name, composition.composition_order;


-- =========================================================
-- 35. PROCEDURE AND FUNCTION USAGE
-- =========================================================

SELECT *
FROM validate_component_hook_order(
    (
        SELECT render_id
        FROM render_sessions
        WHERE render_sequence = 1
    )
);


SELECT *
FROM component_cache_report(
    (
        SELECT component_id
        FROM components
        WHERE component_name = 'RepositoryDashboard'
    )
);


-- =========================================================
-- 36. TRANSACTIONAL WORKFLOW EXAMPLE
-- =========================================================

-- A valid production observation is inserted atomically.
-- If either the render or its execution is invalid, the
-- transaction rolls back.

SAVEPOINT before_observation;

DO $$
DECLARE
    v_component_id BIGINT;
    v_hook_id BIGINT;
    v_render_id BIGINT;
BEGIN
    SELECT component_id
    INTO v_component_id
    FROM components
    WHERE component_name = 'RepositoryDashboard';

    SELECT hook_id
    INTO v_hook_id
    FROM hook_definitions
    WHERE component_id = v_component_id
      AND hook_name = 'filteredRepositories';

    INSERT INTO render_sessions (
        component_id,
        render_sequence,
        status,
        trigger_reason,
        props_fingerprint
    )
    VALUES (
        v_component_id,
        5,
        'started',
        'dependency_update',
        'props-observation-005'
    )
    RETURNING render_id INTO v_render_id;

    INSERT INTO hook_executions (
        render_id,
        hook_id,
        execution_order,
        outcome,
        execution_duration_us,
        dependency_count
    )
    VALUES (
        v_render_id,
        v_hook_id,
        1,
        'cache_miss',
        142.0,
        2
    );

    INSERT INTO dependency_snapshots (
        execution_id,
        dependency_position,
        dependency_type,
        dependency_fingerprint
    )
    SELECT
        execution_id,
        0,
        'object',
        'repository-array-v2'
    FROM hook_executions
    WHERE render_id = v_render_id;

    INSERT INTO dependency_snapshots (
        execution_id,
        dependency_position,
        dependency_type,
        dependency_fingerprint
    )
    SELECT
        execution_id,
        1,
        'number',
        '85'
    FROM hook_executions
    WHERE render_id = v_render_id;

    UPDATE render_sessions
    SET
        status = 'completed',
        completed_at = CURRENT_TIMESTAMP,
        duration_ms = 3.4
    WHERE render_id = v_render_id;

EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Observation rejected: %', SQLERRM;
        RAISE;
END;
$$;

COMMIT;
