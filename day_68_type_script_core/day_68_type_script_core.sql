-- ============================================================
-- TYPESCRIPT CORE: POSTGRESQL DATA MODEL
-- Arrays, Objects, Tuples, Enums, Unions, Intersections, Aliases
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS typescript_core;

SET search_path TO typescript_core, public;

-- ------------------------------------------------------------
-- 1. Type aliases using DOMAIN
-- ------------------------------------------------------------

CREATE DOMAIN user_id AS BIGINT
CHECK (VALUE > 0);

CREATE DOMAIN valid_email AS TEXT
CHECK (
    VALUE ~ '^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$'
);

CREATE DOMAIN score_value AS NUMERIC(5, 2)
CHECK (VALUE >= 0 AND VALUE <= 100);

CREATE DOMAIN non_empty_text AS TEXT
CHECK (length(trim(VALUE)) > 0);


-- ------------------------------------------------------------
-- 2. Enums
-- ------------------------------------------------------------

CREATE TYPE user_role AS ENUM (
    'ADMIN',
    'DEVELOPER',
    'ANALYST',
    'VIEWER'
);

CREATE TYPE account_status AS ENUM (
    'ACTIVE',
    'SUSPENDED',
    'PENDING'
);

CREATE TYPE project_status AS ENUM (
    'PLANNED',
    'IN_PROGRESS',
    'COMPLETED'
);

CREATE TYPE api_result_kind AS ENUM (
    'SUCCESS',
    'ERROR'
);


-- ------------------------------------------------------------
-- 3. Composite types representing objects
-- ------------------------------------------------------------

CREATE TYPE profile_object AS (
    display_name TEXT,
    email TEXT,
    location TEXT
);

CREATE TYPE permission_object AS (
    can_read BOOLEAN,
    can_write BOOLEAN,
    can_delete BOOLEAN
);

CREATE TYPE audit_object AS (
    created_by BIGINT,
    created_at TIMESTAMPTZ
);


-- ------------------------------------------------------------
-- 4. Tuple-like composite type
-- ------------------------------------------------------------

CREATE TYPE coordinate_tuple AS (
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION
);

CREATE FUNCTION make_coordinate(
    p_latitude DOUBLE PRECISION,
    p_longitude DOUBLE PRECISION
)
RETURNS coordinate_tuple
LANGUAGE plpgsql
IMMUTABLE
AS $$
BEGIN
    IF p_latitude IS NULL OR p_longitude IS NULL THEN
        RAISE EXCEPTION 'Coordinates cannot be NULL';
    END IF;

    IF p_latitude NOT BETWEEN -90 AND 90 THEN
        RAISE EXCEPTION 'Invalid latitude';
    END IF;

    IF p_longitude NOT BETWEEN -180 AND 180 THEN
        RAISE EXCEPTION 'Invalid longitude';
    END IF;

    RETURN ROW(
        p_latitude,
        p_longitude
    )::coordinate_tuple;
END;
$$;


-- ------------------------------------------------------------
-- 5. User objects and array fields
-- ------------------------------------------------------------

CREATE TABLE users (
    id user_id PRIMARY KEY,
    display_name non_empty_text NOT NULL,
    email valid_email NOT NULL UNIQUE,
    location non_empty_text NOT NULL,
    role user_role NOT NULL DEFAULT 'VIEWER',
    status account_status NOT NULL DEFAULT 'PENDING',

    -- PostgreSQL native array.
    tags TEXT[] NOT NULL DEFAULT '{}',

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_tags CHECK (
        array_position(tags, NULL) IS NULL
    )
);

CREATE INDEX idx_users_role_status
ON users(role, status);

CREATE INDEX idx_users_tags
ON users USING GIN(tags);


-- ------------------------------------------------------------
-- 6. Projects and array relationships
-- ------------------------------------------------------------

CREATE TABLE projects (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name non_empty_text NOT NULL UNIQUE,
    status project_status NOT NULL DEFAULT 'PLANNED',
    owner_id user_id NOT NULL REFERENCES users(id),
    member_ids BIGINT[] NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_member_ids CHECK (
        array_position(member_ids, NULL) IS NULL
    )
);

CREATE INDEX idx_projects_status
ON projects(status);

CREATE INDEX idx_projects_members
ON projects USING GIN(member_ids);


-- ------------------------------------------------------------
-- 7. Intersection-style resource model
-- ------------------------------------------------------------

CREATE TABLE managed_resources (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name non_empty_text NOT NULL,
    created_by user_id NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    can_read BOOLEAN NOT NULL DEFAULT TRUE,
    can_write BOOLEAN NOT NULL DEFAULT FALSE,
    can_delete BOOLEAN NOT NULL DEFAULT FALSE,

    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    CONSTRAINT metadata_must_be_object CHECK (
        jsonb_typeof(metadata) = 'object'
    )
);

CREATE INDEX idx_resources_metadata
ON managed_resources USING GIN(metadata);

CREATE INDEX idx_resources_creator
ON managed_resources(created_by);


-- ------------------------------------------------------------
-- 8. Union-style API results
-- ------------------------------------------------------------

CREATE TABLE api_results (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    result_kind api_result_kind NOT NULL,

    success_data JSONB,
    error_message TEXT,
    error_code INTEGER,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_result_variant CHECK (
        (
            result_kind = 'SUCCESS'
            AND success_data IS NOT NULL
            AND jsonb_typeof(success_data) = 'object'
            AND error_message IS NULL
            AND error_code IS NULL
        )
        OR
        (
            result_kind = 'ERROR'
            AND success_data IS NULL
            AND error_message IS NOT NULL
            AND length(trim(error_message)) > 0
            AND error_code BETWEEN 400 AND 599
        )
    )
);


-- ------------------------------------------------------------
-- 9. Generic-like reusable score records
-- ------------------------------------------------------------

CREATE TABLE assessments (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id user_id NOT NULL REFERENCES users(id),
    scores score_value[] NOT NULL,
    average_score NUMERIC(5, 2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT non_empty_scores CHECK (
        cardinality(scores) > 0
    ),

    CONSTRAINT no_null_scores CHECK (
        array_position(scores, NULL) IS NULL
    )
);

CREATE INDEX idx_assessments_user
ON assessments(user_id);


-- ------------------------------------------------------------
-- 10. Trigger for score calculations
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION calculate_assessment_average()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    total NUMERIC;
    item_count INTEGER;
BEGIN
    IF NEW.scores IS NULL OR cardinality(NEW.scores) = 0 THEN
        RAISE EXCEPTION 'At least one score is required';
    END IF;

    SELECT
        SUM(value),
        COUNT(*)
    INTO total, item_count
    FROM unnest(NEW.scores) AS value;

    NEW.average_score := ROUND(total / item_count, 2);

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_calculate_average
BEFORE INSERT OR UPDATE OF scores
ON assessments
FOR EACH ROW
EXECUTE FUNCTION calculate_assessment_average();


-- ------------------------------------------------------------
-- 11. Function: retrieve a user using an identifier
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION get_user_profile(
    p_user_id user_id
)
RETURNS TABLE (
    id BIGINT,
    display_name TEXT,
    email TEXT,
    role user_role,
    status account_status,
    tags TEXT[]
)
LANGUAGE sql
STABLE
AS $$
    SELECT
        u.id::BIGINT,
        u.display_name::TEXT,
        u.email::TEXT,
        u.role,
        u.status,
        u.tags
    FROM users u
    WHERE u.id = p_user_id;
$$;


-- ------------------------------------------------------------
-- 12. Function: determine permissions
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION can_manage_resource(
    p_resource_id BIGINT,
    p_user_id user_id
)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
AS $$
    SELECT EXISTS (
        SELECT 1
        FROM managed_resources r
        JOIN users u ON u.id = p_user_id
        WHERE r.id = p_resource_id
          AND u.status = 'ACTIVE'
          AND (
              u.role = 'ADMIN'
              OR r.created_by = p_user_id
          )
          AND r.can_write = TRUE
    );
$$;


-- ------------------------------------------------------------
-- 13. Procedure: create an assessment
-- ------------------------------------------------------------

CREATE OR REPLACE PROCEDURE create_assessment(
    p_user_id user_id,
    p_scores score_value[]
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF p_scores IS NULL OR cardinality(p_scores) = 0 THEN
        RAISE EXCEPTION 'Assessment must contain scores';
    END IF;

    INSERT INTO assessments (
        user_id,
        scores
    )
    VALUES (
        p_user_id,
        p_scores
    );
END;
$$;


-- ------------------------------------------------------------
-- 14. Sample users
-- ------------------------------------------------------------

INSERT INTO users (
    id,
    display_name,
    email,
    location,
    role,
    status,
    tags
)
VALUES
(
    101,
    'Atul Pandey',
    'atul@example.com',
    'Lucknow',
    'ADMIN',
    'ACTIVE',
    ARRAY['typescript', 'backend', 'database']
),
(
    102,
    'Riya Sharma',
    'riya@example.com',
    'Delhi',
    'DEVELOPER',
    'ACTIVE',
    ARRAY['javascript', 'typescript']
),
(
    103,
    'Aman Verma',
    'aman@example.com',
    'Pune',
    'ANALYST',
    'PENDING',
    ARRAY['analytics', 'sql']
),
(
    104,
    'Neha Singh',
    'neha@example.com',
    'Mumbai',
    'VIEWER',
    'SUSPENDED',
    ARRAY['reporting']
);


-- ------------------------------------------------------------
-- 15. Sample projects
-- ------------------------------------------------------------

INSERT INTO projects (
    name,
    status,
    owner_id,
    member_ids
)
VALUES
(
    'TypeScript Core Platform',
    'IN_PROGRESS',
    101,
    ARRAY[101, 102]
),
(
    'Data Analytics Portal',
    'PLANNED',
    101,
    ARRAY[101, 103]
);


-- ------------------------------------------------------------
-- 16. Sample intersection resources
-- ------------------------------------------------------------

INSERT INTO managed_resources (
    name,
    created_by,
    can_read,
    can_write,
    can_delete,
    metadata
)
VALUES
(
    'Project Repository',
    101,
    TRUE,
    TRUE,
    FALSE,
    '{"category":"source_code","version":1}'::jsonb
),
(
    'Analytics Dashboard',
    102,
    TRUE,
    FALSE,
    FALSE,
    '{"category":"analytics","version":2}'::jsonb
);


-- ------------------------------------------------------------
-- 17. Sample discriminated union results
-- ------------------------------------------------------------

INSERT INTO api_results (
    result_kind,
    success_data
)
VALUES (
    'SUCCESS',
    '{"user_id":101,"status":"active"}'::jsonb
);

INSERT INTO api_results (
    result_kind,
    error_message,
    error_code
)
VALUES (
    'ERROR',
    'Permission denied',
    403
);


-- ------------------------------------------------------------
-- 18. Sample assessments
-- ------------------------------------------------------------

INSERT INTO assessments (
    user_id,
    scores
)
VALUES
(
    101,
    ARRAY[85, 92, 67, 48, 92]::score_value[]
),
(
    102,
    ARRAY[75, 81, 90]::score_value[]
);


-- ------------------------------------------------------------
-- 19. View: user and project reporting
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW user_project_summary AS
SELECT
    u.id,
    u.display_name,
    u.role,
    u.status,
    COUNT(p.id) AS project_count,
    COALESCE(
        array_agg(p.name)
            FILTER (WHERE p.id IS NOT NULL),
        ARRAY[]::TEXT[]
    ) AS projects
FROM users u
LEFT JOIN projects p
    ON p.owner_id = u.id
GROUP BY
    u.id,
    u.display_name,
    u.role,
    u.status;


-- ------------------------------------------------------------
-- 20. View: assessment statistics
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW assessment_statistics AS
SELECT
    u.id AS user_id,
    u.display_name,
    COUNT(a.id) AS assessment_count,
    ROUND(AVG(a.average_score), 2) AS overall_average,
    MAX(a.average_score) AS highest_average
FROM users u
LEFT JOIN assessments a
    ON a.user_id = u.id
GROUP BY u.id, u.display_name;


-- ------------------------------------------------------------
-- 21. Retrieval queries
-- ------------------------------------------------------------

SELECT *
FROM get_user_profile(101);

SELECT *
FROM user_project_summary
ORDER BY id;

SELECT *
FROM assessment_statistics
ORDER BY user_id;


-- ------------------------------------------------------------
-- 22. Array operations
-- ------------------------------------------------------------

SELECT
    id,
    display_name,
    tags,
    'typescript' = ANY(tags) AS uses_typescript
FROM users;

SELECT
    id,
    name,
    member_ids,
    cardinality(member_ids) AS member_count
FROM projects;


-- ------------------------------------------------------------
-- 23. JSON object operations
-- ------------------------------------------------------------

SELECT
    id,
    name,
    metadata ->> 'category' AS category,
    metadata ->> 'version' AS version
FROM managed_resources;


-- ------------------------------------------------------------
-- 24. Tuple operations
-- ------------------------------------------------------------

SELECT make_coordinate(
    26.8467,
    80.9462
) AS lucknow_coordinates;


-- ------------------------------------------------------------
-- 25. Union operations
-- ------------------------------------------------------------

SELECT
    id,
    result_kind,
    CASE
        WHEN result_kind = 'SUCCESS'
            THEN success_data::TEXT
        WHEN result_kind = 'ERROR'
            THEN error_message
    END AS result_description
FROM api_results;


-- ------------------------------------------------------------
-- 26. Permission evaluation
-- ------------------------------------------------------------

SELECT
    id,
    name,
    created_by,
    can_manage_resource(id, 101) AS admin_can_manage
FROM managed_resources;


-- ------------------------------------------------------------
-- 27. CTE: user score ranking
-- ------------------------------------------------------------

WITH ranked_users AS (
    SELECT
        u.id,
        u.display_name,
        AVG(a.average_score) AS average_score
    FROM users u
    JOIN assessments a
        ON a.user_id = u.id
    GROUP BY u.id, u.display_name
),
ranked AS (
    SELECT
        *,
        RANK() OVER (
            ORDER BY average_score DESC
        ) AS score_rank
    FROM ranked_users
)
SELECT *
FROM ranked
ORDER BY score_rank;


-- ------------------------------------------------------------
-- 28. Validation and failure cases
-- ------------------------------------------------------------

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM users
        WHERE email !~ '^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$'
    ) THEN
        RAISE EXCEPTION 'Invalid user email detected';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM users
        WHERE status = 'ACTIVE'
          AND role = 'VIEWER'
          AND 'administrator' = ANY(tags)
    ) THEN
        RAISE EXCEPTION 'Invalid role-tag combination';
    END IF;

    RAISE NOTICE 'Validation completed';
END;
$$;


-- ------------------------------------------------------------
-- 29. Transactional workflow
-- ------------------------------------------------------------

SAVEPOINT before_project;

INSERT INTO projects (
    name,
    status,
    owner_id,
    member_ids
)
VALUES (
    'Advanced Type Modeling',
    'IN_PROGRESS',
    101,
    ARRAY[101, 102]
);

-- Verify the inserted project.
SELECT *
FROM projects
WHERE name = 'Advanced Type Modeling';

-- Keep the valid insertion.
RELEASE SAVEPOINT before_project;


-- ------------------------------------------------------------
-- 30. Performance and operational reporting
-- ------------------------------------------------------------

EXPLAIN
SELECT *
FROM users
WHERE role = 'ADMIN'
  AND status = 'ACTIVE';

EXPLAIN
SELECT *
FROM users
WHERE tags @> ARRAY['typescript'];


COMMIT;
