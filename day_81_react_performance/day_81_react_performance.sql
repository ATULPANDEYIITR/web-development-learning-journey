-- ============================================================
-- REACT PERFORMANCE ENGINEERING
-- PostgreSQL 15+
--
-- Domain model:
-- Applications
--   -> Components
--   -> Component renders
--   -> Memoization cache metrics
--   -> Code-split chunks
--   -> Lazy-load events
--   -> Performance measurements
--   -> Performance evaluations
--
-- Run as a database owner or a role permitted to create objects.
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS react_performance;

SET search_path TO react_performance, public;

-- ============================================================
-- 1. ENUMERATED DOMAIN TYPES
-- ============================================================

CREATE TYPE component_type AS ENUM (
    'PAGE',
    'LAYOUT',
    'FUNCTIONAL',
    'MEMOIZED',
    'CONTEXT_PROVIDER',
    'SUSPENSE_BOUNDARY'
);

CREATE TYPE chunk_status AS ENUM (
    'REGISTERED',
    'REQUESTED',
    'LOADED',
    'FAILED'
);

CREATE TYPE load_trigger AS ENUM (
    'INITIAL_RENDER',
    'ROUTE_NAVIGATION',
    'USER_INTERACTION',
    'PREFETCH',
    'RETRY'
);

CREATE TYPE evaluation_status AS ENUM (
    'PASS',
    'WARNING',
    'FAIL'
);

-- ============================================================
-- 2. APPLICATIONS
-- ============================================================

CREATE TABLE applications (
    application_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    application_name VARCHAR(150) NOT NULL UNIQUE,
    environment VARCHAR(30) NOT NULL DEFAULT 'development',
    version VARCHAR(40) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_environment CHECK (
        environment IN (
            'development',
            'staging',
            'production'
        )
    )
);

-- ============================================================
-- 3. COMPONENTS
-- ============================================================

CREATE TABLE components (
    component_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    application_id BIGINT NOT NULL
        REFERENCES applications(application_id)
        ON DELETE CASCADE,

    component_name VARCHAR(150) NOT NULL,
    component_type component_type NOT NULL,
    parent_component_id BIGINT,
    memoization_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    estimated_complexity INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT unique_component_name
        UNIQUE(application_id, component_name),

    CONSTRAINT valid_complexity
        CHECK (estimated_complexity > 0),

    CONSTRAINT valid_parent
        FOREIGN KEY (parent_component_id)
        REFERENCES components(component_id)
        ON DELETE SET NULL,

    CONSTRAINT no_direct_self_parent
        CHECK (
            parent_component_id IS NULL
            OR parent_component_id <> component_id
        )
);

CREATE INDEX idx_components_application
    ON components(application_id);

CREATE INDEX idx_components_parent
    ON components(parent_component_id);

CREATE INDEX idx_components_memoized
    ON components(application_id, memoization_enabled);

-- ============================================================
-- 4. COMPONENT RENDER EVENTS
-- ============================================================

CREATE TABLE component_renders (
    render_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    component_id BIGINT NOT NULL
        REFERENCES components(component_id)
        ON DELETE CASCADE,

    session_id UUID NOT NULL,
    render_sequence INTEGER NOT NULL,
    render_started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    render_duration_ms NUMERIC(12, 4) NOT NULL,
    was_skipped BOOLEAN NOT NULL DEFAULT FALSE,
    props_fingerprint CHAR(64) NOT NULL,

    trigger_reason VARCHAR(60) NOT NULL,

    CONSTRAINT valid_render_duration
        CHECK (render_duration_ms >= 0),

    CONSTRAINT valid_render_sequence
        CHECK (render_sequence > 0),

    CONSTRAINT unique_session_render
        UNIQUE(component_id, session_id, render_sequence)
);

CREATE INDEX idx_renders_component_time
    ON component_renders(component_id, render_started_at DESC);

CREATE INDEX idx_renders_session
    ON component_renders(session_id, render_sequence);

CREATE INDEX idx_renders_duration
    ON component_renders(render_duration_ms DESC);

CREATE INDEX idx_renders_skipped
    ON component_renders(component_id, was_skipped);

-- ============================================================
-- 5. MEMOIZATION METRICS
-- ============================================================

CREATE TABLE memoization_metrics (
    metric_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    component_id BIGINT NOT NULL
        REFERENCES components(component_id)
        ON DELETE CASCADE,

    measured_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    cache_hits BIGINT NOT NULL DEFAULT 0,
    cache_misses BIGINT NOT NULL DEFAULT 0,
    cache_evictions BIGINT NOT NULL DEFAULT 0,

    cache_memory_kb NUMERIC(12, 2) NOT NULL DEFAULT 0,

    CONSTRAINT valid_cache_counts CHECK (
        cache_hits >= 0
        AND cache_misses >= 0
        AND cache_evictions >= 0
        AND cache_memory_kb >= 0
    )
);

CREATE INDEX idx_memoization_component_time
    ON memoization_metrics(component_id, measured_at DESC);

-- ============================================================
-- 6. CODE-SPLIT CHUNKS
-- ============================================================

CREATE TABLE code_chunks (
    chunk_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    application_id BIGINT NOT NULL
        REFERENCES applications(application_id)
        ON DELETE CASCADE,

    chunk_name VARCHAR(150) NOT NULL,
    route_pattern VARCHAR(200),
    chunk_size_kb NUMERIC(12, 2) NOT NULL,
    compressed_size_kb NUMERIC(12, 2),
    is_initial_chunk BOOLEAN NOT NULL DEFAULT FALSE,
    is_prefetchable BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT unique_chunk
        UNIQUE(application_id, chunk_name),

    CONSTRAINT valid_chunk_size
        CHECK (chunk_size_kb > 0),

    CONSTRAINT valid_compressed_size
        CHECK (
            compressed_size_kb IS NULL
            OR (
                compressed_size_kb > 0
                AND compressed_size_kb <= chunk_size_kb
            )
        )
);

CREATE INDEX idx_chunks_application
    ON code_chunks(application_id);

CREATE INDEX idx_chunks_initial
    ON code_chunks(application_id, is_initial_chunk);

-- ============================================================
-- 7. COMPONENT-TO-CHUNK MAPPING
-- ============================================================

CREATE TABLE component_chunks (
    component_id BIGINT NOT NULL
        REFERENCES components(component_id)
        ON DELETE CASCADE,

    chunk_id BIGINT NOT NULL
        REFERENCES code_chunks(chunk_id)
        ON DELETE CASCADE,

    is_primary_chunk BOOLEAN NOT NULL DEFAULT FALSE,

    PRIMARY KEY(component_id, chunk_id)
);

CREATE INDEX idx_component_chunks_chunk
    ON component_chunks(chunk_id);

-- ============================================================
-- 8. LAZY LOADING EVENTS
-- ============================================================

CREATE TABLE lazy_load_events (
    load_event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    chunk_id BIGINT NOT NULL
        REFERENCES code_chunks(chunk_id)
        ON DELETE CASCADE,

    session_id UUID NOT NULL,

    trigger_type load_trigger NOT NULL,
    status chunk_status NOT NULL DEFAULT 'REGISTERED',

    requested_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    transfer_duration_ms NUMERIC(12, 4),
    retry_count INTEGER NOT NULL DEFAULT 0,

    error_code VARCHAR(80),
    error_message VARCHAR(500),

    CONSTRAINT valid_retry_count
        CHECK (retry_count >= 0),

    CONSTRAINT valid_transfer_duration
        CHECK (
            transfer_duration_ms IS NULL
            OR transfer_duration_ms >= 0
        ),

    CONSTRAINT valid_load_timestamps
        CHECK (
            completed_at IS NULL
            OR requested_at IS NULL
            OR completed_at >= requested_at
        ),

    CONSTRAINT valid_loaded_event
        CHECK (
            status <> 'LOADED'
            OR completed_at IS NOT NULL
        ),

    CONSTRAINT valid_failure_event
        CHECK (
            status <> 'FAILED'
            OR error_code IS NOT NULL
        )
);

CREATE INDEX idx_lazy_load_chunk_time
    ON lazy_load_events(chunk_id, requested_at DESC);

CREATE INDEX idx_lazy_load_failures
    ON lazy_load_events(status, requested_at DESC)
    WHERE status = 'FAILED';

CREATE INDEX idx_lazy_load_session
    ON lazy_load_events(session_id);

-- ============================================================
-- 9. PERFORMANCE MEASUREMENTS
-- ============================================================

CREATE TABLE performance_measurements (
    measurement_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    application_id BIGINT NOT NULL
        REFERENCES applications(application_id)
        ON DELETE CASCADE,

    session_id UUID NOT NULL,

    measured_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    metric_name VARCHAR(100) NOT NULL,
    metric_value NUMERIC(14, 4) NOT NULL,
    unit VARCHAR(30) NOT NULL,

    page_name VARCHAR(150),
    device_class VARCHAR(40),

    CONSTRAINT valid_metric_value
        CHECK (metric_value >= 0)
);

CREATE INDEX idx_performance_application_time
    ON performance_measurements(
        application_id,
        measured_at DESC
    );

CREATE INDEX idx_performance_metric
    ON performance_measurements(
        application_id,
        metric_name,
        measured_at DESC
    );

CREATE INDEX idx_performance_page
    ON performance_measurements(
        application_id,
        page_name,
        metric_name
    );

-- ============================================================
-- 10. PERFORMANCE THRESHOLD POLICIES
-- ============================================================

CREATE TABLE performance_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    application_id BIGINT NOT NULL
        REFERENCES applications(application_id)
        ON DELETE CASCADE,

    metric_name VARCHAR(100) NOT NULL,
    maximum_value NUMERIC(14, 4) NOT NULL,
    unit VARCHAR(30) NOT NULL,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_maximum_value
        CHECK (maximum_value > 0),

    CONSTRAINT unique_application_policy
        UNIQUE(application_id, metric_name)
);

-- ============================================================
-- 11. PERFORMANCE EVALUATIONS
-- ============================================================

CREATE TABLE performance_evaluations (
    evaluation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    measurement_id BIGINT NOT NULL
        REFERENCES performance_measurements(measurement_id)
        ON DELETE CASCADE,

    policy_id BIGINT NOT NULL
        REFERENCES performance_policies(policy_id)
        ON DELETE CASCADE,

    status evaluation_status NOT NULL,

    evaluated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT unique_measurement_policy
        UNIQUE(measurement_id, policy_id)
);

-- ============================================================
-- 12. APPLICATION METADATA
-- ============================================================

INSERT INTO applications (
    application_name,
    environment,
    version
)
VALUES
    ('Commerce Dashboard', 'production', '2.4.0'),
    ('Internal Administration', 'staging', '1.8.0');

-- ============================================================
-- 13. COMPONENT SAMPLE DATA
-- ============================================================

INSERT INTO components (
    application_id,
    component_name,
    component_type,
    memoization_enabled,
    estimated_complexity
)
VALUES
    (1, 'ApplicationLayout', 'LAYOUT', FALSE, 2),
    (1, 'ProductPage', 'PAGE', FALSE, 4),
    (1, 'ProductList', 'MEMOIZED', TRUE, 8),
    (1, 'ProductCard', 'MEMOIZED', TRUE, 5),
    (1, 'ProductSummary', 'FUNCTIONAL', FALSE, 3),
    (1, 'AnalyticsPage', 'PAGE', FALSE, 9),
    (1, 'AnalyticsBoundary', 'SUSPENSE_BOUNDARY', FALSE, 2),
    (2, 'AdminPage', 'PAGE', FALSE, 6),
    (2, 'UserTable', 'MEMOIZED', TRUE, 8);

-- Set parent relationships after component creation.
UPDATE components child
SET parent_component_id = parent.component_id
FROM components parent
WHERE child.application_id = parent.application_id
  AND (
      (child.component_name = 'ProductPage'
       AND parent.component_name = 'ApplicationLayout')
      OR
      (child.component_name = 'ProductList'
       AND parent.component_name = 'ProductPage')
      OR
      (child.component_name = 'ProductCard'
       AND parent.component_name = 'ProductList')
      OR
      (child.component_name = 'AnalyticsPage'
       AND parent.component_name = 'ApplicationLayout')
      OR
      (child.component_name = 'AnalyticsBoundary'
       AND parent.component_name = 'AnalyticsPage')
  );

-- ============================================================
-- 14. CODE CHUNK SAMPLE DATA
-- ============================================================

INSERT INTO code_chunks (
    application_id,
    chunk_name,
    route_pattern,
    chunk_size_kb,
    compressed_size_kb,
    is_initial_chunk,
    is_prefetchable
)
VALUES
    (1, 'main.bundle', '/', 820, 250, TRUE, FALSE),
    (1, 'product.bundle', '/products', 260, 82, FALSE, TRUE),
    (1, 'analytics.bundle', '/analytics', 430, 135, FALSE, TRUE),
    (1, 'charts.bundle', '/analytics/charts', 350, 110, FALSE, TRUE),
    (2, 'admin.bundle', '/admin', 390, 125, FALSE, TRUE);

INSERT INTO component_chunks (
    component_id,
    chunk_id,
    is_primary_chunk
)
SELECT
    component.component_id,
    chunk.chunk_id,
    TRUE
FROM components component
JOIN code_chunks chunk
    ON (
        component.component_name = 'ApplicationLayout'
        AND chunk.chunk_name = 'main.bundle'
    )
    OR (
        component.component_name IN (
            'ProductPage',
            'ProductList',
            'ProductCard',
            'ProductSummary'
        )
        AND chunk.chunk_name = 'product.bundle'
    )
    OR (
        component.component_name IN (
            'AnalyticsPage',
            'AnalyticsBoundary'
        )
        AND chunk.chunk_name = 'analytics.bundle'
    )
    OR (
        component.component_name = 'AdminPage'
        AND chunk.chunk_name = 'admin.bundle'
    );

-- ============================================================
-- 15. RENDER SAMPLE DATA
-- ============================================================

INSERT INTO component_renders (
    component_id,
    session_id,
    render_sequence,
    render_duration_ms,
    was_skipped,
    props_fingerprint,
    trigger_reason
)
SELECT
    component_id,
    '11111111-1111-1111-1111-111111111111',
    sequence_number,
    duration,
    skipped,
    repeat('a', 64),
    reason
FROM components component
CROSS JOIN (
    VALUES
        (1, 12.5000, FALSE, 'INITIAL_RENDER'),
        (2, 8.3000, FALSE, 'STATE_UPDATE'),
        (3, 0.1000, TRUE, 'UNCHANGED_PROPS'),
        (4, 0.2000, TRUE, 'UNCHANGED_PROPS'),
        (5, 17.8000, FALSE, 'FILTER_CHANGE')
) AS sample(sequence_number, duration, skipped, reason)
WHERE component.component_name = 'ProductList';

INSERT INTO component_renders (
    component_id,
    session_id,
    render_sequence,
    render_duration_ms,
    was_skipped,
    props_fingerprint,
    trigger_reason
)
SELECT
    component_id,
    '22222222-2222-2222-2222-222222222222',
    1,
    24.5000,
    FALSE,
    repeat('b', 64),
    'INITIAL_RENDER'
FROM components
WHERE component_name = 'AnalyticsPage';

-- ============================================================
-- 16. MEMOIZATION SAMPLE METRICS
-- ============================================================

INSERT INTO memoization_metrics (
    component_id,
    cache_hits,
    cache_misses,
    cache_evictions,
    cache_memory_kb
)
SELECT
    component_id,
    850,
    150,
    12,
    512
FROM components
WHERE component_name = 'ProductList';

INSERT INTO memoization_metrics (
    component_id,
    cache_hits,
    cache_misses,
    cache_evictions,
    cache_memory_kb
)
SELECT
    component_id,
    120,
    480,
    90,
    2048
FROM components
WHERE component_name = 'UserTable';

-- ============================================================
-- 17. LAZY LOADING SAMPLE EVENTS
-- ============================================================

INSERT INTO lazy_load_events (
    chunk_id,
    session_id,
    trigger_type,
    status,
    requested_at,
    completed_at,
    transfer_duration_ms
)
SELECT
    chunk_id,
    '11111111-1111-1111-1111-111111111111',
    'ROUTE_NAVIGATION',
    'LOADED',
    NOW() - INTERVAL '10 seconds',
    NOW() - INTERVAL '9 seconds',
    850
FROM code_chunks
WHERE chunk_name = 'analytics.bundle';

INSERT INTO lazy_load_events (
    chunk_id,
    session_id,
    trigger_type,
    status,
    requested_at,
    completed_at,
    transfer_duration_ms,
    retry_count,
    error_code,
    error_message
)
SELECT
    chunk_id,
    '33333333-3333-3333-3333-333333333333',
    'USER_INTERACTION',
    'FAILED',
    NOW() - INTERVAL '5 minutes',
    NOW() - INTERVAL '4 minutes',
    0,
    1,
    'CHUNK_LOAD_FAILED',
    'Network request failed while retrieving the chunk.'
FROM code_chunks
WHERE chunk_name = 'charts.bundle';

-- ============================================================
-- 18. PERFORMANCE POLICIES
-- ============================================================

INSERT INTO performance_policies (
    application_id,
    metric_name,
    maximum_value,
    unit
)
VALUES
    (1, 'LCP', 2500, 'ms'),
    (1, 'INP', 200, 'ms'),
    (1, 'CLS', 0.1, 'score'),
    (1, 'INITIAL_BUNDLE_SIZE', 300, 'KB'),
    (2, 'LCP', 2500, 'ms');

-- ============================================================
-- 19. PERFORMANCE MEASUREMENT SAMPLE DATA
-- ============================================================

INSERT INTO performance_measurements (
    application_id,
    session_id,
    metric_name,
    metric_value,
    unit,
    page_name,
    device_class
)
VALUES
    (1, '11111111-1111-1111-1111-111111111111',
     'LCP', 2100, 'ms', '/products', 'desktop'),

    (1, '11111111-1111-1111-1111-111111111111',
     'INP', 160, 'ms', '/products', 'desktop'),

    (1, '11111111-1111-1111-1111-111111111111',
     'CLS', 0.04, 'score', '/products', 'desktop'),

    (1, '22222222-2222-2222-2222-222222222222',
     'LCP', 3100, 'ms', '/analytics', 'mobile'),

    (1, '22222222-2222-2222-2222-222222222222',
     'INP', 260, 'ms', '/analytics', 'mobile'),

    (1, '22222222-2222-2222-2222-222222222222',
     'CLS', 0.14, 'score', '/analytics', 'mobile'),

    (2, '33333333-3333-3333-3333-333333333333',
     'LCP', 1900, 'ms', '/admin', 'desktop');

-- ============================================================
-- 20. PERFORMANCE EVALUATION FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION evaluate_measurement(
    p_measurement_id BIGINT
)
RETURNS evaluation_status
LANGUAGE plpgsql
AS $$
DECLARE
    v_value NUMERIC;
    v_metric VARCHAR(100);
    v_application_id BIGINT;
    v_policy RECORD;
    v_status evaluation_status;
BEGIN
    SELECT
        metric_value,
        metric_name,
        application_id
    INTO
        v_value,
        v_metric,
        v_application_id
    FROM performance_measurements
    WHERE measurement_id = p_measurement_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Measurement % does not exist',
            p_measurement_id;
    END IF;

    SELECT *
    INTO v_policy
    FROM performance_policies
    WHERE application_id = v_application_id
      AND metric_name = v_metric
      AND is_active = TRUE;

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'No active policy for metric %',
            v_metric;
    END IF;

    IF v_value <= v_policy.maximum_value THEN
        v_status := 'PASS';
    ELSE
        v_status := 'FAIL';
    END IF;

    INSERT INTO performance_evaluations (
        measurement_id,
        policy_id,
        status
    )
    VALUES (
        p_measurement_id,
        v_policy.policy_id,
        v_status
    )
    ON CONFLICT (measurement_id, policy_id)
    DO UPDATE SET
        status = EXCLUDED.status,
        evaluated_at = NOW();

    RETURN v_status;
END;
$$;

-- ============================================================
-- 21. EVALUATE ALL EXISTING MEASUREMENTS
-- ============================================================

DO $$
DECLARE
    measurement RECORD;
BEGIN
    FOR measurement IN
        SELECT measurement_id
        FROM performance_measurements
    LOOP
        PERFORM evaluate_measurement(
            measurement.measurement_id
        );
    END LOOP;
END;
$$;

-- ============================================================
-- 22. COMPONENT RENDER SUMMARY VIEW
-- ============================================================

CREATE OR REPLACE VIEW component_render_summary AS
SELECT
    application.application_name,
    component.component_name,
    component.memoization_enabled,

    COUNT(render.render_id) AS total_renders,

    COUNT(*) FILTER (
        WHERE render.was_skipped
    ) AS skipped_renders,

    COUNT(*) FILTER (
        WHERE NOT render.was_skipped
    ) AS executed_renders,

    ROUND(
        AVG(render.render_duration_ms),
        3
    ) AS average_render_ms,

    ROUND(
        MAX(render.render_duration_ms),
        3
    ) AS maximum_render_ms

FROM components component

JOIN applications application
    ON application.application_id = component.application_id

LEFT JOIN component_renders render
    ON render.component_id = component.component_id

GROUP BY
    application.application_name,
    component.component_name,
    component.memoization_enabled;

-- ============================================================
-- 23. MEMOIZATION EFFECTIVENESS VIEW
-- ============================================================

CREATE OR REPLACE VIEW memoization_effectiveness AS
SELECT
    component.component_name,

    SUM(metric.cache_hits) AS total_hits,
    SUM(metric.cache_misses) AS total_misses,

    SUM(metric.cache_evictions) AS total_evictions,

    ROUND(
        SUM(metric.cache_hits)::NUMERIC /
        NULLIF(
            SUM(metric.cache_hits + metric.cache_misses),
            0
        ),
        4
    ) AS hit_rate,

    SUM(metric.cache_memory_kb) AS cache_memory_kb

FROM memoization_metrics metric

JOIN components component
    ON component.component_id = metric.component_id

GROUP BY component.component_name;

-- ============================================================
-- 24. LAZY LOADING PERFORMANCE VIEW
-- ============================================================

CREATE OR REPLACE VIEW lazy_loading_summary AS
SELECT
    chunk.chunk_name,
    chunk.route_pattern,
    chunk.chunk_size_kb,
    chunk.compressed_size_kb,

    COUNT(event.load_event_id) AS total_requests,

    COUNT(*) FILTER (
        WHERE event.status = 'LOADED'
    ) AS successful_loads,

    COUNT(*) FILTER (
        WHERE event.status = 'FAILED'
    ) AS failed_loads,

    ROUND(
        AVG(event.transfer_duration_ms),
        3
    ) AS average_transfer_ms

FROM code_chunks chunk

LEFT JOIN lazy_load_events event
    ON event.chunk_id = chunk.chunk_id

GROUP BY
    chunk.chunk_name,
    chunk.route_pattern,
    chunk.chunk_size_kb,
    chunk.compressed_size_kb;

-- ============================================================
-- 25. APPLICATION PERFORMANCE REPORT
-- ============================================================

CREATE OR REPLACE VIEW application_performance_report AS
SELECT
    application.application_name,
    measurement.metric_name,
    measurement.unit,

    COUNT(*) AS measurement_count,

    ROUND(AVG(measurement.metric_value), 3) AS average_value,

    ROUND(
        PERCENTILE_CONT(0.75)
        WITHIN GROUP (
            ORDER BY measurement.metric_value
        )::NUMERIC,
        3
    ) AS p75_value,

    ROUND(MAX(measurement.metric_value), 3) AS maximum_value,

    MAX(policy.maximum_value) AS allowed_maximum,

    COUNT(*) FILTER (
        WHERE measurement.metric_value > policy.maximum_value
    ) AS violations

FROM performance_measurements measurement

JOIN applications application
    ON application.application_id = measurement.application_id

LEFT JOIN performance_policies policy
    ON policy.application_id = measurement.application_id
   AND policy.metric_name = measurement.metric_name
   AND policy.is_active = TRUE

GROUP BY
    application.application_name,
    measurement.metric_name,
    measurement.unit;

-- ============================================================
-- 26. STORED PROCEDURE FOR APPLICATION EVALUATION
-- ============================================================

CREATE OR REPLACE PROCEDURE evaluate_application(
    p_application_id BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    item RECORD;
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM applications
        WHERE application_id = p_application_id
    ) THEN
        RAISE EXCEPTION
            'Unknown application: %',
            p_application_id;
    END IF;

    FOR item IN
        SELECT measurement_id
        FROM performance_measurements
        WHERE application_id = p_application_id
    LOOP
        PERFORM evaluate_measurement(item.measurement_id);
    END LOOP;
END;
$$;

-- ============================================================
-- 27. TRIGGER FOR RENDER EVENT VALIDATION
-- ============================================================

CREATE OR REPLACE FUNCTION validate_render_event()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_memoized BOOLEAN;
BEGIN
    SELECT memoization_enabled
    INTO v_memoized
    FROM components
    WHERE component_id = NEW.component_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Component does not exist.';
    END IF;

    IF NEW.was_skipped AND NOT v_memoized THEN
        RAISE EXCEPTION
            'A non-memoized component cannot record a memoized skip.';
    END IF;

    IF NEW.was_skipped AND NEW.render_duration_ms > 5 THEN
        RAISE EXCEPTION
            'Skipped render duration exceeds the configured recording limit.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_render_event
BEFORE INSERT OR UPDATE ON component_renders
FOR EACH ROW
EXECUTE FUNCTION validate_render_event();

-- ============================================================
-- 28. TRANSACTIONAL WORKFLOW EXAMPLE
-- ============================================================

DO $$
DECLARE
    v_measurement_id BIGINT;
BEGIN
    SELECT measurement_id
    INTO v_measurement_id
    FROM performance_measurements
    WHERE metric_name = 'LCP'
      AND page_name = '/products'
    ORDER BY measured_at DESC
    LIMIT 1;

    IF v_measurement_id IS NOT NULL THEN
        PERFORM evaluate_measurement(v_measurement_id);
    END IF;
END;
$$;

-- ============================================================
-- 29. RETRIEVAL: COMPONENT PERFORMANCE
-- ============================================================

SELECT *
FROM component_render_summary
ORDER BY average_render_ms DESC NULLS LAST;

-- ============================================================
-- 30. RETRIEVAL: MEMOIZATION
-- ============================================================

SELECT *
FROM memoization_effectiveness
ORDER BY hit_rate DESC NULLS LAST;

-- ============================================================
-- 31. RETRIEVAL: CHUNK PERFORMANCE
-- ============================================================

SELECT *
FROM lazy_loading_summary
ORDER BY failed_loads DESC, chunk_size_kb DESC;

-- ============================================================
-- 32. VALIDATION: FAILED CHUNK LOADS
-- ============================================================

SELECT
    chunk.chunk_name,
    event.status,
    event.error_code,
    event.error_message,
    event.retry_count
FROM lazy_load_events event
JOIN code_chunks chunk
    ON chunk.chunk_id = event.chunk_id
WHERE event.status = 'FAILED'
ORDER BY event.requested_at DESC;

-- ============================================================
-- 33. AGGREGATION: RENDER COST BY COMPONENT
-- ============================================================

SELECT
    component.component_name,
    COUNT(*) AS render_count,
    ROUND(SUM(render.render_duration_ms), 3) AS total_render_ms,
    ROUND(AVG(render.render_duration_ms), 3) AS average_render_ms
FROM component_renders render
JOIN components component
    ON component.component_id = render.component_id
GROUP BY component.component_name
ORDER BY total_render_ms DESC;

-- ============================================================
-- 34. EVALUATION: PERFORMANCE POLICY VIOLATIONS
-- ============================================================

SELECT
    application.application_name,
    measurement.metric_name,
    measurement.metric_value,
    policy.maximum_value,
    evaluation.status
FROM performance_evaluations evaluation
JOIN performance_measurements measurement
    ON measurement.measurement_id = evaluation.measurement_id
JOIN performance_policies policy
    ON policy.policy_id = evaluation.policy_id
JOIN applications application
    ON application.application_id = measurement.application_id
WHERE evaluation.status <> 'PASS'
ORDER BY measurement.metric_value DESC;

-- ============================================================
-- 35. ELIGIBILITY: INITIAL BUNDLE BUDGET
-- ============================================================

SELECT
    application.application_name,
    SUM(chunk.chunk_size_kb) AS initial_bundle_kb,
    SUM(chunk.compressed_size_kb) AS compressed_initial_bundle_kb,
    CASE
        WHEN SUM(chunk.compressed_size_kb) <= 300
            THEN 'WITHIN_BUDGET'
        ELSE 'BUDGET_EXCEEDED'
    END AS budget_status
FROM applications application
JOIN code_chunks chunk
    ON chunk.application_id = application.application_id
WHERE chunk.is_initial_chunk = TRUE
GROUP BY application.application_name;

-- ============================================================
-- 36. WORKFLOW: REEVALUATE APPLICATION
-- ============================================================

CALL evaluate_application(1);

-- ============================================================
-- 37. REPORTING: APPLICATION METRICS
-- ============================================================

SELECT *
FROM application_performance_report
ORDER BY application_name, metric_name;

COMMIT;
