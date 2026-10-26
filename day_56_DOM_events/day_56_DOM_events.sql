DROP SCHEMA IF EXISTS dom_events CASCADE;
CREATE SCHEMA dom_events;

SET search_path = dom_events, public;

-- A relational event model separates DOM hierarchy, listener configuration,
-- dispatched events, propagation, and default-action outcomes.

CREATE TYPE event_phase AS ENUM (
    'capturing',
    'at_target',
    'bubbling'
);

CREATE TYPE listener_kind AS ENUM (
    'direct',
    'delegated'
);

CREATE TYPE event_dispatch_status AS ENUM (
    'created',
    'dispatched',
    'cancelled',
    'failed'
);

CREATE TABLE event_target (
    target_id BIGSERIAL PRIMARY KEY,
    parent_id BIGINT REFERENCES event_target(target_id)
        ON DELETE CASCADE,
    element_name TEXT NOT NULL,
    element_id TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT valid_element_name
        CHECK (length(trim(element_name)) > 0),
    CONSTRAINT no_self_parent
        CHECK (parent_id IS NULL OR parent_id <> target_id),
    CONSTRAINT unique_sibling_identifier
        UNIQUE (parent_id, element_id)
);

CREATE INDEX idx_event_target_parent
    ON event_target(parent_id);

CREATE TABLE target_class (
    target_id BIGINT NOT NULL
        REFERENCES event_target(target_id)
        ON DELETE CASCADE,
    class_name TEXT NOT NULL,
    PRIMARY KEY (target_id, class_name),
    CHECK (length(trim(class_name)) > 0)
);

CREATE TABLE event_listener (
    listener_id BIGSERIAL PRIMARY KEY,
    target_id BIGINT NOT NULL
        REFERENCES event_target(target_id)
        ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    listener_kind listener_kind NOT NULL DEFAULT 'direct',
    selector TEXT,
    capture BOOLEAN NOT NULL DEFAULT FALSE,
    once_listener BOOLEAN NOT NULL DEFAULT FALSE,
    passive BOOLEAN NOT NULL DEFAULT FALSE,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    listener_priority INTEGER NOT NULL DEFAULT 100,
    CONSTRAINT valid_event_type
        CHECK (length(trim(event_type)) > 0),
    CONSTRAINT delegated_listener_requires_selector
        CHECK (
            listener_kind = 'direct'
            OR length(trim(coalesce(selector, ''))) > 0
        )
);

CREATE INDEX idx_listener_dispatch
    ON event_listener(target_id, event_type, capture, enabled);

CREATE TABLE dispatched_event (
    event_id BIGSERIAL PRIMARY KEY,
    event_type TEXT NOT NULL,
    target_id BIGINT NOT NULL
        REFERENCES event_target(target_id),
    bubbles BOOLEAN NOT NULL DEFAULT TRUE,
    cancelable BOOLEAN NOT NULL DEFAULT TRUE,
    status event_dispatch_status NOT NULL DEFAULT 'created',
    default_prevented BOOLEAN NOT NULL DEFAULT FALSE,
    propagation_stopped BOOLEAN NOT NULL DEFAULT FALSE,
    immediate_propagation_stopped BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    completed_at TIMESTAMPTZ,
    CONSTRAINT valid_dispatch_event_type
        CHECK (length(trim(event_type)) > 0)
);

CREATE INDEX idx_dispatched_event_target_type
    ON dispatched_event(target_id, event_type, created_at DESC);

CREATE TABLE event_delivery (
    delivery_id BIGSERIAL PRIMARY KEY,
    event_id BIGINT NOT NULL
        REFERENCES dispatched_event(event_id)
        ON DELETE CASCADE,
    listener_id BIGINT
        REFERENCES event_listener(listener_id)
        ON DELETE SET NULL,
    current_target_id BIGINT NOT NULL
        REFERENCES event_target(target_id),
    phase event_phase NOT NULL,
    sequence_number INTEGER NOT NULL,
    handled BOOLEAN NOT NULL DEFAULT TRUE,
    prevented_default BOOLEAN NOT NULL DEFAULT FALSE,
    stopped_propagation BOOLEAN NOT NULL DEFAULT FALSE,
    execution_error TEXT,
    delivered_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    UNIQUE (event_id, sequence_number)
);

CREATE INDEX idx_event_delivery_event
    ON event_delivery(event_id, sequence_number);

CREATE TABLE default_action (
    action_id BIGSERIAL PRIMARY KEY,
    event_type TEXT NOT NULL UNIQUE,
    action_name TEXT NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT valid_action_name
        CHECK (length(trim(action_name)) > 0)
);

CREATE TABLE event_policy (
    policy_id BIGSERIAL PRIMARY KEY,
    policy_name TEXT NOT NULL UNIQUE,
    allow_default_action BOOLEAN NOT NULL DEFAULT TRUE,
    require_cancelable BOOLEAN NOT NULL DEFAULT FALSE,
    max_bubble_depth INTEGER NOT NULL DEFAULT 100,
    CONSTRAINT valid_policy_name
        CHECK (length(trim(policy_name)) > 0),
    CONSTRAINT valid_bubble_depth
        CHECK (max_bubble_depth BETWEEN 1 AND 10000)
);

CREATE TABLE event_type_policy (
    policy_id BIGINT NOT NULL
        REFERENCES event_policy(policy_id)
        ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    allow_dispatch BOOLEAN NOT NULL DEFAULT TRUE,
    PRIMARY KEY (policy_id, event_type)
);

-- Prevent a disabled target from receiving new listeners.
CREATE OR REPLACE FUNCTION validate_listener_target()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM event_target
        WHERE target_id = NEW.target_id
          AND is_active
    ) THEN
        RAISE EXCEPTION
            'Cannot attach listener to inactive target %',
            NEW.target_id;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_listener_target
BEFORE INSERT OR UPDATE ON event_listener
FOR EACH ROW
EXECUTE FUNCTION validate_listener_target();

-- Once listeners are modeled as consumed, disabling them preserves an
-- auditable record while preventing another invocation.
CREATE OR REPLACE FUNCTION consume_once_listener(
    p_listener_id BIGINT
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE event_listener
    SET enabled = FALSE
    WHERE listener_id = p_listener_id
      AND once_listener = TRUE;
END;
$$;

-- Build the root-to-target propagation path with a recursive CTE.
CREATE OR REPLACE FUNCTION event_path(
    p_target_id BIGINT
)
RETURNS TABLE (
    target_id BIGINT,
    depth INTEGER,
    element_name TEXT,
    element_id TEXT
)
LANGUAGE sql
AS $$
    WITH RECURSIVE hierarchy AS (
        SELECT
            et.target_id,
            et.parent_id,
            et.element_name,
            et.element_id,
            0 AS depth
        FROM event_target et
        WHERE et.target_id = p_target_id

        UNION ALL

        SELECT
            parent.target_id,
            parent.parent_id,
            parent.element_name,
            parent.element_id,
            child.depth + 1
        FROM hierarchy child
        JOIN event_target parent
          ON parent.target_id = child.parent_id
    )
    SELECT
        target_id,
        depth,
        element_name,
        element_id
    FROM hierarchy
    ORDER BY depth DESC;
$$;

CREATE OR REPLACE FUNCTION event_depth(
    p_target_id BIGINT
)
RETURNS INTEGER
LANGUAGE sql
AS $$
    SELECT count(*)::INTEGER
    FROM event_path(p_target_id);
$$;

-- Example target hierarchy.
INSERT INTO event_target (
    target_id,
    parent_id,
    element_name,
    element_id
)
OVERRIDING SYSTEM VALUE
VALUES
    (1, NULL, 'document', NULL),
    (2, 1, 'section', 'app'),
    (3, 2, 'ul', 'users'),
    (4, 3, 'li', 'user-17'),
    (5, 4, 'button', 'delete'),
    (6, 2, 'form', 'profile'),
    (7, 6, 'input', 'email');

INSERT INTO target_class(target_id, class_name)
VALUES
    (4, 'user-row'),
    (5, 'danger-action');

INSERT INTO event_listener (
    listener_id,
    target_id,
    event_type,
    listener_kind,
    selector,
    capture,
    once_listener,
    passive,
    listener_priority
)
OVERRIDING SYSTEM VALUE
VALUES
    (1, 1, 'click', 'direct', NULL, TRUE, FALSE, FALSE, 10),
    (2, 2, 'click', 'direct', NULL, TRUE, FALSE, FALSE, 20),
    (3, 5, 'click', 'direct', NULL, FALSE, FALSE, FALSE, 30),
    (4, 2, 'click', 'direct', NULL, FALSE, FALSE, FALSE, 40),
    (5, 1, 'click', 'direct', NULL, FALSE, FALSE, FALSE, 50),
    (6, 3, 'click', 'delegated', '.user-row', FALSE, FALSE, FALSE, 25),
    (7, 5, 'navigate', 'direct', NULL, FALSE, FALSE, FALSE, 30),
    (8, 5, 'audit', 'direct', NULL, FALSE, TRUE, FALSE, 30),
    (9, 5, 'wheel', 'direct', NULL, FALSE, FALSE, TRUE, 30),
    (10, 6, 'focus', 'direct', NULL, FALSE, FALSE, FALSE, 30);

INSERT INTO default_action(event_type, action_name)
VALUES
    ('click', 'activate-control'),
    ('navigate', 'browser-navigation'),
    ('wheel', 'scroll-content'),
    ('focus', 'focus-control');

INSERT INTO event_policy (
    policy_id,
    policy_name,
    allow_default_action,
    require_cancelable,
    max_bubble_depth
)
OVERRIDING SYSTEM VALUE
VALUES
    (1, 'standard-ui', TRUE, FALSE, 100),
    (2, 'secure-navigation', FALSE, TRUE, 20);

INSERT INTO event_type_policy(
    policy_id,
    event_type,
    allow_dispatch
)
VALUES
    (1, 'click', TRUE),
    (1, 'navigate', TRUE),
    (1, 'wheel', TRUE),
    (1, 'focus', TRUE),
    (1, 'audit', TRUE),
    (2, 'navigate', TRUE);

-- Event 1: normal click. Capture and bubble are both represented.
INSERT INTO dispatched_event (
    event_id,
    event_type,
    target_id,
    bubbles,
    cancelable,
    status
)
OVERRIDING SYSTEM VALUE
VALUES
    (1, 'click', 5, TRUE, TRUE, 'dispatched');

INSERT INTO event_delivery (
    event_id,
    listener_id,
    current_target_id,
    phase,
    sequence_number
)
VALUES
    (1, 1, 1, 'capturing', 1),
    (1, 2, 2, 'capturing', 2),
    (1, 3, 5, 'at_target', 3),
    (1, 4, 2, 'bubbling', 4),
    (1, 5, 1, 'bubbling', 5);

-- Delegated listener on the list handles a descendant row.
INSERT INTO event_delivery (
    event_id,
    listener_id,
    current_target_id,
    phase,
    sequence_number
)
VALUES
    (1, 6, 3, 'bubbling', 6);

-- Event 2: navigation cancelled by preventDefault.
INSERT INTO dispatched_event (
    event_id,
    event_type,
    target_id,
    bubbles,
    cancelable,
    status,
    default_prevented
)
OVERRIDING SYSTEM VALUE
VALUES
    (2, 'navigate', 5, TRUE, TRUE, 'cancelled', TRUE);

INSERT INTO event_delivery (
    event_id,
    listener_id,
    current_target_id,
    phase,
    sequence_number,
    prevented_default
)
VALUES
    (2, 7, 5, 'at_target', 1, TRUE);

-- Event 3: once listener is consumed.
INSERT INTO dispatched_event (
    event_id,
    event_type,
    target_id,
    bubbles,
    cancelable,
    status
)
OVERRIDING SYSTEM VALUE
VALUES
    (3, 'audit', 5, TRUE, FALSE, 'dispatched');

INSERT INTO event_delivery (
    event_id,
    listener_id,
    current_target_id,
    phase,
    sequence_number
)
VALUES
    (3, 8, 5, 'at_target', 1);

SELECT consume_once_listener(8);

-- Event 4: passive wheel listener cannot cancel the default action.
INSERT INTO dispatched_event (
    event_id,
    event_type,
    target_id,
    bubbles,
    cancelable,
    status,
    default_prevented
)
OVERRIDING SYSTEM VALUE
VALUES
    (4, 'wheel', 5, TRUE, TRUE, 'dispatched', FALSE);

INSERT INTO event_delivery (
    event_id,
    listener_id,
    current_target_id,
    phase,
    sequence_number,
    prevented_default
)
VALUES
    (4, 9, 5, 'at_target', 1, FALSE);

-- Event 5: focus does not bubble.
INSERT INTO dispatched_event (
    event_id,
    event_type,
    target_id,
    bubbles,
    cancelable,
    status
)
OVERRIDING SYSTEM VALUE
VALUES
    (5, 'focus', 7, FALSE, FALSE, 'dispatched');

INSERT INTO event_delivery (
    event_id,
    listener_id,
    current_target_id,
    phase,
    sequence_number
)
VALUES
    (5, 10, 6, 'capturing', 1);

-- Retrieve the actual hierarchy.
SELECT *
FROM event_path(5);

-- Evaluate which listeners would participate in bubbling for a target.
SELECT
    el.listener_id,
    el.target_id,
    et.element_name,
    el.event_type,
    el.listener_kind,
    el.selector,
    el.capture,
    el.once_listener,
    el.passive
FROM event_listener el
JOIN event_target et
  ON et.target_id = el.target_id
WHERE el.event_type = 'click'
  AND el.enabled
ORDER BY el.listener_priority;

-- Event delivery report.
SELECT
    de.event_id,
    de.event_type,
    target.element_name AS event_target,
    target.element_id,
    de.status,
    de.bubbles,
    de.cancelable,
    de.default_prevented,
    COUNT(ed.delivery_id) AS deliveries
FROM dispatched_event de
JOIN event_target target
  ON target.target_id = de.target_id
LEFT JOIN event_delivery ed
  ON ed.event_id = de.event_id
GROUP BY
    de.event_id,
    de.event_type,
    target.element_name,
    target.element_id,
    de.status,
    de.bubbles,
    de.cancelable,
    de.default_prevented
ORDER BY de.event_id;

-- Determine default-action eligibility.
SELECT
    de.event_id,
    de.event_type,
    da.action_name,
    CASE
        WHEN de.status = 'cancelled'
            THEN FALSE
        WHEN NOT de.cancelable
            THEN TRUE
        WHEN de.default_prevented
            THEN FALSE
        WHEN da.enabled
            THEN TRUE
        ELSE FALSE
    END AS default_action_allowed
FROM dispatched_event de
LEFT JOIN default_action da
  ON da.event_type = de.event_type
ORDER BY de.event_id;

-- Policy evaluation: dispatch is allowed only when the selected policy
-- permits the event type and the event satisfies cancelability rules.
SELECT
    ep.policy_name,
    de.event_id,
    de.event_type,
    ep.allow_default_action,
    ep.require_cancelable,
    etp.allow_dispatch,
    (
        etp.allow_dispatch
        AND (
            NOT ep.require_cancelable
            OR de.cancelable
        )
        AND event_depth(de.target_id) <= ep.max_bubble_depth
    ) AS eligible
FROM event_policy ep
JOIN event_type_policy etp
  ON etp.policy_id = ep.policy_id
JOIN dispatched_event de
  ON de.event_type = etp.event_type
WHERE ep.policy_id IN (1, 2)
ORDER BY ep.policy_id, de.event_id;

-- Transactional example: disable an event listener and record a failed
-- dispatch atomically.
BEGIN;

UPDATE event_listener
SET enabled = FALSE
WHERE listener_id = 7;

UPDATE dispatched_event
SET status = 'failed',
    completed_at = clock_timestamp()
WHERE event_id = 2
  AND status = 'cancelled';

COMMIT;

-- Final state report.
SELECT
    de.event_id,
    de.event_type,
    de.status,
    de.default_prevented,
    de.propagation_stopped,
    de.immediate_propagation_stopped,
    de.created_at,
    de.completed_at
FROM dispatched_event de
ORDER BY de.event_id;
