DROP SCHEMA IF EXISTS http_api_demo CASCADE;
CREATE SCHEMA http_api_demo;

SET search_path TO http_api_demo, public;

CREATE TYPE http_method AS ENUM (
    'GET',
    'POST',
    'PUT',
    'PATCH',
    'DELETE'
);

CREATE TYPE request_state AS ENUM (
    'created',
    'validated',
    'sent',
    'received',
    'failed'
);

CREATE TYPE response_class AS ENUM (
    'informational',
    'success',
    'redirect',
    'client_error',
    'server_error'
);

CREATE TABLE api_clients (
    client_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    client_name TEXT NOT NULL UNIQUE,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE api_requests (
    request_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    client_id BIGINT NOT NULL REFERENCES api_clients(client_id),
    method http_method NOT NULL,
    endpoint TEXT NOT NULL,
    request_headers JSONB NOT NULL DEFAULT '{}'::jsonb,
    request_body JSONB,
    state request_state NOT NULL DEFAULT 'created',
    attempt_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    CONSTRAINT endpoint_not_blank CHECK (btrim(endpoint) <> ''),
    CONSTRAINT attempt_count_nonnegative CHECK (attempt_count >= 0)
);

CREATE TABLE api_responses (
    response_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    request_id BIGINT NOT NULL UNIQUE
        REFERENCES api_requests(request_id)
        ON DELETE CASCADE,
    status_code INTEGER NOT NULL,
    reason TEXT NOT NULL,
    response_headers JSONB NOT NULL DEFAULT '{}'::jsonb,
    response_body JSONB,
    duration_ms NUMERIC(12, 3),
    received_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_status_code CHECK (
        status_code BETWEEN 100 AND 599
    ),
    CONSTRAINT duration_nonnegative CHECK (
        duration_ms IS NULL OR duration_ms >= 0
    )
);

CREATE TABLE request_events (
    event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    request_id BIGINT NOT NULL
        REFERENCES api_requests(request_id)
        ON DELETE CASCADE,
    state request_state NOT NULL,
    event_message TEXT NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE api_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    policy_name TEXT NOT NULL UNIQUE,
    max_request_attempts INTEGER NOT NULL DEFAULT 3,
    timeout_ms INTEGER NOT NULL DEFAULT 5000,
    allow_get BOOLEAN NOT NULL DEFAULT TRUE,
    allow_post BOOLEAN NOT NULL DEFAULT TRUE,
    allow_put BOOLEAN NOT NULL DEFAULT TRUE,
    allow_patch BOOLEAN NOT NULL DEFAULT TRUE,
    allow_delete BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT positive_attempt_limit CHECK (
        max_request_attempts > 0
    ),
    CONSTRAINT positive_timeout CHECK (
        timeout_ms > 0
    )
);

CREATE TABLE status_rules (
    rule_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    policy_id BIGINT NOT NULL REFERENCES api_policies(policy_id)
        ON DELETE CASCADE,
    status_code INTEGER NOT NULL,
    acceptable BOOLEAN NOT NULL,
    retryable BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (policy_id, status_code),
    CONSTRAINT status_rule_range CHECK (
        status_code BETWEEN 100 AND 599
    )
);

CREATE INDEX idx_api_requests_client_created
    ON api_requests(client_id, created_at DESC);

CREATE INDEX idx_api_requests_state
    ON api_requests(state);

CREATE INDEX idx_api_responses_status
    ON api_responses(status_code);

CREATE INDEX idx_request_events_request_time
    ON request_events(request_id, occurred_at);

CREATE INDEX idx_api_requests_headers
    ON api_requests USING GIN(request_headers);

CREATE OR REPLACE FUNCTION classify_status(
    p_status INTEGER
)
RETURNS response_class
LANGUAGE plpgsql
IMMUTABLE
AS $$
BEGIN
    IF p_status BETWEEN 100 AND 199 THEN
        RETURN 'informational';
    ELSIF p_status BETWEEN 200 AND 299 THEN
        RETURN 'success';
    ELSIF p_status BETWEEN 300 AND 399 THEN
        RETURN 'redirect';
    ELSIF p_status BETWEEN 400 AND 499 THEN
        RETURN 'client_error';
    ELSIF p_status BETWEEN 500 AND 599 THEN
        RETURN 'server_error';
    END IF;

    RAISE EXCEPTION 'Invalid HTTP status: %', p_status;
END;
$$;

CREATE OR REPLACE FUNCTION is_retryable_status(
    p_status INTEGER
)
RETURNS BOOLEAN
LANGUAGE sql
IMMUTABLE
AS $$
    SELECT p_status IN (408, 429, 500, 502, 503, 504);
$$;

CREATE OR REPLACE FUNCTION validate_request_before_insert()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    header_name TEXT;
    header_value TEXT;
BEGIN
    IF NEW.endpoint !~ '^https?://'
       AND NEW.endpoint NOT LIKE '/%' THEN
        RAISE EXCEPTION
            'Endpoint must be an HTTP(S) URL or application path';
    END IF;

    IF NEW.attempt_count < 0 THEN
        RAISE EXCEPTION 'attempt_count cannot be negative';
    END IF;

    IF NEW.method IN ('GET', 'DELETE')
       AND NEW.request_body IS NOT NULL THEN
        RAISE EXCEPTION
            '% requests cannot contain a request body in this model',
            NEW.method;
    END IF;

    FOR header_name, header_value IN
        SELECT key, value
        FROM jsonb_each_text(NEW.request_headers)
    LOOP
        IF header_name ~ '[\r\n]'
           OR header_value ~ '[\r\n]' THEN
            RAISE EXCEPTION
                'CR/LF characters are forbidden in HTTP headers';
        END IF;
    END LOOP;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_request
BEFORE INSERT OR UPDATE ON api_requests
FOR EACH ROW
EXECUTE FUNCTION validate_request_before_insert();

CREATE OR REPLACE FUNCTION record_request_event()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO request_events (
            request_id,
            state,
            event_message
        )
        VALUES (
            NEW.request_id,
            NEW.state,
            'Request created'
        );
    ELSIF NEW.state IS DISTINCT FROM OLD.state THEN
        INSERT INTO request_events (
            request_id,
            state,
            event_message
        )
        VALUES (
            NEW.request_id,
            NEW.state,
            format(
                'Request state changed from %s to %s',
                OLD.state,
                NEW.state
            )
        );
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_request_state_event
AFTER INSERT OR UPDATE OF state ON api_requests
FOR EACH ROW
EXECUTE FUNCTION record_request_event();

CREATE OR REPLACE FUNCTION response_state_update()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE api_requests
    SET state = 'received',
        completed_at = NEW.received_at
    WHERE request_id = NEW.request_id;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_response_state
AFTER INSERT ON api_responses
FOR EACH ROW
EXECUTE FUNCTION response_state_update();

CREATE OR REPLACE FUNCTION evaluate_request(
    p_request_id BIGINT,
    p_policy_id BIGINT
)
RETURNS TABLE (
    request_id BIGINT,
    method http_method,
    status_code INTEGER,
    status_group response_class,
    acceptable BOOLEAN,
    retryable BOOLEAN,
    decision TEXT
)
LANGUAGE sql
AS $$
    SELECT
        r.request_id,
        r.method,
        s.status_code,
        classify_status(s.status_code),
        COALESCE(sr.acceptable, s.status_code BETWEEN 200 AND 299),
        COALESCE(
            sr.retryable,
            is_retryable_status(s.status_code)
        ),
        CASE
            WHEN COALESCE(
                sr.acceptable,
                s.status_code BETWEEN 200 AND 299
            )
            THEN 'accepted'
            WHEN COALESCE(
                sr.retryable,
                is_retryable_status(s.status_code)
            )
            AND r.attempt_count <
                p.max_request_attempts
            THEN 'retry'
            ELSE 'rejected'
        END
    FROM api_requests r
    JOIN api_responses s
        ON s.request_id = r.request_id
    JOIN api_policies p
        ON p.policy_id = p_policy_id
    LEFT JOIN status_rules sr
        ON sr.policy_id = p.policy_id
       AND sr.status_code = s.status_code
    WHERE r.request_id = p_request_id;
$$;

CREATE VIEW request_status_report AS
SELECT
    r.request_id,
    c.client_name,
    r.method,
    r.endpoint,
    r.state,
    r.attempt_count,
    resp.status_code,
    classify_status(resp.status_code) AS status_group,
    is_retryable_status(resp.status_code) AS retryable,
    resp.duration_ms,
    r.created_at,
    resp.received_at
FROM api_requests r
JOIN api_clients c
    ON c.client_id = r.client_id
LEFT JOIN api_responses resp
    ON resp.request_id = r.request_id;

CREATE VIEW endpoint_performance AS
SELECT
    endpoint,
    count(*) AS request_count,
    count(*) FILTER (
        WHERE resp.status_code BETWEEN 200 AND 299
    ) AS successful_requests,
    count(*) FILTER (
        WHERE resp.status_code BETWEEN 400 AND 499
    ) AS client_errors,
    count(*) FILTER (
        WHERE resp.status_code BETWEEN 500 AND 599
    ) AS server_errors,
    round(
        avg(resp.duration_ms)::numeric,
        3
    ) AS average_duration_ms
FROM api_requests r
LEFT JOIN api_responses resp
    ON resp.request_id = r.request_id
GROUP BY endpoint;

INSERT INTO api_clients (client_name)
VALUES
    ('web-frontend'),
    ('batch-worker'),
    ('mobile-client');

INSERT INTO api_policies (
    policy_name,
    max_request_attempts,
    timeout_ms,
    allow_get,
    allow_post,
    allow_put,
    allow_patch,
    allow_delete
)
VALUES
    ('standard-api', 3, 5000, TRUE, TRUE, TRUE, TRUE, TRUE),
    ('read-only-api', 2, 3000, TRUE, FALSE, FALSE, FALSE, FALSE);

INSERT INTO status_rules (
    policy_id,
    status_code,
    acceptable,
    retryable
)
SELECT policy_id, status_code, acceptable, retryable
FROM (
    SELECT
        policy_id,
        200 AS status_code,
        TRUE AS acceptable,
        FALSE AS retryable
    FROM api_policies
    WHERE policy_name = 'standard-api'

    UNION ALL

    SELECT
        policy_id,
        201,
        TRUE,
        FALSE
    FROM api_policies
    WHERE policy_name = 'standard-api'

    UNION ALL

    SELECT
        policy_id,
        204,
        TRUE,
        FALSE
    FROM api_policies
    WHERE policy_name = 'standard-api'

    UNION ALL

    SELECT
        policy_id,
        429,
        FALSE,
        TRUE
    FROM api_policies
    WHERE policy_name = 'standard-api'

    UNION ALL

    SELECT
        policy_id,
        503,
        FALSE,
        TRUE
    FROM api_policies
    WHERE policy_name = 'standard-api'

    UNION ALL

    SELECT
        policy_id,
        200,
        TRUE,
        FALSE
    FROM api_policies
    WHERE policy_name = 'read-only-api'
) rules;

INSERT INTO api_requests (
    client_id,
    method,
    endpoint,
    request_headers,
    request_body,
    state,
    attempt_count,
    sent_at
)
SELECT
    client_id,
    'GET',
    'https://api.example.test/users',
    '{"Accept":"application/json","X-Request-ID":"req-001"}',
    NULL,
    'sent',
    1,
    CURRENT_TIMESTAMP
FROM api_clients
WHERE client_name = 'web-frontend';

INSERT INTO api_responses (
    request_id,
    status_code,
    reason,
    response_headers,
    response_body,
    duration_ms
)
SELECT
    request_id,
    200,
    'OK',
    '{"Content-Type":"application/json"}',
    '{"users":[{"id":1,"name":"Anita"}]}',
    84.500
FROM api_requests
WHERE endpoint = 'https://api.example.test/users';

INSERT INTO api_requests (
    client_id,
    method,
    endpoint,
    request_headers,
    request_body,
    state,
    attempt_count,
    sent_at
)
SELECT
    client_id,
    'POST',
    'https://api.example.test/users',
    '{"Accept":"application/json","Content-Type":"application/json"}',
    '{"name":"Priya"}',
    'sent',
    1,
    CURRENT_TIMESTAMP
FROM api_clients
WHERE client_name = 'web-frontend';

INSERT INTO api_responses (
    request_id,
    status_code,
    reason,
    response_headers,
    response_body,
    duration_ms
)
SELECT
    request_id,
    201,
    'Created',
    '{"Content-Type":"application/json"}',
    '{"id":3,"name":"Priya"}',
    112.200
FROM api_requests
WHERE method = 'POST'
  AND endpoint = 'https://api.example.test/users';

INSERT INTO api_requests (
    client_id,
    method,
    endpoint,
    request_headers,
    request_body,
    state,
    attempt_count,
    sent_at
)
SELECT
    client_id,
    'GET',
    'https://api.example.test/missing',
    '{"Accept":"application/json"}',
    NULL,
    'sent',
    1,
    CURRENT_TIMESTAMP
FROM api_clients
WHERE client_name = 'batch-worker';

INSERT INTO api_responses (
    request_id,
    status_code,
    reason,
    response_headers,
    response_body,
    duration_ms
)
SELECT
    request_id,
    404,
    'Not Found',
    '{"Content-Type":"application/json"}',
    '{"error":"resource_not_found"}',
    41.700
FROM api_requests
WHERE endpoint = 'https://api.example.test/missing';

INSERT INTO api_requests (
    client_id,
    method,
    endpoint,
    request_headers,
    request_body,
    state,
    attempt_count,
    sent_at
)
SELECT
    client_id,
    'GET',
    'https://api.example.test/users',
    '{"Accept":"application/json"}',
    NULL,
    'sent',
    2,
    CURRENT_TIMESTAMP
FROM api_clients
WHERE client_name = 'batch-worker';

INSERT INTO api_responses (
    request_id,
    status_code,
    reason,
    response_headers,
    response_body,
    duration_ms
)
SELECT
    request_id,
    503,
    'Service Unavailable',
    '{"Retry-After":"2"}',
    '{"error":"temporarily_unavailable"}',
    5001.900
FROM api_requests
WHERE client_id = (
    SELECT client_id
    FROM api_clients
    WHERE client_name = 'batch-worker'
)
AND attempt_count = 2;

-- Retrieval: inspect the complete request/response lifecycle.
SELECT *
FROM request_status_report
ORDER BY request_id;

-- Status-code evaluation.
SELECT
    status_code,
    classify_status(status_code) AS status_group,
    is_retryable_status(status_code) AS retryable
FROM (
    VALUES
        (200),
        (201),
        (301),
        (404),
        (429),
        (503)
) AS codes(status_code);

-- Policy-based eligibility for a specific request.
SELECT *
FROM evaluate_request(
    (
        SELECT request_id
        FROM api_requests
        WHERE endpoint = 'https://api.example.test/missing'
        LIMIT 1
    ),
    (
        SELECT policy_id
        FROM api_policies
        WHERE policy_name = 'standard-api'
    )
);

-- Aggregation: endpoint reliability and latency.
SELECT *
FROM endpoint_performance
ORDER BY request_count DESC, endpoint;

-- JSON header inspection.
SELECT
    request_id,
    request_headers ->> 'Accept' AS accepted_media_type,
    request_headers ->> 'X-Request-ID' AS request_trace_id
FROM api_requests
ORDER BY request_id;

-- Failure reporting.
SELECT
    request_id,
    method,
    endpoint,
    status_code,
    reason
FROM request_status_report
WHERE status_code >= 400
ORDER BY request_id;

-- Transactional state change: mark a failed request as requiring retry.
BEGIN;

WITH candidate AS (
    SELECT request_id
    FROM api_requests r
    JOIN api_responses resp
        ON resp.request_id = r.request_id
    WHERE resp.status_code IN (408, 429, 500, 502, 503, 504)
      AND r.attempt_count < (
          SELECT max_request_attempts
          FROM api_policies
          WHERE policy_name = 'standard-api'
      )
    ORDER BY r.created_at
    FOR UPDATE OF r
    LIMIT 1
)
UPDATE api_requests r
SET state = 'validated',
    attempt_count = attempt_count + 1
FROM candidate c
WHERE r.request_id = c.request_id;

COMMIT;

-- CTE reporting: compare successful and unsuccessful requests.
WITH classified AS (
    SELECT
        endpoint,
        CASE
            WHEN status_code BETWEEN 200 AND 299
                THEN 'success'
            WHEN status_code BETWEEN 400 AND 499
                THEN 'client_error'
            WHEN status_code BETWEEN 500 AND 599
                THEN 'server_error'
            ELSE 'other'
        END AS result_group
    FROM request_status_report
    WHERE status_code IS NOT NULL
)
SELECT
    endpoint,
    count(*) FILTER (
        WHERE result_group = 'success'
    ) AS successes,
    count(*) FILTER (
        WHERE result_group = 'client_error'
    ) AS client_errors,
    count(*) FILTER (
        WHERE result_group = 'server_error'
    ) AS server_errors
FROM classified
GROUP BY endpoint
ORDER BY endpoint;
