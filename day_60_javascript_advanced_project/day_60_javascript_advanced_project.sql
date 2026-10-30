/*
 * API-powered operational dashboard
 * PostgreSQL 14 or later.
 *
 * Model:
 *   API sources
 *     -> synchronization runs
 *     -> services and metric observations
 *     -> incidents
 *     -> dashboard evaluation
 *     -> persisted dashboard snapshots
 *
 * The script is self-contained and recreates its demonstration schema.
 */

DROP SCHEMA IF EXISTS ops_dashboard CASCADE;
CREATE SCHEMA ops_dashboard;
SET search_path TO ops_dashboard, public;

-- ---------------------------------------------------------------------
-- Domain types
-- ---------------------------------------------------------------------

CREATE TYPE service_status AS ENUM (
    'OPERATIONAL',
    'DEGRADED',
    'DOWN'
);

CREATE TYPE incident_severity AS ENUM (
    'LOW',
    'MEDIUM',
    'HIGH',
    'CRITICAL'
);

CREATE TYPE incident_status AS ENUM (
    'OPEN',
    'INVESTIGATING',
    'RESOLVED'
);

CREATE TYPE sync_status AS ENUM (
    'RUNNING',
    'SUCCEEDED',
    'PARTIAL',
    'FAILED'
);

CREATE TYPE dashboard_status AS ENUM (
    'READY',
    'DEGRADED',
    'ERROR'
);

-- ---------------------------------------------------------------------
-- API sources and service inventory
-- ---------------------------------------------------------------------

CREATE TABLE api_sources (
    source_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_name VARCHAR(100) NOT NULL UNIQUE,
    base_url TEXT NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT api_source_name_not_empty
        CHECK (BTRIM(source_name) <> ''),

    CONSTRAINT api_source_url_not_empty
        CHECK (BTRIM(base_url) <> '')
);

CREATE TABLE services (
    service_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    service_key VARCHAR(80) NOT NULL UNIQUE,
    service_name VARCHAR(150) NOT NULL,
    region VARCHAR(80) NOT NULL,
    current_status service_status NOT NULL DEFAULT 'OPERATIONAL',
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT service_key_not_empty
        CHECK (BTRIM(service_key) <> ''),

    CONSTRAINT service_name_not_empty
        CHECK (BTRIM(service_name) <> ''),

    CONSTRAINT service_region_not_empty
        CHECK (BTRIM(region) <> '')
);

COMMENT ON TABLE api_sources IS
    'Defines upstream API providers used by dashboard ingestion jobs.';

COMMENT ON TABLE services IS
    'Canonical service inventory used to associate metrics and incidents.';

-- ---------------------------------------------------------------------
-- API synchronization lifecycle
-- ---------------------------------------------------------------------

CREATE TABLE api_sync_runs (
    sync_run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_id BIGINT NOT NULL REFERENCES api_sources(source_id),
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    status sync_status NOT NULL DEFAULT 'RUNNING',
    records_received INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,

    CONSTRAINT sync_records_non_negative
        CHECK (records_received >= 0),

    CONSTRAINT sync_time_order
        CHECK (completed_at IS NULL OR completed_at >= started_at),

    CONSTRAINT sync_completion_matches_status
        CHECK (
            (status = 'RUNNING' AND completed_at IS NULL)
            OR
            (status <> 'RUNNING' AND completed_at IS NOT NULL)
        ),

    CONSTRAINT sync_error_not_empty
        CHECK (error_message IS NULL OR BTRIM(error_message) <> '')
);

CREATE TABLE api_sync_endpoints (
    sync_endpoint_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    sync_run_id BIGINT NOT NULL
        REFERENCES api_sync_runs(sync_run_id) ON DELETE CASCADE,
    endpoint_path VARCHAR(200) NOT NULL,
    http_status SMALLINT,
    records_received INTEGER NOT NULL DEFAULT 0,
    latency_ms NUMERIC(12, 3),
    error_message TEXT,
    succeeded BOOLEAN NOT NULL,

    CONSTRAINT sync_endpoint_path_not_empty
        CHECK (BTRIM(endpoint_path) <> ''),

    CONSTRAINT sync_http_status_range
        CHECK (http_status IS NULL OR http_status BETWEEN 100 AND 599),

    CONSTRAINT sync_endpoint_records_non_negative
        CHECK (records_received >= 0),

    CONSTRAINT sync_latency_non_negative
        CHECK (latency_ms IS NULL OR latency_ms >= 0),

    CONSTRAINT sync_endpoint_outcome
        CHECK (
            (succeeded = TRUE AND http_status BETWEEN 200 AND 299
                AND error_message IS NULL)
            OR
            (succeeded = FALSE)
        ),

    CONSTRAINT sync_endpoint_unique_path
        UNIQUE (sync_run_id, endpoint_path)
);

COMMENT ON TABLE api_sync_runs IS
    'Tracks the lifecycle and result of each upstream API synchronization.';

COMMENT ON TABLE api_sync_endpoints IS
    'Stores endpoint-level HTTP results so partial API failures remain visible.';

-- ---------------------------------------------------------------------
-- Metric definitions and observations
-- ---------------------------------------------------------------------

CREATE TABLE metric_definitions (
    metric_name VARCHAR(80) PRIMARY KEY,
    description TEXT NOT NULL,
    unit VARCHAR(30) NOT NULL,
    minimum_value NUMERIC(18, 4) NOT NULL DEFAULT 0,

    CONSTRAINT metric_name_not_empty
        CHECK (BTRIM(metric_name) <> ''),

    CONSTRAINT metric_unit_not_empty
        CHECK (BTRIM(unit) <> ''),

    CONSTRAINT metric_minimum_non_negative
        CHECK (minimum_value >= 0)
);

CREATE TABLE metric_observations (
    observation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    service_id BIGINT NOT NULL
        REFERENCES services(service_id) ON DELETE CASCADE,
    source_id BIGINT NOT NULL
        REFERENCES api_sources(source_id),
    metric_name VARCHAR(80) NOT NULL
        REFERENCES metric_definitions(metric_name),
    metric_value NUMERIC(18, 4) NOT NULL,
    observed_at TIMESTAMPTZ NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT metric_value_non_negative
        CHECK (metric_value >= 0),

    CONSTRAINT metric_observation_unique
        UNIQUE (service_id, metric_name, observed_at),

    CONSTRAINT metric_observation_not_future
        CHECK (observed_at <= NOW() + INTERVAL '5 minutes')
);

COMMENT ON TABLE metric_observations IS
    'Time-stamped measurements retrieved from upstream service APIs.';

-- The composite index supports latest-per-service metric lookups.
CREATE INDEX idx_metric_latest_lookup
    ON metric_observations (
        service_id,
        metric_name,
        observed_at DESC
    );

-- ---------------------------------------------------------------------
-- Incident management
-- ---------------------------------------------------------------------

CREATE TABLE incidents (
    incident_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    external_reference VARCHAR(100) NOT NULL UNIQUE,
    service_id BIGINT NOT NULL
        REFERENCES services(service_id),
    severity incident_severity NOT NULL,
    status incident_status NOT NULL DEFAULT 'OPEN',
    title VARCHAR(250) NOT NULL,
    opened_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT incident_reference_not_empty
        CHECK (BTRIM(external_reference) <> ''),

    CONSTRAINT incident_title_not_empty
        CHECK (BTRIM(title) <> ''),

    CONSTRAINT incident_resolution_state
        CHECK (
            (status = 'RESOLVED' AND resolved_at IS NOT NULL)
            OR
            (status <> 'RESOLVED' AND resolved_at IS NULL)
        ),

    CONSTRAINT incident_time_order
        CHECK (resolved_at IS NULL OR resolved_at >= opened_at)
);

CREATE INDEX idx_incidents_open_by_service
    ON incidents (service_id, severity, opened_at DESC)
    WHERE status <> 'RESOLVED';

COMMENT ON TABLE incidents IS
    'Stores operational incidents separately from raw metric observations.';

-- ---------------------------------------------------------------------
-- Dashboard configuration and snapshots
-- ---------------------------------------------------------------------

CREATE TABLE dashboard_widgets (
    widget_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    widget_key VARCHAR(80) NOT NULL UNIQUE,
    title VARCHAR(120) NOT NULL,
    widget_type VARCHAR(40) NOT NULL,
    position INTEGER NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    configuration JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT widget_key_not_empty
        CHECK (BTRIM(widget_key) <> ''),

    CONSTRAINT widget_title_not_empty
        CHECK (BTRIM(title) <> ''),

    CONSTRAINT widget_type_not_empty
        CHECK (BTRIM(widget_type) <> ''),

    CONSTRAINT widget_position_non_negative
        CHECK (position >= 0),

    CONSTRAINT widget_configuration_object
        CHECK (JSONB_TYPEOF(configuration) = 'object')
);

CREATE TABLE dashboard_snapshots (
    snapshot_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    state dashboard_status NOT NULL,
    stale_resource_count INTEGER NOT NULL DEFAULT 0,
    payload JSONB NOT NULL,

    CONSTRAINT stale_resource_count_non_negative
        CHECK (stale_resource_count >= 0),

    CONSTRAINT snapshot_payload_object
        CHECK (JSONB_TYPEOF(payload) = 'object')
);

CREATE INDEX idx_dashboard_snapshots_created
    ON dashboard_snapshots (created_at DESC);

-- ---------------------------------------------------------------------
-- Timestamp maintenance
-- ---------------------------------------------------------------------

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at := NOW();
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_api_sources_updated_at
BEFORE UPDATE ON api_sources
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_services_updated_at
BEFORE UPDATE ON services
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_incidents_updated_at
BEFORE UPDATE ON incidents
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

-- ---------------------------------------------------------------------
-- Synchronization finalization
-- ---------------------------------------------------------------------

CREATE OR REPLACE FUNCTION finish_sync_run(
    p_sync_run_id BIGINT,
    p_status sync_status,
    p_records_received INTEGER,
    p_error_message TEXT DEFAULT NULL
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    v_updated_count INTEGER;
BEGIN
    IF p_status = 'RUNNING' THEN
        RAISE EXCEPTION 'A completed synchronization cannot remain RUNNING';
    END IF;

    IF p_records_received < 0 THEN
        RAISE EXCEPTION 'Record count cannot be negative';
    END IF;

    IF p_status = 'SUCCEEDED' AND p_error_message IS NOT NULL THEN
        RAISE EXCEPTION 'Successful synchronization cannot contain an error';
    END IF;

    UPDATE api_sync_runs
       SET status = p_status,
           records_received = p_records_received,
           error_message = p_error_message,
           completed_at = NOW()
     WHERE sync_run_id = p_sync_run_id
       AND status = 'RUNNING';

    GET DIAGNOSTICS v_updated_count = ROW_COUNT;

    IF v_updated_count <> 1 THEN
        RAISE EXCEPTION
            'Sync run % does not exist or is already completed',
            p_sync_run_id;
    END IF;
END;
$$;

COMMENT ON FUNCTION finish_sync_run IS
    'Allows a running synchronization to transition exactly once to a terminal state.';

-- ---------------------------------------------------------------------
-- Dashboard evaluation
-- ---------------------------------------------------------------------

CREATE OR REPLACE FUNCTION evaluate_dashboard(
    p_window INTERVAL DEFAULT INTERVAL '15 minutes'
)
RETURNS TABLE (
    service_id BIGINT,
    service_key VARCHAR(80),
    service_name VARCHAR(150),
    registered_status service_status,
    latest_latency_ms NUMERIC,
    latest_error_rate_pct NUMERIC,
    last_observed_at TIMESTAMPTZ,
    open_incident_count BIGINT,
    critical_incident_count BIGINT,
    data_age_seconds NUMERIC,
    evaluated_status TEXT
)
LANGUAGE sql
STABLE
AS $$
    WITH latest_metrics AS (
        SELECT
            mo.service_id,
            MAX(mo.observed_at) AS last_observed_at,
            MAX(mo.metric_value)
                FILTER (WHERE mo.metric_name = 'latency_ms')
                AS latest_latency_ms,
            MAX(mo.metric_value)
                FILTER (WHERE mo.metric_name = 'error_rate_pct')
                AS latest_error_rate_pct
        FROM metric_observations mo
        WHERE mo.observed_at >= NOW() - p_window
        GROUP BY mo.service_id
    ),
    incident_counts AS (
        SELECT
            i.service_id,
            COUNT(*) FILTER (
                WHERE i.status <> 'RESOLVED'
            ) AS open_incident_count,
            COUNT(*) FILTER (
                WHERE i.status <> 'RESOLVED'
                  AND i.severity = 'CRITICAL'
            ) AS critical_incident_count
        FROM incidents i
        GROUP BY i.service_id
    ),
    service_data AS (
        SELECT
            s.service_id,
            s.service_key,
            s.service_name,
            s.current_status,
            lm.latest_latency_ms,
            lm.latest_error_rate_pct,
            lm.last_observed_at,
            COALESCE(ic.open_incident_count, 0) AS open_incident_count,
            COALESCE(ic.critical_incident_count, 0)
                AS critical_incident_count,
            CASE
                WHEN lm.last_observed_at IS NULL THEN NULL
                ELSE EXTRACT(
                    EPOCH FROM NOW() - lm.last_observed_at
                )
            END AS data_age_seconds
        FROM services s
        LEFT JOIN latest_metrics lm
            ON lm.service_id = s.service_id
        LEFT JOIN incident_counts ic
            ON ic.service_id = s.service_id
        WHERE s.enabled = TRUE
    )
    SELECT
        sd.service_id,
        sd.service_key,
        sd.service_name,
        sd.current_status,
        sd.latest_latency_ms,
        sd.latest_error_rate_pct,
        sd.last_observed_at,
        sd.open_incident_count,
        sd.critical_incident_count,
        sd.data_age_seconds,
        CASE
            WHEN sd.current_status = 'DOWN'
                OR sd.critical_incident_count > 0
                THEN 'DOWN'
            WHEN sd.data_age_seconds IS NULL
                OR sd.data_age_seconds > 600
                THEN 'STALE'
            WHEN sd.current_status = 'DEGRADED'
                OR sd.open_incident_count > 0
                OR COALESCE(sd.latest_error_rate_pct, 0) >= 5
                THEN 'DEGRADED'
            ELSE 'HEALTHY'
        END AS evaluated_status
    FROM service_data sd
    ORDER BY sd.service_name;
$$;

COMMENT ON FUNCTION evaluate_dashboard IS
    'Combines recent service measurements, service status, and active incidents.';

CREATE OR REPLACE VIEW dashboard_service_health AS
SELECT *
FROM evaluate_dashboard(INTERVAL '15 minutes');

CREATE OR REPLACE VIEW dashboard_status_counts AS
SELECT
    evaluated_status,
    COUNT(*) AS service_count
FROM dashboard_service_health
GROUP BY evaluated_status;

-- ---------------------------------------------------------------------
-- Dashboard snapshot creation
-- ---------------------------------------------------------------------

CREATE OR REPLACE FUNCTION refresh_dashboard_snapshot()
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    v_payload JSONB;
    v_stale_count INTEGER;
    v_error_count INTEGER;
    v_state dashboard_status;
    v_snapshot_id BIGINT;
BEGIN
    SELECT
        COALESCE(
            JSONB_AGG(
                JSONB_BUILD_OBJECT(
                    'service_id', service_id,
                    'service_key', service_key,
                    'service_name', service_name,
                    'registered_status', registered_status,
                    'latest_latency_ms', latest_latency_ms,
                    'latest_error_rate_pct', latest_error_rate_pct,
                    'last_observed_at', last_observed_at,
                    'open_incident_count', open_incident_count,
                    'critical_incident_count', critical_incident_count,
                    'data_age_seconds', data_age_seconds,
                    'evaluated_status', evaluated_status
                )
                ORDER BY service_name
            ),
            '[]'::JSONB
        )
    INTO v_payload
    FROM evaluate_dashboard(INTERVAL '15 minutes');

    SELECT COUNT(*)
    INTO v_stale_count
    FROM evaluate_dashboard(INTERVAL '15 minutes')
    WHERE evaluated_status = 'STALE';

    SELECT COUNT(*)
    INTO v_error_count
    FROM api_sync_runs
    WHERE status IN ('FAILED', 'PARTIAL')
      AND started_at >= NOW() - INTERVAL '15 minutes';

    v_state := CASE
        WHEN NOT EXISTS (
            SELECT 1 FROM services WHERE enabled = TRUE
        ) THEN 'ERROR'
        WHEN v_stale_count > 0 OR v_error_count > 0 THEN 'DEGRADED'
        ELSE 'READY'
    END;

    INSERT INTO dashboard_snapshots (
        state,
        stale_resource_count,
        payload
    )
    VALUES (
        v_state,
        v_stale_count,
        JSONB_BUILD_OBJECT(
            'generated_at', NOW(),
            'window', '15 minutes',
            'services', v_payload,
            'recent_sync_errors', v_error_count
        )
    )
    RETURNING snapshot_id INTO v_snapshot_id;

    RETURN v_snapshot_id;
END;
$$;

-- ---------------------------------------------------------------------
-- Reference data
-- ---------------------------------------------------------------------

INSERT INTO api_sources (source_name, base_url)
VALUES
    ('Service Metrics API', 'https://metrics.internal.example/api'),
    ('Incident Management API', 'https://incidents.internal.example/api');

INSERT INTO services (
    service_key,
    service_name,
    region,
    current_status
)
VALUES
    ('payments', 'Payment Processing', 'ap-south-1', 'OPERATIONAL'),
    ('identity', 'Identity Service', 'ap-south-1', 'OPERATIONAL'),
    ('notifications', 'Notification Gateway', 'ap-south-1', 'DEGRADED'),
    ('analytics', 'Analytics Pipeline', 'ap-south-1', 'OPERATIONAL');

INSERT INTO metric_definitions (
    metric_name,
    description,
    unit,
    minimum_value
)
VALUES
    (
        'latency_ms',
        'Observed API response latency',
        'ms',
        0
    ),
    (
        'error_rate_pct',
        'Percentage of requests resulting in an error',
        '%',
        0
    ),
    (
        'requests_per_minute',
        'Number of requests processed per minute',
        'requests/min',
        0
    );

INSERT INTO dashboard_widgets (
    widget_key,
    title,
    widget_type,
    position,
    configuration
)
VALUES
    (
        'service_health',
        'Service Health',
        'STATUS_GRID',
        1,
        '{"show_region": true, "show_open_incidents": true}'::JSONB
    ),
    (
        'api_latency',
        'API Latency',
        'TIME_SERIES',
        2,
        '{"metric": "latency_ms", "window_minutes": 15}'::JSONB
    ),
    (
        'incident_summary',
        'Incident Summary',
        'INCIDENT_LIST',
        3,
        '{"include_resolved": false}'::JSONB
    );

-- ---------------------------------------------------------------------
-- API synchronization examples
-- ---------------------------------------------------------------------

DO $$
DECLARE
    v_source_id BIGINT;
    v_run_id BIGINT;
BEGIN
    SELECT source_id
      INTO v_source_id
      FROM api_sources
     WHERE source_name = 'Service Metrics API';

    INSERT INTO api_sync_runs (source_id)
    VALUES (v_source_id)
    RETURNING sync_run_id INTO v_run_id;

    INSERT INTO api_sync_endpoints (
        sync_run_id,
        endpoint_path,
        http_status,
        records_received,
        latency_ms,
        succeeded
    )
    VALUES
        (
            v_run_id,
            '/services/metrics',
            200,
            15,
            42.8,
            TRUE
        );

    PERFORM finish_sync_run(
        v_run_id,
        'SUCCEEDED',
        15,
        NULL
    );
END;
$$;

DO $$
DECLARE
    v_source_id BIGINT;
    v_run_id BIGINT;
BEGIN
    SELECT source_id
      INTO v_source_id
      FROM api_sources
     WHERE source_name = 'Incident Management API';

    INSERT INTO api_sync_runs (source_id)
    VALUES (v_source_id)
    RETURNING sync_run_id INTO v_run_id;

    INSERT INTO api_sync_endpoints (
        sync_run_id,
        endpoint_path,
        http_status,
        records_received,
        latency_ms,
        error_message,
        succeeded
    )
    VALUES
        (
            v_run_id,
            '/incidents/open',
            503,
            0,
            2500.0,
            'Upstream service temporarily unavailable',
            FALSE
        );

    PERFORM finish_sync_run(
        v_run_id,
        'FAILED',
        0,
        'Incident API returned HTTP 503'
    );
END;
$$;

-- ---------------------------------------------------------------------
-- Metric observations
-- ---------------------------------------------------------------------

INSERT INTO metric_observations (
    service_id,
    source_id,
    metric_name,
    metric_value,
    observed_at
)
SELECT
    s.service_id,
    src.source_id,
    v.metric_name,
    v.metric_value,
    NOW() - v.age
FROM (
    VALUES
        ('payments', 'latency_ms', 145.2::NUMERIC, INTERVAL '12 seconds'),
        ('payments', 'error_rate_pct', 0.8::NUMERIC, INTERVAL '12 seconds'),
        ('payments', 'requests_per_minute', 1250::NUMERIC, INTERVAL '12 seconds'),
        ('identity', 'latency_ms', 88.4::NUMERIC, INTERVAL '8 seconds'),
        ('identity', 'error_rate_pct', 0.2::NUMERIC, INTERVAL '8 seconds'),
        ('identity', 'requests_per_minute', 2100::NUMERIC, INTERVAL '8 seconds'),
        ('notifications', 'latency_ms', 420.0::NUMERIC, INTERVAL '20 seconds'),
        ('notifications', 'error_rate_pct', 6.2::NUMERIC, INTERVAL '20 seconds'),
        ('notifications', 'requests_per_minute', 870::NUMERIC, INTERVAL '20 seconds'),
        ('analytics', 'latency_ms', 180.0::NUMERIC, INTERVAL '25 minutes'),
        ('analytics', 'error_rate_pct', 0.5::NUMERIC, INTERVAL '25 minutes')
) AS v(service_key, metric_name, metric_value, age)
JOIN services s
    ON s.service_key = v.service_key
JOIN api_sources src
    ON src.source_name = 'Service Metrics API';

-- ---------------------------------------------------------------------
-- Incident examples
-- ---------------------------------------------------------------------

INSERT INTO incidents (
    external_reference,
    service_id,
    severity,
    status,
    title,
    opened_at,
    resolved_at
)
SELECT
    v.external_reference,
    s.service_id,
    v.severity::incident_severity,
    v.status::incident_status,
    v.title,
    NOW() - v.age,
    CASE
        WHEN v.status = 'RESOLVED'
            THEN NOW() - INTERVAL '1 hour'
        ELSE NULL
    END
FROM (
    VALUES
        (
            'INC-2041',
            'notifications',
            'HIGH',
            'INVESTIGATING',
            'Elevated notification latency',
            INTERVAL '30 minutes'
        ),
        (
            'INC-2038',
            'payments',
            'LOW',
            'RESOLVED',
            'Intermittent callback delay',
            INTERVAL '2 hours'
        ),
        (
            'INC-2050',
            'identity',
            'CRITICAL',
            'OPEN',
            'Identity token validation alerts',
            INTERVAL '5 minutes'
        )
) AS v(
    external_reference,
    service_key,
    severity,
    status,
    title,
    age
)
JOIN services s
    ON s.service_key = v.service_key;

-- ---------------------------------------------------------------------
-- Retrieval and operational reporting
-- ---------------------------------------------------------------------

-- 1. Current service inventory and evaluated health.
SELECT
    service_key,
    service_name,
    registered_status,
    evaluated_status,
    last_observed_at,
    data_age_seconds
FROM dashboard_service_health
ORDER BY service_name;

-- 2. Latest measurements for each service and metric.
WITH ranked_observations AS (
    SELECT
        s.service_key,
        mo.metric_name,
        mo.metric_value,
        mo.observed_at,
        ROW_NUMBER() OVER (
            PARTITION BY mo.service_id, mo.metric_name
            ORDER BY mo.observed_at DESC
        ) AS observation_rank
    FROM metric_observations mo
    JOIN services s
        ON s.service_id = mo.service_id
)
SELECT
    service_key,
    metric_name,
    metric_value,
    observed_at
FROM ranked_observations
WHERE observation_rank = 1
ORDER BY service_key, metric_name;

-- 3. Open incidents by severity and service.
SELECT
    s.service_name,
    i.severity,
    COUNT(*) AS incident_count,
    MIN(i.opened_at) AS oldest_open_incident
FROM incidents i
JOIN services s
    ON s.service_id = i.service_id
WHERE i.status <> 'RESOLVED'
GROUP BY s.service_name, i.severity
ORDER BY
    CASE i.severity
        WHEN 'CRITICAL' THEN 1
        WHEN 'HIGH' THEN 2
        WHEN 'MEDIUM' THEN 3
        WHEN 'LOW' THEN 4
    END;

-- 4. Synchronization status and endpoint failures.
SELECT
    src.source_name,
    r.sync_run_id,
    r.status,
    r.records_received,
    r.started_at,
    r.completed_at,
    e.endpoint_path,
    e.http_status,
    e.succeeded,
    e.error_message
FROM api_sync_runs r
JOIN api_sources src
    ON src.source_id = r.source_id
LEFT JOIN api_sync_endpoints e
    ON e.sync_run_id = r.sync_run_id
ORDER BY r.started_at DESC, e.endpoint_path;

-- 5. Service health distribution.
SELECT
    evaluated_status,
    service_count
FROM dashboard_status_counts
ORDER BY evaluated_status;

-- 6. Identify stale services separately from operational health.
SELECT
    service_key,
    service_name,
    last_observed_at,
    data_age_seconds,
    evaluated_status
FROM dashboard_service_health
WHERE evaluated_status = 'STALE'
   OR data_age_seconds IS NULL
ORDER BY data_age_seconds DESC NULLS FIRST;

-- ---------------------------------------------------------------------
-- Transactional dashboard snapshot
-- ---------------------------------------------------------------------

BEGIN;

SELECT refresh_dashboard_snapshot() AS created_snapshot_id;

COMMIT;

-- Inspect the most recent stored snapshot.
SELECT
    snapshot_id,
    created_at,
    state,
    stale_resource_count,
    JSONB_ARRAY_LENGTH(payload -> 'services') AS service_count,
    payload
FROM dashboard_snapshots
ORDER BY created_at DESC
LIMIT 5;

-- ---------------------------------------------------------------------
-- Validation examples
-- ---------------------------------------------------------------------

-- This query returns any service metric definitions with no observations.
SELECT
    s.service_key,
    md.metric_name
FROM services s
CROSS JOIN metric_definitions md
LEFT JOIN metric_observations mo
    ON mo.service_id = s.service_id
   AND mo.metric_name = md.metric_name
WHERE s.enabled = TRUE
  AND mo.observation_id IS NULL
ORDER BY s.service_key, md.metric_name;

-- This query identifies synchronization sources with recent failures.
SELECT
    src.source_name,
    COUNT(*) FILTER (WHERE r.status = 'FAILED') AS failed_runs,
    COUNT(*) FILTER (WHERE r.status = 'PARTIAL') AS partial_runs,
    MAX(r.started_at) AS latest_attempt
FROM api_sources src
LEFT JOIN api_sync_runs r
    ON r.source_id = src.source_id
   AND r.started_at >= NOW() - INTERVAL '24 hours'
GROUP BY src.source_name
ORDER BY src.source_name;
