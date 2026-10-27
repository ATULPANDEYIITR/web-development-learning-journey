DROP SCHEMA IF EXISTS browser_api_demo CASCADE;
CREATE SCHEMA browser_api_demo;

SET search_path = browser_api_demo;

CREATE TYPE storage_scope AS ENUM ('local', 'session');
CREATE TYPE cookie_same_site AS ENUM ('Strict', 'Lax', 'None');
CREATE TYPE navigation_action AS ENUM ('push_state', 'replace_state', 'back', 'forward');
CREATE TYPE navigation_result AS ENUM ('allowed', 'blocked');

CREATE TABLE repositories (
    repository_id BIGSERIAL PRIMARY KEY,
    repository_name TEXT NOT NULL UNIQUE,
    origin TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (repository_name <> ''),
    CHECK (origin ~ '^https://[^/]+$')
);

CREATE TABLE browser_storage (
    storage_id BIGSERIAL PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repositories(repository_id)
        ON DELETE CASCADE,
    scope storage_scope NOT NULL,
    storage_key TEXT NOT NULL,
    storage_value TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (repository_id, scope, storage_key),
    CHECK (storage_key <> '')
);

CREATE INDEX idx_browser_storage_scope
    ON browser_storage(repository_id, scope);

CREATE TABLE browser_cookies (
    cookie_id BIGSERIAL PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repositories(repository_id)
        ON DELETE CASCADE,
    cookie_name TEXT NOT NULL,
    cookie_value TEXT NOT NULL,
    path TEXT NOT NULL DEFAULT '/',
    secure BOOLEAN NOT NULL DEFAULT TRUE,
    http_only BOOLEAN NOT NULL DEFAULT TRUE,
    same_site cookie_same_site NOT NULL DEFAULT 'Lax',
    max_age INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (repository_id, cookie_name, path),
    CHECK (cookie_name <> ''),
    CHECK (path LIKE '/%'),
    CHECK (max_age IS NULL OR max_age >= 0),
    CHECK (same_site <> 'None' OR secure = TRUE)
);

CREATE INDEX idx_browser_cookies_repository
    ON browser_cookies(repository_id);

CREATE TABLE navigation_sessions (
    navigation_session_id BIGSERIAL PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repositories(repository_id)
        ON DELETE CASCADE,
    session_key UUID NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE history_entries (
    history_entry_id BIGSERIAL PRIMARY KEY,
    navigation_session_id BIGINT NOT NULL
        REFERENCES navigation_sessions(navigation_session_id)
        ON DELETE CASCADE,
    position INTEGER NOT NULL,
    url TEXT NOT NULL,
    state JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (navigation_session_id, position),
    CHECK (position >= 0),
    CHECK (url ~ '^https://[^/]+/')
);

CREATE INDEX idx_history_session_position
    ON history_entries(navigation_session_id, position);

CREATE TABLE url_operations (
    operation_id BIGSERIAL PRIMARY KEY,
    navigation_session_id BIGINT NOT NULL
        REFERENCES navigation_sessions(navigation_session_id)
        ON DELETE CASCADE,
    action navigation_action NOT NULL,
    source_url TEXT,
    target_url TEXT,
    result navigation_result NOT NULL,
    reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_url_operations_session_time
    ON url_operations(navigation_session_id, created_at DESC);

CREATE OR REPLACE FUNCTION validate_cookie()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.cookie_name = '' THEN
        RAISE EXCEPTION 'Cookie name cannot be empty';
    END IF;

    IF NEW.path NOT LIKE '/%' THEN
        RAISE EXCEPTION 'Cookie path must start with /';
    END IF;

    IF NEW.same_site = 'None' AND NEW.secure = FALSE THEN
        RAISE EXCEPTION
            'SameSite=None requires Secure';
    END IF;

    NEW.updated_at := now();

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_cookie
BEFORE INSERT OR UPDATE ON browser_cookies
FOR EACH ROW
EXECUTE FUNCTION validate_cookie();

CREATE OR REPLACE FUNCTION validate_storage_value()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    total_size BIGINT;
BEGIN
    /*
     * This example applies a deliberately explicit 5 KiB logical quota.
     * Real browser quota calculations are implementation-dependent.
     */
    SELECT COALESCE(
        SUM(length(storage_key) + length(storage_value)),
        0
    )
    INTO total_size
    FROM browser_storage
    WHERE repository_id = NEW.repository_id
      AND scope = NEW.scope
      AND storage_id <> COALESCE(NEW.storage_id, -1);

    IF total_size
        + length(NEW.storage_key)
        + length(NEW.storage_value) > 5120
    THEN
        RAISE EXCEPTION
            'Logical storage quota exceeded for % storage',
            NEW.scope;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_storage_value
BEFORE INSERT OR UPDATE ON browser_storage
FOR EACH ROW
EXECUTE FUNCTION validate_storage_value();

CREATE OR REPLACE FUNCTION same_origin(
    p_origin TEXT,
    p_target TEXT
)
RETURNS BOOLEAN
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
    origin_host TEXT;
    target_host TEXT;
BEGIN
    IF p_origin IS NULL OR p_target IS NULL THEN
        RETURN FALSE;
    END IF;

    IF p_origin !~ '^https://[^/]+$'
       OR p_target !~ '^https://[^/]+/'
    THEN
        RETURN FALSE;
    END IF;

    origin_host := regexp_replace(
        p_origin,
        '^https://([^/]+)$',
        '\1'
    );

    target_host := regexp_replace(
        p_target,
        '^https://([^/]+)/.*$',
        '\1'
    );

    RETURN origin_host = target_host;
END;
$$;

CREATE OR REPLACE VIEW storage_state AS
SELECT
    r.repository_name,
    bs.scope,
    bs.storage_key,
    bs.storage_value,
    bs.updated_at
FROM browser_storage bs
JOIN repositories r
    ON r.repository_id = bs.repository_id;

CREATE OR REPLACE VIEW cookie_security_report AS
SELECT
    r.repository_name,
    c.cookie_name,
    c.secure,
    c.http_only,
    c.same_site,
    CASE
        WHEN c.same_site = 'None' AND NOT c.secure
            THEN 'invalid'
        WHEN c.cookie_name ILIKE '%session%'
             AND NOT c.secure
            THEN 'session cookie missing Secure'
        WHEN c.cookie_name ILIKE '%session%'
             AND NOT c.http_only
            THEN 'session cookie exposed to JavaScript'
        ELSE 'acceptable'
    END AS security_status
FROM browser_cookies c
JOIN repositories r
    ON r.repository_id = c.repository_id;

CREATE OR REPLACE VIEW navigation_report AS
SELECT
    r.repository_name,
    ns.session_key,
    COUNT(he.history_entry_id) AS history_length,
    MIN(he.position) AS first_position,
    MAX(he.position) AS last_position
FROM navigation_sessions ns
JOIN repositories r
    ON r.repository_id = ns.repository_id
LEFT JOIN history_entries he
    ON he.navigation_session_id = ns.navigation_session_id
GROUP BY
    r.repository_name,
    ns.session_key;

INSERT INTO repositories (
    repository_name,
    origin
)
VALUES
    ('Portal', 'https://portal.example.test'),
    ('Storefront', 'https://store.example.test');

INSERT INTO browser_storage (
    repository_id,
    scope,
    storage_key,
    storage_value
)
SELECT
    repository_id,
    'local',
    'theme',
    'dark'
FROM repositories
WHERE repository_name = 'Portal';

INSERT INTO browser_storage (
    repository_id,
    scope,
    storage_key,
    storage_value
)
SELECT
    repository_id,
    'local',
    'language',
    'en'
FROM repositories
WHERE repository_name = 'Portal';

INSERT INTO browser_storage (
    repository_id,
    scope,
    storage_key,
    storage_value
)
SELECT
    repository_id,
    'session',
    'checkoutStep',
    'payment'
FROM repositories
WHERE repository_name = 'Storefront';

INSERT INTO browser_cookies (
    repository_id,
    cookie_name,
    cookie_value,
    path,
    secure,
    http_only,
    same_site,
    max_age
)
SELECT
    repository_id,
    'session_id',
    'opaque-server-token',
    '/',
    TRUE,
    TRUE,
    'Lax',
    NULL
FROM repositories
WHERE repository_name = 'Portal';

INSERT INTO browser_cookies (
    repository_id,
    cookie_name,
    cookie_value,
    path,
    secure,
    http_only,
    same_site,
    max_age
)
SELECT
    repository_id,
    'consent',
    'essential',
    '/',
    TRUE,
    FALSE,
    'Lax',
    86400
FROM repositories
WHERE repository_name = 'Portal';

INSERT INTO navigation_sessions (
    repository_id,
    session_key
)
SELECT
    repository_id,
    '11111111-1111-1111-1111-111111111111'
FROM repositories
WHERE repository_name = 'Portal';

INSERT INTO history_entries (
    navigation_session_id,
    position,
    url,
    state
)
SELECT
    navigation_session_id,
    0,
    'https://portal.example.test/dashboard',
    '{"tab":"home"}'
FROM navigation_sessions
WHERE session_key =
    '11111111-1111-1111-1111-111111111111';

INSERT INTO history_entries (
    navigation_session_id,
    position,
    url,
    state
)
SELECT
    navigation_session_id,
    1,
    'https://portal.example.test/dashboard?tab=activity',
    '{"tab":"activity"}'
FROM navigation_sessions
WHERE session_key =
    '11111111-1111-1111-1111-111111111111';

INSERT INTO history_entries (
    navigation_session_id,
    position,
    url,
    state
)
SELECT
    navigation_session_id,
    2,
    'https://portal.example.test/dashboard?tab=settings',
    '{"tab":"settings"}'
FROM navigation_sessions
WHERE session_key =
    '11111111-1111-1111-1111-111111111111';

INSERT INTO url_operations (
    navigation_session_id,
    action,
    source_url,
    target_url,
    result,
    reason
)
SELECT
    navigation_session_id,
    'push_state',
    'https://portal.example.test/dashboard',
    'https://portal.example.test/dashboard?tab=activity',
    'allowed',
    'Same-origin application navigation'
FROM navigation_sessions
WHERE session_key =
    '11111111-1111-1111-1111-111111111111';

INSERT INTO url_operations (
    navigation_session_id,
    action,
    source_url,
    target_url,
    result,
    reason
)
SELECT
    navigation_session_id,
    'push_state',
    'https://portal.example.test/dashboard',
    'https://attacker.example.test/login',
    'blocked',
    'Cross-origin target rejected by application policy'
FROM navigation_sessions
WHERE session_key =
    '11111111-1111-1111-1111-111111111111';

-- Retrieval: persistent and session-scoped values remain distinct.
SELECT *
FROM storage_state
ORDER BY repository_name, scope, storage_key;

-- Validation: identify cookies that violate application security expectations.
SELECT *
FROM cookie_security_report
ORDER BY repository_name, cookie_name;

-- Aggregation: compare storage usage by repository and scope.
SELECT
    r.repository_name,
    bs.scope,
    COUNT(*) AS item_count,
    SUM(length(bs.storage_key) + length(bs.storage_value)) AS logical_size
FROM browser_storage bs
JOIN repositories r
    ON r.repository_id = bs.repository_id
GROUP BY r.repository_name, bs.scope
ORDER BY r.repository_name, bs.scope;

-- History reporting: determine the number of entries per navigation session.
SELECT *
FROM navigation_report
ORDER BY repository_name;

-- Eligibility-style navigation evaluation.
SELECT
    r.repository_name,
    u.target_url,
    u.result,
    same_origin(r.origin, u.target_url) AS same_origin_check,
    u.reason
FROM url_operations u
JOIN navigation_sessions ns
    ON ns.navigation_session_id = u.navigation_session_id
JOIN repositories r
    ON r.repository_id = ns.repository_id
ORDER BY u.created_at;

-- Transactional state change: replace a preference atomically.
BEGIN;

UPDATE browser_storage
SET storage_value = 'light'
WHERE repository_id = (
    SELECT repository_id
    FROM repositories
    WHERE repository_name = 'Portal'
)
AND scope = 'local'
AND storage_key = 'theme';

INSERT INTO url_operations (
    navigation_session_id,
    action,
    source_url,
    target_url,
    result,
    reason
)
SELECT
    navigation_session_id,
    'replace_state',
    'https://portal.example.test/dashboard',
    'https://portal.example.test/dashboard?theme=light',
    'allowed',
    'Preference changed without document navigation'
FROM navigation_sessions
WHERE session_key =
    '11111111-1111-1111-1111-111111111111';

COMMIT;

-- Failure case: the trigger rejects SameSite=None without Secure.
DO $$
BEGIN
    BEGIN
        INSERT INTO browser_cookies (
            repository_id,
            cookie_name,
            cookie_value,
            secure,
            http_only,
            same_site
        )
        SELECT
            repository_id,
            'invalid_cross_site',
            'bad',
            FALSE,
            TRUE,
            'None'
        FROM repositories
        WHERE repository_name = 'Portal';
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE
            'Expected cookie validation failure: %',
            SQLERRM;
    END;
END;
$$;

-- Failure case: a cross-origin URL is recorded as blocked.
INSERT INTO url_operations (
    navigation_session_id,
    action,
    source_url,
    target_url,
    result,
    reason
)
SELECT
    navigation_session_id,
    'push_state',
    'https://portal.example.test/dashboard',
    'https://evil.example.test/',
    CASE
        WHEN same_origin(
            'https://portal.example.test',
            'https://evil.example.test/'
        )
        THEN 'allowed'::navigation_result
        ELSE 'blocked'::navigation_result
    END,
    'Origin comparison'
FROM navigation_sessions
WHERE session_key =
    '11111111-1111-1111-1111-111111111111';
