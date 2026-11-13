-- ============================================================
-- REACT EVENTS AND FORMS
-- PostgreSQL 16+
--
-- Relational model for:
--   Form definitions
--   Input fields
--   Controlled and uncontrolled inputs
--   Validation policies
--   User sessions
--   Form state transitions
--   Event records
--   Form submissions
--   Field-level validation errors
--   Asynchronous validation results
--
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS react_forms;

SET search_path TO react_forms, public;

-- ------------------------------------------------------------
-- 1. ENUM TYPES
-- ------------------------------------------------------------

CREATE TYPE input_type AS ENUM (
    'text',
    'email',
    'password',
    'number',
    'checkbox',
    'select',
    'textarea'
);

CREATE TYPE form_status AS ENUM (
    'idle',
    'dirty',
    'validating',
    'invalid',
    'submitting',
    'submitted'
);

CREATE TYPE control_mode AS ENUM (
    'controlled',
    'uncontrolled'
);

CREATE TYPE event_type AS ENUM (
    'click',
    'input',
    'change',
    'focus',
    'blur',
    'submit',
    'reset'
);

CREATE TYPE submission_status AS ENUM (
    'pending',
    'validated',
    'rejected',
    'processing',
    'completed',
    'failed'
);

-- ------------------------------------------------------------
-- 2. FORM DEFINITIONS
-- ------------------------------------------------------------

CREATE TABLE forms (
    form_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    form_key VARCHAR(100) NOT NULL UNIQUE,

    form_name VARCHAR(150) NOT NULL,

    description TEXT,

    version INTEGER NOT NULL DEFAULT 1,

    active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_form_version CHECK (version > 0),

    CONSTRAINT valid_form_name CHECK (
        LENGTH(TRIM(form_name)) > 0
    )
);

-- ------------------------------------------------------------
-- 3. FORM FIELDS
-- ------------------------------------------------------------

CREATE TABLE form_fields (
    field_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    form_id BIGINT NOT NULL REFERENCES forms(form_id)
        ON DELETE CASCADE,

    field_key VARCHAR(100) NOT NULL,

    label VARCHAR(150) NOT NULL,

    field_type input_type NOT NULL,

    control_mode control_mode NOT NULL DEFAULT 'controlled',

    required BOOLEAN NOT NULL DEFAULT FALSE,

    default_value JSONB,

    max_length INTEGER NOT NULL DEFAULT 255,

    display_order INTEGER NOT NULL DEFAULT 0,

    enabled BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT unique_form_field UNIQUE (
        form_id,
        field_key
    ),

    CONSTRAINT positive_field_length CHECK (
        max_length > 0
    ),

    CONSTRAINT valid_display_order CHECK (
        display_order >= 0
    )
);

CREATE INDEX idx_form_fields_order
ON form_fields(form_id, display_order);

-- ------------------------------------------------------------
-- 4. VALIDATION POLICIES
-- ------------------------------------------------------------

CREATE TABLE validation_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    field_id BIGINT NOT NULL REFERENCES form_fields(field_id)
        ON DELETE CASCADE,

    minimum_length INTEGER,

    maximum_length INTEGER,

    minimum_numeric NUMERIC,

    maximum_numeric NUMERIC,

    email_validation BOOLEAN NOT NULL DEFAULT FALSE,

    regex_pattern TEXT,

    custom_error_message TEXT,

    enabled BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT valid_length_range CHECK (
        minimum_length IS NULL
        OR maximum_length IS NULL
        OR minimum_length <= maximum_length
    ),

    CONSTRAINT valid_numeric_range CHECK (
        minimum_numeric IS NULL
        OR maximum_numeric IS NULL
        OR minimum_numeric <= maximum_numeric
    )
);

CREATE INDEX idx_validation_policies_field
ON validation_policies(field_id)
WHERE enabled = TRUE;

-- ------------------------------------------------------------
-- 5. FORM SESSIONS
-- ------------------------------------------------------------

CREATE TABLE form_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    form_id BIGINT NOT NULL REFERENCES forms(form_id),

    session_reference VARCHAR(120) NOT NULL UNIQUE,

    current_status form_status NOT NULL DEFAULT 'idle',

    revision BIGINT NOT NULL DEFAULT 0,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_revision CHECK (revision >= 0)
);

CREATE INDEX idx_sessions_form_status
ON form_sessions(form_id, current_status);

CREATE INDEX idx_sessions_updated
ON form_sessions(updated_at DESC);

-- ------------------------------------------------------------
-- 6. FIELD VALUES
-- ------------------------------------------------------------

CREATE TABLE field_values (
    session_id UUID NOT NULL REFERENCES form_sessions(session_id)
        ON DELETE CASCADE,

    field_id BIGINT NOT NULL REFERENCES form_fields(field_id),

    value JSONB,

    touched BOOLEAN NOT NULL DEFAULT FALSE,

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY(session_id, field_id)
);

CREATE INDEX idx_field_values_field
ON field_values(field_id);

-- ------------------------------------------------------------
-- 7. EVENT LOG
-- ------------------------------------------------------------

CREATE TABLE form_events (
    event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    session_id UUID NOT NULL REFERENCES form_sessions(session_id)
        ON DELETE CASCADE,

    field_id BIGINT REFERENCES form_fields(field_id),

    event event_type NOT NULL,

    event_payload JSONB NOT NULL DEFAULT '{}'::jsonb,

    bubbles BOOLEAN NOT NULL DEFAULT TRUE,

    default_prevented BOOLEAN NOT NULL DEFAULT FALSE,

    propagation_stopped BOOLEAN NOT NULL DEFAULT FALSE,

    event_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_event_payload CHECK (
        jsonb_typeof(event_payload) = 'object'
    )
);

CREATE INDEX idx_events_session_time
ON form_events(session_id, event_timestamp DESC);

CREATE INDEX idx_events_type
ON form_events(event, event_timestamp DESC);

-- ------------------------------------------------------------
-- 8. SUBMISSIONS
-- ------------------------------------------------------------

CREATE TABLE form_submissions (
    submission_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    session_id UUID NOT NULL REFERENCES form_sessions(session_id),

    submission_number INTEGER NOT NULL,

    submitted_revision BIGINT NOT NULL,

    status submission_status NOT NULL DEFAULT 'pending',

    submitted_payload JSONB NOT NULL,

    idempotency_key UUID NOT NULL DEFAULT gen_random_uuid(),

    failure_reason TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    processed_at TIMESTAMPTZ,

    CONSTRAINT unique_session_submission UNIQUE (
        session_id,
        submission_number
    ),

    CONSTRAINT unique_idempotency_key UNIQUE (
        idempotency_key
    ),

    CONSTRAINT valid_submission_number CHECK (
        submission_number > 0
    ),

    CONSTRAINT valid_submitted_revision CHECK (
        submitted_revision >= 0
    ),

    CONSTRAINT valid_submission_payload CHECK (
        jsonb_typeof(submitted_payload) = 'object'
    )
);

CREATE INDEX idx_submission_status
ON form_submissions(status, created_at DESC);

CREATE INDEX idx_submission_session
ON form_submissions(session_id, submission_number DESC);

-- ------------------------------------------------------------
-- 9. VALIDATION ERRORS
-- ------------------------------------------------------------

CREATE TABLE validation_errors (
    error_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    submission_id BIGINT NOT NULL
        REFERENCES form_submissions(submission_id)
        ON DELETE CASCADE,

    field_id BIGINT REFERENCES form_fields(field_id),

    error_code VARCHAR(60) NOT NULL,

    error_message TEXT NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_validation_errors_submission
ON validation_errors(submission_id);

-- ------------------------------------------------------------
-- 10. STATE TRANSITION AUDIT
-- ------------------------------------------------------------

CREATE TABLE form_state_history (
    history_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    session_id UUID NOT NULL REFERENCES form_sessions(session_id),

    previous_status form_status,

    next_status form_status NOT NULL,

    revision BIGINT NOT NULL,

    changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_state_history_session
ON form_state_history(session_id, changed_at DESC);

-- ------------------------------------------------------------
-- 11. STATE TRANSITION FUNCTION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_form_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    valid_transition BOOLEAN;
BEGIN
    IF NEW.current_status = OLD.current_status THEN
        RETURN NEW;
    END IF;

    valid_transition := CASE OLD.current_status

        WHEN 'idle' THEN
            NEW.current_status IN ('dirty', 'validating')

        WHEN 'dirty' THEN
            NEW.current_status IN (
                'dirty', 'idle', 'validating'
            )

        WHEN 'validating' THEN
            NEW.current_status IN (
                'dirty', 'invalid', 'idle'
            )

        WHEN 'invalid' THEN
            NEW.current_status IN (
                'dirty', 'idle', 'validating'
            )

        WHEN 'submitting' THEN
            NEW.current_status IN (
                'submitted', 'dirty', 'invalid'
            )

        WHEN 'submitted' THEN
            NEW.current_status IN (
                'dirty', 'idle', 'validating'
            )

        ELSE FALSE

    END;

    IF NOT valid_transition THEN
        RAISE EXCEPTION
            'Invalid form transition: % -> %',
            OLD.current_status,
            NEW.current_status;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_form_transition
BEFORE UPDATE OF current_status
ON form_sessions
FOR EACH ROW
EXECUTE FUNCTION validate_form_transition();

-- ------------------------------------------------------------
-- 12. SESSION AUDIT TRIGGER
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION audit_form_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.current_status IS DISTINCT FROM NEW.current_status
       OR OLD.revision IS DISTINCT FROM NEW.revision THEN

        INSERT INTO form_state_history (
            session_id,
            previous_status,
            next_status,
            revision
        )
        VALUES (
            NEW.session_id,
            OLD.current_status,
            NEW.current_status,
            NEW.revision
        );
    END IF;

    NEW.updated_at := NOW();

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_audit_form_transition
BEFORE UPDATE
ON form_sessions
FOR EACH ROW
EXECUTE FUNCTION audit_form_transition();

-- ------------------------------------------------------------
-- 13. FIELD VALUE INTEGRITY TRIGGER
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_field_value()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    field_record form_fields%ROWTYPE;
    session_form_id BIGINT;
    input_text TEXT;
BEGIN
    SELECT *
    INTO field_record
    FROM form_fields
    WHERE field_id = NEW.field_id
      AND enabled = TRUE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Field does not exist or is disabled';
    END IF;

    SELECT form_id
    INTO session_form_id
    FROM form_sessions
    WHERE session_id = NEW.session_id;

    IF session_form_id IS DISTINCT FROM field_record.form_id THEN
        RAISE EXCEPTION
            'Field does not belong to the session form';
    END IF;

    IF NEW.value IS NULL THEN
        IF field_record.required THEN
            RAISE EXCEPTION 'Required field cannot be NULL';
        END IF;

        RETURN NEW;
    END IF;

    IF field_record.field_type = 'checkbox'
       AND jsonb_typeof(NEW.value) <> 'boolean' THEN

        RAISE EXCEPTION 'Checkbox requires a boolean value';
    END IF;

    IF field_record.field_type IN (
        'text', 'email', 'password', 'textarea', 'select'
    ) THEN

        IF jsonb_typeof(NEW.value) <> 'string' THEN
            RAISE EXCEPTION
                'Text field requires a JSON string';
        END IF;

        input_text := NEW.value #>> '{}';

        IF field_record.required
           AND LENGTH(TRIM(input_text)) = 0 THEN

            RAISE EXCEPTION 'Required field cannot be empty';
        END IF;

        IF LENGTH(input_text) > field_record.max_length THEN
            RAISE EXCEPTION 'Maximum field length exceeded';
        END IF;
    END IF;

    IF field_record.field_type = 'number'
       AND jsonb_typeof(NEW.value) <> 'number' THEN

        RAISE EXCEPTION 'Number field requires a JSON number';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_field_value
BEFORE INSERT OR UPDATE OF value
ON field_values
FOR EACH ROW
EXECUTE FUNCTION validate_field_value();

-- ------------------------------------------------------------
-- 14. FIELD VALIDATION FUNCTION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_submission(
    p_session_id UUID
)
RETURNS TABLE (
    field_name VARCHAR,
    error_code VARCHAR,
    error_message TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN

    RETURN QUERY

    SELECT
        f.field_key::VARCHAR,
        'REQUIRED'::VARCHAR,
        'This field is required'::TEXT

    FROM form_fields f

    LEFT JOIN field_values v
        ON v.field_id = f.field_id
       AND v.session_id = p_session_id

    WHERE f.form_id = (
        SELECT form_id
        FROM form_sessions
        WHERE session_id = p_session_id
    )

    AND f.enabled = TRUE

    AND f.required = TRUE

    AND (
        v.value IS NULL
        OR (
            jsonb_typeof(v.value) = 'string'
            AND LENGTH(TRIM(v.value #>> '{}')) = 0
        )
    )

    UNION ALL

    SELECT
        f.field_key::VARCHAR,
        'EMAIL'::VARCHAR,
        'Invalid email address'::TEXT

    FROM form_fields f

    JOIN field_values v
        ON v.field_id = f.field_id
       AND v.session_id = p_session_id

    JOIN validation_policies p
        ON p.field_id = f.field_id
       AND p.enabled = TRUE

    WHERE p.email_validation = TRUE

    AND (
        v.value #>> '{}'
    ) !~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'

    UNION ALL

    SELECT
        f.field_key::VARCHAR,
        'MIN_LENGTH'::VARCHAR,
        'Minimum length not satisfied'::TEXT

    FROM form_fields f

    JOIN field_values v
        ON v.field_id = f.field_id
       AND v.session_id = p_session_id

    JOIN validation_policies p
        ON p.field_id = f.field_id
       AND p.enabled = TRUE

    WHERE p.minimum_length IS NOT NULL

    AND jsonb_typeof(v.value) = 'string'

    AND LENGTH(v.value #>> '{}') < p.minimum_length

    UNION ALL

    SELECT
        f.field_key::VARCHAR,
        'MAX_LENGTH'::VARCHAR,
        'Maximum length exceeded'::TEXT

    FROM form_fields f

    JOIN field_values v
        ON v.field_id = f.field_id
       AND v.session_id = p_session_id

    WHERE jsonb_typeof(v.value) = 'string'

    AND LENGTH(v.value #>> '{}') > f.max_length;

END;
$$;

-- ------------------------------------------------------------
-- 15. SUBMISSION PROCESSING FUNCTION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION process_form_submission(
    p_session_id UUID
)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    session_record form_sessions%ROWTYPE;

    new_submission_id BIGINT;

    next_number INTEGER;

    validation_count INTEGER;

    payload JSONB;

BEGIN

    SELECT *
    INTO session_record
    FROM form_sessions
    WHERE session_id = p_session_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Session not found';
    END IF;

    IF session_record.current_status = 'submitting' THEN
        RAISE EXCEPTION 'Submission already in progress';
    END IF;

    IF session_record.current_status = 'submitted' THEN
        RAISE EXCEPTION 'Session already submitted';
    END IF;

    UPDATE form_sessions
    SET current_status = 'validating'
    WHERE session_id = p_session_id;

    SELECT COUNT(*)
    INTO validation_count
    FROM validate_submission(p_session_id);

    SELECT COALESCE(MAX(submission_number), 0) + 1
    INTO next_number
    FROM form_submissions
    WHERE session_id = p_session_id;

    SELECT COALESCE(
        jsonb_object_agg(f.field_key, v.value),
        '{}'::jsonb
    )
    INTO payload
    FROM field_values v
    JOIN form_fields f
        ON f.field_id = v.field_id
    WHERE v.session_id = p_session_id;

    INSERT INTO form_submissions (
        session_id,
        submission_number,
        submitted_revision,
        status,
        submitted_payload
    )
    VALUES (
        p_session_id,
        next_number,
        session_record.revision,
        CASE
            WHEN validation_count = 0 THEN 'validated'
            ELSE 'rejected'
        END,
        payload
    )
    RETURNING submission_id
    INTO new_submission_id;

    IF validation_count > 0 THEN

        INSERT INTO validation_errors (
            submission_id,
            field_id,
            error_code,
            error_message
        )
        SELECT
            new_submission_id,
            f.field_id,
            validation.error_code,
            validation.error_message

        FROM validate_submission(p_session_id) validation

        LEFT JOIN form_fields f
            ON f.form_id = session_record.form_id
           AND f.field_key = validation.field_name;

        UPDATE form_sessions
        SET current_status = 'invalid'
        WHERE session_id = p_session_id;

        RETURN new_submission_id;
    END IF;

    UPDATE form_sessions
    SET current_status = 'submitting'
    WHERE session_id = p_session_id;

    -- The transaction models an accepted submission.
    -- An external service would process this through an outbox
    -- or asynchronous worker.

    UPDATE form_submissions
    SET status = 'completed',
        processed_at = NOW()
    WHERE submission_id = new_submission_id;

    UPDATE form_sessions
    SET current_status = 'submitted'
    WHERE session_id = p_session_id;

    RETURN new_submission_id;

END;
$$;

-- ------------------------------------------------------------
-- 16. REPORTING VIEW
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW form_submission_report AS

SELECT
    f.form_key,
    f.form_name,
    s.session_reference,
    s.current_status,
    s.revision,

    COUNT(DISTINCT sub.submission_id) AS submission_count,

    COUNT(DISTINCT CASE
        WHEN sub.status = 'completed'
        THEN sub.submission_id
    END) AS completed_count,

    COUNT(DISTINCT CASE
        WHEN sub.status = 'rejected'
        THEN sub.submission_id
    END) AS rejected_count,

    MAX(sub.created_at) AS last_submission

FROM forms f

JOIN form_sessions s
    ON s.form_id = f.form_id

LEFT JOIN form_submissions sub
    ON sub.session_id = s.session_id

GROUP BY
    f.form_id,
    f.form_key,
    f.form_name,
    s.session_id,
    s.session_reference,
    s.current_status,
    s.revision;

-- ------------------------------------------------------------
-- 17. SAMPLE FORM DEFINITIONS
-- ------------------------------------------------------------

INSERT INTO forms (
    form_key,
    form_name,
    description
)
VALUES (
    'user_registration',
    'User Registration',
    'Registration form with event and validation tracking'
);

INSERT INTO form_fields (
    form_id,
    field_key,
    label,
    field_type,
    control_mode,
    required,
    max_length,
    display_order
)
SELECT
    form_id,
    data.field_key,
    data.label,
    data.field_type::input_type,
    data.control_mode::control_mode,
    data.required,
    data.max_length,
    data.display_order

FROM forms

CROSS JOIN (
    VALUES
        ('username', 'Username', 'text', 'controlled', TRUE, 30, 1),
        ('email', 'Email', 'email', 'controlled', TRUE, 100, 2),
        ('password', 'Password', 'password', 'controlled', TRUE, 128, 3),
        ('confirm_password', 'Confirm Password', 'password', 'controlled', TRUE, 128, 4),
        ('newsletter', 'Newsletter', 'checkbox', 'uncontrolled', FALSE, 1, 5)
) AS data(
    field_key,
    label,
    field_type,
    control_mode,
    required,
    max_length,
    display_order
)

WHERE form_key = 'user_registration';

-- ------------------------------------------------------------
-- 18. SAMPLE VALIDATION POLICIES
-- ------------------------------------------------------------

INSERT INTO validation_policies (
    field_id,
    minimum_length,
    maximum_length,
    email_validation
)
SELECT
    field_id,

    CASE field_key
        WHEN 'username' THEN 3
        WHEN 'password' THEN 8
        ELSE NULL
    END,

    max_length,

    field_key = 'email'

FROM form_fields
WHERE form_key IS NOT NULL
  AND field_id IN (
      SELECT field_id
      FROM form_fields
  );

-- ------------------------------------------------------------
-- 19. SAMPLE SESSIONS
-- ------------------------------------------------------------

INSERT INTO form_sessions (
    form_id,
    session_reference
)
SELECT
    form_id,
    'SESSION-VALID-001'
FROM forms
WHERE form_key = 'user_registration';

INSERT INTO form_sessions (
    form_id,
    session_reference
)
SELECT
    form_id,
    'SESSION-INVALID-001'
FROM forms
WHERE form_key = 'user_registration';

-- ------------------------------------------------------------
-- 20. SAMPLE VALID FIELD VALUES
-- ------------------------------------------------------------

INSERT INTO field_values (
    session_id,
    field_id,
    value,
    touched
)
SELECT
    s.session_id,
    f.field_id,

    CASE f.field_key
        WHEN 'username' THEN '"atul"'::jsonb
        WHEN 'email' THEN '"atul@example.com"'::jsonb
        WHEN 'password' THEN '"SecurePass123"'::jsonb
        WHEN 'confirm_password' THEN '"SecurePass123"'::jsonb
        WHEN 'newsletter' THEN 'true'::jsonb
    END,

    TRUE

FROM form_sessions s

JOIN forms form
    ON form.form_id = s.form_id

JOIN form_fields f
    ON f.form_id = form.form_id

WHERE s.session_reference = 'SESSION-VALID-001';

-- ------------------------------------------------------------
-- 21. SAMPLE INVALID FIELD VALUES
-- ------------------------------------------------------------

INSERT INTO field_values (
    session_id,
    field_id,
    value,
    touched
)
SELECT
    s.session_id,
    f.field_id,

    CASE f.field_key
        WHEN 'username' THEN '"ab"'::jsonb
        WHEN 'email' THEN '"invalid-email"'::jsonb
        WHEN 'password' THEN '"short"'::jsonb
        WHEN 'confirm_password' THEN '"different"'::jsonb
        WHEN 'newsletter' THEN 'false'::jsonb
    END,

    TRUE

FROM form_sessions s

JOIN forms form
    ON form.form_id = s.form_id

JOIN form_fields f
    ON f.form_id = form.form_id

WHERE s.session_reference = 'SESSION-INVALID-001';

-- ------------------------------------------------------------
-- 22. SAMPLE EVENT RECORDS
-- ------------------------------------------------------------

INSERT INTO form_events (
    session_id,
    field_id,
    event,
    event_payload,
    bubbles
)
SELECT
    s.session_id,
    f.field_id,
    'change',
    jsonb_build_object(
        'field',
        f.field_key,
        'source',
        'user-input'
    ),
    TRUE

FROM form_sessions s

JOIN forms form
    ON form.form_id = s.form_id

JOIN form_fields f
    ON f.form_id = form.form_id

WHERE s.session_reference = 'SESSION-VALID-001';

-- ------------------------------------------------------------
-- 23. PROCESS VALID SUBMISSION
-- ------------------------------------------------------------

DO $$
DECLARE
    target_session UUID;
    result_id BIGINT;
BEGIN

    SELECT session_id
    INTO target_session
    FROM form_sessions
    WHERE session_reference = 'SESSION-VALID-001';

    result_id := process_form_submission(target_session);

    RAISE NOTICE 'Valid submission ID: %', result_id;

END;
$$;

-- ------------------------------------------------------------
-- 24. PROCESS INVALID SUBMISSION
-- ------------------------------------------------------------

DO $$
DECLARE
    target_session UUID;
    result_id BIGINT;
BEGIN

    SELECT session_id
    INTO target_session
    FROM form_sessions
    WHERE session_reference = 'SESSION-INVALID-001';

    result_id := process_form_submission(target_session);

    RAISE NOTICE 'Invalid submission ID: %', result_id;

END;
$$;

-- ------------------------------------------------------------
-- 25. RETRIEVAL QUERIES
-- ------------------------------------------------------------

-- Retrieve available fields and their input behavior.

SELECT
    form_key,
    field_key,
    label,
    field_type,
    control_mode,
    required,
    max_length

FROM forms f

JOIN form_fields ff
    ON ff.form_id = f.form_id

WHERE f.form_key = 'user_registration'

ORDER BY display_order;

-- Retrieve current session state.

SELECT
    session_reference,
    current_status,
    revision,
    created_at,
    updated_at

FROM form_sessions
ORDER BY created_at;

-- Retrieve recorded events.

SELECT
    e.event_id,
    s.session_reference,
    e.event,
    f.field_key,
    e.event_payload,
    e.event_timestamp

FROM form_events e

JOIN form_sessions s
    ON s.session_id = e.session_id

LEFT JOIN form_fields f
    ON f.field_id = e.field_id

ORDER BY e.event_timestamp DESC;

-- ------------------------------------------------------------
-- 26. VALIDATION QUERY
-- ------------------------------------------------------------

SELECT *
FROM form_submissions;

SELECT
    sub.submission_id,
    f.field_key,
    e.error_code,
    e.error_message

FROM validation_errors e

JOIN form_submissions sub
    ON sub.submission_id = e.submission_id

LEFT JOIN form_fields f
    ON f.field_id = e.field_id

ORDER BY sub.submission_id;

-- ------------------------------------------------------------
-- 27. AGGREGATION
-- ------------------------------------------------------------

SELECT
    status,
    COUNT(*) AS total_submissions

FROM form_submissions

GROUP BY status

ORDER BY status;

-- ------------------------------------------------------------
-- 28. ELIGIBILITY DETERMINATION
-- ------------------------------------------------------------

WITH latest_submission AS (

    SELECT DISTINCT ON (session_id)
        submission_id,
        session_id,
        status,
        submitted_revision

    FROM form_submissions

    ORDER BY
        session_id,
        submission_number DESC

)

SELECT
    s.session_reference,

    s.current_status,

    ls.submission_id,

    CASE
        WHEN s.current_status = 'submitted'
         AND ls.status = 'completed'
         AND ls.submitted_revision = s.revision
        THEN TRUE

        ELSE FALSE
    END AS completed_at_current_revision

FROM form_sessions s

LEFT JOIN latest_submission ls
    ON ls.session_id = s.session_id;

-- ------------------------------------------------------------
-- 29. OPERATIONAL REPORTING
-- ------------------------------------------------------------

SELECT *
FROM form_submission_report
ORDER BY form_key, session_reference;

-- ------------------------------------------------------------
-- 30. VALIDATION FAILURE ANALYSIS
-- ------------------------------------------------------------

SELECT
    error_code,
    COUNT(*) AS occurrence_count

FROM validation_errors

GROUP BY error_code

ORDER BY occurrence_count DESC;

-- ------------------------------------------------------------
-- 31. EVENT FREQUENCY REPORT
-- ------------------------------------------------------------

SELECT
    event,
    COUNT(*) AS total_events,
    COUNT(DISTINCT session_id) AS affected_sessions

FROM form_events

GROUP BY event

ORDER BY total_events DESC;

-- ------------------------------------------------------------
-- 32. TRANSACTION ROLLBACK DEMONSTRATION
-- ------------------------------------------------------------

SAVEPOINT before_test_update;

-- This update is valid, but is intentionally rolled back.
UPDATE form_sessions
SET revision = revision + 1
WHERE session_reference = 'SESSION-VALID-001';

ROLLBACK TO SAVEPOINT before_test_update;

-- ------------------------------------------------------------
-- 33. DATABASE PERFORMANCE
-- ------------------------------------------------------------

ANALYZE forms;
ANALYZE form_fields;
ANALYZE form_sessions;
ANALYZE field_values;
ANALYZE form_events;
ANALYZE form_submissions;
ANALYZE validation_errors;

COMMIT;
