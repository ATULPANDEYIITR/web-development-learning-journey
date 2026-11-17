-- ============================================================
-- REACT ROUTING: RELATIONAL ROUTING AND ACCESS CONTROL MODEL
-- PostgreSQL 15+
--
-- Models:
-- SPA applications, routes, nested route relationships,
-- dynamic parameters, users, roles, access policies,
-- navigation requests, redirects, and route resolution.
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS react_routing;

SET search_path TO react_routing, public;

-- ------------------------------------------------------------
-- ENUMERATIONS
-- ------------------------------------------------------------

CREATE TYPE user_role AS ENUM (
    'guest',
    'user',
    'admin'
);

CREATE TYPE route_access_policy AS ENUM (
    'public',
    'authenticated',
    'role_restricted'
);

CREATE TYPE navigation_status AS ENUM (
    'success',
    'not_found',
    'redirect',
    'forbidden'
);

-- ------------------------------------------------------------
-- APPLICATIONS
-- ------------------------------------------------------------

CREATE TABLE applications (
    application_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    application_name VARCHAR(120) NOT NULL UNIQUE,
    base_path VARCHAR(255) NOT NULL DEFAULT '/',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_base_path
        CHECK (left(base_path, 1) = '/')
);

-- ------------------------------------------------------------
-- USERS
-- ------------------------------------------------------------

CREATE TABLE app_users (
    user_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    role user_role NOT NULL DEFAULT 'guest',
    authenticated BOOLEAN NOT NULL DEFAULT FALSE,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- ROUTES
--
-- parent_route_id establishes nested route relationships.
-- path represents the full URL pattern.
-- ------------------------------------------------------------

CREATE TABLE routes (
    route_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    application_id BIGINT NOT NULL
        REFERENCES applications(application_id)
        ON DELETE CASCADE,

    parent_route_id BIGINT,

    route_name VARCHAR(120) NOT NULL,
    path VARCHAR(500) NOT NULL,
    component_name VARCHAR(150) NOT NULL,

    access_policy route_access_policy NOT NULL DEFAULT 'public',

    redirect_path VARCHAR(500),

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT route_parent_fk
        FOREIGN KEY (parent_route_id)
        REFERENCES routes(route_id)
        ON DELETE CASCADE,

    CONSTRAINT unique_route_name
        UNIQUE (application_id, route_name),

    CONSTRAINT valid_route_path
        CHECK (left(path, 1) = '/'),

    CONSTRAINT no_self_parent
        CHECK (parent_route_id IS NULL OR parent_route_id <> route_id),

    CONSTRAINT redirect_path_valid
        CHECK (redirect_path IS NULL OR left(redirect_path, 1) = '/'),

    CONSTRAINT valid_route_redirect
        CHECK (
            redirect_path IS NULL
            OR redirect_path <> path
        )
);

CREATE INDEX idx_routes_application
    ON routes(application_id, is_active);

CREATE INDEX idx_routes_parent
    ON routes(parent_route_id);

CREATE INDEX idx_routes_path
    ON routes(application_id, path);

-- ------------------------------------------------------------
-- ROUTE ROLE PERMISSIONS
-- ------------------------------------------------------------

CREATE TABLE route_role_permissions (
    route_id BIGINT NOT NULL
        REFERENCES routes(route_id)
        ON DELETE CASCADE,

    role user_role NOT NULL,

    PRIMARY KEY (route_id, role)
);

CREATE INDEX idx_route_permissions_role
    ON route_role_permissions(role, route_id);

-- ------------------------------------------------------------
-- NAVIGATION REQUESTS
-- ------------------------------------------------------------

CREATE TABLE navigation_requests (
    request_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    application_id BIGINT NOT NULL
        REFERENCES applications(application_id),

    user_id BIGINT
        REFERENCES app_users(user_id)
        ON DELETE SET NULL,

    requested_path VARCHAR(1000) NOT NULL,

    resolved_path VARCHAR(1000),

    route_id BIGINT
        REFERENCES routes(route_id)
        ON DELETE SET NULL,

    status navigation_status NOT NULL DEFAULT 'not_found',

    failure_reason TEXT,

    requested_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT requested_path_valid
        CHECK (left(requested_path, 1) = '/')
);

CREATE INDEX idx_navigation_application_date
    ON navigation_requests(application_id, requested_at DESC);

CREATE INDEX idx_navigation_status
    ON navigation_requests(status);

CREATE INDEX idx_navigation_user
    ON navigation_requests(user_id, requested_at DESC);

-- ------------------------------------------------------------
-- NAVIGATION PARAMETERS
--
-- Dynamic values such as productId=501 and userId=101.
-- ------------------------------------------------------------

CREATE TABLE navigation_parameters (
    parameter_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    request_id BIGINT NOT NULL
        REFERENCES navigation_requests(request_id)
        ON DELETE CASCADE,

    parameter_name VARCHAR(100) NOT NULL,
    parameter_value TEXT NOT NULL,

    UNIQUE (request_id, parameter_name)
);

-- ------------------------------------------------------------
-- QUERY PARAMETERS
-- ------------------------------------------------------------

CREATE TABLE navigation_query_parameters (
    query_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    request_id BIGINT NOT NULL
        REFERENCES navigation_requests(request_id)
        ON DELETE CASCADE,

    parameter_name VARCHAR(100) NOT NULL,
    parameter_value TEXT NOT NULL
);

CREATE INDEX idx_query_request
    ON navigation_query_parameters(request_id);

-- ------------------------------------------------------------
-- VALIDATE NESTED ROUTE RELATIONSHIPS
--
-- Prevent cross-application parent relationships.
-- Prevent circular ancestry.
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_route_parent()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    parent_application BIGINT;
    current_parent BIGINT;
    depth INTEGER := 0;
BEGIN
    IF NEW.parent_route_id IS NULL THEN
        RETURN NEW;
    END IF;

    SELECT application_id
    INTO parent_application
    FROM routes
    WHERE route_id = NEW.parent_route_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Parent route does not exist.';
    END IF;

    IF parent_application <> NEW.application_id THEN
        RAISE EXCEPTION
            'Parent and child routes must belong to the same application.';
    END IF;

    current_parent := NEW.parent_route_id;

    WHILE current_parent IS NOT NULL LOOP
        IF current_parent = NEW.route_id THEN
            RAISE EXCEPTION 'Circular route hierarchy detected.';
        END IF;

        SELECT parent_route_id
        INTO current_parent
        FROM routes
        WHERE route_id = current_parent;

        depth := depth + 1;

        IF depth > 100 THEN
            RAISE EXCEPTION 'Route nesting exceeds the maximum depth.';
        END IF;
    END LOOP;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_route_parent
BEFORE INSERT OR UPDATE OF parent_route_id, application_id
ON routes
FOR EACH ROW
EXECUTE FUNCTION validate_route_parent();

-- ------------------------------------------------------------
-- VALIDATE ROUTE PERMISSIONS
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_route_permission()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    policy route_access_policy;
BEGIN
    SELECT access_policy
    INTO policy
    FROM routes
    WHERE route_id = NEW.route_id;

    IF policy <> 'role_restricted' THEN
        RAISE EXCEPTION
            'Role permissions are only valid for role-restricted routes.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_route_permission
BEFORE INSERT OR UPDATE
ON route_role_permissions
FOR EACH ROW
EXECUTE FUNCTION validate_route_permission();

-- ------------------------------------------------------------
-- ENSURE ROLE-RESTRICTED ROUTES HAVE PERMISSIONS
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION enforce_route_permissions()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.access_policy = 'role_restricted'
       AND NOT EXISTS (
           SELECT 1
           FROM route_role_permissions
           WHERE route_id = NEW.route_id
       )
    THEN
        RAISE EXCEPTION
            'Role-restricted route requires at least one permitted role.';
    END IF;

    IF NEW.access_policy <> 'role_restricted'
       AND EXISTS (
           SELECT 1
           FROM route_role_permissions
           WHERE route_id = NEW.route_id
       )
    THEN
        RAISE EXCEPTION
            'Non-restricted routes cannot have role permissions.';
    END IF;

    RETURN NULL;
END;
$$;

CREATE CONSTRAINT TRIGGER trg_enforce_route_permissions
AFTER INSERT OR UPDATE OF access_policy
ON routes
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION enforce_route_permissions();

-- ------------------------------------------------------------
-- ROUTE RESOLUTION FUNCTION
--
-- Resolves an exact route pattern.
-- Supports :parameter segments and * wildcard segments.
-- Nested routes are stored separately from URL matching.
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION resolve_route(
    p_application_id BIGINT,
    p_requested_path TEXT
)
RETURNS TABLE (
    matched_route_id BIGINT,
    matched_route_name VARCHAR,
    matched_component VARCHAR,
    matched_policy route_access_policy
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    candidate RECORD;
    expected_parts TEXT[];
    actual_parts TEXT[];
    expected_segment TEXT;
    actual_segment TEXT;
    i INTEGER;
    matched BOOLEAN;
BEGIN
    IF p_requested_path IS NULL
       OR left(p_requested_path, 1) <> '/'
    THEN
        RAISE EXCEPTION 'Invalid requested path.';
    END IF;

    SELECT regexp_replace(
        regexp_replace(p_requested_path, '/+', '/', 'g'),
        '/+$',
        ''
    )
    INTO p_requested_path;

    IF p_requested_path = '' THEN
        p_requested_path := '/';
    END IF;

    actual_parts := CASE
        WHEN p_requested_path = '/' THEN ARRAY[]::TEXT[]
        ELSE string_to_array(
            substring(p_requested_path FROM 2),
            '/'
        )
    END;

    FOR candidate IN
        SELECT
            r.route_id,
            r.route_name,
            r.component_name,
            r.access_policy,
            r.path
        FROM routes r
        WHERE r.application_id = p_application_id
          AND r.is_active = TRUE
        ORDER BY
            length(r.path) DESC,
            r.route_id
    LOOP
        expected_parts := CASE
            WHEN candidate.path = '/' THEN ARRAY[]::TEXT[]
            ELSE string_to_array(
                substring(candidate.path FROM 2),
                '/'
            )
        END;

        IF cardinality(expected_parts) <> cardinality(actual_parts) THEN
            CONTINUE;
        END IF;

        matched := TRUE;

        FOR i IN 1..cardinality(expected_parts) LOOP
            expected_segment := expected_parts[i];
            actual_segment := actual_parts[i];

            IF expected_segment LIKE ':%' THEN
                IF actual_segment = '' THEN
                    matched := FALSE;
                    EXIT;
                END IF;

            ELSIF expected_segment = '*' THEN
                NULL;

            ELSIF expected_segment <> actual_segment THEN
                matched := FALSE;
                EXIT;
            END IF;
        END LOOP;

        IF matched THEN
            matched_route_id := candidate.route_id;
            matched_route_name := candidate.route_name;
            matched_component := candidate.component_name;
            matched_policy := candidate.access_policy;

            RETURN NEXT;
        END IF;
    END LOOP;

    RETURN;
END;
$$;

-- ------------------------------------------------------------
-- ROUTE ACCESS EVALUATION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION evaluate_route_access(
    p_route_id BIGINT,
    p_user_id BIGINT
)
RETURNS navigation_status
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    policy route_access_policy;
    current_role user_role;
    is_authenticated BOOLEAN;
    is_active BOOLEAN;
BEGIN
    SELECT
        r.access_policy
    INTO policy
    FROM routes r
    WHERE r.route_id = p_route_id
      AND r.is_active = TRUE;

    IF NOT FOUND THEN
        RETURN 'not_found';
    END IF;

    IF policy = 'public' THEN
        RETURN 'success';
    END IF;

    SELECT
        u.role,
        u.authenticated,
        u.active
    INTO
        current_role,
        is_authenticated,
        is_active
    FROM app_users u
    WHERE u.user_id = p_user_id;

    IF NOT FOUND
       OR NOT is_active
       OR NOT is_authenticated
    THEN
        RETURN 'redirect';
    END IF;

    IF policy = 'authenticated' THEN
        RETURN 'success';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM route_role_permissions rp
        WHERE rp.route_id = p_route_id
          AND rp.role = current_role
    ) THEN
        RETURN 'success';
    END IF;

    RETURN 'forbidden';
END;
$$;

-- ------------------------------------------------------------
-- PROCESS A NAVIGATION REQUEST
-- ------------------------------------------------------------

CREATE OR REPLACE PROCEDURE process_navigation(
    IN p_application_id BIGINT,
    IN p_user_id BIGINT,
    IN p_requested_path TEXT,
    INOUT p_request_id BIGINT DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
DECLARE
    matched RECORD;
    final_status navigation_status;
    target_path TEXT;
BEGIN
    IF p_requested_path IS NULL
       OR left(p_requested_path, 1) <> '/'
    THEN
        RAISE EXCEPTION 'Requested path must begin with /.';
    END IF;

    SELECT *
    INTO matched
    FROM resolve_route(
        p_application_id,
        p_requested_path
    )
    LIMIT 1;

    IF NOT FOUND THEN
        final_status := 'not_found';
        target_path := p_requested_path;

    ELSE
        final_status := evaluate_route_access(
            matched.matched_route_id,
            p_user_id
        );

        target_path := CASE
            WHEN final_status = 'redirect' THEN '/login'
            ELSE p_requested_path
        END;
    END IF;

    INSERT INTO navigation_requests (
        application_id,
        user_id,
        requested_path,
        resolved_path,
        route_id,
        status,
        failure_reason
    )
    VALUES (
        p_application_id,
        p_user_id,
        p_requested_path,
        target_path,
        matched.matched_route_id,
        final_status,
        CASE
            WHEN final_status = 'not_found'
                THEN 'No matching route.'
            WHEN final_status = 'redirect'
                THEN 'Authentication required.'
            WHEN final_status = 'forbidden'
                THEN 'Insufficient role permissions.'
            ELSE NULL
        END
    )
    RETURNING request_id INTO p_request_id;
END;
$$;

-- ------------------------------------------------------------
-- APPLICATION AND SAMPLE USERS
-- ------------------------------------------------------------

INSERT INTO applications (
    application_name,
    base_path
)
VALUES (
    'Enterprise React Portal',
    '/'
);

INSERT INTO app_users (
    username,
    email,
    role,
    authenticated
)
VALUES
    ('alice', 'alice@example.com', 'user', TRUE),
    ('root', 'root@example.com', 'admin', TRUE),
    ('visitor', 'visitor@example.com', 'guest', FALSE);

-- ------------------------------------------------------------
-- ROUTE DEFINITIONS
-- ------------------------------------------------------------

INSERT INTO routes (
    application_id,
    route_name,
    path,
    component_name,
    access_policy
)
VALUES
    (1, 'application', '/', 'ApplicationLayout', 'public'),
    (1, 'home', '/', 'HomePage', 'public'),
    (1, 'about', '/about', 'AboutPage', 'public'),
    (1, 'products', '/products', 'ProductsLayout', 'public'),
    (1, 'product_list', '/products', 'ProductList', 'public'),
    (1, 'product_details', '/products/:productId',
        'ProductDetails', 'public'),
    (1, 'users', '/users', 'UsersLayout', 'public'),
    (1, 'user_profile', '/users/:userId',
        'UserProfile', 'public'),
    (1, 'dashboard', '/dashboard',
        'Dashboard', 'role_restricted'),
    (1, 'admin', '/admin',
        'AdminPanel', 'role_restricted'),
    (1, 'login', '/login', 'LoginPage', 'public'),
    (1, 'account', '/account', 'AccountPage', 'authenticated');

-- ------------------------------------------------------------
-- NESTED ROUTE RELATIONSHIPS
-- ------------------------------------------------------------

UPDATE routes child
SET parent_route_id = parent.route_id
FROM routes parent
WHERE child.application_id = parent.application_id
  AND (
      (child.route_name IN ('home', 'about', 'products',
          'product_list', 'users', 'dashboard',
          'admin', 'login', 'account')
       AND parent.route_name = 'application')
      OR
      (child.route_name = 'product_details'
       AND parent.route_name = 'products')
      OR
      (child.route_name = 'user_profile'
       AND parent.route_name = 'users')
  );

-- ------------------------------------------------------------
-- ACCESS PERMISSIONS
-- ------------------------------------------------------------

INSERT INTO route_role_permissions (
    route_id,
    role
)
SELECT route_id, 'user'::user_role
FROM routes
WHERE route_name = 'dashboard';

INSERT INTO route_role_permissions (
    route_id,
    role
)
SELECT route_id, 'admin'::user_role
FROM routes
WHERE route_name IN ('dashboard', 'admin');

-- ------------------------------------------------------------
-- PROCESS EXAMPLE REQUESTS
-- ------------------------------------------------------------

CALL process_navigation(1, NULL, '/', NULL);

CALL process_navigation(1, NULL, '/products', NULL);

CALL process_navigation(1, 1, '/products/501', NULL);

CALL process_navigation(1, 1, '/dashboard', NULL);

CALL process_navigation(1, 2, '/admin', NULL);

CALL process_navigation(1, 1, '/admin', NULL);

CALL process_navigation(1, NULL, '/unknown', NULL);

-- ------------------------------------------------------------
-- VIEW: NAVIGATION REPORT
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW navigation_report AS
SELECT
    nr.request_id,
    a.application_name,
    u.username,
    nr.requested_path,
    nr.resolved_path,
    r.route_name,
    r.component_name,
    nr.status,
    nr.failure_reason,
    nr.requested_at
FROM navigation_requests nr
JOIN applications a
    ON a.application_id = nr.application_id
LEFT JOIN app_users u
    ON u.user_id = nr.user_id
LEFT JOIN routes r
    ON r.route_id = nr.route_id;

-- ------------------------------------------------------------
-- VIEW: ROUTE ACCESS CONFIGURATION
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW route_access_report AS
SELECT
    r.route_id,
    r.route_name,
    r.path,
    r.component_name,
    r.access_policy,
    COALESCE(
        array_agg(rp.role::TEXT)
            FILTER (WHERE rp.role IS NOT NULL),
        ARRAY[]::TEXT[]
    ) AS permitted_roles,
    r.parent_route_id,
    r.is_active
FROM routes r
LEFT JOIN route_role_permissions rp
    ON rp.route_id = r.route_id
GROUP BY
    r.route_id,
    r.route_name,
    r.path,
    r.component_name,
    r.access_policy,
    r.parent_route_id,
    r.is_active;

COMMIT;

-- ============================================================
-- RETRIEVAL AND REPORTING QUERIES
-- ============================================================

-- 1. List every registered route.

SELECT *
FROM route_access_report
ORDER BY route_id;

-- 2. Retrieve nested route relationships.

WITH RECURSIVE route_tree AS (
    SELECT
        route_id,
        parent_route_id,
        route_name,
        path,
        component_name,
        0 AS depth,
        route_name::TEXT AS route_hierarchy
    FROM routes
    WHERE parent_route_id IS NULL
      AND application_id = 1

    UNION ALL

    SELECT
        child.route_id,
        child.parent_route_id,
        child.route_name,
        child.path,
        child.component_name,
        parent.depth + 1,
        parent.route_hierarchy || ' -> ' || child.route_name
    FROM routes child
    JOIN route_tree parent
        ON child.parent_route_id = parent.route_id
)
SELECT *
FROM route_tree
ORDER BY route_hierarchy;

-- 3. Evaluate access for each user and route.

SELECT
    u.username,
    r.route_name,
    r.path,
    evaluate_route_access(r.route_id, u.user_id) AS access_result
FROM app_users u
CROSS JOIN routes r
WHERE r.access_policy <> 'public'
ORDER BY u.username, r.route_name;

-- 4. Navigation statistics.

SELECT
    status,
    COUNT(*) AS request_count
FROM navigation_requests
GROUP BY status
ORDER BY request_count DESC;

-- 5. Failed navigation requests.

SELECT *
FROM navigation_report
WHERE status IN ('not_found', 'redirect', 'forbidden')
ORDER BY requested_at DESC;

-- 6. Route usage frequency.

SELECT
    r.route_name,
    r.path,
    COUNT(nr.request_id) AS total_requests
FROM routes r
LEFT JOIN navigation_requests nr
    ON nr.route_id = r.route_id
GROUP BY r.route_id, r.route_name, r.path
ORDER BY total_requests DESC;

-- 7. Dynamic parameter storage example.

INSERT INTO navigation_parameters (
    request_id,
    parameter_name,
    parameter_value
)
SELECT
    request_id,
    'productId',
    '501'
FROM navigation_requests
WHERE requested_path = '/products/501'
ORDER BY request_id DESC
LIMIT 1
ON CONFLICT (request_id, parameter_name)
DO UPDATE SET parameter_value = EXCLUDED.parameter_value;

-- 8. Query parameter storage example.

INSERT INTO navigation_query_parameters (
    request_id,
    parameter_name,
    parameter_value
)
SELECT
    request_id,
    'tab',
    'activity'
FROM navigation_requests
WHERE requested_path = '/products/501'
ORDER BY request_id DESC
LIMIT 1;

-- 9. Validate that all role-restricted routes have permissions.

SELECT
    r.route_name,
    COUNT(rp.role) AS permission_count,
    COUNT(rp.role) > 0 AS permissions_valid
FROM routes r
LEFT JOIN route_role_permissions rp
    ON rp.route_id = r.route_id
WHERE r.access_policy = 'role_restricted'
GROUP BY r.route_id, r.route_name;

-- 10. Recent navigation requests using a CTE.

WITH recent_requests AS (
    SELECT *
    FROM navigation_requests
    WHERE requested_at >= CURRENT_TIMESTAMP - INTERVAL '7 days'
)
SELECT
    status,
    COUNT(*) AS total_requests,
    COUNT(DISTINCT user_id) AS distinct_users
FROM recent_requests
GROUP BY status
ORDER BY total_requests DESC;
