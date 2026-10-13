-- Dates and Internationalization
-- PostgreSQL 15 or later.
--
-- The schema models international operations scheduling.
-- TIMESTAMPTZ represents an instant, not the original named time zone.
-- Named IANA zones are retained separately so local presentation and
-- future calendar rules can be handled deliberately by the application.

BEGIN;

DROP VIEW IF EXISTS event_localized_view;
DROP VIEW IF EXISTS upcoming_event_view;
DROP TABLE IF EXISTS event_audit;
DROP TABLE IF EXISTS scheduled_events;
DROP TABLE IF EXISTS display_preferences;
DROP TABLE IF EXISTS supported_zones;

CREATE TABLE supported_zones (
    zone_name TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT supported_zone_name_not_empty
        CHECK (length(trim(zone_name)) > 0)
);

CREATE TABLE display_preferences (
    preference_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_code TEXT NOT NULL UNIQUE,
    locale_tag TEXT NOT NULL,
    zone_name TEXT NOT NULL REFERENCES supported_zones(zone_name),
    date_style TEXT NOT NULL DEFAULT 'medium',
    time_style TEXT NOT NULL DEFAULT 'short',
    CONSTRAINT valid_locale_tag
        CHECK (locale_tag ~ '^[A-Za-z]{2,8}(-[A-Za-z0-9]{1,8})*$'),
    CONSTRAINT valid_date_style
        CHECK (date_style IN ('short', 'medium', 'long', 'full')),
    CONSTRAINT valid_time_style
        CHECK (time_style IN ('short', 'medium', 'long', 'full'))
);

CREATE TABLE scheduled_events (
    event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    external_code TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL,
    display_zone TEXT NOT NULL REFERENCES supported_zones(zone_name),
    event_kind TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'scheduled',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    calendar_date DATE,
    local_wall_time TIME WITHOUT TIME ZONE,
    requested_offset_seconds INTEGER,
    CONSTRAINT nonempty_event_code
        CHECK (length(trim(external_code)) > 0),
    CONSTRAINT nonempty_event_title
        CHECK (length(trim(title)) > 0),
    CONSTRAINT valid_event_kind
        CHECK (event_kind IN ('deployment', 'security', 'maintenance', 'review')),
    CONSTRAINT valid_event_status
        CHECK (status IN ('scheduled', 'completed', 'cancelled')),
    CONSTRAINT valid_offset_seconds
        CHECK (
            requested_offset_seconds IS NULL
            OR requested_offset_seconds BETWEEN -50400 AND 50400
        )
);

-- This index supports chronological retrieval and range-based scheduling.
CREATE INDEX scheduled_events_occurred_at_idx
    ON scheduled_events (occurred_at);

CREATE INDEX scheduled_events_status_time_idx
    ON scheduled_events (status, occurred_at);

CREATE INDEX scheduled_events_display_zone_time_idx
    ON scheduled_events (display_zone, occurred_at);

CREATE TABLE event_audit (
    audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    event_id BIGINT NOT NULL REFERENCES scheduled_events(event_id),
    action TEXT NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    previous_status TEXT,
    new_status TEXT,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT valid_audit_action
        CHECK (action IN ('created', 'status_changed', 'rescheduled'))
);

INSERT INTO supported_zones (zone_name, description) VALUES
    ('UTC', 'Coordinated Universal Time'),
    ('Asia/Kolkata', 'India Standard Time region'),
    ('Europe/London', 'United Kingdom regional time'),
    ('America/New_York', 'Eastern United States regional time'),
    ('Asia/Tokyo', 'Japan regional time');

INSERT INTO display_preferences
    (user_code, locale_tag, zone_name, date_style, time_style)
VALUES
    ('OPS_INDIA', 'en-IN', 'Asia/Kolkata', 'long', 'short'),
    ('SEC_UK', 'en-GB', 'Europe/London', 'full', 'short'),
    ('PLATFORM_US', 'en-US', 'America/New_York', 'medium', 'long');

INSERT INTO scheduled_events (
    external_code,
    title,
    occurred_at,
    display_zone,
    event_kind,
    status,
    calendar_date,
    local_wall_time,
    requested_offset_seconds
)
VALUES
    (
        'DEP-104',
        'Production deployment review',
        TIMESTAMPTZ '2026-10-13 09:00:00+00',
        'Asia/Kolkata',
        'deployment',
        'scheduled',
        DATE '2026-10-13',
        TIME '14:30:00',
        19800
    ),
    (
        'SEC-207',
        'Security incident exercise',
        TIMESTAMPTZ '2026-10-13 15:00:00+00',
        'Europe/London',
        'security',
        'scheduled',
        DATE '2026-10-13',
        TIME '16:00:00',
        3600
    ),
    (
        'OPS-315',
        'Infrastructure maintenance',
        TIMESTAMPTZ '2026-10-14 01:00:00+00',
        'America/New_York',
        'maintenance',
        'scheduled',
        DATE '2026-10-13',
        TIME '21:00:00',
        -14400
    ),
    (
        'REV-412',
        'Quarterly service review',
        TIMESTAMPTZ '2026-10-15 10:00:00+00',
        'Asia/Tokyo',
        'review',
        'completed',
        DATE '2026-10-15',
        TIME '19:00:00',
        32400
    );

-- A PostgreSQL TIMESTAMPTZ value is rendered using the session time zone.
-- AT TIME ZONE converts the stored instant into a wall-clock value in a
-- named regional zone. It does not preserve the zone name in the result.
CREATE VIEW event_localized_view AS
SELECT
    e.event_id,
    e.external_code,
    e.title,
    e.occurred_at,
    e.occurred_at AT TIME ZONE 'UTC' AS utc_wall_time,
    e.occurred_at AT TIME ZONE e.display_zone AS regional_wall_time,
    e.display_zone,
    e.event_kind,
    e.status,
    e.calendar_date,
    e.local_wall_time,
    e.requested_offset_seconds
FROM scheduled_events AS e;

CREATE VIEW upcoming_event_view AS
SELECT
    event_id,
    external_code,
    title,
    occurred_at,
    display_zone,
    event_kind,
    status
FROM scheduled_events
WHERE status = 'scheduled'
ORDER BY occurred_at;

-- Record event creation and state changes without changing the event's instant.
CREATE FUNCTION audit_scheduled_event()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO event_audit (
            event_id,
            action,
            new_status,
            details
        )
        VALUES (
            NEW.event_id,
            'created',
            NEW.status,
            jsonb_build_object(
                'external_code', NEW.external_code,
                'display_zone', NEW.display_zone,
                'occurred_at', NEW.occurred_at
            )
        );

        RETURN NEW;
    END IF;

    IF OLD.status IS DISTINCT FROM NEW.status THEN
        INSERT INTO event_audit (
            event_id,
            action,
            previous_status,
            new_status,
            details
        )
        VALUES (
            NEW.event_id,
            'status_changed',
            OLD.status,
            NEW.status,
            jsonb_build_object(
                'external_code', NEW.external_code,
                'occurred_at', NEW.occurred_at
            )
        );
    END IF;

    IF OLD.occurred_at IS DISTINCT FROM NEW.occurred_at THEN
        INSERT INTO event_audit (
            event_id,
            action,
            previous_status,
            new_status,
            details
        )
        VALUES (
            NEW.event_id,
            'rescheduled',
            OLD.status,
            NEW.status,
            jsonb_build_object(
                'previous_instant', OLD.occurred_at,
                'new_instant', NEW.occurred_at,
                'display_zone', NEW.display_zone
            )
        );
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER scheduled_events_audit_trigger
AFTER INSERT OR UPDATE OF status, occurred_at
ON scheduled_events
FOR EACH ROW
EXECUTE FUNCTION audit_scheduled_event();

-- Inspect all events in UTC and their regional wall-clock representations.
SELECT
    external_code,
    title,
    occurred_at AT TIME ZONE 'UTC' AS utc_time,
    occurred_at AT TIME ZONE display_zone AS regional_time,
    display_zone,
    status
FROM scheduled_events
ORDER BY occurred_at;

-- Convert one fixed instant into several regional representations.
WITH reference_instant AS (
    SELECT TIMESTAMPTZ '2026-10-13 10:00:00+00' AS instant
)
SELECT
    instant,
    instant AT TIME ZONE 'UTC' AS utc_time,
    instant AT TIME ZONE 'Asia/Kolkata' AS india_time,
    instant AT TIME ZONE 'Europe/London' AS london_time,
    instant AT TIME ZONE 'America/New_York' AS new_york_time,
    instant AT TIME ZONE 'Asia/Tokyo' AS tokyo_time
FROM reference_instant;

-- Retrieve scheduled workload per regional zone and calendar day.
SELECT
    display_zone,
    (occurred_at AT TIME ZONE display_zone)::date AS regional_date,
    COUNT(*) AS event_count,
    MIN(occurred_at) AS first_instant,
    MAX(occurred_at) AS last_instant
FROM scheduled_events
WHERE status = 'scheduled'
GROUP BY
    display_zone,
    (occurred_at AT TIME ZONE display_zone)::date
ORDER BY regional_date, display_zone;

-- Demonstrate timestamp-based deadline evaluation using a fixed reference
-- instant so that the sample output is reproducible.
WITH reference_time AS (
    SELECT TIMESTAMPTZ '2026-10-13 12:00:00+00' AS now_utc
)
SELECT
    e.external_code,
    e.title,
    e.occurred_at,
    r.now_utc,
    CASE
        WHEN e.occurred_at < r.now_utc THEN 'past'
        WHEN e.occurred_at = r.now_utc THEN 'due_now'
        ELSE 'future'
    END AS time_state
FROM scheduled_events AS e
CROSS JOIN reference_time AS r
ORDER BY e.occurred_at;

-- Calendar-day intervals and elapsed durations are distinct.
SELECT
    external_code,
    occurred_at,
    occurred_at + INTERVAL '24 hours' AS after_24_elapsed_hours,
    occurred_at + INTERVAL '1 day' AS after_calendar_day
FROM scheduled_events
WHERE external_code = 'DEP-104';

-- Update a status within a transaction. The trigger creates an audit row.
BEGIN;

UPDATE scheduled_events
SET status = 'completed'
WHERE external_code = 'DEP-104'
  AND status = 'scheduled';

SELECT
    e.external_code,
    e.status,
    a.action,
    a.previous_status,
    a.new_status,
    a.recorded_at
FROM scheduled_events AS e
JOIN event_audit AS a ON a.event_id = e.event_id
WHERE e.external_code = 'DEP-104'
ORDER BY a.audit_id;

COMMIT;

-- The next query exposes the difference between stored instants and
-- user-selected wall-clock values. PostgreSQL does not automatically prove
-- that calendar_date, local_wall_time, requested_offset_seconds, and the
-- regional zone agree. Application validation or a dedicated database
-- function must verify that policy, especially around DST gaps and overlaps.
SELECT
    external_code,
    display_zone,
    calendar_date,
    local_wall_time,
    requested_offset_seconds,
    occurred_at,
    occurred_at AT TIME ZONE display_zone AS actual_regional_wall_time
FROM scheduled_events
ORDER BY external_code;

-- Demonstrate that a database constraint rejects an invalid status.
-- The nested block catches the expected error so the script can continue.
DO $$
BEGIN
    BEGIN
        UPDATE scheduled_events
        SET status = 'waiting'
        WHERE external_code = 'SEC-207';

        RAISE EXCEPTION 'Expected invalid status to be rejected';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE 'Invalid status rejected by CHECK constraint';
    END;
END;
$$;

-- Show the audit history created by inserts and status updates.
SELECT
    e.external_code,
    a.action,
    a.previous_status,
    a.new_status,
    a.recorded_at,
    a.details
FROM event_audit AS a
JOIN scheduled_events AS e ON e.event_id = a.event_id
ORDER BY a.audit_id;

COMMIT;
