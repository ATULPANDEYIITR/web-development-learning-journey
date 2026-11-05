/*
    NODE.JS FUNDAMENTALS
    PostgreSQL Runtime and Deployment Configuration Registry

    Models:
    - Node.js application registrations
    - Runtime versions
    - Module dependencies
    - Environment configurations
    - Filesystem resource metadata
    - Deployment validation
    - Runtime health checks
    - Configuration policies
    - Deployment eligibility

    PostgreSQL 15+
*/

BEGIN;

CREATE SCHEMA IF NOT EXISTS node_runtime;

SET search_path TO node_runtime, public;

-- =========================================================
-- ENUM TYPES
-- =========================================================

CREATE TYPE environment_mode AS ENUM (
    'development',
    'test',
    'production'
);

CREATE TYPE module_type AS ENUM (
    'builtin',
    'commonjs',
    'es_module',
    'third_party'
);

CREATE TYPE deployment_status AS ENUM (
    'registered',
    'validating',
    'ready',
    'blocked',
    'deployed',
    'failed'
);

CREATE TYPE check_status AS ENUM (
    'passed',
    'warning',
    'failed'
);

CREATE TYPE filesystem_resource_type AS ENUM (
    'file',
    'directory',
    'configuration',
    'log'
);

-- =========================================================
-- APPLICATION REGISTRY
-- =========================================================

CREATE TABLE applications (
    application_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    application_name VARCHAR(150) NOT NULL UNIQUE,

    description TEXT NOT NULL,

    entry_point VARCHAR(255) NOT NULL,

    minimum_node_major INTEGER NOT NULL,

    minimum_node_minor INTEGER NOT NULL DEFAULT 0,

    minimum_node_patch INTEGER NOT NULL DEFAULT 0,

    mode environment_mode NOT NULL DEFAULT 'development',

    status deployment_status NOT NULL DEFAULT 'registered',

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_application_name
        CHECK (application_name ~ '^[a-zA-Z0-9_-]+$'),

    CONSTRAINT valid_entry_point
        CHECK (
            entry_point NOT LIKE '/%'
            AND entry_point NOT LIKE '%..%'
        ),

    CONSTRAINT valid_runtime_version
        CHECK (
            minimum_node_major >= 18
            AND minimum_node_minor >= 0
            AND minimum_node_patch >= 0
        )
);

-- =========================================================
-- NODE.JS RUNTIME INVENTORY
-- =========================================================

CREATE TABLE runtime_instances (
    runtime_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    application_id BIGINT NOT NULL
        REFERENCES applications(application_id)
        ON DELETE CASCADE,

    node_major INTEGER NOT NULL,

    node_minor INTEGER NOT NULL,

    node_patch INTEGER NOT NULL,

    platform VARCHAR(40) NOT NULL,

    architecture VARCHAR(40) NOT NULL,

    process_id BIGINT,

    executable_path TEXT NOT NULL,

    working_directory TEXT NOT NULL,

    memory_limit_mb INTEGER,

    detected_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_runtime_components
        CHECK (
            node_major >= 0
            AND node_minor >= 0
            AND node_patch >= 0
        ),

    CONSTRAINT valid_process_id
        CHECK (process_id IS NULL OR process_id > 0),

    CONSTRAINT valid_memory_limit
        CHECK (memory_limit_mb IS NULL OR memory_limit_mb > 0)
);

CREATE INDEX idx_runtime_application
ON runtime_instances(application_id, detected_at DESC);

-- =========================================================
-- MODULE REGISTRY
-- =========================================================

CREATE TABLE modules (
    module_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    module_name VARCHAR(150) NOT NULL,

    module_version VARCHAR(50) NOT NULL,

    module_category module_type NOT NULL,

    description TEXT,

    CONSTRAINT unique_module_version
        UNIQUE(module_name, module_version)
);

-- Node.js built-in modules are registered separately from
-- npm packages because they do not require installation.

INSERT INTO modules (
    module_name,
    module_version,
    module_category,
    description
)
VALUES
    ('fs', 'builtin', 'builtin', 'Filesystem operations'),
    ('path', 'builtin', 'builtin', 'Path manipulation'),
    ('os', 'builtin', 'builtin', 'Operating system information'),
    ('http', 'builtin', 'builtin', 'HTTP server functionality'),
    ('https', 'builtin', 'builtin', 'HTTPS functionality'),
    ('events', 'builtin', 'builtin', 'Event-driven programming'),
    ('crypto', 'builtin', 'builtin', 'Cryptographic operations'),
    ('util', 'builtin', 'builtin', 'Utility functions'),
    ('stream', 'builtin', 'builtin', 'Streaming data'),
    ('buffer', 'builtin', 'builtin', 'Binary data handling'),
    ('express', '5.1.0', 'third_party', 'Web application framework'),
    ('pg', '8.16.0', 'third_party', 'PostgreSQL client'),
    ('inventory-core', '1.0.0', 'commonjs', 'Inventory business module'),
    ('inventory-api', '1.0.0', 'es_module', 'Inventory API entry module');

CREATE TABLE application_modules (
    application_id BIGINT NOT NULL
        REFERENCES applications(application_id)
        ON DELETE CASCADE,

    module_id BIGINT NOT NULL
        REFERENCES modules(module_id),

    is_direct_dependency BOOLEAN NOT NULL DEFAULT TRUE,

    is_optional BOOLEAN NOT NULL DEFAULT FALSE,

    PRIMARY KEY (application_id, module_id)
);

CREATE TABLE module_dependencies (
    parent_module_id BIGINT NOT NULL
        REFERENCES modules(module_id)
        ON DELETE CASCADE,

    dependency_module_id BIGINT NOT NULL
        REFERENCES modules(module_id),

    PRIMARY KEY (parent_module_id, dependency_module_id),

    CONSTRAINT no_direct_self_dependency
        CHECK (parent_module_id <> dependency_module_id)
);

-- =========================================================
-- ENVIRONMENT VARIABLE DEFINITIONS
-- =========================================================

CREATE TABLE environment_variable_definitions (
    definition_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    application_id BIGINT NOT NULL
        REFERENCES applications(application_id)
        ON DELETE CASCADE,

    variable_name VARCHAR(150) NOT NULL,

    is_required BOOLEAN NOT NULL DEFAULT FALSE,

    is_secret BOOLEAN NOT NULL DEFAULT FALSE,

    expected_type VARCHAR(30) NOT NULL DEFAULT 'string',

    description TEXT,

    CONSTRAINT unique_application_variable
        UNIQUE(application_id, variable_name),

    CONSTRAINT valid_variable_name
        CHECK (variable_name ~ '^[A-Z][A-Z0-9_]*$'),

    CONSTRAINT valid_variable_type
        CHECK (
            expected_type IN (
                'string',
                'integer',
                'boolean',
                'url'
            )
        )
);

-- Store configuration metadata separately from secret values.
-- Production secret values should be held in a dedicated
-- secrets manager rather than ordinary database columns.

CREATE TABLE environment_configurations (
    configuration_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    definition_id BIGINT NOT NULL
        REFERENCES environment_variable_definitions(definition_id)
        ON DELETE CASCADE,

    mode environment_mode NOT NULL,

    configured BOOLEAN NOT NULL DEFAULT FALSE,

    non_secret_value TEXT,

    configured_at TIMESTAMPTZ,

    CONSTRAINT unique_environment_configuration
        UNIQUE(definition_id, mode),

    CONSTRAINT secret_value_protection
        CHECK (
            non_secret_value IS NULL
            OR non_secret_value NOT LIKE 'password=%'
        )
);

-- =========================================================
-- FILESYSTEM RESOURCE INVENTORY
-- =========================================================

CREATE TABLE filesystem_resources (
    resource_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    application_id BIGINT NOT NULL
        REFERENCES applications(application_id)
        ON DELETE CASCADE,

    relative_path TEXT NOT NULL,

    resource_type filesystem_resource_type NOT NULL,

    file_size_bytes BIGINT NOT NULL DEFAULT 0,

    readable BOOLEAN NOT NULL DEFAULT TRUE,

    writable BOOLEAN NOT NULL DEFAULT FALSE,

    last_modified TIMESTAMPTZ,

    CONSTRAINT unique_application_path
        UNIQUE(application_id, relative_path),

    CONSTRAINT valid_relative_path
        CHECK (
            relative_path <> ''
            AND relative_path NOT LIKE '/%'
            AND relative_path NOT LIKE '../%'
            AND relative_path NOT LIKE '%/../%'
        ),

    CONSTRAINT valid_file_size
        CHECK (file_size_bytes >= 0)
);

CREATE INDEX idx_filesystem_application_type
ON filesystem_resources(application_id, resource_type);

-- =========================================================
-- DEPLOYMENT RECORDS
-- =========================================================

CREATE TABLE deployments (
    deployment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    application_id BIGINT NOT NULL
        REFERENCES applications(application_id),

    runtime_id BIGINT
        REFERENCES runtime_instances(runtime_id),

    requested_by VARCHAR(120) NOT NULL,

    deployment_version VARCHAR(60) NOT NULL,

    status deployment_status NOT NULL DEFAULT 'registered',

    started_at TIMESTAMPTZ,

    completed_at TIMESTAMPTZ,

    CONSTRAINT valid_deployment_dates
        CHECK (
            completed_at IS NULL
            OR started_at IS NULL
            OR completed_at >= started_at
        )
);

CREATE INDEX idx_deployments_status
ON deployments(status, started_at DESC);

-- =========================================================
-- DEPLOYMENT VALIDATION RESULTS
-- =========================================================

CREATE TABLE validation_checks (
    check_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    deployment_id BIGINT NOT NULL
        REFERENCES deployments(deployment_id)
        ON DELETE CASCADE,

    check_category VARCHAR(60) NOT NULL,

    check_name VARCHAR(150) NOT NULL,

    result check_status NOT NULL,

    details TEXT NOT NULL,

    checked_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_validation_deployment_status
ON validation_checks(deployment_id, result);

-- =========================================================
-- APPLICATION REGISTRATION
-- =========================================================

INSERT INTO applications (
    application_name,
    description,
    entry_point,
    minimum_node_major,
    minimum_node_minor,
    minimum_node_patch,
    mode
)
VALUES (
    'inventory-api',
    'Inventory API using the Node.js runtime',
    'src/index.js',
    18,
    0,
    0,
    'production'
);

-- =========================================================
-- RUNTIME INSTANCE
-- =========================================================

INSERT INTO runtime_instances (
    application_id,
    node_major,
    node_minor,
    node_patch,
    platform,
    architecture,
    process_id,
    executable_path,
    working_directory,
    memory_limit_mb
)
SELECT
    application_id,
    22,
    11,
    0,
    'linux',
    'x64',
    4200,
    '/usr/bin/node',
    '/srv/inventory-api',
    512
FROM applications
WHERE application_name = 'inventory-api';

-- =========================================================
-- APPLICATION MODULE RELATIONSHIPS
-- =========================================================

INSERT INTO application_modules (
    application_id,
    module_id,
    is_direct_dependency
)
SELECT
    a.application_id,
    m.module_id,
    TRUE
FROM applications a
CROSS JOIN modules m
WHERE a.application_name = 'inventory-api'
AND m.module_name IN (
    'express',
    'pg',
    'inventory-core',
    'fs',
    'path',
    'http',
    'crypto'
);

-- Module dependency graph.

INSERT INTO module_dependencies (
    parent_module_id,
    dependency_module_id
)
SELECT parent.module_id, dependency.module_id
FROM modules parent
JOIN modules dependency
    ON (
        (parent.module_name = 'inventory-core'
            AND dependency.module_name IN ('pg', 'crypto'))
        OR
        (parent.module_name = 'inventory-api'
            AND dependency.module_name IN (
                'express',
                'inventory-core',
                'http'
            ))
    );

-- =========================================================
-- ENVIRONMENT VARIABLE POLICIES
-- =========================================================

INSERT INTO environment_variable_definitions (
    application_id,
    variable_name,
    is_required,
    is_secret,
    expected_type,
    description
)
SELECT
    application_id,
    variable_name,
    required,
    secret,
    expected_type,
    description
FROM applications
CROSS JOIN (
    VALUES
        (
            'NODE_ENV',
            TRUE,
            FALSE,
            'string',
            'Application execution mode'
        ),
        (
            'PORT',
            TRUE,
            FALSE,
            'integer',
            'HTTP server port'
        ),
        (
            'DATABASE_URL',
            TRUE,
            TRUE,
            'url',
            'PostgreSQL connection configuration'
        ),
        (
            'LOG_LEVEL',
            FALSE,
            FALSE,
            'string',
            'Application logging level'
        )
) AS configuration(
    variable_name,
    required,
    secret,
    expected_type,
    description
)
WHERE application_name = 'inventory-api';

-- The secret DATABASE_URL is marked configured, but its
-- credential-bearing value is intentionally not stored.

INSERT INTO environment_configurations (
    definition_id,
    mode,
    configured,
    non_secret_value,
    configured_at
)
SELECT
    definition_id,
    'production',
    TRUE,
    CASE
        WHEN is_secret THEN NULL
        WHEN variable_name = 'NODE_ENV' THEN 'production'
        WHEN variable_name = 'PORT' THEN '8080'
        WHEN variable_name = 'LOG_LEVEL' THEN 'info'
    END,
    CURRENT_TIMESTAMP
FROM environment_variable_definitions
WHERE application_id = (
    SELECT application_id
    FROM applications
    WHERE application_name = 'inventory-api'
);

-- =========================================================
-- FILESYSTEM INVENTORY
-- =========================================================

INSERT INTO filesystem_resources (
    application_id,
    relative_path,
    resource_type,
    file_size_bytes,
    readable,
    writable
)
SELECT
    application_id,
    relative_path,
    resource_type,
    file_size,
    TRUE,
    writable
FROM applications
CROSS JOIN (
    VALUES
        (
            'src/index.js',
            'file'::filesystem_resource_type,
            4096::BIGINT,
            FALSE
        ),
        (
            'src/services/inventory.js',
            'file'::filesystem_resource_type,
            2048::BIGINT,
            FALSE
        ),
        (
            'config/runtime.json',
            'configuration'::filesystem_resource_type,
            512::BIGINT,
            FALSE
        ),
        (
            'logs/application.log',
            'log'::filesystem_resource_type,
            0::BIGINT,
            TRUE
        )
) AS resources(
    relative_path,
    resource_type,
    file_size,
    writable
)
WHERE application_name = 'inventory-api';

-- =========================================================
-- DEPLOYMENT CREATION
-- =========================================================

INSERT INTO deployments (
    application_id,
    runtime_id,
    requested_by,
    deployment_version,
    status,
    started_at
)
SELECT
    a.application_id,
    r.runtime_id,
    'platform-admin',
    '1.0.0',
    'validating',
    CURRENT_TIMESTAMP
FROM applications a
JOIN runtime_instances r
    ON r.application_id = a.application_id
WHERE a.application_name = 'inventory-api';

-- =========================================================
-- VALIDATION FUNCTION
-- =========================================================

CREATE OR REPLACE FUNCTION validate_deployment(
    p_deployment_id BIGINT
)
RETURNS TABLE (
    category TEXT,
    check_result check_status,
    message TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_application_id BIGINT;
    v_required_major INTEGER;
    v_required_minor INTEGER;
    v_required_patch INTEGER;

    v_actual_major INTEGER;
    v_actual_minor INTEGER;
    v_actual_patch INTEGER;

    v_mode environment_mode;
BEGIN
    SELECT
        a.application_id,
        a.minimum_node_major,
        a.minimum_node_minor,
        a.minimum_node_patch,
        a.mode,
        r.node_major,
        r.node_minor,
        r.node_patch
    INTO
        v_application_id,
        v_required_major,
        v_required_minor,
        v_required_patch,
        v_mode,
        v_actual_major,
        v_actual_minor,
        v_actual_patch
    FROM deployments d
    JOIN applications a
        ON a.application_id = d.application_id
    LEFT JOIN runtime_instances r
        ON r.runtime_id = d.runtime_id
    WHERE d.deployment_id = p_deployment_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Deployment % does not exist',
            p_deployment_id;
    END IF;

    -- Runtime compatibility is lexicographical:
    -- major, then minor, then patch.

    category := 'RUNTIME';

    IF v_actual_major IS NULL THEN
        check_result := 'failed';
        message := 'No runtime instance is assigned.';

    ELSIF ROW(v_actual_major, v_actual_minor, v_actual_patch)
        >= ROW(v_required_major, v_required_minor, v_required_patch)
    THEN
        check_result := 'passed';
        message := 'Node.js runtime meets the minimum version.';

    ELSE
        check_result := 'failed';
        message := 'Node.js runtime version is insufficient.';
    END IF;

    RETURN NEXT;

    -- Required environment variables must be configured
    -- for the application's declared execution mode.

    category := 'ENVIRONMENT';

    IF EXISTS (
        SELECT 1
        FROM environment_variable_definitions definition
        LEFT JOIN environment_configurations configuration
            ON configuration.definition_id = definition.definition_id
            AND configuration.mode = v_mode
        WHERE definition.application_id = v_application_id
        AND definition.is_required
        AND (
            configuration.configuration_id IS NULL
            OR NOT configuration.configured
        )
    ) THEN
        check_result := 'failed';
        message := 'One or more required environment variables are missing.';
    ELSE
        check_result := 'passed';
        message := 'All required environment variables are configured.';
    END IF;

    RETURN NEXT;

    -- A secret is considered configured based on metadata.
    -- Its actual value is not retrieved or exposed.

    category := 'MODULES';

    IF EXISTS (
        SELECT 1
        FROM application_modules am
        JOIN modules m ON m.module_id = am.module_id
        WHERE am.application_id = v_application_id
        AND NOT EXISTS (
            SELECT 1
            FROM module_dependencies md
            JOIN modules dependency
                ON dependency.module_id = md.dependency_module_id
            WHERE md.parent_module_id = m.module_id
        )
        AND m.module_category = 'third_party'
        AND m.module_version IS NULL
    ) THEN
        check_result := 'failed';
        message := 'An application dependency is invalid.';
    ELSE
        check_result := 'passed';
        message := 'Registered module metadata is valid.';
    END IF;

    RETURN NEXT;

    -- The application entry point must be registered as a
    -- readable file within the declared filesystem inventory.

    category := 'ENTRY_POINT';

    IF EXISTS (
        SELECT 1
        FROM applications a
        WHERE a.application_id = v_application_id
        AND NOT EXISTS (
            SELECT 1
            FROM filesystem_resources f
            WHERE f.application_id = a.application_id
            AND f.relative_path = a.entry_point
            AND f.resource_type = 'file'
            AND f.readable
        )
    ) THEN
        check_result := 'failed';
        message := 'Application entry point is not registered as readable.';
    ELSE
        check_result := 'passed';
        message := 'Application entry point is registered.';
    END IF;

    RETURN NEXT;

END;
$$;

-- =========================================================
-- DEPLOYMENT PROCESSING PROCEDURE
-- =========================================================

CREATE OR REPLACE PROCEDURE process_deployment(
    p_deployment_id BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_result RECORD;
    v_failed BOOLEAN := FALSE;
BEGIN
    UPDATE deployments
    SET status = 'validating'
    WHERE deployment_id = p_deployment_id
    AND status IN ('registered', 'blocked', 'validating');

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Deployment cannot enter validation state.';
    END IF;

    DELETE FROM validation_checks
    WHERE deployment_id = p_deployment_id;

    FOR v_result IN
        SELECT *
        FROM validate_deployment(p_deployment_id)
    LOOP
        INSERT INTO validation_checks (
            deployment_id,
            check_category,
            check_name,
            result,
            details
        )
        VALUES (
            p_deployment_id,
            v_result.category,
            v_result.category || ' validation',
            v_result.check_result,
            v_result.message
        );

        IF v_result.check_result = 'failed' THEN
            v_failed := TRUE;
        END IF;
    END LOOP;

    UPDATE deployments
    SET
        status = CASE
            WHEN v_failed THEN 'blocked'::deployment_status
            ELSE 'ready'::deployment_status
        END,
        completed_at = CURRENT_TIMESTAMP
    WHERE deployment_id = p_deployment_id;

END;
$$;

-- =========================================================
-- DEPLOYMENT STATUS VIEW
-- =========================================================

CREATE OR REPLACE VIEW deployment_readiness AS
SELECT
    d.deployment_id,
    a.application_name,
    d.deployment_version,
    d.status,
    COUNT(vc.check_id) AS total_checks,
    COUNT(*) FILTER (
        WHERE vc.result = 'passed'
    ) AS passed_checks,
    COUNT(*) FILTER (
        WHERE vc.result = 'warning'
    ) AS warning_checks,
    COUNT(*) FILTER (
        WHERE vc.result = 'failed'
    ) AS failed_checks,
    d.started_at,
    d.completed_at
FROM deployments d
JOIN applications a
    ON a.application_id = d.application_id
LEFT JOIN validation_checks vc
    ON vc.deployment_id = d.deployment_id
GROUP BY
    d.deployment_id,
    a.application_name,
    d.deployment_version,
    d.status,
    d.started_at,
    d.completed_at;

-- =========================================================
-- RETRIEVAL: APPLICATION AND RUNTIME
-- =========================================================

SELECT
    a.application_name,
    a.entry_point,
    a.mode,
    CONCAT(
        a.minimum_node_major, '.',
        a.minimum_node_minor, '.',
        a.minimum_node_patch
    ) AS minimum_node_version,
    CONCAT(
        r.node_major, '.',
        r.node_minor, '.',
        r.node_patch
    ) AS actual_node_version,
    r.platform,
    r.architecture,
    r.process_id,
    r.memory_limit_mb
FROM applications a
LEFT JOIN runtime_instances r
    ON r.application_id = a.application_id;

-- =========================================================
-- RETRIEVAL: MODULE DEPENDENCIES
-- =========================================================

SELECT
    parent.module_name AS parent_module,
    parent.module_version AS parent_version,
    dependency.module_name AS dependency_module,
    dependency.module_category
FROM module_dependencies md
JOIN modules parent
    ON parent.module_id = md.parent_module_id
JOIN modules dependency
    ON dependency.module_id = md.dependency_module_id
ORDER BY parent.module_name, dependency.module_name;

-- =========================================================
-- VALIDATION: REQUIRED ENVIRONMENT VARIABLES
-- =========================================================

SELECT
    definition.variable_name,
    definition.is_required,
    definition.is_secret,
    COALESCE(configuration.configured, FALSE) AS configured,
    CASE
        WHEN definition.is_required
            AND COALESCE(configuration.configured, FALSE) = FALSE
            THEN 'MISSING'
        WHEN definition.is_secret
            THEN 'CONFIGURED_SECRET_VALUE_PROTECTED'
        ELSE 'CONFIGURED'
    END AS validation_status
FROM environment_variable_definitions definition
LEFT JOIN environment_configurations configuration
    ON configuration.definition_id = definition.definition_id
    AND configuration.mode = 'production'
WHERE definition.application_id = (
    SELECT application_id
    FROM applications
    WHERE application_name = 'inventory-api'
)
ORDER BY definition.variable_name;

-- =========================================================
-- AGGREGATION: MODULE COUNTS
-- =========================================================

SELECT
    m.module_category,
    COUNT(*) AS registered_modules
FROM application_modules am
JOIN modules m
    ON m.module_id = am.module_id
GROUP BY m.module_category
ORDER BY m.module_category;

-- =========================================================
-- REPORTING: FILESYSTEM RESOURCES
-- =========================================================

SELECT
    resource_type,
    COUNT(*) AS resource_count,
    SUM(file_size_bytes) AS total_size_bytes,
    COUNT(*) FILTER (WHERE writable) AS writable_resources,
    COUNT(*) FILTER (WHERE readable) AS readable_resources
FROM filesystem_resources
WHERE application_id = (
    SELECT application_id
    FROM applications
    WHERE application_name = 'inventory-api'
)
GROUP BY resource_type
ORDER BY resource_type;

-- =========================================================
-- WORKFLOW: EXECUTE DEPLOYMENT VALIDATION
-- =========================================================

CALL process_deployment(
    (
        SELECT deployment_id
        FROM deployments
        WHERE deployment_version = '1.0.0'
        ORDER BY deployment_id DESC
        LIMIT 1
    )
);

-- =========================================================
-- ELIGIBILITY DETERMINATION
-- =========================================================

SELECT
    deployment_id,
    application_name,
    deployment_version,
    status,
    total_checks,
    passed_checks,
    warning_checks,
    failed_checks,
    CASE
        WHEN status = 'ready' AND failed_checks = 0
            THEN 'ELIGIBLE'
        ELSE 'NOT ELIGIBLE'
    END AS deployment_eligibility
FROM deployment_readiness;

-- =========================================================
-- VALIDATION HISTORY
-- =========================================================

SELECT
    d.deployment_id,
    vc.check_category,
    vc.result,
    vc.details,
    vc.checked_at
FROM validation_checks vc
JOIN deployments d
    ON d.deployment_id = vc.deployment_id
ORDER BY vc.checked_at DESC, vc.check_category;

-- =========================================================
-- FAILURE SCENARIO: MISSING REQUIRED ENVIRONMENT VARIABLE
-- =========================================================

BEGIN;

UPDATE environment_configurations
SET configured = FALSE
WHERE definition_id IN (
    SELECT definition_id
    FROM environment_variable_definitions
    WHERE variable_name = 'DATABASE_URL'
)
AND mode = 'production';

SELECT
    definition.variable_name,
    definition.is_required,
    configuration.configured,
    CASE
        WHEN definition.is_required
            AND NOT COALESCE(configuration.configured, FALSE)
            THEN 'BLOCKED'
        ELSE 'VALID'
    END AS eligibility
FROM environment_variable_definitions definition
LEFT JOIN environment_configurations configuration
    ON configuration.definition_id = definition.definition_id
    AND configuration.mode = 'production'
WHERE definition.variable_name = 'DATABASE_URL';

ROLLBACK;

-- =========================================================
-- FAILURE SCENARIO: INSUFFICIENT NODE.JS VERSION
-- =========================================================

SELECT
    application_name,
    minimum_node_major,
    runtime.node_major AS actual_major,
    CASE
        WHEN runtime.node_major >= minimum_node_major
            THEN 'COMPATIBLE'
        ELSE 'INCOMPATIBLE'
    END AS runtime_compatibility
FROM applications
JOIN runtime_instances runtime
    USING (application_id);

-- =========================================================
-- TRANSACTIONAL DEPLOYMENT GOVERNANCE
-- =========================================================

-- This block demonstrates that deployment status changes
-- and associated validation records are transactionally managed.

BEGIN;

UPDATE deployments
SET status = 'validating'
WHERE deployment_version = '1.0.0'
AND status = 'ready';

SELECT
    deployment_id,
    status
FROM deployments
WHERE deployment_version = '1.0.0';

ROLLBACK;

-- =========================================================
-- OPERATIONAL REPORT
-- =========================================================

SELECT
    a.application_name,
    a.mode,
    d.status,
    COUNT(DISTINCT am.module_id) AS module_count,
    COUNT(DISTINCT fr.resource_id) AS filesystem_resource_count,
    COUNT(DISTINCT ev.definition_id) AS environment_variable_count
FROM applications a
LEFT JOIN deployments d
    ON d.application_id = a.application_id
LEFT JOIN application_modules am
    ON am.application_id = a.application_id
LEFT JOIN filesystem_resources fr
    ON fr.application_id = a.application_id
LEFT JOIN environment_variable_definitions ev
    ON ev.application_id = a.application_id
GROUP BY
    a.application_name,
    a.mode,
    d.status
ORDER BY a.application_name;

COMMIT;
