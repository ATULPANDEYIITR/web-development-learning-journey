-- ============================================================
-- ADVANCED TYPE SYSTEM CONCEPTS
-- PostgreSQL implementation
--
-- Models:
-- 1. Generic-type-inspired JSONB structures
-- 2. Utility-type-inspired partial and selected projections
-- 3. Type narrowing through validated discriminators
-- 4. Type guards through database functions
-- 5. Conditional-type-inspired polymorphic processing
-- 6. Constraints, triggers, views, and reporting
--
-- PostgreSQL 14+
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS advanced_types;

SET search_path TO advanced_types, public;

-- ============================================================
-- 1. ENUMS: DISCRIMINATED VARIANTS
-- ============================================================

CREATE TYPE account_status AS ENUM (
    'ACTIVE',
    'SUSPENDED',
    'CLOSED'
);

CREATE TYPE payload_kind AS ENUM (
    'USER',
    'PRODUCT',
    'INVOICE'
);

CREATE TYPE operation_status AS ENUM (
    'SUCCESS',
    'FAILURE',
    'PENDING'
);

-- ============================================================
-- 2. CORE TABLES
-- ============================================================

CREATE TABLE users (
    user_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    full_name VARCHAR(150) NOT NULL,

    email VARCHAR(255) NOT NULL UNIQUE,

    department VARCHAR(100),

    phone VARCHAR(30),

    status account_status NOT NULL DEFAULT 'ACTIVE',

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_user_name
        CHECK (length(trim(full_name)) > 0),

    CONSTRAINT valid_email
        CHECK (
            email ~* '^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$'
        )
);

CREATE TABLE products (
    product_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    product_name VARCHAR(150) NOT NULL,

    price NUMERIC(14, 2) NOT NULL,

    active BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT valid_product_name
        CHECK (length(trim(product_name)) > 0),

    CONSTRAINT nonnegative_price
        CHECK (price >= 0)
);

-- ============================================================
-- 3. GENERIC PAYLOAD STORAGE
-- ============================================================

CREATE TABLE typed_payloads (
    payload_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    payload_name VARCHAR(150) NOT NULL,

    payload_type payload_kind NOT NULL,

    payload JSONB NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT payload_is_object
        CHECK (jsonb_typeof(payload) = 'object')
);

CREATE INDEX idx_payload_type
    ON typed_payloads(payload_type);

CREATE INDEX idx_payload_json
    ON typed_payloads USING GIN(payload);

-- ============================================================
-- 4. OPERATION RESULTS: DISCRIMINATED UNION
-- ============================================================

CREATE TABLE operation_results (
    result_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    operation_status operation_status NOT NULL,

    success_data JSONB,

    failure_message TEXT,

    error_code INTEGER,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_result_variant CHECK (
        (
            operation_status = 'SUCCESS'
            AND success_data IS NOT NULL
            AND failure_message IS NULL
            AND error_code IS NULL
        )
        OR
        (
            operation_status = 'FAILURE'
            AND success_data IS NULL
            AND failure_message IS NOT NULL
            AND error_code IS NOT NULL
        )
        OR
        (
            operation_status = 'PENDING'
            AND success_data IS NULL
            AND failure_message IS NULL
            AND error_code IS NULL
        )
    )
);

CREATE INDEX idx_result_status
    ON operation_results(operation_status, created_at DESC);

-- ============================================================
-- 5. GENERIC-STYLE ENTITY REGISTRY
-- ============================================================

CREATE TABLE entity_registry (
    entity_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    entity_type VARCHAR(50) NOT NULL,

    external_key VARCHAR(150) NOT NULL,

    attributes JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT unique_entity_key
        UNIQUE (entity_type, external_key),

    CONSTRAINT valid_entity_type
        CHECK (
            entity_type IN (
                'USER',
                'PRODUCT',
                'INVOICE',
                'TRANSACTION'
            )
        ),

    CONSTRAINT valid_attributes
        CHECK (jsonb_typeof(attributes) = 'object')
);

CREATE INDEX idx_entity_type
    ON entity_registry(entity_type);

-- ============================================================
-- 6. TYPE GUARDS
-- ============================================================

CREATE OR REPLACE FUNCTION is_valid_user_payload(
    input_payload JSONB
)
RETURNS BOOLEAN
LANGUAGE SQL
IMMUTABLE
AS $$
    SELECT
        jsonb_typeof(input_payload) = 'object'
        AND input_payload ? 'user_id'
        AND input_payload ? 'name'
        AND input_payload ? 'email'
        AND jsonb_typeof(input_payload->'user_id') = 'number'
        AND jsonb_typeof(input_payload->'name') = 'string'
        AND jsonb_typeof(input_payload->'email') = 'string'
        AND length(trim(input_payload->>'name')) > 0
        AND (input_payload->>'email') ~*
            '^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$'
        AND (input_payload->>'user_id') ~ '^[1-9][0-9]*$';
$$;

CREATE OR REPLACE FUNCTION is_valid_product_payload(
    input_payload JSONB
)
RETURNS BOOLEAN
LANGUAGE SQL
IMMUTABLE
AS $$
    SELECT
        jsonb_typeof(input_payload) = 'object'
        AND input_payload ? 'product_id'
        AND input_payload ? 'name'
        AND input_payload ? 'price'
        AND jsonb_typeof(input_payload->'product_id') = 'number'
        AND jsonb_typeof(input_payload->'name') = 'string'
        AND jsonb_typeof(input_payload->'price') = 'number'
        AND length(trim(input_payload->>'name')) > 0
        AND (input_payload->>'product_id') ~ '^[1-9][0-9]*$'
        AND (input_payload->>'price') ~ '^[0-9]+(\.[0-9]+)?$';
$$;

-- ============================================================
-- 7. TYPE-SPECIFIC PAYLOAD VALIDATION
-- ============================================================

CREATE OR REPLACE FUNCTION validate_typed_payload()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    CASE NEW.payload_type

        WHEN 'USER' THEN
            IF NOT is_valid_user_payload(NEW.payload) THEN
                RAISE EXCEPTION 'Invalid USER payload';
            END IF;

        WHEN 'PRODUCT' THEN
            IF NOT is_valid_product_payload(NEW.payload) THEN
                RAISE EXCEPTION 'Invalid PRODUCT payload';
            END IF;

        WHEN 'INVOICE' THEN
            IF NOT (
                NEW.payload ? 'invoice_id'
                AND NEW.payload ? 'amount'
                AND jsonb_typeof(NEW.payload->'invoice_id') = 'string'
                AND jsonb_typeof(NEW.payload->'amount') = 'number'
                AND length(trim(NEW.payload->>'invoice_id')) > 0
                AND (NEW.payload->>'amount') ~ '^[0-9]+(\.[0-9]+)?$'
            ) THEN
                RAISE EXCEPTION 'Invalid INVOICE payload';
            END IF;

    END CASE;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_payload
BEFORE INSERT OR UPDATE ON typed_payloads
FOR EACH ROW
EXECUTE FUNCTION validate_typed_payload();

-- ============================================================
-- 8. PARTIAL UPDATE: PARTIAL<T> EQUIVALENT
-- ============================================================

CREATE OR REPLACE PROCEDURE update_user_partial(
    p_user_id BIGINT,
    p_changes JSONB
)
LANGUAGE plpgsql
AS $$
DECLARE
    existing_user users%ROWTYPE;
    updated_name TEXT;
    updated_email TEXT;
    updated_department TEXT;
    updated_phone TEXT;
BEGIN
    IF jsonb_typeof(p_changes) <> 'object' THEN
        RAISE EXCEPTION 'Changes must be a JSON object';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM jsonb_object_keys(p_changes) AS k(key)
        WHERE key NOT IN (
            'full_name',
            'email',
            'department',
            'phone'
        )
    ) THEN
        RAISE EXCEPTION 'Unsupported update property';
    END IF;

    SELECT *
    INTO existing_user
    FROM users
    WHERE user_id = p_user_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'User not found: %', p_user_id;
    END IF;

    updated_name := CASE
        WHEN p_changes ? 'full_name'
            THEN p_changes->>'full_name'
        ELSE existing_user.full_name
    END;

    updated_email := CASE
        WHEN p_changes ? 'email'
            THEN p_changes->>'email'
        ELSE existing_user.email
    END;

    updated_department := CASE
        WHEN p_changes ? 'department'
            THEN p_changes->>'department'
        ELSE existing_user.department
    END;

    updated_phone := CASE
        WHEN p_changes ? 'phone'
            THEN p_changes->>'phone'
        ELSE existing_user.phone
    END;

    IF updated_name IS NULL OR length(trim(updated_name)) = 0 THEN
        RAISE EXCEPTION 'Name cannot be empty';
    END IF;

    IF updated_email IS NULL OR updated_email !~*
        '^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$' THEN
        RAISE EXCEPTION 'Invalid email';
    END IF;

    UPDATE users
    SET
        full_name = updated_name,
        email = updated_email,
        department = updated_department,
        phone = updated_phone
    WHERE user_id = p_user_id;
END;
$$;

-- ============================================================
-- 9. PICK<T, K> AND OMIT<T, K> EQUIVALENTS
-- ============================================================

CREATE OR REPLACE FUNCTION pick_json_fields(
    source JSONB,
    selected_fields TEXT[]
)
RETURNS JSONB
LANGUAGE SQL
IMMUTABLE
AS $$
    SELECT COALESCE(
        jsonb_object_agg(key, value),
        '{}'::jsonb
    )
    FROM jsonb_each(source)
    WHERE key = ANY(selected_fields);
$$;

CREATE OR REPLACE FUNCTION omit_json_fields(
    source JSONB,
    excluded_fields TEXT[]
)
RETURNS JSONB
LANGUAGE SQL
IMMUTABLE
AS $$
    SELECT COALESCE(
        jsonb_object_agg(key, value),
        '{}'::jsonb
    )
    FROM jsonb_each(source)
    WHERE NOT key = ANY(excluded_fields);
$$;

-- ============================================================
-- 10. CONDITIONAL-TYPE-INSPIRED TRANSFORMATION
-- ============================================================

CREATE OR REPLACE FUNCTION normalize_typed_value(
    input_value JSONB
)
RETURNS JSONB
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
    value_type TEXT;
BEGIN
    value_type := jsonb_typeof(input_value);

    CASE value_type

        WHEN 'string' THEN
            RETURN to_jsonb(lower(trim(input_value #>> '{}')));

        WHEN 'number' THEN
            RETURN to_jsonb(abs((input_value #>> '{}')::NUMERIC));

        WHEN 'boolean' THEN
            RETURN input_value;

        WHEN 'null' THEN
            RETURN 'null'::jsonb;

        ELSE
            RAISE EXCEPTION
                'Unsupported value type: %',
                value_type;

    END CASE;
END;
$$;

-- ============================================================
-- 11. REPORTING VIEW
-- ============================================================

CREATE OR REPLACE VIEW user_type_report AS
SELECT
    u.user_id,
    u.full_name,
    u.email,
    u.department,
    u.status,
    jsonb_build_object(
        'user_id', u.user_id,
        'name', u.full_name,
        'email', u.email
    ) AS public_profile
FROM users u;

-- ============================================================
-- 12. SAMPLE DATA
-- ============================================================

INSERT INTO users (
    full_name,
    email,
    department,
    phone,
    status
)
VALUES
    (
        'Aarav Sharma',
        'aarav@example.com',
        'Engineering',
        '+91-9000000001',
        'ACTIVE'
    ),
    (
        'Mira Verma',
        'mira@example.com',
        'Security',
        '+91-9000000002',
        'ACTIVE'
    ),
    (
        'Ravi Kumar',
        'ravi@example.com',
        'Research',
        NULL,
        'SUSPENDED'
    );

INSERT INTO products (
    product_name,
    price,
    active
)
VALUES
    ('Security Platform', 4999.00, TRUE),
    ('Analytics Service', 2499.00, TRUE),
    ('Legacy Package', 999.00, FALSE);

INSERT INTO typed_payloads (
    payload_name,
    payload_type,
    payload
)
VALUES
    (
        'External User',
        'USER',
        '{"user_id":101,"name":"Anika","email":"anika@example.com"}'
    ),
    (
        'External Product',
        'PRODUCT',
        '{"product_id":201,"name":"Audit System","price":1500.00}'
    ),
    (
        'Invoice Record',
        'INVOICE',
        '{"invoice_id":"INV-001","amount":7500.00}'
    );

INSERT INTO operation_results (
    operation_status,
    success_data
)
VALUES (
    'SUCCESS',
    '{"transaction_id":"TX-001","amount":5000}'
);

INSERT INTO operation_results (
    operation_status,
    failure_message,
    error_code
)
VALUES (
    'FAILURE',
    'Insufficient permissions',
    403
);

INSERT INTO operation_results (
    operation_status
)
VALUES ('PENDING');

INSERT INTO entity_registry (
    entity_type,
    external_key,
    attributes
)
VALUES
    (
        'USER',
        'U-001',
        '{"department":"Engineering","level":3}'
    ),
    (
        'PRODUCT',
        'P-001',
        '{"category":"Security","version":"2.0"}'
    ),
    (
        'TRANSACTION',
        'TX-001',
        '{"currency":"INR","amount":5000}'
    );

-- ============================================================
-- 13. GENERIC RETRIEVAL
-- ============================================================

SELECT *
FROM typed_payloads
ORDER BY payload_id;

SELECT
    entity_type,
    external_key,
    attributes
FROM entity_registry
WHERE entity_type = 'USER';

-- ============================================================
-- 14. TYPE GUARD VALIDATION
-- ============================================================

SELECT
    payload_id,
    payload_type,
    CASE
        WHEN payload_type = 'USER'
            THEN is_valid_user_payload(payload)
        WHEN payload_type = 'PRODUCT'
            THEN is_valid_product_payload(payload)
        ELSE TRUE
    END AS valid_payload
FROM typed_payloads;

-- ============================================================
-- 15. UTILITY-TYPE OPERATIONS
-- ============================================================

SELECT pick_json_fields(
    '{
        "name":"Mira",
        "email":"mira@example.com",
        "password":"secret",
        "department":"Security"
    }'::jsonb,
    ARRAY['name', 'email']
);

SELECT omit_json_fields(
    '{
        "name":"Mira",
        "email":"mira@example.com",
        "password":"secret"
    }'::jsonb,
    ARRAY['password']
);

-- ============================================================
-- 16. CONDITIONAL TYPE PROCESSING
-- ============================================================

SELECT normalize_typed_value('" TYPESCRIPT "'::jsonb);

SELECT normalize_typed_value('-125.50'::jsonb);

SELECT normalize_typed_value('true'::jsonb);

SELECT normalize_typed_value('null'::jsonb);

-- ============================================================
-- 17. AGGREGATION AND REPORTING
-- ============================================================

SELECT
    status,
    COUNT(*) AS user_count
FROM users
GROUP BY status
ORDER BY status;

SELECT
    entity_type,
    COUNT(*) AS entity_count
FROM entity_registry
GROUP BY entity_type
ORDER BY entity_type;

SELECT
    operation_status,
    COUNT(*) AS operation_count
FROM operation_results
GROUP BY operation_status;

SELECT *
FROM user_type_report
ORDER BY user_id;

-- ============================================================
-- 18. CTE-BASED TYPE EVALUATION
-- ============================================================

WITH payload_evaluation AS (
    SELECT
        payload_id,
        payload_type,
        payload,
        CASE
            WHEN payload_type = 'USER'
                THEN is_valid_user_payload(payload)
            WHEN payload_type = 'PRODUCT'
                THEN is_valid_product_payload(payload)
            ELSE TRUE
        END AS valid
    FROM typed_payloads
)
SELECT
    payload_type,
    COUNT(*) AS total_records,
    COUNT(*) FILTER (WHERE valid) AS valid_records,
    COUNT(*) FILTER (WHERE NOT valid) AS invalid_records
FROM payload_evaluation
GROUP BY payload_type;

-- ============================================================
-- 19. TRANSACTIONAL PARTIAL UPDATE
-- ============================================================

SAVEPOINT before_partial_update;

CALL update_user_partial(
    1,
    '{"department":"Advanced Engineering"}'::jsonb
);

SELECT
    user_id,
    full_name,
    department
FROM users
WHERE user_id = 1;

RELEASE SAVEPOINT before_partial_update;

-- ============================================================
-- 20. VALIDATION FAILURE EXAMPLES
-- ============================================================

-- Execute these separately to observe constraint failures.
-- INSERT INTO users(full_name, email)
-- VALUES ('', 'invalid@example.com');

-- INSERT INTO typed_payloads(payload_name, payload_type, payload)
-- VALUES ('Invalid User', 'USER', '{"name":"Missing ID"}');

-- UPDATE users SET email = 'invalid-email' WHERE user_id = 1;

-- ============================================================
-- 21. PERFORMANCE AND DATA INTEGRITY
-- ============================================================

CREATE INDEX idx_users_status_department
    ON users(status, department);

CREATE INDEX idx_products_active_price
    ON products(active, price)
    WHERE active = TRUE;

CREATE INDEX idx_payload_created
    ON typed_payloads(created_at DESC);

-- ============================================================
-- 22. FINAL VALIDATION
-- ============================================================

DO $$
BEGIN
    IF (SELECT COUNT(*) FROM users) < 3 THEN
        RAISE EXCEPTION 'User sample validation failed';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM typed_payloads
        WHERE payload_type = 'USER'
    ) THEN
        RAISE EXCEPTION 'User payload validation failed';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM operation_results
        WHERE operation_status = 'SUCCESS'
    ) THEN
        RAISE EXCEPTION 'Success result missing';
    END IF;

    RAISE NOTICE 'Advanced type database validation passed';
END;
$$;

COMMIT;

-- ============================================================
-- END
-- ============================================================
