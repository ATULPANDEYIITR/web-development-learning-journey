-- ============================================================
-- UI ENGINEERING
-- Design Systems, Component Libraries, Tokens and Accessibility
-- PostgreSQL 15+
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS ui_engineering;

SET search_path TO ui_engineering, public;

-- ============================================================
-- 1. DOMAIN TYPES
-- ============================================================

CREATE TYPE token_category AS ENUM (
    'color',
    'spacing',
    'typography',
    'radius',
    'elevation',
    'motion'
);

CREATE TYPE component_status AS ENUM (
    'draft',
    'review',
    'approved',
    'deprecated'
);

CREATE TYPE accessibility_level AS ENUM (
    'A',
    'AA',
    'AAA'
);

CREATE TYPE audit_severity AS ENUM (
    'error',
    'warning',
    'info'
);

CREATE TYPE theme_mode AS ENUM (
    'light',
    'dark',
    'high_contrast'
);

-- ============================================================
-- 2. DESIGN SYSTEMS AND ORGANIZATION
-- ============================================================

CREATE TABLE design_systems (
    system_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    system_name VARCHAR(150) NOT NULL UNIQUE,
    description TEXT,
    version VARCHAR(30) NOT NULL DEFAULT '1.0.0',
    owner VARCHAR(150) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_system_version
        CHECK (version ~ '^[0-9]+\.[0-9]+\.[0-9]+$')
);

CREATE TABLE system_members (
    member_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    system_id BIGINT NOT NULL
        REFERENCES design_systems(system_id) ON DELETE CASCADE,
    username VARCHAR(100) NOT NULL,
    role VARCHAR(30) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT valid_member_role
        CHECK (
            role IN (
                'designer',
                'developer',
                'accessibility_reviewer',
                'maintainer',
                'administrator'
            )
        ),

    UNIQUE (system_id, username)
);

-- ============================================================
-- 3. DESIGN TOKENS
-- ============================================================

CREATE TABLE design_tokens (
    token_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    system_id BIGINT NOT NULL
        REFERENCES design_systems(system_id) ON DELETE CASCADE,
    token_name VARCHAR(150) NOT NULL,
    category token_category NOT NULL,
    token_value VARCHAR(500) NOT NULL,
    description TEXT,
    alias_token_id BIGINT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_system_token
        UNIQUE (system_id, token_name),

    CONSTRAINT token_not_self_referencing
        CHECK (alias_token_id IS NULL OR alias_token_id <> token_id),

    CONSTRAINT valid_token_name
        CHECK (
            token_name ~
            '^[a-z][a-z0-9-]*(\.[a-z][a-z0-9-]*)*$'
        ),

    CONSTRAINT valid_spacing_token
        CHECK (
            category <> 'spacing'
            OR token_value ~ '^[0-9]+(\.[0-9]+)?(px|rem)$'
        ),

    CONSTRAINT valid_color_token
        CHECK (
            category <> 'color'
            OR token_value ~ '^#[0-9A-Fa-f]{6}$'
            OR alias_token_id IS NOT NULL
        )
);

ALTER TABLE design_tokens
ADD CONSTRAINT token_alias_fk
FOREIGN KEY (alias_token_id)
REFERENCES design_tokens(token_id)
ON DELETE RESTRICT;

CREATE INDEX idx_tokens_system_category
ON design_tokens(system_id, category);

CREATE INDEX idx_tokens_alias
ON design_tokens(alias_token_id)
WHERE alias_token_id IS NOT NULL;

-- ============================================================
-- 4. THEMES
-- ============================================================

CREATE TABLE themes (
    theme_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    system_id BIGINT NOT NULL
        REFERENCES design_systems(system_id) ON DELETE CASCADE,
    theme_name VARCHAR(100) NOT NULL,
    mode theme_mode NOT NULL,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,

    UNIQUE (system_id, theme_name)
);

CREATE TABLE theme_overrides (
    override_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    theme_id BIGINT NOT NULL
        REFERENCES themes(theme_id) ON DELETE CASCADE,
    token_id BIGINT NOT NULL
        REFERENCES design_tokens(token_id) ON DELETE CASCADE,
    override_value VARCHAR(500) NOT NULL,

    UNIQUE (theme_id, token_id)
);

-- ============================================================
-- 5. COMPONENT LIBRARY
-- ============================================================

CREATE TABLE component_categories (
    category_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    system_id BIGINT NOT NULL
        REFERENCES design_systems(system_id) ON DELETE CASCADE,
    category_name VARCHAR(100) NOT NULL,
    description TEXT,

    UNIQUE (system_id, category_name)
);

CREATE TABLE components (
    component_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    system_id BIGINT NOT NULL
        REFERENCES design_systems(system_id) ON DELETE CASCADE,
    category_id BIGINT NOT NULL
        REFERENCES component_categories(category_id),
    component_name VARCHAR(120) NOT NULL,
    version VARCHAR(30) NOT NULL,
    status component_status NOT NULL DEFAULT 'draft',
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_component_version
        CHECK (version ~ '^[0-9]+\.[0-9]+\.[0-9]+$'),

    CONSTRAINT valid_component_name
        CHECK (component_name ~ '^[A-Z][A-Za-z0-9]*$'),

    UNIQUE (system_id, component_name, version),
    UNIQUE (component_id, system_id)
);

CREATE INDEX idx_components_status
ON components(system_id, status);

CREATE INDEX idx_components_category
ON components(category_id);

CREATE TABLE component_properties (
    property_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    component_id BIGINT NOT NULL
        REFERENCES components(component_id) ON DELETE CASCADE,
    property_name VARCHAR(100) NOT NULL,
    property_type VARCHAR(30) NOT NULL,
    required BOOLEAN NOT NULL DEFAULT FALSE,
    default_value JSONB,
    allowed_values JSONB NOT NULL DEFAULT '[]'::jsonb,

    CONSTRAINT valid_property_type
        CHECK (
            property_type IN (
                'string',
                'number',
                'boolean',
                'object',
                'array'
            )
        ),

    CONSTRAINT allowed_values_array
        CHECK (jsonb_typeof(allowed_values) = 'array'),

    UNIQUE (component_id, property_name)
);

CREATE TABLE component_dependencies (
    component_id BIGINT NOT NULL
        REFERENCES components(component_id) ON DELETE CASCADE,
    dependency_component_id BIGINT NOT NULL
        REFERENCES components(component_id) ON DELETE RESTRICT,

    PRIMARY KEY (component_id, dependency_component_id),

    CONSTRAINT no_self_dependency
        CHECK (component_id <> dependency_component_id)
);

CREATE TABLE component_token_dependencies (
    component_id BIGINT NOT NULL
        REFERENCES components(component_id) ON DELETE CASCADE,
    token_id BIGINT NOT NULL
        REFERENCES design_tokens(token_id) ON DELETE RESTRICT,

    PRIMARY KEY (component_id, token_id)
);

-- ============================================================
-- 6. ACCESSIBILITY GOVERNANCE
-- ============================================================

CREATE TABLE accessibility_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    system_id BIGINT NOT NULL
        REFERENCES design_systems(system_id) ON DELETE CASCADE,
    policy_name VARCHAR(120) NOT NULL,
    level accessibility_level NOT NULL DEFAULT 'AA',
    minimum_contrast NUMERIC(4,2) NOT NULL DEFAULT 4.50,
    keyboard_required BOOLEAN NOT NULL DEFAULT TRUE,
    visible_focus_required BOOLEAN NOT NULL DEFAULT TRUE,
    accessible_name_required BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT valid_minimum_contrast
        CHECK (minimum_contrast BETWEEN 1 AND 21),

    UNIQUE (system_id, policy_name)
);

CREATE TABLE component_accessibility (
    component_id BIGINT PRIMARY KEY
        REFERENCES components(component_id) ON DELETE CASCADE,
    policy_id BIGINT NOT NULL
        REFERENCES accessibility_policies(policy_id),
    semantic_role VARCHAR(100) NOT NULL,
    accessible_name BOOLEAN NOT NULL,
    keyboard_operable BOOLEAN NOT NULL,
    visible_focus BOOLEAN NOT NULL,
    observed_contrast NUMERIC(5,2),

    CONSTRAINT valid_observed_contrast
        CHECK (
            observed_contrast IS NULL
            OR observed_contrast BETWEEN 0 AND 21
        )
);

CREATE TABLE accessibility_audits (
    audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    component_id BIGINT NOT NULL
        REFERENCES components(component_id) ON DELETE CASCADE,
    severity audit_severity NOT NULL,
    criterion VARCHAR(150) NOT NULL,
    finding TEXT NOT NULL,
    audited_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_accessibility_findings
ON accessibility_audits(component_id, severity);

-- ============================================================
-- 7. COMPONENT RELEASE HISTORY
-- ============================================================

CREATE TABLE component_releases (
    release_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    component_id BIGINT NOT NULL
        REFERENCES components(component_id) ON DELETE RESTRICT,
    version VARCHAR(30) NOT NULL,
    released_by VARCHAR(100) NOT NULL,
    release_notes TEXT,
    released_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (component_id, version),

    CHECK (version ~ '^[0-9]+\.[0-9]+\.[0-9]+$')
);

CREATE TABLE component_events (
    event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    component_id BIGINT NOT NULL
        REFERENCES components(component_id) ON DELETE CASCADE,
    previous_status component_status,
    new_status component_status NOT NULL,
    actor VARCHAR(100) NOT NULL,
    event_time TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    details JSONB NOT NULL DEFAULT '{}'::jsonb
);

-- ============================================================
-- 8. UPDATED TIMESTAMP TRIGGER
-- ============================================================

CREATE FUNCTION update_component_timestamp()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at := CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_component_timestamp
BEFORE UPDATE ON components
FOR EACH ROW
EXECUTE FUNCTION update_component_timestamp();

-- ============================================================
-- 9. COMPONENT STATE TRANSITION AUDIT
-- ============================================================

CREATE FUNCTION audit_component_status()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.status IS DISTINCT FROM OLD.status THEN
        INSERT INTO component_events (
            component_id,
            previous_status,
            new_status,
            actor,
            details
        )
        VALUES (
            NEW.component_id,
            OLD.status,
            NEW.status,
            COALESCE(
                current_setting('ui_engineering.actor', TRUE),
                CURRENT_USER
            ),
            jsonb_build_object('source', 'database_trigger')
        );
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_component_status_audit
AFTER UPDATE OF status ON components
FOR EACH ROW
EXECUTE FUNCTION audit_component_status();

-- ============================================================
-- 10. TOKEN RESOLUTION
-- ============================================================

CREATE FUNCTION resolve_token(
    p_token_id BIGINT,
    p_theme_id BIGINT DEFAULT NULL
)
RETURNS TEXT
LANGUAGE plpgsql
AS $$
DECLARE
    current_token BIGINT := p_token_id;
    next_token BIGINT;
    resolved_value TEXT;
    visited BIGINT[] := ARRAY[]::BIGINT[];
    override_value TEXT;
BEGIN
    LOOP
        IF current_token = ANY(visited) THEN
            RAISE EXCEPTION
                'Circular token alias detected at token %',
                current_token;
        END IF;

        visited := array_append(visited, current_token);

        IF p_theme_id IS NOT NULL THEN
            SELECT o.override_value
            INTO override_value
            FROM theme_overrides o
            WHERE o.theme_id = p_theme_id
              AND o.token_id = current_token;

            IF FOUND THEN
                RETURN override_value;
            END IF;
        END IF;

        SELECT alias_token_id, token_value
        INTO next_token, resolved_value
        FROM design_tokens
        WHERE token_id = current_token;

        IF NOT FOUND THEN
            RAISE EXCEPTION
                'Unknown token ID: %',
                current_token;
        END IF;

        IF next_token IS NULL THEN
            RETURN resolved_value;
        END IF;

        current_token := next_token;
    END LOOP;
END;
$$;

-- ============================================================
-- 11. COMPONENT VALIDATION FUNCTION
-- ============================================================

CREATE FUNCTION validate_component(p_component_id BIGINT)
RETURNS TABLE (
    severity audit_severity,
    criterion TEXT,
    finding TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    accessibility_record RECORD;
    dependency_record RECORD;
    token_record RECORD;
    minimum_ratio NUMERIC;
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM components
        WHERE component_id = p_component_id
    ) THEN
        RAISE EXCEPTION 'Unknown component: %', p_component_id;
    END IF;

    -- Validate required token references.
    FOR token_record IN
        SELECT t.token_id, t.token_name
        FROM component_token_dependencies d
        JOIN design_tokens t ON t.token_id = d.token_id
        WHERE d.component_id = p_component_id
    LOOP
        BEGIN
            PERFORM resolve_token(token_record.token_id);
        EXCEPTION WHEN OTHERS THEN
            severity := 'error';
            criterion := 'design-token-integrity';
            finding := SQLERRM;
            RETURN NEXT;
        END;
    END LOOP;

    -- Validate declared component dependencies.
    FOR dependency_record IN
        SELECT d.dependency_component_id
        FROM component_dependencies d
        WHERE d.component_id = p_component_id
    LOOP
        IF NOT EXISTS (
            SELECT 1
            FROM components
            WHERE component_id =
                dependency_record.dependency_component_id
        ) THEN
            severity := 'error';
            criterion := 'component-dependency';
            finding := 'Referenced component is missing';
            RETURN NEXT;
        END IF;
    END LOOP;

    SELECT
        ca.*,
        ap.minimum_contrast,
        ap.keyboard_required,
        ap.visible_focus_required,
        ap.accessible_name_required
    INTO accessibility_record
    FROM component_accessibility ca
    JOIN accessibility_policies ap
      ON ap.policy_id = ca.policy_id
    WHERE ca.component_id = p_component_id;

    IF NOT FOUND THEN
        severity := 'error';
        criterion := 'accessibility-policy';
        finding := 'No accessibility policy is assigned';
        RETURN NEXT;
        RETURN;
    END IF;

    IF accessibility_record.semantic_role IS NULL
       OR accessibility_record.semantic_role = '' THEN
        severity := 'error';
        criterion := 'semantic-role';
        finding := 'Semantic role is required';
        RETURN NEXT;
    END IF;

    IF accessibility_record.accessible_name_required
       AND NOT accessibility_record.accessible_name THEN
        severity := 'error';
        criterion := 'accessible-name';
        finding := 'Accessible name is missing';
        RETURN NEXT;
    END IF;

    IF accessibility_record.keyboard_required
       AND NOT accessibility_record.keyboard_operable THEN
        severity := 'error';
        criterion := 'keyboard-operation';
        finding := 'Keyboard operation is unavailable';
        RETURN NEXT;
    END IF;

    IF accessibility_record.visible_focus_required
       AND NOT accessibility_record.visible_focus THEN
        severity := 'error';
        criterion := 'visible-focus';
        finding := 'Visible focus indicator is missing';
        RETURN NEXT;
    END IF;

    minimum_ratio := accessibility_record.minimum_contrast;

    IF accessibility_record.observed_contrast IS NULL THEN
        severity := 'warning';
        criterion := 'contrast-measurement';
        finding := 'Contrast measurement is unavailable';
        RETURN NEXT;
    ELSIF accessibility_record.observed_contrast < minimum_ratio THEN
        severity := 'error';
        criterion := 'contrast-ratio';
        finding := format(
            'Observed contrast %s is below required %s',
            accessibility_record.observed_contrast,
            minimum_ratio
        );
        RETURN NEXT;
    END IF;

    RETURN;
END;
$$;

-- ============================================================
-- 12. COMPONENT APPROVAL PROCEDURE
-- ============================================================

CREATE PROCEDURE approve_component(
    p_component_id BIGINT,
    p_actor VARCHAR(100)
)
LANGUAGE plpgsql
AS $$
DECLARE
    current_state component_status;
    error_count BIGINT;
BEGIN
    SELECT status
    INTO current_state
    FROM components
    WHERE component_id = p_component_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Component does not exist';
    END IF;

    IF current_state <> 'review' THEN
        RAISE EXCEPTION
            'Only components under review can be approved';
    END IF;

    SELECT COUNT(*)
    INTO error_count
    FROM validate_component(p_component_id)
    WHERE severity = 'error';

    IF error_count > 0 THEN
        RAISE EXCEPTION
            'Approval rejected: % validation errors',
            error_count;
    END IF;

    PERFORM set_config(
        'ui_engineering.actor',
        p_actor,
        TRUE
    );

    UPDATE components
    SET status = 'approved'
    WHERE component_id = p_component_id;
END;
$$;

-- ============================================================
-- 13. RELEASE ELIGIBILITY VIEW
-- ============================================================

CREATE VIEW component_release_eligibility AS
SELECT
    c.component_id,
    ds.system_name,
    c.component_name,
    c.version,
    c.status,
    COUNT(*) FILTER (
        WHERE findings.severity = 'error'
    ) AS error_count,
    COUNT(*) FILTER (
        WHERE findings.severity = 'warning'
    ) AS warning_count,
    (
        c.status = 'approved'
        AND COUNT(*) FILTER (
            WHERE findings.severity = 'error'
        ) = 0
    ) AS release_eligible
FROM components c
JOIN design_systems ds
    ON ds.system_id = c.system_id
LEFT JOIN LATERAL validate_component(c.component_id)
    AS findings ON TRUE
GROUP BY
    c.component_id,
    ds.system_name,
    c.component_name,
    c.version,
    c.status;

-- ============================================================
-- 14. COMPONENT DEPENDENCY REPORT
-- ============================================================

CREATE VIEW component_dependency_report AS
SELECT
    c.component_id,
    c.component_name,
    COALESCE(
        array_agg(d.component_name)
            FILTER (WHERE d.component_id IS NOT NULL),
        ARRAY[]::VARCHAR[]
    ) AS dependencies
FROM components c
LEFT JOIN component_dependencies cd
    ON cd.component_id = c.component_id
LEFT JOIN components d
    ON d.component_id = cd.dependency_component_id
GROUP BY c.component_id, c.component_name;

-- ============================================================
-- 15. SAMPLE ENTERPRISE DESIGN SYSTEM
-- ============================================================

INSERT INTO design_systems (
    system_name,
    description,
    version,
    owner
)
VALUES (
    'Enterprise UI System',
    'Reusable enterprise interface components and governance',
    '1.0.0',
    'Frontend Platform Team'
);

INSERT INTO system_members (
    system_id,
    username,
    role
)
SELECT system_id, member.username, member.role
FROM design_systems
CROSS JOIN (
    VALUES
        ('design.lead', 'designer'),
        ('frontend.lead', 'developer'),
        ('a11y.reviewer', 'accessibility_reviewer'),
        ('platform.admin', 'administrator')
) AS member(username, role)
WHERE system_name = 'Enterprise UI System';

INSERT INTO design_tokens (
    system_id,
    token_name,
    category,
    token_value
)
SELECT
    system_id,
    token_name,
    category::token_category,
    token_value
FROM design_systems
CROSS JOIN (
    VALUES
        ('color.brand.primary', 'color', '#2457C5'),
        ('color.text.primary', 'color', '#172033'),
        ('color.surface.default', 'color', '#FFFFFF'),
        ('spacing.small', 'spacing', '8px'),
        ('spacing.medium', 'spacing', '16px'),
        ('spacing.large', 'spacing', '24px'),
        ('radius.medium', 'radius', '8px'),
        ('typography.body', 'typography', '16px')
) AS valueset(token_name, category, token_value)
WHERE system_name = 'Enterprise UI System';

-- Create token alias after the referenced token exists.
INSERT INTO design_tokens (
    system_id,
    token_name,
    category,
    token_value,
    alias_token_id
)
SELECT
    ds.system_id,
    'color.action.primary',
    'color',
    'color.brand.primary',
    source.token_id
FROM design_systems ds
JOIN design_tokens source
    ON source.system_id = ds.system_id
   AND source.token_name = 'color.brand.primary'
WHERE ds.system_name = 'Enterprise UI System';

INSERT INTO themes (system_id, theme_name, mode, is_default)
SELECT system_id, 'light', 'light', TRUE
FROM design_systems
WHERE system_name = 'Enterprise UI System';

INSERT INTO themes (system_id, theme_name, mode)
SELECT system_id, 'dark', 'dark'
FROM design_systems
WHERE system_name = 'Enterprise UI System';

INSERT INTO theme_overrides (
    theme_id,
    token_id,
    override_value
)
SELECT
    th.theme_id,
    tk.token_id,
    overrides.override_value
FROM themes th
JOIN design_tokens tk
    ON tk.system_id = th.system_id
JOIN (
    VALUES
        ('color.brand.primary', '#8CAFFF'),
        ('color.text.primary', '#FFFFFF'),
        ('color.surface.default', '#172033')
) AS overrides(token_name, override_value)
    ON overrides.token_name = tk.token_name
WHERE th.theme_name = 'dark';

-- ============================================================
-- 16. CATEGORIES AND COMPONENTS
-- ============================================================

INSERT INTO component_categories (
    system_id,
    category_name,
    description
)
SELECT
    system_id,
    category_name,
    description
FROM design_systems
CROSS JOIN (
    VALUES
        ('Actions', 'Buttons and interactive actions'),
        ('Forms', 'Form inputs and validation controls'),
        ('Navigation', 'Navigation and information hierarchy')
) AS categories(category_name, description)
WHERE system_name = 'Enterprise UI System';

INSERT INTO components (
    system_id,
    category_id,
    component_name,
    version,
    description
)
SELECT
    ds.system_id,
    cc.category_id,
    data.component_name,
    '1.0.0',
    data.description
FROM design_systems ds
JOIN (
    VALUES
        ('Button', 'Actions', 'Primary reusable action control'),
        ('IconButton', 'Actions', 'Icon-only action control'),
        ('TextField', 'Forms', 'Accessible text input')
) AS data(component_name, category_name, description)
    ON TRUE
JOIN component_categories cc
    ON cc.system_id = ds.system_id
   AND cc.category_name = data.category_name
WHERE ds.system_name = 'Enterprise UI System';

-- Component property definitions.
INSERT INTO component_properties (
    component_id,
    property_name,
    property_type,
    required,
    allowed_values
)
SELECT
    c.component_id,
    p.property_name,
    p.property_type,
    p.required,
    p.allowed_values::jsonb
FROM components c
JOIN design_systems ds
    ON ds.system_id = c.system_id
JOIN (
    VALUES
        ('Button', 'label', 'string', TRUE, '[]'),
        ('Button', 'variant', 'string', FALSE,
            '["primary","secondary","danger"]'),
        ('Button', 'disabled', 'boolean', FALSE, '[]'),
        ('IconButton', 'icon', 'string', TRUE, '[]'),
        ('IconButton', 'label', 'string', TRUE, '[]'),
        ('TextField', 'label', 'string', TRUE, '[]'),
        ('TextField', 'required', 'boolean', FALSE, '[]'),
        ('TextField', 'type', 'string', FALSE,
            '["text","email","password","search"]')
) AS p(
    component_name,
    property_name,
    property_type,
    required,
    allowed_values
)
    ON p.component_name = c.component_name
WHERE ds.system_name = 'Enterprise UI System';

-- Component dependencies.
INSERT INTO component_dependencies (
    component_id,
    dependency_component_id
)
SELECT icon.component_id, button.component_id
FROM components icon
JOIN components button
    ON button.system_id = icon.system_id
WHERE icon.component_name = 'IconButton'
  AND button.component_name = 'Button';

-- Token dependencies.
INSERT INTO component_token_dependencies (
    component_id,
    token_id
)
SELECT
    c.component_id,
    t.token_id
FROM components c
JOIN design_tokens t
    ON t.system_id = c.system_id
JOIN (
    VALUES
        ('Button', 'color.action.primary'),
        ('Button', 'spacing.medium'),
        ('Button', 'radius.medium'),
        ('IconButton', 'color.text.primary'),
        ('IconButton', 'spacing.medium'),
        ('TextField', 'color.text.primary'),
        ('TextField', 'spacing.medium'),
        ('TextField', 'radius.medium')
) AS mapping(component_name, token_name)
    ON mapping.component_name = c.component_name
   AND mapping.token_name = t.token_name;

-- ============================================================
-- 17. ACCESSIBILITY POLICY AND AUDIT DATA
-- ============================================================

INSERT INTO accessibility_policies (
    system_id,
    policy_name,
    level,
    minimum_contrast
)
SELECT
    system_id,
    'WCAG AA Enterprise Policy',
    'AA',
    4.50
FROM design_systems
WHERE system_name = 'Enterprise UI System';

INSERT INTO component_accessibility (
    component_id,
    policy_id,
    semantic_role,
    accessible_name,
    keyboard_operable,
    visible_focus,
    observed_contrast
)
SELECT
    c.component_id,
    p.policy_id,
    data.semantic_role,
    data.accessible_name,
    data.keyboard_operable,
    data.visible_focus,
    data.observed_contrast
FROM components c
JOIN accessibility_policies p
    ON p.system_id = c.system_id
JOIN (
    VALUES
        ('Button', 'button', TRUE, TRUE, TRUE, 5.80),
        ('IconButton', 'button', TRUE, TRUE, TRUE, 5.20),
        ('TextField', 'textbox', TRUE, TRUE, TRUE, 5.20)
) AS data(
    component_name,
    semantic_role,
    accessible_name,
    keyboard_operable,
    visible_focus,
    observed_contrast
)
    ON data.component_name = c.component_name
WHERE p.policy_name = 'WCAG AA Enterprise Policy';

-- Record an intentional failure for audit demonstration.
INSERT INTO accessibility_audits (
    component_id,
    severity,
    criterion,
    finding
)
SELECT
    component_id,
    'warning',
    'focus-appearance',
    'Legacy focus styling requires visual regression verification'
FROM components
WHERE component_name = 'TextField';

-- ============================================================
-- 18. INITIAL WORKFLOW PROCESSING
-- ============================================================

UPDATE components
SET status = 'review'
WHERE component_name IN ('Button', 'IconButton', 'TextField')
  AND status = 'draft';

-- Approval is transactional and validates accessibility and tokens.
CALL approve_component(
    (
        SELECT component_id
        FROM components
        WHERE component_name = 'Button'
    ),
    'design.lead'
);

CALL approve_component(
    (
        SELECT component_id
        FROM components
        WHERE component_name = 'IconButton'
    ),
    'platform.admin'
);

-- TextField intentionally remains under review.
-- It is valid in this dataset but has not yet received approval.

-- ============================================================
-- 19. SAMPLE RELEASE
-- ============================================================

INSERT INTO component_releases (
    component_id,
    version,
    released_by,
    release_notes
)
SELECT
    component_id,
    version,
    'platform.admin',
    'Initial approved component release'
FROM components
WHERE component_name IN ('Button', 'IconButton')
  AND status = 'approved';

COMMIT;

-- ============================================================
-- 20. RETRIEVAL QUERIES
-- ============================================================

-- List tokens belonging to the enterprise system.
SELECT
    token_name,
    category,
    token_value,
    alias_token_id
FROM design_tokens
WHERE system_id = (
    SELECT system_id
    FROM design_systems
    WHERE system_name = 'Enterprise UI System'
)
ORDER BY category, token_name;

-- List components with their category and status.
SELECT
    c.component_name,
    c.version,
    cc.category_name,
    c.status
FROM components c
JOIN component_categories cc
    ON cc.category_id = c.category_id
ORDER BY cc.category_name, c.component_name;

-- Retrieve component properties.
SELECT
    c.component_name,
    p.property_name,
    p.property_type,
    p.required,
    p.allowed_values
FROM components c
JOIN component_properties p
    ON p.component_id = c.component_id
ORDER BY c.component_name, p.property_name;

-- Resolve a token.
SELECT
    token_name,
    resolve_token(token_id) AS resolved_value
FROM design_tokens
WHERE token_name = 'color.action.primary';

-- Resolve a token in the dark theme.
SELECT
    resolve_token(
        t.token_id,
        th.theme_id
    ) AS dark_primary_color
FROM design_tokens t
JOIN themes th
    ON th.system_id = t.system_id
WHERE t.token_name = 'color.brand.primary'
  AND th.theme_name = 'dark';

-- ============================================================
-- 21. ACCESSIBILITY VALIDATION
-- ============================================================

SELECT
    c.component_name,
    findings.severity,
    findings.criterion,
    findings.finding
FROM components c
CROSS JOIN LATERAL validate_component(c.component_id) findings
ORDER BY c.component_name, findings.severity;

-- Components failing accessibility or dependency validation.
SELECT
    c.component_name,
    COUNT(*) FILTER (
        WHERE findings.severity = 'error'
    ) AS error_count
FROM components c
LEFT JOIN LATERAL validate_component(c.component_id)
    findings ON TRUE
GROUP BY c.component_id, c.component_name
HAVING COUNT(*) FILTER (
    WHERE findings.severity = 'error'
) > 0;

-- ============================================================
-- 22. AGGREGATION AND REPORTING
-- ============================================================

-- Component distribution by lifecycle state.
SELECT
    status,
    COUNT(*) AS component_count
FROM components
GROUP BY status
ORDER BY status;

-- Components per category.
SELECT
    cc.category_name,
    COUNT(c.component_id) AS component_count,
    COUNT(*) FILTER (
        WHERE c.status = 'approved'
    ) AS approved_count
FROM component_categories cc
LEFT JOIN components c
    ON c.category_id = cc.category_id
GROUP BY cc.category_id, cc.category_name
ORDER BY cc.category_name;

-- Accessibility audit severity distribution.
SELECT
    severity,
    COUNT(*) AS finding_count
FROM accessibility_audits
GROUP BY severity
ORDER BY severity;

-- Component release history.
SELECT
    c.component_name,
    r.version,
    r.released_by,
    r.released_at
FROM component_releases r
JOIN components c
    ON c.component_id = r.component_id
ORDER BY r.released_at DESC;

-- ============================================================
-- 23. RELEASE ELIGIBILITY
-- ============================================================

SELECT
    component_name,
    version,
    status,
    error_count,
    warning_count,
    release_eligible
FROM component_release_eligibility
ORDER BY component_name;

-- ============================================================
-- 24. DEPENDENCY ANALYSIS USING RECURSIVE CTE
-- ============================================================

WITH RECURSIVE dependency_tree AS (
    SELECT
        component_id,
        dependency_component_id,
        1 AS depth,
        ARRAY[component_id, dependency_component_id] AS path
    FROM component_dependencies

    UNION ALL

    SELECT
        dt.component_id,
        cd.dependency_component_id,
        dt.depth + 1,
        dt.path || cd.dependency_component_id
    FROM dependency_tree dt
    JOIN component_dependencies cd
        ON cd.component_id = dt.dependency_component_id
    WHERE NOT cd.dependency_component_id = ANY(dt.path)
)
SELECT
    source.component_name AS component,
    target.component_name AS dependency,
    dt.depth
FROM dependency_tree dt
JOIN components source
    ON source.component_id = dt.component_id
JOIN components target
    ON target.component_id = dt.dependency_component_id
ORDER BY source.component_name, dt.depth;

-- ============================================================
-- 25. WORKFLOW EVENT HISTORY
-- ============================================================

SELECT
    c.component_name,
    e.previous_status,
    e.new_status,
    e.actor,
    e.event_time
FROM component_events e
JOIN components c
    ON c.component_id = e.component_id
ORDER BY e.event_time DESC;

-- ============================================================
-- 26. TRANSACTIONAL FAILURE DEMONSTRATION
-- ============================================================

-- This transaction deliberately rolls back an invalid transition.
-- The database remains in its previously committed state.

BEGIN;

DO $$
DECLARE
    target_component BIGINT;
BEGIN
    SELECT component_id
    INTO target_component
    FROM components
    WHERE component_name = 'Button';

    BEGIN
        UPDATE components
        SET status = 'draft'
        WHERE component_id = target_component;

        RAISE EXCEPTION
            'Demonstration: operation deliberately rolled back';

    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE
            'Failure handled: %',
            SQLERRM;
    END;
END;
$$;

ROLLBACK;

-- ============================================================
-- 27. INDEX AND QUERY PERFORMANCE INSPECTION
-- ============================================================

EXPLAIN
SELECT
    component_name,
    status
FROM components
WHERE system_id = (
    SELECT system_id
    FROM design_systems
    WHERE system_name = 'Enterprise UI System'
)
AND status = 'approved';

EXPLAIN
SELECT
    token_name,
    token_value
FROM design_tokens
WHERE system_id = (
    SELECT system_id
    FROM design_systems
    WHERE system_name = 'Enterprise UI System'
)
AND category = 'color';

-- ============================================================
-- 28. OPERATIONAL GOVERNANCE NOTES
-- ============================================================

-- Application-level controls should additionally enforce:
-- 1. Tenant and organization authorization.
-- 2. Controlled component deletion and immutable release history.
-- 3. Token alias cycle prevention during token creation.
-- 4. Cross-system dependency prevention.
-- 5. Version compatibility and semantic release policies.
-- 6. Accessibility testing in actual rendered browser contexts.
-- 7. Atomic publication of tokens, themes and components.
-- 8. Audit retention and actor identity management.
--
-- PostgreSQL constraints enforce row-level integrity.
-- Complex dependency cycles and multi-record lifecycle rules
-- require transactional validation or additional triggers.
