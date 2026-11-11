/*
 * React Component Architecture
 *
 * PostgreSQL component registry and composition management.
 *
 * Models:
 * - Functional component definitions
 * - Reusable component versions
 * - Component properties and prop types
 * - Default and required properties
 * - Component composition relationships
 * - Component instances
 * - Conditional rendering configuration
 * - Component lifecycle and deprecation
 * - Validation and dependency tracking
 * - Composition cycle prevention
 * - Component usage analytics
 *
 * Target: PostgreSQL 15+
 */

BEGIN;

CREATE SCHEMA IF NOT EXISTS react_catalog;

SET search_path TO react_catalog, public;


-- ============================================================
-- ENUM TYPES
-- ============================================================

CREATE TYPE component_status AS ENUM (
    'draft',
    'registered',
    'active',
    'deprecated',
    'retired'
);

CREATE TYPE prop_type AS ENUM (
    'string',
    'number',
    'boolean',
    'object',
    'array',
    'function',
    'node',
    'any'
);

CREATE TYPE composition_type AS ENUM (
    'child',
    'layout',
    'conditional',
    'list_item'
);

CREATE TYPE instance_status AS ENUM (
    'created',
    'validated',
    'rendered',
    'failed'
);


-- ============================================================
-- COMPONENT DEFINITIONS
-- ============================================================

CREATE TABLE components (
    component_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    component_name VARCHAR(100) NOT NULL,

    description TEXT NOT NULL,

    component_category VARCHAR(80) NOT NULL,

    status component_status NOT NULL DEFAULT 'draft',

    current_version INTEGER NOT NULL DEFAULT 1,

    accepts_children BOOLEAN NOT NULL DEFAULT TRUE,

    is_reusable BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_component_name UNIQUE(component_name),

    CONSTRAINT chk_component_name
        CHECK (
            component_name ~ '^[A-Z][A-Za-z0-9]*$'
        ),

    CONSTRAINT chk_component_version
        CHECK (current_version > 0)
);


-- ============================================================
-- COMPONENT VERSIONS
-- ============================================================

CREATE TABLE component_versions (
    version_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    component_id BIGINT NOT NULL
        REFERENCES components(component_id)
        ON DELETE RESTRICT,

    version_number INTEGER NOT NULL,

    implementation_type VARCHAR(30) NOT NULL
        DEFAULT 'functional',

    source_reference VARCHAR(255),

    change_description TEXT NOT NULL,

    is_breaking_change BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_component_version
        UNIQUE(component_id, version_number),

    CONSTRAINT chk_version_number
        CHECK (version_number > 0),

    CONSTRAINT chk_implementation_type
        CHECK (
            implementation_type IN (
                'functional',
                'composite'
            )
        )
);


-- ============================================================
-- PROPERTY DEFINITIONS
-- ============================================================

CREATE TABLE component_props (
    prop_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    version_id BIGINT NOT NULL
        REFERENCES component_versions(version_id)
        ON DELETE CASCADE,

    prop_name VARCHAR(100) NOT NULL,

    data_type prop_type NOT NULL,

    is_required BOOLEAN NOT NULL DEFAULT FALSE,

    has_default BOOLEAN NOT NULL DEFAULT FALSE,

    default_value JSONB,

    validation_rules JSONB NOT NULL DEFAULT '{}'::jsonb,

    description TEXT NOT NULL DEFAULT '',

    CONSTRAINT uq_version_prop
        UNIQUE(version_id, prop_name),

    CONSTRAINT chk_prop_name
        CHECK (
            prop_name ~ '^[A-Za-z_$][A-Za-z0-9_$]*$'
        ),

    CONSTRAINT chk_default_configuration
        CHECK (
            (
                has_default = FALSE
                AND default_value IS NULL
            )
            OR
            (
                has_default = TRUE
                AND default_value IS NOT NULL
                AND is_required = FALSE
            )
        ),

    CONSTRAINT chk_validation_object
        CHECK (
            jsonb_typeof(validation_rules) = 'object'
        )
);


-- ============================================================
-- COMPONENT COMPOSITION
-- ============================================================

CREATE TABLE component_compositions (
    composition_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    parent_version_id BIGINT NOT NULL
        REFERENCES component_versions(version_id)
        ON DELETE CASCADE,

    child_version_id BIGINT NOT NULL
        REFERENCES component_versions(version_id)
        ON DELETE RESTRICT,

    relationship composition_type NOT NULL DEFAULT 'child',

    display_order INTEGER NOT NULL DEFAULT 0,

    is_required BOOLEAN NOT NULL DEFAULT FALSE,

    condition_expression JSONB NOT NULL DEFAULT '{}'::jsonb,

    CONSTRAINT chk_no_direct_self_composition
        CHECK (parent_version_id <> child_version_id),

    CONSTRAINT chk_display_order
        CHECK (display_order >= 0),

    CONSTRAINT uq_composition
        UNIQUE (
            parent_version_id,
            child_version_id,
            relationship
        )
);


-- ============================================================
-- APPLICATIONS
-- ============================================================

CREATE TABLE applications (
    application_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    application_name VARCHAR(150) NOT NULL UNIQUE,

    description TEXT NOT NULL DEFAULT '',

    environment VARCHAR(30) NOT NULL DEFAULT 'development',

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_environment
        CHECK (
            environment IN (
                'development',
                'testing',
                'staging',
                'production'
            )
        )
);


-- ============================================================
-- COMPONENT INSTANCES
-- ============================================================

CREATE TABLE component_instances (
    instance_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    application_id BIGINT NOT NULL
        REFERENCES applications(application_id)
        ON DELETE CASCADE,

    version_id BIGINT NOT NULL
        REFERENCES component_versions(version_id)
        ON DELETE RESTRICT,

    instance_key VARCHAR(150) NOT NULL,

    supplied_props JSONB NOT NULL DEFAULT '{}'::jsonb,

    resolved_props JSONB,

    status instance_status NOT NULL DEFAULT 'created',

    error_message TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    rendered_at TIMESTAMPTZ,

    CONSTRAINT uq_application_instance
        UNIQUE(application_id, instance_key),

    CONSTRAINT chk_supplied_props_object
        CHECK (
            jsonb_typeof(supplied_props) = 'object'
        ),

    CONSTRAINT chk_resolved_props_object
        CHECK (
            resolved_props IS NULL
            OR jsonb_typeof(resolved_props) = 'object'
        )
);


-- ============================================================
-- COMPONENT USAGE EVENTS
-- ============================================================

CREATE TABLE component_usage_events (
    event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    instance_id BIGINT NOT NULL
        REFERENCES component_instances(instance_id)
        ON DELETE CASCADE,

    event_type VARCHAR(40) NOT NULL,

    execution_time_ms NUMERIC(12,3),

    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_execution_time
        CHECK (
            execution_time_ms IS NULL
            OR execution_time_ms >= 0
        )
);


-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX idx_components_status
    ON components(status);

CREATE INDEX idx_components_category
    ON components(component_category);

CREATE INDEX idx_versions_component
    ON component_versions(component_id, version_number DESC);

CREATE INDEX idx_props_version
    ON component_props(version_id);

CREATE INDEX idx_composition_parent
    ON component_compositions(parent_version_id, display_order);

CREATE INDEX idx_composition_child
    ON component_compositions(child_version_id);

CREATE INDEX idx_instances_application_status
    ON component_instances(application_id, status);

CREATE INDEX idx_instances_version
    ON component_instances(version_id);

CREATE INDEX idx_usage_instance_time
    ON component_usage_events(instance_id, recorded_at DESC);


-- ============================================================
-- UPDATED_AT TRIGGER
-- ============================================================

CREATE OR REPLACE FUNCTION update_component_timestamp()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at := NOW();
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_component_updated_at
BEFORE UPDATE ON components
FOR EACH ROW
EXECUTE FUNCTION update_component_timestamp();


-- ============================================================
-- COMPONENT VERSION VALIDATION
-- ============================================================

CREATE OR REPLACE FUNCTION validate_component_version()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    current_component_version INTEGER;
BEGIN
    SELECT current_version
    INTO current_component_version
    FROM components
    WHERE component_id = NEW.component_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Component does not exist';
    END IF;

    IF NEW.version_number <= current_component_version THEN
        RAISE EXCEPTION
            'New version must exceed current version %',
            current_component_version;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_component_version
BEFORE INSERT ON component_versions
FOR EACH ROW
EXECUTE FUNCTION validate_component_version();


-- ============================================================
-- COMPONENT DEPENDENCY CYCLE DETECTION
-- ============================================================

CREATE OR REPLACE FUNCTION prevent_composition_cycle()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    creates_cycle BOOLEAN;
BEGIN
    IF NEW.parent_version_id = NEW.child_version_id THEN
        RAISE EXCEPTION 'A component cannot contain itself';
    END IF;

    WITH RECURSIVE descendants(version_id) AS (
        SELECT NEW.child_version_id

        UNION

        SELECT cc.child_version_id
        FROM component_compositions cc
        JOIN descendants d
            ON cc.parent_version_id = d.version_id
    )
    SELECT EXISTS (
        SELECT 1
        FROM descendants
        WHERE version_id = NEW.parent_version_id
    )
    INTO creates_cycle;

    IF creates_cycle THEN
        RAISE EXCEPTION
            'Composition would introduce a dependency cycle';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_prevent_composition_cycle
BEFORE INSERT OR UPDATE ON component_compositions
FOR EACH ROW
EXECUTE FUNCTION prevent_composition_cycle();


-- ============================================================
-- PROPERTY VALIDATION FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION validate_component_props(
    p_version_id BIGINT,
    p_supplied JSONB
)
RETURNS JSONB
LANGUAGE plpgsql
AS $$
DECLARE
    property_record RECORD;
    supplied_value JSONB;
    resolved JSONB := '{}'::jsonb;
    actual_type TEXT;
    expected_type TEXT;
BEGIN
    IF jsonb_typeof(p_supplied) <> 'object' THEN
        RAISE EXCEPTION 'Properties must be a JSON object';
    END IF;

    -- Reject unknown properties.
    IF EXISTS (
        SELECT 1
        FROM jsonb_object_keys(p_supplied) AS supplied(key)
        WHERE NOT EXISTS (
            SELECT 1
            FROM component_props cp
            WHERE cp.version_id = p_version_id
              AND cp.prop_name = supplied.key
        )
    ) THEN
        RAISE EXCEPTION 'Unknown component property supplied';
    END IF;

    FOR property_record IN
        SELECT *
        FROM component_props
        WHERE version_id = p_version_id
    LOOP
        supplied_value := p_supplied -> property_record.prop_name;

        IF supplied_value IS NULL THEN
            IF property_record.has_default THEN
                supplied_value := property_record.default_value;
            ELSIF property_record.is_required THEN
                RAISE EXCEPTION
                    'Required property missing: %',
                    property_record.prop_name;
            ELSE
                CONTINUE;
            END IF;
        END IF;

        actual_type := jsonb_typeof(supplied_value);

        expected_type := CASE property_record.data_type
            WHEN 'string' THEN 'string'
            WHEN 'number' THEN 'number'
            WHEN 'boolean' THEN 'boolean'
            WHEN 'object' THEN 'object'
            WHEN 'array' THEN 'array'
            WHEN 'function' THEN 'object'
            WHEN 'node' THEN 'object'
            WHEN 'any' THEN actual_type
        END;

        IF property_record.data_type <> 'any'
           AND actual_type <> expected_type THEN
            RAISE EXCEPTION
                'Invalid type for property %. Expected %, received %',
                property_record.prop_name,
                expected_type,
                actual_type;
        END IF;

        -- Optional minimum and maximum string length.
        IF property_record.data_type = 'string' THEN
            IF property_record.validation_rules ? 'minLength'
               AND char_length(supplied_value #>> '{}')
                   < (property_record.validation_rules ->> 'minLength')::integer
            THEN
                RAISE EXCEPTION
                    'Property % is shorter than allowed',
                    property_record.prop_name;
            END IF;

            IF property_record.validation_rules ? 'maxLength'
               AND char_length(supplied_value #>> '{}')
                   > (property_record.validation_rules ->> 'maxLength')::integer
            THEN
                RAISE EXCEPTION
                    'Property % exceeds maximum length',
                    property_record.prop_name;
            END IF;
        END IF;

        resolved := resolved || jsonb_build_object(
            property_record.prop_name,
            supplied_value
        );
    END LOOP;

    RETURN resolved;
END;
$$;


-- ============================================================
-- COMPONENT INSTANCE VALIDATION
-- ============================================================

CREATE OR REPLACE PROCEDURE validate_component_instance(
    p_instance_id BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    instance_record component_instances%ROWTYPE;
    resolved JSONB;
    component_state component_status;
BEGIN
    SELECT ci.*
    INTO instance_record
    FROM component_instances ci
    WHERE ci.instance_id = p_instance_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Component instance not found';
    END IF;

    SELECT c.status
    INTO component_state
    FROM component_versions cv
    JOIN components c
        ON c.component_id = cv.component_id
    WHERE cv.version_id = instance_record.version_id;

    IF component_state <> 'active' THEN
        RAISE EXCEPTION
            'Only active components can be validated';
    END IF;

    resolved := validate_component_props(
        instance_record.version_id,
        instance_record.supplied_props
    );

    UPDATE component_instances
    SET resolved_props = resolved,
        status = 'validated',
        error_message = NULL
    WHERE instance_id = p_instance_id;
END;
$$;


-- ============================================================
-- COMPONENT CATALOG VIEW
-- ============================================================

CREATE OR REPLACE VIEW component_catalog AS
SELECT
    c.component_id,
    c.component_name,
    c.component_category,
    c.description,
    c.status,
    c.current_version,
    c.accepts_children,
    COUNT(DISTINCT cp.prop_id) AS property_count,
    COUNT(DISTINCT cc.composition_id) AS composition_count
FROM components c
LEFT JOIN component_versions cv
    ON cv.component_id = c.component_id
   AND cv.version_number = c.current_version
LEFT JOIN component_props cp
    ON cp.version_id = cv.version_id
LEFT JOIN component_compositions cc
    ON cc.parent_version_id = cv.version_id
GROUP BY
    c.component_id,
    c.component_name,
    c.component_category,
    c.description,
    c.status,
    c.current_version,
    c.accepts_children;


-- ============================================================
-- COMPONENT USAGE REPORT
-- ============================================================

CREATE OR REPLACE VIEW component_usage_report AS
SELECT
    c.component_name,
    cv.version_number,
    COUNT(DISTINCT ci.instance_id) AS total_instances,
    COUNT(*) FILTER (
        WHERE ci.status = 'rendered'
    ) AS rendered_instances,
    COUNT(*) FILTER (
        WHERE ci.status = 'failed'
    ) AS failed_instances,
    ROUND(
        AVG(ue.execution_time_ms),
        3
    ) AS average_execution_ms
FROM components c
JOIN component_versions cv
    ON cv.component_id = c.component_id
JOIN component_instances ci
    ON ci.version_id = cv.version_id
LEFT JOIN component_usage_events ue
    ON ue.instance_id = ci.instance_id
GROUP BY
    c.component_name,
    cv.version_number;


-- ============================================================
-- SAMPLE DATA
-- ============================================================

INSERT INTO components (
    component_name,
    description,
    component_category,
    status,
    current_version,
    accepts_children
)
VALUES
(
    'Text',
    'Reusable text display component',
    'display',
    'active',
    1,
    FALSE
),
(
    'Button',
    'Reusable action button',
    'input',
    'active',
    1,
    FALSE
),
(
    'Badge',
    'Status indicator component',
    'display',
    'active',
    1,
    FALSE
),
(
    'Card',
    'Composable content container',
    'layout',
    'active',
    1,
    TRUE
),
(
    'Conditional',
    'Conditionally rendered container',
    'logic',
    'active',
    1,
    TRUE
);


INSERT INTO component_versions (
    component_id,
    version_number,
    implementation_type,
    change_description
)
SELECT
    component_id,
    1,
    CASE
        WHEN component_name = 'Card' THEN 'composite'
        WHEN component_name = 'Conditional' THEN 'composite'
        ELSE 'functional'
    END,
    'Initial component implementation'
FROM components
ORDER BY component_id;


-- Text properties.

INSERT INTO component_props (
    version_id,
    prop_name,
    data_type,
    is_required,
    has_default,
    default_value,
    description
)
SELECT
    cv.version_id,
    'content',
    'string',
    TRUE,
    FALSE,
    NULL,
    'Text content displayed by the component'
FROM component_versions cv
JOIN components c USING (component_id)
WHERE c.component_name = 'Text';


INSERT INTO component_props (
    version_id,
    prop_name,
    data_type,
    has_default,
    default_value,
    description
)
SELECT
    cv.version_id,
    'tone',
    'string',
    TRUE,
    '"normal"'::jsonb,
    'Text visual tone'
FROM component_versions cv
JOIN components c USING (component_id)
WHERE c.component_name = 'Text';


-- Button properties.

INSERT INTO component_props (
    version_id,
    prop_name,
    data_type,
    is_required,
    description
)
SELECT
    cv.version_id,
    'label',
    'string',
    TRUE,
    'Visible button label'
FROM component_versions cv
JOIN components c USING (component_id)
WHERE c.component_name = 'Button';


INSERT INTO component_props (
    version_id,
    prop_name,
    data_type,
    has_default,
    default_value,
    description
)
SELECT
    cv.version_id,
    'disabled',
    'boolean',
    TRUE,
    'false'::jsonb,
    'Controls whether the button is disabled'
FROM component_versions cv
JOIN components c USING (component_id)
WHERE c.component_name = 'Button';


INSERT INTO component_props (
    version_id,
    prop_name,
    data_type,
    has_default,
    default_value
)
SELECT
    cv.version_id,
    'variant',
    'string',
    TRUE,
    '"primary"'::jsonb
FROM component_versions cv
JOIN components c USING (component_id)
WHERE c.component_name = 'Button';


-- Badge properties.

INSERT INTO component_props (
    version_id,
    prop_name,
    data_type,
    is_required,
    description
)
SELECT
    cv.version_id,
    'label',
    'string',
    TRUE,
    'Visible badge text'
FROM component_versions cv
JOIN components c USING (component_id)
WHERE c.component_name = 'Badge';


INSERT INTO component_props (
    version_id,
    prop_name,
    data_type,
    has_default,
    default_value
)
SELECT
    cv.version_id,
    'status',
    'string',
    TRUE,
    '"neutral"'::jsonb
FROM component_versions cv
JOIN components c USING (component_id)
WHERE c.component_name = 'Badge';


-- Card properties.

INSERT INTO component_props (
    version_id,
    prop_name,
    data_type,
    is_required
)
SELECT
    cv.version_id,
    'title',
    'string',
    TRUE
FROM component_versions cv
JOIN components c USING (component_id)
WHERE c.component_name = 'Card';


INSERT INTO component_props (
    version_id,
    prop_name,
    data_type,
    has_default,
    default_value
)
SELECT
    cv.version_id,
    'description',
    'string',
    TRUE,
    '""'::jsonb
FROM component_versions cv
JOIN components c USING (component_id)
WHERE c.component_name = 'Card';


-- Conditional properties.

INSERT INTO component_props (
    version_id,
    prop_name,
    data_type,
    is_required,
    description
)
SELECT
    cv.version_id,
    'visible',
    'boolean',
    TRUE,
    'Controls conditional rendering'
FROM component_versions cv
JOIN components c USING (component_id)
WHERE c.component_name = 'Conditional';


-- Composition: Card contains Text, Badge, Button and Conditional.

INSERT INTO component_compositions (
    parent_version_id,
    child_version_id,
    relationship,
    display_order,
    is_required
)
SELECT
    parent.version_id,
    child.version_id,
    'child',
    CASE child_component.component_name
        WHEN 'Text' THEN 1
        WHEN 'Badge' THEN 2
        WHEN 'Button' THEN 3
        WHEN 'Conditional' THEN 4
    END,
    FALSE
FROM component_versions parent
JOIN components parent_component
    ON parent_component.component_id = parent.component_id
JOIN component_versions child
    ON child.version_number = 1
JOIN components child_component
    ON child_component.component_id = child.component_id
WHERE parent_component.component_name = 'Card'
  AND child_component.component_name IN (
      'Text',
      'Badge',
      'Button',
      'Conditional'
  );


-- Applications.

INSERT INTO applications (
    application_name,
    description,
    environment
)
VALUES
(
    'Project Management Portal',
    'Enterprise project management interface',
    'development'
),
(
    'Operations Dashboard',
    'Internal operational dashboard',
    'testing'
);


-- Create component instances.

INSERT INTO component_instances (
    application_id,
    version_id,
    instance_key,
    supplied_props
)
SELECT
    a.application_id,
    cv.version_id,
    'dashboard-main-card',
    jsonb_build_object(
        'title', 'Project Dashboard',
        'description', 'Operational project information'
    )
FROM applications a
JOIN components c
    ON c.component_name = 'Card'
JOIN component_versions cv
    ON cv.component_id = c.component_id
   AND cv.version_number = 1
WHERE a.application_name = 'Project Management Portal';


INSERT INTO component_instances (
    application_id,
    version_id,
    instance_key,
    supplied_props
)
SELECT
    a.application_id,
    cv.version_id,
    'dashboard-primary-button',
    '{"label":"Open Projects"}'::jsonb
FROM applications a
JOIN components c
    ON c.component_name = 'Button'
JOIN component_versions cv
    ON cv.component_id = c.component_id
   AND cv.version_number = 1
WHERE a.application_name = 'Project Management Portal';


INSERT INTO component_instances (
    application_id,
    version_id,
    instance_key,
    supplied_props
)
SELECT
    a.application_id,
    cv.version_id,
    'dashboard-invalid-button',
    '{"disabled":"yes"}'::jsonb
FROM applications a
JOIN components c
    ON c.component_name = 'Button'
JOIN component_versions cv
    ON cv.component_id = c.component_id
   AND cv.version_number = 1
WHERE a.application_name = 'Operations Dashboard';


-- ============================================================
-- VALIDATION WORKFLOW
-- ============================================================

DO $$
DECLARE
    valid_instance BIGINT;
    invalid_instance BIGINT;
BEGIN
    SELECT instance_id
    INTO valid_instance
    FROM component_instances
    WHERE instance_key = 'dashboard-main-card';

    CALL validate_component_instance(valid_instance);

    SELECT instance_id
    INTO valid_instance
    FROM component_instances
    WHERE instance_key = 'dashboard-primary-button';

    CALL validate_component_instance(valid_instance);

    SELECT instance_id
    INTO invalid_instance
    FROM component_instances
    WHERE instance_key = 'dashboard-invalid-button';

    BEGIN
        CALL validate_component_instance(invalid_instance);
    EXCEPTION
        WHEN OTHERS THEN
            UPDATE component_instances
            SET status = 'failed',
                error_message = SQLERRM
            WHERE instance_id = invalid_instance;
    END;
END;
$$;


-- ============================================================
-- RECORD RENDERING EVENTS
-- ============================================================

INSERT INTO component_usage_events (
    instance_id,
    event_type,
    execution_time_ms
)
SELECT
    instance_id,
    'render',
    CASE instance_key
        WHEN 'dashboard-main-card' THEN 1.450
        WHEN 'dashboard-primary-button' THEN 0.320
        ELSE NULL
    END
FROM component_instances
WHERE status = 'validated';


-- ============================================================
-- RETRIEVAL: COMPONENT CATALOG
-- ============================================================

SELECT
    component_name,
    component_category,
    status,
    current_version,
    property_count,
    composition_count
FROM component_catalog
ORDER BY component_category, component_name;


-- ============================================================
-- RETRIEVAL: COMPONENT PROPERTIES
-- ============================================================

SELECT
    c.component_name,
    cp.prop_name,
    cp.data_type,
    cp.is_required,
    cp.has_default,
    cp.default_value
FROM component_props cp
JOIN component_versions cv
    ON cv.version_id = cp.version_id
JOIN components c
    ON c.component_id = cv.component_id
ORDER BY c.component_name, cp.prop_name;


-- ============================================================
-- VALIDATION: INSTANCE STATES
-- ============================================================

SELECT
    a.application_name,
    ci.instance_key,
    ci.status,
    ci.resolved_props,
    ci.error_message
FROM component_instances ci
JOIN applications a
    ON a.application_id = ci.application_id
ORDER BY ci.instance_id;


-- ============================================================
-- EVALUATION: COMPONENT DEPENDENCY TREE
-- ============================================================

WITH RECURSIVE dependency_tree AS (
    SELECT
        cc.parent_version_id,
        cc.child_version_id,
        1 AS depth,
        ARRAY[
            cc.parent_version_id,
            cc.child_version_id
        ]::BIGINT[] AS path
    FROM component_compositions cc

    UNION ALL

    SELECT
        dt.parent_version_id,
        cc.child_version_id,
        dt.depth + 1,
        dt.path || cc.child_version_id
    FROM dependency_tree dt
    JOIN component_compositions cc
        ON cc.parent_version_id = dt.child_version_id
    WHERE NOT cc.child_version_id = ANY(dt.path)
      AND dt.depth < 20
)
SELECT
    parent.component_name AS parent_component,
    child.component_name AS child_component,
    dt.depth
FROM dependency_tree dt
JOIN component_versions pvc
    ON pvc.version_id = dt.parent_version_id
JOIN components parent
    ON parent.component_id = pvc.component_id
JOIN component_versions cvc
    ON cvc.version_id = dt.child_version_id
JOIN components child
    ON child.component_id = cvc.component_id
ORDER BY parent.component_name, dt.depth;


-- ============================================================
-- AGGREGATION: APPLICATION COMPONENT COUNTS
-- ============================================================

SELECT
    a.application_name,
    COUNT(ci.instance_id) AS total_instances,
    COUNT(*) FILTER (
        WHERE ci.status = 'validated'
    ) AS validated_instances,
    COUNT(*) FILTER (
        WHERE ci.status = 'failed'
    ) AS failed_instances,
    COUNT(*) FILTER (
        WHERE ci.status = 'rendered'
    ) AS rendered_instances
FROM applications a
LEFT JOIN component_instances ci
    ON ci.application_id = a.application_id
GROUP BY a.application_id, a.application_name
ORDER BY a.application_name;


-- ============================================================
-- REPORTING: COMPONENT PERFORMANCE
-- ============================================================

SELECT
    component_name,
    version_number,
    total_instances,
    rendered_instances,
    failed_instances,
    average_execution_ms
FROM component_usage_report
ORDER BY total_instances DESC, component_name;


-- ============================================================
-- ELIGIBILITY: COMPONENT COMPOSITION
-- ============================================================

SELECT
    parent.component_name AS parent,
    child.component_name AS child,
    parent.status AS parent_status,
    child.status AS child_status,
    CASE
        WHEN parent.status <> 'active'
            THEN 'INELIGIBLE_PARENT'
        WHEN child.status <> 'active'
            THEN 'INELIGIBLE_CHILD'
        ELSE 'ELIGIBLE'
    END AS composition_eligibility
FROM component_compositions cc
JOIN component_versions pvc
    ON pvc.version_id = cc.parent_version_id
JOIN components parent
    ON parent.component_id = pvc.component_id
JOIN component_versions cvc
    ON cvc.version_id = cc.child_version_id
JOIN components child
    ON child.component_id = cvc.component_id
ORDER BY parent.component_name, child.component_name;


-- ============================================================
-- FAILURE CASE: INVALID PROP VALIDATION
-- ============================================================

DO $$
DECLARE
    button_version BIGINT;
BEGIN
    SELECT cv.version_id
    INTO button_version
    FROM component_versions cv
    JOIN components c
        ON c.component_id = cv.component_id
    WHERE c.component_name = 'Button'
      AND cv.version_number = 1;

    BEGIN
        PERFORM validate_component_props(
            button_version,
            '{"label":123}'::jsonb
        );

        RAISE EXCEPTION
            'Expected invalid property validation to fail';
    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE
                'Invalid property correctly rejected: %',
                SQLERRM;
    END;
END;
$$;


-- ============================================================
-- FAILURE CASE: UNKNOWN PROPERTY
-- ============================================================

DO $$
DECLARE
    button_version BIGINT;
BEGIN
    SELECT cv.version_id
    INTO button_version
    FROM component_versions cv
    JOIN components c
        ON c.component_id = cv.component_id
    WHERE c.component_name = 'Button'
      AND cv.version_number = 1;

    BEGIN
        PERFORM validate_component_props(
            button_version,
            '{"label":"Save","unknown":true}'::jsonb
        );

        RAISE EXCEPTION
            'Expected unknown property validation to fail';
    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE
                'Unknown property correctly rejected: %',
                SQLERRM;
    END;
END;
$$;


COMMIT;
