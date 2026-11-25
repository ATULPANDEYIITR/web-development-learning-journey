/*
===============================================================================
NEXT.JS ADVANCED ARCHITECTURE
PostgreSQL 15+

Relational model for:
- Next.js Server Components
- Client Components
- Component boundaries
- Serializable props
- Server-side data access
- Suspense boundaries
- Loading and streaming states
- Error boundaries
- Error recovery
- Nested routes
- Rendering requests
- Request-scoped data caching
- Component execution events

The database models application rendering and its lifecycle.
It does not execute React components or replace Next.js runtime behavior.

The script is repeatable for demonstration purposes.
===============================================================================
*/

BEGIN;

CREATE SCHEMA IF NOT EXISTS nextjs_lab;

SET search_path TO nextjs_lab, public;

/*
===============================================================================
1. ENUMERATED DOMAIN TYPES
===============================================================================
*/

DO $$
BEGIN
    CREATE TYPE component_kind AS ENUM (
        'server',
        'client'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END
$$;

DO $$
BEGIN
    CREATE TYPE render_state AS ENUM (
        'created',
        'loading',
        'streaming',
        'ready',
        'error',
        'not_found',
        'recovered'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END
$$;

DO $$
BEGIN
    CREATE TYPE boundary_kind AS ENUM (
        'suspense',
        'error'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END
$$;

DO $$
BEGIN
    CREATE TYPE execution_status AS ENUM (
        'pending',
        'running',
        'succeeded',
        'failed',
        'timed_out',
        'cancelled'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END
$$;

/*
===============================================================================
2. APPLICATION AND ROUTE STRUCTURE
===============================================================================
*/

CREATE TABLE IF NOT EXISTS applications (
    application_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    application_name VARCHAR(150) NOT NULL UNIQUE,

    framework VARCHAR(50) NOT NULL DEFAULT 'Next.js',

    framework_version VARCHAR(30) NOT NULL,

    app_router_enabled BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT application_name_not_blank
        CHECK (BTRIM(application_name) <> ''),

    CONSTRAINT valid_framework_version
        CHECK (BTRIM(framework_version) <> '')
);


CREATE TABLE IF NOT EXISTS routes (
    route_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    application_id BIGINT NOT NULL
        REFERENCES applications(application_id)
        ON DELETE CASCADE,

    parent_route_id BIGINT,

    route_segment VARCHAR(150) NOT NULL,

    route_path TEXT NOT NULL,

    loading_enabled BOOLEAN NOT NULL DEFAULT FALSE,

    error_boundary_enabled BOOLEAN NOT NULL DEFAULT FALSE,

    not_found_enabled BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT route_parent_fk
        FOREIGN KEY (parent_route_id)
        REFERENCES routes(route_id)
        ON DELETE CASCADE,

    CONSTRAINT route_segment_not_blank
        CHECK (BTRIM(route_segment) <> ''),

    CONSTRAINT route_path_not_blank
        CHECK (BTRIM(route_path) <> ''),

    CONSTRAINT route_not_own_parent
        CHECK (
            parent_route_id IS NULL
            OR parent_route_id <> route_id
        ),

    CONSTRAINT unique_application_route
        UNIQUE (application_id, route_path),

    CONSTRAINT unique_route_identity
        UNIQUE (route_id, application_id)
);


CREATE INDEX IF NOT EXISTS idx_routes_parent
    ON routes(parent_route_id);

CREATE INDEX IF NOT EXISTS idx_routes_application_path
    ON routes(application_id, route_path);


/*
===============================================================================
3. COMPONENT DEFINITIONS
===============================================================================
*/

CREATE TABLE IF NOT EXISTS components (
    component_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    application_id BIGINT NOT NULL
        REFERENCES applications(application_id)
        ON DELETE CASCADE,

    route_id BIGINT NOT NULL,

    component_name VARCHAR(150) NOT NULL,

    component_type component_kind NOT NULL,

    parent_component_id BIGINT,

    client_boundary BOOLEAN NOT NULL DEFAULT FALSE,

    uses_browser_api BOOLEAN NOT NULL DEFAULT FALSE,

    uses_server_secret BOOLEAN NOT NULL DEFAULT FALSE,

    server_only_module BOOLEAN NOT NULL DEFAULT FALSE,

    interactive BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT component_route_fk
        FOREIGN KEY (route_id, application_id)
        REFERENCES routes(route_id, application_id)
        ON DELETE CASCADE,

    CONSTRAINT component_parent_fk
        FOREIGN KEY (parent_component_id)
        REFERENCES components(component_id)
        ON DELETE SET NULL,

    CONSTRAINT component_name_not_blank
        CHECK (BTRIM(component_name) <> ''),

    CONSTRAINT server_component_cannot_use_browser_api
        CHECK (
            component_type <> 'server'
            OR uses_browser_api = FALSE
        ),

    CONSTRAINT client_component_not_server_only
        CHECK (
            component_type <> 'client'
            OR server_only_module = FALSE
        ),

    CONSTRAINT client_component_not_directly_server_secret
        CHECK (
            component_type <> 'client'
            OR uses_server_secret = FALSE
        ),

    CONSTRAINT unique_component_per_route
        UNIQUE (route_id, component_name),

    CONSTRAINT unique_component_application
        UNIQUE (component_id, application_id)
);


CREATE INDEX IF NOT EXISTS idx_components_route
    ON components(route_id);

CREATE INDEX IF NOT EXISTS idx_components_kind
    ON components(application_id, component_type);


/*
===============================================================================
4. COMPONENT PROPS AND SERIALIZATION CONTRACTS
===============================================================================
*/

CREATE TABLE IF NOT EXISTS component_props (
    prop_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    component_id BIGINT NOT NULL
        REFERENCES components(component_id)
        ON DELETE CASCADE,

    prop_name VARCHAR(150) NOT NULL,

    prop_value JSONB NOT NULL,

    serializable BOOLEAN NOT NULL DEFAULT TRUE,

    contains_sensitive_data BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT prop_name_not_blank
        CHECK (BTRIM(prop_name) <> ''),

    CONSTRAINT unique_component_prop
        UNIQUE (component_id, prop_name)
);


CREATE INDEX IF NOT EXISTS idx_component_props_component
    ON component_props(component_id);


/*
===============================================================================
5. DATA RESOURCES
===============================================================================
*/

CREATE TABLE IF NOT EXISTS data_resources (
    resource_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    application_id BIGINT NOT NULL
        REFERENCES applications(application_id)
        ON DELETE CASCADE,

    resource_name VARCHAR(150) NOT NULL,

    resource_type VARCHAR(50) NOT NULL,

    server_only BOOLEAN NOT NULL DEFAULT TRUE,

    sensitive BOOLEAN NOT NULL DEFAULT FALSE,

    cache_enabled BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT resource_name_not_blank
        CHECK (BTRIM(resource_name) <> ''),

    CONSTRAINT unique_resource
        UNIQUE (application_id, resource_name)
);


CREATE TABLE IF NOT EXISTS component_data_access (
    component_id BIGINT NOT NULL
        REFERENCES components(component_id)
        ON DELETE CASCADE,

    resource_id BIGINT NOT NULL
        REFERENCES data_resources(resource_id)
        ON DELETE CASCADE,

    access_type VARCHAR(30) NOT NULL,

    PRIMARY KEY (component_id, resource_id),

    CONSTRAINT valid_access_type
        CHECK (
            access_type IN (
                'read',
                'write',
                'read_write'
            )
        )
);


/*
===============================================================================
6. RENDERING REQUESTS
===============================================================================
*/

CREATE TABLE IF NOT EXISTS render_requests (
    request_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    application_id BIGINT NOT NULL
        REFERENCES applications(application_id)
        ON DELETE CASCADE,

    route_id BIGINT NOT NULL
        REFERENCES routes(route_id)
        ON DELETE RESTRICT,

    request_method VARCHAR(10) NOT NULL DEFAULT 'GET',

    request_status execution_status NOT NULL DEFAULT 'pending',

    started_at TIMESTAMPTZ,

    completed_at TIMESTAMPTZ,

    duration_ms NUMERIC(14, 3),

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_request_method
        CHECK (
            request_method IN (
                'GET',
                'POST',
                'PUT',
                'PATCH',
                'DELETE'
            )
        ),

    CONSTRAINT valid_request_duration
        CHECK (
            duration_ms IS NULL
            OR duration_ms >= 0
        ),

    CONSTRAINT valid_request_timestamps
        CHECK (
            completed_at IS NULL
            OR started_at IS NULL
            OR completed_at >= started_at
        )
);


CREATE INDEX IF NOT EXISTS idx_render_requests_application
    ON render_requests(application_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_render_requests_status
    ON render_requests(request_status, created_at DESC);


/*
===============================================================================
7. BOUNDARIES AND LOADING STATES
===============================================================================
*/

CREATE TABLE IF NOT EXISTS rendering_boundaries (
    boundary_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    route_id BIGINT NOT NULL
        REFERENCES routes(route_id)
        ON DELETE CASCADE,

    component_id BIGINT
        REFERENCES components(component_id)
        ON DELETE CASCADE,

    boundary_name VARCHAR(150) NOT NULL,

    boundary_type boundary_kind NOT NULL,

    fallback_content TEXT NOT NULL,

    timeout_ms INTEGER,

    CONSTRAINT boundary_name_not_blank
        CHECK (BTRIM(boundary_name) <> ''),

    CONSTRAINT valid_boundary_timeout
        CHECK (
            timeout_ms IS NULL
            OR timeout_ms > 0
        )
);


CREATE TABLE IF NOT EXISTS render_events (
    event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    request_id UUID NOT NULL
        REFERENCES render_requests(request_id)
        ON DELETE CASCADE,

    component_id BIGINT
        REFERENCES components(component_id)
        ON DELETE SET NULL,

    boundary_id BIGINT
        REFERENCES rendering_boundaries(boundary_id)
        ON DELETE SET NULL,

    event_state render_state NOT NULL,

    event_message TEXT,

    occurred_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    duration_ms NUMERIC(14, 3),

    CONSTRAINT valid_event_duration
        CHECK (
            duration_ms IS NULL
            OR duration_ms >= 0
        )
);


CREATE INDEX IF NOT EXISTS idx_render_events_request
    ON render_events(request_id, occurred_at);

CREATE INDEX IF NOT EXISTS idx_render_events_state
    ON render_events(event_state, occurred_at DESC);


/*
===============================================================================
8. ERROR DETAILS AND RECOVERY ATTEMPTS
===============================================================================
*/

CREATE TABLE IF NOT EXISTS render_errors (
    error_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    request_id UUID NOT NULL
        REFERENCES render_requests(request_id)
        ON DELETE CASCADE,

    component_id BIGINT
        REFERENCES components(component_id)
        ON DELETE SET NULL,

    boundary_id BIGINT
        REFERENCES rendering_boundaries(boundary_id)
        ON DELETE SET NULL,

    error_code VARCHAR(100) NOT NULL,

    error_message TEXT NOT NULL,

    recoverable BOOLEAN NOT NULL DEFAULT FALSE,

    retry_count INTEGER NOT NULL DEFAULT 0,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_retry_count
        CHECK (retry_count >= 0),

    CONSTRAINT error_code_not_blank
        CHECK (BTRIM(error_code) <> ''),

    CONSTRAINT error_message_not_blank
        CHECK (BTRIM(error_message) <> '')
);


CREATE TABLE IF NOT EXISTS recovery_attempts (
    recovery_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    error_id BIGINT NOT NULL
        REFERENCES render_errors(error_id)
        ON DELETE CASCADE,

    attempt_number INTEGER NOT NULL,

    recovery_status execution_status NOT NULL,

    attempted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    recovery_message TEXT,

    CONSTRAINT positive_attempt_number
        CHECK (attempt_number > 0),

    CONSTRAINT unique_error_attempt
        UNIQUE (error_id, attempt_number)
);


/*
===============================================================================
9. REQUEST-SCOPED CACHE RECORDS
===============================================================================
*/

CREATE TABLE IF NOT EXISTS request_cache (
    cache_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    request_id UUID NOT NULL
        REFERENCES render_requests(request_id)
        ON DELETE CASCADE,

    cache_key VARCHAR(255) NOT NULL,

    resource_id BIGINT
        REFERENCES data_resources(resource_id)
        ON DELETE SET NULL,

    cache_value JSONB,

    expires_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_request_cache_key
        UNIQUE (request_id, cache_key),

    CONSTRAINT cache_key_not_blank
        CHECK (BTRIM(cache_key) <> '')
);


CREATE INDEX IF NOT EXISTS idx_request_cache_expiration
    ON request_cache(expires_at)
    WHERE expires_at IS NOT NULL;


/*
===============================================================================
10. DATABASE INTEGRITY TRIGGERS
===============================================================================
*/

/*
A Client Component cannot directly declare server-only data access.
This trigger checks relationships that cannot be expressed through
ordinary single-row CHECK constraints.
*/

CREATE OR REPLACE FUNCTION validate_component_data_access()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_component_type component_kind;
    v_server_only BOOLEAN;
    v_sensitive BOOLEAN;
BEGIN
    SELECT
        c.component_type,
        r.server_only,
        r.sensitive
    INTO
        v_component_type,
        v_server_only,
        v_sensitive
    FROM components c
    JOIN data_resources r
        ON r.resource_id = NEW.resource_id
    WHERE c.component_id = NEW.component_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Component or resource does not exist.';
    END IF;

    IF v_component_type = 'client'
       AND (v_server_only OR v_sensitive) THEN

        RAISE EXCEPTION
            'Client Components cannot directly access server-only or sensitive resources.';
    END IF;

    RETURN NEW;
END;
$$;


DROP TRIGGER IF EXISTS trg_validate_component_data_access
    ON component_data_access;

CREATE TRIGGER trg_validate_component_data_access
BEFORE INSERT OR UPDATE
ON component_data_access
FOR EACH ROW
EXECUTE FUNCTION validate_component_data_access();


/*
A Server Component must not directly declare a client interaction.
Interactivity belongs in a Client Component.
*/

CREATE OR REPLACE FUNCTION validate_component_prop()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_kind component_kind;
BEGIN
    SELECT component_type
    INTO v_kind
    FROM components
    WHERE component_id = NEW.component_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Component does not exist.';
    END IF;

    IF v_kind = 'client'
       AND NEW.contains_sensitive_data THEN

        RAISE EXCEPTION
            'Sensitive data cannot be passed to Client Component props.';
    END IF;

    IF NOT NEW.serializable THEN
        RAISE EXCEPTION
            'Non-serializable props cannot cross the component boundary.';
    END IF;

    RETURN NEW;
END;
$$;


DROP TRIGGER IF EXISTS trg_validate_component_prop
    ON component_props;

CREATE TRIGGER trg_validate_component_prop
BEFORE INSERT OR UPDATE
ON component_props
FOR EACH ROW
EXECUTE FUNCTION validate_component_prop();


/*
Prevent impossible render-request state transitions.
*/

CREATE OR REPLACE FUNCTION validate_request_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.request_status = 'succeeded'
       AND NEW.request_status <> 'succeeded' THEN
        RAISE EXCEPTION
            'Completed successful requests are immutable.';
    END IF;

    IF OLD.request_status = 'failed'
       AND NEW.request_status = 'running' THEN
        RAISE EXCEPTION
            'Failed requests cannot restart without a new request.';
    END IF;

    IF NEW.completed_at IS NOT NULL
       AND NEW.started_at IS NULL THEN
        RAISE EXCEPTION
            'A completed request must have a start timestamp.';
    END IF;

    RETURN NEW;
END;
$$;


DROP TRIGGER IF EXISTS trg_validate_request_transition
    ON render_requests;

CREATE TRIGGER trg_validate_request_transition
BEFORE UPDATE
ON render_requests
FOR EACH ROW
EXECUTE FUNCTION validate_request_transition();


/*
===============================================================================
11. COMPONENT SERIALIZATION ELIGIBILITY
===============================================================================
*/

CREATE OR REPLACE FUNCTION component_serialization_eligible(
    p_component_id BIGINT
)
RETURNS BOOLEAN
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_kind component_kind;
    v_invalid_count BIGINT;
BEGIN
    SELECT component_type
    INTO v_kind
    FROM components
    WHERE component_id = p_component_id;

    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;

    IF v_kind = 'server' THEN
        RETURN TRUE;
    END IF;

    SELECT COUNT(*)
    INTO v_invalid_count
    FROM component_props
    WHERE component_id = p_component_id
      AND (
          serializable = FALSE
          OR contains_sensitive_data = TRUE
      );

    RETURN v_invalid_count = 0;
END;
$$;


/*
===============================================================================
12. RENDER ELIGIBILITY VIEW
===============================================================================
*/

CREATE OR REPLACE VIEW component_render_eligibility AS
SELECT
    c.component_id,
    c.component_name,
    c.component_type,
    c.route_id,
    r.route_path,

    CASE
        WHEN c.component_type = 'server'
             AND c.uses_browser_api THEN FALSE

        WHEN c.component_type = 'client'
             AND c.server_only_module THEN FALSE

        WHEN c.component_type = 'client'
             AND c.uses_server_secret THEN FALSE

        ELSE component_serialization_eligible(c.component_id)
    END AS eligible,

    CASE
        WHEN c.component_type = 'server'
             AND c.uses_browser_api
            THEN 'Server Component uses browser API'

        WHEN c.component_type = 'client'
             AND c.server_only_module
            THEN 'Client Component imports server-only module'

        WHEN c.component_type = 'client'
             AND c.uses_server_secret
            THEN 'Client Component exposes server secret'

        WHEN NOT component_serialization_eligible(c.component_id)
            THEN 'Invalid or sensitive component props'

        ELSE 'Eligible'
    END AS evaluation_message

FROM components c
JOIN routes r
    ON r.route_id = c.route_id;


/*
===============================================================================
13. ROUTE HIERARCHY REPORT
===============================================================================
*/

CREATE OR REPLACE VIEW route_hierarchy AS
WITH RECURSIVE route_tree AS (
    SELECT
        route_id,
        application_id,
        parent_route_id,
        route_segment,
        route_path,
        0 AS depth,
        route_path::TEXT AS hierarchy_path
    FROM routes
    WHERE parent_route_id IS NULL

    UNION ALL

    SELECT
        child.route_id,
        child.application_id,
        child.parent_route_id,
        child.route_segment,
        child.route_path,
        parent.depth + 1,
        parent.hierarchy_path || ' / ' || child.route_segment
    FROM routes child
    JOIN route_tree parent
        ON child.parent_route_id = parent.route_id
       AND child.application_id = parent.application_id
)
SELECT *
FROM route_tree;


/*
===============================================================================
14. PERFORMANCE AND EXECUTION REPORT
===============================================================================
*/

CREATE OR REPLACE VIEW rendering_performance_report AS
SELECT
    rr.application_id,
    rr.request_status,
    COUNT(*) AS request_count,

    ROUND(
        AVG(rr.duration_ms),
        2
    ) AS average_duration_ms,

    ROUND(
        MAX(rr.duration_ms),
        2
    ) AS maximum_duration_ms,

    COUNT(*) FILTER (
        WHERE rr.request_status = 'failed'
    ) AS failed_requests,

    COUNT(*) FILTER (
        WHERE rr.request_status = 'timed_out'
    ) AS timed_out_requests

FROM render_requests rr
GROUP BY
    rr.application_id,
    rr.request_status;


/*
===============================================================================
15. SAMPLE APPLICATION
===============================================================================
*/

INSERT INTO applications (
    application_name,
    framework,
    framework_version,
    app_router_enabled
)
VALUES (
    'Enterprise Dashboard',
    'Next.js',
    '16.0',
    TRUE
)
ON CONFLICT (application_name)
DO UPDATE SET
    framework_version = EXCLUDED.framework_version,
    app_router_enabled = EXCLUDED.app_router_enabled;


INSERT INTO routes (
    application_id,
    parent_route_id,
    route_segment,
    route_path,
    loading_enabled,
    error_boundary_enabled,
    not_found_enabled
)
SELECT
    application_id,
    NULL,
    'dashboard',
    '/dashboard',
    TRUE,
    TRUE,
    TRUE
FROM applications
WHERE application_name = 'Enterprise Dashboard'
ON CONFLICT (application_id, route_path)
DO NOTHING;


INSERT INTO routes (
    application_id,
    parent_route_id,
    route_segment,
    route_path,
    loading_enabled,
    error_boundary_enabled,
    not_found_enabled
)
SELECT
    parent.application_id,
    parent.route_id,
    child.route_segment,
    child.route_path,
    TRUE,
    TRUE,
    TRUE
FROM routes parent
CROSS JOIN (
    VALUES
        ('analytics', '/dashboard/analytics'),
        ('reports', '/dashboard/reports')
) AS child(route_segment, route_path)
WHERE parent.route_path = '/dashboard'
ON CONFLICT (application_id, route_path)
DO NOTHING;


/*
===============================================================================
16. COMPONENT SAMPLE RECORDS
===============================================================================
*/

INSERT INTO components (
    application_id,
    route_id,
    component_name,
    component_type,
    client_boundary,
    uses_browser_api,
    uses_server_secret,
    server_only_module,
    interactive
)
SELECT
    r.application_id,
    r.route_id,
    sample.component_name,
    sample.component_type::component_kind,
    sample.client_boundary,
    sample.uses_browser_api,
    sample.uses_server_secret,
    sample.server_only_module,
    sample.interactive
FROM routes r
CROSS JOIN (
    VALUES
        (
            'DashboardPage',
            'server',
            FALSE,
            FALSE,
            FALSE,
            FALSE,
            FALSE
        ),
        (
            'DashboardControls',
            'client',
            TRUE,
            TRUE,
            FALSE,
            FALSE,
            TRUE
        ),
        (
            'AnalyticsPage',
            'server',
            FALSE,
            FALSE,
            FALSE,
            FALSE,
            FALSE
        ),
        (
            'AnalyticsChart',
            'client',
            TRUE,
            TRUE,
            FALSE,
            FALSE,
            TRUE
        ),
        (
            'ReportsPage',
            'server',
            FALSE,
            FALSE,
            FALSE,
            FALSE,
            FALSE
        ),
        (
            'ReportsFilters',
            'client',
            TRUE,
            TRUE,
            FALSE,
            FALSE,
            TRUE
        )
) AS sample(
    component_name,
    component_type,
    client_boundary,
    uses_browser_api,
    uses_server_secret,
    server_only_module,
    interactive
)
WHERE
    (r.route_path = '/dashboard'
        AND sample.component_name IN (
            'DashboardPage',
            'DashboardControls'
        ))
    OR
    (r.route_path = '/dashboard/analytics'
        AND sample.component_name IN (
            'AnalyticsPage',
            'AnalyticsChart'
        ))
    OR
    (r.route_path = '/dashboard/reports'
        AND sample.component_name IN (
            'ReportsPage',
            'ReportsFilters'
        ))
ON CONFLICT (route_id, component_name)
DO NOTHING;


/*
===============================================================================
17. DATA RESOURCE SAMPLE RECORDS
===============================================================================
*/

INSERT INTO data_resources (
    application_id,
    resource_name,
    resource_type,
    server_only,
    sensitive,
    cache_enabled
)
SELECT
    application_id,
    sample.resource_name,
    sample.resource_type,
    sample.server_only,
    sample.sensitive,
    sample.cache_enabled
FROM applications
CROSS JOIN (
    VALUES
        (
            'user_repository',
            'database',
            TRUE,
            TRUE,
            TRUE
        ),
        (
            'dashboard_metrics',
            'database',
            TRUE,
            FALSE,
            TRUE
        ),
        (
            'analytics_api',
            'external_api',
            TRUE,
            FALSE,
            TRUE
        ),
        (
            'public_configuration',
            'configuration',
            FALSE,
            FALSE,
            TRUE
        )
) AS sample(
    resource_name,
    resource_type,
    server_only,
    sensitive,
    cache_enabled
)
WHERE application_name = 'Enterprise Dashboard'
ON CONFLICT (application_id, resource_name)
DO NOTHING;


/*
===============================================================================
18. COMPONENT DATA ACCESS
===============================================================================
*/

INSERT INTO component_data_access (
    component_id,
    resource_id,
    access_type
)
SELECT
    c.component_id,
    d.resource_id,
    'read'
FROM components c
JOIN data_resources d
    ON d.application_id = c.application_id
WHERE c.component_name = 'DashboardPage'
  AND d.resource_name IN (
      'user_repository',
      'dashboard_metrics'
  )
ON CONFLICT DO NOTHING;


INSERT INTO component_data_access (
    component_id,
    resource_id,
    access_type
)
SELECT
    c.component_id,
    d.resource_id,
    'read'
FROM components c
JOIN data_resources d
    ON d.application_id = c.application_id
WHERE c.component_name = 'AnalyticsPage'
  AND d.resource_name = 'analytics_api'
ON CONFLICT DO NOTHING;


/*
===============================================================================
19. COMPONENT PROPS
===============================================================================
*/

INSERT INTO component_props (
    component_id,
    prop_name,
    prop_value,
    serializable,
    contains_sensitive_data
)
SELECT
    component_id,
    'theme',
    '"dark"'::JSONB,
    TRUE,
    FALSE
FROM components
WHERE component_name = 'DashboardControls'
ON CONFLICT (component_id, prop_name)
DO UPDATE SET
    prop_value = EXCLUDED.prop_value;


/*
===============================================================================
20. BOUNDARY CONFIGURATION
===============================================================================
*/

INSERT INTO rendering_boundaries (
    route_id,
    component_id,
    boundary_name,
    boundary_type,
    fallback_content,
    timeout_ms
)
SELECT
    r.route_id,
    c.component_id,
    'AnalyticsSuspense',
    'suspense',
    'Loading analytics...',
    5000
FROM routes r
JOIN components c
    ON c.route_id = r.route_id
WHERE r.route_path = '/dashboard/analytics'
  AND c.component_name = 'AnalyticsChart'
ON CONFLICT DO NOTHING;


INSERT INTO rendering_boundaries (
    route_id,
    component_id,
    boundary_name,
    boundary_type,
    fallback_content,
    timeout_ms
)
SELECT
    r.route_id,
    c.component_id,
    'DashboardErrorBoundary',
    'error',
    'Dashboard temporarily unavailable.',
    NULL
FROM routes r
JOIN components c
    ON c.route_id = r.route_id
WHERE r.route_path = '/dashboard'
  AND c.component_name = 'DashboardPage'
ON CONFLICT DO NOTHING;


/*
===============================================================================
21. SAMPLE RENDER REQUESTS
===============================================================================
*/

INSERT INTO render_requests (
    request_id,
    application_id,
    route_id,
    request_method,
    request_status,
    started_at,
    completed_at,
    duration_ms
)
SELECT
    sample.request_id::UUID,
    a.application_id,
    r.route_id,
    'GET',
    sample.request_status::execution_status,
    CURRENT_TIMESTAMP - sample.duration_seconds * INTERVAL '1 second',
    CURRENT_TIMESTAMP,
    sample.duration_seconds * 1000
FROM applications a
JOIN routes r
    ON r.application_id = a.application_id
CROSS JOIN (
    VALUES
        (
            '11111111-1111-4111-8111-111111111111',
            '/dashboard',
            'succeeded',
            0.145
        ),
        (
            '22222222-2222-4222-8222-222222222222',
            '/dashboard/analytics',
            'succeeded',
            0.320
        ),
        (
            '33333333-3333-4333-8333-333333333333',
            '/dashboard/reports',
            'failed',
            1.500
        ),
        (
            '44444444-4444-4444-8444-444444444444',
            '/dashboard/analytics',
            'timed_out',
            5.000
        )
) AS sample(
    request_id,
    route_path,
    request_status,
    duration_seconds
)
WHERE
    a.application_name = 'Enterprise Dashboard'
    AND r.route_path = sample.route_path
ON CONFLICT (request_id)
DO NOTHING;


/*
===============================================================================
22. RENDER EVENTS
===============================================================================
*/

INSERT INTO render_events (
    request_id,
    component_id,
    boundary_id,
    event_state,
    event_message,
    duration_ms
)
SELECT
    rr.request_id,
    c.component_id,
    b.boundary_id,
    sample.event_state::render_state,
    sample.event_message,
    sample.duration_ms
FROM (
    VALUES
        (
            '11111111-1111-4111-8111-111111111111',
            'DashboardPage',
            'ready',
            'Server Component rendered successfully',
            75.0
        ),
        (
            '11111111-1111-4111-8111-111111111111',
            'DashboardControls',
            'ready',
            'Client Component props prepared',
            12.0
        ),
        (
            '22222222-2222-4222-8222-222222222222',
            'AnalyticsChart',
            'streaming',
            'Analytics data pending',
            100.0
        ),
        (
            '22222222-2222-4222-8222-222222222222',
            'AnalyticsChart',
            'ready',
            'Analytics data completed',
            220.0
        ),
        (
            '33333333-3333-4333-8333-333333333333',
            'ReportsPage',
            'error',
            'Database connection failed',
            1500.0
        ),
        (
            '44444444-4444-4444-8444-444444444444',
            'AnalyticsChart',
            'loading',
            'Analytics query started',
            0.0
        ),
        (
            '44444444-4444-4444-8444-444444444444',
            'AnalyticsChart',
            'streaming',
            'Loading fallback displayed',
            5000.0
        )
) AS sample(
    request_id,
    component_name,
    event_state,
    event_message,
    duration_ms
)
JOIN render_requests rr
    ON rr.request_id = sample.request_id::UUID
LEFT JOIN components c
    ON c.component_name = sample.component_name
   AND c.application_id = rr.application_id
LEFT JOIN rendering_boundaries b
    ON b.component_id = c.component_id
ON CONFLICT DO NOTHING;


/*
===============================================================================
23. ERROR AND RECOVERY SAMPLE RECORDS
===============================================================================
*/

INSERT INTO render_errors (
    request_id,
    component_id,
    error_code,
    error_message,
    recoverable,
    retry_count
)
SELECT
    rr.request_id,
    c.component_id,
    'DATABASE_CONNECTION_FAILED',
    'Database connection interrupted while loading reports.',
    TRUE,
    1
FROM render_requests rr
JOIN components c
    ON c.application_id = rr.application_id
WHERE rr.request_id =
    '33333333-3333-4333-8333-333333333333'
  AND c.component_name = 'ReportsPage'
ON CONFLICT DO NOTHING;


INSERT INTO recovery_attempts (
    error_id,
    attempt_number,
    recovery_status,
    recovery_message
)
SELECT
    error_id,
    1,
    'succeeded',
    'Database connection restored and component rendered again.'
FROM render_errors
WHERE error_code = 'DATABASE_CONNECTION_FAILED'
ON CONFLICT (error_id, attempt_number)
DO NOTHING;


/*
===============================================================================
24. CACHE SAMPLE RECORDS
===============================================================================
*/

INSERT INTO request_cache (
    request_id,
    cache_key,
    resource_id,
    cache_value,
    expires_at
)
SELECT
    rr.request_id,
    'dashboard:metrics',
    dr.resource_id,
    '{"projects":12,"pendingTasks":8,"completedTasks":24}'::JSONB,
    CURRENT_TIMESTAMP + INTERVAL '5 minutes'
FROM render_requests rr
JOIN data_resources dr
    ON dr.application_id = rr.application_id
WHERE rr.request_id =
    '11111111-1111-4111-8111-111111111111'
  AND dr.resource_name = 'dashboard_metrics'
ON CONFLICT (request_id, cache_key)
DO NOTHING;


/*
===============================================================================
25. TRANSACTIONAL REQUEST COMPLETION
===============================================================================
*/

SAVEPOINT before_request_update;

UPDATE render_requests
SET
    request_status = 'succeeded',
    completed_at = COALESCE(completed_at, CURRENT_TIMESTAMP)
WHERE request_id =
    '11111111-1111-4111-8111-111111111111'
  AND request_status = 'succeeded';

RELEASE SAVEPOINT before_request_update;


/*
===============================================================================
26. WORKFLOW PROCESSING FUNCTION
===============================================================================
*/

CREATE OR REPLACE FUNCTION record_component_event(
    p_request_id UUID,
    p_component_id BIGINT,
    p_state render_state,
    p_message TEXT,
    p_duration_ms NUMERIC DEFAULT NULL
)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    v_event_id BIGINT;
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM render_requests
        WHERE request_id = p_request_id
    ) THEN
        RAISE EXCEPTION 'Render request does not exist.';
    END IF;

    IF p_duration_ms IS NOT NULL
       AND p_duration_ms < 0 THEN
        RAISE EXCEPTION 'Duration cannot be negative.';
    END IF;

    IF p_component_id IS NOT NULL
       AND NOT EXISTS (
           SELECT 1
           FROM components
           WHERE component_id = p_component_id
       ) THEN
        RAISE EXCEPTION 'Component does not exist.';
    END IF;

    INSERT INTO render_events (
        request_id,
        component_id,
        event_state,
        event_message,
        duration_ms
    )
    VALUES (
        p_request_id,
        p_component_id,
        p_state,
        p_message,
        p_duration_ms
    )
    RETURNING event_id INTO v_event_id;

    RETURN v_event_id;
END;
$$;


/*
===============================================================================
27. MERGE-LIKE ATOMIC RECOVERY PROCEDURE
===============================================================================
*/

CREATE OR REPLACE PROCEDURE recover_render_error(
    p_error_id BIGINT,
    p_success BOOLEAN,
    p_message TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_next_attempt INTEGER;
BEGIN
    SELECT COALESCE(MAX(attempt_number), 0) + 1
    INTO v_next_attempt
    FROM recovery_attempts
    WHERE error_id = p_error_id;

    IF NOT EXISTS (
        SELECT 1
        FROM render_errors
        WHERE error_id = p_error_id
          AND recoverable = TRUE
    ) THEN
        RAISE EXCEPTION
            'Error does not exist or is not recoverable.';
    END IF;

    INSERT INTO recovery_attempts (
        error_id,
        attempt_number,
        recovery_status,
        recovery_message
    )
    VALUES (
        p_error_id,
        v_next_attempt,
        CASE
            WHEN p_success THEN 'succeeded'::execution_status
            ELSE 'failed'::execution_status
        END,
        p_message
    );

    UPDATE render_errors
    SET retry_count = v_next_attempt
    WHERE error_id = p_error_id;
END;
$$;


/*
===============================================================================
28. RETRIEVAL QUERIES
===============================================================================
*/

/* Application route structure. */

SELECT
    a.application_name,
    h.depth,
    h.hierarchy_path
FROM route_hierarchy h
JOIN applications a
    ON a.application_id = h.application_id
ORDER BY
    a.application_name,
    h.depth,
    h.route_path;


/* Component inventory. */

SELECT
    r.route_path,
    c.component_name,
    c.component_type,
    c.interactive,
    c.client_boundary
FROM components c
JOIN routes r
    ON r.route_id = c.route_id
ORDER BY
    r.route_path,
    c.component_type;


/*
===============================================================================
29. SERIALIZATION VALIDATION QUERY
===============================================================================
*/

SELECT
    component_name,
    component_type,
    eligible,
    evaluation_message
FROM component_render_eligibility
ORDER BY component_name;


/*
===============================================================================
30. AGGREGATION AND PERFORMANCE QUERIES
===============================================================================
*/

/* Component rendering state counts. */

SELECT
    c.component_name,
    e.event_state,
    COUNT(*) AS event_count,
    ROUND(
        AVG(e.duration_ms),
        2
    ) AS average_duration_ms
FROM render_events e
JOIN components c
    ON c.component_id = e.component_id
GROUP BY
    c.component_name,
    e.event_state
ORDER BY
    c.component_name,
    e.event_state;


/* Application-level rendering performance. */

SELECT
    a.application_name,
    p.request_status,
    p.request_count,
    p.average_duration_ms,
    p.maximum_duration_ms,
    p.failed_requests,
    p.timed_out_requests
FROM rendering_performance_report p
JOIN applications a
    ON a.application_id = p.application_id
ORDER BY
    a.application_name,
    p.request_status;


/*
===============================================================================
31. LOADING AND ERROR BOUNDARY REPORT
===============================================================================
*/

SELECT
    r.route_path,
    b.boundary_name,
    b.boundary_type,
    b.fallback_content,
    b.timeout_ms
FROM rendering_boundaries b
JOIN routes r
    ON r.route_id = b.route_id
ORDER BY
    r.route_path,
    b.boundary_type;


/*
===============================================================================
32. RECOVERY EVALUATION
===============================================================================
*/

SELECT
    e.error_code,
    e.error_message,
    e.recoverable,
    e.retry_count,
    ra.attempt_number,
    ra.recovery_status,
    ra.recovery_message
FROM render_errors e
LEFT JOIN recovery_attempts ra
    ON ra.error_id = e.error_id
ORDER BY
    e.error_id,
    ra.attempt_number;


/*
===============================================================================
33. CACHE RETRIEVAL AND EXPIRATION
===============================================================================
*/

SELECT
    rr.request_id,
    rc.cache_key,
    rc.cache_value,
    rc.expires_at,
    CASE
        WHEN rc.expires_at IS NULL THEN 'NO_EXPIRY'
        WHEN rc.expires_at > CURRENT_TIMESTAMP THEN 'VALID'
        ELSE 'EXPIRED'
    END AS cache_status
FROM request_cache rc
JOIN render_requests rr
    ON rr.request_id = rc.request_id;


/*
===============================================================================
34. FAILURE-CASE VALIDATION
===============================================================================
*/

/*
A Client Component attempting to access sensitive server data
must be rejected by the trigger.

The exception is deliberately caught so the remaining SQL
demonstration can continue.
*/

DO $$
DECLARE
    v_client_id BIGINT;
    v_resource_id BIGINT;
BEGIN
    SELECT component_id
    INTO v_client_id
    FROM components
    WHERE component_name = 'DashboardControls'
    LIMIT 1;

    SELECT resource_id
    INTO v_resource_id
    FROM data_resources
    WHERE resource_name = 'user_repository'
    LIMIT 1;

    IF v_client_id IS NOT NULL
       AND v_resource_id IS NOT NULL THEN

        BEGIN
            INSERT INTO component_data_access (
                component_id,
                resource_id,
                access_type
            )
            VALUES (
                v_client_id,
                v_resource_id,
                'read'
            );

        EXCEPTION
            WHEN raise_exception THEN
                RAISE NOTICE
                    'Expected security rejection: %',
                    SQLERRM;
        END;
    END IF;
END;
$$;


/*
An invalid negative duration must be rejected by a constraint.
*/

DO $$
DECLARE
    v_rejected BOOLEAN := FALSE;
BEGIN
    BEGIN
        UPDATE render_requests
        SET duration_ms = -10
        WHERE request_id =
            '11111111-1111-4111-8111-111111111111';

    EXCEPTION
        WHEN check_violation THEN
            v_rejected := TRUE;
    END;

    IF NOT v_rejected THEN
        RAISE EXCEPTION
            'Negative duration validation did not work.';
    END IF;

    RAISE NOTICE
        'Negative duration correctly rejected.';
END;
$$;


/*
===============================================================================
35. OPERATIONAL SUMMARY
===============================================================================
*/

SELECT
    a.application_name,

    COUNT(DISTINCT r.route_id) AS total_routes,

    COUNT(DISTINCT c.component_id) AS total_components,

    COUNT(DISTINCT c.component_id)
        FILTER (
            WHERE c.component_type = 'server'
        ) AS server_components,

    COUNT(DISTINCT c.component_id)
        FILTER (
            WHERE c.component_type = 'client'
        ) AS client_components,

    COUNT(DISTINCT rr.request_id) AS total_requests,

    COUNT(DISTINCT rr.request_id)
        FILTER (
            WHERE rr.request_status = 'failed'
        ) AS failed_requests

FROM applications a
LEFT JOIN routes r
    ON r.application_id = a.application_id
LEFT JOIN components c
    ON c.application_id = a.application_id
LEFT JOIN render_requests rr
    ON rr.application_id = a.application_id
GROUP BY
    a.application_id,
    a.application_name;


/*
===============================================================================
36. COMPLETION
===============================================================================
*/

COMMIT;

RESET search_path;

/*
Operational notes:

1. Server and Client Component boundaries are modeled independently.
2. Database constraints protect declared component contracts.
3. Suspense boundaries represent loading and streaming states.
4. Error boundaries represent isolated rendering failures.
5. Recovery attempts are stored separately from original errors.
6. Request caches are scoped to individual render requests.
7. Route hierarchy uses recursive CTE traversal.
8. Indexes support route, request and event retrieval.
9. Sensitive data is not stored in Client Component props.
10. Real React Server Component serialization supports additional
    framework-defined values; the database contract is intentionally
    more restrictive.
*/
