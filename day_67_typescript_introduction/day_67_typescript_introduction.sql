-- ============================================================
-- TypeScript Introduction
-- Why TypeScript, Type Annotations, Primitive Types,
-- and Type Inference
--
-- PostgreSQL model of a typed configuration and validation
-- registry for application environments.
--
-- Compatible with PostgreSQL 14+.
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS typescript_lab;

SET search_path TO typescript_lab, public;

-- ------------------------------------------------------------
-- 1. Primitive type categories
-- ------------------------------------------------------------

CREATE TYPE primitive_kind AS ENUM (
    'STRING',
    'NUMBER',
    'BOOLEAN',
    'NULL'
);

CREATE TYPE validation_status AS ENUM (
    'VALID',
    'INVALID',
    'WARNING'
);

CREATE TYPE environment_kind AS ENUM (
    'DEVELOPMENT',
    'TESTING',
    'PRODUCTION'
);

CREATE TYPE configuration_state AS ENUM (
    'DRAFT',
    'VALIDATED',
    'ACTIVE',
    'REJECTED',
    'ARCHIVED'
);

-- ------------------------------------------------------------
-- 2. Application registry
-- ------------------------------------------------------------

CREATE TABLE applications (
    application_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    application_name VARCHAR(100) NOT NULL UNIQUE,

    owner_name VARCHAR(120) NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT application_name_not_empty
        CHECK (length(trim(application_name)) > 0),

    CONSTRAINT owner_name_not_empty
        CHECK (length(trim(owner_name)) > 0)
);

-- ------------------------------------------------------------
-- 3. Environment configuration
-- ------------------------------------------------------------

CREATE TABLE environment_configurations (
    configuration_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    application_id BIGINT NOT NULL
        REFERENCES applications(application_id)
        ON DELETE RESTRICT,

    environment environment_kind NOT NULL,

    port INTEGER NOT NULL,

    debug_enabled BOOLEAN NOT NULL DEFAULT FALSE,

    state configuration_state NOT NULL DEFAULT 'DRAFT',

    version_number INTEGER NOT NULL DEFAULT 1,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_port
        CHECK (port BETWEEN 1 AND 65535),

    CONSTRAINT valid_version
        CHECK (version_number > 0),

    CONSTRAINT unique_application_environment_version
        UNIQUE (
            application_id,
            environment,
            version_number
        )
);

CREATE INDEX idx_config_application_environment
ON environment_configurations (
    application_id,
    environment,
    state
);

-- ------------------------------------------------------------
-- 4. Typed configuration properties
--
-- PostgreSQL stores values as text, but primitive_kind records
-- the declared type. A trigger enforces consistency.
-- ------------------------------------------------------------

CREATE TABLE configuration_properties (
    property_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    configuration_id BIGINT NOT NULL
        REFERENCES environment_configurations(configuration_id)
        ON DELETE CASCADE,

    property_name VARCHAR(100) NOT NULL,

    declared_type primitive_kind NOT NULL,

    string_value TEXT,

    number_value NUMERIC(20, 6),

    boolean_value BOOLEAN,

    is_nullable BOOLEAN NOT NULL DEFAULT FALSE,

    inferred_type primitive_kind,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_configuration_property
        UNIQUE (configuration_id, property_name),

    CONSTRAINT property_name_not_empty
        CHECK (length(trim(property_name)) > 0),

    CONSTRAINT exactly_one_typed_value
        CHECK (
            (
                declared_type = 'STRING'
                AND string_value IS NOT NULL
                AND number_value IS NULL
                AND boolean_value IS NULL
            )
            OR
            (
                declared_type = 'NUMBER'
                AND string_value IS NULL
                AND number_value IS NOT NULL
                AND boolean_value IS NULL
            )
            OR
            (
                declared_type = 'BOOLEAN'
                AND string_value IS NULL
                AND number_value IS NULL
                AND boolean_value IS NOT NULL
            )
            OR
            (
                declared_type = 'NULL'
                AND string_value IS NULL
                AND number_value IS NULL
                AND boolean_value IS NULL
                AND is_nullable = TRUE
            )
        )
);

CREATE INDEX idx_properties_configuration
ON configuration_properties(configuration_id);

CREATE INDEX idx_properties_declared_type
ON configuration_properties(declared_type);

-- ------------------------------------------------------------
-- 5. Validation rules
-- ------------------------------------------------------------

CREATE TABLE validation_rules (
    rule_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    property_name VARCHAR(100) NOT NULL,

    expected_type primitive_kind NOT NULL,

    required BOOLEAN NOT NULL DEFAULT TRUE,

    minimum_number NUMERIC(20, 6),

    maximum_number NUMERIC(20, 6),

    CONSTRAINT valid_numeric_range
        CHECK (
            minimum_number IS NULL
            OR maximum_number IS NULL
            OR minimum_number <= maximum_number
        )
);

INSERT INTO validation_rules (
    property_name,
    expected_type,
    required,
    minimum_number,
    maximum_number
)
VALUES
    ('applicationName', 'STRING', TRUE, NULL, NULL),
    ('port', 'NUMBER', TRUE, 1, 65535),
    ('debug', 'BOOLEAN', TRUE, NULL, NULL),
    ('supportEmail', 'STRING', FALSE, NULL, NULL),
    ('sessionTimeout', 'NUMBER', TRUE, 60, 86400);

-- ------------------------------------------------------------
-- 6. Validation audit log
-- ------------------------------------------------------------

CREATE TABLE validation_audit (
    audit_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    configuration_id BIGINT NOT NULL
        REFERENCES environment_configurations(configuration_id)
        ON DELETE CASCADE,

    property_name VARCHAR(100) NOT NULL,

    expected_type primitive_kind NOT NULL,

    actual_type primitive_kind NOT NULL,

    result validation_status NOT NULL,

    message TEXT NOT NULL,

    checked_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_validation_audit_configuration
ON validation_audit(configuration_id, result);

-- ------------------------------------------------------------
-- 7. Infer primitive type
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION infer_primitive_type(
    p_string TEXT,
    p_number NUMERIC,
    p_boolean BOOLEAN,
    p_is_null BOOLEAN
)
RETURNS primitive_kind
LANGUAGE plpgsql
IMMUTABLE
AS $$
BEGIN
    IF p_is_null THEN
        RETURN 'NULL';
    ELSIF p_string IS NOT NULL THEN
        RETURN 'STRING';
    ELSIF p_number IS NOT NULL THEN
        RETURN 'NUMBER';
    ELSIF p_boolean IS NOT NULL THEN
        RETURN 'BOOLEAN';
    END IF;

    RETURN 'NULL';
END;
$$;

-- ------------------------------------------------------------
-- 8. Property integrity trigger
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION enforce_property_type()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.inferred_type := infer_primitive_type(
        NEW.string_value,
        NEW.number_value,
        NEW.boolean_value,
        NEW.declared_type = 'NULL'
    );

    IF NEW.declared_type <> NEW.inferred_type THEN
        RAISE EXCEPTION
            'Declared type % does not match inferred type %',
            NEW.declared_type,
            NEW.inferred_type;
    END IF;

    IF NEW.declared_type = 'STRING'
       AND length(trim(NEW.string_value)) = 0 THEN
        RAISE EXCEPTION
            'String properties cannot contain only whitespace';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_enforce_property_type
BEFORE INSERT OR UPDATE
ON configuration_properties
FOR EACH ROW
EXECUTE FUNCTION enforce_property_type();

-- ------------------------------------------------------------
-- 9. Prevent direct modification of active configurations
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION protect_active_configuration()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.state = 'ACTIVE' THEN
        RAISE EXCEPTION
            'Active configurations cannot be modified directly';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_protect_active_configuration
BEFORE UPDATE OR DELETE
ON environment_configurations
FOR EACH ROW
EXECUTE FUNCTION protect_active_configuration();

-- ------------------------------------------------------------
-- 10. Configuration validation function
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_configuration(
    p_configuration_id BIGINT
)
RETURNS TABLE (
    property_name TEXT,
    expected_type primitive_kind,
    actual_type primitive_kind,
    result validation_status,
    message TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    property_record RECORD;
    rule_record RECORD;
    numeric_value NUMERIC;
    validation_result validation_status;
    validation_message TEXT;
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM environment_configurations
        WHERE configuration_id = p_configuration_id
    ) THEN
        RAISE EXCEPTION
            'Configuration % does not exist',
            p_configuration_id;
    END IF;

    FOR rule_record IN
        SELECT *
        FROM validation_rules
        ORDER BY rule_id
    LOOP
        SELECT *
        INTO property_record
        FROM configuration_properties
        WHERE configuration_id = p_configuration_id
          AND configuration_properties.property_name =
              rule_record.property_name;

        IF NOT FOUND THEN
            IF rule_record.required THEN
                validation_result := 'INVALID';
                validation_message := 'Required property is missing';
            ELSE
                validation_result := 'WARNING';
                validation_message := 'Optional property is missing';
            END IF;

            property_name := rule_record.property_name;
            expected_type := rule_record.expected_type;
            actual_type := 'NULL';
            result := validation_result;
            message := validation_message;

        ELSE
            property_name := rule_record.property_name;
            expected_type := rule_record.expected_type;
            actual_type := property_record.inferred_type;

            validation_result := 'VALID';
            validation_message := 'Type matches declaration';

            IF property_record.declared_type <>
                rule_record.expected_type THEN

                validation_result := 'INVALID';
                validation_message := 'Primitive type mismatch';

            ELSIF rule_record.expected_type = 'NUMBER' THEN

                numeric_value := property_record.number_value;

                IF rule_record.minimum_number IS NOT NULL
                   AND numeric_value < rule_record.minimum_number THEN

                    validation_result := 'INVALID';
                    validation_message := 'Value below minimum';

                ELSIF rule_record.maximum_number IS NOT NULL
                   AND numeric_value > rule_record.maximum_number THEN

                    validation_result := 'INVALID';
                    validation_message := 'Value above maximum';
                END IF;
            END IF;

            result := validation_result;
            message := validation_message;
        END IF;

        INSERT INTO validation_audit (
            configuration_id,
            property_name,
            expected_type,
            actual_type,
            result,
            message
        )
        VALUES (
            p_configuration_id,
            property_name,
            expected_type,
            actual_type,
            result,
            message
        );

        RETURN NEXT;
    END LOOP;
END;
$$;

-- ------------------------------------------------------------
-- 11. Configuration activation procedure
-- ------------------------------------------------------------

CREATE OR REPLACE PROCEDURE activate_configuration(
    p_configuration_id BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    invalid_count BIGINT;
BEGIN
    -- Lock the configuration while checking and activating it.
    PERFORM 1
    FROM environment_configurations
    WHERE configuration_id = p_configuration_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Configuration does not exist';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM environment_configurations
        WHERE configuration_id = p_configuration_id
          AND state = 'ACTIVE'
    ) THEN
        RAISE EXCEPTION
            'Configuration is already active';
    END IF;

    DELETE FROM validation_audit
    WHERE configuration_id = p_configuration_id;

    SELECT COUNT(*)
    INTO invalid_count
    FROM validate_configuration(p_configuration_id)
    WHERE result = 'INVALID';

    IF invalid_count > 0 THEN
        UPDATE environment_configurations
        SET state = 'REJECTED'
        WHERE configuration_id = p_configuration_id;

        RAISE EXCEPTION
            'Activation rejected: % validation errors',
            invalid_count;
    END IF;

    UPDATE environment_configurations
    SET state = 'ACTIVE'
    WHERE configuration_id = p_configuration_id;
END;
$$;

-- ------------------------------------------------------------
-- 12. Reporting view
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW configuration_validation_report AS
SELECT
    a.application_name,
    c.configuration_id,
    c.environment,
    c.port,
    c.debug_enabled,
    c.state,
    COUNT(DISTINCT p.property_id) AS property_count,
    COUNT(audit.audit_id) AS validation_count,
    COUNT(audit.audit_id) FILTER (
        WHERE audit.result = 'VALID'
    ) AS valid_count,
    COUNT(audit.audit_id) FILTER (
        WHERE audit.result = 'INVALID'
    ) AS invalid_count,
    COUNT(audit.audit_id) FILTER (
        WHERE audit.result = 'WARNING'
    ) AS warning_count
FROM environment_configurations c
JOIN applications a
    ON a.application_id = c.application_id
LEFT JOIN configuration_properties p
    ON p.configuration_id = c.configuration_id
LEFT JOIN validation_audit audit
    ON audit.configuration_id = c.configuration_id
GROUP BY
    a.application_name,
    c.configuration_id,
    c.environment,
    c.port,
    c.debug_enabled,
    c.state;

-- ------------------------------------------------------------
-- 13. Sample applications
-- ------------------------------------------------------------

INSERT INTO applications (
    application_name,
    owner_name
)
VALUES
    ('EmployeeRegistry', 'Engineering'),
    ('ResearchPortal', 'Research');

INSERT INTO environment_configurations (
    application_id,
    environment,
    port,
    debug_enabled,
    state
)
VALUES
    (
        1,
        'DEVELOPMENT',
        8080,
        TRUE,
        'DRAFT'
    ),
    (
        1,
        'PRODUCTION',
        8443,
        FALSE,
        'DRAFT'
    ),
    (
        2,
        'TESTING',
        9000,
        TRUE,
        'DRAFT'
    );

-- ------------------------------------------------------------
-- 14. Typed configuration properties
-- ------------------------------------------------------------

INSERT INTO configuration_properties (
    configuration_id,
    property_name,
    declared_type,
    string_value
)
VALUES
    (1, 'applicationName', 'STRING', 'EmployeeRegistry'),
    (1, 'supportEmail', 'STRING', 'support@example.com');

INSERT INTO configuration_properties (
    configuration_id,
    property_name,
    declared_type,
    number_value
)
VALUES
    (1, 'port', 'NUMBER', 8080),
    (1, 'sessionTimeout', 'NUMBER', 3600);

INSERT INTO configuration_properties (
    configuration_id,
    property_name,
    declared_type,
    boolean_value
)
VALUES
    (1, 'debug', 'BOOLEAN', TRUE);

INSERT INTO configuration_properties (
    configuration_id,
    property_name,
    declared_type,
    string_value
)
VALUES
    (2, 'applicationName', 'STRING', 'EmployeeRegistry');

INSERT INTO configuration_properties (
    configuration_id,
    property_name,
    declared_type,
    number_value
)
VALUES
    (2, 'port', 'NUMBER', 8443),
    (2, 'sessionTimeout', 'NUMBER', 7200);

INSERT INTO configuration_properties (
    configuration_id,
    property_name,
    declared_type,
    boolean_value
)
VALUES
    (2, 'debug', 'BOOLEAN', FALSE);

INSERT INTO configuration_properties (
    configuration_id,
    property_name,
    declared_type,
    string_value
)
VALUES
    (3, 'applicationName', 'STRING', 'ResearchPortal');

INSERT INTO configuration_properties (
    configuration_id,
    property_name,
    declared_type,
    number_value
)
VALUES
    (3, 'port', 'NUMBER', 9000),
    (3, 'sessionTimeout', 'NUMBER', 30);

INSERT INTO configuration_properties (
    configuration_id,
    property_name,
    declared_type,
    boolean_value
)
VALUES
    (3, 'debug', 'BOOLEAN', TRUE);

-- ------------------------------------------------------------
-- 15. Retrieve configuration properties
-- ------------------------------------------------------------

SELECT
    c.configuration_id,
    c.environment,
    p.property_name,
    p.declared_type,
    p.inferred_type,
    COALESCE(
        p.string_value,
        p.number_value::TEXT,
        p.boolean_value::TEXT,
        'NULL'
    ) AS property_value
FROM environment_configurations c
JOIN configuration_properties p
    ON p.configuration_id = c.configuration_id
ORDER BY
    c.configuration_id,
    p.property_name;

-- ------------------------------------------------------------
-- 16. Demonstrate successful validation
-- ------------------------------------------------------------

SELECT *
FROM validate_configuration(1);

-- ------------------------------------------------------------
-- 17. Demonstrate invalid configuration
--
-- The testing configuration has sessionTimeout = 30,
-- while the required minimum is 60.
-- ------------------------------------------------------------

SELECT *
FROM validate_configuration(3);

-- ------------------------------------------------------------
-- 18. Primitive type aggregation
-- ------------------------------------------------------------

SELECT
    declared_type,
    COUNT(*) AS property_count
FROM configuration_properties
GROUP BY declared_type
ORDER BY declared_type;

-- ------------------------------------------------------------
-- 19. Configuration reporting
-- ------------------------------------------------------------

SELECT *
FROM configuration_validation_report
ORDER BY configuration_id;

-- ------------------------------------------------------------
-- 20. CTE-based validation analysis
-- ------------------------------------------------------------

WITH property_analysis AS (
    SELECT
        configuration_id,
        declared_type,
        COUNT(*) AS total_properties
    FROM configuration_properties
    GROUP BY
        configuration_id,
        declared_type
),
configuration_analysis AS (
    SELECT
        configuration_id,
        SUM(total_properties) AS total_properties
    FROM property_analysis
    GROUP BY configuration_id
)
SELECT
    configuration_id,
    total_properties
FROM configuration_analysis
ORDER BY configuration_id;

-- ------------------------------------------------------------
-- 21. Transactional activation of valid configuration
-- ------------------------------------------------------------

SAVEPOINT valid_activation;

CALL activate_configuration(1);

RELEASE SAVEPOINT valid_activation;

-- ------------------------------------------------------------
-- 22. Demonstrate failed activation without aborting script
--
-- The exception is caught in a PL/pgSQL block.
-- The rejected configuration remains available for inspection.
-- ------------------------------------------------------------

DO $$
BEGIN
    BEGIN
        CALL activate_configuration(3);
    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE
                'Expected activation failure: %',
                SQLERRM;
    END;
END;
$$;

-- ------------------------------------------------------------
-- 23. Inspect final workflow state
-- ------------------------------------------------------------

SELECT
    application_id,
    environment,
    port,
    state,
    version_number
FROM environment_configurations
ORDER BY configuration_id;

SELECT
    property_name,
    expected_type,
    actual_type,
    result,
    message
FROM validation_audit
WHERE configuration_id = 3
ORDER BY audit_id;

COMMIT;
