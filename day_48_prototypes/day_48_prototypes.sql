-- PostgreSQL: model JavaScript-inspired prototype inheritance for configuration.
-- This is an explicit relational model, not native JavaScript object semantics.

BEGIN;

DROP VIEW IF EXISTS effective_configuration;
DROP FUNCTION IF EXISTS resolve_configuration(BIGINT, TEXT);
DROP TABLE IF EXISTS configuration_overrides;
DROP TABLE IF EXISTS configuration_profiles;

CREATE TABLE configuration_profiles (
    profile_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    profile_name TEXT NOT NULL UNIQUE,
    parent_profile_id BIGINT REFERENCES configuration_profiles(profile_id)
        ON DELETE RESTRICT,
    environment TEXT NOT NULL CHECK (
        environment IN ('development', 'staging', 'production')
    ),
    CHECK (
        parent_profile_id IS NULL OR parent_profile_id <> profile_id
    )
);

CREATE TABLE configuration_overrides (
    profile_id BIGINT NOT NULL REFERENCES configuration_profiles(profile_id)
        ON DELETE CASCADE,
    property_name TEXT NOT NULL CHECK (length(trim(property_name)) > 0),
    property_value TEXT NOT NULL,
    PRIMARY KEY (profile_id, property_name)
);

CREATE INDEX configuration_parent_idx
    ON configuration_profiles(parent_profile_id);

CREATE INDEX configuration_property_lookup_idx
    ON configuration_overrides(property_name, profile_id);

INSERT INTO configuration_profiles
    (profile_name, parent_profile_id, environment)
VALUES
    ('organization-defaults', NULL, 'development');

INSERT INTO configuration_overrides
    (profile_id, property_name, property_value)
SELECT profile_id, property_name, property_value
FROM configuration_profiles
CROSS JOIN (
    VALUES
        ('region', 'ap-south-1'),
        ('logLevel', 'INFO'),
        ('timeoutSeconds', '30')
) AS defaults(property_name, property_value)
WHERE profile_name = 'organization-defaults';

INSERT INTO configuration_profiles
    (profile_name, parent_profile_id, environment)
SELECT
    'payments-service',
    profile_id,
    'staging'
FROM configuration_profiles
WHERE profile_name = 'organization-defaults';

INSERT INTO configuration_overrides
    (profile_id, property_name, property_value)
SELECT profile_id, property_name, property_value
FROM configuration_profiles
CROSS JOIN (
    VALUES
        ('endpoint', 'https://api.internal.example'),
        ('logLevel', 'WARN')
) AS defaults(property_name, property_value)
WHERE profile_name = 'payments-service';

INSERT INTO configuration_profiles
    (profile_name, parent_profile_id, environment)
SELECT
    'payments-production',
    profile_id,
    'production'
FROM configuration_profiles
WHERE profile_name = 'payments-service';

INSERT INTO configuration_overrides
    (profile_id, property_name, property_value)
SELECT profile_id, property_name, property_value
FROM configuration_profiles
CROSS JOIN (
    VALUES
        ('timeoutSeconds', '45'),
        ('logLevel', 'ERROR')
) AS overrides(property_name, property_value)
WHERE profile_name = 'payments-production';

-- Resolve a property by searching the selected profile and its ancestors.
-- The nearest definition wins, matching prototype-chain shadowing.
CREATE FUNCTION resolve_configuration(
    selected_profile_id BIGINT,
    requested_property TEXT
)
RETURNS TABLE (
    property_value TEXT,
    source_profile TEXT,
    inheritance_depth INTEGER
)
LANGUAGE SQL
STABLE
AS $$
    WITH RECURSIVE profile_chain AS (
        SELECT
            p.profile_id,
            p.profile_name,
            p.parent_profile_id,
            0 AS depth,
            ARRAY[p.profile_id] AS visited
        FROM configuration_profiles AS p
        WHERE p.profile_id = selected_profile_id

        UNION ALL

        SELECT
            parent.profile_id,
            parent.profile_name,
            parent.parent_profile_id,
            chain.depth + 1,
            chain.visited || parent.profile_id
        FROM profile_chain AS chain
        JOIN configuration_profiles AS parent
            ON parent.profile_id = chain.parent_profile_id
        WHERE NOT parent.profile_id = ANY(chain.visited)
    )
    SELECT
        overrides.property_value,
        chain.profile_name,
        chain.depth
    FROM profile_chain AS chain
    JOIN configuration_overrides AS overrides
        ON overrides.profile_id = chain.profile_id
    WHERE overrides.property_name = requested_property
    ORDER BY chain.depth
    LIMIT 1;
$$;

CREATE VIEW effective_configuration AS
WITH RECURSIVE profile_chain AS (
    SELECT
        p.profile_id AS selected_profile_id,
        p.profile_name AS selected_profile,
        p.profile_id,
        p.parent_profile_id,
        0 AS depth,
        ARRAY[p.profile_id] AS visited
    FROM configuration_profiles AS p

    UNION ALL

    SELECT
        chain.selected_profile_id,
        chain.selected_profile,
        parent.profile_id,
        parent.parent_profile_id,
        chain.depth + 1,
        chain.visited || parent.profile_id
    FROM profile_chain AS chain
    JOIN configuration_profiles AS parent
        ON parent.profile_id = chain.parent_profile_id
    WHERE NOT parent.profile_id = ANY(chain.visited)
),
ranked_properties AS (
    SELECT
        chain.selected_profile_id,
        chain.selected_profile,
        overrides.property_name,
        overrides.property_value,
        chain.profile_name AS source_profile,
        chain.depth,
        row_number() OVER (
            PARTITION BY
                chain.selected_profile_id,
                overrides.property_name
            ORDER BY chain.depth
        ) AS precedence
    FROM profile_chain AS chain
    JOIN configuration_profiles AS source
        ON source.profile_id = chain.profile_id
    JOIN configuration_overrides AS overrides
        ON overrides.profile_id = source.profile_id
)
SELECT
    selected_profile_id,
    selected_profile,
    property_name,
    property_value,
    source_profile,
    depth AS inheritance_depth
FROM ranked_properties
WHERE precedence = 1;

-- Effective properties and their origin reveal exactly where shadowing occurs.
SELECT
    selected_profile,
    property_name,
    property_value,
    source_profile,
    inheritance_depth
FROM effective_configuration
WHERE selected_profile = 'payments-production'
ORDER BY property_name;

-- A targeted lookup returns the nearest timeout definition.
SELECT *
FROM resolve_configuration(
    (
        SELECT profile_id
        FROM configuration_profiles
        WHERE profile_name = 'payments-production'
    ),
    'timeoutSeconds'
);

-- Detect cyclic inheritance. This query traverses each profile's parent chain
-- and reports any profile encountered twice along the same path.
WITH RECURSIVE ancestry AS (
    SELECT
        profile_id AS start_id,
        profile_id AS current_id,
        parent_profile_id,
        ARRAY[profile_id] AS path,
        FALSE AS cycle_found
    FROM configuration_profiles

    UNION ALL

    SELECT
        ancestry.start_id,
        parent.profile_id,
        parent.parent_profile_id,
        ancestry.path || parent.profile_id,
        parent.profile_id = ANY(ancestry.path)
    FROM ancestry
    JOIN configuration_profiles AS parent
        ON parent.profile_id = ancestry.parent_profile_id
    WHERE NOT ancestry.cycle_found
)
SELECT start_id, path
FROM ancestry
WHERE cycle_found;

-- A direct self-reference is rejected by the CHECK constraint. Longer cycles
-- require a trigger or a controlled update procedure for full enforcement.
DO $$
BEGIN
    BEGIN
        UPDATE configuration_profiles
        SET parent_profile_id = profile_id
        WHERE profile_name = 'organization-defaults';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE 'Self-referential profile rejected as expected.';
    END;
END;
$$;

-- Application-level configuration validation can use the resolved values.
WITH selected AS (
    SELECT profile_id
    FROM configuration_profiles
    WHERE profile_name = 'payments-production'
),
required_values AS (
    SELECT
        (SELECT property_value FROM resolve_configuration(
            selected.profile_id, 'endpoint'
        )) AS endpoint,
        (SELECT property_value FROM resolve_configuration(
            selected.profile_id, 'timeoutSeconds'
        )) AS timeout_seconds
    FROM selected
)
SELECT
    endpoint,
    timeout_seconds,
    endpoint LIKE 'https://%' AS uses_https,
    CASE
        WHEN timeout_seconds ~ '^[0-9]+$'
        THEN timeout_seconds::INTEGER BETWEEN 1 AND 120
        ELSE FALSE
    END AS timeout_is_valid
FROM required_values;

COMMIT;
