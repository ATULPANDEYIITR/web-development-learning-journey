DROP SCHEMA IF EXISTS event_loop_demo CASCADE;
CREATE SCHEMA event_loop_demo;

SET search_path TO event_loop_demo;

-- A host runtime has several distinct execution concepts:
-- synchronous stack frames, tasks, microtasks, and rendering work.
-- The relational model keeps these concepts separate rather than
-- treating every callback as the same kind of queue item.

CREATE TYPE execution_source AS ENUM (
    'script',
    'timer',
    'network',
    'user_event',
    'render'
);

CREATE TYPE queue_kind AS ENUM (
    'task',
    'microtask',
    'render'
);

CREATE TYPE execution_state AS ENUM (
    'queued',
    'running',
    'completed',
    'failed',
    'cancelled'
);

CREATE TABLE event_loop (
    loop_id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    current_time_ms BIGINT NOT NULL DEFAULT 0
        CHECK (current_time_ms >= 0),
    frame_interval_ms INTEGER NOT NULL DEFAULT 16
        CHECK (frame_interval_ms > 0),
    max_microtasks_per_checkpoint INTEGER NOT NULL DEFAULT 1000
        CHECK (max_microtasks_per_checkpoint > 0)
);

CREATE TABLE execution_context (
    context_id BIGSERIAL PRIMARY KEY,
    loop_id BIGINT NOT NULL REFERENCES event_loop(loop_id)
        ON DELETE CASCADE,
    name TEXT NOT NULL,
    parent_context_id BIGINT REFERENCES execution_context(context_id),
    stack_depth INTEGER NOT NULL CHECK (stack_depth >= 0),
    entered_at_ms BIGINT NOT NULL CHECK (entered_at_ms >= 0),
    exited_at_ms BIGINT,
    CHECK (exited_at_ms IS NULL OR exited_at_ms >= entered_at_ms)
);

CREATE TABLE queue_item (
    item_id BIGSERIAL PRIMARY KEY,
    loop_id BIGINT NOT NULL REFERENCES event_loop(loop_id)
        ON DELETE CASCADE,
    queue queue_kind NOT NULL,
    source execution_source NOT NULL,
    name TEXT NOT NULL,
    scheduled_at_ms BIGINT NOT NULL CHECK (scheduled_at_ms >= 0),
    sequence_no BIGINT NOT NULL,
    state execution_state NOT NULL DEFAULT 'queued',
    created_at_ms BIGINT NOT NULL CHECK (created_at_ms >= 0),
    started_at_ms BIGINT,
    completed_at_ms BIGINT,
    error_message TEXT,
    CHECK (
        started_at_ms IS NULL
        OR started_at_ms >= created_at_ms
    ),
    CHECK (
        completed_at_ms IS NULL
        OR started_at_ms IS NOT NULL
    ),
    CHECK (
        state <> 'failed'
        OR error_message IS NOT NULL
    ),
    UNIQUE (loop_id, sequence_no)
);

CREATE TABLE stack_event (
    stack_event_id BIGSERIAL PRIMARY KEY,
    loop_id BIGINT NOT NULL REFERENCES event_loop(loop_id)
        ON DELETE CASCADE,
    context_id BIGINT REFERENCES execution_context(context_id),
    event_time_ms BIGINT NOT NULL CHECK (event_time_ms >= 0),
    operation TEXT NOT NULL,
    stack_depth INTEGER NOT NULL CHECK (stack_depth >= 0)
);

CREATE TABLE microtask_checkpoint (
    checkpoint_id BIGSERIAL PRIMARY KEY,
    loop_id BIGINT NOT NULL REFERENCES event_loop(loop_id)
        ON DELETE CASCADE,
    started_at_ms BIGINT NOT NULL CHECK (started_at_ms >= 0),
    completed_at_ms BIGINT,
    processed_count INTEGER NOT NULL DEFAULT 0
        CHECK (processed_count >= 0),
    exhausted_safely BOOLEAN,
    CHECK (
        completed_at_ms IS NULL
        OR completed_at_ms >= started_at_ms
    ),
    CHECK (
        exhausted_safely IS NULL
        OR completed_at_ms IS NOT NULL
    )
);

CREATE TABLE rendering_opportunity (
    render_id BIGSERIAL PRIMARY KEY,
    loop_id BIGINT NOT NULL REFERENCES event_loop(loop_id)
        ON DELETE CASCADE,
    frame_number BIGINT NOT NULL CHECK (frame_number >= 1),
    frame_time_ms BIGINT NOT NULL CHECK (frame_time_ms >= 0),
    status TEXT NOT NULL CHECK (
        status IN ('scheduled', 'executed', 'skipped')
    ),
    UNIQUE (loop_id, frame_number)
);

CREATE INDEX idx_queue_ready_tasks
    ON queue_item (loop_id, scheduled_at_ms, sequence_no)
    WHERE queue = 'task' AND state = 'queued';

CREATE INDEX idx_queue_microtasks
    ON queue_item (loop_id, sequence_no)
    WHERE queue = 'microtask' AND state = 'queued';

CREATE INDEX idx_stack_history
    ON stack_event (loop_id, event_time_ms, stack_depth);

CREATE OR REPLACE FUNCTION validate_queue_item()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    loop_clock BIGINT;
BEGIN
    SELECT current_time_ms
    INTO loop_clock
    FROM event_loop
    WHERE loop_id = NEW.loop_id;

    IF NEW.scheduled_at_ms < NEW.created_at_ms THEN
        RAISE EXCEPTION
            'scheduled_at_ms cannot precede created_at_ms';
    END IF;

    IF NEW.queue = 'microtask'
       AND NEW.scheduled_at_ms <> NEW.created_at_ms THEN
        RAISE EXCEPTION
            'microtasks are checkpoint work, not delayed timer tasks';
    END IF;

    IF NEW.queue = 'render'
       AND NEW.source <> 'render' THEN
        RAISE EXCEPTION
            'render queue items must have render source';
    END IF;

    IF NEW.state = 'running'
       AND NEW.started_at_ms IS NULL THEN
        RAISE EXCEPTION
            'running queue item requires started_at_ms';
    END IF;

    IF loop_clock IS NULL THEN
        RAISE EXCEPTION
            'unknown event loop %', NEW.loop_id;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_queue_item
BEFORE INSERT OR UPDATE ON queue_item
FOR EACH ROW
EXECUTE FUNCTION validate_queue_item();

CREATE OR REPLACE FUNCTION enqueue_microtask(
    p_loop_id BIGINT,
    p_name TEXT,
    p_source execution_source DEFAULT 'script'
)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    v_now BIGINT;
    v_sequence BIGINT;
    v_id BIGINT;
BEGIN
    IF p_name IS NULL OR length(trim(p_name)) = 0 THEN
        RAISE EXCEPTION 'microtask name is required';
    END IF;

    SELECT current_time_ms
    INTO v_now
    FROM event_loop
    WHERE loop_id = p_loop_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'event loop % does not exist', p_loop_id;
    END IF;

    SELECT COALESCE(MAX(sequence_no), 0) + 1
    INTO v_sequence
    FROM queue_item
    WHERE loop_id = p_loop_id;

    INSERT INTO queue_item (
        loop_id,
        queue,
        source,
        name,
        scheduled_at_ms,
        sequence_no,
        state,
        created_at_ms
    )
    VALUES (
        p_loop_id,
        'microtask',
        p_source,
        p_name,
        v_now,
        v_sequence,
        'queued',
        v_now
    )
    RETURNING item_id INTO v_id;

    RETURN v_id;
END;
$$;

CREATE OR REPLACE FUNCTION advance_loop_clock(
    p_loop_id BIGINT,
    p_new_time_ms BIGINT
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    v_current BIGINT;
BEGIN
    IF p_new_time_ms < 0 THEN
        RAISE EXCEPTION 'time cannot be negative';
    END IF;

    SELECT current_time_ms
    INTO v_current
    FROM event_loop
    WHERE loop_id = p_loop_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'event loop % does not exist', p_loop_id;
    END IF;

    IF p_new_time_ms < v_current THEN
        RAISE EXCEPTION
            'event-loop clock cannot move backward: % -> %',
            v_current,
            p_new_time_ms;
    END IF;

    UPDATE event_loop
    SET current_time_ms = p_new_time_ms
    WHERE loop_id = p_loop_id;
END;
$$;

INSERT INTO event_loop (
    name,
    current_time_ms,
    frame_interval_ms,
    max_microtasks_per_checkpoint
)
VALUES (
    'browser-demo',
    0,
    16,
    100
);

INSERT INTO execution_context (
    loop_id,
    name,
    stack_depth,
    entered_at_ms
)
VALUES
    (1, 'global-script', 1, 0),
    (1, 'event-handler', 2, 0),
    (1, 'nested-function', 3, 0);

INSERT INTO stack_event (
    loop_id,
    context_id,
    event_time_ms,
    operation,
    stack_depth
)
VALUES
    (1, 1, 0, 'enter global-script', 1),
    (1, 2, 0, 'enter event-handler', 2),
    (1, 3, 0, 'enter nested-function', 3),
    (1, 3, 1, 'exit nested-function', 3),
    (1, 2, 1, 'exit event-handler', 2),
    (1, 1, 1, 'exit global-script', 1);

INSERT INTO queue_item (
    loop_id,
    queue,
    source,
    name,
    scheduled_at_ms,
    sequence_no,
    state,
    created_at_ms
)
VALUES
    (1, 'task', 'timer', 'setTimeout-0', 0, 1, 'completed', 0),
    (1, 'microtask', 'script', 'promise-then', 0, 2, 'completed', 0),
    (1, 'task', 'network', 'fetch-response', 5, 3, 'queued', 0),
    (1, 'microtask', 'network', 'response-promise', 5, 4, 'queued', 5),
    (1, 'render', 'render', 'paint-frame-1', 16, 5, 'queued', 0),
    (1, 'task', 'user_event', 'click-handler', 20, 6, 'queued', 0);

INSERT INTO microtask_checkpoint (
    loop_id,
    started_at_ms,
    completed_at_ms,
    processed_count,
    exhausted_safely
)
VALUES
    (1, 0, 1, 1, TRUE),
    (1, 5, NULL, 1, NULL);

INSERT INTO rendering_opportunity (
    loop_id,
    frame_number,
    frame_time_ms,
    status
)
VALUES
    (1, 1, 16, 'scheduled'),
    (1, 2, 32, 'scheduled');

-- Retrieve the next task that is eligible to execute.
SELECT
    item_id,
    name,
    source,
    scheduled_at_ms,
    sequence_no
FROM queue_item
WHERE loop_id = 1
  AND queue = 'task'
  AND state = 'queued'
  AND scheduled_at_ms <= (
      SELECT current_time_ms
      FROM event_loop
      WHERE loop_id = 1
  )
ORDER BY scheduled_at_ms, sequence_no
LIMIT 1;

-- Microtasks are evaluated separately from ordinary tasks.
SELECT
    item_id,
    name,
    sequence_no,
    state
FROM queue_item
WHERE loop_id = 1
  AND queue = 'microtask'
ORDER BY sequence_no;

-- Show the complete execution timeline.
SELECT
    q.scheduled_at_ms,
    q.queue,
    q.source,
    q.name,
    q.state,
    q.sequence_no
FROM queue_item AS q
WHERE q.loop_id = 1
ORDER BY q.scheduled_at_ms, q.sequence_no;

-- Detect queued work that can compete for execution.
SELECT
    queue,
    COUNT(*) AS pending_items,
    MIN(scheduled_at_ms) AS earliest_scheduled_time
FROM queue_item
WHERE loop_id = 1
  AND state = 'queued'
GROUP BY queue
ORDER BY queue;

-- Rendering opportunities expose frame boundaries separately from
-- ordinary task execution.
SELECT
    frame_number,
    frame_time_ms,
    status
FROM rendering_opportunity
WHERE loop_id = 1
ORDER BY frame_number;

-- Find execution contexts that increase stack depth.
SELECT
    context_id,
    name,
    stack_depth,
    entered_at_ms,
    exited_at_ms
FROM execution_context
WHERE loop_id = 1
ORDER BY entered_at_ms, stack_depth;

-- Transactional state transition:
-- claim the earliest ready task without allowing two workers to claim it.
BEGIN;

WITH candidate AS (
    SELECT item_id
    FROM queue_item
    WHERE loop_id = 1
      AND queue = 'task'
      AND state = 'queued'
      AND scheduled_at_ms <= (
          SELECT current_time_ms
          FROM event_loop
          WHERE loop_id = 1
      )
    ORDER BY scheduled_at_ms, sequence_no
    FOR UPDATE SKIP LOCKED
    LIMIT 1
)
UPDATE queue_item AS q
SET
    state = 'running',
    started_at_ms = (
        SELECT current_time_ms
        FROM event_loop
        WHERE loop_id = 1
    )
FROM candidate
WHERE q.item_id = candidate.item_id;

COMMIT;

-- Microtask pressure can be identified before it creates long
-- checkpoints and delays rendering.
SELECT
    checkpoint_id,
    started_at_ms,
    completed_at_ms,
    processed_count,
    exhausted_safely
FROM microtask_checkpoint
WHERE processed_count >= (
    SELECT max_microtasks_per_checkpoint
    FROM event_loop
    WHERE loop_id = 1
)
ORDER BY started_at_ms;
