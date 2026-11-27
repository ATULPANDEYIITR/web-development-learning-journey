-- =========================================================
-- NEXT.JS FULL-STACK ARCHITECTURE
-- PostgreSQL persistence and application workflow
--
-- Concepts:
--   1. Route handler persistence
--   2. Server action persistence
--   3. Authentication and authorization
--   4. Environment configuration registry
--   5. Input validation
--   6. Transaction management
--   7. Audit logging
--   8. Cache invalidation events
--   9. Application-level reporting
--
-- Compatible with PostgreSQL 15+
--
-- Execute:
--   psql -U postgres -d postgres -f nextjs_fullstack.sql
-- =========================================================


-- =========================================================
-- 1. SCHEMA
-- =========================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS nextjs_app;

SET search_path TO nextjs_app, public;


-- =========================================================
-- 2. ENUM TYPES
-- =========================================================

CREATE TYPE application_environment AS ENUM (
    'development',
    'test',
    'production'
);

CREATE TYPE user_role AS ENUM (
    'user',
    'admin'
);

CREATE TYPE action_type AS ENUM (
    'ROUTE_HANDLER',
    'SERVER_ACTION',
    'MIDDLEWARE',
    'SYSTEM'
);

CREATE TYPE request_state AS ENUM (
    'RECEIVED',
    'AUTHORIZED',
    'REJECTED',
    'COMPLETED',
    'FAILED'
);


-- =========================================================
-- 3. ENVIRONMENT CONFIGURATION
-- =========================================================

CREATE TABLE environment_config (
    config_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    environment application_environment NOT NULL,

    variable_name VARCHAR(150) NOT NULL,

    is_public BOOLEAN NOT NULL DEFAULT FALSE,

    is_secret BOOLEAN NOT NULL DEFAULT FALSE,

    value_present BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT unique_environment_variable
        UNIQUE(environment, variable_name),

    CONSTRAINT valid_environment_variable_name
        CHECK (
            variable_name ~ '^[A-Z][A-Z0-9_]*$'
        ),

    CONSTRAINT public_secret_separation
        CHECK (NOT (is_public AND is_secret))
);

CREATE INDEX idx_environment_config_environment
ON environment_config(environment);


-- =========================================================
-- 4. USERS
-- =========================================================

CREATE TABLE app_users (
    user_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    username VARCHAR(80) NOT NULL UNIQUE,

    email VARCHAR(255) NOT NULL UNIQUE,

    password_hash TEXT NOT NULL,

    role user_role NOT NULL DEFAULT 'user',

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_username
        CHECK (username ~ '^[A-Za-z0-9_]{3,80}$'),

    CONSTRAINT valid_email
        CHECK (POSITION('@' IN email) > 1)
);

CREATE INDEX idx_app_users_role_active
ON app_users(role, is_active);


-- =========================================================
-- 5. APPLICATION SESSIONS
-- =========================================================

CREATE TABLE app_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id BIGINT NOT NULL
        REFERENCES app_users(user_id)
        ON DELETE CASCADE,

    token_hash TEXT NOT NULL UNIQUE,

    expires_at TIMESTAMPTZ NOT NULL,

    revoked_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_session_expiration
        CHECK (expires_at > created_at)
);

CREATE INDEX idx_sessions_active_user
ON app_sessions(user_id, expires_at)
WHERE revoked_at IS NULL;


-- =========================================================
-- 6. APPLICATION TASKS
-- =========================================================

CREATE TABLE tasks (
    task_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    user_id BIGINT NOT NULL
        REFERENCES app_users(user_id)
        ON DELETE CASCADE,

    title VARCHAR(120) NOT NULL,

    completed BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_task_title
        CHECK (
            LENGTH(BTRIM(title)) BETWEEN 1 AND 120
        )
);

CREATE INDEX idx_tasks_user_created
ON tasks(user_id, created_at DESC);

CREATE INDEX idx_tasks_pending
ON tasks(user_id, created_at DESC)
WHERE completed = FALSE;


-- =========================================================
-- 7. REQUEST EXECUTION LOG
-- =========================================================

CREATE TABLE request_logs (
    request_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id BIGINT
        REFERENCES app_users(user_id)
        ON DELETE SET NULL,

    method VARCHAR(10) NOT NULL,

    request_path TEXT NOT NULL,

    action action_type NOT NULL,

    state request_state NOT NULL DEFAULT 'RECEIVED',

    http_status SMALLINT,

    duration_ms NUMERIC(12, 3),

    error_code VARCHAR(80),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_http_method
        CHECK (
            method IN (
                'GET', 'POST', 'PUT',
                'PATCH', 'DELETE', 'OPTIONS', 'HEAD'
            )
        ),

    CONSTRAINT valid_http_status
        CHECK (
            http_status IS NULL OR
            http_status BETWEEN 100 AND 599
        ),

    CONSTRAINT valid_request_duration
        CHECK (
            duration_ms IS NULL OR duration_ms >= 0
        )
);

CREATE INDEX idx_request_logs_created
ON request_logs(created_at DESC);

CREATE INDEX idx_request_logs_state
ON request_logs(state, created_at DESC);

CREATE INDEX idx_request_logs_user
ON request_logs(user_id, created_at DESC);


-- =========================================================
-- 8. CACHE INVALIDATION EVENTS
-- =========================================================

CREATE TABLE cache_invalidation_events (
    event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    cache_key VARCHAR(255) NOT NULL,

    reason VARCHAR(100) NOT NULL,

    user_id BIGINT
        REFERENCES app_users(user_id)
        ON DELETE SET NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_cache_events_created
ON cache_invalidation_events(created_at DESC);


-- =========================================================
-- 9. AUDIT LOG
-- =========================================================

CREATE TABLE audit_logs (
    audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    user_id BIGINT
        REFERENCES app_users(user_id)
        ON DELETE SET NULL,

    action VARCHAR(100) NOT NULL,

    resource_type VARCHAR(100) NOT NULL,

    resource_id BIGINT,

    source action_type NOT NULL,

    details JSONB NOT NULL DEFAULT '{}'::JSONB,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_user_created
ON audit_logs(user_id, created_at DESC);

CREATE INDEX idx_audit_resource
ON audit_logs(resource_type, resource_id);

CREATE INDEX idx_audit_details
ON audit_logs USING GIN(details);


-- =========================================================
-- 10. CONFIGURATION VALIDATION
-- =========================================================

CREATE OR REPLACE FUNCTION validate_environment_config(
    p_environment application_environment
)
RETURNS BOOLEAN
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    missing_count INTEGER;
BEGIN
    SELECT COUNT(*)
    INTO missing_count
    FROM (
        SELECT required.variable_name
        FROM (
            VALUES
                ('DATABASE_URL'),
                ('SESSION_SECRET'),
                ('APP_ENV')
        ) AS required(variable_name)

        LEFT JOIN environment_config config
            ON config.variable_name = required.variable_name
            AND config.environment = p_environment
            AND config.value_present = TRUE

        WHERE config.config_id IS NULL
    ) missing;

    RETURN missing_count = 0;
END;
$$;


-- =========================================================
-- 11. TIMESTAMP UPDATE TRIGGER
-- =========================================================

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

CREATE TRIGGER tasks_updated_at
BEFORE UPDATE ON tasks
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER environment_updated_at
BEFORE UPDATE ON environment_config
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();


-- =========================================================
-- 12. TASK CREATION FUNCTION
-- =========================================================

CREATE OR REPLACE FUNCTION create_task(
    p_user_id BIGINT,
    p_title TEXT,
    p_source action_type DEFAULT 'ROUTE_HANDLER'
)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    new_task_id BIGINT;
    normalized_title TEXT;
BEGIN
    normalized_title := BTRIM(p_title);

    IF normalized_title IS NULL
       OR LENGTH(normalized_title) = 0
       OR LENGTH(normalized_title) > 120 THEN

        RAISE EXCEPTION
            'Invalid task title'
            USING ERRCODE = '22023';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM app_users
        WHERE user_id = p_user_id
          AND is_active = TRUE
    ) THEN
        RAISE EXCEPTION
            'User is not active or does not exist'
            USING ERRCODE = '42501';
    END IF;

    INSERT INTO tasks (
        user_id,
        title
    )
    VALUES (
        p_user_id,
        normalized_title
    )
    RETURNING task_id INTO new_task_id;

    INSERT INTO audit_logs (
        user_id,
        action,
        resource_type,
        resource_id,
        source,
        details
    )
    VALUES (
        p_user_id,
        'CREATE',
        'TASK',
        new_task_id,
        p_source,
        jsonb_build_object(
            'title_length',
            LENGTH(normalized_title)
        )
    );

    INSERT INTO cache_invalidation_events (
        cache_key,
        reason,
        user_id
    )
    VALUES (
        'tasks:' || p_user_id,
        'TASK_CREATED',
        p_user_id
    );

    RETURN new_task_id;
END;
$$;


-- =========================================================
-- 13. TASK UPDATE FUNCTION
-- =========================================================

CREATE OR REPLACE FUNCTION update_task_status(
    p_task_id BIGINT,
    p_user_id BIGINT,
    p_completed BOOLEAN
)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
DECLARE
    affected INTEGER;
BEGIN
    UPDATE tasks
    SET completed = p_completed
    WHERE task_id = p_task_id
      AND user_id = p_user_id;

    GET DIAGNOSTICS affected = ROW_COUNT;

    IF affected = 0 THEN
        IF EXISTS (
            SELECT 1
            FROM tasks
            WHERE task_id = p_task_id
        ) THEN
            RAISE EXCEPTION
                'Task ownership violation'
                USING ERRCODE = '42501';
        END IF;

        RAISE EXCEPTION
            'Task not found'
            USING ERRCODE = 'P0002';
    END IF;

    INSERT INTO audit_logs (
        user_id,
        action,
        resource_type,
        resource_id,
        source,
        details
    )
    VALUES (
        p_user_id,
        'UPDATE',
        'TASK',
        p_task_id,
        'SERVER_ACTION',
        jsonb_build_object(
            'completed',
            p_completed
        )
    );

    INSERT INTO cache_invalidation_events (
        cache_key,
        reason,
        user_id
    )
    VALUES (
        'tasks:' || p_user_id,
        'TASK_UPDATED',
        p_user_id
    );

    RETURN TRUE;
END;
$$;


-- =========================================================
-- 14. DELETE FUNCTION
-- =========================================================

CREATE OR REPLACE FUNCTION delete_task(
    p_task_id BIGINT,
    p_user_id BIGINT
)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
DECLARE
    affected INTEGER;
BEGIN
    DELETE FROM tasks
    WHERE task_id = p_task_id
      AND user_id = p_user_id;

    GET DIAGNOSTICS affected = ROW_COUNT;

    IF affected = 0 THEN
        RAISE EXCEPTION
            'Task not found or ownership violation'
            USING ERRCODE = 'P0002';
    END IF;

    INSERT INTO audit_logs (
        user_id,
        action,
        resource_type,
        resource_id,
        source
    )
    VALUES (
        p_user_id,
        'DELETE',
        'TASK',
        p_task_id,
        'ROUTE_HANDLER'
    );

    INSERT INTO cache_invalidation_events (
        cache_key,
        reason,
        user_id
    )
    VALUES (
        'tasks:' || p_user_id,
        'TASK_DELETED',
        p_user_id
    );

    RETURN TRUE;
END;
$$;


-- =========================================================
-- 15. REQUEST STATE TRANSITION VALIDATION
-- =========================================================

CREATE OR REPLACE FUNCTION validate_request_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'UPDATE' THEN

        IF OLD.state IN ('COMPLETED', 'REJECTED', 'FAILED') THEN
            RAISE EXCEPTION
                'Terminal request states cannot be modified';
        END IF;

        IF OLD.state = 'RECEIVED'
           AND NEW.state NOT IN (
               'AUTHORIZED',
               'REJECTED',
               'FAILED'
           ) THEN

            RAISE EXCEPTION
                'Invalid RECEIVED state transition';
        END IF;

        IF OLD.state = 'AUTHORIZED'
           AND NEW.state NOT IN (
               'COMPLETED',
               'FAILED'
           ) THEN

            RAISE EXCEPTION
                'Invalid AUTHORIZED state transition';
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER request_state_transition
BEFORE UPDATE OF state ON request_logs
FOR EACH ROW
EXECUTE FUNCTION validate_request_transition();


-- =========================================================
-- 16. REQUEST PROCESSING PROCEDURE
-- =========================================================

CREATE OR REPLACE PROCEDURE process_request(
    p_request_id UUID,
    p_user_id BIGINT,
    p_method VARCHAR(10),
    p_path TEXT,
    p_action action_type,
    p_http_status SMALLINT,
    p_duration_ms NUMERIC
)
LANGUAGE plpgsql
AS $$
DECLARE
    final_state request_state;
BEGIN
    IF p_http_status BETWEEN 200 AND 299 THEN
        final_state := 'COMPLETED';
    ELSIF p_http_status BETWEEN 400 AND 499 THEN
        final_state := 'REJECTED';
    ELSE
        final_state := 'FAILED';
    END IF;

    INSERT INTO request_logs (
        request_id,
        user_id,
        method,
        request_path,
        action,
        state,
        http_status,
        duration_ms
    )
    VALUES (
        p_request_id,
        p_user_id,
        p_method,
        p_path,
        p_action,
        'RECEIVED',
        NULL,
        p_duration_ms
    );

    IF final_state = 'COMPLETED' THEN
        UPDATE request_logs
        SET state = 'AUTHORIZED'
        WHERE request_id = p_request_id;
    END IF;

    UPDATE request_logs
    SET state = final_state,
        http_status = p_http_status
    WHERE request_id = p_request_id;

END;
$$;


-- =========================================================
-- 17. REPORTING VIEWS
-- =========================================================

CREATE OR REPLACE VIEW user_task_statistics AS
SELECT
    u.user_id,
    u.username,
    u.role,
    COUNT(t.task_id) AS total_tasks,
    COUNT(t.task_id) FILTER (
        WHERE t.completed = TRUE
    ) AS completed_tasks,
    COUNT(t.task_id) FILTER (
        WHERE t.completed = FALSE
    ) AS pending_tasks
FROM app_users u
LEFT JOIN tasks t
    ON t.user_id = u.user_id
GROUP BY
    u.user_id,
    u.username,
    u.role;


CREATE OR REPLACE VIEW request_performance_report AS
SELECT
    action,
    state,
    COUNT(*) AS request_count,
    ROUND(AVG(duration_ms), 3) AS average_duration_ms,
    ROUND(MAX(duration_ms), 3) AS maximum_duration_ms,
    COUNT(*) FILTER (
        WHERE http_status >= 500
    ) AS server_errors
FROM request_logs
GROUP BY action, state;


CREATE OR REPLACE VIEW cache_invalidation_report AS
SELECT
    reason,
    COUNT(*) AS event_count,
    MAX(created_at) AS last_event
FROM cache_invalidation_events
GROUP BY reason;


-- =========================================================
-- 18. SAMPLE ENVIRONMENT CONFIGURATION
-- =========================================================

INSERT INTO environment_config (
    environment,
    variable_name,
    is_public,
    is_secret,
    value_present
)
VALUES
(
    'development',
    'DATABASE_URL',
    FALSE,
    TRUE,
    TRUE
),
(
    'development',
    'SESSION_SECRET',
    FALSE,
    TRUE,
    TRUE
),
(
    'development',
    'APP_ENV',
    FALSE,
    FALSE,
    TRUE
),
(
    'development',
    'NEXT_PUBLIC_APP_NAME',
    TRUE,
    FALSE,
    TRUE
),
(
    'production',
    'DATABASE_URL',
    FALSE,
    TRUE,
    TRUE
),
(
    'production',
    'SESSION_SECRET',
    FALSE,
    TRUE,
    TRUE
),
(
    'production',
    'APP_ENV',
    FALSE,
    FALSE,
    TRUE
)
ON CONFLICT (environment, variable_name)
DO NOTHING;


-- =========================================================
-- 19. SAMPLE USERS
-- Password hashes are demonstration-only values.
-- Production authentication must use a proper password
-- hashing algorithm and a secure credential provider.
-- =========================================================

INSERT INTO app_users (
    username,
    email,
    password_hash,
    role
)
VALUES
(
    'alice',
    'alice@example.com',
    '$2b$12$demonstration_hash_alice',
    'user'
),
(
    'bob',
    'bob@example.com',
    '$2b$12$demonstration_hash_bob',
    'user'
),
(
    'admin',
    'admin@example.com',
    '$2b$12$demonstration_hash_admin',
    'admin'
)
ON CONFLICT (username)
DO NOTHING;


-- =========================================================
-- 20. SAMPLE TASK CREATION
-- =========================================================

DO $$
DECLARE
    alice_id BIGINT;
    bob_id BIGINT;
BEGIN
    SELECT user_id INTO alice_id
    FROM app_users
    WHERE username = 'alice';

    SELECT user_id INTO bob_id
    FROM app_users
    WHERE username = 'bob';

    IF NOT EXISTS (
        SELECT 1 FROM tasks
        WHERE user_id = alice_id
          AND title = 'Implement route handlers'
    ) THEN
        PERFORM create_task(
            alice_id,
            'Implement route handlers',
            'ROUTE_HANDLER'
        );
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM tasks
        WHERE user_id = alice_id
          AND title = 'Implement server actions'
    ) THEN
        PERFORM create_task(
            alice_id,
            'Implement server actions',
            'SERVER_ACTION'
        );
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM tasks
        WHERE user_id = bob_id
          AND title = 'Configure middleware'
    ) THEN
        PERFORM create_task(
            bob_id,
            'Configure middleware',
            'SERVER_ACTION'
        );
    END IF;
END;
$$;


-- =========================================================
-- 21. SAMPLE TASK UPDATE
-- =========================================================

DO $$
DECLARE
    target_task BIGINT;
    alice_id BIGINT;
BEGIN
    SELECT user_id INTO alice_id
    FROM app_users
    WHERE username = 'alice';

    SELECT task_id INTO target_task
    FROM tasks
    WHERE user_id = alice_id
      AND title = 'Implement route handlers'
    ORDER BY task_id
    LIMIT 1;

    IF target_task IS NOT NULL THEN
        PERFORM update_task_status(
            target_task,
            alice_id,
            TRUE
        );
    END IF;
END;
$$;


-- =========================================================
-- 22. REQUEST LOG SAMPLE DATA
-- =========================================================

CALL process_request(
    gen_random_uuid(),
    (SELECT user_id FROM app_users WHERE username = 'alice'),
    'POST',
    '/api/tasks',
    'ROUTE_HANDLER',
    201,
    12.450
);

CALL process_request(
    gen_random_uuid(),
    NULL,
    'GET',
    '/api/tasks',
    'MIDDLEWARE',
    401,
    1.230
);

CALL process_request(
    gen_random_uuid(),
    (SELECT user_id FROM app_users WHERE username = 'alice'),
    'POST',
    '/api/tasks',
    'SERVER_ACTION',
    400,
    3.500
);


-- =========================================================
-- 23. ELIGIBILITY AND CONFIGURATION QUERIES
-- =========================================================

-- Determine whether an environment has all required settings.

SELECT
    environment,
    validate_environment_config(environment)
        AS configuration_valid
FROM (
    SELECT DISTINCT environment
    FROM environment_config
) environments
ORDER BY environment;


-- Display only public environment variable names.
-- Actual secret values are not stored in this registry.

SELECT
    environment,
    variable_name
FROM environment_config
WHERE is_public = TRUE
  AND value_present = TRUE
ORDER BY environment, variable_name;


-- Detect missing environment variables.

WITH required_variables(variable_name) AS (
    VALUES
        ('DATABASE_URL'),
        ('SESSION_SECRET'),
        ('APP_ENV')
)
SELECT
    environments.environment,
    required_variables.variable_name AS missing_variable
FROM (
    SELECT DISTINCT environment
    FROM environment_config
) environments
CROSS JOIN required_variables
LEFT JOIN environment_config config
    ON config.environment = environments.environment
   AND config.variable_name = required_variables.variable_name
   AND config.value_present = TRUE
WHERE config.config_id IS NULL
ORDER BY environments.environment;


-- =========================================================
-- 24. TASK RETRIEVAL
-- =========================================================

SELECT
    task_id,
    user_id,
    title,
    completed,
    created_at
FROM tasks
WHERE user_id = (
    SELECT user_id
    FROM app_users
    WHERE username = 'alice'
)
ORDER BY created_at DESC;


-- =========================================================
-- 25. TASK AGGREGATION
-- =========================================================

SELECT *
FROM user_task_statistics
ORDER BY user_id;


-- =========================================================
-- 26. REQUEST PERFORMANCE EVALUATION
-- =========================================================

SELECT
    action,
    request_count,
    average_duration_ms,
    maximum_duration_ms,
    server_errors
FROM request_performance_report
ORDER BY request_count DESC;


-- =========================================================
-- 27. FAILURE ANALYSIS
-- =========================================================

SELECT
    state,
    http_status,
    COUNT(*) AS occurrences
FROM request_logs
GROUP BY state, http_status
ORDER BY occurrences DESC;


-- =========================================================
-- 28. AUDIT REPORT
-- =========================================================

SELECT
    audit_id,
    user_id,
    action,
    resource_type,
    resource_id,
    source,
    created_at
FROM audit_logs
ORDER BY created_at DESC
LIMIT 100;


-- =========================================================
-- 29. CACHE INVALIDATION REPORT
-- =========================================================

SELECT *
FROM cache_invalidation_report
ORDER BY event_count DESC;


-- =========================================================
-- 30. SERVER ACTION WORKFLOW
-- =========================================================

-- The transaction ensures that the task, audit entry,
-- and invalidation event either all persist or all roll back.

DO $$
DECLARE
    alice_id BIGINT;
    created_id BIGINT;
BEGIN
    SELECT user_id INTO alice_id
    FROM app_users
    WHERE username = 'alice';

    created_id := create_task(
        alice_id,
        'Validate production environment variables',
        'SERVER_ACTION'
    );

    RAISE NOTICE 'Created task: %', created_id;
END;
$$;


-- =========================================================
-- 31. OWNERSHIP VALIDATION
-- =========================================================

-- The following query identifies tasks whose ownership
-- references are inconsistent. The foreign key prevents
-- missing user records.

SELECT
    t.task_id,
    t.user_id,
    t.title
FROM tasks t
LEFT JOIN app_users u
    ON u.user_id = t.user_id
WHERE u.user_id IS NULL;


-- =========================================================
-- 32. TRANSACTION FAILURE HANDLING
-- =========================================================

-- This transaction intentionally tests invalid input.
-- The exception block rolls back the failed operation.

DO $$
DECLARE
    alice_id BIGINT;
BEGIN
    SELECT user_id INTO alice_id
    FROM app_users
    WHERE username = 'alice';

    BEGIN
        PERFORM create_task(
            alice_id,
            '',
            'ROUTE_HANDLER'
        );

    EXCEPTION
        WHEN SQLSTATE '22023' THEN
            RAISE NOTICE
                'Validation failure handled: %',
                SQLERRM;
    END;
END;
$$;


-- =========================================================
-- 33. EXPIRED SESSION IDENTIFICATION
-- =========================================================

SELECT
    session_id,
    user_id,
    expires_at
FROM app_sessions
WHERE expires_at <= NOW()
  AND revoked_at IS NULL
ORDER BY expires_at;


-- =========================================================
-- 34. EXPIRED SESSION CLEANUP
-- =========================================================

DELETE FROM app_sessions
WHERE expires_at <= NOW()
   OR revoked_at IS NOT NULL;


-- =========================================================
-- 35. DATABASE SECURITY NOTES
-- =========================================================

-- Application database credentials should have only the
-- permissions required by the application.
--
-- The following example role is intentionally created
-- conditionally for environments where the operator has
-- permission to create roles.

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_roles
        WHERE rolname = 'nextjs_app_runtime'
    ) THEN
        CREATE ROLE nextjs_app_runtime
        NOLOGIN;
    END IF;
END;
$$;

GRANT USAGE ON SCHEMA nextjs_app
TO nextjs_app_runtime;

GRANT SELECT, INSERT, UPDATE, DELETE
ON app_users, app_sessions, tasks, request_logs,
   cache_invalidation_events, audit_logs
TO nextjs_app_runtime;

GRANT SELECT
ON environment_config
TO nextjs_app_runtime;

GRANT SELECT
ON user_task_statistics,
   request_performance_report,
   cache_invalidation_report
TO nextjs_app_runtime;

GRANT USAGE, SELECT
ON ALL SEQUENCES IN SCHEMA nextjs_app
TO nextjs_app_runtime;

GRANT EXECUTE
ON FUNCTION validate_environment_config(application_environment),
            create_task(BIGINT, TEXT, action_type),
            update_task_status(BIGINT, BIGINT, BOOLEAN),
            delete_task(BIGINT, BIGINT)
TO nextjs_app_runtime;


-- =========================================================
-- 36. COMPLETION
-- =========================================================

COMMIT;

RESET search_path;

SELECT
    'Next.js full-stack database initialized'
        AS initialization_status,
    CURRENT_TIMESTAMP AS executed_at;
