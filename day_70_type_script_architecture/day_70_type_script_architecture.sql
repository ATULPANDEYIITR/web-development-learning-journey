-- ============================================================
-- TYPESCRIPT ARCHITECTURE MANAGEMENT DATABASE
-- PostgreSQL 15+
--
-- Models:
-- 1. Projects and source files.
-- 2. TypeScript interfaces and properties.
-- 3. Interface inheritance.
-- 4. Modules, imports and exports.
-- 5. Declaration files.
-- 6. Compiler configurations.
-- 7. Strict-mode policies.
-- 8. Architecture validation.
-- 9. Dependency graphs and build ordering.
-- 10. Validation diagnostics.
--
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS ts_architecture;

SET search_path TO ts_architecture, public;

-- ============================================================
-- ENUMERATED DOMAIN TYPES
-- ============================================================

CREATE TYPE module_kind AS ENUM (
    'esm',
    'commonjs',
    'declaration',
    'ambient'
);

CREATE TYPE property_kind AS ENUM (
    'primitive',
    'object',
    'function',
    'array',
    'union',
    'intersection',
    'generic',
    'custom'
);

CREATE TYPE diagnostic_severity AS ENUM (
    'error',
    'warning',
    'info'
);

CREATE TYPE validation_status AS ENUM (
    'pending',
    'running',
    'passed',
    'failed'
);

-- ============================================================
-- PROJECTS
-- ============================================================

CREATE TABLE projects (
    project_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_name VARCHAR(150) NOT NULL UNIQUE,
    description TEXT,
    typescript_version VARCHAR(30) NOT NULL,
    project_root TEXT NOT NULL DEFAULT '.',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_project_name
        CHECK (length(trim(project_name)) > 0)
);

-- ============================================================
-- COMPILER CONFIGURATION
-- One configuration per project.
-- ============================================================

CREATE TABLE compiler_configurations (
    configuration_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    project_id BIGINT NOT NULL UNIQUE
        REFERENCES projects(project_id)
        ON DELETE CASCADE,

    target VARCHAR(30) NOT NULL DEFAULT 'ES2022',
    module_system VARCHAR(30) NOT NULL DEFAULT 'NodeNext',
    module_resolution VARCHAR(30) NOT NULL DEFAULT 'NodeNext',

    strict BOOLEAN NOT NULL DEFAULT TRUE,
    strict_null_checks BOOLEAN NOT NULL DEFAULT TRUE,
    no_implicit_any BOOLEAN NOT NULL DEFAULT TRUE,
    strict_function_types BOOLEAN NOT NULL DEFAULT TRUE,
    strict_property_initialization BOOLEAN NOT NULL DEFAULT TRUE,
    no_implicit_override BOOLEAN NOT NULL DEFAULT TRUE,
    no_unused_locals BOOLEAN NOT NULL DEFAULT TRUE,
    no_unused_parameters BOOLEAN NOT NULL DEFAULT TRUE,
    no_unchecked_indexed_access BOOLEAN NOT NULL DEFAULT TRUE,
    exact_optional_property_types BOOLEAN NOT NULL DEFAULT TRUE,

    declaration_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    declaration_map BOOLEAN NOT NULL DEFAULT TRUE,
    source_map BOOLEAN NOT NULL DEFAULT TRUE,
    es_module_interop BOOLEAN NOT NULL DEFAULT TRUE,
    force_consistent_casing BOOLEAN NOT NULL DEFAULT TRUE,
    skip_lib_check BOOLEAN NOT NULL DEFAULT FALSE,

    root_directory TEXT NOT NULL DEFAULT 'src',
    output_directory TEXT NOT NULL DEFAULT 'dist',

    include_patterns JSONB NOT NULL
        DEFAULT '["src/**/*.ts"]'::jsonb,

    exclude_patterns JSONB NOT NULL
        DEFAULT '["node_modules","dist"]'::jsonb,

    path_aliases JSONB NOT NULL
        DEFAULT '{}'::jsonb,

    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT different_source_output_directories
        CHECK (root_directory <> output_directory),

    CONSTRAINT valid_include_patterns
        CHECK (jsonb_typeof(include_patterns) = 'array'),

    CONSTRAINT valid_exclude_patterns
        CHECK (jsonb_typeof(exclude_patterns) = 'array'),

    CONSTRAINT valid_path_aliases
        CHECK (jsonb_typeof(path_aliases) = 'object')
);

-- ============================================================
-- STRICT CONFIGURATION ENFORCEMENT
-- ============================================================

CREATE OR REPLACE FUNCTION validate_compiler_configuration()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.strict THEN
        IF NOT NEW.strict_null_checks
           OR NOT NEW.no_implicit_any
           OR NOT NEW.strict_function_types
           OR NOT NEW.strict_property_initialization
        THEN
            RAISE EXCEPTION
                'Strict mode requires all mandatory strict checks.';
        END IF;
    END IF;

    IF NEW.root_directory = NEW.output_directory THEN
        RAISE EXCEPTION
            'Source and output directories must differ.';
    END IF;

    IF jsonb_array_length(NEW.include_patterns) = 0 THEN
        RAISE EXCEPTION
            'At least one include pattern is required.';
    END IF;

    NEW.updated_at := CURRENT_TIMESTAMP;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_compiler_configuration
BEFORE INSERT OR UPDATE
ON compiler_configurations
FOR EACH ROW
EXECUTE FUNCTION validate_compiler_configuration();

-- ============================================================
-- SOURCE FILES
-- ============================================================

CREATE TABLE source_files (
    file_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    project_id BIGINT NOT NULL
        REFERENCES projects(project_id)
        ON DELETE CASCADE,

    file_path TEXT NOT NULL,
    extension VARCHAR(15) NOT NULL,
    is_declaration BOOLEAN NOT NULL DEFAULT FALSE,
    is_entry_point BOOLEAN NOT NULL DEFAULT FALSE,
    source_hash VARCHAR(128),

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_project_file
        UNIQUE(project_id, file_path),

    CONSTRAINT supported_typescript_extensions
        CHECK (
            extension IN (
                '.ts',
                '.tsx',
                '.mts',
                '.cts',
                '.d.ts'
            )
        ),

    CONSTRAINT valid_file_path
        CHECK (length(trim(file_path)) > 0)
);

CREATE INDEX idx_source_files_project
    ON source_files(project_id);

CREATE INDEX idx_source_files_declarations
    ON source_files(project_id, is_declaration);

-- ============================================================
-- INTERFACES
-- ============================================================

CREATE TABLE interfaces (
    interface_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    project_id BIGINT NOT NULL
        REFERENCES projects(project_id)
        ON DELETE CASCADE,

    file_id BIGINT
        REFERENCES source_files(file_id)
        ON DELETE SET NULL,

    interface_name VARCHAR(150) NOT NULL,
    is_exported BOOLEAN NOT NULL DEFAULT FALSE,
    is_declaration_only BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_interface_name
        UNIQUE(project_id, interface_name),

    CONSTRAINT valid_interface_name
        CHECK (length(trim(interface_name)) > 0)
);

CREATE INDEX idx_interfaces_project
    ON interfaces(project_id);

-- ============================================================
-- INTERFACE INHERITANCE
-- ============================================================

CREATE TABLE interface_inheritance (
    inheritance_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    child_interface_id BIGINT NOT NULL
        REFERENCES interfaces(interface_id)
        ON DELETE CASCADE,

    parent_interface_id BIGINT NOT NULL
        REFERENCES interfaces(interface_id)
        ON DELETE RESTRICT,

    CONSTRAINT unique_interface_parent
        UNIQUE(child_interface_id, parent_interface_id),

    CONSTRAINT no_direct_self_inheritance
        CHECK (child_interface_id <> parent_interface_id)
);

CREATE INDEX idx_inheritance_parent
    ON interface_inheritance(parent_interface_id);

-- ============================================================
-- INTERFACE PROPERTIES
-- ============================================================

CREATE TABLE interface_properties (
    property_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    interface_id BIGINT NOT NULL
        REFERENCES interfaces(interface_id)
        ON DELETE CASCADE,

    property_name VARCHAR(150) NOT NULL,
    property_type TEXT NOT NULL,
    property_category property_kind NOT NULL DEFAULT 'custom',

    is_optional BOOLEAN NOT NULL DEFAULT FALSE,
    is_readonly BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_interface_property
        UNIQUE(interface_id, property_name),

    CONSTRAINT valid_property_name
        CHECK (length(trim(property_name)) > 0),

    CONSTRAINT valid_property_type
        CHECK (length(trim(property_type)) > 0)
);

CREATE INDEX idx_properties_interface
    ON interface_properties(interface_id);

-- ============================================================
-- MODULES
-- ============================================================

CREATE TABLE modules (
    module_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    project_id BIGINT NOT NULL
        REFERENCES projects(project_id)
        ON DELETE CASCADE,

    file_id BIGINT NOT NULL
        REFERENCES source_files(file_id)
        ON DELETE CASCADE,

    module_name VARCHAR(150) NOT NULL,
    module_type module_kind NOT NULL DEFAULT 'esm',

    is_entry_point BOOLEAN NOT NULL DEFAULT FALSE,
    description TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_module_name
        UNIQUE(project_id, module_name),

    CONSTRAINT unique_module_file
        UNIQUE(project_id, file_id)
);

CREATE INDEX idx_modules_project
    ON modules(project_id);

CREATE INDEX idx_modules_entry_points
    ON modules(project_id, is_entry_point)
    WHERE is_entry_point = TRUE;

-- ============================================================
-- MODULE EXPORTS
-- ============================================================

CREATE TABLE module_exports (
    export_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    module_id BIGINT NOT NULL
        REFERENCES modules(module_id)
        ON DELETE CASCADE,

    symbol_name VARCHAR(150) NOT NULL,
    export_kind VARCHAR(30) NOT NULL DEFAULT 'named',

    CONSTRAINT unique_module_export
        UNIQUE(module_id, symbol_name),

    CONSTRAINT valid_export_kind
        CHECK (
            export_kind IN (
                'named',
                'default',
                'namespace',
                'type'
            )
        )
);

CREATE INDEX idx_module_exports_symbol
    ON module_exports(symbol_name);

-- ============================================================
-- MODULE IMPORTS
-- ============================================================

CREATE TABLE module_imports (
    import_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    source_module_id BIGINT NOT NULL
        REFERENCES modules(module_id)
        ON DELETE CASCADE,

    target_module_id BIGINT NOT NULL
        REFERENCES modules(module_id)
        ON DELETE RESTRICT,

    imported_symbol VARCHAR(150),
    import_kind VARCHAR(30) NOT NULL DEFAULT 'named',

    CONSTRAINT unique_module_import
        UNIQUE(
            source_module_id,
            target_module_id,
            imported_symbol
        ),

    CONSTRAINT no_direct_self_import
        CHECK (source_module_id <> target_module_id),

    CONSTRAINT valid_import_kind
        CHECK (
            import_kind IN (
                'named',
                'default',
                'namespace',
                'side_effect',
                'type'
            )
        )
);

CREATE INDEX idx_import_source
    ON module_imports(source_module_id);

CREATE INDEX idx_import_target
    ON module_imports(target_module_id);

-- ============================================================
-- MODULE INTERFACE ASSOCIATIONS
-- ============================================================

CREATE TABLE module_interfaces (
    module_id BIGINT NOT NULL
        REFERENCES modules(module_id)
        ON DELETE CASCADE,

    interface_id BIGINT NOT NULL
        REFERENCES interfaces(interface_id)
        ON DELETE CASCADE,

    PRIMARY KEY(module_id, interface_id)
);

-- ============================================================
-- VALIDATION RUNS
-- ============================================================

CREATE TABLE validation_runs (
    run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    project_id BIGINT NOT NULL
        REFERENCES projects(project_id)
        ON DELETE CASCADE,

    configuration_id BIGINT
        REFERENCES compiler_configurations(configuration_id)
        ON DELETE SET NULL,

    status validation_status NOT NULL DEFAULT 'pending',

    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    module_count INTEGER NOT NULL DEFAULT 0,
    error_count INTEGER NOT NULL DEFAULT 0,
    warning_count INTEGER NOT NULL DEFAULT 0,

    CONSTRAINT nonnegative_validation_counts
        CHECK (
            module_count >= 0
            AND error_count >= 0
            AND warning_count >= 0
        ),

    CONSTRAINT valid_validation_timestamps
        CHECK (
            completed_at IS NULL
            OR started_at IS NULL
            OR completed_at >= started_at
        )
);

CREATE INDEX idx_validation_project_time
    ON validation_runs(project_id, started_at DESC);

-- ============================================================
-- VALIDATION DIAGNOSTICS
-- ============================================================

CREATE TABLE architecture_diagnostics (
    diagnostic_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    run_id BIGINT NOT NULL
        REFERENCES validation_runs(run_id)
        ON DELETE CASCADE,

    file_id BIGINT
        REFERENCES source_files(file_id)
        ON DELETE SET NULL,

    diagnostic_code VARCHAR(40) NOT NULL,
    severity diagnostic_severity NOT NULL,
    message TEXT NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT nonempty_diagnostic_message
        CHECK (length(trim(message)) > 0)
);

CREATE INDEX idx_diagnostics_run_severity
    ON architecture_diagnostics(run_id, severity);

CREATE INDEX idx_diagnostics_code
    ON architecture_diagnostics(diagnostic_code);

-- ============================================================
-- MODULE IMPORT VALIDATION
-- Ensures imported symbols exist in the target module.
-- ============================================================

CREATE OR REPLACE FUNCTION validate_module_import()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    source_project BIGINT;
    target_project BIGINT;
    target_kind module_kind;
BEGIN
    SELECT project_id
    INTO source_project
    FROM modules
    WHERE module_id = NEW.source_module_id;

    SELECT project_id, module_type
    INTO target_project, target_kind
    FROM modules
    WHERE module_id = NEW.target_module_id;

    IF source_project IS DISTINCT FROM target_project THEN
        RAISE EXCEPTION
            'Modules belonging to different projects cannot be linked.';
    END IF;

    IF target_kind = 'ambient' AND NEW.import_kind = 'side_effect' THEN
        RAISE EXCEPTION
            'Ambient declarations cannot be used as side-effect modules.';
    END IF;

    IF NEW.imported_symbol IS NOT NULL THEN
        IF NOT EXISTS (
            SELECT 1
            FROM module_exports
            WHERE module_id = NEW.target_module_id
              AND symbol_name = NEW.imported_symbol
        ) THEN
            RAISE EXCEPTION
                'Imported symbol % is not exported by target module.',
                NEW.imported_symbol;
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_module_import
BEFORE INSERT OR UPDATE
ON module_imports
FOR EACH ROW
EXECUTE FUNCTION validate_module_import();

-- ============================================================
-- INTERFACE INHERITANCE CYCLE VALIDATION
-- ============================================================

CREATE OR REPLACE FUNCTION validate_interface_inheritance()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    cycle_detected BOOLEAN;
BEGIN
    IF (
        SELECT project_id
        FROM interfaces
        WHERE interface_id = NEW.child_interface_id
    ) IS DISTINCT FROM (
        SELECT project_id
        FROM interfaces
        WHERE interface_id = NEW.parent_interface_id
    ) THEN
        RAISE EXCEPTION
            'Interface inheritance cannot cross projects.';
    END IF;

    WITH RECURSIVE ancestry(interface_id) AS (
        SELECT NEW.parent_interface_id

        UNION

        SELECT inheritance.parent_interface_id
        FROM interface_inheritance inheritance
        JOIN ancestry
          ON inheritance.child_interface_id = ancestry.interface_id
    )
    SELECT EXISTS (
        SELECT 1
        FROM ancestry
        WHERE interface_id = NEW.child_interface_id
    )
    INTO cycle_detected;

    IF cycle_detected THEN
        RAISE EXCEPTION
            'Circular interface inheritance is prohibited.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_interface_inheritance
BEFORE INSERT OR UPDATE
ON interface_inheritance
FOR EACH ROW
EXECUTE FUNCTION validate_interface_inheritance();

-- ============================================================
-- CONFIGURATION ELIGIBILITY VIEW
-- ============================================================

CREATE VIEW configuration_eligibility AS
SELECT
    configuration_id,
    project_id,
    strict,
    (
        NOT strict
        OR (
            strict_null_checks
            AND no_implicit_any
            AND strict_function_types
            AND strict_property_initialization
        )
    ) AS strict_configuration_valid,
    (
        root_directory <> output_directory
    ) AS directory_configuration_valid,
    declaration_enabled,
    source_map,
    target,
    module_system
FROM compiler_configurations;

-- ============================================================
-- MODULE DEPENDENCY REPORT
-- ============================================================

CREATE VIEW module_dependency_report AS
SELECT
    source.module_id,
    source.project_id,
    source.module_name AS source_module,
    target.module_name AS dependency_module,
    target.module_type AS dependency_type
FROM module_imports imports
JOIN modules source
    ON source.module_id = imports.source_module_id
JOIN modules target
    ON target.module_id = imports.target_module_id;

-- ============================================================
-- INTERFACE PROPERTY REPORT
-- ============================================================

CREATE VIEW interface_property_report AS
SELECT
    interfaces.interface_id,
    interfaces.project_id,
    interfaces.interface_name,
    properties.property_name,
    properties.property_type,
    properties.property_category,
    properties.is_optional,
    properties.is_readonly
FROM interfaces
JOIN interface_properties properties
    ON properties.interface_id = interfaces.interface_id;

-- ============================================================
-- VALIDATION SUMMARY
-- ============================================================

CREATE VIEW validation_summary AS
SELECT
    runs.run_id,
    projects.project_name,
    runs.status,
    runs.module_count,
    runs.error_count,
    runs.warning_count,
    runs.started_at,
    runs.completed_at
FROM validation_runs runs
JOIN projects
    ON projects.project_id = runs.project_id;

-- ============================================================
-- RECURSIVE DEPENDENCY REACHABILITY
-- ============================================================

CREATE OR REPLACE FUNCTION get_module_dependencies(
    requested_module BIGINT
)
RETURNS TABLE (
    module_id BIGINT,
    module_name VARCHAR(150),
    dependency_depth INTEGER
)
LANGUAGE sql
STABLE
AS $$
    WITH RECURSIVE dependency_tree AS (
        SELECT
            target.module_id,
            target.module_name,
            1 AS depth,
            ARRAY[requested_module, target.module_id]::BIGINT[] AS path
        FROM module_imports imports
        JOIN modules target
            ON target.module_id = imports.target_module_id
        WHERE imports.source_module_id = requested_module

        UNION ALL

        SELECT
            target.module_id,
            target.module_name,
            tree.depth + 1,
            tree.path || target.module_id
        FROM dependency_tree tree
        JOIN module_imports imports
            ON imports.source_module_id = tree.module_id
        JOIN modules target
            ON target.module_id = imports.target_module_id
        WHERE NOT target.module_id = ANY(tree.path)
    )
    SELECT
        dependency_tree.module_id,
        dependency_tree.module_name,
        MIN(dependency_tree.depth)::INTEGER
    FROM dependency_tree
    GROUP BY
        dependency_tree.module_id,
        dependency_tree.module_name
    ORDER BY MIN(dependency_tree.depth), dependency_tree.module_name;
$$;

-- ============================================================
-- PROJECT VALIDATION PROCEDURE
-- Records module counts and configuration failures.
-- ============================================================

CREATE OR REPLACE PROCEDURE validate_project(
    requested_project BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    new_run_id BIGINT;
    configuration_row RECORD;
    current_module_count INTEGER;
    current_errors INTEGER := 0;
    current_warnings INTEGER := 0;
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM projects
        WHERE project_id = requested_project
    ) THEN
        RAISE EXCEPTION
            'Project % does not exist.',
            requested_project;
    END IF;

    SELECT *
    INTO configuration_row
    FROM compiler_configurations
    WHERE project_id = requested_project;

    SELECT COUNT(*)::INTEGER
    INTO current_module_count
    FROM modules
    WHERE project_id = requested_project;

    INSERT INTO validation_runs (
        project_id,
        configuration_id,
        status,
        started_at,
        module_count
    )
    VALUES (
        requested_project,
        configuration_row.configuration_id,
        'running',
        CURRENT_TIMESTAMP,
        current_module_count
    )
    RETURNING run_id INTO new_run_id;

    IF configuration_row.configuration_id IS NULL THEN
        current_errors := current_errors + 1;

        INSERT INTO architecture_diagnostics (
            run_id,
            diagnostic_code,
            severity,
            message
        )
        VALUES (
            new_run_id,
            'CONFIG001',
            'error',
            'Project has no compiler configuration.'
        );

    ELSIF NOT EXISTS (
        SELECT 1
        FROM configuration_eligibility
        WHERE project_id = requested_project
          AND strict_configuration_valid
          AND directory_configuration_valid
    ) THEN
        current_errors := current_errors + 1;

        INSERT INTO architecture_diagnostics (
            run_id,
            diagnostic_code,
            severity,
            message
        )
        VALUES (
            new_run_id,
            'CONFIG002',
            'error',
            'Compiler configuration is not eligible.'
        );
    END IF;

    -- Detect module imports with unresolved symbols.
    SELECT COUNT(*)::INTEGER
    INTO current_errors
    FROM module_imports imports
    WHERE EXISTS (
        SELECT 1
        FROM modules source
        JOIN modules target
            ON target.module_id = imports.target_module_id
        WHERE source.module_id = imports.source_module_id
          AND source.project_id = requested_project
          AND NOT EXISTS (
              SELECT 1
              FROM module_exports exports
              WHERE exports.module_id = target.module_id
                AND exports.symbol_name = imports.imported_symbol
          )
          AND imports.imported_symbol IS NOT NULL
    );

    INSERT INTO architecture_diagnostics (
        run_id,
        diagnostic_code,
        severity,
        message
    )
    SELECT
        new_run_id,
        'MODULE001',
        'error',
        'Imported symbol is missing from its target module.'
    FROM module_imports imports
    JOIN modules source
        ON source.module_id = imports.source_module_id
    JOIN modules target
        ON target.module_id = imports.target_module_id
    WHERE source.project_id = requested_project
      AND imports.imported_symbol IS NOT NULL
      AND NOT EXISTS (
          SELECT 1
          FROM module_exports exports
          WHERE exports.module_id = target.module_id
            AND exports.symbol_name = imports.imported_symbol
      );

    current_warnings := current_warnings + (
        SELECT COUNT(*)::INTEGER
        FROM modules
        WHERE project_id = requested_project
          AND module_type = 'declaration'
          AND NOT EXISTS (
              SELECT 1
              FROM module_exports
              WHERE module_id = modules.module_id
          )
    );

    INSERT INTO architecture_diagnostics (
        run_id,
        diagnostic_code,
        severity,
        message
    )
    SELECT
        new_run_id,
        'DECL001',
        'warning',
        'Declaration module has no registered exports.'
    FROM modules
    WHERE project_id = requested_project
      AND module_type = 'declaration'
      AND NOT EXISTS (
          SELECT 1
          FROM module_exports
          WHERE module_id = modules.module_id
      );

    SELECT COUNT(*)::INTEGER
    INTO current_errors
    FROM architecture_diagnostics
    WHERE run_id = new_run_id
      AND severity = 'error';

    UPDATE validation_runs
    SET
        status = CASE
            WHEN current_errors > 0 THEN 'failed'
            ELSE 'passed'
        END,
        error_count = current_errors,
        warning_count = current_warnings,
        completed_at = CURRENT_TIMESTAMP
    WHERE run_id = new_run_id;

END;
$$;

-- ============================================================
-- SAMPLE PROJECT
-- ============================================================

INSERT INTO projects (
    project_name,
    description,
    typescript_version
)
VALUES (
    'Enterprise User Platform',
    'Modular TypeScript application with strict contracts and layered architecture.',
    '5.9'
);

INSERT INTO compiler_configurations (
    project_id,
    target,
    module_system,
    module_resolution,
    strict,
    strict_null_checks,
    no_implicit_any,
    strict_function_types,
    strict_property_initialization,
    no_implicit_override,
    no_unused_locals,
    no_unused_parameters,
    no_unchecked_indexed_access,
    exact_optional_property_types,
    declaration_enabled,
    declaration_map,
    source_map,
    root_directory,
    output_directory,
    path_aliases
)
SELECT
    project_id,
    'ES2022',
    'NodeNext',
    'NodeNext',
    TRUE,
    TRUE,
    TRUE,
    TRUE,
    TRUE,
    TRUE,
    TRUE,
    TRUE,
    TRUE,
    TRUE,
    TRUE,
    TRUE,
    TRUE,
    'src',
    'dist',
    '{
        "@domain/*": ["src/domain/*"],
        "@services/*": ["src/services/*"],
        "@infrastructure/*": ["src/infrastructure/*"]
    }'::jsonb
FROM projects
WHERE project_name = 'Enterprise User Platform';

-- ============================================================
-- SOURCE FILE RECORDS
-- ============================================================

INSERT INTO source_files (
    project_id,
    file_path,
    extension,
    is_declaration,
    is_entry_point
)
SELECT
    project_id,
    records.file_path,
    records.extension,
    records.is_declaration,
    records.is_entry_point
FROM projects
CROSS JOIN (
    VALUES
        ('src/domain/user.ts', '.ts', FALSE, FALSE),
        ('src/domain/contracts.d.ts', '.d.ts', TRUE, FALSE),
        ('src/infrastructure/user-repository.ts', '.ts', FALSE, FALSE),
        ('src/services/user-service.ts', '.ts', FALSE, FALSE),
        ('src/api/server.ts', '.ts', FALSE, TRUE)
) AS records(
    file_path,
    extension,
    is_declaration,
    is_entry_point
)
WHERE projects.project_name = 'Enterprise User Platform';

-- ============================================================
-- INTERFACE RECORDS
-- ============================================================

INSERT INTO interfaces (
    project_id,
    file_id,
    interface_name,
    is_exported,
    is_declaration_only
)
SELECT
    project_id,
    file_id,
    records.interface_name,
    TRUE,
    records.declaration_only
FROM projects
JOIN source_files USING (project_id)
JOIN (
    VALUES
        ('src/domain/user.ts', 'Entity', FALSE),
        ('src/domain/user.ts', 'User', FALSE),
        ('src/domain/user.ts', 'UserRepository', FALSE),
        ('src/domain/contracts.d.ts', 'ExternalIdentity', TRUE)
) AS records(file_path, interface_name, declaration_only)
ON source_files.file_path = records.file_path
WHERE projects.project_name = 'Enterprise User Platform';

-- ============================================================
-- INTERFACE INHERITANCE
-- ============================================================

INSERT INTO interface_inheritance (
    child_interface_id,
    parent_interface_id
)
SELECT
    child.interface_id,
    parent.interface_id
FROM interfaces child
JOIN interfaces parent
    ON parent.project_id = child.project_id
WHERE child.interface_name = 'User'
  AND parent.interface_name = 'Entity';

-- ============================================================
-- INTERFACE PROPERTIES
-- ============================================================

INSERT INTO interface_properties (
    interface_id,
    property_name,
    property_type,
    property_category,
    is_optional,
    is_readonly
)
SELECT
    interfaces.interface_id,
    records.property_name,
    records.property_type,
    records.property_category::property_kind,
    records.is_optional,
    records.is_readonly
FROM interfaces
JOIN (
    VALUES
        ('Entity', 'id', 'string', 'primitive', FALSE, TRUE),
        ('User', 'email', 'string', 'primitive', FALSE, FALSE),
        ('User', 'displayName', 'string', 'primitive', FALSE, FALSE),
        ('User', 'phone', 'string', 'primitive', TRUE, FALSE),
        ('UserRepository', 'findById', '(id: string) => Promise<User | null>', 'function', FALSE, FALSE),
        ('UserRepository', 'save', '(user: User) => Promise<void>', 'function', FALSE, FALSE),
        ('ExternalIdentity', 'providerId', 'string', 'primitive', FALSE, FALSE)
) AS records(
    interface_name,
    property_name,
    property_type,
    property_category,
    is_optional,
    is_readonly
)
ON interfaces.interface_name = records.interface_name
WHERE interfaces.project_id = (
    SELECT project_id
    FROM projects
    WHERE project_name = 'Enterprise User Platform'
);

-- ============================================================
-- MODULE RECORDS
-- ============================================================

INSERT INTO modules (
    project_id,
    file_id,
    module_name,
    module_type,
    is_entry_point
)
SELECT
    project_id,
    file_id,
    records.module_name,
    records.module_type::module_kind,
    records.is_entry_point
FROM projects
JOIN source_files USING (project_id)
JOIN (
    VALUES
        ('src/domain/user.ts', 'domain', 'esm', FALSE),
        ('src/domain/contracts.d.ts', 'declarations', 'declaration', FALSE),
        ('src/infrastructure/user-repository.ts', 'infrastructure', 'esm', FALSE),
        ('src/services/user-service.ts', 'services', 'esm', FALSE),
        ('src/api/server.ts', 'api', 'esm', TRUE)
) AS records(
    file_path,
    module_name,
    module_type,
    is_entry_point
)
ON source_files.file_path = records.file_path
WHERE projects.project_name = 'Enterprise User Platform';

-- ============================================================
-- MODULE EXPORTS
-- ============================================================

INSERT INTO module_exports (
    module_id,
    symbol_name,
    export_kind
)
SELECT
    modules.module_id,
    records.symbol_name,
    records.export_kind
FROM modules
JOIN (
    VALUES
        ('domain', 'Entity', 'type'),
        ('domain', 'User', 'type'),
        ('domain', 'UserRepository', 'type'),
        ('declarations', 'ExternalIdentity', 'type'),
        ('infrastructure', 'PostgresUserRepository', 'named'),
        ('services', 'UserService', 'named'),
        ('api', 'startServer', 'named')
) AS records(module_name, symbol_name, export_kind)
ON modules.module_name = records.module_name;

-- ============================================================
-- MODULE IMPORTS
-- ============================================================

INSERT INTO module_imports (
    source_module_id,
    target_module_id,
    imported_symbol,
    import_kind
)
SELECT
    source.module_id,
    target.module_id,
    records.imported_symbol,
    records.import_kind
FROM (
    VALUES
        ('infrastructure', 'domain', 'UserRepository', 'type'),
        ('services', 'domain', 'User', 'type'),
        ('services', 'infrastructure', 'PostgresUserRepository', 'named'),
        ('api', 'services', 'UserService', 'named')
) AS records(
    source_name,
    target_name,
    imported_symbol,
    import_kind
)
JOIN modules source
    ON source.module_name = records.source_name
JOIN modules target
    ON target.module_name = records.target_name;

-- ============================================================
-- MODULE INTERFACE ASSOCIATIONS
-- ============================================================

INSERT INTO module_interfaces (
    module_id,
    interface_id
)
SELECT
    modules.module_id,
    interfaces.interface_id
FROM (
    VALUES
        ('domain', 'User'),
        ('domain', 'UserRepository'),
        ('infrastructure', 'UserRepository'),
        ('services', 'User')
) AS records(module_name, interface_name)
JOIN modules
    ON modules.module_name = records.module_name
JOIN interfaces
    ON interfaces.interface_name = records.interface_name
   AND interfaces.project_id = modules.project_id;

-- ============================================================
-- SAMPLE VALIDATION
-- ============================================================

CALL validate_project(
    (
        SELECT project_id
        FROM projects
        WHERE project_name = 'Enterprise User Platform'
    )
);

-- ============================================================
-- RETRIEVAL QUERIES
-- ============================================================

-- Project compiler configuration.
SELECT
    projects.project_name,
    configuration.target,
    configuration.module_system,
    configuration.module_resolution,
    configuration.strict
FROM projects
JOIN compiler_configurations configuration
    USING (project_id);

-- Module and export inventory.
SELECT
    modules.module_name,
    modules.module_type,
    exports.symbol_name,
    exports.export_kind
FROM modules
LEFT JOIN module_exports exports
    USING (module_id)
ORDER BY modules.module_name, exports.symbol_name;

-- Interface contracts.
SELECT *
FROM interface_property_report
ORDER BY interface_name, property_name;

-- Module dependencies.
SELECT *
FROM module_dependency_report
ORDER BY source_module, dependency_module;

-- ============================================================
-- CTE: DEPENDENCY DEPTH
-- ============================================================

WITH RECURSIVE dependency_tree AS (
    SELECT
        source.module_id,
        source.module_name,
        0 AS depth,
        ARRAY[source.module_id]::BIGINT[] AS path
    FROM modules source
    WHERE source.is_entry_point = TRUE

    UNION ALL

    SELECT
        target.module_id,
        target.module_name,
        tree.depth + 1,
        tree.path || target.module_id
    FROM dependency_tree tree
    JOIN module_imports imports
        ON imports.source_module_id = tree.module_id
    JOIN modules target
        ON target.module_id = imports.target_module_id
    WHERE NOT target.module_id = ANY(tree.path)
)
SELECT
    module_name,
    MIN(depth) AS minimum_dependency_depth
FROM dependency_tree
GROUP BY module_name
ORDER BY minimum_dependency_depth, module_name;

-- ============================================================
-- AGGREGATION
-- ============================================================

SELECT
    modules.project_id,
    COUNT(DISTINCT modules.module_id) AS module_count,
    COUNT(DISTINCT imports.import_id) AS import_count,
    COUNT(DISTINCT exports.export_id) AS export_count
FROM modules
LEFT JOIN module_imports imports
    ON imports.source_module_id = modules.module_id
LEFT JOIN module_exports exports
    ON exports.module_id = modules.module_id
GROUP BY modules.project_id;

-- ============================================================
-- DECLARATION FILE REPORT
-- ============================================================

SELECT
    modules.module_name,
    files.file_path,
    COUNT(exports.export_id) AS exported_symbols
FROM modules
JOIN source_files files
    USING (file_id)
LEFT JOIN module_exports exports
    USING (module_id)
WHERE modules.module_type = 'declaration'
GROUP BY
    modules.module_name,
    files.file_path;

-- ============================================================
-- ELIGIBILITY DETERMINATION
-- ============================================================

SELECT
    project_name,
    strict,
    strict_configuration_valid,
    directory_configuration_valid,
    (
        strict_configuration_valid
        AND directory_configuration_valid
    ) AS compiler_eligible
FROM configuration_eligibility
JOIN projects USING (project_id);

-- ============================================================
-- VALIDATION REPORT
-- ============================================================

SELECT *
FROM validation_summary
ORDER BY started_at DESC;

SELECT
    diagnostics.diagnostic_code,
    diagnostics.severity,
    diagnostics.message,
    diagnostics.created_at
FROM architecture_diagnostics diagnostics
ORDER BY diagnostics.created_at DESC;

-- ============================================================
-- FAILURE CASE: INVALID STRICT CONFIGURATION
--
-- Execute separately to observe the expected trigger error.
-- ============================================================

-- UPDATE compiler_configurations
-- SET strict_null_checks = FALSE
-- WHERE project_id = (
--     SELECT project_id
--     FROM projects
--     WHERE project_name = 'Enterprise User Platform'
-- );

-- ============================================================
-- FAILURE CASE: MISSING EXPORTED SYMBOL
--
-- The import trigger rejects this insertion.
-- Execute separately to observe the expected trigger error.
-- ============================================================

-- INSERT INTO module_imports (
--     source_module_id,
--     target_module_id,
--     imported_symbol,
--     import_kind
-- )
-- SELECT
--     source.module_id,
--     target.module_id,
--     'MissingRepository',
--     'named'
-- FROM modules source
-- CROSS JOIN modules target
-- WHERE source.module_name = 'services'
--   AND target.module_name = 'domain';

-- ============================================================
-- FAILURE CASE: CIRCULAR INTERFACE INHERITANCE
--
-- Execute separately to observe the expected trigger error.
-- ============================================================

-- INSERT INTO interface_inheritance (
--     child_interface_id,
--     parent_interface_id
-- )
-- SELECT
--     parent.interface_id,
--     child.interface_id
-- FROM interfaces child
-- JOIN interfaces parent
--   ON parent.project_id = child.project_id
-- WHERE child.interface_name = 'User'
--   AND parent.interface_name = 'Entity';

-- ============================================================
-- TRANSACTION DEMONSTRATION
-- ============================================================

SAVEPOINT before_optional_configuration_change;

UPDATE compiler_configurations
SET
    no_unused_locals = TRUE,
    no_unused_parameters = TRUE
WHERE project_id = (
    SELECT project_id
    FROM projects
    WHERE project_name = 'Enterprise User Platform'
);

RELEASE SAVEPOINT before_optional_configuration_change;

COMMIT;
