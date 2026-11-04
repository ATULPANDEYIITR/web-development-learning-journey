-- ============================================================
-- PACKAGE MANAGEMENT GOVERNANCE DATABASE
-- PostgreSQL 15+
--
-- Models:
-- Projects, package manifests, packages, versions,
-- dependencies, lockfiles, npm scripts, security advisories,
-- installation records, and release eligibility.
--
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS package_management;

SET search_path TO package_management, public;

-- ------------------------------------------------------------
-- ENUMERATIONS
-- ------------------------------------------------------------

CREATE TYPE dependency_type AS ENUM (
    'production',
    'development',
    'optional',
    'peer'
);

CREATE TYPE package_status AS ENUM (
    'active',
    'deprecated',
    'withdrawn'
);

CREATE TYPE installation_environment AS ENUM (
    'development',
    'testing',
    'staging',
    'production'
);

CREATE TYPE release_status AS ENUM (
    'pending',
    'approved',
    'rejected'
);

CREATE TYPE advisory_severity AS ENUM (
    'low',
    'moderate',
    'high',
    'critical'
);

-- ------------------------------------------------------------
-- PROJECTS
-- ------------------------------------------------------------

CREATE TABLE projects (
    project_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_name VARCHAR(214) NOT NULL UNIQUE,
    project_version VARCHAR(50) NOT NULL,
    node_engine VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_project_version CHECK (
        project_version ~
        '^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$'
    )
);

-- ------------------------------------------------------------
-- PACKAGE REGISTRY
-- ------------------------------------------------------------

CREATE TABLE packages (
    package_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    package_name VARCHAR(214) NOT NULL UNIQUE,
    description TEXT,
    maintainer VARCHAR(150),
    package_status package_status NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_package_name CHECK (
        package_name ~
        '^(@[a-z0-9._-]+/)?[a-z0-9._-]+$'
    )
);

CREATE TABLE package_versions (
    package_version_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    package_id BIGINT NOT NULL REFERENCES packages(package_id),
    version VARCHAR(50) NOT NULL,
    published_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    integrity_sha256 CHAR(64),
    deprecated BOOLEAN NOT NULL DEFAULT FALSE,

    UNIQUE(package_id, version),

    CONSTRAINT valid_semver CHECK (
        version ~
        '^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$'
    ),

    CONSTRAINT valid_integrity CHECK (
        integrity_sha256 IS NULL OR
        integrity_sha256 ~ '^[a-f0-9]{64}$'
    )
);

-- ------------------------------------------------------------
-- PROJECT DEPENDENCIES
-- ------------------------------------------------------------

CREATE TABLE project_dependencies (
    dependency_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES projects(project_id),
    package_id BIGINT NOT NULL REFERENCES packages(package_id),
    dependency_kind dependency_type NOT NULL,
    version_range VARCHAR(100) NOT NULL,
    is_required BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(project_id, package_id, dependency_kind),

    CONSTRAINT nonempty_version_range CHECK (
        LENGTH(TRIM(version_range)) > 0
    )
);

CREATE INDEX idx_project_dependencies_project
ON project_dependencies(project_id);

CREATE INDEX idx_project_dependencies_package
ON project_dependencies(package_id);

-- ------------------------------------------------------------
-- TRANSITIVE PACKAGE DEPENDENCIES
-- ------------------------------------------------------------

CREATE TABLE package_dependencies (
    package_dependency_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    parent_version_id BIGINT NOT NULL
        REFERENCES package_versions(package_version_id),
    child_package_id BIGINT NOT NULL
        REFERENCES packages(package_id),
    version_range VARCHAR(100) NOT NULL,

    UNIQUE(parent_version_id, child_package_id),

    CONSTRAINT no_empty_transitive_range CHECK (
        LENGTH(TRIM(version_range)) > 0
    )
);

CREATE INDEX idx_package_dependencies_parent
ON package_dependencies(parent_version_id);

-- ------------------------------------------------------------
-- PACKAGE LOCKFILES
-- ------------------------------------------------------------

CREATE TABLE lockfiles (
    lockfile_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES projects(project_id),
    lockfile_version INTEGER NOT NULL,
    content_sha256 CHAR(64) NOT NULL,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    verified BOOLEAN NOT NULL DEFAULT FALSE,

    CONSTRAINT valid_lockfile_version CHECK (
        lockfile_version IN (1, 2, 3)
    ),

    CONSTRAINT valid_lockfile_hash CHECK (
        content_sha256 ~ '^[a-f0-9]{64}$'
    )
);

CREATE INDEX idx_lockfiles_project_date
ON lockfiles(project_id, generated_at DESC);

CREATE TABLE locked_packages (
    locked_package_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    lockfile_id BIGINT NOT NULL REFERENCES lockfiles(lockfile_id),
    package_version_id BIGINT NOT NULL
        REFERENCES package_versions(package_version_id),
    dependency_kind dependency_type NOT NULL,
    resolved_integrity CHAR(64),

    UNIQUE(lockfile_id, package_version_id),

    CONSTRAINT valid_resolved_integrity CHECK (
        resolved_integrity IS NULL OR
        resolved_integrity ~ '^[a-f0-9]{64}$'
    )
);

-- ------------------------------------------------------------
-- NPM SCRIPTS
-- ------------------------------------------------------------

CREATE TABLE npm_scripts (
    script_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES projects(project_id),
    script_name VARCHAR(100) NOT NULL,
    command TEXT NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    execution_timeout_seconds INTEGER NOT NULL DEFAULT 300,

    UNIQUE(project_id, script_name),

    CONSTRAINT valid_script_command CHECK (
        LENGTH(TRIM(command)) > 0
    ),

    CONSTRAINT valid_script_timeout CHECK (
        execution_timeout_seconds BETWEEN 1 AND 86400
    )
);

-- ------------------------------------------------------------
-- SECURITY ADVISORIES
-- ------------------------------------------------------------

CREATE TABLE security_advisories (
    advisory_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    advisory_code VARCHAR(100) NOT NULL UNIQUE,
    package_id BIGINT NOT NULL REFERENCES packages(package_id),
    affected_version_range VARCHAR(100) NOT NULL,
    severity advisory_severity NOT NULL,
    description TEXT NOT NULL,
    published_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE INDEX idx_security_advisories_package
ON security_advisories(package_id, active);

-- ------------------------------------------------------------
-- INSTALLATION RECORDS
-- ------------------------------------------------------------

CREATE TABLE installations (
    installation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES projects(project_id),
    lockfile_id BIGINT REFERENCES lockfiles(lockfile_id),
    environment installation_environment NOT NULL,
    installed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN NOT NULL DEFAULT FALSE,
    failure_reason TEXT
);

CREATE INDEX idx_installations_project_environment
ON installations(project_id, environment, installed_at DESC);

-- ------------------------------------------------------------
-- RELEASE POLICY
-- ------------------------------------------------------------

CREATE TABLE release_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES projects(project_id),
    policy_name VARCHAR(150) NOT NULL,
    require_lockfile BOOLEAN NOT NULL DEFAULT TRUE,
    reject_wildcard_ranges BOOLEAN NOT NULL DEFAULT TRUE,
    maximum_severity advisory_severity NOT NULL DEFAULT 'moderate',
    require_integrity BOOLEAN NOT NULL DEFAULT TRUE,
    active BOOLEAN NOT NULL DEFAULT TRUE,

    UNIQUE(project_id, policy_name)
);

CREATE TABLE release_evaluations (
    evaluation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES projects(project_id),
    policy_id BIGINT NOT NULL REFERENCES release_policies(policy_id),
    lockfile_id BIGINT REFERENCES lockfiles(lockfile_id),
    status release_status NOT NULL DEFAULT 'pending',
    evaluated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    findings JSONB NOT NULL DEFAULT '[]'::JSONB
);

-- ------------------------------------------------------------
-- SEMANTIC VERSION COMPARISON
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION semver_compare(
    left_version TEXT,
    right_version TEXT
)
RETURNS INTEGER
LANGUAGE plpgsql
IMMUTABLE
STRICT
AS $$
DECLARE
    left_parts INTEGER[];
    right_parts INTEGER[];
    i INTEGER;
BEGIN
    IF left_version !~
       '^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$'
       OR right_version !~
       '^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$'
    THEN
        RAISE EXCEPTION 'Invalid semantic version.';
    END IF;

    SELECT ARRAY_AGG(value::INTEGER ORDER BY position)
    INTO left_parts
    FROM regexp_split_to_table(left_version, '\.')
         WITH ORDINALITY AS parts(value, position);

    SELECT ARRAY_AGG(value::INTEGER ORDER BY position)
    INTO right_parts
    FROM regexp_split_to_table(right_version, '\.')
         WITH ORDINALITY AS parts(value, position);

    FOR i IN 1..3 LOOP
        IF left_parts[i] > right_parts[i] THEN
            RETURN 1;
        ELSIF left_parts[i] < right_parts[i] THEN
            RETURN -1;
        END IF;
    END LOOP;

    RETURN 0;
END;
$$;

-- ------------------------------------------------------------
-- VERSION RANGE EVALUATION
-- Supports exact, ^, ~, >=, <=, > and <.
-- Complex npm ranges and prerelease rules require a full
-- npm-compatible semver implementation.
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION semver_satisfies(
    candidate TEXT,
    version_range TEXT
)
RETURNS BOOLEAN
LANGUAGE plpgsql
IMMUTABLE
STRICT
AS $$
DECLARE
    operator TEXT;
    base_version TEXT;
    comparison INTEGER;
    candidate_major INTEGER;
    candidate_minor INTEGER;
    base_major INTEGER;
    base_minor INTEGER;
    base_patch INTEGER;
BEGIN
    IF version_range IN ('*', 'latest') THEN
        RETURN TRUE;
    END IF;

    IF candidate !~
       '^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$'
    THEN
        RETURN FALSE;
    END IF;

    operator := substring(version_range FROM '^(>=|<=|>|<|\^|~)');

    IF operator IS NULL THEN
        operator := '=';
        base_version := version_range;
    ELSE
        base_version := substring(
            version_range FROM length(operator) + 1
        );
    END IF;

    IF base_version !~
       '^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$'
    THEN
        RETURN FALSE;
    END IF;

    comparison := semver_compare(candidate, base_version);

    SELECT split_part(candidate, '.', 1)::INTEGER,
           split_part(candidate, '.', 2)::INTEGER,
           split_part(base_version, '.', 1)::INTEGER,
           split_part(base_version, '.', 2)::INTEGER,
           split_part(base_version, '.', 3)::INTEGER
    INTO candidate_major, candidate_minor,
         base_major, base_minor, base_patch;

    CASE operator
        WHEN '=' THEN RETURN comparison = 0;
        WHEN '>=' THEN RETURN comparison >= 0;
        WHEN '<=' THEN RETURN comparison <= 0;
        WHEN '>' THEN RETURN comparison > 0;
        WHEN '<' THEN RETURN comparison < 0;

        WHEN '~' THEN
            RETURN comparison >= 0
               AND candidate_major = base_major
               AND candidate_minor = base_minor;

        WHEN '^' THEN
            IF comparison < 0 THEN
                RETURN FALSE;
            END IF;

            IF base_major > 0 THEN
                RETURN candidate_major = base_major;
            ELSIF base_minor > 0 THEN
                RETURN candidate_major = 0
                   AND candidate_minor = base_minor;
            ELSE
                RETURN candidate_major = 0
                   AND candidate_minor = 0
                   AND split_part(candidate, '.', 3)::INTEGER = base_patch;
            END IF;

        ELSE
            RETURN FALSE;
    END CASE;
END;
$$;

-- ------------------------------------------------------------
-- AUTOMATIC AUDIT TIMESTAMPS
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION prevent_withdrawn_package_publish()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    current_status package_status;
BEGIN
    SELECT package_status
    INTO current_status
    FROM packages
    WHERE package_id = NEW.package_id
    FOR SHARE;

    IF current_status = 'withdrawn' THEN
        RAISE EXCEPTION
            'Cannot publish a version of a withdrawn package.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_prevent_withdrawn_package_publish
BEFORE INSERT ON package_versions
FOR EACH ROW
EXECUTE FUNCTION prevent_withdrawn_package_publish();

-- ------------------------------------------------------------
-- RELEASE EVALUATION FUNCTION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION evaluate_project_release(
    p_project_id BIGINT,
    p_policy_id BIGINT,
    p_lockfile_id BIGINT
)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    policy_row release_policies%ROWTYPE;
    lock_row lockfiles%ROWTYPE;
    finding_list JSONB := '[]'::JSONB;
    dependency_record RECORD;
    advisory_record RECORD;
    evaluation_id_result BIGINT;
    blocked BOOLEAN := FALSE;
BEGIN
    SELECT *
    INTO policy_row
    FROM release_policies
    WHERE policy_id = p_policy_id
      AND project_id = p_project_id
      AND active = TRUE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Active release policy not found.';
    END IF;

    IF p_lockfile_id IS NOT NULL THEN
        SELECT *
        INTO lock_row
        FROM lockfiles
        WHERE lockfile_id = p_lockfile_id
          AND project_id = p_project_id;
    END IF;

    IF policy_row.require_lockfile AND NOT FOUND THEN
        finding_list := finding_list ||
            jsonb_build_array(
                jsonb_build_object(
                    'type', 'LOCKFILE',
                    'message', 'Required lockfile is missing.'
                )
            );
        blocked := TRUE;
    ELSIF p_lockfile_id IS NOT NULL AND lock_row.lockfile_id IS NULL THEN
        finding_list := finding_list ||
            jsonb_build_array(
                jsonb_build_object(
                    'type', 'LOCKFILE',
                    'message', 'Lockfile does not belong to this project.'
                )
            );
        blocked := TRUE;
    ELSIF p_lockfile_id IS NOT NULL AND NOT lock_row.verified THEN
        finding_list := finding_list ||
            jsonb_build_array(
                jsonb_build_object(
                    'type', 'LOCKFILE',
                    'message', 'Lockfile has not been verified.'
                )
            );
        blocked := TRUE;
    END IF;

    -- Inspect direct dependency range declarations.
    FOR dependency_record IN
        SELECT p.package_name, d.version_range
        FROM project_dependencies d
        JOIN packages p ON p.package_id = d.package_id
        WHERE d.project_id = p_project_id
    LOOP
        IF policy_row.reject_wildcard_ranges
           AND dependency_record.version_range = '*'
        THEN
            finding_list := finding_list ||
                jsonb_build_array(
                    jsonb_build_object(
                        'type', 'UNBOUNDED_DEPENDENCY',
                        'package', dependency_record.package_name
                    )
                );

            blocked := TRUE;
        END IF;
    END LOOP;

    -- Inspect actual locked versions against security advisories.
    IF p_lockfile_id IS NOT NULL THEN
        FOR advisory_record IN
            SELECT
                p.package_name,
                pv.version,
                sa.advisory_code,
                sa.severity,
                sa.affected_version_range
            FROM locked_packages lp
            JOIN package_versions pv
                ON pv.package_version_id = lp.package_version_id
            JOIN packages p
                ON p.package_id = pv.package_id
            JOIN security_advisories sa
                ON sa.package_id = p.package_id
            WHERE lp.lockfile_id = p_lockfile_id
              AND sa.active = TRUE
              AND semver_satisfies(
                  pv.version,
                  sa.affected_version_range
              )
        LOOP
            finding_list := finding_list ||
                jsonb_build_array(
                    jsonb_build_object(
                        'type', 'SECURITY_ADVISORY',
                        'package', advisory_record.package_name,
                        'version', advisory_record.version,
                        'advisory', advisory_record.advisory_code,
                        'severity', advisory_record.severity
                    )
                );

            IF CASE policy_row.maximum_severity
                WHEN 'low' THEN
                    advisory_record.severity IN (
                        'moderate', 'high', 'critical'
                    )
                WHEN 'moderate' THEN
                    advisory_record.severity IN ('high', 'critical')
                WHEN 'high' THEN
                    advisory_record.severity = 'critical'
                ELSE FALSE
            END THEN
                blocked := TRUE;
            END IF;
        END LOOP;

        IF policy_row.require_integrity AND EXISTS (
            SELECT 1
            FROM locked_packages lp
            JOIN package_versions pv
                ON pv.package_version_id = lp.package_version_id
            WHERE lp.lockfile_id = p_lockfile_id
              AND (
                  lp.resolved_integrity IS NULL
                  OR pv.integrity_sha256 IS NULL
                  OR lp.resolved_integrity <> pv.integrity_sha256
              )
        ) THEN
            finding_list := finding_list ||
                jsonb_build_array(
                    jsonb_build_object(
                        'type', 'INTEGRITY',
                        'message', 'Package integrity verification failed.'
                    )
                );

            blocked := TRUE;
        END IF;
    END IF;

    INSERT INTO release_evaluations (
        project_id,
        policy_id,
        lockfile_id,
        status,
        findings
    )
    VALUES (
        p_project_id,
        p_policy_id,
        p_lockfile_id,
        CASE
            WHEN blocked THEN 'rejected'::release_status
            ELSE 'approved'::release_status
        END,
        finding_list
    )
    RETURNING evaluation_id INTO evaluation_id_result;

    RETURN evaluation_id_result;
END;
$$;

-- ------------------------------------------------------------
-- SAMPLE PROJECTS
-- ------------------------------------------------------------

INSERT INTO projects (
    project_name,
    project_version,
    node_engine
)
VALUES
    ('enterprise-api', '2.1.0', 'node-20'),
    ('analytics-dashboard', '1.4.0', 'node-20');

INSERT INTO packages (
    package_name,
    description,
    maintainer
)
VALUES
    ('express', 'Node.js web application framework', 'platform-team'),
    ('pg', 'PostgreSQL client for Node.js', 'database-team'),
    ('typescript', 'JavaScript type system', 'frontend-team'),
    ('jest', 'JavaScript testing framework', 'qa-team'),
    ('lodash', 'JavaScript utility library', 'platform-team');

INSERT INTO package_versions (
    package_id,
    version,
    integrity_sha256
)
SELECT
    package_id,
    version,
    encode(
        digest(package_name || '@' || version, 'sha256'),
        'hex'
    )
FROM packages
CROSS JOIN (
    VALUES
        ('express', '4.21.0'),
        ('express', '4.21.1'),
        ('pg', '8.13.0'),
        ('pg', '8.14.0'),
        ('typescript', '5.7.0'),
        ('jest', '29.7.0'),
        ('lodash', '4.17.20'),
        ('lodash', '4.17.21')
) AS versions(package_name, version)
WHERE packages.package_name = versions.package_name;

-- ------------------------------------------------------------
-- PROJECT DEPENDENCIES
-- ------------------------------------------------------------

INSERT INTO project_dependencies (
    project_id,
    package_id,
    dependency_kind,
    version_range
)
SELECT
    pr.project_id,
    p.package_id,
    d.kind::dependency_type,
    d.version_range
FROM (
    VALUES
        ('enterprise-api', 'express', 'production', '^4.21.0'),
        ('enterprise-api', 'pg', 'production', '^8.13.0'),
        ('enterprise-api', 'jest', 'development', '^29.0.0'),
        ('enterprise-api', 'typescript', 'development', '^5.7.0'),
        ('analytics-dashboard', 'lodash', 'production', '^4.17.0'),
        ('analytics-dashboard', 'typescript', 'development', '^5.7.0')
) AS d(project_name, package_name, kind, version_range)
JOIN projects pr ON pr.project_name = d.project_name
JOIN packages p ON p.package_name = d.package_name;

-- ------------------------------------------------------------
-- NPM SCRIPTS
-- ------------------------------------------------------------

INSERT INTO npm_scripts (
    project_id,
    script_name,
    command,
    execution_timeout_seconds
)
SELECT
    project_id,
    scripts.script_name,
    scripts.command,
    scripts.timeout_seconds
FROM projects
CROSS JOIN (
    VALUES
        ('start', 'node server.js', 300),
        ('test', 'jest --runInBand', 600),
        ('build', 'tsc --build', 900),
        ('lint', 'eslint .', 300)
) AS scripts(script_name, command, timeout_seconds)
WHERE projects.project_name = 'enterprise-api';

-- ------------------------------------------------------------
-- SECURITY ADVISORIES
-- ------------------------------------------------------------

INSERT INTO security_advisories (
    advisory_code,
    package_id,
    affected_version_range,
    severity,
    description
)
SELECT
    'DEMO-LODASH-001',
    package_id,
    '<4.17.21',
    'high',
    'Demonstration advisory for outdated lodash versions.'
FROM packages
WHERE package_name = 'lodash';

INSERT INTO security_advisories (
    advisory_code,
    package_id,
    affected_version_range,
    severity,
    description
)
SELECT
    'DEMO-PG-001',
    package_id,
    '<8.14.0',
    'moderate',
    'Demonstration advisory for an outdated database driver.'
FROM packages
WHERE package_name = 'pg';

-- ------------------------------------------------------------
-- RELEASE POLICIES
-- ------------------------------------------------------------

INSERT INTO release_policies (
    project_id,
    policy_name,
    require_lockfile,
    reject_wildcard_ranges,
    maximum_severity,
    require_integrity
)
SELECT
    project_id,
    'Production Security Policy',
    TRUE,
    TRUE,
    'moderate',
    TRUE
FROM projects;

-- ------------------------------------------------------------
-- DEMONSTRATION LOCKFILES
-- ------------------------------------------------------------

INSERT INTO lockfiles (
    project_id,
    lockfile_version,
    content_sha256,
    verified
)
SELECT
    project_id,
    3,
    repeat('a', 64),
    TRUE
FROM projects;

-- Lock exact package versions.
INSERT INTO locked_packages (
    lockfile_id,
    package_version_id,
    dependency_kind,
    resolved_integrity
)
SELECT
    l.lockfile_id,
    pv.package_version_id,
    CASE
        WHEN p.package_name IN ('jest', 'typescript')
            THEN 'development'::dependency_type
        ELSE 'production'::dependency_type
    END,
    pv.integrity_sha256
FROM lockfiles l
JOIN projects pr ON pr.project_id = l.project_id
JOIN (
    VALUES
        ('enterprise-api', 'express', '4.21.1'),
        ('enterprise-api', 'pg', '8.13.0'),
        ('enterprise-api', 'jest', '29.7.0'),
        ('enterprise-api', 'typescript', '5.7.0'),
        ('analytics-dashboard', 'lodash', '4.17.20'),
        ('analytics-dashboard', 'typescript', '5.7.0')
) AS selected(project_name, package_name, version)
    ON selected.project_name = pr.project_name
JOIN packages p ON p.package_name = selected.package_name
JOIN package_versions pv
    ON pv.package_id = p.package_id
   AND pv.version = selected.version;

-- ------------------------------------------------------------
-- SEMANTIC VERSIONING TESTS
-- ------------------------------------------------------------

SELECT
    '4.21.1' AS candidate,
    '^4.0.0' AS version_range,
    semver_satisfies('4.21.1', '^4.0.0') AS accepted;

SELECT
    '4.21.1' AS candidate,
    '~4.21.0' AS version_range,
    semver_satisfies('4.21.1', '~4.21.0') AS accepted;

SELECT
    '5.0.0' AS candidate,
    '^4.0.0' AS version_range,
    semver_satisfies('5.0.0', '^4.0.0') AS accepted;

-- ------------------------------------------------------------
-- DEPENDENCY INVENTORY
-- ------------------------------------------------------------

SELECT
    pr.project_name,
    p.package_name,
    d.dependency_kind,
    d.version_range,
    d.is_required
FROM project_dependencies d
JOIN projects pr ON pr.project_id = d.project_id
JOIN packages p ON p.package_id = d.package_id
ORDER BY pr.project_name, d.dependency_kind, p.package_name;

-- ------------------------------------------------------------
-- DEPENDENCY AGGREGATION
-- ------------------------------------------------------------

SELECT
    pr.project_name,
    COUNT(*) FILTER (
        WHERE d.dependency_kind = 'production'
    ) AS production_dependencies,
    COUNT(*) FILTER (
        WHERE d.dependency_kind = 'development'
    ) AS development_dependencies,
    COUNT(*) FILTER (
        WHERE d.dependency_kind = 'optional'
    ) AS optional_dependencies,
    COUNT(*) FILTER (
        WHERE d.dependency_kind = 'peer'
    ) AS peer_dependencies
FROM projects pr
LEFT JOIN project_dependencies d
    ON d.project_id = pr.project_id
GROUP BY pr.project_id, pr.project_name
ORDER BY pr.project_name;

-- ------------------------------------------------------------
-- LOCKFILE CONTENT REPORT
-- ------------------------------------------------------------

SELECT
    pr.project_name,
    p.package_name,
    pv.version,
    lp.dependency_kind,
    lp.resolved_integrity
FROM locked_packages lp
JOIN lockfiles l ON l.lockfile_id = lp.lockfile_id
JOIN projects pr ON pr.project_id = l.project_id
JOIN package_versions pv
    ON pv.package_version_id = lp.package_version_id
JOIN packages p ON p.package_id = pv.package_id
ORDER BY pr.project_name, p.package_name;

-- ------------------------------------------------------------
-- LOCKFILE DEPENDENCY VALIDATION
-- ------------------------------------------------------------

SELECT
    pr.project_name,
    p.package_name,
    d.version_range,
    pv.version AS locked_version,
    semver_satisfies(pv.version, d.version_range) AS compatible
FROM project_dependencies d
JOIN projects pr ON pr.project_id = d.project_id
JOIN packages p ON p.package_id = d.package_id
LEFT JOIN lockfiles l ON l.project_id = pr.project_id
LEFT JOIN locked_packages lp
    ON lp.lockfile_id = l.lockfile_id
JOIN package_versions pv
    ON pv.package_version_id = lp.package_version_id
   AND pv.package_id = p.package_id
WHERE l.verified = TRUE
ORDER BY pr.project_name, p.package_name;

-- ------------------------------------------------------------
-- SECURITY AUDIT REPORT
-- ------------------------------------------------------------

SELECT
    pr.project_name,
    p.package_name,
    pv.version,
    sa.advisory_code,
    sa.severity,
    sa.affected_version_range,
    semver_satisfies(
        pv.version,
        sa.affected_version_range
    ) AS affected
FROM locked_packages lp
JOIN lockfiles l ON l.lockfile_id = lp.lockfile_id
JOIN projects pr ON pr.project_id = l.project_id
JOIN package_versions pv
    ON pv.package_version_id = lp.package_version_id
JOIN packages p ON p.package_id = pv.package_id
JOIN security_advisories sa
    ON sa.package_id = p.package_id
WHERE sa.active = TRUE
  AND semver_satisfies(pv.version, sa.affected_version_range)
ORDER BY
    CASE sa.severity
        WHEN 'critical' THEN 1
        WHEN 'high' THEN 2
        WHEN 'moderate' THEN 3
        ELSE 4
    END;

-- ------------------------------------------------------------
-- RELEASE ELIGIBILITY EVALUATION
-- ------------------------------------------------------------

DO $$
DECLARE
    project_record RECORD;
    evaluation_result BIGINT;
BEGIN
    FOR project_record IN
        SELECT
            p.project_id,
            rp.policy_id,
            l.lockfile_id
        FROM projects p
        JOIN release_policies rp
            ON rp.project_id = p.project_id
           AND rp.active = TRUE
        LEFT JOIN lockfiles l
            ON l.project_id = p.project_id
    LOOP
        evaluation_result := evaluate_project_release(
            project_record.project_id,
            project_record.policy_id,
            project_record.lockfile_id
        );

        RAISE NOTICE
            'Project % evaluated. Evaluation ID: %',
            project_record.project_id,
            evaluation_result;
    END LOOP;
END;
$$;

-- ------------------------------------------------------------
-- RELEASE EVALUATION REPORT
-- ------------------------------------------------------------

SELECT
    pr.project_name,
    rp.policy_name,
    re.evaluation_id,
    re.status,
    re.findings,
    re.evaluated_at
FROM release_evaluations re
JOIN projects pr ON pr.project_id = re.project_id
JOIN release_policies rp ON rp.policy_id = re.policy_id
ORDER BY re.evaluated_at DESC;

-- ------------------------------------------------------------
-- NPM SCRIPT INVENTORY
-- ------------------------------------------------------------

SELECT
    pr.project_name,
    ns.script_name,
    ns.command,
    ns.enabled,
    ns.execution_timeout_seconds
FROM npm_scripts ns
JOIN projects pr ON pr.project_id = ns.project_id
ORDER BY pr.project_name, ns.script_name;

-- ------------------------------------------------------------
-- TRANSACTIONAL INSTALLATION RECORD
-- ------------------------------------------------------------

DO $$
DECLARE
    selected_project BIGINT;
    selected_lockfile BIGINT;
BEGIN
    SELECT project_id
    INTO selected_project
    FROM projects
    WHERE project_name = 'enterprise-api';

    SELECT lockfile_id
    INTO selected_lockfile
    FROM lockfiles
    WHERE project_id = selected_project
    ORDER BY generated_at DESC
    LIMIT 1;

    INSERT INTO installations (
        project_id,
        lockfile_id,
        environment,
        success
    )
    VALUES (
        selected_project,
        selected_lockfile,
        'staging',
        TRUE
    );

    RAISE NOTICE 'Staging installation recorded.';
END;
$$;

-- ------------------------------------------------------------
-- FAILURE CASE: UNBOUNDED DEPENDENCY DETECTION
-- ------------------------------------------------------------

SELECT
    pr.project_name,
    p.package_name,
    d.version_range,
    'UNBOUNDED RANGE' AS validation_result
FROM project_dependencies d
JOIN projects pr ON pr.project_id = d.project_id
JOIN packages p ON p.package_id = d.package_id
WHERE d.version_range IN ('*', 'latest');

-- ------------------------------------------------------------
-- FAILURE CASE: INTEGRITY MISMATCH
-- ------------------------------------------------------------

SELECT
    pr.project_name,
    p.package_name,
    pv.version,
    'INTEGRITY MISMATCH' AS validation_result
FROM locked_packages lp
JOIN lockfiles l ON l.lockfile_id = lp.lockfile_id
JOIN projects pr ON pr.project_id = l.project_id
JOIN package_versions pv
    ON pv.package_version_id = lp.package_version_id
JOIN packages p ON p.package_id = pv.package_id
WHERE lp.resolved_integrity IS DISTINCT FROM pv.integrity_sha256;

-- ------------------------------------------------------------
-- FINAL DATABASE STATISTICS
-- ------------------------------------------------------------

SELECT
    (SELECT COUNT(*) FROM projects) AS projects,
    (SELECT COUNT(*) FROM packages) AS packages,
    (SELECT COUNT(*) FROM package_versions) AS package_versions,
    (SELECT COUNT(*) FROM project_dependencies) AS dependencies,
    (SELECT COUNT(*) FROM lockfiles) AS lockfiles,
    (SELECT COUNT(*) FROM security_advisories) AS advisories,
    (SELECT COUNT(*) FROM release_evaluations) AS evaluations;

COMMIT;
