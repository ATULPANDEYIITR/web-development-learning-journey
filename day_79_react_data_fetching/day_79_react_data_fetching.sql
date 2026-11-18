-- =========================================================
-- REACT DATA FETCHING
-- PostgreSQL API Query, Cache, Request, and Error Management
--
-- PostgreSQL 15+
--
-- Models:
-- API services
-- API endpoints
-- Clients and query subscriptions
-- Request execution
-- Loading, success, and error states
-- Response caching
-- Cache invalidation
-- Retry attempts
-- Request deduplication
-- Stale cache detection
-- Query performance reporting
-- =========================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS data_fetching;

SET search_path TO data_fetching, public;

-- ---------------------------------------------------------
-- 1. Enumerated domain types
-- ---------------------------------------------------------

CREATE TYPE request_status AS ENUM (
    'idle',
    'loading',
    'success',
    'error',
    'cancelled'
);

CREATE TYPE http_method AS ENUM (
    'GET',
    'POST',
    'PUT',
    'PATCH',
    'DELETE'
);

CREATE TYPE cache_policy AS ENUM (
    'cache_first',
    'network_first',
    'stale_while_revalidate',
    'network_only'
);

CREATE TYPE error_category AS ENUM (
    'network',
    'client',
    'server',
    'timeout',
    'invalid_response',
    'cancelled'
);

-- ---------------------------------------------------------
-- 2. API services
-- ---------------------------------------------------------

CREATE TABLE api_services (
    service_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    service_name VARCHAR(120) NOT NULL UNIQUE,

    base_url TEXT NOT NULL,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_base_url CHECK (
        base_url ~ '^https?://'
    )
);

-- ---------------------------------------------------------
-- 3. API endpoints
-- ---------------------------------------------------------

CREATE TABLE api_endpoints (
    endpoint_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    service_id BIGINT NOT NULL
        REFERENCES api_services(service_id),

    endpoint_path TEXT NOT NULL,

    method http_method NOT NULL DEFAULT 'GET',

    timeout_ms INTEGER NOT NULL DEFAULT 5000,

    cache_ttl_seconds INTEGER NOT NULL DEFAULT 30,

    maximum_retries INTEGER NOT NULL DEFAULT 2,

    is_cacheable BOOLEAN NOT NULL DEFAULT TRUE,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT unique_service_endpoint
        UNIQUE (service_id, endpoint_path, method),

    CONSTRAINT valid_endpoint_path CHECK (
        endpoint_path LIKE '/%'
    ),

    CONSTRAINT valid_timeout CHECK (
        timeout_ms BETWEEN 100 AND 120000
    ),

    CONSTRAINT valid_cache_ttl CHECK (
        cache_ttl_seconds BETWEEN 0 AND 86400
    ),

    CONSTRAINT valid_retry_count CHECK (
        maximum_retries BETWEEN 0 AND 10
    )
);

CREATE INDEX idx_api_endpoints_service
ON api_endpoints(service_id, is_active);

-- ---------------------------------------------------------
-- 4. Application clients
-- ---------------------------------------------------------

CREATE TABLE application_clients (
    client_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    client_name VARCHAR(120) NOT NULL UNIQUE,

    environment VARCHAR(30) NOT NULL,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_environment CHECK (
        environment IN (
            'development',
            'testing',
            'staging',
            'production'
        )
    )
);

-- ---------------------------------------------------------
-- 5. Query definitions
-- ---------------------------------------------------------

CREATE TABLE queries (
    query_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    client_id BIGINT NOT NULL
        REFERENCES application_clients(client_id),

    endpoint_id BIGINT NOT NULL
        REFERENCES api_endpoints(endpoint_id),

    query_key VARCHAR(255) NOT NULL,

    parameters JSONB NOT NULL DEFAULT '{}'::JSONB,

    policy cache_policy NOT NULL DEFAULT 'cache_first',

    enabled BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT unique_client_query
        UNIQUE (client_id, query_key),

    CONSTRAINT parameters_must_be_object CHECK (
        jsonb_typeof(parameters) = 'object'
    )
);

CREATE INDEX idx_queries_client
ON queries(client_id, enabled);

CREATE INDEX idx_queries_endpoint
ON queries(endpoint_id);

CREATE INDEX idx_queries_parameters
ON queries USING GIN(parameters);

-- ---------------------------------------------------------
-- 6. Request execution history
-- ---------------------------------------------------------

CREATE TABLE api_requests (
    request_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    query_id BIGINT NOT NULL
        REFERENCES queries(query_id),

    request_key VARCHAR(255) NOT NULL,

    status request_status NOT NULL DEFAULT 'idle',

    started_at TIMESTAMPTZ,

    completed_at TIMESTAMPTZ,

    http_status_code INTEGER,

    response_body JSONB,

    error_message TEXT,

    error_type error_category,

    attempt_number INTEGER NOT NULL DEFAULT 1,

    is_cache_hit BOOLEAN NOT NULL DEFAULT FALSE,

    response_time_ms NUMERIC(12, 3),

    CONSTRAINT valid_attempt_number CHECK (
        attempt_number >= 1
    ),

    CONSTRAINT valid_http_status CHECK (
        http_status_code IS NULL OR
        http_status_code BETWEEN 100 AND 599
    ),

    CONSTRAINT valid_response_time CHECK (
        response_time_ms IS NULL OR
        response_time_ms >= 0
    ),

    CONSTRAINT valid_completion_time CHECK (
        completed_at IS NULL OR
        started_at IS NULL OR
        completed_at >= started_at
    )
);

CREATE INDEX idx_requests_query_time
ON api_requests(query_id, started_at DESC);

CREATE INDEX idx_requests_status_time
ON api_requests(status, started_at DESC);

CREATE INDEX idx_requests_key
ON api_requests(request_key);

CREATE INDEX idx_requests_failures
ON api_requests(error_type, completed_at DESC)
WHERE status = 'error';

-- ---------------------------------------------------------
-- 7. Response cache
-- ---------------------------------------------------------

CREATE TABLE response_cache (
    cache_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    query_id BIGINT NOT NULL
        REFERENCES queries(query_id),

    cache_key VARCHAR(255) NOT NULL,

    response_data JSONB NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    expires_at TIMESTAMPTZ NOT NULL,

    last_accessed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    access_count BIGINT NOT NULL DEFAULT 0,

    CONSTRAINT unique_query_cache_key
        UNIQUE (query_id, cache_key),

    CONSTRAINT valid_expiration CHECK (
        expires_at > created_at
    ),

    CONSTRAINT valid_access_count CHECK (
        access_count >= 0
    )
);

CREATE INDEX idx_cache_expiration
ON response_cache(expires_at);

CREATE INDEX idx_cache_query_expiration
ON response_cache(query_id, expires_at);

-- ---------------------------------------------------------
-- 8. Cache access audit
-- ---------------------------------------------------------

CREATE TABLE cache_events (
    event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    cache_id BIGINT
        REFERENCES response_cache(cache_id)
        ON DELETE SET NULL,

    query_id BIGINT NOT NULL
        REFERENCES queries(query_id),

    event_type VARCHAR(30) NOT NULL,

    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_cache_event CHECK (
        event_type IN (
            'hit',
            'miss',
            'write',
            'invalidate',
            'expire',
            'refresh'
        )
    )
);

CREATE INDEX idx_cache_events_query
ON cache_events(query_id, occurred_at DESC);

-- ---------------------------------------------------------
-- 9. Request deduplication registry
-- ---------------------------------------------------------

CREATE TABLE active_requests (
    request_key VARCHAR(255) PRIMARY KEY,

    query_id BIGINT NOT NULL
        REFERENCES queries(query_id),

    request_id BIGINT NOT NULL
        REFERENCES api_requests(request_id),

    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_active_requests_query
ON active_requests(query_id);

-- ---------------------------------------------------------
-- 10. Request state transition validation
-- ---------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_request_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'UPDATE' THEN

        IF OLD.status IN (
            'success',
            'error',
            'cancelled'
        ) AND NEW.status <> OLD.status THEN

            IF NOT (
                OLD.status = 'error'
                AND NEW.status = 'loading'
            ) THEN

                RAISE EXCEPTION
                    'Invalid request state transition: % to %',
                    OLD.status,
                    NEW.status;

            END IF;
        END IF;

        IF NEW.status = 'success'
           AND NEW.http_status_code IS NOT NULL
           AND NEW.http_status_code NOT BETWEEN 200 AND 299
        THEN
            RAISE EXCEPTION
                'Successful requests require a 2xx HTTP status.';
        END IF;

        IF NEW.status = 'error'
           AND NEW.error_message IS NULL
        THEN
            RAISE EXCEPTION
                'Failed requests require an error message.';
        END IF;

    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_request_transition
BEFORE UPDATE ON api_requests
FOR EACH ROW
EXECUTE FUNCTION validate_request_transition();

-- ---------------------------------------------------------
-- 11. Cache expiration cleanup
-- ---------------------------------------------------------

CREATE OR REPLACE FUNCTION remove_expired_cache()
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    removed_count INTEGER;
BEGIN
    DELETE FROM response_cache
    WHERE expires_at <= NOW();

    GET DIAGNOSTICS removed_count = ROW_COUNT;

    RETURN removed_count;
END;
$$;

-- ---------------------------------------------------------
-- 12. Cache retrieval
-- ---------------------------------------------------------

CREATE OR REPLACE FUNCTION get_cached_response(
    p_query_id BIGINT,
    p_cache_key VARCHAR
)
RETURNS JSONB
LANGUAGE plpgsql
AS $$
DECLARE
    cached_data JSONB;
    cached_id BIGINT;
BEGIN
    SELECT cache_id, response_data
    INTO cached_id, cached_data
    FROM response_cache
    WHERE query_id = p_query_id
      AND cache_key = p_cache_key
      AND expires_at > NOW()
    FOR UPDATE;

    IF NOT FOUND THEN

        INSERT INTO cache_events (
            query_id,
            event_type
        )
        VALUES (
            p_query_id,
            'miss'
        );

        RETURN NULL;
    END IF;

    UPDATE response_cache
    SET
        last_accessed_at = NOW(),
        access_count = access_count + 1
    WHERE cache_id = cached_id;

    INSERT INTO cache_events (
        cache_id,
        query_id,
        event_type
    )
    VALUES (
        cached_id,
        p_query_id,
        'hit'
    );

    RETURN cached_data;
END;
$$;

-- ---------------------------------------------------------
-- 13. Cache write or refresh
-- ---------------------------------------------------------

CREATE OR REPLACE FUNCTION store_cached_response(
    p_query_id BIGINT,
    p_cache_key VARCHAR,
    p_response JSONB,
    p_ttl_seconds INTEGER
)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    new_cache_id BIGINT;
BEGIN
    IF p_ttl_seconds <= 0 OR p_ttl_seconds > 86400 THEN
        RAISE EXCEPTION
            'Cache TTL must be between 1 and 86400 seconds.';
    END IF;

    INSERT INTO response_cache (
        query_id,
        cache_key,
        response_data,
        created_at,
        expires_at
    )
    VALUES (
        p_query_id,
        p_cache_key,
        p_response,
        NOW(),
        NOW() + make_interval(secs => p_ttl_seconds)
    )
    ON CONFLICT (query_id, cache_key)
    DO UPDATE SET
        response_data = EXCLUDED.response_data,
        created_at = NOW(),
        expires_at = EXCLUDED.expires_at,
        last_accessed_at = NOW(),
        access_count = 0
    RETURNING cache_id INTO new_cache_id;

    INSERT INTO cache_events (
        cache_id,
        query_id,
        event_type
    )
    VALUES (
        new_cache_id,
        p_query_id,
        'write'
    );

    RETURN new_cache_id;
END;
$$;

-- ---------------------------------------------------------
-- 14. Cache invalidation
-- ---------------------------------------------------------

CREATE OR REPLACE PROCEDURE invalidate_query_cache(
    p_query_id BIGINT
)
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO cache_events (
        query_id,
        event_type
    )
    SELECT
        query_id,
        'invalidate'
    FROM response_cache
    WHERE query_id = p_query_id;

    DELETE FROM response_cache
    WHERE query_id = p_query_id;
END;
$$;

-- ---------------------------------------------------------
-- 15. Request lifecycle creation
-- ---------------------------------------------------------

CREATE OR REPLACE FUNCTION start_api_request(
    p_query_id BIGINT,
    p_request_key VARCHAR
)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    new_request_id BIGINT;
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM queries q
        JOIN application_clients c
          ON c.client_id = q.client_id
        JOIN api_endpoints e
          ON e.endpoint_id = q.endpoint_id
        JOIN api_services s
          ON s.service_id = e.service_id
        WHERE q.query_id = p_query_id
          AND q.enabled = TRUE
          AND c.is_active = TRUE
          AND e.is_active = TRUE
          AND s.is_active = TRUE
    ) THEN
        RAISE EXCEPTION
            'Query is disabled or its API configuration is inactive.';
    END IF;

    INSERT INTO api_requests (
        query_id,
        request_key,
        status,
        started_at
    )
    VALUES (
        p_query_id,
        p_request_key,
        'loading',
        NOW()
    )
    RETURNING request_id INTO new_request_id;

    RETURN new_request_id;
END;
$$;

-- ---------------------------------------------------------
-- 16. Request completion
-- ---------------------------------------------------------

CREATE OR REPLACE PROCEDURE complete_api_request(
    p_request_id BIGINT,
    p_status_code INTEGER,
    p_response JSONB,
    p_duration_ms NUMERIC
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF p_status_code NOT BETWEEN 200 AND 299 THEN
        RAISE EXCEPTION
            'Completion requires an HTTP 2xx response.';
    END IF;

    UPDATE api_requests
    SET
        status = 'success',
        http_status_code = p_status_code,
        response_body = p_response,
        completed_at = NOW(),
        response_time_ms = p_duration_ms,
        error_message = NULL,
        error_type = NULL
    WHERE request_id = p_request_id
      AND status = 'loading';

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Request does not exist or is not loading.';
    END IF;

    DELETE FROM active_requests
    WHERE request_id = p_request_id;
END;
$$;

-- ---------------------------------------------------------
-- 17. Request failure
-- ---------------------------------------------------------

CREATE OR REPLACE PROCEDURE fail_api_request(
    p_request_id BIGINT,
    p_category error_category,
    p_message TEXT,
    p_status_code INTEGER DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF p_message IS NULL OR length(trim(p_message)) = 0 THEN
        RAISE EXCEPTION
            'Failure message cannot be empty.';
    END IF;

    UPDATE api_requests
    SET
        status = 'error',
        error_type = p_category,
        error_message = p_message,
        http_status_code = p_status_code,
        completed_at = NOW()
    WHERE request_id = p_request_id
      AND status = 'loading';

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Request does not exist or is not loading.';
    END IF;

    DELETE FROM active_requests
    WHERE request_id = p_request_id;
END;
$$;

-- ---------------------------------------------------------
-- 18. Seed realistic API services
-- ---------------------------------------------------------

INSERT INTO api_services (
    service_name,
    base_url
)
VALUES
(
    'User Management API',
    'https://api.example.com'
),
(
    'Inventory API',
    'https://inventory.example.com'
);

INSERT INTO api_endpoints (
    service_id,
    endpoint_path,
    method,
    timeout_ms,
    cache_ttl_seconds,
    maximum_retries
)
VALUES
(
    1,
    '/users',
    'GET',
    5000,
    60,
    2
),
(
    1,
    '/users/profile',
    'GET',
    3000,
    120,
    1
),
(
    1,
    '/users',
    'POST',
    5000,
    0,
    0
),
(
    2,
    '/products',
    'GET',
    8000,
    30,
    3
);

INSERT INTO application_clients (
    client_name,
    environment
)
VALUES
('React Dashboard', 'development'),
('Enterprise Portal', 'production');

INSERT INTO queries (
    client_id,
    endpoint_id,
    query_key,
    parameters,
    policy
)
VALUES
(
    1,
    1,
    'users-list',
    '{"page":1,"limit":20}',
    'cache_first'
),
(
    1,
    2,
    'user-profile',
    '{"userId":1}',
    'stale_while_revalidate'
),
(
    2,
    4,
    'product-list',
    '{"category":"electronics"}',
    'network_first'
);

-- ---------------------------------------------------------
-- 19. Successful request
-- ---------------------------------------------------------

INSERT INTO api_requests (
    query_id,
    request_key,
    status,
    started_at,
    completed_at,
    http_status_code,
    response_body,
    response_time_ms
)
VALUES (
    1,
    'users-page-1',
    'success',
    NOW() - INTERVAL '200 milliseconds',
    NOW(),
    200,
    '[
        {"id":1,"name":"Aarav"},
        {"id":2,"name":"Meera"}
    ]'::JSONB,
    125.5
);

-- ---------------------------------------------------------
-- 20. Failed request
-- ---------------------------------------------------------

INSERT INTO api_requests (
    query_id,
    request_key,
    status,
    started_at,
    completed_at,
    http_status_code,
    error_type,
    error_message,
    response_time_ms
)
VALUES (
    1,
    'users-server-failure',
    'error',
    NOW() - INTERVAL '3 seconds',
    NOW(),
    503,
    'server',
    'Upstream service unavailable.',
    3000
);

-- ---------------------------------------------------------
-- 21. Cancelled request
-- ---------------------------------------------------------

INSERT INTO api_requests (
    query_id,
    request_key,
    status,
    started_at,
    completed_at,
    error_type,
    error_message
)
VALUES (
    2,
    'profile-cancelled',
    'cancelled',
    NOW() - INTERVAL '2 seconds',
    NOW(),
    'cancelled',
    'Request cancelled after component cleanup.'
);

-- ---------------------------------------------------------
-- 22. Seed response cache
-- ---------------------------------------------------------

SELECT store_cached_response(
    1,
    'users-page-1',
    '[
        {"id":1,"name":"Aarav"},
        {"id":2,"name":"Meera"}
    ]'::JSONB,
    60
);

SELECT store_cached_response(
    2,
    'profile-user-1',
    '{"id":1,"name":"Aarav","role":"Developer"}'::JSONB,
    120
);

-- ---------------------------------------------------------
-- 23. Seed active request
-- ---------------------------------------------------------

INSERT INTO api_requests (
    query_id,
    request_key,
    status,
    started_at
)
VALUES (
    3,
    'products-active-request',
    'loading',
    NOW()
);

INSERT INTO active_requests (
    request_key,
    query_id,
    request_id
)
SELECT
    request_key,
    query_id,
    request_id
FROM api_requests
WHERE request_key = 'products-active-request';

COMMIT;

-- =========================================================
-- REPORTING AND WORKFLOW QUERIES
-- =========================================================

-- ---------------------------------------------------------
-- 24. Retrieve registered endpoints
-- ---------------------------------------------------------

SELECT
    s.service_name,
    e.endpoint_path,
    e.method,
    e.timeout_ms,
    e.cache_ttl_seconds,
    e.maximum_retries
FROM api_services s
JOIN api_endpoints e
    ON e.service_id = s.service_id
ORDER BY s.service_name, e.endpoint_path;

-- ---------------------------------------------------------
-- 25. Retrieve query definitions
-- ---------------------------------------------------------

SELECT
    q.query_id,
    c.client_name,
    q.query_key,
    e.endpoint_path,
    e.method,
    q.policy,
    q.parameters
FROM queries q
JOIN application_clients c
    ON c.client_id = q.client_id
JOIN api_endpoints e
    ON e.endpoint_id = q.endpoint_id
ORDER BY q.query_id;

-- ---------------------------------------------------------
-- 26. Request state reporting
-- ---------------------------------------------------------

SELECT
    status,
    COUNT(*) AS total_requests
FROM api_requests
GROUP BY status
ORDER BY status;

-- ---------------------------------------------------------
-- 27. API performance evaluation
-- ---------------------------------------------------------

SELECT
    q.query_key,
    COUNT(r.request_id) AS total_requests,
    ROUND(
        AVG(r.response_time_ms),
        2
    ) AS average_response_ms,
    ROUND(
        MAX(r.response_time_ms),
        2
    ) AS maximum_response_ms,
    COUNT(*) FILTER (
        WHERE r.status = 'error'
    ) AS failures,
    COUNT(*) FILTER (
        WHERE r.is_cache_hit = TRUE
    ) AS cache_hits
FROM queries q
LEFT JOIN api_requests r
    ON r.query_id = q.query_id
GROUP BY q.query_id, q.query_key
ORDER BY q.query_key;

-- ---------------------------------------------------------
-- 28. Cache effectiveness
-- ---------------------------------------------------------

SELECT
    q.query_key,
    COUNT(ce.event_id) FILTER (
        WHERE ce.event_type = 'hit'
    ) AS cache_hits,
    COUNT(ce.event_id) FILTER (
        WHERE ce.event_type = 'miss'
    ) AS cache_misses,
    ROUND(
        100.0 *
        COUNT(ce.event_id) FILTER (
            WHERE ce.event_type = 'hit'
        ) /
        NULLIF(
            COUNT(ce.event_id) FILTER (
                WHERE ce.event_type IN ('hit', 'miss')
            ),
            0
        ),
        2
    ) AS hit_percentage
FROM queries q
LEFT JOIN cache_events ce
    ON ce.query_id = q.query_id
GROUP BY q.query_id, q.query_key;

-- ---------------------------------------------------------
-- 29. Identify expired cache records
-- ---------------------------------------------------------

SELECT
    cache_id,
    query_id,
    cache_key,
    expires_at
FROM response_cache
WHERE expires_at <= NOW();

-- ---------------------------------------------------------
-- 30. Identify active requests
-- ---------------------------------------------------------

SELECT
    ar.request_key,
    q.query_key,
    r.started_at,
    NOW() - r.started_at AS elapsed_time
FROM active_requests ar
JOIN api_requests r
    ON r.request_id = ar.request_id
JOIN queries q
    ON q.query_id = ar.query_id
ORDER BY r.started_at;

-- ---------------------------------------------------------
-- 31. CTE-based error analysis
-- ---------------------------------------------------------

WITH request_metrics AS (
    SELECT
        query_id,
        COUNT(*) AS total_requests,
        COUNT(*) FILTER (
            WHERE status = 'success'
        ) AS successful_requests,
        COUNT(*) FILTER (
            WHERE status = 'error'
        ) AS failed_requests
    FROM api_requests
    GROUP BY query_id
)
SELECT
    q.query_key,
    rm.total_requests,
    rm.successful_requests,
    rm.failed_requests,
    ROUND(
        100.0 * rm.failed_requests /
        NULLIF(rm.total_requests, 0),
        2
    ) AS failure_percentage
FROM request_metrics rm
JOIN queries q
    ON q.query_id = rm.query_id
ORDER BY failure_percentage DESC;

-- ---------------------------------------------------------
-- 32. Determine whether a query is eligible for caching
-- ---------------------------------------------------------

SELECT
    q.query_id,
    q.query_key,
    e.method,
    e.is_cacheable,
    e.cache_ttl_seconds,
    CASE
        WHEN q.enabled = FALSE
            THEN 'DISABLED'
        WHEN e.is_active = FALSE
            THEN 'ENDPOINT_INACTIVE'
        WHEN e.method <> 'GET'
            THEN 'NON_GET_REQUEST'
        WHEN e.is_cacheable = FALSE
            THEN 'CACHE_DISABLED'
        WHEN e.cache_ttl_seconds = 0
            THEN 'ZERO_TTL'
        ELSE 'CACHE_ELIGIBLE'
    END AS eligibility
FROM queries q
JOIN api_endpoints e
    ON e.endpoint_id = q.endpoint_id;

-- ---------------------------------------------------------
-- 33. Demonstrate transactional cache invalidation
-- ---------------------------------------------------------

BEGIN;

CALL invalidate_query_cache(1);

COMMIT;

-- ---------------------------------------------------------
-- 34. Demonstrate cache retrieval
-- ---------------------------------------------------------

SELECT get_cached_response(
    2,
    'profile-user-1'
) AS cached_profile;

-- ---------------------------------------------------------
-- 35. Demonstrate successful request processing
-- ---------------------------------------------------------

BEGIN;

DO $$
DECLARE
    new_id BIGINT;
BEGIN
    new_id := start_api_request(
        1,
        'transactional-users-request'
    );

    CALL complete_api_request(
        new_id,
        200,
        '{"users":[{"id":10,"name":"Riya"}]}'::JSONB,
        85.5
    );
END;
$$;

COMMIT;

-- ---------------------------------------------------------
-- 36. Demonstrate failed request processing
-- ---------------------------------------------------------

BEGIN;

DO $$
DECLARE
    new_id BIGINT;
BEGIN
    new_id := start_api_request(
        1,
        'transactional-failed-request'
    );

    CALL fail_api_request(
        new_id,
        'server',
        'Upstream service unavailable.',
        503
    );
END;
$$;

COMMIT;

-- ---------------------------------------------------------
-- 37. Remove expired cache entries
-- ---------------------------------------------------------

SELECT remove_expired_cache() AS removed_cache_entries;

-- ---------------------------------------------------------
-- 38. Query status distribution by client
-- ---------------------------------------------------------

SELECT
    c.client_name,
    r.status,
    COUNT(*) AS request_count
FROM application_clients c
JOIN queries q
    ON q.client_id = c.client_id
JOIN api_requests r
    ON r.query_id = q.query_id
GROUP BY c.client_name, r.status
ORDER BY c.client_name, r.status;

-- ---------------------------------------------------------
-- 39. Recent request history
-- ---------------------------------------------------------

SELECT
    r.request_id,
    q.query_key,
    r.request_key,
    r.status,
    r.http_status_code,
    r.response_time_ms,
    r.error_type,
    r.started_at,
    r.completed_at
FROM api_requests r
JOIN queries q
    ON q.query_id = r.query_id
ORDER BY r.started_at DESC
LIMIT 50;

-- ---------------------------------------------------------
-- 40. Final integrity checks
-- ---------------------------------------------------------

SELECT
    COUNT(*) AS invalid_successful_requests
FROM api_requests
WHERE status = 'success'
  AND http_status_code IS NOT NULL
  AND http_status_code NOT BETWEEN 200 AND 299;

SELECT
    COUNT(*) AS invalid_failed_requests
FROM api_requests
WHERE status = 'error'
  AND error_message IS NULL;

SELECT
    COUNT(*) AS expired_cache_entries
FROM response_cache
WHERE expires_at <= NOW();
