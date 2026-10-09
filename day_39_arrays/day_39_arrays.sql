-- PostgreSQL 14+
-- Deployment telemetry modeled as relational data, with array operations
-- represented by ordered rows, aggregates, filtering, and existence queries.

BEGIN;

DROP VIEW IF EXISTS service_health_report;
DROP TABLE IF EXISTS deployment_samples;
DROP TABLE IF EXISTS monitored_services;

CREATE TABLE monitored_services (
    service_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    service_name TEXT NOT NULL CHECK (length(trim(service_name)) > 0),
    version TEXT NOT NULL CHECK (length(trim(version)) > 0),
    UNIQUE (service_name, version)
);

CREATE TABLE deployment_samples (
    sample_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    service_id BIGINT NOT NULL REFERENCES monitored_services(service_id)
        ON DELETE RESTRICT,
    sampled_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    latency_ms NUMERIC(12, 3) NOT NULL CHECK (latency_ms >= 0),
    failed_requests INTEGER NOT NULL DEFAULT 0 CHECK (failed_requests >= 0),
    healthy BOOLEAN NOT NULL
);

-- Supports per-service time-window scans and chronological retrieval.
CREATE INDEX deployment_samples_service_time_idx
    ON deployment_samples (service_id, sampled_at DESC);

-- Supports queries that prioritize high-latency observations.
CREATE INDEX deployment_samples_latency_idx
    ON deployment_samples (latency_ms DESC);

INSERT INTO monitored_services (service_name, version) VALUES
    ('gateway', '3.2.0'),
    ('billing', '2.8.1'),
    ('inventory', '1.9.4'),
    ('search', '4.1.0');

INSERT INTO deployment_samples
    (service_id, sampled_at, latency_ms, failed_requests, healthy)
SELECT
    service_id,
    TIMESTAMPTZ '2026-10-09 08:00:00+00',
    CASE service_name
        WHEN 'gateway' THEN 45.500
        WHEN 'billing' THEN 135.000
        WHEN 'inventory' THEN 88.000
        WHEN 'search' THEN 172.500
    END,
    CASE service_name
        WHEN 'gateway' THEN 2
        WHEN 'billing' THEN 8
        WHEN 'inventory' THEN 0
        WHEN 'search' THEN 15
    END,
    service_name <> 'inventory'
FROM monitored_services;

INSERT INTO deployment_samples
    (service_id, sampled_at, latency_ms, failed_requests, healthy)
SELECT service_id, TIMESTAMPTZ '2026-10-09 08:05:00+00',
       52.000, 1, TRUE
FROM monitored_services
WHERE service_name = 'gateway';

-- A view provides a stable reporting interface over individual observations.
CREATE VIEW service_health_report AS
SELECT
    s.service_id,
    s.service_name,
    s.version,
    COUNT(d.sample_id) AS sample_count,
    AVG(d.latency_ms) AS average_latency_ms,
    MAX(d.latency_ms) AS maximum_latency_ms,
    COALESCE(SUM(d.failed_requests), 0) AS total_failed_requests,
    COUNT(d.sample_id) FILTER (WHERE d.healthy) AS healthy_sample_count,
    COUNT(d.sample_id) FILTER (WHERE NOT d.healthy) AS unhealthy_sample_count,
    COALESCE(BOOL_AND(d.healthy), FALSE) AS all_samples_healthy,
    COALESCE(BOOL_OR(d.latency_ms > 100), FALSE) AS has_slow_sample
FROM monitored_services AS s
LEFT JOIN deployment_samples AS d
    ON d.service_id = s.service_id
GROUP BY s.service_id, s.service_name, s.version;

-- Inspect aggregated behavior, including services without any samples.
SELECT *
FROM service_health_report
ORDER BY average_latency_ms DESC NULLS LAST;

-- Filter: return observations exceeding the latency threshold.
SELECT s.service_name, d.sampled_at, d.latency_ms
FROM deployment_samples AS d
JOIN monitored_services AS s USING (service_id)
WHERE d.latency_ms > 100
ORDER BY d.latency_ms DESC;

-- Find: select the earliest unhealthy observation in the dataset.
SELECT s.service_name, d.sampled_at, d.latency_ms
FROM deployment_samples AS d
JOIN monitored_services AS s USING (service_id)
WHERE NOT d.healthy
ORDER BY d.sampled_at, d.sample_id
LIMIT 1;

-- Some: EXISTS answers whether at least one critical observation exists.
SELECT EXISTS (
    SELECT 1
    FROM deployment_samples
    WHERE latency_ms >= 150
) AS has_critical_latency;

-- Every: NOT EXISTS finds services with at least one unhealthy sample.
SELECT s.service_name
FROM monitored_services AS s
WHERE NOT EXISTS (
    SELECT 1
    FROM deployment_samples AS d
    WHERE d.service_id = s.service_id
      AND NOT d.healthy
)
ORDER BY s.service_name;

-- Array aggregation retains sample order explicitly through ORDER BY.
SELECT
    s.service_name,
    ARRAY_AGG(d.latency_ms ORDER BY d.sampled_at, d.sample_id)
        FILTER (WHERE d.sample_id IS NOT NULL) AS latency_array,
    ARRAY_AGG(d.healthy ORDER BY d.sampled_at, d.sample_id)
        FILTER (WHERE d.sample_id IS NOT NULL) AS health_array
FROM monitored_services AS s
LEFT JOIN deployment_samples AS d USING (service_id)
GROUP BY s.service_id, s.service_name
ORDER BY s.service_name;

-- Transform: project each observation into a labeled status.
SELECT
    s.service_name,
    d.latency_ms,
    CASE
        WHEN d.latency_ms >= 150 THEN 'critical'
        WHEN d.latency_ms > 100 THEN 'slow'
        ELSE 'within_threshold'
    END AS latency_status
FROM deployment_samples AS d
JOIN monitored_services AS s USING (service_id)
ORDER BY s.service_name, d.sampled_at;

-- Transactional integrity: invalid negative values violate CHECK constraints.
-- Run this statement separately if testing failure behavior because a failed
-- statement aborts the current transaction until rollback.
SAVEPOINT before_invalid_sample;

-- This intentionally invalid statement is commented out to keep the script
-- executable without aborting the transaction:
-- INSERT INTO deployment_samples (service_id, latency_ms, failed_requests, healthy)
-- SELECT service_id, -1, 0, TRUE
-- FROM monitored_services WHERE service_name = 'gateway';

ROLLBACK TO SAVEPOINT before_invalid_sample;

COMMIT;
