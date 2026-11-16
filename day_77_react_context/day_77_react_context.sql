/*
 * React Context: Relational Model of Provider-Based State
 *
 * PostgreSQL 15+
 *
 * Models:
 * - Applications
 * - Context definitions
 * - Provider instances
 * - Parent and child provider scopes
 * - Consumer registrations
 * - Context subscriptions
 * - State snapshots
 * - State transitions
 * - Typed actions
 * - Access policies
 * - Notification delivery
 *
 * The database represents a server-side state-management
 * service inspired by Context API concepts.
 *
 * React Context itself is an in-memory frontend mechanism.
 * This schema models a complementary persistent backend.
 */

BEGIN;

CREATE SCHEMA IF NOT EXISTS context_management;

SET search_path TO context_management, public;


/* =========================================================
   1. Enumerated Domain Types
   ========================================================= */

CREATE TYPE context_status AS ENUM (
    'ACTIVE',
    'DISABLED',
    'ARCHIVED'
);

CREATE TYPE provider_status AS ENUM (
    'ACTIVE',
    'INACTIVE'
);

CREATE TYPE consumer_status AS ENUM (
    'ACTIVE',
    'UNSUBSCRIBED'
);

CREATE TYPE action_status AS ENUM (
    'ACCEPTED',
    'REJECTED',
    'PROCESSED'
);

CREATE TYPE notification_status AS ENUM (
    'PENDING',
    'DELIVERED',
    'FAILED'
);


/* =========================================================
   2. Applications
   ========================================================= */

CREATE TABLE applications (
    application_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    application_key VARCHAR(100) NOT NULL UNIQUE,

    application_name VARCHAR(150) NOT NULL,

    environment VARCHAR(30) NOT NULL
        CHECK (
            environment IN (
                'development',
                'testing',
                'staging',
                'production'
            )
        ),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


/* =========================================================
   3. Context Definitions
   ========================================================= */

CREATE TABLE context_definitions (
    context_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    application_id BIGINT NOT NULL
        REFERENCES applications(application_id)
        ON DELETE CASCADE,

    context_name VARCHAR(120) NOT NULL,

    description TEXT,

    default_state JSONB NOT NULL DEFAULT '{}'::JSONB,

    status context_status NOT NULL DEFAULT 'ACTIVE',

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(application_id, context_name),

    CHECK (jsonb_typeof(default_state) = 'object')
);


/* =========================================================
   4. Provider Instances
   ========================================================= */

CREATE TABLE providers (
    provider_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    context_id BIGINT NOT NULL
        REFERENCES context_definitions(context_id)
        ON DELETE CASCADE,

    parent_provider_id BIGINT,

    provider_name VARCHAR(120) NOT NULL,

    scope_key VARCHAR(150) NOT NULL,

    status provider_status NOT NULL DEFAULT 'ACTIVE',

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(context_id, scope_key),

    UNIQUE(provider_id, context_id),

    FOREIGN KEY(parent_provider_id, context_id)
        REFERENCES providers(provider_id, context_id)
        DEFERRABLE INITIALLY IMMEDIATE,

    CHECK (
        parent_provider_id IS NULL
        OR parent_provider_id <> provider_id
    )
);

CREATE INDEX idx_providers_parent
    ON providers(parent_provider_id);

CREATE INDEX idx_providers_context_status
    ON providers(context_id, status);


/* =========================================================
   5. State Snapshots
   ========================================================= */

CREATE TABLE state_snapshots (
    snapshot_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    provider_id BIGINT NOT NULL
        REFERENCES providers(provider_id)
        ON DELETE CASCADE,

    version BIGINT NOT NULL CHECK(version >= 0),

    state_data JSONB NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(provider_id, version),

    CHECK (jsonb_typeof(state_data) = 'object')
);

CREATE INDEX idx_snapshots_provider_version
    ON state_snapshots(provider_id, version DESC);


/* =========================================================
   6. Consumers
   ========================================================= */

CREATE TABLE consumers (
    consumer_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    application_id BIGINT NOT NULL
        REFERENCES applications(application_id)
        ON DELETE CASCADE,

    consumer_name VARCHAR(120) NOT NULL,

    component_path VARCHAR(300) NOT NULL,

    status consumer_status NOT NULL DEFAULT 'ACTIVE',

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(application_id, component_path)
);


/* =========================================================
   7. Context Subscriptions
   ========================================================= */

CREATE TABLE context_subscriptions (
    subscription_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    consumer_id BIGINT NOT NULL
        REFERENCES consumers(consumer_id)
        ON DELETE CASCADE,

    provider_id BIGINT NOT NULL
        REFERENCES providers(provider_id)
        ON DELETE CASCADE,

    selector_path VARCHAR(300) NOT NULL,

    last_seen_version BIGINT NOT NULL DEFAULT 0
        CHECK(last_seen_version >= 0),

    subscribed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(consumer_id, provider_id, selector_path)
);

CREATE INDEX idx_subscriptions_provider
    ON context_subscriptions(provider_id);

CREATE INDEX idx_subscriptions_consumer
    ON context_subscriptions(consumer_id);


/* =========================================================
   8. State Actions
   ========================================================= */

CREATE TABLE state_actions (
    action_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    provider_id BIGINT NOT NULL
        REFERENCES providers(provider_id)
        ON DELETE CASCADE,

    action_type VARCHAR(60) NOT NULL,

    payload JSONB NOT NULL DEFAULT '{}'::JSONB,

    status action_status NOT NULL DEFAULT 'ACCEPTED',

    error_message TEXT,

    previous_version BIGINT,

    resulting_version BIGINT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    processed_at TIMESTAMPTZ,

    CHECK(jsonb_typeof(payload) = 'object'),

    CHECK(
        resulting_version IS NULL
        OR resulting_version > previous_version
    )
);

CREATE INDEX idx_actions_provider_time
    ON state_actions(provider_id, created_at DESC);

CREATE INDEX idx_actions_status
    ON state_actions(status, created_at);


/* =========================================================
   9. Notification Queue
   ========================================================= */

CREATE TABLE context_notifications (
    notification_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    subscription_id BIGINT NOT NULL
        REFERENCES context_subscriptions(subscription_id)
        ON DELETE CASCADE,

    action_id BIGINT NOT NULL
        REFERENCES state_actions(action_id)
        ON DELETE CASCADE,

    status notification_status NOT NULL DEFAULT 'PENDING',

    attempt_count INTEGER NOT NULL DEFAULT 0
        CHECK(attempt_count >= 0),

    error_message TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    delivered_at TIMESTAMPTZ,

    UNIQUE(subscription_id, action_id)
);

CREATE INDEX idx_notifications_pending
    ON context_notifications(created_at)
    WHERE status = 'PENDING';


/* =========================================================
   10. Access Policies
   ========================================================= */

CREATE TABLE context_access_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    context_id BIGINT NOT NULL
        REFERENCES context_definitions(context_id)
        ON DELETE CASCADE,

    role_name VARCHAR(80) NOT NULL,

    can_read BOOLEAN NOT NULL DEFAULT FALSE,

    can_write BOOLEAN NOT NULL DEFAULT FALSE,

    can_manage_providers BOOLEAN NOT NULL DEFAULT FALSE,

    UNIQUE(context_id, role_name)
);


/* =========================================================
   11. Provider State Retrieval
   ========================================================= */

CREATE OR REPLACE FUNCTION get_provider_state(
    p_provider_id BIGINT
)
RETURNS JSONB
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    result JSONB;
BEGIN
    SELECT state_data
    INTO result
    FROM state_snapshots
    WHERE provider_id = p_provider_id
    ORDER BY version DESC
    LIMIT 1;

    IF result IS NULL THEN
        SELECT cd.default_state
        INTO result
        FROM providers p
        JOIN context_definitions cd
            ON cd.context_id = p.context_id
        WHERE p.provider_id = p_provider_id
          AND p.status = 'ACTIVE'
          AND cd.status = 'ACTIVE';
    END IF;

    IF result IS NULL THEN
        RAISE EXCEPTION
            'Active provider % does not exist',
            p_provider_id;
    END IF;

    RETURN result;
END;
$$;


/* =========================================================
   12. Provider State Update Function
   ========================================================= */

CREATE OR REPLACE FUNCTION update_provider_state(
    p_provider_id BIGINT,
    p_expected_version BIGINT,
    p_new_state JSONB,
    p_action_type VARCHAR(60),
    p_payload JSONB DEFAULT '{}'::JSONB
)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    current_version BIGINT;
    new_version BIGINT;
    current_state JSONB;
    new_action_id BIGINT;
    provider_active BOOLEAN;
BEGIN

    IF jsonb_typeof(p_new_state) <> 'object'
       OR jsonb_typeof(p_payload) <> 'object' THEN
        RAISE EXCEPTION
            'State and action payload must be JSON objects';
    END IF;

    IF p_action_type NOT IN (
        'LOGIN',
        'LOGOUT',
        'UPDATE_PROFILE',
        'SET_THEME',
        'SET_LANGUAGE',
        'RESET'
    ) THEN
        RAISE EXCEPTION 'Unsupported action type';
    END IF;

    SELECT
        status = 'ACTIVE'
    INTO provider_active
    FROM providers
    WHERE provider_id = p_provider_id
    FOR UPDATE;

    IF NOT FOUND OR NOT provider_active THEN
        RAISE EXCEPTION 'Provider is unavailable';
    END IF;

    SELECT
        version,
        state_data
    INTO
        current_version,
        current_state
    FROM state_snapshots
    WHERE provider_id = p_provider_id
    ORDER BY version DESC
    LIMIT 1
    FOR UPDATE;

    IF current_version IS NULL THEN
        SELECT cd.default_state
        INTO current_state
        FROM providers p
        JOIN context_definitions cd
            ON cd.context_id = p.context_id
        WHERE p.provider_id = p_provider_id;

        current_version := 0;
    END IF;

    /*
     * Optimistic concurrency control prevents an update
     * from overwriting a newer state transition.
     */
    IF current_version <> p_expected_version THEN
        RAISE EXCEPTION
            'Version conflict: expected %, actual %',
            p_expected_version,
            current_version;
    END IF;

    /*
     * Application-specific invariants.
     */
    IF p_new_state ? 'authenticated'
       AND jsonb_typeof(
           p_new_state -> 'authenticated'
       ) <> 'boolean' THEN
        RAISE EXCEPTION
            'authenticated must be boolean';
    END IF;

    IF p_new_state ? 'theme'
       AND p_new_state ->> 'theme'
           NOT IN ('light', 'dark', 'system') THEN
        RAISE EXCEPTION 'Invalid theme';
    END IF;

    IF p_new_state ? 'language'
       AND p_new_state ->> 'language'
           NOT IN ('en', 'hi', 'fr', 'de') THEN
        RAISE EXCEPTION 'Unsupported language';
    END IF;

    IF p_new_state ->> 'authenticated' = 'true'
       AND NOT (
           p_new_state -> 'profile' ? 'user_id'
       ) THEN
        RAISE EXCEPTION
            'Authenticated state requires profile.user_id';
    END IF;

    IF p_new_state ->> 'authenticated' = 'false'
       AND p_new_state -> 'profile'
           IS DISTINCT FROM '{}'::JSONB THEN
        RAISE EXCEPTION
            'Unauthenticated state requires empty profile';
    END IF;

    new_version := current_version + 1;

    INSERT INTO state_actions (
        provider_id,
        action_type,
        payload,
        status,
        previous_version,
        resulting_version,
        processed_at
    )
    VALUES (
        p_provider_id,
        p_action_type,
        p_payload,
        'PROCESSED',
        current_version,
        new_version,
        NOW()
    )
    RETURNING action_id INTO new_action_id;

    INSERT INTO state_snapshots (
        provider_id,
        version,
        state_data
    )
    VALUES (
        p_provider_id,
        new_version,
        p_new_state
    );

    /*
     * Queue notifications for active consumers.
     * Delivery is handled separately from the state transaction.
     */
    INSERT INTO context_notifications (
        subscription_id,
        action_id
    )
    SELECT
        subscription_id,
        new_action_id
    FROM context_subscriptions
    WHERE provider_id = p_provider_id
      AND EXISTS (
          SELECT 1
          FROM consumers c
          WHERE c.consumer_id =
              context_subscriptions.consumer_id
            AND c.status = 'ACTIVE'
      )
    ON CONFLICT(subscription_id, action_id)
    DO NOTHING;

    RETURN new_version;
END;
$$;


/* =========================================================
   13. Consumer Notification Processing
   ========================================================= */

CREATE OR REPLACE PROCEDURE process_context_notifications(
    p_batch_size INTEGER DEFAULT 100
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF p_batch_size < 1 OR p_batch_size > 1000 THEN
        RAISE EXCEPTION
            'Batch size must be between 1 and 1000';
    END IF;

    WITH selected AS (
        SELECT notification_id
        FROM context_notifications
        WHERE status IN ('PENDING', 'FAILED')
          AND attempt_count < 5
        ORDER BY created_at
        LIMIT p_batch_size
        FOR UPDATE SKIP LOCKED
    )
    UPDATE context_notifications n
    SET
        status = 'DELIVERED',
        attempt_count = attempt_count + 1,
        delivered_at = NOW(),
        error_message = NULL
    FROM selected
    WHERE n.notification_id = selected.notification_id;

    /*
     * This procedure demonstrates queue-state processing.
     * A real external consumer must acknowledge delivery.
     */
END;
$$;


/* =========================================================
   14. Sample Applications
   ========================================================= */

INSERT INTO applications (
    application_key,
    application_name,
    environment
)
VALUES
    (
        'PORTAL-001',
        'Enterprise Employee Portal',
        'production'
    ),
    (
        'ADMIN-001',
        'Administration Console',
        'staging'
    );


/* =========================================================
   15. Sample Context Definitions
   ========================================================= */

INSERT INTO context_definitions (
    application_id,
    context_name,
    description,
    default_state
)
SELECT
    application_id,
    'ApplicationContext',
    'Central application state',
    '{
        "authenticated": false,
        "profile": {},
        "theme": "light",
        "language": "en"
    }'::JSONB
FROM applications
WHERE application_key = 'PORTAL-001';

INSERT INTO context_definitions (
    application_id,
    context_name,
    description,
    default_state
)
SELECT
    application_id,
    'LocalThemeContext',
    'Nested theme state',
    '{"theme": "dark"}'::JSONB
FROM applications
WHERE application_key = 'PORTAL-001';


/* =========================================================
   16. Sample Providers
   ========================================================= */

INSERT INTO providers (
    context_id,
    provider_name,
    scope_key
)
SELECT
    context_id,
    'RootApplicationProvider',
    'root'
FROM context_definitions
WHERE context_name = 'ApplicationContext';

INSERT INTO providers (
    context_id,
    parent_provider_id,
    provider_name,
    scope_key
)
SELECT
    child.context_id,
    parent.provider_id,
    'DashboardThemeProvider',
    'dashboard'
FROM context_definitions child
JOIN providers parent
    ON parent.context_id = child.context_id
WHERE child.context_name = 'ApplicationContext'
  AND parent.scope_key = 'root';

INSERT INTO providers (
    context_id,
    provider_name,
    scope_key
)
SELECT
    context_id,
    'LocalThemeProvider',
    'local-theme'
FROM context_definitions
WHERE context_name = 'LocalThemeContext';


/* =========================================================
   17. Initial State Snapshots
   ========================================================= */

INSERT INTO state_snapshots (
    provider_id,
    version,
    state_data
)
SELECT
    p.provider_id,
    0,
    cd.default_state
FROM providers p
JOIN context_definitions cd
    ON cd.context_id = p.context_id;


/* =========================================================
   18. Consumers
   ========================================================= */

INSERT INTO consumers (
    application_id,
    consumer_name,
    component_path
)
SELECT
    application_id,
    'DashboardConsumer',
    'src/components/Dashboard'
FROM applications
WHERE application_key = 'PORTAL-001';

INSERT INTO consumers (
    application_id,
    consumer_name,
    component_path
)
SELECT
    application_id,
    'ThemeConsumer',
    'src/components/ThemeSelector'
FROM applications
WHERE application_key = 'PORTAL-001';

INSERT INTO consumers (
    application_id,
    consumer_name,
    component_path
)
SELECT
    application_id,
    'ProfileConsumer',
    'src/components/ProfilePanel'
FROM applications
WHERE application_key = 'PORTAL-001';


/* =========================================================
   19. Consumer Subscriptions
   ========================================================= */

INSERT INTO context_subscriptions (
    consumer_id,
    provider_id,
    selector_path
)
SELECT
    c.consumer_id,
    p.provider_id,
    CASE c.consumer_name
        WHEN 'DashboardConsumer' THEN '$'
        WHEN 'ThemeConsumer' THEN '$.theme'
        WHEN 'ProfileConsumer' THEN '$.profile'
    END
FROM consumers c
JOIN providers p
    ON p.scope_key = 'root'
WHERE c.application_id = (
    SELECT application_id
    FROM applications
    WHERE application_key = 'PORTAL-001'
);


/* =========================================================
   20. Access Policies
   ========================================================= */

INSERT INTO context_access_policies (
    context_id,
    role_name,
    can_read,
    can_write,
    can_manage_providers
)
SELECT
    context_id,
    'viewer',
    TRUE,
    FALSE,
    FALSE
FROM context_definitions
WHERE context_name = 'ApplicationContext';

INSERT INTO context_access_policies (
    context_id,
    role_name,
    can_read,
    can_write,
    can_manage_providers
)
SELECT
    context_id,
    'application_admin',
    TRUE,
    TRUE,
    TRUE
FROM context_definitions
WHERE context_name = 'ApplicationContext';


/* =========================================================
   21. Transactional State Update
   ========================================================= */

DO $$
DECLARE
    root_provider BIGINT;
    current_state JSONB;
    current_version BIGINT;
    updated_state JSONB;
BEGIN
    SELECT provider_id
    INTO root_provider
    FROM providers
    WHERE scope_key = 'root'
    LIMIT 1;

    SELECT
        version,
        state_data
    INTO
        current_version,
        current_state
    FROM state_snapshots
    WHERE provider_id = root_provider
    ORDER BY version DESC
    LIMIT 1;

    /*
     * Login is a complete state transition.
     */
    updated_state := jsonb_build_object(
        'authenticated', TRUE,
        'profile', jsonb_build_object(
            'user_id', 'USR-1001',
            'name', 'Aarav Sharma',
            'email', 'aarav@example.com'
        ),
        'theme', 'dark',
        'language', 'en'
    );

    PERFORM update_provider_state(
        root_provider,
        current_version,
        updated_state,
        'LOGIN',
        '{"user_id":"USR-1001"}'::JSONB
    );
END;
$$;


/* =========================================================
   22. Reporting View
   ========================================================= */

CREATE OR REPLACE VIEW provider_state_report AS
SELECT
    a.application_name,
    cd.context_name,
    p.provider_name,
    p.scope_key,
    p.status AS provider_status,
    s.version,
    s.state_data,
    s.created_at
FROM providers p
JOIN context_definitions cd
    ON cd.context_id = p.context_id
JOIN applications a
    ON a.application_id = cd.application_id
LEFT JOIN LATERAL (
    SELECT
        version,
        state_data,
        created_at
    FROM state_snapshots
    WHERE provider_id = p.provider_id
    ORDER BY version DESC
    LIMIT 1
) s ON TRUE;


/* =========================================================
   23. Subscription Aggregation
   ========================================================= */

CREATE OR REPLACE VIEW consumer_subscription_report AS
SELECT
    a.application_name,
    c.consumer_name,
    c.component_path,
    COUNT(cs.subscription_id) AS subscription_count,
    COUNT(DISTINCT cs.provider_id) AS provider_count
FROM consumers c
JOIN applications a
    ON a.application_id = c.application_id
LEFT JOIN context_subscriptions cs
    ON cs.consumer_id = c.consumer_id
GROUP BY
    a.application_name,
    c.consumer_name,
    c.component_path;


/* =========================================================
   24. Latest State and Historical Evaluation
   ========================================================= */

WITH ranked_states AS (
    SELECT
        provider_id,
        version,
        state_data,
        created_at,
        ROW_NUMBER() OVER (
            PARTITION BY provider_id
            ORDER BY version DESC
        ) AS row_number
    FROM state_snapshots
)
SELECT
    provider_id,
    version,
    state_data,
    created_at
FROM ranked_states
WHERE row_number = 1
ORDER BY provider_id;


/* =========================================================
   25. Action History
   ========================================================= */

SELECT
    p.provider_name,
    sa.action_type,
    sa.status,
    sa.previous_version,
    sa.resulting_version,
    sa.payload,
    sa.created_at
FROM state_actions sa
JOIN providers p
    ON p.provider_id = sa.provider_id
ORDER BY sa.created_at DESC;


/* =========================================================
   26. Consumer and Notification Report
   ========================================================= */

SELECT
    c.consumer_name,
    cs.selector_path,
    COUNT(n.notification_id) AS notification_count,
    COUNT(*) FILTER (
        WHERE n.status = 'DELIVERED'
    ) AS delivered_count,
    COUNT(*) FILTER (
        WHERE n.status = 'PENDING'
    ) AS pending_count,
    COUNT(*) FILTER (
        WHERE n.status = 'FAILED'
    ) AS failed_count
FROM consumers c
JOIN context_subscriptions cs
    ON cs.consumer_id = c.consumer_id
LEFT JOIN context_notifications n
    ON n.subscription_id = cs.subscription_id
GROUP BY
    c.consumer_name,
    cs.selector_path;


/* =========================================================
   27. Eligibility Evaluation
   ========================================================= */

SELECT
    p.provider_id,
    p.provider_name,
    p.status,
    cd.status AS context_status,
    CASE
        WHEN p.status <> 'ACTIVE'
            THEN 'INELIGIBLE_PROVIDER_DISABLED'
        WHEN cd.status <> 'ACTIVE'
            THEN 'INELIGIBLE_CONTEXT_DISABLED'
        WHEN NOT EXISTS (
            SELECT 1
            FROM state_snapshots ss
            WHERE ss.provider_id = p.provider_id
        )
            THEN 'DEFAULT_STATE_REQUIRED'
        ELSE 'ELIGIBLE'
    END AS eligibility
FROM providers p
JOIN context_definitions cd
    ON cd.context_id = p.context_id;


/* =========================================================
   28. Failed Action Analysis
   ========================================================= */

SELECT
    action_type,
    status,
    COUNT(*) AS action_count
FROM state_actions
GROUP BY action_type, status
ORDER BY action_type, status;


/* =========================================================
   29. Data Integrity Verification
   ========================================================= */

DO $$
DECLARE
    invalid_count BIGINT;
BEGIN
    SELECT COUNT(*)
    INTO invalid_count
    FROM state_snapshots
    WHERE jsonb_typeof(state_data) <> 'object';

    IF invalid_count > 0 THEN
        RAISE EXCEPTION
            'Invalid state snapshots detected';
    END IF;

    SELECT COUNT(*)
    INTO invalid_count
    FROM context_subscriptions cs
    JOIN consumers c
        ON c.consumer_id = cs.consumer_id
    WHERE c.status = 'UNSUBSCRIBED';

    RAISE NOTICE
        'Inactive consumer subscriptions: %',
        invalid_count;
END;
$$;


/* =========================================================
   30. Notification Processing
   ========================================================= */

CALL process_context_notifications(100);


/* =========================================================
   31. Final Reports
   ========================================================= */

SELECT *
FROM provider_state_report
ORDER BY application_name, context_name, scope_key;

SELECT *
FROM consumer_subscription_report
ORDER BY consumer_name;


/*
 * Important design properties:
 *
 * 1. Provider instances maintain independent scopes.
 * 2. Parent relationships model nested providers.
 * 3. Snapshots retain state history.
 * 4. Version checks prevent lost updates.
 * 5. Consumer subscriptions identify selected state paths.
 * 6. Notifications are stored independently of state changes.
 * 7. Policies distinguish read, write, and administration.
 * 8. Database transactions protect each state transition.
 *
 * Client-side React Context remains separate from this
 * persistent server-side representation.
 */

COMMIT;
