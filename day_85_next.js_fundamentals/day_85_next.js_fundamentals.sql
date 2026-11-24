/*
 * NEXT.JS FUNDAMENTALS
 *
 * PostgreSQL 15+
 *
 * Relational model for:
 * - Applications
 * - File-system route segments
 * - Pages
 * - Nested layouts
 * - Components
 * - Server/client execution boundaries
 * - Component dependencies
 * - Navigation events
 * - Rendering requests
 * - Authentication and access decisions
 *
 * Run as a database user permitted to create schemas.
 */

BEGIN;

CREATE SCHEMA IF NOT EXISTS nextjs_lab;

SET search_path TO nextjs_lab, public;

-- ============================================================
-- 1. DOMAIN TYPES
-- ============================================================

CREATE TYPE component_kind AS ENUM (
    'server',
    'client'
);

CREATE TYPE segment_kind AS ENUM (
    'static',
    'dynamic',
    'catch_all'
);

CREATE TYPE render_status AS ENUM (
    'success',
    'not_found',
    'unauthorized',
    'error'
);

CREATE TYPE navigation_status AS ENUM (
    'started',
    'completed',
    'failed'
);

-- ============================================================
-- 2. APPLICATIONS
-- ============================================================

CREATE TABLE applications (
    application_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    application_name VARCHAR(120) NOT NULL UNIQUE,
    framework VARCHAR(40) NOT NULL DEFAULT 'Next.js',
    architecture VARCHAR(30) NOT NULL DEFAULT 'App Router',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_framework
        CHECK (framework IN ('Next.js')),

    CONSTRAINT valid_architecture
        CHECK (architecture IN ('App Router', 'Pages Router'))
);

INSERT INTO applications (
    application_name,
    framework,
    architecture
)
VALUES (
    'Enterprise Documentation Portal',
    'Next.js',
    'App Router'
);

-- ============================================================
-- 3. ROUTE SEGMENTS
-- ============================================================

CREATE TABLE route_segments (
    segment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    application_id BIGINT NOT NULL
        REFERENCES applications(application_id)
        ON DELETE CASCADE,

    segment_name VARCHAR(120) NOT NULL,
    segment_type segment_kind NOT NULL,
    segment_position INTEGER NOT NULL,

    CONSTRAINT valid_segment_name
        CHECK (
            segment_name <> ''
            AND segment_name !~ '[/\\]'
        ),

    CONSTRAINT valid_position
        CHECK (segment_position >= 0),

    CONSTRAINT unique_segment_position
        UNIQUE (application_id, segment_position)
);

-- ============================================================
-- 4. LAYOUTS
-- ============================================================

CREATE TABLE layouts (
    layout_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    application_id BIGINT NOT NULL
        REFERENCES applications(application_id)
        ON DELETE CASCADE,

    layout_name VARCHAR(120) NOT NULL,
    layout_path VARCHAR(255) NOT NULL,
    parent_layout_id BIGINT REFERENCES layouts(layout_id),
    preserves_state BOOLEAN NOT NULL DEFAULT TRUE,
    component_type component_kind NOT NULL DEFAULT 'server',

    CONSTRAINT unique_layout_path
        UNIQUE (application_id, layout_path),

    CONSTRAINT no_self_parent
        CHECK (parent_layout_id IS DISTINCT FROM layout_id)
);

INSERT INTO layouts (
    application_id,
    layout_name,
    layout_path,
    parent_layout_id,
    preserves_state
)
VALUES
(1, 'RootLayout', 'app/layout.tsx', NULL, TRUE);

INSERT INTO layouts (
    application_id,
    layout_name,
    layout_path,
    parent_layout_id,
    preserves_state
)
VALUES
(1, 'BlogLayout', 'app/blog/layout.tsx', 1, TRUE),
(1, 'DashboardLayout', 'app/dashboard/layout.tsx', 1, TRUE);

-- ============================================================
-- 5. PAGES
-- ============================================================

CREATE TABLE pages (
    page_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    application_id BIGINT NOT NULL
        REFERENCES applications(application_id)
        ON DELETE CASCADE,

    page_name VARCHAR(120) NOT NULL,
    page_path VARCHAR(255) NOT NULL,
    page_file VARCHAR(255) NOT NULL,
    requires_authentication BOOLEAN NOT NULL DEFAULT FALSE,
    is_published BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_page_path
        UNIQUE (application_id, page_path),

    CONSTRAINT unique_page_file
        UNIQUE (application_id, page_file)
);

INSERT INTO pages (
    application_id,
    page_name,
    page_path,
    page_file,
    requires_authentication
)
VALUES
(1, 'HomePage', '/', 'app/page.tsx', FALSE),
(1, 'AboutPage', '/about', 'app/about/page.tsx', FALSE),
(1, 'BlogIndex', '/blog', 'app/blog/page.tsx', FALSE),
(1, 'BlogPost', '/blog/[slug]', 'app/blog/[slug]/page.tsx', FALSE),
(1, 'Dashboard', '/dashboard', 'app/dashboard/page.tsx', TRUE),
(1, 'Documentation', '/docs/[...slug]', 'app/docs/[...slug]/page.tsx', FALSE);

-- ============================================================
-- 6. PAGE-LAYOUT RELATIONSHIP
-- ============================================================

CREATE TABLE page_layouts (
    page_id BIGINT NOT NULL
        REFERENCES pages(page_id)
        ON DELETE CASCADE,

    layout_id BIGINT NOT NULL
        REFERENCES layouts(layout_id)
        ON DELETE RESTRICT,

    nesting_order INTEGER NOT NULL,

    PRIMARY KEY (page_id, layout_id),

    CONSTRAINT valid_nesting_order
        CHECK (nesting_order >= 0),

    CONSTRAINT unique_page_layout_order
        UNIQUE (page_id, nesting_order)
);

INSERT INTO page_layouts (page_id, layout_id, nesting_order)
VALUES
(1, 1, 0),
(2, 1, 0),
(3, 1, 0),
(3, 2, 1),
(4, 1, 0),
(4, 2, 1),
(5, 1, 0),
(5, 3, 1),
(6, 1, 0);

-- ============================================================
-- 7. COMPONENTS
-- ============================================================

CREATE TABLE components (
    component_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    application_id BIGINT NOT NULL
        REFERENCES applications(application_id)
        ON DELETE CASCADE,

    component_name VARCHAR(120) NOT NULL,
    component_file VARCHAR(255) NOT NULL,
    component_type component_kind NOT NULL DEFAULT 'server',

    uses_state BOOLEAN NOT NULL DEFAULT FALSE,
    uses_effect BOOLEAN NOT NULL DEFAULT FALSE,
    uses_browser_api BOOLEAN NOT NULL DEFAULT FALSE,
    has_event_handlers BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_component_file
        UNIQUE (application_id, component_file),

    CONSTRAINT unique_component_name
        UNIQUE (application_id, component_name)
);

INSERT INTO components (
    application_id,
    component_name,
    component_file,
    component_type
)
VALUES
(1, 'RootLayout', 'app/layout.tsx', 'server'),
(1, 'Logo', 'app/components/logo.tsx', 'server'),
(1, 'Navigation', 'app/components/navigation.tsx', 'server');

INSERT INTO components (
    application_id,
    component_name,
    component_file,
    component_type,
    uses_state,
    has_event_handlers
)
VALUES
(1, 'SearchBox', 'app/components/search-box.tsx', 'client', TRUE, TRUE),
(1, 'ThemeToggle', 'app/components/theme-toggle.tsx', 'client', TRUE, TRUE);

INSERT INTO components (
    application_id,
    component_name,
    component_file,
    component_type,
    uses_state
)
VALUES
(1, 'InvalidServerCounter', 'app/components/invalid-counter.tsx',
 'server', TRUE);

-- ============================================================
-- 8. COMPONENT DEPENDENCIES
-- ============================================================

CREATE TABLE component_dependencies (
    parent_component_id BIGINT NOT NULL
        REFERENCES components(component_id)
        ON DELETE CASCADE,

    child_component_id BIGINT NOT NULL
        REFERENCES components(component_id)
        ON DELETE CASCADE,

    PRIMARY KEY (
        parent_component_id,
        child_component_id
    ),

    CONSTRAINT no_direct_self_dependency
        CHECK (
            parent_component_id <> child_component_id
        )
);

INSERT INTO component_dependencies
(parent_component_id, child_component_id)
VALUES
(3, 2),
(3, 4),
(1, 3),
(1, 5);

-- ============================================================
-- 9. ROUTE ACCESS POLICIES
-- ============================================================

CREATE TABLE route_roles (
    page_id BIGINT NOT NULL
        REFERENCES pages(page_id)
        ON DELETE CASCADE,

    role_name VARCHAR(80) NOT NULL,

    PRIMARY KEY (page_id, role_name)
);

INSERT INTO route_roles (page_id, role_name)
VALUES
(5, 'developer'),
(5, 'administrator');

-- ============================================================
-- 10. USERS AND ROLES
-- ============================================================

CREATE TABLE application_users (
    user_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_roles (
    user_id BIGINT NOT NULL
        REFERENCES application_users(user_id)
        ON DELETE CASCADE,

    role_name VARCHAR(80) NOT NULL,

    PRIMARY KEY (user_id, role_name)
);

INSERT INTO application_users (username, is_active)
VALUES
('developer_user', TRUE),
('visitor_user', TRUE),
('disabled_user', FALSE);

INSERT INTO user_roles (user_id, role_name)
VALUES
(1, 'developer'),
(1, 'viewer');

-- ============================================================
-- 11. NAVIGATION REQUESTS
-- ============================================================

CREATE TABLE navigation_requests (
    navigation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    application_id BIGINT NOT NULL
        REFERENCES applications(application_id),

    user_id BIGINT
        REFERENCES application_users(user_id),

    source_path VARCHAR(500),
    destination_path VARCHAR(500) NOT NULL,

    status navigation_status NOT NULL DEFAULT 'started',

    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ,

    CONSTRAINT valid_navigation_time
        CHECK (
            completed_at IS NULL
            OR completed_at >= started_at
        )
);

-- ============================================================
-- 12. RENDERING REQUESTS
-- ============================================================

CREATE TABLE render_requests (
    request_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    application_id BIGINT NOT NULL
        REFERENCES applications(application_id),

    page_id BIGINT
        REFERENCES pages(page_id),

    user_id BIGINT
        REFERENCES application_users(user_id),

    requested_path VARCHAR(500) NOT NULL,

    status render_status NOT NULL DEFAULT 'success',

    response_time_ms INTEGER,
    error_message TEXT,

    requested_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_response_time
        CHECK (
            response_time_ms IS NULL
            OR response_time_ms >= 0
        )
);

-- ============================================================
-- 13. COMPONENT VALIDATION
-- ============================================================

CREATE OR REPLACE FUNCTION validate_component_boundary()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.component_type = 'server'
       AND (
           NEW.uses_state
           OR NEW.uses_effect
           OR NEW.uses_browser_api
           OR NEW.has_event_handlers
       )
    THEN
        RAISE EXCEPTION
            'Server Component % uses client-only functionality',
            NEW.component_name;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER component_boundary_trigger
BEFORE INSERT OR UPDATE ON components
FOR EACH ROW
EXECUTE FUNCTION validate_component_boundary();

-- ============================================================
-- 14. ROUTE RESOLUTION FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION resolve_route(
    p_application_id BIGINT,
    p_path TEXT
)
RETURNS TABLE (
    resolved_page_id BIGINT,
    resolved_page_name VARCHAR,
    resolved_page_path VARCHAR,
    requires_authentication BOOLEAN
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_path TEXT;
BEGIN
    IF p_path IS NULL
       OR length(p_path) > 500
       OR p_path !~ '^/'
       OR p_path ~ '[\\]'
    THEN
        RETURN;
    END IF;

    v_path := split_part(p_path, '?', 1);

    IF v_path ~ '(^|/)\.\.?(/|$)' THEN
        RETURN;
    END IF;

    RETURN QUERY
    SELECT
        p.page_id,
        p.page_name::VARCHAR,
        p.page_path::VARCHAR,
        p.requires_authentication
    FROM pages p
    WHERE p.application_id = p_application_id
      AND p.is_published = TRUE
      AND (
          p.page_path = v_path
          OR (
              p.page_path LIKE '%[slug]%'
              AND v_path ~ (
                  '^' ||
                  regexp_replace(
                      regexp_replace(
                          regexp_replace(
                              p.page_path,
                              '\[slug\]',
                              '[^/]+',
                              'g'
                          ),
                          '\[\.{3}slug\]',
                          '.+',
                          'g'
                      ),
                      '/',
                      '/',
                      'g'
                  ) ||
                  '$'
              )
          )
          OR (
              p.page_path LIKE '%[...slug]%'
              AND v_path LIKE '/docs/%'
          )
      )
    ORDER BY
        CASE
            WHEN p.page_path = v_path THEN 0
            WHEN p.page_path LIKE '%[slug]%' THEN 1
            ELSE 2
        END
    LIMIT 1;
END;
$$;

-- ============================================================
-- 15. ACCESS EVALUATION
-- ============================================================

CREATE OR REPLACE FUNCTION can_access_page(
    p_page_id BIGINT,
    p_user_id BIGINT
)
RETURNS BOOLEAN
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_requires_auth BOOLEAN;
    v_active BOOLEAN;
    v_has_role BOOLEAN;
BEGIN
    SELECT requires_authentication
    INTO v_requires_auth
    FROM pages
    WHERE page_id = p_page_id
      AND is_published = TRUE;

    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;

    IF NOT v_requires_auth THEN
        RETURN TRUE;
    END IF;

    IF p_user_id IS NULL THEN
        RETURN FALSE;
    END IF;

    SELECT is_active
    INTO v_active
    FROM application_users
    WHERE user_id = p_user_id;

    IF NOT FOUND OR NOT v_active THEN
        RETURN FALSE;
    END IF;

    SELECT EXISTS (
        SELECT 1
        FROM route_roles rr
        JOIN user_roles ur
          ON ur.role_name = rr.role_name
        WHERE rr.page_id = p_page_id
          AND ur.user_id = p_user_id
    )
    INTO v_has_role;

    RETURN v_has_role;
END;
$$;

-- ============================================================
-- 16. NESTED LAYOUT REPORT
-- ============================================================

CREATE OR REPLACE VIEW page_layout_hierarchy AS
SELECT
    p.page_id,
    p.page_name,
    p.page_path,
    l.layout_name,
    l.layout_path,
    pl.nesting_order,
    l.preserves_state,
    l.component_type
FROM pages p
JOIN page_layouts pl
    ON pl.page_id = p.page_id
JOIN layouts l
    ON l.layout_id = pl.layout_id;

-- ============================================================
-- 17. COMPONENT EXECUTION REPORT
-- ============================================================

CREATE OR REPLACE VIEW component_execution_report AS
SELECT
    component_id,
    component_name,
    component_file,
    component_type,
    uses_state,
    uses_effect,
    uses_browser_api,
    has_event_handlers,
    CASE
        WHEN component_type = 'server'
         AND (
             uses_state
             OR uses_effect
             OR uses_browser_api
             OR has_event_handlers
         )
        THEN FALSE
        ELSE TRUE
    END AS boundary_valid
FROM components;

-- ============================================================
-- 18. PERFORMANCE INDEXES
-- ============================================================

CREATE INDEX idx_pages_application_path
ON pages(application_id, page_path);

CREATE INDEX idx_pages_published
ON pages(application_id, is_published)
WHERE is_published = TRUE;

CREATE INDEX idx_navigation_destination
ON navigation_requests(application_id, destination_path);

CREATE INDEX idx_navigation_started
ON navigation_requests(started_at DESC);

CREATE INDEX idx_render_page_time
ON render_requests(page_id, requested_at DESC);

CREATE INDEX idx_render_status
ON render_requests(status, requested_at DESC);

CREATE INDEX idx_user_roles_lookup
ON user_roles(user_id, role_name);

CREATE INDEX idx_page_layout_order
ON page_layouts(page_id, nesting_order);

-- ============================================================
-- 19. SAMPLE NAVIGATION AND RENDERING RECORDS
-- ============================================================

INSERT INTO navigation_requests (
    application_id,
    user_id,
    source_path,
    destination_path,
    status,
    completed_at
)
VALUES
(1, 1, '/', '/blog', 'completed', CURRENT_TIMESTAMP),
(1, 1, '/blog', '/blog/nextjs-fundamentals',
 'completed', CURRENT_TIMESTAMP),
(1, 2, '/', '/dashboard', 'failed', NULL),
(1, 1, '/dashboard', '/about',
 'completed', CURRENT_TIMESTAMP);

INSERT INTO render_requests (
    application_id,
    page_id,
    user_id,
    requested_path,
    status,
    response_time_ms,
    error_message
)
VALUES
(1, 1, 1, '/', 'success', 45, NULL),
(1, 3, 1, '/blog', 'success', 78, NULL),
(1, 4, 1, '/blog/nextjs-fundamentals',
 'success', 91, NULL),
(1, 5, 2, '/dashboard',
 'unauthorized', 12, 'Insufficient permissions'),
(1, NULL, 2, '/missing',
 'not_found', 8, 'Route not found'),
(1, 6, 1, '/docs/app/routing',
 'success', 62, NULL);

-- ============================================================
-- 20. VALIDATION AND ELIGIBILITY QUERIES
-- ============================================================

-- A. Retrieve all registered pages.
SELECT
    page_id,
    page_name,
    page_path,
    page_file,
    requires_authentication
FROM pages
WHERE application_id = 1
ORDER BY page_id;

-- B. Retrieve the nested layout hierarchy.
SELECT
    page_name,
    page_path,
    nesting_order,
    layout_name,
    layout_path,
    preserves_state
FROM page_layout_hierarchy
ORDER BY page_id, nesting_order;

-- C. Identify invalid component boundaries.
SELECT *
FROM component_execution_report
WHERE boundary_valid = FALSE;

-- D. Evaluate route resolution.
SELECT *
FROM resolve_route(1, '/blog/nextjs-fundamentals');

-- E. Evaluate dynamic route resolution.
SELECT *
FROM resolve_route(1, '/blog/database-design');

-- F. Evaluate access eligibility.
SELECT
    p.page_name,
    u.username,
    can_access_page(p.page_id, u.user_id) AS access_allowed
FROM pages p
CROSS JOIN application_users u
WHERE p.page_path = '/dashboard'
ORDER BY u.user_id;

-- G. Aggregate navigation activity.
SELECT
    destination_path,
    COUNT(*) AS total_navigations,
    COUNT(*) FILTER (
        WHERE status = 'completed'
    ) AS completed,
    COUNT(*) FILTER (
        WHERE status = 'failed'
    ) AS failed
FROM navigation_requests
GROUP BY destination_path
ORDER BY total_navigations DESC;

-- H. Rendering performance report.
SELECT
    p.page_name,
    COUNT(r.request_id) AS requests,
    ROUND(AVG(r.response_time_ms), 2) AS average_response_ms,
    MAX(r.response_time_ms) AS maximum_response_ms
FROM pages p
LEFT JOIN render_requests r
    ON r.page_id = p.page_id
GROUP BY p.page_id, p.page_name
ORDER BY requests DESC;

-- I. Error monitoring.
SELECT
    requested_path,
    status,
    error_message,
    requested_at
FROM render_requests
WHERE status IN ('error', 'not_found', 'unauthorized')
ORDER BY requested_at DESC;

-- J. Component dependency report.
SELECT
    parent.component_name AS importing_component,
    child.component_name AS imported_component
FROM component_dependencies d
JOIN components parent
    ON parent.component_id = d.parent_component_id
JOIN components child
    ON child.component_id = d.child_component_id
ORDER BY parent.component_name;

-- ============================================================
-- 21. TRANSACTIONAL PAGE PUBLICATION
-- ============================================================

-- Demonstrates atomic publication of an existing page.
DO $$
BEGIN
    UPDATE pages
    SET is_published = TRUE
    WHERE application_id = 1
      AND page_path = '/about';

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Page publication failed';
    END IF;
END;
$$;

-- ============================================================
-- 22. NAVIGATION COMPLETION PROCEDURE
-- ============================================================

CREATE OR REPLACE PROCEDURE complete_navigation(
    p_navigation_id BIGINT,
    p_success BOOLEAN
)
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE navigation_requests
    SET
        status = CASE
            WHEN p_success THEN 'completed'::navigation_status
            ELSE 'failed'::navigation_status
        END,
        completed_at = CURRENT_TIMESTAMP
    WHERE navigation_id = p_navigation_id
      AND status = 'started';

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Navigation % is missing or is not in started state',
            p_navigation_id;
    END IF;
END;
$$;

-- ============================================================
-- 23. EXAMPLE WORKFLOW TRANSACTION
-- ============================================================

DO $$
DECLARE
    v_navigation_id BIGINT;
BEGIN
    INSERT INTO navigation_requests (
        application_id,
        user_id,
        source_path,
        destination_path,
        status
    )
    VALUES (
        1,
        1,
        '/',
        '/about',
        'started'
    )
    RETURNING navigation_id INTO v_navigation_id;

    CALL complete_navigation(v_navigation_id, TRUE);
END;
$$;

-- ============================================================
-- 24. CTE: APPLICATION ARCHITECTURE REPORT
-- ============================================================

WITH page_statistics AS (
    SELECT
        application_id,
        COUNT(*) AS total_pages,
        COUNT(*) FILTER (
            WHERE requires_authentication
        ) AS protected_pages,
        COUNT(*) FILTER (
            WHERE is_published
        ) AS published_pages
    FROM pages
    GROUP BY application_id
),
layout_statistics AS (
    SELECT
        application_id,
        COUNT(*) AS total_layouts
    FROM layouts
    GROUP BY application_id
),
component_statistics AS (
    SELECT
        application_id,
        COUNT(*) AS total_components,
        COUNT(*) FILTER (
            WHERE component_type = 'server'
        ) AS server_components,
        COUNT(*) FILTER (
            WHERE component_type = 'client'
        ) AS client_components
    FROM components
    GROUP BY application_id
)
SELECT
    a.application_name,
    ps.total_pages,
    ps.protected_pages,
    ps.published_pages,
    ls.total_layouts,
    cs.total_components,
    cs.server_components,
    cs.client_components
FROM applications a
JOIN page_statistics ps
    ON ps.application_id = a.application_id
JOIN layout_statistics ls
    ON ls.application_id = a.application_id
JOIN component_statistics cs
    ON cs.application_id = a.application_id;

-- ============================================================
-- 25. DATA INTEGRITY TEST
-- ============================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pages
        WHERE page_path = '/'
    ) THEN
        RAISE EXCEPTION 'Root page is missing';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM layouts
        WHERE layout_name = 'RootLayout'
    ) THEN
        RAISE EXCEPTION 'Root layout is missing';
    END IF;

    IF NOT can_access_page(5, 1) THEN
        RAISE EXCEPTION
            'Developer should have dashboard access';
    END IF;

    IF can_access_page(5, 2) THEN
        RAISE EXCEPTION
            'Visitor must not access dashboard';
    END IF;

    IF can_access_page(5, 3) THEN
        RAISE EXCEPTION
            'Inactive user must not access dashboard';
    END IF;

    IF (
        SELECT COUNT(*)
        FROM page_layouts
        WHERE page_id = 4
    ) <> 2 THEN
        RAISE EXCEPTION
            'Blog post must have two nested layouts';
    END IF;

    RAISE NOTICE 'All database integrity checks passed';
END;
$$;

COMMIT;

-- ============================================================
-- 26. OPTIONAL OPERATIONAL QUERIES
-- ============================================================

-- Inspect the application structure.
SELECT
    a.application_name,
    p.page_name,
    p.page_path,
    l.layout_name,
    pl.nesting_order
FROM applications a
JOIN pages p
    ON p.application_id = a.application_id
LEFT JOIN page_layouts pl
    ON pl.page_id = p.page_id
LEFT JOIN layouts l
    ON l.layout_id = pl.layout_id
ORDER BY p.page_id, pl.nesting_order;

-- Inspect unsuccessful navigation.
SELECT *
FROM navigation_requests
WHERE status = 'failed'
ORDER BY started_at DESC;

-- Inspect Server and Client Component distribution.
SELECT
    component_type,
    COUNT(*) AS component_count
FROM components
GROUP BY component_type
ORDER BY component_type;
