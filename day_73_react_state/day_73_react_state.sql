-- ============================================================
-- REACT STATE MANAGEMENT
-- POSTGRESQL STATE MANAGEMENT AND AUDIT MODEL
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS react_state;

SET search_path TO react_state, public;


-- ============================================================
-- 1. ENUM TYPES
-- ============================================================

CREATE TYPE state_status AS ENUM (
    'active',
    'archived'
);

CREATE TYPE state_event_type AS ENUM (
    'initialized',
    'updated',
    'derived',
    'submitted',
    'reset'
);

CREATE TYPE form_status AS ENUM (
    'draft',
    'valid',
    'invalid',
    'submitted'
);


-- ============================================================
-- 2. APPLICATIONS
-- ============================================================

CREATE TABLE applications (
    application_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    application_name VARCHAR(100) NOT NULL UNIQUE,

    description TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT application_name_not_empty
        CHECK (LENGTH(TRIM(application_name)) > 0)
);


-- ============================================================
-- 3. STATE CONTAINERS
-- ============================================================

CREATE TABLE state_containers (
    container_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    application_id BIGINT NOT NULL
        REFERENCES applications(application_id),

    container_name VARCHAR(100) NOT NULL,

    state_status state_status NOT NULL DEFAULT 'active',

    current_version BIGINT NOT NULL DEFAULT 0,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (application_id, container_name),

    CONSTRAINT valid_version
        CHECK (current_version >= 0),

    CONSTRAINT valid_container_name
        CHECK (LENGTH(TRIM(container_name)) > 0)
);


-- ============================================================
-- 4. STATE SNAPSHOTS
--
-- JSONB supports structured application state.
-- Each version represents a stored state snapshot.
-- ============================================================

CREATE TABLE state_snapshots (
    snapshot_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    container_id BIGINT NOT NULL
        REFERENCES state_containers(container_id),

    version BIGINT NOT NULL,

    state_data JSONB NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT unique_container_version
        UNIQUE (container_id, version),

    CONSTRAINT valid_snapshot_object
        CHECK (jsonb_typeof(state_data) = 'object'),

    CONSTRAINT valid_snapshot_version
        CHECK (version >= 0)
);


CREATE INDEX idx_state_snapshots_container_version
    ON state_snapshots (
        container_id,
        version DESC
    );


-- ============================================================
-- 5. STATE EVENTS
--
-- Records the transition history separately from snapshots.
-- ============================================================

CREATE TABLE state_events (
    event_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    container_id BIGINT NOT NULL
        REFERENCES state_containers(container_id),

    event_type state_event_type NOT NULL,

    previous_version BIGINT NOT NULL,

    next_version BIGINT NOT NULL,

    changed_properties JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_event_versions
        CHECK (
            previous_version >= 0
            AND next_version >= previous_version
        ),

    CONSTRAINT valid_changed_properties
        CHECK (
            jsonb_typeof(changed_properties) = 'object'
        )
);


CREATE INDEX idx_state_events_container_time
    ON state_events (
        container_id,
        created_at DESC
    );


-- ============================================================
-- 6. CONTROLLED FORMS
-- ============================================================

CREATE TABLE controlled_forms (
    form_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    container_id BIGINT NOT NULL UNIQUE
        REFERENCES state_containers(container_id),

    username VARCHAR(50) NOT NULL DEFAULT '',

    email VARCHAR(254) NOT NULL DEFAULT '',

    age INTEGER,

    accepted_terms BOOLEAN NOT NULL DEFAULT FALSE,

    status form_status NOT NULL DEFAULT 'draft',

    validation_errors JSONB NOT NULL DEFAULT '{}'::jsonb,

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_username
        CHECK (LENGTH(TRIM(username)) <= 50),

    CONSTRAINT valid_age
        CHECK (age IS NULL OR age BETWEEN 18 AND 120),

    CONSTRAINT valid_errors_object
        CHECK (
            jsonb_typeof(validation_errors) = 'object'
        )
);


CREATE INDEX idx_controlled_forms_status
    ON controlled_forms(status);


-- ============================================================
-- 7. SHOPPING CART
-- ============================================================

CREATE TABLE cart_items (
    cart_item_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    container_id BIGINT NOT NULL
        REFERENCES state_containers(container_id),

    product_id VARCHAR(50) NOT NULL,

    product_name VARCHAR(150) NOT NULL,

    unit_price NUMERIC(12, 2) NOT NULL,

    quantity INTEGER NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT unique_cart_product
        UNIQUE (container_id, product_id),

    CONSTRAINT valid_unit_price
        CHECK (unit_price >= 0),

    CONSTRAINT valid_quantity
        CHECK (quantity BETWEEN 1 AND 1000000),

    CONSTRAINT valid_product_name
        CHECK (LENGTH(TRIM(product_name)) > 0)
);


CREATE INDEX idx_cart_items_container
    ON cart_items(container_id);


-- ============================================================
-- 8. STATE UPDATE FUNCTION
--
-- Optimistic version checking prevents stale writes.
-- The snapshot and event are created atomically.
-- ============================================================

CREATE OR REPLACE FUNCTION update_application_state(
    p_container_id BIGINT,
    p_expected_version BIGINT,
    p_new_state JSONB,
    p_changed_properties JSONB DEFAULT '{}'::jsonb
)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    v_current_version BIGINT;
    v_next_version BIGINT;
BEGIN
    IF p_new_state IS NULL
       OR jsonb_typeof(p_new_state) <> 'object' THEN
        RAISE EXCEPTION
            'New state must be a JSON object.';
    END IF;

    IF p_changed_properties IS NULL
       OR jsonb_typeof(p_changed_properties) <> 'object' THEN
        RAISE EXCEPTION
            'Changed properties must be a JSON object.';
    END IF;

    SELECT current_version
    INTO v_current_version
    FROM state_containers
    WHERE container_id = p_container_id
      AND state_status = 'active'
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Active state container % not found.',
            p_container_id;
    END IF;

    IF v_current_version <> p_expected_version THEN
        RAISE EXCEPTION
            'State conflict. Expected version %, actual version %.',
            p_expected_version,
            v_current_version;
    END IF;

    v_next_version := v_current_version + 1;

    INSERT INTO state_snapshots (
        container_id,
        version,
        state_data
    )
    VALUES (
        p_container_id,
        v_next_version,
        p_new_state
    );

    INSERT INTO state_events (
        container_id,
        event_type,
        previous_version,
        next_version,
        changed_properties
    )
    VALUES (
        p_container_id,
        'updated',
        v_current_version,
        v_next_version,
        p_changed_properties
    );

    UPDATE state_containers
    SET
        current_version = v_next_version,
        updated_at = NOW()
    WHERE container_id = p_container_id;

    RETURN v_next_version;
END;
$$;


-- ============================================================
-- 9. INITIALIZE STATE FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION initialize_application_state(
    p_container_id BIGINT,
    p_initial_state JSONB
)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    v_version BIGINT;
BEGIN
    IF p_initial_state IS NULL
       OR jsonb_typeof(p_initial_state) <> 'object' THEN
        RAISE EXCEPTION
            'Initial state must be a JSON object.';
    END IF;

    PERFORM 1
    FROM state_containers
    WHERE container_id = p_container_id
      AND state_status = 'active'
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Active container not found.';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM state_snapshots
        WHERE container_id = p_container_id
    ) THEN
        RAISE EXCEPTION
            'State container is already initialized.';
    END IF;

    INSERT INTO state_snapshots (
        container_id,
        version,
        state_data
    )
    VALUES (
        p_container_id,
        0,
        p_initial_state
    );

    INSERT INTO state_events (
        container_id,
        event_type,
        previous_version,
        next_version,
        changed_properties
    )
    VALUES (
        p_container_id,
        'initialized',
        0,
        0,
        p_initial_state
    );

    RETURN 0;
END;
$$;


-- ============================================================
-- 10. CONTROLLED FORM VALIDATION
-- ============================================================

CREATE OR REPLACE FUNCTION validate_controlled_form(
    p_username VARCHAR,
    p_email VARCHAR,
    p_age INTEGER,
    p_accepted_terms BOOLEAN
)
RETURNS JSONB
LANGUAGE plpgsql
AS $$
DECLARE
    v_errors JSONB := '{}'::jsonb;
BEGIN
    IF p_username IS NULL
       OR LENGTH(TRIM(p_username)) = 0 THEN

        v_errors := v_errors ||
            '{"username":"Username is required"}'::jsonb;

    ELSIF LENGTH(p_username) > 50 THEN

        v_errors := v_errors ||
            '{"username":"Username is too long"}'::jsonb;

    END IF;

    IF p_email IS NULL
       OR p_email !~ '^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$'
       OR LENGTH(p_email) > 254 THEN

        v_errors := v_errors ||
            '{"email":"Invalid email address"}'::jsonb;

    END IF;

    IF p_age IS NULL OR p_age NOT BETWEEN 18 AND 120 THEN

        v_errors := v_errors ||
            '{"age":"Age must be between 18 and 120"}'::jsonb;

    END IF;

    IF NOT COALESCE(p_accepted_terms, FALSE) THEN

        v_errors := v_errors ||
            '{"accepted_terms":"Terms acceptance required"}'::jsonb;

    END IF;

    RETURN v_errors;
END;
$$;


-- ============================================================
-- 11. CONTROLLED FORM SUBMISSION PROCEDURE
-- ============================================================

CREATE OR REPLACE PROCEDURE submit_controlled_form(
    p_form_id BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_form controlled_forms%ROWTYPE;
    v_errors JSONB;
BEGIN
    SELECT *
    INTO v_form
    FROM controlled_forms
    WHERE form_id = p_form_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Form % not found.', p_form_id;
    END IF;

    v_errors := validate_controlled_form(
        v_form.username,
        v_form.email,
        v_form.age,
        v_form.accepted_terms
    );

    IF v_errors <> '{}'::jsonb THEN

        UPDATE controlled_forms
        SET
            status = 'invalid',
            validation_errors = v_errors,
            updated_at = NOW()
        WHERE form_id = p_form_id;

        RETURN;
    END IF;

    UPDATE controlled_forms
    SET
        status = 'submitted',
        validation_errors = '{}'::jsonb,
        updated_at = NOW()
    WHERE form_id = p_form_id;
END;
$$;


-- ============================================================
-- 12. CART DERIVED STATE VIEW
--
-- Total items and subtotal are calculated rather than stored.
-- ============================================================

CREATE OR REPLACE VIEW cart_derived_state AS
SELECT
    sc.container_id,

    COALESCE(SUM(ci.quantity), 0)::BIGINT
        AS total_items,

    COALESCE(
        SUM(ci.unit_price * ci.quantity),
        0
    )::NUMERIC(14, 2) AS subtotal,

    COUNT(ci.cart_item_id) > 0 AS has_items

FROM state_containers sc

LEFT JOIN cart_items ci
    ON ci.container_id = sc.container_id

GROUP BY sc.container_id;


-- ============================================================
-- 13. STATE HISTORY VIEW
-- ============================================================

CREATE OR REPLACE VIEW state_history AS
SELECT
    sc.container_name,
    ss.container_id,
    ss.version,
    ss.state_data,
    ss.created_at

FROM state_snapshots ss

JOIN state_containers sc
    ON sc.container_id = ss.container_id;


-- ============================================================
-- 14. CREATE APPLICATION AND STATE CONTAINERS
-- ============================================================

INSERT INTO applications (
    application_name,
    description
)
VALUES
(
    'React State Learning',
    'State management and controlled component demonstration'
)
ON CONFLICT (application_name) DO NOTHING;


INSERT INTO state_containers (
    application_id,
    container_name
)
SELECT
    application_id,
    container_name
FROM applications
CROSS JOIN (
    VALUES
        ('counter'),
        ('registration-form'),
        ('shopping-cart'),
        ('user-profile')
) AS containers(container_name)

WHERE application_name = 'React State Learning'

ON CONFLICT (application_id, container_name) DO NOTHING;


-- ============================================================
-- 15. INITIALIZE SNAPSHOTS
-- ============================================================

DO $$
DECLARE
    v_container_id BIGINT;
    v_initial_state JSONB;
BEGIN
    SELECT container_id
    INTO v_container_id
    FROM state_containers
    WHERE container_name = 'counter';

    IF NOT EXISTS (
        SELECT 1
        FROM state_snapshots
        WHERE container_id = v_container_id
    ) THEN
        PERFORM initialize_application_state(
            v_container_id,
            '{"count":0}'::jsonb
        );
    END IF;

    SELECT container_id
    INTO v_container_id
    FROM state_containers
    WHERE container_name = 'registration-form';

    IF NOT EXISTS (
        SELECT 1
        FROM state_snapshots
        WHERE container_id = v_container_id
    ) THEN
        PERFORM initialize_application_state(
            v_container_id,
            '{
                "username":"",
                "email":"",
                "age":null,
                "accepted_terms":false
            }'::jsonb
        );
    END IF;

    SELECT container_id
    INTO v_container_id
    FROM state_containers
    WHERE container_name = 'shopping-cart';

    IF NOT EXISTS (
        SELECT 1
        FROM state_snapshots
        WHERE container_id = v_container_id
    ) THEN
        PERFORM initialize_application_state(
            v_container_id,
            '{"items":[]}'::jsonb
        );
    END IF;

    SELECT container_id
    INTO v_container_id
    FROM state_containers
    WHERE container_name = 'user-profile';

    IF NOT EXISTS (
        SELECT 1
        FROM state_snapshots
        WHERE container_id = v_container_id
    ) THEN
        PERFORM initialize_application_state(
            v_container_id,
            '{
                "name":"Atul",
                "address":{
                    "city":"Lucknow",
                    "country":"India"
                }
            }'::jsonb
        );
    END IF;
END;
$$;


-- ============================================================
-- 16. INSERT CONTROLLED FORM SAMPLE RECORDS
-- ============================================================

INSERT INTO controlled_forms (
    container_id,
    username,
    email,
    age,
    accepted_terms
)
SELECT
    container_id,
    'Atul',
    'atul@example.com',
    28,
    TRUE
FROM state_containers
WHERE container_name = 'registration-form'
ON CONFLICT (container_id) DO NOTHING;


-- ============================================================
-- 17. INSERT CART SAMPLE RECORDS
-- ============================================================

INSERT INTO cart_items (
    container_id,
    product_id,
    product_name,
    unit_price,
    quantity
)
SELECT
    container_id,
    sample.product_id,
    sample.product_name,
    sample.unit_price,
    sample.quantity
FROM state_containers sc

CROSS JOIN (
    VALUES
        (
            'P001',
            'Mechanical Keyboard',
            2499.00::NUMERIC,
            2
        ),
        (
            'P002',
            'Wireless Mouse',
            999.00::NUMERIC,
            2
        )
) AS sample(
    product_id,
    product_name,
    unit_price,
    quantity
)

WHERE sc.container_name = 'shopping-cart'

ON CONFLICT (container_id, product_id) DO NOTHING;


-- ============================================================
-- 18. UPDATE COUNTER USING OPTIMISTIC VERSION CONTROL
-- ============================================================

DO $$
DECLARE
    v_container_id BIGINT;
    v_version BIGINT;
BEGIN
    SELECT container_id, current_version
    INTO v_container_id, v_version
    FROM state_containers
    WHERE container_name = 'counter';

    PERFORM update_application_state(
        v_container_id,
        v_version,
        '{"count":5}'::jsonb,
        '{"count":{"previous":0,"next":5}}'::jsonb
    );
END;
$$;


-- ============================================================
-- 19. SUBMIT CONTROLLED FORM
-- ============================================================

DO $$
DECLARE
    v_form_id BIGINT;
BEGIN
    SELECT form_id
    INTO v_form_id
    FROM controlled_forms
    LIMIT 1;

    IF v_form_id IS NOT NULL THEN
        CALL submit_controlled_form(v_form_id);
    END IF;
END;
$$;


-- ============================================================
-- 20. RETRIEVAL: CURRENT APPLICATION STATE
-- ============================================================

SELECT
    sc.container_name,
    sc.current_version,
    ss.state_data,
    sc.updated_at

FROM state_containers sc

LEFT JOIN state_snapshots ss
    ON ss.container_id = sc.container_id
   AND ss.version = sc.current_version

ORDER BY sc.container_id;


-- ============================================================
-- 21. RETRIEVAL: STATE EVENT HISTORY
-- ============================================================

SELECT
    sc.container_name,
    se.event_type,
    se.previous_version,
    se.next_version,
    se.changed_properties,
    se.created_at

FROM state_events se

JOIN state_containers sc
    ON sc.container_id = se.container_id

ORDER BY se.created_at DESC;


-- ============================================================
-- 22. VALIDATION REPORT
-- ============================================================

SELECT
    form_id,
    username,
    email,
    age,
    status,
    validation_errors

FROM controlled_forms

ORDER BY form_id;


-- ============================================================
-- 23. DERIVED STATE AGGREGATION
-- ============================================================

SELECT
    sc.container_name,
    cds.total_items,
    cds.subtotal,
    cds.has_items

FROM cart_derived_state cds

JOIN state_containers sc
    ON sc.container_id = cds.container_id

WHERE sc.container_name = 'shopping-cart';


-- ============================================================
-- 24. JSONB STATE PROPERTY RETRIEVAL
-- ============================================================

SELECT
    container_name,
    state_data ->> 'count' AS counter_value

FROM state_history

WHERE container_name = 'counter'

ORDER BY version DESC;


-- ============================================================
-- 25. LATEST SNAPSHOT USING CTE
-- ============================================================

WITH ranked_snapshots AS (
    SELECT
        container_id,
        version,
        state_data,
        ROW_NUMBER() OVER (
            PARTITION BY container_id
            ORDER BY version DESC
        ) AS row_number

    FROM state_snapshots
)

SELECT
    sc.container_name,
    rs.version,
    rs.state_data

FROM ranked_snapshots rs

JOIN state_containers sc
    ON sc.container_id = rs.container_id

WHERE rs.row_number = 1;


-- ============================================================
-- 26. ELIGIBILITY DETERMINATION
-- ============================================================

SELECT
    form_id,
    username,

    CASE
        WHEN status = 'submitted'
             AND accepted_terms = TRUE
             AND age >= 18
        THEN 'ELIGIBLE'

        WHEN status = 'invalid'
        THEN 'VALIDATION_FAILED'

        ELSE 'NOT_ELIGIBLE'
    END AS submission_eligibility

FROM controlled_forms;


-- ============================================================
-- 27. INVALID CART RECORD CHECK
-- ============================================================

SELECT
    cart_item_id,
    product_name,
    unit_price,
    quantity

FROM cart_items

WHERE unit_price < 0
   OR quantity <= 0
   OR LENGTH(TRIM(product_name)) = 0;


-- ============================================================
-- 28. STATE UPDATE TRANSACTION DEMONSTRATION
--
-- A failure rolls back the complete transaction.
-- ============================================================

DO $$
DECLARE
    v_container_id BIGINT;
    v_version BIGINT;
BEGIN
    SELECT container_id, current_version
    INTO v_container_id, v_version
    FROM state_containers
    WHERE container_name = 'user-profile';

    PERFORM update_application_state(
        v_container_id,
        v_version,
        '{
            "name":"Atul",
            "address":{
                "city":"Patna",
                "country":"India"
            }
        }'::jsonb,
        '{
            "address":{
                "city":"Patna"
            }
        }'::jsonb
    );
END;
$$;


-- ============================================================
-- 29. STATE CONTAINER REPORT
-- ============================================================

SELECT
    sc.container_name,
    sc.state_status,
    sc.current_version,
    COUNT(ss.snapshot_id) AS snapshot_count,
    MAX(ss.created_at) AS latest_snapshot

FROM state_containers sc

LEFT JOIN state_snapshots ss
    ON ss.container_id = sc.container_id

GROUP BY
    sc.container_id,
    sc.container_name,
    sc.state_status,
    sc.current_version

ORDER BY sc.container_id;


-- ============================================================
-- 30. PERFORMANCE AND OPERATIONAL CONSIDERATIONS
--
-- - JSONB supports structured state inspection.
-- - Version indexes support snapshot retrieval.
-- - Row-level locks serialize updates to one container.
-- - Optimistic version checks detect stale writes.
-- - Derived values are calculated at query time.
-- - Database transactions preserve snapshot consistency.
-- ============================================================

COMMIT;
