-- ============================================================
-- NEXT.JS DATA ARCHITECTURE
-- Server-side fetching, caching, revalidation and rendering
-- PostgreSQL 14+
--
-- Domain: Enterprise product catalog and personalized account
-- services supporting a Next.js App Router application.
--
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS next_architecture;

SET search_path TO next_architecture, public;

-- ============================================================
-- 1. ENUMERATED DOMAIN TYPES
-- ============================================================

CREATE TYPE render_mode AS ENUM (
    'STATIC',
    'DYNAMIC',
    'PARTIAL'
);

CREATE TYPE fetch_policy AS ENUM (
    'CACHE',
    'NO_STORE'
);

CREATE TYPE cache_entry_state AS ENUM (
    'FRESH',
    'STALE',
    'INVALIDATED',
    'EXPIRED'
);

CREATE TYPE revalidation_type AS ENUM (
    'TAG',
    'PATH'
);

CREATE TYPE refresh_status AS ENUM (
    'PENDING',
    'RUNNING',
    'SUCCEEDED',
    'FAILED',
    'CANCELLED'
);

CREATE TYPE request_status AS ENUM (
    'SUCCESS',
    'FAILED',
    'TIMEOUT',
    'REJECTED'
);

-- ============================================================
-- 2. APPLICATION USERS
-- ============================================================

CREATE TABLE app_users (
    user_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    display_name VARCHAR(120) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_email
        CHECK (position('@' IN email) > 1)
);

-- ============================================================
-- 3. PRODUCT DATA SOURCE
-- ============================================================

CREATE TABLE products (
    product_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_name VARCHAR(200) NOT NULL,
    category VARCHAR(100) NOT NULL,
    price NUMERIC(12, 2) NOT NULL,
    stock_quantity INTEGER NOT NULL DEFAULT 0,
    version INTEGER NOT NULL DEFAULT 1,
    is_published BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_product_name
        CHECK (length(trim(product_name)) > 0),

    CONSTRAINT valid_price
        CHECK (price >= 0),

    CONSTRAINT valid_stock
        CHECK (stock_quantity >= 0),

    CONSTRAINT valid_version
        CHECK (version > 0)
);

CREATE INDEX idx_products_category
    ON products(category);

CREATE INDEX idx_products_published
    ON products(is_published, product_id)
    WHERE is_published = TRUE;

CREATE INDEX idx_products_updated
    ON products(updated_at DESC);

-- ============================================================
-- 4. ROUTE DEFINITIONS
-- ============================================================

CREATE TABLE application_routes (
    route_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    route_path VARCHAR(500) NOT NULL UNIQUE,
    description TEXT,
    configured_mode render_mode NOT NULL,
    personalized BOOLEAN NOT NULL DEFAULT FALSE,
    reads_cookies BOOLEAN NOT NULL DEFAULT FALSE,
    reads_headers BOOLEAN NOT NULL DEFAULT FALSE,
    uses_uncached_data BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT absolute_route_path
        CHECK (route_path LIKE '/%'),

    CONSTRAINT private_route_not_static
        CHECK (
            NOT personalized OR configured_mode = 'DYNAMIC'
        )
);

CREATE INDEX idx_routes_active_mode
    ON application_routes(is_active, configured_mode);

-- ============================================================
-- 5. ROUTE DATA ACCESS POLICIES
-- ============================================================

CREATE TABLE route_data_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    route_id BIGINT NOT NULL
        REFERENCES application_routes(route_id)
        ON DELETE CASCADE,

    policy_name VARCHAR(150) NOT NULL,
    fetch_method VARCHAR(20) NOT NULL DEFAULT 'GET',
    cache_policy fetch_policy NOT NULL,
    ttl_seconds INTEGER NOT NULL DEFAULT 0,
    requires_authentication BOOLEAN NOT NULL DEFAULT FALSE,
    cache_shared BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT unique_route_policy
        UNIQUE(route_id, policy_name),

    CONSTRAINT valid_fetch_method
        CHECK (fetch_method IN ('GET', 'POST', 'PUT', 'DELETE')),

    CONSTRAINT valid_ttl
        CHECK (ttl_seconds >= 0),

    CONSTRAINT uncached_has_zero_ttl
        CHECK (
            cache_policy <> 'NO_STORE'
            OR ttl_seconds = 0
        ),

    CONSTRAINT no_shared_private_cache
        CHECK (
            NOT requires_authentication
            OR NOT cache_shared
        ),

    CONSTRAINT cached_has_ttl
        CHECK (
            cache_policy <> 'CACHE'
            OR ttl_seconds > 0
        )
);

CREATE INDEX idx_route_policies_route
    ON route_data_policies(route_id, cache_policy);

-- ============================================================
-- 6. CACHE TAGS
-- ============================================================

CREATE TABLE cache_tags (
    tag_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tag_name VARCHAR(150) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_tag_name
        CHECK (length(trim(tag_name)) > 0)
);

-- ============================================================
-- 7. CACHE ENTRIES
-- ============================================================

CREATE TABLE cache_entries (
    cache_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    cache_key VARCHAR(500) NOT NULL UNIQUE,
    route_id BIGINT
        REFERENCES application_routes(route_id)
        ON DELETE SET NULL,

    state cache_entry_state NOT NULL DEFAULT 'FRESH',
    cached_payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    last_accessed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    version INTEGER NOT NULL DEFAULT 1,
    invalidated_at TIMESTAMPTZ,

    CONSTRAINT valid_cache_key
        CHECK (length(trim(cache_key)) > 0),

    CONSTRAINT valid_expiration
        CHECK (expires_at > created_at),

    CONSTRAINT valid_cache_version
        CHECK (version > 0)
);

CREATE INDEX idx_cache_state_expiration
    ON cache_entries(state, expires_at);

CREATE INDEX idx_cache_route
    ON cache_entries(route_id);

CREATE INDEX idx_cache_payload
    ON cache_entries USING GIN(cached_payload);

-- ============================================================
-- 8. CACHE ENTRY TO TAG RELATIONSHIP
-- ============================================================

CREATE TABLE cache_entry_tags (
    cache_id BIGINT NOT NULL
        REFERENCES cache_entries(cache_id)
        ON DELETE CASCADE,

    tag_id BIGINT NOT NULL
        REFERENCES cache_tags(tag_id)
        ON DELETE CASCADE,

    PRIMARY KEY(cache_id, tag_id)
);

CREATE INDEX idx_cache_tag_lookup
    ON cache_entry_tags(tag_id, cache_id);

-- ============================================================
-- 9. CACHE ENTRY TO ROUTE PATH RELATIONSHIP
-- ============================================================

CREATE TABLE cache_entry_paths (
    cache_id BIGINT NOT NULL
        REFERENCES cache_entries(cache_id)
        ON DELETE CASCADE,

    route_id BIGINT NOT NULL
        REFERENCES application_routes(route_id)
        ON DELETE CASCADE,

    PRIMARY KEY(cache_id, route_id)
);

CREATE INDEX idx_cache_path_lookup
    ON cache_entry_paths(route_id, cache_id);

-- ============================================================
-- 10. REQUEST EXECUTION LOG
-- ============================================================

CREATE TABLE data_fetch_requests (
    request_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    route_id BIGINT
        REFERENCES application_routes(route_id)
        ON DELETE SET NULL,

    cache_id BIGINT
        REFERENCES cache_entries(cache_id)
        ON DELETE SET NULL,

    requested_by BIGINT
        REFERENCES app_users(user_id)
        ON DELETE SET NULL,

    request_key VARCHAR(500) NOT NULL,
    policy fetch_policy NOT NULL,
    status request_status NOT NULL,
    response_time_ms INTEGER NOT NULL,
    error_message TEXT,
    requested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_response_time
        CHECK (response_time_ms >= 0)
);

CREATE INDEX idx_fetch_route_time
    ON data_fetch_requests(route_id, requested_at DESC);

CREATE INDEX idx_fetch_status_time
    ON data_fetch_requests(status, requested_at DESC);

CREATE INDEX idx_fetch_user
    ON data_fetch_requests(requested_by, requested_at DESC);

-- ============================================================
-- 11. REVALIDATION EVENTS
-- ============================================================

CREATE TABLE revalidation_events (
    event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    event_type revalidation_type NOT NULL,
    identifier VARCHAR(500) NOT NULL,
    triggered_by BIGINT
        REFERENCES app_users(user_id)
        ON DELETE SET NULL,

    invalidated_count INTEGER NOT NULL DEFAULT 0,
    event_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_invalidated_count
        CHECK (invalidated_count >= 0),

    CONSTRAINT valid_identifier
        CHECK (length(trim(identifier)) > 0)
);

CREATE INDEX idx_revalidation_identifier
    ON revalidation_events(event_type, identifier, created_at DESC);

-- ============================================================
-- 12. BACKGROUND CACHE REFRESH JOBS
-- ============================================================

CREATE TABLE cache_refresh_jobs (
    job_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    cache_id BIGINT
        REFERENCES cache_entries(cache_id)
        ON DELETE SET NULL,

    refresh_key VARCHAR(500) NOT NULL,
    status refresh_status NOT NULL DEFAULT 'PENDING',
    attempts INTEGER NOT NULL DEFAULT 0,
    max_attempts INTEGER NOT NULL DEFAULT 3,
    last_error TEXT,
    scheduled_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    CONSTRAINT valid_attempts
        CHECK (
            attempts >= 0
            AND max_attempts > 0
            AND attempts <= max_attempts
        )
);

CREATE INDEX idx_refresh_queue
    ON cache_refresh_jobs(status, scheduled_at)
    WHERE status IN ('PENDING', 'FAILED');

-- ============================================================
-- 13. CACHE ENTRY STATE MANAGEMENT
-- ============================================================

CREATE OR REPLACE FUNCTION determine_cache_state(
    p_cache_id BIGINT
)
RETURNS cache_entry_state
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_entry cache_entries%ROWTYPE;
BEGIN
    SELECT *
    INTO v_entry
    FROM cache_entries
    WHERE cache_id = p_cache_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Cache entry % does not exist', p_cache_id;
    END IF;

    IF v_entry.state = 'INVALIDATED' THEN
        RETURN 'INVALIDATED';
    END IF;

    IF NOW() >= v_entry.expires_at THEN
        RETURN 'EXPIRED';
    END IF;

    RETURN 'FRESH';
END;
$$;

-- ============================================================
-- 14. AUTOMATIC PRODUCT VERSIONING
-- ============================================================

CREATE OR REPLACE FUNCTION maintain_product_version()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.price IS DISTINCT FROM OLD.price
       OR NEW.stock_quantity IS DISTINCT FROM OLD.stock_quantity
       OR NEW.product_name IS DISTINCT FROM OLD.product_name
       OR NEW.category IS DISTINCT FROM OLD.category
       OR NEW.is_published IS DISTINCT FROM OLD.is_published
    THEN
        NEW.version := OLD.version + 1;
        NEW.updated_at := NOW();
    ELSE
        NEW.version := OLD.version;
        NEW.updated_at := OLD.updated_at;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_product_version
BEFORE UPDATE ON products
FOR EACH ROW
EXECUTE FUNCTION maintain_product_version();

-- ============================================================
-- 15. TAG-BASED INVALIDATION
-- ============================================================

CREATE OR REPLACE FUNCTION invalidate_cache_tag(
    p_tag_name VARCHAR,
    p_user_id BIGINT DEFAULT NULL,
    p_reason TEXT DEFAULT 'Data mutation'
)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_tag_id BIGINT;
    v_count INTEGER;
BEGIN
    SELECT tag_id
    INTO v_tag_id
    FROM cache_tags
    WHERE tag_name = p_tag_name;

    IF NOT FOUND THEN
        RETURN 0;
    END IF;

    WITH affected AS (
        UPDATE cache_entries ce
        SET state = 'INVALIDATED',
            invalidated_at = NOW()
        WHERE ce.state <> 'INVALIDATED'
          AND ce.cache_id IN (
              SELECT cet.cache_id
              FROM cache_entry_tags cet
              WHERE cet.tag_id = v_tag_id
          )
        RETURNING ce.cache_id
    )
    SELECT COUNT(*)::INTEGER
    INTO v_count
    FROM affected;

    INSERT INTO revalidation_events(
        event_type,
        identifier,
        triggered_by,
        invalidated_count,
        event_reason
    )
    VALUES (
        'TAG',
        p_tag_name,
        p_user_id,
        v_count,
        p_reason
    );

    RETURN v_count;
END;
$$;

-- ============================================================
-- 16. PATH-BASED INVALIDATION
-- ============================================================

CREATE OR REPLACE FUNCTION invalidate_cache_path(
    p_route_path VARCHAR,
    p_user_id BIGINT DEFAULT NULL,
    p_reason TEXT DEFAULT 'Route revalidation'
)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_route_id BIGINT;
    v_count INTEGER;
BEGIN
    SELECT route_id
    INTO v_route_id
    FROM application_routes
    WHERE route_path = p_route_path;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Route % not registered', p_route_path;
    END IF;

    WITH affected AS (
        UPDATE cache_entries ce
        SET state = 'INVALIDATED',
            invalidated_at = NOW()
        WHERE ce.state <> 'INVALIDATED'
          AND ce.cache_id IN (
              SELECT cep.cache_id
              FROM cache_entry_paths cep
              WHERE cep.route_id = v_route_id
          )
        RETURNING ce.cache_id
    )
    SELECT COUNT(*)::INTEGER
    INTO v_count
    FROM affected;

    INSERT INTO revalidation_events(
        event_type,
        identifier,
        triggered_by,
        invalidated_count,
        event_reason
    )
    VALUES (
        'PATH',
        p_route_path,
        p_user_id,
        v_count,
        p_reason
    );

    RETURN v_count;
END;
$$;

-- ============================================================
-- 17. CACHE ELIGIBILITY EVALUATION
-- ============================================================

CREATE OR REPLACE FUNCTION evaluate_cache_eligibility(
    p_route_id BIGINT,
    p_user_id BIGINT DEFAULT NULL
)
RETURNS BOOLEAN
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_personalized BOOLEAN;
    v_cookies BOOLEAN;
    v_headers BOOLEAN;
    v_uncached BOOLEAN;
    v_requires_auth BOOLEAN;
    v_shared BOOLEAN;
BEGIN
    SELECT
        r.personalized,
        r.reads_cookies,
        r.reads_headers,
        r.uses_uncached_data,
        COALESCE(bool_or(p.requires_authentication), FALSE),
        COALESCE(bool_and(p.cache_shared), FALSE)
    INTO
        v_personalized,
        v_cookies,
        v_headers,
        v_uncached,
        v_requires_auth,
        v_shared
    FROM application_routes r
    LEFT JOIN route_data_policies p
        ON p.route_id = r.route_id
    WHERE r.route_id = p_route_id
    GROUP BY
        r.personalized,
        r.reads_cookies,
        r.reads_headers,
        r.uses_uncached_data;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Route policy not found';
    END IF;

    -- Personalized data cannot be served through a shared cache.
    IF v_personalized
       OR v_cookies
       OR v_headers
       OR v_uncached
       OR v_requires_auth
       OR NOT v_shared
    THEN
        RETURN FALSE;
    END IF;

    RETURN TRUE;
END;
$$;

-- ============================================================
-- 18. RENDERING MODE EVALUATION
-- ============================================================

CREATE OR REPLACE FUNCTION evaluate_render_mode(
    p_route_id BIGINT,
    p_user_id BIGINT DEFAULT NULL
)
RETURNS render_mode
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_personalized BOOLEAN;
    v_cookies BOOLEAN;
    v_headers BOOLEAN;
    v_uncached BOOLEAN;
BEGIN
    SELECT
        personalized,
        reads_cookies,
        reads_headers,
        uses_uncached_data
    INTO
        v_personalized,
        v_cookies,
        v_headers,
        v_uncached
    FROM application_routes
    WHERE route_id = p_route_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Route not found';
    END IF;

    IF v_personalized
       OR v_cookies
       OR v_headers
       OR v_uncached
       OR p_user_id IS NOT NULL
    THEN
        RETURN 'DYNAMIC';
    END IF;

    RETURN 'PARTIAL';
END;
$$;

-- ============================================================
-- 19. PRODUCT UPDATE WITH AUTOMATIC REVALIDATION
-- ============================================================

CREATE OR REPLACE FUNCTION update_product_and_revalidate(
    p_product_id BIGINT,
    p_price NUMERIC DEFAULT NULL,
    p_stock INTEGER DEFAULT NULL,
    p_user_id BIGINT DEFAULT NULL
)
RETURNS products
LANGUAGE plpgsql
AS $$
DECLARE
    v_product products%ROWTYPE;
BEGIN
    IF p_price IS NOT NULL AND p_price < 0 THEN
        RAISE EXCEPTION 'Price cannot be negative';
    END IF;

    IF p_stock IS NOT NULL AND p_stock < 0 THEN
        RAISE EXCEPTION 'Stock cannot be negative';
    END IF;

    UPDATE products
    SET price = COALESCE(p_price, price),
        stock_quantity = COALESCE(p_stock, stock_quantity)
    WHERE product_id = p_product_id
    RETURNING *
    INTO v_product;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Product % not found', p_product_id;
    END IF;

    -- Both detail and collection views depend on product data.
    PERFORM invalidate_cache_tag(
        'product:' || p_product_id,
        p_user_id,
        'Product record updated'
    );

    PERFORM invalidate_cache_tag(
        'products',
        p_user_id,
        'Product collection updated'
    );

    RETURN v_product;
END;
$$;

-- ============================================================
-- 20. CACHE REFRESH JOB SCHEDULING
-- ============================================================

CREATE OR REPLACE FUNCTION schedule_cache_refresh(
    p_cache_id BIGINT
)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    v_key VARCHAR(500);
    v_job_id BIGINT;
BEGIN
    SELECT cache_key
    INTO v_key
    FROM cache_entries
    WHERE cache_id = p_cache_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Cache entry not found';
    END IF;

    -- Avoid duplicate pending or running refreshes.
    INSERT INTO cache_refresh_jobs(
        cache_id,
        refresh_key,
        status
    )
    SELECT
        p_cache_id,
        v_key,
        'PENDING'
    WHERE NOT EXISTS (
        SELECT 1
        FROM cache_refresh_jobs
        WHERE refresh_key = v_key
          AND status IN ('PENDING', 'RUNNING')
    )
    RETURNING job_id INTO v_job_id;

    RETURN v_job_id;
END;
$$;

-- ============================================================
-- 21. ATOMIC REFRESH JOB CLAIMING
-- ============================================================

CREATE OR REPLACE FUNCTION claim_refresh_jobs(
    p_batch_size INTEGER DEFAULT 10
)
RETURNS SETOF cache_refresh_jobs
LANGUAGE plpgsql
AS $$
BEGIN
    IF p_batch_size <= 0 OR p_batch_size > 1000 THEN
        RAISE EXCEPTION 'Invalid batch size';
    END IF;

    RETURN QUERY
    WITH selected AS (
        SELECT job_id
        FROM cache_refresh_jobs
        WHERE status IN ('PENDING', 'FAILED')
          AND attempts < max_attempts
          AND scheduled_at <= NOW()
        ORDER BY scheduled_at, job_id
        LIMIT p_batch_size
        FOR UPDATE SKIP LOCKED
    )
    UPDATE cache_refresh_jobs j
    SET status = 'RUNNING',
        attempts = j.attempts + 1,
        started_at = NOW()
    FROM selected s
    WHERE j.job_id = s.job_id
    RETURNING j.*;
END;
$$;

-- ============================================================
-- 22. REPORTING VIEWS
-- ============================================================

CREATE OR REPLACE VIEW cache_entry_report AS
SELECT
    ce.cache_id,
    ce.cache_key,
    ar.route_path,
    ce.state,
    ce.version,
    ce.created_at,
    ce.expires_at,
    ce.last_accessed_at,
    CASE
        WHEN ce.state = 'INVALIDATED' THEN 'INVALIDATED'
        WHEN NOW() >= ce.expires_at THEN 'EXPIRED'
        ELSE 'FRESH'
    END AS effective_state,
    COALESCE(
        array_agg(DISTINCT ct.tag_name)
            FILTER (WHERE ct.tag_name IS NOT NULL),
        ARRAY[]::VARCHAR[]
    ) AS tags
FROM cache_entries ce
LEFT JOIN application_routes ar
    ON ar.route_id = ce.route_id
LEFT JOIN cache_entry_tags cet
    ON cet.cache_id = ce.cache_id
LEFT JOIN cache_tags ct
    ON ct.tag_id = cet.tag_id
GROUP BY
    ce.cache_id,
    ce.cache_key,
    ar.route_path,
    ce.state,
    ce.version,
    ce.created_at,
    ce.expires_at,
    ce.last_accessed_at;

CREATE OR REPLACE VIEW route_performance_report AS
SELECT
    ar.route_path,
    COUNT(dfr.request_id) AS total_requests,
    COUNT(*) FILTER (
        WHERE dfr.status = 'SUCCESS'
    ) AS successful_requests,
    COUNT(*) FILTER (
        WHERE dfr.status = 'FAILED'
    ) AS failed_requests,
    ROUND(
        AVG(dfr.response_time_ms)::NUMERIC,
        2
    ) AS average_response_ms,
    MAX(dfr.response_time_ms) AS maximum_response_ms
FROM application_routes ar
LEFT JOIN data_fetch_requests dfr
    ON dfr.route_id = ar.route_id
GROUP BY ar.route_id, ar.route_path;

CREATE OR REPLACE VIEW revalidation_report AS
SELECT
    event_type,
    identifier,
    COUNT(*) AS event_count,
    SUM(invalidated_count) AS total_invalidations,
    MAX(created_at) AS latest_event
FROM revalidation_events
GROUP BY event_type, identifier;

-- ============================================================
-- 23. SAMPLE USERS
-- ============================================================

INSERT INTO app_users(email, display_name)
VALUES
    ('admin@example.com', 'System Administrator'),
    ('editor@example.com', 'Catalog Editor'),
    ('customer@example.com', 'Customer Account');

-- ============================================================
-- 24. SAMPLE PRODUCTS
-- ============================================================

INSERT INTO products(
    product_name,
    category,
    price,
    stock_quantity
)
VALUES
    ('Laptop', 'Electronics', 75000, 12),
    ('Keyboard', 'Accessories', 2500, 45),
    ('Monitor', 'Electronics', 18000, 8),
    ('Mouse', 'Accessories', 900, 0),
    ('Webcam', 'Electronics', 4500, 20);

-- ============================================================
-- 25. SAMPLE ROUTES
-- ============================================================

INSERT INTO application_routes(
    route_path,
    description,
    configured_mode,
    personalized,
    reads_cookies,
    reads_headers,
    uses_uncached_data
)
VALUES
    (
        '/products',
        'Public product catalog',
        'PARTIAL',
        FALSE,
        FALSE,
        FALSE,
        FALSE
    ),
    (
        '/products/1',
        'Product detail page',
        'PARTIAL',
        FALSE,
        FALSE,
        FALSE,
        FALSE
    ),
    (
        '/account',
        'Authenticated customer account',
        'DYNAMIC',
        TRUE,
        TRUE,
        FALSE,
        TRUE
    ),
    (
        '/dashboard',
        'Live operational dashboard',
        'DYNAMIC',
        TRUE,
        TRUE,
        TRUE,
        TRUE
    ),
    (
        '/about',
        'Public informational page',
        'STATIC',
        FALSE,
        FALSE,
        FALSE,
        FALSE
    );

-- ============================================================
-- 26. SAMPLE DATA POLICIES
-- ============================================================

INSERT INTO route_data_policies(
    route_id,
    policy_name,
    fetch_method,
    cache_policy,
    ttl_seconds,
    requires_authentication,
    cache_shared
)
SELECT
    route_id,
    'public-catalog',
    'GET',
    'CACHE',
    300,
    FALSE,
    TRUE
FROM application_routes
WHERE route_path = '/products';

INSERT INTO route_data_policies(
    route_id,
    policy_name,
    fetch_method,
    cache_policy,
    ttl_seconds,
    requires_authentication,
    cache_shared
)
SELECT
    route_id,
    'product-detail',
    'GET',
    'CACHE',
    600,
    FALSE,
    TRUE
FROM application_routes
WHERE route_path = '/products/1';

INSERT INTO route_data_policies(
    route_id,
    policy_name,
    fetch_method,
    cache_policy,
    ttl_seconds,
    requires_authentication,
    cache_shared
)
SELECT
    route_id,
    'account-data',
    'GET',
    'NO_STORE',
    0,
    TRUE,
    FALSE
FROM application_routes
WHERE route_path = '/account';

INSERT INTO route_data_policies(
    route_id,
    policy_name,
    fetch_method,
    cache_policy,
    ttl_seconds,
    requires_authentication,
    cache_shared
)
SELECT
    route_id,
    'live-dashboard',
    'GET',
    'NO_STORE',
    0,
    TRUE,
    FALSE
FROM application_routes
WHERE route_path = '/dashboard';

-- ============================================================
-- 27. CACHE TAG DEFINITIONS
-- ============================================================

INSERT INTO cache_tags(tag_name, description)
VALUES
    ('products', 'All product catalog data'),
    ('product:1', 'Individual product 1'),
    ('product:2', 'Individual product 2'),
    ('product:3', 'Individual product 3'),
    ('dashboard', 'Operational dashboard data');

-- ============================================================
-- 28. SAMPLE CACHE ENTRIES
-- ============================================================

INSERT INTO cache_entries(
    cache_key,
    route_id,
    state,
    cached_payload,
    created_at,
    expires_at
)
SELECT
    'catalog:products:v1',
    route_id,
    'FRESH',
    '{
        "collection": "products",
        "count": 5,
        "source": "database"
    }'::JSONB,
    NOW(),
    NOW() + INTERVAL '5 minutes'
FROM application_routes
WHERE route_path = '/products';

INSERT INTO cache_entries(
    cache_key,
    route_id,
    state,
    cached_payload,
    created_at,
    expires_at
)
SELECT
    'product:1:v1',
    route_id,
    'FRESH',
    '{
        "product_id": 1,
        "name": "Laptop",
        "price": 75000
    }'::JSONB,
    NOW(),
    NOW() + INTERVAL '10 minutes'
FROM application_routes
WHERE route_path = '/products/1';

-- ============================================================
-- 29. CACHE TAG AND PATH ASSOCIATIONS
-- ============================================================

INSERT INTO cache_entry_tags(cache_id, tag_id)
SELECT ce.cache_id, ct.tag_id
FROM cache_entries ce
JOIN cache_tags ct
    ON ct.tag_name = 'products'
WHERE ce.cache_key = 'catalog:products:v1';

INSERT INTO cache_entry_tags(cache_id, tag_id)
SELECT ce.cache_id, ct.tag_id
FROM cache_entries ce
JOIN cache_tags ct
    ON ct.tag_name IN ('products', 'product:1')
WHERE ce.cache_key = 'product:1:v1';

INSERT INTO cache_entry_paths(cache_id, route_id)
SELECT ce.cache_id, ar.route_id
FROM cache_entries ce
JOIN application_routes ar
    ON ar.route_path IN ('/products', '/products/1')
WHERE ce.cache_key = 'product:1:v1';

INSERT INTO cache_entry_paths(cache_id, route_id)
SELECT ce.cache_id, ar.route_id
FROM cache_entries ce
JOIN application_routes ar
    ON ar.route_path = '/products'
WHERE ce.cache_key = 'catalog:products:v1';

-- ============================================================
-- 30. REQUEST EXECUTION SAMPLES
-- ============================================================

INSERT INTO data_fetch_requests(
    route_id,
    request_key,
    policy,
    status,
    response_time_ms
)
SELECT
    route_id,
    'catalog-request-001',
    'CACHE',
    'SUCCESS',
    42
FROM application_routes
WHERE route_path = '/products';

INSERT INTO data_fetch_requests(
    route_id,
    request_key,
    policy,
    status,
    response_time_ms
)
SELECT
    route_id,
    'account-request-001',
    'NO_STORE',
    'SUCCESS',
    125
FROM application_routes
WHERE route_path = '/account';

INSERT INTO data_fetch_requests(
    route_id,
    request_key,
    policy,
    status,
    response_time_ms,
    error_message
)
SELECT
    route_id,
    'dashboard-request-002',
    'NO_STORE',
    'FAILED',
    3000,
    'External analytics service unavailable'
FROM application_routes
WHERE route_path = '/dashboard';

-- ============================================================
-- 31. RETRIEVAL QUERIES
-- ============================================================

-- Public catalog retrieval.
SELECT
    product_id,
    product_name,
    category,
    price,
    stock_quantity
FROM products
WHERE is_published = TRUE
ORDER BY product_id;

-- Product lookup.
SELECT *
FROM products
WHERE product_id = 1;

-- Current cache state.
SELECT *
FROM cache_entry_report
ORDER BY cache_id;

-- ============================================================
-- 32. VALIDATION QUERIES
-- ============================================================

-- Detect expired entries.
SELECT
    cache_id,
    cache_key,
    expires_at
FROM cache_entries
WHERE expires_at <= NOW();

-- Detect invalidated entries.
SELECT
    cache_id,
    cache_key,
    invalidated_at
FROM cache_entries
WHERE state = 'INVALIDATED';

-- Detect unsafe shared-cache policies.
SELECT
    ar.route_path,
    p.policy_name
FROM route_data_policies p
JOIN application_routes ar
    ON ar.route_id = p.route_id
WHERE p.requires_authentication
  AND p.cache_shared = TRUE;

-- ============================================================
-- 33. CACHE ELIGIBILITY EVALUATION
-- ============================================================

SELECT
    route_path,
    evaluate_cache_eligibility(route_id) AS shared_cache_allowed
FROM application_routes
ORDER BY route_id;

-- ============================================================
-- 34. DYNAMIC RENDERING EVALUATION
-- ============================================================

SELECT
    route_path,
    configured_mode,
    evaluate_render_mode(route_id) AS evaluated_mode
FROM application_routes
ORDER BY route_id;

-- ============================================================
-- 35. PERFORMANCE AGGREGATION
-- ============================================================

SELECT *
FROM route_performance_report
ORDER BY total_requests DESC;

SELECT
    status,
    COUNT(*) AS request_count,
    ROUND(AVG(response_time_ms)::NUMERIC, 2)
        AS average_response_ms,
    MAX(response_time_ms) AS maximum_response_ms
FROM data_fetch_requests
GROUP BY status
ORDER BY request_count DESC;

-- ============================================================
-- 36. CACHE FRESHNESS AGGREGATION
-- ============================================================

SELECT
    state,
    COUNT(*) AS entry_count,
    MIN(created_at) AS oldest_entry,
    MAX(expires_at) AS latest_expiration
FROM cache_entries
GROUP BY state
ORDER BY state;

-- ============================================================
-- 37. EXAMPLE CTE: CACHE DEPENDENCY ANALYSIS
-- ============================================================

WITH dependency_map AS (
    SELECT
        ce.cache_id,
        ce.cache_key,
        ar.route_path,
        ct.tag_name
    FROM cache_entries ce
    LEFT JOIN application_routes ar
        ON ar.route_id = ce.route_id
    LEFT JOIN cache_entry_tags cet
        ON cet.cache_id = ce.cache_id
    LEFT JOIN cache_tags ct
        ON ct.tag_id = cet.tag_id
),
dependency_summary AS (
    SELECT
        cache_key,
        route_path,
        COUNT(DISTINCT tag_name) AS tag_count,
        array_agg(DISTINCT tag_name)
            FILTER (WHERE tag_name IS NOT NULL) AS tags
    FROM dependency_map
    GROUP BY cache_key, route_path
)
SELECT *
FROM dependency_summary
ORDER BY cache_key;

-- ============================================================
-- 38. TRANSACTIONAL PRODUCT MUTATION
-- ============================================================

BEGIN;

SELECT update_product_and_revalidate(
    1,
    72000.00,
    15,
    NULL
);

-- Check updated source data and version.
SELECT
    product_id,
    price,
    stock_quantity,
    version,
    updated_at
FROM products
WHERE product_id = 1;

-- Check invalidation history.
SELECT *
FROM revalidation_report
ORDER BY latest_event DESC;

COMMIT;

-- ============================================================
-- 39. PATH-BASED REVALIDATION EXAMPLE
-- ============================================================

SELECT invalidate_cache_path(
    '/products',
    NULL,
    'Catalog content refresh'
);

-- ============================================================
-- 40. TAG-BASED REVALIDATION EXAMPLE
-- ============================================================

SELECT invalidate_cache_tag(
    'products',
    NULL,
    'Product collection changed'
);

-- ============================================================
-- 41. SCHEDULE A BACKGROUND REFRESH
-- ============================================================

INSERT INTO cache_entries(
    cache_key,
    state,
    cached_payload,
    created_at,
    expires_at
)
VALUES (
    'dashboard:analytics:v1',
    'STALE',
    '{"metric":"revenue","value":500000}'::JSONB,
    NOW() - INTERVAL '10 minutes',
    NOW() - INTERVAL '1 minute'
)
ON CONFLICT (cache_key) DO NOTHING;

SELECT schedule_cache_refresh(cache_id)
FROM cache_entries
WHERE cache_key = 'dashboard:analytics:v1';

-- ============================================================
-- 42. CLAIM BACKGROUND REFRESH WORK
-- ============================================================

SELECT *
FROM claim_refresh_jobs(10);

-- ============================================================
-- 43. REFRESH JOB REPORTING
-- ============================================================

SELECT
    status,
    COUNT(*) AS job_count,
    SUM(attempts) AS total_attempts,
    MAX(scheduled_at) AS latest_scheduled
FROM cache_refresh_jobs
GROUP BY status
ORDER BY status;

-- ============================================================
-- 44. REVALIDATION AUDIT
-- ============================================================

SELECT
    event_id,
    event_type,
    identifier,
    invalidated_count,
    event_reason,
    created_at
FROM revalidation_events
ORDER BY created_at DESC;

-- ============================================================
-- 45. FINAL APPLICATION REPORT
-- ============================================================

SELECT
    ar.route_path,
    ar.configured_mode,
    evaluate_render_mode(ar.route_id) AS actual_render_mode,
    evaluate_cache_eligibility(ar.route_id)
        AS shared_cache_allowed,
    COUNT(DISTINCT ce.cache_id) AS related_cache_entries,
    COUNT(DISTINCT p.policy_id) AS data_policies
FROM application_routes ar
LEFT JOIN cache_entries ce
    ON ce.route_id = ar.route_id
LEFT JOIN route_data_policies p
    ON p.route_id = ar.route_id
GROUP BY
    ar.route_id,
    ar.route_path,
    ar.configured_mode
ORDER BY ar.route_path;

COMMIT;
